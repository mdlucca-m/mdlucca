"""
(a) Rede psicométrica (gaussian graphical model) das dimensões do BRUMS sob carga:
    compara a rede de correlações parciais no dia descansado (Dia 1) e no dia de
    maior carga (Dia 7); formaliza o "fechamento do perfil" (acoplamento crescente
    entre fadiga e afeto negativo) via força global e teste de permutação.
(b) Robustez ordinal: modelo de odds proporcionais (cumulative link) do dia sobre
    a fadiga e o vigor categorizados em tercis, respeitando a natureza ordinal e o
    efeito-piso das subescalas.

Saídas: network.json ; figuras/rede_humor.png
"""
import os; os.environ['BROWSER_PATH'] = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from numpy.linalg import inv
from statsmodels.miscmodels.ordinal_model import OrderedModel
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT = '/home/user/mdlucca/Artigos/figuras'
rng = np.random.default_rng(2024)

h = pd.read_csv('hum_prof.csv')
DIMS = ['Tensao', 'Depressao', 'Raiva', 'Vigor', 'Fadiga', 'Confusao']
LAB = ['Tensão', 'Depressão', 'Raiva', 'Vigor', 'Fadiga', 'Confusão']

def pcorr_matrix(df):
    Z = (df[DIMS] - df[DIMS].mean()) / df[DIMS].std()
    C = np.corrcoef(Z.values.T)
    P = inv(C + 1e-6 * np.eye(len(DIMS)))
    d = np.sqrt(np.diag(P))
    pc = -P / np.outer(d, d)
    np.fill_diagonal(pc, 0)
    return pc

# estado por atleta: Dia 1 (baseline) vs Dia 7 (média pré/pós)
d1 = h[h['dia'] == 1].groupby('ID')[DIMS].mean().reset_index()
d7 = h[h['dia'] == 7].groupby('ID')[DIMS].mean().reset_index()
ids = sorted(set(d1.ID) & set(d7.ID))
d1 = d1[d1.ID.isin(ids)].sort_values('ID'); d7 = d7[d7.ID.isin(ids)].sort_values('ID')

pc1, pc7 = pcorr_matrix(d1), pcorr_matrix(d7)
strength1 = float(np.abs(pc1).sum() / 2); strength7 = float(np.abs(pc7).sum() / 2)

# teste de permutação da diferença de força global (troca rótulos Dia1/Dia7 por atleta)
stacked = np.vstack([d1[DIMS].values, d7[DIMS].values]); n = len(ids)
obs_diff = strength7 - strength1
perm = []
for _ in range(5000):
    lab = rng.permutation(np.r_[np.zeros(n), np.ones(n)])
    A = pd.DataFrame(stacked[lab == 0], columns=DIMS); B = pd.DataFrame(stacked[lab == 1], columns=DIMS)
    perm.append(np.abs(pcorr_matrix(B)).sum() / 2 - np.abs(pcorr_matrix(A)).sum() / 2)
perm = np.array(perm); p_strength = float((np.abs(perm) >= abs(obs_diff)).mean())

# arestas fadiga–afeto negativo (índices)
iF = DIMS.index('Fadiga')
edges = {}
for tgt in ['Raiva', 'Depressao', 'Tensao']:
    j = DIMS.index(tgt)
    edges[tgt] = dict(dia1=float(pc1[iF, j]), dia7=float(pc7[iF, j]))

# ---- robustez ordinal (odds proporcionais; fadiga/vigor em tercis) ----
def ordinal_day(var):
    dd = h.dropna(subset=[var]).copy()
    q = dd[var].quantile([1/3, 2/3]).values
    dd['cat'] = np.digitize(dd[var], q)              # 0,1,2 (tercis)
    dd['dia_c'] = dd['dia'] - 1
    dd['pos'] = (dd['momento'] == 'pos').astype(float)   # acute pré→pós (baseline=0)
    m = OrderedModel(dd['cat'], dd[['dia_c', 'pos']], distr='logit').fit(method='bfgs', disp=False)
    def ci(name):
        c = float(m.params[name]); se = float(m.bse[name])
        return dict(logOR=c, OR=float(np.exp(c)), p=float(m.pvalues[name]),
                    OR_lo=float(np.exp(c - 1.96 * se)), OR_hi=float(np.exp(c + 1.96 * se)))
    return dict(dia=ci('dia_c'), pos=ci('pos'))

ordv = ordinal_day('Vigor'); ordf = ordinal_day('Fadiga')

res = dict(n=n, strength_d1=strength1, strength_d7=strength7, obs_diff=obs_diff,
           p_strength=p_strength, edges=edges,
           ordinal=dict(Vigor=ordv, Fadiga=ordf))
json.dump(res, open('network.json', 'w'), indent=1, ensure_ascii=False)
print('Força global: Dia1 %.2f | Dia7 %.2f | dif %.2f (p_perm=%.3f)' % (strength1, strength7, obs_diff, p_strength))
for t in edges: print('  Fadiga–%-10s Dia1 %+.2f -> Dia7 %+.2f' % (t, edges[t]['dia1'], edges[t]['dia7']))
for nm, o in [('Vigor', ordv), ('Fadiga', ordf)]:
    print('Ordinal %s: dia OR %.2f [%.2f,%.2f] p=%.3f | pós OR %.2f [%.2f,%.2f] p=%.3f' % (
        nm, o['dia']['OR'], o['dia']['OR_lo'], o['dia']['OR_hi'], o['dia']['p'],
        o['pos']['OR'], o['pos']['OR_lo'], o['pos']['OR_hi'], o['pos']['p']))

# ---- figura: duas redes lado a lado ----
ang = np.linspace(90, 90 - 360, len(DIMS), endpoint=False) * np.pi / 180
pos = {i: (np.cos(a), np.sin(a)) for i, a in enumerate(ang)}
def draw(fig, pc, c):
    mx = np.abs(pc).max()
    for i in range(len(DIMS)):
        for j in range(i + 1, len(DIMS)):
            w = pc[i, j]
            if abs(w) < 0.05: continue
            col = '#c92a2a' if w > 0 else '#1c7ed6'
            fig.add_trace(go.Scatter(x=[pos[i][0], pos[j][0]], y=[pos[i][1], pos[j][1]], mode='lines',
                line=dict(width=1 + 7 * abs(w) / mx, color=col), opacity=0.55, showlegend=False, hoverinfo='skip'), 1, c)
    hi = ['Vigor', 'Fadiga']
    fig.add_trace(go.Scatter(x=[pos[i][0] for i in range(len(DIMS))], y=[pos[i][1] for i in range(len(DIMS))],
        mode='markers+text', text=LAB, textposition='middle center', textfont=dict(size=11, color='white'),
        marker=dict(size=42, color=['#e8590c' if DIMS[i] in hi else '#495057' for i in range(len(DIMS))],
        line=dict(color='white', width=1.5)), showlegend=False, hoverinfo='skip'), 1, c)
    fig.update_xaxes(visible=False, range=[-1.4, 1.4], row=1, col=c)
    fig.update_yaxes(visible=False, range=[-1.4, 1.4], scaleanchor='x%d' % c if c > 1 else 'x', row=1, col=c)

fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.04,
    subplot_titles=['<b>Dia 1 — descansado (força %.2f)</b>' % strength1, '<b>Dia 7 — carga acumulada (força %.2f)</b>' % strength7])
draw(fig, pc1, 1); draw(fig, pc7, 2)
fig.update_layout(template='mdpi', font=dict(color='#1a1a1a', size=14, family='Arial'),
                  paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=10, r=10, t=52, b=10))
fig.write_image(f'{OUT}/rede_humor.png', width=1500, height=760, scale=3)
print('OK rede_humor.png')
