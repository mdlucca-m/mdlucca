"""Autenticacao e controle de acesso do LAPE.

Cada integrante cadastrado pode receber login e senha e passa a acessar a
area restrita para manter o proprio perfil, seus artigos, projetos e
submissoes. Nao ha dependencia externa: as senhas usam PBKDF2-HMAC-SHA256
da biblioteca padrao e as sessoes sao tokens aleatorios guardados no banco.

Perfis de acesso:
  admin        pode tudo, inclusive criar usuarios e rodar os agentes
  coordenacao  pode editar qualquer registro, mas nao gerencia usuarios
  integrante   edita o proprio perfil e cria/edita os registros em que
               participa (artigos, submissoes, projetos)
  leitura      so consulta
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Any

from .db import Database
from .util import clean_text

ITERATIONS = 240_000
SALT_BYTES = 16
SESSION_DAYS = int(os.environ.get("LAPE_SESSION_DAYS", "14"))
MIN_PASSWORD = 8

# Travamento por tentativa e erro. Enquanto o servico morava em 127.0.0.1 isso
# nao fazia diferenca; publicado na internet, e a primeira coisa que alguem
# tenta. A contagem sai do proprio audit_log, entao sobrevive a um reinicio.
LOCK_WINDOW_MIN = int(os.environ.get("LAPE_LOCK_WINDOW_MIN", "15"))
LOCK_AFTER_LOGIN = int(os.environ.get("LAPE_LOCK_AFTER_LOGIN", "8"))
LOCK_AFTER_IP = int(os.environ.get("LAPE_LOCK_AFTER_IP", "25"))

# Hash descartavel, usado quando o login nao existe. Sem ele, uma tentativa
# com login inexistente responde na hora e uma com login valido demora os
# ~100ms do PBKDF2 -- diferenca suficiente para descobrir quem tem conta.
_DUMMY_HASH = ("pbkdf2_sha256$240000$"
               "00000000000000000000000000000000$"
               + "0" * 64)

ROLES = ("admin", "coordenacao", "integrante", "leitura")
ROLE_RANK = {"leitura": 0, "integrante": 1, "coordenacao": 2, "admin": 3}


class AuthError(Exception):
    """Falha de autenticacao ou de permissao."""

    def __init__(self, message: str, status: int = 401) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


# ----------------------------------------------------------------------
# Senhas
# ----------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Devolve 'pbkdf2_sha256$iteracoes$salt$hash' (formato autoexplicativo)."""
    if len(password or "") < MIN_PASSWORD:
        raise AuthError(f"a senha precisa de pelo menos {MIN_PASSWORD} caracteres", 400)
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored or not password:
        return False
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def generate_password(length: int = 12) -> str:
    """Senha inicial legivel, sem caracteres ambiguos."""
    alphabet = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def normalize_login(value: Any) -> str:
    login = (clean_text(value) or "").strip().lower()
    if not login:
        raise AuthError("informe um login (use o e-mail institucional)", 400)
    if not re.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|[a-z0-9._-]{3,}", login):
        raise AuthError("login invalido: use um e-mail ou um identificador simples", 400)
    return login


# ----------------------------------------------------------------------
# Contas
# ----------------------------------------------------------------------
def set_credentials(db: Database, member_id: int, login: str, password: str,
                    role: str = "integrante", must_change: bool = True) -> dict[str, Any]:
    if role not in ROLES:
        raise AuthError(f"perfil invalido: {role}. Use {', '.join(ROLES)}", 400)
    login = normalize_login(login)
    taken = db.dicts("SELECT id FROM members WHERE login = ? AND id <> ?", (login, member_id))
    if taken:
        raise AuthError(f"o login '{login}' ja pertence a outro integrante", 409)
    db.execute(
        "UPDATE members SET login = ?, password_hash = ?, user_role = ?,"
        " must_change_password = ?, updated_at = datetime('now') WHERE id = ?",
        (login, hash_password(password), role, 1 if must_change else 0, member_id),
    )
    db.conn.commit()
    log(db, member_id, login, "credenciais_definidas", "members", member_id, f"perfil={role}")
    return {"member_id": member_id, "login": login, "role": role,
            "must_change_password": must_change}


def _nome_mais_completo(guardado: str | None, digitado: str) -> bool:
    """O nome digitado e o mesmo, so que inteiro?

    A planilha costuma trazer "Andrade"; a pessoa, ao criar o proprio acesso,
    digita "Alexandro Andrade". Quando o guardado cabe dentro do digitado, o
    digitado e melhor -- e so nesse caso trocamos, para nunca substituir um
    nome bom por um pior.
    """
    if not guardado or not digitado:
        return False
    def partes(texto: str) -> list[str]:
        return [t.strip(".").lower() for t in texto.split() if t.strip(".")]
    velhas, novas = partes(guardado), partes(digitado)
    if not velhas:
        return False
    for parte in velhas:
        # inicial casa com a palavra inteira: "A" reconhece "Alexandro"
        if not any(nova == parte or (len(parte) == 1 and nova.startswith(parte))
                   for nova in novas):
            return False
    # melhor = mais partes, ou as mesmas partes com menos iniciais soltas.
    # "Andrade A." e "Alexandro Andrade" tem duas partes cada, mas o segundo
    # troca uma inicial por um nome.
    inteiras = lambda lista: sum(1 for x in lista if len(x) > 1)
    return len(novas) > len(velhas) or inteiras(novas) > inteiras(velhas)


def create_account(db: Database, full_name: str, login: str, password: str | None = None,
                   role: str = "integrante", **extra: Any) -> dict[str, Any]:
    """Cria (ou reaproveita) o integrante e lhe da acesso.

    Reaproveitar importa: o registro que veio da planilha ja tem os artigos
    da pessoa ligados a ele. Criar um segundo registro deixaria a producao
    dela orfa no painel.
    """
    member_id = db.member_id(full_name, create=True, **extra)
    if member_id is None:
        raise AuthError("nao foi possivel identificar o nome informado", 400)
    guardado = db.scalar("SELECT full_name FROM members WHERE id = ?", (member_id,))
    if _nome_mais_completo(guardado, full_name):
        db.execute("UPDATE members SET full_name = ?, updated_at = datetime('now')"
                   " WHERE id = ?", (clean_text(full_name), member_id))
        db.conn.commit()
    generated = password is None
    password = password or generate_password()
    result = set_credentials(db, member_id, login, password, role, must_change=generated)
    if generated:
        result["senha_inicial"] = password
    return result


def change_password(db: Database, member_id: int, current: str, new: str) -> dict[str, Any]:
    row = db.dicts("SELECT password_hash FROM members WHERE id = ?", (member_id,))
    if not row or not verify_password(current, row[0]["password_hash"]):
        raise AuthError("senha atual incorreta", 403)
    db.execute(
        "UPDATE members SET password_hash = ?, must_change_password = 0,"
        " updated_at = datetime('now') WHERE id = ?",
        (hash_password(new), member_id),
    )
    db.conn.commit()
    log(db, member_id, None, "senha_alterada", "members", member_id)
    return {"ok": True}


# ----------------------------------------------------------------------
# Convites: a pessoa se cadastra sozinha
# ----------------------------------------------------------------------
INVITE_DAYS = int(os.environ.get("LAPE_INVITE_DAYS", "14"))


def create_invite(db: Database, created_by: int | None = None, label: str | None = None,
                  role: str = "integrante", max_uses: int = 30,
                  days: int = INVITE_DAYS) -> dict[str, Any]:
    """Gera um link de convite.

    O padrao e um link de equipe: vale para varias pessoas e vence em duas
    semanas. Um link sem prazo que circula em grupo de mensagens vira porta
    aberta meses depois, quando ninguem mais lembra dele.
    """
    if role not in ROLES:
        raise AuthError(f"perfil invalido: {role}. Use {', '.join(ROLES)}", 400)
    if role == "admin":
        raise AuthError("convite nao cria administrador: eleve o perfil depois, "
                        "com a pessoa ja identificada", 400)
    max_uses = max(1, min(int(max_uses), 200))
    days = max(1, min(int(days), 90))
    token = secrets.token_urlsafe(24)
    expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "INSERT INTO invites (token, label, user_role, max_uses, expires_at, created_by)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (token, clean_text(label), role, max_uses, expires, created_by))
    db.conn.commit()
    log(db, created_by, None, "convite_criado", "invites", None,
        f"perfil={role} usos={max_uses} vence={expires}")
    return {"token": token, "user_role": role, "max_uses": max_uses,
            "expires_at": expires, "label": clean_text(label)}


def invite_state(db: Database, token: str) -> dict[str, Any]:
    """Diz se o convite serve, e por que nao serve quando for o caso."""
    rows = db.dicts("SELECT * FROM invites WHERE token = ?", (token or "",))
    if not rows:
        return {"valid": False, "reason": "Este convite nao existe."}
    convite = rows[0]
    if convite["revoked"]:
        return {"valid": False, "reason": "Este convite foi cancelado pela coordenacao."}
    if convite["uses"] >= convite["max_uses"]:
        return {"valid": False, "reason": "Este convite ja atingiu o limite de cadastros."}
    if convite["expires_at"] and convite["expires_at"] < datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
        return {"valid": False, "reason": "Este convite venceu. Peca um novo a coordenacao."}
    return {"valid": True, "label": convite["label"], "user_role": convite["user_role"],
            "expires_at": convite["expires_at"],
            "remaining": convite["max_uses"] - convite["uses"]}


def accept_invite(db: Database, token: str, full_name: str, login_value: str,
                  password: str, ip: str = "") -> dict[str, Any]:
    """Cria o acesso a partir do convite e ja devolve a sessao aberta.

    A senha e escolhida pela propria pessoa: assim ela nunca trafega por
    mensagem, e a coordenacao nunca a conhece.
    """
    estado = invite_state(db, token)
    if not estado["valid"]:
        raise AuthError(estado["reason"], 410)
    if not clean_text(full_name):
        raise AuthError("informe seu nome completo", 400)
    motivo = senha_fraca(password)
    if motivo:
        raise AuthError(f"escolha outra senha: ela {motivo}", 400)
    login_value = normalize_login(login_value)
    if db.dicts("SELECT id FROM members WHERE login = ?", (login_value,)):
        raise AuthError("ja existe acesso com este e-mail. Use 'entrar' ou peca "
                        "a redefinicao da senha a coordenacao.", 409)

    convite = db.dicts("SELECT * FROM invites WHERE token = ?", (token,))[0]
    conta = create_account(db, clean_text(full_name), login_value, password,
                           role=convite["user_role"])
    # o mesmo UPDATE confere o limite de novo: duas pessoas clicando ao mesmo
    # tempo no ultimo uso nao podem passar as duas
    db.execute("UPDATE invites SET uses = uses + 1 WHERE id = ? AND uses < max_uses",
               (convite["id"],))
    db.execute("INSERT INTO invite_uses (invite_id, member_id, ip) VALUES (?, ?, ?)",
               (convite["id"], conta["member_id"], (ip or None) and ip[:60]))
    db.conn.commit()
    log(db, conta["member_id"], login_value, "cadastro_por_convite", "invites",
        convite["id"], None, ip)
    sessao = login(db, login_value, password, ip=ip)
    sessao["created"] = conta
    return sessao


def list_invites(db: Database, limit: int = 40) -> list[dict]:
    return db.dicts(
        "SELECT i.id, i.token, i.label, i.user_role, i.max_uses, i.uses, i.expires_at,"
        "       i.revoked, i.created_at, m.full_name AS created_by_name"
        " FROM invites i LEFT JOIN members m ON m.id = i.created_by"
        " ORDER BY i.id DESC LIMIT ?", (limit,))


def revoke_invite(db: Database, invite_id: int, actor: int | None = None) -> dict[str, Any]:
    db.execute("UPDATE invites SET revoked = 1 WHERE id = ?", (invite_id,))
    db.conn.commit()
    log(db, actor, None, "convite_cancelado", "invites", invite_id)
    return {"revoked": invite_id}


# ----------------------------------------------------------------------
# Sessoes
# ----------------------------------------------------------------------
def recent_failures(db: Database, login_value: str | None = None,
                    ip: str | None = None) -> int:
    """Falhas de login na janela recente, por login ou por origem."""
    if login_value:
        campo, valor = "login", login_value
    elif ip:
        campo, valor = "ip", ip
    else:
        return 0
    return int(db.scalar(
        f"SELECT COUNT(*) FROM audit_log WHERE action = 'login_negado' AND {campo} = ?"
        f" AND at > datetime('now', ?)",
        (valor, f"-{LOCK_WINDOW_MIN} minutes")) or 0)


def check_lock(db: Database, login_value: str, ip: str = "") -> None:
    """Barra a tentativa quando ja houve falhas demais na janela.

    Dois contadores, porque protegem de coisas diferentes: o do login barra
    quem martela uma conta so; o do IP barra quem varre varias contas.
    """
    if recent_failures(db, login_value=login_value) >= LOCK_AFTER_LOGIN:
        raise AuthError(
            f"muitas tentativas para este login. Aguarde {LOCK_WINDOW_MIN} minutos"
            " ou peca a redefinicao da senha a coordenacao.", 429)
    if ip and recent_failures(db, ip=ip) >= LOCK_AFTER_IP:
        raise AuthError(
            f"muitas tentativas a partir deste endereco. Aguarde {LOCK_WINDOW_MIN} minutos.",
            429)


def login(db: Database, login_value: str, password: str, user_agent: str = "",
          ip: str = "") -> dict[str, Any]:
    login_value = (clean_text(login_value) or "").strip().lower()
    check_lock(db, login_value, ip)
    rows = db.dicts(
        "SELECT id, full_name, login, password_hash, user_role, active, must_change_password"
        " FROM members WHERE login = ?", (login_value,))
    if not rows:
        # gasta o mesmo tempo de um login que existe, para nao entregar
        # quem tem conta pela demora da resposta
        verify_password(password, _DUMMY_HASH)
        log(db, None, login_value, "login_negado", "sessions", None,
            "login inexistente", ip)
        raise AuthError("login ou senha incorretos", 401)
    if not verify_password(password, rows[0]["password_hash"]):
        log(db, None, login_value, "login_negado", "sessions", None,
            "senha incorreta", ip)
        raise AuthError("login ou senha incorretos", 401)
    member = rows[0]
    if not member["active"]:
        raise AuthError("este acesso esta desativado. Fale com a coordenacao.", 403)

    token = secrets.token_urlsafe(32)
    expires = (datetime.now() + timedelta(days=SESSION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "INSERT INTO sessions (token, member_id, expires_at, user_agent, ip)"
        " VALUES (?, ?, ?, ?, ?)", (token, member["id"], expires, user_agent[:200], ip[:60]))
    db.execute("UPDATE members SET last_login_at = datetime('now') WHERE id = ?", (member["id"],))
    db.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
    db.conn.commit()
    # o acerto zera o contador: quem errou e depois lembrou nao fica travado
    db.execute("DELETE FROM audit_log WHERE action = 'login_negado' AND login = ?",
               (login_value,))
    db.conn.commit()
    log(db, member["id"], member["login"], "login", "sessions", None, None, ip)
    return {
        "token": token,
        "expires_at": expires,
        "user": public_user(db, member["id"]),
    }


def logout(db: Database, token: str) -> dict[str, Any]:
    db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    db.conn.commit()
    return {"ok": True}


def current_user(db: Database, token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    rows = db.dicts(
        "SELECT s.member_id FROM sessions s WHERE s.token = ? AND s.expires_at > datetime('now')",
        (token,))
    return public_user(db, rows[0]["member_id"]) if rows else None


def public_user(db: Database, member_id: int) -> dict[str, Any]:
    rows = db.dicts(
        "SELECT id, full_name, short_name, login, user_role, must_change_password, email,"
        " role, research_line, photo_url, n_articles, n_published, n_projects, h_index"
        " FROM v_researcher WHERE id = ?", (member_id,))
    if not rows:
        raise AuthError("integrante nao encontrado", 404)
    return rows[0]


# ----------------------------------------------------------------------
# Permissoes
# ----------------------------------------------------------------------
def require(user: dict[str, Any] | None, minimum: str = "integrante") -> dict[str, Any]:
    if user is None:
        raise AuthError("e preciso entrar para fazer isso", 401)
    if ROLE_RANK.get(user.get("user_role", "leitura"), 0) < ROLE_RANK[minimum]:
        raise AuthError("seu perfil nao permite esta acao", 403)
    return user


def can_edit_member(user: dict[str, Any], member_id: int) -> bool:
    """Integrante edita o proprio cadastro; coordenacao edita qualquer um."""
    if ROLE_RANK.get(user.get("user_role", "leitura"), 0) >= ROLE_RANK["coordenacao"]:
        return True
    return int(user["id"]) == int(member_id)


def can_edit_article(db: Database, user: dict[str, Any], article_id: int) -> bool:
    if ROLE_RANK.get(user.get("user_role", "leitura"), 0) >= ROLE_RANK["coordenacao"]:
        return True
    return bool(db.scalar(
        "SELECT 1 FROM article_authors WHERE article_id = ? AND member_id = ?"
        " UNION SELECT 1 FROM articles WHERE id = ? AND lead_member_id = ?",
        (article_id, user["id"], article_id, user["id"])))


# ----------------------------------------------------------------------
# Auditoria
# ----------------------------------------------------------------------
def log(db: Database, member_id: int | None, login_value: str | None, action: str,
        entity: str | None = None, entity_id: Any = None, detail: str | None = None,
        ip: str | None = None) -> None:
    db.execute(
        "INSERT INTO audit_log (member_id, login, action, entity, entity_id, detail, ip)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (member_id, login_value, action, entity, str(entity_id) if entity_id else None,
         detail, (ip or None) and ip[:60]),
    )
    db.conn.commit()


# Senhas que aparecem em modelo de configuracao e em tutorial. Servem para o
# primeiro teste na propria maquina; publicadas na internet, sao conta aberta.
SENHAS_DE_EXEMPLO = frozenset({
    "troque-por-uma-senha-longa", "troque-esta-senha", "senha", "senha123",
    "12345678", "123456789", "admin", "admin123", "lape", "lape2026",
    "mudar123", "trocar123", "password", "demonstracao123",
})


def senha_fraca(password: str | None) -> str | None:
    """Devolve o motivo pelo qual a senha nao serve, ou None se serve."""
    if not password or len(password) < MIN_PASSWORD:
        return f"tem menos de {MIN_PASSWORD} caracteres"
    if password.strip().lower() in SENHAS_DE_EXEMPLO:
        return "e uma das senhas de exemplo da documentacao"
    if len(set(password)) < 4:
        return "repete poucos caracteres diferentes"
    return None


def bootstrap_admin(db: Database, login_value: str | None = None,
                    password: str | None = None) -> dict[str, Any] | None:
    """Cria o primeiro administrador se ainda nao existir nenhum.

    Le LAPE_ADMIN_LOGIN e LAPE_ADMIN_PASSWORD do ambiente, o que permite
    subir o servico na nuvem ja com acesso configurado.

    Recusa senha de exemplo. Enquanto o servico morava em 127.0.0.1 isso era
    detalhe; publicado, uma senha de tutorial e a porta destrancada -- e o
    modelo .env.example traz uma justamente para ser trocada.
    """
    if db.scalar("SELECT COUNT(*) FROM members WHERE user_role = 'admin' AND login IS NOT NULL"):
        return None
    login_value = login_value or os.environ.get("LAPE_ADMIN_LOGIN")
    password = password or os.environ.get("LAPE_ADMIN_PASSWORD")
    if not login_value:
        return None
    motivo = senha_fraca(password)
    if motivo:
        raise AuthError(
            f"a senha do primeiro administrador nao serve: {motivo}."
            " Ajuste LAPE_ADMIN_PASSWORD antes de publicar o servico.", 400)
    name = os.environ.get("LAPE_ADMIN_NAME", "Administracao LAPE")
    return create_account(db, name, login_value, password, role="admin")
