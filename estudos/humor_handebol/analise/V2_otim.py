# -*- coding: utf-8 -*-
"""Programação linear: como distribuir as horas do microciclo terminal.

Duas etapas. Primeiro estima-se, na própria base, a resposta do humor à carga do
dia e à carga da véspera. Depois monta-se o programa linear que maximiza a carga
semanal sujeita a tetos de fadiga, pisos de vigor, polimento final e limites de
variação entre dias consecutivos, e leem-se os preços-sombra para saber qual
restrição está segurando a solução.

Advertência que acompanha o modelo: com uma equipe e sete dias, o efeito das
horas é indissociável do dia do microciclo e da carga acumulada. Os coeficientes
são associativos e servem de instrumento de planejamento, não de prova causal.
"""
import os, json, sqlite3, itertools
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
from scipy.optimize import linprog
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
B=json.load(open(os.path.join(DADOS,"V2_base.json")))
CARGA={int(k):v for k,v in B['CARGA'].items()}
H_OBS=np.array([CARGA[d]['h'] for d in range(1,8)])
TIPO={d:CARGA[d]['tipo'] for d in range(1,8)}

# ============================ 1. RESPOSTA DOSE-HUMOR ============================
df=pd.DataFrame(B['pares']).rename(columns={'a':'atleta'})
df['h']=df.dia.map(lambda d:CARGA[d]['h'])
df['h_vespera']=df.dia.map(lambda d:CARGA[d-1]['h'] if d>1 else 0.0)
df['acum']=df.dia.map(lambda d:CARGA[d]['acum'])
MOD={}
print("=== RESPOSTA DOSE-HUMOR (modelo misto, intercepto aleatório por atleta) ===")
print(f"  y = β₀ + β₁·h_d + β₂·h_(d−1) + u_a   ·   n = {len(df)} pares, {df.atleta.nunique()} atletas\n")
print(f"  {'variável':<10} {'β₀':>8} {'β₁ (dia)':>11} {'p':>9} {'β₂ (véspera)':>14} {'p':>9}")
for v in ['Fadiga','Vigor','TMD','Tensão']:
    d2=df[['atleta','h','h_vespera',v]].dropna().rename(columns={v:'y'})
    m=smf.mixedlm("y ~ h + h_vespera", d2, groups=d2.atleta).fit(reml=False)
    MOD[v]=dict(b0=float(m.params['Intercept']), b1=float(m.params['h']), b2=float(m.params['h_vespera']),
                p1=float(m.pvalues['h']), p2=float(m.pvalues['h_vespera']),
                se1=float(m.bse['h']), se2=float(m.bse['h_vespera']), n=int(len(d2)))
    e=MOD[v]
    print(f"  {v:<10} {e['b0']:>8.3f} {e['b1']:>11.4f} {e['p1']:>9.4f} {e['b2']:>14.4f} {e['p2']:>9.4f}")
print("\n  Leitura: o coeficiente é a variação esperada do escore por hora adicional de treino,")
print("  mantida a carga da véspera. Efeito do dia e da carga acumulada não são separáveis nesta amostra.")

# ============================ 2. OS PROGRAMAS LINEARES ============================
# Decisão: h_1 … h_7, horas de treino de cada dia do microciclo.
# O humor do dia d responde à véspera (β₂), não ao próprio dia (β₁ não significativo),
# de modo que toda restrição de recuperação é defasada em um dia.
F, V = MOD['Fadiga'], MOD['Vigor']
prev=lambda M,x: [float(M['b0']+M['b1']*x[d-1]+M['b2']*(x[d-2] if d>1 else 0)) for d in range(1,8)]
OBS=dict(total=float(H_OBS.sum()), horas=[float(v) for v in H_OBS],
         fadiga=prev(F,H_OBS), vigor=prev(V,H_OBS))
OBS['vigor_minimo']=float(min(OBS['vigor'])); OBS['fadiga_maxima']=float(max(OBS['fadiga']))

PAR=dict(
  h_max=5.0,                 # teto diário, igual ao maior dia observado
  h_min=1.0,                 # estímulo mínimo em dia de treino
  fadiga_max=7.0,            # teto de fadiga prevista, em pontos da subescala
  vigor_min=4.5,             # piso de vigor previsto
  salto_max=2.5,             # variação máxima entre dias consecutivos
  amistoso={3:4.5, 5:5.0},   # amistoso de D3 e de D5, fixados pelo calendário
  polimento=0.6,             # D7 não passa de 60% de nenhum dia anterior
  total=23.0,                # carga da semana; no Programa I é igualdade
)

def montar(par, objetivo='maximin_vigor', total_como='igualdade'):
    """Devolve (resultado, rótulos das desigualdades, rótulos das igualdades, A_ub, b_ub).

    Variáveis: h_1…h_7 e, quando o objetivo é maximin, a folga t (vigor mínimo garantido).
    """
    n=7; maximin = (objetivo=='maximin_vigor'); m=n+1 if maximin else n
    if maximin:   c=np.r_[np.zeros(n), -1.0]              # max t  ⇔  min −t
    elif objetivo=='carga': c=np.r_[-np.ones(n)]           # max Σh
    else: c=np.array([F['b1'] if d==7 else (F['b2'] if d==6 else 0.0) for d in range(1,8)])
    def lin(coef, extra=0.0):
        a=np.zeros(m); a[:n]=coef
        if maximin: a[n]=extra
        return a
    A=[]; b=[]; rot=[]
    for d in range(1,8):                                   # fadiga prevista ≤ teto
        v=np.zeros(n); v[d-1]=F['b1']
        if d>1: v[d-2]=F['b2']
        A.append(lin(v)); b.append(par['fadiga_max']-F['b0'])
        rot.append(f"fadiga prevista em D{d} ≤ {par['fadiga_max']:.1f}")
    for d in range(1,8):                                   # vigor previsto ≥ piso (e ≥ t no maximin)
        v=np.zeros(n); v[d-1]=-V['b1']
        if d>1: v[d-2]=-V['b2']
        A.append(lin(v)); b.append(V['b0']-par['vigor_min'])
        rot.append(f"vigor previsto em D{d} ≥ {par['vigor_min']:.2f}")
        if maximin:
            A.append(lin(v, extra=1.0)); b.append(V['b0'])
            rot.append(f"vigor previsto em D{d} ≥ t")
    for d in range(2,8):                                   # variação entre dias consecutivos
        v=np.zeros(n); v[d-1]=1; v[d-2]=-1
        A.append(lin(v)); b.append(par['salto_max']); rot.append(f"D{d} − D{d-1} ≤ {par['salto_max']:.1f} h")
        A.append(lin(-v)); b.append(par['salto_max']); rot.append(f"D{d-1} − D{d} ≤ {par['salto_max']:.1f} h")
    for d in range(1,7):                                   # polimento do último dia
        v=np.zeros(n); v[6]=1; v[d-1]=-par['polimento']
        A.append(lin(v)); b.append(0.0); rot.append(f"polimento: D7 ≤ {par['polimento']:.0%} de D{d}")
    Ae=[]; be=[]; rote=[]
    for d,hh in par['amistoso'].items():
        v=np.zeros(n); v[d-1]=1; Ae.append(lin(v)); be.append(hh)
        rote.append(f"D{d} fixado em {hh:.1f} h pelo calendário")
    if total_como=='igualdade':
        Ae.append(lin(np.ones(n))); be.append(par['total']); rote.append(f"carga da semana = {par['total']:.1f} h")
    else:
        A.append(lin(np.ones(n))); b.append(par['total']); rot.append(f"carga da semana ≤ {par['total']:.1f} h")
    lim=[(par['h_min'], par['h_max'])]*n + ([(None,None)] if maximin else [])
    r=linprog(c, A_ub=np.array(A), b_ub=np.array(b), A_eq=np.array(Ae), b_eq=np.array(be),
              bounds=lim, method='highs')
    return r, rot, rote, np.array(A), np.array(b)

# ---------------- Programa I: mesma carga, melhor arranjo ----------------
res, ROT, ROT_EQ, A_ub, b_ub = montar(PAR)
if not res.success: raise SystemExit("Programa I inviável: "+res.message)
h=res.x[:7]; t=float(res.x[7])
SOL=dict(programa='I · redistribuir as mesmas 23 horas maximizando o pior dia de vigor',
         sucesso=True, total=float(h.sum()), horas=[float(x) for x in h],
         vigor_minimo_garantido=t, fadiga=prev(F,h), vigor=prev(V,h), pth=prev(MOD['TMD'],h))
print("\n=== PROGRAMA I — mesma carga semanal, arranjo que maximiza o pior dia de vigor ===")
print("  max t   s.a.   vigor previsto em D_d ≥ t  (d = 1…7),  Σ h_d = 23,  demais restrições")
print(f"\n  {'dia':<5} {'estímulo':<15} {'observado':>10} {'ótimo':>8} {'Δ':>7} "
      f"{'fadiga prev.':>13} {'vigor prev.':>12}")
for d in range(1,8):
    print(f"  D{d:<4} {TIPO[d]:<15} {H_OBS[d-1]:>10.1f} {h[d-1]:>8.2f} {h[d-1]-H_OBS[d-1]:>+7.2f} "
          f"{SOL['fadiga'][d-1]:>13.2f} {SOL['vigor'][d-1]:>12.2f}")
print(f"  {'total':<21} {H_OBS.sum():>10.1f} {h.sum():>8.2f} {h.sum()-H_OBS.sum():>+7.2f}")
print(f"\n  pior dia de vigor: observado {OBS['vigor_minimo']:.2f} → ótimo {t:.2f} "
      f"(ganho de {t-OBS['vigor_minimo']:+.2f} ponto, com a mesma carga)")
print(f"  fadiga máxima da semana: observada {OBS['fadiga_maxima']:.2f} → ótima {max(SOL['fadiga']):.2f}")

# ---------------- preços-sombra ----------------
marg=res.ineqlin.marginals; margeq=res.eqlin.marginals
folga=b_ub-A_ub@res.x
ATIVAS=[dict(restricao=r, preco_sombra=float(-mm), folga=float(ss), ativa=bool(abs(ss)<1e-7))
        for r,mm,ss in zip(ROT,marg,folga) if abs(mm)>1e-9]
EQ=[dict(restricao=r, preco_sombra=float(-mm)) for r,mm in zip(ROT_EQ,margeq)]
print("\n=== RESTRIÇÕES QUE SEGURAM A SOLUÇÃO (preço-sombra em pontos de vigor) ===")
print("  O preço-sombra é quanto o pior dia de vigor melhora se a restrição afrouxar uma unidade.")
for a in sorted(ATIVAS,key=lambda a:-abs(a['preco_sombra']))[:8]:
    print(f"  {a['restricao']:<44} folga {a['folga']:>7.3f}   preço-sombra {a['preco_sombra']:>+7.4f}")
for e in EQ:
    print(f"  {e['restricao']:<44} {'':>13}   preço-sombra {e['preco_sombra']:>+7.4f}")

# ---------------- Programa II: teto de carga imposto pela recuperação ----------------
p2=dict(PAR); p2['total']=35.0; p2['vigor_min']=OBS['vigor_minimo']
res2,ROT2,ROTE2,A2,b2=montar(p2, objetivo='carga', total_como='desigualdade')
h2=res2.x[:7]
SOL2=dict(programa='II · carga máxima que as restrições de recuperação admitem',
          sucesso=bool(res2.success), total=float(h2.sum()), horas=[float(x) for x in h2],
          fadiga=prev(F,h2), vigor=prev(V,h2))
print("\n=== PROGRAMA II — teto de carga que a recuperação admite ===")
print(f"  Exigindo apenas o mesmo pior dia de vigor do calendário observado ({OBS['vigor_minimo']:.2f}),")
print(f"  a semana comportaria {h2.sum():.2f} h: " + "  ".join(f"D{d}={h2[d-1]:.1f}" for d in range(1,8)))
print(f"  São {h2.sum()-H_OBS.sum():+.2f} h além das {H_OBS.sum():.0f} observadas. O número é EXTRAPOLAÇÃO:")
print(f"  o modelo foi ajustado com dias entre {H_OBS.min():.1f} h e {H_OBS.max():.1f} h e sobre uma única")
print("  equipe; sete dias seguidos perto do teto estão fora do suporte dos dados.")

# ---------------- fronteira eficiente ----------------
FRONTEIRA=[]
for L in [14.,16.,18.,20.,22.,23.,24.,26.,28.]:
    p=dict(PAR); p['total']=L
    r,_,_,_,_=montar(p)
    if r.success:
        x=r.x[:7]
        FRONTEIRA.append(dict(carga=L, vigor_minimo=float(r.x[7]), horas=[float(v) for v in x],
                              fadiga_maxima=float(max(prev(F,x))), fadiga_D7=prev(F,x)[6]))
    else: FRONTEIRA.append(dict(carga=L, viavel=False))
print("\n=== FRONTEIRA EFICIENTE: carga da semana contra o pior dia de vigor ===")
print(f"  {'carga':>7} {'vigor mínimo':>13} {'fadiga máxima':>14}   distribuição ótima")
for f in FRONTEIRA:
    if f.get('viavel') is False: print(f"  {f['carga']:>7.1f} {'inviável':>13}"); continue
    print(f"  {f['carga']:>7.1f} {f['vigor_minimo']:>13.3f} {f['fadiga_maxima']:>14.2f}   "
          + " ".join(f"{v:.1f}" for v in f['horas']))
viav=[f for f in FRONTEIRA if f.get('viavel') is not False]
inviav=[f for f in FRONTEIRA if f.get('viavel') is False]
MIN_ESTRUTURAL=None
if inviav:
    lo,hi=max(f['carga'] for f in inviav), min(f['carga'] for f in viav)
    for _ in range(30):
        m=(lo+hi)/2; p=dict(PAR); p['total']=m
        r,_,_,_,_=montar(p)
        if r.success: hi=m
        else: lo=m
    MIN_ESTRUTURAL=float(hi)
    print(f"\n  Carga semanal mínima estruturalmente viável: {MIN_ESTRUTURAL:.2f} h. Abaixo disso não existe "
          "distribuição que respeite os dois amistosos, o salto máximo entre dias e o estímulo mínimo diário.")
if len(viav)>1:
    a,b_=viav[0],viav[-1]
    incl=(b_['vigor_minimo']-a['vigor_minimo'])/(b_['carga']-a['carga'])
    verbo="sobe" if incl>0 else "cai"
    print(f"  De {a['carga']:.0f} h a {b_['carga']:.0f} h, o pior dia de vigor {verbo} de {a['vigor_minimo']:.3f} "
          f"para {b_['vigor_minimo']:.3f}: {abs(incl):.4f} ponto por hora acrescentada.")
    print("  A inclinação é quase nula porque quem comprime a semana não é o volume de treino, e sim os dois")
    print("  amistosos: o preço-sombra de D5 diz que cada hora do amistoso custa "
          f"{abs([e for e in EQ if e['restricao'].startswith('D5')][0]['preco_sombra']):.3f} ponto do pior dia de vigor.")

# ---------------- sensibilidade ----------------
SENS=[]
for nome,ch,vals in [('Teto de fadiga','fadiga_max',[5.5,6.0,6.5,7.0,7.5,8.0]),
                     ('Piso de vigor','vigor_min',[4.0,4.25,4.5,4.75,5.0]),
                     ('Salto máximo entre dias','salto_max',[1.0,1.5,2.0,2.5,3.0]),
                     ('Fator de polimento','polimento',[0.4,0.5,0.6,0.7,0.8]),
                     ('Teto diário','h_max',[4.0,4.5,5.0,5.5,6.0])]:
    pts=[]
    for val in vals:
        p=dict(PAR); p[ch]=val
        r,_,_,_,_=montar(p)
        pts.append(dict(valor=val, viavel=bool(r.success),
                        vigor_minimo=(float(r.x[7]) if r.success else None),
                        horas=([float(v) for v in r.x[:7]] if r.success else None)))
    SENS.append(dict(parametro=nome, chave=ch, pontos=pts))
print("\n=== SENSIBILIDADE (efeito sobre o pior dia de vigor, com 23 h fixas) ===")
for s_ in SENS:
    print(f"  {s_['parametro']}:")
    for p_ in s_['pontos']:
        print(f"    {p_['valor']:>6.2f} → " +
              (f"vigor mínimo {p_['vigor_minimo']:.3f}" if p_['viavel'] else "inviável"))

json.dump(dict(MODELO=MOD, PARAMETROS={k:v for k,v in PAR.items() if k!='amistoso'},
               AMISTOSO={str(k):v for k,v in PAR['amistoso'].items()},
               OBSERVADO=OBS, PROGRAMA_I=SOL, PROGRAMA_II=SOL2, ATIVAS=ATIVAS, EQ=EQ,
               FRONTEIRA=FRONTEIRA, CARGA_MINIMA_ESTRUTURAL=MIN_ESTRUTURAL, SENSIBILIDADE=SENS, TIPO={str(k):v for k,v in TIPO.items()}),
          open(os.path.join(DADOS,"V2_otim.json"),"w"), ensure_ascii=False, indent=1)
print(f"\n→ {os.path.join(DADOS,'V2_otim.json')}")
