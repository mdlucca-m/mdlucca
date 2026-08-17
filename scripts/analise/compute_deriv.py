import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
h=pd.read_csv(SC+'/hum_prof.csv'); days=np.arange(1,8)
ORD=[('Vigor','Vigor'),('Fadiga','Fadiga'),('TMD','PTH'),('Tensao','Tensão'),
     ('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]
GR=3  # grau do polinômio ajustado (cúbico: permite uma inflexão)
R={'grau':GR,'vars':{}}
for k,lab in ORD:
    y=h.groupby('dia')[k].mean().reindex(days).values
    c=np.polyfit(days,y,GR); P=np.poly1d(c); dP=P.deriv(1); d2P=P.deriv(2)
    yhat=P(days); r2=float(1-((y-yhat)**2).sum()/((y-y.mean())**2).sum())
    crit=sorted([float(r.real) for r in dP.roots if abs(r.imag)<1e-6 and 1<=r.real<=7])
    infl=sorted([float(r.real) for r in d2P.roots if abs(r.imag)<1e-6 and 1<=r.real<=7])
    # dia de maior taxa de variação (|P'| máximo) no intervalo
    tt=np.linspace(1,7,601); dmax_t=float(tt[np.argmax(np.abs(dP(tt)))])
    R['vars'][k]=dict(lab=lab,coef=[float(x) for x in c],r2=r2,
        taxa_media=float((y[-1]-y[0])/6),
        dP1=float(dP(1)),dP7=float(dP(7)),
        P1=float(P(1)),P7=float(P(7)),
        crit=[round(x,1) for x in crit],infl=[round(x,1) for x in infl],
        dmax_day=round(dmax_t,1),dmax_val=float(dP(dmax_t)))
json.dump(R,open(SC+'/deriv.json','w'),indent=1,ensure_ascii=False)
print('Ajuste polinomial grau %d (médias diárias):'%GR)
for k,lab in ORD:
    v=R['vars'][k]
    print('  %-9s R²=%.2f taxa_méd=%+.2f/d P\'(1)=%+.2f P\'(7)=%+.2f inflexão=%s'%(
        lab,v['r2'],v['taxa_media'],v['dP1'],v['dP7'],v['infl']))
