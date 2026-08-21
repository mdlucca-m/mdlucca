import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy.stats import norm
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
X=pd.read_csv('brums_itens_anon.csv')
scales={'Vigor':['vig1','vig2','vig3','vig4'],'Fadiga':['fad1','fad2','fad3','fad4']}
def loadings(items):
    R=np.corrcoef(X[items].values,rowvar=False); w,V=np.linalg.eigh(R); v=V[:,-1]
    if v.mean()<0: v=-v
    return np.clip(v*np.sqrt(w[-1]),-0.95,0.95)
def thresholds(col):
    z=X[col].values; n=len(z); cum=0; th=[]
    for c in sorted(pd.unique(z))[:-1]:
        cum+=(z==c).sum(); pr=min(max(cum/n,1e-4),1-1e-4); th.append(norm.ppf(pr))
    return th
def item_info(theta,a,bs):
    # Samejima GRM information (stable analytic form)
    Pstar=[np.ones_like(theta)]+[1/(1+np.exp(-a*(theta-b))) for b in bs]+[np.zeros_like(theta)]
    info=np.zeros_like(theta)
    for k in range(len(Pstar)-1):
        Pk=np.clip(Pstar[k]-Pstar[k+1],1e-6,1)
        term=a*Pstar[k]*(1-Pstar[k]) - a*Pstar[k+1]*(1-Pstar[k+1])
        info+=term**2/Pk
    return info
th=np.linspace(-4,4,500)
fig,axes=plt.subplots(1,2,figsize=(12,4.6),dpi=190)
for ax,(sc,items) in zip(axes,scales.items()):
    lam=loadings(items); TI=np.zeros_like(th); used=0
    for it,l in zip(items,lam):
        l=abs(l); 
        if l<0.5 or X[it].nunique()<3: continue
        a=1.702*l/np.sqrt(max(1-l**2,1e-3)); bs=[t/l for t in thresholds(it)]
        TI+=item_info(th,a,bs); used+=1
    col='#2f9e44' if sc=='Vigor' else '#e8590c'
    ax.plot(th,TI,lw=2.6,color=col); ax.fill_between(th,TI,alpha=.12,color=col)
    peak=th[np.argmax(TI)]; ax.axvline(peak,ls='--',color='#555',lw=1)
    ax.set_title(f'{sc} — informação do teste ({used} itens; pico θ={peak:+.1f})',fontweight='bold',fontsize=11,loc='left')
    ax.set_xlabel('Traço latente θ (DP)'); ax.set_ylabel('Informação'); ax.spines[['top','right']].set_visible(False)
fig.suptitle('TRI (Modelo de Resposta Gradual de Samejima): função de informação do teste',fontweight='bold',fontsize=12.5,y=1.0)
fig.tight_layout()
out='/home/user/mdlucca/Artigos/figuras/tri_informacao.png'; fig.savefig(out,bbox_inches='tight',facecolor='white'); print('SAVED',out)
