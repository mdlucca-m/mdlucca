import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv')
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
# z-standardize within sample
Z=hum[SUB].apply(lambda c:(c-c.mean())/c.std())
# canonical centroids (z-units) — Parsons-Smith et al. (2017) shapes [Tens,Dep,Raiv,Vig,Fad,Conf]
CENT={
 'Iceberg':        [-0.5,-0.5,-0.5,+1.0,-0.5,-0.5],
 'Iceberg invertido':[+0.6,+0.6,+0.6,-1.0,+0.6,+0.6],
 'Everest invertido':[+1.2,+1.4,+1.2,-0.8,+1.2,+1.2],
 'Barbatana tubarão':[+0.2,+0.2,+0.2,+0.3,+1.4,+0.2],
 'Superfície':     [0,0,0,0,0,0],
 'Submerso':       [-0.9,-0.9,-0.9,-0.9,-0.9,-0.9],
}
names=list(CENT); CMAT=np.array([CENT[k] for k in names])
def classify(row):
    d=((CMAT-row.values)**2).sum(1); return names[int(np.argmin(d))]
hum['perfil']=Z.apply(classify,axis=1)
# iceberg index (z): vigor - mean(negatives)
NEG=['Tensao','Depressao','Raiva','Fadiga','Confusao']
hum['ice_idx']=Z['Vigor']-Z[NEG].mean(axis=1)
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

p("="*80); p("DISTRIBUIÇÃO DOS 6 PERFIS DE HUMOR — global e por dia (%)"); p("="*80)
glob=hum['perfil'].value_counts(normalize=True).mul(100).round(1)
p("Global:", glob.to_dict())
tab=pd.crosstab(hum['dia'],hum['perfil'],normalize='index').mul(100).round(1)
p("\nPor dia (%):"); p(tab.to_string())

p("\n"+"="*80); p("COMO O GRUPO COMEÇA vs TERMINA A SEMANA"); p("="*80)
for d in [1,7]:
    g=hum[hum.dia==d]
    ic=100*(g['perfil']=='Iceberg').mean(); sf=100*(g['perfil']=='Barbatana tubarão').mean()
    ii=100*(g['perfil']=='Iceberg invertido').mean()
    p(f"  Dia {d}: iceberg={ic:.0f}%  barbatana={sf:.0f}%  iceberg invertido={ii:.0f}%  índice-iceberg(z) médio={g['ice_idx'].mean():+.2f}")
# shift test D1 vs D7 (iceberg index, Mann-Whitney)
u=stats.mannwhitneyu(hum[hum.dia==1]['ice_idx'],hum[hum.dia==7]['ice_idx'])
p(f"  Mann-Whitney índice-iceberg D1 vs D7: U p={u.pvalue:.2e}")

p("\n"+"="*80); p("QUAL DIA TEM MAIS VARIAÇÃO? (dispersão entre atletas e intra-dia pré→pós)"); p("="*80)
p(f"{'Dia':>3s} {'DP(ice_idx)':>11s} {'IQR TMD':>8s} {'|Δ pré→pós| médio TMD':>22s}")
varrow=[]
for d in range(1,8):
    g=hum[hum.dia==d]
    sd=g['ice_idx'].std(); iqr=g['TMD'].quantile(.75)-g['TMD'].quantile(.25)
    # intra-day pre->post abs change per athlete
    ch=[]
    for aid,ga in g.groupby('ID'):
        ga=ga.sort_values('seq'); pre=ga[ga.momento=='pre']['TMD']; pos=ga[ga.momento=='pos']['TMD']
        if len(pre) and len(pos): ch.append(abs(pos.iloc[0]-pre.iloc[0]))
    mch=np.mean(ch) if ch else np.nan
    varrow.append((d,sd,iqr,mch))
    p(f"{d:>3d} {sd:>11.2f} {iqr:>8.1f} {mch:>22.2f}")
dmaxsd=max(varrow,key=lambda r:r[1]); dmaxch=max(varrow,key=lambda r:(r[3] if not np.isnan(r[3]) else 0))
p(f"  => Maior dispersão ENTRE atletas: Dia {dmaxsd[0]}  |  Maior variação INTRA-dia (pré→pós): Dia {dmaxch[0]}")
# Levene / Fligner for homogeneity of variance across days (ice_idx)
groups=[hum[hum.dia==d]['ice_idx'].dropna() for d in range(1,8)]
fl=stats.fligner(*groups)
p(f"  Fligner-Killeen (variância do índice-iceberg difere entre dias?): stat={fl.statistic:.2f} p={fl.pvalue:.3f}")

p("\n"+"="*80); p("PRÉ vs PÓS — geral do grupo (perfis e índice)"); p("="*80)
for m in ['pre','pos']:
    g=hum[hum.momento==m]
    p(f"  {m}: índice-iceberg(z)={g['ice_idx'].mean():+.2f}  iceberg={100*(g.perfil=='Iceberg').mean():.0f}%  superfície={100*(g.perfil=='Superfície').mean():.0f}%")
w=stats.wilcoxon(*[hum[hum.momento=='pre'].groupby('ID')['ice_idx'].mean().align(hum[hum.momento=='pos'].groupby('ID')['ice_idx'].mean(),join='inner')[i].values for i in (0,1)])
p(f"  Wilcoxon pré vs pós (índice-iceberg agregado por atleta): p={w.pvalue:.4f}")

p("\n"+"="*80); p("RELAÇÃO FADIGA FÍSICA × FADIGA MENTAL × FADIGA (BRUMS)"); p("="*80)
def rmcorr(df,x,y):
    import statsmodels.formula.api as smf; from statsmodels.stats.anova import anova_lm
    d=df[['ID',x,y]].dropna().rename(columns={x:'X',y:'Y'})
    m=smf.ols('Y~C(ID)+X',data=d).fit(); a=anova_lm(m,typ=1)
    ss=a.loc['X','sum_sq']; se=a.loc['Residual','sum_sq']
    return np.sign(m.params['X'])*np.sqrt(ss/(ss+se))
pairs=[('FadFisica','Fadiga'),('FadFisica','FadMental'),('FadMental','Fadiga')]
for a,b in pairs:
    rs=stats.spearmanr(hum[a],hum[b]).correlation; rm=rmcorr(hum,a,b)
    p(f"  {a} × {b}: Spearman ρ={rs:+.2f} | rmcorr (intra-atleta)={rm:+.2f}")
# trajectory correlation of the three across days
tj=hum.groupby('dia')[['FadFisica','FadMental','Fadiga']].mean()
p("  Médias por dia:"); p(tj.round(2).to_string())

hum.to_csv(f'{SC}/hum_prof.csv',index=False)
open(f'{SC}/res_profiles.txt','w').write('\n'.join(out)); print("\n[saved hum_prof.csv, res_profiles.txt]")
