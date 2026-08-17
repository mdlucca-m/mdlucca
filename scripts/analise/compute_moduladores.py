"""
Moduladores da MAGNITUDE dos efeitos agudo e crônico do humor.

Efeito AGUDO   = variação intrassessão (pós − pré) por atleta-dia (dias 2–7).
Efeito CRÔNICO = inclinação semanal (taxa por dia) da média diária, por atleta (≥ 4 dias).

Para cada efeito, testa-se quanto as características do atleta modulam a sua magnitude
— aptidão aeróbia intermitente (PV do T-CAR), composição corporal (massa, % de gordura),
potência de membros inferiores (salto CMJ, arremesso Baker), sono (Epworth), estresse
(PSS-14) e carga interna (TRIMP) — por correlação de Pearson e pelo COEFICIENTE DE
DETERMINAÇÃO (R²) de cada relação, além de modelos de regressão múltipla (R², R²
ajustado e coeficientes padronizados β*). Reporta-se também o controle de comparações
múltiplas (Holm), dado o número de testes exploratórios.
Saída: moduladores.json
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats

h = pd.read_csv('hum_prof.csv'); phys = pd.read_csv('phys.csv')
F = pd.read_csv('tcar2_features.csv')[['ID', 'PVini', 'TRIMP']]
VARS = ['Vigor', 'Fadiga', 'TMD']
MODS = ['PVini', 'pGordura', 'massa', 'CMJ_mai', 'Baker_mai', 'Epworth', 'PSS', 'TRIMP']
MODLAB = {'PVini': 'Aptidão (PV T-CAR)', 'pGordura': '% de gordura', 'massa': 'Massa corporal',
          'CMJ_mai': 'Potência (CMJ)', 'Baker_mai': 'Potência (Baker)', 'Epworth': 'Sonolência (Epworth)',
          'PSS': 'Estresse (PSS-14)', 'TRIMP': 'Carga interna (TRIMP)'}

# ---------- efeito AGUDO (pós − pré por atleta-dia) ----------
piv = h[h.momento.isin(['pre', 'pos'])].pivot_table(index=['ID', 'dia'], columns='momento', values=VARS)
ac = pd.DataFrame({v: piv[(v, 'pos')] - piv[(v, 'pre')] for v in VARS}).dropna().reset_index()
acute = {'n_obs': int(len(ac)), 'n_ath': int(ac.ID.nunique()), 'mean': {}, 'day_trend': {}}
for v in VARS:
    acute['mean'][v] = float(ac[v].mean())
    lr = stats.linregress(ac.dia, ac[v])
    acute['day_trend'][v] = {'slope': float(lr.slope), 'p': float(lr.pvalue)}
# moderação do efeito agudo médio por atleta
acm = ac.groupby('ID')[VARS].mean().add_prefix('ac_')

# ---------- efeito CRÔNICO (inclinação semanal por atleta) ----------
dm = h.groupby(['ID', 'dia']).mean(numeric_only=True).reset_index()
def wslope(g, v):
    gg = g.dropna(subset=[v])
    return stats.linregress(gg.dia, gg[v]).slope if gg.dia.nunique() >= 4 else np.nan
S = pd.DataFrame({'sl_' + v: dm.groupby('ID').apply(lambda g: wslope(g, v)) for v in VARS})
epw = h.groupby('ID').agg(Epworth=('Epworth', 'mean'), PSS=('PSS', 'mean'))
M = (S.join(acm).join(phys.set_index('ID')[['massa', 'pGordura', 'CMJ_mai', 'Baker_mai']])
       .join(F.set_index('ID')).join(epw))

def matrix(prefix):
    mat = {}; pvals = []
    for v in VARS:
        eff = prefix + v; mat[v] = {}
        for m in MODS:
            d = M[[eff, m]].dropna()
            if len(d) < 8:
                mat[v][m] = None; continue
            r, p = stats.pearsonr(d[eff], d[m])
            mat[v][m] = {'r': float(r), 'r2': float(r * r), 'p': float(p), 'n': int(len(d))}
            pvals.append((v, m, p))
    return mat, pvals

chr_mat, chr_p = matrix('sl_')
acu_mat, acu_p = matrix('ac_')

# controle de comparações múltiplas (Holm) sobre todos os testes de moderação
allp = chr_p + acu_p
order = sorted(range(len(allp)), key=lambda i: allp[i][2])
m = len(allp); holm_sig = []
for rank, i in enumerate(order):
    v, mod, p = allp[i]
    if p <= 0.05 / (m - rank):
        holm_sig.append({'efeito': v, 'moderador': mod, 'p': float(p)})
    else:
        break

# ---------- regressão múltipla (coeficientes padronizados + R²) ----------
def mlr(y, Xcols):
    d = M[[y] + Xcols].dropna()
    yv = (d[y] - d[y].mean()) / d[y].std()
    Xz = [np.ones(len(d))] + [((d[c] - d[c].mean()) / d[c].std()).values for c in Xcols]
    X = np.column_stack(Xz)
    b, *_ = np.linalg.lstsq(X, yv.values, rcond=None); yh = X @ b
    rss = float(np.sum((yv.values - yh) ** 2)); tss = float(np.sum((yv.values - yv.mean()) ** 2))
    r2 = 1 - rss / tss; n = len(d); p = len(Xcols); adj = 1 - (1 - r2) * (n - 1) / (n - p - 1)
    return {'r2': float(r2), 'adj': float(adj), 'n': int(n),
            'beta': {c: float(bb) for c, bb in zip(Xcols, b[1:])}}
mlr_models = {
    'sl_Vigor~PVini+CMJ_mai': mlr('sl_Vigor', ['PVini', 'CMJ_mai']),
    'sl_Vigor~PVini+Epworth': mlr('sl_Vigor', ['PVini', 'Epworth']),
    'sl_Fadiga~PVini+TRIMP':  mlr('sl_Fadiga', ['PVini', 'TRIMP']),
    'sl_TMD~PVini+TRIMP':     mlr('sl_TMD', ['PVini', 'TRIMP']),
}
slope_mean = {v: float(M['sl_' + v].mean()) for v in VARS}

RES = dict(mods=MODS, modlab=MODLAB, vars=VARS, acute=acute,
           chronic=dict(slope_mean=slope_mean, matrix=chr_mat),
           acute_matrix=acu_mat, mlr=mlr_models, n_tests=m, holm_sig=holm_sig,
           n_ath_chronic=int(M['sl_Vigor'].notna().sum()))
json.dump(RES, open('moduladores.json', 'w'), indent=1, ensure_ascii=False)

# ---------- relatório ----------
print('EFEITO AGUDO (pós−pré) — n=%d obs, %d atletas' % (acute['n_obs'], acute['n_ath']))
for v in VARS:
    print('  Δ %-6s média=%+.2f | tendência ao longo da semana: slope=%+.3f p=%.3f'
          % (v, acute['mean'][v], acute['day_trend'][v]['slope'], acute['day_trend'][v]['p']))
print('\nEFEITO CRÔNICO (inclinação/dia) — %d atletas' % RES['n_ath_chronic'])
for v in VARS:
    print('  %s (slope médio=%+.3f/dia): melhores moduladores por R²:' % (v, slope_mean[v]))
    items = [(m, chr_mat[v][m]) for m in MODS if chr_mat[v][m]]
    for m, s in sorted(items, key=lambda kv: -kv[1]['r2'])[:3]:
        print('     %-20s r=%+.2f R²=%.2f p=%.3f%s' % (MODLAB[m], s['r'], s['r2'], s['p'], '  *' if s['p'] < 0.05 else ''))
print('\nRegressão múltipla (β* padronizado):')
for k, mm in mlr_models.items():
    print('  %-26s R²=%.2f adjR²=%.2f n=%d | %s' % (k, mm['r2'], mm['adj'], mm['n'], {c: round(b, 2) for c, b in mm['beta'].items()}))
print('\nComparações múltiplas: %d testes | sobreviventes a Holm: %s' % (RES['n_tests'], holm_sig or 'nenhum'))
