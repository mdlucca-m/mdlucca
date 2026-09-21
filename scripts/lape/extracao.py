"""Extracao de dados e risco de vies dos estudos incluidos.

Depois da triagem vem a parte que ninguem gosta: ler cada estudo e tirar
dele, campo a campo, o que a revisao precisa. Hoje isso e feito em
planilha compartilhada -- e a planilha nao sabe que duas pessoas deviam
extrair em separado, nem onde as duas discordaram. O Rayyan nao faz nem
isso: a triagem acaba e a ferramenta acaba junto.

O desenho e o mesmo da triagem, e pela mesma razao: cada pessoa preenche
a sua, e a versao final e uma terceira coisa, construida a partir das
duas. Sem isso, "extracao em duplicata" vira uma pessoa conferindo o que
a outra digitou -- que nao e a mesma coisa e nao vale como duplicata.

Duas saidas, que sao o que a revista pede:

  a tabela de caracteristicas dos estudos incluidos
  o semaforo de risco de vies, com o julgamento de cada dominio
"""
from __future__ import annotations

import json
from typing import Any

from .db import Database
from .util import clean_text

TIPOS = ("texto", "texto_longo", "numero", "data", "escolha", "multipla", "sim_nao")

# ----------------------------------------------------------------------
# O formulario de extracao
# ----------------------------------------------------------------------
# Ponto de partida, nao camisa de forca: cobre o que quase toda revisao de
# intervencao precisa, e cada revisao acrescenta ou tira o que quiser. Uma
# revisao que comeca com a folha em branco costuma terminar com campos
# inventados no meio do caminho, e ai metade dos estudos ja foi extraida
# sem eles.
FORMULARIO_PADRAO: tuple[dict[str, Any], ...] = (
    {"code": "pais", "label": "País", "kind": "texto", "grupo": "Identificação"},
    {"code": "delineamento", "label": "Delineamento", "kind": "escolha",
     "grupo": "Identificação",
     "options": "Ensaio randomizado;Ensaio não randomizado;Coorte;Caso-controle;"
                "Transversal;Série de casos;Qualitativo;Revisão"},
    {"code": "financiamento", "label": "Financiamento", "kind": "texto",
     "grupo": "Identificação", "help": "Agência, ou 'não declarado'"},
    {"code": "n_total", "label": "N total", "kind": "numero", "grupo": "Participantes",
     "required": 1},
    {"code": "n_intervencao", "label": "N no grupo intervenção", "kind": "numero",
     "grupo": "Participantes"},
    {"code": "n_controle", "label": "N no grupo controle", "kind": "numero",
     "grupo": "Participantes"},
    {"code": "idade", "label": "Idade (média ± DP)", "kind": "texto",
     "grupo": "Participantes"},
    {"code": "sexo", "label": "Sexo (% mulheres)", "kind": "texto",
     "grupo": "Participantes"},
    {"code": "populacao", "label": "População", "kind": "texto_longo",
     "grupo": "Participantes", "help": "Quem eram, e como foram recrutados"},
    {"code": "intervencao", "label": "Intervenção", "kind": "texto_longo",
     "grupo": "Intervenção", "required": 1},
    {"code": "duracao", "label": "Duração", "kind": "texto", "grupo": "Intervenção"},
    {"code": "frequencia", "label": "Frequência", "kind": "texto", "grupo": "Intervenção"},
    {"code": "comparador", "label": "Comparador", "kind": "texto_longo",
     "grupo": "Intervenção"},
    {"code": "desfecho_primario", "label": "Desfecho primário", "kind": "texto_longo",
     "grupo": "Desfechos", "required": 1},
    {"code": "instrumentos", "label": "Instrumentos", "kind": "texto_longo",
     "grupo": "Desfechos", "help": "Escalas e questionários usados"},
    {"code": "momentos", "label": "Momentos de avaliação", "kind": "texto",
     "grupo": "Desfechos"},
    {"code": "resultado", "label": "Resultado principal", "kind": "texto_longo",
     "grupo": "Resultados", "required": 1},
    {"code": "tamanho_efeito", "label": "Tamanho de efeito", "kind": "texto",
     "grupo": "Resultados", "help": "d de Cohen, diferença média, RR — com IC quando houver"},
    {"code": "perdas", "label": "Perdas de seguimento", "kind": "texto",
     "grupo": "Resultados"},
    {"code": "conclusao", "label": "Conclusão dos autores", "kind": "texto_longo",
     "grupo": "Resultados"},
)
# ----------------------------------------------------------------------
# O formulario completo -- o que uma revisao sistematica deve extrair
# ----------------------------------------------------------------------
# O de cima e um comeco. Este e a lista inteira, e ela nao e opiniao: sai
# do item 10 do PRISMA 2020 (o que se buscou em cada estudo, e TODOS os
# resultados, e nao so os significativos), do capitulo 5 do manual
# Cochrane (o que uma ficha de coleta tem de ter) e das listas do JBI.
#
# Um campo aqui nao esta porque seria bonito te-lo: esta porque a sua
# falta aparece depois, e sempre tarde. Financiamento e conflito de
# interesse sao pedidos por revista e nao se acham mais quando a leitura
# ja passou. Idioma e pais sao o que sustenta dizer de onde vem a
# evidencia -- e uma revisao brasileira que nao consegue dizer isso perde
# justamente o seu argumento. Fidedignidade NA AMOSTRA, e nao a do artigo
# de validacao, e o que separa um achado de um ruido, e e o campo que
# mais falta nas revisoes de psicologia do esporte. Resultado nao
# significativo tem campo proprio porque, sem ele, a extracao copia o
# resumo -- e o resumo so conta o que deu certo.
#
# Extrair tudo custa caro, e o custo e real: sao cinquenta e poucos
# campos por estudo, em duplicata. Por isso ele e uma ESCOLHA, e nao o
# padrao. Mas a escolha inversa custa mais: o campo que nao se extraiu na
# primeira leitura so se recupera relendo os estudos todos.
FORMULARIO_COMPLETO: tuple[dict[str, Any], ...] = (
    # -- de onde veio o estudo, e o que ele declara sobre si -------------
    {"code": "idioma", "label": "Idioma da publicação", "kind": "texto",
     "grupo": "Identificação e procedência"},
    {"code": "pais", "label": "País(es) da coleta", "kind": "texto",
     "grupo": "Identificação e procedência",
     "help": "Onde os dados foram coletados, que nem sempre é o país dos autores"},
    {"code": "contexto", "label": "Contexto", "kind": "texto",
     "grupo": "Identificação e procedência",
     "help": "Clube, escola, seleção, federação, laboratório"},
    {"code": "registro", "label": "Registro ou protocolo", "kind": "texto",
     "grupo": "Identificação e procedência",
     "help": "Número do registro, ou “não declarado”"},
    {"code": "financiamento", "label": "Financiamento", "kind": "texto",
     "grupo": "Identificação e procedência", "help": "Agência, ou “não declarado”"},
    {"code": "conflito", "label": "Conflito de interesses", "kind": "texto",
     "grupo": "Identificação e procedência",
     "help": "O que os autores declaram — inclusive quando declaram que não há"},
    {"code": "etica", "label": "Aprovação ética e consentimento", "kind": "texto",
     "grupo": "Identificação e procedência"},
    {"code": "dados_abertos", "label": "Dados ou materiais disponíveis", "kind": "texto",
     "grupo": "Identificação e procedência",
     "help": "Repositório e link, quando houver"},
    {"code": "relatos_irmaos", "label": "Outros relatos do mesmo estudo",
     "kind": "texto_longo", "grupo": "Identificação e procedência",
     "help": "Dois artigos da mesma coleta são UM estudo. Sem este campo, a "
             "mesma amostra entra duas vezes na síntese"},

    # -- o desenho -------------------------------------------------------
    {"code": "delineamento", "label": "Delineamento", "kind": "escolha",
     "grupo": "Delineamento", "required": 1,
     "options": "Transversal correlacional;Transversal comparativo;"
                "Longitudinal (painel);Coorte prospectiva;Ensaio randomizado;"
                "Ensaio não randomizado ou quase-experimental;"
                "Delineamento de caso único;Qualitativo;Métodos mistos;"
                "Validação de instrumento;Revisão"},
    {"code": "unidade", "label": "Unidade de análise", "kind": "escolha",
     "grupo": "Delineamento",
     "options": "Atleta;Equipe;Díade treinador-atleta;Sessão ou jogo;Outra",
     "help": "Atleta dentro de equipe é dado aninhado, e muda a análise que cabe"},
    {"code": "momentos", "label": "Momentos de coleta", "kind": "texto",
     "grupo": "Delineamento", "help": "Quantos, e quando — “único”, se for um só"},
    {"code": "periodo", "label": "Período da coleta", "kind": "texto",
     "grupo": "Delineamento",
     "help": "Mês e ano, e onde da temporada — pré-temporada não é fim de campeonato"},
    {"code": "amostragem", "label": "Amostragem", "kind": "escolha",
     "grupo": "Delineamento",
     "options": "Conveniência;Aleatória;Estratificada;Censo;Bola de neve;Não declarada"},
    {"code": "calculo_amostral", "label": "Cálculo do tamanho amostral",
     "kind": "texto", "grupo": "Delineamento",
     "help": "O que foi declarado, ou “não declarado”"},
    {"code": "elegibilidade", "label": "Critérios de elegibilidade do estudo",
     "kind": "texto_longo", "grupo": "Delineamento"},

    # -- quem ------------------------------------------------------------
    {"code": "n_total", "label": "N recrutado", "kind": "numero",
     "grupo": "Participantes", "required": 1},
    {"code": "n_analisado", "label": "N analisado", "kind": "numero",
     "grupo": "Participantes",
     "help": "Quase nunca é o mesmo que o recrutado, e é este que vale"},
    {"code": "perdas", "label": "Perdas e recusas", "kind": "texto",
     "grupo": "Participantes", "help": "Quantos, e por quê"},
    {"code": "idade", "label": "Idade", "kind": "texto", "grupo": "Participantes",
     "help": "Média ± DP e faixa"},
    {"code": "sexo", "label": "Sexo", "kind": "texto", "grupo": "Participantes",
     "help": "n e % de cada — e não só “% mulheres”, que some quando não é binário"},
    {"code": "populacao", "label": "Quem eram, e como chegaram ao estudo",
     "kind": "texto_longo", "grupo": "Participantes"},

    # -- o que foi medido ------------------------------------------------
    {"code": "construtos", "label": "Construtos medidos", "kind": "texto_longo",
     "grupo": "Medidas", "required": 1},
    {"code": "instrumentos", "label": "Instrumentos", "kind": "texto_longo",
     "grupo": "Medidas", "help": "Nome, sigla, número de itens e escala de resposta"},
    {"code": "versao_instrumento", "label": "Versão, idioma e validação",
     "kind": "texto_longo", "grupo": "Medidas",
     "help": "Qual tradução, e a referência da validação naquele idioma"},
    {"code": "fidedignidade", "label": "Fidedignidade NA AMOSTRA", "kind": "texto_longo",
     "grupo": "Medidas",
     "help": "α ou ω por subescala, medidos neste estudo — e não os do artigo "
             "de validação. É o campo que mais falta, e o que separa achado de ruído"},
    {"code": "validade", "label": "Evidência de validade relatada", "kind": "texto",
     "grupo": "Medidas", "help": "AFC, invariância, validade convergente"},

    # -- intervencao, quando houver --------------------------------------
    {"code": "houve_intervencao", "label": "Houve intervenção?", "kind": "sim_nao",
     "grupo": "Intervenção",
     "help": "Não havendo, o resto deste grupo fica em branco de propósito"},
    {"code": "intervencao", "label": "Intervenção", "kind": "texto_longo",
     "grupo": "Intervenção",
     "help": "O quê, quem aplicou, como, onde e quanto — o roteiro do TIDieR"},
    {"code": "base_teorica", "label": "Base teórica declarada", "kind": "texto",
     "grupo": "Intervenção"},
    {"code": "duracao", "label": "Duração", "kind": "texto", "grupo": "Intervenção"},
    {"code": "frequencia", "label": "Frequência e dose", "kind": "texto",
     "grupo": "Intervenção"},
    {"code": "comparador", "label": "Comparador", "kind": "texto_longo",
     "grupo": "Intervenção", "help": "O que o outro grupo recebeu — “nada” também é resposta"},
    {"code": "fidelidade", "label": "Fidelidade de implementação", "kind": "texto",
     "grupo": "Intervenção", "help": "Como se verificou que a intervenção aconteceu como descrita"},

    # -- como analisaram -------------------------------------------------
    {"code": "analise", "label": "Método de análise", "kind": "texto_longo",
     "grupo": "Análise", "required": 1},
    {"code": "confundidores", "label": "Confundidores controlados", "kind": "texto",
     "grupo": "Análise"},
    {"code": "aninhamento", "label": "Aninhamento tratado?", "kind": "texto",
     "grupo": "Análise",
     "help": "Atletas da mesma equipe não são observações independentes. "
             "Ignorar isso infla a significância"},
    {"code": "faltantes", "label": "Dados faltantes", "kind": "texto",
     "grupo": "Análise", "help": "Quantos, e o que fizeram com eles"},

    # -- o que acharam ---------------------------------------------------
    {"code": "desfecho_primario", "label": "Desfecho primário", "kind": "texto_longo",
     "grupo": "Resultados", "required": 1},
    {"code": "resultado", "label": "Resultado principal", "kind": "texto_longo",
     "grupo": "Resultados", "required": 1},
    {"code": "tamanho_efeito", "label": "Tamanhos de efeito", "kind": "texto_longo",
     "grupo": "Resultados",
     "help": "d, r, β, η², RR — com intervalo de confiança quando houver. "
             "Valor de p sozinho não diz tamanho de nada"},
    {"code": "nao_significativos", "label": "Resultados não significativos",
     "kind": "texto_longo", "grupo": "Resultados",
     "help": "O PRISMA pede TODOS os resultados. Sem este campo, a extração "
             "copia o resumo — e o resumo conta o que deu certo"},
    {"code": "subgrupos", "label": "Diferenças por subgrupo", "kind": "texto_longo",
     "grupo": "Resultados", "help": "Sexo, idade, nível, categoria"},
    {"code": "conclusao", "label": "Conclusão dos autores", "kind": "texto_longo",
     "grupo": "Resultados"},
    {"code": "limitacoes", "label": "Limitações declaradas", "kind": "texto_longo",
     "grupo": "Resultados"},

    # -- o registro da propria extracao ----------------------------------
    {"code": "texto_completo", "label": "Texto completo obtido?", "kind": "sim_nao",
     "grupo": "Registro da extração",
     "help": "Extração feita só pelo resumo não vale, e precisa aparecer"},
    {"code": "contato_autores", "label": "Contato com os autores", "kind": "texto",
     "grupo": "Registro da extração",
     "help": "Quando, o que se pediu e o que responderam"},
    {"code": "observacoes", "label": "Observações de quem extraiu",
     "kind": "texto_longo", "grupo": "Registro da extração"},
)


# ----------------------------------------------------------------------
# A autodeterminacao no handebol
# ----------------------------------------------------------------------
# O completo, mais o que ESTA revisao pergunta. Um formulario generico
# extrairia "construtos medidos: motivacao intrinseca" e pararia ai -- e
# a revisao que quer saber o que a teoria da autodeterminacao ja disse
# sobre o handebol precisa saber QUAL regulacao, medida por QUAL
# instrumento, em QUE papel no modelo, e o que deu.
#
# Os campos da modalidade existem pela mesma razao. Metade da literatura
# de handebol e de amostra misturada -- handebol, volei e basquete no
# mesmo estudo --, e uma revisao que nao anota a proporcao acaba
# descrevendo esporte coletivo em geral com o nome de handebol. Nivel
# competitivo idem: suporte a autonomia em categoria de base escolar e
# em selecao adulta nao sao o mesmo achado.
FORMULARIO_AUTODETERMINACAO: tuple[dict[str, Any], ...] = FORMULARIO_COMPLETO + (
    {"code": "amostra_handebol", "label": "A amostra é só de handebol?",
     "kind": "sim_nao", "grupo": "Handebol", "required": 1},
    {"code": "proporcao_handebol", "label": "Quantos jogavam handebol",
     "kind": "texto", "grupo": "Handebol",
     "help": "n e % — sem isso, amostra misturada vira “handebol” na síntese"},
    {"code": "nivel", "label": "Nível competitivo", "kind": "escolha",
     "grupo": "Handebol",
     "options": "Escolar ou recreacional;Regional;Nacional;Internacional ou elite;"
                "Misto;Não declarado"},
    {"code": "categoria", "label": "Categoria etária", "kind": "texto",
     "grupo": "Handebol", "help": "Sub-14, sub-16, sub-18, adulto, máster"},
    {"code": "experiencia", "label": "Tempo de prática", "kind": "texto",
     "grupo": "Handebol"},
    {"code": "volume", "label": "Volume de treino", "kind": "texto",
     "grupo": "Handebol", "help": "Horas e sessões por semana"},
    {"code": "quem_respondeu", "label": "Quem respondeu", "kind": "escolha",
     "grupo": "Handebol",
     "options": "Atletas;Treinadores;Pais;Árbitros;Mais de um grupo",
     "help": "Treinador respondendo sobre o próprio estilo não é o atleta "
             "dizendo o que percebe, e a literatura mistura os dois"},

    {"code": "construtos_tad", "label": "Construtos da TAD medidos",
     "kind": "multipla", "grupo": "Autodeterminação", "required": 1,
     "options": "Satisfação das necessidades;Frustração das necessidades;"
                "Autonomia;Competência;Relacionamento;Motivação intrínseca;"
                "Regulação integrada;Regulação identificada;Regulação introjetada;"
                "Regulação externa;Amotivação;Motivação autônoma;"
                "Motivação controlada;Índice de autonomia relativa;"
                "Suporte à autonomia;Estilo controlador;Clima motivacional"},
    {"code": "mini_teoria", "label": "Mini-teoria invocada", "kind": "escolha",
     "grupo": "Autodeterminação",
     "options": "Necessidades psicológicas básicas (BPNT);"
                "Integração organísmica (OIT);Avaliação cognitiva (CET);"
                "Conteúdo de metas (GCT);Motivação nas relações (RMT);"
                "Orientações causais (COT);Não explicitada",
     "help": "“Usamos a TAD” sem dizer qual mini-teoria é o caso mais comum, "
             "e é um achado sobre a literatura"},
    {"code": "papel_tad", "label": "Papel da TAD no modelo", "kind": "escolha",
     "grupo": "Autodeterminação", "required": 1,
     "options": "Variável dependente;Variável independente;Mediadora;Moderadora;"
                "Apenas descritiva;Base da intervenção"},
    {"code": "instrumento_tad", "label": "Instrumento da TAD", "kind": "texto_longo",
     "grupo": "Autodeterminação", "required": 1,
     "help": "BRSQ, SMS, SMS-II, BNSSS, BPNES, PNTS, SCQ, CCBS, PMCSQ-2, "
             "IAR — com a versão e o número de itens"},
    {"code": "alfa_tad", "label": "Fidedignidade das subescalas da TAD",
     "kind": "texto_longo", "grupo": "Autodeterminação",
     "help": "α ou ω de cada regulação, nesta amostra. Amotivação costuma ser "
             "a subescala mais frágil, e o número raramente aparece no resumo"},
    {"code": "correlacoes_tad", "label": "Coeficientes dos construtos da TAD",
     "kind": "texto_longo", "grupo": "Autodeterminação",
     "help": "r, β ou d de cada relação testada, com p e IC — é o que uma "
             "meta-análise futura precisa, e não se recupera do resumo"},
    {"code": "direcao", "label": "O achado sustenta a TAD?", "kind": "escolha",
     "grupo": "Autodeterminação",
     "options": "Sustenta;Sustenta em parte;Não sustenta;Misto;Não testa a teoria"},
)


# ----------------------------------------------------------------------
# Os formularios, para a revisao escolher
# ----------------------------------------------------------------------
# Escolher fica com a revisao e nao com o codigo: uma revisao de
# intervencao nao quer os campos da autodeterminacao, e uma revisao de
# escopo nao quer nenhum dos dois inteiros. O que o codigo faz e ter os
# tres ESCRITOS, para ninguem comecar da folha em branco -- que e como se
# chega a metade dos estudos extraidos sem um campo que faltava.
FORMULARIOS: dict[str, dict[str, Any]] = {
    "padrao": {
        "nome": "Padrão — revisão de intervenção",
        "descricao": "O que quase toda revisão de intervenção precisa. Vinte campos.",
        "campos": FORMULARIO_PADRAO,
    },
    "completo": {
        "nome": "Completo — padrão ouro de revisão sistemática",
        "descricao": "Tudo o que o PRISMA 2020, o manual Cochrane e o JBI pedem "
                     "que se extraia de cada estudo, inclusive o que não deu "
                     "significativo. Cinquenta e um campos, em duplicata.",
        "campos": FORMULARIO_COMPLETO,
    },
    "autodeterminacao": {
        "nome": "Completo + autodeterminação no esporte",
        "descricao": "O completo, mais as regulações do continuum, os "
                     "instrumentos da teoria e a proporção da amostra que "
                     "joga a modalidade.",
        "campos": FORMULARIO_AUTODETERMINACAO,
    },
}


# ----------------------------------------------------------------------
# Risco de vies
# ----------------------------------------------------------------------
# Os instrumentos vivem aqui, e nao no banco, porque sao padrao publicado:
# a RoB 2 tem os dominios que tem, e nao cabe a cada revisao inventar os
# seus. O que vai para o banco e a copia que a revisao usa -- assim uma
# revisao antiga nao muda de instrumento quando o codigo e atualizado.
FERRAMENTAS_ROB: dict[str, dict[str, Any]] = {
    "rob2": {
        "nome": "RoB 2 (Cochrane, ensaios randomizados)",
        "julgamentos": (
            ("baixo", "Baixo risco", "good"),
            ("duvidas", "Algumas dúvidas", "warning"),
            ("alto", "Alto risco", "critical"),
        ),
        "dominios": (
            ("d1", "Processo de randomização"),
            ("d2", "Desvios das intervenções pretendidas"),
            ("d3", "Dados de desfecho faltantes"),
            ("d4", "Mensuração do desfecho"),
            ("d5", "Seleção do resultado relatado"),
        ),
    },
    "robins": {
        "nome": "ROBINS-I (estudos não randomizados de intervenção)",
        "julgamentos": (
            ("baixo", "Baixo risco", "good"),
            ("moderado", "Risco moderado", "warning"),
            ("serio", "Risco sério", "serious"),
            ("critico", "Risco crítico", "critical"),
            ("sem_info", "Sem informação", "neutro"),
        ),
        "dominios": (
            ("d1", "Confundimento"),
            ("d2", "Seleção dos participantes"),
            ("d3", "Classificação das intervenções"),
            ("d4", "Desvios das intervenções pretendidas"),
            ("d5", "Dados faltantes"),
            ("d6", "Mensuração dos desfechos"),
            ("d7", "Seleção do resultado relatado"),
        ),
    },
    # A MMAT existe aqui por uma razao que a lista de cima nao resolve: a
    # ferramenta e UMA POR REVISAO, e ha revisao cujos estudos nao tem
    # todos o mesmo desenho. A da autodeterminacao no handebol e assim --
    # vinte e poucos transversais, um ensaio randomizado, uma coorte,
    # qualitativos e validacoes de instrumento. Avaliar tudo aquilo com a
    # RoB 2 seria julgar transversal por randomizacao que ele nao tem, e
    # com o JBI transversal seria deixar o ensaio sem julgamento.
    #
    # A MMAT foi feita exatamente para isso: duas perguntas de triagem que
    # valem para todo estudo, e cinco criterios por categoria de desenho.
    # Cada estudo responde as duas primeiras e os cinco da SUA categoria;
    # os das outras ficam em "nao se aplica", que e resposta e nao lacuna.
    #
    # E nao tem dominio "geral". Isso nao e esquecimento: a propria MMAT
    # desaconselha somar os criterios num escore unico, porque um numero
    # esconde QUAL criterio falhou -- e e o criterio que muda a leitura do
    # estudo, nao a media dele.
    "mmat": {
        "nome": "MMAT 2018 (desenhos mistos: qualitativo, ensaio, não randomizado, "
                "descritivo e misto)",
        "sem_geral": True,
        "julgamentos": (
            ("sim", "Sim", "good"),
            ("nao", "Não", "critical"),
            ("indeterminado", "Não dá para dizer", "warning"),
            ("na", "Não se aplica", "neutro"),
        ),
        "dominios": (
            ("s1", "T1. As perguntas de pesquisa estão claras?"),
            ("s2", "T2. Os dados coletados permitem responder às perguntas?"),
            ("q1", "1.1 Qualitativo — a abordagem é adequada à pergunta?"),
            ("q2", "1.2 Qualitativo — os métodos de coleta são adequados?"),
            ("q3", "1.3 Qualitativo — os achados derivam dos dados?"),
            ("q4", "1.4 Qualitativo — a interpretação é sustentada pelos dados?"),
            ("q5", "1.5 Qualitativo — há coerência entre dados, análise e interpretação?"),
            ("r1", "2.1 Ensaio randomizado — a randomização foi bem feita?"),
            ("r2", "2.2 Ensaio randomizado — os grupos eram comparáveis no início?"),
            ("r3", "2.3 Ensaio randomizado — os dados de desfecho estão completos?"),
            ("r4", "2.4 Ensaio randomizado — quem avaliou o desfecho estava cego?"),
            ("r5", "2.5 Ensaio randomizado — os participantes aderiram à intervenção?"),
            ("n1", "3.1 Não randomizado — os participantes representam a população-alvo?"),
            ("n2", "3.2 Não randomizado — as medidas do desfecho e da exposição são adequadas?"),
            ("n3", "3.3 Não randomizado — os dados de desfecho estão completos?"),
            ("n4", "3.4 Não randomizado — os confundidores foram considerados?"),
            ("n5", "3.5 Não randomizado — a exposição ocorreu como pretendido?"),
            ("d1", "4.1 Descritivo — a estratégia de amostragem é pertinente?"),
            ("d2", "4.2 Descritivo — a amostra representa a população-alvo?"),
            ("d3", "4.3 Descritivo — as medidas são adequadas?"),
            ("d4", "4.4 Descritivo — o risco de viés de não resposta é baixo?"),
            ("d5", "4.5 Descritivo — a análise estatística responde à pergunta?"),
            ("m1", "5.1 Misto — há justificativa para o delineamento misto?"),
            ("m2", "5.2 Misto — os componentes estão integrados?"),
            ("m3", "5.3 Misto — a integração é adequadamente interpretada?"),
            ("m4", "5.4 Misto — divergências entre os componentes são tratadas?"),
            ("m5", "5.5 Misto — cada componente cumpre os critérios da sua tradição?"),
        ),
    },
    "jbi_transversal": {
        "nome": "JBI — estudos transversais analíticos",
        "julgamentos": (
            ("sim", "Sim", "good"),
            ("nao", "Não", "critical"),
            ("incerto", "Incerto", "warning"),
            ("na", "Não se aplica", "neutro"),
        ),
        "dominios": (
            ("d1", "Critérios de inclusão definidos"),
            ("d2", "Participantes e contexto descritos"),
            ("d3", "Exposição medida de forma válida"),
            ("d4", "Critérios objetivos de medida"),
            ("d5", "Confundidores identificados"),
            ("d6", "Estratégias para lidar com confundidores"),
            ("d7", "Desfechos medidos de forma válida"),
            ("d8", "Análise estatística apropriada"),
        ),
    },
}
GERAL = ("geral", "Risco de viés geral")


def preparar(db: Database, review_id: int, ferramenta: str = "rob2",
             campos: tuple[dict[str, Any], ...] | None = None,
             formulario: str = "padrao") -> dict[str, int]:
    """Instala o formulario e os dominios da ferramenta escolhida.

    Nao apaga o que ja existe: rodar de novo acrescenta o que faltava e
    deixa em paz o que a revisao ja mexeu. Trocar de instrumento no meio
    de uma revisao e decisao seria, e nao pode acontecer por engano.

    Trocar de FORMULARIO no meio tambem nao apaga nada, e pela mesma
    razao: os campos entram por codigo, e o que ja foi extraido continua
    preso ao campo de onde saiu. Uma revisao que comecou no padrao e
    passou para o completo ganha os campos que faltavam e nao perde
    nenhuma linha do que ja tinha sido lido.
    """
    if ferramenta not in FERRAMENTAS_ROB:
        raise ValueError(f"instrumento desconhecido: {ferramenta}. "
                         f"Use {', '.join(FERRAMENTAS_ROB)}")
    if campos is None:
        if formulario not in FORMULARIOS:
            raise ValueError(f"formulário desconhecido: {formulario}. "
                             f"Use {', '.join(FORMULARIOS)}")
        campos = FORMULARIOS[formulario]["campos"]
    for seq, campo in enumerate(campos, start=1):
        db.upsert("extraction_fields", {
            "review_id": review_id, "code": campo["code"], "label": campo["label"],
            "kind": campo.get("kind", "texto"), "options": campo.get("options"),
            "help": campo.get("help"), "grupo": campo.get("grupo"),
            "seq": seq, "required": int(campo.get("required", 0)),
        }, conflict=("review_id", "code"), preserve=("label", "kind", "options", "help"))
    # O dominio "geral" e o julgamento do estudo inteiro, e nem toda
    # ferramenta o tem: a MMAT desaconselha o escore unico por escrito, e
    # acrescenta-lo seria pedir a equipe o que a ferramenta diz para nao
    # fazer.
    dominios = list(FERRAMENTAS_ROB[ferramenta]["dominios"])
    if not FERRAMENTAS_ROB[ferramenta].get("sem_geral"):
        dominios = dominios + [GERAL]
    for seq, (code, label) in enumerate(dominios, start=1):
        db.upsert("rob_domains", {
            "review_id": review_id, "code": code, "label": label, "seq": seq,
        }, conflict=("review_id", "code"), preserve=("label",))
    db.execute("UPDATE reviews SET rob_tool = ?, extraction_form = ?,"
               "       study_designs = COALESCE(study_designs, ?) WHERE id = ?",
               (ferramenta, formulario, ferramenta, review_id))
    db.conn.commit()
    return {"campos": len(campos), "dominios": len(dominios)}


def ferramenta_da(db: Database, review_id: int) -> dict[str, Any]:
    """O instrumento desta revisao.

    Le `rob_tool` primeiro e `study_designs` depois, nesta ordem, por
    causa das revisoes abertas antes de existir a coluna propria: nelas o
    instrumento esta no campo antigo, e ler so o novo faria todas
    voltarem para a RoB 2 de uma migracao para a outra.
    """
    linha = db.dicts("SELECT rob_tool, study_designs FROM reviews WHERE id = ?",
                     (review_id,))
    guardado = (linha[0]["rob_tool"] if linha else None) or \
               (linha[0]["study_designs"] if linha else None)
    codigo = str(guardado or "")
    escolhida = FERRAMENTAS_ROB.get(codigo, FERRAMENTAS_ROB["rob2"])
    return {"codigo": codigo if codigo in FERRAMENTAS_ROB else "rob2", **escolhida}


def formulario_de(db: Database, review_id: int) -> dict[str, Any]:
    """Qual formulario esta revisao usa -- para a tela dizer o nome dele."""
    codigo = str(db.scalar("SELECT extraction_form FROM reviews WHERE id = ?",
                           (review_id,)) or "")
    escolhido = FORMULARIOS.get(codigo)
    if escolhido is None:
        return {"codigo": None, "nome": "Formulário próprio desta revisão",
                "descricao": "Os campos foram definidos aqui, e não por um "
                             "formulário declarado."}
    return {"codigo": codigo, **{k: v for k, v in escolhido.items() if k != "campos"}}


# ----------------------------------------------------------------------
# Preencher
# ----------------------------------------------------------------------
def campos(db: Database, review_id: int) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT id, code, label, kind, options, help, grupo, seq, required"
        "  FROM extraction_fields WHERE review_id = ? ORDER BY seq", (review_id,))


def dominios(db: Database, review_id: int) -> list[dict[str, Any]]:
    return db.dicts("SELECT id, code, label, help, seq FROM rob_domains"
                    " WHERE review_id = ? ORDER BY seq", (review_id,))


def gravar(db: Database, ref_id: int, member_id: int,
           valores: dict[str, Any], risco: dict[str, Any] | None = None) -> dict[str, int]:
    """Grava a extracao de UMA pessoa sobre UM estudo.

    Chave e o codigo do campo, e nao o id: assim o formulario da revisao
    pode ganhar campo novo sem quebrar quem ja tinha a tela aberta.
    """
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    if review_id is None:
        raise ValueError(f"referência {ref_id} não existe")
    por_codigo = {c["code"]: c for c in campos(db, review_id)}
    gravados = 0
    for codigo, valor in (valores or {}).items():
        campo = por_codigo.get(codigo)
        if campo is None:
            continue
        db.upsert("extractions", {
            "ref_id": ref_id, "member_id": member_id, "field_id": campo["id"],
            "value": _texto(valor), "updated_at": db.scalar("SELECT datetime('now')"),
        }, conflict=("ref_id", "member_id", "field_id"))
        gravados += 1

    dominios_por_codigo = {d["code"]: d for d in dominios(db, review_id)}
    julgamentos = {j[0] for j in ferramenta_da(db, review_id)["julgamentos"]}
    riscos = 0
    for codigo, resposta in (risco or {}).items():
        dominio = dominios_por_codigo.get(codigo)
        if dominio is None:
            continue
        item = resposta if isinstance(resposta, dict) else {"julgamento": resposta}
        julgamento = clean_text(item.get("julgamento"))
        if julgamento not in julgamentos:
            raise ValueError(
                f"julgamento desconhecido: {julgamento}. Use {', '.join(sorted(julgamentos))}")
        db.upsert("rob_answers", {
            "ref_id": ref_id, "member_id": member_id, "domain_id": dominio["id"],
            "judgement": julgamento, "support": clean_text(item.get("justificativa")),
            "updated_at": db.scalar("SELECT datetime('now')"),
        }, conflict=("ref_id", "member_id", "domain_id"))
        riscos += 1
    db.conn.commit()
    return {"campos": gravados, "dominios": riscos}


def minha_extracao(db: Database, ref_id: int, member_id: int) -> dict[str, Any]:
    valores = {linha["code"]: linha["value"] for linha in db.dicts(
        "SELECT f.code, e.value FROM extractions e"
        "  JOIN extraction_fields f ON f.id = e.field_id"
        " WHERE e.ref_id = ? AND e.member_id = ?", (ref_id, member_id))}
    risco = {linha["code"]: {"julgamento": linha["judgement"],
                             "justificativa": linha["support"]}
             for linha in db.dicts(
        "SELECT d.code, a.judgement, a.support FROM rob_answers a"
        "  JOIN rob_domains d ON d.id = a.domain_id"
        " WHERE a.ref_id = ? AND a.member_id = ?", (ref_id, member_id))}
    return {"valores": valores, "risco": risco}


# ----------------------------------------------------------------------
# Comparar e acordar
# ----------------------------------------------------------------------
def divergencias(db: Database, ref_id: int) -> dict[str, Any]:
    """Onde as extracoes discordam -- campo a campo, dominio a dominio.

    So faz sentido depois de duas pessoas terem preenchido. Antes disso a
    comparacao seria entre uma extracao e o vazio, e apontaria diferenca
    em tudo.
    """
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    quem = db.dicts(
        "SELECT DISTINCT m.id, m.full_name FROM extractions e"
        "  JOIN members m ON m.id = e.member_id WHERE e.ref_id = ?"
        " UNION SELECT DISTINCT m.id, m.full_name FROM rob_answers a"
        "  JOIN members m ON m.id = a.member_id WHERE a.ref_id = ?"
        " ORDER BY 2", (ref_id, ref_id))
    por_pessoa = {p["id"]: minha_extracao(db, ref_id, p["id"]) for p in quem}
    final = versao_final(db, ref_id)

    campos_diff, iguais = [], []
    for campo in campos(db, review_id):
        respostas = {p["full_name"]: (por_pessoa[p["id"]]["valores"].get(campo["code"]) or "")
                     for p in quem}
        valores = {v.strip() for v in respostas.values()}
        acordado = final["valores"].get(campo["code"])
        item = {**campo, "respostas": respostas, "final": acordado,
                "resolvida": acordado not in (None, ""),
                "sugestao": next((v for v in respostas.values() if v.strip()), "")}
        (iguais if len(valores) <= 1 else campos_diff).append(item)

    risco_diff, risco_iguais = [], []
    for dominio in dominios(db, review_id):
        respostas = {p["full_name"]: por_pessoa[p["id"]]["risco"].get(dominio["code"])
                     for p in quem}
        julgamentos = {(r or {}).get("julgamento") for r in respostas.values()}
        acordado = final["risco"].get(dominio["code"])
        item = {**dominio, "respostas": respostas, "final": acordado,
                "resolvida": bool(acordado)}
        (risco_iguais if len(julgamentos) <= 1 else risco_diff).append(item)

    return {"pessoas": quem, "divergencias": campos_diff, "acordo": iguais,
            "risco_divergente": risco_diff, "risco_acordo": risco_iguais,
            "pronto": len(quem) >= 2}


def acordar(db: Database, ref_id: int, member_id: int,
            valores: dict[str, Any] | None = None,
            risco: dict[str, Any] | None = None) -> dict[str, int]:
    """Grava a versao final -- a que vai para a tabela do artigo."""
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    if review_id is None:
        raise ValueError(f"referência {ref_id} não existe")
    por_codigo = {c["code"]: c for c in campos(db, review_id)}
    agora = db.scalar("SELECT datetime('now')")
    n = 0
    for codigo, valor in (valores or {}).items():
        campo = por_codigo.get(codigo)
        if campo is None:
            continue
        db.execute(
            "INSERT INTO extraction_final (ref_id, field_id, value, decided_by, decided_at)"
            " VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT (ref_id, field_id) DO UPDATE SET value = excluded.value,"
            "   decided_by = excluded.decided_by, decided_at = excluded.decided_at",
            (ref_id, campo["id"], _texto(valor), member_id, agora))
        n += 1
    dominios_por_codigo = {d["code"]: d for d in dominios(db, review_id)}
    julgamentos = {j[0] for j in ferramenta_da(db, review_id)["julgamentos"]}
    r = 0
    for codigo, resposta in (risco or {}).items():
        dominio = dominios_por_codigo.get(codigo)
        if dominio is None:
            continue
        item = resposta if isinstance(resposta, dict) else {"julgamento": resposta}
        julgamento = clean_text(item.get("julgamento"))
        if julgamento not in julgamentos:
            raise ValueError(f"julgamento desconhecido: {julgamento}")
        db.execute(
            "INSERT INTO rob_final (ref_id, domain_id, judgement, support, decided_by, decided_at)"
            " VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (ref_id, domain_id) DO UPDATE SET judgement = excluded.judgement,"
            "   support = excluded.support, decided_by = excluded.decided_by,"
            "   decided_at = excluded.decided_at",
            (ref_id, dominio["id"], julgamento, clean_text(item.get("justificativa")),
             member_id, agora))
        r += 1
    db.conn.commit()
    return {"campos": n, "dominios": r}


def versao_final(db: Database, ref_id: int) -> dict[str, Any]:
    valores = {linha["code"]: linha["value"] for linha in db.dicts(
        "SELECT f.code, x.value FROM extraction_final x"
        "  JOIN extraction_fields f ON f.id = x.field_id WHERE x.ref_id = ?", (ref_id,))}
    risco = {linha["code"]: {"julgamento": linha["judgement"],
                             "justificativa": linha["support"]}
             for linha in db.dicts(
        "SELECT d.code, x.judgement, x.support FROM rob_final x"
        "  JOIN rob_domains d ON d.id = x.domain_id WHERE x.ref_id = ?", (ref_id,))}
    return {"valores": valores, "risco": risco}


# ----------------------------------------------------------------------
# As saidas
# ----------------------------------------------------------------------
def consenso(db: Database, ref_id: int) -> dict[str, dict[str, Any]]:
    """O valor que vale para cada campo, e de onde ele veio.

    Tres origens, nesta ordem:

      `acordado`   alguem conciliou as duas extracoes e gravou a final
      `unanime`    as duas pessoas escreveram a mesma coisa -- e isso JA e
                   consenso; exigir um clique para confirmar o que ninguem
                   contesta e trabalho inutil, e trabalho inutil e pulado
      `provisorio` so uma pessoa extraiu, ou as duas discordam e ninguem
                   conciliou ainda

    A origem viaja junto com o valor porque a tabela precisa mostrar a
    diferenca: celula vazia parece "nao se aplica", e nao "ainda nao
    conferimos".
    """
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    final = versao_final(db, ref_id)["valores"]
    por_campo: dict[str, list[str]] = {}
    for linha in db.dicts(
            "SELECT f.code, e.value FROM extractions e"
            "  JOIN extraction_fields f ON f.id = e.field_id"
            " WHERE e.ref_id = ? ORDER BY e.updated_at", (ref_id,)):
        por_campo.setdefault(linha["code"], []).append((linha["value"] or "").strip())

    saida: dict[str, dict[str, Any]] = {}
    for campo in campos(db, review_id):
        codigo = campo["code"]
        acordado = final.get(codigo)
        if acordado not in (None, ""):
            saida[codigo] = {"valor": acordado, "origem": "acordado"}
            continue
        dadas = [v for v in por_campo.get(codigo, []) if v]
        if dadas and len(set(dadas)) == 1 and len(dadas) >= 2:
            saida[codigo] = {"valor": dadas[0], "origem": "unanime"}
        elif dadas:
            saida[codigo] = {"valor": dadas[0], "origem": "provisorio"}
        else:
            saida[codigo] = {"valor": "", "origem": "vazio"}
    return saida


def consenso_risco(db: Database, ref_id: int) -> dict[str, dict[str, Any]]:
    """O mesmo, para os dominios de risco de vies."""
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    final = versao_final(db, ref_id)["risco"]
    por_dominio: dict[str, list[dict[str, Any]]] = {}
    for linha in db.dicts(
            "SELECT d.code, a.judgement, a.support FROM rob_answers a"
            "  JOIN rob_domains d ON d.id = a.domain_id"
            " WHERE a.ref_id = ? ORDER BY a.updated_at", (ref_id,)):
        por_dominio.setdefault(linha["code"], []).append(linha)

    saida: dict[str, dict[str, Any]] = {}
    for dominio in dominios(db, review_id):
        codigo = dominio["code"]
        acordado = final.get(codigo)
        if acordado:
            saida[codigo] = {**acordado, "origem": "acordado"}
            continue
        dadas = por_dominio.get(codigo, [])
        julgamentos = {d["judgement"] for d in dadas}
        if len(julgamentos) == 1 and len(dadas) >= 2:
            saida[codigo] = {"julgamento": dadas[0]["judgement"],
                             "justificativa": dadas[0]["support"], "origem": "unanime"}
        elif dadas:
            saida[codigo] = {"julgamento": dadas[0]["judgement"],
                             "justificativa": dadas[0]["support"], "origem": "provisorio"}
        else:
            saida[codigo] = {"julgamento": None, "origem": "vazio"}
    return saida


def tabela(db: Database, review_id: int) -> dict[str, Any]:
    """A tabela de caracteristicas dos estudos incluidos.

    Cada linha e um estudo, cada coluna um campo do formulario. O valor
    e o acordado; onde ainda nao houve acordo, mostra-se o que uma pessoa
    escreveu, marcado como provisorio -- em branco pareceria "nao se
    aplica", e nao "ainda nao conferimos".
    """
    incluidos = db.dicts(
        "SELECT id, title, authors, journal, year, doi FROM refs"
        " WHERE review_id = ? AND stage = 'incluido' AND duplicate_of IS NULL"
        " ORDER BY COALESCE(year, 0), title", (review_id,))
    lista_campos = campos(db, review_id)
    linhas = []
    for estudo in incluidos:
        celulas = consenso(db, estudo["id"])
        linhas.append({**estudo, "estudo": _citacao(estudo), "celulas": celulas})
    return {"campos": lista_campos, "estudos": linhas}


def _citacao(estudo: dict[str, Any]) -> str:
    """'Vilarino et al., 2023' -- como o estudo aparece na tabela."""
    autores = [p.strip() for p in str(estudo.get("authors") or "").split(";") if p.strip()]
    if not autores:
        return str(estudo.get("title") or "sem autoria")[:60]
    primeiro = autores[0].split(",")[0].strip() or autores[0]
    sufixo = " et al." if len(autores) > 2 else (f" & {autores[1].split(',')[0].strip()}"
                                                 if len(autores) == 2 else "")
    return f"{primeiro}{sufixo}, {estudo.get('year') or 's.d.'}"


def semaforo(db: Database, review_id: int) -> dict[str, Any]:
    """Os dados do semaforo de risco de vies: estudos x dominios."""
    ferramenta = ferramenta_da(db, review_id)
    tons = {codigo: tom for codigo, _, tom in ferramenta["julgamentos"]}
    rotulos = {codigo: rotulo for codigo, rotulo, _ in ferramenta["julgamentos"]}
    lista_dominios = dominios(db, review_id)
    estudos = db.dicts(
        "SELECT id, title, authors, year FROM refs"
        " WHERE review_id = ? AND stage = 'incluido' AND duplicate_of IS NULL"
        " ORDER BY COALESCE(year, 0), title", (review_id,))
    linhas, resumo = [], {d["code"]: {} for d in lista_dominios}
    for estudo in estudos:
        acordado = consenso_risco(db, estudo["id"])
        celulas = []
        for dominio in lista_dominios:
            item = acordado.get(dominio["code"]) or {}
            julgamento = item.get("julgamento")
            celulas.append({
                "dominio": dominio["code"], "julgamento": julgamento,
                "rotulo": rotulos.get(julgamento, "Sem julgamento"),
                "tom": tons.get(julgamento, "neutro"),
                "origem": item.get("origem", "vazio"),
                "justificativa": item.get("justificativa"),
            })
            chave = julgamento or "sem_julgamento"
            resumo[dominio["code"]][chave] = resumo[dominio["code"]].get(chave, 0) + 1
        linhas.append({"estudo": _citacao(estudo), "ref_id": estudo["id"],
                       "title": estudo["title"], "celulas": celulas})
    legenda = [{"codigo": c, "rotulo": r, "tom": t}
               for c, r, t in ferramenta["julgamentos"]]
    # Circulo cinza aparece na grade sempre que um dominio ainda nao foi
    # julgado. Se ele nao estiver na legenda, o desenho tem um simbolo sem
    # significado -- e quem le nao sabe se e "sem risco" ou "sem resposta".
    if any(c["julgamento"] is None for linha in linhas for c in linha["celulas"]):
        legenda.append({"codigo": None, "rotulo": "Sem julgamento", "tom": "neutro"})
    return {"ferramenta": ferramenta["nome"], "codigo": ferramenta["codigo"],
            "julgamentos": legenda,
            "dominios": lista_dominios, "estudos": linhas, "resumo": resumo}


def progresso(db: Database, review_id: int) -> dict[str, Any]:
    """Quanto da extracao ja foi feita, e por quem."""
    incluidos = int(db.scalar(
        "SELECT COUNT(*) FROM refs WHERE review_id = ? AND stage = 'incluido'"
        "   AND duplicate_of IS NULL", (review_id,)) or 0)
    com_duas = int(db.scalar(
        "SELECT COUNT(*) FROM (SELECT e.ref_id FROM extractions e"
        "   JOIN refs r ON r.id = e.ref_id WHERE r.review_id = ?"
        "   GROUP BY e.ref_id HAVING COUNT(DISTINCT e.member_id) >= 2)", (review_id,)) or 0)
    acordados = int(db.scalar(
        "SELECT COUNT(DISTINCT x.ref_id) FROM extraction_final x"
        "  JOIN refs r ON r.id = x.ref_id WHERE r.review_id = ?", (review_id,)) or 0)
    return {
        "incluidos": incluidos, "com_duas_extracoes": com_duas, "acordados": acordados,
        "por_pessoa": db.dicts(
            "SELECT m.full_name AS quem, COUNT(DISTINCT e.ref_id) AS estudos,"
            "       COUNT(*) AS campos, MAX(e.updated_at) AS ultima"
            "  FROM extractions e JOIN members m ON m.id = e.member_id"
            "  JOIN refs r ON r.id = e.ref_id WHERE r.review_id = ?"
            " GROUP BY m.id ORDER BY estudos DESC", (review_id,)),
    }


def _texto(valor: Any) -> str | None:
    if isinstance(valor, (list, tuple)):
        return "; ".join(str(v) for v in valor if str(v).strip()) or None
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    return clean_text(valor)
