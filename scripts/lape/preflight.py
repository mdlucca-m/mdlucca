"""Conferência antes de publicar o LAPE na internet.

Enquanto o serviço mora em 127.0.0.1, quase nada disto importa: quem alcança
a porta já está sentado na máquina. Publicado, cada item vira uma porta que
pode ficar destrancada — e é fácil esquecer um deles no meio da instalação.

Este módulo não conserta nada: ele olha o ambiente e o banco e diz, em
português, o que ainda falta. Cada achado tem uma gravidade e uma instrução
do que fazer.

    python3 scripts/lape_agent.py publicar
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

from . import auth
from .db import Database

# gravidade -> como aparece na saída
NIVEIS = {"impede": "IMPEDE", "risco": "RISCO ", "aviso": "AVISO ", "ok": "  ok  "}


def _item(nivel: str, titulo: str, detalhe: str = "") -> dict[str, str]:
    return {"nivel": nivel, "titulo": titulo, "detalhe": detalhe}


def conferir(db: Database, ambiente: dict[str, str] | None = None) -> list[dict[str, str]]:
    """Devolve a lista de achados, do mais grave para o menos."""
    env = ambiente if ambiente is not None else dict(os.environ)
    achados: list[dict[str, str]] = []

    # ---------------------------------------------------------------- HTTPS
    if env.get("LAPE_BEHIND_HTTPS") == "1":
        achados.append(_item("ok", "Cookie de sessão marcado como Secure"))
    else:
        achados.append(_item(
            "impede", "Sem HTTPS: a senha viaja em texto claro",
            "Ponha o Caddy ou o túnel do Cloudflare na frente e defina "
            "LAPE_BEHIND_HTTPS=1. O docker-compose.prod.yml já faz as duas coisas."))

    # ---------------------------------------------------------------- proxy
    if env.get("LAPE_TRUST_PROXY") == "1":
        achados.append(_item("ok", "Endereço real do visitante lido do proxy"))
    else:
        achados.append(_item(
            "aviso", "LAPE_TRUST_PROXY desligado",
            "Atrás de proxy, o travamento por tentativa e erro vê todo mundo com o "
            "mesmo endereço. Ligue SÓ se houver mesmo um proxy na frente."))

    # ------------------------------------------------------------ acessos
    admins = int(db.scalar(
        "SELECT COUNT(*) FROM members WHERE user_role = 'admin' AND login IS NOT NULL") or 0)
    usuarios = int(db.scalar("SELECT COUNT(*) FROM members WHERE login IS NOT NULL") or 0)
    if not admins:
        achados.append(_item(
            "impede", "Nenhum administrador cadastrado",
            "python3 scripts/lape_agent.py usuarios --criar 'Nome' email@udesc.br --perfil admin"))
    else:
        achados.append(_item("ok", f"{admins} administrador(es), {usuarios} acesso(s) no total"))

    motivo = auth.senha_fraca(env.get("LAPE_ADMIN_PASSWORD"))
    if env.get("LAPE_ADMIN_PASSWORD") and motivo:
        achados.append(_item(
            "impede", f"LAPE_ADMIN_PASSWORD não serve: {motivo}",
            'python3 -c "import secrets; print(secrets.token_urlsafe(18))"'))

    pendentes = int(db.scalar(
        "SELECT COUNT(*) FROM members WHERE login IS NOT NULL AND must_change_password = 1") or 0)
    if pendentes:
        achados.append(_item(
            "aviso", f"{pendentes} acesso(s) ainda com a senha inicial",
            "Quem recebeu senha da coordenação precisa trocá-la no primeiro acesso."))

    # ------------------------------------------------------------ sessões
    velhas = int(db.scalar(
        "SELECT COUNT(*) FROM sessions WHERE expires_at < datetime('now')") or 0)
    if velhas:
        achados.append(_item(
            "aviso", f"{velhas} sessão(ões) vencidas no banco",
            "São apagadas no próximo login; nenhuma delas ainda dá acesso."))

    # --------------------------------------------------------- painel público
    if env.get("LAPE_PUBLIC_DASHBOARD") == "1":
        achados.append(_item(
            "risco", "Painel visível sem login",
            "Qualquer pessoa com o endereço vê os indicadores, inclusive artigos "
            "ainda não publicados. A área de cadastro segue protegida. "
            "Se não era a intenção, use LAPE_PUBLIC_DASHBOARD=0."))
    else:
        achados.append(_item("ok", "Painel exige login"))

    # ------------------------------------------------------------- automação
    hooks = int(db.scalar("SELECT COUNT(*) FROM webhooks WHERE active = 1") or 0)
    if hooks and not env.get("LAPE_WEBHOOK_SECRET"):
        achados.append(_item(
            "risco", f"{hooks} webhook(s) cadastrados sem segredo de assinatura",
            "Sem LAPE_WEBHOOK_SECRET o destino não tem como provar que a mensagem "
            "saiu do LAPE. Gere um e recadastre os destinos."))
    if env.get("LAPE_API_TOKEN") and len(env["LAPE_API_TOKEN"]) < 24:
        achados.append(_item(
            "risco", "LAPE_API_TOKEN curto demais",
            "Ele vale como senha de serviço. Use pelo menos 32 caracteres aleatórios."))

    # ------------------------------------------------------------ convites
    try:
        abertos = db.dicts(
            "SELECT label, max_uses - uses AS vagas, expires_at FROM invites"
            " WHERE revoked = 0 AND uses < max_uses"
            " AND (expires_at IS NULL OR expires_at > datetime('now'))")
    except Exception:
        abertos = []
    if abertos:
        vagas = sum(int(c["vagas"] or 0) for c in abertos)
        sem_prazo = [c for c in abertos if not c["expires_at"]]
        achados.append(_item(
            "risco" if sem_prazo else "aviso",
            f"{len(abertos)} convite(s) em aberto, {vagas} vaga(s) de cadastro",
            "Quem tiver o link cria acesso sozinho. Cancele os que ja circularam "
            "em Area do integrante -> Administracao."
            + (" Ha convite sem prazo de validade." if sem_prazo else "")))

    # --------------------------------------------------------------- dados
    caminho = str(db.path)
    if caminho.startswith("/app/") or caminho.startswith("/tmp/"):
        achados.append(_item(
            "impede", f"Banco em caminho efêmero ({caminho})",
            "Num contêiner, /app se perde a cada atualização da imagem. Aponte "
            "LAPE_DB para um volume — /dados/db.sqlite no compose de produção."))
    else:
        achados.append(_item("ok", f"Banco em {caminho}"))

    ultimo = db.dicts(
        "SELECT run_at FROM ingest_log WHERE source = 'backup' ORDER BY id DESC LIMIT 1")
    if not ultimo:
        achados.append(_item(
            "aviso", "Nenhum backup registrado",
            "deploy/backup.sh faz cópia diária. Um banco sem cópia é um "
            "laboratório a uma falha de disco de perder tudo."))
    else:
        quando = str(ultimo[0]["run_at"])
        try:
            atrasado = datetime.fromisoformat(quando) < datetime.now() - timedelta(days=7)
        except ValueError:
            atrasado = False
        achados.append(_item("aviso" if atrasado else "ok",
                             f"Último backup em {quando}"))

    ordem = {"impede": 0, "risco": 1, "aviso": 2, "ok": 3}
    return sorted(achados, key=lambda a: ordem[a["nivel"]])


def resumo(achados: list[dict[str, str]]) -> dict[str, Any]:
    contagem = {n: sum(1 for a in achados if a["nivel"] == n) for n in NIVEIS}
    return {
        "pronto": contagem["impede"] == 0,
        "impedimentos": contagem["impede"],
        "riscos": contagem["risco"],
        "avisos": contagem["aviso"],
        "itens": achados,
    }


def imprimir(achados: list[dict[str, str]]) -> bool:
    """Escreve o relatório e devolve True se nada impede a publicação."""
    print("Conferência para publicar na internet\n")
    for achado in achados:
        print(f"  [{NIVEIS[achado['nivel']]}] {achado['titulo']}")
        if achado["detalhe"]:
            for linha in _quebrar(achado["detalhe"], 72):
                print(f"           {linha}")
    dados = resumo(achados)
    print()
    if dados["pronto"]:
        print("  Nada impede a publicação.", end="")
        if dados["riscos"]:
            print(f" Ainda há {dados['riscos']} risco(s) para decidir conscientemente.", end="")
        print()
    else:
        print(f"  {dados['impedimentos']} item(ns) impedem a publicação. "
              "Resolva antes de expor o endereço.")
    return dados["pronto"]


def _quebrar(texto: str, largura: int) -> list[str]:
    linhas, atual = [], ""
    for palavra in texto.split():
        if len(atual) + len(palavra) + 1 > largura:
            linhas.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    if atual:
        linhas.append(atual)
    return linhas
