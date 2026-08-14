import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.nonparametric.smoothers_lowess import lowess
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
OUT='/home/user/mdlucca/Artigos/figuras'; os.makedirs(OUT,exist_ok=True)
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/humor.csv'); hp=pd.read_csv(f'{SC}/hum_prof.csv')
amp=json.load(open(f'{SC}/amp_docx.json')); grp=amp['grp']
AMP=json.load(open(f'{SC}/amp_data.json')); sn=AMP['sn']
DN=json.load(open(f'{SC}/denoise.json')); PP=json.load(open(f'{SC}/prepost.json'))
INF=json.load(open(f'{SC}/inflexao.json'))
W=1600; Hh=900  # export size (white, print-friendly)
def T(**k):
    base=dict(template='plotly_white',font=dict(color='#111',size=16,family='Arial'),
              paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=70,r=30,t=70,b=70))
    base.update(k); return base
def save(f,n): f.write_image(f'{OUT}/{n}.png',width=W,height=Hh,scale=2)
# ABNT-friendly saturated palette on white
CV={'Vigor':'#2b8a3e','Fadiga':'#c92a2a','TMD':'#5f3dc4','FadMental':'#e67700','FadFisica':'#c92a2a'}
LB={'Vigor':'Vigor','Fadiga':'Fadiga BRUMS','TMD':'PTH/TMD','FadMental':'Fadiga mental','FadFisica':'Fadiga física'}
HIIT=dict(line=dict(color='#c92a2a',width=1,dash='dot'))

# ---- F: adx1 grupo semana (4 vars trajectory) ----
V4=['Vigor','Fadiga','TMD','FadMental']
fig=make_subplots(rows=2,cols=2,subplot_titles=[LB[v] for v in V4],vertical_spacing=0.14,horizontal_spacing=0.1)
for v,(r,c) in zip(V4,[(1,1),(1,2),(2,1),(2,2)]):
    d=hum.dropna(subset=[v]); dm=d.groupby('dia')[v].mean(); sd=d.groupby('dia')[v].std()
    lo=lowess(d[v],d['dia'],frac=0.6,return_sorted=True); days=dm.index.values
    fig.add_trace(go.Scatter(x=list(days)+list(days[::-1]),y=list(dm.values+sd.values)+list((dm.values-sd.values)[::-1]),fill='toself',fillcolor='rgba(120,120,120,0.13)',line=dict(width=0),mode='lines',showlegend=False,hoverinfo='skip'),r,c)
    fig.add_trace(go.Scatter(x=days,y=dm.values,mode='lines+markers',line=dict(color=CV[v],width=3),marker=dict(size=7),showlegend=False),r,c)
    fig.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',line=dict(color='#333',width=1.5,dash='dot'),showlegend=False),r,c)
    for dd in (2,4,7): fig.add_vline(x=dd,row=r,col=c,**HIIT)
fig.update_layout(**T(height=820)); fig.update_xaxes(dtick=1,title='Dia'); save(fig,'abnt_f1_trajetoria')

# ---- F: amp_a variancia ----
order=['FadFisica','Fadiga','Vigor','TMD','FadMental','Raiva','Confusao','Depressao','Tensao']
LBx={**LB,'Raiva':'Raiva','Confusao':'Confusão','Depressao':'Depressão','Tensao':'Tensão'}
xs=[LBx[v] for v in order]
fig=go.Figure()
fig.add_trace(go.Bar(x=xs,y=[sn[v]['pday'] for v in order],name='Sinal do microciclo',marker_color='#c92a2a'))
fig.add_trace(go.Bar(x=xs,y=[sn[v]['ptrait'] for v in order],name='Traço (entre atletas)',marker_color='#1c7ed6'))
fig.add_trace(go.Bar(x=xs,y=[sn[v]['pnoise'] for v in order],name='Ruído (resíduo)',marker_color='#adb5bd'))
fig.update_layout(**T(barmode='stack',height=560,legend=dict(orientation='h',y=-0.25),xaxis_tickangle=-20),yaxis_title='% da variância')
save(fig,'abnt_f_variancia')

# ---- F: adx6 pré/mid/pós ----
fig=make_subplots(rows=2,cols=2,subplot_titles=[LB[v] for v in V4],vertical_spacing=0.14,horizontal_spacing=0.1)
for v,(r,c) in zip(V4,[(1,1),(1,2),(2,1),(2,2)]):
    days=list(range(1,8))
    pre=[PP[v][str(d)]['pre_m'] for d in days]; mid=[PP[v][str(d)]['mid_m'] for d in days]; pos=[PP[v][str(d)]['pos_m'] for d in days]
    fig.add_trace(go.Bar(x=days,y=pre,name='pré',marker_color='#1c7ed6',showlegend=(r==1 and c==1)),r,c)
    fig.add_trace(go.Bar(x=days,y=mid,name='mid',marker_color='#adb5bd',showlegend=(r==1 and c==1)),r,c)
    fig.add_trace(go.Bar(x=days,y=pos,name='pós',marker_color=CV[v],showlegend=(r==1 and c==1)),r,c)
    for d in days:
        rr=PP[v][str(d)]
        if rr['p'] is not None and rr['p']<0.05:
            fig.add_annotation(x=d,y=max([x for x in [rr['pre_m'],rr['mid_m'],rr['pos_m']] if x is not None])+0.5,text='*',showarrow=False,font=dict(size=20,color='#111'),row=r,col=c)
fig.update_layout(**T(height=820,barmode='group',bargap=0.25,bargroupgap=0.06,legend=dict(orientation='h',y=-0.12))); fig.update_xaxes(dtick=1); save(fig,'abnt_f_prepos')

# ---- F: adx3 heatmap per athlete ----
ids=sorted(hum['ID'].unique()); M=[]
for aid in ids:
    M.append([ (lambda g: g[v].max()-g[v].min() if len(g) else np.nan)(hum[(hum.ID==aid)].dropna(subset=[v])) for v in V4])
M=pd.DataFrame(M,index=ids,columns=[LB[v] for v in V4]); Mz=(M-M.mean())/M.std(); ordr=Mz.mean(axis=1).sort_values().index
fig=go.Figure(go.Heatmap(z=Mz.loc[ordr].values,x=list(M.columns),y=list(ordr),colorscale='RdBu',reversescale=True,zmid=0,colorbar=dict(title='ampl. (z)')))
fig.update_layout(**T(height=800)); save(fig,'abnt_f_heatmap')

# ---- F: den1 correlations obs vs denoised ----
keys=['Vigor','Fadiga','TMD','FadMental']
def MM(d): return pd.DataFrame(d).loc[keys,keys]
Robs=MM(DN['Robs']); Rden=MM(DN['Rden'])
fig=make_subplots(rows=1,cols=2,subplot_titles=['Observada (com ruído)','Sem ruído (nível-grupo)'],horizontal_spacing=0.16)
for j,Mx in enumerate([Robs,Rden],1):
    fig.add_trace(go.Heatmap(z=Mx.values,x=[LB[k] for k in keys],y=[LB[k] for k in keys],zmin=-1,zmax=1,colorscale='RdBu',reversescale=True,text=Mx.round(2).values,texttemplate='%{text}',textfont=dict(size=16,color='#111'),showscale=(j==2),colorbar=dict(title='r')),1,j)
fig.update_layout(**T(height=560)); save(fig,'abnt_f_corr')

# ---- F: den3 MDC vs k ----
km=DN['kmdc']; sig={v:sn.get(v,{}).get('sig',None) for v in keys}
sig={'Vigor':2.83,'Fadiga':3.74,'TMD':6.24,'FadMental':0.92}
fig=make_subplots(rows=2,cols=2,subplot_titles=[LB[v] for v in keys],vertical_spacing=0.15,horizontal_spacing=0.1)
for v,(r,c) in zip(keys,[(1,1),(1,2),(2,1),(2,2)]):
    ks=[1,2,3,5,7]; mdc=[km[v][str(x)] for x in ks]
    fig.add_trace(go.Scatter(x=ks,y=mdc,mode='lines+markers',line=dict(color=CV[v],width=3),marker=dict(size=8),showlegend=False),r,c)
    fig.add_hline(y=sig[v],line=dict(color='#111',dash='dash',width=1.5),row=r,col=c)
fig.update_layout(**T(height=760)); fig.update_xaxes(title='nº de coletas (k)',dtick=1); fig.update_yaxes(title='unidades'); save(fig,'abnt_f_mdck')

# ---- F: pf2 dissociacao física×mental ----
fig=go.Figure()
for v in ['FadFisica','FadMental']:
    d=hum.dropna(subset=[v]); lo=lowess(d[v],d['dia'],frac=0.6,return_sorted=True); dm=d.groupby('dia')[v].mean()
    fig.add_trace(go.Scatter(x=dm.index,y=dm.values,mode='markers',marker=dict(color=CV[v],size=8,opacity=.5),showlegend=False))
    fig.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',name=LB[v],line=dict(color=CV[v],width=4)))
fig.update_layout(**T(height=520,legend=dict(orientation='h',y=-0.18)),xaxis=dict(dtick=1,title='Dia'),yaxis=dict(title='Escore (0–10)',range=[0,10]))
save(fig,'abnt_f_fisica_mental')

# ---- F: pv2 vigor×TMD (z) ----
fig=go.Figure()
for v in ['Vigor','TMD']:
    d=hum.dropna(subset=[v]); z=(d[v]-hum[v].mean())/hum[v].std()
    dz=pd.Series(z.values,index=d['dia'].values).groupby(level=0).mean(); lo=lowess(z,d['dia'],frac=0.6,return_sorted=True)
    fig.add_trace(go.Scatter(x=dz.index,y=dz.values,mode='markers',marker=dict(color=CV[v],size=8,opacity=.5),showlegend=False))
    fig.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',name=LB[v],line=dict(color=CV[v],width=4)))
fig.add_hline(y=0,line=dict(color='#888',dash='dot'))
fig.update_layout(**T(height=520,legend=dict(orientation='h',y=-0.18)),xaxis=dict(dtick=1,title='Dia'),yaxis=dict(title='Escore padronizado (z)'))
save(fig,'abnt_f_vigor_tmd')

# ---- F: profiles stacked area + inflection ----
PROF=['Iceberg','Barbatana tubarão','Superfície','Submerso','Iceberg invertido','Everest invertido']
PCOL={'Iceberg':'#1c7ed6','Barbatana tubarão':'#c92a2a','Superfície':'#868e96','Submerso':'#7048e8','Iceberg invertido':'#e8590c','Everest invertido':'#c2255c'}
tab=pd.crosstab(hp['dia'],hp['perfil'],normalize='index').mul(100).reindex(columns=PROF).fillna(0)
fig=go.Figure()
for pr in PROF:
    fig.add_trace(go.Scatter(x=tab.index,y=tab[pr],mode='lines',stackgroup='one',name=pr,line=dict(width=0.5,color=PCOL[pr]),fillcolor=PCOL[pr]))
fig.add_vline(x=INF['infl_sm'],line=dict(color='#111',width=2.5,dash='dash'))
fig.add_annotation(x=INF['infl_sm'],y=100,text=f"inflexão ≈ dia {INF['infl_sm']:.1f}",showarrow=False,yshift=12,font=dict(color='#111',size=14))
fig.update_layout(**T(height=560,legend=dict(orientation='h',y=-0.15)),xaxis=dict(dtick=1,title='Dia'),yaxis_title='% dos atletas')
save(fig,'abnt_f_perfis')

# ---- F: iceberg index raw vs LOWESS + inflection ----
d=hp.dropna(subset=['ice_idx']); days=np.arange(1,8); rng=np.random.default_rng(7)
raw=d.groupby('dia')['ice_idx'].mean().reindex(days).values; lo=lowess(d['ice_idx'],d['dia'],frac=0.6,return_sorted=True)
cc=INF['ci_clean']
fig=go.Figure()
fig.add_trace(go.Scatter(x=d['dia']+rng.normal(0,0.06,len(d)),y=d['ice_idx'],mode='markers',name='observações (ruído)',marker=dict(color='#74c0fc',size=5,opacity=.4)))
fig.add_trace(go.Scatter(x=days,y=raw,mode='lines+markers',name='média diária (com ruído)',line=dict(color='#e67700',width=2,dash='dot'),marker=dict(size=8)))
fig.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',name='LOWESS (sem ruído)',line=dict(color='#c92a2a',width=4)))
fig.add_vrect(x0=cc[0],x1=cc[2],fillcolor='rgba(0,0,0,0.06)',line_width=0)
fig.add_vline(x=cc[1],line=dict(color='#111',width=2.5,dash='dash'))
fig.add_annotation(x=cc[1],y=d['ice_idx'].max(),text=f"inflexão dia {cc[1]:.1f}",showarrow=False,yshift=10,font=dict(color='#111',size=13))
fig.add_hline(y=0,line=dict(color='#888',dash='dot'))
fig.update_layout(**T(height=540,legend=dict(orientation='h',y=-0.2)),xaxis=dict(dtick=1,title='Dia'),yaxis_title='Índice-iceberg (z)')
save(fig,'abnt_f_indice')
print('white figs OK')
