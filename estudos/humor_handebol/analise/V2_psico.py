# -*- coding: utf-8 -*-
"""Confiabilidade e estrutura do BRUMS neste elenco.

Os artigos citam a validação brasileira do instrumento, mas nunca verificaram
como ele se comporta nesta amostra. A verificação importa porque a tensão é o
marcador que sustenta a leitura de «ativação, não sofrimento» dos dois artigos e
o preditor protetor da modelagem: se a subescala não for confiável aqui, a
leitura precisa de ressalva ou de outro suporte.

Reamostragem agrupada por atleta em toda estimativa de intervalo: os 456
registros não são independentes.
"""
import os, io, json, contextlib, importlib.util, collections
import numpy as np
from scipy import stats
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
spec=importlib.util.spec_from_file_location("v2qual", os.path.join(RAIZ,"analise","V2_qual.py"))
mq=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(mq)
D=mq.DENTRO; SUBESC=mq.SUBESC; ITENS=list(mq.ITEM_BRUMS)
ATL=sorted({x['atleta'] for x in D})
POR={a:[x for x in D if x['atleta']==a] for a in ATL}
rng=np.random.default_rng(20240427)

def mat(regs, itens): return np.array([[r['itens'][i] for i in itens] for r in regs], float)

# ---------------- alfa de Cronbach ----------------
def alfa(A):
    k=A.shape[1]; vt=A.sum(1).var(ddof=1)
    if vt<=0 or k<2: return float('nan')
    return k/(k-1)*(1-A.var(0,ddof=1).sum()/vt)

# ---------------- ômega de McDonald, por eixo principal iterado ----------------
def omega(A, iters=60):
    R=np.corrcoef(A, rowvar=False)
    if np.isnan(R).any(): return float('nan'), None
    h2=np.array([1-1/np.diag(np.linalg.pinv(R))[j] for j in range(R.shape[0])])  # comunalidade inicial (SMC)
    for _ in range(iters):
        Rr=R.copy(); np.fill_diagonal(Rr,h2)
        w,v=np.linalg.eigh(Rr); j=int(np.argmax(w))
        lam=v[:,j]*np.sqrt(max(w[j],1e-12))
        novo=lam**2
        if np.max(np.abs(novo-h2))<1e-8: h2=novo; break
        h2=np.clip(novo,0,0.999)
    if lam.sum()<0: lam=-lam
    s=A.std(0,ddof=1)                       # de padronizado para a métrica do item
    L=lam*s; psi=s**2-L**2
    den=L.sum()**2+psi.sum()
    return (float(L.sum()**2/den) if den>0 else float('nan')), lam

# ---------------- reamostragem agrupada por atleta ----------------
def ic_agrupado(itens, fn, B=800):
    vs=[]
    for _ in range(B):
        sel=rng.choice(ATL, size=len(ATL), replace=True)
        regs=[r for a in sel for r in POR[a]]
        if len(regs)<10: continue
        try: v=fn(mat(regs,itens))
        except Exception: continue
        if isinstance(v,tuple): v=v[0]
        if v==v: vs.append(v)
    return (float(np.percentile(vs,2.5)), float(np.percentile(vs,97.5))) if len(vs)>50 else (None,None)

CONF=[]
print(f"=== CONFIABILIDADE DAS SEIS SUBESCALAS (n = {len(D)} registros, {len(ATL)} atletas) ===\n")
print(f"  {'subescala':<11} {'alfa':>6} {'IC 95% do alfa':>18} {'omega':>7} {'IC 95% do omega':>19}")
for s,itens in SUBESC.items():
    A=mat(D,itens); a=alfa(A); om,lam=omega(A)
    ica=ic_agrupado(itens, alfa); ico=ic_agrupado(itens, omega)
    r_tot=[float(np.corrcoef(A[:,j], np.delete(A,j,axis=1).sum(1))[0,1]) for j in range(A.shape[1])]
    a_sem=[float(alfa(np.delete(A,j,axis=1))) for j in range(A.shape[1])]
    piso=[float((A[:,j]==0).mean()*100) for j in range(A.shape[1])]
    CONF.append(dict(subescala=s, itens=itens, alfa=float(a), alfa_ic=list(ica),
                     omega=float(om), omega_ic=list(ico),
                     cargas=[float(x) for x in (lam if lam is not None else [])],
                     item_total=r_tot, alfa_sem_item=a_sem, pct_piso=piso,
                     adequada=bool(a>=.70)))
    print(f"  {s:<11} {a:>6.3f} {f'[{ica[0]:.3f}; {ica[1]:.3f}]' if ica[0] is not None else '—':>18} "
          f"{om:>7.3f} {f'[{ico[0]:.3f}; {ico[1]:.3f}]' if ico[0] is not None else '—':>19}"
          + ("" if a>=.70 else "   ← abaixo de 0,70"))
print("\n  item a item:")
print(f"  {'subescala':<11} {'item':<16} {'r item-total':>13} {'alfa sem ele':>13} {'% no piso':>10} {'carga':>7}")
for c in CONF:
    for j,i in enumerate(c['itens']):
        print(f"  {c['subescala']:<11} {i:<16} {c['item_total'][j]:>13.2f} {c['alfa_sem_item'][j]:>13.3f} "
              f"{c['pct_piso'][j]:>10.1f} {c['cargas'][j] if c['cargas'] else float('nan'):>7.2f}")

# ---------------- escalonamento multitraço ----------------
# Ware: um item deve correlacionar-se mais com a própria subescala (corrigida) do
# que com qualquer outra. Cada comparação vencida é um sucesso de escalonamento.
import warnings; warnings.filterwarnings('ignore')
TODOS={s:mat(D,i) for s,i in SUBESC.items()}
MT=[]; suc=0; tot=0
for s,itens in SUBESC.items():
    A=TODOS[s]
    for j,it in enumerate(itens):
        r_prop=float(np.corrcoef(A[:,j], np.delete(A,j,axis=1).sum(1))[0,1])
        outras={}
        for s2 in SUBESC:
            if s2==s: continue
            r=float(np.corrcoef(A[:,j], TODOS[s2].sum(1))[0,1]); outras[s2]=r
        venceu=sum(1 for r in outras.values() if r_prop>r); suc+=venceu; tot+=len(outras)
        MT.append(dict(subescala=s, item=it, r_propria=r_prop, r_outras=outras,
                       vitorias=venceu, de=len(outras),
                       maior_alheia=max(outras, key=outras.get), r_maior=max(outras.values())))
print(f"\n=== ESCALONAMENTO MULTITRAÇO ===")
print(f"  {suc} de {tot} comparações vencidas ({100*suc/tot:.1f}%): o item correlaciona-se mais com a "
      "própria subescala do que com a alheia.")
falhas=[m for m in MT if m['vitorias']<m['de']]
if falhas:
    print("  itens que perdem alguma comparação:")
    for m in falhas:
        print(f"    {m['subescala']:<11} {m['item']:<16} própria {m['r_propria']:.2f} × "
              f"{m['maior_alheia']} {m['r_maior']:.2f}   ({m['vitorias']}/{m['de']})")

# ---------------- a tensão no nível do item ----------------
# A tensão é o marcador protetor da modelagem. Se a subescala é frágil, de onde
# vem o sinal: dos quatro itens, do núcleo de dois, ou de um só?
import sqlite3, pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier
P=json.load(open(os.path.join(DADOS,"V2_perfis.json")))
C=np.array(P['C']); RISCO={3,4,5}
NORMA={'Tensão':[4.0,3.077],'Depressão':[0.933,1.867],'Raiva':[0.761,1.522],
       'Vigor':[8.195,3.902],'Fadiga':[3.019,3.019],'Confusão':[1.425,1.781]}
SUB6=list(NORMA)
def faixa(v):
    T=np.array([(v[i]-NORMA[s][0])/NORMA[s][1]*10+50 for i,s in enumerate(SUB6)])
    return int(((C-T)**2).sum(1).argmin())
por=collections.defaultdict(list)
for x in D: por[(x['atleta'],x['dia'])].append(x)
linhas=[]
for (a,d),g in por.items():
    if d<2 or len(g)<2: continue
    g=sorted(g,key=lambda x:x['carimbo']); pre,pos=g[0],g[-1]
    r=dict(atleta=a, dia=d, pth=pre['calc']['TMD'],
           y=int(faixa([pos['calc'][s] for s in SUB6]) in RISCO))
    for it in SUBESC['Tensão']: r['it_'+it]=pre['itens'][it]
    r['tensao']=pre['calc']['Tensão']
    r['nucleo']=pre['itens']['Ansioso']+pre['itens']['Preocupado']
    linhas.append(r)
df=pd.DataFrame(linhas)
g_=df.atleta.values; y=df.y.values
def auc_de(cols, reps=8):
    X=df[cols].astype(float).values; out=[]
    for rp in range(reps):
        cv=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=900+rp)
        pr=np.full(len(y),np.nan)
        for tr,te in cv.split(X,y,g_):
            m=XGBClassifier(n_estimators=200,max_depth=2,learning_rate=0.05,subsample=0.8,
                colsample_bytree=0.7,reg_lambda=3.0,min_child_weight=4,eval_metric='logloss',
                random_state=0,n_jobs=-1).fit(X[tr],y[tr])
            pr[te]=m.predict_proba(X[te])[:,1]
        out.append(roc_auc_score(y,pr))
    return float(np.mean(out)), float(np.std(out,ddof=1))
ESPEC=[('PTH sozinho',['pth']),
       ('PTH + subescala de tensão (4 itens)',['pth','tensao']),
       ('PTH + núcleo ansioso e preocupado',['pth','nucleo']),
       ('PTH + os quatro itens separados',['pth']+['it_'+i for i in SUBESC['Tensão']]),
       ('PTH + apenas «ansioso»',['pth','it_Ansioso']),
       ('PTH + apenas «preocupado»',['pth','it_Preocupado']),
       ('PTH + apenas «tenso»',['pth','it_Tenso']),
       ('PTH + apenas «apavorado»',['pth','it_Apavorado'])]
TENS=[]
print(f"\n=== DE ONDE VEM A TENSÃO PROTETORA (n = {len(df)} pares, {df.atleta.nunique()} atletas) ===")
print(f"  {'especificação':<38} {'AUC':>7} {'dp entre repetições':>21}")
for nome,cols in ESPEC:
    m,s_=auc_de(cols); TENS.append(dict(especificacao=nome, colunas=cols, auc=m, dp=s_))
    print(f"  {nome:<38} {m:>7.3f} {s_:>21.3f}")
base=TENS[0]['auc']
melhor=max(TENS[1:],key=lambda e:e['auc'])
print(f"\n  ganho sobre o PTH sozinho: melhor especificação é «{melhor['especificacao']}» "
      f"({melhor['auc']-base:+.3f}).")

json.dump(dict(CONF=CONF, MULTITRACO=dict(sucessos=suc, total=tot, pct=100*suc/tot, itens=MT),
               TENSAO=TENS, n=len(D), atletas=len(ATL), n_pares=len(df)),
          open(os.path.join(DADOS,"V2_psico.json"),'w'), ensure_ascii=False, indent=1)
print(f"\n→ {os.path.join(DADOS,'V2_psico.json')}")
