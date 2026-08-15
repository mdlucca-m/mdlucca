import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.nonparametric.smoothers_lowess import lowess
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
OUT='/home/user/mdlucca/Artigos/figuras'
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/hum_prof.csv'); h2=hum[hum.momento.isin(['pre','pos'])].copy()
R=json.load(open(f'{SC}/semana.json'))
CORE=[('Vigor','Vigor'),('Fadiga','Fadiga (BRUMS)'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental')]
CV={'Vigor':'#2b8a3e','Fadiga':'#c92a2a','FadFisica':'#d9480f','FadMental':'#6741d9'}
days=np.arange(1,8)
def daily(v): return h2.dropna(subset=[v]).groupby(['ID','dia'])[v].mean().reset_index()
def T(**k):
    base=dict(template='plotly_white',font=dict(color='#111',size=16,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=70,r=30,t=60,b=70)); base.update(k); return base
def save(f,n): f.write_image(f'{OUT}/{n}.png',width=1600,height=900,scale=2)

# S1: perfil médio D1 vs D7 (radar z) — profile shape
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']; LB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
Z=hum[SUB].apply(lambda c:(c-c.mean())/c.std()); Zc=pd.concat([hum[['dia']],Z],axis=1)
f=go.Figure()
for dd,c in [(1,'#1c7ed6'),(7,'#c92a2a')]:
    r=Zc[Zc.dia==dd][SUB].mean().values
    f.add_trace(go.Scatterpolar(r=list(r)+[r[0]],theta=LB+[LB[0]],name=f'Dia {dd}',line=dict(color=c,width=3),fill='toself',opacity=.35))
f.update_layout(**T(height=620),polar=dict(bgcolor='white',radialaxis=dict(gridcolor='#ddd'),angularaxis=dict(gridcolor='#ddd')),legend=dict(orientation='h',y=-0.05))
save(f,'sem_f_radar')

# S2: trajetória semanal das 4 vars (M±DP + LOWESS), SEM marcação de HIIT
f=make_subplots(rows=2,cols=2,subplot_titles=[l for _,l in CORE],vertical_spacing=0.14,horizontal_spacing=0.1)
for (v,lab),(r,c) in zip(CORE,[(1,1),(1,2),(2,1),(2,2)]):
    d=daily(v); dm=d.groupby('dia')[v].mean(); sd=d.groupby('dia')[v].std()
    dd=h2.dropna(subset=[v]); lo=lowess(dd[v],dd['dia'],frac=0.6,return_sorted=True)
    f.add_trace(go.Scatter(x=list(days)+list(days[::-1]),y=list(dm.values+sd.values)+list((dm.values-sd.values)[::-1]),fill='toself',fillcolor='rgba(120,120,120,0.13)',line=dict(width=0),mode='lines',showlegend=False,hoverinfo='skip'),r,c)
    f.add_trace(go.Scatter(x=days,y=dm.values,mode='lines+markers',line=dict(color=CV[v],width=3),marker=dict(size=7),showlegend=False),r,c)
    f.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',line=dict(color='#333',width=1.5,dash='dot'),showlegend=False),r,c)
f.update_layout(**T(height=820)); f.update_xaxes(dtick=1,title='Dia'); save(f,'sem_f_trajetoria')

# S3: pré vs pós por dia (barras) das 4 vars — efeito agudo
f=make_subplots(rows=2,cols=2,subplot_titles=[l for _,l in CORE],vertical_spacing=0.14,horizontal_spacing=0.1)
for (v,lab),(r,c) in zip(CORE,[(1,1),(1,2),(2,1),(2,2)]):
    pre=[h2[(h2.dia==dd)&(h2.momento=='pre')][v].mean() for dd in days]
    pos=[h2[(h2.dia==dd)&(h2.momento=='pos')][v].mean() for dd in days]
    f.add_trace(go.Bar(x=list(days),y=pre,name='pré',marker_color='#1c7ed6',showlegend=(r==1 and c==1)),r,c)
    f.add_trace(go.Bar(x=list(days),y=pos,name='pós',marker_color=CV[v],showlegend=(r==1 and c==1)),r,c)
f.update_layout(**T(height=820,barmode='group',bargap=0.25,legend=dict(orientation='h',y=-0.12))); f.update_xaxes(dtick=1,title='Dia'); save(f,'sem_f_prepos')

# S4: derivadas (velocidade/aceleração) + inflexão por variável (cubic)
f=make_subplots(rows=2,cols=2,subplot_titles=[l for _,l in CORE],vertical_spacing=0.15,horizontal_spacing=0.1,specs=[[{"secondary_y":True}]*2]*2)
gx=np.linspace(1,7,120)
for (v,lab),(r,c) in zip(CORE,[(1,1),(1,2),(2,1),(2,2)]):
    dm=np.array(R['der'][v]['daymean']); cc=np.polyfit(days,dm,3)
    vel=np.polyval(np.polyder(cc,1),gx); acc=np.polyval(np.polyder(cc,2),gx)
    f.add_trace(go.Scatter(x=gx,y=vel,mode='lines',line=dict(color=CV[v],width=3),name='velocidade',showlegend=(r==1 and c==1)),r,c,secondary_y=False)
    f.add_trace(go.Scatter(x=gx,y=acc,mode='lines',line=dict(color='#868e96',width=2,dash='dash'),name='aceleração',showlegend=(r==1 and c==1)),r,c,secondary_y=True)
    f.add_hline(y=0,line=dict(color='#bbb',dash='dot'),row=r,col=c)
    inf=R['der'][v]['infl']
    if inf: f.add_vline(x=inf,line=dict(color='#111',width=1.5,dash='dash'),row=r,col=c)
f.update_layout(**T(height=820,legend=dict(orientation='h',y=-0.1))); f.update_xaxes(dtick=1,title='Dia'); save(f,'sem_f_derivadas')

# S5: decomposição sinal/traço/ruído (barras empilhadas)
xs=[l for _,l in CORE]; dec=R['dec']
f=go.Figure()
f.add_trace(go.Bar(x=xs,y=[dec[v]['pday'] for v,_ in CORE],name='Sinal (semana)',marker_color='#c92a2a'))
f.add_trace(go.Bar(x=xs,y=[dec[v]['ptrait'] for v,_ in CORE],name='Traço (entre atletas)',marker_color='#1c7ed6'))
f.add_trace(go.Bar(x=xs,y=[dec[v]['pnoise'] for v,_ in CORE],name='Ruído',marker_color='#adb5bd'))
f.update_layout(**T(height=560,barmode='stack',legend=dict(orientation='h',y=-0.18)),yaxis_title='% da variância'); save(f,'sem_f_decomp')

# S6: com vs sem ruído (índice-iceberg + LOWESS + inflexão) — filtro/suavização
di=hum.dropna(subset=['ice_idx']); iceday=di.groupby('dia')['ice_idx'].mean().reindex(days).values
lo=lowess(di['ice_idx'],di['dia'],frac=0.6,return_sorted=True); rng=np.random.default_rng(7)
f=go.Figure()
f.add_trace(go.Scatter(x=di['dia']+rng.normal(0,0.06,len(di)),y=di['ice_idx'],mode='markers',name='observações (ruído)',marker=dict(color='#74c0fc',size=5,opacity=.4)))
f.add_trace(go.Scatter(x=days,y=iceday,mode='lines+markers',name='média diária (com ruído)',line=dict(color='#e67700',width=2,dash='dot'),marker=dict(size=8)))
f.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',name='LOWESS (sem ruído)',line=dict(color='#c92a2a',width=4)))
f.add_vline(x=R['ice']['infl'],line=dict(color='#111',width=2.5,dash='dash'))
f.add_annotation(x=R['ice']['infl'],y=di['ice_idx'].max(),text=f"inflexão dia {R['ice']['infl']:.1f}",showarrow=False,yshift=10,font=dict(color='#111',size=14))
f.add_hline(y=0,line=dict(color='#888',dash='dot'))
f.update_layout(**T(height=560,legend=dict(orientation='h',y=-0.2)),xaxis=dict(dtick=1,title='Dia'),yaxis_title='Índice-iceberg (z)'); save(f,'sem_f_ruido')

# S7: efeito agudo vs crônico (|dz|) por variável
agu=R['agu']; cron=R['cron']
f=go.Figure()
f.add_trace(go.Bar(x=[l for _,l in CORE],y=[abs(agu[v]['dz']) for v,_ in CORE],name='Agudo (pré→pós)',marker_color='#4dabf7'))
f.add_trace(go.Bar(x=[l for _,l in CORE],y=[abs(cron[v]['dz']) for v,_ in CORE],name='Crônico (D1→D7)',marker_color='#c92a2a'))
f.update_layout(**T(height=520,barmode='group',legend=dict(orientation='h',y=-0.18)),yaxis_title='|dz| (tamanho de efeito)'); save(f,'sem_f_agudo_cronico')

# S8: perfis (%) ao longo da semana (área empilhada) — sem HIIT
PROF=['Iceberg','Barbatana tubarão','Superfície','Submerso','Iceberg invertido','Everest invertido']
PCOL={'Iceberg':'#1c7ed6','Barbatana tubarão':'#c92a2a','Superfície':'#868e96','Submerso':'#7048e8','Iceberg invertido':'#e8590c','Everest invertido':'#c2255c'}
tab=pd.crosstab(hum['dia'],hum['perfil'],normalize='index').mul(100).reindex(columns=PROF).fillna(0)
f=go.Figure()
for pr in PROF:
    f.add_trace(go.Scatter(x=tab.index,y=tab[pr],mode='lines',stackgroup='one',name=pr,line=dict(width=0.5,color=PCOL[pr]),fillcolor=PCOL[pr]))
f.update_layout(**T(height=560,legend=dict(orientation='h',y=-0.15)),xaxis=dict(dtick=1,title='Dia'),yaxis_title='% dos atletas'); save(f,'sem_f_perfis')

# S9: variação individual D1->D7 (Vigor & FadFisica) — cada atleta uma linha
f=make_subplots(rows=1,cols=2,subplot_titles=['Vigor','Fadiga física'],horizontal_spacing=0.12)
for j,(v) in enumerate(['Vigor','FadFisica'],1):
    d=daily(v).pivot(index='ID',columns='dia',values=v)
    for aid in d.index:
        y=d.loc[aid].reindex(days).values
        f.add_trace(go.Scatter(x=days,y=y,mode='lines',line=dict(color='rgba(120,120,120,0.35)',width=1),showlegend=False),1,j)
    dm=d.mean().reindex(days).values
    f.add_trace(go.Scatter(x=days,y=dm,mode='lines+markers',line=dict(color=CV[v],width=4),marker=dict(size=8),showlegend=False),1,j)
f.update_layout(**T(height=520)); f.update_xaxes(dtick=1,title='Dia'); save(f,'sem_f_individual')
print('semana figs OK')
