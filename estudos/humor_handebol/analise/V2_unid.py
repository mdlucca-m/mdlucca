# -*- coding: utf-8 -*-
"""A unidade de análise muda o veredito inferencial, ou só a prevalência?

A auditoria mostrou que as quatro unidades produzem variações do perfil iceberg
entre 0,6 e 18,0 pontos percentuais sobre os mesmos dados. Falta responder à
pergunta gêmea, que é a do Artigo 2: os testes de hipótese também trocam de
veredito conforme a unidade? Se trocarem, declarar a unidade deixa de ser
higiene e passa a ser condição de validade.
"""
import os, json, collections
import numpy as np
from scipy import stats
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
B=json.load(open(os.path.join(DADOS,"V2_base.json")))
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V7=SUB+['TMD']
REG=B['registros']; PARES=B['pares']

# ---------------- as quatro unidades, cada uma como uma tabela atleta × dia ----------------
def u_ad():                                   # par atleta-dia: média das respostas do dia
    return {(p['a'],p['dia']):{v:p[v] for v in V7} for p in PARES}
def u_r():                                    # registro: cada formulário conta uma vez
    d=collections.defaultdict(list)
    for r in REG: d[(r['a'],r['dia'])].append(r)
    return d                                  # tratada à parte: não é uma tabela atleta × dia
def u_286():                                  # primeiro e último registro do dia
    por=collections.defaultdict(list)
    for r in REG: por[(r['a'],r['dia'])].append(r)
    out={}
    for k,g in por.items():
        g=sorted(g,key=lambda x:x['ts'])
        sel=[g[0]] if k[1]==1 else [g[0],g[-1]]
        out[k]={v:float(np.mean([x[v] for x in sel])) for v in V7}
    return out
UNID={'U-AD':u_ad(), 'U-286':u_286()}
# U-PAR é a U-AD restrita aos atletas com medida em D1 e em D7
ad=UNID['U-AD']
comuns={a for a,d in ad if d==1} & {a for a,d in ad if d==7}
UNID['U-PAR']={k:v for k,v in ad.items() if k[0] in comuns}
# U-R: cada registro é uma observação; para os testes pareados, exige agregação,
# de modo que a única leitura possível é a não pareada. Fica declarada como tal.

def testes(tab):
    """Friedman sobre atletas completos, Page e Wilcoxon D1×D7, por variável."""
    ats=sorted({a for a,_ in tab})
    comp=[a for a in ats if all((a,d) in tab for d in range(1,8))]
    par17=[a for a in ats if (a,1) in tab and (a,7) in tab]
    out={}
    for v in V7:
        r={}
        if len(comp)>=5:
            M=np.array([[tab[(a,d)][v] for d in range(1,8)] for a in comp],float)
            try:
                chi,p=stats.friedmanchisquare(*M.T); r['friedman_p']=float(p)
                r['W']=float(chi/(len(comp)*6))
            except Exception: r['friedman_p']=None; r['W']=None
            # L de Page com alternativa ordenada
            postos=np.array([stats.rankdata(l) for l in M])
            L=float(sum((d+1)*postos[:,d].sum() for d in range(7)))
            n,k=len(comp),7
            mu=n*k*(k+1)**2/4; sd=np.sqrt(n*(k**3-k)**2/(144*(k-1)))
            z=(L-mu)/sd; r['page_p']=float(2*(1-stats.norm.cdf(abs(z)))); r['page_z']=float(z)
        else:
            r['friedman_p']=r['W']=r['page_p']=r['page_z']=None
        if len(par17)>=6:
            x=[tab[(a,1)][v] for a in par17]; y=[tab[(a,7)][v] for a in par17]
            try:
                s_,p=stats.wilcoxon(x,y); r['wilcoxon_p']=float(p)
                r['delta']=float(np.mean(y)-np.mean(x))
            except Exception: r['wilcoxon_p']=None; r['delta']=None
        else: r['wilcoxon_p']=r['delta']=None
        r['n_completos']=len(comp); r['n_pareados']=len(par17)
        out[v]=r
    return out

RES={u:testes(t) for u,t in UNID.items()}
# U-R: leitura não pareada, Kruskal-Wallis entre os sete dias sobre todos os registros
por_dia={d:[r for r in REG if r['dia']==d] for d in range(1,8)}
RES['U-R']={}
for v in V7:
    grupos=[[r[v] for r in por_dia[d]] for d in range(1,8)]
    h,p=stats.kruskal(*grupos)
    x=[r[v] for r in por_dia[1]]; y=[r[v] for r in por_dia[7]]
    u_,p2=stats.mannwhitneyu(x,y)
    RES['U-R'][v]=dict(friedman_p=None, W=None, page_p=None, page_z=None,
                       wilcoxon_p=float(p2), delta=float(np.mean(y)-np.mean(x)),
                       kruskal_p=float(p), n_completos=None, n_pareados=None,
                       nota='não pareada: o registro não permite pareamento por atleta')

ORD=['U-AD','U-286','U-PAR','U-R']
print("=== O VEREDITO INFERENCIAL MUDA COM A UNIDADE DE ANÁLISE? ===")
print("  Contraste entre a linha de base e a véspera da estreia (D1 × D7), por unidade.\n")
print(f"  {'variável':<11} " + " ".join(f"{u:>22}" for u in ORD))
print(f"  {'':<11} " + " ".join(f"{'p (Δ)':>22}" for _ in ORD))
TROCA=[]
for v in V7:
    linha=[]; vered=[]
    for u in ORD:
        r=RES[u][v]; p=r['wilcoxon_p']
        linha.append(f"{p:.4f} ({r['delta']:+.2f})" if p is not None else "—")
        vered.append(None if p is None else p<.05)
    n_sig=sum(1 for x in vered if x is True); n_val=sum(1 for x in vered if x is not None)
    troca=bool(0<n_sig<n_val)
    TROCA.append(dict(variavel=v, vereditos={u:vered[i] for i,u in enumerate(ORD)},
                      p={u:RES[u][v]['wilcoxon_p'] for u in ORD},
                      delta={u:RES[u][v]['delta'] for u in ORD}, troca=troca))
    print(f"  {v:<11} " + " ".join(f"{x:>22}" for x in linha) + ("   ← troca" if troca else ""))
n_troca=sum(1 for t in TROCA if t['troca'])
print(f"\n  {n_troca} de {len(V7)} variáveis trocam de veredito conforme a unidade adotada.")
print(f"  n pareado por unidade: " + " · ".join(
    f"{u} = {RES[u][V7[0]]['n_pareados'] if RES[u][V7[0]]['n_pareados'] is not None else 'não pareável'}"
    for u in ORD))

print("\n=== COMPARAÇÃO GLOBAL ENTRE OS SETE DIAS (Friedman, atletas completos) ===")
print(f"  {'variável':<11} " + " ".join(f"{u:>16}" for u in ORD[:3]))
TROCA_G=[]
for v in V7:
    linha=[]; vered=[]
    for u in ORD[:3]:
        p=RES[u][v]['friedman_p']
        linha.append(f"{p:.4f}" if p is not None else "—"); vered.append(None if p is None else p<.05)
    n_sig=sum(1 for x in vered if x is True); n_val=sum(1 for x in vered if x is not None)
    troca=bool(0<n_sig<n_val)
    TROCA_G.append(dict(variavel=v, p={u:RES[u][v]['friedman_p'] for u in ORD[:3]}, troca=troca))
    print(f"  {v:<11} " + " ".join(f"{x:>16}" for x in linha) + ("   ← troca" if troca else ""))
print(f"  atletas completos: " + " · ".join(f"{u} = {RES[u][V7[0]]['n_completos']}" for u in ORD[:3]))
print(f"  {sum(1 for t in TROCA_G if t['troca'])} de {len(V7)} variáveis trocam de veredito no teste global.")

json.dump(dict(RES=RES, TROCA_D1D7=TROCA, TROCA_GLOBAL=TROCA_G, ordem=ORD),
          open(os.path.join(DADOS,"V2_unid.json"),'w'), ensure_ascii=False, indent=1)
print(f"\n→ {os.path.join(DADOS,'V2_unid.json')}")
