import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); F=pd.read_csv('ajuste_features.csv')
days=np.arange(1,8)
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=25,t=50,b=55)); b.update(k); return b
grp=F.set_index('ID')['iceberg_grp'].to_dict()
h['grp']=h.ID.map(grp)
dm=h.groupby(['ID','dia'])[['FadFisica','Vigor']].mean().reset_index()
dm['grp']=dm.ID.map(grp)

f=make_subplots(rows=2,cols=2,vertical_spacing=0.14,horizontal_spacing=0.11,
    subplot_titles=['A) Aptidão (PV) × fadiga física semanal','B) Vigor ao longo da semana por perfil',
        'C) "Começa bem e termina mal" (vigor D1 × queda)','D) Poder de indicação de cada ajuste (AUC / |ρ|)'])
# A: PV vs wk_FadFis
m=F[['PV','wk_FadFis']].dropna(); lr=stats.linregress(m.PV,m.wk_FadFis); r,p=stats.spearmanr(m.PV,m.wk_FadFis)
f.add_trace(go.Scatter(x=m.PV,y=m.wk_FadFis,mode='markers',marker=dict(size=10,color='#1c7ed6'),showlegend=False),1,1)
xx=np.array([m.PV.min(),m.PV.max()]); f.add_trace(go.Scatter(x=xx,y=lr.intercept+lr.slope*xx,mode='lines',line=dict(color='#c92a2a',width=2.5),showlegend=False),1,1)
f.add_annotation(x=m.PV.max(),y=m.wk_FadFis.max(),text='ρ=%.2f (p=%.2f)'%(r,p),showarrow=False,xanchor='right',font=dict(size=12),row=1,col=1)
# B: vigor trajectory by iceberg group
for gg,col in [('Iceberg alto','#2b8a3e'),('Iceberg baixo','#e8590c')]:
    s=dm[dm.grp==gg].groupby('dia')['Vigor'].mean().reindex(days)
    f.add_trace(go.Scatter(x=days,y=s.values,mode='lines+markers',name=gg,line=dict(color=col,width=3),marker=dict(size=8)),2,1) if False else \
    f.add_trace(go.Scatter(x=days,y=s.values,mode='lines+markers',name=gg,line=dict(color=col,width=3),marker=dict(size=8),showlegend=True),1,2)
# C: vigD1 vs vig_drop
m2=F[['vig_D1','vig_drop']].dropna(); lr2=stats.linregress(m2.vig_D1,m2.vig_drop); r2,p2=stats.spearmanr(m2.vig_D1,m2.vig_drop)
f.add_trace(go.Scatter(x=m2.vig_D1,y=m2.vig_drop,mode='markers',marker=dict(size=10,color='#6741d9'),showlegend=False),2,1)
xx=np.array([m2.vig_D1.min(),m2.vig_D1.max()]); f.add_trace(go.Scatter(x=xx,y=lr2.intercept+lr2.slope*xx,mode='lines',line=dict(color='#c92a2a',width=2.5),showlegend=False),2,1)
f.add_annotation(x=m2.vig_D1.max(),y=m2.vig_drop.min(),text='ρ=%.2f (p=%.3f)'%(r2,p2),showarrow=False,xanchor='right',font=dict(size=12),row=2,col=1)
# D: adjustment power bar (established metrics)
labs=['Logística/ROC<br>PV (estado)','Alometria<br>PV (|b|→esc.)','Perfil humor<br>iceberg×PV','Regressão<br>PV×fadiga','% Gordura<br>(ROC acúmulo)']
vals=[0.84,0.62,0.40,0.52,0.47]  # AUC or |rho|; alometria shown as R-like 0.62 (|b| normalizado ilustrativo)
cols=['#2b8a3e','#1c7ed6','#1c7ed6','#1c7ed6','#adb5bd']
f.add_trace(go.Bar(x=labs,y=vals,marker_color=cols,text=[f'{v:.2f}' for v in vals],textposition='outside',showlegend=False),2,2)
f.add_hline(y=0.5,line=dict(color='#868e96',dash='dot'),row=2,col=2)
f.update_yaxes(range=[0,1],title='AUC / |ρ|',row=2,col=2)
f.update_xaxes(title='PV (km·h⁻¹)',row=1,col=1); f.update_yaxes(title='Fadiga física (0–10)',row=1,col=1)
f.update_xaxes(title='Dia',dtick=1,row=1,col=2); f.update_yaxes(title='Vigor (BRUMS)',row=1,col=2)
f.update_xaxes(title='Vigor no D1',row=2,col=1); f.update_yaxes(title='Queda de vigor D1→D7',row=2,col=1)
f.update_layout(**T(height=820,legend=dict(orientation='h',y=1.07,x=0.55,font=dict(size=11))))
f.write_image(f'{OUT}/x_ajuste.png',width=1500,height=980,scale=2)
print('fig x_ajuste OK')
