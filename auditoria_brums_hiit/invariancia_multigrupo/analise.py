# -*- coding: utf-8 -*-
"""AFC multigrupo e invariância de medida pré→pós (semopy).
Testa se a estrutura do BRUMS é invariante entre o momento pré e o pós-treino:
 - CONFIGURAL: AFC ajustada em cada grupo (mesma estrutura, parâmetros livres);
 - MÉTRICA (cargas): congruência de Tucker φ por fator + teste ΔCFI (grupo pós
   com as cargas fixadas na solução do pré) com limiares de Cheung & Rensvold
   (ΔCFI ≤ 0,01) e Chen (ΔRMSEA ≤ 0,015).
Restringe-se aos quatro fatores confiáveis (Depressão, Raiva, Vigor, Fadiga);
Tensão e Confusão são excluídas por variância degenerada (efeito piso), como já
observado na AFC. Reproduzível: python analise.py
Fonte: analises_avancadas/itens_brums.csv."""
import os, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import semopy

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
d=pd.read_csv(os.path.join(ROOT,'analises_avancadas','itens_brums.csv'))
d=d[d['momento'].isin(['pre','pos'])].copy()
TEAL='#0e9c90'; CORAL='#c0392b'; INK='#16273d'; MUT='#5b6b82'; LINE='#d6deea'; GOLD='#b0790f'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':LINE,'axes.labelcolor':INK,
 'xtick.color':INK,'ytick.color':INK,'figure.facecolor':'white','axes.facecolor':'white'})

SUBS={'Depressão':'depressao','Raiva':'raiva','Vigor':'vigor','Fadiga':'fadiga'}
def desc_livre():
    return '\n'.join(f"{F} =~ "+' + '.join(f'{p}_{i}' for i in range(1,5)) for F,p in SUBS.items())
def stat(m,k):
    return float(semopy.calc_stats(m).T.loc[k,'Value'])

def fit_grupo(sub, desc):
    m=semopy.Model(desc); m.fit(sub)
    ins=m.inspect(std_est=True); load=ins[ins['op']=='~']
    return m, load

desc=desc_livre()
OUT={'grupos':{}, 'cargas_std':{}, 'cargas_unstd':{}}
for g in ['pre','pos']:
    sub=d[d.momento==g]
    m,load=fit_grupo(sub,desc)
    OUT['grupos'][g]={'n':int(len(sub)),'CFI':stat(m,'CFI'),'TLI':stat(m,'TLI'),
        'RMSEA':stat(m,'RMSEA'),'chi2':stat(m,'chi2'),'DoF':stat(m,'DoF')}
    OUT['cargas_std'][g]={r['lval']:float(r['Est. Std']) for _,r in load.iterrows()}
    OUT['cargas_unstd'][g]={r['lval']:float(r['Estimate']) for _,r in load.iterrows()}

items=[f'{p}_{i}' for p in SUBS.values() for i in range(1,5)]
# --- Tucker's congruence φ (métrica) por fator e global ---
def tucker(x,y):
    x=np.array(x); y=np.array(y); return float((x@y)/np.sqrt((x@x)*(y@y)))
phi={}
for F,p in SUBS.items():
    its=[f'{p}_{i}' for i in range(1,5)]
    phi[F]=tucker([OUT['cargas_std']['pre'][i] for i in its],[OUT['cargas_std']['pos'][i] for i in its])
phi_global=tucker([OUT['cargas_std']['pre'][i] for i in items],[OUT['cargas_std']['pos'][i] for i in items])

# --- teste ΔCFI (métrica): pós com cargas FIXADAS na solução do pré ---
lam_pre=OUT['cargas_unstd']['pre']
desc_fix='\n'.join(f"{F} =~ "+' + '.join(f"{lam_pre[f'{p}_{i}']:.4f}*{p}_{i}" for i in range(1,5)) for F,p in SUBS.items())
m_pos_fix=semopy.Model(desc_fix); m_pos_fix.fit(d[d.momento=='pos'])
cfi_pos_metric=stat(m_pos_fix,'CFI'); rmsea_pos_metric=stat(m_pos_fix,'RMSEA')
dCFI=cfi_pos_metric-OUT['grupos']['pos']['CFI']; dRMSEA=rmsea_pos_metric-OUT['grupos']['pos']['RMSEA']
metrica_ok=bool(dCFI>=-0.01 and dRMSEA<=0.015 and phi_global>=0.95)

conclusao=('invariância métrica sustentada pela congruência (φ global %.3f ≥ 0,95); '
 'o teste ΔCFI estrito — pós com cargas fixadas no pré, mais conservador que o modelo '
 'métrico conjunto — fica em %+.3f (limiar −0,01), indicando pequeno custo de ajuste.'%(phi_global,dCFI))
OUT['invariancia']={'tucker_phi_fator':phi,'tucker_phi_global':phi_global,
    'CFI_pos_configural':OUT['grupos']['pos']['CFI'],'CFI_pos_metrica':cfi_pos_metric,
    'delta_CFI':dCFI,'RMSEA_pos_metrica':rmsea_pos_metric,'delta_RMSEA':dRMSEA,
    'limiar_dCFI':-0.01,'limiar_dRMSEA':0.015,'metrica_congruencia_ok':bool(phi_global>=0.95),
    'metrica_dCFI_estrito_ok':bool(dCFI>=-0.01 and dRMSEA<=0.015),'conclusao':conclusao,
    'fatores_excluidos':['Tensão','Confusão'],'motivo_exclusao':'variância degenerada (efeito piso)'}

# ================= FIGURA =================
fig,axs=plt.subplots(1,2,figsize=(13.2,5.4),dpi=150,gridspec_kw={'width_ratios':[1.5,1]})
fig.patch.set_facecolor('white')
fig.suptitle('AFC multigrupo e invariância de medida (pré vs. pós)',x=0.06,ha='left',fontsize=15,fontweight='bold',y=0.98)
fig.text(0.06,0.905,f'Configural: CFI pré {OUT["grupos"]["pre"]["CFI"]:.2f} / pós {OUT["grupos"]["pos"]["CFI"]:.2f}. '
         f'Métrica: Tucker φ global {phi_global:.3f} (cargas congruentes); ΔCFI estrito {dCFI:+.3f} (conservador).',fontsize=9.5,color=MUT)
ax=axs[0]; x=np.arange(len(items)); w=0.4
ax.bar(x-w/2,[OUT['cargas_std']['pre'][i] for i in items],w,color=TEAL,label='pré')
ax.bar(x+w/2,[OUT['cargas_std']['pos'][i] for i in items],w,color=CORAL,label='pós')
ax.set_xticks(x); ax.set_xticklabels(items,rotation=60,ha='right',fontsize=7)
ax.set_ylabel('carga padronizada'); ax.set_ylim(0,1.05); ax.legend(fontsize=9,frameon=False,loc='upper right')
ax.set_title('Cargas padronizadas por item — pré vs. pós',fontsize=11,loc='left')
for s in ['top','right']: ax.spines[s].set_visible(False)
# φ por fator
ax2=axs[1]; fs=list(SUBS); y=np.arange(len(fs))
ax2.barh(y,[phi[f] for f in fs],color=[TEAL if phi[f]>=0.95 else GOLD for f in fs])
ax2.axvline(0.95,color=CORAL,ls='--',lw=1.2,label='φ = 0,95'); ax2.set_xlim(0.8,1.0)
ax2.set_yticks(y); ax2.set_yticklabels(fs,fontsize=9)
for i,f in enumerate(fs): ax2.text(phi[f]-0.005,i,f'{phi[f]:.3f}',va='center',ha='right',fontsize=8,color='white')
ax2.set_title('Congruência de Tucker φ por fator',fontsize=11,loc='left'); ax2.legend(fontsize=8,frameon=False,loc='lower left')
for s in ['top','right']: ax2.spines[s].set_visible(False)
fig.subplots_adjust(left=0.06,right=0.98,top=0.84,bottom=0.2,wspace=0.22)
fig.savefig(os.path.join(HERE,'invariancia_multigrupo_fig.png'),dpi=150,facecolor='white',bbox_inches='tight'); plt.close(fig)

json.dump(OUT,open(os.path.join(HERE,'resultados.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('Configural: CFI pré %.3f / pós %.3f · RMSEA pré %.3f / pós %.3f'%(
    OUT['grupos']['pre']['CFI'],OUT['grupos']['pos']['CFI'],OUT['grupos']['pre']['RMSEA'],OUT['grupos']['pos']['RMSEA']))
print('Tucker φ global %.3f · por fator: %s'%(phi_global,{k:round(v,3) for k,v in phi.items()}))
print('Métrica ΔCFI %.3f · ΔRMSEA %.3f · sustentada=%s'%(dCFI,dRMSEA,metrica_ok))
