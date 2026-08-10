# -*- coding: utf-8 -*-
"""Curva ROC das DERIVADAS (BRUMS × HIIT).

Em vez do nível absoluto, usa a DERIVADA aguda (Δ = pós − pré, por atleta-dia)
como escore diagnóstico. Pergunta: a taxa de variação do humor discrimina um
DIA DE HIIT melhor do que o nível absoluto? Compara, para cada variável:
  · AUC da DERIVADA (Δ agudo)  vs  · AUC do NÍVEL (média do dia)
para separar dia de HIIT (2/4/7) de dia sem HIIT (1/3/5/6). IC95% por
bootstrap agrupado por atleta (reamostra atletas), com orientação do escore.

Autocontido: lê ../modelagem/base_modelagem.csv. Uso: python roc_derivadas.py
Dependências: numpy pandas scikit-learn matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore'); RS=np.random.RandomState(7)
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')
df=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
VARS={'PTH':'PTH (TMD)','FadFis':'Fadiga física','Fadiga':'Fadiga','Vigor':'Vigor','FadMen':'Fadiga mental'}

# ---- monta, por atleta-dia: derivada aguda (pós−pré) e nível (média do dia) ----
pre=df[df.momento=='pre'].groupby(['atleta','dia'])[list(VARS)].mean()
pos=df[df.momento=='pos'].groupby(['atleta','dia'])[list(VARS)].mean()
idx=pre.index.intersection(pos.index)
deriv=(pos.loc[idx]-pre.loc[idx])
level=(pos.loc[idx]+pre.loc[idx])/2
meta=pd.DataFrame(index=idx); meta['atleta']=[a for a,d in idx]; meta['hiit']=[1 if d in(2,4,7) else 0 for a,d in idx]
lab=meta['hiit'].values; ath=np.array(meta['atleta'].values)

def auc_oriented(score,y):
    a=roc_auc_score(y,score)
    return (a,'↑ no HIIT') if a>=0.5 else (1-a,'↓ no HIIT')  # orienta p/ AUC>=0.5
def boot_ci(score,y,g,n=2000):
    aths=np.unique(g); out=[]
    for _ in range(n):
        pick=RS.choice(aths,len(aths),replace=True)
        ridx=np.concatenate([np.where(g==a)[0] for a in pick])
        ys=y[ridx]
        if len(set(ys))<2: continue
        a=roc_auc_score(ys,score[ridx]); out.append(max(a,1-a))
    return (round(float(np.percentile(out,2.5)),3),round(float(np.percentile(out,97.5)),3)) if out else (None,None)

rows=[]
for k,labk in VARS.items():
    ad,dird=auc_oriented(deriv[k].values,lab); al,dirl=auc_oriented(level[k].values,lab)
    ci_d=boot_ci(deriv[k].values,lab,ath); ci_l=boot_ci(level[k].values,lab,ath)
    rows.append(dict(var=labk,AUC_derivada=round(float(ad),3),IC_derivada=list(ci_d),dir_derivada=dird,
                     AUC_nivel=round(float(al),3),IC_nivel=list(ci_l),dir_nivel=dirl,
                     ganho=round(float(ad-al),3)))
rows.sort(key=lambda r:-r['AUC_derivada'])
out={'n_atleta_dia':int(len(idx)),'alvo':'dia de HIIT (2/4/7) vs sem HIIT (1/3/5/6)',
     'validacao':'IC95% por bootstrap agrupado por atleta','resultados':rows}
json.dump(out,open(os.path.join(HERE,'resultados_roc_derivadas.json'),'w'),ensure_ascii=False,indent=1,default=str)
print("ROC das derivadas (Δ agudo) vs nível — separar dia de HIIT:")
for r in rows: print(f"   {r['var']:14s} AUC_deriv={r['AUC_derivada']:.2f} {r['IC_derivada']}  vs  AUC_nível={r['AUC_nivel']:.2f}  (ganho {r['ganho']:+.2f})")

# ================= figura =================
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(1,2,figsize=(13,5.6),dpi=160)
# A curvas ROC das derivadas
ax=axs[0]; cols=[P['RED'],P['BLUE'],P['GOLD'],P['TEAL'],P['VIO']]
ax.plot([0,1],[0,1],ls=':',color=P['MUT'],lw=1)
for i,(k,labk) in enumerate(VARS.items()):
    s=deriv[k].values; a=roc_auc_score(lab,s)
    if a<0.5: s=-s; a=1-a
    fpr,tpr,_=roc_curve(lab,s)
    ax.plot(fpr,tpr,color=cols[i],lw=2,label=f'{labk} (AUC {a:.2f})')
ax.set_xlabel('1 − especificidade'); ax.set_ylabel('sensibilidade'); ax.legend(fontsize=8.5,frameon=False,loc='lower right')
ax.set_title('A · ROC da DERIVADA aguda (Δ pós−pré)\npara separar dia de HIIT',fontsize=11,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
ax.set_xlim(0,1);ax.set_ylim(0,1.02)
# B derivada vs nível (AUC com IC)
ax=axs[1]; y=np.arange(len(rows)); w=0.38
for i,r in enumerate(rows):
    ax.plot(r['IC_derivada'],[i+w/2,i+w/2],color=P['RED'],lw=2,alpha=.5)
    ax.plot(r['IC_nivel'],[i-w/2,i-w/2],color=P['BLUE'],lw=2,alpha=.5)
ax.barh(y+w/2,[r['AUC_derivada'] for r in rows],w,color=P['RED'],label='derivada (Δ agudo)')
ax.barh(y-w/2,[r['AUC_nivel'] for r in rows],w,color=P['BLUE'],label='nível (média do dia)')
ax.axvline(0.5,ls='--',color=P['MUT'],lw=1); ax.text(0.505,len(rows)-.4,'acaso',fontsize=8,color=P['MUT'])
ax.set_yticks(y); ax.set_yticklabels([r['var'] for r in rows]); ax.set_xlim(0.4,0.8); ax.set_xlabel('AUC (IC95% bootstrap por atleta)')
ax.legend(fontsize=8.5,frameon=False,loc='lower right')
ax.set_title('B · Derivada vs nível como diagnóstico\ndo dia de HIIT',fontsize=11,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'roc_derivadas_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_roc_derivadas.json + roc_derivadas_fig.png")
