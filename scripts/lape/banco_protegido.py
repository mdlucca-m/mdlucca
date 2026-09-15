"""Impedir que o banco do laboratorio va para um repositorio publico.

O `data/db.sqlite` esta versionado desde o primeiro commit, e nao ha como
"des-versionar" sem consequencia: um commit que o remove faz o `git pull`
da maquina do laboratorio ABORTAR para sempre, porque o banco de la esta
modificado e o merge quereria apaga-lo. Medido, nao suposto -- o "Abrir
LAPE" passaria a dizer "nao deu para atualizar agora" em toda subida, e o
sistema ficaria congelado numa versao antiga sem ninguem entender por que.

A copia que esta no Git e de 19 artigos e 17 primeiros nomes, sem login,
sem senha, sem e-mail e sem telefone -- conferidas as DEZ versoes do
historico, uma por uma. O risco nao e ela: e a PROXIMA. Um `git add -A`
na maquina do laboratorio hoje empurraria o banco vivo -- com os logins e
os hashes de senha de quem tem conta -- para um repositorio publico, e
esse commit fica no historico mesmo depois de apagado.

Duas travas, e nao uma:

  1. `skip-worktree` no `data/db.sqlite`. O git passa a ignorar as
     modificacoes locais desse arquivo: ele nao aparece no `git status`,
     o `git add -A` nao o pega, e o `git pull` continua funcionando com o
     banco vivo intacto no lugar. E a trava que resolve o caso normal;
  2. um gancho de pre-commit que recusa um commit cujo `data/db.sqlite`
     em fila tenha login, senha, e-mail ou telefone. E a trava para
     quando a primeira for desfeita -- `git add -f`, um clone novo, uma
     ferramenta grafica que mexe no index.

Nenhuma das duas apaga nada, e nenhuma depende de o servidor estar de pe.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Any

BANCO_NO_GIT = "data/db.sqlite"

# Os campos que transformam "uma lista de nomes" em "dados de pessoas".
# `password_hash` e `login` sao os que dao acesso; `email` e `phone` sao
# dado pessoal de gente de uma universidade publica, e nao viram publicos
# por descuido de ferramenta.
CAMPOS_DE_SEGREDO = ("login", "password_hash", "email", "phone")

GANCHO = """#!/bin/sh
# Instalado pelo LAPE -- veja scripts/lape/banco_protegido.py
#
# Recusa um commit que leve o banco do laboratorio com dados de pessoas
# dentro. Se nao houver Python nesta maquina o commit SEGUE, com recado:
# uma trava que impede de comitar qualquer coisa por falta de Python
# seria pior do que o problema que ela evita, e a trava principal
# (skip-worktree) nao depende deste gancho.
raiz="$(git rev-parse --show-toplevel)"
for py in python3 python py; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" "$raiz/scripts/lape_agent.py" conferir-commit
  fi
done
echo "  . python nao encontrado -- commit seguiu sem conferir o banco" >&2
exit 0
"""


def _git(raiz: Path, *args: str, silencioso: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(raiz), text=True,
                          capture_output=silencioso)


def esta_num_repositorio(raiz: Path) -> bool:
    return _git(raiz, "rev-parse", "--git-dir").returncode == 0


def _dir_do_git(raiz: Path) -> Path | None:
    saida = _git(raiz, "rev-parse", "--absolute-git-dir")
    if saida.returncode != 0:
        return None
    return Path(saida.stdout.strip())


def esta_versionado(raiz: Path) -> bool:
    return _git(raiz, "ls-files", "--error-unmatch",
                BANCO_NO_GIT).returncode == 0


def tem_skip_worktree(raiz: Path) -> bool:
    """`git ls-files -v` marca skip-worktree com "S" MAIUSCULO na coluna 1.

    Nao com minuscula: minuscula em `ls-files -v` e assume-unchanged, que
    e outra coisa. Procurar minuscula respondia "nao esta ligado" com a
    trava ligada -- e um status que mente faz a pessoa "consertar" o que
    esta funcionando. "H" e o arquivo normal.
    """
    saida = _git(raiz, "ls-files", "-v", BANCO_NO_GIT)
    return saida.stdout.startswith("S ")


def tem_dados_de_pessoas(caminho: Path) -> list[str]:
    """Quais campos de segredo este arquivo sqlite tem preenchidos.

    Le em modo somente-leitura e por URI: abrir um sqlite para escrita
    cria o arquivo se ele nao existir, e aqui isso plantaria um banco
    vazio no lugar de responder a pergunta.
    """
    if not caminho.exists() or caminho.stat().st_size == 0:
        return []
    achados: list[str] = []
    try:
        con = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    except sqlite3.Error:
        return []
    try:
        tabelas = {linha[0] for linha in con.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "members" not in tabelas:
            return []
        colunas = {linha[1] for linha in con.execute("PRAGMA table_info(members)")}
        for campo in CAMPOS_DE_SEGREDO:
            if campo not in colunas:
                continue
            n = con.execute(
                f"SELECT COUNT(*) FROM members"
                f" WHERE {campo} IS NOT NULL AND {campo} != ''").fetchone()[0]
            if n:
                achados.append(f"{campo}: {n}")
    except sqlite3.DatabaseError:
        # Arquivo que nao e sqlite valido nao e um banco com segredo --
        # e outro problema, e nao e deste modulo.
        return []
    finally:
        con.close()
    return achados


def conferir_o_que_vai_no_commit(raiz: Path) -> tuple[int, str]:
    """O gancho de pre-commit: 0 deixa passar, 1 recusa.

    Confere o conteudo EM FILA (`:caminho`), e nao o arquivo em disco:
    sao coisas diferentes quando alguem faz `git add` e depois mexe no
    arquivo, e o que vai para o historico e o que esta em fila.
    """
    em_fila = _git(raiz, "diff", "--cached", "--name-only")
    if em_fila.returncode != 0:
        return 0, ""
    if BANCO_NO_GIT not in em_fila.stdout.split():
        return 0, ""

    bruto = subprocess.run(["git", "show", f":{BANCO_NO_GIT}"], cwd=str(raiz),
                           capture_output=True)
    if bruto.returncode != 0:
        return 0, ""
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "em_fila.sqlite"
        copia.write_bytes(bruto.stdout)
        achados = tem_dados_de_pessoas(copia)
    if not achados:
        return 0, ""
    return 1, (
        "\n  RECUSADO: este commit leva o banco do laboratorio com dados\n"
        "  de pessoas dentro -- " + ", ".join(achados) + ".\n\n"
        "  O repositorio e publico, e commit apagado continua no\n"
        "  historico. Tire o banco da fila:\n\n"
        "      git restore --staged data/db.sqlite\n\n"
        "  Para nunca mais precisar disto:\n\n"
        "      python scripts/lape_agent.py proteger\n\n"
        "  Se for de proposito -- um banco de exemplo, sem ninguem\n"
        "  dentro -- o caminho e `git commit --no-verify`.\n")


def proteger(raiz: Path) -> dict[str, Any]:
    """Liga as duas travas. Rodar duas vezes nao faz nada diferente."""
    feito: dict[str, Any] = {"skip_worktree": None, "gancho": None,
                             "porque": None}
    if not esta_num_repositorio(raiz):
        feito["porque"] = "esta pasta nao e um repositorio git"
        return feito

    if esta_versionado(raiz):
        if tem_skip_worktree(raiz):
            feito["skip_worktree"] = "ja estava"
        else:
            r = _git(raiz, "update-index", "--skip-worktree", BANCO_NO_GIT)
            feito["skip_worktree"] = "ligado" if r.returncode == 0 else "falhou"
    else:
        feito["skip_worktree"] = "nao versionado"

    git_dir = _dir_do_git(raiz)
    if git_dir is None:
        feito["gancho"] = "falhou"
        return feito
    hooks = git_dir / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    alvo = hooks / "pre-commit"
    if alvo.exists() and alvo.read_text(encoding="utf-8") == GANCHO:
        feito["gancho"] = "ja estava"
        return feito
    if alvo.exists() and "banco_protegido" not in alvo.read_text(
            encoding="utf-8", errors="replace"):
        # Gancho de outra pessoa nao se sobrescreve em silencio.
        feito["gancho"] = "ja existe outro pre-commit -- nao foi trocado"
        return feito
    alvo.write_text(GANCHO, encoding="utf-8")
    os.chmod(alvo, 0o755)
    feito["gancho"] = "instalado"
    return feito


def situacao(raiz: Path) -> dict[str, Any]:
    """Como estao as travas, e o que o banco vivo tem dentro."""
    git_dir = _dir_do_git(raiz)
    gancho = git_dir / "hooks" / "pre-commit" if git_dir else None
    return {
        "repositorio": esta_num_repositorio(raiz),
        "versionado": esta_versionado(raiz) if esta_num_repositorio(raiz) else False,
        "skip_worktree": tem_skip_worktree(raiz) if esta_num_repositorio(raiz) else False,
        "gancho": bool(gancho and gancho.exists()
                       and "banco_protegido" in gancho.read_text(
                           encoding="utf-8", errors="replace")),
        "segredo_no_banco_vivo": tem_dados_de_pessoas(raiz / BANCO_NO_GIT),
    }
