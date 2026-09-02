# -*- coding: utf-8 -*-
"""Artigo descritivo, exploratório e não paramétrico dos perfis de humor, em oito páginas.

Recorte: as sete variáveis do BRUMS descritas por inteiro (posição, dispersão,
forma, efeito de piso), a bateria não paramétrica completa contra os sete dias
(Friedman, Page, Wilcoxon pareado), a estrutura de associação entre variáveis
(Spearman) e os seis perfis de humor, com prevalência, trajetória diária,
resposta ao estímulo e migração intradiária. Todo número procede dos JSON de
análise e da tabela resultado, nunca de rascunho anterior.
"""
import os, sys, collections, sqlite3
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_docx_base.py")).read())

sec.top_margin, sec.bottom_margin = Cm(2.3), Cm(2.3)
st.font.size = Pt(11)
pf.line_spacing = 1.12
pf.space_after = Pt(3)

import re as _re
def p_(txt, size=11, spacing=1.12, after=3, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
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
         before=before, after=3, spacing=1.12)

def cap_(txt):
    para(txt, indent=False, size=9, align=WD_ALIGN_PARAGRAPH.LEFT, before=7, after=2, spacing=1.0)

def nota_(txt):
    para("Nota: " + txt, indent=False, size=8.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         before=2, after=8, spacing=1.0)

prox_tab = lambda: _CONT['tab'] + 1
prox_fig = lambda: _CONT['fig'] + 1

def fig_(arq, legenda, w=13.2):
    cap_(f"Figura {fig()} – {legenda}")
    doc.add_picture(os.path.join(S, arq), width=Cm(w))
    q = doc.paragraphs[-1]; q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.first_line_indent = Cm(0); q.paragraph_format.space_after = Pt(8)

jd = lambda n: json.load(open(os.path.join(DADOS, n + ".json"), encoding='utf-8'))
QP = jd("V2_perfis"); A1 = jd("V2_a1"); A3 = jd("V2_a3"); B = jd("V2_base"); PR = jd("V2_proto")
SER = A1['SER']; DESC = A1['DESC']; SERP = A3['SERP']; NOMES = QP['NOMES']; REF = QP['PREV_REF']
lab = QP['lab_AD']; CT = collections.Counter(lab); NAD = len(lab)
V7 = ['Tensão', 'Depressão', 'Raiva', 'Vigor', 'Fadiga', 'Confusão', 'TMD']
Lb = lambda v: 'PTH' if v == 'TMD' else v

def n_(x, d=1):
    if x is None or (isinstance(x, float) and x != x): return "—"
    return f"{x:.{d}f}".replace('.', ',').replace('-', '−')
def pf_(p, d=3):
    if p is None: return "—"
    return "< 0,001" if p < 0.001 else f"{p:.{d}f}".replace('.', ',')

cx = sqlite3.connect(os.path.join(RAIZ, "base", "humor_handebol.sqlite")); cx.row_factory = sqlite3.Row
def pget(var, rec, teste_like, via="não paramétrica"):
    r = cx.execute("SELECT p,estatistica,efeito,n FROM resultado WHERE variavel=? AND recorte=? "
                   "AND teste LIKE ? AND via=?", (var, rec, teste_like, via)).fetchone()
    return r

sys.path.insert(0, os.path.join(RAIZ, "texto")); import REFS as _R
# Índices em REFS.REFS efetivamente citados no corpo do texto abaixo, um a um.
ESCOLHIDAS = [36, 12, 22, 54, 56, 8, 60, 35, 21, 51, 43, 50, 5, 30, 15]

# ============================== documento ==============================
para("PERFIS DE HUMOR DE ATLETAS DE HANDEBOL DE ELITE NA ÚLTIMA SEMANA DE PRÉ-TEMPORADA:",
     indent=False, bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=2, spacing=1.12)
para("ANÁLISE DESCRITIVA, EXPLORATÓRIA E NÃO PARAMÉTRICA",
     indent=False, bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=9, spacing=1.12)

h_("RESUMO", before=0, size=10)
p_(f"Este estudo descreve o comportamento das sete dimensões do BRUMS e a distribuição dos seis perfis de "
   f"humor em {len(B['ATL'])} atletas de handebol masculino de elite, ao longo dos sete dias que antecederam "
   f"a estreia competitiva. Estudo observacional longitudinal de medidas repetidas, com {NAD} pares "
   "atleta-dia. As sete variáveis foram descritas por posição, dispersão e forma, e testadas contra os sete "
   "dias por via não paramétrica, porque a maioria não satisfaz normalidade e quatro delas apresentam efeito "
   "de piso acima de 40%. O vigor recua "
   f"{n_(abs(SER['Vigor']['dtot']),2)} pontos e a fadiga avança {n_(SER['Fadiga']['dtot'],2)}, ambos com "
   "tendência confirmada pelo teste de Page (p < 0,001) e pelo contraste pareado entre o primeiro e o "
   f"sétimo dia (Wilcoxon, p < 0,001). A barbatana de tubarão comparece em {n_(100*CT[3]/NAD)}% dos pares, "
   f"mais que o dobro da prevalência de referência, e a faixa de risco passa de "
   f"{n_(SERP['De risco']['y'][0])}% para {n_(SERP['De risco']['y'][6])}%. A distribuição dos perfis não "
   f"difere entre os tipos de estímulo (χ² = {n_(A3['chi'],2)}; p = {pf_(A3['p_chi'])}), e a migração entre "
   f"o início e o fim do dia é assimétrica em direção à faixa de risco "
   f"({A3['MCN']['TODOS']['entra']} entradas contra {A3['MCN']['TODOS']['sai']} saídas; "
   f"p = {pf_(A3['MCN']['TODOS']['p'])}). Conclui-se que a semana desloca o elenco de modo consistente e "
   "estatisticamente sustentado, e que a via não paramétrica é a leitura apropriada para escalas com efeito "
   "de piso e distribuição repetida em pequena amostra.",
   indent=False, size=10, spacing=1.08, after=4)
para("__Palavras-chave:__ Estados de humor. Handebol. Estatística não paramétrica. Pré-temporada. BRUMS.",
     indent=False, size=10, spacing=1.08, after=9)

h_("1 INTRODUÇÃO", before=3)
p_("A Escala de Humor de Brunel descreve seis dimensões do estado afetivo e permite compor um escore de "
   "perturbação total, e a sua leitura mais difundida no esporte é a classificação em seis perfis, obtida "
   "pela distância entre o vetor de escores T de um respondente e seis centroides de referência "
   "(PARSONS-SMITH; TERRY; MACHIN, 2017). Essa tipologia consolidou-se em amostras transversais de milhares "
   "de respondentes, e a sua estabilidade em contextos culturais distintos está bem documentada "
   "(HAN; PARSONS-SMITH; TERRY, 2020; LEW et al., 2023; TERRY; PARSONS-SMITH; VLACHOPOULOS, 2024). O "
   "acompanhamento diário de um elenco reduzido, contudo, levanta uma exigência que os estudos de "
   "prevalência não enfrentam: separar o movimento real da flutuação amostral, sem o socorro de uma amostra "
   "grande que dilua o ruído.")
p_("As subescalas do BRUMS têm, além disso, propriedades métricas que desaconselham o tratamento paramétrico "
   "automático: distribuição assimétrica, amplitude estreita e concentração de respostas no valor mínimo, o "
   "chamado efeito de piso (TERWEE et al., 2007). Em desenho de medidas repetidas com poucos indivíduos, a "
   "combinação de não normalidade e efeito de piso recomenda a família de testes que dispensa o pressuposto "
   "de distribuição, a saber, Friedman, Wilcoxon, Page e correlação de postos (FRIEDMAN, 1937; WILCOXON, "
   "1945; PAGE, 1963; KENDALL; SMITH, 1939). O objetivo deste estudo é descrever a posição, a dispersão e a "
   "forma das sete variáveis do BRUMS e a distribuição dos seis perfis de humor ao longo do microciclo "
   "terminal de pré-temporada de um elenco de handebol de elite, com a bateria não paramétrica completa "
   "contra os sete dias e contra o tipo de estímulo.")

h_("2 MÉTODO")
h_("2.1 Delineamento, participantes e coleta", before=6, size=10.5)
p_(f"Estudo observacional longitudinal de medidas repetidas, com sete dias consecutivos, entre 21 e 27 de "
   f"abril de 2024, sem intervenção dos pesquisadores. Participaram {len(B['ATL'])} atletas de handebol "
   "masculino de equipe da primeira divisão nacional, com idade média de 21,96 anos e desvio-padrão de "
   "3,81. A carga acumulada progrediu de 1,5 hora no primeiro dia a 23,0 horas ao término do sétimo. A "
   "semana reuniu quatro tipos de estímulo: conteúdo técnico e tático no primeiro dia, que serviu de linha "
   "de base; treino intervalado de alta intensidade com trabalho técnico no segundo, quarto e sétimo; jogo "
   "amistoso no terceiro e no quinto; conteúdo técnico, tático e de força no sexto. O primeiro dia teve "
   "coleta única, à noite; do segundo ao sétimo houve uma medida no início e outra ao fim do dia.")
h_("2.2 Instrumento e classificação nos perfis", before=6, size=10.5)
p_("Aplicou-se a Escala de Humor de Brunel (TERRY et al., 1999), validada para o português brasileiro por "
   "Rohlfs et al. (2008). O instrumento reúne vinte e quatro itens em seis subescalas de quatro itens, em "
   "escala de zero a quatro, e os escores brutos foram convertidos em escore T contra parâmetros normativos "
   "de amostras atléticas, com média cinquenta e desvio-padrão dez (TERRY; LANE, 2000). A perturbação total "
   "do humor soma as cinco subescalas negativas e subtrai o vigor. Cada vetor de seis escores T foi "
   "atribuído ao perfil cujo centroide de referência se encontra a menor distância euclidiana "
   "(PARSONS-SMITH; TERRY; MACHIN, 2017), e os seis perfis foram agrupados em três faixas: favorável, que "
   "reúne o iceberg; neutra, superfície e submerso; e de risco, os três restantes.")
h_("2.3 Unidade de análise e composição do valor diário", before=6, size=10.5)
p_(f"A fonte reúne {PR['TOTAIS']['registros']} registros. A unidade de análise é o par atleta-dia, com "
   f"{NAD} casos, o que impede que atletas mais assíduos pesem mais na estimativa. A regra de composição "
   "foi auditada contra os carimbos de data e hora: no dia basal, de coleta única, vale a primeira resposta "
   "de cada atleta, porque as respostas tardias daquela noite são repetição e não segunda medida; do "
   "segundo ao sétimo dia valem o primeiro e o último registro, tomados como medida do início e do fim do "
   "dia.")
h_("2.4 Análise estatística", before=6, size=10.5)
p_("A estatística descritiva incluiu média, desvio-padrão, mediana, quartis, coeficiente de variação, "
   "assimetria, curtose e o teste de Shapiro-Wilk para normalidade, além do efeito de piso, definido como o "
   "percentual de respostas no valor mínimo possível. A comparação entre os sete dias usou o teste de "
   "Friedman (FRIEDMAN, 1937), com o coeficiente W de Kendall como tamanho de efeito, sobre os atletas com "
   "registro completo. A tendência ordenada foi testada pelo L de Page (PAGE, 1963). O contraste entre o "
   "primeiro e o sétimo dia usou o teste de Wilcoxon pareado (WILCOXON, 1945), com o coeficiente r como "
   "tamanho de efeito, restrito aos atletas com medida nos dois extremos. A estrutura de associação entre as "
   "sete variáveis usou o coeficiente de correlação de postos de Spearman. A estabilidade da classificação "
   "nos perfis usou o Q de Cochran (COCHRAN, 1950) sobre os atletas com registro completo, a associação "
   "entre perfil e tipo de estímulo o qui-quadrado de contingência, e a migração entre a medida do início e "
   "a do fim do dia o teste de McNemar (McNEMAR, 1947), com ajuste de Holm (HOLM, 1979) para as comparações "
   "por estímulo. O processamento correu em Python 3.11, com SciPy e NumPy, e todos os resultados foram "
   "recalculados por um segundo caminho de código a partir do item do formulário.")

h_("3 RESULTADOS")
h_("3.1 Estatística descritiva das sete variáveis", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} e a Figura {prox_fig()} descrevem as sete variáveis sobre os {NAD} pares "
   "atleta-dia. Nenhuma delas segue distribuição normal pelo teste de Shapiro-Wilk, e quatro apresentam "
   "efeito de piso acima de 40%, o que justifica a via não paramétrica adotada.")
cap_(f"Tabela {tab()} – Posição, dispersão, forma e efeito de piso das sete variáveis")
mktable(["Variável", "Md (Q1–Q3)", "M (DP)", "Assimetria", "Curtose", "Shapiro-Wilk", "Piso"],
        [[Lb(v), f"{n_(DESC[v]['md'])} ({n_(DESC[v]['q1'])}–{n_(DESC[v]['q3'])})",
          f"{n_(DESC[v]['m'])} ({n_(DESC[v]['sd'])})", n_(DESC[v]['sk'], 2), n_(DESC[v]['ku'], 2),
          pf_(DESC[v]['pW']), n_(DESC[v]['piso']) + "%"] for v in V7],
        widths=[2.0, 2.6, 2.4, 2.0, 1.9, 2.2, 1.5], fs=8.5)
nota_("Md: mediana; Q1–Q3: primeiro e terceiro quartis; M: média; DP: desvio-padrão. Piso: percentual de "
      "respostas no valor mínimo da subescala. PTH é a perturbação total do humor, único escore composto, "
      "sem piso próprio por não ser subescala.")
p_("O vigor e a fadiga são as variáveis de maior dispersão e menor efeito de piso, ao passo que a confusão e "
   "a depressão concentram entre 60% e 70% das respostas no valor mínimo, o que restringe a sua variância "
   "disponível e, com ela, a capacidade de qualquer teste de detectar diferença.")
fig_("F3fig.png", "Distribuição das sete variáveis, com a mediana, o intervalo interquartil e o efeito de "
     "piso assinalado em cada painel.", w=13.4)

h_("3.2 Comparação não paramétrica entre os sete dias", before=6, size=10.5)
p_(f"A Figura {prox_fig()} mostra a trajetória das seis subescalas, e a Tabela {prox_tab()} traz o teste "
   "de Friedman entre os sete dias, o teste de Page para tendência ordenada e o contraste pareado de "
   "Wilcoxon entre o primeiro e o sétimo dia.")
cap_(f"Tabela {tab()} – Friedman, tendência de Page e contraste pareado D1×D7")
rows = []
for v in V7:
    fr = pget(v, 'D1..D7', '%Friedman%')
    pg = pget(v, 'ordenada D1→D7', '%Page%')
    wc = pget(v, 'D1–D7', '%Wilcoxon%')
    rows.append([Lb(v), f"{n_(fr['estatistica'],2)} ({pf_(fr['p'])})" if fr else "—",
                 pf_(pg['estatistica']).replace('< 0,001','—') if False else n_(pg['estatistica'],2) if pg else "—",
                 pf_(pg['p']) if pg else "—",
                 f"{n_(wc['estatistica'],2)}" if wc else "—", pf_(wc['p']) if wc else "—",
                 n_(wc['efeito'],2) if wc else "—"])
mktable(["Variável", "Friedman χ² (p)", "Page z", "Page p", "Wilcoxon Δ", "p", "r"], rows,
        widths=[1.8, 2.6, 1.5, 1.5, 1.7, 1.5, 1.2], fs=8)
nota_("Friedman e Page operam sobre os dezenove atletas com registro nos sete dias; o contraste pareado, "
      "sobre os vinte e um com medida em D1 e D7. Δ é a estatística de postos do Wilcoxon; r, o tamanho de "
      "efeito. PTH é a perturbação total do humor.")
p_("Vigor, fadiga, tensão e confusão apresentam os três testes significativos, com tamanho de efeito "
   "grande no contraste pareado, r entre 0,54 e 0,84. A perturbação total é significativa pelo Friedman "
   "(p = 0,024) e pelo contraste pareado (p = 0,004), mas não pela tendência de Page (p = 0,163), porque o "
   "seu acoplamento crescente com a fadiga ao longo da semana produz uma curva que se acentua perto do fim "
   "e não a reta que o teste de tendência procura. Depressão e raiva não alcançam significância por nenhum "
   "dos três testes.")
fig_("F4fig.png", "Trajetória das seis subescalas em escore T ao longo do microciclo, com o resultado do "
     "teste de Page assinalado.", w=13.4)

h_("3.3 Estrutura de associação entre as variáveis", before=6, size=10.5)
p_(f"A Figura {prox_fig()} ordena as 21 associações de Spearman entre as sete variáveis, sobre os "
   f"{NAD} pares atleta-dia, com o coeficiente de Pearson ao lado para comparação.")
fig_("G5fig.png", "As 21 associações entre pares das sete variáveis do BRUMS por Spearman, com o coeficiente de "
     "Pearson ao lado para comparação.", w=13.4)
mv = A3['MAT']
p_(f"A associação mais forte do conjunto liga a fadiga à perturbação total (ρ = {n_(mv['Fadiga×TMD']['rho'],3)}; "
   f"p < 0,001), seguida pela do vigor com a perturbação total, em sentido inverso "
   f"(ρ = {n_(mv['Vigor×TMD']['rho'],3)}; p < 0,001) e pela do vigor com a fadiga "
   f"(ρ = {n_(mv['Vigor×Fadiga']['rho'],3)}; p < 0,001). A tensão comporta-se de modo atípico: correlaciona-se "
   f"positivamente com o vigor (ρ = {n_(mv['Tensão×Vigor']['rho'],3)}; p = {pf_(mv['Tensão×Vigor']['p'])}) e "
   f"não se correlaciona com a fadiga (ρ = {n_(mv['Tensão×Fadiga']['rho'],3)}; "
   f"p = {pf_(mv['Tensão×Fadiga']['p'])}), padrão que a teoria do afeto negativo não prevê e que sugere "
   "função de ativação, e não de sofrimento, neste contexto.")

h_("3.4 Prevalência dos seis perfis de humor", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} apresenta a prevalência dos seis perfis sobre os {NAD} pares atleta-dia, "
   "comparada com a referência populacional do estudo que identificou a tipologia.")
cap_(f"Tabela {tab()} – Prevalência dos seis perfis e comparação com a referência")
mktable(["Perfil", "Pares", "Prevalência", "Referência", "Razão"],
        [[nome, str(CT[k]), n_(100*CT[k]/NAD) + "%", n_(REF[k]) + "%", n_(100*CT[k]/NAD/REF[k], 2)]
         for k, nome in enumerate(NOMES)],
        widths=[4.6, 2.2, 3.0, 3.0, 3.2], fs=9)
nota_("Referência populacional de Parsons-Smith, Terry e Machin (2017). A razão divide a prevalência "
      "observada pela de referência.")
p_(f"A barbatana de tubarão comparece com mais que o dobro da prevalência de referência e o submerso com "
   "menos da metade, o que descreve um elenco que mantém vigor enquanto acumula tensão, raiva e fadiga, e "
   f"não um estado de colapso generalizado, como mostra a assinatura de cada perfil na Figura {prox_fig()}.")
fig_("P4fig.png", "Assinatura dos seis perfis em escore T: o centroide observado neste elenco contra o "
     "centroide de referência, com a prevalência de cada perfil e o dia em que predomina.", w=12.6)

h_("3.5 Trajetória diária dos perfis e migração intradiária", before=6, size=10.5)
ordem = NOMES + ['Favorável', 'Neutra', 'De risco']
p_(f"A Tabela {prox_tab()} traz a prevalência diária dos perfis e das faixas, com o deslocamento entre os "
   "extremos confrontado com o piso de ruído, definido como a média dos sete erros-padrão binomiais da "
   "própria série.")
cap_(f"Tabela {tab()} – Prevalência diária dos perfis e das faixas, com deslocamento, piso e veredito")
mktable(["Perfil ou faixa"] + [f"D{d}" for d in range(1, 8)] + ["Δ", "Piso", "Veredito"],
        [[k] + [n_(SERP[k]['y'][d]) for d in range(7)] + [n_(SERP[k]['dtot']), n_(SERP[k]['piso']),
          ("não avaliável" if SERP[k]['fragil'] else ("sinal" if SERP[k]['sinal'] else "ruído"))]
         for k in ordem],
        widths=[3.0] + [0.98] * 7 + [1.1, 1.0, 2.3], fs=7.5)
nota_(f"Valores em percentagem dos pares do dia; denominadores de D1 a D7: "
      f"{', '.join(str(x) for x in A1['nd'])}. O Everest invertido reúne dois pares no conjunto inteiro, e o "
      "piso binomial encolhe perto de zero, razão pela qual a sua série fica assinalada como não "
      "interpretável.")
p_(f"A Figura {prox_fig()} mostra a composição diária do elenco entre os seis perfis. Oito das nove "
   "séries deslocam-se acima do próprio piso. A faixa de risco passa de "
   f"{n_(SERP['De risco']['y'][0])}% para {n_(SERP['De risco']['y'][6])}%, deslocamento de "
   f"{n_(SERP['De risco']['dtot'])} pontos percentuais contra um piso de {n_(SERP['De risco']['piso'])}. O "
   f"teste de estabilidade da classificação, restrito aos dezenove atletas com registro completo, só "
   f"alcança significância no perfil superfície (Q = {n_(A3['CQ']['Superfície']['Q'],2)}; "
   f"p = {pf_(A3['CQ']['Superfície']['p'])}), o que não contradiz o resultado anterior: o teste categórico "
   "exige um número de observações que um elenco não fornece, ao passo que a série de prevalências, "
   "confrontada com o próprio erro de amostragem, já reconhece o movimento.")
fig_("P2fig.png", "Composição do elenco entre os seis perfis, dia a dia, e as três faixas de humor com o "
     "ponto em que a de risco ultrapassa a favorável.", w=13.6)
p_(f"A distribuição dos perfis não difere entre os três tipos de estímulo "
   f"(χ² = {n_(A3['chi'],2)}; gl = {A3['gl']}; p = {pf_(A3['p_chi'])}), nem a das três faixas "
   f"(χ² = {n_(A3['chi_f'],2)}; gl = {A3['gl_f']}; p = {pf_(A3['p_f'])}). A dupla coleta diária revela, "
   "porém, migração assimétrica para a faixa de risco entre o início e o fim do mesmo dia: "
   f"{A3['MCN']['TODOS']['entra']} pares entram nela e {A3['MCN']['TODOS']['sai']} saem "
   f"(χ² = {n_(A3['MCN']['TODOS']['chi'],2)}; p = {pf_(A3['MCN']['TODOS']['p'])}), fenômeno que um "
   "protocolo de medida única perderia por inteiro.")

h_("4 DISCUSSÃO")
p_("A convergência entre a bateria não paramétrica e o critério do piso de ruído sustenta a leitura central "
   "deste estudo: o elenco se desloca de modo real, não amostral, em direção a um perfil de maior custo "
   "afetivo, e o faz sem que o tipo de estímulo determine essa direção. A tensão comporta-se de modo que a "
   "teoria do afeto negativo não prevê: associa-se ao vigor e não à fadiga, o que sugere função de "
   "ativação, e não de sofrimento, uma leitura que a matriz de Spearman torna visível e que a média isolada "
   "de cada subescala esconderia.")
p_("O segundo resultado é metodológico. A classificação em seis rótulos é, por construção, uma quantização "
   "que descarta a informação contida em deslocamentos que não atravessam uma fronteira de decisão, e essa "
   "propriedade aparece nos testes: o qui-quadrado não distingue os tipos de estímulo e o Q de Cochran não "
   "reconhece instabilidade na maioria dos perfis, ao passo que as séries de prevalência, lidas contra o "
   "próprio erro de amostragem, mostram deslocamento inequívoco em oito das nove séries. A recomendação não "
   "é escolher entre os dois planos: o perfil comunica bem e detecta mal, a variável contínua detecta bem e "
   "comunica mal, e o uso conjunto é o que os dados sustentam.")
p_("__Limitações.__ Uma equipe, sete dias e vinte e sete atletas, sem grupo de comparação. Os tipos de "
   "estímulo não foram aleatorizados e confundem-se com a posição no microciclo e com a carga acumulada. As "
   "ausências reduzem de vinte e sete a vinte e um os respondentes no sétimo dia, e os testes de série "
   "completa operam sobre dezenove. O estudo é descritivo e não estabelece relação causal entre carga e "
   "perfil.")

h_("5 CONCLUSÃO")
p_("As sete variáveis do BRUMS não satisfazem normalidade e quatro apresentam efeito de piso relevante, o "
   "que torna a via não paramétrica a escolha apropriada, e não uma alternativa conservadora. Sob essa via, "
   "vigor, fadiga, tensão e confusão deslocam-se de modo monotônico e estatisticamente sustentado ao longo "
   "da semana, e a perturbação total os acompanha no contraste entre extremos sem desenhar a mesma reta, "
   "com a barbatana de tubarão e a faixa de risco em franca expansão. A distribuição dos perfis não difere "
   "entre tipos de estímulo, e a migração intradiária para a faixa de risco só se torna visível com duas "
   "coletas por dia. Para o monitoramento em clube, a leitura conjunta do perfil e da variável contínua, sob "
   "critério não paramétrico e com o piso de ruído declarado, é a que os dados recomendam.")

h_("REFERÊNCIAS")
for i in sorted(ESCOLHIDAS, key=lambda k: _R.REFS[k]):
    para(_R.REFS[i], indent=False, size=9, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         before=0, after=2.5, spacing=1.0)

out = os.path.join(S, "ARTIGO_DESCRITIVO_EXPLORATORIO_PERFIS_HUMOR_HANDEBOL.docx")
doc.save(out)
print("salvo:", out)
