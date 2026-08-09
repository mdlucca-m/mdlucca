"""app/db.py — acesso ao SQLite (somente leitura para a API)."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "db.sqlite"


def db_path() -> Path:
    return Path(os.environ.get("MDLUCCA_DB", DEFAULT_DB))


def connect() -> sqlite3.Connection:
    p = db_path()
    if not p.exists():
        raise FileNotFoundError(
            f"Banco nao encontrado em {p}. Rode: python3 scripts/ingest.py"
        )
    # modo somente-leitura via URI
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def connect_rw() -> sqlite3.Connection:
    """Conexao de LEITURA/ESCRITA (cadastro de alunos, sessoes, links).

    Diferente de connect() (somente leitura), usada apenas pelos endpoints
    que gravam no banco. Garante as tabelas auxiliares de produto (share).
    """
    p = db_path()
    con = sqlite3.connect(str(p))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    _ensure_product_tables(con)
    return con


def _ensure_product_tables(con: sqlite3.Connection) -> None:
    """Cria (idempotente) as tabelas da camada de produto sem re-ingestao."""
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS share (
            token       TEXT PRIMARY KEY,
            kind        TEXT NOT NULL,      /* session | submovement */
            ref_id      INTEGER NOT NULL,
            title       TEXT,
            audience    TEXT,               /* atleta | treinador | ambos */
            created_at  TEXT NOT NULL,
            views       INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS upload (
            id          INTEGER PRIMARY KEY,
            athlete_id  INTEGER NOT NULL,
            filename    TEXT,
            path        TEXT,
            exercise    TEXT,
            mass_kg     REAL,
            stature_m   REAL,
            load_kg     REAL,
            status      TEXT NOT NULL DEFAULT 'queued',  /* queued|processing|done|error */
            session_id  INTEGER,
            error       TEXT,
            created_at  TEXT NOT NULL,
            analyzed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS analysis_run (
            id                INTEGER PRIMARY KEY,
            session_id        INTEGER NOT NULL,
            algorithm_version TEXT,
            classification    TEXT,     /* JSON */
            quality_score     REAL,
            quality_level     TEXT,
            warnings          TEXT,     /* JSON */
            metrics           TEXT,     /* JSON (resumo por rep) */
            literature_checks TEXT,     /* JSON */
            provenance        TEXT,     /* JSON */
            created_at        TEXT NOT NULL
        );
        """
    )
    con.commit()


def rows(con: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(r) for r in con.execute(sql, params).fetchall()]


def one(con: sqlite3.Connection, sql: str, params: tuple = ()) -> dict | None:
    r = con.execute(sql, params).fetchone()
    return dict(r) if r else None


def parse_json_fields(d: dict, fields: list[str]) -> dict:
    """Converte colunas TEXT que guardam JSON em objetos Python."""
    out = dict(d)
    for f in fields:
        if out.get(f) is not None:
            try:
                out[f] = json.loads(out[f])
            except (TypeError, json.JSONDecodeError):
                pass
    return out
