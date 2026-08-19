import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); ADV=json.load(open('adv.json'))
CV='#2f9e44'; CF='#e8590c'
seq=[(1,'baseline',1.0)]
for d in range(2,8): seq+=[(d,'pre',d-0.2),(d,'pos',d+0.2)]
x=np.array([xx for _,_,xx in seq])
def cm(k): return np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m,_ in seq])
yv=cm('Vigor'); yf=cm('Fadiga')
sv=UnivariateSpline(x,yv,k=4,s=len(x)*np.var(yv)*0.85)
sf=UnivariateSpline(x,yf,k=4,s=len(x)*np.var(yf)*0.85)
xd=np.linspace(x.min(),x.max(),400)
V=sv(xd); F=sf(xd); D=V-F
cr=ADV['vf_cross']; xc_last=ADV['vf_last']['x']
# regiao de zoom: em torno do ultimo cruzamento (definitivo)
zlo,zhi=max(x.min(),xc_last-1.6),x.max()

f=make_subplots(rows=2,cols=1,vertical_spacing=0.13,row_heights=[0.5,0.5],
    subplot_titles=['<b>Vigor e fadiga: área sombreada entre as curvas (semana completa)</b>',
                    '<b>Zoom: diferença suavizada vigor − fadiga (área sombreada das derivadas do gap)</b>'])
# ---------- PAINEL 1: curvas + area sombreada entre elas ----------
# area verde onde vigor>fadiga, laranja onde fadiga>vigor (dois traços com fill='tonexty')
f.add_trace(go.Scatter(x=xd,y=np.maximum(V,F),mode='lines',line=dict(width=0),showlegend=False,hoverinfo='skip'),1,1)
f.add_trace(go.Scatter(x=xd,y=np.minimum(V,F),mode='lines',line=dict(width=0),fill='tonexty',
    fillcolor='rgba(134,142,150,0.18)',showlegend=False,hoverinfo='skip'),1,1)
f.add_trace(go.Scatter(x=xd,y=V,mode='lines',line=dict(color=CV,width=6),name='Vigor'),1,1)
f.add_trace(go.Scatter(x=xd,y=F,mode='lines',line=dict(color=CF,width=6),name='Fadiga'),1,1)
for c in cr:
    f.add_trace(go.Scatter(x=[c['x']],y=[c['y']],mode='markers',marker=dict(symbol='diamond',size=14,
        color='#212529',line=dict(color='white',width=2)),showlegend=False),1,1)
    f.add_annotation(x=c['x'],y=c['y'],text='dia %.1f'%c['x'],showarrow=False,yshift=-16,font=dict(size=10,color='#212529'),row=1,col=1)
f.add_vrect(x0=zlo,x1=zhi,fillcolor='#7048e8',opacity=0.05,line_width=0,layer='below',row=1,col=1)
f.add_annotation(x=(zlo+zhi)/2,y=max(V.max(),F.max()),text='região ampliada ↓',showarrow=False,
    font=dict(size=10.5,color='#5f3dc4'),row=1,col=1)
f.update_yaxes(title='Escore (0–16)',showgrid=False,zeroline=False,row=1,col=1)
f.update_xaxes(title='',dtick=1,range=[x.min()-0.1,x.max()+0.1],showgrid=False,zeroline=False,row=1,col=1)
# ---------- PAINEL 2: zoom da diferenca V-F com area sombreada ao zero ----------
m=(xd>=zlo)&(xd<=zhi); xz=xd[m]; Dz=D[m]
f.add_trace(go.Scatter(x=xz,y=np.where(Dz>=0,Dz,0),mode='lines',line=dict(width=0),fill='tozeroy',
    fillcolor='rgba(47,158,68,0.30)',showlegend=False,hoverinfo='skip'),2,1)
f.add_trace(go.Scatter(x=xz,y=np.where(Dz<0,Dz,0),mode='lines',line=dict(width=0),fill='tozeroy',
    fillcolor='rgba(232,89,12,0.30)',showlegend=False,hoverinfo='skip'),2,1)
f.add_trace(go.Scatter(x=xz,y=Dz,mode='lines',line=dict(color='#5f3dc4',width=5),name='Vigor − fadiga'),2,1)
f.add_hline(y=0,line=dict(color='#495057',width=1.6),row=2,col=1)
# cruzamentos dentro do zoom
for c in cr:
    if zlo<=c['x']<=zhi:
        f.add_trace(go.Scatter(x=[c['x']],y=[0],mode='markers',marker=dict(size=14,color='#212529',
            line=dict(color='white',width=2)),showlegend=False),2,1)
        f.add_annotation(x=c['x'],y=0,text='<b>cruzamento<br>dia %.1f</b>'%c['x'],showarrow=True,arrowhead=0,
            ax=0,ay=-34,font=dict(size=11,color='#212529'),bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#212529',borderwidth=1,borderpad=3,row=2,col=1)
f.add_annotation(x=zlo+0.05,y=max(Dz)*0.8,text='vigor domina',showarrow=False,xanchor='left',font=dict(size=11,color=CV),row=2,col=1)
f.add_annotation(x=zhi-0.05,y=min(Dz)*0.8,text='fadiga domina',showarrow=False,xanchor='right',font=dict(size=11,color=CF),row=2,col=1)
pad=(Dz.max()-Dz.min())*0.18+0.3
f.update_yaxes(title='Diferença de escore',range=[Dz.min()-pad,Dz.max()+pad],showgrid=False,zeroline=False,row=2,col=1)
f.update_xaxes(title='Dia do microciclo',dtick=0.5,range=[zlo,zhi],showgrid=False,zeroline=False,row=2,col=1)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=62,r=24,t=60,b=52),
    legend=dict(orientation='h',y=1.10,x=0.5,xanchor='center',font=dict(size=12),
        bgcolor='rgba(255,255,255,0.7)',bordercolor='#dee2e6',borderwidth=1))
f.write_image(f'{OUT}/deriv_zoom.png',width=1500,height=1080,scale=3)
print('OK deriv_zoom.png | zoom',round(zlo,2),'-',round(zhi,2),'| cruzamento definitivo dia',round(xc_last,2))
