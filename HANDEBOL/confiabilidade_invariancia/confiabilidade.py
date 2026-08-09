# -*- coding: utf-8 -*-
"""Confiabilidade · significância · invariância (BRUMS × HIIT).

  A. CONFIABILIDADE por subescala: α de Cronbach (IC95%), ω de McDonald
     (a partir das cargas de 1 fator), r inter-item médio. Decisão de
     SIGNIFICÂNCIA prática: o IC do α exclui/atinge 0,70?
  B. INVARIÂNCIA de medida pré×pós: CFA por grupo (ajuste), congruência de
     cargas (Tucker φ) e cargas lado a lado. (ΔCFI formal exige lavaan/R.)

Autocontido: itens em ../analises_avancadas/itens_brums.csv (anonimizado).
Uso: python confiabilidade.py → resultados_confiabilidade.json + confiabilidade_fig.png
Dependências: numpy scipy pandas pingouin factor_analyzer matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
import pingouin as pg
from factor_analyzer import FactorAnalyzer
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore'); rng=np.random.RandomState(7)
HERE=os.path.dirname(os.path.abspath(__file__))
df=pd.read_csv(os.path.join(HERE,'..','analises_avancadas','itens_brums.csv'))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')
GROUPS={'Tensão':['tensao_1','tensao_2','tensao_3','tensao_4'],'Depressão':['depressao_1','depressao_2','depressao_3','depressao_4'],
        'Raiva':['raiva_1','raiva_2','raiva_3','raiva_4'],'Vigor':['vigor_1','vigor_2','vigor_3','vigor_4'],
        'Fadiga':['fadiga_1','fadiga_2','fadiga_3','fadiga_4'],'Confusão':['confusao_1','confusao_2','confusao_3','confusao_4']}
out={'n':int(len(df))}

# ---------- A. Confiabilidade ----------
def omega(X):
    Xv=X.dropna();
    if Xv.shape[0]<10 or Xv.std().min()<1e-6: return np.nan
    fa=FactorAnalyzer(n_factors=1,rotation=None,method='minres'); fa.fit(Xv)
    lam=fa.loadings_[:,0]; err=1-lam**2
    s=lam.sum(); return float(s*s/(s*s+err.sum()))
rowsA=[]
for s,items in GROUPS.items():
    X=df[items]
    try: a,ci=pg.cronbach_alpha(data=X.dropna())
    except Exception: a,ci=(np.nan,[np.nan,np.nan])
    cc=X.dropna().corr().values; rii=cc[np.triu_indices(len(items),1)].mean()
    om=omega(X)
    rowsA.append({'sub':s,'k':len(items),'alpha':round(float(a),3),'alpha_ic':[round(float(ci[0]),3),round(float(ci[1]),3)],
        'omega':round(om,3) if np.isfinite(om) else None,'r_inter_item':round(float(rii),3),
        'adequada':bool(a>=0.70),'ic_atinge_070':bool(ci[1]>=0.70)})
out['A_confiabilidade']=rowsA
print("A. Confiabilidade por subescala:")
for r in rowsA: print(f"   {r['sub']:10s} α={r['alpha']:.2f} IC[{r['alpha_ic'][0]:.2f};{r['alpha_ic'][1]:.2f}]  ω={r['omega']}  r_ii={r['r_inter_item']:.2f}  {'≥0,70 OK' if r['adequada'] else 'abaixo de 0,70'}")

# ---------- B. Invariância pré×pós (cargas por subescala via factor_analyzer) ----------
Mi=df[df['momento'].isin(['pre','pos'])].copy()
def loadings(dat):
    ld={}
    for s,items in GROUPS.items():
        X=dat[items].dropna()
        if X.shape[0]<10 or X.std().min()<1e-6:
            for it in items:
                if dat[it].std()>1e-6: ld[it]=np.nan
            continue
        fa=FactorAnalyzer(n_factors=1,rotation=None,method='minres'); fa.fit(X)
        for it,l in zip(items,fa.loadings_[:,0]): ld[it]=round(float(l),3)
    return ld
ldp=loadings(Mi[Mi.momento=='pre']); ldo=loadings(Mi[Mi.momento=='pos'])
ks=[k for k in ldp if k in ldo and np.isfinite(ldp[k]) and np.isfinite(ldo[k]) and abs(ldp[k])>1e-6 and abs(ldo[k])>1e-6]
a=np.array([ldp[k] for k in ks]); b=np.array([ldo[k] for k in ks])
tucker=float(np.sum(a*b)/np.sqrt(np.sum(a**2)*np.sum(b**2)))
# CFI por grupo já computado no módulo analises_avancadas (semopy)
try:
    aa=json.load(open(os.path.join(HERE,'..','analises_avancadas','resultados.json')))['invariance_pre_pos']
    cfi_pre=aa.get('CFI_pre'); cfi_pos=aa.get('CFI_pos'); dead=aa.get('itens_excluidos',[])
except Exception:
    cfi_pre=cfi_pos=None; dead=[]
inv={'itens_excluidos':dead,'n_pre':int((Mi.momento=='pre').sum()),'n_pos':int((Mi.momento=='pos').sum()),
     'CFI_pre':cfi_pre,'CFI_pos':cfi_pos,
     'tucker_phi':round(tucker,3),'invariancia_metrica':bool(tucker>=0.95),
     'cargas':{k:{'pre':ldp[k],'pos':ldo[k]} for k in ks},
     'nota':'cargas de 1 fator por subescala (factor_analyzer); CFI por grupo do módulo analises_avancadas; ΔCFI formal (configural→métrico→escalar) requer lavaan/R'}
out['B_invariancia']=inv
print(f"\nB. Invariância pré×pós: CFI pré={inv['CFI_pre']} pós={inv['CFI_pos']} · Tucker φ={inv['tucker_phi']} → {'métrica sustentada' if inv['invariancia_metrica'] else 'atenção'} (itens excluídos: {dead})")

json.dump(out,open(os.path.join(HERE,'resultados_confiabilidade.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ---------- figura ----------
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(1,2,figsize=(12.5,5),dpi=170)
A=sorted(rowsA,key=lambda r:r['alpha']); ax=axs[0]; y=np.arange(len(A))
ax.barh(y,[r['alpha'] for r in A],color=[P['TEAL'] if r['adequada'] else P['RED'] for r in A])
for i,r in enumerate(A):
    ax.plot(r['alpha_ic'],[i,i],color=P['NAVY'],lw=1.4,alpha=.6)
    if r['omega'] is not None: ax.plot(r['omega'],i,'D',color=P['GOLD'],ms=6)
ax.axvline(0.70,ls='--',color=P['MUT'],lw=1.2); ax.text(0.70,len(A)-0.4,' 0,70',fontsize=8,color=P['MUT'])
ax.set_yticks(y); ax.set_yticklabels([r['sub'] for r in A]); ax.set_xlim(0,1); ax.set_xlabel('α de Cronbach (IC95%) · ◆ = ω de McDonald')
for sp in['top','right']: ax.spines[sp].set_visible(False)
ax.set_title('A · Confiabilidade por subescala',fontsize=11,loc='left',color=P['NAVY'],fontweight='bold')
ax2=axs[1]
xv=[ldp[k] for k in ks]; yv=[ldo[k] for k in ks]
ax2.scatter(xv,yv,s=40,color=P['BLUE'],alpha=.75,edgecolor='white',lw=.6)
ax2.plot([min(xv+yv)-.05,1],[min(xv+yv)-.05,1],ls=':',color=P['GRID'])
ax2.set_xlabel('carga padronizada — PRÉ'); ax2.set_ylabel('carga padronizada — PÓS')
ax2.text(0.03,0.95,f'Tucker φ = {tucker:.3f}\n(≥0,95 → invariância métrica)',transform=ax2.transAxes,va='top',fontsize=9,color=P['NAVY'])
for sp in['top','right']: ax2.spines[sp].set_visible(False)
ax2.set_title('B · Invariância métrica pré×pós (cargas)',fontsize=11,loc='left',color=P['NAVY'],fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(HERE,'confiabilidade_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_confiabilidade.json + confiabilidade_fig.png")
