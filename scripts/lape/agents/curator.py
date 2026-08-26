"""Agente Curador do LAPE.

Responsabilidade unica: manter o banco de dados coerente e publicavel.
Recebe dados de tres origens -- planilhas, Currículo Lattes e o agente
rastreador -- alem do cadastro manual feito pela API, e entrega o banco
normalizado mais o painel HTML e o JSON de indicadores.

O que ele faz:
  cadastrar   grava artigos, submissoes, integrantes, linhas e eventos
              aceitando os mesmos nomes de coluna das planilhas
  consolidar  deduplica titulos, resolve autores, deriva status e datas
  revisar     promove ou descarta as descobertas do rastreador
  validar     lista as lacunas que limitam as analises
  publicar    recalcula os indicadores e regenera o painel
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .. import config, ingest_excel, ingest_lattes, metrics, report
from ..db import Database
from ..mapping import build_column_map
from ..util import clean_text, norm_key, title_key

NAME = "curador"

# tabela -> (handler de ingestao, tabela fisica, chave de busca)
REGISTRARS: dict[str, tuple[Any, str]] = {
    "articles": (ingest_excel.ingest_articles, "articles"),
    "submissions": (ingest_excel.ingest_submissions, "submissions"),
    "members": (ingest_excel.ingest_members, "members"),
    "research_lines": (ingest_excel.ingest_research_lines, "research_lines"),
    "institutions": (ingest_excel.ingest_institutions, "institutions"),
    "events": (ingest_excel.ingest_events, "events"),
    "projects": (ingest_excel.ingest_projects, "projects"),
    "project_members": (ingest_excel.ingest_project_members, "project_members"),
    "rejection_reasons": (ingest_excel.ingest_rejection_reasons, "rejection_reasons"),
    "authors": (ingest_excel.ingest_authors, "article_authors"),
    "event_participants": (ingest_excel.ingest_event_participants, "event_participants"),
}


# ----------------------------------------------------------------------
# Cadastro
# ----------------------------------------------------------------------
def normalize_payload(entity: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Aceita chaves canonicas ('title') ou de planilha ('Titulo do artigo')."""
    column_map = build_column_map(entity, list(payload))
    row: dict[str, Any] = {}
    for original, field in column_map.items():
        row[field] = payload[original]
    for key, value in payload.items():  # chaves ja canonicas passam direto
        row.setdefault(norm_key(key), value)
    return row


def register(db: Database, entity: str, payload: dict[str, Any] | list[dict[str, Any]],
             ) -> dict[str, Any]:
    """Cadastra ou atualiza registros de qualquer entidade do banco."""
    if entity not in REGISTRARS:
        raise ValueError(f"entidade desconhecida: {entity}"
                         f" (use uma de {', '.join(sorted(REGISTRARS))})")
    handler, table = REGISTRARS[entity]
    items = payload if isinstance(payload, list) else [payload]
    rows = [normalize_payload(entity, item) for item in items]
    written = handler(db, rows)
    db.conn.commit()
    db.log_ingest(NAME, target=table, file="api", rows_read=len(rows), rows_written=written)
    return {"entity": entity, "received": len(rows), "written": written,
            "records": _echo(db, entity, rows)}


def _echo(db: Database, entity: str, rows: list[dict]) -> list[dict]:
    """Devolve os registros gravados, para a API confirmar o que persistiu."""
    if entity == "articles":
        keys = [title_key(r.get("title")) for r in rows if clean_text(r.get("title"))]
        if not keys:
            return []
        marks = ", ".join("?" for _ in keys)
        return db.dicts(
            f"SELECT * FROM v_articles_full WHERE title_key IN ({marks})", keys
        )
    if entity == "members":
        from ..util import author_key

        keys = [author_key(r.get("full_name")) for r in rows if clean_text(r.get("full_name"))]
        if not keys:
            return []
        marks = ", ".join("?" for _ in keys)
        return db.dicts(f"SELECT * FROM members WHERE name_key IN ({marks})", keys)
    return []


# ----------------------------------------------------------------------
# Revisao das descobertas do rastreador
# ----------------------------------------------------------------------
def review_discovery(db: Database, discovery_id: int, action: str = "aceitar",
                     overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Promove uma descoberta a artigo do banco, ou a descarta."""
    row = db.dicts("SELECT * FROM discoveries WHERE id = ?", (discovery_id,))
    if not row:
        raise KeyError(f"descoberta {discovery_id} nao encontrada")
    discovery = row[0]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if action in ("ignorar", "descartar", "rejeitar"):
        db.execute("UPDATE discoveries SET status = 'ignorado', reviewed_at = ? WHERE id = ?",
                   (now, discovery_id))
        db.conn.commit()
        return {"id": discovery_id, "status": "ignorado"}

    payload = {
        "title": discovery["title"],
        "authors": discovery["authors"],
        "journal": discovery["journal"],
        "year_published": discovery["year"],
        "doi": discovery["doi"],
        "url": discovery["url"],
        "status": "publicado" if discovery["year"] else "aceito",
        "openalex_citations": discovery["citations"],
        **(overrides or {}),
    }
    result = register(db, "articles", payload)
    article_id = db.scalar("SELECT id FROM articles WHERE title_key = ?",
                           (title_key(discovery["title"]),))
    if discovery["citations"] is not None:
        db.execute("UPDATE articles SET openalex_citations = ? WHERE id = ?",
                   (discovery["citations"], article_id))
    db.execute(
        "UPDATE discoveries SET status = 'aceito', reviewed_at = ?, article_id = ? WHERE id = ?",
        (now, article_id, discovery_id),
    )
    db.conn.commit()
    return {"id": discovery_id, "status": "aceito", "article_id": article_id,
            "article": result["records"][0] if result["records"] else None}


def auto_review(db: Database, min_authors_matched: int = 2) -> dict[str, Any]:
    """Aceita automaticamente descobertas com forte evidencia de autoria.

    Exige que pelo menos `min_authors_matched` autores da publicacao ja
    sejam integrantes cadastrados -- o que praticamente elimina homonimos.
    """
    from ..util import author_key, split_authors

    known = {row["name_key"] for row in db.dicts("SELECT name_key FROM members")}
    accepted = 0
    for discovery in db.dicts("SELECT id, authors FROM discoveries WHERE status = 'pendente'"):
        matches = sum(1 for name in split_authors(discovery["authors"])
                      if author_key(name) in known)
        if matches >= min_authors_matched:
            review_discovery(db, discovery["id"], "aceitar")
            accepted += 1
    return {"accepted": accepted}


# ----------------------------------------------------------------------
# Consolidacao e validacao
# ----------------------------------------------------------------------
def consolidate(db: Database) -> dict[str, Any]:
    """Deriva status, datas e vinculos apos qualquer carga de dados."""
    ingest_excel._sync_article_dates(db)
    ingest_excel.derive_status(db)
    ingest_excel._geocode_events(db)
    db.execute(
        "UPDATE articles SET year_published = CAST(substr(published_on, 1, 4) AS INTEGER)"
        " WHERE year_published IS NULL AND published_on IS NOT NULL AND status = 'publicado'"
    )
    db.conn.commit()
    indices = metrics.compute_h_indexes(db)
    return {"articles": int(db.scalar("SELECT COUNT(*) FROM articles") or 0),
            "h_index_recalculado": indices["members"]}


def duplicate_candidates(db: Database) -> list[dict]:
    """Integrantes que provavelmente sao a mesma pessoa em duas grafias."""
    members = db.dicts("SELECT id, full_name, name_key FROM members ORDER BY full_name")
    out: list[dict] = []
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            first_a = a["full_name"].split()[0].lower()
            first_b = b["full_name"].split()[0].lower()
            same_surname = a["name_key"].split("_")[0] == b["name_key"].split("_")[0]
            same_first = first_a == first_b and len(first_a) > 3
            if same_surname or same_first:
                out.append({"a_id": a["id"], "a": a["full_name"],
                            "b_id": b["id"], "b": b["full_name"],
                            "motivo": "mesmo sobrenome" if same_surname else "mesmo primeiro nome"})
    return out


def validate(db: Database) -> dict[str, Any]:
    quality = metrics.data_quality(db)
    duplicates = duplicate_candidates(db)
    return {
        "issues": quality["issues"],
        "duplicate_members": duplicates,
        "pending_discoveries": int(
            db.scalar("SELECT COUNT(*) FROM discoveries WHERE status = 'pendente'") or 0),
        "articles_without_authors": int(db.scalar(
            "SELECT COUNT(*) FROM articles a WHERE NOT EXISTS"
            " (SELECT 1 FROM article_authors aa WHERE aa.article_id = a.id)") or 0),
    }


# ----------------------------------------------------------------------
# Publicacao
# ----------------------------------------------------------------------
def publish(db: Database, output: Path = config.REPORT_PATH,
            window: int = config.WINDOW_YEARS, json_output: Path | None = None) -> dict[str, Any]:
    payload = metrics.build_payload(db, window=window)
    html = report.render(payload, output)
    data_path = json_output or output.with_suffix(".json")
    report.export_json(payload, data_path)
    db.log_ingest(NAME, target="report", file=str(html),
                  rows_written=payload["overview"]["n_articles"])
    return {"html": str(html), "json": str(data_path), "overview": payload["overview"]}


# ----------------------------------------------------------------------
# Execucao
# ----------------------------------------------------------------------
def run(db: Database, raw_dir: Path = config.RAW_DIR, output: Path = config.REPORT_PATH,
        window: int = config.WINDOW_YEARS, with_tracker: bool = True,
        tracker_tasks: tuple[str, ...] = ("enriquecer", "citar", "perfis"),
        auto_accept: bool = False, verbose: bool = True) -> dict[str, Any]:
    """Ciclo completo: carregar, consolidar, rastrear, validar e publicar."""
    from . import tracker as tracker_agent

    if verbose:
        print(f"[agente:{NAME}] ciclo completo")
    result: dict[str, Any] = {"agent": NAME, "at": datetime.now().isoformat(timespec="seconds")}

    if verbose:
        print("  planilhas")
    result["excel"] = ingest_excel.ingest_all(db, raw_dir, verbose=verbose)
    if verbose:
        print("  currículo Lattes")
    result["lattes"] = ingest_lattes.ingest_all(db, raw_dir, verbose=verbose)

    if with_tracker:
        result["tracker"] = tracker_agent.run(db, tracker_tasks, verbose=verbose)
        if auto_accept:
            result["auto_review"] = auto_review(db)

    result["consolidate"] = consolidate(db)
    result["validation"] = validate(db)
    result["publish"] = publish(db, output, window)
    if verbose:
        over = result["publish"]["overview"]
        print(f"  {over['n_articles']} artigos | {over['n_published']} publicados"
              f" | {over['n_members']} integrantes | {over['n_events']} atividades")
        print(f"  painel: {result['publish']['html']}")
    return result
