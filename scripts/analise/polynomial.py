import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv')
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

# orthogonal polynomials for days 1..7
def ortho_poly(x,degree):
    x=np.asarray(x,float); X=np.vander(x,degree+1,increasing=True)
    Q,R=np.linalg.qr(X); Q=Q[:,1:]  # drop intercept
    # sign convention: linear increasing
    for j in range(Q.shape[1]):
        if np.corrcoef(Q[:,j], x**(j+1))[0,1]<0: Q[:,j]*=-1
    return Q
DAYS=np.arange(1,8); P=ortho_poly(DAYS,6)   # 7x6
polymap={d:P[i] for i,d in enumerate(DAYS)}
names=['lin','quad','cub','quart','quint','sext']

# =============== 1. ORTHOGONAL POLYNOMIAL TREND ANALYSIS (mixed model) ===============
p("="*76); p("1. ANALISE DE TENDENCIA POR POLINOMIOS ORTOGONAIS (efeito do dia, modelo misto)"); p("="*76)
p("   Cada termo testa uma componente da FORMA da trajetoria (7 dias -> ate 6a ordem)")
for v,lab in [('FadFisica','Fadiga fisica'),('Vigor','Vigor'),('Fadiga','Fadiga BRUMS'),('TMD','TMD')]:
    d=hum[['ID','dia',v]].dropna().rename(columns={v:'y'}).copy()
    for j,nm in enumerate(names):
        d[nm]=d['dia'].map(lambda dd: polymap[int(dd)][j])
    m=smf.mixedlm('y~'+'+'.join(names),d,groups=d['ID']).fit(reml=False)
    p(f"\n### {lab}")
    for nm in names:
        b=m.params[nm]; pv=m.pvalues[nm]; star='***' if pv<0.001 else '**' if pv<0.01 else '*' if pv<0.05 else ''
        p(f"    {nm:6s} beta={b:+7.3f}  p={pv:.4f} {star}")
    sig=[nm for nm in names if m.pvalues[nm]<0.05]
    p(f"    -> componentes significativas: {sig if sig else 'nenhuma'}")

# =============== 2. POLYNOMIAL GROWTH MODELS (random slopes) by AIC/LRT ===============
p("\n"+"="*76); p("2. CRESCIMENTO POLINOMIAL MULTINIVEL (inclinacoes aleatorias; AIC e LRT)"); p("="*76)
p("   Compara ordens 1(linear)/2(quadratico)/3(cubico) com efeitos aleatorios por atleta")
def growth(v):
    d=hum[['ID','dia',v]].dropna().rename(columns={v:'y'}).copy()
    d['t']=(d['dia']-4)/1.0  # center at mid-week
    d['t2']=d['t']**2; d['t3']=d['t']**3
    res={}
    # order1: random intercept+slope
    m1=smf.mixedlm('y~t',d,groups=d.ID,re_formula='~t').fit(reml=False)
    m2=smf.mixedlm('y~t+t2',d,groups=d.ID,re_formula='~t').fit(reml=False)
    m3=smf.mixedlm('y~t+t2+t3',d,groups=d.ID,re_formula='~t').fit(reml=False)
    return m1,m2,m3
def lrt(a,b):  # b nested-bigger
    stat=2*(b.llf-a.llf); df=b.df_modelwc-a.df_modelwc
    return stat, stats.chi2.sf(stat,max(df,1)), df
for v,lab in [('TMD','TMD'),('FadFisica','Fadiga fisica'),('Vigor','Vigor')]:
    m1,m2,m3=growth(v)
    p(f"\n### {lab}")
    p(f"    AIC: linear={m1.aic:.1f}  quadratico={m2.aic:.1f}  cubico={m3.aic:.1f}")
    s2,p2,_=lrt(m1,m2); s3,p3,_=lrt(m2,m3)
    p(f"    LRT quad vs lin: chi2={s2:.2f} p={p2:.4f} | cub vs quad: chi2={s3:.2f} p={p3:.4f}")
    best=[('linear',m1.aic),('quadratico',m2.aic),('cubico',m3.aic)]
    bn=min(best,key=lambda x:x[1])[0]
    # report coefficients of best
    mb={'linear':m1,'quadratico':m2,'cubico':m3}[bn]
    coefs=', '.join(f"{k}={mb.params[k]:+.2f}(p={mb.pvalues[k]:.3f})" for k in mb.params.index if k in ['t','t2','t3'])
    p(f"    -> melhor por AIC: {bn}; coefs: {coefs}")

# =============== 3. CONTRASTES ADICIONAIS ===============
p("\n"+"="*76); p("3a. HIIT vs TECNICO-TATICO — pares de dias (por atleta, Holm)"); p("="*76)
def holm(pv):
    pv=np.asarray(pv,dtype=float); o=np.argsort(pv); adj=np.empty(len(pv)); m=len(pv); run=0.0
    for r,i in enumerate(o): run=max(run,(m-r)*pv[i]); adj[i]=min(run,1)
    return adj
hiit=[2,4,7]; tt=[3,5,6]
for v,lab in [('TMD','TMD'),('FadFisica','Fadiga fisica'),('Vigor','Vigor')]:
    pairs=[(h,t) for h in hiit for t in tt]; praws=[]; info=[]
    for h,t in pairs:
        a=hum[hum.dia==h].groupby('ID')[v].mean(); b=hum[hum.dia==t].groupby('ID')[v].mean()
        com=a.index.intersection(b.index); da=a.loc[com].values; db=b.loc[com].values
        rr=stats.ttest_rel(da,db); pv=float(np.ravel(rr.pvalue)[0]); praws.append(pv); info.append((h,t,float((da-db).mean()),pv))
    padj=holm(praws)
    nsig=sum(pa<0.05 for pa in padj)
    p(f"  {lab:12s}: {nsig}/9 pares HIIT-TT significativos (Holm).  "+
      "; ".join(f"D{h}vD{t}:Δ={dm:+.1f}{'*' if pa<0.05 else ''}" for (h,t,dm,pv),pa in zip(info,padj)))

p("\n=== 3b. PRE->POS dentro de cada dia de treino (agregado por atleta, FDR) ===")
def fdr(pv):
    pv=np.asarray(pv); o=np.argsort(pv); r=np.empty(len(pv)); r[o]=np.arange(1,len(pv)+1)
    q=pv*len(pv)/r; qs=q[o][::-1]; qs=np.minimum.accumulate(qs)[::-1]; adj=np.empty(len(pv)); adj[o]=qs
    return np.clip(adj,0,1)
for v,lab in [('FadFisica','Fadiga fisica'),('TMD','TMD'),('Vigor','Vigor')]:
    praws=[]; info=[]
    for dia in [2,3,4,5,6,7]:
        per=[]
        for aid,g in hum[hum.dia==dia].groupby('ID'):
            g=g.sort_values('seq'); pre=g[g.momento=='pre'][v]; pos=g[g.momento=='pos'][v]
            if len(pre) and len(pos) and pd.notna(pre.iloc[0]) and pd.notna(pos.iloc[0]): per.append(pos.iloc[0]-pre.iloc[0])
        per=np.array(per)
        if len(per)>3 and per.std()>0:
            t,pv=stats.ttest_1samp(per,0); praws.append(pv); info.append((dia,per.mean(),per.mean()/per.std(ddof=1),pv))
    padj=fdr([x[3] for x in info])
    p(f"  {lab:12s}: "+"  ".join(f"D{d}:dz={dz:+.2f}{'*' if pa<0.05 else ''}" for (d,dm,dz,pv),pa in zip(info,padj)))

open(f'{SC}/res_poly.txt','w').write('\n'.join(out)); print("\n[saved res_poly.txt]")
