import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv')
F=pd.read_csv('tcar2_features.csv')[['ID','pos','PV','PVini']]  # PV=T-CAR2(fin), PVini=T-CAR1
days=np.arange(1,8)
dm=h.groupby(['ID','dia'])['FadFisica'].mean().reset_index().merge(F,on='ID',how='left')
wk=h.groupby('ID')['FadFisica'].mean().reset_index().merge(F,on='ID',how='left')

def reg(x,y):
    m=pd.DataFrame({'x':x,'y':y}).dropna()
    if len(m)<5: return None
    lr=stats.linregress(m.x,m.y); rho,pr=stats.spearmanr(m.x,m.y)
    return dict(slope=float(lr.slope),intercept=float(lr.intercept),r2=float(lr.rvalue**2),p=float(lr.pvalue),
        rho=float(rho),rho_p=float(pr),n=int(len(m)))
# weekly
WK={'PVini':reg(wk.PVini,wk.FadFisica),'PVfin':reg(wk.PV,wk.FadFisica)}
# per-day
DAY={'PVini':{},'PVfin':{}}
for d in days:
    sub=dm[dm.dia==d]
    DAY['PVini'][int(d)]=reg(sub.PVini,sub.FadFisica)
    DAY['PVfin'][int(d)]=reg(sub.PV,sub.FadFisica)

# ---- logistic threshold P(high fatigue day) ~ PV ----
def auc(score,label):
    s=np.asarray(score,float); y=np.asarray(label); pos=s[y==1]; neg=s[y==0]
    if len(pos)==0 or len(neg)==0: return np.nan
    return float(stats.mannwhitneyu(pos,neg).statistic/(len(pos)*len(neg)))
def logit(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float); b0,b1=0.,0.
    for _ in range(300):
        z=b0+b1*x; pr=1/(1+np.exp(-z)); W=pr*(1-pr)+1e-9
        g0=np.sum(y-pr); g1=np.sum((y-pr)*x); h00=-np.sum(W); h01=-np.sum(W*x); h11=-np.sum(W*x*x); det=h00*h11-h01*h01
        b0-=(h11*g0-h01*g1)/det; b1-=(-h01*g0+h00*g1)/det
    return b0,b1
def youden(x,y):
    x=np.asarray(x,float); y=np.asarray(y); best=None
    for t in np.unique(x):
        pred=(x<=t).astype(int); tp=np.sum((pred==1)&(y==1)); fn=np.sum((pred==0)&(y==1)); tn=np.sum((pred==0)&(y==0)); fp=np.sum((pred==1)&(y==0))
        se=tp/(tp+fn+1e-9); sp=tn/(tn+fp+1e-9); j=se+sp-1
        if best is None or j>best[1]: best=(float(t),float(j),float(se),float(sp))
    return best
def limiar(col):
    dd=dm.dropna(subset=['FadFisica',col]).copy(); cut=dd.FadFisica.quantile(2/3); dd['hi']=(dd.FadFisica>=cut).astype(int)
    A=auc(-dd[col],dd['hi']); b0,b1=logit(dd[col],dd['hi']); yt=youden(dd[col],dd['hi'])
    ids=dd.ID.unique(); rng=np.random.default_rng(2024); boot=[]
    for _ in range(500):
        s=rng.choice(ids,len(ids),True); g=pd.concat([dd[dd.ID==i] for i in s]); boot.append(auc(-g[col],g['hi']))
    lo,hi=np.nanpercentile(boot,[2.5,97.5])
    return dict(auc=float(A),lo=float(lo),hi=float(hi),OR=float(np.exp(b1)),thr=yt[0],sens=yt[2],spec=yt[3],
        thr50=float(-b0/b1) if b1 else None,b0=float(b0),b1=float(b1),cut=float(cut),n=int(len(dd)))
LIM={'PVini':limiar('PVini'),'PVfin':limiar('PV')}

# ---- fitness terciles: mean weekly fatigue (most fit vs least fit) ----
wk['t_ini']=pd.qcut(wk.PVini,3,labels=['Baixa','Média','Alta'])
TERC={str(k):dict(n=int(len(g)),PV=float(g.PVini.mean()),FadFis=float(g.FadFisica.mean())) for k,g in wk.groupby('t_ini')}

RES=dict(WK=WK,DAY=DAY,LIM=LIM,TERC=TERC,pv_ini_mean=float(wk.PVini.mean()),pv_fin_mean=float(wk.PV.mean()))
json.dump(RES,open('tcar_limiar.json','w'),indent=1)
print('WEEKLY  T-CAR1 β=%.2f R²=%.2f ρ=%.2f p=%.3f | T-CAR2 β=%.2f R²=%.2f ρ=%.2f p=%.3f'%(
 WK['PVini']['slope'],WK['PVini']['r2'],WK['PVini']['rho'],WK['PVini']['p'],WK['PVfin']['slope'],WK['PVfin']['r2'],WK['PVfin']['rho'],WK['PVfin']['p']))
print('\nPER-DAY ρ (T-CAR1 / T-CAR2):')
for d in days:
    a=DAY['PVini'][int(d)]; b=DAY['PVfin'][int(d)]
    print('  D%d  %+.2f (p=%.2f) / %+.2f (p=%.2f)'%(d,a['rho'],a['rho_p'],b['rho'],b['rho_p']))
print('\nLIMIAR T-CAR1 AUC=%.2f[%.2f-%.2f] thr=%.1f (se%.2f/sp%.2f) OR=%.2f'%(LIM['PVini']['auc'],LIM['PVini']['lo'],LIM['PVini']['hi'],LIM['PVini']['thr'],LIM['PVini']['sens'],LIM['PVini']['spec'],LIM['PVini']['OR']))
print('LIMIAR T-CAR2 AUC=%.2f[%.2f-%.2f] thr=%.1f (se%.2f/sp%.2f) OR=%.2f'%(LIM['PVfin']['auc'],LIM['PVfin']['lo'],LIM['PVfin']['hi'],LIM['PVfin']['thr'],LIM['PVfin']['sens'],LIM['PVfin']['spec'],LIM['PVfin']['OR']))
print('\nTERCIS aptidão (T-CAR1) — fadiga semanal:',{k:round(v['FadFis'],2) for k,v in TERC.items()})
