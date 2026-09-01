# -*- coding: utf-8 -*-
"""Modelos de árvore sobre a base do handebol.

Pergunta: com a medida da MANHÃ, dá para antecipar quem termina o dia na faixa de risco?
Alvo e preditores são separados no tempo, de modo que a previsão não é circular.
Validação agrupada por atleta: nenhum atleta aparece ao mesmo tempo no treino e no teste.
"""
import os, json, sqlite3, warnings
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score, balanced_accuracy_score, confusion_matrix, brier_score_loss
from sklearn.inspection import permutation_importance
from xgboost import XGBClassifier
warnings.filterwarnings('ignore')
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); os.makedirs(DADOS, exist_ok=True)
rng=np.random.default_rng(20240421)

# ---------------- montagem da matriz ----------------
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
pp=pd.read_sql("SELECT atleta,dia,variavel,pre,pos FROM pre_pos",cx)
larga=pp.pivot_table(index=['atleta','dia'],columns='variavel',values=['pre','pos']).reset_index()
larga.columns=['_'.join(c).strip('_') for c in larga.columns]
dias=pd.read_sql("SELECT dia,tipo_estimulo,horas,sessoes,carga_acumulada FROM dia",cx)
ad=pd.read_sql("SELECT atleta,dia,perfil,faixa FROM atleta_dia",cx)
cx.close()
df=larga.merge(dias,on='dia',how='left')

SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
NORMA={'Tensão':[4.0,3.077],'Depressão':[0.933,1.867],'Raiva':[0.761,1.522],
       'Vigor':[8.195,3.902],'Fadiga':[3.019,3.019],'Confusão':[1.425,1.781]}
C=np.array(json.load(open(os.path.join(DADOS,"V2_perfis.json")))['C'])
NOMES=json.load(open(os.path.join(DADOS,"V2_perfis.json")))['NOMES']
RISCO={3,4,5}
def faixa(vec6):
    T=np.array([(vec6[i]-NORMA[s][0])/NORMA[s][1]*10+50 for i,s in enumerate(SUB)])
    return int(((C-T)**2).sum(1).argmin())
df['perfil_pre']=[faixa([r['pre_'+s] for s in SUB]) for _,r in df.iterrows()]
df['perfil_pos']=[faixa([r['pos_'+s] for s in SUB]) for _,r in df.iterrows()]
df['risco_pre']=df.perfil_pre.isin(RISCO).astype(int)
df['y']=df.perfil_pos.isin(RISCO).astype(int)

PRED=(['pre_'+s for s in SUB]+['pre_TMD','pre_Fad.Física','pre_Fad.Mental','pre_Epworth','pre_PSS']
      +['risco_pre','dia','horas','carga_acumulada'])
for t in ['HIIT','Amistoso','Técnico/força']:
    col='estimulo_'+t.split('/')[0]; df[col]=(df.tipo_estimulo==t).astype(int); PRED.append(col)
ROTULO={'pre_Tensão':'Tensão (manhã)','pre_Depressão':'Depressão (manhã)','pre_Raiva':'Raiva (manhã)',
 'pre_Vigor':'Vigor (manhã)','pre_Fadiga':'Fadiga (manhã)','pre_Confusão':'Confusão (manhã)',
 'pre_TMD':'PTH (manhã)','pre_Fad.Física':'Fadiga física (manhã)','pre_Fad.Mental':'Fadiga mental (manhã)',
 'pre_Epworth':'Sonolência (manhã)','pre_PSS':'Estresse percebido (manhã)',
 'risco_pre':'Já estava em risco de manhã','dia':'Dia do microciclo','horas':'Horas de treino do dia',
 'carga_acumulada':'Carga acumulada','estimulo_HIIT':'Dia de HIIT','estimulo_Amistoso':'Dia de amistoso',
 'estimulo_Técnico':'Dia técnico e de força'}
X=df[PRED].astype(float).values; y=df.y.values; g=df.atleta.values
print(f"observações: {len(y)} · atletas: {len(set(g))} · eventos: {y.sum()} ({y.mean():.1%})")
print(f"regra trivial (já estava em risco de manhã): acerta {(df.risco_pre==df.y).mean():.1%}")

# ---------------- modelos ----------------
def mk():
    return {
     'Árvore de decisão': DecisionTreeClassifier(max_depth=3, min_samples_leaf=12,
        class_weight='balanced', random_state=0),
     'Random Forest': RandomForestClassifier(n_estimators=300, max_depth=4, min_samples_leaf=6,
        max_features='sqrt', class_weight='balanced_subsample', random_state=0, n_jobs=-1),
     'XGBoost': XGBClassifier(n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8,
        colsample_bytree=0.7, reg_lambda=3.0, min_child_weight=4, eval_metric='logloss',
        random_state=0, n_jobs=-1),
     'Regressão logística': Pipeline([('z',StandardScaler()),
        ('lr',LogisticRegression(C=0.35, max_iter=4000, class_weight='balanced'))]),
    }
BASE={'Classe majoritária': None, 'Regra: já estava em risco': None}

def avaliar(X,y,g,rep=8,k=5):
    """Validação agrupada por atleta, repetida. Devolve as previsões fora da amostra."""
    nomes=list(mk())+list(BASE)
    prev={n:[] for n in nomes}; verdade=[]; grupo=[]
    for r in range(rep):
        cv=StratifiedGroupKFold(n_splits=k, shuffle=True, random_state=100+r)
        for tr,te in cv.split(X,y,g):
            verdade.append(y[te]); grupo.append(g[te])
            for n,m in mk().items():
                m.fit(X[tr],y[tr]); prev[n].append(m.predict_proba(X[te])[:,1])
            prev['Classe majoritária'].append(np.full(len(te), y[tr].mean()))
            prev['Regra: já estava em risco'].append(X[te][:,PRED.index('risco_pre')])
    return ({n:np.concatenate(v) for n,v in prev.items()},
            np.concatenate(verdade), np.concatenate(grupo), rep)

def ic_boot(y,p,g,fn,B=500):
    ats=np.unique(g); out=[]
    for _ in range(B):
        sel=rng.choice(ats,len(ats),replace=True)
        idx=np.concatenate([np.where(g==a)[0] for a in sel])
        yy,pp_=y[idx],p[idx]
        if len(np.unique(yy))<2: continue
        try: out.append(fn(yy,pp_))
        except Exception: pass
    return (float(np.percentile(out,2.5)), float(np.percentile(out,97.5))) if out else (np.nan,np.nan)

prev,yv,gv,rep=avaliar(X,y,g)
print(f"\nvalidação: {rep} repetições × 5 partições agrupadas por atleta → {len(yv)} previsões fora da amostra\n")
RES={}
print(f"{'modelo':26}{'AUC':>7}{'IC 95%':>18}{'ac.balanc.':>12}{'sens.':>8}{'espec.':>8}{'Brier':>8}")
for n,p in prev.items():
    auc=roc_auc_score(yv,p) if len(np.unique(p))>1 else 0.5
    lo,hi=ic_boot(yv,p,gv,roc_auc_score)
    yb=(p>=0.5).astype(int)
    tn,fp,fn_,tp=confusion_matrix(yv,yb,labels=[0,1]).ravel()
    RES[n]=dict(auc=float(auc), ic=[lo,hi], bacc=float(balanced_accuracy_score(yv,yb)),
        sens=float(tp/(tp+fn_)) if tp+fn_ else np.nan, espec=float(tn/(tn+fp)) if tn+fp else np.nan,
        brier=float(brier_score_loss(yv,np.clip(p,0,1))), n=int(len(yv)))
    print(f"{n:26}{auc:7.3f}{f'[{lo:.3f}, {hi:.3f}]':>18}{RES[n]['bacc']:12.3f}"
          f"{RES[n]['sens']:8.3f}{RES[n]['espec']:8.3f}{RES[n]['brier']:8.3f}")

# diferença de AUC contra a regra trivial, com IC agrupado
def dif_auc(nome):
    a,b=prev[nome],prev['Regra: já estava em risco']; ats=np.unique(gv); out=[]
    for _ in range(900):
        sel=rng.choice(ats,len(ats),replace=True)
        idx=np.concatenate([np.where(gv==x)[0] for x in sel])
        if len(np.unique(yv[idx]))<2: continue
        out.append(roc_auc_score(yv[idx],a[idx])-roc_auc_score(yv[idx],b[idx]))
    return float(np.mean(out)), float(np.percentile(out,2.5)), float(np.percentile(out,97.5))
print("\nganho de AUC sobre a regra trivial (IC 95% por reamostragem de atletas):")
GANHO={}
for n in ['Árvore de decisão','Random Forest','XGBoost','Regressão logística']:
    m_,lo,hi=dif_auc(n); GANHO[n]=dict(m=m_,ic=[lo,hi])
    print(f"  {n:22}{m_:+.3f}  [{lo:+.3f}, {hi:+.3f}]  {'—' if lo<0<hi else 'exclui zero'}")
json.dump(dict(RES=RES, GANHO=GANHO, PRED=PRED, ROTULO=ROTULO, n=len(y), eventos=int(y.sum()),
               atletas=len(set(g)), rep=rep,
               taxa_base=float(y.mean()), regra_trivial=float((df.risco_pre==df.y).mean())),
          open(os.path.join(DADOS,"V2_ml.json"),'w'), ensure_ascii=False)
np.save(os.path.join(DADOS,"ml_X.npy"),X); np.save(os.path.join(DADOS,"ml_y.npy"),y)
np.save(os.path.join(DADOS,"ml_g.npy"),g.astype(str))
print("\ngravado: V2_ml.json")
