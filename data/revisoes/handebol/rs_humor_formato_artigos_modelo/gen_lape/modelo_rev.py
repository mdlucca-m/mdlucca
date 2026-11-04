# ---- revisão no padrão do artigo modelo: QP1 na ordem do modelo, discussão ampliada e conclusão reflexiva ----
# Executado pelos montadores (artigo, documento e ABNT) sobre o texto do gerador: revisar(txt, abnt).

QP1 = '''P(f"O estudo mais antigo encontrado foi publicado por {a('H2')}, com data provável de 2008. Desde então, "
  f"{NE} estudos publicados investigaram o tema até 2026, e o mais recente foi publicado por {a('H34')} (ver Apêndice A "
  f"para a lista completa dos estudos selecionados). Os anos com o maior número de estudos publicados foram 2014, 2022, "
  f"2023 e 2025, com quatro estudos cada, seguidos de 2010, 2018 e 2020, com três estudos por ano, e de 2015 e 2017, com "
  f"dois estudos por ano (Figura 2A). A partir de 2018, foram publicados "
  f"{sum(1 for e in EST if NORM[e['id']][0] >= 2018)} dos {NE} estudos. O estudo com o maior período de acompanhamento "
  f"foi o de {a('H3')}, com cinco medidas ao longo de 40 semanas da temporada.")
P(f"Quanto às populações investigadas, {ext(NIV['Elite'])} estudos avaliaram atletas de elite, {ext(NIV['Formação'])} "
  f"avaliaram atletas das categorias de formação e {ext(NIV['Nacional'])}, atletas de nível nacional; "
  f"{ext(NIV['Escolar'])} estudos investigaram escolares, {ext(NIV['Universitário'])} investigaram atletas "
  f"universitários e {ext(NIV['Amador'])}, atletas amadores (Figura 2D). Apenas {ext(NIV['Não relatado'])} estudos não "
  f"relataram o nível competitivo dos participantes. Os dois estudos de handebol de praia avaliaram 17 jogadoras da "
  f"seleção brasileira {c('H17')} e 181 atletas de ambos os sexos de equipes classificadas para a Copa da Espanha de "
  f"2016 {c('H21')}, e seleções nacionais compuseram ainda a amostra de outros dois estudos, com 39 jogadoras das "
  f"seleções adulta, júnior e juvenil do Chile {c('H22')} e 584 atletas húngaros das seleções sub-17, sub-19, sub-21 e "
  f"adulta e do programa de talentos sub-15 {c('H34')}.")
assert PAIS['Brasil'] == PAIS['Tunísia'] and PAIS['Irã'] == PAIS['Ucrânia'] == 2
P(f"Os países em que o tema foi pesquisado foram a Espanha, com {PAIS['Espanha']} estudos, seguida do Brasil e da "
  f"Tunísia, com {PAIS['Brasil']} estudos cada, do Irã e da Ucrânia, com dois estudos cada, e de Portugal, Iraque, "
  f"Alemanha, Índia, Chile, Croácia, Jordânia, Hungria e Sérvia, com um estudo cada (Figura 2B). Apenas "
  f"{ext(PAIS['Não relatado'])} estudos não relataram o país em que a pesquisa foi realizada.")
P(f"Dos {NE} estudos incluídos, {ext(DEL['Transversal'])} são transversais, {ext(DEL['Longitudinal'])} são "
  f"longitudinais, {ext(DEL['Quase-experimental'])} são quase-experimentais, {ext(DEL['Cruzado'])} são cruzados e "
  f"{ext(DEL['Ensaio randomizado'])} são ensaios randomizados (Figura 2E). A medida do humor ocorreu no treinamento em "
  f"{ext(CTX['Treinamento'])} estudos, na competição oficial em {ext(CTX['Competição oficial'])}, ao longo do período "
  f"competitivo em {ext(CTX['Período competitivo'])} e em laboratório em {ext(CTX['Laboratório'])} (Figura 2F), e dois "
  f"estudos avaliaram atletas durante o confinamento da pandemia de COVID-19 {c('H20', 'N3')}.")
P(f"Os estudos incluíram um total de {mil(SOMA)} participantes, e apenas um estudo não relatou o número de "
  f"participantes {c('H2')}. O estudo com a maior amostra foi o de {a('H34')}, com 584 atletas, seguido dos estudos com "
  f"407 adolescentes croatas, comparados a 349 inativos {c('H27')}, e com 187 atletas federados, 77 deles profissionais "
  f"{c('H20')}. No outro extremo, o programa de autorregulação do humor envolveu 6 jogadores, selecionados entre 20 "
  f"pelos escores mais negativos {c('H10')}. O tamanho da amostra variou de {min(NS)} a {max(NS)} participantes, com "
  f"mediana de {br(MED, 0)}, e {ext(N30)} estudos reuniram menos de 30 atletas. A maioria dos estudos investigou "
  f"amostras femininas: quanto ao sexo, {ext(SEXO['feminino'])} estudos incluíram apenas mulheres, "
  f"{ext(SEXO['masculino'])} apenas homens e {ext(SEXO['misto'])} homens e mulheres, e {ext(SEXO['n.r.'])} não "
  f"relataram o sexo dos participantes (Figura 2C).")
P(f"A faixa etária dos participantes variou, e as amostras mais jovens tinham de 13 a 14 anos {c('H27')} e média de "
  f"13,81 ± 0,73 anos {c('N5')}. Entre os adolescentes, as médias chegaram a 17,4 ± 2,08 anos {c('H29')}, e dois "
  f"estudos descreveram a amostra apenas como adolescente {c('N1', 'N8')}; entre os juniores, as médias foram de "
  f"18,6 ± 2,4 anos {c('H15')} e de 18,8 ± 0,20 anos {c('H11')}. O estudo com a amostra de maior média de idade foi o de "
  f"{a('H13')}, com 30,46 ± 8,29 anos, e o de maior amplitude etária abrangeu atletas de 14 a 35 anos {c('H34')}. "
  f"Quatro estudos não relataram esses dados {c('H2', 'H4', 'H14', 'H30')}. A leitura integral apoiou-se no texto "
  f"completo em {FTL} relatórios e apenas no resumo em {NR - FTL}, e o Apêndice A apresenta a extração completa de "
  f"cada estudo.")
'''

DH41 = '''P(f"Estudos recentes da modalidade mostram que o acompanhamento diário do estado psicológico é viável nas equipes de "
  f"handebol feminino, população predominante nesta revisão. Em 19 jogadoras profissionais eslovenas acompanhadas por 60 "
  f"dias da temporada, com questionários diários pelo celular e registro do sono por anel, o estresse percebido "
  f"associou-se a menor envolvimento com o esporte no dia seguinte, e as noites com mais sono REM atenuaram ligeiramente "
  f"essa relação {R.cite('e158')}. Em 50 jogadoras norueguesas adolescentes, avaliadas antes, durante e depois de 11 a "
  f"12 sessões ao longo de quatro semanas, o prazer com a prática foi maior quando as atletas perceberam comportamentos "
  f"do treinador favoráveis às suas necessidades psicológicas {R.cite('e185')}, e o prazer antes do treino associou-se à "
  f"carga física da sessão, que, por sua vez, associou-se ao prazer após o treino {R.cite('e184')}. Em atletas "
  f"universitários de três modalidades coletivas, as jogadoras de handebol relataram mais estresse que os jogadores "
  f"{R.cite('e175')}. Esses estudos reforçam que o sexo, o papel do treinador e o momento da medida modificam a resposta "
  f"afetiva e que medidas breves e repetidas são exequíveis na rotina das equipes.")
'''

DH42 = '''P(f"A relação entre o humor e a carga, observada sobretudo na fadiga e no vigor, também aparece nos estudos recentes "
  f"que monitoraram o estresse e a recuperação no handebol. Em 189 jogadores de elite acompanhados por 45 semanas, o "
  f"estresse percebido associou-se à carga e ao cortisol, e 86% dos atletas apresentaram associação positiva entre "
  f"estresse e carga {R.cite('e147')}. Em 16 jogadores profissionais, os itens de estresse de uma escala breve de "
  f"recuperação e estresse foram mais altos, e os de recuperação mais baixos, nos dias sem descanso, acompanhados da "
  f"creatina quinase {R.cite('e150')}. Em 93 jogadores universitários acompanhados por duas temporadas, a fadiga "
  f"percebida foi o único preditor significativo do risco de lesão do ligamento cruzado anterior {R.cite('e178')}, e, "
  f"nos Jogos de Praia do Mediterrâneo de 2023, a fadiga, a dor muscular e o estresse de dez jogadoras da seleção "
  f"italiana tenderam a aumentar ao longo dos dias de competição {R.cite('e152')}. Medidas objetivas e subjetivas de fadiga "
  f"também foram comparadas em 100 jogadores ao longo da temporada {R.cite('e144')} e durante um jogo oficial de "
  f"adolescentes {R.cite('e183')}. Esses resultados indicam que as escalas breves de estresse e recuperação respondem à "
  f"carga de modo semelhante às dimensões fadiga e vigor do perfil de humor, e que a inclusão de um instrumento de humor "
  f"validado nesses protocolos permitiria comparar os achados entre os estudos.")
'''

DH43 = '''P(f"As intervenções psicológicas mais recentes no handebol reproduzem as características dos estudos incluídos: "
  f"delineamentos quase-experimentais, amostras pequenas e desfechos diferentes do perfil de humor. Uma sessão de "
  f"hipnose em áudio de 30 minutos, aplicada antes de oito jogos oficiais da liga em 24 atletas de duas equipes, "
  f"aumentou a autoconfiança e reduziu a ansiedade cognitiva e somática antes do jogo, sem efeito sobre a força de "
  f"preensão manual e o desempenho nos arremessos {R.cite('e181')}. Um programa de treino do estado de fluxo baseado em "
  f"mindfulness melhorou a tomada de decisão e o bem-estar mental de 105 atletas de elite jovens e adultos "
  f"{R.cite('e153')}, e um programa de oito semanas de relaxamento muscular progressivo e imagética foi testado em 36 "
  f"jogadoras cadetes, com delineamento quase-experimental e grupo controle {R.cite('e196')}. O treino de neurofeedback foi avaliado em dez "
  f"jogadores profissionais, quatro no grupo experimental e seis no controle {R.cite('e170')}, e até o estresse do "
  f"treinador foi alvo de intervenção, pois a respiração lenta reduziu a alfa-amilase salivar de um técnico profissional "
  f"em jogos oficiais {R.cite('nikolovski2023b')}. Nenhum desses estudos utilizou o POMS ou a BRUMS, o que mantém aberta "
  f"a pergunta sobre o efeito dessas intervenções no estado de humor dos atletas de handebol.")
'''

DH44 = '''P(f"A falta de padronização dos desfechos, observada nesta revisão nas versões do POMS e no momento da medida, "
  f"também limita outras sínteses recentes da modalidade. Na revisão que combinou estatisticamente os estudos sobre a "
  f"fadiga e o arremesso, a fadiga aguda reduziu a velocidade do arremesso, mas não permitiu conclusão sobre a precisão, "
  f"porque os estudos definiram a precisão de formas muito diferentes {R.cite('hadjisavvas2026fadiga')}. Do mesmo modo, "
  f"os estudos de monitoramento citados anteriormente empregaram escalas distintas de bem-estar, de recuperação e de "
  f"estresse {R.cite('e147', 'e150', 'e152')}. A escolha de um instrumento validado e de momentos de medida "
  f"padronizados é, portanto, condição para que os estudos futuros sobre o humor no handebol possam ser comparados e "
  f"combinados.")
'''

_BUL_CONC = '''[f"Os {NE} estudos, publicados entre 2008 e 2026, reuniram {mil(SOMA)} participantes, concentraram-se na Espanha, "
          f"na Tunísia e no Brasil e investigaram sobretudo amostras pequenas e femininas, com mediana de {br(MED, 0)} "
          f"participantes por estudo e escolares em parte deles;",
          f"O POMS e suas versões predominaram na medida do humor, em {FAM['POMS e versões']} estudos e em versões de 30 a "
          f"65 itens, enquanto a BRUMS, concebida para a aplicação repetida, apareceu em apenas três estudos, e o momento "
          f"da medida foi declarado com precisão em apenas {QI['q4']['sim']};",
          f"O humor associou-se à carga, sobretudo por meio da fadiga e do vigor, ao resultado do jogo, às habilidades "
          f"psicológicas e ao convívio social; {DIRC['Efeito ou associação']} estudos relataram efeito ou associação e "
          f"{DIRC['Misto']} resultados mistos, com certeza baixa a muito baixa;",
          "Doze estudos testaram intervenções, e o encorajamento verbal e o feedback modificaram o humor durante a "
          "prática, com certeza baixa em escolares e muito baixa em atletas, enquanto as intervenções nutricionais, "
          "psicológicas e musicais não demonstraram efeito consistente e nenhuma intervenção de sono ou de recuperação "
          "foi testada;",
          f"A qualidade foi alta em {QUAL['Alta']} estudos, moderada em {QUAL['Moderada']} e baixa em {QUAL['Baixa']}, a "
          f"análise estatística foi adequada em apenas {QI['q6']['sim']}, e as falhas de relato atravessaram todos os "
          f"níveis de qualidade."]'''

_ABRE = ('"Conclui-se que as evidências científicas sobre os estados de humor em atletas de handebol no treinamento e na "\n'
         '  "competição são escassas, recentes e predominantemente observacionais, e que o humor desses atletas responde à "\n'
         '  "carga, ao contexto competitivo e à interação com treinadores e colegas, embora a força dessas evidências ainda "\n'
         '  "seja limitada. Os principais pontos dos achados são:"')

_REFLEXAO = '''P("Esses resultados convidam a uma reflexão sobre o lugar do humor no handebol. Na maior parte dos estudos, o humor "
  "foi tratado como um retrato pontual, obtido uma única vez e interpretado de forma isolada, quando a própria rotina "
  "da modalidade, com jogos frequentes, viagens, torneios concentrados e contato constante entre colegas, exige um "
  "acompanhamento contínuo. Medir mais não basta: é preciso medir no momento certo, com o mesmo instrumento, e "
  "relacionar o humor ao que acontece no treino e no jogo. Do mesmo modo, a escassez de intervenções contrasta com a "
  "facilidade com que o encorajamento verbal e o feedback modificaram o humor nos poucos estudos experimentais, o que indica que "
  "o conhecimento disponível ainda não chegou à rotina das equipes e que a rotina das equipes ainda não chegou à "
  "pesquisa. Os estudos recentes da modalidade, com registros diários de estresse, de prazer e de sono em equipes "
  "inteiras, mostram que esse caminho é viável e que o perfil de humor pode ser incorporado sem custo relevante.")
P("Com base nas evidências sintetizadas, técnicos e psicólogos do esporte podem adotar o monitoramento breve e regular "
  "do humor, em horário fixo, e valorizar a comunicação positiva com os atletas, enquanto pesquisadores e gestores "
  "esportivos podem priorizar medidas repetidas por sessão, momento da medida declarado, análise por sexo, relato "
  "completo dos resultados e estudos experimentais conduzidos na rotina das equipes, incluídas intervenções de sono e "
  "de recuperação. Essas informações podem orientar a prática e a pesquisa sobre o humor no treinamento e na "
  "competição do handebol.")
'''

CONC_ART = ('H1("5. Conclusões")\nP(' + _ABRE + ')\nfor _b in ' + _BUL_CONC + ':\n    BUL(_b, marca="•")\n'
            + _REFLEXAO)
CONC_ABNT = ('H1("5 Conclusão")\nP(' + _ABRE + ')\nfor _b in ' + _BUL_CONC + ':\n    P("•  " + _b, primeira=0)\n'
             + _REFLEXAO)


def _qp1(txt):
    for ini in ['P(f"O estudo mais antigo foi publicado por', 'P(f"Os {NE} estudos foram publicados entre 2008 e 2026, com média']:
        if ini in txt:
            break
    else:
        raise AssertionError("início da QP1 não encontrado")
    assert txt.count(ini) == 1
    i = txt.index(ini)
    j = txt.index('figura("Figura2_Caracteristicas_RS.png"', i)
    return txt[:i] + QP1 + txt[j:]


def _antes(txt, ancora, novo):
    assert txt.count(ancora) == 1, ancora
    return txt.replace(ancora, novo + ancora)


def revisar(txt, abnt=False):
    txt = _qp1(txt)
    if abnt:
        txt = _antes(txt, 'H2("4.2 ', DH41)
        txt = _antes(txt, 'H2("4.4 ', DH42)
        txt = _antes(txt, 'H2("4.5 ', DH43)
        txt = _antes(txt, 'H2("4.6 ', DH44)
        i = txt.index('H1("5 Conclusão")')
        fimc = 'intervenções de sono e de clima motivacional.")\n'
        j = txt.index(fimc, i) + len(fimc)
        txt = txt[:i] + CONC_ABNT + txt[j:]
    else:
        txt = _antes(txt, 'H2("4.2. ', DH41)
        txt = _antes(txt, 'H2("4.3. ', DH42)
        txt = _antes(txt, 'H2("4.4. ', DH43)
        txt = _antes(txt, 'H2("4.5. ', DH44)
        i = txt.index('H1("5. Conclusões")')
        fimc = 'delineamentos experimentais na rotina das equipes.")\n'
        j = txt.index(fimc, i) + len(fimc)
        txt = txt[:i] + CONC_ART + txt[j:]
    return txt
