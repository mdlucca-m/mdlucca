import os; os.environ['BROWSER_PATH'] = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
import mdpi_style
OUT = '/home/user/mdlucca/Artigos/figuras'
h = pd.read_csv('hum_prof.csv')
L = json.load(open('logistica.json'))['pth_dia']

def logit(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float); b0, b1 = 0., 0.
    for _ in range(400):
        pr = 1 / (1 + np.exp(-(b0 + b1 * x))); W = pr * (1 - pr) + 1e-9
        g0 = np.sum(y - pr); g1 = np.sum((y - pr) * x)
        h00 = -np.sum(W); h01 = -np.sum(W * x); h11 = -np.sum(W * x * x); det = h00 * h11 - h01 * h01
        b0 -= (h11 * g0 - h01 * g1) / det; b1 -= (-h01 * g0 + h00 * g1) / det
    return b0, b1

sub = h.dropna(subset=['dia', 'TMD']).copy()
cut = sub['TMD'].quantile(2 / 3); sub['y'] = (sub['TMD'] >= cut).astype(int)
b0, b1 = logit(sub['dia'], sub['y'])
dd = np.linspace(1, 7, 200); pr = 1 / (1 + np.exp(-(b0 + b1 * dd)))
obs = sub.groupby('dia').agg(p=('y', 'mean'), n=('y', 'size'))

f = go.Figure()
f.add_trace(go.Scatter(x=dd, y=pr, mode='lines', line=dict(color='#1c7ed6', width=5), name='Curva logística'))
f.add_trace(go.Scatter(x=obs.index, y=obs.p, mode='markers',
    marker=dict(size=14, color='#1c7ed6', opacity=0.7, line=dict(color='white', width=1.3)),
    name='Proporção observada'))
f.add_annotation(x=0.03, y=0.96, xref='x domain', yref='y domain', showarrow=False, xanchor='left',
    text='OR = %s/dia (IC95%% %s–%s)' % (('%.2f' % L['OR_dia']).replace('.', ','),
        ('%.2f' % L['OR_lo']).replace('.', ','), ('%.2f' % L['OR_hi']).replace('.', ',')),
    font=dict(size=13, color='#1a1a1a'), bgcolor='rgba(255,255,255,0.82)')
f.update_xaxes(title='Dia do microciclo', dtick=1, gridcolor='#eceef1', zeroline=False)
f.update_yaxes(title='P(dia de PTH elevada)', range=[-0.03, 0.7], gridcolor='#eceef1', zeroline=False)
f.update_layout(template='mdpi', title=dict(text='<b>Probabilidade de um dia de Perturbação Total do Humor elevada ao longo do microciclo</b>', font=dict(size=15)),
    font=dict(color='#1a1a1a', size=14, family='Arial'), paper_bgcolor='white', plot_bgcolor='white',
    margin=dict(l=64, r=26, t=58, b=54), legend=dict(orientation='h', y=1.02, x=0.5, xanchor='center', font=dict(size=12)))
f.write_image(f'{OUT}/pth_logistic.png', width=1100, height=560, scale=3)
print('OK pth_logistic.png | OR/dia=%.2f [%.2f-%.2f] P(D1)=%.2f P(D7)=%.2f' % (
    L['OR_dia'], L['OR_lo'], L['OR_hi'], L['p_d1'], L['p_d7']))
