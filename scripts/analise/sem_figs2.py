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
CORE=[('Vigor','Vigor'),('Fadiga','Fadiga (BRUMS)'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental')]
CV={'Vigor':'#2b8a3e','Fadiga':'#c92a2a','FadFisica':'#d9480f','FadMental':'#6741d9'}
days=np.arange(1,8)
def T(**k):
    base=dict(template='plotly_white',font=dict(color='#111',size=16,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=70,r=30,t=60,b=70)); base.update(k); return base
def save(f,n): f.write_image(f'{OUT}/{n}.png',width=1600,height=900,scale=2)

# ---- regression stats per variable (obs over week) ----
reg={}
for v,lab in CORE+[('TMD','PTH/TMD'),('ice_idx','Índice-iceberg')]:
    d=h2.dropna(subset=[v]) if v in h2 else hum.dropna(subset=[v])
    src=h2 if v in ['Vigor','Fadiga','FadFisica','FadMental','TMD'] else hum
    d=src.dropna(subset=[v])
    lr=stats.linregress(d['dia'],d[v])
    reg[v]=dict(lab=lab,slope=float(lr.slope),inter=float(lr.intercept),r2=float(lr.rvalue**2),p=float(lr.pvalue))
json.dump(reg,open(f'{SC}/reg.json','w'),indent=1)
print('REGRESSÃO (coef/dia, R2, p):')
for v,lab in CORE: r=reg[v]; print('  %-16s b=%+.3f R2=%.3f p=%.1e'%(lab,r['slope'],r['r2'],r['p']))

# ---- FIG histogramas (distribuição) 2x2 ----
f=make_subplots(rows=2,cols=2,subplot_titles=[l for _,l in CORE],vertical_spacing=0.14,horizontal_spacing=0.1)
for (v,lab),(r,c) in zip(CORE,[(1,1),(1,2),(2,1),(2,2)]):
    x=h2[v].dropna()
    f.add_trace(go.Histogram(x=x,marker_color=CV[v],opacity=0.8,nbinsx=14,showlegend=False),r,c)
    f.add_vline(x=x.mean(),line=dict(color='#111',width=2,dash='dash'),row=r,col=c)
f.update_layout(**T(height=820,bargap=0.05)); f.update_yaxes(title='Frequência'); save(f,'sem_f_hist')

# ---- FIG boxplots por dia 2x2 ----
f=make_subplots(rows=2,cols=2,subplot_titles=[l for _,l in CORE],vertical_spacing=0.14,horizontal_spacing=0.1)
for (v,lab),(r,c) in zip(CORE,[(1,1),(1,2),(2,1),(2,2)]):
    for dd in days:
        f.add_trace(go.Box(y=h2[h2.dia==dd][v].dropna(),name=str(dd),marker_color=CV[v],line=dict(color=CV[v]),
            boxpoints='outliers',showlegend=False),r,c)
f.update_layout(**T(height=820)); f.update_xaxes(title='Dia'); save(f,'sem_f_boxplot')

# ---- FIG regressão linear 2x2 (scatter + reta + R2) ----
f=make_subplots(rows=2,cols=2,subplot_titles=[l for _,l in CORE],vertical_spacing=0.15,horizontal_spacing=0.1)
rng=np.random.default_rng(5)
for (v,lab),(r,c) in zip(CORE,[(1,1),(1,2),(2,1),(2,2)]):
    d=h2.dropna(subset=[v]); rr=reg[v]
    f.add_trace(go.Scatter(x=d['dia']+rng.normal(0,0.09,len(d)),y=d[v],mode='markers',marker=dict(color=CV[v],size=5,opacity=.3),showlegend=False),r,c)
    xs=np.array([1,7]); f.add_trace(go.Scatter(x=xs,y=rr['inter']+rr['slope']*xs,mode='lines',line=dict(color='#111',width=3),showlegend=False),r,c)
    f.add_annotation(x=4,y=d[v].max(),text=f"b = {rr['slope']:+.2f}/dia · R² = {rr['r2']:.2f}".replace('.',','),showarrow=False,font=dict(size=13,color='#111'),row=r,col=c)
f.update_layout(**T(height=820)); f.update_xaxes(dtick=1,title='Dia'); save(f,'sem_f_regressao')

# ---- FIG deterioração do eixo (z padronizado: vigor / fadiga / fadiga física) ----
f=go.Figure()
for v,lab in [('Vigor','Vigor'),('Fadiga','Fadiga (BRUMS)'),('FadFisica','Fadiga física')]:
    d=h2.dropna(subset=[v]); z=(d[v]-h2[v].mean())/h2[v].std()
    dm=pd.Series(z.values,index=d['dia'].values).groupby(level=0).mean().reindex(days)
    lr=stats.linregress(d['dia'],z)
    f.add_trace(go.Scatter(x=days,y=dm.values,mode='markers',marker=dict(color=CV[v],size=9),showlegend=False))
    xs=np.array([1,7]); f.add_trace(go.Scatter(x=xs,y=lr.intercept+lr.slope*xs,mode='lines',name=lab,line=dict(color=CV[v],width=4)))
f.add_hline(y=0,line=dict(color='#888',dash='dot'))
f.update_layout(**T(height=560,legend=dict(orientation='h',y=-0.18)),xaxis=dict(dtick=1,title='Dia'),yaxis_title='Escore padronizado (z)')
save(f,'sem_f_deterioracao')

# ---- FIG iceberg ao longo da semana (composto: % iceberg barras + índice linha) ----
di=hum.dropna(subset=['ice_idx']); iceday=di.groupby('dia')['ice_idx'].mean().reindex(days)
pice=[100*(hum[hum.dia==dd]['perfil']=='Iceberg').mean() for dd in days]
lr=stats.linregress(di['dia'],di['ice_idx']); lo=lowess(di['ice_idx'],di['dia'],frac=0.6,return_sorted=True)
f=make_subplots(specs=[[{"secondary_y":True}]])
f.add_trace(go.Bar(x=days,y=pice,name='% perfil iceberg',marker_color='#a5d8ff',opacity=0.85),secondary_y=False)
f.add_trace(go.Scatter(x=days,y=iceday.values,mode='lines+markers',name='índice-iceberg (z)',line=dict(color='#1c7ed6',width=3),marker=dict(size=8)),secondary_y=True)
xs=np.array([1,7]); f.add_trace(go.Scatter(x=xs,y=lr.intercept+lr.slope*xs,mode='lines',name=f"regressão (b={lr.slope:+.2f}/dia; R²={lr.rvalue**2:.2f})".replace('.',','),line=dict(color='#111',width=2,dash='dash')),secondary_y=True)
f.update_layout(**T(height=560,legend=dict(orientation='h',y=-0.2)),xaxis=dict(dtick=1,title='Dia'))
f.update_yaxes(title_text='% em perfil iceberg',secondary_y=False); f.update_yaxes(title_text='Índice-iceberg (z)',secondary_y=True)
save(f,'sem_f_iceberg')
print('figs2 OK')
