# -*- coding: utf-8 -*-
"""Carga interna por TRIMP — BRUMS × HIIT.

TRIMP = intensidade × duração. A planilha de FC/PSE NÃO registrou a duração das
fases; portanto calcula-se aqui o que é honesto sem duração:

  1. Intensidade por fase via FRAÇÃO DA RESERVA DE FC (%HRR) com a ponderação
     exponencial de Banister:  w = %HRR · 0,64 · e^(1,92 · %HRR)  (homens)
     — FCrepouso = menor FC pré do atleta; FCmax = maior FC pico do atleta.
  2. TRIMP RELATIVO por sessão = Σ das ponderações das 5 fases (duração unitária
     por fase). É um índice comparável entre atletas/sessões, NÃO um AU absoluto.
  3. Comparação com a carga de Foster (Σ PSE) — concordância das duas famílias.
  4. TRIMP × resposta aguda do humor (Δ PTH nos dias de HIIT) por atleta.

Para o TRIMP absoluto (AU) basta multiplicar w pela duração real de cada fase:
  TRIMP_fase = duracao_min · w  →  passe as durações e recalculo.

Autocontido: lê fc_fases.csv (FC/PSE anonimizada) e ../modelagem/base_modelagem.csv (BRUMS).
Uso: python trimp.py   → resultados_trimp.json + trimp_figuras.png
Dependências: numpy pandas scipy matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')

fc=pd.read_csv(os.path.join(HERE,'fc_fases.csv'))
B=1.92; A=0.64  # Banister (homens)
# proxies por atleta
fcrest=fc.groupby('atleta')['fc_pre'].min()
fcmax =fc.groupby('atleta')['fc_pos'].max()
fc['rest']=fc['atleta'].map(fcrest); fc['max']=fc['atleta'].map(fcmax)
fc['valida']=fc['fc_pos'].notna() & (fc['max']>fc['rest'])
fc['hrr']=np.where(fc['valida'],((fc['fc_pos']-fc['rest'])/(fc['max']-fc['rest'])).clip(0,1),np.nan)
fc['w']=fc['hrr']*A*np.exp(B*fc['hrr'])          # TRIMP por minuto (intensidade)

# TRIMP relativo por sessão — exige >=3 fases válidas (senão descarta a sessão)
sess=fc.groupby(['atleta','sessao']).agg(trimp_rel=('w','sum'), foster=('pse','sum'),
       hrr_medio=('hrr','mean'), fc_pico=('fc_pos','max'), nval=('valida','sum')).reset_index()
n_desc=int((sess['nval']<3).sum())
sess=sess[sess['nval']>=3].copy()
out_desc=n_desc
out={'n_atletas':int(fc['atleta'].nunique()),'sessoes_descartadas_fc_invalida':None,'formula':'w = %HRR*0.64*exp(1.92*%HRR); TRIMP_rel = sum(w das 5 fases)'}

# média por sessão
bysess=sess.groupby('sessao').agg(trimp_rel=('trimp_rel','mean'), foster=('foster','mean'),
        hrr=('hrr_medio','mean')).round(2).reset_index()
out['sessoes_descartadas_fc_invalida']=out_desc
out['por_sessao']=bysess.to_dict('records')
print("TRIMP relativo médio por sessão:")
for r in out['por_sessao']: print(f"  {r['sessao']}: TRIMP_rel={r['trimp_rel']:.2f}  %HRR={r['hrr']:.2f}  Foster(ΣPSE)={r['foster']:.1f}")

# concordância TRIMP (FC) x Foster (PSE) no nível atleta-sessão
cc=sess.dropna(subset=['trimp_rel','foster'])
rp,pp=stats.pearsonr(cc['trimp_rel'],cc['foster']); rs,ps=stats.spearmanr(cc['trimp_rel'],cc['foster'])
out['concordancia_TRIMP_Foster']={'pearson':round(float(rp),2),'p':float(pp),'spearman':round(float(rs),2),'n':int(len(cc))}
print(f"\nConcordância TRIMP(FC) × Foster(PSE): r={rp:.2f} (rho={rs:.2f}), n={len(cc)}")

# carga semanal por atleta: total, monotonia, strain (família TRIMP)
def load_metrics(g,col):
    v=g[col].dropna().values
    if len(v)<2: return (np.nan,np.nan,np.nan)
    mn=v.mean(); sd=v.std(ddof=1); mono=mn/sd if sd>0 else np.nan
    return (round(float(v.sum()),1), round(float(mono),2) if np.isfinite(mono) else None,
            round(float(v.sum()*mono),1) if np.isfinite(mono) else None)
wk=[]
for a,g in sess.groupby('atleta'):
    tt,tm,tsr=load_metrics(g,'trimp_rel'); ft,fm,fsr=load_metrics(g,'foster')
    wk.append({'atleta':a,'trimp_total':tt,'trimp_monotonia':tm,'trimp_strain':tsr,'foster_total':ft})
wkdf=pd.DataFrame(wk)
out['semanal_resumo']={'trimp_total':[round(wkdf['trimp_total'].mean(),1),round(wkdf['trimp_total'].std(),1)],
    'trimp_monotonia':[round(wkdf['trimp_monotonia'].mean(),2),round(wkdf['trimp_monotonia'].std(),2)],
    'trimp_strain':[round(wkdf['trimp_strain'].mean(),1),round(wkdf['trimp_strain'].std(),1)]}
print(f"Semanal (média±DP): TRIMP total {out['semanal_resumo']['trimp_total']}, monotonia {out['semanal_resumo']['trimp_monotonia']}, strain {out['semanal_resumo']['trimp_strain']}")

# TRIMP (por atleta) × Δ PTH agudo nos dias de HIIT (BRUMS)
bm=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
h=bm[(bm.hiit==1)&(bm.momento.isin(['pre','pos']))]
dpth={}
for a,g in h.groupby('atleta'):
    ds=[]
    for d,gd in g.groupby('dia'):
        pre=gd[gd.momento=='pre']['PTH']; pos=gd[gd.momento=='pos']['PTH']
        if len(pre) and len(pos): ds.append(float(pos.mean()-pre.mean()))
    if ds: dpth[a]=np.mean(ds)
tr_ath=sess.groupby('atleta')['trimp_rel'].mean()
common=sorted(set(dpth)&set(tr_ath.index))
link=None
if len(common)>=5:
    xs=np.array([tr_ath[a] for a in common]); ys=np.array([dpth[a] for a in common])
    r,pv=stats.pearsonr(xs,ys)
    link={'r':round(float(r),2),'p':float(pv),'n':len(common)}
    out['TRIMP_x_humor']=link
    print(f"\nTRIMP × Δ PTH agudo (por atleta): r={r:.2f}, p={pv:.3f}, n={len(common)}")

json.dump(out,open(os.path.join(HERE,'resultados_trimp.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ---- figura ----
fig,ax=plt.subplots(1,3,figsize=(13,3.9),dpi=160)
# (1) TRIMP e Foster por sessão
x=np.arange(len(bysess)); ax0=ax[0]; ax0b=ax0.twinx()
ax0.bar(x-0.2,bysess['trimp_rel'],0.4,color=P['RED'],label='TRIMP relativo')
ax0b.bar(x+0.2,bysess['foster'],0.4,color=P['GOLD'],label='Foster (ΣPSE)')
ax0.set_xticks(x); ax0.set_xticklabels(bysess['sessao']); ax0.set_ylabel('TRIMP relativo',color=P['RED']); ax0b.set_ylabel('Foster ΣPSE',color=P['GOLD'])
ax0.set_title('Carga interna por sessão',fontsize=10,loc='left',color=P['NAVY'])
for s in['top']: ax0.spines[s].set_visible(False); ax0b.spines[s].set_visible(False)
# (2) concordância TRIMP x Foster
ax1=ax[1]; ax1.scatter(cc['trimp_rel'],cc['foster'],s=28,color=P['TEAL'],alpha=.6,edgecolor='white',lw=.5)
b1,b0=np.polyfit(cc['trimp_rel'],cc['foster'],1); xs2=np.array([cc['trimp_rel'].min(),cc['trimp_rel'].max()])
ax1.plot(xs2,b0+b1*xs2,color=P['GOLD'],lw=2); ax1.set_xlabel('TRIMP relativo (FC)'); ax1.set_ylabel('Foster (ΣPSE)')
ax1.text(0.03,0.95,f'r={rp:.2f}',transform=ax1.transAxes,va='top',color=P['MUT'],fontsize=10)
ax1.set_title('TRIMP (FC) × Foster (PSE)',fontsize=10,loc='left',color=P['NAVY'])
for s in['top','right']: ax1.spines[s].set_visible(False)
# (3) TRIMP x humor
ax2=ax[2]
if link:
    xs=np.array([tr_ath[a] for a in common]); ys=np.array([dpth[a] for a in common])
    ax2.scatter(xs,ys,s=34,color=P['VIO'],alpha=.7,edgecolor='white',lw=.5)
    b1,b0=np.polyfit(xs,ys,1); xr=np.array([xs.min(),xs.max()]); ax2.plot(xr,b0+b1*xr,color=P['GOLD'],lw=2)
    ax2.axhline(0,color=P['MUT'],lw=1); ax2.set_xlabel('TRIMP relativo médio'); ax2.set_ylabel('Δ PTH agudo (dias HIIT)')
    ax2.text(0.03,0.95,f"r={link['r']:.2f} (n.s.)" if link['p']>=.05 else f"r={link['r']:.2f}",transform=ax2.transAxes,va='top',color=P['MUT'],fontsize=10)
ax2.set_title('TRIMP × resposta do humor',fontsize=10,loc='left',color=P['NAVY'])
for s in['top','right']: ax2.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'trimp_figuras.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_trimp.json + trimp_figuras.png")
