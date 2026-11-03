"""Figura 10 simplificada (estilo do artigo modelo): número de estudos de cada domínio por período.

    python3 figs_periodos.py   -> figuras/Figura_periodos_dominios.png (4K)
"""
import numpy as np
import quadro_sintese as Q
from figs_nossos import FIG, M, plt, tom, aparar

PER = [("Até 2015", 1994, 2015), ("2016 a 2020", 2016, 2020), ("2021 a 2026", 2021, 2026)]
CORP = ["#b9c4d0", "#6f9bc3", "#1f4e79"]


def figura():
    c = Q.carregar()
    doms = sorted(Q.DOM, key=lambda d: -int(c[d].sum()))
    val = [[int(c[(c.Ano >= lo) & (c.Ano <= hi)][d].sum()) for _, lo, hi in PER] for d in doms]
    tot = [len(c[(c.Ano >= lo) & (c.Ano <= hi)]) for _, lo, hi in PER]
    fig, ax = plt.subplots(figsize=(11, 5.6), facecolor="white")
    x = np.arange(len(doms))
    w = 0.26
    for j, (rot, _, _) in enumerate(PER):
        xs = x + (j - 1) * w
        vs = [v[j] for v in val]
        ax.bar(xs, vs, w * 0.92, color=CORP[j], ec=tom(CORP[j], -0.25), lw=0.6, zorder=3,
               label=f"{rot} ({tot[j]} estudos)")
        for xi, vi in zip(xs, vs):
            ax.text(xi, vi + 0.6, str(vi), ha="center", va="bottom", fontsize=9.5, color=M.TXT, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([M.CAT_QUEBRA[d] for d in doms], fontsize=10)
    ax.set_ylabel("Número de estudos", fontsize=12)
    ax.set_ylim(0, max(max(v) for v in val) * 1.15)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.yaxis.grid(True, color="#e3e7ec", lw=0.9, zorder=0)
    ax.tick_params(length=0, colors=M.TXT)
    ax.legend(frameon=False, fontsize=10.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "Figura_periodos_dominios.png", dpi=400, facecolor="white")
    plt.close(fig)
    aparar("Figura_periodos_dominios.png")
    return doms, val, tot


if __name__ == "__main__":
    print(figura())
