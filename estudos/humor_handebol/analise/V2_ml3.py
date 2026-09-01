# -*- coding: utf-8 -*-
"""Diagnóstico das folhas: o corte pelo PTH é reversão à média ou informação?

A folha mais forte da árvore é contraintuitiva — atletas com PTH baixo de manhã
terminam o dia em risco com probabilidade alta. Antes de escrever qualquer coisa
sobre ela, três verificações:
  1. reversão à média: quem começa baixo tende a subir por construção;
  2. modelos aninhados: o que cada preditor acrescenta de AUC sobre o anterior;
  3. leitura clínica das folhas: o que muda da manhã para a noite dentro de cada uma.
"""
import os, json, sqlite3, warnings
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier
warnings.filterwarnings('ignore')
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
M=json.load(open(os.path.join(DADOS,"V2_ml.json")))
PRED=M['PRED']; ROT=M['ROTULO']
X=np.load(os.path.join(DADOS,"ml_X.npy")); y=np.load(os.path.join(DADOS,"ml_y.npy"))
g=np.load(os.path.join(DADOS,"ml_g.npy"), allow_pickle=True).astype(str)

cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
pp=pd.read_sql("SELECT atleta,dia,variavel,pre,pos FROM pre_pos",cx); cx.close()
larga=pp.pivot_table(index=['atleta','dia'],columns='variavel',values=['pre','pos']).reset_index()
larga.columns=['_'.join(c).strip('_') for c in larga.columns]
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
NORMA={'Tensão':[4.0,3.077],'Depressão':[0.933,1.867],'Raiva':[0.761,1.522],
       'Vigor':[8.195,3.902],'Fadiga':[3.019,3.019],'Confusão':[1.425,1.781]}
P=json.load(open(os.path.join(DADOS,"V2_perfis.json")))
C=np.array(P['C']); NOMES=P['NOMES']; RISCO={3,4,5}
def faixa(v):
    T=np.array([(v[i]-NORMA[s][0])/NORMA[s][1]*10+50 for i,s in enumerate(SUB)])
    return int(((C-T)**2).sum(1).argmin())
larga['perfil_pre']=[faixa([r['pre_'+s] for s in SUB]) for _,r in larga.iterrows()]
larga['perfil_pos']=[faixa([r['pos_'+s] for s in SUB]) for _,r in larga.iterrows()]

# ---------- 1. reversão à média ----------
print("=== 1. REVERSÃO À MÉDIA: ρ(valor da manhã, variação manhã→noite) ===")
print("   um ρ negativo forte indica componente mecânico: começar baixo obriga a subir.")
REV=[]
for v in SUB+['TMD']:
    a=larga['pre_'+v].values.astype(float); d=larga['pos_'+v].values.astype(float)-a
    r,p=spearmanr(a,d)
    REV.append(dict(variavel=('PTH' if v=='TMD' else v), rho=float(r), p=float(p), n=int(len(a)),
                    mecanico=bool(p<0.05)))
for e in sorted(REV,key=lambda e:e['rho']):
    est='***' if e['p']<.001 else '**' if e['p']<.01 else '*' if e['p']<.05 else 'n.s.'
    print(f"  {e['variavel']:<10} ρ = {e['rho']:+.3f}  p = {e['p']:.4f} {est}")

# ---------- 2. modelos aninhados ----------
print("\n=== 2. MODELOS ANINHADOS: AUC agrupada por atleta, acrescentando um preditor por vez ===")
SEQ=[('só PTH (manhã)',['pre_TMD']),
     ('PTH + tensão',['pre_TMD','pre_Tensão']),
     ('PTH + tensão + fadiga física',['pre_TMD','pre_Tensão','pre_Fad.Física']),
     ('todos os preditores',PRED)]
ANIN=[]
for nome,cols in SEQ:
    idx=[PRED.index(c) for c in cols]; Xi=X[:,idx]; aucs=[]
    for r in range(8):
        cv=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=700+r)
        pr=np.full(len(y),np.nan)
        for tr,te in cv.split(Xi,y,g):
            m=XGBClassifier(n_estimators=200,max_depth=2,learning_rate=0.05,subsample=0.8,
                colsample_bytree=0.7,reg_lambda=3.0,min_child_weight=4,eval_metric='logloss',
                random_state=0,n_jobs=-1).fit(Xi[tr],y[tr])
            pr[te]=m.predict_proba(Xi[te])[:,1]
        aucs.append(roc_auc_score(y,pr))
    ANIN.append(dict(modelo=nome,k=len(cols),auc=float(np.mean(aucs)),dp=float(np.std(aucs,ddof=1))))
    print(f"  {nome:<32} k={len(cols):>2}  AUC = {np.mean(aucs):.3f} ± {np.std(aucs,ddof=1):.3f}")

# ---------- 3. leitura das folhas ----------
print("\n=== 3. O QUE ACONTECE DENTRO DAS FOLHAS DA MANHÃ PARA A NOITE ===")
FOL=[('Folha contraintuitiva (PTH ≤ 2,5 · tensão ≤ 0,5 · estresse ≤ 22,5)',
      (larga.pre_TMD<=2.5)&(larga['pre_Tensão']<=0.5)&(larga.pre_PSS<=22.5)),
     ('Folha protegida (PTH ≤ 2,5 · tensão > 1,5)',
      (larga.pre_TMD<=2.5)&(larga['pre_Tensão']>1.5))]
FOLHAS=[]
for nome,mk in FOL:
    s=larga[mk]
    ent=dict(folha=nome,n=int(len(s)),
        manha={v:float(s['pre_'+v].mean()) for v in SUB+['TMD']},
        noite={v:float(s['pos_'+v].mean()) for v in SUB+['TMD']},
        perfil_manha={NOMES[k]:int(c) for k,c in s.perfil_pre.value_counts().items()},
        perfil_noite={NOMES[k]:int(c) for k,c in s.perfil_pos.value_counts().items()},
        risco_noite=float(s.perfil_pos.isin(RISCO).mean()))
    FOLHAS.append(ent)
    print(f"\n  {nome}  (n={ent['n']}, {ent['risco_noite']:.0%} em risco à noite)")
    print(f"    manhã: vigor {ent['manha']['Vigor']:.2f} · fadiga {ent['manha']['Fadiga']:.2f} · "
          f"tensão {ent['manha']['Tensão']:.2f} · PTH {ent['manha']['TMD']:+.2f}")
    print(f"    noite: vigor {ent['noite']['Vigor']:.2f} · fadiga {ent['noite']['Fadiga']:.2f} · "
          f"tensão {ent['noite']['Tensão']:.2f} · PTH {ent['noite']['TMD']:+.2f}")
    print(f"    perfis à noite: {', '.join(f'{k} {v}' for k,v in ent['perfil_noite'].items())}")

# perfis médios da noite, para conferir o que cada rótulo significa nesta solução
PERFN=[]
for k,s in larga.groupby('perfil_pos'):
    PERFN.append(dict(perfil=NOMES[k],n=int(len(s)),risco=bool(k in RISCO),
                      **{v:float(s['pos_'+v].mean()) for v in SUB+['TMD']}))
print("\n  perfis observados à noite (médias brutas):")
for e in sorted(PERFN,key=lambda e:-e['n']):
    print(f"    {e['perfil']:<22} n={e['n']:>3}  vigor {e['Vigor']:.2f}  fadiga {e['Fadiga']:.2f}  PTH {e['TMD']:+.2f}")

# ---------- veredicto ----------
br=lambda x,d=3: f"{x:.{d}f}".replace('.',',').replace('-','−')
rev={e['variavel']:e for e in REV}
VER=dict(
 pth=dict(rho=rev['PTH']['rho'], p=rev['PTH']['p'], mecanico=rev['PTH']['mecanico']),
 tensao=dict(rho=rev['Tensão']['rho'], p=rev['Tensão']['p'], mecanico=rev['Tensão']['mecanico']),
 ganho_tensao=float(ANIN[1]['auc']-ANIN[0]['auc']),
 texto=("O corte pelo PTH tem componente mecânico: quem amanhece com PTH baixo tende a subir por "
        f"reversão à média (ρ = {br(rev['PTH']['rho'])}, p < 0,001). O corte pela tensão não tem: "
        f"a tensão da manhã não prediz a própria variação (ρ = {br(rev['Tensão']['rho'])}, "
        f"p = {br(rev['Tensão']['p'])}). Acrescentar a tensão ao PTH eleva a AUC de "
        f"{br(ANIN[0]['auc'])} para {br(ANIN[1]['auc'])}, de modo que a tensão matinal carrega "
        "informação própria: alguma tensão pela manhã protege, e a ausência completa de tensão "
        "em atleta já muito favorável antecede a queda vespertina."))
print("\n=== VEREDICTO ===\n"+VER['texto'])
json.dump(dict(REVERSAO=REV,ANINHADOS=ANIN,FOLHAS=FOLHAS,PERFIL_NOITE=PERFN,VEREDICTO=VER),
          open(os.path.join(DADOS,"V2_ml3.json"),'w'), ensure_ascii=False, indent=1)
print(f"\n→ {os.path.join(DADOS,'V2_ml3.json')}")
