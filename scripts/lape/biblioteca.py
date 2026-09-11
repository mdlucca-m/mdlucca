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
from datetime import date
from typing import Any

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
# Os acervos declarados
# ----------------------------------------------------------------------
# A populacao e "atleta", e nao "esporte". A diferenca custou metade do
# acervo e vale a pena escrever: com `"sports"[MeSH]` a busca traz 847
# registros e entre eles programas comunitarios de caminhada, que tem
# estado de humor medido e nao tem atleta nenhum. Fechando em atleta, sao
# 431 -- e sao de quem a pergunta e sobre.
#
# `POMS` PRECISA do [Title/Abstract]. Solto, a PubMed o traduz para
# `"prod oper manag"[Journal]` junto com o termo, e a revista Production &
# Operations Management entra no acervo de psicologia do esporte. Foi
# medido: 362 registros, e nenhum aviso de que isso aconteceu.
HUMOR_CONSTRUTO = (
    '"Profile of Mood States"[Title/Abstract] OR "mood state"[Title/Abstract]'
    ' OR "mood states"[Title/Abstract] OR "mood profile"[Title/Abstract]'
    ' OR "mood disturbance"[Title/Abstract] OR "POMS"[Title/Abstract]'
    ' OR "BRUMS"[Title/Abstract] OR "Brunel Mood Scale"[Title/Abstract]'
    ' OR "iceberg profile"[Title/Abstract]'
)
HUMOR_POPULACAO = (
    '"athletes"[MeSH Terms] OR athlete[Title/Abstract] OR athletes[Title/Abstract]'
    ' OR "elite sport"[Title/Abstract] OR "competitive sport"[Title/Abstract]'
)

# Os esportes em que o acervo se divide. Cada um e um termo de busca, e a
# lista sai do que a literatura de humor no esporte de fato estuda -- nao
# de uma lista de modalidades olimpicas, que traria dezenas de segmentos
# vazios e faria a tela parecer quebrada.
ESPORTES: tuple[tuple[str, str], ...] = (
    ("Futebol", 'soccer[Title/Abstract] OR football[Title/Abstract]'),
    ("Natação", 'swimming[Title/Abstract] OR swimmers[Title/Abstract]'),
    ("Atletismo", '"track and field"[Title/Abstract] OR runners[Title/Abstract]'
                  ' OR "distance running"[Title/Abstract]'),
    ("Handebol", 'handball[Title/Abstract]'),
    ("Basquete", 'basketball[Title/Abstract]'),
    ("Vôlei", 'volleyball[Title/Abstract]'),
    ("Judô e lutas", 'judo[Title/Abstract] OR wrestling[Title/Abstract]'
                     ' OR "combat sport"[Title/Abstract] OR "combat sports"[Title/Abstract]'
                     ' OR taekwondo[Title/Abstract] OR karate[Title/Abstract]'),
    ("Ginástica", 'gymnastics[Title/Abstract] OR gymnasts[Title/Abstract]'),
    ("Ciclismo", 'cycling[Title/Abstract] OR cyclists[Title/Abstract]'),
    ("Remo e canoagem", 'rowing[Title/Abstract] OR rowers[Title/Abstract]'
                        ' OR canoeing[Title/Abstract] OR kayak[Title/Abstract]'),
    ("Tênis e raquete", 'tennis[Title/Abstract] OR badminton[Title/Abstract]'
                        ' OR "table tennis"[Title/Abstract]'),
    ("Paradesporto", 'paralympic[Title/Abstract] OR "para athletes"[Title/Abstract]'
                     ' OR "disability sport"[Title/Abstract]'),
    ("Rugby e futebol americano", 'rugby[Title/Abstract] OR "american football"[Title/Abstract]'),
    ("Triatlo", 'triathlon[Title/Abstract] OR triathletes[Title/Abstract]'),
)

# (codigo, titulo, linha de pesquisa, eixo, descricao, construto, populacao, segmentos)
BIBLIOTECAS: tuple[dict[str, Any], ...] = (
    {
        "code": "humor_esporte",
        "title": "Estado de humor no esporte",
        "linha": "psicologia_do_esporte",
        "eixo": "esporte",
        "descricao":
            "O que se sabe sobre o humor de quem compete: como ele é medido, o que o "
            "move ao longo de uma temporada e o que ele antecipa do desempenho e do "
            "adoecimento. O acervo cobre a produção indexada na PubMed e se divide por "
            "modalidade, porque a mesma medida responde de maneira diferente num "
            "esporte coletivo e num de resistência.",
        "construto": HUMOR_CONSTRUTO,
        "populacao": HUMOR_POPULACAO,
        "segmentos": ESPORTES,
    },
)


def query_de(biblioteca: dict[str, Any], segmento_termo: str | None = None) -> str:
    """A busca inteira, montada das partes declaradas."""
    partes = [f"({biblioteca['construto']})", f"({biblioteca['populacao']})"]
    if segmento_termo:
        partes.append(f"({segmento_termo})")
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

        # A busca geral, sem segmento: e ela que define o tamanho do acervo.
        _guardar_busca(db, bid, None, query_de(decl))
        for nome, termo in decl["segmentos"]:
            _guardar_busca(db, bid, nome, query_de(decl, termo))
    db.conn.commit()
    return {"novas": novas, "ja_havia": ja_havia, "total": len(BIBLIOTECAS)}


def _guardar_busca(db: Database, biblioteca_id: int, segmento: str | None,
                   query: str) -> None:
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
        " WHERE biblioteca_id = ? AND base = 'pubmed'"
        "   AND ((segmento IS NULL AND ? IS NULL) OR segmento = ?)",
        (biblioteca_id, segmento, segmento))
    if achada:
        db.execute("UPDATE biblioteca_busca SET query = ? WHERE id = ?", (query, achada))
        return
    db.execute(
        "INSERT INTO biblioteca_busca (biblioteca_id, base, segmento, query)"
        " VALUES (?, 'pubmed', ?, ?)", (biblioteca_id, segmento, query))


# ----------------------------------------------------------------------
# A atualizacao
# ----------------------------------------------------------------------
def atualizar(db: Database, code: str, limite: int = 400,
              verbose: bool = False) -> dict[str, Any]:
    """Roda as buscas do acervo e recolhe o que ainda nao estava aqui.

    Uma busca falhar nao derruba as outras: a rede cai no meio de quatorze
    modalidades, e perder as treze que ja tinham voltado por causa da
    decima quarta seria trocar um acervo por um erro. O erro fica gravado
    ao lado da busca que falhou, e a tela o mostra.
    """
    from . import referencias, sources
    from .revisao import chave_de_uniao

    dados = db.dicts("SELECT id, title FROM biblioteca WHERE code = ?", (code,))
    if not dados:
        raise ValueError(f"biblioteca “{code}” não existe")
    bid, titulo = dados[0]["id"], dados[0]["title"]

    buscas = db.dicts(
        "SELECT id, segmento, query FROM biblioteca_busca"
        " WHERE biblioteca_id = ? ORDER BY segmento IS NULL DESC, segmento", (bid,))
    hoje = date.today().isoformat()
    resumo = {"biblioteca": titulo, "buscas": 0, "achados": 0, "novos": 0,
              "erros": 0, "segmentos": []}

    for busca in buscas:
        resumo["buscas"] += 1
        try:
            pmids = sources.pubmed_search(busca["query"], retmax=limite)
            registros = referencias.ler_nbib(sources.pubmed_medline(pmids)) if pmids else []
        except Exception as erro:  # noqa: BLE001 -- uma busca nao derruba as outras
            db.execute("UPDATE biblioteca_busca SET rodada_em = ?, erro = ? WHERE id = ?",
                       (hoje, str(erro)[:300], busca["id"]))
            resumo["erros"] += 1
            if verbose:
                print(f"  ! {busca['segmento'] or 'geral'}: {erro}")
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
        if busca["segmento"]:
            resumo["segmentos"].append({"segmento": busca["segmento"],
                                        "achados": len(registros), "novos": novos})
        if verbose:
            print(f"  {busca['segmento'] or 'geral'}: {len(registros)} achado(s),"
                  f" {novos} novo(s)")

    db.execute("UPDATE biblioteca SET atualizada_em = ? WHERE id = ?", (hoje, bid))
    db.conn.commit()
    db.log_ingest("biblioteca", target=code, rows_read=resumo["achados"],
                  rows_written=resumo["novos"],
                  status="ok" if not resumo["erros"] else "parcial",
                  message=f"{resumo['novos']} novo(s) em {resumo['buscas']} busca(s)")
    return resumo


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
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pubmed')",
        (biblioteca_id, chave, segmento, clean_text(registro.get("title")),
         clean_text(registro.get("abstract")),
         "; ".join(registro.get("authors") or []) if isinstance(registro.get("authors"), list)
         else clean_text(registro.get("authors")),
         clean_text(registro.get("journal")), registro.get("year"),
         norm_doi(registro.get("doi")), clean_text(registro.get("pmid")),
         clean_text(registro.get("pmc")), clean_text(registro.get("url")),
         clean_text(registro.get("oa_url")), json.dumps(paises, ensure_ascii=False)))
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
           busca: str | None = None, limite: int = 300) -> dict[str, Any]:
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
    if busca:
        onde.append("(LOWER(title) LIKE ? OR LOWER(abstract) LIKE ?"
                    " OR LOWER(authors) LIKE ? OR LOWER(journal) LIKE ?)")
        params.extend([f"%{busca.lower()}%"] * 4)
    itens = db.dicts(
        f"SELECT * FROM biblioteca_item WHERE {' AND '.join(onde)}"
        f" ORDER BY COALESCE(year, 0) DESC, title LIMIT ?", params + [limite])
    return {"biblioteca": biblioteca, "itens": [_item(i) for i in itens],
            "segmento": segmento, "busca": busca}


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
    segmentos = []
    for busca in db.dicts(
            "SELECT segmento, achados, rodada_em, erro FROM biblioteca_busca"
            " WHERE biblioteca_id = ? AND segmento IS NOT NULL ORDER BY segmento", (bid,)):
        n = int(db.scalar(
            "SELECT COUNT(*) FROM biblioteca_item WHERE biblioteca_id = ?"
            "   AND ('; ' || segmento || '; ') LIKE ?",
            (bid, f"%; {busca['segmento']}; %")) or 0)
        segmentos.append({"segmento": busca["segmento"], "n": n,
                          "rodada_em": busca["rodada_em"], "erro": busca["erro"]})
    segmentos.sort(key=lambda x: (-x["n"], x["segmento"]))

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
