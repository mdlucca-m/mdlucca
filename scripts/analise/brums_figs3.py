import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style  # estilo MDPI (registra template e torna padrão)
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
days=np.arange(1,8)
PAL={'Vigor':'#2f9e44','Fadiga':'#e8590c','Tensao':'#1971c2','Depressao':'#9c36b5','Raiva':'#e03131','Confusao':'#f08c00'}
NM={'Vigor':'Vigor','Fadiga':'Fadiga','Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
ORDER=['Vigor','Fadiga','Tensao','Depressao','Raiva','Confusao']
def base(**k):
    b=dict(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
        margin=dict(l=58,r=20,t=48,b=48)); b.update(k); return b
GRID=dict(gridcolor='#eceef1',zeroline=False)

# ============ HISTOGRAMS (2x3) ============
f=make_subplots(rows=2,cols=3,vertical_spacing=0.14,horizontal_spacing=0.08,
    subplot_titles=['<b>%s</b>'%NM[k] for k in ORDER])
for idx,k in enumerate(ORDER):
    r,c=divmod(idx,3); r+=1; c+=1
    x=h[k].dropna()
    f.add_trace(go.Histogram(x=x,marker=dict(color=PAL[k],line=dict(color='white',width=1)),
        xbins=dict(start=-0.5,end=16.5,size=1),showlegend=False,opacity=0.9),r,c)
    f.add_vline(x=float(x.median()),line=dict(color='#111',dash='dash',width=2),row=r,col=c)
    f.update_xaxes(title='Escore (0–16)' if r==2 else '',dtick=4,range=[-0.5,16.5],row=r,col=c,**GRID)
    f.update_yaxes(title='Frequência' if c==1 else '',row=r,col=c,**GRID)
f.update_layout(**base(height=620,width=1400))
f.write_image(f'{OUT}/xb3_hist.png',width=1500,height=680,scale=3)

# ============ BOXPLOTS by day (2x3) ============
f=make_subplots(rows=2,cols=3,vertical_spacing=0.13,horizontal_spacing=0.07,
    subplot_titles=['<b>%s</b>'%NM[k] for k in ORDER])
for idx,k in enumerate(ORDER):
    r,c=divmod(idx,3); r+=1; c+=1
    for d in days:
        yv=h[h.dia==d][k].dropna()
        f.add_trace(go.Box(y=yv,name=str(d),marker=dict(color=PAL[k]),line=dict(width=1.5),
            fillcolor=PAL[k],opacity=0.55,boxpoints='outliers',marker_size=4,showlegend=False,width=0.6),r,c)
    f.update_xaxes(title='Dia' if r==2 else '',row=r,col=c,**GRID)
    f.update_yaxes(title='Escore (0–16)' if c==1 else '',row=r,col=c,**GRID)
f.update_layout(**base(height=680,width=1420,boxgap=0.25))
f.write_image(f'{OUT}/xb3_box.png',width=1520,height=740,scale=3)
print('figs OK: xb3_hist, xb3_box')
