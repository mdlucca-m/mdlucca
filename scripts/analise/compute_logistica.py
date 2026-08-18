"""
Regressões logísticas adicionais alinhadas aos objetivos do estudo.

  A) Migração de perfil ao longo do microciclo (objetivo viii; hipótese central):
     P(iceberg) ~ dia   e   P(barbatana de tubarão) ~ dia
     -> OR por dia (com IC bootstrap por atleta), prob. prevista no Dia 1 e Dia 7.
  B) Aptidão protege a prontidão (objetivos viii+ix):
     P(iceberg) ~ PV(T-CAR1)   e   modelo ajustado P(iceberg) ~ dia + PV.
  C) Limiar de baixo vigor (objetivo ix; simétrico ao limiar de fadiga):
     P(dia de baixo vigor) ~ PV(T-CAR1), com corte de Youden, AUC e OR.

Todos os modelos reportam log-verossimilhança, pseudo-R² de McFadden, AIC, BIC e AUC.
Saída: logistica.json
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats

h = pd.read_csv('hum_prof.csv')
F = pd.read_csv('tcar2_features.csv')[['ID', 'PV', 'PVini']]   # PVini = T-CAR1
h = h.merge(F, on='ID', how='left')
days = np.arange(1, 8)

# ---------------- ajuste logístico (Newton-Raphson) + estatísticas ----------------
def logit_fit(X, y):
    """X: matriz n×p SEM intercepto; y: 0/1. Retorna coefs (b0 + b) e estatísticas."""
    X = np.asarray(X, float); y = np.asarray(y, float); n = len(y)
    if X.ndim == 1: X = X[:, None]
    Xd = np.column_stack([np.ones(n), X]); p = Xd.shape[1]
    b = np.zeros(p)
    for _ in range(400):
        z = Xd @ b; pr = 1 / (1 + np.exp(-z)); W = pr * (1 - pr) + 1e-9
        g = Xd.T @ (y - pr); H = -(Xd * W[:, None]).T @ Xd
        b -= np.linalg.solve(H, g)
    z = Xd @ b; pr = np.clip(1 / (1 + np.exp(-z)), 1e-9, 1 - 1e-9)
    ll = float(np.sum(y * np.log(pr) + (1 - y) * np.log(1 - pr)))
    p0 = y.mean(); ll0 = float(np.sum(y * np.log(p0) + (1 - y) * np.log(1 - p0)))
    mcf = 1 - ll / ll0 if ll0 != 0 else np.nan
    k = p; aic = 2 * k - 2 * ll; bic = k * np.log(n) - 2 * ll
    pos, neg = pr[y == 1], pr[y == 0]
    auc = float(stats.mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg))) if len(pos) and len(neg) else np.nan
    return dict(b=[float(v) for v in b], OR=[float(np.exp(v)) for v in b[1:]],
                ll=ll, ll0=ll0, mcfadden=float(mcf), aic=float(aic), bic=float(bic),
                auc=auc, n=int(n), events=int(y.sum()))

def prob_at(fit, xrow):
    z = fit['b'][0] + sum(fit['b'][1 + i] * xrow[i] for i in range(len(xrow)))
    return float(1 / (1 + np.exp(-z)))

def boot_or(sub, xcols, ycol, seed=2024, B=1000):
    """IC95% do OR do 1º preditor por reamostragem de ATLETAS (clusters)."""
    ids = sub.ID.unique(); rng = np.random.default_rng(seed); ors = []
    for _ in range(B):
        s = rng.choice(ids, len(ids), True)
        g = pd.concat([sub[sub.ID == i] for i in s])
        try:
            f = logit_fit(g[xcols].values, g[ycol].values); ors.append(f['OR'][0])
        except Exception:
            pass
    lo, hi = np.nanpercentile(ors, [2.5, 97.5])
    return float(lo), float(hi)

def youden(x, y):
    x = np.asarray(x, float); y = np.asarray(y); best = None
    for t in np.unique(x):
        pred = (x <= t).astype(int)
        tp = np.sum((pred == 1) & (y == 1)); fn = np.sum((pred == 0) & (y == 1))
        tn = np.sum((pred == 0) & (y == 0)); fp = np.sum((pred == 1) & (y == 0))
        se = tp / (tp + fn + 1e-9); sp = tn / (tn + fp + 1e-9); j = se + sp - 1
        if best is None or j > best[1]: best = (float(t), float(j), float(se), float(sp))
    return best

RES = {}

# ================= A) Migração de perfil ~ dia =================
A = {}
for perfil, key in [('Iceberg', 'iceberg'), ('Barbatana tubarão', 'barbatana')]:
    sub = h.dropna(subset=['dia']).copy(); sub['y'] = (sub.perfil == perfil).astype(int)
    fit = logit_fit(sub['dia'].values, sub['y'].values)
    lo, hi = boot_or(sub, ['dia'], 'y')
    fit['OR_dia'] = fit['OR'][0]; fit['OR_lo'], fit['OR_hi'] = lo, hi
    fit['p_d1'] = prob_at(fit, [1]); fit['p_d7'] = prob_at(fit, [7])
    A[key] = fit
RES['migracao'] = A

# ================= B) Aptidão protege a prontidão =================
B = {}
sub = h.dropna(subset=['PVini']).copy(); sub['y'] = (sub.perfil == 'Iceberg').astype(int)
fpv = logit_fit(sub['PVini'].values, sub['y'].values)
lo, hi = boot_or(sub, ['PVini'], 'y')
fpv['OR_pv'] = fpv['OR'][0]; fpv['OR_lo'], fpv['OR_hi'] = lo, hi
B['iceberg_pv'] = fpv
# modelo ajustado: dia + PV
sub2 = h.dropna(subset=['PVini', 'dia']).copy(); sub2['y'] = (sub2.perfil == 'Iceberg').astype(int)
fadj = logit_fit(sub2[['dia', 'PVini']].values, sub2['y'].values)
fadj['OR_dia'] = fadj['OR'][0]; fadj['OR_pv'] = fadj['OR'][1]
B['iceberg_adj'] = fadj
RES['aptidao'] = B

# ================= C) Limiar de baixo vigor ~ PV =================
dm = h.groupby(['ID', 'dia']).agg(Vigor=('Vigor', 'mean'), PVini=('PVini', 'first')).reset_index()
dd = dm.dropna(subset=['Vigor', 'PVini']).copy()
cut = dd.Vigor.quantile(1 / 3)                        # tercil INFERIOR de vigor = "baixo vigor"
dd['lo'] = (dd.Vigor <= cut).astype(int)
fv = logit_fit((-dd['PVini']).values, dd['lo'].values)   # sinal invertido: menor PV -> maior risco
yt = youden(dd['PVini'].values, dd['lo'].values)          # corte sobre PV (regra x<=t prediz baixo vigor)
# OR por km/h a partir do modelo direto sobre PV
fv_dir = logit_fit(dd['PVini'].values, dd['lo'].values)
ids = dd.ID.unique(); rng = np.random.default_rng(2024); aucs = []
def auc_mw(score, label):
    s = np.asarray(score, float); y = np.asarray(label); pos = s[y == 1]; neg = s[y == 0]
    if not len(pos) or not len(neg): return np.nan
    return float(stats.mannwhitneyu(pos, neg).statistic / (len(pos) * len(neg)))
for _ in range(1000):
    s = rng.choice(ids, len(ids), True); g = pd.concat([dd[dd.ID == i] for i in s])
    aucs.append(auc_mw(-g['PVini'], g['lo']))
alo, ahi = np.nanpercentile(aucs, [2.5, 97.5])
RES['baixo_vigor'] = dict(cut=float(cut), thr=yt[0], sens=yt[2], spec=yt[3],
                          OR_kmh=float(np.exp(fv_dir['b'][1])),
                          auc=auc_mw(-dd['PVini'], dd['lo']), auc_lo=float(alo), auc_hi=float(ahi),
                          mcfadden=fv_dir['mcfadden'], aic=fv_dir['aic'], bic=fv_dir['bic'],
                          ll=fv_dir['ll'], n=int(len(dd)), events=int(dd['lo'].sum()))

# ================= D) Dia de PTH elevada ~ dia =================
sub = h.dropna(subset=['dia', 'TMD']).copy()
cutp = sub['TMD'].quantile(2 / 3)                      # tercil SUPERIOR de PTH = "PTH elevada"
sub['y'] = (sub['TMD'] >= cutp).astype(int)
fp = logit_fit(sub['dia'].values, sub['y'].values)
lo, hi = boot_or(sub, ['dia'], 'y')
fp['OR_dia'] = fp['OR'][0]; fp['OR_lo'], fp['OR_hi'] = lo, hi
fp['p_d1'] = prob_at(fp, [1]); fp['p_d7'] = prob_at(fp, [7]); fp['cut'] = float(cutp)
RES['pth_dia'] = fp

json.dump(RES, open('logistica.json', 'w'), indent=1, ensure_ascii=False)

# ---------------- relatório ----------------
print('A) MIGRAÇÃO DE PERFIL ~ DIA')
for key, lab in [('iceberg', 'Iceberg'), ('barbatana', 'Barbatana de tubarão')]:
    f = A[key]
    print('  %-20s OR/dia=%.2f [%.2f-%.2f]  P(D1)=%.2f P(D7)=%.2f  McFadden=%.3f AUC=%.2f (ev=%d)'
          % (lab, f['OR_dia'], f['OR_lo'], f['OR_hi'], f['p_d1'], f['p_d7'], f['mcfadden'], f['auc'], f['events']))
print('B) APTIDÃO -> PRONTIDÃO (iceberg)')
print('  P(iceberg) ~ PV      OR/km-h=%.2f [%.2f-%.2f]  McFadden=%.3f AUC=%.2f'
      % (B['iceberg_pv']['OR_pv'], B['iceberg_pv']['OR_lo'], B['iceberg_pv']['OR_hi'],
         B['iceberg_pv']['mcfadden'], B['iceberg_pv']['auc']))
print('  Ajustado dia+PV      OR/dia=%.2f  OR/km-h=%.2f  McFadden=%.3f'
      % (B['iceberg_adj']['OR_dia'], B['iceberg_adj']['OR_pv'], B['iceberg_adj']['mcfadden']))
c = RES['baixo_vigor']
print('C) LIMIAR DE BAIXO VIGOR ~ PV')
print('  OR/km-h=%.2f  limiar(Youden)=%.1f km/h (sens=%.2f esp=%.2f)  AUC=%.2f [%.2f-%.2f] McFadden=%.3f (ev=%d/%d)'
      % (c['OR_kmh'], c['thr'], c['sens'], c['spec'], c['auc'], c['auc_lo'], c['auc_hi'], c['mcfadden'], c['events'], c['n']))
p = RES['pth_dia']
print('D) DIA DE PTH ELEVADA ~ DIA')
print('  OR/dia=%.2f [%.2f-%.2f]  P(D1)=%.2f P(D7)=%.2f  McFadden=%.3f AUC=%.2f (ev=%d/%d)'
      % (p['OR_dia'], p['OR_lo'], p['OR_hi'], p['p_d1'], p['p_d7'], p['mcfadden'], p['auc'], p['events'], p['n']))
