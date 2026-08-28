#!/usr/bin/env python3
"""Figuras dos dois artigos da série.

Fundo branco, sem linhas de grade, 300 dpi. Cada série carrega marcador ou
posição própria além da cor, o que preserva a leitura em impressão
monocromática.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "artigo4p"))
import fonte as F  # noqa: E402

AZUL, TIJOLO, VERDE = "#3A6EA5", "#A63A2B", "#4E8F3A"
CINZA, CINZA_CLARO, FAIXA = "#3A3A3A", "#8C8C8C", "#EFEFEF"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comum"))
from grafico import virgula  # noqa: E402

DPI = 300


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


def vg(v, casas=2):
    return f"{v:.{casas}f}".replace(".", ",").replace("-", "−")


# ══════════════════════════════════ Artigo 1 ═══════════════════════════════
def fig_distribuicao(destino: Path) -> Path:
    """Caixa construída sobre os percentis observados, não sobre média e
    desvio: com assimetria de até 3,7 a média deixa de descrever a
    distribuição. A faixa cinza marca o piso da escala."""
    ordem = ["Vigor", "Fadiga", "Raiva", "Tensão", "Depressão", "Confusão"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.5 / 2.54, 7.2 / 2.54),
                                 dpi=DPI, gridspec_kw={"width_ratios": [1.2, 1]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        limpar(ax)

    for i, nome in enumerate(ordem):
        p5, p25, p50, p75, p95 = F.PERCENTIS[nome]
        y = len(ordem) - 1 - i
        a1.plot([p5, p95], [y, y], color=CINZA, linewidth=0.9, zorder=2)
        for extremo in (p5, p95):
            a1.plot([extremo, extremo], [y - 0.1, y + 0.1], color=CINZA,
                    linewidth=0.9, zorder=2)
        a1.add_patch(Rectangle((p25, y - 0.22), max(p75 - p25, 0.12), 0.44,
                               facecolor=AZUL, edgecolor="white",
                               linewidth=0.6, zorder=3))
        a1.plot([p50, p50], [y - 0.22, y + 0.22], color="white", linewidth=1.4,
                zorder=4)
        a1.annotate(f"mediana {p50}", (p95 + 0.4, y), fontsize=6.6,
                    color=CINZA, va="center")
    a1.axvspan(-0.35, 0.35, color=FAIXA, zorder=0)
    a1.set_yticks(range(len(ordem)))
    a1.set_yticklabels(ordem[::-1], fontsize=7.5)
    a1.set_xlim(-0.6, 17)
    a1.set_ylim(-0.6, len(ordem) - 0.4)
    a1.set_xlabel("Escore da subescala (0 a 16 pontos)", fontsize=7.5,
                  color=CINZA)
    a1.set_title("A. Distribuição observada, por percentis", fontsize=8.6,
                 color=CINZA, loc="left", pad=6)
    a1.legend(handles=[
        Patch(facecolor=AZUL, label="intervalo interquartil (P25 a P75)"),
        Line2D([], [], color=CINZA, label="P5 a P95"),
        Patch(facecolor=FAIXA, label="piso da escala")],
        frameon=False, fontsize=6.6, labelcolor=CINZA, loc="lower right",
        handlelength=1.2, borderpad=0.1, labelspacing=0.28)

    pisos = [(n, F.DESCRITIVA[n][6]) for n in ordem]
    pisos.sort(key=lambda x: x[1])
    ys = list(range(len(pisos)))
    for y, (nome, piso) in zip(ys, pisos):
        cor = TIJOLO if piso >= 40 else VERDE
        a2.barh(y, piso, height=0.55, color=cor, zorder=3)
        a2.text(piso + 1.6, y, f"{vg(piso, 1)}%", va="center", fontsize=6.8,
                color=cor)
    a2.axvline(40, color=CINZA, linewidth=0.8, linestyle=(0, (4, 3)), zorder=2)
    a2.annotate("limite de 40%", (40.8, len(pisos) - 0.55), fontsize=6.4,
                color=CINZA)
    a2.set_yticks(ys)
    a2.set_yticklabels([n for n, _ in pisos], fontsize=7.5)
    a2.set_xlim(0, 100)
    a2.set_xlabel("Respostas no valor mínimo da subescala (%)", fontsize=7.5,
                  color=CINZA)
    a2.set_title("B. Efeito piso", fontsize=8.6, color=CINZA, loc="left", pad=6)
    fig.tight_layout(w_pad=2.4)
    return salvar(fig, destino, "a1_distribuicao.png")


def fig_psicometria(destino: Path) -> Path:
    """Confiabilidade interna e estabilidade entre dias, lado a lado: uma
    subescala útil precisa das duas."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.5 / 2.54, 7.0 / 2.54),
                                 dpi=DPI)
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        limpar(ax)

    ordem = sorted(F.CONFIABILIDADE, key=lambda k: F.CONFIABILIDADE[k][0])
    ys = list(range(len(ordem)))
    altura = 0.36
    for desloc, indice, cor, rotulo in ((altura / 2, 0, CINZA_CLARO,
                                         "alfa de Cronbach"),
                                        (-altura / 2, 2, AZUL,
                                         "ômega ordinal")):
        vals = [F.CONFIABILIDADE[n][indice] for n in ordem]
        xs = [v if v is not None else 0 for v in vals]
        a1.barh([y + desloc for y in ys], xs, height=altura, color=cor,
                label=rotulo, zorder=3)
        for y, v in zip(ys, vals):
            texto = vg(v) if v is not None else "não estimável"
            a1.text((v if v else 0) + 0.015, y + desloc, texto, va="center",
                    fontsize=6.4, color=cor)
    a1.axvline(0.70, color=TIJOLO, linewidth=0.9, linestyle=(0, (4, 3)),
               zorder=2)
    a1.annotate("0,70", (0.712, len(ordem) - 0.55), fontsize=6.4,
                color=TIJOLO)
    a1.set_yticks(ys)
    a1.set_yticklabels(ordem, fontsize=7.5)
    a1.set_xlim(0, 1.22)
    a1.set_xlabel("Coeficiente de confiabilidade", fontsize=7.5, color=CINZA)
    a1.set_title("A. Consistência interna", fontsize=8.6, color=CINZA,
                 loc="left", pad=6)
    a1.legend(frameon=False, fontsize=6.6, labelcolor=CINZA,
              loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=2,
              handlelength=1.2, borderpad=0.1, columnspacing=1.6)

    ordem2 = sorted(F.ESTABILIDADE, key=lambda k: F.ESTABILIDADE[k][0])
    ys2 = list(range(len(ordem2)))
    for y, nome in zip(ys2, ordem2):
        um, sete = F.ESTABILIDADE[nome]
        a2.annotate("", xy=(sete, y), xytext=(um, y),
                    arrowprops={"arrowstyle": "-|>,head_width=0.16,"
                                "head_length=0.34", "color": VERDE,
                                "linewidth": 1.5, "shrinkA": 0, "shrinkB": 0})
        a2.plot(um, y, "o", color="white", markersize=5.4,
                markeredgecolor=CINZA_CLARO, markeredgewidth=1.2, zorder=3)
        a2.annotate(f"{vg(um)} para {vg(sete)}", (sete + 0.02, y), fontsize=6.6,
                    color=VERDE, va="center")
    a2.axvline(0.70, color=TIJOLO, linewidth=0.9, linestyle=(0, (4, 3)),
               zorder=1)
    a2.set_yticks(ys2)
    a2.set_yticklabels(ordem2, fontsize=7.5)
    a2.set_xlim(0.2, 1.24)
    a2.set_xlabel("ICC de uma coleta e da média de sete dias", fontsize=7.5,
                  color=CINZA)
    a2.set_title("B. Estabilidade entre dias", fontsize=8.6, color=CINZA,
                 loc="left", pad=6)
    fig.tight_layout(w_pad=2.6)
    return salvar(fig, destino, "a1_psicometria.png")


# ══════════════════════════════════ Artigo 2 ═══════════════════════════════
def fig_sessoes(destino: Path) -> Path:
    """A tese do Artigo 2: o estímulo externo cai enquanto o custo interno
    sobe, ao longo das três sessões equivalentes de HIIT."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.5 / 2.54, 7.6 / 2.54),
                                 dpi=DPI)
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        limpar(ax)

    xs = [1, 2, 3]
    rotulos = ["S1 (dia 2)", "S2 (dia 4)", "S3 (dia 7)"]

    # A · o que a sessão entregou, em percentual da primeira sessão
    entregue = {"FC de pico": F.ESTIMULO["FC de pico (bpm)"][:3],
                "Esforço percebido": F.ESTIMULO["PSE final (0 a 10)"][:3]}
    estilos = {"FC de pico": (AZUL, "o"), "Esforço percebido": (TIJOLO, "s")}
    for nome, serie in entregue.items():
        cor, marca = estilos[nome]
        rel = [100 * v / serie[0] for v in serie]
        a1.plot(xs, rel, color=cor, marker=marca, markersize=4.6,
                linewidth=1.6, zorder=3, markeredgecolor="white",
                markeredgewidth=0.6, label=nome)
        for x, v, bruto in zip(xs, rel, serie):
            a1.annotate(vg(bruto, 0 if bruto > 20 else 1),
                        (x, v), textcoords="offset points",
                        xytext=(0, 8 if cor == TIJOLO else -13), ha="center",
                        fontsize=6.6, color=cor, fontweight="bold")
    a1.axhline(100, color=CINZA, linewidth=0.8, linestyle=(0, (4, 3)), zorder=1)
    a1.set_xticks(xs)
    a1.set_xticklabels(rotulos, fontsize=7.5)
    a1.set_xlim(0.7, 3.3)
    a1.set_ylim(94, 110)
    a1.set_ylabel("Percentual da primeira sessão", fontsize=7.5, color=CINZA)
    a1.set_title("A. O que a sessão entregou e o que ela custou",
                 fontsize=8.6, color=CINZA, loc="left", pad=6)
    a1.legend(frameon=False, fontsize=6.8, labelcolor=CINZA, loc="upper left",
              handlelength=1.4, borderpad=0.1, labelspacing=0.3)

    # B · custo psicológico acumulado, com a inclinação por sessão
    chaves = ["PTH (TMD)", "Fadiga (BRUMS)", "Fadiga física", "Sonolência",
              "Vigor", "TQR (recuperação)"]
    marcas = ["o", "s", "^", "D", "v", "P"]
    tracado = []
    for nome, marca in zip(chaves, marcas):
        s1, s2, s3, incl, sig, _ = F.SESSOES[nome]
        cor = TIJOLO if (incl > 0) == F.AUMENTO_RUIM[nome] else VERDE
        rel = [100 * v / s1 for v in (s1, s2, s3)]
        a2.plot(xs, rel, color=cor, marker=marca, markersize=4.2,
                linewidth=1.4, zorder=3, markeredgecolor="white",
                markeredgewidth=0.6)
        tracado.append([rel[2], nome, incl, cor])

    # Afasta os rótulos que ficariam sobrepostos, sem mover as linhas.
    tracado.sort(key=lambda t: t[0])
    minimo = 5.5
    for i in range(1, len(tracado)):
        if tracado[i][0] - tracado[i - 1][0] < minimo:
            tracado[i][0] = tracado[i - 1][0] + minimo
    for altura_rotulo, nome, incl, cor in tracado:
        a2.annotate(f"{nome}  {F.sinal(incl, 2)}/sessão",
                    (3.08, altura_rotulo), fontsize=6.4, color=cor,
                    va="center")
    a2.axhline(100, color=CINZA, linewidth=0.8, linestyle=(0, (4, 3)), zorder=1)
    a2.set_xticks(xs)
    a2.set_xticklabels(["S1", "S2", "S3"], fontsize=7.5)
    a2.set_xlim(0.85, 5.6)
    a2.set_xlabel("Sessão de HIIT", fontsize=7.5, color=CINZA)
    a2.set_ylabel("Percentual da primeira sessão", fontsize=7.5, color=CINZA)
    a2.set_title("B. Custo psicológico ao longo das três sessões",
                 fontsize=8.6, color=CINZA, loc="left", pad=6)
    a2.legend(handles=[Line2D([], [], color=TIJOLO,
                              label="piora em relação à primeira sessão")],
              frameon=False, fontsize=6.6, labelcolor=CINZA, loc="lower left",
              handlelength=1.2, borderpad=0.1, labelspacing=0.28)
    fig.tight_layout(w_pad=2.2)
    return salvar(fig, destino, "a2_sessoes.png")


def fig_mdc(destino: Path) -> Path:
    """Quem de fato mudou: proporção que ultrapassa o menor valor detectável,
    na sessão e na semana, e recuperação noturna."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.5 / 2.54, 7.0 / 2.54),
                                 dpi=DPI, gridspec_kw={"width_ratios": [1.3, 1]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        limpar(ax)

    ordem = sorted(F.MDC, key=lambda k: F.MDC[k][3])
    ys = list(range(len(ordem)))
    altura = 0.36
    for desloc, indice, cor, rotulo in ((altura / 2, 1, CINZA_CLARO,
                                         "na sessão"),
                                        (-altura / 2, 3, TIJOLO, "na semana")):
        vals = [F.MDC[n][indice] for n in ordem]
        a1.barh([y + desloc for y in ys], vals, height=altura, color=cor,
                label=rotulo, zorder=3)
        for y, v in zip(ys, vals):
            a1.text(v + 1.4, y + desloc, f"{v}%", va="center", fontsize=6.4,
                    color=cor)
    a1.set_yticks(ys)
    a1.set_yticklabels(ordem, fontsize=7.5)
    a1.set_xlim(0, 78)
    a1.set_xlabel("Atletas acima do menor valor detectável (%)", fontsize=7.5,
                  color=CINZA)
    a1.set_title("A. Mudança que ultrapassa o erro de medida", fontsize=8.6,
                 color=CINZA, loc="left", pad=6)
    a1.legend(frameon=False, fontsize=6.6, labelcolor=CINZA, loc="lower right",
              handlelength=1.2, borderpad=0.1, labelspacing=0.28)

    ordem2 = sorted(F.RECUPERACAO, key=lambda k: F.RECUPERACAO[k][0])
    ys2 = list(range(len(ordem2)))
    for y, nome in zip(ys2, ordem2):
        rec, desloc = F.RECUPERACAO[nome]
        cor = VERDE if rec >= 100 else TIJOLO
        a2.barh(y, rec, height=0.5, color=cor, zorder=3)
        a2.text(rec + 2.0, y, f"{vg(rec, 1)}%", va="center", fontsize=6.8,
                color=cor)
    a2.axvline(100, color=CINZA, linewidth=0.9, linestyle=(0, (4, 3)), zorder=2)
    a2.annotate("recuperação completa", (101.5, -0.42), fontsize=6.4,
                color=CINZA)
    a2.set_yticks(ys2)
    a2.set_yticklabels(ordem2, fontsize=7.5)
    a2.set_xlim(0, 148)
    a2.set_xlabel("Recuperação noturna média (%)", fontsize=7.5, color=CINZA)
    a2.set_title("B. Quanto a noite devolve", fontsize=8.6, color=CINZA,
                 loc="left", pad=6)
    fig.tight_layout(w_pad=2.4)
    return salvar(fig, destino, "a2_mdc.png")


def gerar_artigo1(destino: Path) -> list[Path]:
    print("figuras do Artigo 1:")
    return [fig_distribuicao(destino), fig_psicometria(destino)]


def gerar_artigo2(destino: Path) -> list[Path]:
    print("figuras do Artigo 2:")
    return [fig_sessoes(destino), fig_mdc(destino)]


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "data/figartigos")
    gerar_artigo1(d)
    gerar_artigo2(d)
