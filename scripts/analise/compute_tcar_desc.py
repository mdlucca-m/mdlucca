# Descritiva completa do T-CAR (covariável fisiológica) -> tcar_desc.json
import pandas as pd, numpy as np, json
t=pd.read_csv('tcar2_features.csv')
rows=[('PVini','T-CAR1 – pico de velocidade (km/h)'),('PV','T-CAR2 – pico de velocidade (km/h)'),
 ('dPV','ΔPV – ganho na pré-temporada (km/h)'),('dist','Distância percorrida (m)'),
 ('reps_ini','Repetições completadas (n)'),('FCmax','FC máxima (bpm)'),('FCpico','FC de pico no teste (bpm)'),
 ('HRmean','FC média no teste (bpm)'),('HRR','Recuperação da FC em 1 min (bpm)'),
 ('TRIMP','Impulso de treino – TRIMP (u.a.)'),('PSE','Percepção subjetiva de esforço (0–10)')]
out=[]
for k,lab in rows:
    x=t[k].dropna()
    out.append(dict(k=k,lab=lab,n=int(x.shape[0]),m=float(x.mean()),sd=float(x.std(ddof=1)),
        mn=float(x.min()),mx=float(x.max()),cv=float(100*x.std(ddof=1)/x.mean()) if x.mean() else float('nan')))
json.dump(out,open('tcar_desc.json','w'),indent=1,ensure_ascii=False)
print('T-CAR descritiva: %d parâmetros'%len(out))
