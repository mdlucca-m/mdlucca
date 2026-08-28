"""API HTTP e aplicacao web do LAPE.

Serve tres coisas no mesmo endereco:
  /            painel de indicadores, lido ao vivo do banco
  /entrar      tela de acesso
  /app         area do integrante (perfil, artigos, projetos, submissoes)
  /api/...     API REST

Usa apenas a biblioteca padrao -- nao precisa de Flask/FastAPI -- e abre
uma conexao SQLite por requisicao, o que a torna segura com varias
requisicoes simultaneas.

Acesso
  Cada integrante tem login e senha (ver lape/auth.py). A sessao vive num
  cookie HttpOnly. Scripts e integracoes podem usar, em vez do cookie, o
  cabecalho `Authorization: Bearer <LAPE_API_TOKEN>`, que vale como admin.

Variaveis de ambiente
  LAPE_API_TOKEN         token de servico (CI, scripts) -- opcional
  LAPE_PUBLIC_DASHBOARD  "1" deixa o painel visivel sem login
  LAPE_ADMIN_LOGIN       cria o primeiro administrador na subida
  LAPE_ADMIN_PASSWORD    senha desse administrador
  LAPE_BEHIND_HTTPS      "1" marca o cookie como Secure (use na nuvem)
"""
from __future__ import annotations

import json
import os
import queue
import re
import threading
import traceback
import urllib.parse
from http import cookies
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from . import auth, config, export, metrics, report
from .db import Database

TOKEN = os.environ.get("LAPE_API_TOKEN", "")
PUBLIC_DASHBOARD = os.environ.get("LAPE_PUBLIC_DASHBOARD", "") == "1"
# Só confie no cabeçalho do proxy quando houver mesmo um proxy na frente:
# X-Forwarded-For é escrito pelo cliente quando não há.
TRUST_PROXY = os.environ.get("LAPE_TRUST_PROXY", "") == "1"
BEHIND_HTTPS = os.environ.get("LAPE_BEHIND_HTTPS", "") == "1"
COOKIE_NAME = "lape_session"

# Valem para toda resposta, inclusive sem o Caddy na frente. A CSP aqui não
# promete impedir XSS — as páginas são autocontidas e usam script embutido,
# então 'unsafe-inline' é necessário. O que ela impede é o que importa quando
# o serviço fica público: carregar ou vazar dado para outro servidor, ser
# colocado dentro de um iframe alheio e ter a base das URLs sequestrada.
CSP = ("default-src 'self'; "
       "script-src 'self' 'unsafe-inline'; "
       "style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data:; "
       "font-src 'self' data:; "
       "connect-src 'self'; "
       "form-action 'self'; "
       "base-uri 'none'; "
       "frame-ancestors 'none'")
SECURITY_HEADERS = [
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "same-origin"),
    ("X-Frame-Options", "DENY"),
    ("Content-Security-Policy", CSP),
    ("Cross-Origin-Opener-Policy", "same-origin"),
]
MAX_BODY = 8 * 1024 * 1024

TEMPLATES = Path(__file__).resolve().parent / "templates"

FAVICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<rect width="64" height="64" rx="14" fill="#2f6fb5"/>'
    '<text x="32" y="43" font-family="Helvetica,Arial" font-size="30" font-weight="bold"'
    ' fill="#fff" text-anchor="middle">LP</text></svg>'
)

# entidade da URL -> (tabela do curador, consulta de listagem, perfil minimo para gravar)
ENTITIES: dict[str, tuple[str, str, str]] = {
    "articles": ("articles", "SELECT * FROM v_articles_full", "integrante"),
    "submissions": ("submissions",
                    "SELECT s.*, a.title AS article_title, a.internal_code,"
                    " r.label AS rejection_reason_label FROM submissions s"
                    " JOIN articles a ON a.id = s.article_id"
                    " LEFT JOIN rejection_reasons r ON r.id = s.rejection_reason_id",
                    "integrante"),
    "members": ("members", "SELECT * FROM v_researcher", "coordenacao"),
    "researchers": ("members", "SELECT * FROM v_researcher", "coordenacao"),
    "projects": ("projects", "SELECT * FROM v_projects", "integrante"),
    "events": ("events", "SELECT * FROM events", "integrante"),
    "research-lines": ("research_lines", "SELECT * FROM research_lines", "coordenacao"),
    "institutions": ("institutions", "SELECT * FROM institutions", "coordenacao"),
    "rejection-reasons": ("rejection_reasons", "SELECT * FROM rejection_reasons", "coordenacao"),
}


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


# ----------------------------------------------------------------------
# Rotas publicas / de sessao
# ----------------------------------------------------------------------
def route_index(ctx: "Context") -> Any:
    return {
        "service": "LAPE API",
        "lab": config.LAB_NAME,
        "version": "2.0.0",
        "authenticated": ctx.user is not None,
        "user": ctx.user,
        "paginas": {"painel": "/", "entrar": "/entrar", "area_do_integrante": "/app",
                    "mural": "/mural"},
        "rotas": [
            "POST /api/auth/login            {login, senha}",
            "POST /api/auth/logout",
            "GET  /api/auth/me",
            "POST /api/auth/senha            {atual, nova}",
            "POST /api/auth/usuarios         (admin) {nome, login, senha, perfil}",
            "GET  /api/health",
            "GET  /api/metrics[/<bloco>]",
            "GET  /api/state                 mudou algo? (consulta barata)",
            "GET  /api/catalog               medidas e dimensões disponíveis",
            "GET  /api/query                 ?medida=&por=&quebra=&linha=&ano=…",
            "GET  /api/history               ?metrica=publicados",
            "GET  /api/lake/lineage          (coordenação) de onde veio cada carga",
            "GET  /api/stream                 eventos em tempo real (SSE)",
            "POST /api/invites                (coordenação) gera link de convite",
            "GET  /api/convite/<token>        estado do convite (público)",
            "POST /api/convite/<token>/aceitar  a pessoa cria o próprio acesso",
            "GET  /api/automation             (coordenação) webhooks e entregas",
            "POST /api/webhooks               (coordenação) cadastra destino n8n",
            "POST /api/hooks/n8n              porta de entrada do n8n (HMAC ou token)",
            "POST /api/agents/lake           (coordenação) reconstrói o lakehouse",
            "GET  /api/<entidade>            filtros: q, status, linha, ano, limit, offset",
            "GET  /api/articles/<id>",
            "GET  /api/researchers/<id>",
            "POST /api/<entidade>            cadastra ou atualiza",
            "GET  /api/discoveries",
            "POST /api/discoveries/<id>/review",
            "POST /api/agents/tracker        (coordenacao)",
            "POST /api/agents/curator        (coordenacao)",
            "GET  /api/export/sqlite         (admin)",
        ],
        "entidades": sorted(ENTITIES),
    }


def route_login(ctx: "Context") -> Any:
    body = ctx.body or {}
    login_value = body.get("login") or body.get("usuario") or body.get("email")
    password = body.get("senha") or body.get("password")
    if not login_value or not password:
        raise ApiError(400, "informe login e senha")
    session = auth.login(ctx.db, login_value, password,
                         user_agent=ctx.handler.headers.get("User-Agent", ""),
                         ip=ctx.handler._client_ip())
    ctx.set_cookie = session["token"]
    return {"ok": True, "user": session["user"], "expires_at": session["expires_at"]}


def route_invite_create(ctx: "Context") -> Any:
    """Gera o link de convite que a coordenação envia ao laboratório."""
    user = auth.require(ctx.user, "coordenacao")
    body = ctx.body or {}
    convite = auth.create_invite(
        ctx.db, created_by=user["id"],
        label=body.get("nome") or body.get("label"),
        role=body.get("perfil") or body.get("role") or "integrante",
        max_uses=int(body.get("usos") or body.get("max_uses") or 30),
        days=int(body.get("dias") or body.get("days") or auth.INVITE_DAYS))
    convite["link"] = ctx.handler._base_url() + "/convite/" + convite["token"]
    return convite


def route_invite_list(ctx: "Context") -> Any:
    auth.require(ctx.user, "coordenacao")
    base = ctx.handler._base_url()
    convites = auth.list_invites(ctx.db)
    for convite in convites:
        convite["link"] = base + "/convite/" + convite["token"]
        convite["state"] = auth.invite_state(ctx.db, convite["token"])
    return convites


def route_invite_revoke(ctx: "Context", invite_id: str) -> Any:
    user = auth.require(ctx.user, "coordenacao")
    return auth.revoke_invite(ctx.db, int(invite_id), user["id"])


def route_invite_state(ctx: "Context", token: str) -> Any:
    """Pública de propósito: a página do convite precisa saber se ele serve."""
    return auth.invite_state(ctx.db, token)


def route_invite_accept(ctx: "Context", token: str) -> Any:
    """Pública: é aqui que a pessoa convidada cria o próprio acesso."""
    body = ctx.body or {}
    ip = ctx.handler._client_ip()
    # o mesmo travamento do login vale aqui, senão o convite vira porta para
    # criar contas em massa
    auth.check_lock(ctx.db, f"convite:{token}"[:80], ip)
    try:
        sessao = auth.accept_invite(
            ctx.db, token,
            full_name=body.get("nome") or body.get("full_name") or "",
            login_value=body.get("email") or body.get("login") or "",
            password=body.get("senha") or body.get("password") or "",
            ip=ip)
    except auth.AuthError:
        auth.log(ctx.db, None, f"convite:{token}"[:80], "login_negado", "invites",
                 None, "convite recusado", ip)
        raise
    ctx.set_cookie = sessao["token"]
    return {"ok": True, "user": sessao["user"]}


def route_logout(ctx: "Context") -> Any:
    if ctx.token:
        auth.logout(ctx.db, ctx.token)
    ctx.clear_cookie = True
    return {"ok": True}


def route_me(ctx: "Context") -> Any:
    if ctx.user is None:
        raise ApiError(401, "nao autenticado")
    return ctx.user


def route_change_password(ctx: "Context") -> Any:
    user = auth.require(ctx.user, "leitura")
    body = ctx.body or {}
    return auth.change_password(ctx.db, user["id"],
                                body.get("atual") or body.get("current") or "",
                                body.get("nova") or body.get("new") or "")


def route_create_user(ctx: "Context") -> Any:
    auth.require(ctx.user, "admin")
    body = ctx.body or {}
    if not body.get("nome") or not body.get("login"):
        raise ApiError(400, "informe nome e login")
    return auth.create_account(ctx.db, body["nome"], body["login"], body.get("senha"),
                               role=body.get("perfil", "integrante"))


def route_health(ctx: "Context") -> Any:
    db = ctx.db
    return {
        "status": "ok",
        "database": str(db.path),
        "authenticated": ctx.user is not None,
        "articles": int(db.scalar("SELECT COUNT(*) FROM articles") or 0),
        "members": int(db.scalar("SELECT COUNT(*) FROM members") or 0),
        "projects": int(db.scalar("SELECT COUNT(*) FROM projects") or 0),
        "submissions": int(db.scalar("SELECT COUNT(*) FROM submissions") or 0),
        "events": int(db.scalar("SELECT COUNT(*) FROM events") or 0),
        "pending_discoveries": int(
            db.scalar("SELECT COUNT(*) FROM discoveries WHERE status = 'pendente'") or 0),
        "users": int(db.scalar("SELECT COUNT(*) FROM members WHERE login IS NOT NULL") or 0),
        "last_ingest": db.dicts(
            "SELECT run_at, source, status FROM ingest_log ORDER BY id DESC LIMIT 1"),
    }


# ----------------------------------------------------------------------
# Leitura
# ----------------------------------------------------------------------
def route_metrics(ctx: "Context", block: str | None = None) -> Any:
    window = int(ctx.query.get("window", [config.WINDOW_YEARS])[0])
    payload = metrics.build_payload(ctx.db, window=window)
    if block:
        if block not in payload:
            raise ApiError(404, f"bloco '{block}' inexistente."
                                f" Disponíveis: {', '.join(sorted(payload))}")
        return payload[block]
    return payload


def route_list(ctx: "Context", entity: str) -> Any:
    _, base_sql, _ = ENTITIES[entity]
    query = ctx.query
    clauses: list[str] = []
    params: list[Any] = []
    if "status" in query:
        clauses.append("status = ?")
        params.append(query["status"][0])
    if "linha" in query or "research_line" in query:
        clauses.append("research_line = ?")
        params.append((query.get("linha") or query.get("research_line"))[0])
    if "ano" in query:
        clauses.append("year_published = ?")
        params.append(int(query["ano"][0]))
    if "q" in query:
        clauses.append("lower(COALESCE(title, full_name, name, '')) LIKE ?")
        params.append(f"%{query['q'][0].lower()}%")
    sql = base_sql + (" WHERE " + " AND ".join(clauses) if clauses else "")
    limit = min(int(query.get("limit", [500])[0]), 5000)
    offset = int(query.get("offset", [0])[0])
    sql += f" LIMIT {limit} OFFSET {offset}"
    try:
        rows = ctx.db.dicts(sql, params)
    except Exception as exc:
        raise ApiError(400, f"consulta inválida: {exc}") from exc
    if entity in ("members", "researchers"):
        for row in rows:
            row.pop("password_hash", None)
    return {"entity": entity, "count": len(rows), "limit": limit, "offset": offset, "items": rows}


def route_article_detail(ctx: "Context", article_id: str) -> Any:
    db = ctx.db
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
    article["projects"] = db.dicts(
        "SELECT p.id, p.name FROM project_articles pa JOIN projects p ON p.id = pa.project_id"
        " WHERE pa.article_id = ?", (int(article_id),))
    article["can_edit"] = bool(ctx.user and auth.can_edit_article(db, ctx.user, int(article_id)))
    return article


def route_team(ctx: "Context") -> Any:
    """Lista enxuta da equipe: nome, vinculo e quem pode orientar.

    Existe porque `/api/members` exige coordenacao -- e quem esta preenchendo
    a propria ficha precisa escolher o orientador numa lista, nao digitar o
    nome de cabeca. Aqui so sai o que ja aparece no painel: nome e vinculo.
    """
    from .mapping import ORIENTAM, ROLE_LABEL

    pessoas = ctx.db.dicts(
        "SELECT id, full_name, short_name, role FROM members"
        " WHERE is_external = 0 AND active = 1 ORDER BY full_name")
    for pessoa in pessoas:
        pessoa["role_label"] = ROLE_LABEL.get(pessoa["role"] or "", pessoa["role"])
        pessoa["orienta"] = (pessoa["role"] or "") in ORIENTAM
    return {"items": pessoas, "count": len(pessoas)}


def route_researcher_detail(ctx: "Context", member_id: str) -> Any:
    db = ctx.db
    rows = db.dicts("SELECT * FROM v_researcher WHERE id = ?", (int(member_id),))
    if not rows:
        raise ApiError(404, f"pesquisador {member_id} não encontrado")
    person = rows[0]
    person["project_list"] = db.dicts(
        "SELECT p.id, p.code, p.name, p.status, p.funder, pm.role"
        " FROM project_members pm JOIN projects p ON p.id = pm.project_id"
        " WHERE pm.member_id = ? ORDER BY p.status, p.name", (int(member_id),))
    person["articles"] = db.dicts(
        "SELECT a.id, a.internal_code, a.title, a.status, a.year_published, a.journal, a.doi,"
        "       a.scopus_citations, a.wos_citations, a.openalex_citations, aa.author_order"
        " FROM article_authors aa JOIN articles a ON a.id = aa.article_id"
        " WHERE aa.member_id = ?"
        " ORDER BY COALESCE(a.year_published, 9999) DESC, a.title", (int(member_id),))
    person["coauthors"] = db.dicts(
        "SELECT m.id, m.full_name, COUNT(*) AS n FROM article_authors a1"
        " JOIN article_authors a2 ON a2.article_id = a1.article_id AND a2.member_id <> a1.member_id"
        " JOIN members m ON m.id = a2.member_id"
        " WHERE a1.member_id = ? GROUP BY m.id ORDER BY n DESC LIMIT 15", (int(member_id),))
    person["can_edit"] = bool(ctx.user and auth.can_edit_member(ctx.user, int(member_id)))
    return person


def route_state(ctx: "Context") -> Any:
    """Resposta barata para o painel saber se algo mudou, sem recalcular tudo."""
    db = ctx.db
    return {
        "articles": int(db.scalar("SELECT COUNT(*) FROM articles") or 0),
        "members": int(db.scalar("SELECT COUNT(*) FROM members") or 0),
        "submissions": int(db.scalar("SELECT COUNT(*) FROM submissions") or 0),
        "events": int(db.scalar("SELECT COUNT(*) FROM events") or 0),
        "projects": int(db.scalar("SELECT COUNT(*) FROM projects") or 0),
        "pending_discoveries": int(
            db.scalar("SELECT COUNT(*) FROM discoveries WHERE status = 'pendente'") or 0),
        "last_ingest": db.dicts(
            "SELECT run_at, source, target, status FROM ingest_log ORDER BY id DESC LIMIT 1"),
        "server_time": datetime.now().isoformat(timespec="seconds"),
    }


def route_catalog(ctx: "Context") -> Any:
    """Medidas, dimensões e filtros aceitos pela camada ouro."""
    from . import lake

    return lake.catalog()


def route_query(ctx: "Context") -> Any:
    """Agrega uma medida por uma ou duas dimensões, sobre a camada ouro.

    Nada do que o cliente envia vira SQL: ele escolhe chaves de uma lista,
    e cada chave traz a expressão já escrita.
    """
    from . import lake

    query = ctx.query
    filters = {}
    for key in lake.FILTERS:
        if key in query and query[key][0] not in ("", None):
            filters[key] = query[key][0]
    try:
        return lake.query(
            ctx.db,
            measure=query.get("medida", ["artigos"])[0],
            by=query.get("por", ["linha"])[0],
            split=(query.get("quebra", [None])[0] or None),
            filters=filters,
            limit=int(query.get("limite", [40])[0]),
            order=query.get("ordem", ["valor"])[0],
        )
    except lake.QueryError as exc:
        raise ApiError(400, str(exc)) from exc


def route_history(ctx: "Context") -> Any:
    from . import lake

    metric = ctx.query.get("metrica", ["artigos"])[0]
    if metric not in lake.SNAPSHOT_METRICS:
        raise ApiError(400, f"indicador desconhecido: {metric}."
                            f" Use um de: {', '.join(sorted(lake.SNAPSHOT_METRICS))}")
    return {
        "metric": metric,
        "series": lake.metric_history(ctx.db, metric, "total",
                                      min(int(ctx.query.get("limite", [120])[0]), 500)),
        "delta_30d": lake.metric_delta(ctx.db, metric, 30),
        "by_line": lake.metric_history(ctx.db, metric, "linha", 400),
    }


def route_lineage(ctx: "Context") -> Any:
    from . import lake

    auth.require(ctx.user, "coordenacao")
    return {"items": lake.lineage(ctx.db, min(int(ctx.query.get("limite", [80])[0]), 500))}


def route_lake(ctx: "Context") -> Any:
    from . import lake

    user = auth.require(ctx.user, "coordenacao")
    options = ctx.body or {}
    auth.log(ctx.db, user["id"], user.get("login"), "lakehouse")
    return lake.run(ctx.db, with_export=bool(options.get("exportar", False)), verbose=False)


def route_automation(ctx: "Context") -> Any:
    """Painel de automação: eventos, webhooks e últimas entregas."""
    from . import hooks

    auth.require(ctx.user, "coordenacao")
    return hooks.status(ctx.db, min(int(ctx.query.get("limite", [40])[0]), 200))


def route_webhook_create(ctx: "Context") -> Any:
    """Cadastra um webhook do n8n (ou de qualquer outro destino)."""
    from . import hooks

    user = auth.require(ctx.user, "coordenacao")
    body = ctx.body or {}
    if not body.get("url"):
        raise ApiError(400, "informe a url do webhook")
    try:
        created = hooks.register(ctx.db, body.get("nome") or body.get("name") or "n8n",
                                 body["url"], body.get("evento") or body.get("event") or "*",
                                 body.get("segredo") or body.get("secret"))
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc
    auth.log(ctx.db, user["id"], user.get("login"), "webhook_cadastrado", "webhooks",
             created["id"], created["url"])
    return created


def route_webhook_delete(ctx: "Context", hook_id: str) -> Any:
    from . import hooks

    user = auth.require(ctx.user, "coordenacao")
    auth.log(ctx.db, user["id"], user.get("login"), "webhook_removido", "webhooks", hook_id)
    return hooks.remove(ctx.db, int(hook_id))


def route_webhook_test(ctx: "Context", hook_id: str) -> Any:
    """Dispara um evento de teste, em primeiro plano, para ver o resultado na hora."""
    from . import hooks

    auth.require(ctx.user, "coordenacao")
    rows = ctx.db.dicts("SELECT * FROM webhooks WHERE id = ?", (int(hook_id),))
    if not rows:
        raise ApiError(404, f"webhook {hook_id} não encontrado")
    message = {"event": "teste", "detail": "disparo manual a partir do painel",
               "at": datetime.now().isoformat(timespec="seconds"), "data": {"ok": True}}
    hooks.dispatch(ctx.db, "*", message, background=False)
    return {"sent": True, "last": ctx.db.dicts(
        "SELECT status, http_code, error, duration_ms FROM webhook_deliveries"
        " WHERE webhook_id = ? ORDER BY id DESC LIMIT 1", (int(hook_id),))}


def route_incoming_hook(ctx: "Context") -> Any:
    """Porta de entrada do n8n.

    Aceita assinatura HMAC (LAPE_WEBHOOK_SECRET) ou o token de serviço.
    Ações: curador, rastreador, lake, ou o cadastro de qualquer entidade.
    """
    from . import hooks
    from .agents import curator, tracker

    raw = getattr(ctx.handler, "raw_body", b"")
    signature = ctx.handler.headers.get("X-LAPE-Signature")
    autorizado = (
        ctx.handler._service_token()                                   # token de serviço
        or hooks.verify(hooks.WEBHOOK_SECRET, raw, signature)          # assinatura HMAC
        or (ctx.user is not None
            and auth.ROLE_RANK[ctx.user["user_role"]] >= auth.ROLE_RANK["coordenacao"])
    )
    if not autorizado:
        raise ApiError(401, "assinatura ausente ou inválida. Configure LAPE_WEBHOOK_SECRET "
                            "no LAPE e no n8n, ou use o token de serviço.")

    body = ctx.body or {}
    action = (body.get("acao") or body.get("action") or "curador").lower()
    detail = f"n8n:{action}"

    if action in ("curador", "curator", "atualizar"):
        result = curator.run(ctx.db, with_tracker=bool(body.get("rastrear", False)),
                             with_lake=True, verbose=False)
        resumo = result["publish"]["overview"]
    elif action in ("rastreador", "tracker"):
        tasks = tuple(body.get("tarefas") or body.get("tasks") or ("enriquecer", "citar"))
        invalid = [t for t in tasks if t not in tracker.TASKS]
        if invalid:
            raise ApiError(400, f"tarefas inválidas: {invalid}")
        result = tracker.run(ctx.db, tasks, verbose=False)
        resumo = {k: v for k, v in result.items() if k != "agent"}
    elif action in ("lake", "lakehouse"):
        from . import lake

        result = lake.run(ctx.db, with_export=bool(body.get("exportar")), verbose=False)
        resumo = result.get("gold", {})
    elif action in ("cadastrar", "register"):
        entity = body.get("entidade") or body.get("entity") or "articles"
        if entity not in ENTITIES:
            raise ApiError(400, f"entidade desconhecida: {entity}")
        dados = body.get("dados") or body.get("data")
        if dados is None:
            raise ApiError(400, "informe 'dados' com o registro a cadastrar")
        result = curator.register(ctx.db, ENTITIES[entity][0], dados)
        resumo = {"entidade": entity, "gravados": result["written"]}
    else:
        raise ApiError(400, "ação desconhecida. Use: curador, rastreador, lake ou cadastrar")

    hooks.emit(ctx.db, "agente.concluido", entity="n8n", detail=detail, actor="n8n")
    return {"ok": True, "acao": action, "resumo": resumo}


def route_discoveries(ctx: "Context") -> Any:
    status = ctx.query.get("status", ["pendente"])[0]
    rows = ctx.db.dicts(
        "SELECT * FROM discoveries WHERE status = ? ORDER BY COALESCE(citations,0) DESC,"
        " COALESCE(year,0) DESC LIMIT ?",
        (status, min(int(ctx.query.get("limit", [200])[0]), 1000)))
    return {"status": status, "count": len(rows), "items": rows}


# ----------------------------------------------------------------------
# Escrita
# ----------------------------------------------------------------------
def route_create(ctx: "Context", entity: str) -> Any:
    from .agents import curator

    table, _, minimum = ENTITIES[entity]
    user = auth.require(ctx.user, "integrante")
    if ctx.body is None:
        raise ApiError(400, "corpo JSON obrigatório")

    # Integrante mexe no proprio cadastro; alterar terceiros exige coordenacao.
    if table == "members" and auth.ROLE_RANK[user["user_role"]] < auth.ROLE_RANK["coordenacao"]:
        items = ctx.body if isinstance(ctx.body, list) else [ctx.body]
        for item in items:
            target = item.get("id") or item.get("member_id")
            name = item.get("full_name") or item.get("Nome completo") or item.get("nome")
            if target and int(target) != int(user["id"]):
                raise ApiError(403, "você só pode editar o seu próprio cadastro")
            if not target and name and _name_key(name) != _name_key(user["full_name"]):
                raise ApiError(403, "você só pode editar o seu próprio cadastro")
    elif auth.ROLE_RANK[user["user_role"]] < auth.ROLE_RANK[minimum]:
        raise ApiError(403, f"esta ação exige perfil {minimum} ou superior")

    try:
        result = curator.register(ctx.db, table, ctx.body)
    except ValueError as exc:
        raise ApiError(400, str(exc)) from exc
    auth.log(ctx.db, user["id"], user.get("login"), "cadastro", table,
             None, f"{result['written']} registro(s)")
    return result


def _name_key(name: Any) -> str:
    from .util import author_key

    return author_key(name)


def route_review(ctx: "Context", discovery_id: str) -> Any:
    from .agents import curator

    user = auth.require(ctx.user, "coordenacao")
    action = (ctx.body or {}).get("action", "aceitar")
    try:
        result = curator.review_discovery(ctx.db, int(discovery_id), action,
                                          (ctx.body or {}).get("overrides"))
    except KeyError as exc:
        raise ApiError(404, str(exc)) from exc
    auth.log(ctx.db, user["id"], user.get("login"), f"descoberta_{action}",
             "discoveries", discovery_id)
    return result


def route_tracker(ctx: "Context") -> Any:
    from .agents import tracker

    user = auth.require(ctx.user, "coordenacao")
    options = ctx.body or {}
    tasks = tuple(options.get("tasks") or tracker.TASKS)
    invalid = [t for t in tasks if t not in tracker.TASKS]
    if invalid:
        raise ApiError(400, f"tarefas inválidas: {invalid}. Use {list(tracker.TASKS)}")
    auth.log(ctx.db, user["id"], user.get("login"), "agente_rastreador", detail=",".join(tasks))
    return tracker.run(ctx.db, tasks, verbose=False, limit=options.get("limit"),
                       since_year=options.get("since_year"))


def route_curator(ctx: "Context") -> Any:
    from .agents import curator

    user = auth.require(ctx.user, "coordenacao")
    options = ctx.body or {}
    auth.log(ctx.db, user["id"], user.get("login"), "agente_curador")
    return curator.run(
        ctx.db,
        with_tracker=bool(options.get("with_tracker", False)),
        tracker_tasks=tuple(options.get("tracker_tasks") or ("enriquecer", "citar", "perfis")),
        auto_accept=bool(options.get("auto_accept", False)),
        with_lake=bool(options.get("with_lake", True)),
        export_lake=bool(options.get("export_lake", False)),
        window=int(options.get("window", config.WINDOW_YEARS)),
        verbose=False,
    )


def route_audit(ctx: "Context") -> Any:
    auth.require(ctx.user, "coordenacao")
    return {"items": ctx.db.dicts(
        "SELECT at, login, action, entity, entity_id, detail FROM audit_log"
        " ORDER BY id DESC LIMIT ?", (min(int(ctx.query.get("limit", [200])[0]), 1000),))}


# ----------------------------------------------------------------------
# Tabela de rotas: (metodo, padrao, funcao, perfil minimo | None = publico)
# ----------------------------------------------------------------------
ROUTES: list[tuple[str, str, Callable, str | None]] = [
    ("GET", r"^/api/?$", route_index, None),
    ("POST", r"^/api/auth/login/?$", route_login, None),
    ("POST", r"^/api/auth/logout/?$", route_logout, None),
    ("GET", r"^/api/auth/me/?$", route_me, None),
    ("POST", r"^/api/auth/senha/?$", route_change_password, "leitura"),
    ("POST", r"^/api/auth/usuarios/?$", route_create_user, "admin"),
    ("GET", r"^/api/health/?$", route_health, None),
    ("GET", r"^/api/state/?$", route_state, "leitura"),
    ("GET", r"^/api/catalog/?$", route_catalog, "leitura"),
    ("GET", r"^/api/query/?$", route_query, "leitura"),
    ("GET", r"^/api/history/?$", route_history, "leitura"),
    ("GET", r"^/api/lake/lineage/?$", route_lineage, "coordenacao"),
    ("POST", r"^/api/invites/?$", route_invite_create, "coordenacao"),
    ("GET", r"^/api/invites/?$", route_invite_list, "coordenacao"),
    ("POST", r"^/api/invites/(?P<invite_id>\d+)/revogar/?$", route_invite_revoke, "coordenacao"),
    ("GET", r"^/api/convite/(?P<token>[A-Za-z0-9_-]{16,64})/?$", route_invite_state, None),
    ("POST", r"^/api/convite/(?P<token>[A-Za-z0-9_-]{16,64})/aceitar/?$", route_invite_accept, None),
    ("GET", r"^/api/automation/?$", route_automation, "coordenacao"),
    ("POST", r"^/api/webhooks/?$", route_webhook_create, "coordenacao"),
    ("POST", r"^/api/webhooks/(?P<hook_id>\d+)/remover/?$", route_webhook_delete, "coordenacao"),
    ("POST", r"^/api/webhooks/(?P<hook_id>\d+)/testar/?$", route_webhook_test, "coordenacao"),
    ("POST", r"^/api/hooks/n8n/?$", route_incoming_hook, None),
    ("POST", r"^/api/agents/lake/?$", route_lake, "coordenacao"),
    ("GET", r"^/api/metrics/?$", route_metrics, "leitura"),
    ("GET", r"^/api/metrics/(?P<block>[a-z_]+)/?$", route_metrics, "leitura"),
    ("GET", r"^/api/articles/(?P<article_id>\d+)/?$", route_article_detail, "leitura"),
    ("GET", r"^/api/researchers/(?P<member_id>\d+)/?$", route_researcher_detail, "leitura"),
    ("GET", r"^/api/equipe/?$", route_team, "integrante"),
    ("GET", r"^/api/discoveries/?$", route_discoveries, "leitura"),
    ("POST", r"^/api/discoveries/(?P<discovery_id>\d+)/review/?$", route_review, "coordenacao"),
    ("POST", r"^/api/agents/tracker/?$", route_tracker, "coordenacao"),
    ("POST", r"^/api/agents/curator/?$", route_curator, "coordenacao"),
    ("GET", r"^/api/audit/?$", route_audit, "coordenacao"),
]
for _name in ENTITIES:
    ROUTES.append(("GET", rf"^/api/{_name}/?$",
                   lambda ctx, _n=_name: route_list(ctx, _n), "leitura"))
    ROUTES.append(("POST", rf"^/api/{_name}/?$",
                   lambda ctx, _n=_name: route_create(ctx, _n), "integrante"))


class Context:
    """Tudo o que uma rota precisa saber sobre a requisicao."""

    def __init__(self, handler: "Handler", db: Database, query: dict, body: Any,
                 user: dict | None, token: str | None) -> None:
        self.handler = handler
        self.db = db
        self.query = query
        self.body = body
        self.user = user
        self.token = token
        self.set_cookie: str | None = None
        self.clear_cookie = False


# ----------------------------------------------------------------------
# Servidor
# ----------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "LAPE-API/2.0"
    protocol_version = "HTTP/1.1"
    db_path: Path = config.DB_PATH
    report_path: Path = config.REPORT_PATH
    raw_body: bytes = b""

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"  {self.address_string()} {fmt % args}")

    # -- utilidades --
    def _send(self, status: int, payload: Any, content_type: str = "application/json",
              extra_headers: list[tuple[str, str]] | None = None) -> None:
        body = (json.dumps(payload, ensure_ascii=False, default=str, indent=2).encode("utf-8")
                if content_type == "application/json" else payload)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # Toda pagina e toda resposta da API sao remontadas do banco a cada
        # acesso -- nenhuma delas pode ser guardada. Sem este cabecalho o
        # navegador guarda por conta propria e devolve a versao velha: quem
        # atualiza o sistema recarrega a pagina e jura que nada mudou.
        # O favicon e a excecao: nunca muda, e cabe guardar.
        if content_type == "image/svg+xml":
            self.send_header("Cache-Control", "public, max-age=86400")
        else:
            self.send_header("Cache-Control", "no-store, must-revalidate")
        for nome, valor in SECURITY_HEADERS:
            self.send_header(nome, valor)
        for key, value in (extra_headers or []):
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _cookie_token(self) -> str | None:
        raw = self.headers.get("Cookie")
        if not raw:
            return None
        jar = cookies.SimpleCookie()
        try:
            jar.load(raw)
        except cookies.CookieError:
            return None
        item = jar.get(COOKIE_NAME)
        return item.value if item else None

    def _cookie_header(self, token: str | None) -> tuple[str, str]:
        flags = "HttpOnly; SameSite=Lax; Path=/"
        if BEHIND_HTTPS:
            flags += "; Secure"
        if token is None:
            return ("Set-Cookie", f"{COOKIE_NAME}=; Max-Age=0; {flags}")
        return ("Set-Cookie",
                f"{COOKIE_NAME}={token}; Max-Age={auth.SESSION_DAYS * 86400}; {flags}")

    def _base_url(self) -> str:
        """Endereço por onde o visitante chegou — é o que vai no link do convite.

        Atrás do túnel ou do Caddy, o endereço público está no Host que o
        proxy repassa; o nosso é sempre 127.0.0.1 e não serviria para ninguém.
        """
        host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or ""
        host = host.split(",")[0].strip()
        if not host:
            return f"http://127.0.0.1:{self.server.server_address[1]}"
        esquema = self.headers.get("X-Forwarded-Proto", "").split(",")[0].strip()
        if not esquema:
            esquema = "https" if BEHIND_HTTPS else "http"
        return f"{esquema}://{host}"

    def _client_ip(self) -> str:
        """Endereço de quem chamou, respeitando o proxy só quando ele existe."""
        if TRUST_PROXY:
            encaminhado = self.headers.get("X-Forwarded-For", "")
            if encaminhado:
                return encaminhado.split(",")[0].strip()[:60]
            real = self.headers.get("X-Real-IP", "")
            if real:
                return real.strip()[:60]
        return self.client_address[0]

    def _service_token(self) -> bool:
        header = self.headers.get("Authorization", "")
        return bool(TOKEN) and header.removeprefix("Bearer ").strip() == TOKEN

    def _resolve_user(self, db: Database) -> tuple[dict | None, str | None]:
        if self._service_token():
            return ({"id": None, "full_name": "Serviço (token)", "login": "servico",
                     "user_role": "admin"}, None)
        token = self._cookie_token() or (self.headers.get("X-LAPE-Session") or None)
        return (auth.current_user(db, token), token)

    def _body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return None
        if length > MAX_BODY:
            raise ApiError(413, "corpo da requisição excede 8 MB")
        raw = self.rfile.read(length)
        self.raw_body = raw          # o HMAC assina os bytes, não o JSON reserializado
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
        path, query = parsed.path.rstrip("/") or "/", urllib.parse.parse_qs(parsed.query)

        if method == "GET" and path in ("/", "/painel", "/index.html"):
            return self._serve_dashboard()
        if method == "GET" and path in ("/mural", "/tv"):
            return self._serve_dashboard(mural=True)
        if method == "GET" and path in ("/entrar", "/login"):
            return self._serve_page("login.html")
        if method == "GET" and path in ("/app", "/area", "/cadastro"):
            return self._serve_page("app.html")
        if method == "GET" and path.startswith("/convite"):
            return self._serve_page("convite.html")
        if method == "GET" and path == "/api/stream":
            return self._serve_stream()
        if method == "GET" and path == "/favicon.ico":
            return self._send(200, FAVICON, "image/svg+xml")
        if method == "GET" and path == "/api/export/sqlite":
            return self._serve_database()
        if method == "GET" and path == "/api/export/artigos":
            return self._serve_export(query)
        if method == "GET" and path == "/api/export/planilha":
            return self._serve_planilha()

        for verb, pattern, handler, minimum in ROUTES:
            match = re.match(pattern, path)
            if not match or verb != method:
                continue
            db = None
            try:
                body = self._body() if method == "POST" else None
                db = Database(self.db_path)
                user, token = self._resolve_user(db)
                if minimum is not None and not (minimum == "leitura" and PUBLIC_DASHBOARD):
                    auth.require(user, minimum)
                ctx = Context(self, db, query, body, user, token)
                result = handler(ctx, **match.groupdict())
                headers = []
                if ctx.set_cookie:
                    headers.append(self._cookie_header(ctx.set_cookie))
                if ctx.clear_cookie:
                    headers.append(self._cookie_header(None))
                return self._send(200, result, extra_headers=headers)
            except auth.AuthError as exc:
                return self._send(exc.status, {"error": exc.message})
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

    # -- paginas --
    def _serve_dashboard(self, mural: bool = False) -> None:
        """Painel (ou mural) renderizado com os dados atuais, a cada acesso."""
        db = Database(self.db_path)
        try:
            user, _ = self._resolve_user(db)
            if user is None and not PUBLIC_DASHBOARD:
                return self._redirect("/entrar")
            payload = metrics.build_payload(db)
            payload["session"] = {"live": True, "user": user}
            html = report.render_mural(payload) if mural else report.render_html(payload)
        except Exception as exc:
            traceback.print_exc()
            return self._send(500, {"error": f"falha ao montar o painel: {exc}"})
        finally:
            db.close()
        self._send(200, html, "text/html")

    def _serve_stream(self) -> None:
        """Streaming de eventos (SSE): o painel redesenha no instante da mudança.

        Sem Content-Length e com Connection: close — o corpo termina quando a
        conexão fecha, que é como o EventSource espera. Um sinal a cada 20 s
        mantém a conexão viva atrás de proxy.
        """
        from . import hooks

        db = Database(self.db_path)
        try:
            user, _ = self._resolve_user(db)
            if user is None and not PUBLIC_DASHBOARD:
                return self._send(401, {"error": "é preciso entrar para acompanhar o streaming"})
            last = hooks.latest_id(db)
        finally:
            db.close()

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("X-Accel-Buffering", "no")   # nginx não deve bufferizar
        self.send_header("Connection", "close")
        self.end_headers()

        channel = hooks.subscribe()
        try:
            self._sse(f"retry: 5000\nid: {last}\nevent: pronto\n"
                      f"data: {json.dumps({'ok': True, 'since': last})}\n\n")
            while True:
                try:
                    message = channel.get(timeout=20)
                except queue.Empty:
                    self._sse(": ping\n\n")           # comentário SSE = sinal de vida
                    continue
                self._sse("event: mudanca\ndata: "
                          + json.dumps(message, ensure_ascii=False, default=str) + "\n\n")
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass                                        # o navegador foi embora
        finally:
            hooks.unsubscribe(channel)

    def _sse(self, text: str) -> None:
        self.wfile.write(text.encode("utf-8"))
        self.wfile.flush()

    def _serve_page(self, name: str) -> None:
        path = TEMPLATES / name
        if not path.exists():
            return self._send(404, {"error": f"página {name} não encontrada"})
        html = path.read_text(encoding="utf-8")
        html = html.replace("__BASE_CSS__", (TEMPLATES / "theme.css").read_text(encoding="utf-8"))
        if "__ICONS_JS__" in html:
            html = html.replace("__ICONS_JS__", (TEMPLATES / "icons.js").read_text(encoding="utf-8"))
        self._send(200, html, "text/html")

    def _serve_database(self) -> None:
        db = Database(self.db_path)
        try:
            user, _ = self._resolve_user(db)
            auth.require(user, "admin")
        except auth.AuthError as exc:
            return self._send(exc.status, {"error": exc.message})
        finally:
            db.close()
        if not self.db_path.exists():
            return self._send(404, {"error": "banco não encontrado"})
        self._send(200, self.db_path.read_bytes(), "application/vnd.sqlite3",
                   [("Content-Disposition", 'attachment; filename="lape.sqlite"')])

    def _serve_export(self, query: dict) -> None:
        """Tabela de extracao da producao, nos formatos de troca.

        `formato=csv|bibtex|ris`; `publicados=1` limita ao que ja saiu. Vai
        como anexo para o navegador salvar o arquivo em vez de exibi-lo.
        """
        db = Database(self.db_path)
        try:
            user, _ = self._resolve_user(db)
            if not PUBLIC_DASHBOARD:
                auth.require(user, "leitura")
            formato = (query.get("formato") or ["csv"])[0].strip().lower()
            publicados = (query.get("publicados") or ["0"])[0] in ("1", "true", "sim")
            conteudo, nome, mime = export.extrair(db, formato, publicados)
        except auth.AuthError as exc:
            return self._send(exc.status, {"error": exc.message})
        except ValueError as exc:
            return self._send(400, {"error": str(exc)})
        except Exception as exc:  # nunca derruba o servidor
            traceback.print_exc()
            return self._send(500, {"error": f"falha ao extrair: {exc}"})
        finally:
            db.close()
        self._send(200, conteudo, mime,
                   [("Content-Disposition", f'attachment; filename="{nome}"')])

    def _serve_planilha(self) -> None:
        """A planilha do laboratorio, com o cadastro de agora.

        Ela ja e reescrita sozinha em segundo plano; aqui a gente so garante
        que quem clicou nao vai baixar a versao de antes do ultimo cadastro.
        """
        from . import planilha

        db = Database(self.db_path)
        try:
            user, _ = self._resolve_user(db)
            if not PUBLIC_DASHBOARD:
                auth.require(user, "leitura")
            planilha.rodar(db, db_path=self.db_path)
            alvo = planilha.caminho(self.db_path)
            if not alvo.exists():
                alvo = Path(planilha.gerar(db, db_path=self.db_path))
        except auth.AuthError as exc:
            return self._send(exc.status, {"error": exc.message})
        except Exception as exc:  # nunca derruba o servidor
            traceback.print_exc()
            return self._send(500, {"error": f"falha ao montar a planilha: {exc}"})
        finally:
            db.close()
        self._send(200, alvo.read_bytes(),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   [("Content-Disposition", f'attachment; filename="{alvo.name}"')])


BACKUP_INTERVALO_S = int(os.environ.get("LAPE_BACKUP_CHECAGEM_S", "300"))


def _agendar_backup(db_path: Path) -> threading.Event:
    """Copia de seguranca e planilha que acompanham o cadastro, sozinhas.

    Uma linha de execucao propria acorda de tempos em tempos e pergunta ao
    modulo `backup` se ha motivo -- cadastro novo desde a ultima copia, ou
    um dia inteiro sem nenhuma. Cada checagem abre e fecha a sua conexao:
    conexao de SQLite nao atravessa linhas de execucao.

    Falhar aqui nao pode derrubar o servico: um disco cheio e um problema
    para resolver, nao motivo para o laboratorio ficar fora do ar. Por isso
    o aviso e impresso e a vida segue.
    """
    parar = threading.Event()
    if os.environ.get("LAPE_BACKUP", "1") == "0":
        return parar

    def rodar() -> None:
        from . import backup, planilha

        while not parar.is_set():
            try:
                db = Database(db_path)
                try:
                    feito = backup.rodar(db, db_path=db_path)
                finally:
                    db.close()
                if feito:
                    print(f"  backup: {Path(feito['arquivo']).name}"
                          f" ({feito['bytes'] // 1024} kB) — {feito['motivo']}")
            except Exception as exc:                      # nunca derruba o servico
                print(f"  ! backup falhou: {type(exc).__name__}: {exc}")
            # A planilha e o espelho do cadastro em Excel. Vai na mesma volta
            # da copia de seguranca, com a sua propria conta de mudancas: um
            # erro ao escrever o .xlsx (Excel aberto, disco cheio) nao pode
            # levar junto a copia de seguranca, nem o servico.
            if os.environ.get("LAPE_PLANILHA", "1") != "0":
                try:
                    db = Database(db_path)
                    try:
                        feita = planilha.rodar(db, db_path=db_path)
                    finally:
                        db.close()
                    if feita.get("gerou"):
                        print(f"  planilha: {Path(feita['arquivo']).name} — {feita['motivo']}")
                except Exception as exc:                  # nunca derruba o servico
                    print(f"  ! planilha falhou: {type(exc).__name__}: {exc}")
            parar.wait(BACKUP_INTERVALO_S)

    threading.Thread(target=rodar, name="lape-backup", daemon=True).start()
    return parar


def serve(host: str = "127.0.0.1", port: int = 8000, db_path: Path = config.DB_PATH,
          report_path: Path = config.REPORT_PATH) -> None:
    Handler.db_path = Path(db_path)
    Handler.report_path = Path(report_path)
    db = Database(db_path)
    db.migrate()
    try:
        created = auth.bootstrap_admin(db)
    except auth.AuthError as exc:
        # falha fechado: e melhor nao subir do que subir com a senha do tutorial
        db.close()
        raise SystemExit(f"\n  ! {exc.message}\n")
    users = int(db.scalar("SELECT COUNT(*) FROM members WHERE login IS NOT NULL") or 0)
    db.close()

    publico = host not in ("127.0.0.1", "localhost", "::1")
    print(f"LAPE em http://{host}:{port}")
    print(f"  painel ............ http://{host}:{port}/")
    print(f"  entrar ............ http://{host}:{port}/entrar")
    print(f"  área do integrante  http://{host}:{port}/app")
    print(f"  API ............... http://{host}:{port}/api")
    print(f"  banco ............. {db_path}")
    print(f"  painel público .... {'sim' if PUBLIC_DASHBOARD else 'não (exige login)'}")
    print(f"  usuários .......... {users}")
    if publico and not BEHIND_HTTPS:
        print("\n  ! Este endereço é alcançável de fora desta máquina e o tráfego não")
        print("    está cifrado: a senha vai em texto claro pela rede. Para publicar,")
        print("    ponha o Caddy (ou o túnel do Cloudflare) na frente e defina")
        print("    LAPE_BEHIND_HTTPS=1 — veja 'Publicar na nuvem' no README.")
    if publico and not TRUST_PROXY:
        print("  ! Atrás de proxy, defina LAPE_TRUST_PROXY=1, senão o travamento por")
        print("    tentativa e erro vê todo mundo com o mesmo endereço.")
    if created:
        print(f"\n  ADMINISTRADOR CRIADO: {created['login']}")
        if "senha_inicial" in created:
            print(f"  SENHA INICIAL: {created['senha_inicial']}  (troque no primeiro acesso)")
    elif not users:
        print("\n  ! Nenhum usuário cadastrado. Crie o primeiro administrador:")
        print("      python3 scripts/lape_agent.py usuarios --criar 'Nome' email@udesc.br --perfil admin")

    parar_backup = _agendar_backup(Path(db_path))

    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nservidor encerrado")
    finally:
        parar_backup.set()
        server.server_close()
