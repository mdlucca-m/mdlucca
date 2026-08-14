import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv')
VARS=[('Vigor','Vigor (0–20)'),('Fadiga','Fadiga BRUMS (0–20)'),('TMD','PTH/TMD'),('FadMental','Fadiga mental (0–10)')]
PP={}
for v,lab in VARS:
    rows={}
    for day in range(1,8):
        g=hum[(hum.dia==day)].dropna(subset=[v])
        pre=g[g.momento=='pre'][['ID',v]].set_index('ID')[v]
        pos=g[g.momento=='pos'][['ID',v]].set_index('ID')[v]
        # paired by athlete
        common=pre.index.intersection(pos.index)
        a,b=pre.loc[common],pos.loc[common]
        d=b-a; npair=len(common)
        pmean=pre.mean(); psd=pre.std(); qmean=pos.mean(); qsd=pos.std()
        delta=qmean-pmean
        if npair>=3 and d.std()>0:
            dz=d.mean()/d.std()
            try: w=stats.wilcoxon(a.values,b.values); pw=w.pvalue
            except Exception: pw=np.nan
        else: dz=np.nan; pw=np.nan
        rows[day]=dict(npre=int(pre.count()),npos=int(pos.count()),npair=npair,
            pre_m=round(float(pmean),2),pre_sd=round(float(psd),2),
            pos_m=round(float(qmean),2),pos_sd=round(float(qsd),2),
            delta=round(float(delta),2),dz=(round(float(dz),2) if not np.isnan(dz) else None),
            p=(float(pw) if not np.isnan(pw) else None),hiit=int(g['HIIT'].iloc[0]) if len(g) else 0)
    PP[v]=rows
json.dump(PP,open(f'{SC}/prepost.json','w'),indent=1)
# print quick view
for v,lab in VARS:
    print('==',lab)
    for day,r in PP[v].items():
        star='*' if (r['p'] is not None and r['p']<0.05) else ' '
        print(f"  D{day}{'(HIIT)' if r['hiit'] else '      '} pré {r['pre_m']:.2f}±{r['pre_sd']:.2f}  pós {r['pos_m']:.2f}±{r['pos_sd']:.2f}  Δ{r['delta']:+.2f}  dz={r['dz']} p={r['p'] if r['p'] is None else round(r['p'],4)}{star}")
