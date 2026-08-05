import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
from scipy import stats
hum=pd.read_csv('humor.csv'); fc=pd.read_csv('fc_sessions.csv')
phys=pd.read_csv('phys.csv')
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)
rng=np.random.default_rng(11)

# ===== SESSION-LEVEL MOOD (HIIT days 2,4,7 = S1,S2,S3) =====
p("=== PROGRESSAO DO HUMOR ENTRE AS 3 SESSOES DE HIIT (D2->D4->D7) ===")
sess_day={ 'S1':2,'S2':4,'S3':7 }
# per athlete-day mood on HIIT days
hd=hum[hum.dia.isin([2,4,7])].groupby(['ID','dia'])[['TMD','Vigor','Fadiga','FadFisica']].mean().reset_index()
for v in ['TMD','Vigor','Fadiga','FadFisica']:
    m=hd.groupby('dia')[v].mean()
    p(f"  {v:10s} S1(D2)={m[2]:.2f}  S2(D4)={m[4]:.2f}  S3(D7)={m[7]:.2f}")
# progression slope (mixed): value ~ session order
hd['ord']=hd.dia.map({2:1,4:2,7:3})
import statsmodels.formula.api as smf
for v in ['TMD','Vigor','FadFisica']:
    d=hd[['ID','ord',v]].dropna().rename(columns={v:'y'})
    m=smf.mixedlm('y~ord',d,groups=d.ID).fit(reml=False)
    p(f"  slope/sessao {v:10s}={m.params['ord']:+.2f}  p={m.pvalues['ord']:.4f}")

# ===== INTERNAL LOAD PER SESSION (S1-S3 only, within window) =====
p("\n=== CARGA INTERNA POR SESSAO (S1-S3, dentro da janela) ===")
fcw=fc[fc.sessao.isin(['S1','S2','S3'])]
for s in ['S1','S2','S3']:
    g=fcw[fcw.sessao==s]
    p(f"  {s}: FC pico={g.FCpico.mean():.1f} bpm  HRR1'={g.HRR.mean():.1f}  PSE={g.PSE.mean():.2f}")
fr=stats.friedmanchisquare(*[fcw[fcw.sessao==s].sort_values('ID').FCpico.values for s in ['S1','S2','S3']])
p(f"  Friedman FC pico S1-S3: chi2={fr.statistic:.2f} p={fr.pvalue:.4f}")

# ===== PSYCHOPHYSIOLOGICAL COUPLING (within-athlete FC x mood across 3 sessions) =====
p("\n=== ACOPLAMENTO FC x HUMOR (intra-atleta, 3 sessoes) — rmcorr ===")
fcw2=fcw.copy(); fcw2['dia']=fcw2.sessao.map(sess_day)
J=fcw2.merge(hd,on=['ID','dia'],how='inner')
def rmcorr(df, x, y, subj='ID'):
    # ANCOVA-based repeated measures correlation (Bakdash & Marusich)
    d=df[[subj,x,y]].dropna()
    import statsmodels.formula.api as smf
    d=d.rename(columns={x:'X',y:'Y'})
    m=smf.ols('Y~C(%s)+X'%subj,data=d).fit()
    b=m.params['X']
    # sign * sqrt(partial eta2)
    from statsmodels.stats.anova import anova_lm
    aov=anova_lm(m,typ=1)
    ss_x=aov.loc['X','sum_sq']; ss_e=aov.loc['Residual','sum_sq']
    r=np.sign(b)*np.sqrt(ss_x/(ss_x+ss_e))
    dfe=int(m.df_resid)
    return r,dfe,len(d)
for y in ['Vigor','TMD','FadFisica']:
    try:
        r,dfe,n=rmcorr(J,'FCpico',y)
        p(f"  FC pico x {y:9s}: rmcorr={r:+.2f} (gl={dfe}, n={n})")
    except Exception as e:
        p(f"  FC pico x {y}: FAIL {e}")
# PSE x mood
for y in ['TMD','FadFisica']:
    try:
        r,dfe,n=rmcorr(J,'PSE',y); p(f"  PSE     x {y:9s}: rmcorr={r:+.2f} (gl={dfe}, n={n})")
    except Exception as e: p(f"  PSE x {y}: FAIL")

# ===== RELIABLE CHANGE INDEX (D1 -> D7) =====
p("\n=== MUDANCA INDIVIDUAL CONFIAVEL (RCI, D1->D7) ===")
# SEM per variable from omega reliability & SD
rel={'FadFisica':0.87,'Fadiga':0.87,'Vigor':0.79,'TMD':0.90}
for v in ['FadFisica','Fadiga','Vigor','TMD']:
    d1=hum[hum.dia==1].groupby('ID')[v].mean(); d7=hum[hum.dia==7].groupby('ID')[v].mean()
    j=pd.concat([d1,d7],axis=1,keys=['d1','d7']).dropna()
    sd=hum[v].std(); sem=sd*np.sqrt(1-rel[v]); sdiff=np.sqrt(2)*sem; mdc=1.96*sdiff
    z=(j.d7-j.d1)/sdiff
    inc=(z>1.96).sum(); dec=(z<-1.96).sum(); nc=len(j)-inc-dec
    p(f"  {v:10s} n={len(j)} MDC95={mdc:.2f}  aumento_confiavel={inc}  sem_mudanca={nc}  reducao={dec}")

# ===== INTRA-INDIVIDUAL VARIABILITY (iSD, MSSD) =====
p("\n=== VARIABILIDADE INTRA-INDIVIDUAL (iSD, MSSD) ===")
for v in ['TMD','Vigor','Fadiga','Tensao','Confusao']:
    iSDs=[]; mssds=[]
    for aid,g in hum.groupby('ID'):
        g=g.sort_values(['dia','seq']); s=g[v].dropna().values
        if len(s)>=3:
            iSDs.append(np.std(s,ddof=1)); mssds.append(np.mean(np.diff(s)**2))
    p(f"  {v:10s} iSD={np.mean(iSDs):.2f}  MSSD={np.mean(mssds):.1f}")

# ===== ETM vs SWC (Hopkins usefulness) =====
p("\n=== ERRO TIPICO DA MEDIDA vs SWC (utilidade) ===")
for v in ['FadFisica','Fadiga','Vigor','TMD']:
    # typical error from test-retest of consecutive days within athlete
    diffs=[]
    for aid,g in hum.groupby('ID'):
        gg=g.groupby('dia')[v].mean().sort_index().values
        diffs+=list(np.diff(gg))
    te=np.std(diffs,ddof=1)/np.sqrt(2)
    swc=0.2*hum.groupby('ID')[v].mean().std()
    p(f"  {v:10s} ETM={te:.2f} ({100*te/hum[v].mean():.0f}%)  SWC={swc:.2f}  {'util' if te<swc else 'marginal'}")

# ===== BASELINE FITNESS AS COVARIATE (pre-week T-CAR 15/04) - moderation only =====
p("\n=== APTIDAO PRE-SEMANA (covariavel de base) x resposta da semana ===")
wk=hum.groupby('ID')[['FadFisica','TMD','Vigor']].mean()
mo=wk.join(phys.set_index('ID')[['TCAR_PV_ini']]).dropna()
for v in ['FadFisica','TMD']:
    r=stats.spearmanr(mo.TCAR_PV_ini,mo[v])
    p(f"  T-CAR base x {v:9s} (media semana): rho={r.correlation:+.2f} p={r.pvalue:.3f}")

open('res_a3w.txt','w').write('\n'.join(out)); print("\n[saved res_a3w.txt]")
