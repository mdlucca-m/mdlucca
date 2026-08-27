#!/usr/bin/env python3
"""Reexecuta a busca no PubMed, Scopus e Web of Science e atualiza a biblioteca.

    python3 scripts/atualizar_buscas.py --db data/BIBLIOTECA_HANDEBOL.sqlite
    python3 scripts/atualizar_buscas.py --bases pubmed --contar-apenas
    python3 scripts/atualizar_buscas.py --db lib.sqlite --bruto data/bruto/

Credenciais, por variável de ambiente:
    NCBI_API_KEY      opcional; sem ela o PubMed roda a 3 req/s em vez de 10
    NCBI_EMAIL        recomendado pela NLM para contato em caso de abuso
    SCOPUS_API_KEY    obrigatória para o Scopus   (https://dev.elsevier.com)
    SCOPUS_INSTTOKEN  opcional; habilita a view COMPLETE (resumo, autores)
    WOS_API_KEY       obrigatória para o WoS      (https://developer.clarivate.com)

Hosts que precisam estar liberados na política de rede do ambiente:
    eutils.ncbi.nlm.nih.gov     api.elsevier.com     api.clarivate.com
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from busca import deposito, estrategia
from busca.clientes import ChaveAusente, PubMed, Scopus, WebOfScience
from busca.http import BloqueioDeRede, ErroHTTP, Sessao
from busca.normalizar import deduplicar, normalizar

BASES = {
    "pubmed": (PubMed, estrategia.pubmed, "PubMed"),
    "scopus": (Scopus, estrategia.scopus, "Scopus"),
    "wos": (WebOfScience, estrategia.wos, "Web of Science"),
}


def executar(bases: list[str], *, janela: tuple[int, int], dir_bruto: Path | None,
             contar_apenas: bool, limite: int | None) -> tuple[list[dict], dict, dict]:
    brutos: list[dict] = []
    rendimento: dict[str, dict] = {}
    consultas: dict[str, str] = {}

    for chave in bases:
        cls, montar, rotulo = BASES[chave]
        consulta = montar()
        consultas[chave] = consulta
        print(f"\n── {rotulo} ── consulta com {len(consulta)} caracteres")

        try:
            cliente = cls(sessao=Sessao(
                req_por_segundo=3.0,
                dir_bruto=dir_bruto / chave if dir_bruto else None))
        except ChaveAusente as e:
            print(f"   ✗ {e}")
            rendimento[rotulo] = {"declarados": None, "recuperados": None, "erro": str(e)}
            continue

        try:
            kw = {"janela": janela} if chave == "pubmed" else {}
            declarados = cliente.contar(consulta, **kw)
            print(f"   a base declara {declarados} registros")
            rendimento[rotulo] = {"declarados": declarados, "recuperados": 0, "erro": None}
            if contar_apenas:
                continue

            n = 0
            for reg in cliente.buscar(consulta, **kw):
                brutos.append(reg)
                n += 1
                if n % 100 == 0:
                    print(f"   … {n}/{declarados}")
                if limite and n >= limite:
                    print(f"   (interrompido em --limite {limite})")
                    break
            rendimento[rotulo]["recuperados"] = n
            print(f"   ✓ {n} registros recuperados")

        except BloqueioDeRede as e:
            print(f"   ✗ rede: {e}")
            rendimento[rotulo] = {"declarados": None, "recuperados": None, "erro": f"rede: {e}"}
        except ErroHTTP as e:
            print(f"   ✗ {e}")
            rendimento[rotulo] = {"declarados": None, "recuperados": None, "erro": str(e)}

    return brutos, rendimento, consultas


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default="data/BIBLIOTECA_HANDEBOL.sqlite",
                   help="biblioteca SQLite (criada se não existir)")
    p.add_argument("--bases", default="pubmed,scopus,wos",
                   help="bases a interrogar, separadas por vírgula")
    p.add_argument("--janela", default=f"{estrategia.JANELA[0]}-{estrategia.JANELA[1]}")
    p.add_argument("--bruto", type=Path, default=None,
                   help="diretório onde gravar as respostas cruas, para auditoria")
    p.add_argument("--contar-apenas", action="store_true",
                   help="só reporta o total declarado por cada base")
    p.add_argument("--limite", type=int, default=None,
                   help="máximo de registros por base (para testes)")
    p.add_argument("--imprimir-consultas", action="store_true")
    a = p.parse_args(argv)

    if a.imprimir_consultas:
        for chave in a.bases.split(","):
            _, montar, rotulo = BASES[chave.strip()]
            q = montar()
            print(f"=== {rotulo} ({len(q)} caracteres) ===\n{q}\n")
        return 0

    ini, fim = (int(x) for x in a.janela.split("-"))
    bases = [b.strip() for b in a.bases.split(",") if b.strip() in BASES]
    t0 = time.monotonic()

    brutos, rendimento, consultas = executar(
        bases, janela=(ini, fim), dir_bruto=a.bruto,
        contar_apenas=a.contar_apenas, limite=a.limite)

    print("\n── rendimento por base ──")
    for base, v in rendimento.items():
        estado = v["erro"] or f"{v['recuperados']} de {v['declarados']}"
        print(f"   {base:16s} {estado}")

    if a.contar_apenas:
        return 0
    if not brutos:
        print("\nNenhum registro recuperado — nada a gravar.")
        return 1

    registros = [normalizar(r) for r in brutos]
    unicos, duplicatas = deduplicar(registros)
    print(f"\n── deduplicação ── {len(registros)} identificados → "
          f"{len(duplicatas)} duplicatas → {len(unicos)} únicos")
    por_criterio: dict[str, int] = {}
    for d in duplicatas:
        por_criterio[d["_criterio"]] = por_criterio.get(d["_criterio"], 0) + 1
    for c, n in sorted(por_criterio.items()):
        print(f"   por {c}: {n}")

    fora = [r for r in unicos if r["ano"] and not (ini <= int(r["ano"]) <= fim)]
    if fora:
        print(f"   ⚠ {len(fora)} registros fora da janela {ini}-{fim}; não serão gravados")
        unicos = [r for r in unicos if r not in fora]

    Path(a.db).parent.mkdir(parents=True, exist_ok=True)
    con = deposito.conectar(a.db)
    novos, atualizados = deposito.gravar(con, unicos)
    eid = deposito.registrar_execucao(
        con, janela=(ini, fim), rendimento=rendimento, duplicatas=duplicatas,
        unicos=len(unicos), novos=novos, atualizados=atualizados,
        duracao_s=int(time.monotonic() - t0), consultas=consultas)

    print(f"\n── biblioteca ── {novos} novos, {atualizados} atualizados "
          f"(execução #{eid} em {a.db})")
    print("\nTabela 1 do manuscrito, gerada dos dados desta execução:\n")
    print(deposito.tabela_rendimento(con, eid))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
