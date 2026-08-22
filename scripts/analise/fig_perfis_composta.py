# -*- coding: utf-8 -*-
# Figura COMPOSTA e analitica dos perfis de humor (varios paineis num so):
#  A) as 6 formas de perfil (T-scores)         B) prevalencia de cada perfil
#  C) composicao dos perfis por dia (%)         D) indice-iceberg e % iceberg ao longo da semana
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
h=pd.read_csv('humor_anon.csv')
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']; XL=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
NEG=['Tensao','Depressao','Raiva','Fadiga','Confusao']
ad=h.groupby(['ID','dia'])[SUB].mean().reset_index().dropna(subset=SUB)
Z=ad[SUB].apply(lambda c:(c-c.mean())/c.std()); T=50+10*Z
CENT={'Iceberg':[-0.5,-0.5,-0.5,1.0,-0.5,-0.5],'Iceberg invertido':[0.6,0.6,0.6,-1.0,0.6,0.6],
 'Everest invertido':[1.2,1.4,1.2,-0.8,1.2,1.2],'Barbatana de tubarão':[0.2,0.2,0.2,0.3,1.4,0.2],
 'Superfície':[0,0,0,0,0,0],'Submerso':[-0.9,-0.9,-0.9,-0.9,-0.9,-0.9]}
names=list(CENT); CM=np.array([CENT[k] for k in names])
ad['perfil']=[names[int(np.argmin(((CM-r.values)**2).sum(1)))] for _,r in Z.iterrows()]; T['perfil']=ad['perfil'].values
ORD=['Iceberg','Superfície','Submerso','Barbatana de tubarão','Everest invertido','Iceberg invertido']
COL={'Iceberg':'#2f9e44','Superfície':'#1971c2','Submerso':'#7048e8','Barbatana de tubarão':'#e8590c',
     'Everest invertido':'#e0525b','Iceberg invertido':'#f59f00'}
prev={p:100*np.mean(ad['perfil']==p) for p in ORD}
ad['ice']=Z['Vigor'].values-Z[NEG].mean(axis=1).values

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
fig=plt.figure(figsize=(15,9.2),dpi=200)
gs=GridSpec(2,2,figure=fig,height_ratios=[1,0.9],hspace=0.34,wspace=0.22)

# ---- A: as 6 formas ----
axA=fig.add_subplot(gs[0,0]); x=np.arange(6)
axA.axhspan(40,60,color='#f1f3f5',alpha=.7,zorder=0); axA.axhline(50,color='#868e96',lw=1.2,ls='--',zorder=1)
for p in ORD:
    m=T[T.perfil==p][SUB].mean().values
    axA.plot(x,m,'-o',color=COL[p],lw=2.3,ms=5.5,label=f'{p} ({prev[p]:.0f}%)',zorder=3)
axA.set_xticks(x); axA.set_xticklabels(XL,fontsize=9.5,rotation=12); axA.set_ylabel('Escore T (50 ± 10)')
axA.set_ylim(32,72); axA.set_xlim(-0.3,5.3)
for sp in ['top','right']: axA.spines[sp].set_visible(False)
axA.set_title('(A) As seis formas de perfil de humor',fontweight='bold',fontsize=12,loc='left')

# ---- B: prevalencia ----
axB=fig.add_subplot(gs[0,1])
vals=[prev[p] for p in ORD]; y=np.arange(len(ORD))[::-1]
axB.barh(y,vals,color=[COL[p] for p in ORD],alpha=.92,height=.66)
for yi,p in zip(y,ORD): axB.text(prev[p]+0.5,yi,f'{prev[p]:.0f}%',va='center',fontsize=10,fontweight='bold')
axB.set_yticks(y); axB.set_yticklabels(ORD,fontsize=10); axB.set_xlabel('Prevalência na amostra (%)'); axB.set_xlim(0,36)
for sp in ['top','right']: axB.spines[sp].set_visible(False)
axB.set_title('(B) Prevalência de cada perfil',fontweight='bold',fontsize=12,loc='left')

# ---- C: composicao por dia (stacked %) ----
axC=fig.add_subplot(gs[1,0])
comp=pd.crosstab(ad['dia'],ad['perfil'],normalize='index').mul(100)[ORD].reindex(range(1,8))
bottom=np.zeros(7); days=np.arange(1,8)
for p in ORD:
    axC.bar(days,comp[p].values,bottom=bottom,color=COL[p],width=.8,label=p); bottom+=comp[p].values
axC.set_xticks(days); axC.set_xlabel('Dia do microciclo'); axC.set_ylabel('% de atletas'); axC.set_ylim(0,100)
for sp in ['top','right']: axC.spines[sp].set_visible(False)
axC.set_title('(C) Composição dos perfis dia a dia',fontweight='bold',fontsize=12,loc='left')
for d in [2,4,7]: axC.plot(d,101.5,'v',color='#212529',ms=6,clip_on=False)
axC.text(7.4,101.5,'▼ HIIT',color='#212529',fontsize=8.5,ha='right',va='bottom')

# ---- D: indice iceberg + % iceberg por dia ----
axD=fig.add_subplot(gs[1,1])
ic=ad.groupby('dia')['ice'].agg(['mean','sem']).reindex(range(1,8))
axD.axhspan(-0.05,0.05,color='#f1f3f5',alpha=0)  # spacer
axD.errorbar(days,ic['mean'],yerr=ic['sem'],fmt='-o',color='#2f9e44',lw=2.6,ms=7,capsize=4,label='índice-iceberg (z)')
axD.axhline(0,color='#adb5bd',lw=1,ls=':')
for d in [2,4,7]: axD.axvspan(d-.3,d+.3,color='#e8590c',alpha=.08)
axD.set_xticks(days); axD.set_xlabel('Dia do microciclo'); axD.set_ylabel('Índice-iceberg (z: vigor − negativas)',color='#2f9e44')
axD.tick_params(axis='y',labelcolor='#2f9e44')
axD2=axD.twinx()
icep=[100*np.mean(ad[ad.dia==d]['perfil']=='Iceberg') for d in days]
axD2.plot(days,icep,'--s',color='#1971c2',lw=2,ms=6,label='% perfil iceberg')
axD2.set_ylabel('% com perfil iceberg',color='#1971c2'); axD2.tick_params(axis='y',labelcolor='#1971c2'); axD2.set_ylim(0,55)
for sp in ['top']: axD.spines[sp].set_visible(False); axD2.spines[sp].set_visible(False)
axD.set_title('(D) Erosão do iceberg ao longo da semana',fontweight='bold',fontsize=12,loc='left')

from matplotlib.lines import Line2D
handles=[Line2D([0],[0],color=COL[p],lw=3,marker='o',ms=6,label=f'{p} ({prev[p]:.0f}%)') for p in ORD]
fig.legend(handles=handles,frameon=False,fontsize=10,loc='lower center',ncol=6,bbox_to_anchor=(0.5,-0.02))
fig.suptitle('Perfis de humor de atletas de handebol de elite — panorama analítico (BRUMS, seis perfis de Terry/Parsons-Smith)',
             fontweight='bold',fontsize=13.5,y=0.995)
fig.savefig('/home/user/mdlucca/Artigos/figuras/perfis_humor_composta.png',bbox_inches='tight',facecolor='white')
print('prevalência:',{p:round(prev[p]) for p in ORD})
print('índice-iceberg D1..D7:',[round(float(v),2) for v in ic['mean'].values])
print('% iceberg D1..D7:',[round(v) for v in icep])
print('[figura: perfis_humor_composta.png]')
