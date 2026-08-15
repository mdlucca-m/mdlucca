import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy.optimize import minimize
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'

# ================= rmcorr matrix (within-athlete) =================
hum=pd.read_csv(f'{SC}/hum_prof.csv'); h2=hum[hum.momento.isin(['pre','pos'])].copy()
V=[('Vigor','Vigor'),('Fadiga','Fadiga BRUMS'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental'),('TMD','PTH/TMD')]
keys=[k for k,_ in V]
def rmcorr(df,x,y):
    d=df[['ID',x,y]].dropna().rename(columns={x:'X',y:'Y'})
    m=smf.ols('Y~C(ID)+X',data=d).fit(); a=anova_lm(m,typ=1)
    ss=a.loc['X','sum_sq']; se=a.loc['Residual','sum_sq']
    return float(np.sign(m.params['X'])*np.sqrt(ss/(ss+se)))
Rm=pd.DataFrame(np.eye(len(keys)),index=keys,columns=keys)
for i,x in enumerate(keys):
    for y in keys[i+1:]:
        r=rmcorr(h2,x,y); Rm.loc[x,y]=r; Rm.loc[y,x]=r
print('rmcorr (intra-atleta):'); print(Rm.round(2).to_string())
json.dump({'R':Rm.round(3).to_dict(),'labels':{k:l for k,l in V}},open(f'{SC}/rmcorr.json','w'),indent=1)

# ================= 6-factor CFA (ML) on 24 BRUMS items =================
it=pd.read_csv(f'{SC}/items.csv')
SUBIT=[('Tensão',['Apavorado','Ansioso','Preocupado','Tenso']),('Depressão',['Deprimido','Desanimado','Triste','Infeliz']),
 ('Raiva',['Irritado','Zangado','ComRaiva','MalHumorado']),('Vigor',['Animado','ComDisposição','ComEnergia','Alerta']),
 ('Fadiga',['Esgotado','Exausto','Sonolento','Cansado']),('Confusão',['Confuso','Inseguro','Desorientado','Indeciso'])]
items=[i for _,g in SUBIT for i in g]
X=it[items].apply(pd.to_numeric,errors='coerce').dropna()
N=len(X); S=np.corrcoef(X.T.values); p=len(items); nf=6
fac_of=np.repeat(np.arange(nf),4)   # item -> factor
def build(theta):
    lam=theta[:p]; logpsi=theta[p:2*p]; ch=theta[2*p:]
    C=np.zeros((nf,nf)); C[np.tril_indices(nf)]=ch
    Phi=C@C.T; d=np.sqrt(np.diag(Phi)); Phi=Phi/np.outer(d,d)   # normalize to correlation
    L=np.zeros((p,nf))
    for i in range(p): L[i,fac_of[i]]=lam[i]
    Sig=L@Phi@L.T+np.diag(np.exp(logpsi))
    return Sig,Phi,L
def fitfun(theta):
    Sig,_,_=build(theta)
    try:
        s,ld=np.linalg.slogdet(Sig)
        if s<=0: return 1e6
        Si=np.linalg.inv(Sig)
        F=ld+np.trace(S@Si)-np.linalg.slogdet(S)[1]-p
        return F if np.isfinite(F) else 1e6
    except Exception: return 1e6
# start values
lam0=np.full(p,0.7); psi0=np.log(np.full(p,0.5))
sub_scores=pd.DataFrame({name:X[g].mean(1) for name,g in SUBIT}); C0=np.linalg.cholesky(np.corrcoef(sub_scores.T.values)+1e-6*np.eye(nf))
th0=np.concatenate([lam0,psi0,C0[np.tril_indices(nf)]])
res=minimize(fitfun,th0,method='Nelder-Mead',options={'maxiter':40000,'xatol':1e-4,'fatol':1e-6})
res=minimize(fitfun,res.x,method='Powell',options={'maxiter':40000})
Fmin=res.fun; Sig,Phi,L=build(res.x)
npar_=p+p+ (nf*(nf+1)//2) - nf   # loadings+resid+factor corr (minus nf scale redundancy)
dfm=p*(p+1)//2 - npar_
chi2=(N-1)*Fmin
# null (independence) model
Snull=np.eye(p); Fnull=np.linalg.slogdet(np.diag(np.diag(S)))[1]+np.trace(S@np.linalg.inv(np.diag(np.diag(S))))-np.linalg.slogdet(S)[1]-p
chi2_null=(N-1)*Fnull; df_null=p*(p-1)//2
rmsea=np.sqrt(max(chi2-dfm,0)/(dfm*(N-1)))
cfi=1-max(chi2-dfm,0)/max(chi2_null-df_null,1e-9)
tli=((chi2_null/df_null)-(chi2/dfm))/((chi2_null/df_null)-1)
resid=S-Sig; srmr=np.sqrt(np.mean(resid[np.tril_indices(p)]**2))
loads=[abs(L[i,fac_of[i]]) for i in range(p)]
subload={name:[float(abs(L[items.index(i),fac_of[items.index(i)]])) for i in g] for name,g in SUBIT}
print('\nCFA 6 fatores (ML, %d itens, N=%d obs):'%(p,N))
print('  chi2=%.0f df=%d | CFI=%.3f TLI=%.3f RMSEA=%.3f SRMR=%.3f'%(chi2,dfm,cfi,tli,rmsea,srmr))
print('  cargas padronizadas por subescala (faixa):')
for name,ls in subload.items(): print('    %-10s %.2f–%.2f'%(name,min(ls),max(ls)))
FAC=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
Phidf=pd.DataFrame(Phi,index=FAC,columns=FAC)
print('  correlações entre fatores:'); print(Phidf.round(2).to_string())
json.dump(dict(chi2=float(chi2),df=int(dfm),cfi=float(cfi),tli=float(tli),rmsea=float(rmsea),srmr=float(srmr),
    N=int(N),subload={k:[round(x,2) for x in v] for k,v in subload.items()},Phi=Phidf.round(3).to_dict(),FAC=FAC),
    open(f'{SC}/cfa.json','w'),indent=1)
print('\nsaved rmcorr.json, cfa.json')
