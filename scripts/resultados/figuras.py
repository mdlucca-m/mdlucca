#!/usr/bin/env python3
"""Figuras do relatório de resultados, em padrão ABNT.

Fundo branco, sem linhas de grade, sem moldura superior nem direita, escala de
cinza-compatível na impressão. Todos os valores vêm das tabelas do artigo, e a
origem de cada um está declarada em DADOS.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

AZUL, TIJOLO, VERDE = "#3A6EA5", "#A63A2B", "#4E8F3A"
CINZA, CINZA_CLARO = "#3A3A3A", "#9A9A9A"
DPI = 300

DIAS = [1, 2, 3, 4, 5, 6, 7]
HIIT = {2, 4, 7}

# Tabela 19 do artigo: médias diárias estimadas pelo modelo misto.
DIARIO = {
    "PTH (TMD)":      [2.52, 4.61, 2.87, 4.76, 2.19, 4.80, 8.28],
    "Vigor":          [7.61, 5.66, 5.71, 5.28, 5.56, 5.74, 4.49],
    "Fadiga":         [3.96, 5.17, 5.00, 5.76, 5.27, 5.75, 7.46],
    "Fadiga física":  [4.20, 5.59, 5.94, 6.53, 5.93, 6.28, 7.56],
    "Tensão":         [2.17, 1.64, 1.13, 1.37, 1.01, 1.49, 0.94],
    "Depressão":      [1.04, 1.23, 0.70, 1.13, 0.69, 1.06, 1.27],
    "Raiva":          [1.98, 1.72, 1.44, 1.37, 0.60, 1.66, 2.59],
    "Confusão":       [0.98, 0.52, 0.30, 0.41, 0.19, 0.59, 0.51],
}
# Esquema 1 e seção 3.3: duração média do dia, em horas.
DURACAO = [0.0, 2.25, 4.75, 2.25, 4.75, 4.75, 2.25]
SESSOES = [0, 2, 3, 2, 3, 3, 2]

# Tabela 23: resposta aguda pré para pós, agregada por atleta.
AGUDO = [
    ("Fadiga física", 0.76, 0.53, 1.02, True),
    ("Fadiga",        0.45, 0.23, 0.66, True),
    ("PTH (TMD)",     0.44, 0.20, 0.70, True),
    ("Vigor",        -0.39, -0.61, -0.16, True),
    ("Fadiga mental", 0.27, 0.08, 0.44, True),
    ("Depressão",     0.19, -0.03, 0.36, False),
    ("Tensão",        0.15, -0.01, 0.30, False),
    ("Raiva",         0.14, -0.10, 0.34, False),
    ("Confusão",     -0.04, -0.21, 0.10, False),
]
# Tabela 27: resposta aguda por tipo de dia.
POR_TIPO = [
    ("Fadiga física", (0.71, 0.31, 1.11), (1.04, 0.66, 1.43)),
    ("Fadiga",        (0.38, -0.02, 0.78), (0.64, 0.26, 1.03)),
    ("PTH (TMD)",     (0.41, 0.01, 0.81), (0.52, 0.14, 0.91)),
    ("Vigor",        (-0.44, -0.84, -0.04), (-0.39, -0.77, 0.00)),
]
# Tabela 20: perfil iceberg e perturbação por dia.
ICEBERG = [71.4, 48.9, 44.0, 41.7, 53.5, 47.1, 32.6]
PERTURBADO = [47.6, 64.9, 54.7, 65.0, 50.7, 55.9, 71.7]
# Tabela 21: perfis de Parsons-Smith no primeiro e no último dia.
PERFIS = [
    ("Superfície", 47.6, 60.9), ("Iceberg", 21.4, 6.5),
    ("Submerso", 7.1, 10.9), ("Iceberg invertido", 9.5, 6.5),
    ("Barbatana de tubarão", 9.5, 10.9), ("Everest invertido", 4.8, 4.3),
]
# Tabela 48: carga interna nas três sessões de HIIT.
SESSOES_HIIT = {"dia": ["Dia 2", "Dia 4", "Dia 7"], "fc": [184, 183, 181],
                "pse": [8.5, 8.5, 9.1], "hrr": [25.2, 27.4, 27.8]}


def eixo_limpo(ax, *, esquerda=True):
    """Fundo branco, sem grade, sem moldura superior nem direita."""
    ax.set_facecolor("white")
    ax.grid(False)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(CINZA)
        ax.spines[lado].set_linewidth(0.8)
    if not esquerda:
        ax.spines["left"].set_visible(False)
    ax.tick_params(colors=CINZA, labelsize=9, width=0.8, length=3)
    for rot in ax.get_xticklabels() + ax.get_yticklabels():
        rot.set_color(CINZA)


def nova(largura=16, altura=9):
    fig, ax = plt.subplots(figsize=(largura / 2.54, altura / 2.54), dpi=DPI)
    fig.patch.set_facecolor("white")
    eixo_limpo(ax)
    return fig, ax


def salvar(fig, destino: Path, nome: str):
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / nome
    fig.savefig(caminho, dpi=DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"  {nome}")
    return caminho


# ── Figura 1 · carga por dia ───────────────────────────────────────────────
def figura_carga(destino: Path):
    fig, ax = nova(16, 8)
    cores = [TIJOLO if d in HIIT else AZUL for d in DIAS]
    barras = ax.bar(DIAS, DURACAO, color=cores, width=0.62, zorder=3)
    for d, h, s in zip(DIAS, DURACAO, SESSOES):
        if h == 0:
            ax.text(d, 0.12, "repouso", ha="center", va="bottom",
                    fontsize=8.5, color=CINZA)
        else:
            ax.text(d, h + 0.12, f"{h:.2f} h".replace(".", ","), ha="center",
                    va="bottom", fontsize=8.5, color=CINZA)
            ax.text(d, h / 2, f"{s} sessões", ha="center", va="center",
                    fontsize=8.5, color="white")
    ax.set_ylabel("Duração do dia de treino (horas)", fontsize=9.5, color=CINZA)
    ax.set_xlabel("Dia do microciclo", fontsize=9.5, color=CINZA)
    ax.set_xticks(DIAS)
    ax.set_ylim(0, 5.6)
    ax.yaxis.set_major_locator(MultipleLocator(1))
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=TIJOLO, label="Dia com HIIT"),
                       Patch(facecolor=AZUL, label="Dia de volume, sem HIIT")],
              frameon=False, fontsize=9, loc="upper left", labelcolor=CINZA)
    return salvar(fig, destino, "figura1_carga.png")


# ── Figura 2 · trajetória diária ───────────────────────────────────────────
def figura_trajetoria(destino: Path):
    fig, ax = nova(16, 9)
    series = [("PTH (TMD)", TIJOLO, "o", "-"), ("Fadiga", AZUL, "s", "-"),
              ("Vigor", VERDE, "^", "-")]
    for nome, cor, marca, traco in series:
        y = DIARIO[nome]
        ax.plot(DIAS, y, color=cor, marker=marca, markersize=5.5,
                linewidth=1.8, linestyle=traco, label=nome, zorder=3,
                markeredgecolor="white", markeredgewidth=0.8)
        ax.annotate(f"{y[-1]:.2f}".replace(".", ","), (DIAS[-1], y[-1]),
                    textcoords="offset points", xytext=(9, 0), fontsize=9,
                    color=cor, va="center", fontweight="bold")
    for d in HIIT:
        ax.axvline(d, color=CINZA_CLARO, linewidth=0.7, linestyle=(0, (3, 3)),
                   zorder=1)
    ax.text(5.6, 0.35, "linhas tracejadas: dias com HIIT", fontsize=8.5,
            color=CINZA_CLARO, ha="center")
    ax.set_ylabel("Escore médio do dia", fontsize=9.5, color=CINZA)
    ax.set_xlabel("Dia do microciclo", fontsize=9.5, color=CINZA)
    ax.set_xticks(DIAS)
    ax.set_xlim(0.7, 7.7)
    ax.set_ylim(0, 9.3)
    ax.legend(frameon=False, fontsize=9, loc="upper center", ncol=3,
              labelcolor=CINZA, bbox_to_anchor=(0.5, 1.10))
    return salvar(fig, destino, "figura2_trajetoria.png")


# ── Figura 3 · resposta aguda com intervalo de confiança ───────────────────
def figura_agudo(destino: Path):
    fig, ax = nova(16, 10)
    nomes = [a[0] for a in AGUDO][::-1]
    pos = range(len(nomes))
    for i, (nome, dz, li, ls, signif) in enumerate(AGUDO[::-1]):
        cor = TIJOLO if signif else CINZA_CLARO
        ax.plot([li, ls], [i, i], color=cor, linewidth=1.6, zorder=2,
                solid_capstyle="butt")
        ax.plot(dz, i, "o", color=cor, markersize=6.5, zorder=3,
                markeredgecolor="white", markeredgewidth=0.8)
        ax.text(ls + 0.05 if dz > 0 else li - 0.05,
                i, f"{dz:+.2f}".replace(".", ","), fontsize=8.5, color=cor,
                va="center", ha="left" if dz > 0 else "right")
    ax.axvline(0, color=CINZA, linewidth=0.9, zorder=1)
    ax.set_yticks(list(pos))
    ax.set_yticklabels(nomes, fontsize=9.5)
    ax.set_xlabel("Tamanho de efeito da resposta aguda, dz, com IC 95%",
                  fontsize=9.5, color=CINZA)
    ax.set_xlim(-0.95, 1.35)
    ax.set_ylim(-0.7, len(nomes) - 0.3)
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([], [], color=TIJOLO, marker="o", linestyle="-",
               label="sobrevive à correção FDR"),
        Line2D([], [], color=CINZA_CLARO, marker="o", linestyle="-",
               label="não sobrevive à correção FDR")],
        frameon=False, fontsize=9, loc="lower right", labelcolor=CINZA)
    return salvar(fig, destino, "figura3_resposta_aguda.png")


# ── Figura 4 · resposta aguda por tipo de dia ──────────────────────────────
def figura_tipo_dia(destino: Path):
    fig, ax = nova(16, 8)
    largura = 0.34
    for i, (nome, sem, com) in enumerate(POR_TIPO):
        for desloc, (dz, li, ls), cor, rot in (
                (-largura / 2, sem, AZUL, "Sem HIIT"),
                (+largura / 2, com, TIJOLO, "Com HIIT")):
            x = i + desloc
            ax.plot([x, x], [li, ls], color=cor, linewidth=1.5, zorder=2)
            ax.plot(x, dz, "o", color=cor, markersize=6, zorder=3,
                    markeredgecolor="white", markeredgewidth=0.8,
                    label=rot if i == 0 else None)
            ax.text(x, ls + 0.04, f"{dz:+.2f}".replace(".", ","), ha="center",
                    va="bottom", fontsize=8, color=cor)
    ax.axhline(0, color=CINZA, linewidth=0.9, zorder=1)
    ax.set_xticks(range(len(POR_TIPO)))
    ax.set_xticklabels([p[0] for p in POR_TIPO], fontsize=9.5)
    ax.set_ylabel("dz da resposta aguda, com IC 95%", fontsize=9.5, color=CINZA)
    ax.set_ylim(-1.05, 1.65)
    ax.legend(frameon=False, fontsize=9, loc="upper right", labelcolor=CINZA)
    return salvar(fig, destino, "figura4_tipo_de_dia.png")


# ── Figura 5 · perfis de humor ─────────────────────────────────────────────
def figura_perfis(destino: Path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17 / 2.54, 8 / 2.54), dpi=DPI,
                                 gridspec_kw={"width_ratios": [1.05, 1]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        eixo_limpo(ax)

    a1.plot(DIAS, ICEBERG, color=VERDE, marker="o", markersize=5.5,
            linewidth=1.8, label="Perfil iceberg", zorder=3,
            markeredgecolor="white", markeredgewidth=0.8)
    a1.plot(DIAS, PERTURBADO, color=TIJOLO, marker="s", markersize=5.5,
            linewidth=1.8, label="Humor perturbado (PTH > 0)", zorder=3,
            markeredgecolor="white", markeredgewidth=0.8)
    for y, cor in ((ICEBERG, VERDE), (PERTURBADO, TIJOLO)):
        a1.annotate(f"{y[-1]:.1f}%".replace(".", ","), (7, y[-1]),
                    textcoords="offset points", xytext=(7, 0), fontsize=8.5,
                    color=cor, va="center", fontweight="bold")
    a1.set_xticks(DIAS)
    a1.set_xlim(0.7, 7.9)
    a1.set_ylim(0, 82)
    a1.set_ylabel("Atletas (%)", fontsize=9.5, color=CINZA)
    a1.set_xlabel("Dia do microciclo", fontsize=9.5, color=CINZA)
    a1.set_title("A. Prontidão ao longo da semana", fontsize=10,
                 color=CINZA, loc="left", pad=8)
    a1.legend(frameon=False, fontsize=8.5, loc="lower left", labelcolor=CINZA)

    nomes = [p[0] for p in PERFIS][::-1]
    d1 = [p[1] for p in PERFIS][::-1]
    d7 = [p[2] for p in PERFIS][::-1]
    y = range(len(nomes))
    alt = 0.34
    a2.barh([i + alt / 2 for i in y], d1, height=alt, color=AZUL,
            label="Dia 1", zorder=3)
    a2.barh([i - alt / 2 for i in y], d7, height=alt, color=TIJOLO,
            label="Dia 7", zorder=3)
    for i, (v1, v7) in enumerate(zip(d1, d7)):
        a2.text(v1 + 1, i + alt / 2, f"{v1:.1f}".replace(".", ","),
                va="center", fontsize=8, color=AZUL)
        a2.text(v7 + 1, i - alt / 2, f"{v7:.1f}".replace(".", ","),
                va="center", fontsize=8, color=TIJOLO)
    a2.set_yticks(list(y))
    a2.set_yticklabels(nomes, fontsize=8.5)
    a2.set_xlim(0, 72)
    a2.set_xlabel("Observações (%)", fontsize=9.5, color=CINZA)
    a2.set_title("B. Perfis de Parsons-Smith", fontsize=10, color=CINZA,
                 loc="left", pad=8)
    a2.legend(frameon=False, fontsize=8.5, loc="center right",
              bbox_to_anchor=(1.0, 0.42), labelcolor=CINZA)
    fig.tight_layout(w_pad=2.5)
    return salvar(fig, destino, "figura5_perfis.png")


# ── Figura 6 · carga interna nas sessões de HIIT ───────────────────────────
def figura_hiit(destino: Path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16 / 2.54, 7 / 2.54), dpi=DPI)
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        eixo_limpo(ax)
    x = [1, 2, 3]
    rot = SESSOES_HIIT["dia"]

    a1.plot(x, SESSOES_HIIT["fc"], color=AZUL, marker="o", markersize=6,
            linewidth=1.8, zorder=3, markeredgecolor="white",
            markeredgewidth=0.8)
    for xi, v in zip(x, SESSOES_HIIT["fc"]):
        a1.text(xi, v + 0.35, str(v), ha="center", fontsize=8.5, color=AZUL)
    a1.set_xticks(x)
    a1.set_xticklabels(rot, fontsize=9)
    a1.set_ylim(178, 186.5)
    a1.set_ylabel("FC de pico (bpm)", fontsize=9.5, color=CINZA)
    a1.set_title("A. Carga externa entregue", fontsize=10, color=CINZA,
                 loc="left", pad=8)

    a2.plot(x, SESSOES_HIIT["pse"], color=TIJOLO, marker="s", markersize=6,
            linewidth=1.8, zorder=3, markeredgecolor="white",
            markeredgewidth=0.8)
    for xi, v in zip(x, SESSOES_HIIT["pse"]):
        a2.text(xi, v + 0.06, f"{v:.1f}".replace(".", ","), ha="center",
                fontsize=8.5, color=TIJOLO)
    a2.set_xticks(x)
    a2.set_xticklabels(rot, fontsize=9)
    a2.set_ylim(8.1, 9.5)
    a2.set_ylabel("PSE ao final da sessão (0 a 10)", fontsize=9.5, color=CINZA)
    a2.set_title("B. Esforço percebido", fontsize=10, color=CINZA,
                 loc="left", pad=8)
    fig.tight_layout(w_pad=3)
    return salvar(fig, destino, "figura6_hiit.png")


def gerar_todas(destino: Path) -> list[Path]:
    print("figuras geradas:")
    return [figura_carga(destino), figura_trajetoria(destino),
            figura_agudo(destino), figura_tipo_dia(destino),
            figura_perfis(destino), figura_hiit(destino)]


if __name__ == "__main__":
    import sys
    gerar_todas(Path(sys.argv[1] if len(sys.argv) > 1 else "data/figuras"))
