# -*- coding: utf-8 -*-
import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')
plt.rcParams.update({'font.family':'DejaVu Sans','axes.edgecolor':P['MUT'],'axes.labelcolor':P['NAVY'],
    'xtick.color':P['MUT'],'ytick.color':P['MUT'],'axes.titlecolor':P['NAVY']})
FIG='/home/user/mdlucca/auditoria_brums_hiit/figuras/'
def sty(ax):
    for s in ['top','right']: ax.spines[s].set_visible(False)
    ax.grid(axis='x',color=P['GRID'],lw=1); ax.set_axisbelow(True)

mod=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/modelagem/resultados_modelagem.json'))
adv=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/analises_avancadas/resultados.json'))
LAB={'PTH':'PTH (TMD)','FadFis':'Fadiga física','Fadiga':'Fadiga','Vigor':'Vigor','FadMen':'Fadiga mental',
     'Tensão':'Tensão','Depressão':'Depressão','Raiva':'Raiva','Confusão':'Confusão'}

# --- M1: resposta aguda dz (FDR) ---
A=[r for r in mod['A_resposta_aguda'] if 'dz' in r]
A=sorted(A,key=lambda r:r['dz'])
fig,ax=plt.subplots(figsize=(7,4.4),dpi=170)
cols=[P['RED'] if r['signif_FDR'] and r['dz']>0 else (P['TEAL'] if r['signif_FDR'] else P['MUT']) for r in A]
ax.barh([LAB[r['y']] for r in A],[r['dz'] for r in A],color=cols)
for i,r in enumerate(A):
    ax.text(r['dz']+(0.03 if r['dz']>=0 else -0.03),i,f"{r['dz']:+.2f}{'*' if r['signif_FDR'] else ''}",
            va='center',ha='left' if r['dz']>=0 else 'right',fontsize=9,color=P['NAVY'])
ax.axvline(0,color=P['MUT'],lw=1); sty(ax); ax.set_xlabel('dz (agregado por atleta)')
ax.set_title('Resposta aguda pré→pós — modelo misto (* sobrevive ao FDR)',fontsize=11,loc='left')
fig.tight_layout(); fig.savefig(FIG+'M1_resposta_aguda_dz.png',facecolor='white'); plt.close()

# --- M2: acúmulo (inclinação/dia) ---
B=mod['B_acumulo_microciclo']
fig,ax=plt.subplots(figsize=(6.6,3.4),dpi=170)
cols=[P['RED'] if b['inclinacao_por_dia']>0 else P['TEAL'] for b in B]
ax.barh([LAB[b['y']] for b in B],[b['inclinacao_por_dia'] for b in B],color=cols)
for i,b in enumerate(B):
    ax.text(b['inclinacao_por_dia']+(0.01 if b['inclinacao_por_dia']>=0 else -0.01),i,
            f"{b['inclinacao_por_dia']:+.2f}/dia  p={b['p']:.3f}",va='center',
            ha='left' if b['inclinacao_por_dia']>=0 else 'right',fontsize=9,color=P['NAVY'])
ax.axvline(0,color=P['MUT'],lw=1); sty(ax); ax.set_xlabel('inclinação por dia (modelo de crescimento)')
ax.set_xlim(-0.5,0.75)
ax.set_title('Acúmulo no microciclo — inclinação aleatória por atleta',fontsize=11,loc='left')
fig.tight_layout(); fig.savefig(FIG+'M2_acumulo_inclinacao.png',facecolor='white'); plt.close()

# --- M3: efeito HIIT nível do dia ---
C=mod['C_efeito_HIIT_nivel_dia']
fig,ax=plt.subplots(figsize=(6.6,3.4),dpi=170)
cols=[P['RED'] if c['efeito_HIIT']>0 else P['TEAL'] for c in C]
ax.barh([LAB[c['y']] for c in C],[c['efeito_HIIT'] for c in C],color=cols)
for i,c in enumerate(C):
    ax.text(c['efeito_HIIT']+(0.03 if c['efeito_HIIT']>=0 else -0.03),i,
            f"{c['efeito_HIIT']:+.2f}  p={c['p']:.3f}",va='center',
            ha='left' if c['efeito_HIIT']>=0 else 'right',fontsize=9,color=P['NAVY'])
ax.axvline(0,color=P['MUT'],lw=1); sty(ax); ax.set_xlabel('Δ HIIT − técnico-tático (nível do dia)')
ax.set_xlim(-1.1,3.0)
ax.set_title('Efeito do HIIT vs. técnico-tático (dias 2–7)',fontsize=11,loc='left')
fig.tight_layout(); fig.savefig(FIG+'M3_efeito_hiit.png',facecolor='white'); plt.close()

# --- A1: CFA loadings grouped by subscale ---
GROUPS={'Tensão':['tensao_1','tensao_2','tensao_3','tensao_4'],'Depressão':['depressao_1','depressao_2','depressao_3','depressao_4'],
 'Raiva':['raiva_1','raiva_2','raiva_3','raiva_4'],'Vigor':['vigor_1','vigor_2','vigor_3','vigor_4'],
 'Fadiga':['fadiga_1','fadiga_2','fadiga_3','fadiga_4'],'Confusão':['confusao_1','confusao_2','confusao_3','confusao_4']}
ld=adv['CFA_DWLS']['loadings_std']
fig,ax=plt.subplots(figsize=(8,4.2),dpi=170)
palette=[P['BLUE'],P['VIO'],P['RED'],P['TEAL'],P['GOLD'],P['NAVY']]
x=0; ticks=[]; tlab=[]
for gi,(s,items) in enumerate(GROUPS.items()):
    for it in items:
        v=ld.get(it,0); ax.bar(x,v,color=palette[gi],width=0.8); ticks.append(x); tlab.append(it.split('_')[1]); x+=1
    x+=0.8
ax.set_xticks(ticks); ax.set_xticklabels(tlab,fontsize=7)
ax.axhline(0.4,color=P['MUT'],ls='--',lw=1); ax.text(x,0.41,'0,40',fontsize=8,color=P['MUT'])
for s2 in ['top','right']: ax.spines[s2].set_visible(False)
ax.grid(axis='y',color=P['GRID'],lw=1); ax.set_axisbelow(True); ax.set_ylabel('carga padronizada')
ax.set_ylim(0,1)
ax.set_title('CFA (DWLS) — cargas padronizadas por subescala (CFI 0,921; RMSEA 0,055)',fontsize=10.5,loc='left')
import matplotlib.patches as mp
ax.legend([mp.Patch(color=palette[i]) for i in range(6)],list(GROUPS),ncol=6,fontsize=8,frameon=False,loc='upper center',bbox_to_anchor=(0.5,-0.12))
fig.tight_layout(); fig.savefig(FIG+'A1_cfa_cargas.png',facecolor='white'); plt.close()

# --- A2: HTMT heatmap ---
SUBS=list(GROUPS); H=np.full((6,6),np.nan)
for k,v in adv['HTMT'].items():
    a,b=k.split('~'); i=SUBS.index(a); j=SUBS.index(b); H[i,j]=v; H[j,i]=v
np.fill_diagonal(H,np.nan)
fig,ax=plt.subplots(figsize=(6,5),dpi=170)
im=ax.imshow(H,cmap='YlOrRd',vmin=0,vmax=1)
ax.set_xticks(range(6)); ax.set_yticks(range(6)); ax.set_xticklabels(SUBS,rotation=40,ha='right',fontsize=9); ax.set_yticklabels(SUBS,fontsize=9)
for i in range(6):
    for j in range(6):
        if not np.isnan(H[i,j]): ax.text(j,i,f'{H[i,j]:.2f}',ha='center',va='center',fontsize=8,color='#222' if H[i,j]<0.7 else 'white')
cb=fig.colorbar(im,fraction=0.046,pad=0.04); cb.set_label('HTMT')
ax.set_title('HTMT (correlações policóricas) — máx 0,846 < 0,85',fontsize=10.5,loc='left')
fig.tight_layout(); fig.savefig(FIG+'A2_htmt.png',facecolor='white'); plt.close()

# --- A3: GRM discriminations ---
grm=adv['GRM_discrimination']
fig,ax=plt.subplots(figsize=(8,4),dpi=170); x=0; ticks=[]; tlab=[]
for gi,(s,items) in enumerate(GROUPS.items()):
    a=grm[s]['a']
    for k,val in enumerate(a):
        ax.bar(x,val,color=palette[gi],width=0.8); ticks.append(x); tlab.append(f"{s[:3]}{k+1}"); x+=1
    x+=0.8
ax.set_xticks(ticks); ax.set_xticklabels(tlab,fontsize=7,rotation=45,ha='right')
for s2 in ['top','right']: ax.spines[s2].set_visible(False)
ax.grid(axis='y',color=P['GRID'],lw=1); ax.set_axisbelow(True); ax.set_ylabel('discriminação a (TRI)')
ax.set_title('TRI — discriminação por item (Modelo de Resposta Graduada)',fontsize=10.5,loc='left')
fig.tight_layout(); fig.savefig(FIG+'A3_grm.png',facecolor='white'); plt.close()

# --- A4: Bayes factors (log scale) ---
bf=adv['bayes_JZS_agregado_por_atleta']
name={'FadFis':'Fadiga física','esc_vigor':'Vigor','PTH':'PTH','esc_fadiga':'Fadiga','esc_confusao':'Confusão',
      'esc_tensao':'Tensão','esc_depressao':'Depressão','esc_raiva':'Raiva','FadMen':'Fadiga mental'}
items=sorted(bf.items(),key=lambda kv:kv[1]['BF10'])
fig,ax=plt.subplots(figsize=(7,4.2),dpi=170)
vals=[v['BF10'] for _,v in items]; labs=[name.get(k,k) for k,_ in items]
cols=[P['RED'] if v>=3 else (P['TEAL'] if v<=1/3 else P['MUT']) for v in vals]
ax.barh(labs,np.log10(vals),color=cols)
for i,v in enumerate(vals):
    ax.text(np.log10(v)+(0.05 if v>=1 else -0.05),i,f'{v:.2f}' if v<100 else f'{v:.0f}',va='center',
            ha='left' if v>=1 else 'right',fontsize=9,color=P['NAVY'])
for xv,lab in [(np.log10(3),'3'),(np.log10(1/3),'1/3')]:
    ax.axvline(xv,color=P['MUT'],ls='--',lw=1)
ax.axvline(0,color=P['NAVY'],lw=1)
sty(ax); ax.set_xlabel('log₁₀ BF₁₀  (direita=efeito, esquerda=equivalência)')
ax.set_title('Fator de Bayes JZS — Δ agudo pré→pós (agregado por atleta)',fontsize=10.5,loc='left')
fig.tight_layout(); fig.savefig(FIG+'A4_bayes.png',facecolor='white'); plt.close()

print("figuras geradas:", sorted(__import__('os').listdir(FIG)))
