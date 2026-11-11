"""Figura da qualidade metodológica dos estudos de intervenção (EPHPP)."""
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).parent))
from qualidade_ephpp import Q, global_
from intervencoes_detalhe import EST, TIPOS

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "qualidade_ephpp.png"
fam = {f.name for f in fm.fontManager.ttflist}
plt.rcParams["font.family"] = "Liberation Serif" if "Liberation Serif" in fam else "DejaVu Serif"
plt.rcParams["font.size"] = 9
COR = {"Forte": "#4C9A6A", "Moderado": "#E3B448", "Fraco": "#C8553D"}
MAPA = {"F": "Forte", "M": "Moderado", "Fr": "Fraco"}
GL = {"Forte": "Forte", "Moderada": "Moderado", "Fraca": "Fraco"}
qs = [q for q in Q.values() if q]
comps = [("sel", "Seleção"), ("del_", "Delineamento"), ("conf", "Fatores de confusão"), ("ceg", "Cegamento"),
         ("col", "Coleta de dados"), ("perd", "Perdas e desistências")]


def barras(ax, linhas, rotulos, xmax, titulo, xlabel):
    y = list(range(len(linhas)))[::-1]
    for yi, c in zip(y, linhas):
        esq = 0
        for cat in ("Forte", "Moderado", "Fraco"):
            v = c.get(cat, 0)
            if v:
                ax.barh(yi, v, left=esq, color=COR[cat], edgecolor="white", height=0.62)
                ax.text(esq + v / 2, yi, str(v), ha="center", va="center", fontsize=8.5, fontweight="bold",
                        color="black" if cat == "Moderado" else "white")
            esq += v
    ax.set_yticks(y)
    ax.set_yticklabels(rotulos)
    ax.set_xlim(0, xmax)
    ax.set_xlabel(xlabel)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title(titulo, loc="left", fontsize=10, fontweight="bold")


fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.25, 1]})
lin = [Counter(MAPA[q[k]] for q in qs) for k, _ in comps] + [Counter(GL[global_(q)] for q in qs)]
barras(a1, lin, [c[1] for c in comps] + ["Qualidade global"], 23, "(A) Componentes do EPHPP",
       "Número de estudos (n = 23)")
g = {n: global_(q) for n, q in Q.items() if q}
rot = {"Treino de habilidades psicológicas": "Treino de habilidades\npsicológicas",
       "Feedback e ação do treinador": "Feedback e ação\ndo treinador", "Nutrição e suplementação": "Nutrição e\nsuplementação"}
lin2 = [Counter(GL[g[n]] for n in g if EST[n]["tipo"] == t) for t in TIPOS]
barras(a2, lin2, [rot.get(t, t) for t in TIPOS], 10.5, "(B) Qualidade global por tipo de intervenção",
       "Número de estudos")
fig.legend(handles=[Patch(color=COR[k], label=k) for k in COR], loc="lower center", ncol=3, frameon=False,
           bbox_to_anchor=(0.5, -0.01))
plt.tight_layout(rect=(0, 0.07, 1, 1))
plt.savefig(SAIDA, dpi=300)
print("ok", SAIDA)
