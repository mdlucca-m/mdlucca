import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style  # estilo MDPI (registra template e torna padrão)
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); days=np.arange(1,8)
def ms(v):
    m=h.groupby('dia')[v].mean().reindex(days).values
    se=h.groupby('dia')[v].sem().reindex(days).values
    return m,se
f=make_subplots(rows=1,cols=2,subplot_titles=('Sonolência (Epworth, 0–18)','Estresse percebido (PSS-14, 0–56)'),horizontal_spacing=0.13)
def panel(v,color,fill,c):
    m,se=ms(v); up=m+1.96*se; lo=m-1.96*se
    f.add_trace(go.Scatter(x=list(days)+list(days[::-1]),y=list(up)+list(lo[::-1]),fill='toself',fillcolor=fill,mode='lines',line=dict(width=0),showlegend=False,hoverinfo='skip'),1,c)
    f.add_trace(go.Scatter(x=days,y=m,mode='lines+markers',line=dict(color=color,width=5.2),marker=dict(size=11,color=color,line=dict(color='white',width=1.5)),showlegend=False),1,c)
panel('Epworth','#1c7ed6','rgba(28,126,214,0.16)',1)
panel('PSS','#7048e8','rgba(112,72,232,0.15)',2)
f.update_xaxes(title_text='Dia do microciclo',tickvals=list(days),gridcolor='#eceef1',zeroline=False)
f.update_yaxes(gridcolor='#eceef1',zeroline=False)
f.update_yaxes(range=[6,13],row=1,col=1); f.update_yaxes(range=[18,26],row=1,col=2)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),
   paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=56,r=24,t=54,b=54),width=1000,height=430)
for a in f.layout.annotations: a.font.size=15
f.write_image(OUT+'/sono_traj.png',scale=2)
print('OK sono_traj.png')
