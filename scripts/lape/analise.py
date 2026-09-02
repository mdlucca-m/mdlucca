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


# ----------------------------------------------------------------------
# Incidencia e prevalencia da producao
# ----------------------------------------------------------------------
# A leitura e a da epidemiologia, e ela cabe porque a pergunta e a mesma:
#
#   INCIDENCIA -- casos NOVOS num periodo, sobre quem estava em risco de
#   virar caso. Aceite e rejeicao so podem acontecer com artigo que esta
#   em avaliacao; publicacao so com artigo ja aceito. Contar aceites sobre
#   o acervo inteiro daria uma taxa que cai sozinha toda vez que alguem
#   comeca um artigo novo -- e nao foi isso que aconteceu.
#
#   PREVALENCIA -- a fatia da carteira em cada situacao NUM INSTANTE. Nao
#   e o que aconteceu no ano, e o que esta parado ali no dia 31.
#
# Denominador pequeno faz taxa grande. Abaixo de MIN_EM_RISCO a taxa sai,
# mas marcada: um aceite sobre dois artigos e "50%" e nao quer dizer nada.
MIN_EM_RISCO = 3

ESTADOS = ("em produção", "em avaliação", "aceito", "publicado",
           "rejeitado", "arquivado")


def _dia(valor: Any) -> str | None:
    texto = str(valor or "")[:10]
    return texto if len(texto) == 10 else None


def estado_em(artigo: dict[str, Any], ate_dia: str) -> str | None:
    """Em que situacao o artigo estava naquele dia -- ou None se nem existia.

    Reconstruido das datas, e nao do `status` de hoje: o status atual diz
    onde o artigo esta agora, e a prevalencia de 2019 precisa saber onde
    ele estava em 2019.
    """
    saiu = artigo.get("saiu_em")
    if saiu and saiu <= ate_dia:
        return artigo.get("saiu_como")
    for campo, estado in (("published_on", "publicado"), ("accepted_on", "aceito"),
                          ("first_submission_on", "em avaliação"),
                          ("started_on", "em produção")):
        dia = _dia(artigo.get(campo))
        if dia and dia <= ate_dia:
            return estado
    return None


def _artigos_para_estado(db: Database) -> list[dict[str, Any]]:
    """Os artigos com as datas, e com a data em que sairam do funil.

    Rejeitado e arquivado nao estao na linha do tempo das datas -- estao
    no status. A data em que isso aconteceu vem da ultima decisao
    registrada; sem decisao nenhuma, nao da para dizer quando, e o artigo
    segue a leitura das datas.
    """
    artigos = db.dicts(
        "SELECT id, status, started_on, first_submission_on, accepted_on,"
        "       published_on FROM articles")
    ultima = {linha["article_id"]: linha["quando"] for linha in db.dicts(
        "SELECT article_id, MAX(decision_on) AS quando FROM submissions"
        " WHERE decision_on IS NOT NULL GROUP BY article_id")}
    for artigo in artigos:
        artigo["saiu_em"] = None
        artigo["saiu_como"] = None
        if artigo["status"] in ("rejeitado", "arquivado"):
            artigo["saiu_em"] = _dia(ultima.get(artigo["id"]))
            artigo["saiu_como"] = artigo["status"]
    return artigos


def prevalencia(db: Database, anos: list[int]) -> dict[str, Any]:
    """A fatia da carteira em cada situacao, no ultimo dia de cada ano."""
    artigos = _artigos_para_estado(db)
    serie = []
    for ano in anos:
        fim = f"{ano}-12-31"
        conta = {estado: 0 for estado in ESTADOS}
        for artigo in artigos:
            estado = estado_em(artigo, fim)
            if estado:
                conta[estado] += 1
        total = sum(conta.values())
        serie.append({
            "ano": ano, "total": total, "estados": conta,
            "fracao": {e: (round(n / total * 100, 1) if total else 0)
                       for e, n in conta.items()},
        })
    return {"anos": anos, "serie": serie, "estados": list(ESTADOS),
            "hoje": serie[-1] if serie else None}


def incidencia(db: Database, anos: list[int]) -> dict[str, Any]:
    """Casos novos por ano, cada um sobre quem estava em risco de virar caso."""
    artigos = _artigos_para_estado(db)
    linhas = []
    for ano in anos:
        inicio, fim = f"{ano}-01-01", f"{ano}-12-31"
        vespera = f"{ano - 1}-12-31"
        em_avaliacao = sum(1 for a in artigos if estado_em(a, vespera) == "em avaliação")
        aceitos_antes = sum(1 for a in artigos if estado_em(a, vespera) == "aceito")

        def no_ano(campo: str) -> int:
            return sum(1 for a in artigos
                       if (_dia(a.get(campo)) or "") >= inicio
                       and (_dia(a.get(campo)) or "") <= fim)

        novos_aceitos = no_ano("accepted_on")
        novos_publicados = no_ano("published_on")
        novos_submetidos = no_ano("first_submission_on")
        rejeitados = int(db.scalar(
            "SELECT COUNT(*) FROM submissions"
            " WHERE decision = 'rejeitado' AND decision_on BETWEEN ? AND ?",
            (inicio, fim)) or 0)

        # Em risco de aceite ou rejeicao: o que estava em avaliacao na
        # virada, mais o que entrou em avaliacao durante o ano.
        risco_decisao = em_avaliacao + novos_submetidos
        risco_publicacao = aceitos_antes + novos_aceitos

        def taxa(casos: int, risco: int) -> float | None:
            return round(casos / risco * 100, 1) if risco else None

        linhas.append({
            "ano": ano,
            "em_avaliacao_no_inicio": em_avaliacao,
            "submetidos": novos_submetidos,
            "aceitos": novos_aceitos,
            "rejeitados": rejeitados,
            "publicados": novos_publicados,
            "em_risco_decisao": risco_decisao,
            "em_risco_publicacao": risco_publicacao,
            "taxa_aceite": taxa(novos_aceitos, risco_decisao),
            "taxa_rejeicao": taxa(rejeitados, risco_decisao),
            "taxa_publicacao": taxa(novos_publicados, risco_publicacao),
            "confiavel": risco_decisao >= MIN_EM_RISCO,
            "porque": (None if risco_decisao >= MIN_EM_RISCO else
                       f"{risco_decisao} artigo(s) em risco no ano — "
                       "a taxa existe, mas oscila com um caso só"),
        })
    return {"anos": anos, "serie": linhas, "minimo_em_risco": MIN_EM_RISCO}


# ----------------------------------------------------------------------
# Triangulacao: a quem se aplica, o que se faz, o que se mede
# ----------------------------------------------------------------------
# Um artigo de intervencao responde tres perguntas, e so responde de
# verdade quando responde as tres: EM QUEM (condicao clinica), COM O QUE
# (intervencao) e MEDINDO O QUE (desfecho). E o triangulo de PICO, e o
# vocabulario do laboratorio ja esta organizado nesses grupos.
#
# O valor de olhar assim nao e contar cruzamentos bonitos -- e ver a
# PERNA QUE FALTA. Artigo com condicao e intervencao mas sem desfecho
# declarado e um artigo que diz o que fez e nao diz o que mediu.
PERNAS = {
    "aplicacao": "Condição clínica",
    "intervencao": "Intervenção",
    "desfecho": "Desfecho psicológico",
}


def triangulacao(db: Database, minimo: int = 1) -> dict[str, Any]:
    """Os trios condicao x intervencao x desfecho, e o que falta em cada artigo."""
    linhas = db.dicts(
        "SELECT av.article_id, v.code, v.label, v.grupo, a.title,"
        "       a.year_published, a.published_on, a.started_on,"
        "       a.first_submission_on"
        "  FROM article_variables av"
        "  JOIN variables v ON v.id = av.variable_id"
        "  JOIN articles a ON a.id = av.article_id")
    por_artigo: dict[int, dict[str, Any]] = {}
    for linha in linhas:
        item = por_artigo.setdefault(linha["article_id"], {
            "id": linha["article_id"], "titulo": linha["title"],
            "ano": _ano_do_artigo(linha),
            "pernas": {chave: [] for chave in PERNAS}})
        for chave, grupo in PERNAS.items():
            if linha["grupo"] == grupo:
                item["pernas"][chave].append(linha["label"])

    trios: dict[tuple[str, str, str], dict[str, Any]] = {}
    completos, faltando = [], {chave: [] for chave in PERNAS}
    for item in por_artigo.values():
        cheias = [c for c in PERNAS if item["pernas"][c]]
        if len(cheias) == len(PERNAS):
            completos.append(item)
            for aplicacao in item["pernas"]["aplicacao"]:
                for intervencao in item["pernas"]["intervencao"]:
                    for desfecho in item["pernas"]["desfecho"]:
                        chave = (aplicacao, intervencao, desfecho)
                        alvo = trios.setdefault(chave, {
                            "aplicacao": aplicacao, "intervencao": intervencao,
                            "desfecho": desfecho, "artigos": []})
                        if item["id"] not in [a["id"] for a in alvo["artigos"]]:
                            alvo["artigos"].append(
                                {"id": item["id"], "titulo": item["titulo"],
                                 "ano": item["ano"]})
        else:
            for chave in PERNAS:
                if not item["pernas"][chave]:
                    faltando[chave].append(
                        {"id": item["id"], "titulo": item["titulo"],
                         "tem": {c: item["pernas"][c] for c in PERNAS
                                 if item["pernas"][c]}})

    lista = sorted(trios.values(), key=lambda t: (-len(t["artigos"]),
                                                  t["aplicacao"], t["intervencao"]))
    lista = [dict(t, n=len(t["artigos"])) for t in lista if len(t["artigos"]) >= minimo]
    return {
        "trios": lista,
        "completos": len(completos),
        "com_variavel": len(por_artigo),
        "faltando": faltando,
        "pernas": PERNAS,
        "matrizes": [
            _matriz(por_artigo, "aplicacao", "intervencao"),
            _matriz(por_artigo, "intervencao", "desfecho"),
        ],
    }


def _matriz(por_artigo: dict[int, dict[str, Any]], eixo_x: str,
            eixo_y: str) -> dict[str, Any]:
    """Quantos artigos cruzam cada par -- a face do triangulo, achatada."""
    conta: dict[tuple[str, str], int] = {}
    colunas: dict[str, int] = {}
    linhas_: dict[str, int] = {}
    for item in por_artigo.values():
        for x in item["pernas"][eixo_x]:
            for y in item["pernas"][eixo_y]:
                conta[(x, y)] = conta.get((x, y), 0) + 1
                colunas[x] = colunas.get(x, 0) + 1
                linhas_[y] = linhas_.get(y, 0) + 1
    ordem_x = sorted(colunas, key=lambda k: -colunas[k])
    ordem_y = sorted(linhas_, key=lambda k: -linhas_[k])
    return {
        "eixo_x": PERNAS[eixo_x], "eixo_y": PERNAS[eixo_y],
        "colunas": ordem_x, "linhas": ordem_y,
        "celulas": [{"x": x, "y": y, "n": conta[(x, y)]}
                    for (x, y) in sorted(conta, key=lambda k: -conta[k])],
    }


# ----------------------------------------------------------------------
# Projetos, com a extensao separada
# ----------------------------------------------------------------------
# Extensao nao e pesquisa com outro nome: tem outro publico, outra
# entrega e outra prestacao de contas. Misturar as duas numa lista so faz
# a extensao sumir -- ela e sempre a minoria, e some primeiro.
def e_extensao(projeto: dict[str, Any]) -> bool:
    """Reconhece extensao pelo tipo, e pelo nome quando o tipo esta vazio."""
    from .util import norm_key

    tipo = norm_key(projeto.get("kind") or "")
    if "extensao" in tipo or "extension" in tipo:
        return True
    if tipo:
        return False
    # Sem tipo declarado, o nome e o unico indicio -- e e melhor que nada,
    # desde que o painel diga que foi assim que se descobriu.
    return "extensao" in norm_key(projeto.get("name") or "")


def projetos(db: Database) -> dict[str, Any]:
    """Os projetos, separados por tipo, com equipe, periodo e producao."""
    linhas = db.dicts(
        "SELECT p.*, rl.name AS linha,"
        "       (SELECT COUNT(*) FROM project_members pm WHERE pm.project_id = p.id) AS pessoas,"
        "       (SELECT COUNT(*) FROM project_articles pa WHERE pa.project_id = p.id) AS artigos"
        "  FROM projects p"
        "  LEFT JOIN research_lines rl ON rl.id = p.research_line_id"
        " ORDER BY COALESCE(p.started_on, '') DESC, p.name")
    equipes: dict[int, list[str]] = {}
    for linha in db.dicts(
            "SELECT pm.project_id, m.full_name, pm.role"
            "  FROM project_members pm JOIN members m ON m.id = pm.member_id"
            " ORDER BY m.full_name"):
        equipes.setdefault(linha["project_id"], []).append(
            linha["full_name"] + (f" ({linha['role']})" if linha["role"] else ""))
    for projeto in linhas:
        projeto["extensao"] = e_extensao(projeto)
        projeto["equipe"] = equipes.get(projeto["id"], [])
        projeto["tipo_deduzido"] = projeto["extensao"] and not (projeto.get("kind") or "")
    extensao = [p for p in linhas if p["extensao"]]
    return {
        "todos": linhas,
        "extensao": extensao,
        "pesquisa": [p for p in linhas if not p["extensao"]],
        "em_andamento": [p for p in extensao if p["status"] == "em_andamento"],
        "pessoas_alcancadas": sum(p["pessoas"] for p in extensao),
    }


# ----------------------------------------------------------------------
# Raio-X: varias medidas analiticas, cada uma com a sua base a vista
# ----------------------------------------------------------------------
# Um indicador sozinho e um numero; varios indicadores sem a base sao
# varios numeros. O que faz este bloco valer e cada medida vir com o N
# que a sustenta e com a leitura em portugues -- "2,8 variaveis por
# artigo" nao diz nada a quem nao sabe que acima de 2 a producao e
# combinatoria.
#
# Medida sem base suficiente NAO sai com um valor pequeno: sai dizendo
# que nao da para dizer. Uma mediana de dois artigos e o valor do meio
# de dois artigos, e chamar aquilo de mediana e emprestar autoridade que
# o numero nao tem.
MIN_BASE = 3


def _mediana(valores: list[float]) -> float | None:
    if not valores:
        return None
    ordenados = sorted(valores)
    meio = len(ordenados) // 2
    if len(ordenados) % 2:
        return float(ordenados[meio])
    return (ordenados[meio - 1] + ordenados[meio]) / 2


def _dias(de: Any, ate: Any) -> int | None:
    """Dias entre duas datas do cadastro, ou None se falta alguma."""
    try:
        inicio = date.fromisoformat(str(de)[:10])
        fim = date.fromisoformat(str(ate)[:10])
    except (TypeError, ValueError):
        return None
    return (fim - inicio).days if fim >= inicio else None


def _medida(chave: str, rotulo: str, valor: Any, unidade: str, base: int,
            leitura: str, dica: str = "", icone: str = "achado") -> dict[str, Any]:
    basta = base >= MIN_BASE and valor is not None
    return {
        "chave": chave, "rotulo": rotulo, "icone": icone,
        "valor": valor if basta else None,
        "unidade": unidade, "base": base, "confiavel": basta,
        "leitura": leitura if basta else None,
        "porque": None if basta else (
            f"{base} artigo(s) com este dado — abaixo de {MIN_BASE} o número "
            "diria mais do que se sabe" if valor is not None or base else
            "nenhum artigo tem este dado cadastrado"),
        "dica": dica,
    }


def raio_x(db: Database) -> dict[str, Any]:
    """Um punhado de medidas analiticas, cada uma com a base que a sustenta."""
    artigos = db.dicts(
        # `submission_attempts` e `rejections` sao contados pela view, e
        # nao guardados na tabela -- ler de `articles` daria erro.
        "SELECT id, journal, doi, pmc, open_access, submission_attempts,"
        "       rejections, started_on, first_submission_on, accepted_on,"
        "       published_on FROM v_articles_full")
    total = len(artigos)

    por_artigo: dict[int, int] = {}
    for linha in db.dicts(
            "SELECT article_id, COUNT(*) AS n FROM article_variables"
            " GROUP BY article_id"):
        por_artigo[linha["article_id"]] = linha["n"]
    autores: dict[int, int] = {}
    for linha in db.dicts(
            "SELECT article_id, COUNT(*) AS n FROM article_authors"
            " GROUP BY article_id"):
        autores[linha["article_id"]] = linha["n"]

    medidas = []

    # --- densidade tematica -------------------------------------------
    densidades = list(por_artigo.values())
    medidas.append(_medida(
        "densidade", "Variáveis por artigo",
        round(sum(densidades) / len(densidades), 1) if densidades else None,
        "em média", len(densidades),
        ("acima de 2, a produção é combinatória: o valor está no cruzamento, "
         "não na variável isolada")
        if densidades and sum(densidades) / len(densidades) > 2 else
        "cada artigo trata de um assunto de cada vez",
        "Quantos temas o mesmo artigo toca.", "rede"))

    # --- concentracao --------------------------------------------------
    aparicoes = sorted(db.dicts(
        "SELECT v.label, COUNT(*) AS n FROM article_variables av"
        "  JOIN variables v ON v.id = av.variable_id"
        " GROUP BY v.label ORDER BY n DESC"), key=lambda x: -x["n"])
    soma = sum(x["n"] for x in aparicoes)
    topo3 = sum(x["n"] for x in aparicoes[:3])
    medidas.append(_medida(
        "concentracao", "Concentração nos 3 temas maiores",
        round(topo3 / soma * 100) if soma else None, "% das aparições",
        len(aparicoes),
        ("a produção tem um centro claro — foco quando é escolha, "
         "fragilidade quando é inércia")
        if soma and topo3 / soma > 0.5 else "os temas se distribuem",
        "Quanto do que se estuda cabe em três assuntos.", "alvo"))

    # --- colaboracao ---------------------------------------------------
    equipes = list(autores.values())
    mediana_autores = _mediana([float(x) for x in equipes])
    medidas.append(_medida(
        "colaboracao", "Autores por artigo", mediana_autores, "na mediana",
        len(equipes),
        ("equipes grandes: o artigo é de um grupo, não de uma pessoa")
        if mediana_autores and mediana_autores >= 4 else
        "equipes enxutas",
        "O valor do meio, não a média — um artigo de 20 autores não "
        "desloca a leitura.", "pessoas"))

    # --- alcance -------------------------------------------------------
    revistas = {a["journal"] for a in artigos if a["journal"]}
    medidas.append(_medida(
        "revistas", "Periódicos distintos", len(revistas) or None, "revistas",
        len(revistas),
        f"a produção se espalha por {len(revistas)} veículos"
        if len(revistas) > 1 else "concentrada num veículo só",
        "Onde a produção sai.", "livro"))

    # --- travessia: onde o tempo fica ----------------------------------
    etapas = (("escrita → submissão", "started_on", "first_submission_on"),
              ("submissão → aceite", "first_submission_on", "accepted_on"),
              ("aceite → publicação", "accepted_on", "published_on"))
    travessia = []
    for nome, de, ate in etapas:
        vaos = [d for d in (_dias(a[de], a[ate]) for a in artigos) if d is not None]
        travessia.append({"etapa": nome, "dias": _mediana([float(v) for v in vaos]),
                          "base": len(vaos), "confiavel": len(vaos) >= MIN_BASE})
    medidos = [e for e in travessia if e["confiavel"]]
    gargalo = max(medidos, key=lambda e: e["dias"]) if medidos else None
    medidas.append(_medida(
        "travessia", "Da escrita à publicação",
        _mediana([float(d) for d in (
            _dias(a["started_on"], a["published_on"]) for a in artigos)
            if d is not None]) or None,
        "dias na mediana",
        sum(1 for a in artigos if _dias(a["started_on"], a["published_on"]) is not None),
        f"o maior vão é {gargalo['etapa']}, com {int(gargalo['dias'])} dias"
        if gargalo else "o caminho inteiro, de começar a sair",
        "Quanto tempo o artigo leva do começo à publicação.", "relogio"))

    # --- persistencia --------------------------------------------------
    tentativas = [a["submission_attempts"] for a in artigos
                  if a["submission_attempts"]]
    medidas.append(_medida(
        "tentativas", "Submissões por artigo",
        _mediana([float(x) for x in tentativas]), "na mediana", len(tentativas),
        "mais de uma revista por artigo é o normal da área"
        if tentativas and (_mediana([float(x) for x in tentativas]) or 0) > 1 else
        "aceite na primeira revista",
        "Quantas revistas até sair.", "submissao"))

    # --- abertura ------------------------------------------------------
    com_doi = sum(1 for a in artigos if a["doi"])
    livres = sum(1 for a in artigos if a["pmc"] or a["open_access"])
    medidas.append(_medida(
        "abertura", "Com texto livre",
        round(livres / total * 100) if total and livres else None,
        "% do acervo", total if livres else 0,
        f"{livres} de {total} podem ser lidos sem assinatura",
        "Quanto da produção qualquer pessoa consegue ler.", "baixar"))
    medidas.append(_medida(
        "identificados", "Com DOI cadastrado",
        round(com_doi / total * 100) if total and com_doi else None,
        "% do acervo", total if com_doi else 0,
        f"{total - com_doi} artigo(s) ainda não têm identificador — "
        "sem ele o clique não abre o artigo",
        "O DOI é o que liga o registro ao artigo de verdade.", "conectar"))

    return {
        "medidas": medidas,
        "travessia": travessia,
        "total": total,
        "minimo": MIN_BASE,
        "prontas": sum(1 for m in medidas if m["confiavel"]),
    }


# ----------------------------------------------------------------------
# Dendrograma: que assuntos se agrupam, e a que distancia
# ----------------------------------------------------------------------
# A rede tematica diz quais pares andam juntos. O dendrograma diz outra
# coisa: em que ORDEM os assuntos se juntam, e a que custo. Dois temas
# que se fundem baixo sao o mesmo assunto com dois nomes; dois ramos que
# so se encontram no topo sao duas agendas diferentes no mesmo
# laboratorio -- e isso nao aparece numa lista de pares.
#
# Distancia = 1 - Jaccard sobre os artigos. Ligacao pela media (UPGMA):
# a distancia entre dois grupos e a media das distancias entre os seus
# membros. A ligacao simples encadearia tudo num fio so, e a completa
# quebraria grupos legitimos por causa de um par distante.
MIN_PARA_AGRUPAR = 2


def _conjuntos_de_artigos(db: Database) -> dict[str, dict[str, Any]]:
    conjuntos: dict[str, dict[str, Any]] = {}
    for linha in db.dicts(
            "SELECT v.code, v.label, av.article_id"
            "  FROM article_variables av JOIN variables v ON v.id = av.variable_id"):
        item = conjuntos.setdefault(linha["code"], {
            "code": linha["code"], "label": linha["label"], "artigos": set()})
        item["artigos"].add(linha["article_id"])
    return conjuntos


def _distancia(a: set, b: set) -> float:
    uniao = len(a | b)
    return 1.0 - (len(a & b) / uniao) if uniao else 1.0


def dendrograma(db: Database, minimo_artigos: int = 1) -> dict[str, Any]:
    """Agrupa as variaveis pela producao que compartilham (UPGMA)."""
    conjuntos = {c: v for c, v in _conjuntos_de_artigos(db).items()
                 if len(v["artigos"]) >= minimo_artigos}
    if len(conjuntos) < MIN_PARA_AGRUPAR:
        return {"raiz": None, "folhas": [], "altura_maxima": 0,
                "porque": ("é preciso pelo menos duas variáveis com artigo "
                           "para haver o que agrupar")}

    # Cada folha comeca sendo o seu proprio grupo.
    grupos: list[dict[str, Any]] = [
        {"tipo": "folha", "code": v["code"], "label": v["label"],
         "artigos": set(v["artigos"]), "n": len(v["artigos"]),
         "folhas": 1, "altura": 0.0, "filhos": []}
        for v in sorted(conjuntos.values(), key=lambda x: -len(x["artigos"]))]

    # Matriz de distancias entre as FOLHAS. A ligacao pela media (UPGMA)
    # atualiza essa matriz pela formula de Lance-Williams; medir a
    # distancia entre as unioes dos grupos, que e o atalho obvio, nao e
    # UPGMA e nao e monotonica: da dendrograma com inversao, um pai mais
    # baixo que o proprio filho, o que nao tem leitura possivel.
    dist: dict[tuple[int, int], float] = {}
    for i in range(len(grupos)):
        for j in range(i + 1, len(grupos)):
            dist[(i, j)] = _distancia(grupos[i]["artigos"], grupos[j]["artigos"])
    vivos = list(range(len(grupos)))

    def entre(a: int, b: int) -> float:
        return dist[(a, b)] if a < b else dist[(b, a)]

    while len(vivos) > 1:
        melhor, par = None, None
        for x, a in enumerate(vivos):
            for b in vivos[x + 1:]:
                d = entre(a, b)
                if melhor is None or d < melhor:
                    melhor, par = d, (a, b)
        a, b = par
        ga, gb = grupos[a], grupos[b]
        novo_id = len(grupos)
        grupos.append({
            "tipo": "no", "label": None, "altura": round(melhor, 3),
            "artigos": ga["artigos"] | gb["artigos"],
            "n": len(ga["artigos"] | gb["artigos"]),
            "folhas": ga["folhas"] + gb["folhas"],
            "compartilham": len(ga["artigos"] & gb["artigos"]),
            "filhos": [ga, gb],
        })
        # Lance-Williams para a media: a distancia do grupo novo a cada
        # outro e a media das distancias dos dois que se juntaram,
        # ponderada pelo numero de folhas de cada um.
        peso = ga["folhas"] + gb["folhas"]
        for c in vivos:
            if c in (a, b):
                continue
            media = (ga["folhas"] * entre(a, c) + gb["folhas"] * entre(b, c)) / peso
            dist[(min(c, novo_id), max(c, novo_id))] = media
        vivos = [c for c in vivos if c not in (a, b)] + [novo_id]

    grupos = [grupos[vivos[0]]]

    def limpar(no: dict[str, Any]) -> dict[str, Any]:
        saida = {k: v for k, v in no.items() if k not in ("artigos", "folhas")}
        saida["filhos"] = [limpar(f) for f in no["filhos"]]
        return saida

    raiz = limpar(grupos[0])
    folhas: list[dict[str, Any]] = []

    def andar(no: dict[str, Any]) -> None:
        if no["tipo"] == "folha":
            folhas.append({"code": no["code"], "label": no["label"], "n": no["n"]})
        for f in no["filhos"]:
            andar(f)

    andar(raiz)
    return {"raiz": raiz, "folhas": folhas,
            "altura_maxima": raiz.get("altura", 0), "porque": None}


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
    # A afiliacao que veio com o artigo das bases publicas conta igual: e
    # a mesma pergunta ("de onde saiu isto"), respondida por quem assinou
    # em vez de pelo cadastro. Sem ela o mapa fica vazio ate alguem ligar
    # os dezessete integrantes as suas instituicoes, um por um.
    linhas += db.dicts(
        "SELECT ac.article_id, NULL AS instituicao, ac.country,"
        "       NULL AS latitude, NULL AS longitude"
        "  FROM article_countries ac")
    por_pais: dict[str, dict[str, Any]] = {}
    for linha in linhas:
        item = por_pais.setdefault(linha["country"], {
            "pais": linha["country"], "artigos": set(), "instituicoes": set(),
            "latitude": linha["latitude"], "longitude": linha["longitude"]})
        item["artigos"].add(linha["article_id"])
        if linha["instituicao"]:
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
        # Os ids vao junto porque a tela precisa SEGMENTAR por pais, e nao
        # so colorir: clicar na Italia tem de devolver os artigos da Italia.
        # Sem eles, a unica ponte entre o mapa e a tabela era procurar a
        # palavra "Italia" no titulo -- que nao esta la, e o clique levava
        # a uma tabela vazia sem dizer por que.
        saida.append({"pais": item["pais"], "n": len(item["artigos"]),
                      "artigos": sorted(item["artigos"]),
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


# ----------------------------------------------------------------------
# Sintese e lacunas
# ----------------------------------------------------------------------
def sintese(db: Database, panorama_pronto: dict[str, Any] | None = None) -> dict[str, Any]:
    """O que os numeros dizem, em frases -- nao em mais numeros.

    Um painel que so mostra grafico obriga cada leitor a tirar a propria
    conclusao, e cada um tira uma. Aqui as leituras que o dado sustenta
    saem escritas, com o numero que as sustenta ao lado, para que possam
    ser contestadas.
    """
    p = panorama_pronto or panorama(db)
    variaveis = [v for v in p["variaveis"] if v["total_geral"]]
    total = p["total_artigos"] or 1
    achados: list[dict[str, Any]] = []

    if variaveis:
        maior = variaveis[0]
        achados.append({
            "titulo": "O eixo da casa",
            "texto": f"{maior['label']} aparece em {maior['total_geral']} dos {total} "
                     f"artigos ({maior['total_geral'] * 100 // total}%). É o assunto em "
                     f"torno do qual o resto se organiza.",
            "numero": maior["total_geral"], "icone": maior["icone"],
        })

    # Pareto: quantas variaveis seguram 80% das aparicoes
    aparicoes = sorted((v["total_geral"] for v in variaveis), reverse=True)
    soma, quantas = 0, 0
    alvo = sum(aparicoes) * 0.8
    for valor in aparicoes:
        soma += valor
        quantas += 1
        if soma >= alvo:
            break
    if aparicoes:
        achados.append({
            "titulo": "Concentração temática",
            "texto": f"{quantas} de {len(variaveis)} variáveis concentram 80% das "
                     f"aparições. Concentrar é foco quando é escolha, e fragilidade "
                     f"quando é inércia.",
            "numero": quantas, "icone": "alvo",
        })

    ligacoes = sum(v["total_geral"] for v in variaveis)
    if total:
        media = round(ligacoes / total, 1)
        achados.append({
            "titulo": "Quantas perguntas por artigo",
            "texto": f"Cada artigo do LAPE toca {media} variáveis em média. Acima de 2, "
                     f"a produção é combinatória: o valor está no cruzamento, não na "
                     f"variável isolada.",
            "numero": media, "icone": "rede",
        })

    arestas = p["rede"]["arestas"]
    if arestas:
        forte = arestas[0]
        achados.append({
            "titulo": "O par que anda junto",
            "texto": f"{forte['rotulo_a']} e {forte['rotulo_b']} dividem "
                     f"{forte['n']} artigos (Jaccard {forte['jaccard']}). É a dupla que "
                     f"define a identidade da produção.",
            "numero": forte["n"], "icone": "conectar",
        })

    subindo = [v for v in variaveis if v["tendencia"] == "subindo"]
    caindo = [v for v in variaveis if v["tendencia"] == "caindo"]
    if subindo or caindo:
        achados.append({
            "titulo": "Para onde a produção anda",
            "texto": (f"{len(subindo)} variável(is) em alta e {len(caindo)} em queda "
                      f"no recorte de {p['janela']['corte']}."),
            "numero": len(subindo), "icone": "subida",
        })
    else:
        achados.append({
            "titulo": "Ainda não dá para falar em tendência",
            "texto": "Nenhuma variável tem produção em três anos distintos. A série "
                     "temporal do laboratório está no Lattes da equipe — importá-lo "
                     "abre a história inteira para a análise.",
            "numero": None, "icone": "aviso",
        })

    situacoes = dict(db.conn.execute(
        "SELECT status, COUNT(*) FROM articles GROUP BY 1").fetchall())
    publicados = situacoes.get("publicado", 0)
    achados.append({
        "titulo": "Onde o acervo está",
        "texto": (f"{publicados} publicado(s), "
                  f"{situacoes.get('submetido', 0) + situacoes.get('em_revisao', 0)} "
                  f"em avaliação e {situacoes.get('em_producao', 0)} em escrita."),
        "numero": publicados, "icone": "producao",
    })
    return {"achados": achados, "situacoes": situacoes,
            "janela": p["janela"], "total": p["total_artigos"]}


def lacunas(db: Database, panorama_pronto: dict[str, Any] | None = None) -> dict[str, Any]:
    """O que NAO esta la -- que e mais dificil de ver do que o que esta.

    Um painel mostra a producao. A pergunta que faz um laboratorio andar e
    a outra: o que ficou de fora, o que ficou pela metade, e que ponte
    ninguem atravessou ainda.
    """
    from . import variaveis as vocabulario

    p = panorama_pronto or panorama(db)
    por_codigo = {v["code"]: v for v in p["variaveis"]}
    todas = vocabulario.lista(db)
    achados: list[dict[str, Any]] = []

    nunca = [v for v in todas if v["code"] not in por_codigo]
    if nunca:
        achados.append({
            "tipo": "nunca estudada", "peso": len(nunca), "icone": "explorar",
            "titulo": "Variáveis do vocabulário sem nenhum artigo",
            "texto": "Não é acusação: é o mapa do que o laboratório escolheu não olhar. "
                     "Cada uma é uma pergunta possível.",
            "itens": [{"rotulo": v["label"], "grupo": v["grupo"]} for v in nunca],
        })

    solitarias = [v for v in p["variaveis"] if v["total_geral"] == 1]
    if solitarias:
        achados.append({
            "tipo": "fio solto", "peso": len(solitarias), "icone": "prazo",
            "titulo": "Estudadas uma vez só",
            "texto": "Um artigo isolado não sustenta linha de pesquisa. Ou vira série, "
                     "ou some do currículo do laboratório.",
            "itens": [{"rotulo": v["label"], "grupo": v["grupo"]} for v in solitarias],
        })

    # pontes que ninguem atravessou: duas variaveis fortes que nunca
    # apareceram no mesmo artigo
    fortes = [v for v in p["variaveis"] if v["total_geral"] >= 3]
    juntos = {(a["a"], a["b"]) for a in p["rede"]["arestas"]}
    juntos |= {(b, a) for a, b in juntos}
    pontes = []
    for i, a in enumerate(fortes):
        for b in fortes[i + 1:]:
            if (a["code"], b["code"]) not in juntos:
                pontes.append({"rotulo": f"{a['label']} × {b['label']}",
                               "grupo": f"{a['total_geral']} + {b['total_geral']} artigos"})
    if pontes:
        achados.append({
            "tipo": "ponte não atravessada", "peso": len(pontes), "icone": "conectar",
            "titulo": "Variáveis fortes que nunca se encontraram",
            "texto": "As duas já têm massa crítica na casa, e nenhum artigo as juntou. "
                     "É onde costuma estar o artigo que ainda não foi escrito.",
            "itens": pontes[:12],
        })

    so_em_gaveta = db.dicts(
        "SELECT v.label, COUNT(*) AS n FROM article_variables av"
        "  JOIN variables v ON v.id = av.variable_id"
        "  JOIN articles a ON a.id = av.article_id"
        " GROUP BY v.id"
        " HAVING SUM(CASE WHEN a.status = 'publicado' THEN 1 ELSE 0 END) = 0")
    if so_em_gaveta:
        achados.append({
            "tipo": "sem nada publicado", "peso": len(so_em_gaveta), "icone": "pausa",
            "titulo": "Assunto sem nenhum artigo publicado",
            "texto": "Trabalho feito que ainda não virou registro. Enquanto não sair, "
                     "não existe para quem lê de fora.",
            "itens": [{"rotulo": x["label"], "grupo": f"{x['n']} artigo(s) na gaveta"}
                      for x in so_em_gaveta],
        })

    buracos = []
    for rotulo, sql in (
            ("sem ano de referência",
             "SELECT COUNT(*) FROM articles WHERE year_published IS NULL"
             "   AND published_on IS NULL AND accepted_on IS NULL"
             "   AND first_submission_on IS NULL AND started_on IS NULL"),
            ("sem linha de pesquisa",
             "SELECT COUNT(*) FROM articles WHERE research_line_id IS NULL"),
            ("publicado sem DOI",
             "SELECT COUNT(*) FROM articles WHERE status = 'publicado'"
             "   AND (doi IS NULL OR TRIM(doi) = '')"),
            ("sem nenhuma variável reconhecida",
             "SELECT COUNT(*) FROM articles a WHERE NOT EXISTS"
             "  (SELECT 1 FROM article_variables av WHERE av.article_id = a.id)")):
        quantos = int(db.scalar(sql) or 0)
        if quantos:
            buracos.append({"rotulo": rotulo, "grupo": f"{quantos} artigo(s)"})
    if buracos:
        achados.append({
            "tipo": "buraco no cadastro", "peso": sum(
                int(b["grupo"].split()[0]) for b in buracos), "icone": "aviso",
            "titulo": "O que falta no próprio cadastro",
            "texto": "Análise não conserta dado ausente. Cada linha aqui é um número "
                     "que o painel não pode calcular.",
            "itens": buracos,
        })

    achados.sort(key=lambda x: -x["peso"])
    return {"achados": achados}
