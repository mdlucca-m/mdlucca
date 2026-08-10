# -*- coding: utf-8 -*-
"""Análise PREDITIVA do estado de humor pós-treino (BRUMS × HIIT).

Pergunta: quão bem — e a partir de quê — conseguimos PREVER o estado
pós-treino de um atleta? Toda a validação é LEAVE-ONE-ATHLETE-OUT
(LeaveOneGroupOut agrupado pelo atleta): o modelo nunca vê o atleta que
está prevendo, o que respeita a estrutura de medidas repetidas e mede
generalização real para um atleta novo. As predições fora-da-dobra (OOF)
são acumuladas e o R²/AUC é calculado uma única vez sobre elas (pooled).

Compara conjuntos de preditores aninhados para responder à tese:
  1. Média global (referência)         2. Baseline (o pré do próprio dia)
  3. Baseline + contexto (HIIT, dia)    4. Perfil pré completo + contexto
Se (3)/(4) não superam (2), o estado pós é governado pela linha de base
individual — não pela carga/contexto da sessão (confirmação preditiva do
desacoplamento carga↔humor).

Autocontido: lê ../modelagem/base_modelagem.csv (anonimizado A01–A27).
Uso: python preditiva.py → resultados_preditiva.json + preditiva_fig.png
Dependências: numpy pandas scikit-learn matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score, mean_squared_error, roc_auc_score
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')

df=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
SUBS=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','FadMen','EstFis','EstMen']
# ---- monta pares pré→pós por atleta-dia ----
pre=df[df.momento=='pre'].set_index(['atleta','dia'])
pos=df[df.momento=='pos'].set_index(['atleta','dia'])
idx=pre.index.intersection(pos.index)
X=pre.loc[idx].copy(); Y=pos.loc[idx].copy()
grp=np.array([a for a,d in idx])
dia=np.array([d for a,d in idx])
hiit=X['hiit'].values.astype(float)
n=len(idx); n_atl=len(set(grp))
print(f"Pares pré→pós: {n} (de {n_atl} atletas)")

logo=LeaveOneGroupOut()
def oof_reg(Xm, y, model):
    """predições OOF acumuladas (leave-one-athlete-out)."""
    pred=np.full(len(y), np.nan)
    for tr,te in logo.split(Xm,y,grp):
        m=model(); m.fit(Xm[tr],y[tr]); pred[te]=m.predict(Xm[te])
    return pred
def score(y,pred):
    return dict(R2=round(float(r2_score(y,pred)),3),
                RMSE=round(float(np.sqrt(mean_squared_error(y,pred))),3))

RIDGE=lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0))
RF=lambda: RandomForestRegressor(n_estimators=400,max_depth=4,min_samples_leaf=3,random_state=7)

# =========== A. Regressão: prever o estado pós ===========
TARGETS={'PTH':'PTH (TMD)','FadFis':'Fadiga física','Vigor':'Vigor'}
A={}
for tgt,lab in TARGETS.items():
    y=Y[tgt].values.astype(float)
    base_col=tgt  # mesmo construto no pré = linha de base
    FS={
     'Média global':       np.zeros((n,1)),
     'Baseline (pré)':     X[[base_col]].values.astype(float),
     'Baseline + contexto':np.column_stack([X[base_col].values, hiit, dia]).astype(float),
     'Perfil pré completo':np.column_stack([X[SUBS].values, hiit, dia]).astype(float),
    }
    rowsR=[]
    for name,Xm in FS.items():
        if name=='Média global':
            # prevê a média do treino em cada dobra
            pred=np.full(n,np.nan)
            for tr,te in logo.split(Xm,y,grp): pred[te]=y[tr].mean()
            sc=score(y,pred); sc.update(modelo='média')
        else:
            sr=score(y,oof_reg(Xm,y,RIDGE))
            sf=score(y,oof_reg(Xm,y,RF))
            # escolhe o melhor R² entre linear e floresta
            sc=(dict(sr,modelo='Ridge') if sr['R2']>=sf['R2'] else dict(sf,modelo='RandomForest'))
        rowsR.append(dict(preditores=name,**sc))
    A[tgt]=dict(label=lab, resultados=rowsR)
    best=max(rowsR,key=lambda r:r['R2'])
    print(f"  [{lab}] melhor: {best['preditores']} R²={best['R2']} ({best['modelo']})")

# ganho preditivo da carga/contexto sobre o baseline
def r2_of(tgt,name): return next(r['R2'] for r in A[tgt]['resultados'] if r['preditores']==name)
ganho={t:{'baseline':r2_of(t,'Baseline (pré)'),
          'com_contexto':r2_of(t,'Baseline + contexto'),
          'delta_contexto':round(r2_of(t,'Baseline + contexto')-r2_of(t,'Baseline (pré)'),3),
          'perfil_completo':r2_of(t,'Perfil pré completo')} for t in TARGETS}

# =========== B. Classificação: prever o "dia perturbado" ===========
# alvo: fadiga física pós ALTA (>=7, corte de Youden do módulo ROC)
yb=(Y['FadFis'].values>=7).astype(int)
Xb=np.column_stack([X[SUBS].values, hiit, dia]).astype(float)
# baseline: só a fadiga física pré
Xb0=X[['FadFis']].values.astype(float)
def oof_clf(Xm,y,model):
    p=np.full(len(y),np.nan)
    for tr,te in logo.split(Xm,y,grp):
        if len(set(y[tr]))<2: p[te]=y[tr].mean(); continue
        m=model(); m.fit(Xm[tr],y[tr]); p[te]=m.predict_proba(Xm[te])[:,1]
    return p
LOG=lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000,C=1.0))
RFC=lambda: RandomForestClassifier(n_estimators=400,max_depth=4,min_samples_leaf=3,random_state=7)
auc_base=round(float(roc_auc_score(yb,oof_clf(Xb0,yb,LOG))),3)
p_log=oof_clf(Xb,yb,LOG); p_rf=oof_clf(Xb,yb,RFC)
auc_log=round(float(roc_auc_score(yb,p_log)),3); auc_rf=round(float(roc_auc_score(yb,p_rf)),3)
# importância (RF treinada em tudo — só para leitura relativa)
rfc=RFC(); rfc.fit(Xb,yb)
imp=sorted(zip(SUBS+['HIIT','dia'], rfc.feature_importances_), key=lambda t:-t[1])
B=dict(alvo='Fadiga física pós ≥ 7 (corte de Youden, módulo ROC)',
       prevalencia=round(float(yb.mean()),3),
       auc_baseline_fadfis_pre=auc_base, auc_perfil_logistica=auc_log, auc_perfil_floresta=auc_rf,
       importancia=[{'feature':f,'imp':round(float(v),3)} for f,v in imp])
print(f"  Classificação dia perturbado: AUC baseline(FadFis pré)={auc_base} · perfil(log)={auc_log} · perfil(RF)={auc_rf}")

out=dict(n_pares=int(n), n_atletas=int(n_atl), validacao='LeaveOneGroupOut (atleta)',
         A_regressao=A, ganho_contexto=ganho, B_classificacao=B)
json.dump(out,open(os.path.join(HERE,'resultados_preditiva.json'),'w'),ensure_ascii=False,indent=1,default=str)

# =========== figura ===========
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(1,3,figsize=(15.5,5),dpi=160)
# A) R² por conjunto de preditores (PTH e FadFis)
ax=axs[0]
sets=['Média global','Baseline (pré)','Baseline + contexto','Perfil pré completo']
short=['Média','Baseline','Base+HIIT/dia','Perfil pré']
tg=['FadFis','PTH']; cols=[P['RED'],P['BLUE']]
x=np.arange(len(sets)); w=0.38
for j,t in enumerate(tg):
    vals=[r2_of(t,s) for s in sets]
    ax.bar(x+(j-0.5)*w, vals, w, color=cols[j], label=TARGETS[t])
ax.axhline(0,color=P['MUT'],lw=.8)
ax.set_xticks(x); ax.set_xticklabels(short,fontsize=8.5,rotation=12)
ax.set_ylabel('R² fora-da-dobra (LOAO)'); ax.legend(fontsize=8,frameon=False)
ax.set_title('A · Previsibilidade do estado pós\npor conjunto de preditores',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in ['top','right']: ax.spines[sp].set_visible(False)
# B) AUC classificação
ax=axs[1]
labsB=['Baseline\n(FadFis pré)','Perfil pré\n(logística)','Perfil pré\n(floresta)']
valsB=[auc_base,auc_log,auc_rf]
bars=ax.bar(range(3),valsB,color=[P['MUT'],P['TEAL'],P['GOLD']],width=.6)
ax.axhline(0.5,ls='--',color=P['MUT'],lw=1); ax.text(2.4,0.505,'acaso',fontsize=8,color=P['MUT'])
ax.set_ylim(0.4,1.0); ax.set_xticks(range(3)); ax.set_xticklabels(labsB,fontsize=8.5)
ax.set_ylabel('AUC fora-da-dobra (LOAO)')
for i,v in enumerate(valsB): ax.text(i,v+0.01,f'{v:.2f}'.replace('.',','),ha='center',fontsize=9,fontweight='bold',color=P['NAVY'])
ax.set_title('B · Prever o dia perturbado\n(fadiga física pós ≥ 7)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in ['top','right']: ax.spines[sp].set_visible(False)
# C) importância de variáveis
ax=axs[2]
top=B['importancia'][:8][::-1]
ax.barh([t['feature'] for t in top],[t['imp'] for t in top],color=P['VIO'])
ax.set_xlabel('importância (RandomForest)')
ax.set_title('C · O que prevê a fadiga física alta\n(importância relativa)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in ['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'preditiva_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_preditiva.json + preditiva_fig.png")
