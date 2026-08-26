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
        doi = next((i.get("value") for i in item.get("articleids", [])
                    if i.get("idtype") == "doi"), None)
        out.append({
            "source": "pubmed",
            "external_id": pmid,
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
