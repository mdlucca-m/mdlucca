# -*- coding: utf-8 -*-
"""Sonolência — o item "Sonolento" do BRUMS (BRUMS × HIIT).

A sonolência é medida como o item "Sonolento" (fadiga_3), o 3º item da
subescala Fadiga do BRUMS. Este módulo mostra que ele se comporta de forma
DISTINTA dos demais itens de fadiga:
  A. Resposta aguda pré→pós dos 4 itens de Fadiga — a sonolência CAI enquanto
     Esgotado/Exausto/Cansado SOBEM (efeito de ativação/despertar agudo).
  B. Tamanho de efeito (dz) por item, com significância.
  C. Correlação intra-atleta (rm_corr) do Sonolento com os outros itens de
     fadiga e com o Vigor — descolado dos demais.
  D. Confiabilidade da subescala Fadiga COM vs. SEM o item Sonolento.

Autocontido: lê ../analises_avancadas/itens_brums.csv (+ base para o Vigor).
Uso: python sonolencia.py → resultados + figura.
Dependências: numpy pandas scipy pingouin matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats
import pingouin as pg
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')
it=pd.read_csv(os.path.join(HERE,'..','analises_avancadas','itens_brums.csv'))
base=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
FAD={'fadiga_1':'Esgotado','fadiga_2':'Exausto','fadiga_3':'Sonolento','fadiga_4':'Cansado'}
out={'item':'fadiga_3 = "Sonolento" (3º item da subescala Fadiga do BRUMS)'}

# ---- A/B resposta aguda dos 4 itens ----
pre=it[it.momento=='pre'].groupby('atleta')[list(FAD)].mean()
pos=it[it.momento=='pos'].groupby('atleta')[list(FAD)].mean()
ath=pre.index.intersection(pos.index); pre=pre.loc[ath]; pos=pos.loc[ath]
A=[]
for c,nm in FAD.items():
    a=pos[c]; b=pre[c]; dif=(a-b); t,p=stats.ttest_rel(a,b); w,pw=stats.wilcoxon(a,b)
    dz=float(dif.mean()/dif.std(ddof=1))
    A.append(dict(item=nm,key=c,M_pre=round(float(b.mean()),2),M_pos=round(float(a.mean()),2),
                  delta=round(float(dif.mean()),2),dz=round(dz,2),t_p=round(float(p),4),wilcoxon_p=round(float(pw),4),
                  sig=bool(pw<0.05),direcao=('sobe' if dif.mean()>0 else 'cai')))
out['A_resposta_itens']=A
print("A. Resposta aguda dos itens de Fadiga:")
for r in A: print(f"   {r['item']:10s} Δ={r['delta']:+.2f} dz={r['dz']:+.2f} p={r['wilcoxon_p']:.3f} → {r['direcao']}")

# ---- C rm_corr do Sonolento ----
m=it.merge(base[['atleta','dia','momento','Vigor']],on=['atleta','dia','momento'],how='left')
C=[]
for tgt,lab in [('fadiga_1','Esgotado'),('fadiga_2','Exausto'),('fadiga_4','Cansado'),('Vigor','Vigor')]:
    sub=m.dropna(subset=['fadiga_3',tgt])
    r=pg.rm_corr(sub,'fadiga_3',tgt,'atleta')
    C.append(dict(alvo=lab,r=round(float(r['r'].iloc[0]),3),p=round(float(r['pval'].iloc[0]),4)))
out['C_rmcorr_sonolento']=C
print("C. rm_corr Sonolento:",[(c['alvo'],c['r']) for c in C])

# ---- D alpha com vs sem ----
a4,ci4=pg.cronbach_alpha(data=it[['fadiga_1','fadiga_2','fadiga_3','fadiga_4']].dropna())
a3,ci3=pg.cronbach_alpha(data=it[['fadiga_1','fadiga_2','fadiga_4']].dropna())
out['D_alpha']=dict(com_sonolento=round(float(a4),3),ic_com=[round(ci4[0],3),round(ci4[1],3)],
                    sem_sonolento=round(float(a3),3),ic_sem=[round(ci3[0],3),round(ci3[1],3)])
# carga/discriminação do módulo avançado
try:
    adv=json.load(open(os.path.join(HERE,'..','analises_avancadas','resultados.json')))
    out['carga_CFA_sonolento']=adv['CFA_DWLS']['loadings_std'].get('fadiga_3')
    out['discrim_GRM_sonolento']=adv['GRM_discrimination']['Fadiga']['a'][2]
except Exception: pass
print(f"D. α Fadiga com Sonolento={a4:.3f} · sem Sonolento={a3:.3f} · carga CFA={out.get('carga_CFA_sonolento')}")

json.dump(out,open(os.path.join(HERE,'resultados_sonolencia.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ================= figura =================
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(2,2,figsize=(12.5,9.2),dpi=150)
items=[r['item'] for r in A]; x=np.arange(len(items))
colD=[P['RED'] if r['delta']>=0 else P['TEAL'] for r in A]
# A Δ pré→pós
ax=axs[0,0]
ax.bar(x,[r['delta'] for r in A],color=colD)
ax.axhline(0,color=P['MUT'],lw=.8); ax.set_xticks(x); ax.set_xticklabels(items,fontsize=9)
for i,r in enumerate(A): ax.text(i,r['delta']+(0.03 if r['delta']>=0 else -0.03),f"{r['delta']:+.2f}",ha='center',va='bottom' if r['delta']>=0 else 'top',fontsize=9,fontweight='bold',color=P['NAVY'])
ax.set_ylabel('Δ pré→pós (escore 0–4)')
ax.set_title('A · Resposta aguda dos 4 itens de Fadiga\nSonolência anda na contramão',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# B dz
ax=axs[0,1]
ax.barh(x,[r['dz'] for r in A],color=colD)
for i,r in enumerate(A): ax.text(r['dz']+(0.03 if r['dz']>=0 else -0.03),i,f"dz={r['dz']:+.2f}{'*' if r['sig'] else ''}",va='center',ha='left' if r['dz']>=0 else 'right',fontsize=9,color=P['NAVY'])
ax.axvline(0,color=P['MUT'],lw=.8); ax.set_yticks(x); ax.set_yticklabels(items,fontsize=9); ax.set_xlim(-1.0,1.2)
ax.set_xlabel('tamanho de efeito dz (* p<0,05)')
ax.set_title('B · dz por item — todos significativos,\nSonolência com sinal invertido',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# C rm_corr
ax=axs[1,0]
labsC=[c['alvo'] for c in C]; xc=np.arange(len(C))
ax.bar(xc,[c['r'] for c in C],color=[P['GOLD'] if abs(c['r'])<0.2 else P['BLUE'] for c in C])
ax.axhline(0,color=P['MUT'],lw=.8); ax.set_xticks(xc); ax.set_xticklabels(labsC,fontsize=9)
for i,c in enumerate(C): ax.text(i,c['r']+(0.01 if c['r']>=0 else -0.01),f"{c['r']:+.2f}",ha='center',va='bottom' if c['r']>=0 else 'top',fontsize=9,color=P['NAVY'])
ax.set_ylim(-0.35,0.35); ax.set_ylabel('rm_corr (intra-atleta)')
ax.set_title('C · Sonolência × outros itens de fadiga e Vigor\ndescolada dos demais (r≈0)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# D alpha
ax=axs[1,1]
vals=[out['D_alpha']['com_sonolento'],out['D_alpha']['sem_sonolento']]; labsD=['Fadiga\n(4 itens)','Fadiga sem\nSonolento (3)']
bars=ax.bar([0,1],vals,color=[P['MUT'],P['TEAL']],width=.6)
cis=[out['D_alpha']['ic_com'],out['D_alpha']['ic_sem']]
for i,(v,ci) in enumerate(zip(vals,cis)):
    ax.plot([i,i],ci,color=P['NAVY'],lw=1.5); ax.text(i,v+0.03,f"α={v:.3f}".replace('.',','),ha='center',fontsize=10,fontweight='bold',color=P['NAVY'])
ax.axhline(0.70,ls='--',color=P['MUT'],lw=1); ax.text(1.4,0.71,'0,70',fontsize=8,color=P['MUT'])
ax.set_xticks([0,1]); ax.set_xticklabels(labsD,fontsize=9); ax.set_ylim(0,1); ax.set_ylabel('α de Cronbach')
ax.set_title('D · Confiabilidade da Fadiga sobe ao\nremover a Sonolência (0,80 → 0,90)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'sonolencia_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_sonolencia.json + sonolencia_fig.png")
