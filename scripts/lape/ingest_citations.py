"""Citacoes vindas das bases proprietarias: Scopus (Elsevier) e Web of
Science (Clarivate).

Credenciais (variaveis de ambiente, nunca no repositorio):
  SCOPUS_API_KEY     chave da Elsevier Developer Portal
  SCOPUS_INST_TOKEN  token institucional (opcional, para acesso fora da rede)
  WOS_API_KEY        chave da Web of Science Starter API

A consulta e sempre por DOI. E a unica chave que identifica um artigo sem
ambiguidade nas duas bases: buscar por titulo traz homonimo, e um numero de
citacoes atribuido ao artigo errado e pior do que numero nenhum -- ninguem
confere um numero que parece plausivel.

Sem chave, o modulo registra no ingest_log e mantem o que ja estiver nas
planilhas; o pipeline segue funcionando. Cada coleta grava tambem um
snapshot em citation_snapshots, o que permite acompanhar a evolucao.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any

from . import config
from .db import Database

SCOPUS_SEARCH = "https://api.elsevier.com/content/search/scopus"
WOS_SEARCH = "https://api.clarivate.com/apis/wos-starter/v1/documents"
REQUEST_TIMEOUT = 30
THROTTLE_SECONDS = 0.4


class ChaveRecusada(RuntimeError):
    """Chave ausente, invalida, sem permissao ou com a cota estourada.

    Separada do erro comum porque o remedio e outro: nao adianta tentar o
    proximo artigo. Antes disso, uma chave errada rendia uma falha por
    artigo -- dezenove linhas iguais no log e dezenove esperas de rede
    para dizer a mesma coisa uma vez so.
    """


def _pedir(url: str, params: dict[str, Any], headers: dict[str, str],
           fonte: str) -> dict[str, Any]:
    """GET que devolve JSON, na biblioteca padrao.

    Aqui morava um `import requests` com um `except ImportError: return
    None` -- e um None nesse caminho e indistinguivel de "a base nao
    conhece este artigo". Numa maquina sem a biblioteca instalada, a
    coleta inteira respondia `scopus=0 wos=0 erros=0`: o relatorio de
    quem trabalhou e nao achou nada, dado por quem nunca saiu do lugar.
    """
    endereco = url + "?" + urllib.parse.urlencode(params)
    pedido = urllib.request.Request(endereco, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(pedido, timeout=REQUEST_TIMEOUT) as resposta:
            return json.loads(resposta.read().decode("utf-8", "replace") or "{}")
    except urllib.error.HTTPError as erro:
        corpo = ""
        try:
            corpo = erro.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        if erro.code in (401, 403, 429):
            motivo = {401: "chave nao aceita", 403: "sem permissao para esta base",
                      429: "cota do dia esgotada"}[erro.code]
            raise ChaveRecusada(f"{fonte} HTTP {erro.code}: {motivo}. {corpo}".strip())
        raise RuntimeError(f"{fonte} HTTP {erro.code}: {corpo}")
    except urllib.error.URLError as erro:
        raise RuntimeError(f"{fonte} sem resposta: {erro.reason}")


def fetch_scopus(doi: str, api_key: str, inst_token: str = "") -> dict[str, Any] | None:
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
    if inst_token:
        headers["X-ELS-Insttoken"] = inst_token
    dados = _pedir(SCOPUS_SEARCH, {
        "query": f'DOI("{doi}")',
        "field": "citedby-count,eid,prism:doi,dc:title",
        "count": 1,
    }, headers, "Scopus")
    entries = dados.get("search-results", {}).get("entry", [])
    if not entries or "error" in entries[0]:
        return None
    entry = entries[0]
    return {
        "citations": int(entry.get("citedby-count", 0) or 0),
        "scopus_id": entry.get("eid"),
    }


def fetch_wos(doi: str, api_key: str) -> dict[str, Any] | None:
    headers = {"X-ApiKey": api_key, "Accept": "application/json"}
    dados = _pedir(WOS_SEARCH, {"q": f"DO={doi}", "db": "WOS", "limit": 1},
                   headers, "WoS")
    hits = dados.get("hits") or []
    if not hits:
        return None
    hit = hits[0]
    # A Starter API devolve `citations` como lista de bases -- [{"db": "WOS",
    # "count": 12}] -- porque a mesma referencia e contada em indices
    # diferentes. O numero que o mural promete e o da WOS; somar todas as
    # bases inflaria a contagem com o que ninguem foi conferir la.
    citations = hit.get("citations")
    total = 0
    if isinstance(citations, list):
        wos = [c for c in citations if isinstance(c, dict)
               and str(c.get("db", "")).upper() == "WOS"]
        alvo = wos or [c for c in citations if isinstance(c, dict)]
        total = sum(int(c.get("count", 0) or 0) for c in alvo)
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


FONTES = (
    ("scopus", "Scopus", "SCOPUS_API_KEY", "scopus_id"),
    ("wos", "Web of Science", "WOS_API_KEY", "wos_id"),
)


def situacao(db: Database) -> dict[str, Any]:
    """O que a tela precisa dizer ANTES de alguem apertar o botao.

    Tres coisas param esta coleta, e nenhuma delas se descobre apertando:
    nao ha chave, nao ha DOI nos artigos, ou a chave nao vale para a base.
    Sem este retrato, o botao responderia "0 atualizados" nos tres casos.
    """
    com_doi = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE doi IS NOT NULL AND TRIM(doi) <> ''") or 0)
    total = int(db.scalar("SELECT COUNT(*) FROM articles") or 0)
    fontes = []
    for chave, rotulo, variavel, _ in FONTES:
        fontes.append({
            "chave": chave,
            "rotulo": rotulo,
            "variavel": variavel,
            "configurada": bool(getattr(config, variavel, "")),
            "artigos_com_numero": int(db.scalar(
                f"SELECT COUNT(*) FROM articles WHERE {chave}_citations > 0") or 0),
            "citacoes": int(db.scalar(
                f"SELECT COALESCE(SUM({chave}_citations), 0) FROM articles") or 0),
        })
    return {
        "fontes": fontes,
        "artigos": total,
        "com_doi": com_doi,
        "sem_doi": total - com_doi,
        "atualizado_em": db.scalar(
            "SELECT MAX(citations_updated_at) FROM articles"),
        "token_institucional": bool(config.SCOPUS_INST_TOKEN),
    }


def update_citations(db: Database, limit: int | None = None,
                     verbose: bool = True) -> dict[str, Any]:
    """Atualiza citacoes de todos os artigos que tenham DOI."""
    stats: dict[str, Any] = {"scopus": 0, "wos": 0, "sem_doi": 0, "erros": 0,
                             "consultados": 0, "recusadas": {}}
    articles = db.dicts(
        "SELECT id, title, doi FROM articles WHERE doi IS NOT NULL AND TRIM(doi) <> ''"
        " ORDER BY COALESCE(year_published, 0) DESC" + (f" LIMIT {int(limit)}" if limit else "")
    )
    stats["sem_doi"] = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE doi IS NULL OR TRIM(doi) = ''") or 0)
    stats["consultados"] = len(articles)

    chaves = {"scopus": config.SCOPUS_API_KEY, "wos": config.WOS_API_KEY}
    if not any(chaves.values()):
        db.log_ingest("citacoes", status="ignorado",
                      message="SCOPUS_API_KEY/WOS_API_KEY nao configuradas")
        if verbose:
            print("  ! SCOPUS_API_KEY/WOS_API_KEY ausentes -- citacoes mantidas como estao na planilha")
        return stats
    if not articles:
        db.log_ingest("citacoes", status="ignorado",
                      message=f"nenhum artigo com DOI ({stats['sem_doi']} sem)")
        if verbose:
            print(f"  ! nenhum artigo tem DOI -- a consulta e por DOI ({stats['sem_doi']} artigo(s) sem)")
        return stats

    # Uma chave recusada e recusada para sempre nesta rodada: desliga-se a
    # fonte e a outra segue. Insistir artigo a artigo so gastaria a cota
    # que ja estourou -- ou repetiria "chave nao aceita" dezenove vezes.
    desligadas: dict[str, str] = {}
    for article in articles:
        doi = article["doi"].strip()
        for chave, rotulo, _, id_field in FONTES:
            if not chaves[chave] or chave in desligadas:
                continue
            try:
                if chave == "scopus":
                    result = fetch_scopus(doi, chaves[chave], config.SCOPUS_INST_TOKEN)
                else:
                    result = fetch_wos(doi, chaves[chave])
                if result:
                    _record(db, article["id"], chave, result["citations"],
                            id_field, result.get(id_field))
                    stats[chave] += 1
            except ChaveRecusada as exc:
                desligadas[chave] = str(exc)[:300]
                db.log_ingest(chave, status="erro", message=str(exc)[:300])
                if verbose:
                    print(f"  ! {rotulo} desligada nesta rodada: {exc}")
                continue
            except Exception as exc:
                stats["erros"] += 1
                db.log_ingest(chave, file=doi, status="erro", message=str(exc)[:300])
            time.sleep(THROTTLE_SECONDS)

    stats["recusadas"] = desligadas
    db.conn.commit()
    db.log_ingest("citacoes", target="articles", rows_read=len(articles),
                  rows_written=stats["scopus"] + stats["wos"],
                  status="ok" if not (stats["erros"] or desligadas) else "parcial",
                  message=f"scopus={stats['scopus']} wos={stats['wos']} erros={stats['erros']}")
    if verbose:
        print(f"  citacoes: scopus={stats['scopus']} wos={stats['wos']}"
              f" erros={stats['erros']} artigos_sem_doi={stats['sem_doi']}")
    return stats
