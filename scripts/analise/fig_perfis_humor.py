# -*- coding: utf-8 -*-
# Figura canonica dos perfis de humor (estilo Parsons-Smith / "Flamengo"):
# as 6 formas de perfil ao longo das dimensoes do BRUMS em T-scores (media 50, DP 10),
# com linha de referencia em T=50, e a prevalencia de cada perfil na amostra.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
h=pd.read_csv('humor_anon.csv')
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
XL=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
# perfil por atleta-dia
ad=h.groupby(['ID','dia'])[SUB].mean().reset_index().dropna(subset=SUB)
Z=ad[SUB].apply(lambda c:(c-c.mean())/c.std())
T=50+10*Z          # T-scores
CENT={'Iceberg':[-0.5,-0.5,-0.5,1.0,-0.5,-0.5],'Iceberg invertido':[0.6,0.6,0.6,-1.0,0.6,0.6],
 'Everest invertido':[1.2,1.4,1.2,-0.8,1.2,1.2],'Barbatana de tubarão':[0.2,0.2,0.2,0.3,1.4,0.2],
 'Superfície':[0,0,0,0,0,0],'Submerso':[-0.9,-0.9,-0.9,-0.9,-0.9,-0.9]}
names=list(CENT); CM=np.array([CENT[k] for k in names])
lab=[names[int(np.argmin(((CM-r.values)**2).sum(1)))] for _,r in Z.iterrows()]
ad['perfil']=lab; T['perfil']=lab
# perfil medio (T) e prevalencia por cluster
prof_order=['Iceberg','Superfície','Submerso','Barbatana de tubarão','Everest invertido','Iceberg invertido']
COL={'Iceberg':'#2f9e44','Superfície':'#1971c2','Submerso':'#7048e8','Barbatana de tubarão':'#e8590c',
     'Everest invertido':'#e0525b','Iceberg invertido':'#f59f00'}
prev={p:100*np.mean(np.array(lab)==p) for p in prof_order}
print("Prevalência dos perfis (%):")
for p in prof_order: print(f"  {p:22s} {prev[p]:.1f}%  (n={int(sum(np.array(lab)==p))})")

# ---------- FIGURA A: overlay das 6 formas (o "gráfico do Flamengo") ----------
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12})
fig,ax=plt.subplots(figsize=(9.5,6),dpi=200)
x=np.arange(6)
ax.axhspan(40,60,color='#f1f3f5',alpha=.6,zorder=0)          # faixa normal (±1 DP)
ax.axhline(50,color='#868e96',lw=1.4,ls='--',zorder=1)        # referencia populacional
for p in prof_order:
    m=T[T.perfil==p][SUB].mean().values
    ax.plot(x,m,'-o',color=COL[p],lw=2.6,ms=7,label=f'{p} ({prev[p]:.0f}%)',zorder=3)
ax.set_xticks(x); ax.set_xticklabels(XL); ax.set_ylabel('Escore T (média = 50, DP = 10)')
ax.set_ylim(30,72); ax.set_xlim(-0.3,5.3)
for sp in ['top','right']: ax.spines[sp].set_visible(False)
ax.text(5.32,50,'50',va='center',ha='left',fontsize=9,color='#868e96')
ax.set_title('Perfis de humor dos atletas de handebol de elite (BRUMS)\nseis perfis segundo Terry/Parsons-Smith · prevalência entre parênteses',
             fontweight='bold',fontsize=12.5,loc='left')
ax.legend(frameon=False,fontsize=10,loc='upper center',ncol=3,bbox_to_anchor=(0.5,-0.09))
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/perfis_humor_overlay.png',bbox_inches='tight',facecolor='white')

# ---------- FIGURA B: 6 paineis (uma forma por painel) ----------
fig,axs=plt.subplots(2,3,figsize=(13.5,7),dpi=200,sharey=True)
for axp,p in zip(axs.ravel(),prof_order):
    axp.axhspan(40,60,color='#f1f3f5',alpha=.6); axp.axhline(50,color='#868e96',lw=1.2,ls='--')
    m=T[T.perfil==p][SUB].mean().values
    axp.plot(x,m,'-o',color=COL[p],lw=2.8,ms=7)
    axp.set_title(f'{p}  ({prev[p]:.0f}%)',fontweight='bold',fontsize=12,color=COL[p],loc='left')
    axp.set_xticks(x); axp.set_xticklabels(['T','D','R','V','F','C']); axp.set_ylim(30,72)
    for sp in ['top','right']: axp.spines[sp].set_visible(False)
for axp in axs[:,0]: axp.set_ylabel('Escore T')
fig.suptitle('As seis formas de perfil de humor na amostra (T-scores; T=Tensão, D=Depressão, R=Raiva, V=Vigor, F=Fadiga, C=Confusão)',
             fontweight='bold',fontsize=13,y=1.0)
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/perfis_humor_paineis.png',bbox_inches='tight',facecolor='white')
print('\n[figuras: perfis_humor_overlay.png, perfis_humor_paineis.png]')
