"""Acesso ao banco SQLite: migracao, upserts idempotentes e resolvers."""
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from . import config
from .util import clean_text, norm_key


class Database:
    """Wrapper fino sobre sqlite3 com upserts idempotentes.

    Todas as ingestoes sao idempotentes: rodar o pipeline duas vezes sobre
    os mesmos arquivos nao duplica registros nem perde dados preenchidos
    manualmente (campos vazios na origem nunca sobrescrevem valores ja
    gravados).
    """

    def __init__(self, path: Path | str = config.DB_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self._cache: dict[str, dict[str, int]] = {}

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def backup(self) -> Path | None:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return None
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = self.path.with_suffix(f".sqlite.bak_{stamp}")
        shutil.copy2(self.path, target)
        return target

    def migrate(self, schema_path: Path = config.SCHEMA_PATH) -> None:
        if not schema_path.exists():
            raise FileNotFoundError(f"schema nao encontrado: {schema_path}")
        self._drop_views()
        # As colunas novas entram ANTES do script: um indice criado sobre uma
        # coluna que ainda nao existe faz o executescript inteiro falhar, e o
        # banco antigo nao migra. Foi assim que a coluna advisor_id quebrou a
        # migracao de um banco ja em uso.
        self._add_missing_columns(schema_path)
        self.conn.executescript(schema_path.read_text(encoding="utf-8"))
        self.conn.commit()

    def _drop_views(self) -> None:
        """Views sao recriadas a cada migracao.

        'CREATE VIEW IF NOT EXISTS' manteria a definicao antiga em bancos
        ja existentes, escondendo colunas novas do esquema.
        """
        for row in self.query("SELECT name FROM sqlite_master WHERE type = 'view'"):
            self.conn.execute(f"DROP VIEW IF EXISTS {row['name']}")

    def _add_missing_columns(self, schema_path: Path) -> None:
        """Adiciona colunas novas a bancos criados por versoes anteriores.

        'CREATE TABLE IF NOT EXISTS' nao altera tabelas ja existentes, entao
        comparamos o esquema declarado com o real e aplicamos os ALTERs.
        """
        import re

        text = schema_path.read_text(encoding="utf-8")
        for block in re.finditer(
            r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\n\);", text, re.S
        ):
            table, body = block.group(1), block.group(2)
            existing = {row["name"] for row in self.query(f"PRAGMA table_info({table})")}
            if not existing:
                continue
            for line in body.splitlines():
                line = line.strip().rstrip(",")
                match = re.match(r"^(\w+)\s+(TEXT|INTEGER|REAL|NUMERIC|BLOB)\b(.*)$", line)
                if not match or match.group(1).upper() in {"PRIMARY", "UNIQUE", "FOREIGN", "CHECK"}:
                    continue
                column, ctype, rest = match.group(1), match.group(2), match.group(3)
                if column in existing:
                    continue
                # ALTER TABLE nao aceita default nao-constante, NOT NULL sem
                # default, nem UNIQUE -- a unicidade vira um indice a parte.
                rest = re.sub(r"DEFAULT\s*\(datetime\('now'\)\)", "", rest)
                rest = rest.replace("NOT NULL", "") if "DEFAULT" not in rest.upper() else rest
                unique = "UNIQUE" in rest.upper()
                rest = re.sub(r"\bUNIQUE\b", "", rest, flags=re.I)
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ctype} {rest}".strip())
                if unique:
                    self.conn.execute(
                        f"CREATE UNIQUE INDEX IF NOT EXISTS ux_{table}_{column}"
                        f" ON {table}({column})"
                    )

    def close(self) -> None:
        self.conn.commit()
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def query(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def dicts(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        return [dict(row) for row in self.query(sql, params)]

    def scalar(self, sql: str, params: Sequence[Any] = ()) -> Any:
        row = self.conn.execute(sql, params).fetchone()
        return row[0] if row else None

    def execute(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, params)

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------
    def upsert(
        self,
        table: str,
        data: dict[str, Any],
        conflict: Sequence[str],
        preserve: Iterable[str] = (),
        fill_only: bool = False,
    ) -> int:
        """Insere ou atualiza uma linha e devolve o id.

        `preserve` lista colunas que, uma vez gravadas, nunca sao
        sobrescritas (ex.: anotacoes feitas a mao no banco).
        Colunas com valor None nunca apagam um valor existente.
        Com `fill_only=True` a atualizacao so preenche colunas vazias --
        usado por fontes complementares (Lattes, Scopus) para enriquecer
        sem sobrepor o que foi digitado nas planilhas do laboratorio.
        """
        payload = {k: v for k, v in data.items() if v is not None}
        for key in conflict:
            payload.setdefault(key, data.get(key))
        cols = list(payload)
        placeholders = ", ".join("?" for _ in cols)
        conflict_cols = ", ".join(conflict)
        updatable = [c for c in cols if c not in conflict and c not in set(preserve)]
        if updatable:
            if fill_only:
                assignments = ", ".join(f"{c} = COALESCE({table}.{c}, excluded.{c})" for c in updatable)
            else:
                assignments = ", ".join(f"{c} = excluded.{c}" for c in updatable)
            assignments += ", updated_at = datetime('now')" if self._has_column(table, "updated_at") else ""
            action = f"DO UPDATE SET {assignments}"
        else:
            action = "DO NOTHING"
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT ({conflict_cols}) {action}"
        )
        self.conn.execute(sql, [payload[c] for c in cols])
        where = " AND ".join(f"{c} IS ?" for c in conflict)
        return int(self.scalar(f"SELECT id FROM {table} WHERE {where}", [payload.get(c) for c in conflict]))

    def update_row(self, table: str, row_id: int, data: dict[str, Any]) -> None:
        """Atualiza apenas os campos informados (None nunca apaga valor)."""
        payload = {k: v for k, v in data.items() if v is not None}
        if not payload:
            return
        assignments = ", ".join(f"{c} = ?" for c in payload)
        if self._has_column(table, "updated_at"):
            assignments += ", updated_at = datetime('now')"
        self.conn.execute(
            f"UPDATE {table} SET {assignments} WHERE id = ?", [*payload.values(), row_id]
        )

    def _has_column(self, table: str, column: str) -> bool:
        cols = {row["name"] for row in self.query(f"PRAGMA table_info({table})")}
        return column in cols

    # ------------------------------------------------------------------
    # Resolvers (get-or-create)
    # ------------------------------------------------------------------
    def research_line_id(self, name: Any, code: Any = None) -> int | None:
        label = clean_text(name)
        if label is None:
            return None
        key = norm_key(code or label)
        cache = self._cache.setdefault("research_lines", {})
        if key in cache:
            return cache[key]
        row = self.conn.execute(
            "SELECT id FROM research_lines WHERE code = ? OR lower(name) = lower(?)",
            (key, label),
        ).fetchone()
        line_id = int(row["id"]) if row else self.upsert(
            "research_lines", {"code": key, "name": label}, conflict=("code",)
        )
        cache[key] = line_id
        return line_id

    def institution_id(self, name: Any, city: Any = None, **extra: Any) -> int | None:
        label = clean_text(name)
        if label is None:
            return None
        city_v = clean_text(city)
        key = f"{norm_key(label)}|{norm_key(city_v)}"
        cache = self._cache.setdefault("institutions", {})
        if key in cache:
            return cache[key]
        data = {"name": label, "city": city_v}
        data.update({k: v for k, v in extra.items() if v is not None})
        inst_id = self.upsert("institutions", data, conflict=("name", "city"))
        cache[key] = inst_id
        return inst_id

    def rejection_reason_id(self, label: Any, category: Any = None) -> int | None:
        text = clean_text(label)
        if text is None:
            return None
        code = norm_key(text)[:60]
        cache = self._cache.setdefault("rejection_reasons", {})
        if code in cache:
            return cache[code]
        reason_id = self.upsert(
            "rejection_reasons",
            {"code": code, "label": text, "category": clean_text(category)},
            conflict=("code",),
        )
        cache[code] = reason_id
        return reason_id

    def member_id(self, name: Any, create: bool = True, **extra: Any) -> int | None:
        """Resolve um integrante pela chave canonica de autor.

        Faz a ponte entre grafias diferentes da mesma pessoa: 'Andrade'
        (planilha, so sobrenome) e 'ALEXANDRO ANDRADE' (Lattes) acabam no
        mesmo registro, desde que o sobrenome seja unico no laboratorio.
        Sobrenomes ambiguos nao sao fundidos -- use a coluna 'variacoes'
        da aba de integrantes para desambiguar.
        """
        from .util import author_key, display_name

        key = author_key(name)
        if not key:
            return None
        cache = self._cache.setdefault("members", {})
        if key in cache:
            return cache[key]

        row = self.conn.execute("SELECT id FROM members WHERE name_key = ?", (key,)).fetchone()
        if row is None:
            row = self._match_by_surname(key, display_name(name) or str(name))
        if row is not None:
            member_id = int(row["id"])
            cache[key] = member_id
            self.update_row("members", member_id, extra)
            return member_id

        if not create:
            return None
        data = {"name_key": key, "full_name": display_name(name) or str(name)}
        data.update({k: v for k, v in extra.items() if v is not None})
        member = self.upsert("members", data, conflict=("name_key",))
        cache[key] = member
        return member

    def _match_by_surname(self, key: str, display: str = "") -> Any:
        """Casa 'andrade' com 'andrade_a' (e vice-versa) quando for unico."""
        surname = key.split("_", 1)[0]
        if len(surname) < 4:
            return None
        # GLOB, e nao LIKE: em LIKE o '_' e curinga, o que faria
        # 'andrade_a' casar com qualquer sobrenome de mesmo tamanho.
        rows = self.conn.execute(
            "SELECT id, name_key, full_name FROM members WHERE name_key = ? OR name_key GLOB ?",
            (surname, surname + "_*"),
        ).fetchall()
        rows = [r for r in rows if r["name_key"].split("_", 1)[0] == surname]
        if len(rows) != 1:
            return None
        match = rows[0]
        # promove a chave mais especifica ('andrade' -> 'andrade_a')
        if len(key) > len(match["name_key"]):
            self.conn.execute("UPDATE members SET name_key = ? WHERE id = ?", (key, match["id"]))
            self._cache.setdefault("members", {})[match["name_key"]] = int(match["id"])
        if display and len(display) > len(match["full_name"] or ""):
            self.conn.execute("UPDATE members SET full_name = ? WHERE id = ?", (display, match["id"]))
        return match

    def merge_members(self, source_id: int, target_id: int) -> None:
        """Funde dois registros da mesma pessoa criados por grafias diferentes."""
        if source_id == target_id:
            return
        self.conn.execute(
            "UPDATE OR IGNORE article_authors SET member_id = ? WHERE member_id = ?",
            (target_id, source_id),
        )
        self.conn.execute(
            "UPDATE OR IGNORE event_participants SET member_id = ? WHERE member_id = ?",
            (target_id, source_id),
        )
        self.conn.execute(
            "UPDATE articles SET lead_member_id = ? WHERE lead_member_id = ?",
            (target_id, source_id),
        )
        # remove coautoria duplicada do mesmo integrante no mesmo artigo
        self.conn.execute(
            "DELETE FROM article_authors WHERE rowid NOT IN"
            " (SELECT MIN(rowid) FROM article_authors GROUP BY article_id, member_id)"
            " AND member_id = ?",
            (target_id,),
        )
        self.conn.execute("DELETE FROM members WHERE id = ?", (source_id,))
        cache = self._cache.setdefault("members", {})
        for key, value in list(cache.items()):
            if value == source_id:
                cache[key] = target_id

    def register_alias(self, alias: Any, member_id: int) -> None:
        """Aponta uma grafia alternativa para um integrante ja existente."""
        from .util import author_key

        key = author_key(alias)
        if key:
            self._cache.setdefault("members", {})[key] = member_id

    # ------------------------------------------------------------------
    # Log de ingestao
    # ------------------------------------------------------------------
    def log_ingest(
        self,
        source: str,
        target: str | None = None,
        file: str | None = None,
        rows_read: int = 0,
        rows_written: int = 0,
        status: str = "ok",
        message: str | None = None,
    ) -> None:
        self.conn.execute(
            "INSERT INTO ingest_log (source, target, file, rows_read, rows_written, status, message)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (source, target, file, rows_read, rows_written, status, message),
        )
        self.conn.commit()


def open_db(path: Path | str = config.DB_PATH, migrate: bool = True) -> Database:
    db = Database(path)
    if migrate:
        db.migrate()
    return db
