# -*- coding: utf-8 -*-
"""A analise que falta: como os SEIS PERFIS respondem a cada tipo de estimulo.

Ate aqui a resposta ao estimulo foi medida nas variaveis continuas. Esta
rotina leva a pergunta ao nivel do perfil: a distribuicao dos seis perfis
muda conforme o dia seja de intervalado, de amistoso ou de trabalho
tecnico? E a migracao dentro do dia depende do estimulo?
"""
import json, numpy as np
from scipy import stats
from itertools import combinations
rng=np.random.default_rng(20240421)
import os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); SAIDA=os.path.join(RAIZ,"saida")
os.makedirs(SAIDA, exist_ok=True)
B=json.load(open(f"{DADOS}/U_base.json")); PR=B['pares']; PP=B['prepos']; ATL=B['ATL']
Q=json.load(open(f"{DADOS}/U_perfis.json"))
NORMA=B['NORMA']; C=np.array(Q['C'])
SUB6=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
NAMES=['Iceberg','Superfície','Submerso','Barbatana de tubarão','Iceberg invertido','Everest invertido']
EST={1:'Basal',2:'HIIT',3:'Amistoso',4:'HIIT',5:'Amistoso',6:'Técnico',7:'HIIT'}
TIPOS=['HIIT','Amistoso','Técnico']
lab=np.array(Q['lab']); dia=np.array(Q['dia']); ath=np.array(Q['ath'])

def Tv(k,x):
    m,s=NORMA[k]; return (x-m)/s*10+50
def classificar(vec):
    return int(((C-vec)**2).sum(1).argmin())
def holm(ps):
    m=len(ps); o=np.argsort(ps); adj=np.empty(m); run=0.0
    for i,j in enumerate(o):
        run=max(run,(m-i)*ps[j]); adj[j]=min(run,1.0)
    return adj

print("="*84); print("A. PREVALENCIA DOS SEIS PERFIS POR TIPO DE ESTIMULO (pares atleta-dia)")
tipo_par=np.array([EST[d] for d in dia])
PREV_EST={}
print(f"{'Perfil':24}"+"".join(f"{t:>13}" for t in ['Basal']+TIPOS))
for j,nm in enumerate(NAMES):
    linha=f"{nm:24}"; PREV_EST[nm]={}
    for t in ['Basal']+TIPOS:
        m=tipo_par==t
        pct=100*float((lab[m]==j).mean()) if m.any() else float('nan')
        PREV_EST[nm][t]=pct
        linha+=f"{pct:12.1f}%"
    print(linha)
FAIXA_EST={}
for nm,idx in (('Favorável',[0]),('Neutra',[1,2]),('Risco',[3,4,5])):
    linha=f"{nm:24}"; FAIXA_EST[nm]={}
    for t in ['Basal']+TIPOS:
        m=tipo_par==t
        pct=100*float(np.isin(lab[m],idx).mean()) if m.any() else float('nan')
        FAIXA_EST[nm][t]=pct; linha+=f"{pct:12.1f}%"
    print(linha)
NPOR={t:int((tipo_par==t).sum()) for t in ['Basal']+TIPOS}
print(f"{'n de pares':24}"+"".join(f"{NPOR[t]:13}" for t in ['Basal']+TIPOS))

# teste de independencia perfil x estimulo, restrito aos tres estimulos
tab=np.array([[int(((tipo_par==t)&(lab==j)).sum()) for t in TIPOS] for j in range(6)])
chi,p_chi,gl,_=stats.chi2_contingency(tab)
print(f"\nqui-quadrado perfil x estimulo: chi2={chi:.2f}, gl={gl}, p={p_chi:.4f}")
tab_f=np.array([[int(((tipo_par==t)&np.isin(lab,idx)).sum()) for t in TIPOS]
                for idx in ([0],[1,2],[3,4,5])])
chi_f,p_f,gl_f,_=stats.chi2_contingency(tab_f)
print(f"qui-quadrado faixa  x estimulo: chi2={chi_f:.2f}, gl={gl_f}, p={p_f:.4f}")

print("\n"+"="*84); print("B. PERFIL NA MEDIDA PRE E NA POS, POR TIPO DE ESTIMULO")
PP_EST={t:{'pre':np.zeros(6),'pos':np.zeros(6)} for t in TIPOS}
pares_por_tipo={t:[] for t in TIPOS}
for q in PP:
    t=EST[q['dia']]
    jp=classificar(np.array([Tv(s,q['pre_'+s]) for s in SUB6]))
    jq=classificar(np.array([Tv(s,q['pos_'+s]) for s in SUB6]))
    PP_EST[t]['pre'][jp]+=1; PP_EST[t]['pos'][jq]+=1
    pares_por_tipo[t].append((q['a'],jp,jq))
PREV_PP={}
for t in TIPOS:
    n=PP_EST[t]['pre'].sum()
    PREV_PP[t]={'n':int(n),
                'pre':(100*PP_EST[t]['pre']/n).tolist(),
                'pos':(100*PP_EST[t]['pos']/n).tolist()}
    print(f"\n{t}  (n = {int(n)} pares)")
    print(f"  {'perfil':24}{'pré':>9}{'pós':>9}{'Δ':>9}")
    for j,nm in enumerate(NAMES):
        a,b_=PREV_PP[t]['pre'][j],PREV_PP[t]['pos'][j]
        print(f"  {nm:24}{a:8.1f}%{b_:8.1f}%{b_-a:+8.1f}")
    fav=(PREV_PP[t]['pre'][0],PREV_PP[t]['pos'][0])
    ris=(sum(PREV_PP[t]['pre'][3:]),sum(PREV_PP[t]['pos'][3:]))
    PREV_PP[t]['fav']=fav; PREV_PP[t]['ris']=ris
    print(f"  {'Faixa favorável':24}{fav[0]:8.1f}%{fav[1]:8.1f}%{fav[1]-fav[0]:+8.1f}")
    print(f"  {'Faixa de risco':24}{ris[0]:8.1f}%{ris[1]:8.1f}%{ris[1]-ris[0]:+8.1f}")

print("\n"+"="*84); print("C. MIGRACAO INTRADIARIA PARA O RISCO, POR TIPO DE ESTIMULO (McNemar)")
MCN_EST={}
ps=[]
for t in TIPOS:
    b_=c_=n11=n00=0
    for _a,jp,jq in pares_por_tipo[t]:
        rp,rq=jp>=3,jq>=3
        if rp and not rq: b_+=1
        elif rq and not rp: c_+=1
        elif rp and rq: n11+=1
        else: n00+=1
    chi=(abs(b_-c_)-1)**2/(b_+c_) if (b_+c_)>0 else 0.0
    p=float(stats.chi2.sf(chi,1))
    MCN_EST[t]=dict(entra=c_,sai=b_,n11=n11,n00=n00,chi=float(chi),p=p,
                    n=len(pares_por_tipo[t]),
                    razao=(c_/b_ if b_ else float('inf')))
    ps.append(p)
    print(f"  {t:10} entra {c_:3}  sai {b_:3}  estáveis em risco {n11:3}  fora {n00:3}  "
          f"chi2={chi:5.2f}  p={p:.4f}")
adj=holm(np.array(ps))
for t,a in zip(TIPOS,adj): MCN_EST[t]['ph']=float(a)
print("  Holm:", {t:round(MCN_EST[t]['ph'],4) for t in TIPOS})

print("\n"+"="*84); print("D. SERIES DOS SEIS PERFIS: PISO DE RUIDO, SUAVIZACAO E DERIVADAS")
def suavizar(y):
    y=np.asarray(y,float); z=y.copy()
    for i in range(1,len(y)-1): z[i]=.25*y[i-1]+.5*y[i]+.25*y[i+1]
    return z
nd=np.array(Q['nd'],float)
SER_PERF={}
print(f"{'Perfil ou faixa':24}{'D1':>7}{'D7':>7}{'Δ':>8}{'piso':>7}{'sinal':>7}  choques")
series={nm:np.array(Q['prev'][j]) for j,nm in enumerate(NAMES)}
series['Favorável']=np.array(Q['FAV']); series['Neutra']=np.array(Q['NEU'])
series['De risco']=np.array(Q['RIS'])
for nm,y in series.items():
    p_=y/100.0
    se=100*np.sqrt(np.clip(p_*(1-p_),0,None)/nd)
    piso=float(se.mean()); sm=suavizar(y); d1=np.diff(sm)
    ch=[i+1 for i,x in enumerate(d1) if abs(x)>piso]
    SER_PERF[nm]=dict(y=y.tolist(),se=se.tolist(),piso=piso,sm=sm.tolist(),
                      d1=d1.tolist(),choque=ch,dtot=float(y[6]-y[0]),
                      sinal=bool(abs(y[6]-y[0])>piso))
    print(f"{nm:24}{y[0]:6.1f}%{y[6]:6.1f}%{y[6]-y[0]:+8.1f}{piso:7.1f}"
          f"{'SIM' if SER_PERF[nm]['sinal'] else 'não':>7}  "
          +", ".join(f"D{c}→D{c+1}" for c in ch))

print("\n"+"="*84); print("E. CRUZAMENTO ENTRE AS SERIES DE FAIXA (favorável x risco)")
CRZ_P={}
for a_,b_ in (('Favorável','De risco'),('Iceberg','Barbatana de tubarão')):
    ya,yb=series[a_],series[b_]
    lim=float(np.sqrt(SER_PERF[a_]['piso']**2+SER_PERF[b_]['piso']**2))
    dif=ya-yb; cross=[]
    for i in range(6):
        if dif[i]==0 or dif[i+1]==0: continue
        if np.sign(dif[i])!=np.sign(dif[i+1]):
            t=abs(dif[i])/(abs(dif[i])+abs(dif[i+1])); cross.append(float(1+i+t))
    est=bool(abs(dif[0])>lim and abs(dif[6])>lim and np.sign(dif[0])!=np.sign(dif[6]))
    CRZ_P[f"{a_}×{b_}"]=dict(dif=dif.tolist(),lim=lim,cross=cross,est=est,
                             d1=float(dif[0]),d7=float(dif[6]))
    print(f"  {a_} × {b_}: Δ D1={dif[0]:+.1f}  Δ D7={dif[6]:+.1f}  limiar={lim:.1f}  "
          f"cruza em {[round(c,2) for c in cross]}  "
          f"{'INVERSÃO ESTABELECIDA' if est else 'divergência'}")

json.dump(dict(PREV_EST=PREV_EST,FAIXA_EST=FAIXA_EST,NPOR=NPOR,
               chi=float(chi),p_chi=float(p_chi),gl=int(gl),
               chi_f=float(chi_f),p_f=float(p_f),gl_f=int(gl_f),
               tab=tab.tolist(),tab_f=tab_f.tolist(),
               PREV_PP=PREV_PP,MCN_EST=MCN_EST,SER_PERF=SER_PERF,CRZ_P=CRZ_P),
          open(f"{DADOS}/U_estimulo.json","w"),ensure_ascii=False)
print("\nsalvo U_estimulo.json")
