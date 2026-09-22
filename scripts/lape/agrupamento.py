"""Agrupamento: os temas que o ACERVO forma sozinho.

Os segmentos de uma biblioteca sao declarados pelo laboratorio -- alguem
escreveu "clima motivacional" e listou as palavras. Isso e bom e e
proposital: recorte de leitura tem de ser decidido por quem le. Mas deixa
uma pergunta em aberto, e ela e a pergunta de uma revisao de escopo: a
literatura se divide MESMO assim?

Este modulo responde isso sem opinar. Ele le titulo, resumo e palavras-
chave, mede quais termos andam juntos e agrupa os artigos por semelhanca.
O resultado nao substitui os segmentos: ele e posto AO LADO deles, com a
distribuicao de cada grupo pelos segmentos declarados. Quando os dois
coincidem, a segmentacao do laboratorio esta descrevendo a literatura;
quando nao, ha uma conversa para ter -- e e ela que vale.

DECISOES QUE IMPORTAM, porque agrupamento e facil de fazer errado:

  Pouco dado nao vira grupo. Abaixo de `MINIMO` artigos o modulo RECUSA,
  em vez de devolver tres grupos de quatro artigos com cara de achado. Um
  agrupamento de doze artigos e um desenho bonito de nada.

  A mesma pergunta da a mesma resposta. O k-medias comum sorteia os
  centros e muda de resultado a cada rodada -- e um painel que muda
  sozinho entre dois cliques destroi a confianca em tudo o mais que esta
  na tela. Aqui a semeadura e determinista (k-medias++ com sorteio de
  semente fixa) e o desempate e sempre pelo mesmo criterio.

  O numero de grupos nao e escolhido no olho. Testa-se de 2 a `K_MAXIMO`
  e fica o k de melhor silhueta -- e a silhueta vai na resposta, porque
  ela e quem diz se ha estrutura ali ou se os grupos sao um corte
  arbitrario num borrao. Silhueta baixa e dito em palavras, nao escondido.

  Nada de numpy nem scipy: o sistema inteiro e stdlib, e com algumas
  centenas de documentos o Python puro resolve em menos de um segundo.
"""
from __future__ import annotations

import math
import random
import re
from collections import Counter
from typing import Any

from .db import Database
from .util import strip_accents

# Menos que isto nao e acervo, e agrupar vira desenho. O numero nao e
# magico: com doze artigos e tres grupos, cada grupo tem quatro -- e
# qualquer leitura que se faca deles cabe na mao, sem agrupamento nenhum.
MINIMO = 25

K_MAXIMO = 6

# Quantos termos descrevem cada grupo na tela.
TERMOS_POR_GRUPO = 8

# Termo que aparece em quase todo artigo nao separa nada -- e "handball"
# num acervo de handebol e exatamente isso. O corte e relativo ao acervo,
# e nao uma lista escrita a mao: a palavra onipresente muda com o assunto.
TETO_DE_FREQUENCIA = 0.6

# Termo que aparece em um artigo so nao agrupa ninguem, e enche a conta.
PISO_DE_DOCUMENTOS = 2

# Palavras que nao carregam assunto. Sao as duas linguas do acervo, e
# mais o vocabulario de metodo que aparece em todo resumo.
VAZIAS = frozenset("""
a an and are as at be been but by can did do does for from had has have
however if in into is it its of on or our so than that the their then there
these they this those to was were what when where which while who will with
within without
aim aims analysis approach article assess assessed associated association
background between both compared conclusion conclusions data design different
effect effects evidence findings group groups high higher included including
level levels low lower main measure measured method methods objective
obtained one participants purpose randomized result results sample score
scores show showed significant significantly statistical studied studies
study subjects three two use used using variables versus
a as com como da das de do dos e em entre foi foram mais mas na nas no nos
os ou para pela pelo por que se sem ser sao sobre um uma umas uns
analise dados efeito entre estudo estudos foi maior menor metodo metodos
nivel niveis objetivo participantes resultado resultados
""".split())


def _termos(texto: str) -> list[str]:
    """As palavras de um texto, sem acento, sem numero solto e sem as vazias."""
    limpo = strip_accents(str(texto or "")).lower()
    palavras = re.split(r"[^a-z0-9-]+", limpo)
    return [p for p in palavras
            if len(p) > 3 and p not in VAZIAS and not p.isdigit()]


def _texto_do_item(item: dict[str, Any]) -> str:
    """Titulo, resumo e palavras-chave. Nada de autor nem revista.

    O nome do autor agruparia por GRUPO DE PESQUISA em vez de por
    assunto -- e o nome da revista, por revista. Os dois sao perguntas
    legitimas, e sao outras: quem quiser vai ao mapeamento, que ja as
    responde.
    """
    return " ".join(str(item.get(campo) or "")
                    for campo in ("title", "abstract", "keywords"))


def _vetores(itens: list[dict[str, Any]]) -> tuple[list[dict[str, float]], list[str]]:
    """TF-IDF normalizado, um vetor por artigo.

    Normalizado porque resumo longo tem mais palavras, e sem normalizar o
    tamanho do resumo viraria a principal dimensao do agrupamento -- os
    grupos sairiam "artigos com resumo grande" e "artigos sem resumo".
    """
    listas = [Counter(_termos(_texto_do_item(i))) for i in itens]
    n = len(itens)
    documentos = Counter()
    for conta in listas:
        documentos.update(conta.keys())

    vocabulario = sorted(
        t for t, d in documentos.items()
        if d >= PISO_DE_DOCUMENTOS and d <= TETO_DE_FREQUENCIA * n)

    idf = {t: math.log(n / documentos[t]) + 1.0 for t in vocabulario}
    vetores: list[dict[str, float]] = []
    for conta in listas:
        bruto = {t: (1 + math.log(c)) * idf[t]
                 for t, c in conta.items() if t in idf}
        norma = math.sqrt(sum(v * v for v in bruto.values())) or 1.0
        vetores.append({t: v / norma for t, v in bruto.items()})
    return vetores, vocabulario


def _cosseno(a: dict[str, float], b: dict[str, float]) -> float:
    """Os dois ja vem normalizados: o produto interno E o cosseno."""
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(t, 0.0) for t, v in a.items())


def _centro(grupo: list[dict[str, float]]) -> dict[str, float]:
    soma: dict[str, float] = {}
    for vetor in grupo:
        for t, v in vetor.items():
            soma[t] = soma.get(t, 0.0) + v
    norma = math.sqrt(sum(v * v for v in soma.values())) or 1.0
    return {t: v / norma for t, v in soma.items()}


def _semear(vetores: list[dict[str, float]], k: int,
            sorteio: random.Random) -> list[dict[str, float]]:
    """k-medias++: o primeiro centro sorteado, os outros bem longe dele.

    Com a semente fixa isto e deterministico -- a mesma pergunta devolve
    o mesmo agrupamento hoje e amanha. Um painel que muda sozinho entre
    dois cliques destroi a confianca em tudo o mais que esta na tela.
    """
    centros = [dict(vetores[sorteio.randrange(len(vetores))])]
    while len(centros) < k:
        distancias = [min(1.0 - _cosseno(v, c) for c in centros) for v in vetores]
        total = sum(d * d for d in distancias)
        if total <= 0:
            centros.append(dict(vetores[sorteio.randrange(len(vetores))]))
            continue
        alvo = sorteio.random() * total
        acumulado = 0.0
        for vetor, d in zip(vetores, distancias):
            acumulado += d * d
            if acumulado >= alvo:
                centros.append(dict(vetor))
                break
    return centros


def _kmedias(vetores: list[dict[str, float]], k: int,
             voltas: int = 30, semente: int = 20260921) -> list[int]:
    sorteio = random.Random(semente)
    centros = _semear(vetores, k, sorteio)
    rotulos = [0] * len(vetores)
    for _ in range(voltas):
        mudou = False
        for i, vetor in enumerate(vetores):
            # `-j` no desempate: com dois centros igualmente proximos
            # ganha sempre o de menor indice, e nao o que a ordem interna
            # do dicionario entregar primeiro.
            melhor = max(range(k), key=lambda j: (_cosseno(vetor, centros[j]), -j))
            if melhor != rotulos[i]:
                rotulos[i] = melhor
                mudou = True
        for j in range(k):
            membros = [v for v, r in zip(vetores, rotulos) if r == j]
            if membros:
                centros[j] = _centro(membros)
        if not mudou:
            break
    return rotulos


def _silhueta(vetores: list[dict[str, float]], rotulos: list[int]) -> float:
    """Quanto os grupos se separam, de -1 a 1.

    Vai na resposta de proposito. Sem ela, tres grupos de um borrao tem
    exatamente a mesma cara de tres grupos de verdade -- e quem olha nao
    tem como saber qual dos dois esta vendo.
    """
    por_grupo: dict[int, list[dict[str, float]]] = {}
    for vetor, r in zip(vetores, rotulos):
        por_grupo.setdefault(r, []).append(vetor)
    if len(por_grupo) < 2:
        return 0.0
    total = 0.0
    for vetor, r in zip(vetores, rotulos):
        dentro = [1.0 - _cosseno(vetor, o) for o in por_grupo[r] if o is not vetor]
        a = sum(dentro) / len(dentro) if dentro else 0.0
        fora = []
        for outro, membros in por_grupo.items():
            if outro == r:
                continue
            fora.append(sum(1.0 - _cosseno(vetor, o) for o in membros) / len(membros))
        b = min(fora)
        total += (b - a) / max(a, b) if max(a, b) else 0.0
    return total / len(vetores)


def _ler_silhueta(valor: float) -> str:
    """O numero em palavras, porque silhueta ninguem sabe ler de cabeca."""
    if valor >= 0.5:
        return "os grupos se separam bem"
    if valor >= 0.25:
        return "há alguma estrutura, com grupos que se tocam nas bordas"
    if valor >= 0.1:
        return ("a separação é fraca: os grupos são mais um corte de leitura do "
                "que uma divisão que a literatura faça sozinha")
    return ("praticamente não há separação -- leia estes grupos como uma "
            "arrumação da lista, e não como um achado")


def _melhor_k(candidatos: list[tuple[int, list[int], float]]
              ) -> tuple[int, list[int], float] | None:
    """Entre os k testados, qual fica.

    Ganha a melhor silhueta -- MENOS quando ela vem de um grupo
    solitario. Grupo de um artigo nao e grupo: e um artigo. E a silhueta
    ADORA esses: um ponto sozinho longe de todos tem silhueta quase 1 e
    puxa a media do agrupamento inteiro para cima. A tela ficava com
    "grupo de 1" ao lado de grupos de doze, e a nota alta dizendo que
    estava tudo bem.

    Entao entre dois k ganha o que NAO produz grupo solitario; so quando
    todos produzem e que a nota volta a decidir sozinha -- porque ai nao
    ha escolha melhor a fazer, e esconder o resultado seria pior do que
    mostra-lo.

    Funcao a parte, e nao um trecho dentro do laco, porque esta regra e
    testavel sozinha: montar um caso com grupo solitario aqui custa tres
    linhas, e faze-lo aparecer num agrupamento de verdade depende da
    paisagem dos dados -- que muda com o acervo.
    """
    if not candidatos:
        return None
    return max(candidatos,
               key=lambda c: (min(Counter(c[1]).values()) >= 2, c[2]))


def agrupar(db: Database, code: str, segmento: str | None = None,
            k: int | None = None) -> dict[str, Any]:
    """Os grupos que o acervo forma, ao lado dos segmentos declarados."""
    acervo = db.dicts("SELECT id, title FROM biblioteca WHERE code = ?", (code,))
    if not acervo:
        raise ValueError(f"acervo “{code}” não existe")
    acervo = acervo[0]

    condicao = "biblioteca_id = ?"
    params: list[Any] = [acervo["id"]]
    if segmento:
        condicao += " AND segmento = ?"
        params.append(segmento)
    itens = db.dicts(
        "SELECT id, title, abstract, keywords, segmento, year, doi, base"
        f"  FROM biblioteca_item WHERE {condicao}"
        # ORDEM FIXA: o agrupamento depende da ordem de entrada, e sem
        # ordenar a mesma pergunta daria respostas diferentes conforme o
        # plano que o sqlite escolhesse.
        " ORDER BY id", params)

    base = {"acervo": acervo["title"], "code": code, "segmento": segmento,
            "n": len(itens), "grupos": [], "k": 0, "silhueta": None,
            "leitura": None, "aviso": None}
    if len(itens) < MINIMO:
        base["aviso"] = (
            f"{len(itens)} artigo(s) é pouco para agrupar — são precisos ao menos "
            f"{MINIMO}. Abaixo disso os grupos dizem mais sobre o sorteio do que "
            "sobre a literatura.")
        return base

    vetores, vocabulario = _vetores(itens)
    if len(vocabulario) < K_MAXIMO:
        base["aviso"] = ("os resumos não trazem vocabulário suficiente para "
                         "agrupar — o acervo veio sem resumo?")
        return base

    teto = min(K_MAXIMO, len(itens) // 3)
    candidatos = []
    for tentativa in ([k] if k else range(2, max(3, teto + 1))):
        rotulos = _kmedias(vetores, tentativa)
        if len(set(rotulos)) < 2:
            continue
        candidatos.append((tentativa, rotulos, _silhueta(vetores, rotulos)))
    melhor = _melhor_k(candidatos)
    if melhor is None:
        base["aviso"] = "não foi possível formar dois grupos distintos."
        return base

    escolhido, rotulos, nota = melhor
    grupos = []
    for j in range(escolhido):
        membros = [i for i, r in zip(itens, rotulos) if r == j]
        if not membros:
            continue
        vetores_do_grupo = [v for v, r in zip(vetores, rotulos) if r == j]
        centro = _centro(vetores_do_grupo)
        termos = sorted(centro.items(), key=lambda x: (-x[1], x[0]))[:TERMOS_POR_GRUPO]
        anos = sorted(i["year"] for i in membros if i["year"])
        grupos.append({
            "n": len(membros),
            "termos": [t for t, _ in termos],
            "ano_de": anos[0] if anos else None,
            "ano_ate": anos[-1] if anos else None,
            # A ponte com o que o laboratorio declarou: o grupo cai todo
            # dentro de um segmento, ou atravessa varios?
            "segmentos": [{"segmento": nome or "sem segmento", "n": quantos}
                          for nome, quantos in sorted(
                              Counter(i["segmento"] for i in membros).items(),
                              key=lambda x: (-x[1], str(x[0])))],
            "exemplos": [{"title": i["title"], "year": i["year"], "doi": i["doi"]}
                         for i in membros[:5]],
        })
    grupos.sort(key=lambda g: (-g["n"], g["termos"][0] if g["termos"] else ""))

    base.update({"k": len(grupos), "grupos": grupos, "silhueta": round(nota, 3),
                 "leitura": _ler_silhueta(nota),
                 "termos_usados": len(vocabulario)})
    return base
