import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
import statsmodels.api as sm
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv')
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

TRAITS=['Vigor','Fadiga','FadFisica','TMD']
d=hum[['ID','dia','HIIT']+TRAITS].dropna().copy()
d['dia_c']=d['dia']-1  # days since baseline
# z-standardize each trait so scales are comparable (multivariate)
zt={}
for t in TRAITS:
    mu,sd=d[t].mean(),d[t].std(); d[t+'_z']=(d[t]-mu)/sd; zt[t]=(mu,sd)
# long/stacked format
long=d.melt(id_vars=['ID','dia','dia_c','HIIT'], value_vars=[t+'_z' for t in TRAITS],
            var_name='trait', value_name='resp')
long['trait']=long['trait'].str.replace('_z','')
long['obs']=long.groupby(['ID','dia']).ngroup()  # observation id for residual cov
p("="*76); p("MODELO MISTO MULTIVARIADO — eixo energia-fadiga (respostas padronizadas z)"); p("="*76)
p(f"  n obs empilhadas={len(long)}  ({d.ID.nunique()} atletas x {len(TRAITS)} tracos)")

# ---------- Model 1: multivariate, trait-specific DAY slope, unstructured athlete RE ----------
p("\n### Modelo 1: resp ~ 0 + trait + trait:dia_c ;  RE nao-estruturado (trait | atleta)")
m1=smf.mixedlm('resp ~ 0 + C(trait) + C(trait):dia_c', long, groups=long['ID'],
               re_formula='0 + C(trait)').fit(method='lbfgs', reml=False)
# fixed effects: day slope per trait
p("  Efeitos fixos (inclinacao/dia por traco):")
for t in TRAITS:
    key=[k for k in m1.params.index if 'dia_c' in k and t in k]
    if key:
        k=key[0]; p(f"    {t:10s} beta/dia={m1.params[k]:+.3f}  p={m1.pvalues[k]:.4f}")
# athlete-level covariance -> correlation across traits
p("  Correlacao ENTRE-ATLETAS (traco) — matriz dos efeitos aleatorios:")
cov=m1.cov_re.values; labs=[c.replace('C(trait)[','').replace(']','').replace('T.','') for c in m1.cov_re.columns]
sd=np.sqrt(np.diag(cov)); corr=cov/np.outer(sd,sd)
p("        "+"  ".join(f"{l[:8]:>8s}" for l in labs))
for i,l in enumerate(labs):
    p(f"    {l[:8]:>8s} "+"  ".join(f"{corr[i,j]:+8.2f}" for j in range(len(labs))))

# ---------- Model 2: multivariate HIIT effect per trait ----------
p("\n### Modelo 2: resp ~ 0 + trait + trait:HIIT (dias de treino 2-7); RE nao-estruturado")
tr=long[long.dia.isin([2,3,4,5,6,7])]
m2=smf.mixedlm('resp ~ 0 + C(trait) + C(trait):HIIT', tr, groups=tr['ID'],
               re_formula='0 + C(trait)').fit(method='lbfgs', reml=False)
p("  Efeito do dia-HIIT por traco (vs tecnico-tatico):")
for t in TRAITS:
    key=[k for k in m2.params.index if 'HIIT' in k and t in k]
    if key:
        k=key[0]; p(f"    {t:10s} beta(HIIT)={m2.params[k]:+.3f}  p={m2.pvalues[k]:.4f}")

# ---------- Joint (multivariate) test of the day effect via LRT ----------
p("\n### Teste multivariado conjunto do efeito do dia (LRT)")
m0=smf.mixedlm('resp ~ 0 + C(trait)', long, groups=long['ID'], re_formula='0 + C(trait)').fit(method='lbfgs',reml=False)
lr=2*(m1.llf-m0.llf); dfd=len(TRAITS); pj=stats.chi2.sf(lr,dfd)
p(f"    LRT (com vs sem trait:dia): chi2={lr:.2f}, gl={dfd}, p={pj:.2e}  -> deslocamento multivariado do perfil")

# ---------- Model 3: multivariate polynomial (cubic) growth, per trait ----------
p("\n### Modelo 3: crescimento CUBICO multivariado (trait-especifico) — coef t^3 por traco")
long['t']=(long['dia']-4); long['t2']=long['t']**2; long['t3']=long['t']**3
m3=smf.mixedlm('resp ~ 0 + C(trait) + C(trait):t + C(trait):t2 + C(trait):t3', long,
               groups=long['ID'], re_formula='0 + C(trait)').fit(method='lbfgs',reml=False)
for t in TRAITS:
    k3=[k for k in m3.params.index if ':t3' in k and t in k]
    if k3:
        k=k3[0]; p(f"    {t:10s} coef t^3={m3.params[k]:+.4f}  p={m3.pvalues[k]:.4f}")

# ---------- report standardized -> raw slope note ----------
p("\n### Nota de escala: inclinacoes em z; multiplicar por DP do traco para escala bruta:")
for t in TRAITS: p(f"    {t:10s} DP={zt[t][1]:.2f}")

open(f'{SC}/res_mvmixed.txt','w').write('\n'.join(out)); print("\n[saved res_mvmixed.txt]")
