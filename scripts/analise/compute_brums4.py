import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv')
VARS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('TMD','PTH/TMD'),('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]
KEYS=[k for k,_ in VARS]; days=np.arange(1,8)
dm=h.groupby(['ID','dia'])[KEYS].mean().reset_index()
wk=h.groupby('ID')[KEYS].mean()
R={}
# percentiles + CV intra/inter
R['pct']={}; R['cv']={}
for k,_ in VARS:
    x=h[k].dropna()
    R['pct'][k]=dict(p25=float(np.percentile(x,25)),p50=float(np.percentile(x,50)),p75=float(np.percentile(x,75)))
    # CV inter: between-athlete (weekly means)
    m=wk[k]; cv_inter=100*m.std(ddof=1)/m.mean() if m.mean() else np.nan
    # CV intra: within-athlete across days, averaged
    cvs=[]
    for aid,g in dm.groupby('ID'):
        gm=g[k].mean();
        if gm>0: cvs.append(100*g[k].std(ddof=1)/gm)
    R['cv'][k]=dict(inter=float(cv_inter),intra=float(np.nanmean(cvs)))
# Friedman + Kendall W (across 7 days, complete cases)
R['friedman']={}
for k,_ in VARS:
    M=dm.pivot(index='ID',columns='dia',values=k).dropna()
    cols=[M[d].values for d in days]
    chi,p=stats.friedmanchisquare(*cols); n,kk=M.shape; W=chi/(n*(kk-1))
    R['friedman'][k]=dict(chi=float(chi),p=float(p),W=float(W),n=int(n))
# sensitivity ranking = |dz| D1->D7
D17={}
for k,_ in VARS:
    p=dm.pivot(index='ID',columns='dia',values=k); a=p[1]; b=p[7]; c=a.dropna().index.intersection(b.dropna().index); a,b=a.loc[c],b.loc[c]; d=b-a
    dz=d.mean()/d.std(ddof=1) if d.std(ddof=1)>0 else 0
    D17[k]=dict(dz=float(dz),absdz=float(abs(dz)))
R['sens']=D17
# per-athlete D1/D7 (anonymized) + profile transitions
prof_d1=h[h.dia==1].groupby('ID')['perfil'].agg(lambda s:s.mode().iat[0] if len(s.mode()) else None)
prof_d7=h[h.dia==7].groupby('ID')['perfil'].agg(lambda s:s.mode().iat[0] if len(s.mode()) else None)
trans=pd.DataFrame({'D1':prof_d1,'D7':prof_d7}).dropna()
R['prof_trans']={aid:{'D1':row['D1'],'D7':row['D7']} for aid,row in trans.iterrows()}
# per-athlete weekly vigor/fadiga (for spaghetti available in csv)
dm.to_csv('brums_daily.csv',index=False)
# profile percentiles: distribution already in desc2; add count of iceberg athletes D1/D7
R['prof_counts']=dict(iceberg_D1=int((prof_d1=='Iceberg').sum()),iceberg_D7=int((prof_d7=='Iceberg').sum()),
    shark_D1=int((prof_d1=='Barbatana tubarão').sum()),shark_D7=int((prof_d7=='Barbatana tubarão').sum()),n=int(len(trans)))
json.dump(R,open('brums_stats4.json','w'),indent=1,ensure_ascii=False)
print('CV intra / inter (%):')
for k,_ in VARS: print('  %-10s intra=%.0f inter=%.0f'%(k,R['cv'][k]['intra'],R['cv'][k]['inter']))
print('\nFriedman (7 dias) + Kendall W:')
for k,_ in VARS: v=R['friedman'][k]; print('  %-10s chi2=%.1f p=%.4f W=%.2f'%(k,v['chi'],v['p'],v['W']))
print('\nSensibilidade (|dz| D1->D7, ordenado):')
for k,_ in sorted(VARS,key=lambda x:-D17[x[0]]['absdz']): print('  %-10s dz=%+.2f'%(k,D17[k]['dz']))
print('\nPercentis Vigor:',R['pct']['Vigor'],'| Fadiga:',R['pct']['Fadiga'])
print('perfil transições n=%d'%R['prof_counts']['n'])
