"""Artigo 1: perfis de humor em atletas de handebol de elite.

Restrições de redação: nenhum travessão, nenhum traço de meia risca e nenhum
gerúndio.
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "artigo4p"))
import fonte as F  # noqa: E402
from dados import PARSONS, PERFIL_DIA  # noqa: E402

NORMATIVO = {"Iceberg": 29.4, "Submerso": 25.5, "Barbatana tubarão": 17.3,
             "Superfície": 14.8, "Iceberg invertido": 10.3,
             "Everest invertido": 2.7}

TITULO = ("Análise do perfil de humor em atletas de handebol de elite: os "
          "novos perfis e suas características")
SUBTITULO = "Estudo descritivo em um microciclo pré-competitivo"

ABERTURA = [
 ("RESUMO",
  "O perfil de humor é um dos instrumentos mais usados no acompanhamento "
  "psicológico de atletas, e a descrição de seis agrupamentos distintos "
  "renovou o campo a partir de 2017. Nenhum estudo aplicou esses agrupamentos "
  "ao handebol. Este estudo descreve a distribuição dos seis perfis em 27 "
  "atletas de handebol masculino de primeira divisão acompanhados por sete "
  "dias, caracteriza cada subescala da Escala de Humor de Brunel nesta "
  "população e estabelece percentis de referência para a modalidade. Os três "
  "perfis associados a risco à saúde mental somaram 19,9% das observações, "
  "valor próximo aos 26,5% da única amostra brasileira classificada pelo "
  "mesmo critério, que reúne os dois sexos e uma faixa etária mais ampla. O "
  "perfil superfície reuniu 56,8% das observações, 42,0 pontos percentuais "
  "acima da norma, excesso que decorre da padronização dentro da amostra na "
  "ausência de normas de escore da modalidade. Quatro das seis subescalas "
  "apresentaram efeito piso entre 49,6% e 80,5%, mais de três vezes o limite "
  "de 15%, o que restringe a margem de medida e faz o critério de Morgan "
  "superestimar o padrão favorável. Nenhuma subescala foi confiável em uma "
  "leitura isolada, com ICC entre 0,31 e 0,59, e todas passaram de 0,76 na "
  "média de sete dias. O estudo entrega a primeira descrição dos seis perfis "
  "em handebol e os primeiros percentis de referência do instrumento para a "
  "modalidade."),
 ("PALAVRAS-CHAVE",
  "humor; handebol; Escala de Humor de Brunel; perfil de humor; psicometria."),
]

FONTE_TABELA = "Fonte: dados da pesquisa (2026)."
FONTE_FIGURA = "Fonte: elaborada pelos autores (2026)."

_ORDEM = ["Vigor", "Fadiga", "Tensão", "Depressão", "Raiva", "Confusão"]

TABELAS = {

"descritiva": {
 "numero": 1,
 "titulo": ("Caracterização das seis subescalas do BRUMS e da Perturbação "
            "Total do Humor nesta amostra"),
 "cabecalho": ["Subescala", "Média", "Desvio-padrão", "Mediana",
               "Intervalo interquartil", "Assimetria", "Curtose",
               "Piso (%)"],
 "linhas": [[n] + [F.br(v, 2) if isinstance(v, float) else str(v)
                   for v in F.DESCRITIVA[n]]
            for n in ["PTH (TMD)"] + _ORDEM],
 "nota": ("Nota: PTH é a Perturbação Total do Humor, calculada pela soma das "
          "cinco subescalas negativas menos o vigor. Subescalas de 0 a 16 "
          "pontos. Piso é o percentual de respostas no valor mínimo da "
          "subescala. Assimetria acima de 2 e curtose acima de 7 indicam "
          "afastamento grave da normalidade. Fonte primária: Tabela 3 do "
          "relatório completo."),
},

"percentis": {
 "numero": 2,
 "titulo": ("Percentis de referência das subescalas do BRUMS para atletas de "
            "handebol masculino de elite"),
 "cabecalho": ["Subescala", "P5", "P25", "P50", "P75", "P95"],
 "linhas": [[n] + [str(v) for v in F.PERCENTIS[n]]
            for n in ["PTH (TMD)"] + _ORDEM],
 "nota": ("Nota: percentis observados sobre todas as coletas do microciclo. "
          "Na ausência de normas de escore T para handebol, estes percentis "
          "servem de referência provisória para a modalidade e substituem, "
          "para uso aplicado, a comparação com normas de população geral. "
          "Fonte primária: Tabela 74 do relatório completo."),
},

"psicometria": {
 "numero": 3,
 "titulo": ("Confiabilidade interna e estabilidade entre dias de cada "
            "subescala"),
 "cabecalho": ["Subescala", "Alfa", "Alfa ordinal", "Ômega ordinal",
               "Duas metades", "Item-total mínimo", "ICC de uma coleta",
               "ICC da média de sete dias"],
 "linhas": [
  [n] + [F.br(v, 2) if v is not None else "n.e."
         for v in F.CONFIABILIDADE[n]]
  + [F.br(F.ESTABILIDADE[n][0], 2), F.br(F.ESTABILIDADE[n][1], 2)]
  for n in sorted(F.CONFIABILIDADE, key=lambda k: -F.CONFIABILIDADE[k][0])
 ],
 "nota": ("Nota: n.e. indica coeficiente não estimável, porque a matriz "
          "policórica não convergiu nas subescalas com efeito piso extremo. "
          "O ICC de uma coleta é o ICC(1,1) e o da média de sete dias é o "
          "ICC(1,7), obtido pela fórmula de Spearman e Brown. Fonte "
          "primária: Tabelas 6 e 7 do relatório completo."),
},

"correlacao": {
 "numero": 4,
 "titulo": "Correlação entre as seis subescalas do BRUMS",
 "cabecalho": ["Subescala", "Tensão", "Depressão", "Raiva", "Vigor",
               "Fadiga"],
 "linhas": [
  [linha] + [F.br(F.CORRELACAO[(linha, col)], 2)
             if (linha, col) in F.CORRELACAO else ""
             for col in ["Tensão", "Depressão", "Raiva", "Vigor", "Fadiga"]]
  for linha in ["Depressão", "Raiva", "Vigor", "Fadiga", "Confusão"]
 ],
 "nota": ("Nota: correlações entre os fatores da análise fatorial "
          "confirmatória, que ajustou bem ao modelo de seis fatores "
          f"(CFI = {F.br(F.AJUSTE['CFI'], 3)}; "
          f"RMSEA = {F.br(F.AJUSTE['RMSEA'], 3)}). O valor de 0,67 entre "
          "vigor e fadiga é o mais alto do bloco energético e sustenta a "
          "leitura de eixo bipolar. Fonte primária: Tabelas 10 e 11 do "
          "relatório completo."),
},

"perfis": {
 "numero": 5,
 "titulo": ("Os seis perfis de humor: definição, prevalência normativa e "
            "prevalência nesta amostra"),
 "cabecalho": ["Perfil", "Definição pelo padrão das seis subescalas",
               "Norma (%)", "Amostra (%)", "Diferença (p.p.)"],
 "linhas": [
  ["Iceberg",
   "Vigor alto; tensão, depressão, raiva, fadiga e confusão baixas",
   F.br(29.4, 1), F.br(PARSONS["Iceberg"][0], 1),
   F.sinal(PARSONS["Iceberg"][0] - 29.4, 1)],
  ["Submerso", "As seis subescalas abaixo da média, o vigor incluído",
   F.br(25.5, 1), F.br(PARSONS["Submerso"][0], 1),
   F.sinal(PARSONS["Submerso"][0] - 25.5, 1)],
  ["Barbatana de tubarão",
   "O vigor mais baixo de todos os perfis, com fadiga superior à de qualquer "
   "outro perfil exceto o Everest invertido",
   F.br(17.3, 1), F.br(PARSONS["Barbatana tubarão"][0], 1),
   F.sinal(PARSONS["Barbatana tubarão"][0] - 17.3, 1)],
  ["Superfície", "As seis subescalas próximas da média",
   F.br(14.8, 1), F.br(PARSONS["Superfície"][0], 1),
   F.sinal(PARSONS["Superfície"][0] - 14.8, 1)],
  ["Iceberg invertido",
   "Vigor baixo com tensão, depressão, raiva, fadiga e confusão altas",
   F.br(10.3, 1), F.br(PARSONS["Iceberg invertido"][0], 1),
   F.sinal(PARSONS["Iceberg invertido"][0] - 10.3, 1)],
  ["Everest invertido",
   "Vigor baixo, tensão e fadiga altas, e depressão, raiva e confusão muito "
   "altas", F.br(2.7, 1), F.br(PARSONS["Everest invertido"][0], 1),
   F.sinal(PARSONS["Everest invertido"][0] - 2.7, 1)],
 ],
 "nota": ("Nota: definições e prevalências normativas conforme a amostra A de "
          "Parsons-Smith, Terry e Machin (2017), sobre escores T de população "
          "geral. A prevalência desta amostra usa padronização dentro da "
          "própria amostra, na ausência de normas de escore T para handebol, "
          "e por isso a coluna de diferença mede efeito de método antes de "
          "medir efeito de população."),
},

"distribuicao": {
 "numero": 6,
 "titulo": ("Distribuição dos perfis no primeiro e no último dia do "
            "microciclo e nos dois tipos de dia"),
 "cabecalho": ["Perfil", "Global (%)", "Dia 1 (%)", "Dia 7 (%)",
               "Dias de HIIT (%)", "Dias sem HIIT (%)"],
 "linhas": [[nome] + [F.br(v, 1) for v in valores]
            for nome, valores in PARSONS.items()],
 "nota": ("Nota: pelo critério de Morgan, aplicado em paralelo, a proporção "
          f"de atletas em perfil iceberg passa de {F.br(PERFIL_DIA[1][0], 1)}% "
          f"no dia 1 para {F.br(PERFIL_DIA[7][0], 1)}% no dia 7, e a de humor "
          f"perturbado de {F.br(PERFIL_DIA[1][1], 1)}% para "
          f"{F.br(PERFIL_DIA[7][1], 1)}%. Os dois critérios não são "
          "equivalentes: o de Morgan exige apenas que o vigor supere as cinco "
          "negativas, enquanto o de Parsons-Smith exige proximidade a um "
          "centroide específico. Fonte primária: Tabelas 20 e 21 do relatório "
          "completo."),
},
}

_RISCO = sum(PARSONS[k][0] for k in
             ("Barbatana tubarão", "Iceberg invertido", "Everest invertido"))

BLOCOS = [
("h1", "1 INTRODUÇÃO"),
("p", "O humor responde à carga de treino antes que o desempenho caia, tem "
      "custo de coleta baixo e por isso ocupa lugar central no monitoramento "
      "psicológico de atletas desde a descrição do padrão iceberg, em que o "
      "vigor supera as cinco subescalas negativas (Morgan, 1980). O modelo "
      "original opõe esse padrão favorável ao seu inverso, e essa dicotomia "
      "sustentou décadas de pesquisa. Ela tem, porém, um limite conhecido: o "
      "perfil iceberg é o padrão típico de atletas, bem-sucedidos ou não, e "
      "por isso discrimina desempenho menos do que se afirmou (Terry e Lane, "
      "2000). Uma equipe apresenta, em uma mesma semana, estados que a "
      "oposição entre dois padrões não distingue."),
("p", "A análise de agrupamento sobre as seis subescalas da Escala de Humor "
      "de Brunel identificou seis perfis distintos e teoricamente "
      "interpretáveis: iceberg, superfície, submerso, barbatana de tubarão, "
      "iceberg invertido e Everest invertido (Parsons-Smith, Terry e Machin, "
      "2017). Os três últimos associam-se a graus crescentes de risco à saúde "
      "mental. Os seis perfis foram replicados em contexto esportivo geral "
      "(Quartiroli e outros, 2018), em amostras de países distintos (Han e "
      "outros, 2020) e, com a versão brasileira do instrumento, em 898 "
      "atletas de elite e de base de um clube do Rio de Janeiro, entre os "
      "quais 26,5% apresentaram um dos três perfis de risco (Rohlfs, Noce e "
      "Wilke, 2024)."),
("p", "O handebol permanece fora desse mapa. O levantamento que conduzimos "
      "sobre a produção internacional em psicologia do esporte no handebol "
      "entre 2006 e 2026 reúne 525 estudos, dos quais 32 aferem humor ou "
      "afeto, apenas um com desenho longitudinal, e nenhum aplica os seis "
      "perfis. O precedente mais próximo acompanha medidas biológicas e "
      "psicológicas ao longo de uma temporada em handebolistas, com o "
      "instrumento anterior e sem classificação por perfil (Bresciani e "
      "outros, 2010). Falta também o pressuposto de qualquer classificação: "
      "existem normas de escore para amostras esportivas em geral (Terry e "
      "Lane, 2000), mas nenhuma específica do handebol."),
("p", "Este estudo tem três objetivos. O primeiro é descrever a distribuição "
      "dos seis perfis de humor em atletas de handebol masculino de elite. O "
      "segundo é caracterizar o comportamento de cada subescala nesta "
      "população, com atenção ao efeito piso e à estabilidade da medida entre "
      "dias. O terceiro é estabelecer percentis de referência da modalidade, "
      "que é o que permite classificar observações futuras sem dependência da "
      "própria amostra."),

("h1", "2 MÉTODO"),
("h2", "2.1 Participantes e delineamento"),
("p", f"Participaram {F.AMOSTRA['atletas']} atletas de handebol masculino de "
      f"primeira divisão, com {F.AMOSTRA['idade']} anos de idade e "
      f"{F.AMOSTRA['experiencia']} anos de experiência na modalidade, "
      f"distribuídos por posição em {F.AMOSTRA['posicao']}. "
      f"{F.AMOSTRA['completos']} completaram as sete coletas. O delineamento "
      "é observacional e descritivo, com medidas repetidas intraindividuais "
      "ao longo do microciclo de sete dias que antecede a competição. A "
      "unidade de análise é a observação diária, e não o atleta, porque o "
      "perfil de humor é um estado e não um traço."),
("p", "O estudo foi aprovado pelo comitê de ética em pesquisa da instituição "
      "sob o protocolo [inserir número do CAAE], e todos os participantes "
      "assinaram termo de consentimento livre e esclarecido. O número de "
      "observações válidas, com o fluxo de atletas por dia e por coleta, "
      "consta do material suplementar."),
("h2", "2.2 Instrumento"),
("p", "O humor foi aferido pela versão brasileira da Escala de Humor de "
      "Brunel, com 24 itens em escala Likert de cinco pontos e seis "
      "subescalas de 0 a 16 pontos: tensão, depressão, raiva, vigor, fadiga e "
      "confusão. A instrução de resposta foi a de momento presente, e não a "
      "de semana anterior, o que importa para a comparação com outros "
      "estudos: o mesmo instrumento produz escores mais altos sob a instrução "
      "retrospectiva (Rohlfs, Noce e Wilke, 2024). A Perturbação Total do "
      "Humor resume o perfil pela soma das cinco subescalas negativas menos o "
      "vigor, de modo que valores menores indicam humor mais favorável."),
("h2", "2.3 Classificação dos perfis"),
("p", "O procedimento original padroniza as seis subescalas em escore T, "
      "aplica análise de agrupamento hierárquica aglomerativa com distância "
      "euclidiana quadrática pelo método de Ward para fixar o número de "
      "agrupamentos, refina as fronteiras por k-médias e confirma a "
      "classificação por análise discriminante. A solução de seis "
      "agrupamentos foi verificada por inspeção do gráfico de sedimentação "
      "(Parsons-Smith, Terry e Machin, 2017)."),
("p", "Nesta amostra não há normas de escore T para handebol de elite, e o "
      "tamanho amostral não comporta a análise de agrupamento original. As "
      "seis subescalas foram, portanto, padronizadas dentro da própria "
      "amostra, e cada observação foi atribuída ao centroide canônico mais "
      "próximo pela distância euclidiana sobre as seis dimensões "
      "padronizadas. Essa decisão está declarada aqui porque afeta "
      "diretamente a prevalência relatada na seção 3.3, e é discutida na "
      "seção 4. Em paralelo, o critério de Morgan foi aplicado a cada "
      "observação: há perfil iceberg quando o vigor supera todas as cinco "
      "subescalas negativas."),
("h2", "2.4 Análise"),
("p", "As subescalas foram descritas por média, desvio-padrão, mediana, "
      "intervalo interquartil, assimetria, curtose e percentual de respostas "
      "no valor mínimo. Considera-se presente o efeito piso quando mais de "
      "15% das respostas caem no valor mínimo possível (Terwee e outros, "
      "2007). A confiabilidade interna foi estimada pelo alfa de Cronbach, "
      "pelo alfa e pelo ômega ordinais sobre matriz policórica e pelo método "
      "das duas metades. A estabilidade entre dias foi estimada pelo "
      "coeficiente de correlação intraclasse de uma coleta e da média de sete "
      "dias, esta pela fórmula de Spearman e Brown. A estrutura de seis "
      "fatores foi testada por análise fatorial confirmatória com estimador "
      "robusto para dados ordinais e erro-padrão agrupado por atleta. As "
      "análises foram conduzidas em R, com os pacotes psych, lavaan e "
      "semTools. Não houve imputação: cada análise usa as observações "
      "disponíveis, e o denominador de cada estimativa está declarado na nota "
      "da tabela correspondente."),

("h1", "3 RESULTADOS"),
("h2", "3.1 Distribuição das subescalas"),
("p", "As seis subescalas se dividem em dois blocos claros (Tabela 1). Vigor "
      "e fadiga ocupam a faixa central da escala, com médias de 5,70 e 5,65 "
      "pontos, assimetria próxima de zero e piso abaixo de 9%. Tensão, "
      "depressão, raiva e confusão ficam junto ao mínimo, com médias entre "
      "0,45 e 1,60 ponto, assimetria de até 3,73 e curtose de até 16,96."),
("tab", "descritiva"),
("fig", "a1_distribuicao.png", 16.0,
 "Figura 1 - Distribuição observada de cada subescala por percentis (A) e "
 "percentual de respostas no valor mínimo da escala (B)"),
("p", "A Figura 1 mostra o alcance do problema. Em confusão, o percentil 75 "
      "ainda é zero: três quartos das observações estão no mínimo da escala. "
      "Em depressão e raiva, o percentil 50 é zero. Quatro das seis "
      "subescalas ficam entre 49,6% e 80,5% de respostas no piso, mais de "
      "três vezes o limite de 15% a partir do qual o efeito é considerado "
      "presente (Terwee e outros, 2007), o que significa que elas não têm "
      "margem para registrar aumento de sintoma nesta população. Os percentis "
      "observados de todas as subescalas estão na Tabela 2."),
("tab", "percentis"),
("h2", "3.2 Propriedades da medida"),
("p", "A consistência interna é alta em depressão e raiva, com ômega ordinal "
      "de 0,94 e 0,93, adequada em fadiga e vigor e insuficiente em tensão, "
      "com alfa de 0,43 (Tabela 3). Em confusão e tensão a matriz policórica "
      "não convergiu, o que é consequência direta do efeito piso: sem "
      "variação nas respostas não há covariância para estimar."),
("tab", "psicometria"),
("fig", "a1_psicometria.png", 16.0,
 "Figura 2 - Consistência interna de cada subescala (A) e ganho de "
 "estabilidade da média de sete dias sobre a coleta isolada (B)"),
("p", "O painel B da Figura 2 traz o achado de maior consequência prática. "
      "Nenhuma subescala atinge 0,60 de estabilidade em uma coleta isolada, e "
      "todas passam de 0,76 na média de sete dias. Uma leitura isolada do "
      "instrumento não descreve o atleta de forma confiável nesta população; "
      "a média semanal descreve."),
("p", "A estrutura de seis fatores ajustou bem aos dados "
      f"(CFI = {F.br(F.AJUSTE['CFI'], 3)}; "
      f"RMSEA = {F.br(F.AJUSTE['RMSEA'], 3)}). A correlação entre os fatores "
      "(Tabela 4) mostra vigor e fadiga com 0,67, o valor mais alto do bloco "
      "energético, e confusão com tensão em 0,75, o mais alto do bloco de "
      "afeto negativo."),
("tab", "correlacao"),
("h2", "3.3 Prevalência dos perfis"),
("p", "O perfil superfície reúne 56,8% das observações, seguido do iceberg "
      "com 13,8%, do submerso com 9,4%, do iceberg invertido com 9,0%, da "
      "barbatana de tubarão com 7,2% e do Everest invertido com 3,7% "
      "(Tabela 5). Os três perfis associados a risco à saúde mental, isto é, "
      "barbatana de tubarão, iceberg invertido e Everest invertido, somam "
      f"{F.br(_RISCO, 1)}% das observações."),
("tab", "perfis"),
("fig", "fig_prevalencia.png", 16.0,
 "Figura 3 - Prevalência de cada perfil na amostra normativa e nesta amostra "
 "(A) e efeito da padronização interna sobre essa prevalência (B)"),
("p", "A diferença mais visível é o excesso de perfil superfície, 42,0 pontos "
      "percentuais acima da norma, com déficit correspondente nos perfis "
      "iceberg, submerso e barbatana de tubarão. Essa diferença não é achado "
      "clínico: ela decorre da padronização dentro da amostra, que coloca a "
      "média do próprio grupo na linha de água e comprime todas as "
      "observações em direção ao centro. Os dois perfis mais negativos, "
      "iceberg invertido e Everest invertido, ficam a 1,3 e a 1,0 ponto "
      "percentual da norma, o que sugere que a compressão atinge sobretudo os "
      "perfis intermediários e preserva os extremos negativos."),
("p", "Os dois critérios de classificação não concordam entre si, e a "
      "diferença é grande. No primeiro dia, o critério de Morgan classifica "
      "71,4% das observações como perfil iceberg, contra 21,4% pelo critério "
      "de Parsons-Smith (Tabela 6). A discrepância é esperada e decorre da "
      "definição: o critério de Morgan exige apenas que o vigor supere as "
      "cinco subescalas negativas, condição que quatro subescalas presas ao "
      "piso tornam fácil de satisfazer, enquanto o critério de Parsons-Smith "
      "exige proximidade a um centroide específico das seis dimensões. Em uma "
      "população com efeito piso acentuado, o critério de Morgan superestima "
      "a prevalência do padrão favorável."),
("tab", "distribuicao"),

("h1", "4 DISCUSSÃO"),
("p", "Até onde alcança o levantamento descrito na introdução, este é o "
      "primeiro estudo a aplicar os seis perfis de humor ao handebol. Quatro "
      "resultados merecem destaque, e os quatro são tanto substantivos quanto "
      "metodológicos."),
("p", "O primeiro é o efeito piso. Em atletas saudáveis de elite no período "
      "pré-competitivo, tensão, depressão, raiva e confusão concentram entre "
      "49,6% e 80,5% das respostas no valor mínimo. Isso não é falha de "
      "instrumento: é a descrição correta de uma população sem sintoma "
      "clínico. A consequência prática é que essas quatro subescalas servem "
      "para compor o índice total e para sinalizar caso individual atípico, "
      "mas não para acompanhar variação de carga no dia a dia da equipe. A "
      "consequência metodológica é mais séria: o piso impede a estimativa dos "
      "coeficientes ordinais de duas delas e distorce a classificação por "
      "critérios que dependem da ordem entre subescalas, como mostra a "
      "divergência entre os dois critérios na seção 3.3."),
("p", "O segundo é a estabilidade. Com ICC de uma coleta entre 0,31 e 0,59, "
      "nenhuma leitura isolada sustenta decisão sobre um atleta. A média de "
      "sete dias eleva o coeficiente para a faixa de 0,76 a 0,91. A "
      "recomendação que decorre disso é direta: o monitoramento deve "
      "trabalhar com média móvel, e não com o valor do dia. Esse resultado "
      "também qualifica a leitura do perfil, que é atribuído a uma observação "
      "isolada e herda dela a instabilidade."),
("p", "O terceiro é a comparação com a única amostra brasileira classificada "
      "pelos mesmos seis perfis. Entre 898 atletas de elite e de base de um "
      f"clube do Rio de Janeiro, 26,5% apresentaram um perfil de risco; aqui, "
      f"{F.br(_RISCO, 1)}% (Rohlfs, Noce e Wilke, 2024). A diferença tem duas "
      "explicações plausíveis e não excludentes. A amostra brasileira reúne "
      "os dois sexos e uma faixa etária de 12 a 44 anos, e nela os perfis de "
      "risco foram mais frequentes entre mulheres; a nossa é masculina e "
      "adulta. E a amostra brasileira usou também a instrução de semana "
      "anterior, que produz escores mais altos que a instrução de momento "
      "presente adotada aqui. As duas diferenças empurram na mesma direção, o "
      "que torna a prevalência menor observada no handebol coerente com a "
      "literatura, e não contraditória."),
("p", "O quarto é a ausência de normas. A padronização dentro da amostra "
      "resolve a falta de escores T, mas ao custo de tornar a prevalência "
      "incomparável com a literatura, como a Figura 3 quantifica. A saída "
      "está na Tabela 2: os percentis de referência publicados aqui "
      "constituem a primeira régua específica de handebol de elite para o "
      "instrumento e permitem que estudos futuros classifiquem observações "
      "sem depender da própria amostra."),
("h2", "4.1 Aplicação prática"),
("p", "Para a comissão técnica, três decisões decorrem destes resultados. A "
      "primeira é o que medir: no acompanhamento diário bastam vigor, fadiga "
      "e o índice total, porque as demais subescalas não variam o suficiente "
      "para informar. A segunda é como ler: a média móvel de sete dias, e não "
      "o escore do dia, é a unidade com confiabilidade adequada para decisão "
      "sobre um atleta. A terceira é quando agir: um atleta classificado em "
      "barbatana de tubarão, iceberg invertido ou Everest invertido em duas "
      "leituras consecutivas merece conversa individual, porque esses três "
      "perfis somam uma em cada cinco observações desta amostra e são os que "
      "a literatura associa a risco."),
("h2", "4.2 Limitações"),
("p", "Quatro limitações restringem a generalização. A amostra tem 27 atletas "
      "de uma única equipe, dos quais 19 completaram todas as coletas, e o "
      "período monitorado é um único microciclo pré-competitivo, o que "
      "concentra a observação em um momento particular da temporada. A "
      "classificação por proximidade a centroide não reproduz a análise de "
      "agrupamento original: o procedimento indicado para amostras deste "
      "tamanho é a análise de k-médias semeada com os centroides canônicos, "
      "adotada na amostra brasileira de referência (Rohlfs, Noce e Wilke, "
      "2024), e a diferença entre os dois procedimentos ainda não foi "
      "quantificada nestes dados. A ausência de normas de escore T para a "
      "modalidade obriga à padronização interna, cujo efeito a Figura 3 "
      "quantifica. E a amostra é masculina, o que impede qualquer extensão "
      "aos achados de sexo relatados na literatura."),

("h1", "5 CONCLUSÃO"),
("p", "Em atletas de handebol masculino de elite, os seis perfis de humor "
      "descritos na literatura são identificáveis, e os três associados a "
      f"risco à saúde mental somam {F.br(_RISCO, 1)}% das observações, valor "
      "próximo ao da única amostra brasileira classificada pelo mesmo "
      "critério. A distribuição entre os perfis intermediários, porém, "
      "depende da régua: sem normas de escore da modalidade, a padronização "
      "interna concentra as observações no perfil superfície e não é "
      "comparável à norma. Quatro das seis subescalas apresentam efeito piso "
      "acima de 49% e não têm margem de medida útil para o acompanhamento "
      "diário. Nenhuma subescala é confiável em uma leitura isolada, e todas "
      "passam a ser na média de sete dias. Os percentis de referência "
      "apresentados aqui são a primeira régua específica da modalidade e são "
      "a contribuição de uso imediato deste estudo."),

("h1", "REFERÊNCIAS"),
("nota", "BRESCIANI, G. e outros. Monitoring biological and psychological "
         "measures throughout an entire season in male handball players. "
         "European Journal of Sport Science, v. 10, n. 6, p. 377-384, 2010."),
("nota", "HAN, C. S. Y. e outros. Mood profiling in Singapore: cross-cultural "
         "validation and potential applications of mood profile clusters. "
         "Frontiers in Psychology, v. 11, art. 665, 2020."),
("nota", "MORGAN, W. P. Test of champions: the iceberg profile. Psychology "
         "Today, v. 14, p. 92-108, 1980."),
("nota", "PARSONS-SMITH, R. L.; TERRY, P. C.; MACHIN, M. A. Identification "
         "and description of novel mood profile clusters. Frontiers in "
         "Psychology, v. 8, art. 1958, 2017."),
("nota", "QUARTIROLI, A. e outros. Cross-cultural validation of mood profile "
         "clusters in a sport and exercise context. Frontiers in Psychology, "
         "v. 9, art. 1949, 2018."),
("nota", "ROHLFS, I. C. P. M.; NOCE, F.; WILKE, C. F. Prevalence of specific "
         "mood profile clusters among elite and youth athletes at a Brazilian "
         "sports club. Sports, v. 12, n. 7, art. 195, 2024."),
("nota", "TERRY, P. C.; LANE, A. M. Normative values for the profile of mood "
         "states for use with athletic samples. Journal of Applied Sport "
         "Psychology, v. 12, n. 1, p. 93-109, 2000."),
("nota", "TERRY, P. C.; PARSONS-SMITH, R. L. Mood profiling for sustainable "
         "mental health among athletes. Sustainability, v. 13, n. 11, art. "
         "6116, 2021."),
("nota", "TERWEE, C. B. e outros. Quality criteria were proposed for "
         "measurement properties of health status questionnaires. Journal of "
         "Clinical Epidemiology, v. 60, n. 1, p. 34-42, 2007."),
]
