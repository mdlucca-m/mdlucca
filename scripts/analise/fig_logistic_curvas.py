import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); F=pd.read_csv('tcar2_features.csv')[['ID','PVini']]
def logit(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float); b0,b1=0.,0.
    for _ in range(400):
        pr=1/(1+np.exp(-(b0+b1*x))); W=pr*(1-pr)+1e-9
        g0=np.sum(y-pr); g1=np.sum((y-pr)*x); h00=-np.sum(W); h01=-np.sum(W*x); h11=-np.sum(W*x*x); det=h00*h11-h01*h01
        b0-=(h11*g0-h01*g1)/det; b1-=(-h01*g0+h00*g1)/det
    return b0,b1

f=make_subplots(rows=1,cols=2,horizontal_spacing=0.11,
    subplot_titles=['<b>P(dia de fadiga elevada) × pico de velocidade</b>','<b>P(perfil barbatana de tubarão) × dia</b>'])

# --- A: P(fadiga elevada) ~ PV ---
dm=h.groupby(['ID','dia']).agg(Fad=('FadFisica','mean')).reset_index().merge(F,on='ID').dropna(subset=['PVini'])
cut=dm.Fad.quantile(2/3); dm['hi']=(dm.Fad>=cut).astype(int)
b0,b1=logit(dm.PVini,dm.hi); xx=np.linspace(dm.PVini.min(),dm.PVini.max(),200); pr=1/(1+np.exp(-(b0+b1*xx)))
# proporção observada por faixa (binned) para pontos
dm['bin']=pd.cut(dm.PVini,6); binp=dm.groupby('bin').agg(x=('PVini','mean'),p=('hi','mean'),n=('hi','size')).dropna()
f.add_trace(go.Scatter(x=xx,y=pr,mode='lines',line=dict(color='#e8590c',width=5),name='Curva logística',showlegend=True),1,1)
f.add_trace(go.Scatter(x=binp.x,y=binp.p,mode='markers',marker=dict(size=(binp.n*1.6+6),color='#e8590c',opacity=0.55,
    line=dict(color='white',width=1.2)),name='Proporção observada',showlegend=True),1,1)
thr=-b0/b1
f.add_vline(x=thr,line=dict(color='#212529',width=2.5,dash='dash'),row=1,col=1)
f.add_annotation(x=thr,y=0.92,text='limiar 50%%<br>%.1f km/h'%thr,showarrow=False,font=dict(size=12,color='#212529'),row=1,col=1)
f.update_xaxes(title='Pico de velocidade — T-CAR (km/h)',gridcolor='#eceef1',zeroline=False,row=1,col=1)
f.update_yaxes(title='Probabilidade',range=[-0.03,1.03],gridcolor='#eceef1',zeroline=False,row=1,col=1)

# --- B: P(barbatana) ~ dia ---
h2=h.dropna(subset=['dia']).copy(); h2['y']=(h2.perfil=='Barbatana tubarão').astype(int)
b0,b1=logit(h2.dia,h2.y); dd=np.linspace(1,7,200); pr2=1/(1+np.exp(-(b0+b1*dd)))
obs=h2.groupby('dia').agg(p=('y','mean'),n=('y','size'))
f.add_trace(go.Scatter(x=dd,y=pr2,mode='lines',line=dict(color='#1971c2',width=5),name='Curva logística',showlegend=False),1,2)
f.add_trace(go.Scatter(x=obs.index,y=obs.p,mode='markers',marker=dict(size=13,color='#1971c2',opacity=0.7,
    line=dict(color='white',width=1.3)),name='Proporção observada',showlegend=False),1,2)
f.update_xaxes(title='Dia do microciclo',dtick=1,gridcolor='#eceef1',zeroline=False,row=1,col=2)
f.update_yaxes(title='Probabilidade',range=[-0.03,0.5],gridcolor='#eceef1',zeroline=False,row=1,col=2)

f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=22,t=58,b=58),
    legend=dict(orientation='h',y=1.14,x=0.25,xanchor='center',font=dict(size=12)))
f.write_image(f'{OUT}/logistic_curvas.png',width=1560,height=600,scale=3)
print('OK logistic_curvas.png | thr=%.1f'%thr)
