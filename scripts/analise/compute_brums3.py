import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv')
SUB6=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]
KEYS=[k for k,_ in SUB6]; LAB={k:l for k,l in SUB6}
days=np.arange(1,8)
R={}

# ---- 1) Shapiro-Wilk (observation level) ----
R['shapiro']={}
for k,_ in SUB6:
    x=h[k].dropna(); W,p=stats.shapiro(x)
    R['shapiro'][k]=dict(W=float(W),p=float(p),skew=float(stats.skew(x)),kurt=float(stats.kurtosis(x)))

# ---- 2) ICC(2,1) and ICC(2,k) from athlete x day matrix (daily means) ----
dm=h.groupby(['ID','dia'])[KEYS].mean().reset_index()
def icc(k):
    M=dm.pivot(index='ID',columns='dia',values=k).dropna()  # complete cases
    n,kk=M.shape; x=M.values; gm=x.mean()
    SSR=kk*((x.mean(1)-gm)**2).sum(); SSC=n*((x.mean(0)-gm)**2).sum(); SST=((x-gm)**2).sum(); SSE=SST-SSR-SSC
    MSR=SSR/(n-1); MSC=SSC/(kk-1); MSE=SSE/((n-1)*(kk-1))
    icc1=(MSR-MSE)/(MSR+(kk-1)*MSE+kk*(MSC-MSE)/n)
    icck=(MSR-MSE)/(MSR+(MSC-MSE)/n)
    return dict(icc1=float(icc1),icck=float(icck),n=int(n),k=int(kk))
def icc_cls(v):
    return 'pobre' if v<0.5 else ('moderada' if v<0.75 else ('boa' if v<0.9 else 'excelente'))
R['icc']={k:{**icc(k),'cls':icc_cls(icc(k)['icc1'])} for k,_ in SUB6}

# ---- 3) pairwise Spearman (trait = athlete weekly means), rho + p ----
wk=h.groupby('ID')[KEYS].mean()
pairs=[]
for i in range(len(KEYS)):
    for j in range(i+1,len(KEYS)):
        a,b=KEYS[i],KEYS[j]; r,p=stats.spearmanr(wk[a],wk[b],nan_policy='omit')
        pairs.append(dict(a=LAB[a],b=LAB[b],rho=float(r),p=float(p)))
R['pairs']=pairs

# ---- 4) each subscale x Vigor and x Fadiga (trait), rho+p ----
R['axis']={}
for k,_ in SUB6:
    if k in ('Vigor','Fadiga'): continue
    rv,pv=stats.spearmanr(wk[k],wk['Vigor'],nan_policy='omit'); rf,pf=stats.spearmanr(wk[k],wk['Fadiga'],nan_policy='omit')
    R['axis'][k]=dict(rho_vig=float(rv),p_vig=float(pv),rho_fad=float(rf),p_fad=float(pf))

# ---- 5) D1/D7 focus with p ----
def focus(d):
    sub=dm[dm.dia==d]; out={}
    for neg in ['Depressao','Raiva','Confusao','Tensao']:
        rf,pf=stats.spearmanr(sub[neg],sub['Fadiga'],nan_policy='omit'); rv,pv=stats.spearmanr(sub[neg],sub['Vigor'],nan_policy='omit')
        out[neg]=dict(rho_fad=float(rf),p_fad=float(pf),rho_vig=float(rv),p_vig=float(pv))
    return out
R['focusp']={'D1':focus(1),'D7':focus(7)}
json.dump(R,open('brums_stats3.json','w'),indent=1,ensure_ascii=False)
print('Shapiro-Wilk (todas p<0,001 => não normal):')
for k,_ in SUB6: s=R['shapiro'][k]; print('  %-10s W=%.3f p=%.1e skew=%+.2f'%(k,s['W'],s['p'],s['skew']))
print('\nICC(2,1) [consistência entre dias]:')
for k,_ in SUB6: v=R['icc'][k]; print('  %-10s ICC1=%.2f ICCk=%.2f (%s)'%(k,v['icc1'],v['icck'],v['cls']))
print('\nCorrelações significativas (trait):')
for pr in R['pairs']:
    if pr['p']<0.05: print('  %-10s × %-10s ρ=%+.2f p=%.3f'%(pr['a'],pr['b'],pr['rho'],pr['p']))
