# -*- coding: utf-8 -*-
# Analise descritiva ROBUSTA das variaveis do humor (resistente a outliers e ao piso):
#  mediana, IQR (Q1-Q3), MAD, media aparada 20%, min-max, % piso (zeros),
#  assimetria robusta (Bowley/quartis), IC95% bootstrap da mediana.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
rng=np.random.default_rng(7)
h=pd.read_csv('humor_anon.csv')
VARS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Tensao','Tensão'),('Depressao','Depressão'),
      ('Raiva','Raiva'),('Confusao','Confusão'),('TMD','PTH (TMD)'),('FadFisica','Fadiga física'),
      ('FadMental','Fadiga mental')]
def boot_med_ci(x,B=5000):
    x=np.asarray(x); bs=[np.median(rng.choice(x,len(x),replace=True)) for _ in range(B)]
    return np.percentile(bs,2.5),np.percentile(bs,97.5)
rows=[]
print(f"{'var':14s} {'n':>4s} {'Md':>5s} {'IQR(Q1–Q3)':>12s} {'MAD':>5s} {'apar20%':>7s} {'min–max':>8s} {'%piso':>6s} {'assMR':>6s}")
for v,lab in VARS:
    x=h[v].dropna().values; n=len(x)
    md=np.median(x); q1,q3=np.percentile(x,[25,75]); iqr=q3-q1
    mad=stats.median_abs_deviation(x); tri=stats.trim_mean(x,0.2)
    floor=100*np.mean(x<=0.0001); mn,mx=x.min(),x.max()
    bow=((q3-md)-(md-q1))/iqr if iqr>0 else 0.0   # assimetria de Bowley (robusta)
    lo,hi=boot_med_ci(x)
    rows.append(dict(var=v,lab=lab,n=int(n),md=float(md),q1=float(q1),q3=float(q3),iqr=float(iqr),
                     mad=float(mad),trim=float(tri),floor=float(floor),mn=float(mn),mx=float(mx),
                     bowley=float(bow),ci=[float(lo),float(hi)]))
    print(f"{lab:14s} {n:>4d} {md:5.1f} {q1:5.1f}–{q3:<5.1f} {mad:5.2f} {tri:7.2f} {mn:4.0f}–{mx:<4.0f} {floor:5.0f}% {bow:+6.2f}")
json.dump(rows,open('descritiva_robusta.json','w'))

# ---------- figura: boxplots robustos por dimensao ----------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
COL={'Vigor':'#2f9e44','Fadiga':'#e8590c','Tensao':'#4d9de0','Depressao':'#c56bd6','Raiva':'#e0525b',
     'Confusao':'#f0a848','TMD':'#7048e8','FadFisica':'#d9480f','FadMental':'#e8590c'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
order=['Vigor','Fadiga','FadFisica','TMD','FadMental','Tensao','Raiva','Depressao','Confusao']
labs=[dict(VARS)[v] for v in order]
data=[h[v].dropna().values for v in order]
fig,ax=plt.subplots(figsize=(12.5,5.4),dpi=200)
bp=ax.boxplot(data,vert=True,patch_artist=True,widths=.6,showfliers=True,
              medianprops=dict(color='black',lw=2),flierprops=dict(marker='o',ms=3,alpha=.25,mfc='#868e96',mec='none'))
for patch,v in zip(bp['boxes'],order): patch.set_facecolor(COL[v]); patch.set_alpha(.55)
# sobrepor a mediana com IC bootstrap e a media aparada
for i,v in enumerate(order):
    r=[x for x in rows if x['var']==v][0]
    ax.plot([i+1,i+1],r['ci'],color='black',lw=1.2,zorder=5)
    ax.plot(i+1,r['trim'],'D',color='white',mec='black',ms=6,zorder=6)
ax.set_xticks(range(1,len(order)+1)); ax.set_xticklabels(labs,rotation=20,ha='right')
ax.set_ylabel('Escore (BRUMS 0–16; TMD/fadigas em suas escalas)')
ax.set_title('Descritiva robusta das dimensões do humor — mediana (linha), IQR (caixa), IC95% da mediana (barra), média aparada 20% (◇)',
             fontweight='bold',fontsize=11.5,loc='left')
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/descritiva_robusta.png',bbox_inches='tight',facecolor='white')
print('\n[salvo descritiva_robusta.json + figura]')
