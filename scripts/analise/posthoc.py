import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from itertools import combinations
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv'); hr=pd.read_csv(f'{SC}/hr_series.csv')
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

def holm(pv):
    pv=np.asarray(pv); o=np.argsort(pv); adj=np.empty_like(pv); m=len(pv); run=0
    for rank,i in enumerate(o):
        run=max(run,(m-rank)*pv[i]); adj[i]=min(run,1)
    return adj

def posthoc_days(v, days=range(1,8)):
    d=hum[['ID','dia',v]].dropna().rename(columns={v:'y'}); d['dia']=d['dia'].astype(int)
    m=smf.mixedlm('y~C(dia)',d,groups=d['ID']).fit(reml=False)
    params=m.params; cov=m.cov_params()
    # EMM per day: day1=intercept; dayj=intercept+coef
    def coef(j): return 0.0 if j==1 else params.get(f'C(dia)[T.{j}]',0.0)
    emm={j: params['Intercept']+coef(j) for j in days}
    dfres=int(m.nobs - len(params))
    k=len(list(days))
    contrasts=[]
    for a,b in combinations(days,2):
        # diff EMM_b - EMM_a = coef(b)-coef(a); var from cov of the two coefs
        na=f'C(dia)[T.{a}]'; nb=f'C(dia)[T.{b}]'
        va=cov.loc[na,na] if na in cov.index else 0.0
        vb=cov.loc[nb,nb] if nb in cov.index else 0.0
        cab=cov.loc[na,nb] if (na in cov.index and nb in cov.index) else 0.0
        diff=coef(b)-coef(a); se=np.sqrt(max(va+vb-2*cab,1e-12))
        t=diff/se; praw=2*stats.t.sf(abs(t),dfres)
        # Tukey: q=|t|*sqrt(2); p via studentized range
        q=abs(t)*np.sqrt(2)
        try: ptuk=stats.studentized_range.sf(q,k,dfres)
        except Exception: ptuk=np.nan
        contrasts.append([a,b,diff,se,t,praw,ptuk])
    C=pd.DataFrame(contrasts,columns=['a','b','diff','se','t','praw','ptukey'])
    C['pholm']=holm(C['praw'].values)
    return m, emm, C

p("="*74); p("POST HOC — comparacoes par a par entre dias (EMM do modelo misto)"); p("="*74)
for v,lab in [('FadFisica','Fadiga fisica'),('Vigor','Vigor'),('Fadiga','Fadiga BRUMS'),('TMD','TMD')]:
    m,emm,C=posthoc_days(v)
    p(f"\n### {lab} — EMM por dia: "+"  ".join(f"D{j}={emm[j]:.2f}" for j in range(1,8)))
    sig=C[C['ptukey']<0.05].sort_values('ptukey')
    p(f"  Pares significativos (Tukey p<0,05): {len(sig)} de 21")
    for _,r in sig.iterrows():
        p(f"    D{int(r.a)} vs D{int(r.b)}: Δ={r['diff']:+.2f}  t={r.t:+.2f}  p_Tukey={r.ptukey:.4f}  p_Holm={r.pholm:.4f}")
    # focused: each day vs baseline D1
    p(f"  -- vs baseline (D1):")
    for _,r in C[C.a==1].iterrows():
        star='*' if r.ptukey<0.05 else ' '
        p(f"    D1 vs D{int(r.b)}: Δ={r['diff']:+.2f}  p_Tukey={r.ptukey:.3f}{star}")

# ---- POST HOC internal load sessions (FC pico, PSE) ----
p("\n"+"="*74); p("POST HOC — carga interna entre sessoes de HIIT (S1/S2/S3, pareado)"); p("="*74)
for metric in ['HRpico','PSE']:
    piv=hr[hr.sessao.isin(['S1','S2','S3'])].pivot_table(index='nome',columns='sessao',values=metric)
    piv=piv.dropna()
    p(f"\n### {metric}  medias: S1={piv.S1.mean():.2f} S2={piv.S2.mean():.2f} S3={piv.S3.mean():.2f} (n={len(piv)})")
    pairs=[('S1','S2'),('S2','S3'),('S1','S3')]; praws=[]; info=[]
    for a,b in pairs:
        t,pr=stats.ttest_rel(piv[b],piv[a]); w=stats.wilcoxon(piv[b],piv[a]).pvalue
        d=(piv[b]-piv[a]); dz=d.mean()/d.std(ddof=1); praws.append(pr); info.append((a,b,d.mean(),dz,pr,w))
    padj=holm(praws)
    for (a,b,dm,dz,pr,w),pa in zip(info,padj):
        star='*' if pa<0.05 else ' '
        p(f"    {a} vs {b}: Δ={dm:+.2f} dz={dz:+.2f} p={pr:.3f} p_Holm={pa:.3f} pWilcox={w:.3f}{star}")

open(f'{SC}/res_posthoc.txt','w').write('\n'.join(out)); print("\n[saved res_posthoc.txt]")
