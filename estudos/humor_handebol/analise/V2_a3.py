# -*- coding: utf-8 -*-
"""Pipeline V2 — parte 3: perfis no tempo, estímulo, pré/pós, associação, modelo misto."""
import json, numpy as np, collections, warnings, itertools
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
warnings.filterwarnings('ignore')
import os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); SAIDA=os.path.join(RAIZ,"saida")
os.makedirs(DADOS, exist_ok=True); os.makedirs(SAIDA, exist_ok=True)
S=DADOS
B=json.load(open(f"{S}/V2_base.json")); Q=json.load(open(f"{S}/V2_perfis.json"))
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V=SUB+['TMD']
NOMES=Q['NOMES']; CARGA=B['CARGA']; EST={int(k):v['tipo'] for k,v in CARGA.items()}
lab=np.array(Q['lab_AD']); dia=np.array(Q['dia_AD']); ath=np.array(Q['a_AD'])
nd=np.array([int((dia==d).sum()) for d in range(1,8)],float)
def suav(y):
    y=np.asarray(y,float); z=y.copy()
    for i in range(1,len(y)-1): z[i]=.25*y[i-1]+.5*y[i]+.25*y[i+1]
    return z
def holm(ps):
    ps=np.asarray(ps,float); o=np.argsort(ps); m=len(ps); adj=np.empty(m); c=0.
    for i,k in enumerate(o): c=max(c,(m-i)*ps[k]); adj[k]=min(c,1.)
    return adj
# ---------- 1. séries de prevalência ----------
FAV=np.array([100*np.mean(lab[dia==d]==0) for d in range(1,8)])
NEU=np.array([100*np.mean(np.isin(lab[dia==d],[1,2])) for d in range(1,8)])
RIS=np.array([100*np.mean(np.isin(lab[dia==d],[3,4,5])) for d in range(1,8)])
SERP={}
series={nm:np.array([100*np.mean(lab[dia==d]==k) for d in range(1,8)]) for k,nm in enumerate(NOMES)}
series.update({'Favorável':FAV,'Neutra':NEU,'De risco':RIS})
print(f"{'perfil ou faixa':24}{'D1':>7}{'D7':>7}{'Δ':>8}{'piso':>7}  veredito")
for nm,y in series.items():
    p_=y/100.; se=100*np.sqrt(np.clip(p_*(1-p_),0,None)/nd); piso=float(se.mean())
    sm=suav(y); d1=np.diff(sm); ch=[i+1 for i,x in enumerate(d1) if abs(x)>piso]
    frag=bool(y.max()<10)
    SERP[nm]=dict(y=y.tolist(), se=se.tolist(), sm=sm.tolist(), d1=d1.tolist(), piso=piso,
                  choque=ch, dtot=float(y[6]-y[0]), sinal=bool(abs(y[6]-y[0])>piso), fragil=frag)
    print(f"{nm:24}{y[0]:6.1f}%{y[6]:6.1f}%{y[6]-y[0]:+8.1f}{piso:7.1f}  "
          f"{'não avaliável' if frag else ('SINAL' if SERP[nm]['sinal'] else 'ruído')}")
# Q de Cochran por perfil (casos completos)
comp=[a for a in set(ath) if len({d for x,d in zip(ath,dia) if x==a})==7]
CQ={}
for k,nm in enumerate(NOMES)  :
    Yb=np.array([[1 if lab[(ath==a)&(dia==d)][0]==k else 0 for d in range(1,8)] for a in comp])
    L=Yb.sum(1); Cc=Yb.sum(0); kk=7
    den=(kk*L-(L**2)).sum()
    Qv=float((kk-1)*(kk*(Cc**2).sum()-Cc.sum()**2)/den) if den else np.nan
    CQ[nm]=dict(Q=Qv, p=float(stats.chi2.sf(Qv,kk-1)) if den else np.nan, n=len(comp))
Yb=np.array([[1 if lab[(ath==a)&(dia==d)][0] in (3,4,5) else 0 for d in range(1,8)] for a in comp])
L=Yb.sum(1); Cc=Yb.sum(0); den=(7*L-(L**2)).sum()
CQ['Faixa de risco']=dict(Q=float(6*(7*(Cc**2).sum()-Cc.sum()**2)/den), n=len(comp))
CQ['Faixa de risco']['p']=float(stats.chi2.sf(CQ['Faixa de risco']['Q'],6))
# ---------- 2. estímulo ----------
TIPOS=['HIIT','Amistoso','Técnico/força']
tipo=np.array([EST[d] for d in dia])
PREV_EST={nm:{t:float(100*np.mean(lab[tipo==t]==k)) for t in ['Basal']+TIPOS} for k,nm in enumerate(NOMES)}
FAIXA_EST={}
for nome,idx in [('Favorável',[0]),('Neutra',[1,2]),('Risco',[3,4,5])]:
    FAIXA_EST[nome]={t:float(100*np.mean(np.isin(lab[tipo==t],idx))) for t in ['Basal']+TIPOS}
NPOR={t:int((tipo==t).sum()) for t in ['Basal']+TIPOS}
tab=np.array([[int(np.sum((tipo==t)&(lab==k))) for t in TIPOS] for k in range(6)])
chi,pchi,gl,_=stats.chi2_contingency(tab[tab.sum(1)>0])
tabf=np.array([[int(np.sum((tipo==t)&np.isin(lab,idx))) for t in TIPOS] for _,idx in
               [('F',[0]),('N',[1,2]),('R',[3,4,5])]])
chif,pf,glf,_=stats.chi2_contingency(tabf)
print(f"\nperfil × estímulo: χ²={chi:.2f} gl={gl} p={pchi:.4f} | faixa × estímulo: χ²={chif:.2f} gl={glf} p={pf:.4f}")
# níveis por tipo: Friedman (np) e ANOVA de medidas repetidas (par)
PARd=pd.DataFrame(B['pares']); PARd['tipo']=PARd['dia'].map(EST)
NIV={}
for v in V:
    W=PARd.pivot_table(index='a',columns='tipo',values=v,aggfunc='mean')[TIPOS].dropna()
    Yc=W.values.astype(float); n=len(Yc)
    chi2_,p2=stats.friedmanchisquare(*[Yc[:,j] for j in range(3)])
    gm=Yc.mean(); sm_=Yc.mean(1); cm=Yc.mean(0)
    SSc=n*((cm-gm)**2).sum(); SSe=((Yc-sm_[:,None]-cm[None,:]+gm)**2).sum()
    F=(SSc/2)/(SSe/(2*(n-1))); pF=float(stats.f.sf(F,2,2*(n-1)))
    NIV[v]=dict(n=int(n), **{t:float(m) for t,m in zip(TIPOS,cm)},
                chi=float(chi2_), p=float(p2), W=float(chi2_/(n*2)),
                F=float(F), pF=pF, eta2p=float(SSc/(SSc+SSe)))
# ---------- 3. pré/pós por estímulo ----------
PP=B['prepos']
AG={}
for v in V:
    AG[v]={}
    for t in TIPOS:
        g=[(p['pre_'+v],p['pos_'+v]) for p in PP if EST[p['dia']]==t and p.get('pre_'+v) is not None]
        x=np.array([a for a,b in g]); y=np.array([b for a,b in g]); d=y-x
        if (d!=0).sum()==0: AG[v][t]=dict(d=0.,p=1.,r=0.,n=len(d),t=0.,pt=1.,dz=0.); continue
        _,p=stats.wilcoxon(x,y); z=stats.norm.isf(p/2)
        tt,pt=stats.ttest_rel(y,x)
        AG[v][t]=dict(d=float(d.mean()), p=float(p), r=float(z/np.sqrt(len(d))), n=int(len(d)),
                      t=float(tt), pt=float(pt), dz=float(d.mean()/d.std(ddof=1)))
# McNemar por estímulo
def perfil_de(vec):
    C=np.array(Q['C']); return int(((C-vec)**2).sum(1).argmin())
NORMA=B['NORMA']
def Tv(k,x): m,s=NORMA[k]; return (x-m)/s*10+50
MCN={}
for t in ['TODOS']+TIPOS:
    ent=sai=n11=n00=0
    for p in PP:
        if t!='TODOS' and EST[p['dia']]!=t: continue
        a=perfil_de(np.array([Tv(s,p['pre_'+s]) for s in SUB]))
        b=perfil_de(np.array([Tv(s,p['pos_'+s]) for s in SUB]))
        ra,rb=a in (3,4,5), b in (3,4,5)
        if not ra and rb: ent+=1
        elif ra and not rb: sai+=1
        elif ra and rb: n11+=1
        else: n00+=1
    ch=(abs(ent-sai)-1)**2/(ent+sai) if ent+sai else np.nan
    MCN[t]=dict(entra=ent, sai=sai, n11=n11, n00=n00, n=ent+sai+n11+n00,
                chi=float(ch), p=float(stats.chi2.sf(ch,1)) if ent+sai else np.nan)
for t,a in zip(TIPOS,holm([MCN[t]['p'] for t in TIPOS])): MCN[t]['ph']=float(a)
print("McNemar:", {t:(MCN[t]['entra'],MCN[t]['sai'],round(MCN[t]['p'],4)) for t in ['TODOS']+TIPOS})
# ---------- 4. associação: Spearman e Pearson ----------
Xv={v:np.array([p[v] for p in B['pares']],float) for v in V}
MAT={}
for a,b in itertools.combinations(V,2):
    rs,ps=stats.spearmanr(Xv[a],Xv[b]); rp,pp=stats.pearsonr(Xv[a],Xv[b])
    MAT[f"{a}×{b}"]=dict(rho=float(rs), p=float(ps), r=float(rp), pr=float(pp))
for k,a1,a2 in zip(MAT, holm([m['p'] for m in MAT.values()]), holm([m['pr'] for m in MAT.values()])):
    MAT[k]['ph']=float(a1); MAT[k]['phr']=float(a2)
# ---------- 5. modelo misto ----------
d=PARd.copy(); d['diaN']=d['dia'].astype(float)
LMM={}
for v in V:
    dd=d.rename(columns={v:'y'}).copy()
    try:
        m1=smf.mixedlm("y ~ diaN", dd, groups=dd['a']).fit(reml=True)
        m2=smf.mixedlm("y ~ C(tipo)", dd, groups=dd['a']).fit(reml=True)
        LMM[v]=dict(b_dia=float(m1.params['diaN']), se=float(m1.bse['diaN']),
                    z=float(m1.tvalues['diaN']), p=float(m1.pvalues['diaN']),
                    ic=[float(m1.conf_int().loc['diaN',0]), float(m1.conf_int().loc['diaN',1])],
                    icc=float(m1.cov_re.iloc[0,0]/(m1.cov_re.iloc[0,0]+m1.scale)),
                    p_tipo={k:float(vv) for k,vv in m2.pvalues.items() if 'tipo' in k})
    except Exception as e:
        LMM[v]=dict(erro=str(e))
print("\nmodelo misto (coeficiente por dia):")
for v in V:
    if 'b_dia' in LMM[v]:
        print(f"  {v:12} b={LMM[v]['b_dia']:+.3f} IC[{LMM[v]['ic'][0]:+.3f},{LMM[v]['ic'][1]:+.3f}] "
              f"p={LMM[v]['p']:.4f}  CCI={LMM[v]['icc']:.3f}")
json.dump(dict(SERP=SERP, CQ=CQ, PREV_EST=PREV_EST, FAIXA_EST=FAIXA_EST, NPOR=NPOR,
               chi=float(chi), p_chi=float(pchi), gl=int(gl), chi_f=float(chif), p_f=float(pf), gl_f=int(glf),
               NIV=NIV, AG=AG, MCN=MCN, MAT=MAT, LMM=LMM, nd=nd.tolist(),
               FAV=FAV.tolist(), NEU=NEU.tolist(), RIS=RIS.tolist(), ncomp=len(comp)),
          open(f"{S}/V2_a3.json",'w'), ensure_ascii=False)
print("\ngravado: V2_a3.json")
