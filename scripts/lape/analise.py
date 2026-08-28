"""O comportamento das variaveis ao longo do tempo: sinal, ruido e curvatura.

Contagem anual de artigos e uma serie curta e barulhenta. Um ano com tres
publicacoes e outro com uma nao significam "queda de 67%" -- significam
que uma banca atrasou e dois artigos sairam em janeiro em vez de dezembro.
Ler a serie crua leva a diagnosticos falsos, e e o que quase toda
bibliometria faz.

Por isso aqui a serie passa por dois filtros, nessa ordem:

  mediana movel   descarta o pico isolado sem deslocar o resto -- e o
                  filtro robusto: um valor absurdo nao contamina a media
  suavizacao      media ponderada dos vizinhos, que deixa a forma da
                  curva e tira o serrilhado

O que sobra da subtracao (`bruto - suave`) e o RUIDO, e ele e devolvido
junto: uma variavel cujo ruido e maior que o sinal nao tem tendencia
nenhuma para interpretar, por mais bonita que a linha fique.

Sobre "derivada": a serie e anual e discreta, entao o que se calcula sao
DIFERENCAS FINITAS centrais -- velocidade (artigos por ano) e aceleracao
(mudanca da velocidade). Chamar isso de derivada sem dizer que o passo e
de um ano seria rigor de fachada. O ponto de inflexao e onde a aceleracao
troca de sinal: e ali que a curva para de abrir e comeca a fechar, que e
o momento que interessa diagnosticar.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any, Iterable

from .db import Database

JANELA_PADRAO_ANOS = 20
MIN_PONTOS = 4          # abaixo disso nao se fala em tendencia
# Anos DISTINTOS com producao. E a checagem que importa de verdade: uma
# serie de vinte anos em que so um ano tem artigo nao e uma tendencia --
# e um ponto. Sem esta guarda, a suavizacao transforma o ponto numa
# ladeira bonita e o painel anuncia "subindo, confiavel" sobre nada.
MIN_ANOS_COM_DADO = 3
RUIDO_ALTO = 0.8        # ruido acima disso: a serie nao sustenta leitura


# ----------------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------------
def mediana_movel(valores: list[float], janela: int = 3) -> list[float]:
    """Filtro robusto: um pico isolado nao arrasta a curva junto."""
    if len(valores) < janela:
        return list(valores)
    meio = janela // 2
    saida = []
    for i in range(len(valores)):
        esquerda, direita = max(0, i - meio), min(len(valores), i + meio + 1)
        vizinhos = sorted(valores[esquerda:direita])
        saida.append(vizinhos[len(vizinhos) // 2])
    return saida


def suavizar(valores: list[float], pesos: tuple[float, ...] = (1, 2, 1)) -> list[float]:
    """Media ponderada dos vizinhos. Mantem a forma, tira o serrilhado."""
    if len(valores) < 3:
        return list(valores)
    meio = len(pesos) // 2
    total = sum(pesos)
    saida = []
    for i in range(len(valores)):
        acumulado, usado = 0.0, 0.0
        for k, peso in enumerate(pesos):
            j = i + k - meio
            if 0 <= j < len(valores):
                acumulado += valores[j] * peso
                usado += peso
        saida.append(acumulado / (usado or total))
    return saida


def sinal_e_ruido(valores: list[float]) -> dict[str, Any]:
    """Separa o que a serie diz do que ela apenas balanca."""
    anos_com_dado = sum(1 for v in valores if v)
    robusto = mediana_movel([float(v) for v in valores])
    suave = suavizar(robusto)
    ruido = [b - s for b, s in zip(valores, suave)]
    amplitude = (max(suave) - min(suave)) if suave else 0.0
    desvio = _desvio(ruido)
    # razao ruido/sinal: quanto o balanco pesa diante da variacao real
    razao = (desvio / amplitude) if amplitude > 1e-9 else (1.0 if desvio else 0.0)
    bastante = anos_com_dado >= MIN_ANOS_COM_DADO and len(valores) >= MIN_PONTOS
    return {"suave": [round(v, 3) for v in suave],
            "ruido": [round(v, 3) for v in ruido],
            "desvio_do_ruido": round(desvio, 3),
            "razao_ruido": round(razao, 3) if bastante else None,
            "anos_com_dado": anos_com_dado,
            "confiavel": bastante and razao < RUIDO_ALTO,
            "porque": (None if bastante else
                       f"{anos_com_dado} ano(s) com produção — "
                       f"são precisos {MIN_ANOS_COM_DADO} para falar em curva")}


def _desvio(valores: Iterable[float]) -> float:
    dados = list(valores)
    if len(dados) < 2:
        return 0.0
    media = sum(dados) / len(dados)
    return math.sqrt(sum((v - media) ** 2 for v in dados) / (len(dados) - 1))


# ----------------------------------------------------------------------
# Diferencas finitas
# ----------------------------------------------------------------------
def velocidade(suave: list[float]) -> list[float]:
    """Diferenca central: quanto a curva sobe por ano, naquele ponto."""
    n = len(suave)
    if n < 2:
        return [0.0] * n
    saida = []
    for i in range(n):
        if i == 0:
            saida.append(suave[1] - suave[0])
        elif i == n - 1:
            saida.append(suave[-1] - suave[-2])
        else:
            saida.append((suave[i + 1] - suave[i - 1]) / 2)
    return [round(v, 3) for v in saida]


def aceleracao(suave: list[float]) -> list[float]:
    """Segunda diferenca: a curva esta abrindo ou fechando?"""
    n = len(suave)
    if n < 3:
        return [0.0] * n
    saida = [0.0]
    for i in range(1, n - 1):
        saida.append(suave[i + 1] - 2 * suave[i] + suave[i - 1])
    saida.append(0.0)
    return [round(v, 3) for v in saida]


def inflexoes(anos: list[int], suave: list[float]) -> list[dict[str, Any]]:
    """Onde a aceleracao troca de sinal.

    E o ponto que interessa diagnosticar: nao e o pico (ali a curva ja
    virou), e o momento anterior, em que ela para de abrir e comeca a
    fechar. Numa linha de pesquisa, e o ano em que o assunto deixou de
    crescer -- e quase sempre passa despercebido porque o numero ainda
    esta subindo.
    """
    acel = aceleracao(suave)
    vel = velocidade(suave)
    achados = []
    for i in range(1, len(acel) - 1):
        anterior, atual = acel[i - 1], acel[i]
        if anterior == 0 or atual == 0 or (anterior > 0) == (atual > 0):
            continue
        # Quatro casos, e nao dois: a curvatura sozinha nao diz o que
        # aconteceu -- e preciso saber se a curva estava subindo ou
        # caindo naquele ponto. Sem isso, "voltou a abrir" acaba escrito
        # sobre uma queda que apenas desacelerou, que e o contrario.
        subindo = vel[i] > 0
        fechando = anterior > 0        # aceleracao positiva virando negativa
        if fechando and subindo:
            tipo, leitura = "desaceleração", "ainda subia, mas passou a subir menos"
        elif fechando and not subindo:
            tipo, leitura = "aprofundamento", "já caía, e passou a cair mais rápido"
        elif not fechando and not subindo:
            tipo, leitura = "alívio", "ainda caía, mas passou a cair menos"
        else:
            tipo, leitura = "retomada", "voltou a acelerar"
        achados.append({"ano": anos[i], "valor": round(suave[i], 2),
                        "tipo": tipo, "leitura": leitura,
                        "velocidade": vel[i]})
    return achados


def cruzamentos(a: dict[str, Any], b: dict[str, Any],
                anos: list[int]) -> list[dict[str, Any]]:
    """Em que ano uma curva passou a outra, e quem passou quem."""
    sa, sb = a["suave"], b["suave"]
    achados = []
    for i in range(1, min(len(sa), len(sb))):
        antes, agora = sa[i - 1] - sb[i - 1], sa[i] - sb[i]
        if antes == 0 or agora == 0 or (antes > 0) == (agora > 0):
            continue
        # interpola o ano do encontro entre os dois pontos
        fracao = abs(antes) / (abs(antes) + abs(agora))
        achados.append({
            "ano": anos[i - 1] + round(fracao, 2),
            "ano_cheio": anos[i] if fracao > 0.5 else anos[i - 1],
            "quem_subiu": a["label"] if agora > 0 else b["label"],
            "quem_desceu": b["label"] if agora > 0 else a["label"],
            "a": a["code"], "b": b["code"],
        })
    return achados


def tendencia(suave: list[float], vel: list[float], anos_com_dado: int = 0) -> str:
    """Sobe, cai ou fica -- e "nao da para dizer", que e resposta legitima.

    Ha uma tentacao forte de sempre devolver uma das tres primeiras. Ela e
    o que faz painel bonito mentir: com um unico ano de producao, qualquer
    algoritmo de tendencia responde "subindo", e quem le acredita.

    O criterio compara BLOCOS -- a media dos ultimos tres anos contra a
    dos tres anteriores -- e nao a velocidade no ultimo ponto. A diferenca
    importa: a suavizacao amortece as pontas da serie, entao a velocidade
    no ultimo ano sai sempre menor do que a subida real, e uma linha
    claramente em alta era classificada como "estavel". Bloco contra
    bloco e tambem o que um leitor faz de olho.
    """
    if anos_com_dado < MIN_ANOS_COM_DADO or len(suave) < MIN_PONTOS:
        return "sem série suficiente"
    fatia = max(2, min(3, len(suave) // 3))
    recente = sum(suave[-fatia:]) / fatia
    anterior = sum(suave[-2 * fatia:-fatia]) / fatia
    base = max(anterior, sum(suave) / len(suave), 0.5)
    variacao = (recente - anterior) / base
    if variacao > 0.15:
        return "subindo"
    if variacao < -0.15:
        return "caindo"
    return "estável"


def crescimento_anual(suave: list[float]) -> float | None:
    """Taxa media de crescimento no periodo, em porcentagem ao ano."""
    inicio = next((v for v in suave if v > 0), 0)
    fim = suave[-1] if suave else 0
    anos = len(suave) - 1
    if inicio <= 0 or fim <= 0 or anos < 1:
        return None
    return round(((fim / inicio) ** (1 / anos) - 1) * 100, 1)


# ----------------------------------------------------------------------
# O panorama
# ----------------------------------------------------------------------
def _ano_do_artigo(linha: dict[str, Any]) -> int | None:
    """O ano que representa o artigo: publicacao, aceite, submissao, inicio.

    Um laboratorio tem mais artigo em andamento do que publicado, e a
    serie so de publicados esconde o que esta sendo feito agora. A ordem
    aqui vai do fato mais definitivo ao mais provisorio.
    """
    if linha.get("year_published"):
        return int(linha["year_published"])
    for campo in ("published_on", "accepted_on", "first_submission_on", "started_on"):
        valor = linha.get(campo)
        if valor and str(valor)[:4].isdigit():
            return int(str(valor)[:4])
    return None


def panorama(db: Database, desde: int | None = None,
             ate: int | None = None) -> dict[str, Any]:
    """Tudo o que o painel precisa, calculado do banco.

    A janela padrao sao os ultimos 20 anos. E um recorte de metodo, nao de
    gosto: producao de mais de 20 anos atras foi feita com outra equipe,
    outro financiamento e outra pergunta, e misturar tudo numa curva so
    faz a curva nao significar nada.
    """
    hoje = date.today().year
    ate = ate or hoje
    desde = desde or (ate - JANELA_PADRAO_ANOS + 1)
    anos = list(range(desde, ate + 1))

    artigos = db.dicts(
        "SELECT id, title, status, year_published, published_on, accepted_on,"
        "       first_submission_on, started_on, journal, qualis, doi,"
        "       wos_citations, scopus_citations, openalex_citations"
        "  FROM v_articles_full")
    for artigo in artigos:
        artigo["ano"] = _ano_do_artigo(artigo)

    ligacoes = db.dicts(
        "SELECT av.article_id, v.code, v.label, v.grupo, v.icone"
        "  FROM article_variables av JOIN variables v ON v.id = av.variable_id")
    por_artigo: dict[int, list[dict]] = {}
    for ligacao in ligacoes:
        por_artigo.setdefault(ligacao["article_id"], []).append(ligacao)

    catalogo: dict[str, dict[str, Any]] = {}
    for ligacao in ligacoes:
        catalogo.setdefault(ligacao["code"], {
            "code": ligacao["code"], "label": ligacao["label"],
            "grupo": ligacao["grupo"], "icone": ligacao["icone"], "artigos": []})
    for artigo in artigos:
        for ligacao in por_artigo.get(artigo["id"], []):
            catalogo[ligacao["code"]]["artigos"].append(artigo)

    variaveis = []
    for item in catalogo.values():
        dentro = [a for a in item["artigos"] if a["ano"] and desde <= a["ano"] <= ate]
        serie = [sum(1 for a in dentro if a["ano"] == ano) for ano in anos]
        filtrado = sinal_e_ruido(serie)
        suave = filtrado["suave"]
        vel = velocidade(suave)
        acumulado, total = [], 0
        for valor in serie:
            total += valor
            acumulado.append(total)
        anos_com = [a["ano"] for a in dentro]
        variaveis.append({
            **{k: item[k] for k in ("code", "label", "grupo", "icone")},
            "total": len(dentro), "total_geral": len(item["artigos"]),
            "serie": serie, "acumulado": acumulado,
            "velocidade": vel, "aceleracao": aceleracao(suave),
            "inflexoes": inflexoes(anos, suave) if filtrado["confiavel"] else [],
            "tendencia": tendencia(suave, vel, filtrado["anos_com_dado"]),
            "crescimento_ao_ano": (crescimento_anual(suave)
                                   if filtrado["confiavel"] else None),
            "primeiro_ano": min(anos_com) if anos_com else None,
            "ultimo_ano": max(anos_com) if anos_com else None,
            "pico": {"ano": anos[serie.index(max(serie))], "valor": max(serie)}
                    if serie and max(serie) else None,
            **filtrado,
        })
    variaveis.sort(key=lambda v: (-v["total"], v["label"]))

    # cruzamentos entre as variaveis mais fortes: comparar as 20 daria 190
    # pares, e nenhum leitor olha 190 cruzamentos
    fortes = [v for v in variaveis if v["total"] >= 2][:8]
    encontros = []
    for i, a in enumerate(fortes):
        for b in fortes[i + 1:]:
            encontros.extend(cruzamentos(a, b, anos))
    encontros.sort(key=lambda x: -x["ano"])

    return {
        "janela": {"de": desde, "ate": ate, "anos": anos,
                   "corte": f"últimos {ate - desde + 1} anos"},
        "variaveis": variaveis,
        "cruzamentos": encontros[:24],
        "rede": rede(db),
        "paises": paises(db),
        "sem_ano": sum(1 for a in artigos if a["ano"] is None),
        "total_artigos": len(artigos),
        "no_recorte": sum(1 for a in artigos if a["ano"] and desde <= a["ano"] <= ate),
    }


def paises(db: Database) -> dict[str, Any]:
    """De onde vem a producao: o pais da instituicao de cada coautor.

    O artigo nao carrega pais -- quem carrega e a instituicao de quem
    assina. Contar por artigo com pelo menos um autor daquele pais e a
    leitura correta: um artigo Brasil-Noruega conta para os dois, porque
    foi produzido nos dois. Somar por autor inflaria o pais que mandou
    mais gente.
    """
    linhas = db.dicts(
        "SELECT DISTINCT aa.article_id, i.name AS instituicao, i.country,"
        "       i.latitude, i.longitude"
        "  FROM article_authors aa"
        "  JOIN members m ON m.id = aa.member_id"
        "  JOIN institutions i ON i.id = m.institution_id"
        " WHERE i.country IS NOT NULL")
    por_pais: dict[str, dict[str, Any]] = {}
    for linha in linhas:
        item = por_pais.setdefault(linha["country"], {
            "pais": linha["country"], "artigos": set(), "instituicoes": set(),
            "latitude": linha["latitude"], "longitude": linha["longitude"]})
        item["artigos"].add(linha["article_id"])
        item["instituicoes"].add(linha["instituicao"])
        if item["latitude"] is None and linha["latitude"] is not None:
            item["latitude"], item["longitude"] = linha["latitude"], linha["longitude"]

    from . import variaveis

    saida = []
    for item in por_pais.values():
        if item["latitude"] is None:
            achado = variaveis.coordenadas(item["pais"])
            if achado:
                item["latitude"], item["longitude"] = achado
        saida.append({"pais": item["pais"], "n": len(item["artigos"]),
                      "instituicoes": sorted(item["instituicoes"]),
                      "latitude": item["latitude"], "longitude": item["longitude"]})
    saida.sort(key=lambda x: -x["n"])
    return {"top": saida[:5], "todos": saida,
            "com_coordenada": sum(1 for x in saida if x["latitude"] is not None)}


def rede(db: Database) -> dict[str, Any]:
    """Quais variaveis aparecem no mesmo artigo, e com que forca.

    A contagem crua favorece o que e comum: fibromialgia aparece com tudo
    porque aparece em tudo. O Jaccard corrige isso -- ele pergunta que
    fracao das aparicoes das duas e compartilhada, e e por ele que se ve
    o par que anda junto de verdade.
    """
    por_variavel: dict[str, set[int]] = {}
    rotulos: dict[str, dict[str, Any]] = {}
    for linha in db.dicts(
            "SELECT av.article_id, v.code, v.label, v.grupo, v.icone"
            "  FROM article_variables av JOIN variables v ON v.id = av.variable_id"):
        por_variavel.setdefault(linha["code"], set()).add(linha["article_id"])
        rotulos[linha["code"]] = linha

    codigos = sorted(por_variavel, key=lambda c: -len(por_variavel[c]))
    arestas = []
    for i, a in enumerate(codigos):
        for b in codigos[i + 1:]:
            juntos = por_variavel[a] & por_variavel[b]
            if not juntos:
                continue
            uniao = por_variavel[a] | por_variavel[b]
            arestas.append({
                "a": a, "b": b, "rotulo_a": rotulos[a]["label"],
                "rotulo_b": rotulos[b]["label"], "n": len(juntos),
                "jaccard": round(len(juntos) / len(uniao), 3),
            })
    arestas.sort(key=lambda x: (-x["n"], -x["jaccard"]))
    return {
        "nos": [{"code": c, "label": rotulos[c]["label"], "grupo": rotulos[c]["grupo"],
                 "icone": rotulos[c]["icone"], "n": len(por_variavel[c])}
                for c in codigos],
        "arestas": arestas,
    }
