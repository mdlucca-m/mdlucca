"""Revisão do MAPPING_REVIEW.docx conforme os comentários do orientador."""
import copy
import re
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table

sys.path.insert(0, "/home/user/mdlucca/data/revisoes/handebol/mapping_formato_ijerph")
from intervencoes_detalhe import EST  # noqa: E402

ENT, SAI = sys.argv[1], sys.argv[2]
d = Document(ENT)
body = d.element.body
K = list(body.iterchildren())
W = qn


def set_text(p, texto):
    """Troca o texto do parágrafo, mantendo o pPr e o rPr do primeiro run; **x** vira negrito."""
    rpr = p.find(f"./{W('w:r')}/{W('w:rPr')}")
    rpr = copy.deepcopy(rpr) if rpr is not None else None
    for ch in list(p):
        if ch.tag != W("w:pPr"):
            p.remove(ch)
    for i, parte in enumerate(texto.split("**")):
        if not parte:
            continue
        r = OxmlElement("w:r")
        rp = copy.deepcopy(rpr) if rpr is not None else OxmlElement("w:rPr")
        for b in rp.findall(W("w:b")):
            rp.remove(b)
        if i % 2:
            rp.insert(0, OxmlElement("w:b"))
        if len(rp):
            r.append(rp)
        t = OxmlElement("w:t")
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = parte
        r.append(t)
        p.append(r)
    return p


def novo(modelo, texto, depois_de):
    p = copy.deepcopy(modelo)
    set_text(p, texto)
    depois_de.addnext(p)
    return p


def texto(el):
    return "".join(x.text or "" for x in el.iter(W("w:t")))


def troca(el, a, b, n=1):
    t = texto(el)
    assert t.count(a) == n, (a, t[:200])
    set_text(el, t.replace(a, b))


def cel(tc, txt):
    ps = tc.findall(W("w:p"))
    for p in ps[1:]:
        tc.remove(p)
    set_text(ps[0], txt)


CORPO, H2, LEG, NOTA, FONTE = K[85], K[83], K[79], K[81], K[82]
CORPO = copy.deepcopy(CORPO)
H2 = copy.deepcopy(H2)

# ------------------------------------------------------------------ resumo e abstract
set_text(K[3], "Esta revisão de mapeamento analisou o estado da arte das evidências científicas sobre as variáveis "
         "psicológicas investigadas no treinamento e na competição do handebol, com ênfase nos estudos de intervenção. "
         "A busca abrangeu oito bases de dados, sem restrição de data, com publicações até setembro de 2026, e a "
         "seleção obedeceu à estratégia PECOS. Cento e noventa e nove estudos, publicados entre 1994 e 2026, compuseram "
         "a síntese, que incluiu estatística descritiva, análise de agrupamento (cluster) das variáveis investigadas em "
         "conjunto e a descrição da evolução temporal da produção. A produção concentrou-se na Espanha (49 estudos) e no "
         "Brasil (21), em atletas profissionais ou de elite (87 estudos; 43,7%) e de categorias de formação (50; "
         "25,1%), com mediana de 63,5 participantes por estudo. Motivação e autoeficácia (80 estudos) e ansiedade e "
         "estresse (72) predominaram, ao passo que burnout e saúde mental reuniram 14 estudos. A análise de agrupamento "
         "identificou cinco temas, liderados por carga, recuperação e bem-estar (109 estudos) e por motivação e clima "
         "motivacional (67). Desde 2010, a produção cresceu de forma acelerada, e o domínio de sono, bem-estar e "
         "recuperação superou o de motivação e autoeficácia. Apenas 27 estudos adotaram delineamento experimental, e 24 "
         "testaram intervenções; 12 relataram efeito e 10 resultados mistos, com resultados mais favoráveis no treino "
         "de habilidades psicológicas (efeito em 7 de 10 estudos), embora com amostras pequenas e relato incompleto. "
         "Conclui-se que a pesquisa psicológica no handebol é ampla e recente, porém predominantemente observacional, e "
         "que as variáveis mais descritas ainda são as menos testadas por meio de intervenções.")
set_text(K[6], "This mapping review analysed the state of the art of scientific evidence on the psychological variables "
         "investigated in handball training and competition, with emphasis on intervention studies. Eight databases "
         "were searched without date restriction, covering publications up to September 2026, and study selection "
         "followed the PECOS framework. One hundred and ninety-nine studies published between 1994 and 2026 were "
         "synthesised through descriptive statistics, cluster analysis of the variables investigated together and a "
         "description of the temporal evolution of the literature. Research was concentrated in Spain (49 studies) and "
         "Brazil (21), in professional or elite (87 studies; 43.7%) and youth athletes (50; 25.1%), with a median of "
         "63.5 participants per study. Motivation and self-efficacy (80 studies) and anxiety and stress (72) "
         "predominated, whereas burnout and mental health accounted for 14 studies. The cluster analysis identified "
         "five themes, led by load, recovery and well-being (109 studies) and by motivation and motivational climate "
         "(67). Since 2010, the number of studies has grown rapidly, and sleep, well-being and recovery have overtaken "
         "motivation and self-efficacy. Only 27 studies used experimental designs and 24 tested interventions; 12 "
         "reported effects and 10 mixed results, with the most favourable results for psychological skills training "
         "(effects in 7 of 10 studies), although samples were small and reporting was incomplete. Psychological "
         "research in handball is broad and recent but predominantly observational, and the most described variables "
         "remain the least tested through interventions.")

# ------------------------------------------------------------------ introdução
troca(K[52], "envolvendo diferentes construtos, populações", "com diferentes variáveis, populações")
troca(K[54], "Diante da amplitude dos construtos investigados", "Diante da amplitude das variáveis investigadas")
troca(K[56], "capazes de orientar futuras agendas de pesquisa", "capazes de orientar pesquisas futuras")
body.remove(K[57])  # as questões de pesquisa passam para o Método (comentário do orientador)

# ------------------------------------------------------------------ método
set_text(K[63], "Esta revisão de mapeamento foi conduzida de acordo com recomendações metodológicas para scoping "
         "reviews e evidence mapping (JAMES; RANDALL; HADDAWAY, 2016; KHALIL et al., 2025; LI et al., 2025) e seguiu a "
         "estrutura das revisões de mapeamento publicadas pelo Laboratório de Psicologia do Esporte e do Exercício "
         "(Lape) (ANDRADE et al., 2023; DOMINSKI et al., 2021; TRUPPEL et al., 2025). O relato seguiu os itens "
         "aplicáveis do Preferred Reporting Items for Systematic Reviews and Meta-Analyses Extension for Scoping "
         "Reviews (PRISMA-ScR) (TRICCO et al., 2018).")
troca(K[68], "As buscas foram realizadas entre maio e setembro de 2026 nas bases",
      "As buscas foram realizadas até setembro de 2026, com coleta entre maio e setembro desse ano, nas bases")
troca(K[84], "e as divergências foram resolvidas por uma terceira avaliação (concordância de 0,955; κ = 0,927) "
             "(COHEN, 1960; LANDIS; KOCH, 1977); esse coeficiente expressa",
      "e as divergências foram resolvidas por uma terceira avaliação, com concordância de 95,5% entre as passagens "
      "(COHEN, 1960; LANDIS; KOCH, 1977); esse valor expressa")
set_text(K[85], "A síntese foi descritiva. Os estudos foram descritos por frequências absolutas e percentuais, e o "
         "tamanho da amostra, por mediana, média e desvio-padrão. O tamanho da amostra foi comparado entre "
         "delineamentos, sexo, níveis competitivos, contextos e períodos e relacionado ao ano de publicação por testes "
         "não paramétricos, com finalidade exploratória e nível de significância de 5%. Para descrever a evolução "
         "temporal, examinou-se a participação anual de cada domínio entre 2010 e 2026, a fim de identificar o período "
         "de maior crescimento da produção; nas figuras, os valores anuais são apresentados como pontos unidos por uma "
         "linha.")
a = novo(H2, "2.5 Análise de agrupamento (cluster)", K[85])
a = novo(CORPO, "Para identificar quais variáveis psicológicas foram investigadas em conjunto, realizou-se uma análise "
         "de agrupamento (cluster) baseada na coocorrência das variáveis nos mesmos estudos (CALLON; COURTIAL; LAVILLE, "
         "1991), em três etapas.", a)
a = novo(CORPO, "Na primeira etapa, construiu-se uma rede em que cada variável psicológica corresponde a um ponto e "
         "cada ligação entre duas variáveis corresponde ao número de estudos que as investigaram simultaneamente. Na "
         "segunda etapa, as variáveis foram reunidas em agrupamentos pelo algoritmo de Louvain, que junta as variáveis "
         "mais ligadas entre si e menos ligadas às variáveis dos demais agrupamentos (BLONDEL et al., 2008). A qualidade "
         "da separação entre os agrupamentos foi expressa pela modularidade, que varia de 0 a 1; na prática, valores "
         "entre 0,3 e 0,7 indicam agrupamentos bem definidos (NEWMAN; GIRVAN, 2004). Cada agrupamento, denominado "
         "tema, recebeu o nome das variáveis mais frequentes.", a)
a = novo(CORPO, "Na terceira etapa, cada tema foi posicionado no mapa temático segundo duas medidas: a centralidade, que "
         "indica a força das ligações do tema com os demais temas, e a densidade, que indica a força das ligações entre "
         "as variáveis do próprio tema (CALLON; COURTIAL; LAVILLE, 1991; COBO et al., 2011). A combinação dessas medidas "
         "classifica cada tema em um de quatro quadrantes: temas motores, com centralidade e densidade altas, isto é, "
         "bem desenvolvidos e importantes para a área; temas básicos e transversais, com centralidade alta e densidade "
         "baixa, ligados a muitos outros temas; temas de nicho, com centralidade baixa e densidade alta, desenvolvidos, "
         "mas isolados; e temas emergentes ou em declínio, com centralidade e densidade baixas.", a)
a = novo(CORPO, "Complementarmente, calcularam-se a proporção de estudos em que cada domínio foi investigado "
         "isoladamente e a razão de coocorrência, que compara o número de estudos que investigaram dois domínios em "
         "conjunto com o número esperado caso fossem investigados de forma independente; valores acima de 1 indicam "
         "que os domínios aparecem juntos mais do que o esperado. Por fim, os pares de domínios mais estudados em "
         "conjunto foram descritos em três períodos (1994 a 2015, 2016 a 2020 e 2021 a 2026), para identificar os "
         "núcleos de estudo de cada fase.", a)
a = novo(H2, "2.6 Questões de pesquisa", a)
a = novo(CORPO, "As questões de pesquisa (QP) que orientaram a extração dos dados, a análise e a organização dos "
         "resultados foram as seguintes:", a)
QPS = ["Qual é o volume da produção científica e quais são as características dos estudos e das populações "
       "investigadas?",
       "Quais variáveis psicológicas foram estudadas e como se distribuem e se agrupam entre os domínios?",
       "Em quais contextos, países e períodos essas variáveis foram investigadas?",
       "Quais delineamentos foram empregados, quais são os métodos e os protocolos das intervenções testadas e qual é "
       "a qualidade metodológica desses estudos?",
       "Quais resultados foram relatados e quais lacunas permanecem na literatura?"]
for i, q in enumerate(QPS, 1):
    a = novo(CORPO, f"**QP{i}.** {q}", a)
novo(CORPO, "Os resultados são apresentados a seguir na mesma sequência das cinco questões de pesquisa. Cada "
     "subseção inicia com a pergunta, seguida de uma resposta direta e dos dados que a sustentam.", a)
body.remove(K[86])

# ------------------------------------------------------------------ resultados: pergunta, resposta direta e dados
RESP = {
    90: (1, "Foram identificados 199 estudos, publicados entre 1994 e 2026, com crescimento a partir de 2017 e mais "
            "da metade (57,8%) publicada de 2020 em diante. Predominaram atletas profissionais ou de elite (87 estudos) "
            "e de categorias de formação (50), amostras adultas e juvenis e amostras com mediana de 63,5 "
            "participantes; 57 estudos não informaram o sexo dos participantes. Os dados que sustentam essa resposta "
            "são apresentados a seguir e nas Figuras 1 e 2."),
    99: (2, "Os estudos investigaram 40 variáveis, organizadas em sete domínios, com predomínio de motivação e "
            "autoeficácia (80 estudos) e de ansiedade e estresse (72). A análise de agrupamento reuniu as variáveis em "
            "cinco temas: carga, recuperação e bem-estar foi o maior e o mais transversal, e motivação e clima "
            "motivacional e ansiedade, autoconfiança e equipe foram os temas motores. Burnout e saúde mental "
            "permaneceram pouco estudados (14 estudos). Os detalhes constam das Figuras 3 e 4 e do Quadro 1."),
    116: (3, "As variáveis foram investigadas sobretudo na competição (32,7%) e na combinação de treinamento e "
             "competição (33,7%); a ansiedade e o estresse predominaram na competição, e a motivação, as habilidades "
             "mentais e a recuperação, no treinamento. A Espanha (49 estudos) e o Brasil (21) lideraram a produção, "
             "que envolveu 51 países. Ao longo do tempo, a motivação perdeu participação, e o sono, o bem-estar e a "
             "recuperação passaram a ser o domínio mais frequente nos anos recentes (Figuras 5 e 6 e Quadro 1)."),
    132: (4, "Predominaram os delineamentos observacionais (142 estudos; 71,4%), e apenas 27 estudos (13,6%) foram "
             "experimentais. Vinte e quatro estudos testaram intervenções, agrupadas em seis tipos: treino de "
             "habilidades psicológicas (10), feedback ou ação do treinador (4), prática do handebol (4), recuperação e "
             "sono (3), nutrição (2) e música (1). Os protocolos duraram de uma sessão a 12 semanas, com amostras de 8 "
             "a 112 participantes (Figura 7 e Apêndice B). Pelo EPHPP, a qualidade foi forte em 5 dos 23 estudos avaliados, "
             "moderada em 8 e fraca em 10 (Tabela 3)."),
    139: (5, "A maioria dos estudos (62,3%) relatou efeito ou associação entre as variáveis psicológicas e o "
             "treinamento ou a competição. Entre as 24 intervenções, 12 relataram efeito, 10 resultados mistos, uma "
             "foi apenas descritiva e uma não teve resultados acessíveis, com resultados mais favoráveis no treino "
             "de habilidades psicológicas. As principais lacunas são a ausência de intervenções sobre burnout e saúde "
             "mental, o pequeno número de intervenções sobre ansiedade e motivação, as amostras pequenas e a ausência "
             "de ensaios randomizados nas categorias de formação."),
}
for idx, (q, r) in RESP.items():
    p = novo(CORPO, f"**QP{q}. {QPS[q - 1]}**", K[idx])
    novo(CORPO, f"**Resposta.** {r}", p)

# QP1: figuras logo após os parágrafos correspondentes
ant = K[92]
for el in K[95:99]:
    ant.addnext(el)
    ant = el
troca(K[93], "e de formação (50; 25,1%) (Figura 2C, D).",
      "e de formação (50; 25,1%) (Figura 2C, D). Os 87 estudos com atletas profissionais ou de elite formam o maior "
      "subconjunto da revisão.")
set_text(K[94], "O tamanho da amostra, relatado em 186 estudos, variou de 6 a 745 participantes (mediana de 63,5; média "
         "de 126,5 ± 148,5) (Figura 2E). O tamanho da amostra diferiu entre delineamentos (p < 0,001), com as maiores "
         "amostras nos estudos transversais (mediana de 112) e as menores nos experimentais (26,5), entre as "
         "categorias de sexo (p < 0,001) e entre níveis competitivos (p = 0,039), mas não entre contextos (p = 0,064) "
         "nem entre períodos (p = 0,128). As amostras foram menores nos estudos mais recentes (p = 0,022), e a "
         "proporção de estudos experimentais não variou entre os períodos (p = 0,378).")
ant = K[94]
for el in K[101:105]:
    ant.addnext(el)
    ant = el

# QP2
troca(K[100], "O mapa temático organizou-se em cinco temas (modularidade de 0,445; Figura 3): carga, recuperação e "
              "bem-estar (109 estudos), tema básico e transversal; motivação e clima motivacional (67) e ansiedade, "
              "autoconfiança e equipe (47), temas motores; habilidades psicológicas e resiliência (29), tema em "
              "declínio; e competência percebida e diversão (11), tema de nicho.",
      "A análise de agrupamento organizou as variáveis em cinco temas, com modularidade de 0,445, valor que indica "
      "agrupamentos bem definidos (Figura 3): carga, recuperação e bem-estar (109 estudos), tema básico e transversal, "
      "isto é, ligado a muitos outros temas; motivação e clima motivacional (67) e ansiedade, autoconfiança e equipe "
      "(47), temas motores, isto é, bem desenvolvidos e centrais para a área; habilidades psicológicas e resiliência "
      "(29), tema em declínio; e competência percebida e diversão (11), tema de nicho, desenvolvido, mas pouco ligado "
      "aos demais.")
troca(K[106], "Mapa temático das variáveis psicológicas investigadas no handebol (QP2)",
      "Mapa temático dos agrupamentos (clusters) de variáveis psicológicas investigadas no handebol (QP2)")
troca(K[108], "os cinco temas da rede de coocorrência", "os cinco temas da análise de agrupamento")

# QP3 e Quadro 1 (sem a razão de coocorrência nas células)
troca(K[123], "sobretudo com a motivação (lift de 1,46 e 1,24)",
      "sobretudo com a motivação, com frequência 1,46 e 1,24 vez maior que a esperada")
q1 = Table(K[129], d)
for row in q1.rows:
    for c in row.cells:
        t = c.text
        n = re.sub(r"\((\d+); \d+,\d+\)", r"(\1)", t)
        n = n.replace("Relações principais (estudos; lift)", "Variáveis mais estudadas em conjunto (estudos)")
        if n != t:
            cel(c._tc, n)
set_text(K[130], "Nota: números entre parênteses: estudos que investigaram as duas variáveis em conjunto; participação: "
         "percentual dos estudos de cada ano que investigaram a variável, de 2010 a 2026; núcleos de estudo: pares de "
         "domínios mais estudados em conjunto em cada período.")

# QP5
set_text(K[140], "Dos 199 estudos, 124 (62,3%) relataram efeito ou associação, 44 (22,1%) resultados mistos, 10 (5,0%) "
         "ausência de efeito e 15 (7,5%) foram descritivos. Entre as 24 intervenções, 12 relataram efeito, 10 "
         "resultados mistos, uma foi apenas descritiva e uma não teve resultados acessíveis. O treino de "
         "habilidades psicológicas teve efeito em 7 de 10 estudos e resultados mistos em outros 3, com efeitos sobre a "
         "autoeficácia, a motivação autodeterminada, a tomada de decisão, o bem-estar mental e a demanda mental "
         "percebida, além do desempenho técnico e no arremesso. O feedback e a ação do treinador tiveram efeito em 1 de 4 "
         "estudos e resultados mistos nos demais, que dependeram do tipo de feedback e da satisfação com o treinador. "
         "A prática do handebol teve efeito em 2 de 4 estudos, sobre a motivação e a diversão; a recuperação e o sono, "
         "em 1 de 3; a nutrição, em 1 de 2; e a música teve resultado misto. Na leitura integral, 14 intervenções "
         "empregaram distribuição aleatória, quatro delas em delineamento cruzado, mas 12 das 24 tiveram menos de 30 "
         "participantes (mediana de 31,5), e as "
         "amostras dos estudos com efeito (mediana de 35,5) foram maiores que as dos demais (mediana de 24,5). Quatro das "
         "dez intervenções de treino psicológico avaliaram apenas o desempenho técnico, e somente 3 estudos informaram "
         "o tamanho do efeito. Quanto às lacunas, 22 das 42 combinações entre intervenção e desfecho (52%) não "
         "apresentaram estudos (Figura 7B), e a razão entre estudos que investigaram cada domínio e intervenções que o "
         "tiveram como desfecho atingiu 18 para 1 na ansiedade e 10 para 1 na motivação; burnout e saúde mental não "
         "tiveram nenhuma intervenção.")
# tabela-síntese das respostas (nova Tabela 3)
a = novo(CORPO, "A Tabela 4 sintetiza as respostas às cinco questões de pesquisa e indica as figuras, os quadros e as "
         "tabelas em que cada resultado é apresentado.", K[140])
a = novo(LEG, "Tabela 4: Síntese das respostas às cinco questões de pesquisa", a)
tb = copy.deepcopy(K[80])
a.addnext(tb)
a = tb
LIN = [["QP", "Resposta principal", "Onde consultar"],
       ["QP1", "199 estudos (1994 a 2026), 57,8% a partir de 2020; Espanha (49) e Brasil (21); atletas profissionais ou "
               "de elite (87) e de formação (50); mediana de 63,5 participantes; sexo omitido em 57 estudos",
        "Figuras 1 e 2"],
       ["QP2", "40 variáveis em sete domínios; motivação e autoeficácia (80) e ansiedade e estresse (72) predominaram; "
               "cinco temas na análise de agrupamento, com carga, recuperação e bem-estar (109) como tema básico e "
               "transversal; burnout e saúde mental em 14 estudos", "Figuras 3 e 4; Quadro 1"],
       ["QP3", "Competição (32,7%) e treinamento e competição (33,7%); ansiedade na competição e motivação, habilidades "
               "mentais e recuperação no treinamento; 51 países; crescimento do sono, do bem-estar e da recuperação e "
               "recuo da motivação", "Figuras 5 e 6; Quadro 1"],
       ["QP4", "142 estudos observacionais (71,4%) e 27 experimentais (13,6%); 24 intervenções em seis tipos, com "
               "treino de habilidades psicológicas (10) e ação do treinador (4) mais frequentes; de uma sessão a 12 "
               "semanas; qualidade forte em 5, moderada em 8 e fraca em 10 estudos", "Figura 7; Tabela 3; Apêndice B"],
       ["QP5", "124 estudos (62,3%) com efeito ou associação; 12 intervenções com efeito e 10 com resultados mistos; "
               "nenhuma intervenção sobre burnout ou saúde mental; 22 das 42 combinações de intervenção e desfecho sem "
               "estudos", "Figura 7B; Tabela 5; Apêndice B"]]
LARG = [900, 6172, 2000]
grid = tb.find(W("w:tblGrid")).findall(W("w:gridCol"))
for gc, w in zip(grid, LARG):
    gc.set(W("w:w"), str(w))
for tr, lin in zip(tb.findall(W("w:tr")), LIN):
    for j, (tc, v) in enumerate(zip(tr.findall(W("w:tc")), lin)):
        tcw = tc.find(f"./{W('w:tcPr')}/{W('w:tcW')}")
        if tcw is not None:
            tcw.set(W("w:w"), str(LARG[j]))
        cel(tc, v)
        if j == 1 and tr is not tb.findall(W("w:tr"))[0]:
            for p in tc.findall(W("w:p")):
                jc = p.find(f"./{W('w:pPr')}/{W('w:jc')}")
                if jc is not None:
                    jc.set(W("w:val"), "left")
a = novo(NOTA, "Nota: QP: questão de pesquisa.", a)
a = novo(FONTE, "Fonte: elaborada pelos autores (2026).", a)

# ------------------------------------------------------------------ discussão
troca(K[151], "convergem com a metanálise que associa estresse e burnout",
      "convergem com a revisão sistemática com síntese quantitativa que associa estresse e burnout")
troca(K[161], "Esse padrão, aqui denominado lacuna de translação, decorre de delineamentos",
      "Essa distância entre as variáveis mais descritas e as mais testadas pode decorrer de delineamentos")
troca(K[162], "Com mediana de 33 participantes", "Com mediana de 31,5 participantes")
troca(K[162], "nos ensaios randomizados (7 de 10) e nos quase-experimentais (6 de 11)",
      "nos estudos com distribuição aleatória (7 de 14) e nos demais (5 de 10)")
troca(K[166], "o treino de habilidades psicológicas foi a mais frequente e a mais consistente, com efeito em 9 de 10 "
              "estudos.",
      "o treino de habilidades psicológicas foi a mais frequente e a que reuniu mais efeitos, com efeito em 7 de 10 "
      "estudos e resultados mistos em outros 3.")
troca(K[166], "Esses resultados convergem com as metanálises sobre autodiálogo",
      "Esses resultados convergem com as revisões com síntese quantitativa sobre autodiálogo")
troca(K[167], "e de efeitos documentados em metanálise (MARTIN; CARRON; BURKE, 2009)",
      "e de efeitos documentados em revisão com síntese quantitativa (MARTIN; CARRON; BURKE, 2009)")
troca(K[167], "em consonância com a metanálise de intervenções baseadas na autodeterminação",
      "em consonância com a revisão quantitativa das intervenções baseadas na autodeterminação")
troca(K[167], "o tema de carga, recuperação e bem-estar foi o maior da rede, com 109 estudos",
      "o tema de carga, recuperação e bem-estar foi o maior agrupamento, com 109 estudos")
troca(K[167], " Pela abordagem GRADE (GUYATT et al., 2008), apenas o treino psicológico e o feedback do treinador "
              "alcançaram certeza moderada.", "")
novo(CORPO, "Quanto às próximas revisões, os 87 estudos com atletas profissionais ou de elite permitem uma revisão "
     "sistemática específica sobre a psicologia do esporte no treinamento e na competição de atletas de elite do "
     "handebol, com avaliação da qualidade metodológica e da magnitude dos efeitos.", K[171])
troca(K[172], "A Tabela 3 converte", "A Tabela 5 converte")
troca(K[174], "Tabela 3:", "Tabela 5:")
troca(K[181], "das redes de coocorrência entre variáveis", "da análise de agrupamento das variáveis")

# ------------------------------------------------------------------ conclusão por questão de pesquisa
set_text(K[188], "Esta revisão de mapeamento respondeu às cinco questões de pesquisa propostas, e as respostas podem "
         "ser resumidas da seguinte forma:")
CONC = ["**QP1.** A produção reúne 199 estudos, publicados entre 1994 e 2026 e concentrados a partir de 2020, "
        "sobretudo na Espanha e no Brasil, com atletas profissionais ou de elite e de categorias de formação.",
        "**QP2.** Motivação e autoeficácia e ansiedade e estresse foram os domínios mais investigados; a análise de "
        "agrupamento identificou cinco temas, com carga, recuperação e bem-estar como o tema mais amplo e transversal, "
        "enquanto burnout e saúde mental permaneceram pouco estudados.",
        "**QP3.** A ansiedade e o estresse predominaram na competição, e a motivação, as habilidades mentais e a "
        "recuperação, no treinamento; ao longo do tempo, o sono, o bem-estar e a recuperação ganharam espaço, e a "
        "motivação perdeu participação.",
        "**QP4.** Predominaram os estudos observacionais; apenas 27 estudos foram experimentais e 24 testaram "
        "intervenções, a maioria de treino de habilidades psicológicas e de ação do treinador, com amostras pequenas; "
        "pelo EPHPP, apenas 5 dos 23 estudos avaliados tiveram qualidade forte.",
        "**QP5.** A maioria dos estudos relatou efeito ou associação, mas, entre as intervenções, somente 12 relataram "
        "efeito, e nenhuma visou o burnout ou a saúde mental, o que caracteriza as principais lacunas da área."]
a = K[188]
for c_ in CONC:
    a = novo(CORPO, c_, a)
body.remove(K[189])
body.remove(K[190])

# ------------------------------------------------------------------ Apêndice B com os dados conferidos
NOMES = {"Martínez": 2, "Hasan": 81, "Metan": 127, "Benešová": 145, "Martiny": 153, "Lepir": 170, "Norouzi": 173,
         "Upadhyay": 179, "Saket": 196, "Staiano": 199, "Paul Meeûs": 16, "Soto": 94, "García-Herrero": 119,
         "Malfa": 171, "Hornstrup": 61, "Tomar": 111, "Sánchez-Sáez": 128, "Martins": 192, "L'Hermette": 89,
         "Nishida": 107, "Nuell": 174, "Assunção": 57, "Bougrine": 132, "Khazdozi": 50}
DIRB = {"Efeito": "Efeito", "Misto": "Misto", "Não determinável": "Não determ.", "Descritivo": "Descritivo"}
tB = Table(K[430], d)
feitos = set()
for row in tB.rows:
    tcs = row._tr.findall(W("w:tc"))
    if len(tcs) < 6:
        continue
    nome = "".join(x.text or "" for x in tcs[0].iter(W("w:t")))
    n = next((v for k, v in NOMES.items() if nome.startswith(k)), None)
    if n is None:
        continue
    e = EST[n]
    cel(tcs[1], f"{e['mod']}; " + ("amostra não relatada" if e["n"].startswith("Não") else e["n"]))
    cel(tcs[2], f"{e['desc']}; {e['dur'][0].lower() + e['dur'][1:]}")
    cel(tcs[3], e["desf"])
    cel(tcs[4], e["res"])
    cel(tcs[5], DIRB[e["dir"]])
    feitos.add(n)
assert len(feitos) == 24, sorted(set(EST) - feitos)
troca(K[431], "Nota: ECR: ensaio clínico randomizado; QE: quase-experimental; n.r.: não relatado; sem.: semanas.",
      "Nota: dados conferidos na extração com citação literal da fonte; amostra e delineamento corrigidos pela leitura "
      "integral quando diferiam da planilha. Direção: efeito, efeito ou associação relatada; misto, efeito em parte "
      "dos desfechos ou apenas dentro de um grupo; descritivo, sem teste do efeito; não determ., fonte sem resultados.")

exec(open("revisar_qualidade_estrategias.py").read())
exec(open("revisar_aprofundamento.py").read())
# ------------------------------------------------------------------ referências novas e não citadas
refs = [el for el in K[222:421] if el.tag == W("w:p") and texto(el).strip()]
NOVAS = ["ARMIJO-OLIVO, S. et al. Assessment of study quality for systematic reviews: a comparison of the Cochrane "
         "Collaboration Risk of Bias Tool and the Effective Public Health Practice Project Quality Assessment Tool: "
         "methodological research. Journal of Evaluation in Clinical Practice, v. 18, n. 1, p. 12-18, 2012. DOI: "
         "https://doi.org/10.1111/j.1365-2753.2010.01516.x.",
         "THOMAS, B. H. et al. A process for systematically reviewing the literature: providing the research evidence "
         "for public health nursing interventions. Worldviews on Evidence-Based Nursing, v. 1, n. 3, p. 176-184, 2004. "
         "DOI: https://doi.org/10.1111/j.1524-475X.2004.04006.x.",
         "COBO, M. J. et al. An approach for detecting, quantifying, and visualizing the evolution of a research field: "
         "a practical application to the Fuzzy Sets Theory field. Journal of Informetrics, v. 5, n. 1, p. 146-166, "
         "2011. DOI: https://doi.org/10.1016/j.joi.2010.10.002.",
         "NEWMAN, M. E. J.; GIRVAN, M. Finding and evaluating community structure in networks. Physical Review E, v. "
         "69, n. 2, e026113, 2004. DOI: https://doi.org/10.1103/PhysRevE.69.026113."]
for nv in NOVAS:
    alvo = next(r for r in refs if texto(r) > nv)
    p = copy.deepcopy(alvo)
    set_text(p, nv)
    alvo.addprevious(p)

# corpo do texto (sem referências) para conferir citações
fim_txt = next(i for i, el in enumerate(body.iterchildren()) if texto(el).strip() == "REFERÊNCIAS")
todos = list(body.iterchildren())
corpo_txt = " ".join(texto(el) for el in todos[:fim_txt]) + " " + " ".join(
    texto(el) for el in todos if el.tag == W("w:tbl") or "APÊNDICE" in texto(el)[:20])
corpo_up = corpo_txt.upper()
removidas = []
for el in todos[fim_txt + 1:]:
    t = texto(el).strip()
    if el.tag != W("w:p") or not t or t.startswith("APÊNDICE"):
        if t.startswith("APÊNDICE"):
            break
        continue
    m = re.match(r"([^,;.(]+)", t)
    ano = re.findall(r"\b(19\d\d|20\d\d)\b", t)
    sob = m.group(1).strip().upper()
    if not ano:
        continue
    if sob not in corpo_up:
        removidas.append(t[:90])
        body.remove(el)
print("referências removidas (não citadas):")
for r in removidas:
    print("  -", r)

# ------------------------------------------------------------------ comentários resolvidos: remover marcas
for tag in ("w:commentRangeStart", "w:commentRangeEnd"):
    for el in body.iter(W(tag)):
        pass
for el in list(body.iter(W("w:commentRangeStart"))) + list(body.iter(W("w:commentRangeEnd"))):
    el.getparent().remove(el)
for ref in list(body.iter(W("w:commentReference"))):
    r = ref.getparent()
    r.getparent().remove(r)
for rel in list(d.part.rels.values()):
    if rel.reltype.endswith("/comments"):
        tp = rel.target_part
        if hasattr(tp, "element"):
            for c in list(tp.element):
                tp.element.remove(c)
        else:
            tp._blob = re.sub(rb"<w:comment\b.*?</w:comment>", b"", tp.blob, flags=re.S)
TROCAS_F = [("handebol, caracterizando simultaneamente os contextos estudados", "handebol, com a caracterização simultânea dos contextos estudados"),
            ("handebol, caracterizando os estudos, as populações", "handebol, com a caracterização dos estudos, das populações"),
            ("devem ser interpretados considerando que a pré-classificação", "devem ser interpretados com a ressalva de que a pré-classificação"),
            ("rotinas pré-desempenho envolvendo autodiálogo", "rotinas pré-desempenho com autodiálogo"),
            ("As variáveis psicológicas, incluindo processos cognitivos", "As variáveis psicológicas, como os processos cognitivos"),
            ("Além disso, a heterogeneidade dos delineamentos", "Além disso, a diversidade dos delineamentos")]
for a_, b_ in TROCAS_F:
    alvos = [p for p in body.iter(W("w:p")) if a_ in texto(p)]
    assert len(alvos) == 1, (a_, len(alvos))
    set_text(alvos[0], texto(alvos[0]).replace(a_, b_))
d.save(SAI)
print("ok", SAI)
