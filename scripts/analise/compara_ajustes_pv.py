# -*- coding: utf-8 -*-
# Qual ajuste pelo pico de velocidade e mais confiavel?
#  Compara, nos mesmos dados (PV x humor semanal, n=25):
#   (A) ALOMETRICO  : log(y) = a + b*log(PV)   -> y = a'*PV^b  (multiplicativo; exige y>0)
#   (L) LOGARITMICO : y = a + b*log(PV)         (so o preditor em log; usa todos os dados)
#   (lin) linear    : y = a + b*PV              (referencia)
#  Criterios de confiabilidade:
#   - RMSE por validacao cruzada leave-one-out, SEMPRE na escala original de y
#   - fracao de dados usada (o alometrico perde os zeros no log)
#   - estabilidade do coeficiente por bootstrap (CV do slope)
#   - normalidade dos residuos (Shapiro) na escala em que cada modelo e ajustado
import warnings; warnings.filterwarnings('ignore')
import numpy as np, json
from scipy import stats
pm=json.load(open('pv_mood_matched.json'))
PV=np.array(pm['Vigor']['PV']); rng=np.random.default_rng(7)
LAB={'FadFisica':'Fadiga física','Vigor':'Vigor','Fadiga':'Fadiga','TMD':'PTH'}

def fit_pred(xtr,ytr,xte,kind):
    # retorna previsao na escala ORIGINAL de y para xte
    if kind=='alo':
        b,a=np.polyfit(np.log(xtr),np.log(ytr),1); return np.exp(a+b*np.log(xte))
    if kind=='log':
        b,a=np.polyfit(np.log(xtr),ytr,1); return a+b*np.log(xte)
    b,a=np.polyfit(xtr,ytr,1); return a+b*xte

def loo_rmse(x,y,kind):
    # para 'alo' usa apenas y>0 (limitacao do modelo); os demais usam tudo
    err=[]
    idx=np.arange(len(x))
    for i in idx:
        tr=idx!=i
        xtr,ytr=x[tr],y[tr]
        if kind=='alo':
            m=ytr>0.05; xtr,ytr=xtr[m],ytr[m]
            if y[i]<=0.05: continue          # nao ha como avaliar no log; ponto fora do dominio
        pred=fit_pred(xtr,ytr,x[i],kind)
        err.append((pred-y[i])**2)
    return float(np.sqrt(np.mean(err))), len(err)

def slope_boot(x,y,kind,B=3000):
    sl=[]
    for _ in range(B):
        s=rng.integers(0,len(x),len(x)); xs,ys=x[s],y[s]
        if kind=='alo':
            m=ys>0.05; xs,ys=xs[m],ys[m]
            if len(xs)<5: continue
            b=np.polyfit(np.log(xs),np.log(ys),1)[0]
        elif kind=='log': b=np.polyfit(np.log(xs),ys,1)[0]
        else: b=np.polyfit(xs,ys,1)[0]
        sl.append(b)
    sl=np.array(sl); return float(np.median(sl)),float(np.percentile(sl,2.5)),float(np.percentile(sl,97.5)),float(np.std(sl))

print("=== COMPARACAO DE AJUSTES PELO PICO DE VELOCIDADE ===\n")
out={}
for k in ['FadFisica','Vigor']:
    y=np.array(pm[k]['mood']); n0=(y>0.05).sum()
    print(f"### {LAB[k]}  (n={len(y)}; usados no alometrico: {n0})")
    row={}
    for kind,nome in [('alo','Alométrico (log-log)'),('log','Logarítmico (y~logPV)'),('lin','Linear (y~PV)')]:
        rmse,nev=loo_rmse(PV,y,kind)
        med,lo,hi,sd=slope_boot(PV,y,kind)
        # normalidade dos residuos
        if kind=='alo':
            m=y>0.05; b,a=np.polyfit(np.log(PV[m]),np.log(y[m]),1); res=np.log(y[m])-(a+b*np.log(PV[m]))
        elif kind=='log':
            b,a=np.polyfit(np.log(PV),y,1); res=y-(a+b*np.log(PV))
        else:
            b,a=np.polyfit(PV,y,1); res=y-(a+b*PV)
        wsh=stats.shapiro(res).pvalue
        ci_w=hi-lo
        row[kind]=dict(nome=nome,rmse=round(rmse,2),n_eval=nev,slope_ci=[round(lo,2),round(hi,2)],
                       ci_width=round(ci_w,2),slope_cv=round(abs(sd/med),2) if med else None,shapiro_p=round(float(wsh),3))
        print(f"  {nome:24s} RMSE(LOO,orig)={rmse:5.2f} (n={nev})  slope IC95=[{lo:+.2f},{hi:+.2f}] largura={ci_w:.2f}  Shapiro p={wsh:.3f}")
    out[k]=row
    # veredito por RMSE + estabilidade
    best=min(['alo','log','lin'],key=lambda kk:row[kk]['rmse'])
    stab=min(['alo','log','lin'],key=lambda kk:row[kk]['ci_width'])
    print(f"  -> melhor previsão: {row[best]['nome']} | coef mais estável: {row[stab]['nome']}\n")
    out[k]['best_rmse']=best; out[k]['best_stab']=stab
json.dump(out,open('compara_ajustes_pv.json','w'))
print("[salvo compara_ajustes_pv.json]")
