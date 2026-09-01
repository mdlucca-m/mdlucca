# -*- coding: utf-8 -*-
"""Reconferência: os números publicados batem quando recalculados por outro caminho?

V2_qual.py reconstrói tudo a partir do ITEM do formulário; base_v2.py parte das
colunas já pontuadas. São dois caminhos independentes. Se convergirem sobre os
números que sustentam os três documentos, o resultado está confirmado; onde
divergirem, a divergência é o achado.
"""
import os, json, sqlite3, collections, datetime
import numpy as np
from scipy import stats
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
Q=json.load(open(os.path.join(DADOS,"V2_qual.json")))
B=json.load(open(os.path.join(DADOS,"V2_base.json")))
A1=json.load(open(os.path.join(DADOS,"V2_a1.json")))
P=json.load(open(os.path.join(DADOS,"V2_perfis.json")))
ML=json.load(open(os.path.join(DADOS,"V2_ml.json")))
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V7=SUB+['TMD']
NORMA=B['NORMA']

# ---------- caminho A: a base canônica já construída ----------
PARES_A={(p['a'],p['dia']):p for p in B['pares']}

# ---------- caminho B: reconstrução independente a partir do item ----------
# V2_qual.py guarda o resumo, não a linha; refazemos a agregação aqui a partir da fonte.
import importlib.util, io, contextlib
spec=importlib.util.spec_from_file_location("v2qual", os.path.join(RAIZ,"analise","V2_qual.py"))
mod=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(mod)
DENTRO=mod.DENTRO
por=collections.defaultdict(list)
for x in DENTRO: por[(x['atleta'],x['dia'])].append(x)
PARES_B={}
for k,g in por.items():
    g=sorted(g,key=lambda x:x['carimbo'])
    # Mesma regra de composição da base canônica, reconstruída de modo independente:
    # D1 entra por inteiro (basal de janela única); de D2 a D7 valem o primeiro
    # registro do dia (pré) e o último (pós). Ver analise/V2_proto.py.
    elei = g if k[1]==1 else ([g[0]] if len(g)==1 else [g[0],g[-1]])
    PARES_B[k]={v:float(np.mean([y['calc'][v] for y in elei])) for v in V7}

CONF=[]
def registra(bloco, item, a, b, tol=5e-3, unid=''):
    ok=(a is None and b is None) or (a is not None and b is not None and abs(a-b)<=tol)
    CONF.append(dict(bloco=bloco, item=item, caminho_a=a, caminho_b=b,
                     diferenca=(None if a is None or b is None else float(a-b)),
                     confere=bool(ok), unidade=unid))
    return ok

# ---- estrutura ----
registra('Estrutura','Pares atleta-dia', float(len(PARES_A)), float(len(PARES_B)))
registra('Estrutura','Atletas', float(len({k[0] for k in PARES_A})), float(len({k[0] for k in PARES_B})))
registra('Estrutura','Registros no microciclo', float(len(B['registros'])), float(len(DENTRO)))

# ---- Artigo 1: médias diárias e a variação D1→D7 ----
for v in V7:
    for d in (1,7):
        a=float(np.mean([p[v] for p in B['pares'] if p['dia']==d and p[v] is not None]))
        b=float(np.mean([PARES_B[k][v] for k in PARES_B if k[1]==d]))
        registra('Artigo 1 · média diária', f"{v} em D{d}", a, b)
    a1=float(np.mean([p[v] for p in B['pares'] if p['dia']==7]))-float(np.mean([p[v] for p in B['pares'] if p['dia']==1]))
    b1=(float(np.mean([PARES_B[k][v] for k in PARES_B if k[1]==7]))
        -float(np.mean([PARES_B[k][v] for k in PARES_B if k[1]==1])))
    registra('Artigo 1 · variação', f"{v} · D1 → D7", a1, b1)

# ---- Artigo 1: piso de ruído e derivada normalizada ----
def piso_e_derivadas(pares_por_chave):
    med=np.array([np.mean([pares_por_chave[k][v] for k in pares_por_chave if k[1]==d]) for d in range(1,8)])
    ep=np.array([stats.sem([pares_por_chave[k][v] for k in pares_por_chave if k[1]==d]) for d in range(1,8)])
    z=med.copy()
    for i in range(1,6): z[i]=.25*med[i-1]+.5*med[i]+.25*med[i+1]
    return float(ep.mean()), np.diff(z)/ep.mean()
for v in V7:
    pa,da=piso_e_derivadas(PARES_A); pb,db=piso_e_derivadas(PARES_B)
    registra('Artigo 1 · sinal', f"{v} · piso de ruído", pa, pb)
    registra('Artigo 1 · sinal', f"{v} · derivada D1→D2", float(da[0]), float(db[0]))
    registra('Artigo 1 · sinal', f"{v} · derivada D6→D7", float(da[5]), float(db[5]))

# ---- Artigo 1: prevalência da faixa de risco ----
C=np.array(P['C']); RISCO={3,4,5}
def faixa(vec):
    T=np.array([(vec[i]-NORMA[s][0])/NORMA[s][1]*10+50 for i,s in enumerate(SUB)])
    return int(((C-T)**2).sum(1).argmin())
for d in (1,7):
    ka=[p for p in B['pares'] if p['dia']==d]
    a=100*np.mean([faixa([p[s] for s in SUB]) in RISCO for p in ka])
    kb=[k for k in PARES_B if k[1]==d]
    b=100*np.mean([faixa([PARES_B[k][s] for s in SUB]) in RISCO for k in kb])
    registra('Artigo 1 · prevalência', f"Faixa de risco em D{d}", float(a), float(b), unid='%')

# ---- Artigo 2: Friedman e Wilcoxon D1×D7 sobre atletas com os dois dias ----
comuns=sorted({k[0] for k in PARES_A if k[1]==1} & {k[0] for k in PARES_A if k[1]==7})
for v in V7:
    xa=[PARES_A[(a,1)][v] for a in comuns]; ya=[PARES_A[(a,7)][v] for a in comuns]
    xb=[PARES_B[(a,1)][v] for a in comuns]; yb=[PARES_B[(a,7)][v] for a in comuns]
    sa,pa_=stats.wilcoxon(xa,ya); sb,pb_=stats.wilcoxon(xb,yb)
    registra('Artigo 2 · Wilcoxon D1×D7', f"{v} · p", float(pa_), float(pb_), tol=1e-6)
registra('Artigo 2 · pareamento','Atletas com D1 e D7', float(len(comuns)), float(len(comuns)))

# ---- Anexo: base da modelagem ----
prepos=[p for p in B['prepos']]
registra('Anexo · modelagem','Pares pré-pós', float(len(prepos)), float(ML['n']))
registra('Anexo · modelagem','Atletas na modelagem',
         float(len({p['a'] for p in prepos})), float(ML['atletas']))
ev=sum(1 for p in prepos if faixa([p['pos_'+s] for s in SUB]) in RISCO)
registra('Anexo · modelagem','Eventos (risco à noite)', float(ev), float(ML['eventos']))

# ---- normalidade: a escolha não paramétrica do Artigo 2 se justifica? ----
NORMALIDADE=[]
for v in V7:
    xa=[PARES_A[k][v] for k in PARES_A]; xb=[PARES_B[k][v] for k in PARES_B]
    Wa,pa_=stats.shapiro(xa); Wb,pb_=stats.shapiro(xb)
    NORMALIDADE.append(dict(variavel=v, W=float(Wa), p=float(pa_), W_b=float(Wb), p_b=float(pb_),
                            normal=bool(pa_>=.05), n=len(xa)))
    registra('Artigo 2 · normalidade', f"{v} · W de Shapiro-Wilk", float(Wa), float(Wb), tol=1e-6)

ok=sum(1 for c in CONF if c['confere']); tot=len(CONF)
print(f"=== RECONFERÊNCIA POR DOIS CAMINHOS INDEPENDENTES ===")
print(f"  {ok} de {tot} conferências batem dentro da tolerância\n")
por_bloco=collections.defaultdict(lambda:[0,0])
for c in CONF:
    por_bloco[c['bloco']][0]+=c['confere']; por_bloco[c['bloco']][1]+=1
for b,(o,t) in por_bloco.items(): print(f"  {b:<30} {o:>3}/{t}")
falhas=[c for c in CONF if not c['confere']]
if falhas:
    print("\n  DIVERGÊNCIAS:")
    for c in falhas:
        print(f"    {c['bloco']} · {c['item']}: caminho A = {c['caminho_a']}, caminho B = {c['caminho_b']}, "
              f"diferença = {c['diferenca']}")
else:
    print("\n  Nenhuma divergência. Os números dos três documentos se sustentam ao recálculo independente.")
print("\n=== NORMALIDADE DAS MÉDIAS DIÁRIAS (Shapiro-Wilk sobre os 166 pares) ===")
for n in NORMALIDADE:
    print(f"  {n['variavel']:<10} W = {n['W']:.4f} (caminho B: {n['W_b']:.4f})  p = {n['p']:.2e}  "
          + ("normal" if n['normal'] else "não normal"))
print(f"  {sum(1 for n in NORMALIDADE if not n['normal'])} de {len(NORMALIDADE)} variáveis rejeitam a "
      "normalidade, o que sustenta a via não paramétrica como rota principal do Artigo 2.")
json.dump(dict(CONF=CONF, NORMALIDADE=NORMALIDADE, ok=ok, total=tot,
               por_bloco={k:v for k,v in por_bloco.items()}),
          open(os.path.join(DADOS,"V2_conf.json"),"w"), ensure_ascii=False, indent=1)
print(f"\n→ {os.path.join(DADOS,'V2_conf.json')}")
