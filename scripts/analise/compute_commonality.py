"""
Análise de comunalidade e dominância (Paper 2): decompõe o R² da fadiga física
semanal em variância ÚNICA vs COMPARTILHADA entre a aptidão aeróbia (PV do T-CAR),
a capacidade anaeróbia (melhor tempo em sprints repetidos) e a massa corporal.
Formaliza a especificidade aeróbia e o artefato de porte.

Saída: commonality.json
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from itertools import combinations
from scipy import stats

pvwk = pd.read_csv('pv_wk.csv')[['ID', 'FadFisica', 'Vigor', 'PVini']]
rsa = pd.read_csv('rsa_anon.csv')[['ID', 'BkMel']]
phys = pd.read_csv('phys.csv')[['ID', 'massa']]
M = pvwk.merge(rsa, on='ID').merge(phys, on='ID').dropna()
n = len(M)

def r2(y, cols):
    if not cols:
        return 0.0
    X = np.column_stack([np.ones(n)] + [M[c].values for c in cols])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ b
    ss_res = np.sum((y - yhat) ** 2); ss_tot = np.sum((y - y.mean()) ** 2)
    return 1 - ss_res / ss_tot

PRED = {'PVini': 'aeróbia (PV)', 'BkMel': 'anaeróbia (RSA)', 'massa': 'massa'}

def commonality(y):
    preds = list(PRED)
    full = r2(y, preds)
    # dominância geral: contribuição média de cada preditor sobre todos os subconjuntos
    dom = {}
    for p in preds:
        others = [q for q in preds if q != p]
        incs = []
        for k in range(len(others) + 1):
            for sub in combinations(others, k):
                incs.append(r2(y, list(sub) + [p]) - r2(y, list(sub)))
        dom[p] = float(np.mean(incs))
    # variância única (semiparcial²) e compartilhada aeróbia∩massa
    uniq = {p: float(full - r2(y, [q for q in preds if q != p])) for p in preds}
    r_pv = r2(y, ['PVini']); r_mass = r2(y, ['massa']); r_both = r2(y, ['PVini', 'massa'])
    common_pv_mass = float(r_pv + r_mass - r_both)
    return dict(full=float(full), dominance=dom, unique=uniq,
                r_pv=float(r_pv), r_rsa=float(r2(y, ['BkMel'])), r_mass=float(r_mass),
                common_pv_mass=common_pv_mass)

OUT = dict(n=n, labels=PRED,
           FadFisica=commonality(M['FadFisica'].values.astype(float)),
           Vigor=commonality(M['Vigor'].values.astype(float)))
json.dump(OUT, open('commonality.json', 'w'), indent=1, ensure_ascii=False)

for v in ['FadFisica', 'Vigor']:
    o = OUT[v]
    print('== %s == (R² total = %.3f)' % (v, o['full']))
    for p in PRED:
        print('  %-16s dominância %.3f | única %.3f' % (PRED[p], o['dominance'][p], o['unique'][p]))
    print('  R² aeróbia sozinha %.3f | massa sozinha %.3f | comum(aeróbia∩massa) %.3f' % (
        o['r_pv'], o['r_mass'], o['common_pv_mass']))
print('n =', n, '| OK commonality.json')
