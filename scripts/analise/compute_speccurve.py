"""
Specification-curve (multiverse) dos limiares de pico de velocidade (Paper 2).
Varre o espaço de decisões analíticas — valor do limiar de PV, definição do dia
crítico, e forma do PV (bruto vs ajustado pela massa) — e mostra a robustez do
efeito (risco relativo de dia crítico abaixo vs acima do limiar) sob TODAS as
especificações. Também gera a figura da curva de especificação.

Saídas: speccurve.json ; figuras/spec_curve.png
"""
import os; os.environ['BROWSER_PATH'] = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT = '/home/user/mdlucca/Artigos/figuras'

h = pd.read_csv('hum_prof.csv')
pv = pd.read_csv('pv_wk.csv')[['ID', 'PVini']]
phys = pd.read_csv('phys.csv')[['ID', 'massa']]
d = h[h['momento'] != 'baseline'].merge(pv, on='ID').merge(phys, on='ID').dropna(subset=['PVini', 'FadFisica', 'Vigor'])
# PV ajustado pela massa (resíduo alométrico log-log)
b = np.polyfit(np.log(d['massa']), np.log(d['PVini']), 1)[0]
d['PV_adj'] = d['PVini'] / (d['massa'] ** b)

PV_forms = {'bruto': 'PVini', 'ajustado_massa': 'PV_adj'}
# limiares candidatos por forma
def thr_grid(x):
    q = np.quantile(x, [1/3, 0.5, 2/3])
    grid = list(np.round(np.quantile(x, np.linspace(0.25, 0.75, 9)), 3))
    return sorted(set([round(float(t), 3) for t in list(q) + grid]))
# definições de dia crítico
crit_defs = {
    'fadiga>mediana': lambda s: (s['FadFisica'] > s['FadFisica'].median()),
    'fadiga>=tercil_sup': lambda s: (s['FadFisica'] >= s['FadFisica'].quantile(2/3)),
    'vigor<mediana': lambda s: (s['Vigor'] < s['Vigor'].median()),
    'vigor<=tercil_inf': lambda s: (s['Vigor'] <= s['Vigor'].quantile(1/3)),
    'fadiga_alta_ou_vigor_baixo': lambda s: (s['FadFisica'] > s['FadFisica'].median()) | (s['Vigor'] < s['Vigor'].median()),
}
specs = []
for fname, fcol in PV_forms.items():
    x = d[fcol].values
    for thr in thr_grid(x):
        below = d[fcol].values < thr
        if below.sum() < 8 or (~below).sum() < 8:
            continue
        for cname, cfun in crit_defs.items():
            crit = cfun(d).values.astype(float)
            p_below = crit[below].mean(); p_above = crit[~below].mean()
            rr = (p_below + 1e-9) / (p_above + 1e-9)
            specs.append(dict(form=fname, thr=float(thr), crit=cname,
                              rr=float(rr), logrr=float(np.log(rr)),
                              p_below=float(p_below), p_above=float(p_above)))
S = pd.DataFrame(specs).sort_values('logrr').reset_index(drop=True)
res = dict(n_specs=int(len(S)), n_obs=int(len(d)), b_allo=float(b),
           median_rr=float(np.exp(S['logrr'].median())),
           frac_rr_gt1=float((S['rr'] > 1).mean()),
           rr_range=[float(S['rr'].min()), float(S['rr'].max())],
           by_form={f: float(np.exp(S[S.form == f]['logrr'].median())) for f in PV_forms})
json.dump(res, open('speccurve.json', 'w'), indent=1, ensure_ascii=False)
print('especificações:', len(S), '| RR mediano %.2f' % res['median_rr'],
      '| fração RR>1 %.0f%%' % (100 * res['frac_rr_gt1']),
      '| faixa RR [%.2f, %.2f]' % tuple(res['rr_range']))

# ---- figura: curva de especificação ----
col = ['#e8590c' if c.startswith('fadiga') else '#2f9e44' if c.startswith('vigor') else '#1c7ed6' for c in S['crit']]
f = make_subplots(rows=2, cols=1, row_heights=[0.62, 0.38], vertical_spacing=0.06, shared_xaxes=True,
                  subplot_titles=['<b>Curva de especificação — risco relativo de dia crítico (PV baixo vs alto)</b>',
                                  '<b>Especificações analíticas</b>'])
xs = np.arange(len(S))
f.add_trace(go.Scatter(x=xs, y=S['rr'], mode='markers', marker=dict(size=7, color=col, opacity=0.85,
            line=dict(color='white', width=0.6)), showlegend=False), 1, 1)
f.add_hline(y=1, line=dict(color='#495057', width=1.6, dash='dash'), row=1, col=1)
f.update_yaxes(title='Risco relativo (RR)', type='log', gridcolor='#eceef1', row=1, col=1)
# painel inferior: marca a forma do PV
form_y = {'bruto': 1, 'ajustado_massa': 0}
f.add_trace(go.Scatter(x=xs, y=[form_y[v] for v in S['form']], mode='markers',
            marker=dict(size=6, color='#343a40', symbol='line-ns-open'), showlegend=False), 2, 1)
f.update_yaxes(tickvals=[0, 1], ticktext=['PV ajust. massa', 'PV bruto'], row=2, col=1, range=[-0.5, 1.5])
f.update_xaxes(title='Especificação (ordenada pelo tamanho de efeito)', row=2, col=1, gridcolor='#eceef1')
f.update_layout(template='mdpi', font=dict(color='#1a1a1a', size=14, family='Arial'),
                paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=70, r=24, t=54, b=54), height=620)
f.write_image(f'{OUT}/spec_curve.png', width=1500, height=820, scale=3)
print('OK spec_curve.png')
