# -*- coding: utf-8 -*-
"""Pipeline V2 — parte 1: descritivas (robustas e paramétricas), normalidade,
confiabilidade, séries diárias, piso de ruído, suavização, derivadas, cruzamentos."""
import json, numpy as np, collections
from scipy import stats
import os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); SAIDA=os.path.join(RAIZ,"saida")
os.makedirs(DADOS, exist_ok=True); os.makedirs(SAIDA, exist_ok=True)
S=DADOS
B=json.load(open(f"{S}/V2_base.json")); Q=json.load(open(f"{S}/V2_perfis.json"))
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
V=SUB+['TMD']; VX=V+['Fad.Física','Fad.Mental','Epworth','PSS']
NORMA=B['NORMA']; PAR=B['pares']
dia=np.array([p['dia'] for p in PAR]); ath=np.array([p['a'] for p in PAR])
X={v:np.array([p[v] if p.get(v) is not None else np.nan for p in PAR],float) for v in VX}
N=len(PAR); print("pares atleta-dia:",N)

def tmean(x,pr=.2):
    x=np.sort(x[~np.isnan(x)]); k=int(len(x)*pr)
    return float(x[k:len(x)-k].mean()) if len(x)-2*k>0 else float(x.mean())
def boot_md(x,B_=10000,seed=7):
    r=np.random.default_rng(seed); x=x[~np.isnan(x)]
    m=np.median(r.choice(x,(B_,len(x)),replace=True),axis=1)
    return float(np.percentile(m,2.5)), float(np.percentile(m,97.5))

DESC={}
for v in VX:
    x=X[v]; x=x[~np.isnan(x)]
    W,pW=stats.shapiro(x) if len(x)>=3 else (np.nan,np.nan)
    lo,hi=boot_md(x)
    q1,q3=np.percentile(x,[25,75])
    mn=x.min()
    DESC[v]=dict(n=int(len(x)), m=float(x.mean()), sd=float(x.std(ddof=1)),
        se=float(x.std(ddof=1)/np.sqrt(len(x))),
        ic=[float(x.mean()-1.96*x.std(ddof=1)/np.sqrt(len(x))), float(x.mean()+1.96*x.std(ddof=1)/np.sqrt(len(x)))],
        md=float(np.median(x)), q1=float(q1), q3=float(q3), aiq=float(q3-q1),
        md_ic=[lo,hi], tm=tmean(x), mad=float(1.4826*np.median(np.abs(x-np.median(x)))),
        mn=float(mn), mx=float(x.max()), cv=float(100*x.std(ddof=1)/x.mean()) if x.mean() else np.nan,
        sk=float(stats.skew(x)), ku=float(stats.kurtosis(x)),
        W=float(W), pW=float(pW), piso=float(100*np.mean(x==mn)),
        teto=float(100*np.mean(x==x.max())))
print("descritivas ok")

# ---- confiabilidade entre dias (CCI de via única) ----
ICC={}
for v in VX:
    g=collections.defaultdict(list)
    for a,x in zip(ath,X[v]):
        if not np.isnan(x): g[a].append(x)
    g={a:vv for a,vv in g.items() if len(vv)>=2}
    k=np.mean([len(vv) for vv in g.values()])
    todos=np.concatenate([np.array(vv) for vv in g.values()])
    gm=todos.mean()
    msb=sum(len(vv)*(np.mean(vv)-gm)**2 for vv in g.values())/(len(g)-1)
    msw=sum(((np.array(vv)-np.mean(vv))**2).sum() for vv in g.values())/(len(todos)-len(g))
    icc=(msb-msw)/(msb+(k-1)*msw); icck=k*icc/(1+(k-1)*icc)
    epm=float(np.std(todos,ddof=1)*np.sqrt(max(1-icc,0)))
    ICC[v]=dict(icc=float(icc), icck=float(icck), k=float(k), epm=epm,
                mvd=float(1.96*np.sqrt(2)*epm), n=len(g))
print("confiabilidade ok")

# ---- séries diárias, piso de ruído, suavização, derivadas ----
def suav(y):
    y=np.asarray(y,float); z=y.copy()
    for i in range(1,len(y)-1): z[i]=.25*y[i-1]+.5*y[i]+.25*y[i+1]
    return z
SER={}
for v in VX:
    med=np.array([np.nanmean(X[v][dia==d]) for d in range(1,8)])
    ep=np.array([np.nanstd(X[v][dia==d],ddof=1)/np.sqrt(np.sum(~np.isnan(X[v][dia==d]))) for d in range(1,8)])
    piso=float(ep.mean()); sm=suav(med); d1=np.diff(sm); d2=np.diff(d1)
    ch=[i+1 for i in range(6) if abs(d1[i])>piso]
    infl=[float(i+1.5+d2[i]/(d2[i]-d2[i+1])) for i in range(4) if d2[i]*d2[i+1]<0]
    SER[v]=dict(med=med.tolist(), ep=ep.tolist(), sm=sm.tolist(), d1=d1.tolist(), d2=d2.tolist(),
                piso=piso, choque=ch, infl=infl, dtot=float(med[6]-med[0]),
                sinal=bool(abs(med[6]-med[0])>piso), razao=float(abs(med[6]-med[0])/piso))
print(f"{'variável':12}{'Δ':>8}{'piso':>7}{'|Δ|/piso':>10}  veredito  choques")
for v in V:
    d=SER[v]
    print(f"{v:12}{d['dtot']:8.2f}{d['piso']:7.2f}{d['razao']:10.1f}  "
          f"{'SINAL' if d['sinal'] else 'ruído':8}  {', '.join(f'D{c}→D{c+1}' for c in d['choque']) or '—'}")

# ---- cruzamentos entre séries ----
def cruza(a,b):
    A=np.array(SER[a]['sm']); Bs=np.array(SER[b]['sm'])
    dif=A-Bs; lim=float(np.hypot(SER[a]['piso'],SER[b]['piso']))
    cs=[]
    for i in range(6):
        if dif[i]*dif[i+1]<0: cs.append(float(i+1+dif[i]/(dif[i]-dif[i+1])))
    est=bool(cs and abs(dif[0])>lim and abs(dif[-1])>lim)
    return dict(dif=dif.tolist(), lim=lim, cs=cs, est=est, d1=float(dif[0]), d7=float(dif[-1]))
CRZ={f"{a}×{b}":cruza(a,b) for a,b in [('Vigor','Fadiga'),('Vigor','TMD'),('Tensão','Raiva'),
                                        ('Fad.Física','Fad.Mental'),('Vigor','Fad.Física')]}
json.dump(dict(DESC=DESC, ICC=ICC, SER=SER, CRZ=CRZ, N=N,
               nd=[int((dia==d).sum()) for d in range(1,8)]),
          open(f"{S}/V2_a1.json",'w'), ensure_ascii=False)
print("\ngravado: V2_a1.json")
