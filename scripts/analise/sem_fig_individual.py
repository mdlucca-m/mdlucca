import warnings; warnings.filterwarnings('ignore')
import os, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
SC='.'; OUT='Artigos/figuras'
hum=pd.read_csv('hum_prof.csv'); h2=hum[hum.momento.isin(['pre','pos'])].copy()
CV={'Vigor':'#2b8a3e','FadFisica':'#d9480f'}; LB={'Vigor':'Vigor','FadFisica':'Fadiga física'}
def T(**k):
    base=dict(template='plotly_white',font=dict(color='#111',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=30,t=60,b=50)); base.update(k); return base
f=make_subplots(rows=1,cols=2,subplot_titles=[LB['Vigor'],LB['FadFisica']],horizontal_spacing=0.13)
for j,v in enumerate(['Vigor','FadFisica'],1):
    pre=h2[h2.momento=='pre'].groupby('ID')[v].mean(); pos=h2[h2.momento=='pos'].groupby('ID')[v].mean()
    c=pre.index.intersection(pos.index)
    for aid in c:
        f.add_trace(go.Scatter(x=['Pré','Pós'],y=[pre[aid],pos[aid]],mode='lines+markers',
            line=dict(color='rgba(130,130,130,0.45)',width=1),marker=dict(size=4,color=CV[v]),showlegend=False),1,j)
    f.add_trace(go.Scatter(x=['Pré','Pós'],y=[pre[c].mean(),pos[c].mean()],mode='lines+markers',
        line=dict(color=CV[v],width=5),marker=dict(size=10),showlegend=False),1,j)
f.update_layout(**T(height=560)); f.update_yaxes(title='Escore')
f.write_image(f'{OUT}/sem_f_ind_prepos.png',width=1500,height=850,scale=2)
print('OK')
