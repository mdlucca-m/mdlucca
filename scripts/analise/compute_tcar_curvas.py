"""
Comparação de modelos (post hoc) da relação aptidão intermitente (T-CAR) × resposta de humor.
Ajusta, à relação entre o pico de velocidade do T-CAR e as médias semanais de humor,
três formas funcionais contínuas — linear, logarítmica (ln do PV) e polinomial (quadrática) —
e compara a qualidade de ajuste por R², R² ajustado, AIC, BIC e RMSE (seleção a posteriori
do melhor modelo). Para o desfecho binário (dia de fadiga elevada), reforça a regressão
logística com estatísticas de ajuste (log-verossimilhança, pseudo-R² de McFadden, AIC, BIC)
e compara o preditor na escala bruta (PV) versus logarítmica (ln PV).
Saída: tcar_curvas.json
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json

wk = pd.read_csv('pv_wk.csv')            # médias semanais por atleta + PV (T-CAR2 final) + PVini (T-CAR1)
h  = pd.read_csv('hum_prof.csv')         # base diária p/ o desfecho binário de fadiga
F  = pd.read_csv('tcar2_features.csv')[['ID','PV','PVini']]

PRED = 'PVini'                            # T-CAR1 (pico de velocidade), o preditor relevante
PREDLAB = 'T-CAR1 (pico de velocidade)'

# ---------------- utilitários de ajuste (OLS por mínimos quadrados) ----------------
def ols(X, y):
    """Ajuste linear em X (com coluna de 1s já incluída). Retorna coef, R², R²aj, AIC, BIC, RMSE, n, k."""
    n = len(y); p = X.shape[1] - 1                     # nº de preditores (fora o intercepto)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    rss = float(np.sum((y - yhat) ** 2))
    tss = float(np.sum((y - y.mean()) ** 2))
    r2  = 1 - rss / tss if tss > 0 else np.nan
    r2a = 1 - (1 - r2) * (n - 1) / (n - p - 1) if n - p - 1 > 0 else np.nan
    rmse = float(np.sqrt(rss / n))
    k = X.shape[1] + 1                                  # coefs + variância (σ²)
    ll = -0.5 * n * (np.log(2 * np.pi) + np.log(rss / n) + 1)   # log-verossim. gaussiana
    aic = 2 * k - 2 * ll
    bic = k * np.log(n) - 2 * ll
    return dict(beta=[float(b) for b in beta], r2=float(r2), r2a=float(r2a),
                aic=float(aic), bic=float(bic), rmse=rmse, n=int(n), k=int(X.shape[1]), ll=float(ll))

def fit_curvas(x, y):
    m = pd.DataFrame({'x': x, 'y': y}).dropna()
    x = m.x.values.astype(float); y = m.y.values.astype(float)
    one = np.ones_like(x)
    out = {}
    out['linear'] = ols(np.column_stack([one, x]), y)                 # y = a + b·x
    out['log']    = ols(np.column_stack([one, np.log(x)]), y)         # y = a + b·ln(x)
    out['quad']   = ols(np.column_stack([one, x, x ** 2]), y)         # y = a + b·x + c·x²
    # melhor modelo por AIC (menor)
    out['best'] = min(('linear', 'log', 'quad'), key=lambda k_: out[k_]['aic'])
    return out

CONT = {}
for resp, lab in [('FadFisica', 'Fadiga física'), ('Vigor', 'Vigor')]:
    CONT[resp] = fit_curvas(wk[PRED], wk[resp])
    CONT[resp]['lab'] = lab

# ---------------- regressão logística: PV bruto vs ln(PV) ----------------
dm = h.groupby(['ID', 'dia'])['FadFisica'].mean().reset_index().merge(F, on='ID', how='left')
dd = dm.dropna(subset=['FadFisica', PRED]).copy()
cut = dd.FadFisica.quantile(2 / 3)
dd['hi'] = (dd.FadFisica >= cut).astype(int)

def logit_fit(x, y):
    """Newton-Raphson; retorna coefs e estatísticas de ajuste."""
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(y)
    b0, b1 = 0.0, 0.0
    for _ in range(400):
        z = b0 + b1 * x; pr = 1 / (1 + np.exp(-z)); W = pr * (1 - pr) + 1e-9
        g0 = np.sum(y - pr); g1 = np.sum((y - pr) * x)
        h00 = -np.sum(W); h01 = -np.sum(W * x); h11 = -np.sum(W * x * x)
        det = h00 * h11 - h01 * h01
        b0 -= (h11 * g0 - h01 * g1) / det; b1 -= (-h01 * g0 + h00 * g1) / det
    z = b0 + b1 * x; pr = np.clip(1 / (1 + np.exp(-z)), 1e-9, 1 - 1e-9)
    ll = float(np.sum(y * np.log(pr) + (1 - y) * np.log(1 - pr)))     # log-verossim. do modelo
    p0 = y.mean(); ll0 = float(np.sum(y * np.log(p0) + (1 - y) * np.log(1 - p0)))  # modelo nulo
    mcf = 1 - ll / ll0                                                # pseudo-R² de McFadden
    k = 2                                                             # intercepto + inclinação
    aic = 2 * k - 2 * ll; bic = k * np.log(n) - 2 * ll; dev = -2 * ll
    # AUC (Mann-Whitney) sobre o escore
    from scipy import stats
    s = pr; pos = s[y == 1]; neg = s[y == 0]
    auc = float(stats.mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg)))
    return dict(b0=float(b0), b1=float(b1), OR=float(np.exp(b1)), ll=ll, ll0=ll0,
                mcfadden=float(mcf), aic=float(aic), bic=float(bic), dev=float(dev),
                auc=auc, n=int(n))

LOGI = {
    'linear_pred': logit_fit(dd[PRED], dd['hi']),          # logit ~ PV
    'log_pred':    logit_fit(np.log(dd[PRED]), dd['hi']),  # logit ~ ln(PV)
}
LOGI['best'] = min(('linear_pred', 'log_pred'), key=lambda k_: LOGI[k_]['aic'])
LOGI['cut'] = float(cut)

RES = dict(pred=PRED, predlab=PREDLAB, cont=CONT, logistic=LOGI)
json.dump(RES, open('tcar_curvas.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- relatório ----------------
NM = {'linear': 'Linear', 'log': 'Logarítmica', 'quad': 'Polinomial (2º grau)'}
for resp in CONT:
    c = CONT[resp]
    print('\n== %s ~ %s ==' % (c['lab'], PREDLAB))
    print('%-22s %6s %7s %8s %8s %7s' % ('Modelo', 'R²', 'R²aj', 'AIC', 'BIC', 'RMSE'))
    for mdl in ('linear', 'log', 'quad'):
        v = c[mdl]
        star = ' *melhor' if mdl == c['best'] else ''
        print('%-22s %6.3f %7.3f %8.1f %8.1f %7.3f%s' % (NM[mdl], v['r2'], v['r2a'], v['aic'], v['bic'], v['rmse'], star))
print('\n== Regressão logística: dia de fadiga elevada ~ preditor ==')
print('%-16s %8s %10s %8s %8s %6s' % ('Preditor', 'McFadden', 'logLik', 'AIC', 'BIC', 'AUC'))
for k_, lab in [('linear_pred', 'PV (bruto)'), ('log_pred', 'ln(PV)')]:
    v = LOGI[k_]; star = ' *melhor' if k_ == LOGI['best'] else ''
    print('%-16s %8.3f %10.2f %8.1f %8.1f %6.2f%s' % (lab, v['mcfadden'], v['ll'], v['aic'], v['bic'], v['auc'], star))
print('\nOK -> tcar_curvas.json')
