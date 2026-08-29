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
# Paleta divergente dos perfis: polo favorável, cinza neutro e polo de
# risco. Validada por scripts/validate_palette.js.
FAVORAVEL, NEUTRO, RISCO = "#3F7A2E", "#B4B4B0", "#A63A2B"
DIA1, DIA7 = "#8FB8DC", "#28527A"
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
    return [fig_distribuicao(destino), fig_psicometria(destino),
            fig_prevalencia_semana(destino), fig_sinal(destino)]


def gerar_artigo2(destino: Path) -> list[Path]:
    print("figuras do Artigo 2:")
    return [fig_sessoes(destino), fig_mdc(destino)]




# ══════════════════ Artigo 1 · sinal semanal do perfil ═════════════════════
def _erro_padrao(p: float, n: int) -> float:
    """Erro-padrão binomial da proporção, em pontos percentuais."""
    from math import sqrt
    return 100 * sqrt((p / 100) * (1 - p / 100) / n)


def _suavizar(y: list[float]) -> list[float]:
    """Filtro binomial de três pontos, com pesos 1, 2 e 1. É o filtro mais
    leve capaz de separar tendência de ruído em uma série de sete pontos;
    filtros mais pesados apagariam o próprio sinal."""
    s = list(y)
    for i in range(1, len(y) - 1):
        s[i] = (y[i - 1] + 2 * y[i] + y[i + 1]) / 4
    return s


def fig_sinal(destino: Path) -> Path:
    """Série diária do perfil, com a curva suavizada e a derivada.

    Versão enxuta: os pontos observados aparecem como marcadores, a tendência
    como linha única, e o que não é sinal fica em cinza. A banda de
    erro-padrão saiu da figura para a Tabela 7, que a traz por dia.
    """
    from dados import DIAS, DIAS_HIIT, N_DIA, PERFIL_DIA
    ice = [PERFIL_DIA[d][0] for d in DIAS]
    per = [PERFIL_DIA[d][1] for d in DIAS]
    piso = sum(_erro_padrao(v, N_DIA[d]) for v, d in zip(ice, DIAS)) / len(DIAS)
    s_ice, s_per = _suavizar(ice), _suavizar(per)
    d_ice = [s_ice[i] - s_ice[i - 1] for i in range(1, len(DIAS))]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(15.5 / 2.54, 11.4 / 2.54),
                                 dpi=DPI, sharex=True,
                                 gridspec_kw={"height_ratios": [1.55, 1]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        limpar(ax)
        for dia in DIAS_HIIT:
            ax.axvspan(dia - 0.4, dia + 0.4, color=FAIXA, zorder=0)

    # A · duas curvas, sem duplicação de traçado
    for serie, suave, cor, marca, rotulo in (
            (ice, s_ice, FAVORAVEL, "o", "perfil iceberg"),
            (per, s_per, RISCO, "s", "humor perturbado")):
        a1.plot(DIAS, suave, color=cor, linewidth=2.0, zorder=3, label=rotulo)
        a1.plot(DIAS, serie, linestyle="none", marker=marca, markersize=4.2,
                markerfacecolor="white", markeredgecolor=cor,
                markeredgewidth=1.2, zorder=4)
    a1.axhline(50, color=CINZA_CLARO, linewidth=0.9, linestyle=(0, (4, 3)),
               zorder=2)
    a1.annotate("maioria do elenco", (7.36, 51.2), fontsize=6.6,
                color=CINZA_CLARO, va="bottom", ha="right")
    for serie, cor in ((ice, FAVORAVEL), (per, RISCO)):
        for i, dx, ali in ((0, 5, "left"), (6, -5, "right")):
            a1.annotate(f"{serie[i]:.1f}".replace(".", ",") + "%",
                        (DIAS[i], serie[i]), textcoords="offset points",
                        xytext=(dx, 10 if serie[i] > 55 else -16), ha=ali,
                        fontsize=7.0, color=cor, fontweight="bold")
    a1.set_ylim(20, 88)
    a1.set_xlim(0.55, 7.45)
    a1.set_ylabel("Atletas (%)", fontsize=7.8, color=CINZA)
    a1.set_title("A. Predominância diária", fontsize=9.0, color=CINZA,
                 loc="left", pad=8)
    a1.legend(frameon=False, fontsize=7.2, labelcolor=CINZA, loc="lower left",
              handlelength=1.4, borderpad=0.1, labelspacing=0.3)

    # B · derivada: só o que supera o ruído recebe cor
    xs = [d + 0.5 for d in DIAS[:-1]]
    for x, v in zip(xs, d_ice):
        cor = RISCO if abs(v) > piso else CINZA_CLARO
        a2.bar(x, v, width=0.5, color=cor, zorder=3)
        if abs(v) > piso:
            a2.text(x, v - 1.8, f"{v:+.1f}".replace(".", ",").replace("-", "−"),
                    ha="center", va="top", fontsize=7.0, color=cor,
                    fontweight="bold")
    a2.axhspan(-piso, piso, color=FAIXA, zorder=1)
    a2.axhline(0, color=CINZA, linewidth=0.8, zorder=2)
    a2.annotate(f"ruído amostral ±{piso:.1f}".replace(".", ",") + " p.p.",
                (7.36, piso + 0.8), fontsize=6.6, color=CINZA_CLARO,
                va="bottom", ha="right")
    a2.set_ylim(-24, 13)
    a2.set_xticks(DIAS)
    a2.set_xlabel("Dia do microciclo", fontsize=7.8, color=CINZA)
    a2.set_ylabel("Variação (p.p./dia)", fontsize=7.8, color=CINZA)
    a2.set_title("B. Variação diária do perfil iceberg", fontsize=9.0,
                 color=CINZA, loc="left", pad=8)
    fig.tight_layout(h_pad=1.6)
    return salvar(fig, destino, "a1_sinal.png")


# ═══════════ Artigo 1 · prevalência dos perfis ao longo da semana ══════════
GRUPOS = {
    "Favorável": ["Iceberg"],
    "Neutro": ["Superfície", "Submerso"],
    "De risco": ["Barbatana tubarão", "Iceberg invertido", "Everest invertido"],
}
CORES_GRUPO = {"Favorável": FAVORAVEL, "Neutro": NEUTRO, "De risco": RISCO}
MOMENTOS = [("Dia 1\nrepouso", 1), ("Dias sem\nHIIT", 4), ("Dias de\nHIIT", 3),
            ("Dia 7\nvéspera", 2)]


def fig_prevalencia_semana(destino: Path) -> Path:
    """Prevalência dos perfis no nível do grupo ao longo da semana.

    O painel A agrega os seis perfis em três faixas de significado, o que é o
    que a leitura de grupo comporta; o painel B abre os seis no contraste
    entre o primeiro e o último dia.
    """
    from dados import PARSONS

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.0 / 2.54, 8.0 / 2.54),
                                 dpi=DPI,
                                 gridspec_kw={"width_ratios": [1.05, 1.15]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        limpar(ax)

    # A · composição em três faixas, com folga de superfície entre as faixas
    xs = list(range(len(MOMENTOS)))
    base = [0.0] * len(MOMENTOS)
    for grupo, perfis in GRUPOS.items():
        vals = [sum(PARSONS[p][i] for p in perfis) for _, i in MOMENTOS]
        a1.bar(xs, vals, bottom=base, width=0.72, color=CORES_GRUPO[grupo],
               label=grupo, zorder=3, edgecolor="white", linewidth=1.4)
        for x, v, b in zip(xs, vals, base):
            a1.text(x, b + v / 2, f"{v:.1f}".replace(".", ",") + "%",
                    ha="center", va="center", fontsize=6.6, color="white",
                    fontweight="bold")
        base = [b + v for b, v in zip(base, vals)]
    a1.set_xticks(xs)
    a1.set_xticklabels([r for r, _ in MOMENTOS], fontsize=7.4)
    a1.set_ylim(0, 100)
    a1.set_yticks([0, 25, 50, 75, 100])
    a1.set_ylabel("Observações (%)", fontsize=7.8, color=CINZA)
    a1.set_title("A. Composição do grupo", fontsize=9.0, color=CINZA,
                 loc="left", pad=8)
    a1.legend(frameon=False, fontsize=7.2, labelcolor=CINZA, ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, -0.16),
              handlelength=1.0, columnspacing=1.4, handletextpad=0.5)

    # B · os seis perfis, do primeiro ao último dia
    ordem = sorted(PARSONS, key=lambda k: PARSONS[k][1])
    ys = list(range(len(ordem)))
    altura = 0.34
    for desloc, indice, cor, rotulo in ((altura / 2, 1, DIA1, "Dia 1"),
                                        (-altura / 2, 2, DIA7, "Dia 7")):
        vals = [PARSONS[p][indice] for p in ordem]
        a2.barh([y + desloc for y in ys], vals, height=altura, color=cor,
                label=rotulo, zorder=3)
        for y, v in zip(ys, vals):
            a2.text(v + 1.4, y + desloc, f"{v:.1f}".replace(".", ",") + "%",
                    va="center", fontsize=6.8, color=CINZA)
    a2.set_yticks(ys)
    a2.set_yticklabels(ordem, fontsize=7.4)
    a2.set_xlim(0, 76)
    a2.set_xlabel("Observações no perfil (%)", fontsize=7.8, color=CINZA)
    a2.set_title("B. Os seis perfis, do primeiro ao último dia", fontsize=9.0,
                 color=CINZA, loc="left", pad=8)
    a2.legend(frameon=False, fontsize=7.2, labelcolor=CINZA, ncol=2,
              loc="upper center", bbox_to_anchor=(0.5, -0.16),
              handlelength=1.0, columnspacing=1.4, handletextpad=0.5)

    fig.tight_layout(w_pad=2.6)
    return salvar(fig, destino, "a1_prevalencia_semana.png")


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "data/figartigos")
    gerar_artigo1(d)
    gerar_artigo2(d)
