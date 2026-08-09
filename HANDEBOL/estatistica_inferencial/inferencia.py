# -*- coding: utf-8 -*-
"""Estatística inferencial — bateria clássica (BRUMS × HIIT).

Complementa os modelos mistos (../modelagem/) com os testes clássicos que um
comitê espera, sempre respeitando a estrutura de medidas repetidas (agregação
por atleta) e com tamanho de efeito + IC95%:

  A. Resposta aguda pré→pós  — t pareado + Wilcoxon; dz (IC95% bootstrap); FDR
  B. Efeito do dia           — Friedman (casos completos) + ANOVA de MR (pingouin)
  C. HIIT vs. técnico-tático — t pareado no nível do atleta
  D. Correlações repetidas   — rm_corr (Bakdash & Marusich) subescala × externos, FDR
  E. Confiabilidade (ICC)    — ICC(2,1) por subescala (pré vs pós como réplicas)

Autocontido: lê ../modelagem/base_modelagem.csv (anonimizada).
Uso: python inferencia.py   → resultados_inferencia.json + forest_dz.png
Dependências: numpy scipy pandas pingouin matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
import pingouin as pg
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore'); rng=np.random.RandomState(7)
HERE=os.path.dirname(os.path.abspath(__file__))
d=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',GRID='#E3E9F0')
VARS=['FadFis','PTH','Fadiga','Vigor','FadMen','Tensão','Depressão','Raiva','Confusão']
LAB={'FadFis':'Fadiga física','PTH':'PTH (TMD)','Fadiga':'Fadiga','Vigor':'Vigor','FadMen':'Fadiga mental','Tensão':'Tensão','Depressão':'Depressão','Raiva':'Raiva','Confusão':'Confusão'}
out={'n_obs':int(len(d)),'n_atletas':int(d['atleta'].nunique())}

def boot_dz(delta,nb=5000):
    if len(delta)<3: return (np.nan,np.nan)
    dz=[]
    for _ in range(nb):
        s=delta[rng.randint(0,len(delta),len(delta))]
        if s.std(ddof=1)>0: dz.append(s.mean()/s.std(ddof=1))
    return (float(np.percentile(dz,2.5)),float(np.percentile(dz,97.5))) if dz else (np.nan,np.nan)

# ---------- A. Resposta aguda pré→pós ----------
pp=d[d.momento.isin(['pre','pos'])]
rowsA=[]; pv=[]
for v in VARS:
    w=pp.pivot_table(index='atleta',columns='momento',values=v,aggfunc='mean').dropna()
    if len(w)<3: continue
    delta=(w['pos']-w['pre']).values; n=len(delta)
    t,pt=stats.ttest_rel(w['pos'],w['pre'])
    try: ww,pw=stats.wilcoxon(w['pos'],w['pre'])
    except Exception: pw=np.nan
    dz=delta.mean()/delta.std(ddof=1) if delta.std(ddof=1)>0 else 0
    lo,hi=boot_dz(delta)
    rowsA.append({'var':v,'label':LAB[v],'n':int(n),'delta':round(float(delta.mean()),2),
                  'dz':round(float(dz),2),'ic':[round(lo,2),round(hi,2)],
                  't':round(float(t),2),'p':float(pt),'wilcoxon_p':float(pw)}); pv.append(float(pt))
_,pf,_,_=multipletests(pv,method='fdr_bh')
for r,q in zip(rowsA,pf): r['p_FDR']=round(float(q),4); r['sig']=bool(q<0.05); r['p']=round(r['p'],4); r['wilcoxon_p']=round(r['wilcoxon_p'],4)
out['A_aguda']=rowsA
print("A. Resposta aguda (t pareado + Wilcoxon, dz IC95%, FDR):")
for r in rowsA: print(f"   {r['label']:14s} dz={r['dz']:+.2f} IC{r['ic']} t={r['t']:+.2f} p_FDR={r['p_FDR']:.3f} {'*' if r['sig'] else ''}")

# ---------- B. Efeito do dia ----------
B={}
for v in ['FadFis','PTH','Fadiga','Vigor']:
    ad=d.groupby(['atleta','dia'])[v].mean().reset_index()
    piv=ad.pivot(index='atleta',columns='dia',values=v)
    cc=piv.dropna()  # casos completos (7 dias)
    fr=None
    if cc.shape[0]>=3 and cc.shape[1]>=3:
        chi,pfr=stats.friedmanchisquare(*[cc[c].values for c in cc.columns])
        fr={'chi2':round(float(chi),2),'p':float(pfr),'n':int(cc.shape[0]),'k':int(cc.shape[1])}
    try:
        aov=pg.rm_anova(data=ad,dv=v,within='dia',subject='atleta',correction=True)
        F=float(aov['F'].iloc[0]); pav=float(aov['p_GG_corr'].iloc[0]) if 'p_GG_corr' in aov.columns else float(aov['p_unc'].iloc[0])
        rm={'F':round(F,2),'p_GG':float(pav)}
    except Exception as e:
        rm={'erro':str(e)[:60]}
    B[v]={'friedman_casos_completos':fr,'rm_anova':rm}
out['B_efeito_dia']=B
print("\nB. Efeito do dia (Friedman casos completos / RM-ANOVA):")
for v,r in B.items():
    fr=r['friedman_casos_completos']; rm=r['rm_anova']
    print(f"   {v:8s} Friedman {'χ²=%.1f p=%.3f (n=%d)'%(fr['chi2'],fr['p'],fr['n']) if fr else '—'} | RM-ANOVA {'F=%.2f p=%.3f'%(rm['F'],rm['p_GG']) if 'F' in rm else rm.get('erro')}")

# ---------- C. HIIT vs sem (nível do atleta, dias 2-7) ----------
dd=d[d.dia.between(2,7)]; ath=dd.groupby(['atleta','hiit']).apply(lambda g:g[VARS].mean()).reset_index()
rowsC=[]
for v in ['PTH','FadFis','Fadiga','Vigor','FadMen']:
    w=ath.pivot_table(index='atleta',columns='hiit',values=v).dropna()
    if len(w)<3: continue
    t,pt=stats.ttest_rel(w[1],w[0]); dl=(w[1]-w[0]).values; dz=dl.mean()/dl.std(ddof=1) if dl.std(ddof=1)>0 else 0
    rowsC.append({'var':v,'label':LAB[v],'delta_HIIT':round(float(dl.mean()),2),'dz':round(float(dz),2),'t':round(float(t),2),'p':round(float(pt),4),'n':int(len(w))})
out['C_hiit']=rowsC
print("\nC. HIIT vs técnico-tático (t pareado, nível do atleta):")
for r in rowsC: print(f"   {r['label']:14s} Δ={r['delta_HIIT']:+.2f} dz={r['dz']:+.2f} t={r['t']:+.2f} p={r['p']:.3f}")

# ---------- D. Correlações repetidas (rm_corr) ----------
EXT=['FadFis','FadMen','EstFis','EstMen']; SUBS=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
rowsD=[]; pvD=[]
for s in SUBS:
    for e in EXT:
        sub=d[['atleta',s,e]].dropna()
        if sub['atleta'].nunique()<3: continue
        try:
            rc=pg.rm_corr(data=sub,x=s,y=e,subject='atleta')
            r=float(rc['r'].iloc[0]); pval=float(rc['pval'].iloc[0]); ci=rc['CI95'].iloc[0]
            rowsD.append({'sub':s,'ext':e,'r':round(r,2),'ic':[round(ci[0],2),round(ci[1],2)],'p':pval}); pvD.append(pval)
        except Exception: pass
_,pfD,_,_=multipletests(pvD,method='fdr_bh')
for r,q in zip(rowsD,pfD): r['p_FDR']=round(float(q),4); r['sig']=bool(q<0.05); r['p']=round(r['p'],4)
out['D_rmcorr']=rowsD
sig=[r for r in rowsD if r['sig']]
print(f"\nD. Correlações repetidas (rm_corr): {len(sig)}/{len(rowsD)} significativas após FDR. Mais fortes:")
for r in sorted(rowsD,key=lambda x:-abs(x['r']))[:6]: print(f"   {r['sub']}×{r['ext']}: r={r['r']:+.2f} IC{r['ic']} p_FDR={r['p_FDR']:.3f}")

# ---------- E. ICC do atleta (partição de variância, modelo misto) ----------
# ICC(atleta)=var(intercepto)/(var+resíduo): fração da variância que é traço estável.
rowsE=[]
for v in ['FadFis','PTH','Fadiga','Vigor','Tensão','Depressão','Raiva','Confusão','FadMen']:
    dat=d[['atleta',v]].dropna().rename(columns={v:'y'})
    try:
        import statsmodels.formula.api as smf
        m=smf.mixedlm('y ~ 1',dat,groups=dat['atleta']).fit(reml=True,method='lbfgs')
        vg=float(m.cov_re.iloc[0,0]); ve=float(m.scale); icc=vg/(vg+ve)
        rowsE.append({'var':v,'label':LAB[v],'ICC_atleta':round(float(icc),2)})
    except Exception: pass
rowsE.sort(key=lambda r:-r['ICC_atleta'])
out['E_icc_atleta']=rowsE
print("\nE. ICC do atleta (partição de variância — fração de traço estável):")
for r in rowsE: print(f"   {r['label']:14s} ICC={r['ICC_atleta']:.2f}")

json.dump(out,open(os.path.join(HERE,'resultados_inferencia.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ---------- Figura: forest plot dz agudo com IC95% ----------
A=sorted([r for r in rowsA],key=lambda r:r['dz'])
fig,ax=plt.subplots(figsize=(7,4.6),dpi=170)
for i,r in enumerate(A):
    c=P['RED'] if (r['sig'] and r['dz']>0) else (P['TEAL'] if r['sig'] else P['MUT'])
    ax.plot(r['ic'],[i,i],color=c,lw=2.4,alpha=.6); ax.plot(r['dz'],i,'o',color=c,ms=8)
    ax.text(r['ic'][1]+0.03,i,f"{r['dz']:+.2f}{'*' if r['sig'] else ''}",va='center',fontsize=8.5,color=P['NAVY'])
ax.axvline(0,color=P['MUT'],lw=1); ax.set_yticks(range(len(A))); ax.set_yticklabels([r['label'] for r in A])
ax.set_xlabel('dz intra-sujeito (IC95% bootstrap)'); [ax.spines[s].set_visible(False) for s in['top','right']]
ax.set_title('Resposta aguda pré→pós — tamanho de efeito e IC95% (* FDR<0,05)',fontsize=10.5,loc='left',color=P['NAVY'])
fig.tight_layout(); fig.savefig(os.path.join(HERE,'forest_dz.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_inferencia.json + forest_dz.png")
