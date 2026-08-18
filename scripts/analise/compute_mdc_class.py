"""
Classificação individual por mudança confiável (Δ Dia 1 → Dia 7) frente à MDC,
para vigor e fadiga. Uma mudança é "real" quando |Δ| excede a mudança mínima
detectável (MDC90 = 1,65·√2·SEM). Direção interpretada pelo sentido de bem-estar:
  Vigor  ↑ além da MDC = melhora ; ↓ além da MDC = piora
  Fadiga ↑ além da MDC = piora   ; ↓ além da MDC = melhora
Saídas: mdc_class.json ; mdc_class_anon.csv ; figuras/mdc_individual.png
"""
import os; os.environ['BROWSER_PATH'] = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import json, numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT = '/home/user/mdlucca/Artigos/figuras'
MDC = json.load(open('mdc.json'))
h = pd.read_csv('hum_prof.csv')

d1 = h[h['dia'] == 1].groupby('ID')[['Vigor', 'Fadiga']].mean()
d7 = h[h['dia'] == 7].groupby('ID')[['Vigor', 'Fadiga']].mean()
ids = sorted(set(d1.index) & set(d7.index))
D = (d7.loc[ids] - d1.loc[ids]).rename(columns={'Vigor': 'dVigor', 'Fadiga': 'dFadiga'})

def classify(delta, mdc, higher_is_better):
    if abs(delta) < mdc: return 'estável'
    up = delta > 0
    good = up if higher_is_better else (not up)
    return 'melhora' if good else 'piora'

rows = []
mV, mF = MDC['Vigor']['mdc90'], MDC['Fadiga']['mdc90']
for a in ids:
    dv, df = float(D.loc[a, 'dVigor']), float(D.loc[a, 'dFadiga'])
    rows.append(dict(ID=a, dVigor=round(dv, 1), clsVigor=classify(dv, mV, True),
                     dFadiga=round(df, 1), clsFadiga=classify(df, mF, False)))
R = pd.DataFrame(rows)
R.to_csv('mdc_class_anon.csv', index=False)

def counts(col):
    c = R[col].value_counts().to_dict()
    return {k: int(c.get(k, 0)) for k in ['melhora', 'estável', 'piora']}
res = dict(n=len(R), mdc90=dict(Vigor=mV, Fadiga=mF),
           mdc95=dict(Vigor=MDC['Vigor']['mdc95'], Fadiga=MDC['Fadiga']['mdc95']),
           Vigor=counts('clsVigor'), Fadiga=counts('clsFadiga'),
           n_change_vigor=int((R.clsVigor != 'estável').sum()),
           n_change_fadiga=int((R.clsFadiga != 'estável').sum()),
           n_piora_ambos=int(((R.clsVigor == 'piora') & (R.clsFadiga == 'piora')).sum()))
json.dump(res, open('mdc_class.json', 'w'), indent=1, ensure_ascii=False)
print('n =', len(R))
print('Vigor  :', counts('clsVigor'), '| MDC90 =', round(mV, 1))
print('Fadiga :', counts('clsFadiga'), '| MDC90 =', round(mF, 1))
print('Piora em ambos:', res['n_piora_ambos'])
print(R.to_string(index=False))

# ---- figura: mudança individual ordenada, com banda da MDC ----
def panel(fig, col, mdc, higher_better, c, xlab):
    s = R.sort_values(col)
    colr = []
    for a, v in zip(s.ID, s[col]):
        cls = classify(v, mdc, higher_better)
        colr.append('#2f9e44' if cls == 'melhora' else '#e03131' if cls == 'piora' else '#adb5bd')
    fig.add_vrect(x0=-mdc, x1=mdc, fillcolor='#dee2e6', opacity=0.35, line_width=0, row=1, col=c)
    fig.add_vline(x=0, line=dict(color='#495057', width=1), row=1, col=c)
    fig.add_trace(go.Bar(y=s.ID, x=s[col], orientation='h', marker=dict(color=colr),
                         showlegend=False), 1, c)
    fig.update_xaxes(title=xlab, gridcolor='#eceef1', zeroline=False, row=1, col=c)
    fig.update_yaxes(gridcolor='#f1f3f5', row=1, col=c, tickfont=dict(size=8))

fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.10,
    subplot_titles=['<b>Vigor: Δ Dia 1 → Dia 7</b>', '<b>Fadiga: Δ Dia 1 → Dia 7</b>'])
panel(fig, 'dVigor', mV, True, 1, 'Δ Vigor (pontos) — faixa cinza = MDC90')
panel(fig, 'dFadiga', mF, False, 2, 'Δ Fadiga (pontos) — faixa cinza = MDC90')
fig.update_layout(template='mdpi', font=dict(color='#1a1a1a', size=13, family='Arial'),
                  paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=54, r=20, t=52, b=52),
                  height=760, bargap=0.35)
fig.write_image(f'{OUT}/mdc_individual.png', width=1500, height=820, scale=3)
print('OK mdc_individual.png')
