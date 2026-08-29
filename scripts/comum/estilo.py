"""Estilo visual das figuras do projeto.

Reproduz o padrão das figuras de referência enviadas pelo orientador: título
em negrito sobre cada painel, moldura fechada nos quatro lados, linhas de
grade discretas ao fundo, legenda em caixa e rótulo direto sobre os valores.

A paleta foi escolhida pelo trabalho que a variável cumpre e conferida com
scripts/validate_palette.js da habilidade de visualização de dados. Todas as
sequências abaixo passam nos seis testes em modo claro: faixa de luminosidade,
piso de croma, separação sob daltonismo, piso de visão normal e contraste
contra a superfície.
"""
from __future__ import annotations

from pathlib import Path

from matplotlib.ticker import FuncFormatter, ScalarFormatter

# Sequência categórica em ordem fixa, nunca ciclada.
PALETA = ["#2A9D8F", "#E76F51", "#2D6DA4", "#A8842A", "#8E5AA5", "#5B8C3A"]
TEAL, CORAL, AZUL, OCRE, ROXO, VERDE = PALETA
# Par de barras do gráfico de referência.
BARRA_A, BARRA_B = "#3E7CB1", "#E63946"
# Tintas de texto e de estrutura: o texto nunca veste a cor da série.
TINTA, TINTA_FRACA = "#1F1F1F", "#5A5A5A"
GRADE, MOLDURA, FAIXA = "#D4D4D2", "#3A3A3A", "#EFEFED"

DPI = 300
_VIRGULA = FuncFormatter(
    lambda v, _: f"{v:g}".replace(".", ",").replace("-", "−"))


def aplicar(ax, *, grade: str = "ambos") -> None:
    """Moldura fechada, grade discreta atrás dos dados e tinta de texto.

    grade aceita ambos, x, y ou nenhum.
    """
    ax.set_facecolor("white")
    for lado in ("top", "right", "bottom", "left"):
        ax.spines[lado].set_visible(True)
        ax.spines[lado].set_color(MOLDURA)
        ax.spines[lado].set_linewidth(0.9)
    if grade == "nenhum":
        ax.grid(False)
    else:
        eixo = {"ambos": "both", "x": "x", "y": "y"}[grade]
        ax.grid(True, axis=eixo, color=GRADE, linewidth=0.7,
                linestyle=(0, (1, 3)), zorder=0)
        ax.set_axisbelow(True)
    ax.tick_params(colors=TINTA_FRACA, labelsize=8.2, width=0.9, length=3)


def titulo(ax, texto: str, *, tamanho: float = 10.0, centro: bool = True):
    return ax.set_title(texto, fontsize=tamanho, fontweight="bold",
                        color=TINTA, loc="center" if centro else "left",
                        pad=9)


def legenda(ax, **kw):
    """Legenda em caixa, como nas figuras de referência."""
    padrao = dict(frameon=True, fontsize=8.0, labelcolor=TINTA_FRACA,
                  handlelength=1.6, borderpad=0.5, labelspacing=0.4,
                  edgecolor=GRADE, facecolor="white", framealpha=0.95)
    padrao.update(kw)
    leg = ax.legend(**padrao)
    if leg is not None:
        leg.get_frame().set_linewidth(0.8)
    return leg


def virgula(fig) -> None:
    """Vírgula decimal em todo eixo numérico da figura."""
    for ax in fig.axes:
        for eixo in (ax.xaxis, ax.yaxis):
            if isinstance(eixo.get_major_formatter(), ScalarFormatter):
                eixo.set_major_formatter(_VIRGULA)


def salvar(fig, destino: Path, nome: str) -> Path:
    import matplotlib.pyplot as plt
    virgula(fig)
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / nome
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {nome}")
    return caminho


def vg(v: float, casas: int = 1) -> str:
    return f"{v:.{casas}f}".replace(".", ",").replace("-", "−")


def sg(v: float, casas: int = 1) -> str:
    if abs(v) < 0.5 * 10 ** -casas:
        return f"{0.0:.{casas}f}".replace(".", ",")
    return f"{v:+.{casas}f}".replace(".", ",").replace("-", "−")
