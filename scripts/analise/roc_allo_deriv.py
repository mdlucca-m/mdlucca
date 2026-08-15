import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.nonparametric.smoothers_lowess import lowess
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
OUT='/home/user/mdlucca/Artigos/figuras'
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/hum_prof.csv'); h2=hum[hum.momento.isin(['pre','pos'])].copy()
ath=pd.DataFrame(json.load(open(f'{SC}/app_data.json'))['socio']['athletes'])
CORE=[('Vigor','Vigor'),('Fadiga','Fadiga BRUMS'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental'),('TMD','PTH/TMD')]
CV={'Vigor':'#2b8a3e','Fadiga':'#c92a2a','FadFisica':'#d9480f','FadMental':'#6741d9','TMD':'#0b7285'}
days=np.arange(1,8)
def daily(v): return h2.dropna(subset=[v]).groupby(['ID','dia'])[v].mean().reset_index()
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=16,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=65,r=25,t=55,b=60)); b.update(k); return b
def save(f,n): f.write_image(f'{OUT}/{n}.png',width=1600,height=900,scale=2)

# ============ 1) EXPANDED LIMITS & DERIVATIVES ============
D={}
for v,lab in CORE:
    dm=np.array(daily(v).groupby('dia')[v].mean().reindex(days).values)
    c=np.polyfit(days,dm,3); vel=np.polyval(np.polyder(c,1),days); acc=np.polyval(np.polyder(c,2),days); jerk=float(np.polyder(c,3)[0])
    auc_traj=float(np.trapezoid(dm,days))                      # área sob a trajetória (dose acumulada)
    pkvel_day=int(days[np.argmax(np.abs(vel))])
    tot=h2[v].max()-h2[v].min(); intra=daily(v).groupby('ID')[v].apply(lambda s:s.max()-s.min()).mean(); sig=dm.max()-dm.min()
    scale={'Vigor':20,'Fadiga':20,'FadFisica':10,'FadMental':10,'TMD':64}[v]
    D[v]=dict(lab=lab,vel={int(d):float(x) for d,x in zip(days,vel)},acc={int(d):float(x) for d,x in zip(days,acc)},
        jerk=jerk,auc=auc_traj,pkvel_day=pkvel_day,amp_tot=float(tot),amp_intra=float(intra),amp_sig=float(sig),pct_scale=float(100*sig/scale))
json.dump(D,open(f'{SC}/deriv_exp.json','w'),indent=1)

# ============ 2) ROC: D7 vs D1, com ruído (obs) vs sem ruído (média diária) ============
def auc_ci(pos,neg,B=2000,rng=None):
    pos=np.asarray(pos); neg=np.asarray(neg)
    def a(p,n):
        U=stats.mannwhitneyu(p,n,alternative='greater').statistic; return U/(len(p)*len(n))
    obs=a(pos,neg); bs=[]
    for _ in range(B):
        bs.append(a(rng.choice(pos,len(pos)),rng.choice(neg,len(neg))))
    lo,hi=np.percentile(bs,[2.5,97.5]); return obs,lo,hi
def roc_points(pos,neg):
    th=np.unique(np.concatenate([pos,neg])); th=np.sort(th)[::-1]
    tpr=[0];fpr=[0]
    for t in th:
        tpr.append(np.mean(pos>=t)); fpr.append(np.mean(neg>=t))
    tpr.append(1);fpr.append(1); return np.array(fpr),np.array(tpr)
rng=np.random.default_rng(11); ROC={}
for v,lab in CORE:
    sgn=-1 if v=='Vigor' else 1   # vigor: menor no D7 -> inverte sinal para "deterioração"
    # com ruído: observações individuais
    p_raw=sgn*h2[(h2.dia==7)].dropna(subset=[v])[v].values; n_raw=sgn*h2[(h2.dia==1)].dropna(subset=[v])[v].values
    # sem ruído: média diária por atleta
    w=daily(v).pivot(index='ID',columns='dia',values=v); p_f=sgn*w[7].dropna().values; n_f=sgn*w[1].dropna().values
    a_raw=auc_ci(p_raw,n_raw,rng=rng); a_f=auc_ci(p_f,n_f,rng=rng)
    ROC[v]=dict(lab=lab,raw=a_raw,filt=a_f,
        roc_raw=[x.tolist() for x in roc_points(p_raw,n_raw)],roc_filt=[x.tolist() for x in roc_points(p_f,n_f)])
json.dump({k:{kk:(vv if kk in('lab',) else vv) for kk,vv in val.items()} for k,val in ROC.items()},open(f'{SC}/roc.json','w'),indent=1)
print('ROC AUC (D7 vs D1):')
for v,lab in CORE: print('  %-15s com ruído=%.2f [%.2f;%.2f] | sem ruído=%.2f [%.2f;%.2f]'%(lab,*ROC[v]['raw'],*ROC[v]['filt']))

# ============ 3) AJUSTE ALOMÉTRICO ============
ALLO={}
# 3a) trajetória alométrica: Y = a * dia^b (log-log) para as variáveis de fadiga
print('\nAJUSTE ALOMÉTRICO da trajetória (Y = a*dia^b):')
for v,lab in [('FadFisica','Fadiga física'),('Fadiga','Fadiga BRUMS'),('TMD','PTH/TMD')]:
    dm=daily(v).groupby('dia')[v].mean().reindex(days).values; y=np.clip(dm,1e-3,None)
    lr=stats.linregress(np.log(days),np.log(y)); a=np.exp(lr.intercept); b=lr.slope
    # AIC linear vs power
    yl=np.polyval(np.polyfit(days,dm,1),days); rss_lin=np.sum((dm-yl)**2)
    yp=a*days**b; rss_pow=np.sum((dm-yp)**2); nk=7
    aic=lambda rss: nk*np.log(rss/nk)+2*2
    ALLO[v]=dict(lab=lab,a=float(a),b=float(b),r2=float(lr.rvalue**2),p=float(lr.pvalue),aic_lin=float(aic(rss_lin)),aic_pow=float(aic(rss_pow)))
    print('  %-15s a=%.2f b=%.2f R²=%.2f (b>1 acelera, b<1 satura)  AIC pow=%.1f lin=%.1f'%(lab,a,b,lr.rvalue**2,aic(rss_pow),aic(rss_lin)))
# 3b) escalonamento alométrico da aptidão (PV = a*massa^b) e proteção contra fadiga
m=ath.dropna(subset=['massa','PV']); lr=stats.linregress(np.log(m['massa']),np.log(m['PV'])); bexp=lr.slope
ath['PV_allo']=ath['PV']/ath['massa']**bexp
wk=daily('FadFisica').groupby('ID')['FadFisica'].mean().rename('fadwk')
mm=ath.set_index('id').join(wk)
rho_raw=stats.spearmanr(mm['PV'],mm['fadwk'],nan_policy='omit'); rho_allo=stats.spearmanr(mm['PV_allo'],mm['fadwk'],nan_policy='omit')
ALLO['fitness']=dict(b=float(bexp),r2=float(lr.rvalue**2),rho_raw=float(rho_raw.correlation),p_raw=float(rho_raw.pvalue),rho_allo=float(rho_allo.correlation),p_allo=float(rho_allo.pvalue))
print('\nESCALONAMENTO ALOMÉTRICO da aptidão: PV = a*massa^%.2f (R²=%.2f)'%(bexp,lr.rvalue**2))
print('  aptidão × fadiga da semana: bruta ρ=%.2f (p=%.3f) | alométrica (PV/massa^%.2f) ρ=%.2f (p=%.3f)'%(rho_raw.correlation,rho_raw.pvalue,bexp,rho_allo.correlation,rho_allo.pvalue))
json.dump(ALLO,open(f'{SC}/allo.json','w'),indent=1)

# ============ FIGURES ============
# F: derivadas expandidas (velocidade + aceleração por dia, barras) 5 vars
POS=[(1,1),(1,2),(1,3),(2,1),(2,2)]
f=make_subplots(rows=2,cols=3,subplot_titles=[l for _,l in CORE],vertical_spacing=0.14,horizontal_spacing=0.08)
for (v,lab),(r,c) in zip(CORE,POS):
    vel=[D[v]['vel'][str(d)] if str(d) in D[v]['vel'] else D[v]['vel'][d] for d in days]
    acc=[D[v]['acc'][str(d)] if str(d) in D[v]['acc'] else D[v]['acc'][d] for d in days]
    f.add_trace(go.Bar(x=list(days),y=vel,name='velocidade',marker_color=CV[v],showlegend=(r==1 and c==1)),r,c)
    f.add_trace(go.Scatter(x=list(days),y=acc,mode='lines+markers',name='aceleração',line=dict(color='#111',width=2,dash='dot'),showlegend=(r==1 and c==1)),r,c)
    f.add_hline(y=0,line=dict(color='#bbb',dash='dot'),row=r,col=c)
f.update_layout(**T(height=780,legend=dict(orientation='h',y=-0.08))); f.update_xaxes(dtick=1,title='Dia'); save(f,'x_deriv_exp')
# F: ROC curves com vs sem ruído (Vigor, Fadiga BRUMS, Fadiga física, TMD)
f=make_subplots(rows=2,cols=2,subplot_titles=['Vigor','Fadiga BRUMS','Fadiga física','PTH/TMD'],vertical_spacing=0.13,horizontal_spacing=0.12)
for (v),(r,c) in zip(['Vigor','Fadiga','FadFisica','TMD'],[(1,1),(1,2),(2,1),(2,2)]):
    fr,tr=ROC[v]['roc_raw']; ff,tf=ROC[v]['roc_filt']
    f.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',line=dict(color='#ccc',dash='dot'),showlegend=False),r,c)
    f.add_trace(go.Scatter(x=fr,y=tr,mode='lines',name='com ruído',line=dict(color='#adb5bd',width=3),showlegend=(r==1 and c==1)),r,c)
    f.add_trace(go.Scatter(x=ff,y=tf,mode='lines',name='sem ruído (filtrado)',line=dict(color=CV[v],width=3),showlegend=(r==1 and c==1)),r,c)
    f.add_annotation(x=0.6,y=0.15,text=f"AUC {ROC[v]['raw'][0]:.2f}→{ROC[v]['filt'][0]:.2f}".replace('.',','),showarrow=False,font=dict(size=12,color='#111'),row=r,col=c)
f.update_layout(**T(height=800,legend=dict(orientation='h',y=-0.08))); f.update_xaxes(title='1 − especificidade'); f.update_yaxes(title='sensibilidade'); save(f,'x_roc')
# F: allometric trajectory fit (log-log) for fatigue vars
f=make_subplots(rows=1,cols=2,subplot_titles=['Escala linear: Y = a·dia^b','Escala log-log'],horizontal_spacing=0.13)
for v,lab in [('FadFisica','Fadiga física'),('Fadiga','Fadiga BRUMS'),('TMD','PTH/TMD')]:
    dm=daily(v).groupby('dia')[v].mean().reindex(days).values; a=ALLO[v]['a']; b=ALLO[v]['b']
    xs=np.linspace(1,7,50)
    f.add_trace(go.Scatter(x=days,y=dm,mode='markers',marker=dict(color=CV[v],size=8),name=lab,showlegend=True),1,1)
    f.add_trace(go.Scatter(x=xs,y=a*xs**b,mode='lines',line=dict(color=CV[v],width=2),showlegend=False),1,1)
    f.add_trace(go.Scatter(x=np.log(days),y=np.log(np.clip(dm,1e-3,None)),mode='markers',marker=dict(color=CV[v],size=8),showlegend=False),1,2)
    f.add_trace(go.Scatter(x=np.log(xs),y=np.log(a)+b*np.log(xs),mode='lines',line=dict(color=CV[v],width=2),showlegend=False),1,2)
f.update_layout(**T(height=560,legend=dict(orientation='h',y=-0.2))); f.update_xaxes(title='Dia',row=1,col=1); f.update_xaxes(title='ln(Dia)',row=1,col=2); f.update_yaxes(title='Escore',row=1,col=1); f.update_yaxes(title='ln(Escore)',row=1,col=2)
save(f,'x_allo')
print('\nfigs OK: x_deriv_exp, x_roc, x_allo')
