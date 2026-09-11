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
from typing import Any

from . import config
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
BASES = (PUBMED, SCOPUS, WOS)
ROTULO_BASE = {PUBMED: "PubMed", SCOPUS: "Scopus", WOS: "Web of Science"}


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
SO_NA_PUBMED = '"athletes"[MeSH Terms]'

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
        "segmentos": ESPORTES,
    },
)


def query_de(decl: dict[str, Any], segmento_termos: tuple[str, ...] | None = None,
             base: str = PUBMED) -> str:
    """A busca inteira, montada do vocabulario, na sintaxe da base."""
    populacao = frase(decl["populacao"], base)
    if base == PUBMED:
        populacao = f"{SO_NA_PUBMED} OR {populacao}"
    partes = [f"({frase(decl['construto'], base)})", f"({populacao})"]
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
        for base in BASES:
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


THROTTLE = 0.4


# ----------------------------------------------------------------------
# A atualizacao
# ----------------------------------------------------------------------
def atualizar(db: Database, code: str, limite: int = 400,
              bases: tuple[str, ...] | None = None,
              verbose: bool = False) -> dict[str, Any]:
    """Roda as buscas do acervo e recolhe o que ainda nao estava aqui.

    Uma busca falhar nao derruba as outras: a rede cai no meio de quatorze
    modalidades, e perder as treze que ja tinham voltado por causa da
    decima quarta seria trocar um acervo por um erro. O erro fica gravado
    ao lado da busca que falhou, e a tela o mostra.
    """
    from .revisao import chave_de_uniao

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
    resumo = {"biblioteca": titulo, "buscas": 0, "achados": 0, "novos": 0,
              "erros": 0, "sem_chave": [], "por_base": {}, "segmentos": []}

    # Uma chave que falta e uma noticia so, e nao quinze. Antes de rodar as
    # quinze buscas de uma base, pergunta-se pela chave dela: sem isso, a
    # tela mostraria "SCOPUS_API_KEY nao configurada" quinze vezes e a
    # pessoa leria quinze erros onde ha um recado.
    desligadas: dict[str, str] = {}

    for busca in buscas:
        base = busca["base"]
        if base in desligadas:
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
            continue
        except Exception as erro:  # noqa: BLE001 -- uma busca nao derruba as outras
            db.execute("UPDATE biblioteca_busca SET rodada_em = ?, erro = ? WHERE id = ?",
                       (hoje, str(erro)[:300], busca["id"]))
            resumo["erros"] += 1
            if verbose:
                print(f"  ! {base}/{busca['segmento'] or 'geral'}: {erro}")
            continue

        novos = 0
        for registro in registros:
            if _gravar(db, bid, busca["segmento"], registro, chave_de_uniao):
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

    db.execute("UPDATE biblioteca SET atualizada_em = ? WHERE id = ?", (hoje, bid))
    db.conn.commit()
    db.log_ingest("biblioteca", target=code, rows_read=resumo["achados"],
                  rows_written=resumo["novos"],
                  status="ok" if not (resumo["erros"] or desligadas) else "parcial",
                  message=f"{resumo['novos']} novo(s) em {resumo['buscas']} busca(s)")
    return resumo


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
    raise ValueError(f"base desconhecida: {base}")


def _gravar(db: Database, biblioteca_id: int, segmento: str | None,
            registro: dict[str, Any], chave_de_uniao: Any) -> bool:
    """Grava um registro. Devolve True se ele ainda nao estava aqui."""
    from . import variaveis

    chave = chave_de_uniao(registro)
    if not chave:
        return False
    achado = db.dicts(
        "SELECT id, segmento FROM biblioteca_item WHERE biblioteca_id = ? AND chave = ?",
        (biblioteca_id, chave))
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
    db.execute(
        "INSERT INTO biblioteca_item (biblioteca_id, chave, segmento, title, abstract,"
        "        authors, journal, year, doi, pmid, pmc, url, oa_url, paises, base)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (biblioteca_id, chave, segmento, clean_text(registro.get("title")),
         clean_text(registro.get("abstract")),
         "; ".join(registro.get("authors") or []) if isinstance(registro.get("authors"), list)
         else clean_text(registro.get("authors")),
         clean_text(registro.get("journal")), registro.get("year"),
         norm_doi(registro.get("doi")), clean_text(registro.get("pmid")),
         clean_text(registro.get("pmc")), clean_text(registro.get("url")),
         clean_text(registro.get("oa_url")), json.dumps(paises, ensure_ascii=False),
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
            "segmento": segmento, "busca": busca, "pais": pais}


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


def todas(db: Database) -> list[dict[str, Any]]:
    """Os acervos, para a tela listar."""
    return db.dicts(
        "SELECT b.code, b.title, b.descricao, b.eixo, b.atualizada_em,"
        "       rl.name AS linha,"
        "       (SELECT COUNT(*) FROM biblioteca_item i WHERE i.biblioteca_id = b.id) AS n"
        "  FROM biblioteca b LEFT JOIN research_lines rl ON rl.id = b.research_line_id"
        " WHERE b.ativa = 1 ORDER BY b.title")


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
        "rede": _rede_do_acervo(dentro),
        "triangulo": _triangulo(dentro),
        "decisao": _decisao(por_segmento),
    }


def _paises_do_acervo(itens: list[dict[str, Any]]) -> dict[str, Any]:
    """Onde o assunto e estudado, pela afiliacao de quem assina.

    O pais vem de QUEM ASSINA, e nao da revista: uma revista holandesa
    publica o mundo inteiro, e contar por revista responderia "onde se
    publica", que e outra pergunta.
    """
    from .variaveis import bandeira

    contagem: dict[str, dict[str, Any]] = {}
    for item in itens:
        for pais in item.get("paises") or []:
            alvo = contagem.setdefault(pais, {"pais": pais, "n": 0, "artigos": [],
                                              "bandeira": bandeira(pais)})
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
