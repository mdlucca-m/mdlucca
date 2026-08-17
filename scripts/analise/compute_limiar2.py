"""
Dois limiares para o pico de velocidade (PV) do T-CAR -> três faixas de aptidão.

Em vez de um único ponto de corte binário (Youden), definem-se DOIS limiares no PV,
pelos tercis da distribuição do PV na amostra, criando três faixas de decisão:
  - Baixa aptidão   (PV < t1)     -> maior risco
  - Aptidão média   (t1 <= PV <= t2)
  - Alta aptidão    (PV > t2)      -> menor risco
Para cada faixa reporta-se a prevalência de dias de FADIGA FÍSICA elevada (tercil
superior) e de BAIXO VIGOR (tercil inferior). A tendência da prevalência ao longo das
faixas ordenadas é testada pelo teste de Cochran-Armitage (linear-by-linear).
Observação: por serem observações atleta-dia (medidas repetidas), o teste de tendência
é interpretado como descritivo; a inferência formal apoia-se na razão de chances
contínua da regressão logística (com IC bootstrap por atleta) já reportada.
Saída: limiar2.json
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats

h = pd.read_csv('hum_prof.csv')
F = pd.read_csv('tcar2_features.csv')[['ID', 'PVini']]

# base atleta-dia (média das coletas do dia) com PV do T-CAR1
base = h.groupby(['ID', 'dia']).agg(Fad=('FadFisica', 'mean'), Vig=('Vigor', 'mean')).reset_index()
base = base.merge(F, on='ID', how='left').dropna(subset=['PVini'])

# DOIS limiares = tercis da distribuição do PV
t1, t2 = [float(v) for v in np.quantile(base.PVini.values, [1/3, 2/3])]

def cochran_armitage(y, g):
    """Teste de tendência linear em proporções (escores 0,1,2 para as faixas). Retorna z, p."""
    y = np.asarray(y); g = np.asarray(g)
    N = len(y); R = y.sum(); scores = g.astype(float)
    # estatística de tendência
    n_k = np.array([np.sum(g == k) for k in (0, 1, 2)])
    r_k = np.array([np.sum(y[g == k]) for k in (0, 1, 2)])
    s = np.array([0., 1., 2.])
    T = np.sum(s * (r_k - n_k * R / N))
    p_bar = R / N
    var = p_bar * (1 - p_bar) * (np.sum(n_k * s**2) - (np.sum(n_k * s)**2) / N)
    z = T / np.sqrt(var) if var > 0 else np.nan
    p = 2 * (1 - stats.norm.cdf(abs(z))) if np.isfinite(z) else np.nan
    return float(z), float(p)

def analyse(col, q, direction, youden_thr):
    v = base[col].values
    y = (v >= np.quantile(v, q)).astype(int) if direction == 'hi' else (v <= np.quantile(v, q)).astype(int)
    x = base.PVini.values
    g = np.where(x < t1, 0, np.where(x <= t2, 1, 2))     # faixa 0/1/2
    bands = []
    for k, lab, rng in [(0, 'Baixa aptidão', 'PV < %.1f' % t1),
                        (1, 'Aptidão média', '%.1f–%.1f' % (t1, t2)),
                        (2, 'Alta aptidão', 'PV > %.1f' % t2)]:
        mask = g == k; n = int(mask.sum()); ev = int(y[mask].sum())
        bands.append(dict(lab=lab, rng=rng, n=n, ev=ev, prev=float(100 * ev / n) if n else float('nan')))
    z, p = cochran_armitage(y, g)
    return dict(bands=bands, prev_geral=float(100 * y.mean()), trend_z=z, trend_p=p,
                youden=float(youden_thr), n=int(len(base)), events=int(y.sum()))

# limiar único de Youden já reportado (para contraste): fadiga ~15.0 ; baixo vigor 14.9
LIM = json.load(open('tcar_limiar.json'))
you_fad = LIM['LIM']['PVini']['thr']
you_vig = 14.9  # do compute_logistica (limiar de baixo vigor)

RES = dict(t1=t1, t2=t2,
           fadiga=analyse('Fad', 2/3, 'hi', you_fad),
           vigor=analyse('Vig', 1/3, 'lo', you_vig))
json.dump(RES, open('limiar2.json', 'w'), indent=1, ensure_ascii=False)

print('DOIS LIMIARES DE PV (tercis): t1 = %.1f km/h | t2 = %.1f km/h' % (t1, t2))
for key, nm in [('fadiga', 'Dias de FADIGA física elevada'), ('vigor', 'Dias de BAIXO VIGOR')]:
    r = RES[key]
    print('\n%s (prev. geral %.0f%%; Youden único = %.1f km/h; tendência p = %.3f):'
          % (nm, r['prev_geral'], r['youden'], r['trend_p']))
    for b in r['bands']:
        print('   %-14s %-12s n=%3d  prevalência = %4.0f%%' % (b['lab'], b['rng'], b['n'], b['prev']))
