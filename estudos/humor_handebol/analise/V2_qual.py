# -*- coding: utf-8 -*-
"""Auditoria de qualidade e análise exploratória univariada, desde a fonte.

Lê o export original do formulário no nível do ITEM, reconstrói cada escore por
fórmula, confronta com a coluna calculada da planilha, e só então descreve cada
variável pela técnica que o seu tipo de mensuração pede.

Nenhum nome atravessa esta rotina: a codificação A01..A27 ocorre aqui dentro,
pela mesma regra de base_v2.py, de modo que os dois arquivos concordam.
"""
import os, re, json, unicodedata, datetime, collections
import numpy as np, openpyxl
from scipy import stats

RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); os.makedirs(DADOS, exist_ok=True)
UP=os.environ.get("HH_UPLOADS") or "/root/.claude/uploads/4ddb0907-77b2-5876-a286-ef4b6b886e93"
FONTE=os.path.join(UP,"ad245c30-Backup__Banco_de_dados_ORIGINAL_INTOCADO_20260723.xlsx")
D0=datetime.date(2024,4,21)

# ============================ 1. DICIONÁRIO ============================
# Cada item declara: coluna na fonte, tipo de mensuração e domínio admissível.
ITEM_BRUMS={'Apavorado':5,'Animado':6,'Confuso':7,'Esgotado':8,'Deprimido':9,'Desanimado':10,
 'Irritado':11,'Exausto':12,'Inseguro':13,'Sonolento':14,'Zangado':15,'Triste':16,'Ansioso':17,
 'Preocupado':18,'Com disposição':19,'Infeliz':20,'Desorientado':21,'Tenso':22,'Com raiva':23,
 'Com energia':24,'Cansado':25,'Mal-humorado':26,'Alerta':27,'Indeciso':28}
SUBESC={'Tensão':['Apavorado','Ansioso','Preocupado','Tenso'],
        'Depressão':['Deprimido','Desanimado','Infeliz','Triste'],
        'Raiva':['Irritado','Zangado','Com raiva','Mal-humorado'],
        'Vigor':['Animado','Com disposição','Com energia','Alerta'],
        'Fadiga':['Esgotado','Exausto','Sonolento','Cansado'],
        'Confusão':['Confuso','Inseguro','Desorientado','Indeciso']}
ITEM_EPW={'Sentado e lendo':32,'Assistindo TV':33,'Sentado em lugar público':34,
          'Andando de carro por uma hora':35,'Deitado após o almoço':36,'Carro parado no trânsito':37}
ITEM_PSS=[(f"PSS{i+1}",38+i) for i in range(14)]
PSS_INVERTIDOS={4,5,6,7,9,10,13}          # itens positivos da PSS-14
COL={'carimbo':0,'nome':1,'data_declarada':2,'sensacao_fisica':3,'sensacao_mental':4,
     'fad_fisica':29,'fad_mental':30,'tqr':31,'nome_padronizado':52,'ciclo':53,
     'p_tensao':54,'p_depressao':55,'p_raiva':56,'p_vigor':57,'p_fadiga':58,'p_confusao':59,
     'p_tmd':60,'p_fadfis':61,'p_fadmen':62,'p_epworth':63,'p_tqr':64,'p_pss':65,
     'periodo':71,'faixa_horaria':72}

DICIONARIO=[
 dict(v='atleta',            tipo='nominal',    escala='código A01–A27', dominio='27 níveis',
      origem='Nome Padronizado, codificado'),
 dict(v='dia',               tipo='ordinal',    escala='D1–D7',          dominio='1 a 7',
      origem='carimbo de data e hora, virada às 4h'),
 dict(v='tipo_estimulo',     tipo='nominal',    escala='4 níveis',       dominio='Basal, HIIT, Amistoso, Técnico/força',
      origem='planejamento do microciclo'),
 dict(v='periodo',           tipo='nominal',    escala='4 níveis',       dominio='madrugada, manhã, tarde, noite',
      origem='hora do carimbo'),
 dict(v='momento',           tipo='nominal',    escala='3 níveis',       dominio='pré, pós, único',
      origem='ordem do registro no dia'),
 dict(v='sensacao_fisica',   tipo='ordinal',    escala='Likert de 5',    dominio='Muito mal a Muito bem',
      origem='item do formulário'),
 dict(v='sensacao_mental',   tipo='ordinal',    escala='Likert de 5',    dominio='Muito mal a Muito bem',
      origem='item do formulário'),
 dict(v='item BRUMS (24)',   tipo='ordinal',    escala='Likert de 5',    dominio='0 a 4',
      origem='itens 5 a 28 do formulário'),
 dict(v='item Epworth (6)',  tipo='ordinal',    escala='Likert de 4',    dominio='0 a 3',
      origem='itens 32 a 37'),
 dict(v='item PSS (14)',     tipo='ordinal',    escala='Likert de 5',    dominio='0 a 4',
      origem='itens 38 a 51, sete deles invertidos'),
 dict(v='Tensão…Confusão',   tipo='discreta',   escala='soma de 4 itens',dominio='0 a 16',
      origem='calculada por fórmula'),
 dict(v='TMD',               tipo='discreta',   escala='composto',       dominio='−16 a 80',
      origem='calculada por fórmula'),
 dict(v='Fad.Física',        tipo='discreta',   escala='numérica direta',dominio='0 a 10',
      origem='item único'),
 dict(v='Fad.Mental',        tipo='discreta',   escala='numérica direta',dominio='0 a 10',
      origem='item único'),
 dict(v='Epworth',           tipo='discreta',   escala='soma de 6 itens',dominio='0 a 24',
      origem='calculada por fórmula'),
 dict(v='PSS',               tipo='discreta',   escala='soma de 14 itens',dominio='0 a 56',
      origem='calculada por fórmula, com inversão'),
 dict(v='TQR',               tipo='ordinal',    escala='Borg 6–20',      dominio='6 a 20',
      origem='item único'),
 dict(v='escore T',          tipo='contínua',   escala='padronizada',    dominio='real',
      origem='(x − média normativa) ÷ desvio × 10 + 50'),
 dict(v='média diária',      tipo='contínua',   escala='média de 1 a 2 registros', dominio='0 a 16',
      origem='agregação do par atleta-dia'),
 dict(v='hora decimal',      tipo='contínua',   escala='0 a 24 h',       dominio='real',
      origem='carimbo de data e hora'),
]

FORMULAS=[
 dict(id='F1', nome='Subescala do BRUMS',
      formula='S_k = Σ_{i∈k} x_i,  x_i ∈ {0,1,2,3,4},  |k| = 4  ⇒  S_k ∈ [0, 16]',
      nota='Quatro itens por subescala, sem inversão e sem peso.'),
 dict(id='F2', nome='Perturbação total do humor',
      formula='PTH = (Tensão + Depressão + Raiva + Fadiga + Confusão) − Vigor  ⇒  PTH ∈ [−16, 80]',
      nota='Sem a constante 100 que algumas versões acrescentam.'),
 dict(id='F3', nome='Escore T normativo',
      formula='T_k = (S_k − μ_k) ÷ σ_k × 10 + 50',
      nota='μ e σ das normas externas de atletas; o T tem média 50 e desvio 10 na população normativa.'),
 dict(id='F4', nome='Sonolência de Epworth',
      formula='E = Σ_{j=1}^{6} y_j,  y_j ∈ {0,1,2,3}  ⇒  E ∈ [0, 18] nesta aplicação de 6 itens',
      nota='A escala clássica tem 8 situações e vai a 24; o formulário aplicou 6.'),
 dict(id='F5', nome='Estresse percebido (PSS-14)',
      formula='PSS = Σ_{i∉R} z_i + Σ_{i∈R} (4 − z_i),  R = {4,5,6,7,9,10,13}  ⇒  PSS ∈ [0, 56]',
      nota='Sete itens positivos entram invertidos.'),
 dict(id='F6', nome='Cerca de Tukey',
      formula='Q1 − 1,5·IQR  e  Q3 + 1,5·IQR (moderado);  ±3,0·IQR (extremo),  IQR = Q3 − Q1',
      nota='Não pressupõe normalidade.'),
 dict(id='F7', nome='Escore z',
      formula='z = (x − x̄) ÷ s;  |z| > 3 sinaliza discrepância',
      nota='A própria média e o próprio desvio são arrastados pelo valor discrepante.'),
 dict(id='F8', nome='Escore z modificado',
      formula='z_M = 0,6745 · (x − Md) ÷ MAD,  MAD = Md(|x − Md|);  |z_M| > 3,5 sinaliza discrepância',
      nota='Robusto: mediana e MAD não são arrastados. A constante 0,6745 iguala o MAD ao desvio sob normalidade.'),
 dict(id='F9', nome='Coeficiente de variação',
      formula='CV = s ÷ x̄ × 100',
      nota='Comparável entre escalas de amplitudes diferentes.'),
 dict(id='F10', nome='Assimetria e curtose',
      formula='g₁ = m₃ ÷ m₂^{3/2},  g₂ = m₄ ÷ m₂² − 3,  m_r = (1/n)·Σ(x − x̄)^r',
      nota='Curtose em excesso: 0 na normal.'),
 dict(id='F11', nome='Regra de Freedman-Diaconis',
      formula='h = 2 · IQR · n^{−1/3};  k = ⌈(máx − mín) ÷ h⌉',
      nota='Largura de classe do histograma; robusta a caudas pesadas.'),
 dict(id='F12', nome='Regra de Sturges',
      formula='k = ⌈log₂(n) + 1⌉',
      nota='Só aceitável com distribuição próxima da normal e n moderado.'),
 dict(id='F13', nome='Entropia de Shannon normalizada',
      formula='H* = −Σ p_i·log₂(p_i) ÷ log₂(m)',
      nota='Mede o equilíbrio de uma categórica de m níveis: 1 é uniforme, 0 é degenerada.'),
 dict(id='F14', nome='Completude',
      formula='C = (1 − faltantes ÷ total) × 100',
      nota='Calculada por variável, por atleta e por dia.'),
]

# ============================ 2. LEITURA ============================
def chave(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode()
    return re.sub(r'[^a-z ]','',re.sub(r'\s+',' ',s).strip().lower())
def lik(v):
    """Extrai o código numérico de um rótulo Likert do formulário."""
    if v is None: return None
    if isinstance(v,(int,float)): return float(v)
    m=re.match(r'\s*(-?\d+)',str(v)); return float(m.group(1)) if m else None
def dia_de(ts):
    d=ts.date() if ts.hour>=4 else ts.date()-datetime.timedelta(days=1)
    i=(d-D0).days+1
    return i if 1<=i<=7 else None

wb=openpyxl.load_workbook(FONTE, read_only=True, data_only=True)
ws=wb['Diário - Treino']
BRUTO=list(ws.iter_rows(values_only=True))
CAB=list(BRUTO[0]); LIN=BRUTO[1:]
dicw={}
for r in wb['Dicionário Atletas'].iter_rows(values_only=True):
    if r[6] and r[7] and str(r[6])!='Nome como digitado (variante)': dicw[chave(r[6])]=chave(r[7])
wb.close()
wb2=openpyxl.load_workbook(os.path.join(UP,"bc6d935b-COLETAS.xlsx"), read_only=True, data_only=True)
CURADO={t.isoformat():chave(r[1]) for r in wb2['Diario'].iter_rows(values_only=True)
        for t in [r[0]] if isinstance(t,datetime.datetime) and r[1]}
wb2.close()

pad=collections.Counter(chave(r[COL['nome_padronizado']]) for r in LIN if r[COL['nome_padronizado']])
NAOID={k for k in pad if k.startswith('nao ident')}
COD={k:f"A{i+1:02d}" for i,k in enumerate(sorted(k for k in pad if k not in NAOID))}
print(f"fonte: {len(LIN)} linhas, {len(CAB)} colunas · elenco codificado: {len(COD)} atletas")

# ============================ 3. RECONSTRUÇÃO POR FÓRMULA ============================
REG=[]; ORF=[]; FORA=0
for i,r in enumerate(LIN, start=2):
    ts=r[COL['carimbo']]
    if isinstance(ts,str): ts=datetime.datetime.fromisoformat(ts)
    if not isinstance(ts,datetime.datetime): continue
    d=dia_de(ts)
    k=chave(r[COL['nome_padronizado']])
    if k in NAOID:
        alvo=dicw.get(chave(r[COL['nome']])) or CURADO.get(ts.isoformat())
        if alvo in COD: k=alvo
        else: ORF.append(dict(linha=i, carimbo=ts.isoformat())); k=None
    if d is None: FORA+=1
    it={n:lik(r[c]) for n,c in ITEM_BRUMS.items()}
    ep={n:lik(r[c]) for n,c in ITEM_EPW.items()}
    ps={n:lik(r[c]) for n,c in ITEM_PSS}
    calc={}
    for s,itens in SUBESC.items():
        vs=[it[n] for n in itens]
        calc[s]=float(sum(vs)) if all(v is not None for v in vs) else None
    calc['TMD']=(sum(calc[s] for s in ['Tensão','Depressão','Raiva','Fadiga','Confusão'])-calc['Vigor']
                 if all(calc[s] is not None for s in SUBESC) else None)
    vs=list(ep.values()); calc['Epworth']=float(sum(vs)) if all(v is not None for v in vs) else None
    vp=[ps[n] for n,_ in ITEM_PSS]
    calc['PSS']=(float(sum((4-v) if (j+1) in PSS_INVERTIDOS else v for j,v in enumerate(vp)))
                 if all(v is not None for v in vp) else None)
    plan={'Tensão':lik(r[COL['p_tensao']]),'Depressão':lik(r[COL['p_depressao']]),
          'Raiva':lik(r[COL['p_raiva']]),'Vigor':lik(r[COL['p_vigor']]),
          'Fadiga':lik(r[COL['p_fadiga']]),'Confusão':lik(r[COL['p_confusao']]),
          'TMD':lik(r[COL['p_tmd']]),'Epworth':lik(r[COL['p_epworth']]),'PSS':lik(r[COL['p_pss']])}
    REG.append(dict(linha=i, atleta=(COD.get(k) if k else None), dia=d,
        carimbo=ts.isoformat(), hora=ts.hour+ts.minute/60,
        itens=it, epw=ep, pss=ps, calc=calc, plan=plan,
        fad_fisica=lik(r[COL['fad_fisica']]), fad_mental=lik(r[COL['fad_mental']]),
        tqr=lik(r[COL['tqr']]), tqr_plan=lik(r[COL['p_tqr']]), tqr_bruto=r[COL['tqr']],
        sensacao_fisica=r[COL['sensacao_fisica']], sensacao_mental=r[COL['sensacao_mental']],
        nome_livre=r[COL['nome']], nome_pad=r[COL['nome_padronizado']], ciclo=r[COL['ciclo']],
        periodo=r[COL['periodo']], faixa=r[COL['faixa_horaria']],
        data_declarada=(r[COL['data_declarada']].date().isoformat()
                        if isinstance(r[COL['data_declarada']],datetime.datetime) else None)))

# ---- confronto entre a coluna calculada da planilha e a fórmula ----
CONFRONTO=[]
for v in ['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','TMD','Epworth','PSS']:
    par=[(x['calc'][v], x['plan'][v], x['linha']) for x in REG
         if x['calc'].get(v) is not None and x['plan'].get(v) is not None]
    dif=[(l,c,p) for c,p,l in par if abs(c-p)>1e-9]
    d=[abs(c-p) for c,p,_ in par]
    CONFRONTO.append(dict(variavel=v, n_comparado=len(par), n_divergente=len(dif),
        pct=100*len(dif)/max(len(par),1), max_dif=float(max(d)) if d else 0.0,
        exemplos=[dict(linha=l, formula=c, planilha=p) for l,c,p in dif[:6]]))
print("\n=== CONFRONTO: fórmula reconstruída × coluna calculada da planilha ===")
for c in CONFRONTO:
    print(f"  {c['variavel']:<10} n={c['n_comparado']:>3}  divergentes={c['n_divergente']:>3} "
          f"({c['pct']:.1f}%)  maior diferença={c['max_dif']:.0f}")
    for e in c['exemplos'][:3]:
        print(f"       linha {e['linha']}: fórmula {e['formula']:.0f} × planilha {e['planilha']:.0f}")

# ============================ 4. FALTANTES ============================
def compl(n_falta, n_tot): return 100*(1-n_falta/n_tot) if n_tot else 0.0
BLOCOS={'itens do BRUMS (24)':[('itens',n) for n in ITEM_BRUMS],
        'itens de Epworth (6)':[('epw',n) for n in ITEM_EPW],
        'itens da PSS (14)':[('pss',n) for n,_ in ITEM_PSS]}
FALTA_ITEM=[]
for bloco,chaves in BLOCOS.items():
    for grupo,nome in chaves:
        f=sum(1 for x in REG if x[grupo][nome] is None)
        FALTA_ITEM.append(dict(bloco=bloco, item=nome, faltantes=f, n=len(REG),
                               completude=compl(f,len(REG))))
FALTA_VAR=[]
for nome,acesso in [('Fadiga física',lambda x:x['fad_fisica']),('Fadiga mental',lambda x:x['fad_mental']),
                    ('TQR',lambda x:x['tqr']),('Sensação física',lambda x:x['sensacao_fisica']),
                    ('Sensação mental',lambda x:x['sensacao_mental']),
                    ('Data declarada',lambda x:x['data_declarada']),
                    ('Nome padronizado',lambda x:x['nome_pad'])]:
    f=sum(1 for x in REG if acesso(x) in (None,''))
    FALTA_VAR.append(dict(bloco='variável isolada', item=nome, faltantes=f, n=len(REG),
                          completude=compl(f,len(REG))))
for v in ['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','TMD','Epworth','PSS']:
    f=sum(1 for x in REG if x['calc'][v] is None)
    FALTA_VAR.append(dict(bloco='escore calculado', item=v, faltantes=f, n=len(REG),
                          completude=compl(f,len(REG))))

# falta por desenho × falta incidental, na grade atleta × dia
DENTRO=[x for x in REG if x['dia'] is not None and x['atleta']]
grade=collections.defaultdict(list)
for x in DENTRO: grade[(x['atleta'],x['dia'])].append(x)
ATLS=sorted(COD.values())
esperado_por_dia={1:1, **{d:2 for d in range(2,8)}}   # D1 teve janela única
GRADE=[]
for d in range(1,8):
    obs=sum(1 for a in ATLS if (a,d) in grade)
    reg=sum(len(grade[(a,d)]) for a in ATLS if (a,d) in grade)
    esp=len(ATLS)*esperado_por_dia[d]
    GRADE.append(dict(dia=d, atletas_com_registro=obs, atletas_esperados=len(ATLS),
                      registros=reg, registros_esperados=esp,
                      cobertura_atleta=100*obs/len(ATLS), cobertura_registro=100*reg/esp))
FALTA_ATLETA=[]
for a in ATLS:
    dias=sum(1 for d in range(1,8) if (a,d) in grade)
    regs=sum(len(grade[(a,d)]) for d in range(1,8) if (a,d) in grade)
    FALTA_ATLETA.append(dict(atleta=a, dias_com_registro=dias, registros=regs,
                             completude_dias=100*dias/7))
FALTA_ATLETA.sort(key=lambda x:x['dias_com_registro'])
print("\n=== FALTANTES ===")
print(f"  itens do instrumento: {sum(f['faltantes'] for f in FALTA_ITEM)} células ausentes em "
      f"{len(FALTA_ITEM)}×{len(REG)} = {len(FALTA_ITEM)*len(REG)} — completude "
      f"{compl(sum(f['faltantes'] for f in FALTA_ITEM), len(FALTA_ITEM)*len(REG)):.2f}%")
for f in FALTA_VAR:
    if f['faltantes']: print(f"  {f['item']:<18} {f['faltantes']:>3} faltantes ({f['completude']:.1f}% completo)")
print("  cobertura na grade atleta × dia:")
for g in GRADE:
    print(f"    D{g['dia']}  atletas {g['atletas_com_registro']:>2}/{g['atletas_esperados']} "
          f"({g['cobertura_atleta']:.0f}%)  registros {g['registros']:>3}/{g['registros_esperados']} "
          f"({g['cobertura_registro']:.0f}%)")

# ---- registros repetidos no mesmo dia: quantos, com que intervalo, e quão parecidos ----
def vetor(x): return [x['itens'][n] for n in ITEM_BRUMS]
REPET=collections.Counter(); INTERV=[]; DUPL=[]
for (a,d),g in grade.items():
    g=sorted(g,key=lambda x:x['carimbo']); REPET[len(g)]+=1
    for u,w in zip(g,g[1:]):
        t1=datetime.datetime.fromisoformat(u['carimbo']); t2=datetime.datetime.fromisoformat(w['carimbo'])
        dt=(t2-t1).total_seconds()/60
        vu,vw=vetor(u),vetor(w)
        ig=sum(1 for p,q in zip(vu,vw) if p==q)
        INTERV.append(dict(atleta=a, dia=d, minutos=dt, itens_iguais=ig,
                           identico=bool(ig==24), delta_pth=(w['calc']['TMD']-u['calc']['TMD'])))
        if dt<=30:
            DUPL.append(dict(atleta=a, dia=d, minutos=round(dt,1), itens_iguais=ig,
                             identico=bool(ig==24), linha_a=u['linha'], linha_b=w['linha'],
                             pth_a=u['calc']['TMD'], pth_b=w['calc']['TMD']))
mins=np.array([i['minutos'] for i in INTERV])
REPETICAO=dict(
  distribuicao={str(k):int(v) for k,v in sorted(REPET.items())},
  pares_consecutivos=len(INTERV),
  intervalo=dict(mediana=float(np.median(mins)), q1=float(np.percentile(mins,25)),
                 q3=float(np.percentile(mins,75)), minimo=float(mins.min()), maximo=float(mins.max())),
  ate_30min=len(DUPL),
  identicos=sum(1 for i in INTERV if i['identico']),
  identicos_ate_30min=sum(1 for d in DUPL if d['identico']),
  exemplos=sorted(DUPL,key=lambda d:d['minutos'])[:10])
print("\n=== REGISTROS REPETIDOS NO MESMO DIA ===")
print("  registros por par atleta-dia: " +
      " · ".join(f"{k} registro{'s' if int(k)>1 else ''}: {v}" for k,v in REPETICAO['distribuicao'].items()))
q=REPETICAO['intervalo']
print(f"  intervalo entre registros consecutivos: mediana {q['mediana']:.0f} min "
      f"(Q1 {q['q1']:.0f}; Q3 {q['q3']:.0f}; amplitude {q['minimo']:.0f} a {q['maximo']:.0f})")
print(f"  pares com intervalo ≤ 30 min: {REPETICAO['ate_30min']} de {len(INTERV)} "
      f"({100*REPETICAO['ate_30min']/len(INTERV):.1f}%)  ·  vetor de 24 itens idêntico: "
      f"{REPETICAO['identicos']} pares ({REPETICAO['identicos_ate_30min']} deles em ≤ 30 min)")
for e in REPETICAO['exemplos'][:5]:
    print(f"    {e['atleta']} D{e['dia']}  {e['minutos']:>5.1f} min  itens iguais {e['itens_iguais']}/24  "
          f"PTH {e['pth_a']:.0f} → {e['pth_b']:.0f}   linhas {e['linha_a']} e {e['linha_b']}")

# ============================ 5. PADRONIZAÇÃO DE CATEGÓRICAS ============================
def canon(s):
    """Chave canônica que PRESERVA dígitos: sem acento, sem caixa, sem espaço extra."""
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode()
    return re.sub(r'[^a-z0-9 ]','',re.sub(r'\s+',' ',s).strip().lower())
def variantes(valores, ch=canon):
    """Agrupa por chave canônica: níveis com mais de uma grafia precisam de padronização."""
    g=collections.defaultdict(collections.Counter)
    for v in valores:
        if v in (None,''): continue
        g[ch(v)][str(v)]+=1
    return g
CATEG=[]
for nome, acesso in [('Nome (texto livre)',lambda x:x['nome_livre']),
                     ('Nome padronizado',lambda x:x['nome_pad']),
                     ('Ciclo',lambda x:x['ciclo']),
                     ('Sensação física',lambda x:x['sensacao_fisica']),
                     ('Sensação mental',lambda x:x['sensacao_mental']),
                     ('Período do dia',lambda x:x['periodo']),
                     ('Faixa horária',lambda x:x['faixa']),
                     ('TQR (rótulo)',lambda x:x['tqr_bruto'])]:
    vals=[acesso(x) for x in REG]
    g=variantes(vals, ch=(chave if nome.startswith('Nome') else canon))
    grafias=sum(len(c) for c in g.values())
    plural={k:dict(c) for k,c in g.items() if len(c)>1}
    faltantes=sum(1 for v in vals if v in (None,''))
    CATEG.append(dict(variavel=nome, n=len(vals)-faltantes, faltantes=faltantes,
                      niveis_canonicos=len(g), grafias=grafias,
                      niveis_com_variante=len(plural), variantes=plural,
                      frequencia={k:int(sum(c.values())) for k,c in
                                  sorted(g.items(), key=lambda kv:-sum(kv[1].values()))}))
print("\n=== PADRONIZAÇÃO DE VARIÁVEIS CATEGÓRICAS ===")
for c in CATEG:
    marca=" ← precisa de padronização" if c['niveis_com_variante'] else ""
    print(f"  {c['variavel']:<22} {c['niveis_canonicos']:>3} níveis canônicos, "
          f"{c['grafias']:>3} grafias, {c['niveis_com_variante']:>2} com variante{marca}")
    for k,v in list(c['variantes'].items())[:3]:
        print(f"       «{k}» aparece como: " + " · ".join(f"{g} ({n})" for g,n in v.items()))

# tabela de frequência das nominais e ordinais canônicas do estudo
def freq_tabela(valores, ordem=None, rotulo=None):
    c=collections.Counter(v for v in valores if v is not None)
    chaves=list(ordem) if ordem else [k for k,_ in c.most_common()]
    imprevistos={k:v for k,v in c.items() if k not in chaves}
    chaves+= sorted(imprevistos, key=lambda k:-imprevistos[k])
    n=sum(c.values()); acc=0; linhas=[]
    for k in chaves:
        f=c.get(k,0); acc+=f
        linhas.append(dict(nivel=(rotulo(k) if rotulo else str(k)), f=f, pct=100*f/n if n else 0,
                           f_acum=acc, pct_acum=100*acc/n if n else 0))
    p=np.array([l['f'] for l in linhas],float); p=p[p>0]/n
    H=float(-(p*np.log2(p)).sum()/np.log2(len(chaves))) if len(chaves)>1 else 0.0
    return dict(n=n, linhas=linhas, entropia_normalizada=H,
                imprevistos={str(k):int(v) for k,v in imprevistos.items()},
                moda=max(linhas,key=lambda l:l['f'])['nivel'] if linhas else None)
LIK5=['Péssimo','Ruim','Regular','Bem','Muito bem']
FREQ={
 'Estímulo do dia': freq_tabela([{1:'Basal',2:'HIIT',3:'Amistoso',4:'HIIT',5:'Amistoso',
                                  6:'Técnico/força',7:'HIIT'}[x['dia']] for x in DENTRO],
                                 ordem=['Basal','HIIT','Amistoso','Técnico/força']),
 'Período do dia': freq_tabela([x['periodo'] for x in DENTRO],
                                ordem=['Manhã (05h-11h)','Tarde (12h-17h)','Noite (18h-04h)']),
 'Dia do microciclo': freq_tabela([f"D{x['dia']}" for x in DENTRO], ordem=[f"D{d}" for d in range(1,8)]),
 'Sensação física': freq_tabela([x['sensacao_fisica'] for x in DENTRO], ordem=LIK5),
 'Sensação mental': freq_tabela([x['sensacao_mental'] for x in DENTRO], ordem=LIK5),
}
print("\n=== TABELAS DE FREQUÊNCIA ===")
for nome,t in FREQ.items():
    print(f"\n  {nome}  (n = {t['n']}, moda «{t['moda']}», entropia normalizada {t['entropia_normalizada']:.3f})")
    print("    nível                     f      %     f acum   % acum")
    for l in t['linhas']:
        print(f"    {l['nivel']:<22} {l['f']:>4}  {l['pct']:>5.1f}   {l['f_acum']:>5}   {l['pct_acum']:>5.1f}")
    if t['imprevistos']: print(f"    ATENÇÃO: níveis fora da ordem declarada — {t['imprevistos']}")

# a TQR é escala de Borg com âncoras verbais em pontos alternados: rótulo e número puro
# são o mesmo nível, não duas grafias do mesmo nível.
tqr_rot=collections.Counter()
for x in REG:
    if x['tqr'] is not None:
        tqr_rot[int(x['tqr'])] = tqr_rot.get(int(x['tqr']),0)
TQR_ANCORA=sorted({int(x['tqr']):(str(x['tqr_bruto']).strip() if not str(x['tqr_bruto']).strip().isdigit() else '—')
                   for x in REG if x['tqr'] is not None}.items())
dif_tqr=[x['linha'] for x in REG if x['tqr'] is not None and x['tqr_plan'] is not None
         and abs(x['tqr']-x['tqr_plan'])>1e-9]
print(f"\n  TQR: {len(TQR_ANCORA)} pontos observados na escala de Borg 6–20; "
      f"{sum(1 for _,a in TQR_ANCORA if a!='—')} com âncora verbal e "
      f"{sum(1 for _,a in TQR_ANCORA if a=='—')} sem — desenho da escala, não falha de padronização. "
      f"Divergência com a coluna calculada: {len(dif_tqr)} linhas.")

# ============================ 6. UNIVARIADA E OUTLIERS ============================
def descreve(x, nome, tipo, minimo=None, maximo=None):
    x=np.asarray([v for v in x if v is not None], float); n=len(x)
    q1,md,q3=np.percentile(x,[25,50,75]); iqr=q3-q1
    m=float(x.mean()); s=float(x.std(ddof=1))
    mad=float(np.median(np.abs(x-md)))
    lo15,hi15=q1-1.5*iqr, q3+1.5*iqr
    lo30,hi30=q1-3.0*iqr, q3+3.0*iqr
    z=(x-m)/s if s>0 else np.zeros_like(x)
    zm=0.6745*(x-md)/mad if mad>0 else None
    W,pW=stats.shapiro(x) if 3<=n<=5000 else (np.nan,np.nan)
    h_fd=2*iqr*n**(-1/3)
    d=dict(variavel=nome, tipo=tipo, n=n,
        minimo=float(x.min()), maximo=float(x.max()),
        media=m, desvio=s, erro_padrao=float(s/np.sqrt(n)), cv=float(100*s/m) if m else None,
        mediana=float(md), q1=float(q1), q3=float(q3), iqr=float(iqr), amplitude=float(x.max()-x.min()),
        p5=float(np.percentile(x,5)), p95=float(np.percentile(x,95)), mad=mad,
        assimetria=float(stats.skew(x)), curtose=float(stats.kurtosis(x)),
        shapiro_W=float(W), shapiro_p=float(pW),
        tukey_moderado=[float(lo15),float(hi15)], tukey_extremo=[float(lo30),float(hi30)],
        n_tukey_moderado=int(((x<lo15)|(x>hi15)).sum()), n_tukey_extremo=int(((x<lo30)|(x>hi30)).sum()),
        n_z3=int((np.abs(z)>3).sum()),
        n_zmod=(int((np.abs(zm)>3.5).sum()) if zm is not None else None),
        mad_nulo=bool(mad==0), iqr_nulo=bool(iqr==0),
        pct_no_piso=float(100*(x==x.min()).mean()),
        h_freedman_diaconis=float(h_fd),
        k_fd=int(np.ceil((x.max()-x.min())/h_fd)) if h_fd>0 else None,
        k_sturges=int(np.ceil(np.log2(n)+1)))
    if minimo is not None:
        d['fora_do_dominio']=int(((x<minimo)|(x>maximo)).sum()); d['dominio']=[minimo,maximo]
    return d

VARS_NUM=[('Tensão','discreta',0,16),('Depressão','discreta',0,16),('Raiva','discreta',0,16),
          ('Vigor','discreta',0,16),('Fadiga','discreta',0,16),('Confusão','discreta',0,16),
          ('TMD','discreta',-16,80),('Epworth','discreta',0,18),('PSS','discreta',0,56)]
UNI=[]
for v,tp,mn,mx in VARS_NUM:
    UNI.append(descreve([x['calc'][v] for x in DENTRO], v, tp, mn, mx))
UNI.append(descreve([x['fad_fisica'] for x in DENTRO],'Fad.Física','discreta',0,10))
UNI.append(descreve([x['fad_mental'] for x in DENTRO],'Fad.Mental','discreta',0,10))
UNI.append(descreve([x['tqr'] for x in DENTRO],'TQR','ordinal',6,20))
UNI.append(descreve([x['hora'] for x in DENTRO],'Hora do registro','contínua',0,24))
# escore T: contínua por construção
NORMA={'Tensão':[4.0,3.077],'Depressão':[0.933,1.867],'Raiva':[0.761,1.522],
       'Vigor':[8.195,3.902],'Fadiga':[3.019,3.019],'Confusão':[1.425,1.781]}
for v,(mu,sg) in NORMA.items():
    UNI.append(descreve([(x['calc'][v]-mu)/sg*10+50 for x in DENTRO], f'T de {v}', 'contínua'))

print("\n=== UNIVARIADA DAS NUMÉRICAS (nível de registro, n = %d) ===" % len(DENTRO))
print(f"  {'variável':<16} {'tipo':<9} {'mín':>5} {'Q1':>5} {'Md':>5} {'Q3':>5} {'máx':>6} "
      f"{'média':>7} {'dp':>6} {'CV%':>6} {'assim':>6} {'curt':>6} {'Shapiro p':>10}")
for d in UNI:
    print(f"  {d['variavel']:<16} {d['tipo']:<9} {d['minimo']:>5.1f} {d['q1']:>5.1f} {d['mediana']:>5.1f} "
          f"{d['q3']:>5.1f} {d['maximo']:>6.1f} {d['media']:>7.2f} {d['desvio']:>6.2f} "
          f"{(d['cv'] if d['cv'] is not None else float('nan')):>6.1f} {d['assimetria']:>6.2f} "
          f"{d['curtose']:>6.2f} {d['shapiro_p']:>10.4f}")
print("\n  discrepantes por três critérios, e nenhum valor fora do domínio admissível:")
print(f"  {'variável':<16} {'Tukey 1,5':>10} {'Tukey 3,0':>10} {'|z|>3':>7} {'|z_M|>3,5':>10} {'fora domínio':>13}")
for d in UNI:
    print(f"  {d['variavel']:<16} {d['n_tukey_moderado']:>10} {d['n_tukey_extremo']:>10} "
          f"{d['n_z3']:>7} {(str(d['n_zmod']) if d['n_zmod'] is not None else 'MAD=0'):>10} "
          f"{str(d.get('fora_do_dominio','—')):>13}"
          + ("   ← IQR = 0: cerca de Tukey inaplicável" if d['iqr_nulo'] else ""))

# ---- discrepantes intraindividuais: o atleta contra a própria série ----
INTRA=[]
for v,_,_,_ in VARS_NUM:
    por_a=collections.defaultdict(list)
    for x in DENTRO:
        if x['calc'][v] is not None: por_a[x['atleta']].append((x['dia'], x['calc'][v], x['linha']))
    achados=[]
    for a,serie in por_a.items():
        if len(serie)<4: continue
        y=np.array([t[1] for t in serie],float)
        md=np.median(y); mad=np.median(np.abs(y-md))
        if mad==0: continue
        zm=0.6745*(y-md)/mad
        for (d,val,ln),zz in zip(serie,zm):
            if abs(zz)>3.5:
                achados.append(dict(atleta=a, dia=d, valor=float(val), z_mod=float(zz),
                                    mediana_do_atleta=float(md), linha=ln))
    INTRA.append(dict(variavel=v, atletas_avaliados=sum(1 for s in por_a.values() if len(s)>=4),
                      n_discrepantes=len(achados),
                      casos=sorted(achados,key=lambda c:-abs(c['z_mod']))[:6]))
print("\n=== DISCREPANTES INTRAINDIVIDUAIS (z modificado > 3,5 dentro da própria série) ===")
for i in INTRA:
    print(f"  {i['variavel']:<10} {i['n_discrepantes']:>3} casos em {i['atletas_avaliados']} atletas com 4 ou mais dias")
    for c in i['casos'][:2]:
        print(f"       {c['atleta']} D{c['dia']}: {c['valor']:.0f} contra mediana própria "
              f"{c['mediana_do_atleta']:.0f}  (z_M = {c['z_mod']:+.1f}, linha {c['linha']})")

# ============================ 7. INCONSISTÊNCIAS DECLARADAS ============================
INCONS=[]
dd=[x for x in DENTRO if x['data_declarada']]
erro_data=[x for x in dd if x['data_declarada']!=(D0+datetime.timedelta(days=x['dia']-1)).isoformat()]
INCONS.append(dict(id='Q1', gravidade='alta', titulo='Coluna «Data» autorreferida diverge do carimbo',
  achado=f"{len(erro_data)} de {len(dd)} registros com data declarada divergem do dia obtido pelo carimbo; "
         f"o conjunto inclui datas de nascimento.",
  correcao='O dia passa a ser derivado exclusivamente do carimbo de data e hora, com virada às 4h.',
  n=len(erro_data), de=len(dd)))
INCONS.append(dict(id='Q2', gravidade='alta', titulo='Nome em texto livre sem padronização',
  achado=f"{CATEG[0]['grafias']} grafias distintas para {CATEG[0]['niveis_canonicos']} nomes canônicos, "
         f"{CATEG[0]['niveis_com_variante']} deles com mais de uma grafia.",
  correcao='A identidade passa a vir da coluna padronizada, e a codificação A01–A27 é feita na importação.',
  n=CATEG[0]['niveis_com_variante'], de=CATEG[0]['niveis_canonicos']))
INCONS.append(dict(id='Q3', gravidade='alta', titulo='Registros excedentes ao protocolo de coleta',
  achado="O protocolo previa uma coleta em D1 e duas de D2 a D7; a distribuição observada vai de 1 a 6 "
         f"registros por par atleta-dia, e {REPETICAO['ate_30min']} pares consecutivos ocorrem em 30 minutos "
         "ou menos. A conferência pelo carimbo (V2_proto) mostra de 7 a 10 janelas de coleta do elenco por "
         "dia, e não duas.",
  correcao='De D2 a D7 valem o primeiro registro do dia (pré) e o último (pós); os registros '
           'intermediários deixam de compor o valor diário. O pré não exige hora da manhã, porque 59 dos '
           '139 atletas-dia só responderam a partir do meio-dia, sem registro anterior naquele dia. Em D1, '
           'de coleta única, vale a primeira resposta de cada atleta: as 21 respostas tardias são '
           'repetição, e não segunda coleta, pois 21 dos 22 atletas da janela tardia já haviam respondido '
           'às 20h42. Ao todo, 285 dos 456 registros compõem os valores diários.',
  n=sum(v for k,v in REPETICAO['distribuicao'].items() if int(k)>2), de=len(grade)))
INCONS.append(dict(id='Q4', gravidade='média', titulo='Rótulo do domínio da sonolência de Epworth',
  achado='A coluna da planilha é rotulada «Epworth Total (0-24)», mas o formulário aplicou seis das oito '
         'situações da escala, de modo que o máximo possível é 18. O máximo observado é '
         f"{[u for u in UNI if u['variavel']=='Epworth'][0]['maximo']:.0f}.",
  correcao='O domínio declarado passa a 0 a 18, e o texto passa a dizer que é uma aplicação de seis itens.',
  n=6, de=8))
conf=[c for c in CONFRONTO if c['n_divergente']]
INCONS.append(dict(id='Q5', gravidade='nenhuma', titulo='Escores calculados da planilha',
  achado=f"As nove colunas calculadas foram reconstruídas por fórmula a partir dos itens em "
         f"{sum(c['n_comparado'] for c in CONFRONTO)} conferências, com "
         f"{sum(c['n_divergente'] for c in CONFRONTO)} divergências.",
  correcao='Nada a corrigir. A pontuação da planilha está correta, e as divergências entre versões do '
           'manuscrito não vêm do escore.',
  n=sum(c['n_divergente'] for c in CONFRONTO), de=sum(c['n_comparado'] for c in CONFRONTO)))
degen=[u['variavel'] for u in UNI if u['iqr_nulo']]
INCONS.append(dict(id='Q6', gravidade='método', titulo='Cerca de Tukey inaplicável a subescala com piso',
  achado=f"Em {', '.join(degen)} o intervalo interquartil é zero, de modo que a cerca de Tukey classifica "
         "como discrepante todo valor diferente do piso. O z modificado também falha, porque o desvio "
         "absoluto mediano é zero.",
  correcao='Nessas subescalas a triagem passa a ser feita pelo domínio admissível e pela comparação '
           'intraindividual, e não por regra de dispersão.',
  n=len(degen), de=len(UNI)))
print("\n=== INCONSISTÊNCIAS ===")
for i in INCONS:
    print(f"  {i['id']} · {i['gravidade'].upper():<8} {i['titulo']}\n      {i['achado']}\n      → {i['correcao']}")

json.dump(dict(DICIONARIO=DICIONARIO, FORMULAS=FORMULAS, CONFRONTO=CONFRONTO,
               FALTA_ITEM=FALTA_ITEM, FALTA_VAR=FALTA_VAR, GRADE=GRADE, FALTA_ATLETA=FALTA_ATLETA,
               REPETICAO=REPETICAO, CATEG=CATEG, FREQ=FREQ, UNI=UNI, INTRA=INTRA, INCONS=INCONS,
               n_linhas_fonte=len(LIN), n_registros=len(REG), n_no_microciclo=len(DENTRO),
               orfaos=ORF, fora_semana=FORA, tqr_ancoras=TQR_ANCORA),
          open(os.path.join(DADOS,"V2_qual.json"),"w"), ensure_ascii=False, indent=1)
print(f"\n→ {os.path.join(DADOS,'V2_qual.json')}")
