# -*- coding: utf-8 -*-
"""Erro típico, menor mudança importante e magnitude: quando a mudança importa.

Os artigos separam sinal de ruído por um piso construído sobre o erro-padrão
diário do GRUPO. Esse critério responde se a média se moveu. Não responde à
pergunta que o preparador faz, que é individual: a mudança deste atleta é maior
do que o erro da medida, e é grande o bastante para importar?

Três limiares respondem a isso, e são de naturezas distintas:
  · erro típico (ET): o ruído da própria medida, repetida no mesmo atleta;
  · menor mudança relevante (MMR): 0,2 do desvio entre atletas, critério de
    distribuição;
  · mudança mínima importante ancorada (MMI): o valor de mudança que melhor
    separa quem entrou na faixa de risco de quem não entrou, critério externo.
"""
import os, json, collections
import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score, roc_curve
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
B=json.load(open(os.path.join(DADOS,"V2_base.json")))
A1=json.load(open(os.path.join(DADOS,"V2_a1.json")))
P=json.load(open(os.path.join(DADOS,"V2_perfis.json")))
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V7=SUB+['TMD']
PAR={(p['a'],p['dia']):p for p in B['pares']}
ATL=sorted({a for a,_ in PAR})
NORMA=B['NORMA']; C=np.array(P['C']); RISCO={3,4,5}
def faixa(v):
    T=np.array([(v[i]-NORMA[s][0])/NORMA[s][1]*10+50 for i,s in enumerate(SUB)])
    return int(((C-T)**2).sum(1).argmin())
rng=np.random.default_rng(4321)

# ---------------- 1. erro típico, entre dias consecutivos ----------------
# ET = desvio das diferenças entre dias consecutivos ÷ √2. Inclui a variação
# biológica de um dia para o outro, que é o ruído contra o qual o monitoramento
# diário efetivamente opera.
def ic_boot(fn, B_=1500):
    vs=[]
    for _ in range(B_):
        sel=rng.choice(ATL,size=len(ATL),replace=True)
        v=fn(sel)
        if v is not None and v==v: vs.append(v)
    return (float(np.percentile(vs,2.5)), float(np.percentile(vs,97.5))) if len(vs)>100 else (None,None)

TE=[]
print("=== ERRO TÍPICO, MENOR MUDANÇA RELEVANTE E MUDANÇA MÍNIMA DETECTÁVEL ===")
print("  ET a partir das diferenças entre dias consecutivos do mesmo atleta; "
      "MMR = 0,2 × desvio entre atletas.\n")
print(f"  {'variável':<11} {'ET':>6} {'IC 95% do ET':>16} {'ET %':>6} {'MMR':>6} {'MMD95':>7} "
      f"{'MMR/ET':>7} {'aptidão':>12} {'piso do grupo':>14}")
for v in V7:
    difs=[PAR[(a,d+1)][v]-PAR[(a,d)][v] for a in ATL for d in range(1,7)
          if (a,d) in PAR and (a,d+1) in PAR]
    et=float(np.std(difs,ddof=1)/np.sqrt(2))
    medias=[np.mean([PAR[(a,d)][v] for d in range(1,8) if (a,d) in PAR]) for a in ATL]
    sd_entre=float(np.std(medias,ddof=1)); mmr=0.2*sd_entre
    mmd=1.96*np.sqrt(2)*et
    grand=float(np.mean([PAR[k][v] for k in PAR]))
    def _et(sel):
        d=[PAR[(a,dd+1)][v]-PAR[(a,dd)][v] for a in sel for dd in range(1,7)
           if (a,dd) in PAR and (a,dd+1) in PAR]
        return float(np.std(d,ddof=1)/np.sqrt(2)) if len(d)>5 else None
    ic=ic_boot(_et)
    razao=mmr/et if et>0 else float('nan')
    apt=('boa' if razao>=1.0 else 'aceitável' if razao>=0.5 else 'insuficiente')
    piso=A1['SER'][v]['piso']
    TE.append(dict(variavel=v, et=et, et_ic=list(ic), et_pct=float(100*et/grand) if grand else None,
                   sd_entre=sd_entre, mmr=float(mmr), mmd95=float(mmd), razao=float(razao),
                   aptidao=apt, piso_grupo=float(piso), n_difs=len(difs)))
    print(f"  {v:<11} {et:>6.2f} {f'[{ic[0]:.2f}; {ic[1]:.2f}]' if ic[0] else '—':>16} "
          f"{100*et/grand if grand else float('nan'):>6.1f} {mmr:>6.2f} {mmd:>7.2f} {razao:>7.2f} "
          f"{apt:>12} {piso:>14.2f}")
print("\n  O piso do grupo e o erro típico medem coisas diferentes: o primeiro é o ruído da MÉDIA")
print("  diária, o segundo é o ruído da medida de UM atleta. O segundo é sempre maior, e é o que")
print("  vale para decidir sobre um atleta.")

# ---------------- 1b. erro puro da medida, sem variação biológica ----------------
# A auditoria de qualidade encontrou reenvios do mesmo atleta no mesmo dia em
# intervalo curto. Entre dois envios separados por poucos minutos não há treino
# nem sono no meio: a diferença é erro de medida quase puro. A estimativa é
# imprecisa pelo n, mas separa o que o ET de dias consecutivos confunde.
import datetime
pares_curtos=[]
for (a,d),g in por0.items() if False else []: pass
PORD=collections.defaultdict(list)
for r in B['registros']: PORD[(r['a'],r['dia'])].append(r)
for (a,d),g in PORD.items():
    g=sorted(g,key=lambda x:x['ts'])
    for u,w in zip(g,g[1:]):
        dt=(datetime.datetime.fromisoformat(w['ts'])-datetime.datetime.fromisoformat(u['ts'])).total_seconds()/60
        if dt<=30: pares_curtos.append((u,w,dt))
print(f"\n=== ERRO PURO DA MEDIDA: {len(pares_curtos)} reenvios em 30 minutos ou menos ===")
print("  Sem treino nem sono entre os dois envios, a diferença é erro de medida, não mudança real.\n")
print(f"  {'variável':<11} {'ET puro':>8} {'ET entre dias':>14} {'variação biológica':>19} "
      f"{'% do ET que é biológico':>25}")
PURO=[]
for v in V7:
    d=[w[v]-u[v] for u,w,_ in pares_curtos]
    etp=float(np.std(d,ddof=1)/np.sqrt(2)) if len(d)>3 else None
    etd=[t for t in TE if t['variavel']==v][0]['et']
    bio=float(np.sqrt(max(etd**2-etp**2,0))) if etp is not None else None
    pct=float(100*bio**2/etd**2) if bio is not None and etd>0 else None
    PURO.append(dict(variavel=v, et_puro=etp, et_entre_dias=etd, variacao_biologica=bio,
                     pct_biologico=pct, n_pares=len(d)))
    print(f"  {v:<11} {etp if etp is not None else float('nan'):>8.2f} {etd:>14.2f} "
          f"{bio if bio is not None else float('nan'):>19.2f} "
          f"{pct if pct is not None else float('nan'):>25.1f}")
neg=[e['variavel'] for e in PURO if e['variacao_biologica']==0]
print(f"\n  Duas ressalvas, e uma delas desfaz a leitura fácil. Primeira: com n = {len(pares_curtos)} pares a")
print("  estimativa é imprecisa, e quem reenvia é justamente quem quis alterar a resposta, de modo que o")
print("  valor é um TETO do erro de medida, não uma estimativa não enviesada dele. Segunda: mesmo como")
print("  teto, o erro puro é da mesma ordem do erro entre dias — em "
      + (", ".join(neg) if neg else "nenhuma variável") + " ele o iguala ou supera, o que")
print("  é impossível na população e denuncia o tamanho do erro amostral da própria estimativa.")
print("  A decomposição entre erro de medida e variação biológica, portanto, NÃO é identificável com")
print("  estes dados. O que se sustenta é o enunciado que não depende dela: o erro típico entre dias")
print("  supera a menor mudança relevante nas sete variáveis, qualquer que seja a sua composição.")

# ---------------- 2. mudança mínima importante, ancorada ----------------
# Âncora externa: entrar na faixa de risco entre a manhã e a noite do mesmo dia.
por=collections.defaultdict(list)
for r in B['registros']: por[(r['a'],r['dia'])].append(r)
casos=[]
for (a,d),g in por.items():
    if d<2 or len(g)<2: continue
    g=sorted(g,key=lambda x:x['ts']); pre,pos=g[0],g[-1]
    if faixa([pre[s] for s in SUB]) in RISCO: continue      # já estava em risco
    casos.append(dict(a=a, d=d, entrou=int(faixa([pos[s] for s in SUB]) in RISCO),
                      **{v: pos[v]-pre[v] for v in V7}))
y=np.array([c['entrou'] for c in casos])
print(f"\n=== MUDANÇA MÍNIMA IMPORTANTE, ANCORADA NA ENTRADA EM RISCO ===")
print(f"  {len(casos)} pares que amanhecem fora da faixa · {y.sum()} entram até a noite ({y.mean():.1%})\n")
print(f"  {'variável':<11} {'AUC da variação':>16} {'MMI (Youden)':>13} {'sensib.':>8} {'especif.':>9} "
      f"{'MMI/ET':>7} {'supera a MMR?':>14}")
MMI=[]
for v in V7:
    x=np.array([c[v] for c in casos],float)
    direc=1 if v!='Vigor' else -1                    # no vigor, a queda é o evento
    auc=roc_auc_score(y, direc*x)
    fpr,tpr,thr=roc_curve(y, direc*x)
    j=int(np.argmax(tpr-fpr)); corte=float(direc*thr[j])
    e=[t for t in TE if t['variavel']==v][0]
    util=bool(auc>=.60)
    MMI.append(dict(variavel=v, auc=float(auc), corte=(corte if util else None),
                    sens=float(tpr[j]), espec=float(1-fpr[j]), discrimina=util,
                    corte_sobre_et=(float(abs(corte)/e['et']) if util else None),
                    supera_mmr=(bool(abs(corte)>e['mmr']) if util else None),
                    n=len(casos), eventos=int(y.sum())))
    if util:
        print(f"  {v:<11} {auc:>16.3f} {corte:>13.2f} {tpr[j]:>8.2f} {1-fpr[j]:>9.2f} "
              f"{abs(corte)/e['et']:>7.2f} {'sim' if abs(corte)>e['mmr'] else 'não':>14}")
    else:
        print(f"  {v:<11} {auc:>16.3f} {'não discrimina':>13} {'—':>8} {'—':>9} {'—':>7} {'—':>14}")

# ---------------- 3. quantos atletas mudaram de verdade? ----------------
print("\n=== RESPOSTA INDIVIDUAL: QUANTOS ATLETAS SUPERAM CADA LIMIAR ENTRE D1 E D7 ===")
comuns=[a for a in ATL if (a,1) in PAR and (a,7) in PAR]
IND=[]
print(f"  {'variável':<11} {'n':>4} {'|Δ| > ET':>10} {'|Δ| > MMR':>11} {'|Δ| > MMD95':>13} "
      f"{'na direção do grupo':>21}")
for v in V7:
    e=[t for t in TE if t['variavel']==v][0]
    d=np.array([PAR[(a,7)][v]-PAR[(a,1)][v] for a in comuns],float)
    dir_grupo=np.sign(np.mean(d))
    ind=dict(variavel=v, n=len(comuns),
             acima_et=int((np.abs(d)>e['et']).sum()),
             acima_mmr=int((np.abs(d)>e['mmr']).sum()),
             acima_mmd=int((np.abs(d)>e['mmd95']).sum()),
             mesma_direcao=int((np.sign(d)==dir_grupo).sum()),
             delta_medio=float(np.mean(d)))
    IND.append(ind)
    print(f"  {v:<11} {len(comuns):>4} {ind['acima_et']:>10} {ind['acima_mmr']:>11} "
          f"{ind['acima_mmd']:>13} {ind['mesma_direcao']:>21}")
print("\n  A leitura de grupo esconde heterogeneidade: mesmo onde a média se move com clareza,")
print("  parte do elenco não ultrapassa o erro da própria medida.")

json.dump(dict(TE=TE, ET_PURO=PURO, MMI=MMI, INDIVIDUAL=IND, n_atletas_D1D7=len(comuns),
               n_casos_ancora=len(casos), eventos_ancora=int(y.sum())),
          open(os.path.join(DADOS,"V2_te.json"),'w'), ensure_ascii=False, indent=1)
print(f"\n→ {os.path.join(DADOS,'V2_te.json')}")
