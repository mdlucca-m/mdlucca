import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.nonparametric.smoothers_lowess import lowess
import plotly.graph_objects as go
from plotly.subplots import make_subplots
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
FIG='/home/user/mdlucca/Artigos/figuras'; os.makedirs(FIG,exist_ok=True)
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/hum_prof.csv')
# use only pre (first) and pos (last) of each day, per the two-collections/day design
h2=hum[hum.momento.isin(['pre','pos'])].copy()
CORE=[('Vigor','Vigor'),('Fadiga','Fadiga (BRUMS)'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental')]
DESCV=CORE+[('TMD','PTH/TMD'),('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]
days=np.arange(1,8)
R={}

def daily(v):  # per-athlete daily value = mean(pre,pos)
    return h2.dropna(subset=[v]).groupby(['ID','dia'])[v].mean().reset_index()

# 1) DESCRITIVA GERAL (semana) + LIMITES
desc={}
for v,lab in DESCV:
    x=h2[v].dropna()
    desc[v]=dict(lab=lab,n=int(x.size),mean=float(x.mean()),sd=float(x.std()),med=float(x.median()),
        iqr=float(x.quantile(.75)-x.quantile(.25)),mn=float(x.min()),mx=float(x.max()),amp=float(x.max()-x.min()))
R['desc']=desc

# 2) CRÔNICO D1 (baseline) vs D7  (per-athlete daily mean)
cron={}
for v,lab in CORE:
    d=daily(v); w=d.pivot(index='ID',columns='dia',values=v)
    a=w[1].dropna(); b=w[7].dropna(); c=a.index.intersection(b.index)
    a,b=a.loc[c],b.loc[c]; diff=b-a
    dz=diff.mean()/diff.std(); p=stats.wilcoxon(a,b).pvalue
    pct=100*(b.mean()-a.mean())/a.mean() if a.mean()!=0 else np.nan
    worse=100*((diff>0).mean() if v!='Vigor' else (diff<0).mean())
    cron[v]=dict(lab=lab,d1=float(a.mean()),d7=float(b.mean()),delta=float(b.mean()-a.mean()),dz=float(dz),p=float(p),pct=float(pct),worse=float(worse))
R['cron']=cron

# 3) AGUDO pré vs pós (semana agregada por atleta) + por dia
agu={}; agu_day={}
for v,lab in CORE:
    pre=h2[h2.momento=='pre'].groupby('ID')[v].mean(); pos=h2[h2.momento=='pos'].groupby('ID')[v].mean()
    c=pre.index.intersection(pos.index); a,b=pre.loc[c],pos.loc[c]; diff=b-a
    dz=diff.mean()/diff.std(); p=stats.wilcoxon(a,b).pvalue
    agu[v]=dict(lab=lab,pre=float(a.mean()),pos=float(b.mean()),delta=float(b.mean()-a.mean()),dz=float(dz),p=float(p))
    byd={}
    for dd in days:
        g=h2[h2.dia==dd]; pr=g[g.momento=='pre'].groupby('ID')[v].mean(); po=g[g.momento=='pos'].groupby('ID')[v].mean()
        cc=pr.index.intersection(po.index)
        if len(cc)>=3:
            aa,bb=pr.loc[cc],po.loc[cc]; dd2=bb-aa
            byd[int(dd)]=dict(pre=float(aa.mean()),pos=float(bb.mean()),delta=float(bb.mean()-aa.mean()),
                dz=float(dd2.mean()/dd2.std()) if dd2.std()>0 else None,
                p=float(stats.wilcoxon(aa,bb).pvalue) if dd2.std()>0 else None)
    agu_day[v]=byd
R['agu']=agu; R['agu_day']=agu_day

# 4) DECOMPOSIÇÃO sinal/traço/ruído + ETM/MDC/SNR + reliab (on pre/pos data)
dec={}
for v,lab in CORE:
    d=h2.dropna(subset=[v])
    m=smf.ols(f'{v} ~ C(ID)+C(dia)',data=d).fit(); a=anova_lm(m,typ=1)
    ss=a['sum_sq']; tot=ss['C(ID)']+ss['C(dia)']+ss['Residual']
    etm=np.sqrt(a.loc['Residual','mean_sq']); mdc=1.96*np.sqrt(2)*etm
    dmean=daily(v).groupby('dia')[v].mean().reindex(days); sig=dmean.max()-dmean.min()
    nday=d.groupby('dia').size().mean()
    dec[v]=dict(lab=lab,pday=100*ss['C(dia)']/tot,ptrait=100*ss['C(ID)']/tot,pnoise=100*ss['Residual']/tot,
        etm=float(etm),mdc=float(mdc),mdc_g=float(mdc/np.sqrt(nday)),sig=float(sig),snr=float(sig/etm),rel=float(1-ss['Residual']/tot))
R['dec']=dec

# 5) LIMITES + DERIVADAS + INFLEXÃO por variável (cubic on daily means)
der={}
for v,lab in CORE+[('TMD','PTH/TMD')]:
    dm=daily(v).groupby('dia')[v].mean().reindex(days).values
    c=np.polyfit(days,dm,3); c3,c2,c1,c0=c
    infl=-c2/(3*c3) if c3!=0 else np.nan
    infl_valid = (1<=infl<=7)
    d1=np.polyder(c,1); roots=[float(r.real) for r in np.roots(d1) if abs(r.imag)<1e-6 and 1<=r.real<=7]
    vel=np.polyval(d1,days); acc=np.polyval(np.polyder(c,2),days)
    der[v]=dict(lab=lab,daymean=dm.tolist(),infl=(float(infl) if infl_valid else None),turn=sorted(roots),
        vel={int(x):float(y) for x,y in zip(days,vel)},acc={int(x):float(y) for x,y in zip(days,acc)},
        vel_d1=float(vel[0]),vel_d7=float(vel[-1]))
R['der']=der

# 6) SENSIBILIDADE/RESPONSIVIDADE ranking (|dz| agudo, |dz| crônico, SNR)
rank=[]
for v,lab in CORE:
    rank.append(dict(v=v,lab=lab,dz_ag=abs(agu[v]['dz']),dz_cr=abs(cron[v]['dz']),snr=dec[v]['snr'],pday=dec[v]['pday']))
R['rank']=rank

# 7) PERFIS (%) por dia + índice-iceberg trajetória e inflexão
PROF=['Iceberg','Barbatana tubarão','Superfície','Submerso','Iceberg invertido','Everest invertido']
tabp=pd.crosstab(hum['dia'],hum['perfil'],normalize='index').mul(100).reindex(columns=PROF).fillna(0).round(1)
R['perfil_tab']=tabp.to_dict()
di=hum.dropna(subset=['ice_idx']); iceday=di.groupby('dia')['ice_idx'].mean().reindex(days).values
ci=np.polyfit(days,iceday,3); ice_infl=-ci[1]/(3*ci[0])
R['ice']=dict(day=iceday.tolist(),infl=float(ice_infl))

json.dump(R,open(f'{SC}/semana.json','w'),indent=1)
print('CRONICO D1->D7:')
for v,l in CORE:
    c=cron[v]; print('  %-16s %.2f->%.2f dz=%+.2f p=%.3f pctmud=%+.0f%% piora=%.0f%%'%(l,c['d1'],c['d7'],c['dz'],c['p'],c['pct'],c['worse']))
print('AGUDO pre->pos (semana):')
for v,l in CORE:
    a=agu[v]; print('  %-16s %.2f->%.2f dz=%+.2f p=%.4f'%(l,a['pre'],a['pos'],a['dz'],a['p']))
print('DECOMP + INFLEXAO:')
for v,l in CORE:
    d=dec[v]; e=der[v]; print('  %-16s sinal=%.0f%% ruido=%.0f%% SNR=%.2f inflexao=%s virada=%s'%(l,d['pday'],d['pnoise'],d['snr'],('dia%.2f'%e['infl'] if e['infl'] else 'n/d'),[round(x,1) for x in e['turn']]))
print('saved semana.json')
