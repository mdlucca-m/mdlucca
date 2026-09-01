# -*- coding: utf-8 -*-
import os, sys
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"_docx_base.py")).read())
import A2T as A
import numpy as np, sqlite3
def jd(n): return json.load(open(os.path.join(DADOS,n+".json"),encoding='utf-8'))
B=jd("V2_base"); Q=jd("V2_perfis"); A1=jd("V2_a1"); A2=jd("V2_a2"); A3=jd("V2_a3")
CO=jd("V2_conf"); OT=jd("V2_otim")
UN=jd("V2_unid"); FA=jd("V2_falta"); ES=jd("V2_estim")
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V7=SUB+['TMD']
LB={'TMD':'PTH'}
def L(k): return LB.get(k,k)
def n_(x,d=2):
    if x is None or (isinstance(x,float) and x!=x): return "—"
    return f"{x:.{d}f}".replace('.',',').replace('-','−')
def pf_(p,d=3):
    if p is None or (isinstance(p,float) and p!=p): return "—"
    return "< 0,001" if p<0.001 else f"{p:.{d}f}".replace('.',',')

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
    if i==3:
        para("A Figura 1 resume as três vias aplicadas à mesma hipótese e explicita a árvore de decisão que "
             "determina, variável a variável, qual delas governa a conclusão reportada.")
        figura(f"{S}/G1fig.png",fig(),"As três vias de análise aplicadas à mesma hipótese e a árvore de decisão "
               "que define qual delas governa a conclusão em cada variável.",w=16.0)

head("3 RESULTADOS")
head("3.1 Pressupostos", lvl=2)
para(A.R1[0])
figura(f"{S}/G3fig.png",fig(),"Verificação de pressupostos variável a variável: normalidade, esfericidade, "
       "efeito de piso e homogeneidade de variâncias.",w=16.0)
for p in A.R1[1:]: para(p)
caption(f"Tabela {tab()} – Pressupostos das vias paramétricas, variável a variável")
mktable(["Variável","W de Shapiro-Wilk","p","Assim.","Curt.","Piso (%)","ε de GG","p de Levene","Casos completos"],
  [[L(v), n_(A1['DESC'][v]['W'],3), pf_(A1['DESC'][v]['pW']), n_(A1['DESC'][v]['sk']),
    n_(A1['DESC'][v]['ku']), n_(A1['DESC'][v]['piso'],1), n_(A2['PA'][v]['eps'],3),
    pf_(A2['PA'][v]['lev']), str(A2['NP'][v]['n'])] for v in V7],
  widths=[1.9,2.0,1.2,1.1,1.2,1.2,1.3,1.5,1.9], fs=8)
src(nota="ε de Greenhouse-Geisser abaixo de 0,75 indica violação de esfericidade que torna obrigatória a "
         "correção dos graus de liberdade. Casos completos = atletas com registro nos sete dias, único "
         "conjunto sobre o qual as vias clássicas de medidas repetidas podem operar; o total disponível é de "
         "166 pares atleta-dia de 27 atletas.")

head("3.2 A mesma hipótese pelas três vias", lvl=2)
para(A.R2[0])
figura(f"{S}/G2fig.png",fig(),"A mesma hipótese submetida às três vias, e a magnitude do contraste entre a linha "
       "de base e a véspera da estreia com intervalo de confiança.",w=16.0)
for p in A.R2[1:]: para(p)
caption(f"Tabela {tab()} – Comparação entre os sete dias pelas três vias de análise")
rows=[]
for v in V7:
    a,b,c=A2['NP'][v],A2['PA'][v],A3['LMM'][v]
    conc="sim" if (a['p']<.05)==(b['pGG']<.05)==(c['p']<.05) else "__NÃO"
    rows.append([L(v), f"{n_(a['chi'])}", pf_(a['p']), n_(a['W'],3),
                 f"{n_(b['F'])}", pf_(b['pGG']), n_(b['eta2p'],3),
                 f"{n_(c['b_dia'],3)}", pf_(c['p']), conc])
mktable(["Variável","χ² Friedman","p","W","F (ANOVA-MR)","p com GG","η²p","b por dia","p","Concordam"],
        rows, widths=[1.8,1.6,1.2,1.0,1.6,1.3,1.0,1.3,1.2,1.4], fs=8)
src(nota="Friedman e ANOVA de medidas repetidas com gl = 6, restritas aos 19 atletas com registro completo; "
         "ANOVA com graus de liberdade corrigidos por Greenhouse-Geisser. Modelo misto ajustado sobre os 166 "
         "pares atleta-dia, com intercepto aleatório por atleta e o dia como efeito fixo contínuo. A coluna "
         "final indica se as três vias concordam quanto à significância ao nível de 5%.")
caption(f"Tabela {tab()} – Contraste entre a linha de base e a véspera da estreia pelas duas vias")
mktable(["Variável","Δ D1→D7","Wilcoxon p","p Holm","r","t","p","dz","IC 95% da diferença"],
  [[L(v), n_([e for e in A2['NP'][v]['PH'] if e['par']=='D1–D7'][0]['d']),
    pf_([e for e in A2['NP'][v]['PH'] if e['par']=='D1–D7'][0]['p']),
    pf_([e for e in A2['NP'][v]['PH'] if e['par']=='D1–D7'][0]['ph']),
    n_([e for e in A2['NP'][v]['PH'] if e['par']=='D1–D7'][0]['r'],3),
    n_(A2['PA'][v]['t']), pf_(A2['PA'][v]['pt']), n_(A2['PA'][v]['dz'],3),
    f"{n_(A2['PA'][v]['ic'][0])} a {n_(A2['PA'][v]['ic'][1])}"] for v in V7],
  widths=[1.8,1.4,1.6,1.3,1.0,1.2,1.2,1.2,2.6], fs=8)
src(nota="n = 21 atletas com medida no primeiro e no sétimo dia. r = z/√n; dz = diferença média dividida "
         "pelo desvio-padrão das diferenças. A correção de Holm cobre as seis comparações com a linha de base.")
for p in A.R3: para(p)

head("3.3 Modelo linear misto e decomposição da variância", lvl=2)
for p in A.R4[:1]: para(p)
figura(f"{S}/G6fig.png",fig(),"Efeito linear do dia estimado pelo modelo misto e proporção da variância "
       "atribuível a diferenças estáveis entre atletas.",w=16.0)
for p in A.R4[1:]: para(p)
caption(f"Tabela {tab()} – Modelo linear misto: efeito do dia e decomposição da variância")
mktable(["Variável","b por dia","IC 95%","z","p","Variância entre atletas","CCI descritivo","MVD"],
  [[L(v), n_(A3['LMM'][v]['b_dia'],3),
    f"{n_(A3['LMM'][v]['ic'][0],3)} a {n_(A3['LMM'][v]['ic'][1],3)}",
    n_(A3['LMM'][v]['z']), pf_(A3['LMM'][v]['p']), n_(A3['LMM'][v]['icc'],3),
    n_(A1['ICC'][v]['icc'],3), n_(A1['ICC'][v]['mvd'])] for v in V7],
  widths=[2.0,1.5,2.4,1.1,1.3,2.4,1.9,1.2], fs=8)
src(nota="Ajuste por máxima verossimilhança restrita sobre os 166 pares atleta-dia. A variância entre atletas "
         "é a razão entre a variância do intercepto aleatório e a soma dessa variância com a residual. O CCI "
         "descritivo, calculado de modo independente, aparece para comparação. MVD = mínima variação "
         "detectável, em pontos da escala.")

head("3.4 Estrutura de associação pelas duas vias", lvl=2)
for p in A.R5[:1]: para(p)
figura(f"{S}/G5fig.png",fig(),"Matriz de Spearman, matriz de Pearson e concordância entre os dois coeficientes.",w=16.0)
for p in A.R5[1:]: para(p)
caption(f"Tabela {tab()} – Associação entre as sete variáveis pelas duas vias")
MAT=A3['MAT']
mktable(["Par de variáveis","ρ de Spearman","p Holm","r de Pearson","p Holm","|ρ| − |r|"],
  [[k.replace('TMD','PTH').replace('×',' × '), n_(m['rho'],3), pf_(m['ph']), n_(m['r'],3), pf_(m['phr']),
    n_(abs(m['rho'])-abs(m['r']),3)] for k,m in MAT.items()],
  widths=[4.6,2.2,1.7,2.2,1.7,1.8], fs=8)
src(nota="166 pares atleta-dia. Correção de Holm aplicada aos 21 pares em cada via. Valores positivos na "
         "última coluna indicam que a estimativa de postos supera a de momento-produto.")

head("3.5 Resposta ao estímulo e dinâmica intradiária", lvl=2)
for p in A.R6[:1]: para(p)
figura(f"{S}/G4fig.png",fig(),"Distribuição dos perfis e das faixas de humor por tipo de estímulo.",w=16.0)
for p in A.R6[1:]: para(p)
caption(f"Tabela {tab()} – Nível diário e resposta aguda por tipo de estímulo, pelas duas vias")
rows=[["__Nível médio do dia (n = 22 atletas com registro nos três tipos)","","","","",""]]
for v in V7:
    d=A3['NIV'][v]
    rows.append([L(v), n_(d['HIIT']), n_(d['Amistoso']), n_(d['Técnico/força']),
                 f"χ² = {n_(d['chi'])}; p = {pf_(d['p'])}", f"F = {n_(d['F'])}; p = {pf_(d['pF'])}"])
rows.append(["__Resposta aguda: Δ pós − pré (r; p de Wilcoxon | dz; p do t pareado)","","","","",""])
for v in V7:
    lin=[L(v)]
    for t in ['HIIT','Amistoso','Técnico/força']:
        d=A3['AG'][v][t]
        lin.append(f"{n_(d['d'])} ({n_(d['r'],2)}; {pf_(d['p'])} | {n_(d['dz'],2)}; {pf_(d['pt'])})")
    lin+=["",""]
    rows.append(lin)
mktable(["Variável","HIIT","Amistoso","Técnico/força","Friedman","ANOVA-MR"], rows,
        widths=[1.7,3.3,3.3,3.3,1.9,1.9], fs=7.5)
src(nota="Associação entre estímulo e perfil: χ² = "+n_(A3['chi'])+f"; gl = {A3['gl']}; p = "+pf_(A3['p_chi'])+
        ". Associação entre estímulo e faixa: χ² = "+n_(A3['chi_f'])+f"; gl = {A3['gl_f']}; p = "+pf_(A3['p_f'])+
        ". Migração para a faixa de risco nos 119 pares completos: entram "+str(A3['MCN']['TODOS']['entra'])+
        ", saem "+str(A3['MCN']['TODOS']['sai'])+"; χ² = "+n_(A3['MCN']['TODOS']['chi'])+"; p = "+
        pf_(A3['MCN']['TODOS']['p'])+".")

head("3.6 Confronto entre o critério de ruído e as vias inferenciais", lvl=2)
for p in A.R7[:1]: para(p)
caption(f"Tabela {tab()} – O veredito do piso de ruído confrontado com o das três vias")
mktable(["Variável","Δ D1→D7","Piso","|Δ|/piso","Veredito do piso","Friedman","ANOVA-MR","Modelo misto","Concordam"],
  [[L(v), n_(A1['SER'][v]['dtot']), n_(A1['SER'][v]['piso']), n_(A1['SER'][v]['razao'],1),
    ("__SINAL" if A1['SER'][v]['sinal'] else "ruído"),
    ("sig." if A2['NP'][v]['p']<.05 else "n.s."),
    ("sig." if A2['PA'][v]['pGG']<.05 else "n.s."),
    ("sig." if A3['LMM'][v]['p']<.05 else "n.s."),
    ("sim" if (A1['SER'][v]['sinal']==(A2['NP'][v]['p']<.05)==(A2['PA'][v]['pGG']<.05)==(A3['LMM'][v]['p']<.05))
     else "__NÃO")] for v in V7],
  widths=[1.8,1.3,1.1,1.3,2.0,1.4,1.4,1.6,1.4], fs=8)
src(nota="O veredito do piso não depende de hipótese nula: compara o deslocamento total ao ruído amostral "
         "típico da própria série. As duas leituras respondem a perguntas distintas, e a divergência entre "
         "elas indica onde a conclusão é frágil.")
for p in A.R7[1:]: para(p)

head("3.7 Carga do dia e carga da véspera", lvl=2)
para(A.R8[0])
caption(f"Tabela {tab()} – Modelo misto da carga do dia e da carga da véspera")
_M=OT['MODELO']
mktable(["Variável","β₀","β₁ · horas do dia","IC 95% de β₁","p","β₂ · horas da véspera","IC 95% de β₂","p"],
  [[L(v), n_(_M[v]['b0'],3), n_(_M[v]['b1'],4),
    f"{n_(_M[v]['b1']-1.96*_M[v]['se1'],3)}; {n_(_M[v]['b1']+1.96*_M[v]['se1'],3)}", pf_(_M[v]['p1']),
    n_(_M[v]['b2'],4),
    f"{n_(_M[v]['b2']-1.96*_M[v]['se2'],3)}; {n_(_M[v]['b2']+1.96*_M[v]['se2'],3)}", pf_(_M[v]['p2'])]
   for v in ['Fadiga','Vigor','TMD','Tensão']],
  widths=[1.8,1.4,2.2,2.4,1.3,2.4,2.4,1.3], fs=8)
src(nota="Modelo misto com intercepto aleatório por atleta, estimado por máxima verossimilhança sobre os 166 "
         "pares atleta-dia de 27 atletas. O coeficiente exprime a variação esperada do escore por hora "
         "adicional de treino, mantida constante a outra parcela. Com uma única equipe e sete dias, o efeito "
         "das horas não se separa do efeito do dia nem da carga acumulada: as estimativas são associativas.")
for p in A.R8[1:]: para(p)

head("3.8 Sensibilidade do veredito à unidade de análise", lvl=2)
para(A.R9[0])
_ORD=UN['ordem']
caption(f"Tabela {tab()} – O contraste entre a linha de base e a véspera da estreia, por unidade de análise")
mktable(["Variável"]+[f"{u}\np (Δ)" for u in _ORD]+["Troca de veredito"],
  [[L(t['variavel'])]
   + [(f"{pf_(t['p'][u])}\n({n_(t['delta'][u])})" if t['p'][u] is not None else "—") for u in _ORD]
   + ["sim" if t['troca'] else "não"] for t in UN['TROCA_D1D7']],
  widths=[2.0,2.5,2.5,2.5,2.5,2.5], fs=8)
src(nota="U-AD = par atleta-dia, unidade adotada; U-286 = primeiro e último registro do dia; U-PAR = "
         "subamostra dos atletas com medida em D1 e D7; U-R = registro isolado, que não admite pareamento e "
         "por isso recebe teste não pareado. A U-PAR reproduz a U-AD porque o contraste entre extremos já "
         "opera apenas sobre os atletas com as duas medidas.")
para(A.R9[1]); para(A.R9[2])
caption(f"Tabela {tab()} – A comparação global entre os sete dias, por unidade de análise")
mktable(["Variável"]+[f"{u}\np de Friedman" for u in _ORD[:3]]+["Troca de veredito"],
  [[L(t['variavel'])] + [(pf_(t['p'][u]) if t['p'][u] is not None else "—") for u in _ORD[:3]]
   + ["sim" if t['troca'] else "não"] for t in UN['TROCA_GLOBAL']],
  widths=[2.8,3.0,3.0,3.0,3.2], fs=8.5)
src(nota="Restrito, em cada unidade, aos atletas com registro nos sete dias. O registro isolado não admite "
         "teste de medidas repetidas e fica fora da comparação.")
para(A.R9[3])

head("3.9 Robustez à regra de composição do valor diário", lvl=2)
para(A.R9B[0]); para(A.R9B[1])

head("3.10 Mecanismo de ausência", lvl=2)
para(A.R10[0])
caption(f"Tabela {tab()} – A probabilidade de responder no dia seguinte, em função do humor do dia")
mktable(["Variável","β do humor","Erro padrão","p","p de Holm","p do dia","Associação"],
  [[L(m['variavel']), n_(m['beta'],4), n_(m['se'],4), pf_(m['p'],4),
    pf_(m.get('p_holm'),4), pf_(m['p_dia'],4),
    ("sim" if m.get('significativo') else "não")] for m in FA['MISTO'] if m['beta'] is not None],
  widths=[2.4,2.2,2.2,1.8,2.0,1.8,2.2], fs=8.5)
src(nota=f"Modelo logístico de efeitos mistos com intercepto aleatório por atleta, sobre {FA['n_pares']} "
         f"pares atleta-dia com dia seguinte possível, dos quais {FA['n_respondeu']} tiveram resposta. "
         "Correção de Holm para as sete comparações.")
para(A.R10[1]); para(A.R10[2])
caption(f"Tabela {tab()} – Limites de pior caso para a variação entre o primeiro e o sétimo dia")
mktable(["Variável","Δ observado","Limite inferior","Limite superior","Ausentes imputados","Sinal preservado"],
  [[L(l['variavel']), n_(l['delta']), n_(l['limite_inf']), n_(l['limite_sup']),
    str(l['n_ausentes']), ("sim" if l['sinal_preservado'] else "não")] for l in FA['LIMITES']],
  widths=[2.6,2.4,2.6,2.6,2.8,2.6], fs=8.5)
src(nota="Cada atleta com medida em D1 e sem medida em D7 recebe, alternadamente, o quinto e o nonagésimo "
         "quinto percentil observado em D7. O sinal é considerado preservado quando os dois cenários "
         "extremos concordam com o sinal observado.")
para(A.R10[3])

head("3.11 HIIT e amistoso: resposta aguda, contraste pareado e resíduo", lvl=2)
para(A.R11[0])
caption(f"Tabela {tab()} – HIIT contra amistoso, pareado no mesmo atleta")
mktable(["Variável","n","Δ no HIIT","Δ no amistoso","Diferença","IC 95% da diferença","dz","Magnitude","p"],
  [[L(c['variavel']), str(c['n']), n_(c['hiit']), n_(c['amistoso']), n_(c['diferenca']),
    f"{n_(c['ic'][0])}; {n_(c['ic'][1])}", n_(c['dz']), c['magnitude'], pf_(c['p'])]
   for c in ES['CONTRASTE']],
  widths=[1.8,1.0,1.7,1.9,1.6,2.4,1.2,1.8,1.4], fs=8)
src(nota="Δ = resposta aguda, isto é, a diferença entre a última e a primeira medida do dia, promediada "
         "dentro de cada atleta por tipo de estímulo. Teste de Wilcoxon pareado; intervalo por reamostragem; "
         "dz = média da diferença ÷ desvio-padrão da diferença.")
para(A.R11[1])
caption(f"Tabela {tab()} – Resíduo na manhã seguinte, por tipo de estímulo do dia anterior")
mktable(["Variável","Estímulo","n","Δ da manhã","IC 95%","dz","Magnitude","Δ ÷ erro típico","p"],
  [[L(r['variavel']), r['estimulo'], str(r['n']), n_(r['delta']),
    f"{n_(r['ic'][0])}; {n_(r['ic'][1])}", n_(r['dz']), r['magnitude'],
    n_(r['delta_sobre_et']), pf_(r['p'])] for r in ES['RESIDUO']],
  widths=[1.7,2.2,0.9,1.6,2.2,1.1,1.6,2.0,1.3], fs=7.5)
src(nota="Δ = medida da manhã do dia seguinte menos a medida da manhã do dia do estímulo. O erro típico é o "
         "do artigo companheiro, estimado sobre dias consecutivos do mesmo atleta.")
para(A.R11[2]); para(A.R11[3])
caption(f"Tabela {tab()} – Migração para a faixa de risco ao longo do dia, por tipo de estímulo")
mktable(["Estímulo","Pares","Fora da faixa pela manhã","Entram até a noite","Taxa","IC 95%"],
  [[m['estimulo'], str(m['pares']), str(m['fora']), str(m['entram']),
    (n_(100*m['taxa'],1)+"%" if m['taxa'] is not None else "—"),
    f"{n_(100*m['ic'][0],1)}%; {n_(100*m['ic'][1],1)}%"] for m in ES['MIGRACAO']],
  widths=[3.0,1.8,3.4,3.0,1.8,2.6], fs=8.5)
src(nota=f"Intervalo de Jeffreys para a proporção. Qui-quadrado entre os três estímulos: "
         f"χ² = {n_(ES['qui2'])}; {pf_(ES['p_qui2'])}.")
para(A.R11[4])

head("3.12 Reconferência dos resultados", lvl=2)
para("Os valores relatados neste artigo foram recalculados por um segundo caminho de código, independente do "
     "que produziu a base canônica. O caminho A parte das colunas já pontuadas da base de origem; o caminho B "
     "parte do item do formulário e reconstrói cada escore por fórmula, inclusive a perturbação total do humor "
     "e as escalas auxiliares. A Tabela 9 apresenta o resultado por bloco.")
_bl={}
for _c in CO['CONF']:
    _e=_bl.setdefault(_c['bloco'],[0,0]); _e[0]+=int(_c['confere']); _e[1]+=1
caption(f"Tabela {tab()} – Reconferência por dois caminhos independentes de cálculo")
mktable(["Bloco de conferência","Conferências","Coincidem","Divergem"],
        [[b, str(t), str(o), str(t-o)] for b,(o,t) in _bl.items()]
        + [["Total", str(CO['total']), str(CO['ok']), str(CO['total']-CO['ok'])]],
        widths=[6.6,2.8,2.4,2.6], fs=8.5)
src(nota="Tolerância de 5 × 10⁻³ para médias e derivadas e de 10⁻⁶ para valores de p e para a estatística W. "
         "Os valores de W do teste de Shapiro-Wilk coincidem entre os dois caminhos até a quarta casa decimal, "
         "de modo que a opção pela via não paramétrica não depende de particularidade do processamento.")

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
     "Disponibilidade de dados: a base anonimizada, os roteiros das três vias e a base única de resultados "
     "podem ser disponibilizados mediante solicitação ao autor correspondente.", indent=False, size=11,
     spacing=1.15)
head("REFERÊNCIAS")
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
for (abnt,doi) in cx.execute("SELECT abnt, url_doi FROM referencia ORDER BY id"):
    para(abnt + (f" Disponível em: {doi}." if doi else ""), indent=False, size=11, spacing=1.0,
         after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
cx.close()
out=f"{S}/ARTIGO_2_INFERENCIAL_HUMOR_HANDEBOL.docx"
doc.save(out); print("salvo:", out)
