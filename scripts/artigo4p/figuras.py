#!/usr/bin/env python3
"""Figuras do artigo, em painéis compostos e múltiplos gráficos em grade.

Fundo branco, sem linhas de grade, 300 dpi. Cada série carrega marcador
próprio além da cor, o que preserva a leitura em impressão monocromática.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analise import (ACUMULO, BASELINE, DIARIO, HIIT, JOGO, ORDEM,
                     sensibilidade)

AZUL, TIJOLO, VERDE = "#3A6EA5", "#A63A2B", "#4E8F3A"
CINZA, CINZA_CLARO, FAIXA = "#3A3A3A", "#8C8C8C", "#EFEFEF"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comum"))
from grafico import virgula  # noqa: E402

DPI = 300
DIAS = list(range(1, 8))


def limpar(ax, *, y=True):
    ax.set_facecolor("white")
    ax.grid(False)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(CINZA)
        ax.spines[lado].set_linewidth(0.7)
    if not y:
        ax.spines["left"].set_visible(False)
    ax.tick_params(colors=CINZA, labelsize=7.5, width=0.7, length=2.5)


def salvar(fig, destino: Path, nome: str) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / nome
    virgula(fig)
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {nome}")
    return caminho


def marcar_condicoes(ax, topo: float):
    """Faixas de fundo que separam repouso, HIIT, jogo e acúmulo."""
    for dia in HIIT:
        ax.axvspan(dia - 0.42, dia + 0.42, color=FAIXA, zorder=0)


# ── Figura 1 · múltiplos gráficos em grade ─────────────────────────────────
def figura_grade(destino: Path) -> Path:
    fig, eixos = plt.subplots(2, 4, figsize=(17.5 / 2.54, 9.6 / 2.54), dpi=DPI,
                              sharex=True)
    fig.patch.set_facecolor("white")
    planos = eixos.ravel()

    for i, dim in enumerate(ORDEM):
        ax = planos[i]
        limpar(ax)
        y = DIARIO[dim]
        topo = max(y) * 1.28
        marcar_condicoes(ax, topo)
        ax.plot(DIAS, y, color=AZUL, marker="o", markersize=4, linewidth=1.5,
                zorder=3, markeredgecolor="white", markeredgewidth=0.6)
        # anotação do pico e do vale, como nas referências
        i_max, i_min = y.index(max(y)), y.index(min(y))
        for idx, cor, desloc in ((i_max, TIJOLO, 7), (i_min, VERDE, -11)):
            ax.plot(DIAS[idx], y[idx], "o", color=cor, markersize=5, zorder=4,
                    markeredgecolor="white", markeredgewidth=0.6)
            ax.annotate(f"{y[idx]:.1f}".replace(".", ","),
                        (DIAS[idx], y[idx]), textcoords="offset points",
                        xytext=(0, desloc), ha="center", fontsize=7,
                        color=cor, fontweight="bold")
        ax.set_title(dim, fontsize=8.5, color=CINZA, loc="left", pad=4)
        ax.set_ylim(0, topo)
        ax.set_xlim(0.5, 7.5)
        ax.set_xticks(DIAS)

    ultimo = planos[len(ORDEM)]
    ultimo.axis("off")
    ultimo.legend(handles=[
        Patch(facecolor=FAIXA, label="dias de HIIT comparados (2 e 4)"),
        Line2D([], [], color=AZUL, marker="o", linestyle="-",
               label="média diária"),
        Line2D([], [], color=TIJOLO, marker="o", linestyle="",
               label="maior valor da semana"),
        Line2D([], [], color=VERDE, marker="o", linestyle="",
               label="menor valor da semana")],
        frameon=False, fontsize=7.2, loc="center", labelcolor=CINZA)

    for ax in planos[4:]:
        ax.set_xlabel("Dia do microciclo", fontsize=8, color=CINZA)
    fig.tight_layout(h_pad=1.1, w_pad=1.6)
    return salvar(fig, destino, "fig1_grade.png")


# ── Figura 2 · painel composto de três quadros ─────────────────────────────
def figura_painel(destino: Path) -> Path:
    """Um só painel com os três quadros que sustentam a análise de
    sensibilidade: média por condição, especificidade e resposta aguda."""
    dados = {x["dimensao"]: x for x in sensibilidade()}
    fig, (a1, a2, a3) = plt.subplots(
        1, 3, figsize=(17.5 / 2.54, 6.6 / 2.54), dpi=DPI,
        gridspec_kw={"width_ratios": [1.05, 1.0, 1.0]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2, a3):
        limpar(ax)

    # A · média por condição
    chaves = ["PTH", "Vigor", "Fadiga"]
    rotulos = ["Repouso", "HIIT", "Jogo"]
    largura = 0.26
    cores = [CINZA_CLARO, TIJOLO, AZUL]
    for j, cond in enumerate(("baseline", "hiit", "jogo")):
        xs = [i + (j - 1) * largura for i in range(len(chaves))]
        vs = [dados[d][cond] for d in chaves]
        a1.bar(xs, vs, width=largura, color=cores[j], label=rotulos[j], zorder=3)
        for x, v in zip(xs, vs):
            a1.text(x, v + 0.15, f"{v:.2f}".replace(".", ","), ha="center",
                    va="bottom", fontsize=6, color=cores[j], rotation=90)
    a1.set_xticks(range(len(chaves)))
    a1.set_xticklabels(chaves, fontsize=7.5)
    a1.set_ylabel("Escore médio", fontsize=7.5, color=CINZA)
    a1.set_ylim(0, 10.4)
    a1.set_title("A. Média por condição", fontsize=8.5, color=CINZA,
                 loc="left", pad=5)
    a1.legend(frameon=False, fontsize=6.5, labelcolor=CINZA, loc="upper right",
              handlelength=1.1, borderpad=0.1, labelspacing=0.25)

    # B · especificidade ao tipo de estímulo
    ordenado = sorted(sensibilidade(), key=lambda x: -x["especificidade"])
    nomes = [x["dimensao"] for x in ordenado][::-1]
    vals = [x["especificidade"] for x in ordenado][::-1]
    ys = list(range(len(nomes)))
    a2.barh(ys, vals, height=0.55, color=VERDE, zorder=3)
    for i, v in zip(ys, vals):
        a2.text(v + 2.5, i, f"{v:.0f}%", va="center", fontsize=6.5, color=VERDE)
    a2.set_yticks(ys)
    a2.set_yticklabels(nomes, fontsize=7.5)
    a2.set_xlabel("Separação HIIT e jogo (% do repouso)", fontsize=7.5,
                  color=CINZA)
    a2.set_xlim(0, 128)
    a2.set_title("B. Especificidade ao estímulo", fontsize=8.5, color=CINZA,
                 loc="left", pad=5)

    # C · resposta aguda dentro da sessão
    agudo = sorted(sensibilidade(), key=lambda x: -abs(x["dz_agudo"]))
    nomes = [x["dimensao"] for x in agudo][::-1]
    for i, x in enumerate(agudo[::-1]):
        cor = TIJOLO if x["sobrevive"] else CINZA_CLARO
        a3.plot([0, x["dz_agudo"]], [i, i], color=cor, linewidth=1.3, zorder=2)
        a3.plot(x["dz_agudo"], i, "o", color=cor, markersize=4.5, zorder=3,
                markeredgecolor="white", markeredgewidth=0.6)
        desloc = 0.04 if x["dz_agudo"] >= 0 else -0.04
        a3.text(x["dz_agudo"] + desloc, i,
                f'{x["dz_agudo"]:+.2f}'.replace(".", ","), fontsize=6.5,
                color=cor, va="center",
                ha="left" if x["dz_agudo"] >= 0 else "right")
    a3.axvline(0, color=CINZA, linewidth=0.7, zorder=1)
    a3.set_yticks(range(len(nomes)))
    a3.set_yticklabels(nomes, fontsize=7.5)
    a3.set_xlabel("Resposta aguda (dz)", fontsize=7.5, color=CINZA)
    a3.set_xlim(-0.72, 0.78)
    a3.set_ylim(-0.6, len(nomes) + 0.15)
    a3.set_title("C. Resposta dentro da sessão", fontsize=8.5, color=CINZA,
                 loc="left", pad=5)
    a3.legend(handles=[
        Line2D([], [], color=TIJOLO, marker="o", linestyle="-",
               label="p significativo"),
        Line2D([], [], color=CINZA_CLARO, marker="o", linestyle="-",
               label="sem significância")],
        frameon=False, fontsize=6.5, loc="upper left", labelcolor=CINZA,
        handlelength=1.1, borderpad=0.1, labelspacing=0.25)

    fig.tight_layout(w_pad=1.8)
    return salvar(fig, destino, "fig2_painel.png")


def gerar_todas(destino: Path) -> list[Path]:
    print("figuras:")
    return [figura_grade(destino), figura_painel(destino)]


if __name__ == "__main__":
    gerar_todas(Path(sys.argv[1] if len(sys.argv) > 1 else "data/fig4p"))
