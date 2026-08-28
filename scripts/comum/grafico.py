"""Utilidades de formatação comuns às figuras do projeto."""
from __future__ import annotations

from matplotlib.ticker import FuncFormatter, ScalarFormatter

_VIRGULA = FuncFormatter(
    lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))


def virgula(fig) -> None:
    """Troca o ponto decimal pela vírgula em todo eixo numérico da figura.

    Eixos categóricos usam FixedFormatter e ficam intactos, de modo que os
    rótulos de texto não são afetados.
    """
    for ax in fig.axes:
        for eixo in (ax.xaxis, ax.yaxis):
            if isinstance(eixo.get_major_formatter(), ScalarFormatter):
                eixo.set_major_formatter(_VIRGULA)
