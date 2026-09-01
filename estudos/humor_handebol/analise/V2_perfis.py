# -*- coding: utf-8 -*-
"""Classificação nos seis perfis e matriz de reconciliação por unidade de análise."""
import json, numpy as np, collections
from scipy.optimize import linear_sum_assignment
import os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); SAIDA=os.path.join(RAIZ,"saida")
os.makedirs(DADOS, exist_ok=True); os.makedirs(SAIDA, exist_ok=True)
S=DADOS
B=json.load(open(f"{S}/V2_base.json"))
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
NORMA=B['NORMA']; NOMES=['Iceberg','Superfície','Submerso','Barbatana de tubarão','Iceberg invertido','Everest invertido']
# centroides canônicos (Parsons-Smith, Terry & Machin, 2017) em escore T
CAN=np.array(json.load(open(os.path.join(DADOS,"U_perfis.json")))['CAN'])  # centroides canônicos já validados (recuperados das faixas T publicadas)
PREV_REF=[34.3,14.6,30.6,11.6,6.2,2.7]
def Tvec(rec):
    return np.array([(rec[s]-NORMA[s][0])/NORMA[s][1]*10+50 for s in SUB])
def kmeans_semeado(X, C0, it=300):
    C=C0.copy()
    for _ in range(it):
        d=((X[:,None,:]-C[None,:,:])**2).sum(2); lab=d.argmin(1)
        Cn=C.copy()
        for k in range(len(C)):
            if (lab==k).any(): Cn[k]=X[lab==k].mean(0)
        if np.allclose(Cn,C,atol=1e-9): break
        C=Cn
    return C, ((X[:,None,:]-C[None,:,:])**2).sum(2).argmin(1)
def reancorar(C):
    d=((C[:,None,:]-CAN[None,:,:])**2).sum(2)
    r,c=linear_sum_assignment(d); ordem=np.empty(len(C),int); ordem[c]=r
    return ordem
# ---------- unidades de análise ----------
reg=B['registros']
por=collections.defaultdict(list)
for r in reg: por[(r['a'],r['dia'])].append(r)
for k in por: por[k].sort(key=lambda x:x['ts'])
UNI={}
UNI['U-R']  = [dict(a=a,dia=d,**{s:x[s] for s in SUB}) for (a,d),g in por.items() for x in g]
UNI['U-AD'] = [dict(a=p['a'],dia=p['dia'],**{s:p[s] for s in SUB}) for p in B['pares']]
b286=[]
for (a,d),g in por.items():
    if d==1: b286.append(g[-1])
    else:
        b286.append(g[0])
        if len(g)>1: b286.append(g[-1])
UNI['U-286']=[dict(a=x['a'],dia=x['dia'],**{s:x[s] for s in SUB}) for x in b286]
comp={a for a in {p['a'] for p in B['pares']}
      if any(p['a']==a and p['dia']==1 for p in B['pares']) and any(p['a']==a and p['dia']==7 for p in B['pares'])}
UNI['U-PAR']=[u for u in UNI['U-AD'] if u['a'] in comp]
# ---------- ajuste (sempre sobre U-AD, a unidade sem pseudorreplicação) ----------
Xad=np.array([Tvec(u) for u in UNI['U-AD']])
C,_=kmeans_semeado(Xad, CAN.copy())
ordem=reancorar(C); C=C[np.argsort(ordem)]
def classifica(X): return ((X[:,None,:]-C[None,:,:])**2).sum(2).argmin(1)
OUT={'C':C.tolist(),'CAN':CAN.tolist(),'PREV_REF':PREV_REF,'NOMES':NOMES}
print("=== prevalência dos seis perfis por unidade de análise ===")
print(f"{'unidade':8}{'n':>6}  " + ''.join(f"{n[:11]:>13}" for n in NOMES))
REC={}
for u,dados in UNI.items():
    X=np.array([Tvec(x) for x in dados]); lab=classifica(X)
    p=[100*np.mean(lab==k) for k in range(6)]
    REC[u]={'n':len(dados),'prev':p,'lab':lab.tolist(),
            'dia':[x['dia'] for x in dados],'a':[x['a'] for x in dados]}
    print(f"{u:8}{len(dados):6}  " + ''.join(f"{v:13.1f}" for v in p))
print(f"{'ref.2017':8}{'—':>6}  " + ''.join(f"{v:13.1f}" for v in PREV_REF))
print("\n=== iceberg em D1 e D7 por unidade (o número que divergia entre os manuscritos) ===")
print(f"{'unidade':8}{'n D1':>6}{'ice D1':>9}{'n D7':>6}{'ice D7':>9}   variação")
for u,r in REC.items():
    lab=np.array(r['lab']); dia=np.array(r['dia'])
    n1=(dia==1).sum(); n7=(dia==7).sum()
    i1=100*np.mean(lab[dia==1]==0); i7=100*np.mean(lab[dia==7]==0)
    print(f"{u:8}{n1:6}{i1:9.1f}{n7:6}{i7:9.1f}   {i7-i1:+.1f} p.p.")
OUT['REC']={u:{'n':v['n'],'prev':v['prev']} for u,v in REC.items()}
OUT['lab_AD']=REC['U-AD']['lab']; OUT['dia_AD']=REC['U-AD']['dia']; OUT['a_AD']=REC['U-AD']['a']
OUT['T_AD']=Xad.tolist()
json.dump(OUT, open(f"{S}/V2_perfis.json",'w'), ensure_ascii=False)
print("\ngravado: V2_perfis.json")
