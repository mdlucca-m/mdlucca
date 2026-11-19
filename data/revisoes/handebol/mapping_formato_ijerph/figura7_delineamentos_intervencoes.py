"""Figura 7 do mapping: (A) delineamentos dos 199 estudos (Quadro A1); (B) mapa de evidências das intervenções.

    python3 figura7_delineamentos_intervencoes.py <apA.json> <pasta_saida>
"""
import collections
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

import dominios_intervencoes as D
import intervencoes_detalhe as I

AP, OUT = Path(sys.argv[1]), Path(sys.argv[2])
plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 11})

# ---------- 7A
a = json.load(open(AP, encoding="utf-8"))
c = collections.Counter(x["Delineamento e contexto"].split(";")[0].strip() for x in a)
outros = c["Qualitativo"] + c["Estudo de caso"] + c["Validação psicométrica"] + c["Métodos mistos"]
barras = [("Observacional sem desenho especificado", c["Observacional (sem desenho especificado)"], "#1F3B57"),
          ("Transversal", c["Transversal"], "#2F6690"),
          ("Coorte ou longitudinal", c["Coorte ou longitudinal"], "#5B8DB8"),
          ("Quase-experimental", c["Quase-experimental"], "#1B7F4B"),
          ("Ensaio clínico randomizado", c["Ensaio clínico randomizado"], "#2BA36B"),
          ("Experimental cruzado", c["Experimental cruzado (crossover)"], "#6CC59A"),
          ("Qualitativo, caso, validação ou misto", outros, "#9A8C6E"),
          ("Sem informação", c["s.i."], "#A0A7AE")]
assert sum(b[1] for b in barras) == len(a) == 199
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=200)
y = list(range(len(barras)))[::-1]
ax.barh(y, [b[1] for b in barras], color=[b[2] for b in barras], height=0.62)
for yy, (r, v, _) in zip(y, barras):
    ax.text(v + 1.2, yy, f"{v} ({v / 199 * 100:.1f}%)".replace(".", ","), va="center", fontsize=10.5)
ax.set_yticks(y, [b[0] for b in barras])
ax.set_xlim(0, 100)
ax.set_xlabel("Número de estudos")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
obs = sum(b[1] for b in barras[:3]); exp = sum(b[1] for b in barras[3:6])
fig.suptitle(f"(A) Delineamentos dos 199 estudos: {obs} observacionais e {exp} experimentais", fontsize=12.5,
             fontweight="bold", x=0.01, ha="left")
fig.tight_layout()
fig.savefig(OUT / "figura7a_delineamentos.png")
print("7A", obs, exp, outros, c["s.i."])

# ---------- 7B
E = I.EST
ROT = {"Treino de habilidades psicológicas": "Treino de\nhabilidades\npsicológicas", "Feedback e ação do treinador":
       "Feedback e\nação do\ntreinador", "Prática de handebol": "Prática de\nhandebol", "Recuperação e sono":
       "Recuperação\ne sono", "Nutrição e suplementação": "Nutrição e\nsuplementação", "Música": "Música"}
linhas = D.DOMINIOS + [("", "Apenas desempenho\n(sem desfecho psicológico)", None)]
cmap = LinearSegmentedColormap.from_list("v", ["#E8F3EC", "#1B7F4B"])
rand = lambda k: bool(re.search(r"andomiz|ordem aleatória", E[k]["mod"]))
fig, ax = plt.subplots(figsize=(12, 7.4), dpi=200)
nl, nc = len(linhas), len(I.TIPOS)
vazias = 0
for i, (s, nome, _) in enumerate(linhas):
    yy = nl - 1 - i
    for j, t in enumerate(I.TIPOS):
        ks = [k for k in E if E[k]["tipo"] == t and (s in D.DOM[k] if s else not D.DOM[k])]
        if s and not ks:
            vazias += 1
        if ks:
            p = sum(E[k]["dir"] == "Efeito" for k in ks) / len(ks)
            cor = cmap(0.15 + 0.85 * p)
            r = any(rand(k) for k in ks)
            ax.add_patch(Rectangle((j, yy), 1, 1, facecolor=cor, edgecolor="white", linewidth=1.5, zorder=1))
            if r:
                ax.add_patch(Rectangle((j + .04, yy + .04), .92, .92, facecolor="none", edgecolor="#111111",
                                       linewidth=2.2, zorder=3))
            ef = sum(E[k]["dir"] == "Efeito" for k in ks)
            ax.text(j + .5, yy + .5, f"{len(ks)}\n({ef} com efeito)", ha="center", va="center", fontsize=9.5,
                    color="white" if p >= .5 else "#1a1a1a", fontweight="bold", zorder=4)
        else:
            ax.add_patch(Rectangle((j, yy), 1, 1, facecolor="#F4F6F9", edgecolor="white", linewidth=1.5))
            if s:
                ax.text(j + .5, yy + .5, "0", ha="center", va="center", fontsize=9.5, color="#B03A2E")
ax.axhline(1, color="#555555", linewidth=1.2, linestyle="--")
ax.set_xlim(0, nc); ax.set_ylim(0, nl)
ax.set_xticks([j + .5 for j in range(nc)],
              [f"{ROT[t]}\n(n = {sum(E[k]['tipo'] == t for k in E)})" for t in I.TIPOS], fontsize=10)
ax.xaxis.tick_top()
ax.set_yticks([nl - 1 - i + .5 for i in range(nl)],
              [f"{n} ({tot} estudos)" if tot else n for _, n, tot in linhas], fontsize=10)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
fig.suptitle("(B) Mapa de evidências das 24 intervenções: tipo de intervenção × domínio do desfecho",
             fontsize=12.5, fontweight="bold", x=0.01, ha="left")
fig.text(0.01, 0.012, "Número = estudos de intervenção na combinação; verde mais escuro = maior proporção com efeito; "
         "borda preta = inclui ensaio com distribuição aleatória;\n0 em vermelho = combinação sem estudo. "
         "Entre parênteses, à esquerda, o número de estudos que investigaram o domínio entre os 199.",
         fontsize=9, style="italic")
fig.tight_layout(rect=(0, 0.05, 1, 0.96))
fig.savefig(OUT / "figura7b_mapa_intervencoes.png")
print("7B vazias", vazias)
