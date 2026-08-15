import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
R=json.load(open('tcar1_full.json'))
h=pd.read_csv('hum_prof.csv'); F=pd.read_csv('tcar2_features.csv')[['ID','PVini']].rename(columns={'PVini':'PV'})
days=np.arange(1,8)
wk=h.groupby('ID')[['FadFisica','Vigor']].mean().reset_index().merge(F,on='ID',how='left')
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=62,r=55,t=52,b=52)); b.update(k); return b
f=make_subplots(rows=2,cols=2,vertical_spacing=0.15,horizontal_spacing=0.13,
    subplot_titles=['A) Regressão aptidão (PV, T-CAR 1) × vigor semanal','B) Correlação PV × (vigor/fadiga) por dia',
        'C) Limiar logístico do PV: vigor alto e fadiga alta','D) Vigor do grupo e acoplamento PV×vigor por dia'],
    specs=[[{},{}],[{},{'secondary_y':True}]])
# A vigor ~ PV
m=wk[['PV','Vigor']].dropna(); W=R['Vigor']['week']
f.add_trace(go.Scatter(x=m.PV,y=m.Vigor,mode='markers',marker=dict(size=11,color='#2b8a3e'),showlegend=False),1,1)
xx=np.array([m.PV.min(),m.PV.max()]); f.add_trace(go.Scatter(x=xx,y=W['intercept']+W['slope']*xx,mode='lines',line=dict(color='#c92a2a',width=3),showlegend=False),1,1)
f.add_annotation(x=m.PV.min(),y=m.Vigor.max(),xanchor='left',showarrow=False,font=dict(size=12),
    text='vigor = %.1f %+.2f·PV<br>ρ=%.2f (p=%.3f); R²=%.2f'%(W['intercept'],W['slope'],W['rho'],W['p'],W['r2']),row=1,col=1)
# B per-day rho vigor and fatigue
rv=[R['Vigor']['day'][str(d)]['rho'] for d in days]; rf=[R['FadFisica']['day'][str(d)]['rho'] for d in days]
pv=[R['Vigor']['day'][str(d)]['rho_p'] for d in days]; pf=[R['FadFisica']['day'][str(d)]['rho_p'] for d in days]
f.add_trace(go.Bar(x=days,y=rv,name='Vigor',marker_color='#2b8a3e'),1,2)
f.add_trace(go.Bar(x=days,y=rf,name='Fadiga',marker_color='#e8590c'),1,2)
for d,r_,p_ in zip(days,rv,pv):
    if p_<0.05: f.add_annotation(x=d-0.15,y=r_+0.03,text='*',showarrow=False,font=dict(size=18,color='#2b8a3e'),row=1,col=2)
for d,r_,p_ in zip(days,rf,pf):
    if p_<0.05: f.add_annotation(x=d+0.15,y=r_-0.05,text='*',showarrow=False,font=dict(size=18,color='#e8590c'),row=1,col=2)
f.update_yaxes(title='ρ (PV × desfecho)',row=1,col=2)
# C threshold curves vigor & fatigue
tv=R['Vigor']['thr']; tfd=R['FadFisica']['thr']; xr=np.linspace(13,18.5,120)
f.add_trace(go.Scatter(x=xr,y=1/(1+np.exp(-(tv['b0']+tv['b1']*xr))),mode='lines',line=dict(color='#2b8a3e',width=3),name='P(vigor alto)'),2,1)
f.add_trace(go.Scatter(x=xr,y=1/(1+np.exp(-(tfd['b0']+tfd['b1']*xr))),mode='lines',line=dict(color='#e8590c',width=3),name='P(fadiga alta)'),2,1)
f.add_vline(x=tv['thr'],line=dict(color='#2b8a3e',dash='dash'),row=2,col=1)
f.add_annotation(x=tv['thr'],y=0.92,text='limiar vigor %.1f<br>AUC %.2f (VC %.2f)'%(tv['thr'],tv['auc'],tv['cv_auc']),showarrow=False,font=dict(size=10,color='#2b8a3e'),xanchor='left',row=2,col=1)
f.update_yaxes(title='Probabilidade',row=2,col=1,range=[0,1]); f.update_xaxes(title='PV (km·h⁻¹)',row=2,col=1)
# D group vigor by day (bars) + PV x vigor rho (line, secondary y)
vday=[R['vigor_by_day'][str(d)] for d in days]
f.add_trace(go.Bar(x=days,y=vday,name='Vigor médio (grupo)',marker_color='#94d82d',opacity=0.85),2,2,secondary_y=False)
f.add_trace(go.Scatter(x=days,y=rv,mode='lines+markers',name='ρ PV×vigor',line=dict(color='#1c7ed6',width=3),marker=dict(size=8)),2,2,secondary_y=True)
f.update_yaxes(title_text='Vigor médio',row=2,col=2,secondary_y=False,range=[0,9])
f.update_yaxes(title_text='ρ PV×vigor',row=2,col=2,secondary_y=True,range=[0,0.7])
f.update_xaxes(title='Dia',dtick=1,row=2,col=2)
f.update_xaxes(title='PV inicial (km·h⁻¹)',row=1,col=1); f.update_yaxes(title='Vigor semanal',row=1,col=1)
f.update_xaxes(title='Dia',dtick=1,row=1,col=2)
f.update_layout(**T(height=880,barmode='group',legend=dict(orientation='h',y=1.05,x=0.45,font=dict(size=10))))
f.write_image(f'{OUT}/x_limiar.png',width=1500,height=1040,scale=2)
print('fig x_limiar (vigor+fatigue+vigor-days) OK')
