# -*- coding: utf-8 -*-
"""Estrutura de associação em dois planos que a matriz agregada não separa.

Duas perguntas que a correlação agregada dos 166 pares atleta-dia responde mal:

1. A associação entre a fadiga e a perturbação total é constante ao longo da
   semana? Se ela cresce, o composto deixa de agregar seis dimensões e passa a
   reproduzir uma só, de modo que a conveniência do escalar decresce à medida
   que a carga se acumula.

2. Uma correlação entre duas subescalas nasce de os atletas diferirem entre si,
   ou de cada atleta variar de um dia para o outro? A correlação agregada mistura
   os dois planos e pode inverter de sinal entre eles. A separação segue a
   decomposição clássica: o plano entre atletas correlaciona as médias
   individuais; o plano dentro do atleta correlaciona os desvios de cada
   observação em relação à média do próprio atleta.

Escreve dados/V2_assoc.json.
"""
import json, os, numpy as np
from scipy import stats

RAIZ = os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "dados")
B = json.load(open(f"{DADOS}/V2_base.json", encoding="utf-8"))

V7 = ['Tensão', 'Depressão', 'Raiva', 'Vigor', 'Fadiga', 'Confusão', 'TMD']
P = B['pares']                     # a unidade canônica: um valor por atleta e por dia
ath = np.array([r['a'] for r in P]); dia = np.array([r['dia'] for r in P])
X = {v: np.array([r[v] for r in P], float) for v in V7}

n = len(dia)
print(f"{n} pares atleta-dia, {len(set(ath))} atletas")

# ---------- 1. acoplamento fadiga × perturbação total, dia a dia ----------
ACOPL = {"dias": [], "par": "Fadiga×TMD"}
for d in range(1, 8):
    m = dia == d
    rho, p = stats.spearmanr(X['Fadiga'][m], X['TMD'][m])
    ACOPL["dias"].append(dict(dia=d, n=int(m.sum()), rho=float(rho), p=float(p),
                              r2=float(rho ** 2 * 100)))
rhos = [x["rho"] for x in ACOPL["dias"]]
rt, pt = stats.spearmanr(list(range(1, 8)), rhos)
ACOPL.update(rho_d1=rhos[0], rho_d7=rhos[-1],
             r2_d1=ACOPL["dias"][0]["r2"], r2_d7=ACOPL["dias"][-1]["r2"],
             tendencia_rho=float(rt), tendencia_p=float(pt),
             tendencia_significativa=bool(pt < .05))
print("\nacoplamento fadiga × TMD por dia")
for x in ACOPL["dias"]:
    print(f"  D{x['dia']}  n={x['n']:>2}  ρ={x['rho']:+.3f}  p={x['p']:.4f}  r²={x['r2']:5.1f}%")
print(f"  tendência do coeficiente ao longo dos sete dias: ρ={rt:+.3f}  p={pt:.4f}  "
      f"({'significativa' if pt < .05 else 'não conclusiva'})")

# ---------- 2. associação entre atletas e dentro do atleta ----------
ats = sorted(set(ath))
med = {a: {v: float(X[v][ath == a].mean()) for v in V7} for a in ats}
PLANOS = {}
for i, a_ in enumerate(V7):
    for b_ in V7[i + 1:]:
        E = stats.spearmanr([med[a][a_] for a in ats], [med[a][b_] for a in ats])
        dx = np.array([X[a_][k] - med[ath[k]][a_] for k in range(n)])
        dy = np.array([X[b_][k] - med[ath[k]][b_] for k in range(n)])
        D = stats.spearmanr(dx, dy)
        G = stats.spearmanr(X[a_], X[b_])
        PLANOS[f"{a_}×{b_}"] = dict(
            entre_rho=float(E.statistic), entre_p=float(E.pvalue), entre_n=len(ats),
            dentro_rho=float(D.statistic), dentro_p=float(D.pvalue), dentro_n=n,
            agregado_rho=float(G.statistic), agregado_p=float(G.pvalue),
            # discordância só conta quando os dois planos são conclusivos: sinais
            # opostos entre dois coeficientes não significativos não dizem nada.
            discordante=bool(np.sign(E.statistic) != np.sign(D.statistic)
                             and E.pvalue < .05 and D.pvalue < .05))
print(f"\nassociação em dois planos, {len(PLANOS)} pares")
print(f"  {'par':22}{'agregado':>10}{'entre':>10}{'dentro':>10}   observação")
for k, d in PLANOS.items():
    obs = []
    if d['entre_p'] >= .05 and d['dentro_p'] < .05: obs.append("só dentro do atleta")
    if d['entre_p'] < .05 and d['dentro_p'] >= .05: obs.append("só entre atletas")
    if d['discordante']: obs.append("sinais opostos entre os planos")
    print(f"  {k:22}{d['agregado_rho']:+10.3f}{d['entre_rho']:+10.3f}{d['dentro_rho']:+10.3f}   "
          + "; ".join(obs))

SO_DENTRO = [k for k, d in PLANOS.items() if d['entre_p'] >= .05 and d['dentro_p'] < .05]
SO_ENTRE = [k for k, d in PLANOS.items() if d['entre_p'] < .05 and d['dentro_p'] >= .05]
print(f"\n  {len(SO_DENTRO)} pares se associam apenas dentro do atleta; "
      f"{len(SO_ENTRE)} apenas entre atletas.")

json.dump(dict(V7=V7, ACOPL=ACOPL, PLANOS=PLANOS, SO_DENTRO=SO_DENTRO, SO_ENTRE=SO_ENTRE,
               n_pares=n, n_atletas=len(ats)),
          open(f"{DADOS}/V2_assoc.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"\nescrito: {DADOS}/V2_assoc.json")
