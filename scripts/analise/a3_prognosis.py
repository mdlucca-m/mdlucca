import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
from scipy import stats
hum=pd.read_csv('humor.csv'); phys=pd.read_csv('phys.csv')
pre=pd.read_csv('comp_pre.csv'); comp=pd.read_csv('comp_comp.csv'); pos=pd.read_csv('comp_pos.csv')
inj=pd.read_csv('injuries.csv')
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)
rng=np.random.default_rng(3)

# ============ PHASE-LEVEL MOOD TRAJECTORY ============
p("=== TRAJETORIA DE HUMOR POR FASE (TMD baixo=melhor; Vigor alto=melhor) ===")
d1=hum[hum.dia==1]; d7=hum[hum.dia==7]
phases=[('Microciclo D1 (baseline)',d1),('Microciclo D7 (choque)',d7),
        ('Pre-competicao',pre),('Competicao',comp),('Pos-competicao',pos)]
for nm,df in phases:
    p(f"  {nm:26s} n={len(df):3d}  TMD={df.TMD.mean():+.2f}  Vigor={df.Vigor.mean():.2f}  Fadiga={df.Fadiga.mean():.2f}  FadFis={df.FadFisica.mean():.2f}")

# iceberg proportion per phase (vigor > mean of 5 negatives)
def iceberg(df):
    neg=df[['Tensao','Depressao','Raiva','Fadiga','Confusao']].mean(axis=1)
    return 100*(df['Vigor']>neg).mean()
p("\n  %% perfil iceberg:")
for nm,df in phases:
    p(f"    {nm:26s} {iceberg(df):.0f}%")

# ============ TAPER REVERSAL: paired D7 -> pre-comp (matched by ID) ============
p("\n=== REVERSAO PELO TAPER: D7 (choque) -> pre-competicao (pareado por atleta) ===")
d7i=d7.groupby('ID')[['TMD','Vigor','FadFisica']].mean()
prei=pre.dropna(subset=['ID']).groupby('ID')[['TMD','Vigor','FadFisica']].mean()
j=d7i.join(prei,lsuffix='_d7',rsuffix='_pre',how='inner')
p(f"  atletas pareados n={len(j)}")
for v in ['TMD','Vigor','FadFisica']:
    a=j[f'{v}_d7']; b=j[f'{v}_pre']; d=b-a
    dz=d.mean()/d.std(ddof=1); t,pv=stats.ttest_rel(b,a)
    p(f"  {v:9s} D7={a.mean():+.2f} -> pre-comp={b.mean():+.2f}  Δ={d.mean():+.2f} dz={dz:+.2f} p={pv:.4f}")

# ============ WITHIN-MICROCYCLE FEATURES -> PRE-COMP STATE ============
p("\n=== TRACO/TRAJETORIA DO MICROCICLO PREDIZ ESTADO PRE-COMPETICAO? ===")
# per-athlete features in microcycle
feat=[]
for aid,g in hum.groupby('ID'):
    g=g.sort_values('dia')
    b=g[g.dia==1]['TMD'].mean(); e=g[g.dia==7]['TMD'].mean()
    slope=np.polyfit(g['dia'],g['TMD'],1)[0] if g['dia'].nunique()>2 else np.nan
    feat.append(dict(ID=aid, micro_TMD_mean=g.TMD.mean(), micro_FadFis_mean=g.FadFisica.mean(),
                     micro_TMD_slope=slope, micro_D7_TMD=e))
feat=pd.DataFrame(feat)
mg=feat.merge(prei.reset_index().rename(columns={'TMD':'pre_TMD','Vigor':'pre_Vigor','FadFisica':'pre_FadFis'}),on='ID')
p(f"  n pareado={len(mg)}")
for xf,yf in [('micro_TMD_mean','pre_TMD'),('micro_FadFis_mean','pre_FadFis'),('micro_TMD_slope','pre_TMD')]:
    dd=mg[[xf,yf]].dropna(); r=stats.spearmanr(dd[xf],dd[yf])
    p(f"  {xf:18s} -> {yf:10s}: rho={r.correlation:+.2f} p={r.pvalue:.3f} (n={len(dd)})")

# ============ INJURY CASE-CONTROL (hypothesis-generating) ============
p("\n=== PERFIL DOS ATLETAS LESIONADOS vs COORTE (gerador de hipoteses) ===")
inj_ids=[i for i in inj.ID.dropna().unique()]
p(f"  lesionados (IDs anonimizados): {sorted(inj_ids)}  (n={len(inj_ids)})")
prof=feat.merge(phys[['ID','TCAR_PV_ini','pGordura']],on='ID',how='left')
prof['lesao']=prof.ID.isin(inj_ids).astype(int)
for v in ['micro_FadFis_mean','micro_TMD_mean','TCAR_PV_ini']:
    gL=prof[prof.lesao==1][v]; gN=prof[prof.lesao==0][v]
    # standardized diff (Hedges g-ish)
    sp=np.sqrt(((len(gL)-1)*gL.var()+(len(gN)-1)*gN.var())/(len(gL)+len(gN)-2))
    g=(gL.mean()-gN.mean())/sp if sp>0 else np.nan
    p(f"  {v:20s} lesionados={gL.mean():.2f} coorte={gN.mean():.2f}  g={g:+.2f}")

# ============ CONVERGENT VALIDITY: extra instruments at pre-comp ============
p("\n=== VALIDADE CONVERGENTE (pre-comp): humor x sono/ansiedade/burnout ===")
ex=pre.dropna(subset=['ID']).groupby('ID')[['TMD','Vigor','Fadiga','PSQI','SCAT','ABQ']].mean()
for inst in ['PSQI','SCAT','ABQ']:
    for m in ['TMD','Vigor','Fadiga']:
        dd=ex[[inst,m]].dropna()
        if len(dd)>5:
            r=stats.spearmanr(dd[inst],dd[m])
            p(f"  {inst} x {m:6s}: rho={r.correlation:+.2f} p={r.pvalue:.3f} (n={len(dd)})")
p(f"  Descritivas pre-comp: PSQI={ex.PSQI.mean():.1f} SCAT={ex.SCAT.mean():.1f} ABQ={ex.ABQ.mean():.2f}")

open('res_a3.txt','w').write('\n'.join(out)); print("\n[saved res_a3.txt]")
