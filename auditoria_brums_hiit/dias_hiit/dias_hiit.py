# -*- coding: utf-8 -*-
"""Comparação entre os dias do microciclo (BRUMS × HIIT).

Três contrastes sobre a RESPOSTA AGUDA (Δ = pós − pré) por atleta-dia:
  A. Entre os dias de HIIT (D2 vs D4 vs D7) — as três sessões são
     equivalentes ou há tendência (habituação/acúmulo)?  Friedman + Wilcoxon
     pareado par-a-par (FDR).
  B. Entre os dias SEM HIIT (D1, D3, D5, D6) — os dias técnico-táticos são
     equivalentes entre si?  Friedman.
  C. HIIT vs SEM HIIT — média da resposta aguda de cada atleta nos dias de
     HIIT contra a dos dias sem HIIT (Wilcoxon pareado + t, dz e RBC, FDR).

Autocontido: lê ../modelagem/base_modelagem.csv. Uso: python dias_hiit.py
Dependências: numpy pandas scipy pingouin matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats
import pingouin as pg
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')
df=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
VARS={'PTH':'PTH (TMD)','FadFis':'Fadiga física','Vigor':'Vigor','Fadiga':'Fadiga','FadMen':'Fadiga mental'}
HIIT=[2,4,7]; SEM=[1,3,5,6]
# ---- Δ agudo (pós−pré) por atleta-dia ----
pre=df[df.momento=='pre'].groupby(['atleta','dia'])[list(VARS)].mean()
pos=df[df.momento=='pos'].groupby(['atleta','dia'])[list(VARS)].mean()
idx=pre.index.intersection(pos.index)
D=(pos.loc[idx]-pre.loc[idx]).reset_index()
out={'n_obs_delta':int(len(D)),'dias_hiit':HIIT,'dias_sem':SEM}

def fried(days, v):
    M=D[D.dia.isin(days)].pivot_table(index='atleta',columns='dia',values=v)
    M=M.dropna()
    if M.shape[0]<5 or M.shape[1]<2: return None
    chi,p=stats.friedmanchisquare(*[M[c].values for c in M.columns])
    return dict(n=int(M.shape[0]),k=int(M.shape[1]),chi2=round(float(chi),3),p=round(float(p),4),
                medias={int(c):round(float(M[c].mean()),2) for c in M.columns})

# ===== A. entre dias de HIIT =====
A={}
for v,lab in VARS.items():
    fr=fried(HIIT,v)
    pares=[]
    Mh=D[D.dia.isin(HIIT)].pivot_table(index='atleta',columns='dia',values=v)
    for a,b in [(2,4),(2,7),(4,7)]:
        s=Mh[[a,b]].dropna()
        if len(s)>=5:
            w,pw=stats.wilcoxon(s[a],s[b]); pares.append(dict(par=f'D{a}–D{b}',n=int(len(s)),p=round(float(pw),4)))
    A[v]=dict(label=lab,friedman=fr,pares=pares)
out['A_entre_HIIT']=A
print("A. Entre dias de HIIT (Friedman sobre Δ agudo):")
for v,o in A.items():
    fr=o['friedman']; print(f"   {o['label']:14s} médias {fr['medias']}  χ²={fr['chi2']} p={fr['p']} {'(diferem)' if fr['p']<0.05 else '(equivalentes)'}")

# ===== B. entre dias SEM HIIT =====
B={}
for v,lab in VARS.items():
    B[v]=dict(label=lab,friedman=fried(SEM,v))
out['B_entre_SEM']=B
print("B. Entre dias SEM HIIT (Friedman sobre Δ agudo):")
for v,o in B.items():
    fr=o['friedman']; print(f"   {o['label']:14s} médias {fr['medias']}  χ²={fr['chi2']} p={fr['p']} {'(diferem)' if fr['p']<0.05 else '(equivalentes)'}")

# ===== C. HIIT vs SEM (média por atleta) =====
mh=D[D.dia.isin(HIIT)].groupby('atleta')[list(VARS)].mean()
ms=D[D.dia.isin(SEM)].groupby('atleta')[list(VARS)].mean()
ath=mh.index.intersection(ms.index)
C=[]; praw=[]
for v,lab in VARS.items():
    a=mh.loc[ath,v]; b=ms.loc[ath,v]; dif=(a-b).dropna()
    t,pt=stats.ttest_rel(a,b); w,pw=stats.wilcoxon(a,b)
    dz=float(dif.mean()/dif.std(ddof=1))
    try: rbc=float(pg.wilcoxon(a,b)['RBC'].iloc[0])
    except Exception: rbc=np.nan
    praw.append(pw)
    C.append(dict(var=lab,media_HIIT=round(float(a.mean()),2),media_SEM=round(float(b.mean()),2),
                  dif=round(float(dif.mean()),2),dz=round(dz,2),RBC=round(rbc,2) if np.isfinite(rbc) else None,
                  t_p=round(float(pt),4),wilcoxon_p=round(float(pw),4)))
rej,pfdr=pg.multicomp(praw,method='fdr_bh')
for i,r in enumerate(C): r['p_FDR']=round(float(pfdr[i]),4); r['sig']=bool(rej[i])
out['C_HIIT_vs_SEM']=dict(n_atletas=int(len(ath)),resultados=C)
print("C. HIIT vs SEM (Δ agudo médio por atleta):")
for r in C: print(f"   {r['var']:14s} HIIT {r['media_HIIT']:+.2f} vs SEM {r['media_SEM']:+.2f}  dz={r['dz']:+.2f} p(FDR)={r['p_FDR']} {'*' if r['sig'] else ''}")

# ===== trajetória diária (nível médio por dia) =====
lvl=df.groupby('dia')['PTH'].mean()
out['trajetoria_PTH_por_dia']={int(d):round(float(lvl[d]),2) for d in lvl.index}

json.dump(out,open(os.path.join(HERE,'resultados_dias_hiit.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ================= figura =================
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(2,2,figsize=(13,9.5),dpi=150)
vs=list(VARS); labs=[VARS[v] for v in vs]; x=np.arange(len(vs))
# A dias de HIIT
ax=axs[0,0]; w=0.26; cols=[P['GOLD'],P['RED'],P['NAVY']]
for j,dd in enumerate(HIIT):
    vals=[A[v]['friedman']['medias'].get(dd,np.nan) for v in vs]
    ax.bar(x+(j-1)*w,vals,w,color=cols[j],label=f'D{dd}')
ax.axhline(0,color=P['MUT'],lw=.8); ax.set_xticks(x); ax.set_xticklabels(labs,rotation=18,fontsize=8)
ax.set_ylabel('Δ agudo médio (pós−pré)'); ax.legend(frameon=False,fontsize=8,ncol=3,loc='upper right')
ann=' · '.join(f"{VARS[v].split()[0]} p={A[v]['friedman']['p']:.2f}".replace('.',',') for v in ['PTH','FadFis'])
ax.set_title('A · Entre dias de HIIT (D2/D4/D7)\nFriedman: '+ann,fontsize=10,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# B dias sem HIIT
ax=axs[0,1]; w=0.2; colsB=[P['TEAL'],P['BLUE'],P['VIO'],P['GRID']]
for j,dd in enumerate(SEM):
    vals=[B[v]['friedman']['medias'].get(dd,np.nan) for v in vs]
    ax.bar(x+(j-1.5)*w,vals,w,color=colsB[j],label=f'D{dd}')
ax.axhline(0,color=P['MUT'],lw=.8); ax.set_xticks(x); ax.set_xticklabels(labs,rotation=18,fontsize=8)
ax.set_ylabel('Δ agudo médio (pós−pré)'); ax.legend(frameon=False,fontsize=8,ncol=4,loc='upper right')
annB=' · '.join(f"{VARS[v].split()[0]} p={B[v]['friedman']['p']:.2f}".replace('.',',') for v in ['PTH','FadFis'])
ax.set_title('B · Entre dias SEM HIIT (D1/D3/D5/D6)\nFriedman: '+annB,fontsize=10,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# C HIIT vs SEM
ax=axs[1,0]; w=0.36
mh_=[r['media_HIIT'] for r in C]; ms_=[r['media_SEM'] for r in C]
ax.bar(x-w/2,mh_,w,color=P['RED'],label='dias de HIIT'); ax.bar(x+w/2,ms_,w,color=P['TEAL'],label='dias sem HIIT')
ax.axhline(0,color=P['MUT'],lw=.8); ax.set_xticks(x); ax.set_xticklabels(labs,rotation=18,fontsize=8)
ax.set_ylabel('Δ agudo médio por atleta'); ax.legend(frameon=False,fontsize=8.5)
for i,r in enumerate(C):
    if r['sig']:
        yv=max(r['media_HIIT'],r['media_SEM']); ax.text(i,yv+0.12,'*',ha='center',fontsize=15,color=P['NAVY'])
ax.set_title('C · HIIT vs sem HIIT (Δ agudo)\n* = diferença significativa (FDR)',fontsize=10,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# D trajetória diária PTH
ax=axs[1,1]; days=sorted(lvl.index); yv=[lvl[d] for d in days]
ax.plot(days,yv,'-o',color=P['BLUE'],lw=2,ms=6,zorder=2)
for d in days:
    ax.scatter([d],[lvl[d]],s=130,color=(P['RED'] if d in HIIT else P['TEAL']),zorder=3,edgecolor='white',lw=1)
ax.set_xlabel('dia do microciclo'); ax.set_ylabel('PTH médio (nível do dia)')
import matplotlib.patches as mp
ax.legend(handles=[mp.Patch(color=P['RED'],label='dia de HIIT'),mp.Patch(color=P['TEAL'],label='dia sem HIIT')],frameon=False,fontsize=8.5,loc='upper left')
ax.set_title('D · Nível médio de PTH por dia (D1→D7)',fontsize=10,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'dias_hiit_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_dias_hiit.json + dias_hiit_fig.png")
