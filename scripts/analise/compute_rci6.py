import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv'); it=pd.read_csv('items.csv')
ITEMS={'Tensao':['Apavorado','Ansioso','Preocupado','Tenso'],
 'Depressao':['Deprimido','Desanimado','Triste','Infeliz'],
 'Raiva':['Irritado','Zangado','ComRaiva','MalHumorado'],
 'Vigor':['Animado','ComDisposição','ComEnergia','Alerta'],
 'Fadiga':['Esgotado','Exausto','Sonolento','Cansado'],
 'Confusao':['Confuso','Inseguro','Desorientado','Indeciso']}
def alpha(cols):
    X=it[cols].dropna(); k=len(cols); vi=X.var(ddof=1).sum(); vt=X.sum(axis=1).var(ddof=1)
    return float(k/(k-1)*(1-vi/vt))
dm=h.groupby(['ID','dia'])[list(ITEMS)].mean().reset_index()
def piv(v): return dm.pivot(index='ID',columns='dia',values=v)
RES={}
for k in ITEMS:
    a=alpha(ITEMS[k]); p=piv(k); d1=p[1]; d7=p[7]; sd1=d1.std(ddof=1)
    sediff=sd1*np.sqrt(2*(1-a)); rci=(d7-d1)/sediff
    r=rci.dropna(); n=len(r)
    if k=='Vigor':
        piora=int((r<=-1.96).sum()); melhora=int((r>=1.96).sum())
    else:
        piora=int((r>=1.96).sum()); melhora=int((r<=-1.96).sum())
    est=n-piora-melhora
    RES[k]=dict(alpha=a,sd1=float(sd1),sediff=float(sediff),n=int(n),
        piora=piora,estavel=est,melhora=melhora,
        pct_piora=round(100*piora/n),pct_est=round(100*est/n),pct_mel=round(100*melhora/n),
        rci={str(i):(float(x) if pd.notna(x) else None) for i,x in rci.items()})
json.dump(RES,open('rci6.json','w'),indent=1)
print('Subescala   α    EPdif  n  piora(%)  estável(%)  melhora(%)')
for k,v in RES.items():
    print('%-10s %.2f  %.2f  %2d  %d(%d%%)   %d(%d%%)   %d(%d%%)'%(k,v['alpha'],v['sediff'],v['n'],v['piora'],v['pct_piora'],v['estavel'],v['pct_est'],v['melhora'],v['pct_mel']))
