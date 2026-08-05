import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats, optimize
import statsmodels.api as sm
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv'); phys=pd.read_csv(f'{SC}/phys.csv'); ext=pd.read_csv(f'{SC}/ext_load.csv')
well=pd.read_csv(f'{SC}/wellness_all.csv')
well['date']=pd.to_datetime(well['datadia'],errors='coerce')
daymap={pd.Timestamp(2024,4,20+i):i for i in range(1,8)}
well['dia']=well['date'].map(daymap)
rng=np.random.default_rng(2024)
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

# =============== A. EFFECT SIZES (D1->D7) with bootstrap CI ===============
p("="*72); p("A. TAMANHOS DE EFEITO  D1(baseline) -> D7  (por atleta, IC bootstrap 95%)"); p("="*72)
def es_paired(a,b):  # b-a
    d=b-a; dz=d.mean()/d.std(ddof=1)
    # Hedges g (paired, using average SD)
    sp=np.sqrt((a.std(ddof=1)**2+b.std(ddof=1)**2)/2); g=(b.mean()-a.mean())/sp
    J=1-3/(4*(len(d))-1); return dz, g*J
for v in ['FadFisica','Fadiga','TMD','Vigor']:
    d1=hum[hum.dia==1].groupby('ID')[v].mean(); d7=hum[hum.dia==7].groupby('ID')[v].mean()
    j=pd.concat([d1,d7],axis=1,keys=['a','b']).dropna()
    dz,g=es_paired(j.a.values,j.b.values)
    bs=[]
    for _ in range(2000):
        idx=rng.choice(len(j),len(j),replace=True); s=j.iloc[idx]; dd=s.b-s.a
        if dd.std(ddof=1)>0: bs.append(dd.mean()/dd.std(ddof=1))
    lo,hi=np.percentile(bs,[2.5,97.5])
    p(f"  {v:10s} dz={dz:+.2f} [{lo:+.2f},{hi:+.2f}]  Hedges g={g:+.2f}  (n={len(j)})")
# multivariate Mahalanobis D (6 subescalas) D1->D7 with BCa
S=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
d1=hum[hum.dia==1].groupby('ID')[S].mean(); d7=hum[hum.dia==7].groupby('ID')[S].mean()
J=d1.join(d7,lsuffix='1',rsuffix='7').dropna()
M=J[[c+'7' for c in S]].values-J[[c+'1' for c in S]].values
def mahal(M):
    m=M.mean(0); C=np.cov(M,rowvar=False); return float(np.sqrt(m@np.linalg.inv(C)@m))
D=mahal(M); bs=[mahal(M[rng.choice(len(M),len(M),True)]) for _ in range(2000)]
p(f"  Multivariada 6 subescalas: D de Mahalanobis={D:.2f}  IC95%(percentil)=[{np.percentile(bs,2.5):.2f},{np.percentile(bs,97.5):.2f}]")

# =============== B. DERIVADAS (velocidade e aceleracao da mudanca) ===============
p("\n"+"="*72); p("B. LIMITES E DERIVADAS da trajetoria (7 dias)"); p("="*72)
days=np.arange(1,8)
for v in ['TMD','FadFisica','Vigor']:
    y=hum.groupby('dia')[v].mean().reindex(days).values
    d1=np.gradient(y,days)   # 1a derivada (velocidade/dia)
    d2=np.gradient(d1,days)  # 2a derivada (aceleracao)
    imaxv=days[np.argmax(np.abs(d1))]; imaxa=days[np.argmax(np.abs(d2))]
    p(f"  {v:10s} y(D1..D7)={np.round(y,1)}")
    p(f"             velocidade/dia={np.round(d1,2)}  -> |vel| max no dia {imaxv}")
    p(f"             aceleracao   ={np.round(d2,2)}  -> |acel| max no dia {imaxa}")

# =============== C. AJUSTES NAO LINEARES (AIC) ===============
p("\n"+"="*72); p("C. CURVAS NAO LINEARES por dia (comparacao por AIC)"); p("="*72)
def aic(y,yhat,k): n=len(y); rss=np.sum((y-yhat)**2); return n*np.log(rss/n)+2*k
def logistic(t,L,k,t0,c): return c+L/(1+np.exp(-k*(t-t0)))
for v in ['TMD','FadFisica']:
    y=hum.groupby('dia')[v].mean().reindex(days).values; t=days.astype(float)
    res={}
    for name,deg in [('linear',1),('quadratico',2),('cubico',3)]:
        c=np.polyfit(t,y,deg); yh=np.polyval(c,t); res[name]=aic(y,yh,deg+1)
    # exponential y=a*exp(b*t)+c
    try:
        popt,_=optimize.curve_fit(lambda t,a,b,c:a*np.exp(b*t)+c,t,y,p0=[1,0.2,y[0]],maxfev=10000)
        yh=popt[0]*np.exp(popt[1]*t)+popt[2]; res['exponencial']=aic(y,yh,3)
    except Exception: res['exponencial']=np.nan
    # logistic
    try:
        popt,_=optimize.curve_fit(logistic,t,y,p0=[y.max()-y.min(),1,5,y.min()],maxfev=20000)
        yh=logistic(t,*popt); res['logistico']=aic(y,yh,4)
    except Exception: res['logistico']=np.nan
    best=min((k for k in res if not np.isnan(res[k])),key=lambda k:res[k])
    p(f"  {v:10s} AIC: "+"  ".join(f"{k}={res[k]:.1f}" for k in res)+f"  => melhor: {best}")

# =============== D. REGRESSAO LOGISTICA ===============
p("\n"+"="*72); p("D. AJUSTES LOGISTICOS"); p("="*72)
# D1) crescimento logistico da proporcao 'nao-iceberg' por dia
ice=[]
for d in days:
    g=hum[hum.dia==d]; neg=g[['Tensao','Depressao','Raiva','Fadiga','Confusao']].mean(axis=1)
    ice.append(1-(g['Vigor']>neg).mean())  # prop NAO-iceberg (perturbado)
ice=np.array(ice)
try:
    popt,_=optimize.curve_fit(logistic,days.astype(float),ice,p0=[0.5,1,5,0.1],maxfev=20000)
    p(f"  Crescimento logistico da prop. NAO-iceberg: L={popt[0]:.2f} k(inclinacao)={popt[1]:.2f} t0(ponto medio)={popt[2]:.2f} dia")
    p(f"    prop. nao-iceberg observada D1..D7 = {np.round(ice,2)}")
except Exception as e: p("  logistic iceberg FAIL",e)
# D2) logistica ao nivel de obs: P(fadiga fisica ALTA >=8) ~ dia + PV_base
d=hum.merge(phys[['ID','TCAR_PV_ini']],on='ID',how='left')
d['alta']=(d['FadFisica']>=8).astype(int); d['diac']=d['dia']-1
X=sm.add_constant(d[['diac','TCAR_PV_ini']].dropna()); y=d.loc[X.index,'alta']
m=sm.Logit(y,X).fit(disp=0)
p(f"  Logit P(fadiga fisica>=8): OR(dia)={np.exp(m.params['diac']):.2f} (p={m.pvalues['diac']:.3f}); OR(PV base)={np.exp(m.params['TCAR_PV_ini']):.2f} (p={m.pvalues['TCAR_PV_ini']:.3f})")
# D3) dose-resposta logistica: P(TMD alto) ~ PSE nas sessoes de HIIT
hr=pd.read_csv(f'{SC}/hr_series.csv')  # per session PSE by name
# use obs-level: within HIIT days, high TMD ~ fadiga fisica (proxy of internal cost)
hd=hum[hum.dia.isin([2,4,7])].copy(); hd['tmd_alto']=(hd['TMD']>hd['TMD'].median()).astype(int)
Xd=sm.add_constant(hd[['FadFisica']]); md=sm.Logit(hd['tmd_alto'],Xd).fit(disp=0)
p(f"  Dose-resposta logit P(TMD>mediana) ~ fadiga fisica: OR={np.exp(md.params['FadFisica']):.2f}/ponto (p={md.pvalues['FadFisica']:.4f})")

# =============== E. ESCALONAMENTO ALOMETRICO ===============
p("\n"+"="*72); p("E. ESCALONAMENTO ALOMETRICO (log-log: Y = a*massa^b)"); p("="*72)
al=phys[['ID','massa','TCAR_PV_ini']].merge(ext[['ID','vel_kmh','dist_sessao']],on='ID',how='inner')
al=al[(al['massa']>0)&(al['vel_kmh']>0)]
for yv,lab in [('TCAR_PV_ini','PV do T-CAR'),('vel_kmh','veloc. 104%'),('dist_sessao','distancia/sessao')]:
    d=al[['massa',yv]].dropna(); d=d[d[yv]>0]
    b,loga=np.polyfit(np.log(d['massa']),np.log(d[yv]),1)
    r=np.corrcoef(np.log(d['massa']),np.log(d[yv]))[0,1]
    p(f"  {lab:18s} ~ massa^{b:+.2f}  (r_loglog={r:+.2f}, n={len(d)})")
# allometrically scaled fitness (PV/massa^b) vs weekly fatigue
wk=hum.groupby('ID')['FadFisica'].mean()
al2=al.set_index('ID').join(wk).dropna()
al2['PV_scaled']=al2['TCAR_PV_ini']/(al2['massa']**0.5)
r_raw=stats.spearmanr(al2['TCAR_PV_ini'],al2['FadFisica'])
r_sc=stats.spearmanr(al2['PV_scaled'],al2['FadFisica'])
p(f"  Fadiga fisica semana ~ PV bruta: rho={r_raw.correlation:+.2f} (p={r_raw.pvalue:.3f}) | ~ PV/massa^0.5: rho={r_sc.correlation:+.2f} (p={r_sc.pvalue:.3f})")

# =============== F. CURVAS ROC (AUC com IC bootstrap, Youden) ===============
p("\n"+"="*72); p("F. CURVAS ROC (AUC, IC95% bootstrap, corte de Youden)"); p("="*72)
def roc(score,label):
    s=np.asarray(score,float); y=np.asarray(label,int); ok=~np.isnan(s)
    s,y=s[ok],y[ok]
    pos,neg=s[y==1],s[y==0]
    if len(pos)==0 or len(neg)==0: return None
    U=stats.mannwhitneyu(pos,neg).statistic; auc=U/(len(pos)*len(neg))
    if auc<0.5: auc=1-auc; s=-s; pos,neg=s[y==1],s[y==0]
    # Youden
    thr=np.unique(s); best=(0,None,0,0)
    for t in thr:
        sens=(pos>=t).mean(); spec=(neg<t).mean()
        if sens+spec-1>best[0]: best=(sens+spec-1,t,sens,spec)
    bs=[]
    for _ in range(1000):
        ip=rng.choice(len(pos),len(pos),True); ineg=rng.choice(len(neg),len(neg),True)
        U=stats.mannwhitneyu(pos[ip],neg[ineg]).statistic; bs.append(U/(len(pos)*len(neg)))
    return auc,np.percentile(bs,2.5),np.percentile(bs,97.5),best[2],best[3]
# merge TQR into obs by date+athlete-day means (day-level)
tqr_day=well.dropna(subset=['dia']).groupby('dia')['TQR'].apply(lambda s:pd.to_numeric(s,errors='coerce').mean())
# Task 1: discriminate HIIT day (obs level)
tr=hum[hum.dia.isin([2,3,4,5,6,7])].copy()
p("  [Tarefa 1] discriminar DIA de HIIT (obs, dias 2-7):")
for v in ['FadFisica','TMD','Vigor','Fadiga']:
    r=roc(tr[v] if v!='Vigor' else -tr[v], tr['HIIT'])
    if r: p(f"     {v:10s} AUC={r[0]:.2f} [{r[1]:.2f},{r[2]:.2f}] sens={r[3]:.2f} spec={r[4]:.2f}")
# Task 2: discriminate D7 vs D1 (accumulated)
p("  [Tarefa 2] discriminar D7 (acumulo) vs D1 (baseline):")
d17=hum[hum.dia.isin([1,7])].copy(); d17['y']=(d17.dia==7).astype(int)
for v in ['FadFisica','TMD','Vigor','Fadiga']:
    r=roc(d17[v] if v!='Vigor' else -d17[v], d17['y'])
    if r: p(f"     {v:10s} AUC={r[0]:.2f} [{r[1]:.2f},{r[2]:.2f}] sens={r[3]:.2f} spec={r[4]:.2f}")
# Task 3: discriminate high-fatigue day (top tertile FadFisica) by mood
p("  [Tarefa 3] discriminar DIA de fadiga fisica alta (tercil sup.) por humor:")
h=hum.dropna(subset=['FadFisica']).copy(); thr=h['FadFisica'].quantile(2/3); h['y']=(h['FadFisica']>=thr).astype(int)
for v in ['TMD','Fadiga','Vigor']:
    r=roc(h[v] if v!='Vigor' else -h[v], h['y'])
    if r: p(f"     {v:10s} AUC={r[0]:.2f} [{r[1]:.2f},{r[2]:.2f}] sens={r[3]:.2f} spec={r[4]:.2f}")

open(f'{SC}/res_robust.txt','w').write('\n'.join(out)); print("\n[saved res_robust.txt]")
