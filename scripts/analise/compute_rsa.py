"""
Capacidade anaeróbia (RSA — teste de sprints repetidos "Baker") e a fadiga do humor:
associações brutas, parciais (controlando a massa corporal) e alométricas.

Dados de entrada (todos anonimizados por código A):
  rsa_anon.csv  : ID, BkMel (melhor tempo, s), BkSoma (soma 8 sprints, s), BkF (índice de fadiga %F)
  phys.csv      : massa
  hum_prof.csv  : humor diário (para as médias semanais)
  tcar2_features: PVini (pico de velocidade do T-CAR — contraste aeróbio)
Saída: rsa_stats.json
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats

rsa = pd.read_csv('rsa_anon.csv')
phys = pd.read_csv('phys.csv')[['ID', 'massa']]
F = pd.read_csv('tcar2_features.csv')[['ID', 'PVini']]
h = pd.read_csv('hum_prof.csv')
wk = h.groupby('ID').agg(Vigor=('Vigor', 'mean'), Fadiga=('Fadiga', 'mean'),
                         FadFisica=('FadFisica', 'mean'), TMD=('TMD', 'mean')).reset_index()
M = wk.merge(rsa, on='ID').merge(phys, on='ID').merge(F, on='ID').dropna()
n = len(M)

def sp(x, y):
    r, p = stats.spearmanr(M[x], M[y]); return float(r), float(p)

def pcorr(xc, yc, zc):
    xr, yr, zr = [stats.rankdata(M[c].values) for c in (xc, yc, zc)]
    def resid(a, b):
        B = np.column_stack([np.ones(len(b)), b]); c, *_ = np.linalg.lstsq(B, a, rcond=None); return a - B @ c
    rx, ry = resid(xr, zr), resid(yr, zr)
    r, p = stats.pearsonr(rx, ry); return float(r), float(p)

RSA = {'BkMel': 'Melhor tempo (s)', 'BkSoma': 'Soma dos 8 (s)', 'BkF': 'Índice de fadiga (%F)'}
OUT = ['FadFisica', 'Fadiga', 'Vigor']
assoc = {}
for m in RSA:
    assoc[m] = {}
    for o in OUT:
        r, p = sp(m, o); rp, pp = pcorr(m, o, 'massa')
        assoc[m][o] = dict(raw_r=r, raw_p=p, par_r=rp, par_p=pp)

# ajuste alométrico do melhor tempo (tempo/massa^b)
b_allo = float(np.polyfit(np.log(M.massa), np.log(M.BkMel), 1)[0])
M['BkMel_adj'] = M.BkMel / (M.massa ** b_allo)
allo = {}
for o in OUT:
    r0, _ = sp('BkMel', o); r1, p1 = stats.spearmanr(M.BkMel_adj, M[o])
    allo[o] = dict(raw=float(r0), adj=float(r1), adj_p=float(p1))

RES = dict(n=n, labels=RSA, assoc=assoc, allo=allo, b_allo=b_allo,
           mass_bkmel=sp('massa', 'BkMel'), mass_fad=sp('massa', 'FadFisica'),
           pv_fad=sp('PVini', 'FadFisica'), pv_vig=sp('PVini', 'Vigor'),
           rsa_pv=sp('BkMel', 'PVini'), conv=sp('FadFisica', 'Fadiga'))
json.dump(RES, open('rsa_stats.json', 'w'), indent=1, ensure_ascii=False)

print('n=%d' % n)
print('massa x melhor tempo: r=%+.2f p=%.3f' % RES['mass_bkmel'])
for m in RSA:
    print('%s:' % RSA[m])
    for o in OUT:
        a = assoc[m][o]; print('   x %-10s bruto %+.2f (p=%.2f) | parcial|massa %+.2f' % (o, a['raw_r'], a['raw_p'], a['par_r']))
print('alométrico melhor tempo (b=%.2f): FadFisica %+.2f -> %+.2f' % (b_allo, allo['FadFisica']['raw'], allo['FadFisica']['adj']))
print('contraste PV x FadFisica: r=%+.2f p=%.3f | RSA x PV: r=%+.2f | conv FadFis x Fadiga: r=%+.2f' % (
    RES['pv_fad'][0], RES['pv_fad'][1], RES['rsa_pv'][0], RES['conv'][0]))
