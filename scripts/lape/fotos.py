"""A foto de perfil de um integrante: mesma receita da marca do laboratorio.

A imagem trafega como data: URI, direto na coluna `members.photo_url`, e
nao como um arquivo em disco -- e o mesmo raciocinio de `marca.py`: o
integrante mexe no proprio perfil pelo navegador, sem terminal, e a foto
ja precisa viajar embutida para aparecer no mural (que roda numa TV sem
rede) e no cartao de chegada, que ja le `photo_url` hoje.

O teto de tamanho e bem menor que o da marca: aqui e uma foto POR PESSOA,
nao uma so para o laboratorio inteiro, e o cadastro tem gente demais para
cada uma pesar 512 kB. A tela redimensiona a imagem antes de mandar (ver
o `<canvas>` em app.html), entao o teto aqui e so a rede de seguranca --
nunca o caminho esperado de chegar perto dele.
"""
from __future__ import annotations

import base64
import binascii

from .marca import Recusado as _RecusadoMarca
from .marca import _tipo_real as _tipo_real_marca

# 150 kB ja e generoso para uma foto redimensionada no navegador (o
# widget em app.html manda algo em torno de 15-40 kB); o teto existe para
# recusar um upload que bypassou o redimensionamento do lado do
# navegador, nao para ser alcancado no uso normal.
LIMITE_BYTES = 150 * 1024


class Recusado(ValueError):
    """O arquivo nao serve, e a mensagem diz por que."""


def _tipo_real(bruto: bytes) -> str:
    """Reaproveita a deteccao por assinatura de bytes de `marca.py`.

    SVG fica de fora aqui: e vetorial, serve bem a um logotipo, mas nao a
    uma foto de rosto -- e aceitar SVG abriria a porta para um arquivo
    com <script> embutido sendo tratado como imagem de perfil.
    """
    try:
        _extensao, tipo = _tipo_real_marca(bruto)
    except _RecusadoMarca as erro:
        raise Recusado(str(erro)) from None
    if tipo == "image/svg+xml":
        raise Recusado("SVG não serve como foto de perfil: use PNG, WEBP ou JPG.")
    return tipo


def gravar(data_uri: str) -> str:
    """Valida a foto enviada pela tela e devolve o data: URI pronto para
    gravar em `members.photo_url`. Levanta `Recusado` com o motivo quando
    o arquivo nao serve."""
    texto = (data_uri or "").strip()
    if "," in texto and texto.lower().startswith("data:"):
        texto = texto.split(",", 1)[1]
    if not texto:
        raise Recusado("Nenhuma foto veio junto.")
    try:
        bruto = base64.b64decode(texto, validate=True)
    except (binascii.Error, ValueError):
        raise Recusado("O arquivo chegou corrompido no caminho.") from None
    if not bruto:
        raise Recusado("O arquivo está vazio.")
    if len(bruto) > LIMITE_BYTES:
        raise Recusado(f"A foto tem {len(bruto) // 1024} kB e o limite é"
                        f" {LIMITE_BYTES // 1024} kB.")
    tipo = _tipo_real(bruto)
    return f"data:{tipo};base64,{base64.b64encode(bruto).decode('ascii')}"
