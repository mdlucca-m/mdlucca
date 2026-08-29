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
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comum"))
import estilo as E  # noqa: E402
from dados import PARSONS  # noqa: E402

AZUL, TIJOLO, VERDE = "#3A6EA5", "#A63A2B", "#4E8F3A"
CINZA, CINZA_CLARO, FAIXA = "#3A3A3A", "#8C8C8C", "#EFEFEF"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comum"))
from grafico import virgula  # noqa: E402

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
    amostra, na ausência de normas de escore T para handebol de elite. A
    figura existe para tornar esse problema de método visível.
    """
    ordem = sorted(NORMATIVO, key=lambda k: -NORMATIVO[k])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.4 / 2.54, 7.6 / 2.54),
                                 dpi=E.DPI,
                                 gridspec_kw={"width_ratios": [1.3, 1]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        E.aplicar(ax, grade="x")

    ys = list(range(len(ordem)))[::-1]
    altura = 0.36
    norm = [NORMATIVO[p] for p in ordem]
    nosso = [PARSONS[p][0] for p in ordem]
    a1.barh([y + altura / 2 for y in ys], norm, height=altura, color=E.AZUL,
            label="Normativa (Parsons-Smith, 2017)", zorder=3)
    a1.barh([y - altura / 2 for y in ys], nosso, height=altura, color=E.TEAL,
            label="Esta amostra (padronizada internamente)", zorder=3)
    for y, v in zip(ys, norm):
        a1.text(v + 1.4, y + altura / 2, E.vg(v) + "%", va="center",
                fontsize=7.2, color=E.TINTA)
    for y, v in zip(ys, nosso):
        a1.text(v + 1.4, y - altura / 2, E.vg(v) + "%", va="center",
                fontsize=7.2, color=E.TINTA)
    a1.set_yticks(ys)
    a1.set_yticklabels(ordem, fontsize=8.4)
    a1.set_xlim(0, 72)
    a1.set_xlabel("Observações no perfil (%)", fontsize=8.8, color=E.TINTA)
    E.titulo(a1, "A. Prevalência de cada perfil", tamanho=9.4)
    E.legenda(a1, loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=1,
              fontsize=7.4)

    dif = [PARSONS[p][0] - NORMATIVO[p] for p in ordem]
    cores = [E.TEAL if d > 0 else E.CORAL for d in dif]
    a2.barh(ys, dif, height=0.55, color=cores, zorder=3)
    for y, d in zip(ys, dif):
        a2.text(d + (1.8 if d > 0 else -1.8), y, E.sg(d) + " p.p.",
                va="center", ha="left" if d > 0 else "right", fontsize=7.2,
                color=E.TINTA)
    a2.axvline(0, color=E.TINTA, linewidth=1.0, zorder=4)
    a2.set_yticks(ys)
    a2.set_yticklabels([])
    a2.set_xlim(-38, 62)
    a2.set_xlabel("Diferença em relação à norma (p.p.)", fontsize=8.8,
                  color=E.TINTA)
    E.titulo(a2, "B. Efeito da padronização interna", tamanho=9.4)
    E.legenda(a2, handles=[
        Line2D([], [], color=E.TEAL, linewidth=6, label="Acima da norma"),
        Line2D([], [], color=E.CORAL, linewidth=6, label="Abaixo da norma")],
        loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=1, fontsize=7.4)

    fig.tight_layout(w_pad=2.2)
    return E.salvar(fig, destino, "fig_prevalencia.png")


def gerar_todas(destino: Path) -> list[Path]:
    print("figuras do plano:")
    return [figura_prevalencia(destino)]


if __name__ == "__main__":
    gerar_todas(Path(sys.argv[1] if len(sys.argv) > 1 else "data/figplano"))
