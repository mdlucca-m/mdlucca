import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')

# ===================== 1) VIOLIN PLOT + BOX + MÉDIA (PTH por dia) =====================
days=list(range(1,8))
f=go.Figure()
for d in days:
    y=h[h.dia==d]['TMD'].dropna().values
    f.add_trace(go.Violin(y=y,x=[d]*len(y),name='Dia %d'%d,
        line=dict(color='#5f3dc4',width=2.4),fillcolor='rgba(112,72,232,0.35)',
        box_visible=True,meanline_visible=True,points=False,width=0.85,showlegend=False))
    f.add_trace(go.Scatter(x=[d],y=[float(np.mean(y))],mode='markers',
        marker=dict(symbol='diamond',size=11,color='white',line=dict(color='#5f3dc4',width=2.4)),
        showlegend=False,hoverinfo='skip'))
f.add_trace(go.Scatter(x=[None],y=[None],mode='markers',marker=dict(symbol='diamond',size=11,color='white',
    line=dict(color='#5f3dc4',width=2.4)),name='média'))
f.update_layout(template='mdpi',title=dict(text='<b>Distribuição da PTH por dia (violino + caixa + média)</b>',font=dict(size=16)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=60,r=20,t=56,b=76),legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center'))
f.update_yaxes(title='PTH (escore)',showgrid=False,zeroline=True,zerolinecolor='#ced4da')
f.update_xaxes(title='Dia do microciclo',dtick=1,showgrid=False,zeroline=False)
f.write_image(f'{OUT}/tec_violin.png',width=1400,height=820,scale=3)
print('OK tec_violin.png')

# ===================== 2) DISTRIBUIÇÃO ACUMULADA (ECDF) — Dia 1 vs Dia 4 vs Dia 7 =====================
f=go.Figure()
COLS={1:'#1971c2',4:'#868e96',7:'#e8590c'}
for d in [1,4,7]:
    y=np.sort(h[h.dia==d]['TMD'].dropna().values)
    cy=np.arange(1,len(y)+1)/len(y)
    xs=np.repeat(y,2)[1:]; ys=np.repeat(cy,2)[:-1]   # degraus
    f.add_trace(go.Scatter(x=np.r_[y[0],xs],y=np.r_[0,ys],mode='lines',line=dict(color=COLS[d],width=5,shape='hv'),
        name='Dia %d'%d))
f.add_vline(x=0,line=dict(color='#ced4da',width=1,dash='dash'))
f.update_layout(template='mdpi',title=dict(text='<b>Distribuição acumulada da PTH: Dia 1 vs Dia 4 vs Dia 7</b>',font=dict(size=16)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=60,r=20,t=56,b=76),legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center'))
f.update_yaxes(title='Proporção acumulada',range=[-0.02,1.02],showgrid=False,zeroline=False)
f.update_xaxes(title='PTH (escore)',showgrid=False,zeroline=False)
f.write_image(f'{OUT}/tec_ecdf.png',width=1400,height=800,scale=3)
print('OK tec_ecdf.png')

# ===================== 3) PICOS SINALIZADOS (stat_peaks) na trajetória da fadiga =====================
from scipy.signal import argrelextrema
dd=h.dropna(subset=['dia']).groupby('dia')['Fadiga'].mean()
x=dd.index.values.astype(float); y=dd.values
f=go.Figure()
f.add_trace(go.Scatter(x=x,y=y,mode='lines+markers',line=dict(color='#e8590c',width=6),
    marker=dict(size=9,color='#e8590c',line=dict(color='white',width=1)),showlegend=False))
# picos locais (máximos) + valor
idx=argrelextrema(y,np.greater_equal,order=1)[0]
idx=[i for i in idx if 0<i<len(y)-1] + ([int(np.argmax(y))] if np.argmax(y) in (0,len(y)-1) else [])
for i in sorted(set(idx)):
    f.add_trace(go.Scatter(x=[x[i]],y=[y[i]],mode='markers',marker=dict(size=11,color='#a51111'),showlegend=False))
    f.add_annotation(x=x[i],y=y[i],text='<b>%.1f</b>'%y[i],showarrow=False,yshift=15,font=dict(size=12,color='#a51111'))
f.update_layout(template='mdpi',title=dict(text='<b>Picos sinalizados na trajetória da fadiga</b>',font=dict(size=16)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=60,r=20,t=56,b=48))
f.update_yaxes(title='Fadiga (escore)',showgrid=False,zeroline=False)
f.update_xaxes(title='Dia do microciclo',dtick=1,showgrid=False,zeroline=False)
f.write_image(f'{OUT}/tec_picos.png',width=1400,height=760,scale=3)
print('OK tec_picos.png')
