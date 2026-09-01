"""Peca comum aos quatro agentes."""
from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from .. import config
from ..search import Resultado, buscar
from ..store import Filtro, SqliteStore, VectorStore

log = logging.getLogger("lape.rag.agents")

DISCIPLINA = """\
Regras que valem para toda resposta sua:

1. Fundamentacao. Voce so afirma o que os trechos recuperados sustentam.
   Quando o corpus nao responde, voce diz que nao responde e aponta que
   busca faltou — nunca completa a lacuna com conhecimento geral sem
   marcar isso de forma explicita.
2. Rastreabilidade. Cada afirmacao substantiva carrega a marca do trecho
   que a sustenta, no formato [n] correspondente ao contexto fornecido.
3. Precisao numerica. Numeros vem do trecho, nunca de estimativa. Se um
   numero aparece arredondado de formas diferentes em trechos distintos,
   voce assinala a divergencia em vez de escolher um deles em silencio.
4. Lingua. Voce escreve em portugues do Brasil, em registro academico
   culto, sem gerundio e sem floreio.
"""


@dataclass
class SaidaAgente:
    agente: str
    texto: str
    fontes: list[dict] = field(default_factory=list)
    consultas: list[str] = field(default_factory=list)
    uso: dict = field(default_factory=dict)
    aviso: str | None = None

    def to_dict(self) -> dict:
        return {"agente": self.agente, "texto": self.texto, "fontes": self.fontes,
                "consultas": self.consultas, "uso": self.uso, "aviso": self.aviso}

    def imprimir(self) -> None:
        if self.aviso:
            print(f"[aviso] {self.aviso}\n")
        print(self.texto)
        if self.fontes:
            print("\nFontes recuperadas")
            for f in self.fontes:
                titulo = (f.get("titulo") or f["uri"])[:70]
                print(f"  [{f['n']}] {titulo}  {f['citacao']}")
        if self.uso:
            print(f"\n({self.uso.get('entrada',0)} tokens de entrada, "
                  f"{self.uso.get('saida',0)} de saida, "
                  f"cache {self.uso.get('cache_lido',0)})")


def recuperar(store: VectorStore, consultas: list[str], k: int = 8,
              filtro: Filtro | None = None,
              embedder=None) -> tuple[str, list[dict], str | None]:
    """Roda varias consultas e devolve um contexto unico, sem repetir trecho."""
    vistos: set[int] = set()
    hits = []
    aviso = None
    for consulta in consultas:
        r = buscar(store, consulta, k=k, filtro=filtro, embedder=embedder)
        aviso = aviso or r.aviso
        for h in r.hits:
            if h.chunk_id not in vistos:
                vistos.add(h.chunk_id)
                hits.append(h)
    combinado = Resultado(consulta=" | ".join(consultas), hits=hits)
    return combinado.contexto(), combinado.fontes(), aviso


def registrar(store: VectorStore, agente: str, consulta: str, uso: dict) -> None:
    if isinstance(store, SqliteStore):
        store.log_run("agent", agent=agente, query=consulta[:500],
                      model=uso.get("modelo", ""), n_tokens=uso.get("saida", 0),
                      detail=json.dumps(uso, ensure_ascii=False))
