import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
R=json.load(open('tcar_limiar.json'))
h=pd.read_csv('hum_prof.csv'); F=pd.read_csv('tcar2_features.csv')[['ID','PV','PVini']]
days=np.arange(1,8)
wk=h.groupby('ID')['FadFisica'].mean().reset_index().merge(F,on='ID',how='left')
dm=h.groupby(['ID','dia'])['FadFisica'].mean().reset_index().merge(F,on='ID',how='left')
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=20,t=52,b=52)); b.update(k); return b
f=make_subplots(rows=2,cols=2,vertical_spacing=0.15,horizontal_spacing=0.12,
    subplot_titles=['A) Regressão aptidão × fadiga semanal (PV do T-CAR 1)','B) Correlação aptidão–fadiga por dia',
        'C) Ajuste do limiar logístico do PV (dia de fadiga alta)','D) Fadiga semanal por tercil de aptidão (T-CAR 1)'])
# A weekly regression scatter (T-CAR 1)
m=wk[['PVini','FadFisica']].dropna(); W=R['WK']['PVini']
f.add_trace(go.Scatter(x=m.PVini,y=m.FadFisica,mode='markers',marker=dict(size=11,color='#1c7ed6'),showlegend=False),1,1)
xx=np.array([m.PVini.min(),m.PVini.max()]); f.add_trace(go.Scatter(x=xx,y=W['intercept']+W['slope']*xx,mode='lines',line=dict(color='#c92a2a',width=3),showlegend=False),1,1)
f.add_annotation(x=m.PVini.max(),y=m.FadFisica.max(),xanchor='right',showarrow=False,font=dict(size=12),
    text='fadiga = %.1f %+.2f·PV<br>ρ=%.2f (p=%.3f); R²=%.2f'%(W['intercept'],W['slope'],W['rho'],W['p'],W['r2']),row=1,col=1)
# B per-day rho
di=[R['DAY']['PVini'][str(d)]['rho'] for d in days]; df=[R['DAY']['PVfin'][str(d)]['rho'] for d in days]
dip=[R['DAY']['PVini'][str(d)]['rho_p'] for d in days]
f.add_trace(go.Bar(x=days,y=di,name='T-CAR 1',marker_color='#2b8a3e'),1,2)
f.add_trace(go.Bar(x=days,y=df,name='T-CAR 2',marker_color='#94d82d'),1,2)
for d,r_,p_ in zip(days,di,dip):
    if p_<0.05: f.add_annotation(x=d-0.15,y=r_-0.03,text='*',showarrow=False,font=dict(size=20,color='#2b8a3e'),row=1,col=2)
f.update_yaxes(title='ρ (PV × fadiga)',row=1,col=2); f.update_xaxes(title='Dia',dtick=1,row=1,col=2)
# C logistic threshold curves
L1=R['LIM']['PVini']; L2=R['LIM']['PVfin']
xr=np.linspace(13,18.5,120)
for L,col,lab in [(L1,'#2b8a3e','T-CAR 1'),(L2,'#adb5bd','T-CAR 2')]:
    pr=1/(1+np.exp(-(L['b0']+L['b1']*xr)))
    f.add_trace(go.Scatter(x=xr,y=pr,mode='lines',line=dict(color=col,width=3),name=lab,showlegend=False),2,1)
f.add_vline(x=L1['thr'],line=dict(color='#2b8a3e',dash='dash'),row=2,col=1)
f.add_annotation(x=L1['thr'],y=0.9,text='limiar %.1f km/h<br>AUC=%.2f'%(L1['thr'],L1['auc']),showarrow=False,font=dict(size=11,color='#2b8a3e'),xanchor='left',row=2,col=1)
f.update_yaxes(title='P(dia de fadiga alta)',row=2,col=1,range=[0,1]); f.update_xaxes(title='PV (km·h⁻¹)',row=2,col=1)
# D terciles
order=['Baixa','Média','Alta']; vals=[R['TERC'][o]['FadFis'] for o in order]; pvs=[R['TERC'][o]['PV'] for o in order]
f.add_trace(go.Bar(x=['%s<br>(PV %.1f)'%(o,pv) for o,pv in zip(order,pvs)],y=vals,marker_color=['#e8590c','#f59f00','#2b8a3e'],
    text=['%.1f'%v for v in vals],textposition='outside',showlegend=False),2,2)
f.update_yaxes(title='Fadiga física semanal',row=2,col=2,range=[0,8]); f.update_xaxes(title='Tercil de aptidão',row=2,col=2)
f.update_xaxes(title='PV inicial (km·h⁻¹)',row=1,col=1); f.update_yaxes(title='Fadiga física semanal',row=1,col=1)
f.update_layout(**T(height=860,barmode='group',legend=dict(orientation='h',y=1.05,x=0.6,font=dict(size=11))))
f.write_image(f'{OUT}/x_limiar.png',width=1500,height=1010,scale=2)
print('fig x_limiar OK')
