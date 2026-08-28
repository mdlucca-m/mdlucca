#!/usr/bin/env python3
"""Gráficos analíticos: comportamento diário de cada variável e migração dos
perfis de humor ao longo do microciclo.

Fundo branco, sem linhas de grade, 300 dpi. A direção do desvio é codificada
por cor e por posição em relação à linha de base, e não apenas por cor, o que
preserva a leitura em impressão monocromática.
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
from dados import (ACUMULO, AUMENTO_DESFAVORAVEL, BETA_HIIT, DIARIO, DIAS,
                   DIAS_HIIT, EFEITO_DIA, METRICAS_PERFIL, MUDANCA_CONFIAVEL,
                   ORDEM_GRADE, PARSONS, PERFIL_DIA, inclinacao, reta)

AZUL, TIJOLO, VERDE = "#3A6EA5", "#A63A2B", "#4E8F3A"
CINZA, CINZA_CLARO, FAIXA = "#3A3A3A", "#8C8C8C", "#EFEFEF"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comum"))
from grafico import virgula  # noqa: E402

DPI = 300


def vg(v: float, casas: int = 2) -> str:
    """Número com vírgula decimal e sinal de menos, não hífen."""
    return f"{v:.{casas}f}".replace(".", ",").replace("-", "−")


def sg(v: float, casas: int = 2) -> str:
    return f"{v:+.{casas}f}".replace(".", ",").replace("-", "−")


def limpar(ax, *, esquerda=True, baixo=True):
    ax.set_facecolor("white")
    ax.grid(False)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado, mostra in (("left", esquerda), ("bottom", baixo)):
        ax.spines[lado].set_visible(mostra)
        ax.spines[lado].set_color(CINZA)
        ax.spines[lado].set_linewidth(0.7)
    ax.tick_params(colors=CINZA, labelsize=7, width=0.7, length=2.5)


def salvar(fig, destino: Path, nome: str) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / nome
    virgula(fig)
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {nome}")
    return caminho


# ── Comportamento de cada variável ao longo da semana ─────────────────────
def figura_variaveis(destino: Path) -> Path:
    """Uma célula por variável. A linha tracejada é o valor do dia 1, e a área
    entre a curva e essa linha é preenchida na cor do sentido do desvio: tijolo
    quando o desvio é desfavorável, verde quando é favorável. A reta fina é o
    ajuste de mínimos quadrados sobre as médias diárias."""
    fig, eixos = plt.subplots(3, 3, figsize=(17.5 / 2.54, 15.5 / 2.54),
                              dpi=DPI, sharex=True)
    fig.patch.set_facecolor("white")

    for ax, var in zip(eixos.ravel(), ORDEM_GRADE):
        limpar(ax)
        y = DIARIO[var]
        base = y[0]
        pior_para_cima = AUMENTO_DESFAVORAVEL[var]

        for dia in DIAS_HIIT:
            ax.axvspan(dia - 0.4, dia + 0.4, color=FAIXA, zorder=0)

        acima = [max(v, base) for v in y]
        abaixo = [min(v, base) for v in y]
        ax.fill_between(DIAS, base, acima, color=TIJOLO if pior_para_cima
                        else VERDE, alpha=0.22, zorder=1, linewidth=0)
        ax.fill_between(DIAS, abaixo, base, color=VERDE if pior_para_cima
                        else TIJOLO, alpha=0.22, zorder=1, linewidth=0)

        ax.axhline(base, color=CINZA, linewidth=0.8, linestyle=(0, (4, 3)),
                   zorder=2)
        ax.plot(DIAS, reta(y), color=CINZA_CLARO, linewidth=1.0,
                linestyle=(0, (1.5, 1.5)), zorder=3)
        ax.plot(DIAS, y, color=AZUL, marker="o", markersize=3.4,
                linewidth=1.4, zorder=4, markeredgecolor="white",
                markeredgewidth=0.5)

        _, eta, p, _ = EFEITO_DIA[var]
        p_txt = p if p.startswith("<") else f"= {p}"
        ax.set_title(f"{var}\nη² = {vg(eta, 3)}   p {p_txt}",
                     fontsize=7.6, color=CINZA, loc="left", pad=4,
                     linespacing=1.35)

        alto, baixo_v = max(y), min(y)
        folga = (alto - baixo_v) * 0.42 or 0.5
        ax.set_ylim(baixo_v - folga * 0.45, alto + folga)
        ax.set_xlim(0.55, 7.45)
        ax.set_xticks(DIAS)

        # inclinação das médias diárias e deslocamento do dia 1 ao dia 7
        b = inclinacao(y)
        ax.annotate(f"inclinação {sg(b, 2)}/dia\nD1 a D7 {sg(y[6] - base, 2)}",
                    xy=(0.985, 0.955), xycoords="axes fraction", ha="right",
                    va="top", fontsize=6.4, color=CINZA, linespacing=1.3)

    for ax in eixos[-1]:
        ax.set_xlabel("Dia do microciclo", fontsize=7.5, color=CINZA)
    for ax in eixos[:, 0]:
        ax.set_ylabel("Escore", fontsize=7.5, color=CINZA)

    fig.legend(handles=[
        Patch(facecolor=FAIXA, label="dia de HIIT (2, 4 e 7)"),
        Line2D([], [], color=AZUL, marker="o", label="média diária"),
        Line2D([], [], color=CINZA, linestyle=(0, (4, 3)),
               label="valor do dia 1 (linha de base)"),
        Line2D([], [], color=CINZA_CLARO, linestyle=(0, (1.5, 1.5)),
               label="ajuste linear das médias diárias"),
        Patch(facecolor=TIJOLO, alpha=0.22, label="desvio desfavorável"),
        Patch(facecolor=VERDE, alpha=0.22, label="desvio favorável")],
        frameon=False, fontsize=7.2, labelcolor=CINZA, ncol=3,
        loc="lower center", bbox_to_anchor=(0.5, -0.055))
    fig.tight_layout(h_pad=1.6, w_pad=1.8, rect=(0, 0.045, 1, 1))
    return salvar(fig, destino, "fig_variaveis.png")


# ── Migração dos perfis de humor ──────────────────────────────────────────
def figura_perfis(destino: Path) -> Path:
    fig = plt.figure(figsize=(17.5 / 2.54, 12.6 / 2.54), dpi=DPI)
    fig.patch.set_facecolor("white")
    grade = fig.add_gridspec(2, 2, height_ratios=[1.28, 0.82], hspace=0.62,
                             wspace=0.38)
    a1 = fig.add_subplot(grade[0, 0])
    a2 = fig.add_subplot(grade[0, 1])
    a3 = fig.add_subplot(grade[1, :])
    for ax in (a1, a2, a3):
        limpar(ax)

    # A · migração dia a dia pelo critério de Morgan
    iceberg = [PERFIL_DIA[d][0] for d in DIAS]
    perturbado = [PERFIL_DIA[d][1] for d in DIAS]
    for dia in DIAS_HIIT:
        a1.axvspan(dia - 0.4, dia + 0.4, color=FAIXA, zorder=0)
    a1.plot(DIAS, iceberg, color=VERDE, marker="o", markersize=4,
            linewidth=1.6, zorder=3, markeredgecolor="white",
            markeredgewidth=0.6, label="perfil iceberg")
    a1.plot(DIAS, perturbado, color=TIJOLO, marker="s", markersize=4,
            linewidth=1.6, zorder=3, markeredgecolor="white",
            markeredgewidth=0.6, label="humor perturbado (PTH > 0)")
    for serie, cor, desloc in ((iceberg, VERDE, 10), (perturbado, TIJOLO, -15)):
        for i, (dx, ali) in ((0, (2, "left")), (6, (-2, "right"))):
            a1.annotate(f"{vg(serie[i], 1)}%", (DIAS[i], serie[i]),
                        textcoords="offset points", xytext=(dx, desloc),
                        ha=ali, fontsize=6.8, color=cor, fontweight="bold")
    a1.set_ylim(22, 88)
    a1.set_xlim(0.55, 7.45)
    a1.set_xticks(DIAS)
    a1.set_xlabel("Dia do microciclo", fontsize=7.5, color=CINZA)
    a1.set_ylabel("Atletas (%)", fontsize=7.5, color=CINZA)
    a1.set_title("A. Migração diária pelo critério de Morgan", fontsize=8.4,
                 color=CINZA, loc="left", pad=6)
    a1.legend(frameon=False, fontsize=6.8, labelcolor=CINZA, loc="lower left",
              handlelength=1.4, borderpad=0.1, labelspacing=0.3)

    # B · deslocamento de cada perfil de Parsons-Smith, um por linha
    perfis = sorted(PARSONS, key=lambda k: PARSONS[k][1])
    for i, nome in enumerate(perfis):
        d1, d7 = PARSONS[nome][1], PARSONS[nome][2]
        delta = d7 - d1
        cor = (CINZA_CLARO if abs(delta) <= 1.0 else
               AZUL if delta > 0 else TIJOLO)
        a2.annotate("", xy=(d7, i), xytext=(d1, i),
                    arrowprops={"arrowstyle": "-|>,head_width=0.16,"
                                "head_length=0.34", "color": cor,
                                "linewidth": 1.5, "shrinkA": 0, "shrinkB": 0})
        a2.plot(d1, i, "o", color="white", markersize=5.4,
                markeredgecolor=cor, markeredgewidth=1.2, zorder=3)
        a2.annotate(f"{sg(delta, 1)} p.p.", (max(d1, d7) + 2.0, i),
                    fontsize=6.6, color=cor, va="center", ha="left")
    a2.set_yticks(range(len(perfis)))
    a2.set_yticklabels(perfis, fontsize=7.2)
    a2.set_ylim(-0.6, len(perfis) - 0.4)
    a2.set_xlim(0, 82)
    a2.set_xlabel("Observações no perfil (%), do dia 1 ao dia 7",
                  fontsize=7.5, color=CINZA)
    a2.set_title("B. Deslocamento entre os perfis de Parsons-Smith",
                 fontsize=8.4, color=CINZA, loc="left", pad=6)
    a2.legend(handles=[
        Line2D([], [], color="white", marker="o", markeredgecolor=CINZA,
               markeredgewidth=1.2, linestyle="", label="dia 1"),
        Line2D([], [], color=AZUL, label="perfil avança"),
        Line2D([], [], color=TIJOLO, label="perfil recua"),
        Line2D([], [], color=CINZA_CLARO, label="estável (até 1 p.p.)")],
        frameon=False, fontsize=6.4, labelcolor=CINZA, loc="lower right",
        handlelength=1.3, borderpad=0.1, labelspacing=0.28)

    # C · métricas do perfil em dias de HIIT, com intervalo de confiança
    nomes = list(METRICAS_PERFIL)[::-1]
    for i, nome in enumerate(nomes):
        _, _, dz, inf, sup, p = METRICAS_PERFIL[nome]
        cor = TIJOLO if inf * sup > 0 else CINZA_CLARO
        a3.plot([inf, sup], [i, i], color=cor, linewidth=1.5, zorder=2,
                solid_capstyle="butt")
        for extremo in (inf, sup):
            a3.plot([extremo, extremo], [i - 0.09, i + 0.09], color=cor,
                    linewidth=1.2, zorder=2)
        a3.plot(dz, i, "o", color=cor, markersize=5.6, zorder=3,
                markeredgecolor="white", markeredgewidth=0.7)
        a3.annotate(f"dz = {sg(dz, 2)}   IC 95% [{vg(inf, 2)}; {vg(sup, 2)}]"
                    f"   p = {p}", (sup + 0.06, i), fontsize=6.8, color=cor,
                    va="center", ha="left")
    a3.axvline(0, color=CINZA, linewidth=0.8, zorder=1)
    a3.set_yticks(range(len(nomes)))
    a3.set_yticklabels(nomes, fontsize=7.2)
    a3.set_ylim(-0.55, len(nomes) - 0.45)
    a3.set_xlim(-1.45, 2.05)
    a3.set_xlabel("Efeito do dia de HIIT sobre a métrica do perfil (dz)",
                  fontsize=7.5, color=CINZA)
    a3.set_title("C. Efeito do dia de HIIT sobre o perfil, com intervalo de "
                 "confiança de 95%", fontsize=8.4, color=CINZA, loc="left",
                 pad=6)
    return salvar(fig, destino, "fig_perfis.png")


# ── Efeito do HIIT por variável e mudança confiável por atleta ────────────
def figura_efeito(destino: Path) -> Path:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.5 / 2.54, 6.4 / 2.54),
                                 dpi=DPI,
                                 gridspec_kw={"width_ratios": [1.35, 1.0]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        limpar(ax)

    nomes = sorted(BETA_HIIT, key=lambda k: BETA_HIIT[k][0])
    for i, nome in enumerate(nomes):
        beta, inf, sup, p = BETA_HIIT[nome]
        cor = TIJOLO if inf * sup > 0 else CINZA_CLARO
        a1.plot([inf, sup], [i, i], color=cor, linewidth=1.5, zorder=2)
        for extremo in (inf, sup):
            a1.plot([extremo, extremo], [i - 0.12, i + 0.12], color=cor,
                    linewidth=1.2, zorder=2)
        a1.plot(beta, i, "o", color=cor, markersize=5.2, zorder=3,
                markeredgecolor="white", markeredgewidth=0.6)
        a1.annotate(f"{sg(beta, 2)}   p = {p}", (4.75, i), fontsize=6.6,
                    color=cor, va="center", ha="left")
    a1.axvline(0, color=CINZA, linewidth=0.8, zorder=1)
    a1.set_yticks(range(len(nomes)))
    a1.set_yticklabels(nomes, fontsize=7.2)
    a1.set_ylim(-0.6, len(nomes) - 0.4)
    a1.set_xlim(-1.6, 9.4)
    a1.set_xlabel("Efeito do dia de HIIT no modelo misto (pontos da escala)",
                  fontsize=7.5, color=CINZA)
    a1.set_title("A. Magnitude do efeito por variável", fontsize=8.4,
                 color=CINZA, loc="left", pad=6)

    # A cor marca o sentido da mudança para o atleta, não o sinal do escore:
    # subir a fadiga e cair o vigor são, os dois, deterioração.
    chaves = list(MUDANCA_CONFIAVEL)[::-1]
    ys = range(len(chaves))
    esquerda = [0.0] * len(chaves)
    for faixa, cor, rotulo in ((0, TIJOLO, "mudança desfavorável"),
                               (1, CINZA_CLARO, "sem mudança"),
                               (2, VERDE, "mudança favorável")):
        vals = []
        for c in chaves:
            n, aumento, estavel, reducao = MUDANCA_CONFIAVEL[c]
            pior, melhor = ((aumento, reducao) if AUMENTO_DESFAVORAVEL[c]
                            else (reducao, aumento))
            vals.append([pior, estavel, melhor][faixa] / n * 100)
        a2.barh(list(ys), vals, left=esquerda, height=0.55, color=cor,
                label=rotulo, zorder=3)
        for i, (v, e) in enumerate(zip(vals, esquerda)):
            if v >= 9:
                a2.text(e + v / 2, i, f"{v:.0f}%", ha="center", va="center",
                        fontsize=6.6, color="white", fontweight="bold")
        esquerda = [e + v for e, v in zip(esquerda, vals)]
    a2.set_yticks(list(ys))
    a2.set_yticklabels(chaves, fontsize=7.2)
    a2.set_xlim(0, 100)
    a2.set_xlabel("Atletas do dia 1 ao dia 7 (%)", fontsize=7.5, color=CINZA)
    a2.set_title("B. Mudança confiável atleta a atleta", fontsize=8.4,
                 color=CINZA, loc="left", pad=6)
    a2.legend(frameon=False, fontsize=6.6, labelcolor=CINZA, ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, -0.30),
              handlelength=1.1, columnspacing=1.2)
    fig.tight_layout(w_pad=3.0)
    return salvar(fig, destino, "fig_efeito.png")


def gerar_todas(destino: Path) -> list[Path]:
    print("figuras analíticas:")
    return [figura_variaveis(destino), figura_perfis(destino),
            figura_efeito(destino)]


if __name__ == "__main__":
    gerar_todas(Path(sys.argv[1] if len(sys.argv) > 1 else "data/fig4p"))
