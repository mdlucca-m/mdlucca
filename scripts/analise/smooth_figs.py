import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style  # estilo MDPI
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); days=np.arange(1,8); tt=np.linspace(1,7,241)
COL={'Vigor':'#2f9e44','Fadiga':'#e8590c','TMD':'#7048e8','Tensao':'#1c7ed6',
     'Depressao':'#9c36b5','Raiva':'#e03131','Confusao':'#f59f00'}
NM={'Vigor':'Vigor','Fadiga':'Fadiga','TMD':'PTH','Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
PANA=['Vigor','Fadiga','TMD']                              # eixo energia–fadiga
PANB=['Tensao','Depressao','Raiva','Confusao']             # negativas
f=make_subplots(rows=1,cols=2,subplot_titles=('A) Eixo energia–fadiga (sinal suavizado)','B) Subescalas negativas (sinal suavizado)'),horizontal_spacing=0.10)
def draw(keys,col):
    for k in keys:
        y=h.groupby('dia')[k].mean().reindex(days).values
        c=np.polyfit(days,y,3); P=np.poly1d(c)
        # pontos brutos (média diária) — tênues
        f.add_trace(go.Scatter(x=days,y=y,mode='markers',marker=dict(size=6,color=COL[k],opacity=0.45),
            showlegend=False,hoverinfo='skip'),1,col)
        # sinal suavizado (polinômio) — linha cheia
        f.add_trace(go.Scatter(x=tt,y=P(tt),mode='lines',line=dict(color=COL[k],width=3.2),
            name=NM[k],legendgroup=NM[k]),1,col)
draw(PANA,1); draw(PANB,2)
f.update_yaxes(title_text='Escore (0–16)',row=1,col=1,gridcolor='#e6e8eb',zeroline=False)
f.update_yaxes(gridcolor='#e6e8eb',zeroline=False,row=1,col=2)
f.update_xaxes(title_text='Dia do microciclo',tickvals=list(days),gridcolor='#e6e8eb',zeroline=False,row=1,col=1)
f.update_xaxes(title_text='Dia do microciclo',tickvals=list(days),gridcolor='#e6e8eb',zeroline=False,row=1,col=2)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=30,t=64,b=52),width=1120,height=440,
    legend=dict(orientation='h',yanchor='bottom',y=1.10,xanchor='center',x=0.5))
for a in f.layout.annotations[:2]: a.font.size=14
f.write_image(OUT+'/smooth_signal.png',scale=2)
print('OK smooth_signal.png')
