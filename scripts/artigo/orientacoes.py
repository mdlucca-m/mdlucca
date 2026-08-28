"""Atendimento às orientações do orientador (áudios de 27/08).

Cada item abaixo responde a um pedido explícito, e **todo valor vem de uma
tabela ou seção do próprio artigo** — nada é estimado.

  1. "tu tens que me apresentar uma tabela que faça a caracterização de tipo
     de treino de carga... dá pra colocar percentual em relação ao nível de
     exigência"                                        → Tabela 71
  2. "quais são os fatores ou as variáveis que geraram essa distorção"
     "há dias onde a variação é muito pequena... e logo depois o dia onde é a
     variação enorme"                                  → §4.17, análise dia a dia
  3. "a gente tem que colocar em que momento que foi feito esse monitoramento"
                                                        → §3.3
  4. "é um estudo de acompanhamento", não experimental  → §3.1
  5. "os dados vão indicar recomendações para o treinamento, para o técnico e
     para os atletas... evitar que a equipe chegue na véspera do jogo com uma
     condição ruim"                                     → §4.18
"""
from __future__ import annotations

# ── Tabela 71 · caracterização da carga, dia a dia ─────────────────────────
# Conteúdo, sessões e duração: Esquema 1 e §3.3.
# FC de pico, %FCmáx e PSE: Tabela 48 (registradas só nos dias de HIIT, §3.4).
# Volume relativo: duração média do dia ÷ duração do dia de maior volume
#   (2,25 h e 4,75 h, pontos médios das faixas declaradas em §3.3).
# PTH, vigor e fadiga: Tabela 19.
TABELA_CARGA = {
    "numero": 71,
    "legenda": ("Tabela 71 – Caracterização da carga de treino por dia do "
                "microciclo e resposta média do humor."),
    "cabecalho": ["Dia", "Data", "Conteúdo da sessão", "Sessões", "Duração",
                  "Volume rel.", "FC pico", "%FC máx", "PSE", "Exigência",
                  "PTH", "Vigor", "Fadiga"],
    "linhas": [
        ["1", "Dom 21/04", "Repouso / baseline", "0", "—", "—", "—", "—", "—",
         "Repouso", "2,52", "7,61", "3,96"],
        ["2", "Seg 22/04", "HIIT + técnico-tático", "2", "2,0–2,5 h", "47%",
         "184", "99%", "8,5", "Alta intensidade", "4,61", "5,66", "5,17"],
        ["3", "Ter 23/04", "Técnico-tático + TF + amistoso", "3", "4,5–5,0 h",
         "100%", "n.d.", "n.d.", "n.d.", "Alto volume", "2,87", "5,71", "5,00"],
        ["4", "Qua 24/04", "HIIT + técnico-tático", "2", "2,0–2,5 h", "47%",
         "183", "98%", "8,5", "Alta intensidade", "4,76", "5,28", "5,76"],
        ["5", "Qui 25/04", "Técnico-tático + TF + amistoso", "3", "4,5–5,0 h",
         "100%", "n.d.", "n.d.", "n.d.", "Alto volume", "2,19", "5,56", "5,27"],
        ["6", "Sex 26/04", "Técnico-tático ×2 + TF", "3", "4,5–5,0 h", "100%",
         "n.d.", "n.d.", "n.d.", "Alto volume", "4,80", "5,74", "5,75"],
        ["7", "Sáb 27/04", "HIIT + técnico-tático", "2", "2,0–2,5 h", "47%",
         "181", "97%", "9,1", "Alta intensidade", "8,28", "4,49", "7,46"],
    ],
    "fonte": "Fonte: dados da pesquisa (2026).",
    "nota": ("Nota: conteúdo, número de sessões e duração conforme o Esquema 1 "
             "e a seção 3.3. Volume relativo = duração média do dia dividida "
             "pela do dia de maior volume (pontos médios de 2,25 h e 4,75 h). "
             "Frequência cardíaca de pico, percentual da FC máxima e percepção "
             "subjetiva de esforço conforme a Tabela 48; foram registradas "
             "apenas nas sessões de HIIT (seção 3.4), de modo que constam como "
             "n.d. nos demais dias — lacuna a ser suprida em coletas futuras. "
             "PTH, vigor e fadiga são as médias diárias da Tabela 19. TF = "
             "treinamento de força."),
}

# ── §4.17 · leitura dia a dia ───────────────────────────────────────────────
SECAO_CARGA_TITULO = "4.17 Caracterização da carga e a variação diária do humor"

SECAO_CARGA = [
    "A Tabela 71 reúne, num mesmo quadro, o que foi exigido dos atletas em cada "
    "dia e como o humor respondeu. É essa justaposição que permite sair da "
    "descrição da curva para a explicação do que a produziu, e é a ela que as "
    "recomendações da seção seguinte se ancoram.",

    "O microciclo alterna dois tipos de dia. Os dias 2, 4 e 7 combinam HIIT e "
    "treino técnico-tático em 2,0 a 2,5 horas — alta intensidade e volume "
    "reduzido, com frequência cardíaca de pico entre 97% e 99% da máxima e "
    "percepção de esforço entre 8,5 e 9,1. Os dias 3, 5 e 6 concentram treino "
    "técnico-tático, treinamento de força e jogos amistosos em 4,5 a 5,0 horas "
    "— o dobro do volume, sem o estímulo intervalado. O Dia 1 é de repouso e "
    "serve de linha de base.",

    "A perturbação total do humor acompanha essa alternância de forma nítida. "
    "Partindo de 2,52 no repouso, sobe para 4,61 no primeiro dia de HIIT, "
    "recua para 2,87 no dia seguinte, de volume alto, torna a subir para 4,76 "
    "no segundo dia de HIIT e recua novamente para 2,19. Ou seja: nos dias de "
    "alto volume sem HIIT o humor retorna a valores próximos ao de repouso, ao "
    "passo que os dias de alta intensidade elevam a perturbação. A resposta "
    "aguda é governada mais pela intensidade do estímulo do que pelo tempo "
    "total de treino — o que explica por que a variação pré→pós é pequena "
    "justamente nos dias mais longos.",

    "Dois dias rompem esse padrão, e são os mais informativos. O Dia 6, de alto "
    "volume e sem HIIT, apresenta perturbação de 4,80, equivalente à dos dias "
    "de HIIT: às vésperas do encerramento do microciclo, o volume acumulado "
    "passa a produzir sozinho o efeito que antes exigia intensidade. E o Dia 7 "
    "destaca-se de todos: perturbação de 8,28, isto é, 3,3 vezes a do repouso e "
    "1,7 vez a do dia mais perturbado até então. Não se trata do efeito de uma "
    "sessão — a carga do Dia 7 é a mesma dos Dias 2 e 4 —, mas do acúmulo de "
    "seis dias sobre um organismo que já não recupera no mesmo ritmo.",

    "O vigor descreve trajetória distinta e complementar. Cai de forma abrupta "
    "do repouso para o primeiro dia de treino (7,61 → 5,66), estabiliza entre "
    "5,3 e 5,7 ao longo de toda a semana, e só então despenca no Dia 7, para "
    "4,49 — o menor valor do microciclo. A fadiga faz o percurso espelhado, de "
    "3,96 a 7,46. A leitura conjunta é de um sistema que absorve a carga "
    "enquanto consegue e cede no último dia.",

    "As três sessões de HIIT confirmam a leitura por dentro. A frequência "
    "cardíaca de pico cai de 184 para 181 bpm entre a primeira e a terceira "
    "sessão enquanto a percepção de esforço sobe de 8,5 para 9,1 (Tabela 48): "
    "o mesmo estímulo externo, entregue com variação mínima (coeficiente de "
    "variação de 1,7% na FC de pico), passa a custar mais e a mobilizar menos "
    "— assinatura clássica de fadiga acumulada. No mesmo sentido, a "
    "recuperação total percebida cai de 11,5 para 9,6 e a sonolência sobe de "
    "9,2 para 11,2 (Tabela 68).",

    "Uma ressalva estrutural, já declarada na seção 3.3, delimita o alcance "
    "desta leitura: neste microciclo os dias de HIIT são também os de menor "
    "volume, de modo que intensidade e volume estão confundidos e seus efeitos "
    "não podem ser plenamente separados. O que a Tabela 71 sustenta é a "
    "associação entre o tipo de dia e a resposta do humor, não a atribuição "
    "causal a um dos dois componentes isoladamente.",
]

# ── §4.18 · recomendações ───────────────────────────────────────────────────
SECAO_RECOMENDACOES_TITULO = ("4.18 Recomendações para a comissão técnica e "
                              "para os atletas")

SECAO_RECOMENDACOES = [
    "O achado com consequência prática mais direta é o estado em que a equipe "
    "encerra o microciclo. No Dia 7 a perturbação total do humor atinge 8,28, "
    "o vigor cai ao mínimo da semana e a fadiga ao máximo; a proporção de "
    "atletas em perfil iceberg — vigor acima de todas as dimensões negativas, "
    "o padrão associado à prontidão competitiva — cai de 71,4% no Dia 1 para "
    "32,6%, enquanto a proporção de atletas perturbados sobe de 47,6% para "
    "71,7% (Tabela 20). Na classificação de Parsons-Smith, o perfil iceberg "
    "recua de 21,4% para 6,5% entre o primeiro e o último dia (Tabela 21).",

    "A implicação é operacional. Uma competição disputada no dia seguinte ao "
    "encerramento deste microciclo encontraria a equipe no pior estado "
    "psicológico de toda a semana, e não no melhor. O padrão observado — "
    "acúmulo de fadiga, queda acentuada do vigor e elevação da perturbação "
    "total — é o oposto do que se busca na véspera de um jogo. Recomenda-se, "
    "portanto, que o último dia antes da competição não replique a carga aqui "
    "descrita: a alta intensidade do Dia 7, somada a seis dias de acúmulo, "
    "produz justamente a condição que se pretende evitar.",

    "Quatro recomendações decorrem dos dados, e cada uma remete à evidência "
    "que a sustenta.",

    "Primeira: reposicionar o estímulo de alta intensidade. As sessões de HIIT "
    "produziram a maior resposta aguda do microciclo, e a última delas foi "
    "realizada no encerramento. Alocá-la no meio do microciclo, reservando os "
    "dois últimos dias para redução progressiva de carga, permitiria que a "
    "perturbação retornasse aos valores observados nos dias 3 e 5 — próximos "
    "aos do repouso — antes da competição.",

    "Segunda: monitorar por tendência, não por coleta isolada. O erro típico "
    "da medida excede a menor mudança relevante em uma única aplicação, de "
    "modo que a leitura de um único dia não distingue sinal de ruído; a média "
    "de cinco a sete dias, ao contrário, é fiável (Tabela 6). A decisão sobre "
    "um atleta deve apoiar-se na trajetória da semana, e não no escore da "
    "manhã.",

    "Terceira: acompanhar prioritariamente o eixo energia–fadiga. Vigor, "
    "fadiga, fadiga física e perturbação total foram as únicas variáveis a "
    "sobreviver à correção para comparações múltiplas, e são também as menos "
    "afetadas pelo efeito piso (Tabela 35). Tensão, depressão, raiva e "
    "confusão apresentam de 50% a 80% das respostas no valor mínimo: nelas, a "
    "ausência de variação não deve ser lida como ausência de resposta, e sim "
    "como limite do instrumento nesta população.",

    "Quarta: usar a divergência entre carga externa e resposta interna como "
    "sinal de alerta. A queda da frequência cardíaca de pico acompanhada de "
    "aumento da percepção de esforço, entre sessões de carga externa "
    "equivalente, indica que o atleta já não sustenta a mesma resposta "
    "fisiológica ao mesmo estímulo. Quando esse padrão coincide com queda da "
    "recuperação percebida e aumento da sonolência — como ocorreu aqui entre a "
    "primeira e a terceira sessão de HIIT —, há indicação de reduzir a carga "
    "antes que o quadro se consolide.",

    "Cabe registrar o alcance dessas recomendações. Elas derivam de um "
    "microciclo, de uma equipe e de 27 atletas, em delineamento observacional "
    "sem grupo-controle; descrevem o que aconteceu nesta semana e orientam a "
    "formulação de hipóteses, não constituem prescrição validada. A "
    "verificação exige acompanhar microciclos com estruturas diferentes de "
    "distribuição de carga e observar se a trajetória do humor responde na "
    "direção prevista.",
]

# ── Ajustes de texto pedidos ────────────────────────────────────────────────
AJUSTES: list[tuple[str, str, str, str]] = [
    (
        "§3.3 · momento do monitoramento",
        "Microciclo de sete dias (21–27/04/2024) da fase pré-competitiva.",
        "Microciclo de sete dias (21–27/04/2024) correspondente à última semana "
        "de treinamento da fase pré-competitiva, imediatamente anterior ao "
        "início da competição — momento em que a equipe deveria apresentar-se "
        "em condição de prontidão. É esse posicionamento no calendário que "
        "confere sentido prático à trajetória descrita: o estado observado no "
        "Dia 7 é o estado com que a equipe chegaria à véspera do jogo. "
        "[A CONFIRMAR: nomear a competição e a data da primeira partida.]",
        "O orientador pediu que se declare em que momento o monitoramento foi "
        "feito, por ser isso que dá qualidade e consequência prática ao artigo.",
    ),
    (
        "§3.1 · estudo de acompanhamento",
        "Trata-se de um estudo observacional, longitudinal e prospectivo, de "
        "medidas repetidas intraindividuais, conduzido em condições ecológicas "
        "de treinamento — sem aleatorização, grupo-controle ou manipulação "
        "experimental da carga.",
        "Trata-se de um estudo de acompanhamento: observacional, longitudinal e "
        "prospectivo, de medidas repetidas intraindividuais, conduzido em "
        "condições ecológicas de treinamento — sem aleatorização, "
        "grupo-controle ou manipulação experimental da carga. A distinção "
        "importa para a leitura dos resultados: descreve-se a resposta "
        "psicológica a um microciclo pré-competitivo tal como ele foi "
        "planejado pela comissão técnica, e não o efeito de um tratamento "
        "atribuído pelo pesquisador. O que os dados autorizam são "
        "recomendações de monitoramento e de distribuição de carga, não "
        "inferência causal sobre o efeito isolado de um tipo de treino.",
        "O orientador foi explícito: 'seria um estudo experimental do ponto de "
        "vista do efeito do treinamento? Mas é um estudo de acompanhamento'.",
    ),
]
