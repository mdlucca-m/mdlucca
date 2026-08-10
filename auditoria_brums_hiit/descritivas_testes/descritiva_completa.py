# -*- coding: utf-8 -*-
"""Figura de estatística descritiva completa: histogramas, box plots, dispersão
e normalidade (Q–Q) pré vs. pós, para o artigo. Reproduzível, anonimizado.
Uso: python descritiva_completa.py → descritiva_completa_fig.png"""
import os, numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
d=pd.read_csv(os.path.join(ROOT,'modelagem','base_modelagem.csv'))
TEAL='#0e9c90'; CORAL='#c0392b'; INK='#16273d'; MUT='#5b6b82'; LINE='#d6deea'; BLUE='#245c8b'; GOLD='#b0790f'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':LINE,'axes.labelcolor':INK,
 'xtick.color':INK,'ytick.color':INK,'figure.facecolor':'white','axes.facecolor':'white'})
pre=d[d.momento=='pre']; pos=d[d.momento=='pos']

fig=plt.figure(figsize=(13.4,9.2),dpi=150)
fig.suptitle('Estatística descritiva: distribuições, dispersão e normalidade (pré vs. pós)',x=0.055,ha='left',fontsize=15,fontweight='bold',y=0.985)
gs=fig.add_gridspec(2,2,hspace=0.34,wspace=0.24,left=0.07,right=0.975,top=0.90,bottom=0.07)

# A — histogramas (FadFis e PTH) pré vs pós
axA=fig.add_subplot(gs[0,0])
bins=np.linspace(min(d['FadFis'].min(),0),d['FadFis'].max(),16)
axA.hist(pre['FadFis'].dropna(),bins=bins,alpha=0.6,color=BLUE,label='pré',edgecolor='white')
axA.hist(pos['FadFis'].dropna(),bins=bins,alpha=0.6,color=CORAL,label='pós',edgecolor='white')
axA.set_title('A · Histograma — Fadiga física (pré vs. pós)',fontsize=11,loc='left')
axA.set_xlabel('Fadiga física (0–10)'); axA.set_ylabel('frequência'); axA.legend(frameon=False,fontsize=9)
for s in ['top','right']: axA.spines[s].set_visible(False)

# B — box plots pré vs pós para 4 variáveis-chave
axB=fig.add_subplot(gs[0,1]); vars4=['FadFis','Vigor','Fadiga','PTH']; labs=['Fad. física','Vigor','Fadiga','PTH']
data=[]; pos_x=[]; cols=[]
for i,v in enumerate(vars4):
    data.append(pre[v].dropna()); pos_x.append(i*2+0.6); cols.append(BLUE)
    data.append(pos[v].dropna()); pos_x.append(i*2+1.4); cols.append(CORAL)
bp=axB.boxplot(data,positions=pos_x,widths=0.66,patch_artist=True,showfliers=True,
    medianprops=dict(color=INK,lw=1.4),flierprops=dict(marker='o',ms=2.5,mfc=MUT,mec='none',alpha=0.5))
for patch,c in zip(bp['boxes'],cols): patch.set_facecolor(c); patch.set_alpha(0.55); patch.set_edgecolor(c)
axB.set_xticks([i*2+1 for i in range(4)]); axB.set_xticklabels(labs,fontsize=9)
axB.set_title('B · Box plots pré (azul) vs. pós (coral)',fontsize=11,loc='left'); axB.set_ylabel('escore')
for s in ['top','right']: axB.spines[s].set_visible(False)

# C — dispersão Vigor × Fadiga (eixo energia–fadiga), pré e pós
axC=fig.add_subplot(gs[1,0])
axC.scatter(pre['Fadiga'],pre['Vigor'],s=22,c=BLUE,alpha=0.5,edgecolor='none',label='pré')
axC.scatter(pos['Fadiga'],pos['Vigor'],s=22,c=CORAL,alpha=0.5,edgecolor='none',label='pós')
# reta de regressão global
x=d['Fadiga'].values; y=d['Vigor'].values; m=~(np.isnan(x)|np.isnan(y))
b1,b0=np.polyfit(x[m],y[m],1); xs=np.linspace(x[m].min(),x[m].max(),50)
axC.plot(xs,b0+b1*xs,color=INK,lw=1.6,ls='--',label=f'r={np.corrcoef(x[m],y[m])[0,1]:.2f}')
axC.set_title('C · Dispersão — Vigor × Fadiga (eixo energia–fadiga)',fontsize=11,loc='left')
axC.set_xlabel('Fadiga'); axC.set_ylabel('Vigor'); axC.legend(frameon=False,fontsize=9)
for s in ['top','right']: axC.spines[s].set_visible(False)

# D — Q–Q normalidade do PTH, pré e pós
axD=fig.add_subplot(gs[1,1])
for grp,c,lb in [(pre,BLUE,'pré'),(pos,CORAL,'pós')]:
    v=grp['PTH'].dropna().values; (osm,osr),(sl,ic,_)=stats.probplot(v,dist='norm')
    axD.scatter(osm,osr,s=16,c=c,alpha=0.6,edgecolor='none',label=f'{lb} (W={stats.shapiro(v)[0]:.2f})')
    axD.plot(osm,sl*osm+ic,color=c,lw=1.2,alpha=0.8)
axD.set_title('D · Q–Q normalidade — PTH (pré vs. pós)',fontsize=11,loc='left')
axD.set_xlabel('quantis teóricos (normal)'); axD.set_ylabel('quantis observados'); axD.legend(frameon=False,fontsize=9)
for s in ['top','right']: axD.spines[s].set_visible(False)

fig.text(0.055,0.015,'n=456 observações (135 pares pré→pós). Distribuições não-normais (Shapiro–Wilk), justificando a confirmação por testes não-paramétricos e permutação.',fontsize=8.5,color=MUT)
fig.savefig(os.path.join(HERE,'descritiva_completa_fig.png'),dpi=150,facecolor='white',bbox_inches='tight'); plt.close(fig)
print('salvo descritiva_completa_fig.png')
