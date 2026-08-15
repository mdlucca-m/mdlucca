import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv')
F=pd.read_csv('tcar2_features.csv')[['ID','pos','PVini']].rename(columns={'PVini':'PV'})  # T-CAR 1 only
days=np.arange(1,8)
OUT={'Vigor':{},'FadFisica':{}}
dm=h.groupby(['ID','dia'])[['FadFisica','Vigor']].mean().reset_index().merge(F,on='ID',how='left')
wk=h.groupby('ID')[['FadFisica','Vigor']].mean().reset_index().merge(F,on='ID',how='left')

def reg(x,y):
    m=pd.DataFrame({'x':x,'y':y}).dropna()
    lr=stats.linregress(m.x,m.y); rho,pr=stats.spearmanr(m.x,m.y)
    return dict(slope=float(lr.slope),intercept=float(lr.intercept),r2=float(lr.rvalue**2),p=float(lr.pvalue),rho=float(rho),rho_p=float(pr),n=int(len(m)))
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
def youden(x,y,hi_low):  # hi_low='low' => low PV predicts event (fatigue); 'high' => high PV predicts event (vigor)
    x=np.asarray(x,float); y=np.asarray(y); best=None
    for t in np.unique(x):
        pred=(x<=t).astype(int) if hi_low=='low' else (x>=t).astype(int)
        tp=np.sum((pred==1)&(y==1)); fn=np.sum((pred==0)&(y==1)); tn=np.sum((pred==0)&(y==0)); fp=np.sum((pred==1)&(y==0))
        se=tp/(tp+fn+1e-9); sp=tn/(tn+fp+1e-9); j=se+sp-1
        if best is None or j>best[1]: best=(float(t),float(j),float(se),float(sp))
    return best
def loo_auc(col,evcol,topfrac,direction):
    dd=dm.dropna(subset=[evcol,col]).copy()
    cut=dd[evcol].quantile(topfrac if direction=='high' else 1-topfrac)
    dd['ev']=(dd[evcol]>=cut).astype(int) if direction=='high' else (dd[evcol]>=dd[evcol].quantile(2/3)).astype(int)
    # for fatigue: event = top tercile high; for vigor: event = top tercile high
    dd['ev']=(dd[evcol]>=dd[evcol].quantile(2/3)).astype(int)
    ids=dd.ID.unique(); preds=[]; ys=[]
    for hold in ids:
        tr=dd[dd.ID!=hold]; te=dd[dd.ID==hold]
        if tr['ev'].nunique()<2: continue
        b0,b1=logit(tr[col],tr['ev'])
        pr=1/(1+np.exp(-(b0+b1*te[col].values))); preds+=list(pr); ys+=list(te['ev'].values)
    preds=np.array(preds); ys=np.array(ys)
    return float(auc(preds,ys)) if len(set(ys))>1 else np.nan
def threshold(col,evcol,direction):
    dd=dm.dropna(subset=[evcol,col]).copy(); dd['ev']=(dd[evcol]>=dd[evcol].quantile(2/3)).astype(int)
    score=dd[col] if direction=='high' else -dd[col]
    A=auc(score,dd['ev']); b0,b1=logit(dd[col],dd['ev']); yt=youden(dd[col],dd['ev'],'high' if direction=='high' else 'low')
    ids=dd.ID.unique(); rng=np.random.default_rng(7); boot=[]
    for _ in range(500):
        s=rng.choice(ids,len(ids),True); g=pd.concat([dd[dd.ID==i] for i in s]); boot.append(auc(g[col] if direction=='high' else -g[col],g['ev']))
    lo,hi=np.nanpercentile(boot,[2.5,97.5])
    cv=loo_auc(col,evcol,2/3,direction)
    return dict(auc=float(A),lo=float(lo),hi=float(hi),cv_auc=cv,OR=float(np.exp(b1)),thr=yt[0],sens=yt[2],spec=yt[3],b0=float(b0),b1=float(b1),n=int(len(dd)))

RES={}
for v in ['FadFisica','Vigor']:
    RES[v]=dict(week=reg(wk.PV,wk[v]),
        day={int(d):reg(dm[dm.dia==d].PV,dm[dm.dia==d][v]) for d in days},
        thr=threshold('PV',v,'low' if v=='FadFisica' else 'high'))
# terciles weekly by PV
wk['t']=pd.qcut(wk.PV,3,labels=['Baixa','Média','Alta'])
TERC={str(k):dict(n=int(len(g)),PV=float(g.PV.mean()),FadFis=float(g.FadFisica.mean()),Vigor=float(g.Vigor.mean())) for k,g in wk.groupby('t')}
# group daily vigor means (identify high-vigor days) + per-day PV x vigor
vday=h.groupby('dia')['Vigor'].mean().reindex(days)
RES['vigor_by_day']={int(d):float(vday[d]) for d in days}
RES['TERC']=TERC; RES['pv_mean']=float(wk.PV.mean())
json.dump(RES,open('tcar1_full.json','w'),indent=1)

print('T-CAR 1 ONLY (n=27)')
for v in ['FadFisica','Vigor']:
    w=RES[v]['week']; t=RES[v]['thr']
    print('\n== %s =='%v)
    print('  Semana: β=%+.2f R²=%.2f ρ=%+.2f p=%.3f'%(w['slope'],w['r2'],w['rho'],w['p']))
    print('  Por dia ρ:',{d:round(RES[v]['day'][d]['rho'],2) for d in range(1,8)})
    print('  Por dia p:',{d:round(RES[v]['day'][d]['rho_p'],3) for d in range(1,8)})
    print('  Limiar: thr=%.1f km/h AUC=%.2f[%.2f-%.2f] CV_AUC=%.2f sens=%.2f spec=%.2f OR=%.2f'%(t['thr'],t['auc'],t['lo'],t['hi'],t['cv_auc'],t['sens'],t['spec'],t['OR']))
print('\nVigor médio por dia (grupo):',{d:round(RES['vigor_by_day'][d],2) for d in range(1,8)})
print('Tercis PV — Vigor semanal:',{k:round(v['Vigor'],2) for k,v in TERC.items()},'| Fadiga:',{k:round(v['FadFis'],2) for k,v in TERC.items()})
