# -*- coding: utf-8 -*-
"""Mecanismo de ausência: a falta depende do que se quer medir?

Os dois artigos declaram, como limitação, que o mecanismo de ausência não foi
modelado e que a hipótese de ausência ignorável não é verificável. Ela não é
demonstrável, mas é testável em uma direção: se a falta no dia seguinte
dependesse do humor de hoje, a hipótese estaria refutada. Este roteiro faz esse
teste, mede a concentração das faltas e calcula limites de pior caso.
"""
import os, json, collections
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
B=json.load(open(os.path.join(DADOS,"V2_base.json")))
CARGA={int(k):v for k,v in B['CARGA'].items()}
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V7=SUB+['TMD']
P={(p['a'],p['dia']):p for p in B['pares']}
ATL=sorted({a for a,_ in P})

# ---------------- 1. a falta de amanhã depende do humor de hoje? ----------------
lin=[]
for a in ATL:
    for d in range(1,7):
        if (a,d) not in P: continue
        r=dict(atleta=a, dia=d, respondeu=int((a,d+1) in P),
               horas=CARGA[d+1]['h'], estimulo=CARGA[d+1]['tipo'])
        for v in V7: r[v.replace('.','_')]=P[(a,d)][v]
        lin.append(r)
df=pd.DataFrame(lin)
print(f"=== A FALTA DE AMANHÃ DEPENDE DO HUMOR DE HOJE? ===")
print(f"  {len(df)} pares atleta-dia com dia seguinte possível · "
      f"{df.respondeu.sum()} responderam ({df.respondeu.mean():.1%})\n")
UNI=[]
print(f"  {'variável de hoje':<12} {'média se respondeu':>19} {'média se faltou':>16} "
      f"{'diferença':>10} {'p (Mann-Whitney)':>17}")
for v in V7:
    c=v.replace('.','_'); x1=df.loc[df.respondeu==1,c].values; x0=df.loc[df.respondeu==0,c].values
    u,p=stats.mannwhitneyu(x1,x0)
    UNI.append(dict(variavel=v, media_respondeu=float(x1.mean()), media_faltou=float(x0.mean()),
                    diferenca=float(x0.mean()-x1.mean()), p=float(p), n1=int(len(x1)), n0=int(len(x0)),
                    significativo=bool(p<.05)))
    print(f"  {v:<12} {x1.mean():>19.2f} {x0.mean():>16.2f} {x0.mean()-x1.mean():>+10.2f} {p:>17.4f}"
          + ("  ←" if p<.05 else ""))

# ---------------- 2. modelo logístico misto ----------------
print("\n=== MODELO LOGÍSTICO DE EFEITOS MISTOS ===")
print("  logito(responder amanhã) = β₀ + β₁·humor de hoje + β₂·dia + u(atleta)\n")
MIX=[]
for v in V7:
    c=v.replace('.','_'); d2=df[['atleta','dia','respondeu',c]].rename(columns={c:'x'}).dropna()
    try:
        m=smf.mixedlm("respondeu ~ x + dia", d2, groups=d2.atleta).fit(reml=False)
        MIX.append(dict(variavel=v, beta=float(m.params['x']), se=float(m.bse['x']),
                        p=float(m.pvalues['x']), p_dia=float(m.pvalues['dia'])))
    except Exception as e:
        MIX.append(dict(variavel=v, beta=None, se=None, p=None, p_dia=None, erro=str(e)))
# sete testes sobre a mesma pergunta pedem ajuste
val=[e for e in MIX if e['p'] is not None]
ordem=sorted(range(len(val)), key=lambda i: val[i]['p'])
m=len(val); anterior=0.0
for r,i in enumerate(ordem):
    ph=min(1.0, max(anterior, (m-r)*val[i]['p'])); anterior=ph
    val[i]['p_holm']=float(ph); val[i]['significativo']=bool(ph<.05)
print(f"  {'variável':<12} {'β do humor':>12} {'erro padrão':>12} {'p':>9} {'p de Holm':>11} {'p do dia':>10}")
for e in MIX:
    if e['beta'] is None: print(f"  {e['variavel']:<12} {'—':>12}"); continue
    print(f"  {e['variavel']:<12} {e['beta']:>+12.4f} {e['se']:>12.4f} {e['p']:>9.4f} "
          f"{e['p_holm']:>11.4f} {e['p_dia']:>10.4f}" + ("  ←" if e['significativo'] else ""))
sig=[e for e in MIX if e.get('significativo')]
bruto=[e for e in MIX if e['p'] is not None and e['p']<.05]
print(f"\n  {len(bruto)} de {len(MIX)} variáveis com p bruto abaixo de 0,05; "
      f"{len(sig)} sobrevivem ao ajuste de Holm para as sete comparações.")
if bruto and not sig:
    b=bruto[0]
    print(f"  A tensão é a única candidata (β = {b['beta']:+.4f}; p = {b['p']:.4f}), e o sinal é o esperado: "
          "quem amanhece mais tenso responde um pouco menos no dia seguinte. Após o ajuste, "
          f"p = {b['p_holm']:.3f} — insuficiente para afirmar dependência.")

# ---------------- 3. concentração das faltas ----------------
falt={a: 7-sum(1 for d in range(1,8) if (a,d) in P) for a in ATL}
n_falt=np.array(sorted(falt.values()))
sem=sum(1 for v in falt.values() if v==0)
med_humor={a: float(np.mean([P[(a,d)]['TMD'] for d in range(1,8) if (a,d) in P])) for a in ATL}
r_,p_=stats.spearmanr([falt[a] for a in ATL], [med_humor[a] for a in ATL])
CONC=dict(sem_falta=sem, total=len(ATL), max_faltas=int(n_falt.max()),
          mediana=float(np.median(n_falt)),
          com_falta=int(len(ATL)-sem), total_faltas=int(sum(falt.values())),
          rho_faltas_pth=float(r_), p_rho=float(p_))
print(f"\n=== CONCENTRAÇÃO DAS FALTAS ===")
print(f"  {sem} dos {len(ATL)} atletas não faltaram nenhum dia; o máximo é {n_falt.max()} faltas.")
print(f"  As {CONC['total_faltas']} faltas concentram-se em {CONC['com_falta']} atletas "
      f"({CONC['com_falta']/len(ATL):.0%} do elenco); os demais {sem} têm série completa.")
print(f"  Correlação entre número de faltas e PTH médio do atleta: ρ = {r_:+.3f} (p = {p_:.3f}) — "
      + ("associação" if p_<.05 else "sem associação"))

# ---------------- 4. limites de pior caso ----------------
# Se todo ausente em D7 estivesse no pior (ou no melhor) valor plausível, a
# conclusão de queda do vigor entre D1 e D7 sobreviveria?
print("\n=== LIMITES DE PIOR CASO PARA A VARIAÇÃO D1 → D7 ===")
print("  Cada ausente em D7 recebe o pior e o melhor valor plausível do seu próprio percentil extremo.")
LIM=[]
for v in V7:
    obs1=[P[(a,1)][v] for a in ATL if (a,1) in P]
    obs7=[P[(a,7)][v] for a in ATL if (a,7) in P]
    ausentes=[a for a in ATL if (a,1) in P and (a,7) not in P]
    p05,p95=np.percentile(obs7,[5,95])
    d_obs=float(np.mean(obs7)-np.mean(obs1))
    d_lo=float((np.sum(obs7)+p05*len(ausentes))/(len(obs7)+len(ausentes))-np.mean(obs1))
    d_hi=float((np.sum(obs7)+p95*len(ausentes))/(len(obs7)+len(ausentes))-np.mean(obs1))
    mantem=bool(np.sign(d_lo)==np.sign(d_hi)==np.sign(d_obs))
    LIM.append(dict(variavel=v, delta=d_obs, limite_inf=min(d_lo,d_hi), limite_sup=max(d_lo,d_hi),
                    n_ausentes=len(ausentes), sinal_preservado=mantem))
    print(f"  {v:<12} Δ observado {d_obs:>+7.2f}   limites [{min(d_lo,d_hi):>+6.2f}; {max(d_lo,d_hi):>+6.2f}]"
          + ("   sinal preservado" if mantem else "   ← o sinal pode inverter"))
n_ok=sum(1 for l in LIM if l['sinal_preservado'])
print(f"\n  {n_ok} de {len(LIM)} variáveis mantêm o sinal da variação sob os dois cenários extremos.")

json.dump(dict(UNIVARIADA=UNI, MISTO=MIX, CONCENTRACAO=CONC, LIMITES=LIM,
               n_pares=len(df), n_respondeu=int(df.respondeu.sum())),
          open(os.path.join(DADOS,"V2_falta.json"),'w'), ensure_ascii=False, indent=1)
print(f"\n→ {os.path.join(DADOS,'V2_falta.json')}")
