# -*- coding: utf-8 -*-
# Dias com HIIT (2,4,7) x sem HIIT (1,3,5,6): perfil de humor.
#  - por dimensao: media HIIT vs nao-HIIT (pareado por atleta), dz, Wilcoxon, BH-FDR
#  - multivariada: PERMANOVA (perfil 6 dim), permutacao restrita ao atleta
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
rng=np.random.default_rng(7)
S=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
EXTRA=['TMD','FadFisica','FadMental']
LAB={'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Vigor':'Vigor','Fadiga':'Fadiga',
     'Confusao':'Confusão','TMD':'PTH','FadFisica':'Fadiga física','FadMental':'Fadiga mental'}
h=pd.read_csv('humor_anon.csv')
# valor por atleta x dia (media entre momentos)
day=h.groupby(['ID','dia','HIIT'])[S+EXTRA].mean().reset_index()

rows=[]
for v in S+EXTRA:
    per=[]
    for aid,g in day.groupby('ID'):
        hh=g[g.HIIT==1][v]; nn=g[g.HIIT==0][v]
        if len(hh) and len(nn) and hh.notna().any() and nn.notna().any():
            per.append((hh.mean(),nn.mean()))
    per=np.array(per); dif=per[:,0]-per[:,1]
    dz=dif.mean()/dif.std(ddof=1)
    try: w,p=stats.wilcoxon(per[:,0],per[:,1])
    except Exception: p=np.nan
    rows.append(dict(dim=v,lab=LAB[v],hiit=float(per[:,0].mean()),nao=float(per[:,1].mean()),
                     d=float(dif.mean()),dz=float(dz),p=float(p),n=len(per)))
# BH-FDR sobre as 6 subescalas
pv=np.array([r['p'] for r in rows[:6]])
o=np.argsort(pv); rk=np.empty_like(o); rk[o]=np.arange(1,len(pv)+1)
adj=np.minimum.accumulate((pv*len(pv)/rk)[o][::-1])[::-1]; fdr=np.empty_like(adj); fdr[o]=np.clip(adj,0,1)
for i in range(6): rows[i]['fdr']=float(fdr[i])
for i in range(6,len(rows)): rows[i]['fdr']=None

print("=== HIIT (2,4,7) x SEM HIIT (1,3,5,6) — pareado por atleta ===")
print(f"{'dim':14s} {'HIIT':>6s} {'nao':>6s} {'d':>6s} {'dz':>6s} {'p':>7s} {'FDR':>7s}")
for r in rows:
    fdrs=f"{r['fdr']:.3f}" if r['fdr'] is not None else "  -  "
    star='*' if (r['fdr'] is not None and r['fdr']<0.05) else ('†' if r['p']<0.05 else '')
    print(f"{r['lab']:14s} {r['hiit']:6.2f} {r['nao']:6.2f} {r['d']:+6.2f} {r['dz']:+6.2f} {r['p']:7.3f} {fdrs:>7s} {star}")

# ---------- PERMANOVA HIIT vs nao (obs-level, perm restrita ao atleta) ----------
tt=h.dropna(subset=S).copy()
Z=((tt[S]-tt[S].mean())/tt[S].std(ddof=1)).values
gg=tt['HIIT'].values; ids=tt['ID'].values
def pf(g):
    a=2;N=len(Z);tot=((Z-Z.mean(0))**2).sum();wg=sum(((Z[g==l]-Z[g==l].mean(0))**2).sum() for l in np.unique(g))
    return (tot-wg)/(a-1)/(wg/(N-a)),(tot-wg)/tot
F0,R2=pf(gg);cnt=1;NP=9999
for _ in range(NP):
    gp=gg.copy()
    for aid in np.unique(ids):
        idx=np.where(ids==aid)[0];gp[idx]=rng.permutation(gg[idx])
    if pf(gp)[0]>=F0: cnt+=1
pperm=cnt/(NP+1)
print(f"\nPERMANOVA HIIT vs nao: pseudo-F={F0:.2f} R2={R2:.3f} p={pperm:.4f}")

out={'rows':rows,'permanova':{'F':round(float(F0),2),'R2':round(float(R2),3),'p':round(float(pperm),4)},
     'hiit_days':[2,4,7],'non_days':[1,3,5,6]}
json.dump(out,open('hiit_compara.json','w'))

# ---------- figura ----------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
COL={'Tensao':'#4d9de0','Depressao':'#c56bd6','Raiva':'#e0525b','Vigor':'#2f9e44','Fadiga':'#e8590c',
     'Confusao':'#f0a848','TMD':'#7048e8','FadFisica':'#e8590c','FadMental':'#d9480f'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(13,4.8),dpi=200)
# painel 1: dz por dimensao (todas)
allr=sorted(rows,key=lambda r:r['dz'])
yy=range(len(allr)); cols=[COL[r['dim']] for r in allr]
ax[0].barh(list(yy),[r['dz'] for r in allr],color=cols,alpha=.9,height=.66)
ax[0].axvline(0,color='#adb5bd',lw=.8)
ax[0].set_yticks(list(yy)); ax[0].set_yticklabels([r['lab'] for r in allr])
for i,r in zip(yy,allr):
    mk='*' if (r['fdr'] is not None and r['fdr']<0.05) else ('†' if r['p']<0.05 else '')
    if mk: ax[0].text(r['dz']+(0.03 if r['dz']>=0 else -0.03),i,mk,va='center',ha='left' if r['dz']>=0 else 'right',fontsize=13,color=cols[list(yy).index(i)])
ax[0].set_xlabel('dz (HIIT − sem HIIT), pareado por atleta')
ax[0].set_title('Diferença por dimensão nos dias de HIIT\n* FDR<0,05 · † p<0,05',fontweight='bold',fontsize=11,loc='left')
# painel 2: barras HIIT vs nao para as principais
key=['Vigor','Fadiga','FadFisica','TMD']
x=np.arange(len(key)); w=0.38
ax[1].bar(x-w/2,[[r for r in rows if r['dim']==k][0]['nao'] for k in key],w,label='sem HIIT',color='#adb5bd')
ax[1].bar(x+w/2,[[r for r in rows if r['dim']==k][0]['hiit'] for k in key],w,label='dias de HIIT',color='#e8590c')
ax[1].set_xticks(x); ax[1].set_xticklabels([LAB[k] for k in key]); ax[1].set_ylabel('escore médio')
ax[1].set_title('Estados nos dias de HIIT vs demais dias',fontweight='bold',fontsize=11,loc='left'); ax[1].legend(frameon=False,fontsize=9)
fig.suptitle(f'Dias com HIIT (2,4,7) versus sem HIIT (1,3,5,6) — PERMANOVA pseudo-F={F0:.2f}, p={pperm:.3f}'.replace('.',','),
             fontweight='bold',fontsize=12.5,y=1.02)
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/hiit_compara.png',bbox_inches='tight',facecolor='white')
print('[salvo hiit_compara.json + figura]')
