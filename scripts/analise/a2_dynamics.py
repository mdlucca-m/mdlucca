import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
from scipy import stats
import statsmodels.formula.api as smf
hum=pd.read_csv('humor.csv'); phys=pd.read_csv('phys.csv')
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)
rng=np.random.default_rng(7)
VARS=['FadFisica','Fadiga','TMD','Vigor','FadMental','Tensao','Depressao','Raiva','Confusao']

def fdr(pv):
    pv=np.asarray(pv); o=np.argsort(pv); r=np.empty_like(o); r[o]=np.arange(1,len(pv)+1)
    q=pv*len(pv)/r
    # enforce monotonicity
    qs=q[o][::-1]; qs=np.minimum.accumulate(qs)[::-1]; adj=np.empty_like(q); adj[o]=qs
    return np.clip(adj,0,1)

# ================= DAY EFFECT =================
p("=== EFEITO DO DIA (modelo misto, intercepto aleatorio atleta) ===")
rowsp=[]
for v in VARS:
    d=hum[['ID','dia',v]].dropna().rename(columns={v:'y'}); d['dia']=d['dia'].astype(int)
    m=smf.mixedlm('y~C(dia)',d,groups=d['ID']).fit(reml=False)
    # omnibus via Wald on dia terms
    terms=[t for t in m.params.index if t.startswith('C(dia)')]
    R=np.array([[1 if t==tt else 0 for tt in m.params.index] for t in terms])
    wald=float(m.params[terms].values @ np.linalg.inv(m.cov_params().loc[terms,terms].values) @ m.params[terms].values)
    dfn=len(terms); F=wald/dfn; pval=stats.chi2.sf(wald,dfn)
    # eta2p approx from F
    # ICC athlete
    va=m.cov_re.iloc[0,0]; icc=va/(va+m.scale)
    rowsp.append((v,F,pval,icc))
pvals=[r[2] for r in rowsp]; q=fdr(pvals)
for (v,F,pval,icc),qq in zip(rowsp,q):
    p(f"  {v:10s} F~{F:5.2f} p={pval:.4f} p_FDR={qq:.4f} ICC_atleta={icc:.2f}")

# ================= ACUTE PRE->POST (aggregate by athlete) =================
p("\n=== RESPOSTA AGUDA PRE->POS (agregada por atleta, dias 2-7) ===")
train=hum[hum.dia.isin([2,3,4,5,6,7])]
acute={}
for v in VARS:
    per=[]
    for aid,g in train.groupby('ID'):
        deltas=[]
        for dia,gd in g.groupby('dia'):
            gd=gd.sort_values('seq')
            pre=gd[gd.momento=='pre'][v]; pos=gd[gd.momento=='pos'][v]
            if len(pre) and len(pos) and pd.notna(pre.iloc[0]) and pd.notna(pos.iloc[0]):
                deltas.append(pos.iloc[0]-pre.iloc[0])
        if deltas: per.append(np.mean(deltas))
    per=np.array(per)
    dz=per.mean()/per.std(ddof=1)
    t,pt=stats.ttest_1samp(per,0)
    try: w,pw=stats.wilcoxon(per)
    except: pw=np.nan
    # cluster bootstrap CI on dz
    bs=[]
    for _ in range(2000):
        s=rng.choice(per,len(per),replace=True)
        if s.std(ddof=1)>0: bs.append(s.mean()/s.std(ddof=1))
    lo,hi=np.percentile(bs,[2.5,97.5])
    acute[v]=dict(delta=per.mean(),dz=dz,pt=pt,pw=pw,lo=lo,hi=hi,n=len(per))
q=fdr([acute[v]['pt'] for v in VARS])
for v,qq in zip(VARS,q):
    a=acute[v]; a['pfdr']=qq
    p(f"  {v:10s} Δ={a['delta']:+.2f} dz={a['dz']:+.2f} [{a['lo']:+.2f},{a['hi']:+.2f}] p={a['pt']:.3f} pW={a['pw']:.3f} pFDR={qq:.3f} {'*' if qq<0.05 else 'ns'}")

# ================= FLOOR <-> RESPONSIVENESS (feeds Article 1) =================
p("\n=== INTERFACE PISO x RESPONSIVIDADE (subescalas) ===")
floors={'Fadiga':7.7,'Vigor':8.5,'Tensao':49.6,'Depressao':67.1,'Raiva':59.6,'Confusao':80.5}
xs=[]; ys=[]
for s in floors:
    xs.append(floors[s]); ys.append(abs(acute[s]['dz']))
    p(f"  {s:10s} %piso={floors[s]:5.1f}  |dz|={abs(acute[s]['dz']):.2f}")
r=np.corrcoef(xs,ys)[0,1]; b,a0=np.polyfit(xs,ys,1)
p(f"  correlacao |dz| ~ %piso: r={r:.2f}  R2={r**2:.2f}  |dz|={a0:.3f}{b:+.5f}*piso")

# ================= HIIT vs NON-HIIT (day level, paired by athlete) =================
p("\n=== HIIT vs TECNICO-TATICO (nivel do dia, pareado por atleta) ===")
tr=hum[hum.dia.isin([2,3,4,5,6,7])]
for v in ['FadFisica','Fadiga','TMD','Vigor']:
    a=tr[tr.HIIT==1].groupby('ID')[v].mean(); b=tr[tr.HIIT==0].groupby('ID')[v].mean()
    j=pd.concat([a,b],axis=1,keys=['H','N']).dropna()
    d=(j.H-j.N); dz=d.mean()/d.std(ddof=1); t,pv=stats.ttest_rel(j.H,j.N)
    p(f"  {v:10s} HIIT={j.H.mean():.2f} nao={j.N.mean():.2f} Δ={d.mean():+.2f} dz={dz:+.2f} p={pv:.3f}")

# ================= MULTIVARIATE: Hotelling T2 paired + PERMANOVA =================
p("\n=== MULTIVARIADA (perfil 6 subescalas, pre->pos agregado por atleta) ===")
S=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
M=[]
for aid,g in train.groupby('ID'):
    dd=[]
    for dia,gd in g.groupby('dia'):
        gd=gd.sort_values('seq'); pre=gd[gd.momento=='pre']; pos=gd[gd.momento=='pos']
        if len(pre) and len(pos): dd.append(pos[S].iloc[0].values-pre[S].iloc[0].values)
    if dd: M.append(np.mean(dd,axis=0))
M=np.array(M); nA=len(M); pp=len(S)
mean=M.mean(0); cov=np.cov(M,rowvar=False)
T2=nA*mean@np.linalg.inv(cov)@mean
F=(nA-pp)/(pp*(nA-1))*T2; Fp=stats.f.sf(F,pp,nA-pp)
Dmah=np.sqrt(mean@np.linalg.inv(cov)@mean)
p(f"  Hotelling T2: F({pp},{nA-pp})={F:.2f} p={Fp:.3f}  D_Mahalanobis={Dmah:.2f}")
# energy-fatigue axis only
S2=['Vigor','Fadiga']; M2=M[:,[S.index('Vigor'),S.index('Fadiga')]]
mean2=M2.mean(0); cov2=np.cov(M2,rowvar=False)
T2b=nA*mean2@np.linalg.inv(cov2)@mean2; F2=(nA-2)/(2*(nA-1))*T2b; F2p=stats.f.sf(F2,2,nA-2)
p(f"  Eixo energia-fadiga: F(2,{nA-2})={F2:.2f} p={F2p:.3f}  D={np.sqrt(mean2@np.linalg.inv(cov2)@mean2):.2f}")

# PERMANOVA pre vs pos, permutation restricted within athlete
def permanova(df, factorcol, S, nperm=5000):
    Z=(df[S]-df[S].mean())/df[S].std()
    X=Z.values; g=df[factorcol].values; ids=df['ID'].values
    def ss(g):
        tot=((X-X.mean(0))**2).sum()
        wg=0
        for lev in np.unique(g):
            Xi=X[g==lev]; wg+=((Xi-Xi.mean(0))**2).sum()
        a=len(np.unique(g)); N=len(X)
        return (tot-wg)/(a-1)/(wg/(N-a))
    F0=ss(g); cnt=0
    for _ in range(nperm):
        gp=g.copy()
        for aid in np.unique(ids):
            idx=np.where(ids==aid)[0]; gp[idx]=rng.permutation(g[idx])
        if ss(gp)>=F0: cnt+=1
    return F0,(cnt+1)/(nperm+1)
tt=train.dropna(subset=S).copy()
F0,pv=permanova(tt,'momento',S,3000)
p(f"  PERMANOVA pre vs pos (perm restrita ao atleta): pseudo-F={F0:.2f} p={pv:.4f}")
F0h,pvh=permanova(tt,'HIIT',S,3000)
p(f"  PERMANOVA HIIT vs nao: pseudo-F={F0h:.2f} p={pvh:.4f}")

# ================= FITNESS-FATIGUE / MODERATION =================
p("\n=== APTIDAO PREVIA x FADIGA DA SEMANA (moderacao, entre atletas) ===")
wk=hum.groupby('ID')[['FadFisica','TMD']].mean()
mo=wk.join(phys.set_index('ID')[['TCAR_PV_ini']]).dropna()
r1=stats.spearmanr(mo.TCAR_PV_ini,mo.FadFisica); r2=stats.spearmanr(mo.TCAR_PV_ini,mo.TMD)
p(f"  T-CAR PV x fadiga fisica (semana): rho={r1.correlation:.2f} p={r1.pvalue:.3f}")
p(f"  T-CAR PV x TMD medio (semana):     rho={r2.correlation:.2f} p={r2.pvalue:.3f}")
dz_tcar=(phys.TCAR_PV_final-phys.TCAR_PV_ini).mean()/(phys.TCAR_PV_final-phys.TCAR_PV_ini).std(ddof=1)
dz_cmj=(phys.CMJ_mai-phys.CMJ_ini).mean()/(phys.CMJ_mai-phys.CMJ_ini).std(ddof=1)
p(f"  Adaptacao: T-CAR ΔPV={ (phys.TCAR_PV_final-phys.TCAR_PV_ini).mean():.2f} dz={dz_tcar:.2f}; CMJ Δ={(phys.CMJ_mai-phys.CMJ_ini).mean():.2f} dz={dz_cmj:.2f}")

open('res_a2.txt','w').write('\n'.join(out)); print("\n[saved res_a2.txt]")
