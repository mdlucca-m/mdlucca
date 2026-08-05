import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
from scipy import stats
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_kmo, calculate_bartlett_sphericity
import statsmodels.formula.api as smf

it=pd.read_csv('items.csv'); hum=pd.read_csv('humor.csv')
items=list(it.columns[1:25])
subs={'Tensao':['Apavorado','Ansioso','Preocupado','Tenso'],
 'Depressao':['Deprimido','Desanimado','Triste','Infeliz'],
 'Raiva':['Irritado','Zangado','ComRaiva','MalHumorado'],
 'Vigor':['Animado','ComDisposição','ComEnergia','Alerta'],
 'Fadiga':['Esgotado','Exausto','Sonolento','Cansado'],
 'Confusao':['Confuso','Inseguro','Desorientado','Indeciso']}
X=it[items].dropna()
out=[]
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

# ---- KMO / Bartlett ----
kmo_all=calculate_kmo(X)[1]; chi,pval=calculate_bartlett_sphericity(X)
p(f"KMO={kmo_all:.3f}  Bartlett chi2={chi:.0f} p={pval:.2e}")

# ---- Parallel analysis (PCA eigenvalues, numpy) ----
Robs=np.corrcoef(X.values,rowvar=False)
ev=np.sort(np.linalg.eigvalsh(Robs))[::-1]
rng=np.random.default_rng(42); n,k=X.shape; sim=[]
for _ in range(500):
    R=rng.standard_normal((n,k))
    e=np.sort(np.linalg.eigvalsh(np.corrcoef(R,rowvar=False)))[::-1]; sim.append(e)
p95=np.percentile(np.array(sim),95,axis=0)
retain=int((ev>p95).sum())
p(f"Parallel analysis (PCA): retains {retain} factors; first7 eigen={np.round(ev[:7],2)}")
p(f"  random p95 first7={np.round(p95[:7],2)}  cum.var 6 fatores={100*ev[:6].sum()/k:.1f}%")

# ---- Model comparison: principal-factor extraction (numpy), RMSR of reproduced R ----
def princ_factor(R,nf,iters=50):
    Rr=R.copy(); h2=np.ones(len(R))
    for _ in range(iters):
        np.fill_diagonal(Rr,h2)
        w,v=np.linalg.eigh(Rr); idx=np.argsort(w)[::-1][:nf]
        L=v[:,idx]*np.sqrt(np.clip(w[idx],0,None))
        h2=np.clip((L**2).sum(1),0,1)
    return L
for nf in [1,2,6]:
    L=princ_factor(Robs,nf); Rimp=L@L.T; np.fill_diagonal(Rimp,1)
    resid=(Robs-Rimp)[np.triu_indices(k,1)]
    p(f"Principal-factor {nf}: RMSR={np.sqrt((resid**2).mean()):.3f}  commonvar={100*(L**2).sum()/k:.1f}%")

# ---- ICC(1,1) and ICC(1,k) ----
def icc11(long, val, grp):
    g=long.groupby(grp)[val]
    k=len(g); N=len(long.dropna(subset=[val]))
    ni=g.count(); n0=(N-(ni**2).sum()/N)/(k-1)
    grand=long[val].mean()
    msb=(ni*(g.mean()-grand)**2).sum()/(k-1)
    msw=long.groupby(grp)[val].apply(lambda s:((s-s.mean())**2).sum()).sum()/(N-k)
    icc=(msb-msw)/(msb+(n0-1)*msw)
    return icc, n0
p("\n-- ICC(1,1) 1 coleta  vs  ICC(1,7) media 7 dias (Spearman-Brown) --")
sb={}
for s in subs:
    icc,n0=icc11(hum, s if s in hum.columns else s, 'ID')
    icc7=7*icc/(1+6*icc)
    sb[s]=(icc,icc7); p(f"  {s:10s} ICC(1,1)={icc:.2f}  ICC(1,7)={icc7:.2f}")

# ---- Variance decomposition trait/day/state via mixed model (athlete + athlete:day) ----
p("\n-- Decomposicao de variancia (traco / dia / estado) --")
for s in subs:
    d=hum[['ID','dia',s]].dropna().rename(columns={s:'y'})
    d['dia']=d['dia'].astype(int)
    try:
        m=smf.mixedlm('y~1',d,groups=d['ID'],re_formula='1',
                      vc_formula={'dia':'0+C(dia)'}).fit(reml=True)
        va=m.cov_re.iloc[0,0]; vd=list(m.vcomp)[0] if len(m.vcomp)>0 else 0; ve=m.scale
        tot=va+vd+ve
        p(f"  {s:10s} traco={100*va/tot:4.1f}%  dia={100*vd/tot:4.1f}%  estado={100*ve/tot:4.1f}%")
    except Exception as e:
        p(f"  {s:10s} FAIL {e}")

# ---- Generalizability Phi for PTH/TMD: variance atleta/dia/residual ----
p("\n-- Generalizabilidade (TMD): dependabilidade Phi por n coletas --")
d=hum[['ID','dia','TMD']].dropna().rename(columns={'TMD':'y'}); d['dia']=d['dia'].astype(int)
m=smf.mixedlm('y~1',d,groups=d['ID'],re_formula='1',vc_formula={'dia':'0+C(dia)'}).fit(reml=True)
sp=m.cov_re.iloc[0,0]; sd=list(m.vcomp)[0]; se=m.scale
for k in [1,2,3,5,7]:
    phi=sp/(sp+(sd+se)/k)
    p(f"  k={k}: Phi={phi:.2f}")
p(f"  var: atleta={sp:.1f} dia={sd:.1f} residual={se:.1f}")

open('res_a1.txt','w').write('\n'.join(out))
print("\n[saved res_a1.txt]")
