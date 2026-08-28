"""Que codigo esta rodando agora, e se ha coisa nova esperando.

Existe porque "nao atualizou" e uma frase sem resposta possivel: o site
antigo e o novo sao identicos na primeira olhada. Quem esta no
computador do laboratorio precisa conseguir ver, na propria tela e sem
abrir terminal, qual versao esta no ar -- e o script de publicacao
precisa dizer quantas mudancas estao esperando do outro lado.

Tudo aqui degrada em silencio: sem git, sem rede ou fora de um
repositorio, a resposta e "desconhecida", nunca um erro.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from . import config

# O processo e reiniciado a cada publicacao, entao a versao nao muda
# dentro da vida dele -- ler o git a cada carregamento de pagina seria
# um processo novo por visita, sem nada a ganhar.
_CACHE: dict[str, Any] | None = None

TEMPO_LIMITE = 5


def _git(raiz: Path, *args: str) -> str | None:
    """Roda um comando git e devolve a saida, ou None se nao deu."""
    try:
        pronto = subprocess.run(
            ("git", "-C", str(raiz)) + args,
            capture_output=True, text=True, timeout=TEMPO_LIMITE)
    except (OSError, subprocess.SubprocessError):
        return None
    if pronto.returncode != 0:
        return None
    saida = pronto.stdout.strip()
    return saida or None


def atual(raiz: Path | None = None, usar_cache: bool = True) -> dict[str, Any]:
    """O commit no disco: identificacao, data, assunto e ramo.

    `atrasada` conta quantas mudancas ja existem no servidor e ainda nao
    chegaram aqui. Vem do ramo que este acompanha, como ele esta gravado
    no disco: nao vai a rede, entao so conta o que um `git fetch`
    anterior ja trouxe. Sem essa referencia, fica None -- que quer dizer
    "nao sei", e nao "esta em dia".
    """
    global _CACHE
    if usar_cache and raiz is None and _CACHE is not None:
        return _CACHE

    base = Path(raiz) if raiz is not None else config.ROOT
    dados: dict[str, Any] = {
        "commit": None, "data": None, "assunto": None,
        "ramo": None, "atrasada": None, "suja": None,
    }
    if (base / ".git").exists():
        dados["commit"] = _git(base, "rev-parse", "--short", "HEAD")
        dados["data"] = _git(base, "log", "-1", "--format=%cs")
        dados["assunto"] = _git(base, "log", "-1", "--format=%s")
        dados["ramo"] = _git(base, "rev-parse", "--abbrev-ref", "HEAD")
        # O ramo de trabalho pode acompanhar outro ramo do servidor, ou
        # nenhum. Perguntar sempre por origin/<ramo> devolvia "nao sei" a
        # quem so estava fora do main.
        alvo = _git(base, "rev-parse", "--abbrev-ref",
                    "--symbolic-full-name", "@{upstream}") or "origin/main"
        atras = _git(base, "rev-list", "--count", f"HEAD..{alvo}")
        dados["atrasada"] = int(atras) if atras and atras.isdigit() else None
        # `data/` fica de fora: ali mora o banco vivo, que muda a cada
        # cadastro. Contá-lo como alteracao local diria "voce mexeu no
        # codigo" para quem so usou o sistema.
        sujo = _git(base, "status", "--porcelain", "--", ".", ":(exclude)data")
        dados["suja"] = bool(sujo)

    if usar_cache and raiz is None:
        _CACHE = dados
    return dados


def resumo(dados: dict[str, Any] | None = None) -> str:
    """Uma linha para o rodape da tela e para o console."""
    d = dados if dados is not None else atual()
    if not d.get("commit"):
        return "versão desconhecida"
    partes = [f"versão {d['commit']}"]
    if d.get("data"):
        partes.append(d["data"])
    if d.get("ramo") and d["ramo"] not in ("main", "master"):
        partes.append(f"ramo {d['ramo']}")
    return " · ".join(partes)
