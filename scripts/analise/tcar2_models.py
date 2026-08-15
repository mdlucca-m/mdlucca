import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats

h=pd.read_csv('hum_prof.csv')
F=pd.read_csv('tcar2_features.csv')[['ID','pos','PV','PVini','dist','FCmax']]  # PV = PV final (T-CAR 2)
days=np.arange(1,8)
CORE=['FadFisica','Vigor','FadMental','TMD','Fadiga']
# daily athlete means
dm=h.groupby(['ID','dia'])[CORE].mean().reset_index().merge(F,on='ID',how='left')
# weekly per-athlete
wk=h.groupby('ID')[CORE].mean().reset_index().merge(F,on='ID',how='left')

def linreg(x,y):
    m=pd.DataFrame({'x':x,'y':y}).dropna(); lr=stats.linregress(m.x,m.y)
    rho,pr=stats.spearmanr(m.x,m.y)
    return dict(slope=float(lr.slope),intercept=float(lr.intercept),r2=float(lr.rvalue**2),
        p=float(lr.pvalue),rho=float(rho),rho_p=float(pr),n=int(len(m)))

# ===================== 1) REGRESSÕES (semana ~ PV_fin) e comparação PV_ini =====================
REG={}
for v in CORE:
    REG[v]=dict(PVfin=linreg(wk['PV'],wk[v]), PVini=linreg(wk['PVini'],wk[v]))

# ===================== 2) ALOMETRIA (só desfechos positivos, ratio-scale) =====================
def allo_fit(v):
    m=wk[['PV',v]].dropna()
    if (m[v]<=0).any(): return None  # allometria exige variável estritamente positiva
    x=np.log(m['PV']); y=np.log(m[v]); lr=stats.linregress(x,y)
    b=float(lr.slope)
    raw=float(stats.spearmanr(m['PV'],m[v]).correlation)
    after=float(stats.spearmanr(m['PV'],m[v]/(m['PV']**b)).correlation)
    unstable=abs(b)>3 or lr.rvalue**2<0.02
    return dict(b=b,r2=float(lr.rvalue**2),p=float(lr.pvalue),rho_before=raw,rho_after=after,unstable=bool(unstable))
ALLO={v:allo_fit(v) for v in ['FadFisica','Vigor']}
NORM=ALLO  # combined

# ===================== 3) LIMIAR / LOGÍSTICA / ROC (P(dia de fadiga alta) ~ PV_fin) =====================
def auc(score,label):
    s=np.asarray(score,float); y=np.asarray(label)
    pos=s[y==1]; neg=s[y==0]
    if len(pos)==0 or len(neg)==0: return np.nan
    return float(stats.mannwhitneyu(pos,neg).statistic/(len(pos)*len(neg)))
def logit_fit(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float); b0,b1=0.,0.
    for _ in range(300):
        z=b0+b1*x; pr=1/(1+np.exp(-z)); W=pr*(1-pr)+1e-9
        g0=np.sum(y-pr); g1=np.sum((y-pr)*x)
        h00=-np.sum(W); h01=-np.sum(W*x); h11=-np.sum(W*x*x); det=h00*h11-h01*h01
        b0-=( h11*g0-h01*g1)/det; b1-=(-h01*g0+h00*g1)/det
    return b0,b1
def youden(x,y):  # threshold maximizing sens+spec-1 over unique x
    x=np.asarray(x,float); y=np.asarray(y); best=None
    for t in np.unique(x):
        pred=(x<=t).astype(int)  # low PV -> high fatigue
        tp=np.sum((pred==1)&(y==1)); fn=np.sum((pred==0)&(y==1))
        tn=np.sum((pred==0)&(y==0)); fp=np.sum((pred==1)&(y==0))
        sens=tp/(tp+fn+1e-9); spec=tn/(tn+fp+1e-9); j=sens+spec-1
        if best is None or j>best[1]: best=(float(t),float(j),float(sens),float(spec))
    return best
def limiar(predcol):
    d=dm.dropna(subset=['FadFisica',predcol]).copy()
    cut=d['FadFisica'].quantile(2/3); d['hi']=(d['FadFisica']>=cut).astype(int)
    A=auc(-d[predcol],d['hi'])   # low predictor -> high fatigue
    b0,b1=logit_fit(d[predcol],d['hi']); OR=float(np.exp(b1)); thr50=float(-b0/b1) if b1!=0 else None
    yt=youden(d[predcol],d['hi'])
    # bootstrap AUC CI (athlete-clustered)
    ids=d['ID'].unique(); rng=np.random.default_rng(20240428); boot=[]
    for _ in range(600):
        samp=rng.choice(ids,len(ids),replace=True)
        dd=pd.concat([d[d.ID==i] for i in samp])
        boot.append(auc(-dd[predcol],dd['hi']))
    lo,hi=np.nanpercentile(boot,[2.5,97.5])
    return dict(auc=float(A),auc_lo=float(lo),auc_hi=float(hi),OR=OR,thr50=thr50,
        youden_thr=yt[0],youden_j=yt[1],sens=yt[2],spec=yt[3],cut=float(cut),n=int(len(d)))
LIM={'PVfin':limiar('PV'),'PVini':limiar('PVini')}
# tercile Kruskal (weekly FadFisica by PVfin tercile)
wk['terc']=pd.qcut(wk['PV'],3,labels=['Baixo','Médio','Alto'])
TERC={str(k):dict(n=int(len(g)),PV=float(g.PV.mean()),FadFis=float(g.FadFisica.mean()),Vigor=float(g.Vigor.mean())) for k,g in wk.groupby('terc')}
TERC_KW=dict(FadFisica=float(stats.kruskal(*[g.FadFisica.values for _,g in wk.groupby('terc')]).pvalue),
             Vigor=float(stats.kruskal(*[g.Vigor.values for _,g in wk.groupby('terc')]).pvalue))

# ===================== 4) LIMITES & DERIVADAS por tercil de PV_fin =====================
def cubic_traj(sub,v):
    s=sub.groupby('dia')[v].mean().reindex(days)
    yv=s.values; mask=~np.isnan(yv)
    if mask.sum()<4: return None
    c=np.polyfit(days[mask],yv[mask],3); p=np.poly1d(c); d1=p.deriv(); d2=p.deriv(2)
    fine=np.linspace(1,7,200)
    infl=fine[np.argmin(np.abs(d2(fine)))]  # zero of second derivative
    dose=float(np.trapezoid(p(days),days))
    return dict(traj=[float(x) for x in s.values],
        vel_mean=float(np.mean(d1(days))), vel_end=float(d1(7)),
        accel=float(np.mean(d2(days))), inflex=float(infl) if 1<=infl<=7 else None,
        dose=dose, rng=float(np.nanmax(yv)-np.nanmin(yv)))
DERIV={}
dm2=dm.merge(wk[['ID','terc']],on='ID',how='left')
for terc,g in dm2.groupby('terc'):
    DERIV[str(terc)]={v:cubic_traj(g,v) for v in ['FadFisica','Vigor']}

RES=dict(REG=REG,ALLO=ALLO,NORM=NORM,LIM=LIM,TERC=TERC,TERC_KW=TERC_KW,DERIV=DERIV,
    pv_fin_mean=float(wk['PV'].mean()),pv_ini_mean=float(wk['PVini'].mean()),n=int(len(wk)))
json.dump(RES,open('tcar2_models.json','w'),indent=1)

# ---------- console ----------
def f(x): return '%+.2f'%x
print('=== 1) REGRESSÃO semanal ~ PV (fin vs ini) ===')
print('%-10s %28s %28s'%('var','PV_fin (β,R²,ρ,p)','PV_ini (β,R²,ρ,p)'))
for v in CORE:
    a=REG[v]['PVfin']; b=REG[v]['PVini']
    print('%-10s  β=%+.2f R²=%.2f ρ=%+.2f p=%.3f | β=%+.2f R²=%.2f ρ=%+.2f p=%.3f'%(v,a['slope'],a['r2'],a['rho'],a['p'],b['slope'],b['r2'],b['rho'],b['p']))
print('\n=== 2) ALOMETRIA Y~PV_fin^b ; normalização (ρ antes→depois) ===')
for v in ['FadFisica','Vigor']:
    a=ALLO[v];
    if a: print('  %-9s b=%+.2f R²=%.2f p=%.3f | norm ρ %+.2f→%+.2f %s'%(v,a['b'],a['r2'],a['p'],a['rho_before'],a['rho_after'],'(INSTÁVEL)' if a['unstable'] else ''))
print('\n=== 3) LIMIAR/LOGÍSTICA/ROC P(dia fadiga alta) ~ PV ===')
for k,L in LIM.items():
    print('  %-6s AUC=%.2f [%.2f–%.2f] OR=%.2f/km·h limiar(Youden)=%.1f (sens %.2f/spec %.2f) 50%%=%.1f km/h n=%d'%(
        k,L['auc'],L['auc_lo'],L['auc_hi'],L['OR'],L['youden_thr'],L['sens'],L['spec'],L['thr50'],L['n']))
print('  Tercis PV_fin — FadFis:',{k:round(v['FadFis'],2) for k,v in TERC.items()},'Kruskal p=%.3f'%TERC_KW['FadFisica'])
print('\n=== 4) DERIVADAS/LIMITES por tercil PV_fin (FadFisica) ===')
for terc in ['Baixo','Médio','Alto']:
    d=DERIV.get(terc,{}).get('FadFisica')
    if d: print('  %-6s dose=%.1f vel_méd=%+.2f accel=%+.2f inflex=%s range=%.1f'%(terc,d['dose'],d['vel_mean'],d['accel'],('%.1f'%d['inflex']) if d['inflex'] else '—',d['rng']))
