import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats

h=pd.read_csv('hum_prof.csv'); p=pd.read_csv('phys.csv')
p=p.rename(columns={'TCAR_PV_ini':'PV'})
COV=['PV','massa','pGordura','estatura','CMJ_ini','Baker_ini']
days=np.arange(1,8)
CORE=['FadFisica','Vigor','FadMental','TMD','Fadiga']

# daily athlete means (collapse pre/mid/pos)
dm=h.groupby(['ID','dia'])[CORE+['ice_idx']].mean().reset_index()

def piv(v): return dm.pivot(index='ID',columns='dia',values=v)

# ---------- per-athlete outcome features ----------
rows=[]
for aid,g in dm.groupby('ID'):
    g=g.set_index('dia').reindex(days)
    d1={v:g.loc[1,v] for v in CORE+['ice_idx']}
    d7={v:g.loc[7,v] for v in CORE+['ice_idx']}
    # linear slope across the week (least squares) per var
    def slope(v):
        y=g[v].values; m=~np.isnan(y)
        return stats.linregress(days[m],y[m]).slope if m.sum()>2 else np.nan
    rows.append(dict(ID=aid,
        wk_FadFis=g['FadFisica'].mean(), wk_Vigor=g['Vigor'].mean(),
        wk_FadMen=g['FadMental'].mean(), wk_TMD=g['TMD'].mean(),
        ice_mean=g['ice_idx'].mean(), ice_D1=d1['ice_idx'], ice_D7=d7['ice_idx'],
        vig_D1=d1['Vigor'], vig_D7=d7['Vigor'], vig_drop=d1['Vigor']-d7['Vigor'],
        fis_D1=d1['FadFisica'], fis_D7=d7['FadFisica'], fis_accum=d7['FadFisica']-d1['FadFisica'],
        men_accum=d7['FadMental']-d1['FadMental'], tmd_accum=d7['TMD']-d1['TMD'],
        slope_fis=slope('FadFisica'), slope_vig=slope('Vigor'), slope_tmd=slope('TMD')))
F=pd.DataFrame(rows).merge(p[['ID','pos']+COV],on='ID')

# overnight recovery (pos day d -> pre day d+1): recover fatigue (drop) & vigor (rebound)
rec=[]
for aid,g in h.groupby('ID'):
    gg=g.pivot_table(index='dia',columns='momento',values=['FadFisica','Vigor'],aggfunc='mean')
    fr=[]; vr=[]
    for d in range(1,7):
        try:
            fr.append(gg.loc[d,('FadFisica','pos')]-gg.loc[d+1,('FadFisica','pre')])  # fatigue shed overnight
            vr.append(gg.loc[d+1,('Vigor','pre')]-gg.loc[d,('Vigor','pos')])          # vigor regained overnight
        except Exception: pass
    rec.append(dict(ID=aid,rec_fis=np.nanmean(fr) if fr else np.nan,rec_vig=np.nanmean(vr) if vr else np.nan))
F=F.merge(pd.DataFrame(rec),on='ID')

def sr(a,b):
    m=F[[a,b]].dropna(); r,p_=stats.spearmanr(m[a],m[b]); return float(r),float(p_),len(m)

# ================= 1) CORRELATION MATRIX covariate x outcome =================
OUT_VARS=[('wk_FadFis','Fadiga física (média)'),('fis_accum','Acúmulo fadiga física D1→D7'),
    ('vig_drop','Queda de vigor D1→D7'),('wk_TMD','PTH/TMD (média)'),
    ('tmd_accum','Acúmulo PTH D1→D7'),('ice_mean','Índice iceberg (média)'),
    ('rec_fis','Recuperação noturna (fadiga)'),('rec_vig','Recuperação noturna (vigor)'),
    ('slope_fis','Inclinação fadiga física')]
COR={}
for cv in COV:
    COR[cv]={}
    for ov,lab in OUT_VARS:
        r,pp,n=sr(cv,ov); COR[cv][ov]=dict(r=r,p=pp,n=n)

# ================= 2) ALLOMETRIC: which body descriptor scales fatigue =================
# log-log fatigue accumulation vs mass, PV, pGordura (offset to positive)
ALLO={}
for cv in ['massa','PV','pGordura']:
    m=F[[cv,'wk_FadFis']].dropna(); x=np.log(m[cv]); y=np.log(m['wk_FadFis']+1e-6)
    lr=stats.linregress(x,y); ALLO[cv]=dict(b=float(lr.slope),r2=float(lr.rvalue**2),p=float(lr.pvalue))

# ================= 3) LOGISTIC / ROC: PV vs pGordura as classifier of high accumulator =================
def auc(score,label):  # Mann-Whitney U / (n1 n2)
    s=np.asarray(score); y=np.asarray(label); pos=s[y==1]; neg=s[y==0]
    if len(pos)==0 or len(neg)==0: return np.nan
    U=stats.mannwhitneyu(pos,neg).statistic; return float(U/(len(pos)*len(neg)))
# label: high accumulated physical fatigue = top tercile of fis_accum
thr=F['fis_accum'].quantile(2/3); F['hi_accum']=(F['fis_accum']>=thr).astype(int)
ROC={}
for cv,sign in [('PV',-1),('pGordura',1),('massa',1),('CMJ_ini',-1),('Baker_ini',-1)]:
    m=F[[cv,'hi_accum']].dropna(); ROC[cv]=dict(auc=auc(sign*m[cv],m['hi_accum']),n=int(len(m)))
# simple univariate logistic PV -> P(hi_accum), report OR & pseudo-threshold
def logit_fit(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float); b0,b1=0.,0.
    for _ in range(200):
        z=b0+b1*x; pr=1/(1+np.exp(-z)); W=pr*(1-pr)+1e-9
        g0=np.sum(y-pr); g1=np.sum((y-pr)*x)
        h00=-np.sum(W); h01=-np.sum(W*x); h11=-np.sum(W*x*x)
        det=h00*h11-h01*h01
        b0-=( h11*g0-h01*g1)/det; b1-=(-h01*g0+h00*g1)/det
    return b0,b1
mm=F[['PV','hi_accum']].dropna(); b0,b1=logit_fit(mm['PV'],mm['hi_accum'])
LOG=dict(b0=float(b0),b1=float(b1),OR=float(np.exp(b1)),thr50=float(-b0/b1) if b1!=0 else None)

# ================= 4) POSITION =================
POS={}
for pos,g in F.groupby('pos'):
    POS[pos]=dict(n=int(len(g)),PV=float(g.PV.mean()),massa=float(g.massa.mean()),
        pGordura=float(g.pGordura.mean()),wk_FadFis=float(g.wk_FadFis.mean()),
        fis_accum=float(g.fis_accum.mean()),vig_drop=float(g.vig_drop.mean()),
        ice_mean=float(g.ice_mean.mean()),rec_fis=float(g.rec_fis.mean()))
# Kruskal across positions for key outcomes
def kw(v):
    grp=[g[v].dropna().values for _,g in F.groupby('pos') if g[v].notna().sum()>0]
    return float(stats.kruskal(*grp).pvalue) if len(grp)>1 else np.nan
POS_KW={v:kw(v) for v in ['wk_FadFis','fis_accum','vig_drop','PV','pGordura','ice_mean']}

# ================= 5) ICEBERG athletes =================
# iceberg-dominant = top tercile of mean iceberg index
ithr=F['ice_mean'].quantile(2/3); F['iceberg_grp']=np.where(F['ice_mean']>=ithr,'Iceberg alto',
    np.where(F['ice_mean']<=F['ice_mean'].quantile(1/3),'Iceberg baixo','Médio'))
ICE={}
for grp in ['Iceberg alto','Iceberg baixo']:
    g=F[F.iceberg_grp==grp]
    ICE[grp]=dict(n=int(len(g)),PV=float(g.PV.mean()),pGordura=float(g.pGordura.mean()),
        massa=float(g.massa.mean()),wk_FadFis=float(g.wk_FadFis.mean()),
        fis_accum=float(g.fis_accum.mean()),vig_D1=float(g.vig_D1.mean()),
        vig_D7=float(g.vig_D7.mean()),vig_drop=float(g.vig_drop.mean()),
        rec_fis=float(g.rec_fis.mean()),rec_vig=float(g.rec_vig.mean()),
        wk_Vigor=float(g.wk_Vigor.mean()))
# Mann-Whitney iceberg alto vs baixo
ga=F[F.iceberg_grp=='Iceberg alto']; gb=F[F.iceberg_grp=='Iceberg baixo']
ICE_MW={}
for v in ['PV','pGordura','fis_accum','vig_drop','vig_D1','vig_D7','rec_fis','wk_FadFis']:
    a=ga[v].dropna(); b=gb[v].dropna()
    ICE_MW[v]=float(stats.mannwhitneyu(a,b).pvalue) if len(a)>0 and len(b)>0 else np.nan
# correlation iceberg index x PV, x pGordura
ICE_COR=dict(ice_PV=sr('ice_mean','PV'),ice_pG=sr('ice_mean','pGordura'),
    ice_vigdrop=sr('ice_mean','vig_drop'),ice_recfis=sr('ice_mean','rec_fis'),
    ice_accum=sr('ice_mean','fis_accum'))
# "começa bem e termina mal": correlation of D1 vigor with vigor drop
START=dict(vigD1_drop=sr('vig_D1','vig_drop'), ice_vigD1=sr('ice_mean','vig_D1'), ice_vigD7=sr('ice_mean','vig_D7'))

RES=dict(COR=COR,ALLO=ALLO,ROC=ROC,LOG=LOG,POS=POS,POS_KW=POS_KW,ICE=ICE,
    ICE_MW=ICE_MW,ICE_COR=ICE_COR,START=START,
    n=int(len(F)), thr_accum=float(thr), ithr=float(ithr))
json.dump(RES,open('ajuste_gordura.json','w'),indent=1)
F.to_csv('ajuste_features.csv',index=False)

# ---------- console summary ----------
print('n atletas =',len(F))
print('\n== 1) CORRELAÇÃO Spearman covariável × desfecho (r [p]) ==')
print('%-12s'%'', *['%-16s'%ov[:16] for ov,_ in OUT_VARS[:6]])
for cv in COV:
    print('%-12s'%cv, *['%+.2f[%.2f]     '%(COR[cv][ov]['r'],COR[cv][ov]['p'])[:16] for ov,_ in OUT_VARS[:6]])
print('\n== 2) ALOMETRIA (expoente b, R², p) fadiga~descritor ==')
for k,v in ALLO.items(): print('  %-9s b=%+.2f R²=%.2f p=%.3f'%(k,v['b'],v['r2'],v['p']))
print('\n== 3) ROC (AUC classificar acúmulo alto de fadiga) ==')
for k,v in ROC.items(): print('  %-9s AUC=%.2f (n=%d)'%(k,v['auc'],v['n']))
print('  Logística PV: OR=%.3f/km·h  limiar50%%=%.1f km/h'%(LOG['OR'],LOG['thr50']))
print('\n== 4) POSIÇÃO ==')
print('%-9s %4s %6s %6s %6s %8s %8s %8s'%('pos','n','PV','massa','%G','wkFadF','accum','vigDrop'))
for k,v in POS.items(): print('%-9s %4d %6.1f %6.1f %6.1f %8.2f %8.2f %8.2f'%(k,v['n'],v['PV'],v['massa'],v['pGordura'],v['wk_FadFis'],v['fis_accum'],v['vig_drop']))
print('  Kruskal p:',{k:round(v,3) for k,v in POS_KW.items()})
print('\n== 5) ICEBERG alto vs baixo ==')
for k,v in ICE.items(): print('  %-13s n=%d PV=%.1f %%G=%.1f accum=%+.2f vigDrop=%+.2f recFis=%+.2f vigD1=%.1f vigD7=%.1f'%(k,v['n'],v['PV'],v['pGordura'],v['fis_accum'],v['vig_drop'],v['rec_fis'],v['vig_D1'],v['vig_D7']))
print('  MW p:',{k:round(v,3) for k,v in ICE_MW.items()})
print('  ice×PV r=%+.2f[p=%.3f]  ice×%%G r=%+.2f[p=%.3f]  ice×vigDrop r=%+.2f[p=%.3f]  ice×recFis r=%+.2f[p=%.3f]'%(
    *ICE_COR['ice_PV'][:2],*ICE_COR['ice_pG'][:2],*ICE_COR['ice_vigdrop'][:2],*ICE_COR['ice_recfis'][:2]))
print('  começa bem/termina mal: vigD1×vigDrop r=%+.2f[p=%.3f]'%START['vigD1_drop'][:2])
