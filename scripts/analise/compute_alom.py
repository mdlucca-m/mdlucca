import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
h=pd.read_csv(SC+'/hum_prof.csv'); phys=pd.read_csv(SC+'/phys.csv')
wk=h.groupby('ID')[['Vigor','Fadiga','TMD','FadFisica']].mean().reset_index()
F=pd.read_csv(SC+'/tcar2_features.csv')[['ID','PVini']]
D=wk.merge(phys[['ID','massa','estatura','pGordura']],on='ID').merge(F,on='ID').dropna()
R={'n':int(len(D))}
# composição corporal
R['desc']={c:dict(M=float(D[c].mean()),SD=float(D[c].std(ddof=1)),mn=float(D[c].min()),mx=float(D[c].max())) for c in ['massa','estatura','pGordura']}
# correlações massa/%gordura x humor
R['corr']={}
for x in ['massa','pGordura']:
    R['corr'][x]={}
    for y in ['Fadiga','FadFisica','Vigor']:
        r,p=stats.spearmanr(D[x],D[y]); R['corr'][x][y]=dict(rho=float(r),p=float(p))
# expoente alométrico log(PV)~log(massa)
lm=np.polyfit(np.log(D.massa),np.log(D.PVini),1); b=float(lm[0])
rr,pp=stats.pearsonr(np.log(D.massa),np.log(D.PVini))
R['alom']=dict(b=b,loglog_r=float(rr),loglog_p=float(pp))
# PV bruto vs PV normalizado (alométrico) x fadiga física / vigor
D['PV_alom']=D.PVini/(D.massa**b)
R['pv_adj']={}
for lab,col in [('bruto','PVini'),('alom','PV_alom')]:
    rf,pf=stats.spearmanr(D[col],D['FadFisica']); rv,pv=stats.spearmanr(D[col],D['Vigor'])
    R['pv_adj'][lab]=dict(fadfis_rho=float(rf),fadfis_p=float(pf),vigor_rho=float(rv),vigor_p=float(pv))
json.dump(R,open(SC+'/alom.json','w'),indent=1,ensure_ascii=False)
print('n=%d | massa %.1f±%.1f | %%gord %.1f±%.1f | b=%.2f (p=%.3f)'%(R['n'],R['desc']['massa']['M'],R['desc']['massa']['SD'],R['desc']['pGordura']['M'],R['desc']['pGordura']['SD'],b,pp))
print('PV bruto  × FadFís rho=%+.2f (p=%.3f) | × Vigor rho=%+.2f (p=%.3f)'%(R['pv_adj']['bruto']['fadfis_rho'],R['pv_adj']['bruto']['fadfis_p'],R['pv_adj']['bruto']['vigor_rho'],R['pv_adj']['bruto']['vigor_p']))
print('PV alom.  × FadFís rho=%+.2f (p=%.3f) | × Vigor rho=%+.2f (p=%.3f)'%(R['pv_adj']['alom']['fadfis_rho'],R['pv_adj']['alom']['fadfis_p'],R['pv_adj']['alom']['vigor_rho'],R['pv_adj']['alom']['vigor_p']))
