# -*- coding: utf-8 -*-
"""Descritivas + normalidade + testes paramétricos e não-paramétricos (BRUMS × HIIT).

  A. Descritivas completas por variável (n, média, DP, mediana, IQR, mín, máx,
     assimetria, curtose, % piso) + normalidade (Shapiro–Wilk).
  B. Comparação pré→pós lado a lado — PARAMÉTRICO (t pareado, dz, IC95%) vs.
     NÃO-PARAMÉTRICO (Wilcoxon, r de correlação bisserial), agregado por atleta
     (n=27), com a normalidade das diferenças e o teste recomendado.

Autocontido: lê ../modelagem/base_modelagem.csv (anonimizada).
Uso: python descritivas.py → resultados_descritivas.json + descritivas_fig.png
Dependências: numpy scipy pandas pingouin matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats
import pingouin as pg
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
d=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')
VARS=['PTH','FadFis','Fadiga','Vigor','FadMen','Tensão','Depressão','Raiva','Confusão','EstFis','EstMen']
LAB={'PTH':'PTH (TMD)','FadFis':'Fadiga física','Fadiga':'Fadiga','Vigor':'Vigor','FadMen':'Fadiga mental','Tensão':'Tensão','Depressão':'Depressão','Raiva':'Raiva','Confusão':'Confusão','EstFis':'Estado físico','EstMen':'Estado mental'}
out={'n_obs':int(len(d)),'n_atletas':int(d['atleta'].nunique())}

# ---------- A. Descritivas + normalidade (amostra completa) ----------
rowsA=[]
for v in VARS:
    x=d[v].dropna().values; n=len(x); q1,q3=np.percentile(x,[25,75])
    sw=stats.shapiro(x) if 3<=n<=5000 else (np.nan,np.nan)
    rowsA.append({'var':v,'label':LAB[v],'n':int(n),'media':round(float(x.mean()),2),'dp':round(float(x.std(ddof=1)),2),
        'mediana':round(float(np.median(x)),1),'IQR':round(float(q3-q1),1),'min':round(float(x.min()),1),'max':round(float(x.max()),1),
        'assimetria':round(float(stats.skew(x)),2),'curtose':round(float(stats.kurtosis(x)),2),'piso_pct':round(100*float((x==x.min()).mean()),1),
        'shapiro_W':round(float(sw[0]),3),'shapiro_p':float(sw[1]),'normal':bool(sw[1]>0.05)})
out['A_descritivas']=rowsA
print("A. Descritivas + Shapiro–Wilk (amostra completa, n=%d):"%len(d))
for r in rowsA: print(f"   {r['label']:15s} M={r['media']:6.2f} DP={r['dp']:5.2f} Md={r['mediana']:4.1f} assim={r['assimetria']:+.2f} W={r['shapiro_W']:.2f} {'normal' if r['normal'] else 'NÃO-normal'}")

# ---------- B. pré→pós: paramétrico vs não-paramétrico (agregado por atleta) ----------
pp=d[d.momento.isin(['pre','pos'])]
rowsB=[]
for v in VARS:
    w=pp.pivot_table(index='atleta',columns='momento',values=v,aggfunc='mean').dropna()
    if len(w)<5: continue
    pre,pos=w['pre'].values,w['pos'].values; dif=pos-pre; n=len(dif)
    swp=stats.shapiro(dif); norm=bool(swp[1]>0.05)
    tt=pg.ttest(pos,pre,paired=True); tval=float(tt['T'].iloc[0]); tp=float(tt['p_val'].iloc[0]); dz=float(tt['cohen_d'].iloc[0]); ci=tt['CI95'].iloc[0]
    wx=pg.wilcoxon(pos,pre); wp=float(wx['p_val'].iloc[0]); rbc=float(wx['RBC'].iloc[0])
    rowsB.append({'var':v,'label':LAB[v],'n':int(n),'normalidade_dif':'normal' if norm else 'não-normal',
        'shapiro_p':round(float(swp[1]),3),
        't':round(tval,2),'p_t':float(tp),'dz':round(dz,2),'ic':[round(float(ci[0]),2),round(float(ci[1]),2)],
        'wilcoxon_p':float(wp),'rbc':round(rbc,2),
        'recomendado':'não-paramétrico' if not norm else 'paramétrico',
        'concordam':bool((tp<0.05)==(wp<0.05))})
out['B_param_vs_naoparam']=rowsB
print("\nB. Pré→pós — paramétrico (t, dz) vs não-paramétrico (Wilcoxon, RBC), agregado por atleta (n=27):")
for r in rowsB: print(f"   {r['label']:15s} [{r['normalidade_dif']:10s}] t p={r['p_t']:.3f} dz={r['dz']:+.2f} | Wilcoxon p={r['wilcoxon_p']:.3f} RBC={r['rbc']:+.2f} | {'concordam' if r['concordam'] else 'DIVERGEM'}")
disc=[r['label'] for r in rowsB if not r['concordam']]
out['divergencias']=disc; print("\nDivergências paramétrico×não-paramétrico:", disc or "nenhuma")

json.dump(out,open(os.path.join(HERE,'resultados_descritivas.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ---------- figura: (A) assimetria+normalidade  (B) p paramétrico vs não-paramétrico ----------
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(1,2,figsize=(12.5,5),dpi=170)
A=sorted(rowsA,key=lambda r:r['assimetria'])
ax=axs[0]; y=range(len(A)); ax.barh(list(y),[r['assimetria'] for r in A],color=[P['TEAL'] if r['normal'] else P['RED'] for r in A])
ax.set_yticks(list(y)); ax.set_yticklabels([r['label'] for r in A],fontsize=9); ax.axvline(0,color=P['MUT'],lw=1)
for s in['top','right']: ax.spines[s].set_visible(False)
ax.set_xlabel('assimetria (skewness)'); ax.set_title('A · Forma e normalidade das distribuições',fontsize=11,loc='left',color=P['NAVY'],fontweight='bold')
import matplotlib.patches as mp
ax.legend(handles=[mp.Patch(color=P['TEAL'],label='normal (Shapiro p>0,05)'),mp.Patch(color=P['RED'],label='não-normal')],frameon=False,fontsize=8,loc='lower right')
ax2=axs[1]
for r in rowsB:
    xp=-np.log10(max(r['p_t'],1e-4)); yp=-np.log10(max(r['wilcoxon_p'],1e-4))
    c=P['TEAL'] if r['concordam'] else P['GOLD']
    ax2.scatter(xp,yp,s=42,color=c,alpha=.8,edgecolor='white',lw=.6)
    ax2.annotate(r['label'][:8],(xp,yp),fontsize=7,color=P['MUT'],xytext=(3,3),textcoords='offset points')
lim=-np.log10(0.05); ax2.axvline(lim,ls='--',color=P['MUT'],lw=1); ax2.axhline(lim,ls='--',color=P['MUT'],lw=1)
ax2.plot([0,4],[0,4],ls=':',color=P['GRID'],lw=1)
ax2.set_xlabel('−log₁₀ p · t pareado (paramétrico)'); ax2.set_ylabel('−log₁₀ p · Wilcoxon (não-param.)')
for s in['top','right']: ax2.spines[s].set_visible(False)
ax2.set_title('B · Paramétrico × não-paramétrico (concordância)',fontsize=11,loc='left',color=P['NAVY'],fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(HERE,'descritivas_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_descritivas.json + descritivas_fig.png")
