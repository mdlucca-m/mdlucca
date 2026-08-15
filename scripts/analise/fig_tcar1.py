import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
F=pd.read_csv('tcar1_features.csv'); R=json.load(open('tcar1_baseline.json'))
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=25,t=52,b=55)); b.update(k); return b
f=make_subplots(rows=2,cols=2,vertical_spacing=0.15,horizontal_spacing=0.13,
    subplot_titles=['A) PV (T-CAR 1) × fadiga BRUMS no baseline','B) Associação de cada parâmetro com a fadiga (base)',
        'C) Perfil iceberg no baseline por posição','D) O acoplamento aptidão–fadiga emerge na semana'])
# A scatter PV x b_Fadiga
m=F[['PV','b_Fadiga']].dropna(); lr=stats.linregress(m.PV,m.b_Fadiga); r,p=stats.spearmanr(m.PV,m.b_Fadiga)
f.add_trace(go.Scatter(x=m.PV,y=m.b_Fadiga,mode='markers',marker=dict(size=10,color='#1c7ed6'),showlegend=False),1,1)
xx=np.array([m.PV.min(),m.PV.max()]); f.add_trace(go.Scatter(x=xx,y=lr.intercept+lr.slope*xx,mode='lines',line=dict(color='#c92a2a',width=2.5),showlegend=False),1,1)
f.add_annotation(x=m.PV.max(),y=m.b_Fadiga.max(),text='ρ=%.2f (p=%.2f)'%(r,p),showarrow=False,xanchor='right',font=dict(size=12),row=1,col=1)
# B |rho| phys x baseline fatigue (BRUMS)
phys=['PV','dist','FCmax','TRIMP','PSE']; labs=['PV','Distância','FCmáx','TRIMP\n(HIIT)','PSE\n(HIIT)']
rhos=[abs(R['COR'][p]['b_Fadiga']['r']) for p in phys]
cols=['#2b8a3e','#2b8a3e','#4c9be8','#adb5bd','#adb5bd']
f.add_trace(go.Bar(x=[l.replace('\n',' ') for l in labs],y=rhos,marker_color=cols,text=['%.2f'%v for v in rhos],textposition='outside',showlegend=False),1,2)
f.update_yaxes(range=[0,0.5],title='|ρ| com fadiga (base)',row=1,col=2)
# C baseline iceberg by position
order=['Goleiro','Meia','Ponta','Pivô']; ic=[R['POS'][o]['b_ice'] for o in order if o in R['POS']]
oo=[o for o in order if o in R['POS']]
f.add_trace(go.Bar(x=oo,y=ic,marker_color='#6741d9',text=['%.2f'%v for v in ic],textposition='outside',showlegend=False),2,1)
f.update_yaxes(title='Índice iceberg (base)',row=2,col=1)
# D coupling baseline vs week
base_r=abs(R['COR']['PV']['b_FadFisica']['r']); week_r=0.51
f.add_trace(go.Bar(x=['Baseline (D1)','Semana (média)'],y=[base_r,week_r],marker_color=['#94d82d','#2b8a3e'],
    text=['ρ=%.2f'%base_r,'ρ=%.2f'%week_r],textposition='outside',showlegend=False),2,2)
f.update_yaxes(range=[0,0.65],title='|ρ| PV × fadiga física',row=2,col=2)
f.update_xaxes(title='PV (km·h⁻¹)',row=1,col=1); f.update_yaxes(title='Fadiga BRUMS (base)',row=1,col=1)
f.update_layout(**T(height=820))
f.write_image(f'{OUT}/x_tcar1.png',width=1500,height=980,scale=2)
print('fig x_tcar1 OK | base_r=%.2f'%base_r)
