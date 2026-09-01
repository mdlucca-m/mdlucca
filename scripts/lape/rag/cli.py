"""Linha de comando da camada de recuperacao semantica.

    lape_agent.py rag indexar --pasta ~/tese --tipo tese
    lape_agent.py rag buscar "o vigor se recupera durante a noite?"
    lape_agent.py rag status
    lape_agent.py rag mcp                    # servidor MCP em stdio
    lape_agent.py rag escrever "paragrafo sobre o efeito piso da BRUMS"
    lape_agent.py rag coerencia --foco "objetivos contra resultados"
    lape_agent.py rag literatura "mood profile handball" "BRUMS pre-season"
    lape_agent.py rag triagem REV2024 --limite 30
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .. import config as base_config
from . import config
from .embed import get_embedder
from .index import docs_do_banco, indexar_documentos, indexar_pastas
from .search import buscar
from .store import Filtro, SqliteStore


def _abrir(args) -> tuple[sqlite3.Connection, SqliteStore]:
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    store = SqliteStore(conn)
    store.ensure_schema()
    return conn, store


def _filtro(args) -> Filtro | None:
    tipos = getattr(args, "tipo", None)
    de = getattr(args, "ano_de", None)
    ate = getattr(args, "ano_ate", None)
    if not tipos and de is None and ate is None:
        return None
    return Filtro(kinds=[tipos] if isinstance(tipos, str) else tipos,
                  anos=(de, ate) if (de is not None or ate is not None) else None)


def cmd_indexar(args) -> int:
    conn, store = _abrir(args)
    emb = get_embedder(args.backend) if args.backend else get_embedder()
    if not emb.semantic:
        print("[aviso] sem backend semantico: a indexacao usa o hash deterministico.\n"
              "        Defina VOYAGE_API_KEY ou instale sentence-transformers e "
              "reindexe com --reindexar.\n")
    total = None
    if args.banco:
        print("Indexando o que ja esta no banco do LAPE...")
        total = indexar_documentos(store, docs_do_banco(conn), emb,
                                   reindexar=args.reindexar, verbose=args.verboso)
        print(" ", total.resumo())
    if args.pasta or not args.banco:
        pastas = [Path(p) for p in (args.pasta or [])] or config.CORPUS_DIRS
        print(f"Indexando arquivos de: {', '.join(str(p) for p in pastas)}")
        rel = indexar_pastas(store, pastas, kind=args.tipo_doc, embedder=emb,
                             reindexar=args.reindexar, verbose=args.verboso)
        print(" ", rel.resumo())
        for erro in rel.erros[:10]:
            print("   !", erro)
        total = rel
    conn.close()
    return 0 if not total or total.falhas == 0 else 1


def cmd_buscar(args) -> int:
    conn, store = _abrir(args)
    r = buscar(store, args.consulta, k=args.k, filtro=_filtro(args))
    if args.json:
        print(json.dumps({"consulta": r.consulta, "ms": r.ms, "aviso": r.aviso,
                          "fontes": r.fontes(),
                          "trechos": [h.text for h in r.hits]},
                         ensure_ascii=False, indent=2))
        conn.close()
        return 0
    if r.aviso:
        print(f"[aviso] {r.aviso}\n")
    if not r.hits:
        print("Nenhum trecho. O indice pode estar vazio: rode 'rag status'.")
        conn.close()
        return 1
    print(f"{len(r.hits)} trechos em {r.ms} ms "
          f"({r.densa} candidatos densos, {r.lexica} lexicos)\n")
    for i, h in enumerate(r.hits, 1):
        print(f"[{i}] {h.citacao()}  score {h.score:.4f} via {h.origem} "
              f"(chunk_id {h.chunk_id})")
        print(f"    {h.title or h.uri}")
        texto = h.text if args.completo else (h.text[:400] + ("..." if len(h.text) > 400 else ""))
        print("    " + texto.replace("\n", "\n    ") + "\n")
    conn.close()
    return 0


def cmd_status(args) -> int:
    conn, store = _abrir(args)
    s = store.stats()
    emb_ok = True
    try:
        emb = get_embedder()
        emb_desc = f"{emb.model} ({emb.dim} dimensoes)"
        emb_ok = emb.semantic
    except Exception as exc:
        emb_desc = f"indisponivel: {exc}"
        emb_ok = False
    from .llm import disponivel
    llm_ok, llm_motivo = disponivel()
    print(f"Banco:      {args.db}")
    print(f"Documentos: {s['documentos']:>6}")
    print(f"Trechos:    {s['trechos']:>6}")
    print(f"Vetores:    {s['vetores']:>6}")
    print(f"Caracteres: {s['caracteres']:>6}")
    print(f"Store:      {s['backend']}")
    print(f"Embeddings: {emb_desc}" + ("" if emb_ok else "   <- sem busca semantica"))
    print(f"Modelo LLM: {config.LLM_MODEL}" if llm_ok else f"Modelo LLM: {llm_motivo}")
    if s.get("modelos"):
        print("\nVetores por modelo")
        for m in s["modelos"]:
            print(f"  {m['model']:<44} {m['dim']:>5} dim  {m['n']:>7} vetores")
    if s.get("por_tipo"):
        print("\nDocumentos por tipo")
        for t in s["por_tipo"]:
            print(f"  {t['kind']:<16} {t['n']:>5} documentos  {t['trechos'] or 0:>7} trechos")
    ultimas = conn.execute(
        "SELECT kind, agent, query, n_chunks, ms, at FROM rag_runs"
        " ORDER BY id DESC LIMIT 5").fetchall()
    if ultimas:
        print("\nUltimas operacoes")
        for u in ultimas:
            rotulo = u["agent"] or u["kind"]
            print(f"  {u['at']}  {rotulo:<12} {(u['query'] or '')[:44]:<44} {u['ms'] or 0:>6} ms")
    conn.close()
    return 0


def cmd_mcp(args) -> int:
    from .mcp_server import main as servir
    return servir(args.db)


def cmd_escrever(args) -> int:
    from .agents import escrita
    conn, store = _abrir(args)
    base = Path(args.arquivo).read_text(encoding="utf-8") if args.arquivo else None
    saida = escrita.executar(store, args.instrucao, modo=args.modo, texto_base=base,
                             k=args.k, filtro=_filtro(args), palavras=args.palavras)
    _entregar(saida, args)
    conn.close()
    return 0


def cmd_coerencia(args) -> int:
    from .agents import coerencia
    conn, store = _abrir(args)
    saida = coerencia.executar(store, k=args.k, filtro=_filtro(args), foco=args.foco)
    _entregar(saida, args)
    conn.close()
    return 0


def cmd_literatura(args) -> int:
    from .agents import literatura
    conn, store = _abrir(args)
    saida = literatura.executar(store, args.temas, limite=args.limite,
                                indexar=not args.sem_indexar, triar=not args.sem_triagem,
                                mailto=base_config.__dict__.get("CONTACT_EMAIL"))
    _entregar(saida, args)
    conn.close()
    return 0


def cmd_triagem(args) -> int:
    from .agents import revisao
    conn, store = _abrir(args)
    try:
        saida = revisao.executar(store, conn, args.revisao, limite=args.limite,
                                 gravar=args.gravar)
    except LookupError as exc:
        print(exc)
        conn.close()
        return 1
    _entregar(saida, args)
    conn.close()
    return 0


def _entregar(saida, args) -> None:
    if getattr(args, "json", False):
        print(json.dumps(saida.to_dict(), ensure_ascii=False, indent=2))
    else:
        saida.imprimir()
    destino = getattr(args, "para", None)
    if destino:
        Path(destino).write_text(saida.texto, encoding="utf-8")
        print(f"\n[gravado em {destino}]")


def build_parser(pai: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    """Monta o parser do 'rag'. Reutilizavel dentro do lape_agent."""
    descricao = "recuperacao semantica sobre o corpus do laboratorio"
    p = (pai.add_parser("rag", help=descricao, description=__doc__,
                        formatter_class=argparse.RawDescriptionHelpFormatter)
         if pai else argparse.ArgumentParser(prog="rag", description=__doc__))
    p.add_argument("--db", type=Path, default=base_config.DB_PATH,
                   help="banco SQLite (padrao: %(default)s)")
    sub = p.add_subparsers(dest="rag_comando", required=True)

    ind = sub.add_parser("indexar", help="le arquivos e o banco e grava os vetores")
    ind.add_argument("--pasta", action="append", metavar="CAMINHO",
                     help="pasta ou arquivo a indexar (repetivel)")
    ind.add_argument("--banco", action="store_true",
                     help="tambem indexa artigos e referencias ja no banco")
    ind.add_argument("--tipo-doc", default="externo",
                     help="rotulo dos documentos lidos das pastas (padrao: %(default)s)")
    ind.add_argument("--reindexar", action="store_true",
                     help="refaz mesmo o que nao mudou (use ao trocar de modelo)")
    ind.add_argument("--backend", help="voyage, openai, local ou hash")
    ind.add_argument("--silencioso", dest="verboso", action="store_false",
                     help="nao lista arquivo a arquivo")
    ind.set_defaults(func=cmd_indexar, verboso=True)

    bus = sub.add_parser("buscar", help="consulta o indice")
    bus.add_argument("consulta")
    bus.add_argument("-k", type=int, default=config.TOP_K, help="quantos trechos")
    bus.add_argument("--tipo", action="append", help="filtra por tipo (repetivel)")
    bus.add_argument("--ano-de", type=int)
    bus.add_argument("--ano-ate", type=int)
    bus.add_argument("--completo", action="store_true", help="mostra o trecho inteiro")
    bus.add_argument("--json", action="store_true")
    bus.set_defaults(func=cmd_buscar)

    sta = sub.add_parser("status", help="inventario do indice e das credenciais")
    sta.set_defaults(func=cmd_status)

    mcp = sub.add_parser("mcp", help="servidor MCP em stdio")
    mcp.set_defaults(func=cmd_mcp)

    esc = sub.add_parser("escrever", help="agente de escrita com fundamentacao")
    esc.add_argument("instrucao")
    esc.add_argument("--modo", default="redigir",
                     choices=["redigir", "revisar", "expandir", "resumir"])
    esc.add_argument("--arquivo", type=Path, help="texto de partida")
    esc.add_argument("--palavras", type=int, help="extensao alvo")
    esc.add_argument("-k", type=int, default=10)
    esc.add_argument("--tipo", action="append")
    esc.add_argument("--para", type=Path, help="grava a saida neste arquivo")
    esc.add_argument("--json", action="store_true")
    esc.set_defaults(func=cmd_escrever)

    coe = sub.add_parser("coerencia", help="agente de coerencia da tese")
    coe.add_argument("--foco", help="ponto especifico a auditar")
    coe.add_argument("-k", type=int, default=6)
    coe.add_argument("--tipo", action="append", default=["tese"])
    coe.add_argument("--para", type=Path)
    coe.add_argument("--json", action="store_true")
    coe.set_defaults(func=cmd_coerencia)

    lit = sub.add_parser("literatura", help="agente de vigilancia bibliografica")
    lit.add_argument("temas", nargs="+")
    lit.add_argument("--limite", type=int, default=20, help="registros por base e tema")
    lit.add_argument("--sem-indexar", action="store_true")
    lit.add_argument("--sem-triagem", action="store_true")
    lit.add_argument("--para", type=Path)
    lit.add_argument("--json", action="store_true")
    lit.set_defaults(func=cmd_literatura)

    tri = sub.add_parser("triagem", help="agente de revisao sistematica")
    tri.add_argument("revisao", help="codigo ou id da revisao")
    tri.add_argument("--limite", type=int, default=30)
    tri.add_argument("--gravar", action="store_true",
                     help="guarda a sugestao em rag_runs (nunca em screenings)")
    tri.add_argument("--para", type=Path)
    tri.add_argument("--json", action="store_true")
    tri.set_defaults(func=cmd_triagem)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":                            # pragma: no cover
    sys.exit(main())
