"""Atualizar o sistema pelo botão da tela -- sem abrir o CMD.

Chama o MESMO `publicar.ps1` que o "Subir LAPE.bat" chama, sem nenhuma
flag: o script já sabe sozinho qual endereço está valendo (fixo,
permanente ou sorteado) e mantém o mesmo, e já testa a versão nova numa
porta separada antes de trocar o serviço (ver a melhoria em
`deploy/publicar.ps1`). O botão não pula nem repete nenhuma dessas
etapas -- só dispara o mesmo script que sempre existiu.

O processo que atende este clique é o MESMO que o `publicar.ps1` vai
derrubar quando promover a versão nova. Por isso a chamada aqui nunca
pode ESPERAR o script terminar: soltar um processo solto (destacado, sem
processo pai) e responder na hora é o que garante que a resposta HTTP
sai do forno antes de o próprio worker morrer no meio da troca.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from . import config

# Só existem de verdade no Windows; o valor não importa fora dele porque
# `_disparar` só roda depois do guard de `_e_windows()`.
_DETACHED_PROCESS = 0x00000008
_CREATE_NEW_PROCESS_GROUP = 0x00000200


def _e_windows() -> bool:
    return sys.platform.startswith("win")


def _publicar_ps1() -> Path:
    return Path(config.ROOT) / "deploy" / "publicar.ps1"


def _disparar(comando: list[str]) -> None:
    """Solta o processo e não espera -- ver o porquê no docstring do módulo."""
    subprocess.Popen(
        comando, cwd=str(config.ROOT),
        creationflags=_DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def disparar() -> dict[str, Any]:
    """Começa a atualização e volta na hora, sem esperar ela terminar.

    Sem flag nenhuma: o `publicar.ps1` decide sozinho o modo (fixo,
    permanente, sorteado) pelo que já está gravado, do mesmo jeito que o
    `.bat` decide -- um segundo jeito de escolher o modo aqui divergiria
    do `.bat` na primeira vez que alguém mexesse só num dos dois.
    """
    if not _e_windows():
        return {"ok": False,
                "recado": "Esta máquina não é Windows. Rode "
                          ".\\deploy\\publicar.ps1 no PowerShell."}
    script = _publicar_ps1()
    if not script.exists():
        return {"ok": False,
                "recado": f"não encontrei {script} — o sistema está na pasta certa?"}
    try:
        _disparar(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                   "-File", str(script)])
    except OSError as erro:
        return {"ok": False, "recado": f"não consegui iniciar: {erro}"}
    return {"ok": True, "recado": None}
