import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
from scipy import stats
import statsmodels.formula.api as smf
d=pd.read_csv('wellness_all.csv')
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

# day number + within-window filter (21-27/04)
d['date']=pd.to_datetime(d['datadia'],errors='coerce')
daymap={pd.Timestamp(2024,4,20+i):i for i in range(1,8)}  # 21->1 ... 27->7
d['dia']=d['date'].map(daymap)
d=d[d['dia'].notna()].copy(); d['dia']=d['dia'].astype(int)
d['HIIT']=d['dia'].isin([2,4,7]).astype(int)
for c in ['FadFisica','FadMental','Epworth','TQR','PSS','TMD','Vigor','Fadiga']:
    d[c]=pd.to_numeric(d[c],errors='coerce')
# within-day order (pre/post)
d=d.sort_values(['nome','dia'])
d['seq']=d.groupby(['nome','dia']).cumcount()
last=d.groupby(['nome','dia'])['seq'].transform('max')
d['momento']=np.where(d['seq']==0,'pre',np.where(d['seq']==last,'pos','mid'))
p(f"janela 21-27/04: {len(d)} obs, {d['nome'].nunique()} atletas")
INSTR=['TQR','Epworth','PSS','FadFisica','FadMental']

# ---- descriptives + range awareness ----
p("\n=== DESCRITIVAS (instrumentos alem do BRUMS) ===")
meta={'TQR':'recuperacao 6-20 (alto=melhor)','Epworth':'sonolencia 0-18 (alto=mais sono)',
      'PSS':'estresse ~0-56 (alto=+estresse)','FadFisica':'0-10','FadMental':'0-10'}
for v in INSTR:
    s=d[v].dropna()
    p(f"  {v:10s} n={len(s):3d} media={s.mean():.2f} DP={s.std():.2f}  [{s.min():.0f},{s.max():.0f}]  {meta[v]}")

# ---- day effect (mixed) ----
p("\n=== EFEITO DO DIA (modelo misto) ===")
for v in INSTR:
    dd=d[['nome','dia',v]].dropna().rename(columns={v:'y'})
    m=smf.mixedlm('y~C(dia)',dd,groups=dd['nome']).fit(reml=False)
    terms=[t for t in m.params.index if t.startswith('C(dia)')]
    wald=float(m.params[terms].values@np.linalg.inv(m.cov_params().loc[terms,terms].values)@m.params[terms].values)
    F=wald/len(terms); pv=stats.chi2.sf(wald,len(terms))
    va=m.cov_re.iloc[0,0]; icc=va/(va+m.scale)
    # day1 vs day7 means
    m1=dd[dd.dia==1].y.mean(); m7=dd[dd.dia==7].y.mean()
    p(f"  {v:10s} F~{F:5.2f} p={pv:.4f}  ICC_atleta={icc:.2f}  D1={m1:.2f}->D7={m7:.2f}")

# ---- HIIT vs non (day level, paired) ----
p("\n=== HIIT vs TECNICO-TATICO (nivel do dia, pareado) ===")
tr=d[d.dia.isin([2,3,4,5,6,7])]
for v in INSTR:
    a=tr[tr.HIIT==1].groupby('nome')[v].mean(); b=tr[tr.HIIT==0].groupby('nome')[v].mean()
    j=pd.concat([a,b],axis=1,keys=['H','N']).dropna()
    if len(j)>5:
        dz=(j.H-j.N).mean()/(j.H-j.N).std(ddof=1); t,pv=stats.ttest_rel(j.H,j.N)
        p(f"  {v:10s} HIIT={j.H.mean():.2f} nao={j.N.mean():.2f} dz={dz:+.2f} p={pv:.3f}")

# ---- trait/state ICC ----
p("\n=== DECOMPOSICAO TRACO/ESTADO (ICC atleta) ===")
def icc1(long,val):
    g=long.groupby('nome')[val]; k=g.ngroups; N=long[val].notna().sum()
    ni=g.count(); n0=(N-(ni**2).sum()/N)/(k-1); grand=long[val].mean()
    msb=(ni*(g.mean()-grand)**2).sum()/(k-1)
    msw=long.groupby('nome')[val].apply(lambda s:((s-s.mean())**2).sum()).sum()/(N-k)
    return (msb-msw)/(msb+(n0-1)*msw)
for v in INSTR:
    dd=d[['nome',v]].dropna()
    p(f"  {v:10s} ICC_atleta={icc1(dd,v):.2f}")

# ---- convergence with mood (within-athlete rmcorr) ----
p("\n=== CONVERGENCIA COM HUMOR (rmcorr intra-atleta) ===")
def rmcorr(df,x,y):
    dd=df[['nome',x,y]].dropna().rename(columns={x:'X',y:'Y'})
    from statsmodels.stats.anova import anova_lm
    m=smf.ols('Y~C(nome)+X',data=dd).fit(); aov=anova_lm(m,typ=1)
    ssx=aov.loc['X','sum_sq']; sse=aov.loc['Residual','sum_sq']
    return np.sign(m.params['X'])*np.sqrt(ssx/(ssx+sse)), len(dd)
for v in INSTR:
    for m_ in ['TMD','Vigor','Fadiga']:
        try:
            r,n=rmcorr(d,v,m_); p(f"  {v:10s} x {m_:6s}: rmcorr={r:+.2f} (n={n})")
        except Exception as e: p(f"  {v} x {m_}: FAIL")
    p("")

# ---- acute pre->post for TQR/Epworth/PSS ----
p("=== RESPOSTA AGUDA PRE->POS (agregada por atleta) ===")
train=d[d.dia.isin([2,3,4,5,6,7])]
for v in INSTR:
    per=[]
    for aid,g in train.groupby('nome'):
        ds=[]
        for dia,gd in g.groupby('dia'):
            gd=gd.sort_values('seq'); pre=gd[gd.momento=='pre'][v]; pos=gd[gd.momento=='pos'][v]
            if len(pre) and len(pos) and pd.notna(pre.iloc[0]) and pd.notna(pos.iloc[0]):
                ds.append(pos.iloc[0]-pre.iloc[0])
        if ds: per.append(np.mean(ds))
    per=np.array(per)
    if len(per)>5 and per.std()>0:
        dz=per.mean()/per.std(ddof=1); t,pv=stats.ttest_1samp(per,0)
        p(f"  {v:10s} Δ={per.mean():+.2f} dz={dz:+.2f} p={pv:.3f} (n={len(per)})")

open('res_well.txt','w').write('\n'.join(out)); print("\n[saved res_well.txt]")
