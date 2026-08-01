# -*- coding: utf-8 -*-
"""Derivadas por variável e por atleta (BRUMS × HIIT).

Estende o cálculo de derivadas a TODAS as variáveis do eixo humor:
  A. Trajetória diária f(t) por variável (ajuste cúbico), com a DERIVADA
     f'(t) (velocidade de mudança) e a 2ª derivada f''(t) (aceleração).
  B. Quantidades de cálculo por variável: velocidade inicial f'(1), final
     f'(7), dia de |velocidade| máxima, inclinação média (derivada linear).
  C. DERIVADA INDIVIDUAL: inclinação (dV/dia) de cada atleta por regressão
     linear — média, DP e % positivas — quantificando a heterogeneidade da
     "velocidade" de resposta entre atletas.

Autocontido: lê ../modelagem/base_modelagem.csv. Uso: python derivadas_variaveis.py
Dependências: numpy pandas matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GREEN='#2E8B57',GRID='#E3E9F0')
df=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
VARS={'PTH':'PTH (TMD)','FadFis':'Fadiga física','Fadiga':'Fadiga','FadMen':'Fadiga mental','Vigor':'Vigor'}
COL={'PTH':P['NAVY'],'FadFis':P['RED'],'Fadiga':P['GOLD'],'FadMen':P['VIO'],'Vigor':P['TEAL']}
t=np.arange(1,8,dtype=float)
out={'variaveis':list(VARS.values())}

# ---------- A/B ajuste cúbico + derivadas ----------
fits={}; rowsB=[]
for k,lab in VARS.items():
    y=df.groupby('dia')[k].mean().reindex(range(1,8)).values
    c=np.polyfit(t,y,3); d1=np.polyder(c); d2=np.polyder(c,2)
    fits[k]=dict(c=c,d1=d1,d2=d2,y=y)
    fp=np.polyval(d1,t); fpp=np.polyval(d2,t)
    slope_lin=float(np.polyfit(t,y,1)[0])
    imax=int(t[np.argmax(np.abs(fp))])
    rowsB.append(dict(var=lab,vel_inicial=round(float(fp[0]),2),vel_final=round(float(fp[-1]),2),
                      dia_vel_max=imax,inclinacao_media=round(slope_lin,2),
                      direcao=('acumula' if slope_lin>0.05 else ('cai' if slope_lin<-0.05 else 'estável'))))
out['B_derivadas_variaveis']=rowsB
print("A/B. Derivadas por variável (velocidade média/dia):")
for r in rowsB: print(f"   {r['var']:14s} f'(1)={r['vel_inicial']:+.2f} f'(7)={r['vel_final']:+.2f} incl.média={r['inclinacao_media']:+.2f} → {r['direcao']}")

# ---------- C derivada individual (inclinação por atleta) ----------
C=[]; perath={}
for k,lab in VARS.items():
    sl=[]
    for a,g in df.groupby('atleta'):
        if g.dia.nunique()>=3: sl.append(float(np.polyfit(g.dia,g[k],1)[0]))
    sl=np.array(sl); perath[k]=sl
    C.append(dict(var=lab,slope_medio=round(float(sl.mean()),3),slope_dp=round(float(sl.std(ddof=1)),3),
                  pct_positivo=round(100*float((sl>0).mean()),0),n=int(len(sl)),
                  min=round(float(sl.min()),2),max=round(float(sl.max()),2)))
out['C_derivada_individual']=C
print("C. Derivada individual (dV/dia por atleta) — heterogeneidade:")
for r in C: print(f"   {r['var']:14s} média {r['slope_medio']:+.2f} DP {r['slope_dp']:.2f} · {r['pct_positivo']:.0f}% positivas · [{r['min']};{r['max']}]")

json.dump(out,open(os.path.join(HERE,'resultados_derivadas_variaveis.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ================= figura =================
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(2,2,figsize=(13,9.6),dpi=150)
tg=np.linspace(1,7,300)
# A trajetórias padronizadas
ax=axs[0,0]
for k,lab in VARS.items():
    y=fits[k]['y']; z=(np.polyval(fits[k]['c'],tg)-y.mean())/y.std()
    ax.plot(tg,z,'-',color=COL[k],lw=2,label=lab)
    ax.plot(t,(y-y.mean())/y.std(),'o',color=COL[k],ms=4,alpha=.5)
ax.axhline(0,color=P['MUT'],lw=.8); ax.set_xlabel('dia (t)'); ax.set_ylabel('trajetória padronizada (z)')
ax.legend(fontsize=8,frameon=False,ncol=2); ax.set_title('A · Trajetórias f(t) (ajuste cúbico, z)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# B velocidade f'(t) por variável
ax=axs[0,1]
for k,lab in VARS.items():
    ax.plot(tg,np.polyval(fits[k]['d1'],tg),'-',color=COL[k],lw=2,label=lab)
ax.axhline(0,color=P['MUT'],lw=.8); ax.set_xlabel('dia (t)'); ax.set_ylabel("f'(t) — velocidade (pts/dia)")
ax.legend(fontsize=8,frameon=False,ncol=2); ax.set_title("B · Derivada f'(t) — velocidade de mudança",fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# C inclinação média (derivada linear) por variável
ax=axs[1,0]; ks=list(VARS); x=np.arange(len(ks))
vals=[r['inclinacao_media'] for r in rowsB]
ax.bar(x,vals,color=[COL[k] for k in ks])
ax.axhline(0,color=P['MUT'],lw=.8); ax.set_xticks(x); ax.set_xticklabels([VARS[k] for k in ks],rotation=16,fontsize=8.5)
for i,v in enumerate(vals): ax.text(i,v+(0.02 if v>=0 else -0.02),f'{v:+.2f}',ha='center',va='bottom' if v>=0 else 'top',fontsize=9,color=P['NAVY'])
ax.set_ylabel('inclinação média (pts/dia)'); ax.set_title('C · Derivada média por variável\n(acúmulo/dia no microciclo)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# D derivada individual — distribuição das inclinações por atleta
ax=axs[1,1]
data=[perath[k] for k in ks]
bp=ax.boxplot(data,positions=x,widths=0.6,patch_artist=True,showfliers=False)
for i,b in enumerate(bp['boxes']): b.set(facecolor=COL[ks[i]],alpha=.45,edgecolor=COL[ks[i]])
for med in bp['medians']: med.set(color=P['NAVY'],lw=1.4)
for i,k in enumerate(ks):
    xs=np.random.RandomState(1).normal(i,0.06,len(perath[k]))
    ax.scatter(xs,perath[k],s=12,color=COL[k],alpha=.6,edgecolor='white',lw=.4)
ax.axhline(0,color=P['MUT'],lw=1,ls='--'); ax.set_xticks(x); ax.set_xticklabels([VARS[k] for k in ks],rotation=16,fontsize=8.5)
ax.set_ylabel('inclinação por atleta (dV/dia)'); ax.set_title('D · Derivada INDIVIDUAL por atleta\n(heterogeneidade da velocidade)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'derivadas_variaveis_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_derivadas_variaveis.json + derivadas_variaveis_fig.png")
