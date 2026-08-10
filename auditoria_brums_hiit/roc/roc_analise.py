# -*- coding: utf-8 -*-
"""Análise ROC — capacidade discriminativa das variáveis do BRUMS.

Duas perguntas diagnósticas:
  (a) pré vs. pós-treino  — a variável detecta a RESPOSTA AGUDA?
  (b) dia de HIIT vs. sem — a variável separa o TIPO de estímulo (nível do dia)?

Para cada variável: AUC, IC95% por bootstrap AGRUPADO POR ATLETA (reamostra
atletas, respeitando as medidas repetidas), ponto de corte de Youden e a
sensibilidade/especificidade nesse corte. Gera as curvas ROC.

Autocontido: lê ../modelagem/base_modelagem.csv (anonimizada).
Uso: python roc_analise.py   (grava resultados_roc.json e curvas_roc_*.png)
Dependências: numpy pandas scikit-learn matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from sklearn.metrics import roc_curve, roc_auc_score
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore'); rng = np.random.RandomState(7)

HERE = os.path.dirname(os.path.abspath(__file__))
d = pd.read_csv(os.path.join(HERE, '..', 'modelagem', 'base_modelagem.csv'))
VARS = ['FadFis','PTH','Fadiga','Vigor','FadMen','Tensão','Depressão','Raiva','Confusão']
LAB = {'FadFis':'Fadiga física','PTH':'PTH (TMD)','Fadiga':'Fadiga','Vigor':'Vigor','FadMen':'Fadiga mental',
       'Tensão':'Tensão','Depressão':'Depressão','Raiva':'Raiva','Confusão':'Confusão'}
P = dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8')

def auc_dir(y, x):
    """AUC orientada: se <0,5, inverte o preditor (a direção é informativa)."""
    a = roc_auc_score(y, x)
    return (a, 1) if a >= 0.5 else (1-a, -1)

def boot_ci(y, x, grp, nb=2000):
    ath = np.unique(grp); aucs = []
    for _ in range(nb):
        samp = rng.choice(ath, len(ath), replace=True)
        idx = np.concatenate([np.where(grp==a)[0] for a in samp])
        ys, xs = y[idx], x[idx]
        if len(np.unique(ys)) < 2: continue
        try: aucs.append(max(roc_auc_score(ys, xs), 1-roc_auc_score(ys, xs)))
        except Exception: pass
    return (float(np.percentile(aucs,2.5)), float(np.percentile(aucs,97.5))) if aucs else (np.nan,np.nan)

def youden(y, x, sign):
    fpr, tpr, thr = roc_curve(y, sign*x)
    j = tpr - fpr; k = int(np.argmax(j))
    return {'sens':round(float(tpr[k]),3),'espec':round(float(1-fpr[k]),3),
            'corte':round(float(sign*thr[k]),2) if np.isfinite(thr[k]) else None}

def analise(df, label_col, pos_label, titulo, fname):
    rows = []
    curvas = []
    for v in VARS:
        sub = df[[label_col, v, 'atleta']].dropna()
        y = (sub[label_col].values == pos_label).astype(int); x = sub[v].values.astype(float)
        if len(np.unique(y)) < 2: continue
        auc, sign = auc_dir(y, x)
        lo, hi = boot_ci(y, x, sub['atleta'].values)
        yd = youden(y, x, sign)
        rows.append({'var':v,'label':LAB[v],'AUC':round(auc,3),'IC':[round(lo,3),round(hi,3)],
                     'direcao':'↑ no positivo' if sign>0 else '↓ no positivo', **yd,'n':int(len(y))})
        fpr, tpr, _ = roc_curve(y, sign*x); curvas.append((LAB[v], auc, fpr, tpr))
    rows.sort(key=lambda r:-r['AUC'])
    # figura: top 5 curvas
    fig, ax = plt.subplots(figsize=(6.2,5.6), dpi=170)
    cols = [P['RED'],P['GOLD'],P['TEAL'],P['BLUE'],P['VIO']]
    top = sorted(curvas, key=lambda c:-c[1])[:5]
    for i,(lab,auc,fpr,tpr) in enumerate(top):
        ax.plot(fpr, tpr, color=cols[i], lw=2.2, label=f'{lab} (AUC {auc:.2f})')
    ax.plot([0,1],[0,1],ls='--',color=P['MUT'],lw=1)
    ax.set_xlabel('1 − especificidade'); ax.set_ylabel('sensibilidade')
    for s in ['top','right']: ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=9, loc='lower right'); ax.set_title(titulo, fontsize=11, loc='left', color=P['NAVY'])
    fig.tight_layout(); fig.savefig(os.path.join(HERE, fname), facecolor='white'); plt.close()
    return rows

out = {'n_obs': int(len(d))}

# (a) pré vs pós (apenas coletas pré/pós)
pp = d[d['momento'].isin(['pre','pos'])].copy()
out['pre_vs_pos'] = analise(pp, 'momento', 'pos',
    'ROC — discriminar PÓS de PRÉ-treino', 'curvas_roc_pre_pos.png')
print("== pré vs pós (AUC) =="); [print(f"  {r['label']:14s} AUC={r['AUC']:.3f} IC{r['IC']} sens={r['sens']} espec={r['espec']}") for r in out['pre_vs_pos']]

# (b) HIIT vs sem (nível atleta×dia, dias 2-7)
dd = d[d['dia'].between(2,7)].copy()
ad = dd.groupby(['atleta','dia']).agg({**{v:'mean' for v in VARS}, 'hiit':'max'}).reset_index()
ad['grp'] = ad['hiit'].map({1:'hiit',0:'sem'})
out['hiit_vs_sem'] = analise(ad, 'grp', 'hiit',
    'ROC — discriminar dia de HIIT de dia sem HIIT', 'curvas_roc_hiit.png')
print("\n== HIIT vs sem (AUC) =="); [print(f"  {r['label']:14s} AUC={r['AUC']:.3f} IC{r['IC']} sens={r['sens']} espec={r['espec']}") for r in out['hiit_vs_sem']]

json.dump(out, open(os.path.join(HERE,'resultados_roc.json'),'w'), ensure_ascii=False, indent=1, default=str)
print("\nSalvo em resultados_roc.json + curvas_roc_*.png")
