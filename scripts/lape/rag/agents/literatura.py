"""Agente de literatura.

Vigia as bases externas nos temas do pesquisador, indexa o que aparece e
separa o que e realmente novo. A deduplicacao acontece em duas camadas: por
identificador, contra o que ja esta no banco do LAPE, e por semelhanca
semantica, contra o que ja esta no indice — o que apanha o mesmo estudo
publicado com titulo diferente em preprint e em periodico.
"""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field

from ... import sources
from ...util import clean_text, norm_key
from .. import config
from ..chunk import Document
from ..index import indexar_documentos
from ..llm import LLMIndisponivel, perguntar
from ..search import buscar
from ..store import Filtro, SqliteStore, VectorStore
from .base import DISCIPLINA, SaidaAgente, registrar

log = logging.getLogger("lape.rag.agents.literatura")

SISTEMA = DISCIPLINA + """
Voce triagem novidade bibliografica para um pesquisador especifico.

Para cada estudo apresentado, decida entre tres rotulos:
  RELEVANTE   responde a uma das perguntas do pesquisador e acrescenta algo
              que o corpus dele ainda nao contem
  MARGINAL    toca o tema mas repete o que ele ja tem, ou o desenho e fraco
              demais para o uso pretendido
  FORA        nao pertence ao escopo

Formato: uma linha por estudo, no padrao
  ROTULO | primeiro autor, ano | por que, em ate vinte palavras

Depois da lista, escreva um paragrafo curto sobre o que o conjunto sugere
para a agenda do pesquisador. Seja severo: um rotulo RELEVANTE que nao se
sustente custa mais tempo dele do que um MARGINAL a mais.
"""


@dataclass
class Achado:
    titulo: str
    ano: int | None
    doi: str | None
    autores: str | None
    resumo: str
    fonte: str
    similar_a: str | None = None
    similaridade: float = 0.0

    def novo(self, limiar: float = 0.86) -> bool:
        return self.similaridade < limiar


def _da_pubmed(termo: str, limite: int) -> list[Achado]:
    achados: list[Achado] = []
    try:
        pmids = sources.pubmed_search(termo, retmax=limite)
        for reg in sources.pubmed_summaries(pmids):
            titulo = clean_text(reg.get("title") or reg.get("titulo") or "")
            if not titulo:
                continue
            achados.append(Achado(
                titulo=titulo,
                ano=reg.get("year") or reg.get("ano"),
                doi=reg.get("doi"),
                autores=reg.get("authors") or reg.get("autores"),
                resumo=clean_text(reg.get("abstract") or reg.get("resumo") or ""),
                fonte="PubMed"))
    except Exception as exc:
        log.warning("PubMed falhou para %r: %s", termo, exc)
    return achados


def _do_openalex(termo: str, limite: int, mailto: str | None) -> list[Achado]:
    achados: list[Achado] = []
    try:
        dados = sources._get(f"{sources.OPENALEX}/works", {
            "search": termo, "per-page": min(limite, 50), "mailto": mailto,
            "sort": "publication_date:desc"})
        for obra in (dados or {}).get("results", []):
            reg = sources._openalex_work(obra)
            titulo = clean_text(reg.get("title") or "")
            if not titulo:
                continue
            achados.append(Achado(
                titulo=titulo, ano=reg.get("year"), doi=reg.get("doi"),
                autores=reg.get("authors"),
                resumo=clean_text(reg.get("abstract") or ""), fonte="OpenAlex"))
    except Exception as exc:
        log.warning("OpenAlex falhou para %r: %s", termo, exc)
    return achados


def coletar(temas: list[str], limite: int = 20,
            mailto: str | None = None) -> list[Achado]:
    """Busca nas bases e devolve os achados sem duplicata de identificador."""
    vistos: set[str] = set()
    saida: list[Achado] = []
    for tema in temas:
        for achado in _da_pubmed(tema, limite) + _do_openalex(tema, limite, mailto):
            chave = (achado.doi or "").lower() or norm_key(achado.titulo)
            if not chave or chave in vistos:
                continue
            vistos.add(chave)
            saida.append(achado)
    return saida


def marcar_conhecidos(store: VectorStore, achados: list[Achado],
                      limiar: float = 0.86) -> None:
    """Anota, para cada achado, o quanto ele ja e coberto pelo indice."""
    for achado in achados:
        consulta = f"{achado.titulo}. {achado.resumo[:600]}"
        try:
            r = buscar(store, consulta, k=1)
        except Exception as exc:
            log.debug("comparacao semantica falhou: %s", exc)
            continue
        if r.hits:
            achado.similaridade = float(r.hits[0].score)
            achado.similar_a = r.hits[0].title or r.hits[0].uri
            # Com fusao RRF a pontuacao nao e cosseno; usamos a densa quando ha.
            densa = r.hits[0].detalhe.get("score_densa")
            if densa is not None:
                achado.similaridade = float(densa)


def executar(store: VectorStore, temas: list[str], *,
             limite: int = 20, indexar: bool = True,
             triar: bool = True, limiar: float = 0.86,
             mailto: str | None = None) -> SaidaAgente:
    achados = coletar(temas, limite=limite, mailto=mailto)
    if not achados:
        return SaidaAgente(agente="literatura", consultas=temas,
                           texto="Nenhum registro devolvido pelas bases.")
    marcar_conhecidos(store, achados, limiar)
    novos = [a for a in achados if a.novo(limiar)]

    indexados = 0
    if indexar and novos:
        docs = [Document(
            uri=f"doi:{a.doi}" if a.doi else f"titulo:{norm_key(a.titulo)}",
            text=f"{a.titulo}\n\n{a.resumo}".strip(), kind="externo",
            title=a.titulo, authors=a.autores, year=a.ano, source=a.fonte,
            doi=a.doi, meta={"origem": "agente_literatura", "temas": temas})
            for a in novos if len(a.resumo) > 40]
        rel = indexar_documentos(store, docs, verbose=False)
        indexados = rel.indexados

    cabecalho = (f"{len(achados)} registros nas bases; {len(novos)} sem cobertura "
                 f"no indice; {indexados} indexados agora.\n")
    if not triar:
        linhas = [f"- {a.titulo[:100]} ({a.ano or 's.d.'}, {a.fonte})"
                  for a in novos[:60]]
        return SaidaAgente(agente="literatura", consultas=temas,
                           texto=cabecalho + "\n".join(linhas))

    lista = "\n\n".join(
        f"[{i}] {a.titulo}\nAutores: {a.autores or '?'} | Ano: {a.ano or '?'} | "
        f"Fonte: {a.fonte} | DOI: {a.doi or '—'}\nResumo: {a.resumo[:900]}"
        for i, a in enumerate(novos[:40], 1))
    pedido = (f"Temas de interesse do pesquisador: {'; '.join(temas)}.\n\n"
              f"Estudos encontrados e ainda nao cobertos pelo corpus dele:\n\n{lista}")
    try:
        r = perguntar(SISTEMA, [{"role": "user", "content": pedido}])
    except LLMIndisponivel as exc:
        return SaidaAgente(agente="literatura", consultas=temas,
                           texto=cabecalho + f"\nTriagem automatica indisponivel: {exc}\n\n"
                                 + "\n".join(f"- {a.titulo[:110]}" for a in novos[:60]))
    uso = {"modelo": r.modelo, "entrada": r.entrada, "saida": r.saida,
           "cache_lido": r.cache_lido, "custo_estimado": round(r.custo_estimado, 4)}
    registrar(store, "literatura", "; ".join(temas), uso)
    return SaidaAgente(agente="literatura", texto=cabecalho + "\n" + (r.recusa or r.texto),
                       consultas=temas, uso=uso)
