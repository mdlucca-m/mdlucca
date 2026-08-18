import os; os.environ['BROWSER_PATH'] = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import plotly.graph_objects as go
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import mdpi_style
OUT = '/home/user/mdlucca/Artigos/figuras'
h = pd.read_csv('hum_prof.csv')
DIMS = ['Tensao', 'Depressao', 'Raiva', 'Vigor', 'Fadiga', 'Confusao']
LAB = ['Tensão', 'Depressão', 'Raiva', 'Vigor', 'Fadiga', 'Confusão']
d = h.dropna(subset=DIMS + ['TMD']).copy()
Z = StandardScaler().fit_transform(d[DIMS])
p = PCA().fit(Z); sc = p.transform(Z)
ev = p.explained_variance_; vr = p.explained_variance_ratio_
load = (p.components_.T * np.sqrt(ev))            # cargas de correlação (6×k)
# escala das setas para caber sobre os escores
sx = 0.9 * np.abs(sc[:, 0]).max() / np.abs(load[:, 0]).max()
sy = 0.9 * np.abs(sc[:, 1]).max() / np.abs(load[:, 1]).max()
s = min(sx, sy)

f = go.Figure()
# escores coloridos pela PTH (perturbação total) -> mostra que PC1 = eixo de perturbação
f.add_trace(go.Scatter(x=sc[:, 0], y=sc[:, 1], mode='markers',
    marker=dict(size=8, color=d['TMD'], colorscale='RdBu_r', showscale=True, opacity=0.72,
        line=dict(color='white', width=0.6),
        colorbar=dict(title='PTH', thickness=14, len=0.7)),
    name='Observações', hoverinfo='skip'))
# vetores de carga
for i, l in enumerate(LAB):
    col = '#2f9e44' if DIMS[i] == 'Vigor' else '#e8590c' if DIMS[i] == 'Fadiga' else '#495057'
    f.add_annotation(x=load[i, 0] * s, y=load[i, 1] * s, ax=0, ay=0, xref='x', yref='y', axref='x', ayref='y',
        showarrow=True, arrowhead=2, arrowsize=1.1, arrowwidth=2.4, arrowcolor=col)
    f.add_annotation(x=load[i, 0] * s * 1.12, y=load[i, 1] * s * 1.12, text='<b>%s</b>' % l,
        showarrow=False, font=dict(size=13, color=col))
f.add_hline(y=0, line=dict(color='#ced4da', width=1)); f.add_vline(x=0, line=dict(color='#ced4da', width=1))
f.update_layout(template='mdpi', title=dict(text='<b>Biplot da PCA das seis dimensões do BRUMS</b>', font=dict(size=16)),
    font=dict(color='#1a1a1a', size=14, family='Arial'), paper_bgcolor='white', plot_bgcolor='white',
    xaxis=dict(title='PC1 (%.0f%%) — perturbação geral' % (100 * vr[0]), gridcolor='#eceef1', zeroline=False),
    yaxis=dict(title='PC2 (%.0f%%) — ativação' % (100 * vr[1]), gridcolor='#eceef1', zeroline=False),
    margin=dict(l=60, r=20, t=56, b=54), showlegend=False)
f.write_image(f'{OUT}/pca_biplot.png', width=1160, height=780, scale=3)
print('OK pca_biplot.png | PC1 %.0f%% PC2 %.0f%%' % (100 * vr[0], 100 * vr[1]))
