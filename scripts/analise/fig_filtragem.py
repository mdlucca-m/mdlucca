import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.interpolate import UnivariateSpline
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); A=json.load(open('adv.json')); snr=A['snr']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11.5,'axes.edgecolor':'#333','axes.linewidth':1.0,
    'axes.grid':True,'grid.color':'#e3e3e3','grid.linewidth':0.8})
seq=[(1,'baseline')]+sum([[(d,'pre'),(d,'pos')] for d in range(2,8)],[])
x=np.array([d+(-0.2 if m=='pre' else 0.2 if m=='pos' else 0.0) for d,m in seq])
xx=np.linspace(x.min(),x.max(),400)
def sigres(k):
    y=np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m in seq])
    s=UnivariateSpline(x,y,k=4,s=len(x)*np.var(y)*0.85); sig=s(x); res=y-sig; return y,s(xx),sig,res

VARS=[('Vigor','Vigor','#0f8b8d'),('Fadiga','Fadiga','#e8590c'),('TMD','PTH','#7048e8')]
fig=plt.figure(figsize=(14,9.5)); gs=GridSpec(2,3,figure=fig,height_ratios=[1.35,1.0],hspace=0.42,wspace=0.28)
for i,(k,lab,col) in enumerate(VARS):
    y,ys,sig,res=sigres(k); nsd=res.std(ddof=1)
    a=fig.add_subplot(gs[0,i])
    a.fill_between(xx,ys-nsd,ys+nsd,color=col,alpha=0.15,label='faixa de ruído (± DP)')
    a.plot(x,y,'o',color='#868e96',ms=6,alpha=0.8,label='sinal observado (médias)')
    a.plot(xx,ys,color=col,lw=3,label='sinal filtrado (spline)')
    for d in [2,4,7]: a.axvline(d,color='#ccc',ls='--',lw=0.9)
    a.set_title('%s'%lab,fontweight='bold',fontsize=12.5,color=col)
    a.set_xlabel('Dia');
    if i==0: a.set_ylabel('Escore')
    a.legend(fontsize=8.2,loc='upper right',framealpha=0.9)
    a.text(0.03,0.04,'SNR = %.1f'%snr[k]['snr_amp'],transform=a.transAxes,fontsize=10,fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.3',fc='white',ec=col))
# painel de resíduos (ruído) para Vigor e Fadiga
b=fig.add_subplot(gs[1,0:2])
for k,lab,col in VARS[:2]:
    y,ys,sig,res=sigres(k); b.plot(x,res,'o-',color=col,ms=5,lw=1.4,label='%s'%lab)
b.axhline(0,color='#333',lw=1); b.set_title('Ruído residual (observado - sinal filtrado)',fontweight='bold',fontsize=11.5)
b.set_xlabel('Dia'); b.set_ylabel('Resíduo (pts)'); b.legend(fontsize=9)
# SNR por variavel
c=fig.add_subplot(gs[1,2])
DIMS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Tensao','Tensão'),('Depressao','Depr.'),('Raiva','Raiva'),
      ('Confusao','Conf.'),('TMD','PTH')]
ks=[k for k,_ in DIMS if k in snr]; labs=[l for k,l in DIMS if k in snr]
vals=[snr[k]['snr_amp'] for k in ks]; cols=['#0f8b8d' if v>=5 else '#f08c00' if v>=3 else '#e03131' for v in vals]
c.barh(range(len(ks)),vals,color=cols,edgecolor='white'); c.set_yticks(range(len(ks))); c.set_yticklabels(labs,fontsize=9)
c.invert_yaxis(); c.axvline(3,color='#adb5bd',ls='--',lw=1); c.set_title('Relação sinal/ruído por variável',fontweight='bold',fontsize=11.5)
c.set_xlabel('SNR (amplitude do sinal / DP do ruído)')
fig.suptitle('Processo de filtragem das curvas: separação entre sinal e ruído',fontsize=15,fontweight='bold',y=0.98)
fig.savefig(f'{OUT}/filtragem_sinal_ruido.png',dpi=150,bbox_inches='tight',facecolor='white')
print('OK filtragem_sinal_ruido.png')
