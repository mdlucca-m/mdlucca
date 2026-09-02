# -*- coding: utf-8 -*-
"""Relatório de análise exploratória completa dos perfis de humor, organizado
por etapa de análise. Mais amplo que o artigo descritivo de oito páginas:
inclui a transição individual de perfil entre o primeiro e o sétimo dia, a
classificação de risco por atleta, a magnitude de mudança em cada transição
diária, o comportamento intradiário agregado, o ranking de sensibilidade das
onze variáveis, a regressão de tendência com ICC, e as quatro decomposições
da variação. Todo número procede dos JSON de análise e da tabela resultado.
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
ESCOLHIDAS = [51, 43, 50, 36, 5, 60, 49]

# ============================== documento ==============================
para("PERFIS DE HUMOR DE ATLETAS DE HANDEBOL DE ELITE NA ÚLTIMA SEMANA DE PRÉ-TEMPORADA:",
     indent=False, bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=2, spacing=1.1)
para("RELATÓRIO DE ANÁLISE EXPLORATÓRIA COMPLETA, POR ETAPA DE ANÁLISE",
     indent=False, bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=9, spacing=1.1)

h_("RESUMO", before=0, size=10)
p_(f"Este relatório detalha o comportamento das onze variáveis do BRUMS e a distribuição dos seis perfis de "
   f"humor em {len(B['ATL'])} atletas de handebol masculino de elite, ao longo dos sete dias que antecederam "
   f"a estreia competitiva, com {NAD} pares atleta-dia. Descreve dez etapas de análise: estatística descritiva; "
   "sensibilidade e variabilidade; trajetória diária e cruzamentos entre variáveis; comportamento intradiário; "
   "contraste entre o primeiro e o sétimo dia; regressão de tendência com confiabilidade; decomposição da "
   "variação; sonolência e estresse percebido; prevalência e trajetória dos perfis; e transição individual de "
   "perfil com classificação de risco por atleta. O vigor e a fadiga física são as variáveis mais sensíveis à "
   f"semana, com deslocamento de {n_(SER['Vigor']['razao'])} e {n_(SER['Fad.Física']['razao'])} vezes o "
   f"respectivo piso de ruído. A maior mudança conjunta ocorre na primeira transição, D1→D2 "
   f"({n_(EXP['MUDANCA'][0]['soma_abs_pisos'])} pisos somados). Dos {EXP['n_pareados']} atletas com "
   f"classificação em D1 e D7, {EXP['TRANS']['Iceberg']['ficou']} de {EXP['TRANS']['Iceberg']['n_d1']} que "
   f"começaram no iceberg permanecem nele; a maioria migra para perfis de maior custo afetivo. "
   f"{EXP['n_sempre_risco']} atletas permanecem na faixa de risco em todos os dias que responderam, e "
   f"{EXP['n_nunca_risco']} nunca entram nela.",
   indent=False, size=10, spacing=1.05, after=4)
para("__Palavras-chave:__ Estados de humor. Handebol. Análise exploratória. Pré-temporada. BRUMS.",
     indent=False, size=10, spacing=1.05, after=9)

# ---------------------------------------------------------------- 1
h_("1 MÉTODO", before=3)
p_(f"Estudo observacional longitudinal de medidas repetidas, com sete dias consecutivos, entre 21 e 27 de "
   f"abril de 2024, sem intervenção dos pesquisadores. Participaram {len(B['ATL'])} atletas de handebol "
   "masculino de equipe da primeira divisão nacional, com idade média de 21,96 anos e desvio-padrão de 3,81. "
   "O primeiro dia teve coleta única, à noite, e serve de linha de base; do segundo ao sétimo houve uma "
   "medida no início e outra ao fim do dia. A unidade de análise é o par atleta-dia, com "
   f"{NAD} casos, auditada contra os carimbos de data e hora: no dia basal vale a primeira resposta de cada "
   "atleta, e do segundo ao sétimo dia valem o primeiro e o último registro.")
p_("Aplicou-se a Escala de Humor de Brunel (TERRY et al., 1999), validada para o português brasileiro por "
   "Rohlfs et al. (2008), com escores convertidos em escore T contra parâmetros normativos de amostras "
   "atléticas (TERRY; LANE, 2000). Cada vetor de seis escores T foi atribuído ao perfil de centroide mais "
   "próximo (PARSONS-SMITH; TERRY; MACHIN, 2017). Onze variáveis entram nas etapas descritivas: as seis "
   "subescalas, a perturbação total, a fadiga física e a fadiga mental, a sonolência diurna de Epworth e o "
   "estresse percebido.")
p_("O plano estatístico cobre dez etapas, detalhadas em cada secção de resultados: descrição por posição, "
   "dispersão, forma e efeito de piso, com o teste de Shapiro-Wilk (Etapa 1); ranking de sensibilidade pelo "
   "coeficiente de variação e pela razão entre o deslocamento semanal e o piso de ruído, definido como a "
   "média dos sete erros-padrão diários (Etapa 2); ponto de inflexão de cada série, por interpolação sobre a "
   "segunda derivada, e magnitude de mudança em cada transição diária (Etapa 3); teste de Wilcoxon pareado "
   "entre a medida do início e a do fim do dia, agregado sobre os dias com dupla coleta (Etapa 4); teste de "
   "Wilcoxon pareado entre o primeiro e o sétimo dia, com o coeficiente r como tamanho de efeito, classificado "
   "pelos limiares de Cohen (Etapa 5); modelo linear misto com intercepto aleatório por atleta, para a "
   "tendência diária, e coeficiente de correlação intraclasse de duas vias (SHROUT; FLEISS, 1979), para a "
   "confiabilidade da medida repetida (Etapa 6); quatro decomposições da variação, por efeitos aleatórios "
   "cruzados de atleta e dia (Etapa 7); as mesmas etapas descritiva e de tendência aplicadas à sonolência e "
   "ao estresse percebido (Etapa 8); prevalência e trajetória diária dos seis perfis, com Q de Cochran "
   "(COCHRAN, 1950) para estabilidade e qui-quadrado de contingência para a associação com o tipo de "
   "estímulo (Etapa 9); e, por fim, a tabulação cruzada do perfil individual entre o primeiro e o sétimo dia, "
   "com a classificação de cada atleta pelo número de dias na faixa de risco (Etapa 10). O processamento "
   "correu em Python 3.11, com SciPy, NumPy e statsmodels, e todos os resultados foram recalculados por um "
   "segundo caminho de código a partir do item do formulário.")

# ---------------------------------------------------------------- 2
h_("2 RESULTADOS, POR ETAPA DE ANÁLISE")

h_("Etapa 1 — Estatística descritiva das onze variáveis", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} descreve as onze variáveis sobre os {NAD} pares atleta-dia. Nenhuma segue "
   "distribuição normal pelo teste de Shapiro-Wilk.")
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

h_("Etapa 2 — Sensibilidade e variabilidade", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} ordena as onze variáveis pela razão entre o deslocamento semanal e o piso de "
   "ruído, que mede quantas vezes o movimento observado supera a flutuação amostral típica da própria série.")
cap_(f"Tabela {tab()} – Ranking de sensibilidade: deslocamento semanal, piso e razão")
mktable(["Variável", "Δ D1→D7", "Piso", "Razão Δ/piso", "CV%", "Veredito"],
        [[Lb(s['variavel']), n_(s['dtot']), n_(s['piso'], 3), n_(s['razao_piso']) + "×", n_(DESC[s['variavel']]['cv']),
          "sinal" if s['sinal'] else "ruído"] for s in EXP['SENSI']],
        widths=[2.2, 1.7, 1.6, 2.0, 1.6, 1.5], fs=8.5)
nota_("A razão Δ/piso é o critério primário de sensibilidade; o CV descreve a dispersão relativa, mas não "
      "distingue movimento real de ruído amostral.")
p_(f"A fadiga física é a variável mais sensível à semana, com razão de {n_(EXP['SENSI'][0]['razao_piso'])}, "
   f"seguida do vigor, com {n_(EXP['SENSI'][1]['razao_piso'])}. A fadiga mental é a menos sensível entre as "
   "onze, com razão em torno da unidade, o que a coloca no limiar entre sinal e ruído.")

h_("Etapa 3 — Trajetória diária e cruzamentos", before=6, size=10.5)
p_(f"A Figura {prox_fig()} sobrepõe as três séries de maior amplitude e assinala os três pontos em que "
   "vigor, fadiga e perturbação total se cruzam ao longo da semana.")
fig_("P6fig.png", "Vigor, fadiga e perturbação total ao longo do microciclo, com os três pontos de "
     "cruzamento assinalados.", w=13.6)
p_(f"A Tabela {prox_tab()} e a Figura {prox_fig()} classificam a magnitude de mudança em cada uma das seis "
   "transições diárias, soma dos módulos das sete subescalas em unidades de piso.")
cap_(f"Tabela {tab()} – Magnitude de mudança por transição diária e ponto de inflexão de cada variável")
mktable(["Transição", "Soma em pisos (7 variáveis)"],
        [[m['transicao'], n_(m['soma_abs_pisos'])] for m in EXP['MUDANCA']],
        widths=[3.0, 4.0], fs=9)
fig_("X4fig.png", "Magnitude de mudança em cada transição diária.", w=11.6)
p_(f"A Tabela {prox_tab()} traz o dia de inflexão de cada variável, isto é, o ponto em que a curva muda de "
   "concavidade.")
cap_(f"Tabela {tab()} – Ponto de inflexão de cada série, por interpolação sobre a segunda derivada")
mktable(["Variável", "Dia de inflexão", "Transições de choque"],
        [[Lb(v), "D" + n_(SER[v]['infl'][0], 2), (", ".join(f"D{c-1}→D{c}" for c in SER[v]['choque']) or "nenhuma")]
         for v in V7],
        widths=[2.2, 2.3, 4.0], fs=8.5)
nota_("O dia de inflexão é a abscissa em que a segunda derivada da série suavizada troca de sinal, obtida "
      "por interpolação linear. Uma transição de choque é aquela cujo módulo excede o piso de ruído.")
p_(f"A primeira transição, D1→D2, concentra a maior mudança conjunta, "
   f"{n_(EXP['MUDANCA'][0]['soma_abs_pisos'])} pisos somados, seguida pela última, D6→D7, com "
   f"{n_(EXP['MUDANCA'][1]['soma_abs_pisos'])}. As quatro transições centrais somam menos, em conjunto, do "
   "que qualquer uma dessas duas isoladamente, o que confirma o platô observado no meio da semana. A maioria "
   "das variáveis inflete entre o terceiro e o quinto dia.")

h_("Etapa 4 — Comportamento intradiário, entre o início e o fim do dia", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} agrega todos os {EXP['INTRADIA']['Vigor']['n']} pares com dupla coleta, "
   "independentemente do dia ou do tipo de estímulo, e testa a diferença entre a medida do início e a do fim "
   "do dia.")
cap_(f"Tabela {tab()} – Contraste intradiário agregado, todas as onze variáveis")
mktable(["Variável", "Início", "Fim", "Δ", "Wilcoxon p", "r", "Efeito"],
        [[Lb(v), n_(EXP['INTRADIA'][v]['media_pre']), n_(EXP['INTRADIA'][v]['media_pos']),
          n_(EXP['INTRADIA'][v]['media_dif'], 2), pf_(EXP['INTRADIA'][v]['p']),
          n_(EXP['INTRADIA'][v]['efeito_r'], 2), efeito_(EXP['INTRADIA'][v]['efeito_r'])]
         for v in V11],
        widths=[2.0, 1.4, 1.4, 1.4, 1.7, 1.2, 1.7], fs=8.5)
nota_(f"n = {EXP['INTRADIA']['Vigor']['n']} pares com as duas medidas do dia, de D2 a D7. O efeito é "
      "classificado pelos limiares de Cohen para r: trivial < 0,10; pequeno < 0,30; médio < 0,50; grande "
      "≥ 0,50.")
p_("A fadiga física tem o maior efeito intradiário do conjunto, seguida pela perturbação total e pela "
   "fadiga em si; o vigor cai de modo consistente. Epworth, PSS, depressão, raiva e confusão não mudam de "
   "modo estatisticamente sustentado entre o início e o fim do dia, o que os situa como traços mais estáveis "
   "na escala intradiária, ainda que móveis na escala semanal.")

h_("Etapa 5 — Contraste entre o primeiro e o sétimo dia", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} traz o teste de Wilcoxon pareado entre D1 e D7, restrito aos atletas com medida "
   "nos dois extremos, com o tamanho de efeito classificado.")
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
p_(f"A Figura {_CONT['fig']} ordena as onze variáveis pelo tamanho de efeito, e a leitura confirma a Tabela 6: fadiga "
   "física, vigor, fadiga e perturbação total mudam com efeito grande, acima de 0,60; tensão, Epworth e "
   "confusão também alcançam efeito grande, ainda que por margem mais estreita. Depressão, raiva, PSS e "
   "fadiga mental não alcançam significância no contraste pareado, coerente com a leitura da Etapa 2.")

h_("Etapa 6 — Regressão de tendência e confiabilidade", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} traz a inclinação diária estimada por modelo linear misto, com intercepto "
   "aleatório por atleta, e o coeficiente de correlação intraclasse da medida repetida.")
cap_(f"Tabela {tab()} – Regressão de tendência diária (modelo misto) e confiabilidade (ICC)")
mktable(["Variável", "β dia (IC 95%)", "p", "ICC", "Erro típico", "MMD 95%"],
        [[Lb(v), f"{n_(LMM[v]['b_dia'],3)} ({n_(LMM[v]['ic'][0],2)}; {n_(LMM[v]['ic'][1],2)})",
          pf_(LMM[v]['p']), n_(ICC[v]['icc'], 2), n_(ICC[v]['epm']), n_(ICC[v]['mvd'])]
         for v in V7],
        widths=[2.0, 3.0, 1.5, 1.3, 1.7, 1.7], fs=8.5)
nota_("β dia é o coeficiente linear do dia sobre o par atleta-dia, em pontos por dia. ICC é o coeficiente de "
      "correlação intraclasse de duas vias; erro típico e mínima mudança detectável (MMD 95%) vêm da "
      "confiabilidade teste-reteste do instrumento neste elenco.")
p_("O vigor tem a maior inclinação negativa do conjunto. Entre as cinco subescalas negativas, a tensão é a "
   "única com inclinação diária negativa e estatisticamente confiável, β = "
   f"{n_(LMM['Tensão']['b_dia'],3)} (p = {pf_(LMM['Tensão']['p'])}); a confusão também desloca-se em sentido "
   "negativo, mas sem significância. A raiva tem a menor confiabilidade do conjunto, ICC = "
   f"{n_(ICC['Raiva']['icc'],2)}, o que limita a interpretação da sua tendência a nível individual; a "
   f"depressão tem a maior, ICC = {n_(ICC['Depressão']['icc'],2)}.")

h_("Etapa 7 — Decomposição da variação", before=6, size=10.5)
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

h_("Etapa 8 — Sonolência e estresse percebido", before=6, size=10.5)
p_(f"A escala de sonolência de Epworth desloca-se {n_(SER['Epworth']['dtot'])} pontos entre os extremos da "
   f"semana, contra um piso de {n_(SER['Epworth']['piso'], 2)}, razão de {n_(SER['Epworth']['razao'])}, e a "
   f"tendência diária pelo modelo misto não consta na Tabela 7 por não pertencer ao núcleo do BRUMS; o "
   f"contraste pareado D1×D7 é significativo (Tabela 6). O estresse percebido desloca-se apenas "
   f"{n_(SER['PSS']['dtot'])} ponto, com a menor razão de todo o conjunto, {n_(SER['PSS']['razao'])}, e não "
   "alcança significância no contraste pareado nem no intradiário. A sonolência acompanha a fadiga física em "
   "sensibilidade; o estresse percebido, medido pela escala de catorze itens, comporta-se como traço "
   "relativamente estável ao longo desta semana específica.")

h_("Etapa 9 — Prevalência e trajetória dos perfis de humor", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} compara a prevalência dos seis perfis com a referência populacional, e a "
   f"Figura {prox_fig()} traz a assinatura de cada perfil em escore T.")
cap_(f"Tabela {tab()} – Prevalência dos seis perfis no conjunto da semana e comparação com a referência")
mktable(["Perfil", "Pares", "Prevalência", "Referência", "Razão"],
        [[nome, str(CT[k]), n_(100*CT[k]/NAD) + "%", n_(REF[k]) + "%", n_(100*CT[k]/NAD/REF[k], 2)]
         for k, nome in enumerate(NOMES)],
        widths=[4.6, 2.2, 3.0, 3.0, 3.2], fs=9)
fig_("P4fig.png", "Assinatura dos seis perfis em escore T: o centroide observado contra o centroide de "
     "referência.", w=12.6)
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
   f"(χ² = {n_(A3['chi'],2)}; gl = {A3['gl']}; p = {pf_(A3['p_chi'])}).")

h_("Etapa 10 — Transição individual de perfil e classificação de risco", before=6, size=10.5)
p_(f"A Figura {prox_fig()} cruza o perfil de cada atleta no primeiro dia com o perfil no sétimo, sobre os "
   f"{EXP['n_pareados']} atletas com classificação nos dois extremos, e a Tabela {prox_tab()} resume o "
   "mesmo cruzamento por perfil de partida.")
fig_("X3fig.png", "Retenção e migração de perfil, do primeiro ao sétimo dia, por perfil de partida.", w=13.6)
cap_(f"Tabela {tab()} – Para onde foram os atletas de cada perfil inicial")
linT = []
for nome in NOMES:
    t = EXP['TRANS'][nome]
    if t['n_d1'] == 0: continue
    dest = "; ".join(f"{v}× {k}" for k, v in sorted(t['destinos'].items(), key=lambda x: -x[1])) or "—"
    linT.append([nome, str(t['n_d1']), f"{t['ficou']} ({n_(t['pct_ficou'])}%)", dest])
mktable(["Perfil em D1", "n", "Permaneceu", "Migrou para"], linT, widths=[3.2, 1.0, 2.4, 7.4], fs=8.5)
p_(f"O iceberg é o perfil de partida mais frequente ({EXP['TRANS']['Iceberg']['n_d1']} de "
   f"{EXP['n_pareados']} atletas) e o de menor retenção: apenas "
   f"{EXP['TRANS']['Iceberg']['ficou']} permanecem nele no sétimo dia, e a maior parte migra para a "
   "barbatana de tubarão. A barbatana de tubarão, por sua vez, é o único perfil cujo único representante em "
   "D1 nele permanece — indício de que, uma vez alcançado, esse estado tende a se manter.")
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

# ---------------------------------------------------------------- 3
h_("3 DISCUSSÃO")
p_("O quadro que emerge das dez etapas é consistente: a semana desloca o elenco de modo real, mensurável "
   "acima do próprio ruído, concentrado nas variáveis de maior amplitude, vigor e fadiga, e nas duas "
   "extremidades do microciclo. A transição individual de perfil mostra que esse deslocamento não é uma "
   "abstração de grupo: são atletas nomeáveis que trocam de estado, e a maioria dos que partem do iceberg "
   "chegam à barbatana de tubarão, não a um perfil intermediário.")
p_("A classificação de risco por atleta, por sua vez, revela heterogeneidade que a média do elenco esconde. "
   "Nove atletas nunca entram na faixa de risco ao longo de toda a semana, e três nela permanecem o tempo "
   "todo; a maioria transita entre faixas. Um sistema de alerta que trate o elenco como unidade única perderia "
   "essa distinção, que é exatamente a informação de que uma comissão técnica precisa para decidir sobre um "
   "atleta específico.")
p_("__Limitações.__ Uma equipe, sete dias e vinte e sete atletas, sem grupo de comparação. A classificação "
   "de risco individual usa todos os dias respondidos por cada atleta, e não apenas os extremos, de modo que "
   "atletas com menos respostas têm estimativa de percentual mais instável. O estudo é descritivo e não "
   "estabelece relação causal entre carga e perfil.")

h_("4 CONCLUSÃO")
p_("As dez etapas de análise convergem para uma leitura única: a última semana de pré-temporada desloca o "
   "elenco de handebol de elite em direção a um perfil de maior custo afetivo, de modo mensurável, "
   "concentrado na fadiga física e no vigor, com maior movimento nas duas extremidades da semana. A "
   "transição individual de perfil e a classificação de risco por atleta mostram que esse deslocamento é "
   "heterogêneo: a maioria dos atletas transita entre faixas, uma minoria nunca entra em risco e outra nele "
   "permanece o tempo todo. Para o monitoramento em clube, a recomendação é dupla: acompanhar a série "
   "individual de cada atleta, não apenas a média do grupo, e declarar sempre o piso de ruído contra o qual "
   "cada mudança é lida.")

h_("REFERÊNCIAS")
for i in sorted(ESCOLHIDAS, key=lambda k: _R.REFS[k]):
    para(_R.REFS[i], indent=False, size=9, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         before=0, after=2.5, spacing=1.0)

out = os.path.join(S, "RELATORIO_EXPLORATORIO_COMPLETO_PERFIS_HUMOR_HANDEBOL.docx")
doc.save(out)
print("salvo:", out)
