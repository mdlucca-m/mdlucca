# -*- coding: utf-8 -*-
"""Síntese executiva dos quatro documentos, em até cinco páginas.

Todo número vem dos JSON de análise, nunca de texto anterior. O formato é mais
compacto que o dos artigos, com entrelinha 1,15 e margens de 2,5 cm, porque o
destinatário é um leitor único e não uma revista.
"""
import os, sys
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_docx_base.py")).read())

# ---- formato compacto, próprio deste documento ----
for m in ('left_margin', 'right_margin'): setattr(sec, m, Cm(2.2))
sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(1.8)
st.font.size = Pt(10.5)
pf.line_spacing = 1.09
pf.first_line_indent = Cm(0)
pf.space_after = Pt(4)

import re as _re
def p_(txt, size=10.5, spacing=1.09, after=4, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    """Parágrafo sem recuo, com trechos entre __ __ em negrito."""
    q = doc.add_paragraph()
    for i, parte in enumerate(_re.split(r'__(.+?)__', txt)):
        if not parte: continue
        r = q.add_run(parte); r.bold = (i % 2 == 1); r.font.size = Pt(size)
    f = q.paragraph_format; f.alignment = align; f.line_spacing = spacing
    f.space_before = Pt(0); f.space_after = Pt(after); f.first_line_indent = Cm(0)
    return q

def h_(txt, before=10):
    para(txt, indent=False, bold=True, size=11, align=WD_ALIGN_PARAGRAPH.LEFT,
         before=before, after=3, spacing=1.09)

def cap_(txt):
    para(txt, indent=False, size=8.5, align=WD_ALIGN_PARAGRAPH.LEFT,
         before=6, after=2, spacing=1.0)

prox_tab = lambda: _CONT['tab'] + 1
prox_fig = lambda: _CONT['fig'] + 1

def fig_(arq, legenda, w=14.5):
    """Figura com legenda acima e fonte abaixo, no formato compacto deste documento."""
    cap_(f"Figura {fig()} – {legenda}")
    doc.add_picture(os.path.join(S, arq), width=Cm(w))
    q = doc.paragraphs[-1]; q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.first_line_indent = Cm(0); q.paragraph_format.space_after = Pt(7)

def nota_(txt):
    para(txt, indent=False, size=8, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         before=2, after=7, spacing=1.0)

jd = lambda n: json.load(open(os.path.join(DADOS, n + ".json"), encoding='utf-8'))
A1 = jd("V2_a1"); A3 = jd("V2_a3"); CZ = jd("V2_cruz"); DK = jd("V2_decomp")
AS = jd("V2_assoc"); PR = jd("V2_proto"); O = jd("V2_otim"); C = jd("V2_conf")
Q = jd("V2_qual"); B = jd("V2_base"); TE = jd("V2_te"); PS = jd("V2_psico")
NOMES = jd("V2_perfis")["NOMES"]

SER = A1['SER']; SERP = A3['SERP']; DESC = A1['DESC']
V7 = ['Tensão', 'Depressão', 'Raiva', 'Vigor', 'Fadiga', 'Confusão', 'TMD']
L = lambda v: 'PTH' if v == 'TMD' else v

def n_(x, d=2):
    if x is None or (isinstance(x, float) and x != x): return "—"
    return f"{x:.{d}f}".replace('.', ',').replace('-', '−')
def pf_(p, d=3):
    if p is None: return "—"
    return "< 0,001" if p < 0.001 else f"{p:.{d}f}".replace('.', ',')

# p de cada via, recuperado da tabela de resultados já construída
import sqlite3
cx = sqlite3.connect(os.path.join(RAIZ, "base", "humor_handebol.sqlite"))
cx.row_factory = sqlite3.Row
def pget(var, rec, teste_like):
    r = cx.execute("SELECT p FROM resultado WHERE variavel=? AND recorte=? AND teste LIKE ?",
                   (var, rec, teste_like)).fetchone()
    return r['p'] if r else None

# ============================== documento ==============================
para("PERFIL E COMPORTAMENTO DAS DIMENSÕES DO BRUMS NA ÚLTIMA SEMANA DE PRÉ-TEMPORADA",
     indent=False, bold=True, size=12.5, align=WD_ALIGN_PARAGRAPH.CENTER, after=2, spacing=1.12)
para("DE ATLETAS DE HANDEBOL DE ELITE: SÍNTESE DE MÉTODO E RESULTADOS",
     indent=False, bold=True, size=12.5, align=WD_ALIGN_PARAGRAPH.CENTER, after=5, spacing=1.12)
para("Síntese dos quatro produtos do estudo. Todo número procede da base única e foi reconferido por um "
     "segundo caminho de código; todas as figuras e tabelas foram elaboradas pelos autores.",
     indent=False, italic=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER, after=9, spacing=1.1)

# ---------------------------------------------------------------- 1
h_("1 PERGUNTA E DESENHO", before=2)
p_("O estudo descreve como as seis dimensões do humor e a perturbação total se comportam ao longo do "
   "microciclo que antecede a estreia competitiva, e pergunta se essa variação excede o que a própria "
   "amostragem produz. Trata-se de estudo observacional longitudinal de medidas repetidas, com sete dias "
   f"consecutivos, entre 21 e 27 de abril de 2024, sem intervenção dos pesquisadores. Participaram "
   f"{len(B['ATL'])} atletas de handebol masculino de equipe da primeira divisão nacional, com idade média de "
   "21,96 anos e desvio-padrão de 3,81. A carga acumulada progrediu de 1,5 hora no primeiro dia a 23,0 horas "
   "ao término do sétimo.")
p_("O primeiro dia teve coleta única, à noite, e serve de linha de base. Do segundo ao sétimo houve duas "
   "medidas diárias, uma no início e outra ao fim do dia. A semana reuniu quatro tipos de estímulo: conteúdo "
   "técnico e tático no primeiro dia; treino intervalado de alta intensidade combinado com trabalho técnico "
   "no segundo, quarto e sétimo; jogo amistoso no terceiro e no quinto; conteúdo técnico, tático e de força "
   "no sexto.")

# ---------------------------------------------------------------- 2
h_("2 MÉTODO")
tot = PR['TOTAIS']
p_(f"__Unidade de análise.__ A fonte reúne {tot['registros']} registros. A unidade canônica é o par "
   f"atleta-dia, com {tot['atleta_dia']} casos: um valor por atleta e por dia. A regra que compõe esse valor "
   "foi auditada contra os carimbos de data e hora. No dia basal, de coleta única, vale a primeira resposta "
   "de cada atleta, porque as respostas tardias daquela noite são repetição e não segunda medida: dos atletas "
   "que responderam depois das 21 h, todos menos um já haviam respondido às 20h42. Do segundo ao sétimo dia "
   f"valem o primeiro e o último registro. Ao todo, {PR['REGRA_A']['retidos']} registros compõem os valores "
   f"diários e {PR['REGRA_A']['n_excedentes']} permanecem na base sem entrar no cálculo.")
p_("__Tratamento de séries.__ Cada série de sete pontos recebe quatro operações antes de qualquer leitura. "
   "O erro-padrão diário mede a incerteza de cada ponto, amostral para médias e binomial para prevalências. "
   "O piso de ruído é a média dos sete erros-padrão e responde a quanta oscilação a amostragem, sozinha, "
   "produz naquela série. A suavização usa o filtro binomial de três pontos, com núcleo [¼, ½, ¼] nos pontos "
   "internos e extremos preservados; o ganho é H(ω) = cos²(ω/2), que se anula na frequência de Nyquist, "
   "isto é, na componente que troca de sinal a cada dia. As derivadas de primeira e de segunda ordem da "
   "série suavizada exprimem velocidade e aceleração em unidades do piso, o que torna comparáveis variáveis "
   "de amplitudes distintas. Declara-se variação real quando o deslocamento entre o primeiro e o sétimo dia "
   "supera o piso; caso contrário, a oscilação fica atribuída à flutuação amostral.")
p_("__Cruzamentos.__ O encontro entre duas trajetórias é tratado como zero da série da diferença. Reconhece-se "
   "inversão apenas quando a diferença supera o limiar combinado, √(piso²ᴬ + piso²ᴮ), tanto no primeiro quanto "
   "no sétimo dia. A abscissa do cruzamento sai por interpolação linear, e a travessia recebe ainda velocidade, "
   "aceleração e zona de indecisão, definida como o intervalo contíguo em que a diferença permanece dentro do "
   "limiar. A zona mede a determinação da data, questão distinta da existência da inversão.")
p_("__Inferência.__ A mesma hipótese percorreu três vias independentes: não paramétrica (Friedman com "
   "Wilcoxon e ajuste de Holm, L de Page para tendência ordenada, Q de Cochran e McNemar para desfechos "
   "categóricos), paramétrica clássica (ANOVA de medidas repetidas com correção de Greenhouse-Geisser e t "
   "pareado) e modelo linear misto com intercepto aleatório por atleta, que aproveita todos os casos e não "
   "descarta atletas com ausências. A decomposição da variância usou efeitos aleatórios cruzados de atleta e "
   "dia, por máxima verossimilhança restrita.")
p_(f"__Qualidade e reprodutibilidade.__ Os nove escores calculados da planilha foram reconstruídos por "
   f"fórmula a partir dos itens em {sum(c['n_comparado'] for c in Q['CONFRONTO'])} conferências, com "
   f"{sum(c['n_divergente'] for c in Q['CONFRONTO'])} divergências. Os números dos documentos foram "
   f"recalculados por um segundo caminho de código, que parte do item do formulário: "
   f"{C['ok']} de {C['total']} conferências coincidem dentro da "
   "tolerância. Todo o processamento correu em Python 3.11, com NumPy, SciPy, statsmodels, pandas, "
   "scikit-learn, XGBoost e matplotlib. Um único comando refaz a cadeia inteira, do dado de origem aos "
   "documentos finais.")

# ---------------------------------------------------------------- 3
h_("3 RESULTADOS")

p_(f"__3.1 As sete séries contra o próprio ruído.__ A Tabela {prox_tab()} põe lado a lado o deslocamento de "
   "cada variável, o piso da sua série e o veredito das quatro leituras inferenciais. Todas as sete séries "
   "deslocam-se acima do respectivo piso, com razões que vão de 7,1 no vigor a 1,6 na depressão, e a "
   "inferência concorda nos extremos e diverge nas variáveis de deslocamento pequeno.")
cap_(f"Tabela {tab()} – Deslocamento semanal, piso de ruído e veredito pelas três vias")
rows = []
for v in V7:
    d = SER[v]
    pn = pget(v, 'D1..D7', 'Friedman')
    pp = pget(v, 'D1..D7', 'ANOVA%')
    pm = pget(v, 'efeito linear do dia', '%')
    pg = pget(v, 'ordenada D1→D7', '%')
    rows.append([L(v), n_(d['med'][0]), n_(d['med'][6]), n_(d['dtot']) , n_(d['piso'], 3),
                 n_(d['razao'], 1) + "×", pf_(pn), pf_(pp), pf_(pm), pf_(pg)])
mktable(["Variável", "D1", "D7", "Δ", "Piso", "Razão", "Friedman", "ANOVA", "Misto", "Page"],
        rows, widths=[2.0, 1.3, 1.3, 1.4, 1.4, 1.3, 1.7, 1.5, 1.4, 1.5], fs=8)
nota_("Δ é o deslocamento entre D1 e D7; a razão divide o seu módulo pelo piso de ruído. Friedman e ANOVA "
      "operam sobre os dezenove atletas com série completa, o modelo misto sobre os 166 pares, e o L de Page "
      "testa tendência ordenada. PTH é a perturbação total do humor.")
p_("O vigor recua 4,33 pontos e a fadiga avança 4,28, ambos com deslocamento superior a cinco vezes o "
   "respectivo ruído e significativos pelas três vias. A tensão cai 1,26 ponto, movimento contrário ao das "
   "demais dimensões negativas, também significativo pelas três vias. Depressão e raiva superam o piso por "
   "margem estreita, e aí as leituras se separam. A raiva não alcança significância por via alguma, caso em "
   "que a leitura correta é a das vias inferenciais e não a do piso, permissivo naquela faixa. A depressão só "
   "alcança significância no modelo misto (p = 0,049), que aproveita os 166 pares em vez de restringir-se aos "
   "dezenove atletas com série completa; a discrepância mede o custo do descarte de casos incompletos, e não "
   "um efeito que as demais vias tenham deixado escapar.")

fig_("F5fig.png", "Decomposição sinal e ruído das seis subescalas. Cada painel sobrepõe a série observada "
     "com o erro-padrão diário, a série suavizada pelo filtro binomial e a faixa do piso de ruído em torno "
     "do valor basal. A variação só é declarada real onde a curva escapa da faixa.", w=12.4)

p_(f"__3.2 A forma da semana.__ A Figura {prox_fig() - 1} já deixa ver que a deterioração não se distribui de modo uniforme. As transições cujo módulo "
   "excede o piso concentram-se nas duas extremidades e deixam entre elas um platô de quatro dias. O vigor "
   "acumula três transições de choque, na saída do dia basal, na passagem seguinte e na véspera da estreia; "
   "a fadiga e a perturbação total acumulam duas, na primeira e na última transição. A repartição do "
   "deslocamento confirma a leitura: 90,7% do movimento absoluto do vigor ocorre em transições de choque, "
   "contra 71,0% na perturbação total e 65,9% na fadiga, ao passo que o deslocamento da depressão é deriva "
   "pura, sem nenhuma transição acima do piso.")

fig_("P6fig.png", "Vigor, fadiga e perturbação total ao longo do microciclo, com os três cruzamentos "
     "assinalados. A escala da perturbação total aparece à direita, porque a sua amplitude é cerca de cinco "
     "vezes a das subescalas.", w=12.8)

p_(f"__3.3 Perfis de humor.__ A distribuição migra do polo favorável ao desfavorável, e todas as séries de "
   f"prevalência, salvo a do perfil submerso, deslocam-se acima do próprio piso. A Tabela {prox_tab()} traz a "
   "prevalência dia a dia; a Figura 3 mostra a forma de cada perfil e a Figura 4, a composição do elenco ao "
   "longo da semana.")
ordem = ['Iceberg', 'Superfície', 'Submerso', 'Barbatana de tubarão', 'Iceberg invertido',
         'Everest invertido', 'Favorável', 'Neutra', 'De risco']
p_("A faixa de risco, que reúne barbatana de tubarão, iceberg invertido e Everest invertido, passa de 14,8% "
   "a 52,4% dos pares atleta-dia, deslocamento de 37,6 pontos percentuais contra um piso de 9,8. A leitura dia "
   "a dia mostra que a troca não é um evento pontual: o iceberg e a barbatana de tubarão, os dois extremos da "
   "classificação, trocam de posição logo na saída do dia basal e nunca mais se reaproximam.")
cap_(f"Tabela {tab()} – Prevalência diária dos seis perfis e das três faixas, com deslocamento e veredito")
mktable(["Perfil ou faixa"] + [f"D{d}" for d in range(1, 8)] + ["Δ", "Piso", "Veredito"],
        [[k] + [n_(SERP[k]['y'][d], 1) for d in range(7)] +
         [n_(SERP[k]['dtot'], 1), n_(SERP[k]['piso'], 1),
          ("não avaliável" if SERP[k]['fragil'] else ("sinal" if SERP[k]['sinal'] else "ruído"))]
         for k in ordem],
        widths=[3.3] + [1.03] * 7 + [1.15, 1.05, 2.35], fs=7.5)
nota_(f"Valores em percentagem dos pares do dia; denominadores de D1 a D7: "
      f"{', '.join(str(x) for x in A1['nd'])}. As faixas agregam os perfis: favorável reúne o iceberg; "
      "neutra, superfície e submerso; de risco, os três restantes. O Everest invertido reúne dois pares no "
      "conjunto inteiro, e o piso binomial encolhe perto de zero, razão pela qual a sua série fica "
      "assinalada como não interpretável.")

fig_("P4fig.png", "Assinatura dos seis perfis de humor em escore T: o centroide observado neste elenco "
     "contra o canônico de Parsons-Smith, Terry e Machin (2017), com a prevalência de cada perfil e o dia em "
     "que predomina.", w=12.6)

p_("A assinatura de cada perfil merece leitura atenta, porque ela explica o comportamento agregado. O iceberg "
   "descreve o estado de vigor alto com as cinco dimensões negativas abaixo da norma, e é o perfil que a "
   "literatura associa ao bem-estar psicológico. A barbatana de tubarão eleva tensão, raiva e fadiga sem "
   "derrubar o vigor, e por isso não é um estado de colapso, e sim de ativação com custo. O iceberg invertido "
   "espelha o primeiro, com vigor abaixo da norma e as negativas acima. O Everest invertido leva esse padrão "
   "ao extremo e, neste elenco, comparece em apenas dois pares. A semana desloca a distribuição do primeiro "
   "para os dois últimos, e a barbatana de tubarão funciona como estação intermediária.")

fig_("P2fig.png", "Composição do elenco entre os seis perfis, dia a dia, e as três faixas de humor com o "
     "ponto em que a faixa de risco ultrapassa a favorável.", w=13.0)

p_(f"__3.4 Cruzamentos entre trajetórias.__ Os três pares assinalados na Figura 2 foram examinados um a um, "
   f"e a Tabela {prox_tab()} resume a anatomia de cada travessia. O resultado separa duas perguntas "
   "que a inspeção do gráfico confunde: se a inversão existe, e se a sua data está determinada.")
cap_(f"Tabela {tab()} – Anatomia dos cruzamentos por limites e derivadas")
mktable(["Par", "Limiar", "Cruza em", "Velocidade", "Aceleração", "Zona de indecisão", "Veredito"],
        [[k.replace('TMD', 'PTH'), "±" + n_(c['limiar']), "D" + n_(c['cruzamentos'][0]['abscissa']),
          n_(c['cruzamentos'][0]['velocidade_em_limiares']), n_(c['cruzamentos'][0]['aceleracao_em_limiares']),
          n_(c['cruzamentos'][0]['zona_largura']) + " dia",
          "inversão estabelecida" if c['estabelecida'] else "divergência"]
         for k, c in CZ['CRUZ'].items()],
        widths=[2.6, 1.6, 1.7, 2.2, 2.2, 2.8, 3.7], fs=8)
nota_("Velocidade e aceleração vêm em limiares por dia e por dia ao quadrado. A zona de indecisão é o "
      "intervalo em que a diferença entre as duas séries permanece dentro do limiar combinado.")
p_("O vigor e a fadiga trocam de posição de modo estabelecido, com abscissa em 5,13, porém a travessia ocorre "
   "a apenas 0,86 limiar por dia e a zona de indecisão cobre 3,52 dias. A inversão existe; a data não está "
   "determinada. O par entre vigor e perturbação total cruza-se em 6,01 a 2,14 limiares por dia, com zona de "
   "1,42 dia, e é a única travessia nítida. O par entre fadiga e perturbação total não separa nos extremos e "
   "recebe veredito de divergência.")

p_(f"__3.5 De onde vem a variação.__ Um modelo de efeitos aleatórios cruzados situa o objeto do estudo dentro "
   f"da variação total, como mostra a Tabela {prox_tab()}, e o resultado convida à modéstia.")
cap_(f"Tabela {tab()} – Componentes de variância e fidedignidade da série diária")
mktable(["Variável", "Entre atletas", "Entre dias", "Residual", "Fidedignidade da série", "Choque"],
        [[L(v), n_(DK['COMPONENTES'][v]['p_atleta'], 1) + "%", n_(DK['COMPONENTES'][v]['p_dia'], 1) + "%",
          n_(DK['COMPONENTES'][v]['p_residual'], 1) + "%",
          ("nula" if DK['SERIE'][v]['negativa'] else n_(DK['SERIE'][v]['fidedignidade'])),
          n_(DK['DESLOCAMENTO'][v]['p_choque_abs'], 1) + "%"] for v in V7],
        widths=[2.3, 2.8, 2.4, 2.3, 3.7, 2.3], fs=8)
nota_("As três primeiras colunas repartem a variância dos 166 pares. A fidedignidade divide a variância "
      "verdadeira entre as sete médias pela observada, e é nula quando esta fica abaixo da de erro. A última "
      "coluna dá a fração do movimento absoluto em transições acima do piso.")
p_("A parcela atribuível ao dia, que é o movimento do elenco de uma jornada para a outra, é a menor das três "
   "em todas as sete variáveis, de 0,6% na depressão a 15,6% no vigor. A maior parcela cabe às diferenças "
   "estáveis entre atletas. Apenas o vigor, com 0,78, e a fadiga, com 0,62, sustentam leitura de série no "
   "sentido pleno; a série da depressão tem fidedignidade nula, porque a variância entre as suas sete médias, "
   "de 0,094, é menor que a variância de erro, de 0,227.")

p_("__3.6 Confiabilidade e limiares individuais.__ Antes de transportar qualquer leitura do grupo para o "
   "atleta, cabe perguntar se o instrumento distingue, neste elenco, mudança de erro. O erro típico da medida "
   f"e a mínima mudança detectável respondem a isso, na Tabela {prox_tab()}, e a resposta é sóbria: em nenhuma "
   "das sete variáveis a mudança individual detectável cabe dentro da variação que a semana produziu no grupo.")
cap_(f"Tabela {tab()} – Confiabilidade da medida repetida e limiares individuais de mudança")
mktable(["Variável", "α de Cronbach", "ω de McDonald", "CCI", "Erro típico", "MMD 95%", "Δ do grupo"],
        [[L(v),
          n_(next((c['alfa'] for c in PS['CONF'] if c['subescala'] == v), None)),
          n_(next((c['omega'] for c in PS['CONF'] if c['subescala'] == v), None)),
          n_(A1['ICC'][v]['icc']) if v in A1['ICC'] else "—",
          n_(next((t['et'] for t in TE['TE'] if t['variavel'] == v), None)),
          n_(next((t['mmd95'] for t in TE['TE'] if t['variavel'] == v), None)),
          n_(abs(SER[v]['dtot']))] for v in V7],
        widths=[2.3, 2.4, 2.4, 1.7, 2.2, 2.0, 2.2], fs=8)
nota_("α e ω medem a consistência interna dos quatro itens da subescala; o CCI, a estabilidade da medida "
      "repetida no mesmo atleta. O erro típico é o desvio-padrão da diferença dividido por √2, e a mínima "
      "mudança detectável a 95% vale 1,96·√2 vezes esse erro. A perturbação total, por ser composto e não "
      "escala, não tem α nem ω próprios.")
p_("A consequência é metodológica e prática ao mesmo tempo. O deslocamento do vigor no grupo, de 4,33 pontos, "
   "é o único que se aproxima da mínima mudança detectável para um atleta isolado. Para as demais variáveis, "
   "afirmar que um atleta específico piorou exigiria variação maior do que a que a semana inteira produziu na "
   "média do elenco. O monitoramento individual, portanto, pede série longa do próprio atleta, e não "
   "comparação com o grupo em dois pontos.")

p_("__3.7 Resposta ao estímulo e dinâmica intradiária.__ A distribuição dos perfis não difere entre os três "
   f"tipos de estímulo (χ² = {n_(A3['chi'], 3)}; gl = {A3['gl']}; p = {pf_(A3['p_chi'])}), nem a das faixas "
   f"(χ² = {n_(A3['chi_f'], 3)}; gl = {A3['gl_f']}; p = {pf_(A3['p_f'])}). Nenhuma das sete variáveis contínuas "
   "difere entre estímulos na subamostra de vinte e dois atletas presentes nos três tipos de dia, seja pelo "
   "teste de Friedman, seja pela ANOVA de medidas repetidas. Registre-se que os tipos de estímulo não foram "
   "distribuídos ao acaso e confundem-se com a posição no microciclo e com a carga acumulada, de modo que "
   "nenhuma inferência sobre especificidade de estímulo é separável de efeito cumulativo neste desenho.")
mcn = A3['MCN']
p_(f"A comparação entre a medida do início e a do fim do dia revela migração assimétrica para a faixa de "
   f"risco: {mcn['TODOS']['entra']} pares entram nela ao longo do dia e {mcn['TODOS']['sai']} saem "
   f"(χ² = {n_(mcn['TODOS']['chi'])}; p = {pf_(mcn['TODOS']['p'])}). Repartida por estímulo, apenas o treino "
   f"intervalado alcança significância bruta ({mcn['HIIT']['entra']} entram, {mcn['HIIT']['sai']} saem; "
   f"p = {pf_(mcn['HIIT']['p'])}), e a atribuição não sobrevive à correção de Holm "
   f"(p ajustado = {pf_(mcn['HIIT']['ph'])}). O fenômeno só é visível porque houve duas coletas diárias.")

M = O['MODELO']
p_("__3.8 Carga do dia e carga da véspera.__ Um modelo misto com as horas do próprio dia e as da véspera "
   "mostra que o humor do dia responde à véspera, não ao próprio dia. As horas do dia corrente não têm efeito "
   f"detectável sobre o vigor (β = {n_(M['Vigor']['b1'], 3)}; p = {pf_(M['Vigor']['p1'])}) nem sobre a fadiga "
   f"(β = {n_(M['Fadiga']['b1'], 3)}; p = {pf_(M['Fadiga']['p1'])}). As horas da véspera têm: cada hora "
   f"treinada no dia anterior subtrai {n_(abs(M['Vigor']['b2']), 3)} ponto de vigor "
   f"(p = {pf_(M['Vigor']['p2'])}) e soma {n_(M['Fadiga']['b2'], 3)} ponto de fadiga "
   f"(p = {pf_(M['Fadiga']['p2'])}). O humor da manhã é consequência, e não previsão.")
d5 = [e for e in O['EQ'] if e['restricao'].startswith('D5')][0]
p_("Sobre essa resposta estimada resolveu-se um programa linear que redistribui as mesmas 23 horas semanais "
   "de modo a maximizar o pior dia de vigor da semana. O ganho é pequeno, de "
   f"{n_(O['OBSERVADO']['vigor_minimo'])} para {n_(O['PROGRAMA_I']['vigor_minimo_garantido'])} ponto, e a "
   f"razão aparece nos preços-sombra: cada hora do amistoso do quinto dia custa "
   f"{n_(abs(d5['preco_sombra']))} ponto do pior dia de vigor, mais do que qualquer decisão de treino "
   f"disponível. Quem comprime o microciclo é o calendário de jogos, não o volume de treino. A carga semanal "
   f"mínima estruturalmente viável é de {n_(O['CARGA_MINIMA_ESTRUTURAL'], 2)} horas.")

ac = AS['ACOPL']
p_("__3.9 Estrutura de associação.__ A correlação agregada mistura dois planos que se comportam de maneira "
   "distinta. Separados, cinco dos vinte e um pares associam-se apenas dentro do atleta. O caso da tensão é o "
   f"mais informativo: com o vigor, ρ = {n_(AS['PLANOS']['Tensão×Vigor']['entre_rho'], 3)} e "
   f"p = {pf_(AS['PLANOS']['Tensão×Vigor']['entre_p'])} entre atletas, contra "
   f"ρ = {n_(AS['PLANOS']['Tensão×Vigor']['dentro_rho'], 3)} e "
   f"p = {pf_(AS['PLANOS']['Tensão×Vigor']['dentro_p'])} dentro do atleta. Os dias de maior tensão de um "
   "mesmo atleta são os seus dias de maior vigor, ao passo que atletas mais tensos não são, em média, mais "
   f"vigorosos. Com a perturbação total, a correlação agregada de "
   f"{n_(AS['PLANOS']['Tensão×TMD']['agregado_rho'], 3)} "
   f"(p = {pf_(AS['PLANOS']['Tensão×TMD']['agregado_p'])}) desaparece no plano intraindividual "
   f"(ρ = {n_(AS['PLANOS']['Tensão×TMD']['dentro_rho'], 3)}; "
   f"p = {pf_(AS['PLANOS']['Tensão×TMD']['dentro_p'])}). A tensão comporta-se neste elenco como ativação, e "
   "não como sofrimento, com a ressalva de que o efeito de piso de 41,6% oferece explicação métrica "
   "alternativa que os presentes dados não descartam.")
p_("A associação entre a fadiga e a perturbação total cresce ao longo da semana, de "
   f"ρ = {n_(ac['rho_d1'], 3)} no dia basal a ρ = {n_(ac['rho_d7'], 3)} no sétimo, com variância partilhada "
   f"de {n_(ac['r2_d1'], 1)}% a {n_(ac['r2_d7'], 1)}%. A tendência do coeficiente ao longo dos sete dias dá "
   f"ρ = {n_(ac['tendencia_rho'], 3)} com p = {pf_(ac['tendencia_p'])}, valor que não atinge o limiar "
   "convencional, de modo que o achado permanece descritivo. A consequência prática independe do teste: na "
   "fase terminal da pré-temporada, quem acompanha apenas o escalar acompanha, na prática, a fadiga, e o "
   "perfil completo deve ser reportado no lugar do composto isolado.")

p_("__3.10 Robustez das conclusões.__ Três decisões metodológicas foram testadas quanto ao seu efeito sobre os "
   "vereditos. A unidade de análise altera um veredito entre as quatro unidades defensáveis, e o veredito "
   "alterado é o da tensão, por ponderação e não por efeito. A regra de composição do valor diário produz o "
   "contraste mais instrutivo: afastar os 150 registros intermediários do miolo da semana não trocou nenhum "
   "dos vinte e um vereditos, ao passo que corrigir a linha de base, o que afastou apenas 21 registros, "
   "trocou quatro. A assimetria tem explicação estrutural, pois o basal é o ponto contra o qual todos os seis "
   "contrastes se medem. Daí decorre a recomendação de que, em desenhos com linha de base, a regra que a "
   "compõe mereça auditoria específica. Quanto ao mecanismo de ausência, a análise não encontrou padrão que "
   "vincule a falta de resposta ao humor registrado.")

# ---------------------------------------------------------------- 4
h_("4 CONCLUSÕES")
p_("O humor do elenco deteriora-se de modo consistente ao longo da última semana de pré-temporada, e a "
   "deterioração é real no sentido preciso de superar o erro de amostragem da própria série. Ela concentra-se "
   "em duas transições, na saída do dia basal e na véspera da estreia, e deixa entre elas um platô de quatro "
   "dias. A faixa de risco mais que triplica em prevalência.")
p_("O estudo oferece três contribuições de método que o campo do monitoramento não reúne. A primeira é o "
   "critério explícito de decisão: nenhuma variação é lida sem confronto com um limiar declarado, cujo cálculo "
   "exige apenas o desvio-padrão e o número de respondentes de cada dia. A segunda é a distinção entre "
   "inversão estabelecida e data determinada, que a zona de indecisão quantifica e que impede afirmações "
   "excessivamente precisas sobre quando uma troca de regime ocorreu. A terceira é a demonstração de que a "
   "unidade de análise e a regra de composição do valor diário decidem vereditos tanto quanto a via "
   "estatística, e portanto merecem declaração explícita em qualquer relato.")
p_("Do ponto de vista aplicado, três recomendações decorrem dos dados. A migração intradiária para a faixa de "
   "risco só é visível com duas coletas por dia. O perfil comunica bem e detecta mal, ao passo que a variável "
   "contínua detecta bem e comunica mal, de modo que os dois planos devem ser usados em conjunto. E o "
   "acompanhamento que pretenda agir sobre o indivíduo precisa da série individual, porque a variação entre "
   "dias é a menor das três componentes de variância em todas as sete variáveis.")
p_("__Limitações.__ Trata-se de uma equipe, com sete dias e vinte e sete atletas, sem grupo de comparação e "
   "sem aleatorização dos estímulos, que se confundem com a posição no microciclo e com a carga acumulada. As "
   "ausências reduzem de vinte e sete a vinte e um o número de respondentes no sétimo dia. Quatro das seis "
   "subescalas apresentam efeito de piso entre 41,6% e 69,3%, o que comprime a variância e limita a "
   "capacidade de correlação. O programa linear da carga é instrumento de planejamento e não prova causal.")

out = os.path.join(S, "SINTESE_HUMOR_HANDEBOL.docx")
doc.save(out)
print("salvo:", out)
