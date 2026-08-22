# -*- coding: utf-8 -*-
# Ajuste ALOMETRICO e LOGARITMICO do humor pelo pico de velocidade (T-CAR PV).
#  - modelo alometrico (lei de potencia): humor = a * PV^b  ->  log(humor) = log a + b*log(PV)
#  - expoente b (escala alometrica), R2 do ajuste log-log e a curva ajustada
#  - humor "escalonado" alometricamente: humor / PV^b (remove o efeito da aptidao)
#  - tambem o ajuste log-linear (humor ~ log PV) como alternativa
# Dados: pares casados PV x humor semanal (n=25), anonimizados.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, json
from scipy import stats
pm=json.load(open('pv_mood_matched.json'))
PV=np.array(pm['Vigor']['PV'])
LAB={'Vigor':'Vigor','Fadiga':'Fadiga','FadFisica':'Fadiga física','TMD':'PTH'}
DIMS=['FadFisica','Fadiga','Vigor','TMD']
lpv=np.log(PV)
rows=[]
print("=== AJUSTE ALOMETRICO (log-log) DO HUMOR PELO PICO DE VELOCIDADE ===")
print(f"{'dim':14s} {'b (expoente)':>12s} {'IC95 b':>16s} {'R2 loglog':>9s} {'r Pearson':>9s} {'p':>7s}")
for k in DIMS:
    y=np.array(pm[k]['mood'])
    m=y>0.05                      # log exige positivos (exclui pisos exatos)
    x=lpv[m]; ly=np.log(y[m]); n=int(m.sum())
    b,a=np.polyfit(x,ly,1)        # ly = a + b*x
    yhat=a+b*x; ss_res=((ly-yhat)**2).sum(); ss_tot=((ly-ly.mean())**2).sum()
    r2=1-ss_res/ss_tot
    r,p=stats.pearsonr(x,ly)
    se_b=np.sqrt(ss_res/(n-2)/((x-x.mean())**2).sum()); tcrit=stats.t.ppf(.975,n-2)
    lo,hi=b-tcrit*se_b,b+tcrit*se_b
    rows.append(dict(dim=k,lab=LAB[k],b=float(b),lo=float(lo),hi=float(hi),a=float(a),r2=float(r2),
                     r=float(r),p=float(p),n=n,
                     x=[float(v) for v in x],ly=[float(v) for v in ly]))
    print(f"{LAB[k]:14s} {b:+12.2f} [{lo:+.2f},{hi:+.2f}] {r2:9.2f} {r:+9.2f} {p:7.3f}")

# curva alometrica no espaco original (humor = exp(a) * PV^b) para fadiga fisica e vigor
grid=np.linspace(PV.min(),PV.max(),60)
curves={}
for k in ['FadFisica','Vigor']:
    rr=[r for r in rows if r['dim']==k][0]
    curves[k]={'pv':[float(v) for v in grid],'fit':[float(np.exp(rr['a'])*g**rr['b']) for g in grid],
               'pvobs':[float(v) for v in PV],'obs':[float(v) for v in np.array(pm[k]['mood'])]}

json.dump({'rows':rows,'curves':curves,'PV':[float(v) for v in PV]},open('alometrico_pv.json','w'))

# ---------- figura ----------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
COL={'FadFisica':'#e8590c','Vigor':'#2f9e44'}
fig,ax=plt.subplots(1,3,figsize=(15,4.6),dpi=200)
# 1: log-log fadiga fisica
for i,k in enumerate(['FadFisica','Vigor']):
    rr=[r for r in rows if r['dim']==k][0]
    ax[i].scatter(rr['x'],rr['ly'],s=34,color=COL[k],alpha=.7,edgecolors='none')
    xx=np.linspace(min(rr['x']),max(rr['x']),40); ax[i].plot(xx,rr['a']+rr['b']*xx,color=COL[k],lw=2.2)
    ax[i].set_xlabel('log(PV)'); ax[i].set_ylabel(f"log({LAB[k]})")
    ax[i].set_title(f"{LAB[k]}: log-log\nb = {rr['b']:+.2f} [{rr['lo']:+.2f}, {rr['hi']:+.2f}] · R²={rr['r2']:.2f}",fontweight='bold',fontsize=10.5,loc='left')
# 3: curva alometrica no espaco original (fadiga fisica)
k='FadFisica'; c=curves[k]
ax[2].scatter(c['pvobs'],c['obs'],s=34,color=COL[k],alpha=.7,edgecolors='none')
ax[2].plot(c['pv'],c['fit'],color=COL[k],lw=2.4,label=f"humor = a·PV^b (b={[r for r in rows if r['dim']==k][0]['b']:+.2f})")
ax[2].set_xlabel('T-CAR pico de velocidade (km/h)'); ax[2].set_ylabel('Fadiga física')
ax[2].set_title('Curva alométrica (potência) no espaço original\nfadiga física decresce com a aptidão',fontweight='bold',fontsize=10.5,loc='left'); ax[2].legend(frameon=False,fontsize=9)
fig.suptitle('Ajuste alométrico e logarítmico do humor pelo pico de velocidade do T-CAR',fontweight='bold',fontsize=12.5,y=1.03)
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/alometrico_pv.png',bbox_inches='tight',facecolor='white')
print('\n[salvo alometrico_pv.json + figura]')
