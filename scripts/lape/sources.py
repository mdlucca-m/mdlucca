"""Clientes das bases bibliograficas consultadas em tempo real.

Usa apenas a biblioteca padrao (urllib), para que o agente rastreador
funcione em qualquer ambiente -- inclusive dentro do GitHub Actions --
sem dependencias extras.

Bases abertas (nao exigem chave):
  OpenAlex   https://api.openalex.org   metadados + contagem de citacoes
  Crossref   https://api.crossref.org   metadados canonicos por DOI/titulo
  PubMed     E-utilities do NCBI        indexacao biomedica

Bases proprietarias (exigem chave, ver ingest_citations.py):
  Scopus (Elsevier) e Web of Science (Clarivate)
"""
from __future__ import annotations

import re
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .util import clean_text, norm_doi

OPENALEX = "https://api.openalex.org"
CROSSREF = "https://api.crossref.org"
PUBMED = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

USER_AGENT = "LAPE-Pipeline/1.0 (https://www.udesc.br/cefid/lape)"
TIMEOUT = 30
RETRIES = 3
BACKOFF = 2.0
THROTTLE = 0.15


class SourceError(RuntimeError):
    """Falha ao consultar uma base externa."""


def _get_text(url: str, params: dict[str, Any] | None = None,
              timeout: int = 30) -> str:
    """Como `_get`, mas para respostas que nao sao JSON."""
    import urllib.parse
    import urllib.request

    limpos = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    endereco = f"{url}?{urllib.parse.urlencode(limpos)}" if limpos else url
    pedido = urllib.request.Request(endereco, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
        return resposta.read().decode("utf-8", "replace")


def _get(url: str, params: dict[str, Any] | None = None,
         headers: dict[str, str] | None = None, expect_json: bool = True) -> Any:
    """GET com retentativa e backoff exponencial."""
    if params:
        url = f"{url}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "application/json",
                                                   **(headers or {})})
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                payload = response.read()
            time.sleep(THROTTLE)
            return json.loads(payload) if expect_json else payload
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < RETRIES - 1:
                time.sleep(BACKOFF ** (attempt + 1))
                last = exc
                continue
            raise SourceError(f"HTTP {exc.code} em {url}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF ** (attempt + 1))
                continue
    raise SourceError(f"falha ao consultar {url}: {last}")


# ----------------------------------------------------------------------
# OpenAlex
# ----------------------------------------------------------------------
def _so_numero(valor: Any) -> str | None:
    """`https://pubmed.ncbi.nlm.nih.gov/38333426` -> `38333426`."""
    texto = clean_text(valor)
    if not texto:
        return None
    achado = re.search(r"(\d{4,9})\s*$", texto)
    return achado.group(1) if achado else None


def _pmc(valor: Any) -> str | None:
    """Devolve sempre no formato `PMC12345`, venha como vier."""
    texto = clean_text(valor)
    if not texto:
        return None
    achado = re.search(r"(PMC\d+)", texto, re.I)
    return achado.group(1).upper() if achado else None


def _openalex_work(work: dict) -> dict[str, Any]:
    location = (work.get("primary_location") or {}).get("source") or {}
    authors = [
        clean_text((a.get("author") or {}).get("display_name"))
        for a in work.get("authorships", [])
    ]
    return {
        "source": "openalex",
        "external_id": work.get("id"),
        "doi": norm_doi(work.get("doi")),
        "title": clean_text(work.get("title") or work.get("display_name")),
        "authors": [a for a in authors if a],
        "journal": clean_text(location.get("display_name")),
        "issn": (location.get("issn_l") or None),
        "year": work.get("publication_year"),
        "published_on": clean_text(work.get("publication_date")),
        "citations": work.get("cited_by_count"),
        "type": clean_text(work.get("type")),
        "open_access": bool((work.get("open_access") or {}).get("is_oa")),
        # O OpenAlex ja carrega estes tres e eles nunca eram lidos. `oa_url`
        # e o endereco do texto livre -- o que interessa a quem vai ler, e
        # nao a pagina da editora atras do paywall.
        "oa_status": clean_text((work.get("open_access") or {}).get("oa_status")),
        "oa_url": clean_text((work.get("open_access") or {}).get("oa_url")
                             or ((work.get("best_oa_location") or {}).get("pdf_url"))),
        "pmid": _so_numero((work.get("ids") or {}).get("pmid")),
        "pmc": _pmc((work.get("ids") or {}).get("pmcid")),
        "url": (work.get("primary_location") or {}).get("landing_page_url") or work.get("doi"),
        "institutions": sorted({
            clean_text(inst.get("display_name"))
            for a in work.get("authorships", [])
            for inst in a.get("institutions", [])
            if clean_text(inst.get("display_name"))
        }),
        "countries": sorted({
            inst.get("country_code")
            for a in work.get("authorships", [])
            for inst in a.get("institutions", [])
            if inst.get("country_code")
        }),
    }


def openalex_by_doi(doi: str, mailto: str | None = None) -> dict[str, Any] | None:
    doi = norm_doi(doi) or ""
    if not doi:
        return None
    try:
        work = _get(f"{OPENALEX}/works/doi:{urllib.parse.quote(doi)}", {"mailto": mailto})
    except SourceError:
        return None
    return _openalex_work(work) if work else None


def openalex_search_title(title: str, mailto: str | None = None) -> dict[str, Any] | None:
    text = clean_text(title)
    if not text:
        return None
    data = _get(f"{OPENALEX}/works", {
        "filter": f"title.search:{text[:250]}", "per-page": 3, "mailto": mailto,
    })
    for work in data.get("results", []):
        parsed = _openalex_work(work)
        if parsed["title"] and _similar(parsed["title"], text):
            return parsed
    return None


def openalex_works_by_author(name: str | None = None, orcid: str | None = None,
                             institution: str | None = None, since_year: int | None = None,
                             limit: int = 100, mailto: str | None = None) -> list[dict[str, Any]]:
    """Lista a producao de um pesquisador. ORCID e o identificador mais confiavel."""
    filters: list[str] = []
    if orcid:
        filters.append(f"author.orcid:{clean_text(orcid)}")
    elif name:
        filters.append(f"raw_author_name.search:{clean_text(name)}")
    else:
        return []
    if institution:
        filters.append(f"raw_affiliation_strings.search:{institution}")
    if since_year:
        filters.append(f"from_publication_date:{since_year}-01-01")

    results: list[dict[str, Any]] = []
    cursor = "*"
    while len(results) < limit and cursor:
        data = _get(f"{OPENALEX}/works", {
            "filter": ",".join(filters), "per-page": min(100, limit - len(results)),
            "cursor": cursor, "mailto": mailto,
        })
        for work in data.get("results", []):
            results.append(_openalex_work(work))
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not data.get("results"):
            break
    return results[:limit]


def openalex_author(orcid: str | None = None, name: str | None = None,
                    institution: str | None = None,
                    mailto: str | None = None) -> dict[str, Any] | None:
    """Perfil publico do autor: indice h, i10 e total de citacoes.

    O indice h daqui e global -- inclui producao anterior ao laboratorio --
    e por isso e o valor que os pesquisadores costumam reportar.
    """
    if orcid:
        target = f"{OPENALEX}/authors/orcid:{urllib.parse.quote(clean_text(orcid))}"
        try:
            author = _get(target, {"mailto": mailto})
        except SourceError:
            return None
    elif name:
        filters = [f"display_name.search:{clean_text(name)}"]
        if institution:
            filters.append(f"last_known_institutions.display_name.search:{institution}")
        data = _get(f"{OPENALEX}/authors", {
            "filter": ",".join(filters), "per-page": 1, "mailto": mailto})
        results = data.get("results", [])
        if not results:
            return None
        author = results[0]
    else:
        return None

    stats = author.get("summary_stats") or {}
    institutions = author.get("last_known_institutions") or []
    return {
        "openalex_id": author.get("id"),
        "display_name": clean_text(author.get("display_name")),
        "orcid": clean_text(author.get("orcid")),
        "works_count": author.get("works_count"),
        "citations_total": author.get("cited_by_count"),
        "h_index": stats.get("h_index"),
        "i10_index": stats.get("i10_index"),
        "mean_citedness": stats.get("2yr_mean_citedness"),
        "institution": clean_text(institutions[0].get("display_name")) if institutions else None,
    }


# ----------------------------------------------------------------------
# Crossref
# ----------------------------------------------------------------------
def _crossref_item(item: dict) -> dict[str, Any]:
    authors = [
        clean_text(" ".join(filter(None, [a.get("given"), a.get("family")])))
        for a in item.get("author", [])
    ]
    issued = ((item.get("issued") or {}).get("date-parts") or [[None]])[0]
    titles = item.get("title") or []
    containers = item.get("container-title") or []
    return {
        "source": "crossref",
        "external_id": item.get("DOI"),
        "doi": norm_doi(item.get("DOI")),
        "title": clean_text(titles[0] if titles else None),
        "authors": [a for a in authors if a],
        "journal": clean_text(containers[0] if containers else None),
        "issn": (item.get("ISSN") or [None])[0],
        "year": issued[0] if issued else None,
        "published_on": "-".join(str(p).zfill(2) for p in issued) if issued and issued[0] else None,
        "citations": item.get("is-referenced-by-count"),
        "type": clean_text(item.get("type")),
        "url": item.get("URL"),
    }


def crossref_by_doi(doi: str, mailto: str | None = None) -> dict[str, Any] | None:
    doi = norm_doi(doi) or ""
    if not doi:
        return None
    try:
        data = _get(f"{CROSSREF}/works/{urllib.parse.quote(doi)}", {"mailto": mailto})
    except SourceError:
        return None
    return _crossref_item(data.get("message", {}))


def crossref_search_title(title: str, mailto: str | None = None) -> dict[str, Any] | None:
    text = clean_text(title)
    if not text:
        return None
    data = _get(f"{CROSSREF}/works", {
        "query.bibliographic": text[:300], "rows": 3, "select":
        "DOI,title,author,container-title,ISSN,issued,is-referenced-by-count,type,URL",
        "mailto": mailto,
    })
    for item in (data.get("message") or {}).get("items", []):
        parsed = _crossref_item(item)
        if parsed["title"] and _similar(parsed["title"], text):
            return parsed
    return None


# ----------------------------------------------------------------------
# PubMed
# ----------------------------------------------------------------------
def pubmed_search(term: str, retmax: int = 50) -> list[str]:
    data = _get(f"{PUBMED}/esearch.fcgi", {
        "db": "pubmed", "term": term, "retmax": retmax, "retmode": "json",
    })
    return (data.get("esearchresult") or {}).get("idlist", [])


def pubmed_summaries(pmids: list[str]) -> list[dict[str, Any]]:
    if not pmids:
        return []
    data = _get(f"{PUBMED}/esummary.fcgi", {
        "db": "pubmed", "id": ",".join(pmids), "retmode": "json",
    })
    result = data.get("result", {})
    out: list[dict[str, Any]] = []
    for pmid in result.get("uids", []):
        item = result.get(pmid, {})
        ids = item.get("articleids", [])
        doi = next((i.get("value") for i in ids if i.get("idtype") == "doi"), None)
        pmc = _pmc(next((i.get("value") for i in ids
                         if i.get("idtype") in ("pmc", "pmcid")), None))
        out.append({
            "source": "pubmed",
            "external_id": pmid,
            "pmid": pmid,
            "pmc": pmc,
            "oa_url": (f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/" if pmc else None),
            "doi": norm_doi(doi),
            "title": clean_text(item.get("title")),
            "authors": [clean_text(a.get("name")) for a in item.get("authors", []) if a.get("name")],
            "journal": clean_text(item.get("fulljournalname") or item.get("source")),
            "issn": clean_text(item.get("issn")),
            "year": int(str(item.get("pubdate", ""))[:4]) if str(item.get("pubdate", ""))[:4].isdigit() else None,
            "published_on": None,
            "citations": None,
            "type": "journal-article",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return out


def pubmed_por_doi(doi: str) -> dict[str, Any] | None:
    """Acha o registro na PubMed pelo DOI -- o caminho mais confiavel."""
    limpo = norm_doi(doi)
    if not limpo:
        return None
    achados = pubmed_search(f"{limpo}[Location ID]", retmax=2)
    if not achados:
        achados = pubmed_search(f'"{limpo}"[All Fields]', retmax=2)
    registros = pubmed_summaries(achados[:1])
    return registros[0] if registros else None


def pubmed_por_titulo(titulo: str) -> dict[str, Any] | None:
    """Acha pelo titulo, e so aceita se o titulo bater de verdade.

    Busca por titulo devolve resultado quase sempre -- inclusive quando o
    artigo nao esta la. Sem a conferencia, o banco ganharia PMID de outro
    trabalho, e um identificador errado e pior do que nenhum: ele parece
    certo e ninguem confere de novo.
    """
    texto = clean_text(titulo)
    if not texto or len(texto) < 15:
        return None
    achados = pubmed_search(f'"{texto}"[Title]', retmax=3)
    if not achados:
        achados = pubmed_search(f"{texto}[Title]", retmax=3)
    for registro in pubmed_summaries(achados[:3]):
        if _similar(texto, registro.get("title") or "", threshold=0.90):
            return registro
    return None


def pubmed_medline(pmids: list[str], lote: int = 150) -> str:
    """Baixa os registros completos em MEDLINE -- com resumo e afiliacao.

    O `esummary` traz titulo e revista e para por ai. O resumo e a
    afiliacao so vem no `efetch` em MEDLINE, e sao justamente eles que o
    painel precisa: o resumo alimenta o reconhecimento de variaveis, e a
    afiliacao diz de que pais e o estudo.

    O formato e o mesmo do arquivo `.nbib` que a PubMed entrega no botao
    "Send to", entao quem le e o leitor de referencias que ja existe.
    """
    partes: list[str] = []
    for inicio in range(0, len(pmids), lote):
        pedaco = pmids[inicio:inicio + lote]
        partes.append(_get_text(f"{PUBMED}/efetch.fcgi", {
            "db": "pubmed", "id": ",".join(pedaco),
            "rettype": "medline", "retmode": "text",
        }))
    return "\n".join(partes)


def termo_de_autor(nome: str, afiliacao: str | None = None,
                   desde: int | None = None) -> str:
    """Monta a busca da PubMed para um pesquisador.

    A PubMed indexa o autor como "Sobrenome Iniciais" -- "Andrade A", nao
    "Alexandro Andrade". Buscar pelo nome inteiro nao acha nada, e o
    silencio parece "esta pessoa nao publicou".

    A afiliacao nao e enfeite: "Andrade A" sozinho traz milhares de
    artigos de dezenas de pessoas diferentes. Sem ela, a importacao enche
    o banco de producao alheia.

    Desde 2002 a PubMed tambem indexa o nome por extenso, e "Andrade
    Alexandro[Author]" acerta a pessoa sem depender de afiliacao nenhuma
    -- inclusive nos artigos em que ela assinou por outra instituicao.
    Como nem todo registro tem o nome por extenso, os dois caminhos vao
    unidos: nome inteiro OU (abreviado E afiliacao).

    So o PRIMEIRO nome entra na forma por extenso. Incluir o nome do meio
    exige que o registro tambem o traga, e os que nao trazem somem da
    busca (com "Vilarino Guilherme Torres" some um decimo da producao).

    E ha o sobrenome COMPOSTO. A PubMed indexa o sobrenome como o periodico
    mandou, e "Guilherme Torres Vilarino" aparece ora como "Vilarino GT",
    ora como "Torres Vilarino G" -- sao duas entradas diferentes no indice,
    e quem procura so pela ultima palavra perde a outra. Com este autor
    eram 30 de 34 artigos: os quatro que faltavam estavam todos indexados
    pela forma composta, e o silencio parecia "so publicou 30".

    A forma composta vai SEM afiliacao, pelo mesmo motivo do nome por
    extenso: "Torres Vilarino G" e um endereco especifico o bastante --
    hoje, na PubMed inteira, ele so devolve artigos deste laboratorio.
    """
    pedacos = [p for p in clean_text(nome).split() if p]
    sobrenome = pedacos[-1] if pedacos else ""
    iniciais = "".join(p[0] for p in pedacos[:-1]).upper()
    abreviado = f"{sobrenome} {iniciais}[Author]" if iniciais else f"{sobrenome}[Author]"
    inteiro = f"{sobrenome} {pedacos[0]}[Author]" if iniciais else None
    # "Torres Vilarino G": as duas ultimas palavras como sobrenome, e as
    # anteriores viram inicial. So faz sentido com tres pedacos ou mais.
    composto = None
    if len(pedacos) >= 3:
        iniciaisDoComposto = "".join(p[0] for p in pedacos[:-2]).upper()
        composto = f"{pedacos[-2]} {sobrenome} {iniciaisDoComposto}[Author]"
    livres = [x for x in (inteiro, composto) if x]
    if not afiliacao:
        # Sem afiliacao, o abreviado sozinho traz gente demais -- entao,
        # havendo nome de batismo, so as formas especificas valem.
        termo = " OR ".join(livres) if livres else abreviado
    else:
        comAfiliacao = f"{abreviado} AND {clean_text(afiliacao)}[Affiliation]"
        termo = " OR ".join(livres + [f"({comAfiliacao})"]) if livres else comAfiliacao
    if desde:
        janela = f'("{desde}"[Date - Publication] : "3000"[Date - Publication])'
        # Sem os parenteses em volta, o recorte de data grudaria so no
        # ultimo ramo do OR e o outro voltaria a producao inteira.
        termo = f"({termo}) AND {janela}"
    return termo


# ----------------------------------------------------------------------
# Apoio
# ----------------------------------------------------------------------
def _similar(a: str, b: str, threshold: float = 0.86) -> bool:
    """Comparacao tolerante de titulos (evita falsos positivos na busca)."""
    from difflib import SequenceMatcher

    from .util import title_key

    ka, kb = title_key(a), title_key(b)
    if not ka or not kb:
        return False
    if ka == kb or ka.startswith(kb[:40]) or kb.startswith(ka[:40]):
        return True
    return SequenceMatcher(None, ka, kb).ratio() >= threshold


def best_metadata(doi: str | None = None, title: str | None = None,
                  mailto: str | None = None) -> dict[str, Any] | None:
    """Consolida metadados: Crossref manda nos dados, OpenAlex nas citacoes."""
    crossref = crossref_by_doi(doi, mailto) if doi else None
    openalex = openalex_by_doi(doi, mailto) if doi else None
    if not crossref and not openalex and title:
        crossref = crossref_search_title(title, mailto)
        if crossref and crossref.get("doi"):
            openalex = openalex_by_doi(crossref["doi"], mailto)
        if not crossref:
            openalex = openalex_search_title(title, mailto)
    if not crossref and not openalex:
        return None
    merged = dict(openalex or {})
    for key, value in (crossref or {}).items():
        if value not in (None, "", []) and key not in {"citations", "source", "external_id"}:
            merged[key] = value
    merged["source"] = "+".join(filter(None, [
        "crossref" if crossref else None, "openalex" if openalex else None,
    ]))
    merged["citations_openalex"] = (openalex or {}).get("citations")
    merged["citations_crossref"] = (crossref or {}).get("citations")
    return merged
