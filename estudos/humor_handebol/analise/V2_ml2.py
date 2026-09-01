# -*- coding: utf-8 -*-
"""Interpretação: a árvore desenhável, importância por permutação e o subgrupo acionável."""
import os, json, warnings
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score
from sklearn.inspection import permutation_importance
from xgboost import XGBClassifier
warnings.filterwarnings('ignore')
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
M=json.load(open(os.path.join(DADOS,"V2_ml.json")))
PRED=M['PRED']; ROT=M['ROTULO']
X=np.load(os.path.join(DADOS,"ml_X.npy")); y=np.load(os.path.join(DADOS,"ml_y.npy"))
g=np.load(os.path.join(DADOS,"ml_g.npy"), allow_pickle=True).astype(str)
rng=np.random.default_rng(7)

# ---------- 1. árvore final, ajustada em tudo, para leitura ----------
arv=DecisionTreeClassifier(max_depth=3,min_samples_leaf=12,class_weight='balanced',random_state=0).fit(X,y)
print("=== ÁRVORE DE DECISÃO (profundidade 3, folha mínima de 12) ===")
print(export_text(arv,feature_names=[ROT.get(p,p) for p in PRED],decimals=1))
def colher(t,i=0,prof=0,cam=None):
    cam=cam or []; nos=[]
    if t.children_left[i]==-1:
        v=t.value[i][0]; n=int(t.n_node_samples[i]); p=float(v[1]/(v[0]+v[1]))
        nos.append(dict(tipo='folha',prof=prof,n=n,p=p,caminho=list(cam)))
    else:
        f=ROT.get(PRED[t.feature[i]],PRED[t.feature[i]]); lim=float(t.threshold[i])
        nos.append(dict(tipo='no',prof=prof,var=f,limiar=lim,n=int(t.n_node_samples[i]),
                        p=float(t.value[i][0][1]/t.value[i][0].sum()),caminho=list(cam)))
        nos+=colher(t,t.children_left[i],prof+1,cam+[f"{f} ≤ {lim:.1f}"])
        nos+=colher(t,t.children_right[i],prof+1,cam+[f"{f} > {lim:.1f}"])
    return nos
ARV=colher(arv.tree_)
print("\nfolhas:")
for n in ARV:
    if n['tipo']=='folha':
        print(f"  n={n['n']:3}  risco previsto {n['p']:.0%}  ←  {' e '.join(n['caminho'])}")

# ---------- 2. importância por permutação, fora da amostra ----------
print("\n=== IMPORTÂNCIA POR PERMUTAÇÃO (queda de AUC fora da amostra) ===")
imp=np.zeros((6,len(PRED))); linha=0
for r in range(6):
    cv=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=300+r)
    acc=np.zeros(len(PRED)); nf=0
    for tr,te in cv.split(X,y,g):
        m=XGBClassifier(n_estimators=200,max_depth=2,learning_rate=0.05,subsample=0.8,
            colsample_bytree=0.7,reg_lambda=3.0,min_child_weight=4,eval_metric='logloss',
            random_state=0,n_jobs=-1).fit(X[tr],y[tr])
        if len(np.unique(y[te]))<2: continue
        pi=permutation_importance(m,X[te],y[te],scoring='roc_auc',n_repeats=12,random_state=r,n_jobs=-1)
        acc+=pi.importances_mean; nf+=1
    imp[linha]=acc/max(nf,1); linha+=1
med=imp.mean(0); dp=imp.std(0,ddof=1)
ordem=np.argsort(med)[::-1]
IMP=[]
for i in ordem:
    IMP.append(dict(var=ROT.get(PRED[i],PRED[i]), media=float(med[i]), dp=float(dp[i])))
    if med[i]>0.002 or i==ordem[0]:
        print(f"  {ROT.get(PRED[i],PRED[i]):32}{med[i]:+.4f}  ± {dp[i]:.4f}")

# ---------- 3. o subgrupo que interessa: quem estava fora de risco de manhã ----------
iR=PRED.index('risco_pre')
m0=X[:,iR]==0
print(f"\n=== SUBGRUPO ACIONÁVEL: os {int(m0.sum())} que começaram o dia fora da faixa de risco ===")
print(f"  entram na faixa até a noite: {int(y[m0].sum())} ({y[m0].mean():.1%})")
Xs=np.delete(X[m0],iR,axis=1); ys=y[m0]; gs=g[m0]
PREDs=[p for j,p in enumerate(PRED) if j!=iR]
res={}
for nome,mk in [('Árvore de decisão',lambda:DecisionTreeClassifier(max_depth=2,min_samples_leaf=10,
                    class_weight='balanced',random_state=0)),
                ('Random Forest',lambda:RandomForestClassifier(n_estimators=300,max_depth=3,
                    min_samples_leaf=6,max_features='sqrt',class_weight='balanced_subsample',
                    random_state=0,n_jobs=-1)),
                ('XGBoost',lambda:XGBClassifier(n_estimators=150,max_depth=2,learning_rate=0.06,
                    subsample=0.8,colsample_bytree=0.7,reg_lambda=4.0,min_child_weight=4,
                    eval_metric='logloss',random_state=0,n_jobs=-1))]:
    pv=[];yv=[];gv=[]
    for r in range(8):
        cv=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=500+r)
        for tr,te in cv.split(Xs,ys,gs):
            m=mk().fit(Xs[tr],ys[tr]); pv.append(m.predict_proba(Xs[te])[:,1])
            yv.append(ys[te]); gv.append(gs[te])
    pv=np.concatenate(pv);yv=np.concatenate(yv);gv=np.concatenate(gv)
    auc=roc_auc_score(yv,pv)
    ats=np.unique(gv); bs=[]
    for _ in range(500):
        sel=rng.choice(ats,len(ats),replace=True)
        idx=np.concatenate([np.where(gv==a)[0] for a in sel])
        if len(np.unique(yv[idx]))>1: bs.append(roc_auc_score(yv[idx],pv[idx]))
    res[nome]=dict(auc=float(auc),ic=[float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))],
                   n=int(m0.sum()),eventos=int(ys.sum()))
    print(f"  {nome:22} AUC {auc:.3f}  IC 95% [{res[nome]['ic'][0]:.3f}, {res[nome]['ic'][1]:.3f}]")

json.dump(dict(ARVORE=ARV, IMPORTANCIA=IMP, SUBGRUPO=res,
               texto_arvore=export_text(arv,feature_names=[ROT.get(p,p) for p in PRED],decimals=1)),
          open(os.path.join(DADOS,"V2_ml2.json"),'w'), ensure_ascii=False)
print("\ngravado: V2_ml2.json")
