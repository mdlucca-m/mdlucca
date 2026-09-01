# -*- coding: utf-8 -*-
"""Auditoria de aderência ao protocolo declarado de coleta.

Protocolo declarado pelo autor:
  D1 (21/04/2024)  uma única coleta, à noite, após o treino.
  D2 a D7 (22 a 27/04)  duas coletas por atleta: a primeira da manhã como PRÉ
                        e a última do dia como PÓS.
  Nenhuma coleta intermediária entre 21 e 28 de abril de 2024.
  Mais de uma resposta do mesmo atleta no mesmo período é erro.

A rotina confere o cumprimento pelo carimbo de data e hora sob duas leituras:

  REGRA A (literal, sem relógio)  pré = primeiro registro do atleta no dia;
      pós = último registro do dia; excedente = tudo o que fica entre os dois.
      Em D1 vale apenas o primeiro registro. Não pressupõe hora de corte.

  REGRA B (com corte de relógio)  o dia divide-se em manhã (04h–11h59) e fim
      do dia (12h–03h59); vale a primeira resposta da manhã e a última do fim
      do dia. Explicita quantos atletas-dia sequer têm registro de manhã.

Nada é removido aqui. A rotina produz o laudo, a evidência estrutural das
janelas de coleta e a lista anonimizada dos casos.
"""
import os, json, collections, datetime as dt, statistics as st, sqlite3
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS=os.path.join(RAIZ,"dados")
CX=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))

CORTE=12; VIRADA=4; CURTO=30; LACUNA=25
SUB=['tensao','depressao','raiva','vigor','fadiga','confusao','pth']
ts=lambda c: dt.datetime.fromisoformat(c)

REG=[dict(atleta=a, dia=d, carimbo=c, hora=c[11:16], t=ts(c),
          v=dict(zip(SUB,resto)))
     for a,d,c,*resto in CX.execute(
         "select atleta,dia,carimbo,"+",".join(SUB)+" from registro order by atleta,dia,carimbo")]
for r in REG:
    h=int(r['carimbo'][11:13]); r['periodo']='manhã' if VIRADA<=h<CORTE else 'fim do dia'

AD=collections.defaultdict(list)
for r in REG: AD[(r['atleta'],r['dia'])].append(r)
for v in AD.values(): v.sort(key=lambda r:r['t'])

# --------------------------------------------------------------- 1. a janela
JAN=dict(primeiro=min(r['carimbo'] for r in REG), ultimo=max(r['carimbo'] for r in REG),
         fora=sum(1 for r in REG if not (dt.datetime(2024,4,21,4)<=r['t']<dt.datetime(2024,4,28,4))))

# ------------------------------- 2. janelas de coleta do elenco, dia a dia
JANELAS=[]
for d in range(1,8):
    v=sorted([r for r in REG if r['dia']==d], key=lambda r:r['t'])
    bl=[[v[0]]]
    for r in v[1:]:
        if (r['t']-bl[-1][-1]['t']).total_seconds()/60>LACUNA: bl.append([r])
        else: bl[-1].append(r)
    JANELAS.append(dict(dia=d, n=len(bl), blocos=[
        dict(ini=b[0]['hora'], fim=b[-1]['hora'], registros=len(b),
             atletas=len({r['atleta'] for r in b}),
             repeticoes=len(b)-len({r['atleta'] for r in b})) for b in bl]))

# ------------------------------------------------------ 3. as duas regras
def julga(v, d, regra):
    """devolve (indices validos, indices excedentes)"""
    if regra=='A':
        val=[0] if d==1 else ([0] if len(v)==1 else [0,len(v)-1])
    else:
        m=[i for i,r in enumerate(v) if r['periodo']=='manhã']
        f=[i for i,r in enumerate(v) if r['periodo']=='fim do dia']
        val=([f[-1]] if f else []) if d==1 else (([m[0]] if m else [])+([f[-1]] if f else []))
    return val, [i for i in range(len(v)) if i not in val]

RES={}
for regra in ('A','B'):
    exc=[]; conf=0; incompleto=0
    for (a,d),v in sorted(AD.items()):
        val,ex=julga(v,d,regra)
        alvo=1 if d==1 else 2
        if len(val)==alvo and not ex: conf+=1
        if len(val)<alvo: incompleto+=1
        for i in ex:
            r=v[i]; outros=[v[j] for j in range(len(v)) if j!=i]
            perto=min(abs((r['t']-x['t']).total_seconds())/60 for x in outros)
            igual=any(all(abs((r['v'][k] or 0)-(x['v'][k] or 0))<1e-9 for k in SUB) for x in outros)
            exc.append(dict(atleta=a, dia=d, hora=r['hora'], carimbo=r['carimbo'],
                            periodo=r['periodo'], minutos_do_vizinho=round(perto,1),
                            reenvio_imediato=perto<CURTO, identico_a_outro=igual))
    RES[regra]=dict(conformes=conf, incompletos=incompleto, excedentes=exc,
                    n_excedentes=len(exc), retidos=len(REG)-len(exc),
                    reenvio_imediato=sum(1 for x in exc if x['reenvio_imediato']),
                    identicos=sum(1 for x in exc if x['identico_a_outro']))

# ------------------------------- 4. atletas-dia sem nenhum registro de manhã
SEM_MANHA=[dict(atleta=a, dia=d, horas=[r['hora'] for r in v])
           for (a,d),v in sorted(AD.items())
           if d>1 and not any(r['periodo']=='manhã' for r in v)]
SO_MANHA=[dict(atleta=a, dia=d, horas=[r['hora'] for r in v])
          for (a,d),v in sorted(AD.items())
          if d>1 and not any(r['periodo']=='fim do dia' for r in v)]

# ----------------------------------- 5. o que muda no valor diário (Regra A)
IMPACTO={}
for k in SUB:
    dif=[]
    for (a,d),v in AD.items():
        atual=st.mean([r['v'][k] for r in v if r['v'][k] is not None])
        val,_=julga(v,d,'A')
        prot=st.mean([v[i]['v'][k] for i in val if v[i]['v'][k] is not None])
        dif.append(prot-atual)
    IMPACTO[k]=dict(n=len(dif), media=round(st.mean(dif),4), dp=round(st.pstdev(dif),4),
                    max_abs=round(max(abs(x) for x in dif),4),
                    n_diferente=sum(1 for x in dif if abs(x)>1e-9))

POR_DIA=[]
for d in range(1,8):
    sub={k:v for k,v in AD.items() if k[1]==d}
    ea=sum(len(julga(v,d,'A')[1]) for v in sub.values())
    eb=sum(len(julga(v,d,'B')[1]) for v in sub.values())
    POR_DIA.append(dict(dia=d, atletas=len(sub), registros=sum(len(v) for v in sub.values()),
                        esperado=len(sub)*(1 if d==1 else 2),
                        excedente_A=ea, excedente_B=eb,
                        janelas=JANELAS[d-1]['n']))

SAIDA=dict(parametros=dict(corte=CORTE, virada=VIRADA, curto=CURTO, lacuna=LACUNA),
           JANELA=JAN, JANELAS=JANELAS, POR_DIA=POR_DIA,
           REGRA_A={k:v for k,v in RES['A'].items()},
           REGRA_B={k:v for k,v in RES['B'].items()},
           SEM_MANHA=SEM_MANHA, SO_MANHA=SO_MANHA, IMPACTO=IMPACTO,
           TOTAIS=dict(registros=len(REG), atleta_dia=len(AD),
                       esperado=sum(p['esperado'] for p in POR_DIA)))
json.dump(SAIDA, open(os.path.join(JS,"V2_proto.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)

b=lambda x,d=3: f"{x:.{d}f}".replace('.',',').replace('-','−')
print("AUDITORIA DE ADERÊNCIA AO PROTOCOLO DE COLETA")
print(f"janela {JAN['primeiro'][:16].replace('T',' ')} a {JAN['ultimo'][:16].replace('T',' ')}"
      f" · registros fora de 21/04 04h a 28/04 04h: {JAN['fora']}")
print(f"{len(REG)} registros · {len(AD)} pares atleta-dia · esperado pelo protocolo: {SAIDA['TOTAIS']['esperado']}")
print("\nDIA  atletas  registros  esperado  janelas  excedente A  excedente B")
for p in POR_DIA:
    print(f" D{p['dia']}     {p['atletas']:3d}      {p['registros']:4d}      {p['esperado']:4d}"
          f"      {p['janelas']:2d}        {p['excedente_A']:4d}         {p['excedente_B']:4d}")
T=SAIDA['TOTAIS']
print(f"tot     {T['atleta_dia']:3d}      {T['registros']:4d}      {T['esperado']:4d}"
      f"               {RES['A']['n_excedentes']:4d}         {RES['B']['n_excedentes']:4d}")
for r in ('A','B'):
    x=RES[r]
    print(f"\nREGRA {r}: {x['conformes']}/{len(AD)} pares conformes · {x['n_excedentes']} excedentes "
          f"({x['reenvio_imediato']} a menos de {CURTO} min de outro, {x['identicos']} com as sete "
          f"variáveis idênticas) · {x['retidos']} registros retidos")
print(f"\natletas-dia (D2 a D7) sem nenhum registro de manhã: {len(SEM_MANHA)}")
print(f"atletas-dia (D2 a D7) sem nenhum registro depois do meio-dia: {len(SO_MANHA)}")
print("\nJANELAS DE COLETA DO ELENCO (lacuna > 25 min)")
for j in JANELAS:
    print(f"  D{j['dia']}: {j['n']} janelas")
    for b_ in j['blocos']:
        if b_['registros']<3: continue
        print(f"      {b_['ini']}–{b_['fim']}  {b_['registros']:3d} reg  {b_['atletas']:2d} atletas"
              + (f"  ({b_['repeticoes']} repetição na mesma janela)" if b_['repeticoes'] else ""))
print("\nIMPACTO DA REGRA A SOBRE O VALOR DIÁRIO (protocolo − média de todos os registros)")
print(f"  {'variável':<11}{'média':>9}{'DP':>9}{'máx |Δ|':>10}{'alterados':>14}")
for k,v in IMPACTO.items():
    print(f"  {k:<11}{b(v['media']):>9}{b(v['dp']):>9}{b(v['max_abs']):>10}{v['n_diferente']:>9}/{v['n']}")
print(f"\nsalvo: {os.path.join(JS,'V2_proto.json')}")
