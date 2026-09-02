# -*- coding: utf-8 -*-
"""Artigo 2: inferencial completo, paramétrico e não paramétrico."""
TITULO=("Quanto a via e a unidade de análise decidem a conclusão: três rotas estatísticas sobre a mesma "
        "série de humor em um microciclo de handebol de elite")
SUB=("Estudo observacional longitudinal com bateria inferencial completa, modelo linear misto, "
     "sensibilidade à unidade de análise e teste do mecanismo de ausência")

RESUMO=(
"O monitoramento psicológico do atleta produz séries curtas, repetidas e desbalanceadas, e a escolha da via "
"de análise raramente é discutida. Este estudo submeteu a mesma série de humor a três vias (não paramétrica, paramétrica clássica e modelo linear "
"misto) e mediu quanto do resultado é atribuível à via, e não aos dados. "
"Vinte e sete atletas de handebol masculino de primeira divisão responderam à Escala de Humor de Brunel "
"durante a última semana de pré-temporada; os 456 registros foram agregados em 166 pares atleta-dia e 119 "
"pares de manhã e noite. A via não paramétrica reuniu Friedman com W de Kendall, teste L de Page, Wilcoxon "
"com correção de Holm, Q de Cochran, McNemar, Spearman e qui-quadrado de contingência. A via paramétrica "
"reuniu análise de variância de medidas repetidas com correção de Greenhouse-Geisser, teste t pareado com "
"intervalo de confiança, Pearson e teste de Levene. O modelo misto estimou o efeito linear do dia com "
"intercepto aleatório por atleta. As séries foram tratadas por filtro binomial, derivadas de primeira e "
"segunda ordem e piso de ruído. Nenhuma das sete variáveis passou no teste de Shapiro-Wilk, e o ε de "
"Greenhouse-Geisser situou-se entre 0,327 e 0,693, o que indica violação severa de esfericidade em todas "
"elas. As três vias concordaram em cinco das sete variáveis e divergiram em duas. A depressão nada mostrou pelas vias "
"que exigem registro completo (Friedman p = 0,815; análise de variância corrigida p = 0,457) e alcançou "
"significância pelo modelo misto (p = 0,049), que retém os 166 pares em lugar de dezenove atletas. A confusão "
"inverteu o padrão: significativa pelo Friedman (p = 0,001) e não significativa pelo modelo misto (p = 0,079). A "
"sensibilidade à unidade de análise trocou o veredito de uma variável, a tensão, e apenas contra a leitura não "
"pareada. A regra que compõe a linha de base trocou o de quatro, o que a torna a decisão mais consequente das "
"três. Um modelo adicional separou a carga do próprio dia da carga da véspera e mostrou que apenas a segunda tem "
"efeito detectável sobre fadiga e vigor. Todos os valores foram recalculados por um segundo caminho de código, e "
"as sessenta e cinco conferências coincidem. Conclui-se que, em séries de monitoramento com ausências frequentes, "
"reportar uma única via é insuficiente, e que a regra de composição da linha de base merece escrutínio maior do "
"que o número de observações que a formam sugere."
)
PALAVRAS=("estatística não paramétrica; modelo linear misto; medidas repetidas; humor; handebol; "
          "tamanho de efeito")
ABSTRACT=(
"Athlete psychological monitoring produces short, repeated and unbalanced series, and the choice of analytical "
"route is rarely discussed. This study submitted the same mood series to three routes (non-parametric, classical parametric and linear mixed "
"model) and measured how much of the result is attributable to the "
"route rather than to the data. Twenty-seven male first-division handball players completed the Brunel Mood "
"Scale during the final pre-season week; the 456 records were aggregated into 166 athlete-day pairs and 119 "
"morning-evening pairs. The non-parametric route combined Friedman with Kendall's W, Page's L test, Wilcoxon "
"with Holm correction, Cochran's Q, McNemar, Spearman and contingency chi-square. The parametric route "
"combined repeated-measures analysis of variance with Greenhouse-Geisser correction, paired t tests with "
"confidence intervals, Pearson and Levene's test. The mixed model estimated the linear effect of day with a "
"random intercept per athlete. Series were treated with a binomial filter, first and second derivatives and a "
"noise floor. None of the seven variables passed the Shapiro-Wilk test, and Greenhouse-Geisser ε ranged from "
"0.327 to 0.693, indicating severe sphericity violation throughout. The three routes agreed on five of the seven variables and diverged on two. Depression showed nothing by the "
"routes that require complete records (Friedman p = 0.815; corrected analysis of variance p = 0.457) and reached "
"significance by the mixed model (p = 0.049), which retains all 166 pairs instead of nineteen athletes. Confusion "
"reversed the pattern: significant by Friedman (p = 0.001) and non-significant by the mixed model (p = 0.079). "
"Sensitivity to the unit of analysis switched the verdict of one variable, tension, and only against the unpaired "
"reading. The rule composing the baseline switched four, making it the most consequential of the three decisions. "
"In monitoring series with frequent absences, reporting a single route is insufficient, and the rule composing "
"the baseline deserves scrutiny out of proportion to the number of observations that form it."
)
KEYWORDS=("nonparametric statistics; linear mixed model; repeated measures; mood; handball; effect size")

INTRO=[
"A psicologia do esporte herdou da psicometria um instrumental de comparação entre grupos e da fisiologia do "
"exercício um instrumental de comparação entre momentos. O monitoramento diário do atleta situa-se no "
"cruzamento dos dois, e é justamente aí que os pressupostos rangem. Séries de humor coletadas ao longo de um "
"microciclo são curtas, repetidas, desbalanceadas por ausências e medidas em escalas de amplitude estreita com "
"forte concentração no valor mínimo. Nenhuma dessas propriedades favorece os testes que, ainda assim, são "
"rotineiramente aplicados.",

"A tradição de medida do humor no esporte remonta ao modelo de saúde mental de Morgan (1985) e ao perfil "
"iceberg (MORGAN, 1980), e consolidou-se com a Escala de Humor de Brunel (TERRY et al., 1999), suas normas "
"para amostras atléticas (TERRY; LANE, 2000) e sua adaptação brasileira (ROHLFS et al., 2008; ROHLFS et al., "
"2023). Duas metanálises estabeleceram que a relação entre humor e desempenho existe e é de magnitude modesta "
"(BEEDIE; TERRY; LANE, 2000; LOCHBAUM et al., 2021). Os documentos de consenso sobre supertreinamento e "
"recuperação atribuíram ao humor o papel de sentinela precoce (MEEUSEN et al., 2013; KELLMANN et al., 2018), "
"e revisões sistemáticas mostraram que medidas subjetivas superam medidas objetivas na detecção de respostas "
"ao treino (SAW; MAIN; GASTIN, 2016).",

"O que essa literatura raramente discute é o caminho estatístico. Estudos longitudinais de monitoramento "
"tendem a escolher uma via e reportá-la, sem examinar se outra via, igualmente defensável, levaria à "
"conclusão oposta. A escolha, entretanto, não é neutra. A via não paramétrica dispensa a hipótese de "
"normalidade e resiste ao efeito de piso, porém, na sua forma clássica para medidas repetidas, exige registro "
"completo em todas as condições e descarta quem faltou. A via paramétrica clássica estima magnitude e "
"intervalo de confiança, o que a via de postos não oferece, mas pressupõe normalidade e esfericidade e "
"descarta igualmente os casos incompletos. O modelo linear misto retém todas as observações disponíveis e "
"separa a variância entre atletas da variância dentro do atleta, ao preço de pressupostos sobre a forma dos "
"resíduos e sobre a linearidade do efeito.",

"Em amostras grandes e equilibradas, as três vias tendem a convergir, e a discussão é acadêmica. Em um elenco "
"de handebol acompanhado por sete dias, com ausências que reduzem a subamostra completa a menos de um terço "
"do grupo, a convergência deixa de ser garantida. O handebol acrescenta um agravante: a modalidade combina "
"deslocamentos de alta intensidade, mudanças de direção, saltos e contato permanente, com demandas que variam "
"por posição (KARCHER; BUCHHEIT, 2014; GARCÍA-SÁNCHEZ et al., 2023) e carga distribuída de modo desigual "
"entre atletas do mesmo elenco (BÜCHEL; DÖRING; BAUMEISTER, 2026), de forma que a ausência a uma sessão "
"raramente é aleatória.",

"A escolha da via, contudo, não é a única decisão silenciosa. Antes dela vem a de contar: em séries de "
 "monitoramento com ausências e com mais de uma resposta por dia, decidir o que conta como uma observação "
 "já fixa parte do resultado. Instrumentos de autorrelato aplicados diariamente convivem com adesão "
 "incompleta por construção (SAW; MAIN; GASTIN, 2015; McGUIGAN; HASSMÉN; ROSIĆ, 2022), e cada regra de "
 "agregação produz um denominador diferente e uma potência diferente. A literatura de monitoramento "
 "reconhece o problema no plano da medida, ao exigir que a magnitude observada seja lida contra o erro "
 "típico do instrumento (HOPKINS, 2000; LINDBERG et al., 2022), mas raramente o examina no plano da "
 "inferência.",
 "Convém sublinhar que a questão já tem precedente documentado dentro da própria área. Newans, Bellinger e "
 "Drovandi (2022) confrontaram as duas vias sobre 472 observações de partidas de rúgbi e demonstraram que a "
 "exigência de casos completos, imposta pela análise de variância de medidas repetidas, descartaria 48,7% das "
 "observações disponíveis, ao passo que o modelo misto as reteve e recuperou efeitos que a via clássica teria "
 "ocultado. O alerta "
 "extrapola o esporte: a literatura metodológica designa por graus de liberdade do pesquisador o conjunto de "
 "escolhas analíticas defensáveis que, exercidas sem declaração, elevam a taxa de falsos positivos (MANDL et al., "
 "2024). Falta, contudo, quantificar o fenômeno onde ele mais pesa, isto é, em séries curtas de monitoramento "
 "psicológico com ausências frequentes, nas quais cada via disponível opera sobre um denominador próprio. Aí "
 "reside a pergunta que organiza esta investigação: quanto da conclusão pertence aos dados e quanto pertence ao "
 "caminho escolhido para lê-los.",  "Justifica-se, assim, submeter uma mesma série a todas as vias disponíveis e "
 "medir quanto do resultado pertence à via. Essa comparação não é um exercício de estatística aplicada desligado da prática: se a "
"comissão técnica decide reduzir carga a partir de um valor de p, importa saber que esse valor depende de uma "
"escolha metodológica que ninguém declarou. O objetivo geral deste estudo consiste, portanto, em descrever o "
"comportamento das variáveis do BRUMS ao longo da última semana de pré-temporada de atletas de handebol de "
"elite por meio de uma bateria inferencial completa, paramétrica e não paramétrica, acrescida de modelo "
"linear misto, e em quantificar em que medida a conclusão sobre cada variável depende da via escolhida. Como "
"em seu artigo companheiro, a descrição das séries apoia-se em suavização, derivadas e piso de ruído, "
"instrumental que fornece um critério de relevância independente do valor de p.",
]

METODO=[
("Delineamento, participantes e coleta",[
 "O delineamento, a amostra e o procedimento de coleta são os mesmos descritos no artigo companheiro desta "
 "série e aqui se resumem. Vinte e sete atletas de handebol masculino de uma equipe da primeira divisão "
 "nacional, com 21,96 ± 3,81 anos, responderam à Escala de Humor de Brunel ao longo dos sete dias que "
 "antecederam a estreia na competição oficial. O primeiro dia teve janela única noturna e serviu de linha de "
 "base; do segundo ao sétimo houve medida matinal e uma segunda medida ao fim do dia. A semana reuniu treino "
 "intervalado de alta intensidade no segundo, quarto e sétimo dias, jogo amistoso no terceiro e no quinto, e "
 "conteúdo técnico, tático e de força no sexto, com carga acumulada de 1,5 a 23,0 horas.",
 "A unidade de análise é o par atleta-dia: um valor por atleta e por dia, obtido pela média das respostas "
 "daquele atleta naquele dia. O conjunto reúne 456 registros, 166 pares atleta-dia e 119 pares de manhã e "
 "noite. Dezenove dos vinte e sete atletas possuem registro nos sete dias, e essa subamostra completa é a "
 "única sobre a qual as vias clássicas de medidas repetidas podem operar."]),
("Procedência dos dados e auditoria de qualidade",[
 "A base primária é o export do formulário eletrônico. Duas passagens de auditoria a antecederam. A primeira "
 "tratou da procedência: fixou a fonte, definiu o dia pelo carimbo de data e hora com fronteira às quatro da "
 "manhã em lugar da data autorreferida, recuperou quatro registros sem identificação e, sobretudo, declarou a "
 "unidade de análise, que é o par atleta-dia. Essa passagem está descrita em detalhe no artigo descritivo "
 "companheiro, e a ela se deve o fato de os números aqui apresentados não coincidirem com os de versões "
 "anteriores do mesmo estudo.",
 "A segunda passagem tratou da qualidade do dado. Cada escore foi reconstruído por fórmula a partir dos itens "
 "que o compõem e confrontado com a coluna já computada na base de origem: as 4.113 conferências não "
 "apresentaram divergência. A completude do instrumento é integral, sem célula ausente em 20.108 respostas de "
 "item, e nenhum dos 456 registros apresenta valor fora do domínio admissível da sua escala. A cobertura da "
 "grade que cruza atleta e dia, porém, recua a setenta e oito por cento do elenco no quarto e no sétimo dias, "
 "o que explica por que cada teste deste artigo declara o seu número de casos completos e por que os "
 "denominadores diferem entre as três vias.",
 "A triagem de valores discrepantes seguiu ordem definida: verificação de domínio primeiro, e só depois "
 "critérios de dispersão. A precaução não é retórica. Em confusão, e em menor grau em depressão e raiva, o "
 "primeiro e o terceiro quartis coincidem no piso da escala; o intervalo interquartil é nulo, a cerca de "
 "Tukey passa a classificar como discrepante toda resposta diferente de zero, e o escore z modificado torna-se "
 "indefinido porque o desvio absoluto mediano também é nulo. Em variável com efeito de piso, a triagem "
 "apoia-se no domínio e na comparação de cada atleta com a própria série. Nenhum registro foi excluído, "
 "nenhum valor foi imputado e nenhum escore foi alterado.",
 "Por fim, todos os números deste artigo foram recalculados por um segundo caminho de código, independente do "
 "que produziu a base canônica: enquanto este parte das colunas já pontuadas, aquele parte do item do "
 "formulário. As sessenta e cinco conferências coincidem dentro da tolerância adotada."]),
("Via não paramétrica",[
 "A comparação global entre os sete dias empregou o teste de Friedman (FRIEDMAN, 1937), com tamanho de efeito "
 "expresso pelo W de Kendall (KENDALL; SMITH, 1939). A hipótese de tendência ordenada recebeu tratamento "
 "específico pelo teste L de Page (PAGE, 1963), mais potente que o de Friedman quando a alternativa é "
 "monotônica. Os contrastes entre a linha de base e cada dia subsequente recorreram ao teste de postos "
 "sinalizados de Wilcoxon (WILCOXON, 1945), com correção de Holm para as seis comparações (HOLM, 1979) e "
 "tamanho de efeito r obtido pela razão entre o escore z e a raiz do número de pares.",
 "As variáveis categóricas seguiram procedimentos próprios. A estabilidade da prevalência de cada perfil ao "
 "longo dos sete dias foi avaliada pelo Q de Cochran (COCHRAN, 1950); a migração entre a manhã e a noite, pelo "
 "teste de McNemar com correção de continuidade (McNEMAR, 1947); e a associação entre tipo de estímulo e "
 "perfil, pelo qui-quadrado de contingência. As associações entre variáveis contínuas empregaram o "
 "coeficiente de Spearman, com correção de Holm para os vinte e um pares."]),
("Via paramétrica clássica",[
 "A comparação global entre os sete dias empregou análise de variância de medidas repetidas de um fator, sobre "
 "a mesma subamostra completa. A esfericidade foi avaliada pelo ε de Greenhouse-Geisser, calculado a partir "
 "dos autovalores da matriz de covariância duplamente centrada, e os graus de liberdade foram corrigidos por "
 "esse fator em todos os casos, dada a violação generalizada. O tamanho de efeito foi expresso pelo eta "
 "quadrado parcial.",
 "O contraste entre a linha de base e a véspera da estreia empregou o teste t para amostras pareadas, com "
 "intervalo de confiança de noventa e cinco por cento para a diferença média e tamanho de efeito d de Cohen "
 "para medidas repetidas, obtido pela razão entre a diferença média e o desvio-padrão das diferenças. A "
 "homogeneidade de variâncias entre os dias foi verificada pelo teste de Levene, e as associações entre "
 "variáveis contínuas pelo coeficiente de Pearson, também com correção de Holm."]),
("Modelo linear misto",[
 "O terceiro caminho ajusta um modelo linear de efeitos mistos sobre os 166 pares atleta-dia, com o dia como "
 "efeito fixo contínuo e intercepto aleatório por atleta. A estimação empregou máxima verossimilhança "
 "restrita. Do modelo extraem-se três quantidades de interesse: o coeficiente do dia, que expressa a mudança "
 "média por dia na escala original com o respectivo intervalo de confiança; o valor de p desse coeficiente; e "
 "a proporção da variância total atribuível a diferenças estáveis entre atletas, obtida pela razão entre a "
 "variância do intercepto aleatório e a soma dessa variância com a residual.",
 "A vantagem decisiva do modelo, neste contexto, é não exigir registro completo: um atleta com quatro dias "
 "contribui com quatro observações em vez de ser descartado. A contrapartida é o pressuposto de efeito linear "
 "do dia, que o tratamento de séries descrito adiante permite avaliar de modo independente."]),
("Modelo de carga do dia e da véspera",[
 "Ao modelo do efeito do dia acrescentou-se um segundo, destinado a separar a carga do próprio dia da carga "
 "que a antecede. Para cada variável ajustou-se, sobre os 166 pares atleta-dia, a especificação y(a,d) = β₀ + "
 "β₁·h(d) + β₂·h(d − 1) + u(a) + ε(a,d), em que h(d) são as horas de treino do dia d, h(d − 1) as do dia "
 "anterior, u(a) o intercepto aleatório do atleta e ε o resíduo. A estimação empregou máxima verossimilhança. "
 "A separação entre os dois coeficientes responde a uma pergunta que o efeito do dia, sozinho, não distingue: "
 "o humor medido reflete o esforço em curso ou o esforço da véspera?",
 "Uma ressalva delimita o alcance dessa estimativa. Com uma única equipe e sete dias, o efeito das horas não "
 "se separa do efeito do dia do microciclo nem da carga acumulada, que progridem juntos. Os coeficientes são, "
 "portanto, associativos, e a leitura que deles se faz é de convergência com os demais achados, não de "
 "demonstração causal."]),
("Sensibilidade da inferência à unidade de análise",[
 "A auditoria de procedência demonstrou que a prevalência dos perfis varia conforme a unidade de análise "
 "adotada. Resta a pergunta gêmea, que é a deste artigo: o veredito dos testes de hipótese também varia? "
 "Para respondê-la, cada contraste foi refeito sobre três tabelas atleta-dia construídas por regras distintas (o par atleta-dia, o "
 "par formado pelo primeiro e pelo último registro do dia e a subamostra dos atletas com medida no primeiro e no "
 "sétimo dia), além de uma leitura não pareada sobre o registro "
 "isolado, único tratamento que essa unidade admite.",
 "A comparação examinou o contraste entre a linha de base e a véspera da estreia e a comparação global "
 "entre os sete dias. Considerou-se troca de veredito a situação em que a mesma variável cruza o limiar de "
 "cinco por cento em uma unidade e não cruza em outra."]),
("Mecanismo de ausência",[
 "A hipótese de ausência ignorável não é demonstrável com dados observacionais, mas é refutável em uma "
 "direção: se a probabilidade de responder amanhã dependesse do humor de hoje, a hipótese estaria "
 "descartada. Ajustou-se, para cada variável, um modelo logístico de efeitos mistos com intercepto "
 "aleatório por atleta, em que a resposta é o comparecimento no dia seguinte e os preditores são o escore "
 "do dia corrente e o dia do microciclo, com correção de Holm para as sete comparações.",
 "Acrescentaram-se duas verificações. A primeira mede a concentração das faltas entre os atletas e a "
 "associação entre o número de faltas e o humor médio de cada um. A segunda calcula limites de pior caso "
 "para a variação entre o primeiro e o sétimo dia: cada ausente do sétimo dia recebe, alternadamente, o "
 "quinto e o nonagésimo quinto percentil observado naquele dia, e verifica-se se o sinal da variação "
 "sobrevive aos dois cenários extremos."]),
("Tratamento de séries: suavização, derivadas e piso de ruído",[
 "Independentemente das três vias, cada série diária recebeu um tratamento próprio, cuja justificação "
 "completa consta do artigo companheiro e cujos parâmetros se declaram aqui por inteiro, de modo que este "
 "artigo se sustente sozinho. O erro-padrão de cada dia foi calculado, pelo desvio-padrão amostral dividido "
 "pela raiz do número de respondentes do dia no caso das médias e pela fórmula binomial no caso das "
 "prevalências, e a média dos sete erros-padrão define o piso de ruído da série, isto é, a magnitude típica "
 "da oscilação que a amostragem produz por si só.",

 "A suavização empregou o filtro binomial de três pontos, de núcleo [1/4, 1/2, 1/4], que é a terceira linha "
 "normalizada do triângulo de Pascal. Cada ponto interno passa a "
 "ŷ(d) = 0,25·y(d − 1) + 0,50·y(d) + 0,25·y(d + 1) e os extremos conservam o valor observado, sem "
 "preenchimento por reflexão ou extrapolação, porque o deslocamento total da série é medido justamente entre "
 "esses dois pontos. O núcleo tem soma unitária, o que preserva o nível da série; é simétrico, o que anula o "
 "deslocamento de fase e impede que um evento migre no tempo por efeito do filtro; e tem resposta em "
 "frequência H(ω) = cos²(ω/2), que se anula na frequência de Nyquist e portanto remove por construção a "
 "componente que alterna de um dia para o outro, assinatura do ruído amostral em série diária. Descartaram-se "
 "a média móvel simples, cuja resposta não se anula em Nyquist, e o ajuste polinomial local do tipo "
 "Savitzky-Golay, instável nas extremidades de séries de sete pontos.",

 "As derivadas discretas da série suavizada foram calculadas por diferença progressiva, "
 "Δ(d) = ŷ(d + 1) − ŷ(d) para a primeira e Δ²(d) = Δ(d + 1) − Δ(d) para a segunda, e expressas em unidades "
 "do piso pela divisão de cada valor pelo piso da própria variável. Transição de choque é aquela cuja "
 "primeira derivada, em unidades originais, supera o piso em valor absoluto; ponto de inflexão é a abscissa "
 "em que a segunda derivada muda de sinal, obtida por interpolação linear entre os dois dias que a cercam.",

 "Declara-se variação real quando o deslocamento total entre o primeiro e o sétimo dia supera, em valor "
 "absoluto, o piso de ruído, e reporta-se também a razão entre um e outro, que ordena as variáveis por folga. "
 "Esse critério é deliberadamente independente do valor de p: ele responde a quanto a série se moveu em "
 "relação ao seu próprio ruído, e não à probabilidade de observar o movimento sob a hipótese nula. Reportar "
 "os dois lado a lado é parte do argumento deste artigo.",
]),
("Processamento computacional",[
 "Toda a análise foi executada em Python 3.11.15, em ambiente Linux, por cadeia que parte da planilha de "
 "origem e termina nos arquivos de saída sem etapa manual intermediária. As versões das bibliotecas são "
 "declaradas porque resultados de bootstrap e de modelos mistos delas dependem: openpyxl 3.1.5 na "
 "importação, NumPy 2.4.6 na manipulação numérica (HARRIS et al., 2020), SciPy 1.17.1 nos testes de "
 "hipótese (VIRTANEN et al., 2020), statsmodels 0.15.0 nos modelos mistos, matplotlib 3.11.1 nas figuras "
 "(HUNTER, 2007) e python-docx 1.2.0 na exportação.",

 "A importação abre a planilha em modo somente leitura e com leitura de valores em cache, percorre as linhas "
 "da aba do formulário diário e converte as respostas em escala Likert por expressão regular que captura o "
 "dígito inicial do rótulo. A identidade do respondente provém da coluna padronizada, com chave canônica "
 "obtida por normalização Unicode NFKD, remoção de diacríticos, caixa baixa e colapso de espaços. A "
 "codificação dos participantes em A01 a A27 ocorre dentro dessa rotina, antes de qualquer gravação em "
 "disco, e apenas a base anonimizada alimenta as análises. O dia de cada registro deriva do carimbo de data "
 "e hora com fronteira às quatro da manhã.",

 "Na via não paramétrica utilizaram-se as funções shapiro, friedmanchisquare, wilcoxon, chi2_contingency, "
 "spearmanr, mannwhitneyu e kruskal do módulo stats do SciPy, além de rankdata para os postos. O teste L de "
 "Page, o Q de Cochran, o teste de McNemar e a correção de Holm foram implementados a partir das respectivas "
 "definições, por não integrarem a biblioteca, no próprio código depositado. Na via paramétrica "
 "utilizaram-se ttest_rel, pearsonr e levene, com a análise de variância de medidas repetidas e a correção "
 "de Greenhouse-Geisser implementadas diretamente sobre a matriz de somas de quadrados, e as probabilidades "
 "obtidas pelas distribuições f, chi2, t, norm e beta. Os momentos de terceira e quarta ordem vieram de skew "
 "e kurtosis, e o erro-padrão da média de sem.",

 "Os modelos mistos foram ajustados pela interface de fórmulas do statsmodels, com intercepto aleatório por "
 "atleta. O modelo de tendência empregou máxima verossimilhança restrita, apropriada à estimação de "
 "componentes de variância; os modelos de ausência e de carga empregaram máxima verossimilhança plena, "
 "condição necessária para comparar especificações com efeitos fixos distintos. Os intervalos de confiança "
 "sem forma fechada foram obtidos por bootstrap agrupado por atleta, com sorteio de atletas com reposição e "
 "não de linhas, o que respeita a dependência entre observações do mesmo respondente; o gerador "
 "pseudoaleatório recebeu semente fixa em cada rotina, o que torna os intervalos reproduzíveis dígito a "
 "dígito.",

 "A confiabilidade das medidas repetidas foi estimada por correlação intraclasse de via única, com o "
 "coeficiente de medida média pela fórmula de Spearman-Brown (SHROUT; FLEISS, 1979). O efeito de piso seguiu "
 "o critério de Terwee et al. (2007). Adotou-se alfa de cinco por cento, com correção de Holm sempre que uma "
 "família de comparações foi examinada em conjunto.",

 "Os resultados de cada rotina são gravados em arquivos JSON e consolidados em um banco SQLite de camada "
 "tripla, com vinte e seis tabelas de conteúdo, quatro visões e índice de texto completo do tipo FTS5. Os resultados das três vias "
 "residem na mesma tabela, em formato longo, cada linha com a sua variável, o seu recorte, a sua unidade de "
 "análise e a rotina que a produziu, o que permite compará-las por consulta direta em lugar de por "
 "transcrição. As figuras foram geradas com matplotlib a partir desses mesmos arquivos, a 300 pontos por "
 "polegada. A exportação para o formato de texto emprega um módulo comum que fixa página A4, margens de três "
 "centímetros à esquerda, ao topo e à direita e de dois ao pé, Times New Roman de doze pontos, espaçamento "
 "de uma linha e meia, alinhamento justificado e recuo de primeira linha de 1,25 centímetro, com contadores "
 "automáticos de tabelas, figuras e quadros. Todo valor numérico impresso é lido do JSON no momento da "
 "montagem e formatado por função única, com vírgula decimal e sinal menos tipográfico; nenhum número foi "
 "digitado à mão no manuscrito.",

 "O projeto obteve aprovação do comitê de ética sob o parecer CAAE [inserir número do CAAE], e todos os "
 "participantes assinaram termo de consentimento livre e esclarecido.",
]),
]

R1=[
 "Antes de qualquer pressuposto, uma verificação sobre a própria base. Os valores de normalidade aqui "
 "relatados foram recalculados por um caminho de código independente do que gerou a base canônica, o qual parte do item do "
 "formulário e reconstrói cada escore por fórmula. As sete variáveis rejeitam a normalidade "
 "pelos dois caminhos, com valores de W idênticos até a quarta casa decimal. A opção pela via não paramétrica "
 "como rota principal, portanto, não depende de uma particularidade do processamento.",
"A verificação de pressupostos, apresentada na Figura 3 e na Tabela 1, é inequívoca em duas frentes e "
"heterogênea numa terceira. Nenhuma das sete variáveis passa no teste de Shapiro-Wilk ao nível de cinco por "
"cento. O vigor é a que mais se aproxima da normalidade (W = 0,983; p = 0,035) e a depressão a que mais dela se afasta "
"(W = 0,485; p < 0,001), com assimetria de 4,04 e curtose de 19,64. Quatro das seis subescalas apresentam efeito "
"de piso acima do limite de quinze por cento proposto por Terwee et al. (2007): 69,3% na confusão, 61,4% na "
"depressão, 51,8% na raiva e 41,6% na tensão.",
"A esfericidade está violada em todas as variáveis, e severamente. O ε de Greenhouse-Geisser situa-se entre "
"0,327, na tensão, e 0,693, na fadiga, sempre abaixo do limite convencional de 0,75. A correção dos graus de "
"liberdade é, portanto, obrigatória, e não facultativa; a análise de variância sem correção produziria "
"valores de p artificialmente pequenos em todas as sete variáveis. O teste de Levene não rejeita a "
"homogeneidade de variâncias entre os dias em nenhuma variável, o que constitui a única boa notícia entre os "
"pressupostos.",
"Esse quadro autoriza uma expectativa e uma dúvida. A expectativa é que a via não paramétrica, imune à "
"assimetria e ao piso, seja a mais confiável. A dúvida diz respeito ao preço que ela cobra: o teste de "
"Friedman, como a análise de variância de medidas repetidas, exige registro em todos os sete dias e opera "
"sobre dezenove dos vinte e sete atletas, isto é, descarta 88% dos 166 pares atleta-dia disponíveis.",
]
R2=[
"A Figura 2 apresenta o resultado central deste estudo: a mesma hipótese, submetida às três vias, para as sete "
"variáveis. A Tabela 2 traz os valores.",
"As três vias concordam em cinco das sete variáveis. O vigor é significativo pelas três (Friedman p < 0,001; "
"análise de variância corrigida p < 0,001; modelo misto p < 0,001), assim como a fadiga (p = 0,003; p < 0,001; p "
"< 0,001), a perturbação total (p = 0,024; p = 0,020; p < 0,001) e a tensão (p = 0,028; p = 0,012; p = 0,001). A "
"raiva não é significativa por nenhuma (p = 0,487; p = 0,291; p = 0,680).",
"As duas variáveis restantes divergem, e divergem em sentidos opostos. A depressão nada mostra pelas duas vias "
"que exigem registro completo (Friedman χ² = 2,95; p = 0,815; análise de variância corrigida F = 0,73; p = 0,457) "
"e alcança significância pelo modelo misto, ainda que por margem estreita (b = 0,098 ponto por dia; IC 95% 0,001 "
"a 0,195; p = 0,049). A explicação está no custo amostral: as duas primeiras operam sobre dezenove atletas e a "
"terceira retém os 166 pares, o que triplica a informação disponível para estimar um efeito pequeno. Aqui a ordem "
"entre as vias é a esperada, com a via de postos mais conservadora e o modelo misto mais sensível.",
"A confusão inverte esse padrão e por isso merece exame separado. Ela é significativa pelo teste de Friedman (χ² "
"= 22,29; p = 0,001; W = 0,196), permanece significativa pela análise de variância corrigida (F = 3,66; p = "
"0,033; η²p = 0,169) e deixa de sê-lo pelo modelo misto (b = −0,063; IC 95% −0,133 a 0,007; p = 0,079). A explicação "
"reside na forma da trajetória: a confusão cai abruptamente do primeiro para o segundo dia e depois oscila sem "
"direção, de modo que o efeito não é linear no dia. O teste de Friedman, que apenas pergunta se os dias "
"diferem, capta o degrau; o modelo misto, que impõe uma reta, não o capta. A discordância, nesse caso, não "
"indica qual via está certa: indica que a pergunta que cada uma responde é diferente.",
"O teste L de Page, que especifica a alternativa como ordenada, ilumina esse ponto. Ele acusa tendência monotônica em quatro variáveis, a saber, vigor (z = −4,05; p < 0,001), fadiga (z = 3,48; p < "
"0,001), tensão (z = −3,04; p = 0,002) e confusão (z = −2,18; p = 0,029), e nada encontra na depressão, na raiva "
"nem na perturbação total. O contraste com o teste de Friedman é informativo justamente onde os dois discordam: a "
"perturbação total é significativa por Friedman e não apresenta tendência ordenada por Page, o que indica que os "
"dias diferem entre si sem que o deslocamento siga uma direção única. A depressão, por sua vez, escapa às duas, e "
"a significância que o modelo misto lhe atribui repousa inteiramente na imposição de linearidade sobre os 166 "
"pares.",
]
R3=[
"A magnitude, que a via de postos não fornece, aparece na Figura 2 e na Tabela 3. O vigor apresenta o maior "
"efeito do conjunto no contraste entre a linha de base e a véspera da estreia (dz = −0,96; IC 95% da "
"diferença de −4,52 a −1,60 pontos), seguido pela fadiga (dz = 0,84; IC 95% de 1,56 a 5,21). A tensão "
"apresenta efeito médio (dz = −0,57; IC 95% de −2,08 a −0,23) e a confusão, efeito próximo do médio "
"(dz = −0,46; IC 95% de −1,20 a −0,01). A perturbação total, apesar da diferença média de 5,21 pontos, "
"apresenta intervalo que cruza o zero por margem estreita (de −0,05 a 10,47), o que explica o valor de p de "
"0,052 e ilustra o risco de tratar 0,05 como fronteira ontológica.",
"A comparação entre os tamanhos de efeito das duas vias merece registro. O r não paramétrico e o dz paramétrico ordenam as variáveis de modo idêntico (vigor, fadiga, tensão, confusão, "
"perturbação total, raiva, depressão), o que indica que a discordância entre vias diz respeito à detecção, e não à ordenação da "
"importância. Nenhum revisor que exija ambos os índices encontrará contradição substantiva; encontrará, sim, "
"limiares diferentes.",
]
R4=[
"O modelo misto, apresentado na Figura 6 e na Tabela 4, acrescenta duas informações que as outras vias não "
"fornecem. A primeira é a taxa de mudança na escala original: a perturbação total sobe 0,868 ponto por dia (IC 95% 0,445 a "
"1,292), o vigor cai 0,491 (IC 95% −0,642 a −0,341), a fadiga sobe 0,467 (IC 95% 0,299 a 0,636), a tensão cai "
"0,146 (IC 95% −0,229 a −0,064) e a depressão sobe 0,098 (IC 95% 0,001 a 0,195). Traduzido para a semana inteira, "
"o modelo prevê queda de aproximadamente três pontos de vigor e elevação de aproximadamente três de fadiga entre "
"o primeiro e o sétimo dia, valores compatíveis com os deslocamentos observados de 4,52 e 4,33 pontos, e menores "
"por efeito da imposição de linearidade sobre uma trajetória que se move por degraus.",
"A segunda é a decomposição da variância. A proporção atribuível a diferenças estáveis entre atletas varia de "
"0,341, na raiva, a 0,765, na depressão. A leitura substantiva é direta: a raiva comporta-se como estado, "
"sensível ao dia, ao passo que a depressão comporta-se como característica relativamente estável do "
"respondente. Essa distinção tem consequência prática para o monitoramento: variáveis com proporção elevada "
"exigem referência intraindividual, porque a comparação com a média do grupo confunde traço com estado.",
"Convém observar que a ordem dessa decomposição reproduz a da correlação intraclasse calculada de modo independente na descrição (depressão, fadiga, tensão, "
"perturbação total, vigor, confusão e raiva), o que confere consistência interna às duas estimativas.",
]
R5=[
"A estrutura de associação, apresentada na Figura 5 e na Tabela 5, foi estimada pelas duas vias. Quinze dos "
"vinte e um pares de variáveis associam-se de modo significativo após correção de Holm pelo coeficiente de "
"Spearman, e dezessete pelo de Pearson. A concordância entre os dois é alta: a discrepância mediana entre "
"|ρ| e |r| é de 0,05 e a máxima, de 0,20, no par formado pela depressão e pela perturbação total.",
"O padrão substantivo é o mesmo pelas duas vias. A fadiga vincula-se fortemente à perturbação total "
"(ρ = 0,76; r = 0,80) e o vigor, de modo inverso (ρ = −0,62; r = −0,54). A tensão destaca-se por dois "
"comportamentos que a afastam do bloco de afeto negativo: correlaciona-se positivamente com o vigor "
"(ρ = 0,23; p ajustado = 0,028) e não se correlaciona com a fadiga. A leitura mais econômica atribui à "
"tensão, neste contexto, a função de ativação e não de sofrimento, embora uma explicação alternativa de "
"natureza métrica não possa ser descartada: com 40,4% das respostas no valor zero, a variável perde variância "
"e, com ela, capacidade de correlacionar-se.",
"O contraste entre as duas vias é mais informativo onde elas discordam. Nos pares que envolvem a depressão e "
"a confusão, ambas com efeito de piso severo, o coeficiente de Pearson supera sistematicamente o de Spearman: 0,70 contra 0,55 no par depressão e confusão, 0,79 contra 0,61 no par depressão e perturbação "
"total, 0,60 contra 0,44 no par confusão e perturbação total. A explicação é conhecida: poucos valores "
"extremos, em variáveis concentradas no zero, exercem alavancagem desproporcional sobre o coeficiente de "
"momento-produto. Nesses pares, a estimativa de postos é a defensável.",
]
R6=[
"A resposta ao tipo de estímulo, apresentada na Figura 4 e na Tabela 6, foi igualmente examinada pelas duas "
"vias, e o resultado é convergente e negativo. A distribuição dos seis perfis não difere entre os tipos de estímulo (χ² = 6,38; gl = 10; p = 0,782), e tampouco "
"a composição das três faixas (χ² = 3,03; gl = 4; p = 0,553). Os níveis médios das variáveis, comparados nos "
"vinte e dois atletas com registro nos três tipos de dia, não diferem em nenhuma variável por via alguma; o menor "
"valor de p é 0,062, na raiva, pela via não paramétrica, e 0,070, na perturbação total, pela análise de variância "
"de medidas repetidas.",
"A dinâmica intradiária, ao contrário, é robusta pelas duas vias. Nos dias de treino intervalado, a fadiga "
"sobe 2,02 pontos (Wilcoxon p < 0,001; t pareado p < 0,001; dz = 0,58), a perturbação total sobe 4,15 "
"(p < 0,001 em ambas; dz = 0,60) e o vigor cai 1,20 (p = 0,004; dz = −0,41). Nos dias de conteúdo técnico e "
"de força, com apenas vinte pares, os efeitos são maiores: a perturbação total sobe 6,90 pontos (dz = 0,79) e "
"o vigor cai 2,30 (dz = −0,72). A migração para a faixa de risco, considerados os 119 pares completos, tem direção clara: vinte e três pares "
"entram e dez saem (χ² = 4,36; p = 0,037); repartida por estímulo, apenas o treino intervalado alcança "
"significância bruta (p = 0,037), que não sobrevive à correção de Holm (p = 0,111).",
"Cabe registrar a advertência de delineamento que atravessa toda esta seção e que nenhuma via estatística "
"resolve: os tipos de estímulo não foram distribuídos ao acaso ao longo da semana, de modo que o tipo de dia "
"se confunde com a posição no microciclo e com a carga acumulada. O dia de conteúdo técnico e de força "
"ocorreu uma única vez, no penúltimo lugar da sequência, depois de vinte horas e meia de trabalho.",
]
R7=[
"O tratamento de séries oferece um critério paralelo, e a comparação com os valores de p é instrutiva. A "
"Tabela 7 põe lado a lado o veredito do piso de ruído e o das três vias inferenciais.",
"Convém distinguir esta contagem da apresentada na secção 3.2. Lá a comparação era entre as vias, e cinco das "
"sete variáveis recebiam veredito unânime. Aqui a comparação é entre o piso e as vias, e a raiva muda de "
"lado: as três rotas concordam em não a declarar significativa, e é justamente essa unanimidade que a opõe "
"ao piso.",
"As sete séries são sinal pelo piso, e em quatro delas as três vias confirmam o veredito. O vigor e a fadiga "
"deslocam-se 7,1 e 5,7 vezes o respectivo ruído, a perturbação total 4,5 vezes e a tensão 3,5 vezes, e todas "
"as quatro alcançam significância pelas três rotas. As três variáveis restantes divergem, e cada divergência "
"tem causa própria.",
"Na raiva, que se desloca 1,9 vez o seu ruído sem alcançar significância por via alguma, o piso é "
"permissivo: a trajetória não é monotônica, de modo que o deslocamento entre as pontas não representa a "
"série, e a leitura correta é a das vias inferenciais.",
"Na depressão, que apresenta a menor folga do conjunto, de 1,6 vez o ruído, e só alcança significância pelo "
"modelo misto, a divergência mede o custo do descarte de casos incompletos, conforme a secção 3.2 detalhou. "
"O piso e o modelo misto convergem, e ambos se opõem às duas vias que exigem série completa.",
"Na confusão, que se desloca 2,5 vezes o ruído e é significativa pelas duas vias de casos completos mas não "
"pelo coeficiente do modelo misto, a causa não é de poder estatístico, e sim de hipótese testada. O piso "
"acompanha o teste de Friedman, e por bom motivo: ambos respondem à magnitude do movimento, ao passo que o "
"coeficiente avalia a sua forma. A confusão cai 2,25 pisos na primeira transição e mais 1,06 na segunda, e a "
"partir daí oscila sem direção definida. O movimento existe, é grande e está concentrado no início da "
"semana; ele apenas não tem a forma de reta que o coeficiente procura.",
"A conclusão que essa comparação sustenta não é a de que um critério substitui o outro. É a de que eles respondem a perguntas distintas, uma sobre quanto a série se moveu em relação ao seu próprio "
"ruído, outra sobre a probabilidade de observar esse movimento sob a hipótese nula, e que reportar ambos permite ao leitor "
"identificar onde a conclusão é frágil.",
]

R8=[
 "O modelo que separa a carga do próprio dia da carga da véspera produz um resultado que reorganiza a leitura "
 "de todos os anteriores. As horas do próprio dia não exibem efeito detectável sobre a fadiga nem sobre o "
 "vigor; as horas da véspera exibem, e com folga. Cada hora de treino no dia anterior acrescenta 0,433 ponto "
 "de fadiga e subtrai 0,407 ponto de vigor no dia seguinte, ambos com p abaixo de 0,001. A perturbação total "
 "do humor acompanha, com 0,858 ponto por hora da véspera. A Tabela 8 apresenta as estimativas.",
 "O achado converge com a leitura das derivadas apresentada no artigo companheiro e a explica. Os dois "
 "choques da semana localizam-se nas suas extremidades porque é ali que a carga do dia anterior muda de "
 "patamar: o primeiro dia, de linha de base com uma hora e meia, antecede a primeira sessão intervalada; o "
 "sexto dia, com cinco horas, antecede o sétimo. O humor medido em cada manhã não informa sobre o treino que "
 "está por vir, e sim sobre o que já passou.",
 "A implicação prática é imediata e não exige o modelo preditivo do anexo metodológico para ser enunciada. Se "
 "a resposta afetiva é defasada em um dia, a leitura do humor matinal serve para decidir a sessão daquele dia "
 "com base no acúmulo do dia anterior, e não para avaliar a sessão que ainda não ocorreu. Serve, também, para "
 "situar corretamente o que se mede: o escore da manhã é consequência, não previsão."]

R9=[
 "A unidade de análise não altera apenas a prevalência descrita no artigo companheiro: altera o veredito "
 "inferencial. Na comparação entre a linha de base e a véspera da estreia, três das sete variáveis cruzam o "
 "limiar de cinco por cento em uma unidade e não cruzam em outra. A Tabela 10 apresenta os valores.",
 "A única variável que troca é a tensão, e a troca ocorre contra uma unidade específica: as três unidades "
 "pareadas concordam em declará-la significativa (p = 0,007), ao passo que a leitura não pareada sobre o registro "
 "isolado não o faz (p = 0,056). A explicação é de ponderação, não de efeito: a contagem por registro pesa cada "
 "atleta pelo número de vezes que respondeu, e o deslocamento da tensão, de 1,31 ponto entre os extremos da "
 "semana pelo par atleta-dia, reduz-se a 0,66 ponto quando os atletas mais assíduos dominam a média. Vigor, "
 "fadiga, confusão e perturbação total resistem a qualquer unidade, e depressão e raiva não alcançam "
 "significância em nenhuma.",
 "A comparação global entre os sete dias repete o padrão em escala menor: duas variáveis trocam de veredito, "
 "e são a tensão e a perturbação total do humor. Registre-se que a subamostra pareada produz, no contraste "
 "entre extremos, resultado idêntico ao do par atleta-dia, porque esse contraste já opera apenas sobre os atletas com medida nos dois dias; a coincidência vale como "
 "verificação de consistência do procedimento, não como achado.",
 "A consequência prática é direta e vale além deste estudo. Em séries de monitoramento com ausências, "
 "declarar a via estatística sem declarar a unidade de análise deixa metade da decisão implícita. Um "
 "relatório que informe apenas «p = 0,03 pelo teste de Wilcoxon» não permite ao leitor saber se o mesmo "
 "dado, contado de outra forma igualmente defensável, produziria p = 0,07."]

R9B=[
 "Convém distinguir essa instabilidade de uma terceira, que a auditoria de protocolo permitiu testar e que se "
 "revelou a mais consequente das três. A regra que compõe o valor diário foi conferida contra os carimbos de data "
 "e hora, e a conferência produziu duas correções de natureza distinta. A primeira restringiu os dias de segundo "
 "a sétimo ao primeiro e ao último registro de cada atleta, o que afastou 150 registros intermediários. Refeitas "
 "as três vias sobre essa base, nenhum dos vinte e um vereditos trocou de lado. A segunda corrigiu a linha de "
 "base, que passou a reter apenas a primeira resposta de cada atleta na noite de coleta única, o que afastou "
 "outros 21 registros. Essa segunda correção, muito menor em volume, trocou quatro dos vinte e um vereditos.",
 "O contraste entre as três sensibilidades é instrutivo, e a lição não é a que se esperaria. Vinte e um por cento "
 "dos registros afastados no miolo da semana não mudaram veredito algum; cinco por cento afastados na linha de "
 "base mudaram quatro. A assimetria tem explicação estrutural: o basal é o ponto contra o qual todos os seis "
 "contrastes se medem, de modo que um erro nele se propaga a todos, ao passo que um erro no valor de um dia "
 "intermediário afeta apenas os contrastes que o envolvem. Daí decorre uma recomendação prática que a literatura "
 "de monitoramento raramente enuncia: quando o desenho tem uma linha de base, a regra que a compõe merece "
 "escrutínio desproporcional ao número de observações que a formam.",
]

R10=[
 "O mecanismo de ausência, declarado como limitação não verificada nas versões anteriores deste estudo, "
 "passa a ser testado. Nenhuma das sete variáveis do dia corrente se associa à probabilidade de o atleta "
 "responder no dia seguinte após a correção para comparações múltiplas. A Tabela 11 apresenta os "
 "coeficientes.",
 "A tensão é a única candidata: o coeficiente é negativo, o sinal corresponde ao que se esperaria, pois quem amanhece mais tenso comparece um "
 "pouco menos no dia seguinte, e o valor bruto de p é de 0,014. Ele não sobrevive ao "
 "ajuste de Holm, que o leva a 0,101. A leitura honesta é que o dado não permite afirmar dependência, e "
 "tampouco permite descartá-la com segurança: com doze faltas em cento e quarenta e cinco oportunidades, a "
 "potência para detectar uma associação moderada é baixa.",
 "Duas verificações reforçam a leitura. As faltas concentram-se em oito dos vinte e sete atletas, e "
 "dezenove têm série completa; o número de faltas de cada atleta não se correlaciona com o seu humor médio "
 "ao longo da semana. E, sob imputação de pior caso nos ausentes do sétimo dia, as sete variáveis mantêm o sinal da variação entre os "
 "extremos da semana, conforme a Tabela 12. O intervalo mais largo é o da perturbação total, que vai de 5,87 a "
 "12,65 pontos em torno do valor observado de 8,51; o mais estreito é o da confusão, de −0,67 a −0,33.",
 "O conjunto sustenta a hipótese de ausência ignorável melhor do que uma declaração de limitação, e sem "
 "afirmá-la: o que se pode dizer é que, onde a dependência seria detectável, ela não aparece, e que as "
 "conclusões sobre a variação da semana não dependem do que os ausentes teriam respondido."]

R11=[
 "O contraste direto entre os dois estímulos que dominam a semana produz o resultado mais contraintuitivo "
 "deste artigo. No pareamento de cada atleta consigo mesmo, a resposta aguda ao HIIT supera a resposta ao amistoso "
 "na perturbação total do humor em 3,45 pontos, com tamanho de efeito moderado e valor de p de 0,016. O amistoso ocupa o dobro das horas do HIIT, quatro horas e meia ou cinco contra duas ou duas e meia, e ainda "
 "assim custa menos humor no mesmo dia. A Tabela 13 apresenta o contraste variável a variável.",
 "O resíduo da manhã seguinte, na Tabela 14, desloca a atenção para um terceiro estímulo. Nem o HIIT nem o "
 "amistoso deixam efeito detectável na manhã do dia seguinte; o dia técnico e de força deixa, e é grande: "
 "o vigor cai 2,73 pontos, com tamanho de efeito de 0,87 e magnitude de quase duas vezes o erro típico da "
 "medida. A perturbação total do humor acompanha, com aumento de 6,60 pontos.",
 "A convergência com a análise de séries do artigo companheiro é o que dá peso ao achado. Aquela análise "
 "localizou o segundo choque da semana na transição do sexto para o sétimo dia, por um critério que não "
 "usa valor de p nem tipo de estímulo, apenas a derivada da série contra o piso de ruído. Esta localiza o "
 "único resíduo detectável no dia técnico e de força, que é o sexto. Dois caminhos independentes apontam "
 "para o mesmo dia.",
 "O confundimento precisa ser declarado antes de qualquer leitura fisiológica. Há um único dia técnico e de "
 "força no microciclo, e ele é a véspera da estreia. O que se mede como efeito do estímulo é, "
 "inseparavelmente, efeito da posição no microciclo e da carga acumulada de vinte horas e meia. A "
 "convergência entre as duas análises fortalece a localização do fenômeno no tempo; não identifica a sua "
 "causa.",
 "A migração para a faixa de risco, por fim, não distingue os estímulos. Trinta e cinco por cento dos pares "
 "que amanhecem fora da faixa entram nela em dias de HIIT, contra 25,9 por cento no amistoso e 27,3 por "
 "cento no dia técnico e de força, sem diferença detectável entre os três. O desfecho categórico é menos "
 "sensível do que a variação contínua, e a comparação entre eles ilustra o custo de dicotomizar."]

DISCUSSAO=[
("Três decisões metodológicas, de pesos distintos",[
 "O resultado que organiza este artigo ganhou, com a análise por unidade e com a auditoria de protocolo, uma "
 "formulação mais precisa e mais modesta do que a inicial. Três decisões metodológicas foram postas à prova, e "
 "elas não pesam igual. A via de análise troca o veredito de duas variáveis, a depressão e a confusão. A unidade "
 "de análise troca o de uma, a tensão, e apenas contra a leitura não pareada. A regra que compõe a linha de base "
 "troca o de quatro. As três variáveis vulneráveis, tomadas em conjunto, são justamente aquelas de deslocamento "
 "intermediário em relação à dispersão; vigor e fadiga, cujo deslocamento supera cinco vezes o próprio ruído, "
 "resistem a toda combinação.",
 "Vigor e fadiga, cujo deslocamento entre os extremos da semana é de quatro vírgula cinco e de quatro vírgula "
 "três pontos, resistem a toda combinação de via, de unidade e de regra de composição. A raiva, que praticamente "
 "não se move, também resiste, pelo motivo oposto: nenhuma rota a declara significativa. A instabilidade "
 "concentra-se na faixa intermediária, onde o efeito existe mas é da ordem da variabilidade, e é justamente aí "
 "que se situam a depressão, a confusão e a tensão.",
 "A recomendação prática que decorre disso é mais modesta e mais útil do que «reportar várias vias». É declarar as duas escolhas, a via e a unidade, e verificar a estabilidade do veredito nas variáveis de "
 "deslocamento intermediário, que são justamente aquelas sobre as quais a decisão do leitor mudaria."]),
("O dia que deixa resíduo, e o que isso não autoriza a concluir",[
 "O contraste pareado entre HIIT e amistoso e a análise de resíduo produzem, juntos, um deslocamento de "
 "atenção. A resposta aguda maior é a do HIIT, apesar da metade das horas; o resíduo detectável na manhã "
 "seguinte não é nem do HIIT nem do amistoso, mas do dia técnico e de força. Isso converge com o modelo de "
 "carga defasada apresentado acima e com a localização do segundo choque pela análise de derivadas do "
 "artigo companheiro.",
 "A tentação de ler causalidade fisiológica aqui é grande e precisa ser resistida com clareza. O dia "
 "técnico e de força ocorre uma única vez no microciclo, e ocorre na véspera da estreia, com vinte horas e "
 "meia de carga acumulada. Efeito do conteúdo da sessão, efeito da posição na semana e efeito da carga "
 "acumulada são, neste desenho, o mesmo efeito. Três análises independentes concordam sobre QUANDO o "
 "fenômeno acontece; nenhuma delas identifica POR QUE.",
 "O desenho capaz de separá-los é conhecido e não é o deste estudo: exigiria alternar a ordem dos "
 "estímulos entre microciclos ou entre equipes. Enquanto isso não existe, o achado guarda valor descritivo e de planejamento, pois indica onde olhar, mas carece de valor explicativo."]),

("Quanto da conclusão pertence à via",[
 "O achado central deste estudo pode ser enunciado em uma frase: em três das sete variáveis examinadas, o "
 "veredito sobre a existência de mudança ao longo da semana depende da via de análise escolhida. Não se trata "
 "de discrepância marginal em torno do limiar. A tensão passa de p = 0,111 pelo teste de Friedman a p = 0,001 "
 "pelo modelo misto, dois valores separados por duas ordens de grandeza sobre exatamente os mesmos dados.",
 "A explicação principal é amostral e não conceitual. As vias clássicas de medidas repetidas exigem registro "
 "completo em todas as condições, e essa exigência, num elenco acompanhado por sete dias, descarta oito dos "
 "vinte e sete atletas e 88% dos pares atleta-dia disponíveis. O modelo misto retém todas as observações "
 "porque estima a variância entre atletas em vez de eliminá-la por emparelhamento. A diferença de potência "
 "que daí decorre é grande o bastante para inverter conclusões.",
 "Há, porém, um segundo mecanismo, e a confusão o exemplifica. Ela é a variável mais significativa pelo teste "
 "de Friedman e a única que perde significância ao passar para o modelo misto. A razão não é potência, e sim "
 "forma: a confusão desloca-se em degrau entre o primeiro e o segundo dia e depois oscila sem direção. O teste "
 "de Friedman pergunta se os dias diferem, sem especificar como; o modelo misto, na especificação adotada, "
 "pergunta se existe tendência linear. São perguntas diferentes, e a discordância entre elas informa a forma "
 "da trajetória em vez de contradizê-la. Um modelo misto com o dia como fator categórico responderia à "
 "primeira pergunta e provavelmente concordaria com o teste de postos.",
 "Esse ponto tem consequência prática para quem lê literatura de monitoramento. Um estudo que reporte apenas "
 "«ANOVA de medidas repetidas, p = 0,03» esconde três decisões: quantos participantes foram descartados por "
 "dados incompletos, se a esfericidade foi corrigida e se o efeito foi tratado como linear ou categórico. "
 "Nenhuma delas é técnica no sentido de irrelevante; todas as três podem inverter o resultado."]),
("Os pressupostos como diagnóstico, e não como formalidade",[
 "A verificação de pressupostos costuma ser reportada como ritual: uma frase que declara normalidade "
 "verificada e segue adiante. Os presentes dados sugerem um uso mais produtivo. Nenhuma das sete variáveis "
 "passa no teste de Shapiro-Wilk; o ε de Greenhouse-Geisser fica entre 0,327 e 0,693 em todas; e quatro das "
 "seis subescalas apresentam efeito de piso acima do critério de Terwee et al. (2007). Esse conjunto não invalida a análise paramétrica, uma vez que a correção existe precisamente para isso, mas "
 "assinala onde a estimativa está sob tensão.",
 "O efeito de piso, em particular, deixa marca identificável nos coeficientes de associação. Nos pares que "
 "envolvem a depressão e a confusão, ambas com mais de metade das respostas no valor mínimo, o coeficiente de "
 "Pearson excede sistematicamente o de Spearman, com diferenças de até 0,18. Poucos valores extremos, em "
 "distribuições concentradas no zero, exercem alavancagem desproporcional sobre o coeficiente de "
 "momento-produto. Reportar apenas o de Pearson, nesse contexto, superestima a associação.",
 "A recomendação que decorre é que os pressupostos sejam reportados variável a variável, e não como declaração "
 "global sobre o conjunto. Um estudo de monitoramento com seis subescalas pode ter três variáveis em que a via "
 "paramétrica se sustenta e três em que não se sustenta, e a média entre elas não descreve nenhuma."]),
("O critério de ruído como leitura independente do valor de p",[
 "O tratamento de séries adotado neste estudo fornece um critério que não depende de hipótese nula alguma: o "
 "deslocamento total é comparado ao piso de ruído da própria série. As duas leituras convergem onde o "
 "movimento é grande, pois vigor e fadiga constituem sinal pelo piso, com folga de 7,1 e 5,7 vezes, e "
 "alcançam significância pelas três vias, e o mesmo vale para a perturbação total e para a tensão. A "
 "divergência aparece nas variáveis de folga estreita, e é aí que ela se torna útil, porque nomeia a razão "
 "pela qual dois critérios defensáveis chegam a vereditos distintos sobre o mesmo dado.",
 "As três divergências observadas ilustram três lições distintas. Na depressão, o custo do descarte de casos "
 "incompletos: o modelo misto, que aproveita os 166 pares, detecta o que as vias restritas às dezenove "
 "trajetórias completas não detectam. Na raiva, a permissividade do piso: a trajetória não é monotônica e o "
 "deslocamento entre as pontas não representa a série, de modo que nenhuma via confirma o que o critério "
 "sugere. Na confusão, a diferença entre as hipóteses testadas: Friedman e a ANOVA reconhecem um movimento "
 "que o coeficiente linear do modelo misto não reconhece, porque a queda concentra-se nas duas primeiras "
 "transições e não desenha uma reta. Nenhuma das três é falha de um critério isolado; cada uma revela algo "
 "sobre a série que uma leitura única deixaria oculto.",
 "Nenhum dos dois critérios é superior ao outro em abstrato. O valor de p responde a uma pergunta sobre "
 "probabilidade; o piso, a uma pergunta sobre magnitude relativa ao próprio ruído. A literatura de "
 "monitoramento do atleta já se move nessa direção quando adota a mínima variação detectável para decisões "
 "individuais (TERWEE et al., 2007; SAW; MAIN; GASTIN, 2016); o que se propõe aqui é a extensão do mesmo "
 "raciocínio às séries agregadas do grupo, com o critério declarado antes da leitura."]),
("O que os resultados dizem sobre o microciclo, e não sobre o método",[
 "Interessa registrar que, apesar da divergência entre vias, o retrato substantivo do microciclo é estável. As três vias concordam que o vigor cai e a fadiga sobe, e essas são as duas variáveis com maior tamanho de "
 "efeito por qualquer índice: dz de −1,53 e 0,99, r de 0,84 e 0,76. A ordenação das variáveis por magnitude é "
 "praticamente idêntica pelas duas vias. A raiva não se move por critério algum. O eixo do microciclo terminal é, "
 "portanto, o par vigor e fadiga, e essa conclusão não depende da escolha metodológica.",
 "O modelo misto acrescenta a taxa: a fadiga sobe 0,354 ponto por dia e o vigor cai 0,335, o que projeta cerca "
 "de dois pontos de deslocamento ao longo da semana em cada direção. A decomposição da variância acrescenta "
 "outra informação de valor prático: a proporção atribuível a diferenças estáveis entre atletas vai de 0,341 "
 "na raiva a 0,765 na depressão. Variáveis com proporção elevada exigem referência intraindividual no "
 "monitoramento, porque comparar um atleta à média do grupo confunde traço com estado. Essa distinção dialoga "
 "com a evidência de que a carga se distribui de modo desigual entre atletas do mesmo elenco (BÜCHEL; DÖRING; "
 "BAUMEISTER, 2026) e de que a resposta ao treino é individual (SAW; MAIN; GASTIN, 2016).",
 "Quanto ao estímulo, as duas vias convergem em um resultado negativo: nem a distribuição dos perfis nem os "
 "níveis médios distinguem os tipos de dia, com a única exceção da raiva pela via de postos. A dinâmica "
 "intradiária, ao contrário, é robusta pelas duas vias, e a migração para a faixa de risco ao longo do dia é o "
 "fenômeno mais consistente do conjunto. A leitura que os dados sustentam é que o custo do dia de treino "
 "existe e é mensurável, ao passo que a sua atribuição a um tipo particular de estímulo não se sustenta neste "
 "tamanho de amostra e neste delineamento."]),
]
LIMITACOES=[
"A comparação entre vias realizada aqui é empírica e não simula condições controladas. Ela mostra que as vias "
"divergem neste conjunto de dados, com esta estrutura de ausências e estas distribuições, e não estabelece "
"com que frequência divergiriam em outros. Um estudo de simulação com estruturas de dados variadas seria o "
"complemento natural.",
"O modelo misto foi especificado com intercepto aleatório e efeito linear do dia. Especificações alternativas, entre elas o dia como fator categórico, a inclinação aleatória por atleta e a "
"estrutura autorregressiva para os resíduos, produziriam estimativas distintas, e o caso da confusão mostra que a escolha importa. A especificação "
"adotada é a mais simples que responde à pergunta de tendência, e essa escolha foi declarada em vez de "
"otimizada contra o resultado.",
"O mecanismo de ausência não foi modelado. As faltas às sessões não são aleatórias e podem correlacionar-se "
"com o próprio estado que se mede, o que introduz possibilidade de viés que nem o modelo misto elimina; ele "
"apenas dispensa a exigência de dados completos sob o pressuposto mais fraco de ausência aleatória "
"condicional às covariáveis observadas.",
"Os tipos de estímulo não foram distribuídos ao acaso ao longo da semana, de modo que o tipo de dia se "
"confunde com a posição no microciclo e com a carga acumulada. Nenhuma via estatística resolve confundimento "
"de delineamento.",
"Quatro das seis subescalas apresentam efeito de piso severo, o que compromete a detecção de melhora e "
"introduz assimetria em toda comparação. O estudo acompanhou uma única equipe masculina de primeira divisão "
"em uma única semana, e não registrou desfechos externos de desempenho, marcadores fisiológicos ou lesão.",
 "A cobertura da grade que cruza atleta e dia recua a setenta e oito por cento do elenco no quarto e no sétimo "
 "dias, e o número de respostas por atleta e por dia varia de um a seis, acima do previsto no protocolo. A "
 "primeira condição reduz o número de casos completos sobre o qual as vias clássicas podem operar e é uma das "
 "duas causas da divergência entre rotas documentada neste artigo. A segunda foi tratada pela regra de composição "
 "descrita no método, que retém o primeiro e o último registro de cada dia e afasta os 150 intermediários, de "
 "modo que todo atleta-dia contribui com o mesmo número de medidas; resta, ainda assim, a heterogeneidade da "
 "janela entre o pré e o pós, cuja amplitude vai de 52 a 854 minutos.",
 "O modelo que separa a carga do dia da carga da véspera opera sobre uma única equipe e sete dias, condição "
 "na qual o efeito das horas não se separa do efeito do dia do microciclo nem da carga acumulada. Os "
 "coeficientes são associativos, e a defasagem que eles revelam é convergente com as derivadas, não "
 "demonstrativa de causalidade."
,
 "O teste do mecanismo de ausência tem potência baixa. São doze faltas em cento e quarenta e cinco "
 "oportunidades, e a tensão, única variável com valor bruto de p abaixo de cinco por cento, não sobrevive à "
 "correção para as sete comparações. O resultado é compatível com ausência ignorável e não a demonstra; o "
 "que se pode afirmar é que as conclusões sobre a variação da semana sobrevivem aos cenários extremos de "
 "imputação."
]
CONCLUSAO=[
"Submetida às três vias de análise, a mesma série de humor produziu vereditos concordantes em cinco das sete "
"variáveis e discordantes em duas. A depressão passou de não significativa pelas vias que exigem registro "
"completo a significativa pelo modelo misto; a confusão percorreu o caminho inverso. A causa principal é o custo "
"amostral das vias clássicas de medidas repetidas, que exigem registro completo e descartam 88% dos pares "
"disponíveis; a causa secundária é a diferença entre perguntar se os dias diferem e perguntar se existe tendência "
"linear. À variação por via somam-se outras duas, de peso distinto: a unidade de análise trocou um veredito e a "
"regra que compõe a linha de base trocou quatro.",
"O retrato substantivo do microciclo, contudo, resistiu à variação metodológica. O vigor cai e a fadiga sobe por qualquer via e por qualquer índice de magnitude, com os dois maiores tamanhos de "
"efeito do conjunto, e a raiva não se move por critério algum. As duas vias ordenam as variáveis por magnitude de "
"modo praticamente idêntico, o que indica que a discordância diz respeito à detecção e não à importância "
"relativa.",
"Três recomendações decorrem do estudo. Primeira: em séries de monitoramento com ausências frequentes, "
"reportar mais de uma via, e explicitar quantos participantes cada uma descarta. Segunda: reportar os "
"pressupostos variável a variável, e não como declaração global, porque o efeito de piso e a violação de "
"esfericidade não se distribuem igualmente entre as subescalas. Terceira: acompanhar o valor de p com um "
"critério de magnitude relativo ao ruído da própria série, declarado antes da leitura, de modo que o leitor "
"identifique onde a conclusão é frágil.",
"A discordância entre vias não é um defeito a ocultar. Ela é informação: aponta qual pressuposto está sob "
"tensão em cada variável e, com isso, torna auditável um julgamento que de outro modo permaneceria implícito.",
]
