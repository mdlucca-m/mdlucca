import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from scipy.interpolate import UnivariateSpline
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); A=json.load(open('adv.json'))
seq=[(1,'baseline')]+sum([[(d,'pre'),(d,'pos')] for d in range(2,8)],[])
x=np.array([d+(-0.2 if m=='pre' else 0.2 if m=='pos' else 0.0) for d,m in seq])
xx=np.linspace(x.min(),x.max(),400)
def sm(k):
    y=np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m in seq])
    s=UnivariateSpline(x,y,k=4,s=len(x)*np.var(y)*0.85); return s(xx)
DIMS=[('Vigor','Vigor','#2f9e44'),('Fadiga','Fadiga','#e8590c'),('Tensao','Tensão','#1971c2'),
      ('Depressao','Depressão','#9c36b5'),('Raiva','Raiva','#e03131'),('Confusao','Confusão','#f08c00')]
f=go.Figure()
# faixas início/acúmulo
f.add_vrect(x0=1,x1=4,fillcolor='#1971c2',opacity=0.05,line_width=0)
f.add_vrect(x0=4,x1=7.2,fillcolor='#e8590c',opacity=0.05,line_width=0)
for k,lab,col in DIMS:
    f.add_trace(go.Scatter(x=xx,y=sm(k),mode='lines',name=lab,line=dict(color=col,width=4)))
# cruzamentos vigor x fadiga
for c in A['vf_cross']:
    f.add_trace(go.Scatter(x=[c['x']],y=[c['y']],mode='markers',showlegend=False,
        marker=dict(symbol='diamond',size=14,color='#212529',line=dict(color='white',width=1.5))))
    f.add_annotation(x=c['x'],y=c['y'],text='dia %.1f'%c['x'],showarrow=True,arrowhead=0,ax=0,ay=-28,
        font=dict(size=11,color='#212529'),bgcolor='white',bordercolor='#adb5bd',borderwidth=1)
f.update_layout(template='mdpi',title=dict(text='<b>Trajetórias e cruzamentos das seis dimensões do BRUMS ao longo do microciclo</b>',x=0.5,font=dict(size=17)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=70,r=30,t=64,b=90),legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center'))
f.update_xaxes(title='Dia do microciclo',showgrid=False,zeroline=False,dtick=1)
f.update_yaxes(title='Escore (0 a 16)',showgrid=True,gridcolor='#eee',zeroline=False,rangemode='tozero')
f.add_annotation(x=6.5,y=1.0,text='As dimensões negativas permanecem junto ao piso; apenas o par vigor-fadiga ocupa a faixa central e se cruza.',
    showarrow=False,font=dict(size=11,color='#495057'),xanchor='center')
f.write_image(f'{OUT}/cruzamentos_todas_dims.png',width=1700,height=920,scale=3)
print('OK cruzamentos_todas_dims.png')
