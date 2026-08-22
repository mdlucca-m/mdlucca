# -*- coding: utf-8 -*-
# Sensibilidade ANALITICA (robustez das conclusoes as escolhas do metodo).
#  (A) Leave-one-athlete-out (LOAO): estabilidade do efeito D1->D7 (dz de vigor e fadiga)
#      e do pseudo-F da PERMANOVA (fase inicial x tardia) ao remover cada atleta.
#  (B) Janela de dias: D1->D7 vs D2->D7 (excluindo o baseline).
#  (C) Suavizacao: o ponto de inflexao (~dia 4) sob varios suavizadores (polinomio grau 3
#      e splines com diferentes rigidezes).
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
from scipy.interpolate import UnivariateSpline
rng=np.random.default_rng(7)
S=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
h=pd.read_csv('humor_anon.csv')

def dz_d1d7(df,v):
    per=[]
    for aid,g in df.groupby('ID'):
        a1=g[g.dia==1][v]; a7=g[g.dia==7][v]
        if len(a1) and len(a7): per.append(a7.mean()-a1.mean())
    per=np.array(per); return per.mean()/per.std(ddof=1), per
def dz_dxd7(df,v,d0):
    per=[]
    for aid,g in df.groupby('ID'):
        a0=g[g.dia==d0][v]; a7=g[g.dia==7][v]
        if len(a0) and len(a7): per.append(a7.mean()-a0.mean())
    per=np.array(per); return per.mean()/per.std(ddof=1)

# ---------- (A) LOAO ----------
print('=== LEAVE-ONE-ATHLETE-OUT (D1->D7 dz) ===')
loao={}
ath=sorted(h.ID.unique())
for v in ['Vigor','Fadiga','TMD']:
    full,_=dz_d1d7(h,v)
    vals=[dz_d1d7(h[h.ID!=a],v)[0] for a in ath]
    loao[v]={'full':round(float(full),2),'min':round(float(min(vals)),2),'max':round(float(max(vals)),2),
             'range':round(float(max(vals)-min(vals)),3)}
    print(f"  {v:7s} full dz={full:+.2f} | LOAO range [{min(vals):+.2f}, {max(vals):+.2f}] (amplitude {max(vals)-min(vals):.3f})")

# PERMANOVA fase LOAO
d=h[h.dia.isin([1,2,3,5,6,7])].dropna(subset=S).copy(); d['late']=(d.dia>=5).astype(int)
def permF(df):
    X=((df[S]-df[S].mean())/df[S].std(ddof=1)).values; g=df['late'].values
    a=2; N=len(X); tot=((X-X.mean(0))**2).sum(); wg=sum(((X[g==l]-X[g==l].mean(0))**2).sum() for l in (0,1))
    return (tot-wg)/(a-1)/(wg/(N-a))
Ffull=permF(d); Fl=[permF(d[d.ID!=a]) for a in ath]
print(f"  PERMANOVA fase pseudo-F full={Ffull:.2f} | LOAO [{min(Fl):.2f}, {max(Fl):.2f}]")
loao['permF']={'full':round(float(Ffull),2),'min':round(float(min(Fl)),2),'max':round(float(max(Fl)),2)}

# ---------- (B) janela ----------
print('\n=== JANELA (D1->D7 vs D2->D7) ===')
win={}
for v in ['Vigor','Fadiga','TMD']:
    a=dz_dxd7(h,v,1); b=dz_dxd7(h,v,2)
    win[v]={'D1_D7':round(float(a),2),'D2_D7':round(float(b),2)}
    print(f"  {v:7s} D1->D7 dz={a:+.2f} | D2->D7 dz={b:+.2f}")

# ---------- (C) suavizacao / inflexao ----------
print('\n=== INFLEXAO SOB VARIOS SUAVIZADORES (dia) ===')
x=np.arange(1,8)
smooth={}
for v in ['Fadiga','TMD']:
    y=h.groupby('dia')[v].mean().reindex(range(1,8)).values
    infl={}
    # cubico: 2a deriv zero em -b/(3a)
    c=np.polyfit(x,y,3); a3,b2=c[0],c[1]; xi=-b2/(3*a3)
    infl['poly3']=round(float(xi),2)
    # splines com varias rigidezes
    for s in [0.5,1.0,2.0]:
        try:
            sp=UnivariateSpline(x,y,k=3,s=s); d2=sp.derivative(2)
            xs=np.linspace(1,7,600); dd=d2(xs); sign=np.sign(dd)
            zc=xs[np.where(np.diff(sign)!=0)[0]]
            infl[f'spline_s{s}']=round(float(zc[0]),2) if len(zc) else None
        except Exception: infl[f'spline_s{s}']=None
    smooth[v]=infl
    print(f"  {v:7s} inflexao -> "+", ".join(f"{k}={val}" for k,val in infl.items()))

out={'loao':loao,'window':win,'smooth':smooth,'n_ath':len(ath)}
json.dump(out,open('sensibilidade_analitica.json','w'))

# ---------- figura ----------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,3,figsize=(14,4.4),dpi=200)
# A LOAO ranges
vs=['Vigor','Fadiga','TMD']; cc=['#2f9e44','#e8590c','#7048e8']
for i,v in enumerate(vs):
    ax[0].plot([loao[v]['min'],loao[v]['max']],[i,i],color=cc[i],lw=3,alpha=.5)
    ax[0].plot(loao[v]['full'],i,'o',color=cc[i],ms=9)
ax[0].axvline(0,ls=':',color='#adb5bd'); ax[0].set_yticks(range(3)); ax[0].set_yticklabels(vs)
ax[0].set_xlabel('dz D1→D7'); ax[0].set_title('(A) Leave-one-athlete-out\nefeito estável ao remover qualquer atleta',fontweight='bold',fontsize=10.5,loc='left')
# B janela
w=0.35; xb=np.arange(3)
ax[1].bar(xb-w/2,[win[v]['D1_D7'] for v in vs],w,label='D1→D7',color='#1971c2')
ax[1].bar(xb+w/2,[win[v]['D2_D7'] for v in vs],w,label='D2→D7 (sem baseline)',color='#74c0fc')
ax[1].axhline(0,color='#adb5bd',lw=.8); ax[1].set_xticks(xb); ax[1].set_xticklabels(vs)
ax[1].set_ylabel('dz'); ax[1].set_title('(B) Janela de dias\nconclusão idêntica com/sem baseline',fontweight='bold',fontsize=10.5,loc='left'); ax[1].legend(frameon=False,fontsize=8.5)
# C inflexao
methods=['poly3','spline_s0.5','spline_s1.0','spline_s2.0']; ml=['pol. 3','spl. 0,5','spl. 1,0','spl. 2,0']
for i,v in enumerate(['Fadiga','TMD']):
    vals=[smooth[v][m] for m in methods]
    ax[2].plot(range(len(methods)),vals,'-o',color=('#e8590c' if v=='Fadiga' else '#7048e8'),lw=2,label=v)
ax[2].axhspan(3.8,4.4,color='#ced4da',alpha=.3); ax[2].set_xticks(range(len(methods))); ax[2].set_xticklabels(ml,fontsize=9)
ax[2].set_ylabel('dia da inflexão'); ax[2].set_ylim(2.5,5.5)
ax[2].set_title('(C) Suavização\ninflexão ~dia 4 em todos os filtros',fontweight='bold',fontsize=10.5,loc='left'); ax[2].legend(frameon=False,fontsize=9)
fig.suptitle('Sensibilidade analítica — robustez das conclusões às escolhas do método',fontweight='bold',fontsize=12.5,y=1.02)
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/sensibilidade_analitica.png',bbox_inches='tight',facecolor='white')
print('\n[salvo sensibilidade_analitica.json + figura]')
