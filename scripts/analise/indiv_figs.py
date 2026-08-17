import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); days=np.arange(1,8)
dm=h.groupby(['ID','dia'])[['Vigor','Fadiga']].mean().reset_index()
PAN=[('Vigor','#2f9e44'),('Fadiga','#e8590c')]
f=make_subplots(rows=1,cols=2,subplot_titles=('Vigor — trajetórias individuais','Fadiga — trajetórias individuais'),horizontal_spacing=0.10)
for j,(v,col) in enumerate(PAN,1):
    for aid,g in dm.groupby('ID'):
        g=g.sort_values('dia')
        f.add_trace(go.Scatter(x=g['dia'],y=g[v],mode='lines',line=dict(color=col,width=1),opacity=0.28,
            showlegend=False,hoverinfo='skip'),1,j)
    gm=h.groupby('dia')[v].mean().reindex(days)
    f.add_trace(go.Scatter(x=days,y=gm.values,mode='lines+markers',line=dict(color=col,width=4),
        marker=dict(size=9,color=col,line=dict(color='white',width=1.5)),name='Média do grupo',showlegend=(j==1)),1,j)
    f.update_yaxes(title_text='Escore (0–16)' if j==1 else None,row=1,col=j,gridcolor='#e6e8eb',zeroline=False,range=[0,16])
    f.update_xaxes(title_text='Dia do microciclo',tickvals=list(days),row=1,col=j,gridcolor='#e6e8eb',zeroline=False)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=30,t=64,b=52),width=1120,height=440,
    legend=dict(orientation='h',yanchor='bottom',y=1.10,xanchor='center',x=0.5))
for a in f.layout.annotations[:2]: a.font.size=14
f.write_image(OUT+'/indiv_spaghetti.png',scale=2)
print('OK indiv_spaghetti.png')
