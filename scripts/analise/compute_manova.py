import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv'); TS=json.load(open('tscore.json'))
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']  # POMS order for MANOVA tables
NM={'Vigor':'Vigor','Fadiga':'Fadiga','Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
mu=TS['mu']; sd=TS['sd']
def Tsc(k,x): return 50+10*(x-mu[k])/sd[k]
def eta_cls(e): return 'pequeno' if e<0.06 else ('médio' if e<0.14 else 'grande')
def d_cls(d):
    a=abs(d); return 'trivial' if a<0.2 else ('pequeno' if a<0.5 else ('médio' if a<0.8 else 'grande'))
R={}
def paired_block(g1mask,g2mask,by,v1,v2,name):
    # build paired matrix on ID for two conditions
    dm=h.groupby(['ID',by])[SUB].mean().reset_index()
    P={k:dm.pivot(index='ID',columns=by,values=k) for k in SUB}
    idx=None
    for k in SUB:
        a=P[k][v1].dropna().index; b=P[k][v2].dropna().index
        ii=a.intersection(b); idx=ii if idx is None else idx.intersection(ii)
    # difference matrix (T-score units)
    D=np.column_stack([Tsc(k,P[k][v2].loc[idx])-Tsc(k,P[k][v1].loc[idx]) for k in SUB])
    n,p=D.shape; dbar=D.mean(0); S=np.cov(D,rowvar=False)
    T2=n*dbar@np.linalg.pinv(S)@dbar; F=(n-p)/(p*(n-1))*T2; df1=p; df2=n-p
    from scipy.stats import f as fdist
    pval=1-fdist.cdf(F,df1,df2)
    wilks=1/(1+T2/(n-1))
    rows=[]
    for k in SUB:
        a=Tsc(k,P[k][v1].loc[idx]); b=Tsc(k,P[k][v2].loc[idx]); diff=b-a
        t,pt=stats.ttest_rel(b,a); Fu=t**2
        etap=Fu/(Fu+(n-1))
        try: W,pw=stats.wilcoxon(P[k][v1].loc[idx],P[k][v2].loc[idx])
        except: W,pw=np.nan,np.nan
        dz=diff.mean()/diff.std(ddof=1) if diff.std(ddof=1)>0 else 0
        rows.append(dict(k=k,lab=NM[k],m1=float(a.mean()),s1=float(a.std(ddof=1)),m2=float(b.mean()),s2=float(b.std(ddof=1)),
            F=float(Fu),p=float(pt),d=float(dz),eta=float(etap),eta_cls=eta_cls(etap),d_cls=d_cls(dz),
            wlcx_p=float(pw),sig=bool(pt<0.05)))
    R[name]=dict(n=int(n),wilks=float(wilks),Fmv=float(F),df1=int(df1),df2=int(df2),p_mv=float(pval),
        T2=float(T2),eta_mv=float(1-wilks),rows=rows)
paired_block(h.dia==1,h.dia==7,'dia',1,7,'d1d7')
paired_block(h.momento=='pre',h.momento=='pos','momento','pre','pos','prepos')
# one-way repeated MANOVA across 7 days: use Friedman multivar? report per-var RM-ANOVA F (already have Friedman). Add RM-ANOVA omnibus per var:
dm=h.groupby(['ID','dia'])[SUB].mean().reset_index()
rm={}
for k in SUB:
    M=dm.pivot(index='ID',columns='dia',values=k).dropna()
    n,kk=M.shape; x=M.values; gm=x.mean()
    SSsubj=kk*((x.mean(1)-gm)**2).sum(); SStime=n*((x.mean(0)-gm)**2).sum(); SStot=((x-gm)**2).sum(); SSerr=SStot-SSsubj-SStime
    dft=kk-1; dfe=(n-1)*(kk-1); F=(SStime/dft)/(SSerr/dfe)
    from scipy.stats import f as fdist
    pval=1-fdist.cdf(F,dft,dfe); etap=SStime/(SStime+SSerr)
    rm[k]=dict(F=float(F),p=float(pval),df1=int(dft),df2=int(dfe),eta=float(etap),eta_cls=eta_cls(etap))
R['rm_days']=rm
json.dump(R,open('manova.json','w'),indent=1,ensure_ascii=False)
print('D1 vs D7 MANOVA: Wilks=%.3f F(%d,%d)=%.2f p=%.4f eta2=%.3f'%(R['d1d7']['wilks'],R['d1d7']['df1'],R['d1d7']['df2'],R['d1d7']['Fmv'],R['d1d7']['p_mv'],R['d1d7']['eta_mv']))
for r in R['d1d7']['rows']: print('  %-10s T:%.1f(%.1f)->%.1f(%.1f) F=%.2f p=%.3f d=%+.2f eta2=%.3f(%s)'%(r['lab'],r['m1'],r['s1'],r['m2'],r['s2'],r['F'],r['p'],r['d'],r['eta'],r['eta_cls']))
print('Pré vs Pós MANOVA: Wilks=%.3f F(%d,%d)=%.2f p=%.4f eta2=%.3f'%(R['prepos']['wilks'],R['prepos']['df1'],R['prepos']['df2'],R['prepos']['Fmv'],R['prepos']['p_mv'],R['prepos']['eta_mv']))
