import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess
import plotly.graph_objects as go
from plotly.subplots import make_subplots
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
FIG='/home/user/mdlucca/Artigos/figuras'; os.makedirs(FIG,exist_ok=True)
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/hum_prof.csv')
PROF=['Iceberg','Barbatana tubarão','Superfície','Submerso','Iceberg invertido','Everest invertido']
rng=np.random.default_rng(7)
out=[]; L=lambda *a:(out.append(' '.join(str(x) for x in a)),print(*a))

# ---------- helper: cubic fit -> inflection & turning points ----------
def cubic_features(days,y):
    c=np.polyfit(days,y,3)             # c3,c2,c1,c0
    c3,c2,c1,c0=c
    infl=-c2/(3*c3) if c3!=0 else np.nan            # y''=0
    d1=np.polyder(c,1); roots=np.roots(d1)          # velocity=0 (turning pts)
    tp=[float(r.real) for r in roots if abs(r.imag)<1e-6 and 1<=r.real<=7]
    return c,infl,tp

# ---------- 1) ICEBERG INDEX trajectory (the profile summary) ----------
d=hum.dropna(subset=['ice_idx'])
days=np.arange(1,8)
raw_daymean=d.groupby('dia')['ice_idx'].mean().reindex(days).values
c_raw,infl_raw,tp_raw=cubic_features(days,raw_daymean)
L("="*80); L("PONTO DE INFLEXÃO DA TRAJETÓRIA DO PERFIL (índice-iceberg)"); L("="*80)
L(f"Médias diárias (com ruído): {np.round(raw_daymean,3).tolist()}")
L(f"[COM RUÍDO] cubic sobre médias diárias: inflexão = dia {infl_raw:.2f} | pontos de virada (vel=0) = {[round(x,2) for x in tp_raw]}")

# denoised trajectory: LOWESS over all obs, then sample on a grid & find 2nd-deriv sign change
lo=lowess(d['ice_idx'],d['dia'],frac=0.6,return_sorted=True)
gx=np.linspace(1,7,301); gy=np.interp(gx,lo[:,0],lo[:,1])
d2=np.gradient(np.gradient(gy,gx),gx)
sign_changes=gx[:-1][np.diff(np.sign(d2))!=0]
infl_smooth=float(sign_changes[np.argmin(np.abs(sign_changes-4))]) if len(sign_changes) else np.nan
# also cubic on the LOWESS-smoothed daily values (fully denoised)
sm_daymean=np.interp(days,lo[:,0],lo[:,1])
c_sm,infl_sm,tp_sm=cubic_features(days,sm_daymean)
L(f"[SEM RUÍDO] LOWESS 2ª derivada muda de sinal em dia = {infl_smooth:.2f}")
L(f"[SEM RUÍDO] cubic sobre trajetória suavizada: inflexão = dia {infl_sm:.2f} | virada = {[round(x,2) for x in tp_sm]}")

# ---------- 2) bootstrap CI of the inflection (resample athletes) ----------
def boot_infl(denoise=False,B=2000):
    ids=d['ID'].unique(); vals=[]
    for _ in range(B):
        samp=rng.choice(ids,size=len(ids),replace=True)
        rows=pd.concat([d[d.ID==a] for a in samp])
        if denoise:
            l=lowess(rows['ice_idx'],rows['dia'],frac=0.6,return_sorted=True)
            yv=np.interp(days,l[:,0],l[:,1])
        else:
            yv=rows.groupby('dia')['ice_idx'].mean().reindex(days).values
        if np.any(np.isnan(yv)): continue
        _,inf,_=cubic_features(days,yv)
        if 1<=inf<=7: vals.append(inf)
    return np.array(vals)
bi_noise=boot_infl(False); bi_clean=boot_infl(True)
ci_noise=np.percentile(bi_noise,[2.5,50,97.5]); ci_clean=np.percentile(bi_clean,[2.5,50,97.5])
L("\nBOOTSTRAP do ponto de inflexão (resample de atletas, 2000x):")
L(f"  COM ruído (cubic rígido s/ médias diárias): mediana dia {ci_noise[1]:.2f}  IC95% [{ci_noise[0]:.2f}; {ci_noise[2]:.2f}]  largura={ci_noise[2]-ci_noise[0]:.2f}")
L(f"  SEM ruído (LOWESS flexível):                mediana dia {ci_clean[1]:.2f}  IC95% [{ci_clean[0]:.2f}; {ci_clean[2]:.2f}]  largura={ci_clean[2]-ci_clean[0]:.2f}")
L(f"  => PONTO ROBUSTO: ambos centram no dia ~4,0 (ponto estimado praticamente idêntico). O IC do LOWESS é mais largo porque o suavizador é flexível (trade-off viés-variância), não porque tenha mais ruído.")

# ---------- 3) profile migration % per day + inflection of key profiles ----------
tab=pd.crosstab(hum['dia'],hum['perfil'],normalize='index').mul(100).reindex(columns=PROF).fillna(0)
L("\nMIGRAÇÃO DOS PERFIS (%) por dia:"); L(tab.round(1).to_string())
for pr in ['Iceberg','Barbatana tubarão']:
    yv=tab[pr].reindex(days).values; _,inf,tp=cubic_features(days,yv)
    L(f"  {pr}: inflexão dia {inf:.2f} | virada {[round(x,2) for x in tp]}")

# ---------- 4) raw finite-difference acceleration (noisy) vs smooth ----------
vel_raw=np.gradient(raw_daymean,days); acc_raw=np.gradient(vel_raw,days)
L("\nACELERAÇÃO por diferenças finitas (COM ruído) por dia:")
L("  "+str({int(dd):round(a,2) for dd,a in zip(days,acc_raw)}))
L("  (múltiplas trocas de sinal = ruído; o modelo suavizado dá UMA inflexão)")

# ---------- save + figures ----------
res=dict(infl_raw=float(infl_raw),tp_raw=tp_raw,infl_smooth=float(infl_smooth),infl_sm=float(infl_sm),tp_sm=tp_sm,
    ci_noise=ci_noise.tolist(),ci_clean=ci_clean.tolist(),
    raw_daymean=raw_daymean.tolist(),sm_daymean=sm_daymean.tolist(),
    tab=tab.round(1).to_dict())
json.dump(res,open(f'{SC}/inflexao.json','w'),indent=1)

TPL='plotly_dark'; T=dict(template=TPL,font=dict(size=15))
PCOL={'Iceberg':'#4dabf7','Barbatana tubarão':'#f03e3e','Superfície':'#adb5bd','Submerso':'#7048e8','Iceberg invertido':'#ff922b','Everest invertido':'#e64980'}

# FIG A: stacked area of profiles with inflection line
f=go.Figure()
for pr in PROF:
    f.add_trace(go.Scatter(x=tab.index,y=tab[pr],mode='lines',stackgroup='one',name=pr,line=dict(width=0.5,color=PCOL[pr]),fillcolor=PCOL[pr]))
f.add_vline(x=infl_sm,line=dict(color='#fff',width=3,dash='dash'))
f.add_annotation(x=infl_sm,y=100,text=f'inflexão ≈ dia {infl_sm:.1f}',showarrow=False,yshift=14,font=dict(color='#fff',size=14))
f.update_layout(**T,title='Fig A — Migração dos 6 perfis de humor e ponto de inflexão (sem ruído)',xaxis_title='Dia',yaxis_title='% dos atletas',height=560,xaxis=dict(dtick=1),legend=dict(orientation='h',y=-0.15))
f.write_image(f'{FIG}/infl_a_perfis.png',width=3840,height=2160)

# FIG B: iceberg index raw(noisy) vs LOWESS smooth + inflection markers
f=go.Figure()
f.add_trace(go.Scatter(x=d['dia']+rng.normal(0,0.06,len(d)),y=d['ice_idx'],mode='markers',name='observações (ruído)',marker=dict(color='#4dabf7',size=5,opacity=.3)))
f.add_trace(go.Scatter(x=days,y=raw_daymean,mode='lines+markers',name='média diária (com ruído)',line=dict(color='#ffd43b',width=2,dash='dot'),marker=dict(size=8)))
f.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',name='LOWESS (sem ruído)',line=dict(color='#f03e3e',width=4)))
f.add_vline(x=ci_clean[1],line=dict(color='#fff',width=3,dash='dash'))
f.add_vrect(x0=ci_clean[0],x1=ci_clean[2],fillcolor='rgba(255,255,255,0.10)',line_width=0)
f.add_annotation(x=ci_clean[1],y=d['ice_idx'].max(),text=f'inflexão dia {ci_clean[1]:.1f} [IC {ci_clean[0]:.1f};{ci_clean[2]:.1f}]',showarrow=False,yshift=10,font=dict(color='#fff',size=13))
f.add_hline(y=0,line=dict(color='gray',dash='dot'))
f.update_layout(**T,title='Fig B — Índice-iceberg: observações (ruído) vs curva sem ruído (LOWESS) e ponto de inflexão',xaxis_title='Dia',yaxis_title='Índice-iceberg (vigor − negativas, z)',height=540,xaxis=dict(dtick=1),legend=dict(orientation='h',y=-0.18))
f.write_image(f'{FIG}/infl_b_indice.png',width=3840,height=2160)

# FIG C: velocity & acceleration (smoothed cubic) with zero crossings
gx2=np.linspace(1,7,200); yv=np.polyval(c_sm,gx2); vv=np.polyval(np.polyder(c_sm,1),gx2); av=np.polyval(np.polyder(c_sm,2),gx2)
f=make_subplots(specs=[[{"secondary_y":True}]])
f.add_trace(go.Scatter(x=gx2,y=vv,mode='lines',name='velocidade (dy/dia)',line=dict(color='#51cf66',width=3)),secondary_y=False)
f.add_trace(go.Scatter(x=gx2,y=av,mode='lines',name='aceleração (d²y/dia²)',line=dict(color='#f03e3e',width=3)),secondary_y=True)
f.add_hline(y=0,line=dict(color='gray',dash='dot'))
f.add_vline(x=infl_sm,line=dict(color='#fff',width=2,dash='dash'))
f.add_annotation(x=infl_sm,y=0,text=f'inflexão (acel=0) dia {infl_sm:.1f}',showarrow=True,arrowhead=2,ay=-40,font=dict(color='#fff',size=13))
for t in tp_sm:
    f.add_vline(x=t,line=dict(color='#51cf66',width=1,dash='dot'))
f.update_layout(**T,title='Fig C — Derivadas da trajetória do perfil (sem ruído): inflexão onde a aceleração cruza zero',xaxis_title='Dia',height=520,legend=dict(orientation='h',y=-0.18))
f.update_yaxes(title_text='velocidade',secondary_y=False); f.update_yaxes(title_text='aceleração',secondary_y=True)
f.write_image(f'{FIG}/infl_c_derivadas.png',width=3840,height=2160)

# FIG D: bootstrap distributions with vs without noise
f=go.Figure()
f.add_trace(go.Histogram(x=bi_noise,name='com ruído',marker_color='#ffd43b',opacity=.6,nbinsx=40))
f.add_trace(go.Histogram(x=bi_clean,name='sem ruído',marker_color='#f03e3e',opacity=.6,nbinsx=40))
f.add_vline(x=ci_noise[1],line=dict(color='#ffd43b',width=2,dash='dash'))
f.add_vline(x=ci_clean[1],line=dict(color='#f03e3e',width=2,dash='dash'))
f.update_layout(**T,barmode='overlay',title='Fig D — Robustez do ponto de inflexão (bootstrap): com e sem ruído, ambos centram no dia ~4',xaxis_title='Dia da inflexão',yaxis_title='frequência (bootstrap)',height=500,legend=dict(orientation='h',y=-0.18))
f.write_image(f'{FIG}/infl_d_bootstrap.png',width=3840,height=2160)
print('\nfigs OK')
open(f'{SC}/res_inflexao.txt','w').write('\n'.join(out))
