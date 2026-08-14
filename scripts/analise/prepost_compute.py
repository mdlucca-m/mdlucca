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
        # aggregate to one value per athlete per momento (mid may have several intra-session rows)
        pre=g[g.momento=='pre'].groupby('ID')[v].mean()
        mid=g[g.momento=='mid'].groupby('ID')[v].mean()
        pos=g[g.momento=='pos'].groupby('ID')[v].mean()
        # paired pré→pós by athlete
        common=pre.index.intersection(pos.index)
        a,b=pre.loc[common],pos.loc[common]
        d=b-a; npair=len(common)
        pmean=pre.mean(); psd=pre.std(); qmean=pos.mean(); qsd=pos.std()
        mmean=mid.mean(); msd=mid.std(); nmid=int(mid.count())
        delta=qmean-pmean
        if npair>=3 and d.std()>0:
            dz=d.mean()/d.std()
            try: w=stats.wilcoxon(a.values,b.values); pw=w.pvalue
            except Exception: pw=np.nan
        else: dz=np.nan; pw=np.nan
        # Friedman pré/mid/pós when mid exists (athletes with all three)
        pfried=np.nan
        if nmid>=3:
            allc=pre.index.intersection(mid.index).intersection(pos.index)
            if len(allc)>=3:
                try: pfried=stats.friedmanchisquare(pre.loc[allc],mid.loc[allc],pos.loc[allc]).pvalue
                except Exception: pfried=np.nan
        rows[day]=dict(npre=int(pre.count()),nmid=nmid,npos=int(pos.count()),npair=npair,
            pre_m=round(float(pmean),2),pre_sd=round(float(psd),2),
            mid_m=(round(float(mmean),2) if nmid>0 else None),mid_sd=(round(float(msd),2) if nmid>1 else None),
            pos_m=round(float(qmean),2),pos_sd=round(float(qsd),2),
            delta=round(float(delta),2),dz=(round(float(dz),2) if not np.isnan(dz) else None),
            p=(float(pw) if not np.isnan(pw) else None),
            pfried=(float(pfried) if not np.isnan(pfried) else None),
            hiit=int(g['HIIT'].iloc[0]) if len(g) else 0)
    PP[v]=rows
json.dump(PP,open(f'{SC}/prepost.json','w'),indent=1)
# print quick view
for v,lab in VARS:
    print('==',lab)
    for day,r in PP[v].items():
        star='*' if (r['p'] is not None and r['p']<0.05) else ' '
        midtxt=f"mid {r['mid_m']:.2f}" if r['mid_m'] is not None else "mid —  "
        print(f"  D{day}{'(HIIT)' if r['hiit'] else '      '} pré {r['pre_m']:.2f}  {midtxt}  pós {r['pos_m']:.2f}  Δ{r['delta']:+.2f}  dz={r['dz']} p={r['p'] if r['p'] is None else round(r['p'],4)}{star} nmid={r['nmid']}")
