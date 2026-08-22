# -*- coding: utf-8 -*-
# Analise de sensibilidade das variaveis: de quais das 6 dimensoes do BRUMS
# os resultados dependem, medido por 3 lentes independentes.
#  (A) Contribuicao multivariada: PERMANOVA univariada (cada dim sozinha) e
#      leave-one-out (queda de R2 ao remover a dim) — fator = fase (inicial x tardia).
#  (B) Importancia preditiva: importancia por permutacao no modelo logistico
#      (fase tardia D5-7 x inicial D1-3), validacao agrupada por atleta.
#  (C) Responsividade: tamanho de efeito dz (D1->D7, agregado por atleta) e SNR.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.inspection import permutation_importance
from sklearn.base import clone

S=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
LAB={'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Vigor':'Vigor','Fadiga':'Fadiga','Confusao':'Confusão'}
rng=np.random.default_rng(7); NPERM=4999
h=pd.read_csv('humor_anon.csv')

# ---------- fator: fase inicial (D1-3) x tardia (D5-7) ----------
d=h[h.dia.isin([1,2,3,5,6,7])].dropna(subset=S).copy()
d['late']=(d.dia>=5).astype(int)
ids=d['ID'].values; g=d['late'].values.astype(object)

def zmat(df,cols): return ((df[cols]-df[cols].mean())/df[cols].std(ddof=1)).values
def pf_r2(X,gg):
    a=len(np.unique(gg)); N=len(X); tot=((X-X.mean(0))**2).sum(); wg=0.0
    for lev in np.unique(gg):
        Xi=X[gg==lev]; wg+=((Xi-Xi.mean(0))**2).sum()
    return (tot-wg)/(a-1)/(wg/(N-a)), (tot-wg)/tot
def rperm(gg):
    gp=gg.copy()
    for aid in np.unique(ids):
        idx=np.where(ids==aid)[0]; gp[idx]=rng.permutation(gg[idx])
    return gp
def permanova(cols):
    X=zmat(d,cols); F0,R2=pf_r2(X,g); cnt=1
    for _ in range(NPERM):
        if pf_r2(X,rperm(g))[0]>=F0: cnt+=1
    return F0,R2,cnt/(NPERM+1)

F_full,R2_full,p_full=permanova(S)
print(f'PERMANOVA completa (fase): pseudo-F={F_full:.2f} R2={R2_full:.3f} p={p_full:.4f}\n')

rows=[]
for s in S:
    Fu,R2u,pu=permanova([s])                        # univariada
    Fl,R2l,pl=permanova([c for c in S if c!=s])     # leave-one-out
    dR2=R2_full-R2l                                  # contribuicao marginal
    rows.append(dict(dim=s,F_uni=Fu,R2_uni=R2u,p_uni=pu,dR2=dR2))

# ---------- (B) importancia por permutacao no modelo logistico ----------
X=d[S].values; y=d['late'].values
pipe=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000))
gkf=GroupKFold(5)
auc=cross_val_score(pipe,X,y,cv=gkf,groups=ids,scoring='roc_auc').mean()
# importancia por permutacao media entre folds (out-of-fold)
imp=np.zeros(len(S)); cnt=0
for tr,te in gkf.split(X,y,groups=ids):
    m=clone(pipe).fit(X[tr],y[tr])
    r=permutation_importance(m,X[te],y[te],scoring='roc_auc',n_repeats=30,random_state=7)
    imp+=r.importances_mean; cnt+=1
imp/=cnt
# coeficiente padronizado (sinal/direcao)
coef=clone(pipe).fit(X,y).named_steps['logisticregression'].coef_[0]
for i,s in enumerate(S):
    rows[i]['perm_imp']=float(imp[i]); rows[i]['coef']=float(coef[i])

# ---------- (C) responsividade: dz D1->D7 (agregado por atleta) e SNR ----------
def spline_snr(series):
    x=np.arange(len(series)); y=np.asarray(series,float)
    # suavizacao leve por media movel 3 (proxy de spline p/ SNR)
    k=np.array([1,2,3,2,1.]); k/=k.sum()
    sig=np.convolve(np.pad(y,2,mode='edge'),k,mode='valid')
    noise=y-sig
    amp=sig.max()-sig.min(); sd=noise.std(ddof=1) if noise.std(ddof=1)>0 else np.nan
    return amp/sd if sd and sd>0 else np.nan
tr=h.dropna(subset=S)
for i,s in enumerate(S):
    per=[]
    for aid,gg in tr.groupby('ID'):
        a1=gg[gg.dia==1][s]; a7=gg[gg.dia==7][s]
        if len(a1) and len(a7): per.append(a7.mean()-a1.mean())
    per=np.array(per); dz=per.mean()/per.std(ddof=1) if per.std(ddof=1)>0 else np.nan
    daily=tr.groupby('dia')[s].mean().reindex(range(1,8)).values
    rows[i]['dz17']=float(dz); rows[i]['snr']=float(spline_snr(daily))

df=pd.DataFrame(rows).set_index('dim').reindex(S)
print('=== SENSIBILIDADE POR DIMENSAO ===')
print(f"{'dim':11s} {'F_uni':>6s} {'p_uni':>6s} {'dR2_LOO':>8s} {'perm_imp':>9s} {'coef':>6s} {'dz(D1-7)':>8s} {'SNR':>5s}")
for s in S:
    r=df.loc[s]
    print(f"{LAB[s]:11s} {r.F_uni:6.2f} {r.p_uni:6.3f} {r.dR2:8.3f} {r.perm_imp:9.3f} {r.coef:+6.2f} {r.dz17:+8.2f} {r.snr:5.1f}")
print(f"\nAUC modelo (referencia) = {auc:.3f}")

out={'dims':S,'lab':[LAB[s] for s in S],'auc':round(float(auc),3),
     'permanova_full':{'F':round(float(F_full),2),'R2':round(float(R2_full),3),'p':round(float(p_full),4)},
     'F_uni':[round(float(df.loc[s,'F_uni']),2) for s in S],
     'p_uni':[round(float(df.loc[s,'p_uni']),4) for s in S],
     'dR2':[round(float(df.loc[s,'dR2']),3) for s in S],
     'perm_imp':[round(float(df.loc[s,'perm_imp']),3) for s in S],
     'coef':[round(float(df.loc[s,'coef']),2) for s in S],
     'dz17':[round(float(df.loc[s,'dz17']),2) for s in S],
     'snr':[round(float(df.loc[s,'snr']),1) for s in S]}
open('sensibilidade.json','w').write(json.dumps(out))
print('\n[salvo sensibilidade.json]')

# ---------- figura ----------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
COL={'Tensao':'#4d9de0','Depressao':'#c56bd6','Raiva':'#e0525b','Vigor':'#2f9e44','Fadiga':'#e8590c','Confusao':'#f0a848'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
order=sorted(range(len(S)),key=lambda i:out['perm_imp'][i])   # menor->maior (barh de baixo p/ cima)
labs=[out['lab'][i] for i in order]; cols=[COL[S[i]] for i in order]
fig,ax=plt.subplots(1,3,figsize=(14,4.6),dpi=200)
def barh(a,vals,title,xlab,fmt='{:.2f}'):
    v=[vals[i] for i in order]; y=range(len(v))
    a.barh(list(y),v,color=cols,alpha=.9,height=.68)
    a.set_yticks(list(y)); a.set_yticklabels(labs); a.set_title(title,fontweight='bold',fontsize=11.5,loc='left')
    a.set_xlabel(xlab)
    for i,val in zip(y,v): a.text(val+ (max(v)-min(0,min(v)))*0.02, i, fmt.format(val), va='center', fontsize=9.5)
barh(ax[0],out['F_uni'],'Contribuição multivariada','pseudo-F (PERMANOVA univariada)')
ax[0].axvline(1,ls=':',color='#adb5bd',lw=1)
barh(ax[1],out['perm_imp'],'Importância preditiva','queda de AUC ao permutar','{:.3f}')
ax[1].axvline(0,ls=':',color='#adb5bd',lw=1)
absdz=[abs(x) for x in out['dz17']]
barh(ax[2],absdz,'Responsividade','|dz| do D1 ao D7')
fig.suptitle('Análise de sensibilidade das variáveis — de quais dimensões do BRUMS os resultados dependem',
             fontweight='bold',fontsize=12.5,y=1.02)
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/sensibilidade_variaveis.png',bbox_inches='tight',facecolor='white')
print('[figura salva: sensibilidade_variaveis.png]')
