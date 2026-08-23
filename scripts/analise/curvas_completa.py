# -*- coding: utf-8 -*-
# Analise completa das curvas por variavel do BRUMS ao longo da semana:
#  - curva SEM filtro (media diaria bruta) vs COM filtro (spline suavizada)
#  - derivadas (velocidade/aceleracao) -> ponto de inflexao e velocidade de pico
#  - sinal/ruido (SNR) de cada curva
#  - cruzamentos das curvas (pontos de ligacao) com os dias
#  - comportamento de cada variavel com p-valores (Friedman medidas repetidas; D1->D7 Wilcoxon+dz)
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
from scipy.interpolate import UnivariateSpline
h=pd.read_csv('humor_anon.csv')
DIMS=[('Vigor','#2f9e44'),('Fadiga','#e8590c'),('Tensao','#4d9de0'),('Depressao','#c56bd6'),
      ('Raiva','#e0525b'),('Confusao','#f0a848')]
LAB={'Vigor':'Vigor','Fadiga':'Fadiga','Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
x=np.arange(1,8); xf=np.linspace(1,7,300)
ad=h.groupby(['ID','dia'])[[d for d,_ in DIMS]].mean().reset_index()

def smooth(y,s=1.0):
    sp=UnivariateSpline(x,y,k=3,s=s*np.var(y)*len(y)*0.15+1e-6); return sp
def snr(y,yhat):
    noise=y-yhat; amp=yhat.max()-yhat.min(); sd=noise.std(ddof=1)
    return amp/sd if sd>0 else np.nan
res={}
print(f"{'dim':10s} {'D1':>5s} {'D7':>5s} {'dz':>5s} {'Fried χ²':>8s} {'W':>4s} {'p':>6s} {'SNR':>5s} {'infl':>5s} {'vpk':>5s}")
smoothed={}
for v,c in DIMS:
    y=ad.groupby('dia')[v].mean().reindex(x).values
    sp=smooth(y); yhat=sp(x); smoothed[v]=sp(xf)
    d1=sp(xf)[0]; d2v=sp.derivative(2); d1v=sp.derivative(1)
    dd=d2v(xf); sign=np.sign(dd); zc=xf[np.where(np.diff(sign)!=0)[0]]
    infl=float(zc[0]) if len(zc) else np.nan
    vv=d1v(xf); vpk=float(xf[np.argmax(np.abs(vv))])
    sn=snr(y,yhat)
    # Friedman (balanceado) + Wilcoxon D1->D7
    wide=ad.pivot_table(index='ID',columns='dia',values=v)
    bal=wide.dropna()
    fr=stats.friedmanchisquare(*[bal[d] for d in range(1,8)]); W=fr.statistic/(len(bal)*6)
    j=pd.concat([wide[1],wide[7]],axis=1).dropna(); dz=(j[7]-j[1]).mean()/(j[7]-j[1]).std(ddof=1)
    wpair=stats.wilcoxon(j[1],j[7]).pvalue
    res[v]=dict(lab=LAB[v],d1=float(y[0]),d7=float(y[6]),dz=float(dz),wp=float(wpair),
                chi=float(fr.statistic),W=float(W),fp=float(fr.pvalue),snr=float(sn),
                infl=infl,vpk=vpk,raw=[float(a) for a in y])
    print(f"{LAB[v]:10s} {y[0]:5.1f} {y[6]:5.1f} {dz:+5.2f} {fr.statistic:8.1f} {W:4.2f} {fr.pvalue:6.3f} {sn:5.1f} {infl:5.2f} {vpk:5.2f}")

# cruzamentos vigor x fadiga (curvas suavizadas)
def crossings(a,b):
    da=smoothed[a]-smoothed[b]; s=np.sign(da); out=[]
    for i in np.where(np.diff(s)!=0)[0]:
        out.append(round(float(xf[i]),1))
    keep=[];
    for o in out:
        if not keep or o-keep[-1]>0.4: keep.append(o)
    return keep
cvf=crossings('Vigor','Fadiga')
print("\ncruzamentos Vigor×Fadiga (curvas filtradas):",cvf)
res['_cross']={'VigorFadiga':cvf}
res['_xf']=[float(a) for a in xf]; res['_smoothed']={v:[float(a) for a in smoothed[v]] for v,_ in DIMS}
json.dump(res,open('curvas_completa.json','w'))
print('[salvo curvas_completa.json]')
