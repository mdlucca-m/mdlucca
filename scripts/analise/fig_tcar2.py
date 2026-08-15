import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
F=pd.read_csv('tcar2_features.csv'); R2=json.load(open('tcar2_baseline.json')); R1=json.load(open('tcar1_baseline.json'))
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=25,t=52,b=55)); b.update(k); return b
f=make_subplots(rows=2,cols=2,vertical_spacing=0.15,horizontal_spacing=0.13,
    subplot_titles=['A) PV do T-CAR 2 × fadiga BRUMS no baseline','B) T-CAR 1 vs T-CAR 2 — poder sobre o baseline',
        'C) Adaptação individual (ΔPV = T-CAR 2 − T-CAR 1)','D) Quem adaptou mais fadigou menos? (não)'])
# A
m=F[['PV','b_Fadiga']].dropna(); lr=stats.linregress(m.PV,m.b_Fadiga); r,p=stats.spearmanr(m.PV,m.b_Fadiga)
f.add_trace(go.Scatter(x=m.PV,y=m.b_Fadiga,mode='markers',marker=dict(size=10,color='#1c7ed6'),showlegend=False),1,1)
xx=np.array([m.PV.min(),m.PV.max()]); f.add_trace(go.Scatter(x=xx,y=lr.intercept+lr.slope*xx,mode='lines',line=dict(color='#c92a2a',width=2.5),showlegend=False),1,1)
f.add_annotation(x=m.PV.max(),y=m.b_Fadiga.max(),text='ρ=%.2f (p=%.2f)'%(r,p),showarrow=False,xanchor='right',font=dict(size=12),row=1,col=1)
# B grouped bars T-CAR1 vs T-CAR2: |rho| baseline fatigue, iceberg AUC
cats=['|ρ| fadiga (base)','AUC iceberg (base)']
v1=[abs(R1['COR']['PV']['b_Fadiga']['r']),R1['ROC']['PV']['auc']]
v2=[abs(R2['COR']['PV']['b_Fadiga']['r']),R2['ROC']['PV']['auc']]
f.add_trace(go.Bar(x=cats,y=v1,name='T-CAR 1',marker_color='#2b8a3e',text=['%.2f'%x for x in v1],textposition='outside'),1,2)
f.add_trace(go.Bar(x=cats,y=v2,name='T-CAR 2',marker_color='#94d82d',text=['%.2f'%x for x in v2],textposition='outside'),1,2)
f.update_yaxes(range=[0,0.75],title='valor',row=1,col=2)
# C adaptation per athlete sorted
d=F[['ID','dPV']].dropna().sort_values('dPV')
cols=['#c92a2a' if x<0 else '#2b8a3e' for x in d.dPV]
f.add_trace(go.Bar(x=list(range(len(d))),y=d.dPV,marker_color=cols,showlegend=False),2,1)
f.add_hline(y=F.dPV.mean(),line=dict(color='#111',dash='dot'),row=2,col=1)
f.update_yaxes(title='ΔPV (km·h⁻¹)',row=2,col=1); f.update_xaxes(title='atletas (ordenados)',showticklabels=False,row=2,col=1)
# D dPV vs weekly d_FadFisica
m2=F[['dPV','d_FadFisica']].dropna(); r2,p2=stats.spearmanr(m2.dPV,m2.d_FadFisica); lr2=stats.linregress(m2.dPV,m2.d_FadFisica)
f.add_trace(go.Scatter(x=m2.dPV,y=m2.d_FadFisica,mode='markers',marker=dict(size=10,color='#6741d9'),showlegend=False),2,2)
xx=np.array([m2.dPV.min(),m2.dPV.max()]); f.add_trace(go.Scatter(x=xx,y=lr2.intercept+lr2.slope*xx,mode='lines',line=dict(color='#adb5bd',width=2,dash='dash'),showlegend=False),2,2)
f.add_annotation(x=m2.dPV.max(),y=m2.d_FadFisica.max(),text='ρ=%.2f (p=%.2f) n.s.'%(r2,p2),showarrow=False,xanchor='right',font=dict(size=12),row=2,col=2)
f.update_xaxes(title='ΔPV (adaptação)',row=2,col=2); f.update_yaxes(title='Δ fadiga física D1→D7',row=2,col=2)
f.update_xaxes(title='PV T-CAR 2 (km·h⁻¹)',row=1,col=1); f.update_yaxes(title='Fadiga BRUMS (base)',row=1,col=1)
f.update_layout(**T(height=830,legend=dict(orientation='h',y=1.06,x=0.62,font=dict(size=11)),barmode='group'))
f.write_image(f'{OUT}/x_tcar2.png',width=1500,height=1000,scale=2)
print('fig x_tcar2 OK | PVfin×base fadiga rho=%.2f'%r)
