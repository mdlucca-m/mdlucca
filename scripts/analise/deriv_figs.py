import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style  # estilo MDPI (registra template e torna padrão)
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); D=json.load(open('deriv.json')); days=np.arange(1,8)
tt=np.linspace(1,7,241)
LAB_DER='Derivada P′(t)'
LAB_TAX='Taxa de variação P′(t)'
PAN=[('Vigor','Vigor','#2f9e44'),('Fadiga','Fadiga','#e8590c')]
f=make_subplots(rows=1,cols=2,subplot_titles=[p[1] for p in PAN],
    specs=[[{'secondary_y':True},{'secondary_y':True}]],horizontal_spacing=0.20)
for j,(k,lab,col) in enumerate(PAN,1):
    y=h.groupby('dia')[k].mean().reindex(days).values
    c=np.array(D['vars'][k]['coef']); P=np.poly1d(c); dP=P.deriv(1)
    infl=D['vars'][k]['infl']
    f.add_trace(go.Scatter(x=days,y=y,mode='markers',marker=dict(size=12,color=col,line=dict(color='white',width=1.5)),
        name='Média diária',showlegend=(j==1)),1,j,secondary_y=False)
    f.add_trace(go.Scatter(x=tt,y=P(tt),mode='lines',line=dict(color=col,width=4.3),
        name='Ajuste P(t)',showlegend=(j==1)),1,j,secondary_y=False)
    f.add_trace(go.Scatter(x=tt,y=dP(tt),mode='lines',line=dict(color='#495057',width=2,dash='dash'),
        name=LAB_DER,showlegend=(j==1)),1,j,secondary_y=True)
    f.add_hline(y=0,line=dict(color='#adb5bd',width=1),row=1,col=j,secondary_y=True)
    for x in infl:
        f.add_vline(x=x,line=dict(color='#868e96',width=1.5,dash='dot'),row=1,col=j)
        f.add_annotation(x=x,y=P(x),text='inflexão (t=%d)'%round(x),showarrow=True,arrowhead=2,
            ax=30,ay=-30,font=dict(size=11,color='#495057'),row=1,col=j,secondary_y=False)
    f.update_yaxes(title_text='Escore (0–16)',row=1,col=j,secondary_y=False,gridcolor='#eceef1',zeroline=False)
    f.update_yaxes(title_text=LAB_TAX,row=1,col=j,secondary_y=True,gridcolor='rgba(0,0,0,0)',zeroline=False)
    f.update_xaxes(title_text='Dia do microciclo',tickvals=list(days),row=1,col=j,gridcolor='#eceef1',zeroline=False)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=64,r=64,t=64,b=52),width=1120,height=440,
    legend=dict(orientation='h',yanchor='bottom',y=1.10,xanchor='center',x=0.5))
for a in f.layout.annotations[:2]: a.font.size=15
f.write_image(OUT+'/deriv_poly.png',scale=2)
print('OK deriv_poly.png')
