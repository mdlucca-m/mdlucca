"""
Modelo bayesiano multinível de curva de crescimento para o humor (Vigor e Fadiga)
ao longo do microciclo, com separação da resposta AGUDA (pré→pós, intrassessão)
e CRÔNICA (deriva entre dias) e quantificação da heterogeneidade interindividual.

y_ij = b0 + b1*dia_c + b2*pos + u0_i + u1_i*dia_c + e_ij
  u_i ~ N(0, Sigma)  (intercepto e inclinação aleatórios por atleta)
  e_ij ~ N(0, sigma2)

Estimação: amostrador de Gibbs (priors conjugados; sem dependências externas).
Validação: médias a posteriori confrontadas com MixedLM (REML, statsmodels).
Saída: bayes_growth.json
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from numpy.linalg import inv, cholesky
import statsmodels.formula.api as smf

rng = np.random.default_rng(2024)
h = pd.read_csv('hum_prof.csv')
h['pos'] = (h['momento'] == 'pos').astype(float)          # baseline/pré = 0; pós = 1
h['dia_c'] = h['dia'].astype(float) - 1.0                  # dia centrado em 0..6

def wishart_inv(nu, S):
    """Amostra de uma Inverse-Wishart(nu, S) via Wishart de S^{-1}."""
    p = S.shape[0]
    L = cholesky(inv(S))
    A = np.zeros((p, p))
    for i in range(p):
        A[i, i] = np.sqrt(rng.chisquare(nu - i))
        for j in range(i):
            A[i, j] = rng.standard_normal()
    W = L @ A @ A.T @ L.T           # Wishart(nu, S^{-1})
    return inv(W)                    # Inverse-Wishart(nu, S)

def gibbs(y, dia_c, pos, gid, n_iter=20000, burn=6000, thin=4):
    ids = np.unique(gid)
    n = len(ids)
    idx = {g: np.where(gid == g)[0] for g in ids}
    X = np.column_stack([np.ones_like(y), dia_c, pos])      # efeitos fixos
    Z = np.column_stack([np.ones_like(y), dia_c])           # efeitos aleatórios
    p, q = X.shape[1], Z.shape[1]
    # priors
    B0inv = np.eye(p) * 1e-6; b0 = np.zeros(p)
    a_s, b_s = 1e-3, 1e-3                                    # IG p/ sigma2
    nu0 = q + 2; S0 = np.eye(q)                              # IW p/ Sigma
    # init
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    U = {g: np.zeros(q) for g in ids}
    sig2 = np.var(y - X @ beta)
    Sig = np.eye(q)
    keep = {k: [] for k in ['b0', 'b1', 'b2', 'sig2', 's00', 's11', 'rho']}
    XtX = X.T @ X
    for it in range(n_iter):
        # --- beta | . ---
        r = y - np.array([Z[j] @ U[gid[j]] for j in range(len(y))])
        prec = B0inv + XtX / sig2
        cov = inv(prec)
        mean = cov @ (B0inv @ b0 + X.T @ r / sig2)
        beta = rng.multivariate_normal(mean, cov)
        # --- u_i | . ---
        Siginv = inv(Sig)
        ss_u = np.zeros((q, q))
        for g in ids:
            j = idx[g]
            Zi, yi, Xi = Z[j], y[j], X[j]
            prec_u = Siginv + Zi.T @ Zi / sig2
            cov_u = inv(prec_u)
            mean_u = cov_u @ (Zi.T @ (yi - Xi @ beta) / sig2)
            U[g] = rng.multivariate_normal(mean_u, cov_u)
            ss_u += np.outer(U[g], U[g])
        # --- sigma2 | . ---
        resid = y - X @ beta - np.array([Z[j] @ U[gid[j]] for j in range(len(y))])
        sig2 = 1.0 / rng.gamma(a_s + len(y) / 2, 1.0 / (b_s + 0.5 * resid @ resid))
        # --- Sigma | . ---
        Sig = wishart_inv(nu0 + n, S0 + ss_u)
        if it >= burn and (it - burn) % thin == 0:
            keep['b0'].append(beta[0]); keep['b1'].append(beta[1]); keep['b2'].append(beta[2])
            keep['sig2'].append(sig2)
            keep['s00'].append(Sig[0, 0]); keep['s11'].append(Sig[1, 1])
            keep['rho'].append(Sig[0, 1] / np.sqrt(Sig[0, 0] * Sig[1, 1]))
    return {k: np.array(v) for k, v in keep.items()}

def summ(a):
    return dict(mean=float(np.mean(a)), lo=float(np.percentile(a, 2.5)),
               hi=float(np.percentile(a, 97.5)),
               p_dir=float(np.mean(a > 0) if np.mean(a) > 0 else np.mean(a < 0)))

OUT = {}
for var in ['Vigor', 'Fadiga', 'TMD']:
    d = h.dropna(subset=[var]).copy()
    y = d[var].values.astype(float)
    post = gibbs(y, d['dia_c'].values.astype(float), d['pos'].values.astype(float),
                 d['ID'].values)
    icc = post['s00'] / (post['s00'] + post['sig2'])         # ICC (partição intra/entre)
    sd_slope = np.sqrt(post['s11'])                          # heterogeneidade das inclinações
    # validação frequentista (REML)
    md = smf.mixedlm('%s ~ dia_c + pos' % var, d, groups=d['ID'],
                     re_formula='~dia_c').fit(reml=True)
    OUT[var] = dict(
        b_dia=summ(post['b1']), b_pos=summ(post['b2']), b0=summ(post['b0']),
        icc=summ(icc), sd_slope=summ(sd_slope), corr_int_slope=summ(post['rho']),
        freq=dict(b_dia=float(md.fe_params['dia_c']), b_pos=float(md.fe_params['pos']),
                  b0=float(md.fe_params['Intercept'])),
        n_obs=int(len(y)), n_ath=int(d['ID'].nunique()))

json.dump(OUT, open('bayes_growth.json', 'w'), indent=1, ensure_ascii=False)
for v in OUT:
    o = OUT[v]
    print('\n== %s ==' % v)
    print('  dia (crônico): post %.3f [%.3f, %.3f] | REML %.3f' % (
        o['b_dia']['mean'], o['b_dia']['lo'], o['b_dia']['hi'], o['freq']['b_dia']))
    print('  pos (agudo):   post %.3f [%.3f, %.3f] | REML %.3f' % (
        o['b_pos']['mean'], o['b_pos']['lo'], o['b_pos']['hi'], o['freq']['b_pos']))
    print('  ICC: %.2f [%.2f, %.2f] | SD inclinação: %.3f [%.3f, %.3f]' % (
        o['icc']['mean'], o['icc']['lo'], o['icc']['hi'],
        o['sd_slope']['mean'], o['sd_slope']['lo'], o['sd_slope']['hi']))
print('\nOK bayes_growth.json')
