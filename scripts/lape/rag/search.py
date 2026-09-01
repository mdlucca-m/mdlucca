"""Busca hibrida: vetor e BM25 fundidos num unico ranking.

A fusao usa Reciprocal Rank Fusion. Ela combina posicoes, nao pontuacoes,
e por isso nao exige que a similaridade do cosseno e o BM25 estejam na
mesma escala — o que nenhuma normalizacao ad hoc consegue garantir quando o
corpus muda de tamanho.

    score(d) = w * 1/(k + posicao_densa(d)) + (1-w) * 1/(k + posicao_lexica(d))
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from . import config
from .embed import Embedder, get_embedder
from .store import Filtro, Hit, VectorStore

log = logging.getLogger("lape.rag.search")


@dataclass
class Resultado:
    consulta: str
    hits: list[Hit]
    ms: int = 0
    densa: int = 0
    lexica: int = 0
    semantico: bool = True
    aviso: str | None = None

    def contexto(self, max_chars: int = 12000, numerar: bool = True) -> str:
        """Monta o bloco de contexto que vai ao modelo, ja com as fontes."""
        partes: list[str] = []
        total = 0
        for i, h in enumerate(self.hits, 1):
            cabeca = f"[{i}] {h.citacao()}" if numerar else h.citacao()
            titulo = f"\n{h.title}" if h.title else ""
            corpo = f"{cabeca}{titulo}\n{h.text}\n"
            if total + len(corpo) > max_chars:
                break
            partes.append(corpo)
            total += len(corpo)
        return "\n".join(partes)

    def fontes(self) -> list[dict]:
        return [{"n": i, "citacao": h.citacao(), "uri": h.uri, "titulo": h.title,
                 "doi": h.doi, "ano": h.year, "secao": h.section,
                 "trecho": h.ordinal, "score": round(h.score, 4)}
                for i, h in enumerate(self.hits, 1)]


def buscar(store: VectorStore, consulta: str, k: int | None = None,
           filtro: Filtro | None = None, embedder: Embedder | None = None,
           peso_denso: float | None = None,
           candidatos: int | None = None) -> Resultado:
    """Recupera os k trechos mais relevantes para a consulta."""
    inicio = time.time()
    k = k or config.TOP_K
    candidatos = candidatos or max(config.CANDIDATES, k * 4)
    peso = config.DENSE_WEIGHT if peso_denso is None else peso_denso
    emb = embedder or get_embedder()

    densos: list[Hit] = []
    if peso > 0:
        try:
            qvec = emb.embed_query(consulta)
            densos = store.search_dense(qvec, candidatos, filtro)
        except Exception as exc:                     # busca degrada, nao quebra
            log.warning("busca densa indisponivel (%s); seguindo so com BM25", exc)
            peso = 0.0

    lexicos: list[Hit] = []
    if peso < 1:
        lexicos = store.search_lexical(consulta, candidatos, filtro)

    hits = _fundir(densos, lexicos, peso, k)
    aviso = None
    if not emb.semantic:
        aviso = ("busca sem modelo semantico: o ranking vem de sobreposicao de forma, "
                 "nao de sentido. Defina VOYAGE_API_KEY ou instale "
                 "sentence-transformers e reindexe.")
    return Resultado(consulta=consulta, hits=hits,
                     ms=int(1000 * (time.time() - inicio)),
                     densa=len(densos), lexica=len(lexicos),
                     semantico=emb.semantic, aviso=aviso)


def _fundir(densos: list[Hit], lexicos: list[Hit], peso: float, k: int) -> list[Hit]:
    kk = config.RRF_K
    notas: dict[int, float] = {}
    origem: dict[int, set[str]] = {}
    guarda: dict[int, Hit] = {}
    detalhe: dict[int, dict] = {}

    for lista, w, rotulo in ((densos, peso, "densa"), (lexicos, 1 - peso, "lexica")):
        for posicao, h in enumerate(lista, 1):
            notas[h.chunk_id] = notas.get(h.chunk_id, 0.0) + w / (kk + posicao)
            origem.setdefault(h.chunk_id, set()).add(rotulo)
            guarda.setdefault(h.chunk_id, h)
            detalhe.setdefault(h.chunk_id, {})[f"pos_{rotulo}"] = posicao
            detalhe[h.chunk_id][f"score_{rotulo}"] = round(h.score, 4)

    ordenados = sorted(notas.items(), key=lambda item: -item[1])[:k]
    saida: list[Hit] = []
    for chunk_id, nota in ordenados:
        h = guarda[chunk_id]
        h.score = nota
        h.origem = "fusao" if len(origem[chunk_id]) > 1 else next(iter(origem[chunk_id]))
        h.detalhe = detalhe[chunk_id]
        saida.append(h)
    return saida


def vizinhos(store: VectorStore, chunk_id: int, k: int = 5) -> list[Hit]:
    """Trechos semelhantes a um trecho ja conhecido.

    Serve para 'mostre-me o que mais diz isto' e para detectar redundancia
    entre capitulos da propria tese.
    """
    base = store.get_chunks([chunk_id])
    if not base:
        return []
    emb = get_embedder()
    qvec = emb.embed_query(base[0].text[:2000])
    achados = store.search_dense(qvec, k + 1)
    return [h for h in achados if h.chunk_id != chunk_id][:k]
