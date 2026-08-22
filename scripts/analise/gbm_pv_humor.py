# -*- coding: utf-8 -*-
# Gradient boosting como alternativa flexivel ao ajuste do humor pelo pico de velocidade.
# Preve fadiga fisica e vigor a partir do PV (unico preditor) e compara, por LOO-CV na
# escala original, com linear / logaritmico / alometrico. Com n=25 e sinal fraco,
# o esperado e que o GBM NAO supere o linear (sobreajuste).
import warnings; warnings.filterwarnings('ignore')
import numpy as np, json
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
pm=json.load(open('pv_mood_matched.json'))
PV=np.array(pm['Vigor']['PV']).reshape(-1,1)
LAB={'FadFisica':'Fadiga física','Vigor':'Vigor'}

def loo_rmse_param(x,y,kind):
    x=x.ravel(); err=[]
    for i in range(len(x)):
        tr=np.arange(len(x))!=i; xtr,ytr=x[tr],y[tr]
        if kind=='alo':
            m=ytr>0.05;
            if y[i]<=0.05: continue
            b,a=np.polyfit(np.log(xtr[m]),np.log(ytr[m]),1); pred=np.exp(a+b*np.log(x[i]))
        elif kind=='log':
            b,a=np.polyfit(np.log(xtr),ytr,1); pred=a+b*np.log(x[i])
        else:
            b,a=np.polyfit(xtr,ytr,1); pred=a+b*x[i]
        err.append((pred-y[i])**2)
    return float(np.sqrt(np.mean(err)))

def loo_rmse_model(x,y,make):
    err=[]
    for i in range(len(x)):
        tr=np.arange(len(x))!=i
        m=make(); m.fit(x[tr],y[tr]); pred=float(m.predict(x[i:i+1])[0])
        err.append((pred-y[i])**2)
    return float(np.sqrt(np.mean(err)))

def mk_xgb(): return XGBRegressor(n_estimators=200,max_depth=2,learning_rate=0.05,subsample=0.8,
                                  reg_lambda=2.0,random_state=7,verbosity=0)
def mk_lgb(): return LGBMRegressor(n_estimators=200,max_depth=2,num_leaves=4,learning_rate=0.05,
                                   subsample=0.8,reg_lambda=2.0,min_child_samples=8,random_state=7,verbose=-1)

print("=== PREVER HUMOR A PARTIR DO PICO DE VELOCIDADE: GBM vs ajustes paramétricos ===")
print("   (LOO-CV RMSE na escala original — menor é melhor)\n")
out={}
for k in ['FadFisica','Vigor']:
    y=np.array(pm[k]['mood'])
    # baseline: prever a media (sem preditor)
    base=float(np.sqrt(np.mean((y-y.mean())**2)))
    res={
      'baseline(média)':round(base,2),
      'Linear':round(loo_rmse_param(PV,y,'lin'),2),
      'Logarítmico':round(loo_rmse_param(PV,y,'log'),2),
      'Alométrico':round(loo_rmse_param(PV,y,'alo'),2),
      'XGBoost':round(loo_rmse_model(PV,y,mk_xgb),2),
      'LightGBM':round(loo_rmse_model(PV,y,mk_lgb),2),
    }
    out[k]=res
    print(f"### {LAB[k]}")
    for nome,v in res.items(): print(f"   {nome:18s} RMSE = {v}")
    best=min([x for x in res if x!='baseline(média)'],key=lambda kk:res[kk])
    print(f"   -> melhor: {best} (RMSE {res[best]})\n")
    out[k]['best']=best
json.dump(out,open('gbm_pv_humor.json','w'))

# figura
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(12.5,4.6),dpi=200)
for j,k in enumerate(['FadFisica','Vigor']):
    res=out[k]; names=['Linear','Logarítmico','Alométrico','XGBoost','LightGBM']
    vals=[res[n] for n in names]; base=res['baseline(média)']
    cols=['#1971c2','#4dabf7','#adb5bd','#e8590c','#2f9e44']
    ax[j].bar(names,vals,color=cols,alpha=.9)
    ax[j].axhline(base,ls='--',color='#e0525b',lw=1.4,label=f'baseline (média) = {base}')
    for i,v in enumerate(vals): ax[j].text(i,v+0.02,f'{v}',ha='center',fontsize=9.5,fontweight='bold')
    ax[j].set_ylabel('RMSE (LOO, escala original)'); ax[j].set_title(f'{LAB[k]}: prever a partir do PV',fontweight='bold',fontsize=11,loc='left')
    ax[j].set_ylim(0,max(vals+[base])*1.15); ax[j].legend(frameon=False,fontsize=9)
    ax[j].tick_params(axis='x',labelrotation=20)
fig.suptitle('Gradient boosting vs ajustes paramétricos para prever o humor pelo pico de velocidade',fontweight='bold',fontsize=12.5,y=1.03)
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/gbm_pv_humor.png',bbox_inches='tight',facecolor='white')
print('[salvo gbm_pv_humor.json + figura]')
