"""Figuras analíticas e 3D (4K) da revisão sistemática do humor no formato dos artigos modelo.
Grava em figuras/ e os números citados no texto em figuras/ijrs_numeros.json.

    python3 figs_rs_ijerph.py
"""
import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats as sst

sys.path.insert(0, "/home/user/corrigidos/revisada")
sys.path.insert(0, "/home/user/corrigidos/modelo_mdpi")
import modelos as M  # noqa: E402
from modelos import plt, tom, br  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402

os.environ["CITE"] = "autor"
os.environ["CITADOS_FILE"] = "citados_fig_rs.json"
from refs import R  # noqa: E402

AQ = Path(__file__).parent
sys.path.insert(0, str(AQ))
import rs_dados as RD  # noqa: E402

FIG = AQ / "figuras"
K4 = 3900
EST = [e for e in RD.INC if e["id"] not in RD.MESMA_AMOSTRA]
QE = {e["id"]: e for e in RD.INC}
K = RD.CHAVE
DIRS = [("Efeito ou associação", "Efeito ou associação relatado", "#1d6fa3"), ("Misto", "Resultado misto", "#ef9a37"),
        ("Sem efeito", "Sem efeito ou associação", "#e1574a"), ("Descritivo", "Descritivo, sem teste", "#8fa1b3"),
        ("Não determinável", "Não determinável", "#cfd6de")]
TIPOS = [("Encorajamento verbal", ["H25", "H29", "N5"], "#1d6fa3"), ("Feedback", ["H22", "H23"], "#a3174a"),
         ("Programas psicológicos", ["H10", "N8"], "#6aaa3a"), ("Música", ["H14", "H24"], "#3aa8d8"),
         ("Nutrição e suplementação", ["H15", "H28"], "#ef9a37"), ("Informação sobre o esforço", ["H4"], "#7b52c4")]
GRUPOS = [("Competição e resultado do jogo", ["H2", "H5", "H13", "H21", "H31", "H32", "U049"]),
          ("Carga, recuperação e marcadores biológicos", ["H3", "H4", "H9", "H15", "H17", "H34", "N1", "U150"]),
          ("Variáveis psicológicas e contexto", ["H11", "H14", "H20", "H21", "H27", "H28", "H30", "H34", "N2", "N3"]),
          ("Intervenções verbais e psicológicas", ["H4", "H10", "H14", "H22", "H23", "H25", "H29", "N5", "N8"]),
          ("Nutrição e suplementação", ["H15", "H28"]),
          ("Ciclo menstrual e horário do dia", ["H19", "H24", "N4", "O1"])]
OUT = {}


def salvar4k(fig, nome):
    fig.savefig(FIG / nome, dpi=max(250, int(np.ceil(K4 / fig.get_size_inches()[0]))), facecolor="white")
    plt.close(fig)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def dirc(i):
    return RD.DIR_CURTA[QE[i]["direcao"]]


def limpo(ax, grade="x"):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color("#9aa3ad")
    ax.spines["bottom"].set_color("#9aa3ad")
    ax.tick_params(length=0, colors=M.TXT, labelsize=12)
    if grade:
        getattr(ax, f"{grade}axis").grid(True, color="#e6e9ee", lw=0.9, zorder=0)
    ax.set_axisbelow(True)


def bola(ax, x, y, s, c, z=6):
    ax.scatter([x], [y], s=s, color=c, edgecolor=tom(c, -0.4), lw=1.2, zorder=z)
    ax.scatter([x], [y], s=s * 0.35, color=tom(c, 0.55), lw=0, zorder=z + 0.1, alpha=0.75)


def seg3d(ax, x0, w, y, h, cor, dx, dy, lado=True):
    n = 24
    for i in range(n):
        a, b = x0 + w * i / n, x0 + w * (i + 1) / n
        ax.add_patch(Rectangle((a, y), b - a, h, color=tom(cor, -0.22 + 0.30 * i / n), lw=0, zorder=3))
    ax.add_patch(Polygon([(x0, y + h), (x0 + dx, y + h + dy), (x0 + w + dx, y + h + dy), (x0 + w, y + h)],
                         color=tom(cor, 0.35), lw=0, zorder=3))
    if lado:
        ax.add_patch(Polygon([(x0 + w, y), (x0 + w + dx, y + dy), (x0 + w + dx, y + h + dy), (x0 + w, y + h)],
                             color=tom(cor, -0.45), lw=0, zorder=3))


# ------------------------------------------------------------------ pizzas 3D
def pizzas():
    c1 = Counter(RD.DIR_CURTA[e["direcao"]] for e in EST)
    v1 = [c1.get(k, 0) for k, _, _ in DIRS]
    ids = [i for _, g, _ in TIPOS for i in g]
    c2 = Counter(dirc(i) for i in ids)
    v2 = [c2.get(k, 0) for k, _, _ in DIRS]
    fig, axs = plt.subplots(1, 2, figsize=(16, 7.2), facecolor="white")
    for ax, v, tit, tot in ((axs[0], v1, f"(A) Direção dos achados nos {len(EST)} estudos", len(EST)),
                            (axs[1], v2, f"(B) Direção dos achados nas {len(ids)} intervenções", len(ids))):
        vv = [(x, k, c) for x, (k, r, c) in zip(v, DIRS) if x]
        M.pizza3d(ax, [x for x, _, _ in vv], [c for _, _, c in vv], sy=0.55, esp=0.2, min_pct=6, fs=14, destaque=0.05)
        ax.set_title(tit, loc="left", fontsize=17, fontweight="bold", color=M.TXT, pad=4)
        ax.set_ylim(-1.75, 0.85)
        for i, (x, (k, r, c)) in enumerate(zip(v, DIRS)):
            yy = -1.02 - 0.15 * i
            ax.add_patch(Rectangle((-1.12, yy - 0.05), 0.12, 0.1, color=c, ec=tom(c, -0.3)))
            ax.text(-0.94, yy, f"{r}: {x} ({br(100 * x / tot, 1)}%)", va="center", fontsize=13, color=M.TXT)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.02, wspace=0.05)
    salvar4k(fig, "ijrs_direcao_pizza3d.png")
    OUT["dir_est"] = dict(zip([k for k, _, _ in DIRS], v1))
    OUT["dir_int"] = dict(zip([k for k, _, _ in DIRS], v2))


# ------------------------------------------------------------------ barras 3D: grupo de variáveis × direção
def grupos3d():
    tab = []
    for g, ids in GRUPOS:
        ids = [i for i in ids if i not in RD.MESMA_AMOSTRA]
        c = Counter(dirc(i) for i in ids)
        tab.append((g, [c.get(k, 0) for k, _, _ in DIRS]))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 7.0), facecolor="white",
                                 gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.08})
    k = len(tab)
    for ax, rel in ((a1, False), (a2, True)):
        xmax = 100 if rel else 11
        dx, dy = xmax * 0.012, 0.13
        for i, (g, v) in enumerate(tab):
            y = k - 1 - i
            v = np.array(v, float)
            vals = 100 * v / v.sum() if rel else v
            esq = 0
            ult = max(j for j, w in enumerate(vals) if w > 0)
            for j, ((_, _, cor), w, n) in enumerate(zip(DIRS, vals, v)):
                if w <= 0:
                    continue
                seg3d(ax, esq, w, y - 0.3, 0.6, cor, dx, dy, lado=(j == ult))
                if w >= (8 if rel else 0.6):
                    ax.text(esq + w / 2, y, f"{br(w, 0)}%" if rel else str(int(n)), ha="center", va="center",
                            fontsize=13, fontweight="bold", zorder=6,
                            color="white" if cor not in ("#cfd6de", "#8fa1b3") else M.TXT)
                esq += w
            if not rel:
                ax.text(esq + dx + 0.15, y + 0.05, str(int(v.sum())), va="center", fontsize=14, fontweight="bold",
                        color=M.TXT)
        ax.set_xlim(0, xmax + (0 if rel else 0.9))
        ax.set_ylim(-0.7, k - 0.2)
        limpo(ax, "x")
        ax.spines["left"].set_visible(False)
        if rel:
            ax.set_xticks(range(0, 101, 20))
            ax.set_xticklabels([f"{t}%" for t in range(0, 101, 20)])
            ax.set_yticks([])
            ax.set_xlabel("Proporção dos estudos do grupo", fontsize=14, color="#3b4656")
            ax.set_title("(B) Proporção por direção do achado", loc="left", fontsize=18, fontweight="bold",
                         color=M.TXT, pad=12)
        else:
            ax.set_xticks(range(0, 11, 2))
            ax.set_yticks(range(k))
            ax.set_yticklabels([g.replace(", ", ",\n", 1) if len(g) > 28 else g for g, _ in tab][::-1], fontsize=13)
            ax.set_xlabel("Número de estudos (um estudo pode compor mais de um grupo)", fontsize=14, color="#3b4656")
            ax.set_title("(A) Estudos por grupo de variáveis e direção do achado", loc="left", fontsize=18,
                         fontweight="bold", color=M.TXT, pad=12)
    hs = [plt.Rectangle((0, 0), 1, 1, color=c, ec=tom(c, -0.3)) for _, _, c in DIRS]
    fig.legend(hs, [r for _, r, _ in DIRS], loc="lower center", ncol=5, frameon=False, fontsize=13.5,
               bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(left=0.2, right=0.985, top=0.9, bottom=0.17)
    salvar4k(fig, "ijrs_grupos_direcao.png")
    OUT["grupos"] = {g: v for g, v in tab}


# ------------------------------------------------------------------ análise das intervenções
def intervencoes():
    EFE = ("Efeito ou associação", "Misto")
    fig = plt.figure(figsize=(18, 7.8), facecolor="white")
    bx = fig.add_axes([0.06, 0.15, 0.36, 0.67])
    pts = []
    for t, g, c in TIPOS:
        for i in g:
            e = QE[i]
            n = e["n"] if isinstance(e["n"], int) else None
            pts.append((i, t, c, n, e["qualidade"]["pontuacao"]))
    rng = np.random.default_rng(3)
    for y0, y1, cor in ((-0.5, 2.5, "#fdecea"), (2.5, 4.5, "#fff4e2"), (4.5, 6.5, "#e8f4ec")):
        bx.axhspan(y0, y1, color=cor, zorder=0)
    for i, t, c, n, q in pts:
        x = np.log10(n) if n else np.log10(4.5)
        y = q + rng.uniform(-0.18, 0.18)
        bola(bx, x, y, 420, c, z=5)
        bx.text(x + 0.035, y + 0.22, R.autor(K[i]), fontsize=9.5, color=tom(c, -0.45), zorder=7)
    tk = [5, 10, 20, 50, 100]
    bx.set_xticks(np.log10(tk))
    bx.set_xticklabels([str(t) for t in tk])
    bx.set_xlim(np.log10(4), np.log10(160))
    bx.set_ylim(-0.5, 6.5)
    bx.set_yticks(range(7))
    limpo(bx, None)
    bx.set_xlabel("Participantes (escala logarítmica)", fontsize=13, color="#3b4656")
    bx.set_ylabel("Pontuação de qualidade (0 a 6)", fontsize=13, color="#3b4656")
    bx.set_title("(A) Tamanho amostral e qualidade de cada intervenção", loc="left", fontsize=17, fontweight="bold",
                 color=M.TXT, pad=12)
    nn = [n for _, _, _, n, _ in pts if n]
    qq = [q for _, _, _, n, q in pts if n]
    rho, p = sst.spearmanr(nn, qq)
    hs = [plt.Line2D([], [], marker="o", ls="", ms=12, color=c) for _, _, c in TIPOS]
    bx.legend(hs, [t for t, _, _ in TIPOS], loc="upper left", fontsize=10, frameon=True, framealpha=0.9, ncol=2)
    cx = fig.add_axes([0.52, 0.16, 0.36, 0.66])
    lin = []
    for t, g, c in TIPOS:
        kk = sum(dirc(i) in EFE for i in g)
        lin.append((t, c, kk, len(g)) + wilson(kk, len(g)))
    ids = [i for _, g, _ in TIPOS for i in g]
    tk_ = sum(dirc(i) in EFE for i in ids)
    pt, lo, hi = wilson(tk_, len(ids))
    cx.axvspan(100 * lo, 100 * hi, color="#e9edf2", zorder=0)
    cx.axvline(100 * pt, color="#17304f", ls=(0, (4, 3)), lw=1.4, zorder=1)
    cx.text(100 * pt, len(lin) - 0.35, f"conjunto: {tk_}/{len(ids)} ({br(100 * pt, 0)}%)", ha="center", fontsize=11.5,
            color="#17304f")
    for i, (t, c, kk, n, p_, l_, h_) in enumerate(lin):
        y = len(lin) - 1 - i
        cx.plot([100 * l_, 100 * h_], [y, y], color=tom(c, -0.2), lw=4, solid_capstyle="round", zorder=3, alpha=0.75)
        cx.scatter([100 * p_], [y], s=140 + 120 * n, color=c, edgecolor=tom(c, -0.4), lw=1.5, zorder=5)
        cx.text(103, y, f"{kk}/{n} com efeito", va="center", fontsize=12, color=M.TXT)
    cx.set_yticks(range(len(lin)))
    cx.set_yticklabels([t for t, *_ in lin][::-1], fontsize=12.5)
    cx.set_xlim(-2, 125)
    cx.set_xticks(range(0, 101, 20))
    cx.set_xticklabels([f"{t}%" for t in range(0, 101, 20)])
    cx.set_ylim(-0.6, len(lin) - 0.1)
    limpo(cx, "x")
    cx.spines["left"].set_visible(False)
    cx.set_xlabel("Proporção com efeito total ou parcial relatado pelos autores (barra: IC 95% de Wilson)", fontsize=12.5, color="#3b4656")
    cx.set_title("(B) Proporção de intervenções com efeito, por tipo", loc="left", fontsize=17, fontweight="bold",
                 color=M.TXT, pad=30)
    salvar4k(fig, "ijrs_intervencoes_analise.png")
    OUT["int"] = {"rho_nq": round(float(rho), 2), "p_nq": float(p), "n_md": float(np.median(nn)),
                  "n_min": int(min(nn)), "n_max": int(max(nn)),
                  "tot": [tk_, len(ids), round(100 * lo), round(100 * hi)],
                  "tipos": {t: [kk, n] for t, c, kk, n, *_ in lin}}


# ------------------------------------------------------------------ análise da qualidade
QROT = {"q1": "Q1. Objetivo e população definidos", "q2": "Q2. Amostra descrita",
        "q3": "Q3. Instrumento validado e nomeado", "q4": "Q4. Momento da medida declarado",
        "q5": "Q5. Comparador, controle ou ajuste", "q6": "Q6. Análise estatística adequada"}


def qualidade():
    fig = plt.figure(figsize=(18, 7.8), facecolor="white")
    ax = fig.add_axes([0.2, 0.14, 0.36, 0.7])
    est = []
    for q, rot in QROT.items():
        c = Counter(e["qualidade"][q] for e in EST)
        est.append((rot, c["sim"], c["incerto"], c["não"]) + wilson(c["sim"], len(EST)))
    est.sort(key=lambda t: t[4])
    for i, (rot, s_, inc, nao, p_, lo, hi) in enumerate(est):
        c = "#1b7f3b" if p_ >= 0.75 else ("#6aaa3a" if p_ >= 0.5 else ("#ef9a37" if p_ >= 0.25 else "#e1574a"))
        ax.plot([100 * lo, 100 * hi], [i, i], color=tom(c, -0.15), lw=5, solid_capstyle="round", alpha=0.55, zorder=2)
        ax.plot([0, 100 * p_], [i, i], color="#d5dae1", lw=1.2, zorder=1)
        ax.scatter([100 * p_], [i], s=560, color=c, edgecolor=tom(c, -0.4), lw=1.6, zorder=4)
        ax.text(100 * p_, i, str(s_), ha="center", va="center", fontsize=11.5, fontweight="bold", color="white",
                zorder=5)
        ax.text(104, i, f"{br(100 * p_, 0)}% [{br(100 * lo, 0)}; {br(100 * hi, 0)}]; {inc} incerto, {nao} não",
                va="center", fontsize=11.5, color=M.TXT)
    ax.set_yticks(range(len(est)))
    ax.set_yticklabels([t[0] for t in est], fontsize=12.5)
    ax.set_xlim(0, 150)
    ax.set_xticks(range(0, 101, 20))
    ax.set_xticklabels([f"{t}%" for t in range(0, 101, 20)])
    limpo(ax, "x")
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(f"Estudos que atendem ao item (n = {len(EST)}; ponto: número de estudos; barra: IC 95%)",
                  fontsize=12.5, color="#3b4656")
    ax.set_title("(A) Atendimento a cada item de qualidade", loc="left", fontsize=17, fontweight="bold",
                 color=M.TXT, pad=10)
    bx = fig.add_axes([0.66, 0.14, 0.32, 0.7])
    anos = np.array([RD.NORM[e["id"]][0] for e in EST])
    esc = np.array([e["qualidade"]["pontuacao"] for e in EST])
    rho, p = sst.spearmanr(anos, esc)
    b1, b0 = np.polyfit(anos, esc, 1)
    xs = np.linspace(anos.min(), anos.max(), 50)
    rng = np.random.default_rng(11)
    boot = []
    for _ in range(2000):
        ii = rng.integers(0, len(anos), len(anos))
        if len(set(anos[ii])) > 1:
            bb1, bb0 = np.polyfit(anos[ii], esc[ii], 1)
            boot.append(bb0 + bb1 * xs)
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    for y0, y1, cor in ((-0.5, 2.5, "#fdecea"), (2.5, 4.5, "#fff4e2"), (4.5, 6.5, "#e8f4ec")):
        bx.axhspan(y0, y1, color=cor, zorder=0)
    bx.fill_between(xs, lo, hi, color="#1d6fa3", alpha=0.15, zorder=1)
    bx.plot(xs, b0 + b1 * xs, color="#1d6fa3", lw=2.4, zorder=2)
    for e, a, s_, j in zip(EST, anos, esc, rng.uniform(-0.2, 0.2, len(EST))):
        d = RD.DIR_CURTA[e["direcao"]]
        c = next(cc for k, _, cc in DIRS if k == d)
        n = e["n"] if isinstance(e["n"], int) else None
        bola(bx, a + j, s_ + rng.uniform(-0.15, 0.15), 70 + (22 * np.sqrt(n) if n else 0), c, z=5)
    bx.set_xlim(anos.min() - 1, anos.max() + 1)
    bx.set_xticks(range(2008, 2027, 3))
    bx.set_ylim(-0.5, 6.5)
    bx.set_yticks(range(7))
    limpo(bx, None)
    bx.text(anos.min() - 0.6, 5.5, "alta", fontsize=11, color="#1b7f3b", style="italic")
    bx.text(anos.min() - 0.6, 3.5, "moderada", fontsize=11, color="#b8740f", style="italic")
    bx.text(anos.min() - 0.6, 1.5, "baixa", fontsize=11, color="#c0392b", style="italic")
    bx.set_xlabel("Ano de publicação", fontsize=13, color="#3b4656")
    bx.set_ylabel("Pontuação de qualidade (0 a 6)", fontsize=13, color="#3b4656")
    ptx = "p < 0,001" if p < 0.001 else f"p = {br(p, 3)}"
    bx.set_title("(B) Pontuação de qualidade ao longo do tempo", loc="left", fontsize=17, fontweight="bold",
                 color=M.TXT, pad=30)
    bx.text(0, 1.03, f"Spearman: ρ = {br(rho, 2)}; {ptx}; reta com IC 95% (bootstrap)", transform=bx.transAxes,
            fontsize=12, style="italic", color="#3b4656")
    hs = [plt.Line2D([], [], marker="o", ls="", ms=12, color=c) for _, _, c in DIRS]
    bx.legend(hs, [r for _, r, _ in DIRS], loc="lower right", frameon=True, fontsize=10, framealpha=0.9)
    salvar4k(fig, "ijrs_qualidade_analise.png")
    OUT["qual"] = {"rho": round(float(rho), 2), "p": float(p), "md": float(np.median(esc)),
                   "itens": {t[0]: [t[1], round(100 * t[5]), round(100 * t[6])] for t in est}}


if __name__ == "__main__":
    pizzas()
    grupos3d()
    intervencoes()
    qualidade()
    json.dump(OUT, open(FIG / "ijrs_numeros.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(OUT, ensure_ascii=False))
