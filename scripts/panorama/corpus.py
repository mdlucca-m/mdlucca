#!/usr/bin/env python3
"""Panorama da produção internacional sobre psicologia do esporte no handebol.

Responde ao que a revisão precisa declarar antes de qualquer síntese: quantas
revisões já existem, quantos estudos experimentais, quantos transversais, e
como isso se distribui por variável psicológica e por desfecho.

O recorte aqui é mais largo que o da elegibilidade da revisão. A elegibilidade
exclui revisões por delineamento; o panorama precisa contá-las, porque a
pergunta é justamente se o campo já foi revisado. Por isso o universo é
handebol mais janela temporal mais construto psicológico, sem o filtro de
delineamento.

    python3 scripts/panorama/corpus.py                 # imprime o panorama
    python3 scripts/panorama/corpus.py --json saida.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from scripts.curadoria import elegibilidade as E  # noqa: E402
from scripts.curadoria import psicometria as P  # noqa: E402

BANCO = RAIZ / "data" / "BIBLIOTECA_HANDEBOL.sqlite"

# Agrupamento dos tipos e desenhos declarados na biblioteca em categorias de
# delineamento comparáveis entre si.
CATEGORIA = {
    "revisão": ("Revisao", "Revisao sistematica", "Meta-analise"),
    "ensaio controlado": ("Ensaio randomizado controlado", "Ensaio clinico"),
    "experimental sem controle": (),
    "observacional": ("Estudo observacional", "Estudo comparativo"),
    "validação": ("Estudo de validacao",),
    "outro": ("Capitulo de livro", "Trabalho em anais", "Multicentrico"),
}
DESENHO_CATEGORIA = {
    "Revisao de literatura": "revisão",
    "Ensaio randomizado controlado": "ensaio controlado",
    "Randomizado": "ensaio controlado",
    "Pre-pos (intervencao)": "experimental sem controle",
    "Quase-experimental": "experimental sem controle",
    "Transversal": "transversal",
    "Transversal-descritivo": "transversal",
    "Longitudinal": "longitudinal",
    "Coorte": "longitudinal",
    "Caso-controle": "observacional",
    "Estudo de caso": "estudo de caso",
    "Validacao": "validação",
    "Piloto": "experimental sem controle",
}
ORDEM_CATEGORIAS = ["revisão", "ensaio controlado", "experimental sem controle",
                    "transversal", "longitudinal", "observacional",
                    "estudo de caso", "validação", "não especificado", "outro"]


def categoria(tipo: str, desenho: str) -> str:
    """O desenho declarado tem precedência; o tipo entra quando ele falta."""
    d = (desenho or "").strip()
    if d in DESENHO_CATEGORIA:
        return DESENHO_CATEGORIA[d]
    t = (tipo or "").strip()
    for nome, tipos in CATEGORIA.items():
        if t in tipos:
            return nome
    return "não especificado"


def no_escopo(reg: sqlite3.Row, subs: set[str]) -> tuple[bool, set[str]]:
    """Handebol, dentro da janela, com construto psicológico aferido.

    Sem filtro de delineamento, de propósito: a pergunta do panorama inclui as
    revisões.
    """
    ano = (reg["ano"] or "").strip()
    if not ano.isdigit() or not (E.JANELA[0] <= int(ano) <= E.JANELA[1]):
        return False, set()
    plano = E._plano(" ".join(str(reg[c] or "") for c in
                              ("titulo", "resumo", "palavras_chave")))
    if not any(t in plano for t in E.TERMOS_HANDEBOL):
        return False, set()
    instrumentos = P.detectar(reg["titulo"], reg["resumo"], reg["palavras_chave"])
    psico = subs & E.SUBVARIAVEIS_PSICOLOGICAS
    familias = set()
    if instrumentos:
        familias |= P.familias_de(instrumentos)
    familias |= {E.FAMILIA_DE_SUBVARIAVEL[s] for s in psico
                 if s in E.FAMILIA_DE_SUBVARIAVEL}
    if not familias:
        return False, set()
    return True, familias


def levantar(banco: Path = BANCO) -> dict:
    con = sqlite3.connect(banco)
    con.row_factory = sqlite3.Row
    subs: dict[int, set[str]] = {}
    for aid, s in con.execute("SELECT artigo_id, subvariavel FROM artigo_subvariavel"):
        subs.setdefault(aid, set()).add(s)

    registros = list(con.execute("SELECT * FROM artigo ORDER BY id"))
    escopo = []
    for r in registros:
        dentro, familias = no_escopo(r, subs.get(r["id"], set()))
        if dentro:
            escopo.append((r, familias, subs.get(r["id"], set())))

    por_categoria = Counter(categoria(r["tipo_estudo"], r["desenho_estudo"])
                            for r, _, _ in escopo)
    por_familia = Counter(f for _, fams, _ in escopo for f in fams)
    por_sub = Counter(s for _, _, ss in escopo for s in ss
                      if s in E.FAMILIA_DE_SUBVARIAVEL)
    por_ano = Counter(int(r["ano"]) for r, _, _ in escopo)
    por_pais = Counter((r["pais"] or "não declarado").strip() for r, _, _ in escopo)
    por_revista = Counter((r["revista"] or "não declarada").strip()
                          for r, _, _ in escopo)
    por_abordagem = Counter((r["abordagem"] or "não declarada").strip()
                            for r, _, _ in escopo)

    # Cruzamento família por categoria de delineamento: onde está o vazio.
    cruz: dict[str, Counter] = {}
    for r, fams, _ in escopo:
        cat = categoria(r["tipo_estudo"], r["desenho_estudo"])
        for f in fams:
            cruz.setdefault(f, Counter())[cat] += 1

    # Desfechos: a biblioteca guarda a variável analisada em texto livre; o que
    # é comparável entre estudos é a família psicológica e a co-ocorrência com
    # variáveis não psicológicas, que é o que permite validação cruzada.
    NAO_PSICO = {"fisicas", "fisiologicas", "neuromuscular", "biomecanica"}
    vars_por_artigo: dict[int, set[str]] = {}
    for aid, v in con.execute("SELECT artigo_id, variavel FROM artigo_variavel"):
        vars_por_artigo.setdefault(aid, set()).add(v)
    combinado = Counter()
    for r, fams, _ in escopo:
        outras = vars_por_artigo.get(r["id"], set()) & NAO_PSICO
        combinado["psicológica isolada" if not outras
                  else "psicológica combinada com fisiológica ou física"] += 1

    # Onde o humor aparece, e com o quê.
    humor = [(r, ss) for r, fams, ss in escopo if "humor e afeto" in fams]
    humor_com = Counter()
    for r, ss in humor:
        outras = vars_por_artigo.get(r["id"], set()) & NAO_PSICO
        for o in outras:
            humor_com[o] += 1
    humor_cat = Counter(categoria(r["tipo_estudo"], r["desenho_estudo"])
                        for r, _ in humor)

    return {
        "biblioteca": len(registros),
        "escopo": len(escopo),
        "por_categoria": dict(por_categoria),
        "por_familia": dict(por_familia),
        "por_subvariavel": dict(por_sub),
        "por_ano": dict(sorted(por_ano.items())),
        "por_pais": dict(por_pais.most_common(12)),
        "por_revista": dict(por_revista.most_common(12)),
        "por_abordagem": dict(por_abordagem),
        "familia_por_categoria": {f: dict(c) for f, c in cruz.items()},
        "combinacao": dict(combinado),
        "humor": {
            "total": len(humor),
            "por_categoria": dict(humor_cat),
            "combinado_com": dict(humor_com),
        },
    }


def imprimir(p: dict) -> None:
    print(f"biblioteca completa ............ {p['biblioteca']}")
    print(f"no escopo do panorama .......... {p['escopo']}")
    print("  (handebol, 2006 a 2026, com construto psicológico aferido,\n"
          "   sem filtro de delineamento)\n")

    print("── delineamento ──")
    for cat in ORDEM_CATEGORIAS:
        n = p["por_categoria"].get(cat, 0)
        if n:
            print(f"  {n:5d}  {100 * n / p['escopo']:5.1f}%  {cat}")
    print()

    print("── família de variável psicológica ──")
    for f, n in sorted(p["por_familia"].items(), key=lambda x: -x[1]):
        print(f"  {n:5d}  {100 * n / p['escopo']:5.1f}%  {f}")
    print()

    print("── família por delineamento ──")
    cats = [c for c in ORDEM_CATEGORIAS if p["por_categoria"].get(c)]
    largura = max(len(f) for f in p["familia_por_categoria"]) + 1
    cab = "".join(f"{c[:9]:>10s}" for c in cats)
    print(f'  {"família":{largura}s}{cab}')
    for f, c in sorted(p["familia_por_categoria"].items(),
                       key=lambda x: -sum(x[1].values())):
        linha = "".join(f'{c.get(cat, 0):10d}' for cat in cats)
        print(f"  {f:{largura}s}{linha}")
    print()

    print("── combinação de variáveis ──")
    for k, n in sorted(p["combinacao"].items(), key=lambda x: -x[1]):
        print(f"  {n:5d}  {100 * n / p['escopo']:5.1f}%  {k}")
    print()

    h = p["humor"]
    print(f"── humor e afeto: {h['total']} estudos ──")
    for k, n in sorted(h["por_categoria"].items(), key=lambda x: -x[1]):
        print(f"  {n:5d}  {k}")
    print("  combinado com:")
    for k, n in sorted(h["combinado_com"].items(), key=lambda x: -x[1]):
        print(f"    {n:5d}  {k}")
    print()

    print("── produção por ano ──")
    for ano, n in p["por_ano"].items():
        print(f"  {ano}  {'█' * n} {n}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    p = levantar()
    imprimir(p)
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(p, ensure_ascii=False, indent=2))
        print(f"\ngravado: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
