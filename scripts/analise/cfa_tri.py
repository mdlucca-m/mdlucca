import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import optimize
from scipy.stats import norm
import pingouin as pg
X=pd.read_csv('brums_itens_anon.csv'); N=len(X)
model={'Tensao':['ten2','ten3','ten4'],'Depressao':['dep1','dep2','dep3','dep4'],
       'Raiva':['rai1','rai2','rai3','rai4'],'Vigor':['vig1','vig2','vig3','vig4'],
       'Fadiga':['fad1','fad2','fad3','fad4'],'Confusao':['con1','con2','con3','con4']}
items=[c for f in model for c in model[f]]; fac=[f for f in model for _ in model[f]]
p=len(items); k=len(model); fidx={f:i for i,f in enumerate(model)}; lo=[fidx[f] for f in fac]
D=X[items].astype(float).values
S=np.cov(D,rowwith:=False) if False else np.cov(D,rowvar=False)
sd=np.sqrt(np.diag(S)); R=S/np.outer(sd,sd)         # work in correlation metric
tri=np.tril_indices(k,-1)
def build(th):
    lam=th[:p]; phi=np.tanh(th[p:p+len(tri[0])]); ev=1/(1+np.exp(-th[p+len(tri[0]):]))  # error var in (0,1)
    Phi=np.eye(k)
    for m,(a,b) in enumerate(zip(*tri)): Phi[a,b]=Phi[b,a]=phi[m]
    Lam=np.zeros((p,k))
    for i in range(p): Lam[i,lo[i]]=lam[i]
    Sig=Lam@Phi@Lam.T; 
    for i in range(p): Sig[i,i]=Lam[i]@Phi@Lam[i]+ev[i]
    return Sig,Lam,Phi,ev
_,ldR=np.linalg.slogdet(R)
def Fml(th):
    Sig,*_=build(th)
    s,ld=np.linalg.slogdet(Sig)
    if s<=0: return 1e6
    try: return ld+np.trace(R@np.linalg.inv(Sig))-ldR-p
    except: return 1e6
# init: loadings 0.6, phi 0, error logit for ev=0.64
x0=np.concatenate([np.full(p,0.6), np.zeros(len(tri[0])), np.full(p, np.log(0.64/0.36))])
best=None
for m in range(4):
    rng=np.random.default_rng(m); xi=x0+rng.normal(0,0.05,len(x0))
    r=optimize.minimize(Fml,xi,method='L-BFGS-B',options={'maxiter':30000,'maxfun':60000})
    if best is None or r.fun<best.fun: best=r
Sig,Lam,Phi,ev=build(best.x); Fm=max(best.fun,0)
df=p*(p+1)//2-(p+len(tri[0])+p)
chi=(N-1)*Fm; F0=-ldR; chi0=(N-1)*max(F0,0); df0=p*(p-1)//2
rmsea=np.sqrt(max(chi-df,0)/(df*(N-1))); cfi=1-max(chi-df,0)/max(chi0-df0,1e-9)
tli=((chi0/df0)-(chi/df))/((chi0/df0)-1)
ds=np.sqrt(np.diag(Sig)); Rimp=Sig/np.outer(ds,ds); iu=np.tril_indices(p,0)
srmr=np.sqrt(((R-Rimp)[iu]**2).mean())
lam_std=np.array([Lam[i,lo[i]]/ds[i] for i in range(p)])
print(f"=== AFC (ML, métrica de correlação, 6 fatores, 23 itens) N={N} ===")
print(f"chi2={chi:.0f} df={df} | CFI={cfi:.3f} TLI={tli:.3f} RMSEA={rmsea:.3f} SRMR={srmr:.3f}")
print("\nConfiabilidade e cargas por subescala:")
rows=[]
for f,its in model.items():
    a=pg.cronbach_alpha(data=X[its])[0]
    idx=[items.index(x) for x in its]; lam=np.abs(lam_std[idx])
    om=(lam.sum()**2)/((lam.sum()**2)+np.sum(1-lam**2))
    rows.append((f,a,om,lam.mean()))
    print(f"  {f:10s} α={a:+.2f}  ω={om:.2f}  |λ|méd={lam.mean():.2f}")
# ---------- TRI: GRM normal-ogivo via equivalencia AFC-TRI ----------
print("\n=== TRI (GRM normal-ogivo, via equivalência AFC-TRI) ===")
print("a_i = λ/sqrt(1-λ²) (discriminação); b_ik = τ_ik/λ (limiares na escala do traço)")
def thresholds(col):
    z=X[col].values; n=len(z); cum=0; th=[]
    for c in sorted(pd.unique(z))[:-1]:
        cum+=(z==c).sum(); pr=min(max(cum/n,1e-4),1-1e-4); th.append(norm.ppf(pr))
    return th
for f,its in model.items():
    print(f"  [{f}]")
    for it in its:
        i=items.index(it); l=abs(lam_std[i]); a=l/np.sqrt(max(1-l**2,1e-3))
        tau=thresholds(it); bs=[t/l for t in tau] if l>0.1 else []
        bstr=", ".join(f"{b:+.2f}" for b in bs) if bs else "— (item degenerado/piso)"
        flag="" if l>=0.4 and X[it].nunique()>=3 else "  <-- instável (piso/poucas categorias)"
        print(f"    {it:5s} a={a:4.2f}  b=[{bstr}]{flag}")
