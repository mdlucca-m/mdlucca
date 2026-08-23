# -*- coding: utf-8 -*-
# Figura publicação: sonolência (Epworth) e estresse (PSS) ao longo do microciclo.
import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np, json
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy import stats
d=pd.read_csv('humor_epworth_pss_anon.csv')
TIPO={1:'Outro',2:'HIIT',3:'Amistoso',4:'HIIT',5:'Amistoso',6:'Outro',7:'HIIT'}
ad=d.groupby(['ID','dia'])[['Epworth','PSS','TMD','Vigor','Fadiga']].mean().reset_index()
dm=ad.groupby('dia')[['Epworth','PSS']].agg(['mean','sem'])
days=np.arange(1,8)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,3,figsize=(15,4.6),dpi=200,gridspec_kw={'width_ratios':[1.25,1.25,1]})
# A: Epworth
ax=axs[0]
for dd in [2,4,7]: ax.axvspan(dd-.3,dd+.3,color='#e8590c',alpha=.09)
for dd in [3,5]: ax.axvspan(dd-.3,dd+.3,color='#1971c2',alpha=.09)
ax.errorbar(days,dm['Epworth']['mean'],yerr=dm['Epworth']['sem'],fmt='-o',color='#7048e8',lw=2.6,ms=6,capsize=3)
ax.set_title('(A) Sonolência (Epworth) sobe ao longo da semana\nD1 8,8 → D7 11,5 · dz +0,58 · p=0,019',fontweight='bold',loc='left',fontsize=11.5)
ax.set_xlabel('Dia do microciclo'); ax.set_ylabel('Epworth (0–24)'); ax.set_xticks(days)
# B: PSS
ax=axs[1]
for dd in [2,4,7]: ax.axvspan(dd-.3,dd+.3,color='#e8590c',alpha=.09)
for dd in [3,5]: ax.axvspan(dd-.3,dd+.3,color='#1971c2',alpha=.09)
ax.errorbar(days,dm['PSS']['mean'],yerr=dm['PSS']['sem'],fmt='-s',color='#1971c2',lw=2.6,ms=6,capsize=3)
ax.set_title('(B) Estresse (PSS) permanece estável\nD1 22,7 → D7 21,6 · dz −0,19 · p=0,414 (ns)',fontweight='bold',loc='left',fontsize=11.5)
ax.set_xlabel('Dia do microciclo'); ax.set_ylabel('PSS'); ax.set_xticks(days); ax.set_ylim(18,26)
# C: correlações com humor
ax=axs[2]
pairs=[('Epworth','Fadiga'),('Epworth','TMD'),('Epworth','Vigor'),('PSS','TMD'),('PSS','Vigor')]
rs=[stats.spearmanr(ad[a],ad[b])[0] for a,b in pairs]
labs=[f'{a}\n× {b}' for a,b in pairs]; cols=['#e8590c' if r>0 else '#2f9e44' for r in rs]
y=np.arange(len(pairs))[::-1]
ax.barh(y,rs,color=cols,height=.6,alpha=.9)
for yi,r in zip(y,rs): ax.text(r+(0.01 if r>=0 else -0.01),yi,f'{r:+.2f}',va='center',ha='left' if r>=0 else 'right',fontsize=9.5,fontweight='bold')
ax.axvline(0,color='#adb5bd',lw=1); ax.set_yticks(y); ax.set_yticklabels(labs,fontsize=9); ax.set_xlim(-0.35,0.5)
ax.set_title('(C) Relação com o humor\n(ρ de Spearman, atleta-dia)',fontweight='bold',loc='left',fontsize=11.5)
fig.suptitle('Sonolência e estresse no microciclo: o sono acompanha a fadiga; o estresse não muda',fontweight='bold',fontsize=13,y=1.02)
fig.tight_layout()
fig.savefig('/home/user/mdlucca/Artigos/figuras/sono_estresse.png',bbox_inches='tight',facecolor='white')
import os; os.makedirs('/home/user/mdlucca/Artigos/figuras/paper1',exist_ok=True)
fig.savefig('/home/user/mdlucca/Artigos/figuras/paper1/sono_estresse.png',bbox_inches='tight',facecolor='white')
print('[figura: sono_estresse.png]')
