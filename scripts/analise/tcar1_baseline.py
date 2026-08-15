import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, openpyxl, re
from scipy import stats
_isid=lambda x: bool(re.fullmatch(r'A\d{1,2}',str(x).strip()))

UP='/root/.claude/uploads/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/'
# ---------- 1) T-CAR 1 per athlete (already anonymized A-IDs in this sheet) ----------
wb=openpyxl.load_workbook(UP+'789b3ee8-Avalia__es_Handebol_S_o_Jos__2024.xlsx',read_only=True,data_only=True)
ws=wb['T-CAR Unificado']; rows=list(ws.iter_rows(values_only=True))
tc=[]
for r in rows[4:]:
    if r[0] and _isid(r[0]):
        def f(x):
            try: return float(x)
            except: return np.nan
        tc.append(dict(ID=str(r[0]).strip(), pos=r[2], reps_ini=f(r[3]), PV=f(r[9]), FCmax=f(r[11])))
TC=pd.DataFrame(tc)
# distance proxy: T-CAR (Carminatti) intermittent 12s efforts; distance covered ~ reps * effort distance.
# effort distance per rep = PV(m/s)*12s ; PV km/h -> m/s = PV/3.6 ; dist = reps * (PV/3.6) * 12
TC['dist']=TC['reps_ini']*(TC['PV']/3.6)*12.0

# ---------- 2) HIIT internal load per athlete (TRIMP Banister + session-RPE) ----------
fc=pd.read_csv('fc_sessions.csv'); hr=pd.read_csv('hr_series.csv')
fc=fc[fc.sessao.isin(['S1','S2','S3'])]; hr=hr[hr.sessao.isin(['S1','S2','S3'])]
name2id=fc.dropna(subset=['nome','ID']).drop_duplicates('nome').set_index('nome')['ID'].to_dict()
hr['ID']=hr['nome'].map(name2id)
# HRmax per athlete = max HRpico observed; HRrest assumed 60; D nominal 30 min (constant -> scale-invariant)
hrmax=hr.groupby('ID')['HRpico'].max().to_dict()
HRREST=60.0; D=30.0
def trimp_row(row):
    hm=hrmax.get(row['ID'],np.nan)
    if np.isnan(hm) or np.isnan(row['HRmean']): return np.nan
    hrr=(row['HRmean']-HRREST)/(hm-HRREST); hrr=min(max(hrr,0),1)
    return D*hrr*0.64*np.exp(1.92*hrr)
hr['TRIMP']=hr.apply(trimp_row,axis=1)
TR=hr.dropna(subset=['ID']).groupby('ID').agg(TRIMP=('TRIMP','mean'),HRmean=('HRmean','mean')).reset_index()
PSE=fc.groupby('ID').agg(PSE=('PSE','mean'),FCpico=('FCpico','mean'),HRR=('HRR','mean')).reset_index()

# ---------- 3) baseline (D1) psychological ----------
h=pd.read_csv('hum_prof.csv')
PSY=['Vigor','Fadiga','FadFisica','FadMental','TMD','Tensao','Depressao','Raiva','Confusao','ice_idx']
base=h[(h.dia==1)&(h.momento=='pre')]
miss=set(h.ID.unique())-set(base.ID.unique())
if miss:  # fall back to D1 mean for athletes lacking a D1 pre
    add=h[(h.dia==1)&(h.ID.isin(miss))].groupby('ID')[PSY].mean().reset_index()
    base=pd.concat([base[['ID']+PSY],add],ignore_index=True)
BASE=base[['ID']+PSY].groupby('ID').mean().reset_index()
BASE=BASE.rename(columns={c:'b_'+c for c in PSY})
# baseline iceberg profile flag: ice_idx>0 (vigor above the negative-mood cluster)
BASE['b_iceberg']=(BASE['b_ice_idx']>0).astype(int)

# weekly deterioration outcomes (secondary bridge)
dm=h.groupby(['ID','dia'])[['FadFisica','Vigor','TMD']].mean().reset_index()
def d17(v):
    p=dm.pivot(index='ID',columns='dia',values=v)
    return (p[7]-p[1]).rename('d_'+v)
WK=pd.concat([d17('FadFisica'),d17('Vigor'),d17('TMD')],axis=1).reset_index()

# ---------- merge ----------
F=TC.merge(TR,on='ID',how='left').merge(PSE,on='ID',how='left').merge(BASE,on='ID',how='left').merge(WK,on='ID',how='left')
F.to_csv('tcar1_features.csv',index=False)
PHYS=['PV','dist','FCmax','TRIMP','PSE']
def sr(a,b):
    m=F[[a,b]].dropna();
    if len(m)<6: return (np.nan,np.nan,len(m))
    r,p=stats.spearmanr(m[a],m[b]); return float(r),float(p),len(m)

# ===== A) correlation matrix phys x baseline psych =====
OUTB=[('b_Vigor','Vigor (base)'),('b_Fadiga','Fadiga (base)'),('b_FadFisica','Fad. física (base)'),
      ('b_FadMental','Fad. mental (base)'),('b_TMD','PTH/TMD (base)'),('b_ice_idx','Iceberg (base)')]
COR={ph:{ov:dict(zip(('r','p','n'),sr(ph,ov))) for ov,_ in OUTB} for ph in PHYS}

# ===== B) allometry: baseline physical fatigue ~ PV, dist =====
ALLO={}
for cv in ['PV','dist','TRIMP']:
    m=F[[cv,'b_FadFisica']].dropna();
    x=np.log(m[cv]); y=np.log(m['b_FadFisica']+1e-6); lr=stats.linregress(x,y)
    ALLO[cv]=dict(b=float(lr.slope),r2=float(lr.rvalue**2),p=float(lr.pvalue))

# ===== C) ROC/logistic: PV & TRIMP classify baseline iceberg =====
def auc(score,label):
    s=np.asarray(score,float); y=np.asarray(label); pos=s[y==1]; neg=s[y==0]
    if len(pos)==0 or len(neg)==0: return np.nan
    return float(stats.mannwhitneyu(pos,neg).statistic/(len(pos)*len(neg)))
ROC={}
for cv,sign in [('PV',1),('dist',1),('FCmax',1),('TRIMP',-1),('PSE',-1)]:
    m=F[[cv,'b_iceberg']].dropna(); ROC[cv]=dict(auc=auc(sign*m[cv],m['b_iceberg']),n=int(len(m)))

# ===== D) position =====
POS={}
for pos,g in F.groupby('pos'):
    POS[str(pos)]=dict(n=int(len(g)),PV=float(g.PV.mean()),dist=float(g.dist.mean()),TRIMP=float(g.TRIMP.mean()),
        b_Vigor=float(g.b_Vigor.mean()),b_FadFisica=float(g.b_FadFisica.mean()),b_ice=float(g.b_ice_idx.mean()))

# ===== E) secondary: do baseline phys predict weekly deterioration =====
SEC={ph:{ 'd_FadFisica':dict(zip(('r','p','n'),sr(ph,'d_FadFisica'))),
          'd_Vigor':dict(zip(('r','p','n'),sr(ph,'d_Vigor'))) } for ph in ['PV','dist','TRIMP']}

RES=dict(COR=COR,ALLO=ALLO,ROC=ROC,POS=POS,SEC=SEC,n=int(len(F)),
    means={k:float(F[k].mean()) for k in PHYS+['b_Vigor','b_FadFisica','b_TMD']},
    trimp_note='TRIMP Banister a partir da FC média das sessões de HIIT (S1-S3); HRrest=60, D=30min constantes (invariante de escala).')
json.dump(RES,open('tcar1_baseline.json','w'),indent=1)

print('n=',len(F),' | phys means:',{k:round(F[k].mean(),1) for k in PHYS})
print('\nA) CORRELAÇÃO fisiológico(T-CAR1/HIIT) × psicológico BASELINE  (ρ [p])')
print('%-8s'%'',*['%-18s'%l[:18] for _,l in OUTB])
for ph in PHYS:
    print('%-8s'%ph,*['%+.2f[%.2f]       '%(COR[ph][ov]['r'],COR[ph][ov]['p'])[:18] for ov,_ in OUTB])
print('\nB) ALOMETRIA fadiga física base ~ descritor (b,R²,p)')
for k,v in ALLO.items(): print('  %-6s b=%+.2f R²=%.2f p=%.3f'%(k,v['b'],v['r2'],v['p']))
print('\nC) ROC (AUC classificar perfil ICEBERG no baseline)')
for k,v in ROC.items(): print('  %-6s AUC=%.2f (n=%d)'%(k,v['auc'],v['n']))
print('\nD) POSIÇÃO');
for k,v in POS.items(): print('  %-8s n=%d PV=%.1f dist=%.0f TRIMP=%.1f | Vig=%.1f FadFis=%.1f ice=%+.2f'%(k,v['n'],v['PV'],v['dist'],v['TRIMP'],v['b_Vigor'],v['b_FadFisica'],v['b_ice']))
print('\nE) baseline fisiológico → deterioração semanal (ρ[p])')
for ph in ['PV','dist','TRIMP']:
    print('  %-6s ΔFadFís %+.2f[%.2f]  ΔVigor %+.2f[%.2f]'%(ph,SEC[ph]['d_FadFisica']['r'],SEC[ph]['d_FadFisica']['p'],SEC[ph]['d_Vigor']['r'],SEC[ph]['d_Vigor']['p']))
