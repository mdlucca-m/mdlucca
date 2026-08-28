"""Conteúdo do relatório de resultados.

Restrições de redação pedidas: nenhum travessão e nenhum gerúndio no texto
descritivo. Verificadas por scripts/resultados/verificar_estilo.py.

Toda estatística citada vem de uma tabela do Artigo_Final_, e a origem está
declarada na nota de cada tabela.
"""
from __future__ import annotations

TITULO = ("Respostas psicológicas ao treinamento pré-competitivo em atletas "
          "de handebol: resultados de um microciclo de sete dias")

SUBTITULO = ("Caracterização da carga, trajetória do humor e recomendações "
             "para a comissão técnica")

# ═══════════════════════════════════════════════════════════ 1 · abertura ═══
SECOES: list[dict] = [

{"titulo": "1 DELINEAMENTO E MOMENTO DA COLETA", "paragrafos": [
 "Os resultados a seguir descrevem um estudo de acompanhamento: observacional, "
 "longitudinal e prospectivo, com medidas repetidas intraindividuais, "
 "conduzido em condições reais de treinamento. Não houve aleatorização, grupo "
 "de controle nem manipulação experimental da carga. A equipe treinou conforme "
 "o planejamento da comissão técnica, e o estudo registrou a resposta "
 "psicológica a esse planejamento.",

 "A distinção importa para a leitura de tudo o que se segue. O que os dados "
 "autorizam são recomendações de monitoramento e de distribuição de carga. Não "
 "autorizam inferência causal sobre o efeito isolado de um tipo de treino, "
 "porque nenhum tipo de treino foi atribuído pelo pesquisador.",

 "Participaram 27 atletas de handebol masculino de primeira divisão, com 22,2 "
 "anos de idade em média (desvio-padrão de 3,7 anos; amplitude de 17,8 a 38,2 "
 "anos) e 11,3 anos de experiência na modalidade (desvio-padrão de 3,2 anos). "
 "Dezenove atletas, isto é, 70% da amostra, completaram as sete coletas.",

 "O período monitorado foi o microciclo de sete dias entre 21 e 27 de abril de "
 "2024, que corresponde à última semana de treinamento da fase "
 "pré-competitiva, imediatamente anterior ao início da competição. Esse "
 "posicionamento no calendário é o que confere consequência prática aos "
 "achados: o estado observado no sétimo dia é o estado com que a equipe "
 "chegaria à véspera do primeiro jogo.",

 "O humor foi aferido pela Escala de Humor de Brunel (BRUMS), com 24 itens em "
 "escala Likert de cinco pontos e seis subescalas de 0 a 16 pontos: tensão, "
 "depressão, raiva, vigor, fadiga e confusão. A Perturbação Total do Humor "
 "(PTH) resume o perfil em um índice único, pela soma das cinco subescalas "
 "negativas menos o vigor. Valores menores de PTH indicam humor mais "
 "favorável. As coletas ocorreram em dois momentos por dia de treino, a "
 "primeira tomada como pré-sessão e a última como pós-sessão.",
]},

# ═══════════════════════════════════════════════════ 2 · carga de treino ═══
{"titulo": "2 CARACTERIZAÇÃO DA CARGA DE TREINO", "paragrafos": [
 "A Tabela 1 reúne, para cada dia do microciclo, o que foi exigido dos atletas "
 "e como o humor respondeu. É essa justaposição que permite passar da "
 "descrição da curva para a explicação do que a produziu.",
], "tabela": "carga", "pos_tabela": [
 "O microciclo alterna dois tipos de dia. Os dias 2, 4 e 7 combinam treino "
 "intervalado de alta intensidade (HIIT) e treino técnico-tático em 2,0 a 2,5 "
 "horas, com volume reduzido e intensidade elevada. Nesses dias a frequência "
 "cardíaca de pico ficou entre 97% e 99% da máxima e a percepção subjetiva de "
 "esforço entre 8,5 e 9,1 pontos, o que caracteriza sessões quase máximas. Os "
 "dias 3, 5 e 6 concentram treino técnico-tático, treinamento de força e jogos "
 "amistosos em 4,5 a 5,0 horas, isto é, o dobro do volume, sem o estímulo "
 "intervalado. O dia 1 foi de repouso e serve como linha de base.",

 "A intensidade do HIIT foi individualizada pelo teste incremental de "
 "Carminatti. A velocidade de pico obtida no início do mesociclo, de 14,96 "
 "km·h⁻¹, definiu a carga, e as sessões foram corridas a 104% dessa "
 "velocidade individual.",
], "figura": "figura1_carga.png",
   "legenda_figura": ("Figura 1 - Duração e número de sessões por dia do "
                      "microciclo, com destaque para os dias de HIIT.")},

# ═══════════════════════════════════════════════ 3 · trajetória do humor ═══
{"titulo": "3 TRAJETÓRIA DIÁRIA DO HUMOR", "paragrafos": [
 "A Tabela 2 apresenta a média diária de cada variável ao longo dos sete dias. "
 "As médias foram estimadas por modelo linear misto com intercepto aleatório "
 "por atleta, e não por média aritmética simples. A escolha se justifica pela "
 "estrutura dos dados: as observações estão aninhadas dentro de dias, que por "
 "sua vez estão aninhados dentro de atletas, o que gera dependência entre "
 "medidas. O modelo misto acomoda essa dependência, acomoda também o "
 "desbalanceamento entre atletas, que contribuíram com três a sete dias cada, "
 "e não exclui casos incompletos.",
], "tabela": "diario", "pos_tabela": [
 "A perturbação total do humor acompanha a alternância entre os dois tipos de "
 "dia de forma nítida. Parte de 2,52 no repouso, sobe para 4,61 no primeiro "
 "dia de HIIT, recua para 2,87 no dia seguinte, de volume alto, torna a subir "
 "para 4,76 no segundo dia de HIIT e recua novamente para 2,19. Nos dias de "
 "alto volume sem HIIT, portanto, o humor retorna a valores próximos ao de "
 "repouso, ao passo que os dias de alta intensidade elevam a perturbação. A "
 "resposta é governada mais pela intensidade do estímulo do que pelo tempo "
 "total de treino, e é isso que explica por que a variação diária é pequena "
 "justamente nos dias mais longos.",

 "Dois dias rompem esse padrão, e são os mais informativos. O dia 6, de alto "
 "volume e sem HIIT, apresenta perturbação de 4,80, equivalente à dos dias de "
 "HIIT. Às vésperas do encerramento do microciclo, o volume acumulado passa a "
 "produzir sozinho o efeito que antes exigia intensidade. O dia 7 destaca-se "
 "de todos: perturbação de 8,28, isto é, 3,3 vezes a do repouso e 1,7 vez a do "
 "dia mais perturbado até então. Não se trata do efeito de uma sessão "
 "isolada, porque a carga do dia 7 é a mesma dos dias 2 e 4. Trata-se do "
 "acúmulo de seis dias sobre um organismo que já não recupera no mesmo ritmo.",

 "O vigor descreve trajetória distinta e complementar. Cai de forma abrupta do "
 "repouso para o primeiro dia de treino, de 7,61 para 5,66, estabiliza entre "
 "5,3 e 5,7 ao longo de toda a semana e só então despenca no dia 7, para 4,49, "
 "que é o menor valor do microciclo. A fadiga percorre o caminho espelhado, de "
 "3,96 para 7,46. A leitura conjunta descreve um sistema que absorve a carga "
 "enquanto consegue e cede no último dia.",

 "O efeito do dia é estatisticamente significativo para as quatro variáveis do "
 "eixo energia-fadiga. No modelo misto, a perturbação total cresce em média "
 "0,43 ponto por dia (p = 0,010), a fadiga física 0,34 ponto por dia, a fadiga "
 "0,33 ponto por dia e o vigor decresce 0,26 ponto por dia. O coeficiente de "
 "determinação marginal do modelo, que quantifica a variância explicada apenas "
 "pelos efeitos fixos, é de 0,541; o condicional, que inclui a variância "
 "atribuível ao atleta, é de 0,766. A diferença entre os dois indica que "
 "parcela substancial da variância é estável entre atletas, e não atribuível "
 "ao dia.",
], "figura": "figura2_trajetoria.png",
   "legenda_figura": ("Figura 2 - Trajetória diária da perturbação total do "
                      "humor, da fadiga e do vigor ao longo do microciclo.")},

# ══════════════════════════════════════════════════ 4 · resposta aguda ═══
{"titulo": "4 RESPOSTA AGUDA AO TREINO", "paragrafos": [
 "A Tabela 3 apresenta a variação entre a coleta pré-sessão e a pós-sessão, "
 "por variável. Duas decisões analíticas sustentam esses números e precisam "
 "ser explicitadas, porque alteram substancialmente o resultado.",

 "A primeira é a correção da pseudorreplicação. Cada atleta contribuiu com "
 "cerca de cinco pares pré-pós ao longo da semana, o que totaliza "
 "aproximadamente 135 pares. Tratar esses 135 pares como observações "
 "independentes inflaria artificialmente a significância, porque eles "
 "pertencem a apenas 27 atletas. Para evitar essa inflação, as diferenças "
 "foram agregadas por atleta antes do teste, o que toma o atleta como unidade "
 "amostral. O custo de ignorar essa estrutura pode ser quantificado: com "
 "correlação intraclasse próxima de 0,60 e cerca de 17 observações por atleta, "
 "o efeito de desenho é de aproximadamente 10,5, de modo que o conjunto de "
 "observações equivale a cerca de 43 observações independentes. Quando a "
 "correção é aplicada, dois efeitos antes significativos deixam de sê-lo.",

 "A segunda é a correção para comparações múltiplas. Como nove variáveis foram "
 "testadas, a probabilidade de ao menos um falso positivo cresce com o número "
 "de testes. Aplicou-se o controle da taxa de descobertas falsas pelo "
 "procedimento de Benjamini-Hochberg, e a coluna final da Tabela 3 traz o "
 "valor de p já corrigido.",
], "tabela": "agudo", "pos_tabela": [
 "Apenas cinco das nove variáveis sobrevivem à correção, e todas pertencem ao "
 "eixo energia-fadiga: fadiga física, fadiga, perturbação total, vigor e "
 "fadiga mental. As quatro subescalas negativas restantes, isto é, depressão, "
 "tensão, raiva e confusão, não apresentam resposta aguda detectável.",

 "Essa ausência de resposta tem explicação de medida, e não apenas "
 "substantiva. Essas quatro subescalas apresentam efeito piso severo: 80,5% "
 "das respostas de confusão, 67,1% das de depressão, 59,6% das de raiva e "
 "49,6% das de tensão situam-se no valor mínimo da escala. Quando quase todos "
 "os atletas já se encontram no menor valor possível, resta pouca variância "
 "para que qualquer efeito se manifeste. A decomposição da variância confirma "
 "a leitura por outra via: tensão e depressão são fortemente traço, com "
 "correlação intraclasse de atleta próxima de 67%, e deixam apenas cerca de "
 "21% de variância residual para o estado agudo. Como uma sessão de treino só "
 "pode mover a componente de estado, subescalas com pouca variância residual "
 "têm, por construção, pouco a responder.",

 "O tamanho de efeito é reportado em duas convenções, e a distinção entre elas "
 "evita superestimação de magnitude. O dz padroniza a diferença pelo desvio "
 "intraindividual e é sensível à mudança dentro do atleta. O d de Cohen "
 "padroniza pelo desvio total, que inclui a variância entre atletas, e é o "
 "diretamente comparável aos pontos de corte clássicos de 0,2, 0,5 e 0,8. "
 "Aplicar os cortes de Cohen a um dz produz interpretação inflada de "
 "magnitude, razão pela qual as duas colunas constam lado a lado.",

 "Os intervalos de confiança de 95% foram obtidos por reamostragem "
 "bootstrap de clusters, com 2.000 reamostragens de atletas inteiros. Esse "
 "procedimento preserva a estrutura de dependência intra-atleta, que uma "
 "reamostragem de observações isoladas destruiria.",

 "A confirmação multivariada corrobora o achado por duas vias independentes. O "
 "teste de Hotelling T² pareado sobre o vetor de diferenças agregado por "
 "atleta resulta em F(6, 21) = 2,52, com p = 0,054 e distância de Mahalanobis "
 "de 0,83. A PERMANOVA, com distância euclidiana sobre variáveis padronizadas "
 "e 5.000 permutações restritas ao atleta, resulta em pseudo-F = 3,36 com p = "
 "0,0002 para o contraste entre perfil pré e pós-sessão. A concordância entre "
 "uma via paramétrica e uma via de permutação, que dispensa a suposição de "
 "normalidade, foi adotada como critério de robustez.",

 "A análise bayesiana quantifica a força da evidência de forma independente do "
 "valor de p. Os fatores de Bayes JZS sobre as diferenças agregadas por atleta "
 "indicam evidência extrema para a fadiga física (BF₁₀ = 2.444), forte para a "
 "perturbação total (BF₁₀ = 22,4) e para a fadiga (BF₁₀ = 11,3), e moderada "
 "para o vigor (BF₁₀ = 5,9). Para depressão, tensão, raiva e confusão a "
 "evidência é anedótica ou favorável à hipótese nula, o que converge com o "
 "resultado do teste de significância.",
], "figura": "figura3_resposta_aguda.png",
   "legenda_figura": ("Figura 3 - Tamanho de efeito da resposta aguda "
                      "pré-sessão para pós-sessão, com intervalo de confiança "
                      "de 95%.")},

# ═══════════════════════════════════════════ 5 · HIIT versus volume ═══
{"titulo": "5 COMPARAÇÃO ENTRE DIAS DE HIIT E DIAS DE VOLUME", "paragrafos": [
 "A Tabela 4 compara a resposta aguda nos dias com HIIT e nos dias de volume "
 "sem HIIT, com as diferenças agregadas por atleta.",
], "tabela": "tipo_dia", "pos_tabela": [
 "Os dias de HIIT apresentam resposta aguda maior para fadiga física, fadiga e "
 "perturbação total. Para o vigor a diferença se inverte, embora com "
 "intervalos de confiança amplamente sobrepostos entre as duas condições.",

 "A leitura desse contraste exige cautela por duas razões, e ambas são "
 "estruturais. A primeira é o confundimento entre intensidade e volume: neste "
 "microciclo os dias de HIIT são também os de menor volume total de treino, de "
 "modo que os dois componentes não podem ser dissociados. O que a comparação "
 "sustenta é a associação entre o tipo de dia e a resposta do humor, não a "
 "atribuição do efeito a um dos dois componentes isoladamente.",

 "A segunda razão é que o efeito específico do HIIT não sobrevive à análise de "
 "robustez. A diferença em diferenças, que isola o efeito agudo atribuível ao "
 "tipo de sessão, resulta em contrastes não significativos para todas as "
 "variáveis: vigor com p = 0,845, fadiga com p = 0,268, perturbação total com "
 "p = 0,833 e fadiga física com p = 0,255. Os E-values correspondentes, entre "
 "1,72 e 1,95, indicam que um fator de confusão de magnitude modesta seria "
 "suficiente para explicar o efeito de nível do dia. No modelo multivariado, o "
 "termo de interação entre condição e momento não é significativo (F = 0,27; "
 "p = 0,703), ao passo que o termo de semana, que capta o acúmulo, é "
 "significativo (p = 0,002).",

 "A conclusão que os dados sustentam, portanto, é que o salto agudo dentro da "
 "sessão não é atribuível especificamente ao HIIT, e sim comum a qualquer "
 "treino intenso. O efeito específico dos dias de HIIT reside no nível do dia, "
 "não na magnitude da resposta aguda.",
], "figura": "figura4_tipo_de_dia.png",
   "legenda_figura": ("Figura 4 - Resposta aguda por tipo de dia, com "
                      "intervalo de confiança de 95%.")},

# ══════════════════════════════════════════════════ 6 · perfis de humor ═══
{"titulo": "6 PERFIS DE HUMOR", "paragrafos": [
 "Cada observação foi classificada de duas formas complementares. A primeira "
 "aplica o critério de Morgan: há perfil iceberg quando o vigor supera todas "
 "as cinco subescalas negativas. A segunda atribui a observação a um dos seis "
 "perfis descritos por Parsons-Smith e colaboradores, pelo centroide canônico "
 "mais próximo, sobre subescalas padronizadas na própria amostra. A "
 "padronização interna foi necessária porque não existem normas de escore T "
 "para esta população, e os escores resultantes não devem ser lidos como "
 "escores normativos.",
], "tabela": "perfis", "pos_tabela": [
 "A proporção de atletas em perfil iceberg cai de 71,4% no dia 1 para 32,6% no "
 "dia 7, ao passo que a proporção de atletas com humor perturbado sobe de "
 "47,6% para 71,7%. Pela classificação de Parsons-Smith, o perfil iceberg "
 "recua de 21,4% para 6,5% entre o primeiro e o último dia, e o perfil "
 "barbatana de tubarão, associado a fadiga elevada com vigor deprimido, sobe "
 "de 9,5% para 10,9%. O perfil superfície, que é o mais frequente em toda a "
 "semana, sobe de 47,6% para 60,9%.",

 "A PERMANOVA sobre o perfil de humor ao longo dos dias resulta em pseudo-F = "
 "2,52 com p = 0,0002, o que confirma o deslocamento do perfil como fenômeno "
 "multivariado, e não apenas como mudança isolada de uma ou outra subescala.",

 "As duas classificações produzem percentuais diferentes porque operacionalizam "
 "critérios diferentes. O critério de Morgan exige apenas que o vigor supere "
 "as negativas, condição relativamente frequente. A classificação de "
 "Parsons-Smith exige proximidade a um centroide canônico específico, condição "
 "mais restritiva. Convém que relatórios e apresentações declarem qual dos dois "
 "critérios utilizam, para que os percentuais sejam comparáveis entre si.",
], "figura": "figura5_perfis.png",
   "legenda_figura": ("Figura 5 - Prontidão ao longo da semana pelo critério "
                      "de Morgan (A) e distribuição dos perfis de "
                      "Parsons-Smith no primeiro e no último dia (B).")},

# ═══════════════════════════════════════════════════ 7 · carga interna ═══
{"titulo": "7 CARGA INTERNA NAS SESSÕES DE HIIT", "paragrafos": [
 "As três sessões de HIIT do microciclo permitem examinar a resposta interna a "
 "um estímulo externo praticamente idêntico. A Tabela 5 apresenta os "
 "indicadores registrados em cada uma delas.",
], "tabela": "hiit", "pos_tabela": [
 "O estímulo externo foi entregue de forma consistente: a frequência cardíaca "
 "de pico apresenta coeficiente de variação intraindividual de apenas 1,7% "
 "entre as três sessões. A resposta do atleta, contudo, deriva ao longo da "
 "semana. A frequência cardíaca de pico cai de 184 para 181 batimentos por "
 "minuto entre a primeira e a terceira sessão (teste de Friedman, p = 0,001), "
 "ao passo que a percepção subjetiva de esforço sobe de 8,5 para 9,1 pontos "
 "(p = 0,004). A recuperação da frequência cardíaca no primeiro minuto sobe de "
 "25,2 para 27,8 batimentos (p = 0,001) e a deriva cardíaca sobe de 6,7 para "
 "8,5 (p = 0,042).",

 "O mesmo estímulo, portanto, passa a custar mais e a mobilizar menos. Essa "
 "dissociação entre carga externa estável e resposta interna que se desloca é "
 "assinatura clássica de fadiga acumulada. Cabe uma ressalva metodológica: a "
 "queda da frequência cardíaca de pico não indica menor trabalho realizado. "
 "Índices de carga interna baseados em frequência cardíaca, como o TRIMP, "
 "herdam essa supressão e subestimam a carga ao longo do microciclo, "
 "limitação bem documentada na literatura.",

 "As variáveis psicológicas acompanham a mesma progressão entre as três "
 "sessões. A perturbação total sobe de 4,8 para 8,0 pontos, com inclinação de "
 "1,76 ponto por sessão; a fadiga sobe de 5,2 para 7,5; o vigor cai de 5,7 "
 "para 4,7. A recuperação total percebida cai de 11,5 para 9,6 e a sonolência "
 "sobe de 9,2 para 11,2. O estresse percebido, medido pela escala de estresse "
 "percebido de 14 itens, não apresenta variação significativa, o que sugere "
 "que a carga do microciclo afeta o eixo energia-fadiga sem repercussão "
 "detectável sobre o estresse psicossocial geral.",
], "figura": "figura6_hiit.png",
   "legenda_figura": ("Figura 6 - Carga externa entregue (A) e esforço "
                      "percebido (B) nas três sessões de HIIT do microciclo.")},

# ══════════════════════════════════════════════════ 8 · recomendações ═══
{"titulo": "8 RECOMENDAÇÕES PARA A COMISSÃO TÉCNICA E PARA OS ATLETAS",
 "paragrafos": [
 "O achado com consequência prática mais direta é o estado em que a equipe "
 "encerra o microciclo. No dia 7 a perturbação total atinge 8,28 pontos, o "
 "vigor cai ao mínimo da semana e a fadiga ao máximo. A proporção de atletas "
 "em perfil iceberg, padrão associado à prontidão competitiva, cai para 32,6%, "
 "ao passo que a proporção de atletas com humor perturbado sobe para 71,7%.",

 "A implicação é operacional. Uma competição disputada no dia seguinte ao "
 "encerramento deste microciclo encontraria a equipe no pior estado "
 "psicológico de toda a semana, e não no melhor. O padrão observado, com "
 "acúmulo de fadiga, queda acentuada do vigor e elevação da perturbação total, "
 "é o oposto do que se busca na véspera de um jogo. Recomenda-se, portanto, "
 "que o último dia antes da competição não replique a carga aqui descrita.",

 "Quatro recomendações decorrem dos dados, e cada uma remete à evidência que a "
 "sustenta.",

 "A primeira é reposicionar o estímulo de alta intensidade. As sessões de HIIT "
 "produziram a maior resposta aguda do microciclo, e a última delas ocorreu no "
 "encerramento. A alocação dessa sessão no meio do microciclo, com reserva dos "
 "dois últimos dias para redução progressiva de carga, permitiria que a "
 "perturbação retornasse aos valores observados nos dias 3 e 5, próximos aos "
 "do repouso, antes da competição.",

 "A segunda é monitorar por tendência, e não por coleta isolada. O erro típico "
 "da medida excede a menor mudança relevante em uma única aplicação, de modo "
 "que a leitura de um único dia não distingue sinal de ruído. A média de cinco "
 "a sete dias, ao contrário, é fiável. A decisão sobre um atleta deve "
 "apoiar-se na trajetória da semana, e não no escore de uma manhã.",

 "A terceira é acompanhar prioritariamente o eixo energia-fadiga. Vigor, "
 "fadiga, fadiga física e perturbação total foram as únicas variáveis a "
 "sobreviver à correção para comparações múltiplas, e são também as menos "
 "afetadas pelo efeito piso. Nas demais subescalas, a ausência de variação não "
 "deve ser lida como ausência de resposta, e sim como limite do instrumento "
 "nesta população.",

 "A quarta é usar a divergência entre carga externa e resposta interna como "
 "sinal de alerta. A queda da frequência cardíaca de pico acompanhada de "
 "aumento da percepção de esforço, entre sessões de carga externa "
 "equivalente, indica que o atleta já não sustenta a mesma resposta "
 "fisiológica ao mesmo estímulo. Quando esse padrão coincide com queda da "
 "recuperação percebida e aumento da sonolência, como ocorreu entre a primeira "
 "e a terceira sessão de HIIT, há indicação de redução de carga antes que o "
 "quadro se consolide.",

 "Cabe registrar o alcance dessas recomendações. Elas derivam de um "
 "microciclo, de uma equipe e de 27 atletas, em delineamento observacional sem "
 "grupo de controle. Descrevem o que ocorreu nesta semana e orientam a "
 "formulação de hipóteses, mas não constituem prescrição validada. A "
 "verificação exige o acompanhamento de microciclos com estruturas diferentes "
 "de distribuição de carga, com observação de se a trajetória do humor responde "
 "na direção prevista.",
]},
]

# ═════════════════════════════════════════════════════════════ tabelas ═══
TABELAS = {
"carga": {
 "numero": 1,
 "titulo": ("Caracterização da carga de treino por dia do microciclo e "
            "resposta média do humor"),
 "cabecalho": ["Dia", "Data", "Conteúdo", "Sessões", "Duração", "Vol. rel.",
               "FC pico", "%FC máx", "PSE", "PTH", "Vigor", "Fadiga"],
 "linhas": [
  ["1", "21/04", "Repouso", "0", "n.a.", "n.a.", "n.a.", "n.a.", "n.a.",
   "2,52", "7,61", "3,96"],
  ["2", "22/04", "HIIT e técnico-tático", "2", "2,0 a 2,5 h", "47%", "184",
   "99%", "8,5", "4,61", "5,66", "5,17"],
  ["3", "23/04", "Técnico-tático, força e amistoso", "3", "4,5 a 5,0 h",
   "100%", "n.d.", "n.d.", "n.d.", "2,87", "5,71", "5,00"],
  ["4", "24/04", "HIIT e técnico-tático", "2", "2,0 a 2,5 h", "47%", "183",
   "98%", "8,5", "4,76", "5,28", "5,76"],
  ["5", "25/04", "Técnico-tático, força e amistoso", "3", "4,5 a 5,0 h",
   "100%", "n.d.", "n.d.", "n.d.", "2,19", "5,56", "5,27"],
  ["6", "26/04", "Técnico-tático (2) e força", "3", "4,5 a 5,0 h", "100%",
   "n.d.", "n.d.", "n.d.", "4,80", "5,74", "5,75"],
  ["7", "27/04", "HIIT e técnico-tático", "2", "2,0 a 2,5 h", "47%", "181",
   "97%", "9,1", "8,28", "4,49", "7,46"],
 ],
 "nota": ("Nota: volume relativo calculado como a duração média do dia "
          "dividida pela do dia de maior volume, com pontos médios de 2,25 h e "
          "4,75 h. FC pico, %FC máx e PSE foram registrados apenas nas sessões "
          "de HIIT, razão pela qual constam como n.d. nos demais dias; n.a. "
          "indica não aplicável ao dia de repouso. PTH, vigor e fadiga são as "
          "médias diárias estimadas por modelo misto."),
},
"diario": {
 "numero": 2,
 "titulo": "Média diária de cada variável do BRUMS ao longo do microciclo",
 "cabecalho": ["Variável", "Dia 1", "Dia 2", "Dia 3", "Dia 4", "Dia 5",
               "Dia 6", "Dia 7", "Δ por dia"],
 "linhas": [
  ["PTH (TMD)", "2,52", "4,61", "2,87", "4,76", "2,19", "4,80", "8,28", "+0,43*"],
  ["Vigor", "7,61", "5,66", "5,71", "5,28", "5,56", "5,74", "4,49", "−0,26*"],
  ["Fadiga", "3,96", "5,17", "5,00", "5,76", "5,27", "5,75", "7,46", "+0,33*"],
  ["Fadiga física", "4,20", "5,59", "5,94", "6,53", "5,93", "6,28", "7,56", "+0,34*"],
  ["Fadiga mental", "4,63", "4,44", "4,49", "4,38", "4,39", "4,62", "5,05", "+0,12*"],
  ["Tensão", "2,17", "1,64", "1,13", "1,37", "1,01", "1,49", "0,94", "n.s."],
  ["Depressão", "1,04", "1,23", "0,70", "1,13", "0,69", "1,06", "1,27", "n.s."],
  ["Raiva", "1,98", "1,72", "1,44", "1,37", "0,60", "1,66", "2,59", "n.s."],
  ["Confusão", "0,98", "0,52", "0,30", "0,41", "0,19", "0,59", "0,51", "n.s."],
 ],
 "nota": ("Nota: médias marginais estimadas por modelo linear misto com "
          "intercepto aleatório por atleta. Os dias 2, 4 e 7 são de HIIT. A "
          "coluna Δ por dia traz a inclinação da tendência semanal; o "
          "asterisco indica p < 0,05 e n.s. indica ausência de significância."),
},
"agudo": {
 "numero": 3,
 "titulo": ("Resposta aguda entre a coleta pré-sessão e a pós-sessão, "
            "agregada por atleta"),
 "cabecalho": ["Variável", "Δ", "dz", "IC 95% do dz", "d de Cohen",
               "p do modelo", "p corrigido", "Efeito piso"],
 "linhas": [
  ["Fadiga física", "+1,65", "0,76", "[0,53; 1,02]", "0,70", "< 0,001", "< 0,001", "0,7%"],
  ["Fadiga", "+1,50", "0,45", "[0,23; 0,66]", "0,38", "< 0,001", "0,003", "7,7%"],
  ["PTH (TMD)", "+3,47", "0,44", "[0,20; 0,70]", "0,33", "0,001", "0,004", "21,9%"],
  ["Vigor", "−1,09", "−0,39", "[−0,61; −0,16]", "−0,33", "0,002", "0,005", "8,6%"],
  ["Fadiga mental", "+0,57", "0,27", "[0,08; 0,44]", "0,20", "0,012", "0,021", "n.d."],
  ["Depressão", "+0,36", "0,19", "[−0,03; 0,36]", "0,14", "0,103", "0,133 n.s.", "67,1%"],
  ["Tensão", "+0,20", "0,15", "[−0,01; 0,30]", "0,12", "0,087", "0,131 n.s.", "49,6%"],
  ["Raiva", "+0,37", "0,14", "[−0,10; 0,34]", "0,11", "0,276", "0,310 n.s.", "59,6%"],
  ["Confusão", "−0,04", "−0,04", "[−0,21; 0,10]", "−0,03", "0,680", "0,680 n.s.", "80,5%"],
 ],
 "nota": ("Nota: diferenças agregadas por atleta antes do teste, o que corrige "
          "a pseudorreplicação. Intervalos de confiança por bootstrap de "
          "clusters com 2.000 reamostragens de atletas inteiros. O p corrigido "
          "controla a taxa de descobertas falsas pelo procedimento de "
          "Benjamini-Hochberg. O dz padroniza pelo desvio intraindividual e o "
          "d de Cohen pelo desvio total. Efeito piso indica o percentual de "
          "respostas no valor mínimo da escala."),
},
"tipo_dia": {
 "numero": 4,
 "titulo": "Resposta aguda por tipo de dia, com intervalo de confiança de 95%",
 "cabecalho": ["Variável", "dz sem HIIT", "IC 95%", "dz com HIIT", "IC 95%",
               "Diferença em diferenças", "p"],
 "linhas": [
  ["Fadiga física", "0,71", "[0,31; 1,11]", "1,04", "[0,66; 1,43]", "0,29", "0,255"],
  ["Fadiga", "0,38", "[−0,02; 0,78]", "0,64", "[0,26; 1,03]", "0,22", "0,268"],
  ["PTH (TMD)", "0,41", "[0,01; 0,81]", "0,52", "[0,14; 0,91]", "0,07", "0,833"],
  ["Vigor", "−0,44", "[−0,84; −0,04]", "−0,39", "[−0,77; 0,00]", "−0,07", "0,845"],
 ],
 "nota": ("Nota: n = 26 atletas com pares em ambas as condições. A diferença "
          "em diferenças isola o efeito agudo atribuível ao tipo de sessão e "
          "não alcança significância em nenhuma variável. Os E-values "
          "correspondentes situam-se entre 1,72 e 1,95. Os dias de HIIT são "
          "também os de menor volume, de modo que intensidade e volume "
          "permanecem confundidos neste delineamento."),
},
"perfis": {
 "numero": 5,
 "titulo": "Distribuição dos perfis de humor no primeiro e no último dia",
 "cabecalho": ["Critério", "Perfil", "Dia 1", "Dia 7", "Variação"],
 "linhas": [
  ["Morgan", "Perfil iceberg", "71,4%", "32,6%", "−38,8 p.p."],
  ["Morgan", "Humor perturbado (PTH > 0)", "47,6%", "71,7%", "+24,1 p.p."],
  ["Parsons-Smith", "Superfície", "47,6%", "60,9%", "+13,3 p.p."],
  ["Parsons-Smith", "Iceberg", "21,4%", "6,5%", "−14,9 p.p."],
  ["Parsons-Smith", "Submerso", "7,1%", "10,9%", "+3,8 p.p."],
  ["Parsons-Smith", "Iceberg invertido", "9,5%", "6,5%", "−3,0 p.p."],
  ["Parsons-Smith", "Barbatana de tubarão", "9,5%", "10,9%", "+1,4 p.p."],
  ["Parsons-Smith", "Everest invertido", "4,8%", "4,3%", "−0,5 p.p."],
 ],
 "nota": ("Nota: o critério de Morgan classifica como iceberg a observação em "
          "que o vigor supera todas as cinco subescalas negativas. A "
          "classificação de Parsons-Smith atribui a observação ao centroide "
          "canônico mais próximo, sobre subescalas padronizadas na amostra, na "
          "ausência de normas de escore T para esta população. Os percentuais "
          "diferem entre os dois critérios porque as definições diferem. "
          "p.p. indica pontos percentuais."),
},
"hiit": {
 "numero": 6,
 "titulo": "Carga interna e resposta psicológica nas três sessões de HIIT",
 "cabecalho": ["Indicador", "Sessão 1 (dia 2)", "Sessão 2 (dia 4)",
               "Sessão 3 (dia 7)", "Tendência", "p"],
 "linhas": [
  ["FC de pico (bpm)", "184", "183", "181", "queda", "0,001"],
  ["PSE final (0 a 10)", "8,5", "8,5", "9,1", "aumento", "0,004"],
  ["Recuperação da FC em 1 min (bpm)", "25,2", "27,4", "27,8", "aumento", "0,001"],
  ["Deriva cardíaca (%)", "6,7", "8,8", "8,5", "aumento", "0,042"],
  ["PTH (TMD)", "4,8", "5,7", "8,0", "+1,76 por sessão", "< 0,05"],
  ["Fadiga", "5,2", "6,3", "7,5", "+1,08 por sessão", "< 0,05"],
  ["Vigor", "5,7", "5,3", "4,7", "−0,68 por sessão", "< 0,05"],
  ["Recuperação total percebida", "11,5", "11,0", "9,6", "−0,83 por sessão", "< 0,05"],
  ["Sonolência", "9,2", "9,9", "11,2", "+1,05 por sessão", "< 0,05"],
  ["Estresse percebido (PSS-14)", "23,0", "22,9", "21,8", "sem tendência", "n.s."],
 ],
 "nota": ("Nota: valores de frequência cardíaca e esforço percebido testados "
          "pelo teste de Friedman. O coeficiente de variação intraindividual "
          "da FC de pico entre as três sessões é de 1,7%, o que indica "
          "entrega consistente do estímulo externo."),
},
}

FONTE_TABELA = "Fonte: dados da pesquisa (2026)."
FONTE_FIGURA = "Fonte: elaborada pelos autores (2026)."
