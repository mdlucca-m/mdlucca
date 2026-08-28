#!/usr/bin/env python3
"""Figuras do plano editorial.

Fundo branco, sem linhas de grade, 300 dpi.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "artigo4p"))
from dados import PARSONS  # noqa: E402

AZUL, TIJOLO, VERDE = "#3A6EA5", "#A63A2B", "#4E8F3A"
CINZA, CINZA_CLARO, FAIXA = "#3A3A3A", "#8C8C8C", "#EFEFEF"
DPI = 300

# Parsons-Smith, Terry e Machin (2017), amostra A: probabilidades a priori de
# cada agrupamento, sobre escores T normativos.
NORMATIVO = {
    "Iceberg": 29.4,
    "Submerso": 25.5,
    "Barbatana tubarão": 17.3,
    "Superfície": 14.8,
    "Iceberg invertido": 10.3,
    "Everest invertido": 2.7,
}


def limpar(ax):
    ax.set_facecolor("white")
    ax.grid(False)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(CINZA)
        ax.spines[lado].set_linewidth(0.7)
    ax.tick_params(colors=CINZA, labelsize=7.5, width=0.7, length=2.5)


def vg(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


def figura_prevalencia(destino: Path) -> Path:
    """Compara a prevalência de cada perfil na amostra normativa e na nossa.

    A diferença não é achado clínico: ela decorre da padronização dentro da
    amostra, na ausência de normas de escore T para handebol de elite. A figura
    existe para tornar esse problema de método visível.
    """
    ordem = sorted(NORMATIVO, key=lambda k: -NORMATIVO[k])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.5 / 2.54, 7.0 / 2.54),
                                 dpi=DPI, gridspec_kw={"width_ratios": [1.25, 1]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        limpar(ax)

    ys = list(range(len(ordem)))[::-1]
    altura = 0.36
    norm = [NORMATIVO[p] for p in ordem]
    nosso = [PARSONS[p][0] for p in ordem]
    a1.barh([y + altura / 2 for y in ys], norm, height=altura, color=CINZA_CLARO,
            label="normativa (Parsons-Smith, 2017)", zorder=3)
    a1.barh([y - altura / 2 for y in ys], nosso, height=altura, color=AZUL,
            label="esta amostra (padronizada internamente)", zorder=3)
    for y, v in zip(ys, norm):
        a1.text(v + 1.2, y + altura / 2, f"{vg(v)}%", va="center", fontsize=6.6,
                color=CINZA_CLARO)
    for y, v in zip(ys, nosso):
        a1.text(v + 1.2, y - altura / 2, f"{vg(v)}%", va="center", fontsize=6.6,
                color=AZUL)
    a1.set_yticks(ys)
    a1.set_yticklabels(ordem, fontsize=7.5)
    a1.set_xlim(0, 68)
    a1.set_xlabel("Observações no perfil (%)", fontsize=7.5, color=CINZA)
    a1.set_title("A. Prevalência de cada perfil", fontsize=8.6, color=CINZA,
                 loc="left", pad=6)
    a1.legend(frameon=False, fontsize=6.8, labelcolor=CINZA, loc="lower right",
              handlelength=1.2, borderpad=0.1, labelspacing=0.3)

    dif = [PARSONS[p][0] - NORMATIVO[p] for p in ordem]
    cores = [VERDE if d > 0 else TIJOLO for d in dif]
    a2.barh(ys, dif, height=0.5, color=cores, zorder=3)
    for y, d in zip(ys, dif):
        a2.text(d + (1.4 if d > 0 else -1.4), y,
                f"{d:+.1f}".replace(".", ",").replace("-", "−") + " p.p.",
                va="center", ha="left" if d > 0 else "right", fontsize=6.6,
                color=VERDE if d > 0 else TIJOLO)
    a2.axvline(0, color=CINZA, linewidth=0.8, zorder=1)
    a2.set_yticks(ys)
    a2.set_yticklabels([])
    a2.set_xlim(-40, 62)
    a2.set_xlabel("Diferença em relação à norma (pontos percentuais)",
                  fontsize=7.5, color=CINZA)
    a2.set_title("B. Efeito da padronização interna", fontsize=8.6, color=CINZA,
                 loc="left", pad=6)
    a2.legend(handles=[Line2D([], [], color=VERDE, linewidth=5,
                              label="acima da norma"),
                       Line2D([], [], color=TIJOLO, linewidth=5,
                              label="abaixo da norma")],
              frameon=False, fontsize=6.8, labelcolor=CINZA, loc="lower right",
              handlelength=1.0, borderpad=0.1, labelspacing=0.3)

    fig.tight_layout(w_pad=2.0)
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / "fig_prevalencia.png"
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {caminho.name}")
    return caminho


def gerar_todas(destino: Path) -> list[Path]:
    print("figuras do plano:")
    return [figura_prevalencia(destino)]


if __name__ == "__main__":
    gerar_todas(Path(sys.argv[1] if len(sys.argv) > 1 else "data/figplano"))
