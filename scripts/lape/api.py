"""API HTTP do LAPE.

Expoe o banco como servico REST para alimentacao e leitura automatica.
Usa apenas a biblioteca padrao -- nao precisa de Flask/FastAPI -- e abre
uma conexao SQLite por requisicao, o que a torna segura com varias
requisicoes simultaneas.

Subir o servidor:
    python3 scripts/lape_agent.py api --port 8000

Autenticacao (opcional, recomendada fora da rede local):
    export LAPE_API_TOKEN="uma-senha-longa"
    curl -H "Authorization: Bearer uma-senha-longa" ...
Sem LAPE_API_TOKEN definido a API aceita requisicoes sem token.

Rotas
    GET  /                              painel HTML
    GET  /api                           indice das rotas
    GET  /api/health                    status do servico e do banco
    GET  /api/metrics                   todos os indicadores (JSON)
    GET  /api/metrics/<bloco>           um bloco de indicadores
    GET  /api/articles                  filtros: status, linha, q, limit
    GET  /api/articles/<id>             artigo + autores + submissoes + marcos
    POST /api/articles                  cadastra/atualiza (objeto ou lista)
    GET|POST /api/submissions
    GET|POST /api/members
    GET|POST /api/events
    GET|POST /api/research-lines
    GET|POST /api/institutions
    GET  /api/discoveries               achados do rastreador
    POST /api/discoveries/<id>/review   {"action": "aceitar" | "ignorar"}
    POST /api/agents/tracker            {"tasks": ["descobrir","enriquecer","citar"]}
    POST /api/agents/curator            {"with_tracker": true}
    GET  /api/export/sqlite             baixa o banco
"""
from __future__ import annotations

import json
import os
import re
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from . import config, metrics
from .db import Database

TOKEN = os.environ.get("LAPE_API_TOKEN", "")
MAX_BODY = 8 * 1024 * 1024

ENTITY_ROUTES = {
    "articles": ("articles", "SELECT * FROM v_articles_full"),
    "submissions": ("submissions", "SELECT s.*, a.title AS article_title FROM submissions s"
                                   " JOIN articles a ON a.id = s.article_id"),
    "members": ("members", "SELECT * FROM v_member_productivity"),
    "events": ("events", "SELECT * FROM events"),
    "research-lines": ("research_lines", "SELECT * FROM research_lines"),
    "institutions": ("institutions", "SELECT * FROM institutions"),
}


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


# ----------------------------------------------------------------------
# Handlers
# ----------------------------------------------------------------------
def route_index(_db: Database, _q: dict, _body: Any) -> Any:
    return {
        "service": "LAPE API",
        "lab": config.LAB_NAME,
        "version": "1.0.0",
        "auth": "Bearer token obrigatório" if TOKEN else "aberta (defina LAPE_API_TOKEN)",
        "routes": [line.strip() for line in (__doc__ or "").splitlines()
                   if line.strip().startswith(("GET", "POST", "GET|POST"))],
    }


def route_health(db: Database, _q: dict, _body: Any) -> Any:
    return {
        "status": "ok",
        "database": str(db.path),
        "articles": int(db.scalar("SELECT COUNT(*) FROM articles") or 0),
        "members": int(db.scalar("SELECT COUNT(*) FROM members") or 0),
        "submissions": int(db.scalar("SELECT COUNT(*) FROM submissions") or 0),
        "events": int(db.scalar("SELECT COUNT(*) FROM events") or 0),
        "pending_discoveries": int(
            db.scalar("SELECT COUNT(*) FROM discoveries WHERE status = 'pendente'") or 0),
        "last_ingest": db.dicts("SELECT run_at, source, status FROM ingest_log"
                                " ORDER BY id DESC LIMIT 1"),
    }


def route_metrics(db: Database, query: dict, _body: Any, block: str | None = None) -> Any:
    window = int(query.get("window", [config.WINDOW_YEARS])[0])
    payload = metrics.build_payload(db, window=window)
    if block:
        if block not in payload:
            raise ApiError(404, f"bloco '{block}' inexistente."
                                f" Disponíveis: {', '.join(sorted(payload))}")
        return payload[block]
    return payload


def route_list(db: Database, query: dict, _body: Any, entity: str) -> Any:
    _, base_sql = ENTITY_ROUTES[entity]
    clauses: list[str] = []
    params: list[Any] = []
    if "status" in query:
        clauses.append("status = ?")
        params.append(query["status"][0])
    if "linha" in query or "research_line" in query:
        clauses.append("research_line = ?")
        params.append((query.get("linha") or query.get("research_line"))[0])
    if "q" in query:
        clauses.append("lower(COALESCE(title, full_name, name, '')) LIKE ?")
        params.append(f"%{query['q'][0].lower()}%")
    if "ano" in query:
        clauses.append("year_published = ?")
        params.append(int(query["ano"][0]))
    sql = base_sql + (" WHERE " + " AND ".join(clauses) if clauses else "")
    limit = min(int(query.get("limit", [500])[0]), 5000)
    offset = int(query.get("offset", [0])[0])
    sql += f" LIMIT {limit} OFFSET {offset}"
    try:
        rows = db.dicts(sql, params)
    except Exception as exc:
        raise ApiError(400, f"consulta inválida: {exc}") from exc
    return {"entity": entity, "count": len(rows), "limit": limit, "offset": offset, "items": rows}


def route_article_detail(db: Database, _q: dict, _body: Any, article_id: str) -> Any:
    rows = db.dicts("SELECT * FROM v_articles_full WHERE id = ?", (int(article_id),))
    if not rows:
        raise ApiError(404, f"artigo {article_id} não encontrado")
    article = rows[0]
    article["authors_detail"] = db.dicts(
        "SELECT author_order, author_name, member_id, is_corresponding, is_external"
        " FROM article_authors WHERE article_id = ? ORDER BY author_order", (int(article_id),))
    article["submissions"] = db.dicts(
        "SELECT s.*, r.label AS rejection_reason FROM submissions s"
        " LEFT JOIN rejection_reasons r ON r.id = s.rejection_reason_id"
        " WHERE s.article_id = ? ORDER BY s.attempt_no", (int(article_id),))
    article["milestones"] = db.dicts(
        "SELECT milestone, label, occurred_on FROM article_milestones"
        " WHERE article_id = ? ORDER BY seq", (int(article_id),))
    article["citations_history"] = db.dicts(
        "SELECT source, citations, snapshot_on FROM citation_snapshots"
        " WHERE article_id = ? ORDER BY snapshot_on", (int(article_id),))
    return article


def route_create(db: Database, _q: dict, body: Any, entity: str) -> Any:
    from .agents import curator

    if body is None:
        raise ApiError(400, "corpo JSON obrigatório")
    table = ENTITY_ROUTES[entity][0]
    try:
        return curator.register(db, table, body)
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc


def route_discoveries(db: Database, query: dict, _body: Any) -> Any:
    status = query.get("status", ["pendente"])[0]
    rows = db.dicts(
        "SELECT * FROM discoveries WHERE status = ? ORDER BY COALESCE(citations,0) DESC,"
        " COALESCE(year,0) DESC LIMIT ?",
        (status, min(int(query.get("limit", [200])[0]), 1000)),
    )
    return {"status": status, "count": len(rows), "items": rows}


def route_review(db: Database, _q: dict, body: Any, discovery_id: str) -> Any:
    from .agents import curator

    action = (body or {}).get("action", "aceitar")
    try:
        return curator.review_discovery(db, int(discovery_id), action, (body or {}).get("overrides"))
    except KeyError as exc:
        raise ApiError(404, str(exc)) from exc


def route_tracker(db: Database, _q: dict, body: Any) -> Any:
    from .agents import tracker

    options = body or {}
    tasks = tuple(options.get("tasks") or tracker.TASKS)
    invalid = [t for t in tasks if t not in tracker.TASKS]
    if invalid:
        raise ApiError(400, f"tarefas inválidas: {invalid}. Use {list(tracker.TASKS)}")
    return tracker.run(db, tasks, verbose=False, limit=options.get("limit"),
                       since_year=options.get("since_year"))


def route_curator(db: Database, _q: dict, body: Any) -> Any:
    from .agents import curator

    options = body or {}
    return curator.run(
        db,
        with_tracker=bool(options.get("with_tracker", False)),
        tracker_tasks=tuple(options.get("tracker_tasks") or ("enriquecer", "citar")),
        auto_accept=bool(options.get("auto_accept", False)),
        window=int(options.get("window", config.WINDOW_YEARS)),
        verbose=False,
    )


ROUTES: list[tuple[str, str, Callable]] = [
    ("GET", r"^/api/?$", route_index),
    ("GET", r"^/api/health/?$", route_health),
    ("GET", r"^/api/metrics/?$", route_metrics),
    ("GET", r"^/api/metrics/(?P<block>[a-z_]+)/?$", route_metrics),
    ("GET", r"^/api/articles/(?P<article_id>\d+)/?$", route_article_detail),
    ("GET", r"^/api/discoveries/?$", route_discoveries),
    ("POST", r"^/api/discoveries/(?P<discovery_id>\d+)/review/?$", route_review),
    ("POST", r"^/api/agents/tracker/?$", route_tracker),
    ("POST", r"^/api/agents/curator/?$", route_curator),
]
for name in ENTITY_ROUTES:
    ROUTES.append(("GET", rf"^/api/{name}/?$",
                   lambda db, q, b, _n=name: route_list(db, q, b, _n)))
    ROUTES.append(("POST", rf"^/api/{name}/?$",
                   lambda db, q, b, _n=name: route_create(db, q, b, _n)))


# ----------------------------------------------------------------------
# Servidor
# ----------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "LAPE-API/1.0"
    db_path: Path = config.DB_PATH
    report_path: Path = config.REPORT_PATH

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"  {self.address_string()} {fmt % args}")

    # -- utilidades --
    def _send(self, status: int, payload: Any, content_type: str = "application/json") -> None:
        body = (json.dumps(payload, ensure_ascii=False, default=str, indent=2).encode("utf-8")
                if content_type == "application/json" else payload)
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _authorized(self) -> bool:
        if not TOKEN:
            return True
        header = self.headers.get("Authorization", "")
        return header.removeprefix("Bearer ").strip() == TOKEN

    def _body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return None
        if length > MAX_BODY:
            raise ApiError(413, "corpo da requisição excede 8 MB")
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ApiError(400, f"JSON inválido: {exc}") from exc

    # -- metodos HTTP --
    def do_OPTIONS(self) -> None:
        self._send(204, b"", "text/plain")

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")

    def _handle(self, method: str) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path, query = parsed.path, urllib.parse.parse_qs(parsed.query)

        if method == "GET" and path in ("/", "/index.html", "/painel"):
            return self._serve_report()
        if method == "GET" and path == "/api/export/sqlite":
            return self._serve_file(self.db_path, "application/vnd.sqlite3")

        for verb, pattern, handler in ROUTES:
            match = re.match(pattern, path)
            if not match or verb != method:
                continue
            if not self._authorized():
                return self._send(401, {"error": "token inválido ou ausente"})
            db = None
            try:
                body = self._body() if method == "POST" else None
                db = Database(self.db_path)
                result = handler(db, query, body, **match.groupdict())
                return self._send(200, result)
            except ApiError as exc:
                return self._send(exc.status, {"error": exc.message})
            except Exception as exc:  # nunca derruba o servidor
                traceback.print_exc()
                return self._send(500, {"error": f"{type(exc).__name__}: {exc}"})
            finally:
                if db is not None:
                    db.close()
        self._send(404, {"error": f"rota não encontrada: {method} {path}",
                         "dica": "consulte GET /api"})

    def _serve_report(self) -> None:
        if not self.report_path.exists():
            return self._send(404, {"error": "painel ainda não gerado",
                                    "dica": "rode POST /api/agents/curator"})
        self._send(200, self.report_path.read_bytes(), "text/html")

    def _serve_file(self, path: Path, content_type: str) -> None:
        if not self._authorized():
            return self._send(401, {"error": "token inválido ou ausente"})
        if not path.exists():
            return self._send(404, {"error": f"arquivo não encontrado: {path.name}"})
        self._send(200, path.read_bytes(), content_type)


def serve(host: str = "127.0.0.1", port: int = 8000, db_path: Path = config.DB_PATH,
          report_path: Path = config.REPORT_PATH) -> None:
    Handler.db_path = Path(db_path)
    Handler.report_path = Path(report_path)
    db = Database(db_path)
    db.migrate()
    db.close()
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"LAPE API em http://{host}:{port}")
    print(f"  painel:  http://{host}:{port}/")
    print(f"  rotas:   http://{host}:{port}/api")
    print(f"  banco:   {db_path}")
    print(f"  auth:    {'Bearer token exigido' if TOKEN else 'aberta (defina LAPE_API_TOKEN)'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nservidor encerrado")
    finally:
        server.server_close()
