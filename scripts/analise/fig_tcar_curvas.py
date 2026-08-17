import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
wk=pd.read_csv('pv_wk.csv'); R=json.load(open('tcar_curvas.json'))
PRED=R['pred']
HEX={'FadFisica':'#e8590c','Vigor':'#2f9e44'}
NM={'FadFisica':'Fadiga física','Vigor':'Vigor'}
def curve(beta,xx,kind):
    if kind=='linear': return beta[0]+beta[1]*xx
    if kind=='log':    return beta[0]+beta[1]*np.log(xx)
    if kind=='quad':   return beta[0]+beta[1]*xx+beta[2]*xx**2
CL={'linear':'#1971c2','log':'#9c36b5','quad':'#e8590c'}
DASH={'linear':'solid','log':'dash','quad':'dot'}
CLAB={'linear':'Linear','log':'Logarítmica','quad':'Polinomial (2º)'}
f=make_subplots(rows=1,cols=2,horizontal_spacing=0.10,
    subplot_titles=['<b>Fadiga física × T-CAR</b>','<b>Vigor × T-CAR</b>'])
for j,resp in enumerate(['FadFisica','Vigor'],1):
    m=wk[[PRED,resp]].dropna()
    x=m[PRED].values; y=m[resp].values
    xx=np.linspace(x.min(),x.max(),200)
    f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=11,color=HEX[resp],opacity=0.75,
        line=dict(color='white',width=1.3)),showlegend=False),1,j)
    best=R['cont'][resp]['best']
    for kind in ('linear','log','quad'):
        v=R['cont'][resp][kind]
        wid=5 if kind==best else 2.6
        nm='%s (AIC %.0f)'%(CLAB[kind],v['aic'])+(' — melhor' if kind==best else '')
        f.add_trace(go.Scatter(x=xx,y=curve(v['beta'],xx,kind),mode='lines',
            line=dict(color=CL[kind],width=wid,dash=DASH[kind]),name=nm,showlegend=(j==1)),1,j)
    f.update_xaxes(title='Pico de velocidade — T-CAR (km/h)',gridcolor='#eceef1',zeroline=False,row=1,col=j)
    f.update_yaxes(title='Escore semanal (0–16)',gridcolor='#eceef1',zeroline=False,row=1,col=j)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=22,t=54,b=52),
    legend=dict(orientation='h',y=1.14,x=0.5,xanchor='center',font=dict(size=12)))
f.write_image(f'{OUT}/tcar_curvas.png',width=1500,height=600,scale=3)
print('OK tcar_curvas.png')
