"""Armazenamento e busca de vetores.

Uma interface, duas implementacoes. ``SqliteStore`` guarda tudo no mesmo
arquivo que o resto do LAPE e faz a busca densa por produto escalar sobre
uma matriz em memoria — exato, sem indice aproximado, adequado ate a ordem
de 100 mil trechos. ``PgVectorStore`` fala com Postgres e delega a busca ao
indice HNSW do pgvector, para quando o corpus passar disso.

A troca e uma variavel de ambiente. Nenhum chamador precisa mudar:

    LAPE_VECTOR_STORE=pgvector  LAPE_PG_DSN=postgresql://...
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from . import config
from .chunk import Chunk, Document

log = logging.getLogger("lape.rag.store")


@dataclass
class Hit:
    """Um trecho recuperado, com tudo o que a citacao precisa."""
    chunk_id: int
    doc_id: int
    score: float
    text: str
    uri: str
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    kind: str | None = None
    doi: str | None = None
    section: str | None = None
    ordinal: int = 0
    origem: str = "densa"          # densa | lexica | fusao
    detalhe: dict = field(default_factory=dict)

    def citacao(self) -> str:
        """Referencia curta e rastreavel ate o trecho."""
        autor = (self.authors or "").split(";")[0].split(",")[0].strip()
        ano = self.year or "s.d."
        onde = f", {self.section}" if self.section else ""
        base = f"{autor.upper()}, {ano}" if autor else (self.title or self.uri)[:60]
        return f"[{base}{onde}, trecho {self.ordinal}]"


@dataclass
class Filtro:
    kinds: Sequence[str] | None = None
    anos: tuple[int | None, int | None] | None = None
    doc_ids: Sequence[int] | None = None
    ref_table: str | None = None
    uri_prefix: str | None = None

    def sql(self, alias: str = "d") -> tuple[str, list[Any]]:
        partes: list[str] = []
        args: list[Any] = []
        if self.kinds:
            partes.append(f"{alias}.kind IN ({','.join('?' * len(self.kinds))})")
            args.extend(self.kinds)
        if self.anos:
            de, ate = self.anos
            if de is not None:
                partes.append(f"{alias}.year >= ?"); args.append(de)
            if ate is not None:
                partes.append(f"{alias}.year <= ?"); args.append(ate)
        if self.doc_ids:
            partes.append(f"{alias}.id IN ({','.join('?' * len(self.doc_ids))})")
            args.extend(self.doc_ids)
        if self.ref_table:
            partes.append(f"{alias}.ref_table = ?"); args.append(self.ref_table)
        if self.uri_prefix:
            partes.append(f"{alias}.uri LIKE ?"); args.append(f"{self.uri_prefix}%")
        return (" AND ".join(partes) if partes else "1=1"), args


class VectorStore:
    """Contrato que as duas implementacoes cumprem."""

    def ensure_schema(self) -> None: raise NotImplementedError
    def upsert_document(self, doc: Document) -> tuple[int, bool]: raise NotImplementedError
    def replace_chunks(self, doc_id: int, chunks: list[Chunk],
                       vetores: np.ndarray, model: str) -> int: raise NotImplementedError
    def search_dense(self, qvec: np.ndarray, k: int,
                     filtro: Filtro | None = None) -> list[Hit]: raise NotImplementedError
    def search_lexical(self, consulta: str, k: int,
                       filtro: Filtro | None = None) -> list[Hit]: raise NotImplementedError
    def delete_document(self, uri: str) -> bool: raise NotImplementedError
    def stats(self) -> dict: raise NotImplementedError
    def get_chunks(self, ids: Sequence[int]) -> list[Hit]: raise NotImplementedError


# ------------------------------------------------------------------ SQLite
class SqliteStore(VectorStore):
    def __init__(self, conn: sqlite3.Connection, model: str | None = None) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.model = model
        self._mat: np.ndarray | None = None
        self._ids: np.ndarray | None = None
        self._mat_model: str | None = None

    # -------------------------------------------------------------- schema
    def ensure_schema(self) -> None:
        if not config.SQL_RAG.exists():
            raise FileNotFoundError(f"esquema do RAG nao encontrado: {config.SQL_RAG}")
        self.conn.executescript(config.SQL_RAG.read_text(encoding="utf-8"))
        self.conn.commit()

    # ---------------------------------------------------------- documentos
    def upsert_document(self, doc: Document) -> tuple[int, bool]:
        """Grava o documento. Devolve (id, mudou).

        ``mudou`` e falso quando o hash do conteudo bate com o que ja estava
        gravado — nesse caso o chamador pode pular a reindexacao inteira.
        """
        atual = self.conn.execute(
            "SELECT id, content_hash FROM rag_documents WHERE uri = ?",
            (doc.uri,)).fetchone()
        campos = dict(
            uri=doc.uri, kind=doc.kind, title=doc.title, authors=doc.authors,
            year=doc.year, source=doc.source, doi=doc.doi, lang=doc.lang,
            ref_table=doc.ref_table, ref_id=doc.ref_id,
            content_hash=doc.content_hash, n_chars=len(doc.text),
            meta=json.dumps(doc.meta, ensure_ascii=False) if doc.meta else None,
        )
        if atual is None:
            cols = ",".join(campos)
            marks = ",".join("?" * len(campos))
            cur = self.conn.execute(
                f"INSERT INTO rag_documents({cols}) VALUES ({marks})",
                list(campos.values()))
            self.conn.commit()
            return int(cur.lastrowid), True
        mudou = atual["content_hash"] != doc.content_hash
        sets = ",".join(f"{c} = ?" for c in campos)
        self.conn.execute(
            f"UPDATE rag_documents SET {sets}, updated_at = datetime('now') WHERE id = ?",
            list(campos.values()) + [atual["id"]])
        self.conn.commit()
        return int(atual["id"]), mudou

    def replace_chunks(self, doc_id: int, chunks: list[Chunk],
                       vetores: np.ndarray, model: str) -> int:
        if len(chunks) != len(vetores):
            raise ValueError(
                f"{len(chunks)} trechos para {len(vetores)} vetores: contagem incompativel")
        self.conn.execute("DELETE FROM rag_chunks WHERE doc_id = ?", (doc_id,))
        for c, v in zip(chunks, vetores):
            cur = self.conn.execute(
                "INSERT INTO rag_chunks(doc_id, ordinal, section, text, n_tokens,"
                " char_start, char_end) VALUES (?,?,?,?,?,?,?)",
                (doc_id, c.ordinal, c.section, c.text, c.n_tokens,
                 c.char_start, c.char_end))
            arr = np.asarray(v, dtype=np.float32)
            self.conn.execute(
                "INSERT INTO rag_vectors(chunk_id, model, dim, norm, vec)"
                " VALUES (?,?,?,?,?)",
                (int(cur.lastrowid), model, int(arr.shape[0]),
                 float(np.linalg.norm(arr)), arr.tobytes()))
        self.conn.execute(
            "UPDATE rag_documents SET n_chunks = ?, updated_at = datetime('now')"
            " WHERE id = ?", (len(chunks), doc_id))
        self.conn.commit()
        self._mat = None                       # a matriz em cache envelheceu
        return len(chunks)

    def delete_document(self, uri: str) -> bool:
        cur = self.conn.execute("DELETE FROM rag_documents WHERE uri = ?", (uri,))
        self.conn.commit()
        self._mat = None
        return cur.rowcount > 0

    # ------------------------------------------------------------- buscas
    def _carregar_matriz(self, model: str) -> tuple[np.ndarray, np.ndarray]:
        """Le todos os vetores do modelo para memoria, uma vez."""
        if self._mat is not None and self._mat_model == model:
            return self._mat, self._ids
        inicio = time.time()
        linhas = self.conn.execute(
            "SELECT chunk_id, dim, vec FROM rag_vectors WHERE model = ?"
            " ORDER BY chunk_id", (model,)).fetchall()
        if not linhas:
            self._mat = np.zeros((0, 1), dtype=np.float32)
            self._ids = np.zeros((0,), dtype=np.int64)
            self._mat_model = model
            return self._mat, self._ids
        dim = int(linhas[0]["dim"])
        mat = np.empty((len(linhas), dim), dtype=np.float32)
        ids = np.empty(len(linhas), dtype=np.int64)
        for i, linha in enumerate(linhas):
            if int(linha["dim"]) != dim:
                raise ValueError(
                    "vetores de dimensoes diferentes no mesmo modelo; "
                    "reindexe com 'lape_agent.py rag indexar --reindexar'")
            mat[i] = np.frombuffer(linha["vec"], dtype=np.float32, count=dim)
            ids[i] = int(linha["chunk_id"])
        self._mat, self._ids, self._mat_model = mat, ids, model
        log.debug("matriz carregada: %d x %d em %.0f ms",
                  mat.shape[0], mat.shape[1], 1000 * (time.time() - inicio))
        return mat, ids

    def search_dense(self, qvec: np.ndarray, k: int,
                     filtro: Filtro | None = None) -> list[Hit]:
        model = self.model or self._modelo_dominante()
        if model is None:
            return []
        mat, ids = self._carregar_matriz(model)
        if mat.shape[0] == 0:
            return []
        q = np.asarray(qvec, dtype=np.float32).reshape(-1)
        if q.shape[0] != mat.shape[1]:
            raise ValueError(
                f"a consulta tem {q.shape[0]} dimensoes e o indice tem {mat.shape[1]}; "
                "o modelo de embedding mudou — reindexe o corpus")
        permitidos = self._ids_permitidos(filtro)
        pontos = mat @ q
        if permitidos is not None:
            mascara = np.isin(ids, permitidos)
            if not mascara.any():
                return []
            pontos = np.where(mascara, pontos, -np.inf)
        n = min(k, int(np.isfinite(pontos).sum()))
        if n <= 0:
            return []
        topo = np.argpartition(-pontos, n - 1)[:n]
        topo = topo[np.argsort(-pontos[topo])]
        alvo = [int(ids[i]) for i in topo]
        notas = {int(ids[i]): float(pontos[i]) for i in topo}
        hits = self.get_chunks(alvo)
        for h in hits:
            h.score = notas[h.chunk_id]
            h.origem = "densa"
        return sorted(hits, key=lambda h: -h.score)

    def search_lexical(self, consulta: str, k: int,
                       filtro: Filtro | None = None) -> list[Hit]:
        termos = _fts_query(consulta)
        if not termos:
            return []
        onde, args = (filtro or Filtro()).sql("d")
        sql = (
            "SELECT c.id AS chunk_id, c.doc_id, c.text, c.section, c.ordinal,"
            "       d.uri, d.title, d.authors, d.year, d.kind, d.doi,"
            "       bm25(rag_fts) AS bm"
            "  FROM rag_fts JOIN rag_chunks c ON c.id = rag_fts.rowid"
            "  JOIN rag_documents d ON d.id = c.doc_id"
            f" WHERE rag_fts MATCH ? AND {onde}"
            "  ORDER BY bm LIMIT ?"
        )
        try:
            linhas = self.conn.execute(sql, [termos] + args + [k]).fetchall()
        except sqlite3.OperationalError as exc:
            log.warning("busca lexica falhou (%s); consulta: %r", exc, termos)
            return []
        # bm25 do SQLite e melhor quanto menor; invertemos para virar pontuacao.
        return [Hit(chunk_id=l["chunk_id"], doc_id=l["doc_id"], score=-float(l["bm"]),
                    text=l["text"], uri=l["uri"], title=l["title"],
                    authors=l["authors"], year=l["year"], kind=l["kind"],
                    doi=l["doi"], section=l["section"], ordinal=l["ordinal"],
                    origem="lexica") for l in linhas]

    def get_chunks(self, ids: Sequence[int]) -> list[Hit]:
        if not ids:
            return []
        marks = ",".join("?" * len(ids))
        linhas = self.conn.execute(
            "SELECT c.id AS chunk_id, c.doc_id, c.text, c.section, c.ordinal,"
            "       d.uri, d.title, d.authors, d.year, d.kind, d.doi"
            "  FROM rag_chunks c JOIN rag_documents d ON d.id = c.doc_id"
            f" WHERE c.id IN ({marks})", list(ids)).fetchall()
        return [Hit(chunk_id=l["chunk_id"], doc_id=l["doc_id"], score=0.0,
                    text=l["text"], uri=l["uri"], title=l["title"],
                    authors=l["authors"], year=l["year"], kind=l["kind"],
                    doi=l["doi"], section=l["section"], ordinal=l["ordinal"])
                for l in linhas]

    # ------------------------------------------------------------ apoio
    def _ids_permitidos(self, filtro: Filtro | None) -> np.ndarray | None:
        if filtro is None:
            return None
        onde, args = filtro.sql("d")
        if onde == "1=1":
            return None
        linhas = self.conn.execute(
            "SELECT c.id FROM rag_chunks c JOIN rag_documents d ON d.id = c.doc_id"
            f" WHERE {onde}", args).fetchall()
        return np.array([l[0] for l in linhas], dtype=np.int64)

    def _modelo_dominante(self) -> str | None:
        linha = self.conn.execute(
            "SELECT model, COUNT(*) n FROM rag_vectors GROUP BY model"
            " ORDER BY n DESC LIMIT 1").fetchone()
        return linha["model"] if linha else None

    def stats(self) -> dict:
        def um(sql: str, *a):
            linha = self.conn.execute(sql, a).fetchone()
            return linha[0] if linha else 0
        modelos = [dict(r) for r in self.conn.execute(
            "SELECT model, dim, COUNT(*) n FROM rag_vectors GROUP BY model, dim")]
        por_tipo = [dict(r) for r in self.conn.execute(
            "SELECT kind, COUNT(*) n, SUM(n_chunks) trechos"
            "  FROM rag_documents GROUP BY kind ORDER BY n DESC")]
        return {
            "documentos": um("SELECT COUNT(*) FROM rag_documents"),
            "trechos": um("SELECT COUNT(*) FROM rag_chunks"),
            "vetores": um("SELECT COUNT(*) FROM rag_vectors"),
            "caracteres": um("SELECT COALESCE(SUM(n_chars),0) FROM rag_documents"),
            "modelos": modelos,
            "por_tipo": por_tipo,
            "backend": "sqlite",
        }

    def log_run(self, kind: str, **campos) -> None:
        cols = ["kind"] + list(campos)
        marks = ",".join("?" * len(cols))
        self.conn.execute(
            f"INSERT INTO rag_runs({','.join(cols)}) VALUES ({marks})",
            [kind] + list(campos.values()))
        self.conn.commit()


def _fts_query(consulta: str) -> str:
    """Converte texto livre numa consulta FTS5 segura.

    Aspas, parenteses e operadores viram termos comuns; cada palavra com
    tres letras ou mais entra com prefixo, de modo que "fadig" alcance
    "fadiga" e "fadigado".
    """
    palavras = re.findall(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]{2,}", consulta)
    if not palavras:
        return ""
    termos = [f'"{p}"*' if len(p) >= 3 else f'"{p}"' for p in palavras[:24]]
    return " OR ".join(termos)


# ---------------------------------------------------------------- pgvector
class PgVectorStore(VectorStore):
    """Mesma interface sobre Postgres + pgvector.

    Os metadados continuam no SQLite (fonte da verdade do LAPE); aqui ficam
    apenas os vetores e o texto necessario ao ranqueamento, o que mantem a
    migracao reversivel.
    """

    def __init__(self, dsn: str | None = None, model: str | None = None,
                 dim: int = 1024, tabela: str | None = None) -> None:
        self.dsn = dsn or config.PG_DSN
        if not self.dsn:
            raise RuntimeError("LAPE_PG_DSN nao definida para o backend pgvector")
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "backend pgvector exige psycopg (pip install 'psycopg[binary]')"
            ) from exc
        self._psycopg = psycopg
        self.conn = psycopg.connect(self.dsn, autocommit=True)
        self.model = model
        self.dim = dim
        self.tabela = tabela or config.PG_TABLE

    def ensure_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.tabela} (
                    chunk_id  BIGINT PRIMARY KEY,
                    doc_id    BIGINT NOT NULL,
                    uri       TEXT NOT NULL,
                    kind      TEXT,
                    title     TEXT,
                    authors   TEXT,
                    year      INT,
                    doi       TEXT,
                    section   TEXT,
                    ordinal   INT NOT NULL DEFAULT 0,
                    text      TEXT NOT NULL,
                    model     TEXT NOT NULL,
                    vec       vector({self.dim}) NOT NULL
                )""")
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS {self.tabela}_hnsw ON {self.tabela}"
                f" USING hnsw (vec vector_cosine_ops)")
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS {self.tabela}_doc ON {self.tabela}(doc_id)")
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS {self.tabela}_fts ON {self.tabela}"
                f" USING gin (to_tsvector('portuguese', text))")

    def upsert_document(self, doc: Document) -> tuple[int, bool]:
        raise NotImplementedError(
            "no backend pgvector os metadados seguem no SQLite; "
            "use SqliteStore.upsert_document e replique os vetores com replace_chunks")

    def replace_chunks(self, doc_id: int, chunks: list[Chunk],
                       vetores: np.ndarray, model: str,
                       meta: dict | None = None) -> int:
        meta = meta or {}
        with self.conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self.tabela} WHERE doc_id = %s", (doc_id,))
            for c, v in zip(chunks, vetores):
                cur.execute(
                    f"INSERT INTO {self.tabela}(chunk_id, doc_id, uri, kind, title,"
                    " authors, year, doi, section, ordinal, text, model, vec)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (meta.get("chunk_ids", {}).get(c.ordinal, c.ordinal), doc_id,
                     meta.get("uri", ""), meta.get("kind"), meta.get("title"),
                     meta.get("authors"), meta.get("year"), meta.get("doi"),
                     c.section, c.ordinal, c.text, model,
                     list(np.asarray(v, dtype=np.float32))))
        return len(chunks)

    def search_dense(self, qvec: np.ndarray, k: int,
                     filtro: Filtro | None = None) -> list[Hit]:
        onde, args = _pg_filtro(filtro)
        with self.conn.cursor() as cur:
            cur.execute(
                f"SELECT chunk_id, doc_id, text, uri, title, authors, year, kind,"
                f"       doi, section, ordinal, 1 - (vec <=> %s::vector) AS score"
                f"  FROM {self.tabela} WHERE {onde}"
                f"  ORDER BY vec <=> %s::vector LIMIT %s",
                [list(np.asarray(qvec, dtype=np.float32))] + args
                + [list(np.asarray(qvec, dtype=np.float32)), k])
            linhas = cur.fetchall()
        return [Hit(chunk_id=r[0], doc_id=r[1], text=r[2], uri=r[3], title=r[4],
                    authors=r[5], year=r[6], kind=r[7], doi=r[8], section=r[9],
                    ordinal=r[10], score=float(r[11]), origem="densa") for r in linhas]

    def search_lexical(self, consulta: str, k: int,
                       filtro: Filtro | None = None) -> list[Hit]:
        onde, args = _pg_filtro(filtro)
        with self.conn.cursor() as cur:
            cur.execute(
                f"SELECT chunk_id, doc_id, text, uri, title, authors, year, kind,"
                f"       doi, section, ordinal,"
                f"       ts_rank(to_tsvector('portuguese', text),"
                f"               plainto_tsquery('portuguese', %s)) AS score"
                f"  FROM {self.tabela}"
                f" WHERE to_tsvector('portuguese', text) @@"
                f"       plainto_tsquery('portuguese', %s) AND {onde}"
                f" ORDER BY score DESC LIMIT %s",
                [consulta, consulta] + args + [k])
            linhas = cur.fetchall()
        return [Hit(chunk_id=r[0], doc_id=r[1], text=r[2], uri=r[3], title=r[4],
                    authors=r[5], year=r[6], kind=r[7], doi=r[8], section=r[9],
                    ordinal=r[10], score=float(r[11]), origem="lexica") for r in linhas]

    def get_chunks(self, ids: Sequence[int]) -> list[Hit]:
        if not ids:
            return []
        with self.conn.cursor() as cur:
            cur.execute(
                f"SELECT chunk_id, doc_id, text, uri, title, authors, year, kind,"
                f" doi, section, ordinal FROM {self.tabela} WHERE chunk_id = ANY(%s)",
                (list(ids),))
            linhas = cur.fetchall()
        return [Hit(chunk_id=r[0], doc_id=r[1], score=0.0, text=r[2], uri=r[3],
                    title=r[4], authors=r[5], year=r[6], kind=r[7], doi=r[8],
                    section=r[9], ordinal=r[10]) for r in linhas]

    def delete_document(self, uri: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self.tabela} WHERE uri = %s", (uri,))
            return cur.rowcount > 0

    def stats(self) -> dict:
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*), COUNT(DISTINCT doc_id) FROM {self.tabela}")
            trechos, docs = cur.fetchone()
        return {"documentos": docs, "trechos": trechos, "vetores": trechos,
                "backend": "pgvector", "tabela": self.tabela}


def _pg_filtro(filtro: Filtro | None) -> tuple[str, list]:
    if filtro is None:
        return "TRUE", []
    partes, args = [], []
    if filtro.kinds:
        partes.append("kind = ANY(%s)"); args.append(list(filtro.kinds))
    if filtro.anos:
        de, ate = filtro.anos
        if de is not None:
            partes.append("year >= %s"); args.append(de)
        if ate is not None:
            partes.append("year <= %s"); args.append(ate)
    if filtro.doc_ids:
        partes.append("doc_id = ANY(%s)"); args.append(list(filtro.doc_ids))
    if filtro.uri_prefix:
        partes.append("uri LIKE %s"); args.append(f"{filtro.uri_prefix}%")
    return (" AND ".join(partes) if partes else "TRUE"), args


def get_store(conn: sqlite3.Connection, model: str | None = None,
              backend: str | None = None) -> VectorStore:
    escolhido = (backend or config.STORE_BACKEND or "sqlite").lower()
    if escolhido == "sqlite":
        return SqliteStore(conn, model=model)
    if escolhido == "pgvector":
        return PgVectorStore(model=model)
    raise RuntimeError(f"backend de vetores desconhecido: {escolhido}")
