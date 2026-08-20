import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy.stats import wilcoxon, mannwhitneyu, spearmanr
from scipy.interpolate import UnivariateSpline
h=pd.read_csv('hum_prof.csv')
auth=pd.read_csv('auth_full.csv')[['ID','PV']]
DIMS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),
      ('Confusao','Confusão'),('TMD','PTH'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental')]
KEYS=[k for k,_ in DIMS]
OUT={'dims':[[k,l] for k,l in DIMS]}
def val(dia,mo,k):
    s=h[(h.dia==dia)&(h.momento==mo)][['ID',k]].dropna(); return s.set_index('ID')[k]
def paired(a,b):
    j=a.index.intersection(b.index); aa=a.loc[j].values.astype(float); bb=b.loc[j].values.astype(float); d=bb-aa
    n=len(d); dz=float(d.mean()/d.std(ddof=1)) if n>1 and d.std()>0 else 0.0
    try: p=float(wilcoxon(aa,bb).pvalue) if n>=6 and np.any(d!=0) else 1.0
    except Exception: p=1.0
    return dict(n=n,dm=float(d.mean()),dz=dz,p=p,sig=bool(p<0.05))

# ===== 1) TRANSIÇÕES SEQUENCIAIS (12) x todas as variáveis =====
seq=[(1,'baseline')]+sum([[(d,'pre'),(d,'pos')] for d in range(2,8)],[])
labs={'baseline':'base','pre':'pré','pos':'pós'}
trans=[]
for i in range(len(seq)-1):
    (d0,m0),(d1,m1)=seq[i],seq[i+1]
    tipo='Agudo' if d0==d1 else 'Recuperação'
    lab='D%d %s → D%d %s'%(d0,labs[m0],d1,labs[m1])
    row={'lab':lab,'tipo':tipo,'vars':{k:paired(val(d0,m0,k),val(d1,m1,k)) for k in KEYS}}
    trans.append(row)
OUT['trans']=trans

# ===== 2) PRÉ vs PÓS por dia (D2-D7) x todas =====
byday={}
for d in range(2,8):
    byday[d]={k:paired(val(d,'pre',k),val(d,'pos',k)) for k in KEYS}
OUT['prepos_dia']=byday
# pré/pós geral da semana
OUT['prepos_semana']={k:paired(h[h.momento=='pre'].groupby('ID')[k].mean(),h[h.momento=='pos'].groupby('ID')[k].mean()) for k in KEYS}

# ===== 3) EFEITO AGUDO (média pré->pós intradia) vs CRÔNICO (D1->D7) por variável =====
ac={}
for k in KEYS:
    ags=[t['vars'][k]['dm'] for t in trans if t['tipo']=='Agudo']       # dentro do dia
    recs=[t['vars'][k]['dm'] for t in trans if t['tipo']=='Recuperação']# entre dias
    a=h[h.dia==1].groupby('ID')[k].mean(); b=h[h.dia==7].groupby('ID')[k].mean()
    cr=paired(a,b)
    ac[k]={'agudo_medio':float(np.mean(ags)),'recuperacao_media':float(np.mean(recs)),
           'cronico_delta':cr['dm'],'cronico_dz':cr['dz'],'cronico_p':cr['p'],'cronico_sig':cr['sig']}
OUT['agudo_cronico']=ac

# ===== 4) LIMITES e DERIVADAS (spline 13 pontos) por variável =====
x=np.array([d + (-0.2 if m=='pre' else 0.2 if m=='pos' else 0.0) for d,m in seq])
xx=np.linspace(x.min(),x.max(),400)
deriv={}
for k in KEYS:
    y=np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m in seq])
    s=UnivariateSpline(x,y,k=4,s=len(x)*np.var(y)*0.85); ys=s(xx); d1=s.derivative(1)(xx); d2=s.derivative(2)(xx)
    sign=np.sign(d2); zc=np.where(np.diff(sign)!=0)[0]
    infl=[float(xx[j]) for j in zc]
    jv=int(np.argmax(np.abs(d1)))
    deriv[k]={'min':float(ys.min()),'max':float(ys.max()),'min_dia':float(xx[np.argmin(ys)]),'max_dia':float(xx[np.argmax(ys)]),
        'inflexao':infl,'vel_pico':float(d1[jv]),'vel_pico_dia':float(xx[jv]),'acel_pico':float(np.max(np.abs(d2)))}
OUT['derivadas']=deriv

# ===== 5) AJUSTE PELA APTIDÃO: mais vs menos aptos (mediana de PV) =====
wk=h.dropna(subset=['dia']).groupby('ID').agg(**{k:(k,'mean') for k in KEYS}).reset_index()
d1=h[h.dia==1].groupby('ID').agg(**{'d1_'+k:(k,'mean') for k in KEYS}).reset_index()
d7=h[h.dia==7].groupby('ID').agg(**{'d7_'+k:(k,'mean') for k in KEYS}).reset_index()
M=auth.merge(d1,on='ID').merge(d7,on='ID')
med=M['PV'].median(); M['grupo']=np.where(M['PV']>=med,'Mais aptos','Menos aptos')
OUT['pv_mediana']=float(med)
strat={}
for k in KEYS:
    M['delta_'+k]=M['d7_'+k]-M['d1_'+k]
    hi=M[M.grupo=='Mais aptos']['delta_'+k].dropna(); lo=M[M.grupo=='Menos aptos']['delta_'+k].dropna()
    try: p=float(mannwhitneyu(hi,lo).pvalue)
    except Exception: p=1.0
    # correlacao PV x deterioracao
    d=M[['PV','delta_'+k]].dropna(); r,pr=spearmanr(d['PV'],d['delta_'+k])
    strat[k]={'mais_aptos_delta':float(hi.mean()),'menos_aptos_delta':float(lo.mean()),'p_grupos':p,
              'rho_PV':float(r),'p_PV':float(pr),'n_hi':int(len(hi)),'n_lo':int(len(lo))}
OUT['estratificacao']=strat
M[['ID','PV','grupo']+['delta_'+k for k in KEYS]].to_csv('strat_pv.csv',index=False)

# ===== 6) LIMIARES: mudança confiável por variável (MDC a partir do ICC) =====
import numpy as np
lim={}
for k in KEYS:
    piv=h.dropna(subset=['dia']).groupby(['ID','dia'])[k].mean().unstack('dia').dropna()
    if piv.shape[1]<2: continue
    # ICC(2,1) via ANOVA de duas vias
    x2=piv.values; n,kk=x2.shape; gm=x2.mean()
    ms_r=kk*((x2.mean(1)-gm)**2).sum()/(n-1); ms_c=n*((x2.mean(0)-gm)**2).sum()/(kk-1)
    ms_e=((x2-x2.mean(1,keepdims=True)-x2.mean(0,keepdims=True)+gm)**2).sum()/((n-1)*(kk-1))
    icc=(ms_r-ms_e)/(ms_r+(kk-1)*ms_e+kk*(ms_c-ms_e)/n) if (ms_r+(kk-1)*ms_e+kk*(ms_c-ms_e)/n)!=0 else 0
    sd=piv.stack().std(ddof=1); sem=sd*np.sqrt(max(0,1-icc)); mdc95=1.96*np.sqrt(2)*sem
    lim[k]={'icc':float(icc),'sem':float(sem),'mdc95':float(mdc95),'swc':float(0.2*piv.mean(1).std(ddof=1))}
OUT['limiares']=lim

json.dump(OUT,open('temporal.json','w'),ensure_ascii=False,indent=1)
print('OK temporal.json')
print('\n=== TRANSIÇÕES SIGNIFICATIVAS (p<0,05) — onde e quanto ===')
for t in trans:
    sig=[(l,t['vars'][k]) for k,l in DIMS if t['vars'][k]['sig']]
    if sig: print(' %-22s [%s] -> '%(t['lab'],t['tipo'])+', '.join('%s dz=%+.2f (p=%.3f)'%(l,v['dz'],v['p']) for l,v in sig))
print('\n=== EFEITO AGUDO médio vs CRÔNICO (D1->D7) por variável ===')
for k,l in DIMS:
    a=ac[k]; print('  %-13s agudo(intradia)=%+.2f | crônico(D1->D7)=%+.2f dz=%+.2f %s'%(l,a['agudo_medio'],a['cronico_delta'],a['cronico_dz'],'*' if a['cronico_sig'] else ''))
print('\n=== APTIDÃO: mais vs menos aptos — deterioração D1->D7 ===')
for k,l in DIMS:
    s=strat[k]; print('  %-13s mais=%+.1f menos=%+.1f p=%.3f | PV×Δ rho=%+.2f p=%.3f'%(l,s['mais_aptos_delta'],s['menos_aptos_delta'],s['p_grupos'],s['rho_PV'],s['p_PV']))
print('\n=== DERIVADAS: inflexão e pico de velocidade por variável ===')
for k,l in DIMS:
    dv=deriv[k]; inf=('dia %.1f'%dv['inflexao'][0]) if dv['inflexao'] else 'n/d'
    print('  %-13s inflexão %s | vel.pico %+.1f no dia %.1f'%(l,inf,dv['vel_pico'],dv['vel_pico_dia']))
