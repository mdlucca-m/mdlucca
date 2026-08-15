import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
R=json.load(open('tcar2_models.json'))
h=pd.read_csv('hum_prof.csv'); F=pd.read_csv('tcar2_features.csv')[['ID','PV','PVini']]
days=np.arange(1,8)
dm=h.groupby(['ID','dia'])['FadFisica'].mean().reset_index().merge(F,on='ID',how='left')
wk=h.groupby('ID')['FadFisica'].mean().reset_index().merge(F,on='ID',how='left')
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=20,t=52,b=52)); b.update(k); return b
def terc_traj(col):
    w=wk.dropna(subset=[col]).copy(); w['t']=pd.qcut(w[col],3,labels=['Baixo','Médio','Alto'])
    mp=w.set_index('ID')['t'].to_dict(); d=dm.copy(); d['t']=d.ID.map(mp)
    return {str(k):d[d.t==k].groupby('dia')['FadFisica'].mean().reindex(days).values for k in ['Baixo','Médio','Alto']}
tf_fin=terc_traj('PV'); tf_ini=terc_traj('PVini')

f=make_subplots(rows=2,cols=2,vertical_spacing=0.15,horizontal_spacing=0.12,
    subplot_titles=['A) Regressão |ρ| semana × PV — T-CAR 1 vs T-CAR 2','B) Limiar/ROC — AUC (dia de fadiga alta)',
        'C) Derivadas: trajetória por tercil de PV do T-CAR 2','D) Derivadas: trajetória por tercil de PV do T-CAR 1'])
# A grouped bars |rho| by outcome
outs=['FadFisica','Vigor','TMD','Fadiga']; labs=['Fad. física','Vigor','PTH/TMD','Fadiga']
rin=[abs(R['REG'][o]['PVini']['rho']) for o in outs]; rfn=[abs(R['REG'][o]['PVfin']['rho']) for o in outs]
f.add_trace(go.Bar(x=labs,y=rin,name='T-CAR 1',marker_color='#2b8a3e',text=['%.2f'%v for v in rin],textposition='outside'),1,1)
f.add_trace(go.Bar(x=labs,y=rfn,name='T-CAR 2',marker_color='#94d82d',text=['%.2f'%v for v in rfn],textposition='outside'),1,1)
f.update_yaxes(range=[0,0.65],title='|ρ|',row=1,col=1)
# B AUC with CI
L1=R['LIM']['PVini']; L2=R['LIM']['PVfin']
f.add_trace(go.Bar(x=['T-CAR 1','T-CAR 2'],y=[L1['auc'],L2['auc']],marker_color=['#2b8a3e','#94d82d'],
    error_y=dict(type='data',symmetric=False,array=[L1['auc_hi']-L1['auc'],L2['auc_hi']-L2['auc']],arrayminus=[L1['auc']-L1['auc_lo'],L2['auc']-L2['auc_lo']]),
    text=['AUC=%.2f<br>limiar %.1f'%(L1['auc'],L1['youden_thr']),'AUC=%.2f<br>limiar %.1f'%(L2['auc'],L2['youden_thr'])],textposition='outside',showlegend=False),1,2)
f.add_hline(y=0.5,line=dict(color='#868e96',dash='dot'),row=1,col=2); f.update_yaxes(range=[0,0.9],title='AUC',row=1,col=2)
# C trajectories by PVfin tercile
cols={'Baixo':'#e8590c','Médio':'#f59f00','Alto':'#2b8a3e'}
for k in ['Baixo','Médio','Alto']:
    f.add_trace(go.Scatter(x=days,y=tf_fin[k],mode='lines+markers',name='PV '+k,line=dict(color=cols[k],width=3),marker=dict(size=7),showlegend=False),2,1)
f.update_yaxes(title='Fadiga física',row=2,col=1,range=[3,8]); f.update_xaxes(title='Dia',dtick=1,row=2,col=1)
# D trajectories by PVini tercile
for k in ['Baixo','Médio','Alto']:
    f.add_trace(go.Scatter(x=days,y=tf_ini[k],mode='lines+markers',name=k,line=dict(color=cols[k],width=3),marker=dict(size=7)),2,2)
f.update_yaxes(title='Fadiga física',row=2,col=2,range=[3,8]); f.update_xaxes(title='Dia',dtick=1,row=2,col=2)
f.update_layout(**T(height=850,barmode='group',legend=dict(orientation='h',y=1.06,x=0.5,font=dict(size=11))))
f.write_image(f'{OUT}/x_tcar2_models.png',width=1500,height=1010,scale=2)
print('fig x_tcar2_models OK')
print('PVfin tercil ranges FadFis D7:',{k:round(tf_fin[k][-1],1) for k in tf_fin})
print('PVini tercil ranges FadFis D7:',{k:round(tf_ini[k][-1],1) for k in tf_ini})
