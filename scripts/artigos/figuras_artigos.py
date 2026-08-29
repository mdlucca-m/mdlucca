#!/usr/bin/env python3
"""Figuras dos dois artigos da série.

Padrão visual definido em scripts/comum/estilo.py: título em negrito, moldura
fechada, grade discreta ao fundo, legenda em caixa e rótulo direto sobre os
valores. Cada série carrega marcador ou posição própria além da cor, o que
preserva a leitura em impressão monocromática.
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "artigo4p"))
sys.path.insert(0, str(AQUI.parent / "comum"))
import estilo as E  # noqa: E402
import fonte as F  # noqa: E402
from estilo import (AZUL, BARRA_A, BARRA_B, CORAL, FAIXA, GRADE, OCRE, ROXO,
                    TEAL, TINTA, TINTA_FRACA, VERDE, aplicar, legenda, salvar,
                    sg, titulo, vg)  # noqa: E402

DPI = E.DPI
# Codificação divergente dos perfis: polo favorável, cinza neutro no meio e
# polo de risco. O cinza é o ponto neutro do esquema, não uma série a mais.
FAVORAVEL, NEUTRO, RISCO = VERDE, "#B4B4B0", CORAL


# ══════════════════════════════════════════════════════════ Artigo 1 ═══
def fig_distribuicao(destino: Path) -> Path:
    """Caixa construída sobre os percentis observados, não sobre média e
    desvio: com assimetria de até 3,7 a média deixa de descrever a
    distribuição."""
    ordem = ["Vigor", "Fadiga", "Raiva", "Tensão", "Depressão", "Confusão"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.4 / 2.54, 7.6 / 2.54),
                                 dpi=DPI, gridspec_kw={"width_ratios": [1.25, 1]})
    fig.patch.set_facecolor("white")
    aplicar(a1, grade="x")
    aplicar(a2, grade="x")

    for i, nome in enumerate(ordem):
        p5, p25, p50, p75, p95 = F.PERCENTIS[nome]
        y = len(ordem) - 1 - i
        a1.plot([p5, p95], [y, y], color=TINTA_FRACA, linewidth=1.0, zorder=2)
        for extremo in (p5, p95):
            a1.plot([extremo, extremo], [y - 0.12, y + 0.12], color=TINTA_FRACA,
                    linewidth=1.0, zorder=2)
        a1.add_patch(Rectangle((p25, y - 0.24), max(p75 - p25, 0.14), 0.48,
                               facecolor=TEAL, edgecolor="white",
                               linewidth=0.8, zorder=3))
        a1.plot([p50, p50], [y - 0.24, y + 0.24], color="white", linewidth=1.6,
                zorder=4)
        a1.annotate(f"mediana {p50}", (p95 + 0.5, y), fontsize=7.4,
                    color=TINTA_FRACA, va="center")
    a1.axvspan(-0.35, 0.35, color=FAIXA, zorder=1)
    a1.set_yticks(range(len(ordem)))
    a1.set_yticklabels(ordem[::-1], fontsize=8.4)
    a1.set_xlim(-0.6, 17.5)
    a1.set_ylim(-0.6, len(ordem) - 0.4)
    a1.set_xlabel("Escore da subescala (0 a 16 pontos)", fontsize=8.8,
                  color=TINTA)
    titulo(a1, "A. Distribuição por percentis", tamanho=9.4)
    legenda(a1, handles=[
        Patch(facecolor=TEAL, label="intervalo interquartil"),
        Line2D([], [], color=TINTA_FRACA, label="P5 a P95"),
        Patch(facecolor=FAIXA, label="piso da escala")],
        loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=3,
        fontsize=7.4)

    pisos = sorted(((n, F.DESCRITIVA[n][6]) for n in ordem), key=lambda x: x[1])
    for y, (nome, piso) in enumerate(pisos):
        cor = CORAL if piso >= 15 else TEAL
        a2.barh(y, piso, height=0.6, color=cor, zorder=3)
        a2.text(piso + 2.0, y, vg(piso) + "%", va="center", fontsize=7.8,
                color=TINTA)
    a2.axvline(15, color=TINTA, linewidth=1.0, linestyle=(0, (5, 3)), zorder=4)
    a2.annotate("limite de 15%", (17.5, 1.15), fontsize=7.4, color=TINTA,
                fontweight="bold")
    a2.set_yticks(range(len(pisos)))
    a2.set_yticklabels([n for n, _ in pisos], fontsize=8.4)
    a2.set_xlim(0, 100)
    a2.set_xlabel("Respostas no valor mínimo (%)", fontsize=8.8, color=TINTA)
    titulo(a2, "B. Efeito piso")
    fig.tight_layout(w_pad=2.4)
    return salvar(fig, destino, "a1_distribuicao.png")


def fig_psicometria(destino: Path) -> Path:
    """Consistência interna e estabilidade entre dias, lado a lado: uma
    subescala útil precisa das duas."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.4 / 2.54, 7.4 / 2.54),
                                 dpi=DPI)
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        aplicar(ax, grade="x")

    ordem = sorted(F.CONFIABILIDADE, key=lambda k: F.CONFIABILIDADE[k][0])
    ys = list(range(len(ordem)))
    altura = 0.36
    for desloc, indice, cor, rotulo in ((altura / 2, 0, AZUL,
                                         "alfa de Cronbach"),
                                        (-altura / 2, 2, TEAL,
                                         "ômega ordinal")):
        vals = [F.CONFIABILIDADE[n][indice] for n in ordem]
        a1.barh([y + desloc for y in ys], [v or 0 for v in vals],
                height=altura, color=cor, label=rotulo, zorder=3)
        for y, v in zip(ys, vals):
            texto = vg(v, 2) if v is not None else "não estimável"
            a1.text((v or 0) + 0.02, y + desloc, texto, va="center",
                    fontsize=7.2, color=TINTA)
    a1.axvline(0.70, color=CORAL, linewidth=1.1, linestyle=(0, (5, 3)),
               zorder=4)
    a1.annotate("0,70", (0.715, len(ordem) - 0.95), fontsize=7.4, color=CORAL,
                fontweight="bold")
    a1.set_yticks(ys)
    a1.set_yticklabels(ordem, fontsize=8.4)
    a1.set_xlim(0, 1.28)
    a1.set_xlabel("Coeficiente de confiabilidade", fontsize=8.8, color=TINTA)
    titulo(a1, "A. Consistência interna")
    legenda(a1, loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2)

    ordem2 = sorted(F.ESTABILIDADE, key=lambda k: F.ESTABILIDADE[k][0])
    for y, nome in enumerate(ordem2):
        um, sete = F.ESTABILIDADE[nome]
        a2.annotate("", xy=(sete, y), xytext=(um, y),
                    arrowprops={"arrowstyle": "-|>,head_width=0.18,"
                                "head_length=0.36", "color": TEAL,
                                "linewidth": 1.8, "shrinkA": 0, "shrinkB": 0})
        a2.plot(um, y, "o", color="white", markersize=6.0,
                markeredgecolor=AZUL, markeredgewidth=1.5, zorder=3)
        a2.annotate(f"{vg(um, 2)} para {vg(sete, 2)}", (sete + 0.025, y),
                    fontsize=7.4, color=TINTA, va="center")
    a2.axvline(0.70, color=CORAL, linewidth=1.1, linestyle=(0, (5, 3)),
               zorder=1)
    a2.set_yticks(range(len(ordem2)))
    a2.set_yticklabels(ordem2, fontsize=8.4)
    a2.set_xlim(0.2, 1.3)
    a2.set_xlabel("ICC de uma coleta e da média de sete dias", fontsize=8.8,
                  color=TINTA)
    titulo(a2, "B. Estabilidade entre dias")
    legenda(a2, handles=[
        Line2D([], [], color="white", marker="o", markeredgecolor=AZUL,
               markeredgewidth=1.5, linestyle="", label="uma coleta"),
        Line2D([], [], color=TEAL, linewidth=1.8, label="média de sete dias")],
        loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2)
    fig.tight_layout(w_pad=2.6)
    return salvar(fig, destino, "a1_psicometria.png")


GRUPOS = {
    "Favorável": ["Iceberg"],
    "Neutro": ["Superfície", "Submerso"],
    "De risco": ["Barbatana tubarão", "Iceberg invertido", "Everest invertido"],
}
CORES_GRUPO = {"Favorável": FAVORAVEL, "Neutro": NEUTRO, "De risco": RISCO}
MOMENTOS = [("Dia 1\nrepouso", 1), ("Sem\nHIIT", 4), ("Com\nHIIT", 3),
            ("Dia 7\nvéspera", 2)]


def fig_prevalencia_semana(destino: Path) -> Path:
    """Prevalência dos perfis no nível do grupo ao longo da semana."""
    from dados import PARSONS

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.4 / 2.54, 8.4 / 2.54),
                                 dpi=DPI,
                                 gridspec_kw={"width_ratios": [1.15, 1.1]})
    fig.patch.set_facecolor("white")
    aplicar(a1, grade="y")
    aplicar(a2, grade="x")

    xs = list(range(len(MOMENTOS)))
    base = [0.0] * len(MOMENTOS)
    for grupo, perfis in GRUPOS.items():
        vals = [sum(PARSONS[p][i] for p in perfis) for _, i in MOMENTOS]
        a1.bar(xs, vals, bottom=base, width=0.7, color=CORES_GRUPO[grupo],
               label=grupo, zorder=3, edgecolor="white", linewidth=1.6)
        for x, v, b in zip(xs, vals, base):
            a1.text(x, b + v / 2, vg(v) + "%", ha="center", va="center",
                    fontsize=6.8, color="white", fontweight="bold")
        base = [b + v for b, v in zip(base, vals)]
    a1.set_xticks(xs)
    a1.set_xticklabels([r for r, _ in MOMENTOS], fontsize=7.8)
    a1.set_ylim(0, 100)
    a1.set_yticks([0, 25, 50, 75, 100])
    a1.set_ylabel("Observações (%)", fontsize=8.8, color=TINTA)
    titulo(a1, "A. Composição do grupo")
    legenda(a1, loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=3)

    ordem = sorted(PARSONS, key=lambda k: PARSONS[k][1])
    ys = list(range(len(ordem)))
    altura = 0.36
    for desloc, indice, cor, rotulo in ((altura / 2, 1, AZUL, "Dia 1"),
                                        (-altura / 2, 2, CORAL, "Dia 7")):
        vals = [PARSONS[p][indice] for p in ordem]
        a2.barh([y + desloc for y in ys], vals, height=altura, color=cor,
                label=rotulo, zorder=3)
        for y, v in zip(ys, vals):
            a2.text(v + 1.5, y + desloc, vg(v) + "%", va="center",
                    fontsize=7.2, color=TINTA)
    a2.set_yticks(ys)
    a2.set_yticklabels(ordem, fontsize=8.4)
    a2.set_xlim(0, 78)
    a2.set_xlabel("Observações no perfil (%)", fontsize=8.8, color=TINTA)
    titulo(a2, "B. Os seis perfis, do dia 1 ao dia 7", tamanho=9.4)
    legenda(a2, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2)
    fig.tight_layout(w_pad=2.6)
    return salvar(fig, destino, "a1_prevalencia_semana.png")


def _erro_padrao(p: float, n: int) -> float:
    return 100 * sqrt((p / 100) * (1 - p / 100) / n)


def _suavizar(y: list[float]) -> list[float]:
    """Filtro binomial de três pontos, com pesos 1, 2 e 1."""
    s = list(y)
    for i in range(1, len(y) - 1):
        s[i] = (y[i - 1] + 2 * y[i] + y[i + 1]) / 4
    return s


def fig_sinal(destino: Path) -> Path:
    """Série diária do perfil, com a curva suavizada e a derivada."""
    from dados import DIAS, DIAS_HIIT, N_DIA, PERFIL_DIA
    ice = [PERFIL_DIA[d][0] for d in DIAS]
    per = [PERFIL_DIA[d][1] for d in DIAS]
    piso = sum(_erro_padrao(v, N_DIA[d]) for v, d in zip(ice, DIAS)) / len(DIAS)
    s_ice, s_per = _suavizar(ice), _suavizar(per)
    d_ice = [s_ice[i] - s_ice[i - 1] for i in range(1, len(DIAS))]

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(16.0 / 2.54, 12.4 / 2.54),
                                 dpi=DPI, sharex=True,
                                 gridspec_kw={"height_ratios": [1.5, 1]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        aplicar(ax, grade="ambos")
    # A faixa dos dias de HIIT fica só no painel A; no painel B ela se
    # confundiria com a banda de ruído, que usa a mesma tinta.
    for dia in DIAS_HIIT:
        a1.axvspan(dia - 0.4, dia + 0.4, color=FAIXA, zorder=1)

    for serie, suave, cor, marca, rotulo in (
            (ice, s_ice, FAVORAVEL, "o", "Perfil iceberg"),
            (per, s_per, RISCO, "s", "Humor perturbado")):
        a1.plot(DIAS, suave, color=cor, linewidth=2.0, zorder=3, label=rotulo)
        a1.plot(DIAS, serie, linestyle="none", marker=marca, markersize=5.0,
                markerfacecolor="white", markeredgecolor=cor,
                markeredgewidth=1.4, zorder=4)
    a1.axhline(50, color=TINTA_FRACA, linewidth=1.0, linestyle=(0, (5, 3)),
               zorder=2)
    a1.annotate("maioria do elenco", (7.34, 51.4), fontsize=7.4,
                color=TINTA_FRACA, va="bottom", ha="right")
    for serie, cor in ((ice, FAVORAVEL), (per, RISCO)):
        for i, dx, ali in ((0, 6, "left"), (6, -6, "right")):
            a1.annotate(vg(serie[i]) + "%", (DIAS[i], serie[i]),
                        textcoords="offset points",
                        xytext=(dx, 11 if serie[i] > 55 else -17), ha=ali,
                        fontsize=7.8, color=cor, fontweight="bold")
    a1.set_ylim(20, 90)
    a1.set_xlim(0.55, 7.45)
    a1.set_ylabel("Atletas (%)", fontsize=8.8, color=TINTA)
    titulo(a1, "A. Predominância diária dos perfis", tamanho=9.6)
    legenda(a1, loc="lower left")

    xs = [d + 0.5 for d in DIAS[:-1]]
    for x, v in zip(xs, d_ice):
        acima = abs(v) > piso
        cor = RISCO if acima else "#B4B4B0"
        a2.bar(x, v, width=0.55, color=cor, zorder=3)
        if acima:
            a2.text(x, v - 1.6, sg(v), ha="center", va="top", fontsize=7.8,
                    color=cor, fontweight="bold")
    a2.axhspan(-piso, piso, color=FAIXA, zorder=2)
    a2.axhline(0, color=TINTA, linewidth=1.0, zorder=4)
    a2.annotate(f"ruído amostral ±{vg(piso)} p.p.", (7.34, piso + 1.0),
                fontsize=7.4, color=TINTA_FRACA, va="bottom", ha="right")
    a2.set_ylim(-25, 14)
    a2.set_xticks(DIAS)
    a2.set_xlabel("Dia do microciclo", fontsize=8.8, color=TINTA)
    a2.set_ylabel("Variação (p.p./dia)", fontsize=8.8, color=TINTA)
    titulo(a2, "B. Variação diária do perfil iceberg", tamanho=9.6)
    fig.tight_layout(h_pad=1.6)
    return salvar(fig, destino, "a1_sinal.png")


# ══════════════════════════════════════════════════════════ Artigo 2 ═══
def fig_sessoes(destino: Path) -> Path:
    """O estímulo externo cai enquanto o custo interno sobe, ao longo das três
    sessões equivalentes de HIIT."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.4 / 2.54, 8.0 / 2.54),
                                 dpi=DPI)
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        aplicar(ax, grade="ambos")

    xs = [1, 2, 3]
    entregue = {"FC de pico": (F.ESTIMULO["FC de pico (bpm)"][:3], AZUL, "o"),
                "Esforço percebido": (F.ESTIMULO["PSE final (0 a 10)"][:3],
                                      CORAL, "s")}
    for nome, (serie, cor, marca) in entregue.items():
        rel = [100 * v / serie[0] for v in serie]
        a1.plot(xs, rel, color=cor, marker=marca, markersize=6.0,
                linewidth=2.0, zorder=3, markeredgecolor="white",
                markeredgewidth=0.8, label=nome)
        for x, v, bruto in zip(xs, rel, serie):
            a1.annotate(vg(bruto, 0 if float(bruto).is_integer() else 1),
                        (x, v), textcoords="offset points",
                        xytext=(0, 10 if cor == CORAL else -16), ha="center",
                        fontsize=7.8, color=cor, fontweight="bold")
    a1.axhline(100, color=TINTA_FRACA, linewidth=1.0, linestyle=(0, (5, 3)),
               zorder=2)
    a1.set_xticks(xs)
    a1.set_xticklabels(["S1 (dia 2)", "S2 (dia 4)", "S3 (dia 7)"], fontsize=8.2)
    a1.set_xlim(0.7, 3.3)
    a1.set_ylim(94, 111)
    a1.set_ylabel("Percentual da primeira sessão", fontsize=8.8, color=TINTA)
    titulo(a1, "A. Estímulo entregue e esforço percebido", tamanho=9.4)
    legenda(a1, loc="upper left")

    chaves = ["PTH (TMD)", "Fadiga (BRUMS)", "Fadiga física", "Sonolência",
              "Vigor", "TQR (recuperação)"]
    marcas = ["o", "s", "^", "D", "v", "P"]
    tracado = []
    for nome, marca, cor in zip(chaves, marcas, E.PALETA):
        s1, s2, s3, incl, _, _ = F.SESSOES[nome]
        rel = [100 * v / s1 for v in (s1, s2, s3)]
        a2.plot(xs, rel, color=cor, marker=marca, markersize=5.0,
                linewidth=1.8, zorder=3, markeredgecolor="white",
                markeredgewidth=0.7, label=f"{nome} ({sg(incl, 2)}/sessão)")
        tracado.append(rel[2])
    a2.axhline(100, color=TINTA_FRACA, linewidth=1.0, linestyle=(0, (5, 3)),
               zorder=2)
    a2.set_xticks(xs)
    a2.set_xticklabels(["S1", "S2", "S3"], fontsize=8.2)
    a2.set_xlim(0.85, 3.15)
    a2.set_xlabel("Sessão de HIIT", fontsize=8.8, color=TINTA)
    a2.set_ylabel("Percentual da primeira sessão", fontsize=8.8, color=TINTA)
    titulo(a2, "B. Custo psicológico por sessão", tamanho=9.4)
    legenda(a2, loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2,
            fontsize=6.8)
    fig.tight_layout(w_pad=2.6)
    return salvar(fig, destino, "a2_sessoes.png")


def fig_mdc(destino: Path) -> Path:
    """Quem de fato mudou, e quanto a noite devolve."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(17.4 / 2.54, 7.4 / 2.54),
                                 dpi=DPI,
                                 gridspec_kw={"width_ratios": [1.3, 1]})
    fig.patch.set_facecolor("white")
    for ax in (a1, a2):
        aplicar(ax, grade="x")

    ordem = sorted(F.MDC, key=lambda k: F.MDC[k][3])
    ys = list(range(len(ordem)))
    altura = 0.36
    for desloc, indice, cor, rotulo in ((altura / 2, 1, BARRA_A, "Na sessão"),
                                        (-altura / 2, 3, BARRA_B, "Na semana")):
        vals = [F.MDC[n][indice] for n in ordem]
        a1.barh([y + desloc for y in ys], vals, height=altura, color=cor,
                label=rotulo, zorder=3)
        for y, v in zip(ys, vals):
            a1.text(v + 1.6, y + desloc, f"{v}%", va="center", fontsize=7.2,
                    color=TINTA)
    a1.set_yticks(ys)
    a1.set_yticklabels(ordem, fontsize=8.4)
    a1.set_xlim(0, 80)
    a1.set_xlabel("Atletas acima do menor valor detectável (%)", fontsize=8.8,
                  color=TINTA)
    titulo(a1, "A. Mudança acima do erro de medida", tamanho=9.4)
    legenda(a1, loc="upper center", bbox_to_anchor=(0.5, -0.20), ncol=2)

    ordem2 = sorted(F.RECUPERACAO, key=lambda k: F.RECUPERACAO[k][0])
    for y, nome in enumerate(ordem2):
        rec, _ = F.RECUPERACAO[nome]
        cor = TEAL if rec >= 100 else CORAL
        a2.barh(y, rec, height=0.55, color=cor, zorder=3)
        a2.text(rec + 2.4, y, vg(rec) + "%", va="center", fontsize=7.8,
                color=TINTA)
    a2.axvline(100, color=TINTA, linewidth=1.1, linestyle=(0, (5, 3)), zorder=4)
    a2.annotate("recuperação completa", (98, -0.46), fontsize=7.4, color=TINTA,
                ha="right")
    a2.set_yticks(range(len(ordem2)))
    a2.set_yticklabels(ordem2, fontsize=8.4)
    a2.set_xlim(0, 152)
    a2.set_xlabel("Recuperação noturna média (%)", fontsize=8.8, color=TINTA)
    titulo(a2, "B. Quanto a noite devolve")
    fig.tight_layout(w_pad=2.4)
    return salvar(fig, destino, "a2_mdc.png")


def gerar_artigo1(destino: Path) -> list[Path]:
    print("figuras do Artigo 1:")
    return [fig_distribuicao(destino), fig_psicometria(destino),
            fig_prevalencia_semana(destino), fig_sinal(destino)]


def gerar_artigo2(destino: Path) -> list[Path]:
    print("figuras do Artigo 2:")
    return [fig_sessoes(destino), fig_mdc(destino)]


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "data/figartigos")
    gerar_artigo1(d)
    gerar_artigo2(d)
