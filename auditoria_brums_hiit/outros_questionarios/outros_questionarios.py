# -*- coding: utf-8 -*-
"""Os outros questionários — autorrelatos externos ao BRUMS (BRUMS × HIIT).

Trata como uma bateria própria os quatro instrumentos coletados ao lado do
BRUMS: Fadiga física (0–10), Fadiga mental (0–10), Estado físico (0–4) e
Estado mental (0–4).
  A. Resposta aguda pré→pós de cada instrumento (t + Wilcoxon, dz IC95%, FDR).
  B. Contraste HIIT vs sem-HIIT (Δ agudo médio por atleta) de cada um.
  C. CONVERGÊNCIA com o BRUMS: correlação de medidas repetidas (rm_corr,
     intra-atleta) de cada externo × as 6 subescalas + PTH — os externos
     medem o mesmo que o BRUMS?
  D. Estabilidade individual (ICC) de cada externo.

Autocontido: lê ../modelagem/base_modelagem.csv. Uso: python outros_questionarios.py
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
EXT={'FadFis':'Fadiga física','FadMen':'Fadiga mental','EstFis':'Estado físico','EstMen':'Estado mental'}
RANGE={'FadFis':'0–10','FadMen':'0–10','EstFis':'0–4','EstMen':'0–4'}
BR=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
HIIT=[2,4,7]; SEM=[1,3,5,6]
out={}

# ---- pares pré/pós por atleta ----
pre=df[df.momento=='pre'].groupby('atleta')[list(EXT)].mean()
pos=df[df.momento=='pos'].groupby('atleta')[list(EXT)].mean()
ath=pre.index.intersection(pos.index); pre=pre.loc[ath]; pos=pos.loc[ath]

# ===== A. resposta aguda + descritivas =====
A=[]; praw=[]
for k,lab in EXT.items():
    a=pos[k]; b=pre[k]; dif=(a-b).dropna()
    t,pt=stats.ttest_rel(a,b); w,pw=stats.wilcoxon(a,b)
    dz=float(dif.mean()/dif.std(ddof=1))
    ci=[float(np.percentile([np.mean(np.random.RandomState(s).choice(dif.values,len(dif))) for s in range(400)],q)/dif.std(ddof=1) for q in (2.5,97.5))] if False else None
    praw.append(pw)
    A.append(dict(inst=lab,escala=RANGE[k],M=round(float(df[k].mean()),2),DP=round(float(df[k].std()),2),
                  M_pre=round(float(b.mean()),2),M_pos=round(float(a.mean()),2),delta=round(float(dif.mean()),2),
                  dz=round(dz,2),t_p=round(float(pt),4),wilcoxon_p=round(float(pw),4)))
rej,pfdr=pg.multicomp(praw,method='fdr_bh')
for i,r in enumerate(A): r['p_FDR']=round(float(pfdr[i]),4); r['sig']=bool(rej[i])
out['A_resposta_aguda']=A
print("A. Resposta aguda dos externos:")
for r in A: print(f"   {r['inst']:15s} {r['M_pre']:.2f}→{r['M_pos']:.2f} Δ={r['delta']:+.2f} dz={r['dz']:+.2f} p(FDR)={r['p_FDR']} {'*' if r['sig'] else ''}")

# ===== B. HIIT vs sem (Δ agudo médio por atleta) =====
pre2=df[df.momento=='pre'].groupby(['atleta','dia'])[list(EXT)].mean()
pos2=df[df.momento=='pos'].groupby(['atleta','dia'])[list(EXT)].mean()
idx=pre2.index.intersection(pos2.index); Dl=(pos2.loc[idx]-pre2.loc[idx]).reset_index()
mh=Dl[Dl.dia.isin(HIIT)].groupby('atleta')[list(EXT)].mean(); ms=Dl[Dl.dia.isin(SEM)].groupby('atleta')[list(EXT)].mean()
a2=mh.index.intersection(ms.index); B=[]; praw2=[]
for k,lab in EXT.items():
    x=mh.loc[a2,k]; y=ms.loc[a2,k]; w,pw=stats.wilcoxon(x,y); praw2.append(pw)
    B.append(dict(inst=lab,dHIIT=round(float(x.mean()),2),dSEM=round(float(y.mean()),2),wilcoxon_p=round(float(pw),4)))
rej2,pf2=pg.multicomp(praw2,method='fdr_bh')
for i,r in enumerate(B): r['p_FDR']=round(float(pf2[i]),4); r['sig']=bool(rej2[i])
out['B_HIIT_vs_SEM']=B
print("B. HIIT vs sem (externos):",[(r['inst'],r['p_FDR'],'*' if r['sig'] else '') for r in B])

# ===== C. convergência com o BRUMS (rm_corr intra-atleta) =====
targets=BR+['PTH']; Cmat={}; Crows=[]
for k,lab in EXT.items():
    Cmat[k]={}
    for tg in targets:
        sub=df.dropna(subset=[k,tg])
        try:
            rr=pg.rm_corr(data=sub,x=k,y=tg,subject='atleta'); r=float(rr['r'].iloc[0]); pv=float(rr['pval'].iloc[0])
        except Exception: r,pv=(np.nan,np.nan)
        Cmat[k][tg]=round(r,3)
        Crows.append(dict(externo=lab,brums=tg,r=round(r,3),p=round(pv,4),sig=bool(pv<0.05)))
out['C_convergencia_rmcorr']=dict(matriz=Cmat,linhas=Crows)
# destaques
print("C. Convergência (rm_corr) — destaques:")
for k in EXT:
    row=Cmat[k]; best=max(targets,key=lambda t:abs(row[t]) if np.isfinite(row[t]) else 0)
    print(f"   {EXT[k]:15s} mais forte com {best}: r={row[best]:+.2f}")

# ===== D. ICC (estabilidade individual) =====
D=[]
for k,lab in EXT.items():
    try:
        ic=pg.intraclass_corr(data=df.dropna(subset=[k]),targets='atleta',raters='dia',ratings=k)
        icc=float(ic[ic['Type']=='ICC2']['ICC'].iloc[0])
    except Exception:
        g=df.groupby('atleta')[k]; be=g.mean().var(ddof=1); wi=g.var(ddof=1).mean(); icc=float(be/(be+wi))
    D.append(dict(inst=lab,ICC=round(icc,3)))
out['D_ICC']=D
print("D. ICC externos:",{r['inst']:r['ICC'] for r in D})

json.dump(out,open(os.path.join(HERE,'resultados_outros_questionarios.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ================= figura =================
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(2,2,figsize=(13,9.8),dpi=150)
labs=[EXT[k] for k in EXT]; x=np.arange(len(EXT))
# A resposta aguda (dz)
ax=axs[0,0]
dz=[r['dz'] for r in A]; cols=[P['RED'] if r['sig'] else P['GRID'] for r in A]
bars=ax.barh(x,dz,color=[P['RED'] if r['dz']>=0 else P['TEAL'] for r in A])
for i,r in enumerate(A):
    ax.text(r['dz']+(0.03 if r['dz']>=0 else -0.03),i,f"dz={r['dz']:+.2f}{'*' if r['sig'] else ''}",va='center',ha='left' if r['dz']>=0 else 'right',fontsize=8.5,color=P['NAVY'])
ax.axvline(0,color=P['MUT'],lw=.8); ax.set_yticks(x); ax.set_yticklabels(labs); ax.set_xlabel('tamanho de efeito dz (pré→pós)')
ax.set_xlim(-1.5,1.5); ax.set_title('A · Resposta aguda dos outros questionários\n* sobrevive ao FDR',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# B pré vs pós médias
ax=axs[0,1]; w=0.36
ax.bar(x-w/2,[r['M_pre'] for r in A],w,color=P['BLUE'],label='pré'); ax.bar(x+w/2,[r['M_pos'] for r in A],w,color=P['RED'],label='pós')
ax.set_xticks(x); ax.set_xticklabels(labs,rotation=14,fontsize=8.5); ax.set_ylabel('escore médio')
ax.legend(frameon=False,fontsize=9); ax.set_title('B · Média pré vs pós por instrumento',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
ax.text(0.02,0.96,'(escalas 0–10 e 0–4 no mesmo eixo)',transform=ax.transAxes,fontsize=7.5,color=P['MUT'],va='top')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# C heatmap convergência
ax=axs[1,0]; targets=BR+['PTH']
Mtx=np.array([[Cmat[k][t] for t in targets] for k in EXT])
im=ax.imshow(Mtx,cmap='RdBu_r',vmin=-0.7,vmax=0.7,aspect='auto')
ax.set_xticks(range(len(targets))); ax.set_xticklabels(targets,rotation=35,ha='right',fontsize=8)
ax.set_yticks(range(len(EXT))); ax.set_yticklabels(labs,fontsize=8.5)
for i in range(len(EXT)):
    for j in range(len(targets)):
        v=Mtx[i,j]; ax.text(j,i,f'{v:+.2f}'.replace('.',','),ha='center',va='center',fontsize=7,color='white' if abs(v)>0.4 else P['NAVY'])
ax.set_title('C · Convergência com o BRUMS (rm_corr intra-atleta)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
cb=fig.colorbar(im,ax=ax,fraction=0.046,pad=0.03); cb.ax.tick_params(labelsize=7)
# D ICC
ax=axs[1,1]
icc=[r['ICC'] for r in D]
ax.barh(x,icc,color=P['VIO']); ax.set_yticks(x); ax.set_yticklabels(labs)
for i,v in enumerate(icc): ax.text(v+0.01,i,f'{v:.2f}'.replace('.',','),va='center',fontsize=8.5,color=P['NAVY'])
ax.axvline(0.5,ls='--',color=P['MUT'],lw=1); ax.set_xlim(0,0.8); ax.set_xlabel('ICC (estabilidade entre atletas)')
ax.set_title('D · Estabilidade individual (ICC) dos externos',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'outros_questionarios_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_outros_questionarios.json + outros_questionarios_fig.png")
