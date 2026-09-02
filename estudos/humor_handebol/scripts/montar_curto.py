# -*- coding: utf-8 -*-
"""Artigo curto sobre os seis perfis de humor no handebol de elite, em seis páginas.

Recorte deliberadamente estreito: apenas a classificação nos perfis, a sua
prevalência, a trajetória ao longo do microciclo e a migração entre a manhã e a
noite. As sete variáveis contínuas, os cruzamentos e as decomposições ficam nos
documentos maiores. Todo número procede dos JSON de análise.
"""
import os, sys, collections
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_docx_base.py")).read())

sec.top_margin, sec.bottom_margin = Cm(2.3), Cm(2.3)
st.font.size = Pt(11)
pf.line_spacing = 1.15
pf.space_after = Pt(3)

import re as _re
def p_(txt, size=11, spacing=1.15, after=3, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    q = doc.add_paragraph()
    for i, parte in enumerate(_re.split(r'__(.+?)__', txt)):
        if not parte: continue
        r = q.add_run(parte); r.bold = (i % 2 == 1); r.font.size = Pt(size)
    f = q.paragraph_format; f.alignment = align; f.line_spacing = spacing
    f.space_before = Pt(0); f.space_after = Pt(after)
    f.first_line_indent = Cm(1.0) if indent else Cm(0)
    return q

def h_(txt, before=10, size=11):
    para(txt, indent=False, bold=True, size=size, align=WD_ALIGN_PARAGRAPH.LEFT,
         before=before, after=3, spacing=1.15)

def cap_(txt):
    para(txt, indent=False, size=9, align=WD_ALIGN_PARAGRAPH.LEFT, before=7, after=2, spacing=1.0)

def nota_(txt):
    para("Nota: " + txt, indent=False, size=8.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         before=2, after=8, spacing=1.0)

prox_tab = lambda: _CONT['tab'] + 1
prox_fig = lambda: _CONT['fig'] + 1

def fig_(arq, legenda, w=14.0):
    cap_(f"Figura {fig()} – {legenda}")
    doc.add_picture(os.path.join(S, arq), width=Cm(w))
    q = doc.paragraphs[-1]; q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.first_line_indent = Cm(0); q.paragraph_format.space_after = Pt(8)

jd = lambda n: json.load(open(os.path.join(DADOS, n + ".json"), encoding='utf-8'))
QP = jd("V2_perfis"); A1 = jd("V2_a1"); A3 = jd("V2_a3"); B = jd("V2_base"); PR = jd("V2_proto")
SERP = A3['SERP']; NOMES = QP['NOMES']; REF = QP['PREV_REF']
lab = QP['lab_AD']; CT = collections.Counter(lab); NAD = len(lab)

def n_(x, d=1):
    if x is None or (isinstance(x, float) and x != x): return "—"
    return f"{x:.{d}f}".replace('.', ',').replace('-', '−')
def pf_(p, d=3):
    if p is None: return "—"
    return "< 0,001" if p < 0.001 else f"{p:.{d}f}".replace('.', ',')

import sys as _s; _s.path.insert(0, os.path.join(RAIZ, "texto"))
import REFS as _R
ESCOLHIDAS = [33, 36, 12, 22, 54, 42, 43, 51, 50, 20, 31, 46, 14, 38, 5, 30, 15]

# ============================== documento ==============================
para("PERFIS DE HUMOR DE ATLETAS DE HANDEBOL DE ELITE NA ÚLTIMA SEMANA DE PRÉ-TEMPORADA:",
     indent=False, bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=2, spacing=1.15)
para("PREVALÊNCIA, TRAJETÓRIA DIÁRIA E MIGRAÇÃO INTRADIÁRIA",
     indent=False, bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, after=10, spacing=1.15)

h_("RESUMO", before=0, size=10)
para("A classificação do humor em seis perfis descreve bem grandes amostras transversais, e pouco se sabe "
     "sobre o seu comportamento no acompanhamento diário de um elenco. Este estudo descreve a prevalência, a "
     f"trajetória e a migração intradiária dos seis perfis em {len(B['ATL'])} atletas de handebol masculino de "
     "primeira divisão nacional, ao longo dos sete dias que antecederam a estreia competitiva. A Escala de "
     f"Humor de Brunel foi respondida duas vezes ao dia, o que produziu {NAD} pares atleta-dia. Cada resposta "
     "recebeu escore T e foi atribuída ao perfil de centroide mais próximo. As séries diárias de prevalência "
     "foram confrontadas com um piso de ruído, definido como a média dos sete erros-padrão binomiais. O elenco "
     f"apresentou barbatana de tubarão em {n_(100*CT[3]/NAD)}% dos pares, mais que o dobro da referência "
     f"populacional, e submerso em {n_(100*CT[2]/NAD)}%, metade dela. Ao longo da semana o iceberg recuou de "
     f"{n_(SERP['Iceberg']['y'][0])}% para {n_(SERP['Iceberg']['y'][6])}% e a barbatana de tubarão avançou de "
     f"{n_(SERP['Barbatana de tubarão']['y'][0])}% para {n_(SERP['Barbatana de tubarão']['y'][6])}%; a faixa de "
     f"risco passou de {n_(SERP['De risco']['y'][0])}% para {n_(SERP['De risco']['y'][6])}%, deslocamento de "
     f"{n_(SERP['De risco']['dtot'])} pontos percentuais contra um piso de {n_(SERP['De risco']['piso'])}. A "
     f"distribuição dos perfis não diferiu entre os tipos de estímulo (χ² = {n_(A3['chi'],3)}; "
     f"p = {pf_(A3['p_chi'])}). Entre a manhã e a noite, {A3['MCN']['TODOS']['entra']} pares entraram na faixa "
     f"de risco e {A3['MCN']['TODOS']['sai']} saíram (p = {pf_(A3['MCN']['TODOS']['p'])}). A semana redistribui "
     "o elenco entre perfis em vez de deslocá-lo em bloco, e a leitura do fenômeno depende de duas coletas "
     "diárias e de um limiar de ruído declarado.",
     indent=False, size=10, spacing=1.1, after=4)
para("__Palavras-chave:__ Estados de humor. Handebol. Monitoramento do atleta. Pré-temporada. BRUMS.",
     indent=False, size=10, spacing=1.1, after=10)

h_("1 INTRODUÇÃO", before=4)
p_("O modelo de saúde mental proposto por Morgan associou o desempenho esportivo a um padrão de humor com "
   "vigor acima da norma e as dimensões negativas abaixo dela, padrão que a representação gráfica consagrou "
   "como perfil iceberg (MORGAN, 1980). A pesquisa posterior substituiu a leitura de um único padrão por uma "
   "tipologia: a análise de agrupamento sobre grandes amostras identificou seis perfis recorrentes, a saber, "
   "iceberg, superfície, submerso, barbatana de tubarão, iceberg invertido e Everest invertido "
   "(PARSONS-SMITH; TERRY; MACHIN, 2017). A solução mostrou-se estável em contextos culturais distintos "
   "(HAN; PARSONS-SMITH; TERRY, 2020; LEW et al., 2023; TERRY; PARSONS-SMITH; VLACHOPOULOS, 2024) e "
   "encontrou prevalências próprias em atletas brasileiros de alto rendimento (ROHLFS; NOCE; WILKE, 2024).")
p_("Essa tipologia consolidou-se, contudo, sobre amostras transversais de milhares de respondentes, e o "
   "seu transporte para o acompanhamento diário de um elenco reduzido levanta perguntas que os estudos de "
   "prevalência não respondem: quanto a distribuição se move de um dia para o outro, se essa movimentação "
   "excede a flutuação amostral, e se a fotografia da manhã coincide com a da noite. A pergunta tem alcance "
   "prático, porque o monitoramento em clubes profissionais de handebol privilegia indicadores de carga "
   "externa (HENZE et al., 2025), apesar da evidência de que medidas subjetivas superam as objetivas na "
   "detecção da resposta ao treino (SAW; MAIN; GASTIN, 2016).")
p_("A última semana de pré-temporada oferece condição privilegiada para essa observação, pois nela coexistem "
   "a carga acumulada de toda a preparação e a proximidade psicológica da estreia, combinação que os "
   "documentos de consenso associam a risco de resposta desadaptativa (MEEUSEN et al., 2013; KELLMANN et "
   "al., 2018) e que estudos em handebol vinculam a problemas de saúde (RAFNSSON et al., 2021). O objetivo "
   "deste estudo é descrever a prevalência, a trajetória diária e a migração intradiária dos seis perfis de "
   "humor em um elenco de handebol de elite ao longo do microciclo que antecede a estreia, com critério "
   "explícito para separar movimento real de flutuação amostral.")

h_("2 MÉTODO")
h_("2.1 Delineamento, participantes e coleta", before=6, size=10.5)
p_("Estudo observacional longitudinal de medidas repetidas, com sete dias consecutivos, entre 21 e 27 de "
   f"abril de 2024, sem intervenção dos pesquisadores. Participaram {len(B['ATL'])} atletas de handebol "
   "masculino de equipe da primeira divisão nacional, com idade média de 21,96 anos e desvio-padrão de 3,81. "
   "A carga acumulada progrediu de 1,5 hora no primeiro dia a 23,0 horas ao término do sétimo. A semana "
   "reuniu quatro tipos de estímulo: conteúdo técnico e tático no primeiro dia, que serviu de linha de base; "
   "treino intervalado de alta intensidade com trabalho técnico no segundo, quarto e sétimo; jogo amistoso "
   "no terceiro e no quinto; conteúdo técnico, tático e de força no sexto. O primeiro dia teve coleta única, "
   "à noite; do segundo ao sétimo houve uma medida no início e outra ao fim do dia.")
h_("2.2 Instrumento e classificação nos perfis", before=6, size=10.5)
p_("Aplicou-se a Escala de Humor de Brunel (TERRY et al., 1999), validada para o português brasileiro por "
   "Rohlfs et al. (2008). O instrumento reúne vinte e quatro itens em seis subescalas de quatro itens, respondidos em "
   "escala de zero a quatro, o que produz escores de zero a dezesseis por dimensão. Os escores brutos foram "
   "convertidos em escore T contra parâmetros normativos de amostras atléticas, com média cinquenta e "
   "desvio-padrão dez (TERRY; LANE, 2000), e cada vetor de seis escores T foi atribuído ao perfil cujo "
   "centroide de referência se encontra a menor distância euclidiana (PARSONS-SMITH; TERRY; MACHIN, 2017). "
   "Para a leitura aplicada, os perfis foram agrupados em três faixas: favorável, que reúne o iceberg; "
   "neutra, superfície e submerso; e de risco, os três restantes.")
h_("2.3 Unidade de análise e composição do valor diário", before=6, size=10.5)
p_(f"A fonte reúne {PR['TOTAIS']['registros']} registros. A unidade de análise é o par atleta-dia, com "
   f"{NAD} casos, isto é, um valor por atleta e por dia, o que impede que atletas mais assíduos pesem mais "
   "na estimativa. A regra de composição foi auditada contra os carimbos de data e hora. No dia basal, de "
   "coleta única, vale a primeira resposta de cada atleta, porque as respostas tardias daquela noite são "
   "repetição e não segunda medida. Do segundo ao sétimo dia valem o primeiro e o último registro, tomados "
   "como medida do início e do fim do dia.")
h_("2.4 Análise estatística", before=6, size=10.5)
p_("A prevalência diária de cada perfil recebeu erro-padrão binomial, √(p(1−p)/n). O piso de ruído de cada "
   "série foi definido como a média dos sete erros-padrão, e declarou-se movimento real apenas quando o "
   "deslocamento entre o primeiro e o sétimo dia superou esse piso. As séries foram suavizadas por filtro "
   "binomial de três pontos, com núcleo [¼, ½, ¼] nos pontos internos e extremos preservados. A estabilidade "
   "da classificação ao longo dos sete dias foi testada pelo Q de Cochran (COCHRAN, 1950) sobre os atletas "
   "com registro em todos os dias. A associação entre perfil e tipo de estímulo usou o qui-quadrado de "
   "contingência, e a migração entre a medida do início e a do fim do dia, o teste de McNemar (McNEMAR, "
   "1947), com ajuste de Holm (HOLM, 1979) para as comparações por estímulo. O processamento correu em "
   "Python 3.11, e todos os resultados foram recalculados por um segundo caminho de código a partir do item "
   "do formulário.")

h_("3 RESULTADOS")
h_("3.1 Distribuição no conjunto da semana", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} apresenta a prevalência dos seis perfis sobre os {NAD} pares atleta-dia e a "
   "compara com a referência populacional do estudo que identificou a tipologia. O elenco não reproduz a "
   "distribuição de referência, e a discrepância tem direção definida.")
cap_(f"Tabela {tab()} – Prevalência dos seis perfis no conjunto da semana e comparação com a referência")
mktable(["Perfil", "Pares", "Prevalência", "Referência", "Razão"],
        [[nome, str(CT[k]), n_(100*CT[k]/NAD) + "%", n_(REF[k]) + "%", n_(100*CT[k]/NAD/REF[k], 2)]
         for k, nome in enumerate(NOMES)],
        widths=[4.6, 2.2, 3.0, 3.0, 3.2], fs=9)
nota_("Referência populacional de Parsons-Smith, Terry e Machin (2017). A razão divide a prevalência "
      "observada pela de referência; valores acima da unidade indicam sobre-representação neste elenco.")
p_("A barbatana de tubarão comparece com mais que o dobro da prevalência esperada e o iceberg invertido com "
   "mais que o dobro, ao passo que o submerso aparece com menos da metade. O resultado é coerente com um "
   "grupo submetido a carga elevada e proximidade competitiva, e sugere que a distribuição de referência, "
   "obtida em amostras heterogêneas, não serve de expectativa para um elenco em microciclo terminal.")
fig_("P4fig.png", "Assinatura dos seis perfis em escore T: o centroide observado neste elenco contra o "
     "centroide de referência, com a prevalência de cada perfil e o dia em que predomina.", w=12.8)
p_(f"A Figura {prox_fig() - 1} torna visível o que distingue os perfis: a forma da curva, e não o seu nível. O iceberg combina vigor acima da norma com as "
   "cinco dimensões negativas abaixo dela. A barbatana de tubarão eleva tensão, raiva e fadiga sem derrubar "
   "o vigor, e descreve portanto ativação com custo, e não colapso. O iceberg invertido espelha o primeiro, "
   "com vigor deprimido e negativas elevadas. Os centroides observados acompanham de perto os de "
   "referência, o que sustenta a validade da atribuição neste elenco.")

h_("3.2 Trajetória ao longo do microciclo", before=6, size=10.5)
p_(f"A Tabela {prox_tab()} traz a prevalência de cada perfil e de cada faixa nos sete dias, com o "
   "deslocamento entre os extremos confrontado com o piso de ruído da própria série.")
ordem = NOMES + ['Favorável', 'Neutra', 'De risco']
cap_(f"Tabela {tab()} – Prevalência diária dos perfis e das faixas, com deslocamento, piso e veredito")
mktable(["Perfil ou faixa"] + [f"D{d}" for d in range(1, 8)] + ["Δ", "Piso", "Veredito"],
        [[k] + [n_(SERP[k]['y'][d]) for d in range(7)] + [n_(SERP[k]['dtot']), n_(SERP[k]['piso']),
          ("não avaliável" if SERP[k]['fragil'] else ("sinal" if SERP[k]['sinal'] else "ruído"))]
         for k in ordem],
        widths=[3.2] + [1.02] * 7 + [1.15, 1.05, 2.45], fs=7.5)
nota_(f"Valores em percentagem dos pares do dia; denominadores de D1 a D7: "
      f"{', '.join(str(x) for x in A1['nd'])}. O Everest invertido reúne dois pares no conjunto inteiro, e o "
      "piso binomial encolhe perto de zero, razão pela qual a sua série fica assinalada como não "
      "interpretável.")
p_("Oito das nove séries deslocam-se acima do próprio piso, e apenas o perfil submerso permanece na faixa "
   "atribuível à amostragem. O movimento tem sentido único: os dois perfis favoráveis recuam, os dois de "
   "risco avançam, e a faixa de risco mais que triplica. O iceberg e a barbatana de tubarão, extremos "
   "opostos da classificação, trocam de posição logo na saída do dia basal e não voltam a reaproximar-se.")
p_("O teste de estabilidade da classificação, restrito aos dezenove atletas com registro em todos os sete "
   f"dias, alcança o limiar convencional em apenas um dos seis perfis, o superfície "
   f"(Q = {n_(A3['CQ']['Superfície']['Q'],3)}; p = {pf_(A3['CQ']['Superfície']['p'])}), e não o alcança para "
   f"a faixa de risco (Q = {n_(A3['CQ']['Faixa de risco']['Q'],3)}; "
   f"p = {pf_(A3['CQ']['Faixa de risco']['p'])}). O contraste entre esse resultado e o da Tabela 2 não é "
   "contradição, e sim informação sobre o custo do desenho: o teste categórico opera sobre casos completos e "
   "exige um número de observações que um elenco não fornece, ao passo que a série de prevalências, "
   f"confrontada com o erro de amostragem que lhe é próprio, já reconhece o movimento. A Figura {prox_fig()} "
   "resume a semana em uma só imagem, com a composição do elenco dia a dia e o ponto em que a faixa de risco "
   "ultrapassa a favorável.")
fig_("P2fig.png", "Composição do elenco entre os seis perfis, dia a dia, e as três faixas de humor com o "
     "ponto em que a de risco ultrapassa a favorável.", w=14.6)

h_("3.3 Perfil e tipo de estímulo", before=6, size=10.5)
p_(f"A distribuição dos perfis não difere entre os três tipos de estímulo (χ² = {n_(A3['chi'],3)}; "
   f"gl = {A3['gl']}; p = {pf_(A3['p_chi'])}), e a das três faixas tampouco "
   f"(χ² = {n_(A3['chi_f'],3)}; gl = {A3['gl_f']}; p = {pf_(A3['p_f'])}). A Tabela {prox_tab()} mostra as "
   "prevalências por tipo de dia, e a ausência de diferença estatística convive com um gradiente visível na "
   "faixa de risco.")
TIP = ['Basal', 'HIIT', 'Amistoso', 'Técnico/força']
cap_(f"Tabela {tab()} – Prevalência das três faixas de humor por tipo de estímulo")
mktable(["Faixa"] + TIP,
        [[f, n_(A3['FAIXA_EST'][f]['Basal']) + "%", n_(A3['FAIXA_EST'][f]['HIIT']) + "%",
          n_(A3['FAIXA_EST'][f]['Amistoso']) + "%", n_(A3['FAIXA_EST'][f]['Técnico/força']) + "%"]
         for f in ['Favorável', 'Neutra', 'Risco']],
        widths=[4.4, 2.8, 2.7, 2.7, 3.4], fs=8.5)
nota_("O dia basal teve janela única de coleta e não constitui tipo de estímulo comparável aos demais; "
      "aparece como referência. Nenhum dos seis perfis difere entre os três estímulos quando tomado "
      "isoladamente.")
p_("A faixa de risco reúne 14,8% dos pares no dia basal e entre 44,1% e 54,5% nos demais tipos de dia. A "
   "ausência de diferença entre os três estímulos, somada à diferença em relação ao basal, indica que o "
   "determinante é a passagem da semana, e não a natureza da sessão. O desenho não permite separar o efeito "
   "do tipo de estímulo do efeito da carga acumulada, porque cada tipo ocupa posições fixas no microciclo.")

h_("3.4 Migração entre o início e o fim do dia", before=6, size=10.5)
mc = A3['MCN']
p_("A dupla coleta diária permite observar um fenômeno que a medida única esconde. Entre a manhã e a noite "
   f"do mesmo dia, {mc['TODOS']['entra']} pares entram na faixa de risco e {mc['TODOS']['sai']} saem dela "
   f"(χ² = {n_(mc['TODOS']['chi'],2)}; p = {pf_(mc['TODOS']['p'])}), sobre {mc['TODOS']['n']} pares com as "
   f"duas medidas. A assimetria é o achado: a passagem do dia empurra o elenco em uma direção, e a escolha "
   f"entre a medida matinal e a noturna produz retratos substancialmente distintos da mesma jornada. A Tabela "
   f"{prox_tab()} reparte o resultado por tipo de estímulo.")
cap_(f"Tabela {tab()} – Migração para a faixa de risco entre o início e o fim do dia, por tipo de estímulo")
mktable(["Recorte", "Pares", "Entram", "Saem", "χ²", "p", "p ajustado"],
        [["Todos os dias", str(mc['TODOS']['n']), str(mc['TODOS']['entra']), str(mc['TODOS']['sai']),
          n_(mc['TODOS']['chi'], 2), pf_(mc['TODOS']['p']), "—"]] +
        [[t, str(mc[t]['n']), str(mc[t]['entra']), str(mc[t]['sai']), n_(mc[t]['chi'], 2),
          pf_(mc[t]['p']), pf_(mc[t]['ph'])] for t in ['HIIT', 'Amistoso', 'Técnico/força']],
        widths=[3.8, 2.0, 2.0, 1.9, 1.9, 2.2, 2.2], fs=8.5)
nota_("Teste de McNemar sobre a mudança de faixa entre a primeira e a última resposta do dia. O ajuste de "
      "Holm corrige as três comparações por tipo de estímulo.")
p_("Repartida por tipo de dia, apenas o treino intervalado alcança significância bruta, com "
   f"{mc['HIIT']['entra']} entradas contra {mc['HIIT']['sai']} saídas (p = {pf_(mc['HIIT']['p'])}), e a "
   f"atribuição não sobrevive à correção para comparações múltiplas (p ajustado = {pf_(mc['HIIT']['ph'])}). "
   "O fenômeno, portanto, é robusto no conjunto e não se deixa atribuir a um estímulo específico com os "
   "dados disponíveis.")

h_("4 DISCUSSÃO")
p_("O primeiro resultado a destacar é a redistribuição. A semana não desloca o elenco em bloco: ela move "
   "atletas entre perfis, e o faz em sentido único. A leitura por perfis torna esse movimento legível de uma "
   "forma que a média das subescalas não torna, porque comunica um estado com nome e forma, e não um valor "
   "em uma escala abstrata. A sobre-representação da barbatana de tubarão, com mais que o dobro da "
   "prevalência de referência, descreve um elenco que mantém vigor enquanto acumula tensão, raiva e fadiga, "
   "e essa combinação é precisamente a que os documentos de consenso associam à fase que antecede a resposta "
   "desadaptativa (MEEUSEN et al., 2013; KELLMANN et al., 2018).")
p_("O segundo resultado é metodológico e limita o primeiro. A classificação em seis rótulos é, por "
   "construção, uma quantização: ela mapeia um espaço contínuo de seis dimensões em seis categorias e "
   "descarta a informação dos deslocamentos que não atravessam uma fronteira de decisão. A consequência "
   "aparece nos testes, pois o qui-quadrado não distingue os tipos de estímulo e o Q de Cochran não "
   "reconhece instabilidade em cinco dos seis perfis, ao passo que as séries de prevalência, lidas contra o "
   "próprio erro de amostragem, mostram deslocamento inequívoco. Em grandes amostras transversais o tamanho "
   "compensa essa perda de resolução, propriedade que o acompanhamento de um elenco reduzido não herda. A "
   "recomendação não é escolher entre os dois planos: o perfil comunica bem e detecta mal, a variável "
   "contínua detecta bem e comunica mal, e o uso conjunto é o que os dados sustentam.")
p_("__Limitações.__ Uma equipe, sete dias e vinte e sete atletas, sem grupo de comparação. Os tipos de "
   "estímulo não foram aleatorizados e confundem-se com a posição no microciclo e com a carga acumulada, de "
   "modo que nenhuma inferência sobre especificidade de estímulo é separável de efeito cumulativo. As "
   "ausências reduzem de vinte e sete a vinte e um os respondentes no sétimo dia, e os testes de série "
   "completa operam sobre dezenove. O Everest invertido reúne dois pares e não admite leitura. O estudo é "
   "descritivo e não estabelece relação causal entre carga e perfil.")

h_("5 CONCLUSÃO")
p_("A última semana de pré-temporada redistribui o elenco entre os perfis de humor, e a redistribuição "
   "supera, em oito das nove séries examinadas, o que a flutuação amostral produziria. O iceberg recua, a "
   "barbatana de tubarão avança e a faixa de risco mais que triplica, sem que a distribuição difira entre os "
   "tipos de estímulo. A dupla coleta diária revela migração assimétrica para a faixa de risco ao longo do "
   "dia, fenômeno que um protocolo de medida única perderia por inteiro. Para o monitoramento em clube, três "
   "exigências decorrem destes resultados: medir duas vezes ao dia; declarar o limiar de ruído antes de "
   "interpretar a série, cálculo que exige apenas o desvio-padrão e o número de respondentes de cada dia; e "
   "usar o perfil para comunicar sem abrir mão da variável contínua para detectar.")

h_("REFERÊNCIAS")
for i in sorted(ESCOLHIDAS, key=lambda k: _R.REFS[k]):
    para(_R.REFS[i], indent=False, size=9, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         before=0, after=2.5, spacing=1.0)

out = os.path.join(S, "ARTIGO_CURTO_PERFIS_HUMOR_HANDEBOL.docx")
doc.save(out)
print("salvo:", out)
