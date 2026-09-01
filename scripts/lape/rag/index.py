"""Indexacao: do arquivo ou da linha do banco ate o vetor gravado.

O indexador e idempotente por hash de conteudo. Reindexar a mesma pasta nao
gera trabalho nem custo: um documento cujo texto nao mudou e pulado antes
de qualquer chamada de embedding.
"""
from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from . import config
from .chunk import Document, ExtractionError, load, split
from .embed import Embedder, get_embedder
from .store import SqliteStore, VectorStore

log = logging.getLogger("lape.rag.index")


@dataclass
class Relatorio:
    documentos: int = 0
    indexados: int = 0
    pulados: int = 0
    falhas: int = 0
    trechos: int = 0
    tokens: int = 0
    ms: int = 0
    modelo: str = ""
    erros: list[str] = field(default_factory=list)

    def resumo(self) -> str:
        return (f"{self.indexados} documentos indexados, {self.pulados} sem mudanca, "
                f"{self.falhas} com falha; {self.trechos} trechos, "
                f"~{self.tokens} tokens, {self.ms} ms, modelo {self.modelo}")


def varrer(dirs: Iterable[Path]) -> Iterator[Path]:
    """Percorre as pastas e devolve os arquivos indexaveis."""
    for base in dirs:
        base = Path(base)
        if base.is_file():
            if base.suffix.lower() in config.SUPPORTED_SUFFIXES:
                yield base
            continue
        if not base.exists():
            log.warning("pasta inexistente, ignorada: %s", base)
            continue
        for caminho in sorted(base.rglob("*")):
            if caminho.is_file() and caminho.suffix.lower() in config.SUPPORTED_SUFFIXES:
                yield caminho


def indexar_documentos(store: VectorStore, docs: Iterable[Document],
                       embedder: Embedder | None = None,
                       reindexar: bool = False,
                       verbose: bool = True) -> Relatorio:
    """Indexa uma sequencia de documentos ja carregados em memoria."""
    inicio = time.time()
    emb = embedder or get_embedder()
    rel = Relatorio(modelo=emb.model)
    for doc in docs:
        rel.documentos += 1
        try:
            doc_id, mudou = store.upsert_document(doc)
            if not mudou and not reindexar:
                rel.pulados += 1
                if verbose:
                    print(f"  = {doc.uri[-70:]}")
                continue
            trechos = split(doc.text)
            if not trechos:
                rel.falhas += 1
                rel.erros.append(f"{doc.uri}: texto vazio apos a divisao")
                continue
            vetores = emb.embed_documents([t.text for t in trechos])
            store.replace_chunks(doc_id, trechos, vetores, emb.model)
            rel.indexados += 1
            rel.trechos += len(trechos)
            rel.tokens += sum(t.n_tokens for t in trechos)
            if verbose:
                print(f"  + {doc.uri[-70:]}  ({len(trechos)} trechos)")
        except Exception as exc:
            rel.falhas += 1
            rel.erros.append(f"{doc.uri}: {exc}")
            log.warning("falha ao indexar %s: %s", doc.uri, exc)
    rel.ms = int(1000 * (time.time() - inicio))
    if isinstance(store, SqliteStore):
        store.log_run("index", model=emb.model, n_docs=rel.indexados,
                      n_chunks=rel.trechos, n_tokens=rel.tokens, ms=rel.ms)
    return rel


def indexar_pastas(store: VectorStore, dirs: Iterable[Path] | None = None,
                   kind: str = "externo", embedder: Embedder | None = None,
                   reindexar: bool = False, verbose: bool = True) -> Relatorio:
    """Indexa todos os arquivos suportados das pastas informadas."""
    caminhos = list(varrer(dirs or config.CORPUS_DIRS))
    if verbose:
        print(f"{len(caminhos)} arquivos encontrados")

    def gerar() -> Iterator[Document]:
        for caminho in caminhos:
            try:
                yield load(caminho, kind=kind)
            except ExtractionError as exc:
                log.warning("%s", exc)
                print(f"  ! {exc}")

    return indexar_documentos(store, gerar(), embedder, reindexar, verbose)


# ------------------------------------------------------- corpus do proprio banco
def docs_do_banco(conn: sqlite3.Connection, tabelas: tuple[str, ...] = ("articles", "refs"),
                  limite: int | None = None) -> Iterator[Document]:
    """Transforma o que ja esta no banco do LAPE em documentos indexaveis.

    Artigos e referencias de revisao viram documentos de titulo mais resumo.
    E pouco texto por registro, mas e exatamente o texto que a triagem e a
    escrita precisam recuperar.
    """
    conn.row_factory = sqlite3.Row
    for tabela in tabelas:
        try:
            colunas = {r["name"] for r in conn.execute(f"PRAGMA table_info({tabela})")}
        except sqlite3.Error:
            continue
        if not colunas:
            continue
        campos = [c for c in ("id", "title", "titulo", "abstract", "resumo", "year",
                              "ano", "doi", "journal", "periodico", "authors",
                              "autores", "venue") if c in colunas]
        if "id" not in campos:
            continue
        sql = f"SELECT {','.join(campos)} FROM {tabela}"
        if limite:
            sql += f" LIMIT {int(limite)}"
        for linha in conn.execute(sql):
            d = dict(linha)
            titulo = d.get("title") or d.get("titulo") or ""
            resumo = d.get("abstract") or d.get("resumo") or ""
            texto = "\n\n".join(p for p in (titulo, resumo) if p).strip()
            if len(texto) < 60:
                continue
            yield Document(
                uri=f"lape://{tabela}/{d['id']}",
                text=texto,
                kind="article" if tabela == "articles" else "ref",
                title=titulo or None,
                authors=d.get("authors") or d.get("autores"),
                year=d.get("year") or d.get("ano"),
                source=d.get("journal") or d.get("periodico") or d.get("venue"),
                doi=d.get("doi"),
                ref_table=tabela,
                ref_id=int(d["id"]),
            )
