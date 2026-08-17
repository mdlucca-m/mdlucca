import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
from scipy import stats
h=pd.read_csv(SC+'/hum_prof.csv'); days=np.arange(1,8)
# ordem canônica POMS/BRUMS: Tensão–Depressão–Raiva–Vigor–Fadiga–Confusão–TMD
ORD=[('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Vigor','Vigor'),
     ('Fadiga','Fadiga'),('Confusao','Confusão'),('TMD','PTH')]
GR=3  # grau do polinômio ajustado (cúbico: permite uma inflexão)
tt=np.linspace(1,7,601)
R={'grau':GR,'vars':{}}
dcurves={}   # curvas da 1ª derivada P'(t) para análise de acoplamento
for k,lab in ORD:
    y=h.groupby('dia')[k].mean().reindex(days).values
    c=np.polyfit(days,y,GR); P=np.poly1d(c); dP=P.deriv(1); d2P=P.deriv(2)
    yhat=P(days); r2=float(1-((y-yhat)**2).sum()/((y-y.mean())**2).sum())
    crit=sorted([float(r.real) for r in dP.roots if abs(r.imag)<1e-6 and 1<=r.real<=7])
    infl=sorted([float(r.real) for r in d2P.roots if abs(r.imag)<1e-6 and 1<=r.real<=7])
    dcurves[k]=dP(tt)
    # extremos da FUNÇÃO P(t) e limites da DERIVADA P'(t) no intervalo [1,7]
    Pv=P(tt); dPv=dP(tt)
    fmax_i=int(np.argmax(Pv)); fmin_i=int(np.argmin(Pv))
    dmax_i=int(np.argmax(dPv)); dmin_i=int(np.argmin(dPv))
    R['vars'][k]=dict(lab=lab,coef=[float(x) for x in c],r2=r2,
        taxa_media=float((y[-1]-y[0])/6),
        dP1=float(dP(1)),dP7=float(dP(7)),
        d2P1=float(d2P(1)),d2P7=float(d2P(7)),    # 2ª derivada (aceleração) nas bordas
        conc1=('convexa' if d2P(1)>0 else 'côncava'),  # concavidade no início
        P1=float(P(1)),P7=float(P(7)),
        crit=[round(x,1) for x in crit],infl=[round(x,1) for x in infl],
        # extremos da função (valor máx/mín e dia)
        fmax_day=round(float(tt[fmax_i]),1),fmax_val=float(Pv[fmax_i]),
        fmin_day=round(float(tt[fmin_i]),1),fmin_val=float(Pv[fmin_i]),
        # limites da derivada (taxa máx de subida e de queda, e dia)
        dmax_day=round(float(tt[dmax_i]),1),dmax_val=float(dPv[dmax_i]),
        dmin_day=round(float(tt[dmin_i]),1),dmin_val=float(dPv[dmin_i]))
# ---- acoplamento entre variáveis: correlação das curvas de 1ª derivada ----
KS=[k for k,_ in ORD]
R['couple']={}
for i,a in enumerate(KS):
    for b in KS[i+1:]:
        r=float(np.corrcoef(dcurves[a],dcurves[b])[0,1])
        R['couple']['%s|%s'%(a,b)]=r
json.dump(R,open(SC+'/deriv.json','w'),indent=1,ensure_ascii=False)
print('Ajuste polinomial grau %d — 1ª e 2ª derivadas:'%GR)
for k,lab in ORD:
    v=R['vars'][k]
    print('  %-9s R²=%.2f | P\'(1)=%+.2f P\'(7)=%+.2f | P\"(1)=%+.2f P\"(7)=%+.2f (%s) | inflexão=%s'%(
        lab,v['r2'],v['dP1'],v['dP7'],v['d2P1'],v['d2P7'],v['conc1'],v['infl']))
print('\nAcoplamento (corr das curvas P\'): Vigor|Fadiga=%.2f  Vigor|TMD=%.2f  Fadiga|TMD=%.2f'%(
    R['couple'].get('Vigor|Fadiga',float('nan')),R['couple'].get('Vigor|TMD',float('nan')),R['couple'].get('Fadiga|TMD',float('nan'))))
