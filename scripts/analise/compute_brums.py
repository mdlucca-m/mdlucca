import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv'); phys=pd.read_csv('phys.csv')
app=json.load(open('app_data.json'))
days=np.arange(1,8)
SUBS=[('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Vigor','Vigor'),('Fadiga','Fadiga'),('Confusao','Confusão'),('TMD','PTH/TMD')]
def mag(dz):
    a=abs(dz); return 'trivial' if a<0.2 else ('pequeno' if a<0.5 else ('médio' if a<0.8 else 'grande'))
def desc(x):
    x=pd.Series(x).dropna(); n=len(x); m=x.mean(); sd=x.std(ddof=1); se=sd/np.sqrt(n)
    ci=stats.t.interval(0.95,n-1,loc=m,scale=se)
    return dict(n=int(n),mean=float(m),md=float(x.median()),sd=float(sd),lo=float(ci[0]),hi=float(ci[1]),
        mn=float(x.min()),mx=float(x.max()),cv=float(100*sd/m) if m else np.nan)
R={}
# 1) group overall descriptive
R['desc']={k:desc(h[k]) for k,_ in SUBS}
# 2) pré vs pós (week, athlete-level paired means over week)
pp=h[h.momento.isin(['pre','pos'])].copy()
R['prepos']={}
for k,_ in SUBS:
    piv=pp.pivot_table(index='ID',columns='momento',values=k,aggfunc='mean')
    a=piv['pre']; b=piv['pos']; c=a.dropna().index.intersection(b.dropna().index); a,b=a.loc[c],b.loc[c]
    dd=b-a; dz=dd.mean()/dd.std(ddof=1); p=stats.wilcoxon(a,b).pvalue if dd.std()>0 else 1
    se=dd.std(ddof=1)/np.sqrt(len(dd)); ci=stats.t.interval(0.95,len(dd)-1,loc=dd.mean(),scale=se)
    pct=100*dd.mean()/a.mean() if a.mean() else np.nan
    R['prepos'][k]=dict(pre=float(a.mean()),pos=float(b.mean()),delta=float(dd.mean()),pct=float(pct),
        dz=float(dz),lo=float(ci[0]),hi=float(ci[1]),p=float(p),mag=mag(dz),n=int(len(dd)))
# 3) per-day daily means (pre/pos/overall)
R['byday']={}
for k,_ in SUBS:
    dd={}
    for d in days:
        sub=h[h.dia==d]
        pre=sub[sub.momento=='pre'][k].mean(); pos=sub[sub.momento=='pos'][k].mean(); allm=sub[k].mean()
        dd[int(d)]=dict(pre=float(pre),pos=float(pos),all=float(allm))
    R['byday'][k]=dd
# 4) intra-day pré→pós per day (Vigor, Fadiga, TMD)
R['intraday']={}
for k in ['Vigor','Fadiga','TMD']:
    dd={}
    for d in days:
        sub=h[(h.dia==d)&(h.momento.isin(['pre','pos']))]
        piv=sub.pivot_table(index='ID',columns='momento',values=k,aggfunc='mean')
        if 'pre' in piv and 'pos' in piv:
            a=piv['pre']; b=piv['pos']; c=a.dropna().index.intersection(b.dropna().index); a,b=a.loc[c],b.loc[c]
            di=b-a
            if len(di)>2 and di.std(ddof=1)>0:
                dz=di.mean()/di.std(ddof=1); p=stats.wilcoxon(a,b).pvalue
                dd[int(d)]=dict(delta=float(di.mean()),dz=float(dz),p=float(p),mag=mag(dz))
            else: dd[int(d)]=dict(delta=float(di.mean()) if len(di) else np.nan,dz=np.nan,p=np.nan,mag='—')
    R['intraday'][k]=dd
# 5) D1 vs D7 (start vs end of week)
R['d1d7']={}
for k,_ in SUBS:
    piv=h.groupby(['ID','dia'])[k].mean().reset_index().pivot(index='ID',columns='dia',values=k)
    a=piv[1]; b=piv[7]; c=a.dropna().index.intersection(b.dropna().index); a,b=a.loc[c],b.loc[c]; dd=b-a
    dz=dd.mean()/dd.std(ddof=1) if dd.std(ddof=1)>0 else 0; p=stats.wilcoxon(a,b).pvalue if dd.std(ddof=1)>0 else 1
    pct=100*dd.mean()/a.mean() if a.mean() else np.nan
    R['d1d7'][k]=dict(d1=float(a.mean()),d7=float(b.mean()),delta=float(dd.mean()),pct=float(pct),dz=float(dz),p=float(p),mag=mag(dz))
# 6) profiles distribution
PROF_ORDER=['Iceberg','Everest invertido','Iceberg invertido','Submerso','Barbatana tubarão','Superfície']
def dist(df):
    vc=df['perfil'].value_counts(); tot=len(df)
    return {p:round(100*vc.get(p,0)/tot,0) for p in PROF_ORDER}
R['profiles']=dict(overall=dist(h),
    D1=dist(h[h.dia==1]),D7=dist(h[h.dia==7]),
    pre=dist(h[h.momento=='pre']),pos=dist(h[h.momento=='pos']))
# 7) sample characterization
ath=pd.DataFrame(app['socio']['athletes'])
R['sample']=dict(n=len(ath),
    idade=desc(ath['idade']),massa=desc(ath['massa']),estatura=desc(ath['estatura']),
    pG=desc(ath['pG']),exp=desc(ath['exp']),
    pos=ath['pos'].value_counts().to_dict(),
    n_obs=int(len(h)),n_days=7)
# 8) intra-subject variability (range of athlete weekly means; % vigor decrease D1->D7)
R['subject']={}
for k in ['Vigor','Fadiga','TMD']:
    wk=h.groupby('ID')[k].mean()
    piv=h.groupby(['ID','dia'])[k].mean().reset_index().pivot(index='ID',columns='dia',values=k)
    d17=(piv[7]-piv[1]).dropna()
    worse=(d17<0).sum() if k=='Vigor' else (d17>0).sum()
    R['subject'][k]=dict(wk_min=float(wk.min()),wk_max=float(wk.max()),
        pct_worse=round(100*worse/len(d17),0),n=int(len(d17)))
json.dump(R,open('brums_desc.json','w'),indent=1,ensure_ascii=False)
print('OK')
print('pré→pós semana:')
for k,_ in SUBS: v=R['prepos'][k]; print('  %-10s pré=%.2f pós=%.2f Δ=%+.2f (%.0f%%) dz=%+.2f [%.2f,%.2f] p=%.1e %s'%(k,v['pre'],v['pos'],v['delta'],v['pct'],v['dz'],v['lo'],v['hi'],v['p'],v['mag']))
print('D1→D7:')
for k,_ in SUBS: v=R['d1d7'][k]; print('  %-10s D1=%.2f D7=%.2f Δ=%+.2f dz=%+.2f p=%.3f %s'%(k,v['d1'],v['d7'],v['delta'],v['dz'],v['p'],v['mag']))
print('perfis overall:',R['profiles']['overall'])
print('perfis D1:',R['profiles']['D1'],'D7:',R['profiles']['D7'])
