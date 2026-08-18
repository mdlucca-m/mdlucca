import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import plotly.graph_objects as go
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
# ordem canônica POMS/BRUMS
ORDER=[('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),
       ('Vigor','Vigor'),('Fadiga','Fadiga'),('Confusao','Confusão')]
PAL={'Tensao':'#1971c2','Depressao':'#9c36b5','Raiva':'#e03131',
     'Vigor':'#2f9e44','Fadiga':'#e8590c','Confusao':'#f08c00'}
f=go.Figure()
for k,lab in ORDER:
    y=h[k].dropna()
    f.add_trace(go.Box(y=y,name=lab,boxmean=True,               # média = linha tracejada; mediana = linha sólida
        marker=dict(color=PAL[k]),line=dict(width=2.4,color=PAL[k]),
        fillcolor=PAL[k],opacity=0.45,boxpoints='outliers',marker_size=5,
        marker_opacity=0.55,width=0.6,showlegend=False))
    # marcador explícito da média (losango) sobre a linha tracejada
    f.add_trace(go.Scatter(x=[lab],y=[float(y.mean())],mode='markers',
        marker=dict(symbol='diamond',size=9,color='white',line=dict(color=PAL[k],width=2)),
        showlegend=False,hoverinfo='skip'))
# legenda-guia (mediana x média) fora dos dados
f.add_trace(go.Scatter(x=[None],y=[None],mode='lines',line=dict(color='#495057',width=2.4),name='Mediana'))
f.add_trace(go.Scatter(x=[None],y=[None],mode='lines',line=dict(color='#495057',width=2,dash='dash'),name='Média'))
f.add_trace(go.Scatter(x=[None],y=[None],mode='markers',
    marker=dict(symbol='diamond',size=9,color='white',line=dict(color='#495057',width=2)),name='Média (marcador)'))
f.update_layout(template='mdpi',
    font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=60,r=20,t=42,b=50),boxgap=0.35,
    legend=dict(orientation='h',y=1.09,x=0.5,xanchor='center',font=dict(size=12),
        bgcolor='rgba(255,255,255,0.6)',bordercolor='#dee2e6',borderwidth=1))
f.update_yaxes(title='Escore (0–16)',range=[-0.6,16.6],dtick=2,gridcolor='#eceef1',zeroline=False)
f.update_xaxes(gridcolor='#eceef1',zeroline=False)
f.write_image(f'{OUT}/box_humor.png',width=1560,height=620,scale=3)
print('OK box_humor.png')
