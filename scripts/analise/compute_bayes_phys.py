"""
Modelo bayesiano multinível com preditor fisiológico (Paper 2).
Testa se a aptidão aeróbia (pico de velocidade do T-CAR) modula, no nível
do atleta (nível 2), a trajetória do humor (nível 1: dia + pré/pós), tanto
o NÍVEL (intercepto) quanto a TAXA (inclinação por dia).

y_ij = b0 + b1*dia_c + b2*pos + b3*PVc + b4*(dia_c*PVc) + u0_i + u1_i*dia_c + e_ij
  b3 = efeito da aptidão sobre o nível do humor
  b4 = interação aptidão × dia (a aptidão modula a taxa de deriva?)
Aplicado a fadiga física, vigor e PTH. Amostrador de Gibbs (semente 2024).
Validação: médias a posteriori vs MixedLM (REML). Saída: bayes_phys.json
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from numpy.linalg import inv, cholesky
import statsmodels.formula.api as smf

rng = np.random.default_rng(2024)
h = pd.read_csv('hum_prof.csv')
F = pd.read_csv('tcar2_features.csv')[['ID', 'PVini']]
h = h.merge(F, on='ID', how='left')
h['pos'] = (h['momento'] == 'pos').astype(float)
h['dia_c'] = h['dia'].astype(float) - 1.0

def wishart_inv(nu, S):
    p = S.shape[0]; L = cholesky(inv(S)); A = np.zeros((p, p))
    for i in range(p):
        A[i, i] = np.sqrt(rng.chisquare(nu - i))
        for j in range(i): A[i, j] = rng.standard_normal()
    W = L @ A @ A.T @ L.T; return inv(W)

def gibbs(y, Xcols, gid, n_iter=12000, burn=4000, thin=4):
    ids = np.unique(gid); n = len(ids)
    idx = {g: np.where(gid == g)[0] for g in ids}
    X = np.column_stack([np.ones(len(y))] + Xcols)          # inclui intercepto
    Z = np.column_stack([np.ones(len(y)), Xcols[0]])        # random: intercepto + dia
    p, q = X.shape[1], Z.shape[1]
    B0inv = np.eye(p) * 1e-6; b0 = np.zeros(p)
    a_s, b_s = 1e-3, 1e-3; nu0 = q + 2; S0 = np.eye(q)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    U = {g: np.zeros(q) for g in ids}; sig2 = np.var(y - X @ beta); Sig = np.eye(q)
    keep = {k: [] for k in ['b1', 'b2', 'b3', 'b4', 'sig2']}
    XtX = X.T @ X
    for it in range(n_iter):
        r = y - np.array([Z[j] @ U[gid[j]] for j in range(len(y))])
        cov = inv(B0inv + XtX / sig2); mean = cov @ (B0inv @ b0 + X.T @ r / sig2)
        beta = rng.multivariate_normal(mean, cov)
        Siginv = inv(Sig)
        for g in ids:
            j = idx[g]; Zi, yi, Xi = Z[j], y[j], X[j]
            cu = inv(Siginv + Zi.T @ Zi / sig2); mu = cu @ (Zi.T @ (yi - Xi @ beta) / sig2)
            U[g] = rng.multivariate_normal(mu, cu)
        resid = y - X @ beta - np.array([Z[j] @ U[gid[j]] for j in range(len(y))])
        sig2 = 1.0 / rng.gamma(a_s + len(y) / 2, 1.0 / (b_s + 0.5 * resid @ resid))
        ss = np.zeros((q, q))
        for g in ids: ss += np.outer(U[g], U[g])
        Sig = wishart_inv(nu0 + n, S0 + ss)
        if it >= burn and (it - burn) % thin == 0:
            keep['b1'].append(beta[1]); keep['b2'].append(beta[2])
            keep['b3'].append(beta[3]); keep['b4'].append(beta[4]); keep['sig2'].append(sig2)
    return {k: np.array(v) for k, v in keep.items()}

def summ(a):
    return dict(mean=float(np.mean(a)), lo=float(np.percentile(a, 2.5)),
               hi=float(np.percentile(a, 97.5)),
               p_dir=float(max(np.mean(a > 0), np.mean(a < 0))))

OUT = {}
for var in ['FadFisica', 'Vigor', 'TMD']:
    d = h.dropna(subset=[var, 'PVini']).copy()
    d['PVc'] = d['PVini'] - d['PVini'].mean()
    d['dxpv'] = d['dia_c'] * d['PVc']
    y = d[var].values.astype(float)
    post = gibbs(y, [d['dia_c'].values, d['pos'].values, d['PVc'].values, d['dxpv'].values], d['ID'].values)
    md = smf.mixedlm('%s ~ dia_c + pos + PVc + dxpv' % var, d, groups=d['ID'], re_formula='~dia_c').fit(reml=True)
    OUT[var] = dict(b_dia=summ(post['b1']), b_pos=summ(post['b2']),
                    b_pv=summ(post['b3']), b_pvxdia=summ(post['b4']),
                    freq=dict(b_pv=float(md.fe_params['PVc']), b_pvxdia=float(md.fe_params['dxpv'])),
                    n_obs=int(len(y)), n_ath=int(d['ID'].nunique()))

json.dump(OUT, open('bayes_phys.json', 'w'), indent=1, ensure_ascii=False)
for v in OUT:
    o = OUT[v]
    print('== %s (n=%d obs, %d atletas) ==' % (v, o['n_obs'], o['n_ath']))
    print('  aptidao->nivel  b_PV     = %+.3f [%+.3f, %+.3f]  (REML %+.3f)' % (
        o['b_pv']['mean'], o['b_pv']['lo'], o['b_pv']['hi'], o['freq']['b_pv']))
    print('  aptidao->taxa   b_PVxdia = %+.3f [%+.3f, %+.3f]  (REML %+.3f)' % (
        o['b_pvxdia']['mean'], o['b_pvxdia']['lo'], o['b_pvxdia']['hi'], o['freq']['b_pvxdia']))
print('OK bayes_phys.json')
