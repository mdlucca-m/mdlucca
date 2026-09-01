# -*- coding: utf-8 -*-
"""Artigo 1 — descritivo-analítico."""
TITULO=("Perfil e comportamento das dimensões do humor ao longo da última semana de pré-temporada de "
        "atletas de handebol de elite: descrição por limites, derivadas e piso de ruído")
SUB=("Estudo observacional longitudinal com coletas diárias pré e pós, comparação com a linha de base e "
     "tratamento de séries por suavização, derivadas e limiar explícito de ruído")

RESUMO=(
"A literatura sobre humor no esporte descreve escores em corte transversal e raramente acompanha o mesmo "
"atleta ao longo de um microciclo. Quando o faz, compara médias diárias sem declarar qual magnitude de "
"variação considerará relevante, o que deixa a interpretação refém do que se observa. Este estudo descreveu "
"por completo as sete variáveis da Escala de Humor de Brunel ao longo da última semana de pré-temporada de "
"atletas de handebol de elite e propôs um tratamento de série que combina suavização, derivadas de primeira "
"e segunda ordem e um piso de ruído contra o qual toda variação é contrastada. Vinte e sete atletas "
"masculinos de primeira divisão nacional responderam ao instrumento durante sete dias, o que gerou 456 "
"registros agregados em 166 pares atleta-dia e 119 pares de manhã e noite. O primeiro dia teve janela única "
"noturna e serviu de linha de base; do segundo ao sétimo houve medida matinal e vespertina ou noturna. O "
"piso de ruído foi definido como a média dos erros-padrão diários, e declarou-se variação real apenas quando "
"o deslocamento total o superou. Quatro das seis subescalas concentraram entre 40,4% e 65,7% das respostas no "
"valor mínimo. Em escala normativa, a fadiga situou-se em 57,7 e a raiva em 55,4, ao passo que o vigor caiu a "
"43,7 e a tensão a 41,6. O vigor recuou 2,98 pontos contra um piso de 0,59 e a fadiga avançou 3,62 contra "
"0,76; a depressão foi a única série cuja variação não superou o piso. As transições de choque concentraram-se "
"nas duas extremidades da semana e deixaram um platô de quatro dias entre elas. O perfil iceberg recuou de "
"37,0% para 19,0% e a barbatana de tubarão avançou de 11,1% para 28,6%; a faixa de risco passou de 22,2% para "
"52,4%. O teste formal de cruzamento reconheceu inversão estabelecida entre vigor e fadiga no quinto dia e "
"entre vigor e perturbação total no sexto, mas recusou a inversão aparente entre tensão e raiva. Conclui-se "
"que a deterioração do humor no microciclo terminal não é gradual, e sim concentrada em dois eventos discretos, "
"e que a distinção entre variação real e flutuação amostral exige um critério declarado antes da leitura."
)
PALAVRAS=("humor; handebol; Escala de Humor de Brunel; monitoramento do atleta; séries temporais; "
          "pré-temporada")

ABSTRACT=(
"Research on mood in sport reports scores cross-sectionally and rarely follows the same athlete across a "
"microcycle. When it does, it compares daily means without declaring what magnitude of change will count as "
"relevant, which leaves interpretation hostage to whatever is observed. This study fully described the seven "
"variables of the Brunel Mood Scale across the final pre-season week of elite handball players and proposed a "
"series treatment combining smoothing, first and second derivatives, and a noise floor against which every "
"change is contrasted. Twenty-seven male first-division players completed the instrument over seven days, "
"yielding 456 records aggregated into 166 athlete-day pairs and 119 morning-evening pairs. Day one had a "
"single evening window and served as baseline; days two to seven had a morning and a later measurement. The "
"noise floor was defined as the mean of the daily standard errors, and a real change was declared only when "
"total displacement exceeded it. Four of the six subscales concentrated between 40.4% and 65.7% of responses "
"at the minimum value. On the normative scale, fatigue reached 57.7 and anger 55.4, whereas vigour fell to "
"43.7 and tension to 41.6. Vigour dropped 2.98 points against a floor of 0.59 and fatigue rose 3.62 against "
"0.76; depression was the only series whose change did not exceed its floor. Shock transitions concentrated at "
"both ends of the week, leaving a four-day plateau between them. The iceberg profile retreated from 37.0% to "
"19.0% and the shark fin advanced from 11.1% to 28.6%; the risk band went from 22.2% to 52.4%. The formal "
"crossing test recognised an established inversion between vigour and fatigue on day five and between vigour "
"and total mood disturbance on day six, but rejected the apparent inversion between tension and anger. Mood "
"deterioration in the terminal microcycle is not gradual but concentrated in two discrete events, and telling "
"real change from sampling fluctuation requires a criterion declared before reading."
)
KEYWORDS=("mood; handball; Brunel Mood Scale; athlete monitoring; time series; pre-season")

INTRO=[
"O reconhecimento de que o estado afetivo informa sobre a condição de treino de um atleta antecede em décadas "
"o instrumental que hoje o mede. Morgan (1985) propôs um modelo de saúde mental no qual o bem-estar "
"psicológico acompanha o êxito esportivo, e a representação gráfica desse bem-estar — vigor acima da média "
"normativa e as cinco dimensões negativas abaixo dela — recebeu o nome de perfil iceberg (MORGAN, 1980). O "
"Profile of Mood States sustentou essa tradição até que Terry et al. (1999) dele derivassem uma versão breve "
"de vinte e quatro itens, a Escala de Humor de Brunel, validada em seguida para amostras atléticas com "
"valores normativos próprios (TERRY; LANE, 2000) e adaptada ao português por Rohlfs et al. (2008), com "
"estudos psicométricos posteriores em atletas brasileiros (ROHLFS et al., 2023).",

"A força do iceberg como imagem converteu-se, porém, em limitação analítica. Ao reduzir um vetor de seis "
"dimensões a um rótulo binário, a literatura descartou a informação das configurações intermediárias. "
"Parsons-Smith, Terry e Machin (2017) romperam esse impasse com uma classificação por agrupamento que "
"identificou seis configurações recorrentes: além do iceberg, a superfície, o submerso, a barbatana de "
"tubarão, o iceberg invertido e o Everest invertido. A proposta encontrou replicação em contextos culturais "
"diversos (HAN; PARSONS-SMITH; TERRY, 2020; TERRY et al., 2022; LEW et al., 2023; TERRY; PARSONS-SMITH; "
"VLACHOPOULOS, 2024) e chegou ao Brasil pela mão de Rohlfs, Noce e Wilke (2024).",

"Persiste, contudo, uma assimetria entre o que a classificação promete e o uso que dela se faz. Os seis "
"perfis descrevem estados, não traços; entretanto, quase toda a evidência disponível provém de medidas "
"únicas, em corte transversal, que estimam prevalências populacionais sem acompanhar o mesmo atleta ao longo "
"do tempo. Luojumäki et al. (2026) exploraram a distribuição dos agrupamentos por nível de atividade, gênero "
"e idade e permaneceram no plano transversal. Conhece-se, assim, a frequência dos perfis em uma população e "
"ignora-se a dinâmica deles em um indivíduo submetido a cargas sucessivas.",

"O handebol oferece cenário exigente para essa investigação. A modalidade combina deslocamentos de alta "
"intensidade, mudanças de direção, saltos, arremessos e contato permanente, com demandas que variam conforme "
"a posição em quadra (KARCHER; BUCHHEIT, 2014) e o esquema defensivo (SAAL; RHEINSBERG; BAUMGART, 2026). "
"Revisões sistemáticas confirmam esse perfil intermitente e de alta densidade (GARCÍA-SÁNCHEZ et al., 2023; "
"PEREZ ARMENDARIZ; SPYROU; ALCARÁZ, 2024). A pré-temporada agrava o quadro: Rafnsson et al. (2021) "
"documentaram associação entre carga e problemas por uso excessivo justamente nesse período, e Bjørndal et "
"al. (2021) observaram que picos de carga precedem problemas de saúde ao longo da temporada. A carga "
"distribui-se de modo desigual entre atletas do mesmo elenco (BÜCHEL; DÖRING; BAUMEISTER, 2026), o que "
"reforça a necessidade de monitoramento individual. O levantamento de Henze et al. (2025) revelou que a "
"prática em clubes profissionais de handebol ainda privilegia indicadores externos, apesar da evidência de "
"que medidas subjetivas superam medidas objetivas na detecção de respostas ao treino (SAW; MAIN; GASTIN, 2016).",

"A relação entre humor e rendimento foi submetida a duas metanálises que convergem: o efeito existe, é "
"consistente e é de magnitude modesta (BEEDIE; TERRY; LANE, 2000; LOCHBAUM et al., 2021). O valor prático do "
"instrumento reside, por isso, menos na predição de desempenho e mais na vigilância do estado de recuperação. "
"Os documentos de consenso sobre supertreinamento e recuperação atribuem ao humor papel de sentinela precoce "
"(MEEUSEN et al., 2013; KELLMANN et al., 2018), e essa vigilância articula-se com o sono e com o estresse "
"percebido (FERREIRA et al., 2023; SAWCZUK et al., 2021; COSTA; FIGUEIREDO; NAKAMURA, 2022). McFadden et al. "
"(2021) acompanharam mudanças psicológicas ao longo de uma temporada universitária, Bird et al. (2025) "
"reuniram humor, sono e desempenho em seleção nacional durante competição internacional, e Rohlfs et al. "
"(2025) associaram estados de humor à condição de lesão e ao desempenho no salto com contramovimento.",

"Resta um problema metodológico anterior a todos esses, e ele é silencioso. Séries curtas de medidas "
"psicométricas oscilam por razões que nada devem à carga: variação amostral entre dias, ausências, "
"arredondamento em escalas de amplitude estreita. Quando se comparam médias diárias sem um critério de "
"decisão, qualquer subida ou descida ganha estatuto de achado. A literatura psicométrica reconhece o "
"princípio ao exigir a mínima mudança detectável para escores individuais (TERWEE et al., 2007), porém "
"raramente transporta o mesmo cuidado para as séries agregadas do grupo, precisamente onde a tentação "
"narrativa é maior. Não se localizou, na literatura consultada, estudo que aplicasse ao acompanhamento diário "
"das dimensões do humor um tratamento que reunisse suavização, derivadas de primeira e segunda ordem e um "
"limiar explícito de ruído contra o qual toda variação fosse contrastada.",

"Essas lacunas justificam o presente estudo. De um lado, o handebol de elite impõe, na semana que antecede a "
"estreia competitiva, uma sucessão de estímulos heterogêneos cuja repercussão afetiva permanece indocumentada "
"em escala diária. De outro, o instrumental disponível para descrever essa repercussão carece de um critério "
"que separe sinal de ruído. A conjunção dos dois problemas define o objetivo geral desta investigação: "
"descrever o perfil e o comportamento das variáveis do BRUMS ao longo da última semana de pré-temporada de "
"atletas de handebol de elite, com comparação diária entre a manhã e a noite e contraste permanente com a "
"linha de base, por meio de um tratamento de séries que combina suavização, análise de derivadas, piso de "
"ruído e teste formal de cruzamento entre trajetórias.",
]

METODO=[
("Delineamento e contexto",[
 "Trata-se de estudo observacional longitudinal de medidas repetidas, com sete dias consecutivos e "
 "delineamento intraindividual. O período corresponde ao microciclo terminal da pré-temporada, isto é, à "
 "semana imediatamente anterior à estreia da equipe na competição oficial. A escolha desse recorte não é "
 "acidental: nele coexistem a carga acumulada de toda a preparação e a proximidade psicológica da estreia. "
 "Nenhuma intervenção foi introduzida pelos pesquisadores; a programação permaneceu sob responsabilidade da "
 "comissão técnica, e o estudo limitou-se a registrar o que ocorreu.",
 "A semana reuniu quatro tipos de estímulo. O primeiro dia contemplou apenas uma sessão de conteúdo técnico e "
 "tático, com uma hora e meia de duração, e serviu de linha de base. O segundo, o quarto e o sétimo dias "
 "combinaram treino intervalado de alta intensidade com trabalho técnico e tático. O terceiro e o quinto dias "
 "incluíram jogo amistoso. O sexto concentrou conteúdo técnico, tático e de força. A carga acumulada progrediu "
 "de 1,5 hora no primeiro dia para 23,0 horas ao término do sétimo."]),
("Participantes",[
 "Participaram vinte e sete atletas de handebol masculino de uma equipe da primeira divisão nacional, com "
 "idade média de 21,96 anos e desvio-padrão de 3,81 anos. Todos integravam o elenco principal e cumpriam a "
 "programação regular de pré-temporada. Adotaram-se como critérios de inclusão o vínculo formal com a equipe e "
 "a participação nas sessões da semana; excluíram-se atletas em reabilitação que os afastasse do treino "
 "coletivo. A perda de observações decorreu de ausências pontuais e de não devolução do instrumento, o que "
 "reduziu o número de respondentes de vinte e sete no primeiro dia para vinte e um no sétimo."]),
("Procedimento de coleta",[
 "O contato inicial com a comissão técnica ocorreu três meses antes do início da coleta, em reunião na qual se "
 "apresentaram os objetivos, o instrumento e a carga de resposta imposta ao atleta. Após a anuência da "
 "comissão, realizou-se reunião com o elenco, com explicação do procedimento e assinatura do termo de "
 "consentimento livre e esclarecido. Uma sessão de familiarização antecedeu a semana de coleta.",
 "Durante a semana, o protocolo diferenciou o primeiro dia dos demais. No primeiro dia houve janela única de "
 "coleta, aplicada à noite, após o treino: os quarenta e oito registros desse dia distribuem-se entre 20h42 e "
 "01h19 do dia seguinte, e nenhum registro matinal existe. Essa medida foi tomada como linha de base do "
 "microciclo. Do segundo ao sétimo dia houve duas coletas: a primeira pela manhã, antes da sessão inicial, "
 "tratada como medida pré; a última ao fim do dia, tratada como medida pós. Cabe registrar que, no sétimo dia, "
 "todos os quarenta e seis registros ocorreram entre 08h e 14h, de modo que a medida pós daquele dia "
 "corresponde ao início da tarde e não à noite.",
 "A unidade de análise adotada é o par atleta-dia: um valor por atleta e por dia, obtido pela média das "
 "respostas daquele atleta naquele dia. Essa escolha elimina a pseudorreplicação que decorreria do tratamento "
 "de duas ou mais respostas do mesmo atleta no mesmo dia como observações independentes, e garante que cada "
 "atleta pese igualmente em cada dia. As análises de dinâmica intradiária, ao contrário, preservam as duas "
 "medidas e operam sobre os 119 pares completos de manhã e tarde ou noite. O conjunto final reuniu 456 "
 "registros, 166 pares atleta-dia e 119 pares pré e pós."]),
("Procedência dos dados e tratamento de divergências",[
 "A base primária é o export do formulário eletrônico preenchido pelos atletas. Uma auditoria prévia "
 "identificou divergências entre versões derivadas dessa base, e o presente estudo as resolveu antes de "
 "qualquer análise. Três decisões merecem registro.",
 "Primeira: o dia de cada registro passou a ser definido pelo carimbo de data e hora do formulário, com "
 "fronteira às quatro da manhã, e não pela data autorreferida pelo respondente. Essa coluna contém datas de "
 "nascimento e erros de digitação, e por ela 136 dos 457 registros cairiam fora da semana de estudo. A "
 "fronteira às quatro da manhã devolve ao primeiro dia seis registros lançados entre meia-noite e uma da "
 "manhã do dia seguinte, todos de atletas que já haviam respondido na noite anterior.",
 "Segunda: quatro registros receberam o rótulo «não identificado» na coluna de nome padronizado, o que criaria "
 "um vigésimo oitavo atleta inexistente. Dois foram devolvidos ao respondente por correspondência exata no "
 "dicionário de variantes de nome e dois pelo nome curado, no mesmo carimbo de data e hora, de uma base "
 "derivada. O elenco é, portanto, de vinte e sete atletas.",
 "Terceira: a unidade de análise passou a ser declarada. Quatro unidades circulavam nas versões anteriores — "
 "o registro isolado, o par formado pelo primeiro e pelo último registro do dia, o par atleta-dia e a "
 "subamostra dos atletas com medida no primeiro e no sétimo dia. Elas produzem, sobre exatamente os mesmos "
 "dados e com a mesma classificação, variações do perfil iceberg entre o primeiro e o sétimo dia que vão de "
 "0,6 a 18,0 pontos percentuais. A Figura 2 apresenta essa comparação, e o Quadro 1 documenta a linhagem."]),
("Instrumentos",[
 "Aplicou-se a Escala de Humor de Brunel em sua versão brasileira (ROHLFS et al., 2008), composta por vinte e "
 "quatro itens distribuídos em seis subescalas de quatro itens — tensão, depressão, raiva, vigor, fadiga e "
 "confusão —, respondidos em escala de cinco pontos, de zero a quatro, com amplitude de zero a dezesseis por "
 "subescala. A instrução temporal solicitou ao atleta que considerasse como se sentia naquele momento. A "
 "perturbação total do humor resulta da soma das cinco subescalas negativas subtraída do vigor. Todas as "
 "subescalas foram recalculadas a partir dos vinte e quatro itens e conferidas contra as colunas já "
 "computadas na planilha de origem, sem divergência em nenhuma das 2.736 células conferidas.",
 "Para permitir comparação com a norma e classificação nos seis perfis, cada subescala foi convertida em "
 "escore T por padronização contra parâmetros normativos de amostras atléticas, com média cinquenta e "
 "desvio-padrão dez, recuperados por inversão das faixas de escore T publicadas."]),
("Classificação nos seis perfis de humor",[
 "A classificação seguiu a proposta de Parsons-Smith, Terry e Machin (2017). Aplicou-se agrupamento por "
 "k-médias com seis centros, semeados nos centroides canônicos, de modo que a solução não dependesse de "
 "inicialização aleatória; os agrupamentos resultantes foram reancorados aos rótulos originais por atribuição "
 "ótima. Para leitura clínica, os seis perfis foram agregados em três faixas: a favorável reúne o iceberg; a "
 "neutra, a superfície e o submerso; e a de risco, a barbatana de tubarão, o iceberg invertido e o Everest "
 "invertido, configurações que a literatura associa a maior vulnerabilidade (TERRY; PARSONS-SMITH, 2021)."]),
("Tratamento de séries: suavização, derivadas e piso de ruído",[
 "O núcleo metodológico deste estudo é o tratamento aplicado às séries diárias, tanto às médias das subescalas "
 "quanto às prevalências dos perfis. O procedimento tem quatro passos encadeados.",
 "O primeiro estima a incerteza de cada ponto. Para séries de médias, o erro-padrão diário resulta do "
 "desvio-padrão da amostra do dia dividido pela raiz do número de respondentes daquele dia; para séries de "
 "prevalência, decorre da fórmula binomial. O piso de ruído da série é a média dos erros-padrão dos sete dias, "
 "e responde a uma pergunta simples: qual é a magnitude típica da oscilação que a amostragem, por si só, "
 "produz nesta série?",
 "O segundo suaviza a série por filtro binomial de três pontos, no qual cada ponto interno recebe peso um meio "
 "e cada vizinho recebe peso um quarto; os extremos permanecem inalterados. O filtro atenua a oscilação de "
 "alta frequência sem deslocar o nível da série, e a soma unitária dos pesos garante que a média não se altere "
 "de modo sistemático.",
 "O terceiro calcula as derivadas discretas da série suavizada. A primeira, obtida pela diferença entre dias "
 "consecutivos, mede a velocidade da mudança; a segunda, pela diferença entre velocidades consecutivas, mede a "
 "aceleração. Ambas foram expressas em unidades do piso de ruído da própria variável, o que torna comparáveis "
 "subescalas de amplitude e dispersão distintas. Chama-se transição de choque aquela cuja primeira derivada, "
 "em valor absoluto, supera o piso, e ponto de inflexão a abscissa, obtida por interpolação linear, em que a "
 "segunda derivada muda de sinal.",
 "O quarto emite o veredito. Declara-se variação real, ou sinal, quando o deslocamento total entre o primeiro "
 "e o sétimo dia supera, em valor absoluto, o piso de ruído; caso contrário, atribui-se a oscilação à "
 "flutuação amostral. O mesmo princípio governa o teste de cruzamento entre duas séries: calcula-se a série da "
 "diferença e o limiar combinado, definido como a raiz da soma dos quadrados dos dois pisos; o ponto de "
 "cruzamento é a abscissa em que a diferença muda de sinal; e a inversão só é declarada estabelecida quando a "
 "diferença ultrapassa o limiar antes e depois do cruzamento. Do contrário, o achado é classificado como "
 "divergência, categoria que reconhece a troca de posição sem lhe atribuir estatuto de resultado.",
 "Cabe uma ressalva sobre o alcance do piso binomial. Em prevalências próximas de zero, o produto entre a "
 "proporção e o seu complemento tende a zero e o erro-padrão encolhe artificialmente, o que rebaixa o piso e "
 "torna o critério permissivo. Séries de prevalência muito baixa exigem, por isso, leitura cautelosa, e o "
 "texto assinala explicitamente onde essa condição ocorre."]),
("Análise estatística e processamento computacional",[
 "Toda a análise foi executada em Python 3.11. A cadeia parte da planilha e termina no arquivo de saída, sem "
 "etapa manual intermediária, e reproduz-se pela execução de um único comando.",
 "A importação empregou o pacote openpyxl, com percurso célula a célula e reconstrução da matriz de respostas. "
 "Os identificadores nominais foram substituídos por códigos anônimos de A01 a A27 na própria rotina de "
 "importação, de modo que nenhum nome trafegasse para as etapas seguintes. A conversão para arranjos "
 "numéricos, o cálculo de médias diárias, a padronização em escore T, a suavização, as derivadas e os pisos de "
 "ruído utilizaram o NumPy (HARRIS et al., 2020).",
 "Os testes de hipótese utilizaram o módulo stats do SciPy (VIRTANEN et al., 2020). A verificação de "
 "normalidade recorreu ao teste de Shapiro-Wilk, cujo resultado motivou a opção não paramétrica na descrição. "
 "A comparação global entre os sete dias empregou o teste de Friedman (FRIEDMAN, 1937), com tamanho de efeito "
 "pelo W de Kendall (KENDALL; SMITH, 1939); a hipótese de tendência ordenada recebeu tratamento específico "
 "pelo teste L de Page (PAGE, 1963); os contrastes pareados recorreram ao teste de postos sinalizados de "
 "Wilcoxon (WILCOXON, 1945), com correção de Holm (HOLM, 1979). A estabilidade da prevalência de cada perfil "
 "foi avaliada pelo Q de Cochran (COCHRAN, 1950) e a migração intradiária pelo teste de McNemar (McNEMAR, "
 "1947). A associação entre tipo de estímulo e perfil empregou o qui-quadrado de contingência, e as "
 "associações entre variáveis contínuas, o coeficiente de Spearman.",
 "A confiabilidade das medidas repetidas foi estimada por correlação intraclasse de via única, com o "
 "coeficiente de medida média obtido pela fórmula de Spearman-Brown (SHROUT; FLEISS, 1979), acompanhada do "
 "erro-padrão de medida e da mínima variação detectável. O efeito de piso foi avaliado pelo critério de Terwee "
 "et al. (2007). Adotou-se alfa de cinco por cento. As figuras foram produzidas com matplotlib (HUNTER, 2007) "
 "e a exportação do manuscrito utilizou a biblioteca python-docx. Todos os resultados intermediários foram "
 "depositados em uma base única, o que permite auditar cada número do texto contra o objeto que o gerou."]),
("Aspectos éticos e proteção de dados",[
 "O projeto obteve aprovação do comitê de ética em pesquisa com seres humanos sob o parecer CAAE [inserir "
 "número do CAAE], e observou as diretrizes da Resolução 466/2012 do Conselho Nacional de Saúde e os "
 "princípios da Declaração de Helsinque. Todos os participantes assinaram termo de consentimento livre e "
 "esclarecido antes da primeira coleta.",
 "A base primária continha nomes completos associados a escores de humor e a registros de lesão. A "
 "substituição por códigos anônimos ocorre na própria rotina de importação, e apenas a base anonimizada "
 "alimenta as análises. Os arquivos com identificação nominal permanecem sob guarda restrita do pesquisador "
 "responsável e não integram material suplementar nem repositório de dados abertos."]),
]

R1=[
"Os 456 registros distribuem-se de modo desigual ao longo da semana e agregam-se em 166 pares atleta-dia: 27 "
"no primeiro dia, 26 no segundo e no terceiro, 21 no quarto, 23 no quinto, 22 no sexto e 21 no sétimo. A "
"Tabela 1 reúne a descrição completa das sete variáveis. Três traços organizam a leitura.",
"Em primeiro lugar, a assimetria é acentuada nas subescalas negativas: a depressão apresenta assimetria de "
"3,80 e curtose de 17,66, e a confusão, 3,53 e 15,15. Em segundo lugar, a mediana coincide com o valor mínimo "
"da escala em duas subescalas — depressão e confusão — e situa-se a meio ponto dele na raiva, o que desloca a "
"informação para as caudas. Em terceiro lugar, a média aparada a vinte por cento afasta-se sistematicamente "
"da média aritmética nas mesmas subescalas: a depressão cai de 1,02 para 0,31 e a confusão, de 0,50 para "
"0,12. Nenhuma das sete variáveis passa no teste de Shapiro-Wilk ao nível de cinco por cento; o vigor é a que "
"mais se aproxima da normalidade (W = 0,983; p = 0,035) e a depressão a que mais dela se afasta (W = 0,522; "
"p < 0,001). Esse conjunto fundamenta a opção não paramétrica adotada na descrição.",
"O efeito de piso, apresentado na Tabela 2, ultrapassa com folga o limite de quinze por cento proposto por "
"Terwee et al. (2007) em quatro das seis subescalas: 65,7% das respostas de confusão, 52,4% das de depressão, "
"45,2% das de raiva e 40,4% das de tensão concentram-se no valor zero. O vigor e a fadiga escapam a essa "
"condição, com 4,8% e 6,0%. A consequência prática é direta: as quatro subescalas com piso severo possuem "
"margem para subir e quase nenhuma para descer, e qualquer interpretação de queda nessas dimensões deve "
"reconhecer a assimetria do instrumento.",
"A padronização contra a norma de atletas reposiciona o grupo. A fadiga situa-se em 57,7 e a raiva em 55,4, "
"ambas acima da média normativa; o vigor cai a 43,7, a confusão a 44,8 e a tensão a 41,6; a depressão "
"permanece sobre a linha da norma, em 50,5. O grupo, portanto, não exibe o perfil iceberg clássico: combina "
"baixa tensão e baixa confusão com fadiga e raiva elevadas e vigor rebaixado, configuração que se aproxima da "
"barbatana de tubarão descrita por Parsons-Smith, Terry e Machin (2017).",
"A confiabilidade das medidas repetidas ao longo da semana revela heterogeneidade expressiva. A depressão "
"apresenta a maior proporção de variância atribuível a diferenças estáveis entre atletas (CCI de medida única "
"de 0,766) e a raiva a menor (0,349). A leitura substantiva é que a raiva opera predominantemente como "
"estado, sensível à situação do dia, ao passo que a depressão se comporta como característica relativamente "
"estável do respondente. A mínima variação detectável acompanha essa lógica: 2,19 pontos para a confusão, "
"5,62 para a raiva e 14,44 para a perturbação total, valores que estabelecem o patamar abaixo do qual uma "
"mudança individual não se distingue do erro de medida.",
]
R2=[
"A Figura 4 acompanha as trajetórias das seis subescalas em escore T, com o dia sombreado conforme o "
"estímulo, e apresenta o resultado do teste de tendência. A Tabela 3 documenta os testes.",
"O teste L de Page, que especifica a alternativa como ordenada do primeiro ao sétimo dia e por isso ganha "
"potência sobre o de Friedman, identifica tendência monotônica em quatro variáveis. A fadiga cresce "
"(z = 2,86; p = 0,004), o vigor decresce (z = −2,84; p = 0,004), a tensão decresce (z = −2,59; p = 0,010) e a "
"confusão decresce (z = −2,52; p = 0,012). A raiva alcança significância marginal na direção decrescente "
"(z = −2,03; p = 0,043), resultado que exige cautela: a comparação direta entre o primeiro e o sétimo dia "
"mostra elevação de 0,74 ponto. A contradição é aparente e revela a limitação do teste quando a trajetória "
"não é monotônica — a raiva cai até o quinto dia e sobe abruptamente depois, de modo que a soma ponderada de "
"postos favorece a direção do trecho mais longo. Nem a depressão (z = −0,36; p = 0,718) nem a perturbação "
"total (z = 0,79; p = 0,428) apresentam tendência ordenada.",
"O teste de Friedman, restrito aos dezenove atletas com registro completo nos sete dias, rejeita a hipótese de "
"igualdade entre os dias para a confusão (χ² = 24,78; p < 0,001; W = 0,217), a fadiga (χ² = 13,52; p = 0,036; "
"W = 0,119) e o vigor (χ² = 12,90; p = 0,045; W = 0,113). A raiva fica no limiar (p = 0,087), a tensão não o "
"alcança (p = 0,111) e a depressão dele se afasta (p = 0,985). Os coeficientes de concordância são baixos: "
"mesmo a confusão explica pouco mais de um quinto da variância dos postos. Convém registrar que essa análise "
"descarta oito dos vinte e sete atletas, e que o segundo artigo desta série examina o custo dessa exigência.",
"O contraste direto entre a linha de base e a véspera da estreia, pelo teste de Wilcoxon sobre os vinte e um "
"atletas com as duas medidas, confirma dois deslocamentos que sobrevivem à correção de Holm para as seis "
"comparações com a linha de base: o vigor recua 3,06 pontos (p = 0,0007; p ajustado = 0,004; r = 0,743) e a "
"fadiga avança 3,38 pontos (p = 0,0016; p ajustado = 0,008; r = 0,691). A tensão recua 1,15 ponto e alcança "
"significância bruta (p = 0,012), que não resiste ao ajuste (p = 0,059). A confusão aproxima-se do limiar "
"(p = 0,068) e a perturbação total, apesar de crescer 5,21 pontos, não o alcança (p = 0,073), consequência da "
"dispersão elevada do composto.",
]
R3=[
"A Figura 5 decompõe cada série em três camadas sobrepostas: a série observada com o respectivo erro-padrão "
"diário, a série suavizada pelo filtro binomial e a banda do piso de ruído em torno do valor basal. A Tabela 4 "
"registra os parâmetros.",
"O piso de ruído varia de 0,21 ponto, na confusão, a 1,87 ponto, na perturbação total, e essa amplitude "
"justifica por si só o procedimento: uma variação de meio ponto significa coisas opostas nas duas variáveis. "
"Seis das sete séries superam o respectivo piso e recebem o veredito de sinal. O vigor desloca-se 2,98 pontos "
"contra um piso de 0,59, isto é, 5,1 vezes o piso; a fadiga, 3,62 contra 0,76, ou 4,8 vezes; a tensão, 1,21 "
"contra 0,35, ou 3,4 vezes; a perturbação total, 5,89 contra 1,87, ou 3,2 vezes; a confusão, 0,45 contra "
"0,21, ou 2,1 vezes; e a raiva, 0,74 contra 0,50, apenas 1,5 vez, o que a coloca próxima da fronteira do "
"critério. A depressão é a única série cuja variação total, de 0,21 ponto, permanece abaixo do piso de 0,45 e "
"recebe o veredito de ruído. Esse resultado converge com o teste de Friedman e com o de Page, que também nada "
"detectaram na depressão, e ilustra a utilidade do critério: onde os testes formais nada encontram, o piso de "
"ruído oferece uma explicação positiva, e não apenas a ausência de evidência.",
"As transições de choque concentram-se nas duas extremidades da semana. O vigor e a fadiga apresentam choque "
"na passagem do primeiro para o segundo dia e na passagem do sexto para o sétimo; a tensão e a confusão, "
"apenas na primeira dessas passagens; a raiva, nas duas últimas; e a perturbação total, somente na passagem "
"do sexto para o sétimo dia. A depressão não apresenta transição alguma que supere o piso. O padrão que "
"emerge é o de deslocamento por choques nas pontas, com platô intermediário, e não o de deriva lenta e "
"uniforme. Os pontos de inflexão reforçam essa leitura: situam-se entre o terceiro e o quinto dia na maioria "
"das variáveis — 3,86 no vigor, 3,77 na fadiga, 3,53 na perturbação total, 4,54 na tensão e 5,07 na "
"confusão —, o que localiza no miolo da semana a mudança de regime da aceleração.",
]
R4=[
"A Figura 6 expressa as duas derivadas em unidades do piso de ruído de cada variável, o que permite "
"compará-las apesar das diferenças de amplitude e dispersão. A moldura destaca as células cujo valor absoluto "
"supera uma unidade de piso.",
"A primeira derivada mostra que a velocidade se concentra em duas colunas. Na passagem do primeiro para o "
"segundo dia, o vigor cai 2,23 pisos, a confusão cai 1,87, a tensão cai 1,50 e a fadiga sobe 1,46. Na "
"passagem do sexto para o sétimo dia, a raiva sobe 1,86 pisos, a fadiga sobe 1,85, a perturbação total sobe "
"1,78 e o vigor cai 1,72. Entre "
"esses dois extremos, quase todas as velocidades permanecem abaixo de uma unidade de piso, o que confirma o "
"platô. Os dois choques têm naturezas distintas: o primeiro decorre da transição de um dia de carga mínima "
"para o primeiro dia de treino intervalado e afeta simultaneamente o vigor, a tensão e a confusão; o segundo "
"antecede a estreia competitiva e mobiliza a raiva e a fadiga, sem repercussão equivalente sobre a tensão, "
"que continua a cair.",
"A segunda derivada localiza onde o movimento muda de ritmo. O vigor acelera 1,34 piso no segundo dia, o que "
"significa que a queda perde velocidade logo após o choque inicial: a aceleração de sinal contrário atua como "
"freio sobre um deslocamento negativo. No sexto dia o sinal se inverte e o vigor desacelera 1,34 piso, o que "
"antecipa a queda final. A raiva acelera 1,43 piso no quinto dia e a fadiga 1,24 no sexto, ambas com sinal "
"concordante com o deslocamento, isto é, o movimento ganha ritmo. A leitura conjunta das duas derivadas sugere que o microciclo "
"não produz deterioração contínua, e sim dois eventos discretos separados por um período de estabilidade "
"relativa.",
]
R5=[
"A Figura 7 aplica o mesmo tratamento às séries de prevalência dos seis perfis, e a Tabela 5 registra as "
"prevalências diárias e o teste de estabilidade.",
"A distribuição geral dos 166 pares atribui 32,5% ao iceberg, 26,5% à barbatana de tubarão, 18,7% ao "
"submerso, 10,8% ao iceberg invertido, 10,2% à superfície e 1,2% ao Everest invertido. O contraste com a "
"referência de Parsons-Smith, Terry e Machin (2017) é informativo: a barbatana de tubarão comparece com mais "
"que o dobro da prevalência de referência (26,5% contra 11,6%) e o submerso com pouco mais da metade (18,7% "
"contra 30,6%). A amostra não reproduz a distribuição populacional do estudo original, resultado esperado em "
"um grupo submetido a carga elevada e proximidade competitiva.",
"A trajetória diária revela dois movimentos de sentido oposto e magnitude comparável. O iceberg recua de "
"37,0% no primeiro dia para 19,0% no sétimo, deslocamento de 18,0 pontos percentuais contra um piso de 9,5. A "
"barbatana de tubarão avança de 11,1% para 28,6%, deslocamento de 17,5 pontos contra um piso de 9,0. A faixa "
"de risco, que agrega três perfis, sobe de 22,2% para 52,4%, deslocamento de 30,2 pontos contra um piso de "
"9,8 — o maior da série. A superfície recua 13,8 pontos contra um piso de 5,9 e o iceberg invertido avança "
"7,9 contra 6,2. O submerso oscila abaixo do respectivo piso e recebe o veredito de ruído. O Everest "
"invertido, cujo deslocamento nominalmente supera o piso, envolve dois pares atleta-dia no conjunto inteiro; "
"o piso binomial, calculado sobre proporções próximas de zero, encolhe a ponto de deixar de discriminar, e "
"por isso a figura o assinala como não avaliável.",
"O teste Q de Cochran, aplicado aos dezenove atletas com registro completo, não rejeita a hipótese de "
"estabilidade para nenhum dos seis perfis nem para a faixa de risco; os valores de p variam de 0,085, no "
"submerso, a 0,655, na barbatana de tubarão. Esse resultado exige comentário explícito, pois aparentemente "
"contradiz o veredito de sinal descrito acima. As duas análises, porém, respondem a perguntas diferentes e "
"operam sobre conjuntos diferentes. O critério do piso de ruído avalia a série agregada de todos os pares "
"disponíveis e pergunta se o deslocamento excede a oscilação amostral típica; o Q de Cochran avalia dezenove "
"trajetórias individuais completas e pergunta se a probabilidade de pertencer a um perfil difere entre os "
"dias. A perda de trinta por cento dos atletas e a natureza binária do desfecho reduzem drasticamente a "
"potência do segundo teste. A conclusão prudente é que o deslocamento agregado do iceberg para a barbatana de "
"tubarão é consistente e de magnitude relevante, porém não confirmado por teste formal na subamostra completa.",
]
R6=[
"A Figura 9 acompanha o custo do dia e a migração intradiária, e a Tabela 6 registra os testes.",
"Considerados em conjunto os 119 pares completos de manhã e tarde ou noite, a migração para a faixa de risco "
"é inequívoca: vinte e quatro pares entram nessa faixa ao longo do dia e apenas oito saem dela (χ² = 7,03; "
"p = 0,008). O dia de treino, qualquer que seja o conteúdo, desloca o grupo na direção do risco.",
"A resposta aguda por tipo de estímulo distingue dois padrões. Nos dias de treino intervalado, a fadiga sobe "
"2,02 pontos (r = 0,524; p < 0,001), a perturbação total sobe 4,15 (r = 0,521; p < 0,001), o vigor cai 1,20 "
"(r = 0,379; p = 0,004) e a tensão sobe 0,44 (r = 0,297; p = 0,023). Nos dias de conteúdo técnico e de força, "
"registra-se a maior perturbação aguda de toda a semana: a perturbação total sobe 6,90 pontos (r = 0,662; "
"p = 0,003), o vigor cai 2,30 (r = 0,637; p = 0,004), a raiva sobe 1,65 (r = 0,599; p = 0,007) e a depressão "
"sobe 1,05 (r = 0,571; p = 0,011). Nos dias de amistoso, apenas a confusão se move, e para baixo (−0,33; "
"r = 0,350; p = 0,027). O dia sem estímulo intervalado e sem jogo produz, portanto, o maior deslocamento "
"afetivo intradiário do microciclo.",
"A decomposição da migração por tipo de estímulo enfraquece o resultado. Nos dias de treino intervalado, "
"quatorze pares entram na faixa de risco e quatro saem (χ² = 4,50; p = 0,034), valor que não sobrevive à "
"correção de Holm para três comparações (p ajustado = 0,102). Nos dias de amistoso, sete entram e três saem "
"(p = 0,343); nos de conteúdo técnico e de força, três entram e um sai (p = 0,617). A razão entre entradas e "
"saídas é próxima de três para um nos três estímulos, e o que varia é o número de pares disponível em cada "
"categoria. Esse detalhe é decisivo: a diferença entre os valores de p reflete tamanho de amostra, não "
"intensidade de efeito.",
"A classificação categórica, por sua vez, não distingue os estímulos. A distribuição dos seis perfis não "
"difere entre os tipos de dia (χ² = 6,06; gl = 10; p = 0,810), e tampouco difere a composição das três faixas "
"(χ² = 3,66; gl = 4; p = 0,455). Os níveis médios das variáveis contínuas, comparados entre os três tipos de "
"dia nos vinte e dois atletas com registro nos três, apontam diferença apenas na raiva (χ² = 7,82; p = 0,020); "
"as demais variáveis não alcançam o limiar. Uma advertência de delineamento condiciona toda esta seção: os "
"tipos de estímulo não foram distribuídos ao acaso, de modo que o tipo de dia se confunde com a posição no "
"microciclo e com a carga acumulada. O dia de conteúdo técnico e de força é o penúltimo da semana e sucede "
"vinte horas e meia de trabalho; a maior perturbação nele observada admite tanto a leitura de resposta ao "
"estímulo quanto a de efeito cumulativo, e o presente desenho não separa as duas.",
]
R7=[
"A Figura 8 aplica o teste formal de cruzamento e ilustra a diferença entre uma troca de posição aparente e "
"uma inversão estabelecida.",
"O par formado pelo vigor e pela fadiga cruza-se uma única vez, na abscissa 5,21, com limiar combinado de "
"0,96 ponto. A diferença entre as duas séries é de 3,65 pontos no primeiro dia, favorável ao vigor, e de "
"−2,94 pontos no sétimo, favorável à fadiga; ambos os valores superam o limiar, e a inversão é declarada "
"estabelecida. O resultado tem significado prático imediato: em algum ponto do quinto dia o grupo deixa de "
"ser predominantemente vigoroso e passa a ser predominantemente fatigado, e essa troca não se explica por "
"oscilação amostral. Dois outros pares recebem o mesmo veredito: vigor e perturbação total cruzam-se em 6,12 "
"e vigor e fadiga física em 2,60.",
"O par formado pela tensão e pela raiva recebe veredito distinto. As duas séries trocam de posição três "
"vezes, nas abscissas 1,90, 3,91 e 5,33, com limiar combinado de 0,61 ponto; a diferença parte de 0,37 ponto "
"no primeiro dia, valor inferior ao limiar. O procedimento classifica o achado como divergência e recusa-lhe "
"o estatuto de inversão estabelecida, ainda que a separação final, de −1,58 ponto, ultrapasse o limiar. O "
"mesmo ocorre com o par formado pela fadiga física e pela fadiga mental.",
"A faixa favorável e a faixa de risco fornecem o cruzamento de maior amplitude do estudo. Elas partem "
"separadas por 14,8 pontos percentuais em favor da favorável e terminam separadas por 33,3 em favor da de "
"risco, com um único cruzamento, na abscissa 1,88. O limiar combinado é de 13,7 pontos percentuais, e ambas "
"as separações o superam: a inversão é declarada estabelecida. O grupo, portanto, troca de regime já no "
"segundo dia da semana — antes, e de modo mais nítido, do que a inversão entre vigor e fadiga, que só ocorre "
"no quinto. A faixa agrega três perfis e por isso responde antes que qualquer subescala isolada.",
]

DISCUSSAO=[
("A forma da semana: dois choques e um platô",[
 "O primeiro resultado a discutir não é um valor, e sim uma forma. A deterioração do humor ao longo do "
 "microciclo terminal não se distribui de modo uniforme: concentra-se em duas transições e deixa entre elas um "
 "período de estabilidade relativa. As derivadas expressas em unidades do piso de ruído tornam essa forma "
 "visível de maneira que a comparação entre médias diárias jamais permitiria. Na passagem do dia basal para o "
 "primeiro dia de treino intervalado, quatro variáveis se movem acima do piso; na passagem do penúltimo para o "
 "último dia, quatro também; nos quatro dias intermediários, quase nenhuma o faz.",
 "Essa geometria contraria a intuição de acúmulo linear que costuma orientar a leitura de séries de "
 "monitoramento. Se a carga se soma dia após dia, e ela de fato se soma — de 1,5 hora para 23,0 horas ao longo "
 "da semana —, seria razoável esperar deterioração proporcional. O que se observa aproxima-se mais de um "
 "sistema com histerese: resiste até certo ponto, cede de uma vez e depois se estabiliza em novo patamar. "
 "Meeusen et al. (2013) descreveram o continuum entre sobrecarga funcional, sobrecarga não funcional e "
 "supertreinamento em termos de patamares, e não de gradientes; os dados aqui apresentados oferecem, em escala "
 "diária, uma imagem compatível com essa descrição.",
 "O segundo choque tem interpretação distinta do primeiro. Ocorre na véspera da estreia e mobiliza a raiva e a "
 "fadiga sem repercussão equivalente sobre a tensão, que continua a cair. A antecipação competitiva, nesse "
 "grupo, não se traduz em tensão autorrelatada. Gentile et al. (2021) observaram, em contexto de campeonato "
 "mundial, perfis psicológicos que também não replicavam o padrão ansioso esperado, e Bird et al. (2025) "
 "documentaram dissociação semelhante entre marcadores de bem-estar e de ativação. A convergência sugere que "
 "atletas de alto rendimento reconhecem e nomeiam a fadiga com facilidade maior do que a tensão."]),
("Sinal e ruído: uma exigência anterior à interpretação",[
 "A contribuição metodológica deste estudo consiste em tornar explícito um compromisso que a literatura de "
 "monitoramento costuma manter tácito. Antes de examinar uma série, o analista precisa declarar qual magnitude "
 "de variação considerará digna de leitura. Sem essa declaração prévia, a interpretação torna-se refém do que "
 "se observa: sobe-se um degrau e chama-se de tendência; desce-se outro e chama-se de recuperação. O piso de "
 "ruído oferece uma resposta operacional, e a sua virtude não está na sofisticação, que é nenhuma, e sim na "
 "anterioridade.",
 "A literatura psicométrica já reconhece o princípio quando exige a mínima variação detectável para "
 "interpretar mudanças individuais (TERWEE et al., 2007), e os documentos de consenso recomendam critérios "
 "equivalentes (SAW; MAIN; GASTIN, 2016; KELLMANN et al., 2018). O que raramente se faz é transportar o mesmo "
 "cuidado para as séries agregadas do grupo, precisamente onde a tentação narrativa é maior, porque a série do "
 "grupo parece mais estável do que a do indivíduo. Ela é mais estável, de fato; mas o número de respondentes "
 "que a sustenta varia de dia para dia, e essa variação produz oscilação que nada deve à carga.",
 "A aplicação do critério produziu três consequências que ilustram a sua utilidade. Explicou a imobilidade da "
 "depressão em termos positivos: a variação de 0,21 ponto é menor do que a oscilação amostral típica de 0,45, "
 "e não apenas ausência de evidência de mudança. Recusou o estatuto de inversão à troca de posição entre "
 "tensão e raiva, que uma leitura desatenta teria celebrado. E expôs a própria fragilidade em prevalências "
 "próximas de zero, onde o erro-padrão binomial encolhe e o critério se torna permissivo — limitação que o "
 "texto assinala em vez de ocultar.",
 "Há, nessa discussão, uma dimensão que ultrapassa a técnica. Uma série de sete pontos comporta muitas "
 "narrativas, e a escolha entre elas raramente decorre dos dados. O piso de ruído funciona como um compromisso "
 "que o analista assume consigo mesmo antes de olhar, e o seu valor epistemológico reside exatamente aí: "
 "restringe o espaço de histórias que os mesmos números autorizam. Nenhum critério elimina o julgamento; o que "
 "um critério explícito faz é torná-lo auditável."]),
("A unidade de análise como fonte silenciosa de divergência",[
 "A auditoria que precedeu este estudo revelou algo que merece registro na literatura, e não apenas no "
 "apêndice metodológico. Sete versões anteriores deste conjunto de dados chegaram a valores divergentes para a "
 "mesma quantidade — a variação da prevalência do perfil iceberg entre o primeiro e o último dia — e a causa "
 "não foi erro de cálculo em nenhuma delas. Foi a escolha, nunca declarada, de qual observação conta como uma "
 "unidade.",
 "Sobre exatamente os mesmos registros e com a mesma classificação, a variação vai de 0,6 ponto percentual, "
 "quando se conta cada registro do primeiro e do último momento do dia, a 18,0 pontos, quando se conta um "
 "valor por atleta e por dia. A diferença não é sutil: uma leitura sugere estabilidade e a outra, "
 "deterioração acentuada. O mecanismo é simples: as unidades ponderam os atletas de maneira distinta. Quem "
 "respondeu seis vezes num dia pesa seis vezes na contagem por registro e uma vez na contagem por par "
 "atleta-dia; e como a assiduidade não é aleatória, a ponderação carrega informação sobre quem responde, não "
 "apenas sobre o que se sente.",
 "A recomendação que decorre é modesta e exigente ao mesmo tempo: declarar a unidade de análise antes de "
 "reportar qualquer prevalência longitudinal, e reportar a sensibilidade do achado à escolha. Estudos que "
 "acompanham perfis de humor ao longo do tempo em amostras pequenas são particularmente vulneráveis, porque "
 "poucos atletas muito assíduos podem determinar a série inteira."]),
("Implicações para o monitoramento no handebol de elite",[
 "O levantamento de Henze et al. (2025) revelou que a prática de monitoramento em clubes profissionais de "
 "handebol privilegia indicadores de carga externa, apesar da evidência de que medidas subjetivas superam "
 "medidas objetivas na detecção de respostas ao treino (SAW; MAIN; GASTIN, 2016). Os presentes resultados "
 "acrescentam três recomendações operacionais.",
 "A primeira diz respeito à frequência. A migração intradiária para a faixa de risco, com vinte e quatro "
 "entradas contra oito saídas, só se torna visível porque houve duas coletas diárias. Um protocolo com coleta "
 "única perderia integralmente esse fenômeno, e a escolha entre a medida matinal e a vespertina produziria "
 "retratos substancialmente distintos do mesmo dia. A segunda diz respeito ao critério: nenhuma série de "
 "monitoramento deve ser lida sem uma declaração prévia da magnitude que se considerará relevante, e o cálculo "
 "do piso exige apenas o desvio-padrão e o número de respondentes de cada dia. A terceira diz respeito ao "
 "nível de agregação: o perfil comunica bem e detecta mal, ao passo que a variável contínua detecta bem e "
 "comunica mal; o uso conjunto dos dois planos, e não a escolha entre eles, é o que os dados recomendam.",
 "Convém situar essas recomendações no contexto de risco da modalidade. Rafnsson et al. (2021) associaram "
 "carga e problemas por uso excessivo na pré-temporada do handebol, e Bjørndal et al. (2021) verificaram que "
 "picos de carga precedem problemas de saúde. Büchel, Döring e Baumeister (2026) demonstraram que a carga se "
 "distribui de modo desigual entre atletas do mesmo elenco. Se o humor funciona como sentinela precoce, "
 "conforme sustentam os documentos de consenso (MEEUSEN et al., 2013; KELLMANN et al., 2018), a leitura diária "
 "do perfil oferece uma via de baixo custo para identificar, entre atletas submetidos à mesma programação, "
 "aqueles que respondem de modo desproporcional. Rohlfs et al. (2025) reforçaram essa via ao associar estados "
 "de humor à condição de lesão em atletas brasileiros de alto rendimento."]),
]

LIMITACOES=[
"A primeira limitação é de delineamento. Os tipos de estímulo não foram distribuídos ao acaso ao longo da "
"semana, de modo que o tipo de dia se confunde com a posição no microciclo e com a carga acumulada. O dia de "
"conteúdo técnico e de força ocorreu uma única vez e ocupou o penúltimo lugar da sequência; toda inferência "
"sobre a especificidade desse estímulo permanece provisória.",
"A segunda é de tamanho de amostra. Vinte e sete atletas de um único elenco geram entre vinte e um e vinte e "
"sete pares por dia, número que sustenta a descrição mas restringe severamente a potência dos testes "
"categóricos. O Q de Cochran, aplicado aos dezenove atletas com registro completo, não rejeitou a hipótese de "
"estabilidade para nenhum perfil, e essa ausência de rejeição deve ser lida como limitação de potência, e não "
"como evidência de estabilidade.",
"A terceira decorre das propriedades do instrumento nesta amostra. Quatro das seis subescalas apresentam "
"efeito de piso acima do critério de Terwee et al. (2007), o que compromete a capacidade de detectar melhora "
"e introduz assimetria em toda comparação.",
"A quarta refere-se ao piso de ruído em séries de prevalência baixa. O erro-padrão binomial encolhe quando a "
"proporção se aproxima de zero, o que rebaixa o piso e torna o critério permissivo. O caso do Everest "
"invertido, com dois pares no conjunto inteiro, ilustra a condição e foi assinalado como não avaliável.",
"A quinta diz respeito à janela de coleta do sétimo dia. Todos os registros desse dia ocorreram entre oito e "
"quatorze horas, de modo que a medida tomada como pós corresponde ao início da tarde e não à noite. O custo "
"do último dia é, portanto, subestimado em relação aos demais.",
"A sexta é de generalização. O estudo acompanhou uma única equipe masculina de primeira divisão em uma única "
"semana de uma única temporada. A replicação em equipes femininas, em outras fases do calendário e em outros "
"níveis competitivos permanece necessária, e a comparação com outras modalidades coletivas exigirá cautela "
"dada a especificidade das demandas do handebol (KARCHER; BUCHHEIT, 2014; GARCÍA-SÁNCHEZ et al., 2023).",
"A sétima é a ausência de desfechos externos. O estudo não registrou desempenho objetivo, marcadores "
"fisiológicos nem incidência de lesão no período, o que impede verificar se os deslocamentos afetivos "
"observados anteciparam qualquer consequência prática.",
]

CONCLUSAO=[
"O humor de atletas de handebol de elite deteriorou-se de modo consistente ao longo da última semana de "
"pré-temporada. O vigor recuou 2,98 pontos e a fadiga avançou 3,62, ambos muito acima do respectivo piso de "
"ruído, com tendência monotônica confirmada pelo teste de Page. O perfil iceberg recuou de 37,0% para 19,0% "
"dos pares atleta-dia e a faixa de risco avançou de 22,2% para 52,4%. A deterioração, contudo, não se "
"distribuiu de modo uniforme: concentrou-se em duas transições, a primeira na saída do dia basal e a segunda "
"na véspera da estreia, e deixou entre elas um platô de quatro dias.",
"O tratamento de séries proposto — filtro binomial, derivadas de primeira e segunda ordem expressas em "
"unidades de ruído e teste formal de cruzamento — mostrou-se útil em três frentes: localizou as transições de "
"choque e os pontos de inflexão que a comparação entre médias diárias não revela; explicou a imobilidade da "
"depressão em termos positivos; e separou, entre as trocas de posição observadas, as três que constituem "
"inversão estabelecida das duas que permanecem no terreno da divergência. Recomenda-se a sua adoção como "
"etapa prévia à interpretação de qualquer série curta de monitoramento psicológico.",
"A auditoria que precedeu o estudo acrescentou um achado de alcance mais amplo. As divergências entre versões "
"anteriores deste conjunto de dados não decorreram de erro de cálculo, e sim da escolha não declarada da "
"unidade de análise: sobre os mesmos registros, a variação do perfil iceberg entre o primeiro e o último dia "
"vai de 0,6 a 18,0 pontos percentuais conforme quem conte como uma observação. Declarar a unidade antes de "
"reportar prevalências longitudinais deixa de ser preciosismo e passa a ser condição de comparabilidade.",
"Duas orientações práticas encerram o estudo. A comissão técnica que acompanha um elenco na semana anterior à "
"estreia deve concentrar atenção nas duas transições identificadas, e não distribuí-la uniformemente pela "
"semana. E deve manter as duas coletas diárias: a migração para a faixa de risco dentro do próprio dia é o "
"fenômeno mais robusto observado, e uma coleta única o tornaria invisível.",
]
