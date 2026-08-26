"""Enriquecimento de citacoes via Scopus (Elsevier) e Web of Science (Clarivate).

Credenciais (variaveis de ambiente, nunca no repositorio):
  SCOPUS_API_KEY     chave da Elsevier Developer Portal
  SCOPUS_INST_TOKEN  token institucional (opcional, para acesso fora da rede)
  WOS_API_KEY        chave da Web of Science Starter API

Sem chave, o modulo apenas registra no ingest_log e mantem os valores que
ja estiverem nas planilhas -- o pipeline segue funcionando normalmente.
Cada coleta grava tambem um snapshot em citation_snapshots, o que permite
acompanhar a evolucao das citacoes ao longo do tempo.
"""
from __future__ import annotations

import time
from datetime import date
from typing import Any

from . import config
from .db import Database

SCOPUS_SEARCH = "https://api.elsevier.com/content/search/scopus"
WOS_SEARCH = "https://api.clarivate.com/apis/wos-starter/v1/documents"
REQUEST_TIMEOUT = 30
THROTTLE_SECONDS = 0.4


def _requests():
    try:
        import requests  # import tardio: o pipeline roda sem rede
    except ImportError:  # pragma: no cover
        return None
    return requests


def fetch_scopus(doi: str, api_key: str, inst_token: str = "") -> dict[str, Any] | None:
    requests = _requests()
    if requests is None:
        return None
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    if inst_token:
        headers["X-ELS-Insttoken"] = inst_token
    params = {"query": f'DOI("{doi}")', "field": "citedby-count,eid,prism:doi,dc:title", "count": 1}
    response = requests.get(SCOPUS_SEARCH, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"Scopus HTTP {response.status_code}: {response.text[:200]}")
    entries = response.json().get("search-results", {}).get("entry", [])
    if not entries or "error" in entries[0]:
        return None
    entry = entries[0]
    return {
        "citations": int(entry.get("citedby-count", 0) or 0),
        "scopus_id": entry.get("eid"),
    }


def fetch_wos(doi: str, api_key: str) -> dict[str, Any] | None:
    requests = _requests()
    if requests is None:
        return None
    headers = {"X-ApiKey": api_key, "Accept": "application/json"}
    params = {"q": f"DO={doi}", "db": "WOS", "limit": 1}
    response = requests.get(WOS_SEARCH, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"WoS HTTP {response.status_code}: {response.text[:200]}")
    hits = response.json().get("hits", [])
    if not hits:
        return None
    hit = hits[0]
    citations = hit.get("citations") or []
    total = 0
    if isinstance(citations, list):
        total = sum(int(c.get("count", 0) or 0) for c in citations if isinstance(c, dict))
    elif isinstance(citations, (int, str)):
        total = int(citations or 0)
    return {"citations": total, "wos_id": hit.get("uid")}


def _record(db: Database, article_id: int, source: str, citations: int,
            id_field: str, external_id: Any) -> None:
    today = date.today().isoformat()
    column = "scopus_citations" if source == "scopus" else "wos_citations"
    db.execute(
        f"UPDATE articles SET {column} = ?, citations_updated_at = ?"
        f"{', ' + id_field + ' = ?' if external_id else ''} WHERE id = ?",
        ((citations, today, external_id, article_id) if external_id else (citations, today, article_id)),
    )
    db.execute(
        "INSERT OR REPLACE INTO citation_snapshots (article_id, source, citations, snapshot_on)"
        " VALUES (?, ?, ?, ?)",
        (article_id, source, citations, today),
    )


def update_citations(db: Database, limit: int | None = None, verbose: bool = True) -> dict[str, int]:
    """Atualiza citacoes de todos os artigos que tenham DOI."""
    stats = {"scopus": 0, "wos": 0, "sem_doi": 0, "erros": 0}
    articles = db.dicts(
        "SELECT id, title, doi FROM articles WHERE doi IS NOT NULL AND doi <> ''"
        " ORDER BY COALESCE(year_published, 0) DESC" + (f" LIMIT {int(limit)}" if limit else "")
    )
    stats["sem_doi"] = int(db.scalar("SELECT COUNT(*) FROM articles WHERE doi IS NULL OR doi = ''") or 0)

    if not config.SCOPUS_API_KEY and not config.WOS_API_KEY:
        db.log_ingest("citacoes", status="ignorado",
                      message="SCOPUS_API_KEY/WOS_API_KEY nao configuradas")
        if verbose:
            print("  ! SCOPUS_API_KEY/WOS_API_KEY ausentes -- citacoes mantidas como estao na planilha")
        return stats

    for article in articles:
        doi = article["doi"]
        if config.SCOPUS_API_KEY:
            try:
                result = fetch_scopus(doi, config.SCOPUS_API_KEY, config.SCOPUS_INST_TOKEN)
                if result:
                    _record(db, article["id"], "scopus", result["citations"], "scopus_id", result["scopus_id"])
                    stats["scopus"] += 1
            except Exception as exc:
                stats["erros"] += 1
                db.log_ingest("scopus", file=doi, status="erro", message=str(exc)[:300])
            time.sleep(THROTTLE_SECONDS)
        if config.WOS_API_KEY:
            try:
                result = fetch_wos(doi, config.WOS_API_KEY)
                if result:
                    _record(db, article["id"], "wos", result["citations"], "wos_id", result["wos_id"])
                    stats["wos"] += 1
            except Exception as exc:
                stats["erros"] += 1
                db.log_ingest("wos", file=doi, status="erro", message=str(exc)[:300])
            time.sleep(THROTTLE_SECONDS)

    db.conn.commit()
    db.log_ingest("citacoes", target="articles", rows_read=len(articles),
                  rows_written=stats["scopus"] + stats["wos"],
                  status="ok" if not stats["erros"] else "parcial",
                  message=f"scopus={stats['scopus']} wos={stats['wos']} erros={stats['erros']}")
    if verbose:
        print(f"  citacoes: scopus={stats['scopus']} wos={stats['wos']}"
              f" erros={stats['erros']} artigos_sem_doi={stats['sem_doi']}")
    return stats
