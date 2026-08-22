# -*- coding: utf-8 -*-
# (1) Variancia quebrada por HIIT: efeito AGUDO (pre->pos) e RECUPERACAO noturna
#     (pos[d-1]->pre[d]) apos dia de HIIT vs apos dia sem HIIT; e os componentes de
#     variancia (atleta/dia/momento) DENTRO dos dias de HIIT e DENTRO dos sem HIIT.
# (2) Decomposicao SINAL/RUIDO das curvas diarias: tendencia lenta (trend) +
#     componente travada no HIIT + ruido residual; % de variancia e SNR.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import statsmodels.formula.api as smf
from scipy import stats
S=['Vigor','Fadiga','TMD','FadFisica']
LAB={'Vigor':'Vigor','Fadiga':'Fadiga','TMD':'PTH','FadFisica':'Fadiga física'}
HIIT=[2,4,7]
h=pd.read_csv('humor_anon.csv'); h['adia']=h['ID'].astype(str)+'_'+h['dia'].astype(str)

# ---------- (1a) agudo e recuperacao por tipo de dia ----------
def acute_by_type(v):
    hi=[]; no=[]
    for aid,g in h.groupby('ID'):
        gg=g.set_index(['dia','momento'])[v]
        for d in range(1,8):
            try: pre=gg.loc[(d,'pre')].mean(); pos=gg.loc[(d,'pos')].mean()
            except Exception: continue
            if pd.notna(pre) and pd.notna(pos):
                (hi if d in HIIT else no).append(pos-pre)
    return np.array(hi),np.array(no)
def recovery_by_prevtype(v):
    aft_h=[]; aft_n=[]
    for aid,g in h.groupby('ID'):
        gg=g.set_index(['dia','momento'])[v]
        for d in range(2,8):
            try: pprev=gg.loc[(d-1,'pos')].mean(); pren=gg.loc[(d,'pre')].mean()
            except Exception: continue
            if pd.notna(pprev) and pd.notna(pren):
                ((aft_h if (d-1) in HIIT else aft_n)).append(pren-pprev)
    return np.array(aft_h),np.array(aft_n)

print("=== (1) AGUDO e RECUPERACAO por tipo de dia ===")
print(f"{'dim':14s} | agudo HIIT / sem  | recup pós-HIIT / pós-sem")
rows1=[]
for v in S:
    ah,an=acute_by_type(v); rh,rn=recovery_by_prevtype(v)
    r=dict(dim=v,lab=LAB[v],
           ag_h=float(ah.mean()),ag_n=float(an.mean()),
           rec_ph=float(rh.mean()),rec_pn=float(rn.mean()))
    # teste recuperacao pós-HIIT vs pós-sem (amostras independentes de transicoes)
    try: r['rec_p']=float(stats.mannwhitneyu(rh,rn).pvalue)
    except Exception: r['rec_p']=np.nan
    rows1.append(r)
    print(f"{LAB[v]:14s} | {ah.mean():+5.2f} / {an.mean():+5.2f}  | {rh.mean():+5.2f} / {rn.mean():+5.2f}  (p={r['rec_p']:.3f})")

# ---------- (1b) componentes de variancia dentro de HIIT vs sem ----------
def var_comp(df):
    out={}
    for v in S:
        d=df[['ID','adia',v]].dropna().rename(columns={v:'y'})
        try:
            r=smf.mixedlm("y ~ 1",d,groups=d["ID"],re_formula="1",vc_formula={"dia":"0+C(adia)"}).fit(reml=True)
            va=float(np.asarray(r.cov_re).ravel()[0]); vd=float(np.asarray(r.vcomp).ravel()[0]); ve=float(r.scale)
            tot=va+vd+ve; out[v]=[round(va/tot*100,1),round(vd/tot*100,1),round(ve/tot*100,1)]
        except Exception: out[v]=None
    return out
vc_h=var_comp(h[h.dia.isin(HIIT)]); vc_n=var_comp(h[~h.dia.isin(HIIT)])
print("\n=== (1b) COMPONENTES DE VARIANCIA (atleta/dia/momento) ===")
for v in S: print(f"  {LAB[v]:14s} HIIT={vc_h[v]}  sem={vc_n[v]}")

# ---------- (2) decomposicao sinal/ruido das curvas diarias ----------
print("\n=== (2) SINAL/RUIDO DAS CURVAS: trend + HIIT + ruido ===")
x=np.arange(1,8)
rows2=[]
for v in S:
    y=h.groupby('dia')[v].mean().reindex(range(1,8)).values
    yc=y-y.mean()
    # trend: quadratico no dia
    Xt=np.column_stack([x-4,(x-4)**2]); bt,*_=np.linalg.lstsq(Xt,yc,rcond=None); trend=Xt@bt
    det=yc-trend
    # componente HIIT: media do detrended nos dias HIIT vs nao (2 niveis)
    isH=np.isin(x,HIIT).astype(float); hcoef=det[isH==1].mean()-det[isH==0].mean()
    hcomp=(isH-isH.mean())*hcoef
    noise=det-hcomp
    ss=lambda a:float((a**2).sum()); tot=ss(yc) if ss(yc)>0 else 1
    p_tr,p_hi,p_no=ss(trend)/tot*100,ss(hcomp)/tot*100,ss(noise)/tot*100
    snr=(ss(trend)+ss(hcomp))/ss(noise) if ss(noise)>0 else np.nan
    rows2.append(dict(dim=v,lab=LAB[v],trend=round(p_tr,1),hiit=round(p_hi,1),noise=round(p_no,1),snr=round(float(snr),1),
                      y=[round(float(a),2) for a in y],sig=[round(float(a),2) for a in (y.mean()+trend+hcomp)]))
    print(f"  {LAB[v]:14s} trend={p_tr:5.1f}%  HIIT={p_hi:5.1f}%  ruido={p_no:5.1f}%  SNR={snr:.1f}")

json.dump({'rows1':rows1,'vc_hiit':vc_h,'vc_naohiit':vc_n,'rows2':rows2,'hiit_days':HIIT},
          open('hiit_var_snr.json','w'))

# ---------- figura ----------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
COL={'Vigor':'#2f9e44','Fadiga':'#e8590c','TMD':'#7048e8','FadFisica':'#d9480f'}
fig,ax=plt.subplots(1,3,figsize=(15.5,4.7),dpi=200)
# A recuperacao pos-HIIT vs pos-sem
xb=np.arange(len(S)); wd=0.38
ax[0].bar(xb-wd/2,[r['rec_pn'] for r in rows1],wd,label='após dia sem HIIT',color='#adb5bd')
ax[0].bar(xb+wd/2,[r['rec_ph'] for r in rows1],wd,label='após dia de HIIT',color='#e8590c')
ax[0].axhline(0,color='#adb5bd',lw=.8); ax[0].set_xticks(xb); ax[0].set_xticklabels([r['lab'] for r in rows1],fontsize=9)
ax[0].set_ylabel('recuperação noturna (pós→pré, Δ)')
ax[0].set_title('(1) Recuperação noturna por tipo de dia\nmais recuperação após HIIT (proporcional à carga)',fontweight='bold',fontsize=10.5,loc='left'); ax[0].legend(frameon=False,fontsize=8.5)
# B componentes de variancia intra-dia HIIT vs sem (momento %)
mh=[vc_h[v][2] if vc_h[v] else 0 for v in S]; mn=[vc_n[v][2] if vc_n[v] else 0 for v in S]
ax[1].bar(xb-wd/2,mn,wd,label='dias sem HIIT',color='#adb5bd'); ax[1].bar(xb+wd/2,mh,wd,label='dias de HIIT',color='#e8590c')
ax[1].set_xticks(xb); ax[1].set_xticklabels([LAB[v] for v in S],fontsize=9); ax[1].set_ylabel('% variância intra-dia (momentos)')
ax[1].set_title('(1b) Variância intra-dia por tipo de dia\nmais oscilação aguda nos dias de HIIT',fontweight='bold',fontsize=10.5,loc='left'); ax[1].legend(frameon=False,fontsize=8.5)
# C sinal/ruido decomposicao (barras empilhadas)
tr=[r['trend'] for r in rows2]; hi=[r['hiit'] for r in rows2]; no=[r['noise'] for r in rows2]
y2=np.arange(len(S))
ax[2].barh(y2,tr,color='#1971c2',label='tendência (sinal lento)')
ax[2].barh(y2,hi,left=tr,color='#e8590c',label='HIIT (sinal periódico)')
ax[2].barh(y2,no,left=np.array(tr)+np.array(hi),color='#adb5bd',label='ruído')
ax[2].set_yticks(y2); ax[2].set_yticklabels([r['lab'] for r in rows2]); ax[2].set_xlabel('% da variância da curva'); ax[2].set_xlim(0,100)
ax[2].set_title('(2) Sinal/ruído das curvas\ntendência + HIIT = sinal; resto = ruído',fontweight='bold',fontsize=10.5,loc='left'); ax[2].legend(frameon=False,fontsize=8)
fig.suptitle('Variância quebrada por HIIT e decomposição sinal/ruído das curvas',fontweight='bold',fontsize=12.5,y=1.03)
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/hiit_var_snr.png',bbox_inches='tight',facecolor='white')
print('\n[salvo hiit_var_snr.json + figura]')
