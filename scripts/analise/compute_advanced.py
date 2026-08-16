import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import statsmodels.formula.api as smf
from itertools import combinations
hum=pd.read_csv('humor.csv')
def holm(pv):
    pv=np.asarray(pv); o=np.argsort(pv); adj=np.empty_like(pv); m=len(pv); run=0
    for rank,i in enumerate(o):
        run=max(run,(m-rank)*pv[i]); adj[i]=min(run,1)
    return adj
def posthoc(v,days=range(1,8)):
    d=hum[['ID','dia',v]].dropna().rename(columns={v:'y'}); d['dia']=d['dia'].astype(int)
    m=smf.mixedlm('y~C(dia)',d,groups=d['ID']).fit(reml=False)
    params=m.params; cov=m.cov_params()
    coef=lambda j: 0.0 if j==1 else params.get('C(dia)[T.%d]'%j,0.0)
    emm={j:float(params['Intercept']+coef(j)) for j in days}
    dfres=int(m.nobs-len(params)); k=len(list(days))
    pairs={}
    for a,b in combinations(days,2):
        na='C(dia)[T.%d]'%a; nb='C(dia)[T.%d]'%b
        va=cov.loc[na,na] if na in cov.index else 0.0; vb=cov.loc[nb,nb] if nb in cov.index else 0.0
        cab=cov.loc[na,nb] if (na in cov.index and nb in cov.index) else 0.0
        diff=coef(b)-coef(a); se=np.sqrt(max(va+vb-2*cab,1e-12)); t=diff/se
        q=abs(t)*np.sqrt(2)
        try: ptuk=float(stats.studentized_range.sf(q,k,dfres))
        except: ptuk=float('nan')
        pairs['%d_%d'%(a,b)]=dict(diff=float(diff),t=float(t),ptukey=ptuk)
    # day-to-day increments
    dd={j:emm[j]-emm[j-1] for j in range(2,8)}
    return dict(emm=emm,pairs=pairs,step=dd,n=int(d['ID'].nunique()),dfres=dfres)
R={}
for v in ['Vigor','Fadiga','FadFisica','TMD']:
    R[v]=posthoc(v)
# identify days of max change
def keyday(v,updown):
    step=R[v]['step']
    if updown=='down': d=min(step,key=step.get); return int(d),float(step[d])
    else: d=max(step,key=step.get); return int(d),float(step[d])
R['keydays']=dict(
    vigor_maxdrop_day=keyday('Vigor','down')[0], vigor_maxdrop=keyday('Vigor','down')[1],
    fadfis_maxrise_day=keyday('FadFisica','up')[0], fadfis_maxrise=keyday('FadFisica','up')[1],
    fadbrums_maxrise_day=keyday('Fadiga','up')[0], fadbrums_maxrise=keyday('Fadiga','up')[1],
    vigor_min_day=int(min(R['Vigor']['emm'],key=R['Vigor']['emm'].get)),
    fadfis_max_day=int(max(R['FadFisica']['emm'],key=R['FadFisica']['emm'].get)),
    fadbrums_max_day=int(max(R['Fadiga']['emm'],key=R['Fadiga']['emm'].get)))
json.dump(R,open('posthoc.json','w'),indent=1,ensure_ascii=False)
print('EMM Vigor:',{d:round(x,2) for d,x in R['Vigor']['emm'].items()})
print('EMM FadFisica:',{d:round(x,2) for d,x in R['FadFisica']['emm'].items()})
print('EMM Fadiga BRUMS:',{d:round(x,2) for d,x in R['Fadiga']['emm'].items()})
print('\nDias-chave:')
print('  Vigor cai mais forte: D%d->D%d (Δ=%.2f)'%(R['keydays']['vigor_maxdrop_day']-1,R['keydays']['vigor_maxdrop_day'],R['keydays']['vigor_maxdrop']))
print('  Fadiga física sobe mais forte: D%d->D%d (Δ=%.2f)'%(R['keydays']['fadfis_maxrise_day']-1,R['keydays']['fadfis_maxrise_day'],R['keydays']['fadfis_maxrise']))
print('  Fadiga BRUMS sobe mais forte: D%d->D%d (Δ=%.2f)'%(R['keydays']['fadbrums_maxrise_day']-1,R['keydays']['fadbrums_maxrise_day'],R['keydays']['fadbrums_maxrise']))
print('  Vigor mínimo: D%d | Fadiga física máxima: D%d'%(R['keydays']['vigor_min_day'],R['keydays']['fadfis_max_day']))
