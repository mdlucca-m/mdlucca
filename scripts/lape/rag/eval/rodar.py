# -*- coding: utf-8 -*-
"""Mede a recuperacao contra o conjunto de avaliacao.

Compara tres configuracoes sobre o mesmo indice — so vetor, so BM25 e a
fusao — nas mesmas consultas. A metrica principal e a cobertura em k: a
proporcao de perguntas cuja resposta aparece em algum dos k trechos
devolvidos. A secundaria e o posto reciproco medio, que premia a resposta
que chega no topo e nao apenas dentro da lista.

    python3 -m lape.rag.eval.rodar --db banco.sqlite --k 1 3 5 10
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
import time
import unicodedata
from pathlib import Path

from ..search import buscar
from ..store import SqliteStore
from .consultas import CONSULTAS


def _norm(texto: str) -> str:
    """Compara sem acento e sem caixa: '72,3%' precisa casar com '72,3 %'."""
    sem = "".join(c for c in unicodedata.normalize("NFD", texto)
                  if unicodedata.category(c) != "Mn")
    return sem.lower().replace(" ", "")


def acertou(texto: str, alvos: tuple[str, ...]) -> bool:
    corpo = _norm(texto)
    return any(_norm(a) in corpo for a in alvos)


def avaliar(store: SqliteStore, peso: float, ks: list[int],
            embedder=None) -> dict:
    maior = max(ks)
    postos: list[float] = []
    acertos = {k: 0 for k in ks}
    tempos: list[int] = []
    falhas: list[str] = []
    for pergunta, alvos, _doc in CONSULTAS:
        r = buscar(store, pergunta, k=maior, peso_denso=peso, embedder=embedder)
        tempos.append(r.ms)
        posicao = next((i for i, h in enumerate(r.hits, 1)
                        if acertou(h.text, alvos)), None)
        for k in ks:
            if posicao is not None and posicao <= k:
                acertos[k] += 1
        postos.append(1.0 / posicao if posicao else 0.0)
        if posicao is None:
            falhas.append(pergunta)
    n = len(CONSULTAS)
    return {
        "peso_denso": peso,
        "n": n,
        "cobertura": {k: round(100 * acertos[k] / n, 1) for k in ks},
        "posto_reciproco": round(statistics.mean(postos), 3),
        "ms_mediano": int(statistics.median(tempos)),
        "sem_resposta": falhas,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--k", type=int, nargs="+", default=[1, 3, 5, 10])
    p.add_argument("--pesos", type=float, nargs="+", default=[1.0, 0.0, 0.6])
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    store = SqliteStore(conn)
    saida = []
    for peso in args.pesos:
        saida.append(avaliar(store, peso, args.k))
    conn.close()

    if args.json:
        print(json.dumps(saida, ensure_ascii=False, indent=2))
        return 0
    rotulo = {1.0: "so vetor", 0.0: "so BM25"}
    cabeca = f"{'configuracao':<16}" + "".join(f"{'C@'+str(k):>8}" for k in args.k)
    print(cabeca + f"{'PRM':>8}{'ms':>6}")
    print("-" * len(cabeca + "        " + "      "))
    for linha in saida:
        nome = rotulo.get(linha["peso_denso"], f"fusao w={linha['peso_denso']}")
        print(f"{nome:<16}"
              + "".join(f"{linha['cobertura'][k]:>7.1f}%" for k in args.k)
              + f"{linha['posto_reciproco']:>8.3f}{linha['ms_mediano']:>6}")
    print(f"\nC@k = cobertura em k (% das {saida[0]['n']} perguntas cuja resposta "
          "aparece nos k primeiros trechos)")
    print("PRM = posto reciproco medio")
    for linha in saida:
        if linha["sem_resposta"]:
            nome = rotulo.get(linha["peso_denso"], f"fusao w={linha['peso_denso']}")
            print(f"\nsem resposta em {nome} ({len(linha['sem_resposta'])}):")
            for q in linha["sem_resposta"][:8]:
                print(f"  - {q}")
    return 0


if __name__ == "__main__":                             # pragma: no cover
    sys.exit(main())
