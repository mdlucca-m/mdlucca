"""Barramento de eventos do LAPE — tempo real no painel e integração com o n8n.

Todo fato relevante do sistema (artigo cadastrado, achado aprovado, agente
concluído, lakehouse reconstruído) vira um evento. Um evento faz três coisas:

  1. entra em `change_log`, que é o histórico auditável do que aconteceu;
  2. acorda quem estiver assinando `/api/stream`, e o painel redesenha na hora;
  3. é entregue aos webhooks cadastrados — é assim que o n8n fica sabendo.

Segurança da entrega
  Cada webhook tem um segredo. O corpo vai assinado em
  `X-LAPE-Signature: sha256=<hmac>`, e o n8n confere o mesmo HMAC antes de
  agir. Na direção contrária (o n8n chamando o LAPE), a mesma assinatura é
  exigida — ou o token de serviço, para quem preferir cabeçalho simples.

Entrega
  Em segundo plano, com três tentativas e espera crescente. Uma automação
  fora do ar nunca trava o cadastro de um artigo.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import queue
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Callable

from .db import Database

WEBHOOK_SECRET = os.environ.get("LAPE_WEBHOOK_SECRET", "")
DELIVERY_TIMEOUT = 15
DELIVERY_RETRIES = 3
MAX_SUBSCRIBERS = 32

# Catálogo de eventos. O painel e o n8n filtram por estes nomes; '*' vale para todos.
EVENTS: dict[str, str] = {
    "artigo.cadastrado": "Artigo criado ou atualizado",
    "artigo.publicado": "Artigo passou para publicado",
    "submissao.registrada": "Nova tentativa de submissão",
    "submissao.recusada": "Submissão recusada",
    "submissao.aceita": "Submissão aceita",
    "projeto.cadastrado": "Projeto criado ou atualizado",
    "integrante.cadastrado": "Integrante criado ou atualizado",
    "evento.cadastrado": "Atividade ou reunião cadastrada",
    "descoberta.encontrada": "O rastreador encontrou publicação nova",
    "descoberta.aceita": "Achado promovido a artigo do banco",
    "agente.concluido": "Um agente terminou de rodar",
    "lake.atualizado": "Camada analítica reconstruída",
    "dados.alterados": "Algo mudou — o painel precisa redesenhar",
}


# ----------------------------------------------------------------------
# Assinantes em memória (o streaming do painel)
# ----------------------------------------------------------------------
_subscribers: list[queue.Queue] = []
_lock = threading.Lock()


def subscribe() -> queue.Queue:
    """Abre uma fila para um cliente de streaming."""
    channel: queue.Queue = queue.Queue(maxsize=64)
    with _lock:
        while len(_subscribers) >= MAX_SUBSCRIBERS:
            _subscribers.pop(0)          # descarta o mais antigo
        _subscribers.append(channel)
    return channel


def unsubscribe(channel: queue.Queue) -> None:
    with _lock:
        if channel in _subscribers:
            _subscribers.remove(channel)


def subscriber_count() -> int:
    with _lock:
        return len(_subscribers)


def _broadcast(message: dict[str, Any]) -> None:
    with _lock:
        targets = list(_subscribers)
    for channel in targets:
        try:
            channel.put_nowait(message)
        except queue.Full:
            pass                          # cliente lento: perde este aviso, não o próximo


# ----------------------------------------------------------------------
# Assinatura
# ----------------------------------------------------------------------
def sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify(secret: str, body: bytes, header: str | None) -> bool:
    if not secret or not header:
        return False
    return hmac.compare_digest(sign(secret, body), header.strip())


# ----------------------------------------------------------------------
# Emissão
# ----------------------------------------------------------------------
def emit(db: Database, event: str, entity: str | None = None, entity_id: Any = None,
         detail: str | None = None, actor: str | None = None,
         payload: dict[str, Any] | None = None, deliver: bool = True) -> dict[str, Any]:
    """Registra o evento, avisa o painel e entrega aos webhooks."""
    now = datetime.now().isoformat(timespec="seconds")
    db.execute(
        "INSERT INTO change_log (event, entity, entity_id, actor, detail)"
        " VALUES (?, ?, ?, ?, ?)",
        (event, entity, str(entity_id) if entity_id is not None else None, actor, detail))
    db.conn.commit()

    message = {
        "event": event, "entity": entity, "entity_id": entity_id,
        "detail": detail, "actor": actor, "at": now, "data": payload or {},
    }
    _broadcast(message)
    if deliver:
        dispatch(db, event, message)
    return message


def bump(db: Database, reason: str = "atualizacao") -> None:
    """Avisa o painel de que algo mudou, sem entrar no catálogo de eventos."""
    emit(db, "dados.alterados", detail=reason, deliver=False)


# ----------------------------------------------------------------------
# Entrega aos webhooks
# ----------------------------------------------------------------------
def targets_for(db: Database, event: str) -> list[dict]:
    return db.dicts(
        "SELECT * FROM webhooks WHERE active = 1 AND (event = ? OR event = '*')"
        " ORDER BY id", (event,))


def dispatch(db: Database, event: str, message: dict[str, Any],
             background: bool = True) -> None:
    """Envia o evento a cada webhook cadastrado que o assine."""
    hooks = targets_for(db, event)
    if not hooks:
        return
    body = json.dumps(message, ensure_ascii=False, default=str).encode("utf-8")
    path = db.path

    def run() -> None:
        """Entrega em segundo plano.

        Roda numa conexão própria porque a do chamador pertence a outra
        thread. Se o banco não abrir (arquivo removido, disco cheio), a
        entrega segue mesmo assim e só o registro se perde: derrubar a
        thread aqui não devolveria nada a ninguém.
        """
        worker = None
        try:
            worker = Database(path)
        except Exception as exc:                # pragma: no cover - disco/arquivo
            print(f"[hooks] sem registro de entrega ({exc})")
        try:
            for hook in hooks:
                try:
                    _deliver(worker, hook, event, body)
                except Exception as exc:        # um destino ruim não afeta os outros
                    print(f"[hooks] falha ao entregar em {hook.get('url')}: {exc}")
        finally:
            if worker is not None:
                worker.close()

    if background:
        threading.Thread(target=run, daemon=True, name="lape-webhooks").start()
    else:
        run()


def _deliver(db: Database | None, hook: dict, event: str, body: bytes) -> None:
    secret = hook.get("secret") or WEBHOOK_SECRET
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "LAPE-Hooks/1.0",
        "X-LAPE-Event": event,
    }
    if secret:
        headers["X-LAPE-Signature"] = sign(secret, body)

    for attempt in range(1, DELIVERY_RETRIES + 1):
        started = time.time()
        try:
            request = urllib.request.Request(hook["url"], data=body, headers=headers,
                                             method="POST")
            with urllib.request.urlopen(request, timeout=DELIVERY_TIMEOUT) as response:
                code = response.status
            _log_delivery(db, hook, event, "ok", code, attempt, started)
            if db is not None:
                db.execute(
                    "UPDATE webhooks SET last_at = datetime('now'), last_status = 'ok',"
                    " failures = 0 WHERE id = ?", (hook["id"],))
                db.conn.commit()
            return
        except urllib.error.HTTPError as exc:
            error, code = f"HTTP {exc.code}", exc.code
        except Exception as exc:
            error, code = str(exc)[:200], None
        _log_delivery(db, hook, event, "erro", code, attempt, started, error)
        if attempt < DELIVERY_RETRIES:
            time.sleep(2 ** attempt)

    if db is not None:
        db.execute(
            "UPDATE webhooks SET last_at = datetime('now'), last_status = 'erro',"
            " failures = failures + 1 WHERE id = ?", (hook["id"],))
        db.conn.commit()


def _log_delivery(db: Database | None, hook: dict, event: str, status: str, code: int | None,
                  attempt: int, started: float, error: str | None = None) -> None:
    if db is None:
        return
    db.execute(
        "INSERT INTO webhook_deliveries (webhook_id, event, status, http_code, attempt,"
        " duration_ms, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (hook["id"], event, status, code, attempt,
         int((time.time() - started) * 1000), error))
    db.conn.commit()


# ----------------------------------------------------------------------
# Cadastro de webhooks
# ----------------------------------------------------------------------
def register(db: Database, name: str, url: str, event: str = "*",
             secret: str | None = None) -> dict[str, Any]:
    if not url.startswith(("http://", "https://")):
        raise ValueError("a URL do webhook precisa começar com http:// ou https://")
    if event != "*" and event not in EVENTS:
        raise ValueError(f"evento desconhecido: {event}. Use '*' ou um de: "
                         + ", ".join(sorted(EVENTS)))
    hook_id = db.upsert(
        "webhooks",
        {"name": name, "url": url, "event": event, "secret": secret or WEBHOOK_SECRET or None,
         "active": 1},
        conflict=("url", "event"))
    db.conn.commit()
    return db.dicts("SELECT id, name, url, event, active, created_at FROM webhooks"
                    " WHERE id = ?", (hook_id,))[0]


def remove(db: Database, hook_id: int) -> dict[str, Any]:
    db.execute("DELETE FROM webhooks WHERE id = ?", (hook_id,))
    db.conn.commit()
    return {"removed": hook_id}


def status(db: Database, limit: int = 40) -> dict[str, Any]:
    """O que o painel mostra na aba de automação."""
    return {
        "events": [{"id": k, "label": v} for k, v in EVENTS.items()],
        "webhooks": db.dicts(
            "SELECT w.*,"
            " (SELECT COUNT(*) FROM webhook_deliveries d WHERE d.webhook_id = w.id) AS deliveries"
            " FROM webhooks w ORDER BY w.id"),
        "deliveries": db.dicts(
            "SELECT d.at, d.event, d.status, d.http_code, d.attempt, d.duration_ms, d.error,"
            "       w.name AS webhook"
            " FROM webhook_deliveries d LEFT JOIN webhooks w ON w.id = d.webhook_id"
            " ORDER BY d.id DESC LIMIT ?", (limit,)),
        "recent": db.dicts(
            "SELECT at, event, entity, entity_id, actor, detail FROM change_log"
            " ORDER BY id DESC LIMIT ?", (limit,)),
        "subscribers": subscriber_count(),
        "signing": bool(WEBHOOK_SECRET),
    }


def since(db: Database, last_id: int = 0, limit: int = 50) -> list[dict]:
    """Eventos posteriores a um id — reserva de quem perdeu a conexão."""
    return db.dicts(
        "SELECT id, at, event, entity, entity_id, detail FROM change_log"
        " WHERE id > ? ORDER BY id LIMIT ?", (last_id, limit))


def latest_id(db: Database) -> int:
    return int(db.scalar("SELECT COALESCE(MAX(id), 0) FROM change_log") or 0)
