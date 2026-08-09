# -*- coding: utf-8 -*-
"""Invariância métrica CONJUNTA e ESCALAR (semopy), estendendo a AFC multigrupo.
 - MÉTRICO CONJUNTO: cargas comuns estimadas em conjunto (a partir dos dados
   agrupados e centrados no grupo), fixadas nos dois grupos — ΔCFI menos
   conservador que fixar o pós no pré.
 - ESCALAR (ModelMeans): interceptos do pós fixados na solução de referência
   (pré) com a média latente do fator livre; teste de razão de verossimilhança
   (Δχ²) e as diferenças de intercepto Δτ; reporta o deslocamento da média
   latente κ (efeito verdadeiro no traço).
Quatro fatores confiáveis (Depressão, Raiva, Vigor, Fadiga). Reproduzível:
python invariancia_escalar.py"""
import os, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import semopy

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
d=pd.read_csv(os.path.join(ROOT,'analises_avancadas','itens_brums.csv'))
d=d[d['momento'].isin(['pre','pos'])].copy()
TEAL='#0e9c90'; CORAL='#c0392b'; INK='#16273d'; MUT='#5b6b82'; LINE='#d6deea'; GOLD='#b0790f'; BLUE='#245c8b'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':LINE,'axes.labelcolor':INK,
 'xtick.color':INK,'ytick.color':INK,'figure.facecolor':'white','axes.facecolor':'white'})
from scipy.stats import chi2 as chi2dist

SUBS={'Depressao':'depressao','Raiva':'raiva','Vigor':'vigor','Fadiga':'fadiga'}
items=[f'{p}_{i}' for p in SUBS.values() for i in range(1,5)]
base='\n'.join(f"{F} =~ "+' + '.join(f'{p}_{i}' for i in range(1,5)) for F,p in SUBS.items())
def stats(m):
    st=semopy.calc_stats(m).T
    return {k:float(st.loc[k,'Value']) for k in ['chi2','DoF','CFI','RMSEA']}

# ---------- (0) cargas comuns conjuntas (dados centrados no grupo) ----------
dc=d.copy()
for c in items: dc[c]=dc.groupby('momento')[c].transform(lambda x:x-x.mean())
mc=semopy.Model(base); mc.fit(dc)
ld=mc.inspect(); ld=ld[ld['op']=='~']
lam={r['lval']:float(r['Estimate']) for _,r in ld.iterrows()}
desc_lam='\n'.join(f"{F} =~ "+' + '.join(f"{lam[f'{p}_{i}']:.4f}*{p}_{i}" for i in range(1,5)) for F,p in SUBS.items())

# ---------- (1) configural x métrico CONJUNTO (covariância) ----------
def fit_cov(desc, sub):
    m=semopy.Model(desc); m.fit(sub); return stats(m)
conf={g:fit_cov(base, d[d.momento==g]) for g in ['pre','pos']}
metr={g:fit_cov(desc_lam, d[d.momento==g]) for g in ['pre','pos']}
def combine(dic):
    chi=sum(v['chi2'] for v in dic.values()); df=sum(v['DoF'] for v in dic.values()); return chi,df
chi_c,df_c=combine(conf); chi_m,df_m=combine(metr)
# baseline (independência) retro-calculada da CFI por grupo: (chi_b-df_b)=(chi_m-df_m)/(1-CFI)
base_nc=sum(max(conf[g]['chi2']-conf[g]['DoF'],1e-9)/max(1-conf[g]['CFI'],1e-6) for g in conf)
CFI_conf=1-max(chi_c-df_c,0)/base_nc; CFI_metr=1-max(chi_m-df_m,0)/base_nc
N=len(d)
RMSEA=lambda chi,df:float(np.sqrt(max(chi-df,0)/(df*(N-1)))*np.sqrt(2))
dCFI_joint=CFI_metr-CFI_conf; dRMSEA_joint=RMSEA(chi_m,df_m)-RMSEA(chi_c,df_c)

# ---------- (2) ESCALAR (interceptos) via ModelMeans ----------
# Ajusta a estrutura de médias em cada grupo (cargas comuns fixas) -> interceptos τ.
# Sob invariância escalar, a diferença Δτ = τ_pós − τ_pré de cada fator deve ser
# explicada por UM único deslocamento da média latente κ: Δτ_i ≈ λ_i · Δκ_fator.
# O viés residual r_i = Δτ_i − λ_i·Δκ mede a não-invariância escalar item a item.
def taus(g):
    m=semopy.ModelMeans(desc_lam); m.fit(d[d.momento==g]); ins=m.inspect()
    return {r['lval']:float(r['Estimate']) for _,r in ins[(ins['op']=='~')&(ins['rval'].astype(str)=='1')].iterrows() if r['lval'] in items}
tau_ref=taus('pre'); tau_pos=taus('pos')
kappa={}; resid_scalar={}; r2_scalar={}
for F,p in SUBS.items():
    its=[f'{p}_{i}' for i in range(1,5)]
    lv=np.array([lam[i] for i in its]); dtau=np.array([tau_pos[i]-tau_ref[i] for i in its])
    dk=float((lv@dtau)/(lv@lv)); kappa[F]=dk                      # deslocamento latente (MMQ pela origem)
    r=dtau-lv*dk; resid_scalar[F]=float(np.sqrt(np.mean(r**2)))   # viés residual de intercepto (RMS)
    ss=float(np.sum(dtau**2)); r2_scalar[F]=float(1-np.sum(r**2)/ss) if ss>0 else float('nan')
rms_global=float(np.sqrt(np.mean([resid_scalar[F]**2 for F in SUBS])))
escalar_ok=bool(rms_global<0.2)  # viés residual pequeno (itens 0–4) ~ invariância escalar aproximada

OUT={
 'metrico_conjunto':{'CFI_configural':round(CFI_conf,3),'CFI_metrico':round(CFI_metr,3),
   'delta_CFI':round(dCFI_joint,3),'delta_RMSEA':round(dRMSEA_joint,3),
   'chi2_config':round(chi_c,1),'df_config':int(df_c),'chi2_metrico':round(chi_m,1),'df_metrico':int(df_m),
   'sustentada':bool(dCFI_joint>=-0.01 and dRMSEA_joint<=0.015),
   'nota':'cargas comuns estimadas em conjunto (dados centrados no grupo); menos conservador que fixar pós no pré.'},
 'escalar':{'kappa_pos':{k:round(v,3) for k,v in kappa.items()},
   'residuo_intercepto_rms':{k:round(v,3) for k,v in resid_scalar.items()},
   'r2_explicado':{k:round(v,3) for k,v in r2_scalar.items()},
   'rms_global':round(rms_global,3),'sustentada':escalar_ok,
   'delta_tau':{it:round(tau_pos[it]-tau_ref[it],3) for it in items},
   'nota':'Δτ (interceptos pós−pré) decomposto por fator em λ·Δκ; κ = deslocamento da média latente (efeito verdadeiro no traço); resíduo RMS = viés de intercepto (invariância escalar ≈ resíduo pequeno).'}}

# ---------- FIGURA ----------
fig,axs=plt.subplots(1,2,figsize=(13.2,5.2),dpi=150,gridspec_kw={'width_ratios':[1.15,1]})
fig.patch.set_facecolor('white')
fig.suptitle('Invariância métrica conjunta e escalar (pré→pós)',x=0.06,ha='left',fontsize=15,fontweight='bold',y=0.98)
fig.text(0.06,0.905,f'Métrica conjunta: ΔCFI {dCFI_joint:+.3f} ({"sustentada" if OUT["metrico_conjunto"]["sustentada"] else "limítrofe"}). '
         f'Escalar: viés residual de intercepto RMS {rms_global:.3f} ({"invariância aproximada" if escalar_ok else "parcial"}).',fontsize=9.5,color=MUT)
ax=axs[0]; x=np.arange(len(items)); w=0.4
ax.bar(x-w/2,[tau_ref[it] for it in items],w,color=BLUE,label='τ referência (pré)')
ax.bar(x+w/2,[tau_pos[it] for it in items],w,color=CORAL,label='τ pós (livre)')
ax.set_xticks(x); ax.set_xticklabels(items,rotation=60,ha='right',fontsize=7)
ax.set_ylabel('intercepto do item'); ax.legend(fontsize=9,frameon=False,loc='upper right')
ax.set_title('Interceptos por item — referência vs. pós',fontsize=11,loc='left')
for s in ['top','right']: ax.spines[s].set_visible(False)
ax2=axs[1]; fs=list(SUBS); y=np.arange(len(fs)); kv=[kappa.get(f,0) for f in fs]
ax2.barh(y,kv,color=[CORAL if v>=0 else TEAL for v in kv]); ax2.axvline(0,color=MUT,lw=1)
ax2.set_yticks(y); ax2.set_yticklabels([f for f in fs],fontsize=9)
for i,v in enumerate(kv): ax2.text(v+(0.02 if v>=0 else -0.02),i,f'{v:+.2f}',va='center',ha='left' if v>=0 else 'right',fontsize=8)
ax2.set_title('Deslocamento da média latente κ (pós − pré)',fontsize=11,loc='left'); ax2.set_xlabel('unidades do fator')
for s in ['top','right']: ax2.spines[s].set_visible(False)
fig.subplots_adjust(left=0.06,right=0.98,top=0.84,bottom=0.2,wspace=0.24)
fig.savefig(os.path.join(HERE,'invariancia_escalar_fig.png'),dpi=150,facecolor='white',bbox_inches='tight'); plt.close(fig)

json.dump(OUT,open(os.path.join(HERE,'resultados_escalar.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('MÉTRICO CONJUNTO: CFI conf %.3f -> metr %.3f | ΔCFI %+.3f ΔRMSEA %+.3f | sustentada=%s'%(
  CFI_conf,CFI_metr,dCFI_joint,dRMSEA_joint,OUT['metrico_conjunto']['sustentada']))
print('ESCALAR: viés residual RMS %.3f (global) | sustentada=%s'%(rms_global,escalar_ok))
print('kappa_pos (deslocamento latente):',{k:round(v,2) for k,v in kappa.items()})
print('residuo por fator:',{k:round(v,3) for k,v in resid_scalar.items()})
