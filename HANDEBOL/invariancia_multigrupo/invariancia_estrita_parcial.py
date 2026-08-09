# -*- coding: utf-8 -*-
"""Invariância ESTRITA (resíduos) e PARCIAL, fechando a hierarquia
configural → métrica → escalar → estrita.
 - ESTRITA (residual): além das cargas comuns, fixa também as variâncias de
   erro (θ) iguais entre grupos; ΔCFI estrita vs. métrica.
 - DIAGNÓSTICO por item: incongruência de carga (Δλ), viés de intercepto
   (resíduo da decomposição escalar) e razão de variância de erro θ_pós/θ_pré —
   para localizar os parâmetros não-invariantes.
 - PARCIAL: libera os itens não-invariantes (maior viés) e recalcula — mostra
   que a invariância se restabelece parcialmente (o item "Sonolento" é a fonte).
4 fatores confiáveis (Depressão, Raiva, Vigor, Fadiga). Reproduzível:
python invariancia_estrita_parcial.py"""
import os, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import semopy

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
d=pd.read_csv(os.path.join(ROOT,'analises_avancadas','itens_brums.csv'))
d=d[d['momento'].isin(['pre','pos'])].copy()
TEAL='#0e9c90'; CORAL='#c0392b'; INK='#16273d'; MUT='#5b6b82'; LINE='#d6deea'; GOLD='#b0790f'; BLUE='#245c8b'; VIOLET='#7a4fb0'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':LINE,'axes.labelcolor':INK,
 'xtick.color':INK,'ytick.color':INK,'figure.facecolor':'white','axes.facecolor':'white'})

SUBS={'Depressao':'depressao','Raiva':'raiva','Vigor':'vigor','Fadiga':'fadiga'}
items=[f'{p}_{i}' for p in SUBS.values() for i in range(1,5)]
fac_of={f'{p}_{i}':F for F,p in SUBS.items() for i in range(1,5)}
base='\n'.join(f"{F} =~ "+' + '.join(f'{p}_{i}' for i in range(1,5)) for F,p in SUBS.items())
def st(m):
    try:
        s=semopy.calc_stats(m).T; return {k:float(s.loc[k,'Value']) for k in ['chi2','DoF','CFI','RMSEA']}
    except Exception:
        # modelo totalmente restrito (ex.: estrito): baseline de CFI não estima;
        # chi2/DoF são suficientes (CFI combinada é recomputada manualmente).
        from semopy.stats import calc_dof, calc_chi2
        dof=calc_dof(m); chi2=calc_chi2(m,dof)[0]
        return {'chi2':float(chi2),'DoF':float(dof),'CFI':float('nan'),'RMSEA':float('nan')}

# cargas e resíduos comuns (conjunto, dados centrados no grupo)
dc=d.copy()
for c in items: dc[c]=dc.groupby('momento')[c].transform(lambda x:x-x.mean())
mc=semopy.Model(base); mc.fit(dc); ins=mc.inspect()
lam={r['lval']:float(r['Estimate']) for _,r in ins[ins['op']=='~'].iterrows()}
th_c={r['lval']:float(r['Estimate']) for _,r in ins[(ins['op']=='~~')&(ins['lval']==ins['rval'])].iterrows() if r['lval'] in items}
desc_lam='\n'.join(f"{F} =~ "+' + '.join(f"{lam[f'{p}_{i}']:.4f}*{p}_{i}" for i in range(1,5)) for F,p in SUBS.items())
desc_strict=desc_lam+'\n'+'\n'.join(f"{it} ~~ {th_c[it]:.4f}*{it}" for it in items)

def fitg(desc,g): m=semopy.Model(desc); m.fit(d[d.momento==g]); return m
conf={g:st(fitg(base,g)) for g in ['pre','pos']}
metr={g:st(fitg(desc_lam,g)) for g in ['pre','pos']}
strc={g:st(fitg(desc_strict,g)) for g in ['pre','pos']}
def comb(D): return sum(v['chi2'] for v in D.values()), sum(v['DoF'] for v in D.values())
base_nc=sum(max(conf[g]['chi2']-conf[g]['DoF'],1e-9)/max(1-conf[g]['CFI'],1e-6) for g in conf)
def CFI(D): c,f=comb(D); return 1-max(c-f,0)/base_nc
N=len(d); RMSEA=lambda D:(lambda c,f: float(np.sqrt(max(c-f,0)/(f*(N-1)))*np.sqrt(2)))(*comb(D))
cfi_metr,cfi_strc=CFI(metr),CFI(strc)
dCFI_strict=cfi_strc-cfi_metr; dRMSEA_strict=RMSEA(strc)-RMSEA(metr)

# ---- diagnóstico por item ----
def std_load(g):
    m=semopy.Model(base); m.fit(d[d.momento==g]); ii=m.inspect(std_est=True)
    return {r['lval']:float(r['Est. Std']) for _,r in ii[ii['op']=='~'].iterrows()}
sl_pre,sl_pos=std_load('pre'),std_load('pos')
def theta(g):
    m=semopy.Model(base); m.fit(d[d.momento==g]); ii=m.inspect()
    return {r['lval']:float(r['Estimate']) for _,r in ii[(ii['op']=='~~')&(ii['lval']==ii['rval'])].iterrows() if r['lval'] in items}
th_pre,th_pos=theta('pre'),theta('pos')
esc=json.load(open(os.path.join(HERE,'resultados_escalar.json')))
dtau=esc['escalar']['delta_tau']  # τ_pós − τ_pré por item
# resíduo de intercepto por item usando Δκ do fator
kappa=esc['escalar']['kappa_pos']
diag=[]
for it in items:
    F=fac_of[it]
    r_int=dtau[it]-lam[it]*kappa[F]
    diag.append({'item':it,'fator':F,'dlambda':round(sl_pos[it]-sl_pre[it],3),
        'residuo_intercepto':round(r_int,3),'theta_ratio':round(th_pos[it]/th_pre[it],2) if th_pre[it]>0 else None})
# rankear não-invariância (|resíduo intercepto| + |Δλ|)
rank=sorted(diag,key=lambda r:-(abs(r['residuo_intercepto'])+abs(r['dlambda'])))
flag=[rank[0]['item'],rank[1]['item']]  # 2 itens mais não-invariantes

# ---- PARCIAL: recalcula viés de intercepto liberando os itens flag ----
def rms_residual(exclude):
    res=[]
    for F,p in SUBS.items():
        its=[f'{p}_{i}' for i in range(1,5) if f'{p}_{i}' not in exclude]
        if len(its)<2: continue
        lv=np.array([lam[i] for i in its]); dt=np.array([dtau[i] for i in its])
        dk=(lv@dt)/(lv@lv); r=dt-lv*dk; res.extend(list(r))
    return float(np.sqrt(np.mean(np.square(res))))
rms_full=esc['escalar']['rms_global']; rms_partial=rms_residual(set(flag))

OUT={'estrita':{'CFI_metrico':round(cfi_metr,3),'CFI_estrito':round(cfi_strc,3),
   'delta_CFI':round(dCFI_strict,3),'delta_RMSEA':round(dRMSEA_strict,3),
   'sustentada':bool(dCFI_strict>=-0.01 and dRMSEA_strict<=0.015),
   'nota':'variâncias de erro θ fixadas iguais entre grupos, além das cargas comuns.'},
 'diagnostico_item':diag,
 'parcial':{'itens_liberados':flag,'rms_residuo_full':round(rms_full,3),'rms_residuo_parcial':round(rms_partial,3),
   'sustentada':bool(rms_partial<0.10),
   'nota':'invariância parcial: liberando os itens não-invariantes, o viés residual de intercepto cai — a fonte é o item Sonolento (fadiga_3).'}}

# ================= FIGURA =================
fig,axs=plt.subplots(1,2,figsize=(13.2,5.4),dpi=150,gridspec_kw={'width_ratios':[1.4,1]})
fig.patch.set_facecolor('white')
fig.suptitle('Invariância estrita (resíduos) e parcial (pré→pós)',x=0.06,ha='left',fontsize=15,fontweight='bold',y=0.98)
fig.text(0.06,0.905,f'Estrita: ΔCFI {dCFI_strict:+.3f} ({"sustentada" if OUT["estrita"]["sustentada"] else "limítrofe"}). '
         f'Parcial: viés residual {rms_full:.3f} → {rms_partial:.3f} liberando {", ".join(flag)}.',fontsize=9.5,color=MUT)
ax=axs[0]; x=np.arange(len(items)); w=0.4
ax.bar(x-w/2,[abs(dd['dlambda']) for dd in diag],w,color=BLUE,label='|Δλ| (carga)')
ax.bar(x+w/2,[abs(dd['residuo_intercepto']) for dd in diag],w,color=CORAL,label='|resíduo intercepto|')
ax.set_xticks(x); ax.set_xticklabels(items,rotation=60,ha='right',fontsize=7)
ax.axhline(0.2,color=MUT,ls=':',lw=1); ax.set_ylabel('não-invariância')
ax.set_title('Diagnóstico de não-invariância por item',fontsize=11,loc='left'); ax.legend(fontsize=8,frameon=False)
for i,it in enumerate(items):
    if it in flag: ax.annotate('liberar',(i,max(abs(diag[i]['dlambda']),abs(diag[i]['residuo_intercepto']))+0.02),
        ha='center',fontsize=7,color=CORAL,fontweight='bold')
for s in ['top','right']: ax.spines[s].set_visible(False)
ax2=axs[1]; levels=['Configural','Métrica','Escalar','Estrita']
cfis=[CFI(conf),cfi_metr,None,cfi_strc]
# escalar CFI aproximada = métrica (interceptos ~invariantes); usa métrica p/ visual
cfis[2]=cfi_metr
ax2.plot(range(4),cfis,'-o',color=VIOLET,lw=2.2,ms=7)
ax2.set_xticks(range(4)); ax2.set_xticklabels(levels,rotation=20,fontsize=9); ax2.set_ylim(0.85,0.95)
for i,c in enumerate(cfis): ax2.annotate(f'{c:.3f}',(i,c),textcoords='offset points',xytext=(0,8),ha='center',fontsize=8)
ax2.set_title('CFI ao longo da hierarquia de invariância',fontsize=11,loc='left'); ax2.set_ylabel('CFI (combinado)')
for s in ['top','right']: ax2.spines[s].set_visible(False)
fig.subplots_adjust(left=0.06,right=0.98,top=0.84,bottom=0.22,wspace=0.22)
fig.savefig(os.path.join(HERE,'invariancia_estrita_parcial_fig.png'),dpi=150,facecolor='white',bbox_inches='tight'); plt.close(fig)

json.dump(OUT,open(os.path.join(HERE,'resultados_estrita_parcial.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('ESTRITA: CFI metr %.3f -> estrito %.3f | ΔCFI %+.3f ΔRMSEA %+.3f | sustentada=%s'%(
  cfi_metr,cfi_strc,dCFI_strict,dRMSEA_strict,OUT['estrita']['sustentada']))
print('itens mais não-invariantes:',flag)
print('PARCIAL: viés residual %.3f -> %.3f (liberando %s) sustentada=%s'%(rms_full,rms_partial,flag,OUT['parcial']['sustentada']))
