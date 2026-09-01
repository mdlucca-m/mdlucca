# -*- coding: utf-8 -*-
"""Artigo de inovação: limites, derivadas e piso de ruído aplicados aos perfis de humor."""

TITULO=("Limites, derivadas e piso de ruído aplicados aos perfis de humor: comportamento das dimensões "
        "do BRUMS e resposta a estímulos distintos na última semana de pré-temporada de atletas de "
        "handebol de elite")
SUB=("Estudo observacional longitudinal com coletas diárias pré e pós, comparação com linha de base e "
     "tratamento de séries por suavização, derivadas e limiar de ruído")

RESUMO=(
"A literatura sobre perfis de humor no esporte descreve prevalências em corte transversal e raramente "
"acompanha o mesmo atleta ao longo de um microciclo. Duas lacunas persistem: não se sabe como os seis "
"perfis identificados por Parsons-Smith, Terry e Machin se movimentam de um dia para o outro nem como "
"distinguir uma variação real de uma flutuação amostral. Este estudo descreveu o comportamento das "
"variáveis do BRUMS ao longo da última semana de pré-temporada de atletas de handebol de elite, examinou "
"a resposta dos seis perfis a estímulos distintos e propôs um tratamento de série que combina suavização, "
"derivadas e um limiar explícito de ruído. Vinte e sete atletas masculinos de primeira divisão nacional "
"responderam ao instrumento durante sete dias; o primeiro dia teve coleta única noturna, tomada como linha "
"de base, e os seis dias seguintes tiveram coleta matinal e noturna. O conjunto reuniu 166 pares atleta-dia "
"e 120 pares pré e pós. Cada série diária recebeu um filtro binomial de três pontos, e o piso de ruído foi "
"definido como a média dos erros-padrão diários; declarou-se variação real apenas quando o deslocamento "
"total superou esse piso. As primeiras e segundas derivadas da série suavizada, expressas em unidades do "
"piso, localizaram as transições de choque e os pontos de inflexão. O vigor caiu 3,12 pontos e a fadiga "
"subiu 3,49, ambos acima do respectivo piso, com tendência monotônica confirmada pelo teste L de Page. A "
"depressão foi a única subescala cuja variação não superou o piso. O perfil iceberg recuou de 37,0% para "
"19,0% e a barbatana de tubarão avançou de 11,1% para 28,6%. A distribuição dos perfis, contudo, não "
"diferiu entre os tipos de estímulo, e apenas a migração intradiária nos dias de treino intervalado "
"alcançou significância bruta, que não resistiu à correção de Holm. O teste formal de cruzamento "
"reconheceu inversão estabelecida entre vigor e fadiga no quinto dia, mas recusou a inversão aparente "
"entre a faixa favorável e a faixa de risco. Conclui-se que a deterioração do humor ao longo da semana é "
"robusta e progressiva, ao passo que a atribuição dessa deterioração a um tipo particular de estímulo não "
"se sustenta neste tamanho de amostra."
)
PALAVRAS=("perfis de humor; handebol; Escala de Humor de Brunel; monitoramento do atleta; séries temporais; "
          "estatística não paramétrica")

ABSTRACT=(
"Research on mood profiles in sport reports cross-sectional prevalences and rarely follows the same athlete "
"across a microcycle. Two gaps persist: how the six profiles identified by Parsons-Smith, Terry and Machin "
"move from one day to the next, and how to separate a real change from sampling fluctuation. This study "
"described the behaviour of BRUMS variables across the final pre-season week of elite handball players, "
"examined how the six profiles responded to different stimuli, and proposed a series treatment that combines "
"smoothing, derivatives and an explicit noise threshold. Twenty-seven male first-division players completed "
"the instrument over seven days; day one had a single evening assessment, taken as baseline, and the six "
"following days had a morning and an evening assessment. The dataset comprised 166 athlete-day pairs and 120 "
"pre-post pairs. Each daily series received a three-point binomial filter, and the noise floor was defined as "
"the mean of the daily standard errors; a real change was declared only when the total displacement exceeded "
"that floor. First and second derivatives of the smoothed series, expressed in floor units, located shock "
"transitions and inflection points. Vigour fell by 3.12 points and fatigue rose by 3.49, both above their "
"respective floors, with a monotonic trend confirmed by Page's L test. Depression was the only subscale whose "
"variation did not exceed the floor. The iceberg profile retreated from 37.0% to 19.0% and the shark fin "
"advanced from 11.1% to 28.6%. Profile distribution, however, did not differ across stimulus types, and only "
"within-day migration on interval training days reached raw significance, which did not survive Holm "
"correction. The formal crossing test recognised an established inversion between vigour and fatigue on day "
"five but rejected the apparent inversion between the favourable and the risk bands. Mood deterioration "
"across the week is robust and progressive, whereas attributing that deterioration to a particular stimulus "
"type is not supported at this sample size."
)
KEYWORDS=("mood profiles; handball; Brunel Mood Scale; athlete monitoring; time series; nonparametric statistics")

INTRO=[
"O reconhecimento de que o estado afetivo informa sobre a condição de treino de um atleta antecede em "
"décadas o instrumental que hoje o mede. Morgan (1985) propôs um modelo de saúde mental no qual o bem-estar "
"psicológico acompanha o êxito esportivo e a psicopatologia acompanha o fracasso; a representação gráfica "
"desse bem-estar, com o vigor acima da média normativa e as cinco dimensões negativas abaixo dela, recebeu "
"o nome de perfil iceberg (MORGAN, 1980). O Profile of Mood States sustentou essa tradição durante quase "
"trinta anos até que Terry et al. (1999) derivassem dele uma versão breve de vinte e quatro itens, a Escala "
"de Humor de Brunel, validada em seguida para amostras atléticas com valores normativos próprios (TERRY; "
"LANE, 2000) e adaptada ao português por Rohlfs et al. (2008), com estudos psicométricos posteriores que "
"ampliaram a evidência de validade em atletas brasileiros (ROHLFS et al., 2023).",

"A força do iceberg como imagem, porém, converteu-se em limitação analítica. Ao reduzir um vetor de seis "
"dimensões a um rótulo binário — o atleta tem ou não tem o perfil desejável —, a literatura descartou a "
"informação contida nas configurações intermediárias. Parsons-Smith, Terry e Machin (2017) romperam esse "
"impasse com uma classificação por agrupamento que identificou seis configurações recorrentes: além do "
"iceberg, a superfície, o submerso, a barbatana de tubarão, o iceberg invertido e o Everest invertido. A "
"proposta encontrou replicação em contextos culturais diversos (HAN; PARSONS-SMITH; TERRY, 2020; TERRY et "
"al., 2022; LEW et al., 2023; TERRY; PARSONS-SMITH; VLACHOPOULOS, 2024) e chegou ao Brasil pela mão de "
"Rohlfs, Noce e Wilke (2024), que estimaram a prevalência dos seis agrupamentos em atletas de um clube de "
"alto rendimento. Terry e Parsons-Smith (2021) situaram esse instrumental no debate mais amplo sobre saúde "
"mental sustentável no esporte.",

"Persiste, contudo, uma assimetria entre o que a classificação promete e o uso que dela se faz. Os seis "
"perfis descrevem estados, não traços; entretanto, quase toda a evidência disponível provém de medidas "
"únicas, em corte transversal, que estimam prevalências populacionais sem acompanhar o mesmo atleta ao "
"longo do tempo. Luojumäki et al. (2026) exploraram a distribuição dos agrupamentos por nível de atividade, "
"gênero e idade e, ainda assim, permaneceram no plano transversal. O resultado dessa assimetria é que se "
"conhece a frequência dos perfis em uma população e se ignora a dinâmica deles em um indivíduo submetido a "
"cargas sucessivas. Falta, em síntese, saber se um perfil migra, com que velocidade migra e sob qual "
"estímulo migra.",

"O handebol oferece um cenário exigente para essa investigação. A modalidade combina deslocamentos de alta "
"intensidade, mudanças frequentes de direção, saltos, arremessos e contato físico permanente, com demandas "
"que variam de modo acentuado conforme a posição em quadra (KARCHER; BUCHHEIT, 2014) e conforme o esquema "
"defensivo adotado (SAAL; RHEINSBERG; BAUMGART, 2026). Revisões sistemáticas das exigências físicas em "
"competição oficial confirmam esse perfil intermitente e de alta densidade (GARCÍA-SÁNCHEZ et al., 2023; "
"PEREZ ARMENDARIZ; SPYROU; ALCARÁZ, 2024). A pré-temporada agrava o quadro: Rafnsson et al. (2021) "
"documentaram associação entre carga e problemas por uso excessivo justamente nesse período, e Bjørndal et "
"al. (2021) observaram, ao longo de uma temporada completa, que os picos de carga precedem os problemas de "
"saúde. A carga, ademais, distribui-se de maneira desigual entre atletas do mesmo elenco (BÜCHEL; DÖRING; "
"BAUMEISTER, 2026), o que reforça a necessidade de monitoramento individual. O levantamento de Henze et al. "
"(2025) revelou que a prática de monitoramento em clubes profissionais de handebol ainda privilegia "
"indicadores externos, apesar da evidência de que medidas subjetivas superam medidas objetivas na detecção "
"de respostas agudas e crônicas ao treino (SAW; MAIN; GASTIN, 2016).",

"A relação entre humor e rendimento esportivo foi submetida a duas metanálises que convergem em um ponto "
"central: o efeito existe, é consistente e é de magnitude modesta (BEEDIE; TERRY; LANE, 2000; LOCHBAUM et "
"al., 2021). O valor prático do instrumento, por isso, reside menos na predição de desempenho e mais na "
"vigilância do estado de recuperação. Os documentos de consenso sobre supertreinamento e sobre recuperação "
"atribuem ao humor papel de sentinela precoce (MEEUSEN et al., 2013; KELLMANN et al., 2018), e essa "
"vigilância articula-se com o sono e com o estresse percebido. Ferreira et al. (2023) demonstraram que "
"magnitudes distintas de carga alteram o padrão de sono e o estado de humor de jovens futebolistas; Sawczuk "
"et al. (2021) e Costa, Figueiredo e Nakamura (2022) detalharam a influência do sono percebido sobre o "
"bem-estar do atleta; McFadden et al. (2021) acompanharam as mudanças psicológicas e fisiológicas ao longo "
"de uma temporada universitária; Bird et al. (2025) reuniram humor, sono e desempenho em uma seleção "
"nacional de basquetebol durante competição internacional; e Rohlfs et al. (2025) associaram estados de "
"humor à condição de lesão e ao desempenho no salto com contramovimento. Reynoso-Sánchez et al. (2021) e "
"Gentile et al. (2021) acrescentaram evidência sobre a relação entre recuperação, estresse e humor em "
"contextos competitivos distintos.",

"Resta um problema metodológico anterior a todos esses, e ele é silencioso. Séries curtas de medidas "
"psicométricas oscilam por razões que nada devem à carga: variação amostral entre dias, ausências, "
"arredondamento em escalas de amplitude estreita. Quando se comparam prevalências diárias sem um critério "
"de decisão, qualquer subida ou descida ganha estatuto de achado. A literatura de monitoramento do atleta "
"reconhece esse risco quando exige a mínima mudança detectável para escores individuais (TERWEE et al., "
"2007), porém raramente transporta o mesmo cuidado para as séries agregadas do grupo. Não se localizou, na "
"literatura consultada, estudo que aplicasse ao acompanhamento diário dos seis perfis de humor um "
"tratamento de série que reunisse suavização, derivadas de primeira e segunda ordem e um limiar explícito "
"de ruído contra o qual toda variação fosse contrastada.",

"Essas lacunas justificam o presente estudo. De um lado, o handebol de elite impõe, na semana que antecede "
"a estreia competitiva, uma sucessão de estímulos heterogêneos — treino intervalado de alta intensidade, "
"jogos amistosos e sessões de conteúdo técnico e de força — cuja repercussão afetiva permanece "
"indocumentada em escala diária. De outro, o instrumental disponível para descrever essa repercussão carece "
"de um critério que separe sinal de ruído. A conjunção dos dois problemas define o objetivo geral desta "
"investigação: descrever o comportamento das variáveis do BRUMS e a resposta dos seis perfis de humor ao "
"longo da última semana de pré-temporada de atletas de handebol de elite, com comparação diária entre a "
"manhã e a noite e contraste permanente com a linha de base, por meio de um tratamento de séries que "
"combina suavização, análise de derivadas, limiar de ruído e teste formal de cruzamento entre trajetórias.",
]

METODO=[
("Delineamento e contexto",[
 "Trata-se de estudo observacional longitudinal de medidas repetidas, com sete dias consecutivos de "
 "acompanhamento e delineamento intraindividual. O período corresponde ao microciclo terminal da "
 "pré-temporada, isto é, à semana imediatamente anterior à estreia da equipe na competição oficial. A "
 "escolha desse recorte não é acidental: nele coexistem a carga acumulada de toda a preparação e a "
 "proximidade psicológica da estreia, condição que maximiza a chance de observar deslocamentos do estado "
 "afetivo. Nenhuma intervenção foi introduzida pelos pesquisadores; a programação do treino permaneceu "
 "sob responsabilidade exclusiva da comissão técnica, e o estudo limitou-se a registrar o que ocorreu.",
 "A semana reuniu quatro tipos de estímulo. O primeiro dia contemplou apenas uma sessão de conteúdo "
 "técnico e tático, com uma hora e meia de duração, e serviu de linha de base. O segundo, o quarto e o "
 "sétimo dias combinaram treino intervalado de alta intensidade com trabalho técnico e tático. O terceiro "
 "e o quinto dias incluíram jogo amistoso. O sexto dia concentrou conteúdo técnico, tático e de força, sem "
 "estímulo intervalado nem jogo. A carga acumulada progrediu de 1,5 hora no primeiro dia para 23,0 horas "
 "ao término do sétimo."]),
("Participantes",[
 "Participaram vinte e sete atletas de handebol masculino de uma equipe da primeira divisão nacional, com "
 "idade média de 21,96 anos e desvio-padrão de 3,81 anos. Todos integravam o elenco principal e cumpriam a "
 "programação regular de pré-temporada. Adotaram-se como critérios de inclusão o vínculo formal com a "
 "equipe e a participação nas sessões da semana; excluíram-se atletas em processo de reabilitação que os "
 "afastasse do treino coletivo. A perda de observações ao longo da semana decorreu de ausências pontuais "
 "às sessões e de não devolução de instrumento em algum dos dois momentos do dia, o que reduziu o número "
 "de respondentes de vinte e sete no primeiro dia para vinte e um no sétimo."]),
("Procedimento de coleta",[
 "O contato inicial com a comissão técnica ocorreu três meses antes do início da coleta, em reunião na "
 "qual se apresentaram os objetivos, o instrumento e a carga de resposta imposta ao atleta. Após a "
 "anuência da comissão, realizou-se reunião com o elenco, com explicação do procedimento, esclarecimento "
 "de dúvidas e assinatura do termo de consentimento livre e esclarecido. Uma sessão de familiarização "
 "antecedeu a semana de coleta e assegurou que cada atleta compreendesse a instrução temporal do "
 "instrumento e o significado de cada item.",
 "Durante a semana, o protocolo diferenciou o primeiro dia dos demais. No primeiro dia houve coleta única, "
 "aplicada à noite, após o treino, e essa medida foi tomada como linha de base do microciclo. Do segundo "
 "ao sétimo dia houve duas coletas diárias: a primeira pela manhã, antes da sessão inicial, tratada como "
 "medida pré; a última ao fim do dia, após a sessão final, tratada como medida pós. Os instrumentos foram "
 "aplicados em ambiente reservado do centro de treinamento, sempre pelo mesmo avaliador, com intervalo "
 "mínimo de dez minutos após o término da atividade, e sem consulta entre atletas.",
 "A unidade de análise adotada foi o par atleta-dia. Para os dias com duas coletas, o valor diário "
 "corresponde à média das medidas matinal e noturna do mesmo atleta; para o primeiro dia, corresponde à "
 "única medida disponível. Essa escolha elimina a pseudorreplicação que decorreria do tratamento de duas "
 "respostas do mesmo atleta no mesmo dia como observações independentes. As análises de dinâmica "
 "intradiária, ao contrário, preservam as duas medidas e operam sobre os 120 pares completos de manhã e "
 "noite. O conjunto final reuniu 166 pares atleta-dia."]),
("Instrumentos",[
 "Aplicou-se a Escala de Humor de Brunel em sua versão brasileira (ROHLFS et al., 2008), composta por "
 "vinte e quatro itens distribuídos em seis subescalas de quatro itens cada — tensão, depressão, raiva, "
 "vigor, fadiga e confusão —, respondidos em escala de cinco pontos, de zero a quatro, com amplitude de "
 "zero a dezesseis por subescala. A instrução temporal solicitou ao atleta que considerasse como se sentia "
 "naquele momento. A perturbação total do humor resulta da soma das cinco subescalas negativas subtraída "
 "do vigor, e varia de menos dezesseis a oitenta.",
 "Para permitir a comparação com a norma e a classificação nos seis perfis, cada subescala foi convertida "
 "em escore T por padronização contra os parâmetros normativos de amostras atléticas, com média cinquenta "
 "e desvio-padrão dez. Os parâmetros normativos foram recuperados por inversão das faixas de escore T "
 "publicadas, procedimento verificado com precisão de três casas decimais."]),
("Classificação nos seis perfis de humor",[
 "A classificação seguiu a proposta de Parsons-Smith, Terry e Machin (2017). Aplicou-se agrupamento por "
 "k-médias com seis centros, semeados nos centroides canônicos publicados, de modo que a solução não "
 "dependesse de inicialização aleatória. Os agrupamentos resultantes foram reancorados aos rótulos "
 "originais por atribuição ótima, com o algoritmo húngaro aplicado à matriz de distâncias entre centroides "
 "ajustados e canônicos. Uma análise discriminante linear treinada nos centroides canônicos serviu de "
 "verificação de robustez e concordou com a solução por k-médias em 71,1% dos pares atleta-dia.",
 "Para efeito de leitura clínica, os seis perfis foram agregados em três faixas. A faixa favorável reúne "
 "apenas o iceberg. A faixa neutra reúne a superfície e o submerso. A faixa de risco reúne a barbatana de "
 "tubarão, o iceberg invertido e o Everest invertido, configurações que a literatura associa a maior "
 "vulnerabilidade psicológica (TERRY; PARSONS-SMITH, 2021)."]),
("Tratamento de séries: suavização, derivadas e piso de ruído",[
 "O núcleo metodológico deste estudo consiste no tratamento aplicado às séries diárias, tanto às médias "
 "das subescalas quanto às prevalências dos perfis. O procedimento tem quatro passos encadeados.",
 "O primeiro passo estima a incerteza de cada ponto. Para séries de médias, o erro-padrão diário resulta "
 "do desvio-padrão da amostra do dia dividido pela raiz do número de respondentes daquele dia. Para séries "
 "de prevalência, o erro-padrão decorre da fórmula binomial, com a proporção observada e o número de pares "
 "do dia. O piso de ruído da série é definido como a média dos erros-padrão dos sete dias. Essa quantidade "
 "responde a uma pergunta simples: qual é a magnitude típica da oscilação que a amostragem, por si só, "
 "produz nesta série?",
 "O segundo passo suaviza a série. Aplicou-se um filtro binomial de três pontos, no qual cada ponto "
 "interno recebe peso um meio e cada vizinho recebe peso um quarto. Os extremos permanecem inalterados. O "
 "filtro atenua a oscilação de alta frequência sem deslocar o nível da série e preserva a soma dos pesos "
 "igual à unidade, o que garante que a média da série não se altere de modo sistemático.",
 "O terceiro passo calcula as derivadas discretas da série suavizada. A primeira derivada, obtida pela "
 "diferença entre dias consecutivos, mede a velocidade da mudança e responde a quanto o indicador se "
 "desloca por dia. A segunda derivada, obtida pela diferença entre velocidades consecutivas, mede a "
 "aceleração e responde a se o deslocamento ganha ou perde ritmo. Ambas foram expressas em unidades do "
 "piso de ruído da própria variável, o que torna comparáveis subescalas de amplitude e dispersão "
 "distintas. Denominou-se transição de choque aquela cuja primeira derivada, em valor absoluto, supera o "
 "piso; denominou-se ponto de inflexão a abscissa, obtida por interpolação linear, em que a segunda "
 "derivada muda de sinal.",
 "O quarto passo emite o veredito. Declara-se variação real, ou sinal, quando o deslocamento total entre "
 "o primeiro e o sétimo dia supera, em valor absoluto, o piso de ruído; caso contrário, atribui-se a "
 "oscilação à flutuação amostral. O mesmo princípio governa o teste de cruzamento entre duas séries. "
 "Calcula-se a série da diferença entre elas e o limiar combinado, definido como a raiz da soma dos "
 "quadrados dos dois pisos. O ponto de cruzamento é a abscissa em que a diferença muda de sinal, obtida "
 "por interpolação linear. A inversão só é declarada estabelecida quando a diferença ultrapassa o limiar "
 "antes e depois do cruzamento; do contrário, o achado é classificado como divergência, categoria que "
 "reconhece a troca de posição sem lhe atribuir estatuto de resultado.",
 "Cabe uma ressalva sobre o alcance do piso binomial. Em prevalências próximas de zero, o produto entre a "
 "proporção e o seu complemento tende a zero e o erro-padrão binomial encolhe artificialmente, o que "
 "rebaixa o piso e torna o critério permissivo. Séries de prevalência muito baixa, portanto, exigem "
 "leitura cautelosa, e o texto assinala explicitamente onde essa condição ocorre."]),
("Análise estatística e processamento computacional",[
 "Toda a análise foi executada em Python 3.11. A cadeia de processamento parte da planilha e termina no "
 "arquivo de saída, sem etapa manual intermediária, e reproduz-se pela execução sequencial dos roteiros.",
 "A importação empregou o pacote openpyxl para leitura das pastas de trabalho, com percurso célula a "
 "célula das planilhas de cada dia e reconstrução da matriz de respostas em estrutura nativa do Python. Os "
 "identificadores nominais foram substituídos por códigos anônimos de A01 a A27 na própria rotina de "
 "importação, de modo que nenhum nome trafegasse para as etapas seguintes. A conversão para arranjos "
 "numéricos, o cálculo de médias diárias, a padronização em escore T, a suavização, as derivadas e o "
 "cálculo dos pisos de ruído utilizaram o NumPy (HARRIS et al., 2020).",
 "Os testes de hipótese utilizaram o módulo stats do SciPy (VIRTANEN et al., 2020). A verificação de "
 "normalidade recorreu ao teste de Shapiro-Wilk, cujo resultado motivou a opção integralmente não "
 "paramétrica. A comparação global entre os sete dias empregou o teste de Friedman (FRIEDMAN, 1937), com "
 "tamanho de efeito expresso pelo W de Kendall (KENDALL; BABINGTON SMITH, 1939) e restrito aos atletas "
 "com registro completo nos sete dias. A hipótese de tendência ordenada recebeu tratamento específico pelo "
 "teste L de Page (PAGE, 1963), mais potente que o de Friedman quando a alternativa é monotônica. Os "
 "contrastes pareados recorreram ao teste de postos sinalizados de Wilcoxon (WILCOXON, 1945), com correção "
 "de Holm para multiplicidade (HOLM, 1979) e tamanho de efeito r obtido pela razão entre o escore z e a "
 "raiz do número de pares. A dinâmica intradiária entre a manhã e a noite empregou o mesmo teste de "
 "Wilcoxon sobre os pares completos.",
 "As variáveis categóricas seguiram procedimentos próprios. A estabilidade da prevalência de cada perfil "
 "ao longo dos sete dias foi avaliada pelo Q de Cochran (COCHRAN, 1950); a migração entre a manhã e a "
 "noite, pelo teste de McNemar (McNEMAR, 1947) com correção de continuidade; e a associação entre o tipo "
 "de estímulo e o perfil ou a faixa de humor, pelo qui-quadrado de contingência. As associações entre "
 "variáveis contínuas empregaram o coeficiente de Spearman, com decomposição da correlação total em "
 "componente entre atletas, calculada sobre as médias individuais, e componente dentro do atleta, "
 "calculada sobre os desvios em relação à média do próprio atleta. A homogeneidade dos coeficientes ao "
 "longo dos dias foi testada por qui-quadrado sobre as transformações z de Fisher. A persistência recorreu "
 "à autocorrelação de defasagem um, e a precedência temporal, a correlações parciais defasadas com "
 "controle do valor anterior do desfecho.",
 "A confiabilidade das medidas repetidas foi estimada por correlação intraclasse de via única, com o "
 "coeficiente de medida média obtido pela fórmula de Spearman-Brown (SHROUT; FLEISS, 1979), acompanhada do "
 "erro-padrão de medida e da mínima variação detectável. O efeito de piso foi avaliado pelo critério de "
 "Terwee et al. (2007), que considera problemática a concentração de mais de quinze por cento das "
 "respostas no valor extremo da escala. Adotou-se alfa de cinco por cento em todos os testes. As figuras "
 "foram produzidas com matplotlib (HUNTER, 2007), e a exportação do manuscrito utilizou a biblioteca "
 "python-docx. Os resultados intermediários foram serializados em arquivos JSON, o que permite auditar "
 "cada número do texto contra o objeto que o gerou."]),
("Aspectos éticos e proteção de dados",[
 "O projeto obteve aprovação do comitê de ética em pesquisa com seres humanos sob o parecer CAAE "
 "[inserir número do CAAE], e observou as diretrizes da Resolução 466/2012 do Conselho Nacional de Saúde e "
 "os princípios da Declaração de Helsinque. Todos os participantes assinaram termo de consentimento livre "
 "e esclarecido antes da primeira coleta.",
 "A base primária continha nomes completos associados a escores de humor e a registros de lesão. Por essa "
 "razão, a substituição por códigos anônimos ocorreu na própria rotina de importação, e apenas a base "
 "anonimizada alimentou as análises. Os arquivos que contêm identificação nominal permanecem sob guarda "
 "restrita do pesquisador responsável e não integram material suplementar nem repositório de dados "
 "abertos."]),
]

# ---------------- RESULTADOS ----------------
R1=[
"Os 166 pares atleta-dia distribuem-se de modo desigual ao longo da semana, com vinte e sete respondentes "
"no primeiro dia e vinte e um no sétimo. A Tabela 1 reúne a descrição completa das sete variáveis do "
"instrumento. Três traços organizam a leitura. Em primeiro lugar, a assimetria é acentuada nas subescalas "
"negativas: a depressão apresenta assimetria de 3,85 e curtose de 18,06, e a confusão, 3,49 e 14,88. Em "
"segundo lugar, a mediana coincide com o valor mínimo da escala em três subescalas — depressão, confusão e, "
"por pouca margem, raiva —, o que desloca a informação para as caudas. Em terceiro lugar, a média aparada a "
"vinte por cento afasta-se sistematicamente da média aritmética nas mesmas subescalas: a depressão cai de "
"1,01 para 0,31 e a confusão, de 0,51 para 0,12. O vigor é a única variável cuja distribuição não se afasta "
"da normalidade pelo teste de Shapiro-Wilk (W = 0,984; p = 0,054); todas as demais rejeitam a hipótese de "
"normalidade com p inferior a 0,001. Esse conjunto de evidências fundamenta a opção integralmente não "
"paramétrica adotada no restante do estudo.",

"O efeito de piso, apresentado na Tabela 2, ultrapassa com folga o limite de quinze por cento proposto por "
"Terwee et al. (2007) em quatro das seis subescalas: 65,7% das respostas de confusão, 51,2% das de "
"depressão, 44,6% das de raiva e 41,0% das de tensão concentram-se no valor zero. O vigor e a fadiga "
"escapam a essa condição, com 4,8% e 6,0% respectivamente. A consequência prática é direta: as quatro "
"subescalas com piso severo possuem margem para subir, mas quase nenhuma para descer, e qualquer "
"interpretação de queda nessas dimensões deve reconhecer a assimetria do instrumento.",

"A padronização contra a norma de atletas reposiciona o grupo. A fadiga situa-se em 57,9 e a raiva em 55,6, "
"ambas acima da média normativa; o vigor cai a 43,8, a confusão a 44,9 e a tensão a 41,6; a depressão "
"permanece sobre a linha da norma, em 50,4. O grupo, portanto, não exibe o perfil iceberg clássico: ele "
"combina baixa tensão e baixa confusão com fadiga e raiva elevadas e vigor rebaixado, configuração que se "
"aproxima da barbatana de tubarão descrita por Parsons-Smith, Terry e Machin (2017).",

"A confiabilidade das medidas repetidas ao longo da semana, também na Tabela 2, revela heterogeneidade "
"expressiva. A depressão apresenta a maior proporção de variância atribuível a diferenças estáveis entre "
"atletas (CCI de medida única de 0,768) e a raiva, a menor (0,333). A leitura substantiva é que a raiva "
"opera predominantemente como estado, sensível à situação do dia, ao passo que a depressão se comporta como "
"característica relativamente estável do respondente. A mínima variação detectável acompanha essa lógica: "
"3,05 pontos para a tensão, 6,17 para a raiva e 15,52 para a perturbação total, valores que estabelecem o "
"patamar abaixo do qual uma mudança individual não se distingue do erro de medida.",
]

R2=[
"O comportamento temporal das seis subescalas aparece na Figura 2. O painel A acompanha as trajetórias em "
"escore T, com o dia sombreado conforme o estímulo, e o painel B apresenta o resultado do teste de "
"tendência. A Tabela 3 documenta os testes.",

"O teste de Friedman, restrito aos dezenove atletas com registro completo nos sete dias, rejeita a hipótese "
"de igualdade entre os dias para quatro variáveis: confusão (χ² = 25,76; p < 0,001; W = 0,226), vigor "
"(χ² = 14,74; p = 0,022; W = 0,129), fadiga (χ² = 13,19; p = 0,040; W = 0,116) e tensão (χ² = 13,24; "
"p = 0,039; W = 0,116). A raiva fica no limiar (p = 0,056) e a depressão não se aproxima dele (p = 0,936). "
"Os coeficientes de concordância, contudo, são baixos: mesmo a confusão, a variável com maior efeito, "
"explica pouco mais de um quinto da variância dos postos. A comparação global entre dias, portanto, detecta "
"diferença, mas não descreve a sua forma.",

"O teste L de Page fornece o que falta ao de Friedman. Ao especificar a alternativa como ordenada de D1 a "
"D7, ele ganha potência e identifica tendência monotônica em quatro variáveis. O vigor decresce "
"(z = −3,22; p = 0,001), a fadiga cresce (z = 3,16; p = 0,002), a tensão decresce (z = −3,03; p = 0,002) e "
"a confusão decresce (z = −2,61; p = 0,009). A raiva não alcança significância (z = −1,59; p = 0,113), "
"tampouco a depressão (z = −0,58; p = 0,561) ou a perturbação total (z = 0,83; p = 0,405). Merece registro "
"o caso da raiva: o teste de Page a classifica como decrescente, ao passo que a comparação direta entre o "
"primeiro e o sétimo dia mostra elevação. A contradição é apenas aparente e revela a limitação do teste "
"quando a trajetória é não monotônica — a raiva cai até o quinto dia e sobe abruptamente depois, de modo "
"que a soma ponderada de postos favorece a direção do trecho mais longo.",

"O contraste direto entre a linha de base e a véspera da estreia, realizado sobre os vinte e um atletas com "
"as duas medidas, confirma três deslocamentos. O vigor recua 3,15 pontos (r = 0,517; p < 0,001; d de "
"Cohen para amostras pareadas de −0,955), a fadiga avança 3,19 pontos (r = 0,440; p = 0,004; d = 0,723) e a "
"tensão recua 1,20 ponto (r = 0,393; p = 0,011; d = −0,589). A confusão aproxima-se do limiar (p = 0,068) e "
"a perturbação total, apesar de crescer 4,92 pontos, não alcança significância (p = 0,104), consequência da "
"dispersão elevada do composto.",
]

R3=[
"A Figura 3 decompõe cada série em três camadas sobrepostas: a série observada com o respectivo erro-padrão "
"diário, a série suavizada pelo filtro binomial e a banda do piso de ruído em torno do valor basal. A "
"Tabela 4 registra os parâmetros do tratamento.",

"O piso de ruído varia de 0,21 ponto, na confusão, a 1,87 ponto, na perturbação total, e essa amplitude "
"justifica por si só o procedimento: uma variação de meio ponto significa coisas opostas nas duas "
"variáveis. Seis das sete séries superam o respectivo piso e recebem o veredito de sinal. O vigor desloca-se "
"3,12 pontos contra um piso de 0,58, isto é, 5,3 vezes o piso; a fadiga, 3,49 contra 0,76, ou 4,6 vezes; a "
"perturbação total, 5,76 contra 1,87, ou 3,1 vezes; a tensão, 1,23 contra 0,35, ou 3,5 vezes; a confusão, "
"0,47 contra 0,21, ou 2,2 vezes; e a raiva, 0,61 contra 0,50, apenas 1,2 vez, o que a coloca na fronteira "
"do critério. A depressão é a única série cuja variação total, de 0,23 ponto, permanece abaixo do piso de "
"0,45 e recebe o veredito de ruído. Esse resultado converge com o teste de Friedman e com o de Page, que "
"também não detectaram movimento na depressão, e ilustra a utilidade do critério: onde os testes formais "
"nada encontram, o piso de ruído oferece uma explicação positiva, e não apenas a ausência de evidência.",

"As transições de choque concentram-se nas duas extremidades da semana. O vigor e a fadiga apresentam "
"choque na passagem do primeiro para o segundo dia e na passagem do sexto para o sétimo; a tensão e a "
"confusão, apenas na primeira dessas passagens; a raiva, apenas nas duas últimas; e a perturbação total, "
"somente na passagem do sexto para o sétimo dia. A depressão não apresenta transição alguma que supere o "
"piso. O padrão que emerge é o de deslocamento por choques nas pontas, com platô intermediário, e não o de "
"deriva lenta e uniforme. Os pontos de inflexão reforçam essa leitura: situam-se entre o terceiro e o "
"quinto dia na maioria das variáveis — 3,98 no vigor, 3,74 na fadiga, 3,52 na perturbação total, 4,54 na "
"tensão e 5,07 na confusão —, o que localiza no miolo da semana a mudança de regime da aceleração.",
]

R4=[
"A Figura 4 expressa as duas derivadas em unidades do piso de ruído de cada variável, o que permite "
"compará-las diretamente apesar das diferenças de amplitude e dispersão. A moldura destaca as células cujo "
"valor absoluto supera uma unidade de piso.",

"A primeira derivada mostra que a velocidade se concentra em duas colunas. Na passagem do primeiro para o "
"segundo dia, o vigor cai 2,48 pisos, a confusão cai 1,90, a tensão cai 1,49 e a fadiga sobe 1,13. Na "
"passagem do sexto para o sétimo dia, a raiva sobe 1,93 pisos, a fadiga sobe 1,83 e o vigor cai 1,53. Entre "
"esses dois extremos, quase todas as velocidades permanecem abaixo de uma unidade de piso, o que confirma o "
"platô. Chama atenção que os dois choques tenham naturezas distintas: o primeiro decorre da transição de um "
"dia de carga mínima, tomado como linha de base, para o primeiro dia de treino intervalado, e afeta "
"simultaneamente o vigor, a tensão e a confusão; o segundo antecede a estreia competitiva e mobiliza a "
"raiva e a fadiga, sem repercussão equivalente sobre a tensão.",

"A segunda derivada localiza onde o movimento muda de ritmo. O vigor acelera 1,50 piso no segundo dia, o "
"que significa que a queda perde velocidade após o choque inicial — a aceleração positiva atua como freio "
"sobre um deslocamento negativo. A raiva acelera 1,42 piso no quinto dia, e a fadiga, 1,12 piso no sexto, "
"ambas com sinal concordante com o deslocamento, isto é, o movimento ganha ritmo. O vigor, por sua vez, "
"desacelera 1,27 piso no sexto dia, o que antecipa a queda final. A leitura conjunta das duas derivadas "
"sugere que o microciclo não produz uma deterioração contínua, e sim dois eventos discretos separados por "
"um período de estabilidade relativa.",
]

R5=[
"A Figura 5 aplica o mesmo tratamento às séries de prevalência dos seis perfis, e a Tabela 5 registra as "
"prevalências diárias e o teste de estabilidade.",

"A distribuição geral dos 166 pares atribui 31,3% ao iceberg, 25,9% à barbatana de tubarão, 19,3% ao "
"submerso, 11,4% ao iceberg invertido, 10,8% à superfície e 1,2% ao Everest invertido. O contraste com a "
"referência de Parsons-Smith, Terry e Machin (2017) é informativo: a barbatana de tubarão comparece com "
"mais que o dobro da prevalência de referência (25,9% contra 11,6%) e o submerso, com pouco mais da metade "
"(19,3% contra 30,6%). A amostra, portanto, não reproduz a distribuição populacional do estudo original, "
"resultado esperado em um grupo submetido a carga elevada e proximidade competitiva.",

"A trajetória diária revela dois movimentos de sentido oposto e magnitude comparável. O iceberg recua de "
"37,0% no primeiro dia para 19,0% no sétimo, deslocamento de 18,0 pontos percentuais contra um piso de 9,4 "
"pontos. A barbatana de tubarão avança de 11,1% para 28,6%, deslocamento de 17,5 pontos contra um piso de "
"8,9. A faixa de risco, que agrega três perfis, sobe de 29,6% para 52,4%, deslocamento de 22,8 pontos "
"contra um piso de 9,9. A superfície recua 6,3 pontos contra um piso de 6,0, resultado que supera o "
"critério por margem estreita e merece leitura reservada. O submerso e o iceberg invertido oscilam abaixo "
"dos respectivos pisos e recebem o veredito de ruído. O Everest invertido, cujo deslocamento nominalmente "
"supera o piso, envolve dois pares atleta-dia no conjunto inteiro; o piso binomial, calculado sobre "
"proporções próximas de zero, encolhe a ponto de deixar de discriminar, e por isso a figura o assinala "
"como não avaliável.",

"O teste Q de Cochran, aplicado aos dezenove atletas com registro completo, não rejeita a hipótese de "
"estabilidade para nenhum dos seis perfis nem para a faixa de risco. Os valores de p variam de 0,088, no "
"submerso, a 0,855, na faixa de risco. Esse resultado exige comentário explícito, pois aparentemente "
"contradiz o veredito de sinal descrito no parágrafo anterior. As duas análises, porém, respondem a "
"perguntas diferentes e operam sobre conjuntos diferentes. O critério do piso de ruído avalia a série "
"agregada de todos os pares disponíveis e pergunta se o deslocamento observado excede a oscilação amostral "
"típica; o Q de Cochran avalia dezenove trajetórias individuais completas e pergunta se a probabilidade de "
"pertencer a um perfil difere entre os dias. A perda de trinta por cento da amostra e a natureza binária do "
"desfecho reduzem drasticamente a potência do segundo teste. A conclusão prudente é que o deslocamento "
"agregado do iceberg para a barbatana de tubarão é consistente e de magnitude relevante, porém não "
"confirmado por teste formal na subamostra completa.",
]

R6=[
"A Figura 6 apresenta a distribuição dos seis perfis por tipo de estímulo e a composição das faixas de "
"humor, e a Tabela 6 detalha os percentuais. A Tabela 7 reúne o nível médio de cada variável em cada tipo de dia e a respectiva resposta aguda intradiária.",

"O achado principal desta seção é negativo e merece enunciado direto. A distribuição dos seis perfis não "
"difere entre os tipos de estímulo (χ² = 7,58; gl = 10; p = 0,670), e tampouco difere a composição das três "
"faixas de humor (χ² = 4,45; gl = 4; p = 0,349). As diferenças aparentes — a barbatana de tubarão responde "
"por 36,4% dos pares nos dias de conteúdo técnico e de força contra 11,1% no dia basal, e a faixa de risco "
"alcança 50,0% naqueles dias contra 29,6% neste — situam-se dentro da margem de erro para o número de pares "
"disponível em cada categoria, que varia de vinte e dois a sessenta e oito. A classificação categórica, "
"portanto, não distingue os estímulos.",

"A análise das variáveis contínuas, ao contrário, distingue. O nível médio da perturbação total difere "
"entre os tipos de dia (r = 0,455; p = 0,001), assim como o da depressão (r = 0,380; p = 0,007), o da "
"raiva (r = 0,337; p = 0,017), o da fadiga (r = 0,324; p = 0,022) e o do vigor (r = 0,307; p = 0,030). Os "
"dias de treino intervalado apresentam a maior perturbação total média (5,85) e os dias de amistoso, a "
"menor (2,41); os dias de conteúdo técnico e de força situam-se entre elas (4,80). O vigor segue o padrão "
"inverso, com 5,07 nos dias intervalados contra 5,67 nos amistosos e 5,74 nos técnicos. O contraste entre "
"os dois conjuntos de resultados é instrutivo: o estímulo desloca os níveis das variáveis, mas o "
"deslocamento não é suficiente para reconfigurar o vetor de seis dimensões a ponto de mudar a atribuição de "
"perfil. A classificação categórica perde resolução justamente onde a diferença existe.",

"A resposta aguda dentro do dia, medida pela diferença entre a noite e a manhã, confirma essa leitura e "
"acrescenta um resultado contraintuitivo. Nos dias de treino intervalado, a fadiga sobe 2,04 pontos "
"(r = 0,417; p = 0,003) e a perturbação total sobe 3,33 pontos (r = 0,284; p = 0,041), ao passo que o vigor "
"não cai de modo significativo. Nos dias de amistoso, apenas a confusão se move, e para baixo (−0,44; "
"r = 0,321; p = 0,026). Nos dias de conteúdo técnico e de força, contudo, registra-se a maior perturbação "
"aguda de toda a semana: o vigor cai 2,10 pontos (r = 0,410; p = 0,009), a raiva sobe 1,60 (r = 0,406; "
"p = 0,010), a depressão sobe 1,05 (r = 0,404; p = 0,011) e a perturbação total sobe 6,65 pontos "
"(r = 0,427; p = 0,007). O dia sem estímulo intervalado e sem jogo produz, portanto, o maior deslocamento "
"afetivo intradiário do microciclo.",

"Uma advertência de delineamento condiciona toda esta seção. Os tipos de estímulo não foram distribuídos ao "
"acaso ao longo da semana: o treino intervalado ocupa o segundo, o quarto e o sétimo dias; o amistoso, o "
"terceiro e o quinto; e o conteúdo técnico e de força, exclusivamente o sexto. O tipo de estímulo, "
"portanto, confunde-se com a posição no microciclo e com a carga acumulada até aquele ponto. O dia de "
"conteúdo técnico e de força é o penúltimo da semana e sucede vinte horas e meia de trabalho acumulado; a "
"maior perturbação nele observada admite tanto a leitura de resposta ao estímulo quanto a de efeito "
"cumulativo, e o presente delineamento não separa as duas.",
]

R7=[
"A Figura 7 acompanha a migração entre a manhã e a noite dentro de cada tipo de estímulo, e a Tabela 8 "
"registra os testes de McNemar.",

"Considerados em conjunto os 120 pares completos de manhã e noite, a migração para a faixa de risco é "
"inequívoca: vinte e sete pares entram nessa faixa ao longo do dia e apenas nove saem dela (χ² = 8,03; "
"p = 0,005). A prevalência do iceberg cai de 38,8% pela manhã para 25,9% à noite, e a da faixa de risco "
"sobe de 32,7% para 44,9%. O dia de treino, qualquer que seja o seu conteúdo, desloca o grupo na direção do "
"risco.",

"A decomposição por tipo de estímulo enfraquece o resultado. Nos dias de treino intervalado, quinze pares "
"entram na faixa de risco e cinco saem (χ² = 4,05; p = 0,044), valor que não sobrevive à correção de Holm "
"para três comparações (p ajustado = 0,133). Nos dias de amistoso, nove entram e três saem (p = 0,149). Nos "
"dias de conteúdo técnico e de força, três entram e um sai (p = 0,617). A razão entre entradas e saídas é "
"idêntica nos três estímulos — exatamente três para um —, e o que varia é apenas o número de pares "
"disponível em cada categoria. Esse detalhe é decisivo: a diferença entre os três valores de p reflete "
"tamanho de amostra, não intensidade de efeito. A migração intradiária para a faixa de risco é um fenômeno "
"robusto do microciclo; a atribuição dessa migração a um estímulo particular carece de sustentação.",
]

R8=[
"A Figura 8 aplica o teste formal de cruzamento a dois pares de séries e ilustra a diferença entre uma "
"troca de posição aparente e uma inversão estabelecida.",

"A faixa favorável e a faixa de risco trocam de posição três vezes ao longo da semana, nas abscissas 1,49, "
"4,69 e 5,24. O limiar combinado dos dois pisos é de 13,6 pontos percentuais. A diferença entre as duas "
"séries parte de 7,4 pontos no primeiro dia e alcança −33,3 pontos no sétimo; entretanto, em nenhum dos "
"três cruzamentos a diferença ultrapassa o limiar dos dois lados do ponto de troca. O procedimento, "
"portanto, classifica o achado como divergência e recusa-lhe o estatuto de inversão estabelecida. A "
"separação final entre as duas faixas é substancial e supera com folga o limiar, mas ela se consolida "
"apenas na última transição, e a trajetória anterior oscila dentro da margem de ruído.",

"O par formado pelo vigor e pela fadiga recebe veredito distinto. As duas séries cruzam-se uma única vez, "
"na abscissa 5,03, com limiar combinado de 0,96 ponto. A diferença entre vigor e fadiga é de 3,65 pontos no "
"primeiro dia, favorável ao vigor, e de −2,97 pontos no sétimo, favorável à fadiga; ambos os valores "
"superam o limiar. A inversão é, nesse caso, declarada estabelecida. O resultado tem significado prático "
"imediato: em algum ponto do quinto dia, o grupo deixa de ser predominantemente vigoroso e passa a ser "
"predominantemente fatigado, e essa troca não se explica por oscilação amostral.",
]

R9=[
"A Figura 9 encerra os resultados com a estrutura de associação entre as variáveis. O painel A apresenta a "
"matriz de correlações de Spearman; o painel B decompõe as associações em componente entre atletas e "
"componente dentro do atleta; o painel C mede a persistência de um dia para o outro; e o painel D testa a "
"precedência temporal.",

"Quinze dos vinte e um pares de variáveis associam-se de modo significativo após a correção de Holm. A "
"fadiga vincula-se fortemente à perturbação total (ρ = 0,76) e o vigor, de modo inverso (ρ = −0,61). Duas "
"ausências chamam atenção. A tensão não se correlaciona com a fadiga (ρ = −0,08) e correlaciona-se "
"positivamente com o vigor (ρ = 0,21; p ajustado = 0,043), o que a afasta do bloco de afeto negativo e "
"sugere que, neste contexto, a tensão opera como ativação e não como sofrimento. A correlação item-total "
"corrigida confirma a anomalia: a tensão é a única subescala cuja contribuição para o composto não difere "
"de zero (ρ = 0,015; p = 0,848).",

"A decomposição revela que a origem das associações varia. O par formado pela tensão e pelo vigor associa-se "
"apenas dentro do atleta (ρ = 0,30; p < 0,001) e não entre atletas (ρ = 0,21; p = 0,297): em um mesmo "
"atleta, os dias de maior tensão são também os de maior vigor, mas atletas mais tensos não são, em média, "
"mais vigorosos. O par formado pela tensão e pela depressão comporta-se de modo oposto e não se sustenta em "
"nenhum dos dois planos. Já os pares que envolvem a fadiga e a perturbação total mantêm-se robustos nos "
"dois planos, com coeficientes de 0,77 entre atletas e 0,69 dentro do atleta.",

"O acoplamento entre a fadiga e a perturbação total cresce ao longo da semana. O coeficiente diário parte de "
"0,66 no primeiro dia e alcança 0,91 no sétimo, com tendência significativa (tau = 0,929; p = 0,003). A "
"proporção de variância do composto partilhada com a fadiga sobe, por consequência, de 44,2% para 83,3%. À "
"medida que a carga se acumula, portanto, a perturbação total perde multidimensionalidade e converte-se "
"progressivamente em um indicador de fadiga. Dois outros pares apresentam heterogeneidade significativa dos "
"coeficientes ao longo dos dias: raiva e depressão (χ² = 13,96; p = 0,030) e depressão e confusão "
"(χ² = 17,23; p = 0,008).",

"A autocorrelação de defasagem um é elevada e significativa em todas as sete variáveis, de 0,55 na confusão "
"a 0,77 na tensão e na fadiga. O humor de um dia prediz com firmeza o do dia seguinte. Nenhuma das oito "
"correlações parciais defasadas testadas, contudo, alcança significância após o controle do valor anterior "
"do desfecho; a maior magnitude observada é de 0,10, na direção da fadiga sobre a perturbação total "
"(p = 0,249). A estrutura observada é, assim, de covariação simultânea com forte persistência, e não de "
"precedência de uma dimensão sobre outra.",
]

DISCUSSAO=[
("A forma da semana: dois choques e um platô",[
 "O primeiro resultado a discutir não é um valor, e sim uma forma. A deterioração do humor ao longo do "
 "microciclo terminal não se distribui de modo uniforme: ela se concentra em duas transições e deixa entre "
 "elas um período de estabilidade relativa. As derivadas expressas em unidades do piso de ruído tornam essa "
 "forma visível de maneira que a comparação entre médias diárias jamais permitiria. Na passagem do dia "
 "basal para o primeiro dia de treino intervalado, quatro variáveis se movem acima do piso; na passagem do "
 "penúltimo para o último dia, três se movem; nos quatro dias intermediários, quase nenhuma o faz.",
 "Essa geometria contraria a intuição de acúmulo linear que costuma orientar a leitura de séries de "
 "monitoramento. Se a carga se soma dia após dia, e ela de fato se soma — de 1,5 hora para 23,0 horas ao "
 "longo da semana —, seria razoável esperar deterioração proporcional. O que se observa, porém, aproxima-se "
 "mais de um sistema com histerese: ele resiste até certo ponto, cede de uma vez e depois se estabiliza em "
 "novo patamar. Meeusen et al. (2013) descreveram o continuum entre sobrecarga funcional, sobrecarga não "
 "funcional e supertreinamento em termos de patamares, e não de gradientes; os dados aqui apresentados "
 "oferecem, em escala diária, uma imagem compatível com essa descrição.",
 "O segundo choque tem interpretação distinta do primeiro. Ele ocorre na véspera da estreia competitiva e "
 "mobiliza a raiva e a fadiga sem repercussão equivalente sobre a tensão, que continua a cair. A antecipação "
 "competitiva, nesse grupo, não se traduz em tensão autorrelatada. Gentile et al. (2021) observaram, em "
 "contexto de campeonato mundial, perfis psicológicos que também não replicavam o padrão ansioso esperado, e "
 "Bird et al. (2025) documentaram, em seleção nacional durante competição internacional, dissociação "
 "semelhante entre marcadores de bem-estar e de ativação. A convergência sugere que atletas de alto "
 "rendimento reconhecem e nomeiam a fadiga com facilidade maior do que a tensão."]),
("O estímulo desloca níveis sem reconfigurar perfis",[
 "O achado central sobre a resposta aos estímulos é negativo, e a sua interpretação exige cuidado. A "
 "distribuição dos seis perfis não difere entre dias de treino intervalado, dias de amistoso e dias de "
 "conteúdo técnico e de força. As variáveis contínuas, no entanto, diferem: a perturbação total, a "
 "depressão, a raiva, a fadiga e o vigor apresentam níveis médios distintos conforme o tipo de dia. A "
 "coexistência dos dois resultados não é contradição, e sim informação sobre o instrumento de classificação.",
 "A atribuição de perfil resulta da menor distância entre o vetor de seis escores T e seis centroides "
 "fixos. Esse procedimento é, por construção, uma quantização: ele mapeia um espaço contínuo de seis "
 "dimensões em seis rótulos. Toda quantização descarta informação, e a informação descartada é justamente "
 "aquela contida em deslocamentos que não cruzam uma fronteira de decisão. Um atleta cuja fadiga sobe dois "
 "pontos e cujo vigor cai um ponto pode permanecer no mesmo perfil se o seu vetor não atravessar a fronteira "
 "entre duas regiões do espaço. Em uma amostra de vinte e sete atletas, o número de vetores próximos a "
 "fronteiras é pequeno, e o poder da classificação para detectar deslocamentos moderados é, por "
 "consequência, baixo.",
 "Essa constatação tem alcance que ultrapassa o presente estudo. A literatura sobre os seis perfis "
 "consolidou-se sobre estimativas de prevalência em grandes amostras transversais (PARSONS-SMITH; TERRY; "
 "MACHIN, 2017; HAN; PARSONS-SMITH; TERRY, 2020; LEW et al., 2023; TERRY; PARSONS-SMITH; VLACHOPOULOS, "
 "2024; ROHLFS; NOCE; WILKE, 2024), condição na qual o tamanho amostral compensa a perda de resolução da "
 "quantização. O transporte da mesma classificação para o monitoramento longitudinal de um elenco reduzido "
 "não herda essa propriedade. A recomendação que decorre dos dados é direta: em contextos de equipe, os "
 "perfis servem para descrever o estado do grupo e para comunicar esse estado à comissão técnica, ao passo "
 "que a detecção de resposta a estímulos específicos deve permanecer no plano das variáveis contínuas.",
 "Merece exame o resultado que atribui a maior perturbação aguda ao dia de conteúdo técnico e de força. À "
 "primeira vista, ele desafia a expectativa de que o treino intervalado de alta intensidade produza o maior "
 "custo afetivo. Duas explicações concorrem. A primeira é substantiva: sessões longas de conteúdo técnico e "
 "tático combinam exigência atencional sustentada com correção permanente do gesto, e essa combinação pode "
 "custar mais em termos afetivos do que o esforço metabólico concentrado. A segunda é de delineamento: esse "
 "dia é o penúltimo da semana e sucede vinte horas e meia de trabalho acumulado, de modo que a resposta "
 "observada pode expressar o estado do atleta naquele ponto do microciclo, e não a natureza do estímulo. O "
 "presente desenho não arbitra entre as duas, e a honestidade exige que ambas permaneçam abertas."]),
("Sinal e ruído: uma exigência anterior à interpretação",[
 "A contribuição metodológica deste estudo consiste em tornar explícito um compromisso que a literatura de "
 "monitoramento costuma manter tácito. Antes de examinar uma série, o analista precisa declarar qual "
 "magnitude de variação ele considerará digna de leitura. Sem essa declaração prévia, a interpretação "
 "torna-se refém do que se observa: sobe-se um degrau e chama-se de tendência; desce-se outro e chama-se de "
 "recuperação. O piso de ruído, definido como a média dos erros-padrão diários, oferece uma resposta "
 "operacional a essa exigência, e a sua virtude não reside na sofisticação, que é nenhuma, e sim na "
 "anterioridade.",
 "A literatura psicométrica já reconhece o princípio quando exige a mínima variação detectável para "
 "interpretar mudanças individuais (TERWEE et al., 2007), e os documentos de consenso sobre monitoramento "
 "recomendam critérios equivalentes (SAW; MAIN; GASTIN, 2016; KELLMANN et al., 2018). O que raramente se "
 "faz é transportar o mesmo cuidado para as séries agregadas do grupo, precisamente onde a tentação "
 "narrativa é maior, porque a série do grupo parece mais estável do que a do indivíduo. Ela é mais estável, "
 "de fato; mas o número de respondentes que a sustenta varia de dia para dia, e essa variação produz "
 "oscilação que nada deve à carga.",
 "A aplicação do critério aos dados produziu três consequências que ilustram a sua utilidade. Em primeiro "
 "lugar, ele explicou a imobilidade da depressão em termos positivos: a variação de 0,23 ponto é menor do "
 "que a oscilação amostral típica de 0,45 ponto, e não apenas ausência de evidência de mudança. Em segundo "
 "lugar, ele recusou o estatuto de inversão à troca de posição entre a faixa favorável e a faixa de risco, "
 "achado que uma leitura desatenta teria celebrado como o resultado mais vistoso do estudo. Em terceiro "
 "lugar, ele expôs a própria fragilidade em prevalências próximas de zero, onde o erro-padrão binomial "
 "encolhe e o critério se torna permissivo — limitação que o texto assinala em vez de ocultar.",
 "Há, nessa discussão, uma dimensão que ultrapassa a técnica. Uma série de sete pontos comporta muitas "
 "narrativas, e a escolha entre elas raramente decorre dos dados. O piso de ruído funciona como um "
 "compromisso que o analista assume consigo mesmo antes de olhar, e o seu valor epistemológico reside "
 "exatamente aí: ele restringe o espaço de histórias que os mesmos números autorizam. Nenhum critério "
 "elimina o julgamento; o que um critério explícito faz é torná-lo auditável."]),
("A perturbação total como composto que se degrada",[
 "O acoplamento crescente entre a fadiga e a perturbação total constitui, talvez, o achado de maior "
 "consequência prática deste estudo. O coeficiente parte de 0,66 no dia basal e alcança 0,91 na véspera da "
 "estreia, com tendência significativa, de modo que a proporção de variância do composto partilhada com a "
 "fadiga sobe de 44,2% para 83,3%. Em termos operacionais, a perturbação total no primeiro dia agrega "
 "informação de várias dimensões; no sétimo, ela reproduz quase inteiramente a fadiga.",
 "Esse fenômeno tem implicação imediata para a prática do monitoramento. A perturbação total é o indicador "
 "mais utilizado em contextos aplicados justamente pela conveniência de resumir seis dimensões em um "
 "número. A conveniência, porém, não é constante ao longo do microciclo: ela decresce à medida que a carga "
 "se acumula. Quem acompanha apenas o composto na fase terminal da pré-temporada acompanha, na prática, a "
 "subescala de fadiga, e perde a informação que as demais dimensões ainda carregam. A recomendação que "
 "decorre é a de reportar sempre o perfil completo, e não o escalar isolado.",
 "O resultado dialoga com a crítica metanalítica ao poder preditivo do humor sobre o desempenho. Beedie, "
 "Terry e Lane (2000) e Lochbaum et al. (2021) convergem na conclusão de que o efeito existe e é modesto. "
 "Uma explicação possível para essa modéstia reside na própria degradação do composto: se a perturbação "
 "total mede coisas diferentes em momentos diferentes da temporada, a agregação de estudos conduzidos em "
 "fases distintas dilui necessariamente o efeito. A hipótese não se testa com os presentes dados, mas ela "
 "recomenda que estudos futuros reportem a fase do ciclo em que a medida foi obtida."]),
("A tensão como ativação e não como sofrimento",[
 "A tensão comporta-se, neste grupo, de modo que a teoria do afeto negativo não prevê. Ela não se "
 "correlaciona com a fadiga, correlaciona-se positivamente com o vigor e não contribui de modo "
 "significativo para a perturbação total. Além disso, decresce ao longo da semana, com tendência confirmada "
 "pelo teste de Page, exatamente no período em que a fadiga cresce e o vigor cai. A decomposição esclarece "
 "a natureza da associação com o vigor: ela existe apenas dentro do atleta, isto é, os dias de maior tensão "
 "de um mesmo atleta são também os seus dias de maior vigor, ao passo que atletas mais tensos não são, em "
 "média, mais vigorosos.",
 "A leitura mais econômica atribui à tensão, neste contexto, a função de ativação. A distinção entre "
 "ansiedade facilitadora e ansiedade debilitadora percorre a psicologia do esporte há décadas, e o padrão "
 "aqui observado sugere que os itens de tensão da escala captam, em atletas de elite em pré-temporada, "
 "prontidão e não sofrimento. Belgacem et al. (2026) documentaram, em atletas jovens de caratê, associação "
 "entre ansiedade competitiva e alterações de humor e de sono que apontam em direção distinta, o que reforça "
 "a hipótese de que a função da tensão depende do nível competitivo e da fase da temporada.",
 "Cabe, porém, uma explicação alternativa de natureza métrica. A tensão apresenta efeito de piso de 41,0%, "
 "e a sua média em escore T é de 41,6, quase um desvio-padrão abaixo da norma. Uma variável comprimida "
 "contra o limite inferior da escala perde variância e, com ela, capacidade de correlacionar-se. A anomalia "
 "pode, assim, ser artefato de piso e não propriedade psicológica. As duas explicações não se excluem, e a "
 "distinção entre elas exige instrumento com maior amplitude na faixa baixa."]),
("Implicações para o monitoramento no handebol de elite",[
 "O levantamento de Henze et al. (2025) revelou que a prática de monitoramento em clubes profissionais de "
 "handebol privilegia indicadores de carga externa, apesar da evidência de que medidas subjetivas superam "
 "medidas objetivas na detecção de respostas ao treino (SAW; MAIN; GASTIN, 2016). Os presentes resultados "
 "acrescentam três recomendações operacionais a esse debate.",
 "A primeira diz respeito à frequência. A migração intradiária para a faixa de risco, com vinte e sete "
 "entradas contra nove saídas, só se torna visível porque houve duas coletas diárias. Um protocolo com "
 "coleta única perderia integralmente esse fenômeno, e a escolha entre a medida matinal e a noturna "
 "produziria retratos substancialmente distintos do mesmo dia. A segunda diz respeito ao critério. Nenhuma "
 "série de monitoramento deve ser lida sem uma declaração prévia da magnitude que se considerará relevante; "
 "o piso de ruído fornece uma dessas declarações, e o seu cálculo exige apenas o desvio-padrão e o número "
 "de respondentes de cada dia. A terceira diz respeito ao nível de agregação. O perfil comunica bem e "
 "detecta mal; a variável contínua detecta bem e comunica mal. O uso conjunto dos dois planos, e não a "
 "escolha entre eles, é o que os dados recomendam.",
 "Convém situar essas recomendações no contexto de risco da modalidade. Rafnsson et al. (2021) associaram "
 "carga e problemas por uso excessivo na pré-temporada do handebol, e Bjørndal et al. (2021) verificaram "
 "que picos de carga precedem problemas de saúde ao longo da temporada. Büchel, Döring e Baumeister (2026) "
 "demonstraram que a carga se distribui de modo desigual entre atletas do mesmo elenco. Se o humor funciona "
 "como sentinela precoce, conforme sustentam os documentos de consenso (MEEUSEN et al., 2013; KELLMANN et "
 "al., 2018), e se a fadiga percebida acompanha o acúmulo de trabalho, conforme os presentes dados "
 "indicam, então a leitura diária do perfil de humor oferece uma via de baixo custo para identificar, entre "
 "atletas submetidos à mesma programação, aqueles que respondem de modo desproporcional. Rohlfs et al. "
 "(2025) reforçaram essa via ao associar estados de humor à condição de lesão em atletas brasileiros de "
 "alto rendimento."]),
]

LIMITACOES=[
"A primeira limitação é de delineamento e já recebeu enunciado no corpo dos resultados. Os tipos de estímulo "
"não foram distribuídos ao acaso ao longo da semana, de modo que o tipo de dia se confunde com a posição no "
"microciclo e com a carga acumulada. O dia de conteúdo técnico e de força ocorreu uma única vez e ocupou o "
"penúltimo lugar da sequência; toda inferência sobre a especificidade desse estímulo permanece, por isso, "
"provisória.",
"A segunda limitação é de tamanho de amostra. Vinte e sete atletas de um único elenco geram entre vinte e um "
"e vinte e sete pares por dia, número que sustenta a descrição, mas restringe severamente a potência dos "
"testes categóricos. O Q de Cochran, aplicado aos dezenove atletas com registro completo, não rejeitou a "
"hipótese de estabilidade para nenhum perfil, e essa ausência de rejeição deve ser lida como limitação de "
"potência, e não como evidência de estabilidade.",
"A terceira limitação decorre das propriedades do instrumento nesta amostra. Quatro das seis subescalas "
"apresentam efeito de piso acima do critério de Terwee et al. (2007), o que compromete a capacidade de "
"detectar melhora e introduz assimetria em toda comparação. A anomalia da tensão, discutida acima, pode "
"originar-se dessa compressão.",
"A quarta limitação refere-se ao piso de ruído em séries de prevalência baixa. O erro-padrão binomial "
"encolhe quando a proporção se aproxima de zero, o que rebaixa o piso e torna o critério permissivo. O caso "
"do Everest invertido, com dois pares no conjunto inteiro, ilustra a condição, e o texto o assinalou como "
"não interpretável.",
"A quinta limitação é de generalização. O estudo acompanhou uma única equipe masculina de primeira divisão "
"em uma única semana de uma única temporada. A replicação em equipes femininas, em outras fases do "
"calendário e em outros níveis competitivos permanece necessária, e a comparação com outras modalidades "
"coletivas exigirá cautela adicional dada a especificidade das demandas do handebol (KARCHER; BUCHHEIT, "
"2014; GARCÍA-SÁNCHEZ et al., 2023).",
"A sexta limitação diz respeito à ausência de desfechos externos. O estudo não registrou desempenho "
"objetivo, marcadores fisiológicos nem incidência de lesão no período, o que impede verificar se os "
"deslocamentos afetivos observados anteciparam qualquer consequência prática. A associação entre humor, "
"lesão e desempenho, documentada por Rohlfs et al. (2025), permanece, neste conjunto, hipótese e não "
"resultado.",
]

CONCLUSAO=[
"O humor de atletas de handebol de elite deteriorou-se de modo consistente ao longo da última semana de "
"pré-temporada. O vigor recuou 3,12 pontos e a fadiga avançou 3,49, ambos acima do respectivo piso de "
"ruído e com tendência monotônica confirmada por teste específico. O perfil iceberg recuou de 37,0% para "
"19,0% dos pares atleta-dia e a faixa de risco avançou de 29,6% para 52,4%. A deterioração, contudo, não "
"se distribuiu de modo uniforme: ela se concentrou em duas transições, a primeira na saída do dia basal e "
"a segunda na véspera da estreia, e deixou entre elas um platô de quatro dias.",
"A resposta dos seis perfis aos diferentes estímulos não se confirmou. Nem a distribuição dos perfis nem a "
"composição das faixas de humor diferiram entre dias de treino intervalado, dias de amistoso e dias de "
"conteúdo técnico e de força. As variáveis contínuas, ao contrário, distinguiram os estímulos, o que "
"indica perda de resolução da classificação categórica e não ausência de efeito. A migração intradiária "
"para a faixa de risco mostrou-se robusta no conjunto dos 120 pares completos, porém a sua atribuição a um "
"estímulo particular não sobreviveu à correção para comparações múltiplas.",
"O tratamento de séries proposto — filtro binomial, derivadas de primeira e segunda ordem expressas em "
"unidades de ruído e teste formal de cruzamento — mostrou-se útil em três frentes: localizou as transições "
"de choque e os pontos de inflexão que a comparação entre médias diárias não revela; explicou a imobilidade "
"da depressão em termos positivos; e recusou estatuto de resultado a uma troca de posição aparente entre "
"faixas de humor, ao mesmo tempo em que reconheceu a inversão estabelecida entre vigor e fadiga no quinto "
"dia. Recomenda-se a sua adoção como etapa prévia à interpretação de qualquer série curta de monitoramento "
"psicológico.",
"Duas orientações práticas encerram o estudo. A comissão técnica que acompanha um elenco na semana "
"anterior à estreia deve concentrar atenção nas duas transições identificadas, e não distribuí-la "
"uniformemente pela semana. E deve reportar o perfil completo em vez do escalar de perturbação total, cuja "
"informação se reduz progressivamente à fadiga à medida que a carga se acumula.",
]

REFS=[
 'BEEDIE, C. J.; TERRY, P. C.; LANE, A. M. The profile of mood states and athletic performance: two meta-analyses. Journal of Applied Sport Psychology, v. 12, n. 1, p. 49-68, 2000.',
 'BELGACEM, A.; SALEM, A.; YILDIZ, M. et al. Impact of competitive anxiety on mood, sleep, and physical activity levels in young karate athletes. Medicine, v. 105, 2026. DOI: 10.1097/MD.0000000000048435.',
 "BIRD, S. P.; PARSONS-SMITH, R. L.; KING, R. et al. Wellness, mood, sleep, and performance in a women's national basketball team during international competition. Journal of Human Kinetics, 2025. DOI: 10.5114/jhk/200117.",
 'BJØRNDAL, C. T.; BACHE-MATHIESEN, L. K.; GJESDAL, S. et al. An examination of training load, match activities, and health problems in Norwegian youth elite handball players over one competitive season. Frontiers in Sports and Active Living, v. 3, 635103, 2021.',
 'BÜCHEL, D.; DÖRING, M.; BAUMEISTER, J. Inter-individual differences in weekly training load in international-level handball players. Frontiers in Sports and Active Living, v. 7, 1605750, 2026.',
 'COCHRAN, W. G. The comparison of percentages in matched samples. Biometrika, v. 37, n. 3-4, p. 256-266, 1950. DOI: 10.1093/biomet/37.3-4.256.',
 'COSTA, J. A.; FIGUEIREDO, P.; NAKAMURA, F. Y. The importance of sleep in athletes. In: SLEEP MEDICINE AND THE EVOLUTION OF CONTEMPORARY SLEEP SCIENCE. London: IntechOpen, 2022. DOI: 10.5772/intechopen.102535.',
 'FERREIRA, A. B. M.; RIBEIRO, B. L. L.; MELO, A. L. L. S. et al. Effects of different training load magnitudes on sleep pattern and mood state in young soccer players. Sleep Science, v. 16, 2023. DOI: 10.1055/s-0043-1770247.',
 'FRIEDMAN, M. The use of ranks to avoid the assumption of normality implicit in the analysis of variance. Journal of the American Statistical Association, v. 32, n. 200, p. 675-701, 1937. DOI: 10.1080/01621459.1937.10503522.',
 'GARCÍA-SÁNCHEZ, C. et al. Physical demands during official competitions in elite handball: a systematic review. International Journal of Environmental Research and Public Health, v. 20, n. 4, 3353, 2023.',
 "GENTILE, A.; TRIVIĆ, T.; BIANCO, A. et al. Living in the “bubble”: athletes' psychological profile during the Sambo World Championship. Frontiers in Psychology, v. 12, 657652, 2021.",
 'HAN, C. S. Y.; PARSONS-SMITH, R. L.; TERRY, P. C. Mood profiling in Singapore: cross-cultural validation and potential applications of mood profile clusters. Frontiers in Psychology, v. 11, 665, 2020.',
 'HARRIS, C. R. et al. Array programming with NumPy. Nature, v. 585, n. 7825, p. 357-362, 2020.',
 "HENZE, A. S. et al. Athlete monitoring in handball (ATHMON HB): a survey of current practice in professional women's and men's handball. BMC Sports Science, Medicine and Rehabilitation, v. 17, n. 1, 126, 2025.",
 'HOLM, S. A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, v. 6, n. 2, p. 65-70, 1979.',
 'HUNTER, J. D. Matplotlib: a 2D graphics environment. Computing in Science and Engineering, v. 9, n. 3, p. 90-95, 2007.',
 'KARCHER, C.; BUCHHEIT, M. On-court demands of elite handball, with special reference to playing positions. Sports Medicine, v. 44, n. 6, p. 797-814, 2014.',
 'KELLMANN, M. et al. Recovery and performance in sport: consensus statement. International Journal of Sports Physiology and Performance, v. 13, n. 2, p. 240-245, 2018.',
 'KENDALL, M. G.; SMITH, B. B. The problem of m rankings. The Annals of Mathematical Statistics, v. 10, n. 3, p. 275-287, 1939. DOI: 10.1214/aoms/1177732186.',
 'LEW, P. C. F.; PARSONS-SMITH, R. L.; LAMONT-MILLS, A. et al. Cross-cultural validation of the Malaysian Mood Scale and tests of between-group mood differences. International Journal of Environmental Research and Public Health, v. 20, n. 4, 3348, 2023.',
 'LOCHBAUM, M. et al. The Profile of Mood States and athletic performance: a meta-analysis of published studies. European Journal of Investigation in Health, Psychology and Education, v. 11, n. 1, p. 50-70, 2021.',
 'LUOJUMÄKI, R.; RUIZ, M. C.; ADIE, J. et al. Exploring mood profile clusters across physical activity level, gender and age. European Journal of Sport Science, 2026. DOI: 10.1002/ejsc.70131.',
 "McFADDEN, B. A.; WALKER, A. J.; BOZZINI, B. N. et al. Psychological and physiological changes in response to the cumulative demands of a women's division I collegiate soccer season. Journal of Strength and Conditioning Research, v. 35, n. 12, p. 3405-3414, 2021.",
 'McNEMAR, Q. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika, v. 12, n. 2, p. 153-157, 1947. DOI: 10.1007/BF02295996.',
 'MEEUSEN, R. et al. Prevention, diagnosis, and treatment of the overtraining syndrome: joint consensus statement of the European College of Sport Science and the American College of Sports Medicine. Medicine and Science in Sports and Exercise, v. 45, n. 1, p. 186-205, 2013.',
 'MORGAN, W. P. Selected psychological factors limiting performance: a mental health model. In: CLARKE, D. H.; ECKERT, H. M. (org.). Limits of human performance. Champaign: Human Kinetics, 1985. p. 70-80.',
 'MORGAN, W. P. Test of champions: the iceberg profile. Psychology Today, v. 14, p. 92-108, 1980.',
 'PAGE, E. B. Ordered hypotheses for multiple treatments: a significance test for linear ranks. Journal of the American Statistical Association, v. 58, n. 301, p. 216-230, 1963.',
 'PARSONS-SMITH, R. L.; TERRY, P. C.; MACHIN, M. A. Identification and description of novel mood profile clusters. Frontiers in Psychology, v. 8, 1958, 2017.',
 'PEREZ ARMENDARIZ, M. L.; SPYROU, K.; ALCARÁZ, P. E. Match demands of female team sports: a scoping review. Biology of Sport, v. 41, n. 3, p. 175-199, 2024.',
 'RAFNSSON, E. T.; MYKLEBUST, G.; VALDIMARSSON, Ö. et al. Association between training load, intensity, and overuse problems during pre-season in elite handball. Translational Sports Medicine, v. 4, n. 6, p. 858-865, 2021.',
 'REYNOSO-SÁNCHEZ, L. F.; PÉREZ-VERDUZCO, G.; CELESTINO SÁNCHEZ, M. A. et al. Competitive recovery-stress and mood states in Mexican youth athletes. Frontiers in Psychology, v. 11, 627828, 2021.',
 'ROHLFS, I. C. P. M. et al. Psychometric characteristics of the Brazil Mood Scale among youth and elite athletes using two response time frames. Sports, v. 11, n. 12, 244, 2023.',
 'ROHLFS, I. C. P. M.; NOCE, F.; WILKE, C. F. et al. Mood states, injury status, and countermovement jump performance in Brazilian high-performance athletes. Sports, v. 13, n. 9, 303, 2025.',
 'ROHLFS, I. C. P. M.; NOCE, F.; WILKE, C. F. Prevalence of specific mood profile clusters among elite and youth athletes at a Brazilian sports club. Sports, v. 12, n. 7, 195, 2024.',
 'ROHLFS, I. C. P. M.; ROTTA, T. M.; LUFT, C. D. B. et al. A Escala de Humor de Brunel (BRUMS): instrumento para detecção precoce da síndrome do excesso de treinamento. Revista Brasileira de Medicina do Esporte, v. 14, n. 3, p. 176-181, 2008.',
 'SAAL, C.; RHEINSBERG, P.; BAUMGART, C. How different defensive formations affect physical match demands in the German Handball Bundesliga. Frontiers in Sports and Active Living, v. 8, 1811523, 2026.',
 'SAHLI, H.; SAHLI, F.; SAIDANE, M. et al. Testing the psychometric properties of an Arabic version of the Brunel Mood Scale among physical education students. European Journal of Investigation in Health, Psychology and Education, v. 13, n. 8, p. 1539-1552, 2023.',
 'SAW, A. E.; MAIN, L. C.; GASTIN, P. B. Monitoring the athlete training response: subjective self-reported measures trump commonly used objective measures: a systematic review. British Journal of Sports Medicine, v. 50, n. 5, p. 281-291, 2016.',
 'SAWCZUK, T.; JONES, B.; SCANTLEBURY, S. et al. Influence of perceptions of sleep on well-being in youth athletes. Journal of Strength and Conditioning Research, v. 35, n. 4, p. 1066-1073, 2021.',
 'SHROUT, P. E.; FLEISS, J. L. Intraclass correlations: uses in assessing rater reliability. Psychological Bulletin, v. 86, n. 2, p. 420-428, 1979. DOI: 10.1037/0033-2909.86.2.420.',
 'TERRY, P. C.; LANE, A. M. Normative values for the profile of mood states for use with athletic samples. Journal of Applied Sport Psychology, v. 12, n. 1, p. 93-109, 2000.',
 'TERRY, P. C.; LANE, A. M.; LANE, H. J.; KEOHANE, L. Development and validation of a mood measure for adolescents. Journal of Sports Sciences, v. 17, n. 11, p. 861-872, 1999.',
 'TERRY, P. C.; PARSONS-SMITH, R. L. Mood profiling for sustainable mental health among athletes. Sustainability, v. 13, n. 11, 6116, 2021.',
 'TERRY, P. C.; PARSONS-SMITH, R. L.; SKURVYDAS, A. et al. Physical activity and healthy habits influence mood profile clusters in a Lithuanian population. Sustainability, v. 14, n. 16, 10006, 2022.',
 'TERRY, P. C.; PARSONS-SMITH, R. L.; VLACHOPOULOS, S. P. Mood profile clusters among Greek exercise participants and inactive adults. Sci, v. 6, n. 2, 18, 2024.',
 'TERRY, P. C.; SKURVYDAS, A.; LISINSKIENĖ, A. et al. Validation of a Lithuanian-language version of the Brunel Mood Scale: the BRUMS-LTU. International Journal of Environmental Research and Public Health, v. 19, n. 8, 4867, 2022.',
 'TERWEE, C. B. et al. Quality criteria were proposed for measurement properties of health status questionnaires. Journal of Clinical Epidemiology, v. 60, n. 1, p. 34-42, 2007.',
 'VIRTANEN, P. et al. SciPy 1.0: fundamental algorithms for scientific computing in Python. Nature Methods, v. 17, n. 3, p. 261-272, 2020.',
 'VLACHOPOULOS, S. P.; LANE, A. M.; TERRY, P. C. A Greek translation of the Brunel Mood Scale: initial validation among exercise participants and inactive adults. Sports, v. 11, n. 12, 234, 2023.',
 'WILCOXON, F. Individual comparisons by ranking methods. Biometrics Bulletin, v. 1, n. 6, p. 80-83, 1945. DOI: 10.2307/3001968.',
 'WILKE, C. F.; WANNER, S. P.; SANTOS, W. H. M. et al. Influence of faster and slower recovery-profile classifications, self-reported sleep, acute training load, and phase of the microcycle on perceived recovery in football players. International Journal of Sports Physiology and Performance, v. 15, n. 8, p. 1148-1156, 2020.',
]
