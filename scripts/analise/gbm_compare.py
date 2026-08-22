# -*- coding: utf-8 -*-
# Comparacao honesta: Logistica vs XGBoost vs LightGBM na mesma tarefa/validacao.
# Tarefa: prever fase tardia (D5-7) vs inicial (D1-3) a partir das 6 dimensoes do BRUMS.
# Validacao: GroupKFold(5) por atleta (nunca o mesmo atleta em treino e teste).
# Metrica: ROC-AUC.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold, cross_val_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

h = pd.read_csv('humor_anon.csv')
S = ['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
d = h[h.dia.isin([1,2,3,5,6,7])].dropna(subset=S).copy()
d['late'] = (d.dia >= 5).astype(int)
X, y, g = d[S].values, d['late'].values, d['ID'].values
gkf = GroupKFold(5)
print(f"N={len(d)} obs | atletas={d.ID.nunique()} | classe tardia={y.mean():.2f}\n")

modelos = {
    'Logistica': make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
    'XGBoost': XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                             subsample=0.8, colsample_bytree=0.8, reg_lambda=2.0,
                             eval_metric='logloss', random_state=7, verbosity=0),
    'LightGBM': LGBMClassifier(n_estimators=300, max_depth=3, num_leaves=7,
                               learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                               reg_lambda=2.0, min_child_samples=20, random_state=7, verbose=-1),
}
res = {}
for nome, m in modelos.items():
    auc = cross_val_score(m, X, y, cv=gkf, groups=g, scoring='roc_auc')
    res[nome] = (auc.mean(), auc.std())
    print(f"  {nome:10s} AUC = {auc.mean():.3f} +/- {auc.std():.3f}   (folds: "
          + ", ".join(f"{a:.2f}" for a in auc) + ")")

# ---- figura de barras comparativa ----
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT = '/home/user/mdlucca/Artigos/figuras'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False})
nomes = ['Logística', 'XGBoost', 'LightGBM']
means = [res[k][0] for k in res]; sds = [res[k][1] for k in res]
cols = ['#1971c2', '#e8590c', '#2f9e44']
fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=190)
bars = ax.bar(nomes, means, yerr=sds, capsize=6, color=cols, width=0.6,
              error_kw=dict(lw=1.4, ecolor='#495057'))
ax.axhline(0.5, ls='--', color='#adb5bd', lw=1.4, label='acaso (AUC 0,5)')
for b, mn in zip(bars, means):
    ax.text(b.get_x() + b.get_width()/2, mn + 0.012, f'{mn:.2f}',
            ha='center', va='bottom', fontweight='bold', fontsize=11.5)
ax.set_ylim(0.40, 0.72); ax.set_ylabel('AUC (validação cruzada por atleta)')
ax.set_title('Capacidade preditiva por modelo — fase tardia vs inicial\n'
             'modelos flexíveis não superam o teto da logística',
             fontweight='bold', fontsize=11.5, loc='left')
ax.legend(frameon=False, loc='upper right')
fig.tight_layout(); fig.savefig(f'{OUT}/comparacao_modelos_auc.png',
                                bbox_inches='tight', facecolor='white')
print(f'\n[figura salva: {OUT}/comparacao_modelos_auc.png]')
