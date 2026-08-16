import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv')
MOOD=[('Vigor','Vigor'),('Fadiga','Fadiga'),('TMD','PTH'),('FadFisica','Fadiga física')]
R={}
# ---------- SONO (Epworth) + ESTRESSE (PSS) ----------
wk=h.groupby('ID')[['Vigor','Fadiga','TMD','FadFisica','Epworth','PSS']].mean()
def sp(a,b):
    r,p=stats.spearmanr(wk[a],wk[b],nan_policy='omit'); return dict(rho=float(r),p=float(p),n=int(wk[[a,b]].dropna().shape[0]))
R['epw']=dict(m=float(wk.Epworth.mean()),sd=float(wk.Epworth.std(ddof=1)),mn=float(h.Epworth.min()),mx=float(h.Epworth.max()),
    hi=int((wk.Epworth>10).sum()),n=int(len(wk)),corr={k:sp('Epworth',k) for k,_ in MOOD})
R['pss']=dict(m=float(wk.PSS.mean()),sd=float(wk.PSS.std(ddof=1)),mn=float(h.PSS.min()),mx=float(h.PSS.max()),
    corr={k:sp('PSS',k) for k,_ in MOOD})
# grupo sonolência (Epworth>10 vs <=10) — comparação de humor semanal (Mann-Whitney)
wk['sleepy']=(wk.Epworth>10)
R['sleepy_cmp']={}
for k,lab in MOOD:
    a=wk[wk.sleepy][k]; b=wk[~wk.sleepy][k]
    U,p=stats.mannwhitneyu(a,b); 
    # rank-biserial effect
    rb=1-2*U/(len(a)*len(b))
    R['sleepy_cmp'][k]=dict(hi=float(a.mean()),lo=float(b.mean()),U=float(U),p=float(p),rb=float(rb),n_hi=int(len(a)),n_lo=int(len(b)))
# Epworth/PSS por dia (variam ao longo da semana?)
R['epw_day']={int(d):float(v) for d,v in h.groupby('dia').Epworth.mean().items()}
R['pss_day']={int(d):float(v) for d,v in h.groupby('dia').PSS.mean().items()}
Ep=h.groupby(['ID','dia']).Epworth.mean().reset_index().pivot(index='ID',columns='dia',values='Epworth').dropna()
fr_e=stats.friedmanchisquare(*[Ep[d].values for d in range(1,8)])
R['epw_friedman']=dict(chi=float(fr_e.statistic),p=float(fr_e.pvalue),n=int(len(Ep)))

# ---------- HIIT vs NÃO-HIIT ----------
# HIIT days: 2,4,7 ; não-HIIT: 1,3,5,6
h['isH']=h.HIIT==1
# (a) média por atleta em dias HIIT vs não-HIIT -> Wilcoxon pareado
R['hiit']={}
for k,lab in MOOD:
    hh=h[h.isH].groupby('ID')[k].mean(); nn=h[~h.isH].groupby('ID')[k].mean()
    idx=hh.index.intersection(nn.index); a,b=hh.loc[idx],nn.loc[idx]
    W,p=stats.wilcoxon(a,b); d=(a-b); dz=d.mean()/d.std(ddof=1) if d.std(ddof=1)>0 else 0
    R['hiit'][k]=dict(hiit=float(a.mean()),nohiit=float(b.mean()),W=float(W),p=float(p),dz=float(dz),n=int(len(idx)))
# (b) resposta AGUDA pré->pós em dias HIIT vs não-HIIT (isola o estímulo do drift semanal)
R['hiit_acute']={}
for k,lab in [('Vigor','Vigor'),('Fadiga','Fadiga'),('TMD','PTH')]:
    def acute(mask):
        s=h[mask]; pre=s[s.momento=='pre'].groupby(['ID','dia'])[k].mean(); pos=s[s.momento=='pos'].groupby(['ID','dia'])[k].mean()
        d=(pos-pre).dropna(); return d
    dH=acute(h.isH); dN=acute(~h.isH)
    # per-athlete mean acute change on HIIT vs non-HIIT
    aH=dH.groupby(level=0).mean(); aN=dN.groupby(level=0).mean()
    idx=aH.index.intersection(aN.index); x,y=aH.loc[idx],aN.loc[idx]
    W,p=stats.wilcoxon(x,y); dd=(x-y); dz=dd.mean()/dd.std(ddof=1) if dd.std(ddof=1)>0 else 0
    R['hiit_acute'][k]=dict(hiit=float(x.mean()),nohiit=float(y.mean()),W=float(W),p=float(p),dz=float(dz),n=int(len(idx)))
json.dump(R,open('extra.json','w'),indent=1,ensure_ascii=False)
print('SONO Epworth: M=%.1f±%.1f (%.0f-%.0f) | %d/%d atletas com sonolência excessiva (>10)'%(R['epw']['m'],R['epw']['sd'],R['epw']['mn'],R['epw']['mx'],R['epw']['hi'],R['epw']['n']))
print('  Epworth × humor (semanal):',{k:(round(v['rho'],2),round(v['p'],3)) for k,v in R['epw']['corr'].items()})
print('ESTRESSE PSS: M=%.1f±%.1f (%.0f-%.0f)'%(R['pss']['m'],R['pss']['sd'],R['pss']['mn'],R['pss']['mx']))
print('  PSS × humor (semanal):',{k:(round(v['rho'],2),round(v['p'],3)) for k,v in R['pss']['corr'].items()})
print('\\nGrupo sonolência (>10 vs <=10) — humor semanal:')
for k,lab in MOOD: c=R['sleepy_cmp'][k]; print('  %-10s sonolentos=%.2f vs %.2f  p=%.3f rb=%.2f'%(lab,c['hi'],c['lo'],c['p'],c['rb']))
print('\\nHIIT vs não-HIIT (média por atleta):')
for k,lab in MOOD: c=R['hiit'][k]; print('  %-10s HIIT=%.2f vs %.2f  p=%.3f dz=%+.2f'%(lab,c['hiit'],c['nohiit'],c['p'],c['dz']))
print('\\nResposta AGUDA pré→pós em dias HIIT vs não-HIIT:')
for k in ['Vigor','Fadiga','TMD']: c=R['hiit_acute'][k]; print('  %-6s Δ HIIT=%+.2f vs Δ não-HIIT=%+.2f  p=%.3f dz=%+.2f'%(k,c['hiit'],c['nohiit'],c['p'],c['dz']))
