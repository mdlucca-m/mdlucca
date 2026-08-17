import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
from scipy.stats import f as fdist, chi2
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
h=pd.read_csv(SC+'/hum_prof.csv')
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
LAB={'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Vigor':'Vigor','Fadiga':'Fadiga','Confusao':'Confusão','TMD':'PTH'}

# ---- FILTRO: distância de Mahalanobis nas 6 subescalas -> remove outliers multivariados ----
X=h[SUB].values; mu=X.mean(0); S=np.cov(X,rowvar=False); Si=np.linalg.pinv(S)
d2=np.array([ (r-mu)@Si@(r-mu) for r in X ])
thr=chi2.ppf(0.999,df=6)                     # limiar p<0,001
h=h.assign(_maha=d2, _out=d2>thr)
n_out=int(h['_out'].sum())
HF=h[~h['_out']].copy()                       # conjunto FILTRADO (sinal)
print('Outliers multivariados (Mahalanobis, p<0,001): %d de %d (%.1f%%)'%(n_out,len(h),100*n_out/len(h)))

def dz_d1d7(df,k):
    dm=df.groupby(['ID','dia'])[k].mean().reset_index().pivot(index='ID',columns='dia',values=k)
    a,b=dm[1],dm[7]; idx=a.dropna().index.intersection(b.dropna().index); d=b.loc[idx]-a.loc[idx]
    return float(d.mean()/d.std(ddof=1)), float(stats.wilcoxon(a.loc[idx],b.loc[idx]).pvalue)
def friedman(df,k):
    dm=df.groupby(['ID','dia'])[k].mean().reset_index()
    M=dm.pivot(index='ID',columns='dia',values=k).dropna()
    chi,p=stats.friedmanchisquare(*[M[c] for c in M.columns]); return float(p)
def manova_wilks(df):
    mu={k:df[k].mean() for k in SUB}; sd={k:df[k].std(ddof=1) for k in SUB}
    T=lambda k,x:50+10*(x-mu[k])/sd[k]
    dm=df.groupby(['ID','dia'])[SUB].mean().reset_index()
    P={k:dm.pivot(index='ID',columns='dia',values=k) for k in SUB}
    idx=None
    for k in SUB:
        ii=P[k][1].dropna().index.intersection(P[k][7].dropna().index); idx=ii if idx is None else idx.intersection(ii)
    D=np.column_stack([T(k,P[k][7].loc[idx])-T(k,P[k][1].loc[idx]) for k in SUB])
    n,p=D.shape; db=D.mean(0); Sc=np.cov(D,rowvar=False); T2=n*db@np.linalg.pinv(Sc)@db
    F=(n-p)/(p*(n-1))*T2; wilks=1/(1+T2/(n-1)); pval=1-fdist.cdf(F,p,n-p)
    return float(wilks),float(pval)

R={'n_out':n_out,'n_total':int(len(h)),'thr':float(thr),'rows':[]}
print('\n%-12s %18s %18s'%('Métrica','BRUTO','FILTRADO'))
for k in ['Vigor','Fadiga','Tensao','Confusao']:
    dzr,pr=dz_d1d7(h,k); dzf,pf=dz_d1d7(HF,k)
    print('  D1→D7 dz %-8s %+8.2f (p=%.3f)   %+8.2f (p=%.3f)'%(LAB[k],dzr,pr,dzf,pf))
    R['rows'].append(dict(metric='dz_%s'%k,raw=dzr,filt=dzf,raw_p=pr,filt_p=pf))
for k in ['Vigor','Fadiga']:
    fr,ff=friedman(h,k),friedman(HF,k)
    print('  Friedman p %-7s %10.4f        %10.4f'%(LAB[k],fr,ff))
    R['rows'].append(dict(metric='friedman_%s'%k,raw=fr,filt=ff))
wr,wpr=manova_wilks(h); wf,wpf=manova_wilks(HF)
print('  MANOVA Wilks     %8.3f (p=%.4f)  %8.3f (p=%.4f)'%(wr,wpr,wf,wpf))
R['rows'].append(dict(metric='manova_wilks',raw=wr,filt=wf,raw_p=wpr,filt_p=wpf))
# correlações-chave (nível atleta)
def corr(df,a,b):
    wk=df.groupby('ID')[[a,b]].mean(); return float(stats.spearmanr(wk[a],wk[b]).correlation)
for a,b,nm in [('Vigor','Fadiga','Vigor×Fadiga (semanal)'),('Fadiga','FadFisica','Fadiga×FadFís')]:
    cr,cf=corr(h,a,b),corr(HF,a,b)
    print('  ρ %-22s %+8.2f          %+8.2f'%(nm,cr,cf))
    R['rows'].append(dict(metric='rho_%s_%s'%(a,b),raw=cr,filt=cf))
json.dump(R,open(SC+'/audit.json','w'),indent=1,ensure_ascii=False)
print('\n[salvo audit.json]')
