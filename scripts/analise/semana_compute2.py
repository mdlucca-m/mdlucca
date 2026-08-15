import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/hum_prof.csv'); h2=hum[hum.momento.isin(['pre','pos'])].copy()
APP=json.load(open(f'{SC}/app_data.json')); ath=pd.DataFrame(APP['socio']['athletes'])
days=np.arange(1,8)
# TMD now a CORE variable
CORE=[('Vigor','Vigor'),('Fadiga','Fadiga (BRUMS)'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental'),('TMD','PTH/TMD')]
def daily(v): return h2.dropna(subset=[v]).groupby(['ID','dia'])[v].mean().reset_index()
R={}

# ---- full descriptives helper ----
def fulldesc(x):
    x=pd.Series(x).dropna()
    return dict(n=int(x.size),mean=float(x.mean()),sd=float(x.std()),cv=float(100*x.std()/x.mean()) if x.mean()!=0 else None,
        med=float(x.median()),q1=float(x.quantile(.25)),q3=float(x.quantile(.75)),iqr=float(x.quantile(.75)-x.quantile(.25)),
        mn=float(x.min()),mx=float(x.max()),amp=float(x.max()-x.min()),skew=float(stats.skew(x)),kurt=float(stats.kurtosis(x)))

# ---- sociodemographic full descriptives ----
socio={}
for col,lab in [('idade','Idade (anos)'),('exp','Experiência (anos)'),('estatura','Estatura (cm)'),('massa','Massa corporal (kg)'),('pG','Gordura corporal (%)'),('PV','Pico de velocidade T-CAR (km/h)'),('CMJ','CMJ (cm)')]:
    if col in ath: socio[col]=dict(lab=lab,**fulldesc(ath[col]))
R['socio']=socio

# ---- BRUMS + fatigue full descriptives (week) ----
desc={}
for v,lab in [('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Vigor','Vigor'),('Fadiga','Fadiga (BRUMS)'),('Confusao','Confusão'),('TMD','PTH/TMD'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental')]:
    d=fulldesc(h2[v]); d['lab']=lab; d['floor']=float(100*(h2[v].dropna()==h2[v].dropna().min()).mean()); desc[v]=d
R['desc']=desc

# ---- chronic D1 vs D7 (daily mean) ----
cron={}
for v,lab in CORE:
    w=daily(v).pivot(index='ID',columns='dia',values=v)
    a=w[1].dropna(); b=w[7].dropna(); c=a.index.intersection(b.index); a,b=a.loc[c],b.loc[c]; diff=b-a
    cron[v]=dict(lab=lab,d1=float(a.mean()),d7=float(b.mean()),delta=float(b.mean()-a.mean()),dz=float(diff.mean()/diff.std()),
        p=float(stats.wilcoxon(a,b).pvalue),pct=float(100*(b.mean()-a.mean())/a.mean()) if a.mean()!=0 else None,
        worse=float(100*((diff<0).mean() if v=='Vigor' else (diff>0).mean())))
R['cron']=cron

# ---- acute pré vs pós (week + per day) ----
agu={}; agu_day={}
for v,lab in CORE:
    pre=h2[h2.momento=='pre'].groupby('ID')[v].mean(); pos=h2[h2.momento=='pos'].groupby('ID')[v].mean()
    c=pre.index.intersection(pos.index); a,b=pre.loc[c],pos.loc[c]; diff=b-a
    agu[v]=dict(lab=lab,pre=float(a.mean()),pos=float(b.mean()),delta=float(b.mean()-a.mean()),dz=float(diff.mean()/diff.std()),p=float(stats.wilcoxon(a,b).pvalue))
    byd={}
    for dd in days:
        g=h2[h2.dia==dd]; pr=g[g.momento=='pre'].groupby('ID')[v].mean(); po=g[g.momento=='pos'].groupby('ID')[v].mean()
        cc=pr.index.intersection(po.index)
        if len(cc)>=3:
            aa,bb=pr.loc[cc],po.loc[cc]; d2=bb-aa
            byd[int(dd)]=dict(pre=float(aa.mean()),pos=float(bb.mean()),delta=float(bb.mean()-aa.mean()),
                dz=float(d2.mean()/d2.std()) if d2.std()>0 else None,p=float(stats.wilcoxon(aa,bb).pvalue) if d2.std()>0 else None)
    agu_day[v]=byd
R['agu']=agu; R['agu_day']=agu_day

# ---- decomposition + derivatives/inflection ----
dec={}; der={}
for v,lab in CORE:
    d=h2.dropna(subset=[v]); m=smf.ols(f'{v} ~ C(ID)+C(dia)',data=d).fit(); a=anova_lm(m,typ=1)
    ss=a['sum_sq']; tot=ss['C(ID)']+ss['C(dia)']+ss['Residual']; etm=np.sqrt(a.loc['Residual','mean_sq'])
    dm=daily(v).groupby('dia')[v].mean().reindex(days); sig=dm.max()-dm.min(); nday=d.groupby('dia').size().mean()
    dec[v]=dict(lab=lab,pday=100*ss['C(dia)']/tot,ptrait=100*ss['C(ID)']/tot,pnoise=100*ss['Residual']/tot,
        etm=float(etm),mdc=float(1.96*np.sqrt(2)*etm),mdc_g=float(1.96*np.sqrt(2)*etm/np.sqrt(nday)),sig=float(sig),snr=float(sig/etm))
    dmv=dm.values; c=np.polyfit(days,dmv,3); infl=-c[1]/(3*c[0]) if c[0]!=0 else np.nan
    turn=[float(r.real) for r in np.roots(np.polyder(c,1)) if abs(r.imag)<1e-6 and 1<=r.real<=7]
    vel=np.polyval(np.polyder(c,1),days)
    der[v]=dict(lab=lab,daymean=dmv.tolist(),infl=(float(infl) if 1<=infl<=7 else None),turn=sorted(turn),vel_d1=float(vel[0]),vel_d7=float(vel[-1]))
R['dec']=dec; R['der']=der

# ---- responsiveness ranking ----
R['rank']=[dict(v=v,lab=lab,dz_ag=abs(agu[v]['dz']),dz_cr=abs(cron[v]['dz']),snr=dec[v]['snr'],pday=dec[v]['pday']) for v,lab in CORE]

# ---- perfil tab + baseline/final (D1 pré vs D7 pós) incl TMD ----
PROF=['Iceberg','Barbatana tubarão','Superfície','Submerso','Iceberg invertido','Everest invertido']
R['perfil_tab']=pd.crosstab(hum['dia'],hum['perfil'],normalize='index').mul(100).reindex(columns=PROF).fillna(0).round(1).to_dict()
di=hum.dropna(subset=['ice_idx']); iceday=di.groupby('dia')['ice_idx'].mean().reindex(days).values
ci=np.polyfit(days,iceday,3); R['ice']=dict(day=iceday.tolist(),infl=float(-ci[1]/(3*ci[0])))
BF={}
for v,lab in CORE:
    base=hum[(hum.dia==1)&(hum.momento=='pre')].groupby('ID')[v].mean(); fin=hum[(hum.dia==7)&(hum.momento=='pos')].groupby('ID')[v].mean()
    c=base.index.intersection(fin.index); a,b=base.loc[c],fin.loc[c]; d=b-a
    BF[v]=dict(lab=lab,base=float(a.mean()),base_sd=float(a.std()),fin=float(b.mean()),fin_sd=float(b.std()),
        delta=float(b.mean()-a.mean()),dz=float(d.mean()/d.std()),p=float(stats.wilcoxon(a,b).pvalue),pct=float(100*(b.mean()-a.mean())/a.mean()) if a.mean()!=0 else None,n=int(len(c)))
json.dump(BF,open(f'{SC}/baseline_final.json','w'),indent=1)
json.dump(R,open(f'{SC}/semana2.json','w'),indent=1)
print('CRONICO/AGUDO incl TMD:')
for v,l in CORE: print('  %-16s D1->D7 dz=%+.2f | pré-pós dz=%+.2f | SNR=%.2f | inflexão=%s'%(l,cron[v]['dz'],agu[v]['dz'],dec[v]['snr'],('dia%.1f'%der[v]['infl'] if der[v]['infl'] else 'n/d')))
print('TMD baseline->final: %.2f -> %.2f (%+.0f%%) dz=%+.2f p=%.4f'%(BF['TMD']['base'],BF['TMD']['fin'],BF['TMD']['pct'],BF['TMD']['dz'],BF['TMD']['p']))
print('saved semana2.json, baseline_final.json')
