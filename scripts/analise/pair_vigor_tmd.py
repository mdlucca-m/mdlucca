import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, os, json
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.nonparametric.smoothers_lowess import lowess
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
FIG='/home/user/mdlucca/Artigos/figuras'; os.makedirs(FIG,exist_ok=True)
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/humor.csv')
VARS=[('Vigor','Vigor (0–20)','#51cf66'),('TMD','PTH/TMD','#845ef7')]
keys=[v for v,_,_ in VARS]; labs={v:l for v,l,_ in VARS}; cols={v:c for v,_,c in VARS}
TPL='plotly_dark'; T=dict(template=TPL,font=dict(size=15))

# ================= COMPUTE =================
grp={}; per={}; btw={}; PP={}
for v,lab,c in VARS:
    d=hum.dropna(subset=[v]).copy()
    daym=d.groupby('dia')[v].agg(['mean','std'])
    m=smf.ols(f'{v} ~ C(ID)+C(dia)',data=d).fit(); a=anova_lm(m,typ=1)
    ss=a['sum_sq']; tot=ss['C(ID)']+ss['C(dia)']+ss['Residual']
    etm=np.sqrt(a.loc['Residual','mean_sq']); mdc=1.96*np.sqrt(2)*etm
    sd_b=d.groupby('ID')[v].mean().std(); swc=0.2*sd_b
    sig=daym['mean'].max()-daym['mean'].min()
    nday=d.groupby('dia').size().mean(); mdc_g=mdc/np.sqrt(nday)
    rel=1-ss['Residual']/tot
    grp[v]=dict(d1=float(daym['mean'].loc[1]),d7=float(daym['mean'].loc[7]),drift=float(daym['mean'].loc[7]-daym['mean'].loc[1]),
        pday=100*ss['C(dia)']/tot,ptrait=100*ss['C(ID)']/tot,pnoise=100*ss['Residual']/tot,
        etm=etm,mdc=mdc,mdc_g=mdc_g,swc=swc,sig=sig,snr=sig/etm,rel=rel,
        detect_ind=bool(sig>mdc),detect_grp=bool(sig>mdc_g),daymean=daym['mean'].round(2).to_dict())
    # between days
    sdb=d.groupby('dia')[v].std(); dd=d.groupby('dia')[v].mean().diff().abs()
    btw[v]=dict(sd_between=sdb.round(2).to_dict(),dd=dd.round(2).to_dict(),
        day_maxsd=int(sdb.idxmax()),day_maxdd=int(dd.iloc[1:].idxmax()))
    # per athlete
    rows=[]
    for aid,g in d.groupby('ID'):
        amp=g[v].max()-g[v].min(); dm=g.groupby('dia')[v].mean()
        psig=dm.max()-dm.min() if len(dm)>1 else 0
        res=g[v]-g['dia'].map(dm); pnoise=res.std(ddof=0) if len(res)>1 else 0
        rows.append(dict(ID=aid,amp=amp,psig=psig,pnoise=pnoise,snr=(psig/pnoise if pnoise>0 else np.nan)))
    df=pd.DataFrame(rows)
    per[v]=dict(df=df,amp_mean=df.amp.mean(),amp_sd=df.amp.std(),amp_min=df.amp.min(),amp_max=df.amp.max(),
        psig_mean=df.psig.mean(),pnoise_mean=df.pnoise.mean(),pct_snr_gt1=100*(df.snr>1).mean())
    # prepost
    ppd={}
    for day in range(1,8):
        g=d[d.dia==day]
        pre=g[g.momento=='pre'].groupby('ID')[v].mean(); mid=g[g.momento=='mid'].groupby('ID')[v].mean(); pos=g[g.momento=='pos'].groupby('ID')[v].mean()
        common=pre.index.intersection(pos.index); aa,bb=pre.loc[common],pos.loc[common]; diff=bb-aa
        dz=diff.mean()/diff.std() if len(common)>=3 and diff.std()>0 else np.nan
        try: pw=stats.wilcoxon(aa.values,bb.values).pvalue if len(common)>=3 else np.nan
        except Exception: pw=np.nan
        pfried=np.nan; nmid=int(mid.count())
        if nmid>=3:
            allc=pre.index.intersection(mid.index).intersection(pos.index)
            if len(allc)>=3:
                try: pfried=stats.friedmanchisquare(pre.loc[allc],mid.loc[allc],pos.loc[allc]).pvalue
                except Exception: pass
        ppd[day]=dict(pre_m=pre.mean(),pre_sd=pre.std(),mid_m=(mid.mean() if nmid else None),mid_sd=(mid.std() if nmid>1 else None),
            pos_m=pos.mean(),pos_sd=pos.std(),delta=pos.mean()-pre.mean(),
            dz=(dz if not np.isnan(dz) else None),p=(pw if not np.isnan(pw) else None),
            pfried=(pfried if not np.isnan(pfried) else None),hiit=int(g['HIIT'].iloc[0]) if len(g) else 0)
    PP[v]=ppd

# correlation física × mental: observed / disattenuated / group-level
raw=hum[keys].dropna()
r_obs=raw['Vigor'].corr(raw['TMD'])
r_dis=r_obs/np.sqrt(grp['Vigor']['rel']*grp['TMD']['rel'])
gm=hum.groupby('dia')[keys].mean(); r_den=gm['Vigor'].corr(gm['TMD'])
rho_obs=stats.spearmanr(raw['Vigor'],raw['TMD']).correlation
# rmcorr intra-athlete
def rmcorr(df,x,y):
    dd=df[['ID',x,y]].dropna().rename(columns={x:'X',y:'Y'})
    mm=smf.ols('Y~C(ID)+X',data=dd).fit(); aa=anova_lm(mm,typ=1)
    return np.sign(mm.params['X'])*np.sqrt(aa.loc['X','sum_sq']/(aa.loc['X','sum_sq']+aa.loc['Residual','sum_sq']))
rm=rmcorr(hum,'Vigor','TMD')

# effect sizes D1->D7 + corrected
eff={}
for v,_,_ in VARS:
    d1=hum[hum.dia==1].groupby('ID')[v].mean(); d7=hum[hum.dia==7].groupby('ID')[v].mean()
    common=d1.index.intersection(d7.index); diff=d7.loc[common]-d1.loc[common]
    dz=diff.mean()/diff.std(); eff[v]=dict(dz=dz,dz_corr=dz/np.sqrt(grp[v]['rel']))

# MDC vs k
kmdc={v:{k:1.96*np.sqrt(2)*grp[v]['etm']/np.sqrt(k) for k in [1,2,3,5,7]} for v,_,_ in VARS}

print('corr Vigor×TMD: obs r=%.2f rho=%.2f | disatt=%.2f | group=%.2f | rmcorr=%.2f'%(r_obs,rho_obs,r_dis,r_den,rm))
for v,_,_ in VARS: print(f"  {labs[v]}: sig={grp[v]['sig']:.2f} etm={grp[v]['etm']:.2f} snr={grp[v]['snr']:.2f} pday={grp[v]['pday']:.1f}% rel={grp[v]['rel']:.2f} dz={eff[v]['dz']:+.2f}")

# ================= FIGURES =================
# PF1 group trajectory
fig=make_subplots(rows=1,cols=2,subplot_titles=[l for _,l,_ in VARS],horizontal_spacing=0.1)
for j,(v,lab,c) in enumerate(VARS,1):
    d=hum.dropna(subset=[v]); dm=d.groupby('dia')[v].mean(); sd=d.groupby('dia')[v].std()
    lo=lowess(d[v],d['dia'],frac=0.6,return_sorted=True); days=dm.index.values
    fig.add_trace(go.Scatter(x=list(days)+list(days[::-1]),y=list(dm.values+sd.values)+list((dm.values-sd.values)[::-1]),fill='toself',fillcolor='rgba(150,150,150,0.12)',line=dict(width=0),showlegend=False,hoverinfo='skip'),1,j)
    fig.add_trace(go.Scatter(x=days,y=dm.values,mode='lines+markers',line=dict(color=c,width=3),marker=dict(size=9),showlegend=False),1,j)
    fig.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',line=dict(color='#fff',width=2,dash='dot'),showlegend=False),1,j)
    for dd_ in (2,4,7): fig.add_vline(x=dd_,line=dict(color='#f03e3e',width=1,dash='dot'),row=1,col=j)
fig.update_layout(**T,height=520,title='Fig 1 — Fadiga física vs mental ao longo da semana (média ± DP; LOWESS; HIIT = 2,4,7)')
fig.update_xaxes(dtick=1,title='Dia'); fig.write_image(f'{FIG}/pv1_trajetoria.png',width=3840,height=2160)

# PV2 both trajectories overlaid, z-standardized (different scales) — inverse coupling
fig=go.Figure()
for v,lab,c in VARS:
    d=hum.dropna(subset=[v]); z=(d[v]-hum[v].mean())/hum[v].std()
    dz=pd.Series(z.values,index=d['dia'].values).groupby(level=0).mean()
    lo=lowess(z,d['dia'],frac=0.6,return_sorted=True)
    fig.add_trace(go.Scatter(x=dz.index,y=dz.values,mode='markers',marker=dict(color=c,size=8,opacity=.5),showlegend=False))
    fig.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',name=lab,line=dict(color=c,width=4)))
fig.add_hline(y=0,line=dict(color='gray',dash='dot'))
fig.update_layout(**T,height=520,title='Fig 2 — Acoplamento inverso (z): o Vigor desce enquanto o PTH/TMD sobe — espelhos do mesmo eixo',xaxis=dict(dtick=1,title='Dia'),yaxis=dict(title='Escore padronizado (z)'),legend=dict(orientation='h',y=-0.18))
fig.write_image(f'{FIG}/pv2_dissociacao.png',width=3840,height=2160)

# PF3 per-athlete amplitude box vs group signal
fig=go.Figure()
for i,(v,lab,c) in enumerate(VARS):
    df=per[v]['df']
    fig.add_trace(go.Box(y=df.amp,name=lab,marker_color=c,boxpoints='all',pointpos=0,jitter=0.4,marker=dict(size=5,opacity=.5)))
    fig.add_trace(go.Scatter(x=[lab],y=[grp[v]['sig']],mode='markers',marker=dict(symbol='diamond',size=15,color='#fff',line=dict(color=c,width=2)),name='amplitude do sinal (grupo)' if i==0 else None,showlegend=(i==0)))
fig.update_layout(**T,height=560,title='Fig 3 — Amplitude por atleta (caixa) vs amplitude do sinal do grupo (losango)',yaxis_title='Amplitude (max−min na semana)',legend=dict(orientation='h',y=-0.15))
fig.write_image(f'{FIG}/pv3_amp_box.png',width=3840,height=2160)

# PF4 prepost per day (2 panels, 3 bars)
fig=make_subplots(rows=1,cols=2,subplot_titles=[l for _,l,_ in VARS],horizontal_spacing=0.1)
for j,(v,lab,c) in enumerate(VARS,1):
    days=list(range(1,8))
    pre=[PP[v][d]['pre_m'] for d in days]; mid=[PP[v][d]['mid_m'] for d in days]; pos=[PP[v][d]['pos_m'] for d in days]
    fig.add_trace(go.Bar(x=days,y=pre,name='pré',marker_color='#4dabf7',showlegend=(j==1)),1,j)
    fig.add_trace(go.Bar(x=days,y=mid,name='mid',marker_color='#adb5bd',showlegend=(j==1)),1,j)
    fig.add_trace(go.Bar(x=days,y=pos,name='pós',marker_color=c,showlegend=(j==1)),1,j)
    for d in days:
        rr=PP[v][d]
        if rr['p'] is not None and rr['p']<0.05:
            fig.add_annotation(x=d,y=max([x for x in [rr['pre_m'],rr['mid_m'],rr['pos_m']] if x is not None])+0.5,text='*',showarrow=False,font=dict(size=20,color='#fff'),row=1,col=j)
fig.update_layout(**T,height=520,barmode='group',bargap=0.25,bargroupgap=0.06,title='Fig 4 — Pré → mid → pós por dia. * = Wilcoxon pareado pré×pós p<0,05')
fig.update_xaxes(dtick=1,title='Dia'); fig.write_image(f'{FIG}/pv4_prepos.png',width=3840,height=2160)

# PF5 scatter física×mental with regression (obs) + group-level
fig=make_subplots(rows=1,cols=2,subplot_titles=[f'Observações brutas (r={r_obs:.2f}, ρ={rho_obs:.2f})',f'Médias diárias do grupo (r={r_den:.2f})'],horizontal_spacing=0.12)
rng=np.random.default_rng(4)
xj=raw['Vigor']+rng.normal(0,0.08,len(raw)); yj=raw['TMD']+rng.normal(0,0.08,len(raw))
fig.add_trace(go.Scatter(x=xj,y=yj,mode='markers',marker=dict(color='#868e96',size=5,opacity=.35),showlegend=False),1,1)
b=np.polyfit(raw['Vigor'],raw['TMD'],1); xs=np.array([0,10]); fig.add_trace(go.Scatter(x=xs,y=np.polyval(b,xs),mode='lines',line=dict(color='#f03e3e',width=3),showlegend=False),1,1)
fig.add_trace(go.Scatter(x=gm['Vigor'],y=gm['TMD'],mode='markers+text',text=[f'D{d}' for d in gm.index],textposition='top center',marker=dict(color='#ffd43b',size=12),showlegend=False),1,2)
b2=np.polyfit(gm['Vigor'],gm['TMD'],1); xs2=np.linspace(gm['Vigor'].min(),gm['Vigor'].max(),2); fig.add_trace(go.Scatter(x=xs2,y=np.polyval(b2,xs2),mode='lines',line=dict(color='#ffd43b',width=3),showlegend=False),1,2)
fig.update_layout(**T,height=520,title='Fig 5 — Relação fadiga física × mental: bruta (com ruído) vs nível-grupo (denoised)')
fig.update_xaxes(title='Vigor (0–20)'); fig.update_yaxes(title='PTH/TMD')
fig.write_image(f'{FIG}/pv5_scatter.png',width=3840,height=2160)

# PF6 MDC vs k
fig=make_subplots(rows=1,cols=2,subplot_titles=[l for _,l,_ in VARS],horizontal_spacing=0.1)
for j,(v,lab,c) in enumerate(VARS,1):
    ks=[1,2,3,5,7]; mdc=[kmdc[v][k] for k in ks]
    fig.add_trace(go.Scatter(x=ks,y=mdc,mode='lines+markers',line=dict(color=c,width=3),marker=dict(size=9),showlegend=False),1,j)
    fig.add_hline(y=grp[v]['sig'],line=dict(color='#fff',dash='dash',width=2),row=1,col=j)
    fig.add_annotation(x=5,y=grp[v]['sig'],text=f"sinal={grp[v]['sig']:.1f}",showarrow=False,yshift=12,font=dict(color='#fff',size=12),row=1,col=j)
fig.update_layout(**T,height=480,title='Fig 6 — MDC95 individual vs nº de coletas (k); linha branca = amplitude do sinal semanal')
fig.update_xaxes(title='k coletas',dtick=1); fig.write_image(f'{FIG}/pv6_mdc.png',width=3840,height=2160)
print('figs OK')

# stash for docx
G=dict(grp={v:{k:(float(x) if isinstance(x,(int,float,np.floating)) else (x if not isinstance(x,dict) else {str(kk):float(vv) for kk,vv in x.items()})) for k,x in grp[v].items() if k!='daymean'} for v,_,_ in VARS},
    btw={v:{'sd_between':btw[v]['sd_between'],'dd':btw[v]['dd'],'day_maxsd':btw[v]['day_maxsd'],'day_maxdd':btw[v]['day_maxdd']} for v,_,_ in VARS},
    per={v:{k:float(x) for k,x in per[v].items() if k!='df'} for v,_,_ in VARS},
    pp={v:{str(d):{k:(float(x) if isinstance(x,(int,float,np.floating)) else x) for k,x in PP[v][d].items()} for d in range(1,8)} for v,_,_ in VARS},
    corr=dict(r_obs=float(r_obs),rho_obs=float(rho_obs),r_dis=float(r_dis),r_den=float(r_den),rm=float(rm)),
    eff={v:{k:float(x) for k,x in eff[v].items()} for v,_,_ in VARS},
    kmdc={v:{str(k):float(x) for k,x in kmdc[v].items()} for v,_,_ in VARS})
json.dump(G,open(f'{SC}/pair_vigor_tmd.json','w'),indent=1)
print('saved pair_vigor_tmd.json')
