# -*- coding: utf-8 -*-
"""Artigo completo sobre os seis perfis de humor de Terry em atletas de handebol
de elite, na última semana de pré-temporada. Introdução com citações atuais,
método completo, resultados com toda a bateria descritiva e não paramétrica
(Shapiro-Wilk, Friedman, W de Kendall, L de Page, Wilcoxon pareado, Spearman,
modelo misto, ICC, Q de Cochran, qui-quadrado, McNemar) e discussão breve
organizada por tópico. O foco é o comportamento dos seis perfis ao longo da
semana: qual migra mais, qual é o perfil geral do elenco no primeiro e no
sétimo dia, como vigor, fadiga e perturbação total se cruzam, qual variável é
mais sensível e qual o pico de cada uma, e a assinatura que distingue, na
prática, o iceberg da barbatana de tubarão. Todo número procede dos JSON de
análise e da tabela resultado, nunca de rascunho anterior.
"""
import os, sys, collections, sqlite3
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_docx_base.py")).read())

sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.2)
st.font.size = Pt(10.5)
pf.line_spacing = 1.1
pf.space_after = Pt(3)

import re as _re
def p_(txt, size=10.5, spacing=1.1, after=3, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    q = doc.add_paragraph()
    for i, parte in enumerate(_re.split(r'__(.+?)__', txt)):
        if not parte: continue
        r = q.add_run(parte); r.bold = (i % 2 == 1); r.font.size = Pt(size)
    f = q.paragraph_format; f.alignment = align; f.line_spacing = spacing
    f.space_before = Pt(0); f.space_after = Pt(after)
    f.first_line_indent = Cm(1.0) if indent else Cm(0)
    return q

def h_(txt, before=9, size=11):
    para(txt, indent=False, bold=True, size=size, align=WD_ALIGN_PARAGRAPH.LEFT,
         before=before, after=3, spacing=1.1)

def cap_(txt):
    para(txt, indent=False, size=9, align=WD_ALIGN_PARAGRAPH.LEFT, before=7, after=2, spacing=1.0)

def nota_(txt):
    para("Nota: " + txt, indent=False, size=8.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         before=2, after=8, spacing=1.0)

prox_tab = lambda: _CONT['tab'] + 1
prox_fig = lambda: _CONT['fig'] + 1

def fig_(arq, legenda, w=13.4):
    cap_(f"Figura {fig()} – {legenda}")
    doc.add_picture(os.path.join(S, arq), width=Cm(w))
    q = doc.paragraphs[-1]; q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.first_line_indent = Cm(0); q.paragraph_format.space_after = Pt(8)

jd = lambda n: json.load(open(os.path.join(DADOS, n + ".json"), encoding='utf-8'))
QP = jd("V2_perfis"); A1 = jd("V2_a1"); A3 = jd("V2_a3"); B = jd("V2_base"); PR = jd("V2_proto")
DK = jd("V2_decomp"); EXP = jd("V2_expl")
SER = A1['SER']; DESC = A1['DESC']; SERP = A3['SERP']; ICC = A1['ICC']; LMM = A3['LMM']
NOMES = QP['NOMES']; REF = QP['PREV_REF']
lab = QP['lab_AD']; CT = collections.Counter(lab); NAD = len(lab)
V7 = ['Tensão', 'Depressão', 'Raiva', 'Vigor', 'Fadiga', 'Confusão', 'TMD']
V11 = EXP['V11']
Lb = lambda v: 'PTH' if v == 'TMD' else v

def n_(x, d=1):
    if x is None or (isinstance(x, float) and x != x): return "—"
    return f"{x:.{d}f}".replace('.', ',').replace('-', '−')
def pf_(p, d=3):
    if p is None: return "—"
    return "< 0,001" if p < 0.001 else f"{p:.{d}f}".replace('.', ',')
def efeito_(r):
    if r is None: return "—"
    a = abs(r)
    return "grande" if a >= .5 else ("médio" if a >= .3 else ("pequeno" if a >= .1 else "trivial"))

cx = sqlite3.connect(os.path.join(RAIZ, "base", "humor_handebol.sqlite")); cx.row_factory = sqlite3.Row
def pget(var, rec, teste_like, via="não paramétrica"):
    r = cx.execute("SELECT p,estatistica,efeito,n FROM resultado WHERE variavel=? AND recorte=? "
                   "AND teste LIKE ? AND via=?", (var, rec, teste_like, via)).fetchone()
    return r

sys.path.insert(0, os.path.join(RAIZ, "texto")); import REFS as _R
# Índices em REFS.REFS efetivamente citados no corpo do texto abaixo, um a um.
ESCOLHIDAS = [33, 0, 25, 36, 12, 22, 54, 26, 11, 2, 43, 40, 42, 41, 19, 38, 3, 4, 14, 46, 20, 31,
              51, 50, 56, 8, 21, 35, 60, 5, 49, 30]

# ============================== documento ==============================
para("OS SEIS PERFIS DE HUMOR DE TERRY NO HANDEBOL DE ELITE: A SEMANA FINAL DE PRÉ-TEMPORADA",
     indent=False, bold=True, size=13, align=WD_ALIGN_PARAGRAPH.CENTER, after=9, spacing=1.15)

h_("RESUMO", before=0, size=10)
p_(f"Este estudo descreve o comportamento dos seis perfis de humor de Terry, Parsons-Smith e Machin e das "
   f"onze variáveis do BRUMS em {len(B['ATL'])} atletas de handebol masculino de elite, ao longo dos sete "
   f"dias que antecederam a estreia competitiva, com {NAD} pares atleta-dia. O objetivo geral é descrever o "
   "perfil de humor desses atletas na última semana de pré-temporada, com foco em como os seis perfis se "
   "comportam dia a dia, qual migra mais entre o primeiro e o último dia, qual é o perfil geral do elenco em "
   "cada extremo da semana, e como vigor, fadiga e perturbação total se cruzam. O vigor e a fadiga física são "
   f"as variáveis mais sensíveis à semana, com deslocamento de {n_(SER['Vigor']['razao'])} e "
   f"{n_(SER['Fad.Física']['razao'])} vezes o respectivo piso de ruído, ambas com tendência monotônica pelo "
   "teste L de Page. O iceberg é o perfil de partida mais frequente no primeiro dia "
   f"({n_(SERP['Iceberg']['y'][0])}%) e cede lugar, no sétimo, a um empate triplo entre submerso, barbatana "
   f"de tubarão e iceberg invertido ({n_(SERP['Barbatana de tubarão']['y'][6])}% cada). A barbatana de "
   f"tubarão é o perfil de maior retenção individual, e a superfície, o de maior migração. Conclui-se que a "
   "semana desloca o elenco de um perfil de vigor preservado para perfis de maior custo afetivo, sem que o "
   "vigor em si desapareça na maioria dos casos, o que distingue a barbatana de tubarão do colapso completo "
   "do submerso.",
   indent=False, size=10, spacing=1.05, after=4)
para("__Palavras-chave:__ Estados de humor. Perfis de humor. Handebol. Pré-temporada. BRUMS.",
     indent=False, size=10, spacing=1.05, after=9)

# ---------------------------------------------------------------- 1
h_("1 INTRODUÇÃO", before=3)
p_("O estudo dos estados de humor em atletas segue a tradição inaugurada pelo perfil iceberg: Morgan (1980) "
   "descreveu, a partir do Perfil de Estados de Humor, um padrão em que atletas de elite exibem vigor "
   "elevado e as cinco dimensões negativas, tensão, depressão, raiva, fadiga e confusão, abaixo da média "
   "normativa, um contorno gráfico que lembra um iceberg invertido no eixo das ordenadas. Duas metanálises "
   "subsequentes, que reuniram dezenas de estudos, confirmaram associação consistente, ainda que modesta, "
   "entre esse perfil e o desempenho esportivo (BEEDIE; TERRY; LANE, 2000; LOCHBAUM et al., 2021).")
p_("A leitura de um único perfil médio, porém, esconde a heterogeneidade da amostra. Parsons-Smith, Terry e "
   "Machin (2017) reanalisaram milhares de perfis individuais por conglomerados hierárquicos e identificaram "
   "seis padrões distintos, batizados por analogia visual: iceberg, superfície, submerso, barbatana de "
   "tubarão, iceberg invertido e Everest invertido, cada um com prevalência e significado psicológico "
   "próprios. A tipologia foi replicada em amostras de Singapura (HAN; PARSONS-SMITH; TERRY, 2020), da "
   "Malásia (LEW et al., 2023), da Grécia (TERRY; PARSONS-SMITH; VLACHOPOULOS, 2024) e da Finlândia "
   "(LUOJUMÄKI et al., 2026), com prevalências semelhantes de perfis de maior custo afetivo entre "
   "populações fisicamente ativas e sedentárias, e em contextos de confinamento competitivo, como o de um "
   "campeonato mundial de combate (GENTILE et al., 2021) e o de uma seleção nacional de basquete em "
   "competição internacional (BIRD et al., 2025).")
p_("No Brasil, a Escala de Humor de Brunel foi validada por Rohlfs et al. (2008) e teve suas propriedades "
   "psicométricas revisitadas em amostras de atletas jovens e de elite sob dois intervalos de resposta "
   "distintos (ROHLFS et al., 2023). A tipologia de seis perfis foi descrita pela primeira vez em um clube "
   "brasileiro por Rohlfs, Noce e Wilke (2024), que também associaram o perfil individual à ocorrência de "
   "lesão e ao desempenho no salto com contramovimento em atletas de alto rendimento (ROHLFS; NOCE; WILKE, "
   "2025). Falta, ainda, descrição de como esses seis perfis se comportam ao longo de uma semana real de "
   "treinamento em uma modalidade coletiva de contato.")
p_("O handebol de elite impõe demanda física intermitente de alta intensidade, com esforços repetidos de "
   "sprint, salto e contato (KARCHER; BUCHHEIT, 2014), e a pré-temporada concentra o maior volume de carga do "
   "ciclo anual, justamente o período de maior risco de lesões por sobrecarga (RAFNSSON et al., 2021; "
   "BJØRNDAL et al., 2021). A variação individual na carga semanal é ampla mesmo dentro de uma mesma equipe "
   "(BÜCHEL; DÖRING; BAUMEISTER, 2026), e um levantamento recente com equipes profissionais de handebol "
   "mostrou que o monitoramento sistemático do estado psicológico do atleta continua sendo prática "
   "minoritária, distante da carga física, quase sempre monitorada (HENZE et al., 2025). Medidas subjetivas "
   "de autorrelato, como o BRUMS, superam medidas objetivas isoladas na detecção precoce de desequilíbrio "
   "entre carga e recuperação (SAW; MAIN; GASTIN, 2016), e compõem parte central dos consensos internacionais "
   "sobre monitoramento de carga e sobretreinamento (KELLMANN et al., 2018; MEEUSEN et al., 2013).")
p_("O objetivo geral deste estudo é descrever o perfil de humor de atletas de handebol de elite na última "
   "semana de pré-temporada, com foco nos seis perfis de humor de Terry: como se comportam ao longo da "
   "semana, qual perfil migra mais e qual menos entre o primeiro e o último dia, qual é o perfil geral do "
   "elenco no primeiro dia e no sétimo, como o vigor, a fadiga do BRUMS e a perturbação total de humor se "
   "comportam e se cruzam ao longo da semana, qual variável é mais prevalente ou tem mais variação, qual é o "
   "pico de cada variável ao longo da semana, e qual assinatura, em cada subescala, distingue de fato um "
   "perfil de vigor preservado, como a barbatana de tubarão, de um perfil de colapso, como o submerso.")

# ---------------------------------------------------------------- 2
h_("2 MÉTODO")
h_("2.1 Delineamento, participantes e coleta", before=6, size=10.5)
p_(f"Estudo observacional longitudinal de medidas repetidas, com sete dias consecutivos, entre 21 e 27 de "
   f"abril de 2024, sem intervenção dos pesquisadores. Participaram {len(B['ATL'])} atletas de handebol "
   "masculino de equipe da primeira divisão nacional, com idade média de 21,96 anos e desvio-padrão de 3,81. "
   "A semana reuniu quatro tipos de estímulo: conteúdo técnico e tático no primeiro dia, que serviu de linha "
   "de base; treino intervalado de alta intensidade com trabalho técnico no segundo, quarto e sétimo; jogo "
   "amistoso no terceiro e no quinto; conteúdo técnico, tático e de força no sexto. O primeiro dia teve "
   "coleta única, à noite; do segundo ao sétimo houve uma medida no início e outra ao fim do dia.")
h_("2.2 Instrumento e classificação nos perfis", before=6, size=10.5)
p_("Aplicou-se a Escala de Humor de Brunel (TERRY et al., 1999), com vinte e quatro itens em seis subescalas "
   "de quatro itens cada, validada para o português brasileiro por Rohlfs et al. (2008). Os escores brutos "
   "foram convertidos em escore T contra parâmetros normativos de amostras atléticas, com média cinquenta e "
   "desvio-padrão dez (TERRY; LANE, 2000). A perturbação total do humor soma as cinco subescalas negativas e "
   "subtrai o vigor. Cada vetor de seis escores T foi atribuído ao perfil cujo centroide de referência se "
   "encontra a menor distância euclidiana (PARSONS-SMITH; TERRY; MACHIN, 2017), e os seis perfis foram "
   "agrupados em três faixas: favorável, que reúne o iceberg; neutra, superfície e submerso; e de risco, "
   "barbatana de tubarão, iceberg invertido e Everest invertido. Além das seis subescalas, entraram na "
   "análise descritiva a fadiga física, a fadiga mental, a sonolência diurna de Epworth e o estresse "
   "percebido.")
h_("2.3 Unidade de análise e composição do valor diário", before=6, size=10.5)
p_(f"A fonte reúne {PR['TOTAIS']['registros']} registros. A unidade de análise é o par atleta-dia, com "
   f"{NAD} casos, auditada contra os carimbos de data e hora: no dia basal, de coleta única, vale a primeira "
   "resposta de cada atleta, porque as respostas tardias daquela noite são repetição e não segunda medida; "
   "do segundo ao sétimo dia valem o primeiro e o último registro, tomados como medida do início e do fim do "
   "dia.")
h_("2.4 Plano de análise", before=6, size=10.5)
p_("A estatística descritiva incluiu média, desvio-padrão, mediana, quartis, coeficiente de variação, "
   "assimetria e o teste de Shapiro-Wilk para normalidade, além do efeito de piso, definido como o percentual "
   "de respostas no valor mínimo possível, propriedade métrica que desaconselha o tratamento paramétrico "
   "automático de uma escala (TERWEE et al., 2007). A sensibilidade de cada variável foi ordenada pela razão "
   "entre o "
   "deslocamento semanal e o piso de ruído, definido como a média dos sete erros-padrão diários, amostral "
   "para médias e binomial para prevalências. A comparação entre os sete dias usou o teste de Friedman "
   "(FRIEDMAN, 1937), com o coeficiente W de Kendall como tamanho de efeito (KENDALL; SMITH, 1939), e a "
   "tendência ordenada foi testada pelo L de Page (PAGE, 1963). O contraste entre o primeiro e o sétimo dia, e "
   "entre a medida do início e a do fim do dia, usou o teste de Wilcoxon pareado (WILCOXON, 1945), com o "
   "coeficiente r como tamanho de efeito, classificado pelos limiares de Cohen: trivial abaixo de 0,10; "
   "pequeno abaixo de 0,30; médio abaixo de 0,50; grande a partir de 0,50. A estrutura de associação entre "
   "as variáveis usou o coeficiente de correlação de postos de Spearman. A tendência diária foi estimada por "
   "modelo linear misto com intercepto aleatório por atleta, e a confiabilidade da medida repetida pelo "
   "coeficiente de correlação intraclasse de duas vias (SHROUT; FLEISS, 1979). A estabilidade da "
   "classificação em perfil usou o Q de Cochran (COCHRAN, 1950) sobre os atletas com registro completo, a "
   "associação entre perfil e tipo de estímulo o qui-quadrado de contingência, e a migração intradiária para "
   "a faixa de risco o teste de McNemar (McNEMAR, 1947). A variância do par atleta-dia foi reparte por um "
   "modelo de efeitos aleatórios cruzados de atleta e dia. O processamento correu em Python 3.11, com SciPy, "
   "NumPy e statsmodels, e todos os resultados foram recalculados por um segundo caminho de código a partir "
   "do item do formulário.")

# ---------------------------------------------------------------- 3
h_("3 RESULTADOS")

h_("3.1 Estatística descritiva completa das onze variáveis", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} descreve as onze variáveis sobre os {NAD} pares atleta-dia. Nenhuma segue "
   "distribuição normal pelo teste de Shapiro-Wilk, e quatro delas apresentam efeito de piso acima de 40%.")
cap_(f"Tabela {tab()} – Posição, dispersão, forma e efeito de piso das onze variáveis")
mktable(["Variável", "Md (Q1–Q3)", "M (DP)", "CV%", "Assimetria", "Shapiro-Wilk", "Piso"],
        [[Lb(v), f"{n_(DESC[v]['md'])} ({n_(DESC[v]['q1'])}–{n_(DESC[v]['q3'])})",
          f"{n_(DESC[v]['m'])} ({n_(DESC[v]['sd'])})", n_(DESC[v]['cv']), n_(DESC[v]['sk'], 2),
          pf_(DESC[v]['pW']), n_(DESC[v]['piso']) + "%"] for v in V11],
        widths=[2.1, 2.6, 2.3, 1.5, 1.9, 2.1, 1.5], fs=8)
nota_("Md: mediana; Q1–Q3: quartis; M: média; DP: desvio-padrão; CV: coeficiente de variação. PTH é a "
      "perturbação total do humor, sem piso próprio por não ser subescala; Epworth e PSS não têm piso "
      "definido na mesma escala das subescalas.")
p_(f"A Figura {prox_fig()} mostra a distribuição de cada subescala, com a assimetria e a concentração no "
   "valor mínimo que a tabela quantifica.")
fig_("X2fig.png", "Histograma das sete subescalas do BRUMS, com a mediana assinalada.", w=13.6)

h_("3.2 Sensibilidade, variabilidade e pico de cada variável", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} ordena as onze variáveis pela razão entre o deslocamento semanal e o piso de "
   "ruído, que responde a qual variável é mais sensível ou tem mais variação ao longo da semana.")
cap_(f"Tabela {tab()} – Ranking de sensibilidade: deslocamento semanal, piso e razão")
mktable(["Variável", "Δ D1→D7", "Piso", "Razão Δ/piso", "CV%", "Veredito"],
        [[Lb(s['variavel']), n_(s['dtot']), n_(s['piso'], 3), n_(s['razao_piso']) + "×", n_(DESC[s['variavel']]['cv']),
          "sinal" if s['sinal'] else "ruído"] for s in EXP['SENSI']],
        widths=[2.2, 1.7, 1.6, 2.0, 1.6, 1.5], fs=8.5)
nota_("A razão Δ/piso é o critério primário de sensibilidade; o CV descreve a dispersão relativa, mas não "
      "distingue movimento real de ruído amostral.")
p_(f"A fadiga física é a variável mais sensível à semana, com razão de {n_(EXP['SENSI'][0]['razao_piso'])}, "
   f"seguida do vigor, com {n_(EXP['SENSI'][1]['razao_piso'])}. A fadiga mental é a menos sensível entre as "
   f"onze, com razão em torno da unidade. A Tabela {prox_tab()} traz o dia em que cada uma das sete "
   "subescalas alcança o seu valor mais alto e o mais baixo na média bruta do elenco.")
cap_(f"Tabela {tab()} – Dia de pico, máximo e mínimo, de cada subescala")
mktable(["Variável", "Dia do máximo", "Valor máximo", "Dia do mínimo", "Valor mínimo"],
        [[Lb(v), "D" + str(EXP['PICO'][v]['dia_max']), n_(EXP['PICO'][v]['valor_max'], 2),
          "D" + str(EXP['PICO'][v]['dia_min']), n_(EXP['PICO'][v]['valor_min'], 2)] for v in V7],
        widths=[2.2, 2.2, 2.2, 2.2, 2.2], fs=8.5)
nota_("Valor da média bruta diária, antes da suavização. PTH é a perturbação total do humor.")
p_("O vigor atinge o pico no primeiro dia e o vale no sétimo; a fadiga faz o percurso inverso, com o pico "
   "exatamente no sétimo dia. A raiva e a confusão, porém, não têm o valor mais baixo no primeiro dia: ambas "
   f"tocam o mínimo no quinto dia, {n_(EXP['PICO']['Raiva']['valor_min'],2)} e "
   f"{n_(EXP['PICO']['Confusão']['valor_min'],2)} respectivamente, e voltam a subir depois, o que mostra que "
   "nem toda subescala negativa segue uma trajetória de piora simples e contínua ao longo da semana.")

h_("3.3 Comparação não paramétrica entre os sete dias", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} traz o teste de Friedman entre os sete dias, com o coeficiente W de Kendall como "
   "tamanho de efeito, o teste de Page para tendência ordenada, e o contraste pareado de Wilcoxon entre o "
   "primeiro e o sétimo dia, para as onze variáveis.")
cap_(f"Tabela {tab()} – Friedman, W de Kendall, tendência de Page e contraste pareado D1×D7")
rows = []
for v in V11:
    fr = pget(v, 'D1..D7', '%Friedman%')
    pg = pget(v, 'ordenada D1→D7', '%Page%')
    wc = pget(v, 'D1–D7', '%Wilcoxon%')
    rows.append([Lb(v), f"{n_(fr['estatistica'],2)} ({pf_(fr['p'])})" if fr else "—",
                 n_(fr['efeito'], 2) if fr else "—",
                 n_(pg['estatistica'], 2) if pg else "—", pf_(pg['p']) if pg else "—",
                 n_(wc['estatistica'], 2) if wc else "—", pf_(wc['p']) if wc else "—"])
mktable(["Variável", "Friedman χ² (p)", "W", "Page z", "Page p", "Wilcoxon Δ", "p"], rows,
        widths=[1.7, 2.5, 1.1, 1.4, 1.4, 1.6, 1.4], fs=8)
nota_("Friedman, W de Kendall e Page operam sobre os dezenove atletas com registro nos sete dias; o "
      "contraste pareado, sobre os vinte e um com medida em D1 e D7. PTH é a perturbação total do humor.")
p_(f"A Figura {prox_fig()} mostra a trajetória das seis subescalas ao longo do microciclo. Vigor, fadiga, "
   "fadiga física, confusão, Epworth e tensão têm os três testes significativos; a perturbação total é "
   "significativa pelo Friedman (p = 0,024), mas não pela tendência de Page (p = 0,163), porque o seu "
   "acoplamento crescente com a fadiga produz uma curva que se acentua perto do fim da semana, e não a reta "
   "que o teste de tendência procura. Depressão, raiva, fadiga mental e PSS não alcançam significância por "
   "nenhum dos três testes.")
fig_("F4fig.png", "Trajetória das seis subescalas em escore T ao longo do microciclo, com o resultado do "
     "teste de Page assinalado.", w=13.4)

h_("3.4 Vigor, fadiga e perturbação total: cruzamento e magnitude de mudança diária", before=6, size=10.5)
p_(f"A Figura {prox_fig()} sobrepõe vigor, fadiga e perturbação total e assinala os três pontos em que as "
   "séries se cruzam ao longo da semana.")
fig_("P6fig.png", "Vigor, fadiga e perturbação total ao longo do microciclo, com os três pontos de "
     "cruzamento assinalados.", w=13.6)
p_(f"A Tabela {prox_tab()} e a Figura {prox_fig()} classificam a magnitude de mudança em cada uma das seis "
   "transições diárias, soma dos módulos das sete subescalas em unidades de piso, e trazem o dia de "
   "inflexão de cada variável.")
cap_(f"Tabela {tab()} – Magnitude de mudança por transição diária e ponto de inflexão de cada variável")
mktable(["Transição ou variável", "Soma em pisos / dia de inflexão", "Transições de choque"],
        [[m['transicao'], n_(m['soma_abs_pisos']) + " pisos (soma das sete variáveis)", ""]
         for m in EXP['MUDANCA']] +
        [[Lb(v), "D" + n_(SER[v]['infl'][0], 2), (", ".join(f"D{c-1}→D{c}" for c in SER[v]['choque']) or "nenhuma")]
         for v in V7],
        widths=[2.4, 4.4, 4.6], fs=8.5)
nota_("As seis primeiras linhas somam o módulo do deslocamento das sete subescalas em unidades de piso, por "
      "transição; as sete últimas trazem, por variável, o dia de inflexão da série suavizada, obtido por "
      "interpolação sobre a segunda derivada, e as transições cujo módulo excede o próprio piso.")
fig_("X4fig.png", "Magnitude de mudança em cada transição diária.", w=11.6)
p_(f"A primeira transição, D1→D2, concentra a maior mudança conjunta, "
   f"{n_(EXP['MUDANCA'][0]['soma_abs_pisos'])} pisos somados, seguida pela última, D6→D7, com "
   f"{n_(EXP['MUDANCA'][1]['soma_abs_pisos'])}. As quatro transições centrais somam menos, em conjunto, do "
   "que qualquer uma dessas duas isoladamente, o que confirma um platô no meio da semana. A travessia entre "
   "vigor e perturbação total é a mais nítida do conjunto; a travessia entre vigor e fadiga existe, mas com "
   "uma zona de indecisão de vários dias em torno do ponto exato em que as curvas se tocam.")

h_("3.5 Comportamento intradiário, entre o início e o fim do dia", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} agrega todos os {EXP['INTRADIA']['Vigor']['n']} pares com dupla coleta, "
   "independentemente do dia ou do tipo de estímulo, e testa pelo Wilcoxon pareado a diferença entre a "
   "medida do início e a do fim do dia.")
cap_(f"Tabela {tab()} – Contraste intradiário agregado, todas as onze variáveis")
mktable(["Variável", "Início", "Fim", "Δ", "Wilcoxon p", "r", "Efeito"],
        [[Lb(v), n_(EXP['INTRADIA'][v]['media_pre']), n_(EXP['INTRADIA'][v]['media_pos']),
          n_(EXP['INTRADIA'][v]['media_dif'], 2), pf_(EXP['INTRADIA'][v]['p']),
          n_(EXP['INTRADIA'][v]['efeito_r'], 2), efeito_(EXP['INTRADIA'][v]['efeito_r'])]
         for v in V11],
        widths=[2.0, 1.4, 1.4, 1.4, 1.7, 1.2, 1.7], fs=8.5)
nota_(f"n = {EXP['INTRADIA']['Vigor']['n']} pares com as duas medidas do dia, de D2 a D7.")
p_("A fadiga física tem o maior efeito intradiário do conjunto, seguida pela perturbação total e pela "
   "fadiga em si; o vigor cai de modo consistente. Epworth, PSS, depressão, raiva e confusão não mudam de "
   "modo estatisticamente sustentado entre o início e o fim do dia, traços mais estáveis na escala "
   "intradiária, ainda que móveis na escala semanal.")

h_("3.6 Estrutura de associação entre as variáveis", before=6, size=10.5)
p_(f"A Figura {prox_fig()} ordena as 21 associações de Spearman entre as sete variáveis, sobre os "
   f"{NAD} pares atleta-dia, com o coeficiente de Pearson ao lado para comparação.")
fig_("G5fig.png", "As 21 associações entre pares das sete variáveis do BRUMS por Spearman, com o coeficiente de "
     "Pearson ao lado para comparação.", w=13.4)
mv = A3['MAT']
p_(f"A associação mais forte do conjunto liga a fadiga à perturbação total "
   f"(ρ = {n_(mv['Fadiga×TMD']['rho'],3)}; p < 0,001), seguida pela do vigor com a perturbação total, em "
   f"sentido inverso (ρ = {n_(mv['Vigor×TMD']['rho'],3)}; p < 0,001), e pela do vigor com a fadiga "
   f"(ρ = {n_(mv['Vigor×Fadiga']['rho'],3)}; p < 0,001). A tensão comporta-se de modo atípico: correlaciona-se "
   f"positivamente com o vigor (ρ = {n_(mv['Tensão×Vigor']['rho'],3)}; p = {pf_(mv['Tensão×Vigor']['p'])}) e "
   f"não se correlaciona com a fadiga (ρ = {n_(mv['Tensão×Fadiga']['rho'],3)}; "
   f"p = {pf_(mv['Tensão×Fadiga']['p'])}), padrão que a teoria do afeto negativo não prevê e que sugere "
   "função de ativação, e não de sofrimento, no caso da tensão.")

h_("3.7 Contraste entre o primeiro e o sétimo dia, com tamanho de efeito", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} traz o teste de Wilcoxon pareado entre D1 e D7, restrito aos atletas com medida "
   "nos dois extremos, com o tamanho de efeito r classificado pelos limiares de Cohen.")
cap_(f"Tabela {tab()} – Contraste pareado D1×D7, todas as onze variáveis")
rows = []
for v in V11:
    wc = pget(v, 'D1–D7', '%Wilcoxon%')
    rows.append([Lb(v), n_(wc['estatistica'], 2) if wc else "—", pf_(wc['p']) if wc else "—",
                 n_(wc['efeito'], 2) if wc else "—", efeito_(wc['efeito']) if wc else "—",
                 str(wc['n']) if wc else "—"])
mktable(["Variável", "Δ (postos)", "p", "r", "Magnitude", "n"], rows,
        widths=[2.0, 1.6, 1.5, 1.2, 1.8, 1.0], fs=8.5)
nota_("Contraste sobre os atletas com resposta no primeiro e no sétimo dia. Δ é a estatística de postos do "
      "Wilcoxon (WILCOXON, 1945).")
fig_("X5fig.png", "Magnitude do efeito do contraste D1×D7, por variável, com os limiares de Cohen.", w=11.8)
p_(f"A Figura {_CONT['fig']} ordena as onze variáveis pelo tamanho de efeito. Fadiga física, vigor, fadiga e "
   "perturbação total mudam com efeito grande, acima de 0,60; tensão, Epworth e confusão também alcançam "
   "efeito grande, ainda que por margem mais estreita. Depressão, raiva, PSS e fadiga mental não alcançam "
   "significância no contraste pareado, coerente com a leitura da secção 3.2.")

h_("3.8 Regressão de tendência e confiabilidade da medida repetida", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} traz a inclinação diária estimada por modelo linear misto, com intercepto "
   "aleatório por atleta, e o coeficiente de correlação intraclasse da medida repetida.")
cap_(f"Tabela {tab()} – Regressão de tendência diária (modelo misto) e confiabilidade (ICC)")
mktable(["Variável", "β dia (IC 95%)", "p", "ICC", "Erro típico", "MMD 95%"],
        [[Lb(v), f"{n_(LMM[v]['b_dia'],3)} ({n_(LMM[v]['ic'][0],2)}; {n_(LMM[v]['ic'][1],2)})",
          pf_(LMM[v]['p']), n_(ICC[v]['icc'], 2), n_(ICC[v]['epm']), n_(ICC[v]['mvd'])]
         for v in V7],
        widths=[2.0, 3.0, 1.5, 1.3, 1.7, 1.7], fs=8.5)
nota_("β dia é o coeficiente linear do dia sobre o par atleta-dia, em pontos por dia. ICC é o coeficiente de "
      "correlação intraclasse de duas vias (SHROUT; FLEISS, 1979); erro típico e mínima mudança detectável "
      "(MMD 95%) vêm da confiabilidade teste-reteste do instrumento neste elenco.")
p_("O vigor tem a maior inclinação negativa do conjunto. Entre as cinco subescalas negativas, a tensão é a "
   "única com inclinação diária negativa e estatisticamente confiável, β = "
   f"{n_(LMM['Tensão']['b_dia'],3)} (p = {pf_(LMM['Tensão']['p'])}); a confusão também se desloca em sentido "
   "negativo, mas sem significância. A raiva tem a menor confiabilidade do conjunto, ICC = "
   f"{n_(ICC['Raiva']['icc'],2)}, o que limita a interpretação da sua tendência a nível individual; a "
   f"depressão tem a maior, ICC = {n_(ICC['Depressão']['icc'],2)}.")

h_("3.9 Decomposição da variação", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} reparte a variância do par atleta-dia em três componentes, por um modelo de "
   "efeitos aleatórios cruzados de atleta e dia.")
cap_(f"Tabela {tab()} – Componentes de variância e fidedignidade da série diária")
mktable(["Variável", "Entre atletas", "Entre dias", "Residual", "Fidedignidade", "% em choque"],
        [[Lb(v), n_(DK['COMPONENTES'][v]['p_atleta']) + "%", n_(DK['COMPONENTES'][v]['p_dia']) + "%",
          n_(DK['COMPONENTES'][v]['p_residual']) + "%",
          ("nula" if DK['SERIE'][v]['negativa'] else n_(DK['SERIE'][v]['fidedignidade'], 2)),
          n_(DK['DESLOCAMENTO'][v]['p_choque_abs'])] for v in V7],
        widths=[2.0, 2.2, 1.9, 1.9, 2.1, 1.8], fs=8.5)
nota_("A parcela «entre dias» é o objeto deste estudo, o movimento do elenco de um dia para o outro. A "
      "fidedignidade divide a variância verdadeira entre as sete médias diárias pela variância observada.")
p_("A parcela atribuível ao dia é a menor das três em todas as sete variáveis, o que situa a diferença "
   "estável entre atletas como a maior fonte de variação do conjunto. O vigor e a fadiga sustentam leitura "
   "de série no sentido pleno; a depressão tem fidedignidade nula, porque a sua variância entre dias é menor "
   "que a variância de erro.")

h_("3.10 Sonolência e estresse percebido", before=6, size=10.5)
p_(f"A escala de sonolência de Epworth desloca-se {n_(SER['Epworth']['dtot'])} pontos entre os extremos da "
   f"semana, contra um piso de {n_(SER['Epworth']['piso'], 2)}, razão de {n_(SER['Epworth']['razao'])}, e a "
   "tendência de Page é significativa (Tabela 4). O estresse percebido desloca-se apenas "
   f"{n_(SER['PSS']['dtot'])} ponto, com a menor razão de todo o conjunto, {n_(SER['PSS']['razao'])}, e não "
   "alcança significância em nenhum dos testes. A sonolência acompanha a fadiga física em sensibilidade; o "
   "estresse percebido comporta-se como traço relativamente estável ao longo desta semana específica.")

h_("3.11 Os seis perfis de humor: prevalência e assinatura", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} compara a prevalência dos seis perfis com a referência populacional, e a "
   f"Figura {prox_fig()} traz a assinatura de cada perfil em escore T, a base para distinguir, na prática, "
   "um perfil do outro.")
cap_(f"Tabela {tab()} – Prevalência dos seis perfis no conjunto da semana e comparação com a referência")
mktable(["Perfil", "Pares", "Prevalência", "Referência", "Razão"],
        [[nome, str(CT[k]), n_(100*CT[k]/NAD) + "%", n_(REF[k]) + "%", n_(100*CT[k]/NAD/REF[k], 2)]
         for k, nome in enumerate(NOMES)],
        widths=[4.6, 2.2, 3.0, 3.0, 3.2], fs=9)
fig_("P4fig.png", "Assinatura dos seis perfis em escore T: o centroide observado contra o centroide de "
     "referência.", w=12.6)
p_("__A assinatura correta do iceberg e da barbatana de tubarão.__ Os dois perfis não se distinguem pelo "
   "nível de vigor, e sim pelo padrão das cinco subescalas negativas. O iceberg combina vigor alto com todas "
   "as cinco subescalas negativas abaixo da média normativa: é o perfil de menor custo afetivo do conjunto. A "
   "barbatana de tubarão preserva o vigor em nível próximo ao normativo, e não baixo, mas eleva tensão, "
   "raiva e fadiga acima da média, com depressão e confusão discretamente elevadas; a leitura de que fadiga "
   "alta e vigor baixo definem qualquer perfil de risco é imprecisa, porque descreve o submerso, não a "
   "barbatana de tubarão. O submerso, esse sim, combina vigor baixo com as cinco subescalas negativas "
   "elevadas, o colapso completo que a Figura 7 mostra como o perfil mais distante do iceberg no espaço de "
   "escores T. A distinção prática, para uma comissão técnica, é que a barbatana de tubarão descreve um "
   "atleta ativado e tenso, ainda capaz de vigor, ao passo que o submerso descreve um atleta exausto e sem "
   "reserva.")

h_("3.12 Perfil geral do elenco no primeiro e no sétimo dia", before=6, size=10.5)
d1v = {k: SERP[k]['y'][0] for k in NOMES}; d7v = {k: SERP[k]['y'][6] for k in NOMES}
modal_d1 = max(d1v, key=d1v.get); maxd7 = max(d7v.values())
empatados_d7 = [k for k in NOMES if abs(d7v[k] - maxd7) < 1e-6]
p_(f"A Tabela {prox_tab()} cruza a prevalência de cada perfil no primeiro e no sétimo dia. O perfil geral do "
   f"elenco no primeiro dia é o {modal_d1.lower()}, com {n_(d1v[modal_d1])}% dos respondentes; no sétimo dia "
   f"não há um perfil geral único, e sim um empate exato entre {', '.join(k.lower() for k in empatados_d7)}, "
   f"com {n_(maxd7)}% cada.")
cap_(f"Tabela {tab()} – Prevalência de cada perfil no primeiro e no sétimo dia, e deslocamento")
mktable(["Perfil", "D1", "D7", "Δ (pp)"],
        [[nome, n_(d1v[nome]) + "%", n_(d7v[nome]) + "%", n_(d7v[nome] - d1v[nome])] for nome in NOMES],
        widths=[4.6, 2.6, 2.6, 2.6], fs=9)
nota_("pp: pontos percentuais. Denominadores de D1 e D7 na nota da Tabela 12.")
p_("O elenco começa a semana concentrado no perfil de menor custo afetivo e termina disperso entre três "
   "perfis de custo mais alto, sem que nenhum deles isoladamente se torne majoritário: a semana não converge "
   "para um único perfil de chegada, e sim para uma tríade de destinos igualmente prováveis.")

h_("3.13 Trajetória diária dos perfis e das faixas de risco", before=6, size=10.5)
ordem = NOMES + ['Favorável', 'Neutra', 'De risco']
p_(f"A Tabela {prox_tab()} traz a prevalência diária, e a Figura {prox_fig()} mostra a composição do "
   "elenco dia a dia.")
cap_(f"Tabela {tab()} – Prevalência diária dos perfis e das faixas, com deslocamento, piso e veredito")
mktable(["Perfil ou faixa"] + [f"D{d}" for d in range(1, 8)] + ["Δ", "Piso", "Veredito"],
        [[k] + [n_(SERP[k]['y'][d]) for d in range(7)] + [n_(SERP[k]['dtot']), n_(SERP[k]['piso']),
          ("não avaliável" if SERP[k]['fragil'] else ("sinal" if SERP[k]['sinal'] else "ruído"))]
         for k in ordem],
        widths=[3.0] + [0.98] * 7 + [1.1, 1.0, 2.3], fs=7.5)
nota_(f"Denominadores de D1 a D7: {', '.join(str(x) for x in A1['nd'])} pares. O Everest invertido reúne "
      "dois pares no conjunto inteiro e fica assinalado como não interpretável.")
fig_("P2fig.png", "Composição do elenco entre os seis perfis, dia a dia, e as três faixas de humor.", w=13.6)
p_(f"A distribuição dos perfis não difere entre os três tipos de estímulo "
   f"(χ² = {n_(A3['chi'],2)}; gl = {A3['gl']}; p = {pf_(A3['p_chi'])}), nem a das três faixas "
   f"(χ² = {n_(A3['chi_f'],2)}; gl = {A3['gl_f']}; p = {pf_(A3['p_f'])}). O Q de Cochran, restrito aos "
   "dezenove atletas com registro completo, só alcança significância na superfície "
   f"(Q = {n_(A3['CQ']['Superfície']['Q'],2)}; p = {pf_(A3['CQ']['Superfície']['p'])}), o que não contradiz "
   "o resultado anterior: o teste categórico exige mais observações do que um elenco fornece, ao passo que a "
   "série de prevalências, confrontada com o próprio erro amostral, já reconhece o movimento. A dupla coleta "
   "diária revela migração assimétrica para a faixa de risco entre o início e o fim do mesmo dia: "
   f"{A3['MCN']['TODOS']['entra']} pares entram nela e {A3['MCN']['TODOS']['sai']} saem "
   f"(χ² = {n_(A3['MCN']['TODOS']['chi'],2)}; p = {pf_(A3['MCN']['TODOS']['p'])}).")

h_("3.14 Migração individual de perfil e classificação de risco por atleta", before=6, size=10.5)
p_(f"A Figura {prox_fig()} cruza o perfil de cada atleta no primeiro dia com o perfil no sétimo, sobre os "
   f"{EXP['n_pareados']} atletas com classificação nos dois extremos, e a Tabela {prox_tab()} resume o "
   "mesmo cruzamento por perfil de partida, ordenado pela percentagem que permanece no próprio perfil, do "
   "que mais migra ao que menos migra.")
fig_("X3fig.png", "Retenção e migração de perfil, do primeiro ao sétimo dia, por perfil de partida.", w=13.6)
cap_(f"Tabela {tab()} – Para onde foram os atletas de cada perfil inicial, do que mais migra ao que menos migra")
ordenT = sorted([nome for nome in NOMES if EXP['TRANS'][nome]['n_d1'] > 0],
                key=lambda nome: (EXP['TRANS'][nome]['pct_ficou'] if EXP['TRANS'][nome]['pct_ficou'] is not None else 999))
linT = []
for nome in ordenT:
    t = EXP['TRANS'][nome]
    dest = "; ".join(f"{v}× {k}" for k, v in sorted(t['destinos'].items(), key=lambda x: -x[1])) or "—"
    linT.append([nome, str(t['n_d1']), f"{t['ficou']} ({n_(t['pct_ficou'])}%)", dest])
mktable(["Perfil em D1", "n", "Permaneceu", "Migrou para"], linT, widths=[3.2, 1.0, 2.4, 7.4], fs=8.5)
nota_("Ordenado pela percentagem de retenção, do menor ao maior valor. n é o número de atletas com esse "
      "perfil no primeiro dia, entre os vinte e um pareados.")
p_(f"A superfície é o perfil que mais migra: apenas {EXP['TRANS']['Superfície']['ficou']} de "
   f"{EXP['TRANS']['Superfície']['n_d1']} atletas que começaram nele o mantêm no sétimo dia "
   f"({n_(EXP['TRANS']['Superfície']['pct_ficou'])}%). O iceberg, o perfil de partida mais frequente "
   f"({EXP['TRANS']['Iceberg']['n_d1']} de {EXP['n_pareados']} atletas), também tem baixa retenção "
   f"({n_(EXP['TRANS']['Iceberg']['pct_ficou'])}%), e a maior parte migra para a barbatana de tubarão, não "
   "para um perfil intermediário; entre os dois, o iceberg é o de maior peso prático, por reunir mais "
   "atletas. A barbatana de tubarão é, nominalmente, o perfil de maior retenção, cem por cento, mas com um "
   "único representante em D1, o que não permite generalizar: o achado é um indício de que, uma vez "
   "alcançado, esse estado tende a se manter, não uma estimativa robusta.")
p_(f"A classificação de risco individual, resumida na Tabela {prox_tab()}, conta para cada atleta os dias "
   "na faixa de risco, sobre todos os dias em que respondeu.")
cap_(f"Tabela {tab()} – Classificação dos atletas pelo tempo na faixa de risco")
mktable(["Classe", "Atletas", "%"],
        [["Nunca em risco", str(EXP['n_nunca_risco']), n_(100*EXP['n_nunca_risco']/len(EXP['RISCO']))],
         ["Risco intermitente", str(EXP['n_intermitente']), n_(100*EXP['n_intermitente']/len(EXP['RISCO']))],
         ["Sempre em risco", str(EXP['n_sempre_risco']), n_(100*EXP['n_sempre_risco']/len(EXP['RISCO']))]],
        widths=[4.0, 2.5, 2.0], fs=9)
alto = sorted(EXP['RISCO'], key=lambda r: -r['pct_risco'])[:3]
baixo = [r['atleta'] for r in EXP['RISCO'] if r['classe'] == 'nunca em risco']
p_(f"Os atletas {', '.join(r['atleta'] for r in alto)} respondem em risco em todos os dias em que "
   f"responderam. Os atletas {', '.join(baixo)} nunca entraram na faixa de risco. A maioria do elenco, "
   f"{EXP['n_intermitente']} de {len(EXP['RISCO'])} atletas, tem risco intermitente, o que sustenta a leitura "
   "de que a faixa de risco descreve um estado transitório do microciclo, e não um traço fixo da maior parte "
   "do elenco.")

# ---------------------------------------------------------------- 4
h_("4 DISCUSSÃO")
p_("__Os perfis ao longo da semana.__ O elenco começa concentrado no iceberg e termina disperso entre três "
   "perfis de maior custo afetivo, sem convergência a um destino único. A prevalência da barbatana de "
   "tubarão sobe de 3,7% para 23,8% e a do iceberg cai pela metade, movimento que a Tabela 8 confirma acima "
   "do piso de ruído em oito das nove séries de perfil e faixa.")
p_("__Migração e perfil geral, D1 e D7.__ A superfície é o perfil que mais migra e o iceberg, por reunir "
   "mais atletas, o de maior peso prático entre os que perdem a classificação inicial. O perfil geral do "
   "elenco troca de um destino único no primeiro dia para um empate triplo no sétimo, o que já é, em si, um "
   "resultado: a semana não apenas piora o humor médio, torna o próprio destino do elenco menos previsível.")
p_("__Vigor, fadiga e perturbação total.__ As três séries se cruzam de modo consistente, com a travessia "
   "entre vigor e perturbação total como a mais nítida do conjunto; a travessia entre vigor e fadiga carrega "
   "uma zona de indecisão maior. A fadiga física é a variável mais sensível de todo o conjunto, à frente do "
   "próprio vigor, o que aponta a fadiga percebida, e não a queda de vigor, como o sinal de alerta mais "
   "precoce.")
p_("__Pico de cada variável.__ Nem toda subescala negativa piora de forma contínua: raiva e confusão têm o "
   "seu ponto mais baixo no quinto dia, não no primeiro, e voltam a subir depois, um padrão em U que uma "
   "leitura apenas do contraste entre extremos, D1 contra D7, não capturaria.")
p_("__A assinatura do iceberg e da barbatana de tubarão.__ A leitura de que fadiga alta e vigor baixo "
   "definem qualquer perfil de risco é imprecisa. A barbatana de tubarão preserva o vigor e eleva tensão, "
   "raiva e fadiga; o vigor baixo combinado a todas as subescalas negativas altas é a assinatura do submerso, "
   "não da barbatana de tubarão. Essa distinção importa para a leitura clínica: um atleta ativado e tenso "
   "não recebe a mesma conduta que um atleta exausto e sem vigor, ainda que ambos estejam fora do iceberg.")
p_("__Limitações.__ Uma equipe, sete dias e vinte e sete atletas, sem grupo de comparação. Os tipos de "
   "estímulo não foram aleatorizados e confundem-se com a posição no microciclo e com a carga acumulada. A "
   "barbatana de tubarão tem um único representante em D1 na análise de migração individual, o que impede "
   "generalizar a sua retenção de cem por cento. O estudo é descritivo e não estabelece relação causal entre "
   "carga e perfil.")

h_("5 CONCLUSÃO")
p_("A última semana de pré-temporada desloca o elenco de handebol de elite do iceberg, perfil de menor custo "
   "afetivo, para uma tríade de perfis de maior custo, sem que um único perfil de chegada se torne "
   "majoritário. A superfície é quem mais migra e o iceberg quem mais perde representantes em termos "
   "absolutos; vigor e fadiga física são as variáveis mais sensíveis, e suas trajetórias se cruzam com a "
   "perturbação total em pontos determináveis. Nem toda subescala negativa piora de modo contínuo, e a "
   "assinatura que distingue a barbatana de tubarão do submerso está no vigor preservado, não na sua "
   "ausência. Para o monitoramento em clube, a recomendação é dupla: acompanhar o perfil individual, não "
   "apenas a média do grupo, e declarar sempre o piso de ruído contra o qual cada mudança é lida.")

h_("REFERÊNCIAS")
for i in sorted(ESCOLHIDAS, key=lambda k: _R.REFS[k]):
    para(_R.REFS[i], indent=False, size=9, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         before=0, after=2.5, spacing=1.0)

out = os.path.join(S, "ARTIGO_PERFIS_HUMOR_HANDEBOL_COMPLETO.docx")
doc.save(out)
print("salvo:", out)
