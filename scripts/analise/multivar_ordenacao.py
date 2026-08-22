# -*- coding: utf-8 -*-
# Modelos multivariados/multidimensionais — o algoritmo busca a estrutura nos dados.
#  (1) PCoA/MDS classico sobre a distancia euclidiana dos perfis z (mesma metrica da PERMANOVA)
#  (2) k-means nao supervisionado com busca do k por silhueta (descoberta de perfis)
#  (3) PCA para interpretar os eixos (quais dimensoes dominam cada coordenada)
# Saida: JSON com coordenadas/carregamentos para embutir no dashboard + figura.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA

S=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
LAB={'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Vigor':'Vigor','Fadiga':'Fadiga','Confusao':'Confusão'}
h=pd.read_csv('humor_anon.csv')
df=h.dropna(subset=S).copy()
Z=StandardScaler().fit_transform(df[S].values)          # perfis padronizados
N=len(Z); print(f'N={N} obs | atletas={df.ID.nunique()} | dias={sorted(df.dia.unique())}')

# ---------- (1) PCoA classico (= PCA sobre z, pois distancia euclidiana) ----------
D2=((Z[:,None,:]-Z[None,:,:])**2).sum(-1)               # matriz de distancias^2
J=np.eye(N)-np.ones((N,N))/N
B=-0.5*J@D2@J                                            # dupla centragem
evals,evecs=np.linalg.eigh(B)
idx=np.argsort(evals)[::-1]; evals=evals[idx]; evecs=evecs[:,idx]
pos=evals>1e-9
coords=evecs[:,pos]*np.sqrt(evals[pos])                 # coordenadas principais
var=evals[pos]/evals[pos].sum()
print(f'PCoA var explicada: PCo1={var[0]*100:.1f}% PCo2={var[1]*100:.1f}% (2D={sum(var[:2])*100:.1f}%)')
pc=coords[:,:2].copy()

# orienta os eixos de forma interpretavel a partir das PROPRIAS coordenadas:
#  +PCo1 = mais energia (vigor alto, perturbacao baixa); +PCo2 = mais tensao
def corr(a,b): return float(np.corrcoef(a,b)[0,1])
if corr(Z[:,S.index('Vigor')],pc[:,0])<0: pc[:,0]*=-1
if corr(Z[:,S.index('Tensao')],pc[:,1])<0: pc[:,1]*=-1

# cargas = coeficientes de estrutura (correlacao dim x coordenada) -> mesmo sinal das coords
load=np.array([[corr(Z[:,i],pc[:,ax]) for i in range(len(S))] for ax in (0,1)])

# centroides por dia (trajetoria multivariada da semana)
day_cent={}
for d in sorted(df.dia.unique()):
    m=df.dia.values==d; day_cent[int(d)]=[float(pc[m,0].mean()),float(pc[m,1].mean())]

# ---------- (2) k-means: o algoritmo BUSCA o numero de perfis ----------
sil={}
for k in range(2,7):
    lab=KMeans(k,n_init=10,random_state=7).fit_predict(Z)
    sil[k]=float(silhouette_score(Z,lab))
kbest=max(sil,key=sil.get)
km=KMeans(kbest,n_init=10,random_state=7).fit(Z)
labels=km.labels_
print(f'silhueta por k: '+', '.join(f'{k}={v:.3f}' for k,v in sil.items())+f'  -> k*={kbest}')
# perfil medio de cada cluster (em z) para interpretar
centers_z=km.cluster_centers_
# reordena clusters por eixo energia (vigor - fadiga) para rotulagem estavel
energy=centers_z[:,S.index('Vigor')]-centers_z[:,S.index('Fadiga')]
order=np.argsort(-energy); remap={old:new for new,old in enumerate(order)}
labels=np.array([remap[l] for l in labels]); centers_z=centers_z[order]
clust_cent_pc=[[float(pc[labels==c,0].mean()),float(pc[labels==c,1].mean())] for c in range(kbest)]
clust_n=[int((labels==c).sum()) for c in range(kbest)]
print('clusters (n, perfil z vigor/fadiga):')
for c in range(kbest):
    print(f'  C{c+1}: n={clust_n[c]:3d} | '+' '.join(f'{LAB[s]}={centers_z[c,i]:+.2f}' for i,s in enumerate(S)))

# ---------- (3) interpretacao dos eixos (coeficientes de estrutura) ----------
print('cargas PCo1:', ', '.join(f'{LAB[s]}={load[0,i]:+.2f}' for i,s in enumerate(S)))
print('cargas PCo2:', ', '.join(f'{LAB[s]}={load[1,i]:+.2f}' for i,s in enumerate(S)))

# ---------- exporta para o dashboard ----------
out={
  'points':[[round(float(pc[i,0]),3),round(float(pc[i,1]),3),int(labels[i]),int(df.dia.values[i])] for i in range(N)],
  'day_centroids':{str(d):[round(v[0],3),round(v[1],3)] for d,v in day_cent.items()},
  'clusters':{'k':int(kbest),'sil':round(sil[kbest],3),
              'centroids_pc':[[round(a,3),round(b,3)] for a,b in clust_cent_pc],
              'n':clust_n,
              'profile_z':[[round(float(centers_z[c,i]),2) for i in range(len(S))] for c in range(kbest)]},
  'var':[round(float(var[0]),3),round(float(var[1]),3)],
  'sil_curve':{str(k):round(v,3) for k,v in sil.items()},
  'loadings':{'PCo1':[round(float(load[0,i]),2) for i in range(len(S))],
              'PCo2':[round(float(load[1,i]),2) for i in range(len(S))]},
  'dims':S
}
open('multivar_ord.json','w').write(json.dumps(out))
print('\n[salvo multivar_ord.json]')

# ---------- figura estatica (opcional, articles) ----------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,(ax1,ax2)=plt.subplots(1,2,figsize=(13,5.4),dpi=200)
cl=['#2f9e44','#e0525b']
for c in range(kbest):
    m=labels==c; ax1.scatter(pc[m,0],pc[m,1],s=14,c=cl[c],alpha=.45,edgecolors='none',
        label=f'Cluster {c+1} (n={clust_n[c]})')
ax1.axhline(0,color='#ced4da',lw=.8); ax1.axvline(0,color='#ced4da',lw=.8)
ax1.set_xlabel(f'PCo1 ({var[0]*100:.1f}%) — energia ↔ perturbação')
ax1.set_ylabel(f'PCo2 ({var[1]*100:.1f}%)')
ax1.set_title('Ordenação multivariada (PCoA) + agrupamento não supervisionado\n'
              'o algoritmo separa recuperados de perfil de perturbação',fontweight='bold',fontsize=11,loc='left')
ax1.legend(frameon=False,fontsize=9,loc='lower left')
# trajetoria dos centroides por dia (zoom na faixa dos centroides)
dx=[day_cent[d][0] for d in range(1,8)]; dy=[day_cent[d][1] for d in range(1,8)]
import matplotlib.cm as cm
seq=cm.viridis(np.linspace(0,.92,7))
for i in range(6):
    ax2.annotate('',xy=(dx[i+1],dy[i+1]),xytext=(dx[i],dy[i]),
                 arrowprops=dict(arrowstyle='-|>',color='#1971c2',lw=2,alpha=.8))
for d in range(1,8):
    ax2.scatter(dx[d-1],dy[d-1],s=140,color=seq[d-1],edgecolors='#1b3a5b',lw=1.2,zorder=4)
    ax2.annotate(f'D{d}',(dx[d-1],dy[d-1]),ha='center',va='center',fontsize=8.5,fontweight='bold',color='white',zorder=5)
pad=0.18
ax2.set_xlim(min(dx)-pad,max(dx)+pad); ax2.set_ylim(min(dy)-pad,max(dy)+pad)
ax2.axhline(0,color='#ced4da',lw=.8); ax2.axvline(0,color='#ced4da',lw=.8)
ax2.set_xlabel(f'PCo1 ({var[0]*100:.1f}%) — energia ↔ perturbação (zoom)'); ax2.set_ylabel(f'PCo2 ({var[1]*100:.1f}%)')
ax2.set_title('Trajetória semanal do centroide do perfil\ndeslocamento rumo à perturbação até D7 (PERMANOVA p = 0,002)',fontweight='bold',fontsize=11,loc='left')
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/ordenacao_multivariada.png',bbox_inches='tight',facecolor='white')
print('[figura salva: ordenacao_multivariada.png]')
