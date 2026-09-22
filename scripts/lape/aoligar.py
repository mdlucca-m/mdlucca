"""Subir sozinho quando o computador liga -- pela tela, e nao pelo .bat.

Isto ja existia: "Subir sozinho ao ligar.bat", ao lado do "Subir LAPE.bat".
O que faltava era o BOTAO. Quem usa o sistema abre a tela, nao a pasta --
e um arquivo que resolve um problema so serve a quem lembra que ele
existe. Pior: os dois .bat ficam lado a lado com nomes parecidos, e nada
na tela dizia qual dos dois esta valendo agora.

O que este modulo faz e so isto: perguntar ao Windows se o LAPE esta
agendado, e ligar ou desligar esse agendamento chamando o MESMO
`publicar.ps1` que o .bat chama. Nao ha um segundo jeito de agendar
escrito aqui -- se houvesse, ele divergiria do .bat na primeira vez que
alguem mexesse em um dos dois.

O Windows tem DOIS caminhos, e o publicar.ps1 usa os dois de proposito:
a tarefa agendada, que reinicia sozinha se cair e funciona na bateria, e
o atalho na pasta Inicializar, que e o plano B de quem nao e
administrador da maquina -- num computador de universidade, quase
ninguem e. Perguntar so pela tarefa diria "desligado" com o sistema
subindo sozinho pelo atalho, que e a pior resposta possivel: a pessoa
liga de novo e passa a ter dois.

Fora do Windows isto nao existe, e a resposta diz isso em vez de fingir.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import config

# O nome esta escrito no publicar.ps1, e as duas pontas precisam
# concordar: procurar por um nome diferente daquele que foi registrado e
# responder "desligado" para sempre.
NOME_DA_TAREFA = "LAPE - publicar"
NOME_DO_ATALHO = "LAPE - publicar.lnk"

# Quanto esperar pelo Windows. O `schtasks` responde em milissegundos; o
# `publicar.ps1 -AoLigar` registra a tarefa e sai. Trinta segundos e
# folga, e o teto existe para a tela nao ficar pendurada se algo travar.
ESPERA_S = 30


def _e_windows() -> bool:
    return sys.platform.startswith("win")


def _pasta_inicializar() -> Path | None:
    """A pasta Inicializar deste usuario, quando ha uma."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return (Path(appdata) / "Microsoft" / "Windows" / "Start Menu"
            / "Programs" / "Startup")


def _rodar(comando: list[str]) -> tuple[int, str]:
    """Roda e devolve (codigo, saida). Lista, e nunca shell=True.

    Nada aqui vem de quem clicou: o comando e fixo e os caminhos saem do
    proprio sistema de arquivos. Ainda assim a lista e a forma certa --
    com `shell=True`, um dia alguem acrescenta um parametro e a linha
    passa a ser interpretada pelo cmd.
    """
    try:
        feito = subprocess.run(comando, capture_output=True, text=True,
                               timeout=ESPERA_S)
    except FileNotFoundError:
        return 127, "programa não encontrado"
    except subprocess.TimeoutExpired:
        return 124, f"passou de {ESPERA_S} segundos sem responder"
    saida = (feito.stdout or "") + (feito.stderr or "")
    return feito.returncode, saida.strip()


def situacao() -> dict[str, Any]:
    """O LAPE sobe sozinho nesta maquina? E por qual dos dois caminhos?"""
    if not _e_windows():
        return {
            "windows": False, "ligado": False, "como": None,
            "aviso": "Subir sozinho ao ligar é coisa do Windows. Esta máquina "
                     "não é Windows, e por isso o botão não aparece.",
        }

    tarefa = False
    codigo, _ = _rodar(["schtasks", "/Query", "/TN", NOME_DA_TAREFA])
    tarefa = codigo == 0

    atalho = False
    pasta = _pasta_inicializar()
    if pasta is not None:
        atalho = (pasta / NOME_DO_ATALHO).exists()

    # Os DOIS contam. Ver so a tarefa diria "desligado" com o sistema
    # subindo pelo atalho -- e quem lesse isso ligaria de novo, ficando
    # com dois LAPE tentando subir na mesma porta.
    return {
        "windows": True,
        "ligado": tarefa or atalho,
        "como": "tarefa" if tarefa else ("atalho" if atalho else None),
        "tarefa": tarefa,
        "atalho": atalho,
        "aviso": None,
    }


def _publicar_ps1() -> Path:
    return Path(config.ROOT) / "deploy" / "publicar.ps1"


def definir(ligado: bool) -> dict[str, Any]:
    """Liga ou desliga, chamando o MESMO script que o .bat chama.

    Nao ha aqui um segundo jeito de agendar. Se houvesse, ele divergiria
    do .bat na primeira vez que alguem mexesse em um dos dois -- e o
    laboratorio passaria a ter duas verdades sobre o mesmo agendamento.
    """
    if not _e_windows():
        return dict(situacao(), ok=False,
                    recado="Esta máquina não é Windows.")
    script = _publicar_ps1()
    if not script.exists():
        return dict(situacao(), ok=False,
                    recado=f"não encontrei {script} — o sistema está na pasta certa?")
    codigo, saida = _rodar([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(script), "-AoLigar" if ligado else "-NaoAoLigar"])
    depois = situacao()
    if codigo != 0:
        return dict(depois, ok=False,
                    recado=f"o Windows recusou: {saida[:300]}" if saida
                           else "o Windows recusou, sem dizer por quê")
    # A CONFERENCIA depois de agendar, e nao a confianca no codigo de
    # saida: o publicar.ps1 cai no atalho quando a tarefa e negada, e sai
    # com zero nos dois casos. Sem reler, a tela diria "agendado" tendo
    # acontecido outra coisa.
    if depois["ligado"] != ligado:
        return dict(depois, ok=False,
                    recado="o comando rodou, mas o agendamento não mudou"
                           f" — o Windows respondeu: {saida[:200] or 'nada'}")
    return dict(depois, ok=True, recado=saida[:300] or None)
