# -*- coding: utf-8 -*-
"""Base canônica V2 — reconstruída da FONTE-VERDADE (export do formulário).
Nenhum nome atravessa esta rotina: a codificação A01..A27 ocorre aqui dentro.
Decisões documentadas em DECISOES."""
import os, openpyxl, json, unicodedata, re, datetime, collections, hashlib
import numpy as np
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); os.makedirs(DADOS, exist_ok=True)
UP=os.environ.get("HH_UPLOADS") or "/root/.claude/uploads/4ddb0907-77b2-5876-a286-ef4b6b886e93"
P=os.path.join(UP,"ad245c30-Backup__Banco_de_dados_ORIGINAL_INTOCADO_20260723.xlsx")
ITENS={'Tensão':[5,17,18,22],'Depressão':[9,10,16,20],'Raiva':[11,15,23,26],
       'Vigor':[6,19,24,27],'Fadiga':[8,12,14,25],'Confusão':[7,13,21,28]}
SUB=list(ITENS)
D0=datetime.date(2024,4,21)
def chave(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode()
    return re.sub(r'[^a-z ]','',re.sub(r'\s+',' ',s).strip().lower())
def lik(v):
    if v is None: return None
    if isinstance(v,(int,float)): return float(v)
    m=re.match(r'\s*(\d)',str(v)); return float(m.group(1)) if m else None
def dia_de(ts):
    d=ts.date() if ts.hour>=4 else ts.date()-datetime.timedelta(days=1)
    i=(d-D0).days+1
    return i if 1<=i<=7 else None

wb=openpyxl.load_workbook(P, read_only=True, data_only=True)
rows=list(wb['Diário - Treino'].iter_rows(values_only=True))[1:]
dicw={}
for r in wb['Dicionário Atletas'].iter_rows(values_only=True):
    if r[6] and r[7] and str(r[6])!='Nome como digitado (variante)':
        dicw[chave(r[6])]=chave(r[7])
# nomes curados em COLETAS, usados apenas para resolver órfãos por carimbo
wb2=openpyxl.load_workbook(os.path.join(UP,"bc6d935b-COLETAS.xlsx"),
                           read_only=True, data_only=True)
CURADO={}
for r in wb2['Diario'].iter_rows(values_only=True):
    t=r[0]
    if isinstance(t,datetime.datetime) and r[1]: CURADO[t.isoformat()]=chave(r[1])
wb2.close()
wb.close()

pad=collections.Counter(chave(r[52]) for r in rows if r[52])
# o rótulo com 'nao identificado' é marcador, não atleta
NAOID={k for k in pad if k.startswith('nao ident')}
reais=sorted(k for k in pad if k not in NAOID)
COD={k:f"A{i+1:02d}" for i,k in enumerate(reais)}

REG=[]; orf=[]; recup=[]; fora=0
for r in rows:
    ts=r[0]
    if isinstance(ts,str): ts=datetime.datetime.fromisoformat(ts)
    d=dia_de(ts)
    if d is None: fora+=1; continue
    k=chave(r[52])
    if k in NAOID:            # recupera: 1) dicionário de variantes  2) nome curado em COLETAS
        alvo=dicw.get(chave(r[1])) or CURADO.get(ts.isoformat())
        if alvo in COD: k=alvo; recup.append((ts.isoformat(),COD[alvo]))
        else: orf.append(ts.isoformat()); continue
    vals={}
    ok=True
    for s,idx in ITENS.items():
        vs=[lik(r[i]) for i in idx]
        if any(v is None for v in vs): ok=False; break
        vals[s]=sum(vs)
    if not ok: continue
    vals['TMD']=sum(vals[s] for s in SUB if s!='Vigor')-vals['Vigor']
    REG.append(dict(a=COD[k], dia=d, ts=ts.isoformat(), **vals,
                    **{'Fad.Física':lik(r[61]),'Fad.Mental':lik(r[62]),
                       'Epworth':lik(r[63]),'PSS':lik(r[65])}))
REG.sort(key=lambda x:(x['dia'],x['a'],x['ts']))
print(f"atletas: {len(COD)} | registros no microciclo: {len(REG)} | fora da semana: {fora} | órfãos não atribuídos: {len(orf)}")
print("  recuperados:", recup)
print("  órfãos:", orf)

# ---- pares atleta-dia e pares pré/pós ----
VARS=SUB+['TMD','Fad.Física','Fad.Mental','Epworth','PSS']
por=collections.defaultdict(list)
for r in REG: por[(r['a'],r['dia'])].append(r)
PARES=[]; PREPOS=[]; EXCED=[]
for (a,d),g in sorted(por.items(), key=lambda x:(x[0][1],x[0][0])):
    g=sorted(g,key=lambda x:x['ts'])
    # Regra de composição do valor diário, auditada pelo carimbo em V2_proto.py:
    #   D1 teve coleta única, à noite, após o treino. Vale a primeira resposta de
    #   cada atleta; as 21 respostas tardias são repetição, e não segunda coleta.
    #   A conferência sustenta a leitura: dos 22 atletas que respondem depois das
    #   21h, 21 já haviam respondido na janela das 20h42, e o único que não
    #   respondera (A14) responde às 21h54, uma vez só.
    #   De D2 a D7 valem o primeiro registro do dia (pré) e o último (pós). O
    #   pré não exige hora da manhã: 59 atletas-dia só responderam a partir do
    #   meio-dia, sem qualquer registro anterior naquele dia, e nesses casos o
    #   primeiro registro é o pré, atrasado por esquecimento.
    elei = [g[0]] if d==1 else ([g[0]] if len(g)==1 else [g[0],g[-1]])
    for x in (g[1:] if d==1 else g[1:-1]):
        EXCED.append(dict(a=a, dia=d, ts=x['ts'], hora=x['ts'][11:16]))
    p={'a':a,'dia':d,'nobs':len(g),'nusado':len(elei)}
    for v in VARS:
        xs=[x[v] for x in elei if x.get(v) is not None]
        p[v]=float(np.mean(xs)) if xs else None
    PARES.append(p)
    if d>=2 and len(g)>=2:
        pp={'a':a,'dia':d}
        for v in VARS:
            pp['pre_'+v]=g[0].get(v); pp['pos_'+v]=g[-1].get(v)
        pp['h_pre']=g[0]['ts'][11:16]; pp['h_pos']=g[-1]['ts'][11:16]
        PREPOS.append(pp)
nd=[sum(1 for p in PARES if p['dia']==d) for d in range(1,8)]
print(f"pares atleta-dia: {len(PARES)}  por dia {nd}")
print(f"pares pré/pós: {len(PREPOS)}  por dia {[sum(1 for p in PREPOS if p['dia']==d) for d in range(2,8)]}")
print(f"registros que compõem o valor diário: {sum(p['nusado'] for p in PARES)} de {len(REG)}"
      f"  ·  excedentes de protocolo: {len(EXCED)}")

CARGA={1:dict(h=1.5,ses=1,tipo='Basal',cont='Técnico e tático',acum=1.5),
       2:dict(h=2.0,ses=2,tipo='HIIT',cont='HIIT + técnico e tático',acum=3.5),
       3:dict(h=4.5,ses=3,tipo='Amistoso',cont='Técnico, tático, força e amistoso',acum=8.0),
       4:dict(h=2.5,ses=2,tipo='HIIT',cont='HIIT + técnico e tático',acum=10.5),
       5:dict(h=5.0,ses=3,tipo='Amistoso',cont='Técnico, tático, força e amistoso',acum=15.5),
       6:dict(h=5.0,ses=3,tipo='Técnico/força',cont='Técnico, tático e força',acum=20.5),
       7:dict(h=2.5,ses=2,tipo='HIIT',cont='HIIT + técnico e tático',acum=23.0)}
NORMA={'Tensão':[4.0,3.077],'Depressão':[0.933,1.867],'Raiva':[0.761,1.522],
       'Vigor':[8.195,3.902],'Fadiga':[3.019,3.019],'Confusão':[1.425,1.781]}
for p in PARES:
    for s in SUB:
        m,sd=NORMA[s]; p['T_'+s]=(p[s]-m)/sd*10+50
DEC=[
 "Fonte: aba 'Diário - Treino' do export do formulário (base designada FONTE-VERDADE na auditoria do autor).",
 "Dia definido pelo carimbo de data/hora com fronteira às 04h00, e não pela coluna 'Data' autorreferida, "
 "que contém datas de nascimento e erros de digitação: 84 dos 457 registros seriam inutilizáveis por ela "
 "e 88 dos registros do microciclo divergem do dia obtido pelo carimbo.",
 "Microciclo D1=21/04/2024 a D7=27/04/2024; um registro de 29/04 foi excluído.",
 "O rótulo 'Não Identificado' da coluna padronizada é marcador, não atleta: dois de seus quatro registros "
 "foram recuperados por correspondência exata no dicionário de variantes e dois pelo nome curado em "
 "COLETAS.xlsx para o mesmo carimbo de data/hora, o que atribuiu todos os quatro.",
 "D1 teve janela única noturna (20h42 às 01h19 do dia seguinte), sem qualquer registro matinal.",
 "D2 a D7: primeiro registro do dia = pré; último = pós; valor diário = média dos dois. Os registros\n  intermediários são excedentes de protocolo e não entram no valor diário.",
 "O pré não exige hora da manhã: 59 dos 139 atletas-dia de D2 a D7 só responderam a partir do meio-dia,\n  sem nenhum registro anterior naquele dia, e neles o primeiro registro é o pré.",
 "D1 teve coleta única: vale a primeira resposta de cada atleta. Vinte e um dos vinte e sete atletas\n  responderam uma segunda vez, em mediana 153 minutos depois, e essas 21 respostas são repetição, não\n  segunda coleta: dos 22 atletas que respondem depois das 21h, 21 já haviam respondido na janela das\n  20h42, e o único que não respondera responde às 21h54, uma vez só.",
 "Em D7 todos os registros ocorrem entre 08h e 14h: o contraste pré/pós desse dia é manhã contra início da tarde.",
]
json.dump(dict(NORMA=NORMA, CARGA={str(k):v for k,v in CARGA.items()}, ATL=sorted(COD.values()),
               pares=PARES, prepos=PREPOS, registros=REG, nd=nd, DECISOES=DEC,
               orfaos=orf, recuperados=recup, fora_semana=fora, excedentes=EXCED),
          open(os.path.join(DADOS,"V2_base.json"),"w"), ensure_ascii=False)
print("gravado: V2_base.json")
