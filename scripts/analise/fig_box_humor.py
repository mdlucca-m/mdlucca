import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
ORDER=[('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),
       ('Vigor','Vigor'),('Fadiga','Fadiga'),('Confusao','Confusão')]
PAL={'Tensao':'#1971c2','Depressao':'#9c36b5','Raiva':'#e03131',
     'Vigor':'#2f9e44','Fadiga':'#e8590c','Confusao':'#f08c00'}
def yr(y):                                # escala própria da variável (faixa dos dados, visual)
    q1,q3=y.quantile([.25,.75]); iqr=q3-q1
    hi=min(y.max(), q3+1.5*iqr); hi=max(hi, y.mean()+1, 3)   # cobre caixa, bigode e média
    return [-0.4, float(np.ceil(hi))+0.4]
f=make_subplots(rows=2,cols=3,vertical_spacing=0.16,horizontal_spacing=0.09,
    subplot_titles=['<b>%s</b>'%lab for _,lab in ORDER])
for idx,(k,lab) in enumerate(ORDER):
    r,c=divmod(idx,3); r+=1; c+=1
    y=h[k].dropna()
    f.add_trace(go.Box(y=y,name=lab,boxmean=True,boxpoints=False,          # mediana (sólida) + média (tracejada)
        line=dict(width=2.4,color=PAL[k]),fillcolor=PAL[k],opacity=0.45,width=0.55,
        showlegend=False),r,c)
    f.add_trace(go.Scatter(x=[lab],y=[float(y.mean())],mode='markers',      # marcador da média
        marker=dict(symbol='diamond',size=10,color='white',line=dict(color=PAL[k],width=2)),
        showlegend=False,hoverinfo='skip'),r,c)
    rng=yr(y)
    f.update_yaxes(title='Escore' if c==1 else '',range=rng,
        dtick=(1 if rng[1]<=6 else 2),gridcolor='#eceef1',zeroline=False,row=r,col=c)
    f.update_xaxes(showticklabels=False,row=r,col=c)
# legenda-guia (mediana x média)
f.add_trace(go.Scatter(x=[None],y=[None],mode='lines',line=dict(color='#495057',width=2.4),name='Mediana'))
f.add_trace(go.Scatter(x=[None],y=[None],mode='lines',line=dict(color='#495057',width=2,dash='dash'),name='Média'))
f.add_trace(go.Scatter(x=[None],y=[None],mode='markers',
    marker=dict(symbol='diamond',size=10,color='white',line=dict(color='#495057',width=2)),name='Média (marcador)'))
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=58,r=18,t=64,b=24),boxgap=0.4,
    legend=dict(orientation='h',y=1.12,x=0.5,xanchor='center',font=dict(size=12),
        bgcolor='rgba(255,255,255,0.6)',bordercolor='#dee2e6',borderwidth=1))
f.write_image(f'{OUT}/box_humor.png',width=1560,height=720,scale=3)
print('OK box_humor.png (painéis por variável, escala própria)')
