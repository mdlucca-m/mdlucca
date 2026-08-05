import warnings; warnings.filterwarnings('ignore')
import openpyxl, pandas as pd, numpy as np
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
wb=openpyxl.load_workbook(f'{SC}/../../../../root/.claude/uploads/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/f15454c2-Backup__Banco_de_dados.xlsx' if False else '/root/.claude/uploads/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/f15454c2-Backup__Banco_de_dados.xlsx', data_only=True)
ws=wb['Diário - Treino']; rows=list(ws.iter_rows(values_only=True))
cols={'nome':52,'fis':3,'men':4,'TMD':60,'Vigor':57,'Fadiga':58,'FadFisica':61,'FadMental':62,'datadia':67}
d=pd.DataFrame([{k:r[i] for k,i in cols.items()} for r in rows[1:] if r[52]])
scale={'Péssimo':1,'Ruim':2,'Regular':3,'Bem':4,'Muito bem':5}
d['fis_o']=d['fis'].map(scale); d['men_o']=d['men'].map(scale)
d['date']=pd.to_datetime(d['datadia'],errors='coerce')
daymap={pd.Timestamp(2024,4,20+i):i for i in range(1,8)}
d['dia']=d['date'].map(daymap); d=d[d['dia'].notna()].copy(); d['dia']=d['dia'].astype(int)
d['HIIT']=d['dia'].isin([2,4,7]).astype(int)
for c in ['TMD','Vigor','Fadiga','FadFisica','FadMental']: d[c]=pd.to_numeric(d[c],errors='coerce')
d=d.sort_values(['nome','dia']); d['seq']=d.groupby(['nome','dia']).cumcount()
last=d.groupby(['nome','dia'])['seq'].transform('max')
d['momento']=np.where(d['seq']==0,'pre',np.where(d['seq']==last,'pos','mid'))
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

p(f"janela 21-27/04: {len(d)} obs, {d.nome.nunique()} atletas (Péssimo1..Muito bem5)")
p("\n=== DISTRIBUICAO / MEDIA ===")
for v,lab in [('fis_o','Estado FÍSICO'),('men_o','Estado MENTAL')]:
    s=d[v].dropna(); p(f"  {lab:14s} n={len(s)} media={s.mean():.2f} DP={s.std():.2f} %baixo(<=2)={100*(s<=2).mean():.0f}%")

p("\n=== EFEITO DO DIA (modelo misto) ===")
for v,lab in [('fis_o','FÍSICO'),('men_o','MENTAL')]:
    dd=d[['nome','dia',v]].dropna().rename(columns={v:'y'})
    m=smf.mixedlm('y~C(dia)',dd,groups=dd.nome).fit(reml=False)
    terms=[t for t in m.params.index if t.startswith('C(dia)')]
    wald=float(m.params[terms].values@np.linalg.inv(m.cov_params().loc[terms,terms].values)@m.params[terms].values)
    F=wald/len(terms); pv=stats.chi2.sf(wald,len(terms)); va=m.cov_re.iloc[0,0]; icc=va/(va+m.scale)
    p(f"  {lab:8s} F~{F:.2f} p={pv:.4f} ICC={icc:.2f}  D1={dd[dd.dia==1].y.mean():.2f}->D7={dd[dd.dia==7].y.mean():.2f}")

p("\n=== HIIT vs NAO (nivel do dia, pareado) ===")
tr=d[d.dia.isin([2,3,4,5,6,7])]
for v,lab in [('fis_o','FÍSICO'),('men_o','MENTAL')]:
    a=tr[tr.HIIT==1].groupby('nome')[v].mean(); b=tr[tr.HIIT==0].groupby('nome')[v].mean()
    j=pd.concat([a,b],axis=1,keys=['H','N']).dropna(); dz=(j.H-j.N).mean()/(j.H-j.N).std(ddof=1); t,pv=stats.ttest_rel(j.H,j.N)
    p(f"  {lab:8s} HIIT={j.H.mean():.2f} nao={j.N.mean():.2f} dz={dz:+.2f} p={pv:.3f}")

p("\n=== VALIDADE CONVERGENTE COM O BRUMS (rmcorr intra-atleta) ===")
def rmcorr(df,x,y):
    dd=df[['nome',x,y]].dropna().rename(columns={x:'X',y:'Y'})
    m=smf.ols('Y~C(nome)+X',data=dd).fit(); aov=anova_lm(m,typ=1)
    ssx=aov.loc['X','sum_sq']; sse=aov.loc['Residual','sum_sq']
    return np.sign(m.params['X'])*np.sqrt(ssx/(ssx+sse)), len(dd)
for v,lab in [('fis_o','FÍSICO'),('men_o','MENTAL')]:
    for m_ in ['Vigor','Fadiga','FadFisica','TMD']:
        r,n=rmcorr(d,v,m_); p(f"  {lab:8s} x {m_:9s}: rmcorr={r:+.2f} (n={n})")
    p("")

p("=== RESPOSTA AGUDA PRE->POS (agregada por atleta) ===")
for v,lab in [('fis_o','FÍSICO'),('men_o','MENTAL')]:
    per=[]
    for aid,g in tr.groupby('nome'):
        ds=[]
        for dia,gd in g.groupby('dia'):
            gd=gd.sort_values('seq'); pre=gd[gd.momento=='pre'][v]; pos=gd[gd.momento=='pos'][v]
            if len(pre) and len(pos) and pd.notna(pre.iloc[0]) and pd.notna(pos.iloc[0]): ds.append(pos.iloc[0]-pre.iloc[0])
        if ds: per.append(np.mean(ds))
    per=np.array(per); dz=per.mean()/per.std(ddof=1); t,pv=stats.ttest_1samp(per,0)
    p(f"  {lab:8s} Δ={per.mean():+.2f} dz={dz:+.2f} p={pv:.3f} (n={len(per)})")

p("\n=== PODER DISCRIMINANTE: item unico 'estado fisico' detecta dia de fadiga alta? (ROC) ===")
# fatigue-high day = top tertile of FadFisica
dd=d[['fis_o','FadFisica']].dropna()
thr=dd.FadFisica.quantile(2/3); y=(dd.FadFisica>=thr).astype(int); x=-dd.fis_o  # lower state -> higher fatigue
# AUC via Mann-Whitney
from scipy.stats import mannwhitneyu
pos=x[y==1]; neg=x[y==0]; U,_=mannwhitneyu(pos,neg); auc=U/(len(pos)*len(neg))
p(f"  AUC(estado fisico -> dia fadiga alta)={auc:.2f} (n={len(dd)})")

open(f'{SC}/res_self.txt','w').write('\n'.join(out)); print("\n[saved res_self.txt]")
