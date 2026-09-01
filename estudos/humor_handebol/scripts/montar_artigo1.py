# -*- coding: utf-8 -*-
import os, sys
_B=os.path.join(os.path.dirname(os.path.abspath(__file__)),"_docx_base.py")
exec(open(_B).read())
import A1T as A
import numpy as np
def jd(n): return json.load(open(os.path.join(DADOS,n+".json"),encoding='utf-8'))
B=jd("V2_base"); Q=jd("V2_perfis"); A1=jd("V2_a1"); A2=jd("V2_a2"); A3=jd("V2_a3"); AU=jd("V2_audit")
QA=jd("V2_qual"); CO=jd("V2_conf"); UNIQ={u["variavel"]:u for u in QA["UNI"]}
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V7=SUB+['TMD']
LB={'TMD':'PTH'}
def L(k): return LB.get(k,k)
NORMA=B['NORMA']; PERF=Q['NOMES']
def n_(x,d=2):
    if x is None or (isinstance(x,float) and x!=x): return "—"
    return f"{x:.{d}f}".replace('.',',').replace('-','−')
def pf_(p,d=3):
    if p is None or (isinstance(p,float) and p!=p): return "—"
    return "< 0,001" if p<0.001 else f"{p:.{d}f}".replace('.',',')
def Tv(k,x):
    m,s=NORMA[k]; return (x-m)/s*10+50

para(A.TITULO, indent=False, bold=True, size=14, align=WD_ALIGN_PARAGRAPH.CENTER, after=6, spacing=1.15)
para(A.SUB, indent=False, italic=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER, after=18, spacing=1.15)
head("RESUMO"); para(A.RESUMO, indent=False, size=11, spacing=1.0, after=6)
para("Palavras-chave: "+A.PALAVRAS, indent=False, size=11, spacing=1.0, after=12)
head("ABSTRACT"); para(A.ABSTRACT, indent=False, size=11, italic=True, spacing=1.0, after=6)
para("Keywords: "+A.KEYWORDS, indent=False, size=11, italic=True, spacing=1.0, after=6)

head("1 INTRODUÇÃO")
for p in A.INTRO: para(p)

head("2 MÉTODO")
for i,(sub,ps) in enumerate(A.METODO):
    head(f"2.{i+1} {sub}", lvl=2)
    for p in ps: para(p)
    if i==2:
        figura(f"{S}/F1fig.png",1,"Desenho do microciclo, janelas observadas de coleta e cadeia de "
               "processamento das séries.",w=16.0)
    if i==3:
        figura(f"{S}/F2fig.png",2,"As quatro unidades de análise que circulavam nas versões anteriores e o "
               "efeito de cada uma sobre a variação do perfil iceberg entre o primeiro e o sétimo dia.",w=16.0)
        caption("Quadro 1 – Achados da auditoria de procedência e respectivas correções")
        mktable(["","Achado","Correção adotada","Gravidade"],
                [[a['id'], a['achado'], a['correcao'], a['gravidade']] for a in AU['ACHADOS']],
                widths=[1.0,6.2,6.2,1.8], fs=8)
        src(nota="a base corrigida, os roteiros e todos os resultados intermediários estão reunidos em uma "
                 "base única consultável, descrita no material suplementar.")

head("3 RESULTADOS")
head("3.1 Descrição das sete variáveis", lvl=2)
para(A.R1[0])
caption("Tabela 1 – Descrição robusta das sete variáveis nos 166 pares atleta-dia")
mktable(["Variável","Média (DP)","IC 95%","Mediana [Q1–Q3]","IC 95% da mediana","Aparada 20%","MAD","Mín–Máx","CV (%)"],
  [[L(v), f"{n_(d['m'])} ({n_(d['sd'])})", f"{n_(d['ic'][0])}–{n_(d['ic'][1])}",
    f"{n_(d['md'],1)} [{n_(d['q1'],1)}–{n_(d['q3'],1)}]", f"{n_(d['md_ic'][0],1)}–{n_(d['md_ic'][1],1)}",
    n_(d['tm']), n_(d['mad']), f"{n_(d['mn'],1)}–{n_(d['mx'],1)}", n_(d['cv'],1)]
   for v,d in [(v,A1['DESC'][v]) for v in V7]],
  widths=[1.9,1.9,1.7,2.1,1.9,1.4,1.1,1.5,1.1], fs=8)
src(nota="MAD = desvio absoluto mediano multiplicado por 1,4826; CV = coeficiente de variação; PTH = "
         "perturbação total do humor. O intervalo da mediana provém de reamostragem com 10.000 repetições.")
para(A.R1[1])
caption("Tabela 2 – Forma da distribuição, efeito de piso, posição normativa e confiabilidade")
mktable(["Variável","Assim.","Curt.","W de Shapiro-Wilk (p)","Piso (%)","Escore T","CCI (1,1)","CCI (1,k)","EPM","MVD"],
  [[L(v), n_(A1['DESC'][v]['sk']), n_(A1['DESC'][v]['ku']),
    f"{n_(A1['DESC'][v]['W'],3)} ({pf_(A1['DESC'][v]['pW'])})", n_(A1['DESC'][v]['piso'],1),
    (n_(Tv(v,A1['DESC'][v]['m']),1) if v in NORMA else "—"),
    n_(A1['ICC'][v]['icc'],3), n_(A1['ICC'][v]['icck'],3), n_(A1['ICC'][v]['epm']), n_(A1['ICC'][v]['mvd'])]
   for v in V7],
  widths=[1.9,1.1,1.1,2.7,1.2,1.4,1.3,1.3,1.0,1.0], fs=8)
src(nota="Piso = percentual de respostas no valor mínimo; o critério de Terwee et al. (2007) considera "
         "problemática a concentração acima de 15%. CCI (1,1) refere-se à medida única e CCI (1,k) à média "
         "das medidas da semana. EPM = erro-padrão de medida; MVD = mínima variação detectável.")
for p in A.R1[2:]: para(p)
figura(f"{S}/F3fig.png",3,"Distribuição das sete variáveis e efeito de piso.",w=16.0)

head("3.2 Comportamento temporal e tendência ordenada", lvl=2)
para(A.R2[0])
figura(f"{S}/F4fig.png",4,"Trajetória das seis subescalas em escore T ao longo do microciclo e resultado do "
       "teste de tendência de Page.",w=16.0)
for p in A.R2[1:]: para(p)
caption("Tabela 3 – Comparação global entre os sete dias, tendência ordenada e contraste com a linha de base")
mktable(["Variável","χ² Friedman","p","W","z de Page","p","Δ D1→D7","r","p","p Holm"],
  [[L(v), n_(A2['NP'][v]['chi']), pf_(A2['NP'][v]['p']), n_(A2['NP'][v]['W'],3),
    n_(A2['NP'][v]['z']), pf_(A2['NP'][v]['pz']),
    n_([e for e in A2['NP'][v]['PH'] if e['par']=='D1–D7'][0]['d']),
    n_([e for e in A2['NP'][v]['PH'] if e['par']=='D1–D7'][0]['r'],3),
    pf_([e for e in A2['NP'][v]['PH'] if e['par']=='D1–D7'][0]['p']),
    pf_([e for e in A2['NP'][v]['PH'] if e['par']=='D1–D7'][0]['ph'])] for v in V7],
  widths=[1.9,1.6,1.2,1.1,1.3,1.2,1.3,1.0,1.2,1.2], fs=8)
src(nota="Friedman com gl = 6, restrito aos 19 atletas com registro completo nos sete dias; W = coeficiente "
         "de concordância de Kendall. Teste L de Page com alternativa ordenada. Contraste D1–D7 pelo teste de "
         "Wilcoxon em 21 atletas, com correção de Holm para as seis comparações com a linha de base; r = z/√n.")

head("3.3 Sinal, ruído e suavização", lvl=2)
para(A.R3[0])
figura(f"{S}/F5fig.png",5,"Decomposição sinal–ruído das seis subescalas: série observada com erro-padrão, "
       "série suavizada e banda do piso de ruído.",w=16.0)
for p in A.R3[1:]: para(p)
caption("Tabela 4 – Piso de ruído, deslocamento, veredito, transições de choque e pontos de inflexão")
mktable(["Variável","D1","D7","Δ","Piso","|Δ|/piso","Veredito","Transições de choque","Inflexão"],
  [[L(v), n_(d['med'][0]), n_(d['med'][6]), n_(d['dtot']), n_(d['piso']), n_(d['razao'],1),
    ("__SINAL" if d['sinal'] else "ruído"),
    (", ".join(f"D{c}→D{c+1}" for c in d['choque']) or "—"),
    (", ".join(n_(x) for x in d['infl']) or "—")] for v,d in [(v,A1['SER'][v]) for v in V7]],
  widths=[1.9,1.2,1.2,1.3,1.1,1.3,1.4,3.2,1.6], fs=8)
src(nota="O piso de ruído é a média dos sete erros-padrão diários. Declara-se sinal quando |Δ| o supera. "
         "Transição de choque é aquela cuja primeira derivada, em valor absoluto, supera o piso; o ponto de "
         "inflexão é a abscissa, em fração de dia, na qual a segunda derivada muda de sinal.")
figura(f"{S}/F6fig.png",6,"Primeira e segunda derivadas das séries diárias, expressas em unidades do piso de "
       "ruído de cada subescala.",w=16.0)
for p in A.R4[1:]: para(p)

head("3.4 Prevalência diária dos seis perfis", lvl=2)
para(A.R5[0])
figura(f"{S}/F7fig.png",7,"Prevalência diária dos seis perfis de humor, com piso de ruído e transições de "
       "choque.",w=16.0)
for p in A.R5[1:]: para(p)
caption("Tabela 5 – Prevalência diária dos perfis e das faixas, veredito e teste de estabilidade")
rows=[]
for nm in PERF+['Favorável','Neutra','De risco']:
    d=A3['SERP'][nm]
    cq=A3['CQ'].get(nm) or (A3['CQ'].get('Faixa de risco') if nm=='De risco' else None)
    ver=("não avaliável" if d.get('fragil') else ("__SINAL" if d['sinal'] else "ruído"))
    rows.append([nm]+[n_(x,1) for x in d['y']]+[n_(d['dtot'],1), n_(d['piso'],1), ver,
                 (n_(cq['Q']) if cq else "—"), (pf_(cq['p']) if cq else "—")])
mktable(["Perfil ou faixa","D1","D2","D3","D4","D5","D6","D7","Δ","Piso","Veredito","Q","p"], rows,
        widths=[3.0,0.9,0.9,0.9,0.9,0.9,0.9,0.9,1.0,0.9,1.2,0.9,1.0], fs=7.5)
src(nota="Valores em percentual dos pares atleta-dia do dia; n por dia = 27, 26, 26, 21, 23, 22 e 21. Δ e "
         "piso em pontos percentuais. Q de Cochran com gl = 6, restrito aos 19 atletas com registro completo; "
         "a faixa favorável coincide com o perfil iceberg. O Everest invertido aparece como não avaliável "
         "porque envolve dois pares no conjunto inteiro.")

head("3.5 Custo do dia, migração intradiária e resposta ao estímulo", lvl=2)
para(A.R6[0])
figura(f"{S}/F9fig.png",8,"Custo do dia por tipo de estímulo e migração intradiária para a faixa de risco.",w=16.0)
for p in A.R6[1:]: para(p)
caption("Tabela 6 – Resposta aguda intradiária por tipo de estímulo e migração para a faixa de risco")
rows=[["__Resposta aguda (pós − pré): Δ (r; p)","","",""]]
for v in V7:
    lin=[L(v)]
    for t in ['HIIT','Amistoso','Técnico/força']:
        d=A3['AG'][v][t]
        lin.append(f"{n_(d['d'])} ({n_(d['r'],2)}; {pf_(d['p'])})")
    rows.append(lin)
rows.append(["__Migração para a faixa de risco","","",""])
for t in ['TODOS','HIIT','Amistoso','Técnico/força']:
    m=A3['MCN'][t]
    rows.append([t, f"entram {m['entra']} · saem {m['sai']} (n = {m['n']})",
                 f"χ² = {n_(m['chi'])}; p = {pf_(m['p'])}",
                 (f"Holm p = {pf_(m['ph'])}" if m.get('ph') is not None else "—")])
mktable(["Variável ou estímulo","HIIT","Amistoso","Técnico/força"], rows,
        widths=[3.4,3.8,3.8,3.6], fs=8)
src(nota="Resposta aguda pelo teste de Wilcoxon para a diferença entre a última e a primeira medida do dia; "
         "r = z/√n. Migração pelo teste de McNemar com correção de continuidade, com Holm para as três "
         "comparações por estímulo.")

head("3.6 Teste formal de cruzamento", lvl=2)
para(A.R7[0])
figura(f"{S}/F8fig.png",9,"Teste formal de cruzamento entre trajetórias.",w=16.0)
for p in A.R7[1:]: para(p)
caption("Tabela 7 – Cruzamentos testados")
mktable(["Par de séries","Diferença em D1","Diferença em D7","Limiar","Cruzamentos","Veredito"],
  [[k.replace('TMD','PTH'), n_(d['d1']), n_(d['d7']), n_(d['lim']),
    (", ".join(f"D{n_(c)}" for c in d['cs']) or "—"),
    ("__inversão estabelecida" if d['est'] else "divergência")] for k,d in A1['CRZ'].items()],
  widths=[4.2,2.4,2.4,1.6,3.0,3.0], fs=8)
src(nota="O limiar é a raiz da soma dos quadrados dos dois pisos de ruído. A inversão só é declarada "
         "estabelecida quando a diferença o ultrapassa antes e depois do ponto de cruzamento.")

head("3.7 Qualidade dos dados e reconferência dos resultados", lvl=2)
para(A.RQ[0]); para(A.RQ[1])
caption("Tabela 8 – Completude do instrumento e cobertura da grade atleta-dia")
mktable(["Dia","Atletas com registro","Cobertura de atletas (%)","Registros","Previstos no protocolo",
         "Cobertura de registros (%)"],
        [[f"D{g['dia']}", f"{g['atletas_com_registro']} de {g['atletas_esperados']}",
          n_(g['cobertura_atleta'],1), str(g['registros']), str(g['registros_esperados']),
          n_(g['cobertura_registro'],1)] for g in QA['GRADE']],
        widths=[1.6,3.2,3.0,2.2,3.0,3.0], fs=8.5)
src(nota="Completude no nível do item: 100,00%, sem nenhuma célula ausente em 20.108 respostas de "
         "instrumento. O protocolo previa uma coleta em D1, que teve janela única noturna, e duas de D2 a D7; "
         "cobertura de registros acima de cem por cento indica reenvio, e não duplicata.")
para(A.RQ[2])
caption("Tabela 9 – Triagem de valores discrepantes: verificação de domínio e três critérios de dispersão")
mktable(["Variável","Domínio admissível","Fora do domínio","Cerca 1,5 × IQR","Cerca 3,0 × IQR","|z| > 3",
         "|z modificado| > 3,5","IQR"],
        [[L(v), (f"{n_(UNIQ[v]['dominio'][0],0)} a {n_(UNIQ[v]['dominio'][1],0)}"
                 if 'dominio' in UNIQ[v] else "—"),
          str(UNIQ[v].get('fora_do_dominio','—')),
          str(UNIQ[v]['n_tukey_moderado']), str(UNIQ[v]['n_tukey_extremo']), str(UNIQ[v]['n_z3']),
          (str(UNIQ[v]['n_zmod']) if UNIQ[v]['n_zmod'] is not None else "indefinido"),
          n_(UNIQ[v]['iqr'],1)] for v in V7],
        widths=[1.9,2.4,2.0,2.2,2.2,1.5,2.6,1.2], fs=8)
src(nota="Nível de registro, n = 456. A cerca de Tukey usa Q1 − 1,5 × IQR e Q3 + 1,5 × IQR; o escore z "
         "modificado é 0,6745 × (x − mediana) ÷ desvio absoluto mediano. Onde o intervalo interquartil é nulo, "
         "os dois critérios de dispersão perdem sentido, e o escore z modificado torna-se indefinido porque o "
         "desvio absoluto mediano também é nulo.")
para(A.RQ[3])
caption("Tabela 10 – Discrepantes intraindividuais: cada atleta contra a própria série")
mktable(["Variável","Atletas avaliados","Casos","Caso mais extremo"],
        [[L(i['variavel']), str(i['atletas_avaliados']), str(i['n_discrepantes']),
          (f"{i['casos'][0]['atleta']} em D{i['casos'][0]['dia']}: {n_(i['casos'][0]['valor'],0)} contra "
           f"mediana própria {n_(i['casos'][0]['mediana_do_atleta'],0)} "
           f"(z modificado = {'+' if i['casos'][0]['z_mod']>0 else ''}{n_(i['casos'][0]['z_mod'],1)})")
          if i['casos'] else "—"]
         for i in QA['INTRA'] if i['variavel'] in V7],
        widths=[2.4,2.8,1.6,8.2], fs=8.5)
src(nota="Escore z modificado calculado dentro da série de cada atleta, entre os que registraram quatro dias "
         "ou mais. Um caso intraindividual não indica erro de medida.")
para(A.RQ[4])
caption("Tabela 11 – Reconferência por dois caminhos independentes de cálculo")
_bl={}
for _c in CO['CONF']:
    _e=_bl.setdefault(_c['bloco'],[0,0]); _e[0]+=int(_c['confere']); _e[1]+=1
mktable(["Bloco de conferência","Conferências","Coincidem","Divergem"],
        [[b, str(t), str(o), str(t-o)] for b,(o,t) in _bl.items()]
        + [["Total", str(CO['total']), str(CO['ok']), str(CO['total']-CO['ok'])]],
        widths=[6.6,2.8,2.4,2.6], fs=8.5)
src(nota="O caminho A parte das colunas já pontuadas da base de origem e gerou a base canônica; o caminho B "
         "parte do item do formulário e reconstrói cada escore por fórmula. Tolerância de 5 × 10⁻³ para médias "
         "e derivadas e de 10⁻⁶ para valores de p.")

head("4 DISCUSSÃO")
for i,(sub,ps) in enumerate(A.DISCUSSAO):
    head(f"4.{i+1} {sub}", lvl=2)
    for p in ps: para(p)
head("5 LIMITAÇÕES")
for p in A.LIMITACOES: para(p)
head("6 CONCLUSÃO")
for p in A.CONCLUSAO: para(p)
head("DECLARAÇÕES")
para("Aprovação ética: parecer CAAE [inserir número do CAAE]. Consentimento: todos os participantes "
     "assinaram termo de consentimento livre e esclarecido. Financiamento: [inserir]. Conflito de interesses: "
     "os autores declaram não haver conflito de interesses. Contribuição dos autores: [inserir]. "
     "Disponibilidade de dados: a base anonimizada, os roteiros de análise e a base única de resultados podem "
     "ser disponibilizados mediante solicitação ao autor correspondente; os arquivos com identificação nominal "
     "permanecem sob guarda restrita e não são compartilhados.", indent=False, size=11, spacing=1.15)
head("REFERÊNCIAS")
import sqlite3
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
for (abnt,doi) in cx.execute("SELECT abnt, url_doi FROM referencia ORDER BY id"):
    para(abnt + (f" Disponível em: {doi}." if doi else ""), indent=False, size=11, spacing=1.0,
         after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
cx.close()
out=f"{S}/ARTIGO_1_DESCRITIVO_HUMOR_HANDEBOL.docx"
doc.save(out); print("salvo:", out)
