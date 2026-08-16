import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv'); RC=json.load(open('rci6.json')); TS=json.load(open('tscore.json'))
SUB=['Vigor','Fadiga','Tensao','Depressao','Raiva','Confusao']  # profile order for corr matrix
NM={'Vigor':'Vigor','Fadiga':'Fadiga','Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
mu=TS['mu']; sd=TS['sd']
def Tsc(k,x): return 50+10*(x-mu[k])/sd[k]
R={}
# ---- Rohlfs Table 2 style: M, SD, min-max, T range, alpha, intercorrelation (obs-level Spearman) ----
desc=[]
for k in SUB:
    x=h[k].dropna()
    trange=(Tsc(k,x.min()),Tsc(k,x.max()))
    desc.append(dict(k=k,lab=NM[k],M=float(x.mean()),SD=float(x.std(ddof=1)),mn=int(x.min()),mx=int(x.max()),
        tmin=float(trange[0]),tmax=float(trange[1]),alpha=RC[k]['alpha']))
# intercorrelation matrix (Spearman, obs-level)
cm={}
for i,a in enumerate(SUB):
    for j,b in enumerate(SUB):
        if j>i:
            r,p=stats.spearmanr(h[a],h[b],nan_policy='omit'); cm['%s_%s'%(a,b)]=dict(r=float(r),p=float(p))
R['desc']=desc; R['corr']=cm; R['order']=SUB
# ---- Cluster prevalence D1 vs D7 + chi-square ----
PROF=['Iceberg','Everest invertido','Iceberg invertido','Submerso','Barbatana tubarão','Superfície']
def prevcount(mask):
    s=h[mask]['perfil'].value_counts()
    return {p:int(s.get(p,0)) for p in PROF}
d1c=prevcount(h.dia==1); d7c=prevcount(h.dia==7); allc=prevcount(h.index==h.index)
# chi-square on D1 vs D7 contingency (collapse zero rows handled)
tab=np.array([[d1c[p] for p in PROF],[d7c[p] for p in PROF]])
keep=[i for i in range(len(PROF)) if tab[:,i].sum()>0]
tab2=tab[:,keep]
chi,pchi,dof,exp=stats.chi2_contingency(tab2)
R['prev']=dict(D1=d1c,D7=d7c,overall=allc,chi=float(chi),p=float(pchi),dof=int(dof),
    n_d1=int(sum(d1c.values())),n_d7=int(sum(d7c.values())),profiles=PROF)
# ---- T-score comparison D1 vs D7 (M,SD in T units) + Wilcoxon + dz ----
dm=h.groupby(['ID','dia'])[SUB].mean().reset_index()
comp=[]
for k in SUB:
    p=dm.pivot(index='ID',columns='dia',values=k); a=p[1].dropna(); b=p[7].dropna()
    idx=a.index.intersection(b.index); a,b=a.loc[idx],b.loc[idx]
    ta=Tsc(k,a); tb=Tsc(k,b); d=tb-ta
    try: W,pw=stats.wilcoxon(a,b)
    except: W,pw=np.nan,np.nan
    dz=d.mean()/d.std(ddof=1) if d.std(ddof=1)>0 else 0
    comp.append(dict(k=k,lab=NM[k],t_d1=float(ta.mean()),sd_d1=float(ta.std(ddof=1)),
        t_d7=float(tb.mean()),sd_d7=float(tb.std(ddof=1)),W=float(W),p=float(pw),d=float(dz),n=int(len(idx))))
R['comp_d1d7']=comp
json.dump(R,open('model_stats.json','w'),indent=1,ensure_ascii=False)
print('Cluster prevalence D1 vs D7: chi2=%.2f p=%.4f dof=%d'%(R['prev']['chi'],R['prev']['p'],R['prev']['dof']))
print('D1:',d1c); print('D7:',d7c)
print('\nRohlfs-style descriptives (M,SD,alpha):')
for d in desc: print('  %-10s M=%.2f SD=%.2f a=%.2f Trange=%.0f-%.0f'%(d['lab'],d['M'],d['SD'],d['alpha'],d['tmin'],d['tmax']))
print('\nT-score D1->D7 comparison:')
for c in comp: print('  %-10s T:%.1f->%.1f p=%.3f d=%+.2f'%(c['lab'],c['t_d1'],c['t_d7'],c['p'],c['d']))
