import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
phys=pd.read_csv('phys.csv').rename(columns={'TCAR_PV_ini':'PVini'})
tc2=pd.read_csv('tcar2_features.csv')[['ID','PV']]  # PV final (T-CAR 2)
days=np.arange(1,8)
lo=lambda y,x: sm.nonparametric.lowess(y,x,frac=0.6,return_sorted=True)

# weekly per-athlete fatigue + mass + PVfin
wk=h.groupby('ID')['FadFisica'].mean().reset_index().merge(phys[['ID','massa']],on='ID').merge(tc2,on='ID',how='left')
def normrho(col):
    m=wk[[col,'FadFisica']].dropna(); raw=stats.spearmanr(m[col],m['FadFisica']).correlation
    b=stats.linregress(np.log(m[col]),np.log(m['FadFisica']+1e-6)).slope
    after=stats.spearmanr(m[col],m['FadFisica']/(m[col]**b)).correlation
    return abs(raw),abs(after)
mass_raw,mass_norm=normrho('massa'); pv_raw,pv_norm=normrho('PV')

SUB=['Vigor','Fadiga','FadFisica','Tensao','Depressao','Raiva','Confusao']
LAB=['Vigor','Fadiga','Fad.fís','Tensão','Depr.','Raiva','Confusão']
sds=[h[s].std() for s in SUB]

f=make_subplots(rows=2,cols=2,vertical_spacing=0.16,horizontal_spacing=0.13,
    subplot_titles=['A) Por que padronizar (z): escalas desiguais entre subescalas',
        'B) Normalização alométrica: remove o confundimento do tamanho',
        'C) Suavização (LOWESS): extrai o sinal do ruído',
        'D) Tendência suavizada do índice iceberg ao longo da semana'])
# A raw SD by subscale
f.add_trace(go.Bar(x=LAB,y=sds,marker_color='#4c6ef5',text=['%.1f'%v for v in sds],textposition='outside',showlegend=False),1,1)
f.update_yaxes(title='Desvio-padrão bruto',row=1,col=1)
# B |rho| before/after allometric normalization for mass and PVfin
f.add_trace(go.Bar(x=['Massa','PV (T-CAR 2)'],y=[mass_raw,pv_raw],name='bruto',marker_color='#e8590c',text=['%.2f'%mass_raw,'%.2f'%pv_raw],textposition='outside'),1,2)
f.add_trace(go.Bar(x=['Massa','PV (T-CAR 2)'],y=[mass_norm,pv_norm],name='normalizado',marker_color='#2b8a3e',text=['%.2f'%mass_norm,'%.2f'%pv_norm],textposition='outside'),1,2)
f.update_yaxes(title='|ρ| com fadiga física',row=1,col=2,range=[0,0.5])
# C smoothing: daily vigor & fadiga raw vs lowess (observations cloud + trend)
for v,col in [('Vigor','#2b8a3e'),('FadFisica','#e8590c')]:
    dd=h.dropna(subset=[v])
    f.add_trace(go.Scatter(x=dd['dia']+np.random.default_rng(1).normal(0,0.06,len(dd)),y=dd[v],mode='markers',marker=dict(size=4,color=col,opacity=0.18),showlegend=False),2,1)
    dm=h.groupby('dia')[v].mean().reindex(days)
    sm_=lo(dm.values,days)
    f.add_trace(go.Scatter(x=sm_[:,0],y=sm_[:,1],mode='lines',line=dict(color=col,width=4),name=v.replace('FadFisica','Fadiga física')),2,1)
f.update_yaxes(title='Escore (0–10)',row=2,col=1); f.update_xaxes(title='Dia',dtick=1,row=2,col=1)
# D iceberg index smoothed
di=h.groupby('dia')['ice_idx'].mean().reindex(days); smi=lo(di.values,days)
f.add_trace(go.Scatter(x=days,y=di.values,mode='markers',marker=dict(size=8,color='#adb5bd'),name='média diária',showlegend=False),2,2)
f.add_trace(go.Scatter(x=smi[:,0],y=smi[:,1],mode='lines',line=dict(color='#6741d9',width=4),showlegend=False),2,2)
f.add_hline(y=0,line=dict(color='#868e96',dash='dot'),row=2,col=2)
f.update_yaxes(title='Índice iceberg',row=2,col=2); f.update_xaxes(title='Dia',dtick=1,row=2,col=2)
f.update_layout(template='plotly_white',font=dict(color='#111',size=13,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    height=880,legend=dict(orientation='h',y=1.05,x=0.5,font=dict(size=11)),barmode='group',margin=dict(l=60,r=20,t=55,b=52))
f.write_image(f'{OUT}/x_normalizacao.png',width=1500,height=1000,scale=2)
json.dump(dict(mass_raw=float(mass_raw),mass_norm=float(mass_norm),pv_raw=float(pv_raw),pv_norm=float(pv_norm),
    sds={l:float(s) for l,s in zip(LAB,sds)}),open('normalizacao.json','w'),indent=1)
print('fig x_normalizacao OK | massa |ρ| %.2f->%.2f | PVfin %.2f->%.2f'%(mass_raw,mass_norm,pv_raw,pv_norm))
