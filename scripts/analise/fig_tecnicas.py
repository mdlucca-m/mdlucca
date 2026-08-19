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
    f.add_trace(go.Violin(y=y,x=[d]*len(y),name='Dia %d'%d,spanmode='hard',
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
f.update_yaxes(title='PTH (escore)',range=[-15,30],showgrid=False,zeroline=True,zerolinecolor='#ced4da')
f.update_xaxes(title='Dia do microciclo',dtick=1,showgrid=False,zeroline=False)
f.add_annotation(x=0.99,y=0.98,xref='paper',yref='paper',text='escala ajustada (foco na distribuição; caudas extremas fora do eixo)',
    showarrow=False,xanchor='right',font=dict(size=10,color='#868e96'))
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
f.update_xaxes(title='PTH (escore)',range=[-13,32],showgrid=False,zeroline=False)
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

# ===================== 4) ZOOM (recorte ampliado da fase de acúmulo) =====================
from plotly.subplots import make_subplots
ddP=h.dropna(subset=['dia']).groupby('dia')['TMD'].mean()
xf=ddP.index.values.astype(float); yf=ddP.values
# 12 pontos pre/pos para o zoom
gp=h.dropna(subset=['dia']).groupby(['dia','momento'])['TMD'].mean().reset_index()
zx=[]; zy=[]
for d in range(4,8):
    for mo,off in [('pre',-0.2),('pos',0.2)]:
        rr=gp[(gp.dia==d)&(gp.momento==mo)]
        if len(rr): zx.append(d+off); zy.append(float(rr['TMD'].iloc[0]))
f=make_subplots(rows=2,cols=1,vertical_spacing=0.14,row_heights=[0.42,0.58],
    subplot_titles=['<b>Semana completa</b>','<b>Recorte ampliado: fase de acúmulo (dias 4–7, pré/pós)</b>'])
# topo: semana completa + regiao do zoom destacada
f.add_vrect(x0=3.6,x1=7.2,fillcolor='#e8590c',opacity=0.08,line_width=0,layer='below',row=1,col=1)
f.add_trace(go.Scatter(x=xf,y=yf,mode='lines+markers',line=dict(color='#7048e8',width=5),
    marker=dict(size=8,color='#7048e8',line=dict(color='white',width=1)),showlegend=False),1,1)
f.add_annotation(x=5.4,y=max(yf),text='recorte ampliado ↓',showarrow=False,font=dict(size=11,color='#c0410b'),row=1,col=1)
# base: zoom com detalhe pre/pos
f.add_trace(go.Scatter(x=zx,y=zy,mode='lines+markers',line=dict(color='#7048e8',width=6),
    marker=dict(size=11,color='#7048e8',line=dict(color='white',width=1.4)),showlegend=False),2,1)
for xi,yi,d in zip(zx,zy,[4,4,5,5,6,6,7,7]):
    pass
f.update_xaxes(title='Dia',dtick=1,range=[0.8,7.2],showgrid=False,zeroline=False,row=1,col=1)
f.update_xaxes(title='Dia (pré/pós)',dtick=1,range=[3.6,7.2],showgrid=False,zeroline=False,row=2,col=1)
f.update_yaxes(title='PTH',showgrid=False,zeroline=False,row=1,col=1)
f.update_yaxes(title='PTH',showgrid=False,zeroline=False,row=2,col=1)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=58,r=20,t=52,b=48),showlegend=False)
f.write_image(f'{OUT}/tec_zoom.png',width=1400,height=980,scale=3)
print('OK tec_zoom.png')

# ===================== 5) REGRESSÃO POR GRUPO (vigor x fadiga, por fase) =====================
d=h.dropna(subset=['Vigor','Fadiga','dia']).copy()
d['fase']=np.where(d.dia<=4,'Início (dias 1–4)','Acúmulo (dias 5–7)')
COLF={'Início (dias 1–4)':'#1971c2','Acúmulo (dias 5–7)':'#e8590c'}
f=go.Figure()
for fase,col in COLF.items():
    sub=d[d.fase==fase]; xx=sub.Vigor.values.astype(float); yy=sub.Fadiga.values.astype(float)
    f.add_trace(go.Scatter(x=xx,y=yy,mode='markers',marker=dict(size=8,color=col,opacity=0.45,line=dict(color='white',width=0.6)),
        name=fase))
    b1,b0=np.polyfit(xx,yy,1); xr=np.array([xx.min(),xx.max()])
    r=np.corrcoef(xx,yy)[0,1]
    f.add_trace(go.Scatter(x=xr,y=b0+b1*xr,mode='lines',line=dict(color=col,width=6),showlegend=False))
    f.add_annotation(x=xr[1],y=b0+b1*xr[1],text='r = %+.2f'%r,showarrow=False,xanchor='left',xshift=6,font=dict(size=12,color=col))
f.update_layout(template='mdpi',title=dict(text='<b>Relação vigor × fadiga por fase do microciclo (regressão por grupo)</b>',font=dict(size=15)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=60,r=20,t=54,b=76),legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center'))
f.update_yaxes(title='Fadiga (escore)',showgrid=False,zeroline=False)
f.update_xaxes(title='Vigor (escore)',showgrid=False,zeroline=False)
f.write_image(f'{OUT}/tec_regr.png',width=1300,height=860,scale=3)
print('OK tec_regr.png')
