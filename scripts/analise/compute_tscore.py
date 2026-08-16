import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
h=pd.read_csv('hum_prof.csv')
SUB=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]
KEYS=[k for k,_ in SUB]
# T-score = 50 + 10*z, z relative to whole-sample obs mean/SD (Terry/Parsons-Smith within-sample standardization)
mu={k:h[k].mean() for k in KEYS}; sd={k:h[k].std(ddof=1) for k in KEYS}
def T(k,x): return 50+10*(x-mu[k])/sd[k]
R={'mu':mu,'sd':sd,'profile':{}}
# group-mean T per recorte
def recorte(mask,name):
    sub=h[mask]; R['profile'][name]={k:float(T(k,sub[k].mean())) for k in KEYS}
recorte(h.dia==1,'D1'); recorte(h.dia==7,'D7')
recorte(h.momento=='pre','Pre'); recorte(h.momento=='pos','Pos')
recorte(h.index==h.index,'Geral')
for d in range(1,8): recorte(h.dia==d,'dia%d'%d)
json.dump(R,open('tscore.json','w'),indent=1,ensure_ascii=False)
print('T-score profile by recorte (M=50,SD=10):')
for name in ['D1','D7','Geral']:
    print(' ',name,{k:round(v,1) for k,v in R['profile'][name].items()})
