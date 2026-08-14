import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy import stats
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
FIG='/home/user/mdlucca/Artigos/figuras'; os.makedirs(FIG,exist_ok=True)
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/humor.csv')
VARS=[('Vigor','Vigor (0–20)','#51cf66'),('Fadiga','Fadiga BRUMS (0–20)','#f03e3e'),
      ('TMD','PTH/TMD','#845ef7'),('FadMental','Fadiga mental (0–10)','#ffd43b')]
R={}

# ---------- GROUP: weekly trajectory + amplitude + noise ----------
grp={}
for v,lab,c in VARS:
    d=hum.dropna(subset=[v]).copy()
    daym=d.groupby('dia')[v].agg(['mean','std','count'])
    m=smf.ols(f'{v} ~ C(ID)+C(dia)',data=d).fit(); a=anova_lm(m,typ=1)
    ss_id,ss_day,ss_res=a.loc['C(ID)','sum_sq'],a.loc['C(dia)','sum_sq'],a.loc['Residual','sum_sq']
    tot=ss_id+ss_day+ss_res
    etm=np.sqrt(a.loc['Residual','mean_sq']); mdc=1.96*np.sqrt(2)*etm
    sd_b=d.groupby('ID')[v].mean().std(); swc=0.2*sd_b
    sig=daym['mean'].max()-daym['mean'].min()
    nday=d.groupby('dia').size().mean(); mdc_g=mdc/np.sqrt(nday)
    grp[v]=dict(lab=lab,daymean=daym['mean'].round(2).to_dict(),daystd=daym['std'].round(2).to_dict(),
        d1=float(daym['mean'].loc[1]),d7=float(daym['mean'].loc[7]),drift=float(daym['mean'].loc[7]-daym['mean'].loc[1]),
        pday=100*ss_day/tot,ptrait=100*ss_id/tot,pnoise=100*ss_res/tot,etm=etm,mdc=mdc,mdc_g=mdc_g,swc=swc,
        sig=sig,snr=sig/etm,detect_ind=bool(sig>mdc),detect_grp=bool(sig>mdc_g))
R['grp']=grp

# ---------- BETWEEN DAYS: dispersion + day-to-day change ----------
btw={}
for v,lab,c in VARS:
    d=hum.dropna(subset=[v])
    sd_between=d.groupby('dia')[v].std()          # dispersão entre atletas por dia
    daym=d.groupby('dia')[v].mean()
    dd=daym.diff().abs()                            # |mudança dia-a-dia| do grupo
    # per-day intra-day pre->post abs change (mean over athletes)
    intra=[]
    for day in range(1,8):
        g=d[d.dia==day]; ch=[]
        for aid,ga in g.groupby('ID'):
            pre=ga[ga.momento=='pre'][v]; pos=ga[ga.momento=='pos'][v]
            if len(pre) and len(pos): ch.append(abs(pos.iloc[0]-pre.iloc[0]))
        intra.append(np.mean(ch) if ch else np.nan)
    btw[v]=dict(sd_between=sd_between.round(2).to_dict(),dd=dd.round(2).to_dict(),
        intra={i+1:round(x,2) for i,x in enumerate(intra)},
        day_maxsd=int(sd_between.idxmax()),day_maxdd=int(dd.idxmax()))
R['btw']=btw

# ---------- PER ATHLETE: amplitude, personal signal vs noise ----------
per={}
for v,lab,c in VARS:
    d=hum.dropna(subset=[v])
    rows=[]
    for aid,g in d.groupby('ID'):
        amp=g[v].max()-g[v].min()
        dm=g.groupby('dia')[v].mean()
        psig=dm.max()-dm.min() if len(dm)>1 else 0     # amplitude do sinal pessoal (entre dias)
        # personal noise: residual around own daily mean
        res=g[v]-g['dia'].map(dm)
        pnoise=res.std(ddof=0) if len(res)>1 else 0
        drift=(dm.get(7,np.nan)-dm.get(1,np.nan)) if (1 in dm.index and 7 in dm.index) else np.nan
        rows.append(dict(ID=aid,amp=amp,psig=psig,pnoise=pnoise,snr=(psig/pnoise if pnoise>0 else np.nan),drift=drift,mean=g[v].mean()))
    df=pd.DataFrame(rows)
    per[v]=dict(df=df,
        amp_mean=float(df.amp.mean()),amp_sd=float(df.amp.std()),amp_min=float(df.amp.min()),amp_max=float(df.amp.max()),
        psig_mean=float(df.psig.mean()),pnoise_mean=float(df.pnoise.mean()),
        snr_mean=float(df.snr.mean(skipna=True)),
        pct_snr_gt1=float(100*(df.snr>1).mean()),
        drift_mean=float(df.drift.mean(skipna=True)),drift_sd=float(df.drift.std(skipna=True)),
        pct_worse=float(100*(df.drift>0).mean()) if v!='Vigor' else float(100*(df.drift<0).mean()))
R['per']=per

# save JSON-safe
def safe(o):
    if isinstance(o,dict): return {k:safe(v) for k,v in o.items() if k!='df'}
    if isinstance(o,(np.floating,)): return float(o)
    if isinstance(o,(np.integer,)): return int(o)
    if isinstance(o,bool): return o
    return o
json.dump(safe(R),open(f'{SC}/amp_docx.json','w'),indent=1,default=str)
# also dump per-athlete tables
for v,lab,c in VARS:
    per[v]['df'].round(2).to_csv(f'{SC}/peratlheta_{v}.csv',index=False)

TPL='plotly_dark'; T=dict(template=TPL,font=dict(size=15))

# FIG 1 — group trajectories (4 vars, twin scaling: standardize to z for comparability) + raw daily means panel
fig=make_subplots(rows=2,cols=2,subplot_titles=[l for _,l,_ in VARS],vertical_spacing=0.13,horizontal_spacing=0.09)
pos=[(1,1),(1,2),(2,1),(2,2)]
for (v,lab,c),(r,cc) in zip(VARS,pos):
    d=hum.dropna(subset=[v]); dm=d.groupby('dia')[v].mean(); sd=d.groupby('dia')[v].std()
    lo=lowess(d[v],d['dia'],frac=0.6,return_sorted=True)
    days=dm.index.values
    fig.add_trace(go.Scatter(x=list(days)+list(days[::-1]),y=list(dm.values+sd.values)+list((dm.values-sd.values)[::-1]),
        fill='toself',fillcolor='rgba(150,150,150,0.12)',line=dict(width=0),showlegend=False,hoverinfo='skip'),r,cc)
    fig.add_trace(go.Scatter(x=days,y=dm.values,mode='lines+markers',line=dict(color=c,width=3),marker=dict(size=8),showlegend=False),r,cc)
    fig.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',line=dict(color='#fff',width=2,dash='dot'),showlegend=False),r,cc)
    for dd_ in (2,4,7): fig.add_vline(x=dd_,line=dict(color='#f03e3e',width=1,dash='dot'),row=r,col=cc)
fig.update_layout(**T,height=820,title='Fig 1 — Trajetória do grupo ao longo da semana (média ± DP; LOWESS pontilhado; linhas vermelhas = HIIT)')
fig.update_xaxes(dtick=1,title='Dia'); fig.write_image(f'{FIG}/adx1_grupo_semana.png',width=3840,height=2160)

# FIG 2 — between-days dispersion (SD between athletes) per var
fig=go.Figure()
for v,lab,c in VARS:
    sdb=hum.dropna(subset=[v]).groupby('dia')[v].std()
    fig.add_trace(go.Scatter(x=sdb.index,y=sdb.values,mode='lines+markers',name=lab,line=dict(color=c,width=3),marker=dict(size=8)))
fig.update_layout(**T,height=560,title='Fig 2 — Dispersão ENTRE atletas por dia (DP) — heterogeneidade ao longo da semana',
    xaxis=dict(dtick=1,title='Dia'),yaxis_title='DP entre atletas',legend=dict(orientation='h',y=-0.2))
fig.write_image(f'{FIG}/adx2_dispersao_dia.png',width=3840,height=2160)

# FIG 3 — per-athlete amplitude heatmap (athletes sorted; 4 vars z-scaled columns)
mat=[]; ids=sorted(hum['ID'].unique())
for aid in ids:
    row=[]
    for v,lab,c in VARS:
        g=hum[(hum.ID==aid)].dropna(subset=[v]); row.append(g[v].max()-g[v].min() if len(g) else np.nan)
    mat.append(row)
M=pd.DataFrame(mat,index=ids,columns=[l for _,l,_ in VARS])
Mz=(M-M.mean())/M.std()
order=Mz.mean(axis=1).sort_values().index
fig=go.Figure(go.Heatmap(z=Mz.loc[order].values,x=list(M.columns),y=list(order),colorscale='RdBu_r',zmid=0,
    colorbar=dict(title='amplitude (z)'),hovertemplate='%{y} · %{x}<br>amplitude z=%{z:.2f}<extra></extra>'))
fig.update_layout(**T,height=820,title='Fig 3 — Amplitude semanal por atleta (z por variável; atletas ordenados do menor ao maior oscilador)')
fig.write_image(f'{FIG}/adx3_heatmap_atleta.png',width=3840,height=2160)

# FIG 4 — per-athlete amplitude distribution (box + points) with group signal amplitude marked
fig=go.Figure()
for i,(v,lab,c) in enumerate(VARS):
    df=per[v]['df']
    fig.add_trace(go.Box(y=df.amp,name=lab,marker_color=c,boxpoints='all',pointpos=0,jitter=0.4,marker=dict(size=4,opacity=.5)))
    fig.add_trace(go.Scatter(x=[lab],y=[grp[v]['sig']],mode='markers',marker=dict(symbol='diamond',size=14,color='#fff',line=dict(color=c,width=2)),
        name='amplitude do sinal (grupo)' if i==0 else None,showlegend=(i==0)))
fig.update_layout(**T,height=600,title='Fig 4 — Amplitude POR ATLETA (caixa) vs amplitude do SINAL do grupo (losango): o atleta oscila mais que o microciclo',
    yaxis_title='Amplitude (max−min na semana)',legend=dict(orientation='h',y=-0.15))
fig.write_image(f'{FIG}/adx4_amp_atleta_box.png',width=3840,height=2160)

# FIG 5 — small multiples: 6 example athletes trajectories for the 4 vars (z) — signal vs noise per athlete
ex=list(order[:3])+list(order[-3:])  # 3 calmest + 3 most volatile
fig=make_subplots(rows=2,cols=3,subplot_titles=[f'Atleta {a}' for a in ex],vertical_spacing=0.14,horizontal_spacing=0.06)
for idx,aid in enumerate(ex):
    r,cc=idx//3+1,idx%3+1
    g=hum[hum.ID==aid]
    for v,lab,c in VARS:
        gg=g.dropna(subset=[v])
        if len(gg)<2: continue
        z=(gg[v]-hum[v].mean())/hum[v].std()
        dm=pd.Series(z.values,index=gg['dia'].values).groupby(level=0).mean()
        fig.add_trace(go.Scatter(x=dm.index,y=dm.values,mode='lines+markers',line=dict(color=c,width=2),marker=dict(size=5),
            showlegend=(idx==0),name=lab),r,cc)
fig.update_layout(**T,height=760,title='Fig 5 — Trajetórias individuais (z) de 3 atletas mais estáveis (topo) e 3 mais oscilantes (base)',
    legend=dict(orientation='h',y=-0.12))
fig.update_xaxes(dtick=1); fig.write_image(f'{FIG}/adx5_atletas_exemplo.png',width=3840,height=2160)

print('figs OK'); print('drift/pct per var:')
for v,lab,c in VARS: print(f"  {lab}: sig={grp[v]['sig']:.2f} etm={grp[v]['etm']:.2f} snr={grp[v]['snr']:.2f} amp_atleta={per[v]['amp_mean']:.2f}±{per[v]['amp_sd']:.2f} %snr>1={per[v]['pct_snr_gt1']:.0f}")
