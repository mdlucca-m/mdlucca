import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
OUT='/home/user/mdlucca/Artigos/figuras'
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/hum_prof.csv'); h2=hum[hum.momento.isin(['pre','pos'])].copy()
R=json.load(open(f'{SC}/semana2.json')); REG=json.load(open(f'{SC}/reg.json'))
CORE=[('Vigor','Vigor'),('Fadiga','Fadiga (BRUMS)'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental'),('TMD','PTH/TMD')]
CV={'Vigor':'#2b8a3e','Fadiga':'#c92a2a','FadFisica':'#d9480f','FadMental':'#6741d9','TMD':'#0b7285'}
days=np.arange(1,8)
def daily(v): return h2.dropna(subset=[v]).groupby(['ID','dia'])[v].mean().reset_index()
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=25,t=55,b=55)); b.update(k); return b
def save(f,n): f.write_image(f'{OUT}/{n}.png',width=1700,height=1000,scale=2)
POS=[(1,1),(1,2),(1,3),(2,1),(2,2)]

# G histogramas (5 vars)
f=make_subplots(rows=2,cols=3,subplot_titles=[l for _,l in CORE],vertical_spacing=0.13,horizontal_spacing=0.08)
for (v,lab),(r,c) in zip(CORE,POS):
    x=h2[v].dropna(); f.add_trace(go.Histogram(x=x,marker_color=CV[v],opacity=.85,nbinsx=14,showlegend=False),r,c); f.add_vline(x=x.mean(),line=dict(color='#111',width=2,dash='dash'),row=r,col=c)
f.update_layout(**T(height=760,bargap=.05)); f.update_yaxes(title='Freq.'); save(f,'v_hist')

# G boxplots por dia (5 vars)
f=make_subplots(rows=2,cols=3,subplot_titles=[l for _,l in CORE],vertical_spacing=0.13,horizontal_spacing=0.08)
for (v,lab),(r,c) in zip(CORE,POS):
    for dd in days: f.add_trace(go.Box(y=h2[h2.dia==dd][v].dropna(),name=str(dd),marker_color=CV[v],line=dict(color=CV[v]),boxpoints='outliers',showlegend=False),r,c)
f.update_layout(**T(height=760)); f.update_xaxes(title='Dia'); save(f,'v_box')

# G regressão (5 vars)
f=make_subplots(rows=2,cols=3,subplot_titles=[l for _,l in CORE],vertical_spacing=0.14,horizontal_spacing=0.08)
rng=np.random.default_rng(5)
for (v,lab),(r,c) in zip(CORE,POS):
    d=h2.dropna(subset=[v]); rr=REG[v]
    f.add_trace(go.Scatter(x=d['dia']+rng.normal(0,.09,len(d)),y=d[v],mode='markers',marker=dict(color=CV[v],size=4,opacity=.3),showlegend=False),r,c)
    xs=np.array([1,7]); f.add_trace(go.Scatter(x=xs,y=rr['inter']+rr['slope']*xs,mode='lines',line=dict(color='#111',width=3),showlegend=False),r,c)
    f.add_annotation(x=4,y=d[v].max(),text=f"b={rr['slope']:+.2f} · R²={rr['r2']:.2f}".replace('.',','),showarrow=False,font=dict(size=12,color='#111'),row=r,col=c)
f.update_layout(**T(height=760)); f.update_xaxes(dtick=1,title='Dia'); save(f,'v_reg')

# G trajetória (5 vars)
f=make_subplots(rows=2,cols=3,subplot_titles=[l for _,l in CORE],vertical_spacing=0.13,horizontal_spacing=0.08)
for (v,lab),(r,c) in zip(CORE,POS):
    d=daily(v); dm=d.groupby('dia')[v].mean(); sd=d.groupby('dia')[v].std(); dd=h2.dropna(subset=[v]); lo=lowess(dd[v],dd['dia'],frac=.6,return_sorted=True)
    f.add_trace(go.Scatter(x=list(days)+list(days[::-1]),y=list(dm.values+sd.values)+list((dm.values-sd.values)[::-1]),fill='toself',fillcolor='rgba(120,120,120,0.12)',line=dict(width=0),mode='lines',showlegend=False,hoverinfo='skip'),r,c)
    f.add_trace(go.Scatter(x=days,y=dm.values,mode='lines+markers',line=dict(color=CV[v],width=3),marker=dict(size=6),showlegend=False),r,c)
    f.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',line=dict(color='#333',width=1.4,dash='dot'),showlegend=False),r,c)
f.update_layout(**T(height=760)); f.update_xaxes(dtick=1,title='Dia'); save(f,'v_traj')

# G derivadas + inflexão (5 vars) — dual axis
f=make_subplots(rows=2,cols=3,subplot_titles=[l for _,l in CORE],vertical_spacing=0.14,horizontal_spacing=0.09,specs=[[{"secondary_y":True}]*3]*2)
gx=np.linspace(1,7,120)
for (v,lab),(r,c) in zip(CORE,POS):
    dm=np.array(R['der'][v]['daymean']); cc=np.polyfit(days,dm,3)
    f.add_trace(go.Scatter(x=gx,y=np.polyval(np.polyder(cc,1),gx),mode='lines',line=dict(color=CV[v],width=3),name='velocidade',showlegend=(r==1 and c==1)),r,c,secondary_y=False)
    f.add_trace(go.Scatter(x=gx,y=np.polyval(np.polyder(cc,2),gx),mode='lines',line=dict(color='#868e96',width=2,dash='dash'),name='aceleração',showlegend=(r==1 and c==1)),r,c,secondary_y=True)
    f.add_hline(y=0,line=dict(color='#bbb',dash='dot'),row=r,col=c)
    if R['der'][v]['infl']: f.add_vline(x=R['der'][v]['infl'],line=dict(color='#111',width=1.5,dash='dash'),row=r,col=c)
f.update_layout(**T(height=760,legend=dict(orientation='h',y=-0.08))); f.update_xaxes(dtick=1,title='Dia'); save(f,'v_deriv')

# G deterioração z (5 vars: vigor down, fadigas+TMD up)
f=go.Figure()
for v,lab in CORE:
    d=h2.dropna(subset=[v]); z=(d[v]-h2[v].mean())/h2[v].std(); dm=pd.Series(z.values,index=d['dia'].values).groupby(level=0).mean().reindex(days); lr=stats.linregress(d['dia'],z)
    f.add_trace(go.Scatter(x=days,y=dm.values,mode='markers',marker=dict(color=CV[v],size=8),showlegend=False))
    xs=np.array([1,7]); f.add_trace(go.Scatter(x=xs,y=lr.intercept+lr.slope*xs,mode='lines',name=lab,line=dict(color=CV[v],width=4)))
f.add_hline(y=0,line=dict(color='#888',dash='dot'))
f.update_layout(**T(height=580,legend=dict(orientation='h',y=-0.18)),xaxis=dict(dtick=1,title='Dia'),yaxis_title='Escore padronizado (z)'); save(f,'v_deter')

# G TMD composto (trajetória + pré/pós por dia + boxplot)
f=make_subplots(rows=1,cols=3,subplot_titles=['Trajetória (M ± DP; LOWESS)','Pré vs pós por dia','Distribuição por dia'],horizontal_spacing=0.08)
d=daily('TMD'); dm=d.groupby('dia')['TMD'].mean(); sd=d.groupby('dia')['TMD'].std(); dd=h2.dropna(subset=['TMD']); lo=lowess(dd['TMD'],dd['dia'],frac=.6,return_sorted=True)
f.add_trace(go.Scatter(x=list(days)+list(days[::-1]),y=list(dm.values+sd.values)+list((dm.values-sd.values)[::-1]),fill='toself',fillcolor='rgba(11,114,133,0.12)',line=dict(width=0),mode='lines',showlegend=False,hoverinfo='skip'),1,1)
f.add_trace(go.Scatter(x=days,y=dm.values,mode='lines+markers',line=dict(color=CV['TMD'],width=3),marker=dict(size=7),showlegend=False),1,1)
f.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',line=dict(color='#333',width=1.5,dash='dot'),showlegend=False),1,1)
pre=[h2[(h2.dia==dd_)&(h2.momento=='pre')]['TMD'].mean() for dd_ in days]; pos=[h2[(h2.dia==dd_)&(h2.momento=='pos')]['TMD'].mean() for dd_ in days]
f.add_trace(go.Bar(x=list(days),y=pre,name='pré',marker_color='#1c7ed6',showlegend=True),1,2)
f.add_trace(go.Bar(x=list(days),y=pos,name='pós',marker_color=CV['TMD'],showlegend=True),1,2)
for dd_ in days: f.add_trace(go.Box(y=h2[h2.dia==dd_]['TMD'].dropna(),name=str(dd_),marker_color=CV['TMD'],line=dict(color=CV['TMD']),boxpoints='outliers',showlegend=False),1,3)
f.update_layout(**T(height=560,legend=dict(orientation='h',y=-0.2))); f.update_xaxes(dtick=1,title='Dia'); save(f,'v_tmd')

# G ranked individual delta D1->D7 (replaces heatmap) — Vigor & Fadiga física
f=make_subplots(rows=1,cols=2,subplot_titles=['Vigor','Fadiga física'],horizontal_spacing=0.13)
for j,v in enumerate(['Vigor','FadFisica'],1):
    w=daily(v).pivot(index='ID',columns='dia',values=v); d=(w[7]-w[1]).dropna().sort_values()
    f.add_trace(go.Bar(x=d.values,y=d.index,orientation='h',marker_color=[CV[v] if (val>0)==(v!='Vigor') else '#adb5bd' for val in d.values],showlegend=False),1,j)
    f.add_vline(x=0,line=dict(color='#111',width=1),row=1,col=j)
f.update_layout(**T(height=760)); f.update_xaxes(title='Δ D7 − D1'); f.update_yaxes(title='Atleta',tickfont=dict(size=9)); save(f,'v_delta')

# F individual MERGED (2x2): trajetórias (top) + pré/pós (bottom), Vigor & FadFisica
f=make_subplots(rows=2,cols=2,subplot_titles=['Vigor — trajetória individual','Fadiga física — trajetória individual','Vigor — resposta pré→pós','Fadiga física — resposta pré→pós'],vertical_spacing=0.13,horizontal_spacing=0.12)
for j,v in enumerate(['Vigor','FadFisica'],1):
    w=daily(v).pivot(index='ID',columns='dia',values=v)
    for aid in w.index: f.add_trace(go.Scatter(x=days,y=w.loc[aid].reindex(days).values,mode='lines',line=dict(color='rgba(120,120,120,0.30)',width=1),showlegend=False),1,j)
    f.add_trace(go.Scatter(x=days,y=w.mean().reindex(days).values,mode='lines+markers',line=dict(color=CV[v],width=4),marker=dict(size=7),showlegend=False),1,j)
    pre=h2[h2.momento=='pre'].groupby('ID')[v].mean(); pos=h2[h2.momento=='pos'].groupby('ID')[v].mean(); c=pre.index.intersection(pos.index)
    for aid in c: f.add_trace(go.Scatter(x=['Pré','Pós'],y=[pre[aid],pos[aid]],mode='lines',line=dict(color='rgba(120,120,120,0.35)',width=1),showlegend=False),2,j)
    f.add_trace(go.Scatter(x=['Pré','Pós'],y=[pre[c].mean(),pos[c].mean()],mode='lines+markers',line=dict(color=CV[v],width=5),marker=dict(size=10),showlegend=False),2,j)
f.update_layout(**T(height=820)); f.update_xaxes(dtick=1,row=1); save(f,'v_individual')
print('figs3 OK')
