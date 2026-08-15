import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import statsmodels.formula.api as smf
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
it=pd.read_csv(f'{SC}/items.csv')
SUBIT={'Tensão':['Apavorado','Ansioso','Preocupado','Tenso'],'Depressão':['Deprimido','Desanimado','Triste','Infeliz'],
 'Raiva':['Irritado','Zangado','ComRaiva','MalHumorado'],'Vigor':['Animado','ComDisposição','ComEnergia','Alerta'],
 'Fadiga':['Esgotado','Exausto','Sonolento','Cansado'],'Confusão':['Confuso','Inseguro','Desorientado','Indeciso']}
def alpha(X):
    X=X.dropna(); k=X.shape[1]; vi=X.var(ddof=1).sum(); vt=X.sum(1).var(ddof=1)
    return (k/(k-1))*(1-vi/vt)
def omega(X):
    X=X.dropna(); Xs=(X-X.mean())/X.std(); R=np.corrcoef(Xs.T.values)
    w,V=np.linalg.eigh(R); lam=V[:,-1]*np.sqrt(w[-1])          # 1-factor loadings (first PC)
    if lam.sum()<0: lam=-lam
    sl=lam.sum(); err=np.sum(1-lam**2); return sl**2/(sl**2+err)
def mic(X):  # mean inter-item correlation
    R=np.corrcoef(X.dropna().T.values); return (R.sum()-len(R))/(len(R)*(len(R)-1))
rel={}
print('CONFIABILIDADE INTERNA (subescalas BRUMS):')
for sub,items in SUBIT.items():
    X=it[items].apply(pd.to_numeric,errors='coerce')
    a=alpha(X); w=omega(X); m=mic(X); rel[sub]=dict(k=len(items),alpha=float(a),omega=float(w),mic=float(m))
    print('  %-10s α=%.2f  ω=%.2f  r̄(inter-item)=%.2f'%(sub,a,w,m))
json.dump(rel,open(f'{SC}/reliab.json','w'),indent=1)

# ---------- MULTIVARIATE (energy-fatigue axis: 4 primary vars, TMD excluded as derived) ----------
hum=pd.read_csv(f'{SC}/hum_prof.csv'); h2=hum[hum.momento.isin(['pre','pos'])].copy()
V=['Vigor','Fadiga','FadFisica','FadMental']; LB={'Vigor':'Vigor','Fadiga':'Fadiga BRUMS','FadFisica':'Fadiga física','FadMental':'Fadiga mental'}
# trait-level (between-athlete) correlation matrix
am=h2.groupby('ID')[V].mean(); Rtrait=am.corr()
print('\nCORRELAÇÃO ENTRE-ATLETAS (traço):'); print(Rtrait.round(2).to_string())

# multivariate mixed model (stacked long): value ~ var + var:dia, random intercept athlete + var
long=h2.melt(id_vars=['ID','dia'],value_vars=V,var_name='var',value_name='y').dropna()
# z-standardize within variable so scales are comparable
long['y']=long.groupby('var')['y'].transform(lambda s:(s-s.mean())/s.std())
full=smf.mixedlm('y ~ C(var) + C(var):dia', long, groups=long['ID'], re_formula='~C(var)').fit(reml=False)
null=smf.mixedlm('y ~ C(var)', long, groups=long['ID'], re_formula='~C(var)').fit(reml=False)
lr=2*(full.llf-null.llf); dfd=len(full.params)-len(null.params); pjoint=stats.chi2.sf(lr,dfd)
print('\nMODELO MISTO MULTIVARIADO — efeito conjunto do dia (LRT): chi2(%d)=%.1f p=%.2e'%(dfd,lr,pjoint))

# Hotelling T2 + Mahalanobis D for D1 vs D7 (paired, 4-dim)
d1=h2[h2.dia==1].groupby('ID')[V].mean(); d7=h2[h2.dia==7].groupby('ID')[V].mean()
c=d1.index.intersection(d7.index); Dmat=(d7.loc[c]-d1.loc[c]).values; nD=len(c); p=len(V)
mbar=Dmat.mean(0); S=np.cov(Dmat.T); Sinv=np.linalg.pinv(S)
T2=nD*mbar@Sinv@mbar; F=(nD-p)/(p*(nD-1))*T2; pF=stats.f.sf(F,p,nD-p); Dmah=np.sqrt(mbar@Sinv@mbar)
print('Hotelling T² D1 vs D7: T²=%.2f F(%d,%d)=%.2f p=%.4f | D de Mahalanobis=%.2f'%(T2,p,nD-p,F,pF,Dmah))

json.dump(dict(Rtrait=Rtrait.round(3).to_dict(),lr=float(lr),dfd=int(dfd),pjoint=float(pjoint),
    T2=float(T2),F=float(F),pF=float(pF),dfn=p,dfden=int(nD-p),mahal=float(Dmah),n=int(nD)),
    open(f'{SC}/mv.json','w'),indent=1)
print('\nsaved reliab.json, mv.json')
