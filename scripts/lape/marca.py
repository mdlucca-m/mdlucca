"""A marca do laboratorio: o arquivo de logotipo, quando existe.

Sem arquivo, as telas ficam com as duas letras que sempre estiveram la
("LP") -- nada quebra, nada fica vazio. Com arquivo, ele aparece em todas
elas: painel, panorama, mural, aplicativo, entrada e convite.

A imagem viaja EMBUTIDA, como data: URI, e nao como um endereco a buscar.
E o mesmo motivo pelo qual o tema, os icones e os graficos ja viajam assim:
o instantaneo que o professor manda por e-mail, o mural que roda numa TV
sem rede e a pagina publicada em docs/ precisam abrir sozinhos. Um logotipo
que fosse um <img src="/logo.png"> sumiria dos tres.
"""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any

from . import config

# Ordem de procura. SVG primeiro: e o unico que nao perde nitidez no mural,
# que roda numa tela grande, e costuma ser o menor arquivo dos cinco.
NOMES = ("logo.svg", "logo.png", "logo.webp", "logo.jpg", "logo.jpeg")

# Teto de tamanho. O arquivo entra em CADA pagina servida e em cada
# instantaneo gravado; um logotipo de 4 MB somaria 5,3 MB de base64 a todo
# arquivo que alguem manda por e-mail. Recusar e dizer por que e melhor do
# que engordar tudo em silencio.
LIMITE_BYTES = 512 * 1024

TIPOS = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp",
         ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}

_cache: dict[str, Any] = {}


def caminho() -> Path | None:
    """Onde esta o logotipo, se estiver em algum lugar."""
    escolhido = getattr(config, "LOGO_PATH", "")
    if escolhido:
        alvo = Path(escolhido)
        return alvo if alvo.is_file() else None
    for nome in NOMES:
        alvo = config.DATA_DIR / nome
        if alvo.is_file():
            return alvo
    return None


def logo() -> dict[str, Any] | None:
    """O logotipo pronto para embutir, ou None.

    Guarda em memoria pelo par (caminho, mtime): as telas pedem isto a cada
    requisicao, e reler e recodificar meio megabyte a cada visita seria
    trabalho repetido para um arquivo que muda uma vez por ano.
    """
    alvo = caminho()
    if alvo is None:
        return None
    try:
        info = alvo.stat()
    except OSError:
        return None
    chave = f"{alvo}|{info.st_mtime_ns}|{info.st_size}"
    if _cache.get("chave") == chave:
        return _cache.get("valor")

    valor: dict[str, Any] | None = None
    if info.st_size > LIMITE_BYTES:
        valor = {"erro": f"o arquivo tem {info.st_size // 1024} kB e o limite e"
                         f" {LIMITE_BYTES // 1024} kB -- ele entra embutido em cada"
                         f" pagina e em cada instantaneo",
                 "arquivo": str(alvo)}
    else:
        try:
            bruto = alvo.read_bytes()
        except OSError as erro:
            valor = {"erro": str(erro), "arquivo": str(alvo)}
        else:
            tipo = TIPOS.get(alvo.suffix.lower()) or \
                mimetypes.guess_type(alvo.name)[0] or "image/png"
            valor = {
                "src": "data:" + tipo + ";base64,"
                       + base64.b64encode(bruto).decode("ascii"),
                "arquivo": str(alvo),
                "bytes": info.st_size,
                "tipo": tipo,
            }
    _cache["chave"], _cache["valor"] = chave, valor
    return valor


def fonte() -> str | None:
    """So o data: URI, que e o que as telas precisam. None se nao houver."""
    achado = logo()
    return achado.get("src") if achado and achado.get("src") else None


def marcador(alt: str = "") -> str:
    """O que entra no lugar de `__LOGO__` nos modelos HTML.

    Sem logotipo, devolve as duas letras -- e nao um <img> quebrado nem um
    espaco vazio onde havia uma marca.
    """
    src = fonte()
    if not src:
        return "LP"
    rotulo = (alt or config.LAB_NAME).replace('"', "&quot;")
    return f'<img class="logo-img" src="{src}" alt="{rotulo}">'


def situacao() -> dict[str, Any]:
    """Para a tela poder dizer onde por o arquivo, e o que houve com ele."""
    achado = logo()
    return {
        "tem": bool(achado and achado.get("src")),
        "arquivo": (achado or {}).get("arquivo"),
        "erro": (achado or {}).get("erro"),
        "onde": str(config.DATA_DIR / "logo.png"),
        "aceitos": list(NOMES),
        "limite_kb": LIMITE_BYTES // 1024,
    }
