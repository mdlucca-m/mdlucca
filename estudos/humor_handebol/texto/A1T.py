# -*- coding: utf-8 -*-
"""Artigo 1: descritivo-analítico."""
TITULO=("Dois choques e um platô: o comportamento das dimensões do humor no microciclo terminal de "
        "pré-temporada em atletas de handebol de elite")
SUB=("Estudo observacional longitudinal com coletas diárias pré e pós, tratamento de séries por "
     "suavização, derivadas e piso de ruído, e limiares individuais de mudança")

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
"o deslocamento total o superou. Quatro das seis subescalas concentraram entre 41,6% e 69,3% das respostas no valor mínimo. Em escala normativa, a fadiga situou-se em 57,2 e a raiva em 55,6, ao passo que o vigor caiu a 44,1 e a tensão a "
"41,7. O vigor recuou 4,33 pontos contra um piso de 0,61 e a fadiga avançou 4,28 contra 0,76; as sete séries superaram "
"o respectivo piso, com razões que vão de 7,1, no vigor, a 1,6, na depressão. As transições de choque concentraram-se "
"nas duas extremidades da semana e deixaram um platô de quatro dias entre elas. O perfil iceberg recuou de "
"37,0% para 19,0% e a barbatana de tubarão avançou de 11,1% para 28,6%; a faixa de risco passou de 22,2% para "
"52,4%. O teste formal de cruzamento reconheceu inversão estabelecida entre vigor e fadiga no quinto dia e "
"entre vigor e perturbação total no sexto, mas recusou a inversão aparente entre tensão e raiva. A base "
"passou por duas auditorias: a de procedência, que fixou a unidade de análise no par atleta-dia, e a de "
"qualidade, que reconstruiu os escores por fórmula sem divergência nas 4.113 conferências e não "
"encontrou valor fora do domínio das escalas. Conclui-se "
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
"psicológico acompanha o êxito esportivo, e a representação gráfica desse bem-estar, com vigor acima da média normativa e as cinco dimensões negativas "
"abaixo dela, recebeu o nome de perfil iceberg (MORGAN, 1980). O "
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

"Uma segunda lacuna, de natureza métrica, atravessa a primeira. Os instrumentos de autorrelato são hoje o "
 "método mais adotado no monitoramento de atletas, por serem baratos, rápidos e aplicáveis todos os dias, e "
 "a sua contribuição documentada vai além do escore: eles organizam a conversa entre o atleta e a comissão "
 "técnica e permitem que informações relevantes sejam reveladas fora do contato presencial (SAW; MAIN; "
 "GASTIN, 2015). A contrapartida é a adesão, que costuma ser o gargalo prático desse tipo de instrumento e "
 "que não melhora apenas com educação sobre a sua utilidade (McGUIGAN; HASSMÉN; ROSIĆ, 2022).",
 "Ora, decidir sobre um atleta a partir de um escore diário exige saber quanto desse escore é ruído. A "
 "literatura de monitoramento resolveu essa pergunta há duas décadas, com um conjunto de limiares que "
 "raramente aparece nos estudos de humor no esporte: o erro típico da medida, a menor mudança considerada "
 "relevante e a razão entre os dois, que expressa a aptidão do instrumento para detectar o que importa "
 "(HOPKINS, 2000; HOPKINS; SCHABORT; HAWLEY, 2001). Aplicados a testes físicos, esses limiares mostram que "
 "muitos instrumentos consagrados não distinguem a mudança relevante do próprio erro (LINDBERG et al., 2022; "
 "GARRETT et al., 2020). Aplicados a escalas de humor com coleta diária, praticamente não existem.",
 "A relevância prática dessas lacunas não é conjetural. A revisão de escopo de Timmerman, Abbiss e Lawler (2024) "
 "reuniu quarenta e dois estudos sobre a perspectiva de treinadores e de comissões técnicas e registrou três "
 "motivos recorrentes para monitorar: reduzir lesão e doença, orientar o programa de treino e sustentar o "
 "rendimento. Os mesmos profissionais admitem que nenhuma abordagem científica é perfeita e que o dado só adquire "
 "sentido quando se integra à conversa com o atleta. Do outro lado dessa relação, Woolmer, Morris e Noon (2025) "
 "verificaram que a adesão do jogador depende menos da sofisticação do instrumento do que da devolutiva que ele "
 "recebe. Lobo (2026) formula o impasse em termos gerais ao situar a analítica esportiva como cadeia que só se "
 "completa quando a captura do dado desemboca em decisão interpretável. Sucede que devolver ao atleta uma oscilação "
 "indistinguível do erro da medida corrói justamente a confiança de que depende a adesão. Um limiar declarado, "
 "portanto, não constitui refinamento estatístico: é condição para que o monitoramento diário sustente decisão "
 "defensável.",  "Do encontro desses problemas nasce o presente estudo. De um lado, o handebol de elite impõe, na semana que antecede a "
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
 "fronteira às quatro da manhã, e não pela data autorreferida pelo respondente. Essa coluna acumula datas de nascimento e erros de digitação, pois cinquenta e cinco registros trazem ano "
 "anterior a 2020, de modo que oitenta e quatro dos 457 registros seriam inutilizáveis por ela: sessenta e oito caem fora da semana de "
 "estudo e dezesseis estão em branco. Entre os registros do microciclo, oitenta e oito divergem do dia obtido "
 "pelo carimbo. A fronteira às quatro da manhã devolve ao primeiro dia seis registros lançados entre "
 "meia-noite e uma da manhã do dia seguinte, todos de atletas que já haviam respondido na noite anterior.",
 "Segunda: quatro registros receberam o rótulo «não identificado» na coluna de nome padronizado, o que criaria "
 "um vigésimo oitavo atleta inexistente. Dois foram devolvidos ao respondente por correspondência exata no "
 "dicionário de variantes de nome e dois pelo nome curado, no mesmo carimbo de data e hora, de uma base "
 "derivada. O elenco é, portanto, de vinte e sete atletas.",
 "Terceira: a unidade de análise passou a ser declarada. Quatro unidades circulavam nas versões anteriores: o registro isolado, o par formado pelo primeiro e pelo "
 "último registro do dia, o par atleta-dia e a subamostra dos atletas com medida no primeiro e no sétimo dia. Elas produzem, sobre exatamente os mesmos "
 "dados e com a mesma classificação, variações do perfil iceberg entre o primeiro e o sétimo dia que vão de "
 "0,6 a 18,0 pontos percentuais. A Figura 2 apresenta essa comparação, e o Quadro 1 documenta a linhagem.",
 "A essa primeira passagem, dedicada à procedência do número, seguiu-se uma segunda, dedicada à qualidade do "
 "dado em si e descrita na subseção seguinte. A distinção importa: a primeira responde de onde vem cada "
 "valor, e a segunda, se o valor está correto. As duas fontes de erro estavam confundidas nas versões "
 "anteriores, e a segunda auditoria descartou uma delas."]),
("Qualidade dos dados: completude, padronização e triagem de discrepantes",[
 "A segunda passagem de auditoria desceu ao nível do item do formulário. Cada escore de subescala, a "
 "perturbação total do humor e os escores das escalas auxiliares foram reconstruídos por fórmula a partir dos "
 "itens que os compõem e confrontados, linha a linha, com as colunas já computadas na base de origem. As "
 "4.113 conferências não apresentaram divergência alguma. O resultado tem consequência direta sobre a "
 "interpretação das divergências entre versões: elas decorrem da unidade de análise, e não de erro de "
 "pontuação, hipótese que agora está eliminada.",
 "A completude foi medida em três recortes. No nível do item, nenhuma célula está ausente entre as 20.108 "
 "respostas de instrumento, porque o formulário exigia resposta em cada item; quem respondeu, respondeu "
 "tudo. A falta, portanto, não é de item, e sim de comparecimento. Na grade que cruza atleta e dia, a "
 "cobertura parte de vinte e sete atletas no primeiro dia e recua a vinte e um no quarto e no sétimo, o que "
 "corresponde a setenta e oito por cento do elenco. É essa queda, e não a ausência de resposta, que obriga a "
 "declarar o denominador de cada contraste.",
 "O protocolo previa uma coleta no primeiro dia e duas nos demais, mas o número observado de registros por par "
 "atleta-dia varia de um a seis. A conferência dos carimbos de data e hora, apresentada adiante, localiza de quatro a dez janelas de coleta do elenco em cada dia de D2 a D7, e não duas. Daí decorre a regra de composição adotada: o primeiro registro do dia responde pelo estado de pré e o último "
 "pelo de pós, e a média dos dois fornece o valor diário; os registros intermediários permanecem na base, mas não "
 "compõem esse valor. No primeiro dia, de coleta única, vale a primeira resposta de cada atleta. Assim, 285 dos "
 "456 registros compõem os valores diários, e 171 são excedentes de protocolo.",
 "A aderência ao protocolo de coleta foi conferida registro a registro pelo carimbo de data e hora. Nenhum dos "
 "456 registros cai fora do intervalo que vai das quatro da manhã de 21 de abril às quatro da manhã de 28 de "
 "abril. O agrupamento dos carimbos do elenco por lacuna superior a vinte e cinco minutos revela, porém, estrutura "
 "distinta da prevista: o primeiro dia distribui-se por uma janela às 20h42 e outra a partir das 22h59, e os "
 "demais apresentam de quatro a dez janelas cada. Quarenta registros repetem o mesmo atleta dentro de uma "
 "única janela do elenco, e vinte e seis situam-se a menos de trinta minutos de outro registro do mesmo atleta no "
 "mesmo dia. Cinquenta e nove dos 139 pares atleta-dia entre o segundo e o sétimo dia têm o seu primeiro registro "
 "ao meio-dia ou depois, sem qualquer registro anterior naquele dia; nesses casos o primeiro registro é o de pré, "
 "atrasado em relação à hora prevista. É essa constatação que dispensa a regra de composição de qualquer hipótese "
 "de relógio.",  "A padronização das variáveis categóricas foi verificada por comparação de cada valor com a sua "
 "chave canônica, obtida pela remoção de acento, caixa e espaço redundante. O nome digitado em campo livre "
 "apresenta sessenta e sete grafias para quarenta e oito nomes canônicos, quinze deles com mais de uma forma; "
 "é por isso que a identidade do respondente provém da coluna padronizada, e não do texto livre. As demais "
 "variáveis categóricas do formulário não apresentam variante de grafia.",
 "A triagem de valores discrepantes obedeceu a uma ordem. Primeiro a verificação de domínio: valor fora do "
 "intervalo admissível da escala é erro, e não discrepância. Depois três critérios de dispersão: a cerca de Tukey, o escore z e o escore z modificado, este último "
 "construído sobre a mediana e o desvio absoluto "
 "mediano e, por isso, resistente à contaminação pelo próprio valor extremo. A ordem importa porque os três "
 "critérios de dispersão falham em subescala com efeito de piso, condição que se verifica nesta amostra e "
 "cujo tratamento é relatado na seção de resultados."]),
("Instrumentos",[
 "Aplicou-se a Escala de Humor de Brunel em sua versão brasileira (ROHLFS et al., 2008), composta por vinte e "
 "quatro itens distribuídos em seis subescalas de quatro itens (tensão, depressão, raiva, vigor, fadiga e confusão), respondidos em escala de "
 "cinco pontos, de zero a quatro, com amplitude de zero a dezesseis por "
 "subescala. A instrução temporal solicitou ao atleta que considerasse como se sentia naquele momento. A "
 "perturbação total do humor resulta da soma das cinco subescalas negativas subtraída do vigor. Todas as "
 "subescalas foram recalculadas a partir dos vinte e quatro itens e conferidas contra as colunas já "
 "computadas na planilha de origem, sem divergência em nenhuma das 2.736 células conferidas. Estendida às "
 "nove variáveis derivadas da base, incluída a perturbação total do humor, a conferência alcança 4.113 "
 "células e mantém a ausência de divergência.",
 "Para permitir comparação com a norma e classificação nos seis perfis, cada subescala foi convertida em "
 "escore T por padronização contra parâmetros normativos de amostras atléticas, com média cinquenta e "
 "desvio-padrão dez, recuperados por inversão das faixas de escore T publicadas."]),
("Confiabilidade do instrumento neste elenco",[
 "A validação brasileira do instrumento é condição necessária, não suficiente: a consistência interna é "
 "propriedade da resposta de uma amostra, e não do questionário em abstrato. Estimaram-se, por isso, o alfa "
 "de Cronbach e o ômega de McDonald de cada subescala sobre os registros deste elenco, com intervalo de "
 "confiança por reamostragem agrupada por atleta, uma vez que os registros não são independentes entre si.",
 "Complementaram-se essas estimativas com a correlação item-total corrigida, o alfa resultante da remoção de "
 "cada item e o percentual de respostas no piso da escala. Verificou-se ainda o escalonamento multitraço, "
 "que compara a correlação de cada item com a própria subescala, corrigida, e com cada uma das demais: cada "
 "comparação em que o item se aproxima mais da própria subescala conta como sucesso de escalonamento."]),
("Classificação nos seis perfis de humor",[
 "A classificação seguiu a proposta de Parsons-Smith, Terry e Machin (2017). Aplicou-se agrupamento por "
 "k-médias com seis centros, semeados nos centroides canônicos, de modo que a solução não dependesse de "
 "inicialização aleatória; os agrupamentos resultantes foram reancorados aos rótulos originais por atribuição "
 "ótima. Para leitura clínica, os seis perfis foram agregados em três faixas: a favorável reúne o iceberg; a "
 "neutra, a superfície e o submerso; e a de risco, a barbatana de tubarão, o iceberg invertido e o Everest "
 "invertido, configurações que a literatura associa a maior vulnerabilidade (TERRY; PARSONS-SMITH, 2021)."]),
("Tratamento de séries: suavização, derivadas e piso de ruído",[
 "O núcleo metodológico deste estudo é o tratamento aplicado às séries diárias, tanto às médias das "
 "subescalas quanto às prevalências dos perfis. O procedimento tem quatro passos encadeados, descritos a "
 "seguir com detalhe suficiente para reprodução independente.",

 "O primeiro passo estima a incerteza de cada ponto. Para séries de médias, o erro-padrão do dia d é o "
 "desvio-padrão amostral daquele dia dividido pela raiz do número de respondentes do dia, "
 "EP(d) = s(d) ÷ √n(d), com s calculado sobre os n(d) valores diários disponíveis. Para séries de "
 "prevalência, o erro-padrão decorre da fórmula binomial, EP(d) = √[p(d)(1 − p(d)) ÷ n(d)], em que p(d) é a "
 "proporção de pares atleta-dia classificados no perfil naquele dia. O piso de ruído da série é a média "
 "aritmética dos sete erros-padrão, piso = (1/7)·Σ EP(d), e responde a uma pergunta simples: qual é a "
 "magnitude típica da oscilação que a amostragem, por si só, produz nesta série? O piso é, portanto, uma "
 "quantidade da própria série, e não um valor importado da literatura ou fixado por convenção.",

 "O segundo passo suaviza a série. Adotou-se o filtro binomial de três pontos, também chamado filtro "
 "1-2-1, cujo núcleo é o vetor de pesos [1/4, 1/2, 1/4], obtido pela normalização da terceira linha do "
 "triângulo de Pascal. Cada ponto interno da série é substituído pela combinação "
 "ŷ(d) = 0,25·y(d − 1) + 0,50·y(d) + 0,25·y(d + 1), e o primeiro e o sétimo dias permanecem com o valor "
 "observado. Três propriedades motivaram a escolha. A soma unitária dos pesos preserva o nível da série, de "
 "modo que a suavização não introduz viés na média. A simetria do núcleo anula o deslocamento de fase, de "
 "modo que um evento não migra no tempo por efeito do filtro, o que seria fatal em um estudo cujo objeto é "
 "justamente localizar quando a mudança ocorre. E a resposta em frequência do núcleo, H(ω) = cos²(ω/2), "
 "anula-se exatamente na frequência de Nyquist, ω = π, que corresponde à componente que alterna a cada dia; "
 "o filtro remove por construção a oscilação de um dia para o outro, que é a assinatura do ruído amostral em "
 "série diária, e atenua pouco as componentes lentas, que são o objeto de interesse.",

 "Duas decisões acessórias sobre o filtro merecem registro porque afetam resultados. A primeira é o "
 "tratamento das bordas: não se aplicou preenchimento por reflexão, por repetição do extremo ou por qualquer "
 "outra extrapolação, e os dias inicial e final conservam o valor observado. A razão é substantiva, e não de "
 "conveniência: o deslocamento total da série, que fundamenta o veredito de sinal, é a diferença entre esses "
 "dois pontos, e qualquer preenchimento os contaminaria com informação inventada. A segunda é a largura do "
 "núcleo. Um filtro de cinco pontos consumiria quatro dos sete dias em bordas e deixaria apenas três pontos "
 "suavizados, e o ajuste polinomial local do tipo Savitzky-Golay, embora preserve melhor a amplitude de "
 "picos, é instável nas extremidades de séries curtas, precisamente onde este estudo concentra a leitura. "
 "Pela mesma razão, descartou-se a média móvel simples de três pontos, cujo núcleo [1/3, 1/3, 1/3] tem "
 "resposta em frequência que não se anula em Nyquist e ainda inverte o sinal de parte da banda alta. O mesmo "
 "filtro, com os mesmos parâmetros, foi aplicado às onze séries de médias e às nove séries de prevalência, "
 "sem ajuste por variável.",

 "O terceiro passo calcula as derivadas discretas da série suavizada. A primeira derivada é a diferença "
 "progressiva entre dias consecutivos, Δ(d) = ŷ(d + 1) − ŷ(d), o que produz seis valores e mede a velocidade "
 "da mudança. A segunda é a diferença entre velocidades consecutivas, Δ²(d) = Δ(d + 1) − Δ(d), o que produz "
 "cinco valores e mede a aceleração. Ambas foram expressas em unidades do piso de ruído da própria variável, "
 "pela divisão de cada valor pelo piso, o que torna comparáveis subescalas de amplitude e de dispersão "
 "distintas. Chama-se transição de choque aquela cuja primeira derivada, em valor absoluto e em unidades "
 "originais, supera o piso, isto é, |Δ(d)| > piso. Chama-se ponto de inflexão a abscissa em que a segunda "
 "derivada muda de sinal, localizada por interpolação linear entre os dois dias que a cercam pela expressão "
 "d + |Δ²(d)| ÷ (|Δ²(d)| + |Δ²(d + 1)|), o que devolve uma posição em fração de dia.",

 "O quarto passo emite o veredito. Declara-se variação real, ou sinal, quando o deslocamento total entre o "
 "primeiro e o sétimo dia supera, em valor absoluto, o piso de ruído; caso contrário, atribui-se a oscilação "
 "à flutuação amostral. Reporta-se também a razão entre o deslocamento e o piso, que ordena as variáveis por "
 "folga em relação ao próprio ruído e informa mais do que o veredito binário. O mesmo princípio governa o "
 "teste de cruzamento entre duas séries: calcula-se a série da diferença entre as duas séries suavizadas e o "
 "limiar combinado, definido como a raiz da soma dos quadrados dos dois pisos, √(piso²ᴬ + piso²ᴮ), expressão "
 "que supõe independência entre os dois erros; o ponto de cruzamento é a abscissa em que a diferença muda de "
 "sinal, obtida pela mesma interpolação linear; e a inversão só é declarada estabelecida quando a diferença, "
 "em valor absoluto, ultrapassa o limiar tanto no primeiro quanto no sétimo dia. Do contrário, o achado é "
 "classificado como divergência, categoria que reconhece a troca de posição sem lhe atribuir estatuto de "
 "resultado.",

 "Cabe uma ressalva sobre o alcance do piso binomial. Em prevalências próximas de zero, o produto entre a "
 "proporção e o seu complemento tende a zero e o erro-padrão encolhe artificialmente, o que rebaixa o piso e "
 "torna o critério permissivo. Séries de prevalência muito baixa exigem, por isso, leitura cautelosa, e o "
 "texto assinala explicitamente onde essa condição ocorre.",
]),
("Limiares de mudança: o piso do grupo, o erro típico e a menor mudança relevante",[
 "O piso de ruído descrito acima responde a uma pergunta de grupo: a média diária se moveu mais do que a "
 "oscilação que a amostragem produz? A comissão técnica, porém, decide sobre um atleta. Para essa segunda "
 "pergunta acrescentaram-se três limiares consagrados na literatura de monitoramento (HOPKINS, 2000; "
 "HOPKINS; SCHABORT; HAWLEY, 2001).",
 "O erro típico é o desvio-padrão das diferenças entre medidas repetidas do mesmo atleta, dividido pela raiz "
 "de dois. Calculou-se a partir das diferenças entre dias consecutivos, de modo que a estimativa incorpora a variação biológica de um dia para o outro, que constitui o ruído contra o qual o monitoramento diário de fato "
 "opera. A menor mudança relevante adotou o critério de distribuição usual, dois décimos do desvio-padrão "
 "entre atletas, e a mudança mínima detectável correspondeu a 1,96 vezes a raiz de dois vezes o erro típico. "
 "A razão entre a menor mudança relevante e o erro típico expressa a aptidão do instrumento para o "
 "monitoramento individual: valores iguais ou superiores à unidade indicam que o instrumento distingue a "
 "mudança que importa do ruído que a acompanha (LINDBERG et al., 2022; GARRETT et al., 2020).",
 "Aos limiares de distribuição somou-se um limiar ancorado em critério externo. Tomou-se como âncora a "
 "entrada na faixa de risco entre a manhã e a noite do mesmo dia, restrita aos pares que amanhecem fora "
 "dela, e procurou-se o valor de variação que maximiza o índice de Youden na curva de característica de "
 "operação. O limiar assim obtido responde a uma pergunta que o critério de distribuição não responde: qual "
 "variação, nesta amostra, acompanha a transição clínica que interessa?"]),
("Análise estatística e processamento computacional",[
 "Toda a análise foi executada em Python 3.11.15, em ambiente Linux. A cadeia parte da planilha de origem e "
 "termina nos arquivos de saída sem etapa manual intermediária, e reproduz-se pela execução de um único "
 "comando, que encadeia oito etapas: construção da base canônica, classificação nos perfis, análises "
 "descritiva e inferencial, montagem do banco único, coleta do acervo de planilhas e casamento de "
 "referências, auditoria de qualidade e reconferência, modelagem preditiva e, por fim, geração das figuras e "
 "dos documentos. As versões das bibliotecas são declaradas adiante porque resultados numéricos de "
 "bootstrap e de modelos mistos dependem delas.",

 "A importação empregou o pacote openpyxl 3.1.5, com a planilha aberta em modo somente leitura e com leitura "
 "de valores em cache, o que devolve o resultado das fórmulas e não a sua expressão. Percorreram-se as "
 "linhas da aba do formulário diário uma a uma, com extração por posição de coluna. As respostas em escala "
 "Likert foram convertidas por expressão regular que captura o dígito inicial do rótulo, de modo que "
 "variantes de redação do mesmo nível produzam o mesmo número. A identidade do respondente foi resolvida "
 "pela coluna padronizada, com uma chave canônica obtida por normalização Unicode na forma NFKD, remoção de "
 "diacríticos, conversão para caixa baixa e colapso de espaços repetidos; um dicionário de variantes, "
 "mantido na própria planilha, resolve as grafias divergentes. A substituição dos nomes pelos códigos "
 "anônimos de A01 a A27 ocorre dentro dessa mesma rotina, antes de qualquer gravação em disco, de modo que "
 "nenhum nome trafega para as etapas seguintes nem aparece em arquivo intermediário. O dia de cada registro "
 "deriva do carimbo de data e hora, com fronteira às quatro da manhã, e não da data autorreferida.",

 "A manipulação numérica utilizou o NumPy 2.4.6 (HARRIS et al., 2020): conversão para arranjos de ponto "
 "flutuante, agregação por atleta e por dia com tratamento explícito de ausentes, padronização em escore T, "
 "aplicação do filtro binomial, cálculo das derivadas e dos pisos de ruído. Os testes de hipótese utilizaram "
 "o módulo stats do SciPy 1.17.1 (VIRTANEN et al., 2020), com as seguintes funções: shapiro para a "
 "normalidade, friedmanchisquare para a comparação global entre os sete dias, wilcoxon para os contrastes "
 "pareados, ttest_rel para o teste t de amostras dependentes, chi2_contingency para as tabelas de "
 "contingência, spearmanr e pearsonr para as associações, levene para a homogeneidade de variâncias, "
 "mannwhitneyu e kruskal para as comparações entre grupos independentes, skew e kurtosis para os momentos de "
 "terceira e quarta ordem, sem para o erro-padrão da média e rankdata para os postos. As distribuições norm, "
 "chi2, f, t e beta forneceram os valores críticos e as probabilidades de cauda. O teste L de Page, o Q de "
 "Cochran, o teste de McNemar e a correção de Holm não integram a biblioteca e foram implementados "
 "diretamente a partir das respectivas definições, no próprio código depositado.",

 "A modelagem de efeitos mistos utilizou o statsmodels 0.15.0, pela interface de fórmulas, com intercepto "
 "aleatório por atleta. O modelo de tendência foi ajustado por máxima verossimilhança restrita, apropriada "
 "para a estimação de componentes de variância; os modelos auxiliares de ausência e de carga foram ajustados "
 "por máxima verossimilhança plena, condição necessária para comparar especificações com efeitos fixos "
 "distintos. A programação linear da carga empregou a rotina linprog do SciPy, com o método dos pontos "
 "interiores da biblioteca HiGHS. Os intervalos de confiança que não admitem forma fechada foram obtidos por "
 "reamostragem bootstrap agrupada por atleta, isto é, com sorteio de atletas com reposição, e não de linhas, "
 "o que respeita a dependência entre observações do mesmo respondente; o gerador de números pseudoaleatórios "
 "foi instanciado com semente fixa em cada rotina, o que torna os intervalos reproduzíveis dígito a dígito. "
 "Adotaram-se 1.500 replicações para o erro típico, 800 para os coeficientes de consistência interna e 500 "
 "para as áreas sob a curva da modelagem preditiva.",

 "A confiabilidade das medidas repetidas foi estimada por correlação intraclasse de via única, com o "
 "coeficiente de medida média obtido pela fórmula de Spearman-Brown (SHROUT; FLEISS, 1979), acompanhada do "
 "erro-padrão de medida e da mínima variação detectável. O efeito de piso foi avaliado pelo critério de "
 "Terwee et al. (2007). Adotou-se alfa de cinco por cento em todas as decisões, com correção de Holm sempre "
 "que uma família de comparações foi examinada em conjunto.",

 "Os resultados intermediários de cada rotina são gravados em arquivos JSON, e um script de consolidação os "
 "carrega em um banco SQLite de camada tripla: a camada canônica guarda registros, pares atleta-dia e pares "
 "pré-pós; a camada de resultados guarda, em formato longo, cada estatística com a sua variável, o seu "
 "recorte, a sua unidade de análise e a rotina que a produziu; e a camada de acervo guarda a proveniência "
 "das planilhas de origem, aba a aba e célula a célula. O banco reúne vinte e seis tabelas de conteúdo e quatro visões, e um "
 "índice de texto completo do tipo FTS5 permite localizar qualquer número pelo termo que o descreve. Essa "
 "arquitetura é o que torna possível auditar cada valor do texto contra o objeto que o gerou.",

 "As figuras foram produzidas com matplotlib 3.11.1 (HUNTER, 2007) a partir dos mesmos arquivos JSON, sem "
 "reentrada de dados, e gravadas em mapa de bits a 300 pontos por polegada. A exportação do manuscrito "
 "utilizou a biblioteca python-docx 1.2.0. Um módulo comum fixa a formatação editorial, com página A4, "
 "margens de três centímetros à esquerda, ao topo e à direita e de dois centímetros ao pé, fonte Times New "
 "Roman de doze pontos, espaçamento de uma linha e meia, alinhamento justificado e recuo de primeira linha "
 "de 1,25 centímetro; contadores automáticos numeram tabelas, figuras e quadros na ordem de inserção. Todos "
 "os valores numéricos impressos no texto e nas tabelas são lidos dos arquivos JSON no momento da montagem e "
 "formatados por função única, com vírgula decimal e sinal menos tipográfico. Nenhum número foi digitado à "
 "mão no manuscrito, o que elimina por construção a classe de erro mais comum em textos com muitas "
 "estatísticas.",

 "A reprodutibilidade foi verificada por um segundo caminho de código, independente do primeiro, que parte "
 "do item do formulário e reconstrói cada escore por fórmula, e cujo resultado é confrontado com o do "
 "caminho canônico em sessenta e cinco quantidades reportadas neste artigo.",
]),
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
"Em primeiro lugar, a assimetria é acentuada nas subescalas negativas: a depressão apresenta assimetria de 4,04 e "
"curtose de 19,64, e a confusão, 3,78 e 18,03. Em segundo lugar, a mediana coincide com o valor mínimo da escala em três subescalas, depressão, raiva e confusão, o que desloca a "
"informação para as caudas. Em terceiro lugar, a média aparada a vinte por cento afasta-se sistematicamente da "
"média aritmética nas mesmas subescalas: a depressão cai de 0,94 para 0,23, a raiva de 1,61 para 0,65 e a "
"confusão, de 0,52 para 0,12. Nenhuma das sete variáveis passa no teste de Shapiro-Wilk ao nível de cinco por cento; o vigor é a que mais se aproxima da normalidade (W = 0,983; p = 0,035) e a depressão a que mais dela se afasta "
"(W = 0,485; p < 0,001). Esse conjunto fundamenta a opção não paramétrica adotada na descrição.",
"O efeito de piso, apresentado na Tabela 2, ultrapassa com folga o limite de quinze por cento proposto por "
"Terwee et al. (2007) em quatro das seis subescalas: 69,3% das respostas de confusão, 61,4% das de depressão, 51,8% das de raiva e "
"41,6% das de tensão concentram-se no valor zero. O vigor e a fadiga escapam a essa condição, com 6,0% e 8,4%. A consequência prática é direta: as quatro subescalas com piso severo possuem "
"margem para subir e quase nenhuma para descer, e qualquer interpretação de queda nessas dimensões deve "
"reconhecer a assimetria do instrumento.",
"A padronização contra a norma de atletas reposiciona o grupo. A fadiga situa-se em 57,2 e a raiva em 55,6, ambas acima da média normativa; o vigor cai a 44,1, a confusão a "
"44,9 e a tensão a 41,7; a depressão permanece exatamente sobre a linha da norma, em 50,0. O grupo, portanto, não exibe o perfil iceberg clássico: combina "
"baixa tensão e baixa confusão com fadiga e raiva elevadas e vigor rebaixado, configuração que se aproxima da "
"barbatana de tubarão descrita por Parsons-Smith, Terry e Machin (2017).",
"A confiabilidade das medidas repetidas ao longo da semana revela heterogeneidade expressiva. A depressão apresenta a maior proporção de variância atribuível a diferenças estáveis entre atletas (CCI de "
"medida única de 0,666) e a raiva a menor (0,342). A leitura substantiva é que a raiva opera predominantemente "
"como estado, sensível à situação do dia, ao passo que a depressão se comporta como característica relativamente "
"estável do respondente. A mínima variação detectável acompanha essa lógica: 2,52 pontos para a confusão, 5,77 "
"para a raiva e 15,78 para a perturbação total, valores que estabelecem o patamar abaixo do qual uma "
"mudança individual não se distingue do erro de medida.",
]
R2=[
"A Figura 4 acompanha as trajetórias das seis subescalas em escore T, com o dia sombreado conforme o "
"estímulo, e apresenta o resultado do teste de tendência. A Tabela 3 documenta os testes.",
"O teste L de Page, que especifica a alternativa como ordenada do primeiro ao sétimo dia e por isso ganha "
"potência sobre o de Friedman, identifica tendência monotônica em quatro variáveis. O vigor decresce (z = −4,05; "
"p < 0,001), a fadiga cresce (z = 3,48; p < 0,001), a tensão decresce (z = −3,04; p = 0,002) e a confusão "
"decresce (z = −2,18; p = 0,029). A raiva não apresenta tendência ordenada (z = −1,13; p = 0,257), e o resultado "
"merece registro pela razão oposta à que se poderia supor: a comparação direta entre o primeiro e o sétimo dia "
"mostra elevação de 0,98 ponto, mas a trajetória cai até o quinto dia e sobe abruptamente depois, de modo que a "
"soma ponderada de postos, ao pressupor monotonia, não capta um movimento que se dá em duas direções. Nem a "
"depressão (z = 1,13; p = 0,257) nem a perturbação total (z = 1,39; p = 0,163) apresentam tendência ordenada, "
"ainda que ambas se desloquem entre os extremos da semana.",
"O teste de Friedman, restrito aos dezenove atletas com registro completo nos sete dias, rejeita a hipótese de "
"igualdade entre os dias para cinco das sete variáveis: o vigor (χ² = 28,50; p < 0,001; W = 0,250), a confusão "
"(χ² = 22,29; p = 0,001; W = 0,196), a fadiga (χ² = 19,47; p = 0,003; W = 0,171), a perturbação total (χ² = "
"14,61; p = 0,024; W = 0,128) e a tensão (χ² = 14,18; p = 0,028; W = 0,124). A raiva não o alcança (p = 0,487) e "
"a depressão dele se afasta (p = 0,815). Os coeficientes de concordância permanecem baixos: mesmo o vigor explica "
"um quarto da variância dos postos. Convém registrar que essa análise "
"descarta oito dos vinte e sete atletas, e que o segundo artigo desta série examina o custo dessa exigência.",
"O contraste direto entre a linha de base e a véspera da estreia, pelo teste de Wilcoxon sobre os vinte e um "
"atletas com as duas medidas, confirma dois deslocamentos que sobrevivem à correção de Holm para as seis "
"comparações com a linha de base: o vigor recua 4,52 pontos (p = 0,0001; p ajustado = 0,0006; r = 0,840), a fadiga avança 4,33 pontos (p = 0,0005; "
"p ajustado = 0,003; r = 0,759), a perturbação total avança 8,21 pontos (p = 0,004; p ajustado = 0,018; r = "
"0,637) e a tensão recua 1,31 ponto (p = 0,007; p ajustado = 0,042; r = 0,589). A confusão recua 0,71 ponto e "
"alcança significância bruta (p = 0,013), que resvala no ajuste (p = 0,051). A depressão (p = 0,386) e a raiva (p "
"= 0,875) permanecem distantes do limiar.",
]
R3=[
"A Figura 5 decompõe cada série em três camadas sobrepostas: a série observada com o respectivo erro-padrão "
"diário, a série suavizada pelo filtro binomial e a banda do piso de ruído em torno do valor basal. A Tabela 4 "
"registra os parâmetros.",
"O piso de ruído varia de 0,22 ponto, na confusão, a 1,88 ponto, na perturbação total, e essa amplitude justifica "
"por si só o procedimento: uma variação de meio ponto significa coisas opostas nas duas variáveis. As sete séries "
"superam o respectivo piso e recebem o veredito de sinal, mas a folga com que o fazem separa-as em três grupos. O "
"vigor desloca-se 4,33 pontos contra um piso de 0,61, isto é, 7,1 vezes o piso, e a fadiga 4,28 contra 0,76, ou "
"5,6 vezes; ambas ocupam o extremo superior sem ambiguidade. A perturbação total desloca-se 8,51 contra 1,88, ou "
"4,5 vezes, e a tensão 1,26 contra 0,36, ou 3,5 vezes. No extremo inferior situam-se a confusão, com 0,55 contra "
"0,22, ou 2,5 vezes, a raiva, com 0,98 contra 0,51, ou 1,9 vez, e a depressão, com 0,73 contra 0,44, ou 1,6 vez.",
"As transições de choque concentram-se nas duas extremidades da semana. O vigor apresenta choque em três "
"passagens, do primeiro para o segundo dia, do segundo para o terceiro e do sexto para o sétimo; a fadiga e a "
"perturbação total, na primeira e na última dessas passagens; a tensão, apenas na saída do dia basal; a confusão, "
"nas duas primeiras; e a raiva, nas duas últimas. A depressão não apresenta transição alguma que supere o piso, e "
"é a única nessa condição. O padrão que emerge é o de deslocamento por choques nas pontas, com platô "
"intermediário, e não o de deriva lenta e uniforme. Os pontos de inflexão reforçam essa leitura: situam-se entre "
"o terceiro e o quinto dia na maioria das variáveis (3,15 na raiva, 3,31 na perturbação total, 3,66 no vigor, "
"3,69 na fadiga, 4,34 na tensão e 4,96 na confusão), o que localiza no miolo da semana a mudança de regime da "
"aceleração.",
]
R4=[
"A Figura 6 expressa as duas derivadas em unidades do piso de ruído de cada variável, o que permite "
"compará-las apesar das diferenças de amplitude e dispersão. A moldura destaca as células cujo valor absoluto "
"supera uma unidade de piso.",
"A primeira derivada mostra que a velocidade se concentra em duas colunas. Na passagem do primeiro para o segundo "
"dia, o vigor cai 3,64 pisos, a confusão cai 2,25, a fadiga sobe 2,10, a perturbação total sobe 1,73 e a tensão "
"cai 1,39. Na passagem do sexto para o sétimo dia, a raiva sobe 1,74 piso, a perturbação total sobe 1,67, a "
"fadiga sobe 1,63 e o vigor cai 1,78. Entre esses dois extremos, quase todas as velocidades permanecem abaixo de "
"uma unidade de piso, o que confirma o platô. Os dois choques têm naturezas distintas: o primeiro decorre da transição de um dia de carga mínima "
"para o primeiro dia de treino intervalado e afeta simultaneamente o vigor, a tensão e a confusão; o segundo "
"antecede a estreia competitiva e mobiliza a raiva e a fadiga, sem repercussão equivalente sobre a tensão, "
"que continua a cair.",
"A segunda derivada localiza onde o movimento muda de ritmo. O vigor acelera 2,45 pisos no segundo dia, o que significa que a queda perde velocidade logo após o choque "
"inicial: a aceleração de sinal contrário atua como freio sobre um deslocamento negativo. No sexto dia o sinal se "
"inverte e o vigor desacelera 1,23 piso, o que antecipa a queda final. A raiva acelera 1,41 piso no quinto dia e "
"a perturbação total 1,37 no segundo, com sinal contrário ao deslocamento, ao passo que a fadiga desacelera 1,31 "
"piso no segundo dia e volta a acelerar no sexto. A leitura conjunta das duas derivadas sugere que o microciclo "
"não produz deterioração contínua, e sim dois eventos discretos separados por um período de estabilidade "
"relativa.",
]
R5=[
"A Figura 7 aplica o mesmo tratamento às séries de prevalência dos seis perfis, e a Tabela 5 registra as "
"prevalências diárias e o teste de estabilidade.",
"A distribuição geral dos 166 pares atribui 30,1% ao iceberg, 25,3% à barbatana de tubarão, 15,1% ao submerso, "
"14,5% ao iceberg invertido, 13,9% à superfície e 1,2% ao Everest invertido. O contraste com a referência de "
"Parsons-Smith, Terry e Machin (2017) é informativo: a barbatana de tubarão comparece com mais que o dobro da "
"prevalência de referência (25,3% contra 11,6%) e o submerso com a metade (15,1% contra 30,6%). A amostra não reproduz a distribuição populacional do estudo original, resultado esperado em "
"um grupo submetido a carga elevada e proximidade competitiva.",
"A trajetória diária revela dois movimentos de sentido oposto e magnitude comparável. O iceberg recua de 44,4% no "
"primeiro dia para 19,0% no sétimo, deslocamento de 25,4 pontos percentuais contra um piso de 9,2. A barbatana de "
"tubarão avança de 3,7% para 23,8%, deslocamento de 20,1 pontos contra um piso de 8,6. A faixa de risco, que "
"agrega três perfis, sobe de 14,8% para 52,4%, deslocamento de 37,6 pontos contra um piso de 9,8, o maior da "
"série. A superfície recua 17,5 pontos contra um piso de 6,7 e o iceberg invertido avança 12,7 contra 7,0. O "
"submerso avança 5,3 pontos contra um piso de 7,3 e recebe o veredito de ruído. O Everest "
"invertido, cujo deslocamento nominalmente supera o piso, envolve dois pares atleta-dia no conjunto inteiro; "
"o piso binomial, calculado sobre proporções próximas de zero, encolhe a ponto de deixar de discriminar, e "
"por isso a figura o assinala como não avaliável.",
"O teste Q de Cochran, aplicado aos dezenove atletas com registro completo, rejeita a hipótese de estabilidade "
"apenas na superfície (Q = 12,62; p = 0,049) e não a rejeita em nenhum dos outros cinco perfis nem na faixa de "
"risco (Q = 10,39; p = 0,109); os demais valores de p variam de 0,167, no submerso, a 0,554, no iceberg. Esse resultado exige comentário explícito, pois aparentemente "
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
"Considerados em conjunto os 119 pares completos de manhã e tarde ou noite, a migração para a faixa de risco tem "
"direção clara: vinte e três pares entram nessa faixa ao longo do dia e dez saem dela (χ² = 4,36; p = 0,037). O "
"dia de treino, qualquer que seja o conteúdo, desloca o grupo na direção do risco, ainda que a margem seja mais "
"estreita do que a razão entre entradas e saídas sugere à primeira vista.",
"A resposta aguda por tipo de estímulo distingue dois padrões. Nos dias de treino intervalado, a fadiga sobe 2,02 pontos (r = 0,524; p < 0,001), a perturbação total sobe 4,15 "
"(r = 0,521; p < 0,001), o vigor cai 1,20 (r = 0,379; p = 0,004) e a tensão sobe 0,44 (r = 0,297; p = 0,023). Nos "
"dias de conteúdo técnico e de força, registra-se a maior perturbação aguda de toda a semana: a perturbação total "
"sobe 6,90 pontos (r = 0,662; p = 0,003), o vigor cai 2,30 (r = 0,637; p = 0,004), a raiva sobe 1,65 (r = 0,599; "
"p = 0,007) e a depressão sobe 1,05 (r = 0,571; p = 0,011). Nos dias de amistoso, apenas a confusão se move, e "
"para baixo (−0,33; r = 0,350; p = 0,027). Esses valores não dependem da regra de composição do valor diário, "
"pois o contraste intradiário sempre opôs o primeiro registro ao último. O dia sem estímulo intervalado e sem jogo produz, portanto, o maior deslocamento "
"afetivo intradiário do microciclo.",
"A decomposição da migração por tipo de estímulo enfraquece o resultado. Nos dias de treino intervalado, dezessete pares entram na faixa de risco e seis saem (χ² = 4,35; p = 0,037), "
"valor que não sobrevive à correção de Holm para três comparações (p ajustado = 0,111). Nos dias de amistoso, "
"três entram e quatro saem (p = 1,000); nos de conteúdo técnico e de força, três entram e nenhum sai (p = 0,248). "
"O contraste entre os estímulos é, portanto, de direção e não apenas de potência: o treino intervalado empurra o "
"elenco para a faixa de risco ao longo do dia, o dia de conteúdo técnico e de força também, ainda que sobre "
"poucos pares, e o amistoso não o faz.",
"A classificação categórica, por sua vez, não distingue os estímulos. A distribuição dos seis perfis não difere entre os tipos de dia (χ² = 6,38; gl = 10; p = 0,782), e tampouco "
"difere a composição das três faixas (χ² = 3,03; gl = 4; p = 0,553). Os níveis médios das variáveis contínuas, "
"comparados entre os três tipos de dia nos vinte e dois atletas com registro nos três, não alcançam o limiar em "
"nenhuma variável; a raiva é a que mais dele se aproxima (χ² = 5,55; p = 0,062), seguida da confusão (p = 0,069) "
"e do vigor (p = 0,070). Uma advertência de delineamento condiciona toda esta seção: os "
"tipos de estímulo não foram distribuídos ao acaso, de modo que o tipo de dia se confunde com a posição no "
"microciclo e com a carga acumulada. O dia de conteúdo técnico e de força é o penúltimo da semana e sucede "
"vinte horas e meia de trabalho; a maior perturbação nele observada admite tanto a leitura de resposta ao "
"estímulo quanto a de efeito cumulativo, e o presente desenho não separa as duas.",
]
R7=[
"A Figura 8 aplica o teste formal de cruzamento e ilustra a diferença entre uma troca de posição aparente e "
"uma inversão estabelecida.",
"O par formado pelo vigor e pela fadiga cruza-se uma única vez, na abscissa 5,13, com limiar combinado de 0,97 "
"ponto. A diferença entre as duas séries é de 5,56 pontos no primeiro dia, favorável ao vigor, e de −3,05 pontos "
"no sétimo, favorável à fadiga; ambos os valores superam o limiar, e a inversão é declarada estabelecida. O "
"resultado tem significado prático imediato: em algum ponto do quinto dia o grupo deixa de ser predominantemente "
"vigoroso e passa a ser predominantemente fatigado, e essa troca não se explica por oscilação amostral. Três "
"outros pares recebem o mesmo veredito: vigor e perturbação total cruzam-se em 6,01, vigor e fadiga física em "
"2,86 e fadiga física e fadiga mental em 1,58.",
"O par formado pela tensão e pela raiva recebe veredito distinto. As duas séries trocam de posição três vezes, nas abscissas 2,14, 4,24 e 5,26, com limiar combinado de 0,62 "
"ponto; a diferença parte de 0,59 ponto no primeiro dia, valor inferior ao limiar. O procedimento classifica o "
"achado como divergência e recusa-lhe o estatuto de inversão estabelecida, ainda que a separação final, de −1,64 "
"ponto, ultrapasse o limiar. É o único par da série a receber esse veredito.",
"A faixa favorável e a faixa de risco fornecem o cruzamento de maior amplitude do estudo. Elas partem separadas por 29,6 pontos percentuais em favor da favorável e terminam separadas por 33,3 em favor "
"da de risco, com um único cruzamento, na abscissa 1,85. O limiar combinado é de 13,5 pontos percentuais, e ambas "
"as separações o superam com folga: a inversão é declarada estabelecida. O grupo, portanto, troca de regime já no segundo dia da semana, antes e de modo mais nítido do que a inversão "
"entre vigor e fadiga, que só ocorre no quinto. A faixa agrega três perfis e por isso responde antes que qualquer subescala isolada.",
]

RC=[
 "A consistência interna do instrumento neste elenco não é homogênea, e a heterogeneidade tem consequência "
 "interpretativa. Raiva, depressão e fadiga apresentam alfa adequado; vigor e confusão ficam abaixo do "
 "convencional de 0,70; e a tensão fica bem abaixo, com alfa de 0,427. A Tabela 8 apresenta as estimativas "
 "com o intervalo obtido por reamostragem agrupada.",
 "A leitura item a item explica o resultado da tensão sem recorrer a hipótese sobre o instrumento. Dois dos "
 "seus quatro itens praticamente não variam neste elenco: «apavorado» permanece no zero em 99,6 por cento "
 "dos registros e «tenso» em 92,1 por cento, com correlação item-total de 0,11 e 0,14. Os outros dois, "
 "«ansioso» e «preocupado», correlacionam-se com o total em 0,42 e 0,45. A subescala mede, aqui, duas coisas "
 "que não se movem juntas: uma apreensão antecipatória, que varia, e uma tensão somática de intensidade "
 "elevada, que não ocorre. O escalonamento multitraço confirma o diagnóstico ao apontar que «tenso» se "
 "correlaciona mais com a depressão do que com a própria subescala.",
 "A implicação é local e não invalida o instrumento: em elenco saudável de alto rendimento, medido "
 "diariamente, os itens de tensão de alta intensidade têm efeito de piso severo, e o escore de tensão passa "
 "a ser governado pelos dois itens de apreensão. Onde este artigo e o companheiro leem a tensão como "
 "ativação e não como sofrimento, é a essa apreensão que se referem, e a leitura ganha suporte, em vez de perdê-lo, quando se conhece a origem da "
 "variância."]

RP=[
 "As séries de prevalência, examinadas perfil a perfil na Figura 10, revelam um padrão que a média das "
 "subescalas não expõe. Os dois perfis de extremos favorável e desfavorável, o iceberg e a barbatana de "
 "tubarão, trocam de posição já na saída do dia basal e nunca mais se reaproximam: o iceberg parte de 44,4% "
 "e a barbatana de 3,7%, e no segundo dia estão em 23,1% e 30,8%. O iceberg não volta ao patamar inicial em "
 "nenhum momento, e a barbatana atinge o seu máximo em D5, entre os dois amistosos, com 34,8%. O submerso e "
 "o iceberg invertido partilham o pico no último dia, ambos com 23,8%, o que reparte o elenco da véspera da "
 "estreia entre uma configuração de apatia e outra de perturbação franca.",

 "A Figura 11 recompõe a semana como redistribuição, e não como deslocamento de médias. A leitura em área "
 "empilhada mostra que o elenco não migra progressivamente de uma faixa para outra: o rearranjo maior "
 "concentra-se na passagem do primeiro para o segundo dia, quando a faixa de risco quase triplica, e o "
 "restante da semana oscila em torno do novo patamar sem retornar ao inicial. O painel das três faixas "
 "localiza a inversão entre a favorável e a de risco em D1,85, isto é, ainda na primeira metade do segundo "
 "dia.",

 "O mapa da Figura 12 responde à pergunta de onde cada perfil predomina. Por dia, os picos distribuem-se "
 "sem concentração: iceberg em D1, superfície em D2, Everest invertido em D4, barbatana de tubarão em D5, e "
 "submerso e iceberg invertido em D7. Por tipo de estímulo, o contraste é mais nítido: o iceberg alcança "
 "44,4% no dia basal e cai a 23,5% nos dias de HIIT, ao passo que a barbatana de tubarão faz o percurso "
 "inverso, de 3,7% no basal a 31,8% no dia técnico e de força. A associação entre estímulo e perfil, "
 "contudo, não é estatisticamente detectável, o que impede atribuir a distribuição ao tipo de sessão.",

 "A Figura 13 sai da prevalência e volta à forma. Cada painel confronta o centroide observado neste elenco "
 "com o centroide canônico de Parsons-Smith, Terry e Machin (2017), em escore T contra a norma de atletas, "
 "e o que se vê é uma correspondência de formato com deslocamento de nível. O iceberg do elenco tem o "
 "desenho esperado, com o vigor como único ponto acima da linha normativa, mas o pico de vigor fica em 51 "
 "contra 55 na referência: é um iceberg de pouca altura. A barbatana de tubarão reproduz com fidelidade a "
 "combinação que lhe dá nome, com a fadiga isolada em 66 e o vigor em 41, e é o perfil em que o elenco mais "
 "se aproxima do padrão publicado. A superfície e o submerso, ao contrário, afastam-se: a superfície do "
 "elenco exibe um pico de raiva em 62 que a referência não tem, e o submerso desce a 38 no vigor onde a "
 "referência marca 41.",

 "Os dois perfis desfavoráveis merecem leitura separada, porque neles o elenco excede a referência. No "
 "iceberg invertido, a raiva chega a 86 contra 75, e no Everest invertido a depressão alcança 123 contra "
 "89. O Everest invertido, porém, reúne apenas dois pares atleta-dia no conjunto inteiro, e o seu centroide "
 "é, na prática, a média de duas observações; a distância em relação à referência não deve ser interpretada "
 "como característica do elenco. A Figura 14 reúne os seis perfis em um único eixo e permite ver de uma vez "
 "o que a taxonomia organiza: o vigor é a dimensão que separa os perfis favoráveis dos desfavoráveis, e ela "
 "os separa em uma faixa estreita, de 33 a 51, ao passo que a raiva e a depressão, que quase não distinguem "
 "os três primeiros perfis, abrem o leque nos três últimos.",
]

RL=[
 "O piso de ruído empregado até aqui é o erro da média do grupo. A decisão sobre um atleta exige o erro da "
 "medida dele, e os dois números não se confundem: o segundo é sempre maior. A Tabela 9 apresenta os três "
 "limiares individuais ao lado do piso de grupo, e o resultado é desconfortável o bastante para merecer "
 "enunciado direto.",
 "Em todas as sete variáveis o erro típico supera a menor mudança relevante, com razão entre 0,21 e 0,44. "
 "Pelo critério consagrado de monitoramento, portanto, o instrumento aplicado diariamente não distingue, no "
 "atleta isolado, a menor mudança que importaria da oscilação que a própria medida produz. O resultado não "
 "contradiz nada do que os artigos afirmam sobre o grupo: a média de vinte e um a vinte e sete atletas tem "
 "erro-padrão muito menor do que a medida de um. Ele delimita o alcance da aplicação prática.",
 "Uma tentativa de decompor esse erro entre imprecisão do instrumento e variação biológica real usou os "
 "dezessete reenvios ocorridos em trinta minutos ou menos, situação em que não há treino nem sono entre as "
 "duas respostas. A decomposição não se sustenta. Quem reenvia é quem quis alterar a resposta, de modo que "
 "o valor obtido é um teto e não uma estimativa não enviesada; e, mesmo como teto, ele iguala ou supera o "
 "erro entre dias no vigor, o que é impossível na população e denuncia o erro amostral de uma estimativa "
 "com dezessete pares. Registra-se o que não depende da decomposição: qualquer que seja a sua composição, o "
 "erro típico entre dias excede a menor mudança relevante.",
 "O limiar ancorado, na Tabela 10, é o resultado de maior utilidade prática deste artigo. Tomada como "
 "âncora a entrada na faixa de risco ao longo do dia, a variação da fadiga entre a manhã e a noite "
 "discrimina com área sob a curva de 0,954, e o ponto de corte de três pontos alcança sensibilidade de 0,88 "
 "e especificidade de 0,87. A perturbação total do humor acompanha, com área de 0,851 e corte de oito "
 "pontos. Tensão e confusão não discriminam e não recebem corte. Um aumento de três pontos na fadiga ao "
 "longo do dia é, nesta amostra, o sinal operacional mais preciso disponível.",
 "A Tabela 11 mostra por que a leitura de grupo não basta. Entre os vinte e um atletas com medida no "
 "primeiro e no sétimo dia, dezoito variam a fadiga na direção do grupo, mas apenas oito ultrapassam a "
 "mudança mínima detectável; no vigor, dezessete acompanham a direção e seis ultrapassam o limiar. O "
 "deslocamento médio da semana é real e é grande, e ainda assim uma parte do elenco não se move mais do que "
 "o erro da própria medida."]

RQ=[
 "A última seção dos resultados não descreve o humor, e sim a base que o descreve. Ela reúne o que a auditoria "
 "de qualidade encontrou e o resultado da reconferência independente, porque nenhum dos achados anteriores se "
 "sustenta se a base não sustentar.",
 "A completude do instrumento é integral: nenhuma das 20.108 respostas de item está ausente. A cobertura da "
 "grade que cruza atleta e dia, ao contrário, decresce ao longo da semana e chega a setenta e oito por cento "
 "do elenco no quarto e no sétimo dias. A contagem de registros supera o previsto no protocolo em seis dos "
 "sete dias, o que decorre de reenvio e não de duplicata, conforme exposto no método. A Tabela 8 apresenta "
 "os dois recortes.",
 "A triagem de discrepantes, na Tabela 9, produz dois resultados de natureza distinta. O primeiro é factual: "
 "nenhum dos 456 registros apresenta valor fora do domínio admissível da sua escala, o que descarta erro de "
 "digitação, escore impossível e código de ausência tratado como número. O segundo é metodológico e merece "
 "registro porque afeta a leitura de qualquer estudo com estas escalas. Em confusão, o primeiro e o terceiro "
 "quartis coincidem no piso; o intervalo interquartil é nulo; a cerca de Tukey colapsa sobre o próprio piso e "
 "passa a classificar como discrepante toda resposta diferente de zero, isto é, 19,5 por cento da amostra. O "
 "escore z modificado falha pela mesma razão, uma vez que o desvio absoluto mediano também é nulo. Depressão "
 "e raiva aproximam-se dessa condição. Em subescala com efeito de piso, portanto, a triagem de discrepantes "
 "não pode apoiar-se em regra de dispersão do grupo: apoia-se no domínio da escala e na comparação de cada "
 "atleta com a própria série.",
 "Aplicada dentro da série individual, essa comparação identifica poucos casos e todos interpretáveis. Em "
 "raiva, onze registros afastam-se da mediana do próprio atleta por mais de três desvios e meio; em "
 "perturbação total do humor, dez. Nenhum é erro de medida. São os dias em que o atleta destoou de si mesmo, "
 "que é precisamente o que o monitoramento diário existe para detectar.",
 "A reconferência fechou a auditoria. Todos os números deste artigo foram recalculados por um segundo caminho "
 "de código, independente do primeiro: enquanto a base canônica parte das colunas já pontuadas, a "
 "reconferência parte do item do formulário e reconstrói cada escore por fórmula. As sessenta e cinco conferências (médias diárias, variações entre o primeiro e o sétimo dia, pisos de ruído, "
 "derivadas normalizadas, prevalências da faixa de risco, valores de p dos contrastes e estatísticas W do teste "
 "de normalidade) coincidem dentro da tolerância adotada. Nenhum valor do texto precisou de correção."]

DISCUSSAO=[
("A forma da semana: dois choques e um platô",[
 "O primeiro resultado a discutir não é um valor, e sim uma forma. A deterioração do humor ao longo do "
 "microciclo terminal não se distribui de modo uniforme: concentra-se em duas transições e deixa entre elas um "
 "período de estabilidade relativa. As derivadas expressas em unidades do piso de ruído tornam essa forma "
 "visível de maneira que a comparação entre médias diárias jamais permitiria. Na passagem do dia basal para o "
 "primeiro dia de treino intervalado, quatro variáveis se movem acima do piso; na passagem do penúltimo para o "
 "último dia, quatro também; nos quatro dias intermediários, quase nenhuma o faz.",
 "Essa geometria contraria a intuição de acúmulo linear que costuma orientar a leitura de séries de "
 "monitoramento. Se a carga se soma dia após dia, e ela de fato se soma, de 1,5 hora para 23,0 horas ao longo da semana, seria "
 "razoável esperar deterioração proporcional. O que se observa aproxima-se mais de um "
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
 "A aplicação do critério produziu três consequências que ilustram a sua utilidade. Ordenou as sete variáveis por "
 "folga em relação ao próprio ruído, e essa ordenação não coincide com a dos testes formais: a depressão "
 "desloca-se 1,6 vez o seu piso e ainda assim não alcança significância por nenhuma via de postos, ao passo que a "
 "raiva, com 1,9 vez, tampouco a alcança. O critério situa ambas na fronteira, onde o veredito depende do que se "
 "pergunta, em lugar de as reduzir a uma ausência de evidência. Recusou também o estatuto de inversão à troca de "
 "posição entre tensão e raiva, que uma leitura desatenta teria celebrado. E expôs a própria fragilidade em "
 "prevalências próximas de zero, onde o erro-padrão binomial encolhe e o critério se torna permissivo, limitação "
 "que o texto assinala em vez de ocultar.",
 "Há, nessa discussão, uma dimensão que ultrapassa a técnica. Uma série de sete pontos comporta muitas "
 "narrativas, e a escolha entre elas raramente decorre dos dados. O piso de ruído funciona como um compromisso "
 "que o analista assume consigo mesmo antes de olhar, e o seu valor epistemológico reside exatamente aí: "
 "restringe o espaço de histórias que os mesmos números autorizam. Nenhum critério elimina o julgamento; o que "
 "um critério explícito faz é torná-lo auditável."]),
("A unidade de análise como fonte silenciosa de divergência",[
 "A auditoria que precedeu este estudo revelou algo que merece registro na literatura, e não apenas no "
 "apêndice metodológico. Sete versões anteriores deste conjunto de dados chegaram a valores divergentes para a mesma quantidade, a variação da prevalência do perfil iceberg entre o "
 "primeiro e o último dia, e a causa não foi erro de cálculo em nenhuma delas. Foi a escolha, nunca declarada, de qual observação conta como uma "
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
("Do grupo para o atleta: o que os limiares permitem e o que impedem",[
 "A distinção entre o piso de ruído do grupo e o erro típico do atleta organiza o alcance prático de tudo o "
 "que este artigo descreve. O piso responde à pergunta do pesquisador, a de saber se a média se moveu, e por ele a semana exibe sinal claro "
 "em cinco das sete variáveis. O erro típico atende à pergunta do preparador, a de saber se aquele atleta mudou, "
 "e por ele o instrumento diário não alcança, em nenhuma variável, a menor mudança "
 "considerada relevante pelo critério de distribuição usual.",
 "A conclusão não é que o monitoramento diário do humor seja inútil, e sim que ele opera em outra escala de "
 "decisão do que a que a literatura de testes físicos costuma assumir. Instrumentos de autorrelato são "
 "adotados justamente por serem baratos e frequentes, e a sua contribuição documentada está mais em "
 "sustentar a conversa entre atleta e comissão do que em produzir um número de corte individual (SAW; MAIN; "
 "GASTIN, 2015). A adesão, aliás, é o gargalo prático conhecido desse tipo de instrumento, e não melhora "
 "apenas com educação sobre ele (McGUIGAN; HASSMÉN; ROSIĆ, 2022).",
 "O limiar ancorado oferece a saída para a decisão individual, e é por isso que ele merece destaque acima "
 "dos limiares de distribuição. Um aumento de três pontos na fadiga entre a manhã e a noite, com "
 "sensibilidade de 0,88 e especificidade de 0,87, é um critério que a comissão técnica pode aplicar sem "
 "conhecer o desvio-padrão do elenco nem o erro típico da medida. Ele não descreve uma mudança «real» no "
 "sentido psicométrico: descreve a variação que, nesta amostra, acompanha a transição para a faixa de "
 "risco. É pouco para uma afirmação de validade e é suficiente para uma triagem.",
 "Cabe registrar o que esse limiar exige para ser usado fora daqui. Ele foi obtido no mesmo conjunto em que "
 "é avaliado, sem validação externa, e a área sob a curva de 0,954 da fadiga é, por isso, uma estimativa "
 "otimista. A replicação prospectiva com o corte fixado antes da coleta é a única forma de saber quanto "
 "dele sobrevive."]),

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
 "A oitava é de cobertura. A grade que cruza atleta e dia decresce ao longo da semana e chega a setenta e "
 "oito por cento do elenco no "
 "quarto e no sétimo dias. A consequência não é apenas de potência: o subconjunto que comparece ao fim da "
 "semana pode diferir sistematicamente do que deixa de comparecer, e a hipótese de ausência ignorável não é "
 "verificável com estes dados. É por essa razão que cada contraste declara o seu denominador e que a unidade "
 "de análise foi fixada no par atleta-dia.",
 "A nona é de granularidade do registro. O número de respostas por atleta e por dia varia de um a seis, acima do "
 "previsto no protocolo, e a auditoria dos carimbos identificou 150 registros excedentes entre o segundo e o "
 "sétimo dia. A regra de composição neutraliza o efeito de ponderação que essa irregularidade produziria, porque "
 "cada atleta-dia passa a contribuir com exatamente duas medidas, mas não recupera a hora prevista de coleta: o "
 "intervalo entre o pré e o pós tem mediana de 292 minutos e varia de 52 a 854, o que torna a janela intradiária "
 "heterogênea entre atletas. O primeiro dia guarda irregularidade própria, pois vinte e um dos vinte e sete atletas responderam duas vezes "
 "na noite basal. A conferência mostra que essas respostas tardias são repetição, e não segunda coleta: dos vinte "
 "e dois atletas que respondem depois das 21h, vinte e um já haviam respondido na janela das 20h42, e o único que "
 "ainda não respondera o faz às 21h54, uma vez apenas. O basal retém, portanto, a primeira resposta de cada "
 "atleta. A escolha não é neutra, e convém explicitá-la: a segunda resposta é mais desfavorável em dezesseis dos "
 "vinte e um casos, de modo que integrá-la elevaria a perturbação total do basal em 2,4 pontos e reduziria a "
 "deterioração observada ao longo da semana."
]

CONCLUSAO=[
"O humor de atletas de handebol de elite deteriorou-se de modo consistente ao longo da última semana de "
"pré-temporada. O vigor recuou 2,98 pontos e a fadiga avançou 3,62, ambos muito acima do respectivo piso de "
"ruído, com tendência monotônica confirmada pelo teste de Page. O perfil iceberg recuou de 37,0% para 19,0% "
"dos pares atleta-dia e a faixa de risco avançou de 22,2% para 52,4%. A deterioração, contudo, não se "
"distribuiu de modo uniforme: concentrou-se em duas transições, a primeira na saída do dia basal e a segunda "
"na véspera da estreia, e deixou entre elas um platô de quatro dias.",
"O tratamento de séries proposto, que reúne filtro binomial, derivadas de primeira e segunda ordem expressas em "
"unidades de ruído e teste formal de cruzamento, mostrou-se útil em três frentes: localizou as transições de choque e os pontos de inflexão que a comparação entre médias diárias não revela; "
"ordenou as variáveis por folga em relação ao próprio ruído, o que distingue a depressão e a raiva, ambas de "
"deslocamento pequeno mas não nulo, do vigor e da fadiga, cujo deslocamento supera o piso em mais de cinco vezes; "
"e separou, entre as trocas de posição observadas, as quatro que constituem inversão estabelecida da única que "
"permanece no terreno da divergência. Recomenda-se a sua adoção como "
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
