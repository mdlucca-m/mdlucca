# -*- coding: utf-8 -*-
"""HIIT e amistoso: resposta aguda, resíduo do dia seguinte e magnitude.

Os artigos comparam os tipos de estímulo pelo nível diário e pela resposta
aguda. Faltam três coisas: o contraste direto entre HIIT e amistoso, a resposta
RESIDUAL — o que sobra no dia seguinte, que é onde o modelo de carga mostrou
estar o efeito — e a leitura de cada magnitude contra os limiares de erro típico
e de menor mudança relevante, em vez de contra o valor de p apenas.
"""
import os, json, collections
import numpy as np
from scipy import stats
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
B=json.load(open(os.path.join(DADOS,"V2_base.json")))
TEJ=json.load(open(os.path.join(DADOS,"V2_te.json")))
P=json.load(open(os.path.join(DADOS,"V2_perfis.json")))
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V7=SUB+['TMD']
CARGA={int(k):v for k,v in B['CARGA'].items()}
TIPO={d:CARGA[d]['tipo'] for d in range(1,8)}
PAR={(p['a'],p['dia']):p for p in B['pares']}
ATL=sorted({a for a,_ in PAR})
ET={t['variavel']:t for t in TEJ['TE']}
NORMA=B['NORMA']; C=np.array(P['C']); RISCO={3,4,5}
def faixa(v):
    T=np.array([(v[i]-NORMA[s][0])/NORMA[s][1]*10+50 for i,s in enumerate(SUB)])
    return int(((C-T)**2).sum(1).argmin())
rng=np.random.default_rng(777)

def dz_ic(d, B_=4000):
    d=np.asarray(d,float); n=len(d)
    dz=d.mean()/d.std(ddof=1) if d.std(ddof=1)>0 else np.nan
    bs=[]
    for _ in range(B_):
        s=d[rng.integers(0,n,n)]
        if s.std(ddof=1)>0: bs.append(s.mean()/s.std(ddof=1))
    return float(dz), (float(np.percentile(bs,2.5)), float(np.percentile(bs,97.5))) if bs else (None,None)
def rotulo(dz):
    a=abs(dz)
    return ('trivial' if a<.2 else 'pequeno' if a<.5 else 'moderado' if a<.8 else 'grande' if a<1.2 else 'muito grande')

# ---------------- 1. resposta aguda: da manhã à noite do mesmo dia ----------------
por=collections.defaultdict(list)
for r in B['registros']: por[(r['a'],r['dia'])].append(r)
PP={}
for (a,d),g in por.items():
    if d<2 or len(g)<2: continue
    g=sorted(g,key=lambda x:x['ts']); PP[(a,d)]=(g[0],g[-1])
EST=['HIIT','Amistoso','Técnico/força']
print("=== 1. RESPOSTA AGUDA: DA MANHÃ À NOITE DO MESMO DIA ===")
print("  Δ = noite − manhã. A magnitude é lida contra o erro típico (ET) e a menor mudança relevante (MMR).\n")
AGUDA=[]
for v in V7:
    e=ET[v]
    print(f"  {v}")
    print(f"    {'estímulo':<15} {'n':>4} {'Δ médio':>9} {'IC 95%':>18} {'dz':>7} {'IC de dz':>16} "
          f"{'magnitude':>13} {'Δ/ET':>6} {'p':>9}")
    for t in EST:
        ks=[k for k in PP if TIPO[k[1]]==t]
        d=np.array([PP[k][1][v]-PP[k][0][v] for k in ks],float)
        if len(d)<6: continue
        dz,ic=dz_ic(d); s_,p=stats.wilcoxon(d) if np.any(d!=0) else (np.nan,1.0)
        icm=stats.bootstrap((d,), np.mean, n_resamples=3000, random_state=1).confidence_interval
        AGUDA.append(dict(variavel=v, estimulo=t, n=len(d), delta=float(d.mean()),
                          ic=[float(icm.low),float(icm.high)], dz=dz, dz_ic=list(ic),
                          magnitude=rotulo(dz), delta_sobre_et=float(abs(d.mean())/e['et']),
                          supera_mmr=bool(abs(d.mean())>e['mmr']), p=float(p)))
        print(f"    {t:<15} {len(d):>4} {d.mean():>+9.2f} [{icm.low:>+7.2f}; {icm.high:>+6.2f}] "
              f"{dz:>+7.2f} [{ic[0]:>+6.2f}; {ic[1]:>+5.2f}] {rotulo(dz):>13} "
              f"{abs(d.mean())/e['et']:>6.2f} {p:>9.4f}")

# ---------------- 2. HIIT contra amistoso, no mesmo atleta ----------------
print("\n=== 2. HIIT CONTRA AMISTOSO, PAREADO NO MESMO ATLETA ===")
print("  Média da resposta aguda de cada atleta em dias de HIIT contra a dele em dias de amistoso.\n")
print(f"  {'variável':<11} {'n':>4} {'HIIT':>8} {'amistoso':>10} {'diferença':>11} {'IC 95%':>18} "
      f"{'dz':>7} {'magnitude':>12} {'p':>9}")
CONTR=[]
for v in V7:
    ph=[]; pa=[]
    for a in ATL:
        h=[PP[(a,d)][1][v]-PP[(a,d)][0][v] for d in range(2,8) if (a,d) in PP and TIPO[d]=='HIIT']
        m=[PP[(a,d)][1][v]-PP[(a,d)][0][v] for d in range(2,8) if (a,d) in PP and TIPO[d]=='Amistoso']
        if h and m: ph.append(np.mean(h)); pa.append(np.mean(m))
    ph=np.array(ph); pa=np.array(pa); d=ph-pa
    if len(d)<6: continue
    dz,ic=dz_ic(d); s_,p=stats.wilcoxon(ph,pa) if np.any(d!=0) else (np.nan,1.0)
    icm=stats.bootstrap((d,), np.mean, n_resamples=3000, random_state=2).confidence_interval
    CONTR.append(dict(variavel=v, n=len(d), hiit=float(ph.mean()), amistoso=float(pa.mean()),
                      diferenca=float(d.mean()), ic=[float(icm.low),float(icm.high)],
                      dz=dz, magnitude=rotulo(dz), p=float(p)))
    print(f"  {v:<11} {len(d):>4} {ph.mean():>+8.2f} {pa.mean():>+10.2f} {d.mean():>+11.2f} "
          f"[{icm.low:>+7.2f}; {icm.high:>+6.2f}] {dz:>+7.2f} {rotulo(dz):>12} {p:>9.4f}")

# ---------------- 3. resíduo: o que sobra na manhã seguinte ----------------
print("\n=== 3. RESÍDUO: O QUE SOBRA NA MANHÃ SEGUINTE ===")
print("  Δ = manhã do dia d+1 − manhã do dia d, por tipo de estímulo do dia d.")
print("  É aqui que o modelo de carga localizou o efeito: o humor responde à véspera.\n")
print(f"  {'variável':<11} {'estímulo':<15} {'n':>4} {'Δ da manhã':>11} {'IC 95%':>18} {'dz':>7} "
      f"{'magnitude':>12} {'Δ/ET':>6} {'p':>9}")
RESID=[]
for v in V7:
    for t in EST:
        d=[]
        for a in ATL:
            for dd in range(2,7):
                if TIPO[dd]!=t: continue
                if (a,dd) in PP and (a,dd+1) in PP:
                    d.append(PP[(a,dd+1)][0][v]-PP[(a,dd)][0][v])
        d=np.array(d,float)
        if len(d)<6: continue
        e=ET[v]; dz,ic=dz_ic(d); s_,p=stats.wilcoxon(d) if np.any(d!=0) else (np.nan,1.0)
        icm=stats.bootstrap((d,), np.mean, n_resamples=3000, random_state=3).confidence_interval
        RESID.append(dict(variavel=v, estimulo=t, n=len(d), delta=float(d.mean()),
                          ic=[float(icm.low),float(icm.high)], dz=dz, magnitude=rotulo(dz),
                          delta_sobre_et=float(abs(d.mean())/e['et']), p=float(p)))
        print(f"  {v:<11} {t:<15} {len(d):>4} {d.mean():>+11.2f} [{icm.low:>+7.2f}; {icm.high:>+6.2f}] "
              f"{dz:>+7.2f} {rotulo(dz):>12} {abs(d.mean())/e['et']:>6.2f} {p:>9.4f}")

# ---------------- 4. migração para a faixa de risco por estímulo ----------------
print("\n=== 4. MIGRAÇÃO PARA A FAIXA DE RISCO, POR ESTÍMULO ===")
print(f"  {'estímulo':<15} {'pares':>6} {'fora de risco de manhã':>24} {'entram até a noite':>20} "
      f"{'taxa':>8} {'IC 95%':>16}")
MIG=[]
for t in EST:
    ks=[k for k in PP if TIPO[k[1]]==t]
    fora=[k for k in ks if faixa([PP[k][0][s] for s in SUB]) not in RISCO]
    ent=[k for k in fora if faixa([PP[k][1][s] for s in SUB]) in RISCO]
    n,x=len(fora),len(ent)
    lo,hi=stats.beta.ppf([.025,.975],[x+.5,x+.5],[n-x+.5,n-x+.5]) if n else (np.nan,np.nan)
    MIG.append(dict(estimulo=t, pares=len(ks), fora=n, entram=x,
                    taxa=float(x/n) if n else None, ic=[float(lo),float(hi)]))
    print(f"  {t:<15} {len(ks):>6} {n:>24} {x:>20} {x/n if n else float('nan'):>8.1%} "
          f"[{lo:>5.1%}; {hi:>5.1%}]")
tab=np.array([[m['entram'], m['fora']-m['entram']] for m in MIG])
chi,pq,_,_=stats.chi2_contingency(tab)
print(f"\n  qui-quadrado entre os três estímulos: χ² = {chi:.3f}; p = {pq:.4f}")

json.dump(dict(AGUDA=AGUDA, CONTRASTE=CONTR, RESIDUO=RESID, MIGRACAO=MIG,
               qui2=float(chi), p_qui2=float(pq)),
          open(os.path.join(DADOS,"V2_estim.json"),'w'), ensure_ascii=False, indent=1)
print(f"\n→ {os.path.join(DADOS,'V2_estim.json')}")
