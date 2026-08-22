# -*- coding: utf-8 -*-
# Quanto cada perfil de humor variou ao longo da semana e entre os dias:
# prevalencia %/dia, Delta(D7-D1), amplitude, maior salto entre dias, e Cochran Q
# (varia a prevalencia entre os 7 dias?) no subconjunto balanceado.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from statsmodels.stats.contingency_tables import cochrans_q
h=pd.read_csv('humor_anon.csv')
S=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
ad=h.groupby(['ID','dia'])[S].mean().reset_index().dropna(subset=S)
Z=ad[S].apply(lambda c:(c-c.mean())/c.std())
CENT={'Iceberg':[-0.5,-0.5,-0.5,1.0,-0.5,-0.5],'Iceberg invertido':[0.6,0.6,0.6,-1.0,0.6,0.6],
 'Everest invertido':[1.2,1.4,1.2,-0.8,1.2,1.2],'Barbatana de tubarão':[0.2,0.2,0.2,0.3,1.4,0.2],
 'Superfície':[0,0,0,0,0,0],'Submerso':[-0.9,-0.9,-0.9,-0.9,-0.9,-0.9]}
names=list(CENT); CM=np.array([CENT[k] for k in names])
ad['perfil']=[names[int(np.argmin(((CM-r.values)**2).sum(1)))] for _,r in Z.iterrows()]
ORD=['Iceberg','Superfície','Submerso','Barbatana de tubarão','Everest invertido','Iceberg invertido']
pct=pd.crosstab(ad['dia'],ad['perfil'],normalize='index').mul(100).reindex(columns=ORD).reindex(range(1,8))
bal=ad.pivot_table(index='ID',columns='dia',values='perfil',aggfunc='first').dropna()
res=[]
for p in ORD:
    row=[float(pct.loc[d,p]) if not pd.isna(pct.loc[d,p]) else 0.0 for d in range(1,8)]
    M=(bal[[1,2,3,4,5,6,7]]==p).astype(int).values
    try: qp=float(cochrans_q(M).pvalue)
    except Exception: qp=float('nan')
    res.append(dict(perfil=p,pct=[round(x,1) for x in row],delta=round(row[6]-row[0],1),
                    amp=round(max(row)-min(row),1),maxstep=round(max(abs(row[i+1]-row[i]) for i in range(6)),1),qp=round(qp,4)))
json.dump(res,open('perfil_variacao.json','w'))
for r in res: print(r['perfil'],r['pct'],'Δ=',r['delta'],'amp=',r['amp'],'maxΔ=',r['maxstep'],'Qp=',r['qp'])
