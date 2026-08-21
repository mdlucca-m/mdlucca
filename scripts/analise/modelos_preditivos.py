# -*- coding: utf-8 -*-
# Modelos preditivos/regressão, curvas de crescimento (mistos) e de aprendizado
# BRUMS-only (6 dimensões + PTH), banco anonimizado. Gera 3 figuras.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold, learning_curve, cross_val_predict, cross_val_score
from sklearn.metrics import roc_curve, auc as aucf
import statsmodels.formula.api as smf
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('humor_anon.csv'); S=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
days=np.arange(1,8)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
# 1) crescimento (misto)
fig,axes=plt.subplots(1,3,figsize=(14,4.4),dpi=190)
for ax,(v,lab,col) in zip(axes,[('Vigor','Vigor','#2f9e44'),('Fadiga','Fadiga','#e8590c'),('TMD','PTH','#7048e8')]):
    dd=h[['ID','dia',v]].dropna().rename(columns={v:'y'})
    for aid,gg in dd.groupby('ID'): ax.plot(days,gg.groupby('dia').y.mean().reindex(days),color=col,alpha=.12,lw=1)
    b=smf.mixedlm("y ~ dia + I(dia**2)",dd,groups=dd['ID'],re_formula="~dia").fit().params
    xx=np.linspace(1,7,100); ax.plot(xx,b['Intercept']+b['dia']*xx+b['I(dia ** 2)']*xx**2,color=col,lw=3.2,label='curva populacional (modelo misto)')
    ax.set_title(f'{lab} — curva de crescimento',fontweight='bold',fontsize=12,loc='left',color=col)
    ax.set_xlabel('Dia do microciclo'); ax.set_ylabel('Escore'); ax.set_xticks(days); ax.legend(frameon=False,fontsize=8.5)
fig.suptitle('Curvas de crescimento do humor (modelos mistos): trajetórias individuais e curva populacional',fontweight='bold',fontsize=13,y=1.0)
fig.tight_layout(); fig.savefig(f'{OUT}/curvas_crescimento.png',bbox_inches='tight',facecolor='white')
# 2-3) preditivo
d=h[h.dia.isin([1,2,3,5,6,7])].dropna(subset=S).copy(); d['late']=(d.dia>=5).astype(int)
X=d[S].values; y=d['late'].values; g=d['ID'].values
pipe=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000)); gkf=GroupKFold(5)
auc=cross_val_score(pipe,X,y,cv=gkf,groups=g,scoring='roc_auc')
print(f'AUC CV = {auc.mean():.3f} ± {auc.std():.3f}')
proba=cross_val_predict(pipe,X,y,cv=gkf,groups=g,method='predict_proba')[:,1]
fpr,tpr,_=roc_curve(y,proba); AUC=aucf(fpr,tpr)
f2,ax=plt.subplots(figsize=(5.4,5),dpi=190)
ax.plot(fpr,tpr,color='#1971c2',lw=2.8,label=f'Logística (AUC = {AUC:.2f})'); ax.plot([0,1],[0,1],'--',color='#adb5bd',lw=1.3,label='acaso')
ax.set_xlabel('1 − especificidade'); ax.set_ylabel('Sensibilidade'); ax.set_aspect('equal')
ax.set_title('Curva ROC — fase tardia vs inicial\na partir do perfil de humor (validação por atleta)',fontweight='bold',fontsize=11,loc='left'); ax.legend(frameon=False,loc='lower right')
f2.tight_layout(); f2.savefig(f'{OUT}/roc_preditivo.png',bbox_inches='tight',facecolor='white')
sz,tr,va=learning_curve(pipe,X,y,cv=gkf,groups=g,scoring='roc_auc',train_sizes=np.linspace(.2,1,6),shuffle=True,random_state=0)
f3,ax=plt.subplots(figsize=(7,4.6),dpi=190)
ax.plot(sz,tr.mean(1),'o-',color='#1971c2',lw=2.4,label='treino'); ax.fill_between(sz,tr.mean(1)-tr.std(1),tr.mean(1)+tr.std(1),color='#1971c2',alpha=.12)
ax.plot(sz,va.mean(1),'s-',color='#e8590c',lw=2.4,label='validação cruzada (por atleta)'); ax.fill_between(sz,va.mean(1)-va.std(1),va.mean(1)+va.std(1),color='#e8590c',alpha=.12)
ax.axhline(0.5,ls=':',color='#adb5bd',label='acaso (AUC 0,5)'); ax.set_ylim(0.45,0.9)
ax.set_xlabel('Tamanho do conjunto de treino (observações)'); ax.set_ylabel('AUC')
ax.set_title('Curva de aprendizado: sinal limitado, sem overfitting relevante',fontweight='bold',fontsize=11.5,loc='left'); ax.legend(frameon=False,loc='upper right')
f3.tight_layout(); f3.savefig(f'{OUT}/curva_aprendizado.png',bbox_inches='tight',facecolor='white')
print('OK 3 figuras')
