import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv')
F=pd.read_csv('tcar2_features.csv')[['ID','pos','PV','PVini','dPV']]
# weekly athlete means of BRUMS + physical fatigue
WK=h.groupby('ID')[['Vigor','Fadiga','TMD','FadFisica']].mean().reset_index().merge(F,on='ID',how='left')
# D1->D7 change per athlete
dm=h.groupby(['ID','dia'])[['Vigor','Fadiga','TMD','FadFisica']].mean().reset_index()
def d17(col):
    p=dm.pivot(index='ID',columns='dia',values=col); return (p[7]-p[1]).rename('d_'+col)
D=pd.concat([d17(c) for c in ['Vigor','Fadiga','TMD','FadFisica']],axis=1).reset_index().merge(F,on='ID',how='left')
def reg(x,y):
    m=pd.DataFrame({'x':x,'y':y}).dropna()
    if len(m)<5: return None
    lr=stats.linregress(m.x,m.y); rho,pr=stats.spearmanr(m.x,m.y)
    return dict(slope=float(lr.slope),intercept=float(lr.intercept),r=float(lr.rvalue),r2=float(lr.rvalue**2),
        p=float(lr.pvalue),rho=float(rho),rho_p=float(pr),n=int(len(m)),se=float(lr.stderr))
R={'pv':{}}
R['desc']=dict(pvini_m=float(WK.PVini.mean()),pvini_sd=float(WK.PVini.std(ddof=1)),
    pv_m=float(WK.PV.mean()),pv_sd=float(WK.PV.std(ddof=1)),
    dpv_m=float(WK.dPV.mean()),dpv_sd=float(WK.dPV.std(ddof=1)),
    pvini_min=float(WK.PVini.min()),pvini_max=float(WK.PVini.max()))
# weekly regressions vs PVini (T-CAR1) and PV (T-CAR2)
for col in ['Vigor','Fadiga','TMD','FadFisica']:
    R['pv']['wk_'+col]=dict(TCAR1=reg(WK.PVini,WK[col]),TCAR2=reg(WK.PV,WK[col]))
# change regressions
for col in ['Vigor','Fadiga','TMD','FadFisica']:
    R['pv']['d_'+col]=dict(TCAR1=reg(D.PVini,D['d_'+col]),TCAR2=reg(D.PV,D['d_'+col]))
# terciles by PVini -> weekly fatigue/vigor/tmd + D1->D7 fatigue change
WK['terc']=pd.qcut(WK.PVini,3,labels=['Baixa','Média','Alta'])
DM=D.merge(WK[['ID','terc']],on='ID')
terc={}
for k,g in WK.groupby('terc'):
    gd=DM[DM.terc==k]
    terc[str(k)]=dict(n=int(len(g)),pv=float(g.PVini.mean()),
        Vigor=float(g.Vigor.mean()),Fadiga=float(g.Fadiga.mean()),TMD=float(g.TMD.mean()),FadFisica=float(g.FadFisica.mean()),
        dFadiga=float(gd.d_Fadiga.mean()),dVigor=float(gd.d_Vigor.mean()))
R['terc']=terc
# Kruskal across terciles for weekly fatigue
gg=[WK[WK.terc==k]['Fadiga'].values for k in ['Baixa','Média','Alta']]
Hk,pk=stats.kruskal(*gg); R['terc_kruskal_fad']=dict(H=float(Hk),p=float(pk))
gv=[WK[WK.terc==k]['FadFisica'].values for k in ['Baixa','Média','Alta']]
Hk2,pk2=stats.kruskal(*gv); R['terc_kruskal_fadfis']=dict(H=float(Hk2),p=float(pk2))
# save merged frames for figures
WK.to_csv('pv_wk.csv',index=False); D.to_csv('pv_d17.csv',index=False)
json.dump(R,open('pv_stats.json','w'),indent=1,ensure_ascii=False)
print('PV desc: T-CAR1 %.1f±%.1f | T-CAR2 %.1f±%.1f | dPV %.1f±%.1f km/h'%(R['desc']['pvini_m'],R['desc']['pvini_sd'],R['desc']['pv_m'],R['desc']['pv_sd'],R['desc']['dpv_m'],R['desc']['dpv_sd']))
print('\nWeekly regression vs T-CAR1 (PVini):')
for col in ['Vigor','Fadiga','TMD','FadFisica']:
    a=R['pv']['wk_'+col]['TCAR1']; print('  %-10s β=%+.2f R²=%.2f ρ=%+.2f p=%.3f'%(col,a['slope'],a['r2'],a['rho'],a['rho_p']))
print('\nD1->D7 change regression vs T-CAR1:')
for col in ['Vigor','Fadiga']:
    a=R['pv']['d_'+col]['TCAR1']; print('  d_%-8s β=%+.2f R²=%.2f ρ=%+.2f p=%.3f'%(col,a['slope'],a['r2'],a['rho'],a['rho_p']))
print('\nTerciles (T-CAR1) weekly Fadiga BRUMS:',{k:round(v['Fadiga'],2) for k,v in terc.items()},'Kruskal p=%.3f'%pk)
print('Terciles FadFisica:',{k:round(v['FadFisica'],2) for k,v in terc.items()},'Kruskal p=%.3f'%pk2)
