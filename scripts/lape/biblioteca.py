"""A biblioteca: o acervo de leitura da equipe, atualizado sozinho.

Nao e uma revisao sistematica, e a diferenca importa. A revisao responde
UMA pergunta, tem triagem em duplicata, criterio de exclusao escrito antes
e fecha num numero. A biblioteca fica aberta: e o que a equipe le sobre um
assunto, atualizado sozinho, para ninguem repetir a mesma busca toda
semana nem chegar a um artigo pela terceira vez sem saber que ja o tinha.

O que ela nao faz, e nao deve fazer: triar. Um artigo entrar aqui nao diz
que ele responde a pergunta de ninguem -- diz que ele esta no assunto e
que a equipe deveria saber que existe. Quem triar e a revisao, que e outro
modulo, com dois avaliadores e kappa.

A estrategia de cada acervo fica ESCRITA, e nao digitada a cada vez, pelo
mesmo motivo das linhas de pesquisa: e o resultado de conferir quanto cada
termo traz, e conferir isso de novo a cada busca e como o erro entra.
"""
from __future__ import annotations

import json
import time
from datetime import date
from typing import Any, Callable

from . import config, referencias
from .db import Database
from .util import clean_text, norm_doi

# ----------------------------------------------------------------------
# Os enderecos de cada artigo, base por base
# ----------------------------------------------------------------------
# Duas bases respondem por identificador e tres so por busca. A diferenca
# nao e detalhe: um link que abre NO artigo poupa a pessoa; um que abre na
# busca a deixa conferindo se o resultado e mesmo aquele. A tela marca
# quais sao quais, para ninguem clicar esperando a primeira coisa e
# receber a segunda.
DIRETO = "direto"
BUSCA = "busca"


def links(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Todos os caminhos ate o artigo, do mais direto ao menos.

    A ordem e a da certeza, e nao a do prestigio da base: o DOI aponta
    para UM artigo e nao erra; a busca por titulo na Scopus pode trazer
    outro. Pôr a Scopus em primeiro por ser Scopus mandaria a pessoa para
    o caminho mais incerto primeiro.
    """
    import urllib.parse

    doi = norm_doi(item.get("doi"))
    titulo = clean_text(item.get("title")) or ""
    saida: list[dict[str, Any]] = []

    if doi:
        saida.append({"base": "DOI", "tipo": DIRETO, "forte": True,
                      "url": "https://doi.org/" + doi,
                      "dica": "abre o artigo na editora"})
    if item.get("pmid"):
        saida.append({"base": "PubMed", "tipo": DIRETO,
                      "url": f"https://pubmed.ncbi.nlm.nih.gov/{item['pmid']}/",
                      "dica": "registro na PubMed"})
    if item.get("pmc"):
        saida.append({"base": "PMC", "tipo": DIRETO, "livre": True,
                      "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{item['pmc']}/",
                      "dica": "texto completo livre"})
    if item.get("oa_url"):
        saida.append({"base": "Acesso aberto", "tipo": DIRETO, "livre": True,
                      "url": item["oa_url"], "dica": "PDF livre"})

    # As bases fechadas nao abrem por DOI sem convenio, mas a busca por DOI
    # dentro delas cai num resultado so -- e de dentro da universidade ela
    # abre direto. Por titulo, quando nao ha DOI, o resultado e incerto: a
    # tela diz isso em vez de prometer o artigo.
    if doi:
        saida.append({"base": "Scopus", "tipo": BUSCA,
                      "url": "https://www.scopus.com/results/results.uri?st1="
                             + urllib.parse.quote(f'DOI("{doi}")') + "&sot=b&sdt=b",
                      "dica": "busca pelo DOI; abre de dentro da UDESC"})
        saida.append({"base": "Web of Science", "tipo": BUSCA,
                      "url": "https://www.webofscience.com/wos/woscc/basic-search?"
                             + urllib.parse.urlencode({"q": f"DO=({doi})"}),
                      "dica": "busca pelo DOI; depende da assinatura"})
    elif titulo:
        saida.append({"base": "Scopus", "tipo": BUSCA,
                      "url": "https://www.scopus.com/results/results.uri?st1="
                             + urllib.parse.quote(titulo[:200]) + "&sot=b&sdt=b",
                      "dica": "busca pelo título — confira se é o mesmo artigo"})

    # A LILACS nao indexa por DOI de maneira confiavel: a busca vai pelo
    # titulo. Ela entra porque e onde esta a producao latino-americana que
    # as outras tres nao indexam -- e boa parte do que o LAPE publica e o
    # que os vizinhos publicam mora la.
    if titulo:
        saida.append({"base": "LILACS", "tipo": BUSCA,
                      "url": "https://pesquisa.bvsalud.org/portal/?"
                             + urllib.parse.urlencode({"q": titulo[:200], "lang": "pt"}),
                      "dica": "produção latino-americana; busca pelo título"})
    if doi:
        saida.append({"base": "Google Acadêmico", "tipo": BUSCA,
                      "url": "https://scholar.google.com/scholar?"
                             + urllib.parse.urlencode({"q": doi}),
                      "dica": "quem citou, e versões livres"})
    return saida


# ----------------------------------------------------------------------
# O vocabulario, e a sintaxe de cada base
# ----------------------------------------------------------------------
# O vocabulario e declarado UMA vez, em portugues claro: uma lista de
# expressoes. A sintaxe de cada base sai dela.
#
# Escrever a estrategia tres vezes -- uma por base -- seria garantir que
# as tres divergissem: alguem acrescenta um termo na da PubMed, esquece as
# outras duas, e o acervo passa a ter tres tamanhos diferentes sem que
# nada na tela explique por que. Um termo novo entra aqui, numa linha, e
# vale para as tres.
PUBMED, SCOPUS, WOS = "pubmed", "scopus", "wos"
# As tres que o sistema consulta sozinho, porque tem API.
BASES = (PUBMED, SCOPUS, WOS)

# As que NAO tem API aberta -- ou tem e a universidade nao assina o acesso
# por programa. A estrategia delas e montada e GUARDADA do mesmo jeito, e
# quem tem acesso cola na base e traz o resultado.
#
# Por que guardar uma busca que o sistema nao roda: porque uma revisao
# sistematica tem de publicar a estrategia de CADA base, com a data e o
# numero de registros. Montada a mao na hora, ela sai diferente em cada
# base e ninguem consegue refazer um ano depois -- que e exatamente o que
# o revisor da banca pede para conferir.
#
# E porque uma revisao de fibromialgia sem Embase e sem PsycINFO nao esta
# completa, e dizer "o sistema so alcanca tres bases" nao muda isso: muda
# so de quem e o trabalho.
EMBASE, PSYCINFO, CINAHL = "embase", "psycinfo", "cinahl"
COCHRANE, LILACS = "cochrane", "lilacs"
# A SPORTDiscus nao e "mais uma": para psicologia do esporte ela e a base
# do campo. Indexa as revistas que a PubMed nao indexa -- Journal of Sport
# and Exercise Psychology, The Sport Psychologist, International Journal
# of Sport and Exercise Psychology, Psychology of Sport and Exercise --, e
# uma revisao de motivacao no esporte sem ela deixa de fora justamente a
# literatura mais central. E da EBSCO, como a PsycINFO e a CINAHL, e por
# isso a estrategia sai na mesma sintaxe.
SPORTDISCUS = "sportdiscus"
BASES_MANUAIS = (EMBASE, PSYCINFO, CINAHL, COCHRANE, LILACS, SPORTDISCUS)

ROTULO_BASE = {
    PUBMED: "PubMed", SCOPUS: "Scopus", WOS: "Web of Science",
    EMBASE: "Embase", PSYCINFO: "PsycINFO", CINAHL: "CINAHL",
    COCHRANE: "Cochrane CENTRAL", LILACS: "LILACS / BVS",
    SPORTDISCUS: "SPORTDiscus",
}

# O que dizer de cada base que o sistema nao roda. A frase e o recado da
# tela, e ela precisa dizer O QUE FAZER -- "sem API" nao e instrucao.
PORQUE_MANUAL = {
    EMBASE: "A Embase não tem API aberta. Cole a estratégia em embase.com, "
            "com o acesso da universidade.",
    PSYCINFO: "A PsycINFO é vendida pela EBSCO e pela ProQuest, e a sintaxe "
              "muda entre as duas. A estratégia aqui está em EBSCO — confira "
              "por qual plataforma a UDESC assina antes de colar.",
    CINAHL: "A CINAHL é da EBSCO e não tem API aberta. Cole a estratégia na "
            "interface, com o acesso da universidade.",
    COCHRANE: "A Cochrane Library não tem API aberta. Cole a estratégia em "
              "cochranelibrary.com — a CENTRAL é onde estão os ensaios.",
    LILACS: "A BVS não tem API estável. Cole em pesquisa.bvsalud.org — e é "
            "a única busca deste acervo em português e espanhol.",
    SPORTDISCUS: "A SPORTDiscus é da EBSCO e não tem API aberta. Cole a "
                 "estratégia na interface, com o acesso da universidade — é "
                 "nela que estão as revistas de psicologia do esporte que a "
                 "PubMed não indexa.",
}


def frase(termos: tuple[str, ...], base: str) -> str:
    """As expressoes, na sintaxe da base, procurando em titulo e resumo.

    Sempre titulo-resumo-palavra-chave, nunca "todos os campos". Em
    "todos os campos" a PubMed traduz `POMS` para o nome de uma revista de
    gestao de operacoes, e a Scopus acha o termo na lista de referencias
    de artigos que nao sao do assunto. O recorte estreito e o que faz a
    busca ser sobre o texto, e nao sobre o que ha em volta dele.
    """
    limpos = [t.strip() for t in termos if t and t.strip()]
    if not limpos:
        return ""
    if base == PUBMED:
        return " OR ".join(f'"{t}"[Title/Abstract]' for t in limpos)
    if base == SCOPUS:
        return " OR ".join(f'TITLE-ABS-KEY("{t}")' for t in limpos)
    if base == WOS:
        # A WoS agrupa o campo de fora: TS=(a OR b), e nao TS=(a) OR TS=(b).
        return "TS=(" + " OR ".join(f'"{t}"' for t in limpos) + ")"
    if base == EMBASE:
        # Embase.com: aspas simples e os campos depois dos dois-pontos.
        return " OR ".join(f"'{t}':ti,ab,kw" for t in limpos)
    if base == COCHRANE:
        # Cochrane Library: igual na ideia, aspas duplas.
        return " OR ".join(f'"{t}":ti,ab,kw' for t in limpos)
    if base in (PSYCINFO, CINAHL, SPORTDISCUS):
        # EBSCO: um codigo de campo por termo, e os dois campos separados.
        return " OR ".join(f'TI "{t}" OR AB "{t}"' for t in limpos)
    if base == LILACS:
        # BVS: campo minusculo com o termo entre parenteses.
        return " OR ".join(f'ti:("{t}") OR ab:("{t}")' for t in limpos)
    raise ValueError(f"base desconhecida: {base}")


# ----------------------------------------------------------------------
# Os acervos declarados
# ----------------------------------------------------------------------
# A populacao e "atleta", e nao "esporte". A diferenca custou metade do
# acervo e vale a pena escrever: com `"sports"[MeSH]` a busca traz 847
# registros e entre eles programas comunitarios de caminhada, que tem
# estado de humor medido e nao tem atleta nenhum. Fechando em atleta, sao
# 431 -- e sao de quem a pergunta e sobre.
HUMOR_TERMOS = (
    "Profile of Mood States", "mood state", "mood states", "mood profile",
    "mood disturbance", "POMS", "BRUMS", "Brunel Mood Scale", "iceberg profile",
)
ATLETA_TERMOS = ("athlete", "athletes", "elite sport", "competitive sport")

# O MeSH so existe na PubMed. Entra como acrescimo, e nao no vocabulario
# comum: gerar `TITLE-ABS-KEY("athletes[MeSH Terms]")` para a Scopus
# mandaria a base procurar essa sequencia literal de caracteres num
# resumo, e ela nao acharia nada -- sem erro, so zero.
#
# E o MeSH e DE CADA ACERVO, nunca do modulo. Este valor estava fixo aqui
# e somado com OR a populacao de QUALQUER acervo -- o que funcionava por
# acidente, enquanto houve um acervo so, cuja populacao era "atleta".
#
# Com o segundo acervo o acidente virou defeito: OR entre `athletes[MeSH]`
# e a lista de esportes esteticos ALARGA a populacao de volta para atleta
# em geral, e o recorte estetico desaparece sem deixar erro. Conferido na
# PubMed, mesma janela de humor: 11 registros pela lista de termos
# esteticos, 17 pelo MeSH das modalidades -- e 139 com o `athletes[MeSH]`
# somado, quase todos humor em atleta de outra modalidade. Dez vezes mais
# acervo, e do assunto errado.
MESH_DE_ATLETA = ('"athletes"[MeSH Terms]',)

# Os esportes em que o acervo se divide, com as palavras de cada um. A
# lista sai do que a literatura de humor no esporte de fato estuda -- nao
# de uma relacao de modalidades olimpicas, que traria dezenas de
# segmentos vazios e faria a tela parecer quebrada.
ESPORTES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Futebol", ("soccer", "football")),
    ("Natação", ("swimming", "swimmers")),
    ("Atletismo", ("track and field", "runners", "distance running")),
    ("Handebol", ("handball",)),
    ("Basquete", ("basketball",)),
    ("Vôlei", ("volleyball",)),
    ("Judô e lutas", ("judo", "wrestling", "combat sport", "combat sports",
                      "taekwondo", "karate")),
    ("Ginástica", ("gymnastics", "gymnasts")),
    ("Ciclismo", ("cycling", "cyclists")),
    ("Remo e canoagem", ("rowing", "rowers", "canoeing", "kayak")),
    ("Tênis e raquete", ("tennis", "badminton", "table tennis")),
    ("Paradesporto", ("paralympic", "para athletes", "disability sport")),
    ("Rugby e futebol americano", ("rugby", "american football")),
    ("Triatlo", ("triathlon", "triathletes")),
)

# ----------------------------------------------------------------------
# Esportes esteticos
# ----------------------------------------------------------------------
# "Estetico" aqui e a categoria da literatura, e nao um juizo: modalidade
# em que a NOTA depende da aparencia do movimento -- e nao do tempo, da
# distancia ou do gol. E o que junta ginastica, nado artistico, patinacao
# e ballet numa mesma pergunta: as quatro premiam linha corporal, e e por
# isso que a literatura de humor nelas gira em torno de imagem corporal,
# peso e alimentacao, e nao em torno de carga aerobica.
#
# TRES ARMADILHAS DE TERMO, cada uma custou um pedaco de acervo:
#
#   "diving" sozinho traz mergulho autonomo -- descompressao, nitrogenio,
#   mergulhador tecnico. Nada disso e salto ornamental. Vai qualificado.
#
#   "dance" sozinho traz aula de danca em casa de repouso, danca como
#   intervencao em Parkinson e danca recreativa na escola. Sao trabalhos
#   legitimos e sao de OUTRA pergunta -- este acervo e de quem COMPETE ou
#   treina em nivel de performance. Vai qualificado tambem.
#
#   "synchronized swimming" continua indispensavel: a modalidade mudou de
#   nome para "artistic swimming" em 2017, e vinte anos de literatura
#   estao sob o nome antigo. Buscar so pelo novo apaga a metade mais
#   antiga do acervo sem avisar.
ESTETICOS_TERMOS = (
    "aesthetic sport", "aesthetic sports",
    "artistic gymnastics", "rhythmic gymnastics", "gymnastics", "gymnast", "gymnasts",
    "trampoline gymnastics", "acrobatic gymnastics",
    "artistic swimming", "synchronized swimming",
    "figure skating", "figure skater", "figure skaters",
    "springboard diving", "platform diving", "competitive diving",
    "ballet", "ballet dancer", "ballet dancers",
    "dance sport", "dancesport", "competitive dance", "professional dancer",
    "cheerleading",
)

# Os temas em que o acervo se divide. Aqui o eixo NAO e a modalidade -- a
# modalidade e a populacao, e ficaria repetida em todos os segmentos. O
# eixo e a pergunta, e a lista sai do que a literatura de humor em
# esporte estetico de fato tem: imagem corporal e alimentacao dominam, e
# e justamente o que nao aparece na biblioteca de humor em geral.
TEMAS_ESTETICOS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Imagem corporal e alimentação",
     ("body image", "body dissatisfaction", "disordered eating", "eating disorder",
      "eating disorders", "eating attitudes", "weight control", "weight pressure",
      "relative energy deficiency", "RED-S", "female athlete triad")),
    ("Ansiedade e perfeccionismo",
     ("competitive anxiety", "competitive state anxiety", "perfectionism",
      "fear of failure", "self-presentation", "social physique anxiety")),
    ("Carga, recuperação e overtraining",
     ("overtraining", "overreaching", "training load", "training monotony",
      "recovery", "burnout", "staleness")),
    ("Desempenho e competição",
     ("performance", "competition", "precompetitive", "pre-competitive",
      "competitive season")),
    ("Maturação e idade",
     ("maturation", "puberty", "pubertal", "adolescent athletes",
      "young athletes", "youth sport", "early specialization")),
    ("Lesão e dor",
     ("injury", "injuries", "pain", "low back pain", "return to sport")),
)

# ----------------------------------------------------------------------
# Fibromialgia
# ----------------------------------------------------------------------
# Aqui a condicao E a populacao: nao ha um segundo bloco para cruzar. O
# acervo e tudo que existe sobre fibromialgia, e o recorte vem dos temas.
#
# O nome da doenca mudou de forma tres vezes na literatura, e as tres
# formas continuam valendo em bases diferentes: "fibromyalgia",
# "fibromyalgia syndrome" e "fibrositis" -- esta ultima e o nome antigo,
# usado ate os anos 80, e e como esta indexada a literatura mais velha.
# Tirar `fibrositis` nao muda quase nada no total e apaga justamente os
# trabalhos historicos, que e o que uma revisao usa para datar o inicio
# do campo.
#
# "chronic widespread pain" NAO entra: e um diagnostico vizinho e mais
# amplo, com criterio proprio, e somar os dois num acervo so faz a
# pergunta deixar de ser sobre fibromialgia. Quem quiser os dois cruza
# dois acervos -- que e uma decisao, e nao um efeito colateral de um
# termo a mais.
FIBROMIALGIA_TERMOS = (
    "fibromyalgia", "fibromyalgia syndrome", "fibromyalgic", "fibrositis",
)

# EM PORTUGUES E ESPANHOL, para a BVS. Sem isto, uma revisao brasileira de
# fibromialgia busca a America Latina em ingles e nao acha nada -- e a
# literatura que ela mais perde e justamente a de casa. A LILACS indexa
# resumo no idioma de origem.
FIBROMIALGIA_REGIONAIS = (
    "fibromialgia", "síndrome fibromiálgica", "sindrome fibromialgica",
    "fibromiálgica", "fibromialgico",
)

# Os temas em que o acervo se divide. Sai do que a literatura de
# fibromialgia tem, e nao de uma lista de desfechos possiveis: exercicio
# e dor dominam, e saude mental vem logo depois -- que e o cruzamento
# desta linha de pesquisa com a psicologia do exercicio.
TEMAS_FIBROMIALGIA: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Exercício e atividade física",
     ("exercise", "physical activity", "aerobic training", "resistance training",
      "strength training", "aquatic exercise", "hydrotherapy", "physical exercise")),
    ("Dor e sintomas",
     ("pain", "pain threshold", "hyperalgesia", "tender points", "central sensitization",
      "widespread pain", "pain catastrophizing")),
    ("Saúde mental e humor",
     ("depression", "anxiety", "mood", "mood states", "psychological distress",
      "quality of life", "catastrophizing", "self-efficacy")),
    ("Sono e fadiga",
     ("sleep", "sleep quality", "insomnia", "fatigue", "non-restorative sleep")),
    ("Tratamento e medicamento",
     ("pregabalin", "duloxetine", "amitriptyline", "pharmacological treatment",
      "drug therapy", "cannabidiol")),
    ("Diagnóstico e critérios",
     ("diagnosis", "diagnostic criteria", "ACR criteria", "classification criteria",
      "FIQ", "Fibromyalgia Impact Questionnaire", "prevalence")),
    ("Trabalho e incapacidade",
     ("disability", "work ability", "absenteeism", "sick leave", "functional capacity")),
)

# ----------------------------------------------------------------------
# Motivacao no handebol
# ----------------------------------------------------------------------
# Aqui a MOTIVACAO e o construto e o HANDEBOL e a populacao -- e por isso
# o acervo se divide por tema, e nao por modalidade: a modalidade e uma
# so, e repetir-se-ia em todo segmento.
#
# Nao ha MeSH neste acervo, e isso foi CONFERIDO, nao suposto:
# `"Handball"[MeSH Terms]` devolve ZERO na PubMed -- o descritor nao
# existe. O que existe e `"Sports"[MeSH]`, e e justamente a armadilha que
# ja custou acervo no humor no esporte: somado com OR, ele alarga a
# populacao para esporte em geral e o recorte do handebol desaparece sem
# deixar erro. Entao aqui o handebol entra so por termo livre.
MOTIVACAO_TERMOS = (
    "motivation", "motivational climate", "self-determination",
    "self-determined motivation", "intrinsic motivation", "extrinsic motivation",
    "amotivation", "basic psychological needs", "autonomy support",
    "achievement goal", "achievement goals", "goal orientation",
    "task orientation", "ego orientation",
    # Os instrumentos, que e como a literatura de campo se cita. Sem eles,
    # o artigo que diz "we applied the BRSQ" no resumo e nao repete
    # "motivation" fica de fora -- e e o mais especifico do acervo.
    "Sport Motivation Scale", "Behavioural Regulation in Sport Questionnaire",
    "BRSQ", "TEOSQ", "PMCSQ",
)

# "team handball" existe porque nos Estados Unidos "handball" sozinho e
# OUTRO esporte -- o de parede, jogado com a mao contra um frontao. Sem o
# termo composto, parte da literatura americana do handebol de quadra
# fica de fora; com ele, ela entra.
#
# "balonmano" e "handebol" dao ZERO na PubMed -- medido -- e ficam assim
# mesmo: eles nao sao para a PubMed. A Scopus e a WoS indexam resumo em
# espanhol e portugues, e a Espanha e o Brasil sao dois dos paises que
# mais publicam handebol. Custam nada onde nao servem e trazem acervo
# onde servem.
HANDEBOL_TERMOS = (
    "handball", "team handball", "balonmano", "handebol",
)

# O construto EM PORTUGUES E ESPANHOL, para a BVS. Sem isto, uma revisao
# brasileira de handebol busca a America Latina em ingles e nao acha nada
# -- e a literatura que ela mais perde e a de casa. A LILACS indexa o
# resumo no idioma de origem, e a Espanha e o Brasil estao entre os que
# mais publicam handebol.
MOTIVACAO_REGIONAIS = (
    "motivação", "motivacao", "motivación", "motivacion",
    "clima motivacional", "motivação intrínseca", "motivacion intrinseca",
    "autodeterminação", "autodeterminacion", "metas de logro",
)

# Os temas em que o acervo se divide. Os numeros ao lado foram MEDIDOS na
# PubMed em 21/09/2026, e nao estimados -- mas foram medidos com uma
# forma REDUZIDA desta estrategia (o construto encurtado, para caber no
# limite de operadores da consulta), e por isso sao um piso, e nao a
# contagem final. Servem para uma coisa so, que e para o que foram
# feitos: dizer que nenhum segmento esta vazio. O numero de verdade
# aparece no acervo depois da primeira atualizacao, e e ele que vale.
#
# A base inteira -- motivacao E handebol -- deu 60. Os segmentos se
# sobrepoem, porque um trabalho sobre clima motivacional em categoria de
# base conta nos dois, e isso e proposital: segmento aqui e recorte de
# leitura, nao gaveta.
#
# Nenhum segmento vazio entra: segmento sem nada faz a tela parecer
# quebrada e faz quem olha desconfiar do acervo inteiro. A coesao, com
# tres, e o menor que passou -- e fica porque num esporte coletivo a
# pergunta se faz, mesmo que a literatura ainda nao a tenha respondido.
# Um numero pequeno a vista vale mais do que um segmento escondido.
TEMAS_MOTIVACAO_HANDEBOL: tuple[tuple[str, tuple[str, ...]], ...] = (
    # 45 registros
    ("Desempenho e competição",
     ("performance", "competition", "competitive level", "elite", "match",
      "training load", "season")),
    # 31 -- SEXO. Tres segmentos e nao um: "genero e handebol feminino"
    # juntava a modalidade feminina com o estudo que COMPARA os dois, e sao
    # perguntas diferentes -- uma e sobre quem joga, a outra e sobre a
    # diferenca entre quem joga.
    ("Handebol feminino",
     ("women", "female", "girls", "female athletes", "women's handball",
      "female players")),
    # 27
    ("Handebol masculino",
     ("men", "male", "boys", "male athletes", "men's handball", "male players")),
    # 4 -- o menor do acervo, e o mais especifico: so o que compara.
    ("Comparação entre os sexos",
     ("sex differences", "gender differences", "boys and girls", "men and women",
      "sex comparison")),
    # 29
    ("Treinador, liderança e relação",
     ("coach", "coaches", "coaching", "coaching style", "coach behaviour",
      "coach behavior", "leadership", "coach-athlete relationship",
      "autonomy-supportive", "controlling style")),
    # 25 -- CATEGORIA, primeiro degrau
    ("Formação e categorias de base",
     ("youth", "youth sport", "adolescent", "adolescents", "young players",
      "talent development", "talent identification", "relative age effect",
      "early specialization", "junior", "cadet", "under-16", "under-18")),
    # 12 -- CATEGORIA, o handebol que nao e de rendimento
    ("Escolar, universitário e recreativo",
     ("school", "physical education", "university", "college", "collegiate",
      "recreational", "amateur", "leisure")),
    # 8 -- CATEGORIA, o topo
    ("Adulto, profissional e seleção",
     ("adult", "senior", "professional", "first division", "national team",
      "international level")),
    # 20
    ("Clima motivacional e metas de realização",
     ("motivational climate", "achievement goal", "achievement goals",
      "goal orientation", "task orientation", "ego orientation",
      "mastery climate", "performance climate", "task involvement",
      "ego involvement")),
    # 19
    ("Autodeterminação e necessidades psicológicas",
     ("self-determination", "self-determined motivation", "intrinsic motivation",
      "extrinsic motivation", "amotivation", "basic psychological needs",
      "need satisfaction", "need thwarting", "autonomy", "competence",
      "relatedness", "autonomy support")),
    # 9
    ("Lesão e retorno ao jogo",
     ("injury", "injuries", "rehabilitation", "return to play", "return to sport",
      "fear of reinjury")),
    # 8
    ("Burnout, abandono e permanência",
     ("burnout", "dropout", "drop-out", "withdrawal", "attrition", "adherence",
      "retention", "engagement", "athlete burnout")),
    # 7
    ("Autoeficácia, ansiedade e confiança",
     ("self-efficacy", "self-confidence", "competitive anxiety", "anxiety",
      "mental toughness", "resilience", "self-esteem")),
    # 6 -- escola e universidade sairam daqui e ganharam segmento proprio
    # de CATEGORIA; o que fica e o que muda a modalidade em si.
    ("Praia e handebol adaptado",
     ("beach handball", "wheelchair", "disability", "para sport",
      "adapted handball", "goalball")),
    # 3
    ("Coesão e eficácia coletiva",
     ("cohesion", "team cohesion", "collective efficacy", "group dynamics",
      "teamwork", "team climate")),
)

# ----------------------------------------------------------------------
# Teoria da autodeterminacao no handebol
# ----------------------------------------------------------------------
# Este acervo e um RECORTE do de motivacao no handebol, e a relacao entre
# os dois e a mesma que ha entre humor no esporte e humor nos esportes
# esteticos: o de cima responde "o que move quem joga", e este responde
# uma pergunta de teoria -- o que a autodeterminacao, especificamente,
# ja disse sobre o handebol.
#
# A ARMADILHA AQUI E O CONSTRUTO, e ela e a razao de este bloco existir.
# Se "motivation" entrasse na lista, o recorte devolveria praticamente o
# acervo inteiro com outro nome: medido na PubMed, a motivacao em geral
# da 60 registros e a autodeterminacao da 22. Os 38 de diferenca sao
# clima motivacional, metas de realizacao, coesao -- literatura
# legitima, de OUTRA teoria, e e justamente o que este acervo nao quer.
#
# Entao o vocabulario e so o da teoria: os nomes dela, as tres
# necessidades, as regulacoes do continuum e os instrumentos que a medem.
AUTODETERMINACAO_TERMOS = (
    "self-determination theory", "self-determination", "self-determined motivation",
    "basic psychological needs", "psychological need satisfaction",
    "need satisfaction", "need frustration", "need thwarting",
    "autonomy support", "autonomy-supportive", "controlling style",
    "controlling coach behaviour", "controlling coach behavior",
    "intrinsic motivation", "extrinsic motivation", "amotivation",
    "autonomous motivation", "controlled motivation",
    "identified regulation", "introjected regulation", "external regulation",
    "integrated regulation", "behavioural regulation", "behavioral regulation",
    # Os instrumentos: o artigo que diz "we applied the BRSQ" e nao repete
    # o nome da teoria e o mais especifico do acervo, e era o que ficava
    # de fora.
    "Behavioural Regulation in Sport Questionnaire", "BRSQ",
    "Basic Psychological Needs in Exercise Scale", "BPNES",
    "Basic Needs Satisfaction in Sport Scale", "BNSSS",
    "Sport Motivation Scale", "Perceived Autonomy Support",
)

# EM PORTUGUES E ESPANHOL, para a BVS -- e so para ela.
AUTODETERMINACAO_REGIONAIS = (
    "autodeterminação", "autodeterminacao", "autodeterminación", "autodeterminacion",
    "teoria da autodeterminação", "teoría de la autodeterminación",
    "necessidades psicológicas básicas", "necesidades psicológicas básicas",
    "motivação intrínseca", "motivación intrínseca",
    "apoio à autonomia", "apoyo a la autonomía",
)

# Os temas, com o que cada um tem na PubMed -- medido em 21/09/2026, com
# uma forma reduzida da estrategia (o limite de operadores da consulta nao
# deixou rodar a inteira). Sao um piso, e servem para uma coisa so: dizer
# que nenhum segmento esta vazio. A base inteira deu 22.
#
# Num acervo deste tamanho os segmentos se sobrepoem muito -- um estudo de
# suporte a autonomia em categoria de base conta em tres deles. Isso e
# proposital: segmento aqui e recorte de leitura, e nao gaveta.
TEMAS_AUTODETERMINACAO: tuple[tuple[str, tuple[str, ...]], ...] = (
    # 15 registros
    ("Formação e categorias de base",
     ("youth", "youth sport", "adolescent", "adolescents", "young players",
      "children", "school", "physical education")),
    # 11 -- SEXO
    ("Handebol feminino",
     ("women", "female", "girls", "female athletes", "women's handball")),
    # 5
    ("Handebol masculino",
     ("men", "male", "boys", "male athletes", "men's handball")),
    # 3 -- CATEGORIA, o topo. Pequeno, e nao vazio: e onde estao os
    # estudos com selecao e primeira divisao.
    ("Adulto, profissional e seleção",
     ("adult", "senior", "professional", "national team", "first division",
      "international level")),
    # 15
    ("Desempenho, treino e nível competitivo",
     ("performance", "effort", "training", "competitive level", "elite",
      "professional", "season")),
    # 11
    ("Treinador: suporte à autonomia e estilo controlador",
     ("coach", "coaches", "coaching", "autonomy-supportive", "controlling",
      "coach-athlete relationship", "interpersonal style")),
    # 10
    ("Necessidades psicológicas básicas",
     ("need satisfaction", "need frustration", "need thwarting", "autonomy",
      "competence", "relatedness", "basic needs")),
    # 10
    ("Instrumentos e validação",
     ("validation", "psychometric", "factor structure", "questionnaire", "scale",
      "invariance", "reliability")),
    # 8
    ("Bem-estar, vitalidade e burnout",
     ("well-being", "wellbeing", "ill-being", "vitality", "burnout", "enjoyment",
      "satisfaction with life", "positive affect")),
    # 8
    ("Persistência, abandono e intenção de continuar",
     ("dropout", "drop-out", "intention to continue", "persistence", "adherence",
      "commitment", "engagement", "attrition")),
    # 5
    ("Regulações motivacionais: o continuum",
     ("identified regulation", "introjected regulation", "external regulation",
      "integrated regulation", "autonomous motivation", "controlled motivation",
      "relative autonomy index")),
)

BIBLIOTECAS: tuple[dict[str, Any], ...] = (
    {
        "code": "humor_esporte",
        "title": "Estado de humor no esporte",
        "linha": "psicologia_do_esporte",
        "eixo": "esporte",
        "descricao":
            "O que se sabe sobre o humor de quem compete: como ele é medido, o que o "
            "move ao longo de uma temporada e o que ele antecipa do desempenho e do "
            "adoecimento. O acervo se divide por modalidade, porque a mesma medida "
            "responde de maneira diferente num esporte coletivo e num de resistência.",
        "construto": HUMOR_TERMOS,
        "populacao": ATLETA_TERMOS,
        "mesh": MESH_DE_ATLETA,
        "segmentos": ESPORTES,
    },
    {
        "code": "humor_estetico",
        "title": "Estado de humor nos esportes estéticos",
        "linha": "psicologia_do_esporte",
        "eixo": "tema",
        "descricao":
            "Humor em quem compete em modalidade julgada pela aparência do movimento "
            "— ginástica artística e rítmica, nado artístico, patinação, saltos "
            "ornamentais, ballet e dança de competição. É o acervo de base para uma "
            "revisão sistemática, e por isso se divide por TEMA e não por modalidade: "
            "a modalidade é a população, e repetir-se-ia em todo segmento. Nestas "
            "modalidades a nota depende da linha corporal, e a literatura de humor "
            "gira em torno de imagem corporal, peso e alimentação — que é justamente "
            "o que não aparece no acervo de humor no esporte em geral.",
        # O MESMO vocabulario de humor do outro acervo, de proposito. Sao
        # os instrumentos que este laboratorio usa (POMS e BRUMS), e um
        # segundo vocabulario para o mesmo construto seria dois lugares
        # para consertar e um para esquecer.
        "construto": HUMOR_TERMOS,
        "populacao": ESTETICOS_TERMOS,
        # O MeSH das MODALIDADES, e nunca `athletes[MeSH]`: este acervo e
        # de quem compete em esporte julgado, e nao de atleta em geral.
        # Os tres foram conferidos na PubMed e existem. `Diving[MeSH]`
        # fica de fora de proposito: na PubMed, Diving e mergulho
        # subaquatico -- descompressao, apneia --, e nao salto ornamental.
        # E a mesma armadilha do termo livre "diving", pela porta do
        # vocabulario controlado. `Swimming[MeSH]` tambem fica fora:
        # alargaria para natacao de piscina inteira.
        "mesh": ('"Gymnastics"[MeSH Terms]', '"Dancing"[MeSH Terms]',
                 '"Skating"[MeSH Terms]'),
        "segmentos": TEMAS_ESTETICOS,
    },
    {
        "code": "fibromialgia",
        "title": "Fibromialgia — tudo que existe",
        "linha": "exercicio_fibromialgia",
        "eixo": "tema",
        "descricao":
            "O acervo inteiro da condição, e não um cruzamento: aqui a fibromialgia "
            "é a população, e o recorte vem dos temas. É o acervo de base para "
            "revisão, e por isso a estratégia é montada também para as bases que o "
            "sistema não alcança sozinho — Embase, PsycINFO, CINAHL, Cochrane e BVS. "
            "Essas cinco ficam guardadas para quem tem o acesso colar na base: uma "
            "revisão de fibromialgia sem Embase e sem PsycINFO não está completa, e "
            "o sistema não chegar lá não muda isso — muda de quem é o trabalho.",
        "construto": FIBROMIALGIA_TERMOS,
        # A condicao e a populacao: nao ha segundo bloco para cruzar, e
        # inventar um ("humanos", "adultos") so cortaria acervo sem
        # responder nada.
        "populacao": (),
        "regionais": FIBROMIALGIA_REGIONAIS,
        "mesh": ('"Fibromyalgia"[MeSH Terms]',),
        "segmentos": TEMAS_FIBROMIALGIA,
        "manuais": BASES_MANUAIS,
    },
    {
        "code": "motivacao_handebol",
        "title": "Motivação no handebol",
        "linha": "psicologia_do_esporte",
        "eixo": "tema",
        "descricao":
            "O que move quem joga handebol: por que entra, por que fica e por que "
            "para. A motivação é o construto e o handebol é a população, e por isso "
            "o acervo se divide por TEMA — a modalidade é uma só e se repetiria em "
            "todo segmento. Eram cerca de 60 registros na PubMed quando o acervo "
            "foi montado — pequeno e inteiro de ler, o que o torna bom para uma "
            "revisão de escopo: dá para dizer o que existe sem depender de "
            "amostragem. Scopus e Web of Science entram com a mesma estratégia, "
            "escrita na sintaxe de cada uma — e mais seis bases que o sistema "
            "não alcança sozinho ficam com a estratégia pronta para colar, "
            "SPORTDiscus inclusive, que é onde está a psicologia do esporte "
            "que a PubMed não indexa.",
        "construto": MOTIVACAO_TERMOS,
        "populacao": HANDEBOL_TERMOS,
        "regionais": MOTIVACAO_REGIONAIS,
        # Sem MeSH de proposito: `"Handball"[MeSH Terms]` devolve zero na
        # PubMed -- o descritor nao existe --, e `"Sports"[MeSH]` alargaria
        # a populacao para esporte em geral.
        "mesh": (),
        "segmentos": TEMAS_MOTIVACAO_HANDEBOL,
        # As seis que o sistema nao alcanca sozinho. A estrategia delas e
        # montada e guardada do mesmo jeito, para quem tem o acesso colar
        # na base -- e porque uma revisao sistematica publica a estrategia
        # de CADA base, com a data e o numero de registros.
        #
        # A SPORTDiscus e a que mais importa aqui: e nela que estao as
        # revistas de psicologia do esporte que a PubMed nao indexa.
        "manuais": BASES_MANUAIS,
    },
    {
        "code": "autodeterminacao_handebol",
        "title": "Teoria da autodeterminação no handebol",
        "linha": "psicologia_do_esporte",
        "eixo": "tema",
        "descricao":
            "O recorte teórico: o que a teoria da autodeterminação já disse sobre "
            "o handebol — necessidades psicológicas básicas, as regulações do "
            "continuum, suporte à autonomia e estilo controlador do treinador. É "
            "um recorte do acervo de motivação no handebol, e não um acervo "
            "paralelo: lá são 60 registros na PubMed, aqui 22. Os 38 de diferença "
            "são clima motivacional, metas de realização e coesão — literatura "
            "legítima, de outra teoria, e é justamente o que este acervo deixa de "
            "fora de propósito. Por isso o vocabulário não tem a palavra "
            "“motivation” sozinha: com ela, o recorte devolveria o acervo inteiro "
            "com outro nome.",
        "construto": AUTODETERMINACAO_TERMOS,
        "populacao": HANDEBOL_TERMOS,
        "regionais": AUTODETERMINACAO_REGIONAIS,
        # Sem MeSH: `"Handball"[MeSH Terms]` devolve zero na PubMed -- o
        # descritor nao existe -- e `Sports[MeSH]` alargaria a populacao
        # para esporte em geral. Medido junto com o acervo maior.
        "mesh": (),
        "segmentos": TEMAS_AUTODETERMINACAO,
        "manuais": BASES_MANUAIS,
    },
)


def query_de(decl: dict[str, Any], segmento_termos: tuple[str, ...] | None = None,
             base: str = PUBMED) -> str:
    """A busca inteira, montada do vocabulario, na sintaxe da base.

    Cada bloco so entra se tiver termo. Um acervo pode nao ter populacao
    separada -- na fibromialgia a condicao E a populacao --, e o bloco
    vazio gerava `(...) AND ()`, que a base recusa ou, pior, aceita e
    responde outra coisa. Bloco sem termo nao virava zero: virava uma
    busca invalida com cara de busca.
    """
    construto = list(decl["construto"])
    # Na BVS entram tambem os termos em portugues e espanhol. Ela indexa o
    # resumo no idioma de origem, e buscar a America Latina em ingles la
    # e nao achar a literatura de casa.
    if base == LILACS and decl.get("regionais"):
        construto += list(decl["regionais"])

    partes = [f"({frase(tuple(construto), base)})"]

    populacao = frase(decl.get("populacao") or (), base)
    if base == PUBMED and decl.get("mesh"):
        # O MeSH entra no bloco da populacao quando ha populacao, e faz o
        # seu proprio bloco quando nao ha -- na fibromialgia ele e o termo
        # controlado da CONDICAO, e somar com OR ao construto seria
        # perfeito, mas fora de um bloco proprio ele ficaria pendurado no
        # AND anterior e alargaria a busca inteira.
        mesh = " OR ".join(decl["mesh"])
        populacao = f"{mesh} OR {populacao}" if populacao else mesh
        if not decl.get("populacao"):
            # sem populacao, o MeSH da condicao vai junto do construto
            partes = [f"({frase(tuple(construto), base)} OR {mesh})"]
            populacao = ""
    if populacao:
        partes.append(f"({populacao})")
    if segmento_termos:
        partes.append(f"({frase(segmento_termos, base)})")
    return " AND ".join(partes)


def instalar(db: Database) -> dict[str, Any]:
    """Poe os acervos declarados no banco, com as buscas de cada segmento.

    Rodar de novo nao desfaz o que foi mexido nem apaga item nenhum: as
    buscas sao atualizadas pela estrategia escrita aqui, e o acervo ja
    recolhido continua onde esta.
    """
    novas, ja_havia = [], []
    for decl in BIBLIOTECAS:
        linha_id = db.scalar("SELECT id FROM research_lines WHERE code = ?",
                             (decl["linha"],))
        achada = db.scalar("SELECT id FROM biblioteca WHERE code = ?", (decl["code"],))
        if achada:
            db.execute(
                "UPDATE biblioteca SET title = ?, descricao = ?, eixo = ?,"
                "       research_line_id = COALESCE(research_line_id, ?) WHERE id = ?",
                (decl["title"], decl["descricao"], decl["eixo"], linha_id, achada))
            ja_havia.append(decl["title"])
            bid = achada
        else:
            cursor = db.execute(
                "INSERT INTO biblioteca (code, title, descricao, eixo, research_line_id)"
                " VALUES (?, ?, ?, ?, ?)",
                (decl["code"], decl["title"], decl["descricao"], decl["eixo"], linha_id))
            bid = cursor.lastrowid
            novas.append(decl["title"])

        # Uma busca por base e por segmento. A geral, sem segmento, e a
        # que define o tamanho do acervo naquela base.
        # As tres com API, mais as que o acervo declarar como manuais. A
        # estrategia manual e guardada igual: e ela que a revisao publica,
        # e e ela que quem tem o acesso cola na base.
        for base in tuple(BASES) + tuple(decl.get("manuais") or ()):
            _guardar_busca(db, bid, base, None, query_de(decl, base=base))
            for nome, termos in decl["segmentos"]:
                _guardar_busca(db, bid, base, nome, query_de(decl, termos, base))
    db.conn.commit()
    return {"novas": novas, "ja_havia": ja_havia, "total": len(BIBLIOTECAS)}


def _guardar_busca(db: Database, biblioteca_id: int, base: str,
                   segmento: str | None, query: str) -> None:
    """Guarda a busca, uma por segmento -- e a geral, que nao tem segmento.

    Procura antes de gravar, em vez de confiar no `UNIQUE` da tabela, por
    causa de uma regra do SQLite que morde calada: numa restricao UNIQUE,
    dois NULL sao considerados DIFERENTES entre si. A busca geral e a
    unica com `segmento IS NULL`, entao `ON CONFLICT` nunca disparava para
    ela -- e cada instalacao acrescentava mais uma copia da busca geral, em
    silencio, sem erro nenhum.
    """
    achada = db.scalar(
        "SELECT id FROM biblioteca_busca"
        " WHERE biblioteca_id = ? AND base = ?"
        "   AND ((segmento IS NULL AND ? IS NULL) OR segmento = ?)",
        (biblioteca_id, base, segmento, segmento))
    if achada:
        db.execute("UPDATE biblioteca_busca SET query = ? WHERE id = ?", (query, achada))
        return
    db.execute(
        "INSERT INTO biblioteca_busca (biblioteca_id, base, segmento, query)"
        " VALUES (?, ?, ?, ?)", (biblioteca_id, base, segmento, query))


# ----------------------------------------------------------------------
# As bases proprietarias, como FONTE do acervo
# ----------------------------------------------------------------------
# A Scopus e a WoS ja eram consultadas para contar citacoes, uma por DOI.
# Aqui elas entram de outro jeito: respondendo a uma BUSCA e devolvendo
# artigos que o acervo ainda nao tem. E o que faz a biblioteca cobrir o que
# a PubMed nao indexa -- e a psicologia do esporte publica bastante fora
# dela, em revistas de ciencias do esporte que so a Scopus cataloga.
#
# As duas pedem chave. Sem chave a busca nao acontece e a tela diz isso; o
# que ela nao faz e devolver zero calada, que seria indistinguivel de "a
# base nao conhece este assunto".
def buscar_scopus(query: str, limite: int = 200) -> list[dict[str, Any]]:
    """Registros da Scopus para uma busca, paginando de 25 em 25."""
    from .ingest_citations import SCOPUS_SEARCH, _pedir

    chave = getattr(config, "SCOPUS_API_KEY", "")
    if not chave:
        raise SemChave("SCOPUS_API_KEY não está configurada")
    headers = {"X-ELS-APIKey": chave, "Accept": "application/json"}
    if getattr(config, "SCOPUS_INST_TOKEN", ""):
        headers["X-ELS-Insttoken"] = config.SCOPUS_INST_TOKEN

    achados: list[dict[str, Any]] = []
    inicio, passo = 0, 25
    while inicio < limite:
        dados = _pedir(SCOPUS_SEARCH, {
            "query": query, "start": inicio, "count": min(passo, limite - inicio),
            "field": ("dc:title,dc:creator,prism:publicationName,prism:coverDate,"
                      "prism:doi,citedby-count,eid,pubmed-id,openaccess"),
        }, headers, "Scopus")
        entradas = dados.get("search-results", {}).get("entry") or []
        # A Scopus devolve UMA entrada com a chave "error" quando a busca
        # nao acha nada. Tratar isso como artigo gravaria um registro de
        # titulo vazio no acervo.
        entradas = [e for e in entradas if not e.get("error")]
        if not entradas:
            break
        achados.extend(_do_scopus(e) for e in entradas)
        if len(entradas) < passo:
            break
        inicio += passo
        time.sleep(THROTTLE)
    return achados


def _do_scopus(entrada: dict[str, Any]) -> dict[str, Any]:
    data = str(entrada.get("prism:coverDate") or "")
    return {
        "title": clean_text(entrada.get("dc:title")),
        "authors": clean_text(entrada.get("dc:creator")),
        "journal": clean_text(entrada.get("prism:publicationName")),
        "year": int(data[:4]) if data[:4].isdigit() else None,
        "doi": norm_doi(entrada.get("prism:doi")),
        "pmid": clean_text(entrada.get("pubmed-id")),
        "base": SCOPUS,
        # A Scopus nao devolve afiliacao neste conjunto de campos, e pedir
        # o registro completo de cada artigo gastaria uma chamada por
        # artigo. O pais entra depois, pelo DOI, quando a PubMed ou a
        # OpenAlex conhecerem o mesmo artigo.
        "afiliacoes": None,
    }


def buscar_wos(query: str, limite: int = 200) -> list[dict[str, Any]]:
    """Registros da Web of Science Starter API para uma busca."""
    from .ingest_citations import WOS_SEARCH, _pedir

    chave = getattr(config, "WOS_API_KEY", "")
    if not chave:
        raise SemChave("WOS_API_KEY não está configurada")
    headers = {"X-ApiKey": chave, "Accept": "application/json"}

    achados: list[dict[str, Any]] = []
    pagina, por_pagina = 1, 50
    while len(achados) < limite:
        dados = _pedir(WOS_SEARCH, {
            "q": query, "db": "WOS", "limit": min(por_pagina, limite - len(achados)),
            "page": pagina,
        }, headers, "WoS")
        hits = dados.get("hits") or []
        if not hits:
            break
        achados.extend(_do_wos(h) for h in hits)
        if len(hits) < por_pagina:
            break
        pagina += 1
        time.sleep(THROTTLE)
    return achados


def _do_wos(hit: dict[str, Any]) -> dict[str, Any]:
    fonte = hit.get("source") or {}
    ids = hit.get("identifiers") or {}
    nomes = [clean_text(a.get("displayName"))
             for a in (hit.get("names") or {}).get("authors") or []]
    return {
        "title": clean_text(hit.get("title")),
        "authors": "; ".join(n for n in nomes if n),
        "journal": clean_text(fonte.get("sourceTitle")),
        "year": int(fonte["publishYear"]) if str(fonte.get("publishYear", "")).isdigit() else None,
        "doi": norm_doi(ids.get("doi")),
        "pmid": clean_text(ids.get("pmid")),
        "base": WOS,
        "afiliacoes": None,
    }


class SemChave(RuntimeError):
    """A base pede chave e nao ha chave.

    Separada do erro de rede porque o recado e outro: nao adianta tentar de
    novo, e a tela precisa dizer QUAL variavel falta em vez de mostrar um
    zero que parece resposta.
    """


class SemApi(SemChave):
    """A base existe, a estrategia esta pronta, e nao ha por onde chamar.

    Irma de `SemChave` de proposito: o caminho e o mesmo -- avisar UMA vez
    por base, gravar o recado ao lado da busca, e nao derrubar as outras.
    O que muda e o remedio, e por isso a mensagem diz o que fazer em vez
    de dizer que faltou algo.

    O que ela NAO pode ser e um zero. Uma busca da Embase que devolvesse
    lista vazia seria indistinguivel de "a Embase nao tem nada sobre
    fibromialgia", e alguem escreveria isso numa revisao.
    """


THROTTLE = 0.4


# ----------------------------------------------------------------------
# A atualizacao
# ----------------------------------------------------------------------
def quantas_buscas(db: Database, code: str,
                   bases: tuple[str, ...] | None = None) -> int:
    """Quantas buscas o acervo tem guardadas -- o tamanho da tarefa.

    Serve para a barra de progresso saber o total ANTES de comecar. Sem
    isto, "atualizando..." e uma mensagem que nao diz se falta um minuto
    ou quinze, e quem espera fecha a janela no meio.
    """
    dados = db.dicts("SELECT id FROM biblioteca WHERE code = ?", (code,))
    if not dados:
        raise ValueError(f"biblioteca “{code}” não existe")
    if bases:
        marcas = ",".join("?" * len(bases))
        return int(db.scalar(
            "SELECT COUNT(*) FROM biblioteca_busca WHERE biblioteca_id = ?"
            f"   AND base IN ({marcas})", (dados[0]["id"], *bases)) or 0)
    return int(db.scalar(
        "SELECT COUNT(*) FROM biblioteca_busca WHERE biblioteca_id = ?",
        (dados[0]["id"],)) or 0)


def atualizar(db: Database, code: str, limite: int = 400,
              bases: tuple[str, ...] | None = None,
              verbose: bool = False,
              progresso: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    """Roda as buscas do acervo e recolhe o que ainda nao estava aqui.

    Uma busca falhar nao derruba as outras: a rede cai no meio de quatorze
    modalidades, e perder as treze que ja tinham voltado por causa da
    decima quarta seria trocar um acervo por um erro. O erro fica gravado
    ao lado da busca que falhou, e a tela o mostra.

    `progresso` e chamado a cada busca terminada, com o que acabou de
    acontecer. E opcional de proposito: pelo terminal o `verbose` ja
    imprime, e quem chama de um script nao quer nem um nem outro.
    """
    from .revisao import chaves_de_uniao

    dados = db.dicts("SELECT id, title FROM biblioteca WHERE code = ?", (code,))
    if not dados:
        raise ValueError(f"biblioteca “{code}” não existe")
    bid, titulo = dados[0]["id"], dados[0]["title"]

    buscas = db.dicts(
        "SELECT id, base, segmento, query FROM biblioteca_busca"
        " WHERE biblioteca_id = ? ORDER BY base, segmento IS NULL DESC, segmento",
        (bid,))
    if bases:
        buscas = [b for b in buscas if b["base"] in bases]

    hoje = date.today().isoformat()
    # Antes de trazer mais, junta o que ja esta repetido. Acervo com
    # duplicata recebendo artigo novo so acumula duplicata.
    limpeza = limpar_duplicatas(db, code)
    # E le de novo o desenho de quem ja estava aqui: o vocabulario pode ter
    # ganhado termos desde a ultima vez, e nao ha por que o acervo antigo
    # ficar com a leitura velha enquanto o novo entra com a nova.
    reclassificar(db, code)
    resumo = {"biblioteca": titulo, "buscas": 0, "achados": 0, "novos": 0,
              "erros": 0, "sem_chave": [], "por_base": {}, "segmentos": [],
              "repetidos_juntados": limpeza["juntados"]}

    # Uma chave que falta e uma noticia so, e nao quinze. Antes de rodar as
    # quinze buscas de uma base, pergunta-se pela chave dela: sem isso, a
    # tela mostraria "SCOPUS_API_KEY nao configurada" quinze vezes e a
    # pessoa leria quinze erros onde ha um recado.
    desligadas: dict[str, str] = {}
    feitas = 0
    total = len(buscas)

    def terminou(base: str, segmento: str | None, situacao: str,
                 achados: int = 0, novos: int = 0, recado: str = "") -> None:
        """Fecha a busca: grava o que ela trouxe, e so entao avisa.

        O COMMIT E POR BUSCA, e nao no fim do acervo -- e essa e a
        diferenca entre o sistema continuar utilizavel ou nao enquanto a
        atualizacao roda.

        O sqlite3 do Python abre uma transacao na primeira escrita e a
        segura ate o commit. Com o commit so no fim, a trava de escrita
        ficava presa DURANTE AS CHAMADAS DE REDE -- trinta e seis buscas,
        cada uma com ida a base e 0,4 s de pausa, sao minutos de banco
        travado. Nesse intervalo, qualquer outro programa que tentasse
        gravar morria com "database is locked" depois dos trinta segundos
        de espera. Foi o que aconteceu com o curador e com a propria linha
        de comando da biblioteca, na maquina do laboratorio.

        Medido: uma escrita sem commit numa conexao faz a outra estourar;
        com o commit, a segunda grava em 0,00 s. Ler continua funcionando
        nos dois casos, porque o banco esta em WAL -- e por isso a TELA
        continuava normal enquanto o cmd morria, o que fazia o defeito
        parecer coisa do comando.

        Commitar por busca tambem e melhor quando a rede cai no meio: o
        que ja foi recolhido fica, em vez de voltar tudo.
        """
        db.conn.commit()
        if progresso is None:
            return
        progresso({"acervo": code, "titulo": titulo, "base": base,
                   "rotulo": ROTULO_BASE.get(base, base),
                   "segmento": segmento, "situacao": situacao,
                   "achados": achados, "novos": novos, "recado": recado,
                   "feitas": feitas, "total": total})

    for busca in buscas:
        base = busca["base"]
        if base in desligadas:
            # Nao vai a rede, mas conta: a barra precisa chegar ao fim.
            feitas += 1
            terminou(base, busca["segmento"], "pulada",
                   recado=desligadas[base])
            continue
        resumo["buscas"] += 1
        try:
            registros = _colher(base, busca["query"], limite)
        except SemChave as erro:
            desligadas[base] = str(erro)
            resumo["sem_chave"].append({"base": base, "rotulo": ROTULO_BASE.get(base, base),
                                        "porque": str(erro)})
            db.execute("UPDATE biblioteca_busca SET erro = ? WHERE biblioteca_id = ?"
                       "   AND base = ?", (str(erro)[:300], bid, base))
            if verbose:
                print(f"  . {ROTULO_BASE.get(base, base)}: {erro}")
            feitas += 1
            terminou(base, busca["segmento"], "sem_chave", recado=str(erro))
            continue
        except Exception as erro:  # noqa: BLE001 -- uma busca nao derruba as outras
            db.execute("UPDATE biblioteca_busca SET rodada_em = ?, erro = ? WHERE id = ?",
                       (hoje, str(erro)[:300], busca["id"]))
            resumo["erros"] += 1
            if verbose:
                print(f"  ! {base}/{busca['segmento'] or 'geral'}: {erro}")
            feitas += 1
            terminou(base, busca["segmento"], "erro", recado=str(erro))
            continue

        novos = 0
        for registro in registros:
            if _gravar(db, bid, busca["segmento"], registro, chaves_de_uniao):
                novos += 1
        db.execute(
            "UPDATE biblioteca_busca SET rodada_em = ?, achados = ?, novos = ?,"
            "       erro = NULL WHERE id = ?",
            (hoje, len(registros), novos, busca["id"]))
        resumo["achados"] += len(registros)
        resumo["novos"] += novos
        conta = resumo["por_base"].setdefault(
            base, {"rotulo": ROTULO_BASE.get(base, base), "achados": 0, "novos": 0})
        conta["achados"] += len(registros)
        conta["novos"] += novos
        if busca["segmento"]:
            resumo["segmentos"].append({"base": base, "segmento": busca["segmento"],
                                        "achados": len(registros), "novos": novos})
        if verbose:
            print(f"  {base}/{busca['segmento'] or 'geral'}: {len(registros)} achado(s),"
                  f" {novos} novo(s)")
        feitas += 1
        terminou(base, busca["segmento"], "ok", achados=len(registros), novos=novos)

    db.execute("UPDATE biblioteca SET atualizada_em = ? WHERE id = ?", (hoje, bid))
    db.conn.commit()
    db.log_ingest("biblioteca", target=code, rows_read=resumo["achados"],
                  rows_written=resumo["novos"],
                  status="ok" if not (resumo["erros"] or desligadas) else "parcial",
                  message=f"{resumo['novos']} novo(s) em {resumo['buscas']} busca(s)")
    return resumo


def estrategias(db: Database, code: str,
                so_manuais: bool = False) -> list[dict[str, Any]]:
    """As buscas guardadas do acervo, para a tela mostrar e copiar.

    E o que uma revisao sistematica publica: a estrategia de cada base,
    com a data e o numero de registros. Sai daqui e nao da memoria de
    ninguem -- montada a mao na hora, ela sai diferente de uma vez para a
    outra e ninguem refaz um ano depois.
    """
    linhas = db.dicts(
        "SELECT bb.id, bb.base, bb.segmento, bb.query, bb.rodada_em,"
        "       bb.achados, bb.novos, bb.erro"
        "  FROM biblioteca_busca bb JOIN biblioteca b ON b.id = bb.biblioteca_id"
        " WHERE b.code = ? ORDER BY bb.base, bb.segmento IS NULL DESC, bb.segmento",
        (code,))
    if so_manuais:
        linhas = [x for x in linhas if x["base"] in BASES_MANUAIS]
    for x in linhas:
        x["rotulo"] = ROTULO_BASE.get(x["base"], x["base"])
        x["manual"] = x["base"] in BASES_MANUAIS
        x["porque_manual"] = PORQUE_MANUAL.get(x["base"])
    return linhas


def importar_colado(db: Database, code: str, base: str, texto: str,
                    segmento: str | None = None, nome: str = "",
                    formato: str | None = None) -> dict[str, Any]:
    """O que a pessoa exportou da base, colado de volta no acervo.

    E o outro lado das cinco bases sem API: a estrategia sai daqui, a
    pessoa roda na base com o acesso dela, exporta e cola o arquivo aqui.
    Sem isto, a estrategia guardada seria so um texto bonito -- o
    resultado voltaria numa planilha na maquina de alguem, e o acervo
    ficaria em zero para sempre.

    Le RIS, nbib, BibTeX e CSV, que e o que essas cinco exportam, e o
    formato e detectado pelo conteudo: pedir a pessoa para saber se a
    Embase entregou RIS ou BibTeX e transferir para ela um problema que o
    arquivo ja responde.

    Reimportar o mesmo arquivo NAO duplica: `_gravar` procura pelas duas
    chaves do registro. E isso importa aqui mais do que na coleta
    automatica, porque colar duas vezes e o erro natural de quem nao tem
    certeza se o primeiro clique pegou.

    A contabilidade da busca e atualizada -- `achados`, `novos`,
    `rodada_em` --, pelo mesmo motivo de existir: o numero por base, com a
    data, e o que vai no PRISMA.
    """
    from .revisao import chaves_de_uniao

    bid = db.scalar("SELECT id FROM biblioteca WHERE code = ?", (code,))
    if not bid:
        raise ValueError(f"biblioteca “{code}” não existe")
    if not (texto or "").strip():
        raise ValueError("não veio nada para importar")

    registros = referencias.ler(texto, nome, formato)
    if not registros:
        # Nem tudo que parece arquivo de base e arquivo de base: a pessoa
        # pode colar a TELA de resultados em vez do arquivo exportado, e
        # dizer "0 novos" a ela seria dizer que a busca nao achou nada.
        raise ValueError(
            "não reconheci nenhuma referência nesse texto. Exporte da base em "
            "RIS, BibTeX, nbib ou CSV e cole o conteúdo do arquivo — a tela de "
            "resultados da base, copiada, não traz os campos.")

    novos = 0
    for registro in registros:
        registro.setdefault("base", base)
        if _gravar(db, bid, segmento, registro, chaves_de_uniao):
            novos += 1

    hoje = date.today().isoformat()
    # A busca a que este arquivo pertence -- a geral, ou a do segmento.
    # `IS` e nao `=`: segmento nulo nao casa com `= NULL` em SQL, e a
    # busca geral e justamente a que tem segmento nulo.
    db.execute(
        "UPDATE biblioteca_busca SET rodada_em = ?, achados = ?, novos = ?,"
        "       erro = NULL"
        " WHERE biblioteca_id = ? AND base = ? AND segmento IS ?",
        (hoje, len(registros), novos, bid, base, segmento))
    db.execute("UPDATE biblioteca SET atualizada_em = ? WHERE id = ?", (hoje, bid))
    db.conn.commit()
    return {"base": base, "rotulo": ROTULO_BASE.get(base, base),
            "segmento": segmento, "achados": len(registros), "novos": novos,
            "repetidos": len(registros) - novos, "quando": hoje}


def limpar_duplicatas(db: Database, code: str) -> dict[str, Any]:
    """Junta itens que sao o mesmo trabalho e entraram duas vezes.

    Existe por causa de um defeito que ja gravou dado: a primeira versao
    comparava so a chave principal, e um artigo que a PubMed trouxe com DOI
    e a Scopus trouxe sem virava dois. O conserto na gravacao nao desfaz o
    que ja esta no banco, e refazer o acervo inteiro nao e resposta -- sao
    quarenta e cinco buscas e alguns minutos.

    Junta pelo titulo normalizado com o ano, que e a chave que os dois lados
    tem em comum quando o DOI falta num deles. O que sobrevive e o registro
    MAIS COMPLETO -- o que tem DOI, e entre os que tem, o que tem resumo --,
    e os segmentos dos dois se somam: um item achado em "Natação" por uma
    base e em "Handebol" por outra pertence aos dois.
    """
    from .revisao import chaves_de_uniao

    bid = db.scalar("SELECT id FROM biblioteca WHERE code = ?", (code,))
    if not bid:
        raise ValueError(f"biblioteca “{code}” não existe")

    grupos: dict[str, list[dict[str, Any]]] = {}
    for item in db.dicts(
            "SELECT id, chave, chave_titulo, segmento, title, year, doi, abstract"
            "  FROM biblioteca_item WHERE biblioteca_id = ? ORDER BY id", (bid,)):
        alvo_ = item["chave_titulo"]
        if not alvo_:
            # Item gravado pela versao antiga: a chave de titulo nao existe
            # na linha, e sai do proprio registro.
            chaves = chaves_de_uniao({"title": item["title"], "year": item["year"],
                                      "doi": item["doi"]})
            alvo_ = next((c for c in chaves if c.startswith("tit:")), None)
            if alvo_:
                db.execute("UPDATE biblioteca_item SET chave_titulo = ? WHERE id = ?",
                           (alvo_, item["id"]))
        if alvo_:
            grupos.setdefault(alvo_, []).append(item)

    juntados, sumiram = 0, []
    for chave_titulo, itens in grupos.items():
        if len(itens) < 2:
            continue
        # O mais completo fica: com DOI primeiro, depois com resumo, e por
        # fim o mais antigo -- que e o que ja pode estar linkado em algum
        # lugar. Desempate estavel, para rodar duas vezes dar o mesmo.
        itens.sort(key=lambda i: (0 if i["doi"] else 1,
                                  0 if i["abstract"] else 1, i["id"]))
        fica, saem = itens[0], itens[1:]
        segmentos = set()
        for item in itens:
            segmentos.update(s for s in (item["segmento"] or "").split("; ") if s)
        db.execute(
            "UPDATE biblioteca_item SET segmento = ?, chave_titulo = ? WHERE id = ?",
            ("; ".join(sorted(segmentos)) or None, chave_titulo, fica["id"]))
        for item in saem:
            db.execute("DELETE FROM biblioteca_item WHERE id = ?", (item["id"],))
            sumiram.append(item["title"])
        juntados += len(saem)
    db.conn.commit()
    return {"juntados": juntados, "grupos": sum(1 for g in grupos.values() if len(g) > 1),
            "titulos": sumiram[:20]}


def reclassificar(db: Database, code: str) -> dict[str, Any]:
    """Le de novo desenho e intervencao do que ja esta guardado.

    Nao sai para a rede: o cru -- tipos de publicacao e descritores -- fica
    na linha justamente para isto. Quando o vocabulario ganha um termo, o
    acervo inteiro se atualiza em segundos, e nao em quarenta e cinco
    buscas.
    """
    bid = db.scalar("SELECT id FROM biblioteca WHERE code = ?", (code,))
    if not bid:
        raise ValueError(f"biblioteca “{code}” não existe")
    mudaram = 0
    for item in db.dicts(
            "SELECT id, pub_types, keywords, desenho, intervencao"
            "  FROM biblioteca_item WHERE biblioteca_id = ?", (bid,)):
        lido = classificar(item)
        if (lido["desenho"], lido["intervencao"]) == (item["desenho"], item["intervencao"]):
            continue
        db.execute("UPDATE biblioteca_item SET desenho = ?, intervencao = ? WHERE id = ?",
                   (lido["desenho"], lido["intervencao"], item["id"]))
        mudaram += 1
    db.conn.commit()
    com_desenho = int(db.scalar(
        "SELECT COUNT(*) FROM biblioteca_item WHERE biblioteca_id = ?"
        "   AND desenho IS NOT NULL", (bid,)) or 0)
    total = int(db.scalar("SELECT COUNT(*) FROM biblioteca_item WHERE biblioteca_id = ?",
                          (bid,)) or 0)
    return {"mudaram": mudaram, "com_desenho": com_desenho, "total": total}


def _colher(base: str, query: str, limite: int) -> list[dict[str, Any]]:
    """Os registros de uma busca, na base pedida."""
    if base == PUBMED:
        from . import referencias, sources
        pmids = sources.pubmed_search(query, retmax=limite)
        if not pmids:
            return []
        registros = referencias.ler_nbib(sources.pubmed_medline(pmids))
        for r in registros:
            r["base"] = PUBMED
        return registros
    if base == SCOPUS:
        return buscar_scopus(query, limite)
    if base == WOS:
        return buscar_wos(query, limite)
    if base in BASES_MANUAIS:
        raise SemApi(PORQUE_MANUAL.get(
            base, f"{ROTULO_BASE.get(base, base)} não tem API: cole a estratégia na base."))
    raise ValueError(f"base desconhecida: {base}")


def _gravar(db: Database, biblioteca_id: int, segmento: str | None,
            registro: dict[str, Any], chaves_de_uniao: Any) -> bool:
    """Grava um registro. Devolve True se ele ainda nao estava aqui.

    Procura pelas DUAS chaves, e nao so pela principal. As bases discordam
    sobre o DOI: a PubMed traz o artigo com DOI, a Scopus traz o mesmo sem,
    e comparando so a chave principal o segundo vira artigo novo. O acervo
    passaria a contar duas vezes a mesma leitura, e a equipe leria o mesmo
    resumo duas vezes achando que sao dois estudos.
    """
    from . import variaveis

    chaves = chaves_de_uniao(registro)
    if not chaves:
        return False
    chave = chaves[0]
    por_titulo = next((c for c in chaves if c.startswith("tit:")), None)
    achado = db.dicts(
        "SELECT id, segmento FROM biblioteca_item"
        " WHERE biblioteca_id = ? AND (chave IN (%s) OR (chave_titulo IS NOT NULL"
        "   AND chave_titulo IN (%s)))" % (",".join("?" * len(chaves)),
                                           ",".join("?" * len(chaves))),
        (biblioteca_id, *chaves, *chaves))
    if achado:
        # Ja esta aqui, mas pode ter chegado agora por outro segmento: um
        # estudo com nadadores E handebolistas pertence aos dois, e guardar
        # so o primeiro faria o segundo parecer vazio.
        if segmento:
            atuais = [s for s in (achado[0]["segmento"] or "").split("; ") if s]
            if segmento not in atuais:
                atuais.append(segmento)
                db.execute("UPDATE biblioteca_item SET segmento = ? WHERE id = ?",
                           ("; ".join(sorted(atuais)), achado[0]["id"]))
                db.conn.commit()
        return False

    paises = variaveis.paises_da_afiliacao(
        registro.get("afiliacoes") or registro.get("affiliation"))
    lido = classificar(registro)
    db.execute(
        "INSERT INTO biblioteca_item (biblioteca_id, chave, chave_titulo, segmento,"
        "        title, abstract, authors, journal, year, doi, pmid, pmc, url,"
        "        oa_url, paises, pub_types, keywords, desenho, intervencao, base)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (biblioteca_id, chave, por_titulo, segmento, clean_text(registro.get("title")),
         clean_text(registro.get("abstract")),
         "; ".join(registro.get("authors") or []) if isinstance(registro.get("authors"), list)
         else clean_text(registro.get("authors")),
         clean_text(registro.get("journal")), registro.get("year"),
         norm_doi(registro.get("doi")), clean_text(registro.get("pmid")),
         clean_text(registro.get("pmc")), clean_text(registro.get("url")),
         clean_text(registro.get("oa_url")), json.dumps(paises, ensure_ascii=False),
         clean_text(registro.get("pub_types")), clean_text(registro.get("keywords")),
         lido["desenho"], lido["intervencao"],
         registro.get("base") or PUBMED))
    return True


# ----------------------------------------------------------------------
# O que a tela le
# ----------------------------------------------------------------------
def _item(linha: dict[str, Any]) -> dict[str, Any]:
    item = dict(linha)
    try:
        item["paises"] = json.loads(item.get("paises") or "[]")
    except (TypeError, ValueError):
        item["paises"] = []
    item["segmentos"] = [s for s in (item.get("segmento") or "").split("; ") if s]
    item["links"] = links(item)
    # O caminho que abre o artigo, e nao a busca: e o que o botao grande usa.
    direto = [l for l in item["links"] if l["tipo"] == DIRETO]
    item["direto"] = direto[0]["url"] if direto else None
    item["livre"] = any(l.get("livre") for l in item["links"])
    return item


def listar(db: Database, code: str, segmento: str | None = None,
           busca: str | None = None, pais: str | None = None,
           desenho: str | None = None, intervencao: str | None = None,
           limite: int = 300) -> dict[str, Any]:
    """O acervo, inteiro ou recortado por segmento."""
    dados = db.dicts(
        "SELECT b.*, rl.name AS linha FROM biblioteca b"
        " LEFT JOIN research_lines rl ON rl.id = b.research_line_id"
        " WHERE b.code = ?", (code,))
    if not dados:
        raise ValueError(f"biblioteca “{code}” não existe")
    biblioteca = dados[0]

    onde, params = ["biblioteca_id = ?"], [biblioteca["id"]]
    if segmento:
        # `LIKE` porque um item pode pertencer a varios segmentos, guardados
        # numa lista -- e o recorte tem de achar o item nos dois.
        onde.append("('; ' || segmento || '; ') LIKE ?")
        params.append(f"%; {segmento}; %")
    if desenho:
        onde.append("('; ' || desenho || '; ') LIKE ?")
        params.append(f"%; {desenho}; %")
    if intervencao:
        onde.append("('; ' || intervencao || '; ') LIKE ?")
        params.append(f"%; {intervencao}; %")
    if pais:
        # Os paises viajam como JSON na coluna. Procurar o nome entre aspas
        # evita que "Chile" case com um pais cujo nome o contenha, e evita
        # que o recorte por pais vire uma busca em texto -- que era o
        # defeito do clique no mapa do painel: "Itália" nao esta no titulo
        # nem no resumo da maioria dos artigos feitos na Italia.
        onde.append("paises LIKE ?")
        params.append(f'%"{pais}"%')
    if busca:
        onde.append("(LOWER(title) LIKE ? OR LOWER(abstract) LIKE ?"
                    " OR LOWER(authors) LIKE ? OR LOWER(journal) LIKE ?)")
        params.extend([f"%{busca.lower()}%"] * 4)
    itens = db.dicts(
        f"SELECT * FROM biblioteca_item WHERE {' AND '.join(onde)}"
        f" ORDER BY COALESCE(year, 0) DESC, title LIMIT ?", params + [limite])
    return {"biblioteca": biblioteca, "itens": [_item(i) for i in itens],
            "segmento": segmento, "busca": busca, "pais": pais,
            "desenho": desenho, "intervencao": intervencao}


def panorama(db: Database, code: str) -> dict[str, Any]:
    """O retrato do acervo: tamanho, segmentos, anos, países e acesso.

    Serve para a pessoa saber ONDE procurar antes de procurar. Um acervo de
    quatrocentos artigos sem esse retrato e uma lista, e uma lista longa e
    exatamente o que a equipe ja tinha antes de existir biblioteca.
    """
    dados = db.dicts(
        "SELECT b.*, rl.name AS linha FROM biblioteca b"
        " LEFT JOIN research_lines rl ON rl.id = b.research_line_id"
        " WHERE b.code = ?", (code,))
    if not dados:
        raise ValueError(f"biblioteca “{code}” não existe")
    biblioteca = dados[0]
    bid = biblioteca["id"]

    total = int(db.scalar("SELECT COUNT(*) FROM biblioteca_item WHERE biblioteca_id = ?",
                          (bid,)) or 0)
    # Os segmentos saem das BUSCAS, e nao do que foi achado: segmento que
    # voltou vazio precisa aparecer com zero. Some-lo faria a tela dizer que
    # ninguem estuda humor no remo, quando o certo e que a busca nao achou.
    #
    # Ha uma busca por segmento POR BASE, e o segmento e um so. Sem juntar,
    # a tela listava "Handebol" tres vezes seguidas -- uma por base --, e o
    # que era uma divisao por modalidade virava uma lista com repeticao.
    por_segmento: dict[str, dict[str, Any]] = {}
    for busca in db.dicts(
            "SELECT base, segmento, achados, rodada_em, erro FROM biblioteca_busca"
            " WHERE biblioteca_id = ? AND segmento IS NOT NULL"
            " ORDER BY segmento, base", (bid,)):
        alvo = por_segmento.setdefault(busca["segmento"], {
            "segmento": busca["segmento"], "n": 0, "rodada_em": None,
            "erro": None, "erros": [], "bases": []})
        # A data que interessa e a MAIS RECENTE: se a PubMed rodou hoje e a
        # Scopus na semana passada, dizer "semana passada" faria o acervo
        # parecer mais velho do que e.
        if busca["rodada_em"] and (not alvo["rodada_em"]
                                   or busca["rodada_em"] > alvo["rodada_em"]):
            alvo["rodada_em"] = busca["rodada_em"]
        if busca["erro"]:
            alvo["erros"].append({"base": busca["base"], "erro": busca["erro"]})
        if busca["rodada_em"] and not busca["erro"]:
            alvo["bases"].append(busca["base"])

    for nome, alvo in por_segmento.items():
        alvo["n"] = int(db.scalar(
            "SELECT COUNT(*) FROM biblioteca_item WHERE biblioteca_id = ?"
            "   AND ('; ' || segmento || '; ') LIKE ?", (bid, f"%; {nome}; %")) or 0)
        # Um erro para a tela mostrar, com a base que o produziu -- e nao
        # um erro solto, que nao diz onde procurar.
        if alvo["erros"]:
            primeiro = alvo["erros"][0]
            alvo["erro"] = f"{ROTULO_BASE.get(primeiro['base'], primeiro['base'])}: " \
                           f"{primeiro['erro']}"
    segmentos = sorted(por_segmento.values(), key=lambda x: (-x["n"], x["segmento"]))

    anos = db.dicts(
        "SELECT year AS ano, COUNT(*) AS n FROM biblioteca_item"
        " WHERE biblioteca_id = ? AND year IS NOT NULL GROUP BY year ORDER BY year", (bid,))

    contagem: dict[str, int] = {}
    for linha in db.dicts(
            "SELECT paises FROM biblioteca_item WHERE biblioteca_id = ?", (bid,)):
        try:
            for pais in json.loads(linha["paises"] or "[]"):
                contagem[pais] = contagem.get(pais, 0) + 1
        except (TypeError, ValueError):
            continue
    paises = sorted(({"pais": p, "n": n} for p, n in contagem.items()),
                    key=lambda x: (-x["n"], x["pais"]))

    sem_ano = int(db.scalar(
        "SELECT COUNT(*) FROM biblioteca_item WHERE biblioteca_id = ? AND year IS NULL",
        (bid,)) or 0)
    livres = int(db.scalar(
        "SELECT COUNT(*) FROM biblioteca_item WHERE biblioteca_id = ?"
        "   AND (pmc IS NOT NULL OR oa_url IS NOT NULL)", (bid,)) or 0)
    com_doi = int(db.scalar(
        "SELECT COUNT(*) FROM biblioteca_item WHERE biblioteca_id = ?"
        "   AND doi IS NOT NULL AND TRIM(doi) <> ''", (bid,)) or 0)

    return {
        "biblioteca": biblioteca, "total": total, "segmentos": segmentos,
        "anos": anos, "sem_ano": sem_ano, "paises": paises,
        "livres": livres, "com_doi": com_doi,
        "buscas": db.dicts(
            "SELECT segmento, query, rodada_em, achados, novos, erro"
            "  FROM biblioteca_busca WHERE biblioteca_id = ?"
            " ORDER BY segmento IS NULL DESC, segmento", (bid,)),
    }


def todas(db: Database, quem: int | None = None,
          perfil: str = "leitura") -> list[dict[str, Any]]:
    """Os acervos que ESTA pessoa pode ver.

    Acervo restrito e do dono, e da coordenacao. Nao e um cofre: quem
    coordena tem o arquivo do banco na propria maquina, e esconder dela na
    tela nao esconderia nada -- seria teatro, e teatro de privacidade e
    pior que nenhuma, porque quem acredita nele guarda ali o que nao
    guardaria.

    O padrao e conservador de proposito: chamada sem `quem`, devolve so os
    acervos abertos. Uma tela nova que esquecesse de passar o usuario
    mostraria acervo restrito a todo mundo -- e esse e o tipo de descuido
    que nao da erro nenhum e so se descobre depois.
    """
    manda = perfil in ("coordenacao", "admin")
    return db.dicts(
        "SELECT b.code, b.title, b.descricao, b.eixo, b.atualizada_em,"
        "       b.restrita, b.dono_id, m.short_name AS dono,"
        "       rl.name AS linha,"
        "       (SELECT COUNT(*) FROM biblioteca_item i WHERE i.biblioteca_id = b.id) AS n"
        "  FROM biblioteca b"
        "  LEFT JOIN research_lines rl ON rl.id = b.research_line_id"
        "  LEFT JOIN members m ON m.id = b.dono_id"
        " WHERE b.ativa = 1"
        "   AND (b.restrita = 0 OR ? = 1 OR b.dono_id IS ?)"
        " ORDER BY b.title",
        (1 if manda else 0, quem))


def pode_ver(db: Database, code: str, quem: int | None = None,
             perfil: str = "leitura") -> bool:
    """Se esta pessoa pode abrir ESTE acervo, pelo code.

    Existe separada de `todas` porque as rotas de um acervo so -- o
    retrato, a analise, a atualizacao -- entram pelo `code` e nunca
    passariam pela lista. Sem esta, esconder na lista e deixar a rota
    aberta: quem tivesse o endereco veria o acervo restrito, e o endereco
    e o titulo em minusculas.
    """
    linha = db.dicts(
        "SELECT restrita, dono_id FROM biblioteca WHERE code = ?", (code,))
    if not linha:
        return False
    if not linha[0]["restrita"]:
        return True
    if perfil in ("coordenacao", "admin"):
        return True
    return quem is not None and linha[0]["dono_id"] == quem


def declarar_dono(db: Database, code: str, member_id: int | None,
                  restrita: bool | None = None) -> dict[str, Any]:
    """Diz de quem e o acervo, e se ele e so dessa pessoa."""
    achada = db.scalar("SELECT id FROM biblioteca WHERE code = ?", (code,))
    if not achada:
        raise ValueError(f"biblioteca “{code}” não existe")
    if restrita is None:
        restrita = member_id is not None
    db.execute("UPDATE biblioteca SET dono_id = ?, restrita = ? WHERE id = ?",
               (member_id, 1 if restrita else 0, achada))
    db.conn.commit()
    return {"code": code, "dono_id": member_id, "restrita": bool(restrita)}


# ----------------------------------------------------------------------
# O mapeamento analitico do acervo
# ----------------------------------------------------------------------
# As contas sao as MESMAS do painel da producao do laboratorio, e isso e
# de proposito. Elas moram em `analise` e nao sao copiadas para ca: uma
# segunda implementacao de mediana movel divergiria da primeira no dia em
# que alguem corrigisse uma das duas, e o painel passaria a discordar de si
# mesmo sobre o que e uma curva legivel.
#
# O que muda e o objeto: la a serie e a producao do LAPE, aqui e a
# literatura mundial sobre um assunto. A pergunta tambem muda -- nao e
# "como vamos", e "o que o campo esta fazendo, e onde ele parou de crescer".
# Os limiares NAO sao redeclarados aqui. Sao os de `analise`, importados,
# porque uma segunda copia de "0,8" divergiria da primeira no dia em que
# alguem ajustasse uma das duas -- e o sistema passaria a ter duas
# definicoes de "curva legivel", uma para a producao do laboratorio e
# outra para a literatura, sem nada na tela dizendo isso.


def _serie_por_ano(itens: list[dict[str, Any]], anos: list[int]) -> list[float]:
    contagem: dict[int, int] = {}
    for item in itens:
        ano = item.get("year")
        if ano:
            contagem[int(ano)] = contagem.get(int(ano), 0) + 1
    return [float(contagem.get(ano, 0)) for ano in anos]


def _curva(anos: list[int], serie: list[float]) -> dict[str, Any]:
    """A serie filtrada, suas derivadas e o que sobrou de ruido.

    `sinal_e_ruido` ja aplica a mediana movel por dentro. Filtrar antes de
    chama-la passaria a serie pelo filtro DUAS vezes, e o resultado seria
    uma curva mais lisa do que o dado permite -- com menos ruido medido e
    menos inflexoes do que existem, o que faz o campo parecer mais
    estavel do que e.
    """
    from . import analise

    ruido = analise.sinal_e_ruido(serie)
    suave = ruido["suave"]
    vel = analise.velocidade(suave)
    legivel = bool(ruido["confiavel"])
    return {
        "anos": anos, "serie": serie, "suave": suave,
        "velocidade": vel, "aceleracao": analise.aceleracao(suave),
        "ruido": ruido["razao_ruido"], "faixa": ruido.get("faixa"),
        "anos_com_dado": ruido["anos_com_dado"],
        "inflexoes": analise.inflexoes(anos, suave) if legivel else [],
        "tendencia": analise.tendencia(suave, vel, ruido["anos_com_dado"]),
        "crescimento_ao_ano": analise.crescimento_anual(suave),
        "legivel": legivel,
        # Por que NAO da para ler, quando nao da. Sem isto a tela mostra um
        # cartao vazio e quem olha conclui que o assunto nao existe.
        "porque": (None if legivel else (
            ruido["porque"] or f"o ruído responde por {ruido['razao_ruido']} da série")),
    }


def analitico(db: Database, code: str, desde: int | None = None) -> dict[str, Any]:
    """O retrato analitico do acervo: curvas, mapa, rede e a arvore.

    Recorta por ano de proposito: literatura de trinta anos atras foi feita
    com outro instrumento -- o POMS de 65 itens, antes do BRUMS -- e sobre
    outra populacao. Misturar tudo numa curva so faz a curva nao significar
    nada, que e o mesmo motivo do recorte no painel da producao.
    """
    dados = db.dicts(
        "SELECT b.*, rl.name AS linha FROM biblioteca b"
        " LEFT JOIN research_lines rl ON rl.id = b.research_line_id"
        " WHERE b.code = ?", (code,))
    if not dados:
        raise ValueError(f"biblioteca “{code}” não existe")
    biblioteca_ = dados[0]
    bid = biblioteca_["id"]

    itens = [_item(i) for i in db.dicts(
        "SELECT * FROM biblioteca_item WHERE biblioteca_id = ?", (bid,))]
    anos_vistos = sorted({int(i["year"]) for i in itens if i.get("year")})
    if not anos_vistos:
        return {"biblioteca": biblioteca_, "vazio": True,
                "porque": "nenhum artigo do acervo tem ano de publicação"}
    corte = desde or max(anos_vistos[0], date.today().year - 24)
    anos = list(range(corte, date.today().year + 1))
    dentro = [i for i in itens if i.get("year") and int(i["year"]) >= corte]

    # -- a curva do acervo inteiro, e uma por segmento -----------------
    geral = _curva(anos, _serie_por_ano(dentro, anos))
    por_segmento = []
    for nome, _palavras in ESPORTES:
        do_segmento = [i for i in dentro if nome in i["segmentos"]]
        if not do_segmento:
            continue
        curva = _curva(anos, _serie_por_ano(do_segmento, anos))
        curva.update({"segmento": nome, "n": len(do_segmento)})
        por_segmento.append(curva)
    por_segmento.sort(key=lambda x: -x["n"])

    return {
        "biblioteca": biblioteca_, "vazio": False,
        "janela": {"de": corte, "ate": date.today().year, "anos": anos},
        "total": len(itens), "no_recorte": len(dentro),
        "geral": geral, "segmentos": por_segmento,
        "paises": _paises_do_acervo(dentro),
        "desenhos": _contar(dentro, "desenho", DESENHOS),
        "intervencoes": _contar(dentro, "intervencao", INTERVENCOES),
        "espaco_tempo": _espaco_tempo(dentro, anos),
        "rede": _rede_do_acervo(dentro),
        "triangulo": _triangulo(dentro),
        "decisao": _decisao(por_segmento),
    }


def _contar(itens: list[dict[str, Any]], campo: str,
            vocabulario: tuple) -> dict[str, Any]:
    """Quantos artigos em cada rotulo, e quantos ficaram sem leitura.

    O "sem leitura" sai a parte, e nao vira uma fatia chamada "outros".
    Sao artigos que vieram da Scopus ou da WoS, que nao devolvem tipo de
    publicacao nem descritor na busca -- entao nao e que o estudo seja de
    outro desenho: e que ninguem disse qual. Um acervo em que 40% dos
    estudos aparecem como "transversal" por omissao e pior do que um que
    admite o buraco.
    """
    contagem: dict[str, dict[str, Any]] = {}
    for _codigo, rotulo, _termos in vocabulario:
        contagem[rotulo] = {"rotulo": rotulo, "n": 0, "artigos": []}
    sem = 0
    for item in itens:
        rotulos = [r for r in str(item.get(campo) or "").split("; ") if r]
        if not rotulos:
            sem += 1
            continue
        for rotulo in rotulos:
            if rotulo in contagem:
                contagem[rotulo]["n"] += 1
                contagem[rotulo]["artigos"].append(item["id"])
    achados = sorted(contagem.values(), key=lambda x: -x["n"])
    return {"todos": achados, "sem_leitura": sem,
            "com_leitura": len(itens) - sem,
            "quantos": sum(1 for a in achados if a["n"])}


def _espaco_tempo(itens: list[dict[str, Any]],
                  anos: list[int]) -> dict[str, Any]:
    """Quantos artigos por pais em cada ano.

    E o que faz o globo ter tempo: girando, ele mostra ONDE; avancando o
    ano, mostra QUANDO aquele onde aconteceu. Separado do total porque a
    pergunta e outra -- "quem estuda isso" e "quem passou a estudar isso"
    tem respostas diferentes, e a segunda e a que diz para onde o campo
    esta indo.
    """
    por_ano: dict[int, dict[str, int]] = {ano: {} for ano in anos}
    for item in itens:
        ano = int(item.get("year") or 0)
        if ano not in por_ano:
            continue
        for pais in item.get("paises") or []:
            por_ano[ano][pais] = por_ano[ano].get(pais, 0) + 1
    # O acumulado responde "quanto ja se produziu ate aqui", que e a
    # leitura que faz sentido num mapa: o mapa de um ano so pisca, porque
    # a maior parte dos paises publica um artigo a cada tres anos.
    acumulado: dict[str, int] = {}
    quadros = []
    for ano in anos:
        for pais, n in por_ano[ano].items():
            acumulado[pais] = acumulado.get(pais, 0) + n
        quadros.append({"ano": ano, "paises": dict(acumulado),
                        "no_ano": dict(por_ano[ano]),
                        "total": sum(acumulado.values())})
    return {"quadros": quadros, "anos": anos}


def _paises_do_acervo(itens: list[dict[str, Any]]) -> dict[str, Any]:
    """Onde o assunto e estudado, pela afiliacao de quem assina.

    O pais vem de QUEM ASSINA, e nao da revista: uma revista holandesa
    publica o mundo inteiro, e contar por revista responderia "onde se
    publica", que e outra pergunta.
    """
    from .variaveis import bandeira, iso2

    contagem: dict[str, dict[str, Any]] = {}
    for item in itens:
        for pais in item.get("paises") or []:
            # `iso` viaja junto com `bandeira`: o emoji nao aparece no
            # Windows, e e do codigo que a tela desenha a bandeira em SVG.
            alvo = contagem.setdefault(pais, {"pais": pais, "n": 0, "artigos": [],
                                              "bandeira": bandeira(pais),
                                              "iso": iso2(pais)})
            alvo["n"] += 1
            alvo["artigos"].append(item["id"])
    todos = sorted(contagem.values(), key=lambda x: (-x["n"], x["pais"]))
    for alvo in todos:
        alvo["artigos"].sort()
    sem_pais = sum(1 for i in itens if not (i.get("paises") or []))
    return {"todos": todos, "sem_pais": sem_pais,
            "quantos": len(todos)}


def _rede_do_acervo(itens: list[dict[str, Any]],
                    minimo: int = 2) -> dict[str, Any]:
    """Quem escreve com quem, dentro do acervo.

    Os nomes vem do campo de autores, que e texto -- as bases nao dao
    identificador de pessoa de graca. Entao dois autores homonimos viram
    um no, e a mesma pessoa com duas grafias vira dois. A tela diz isso:
    uma rede apresentada como verdade sobre pessoas, construida sobre
    grafias, e uma afirmacao que o dado nao sustenta.
    """
    from .util import author_key

    por_artigo: list[list[str]] = []
    nomes: dict[str, str] = {}
    for item in itens:
        autores = [a.strip() for a in (item.get("authors") or "").split(";") if a.strip()]
        chaves = []
        for autor in autores[:12]:      # 12 primeiros: papel com 40 autores viraria ruido
            chave = author_key(autor)
            if not chave:
                continue
            nomes.setdefault(chave, autor)
            if chave not in chaves:
                chaves.append(chave)
        if len(chaves) > 1:
            por_artigo.append(chaves)

    grau: dict[str, int] = {}
    peso: dict[tuple[str, str], int] = {}
    for chaves in por_artigo:
        for chave in chaves:
            grau[chave] = grau.get(chave, 0) + 1
        for i, a in enumerate(chaves):
            for b in chaves[i + 1:]:
                par = tuple(sorted((a, b)))
                peso[par] = peso.get(par, 0) + 1

    fortes = {par: n for par, n in peso.items() if n >= minimo}
    vivos = {c for par in fortes for c in par}
    return {
        "nos": sorted(({"id": c, "nome": nomes[c], "n": grau.get(c, 0)}
                       for c in vivos), key=lambda x: -x["n"])[:60],
        "arestas": sorted(({"de": a, "para": b, "peso": n}
                           for (a, b), n in fortes.items()), key=lambda x: -x["peso"])[:200],
        "minimo": minimo,
        "autores": len(grau),
        # O aviso viaja com o dado, e nao fica so na tela: quem consumir
        # este payload por outro caminho precisa receber a ressalva junto.
        "ressalva": ("Os nós são grafias de nome, não pessoas: dois autores "
                     "homônimos viram um nó, e a mesma pessoa com duas grafias "
                     "vira dois."),
    }


def _triangulo(itens: list[dict[str, Any]]) -> dict[str, Any]:
    """Modalidade x pais: onde cada esporte e estudado.

    E a face que o acervo sustenta. Triangular construto x intervencao x
    desfecho, como o painel faz com a producao do LAPE, exigiria ler os
    metodos de cada artigo -- e isso o titulo e o resumo nao dizem de
    maneira confiavel. Prometer a triangulacao completa a partir do
    resumo seria dar rigor de fachada a um palpite.
    """
    celulas: dict[tuple[str, str], int] = {}
    esportes: dict[str, int] = {}
    paises: dict[str, int] = {}
    for item in itens:
        for segmento in item.get("segmentos") or []:
            for pais in item.get("paises") or []:
                celulas[(segmento, pais)] = celulas.get((segmento, pais), 0) + 1
                esportes[segmento] = esportes.get(segmento, 0) + 1
                paises[pais] = paises.get(pais, 0) + 1
    linhas = [e for e, _ in sorted(esportes.items(), key=lambda x: -x[1])[:12]]
    colunas = [p for p, _ in sorted(paises.items(), key=lambda x: -x[1])[:12]]
    return {
        "eixo_y": "modalidade", "eixo_x": "país",
        "linhas": linhas, "colunas": colunas,
        "celulas": [{"y": e, "x": p, "n": n} for (e, p), n in celulas.items()
                    if e in linhas and p in colunas],
        "vazios": [e for e in linhas
                   if not any(c for (s, _p), c in celulas.items() if s == e)],
    }


def _decisao(segmentos: list[dict[str, Any]]) -> dict[str, Any]:
    """A arvore que decide se a curva de um segmento pode ser lida.

    As mesmas tres perguntas do painel, com quantas modalidades caem de
    cada lado -- e assim quem olha ve POR QUE a maior parte das
    modalidades nao tem curva, em vez de descobrir isso um cartao vazio de
    cada vez.
    """
    from . import analise

    curtos = [s for s in segmentos if s["anos_com_dado"] < analise.MIN_ANOS_COM_DADO]
    longos = [s for s in segmentos if s["anos_com_dado"] >= analise.MIN_ANOS_COM_DADO]
    ruidosos = [s for s in longos
                if s["ruido"] is not None and s["ruido"] >= analise.RUIDO_ALTO]
    limpos = [s for s in longos if s not in ruidosos]
    viraram = [s for s in limpos if s["inflexoes"]]
    lisos = [s for s in limpos if not s["inflexoes"]]
    nomes = lambda lista: [s["segmento"] for s in lista]  # noqa: E731
    return {
        "total": len(segmentos),
        "curtos": {"n": len(curtos), "quais": nomes(curtos)},
        "ruidosos": {"n": len(ruidosos), "quais": nomes(ruidosos)},
        "viraram": {"n": len(viraram), "quais": nomes(viraram)},
        "lisos": {"n": len(lisos), "quais": nomes(lisos)},
        "min_anos": analise.MIN_ANOS_COM_DADO, "ruido_alto": analise.RUIDO_ALTO,
    }


# ----------------------------------------------------------------------
# Desenho do estudo e intervencao
# ----------------------------------------------------------------------
# A leitura sai do que a BASE declara, e nao de um palpite sobre o texto.
# Tipo de publicacao e descritor MeSH sao curadoria da PubMed, feita por
# indexador humano -- dizer "ensaio randomizado" porque o resumo tem a
# palavra "randomized" seria outra coisa, e erraria justamente nos artigos
# que discutem randomizacao sem serem randomizados.
#
# Por isso tudo aqui procura em `pub_types` e `keywords`, e nao no resumo.
# O preco e que artigo vindo so da Scopus ou da WoS fica SEM desenho -- as
# duas nao devolvem esses campos na busca. A tela diz "não classificado" em
# vez de chutar, porque um acervo em que 40% dos estudos aparecem como
# "transversal" por omissao e pior do que um que admite o buraco.
DESENHOS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    # (codigo, rotulo, termos que a base declara)
    # A ordem e a da forca da evidencia: um artigo que e meta-analise E
    # revisao sistematica conta como meta-analise, que e o que ele tem de
    # mais forte. Sem ordem, o rotulo dependeria de qual termo a base
    # escreveu primeiro.
    ("meta_analise", "Meta-análise", ("Meta-Analysis",)),
    ("revisao_sistematica", "Revisão sistemática",
     ("Systematic Review", "Systematic Reviews as Topic")),
    ("ensaio_randomizado", "Ensaio randomizado",
     ("Randomized Controlled Trial", "Randomized Controlled Trials as Topic")),
    ("ensaio_controlado", "Ensaio controlado",
     ("Controlled Clinical Trial", "Clinical Trial")),
    ("coorte", "Coorte", ("Cohort Studies", "Prospective Studies",
                          "Follow-Up Studies", "Longitudinal Studies")),
    ("caso_controle", "Caso-controle", ("Case-Control Studies",)),
    ("transversal", "Transversal", ("Cross-Sectional Studies",)),
    ("revisao", "Revisão narrativa", ("Review",)),
    ("validacao", "Validação de instrumento",
     ("Validation Study", "Psychometrics", "Reproducibility of Results")),
    ("relato", "Relato de caso", ("Case Reports",)),
)

# As intervencoes que a literatura de humor no esporte de fato testa. Saem
# do MeSH, que e onde a PubMed registra o que foi feito -- e nao de uma
# lista de tudo que existe, que encheria a tela de segmentos vazios.
INTERVENCOES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("resistido", "Treinamento resistido",
     ("Resistance Training", "Weight Lifting", "Muscle Strength")),
    ("aerobio", "Exercício aeróbio",
     ("Exercise", "Running", "Physical Endurance", "Physical Conditioning, Human")),
    ("alta_intensidade", "Alta intensidade",
     ("High-Intensity Interval Training",)),
    ("mental", "Treino mental e psicológico",
     ("Imagery, Psychotherapy", "Cognitive Behavioral Therapy", "Psychotherapy",
      "Relaxation Therapy", "Biofeedback, Psychology", "Hypnosis")),
    ("mindfulness", "Mindfulness e meditação", ("Mindfulness", "Meditation", "Yoga")),
    ("recuperacao", "Recuperação e sono",
     ("Sleep", "Rest", "Muscle Stretching Exercises", "Massage", "Hydrotherapy",
      "Cryotherapy")),
    ("nutricao", "Nutrição e suplementação",
     ("Dietary Supplements", "Caffeine", "Carbohydrates", "Creatine",
      "Sports Nutritional Physiological Phenomena")),
    ("carga", "Carga e periodização",
     ("Physical Exertion", "Workload", "Athletic Performance", "Overtraining")),
    ("musica", "Música", ("Music", "Music Therapy")),
)

NAO_CLASSIFICADO = "não classificado"


def _ler_declarado(termos: str, vocabulario: tuple, limite: int = 0) -> str | None:
    """Os rotulos cujo termo a base declarou, na ordem do vocabulario."""
    if not termos:
        return None
    baixo = termos.lower()
    achados = []
    for _codigo, rotulo, chaves in vocabulario:
        if any(chave.lower() in baixo for chave in chaves):
            achados.append(rotulo)
            if limite and len(achados) >= limite:
                break
    return "; ".join(achados) or None


def classificar(registro: dict[str, Any]) -> dict[str, str | None]:
    """Desenho e intervencao de um registro, pelo que a base declarou.

    O desenho e UM so -- o mais forte --, porque um artigo tem um desenho.
    "Meta-analise e tambem transversal" nao e uma frase sobre metodo, e
    somar as duas contagens faria o total dos desenhos passar do total de
    artigos, o que deixa qualquer percentual sem sentido.

    A intervencao pode ser varias: um ensaio compara treino resistido com
    mindfulness, e ele e dos dois.
    """
    declarado = "; ".join(
        str(registro.get(campo) or "") for campo in ("pub_types", "keywords"))
    return {
        "desenho": _ler_declarado(declarado, DESENHOS, limite=1),
        "intervencao": _ler_declarado(declarado, INTERVENCOES),
    }
