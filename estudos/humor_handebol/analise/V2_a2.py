# -*- coding: utf-8 -*-
"""Pipeline V2 — parte 2: baterias não paramétrica e paramétrica lado a lado."""
import json, numpy as np, collections, warnings
import pandas as pd
from scipy import stats
warnings.filterwarnings('ignore')
import os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); SAIDA=os.path.join(RAIZ,"saida")
os.makedirs(DADOS, exist_ok=True); os.makedirs(SAIDA, exist_ok=True)
S=DADOS
B=json.load(open(f"{S}/V2_base.json"))
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V=SUB+['TMD']
VX=V+['Fad.Física','Fad.Mental','Epworth','PSS']
PAR=B['pares']; CARGA=B['CARGA']
EST={int(k):v['tipo'] for k,v in CARGA.items()}
df=pd.DataFrame([{**{k:p.get(k) for k in ['a','dia']+VX}} for p in PAR])
df['tipo']=df['dia'].map(EST)
M={v:df.pivot_table(index='a',columns='dia',values=v) for v in VX}   # atleta × dia

def holm(ps):
    ps=np.asarray(ps,float); o=np.argsort(ps); m=len(ps); adj=np.empty(m); c=0.
    for i,k in enumerate(o):
        c=max(c,(m-i)*ps[k]); adj[k]=min(c,1.)
    return adj
def pageL(Y):
    """Y: linhas = sujeitos completos, colunas = condições ordenadas."""
    n,k=Y.shape
    R=np.apply_along_axis(stats.rankdata,1,Y)
    L=float(sum((j+1)*R[:,j].sum() for j in range(k)))
    mu=n*k*(k+1)**2/4.0
    var=n*k**2*(k+1)*(k**2-1)/144.0
    z=(L-mu)/np.sqrt(var)
    return L, float(z), float(2*(1-stats.norm.cdf(abs(z))))
def gg_epsilon(Y):
    n,k=Y.shape; S_=np.cov(Y,rowvar=False)
    Sb=S_-S_.mean(0)[None,:]-S_.mean(1)[:,None]+S_.mean()
    num=(k-1)**2*(np.trace(Sb@Sb.T)/ (k-1)**2)  # placeholder
    lam=np.linalg.eigvalsh(Sb)
    eps=(lam.sum()**2)/((k-1)*(lam**2).sum())
    return float(np.clip(eps,1/(k-1),1.0))

NP={}; PA={}
for v in VX:
    Y=M[v].dropna()                       # casos completos nos 7 dias
    Yc=Y.values.astype(float); n,k=Yc.shape
    # ---------- NÃO PARAMÉTRICA ----------
    chi,p=stats.friedmanchisquare(*[Yc[:,j] for j in range(k)]) if n>=2 else (np.nan,np.nan)
    W=float(chi/(n*(k-1))) if n else np.nan
    L,z,pz=pageL(Yc)
    # contrastes D1 vs Dk
    ph=[]
    for j in range(1,k):
        m=~np.isnan(M[v][1]) & ~np.isnan(M[v][j+1])
        x=M[v][1][m].values; y=M[v][j+1][m].values
        if (x!=y).sum()==0: ph.append(dict(par=f"D1–D{j+1}",n=int(m.sum()),p=1.0,r=0.0,d=0.0)); continue
        st,pp=stats.wilcoxon(x,y)
        zz=stats.norm.isf(pp/2)
        ph.append(dict(par=f"D1–D{j+1}",n=int(m.sum()),p=float(pp),
                       r=float(zz/np.sqrt(m.sum())), d=float((y-x).mean())))
    for e,a in zip(ph,holm([e['p'] for e in ph])): e['ph']=float(a)
    NP[v]=dict(n=int(n), chi=float(chi), p=float(p), W=W, L=L, z=z, pz=pz, PH=ph)
    # ---------- PARAMÉTRICA ----------
    gm=Yc.mean(); sm=Yc.mean(1); cm=Yc.mean(0)
    SSs=k*((sm-gm)**2).sum(); SSc=n*((cm-gm)**2).sum()
    SSe=((Yc-sm[:,None]-cm[None,:]+gm)**2).sum()
    dfc=k-1; dfe=(n-1)*(k-1)
    F=(SSc/dfc)/(SSe/dfe); pF=float(stats.f.sf(F,dfc,dfe))
    eta=float(SSc/(SSc+SSe))
    eps=gg_epsilon(Yc); pGG=float(stats.f.sf(F,dfc*eps,dfe*eps))
    m=~np.isnan(M[v][1]) & ~np.isnan(M[v][7])
    x=M[v][1][m].values; y=M[v][7][m].values; dd=y-x
    t,pt=stats.ttest_rel(y,x)
    dz=float(dd.mean()/dd.std(ddof=1))
    se=dd.std(ddof=1)/np.sqrt(len(dd)); tc=stats.t.ppf(.975,len(dd)-1)
    PA[v]=dict(n=int(n), F=float(F), gl=[dfc,dfe], p=pF, eta2p=eta, eps=eps, pGG=pGG,
               t=float(t), pt=float(pt), dz=dz, ndz=int(len(dd)),
               dif=float(dd.mean()), ic=[float(dd.mean()-tc*se), float(dd.mean()+tc*se)],
               lev=float(stats.levene(*[Yc[:,j] for j in range(k)])[1]))
print(f"{'variável':12}|{'  não paramétrica':>34}|{'  paramétrica':>36}")
print(f"{'':12}|{'Friedman p':>12}{'W':>8}{'Page z':>8}{'p':>7}|{'F':>8}{'p GG':>9}{'η²p':>7}{'dz':>7}{'p (t)':>8}")
for v in V:
    a,b=NP[v],PA[v]
    print(f"{v:12}|{a['p']:12.4f}{a['W']:8.3f}{a['z']:8.2f}{a['pz']:7.3f}|"
          f"{b['F']:8.2f}{b['pGG']:9.4f}{b['eta2p']:7.3f}{b['dz']:7.3f}{b['pt']:8.4f}")
json.dump(dict(NP=NP,PA=PA), open(f"{S}/V2_a2.json",'w'), ensure_ascii=False)
print("\ngravado: V2_a2.json")
