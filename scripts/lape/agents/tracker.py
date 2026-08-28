"""Agente Rastreador do LAPE.

Responsabilidade unica: ir buscar informacao la fora e trazer para dentro.
Nao decide o que entra no banco definitivo -- isso e do agente curador.

Tres tarefas:
  descobrir   varre OpenAlex/PubMed pela producao dos integrantes e
              registra em `discoveries` o que ainda nao esta no banco
  enriquecer  completa DOI, periodico, ano e ISSN dos artigos ja
              cadastrados, cruzando Crossref e OpenAlex pelo titulo
  citar       atualiza as contagens de citacao (OpenAlex sempre;
              Scopus e Web of Science quando houver chave de API)

Tudo o que o agente faz fica registrado em `ingest_log`, e nenhuma
informacao vinda de fora sobrescreve o que o laboratorio digitou:
os campos so sao preenchidos quando estao vazios.
"""
from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

from .. import config, hooks, sources
from ..db import Database
from ..util import clean_text, norm_doi, title_key, to_int

MAILTO = os.environ.get("LAPE_CONTACT_EMAIL") or None
INSTITUTION_QUERY = os.environ.get("LAPE_INSTITUTION_QUERY", "Universidade do Estado de Santa Catarina")
NAME = "rastreador"


# ----------------------------------------------------------------------
# Descoberta
# ----------------------------------------------------------------------
def trackable_members(db: Database) -> list[dict]:
    """Integrantes rastreaveis: com ORCID, ou nome completo (2+ palavras)."""
    rows = db.dicts(
        "SELECT id, full_name, short_name, orcid, lattes_id FROM members"
        " WHERE active = 1 ORDER BY full_name"
    )
    extra = [n.strip() for n in os.environ.get("LAPE_TRACK_AUTHORS", "").split(";") if n.strip()]
    tracked = [r for r in rows if clean_text(r["orcid"]) or len(r["full_name"].split()) >= 2]
    for name in extra:
        if not any(r["full_name"].lower() == name.lower() for r in tracked):
            tracked.append({"id": None, "full_name": name, "short_name": None,
                            "orcid": None, "lattes_id": None})
    return tracked


def discover(db: Database, since_year: int | None = None, limit_per_author: int = 60,
             verbose: bool = True) -> dict[str, Any]:
    """Procura producao nova dos integrantes e registra como 'descoberta'.

    Nada entra direto em `articles`: o curador (ou uma pessoa, pela API)
    decide o que promover. Isso evita poluir o banco com homonimos.
    """
    since_year = since_year or (date.today().year - config.WINDOW_YEARS + 1)
    members = trackable_members(db)
    found = new = 0
    errors: list[str] = []

    known = {row["title_key"] for row in db.dicts("SELECT title_key FROM articles")}
    known_dois = {row["doi"] for row in db.dicts(
        "SELECT doi FROM articles WHERE doi IS NOT NULL") }

    for member in members:
        try:
            works = sources.openalex_works_by_author(
                name=member["full_name"], orcid=clean_text(member["orcid"]),
                institution=None if member["orcid"] else INSTITUTION_QUERY,
                since_year=since_year, limit=limit_per_author, mailto=MAILTO,
            )
        except sources.SourceError as exc:
            errors.append(f"{member['full_name']}: {exc}")
            continue
        for work in works:
            found += 1
            key = title_key(work["title"])
            if not key or key in known or (work["doi"] and work["doi"] in known_dois):
                continue
            db.upsert(
                "discoveries",
                {
                    "source": "openalex",
                    "title_key": key,
                    "external_id": work["external_id"],
                    "doi": work["doi"],
                    "title": work["title"],
                    "authors": "; ".join(work["authors"][:25]),
                    "journal": work["journal"],
                    "year": work["year"],
                    "citations": work["citations"],
                    "url": work["url"],
                    "matched_member_id": member["id"],
                    "status": "pendente",
                    "payload": json.dumps(work, ensure_ascii=False),
                },
                conflict=("source", "title_key"),
                fill_only=True,
            )
            known.add(key)
            new += 1

    db.conn.commit()
    if new:
        hooks.emit(db, "descoberta.encontrada", entity="discoveries",
                   detail=f"{new} publicação(ões) nova(s) para revisar",
                   payload={"new": new, "authors_checked": len(members)})
    db.log_ingest(NAME, target="discoveries", rows_read=found, rows_written=new,
                  status="parcial" if errors else "ok",
                  message=f"autores={len(members)} novos={new}"
                          + (f" erros={len(errors)}" if errors else ""))
    if verbose:
        print(f"  descoberta: {len(members)} autores consultados, {found} trabalhos vistos,"
              f" {new} novidades registradas")
        for err in errors[:5]:
            print(f"    ! {err}")
    return {"authors": len(members), "seen": found, "new": new, "errors": errors}


# ----------------------------------------------------------------------
# Enriquecimento
# ----------------------------------------------------------------------
def enrich(db: Database, limit: int | None = None, verbose: bool = True) -> dict[str, Any]:
    """Completa metadados faltantes dos artigos ja cadastrados."""
    pending = db.dicts(
        "SELECT id, title, doi, journal, year_published, status FROM articles"
        " WHERE doi IS NULL OR journal IS NULL OR (status = 'publicado' AND year_published IS NULL)"
        " ORDER BY CASE status WHEN 'publicado' THEN 0 WHEN 'aceito' THEN 1 ELSE 2 END, id"
        + (f" LIMIT {int(limit)}" if limit else "")
    )
    updated = 0
    errors: list[str] = []
    for article in pending:
        try:
            meta = sources.best_metadata(article["doi"], article["title"], mailto=MAILTO)
        except sources.SourceError as exc:
            errors.append(f"{article['title'][:50]}: {exc}")
            continue
        if not meta:
            continue
        _fill_missing(db, article["id"], {
            "doi": meta.get("doi"),
            "journal": meta.get("journal"),
            "issn": meta.get("issn"),
            "year_published": meta.get("year") if article["status"] == "publicado" else None,
            "published_on": meta.get("published_on") if article["status"] == "publicado" else None,
            "url": meta.get("url"),
            "open_access": 1 if meta.get("open_access") else None,
        })
        updated += 1

    db.conn.commit()
    db.log_ingest(NAME, target="articles", rows_read=len(pending), rows_written=updated,
                  status="parcial" if errors else "ok", message="enriquecimento de metadados")
    if verbose:
        print(f"  enriquecimento: {len(pending)} artigos incompletos, {updated} completados")
    return {"pending": len(pending), "updated": updated, "errors": errors}


def identificar(db: Database, limit: int | None = None,
                verbose: bool = True) -> dict[str, Any]:
    """Acha DOI, PMID, PMC e o acesso aberto de cada artigo.

    A ordem das fontes nao e arbitraria:

      1. **DOI**, se ja houver: e o identificador, e o OpenAlex responde por
         ele com tudo -- PMID, PMC, situacao de acesso aberto e o endereco
         do texto livre;
      2. **titulo no OpenAlex**, que cobre revista brasileira e area de
         humanas, que a PubMed nao indexa;
      3. **titulo na PubMed**, so aceitando quando o titulo bate de fato.

    Identificador errado e pior do que nenhum: ele parece certo, e ninguem
    confere de novo. Por isso a busca por titulo exige semelhanca alta, e
    nada aqui sobrescreve o que ja estava preenchido.
    """
    pendentes = db.dicts(
        "SELECT id, title, doi, pmid, pmc, status, year_published FROM articles"
        " WHERE doi IS NULL OR TRIM(COALESCE(doi, '')) = ''"
        "    OR pmid IS NULL OR oa_status IS NULL"
        " ORDER BY CASE status WHEN 'publicado' THEN 0 WHEN 'aceito' THEN 1 ELSE 2 END,"
        "          COALESCE(year_published, 0) DESC, id"
        + (f" LIMIT {int(limit)}" if limit else ""))

    achados, sem_nada, erros = 0, 0, []
    for artigo in pendentes:
        encontrado: dict[str, Any] = {}
        try:
            if artigo["doi"]:
                obra = sources.openalex_by_doi(artigo["doi"], mailto=MAILTO)
                if obra:
                    encontrado.update(obra)
            if not encontrado.get("pmid") or not encontrado.get("doi"):
                obra = sources.openalex_search_title(artigo["title"], mailto=MAILTO)
                if obra:
                    for chave, valor in obra.items():
                        encontrado.setdefault(chave, valor)
            if not encontrado.get("pmid"):
                registro = (sources.pubmed_por_doi(artigo["doi"]) if artigo["doi"]
                            else sources.pubmed_por_titulo(artigo["title"]))
                if registro:
                    for chave, valor in registro.items():
                        encontrado.setdefault(chave, valor)
        except sources.SourceError as exc:
            erros.append(f"{(artigo['title'] or '')[:48]}: {exc}")
            continue

        campos = {
            "doi": encontrado.get("doi"),
            "pmid": encontrado.get("pmid"),
            "pmc": encontrado.get("pmc"),
            "oa_url": encontrado.get("oa_url"),
            "oa_status": encontrado.get("oa_status"),
            "journal": encontrado.get("journal"),
            "issn": encontrado.get("issn"),
            "url": encontrado.get("url"),
        }
        if encontrado.get("open_access") is not None:
            campos["open_access"] = 1 if encontrado["open_access"] else 0
        if artigo["status"] == "publicado":
            campos["year_published"] = encontrado.get("year")
        if any(v is not None for v in campos.values()):
            _fill_missing(db, artigo["id"], campos)
            achados += 1
        else:
            sem_nada += 1

    db.conn.commit()
    db.log_ingest(NAME, target="articles", rows_read=len(pendentes),
                  rows_written=achados, status="parcial" if erros else "ok",
                  message="identificadores e acesso aberto")
    if verbose:
        print(f"  identificadores: {len(pendentes)} sem identificação completa,"
              f" {achados} com algo encontrado, {sem_nada} sem nada nas bases")
    return {"pendentes": len(pendentes), "achados": achados,
            "sem_nada": sem_nada, "erros": erros}


def _fill_missing(db: Database, article_id: int, values: dict[str, Any]) -> None:
    """Preenche apenas os campos ainda vazios do artigo.

    O que veio da planilha ou do Lattes tem precedencia sobre as bases
    externas -- o agente completa lacunas, nunca corrige o laboratorio.
    """
    payload = {k: v for k, v in values.items() if v is not None}
    if not payload:
        return
    assignments = ", ".join(f"{c} = COALESCE({c}, ?)" for c in payload)
    db.execute(
        f"UPDATE articles SET {assignments}, updated_at = datetime('now') WHERE id = ?",
        [*payload.values(), article_id],
    )


# ----------------------------------------------------------------------
# Citacoes
# ----------------------------------------------------------------------
def citations(db: Database, limit: int | None = None, verbose: bool = True) -> dict[str, Any]:
    """Atualiza citacoes: OpenAlex sempre, Scopus/WoS quando houver chave."""
    from .. import ingest_citations

    today = date.today().isoformat()
    articles = db.dicts(
        "SELECT id, doi, title FROM articles WHERE doi IS NOT NULL AND doi <> ''"
        " ORDER BY COALESCE(year_published, 0) DESC" + (f" LIMIT {int(limit)}" if limit else "")
    )
    openalex_ok = 0
    errors: list[str] = []
    for article in articles:
        try:
            work = sources.openalex_by_doi(article["doi"], mailto=MAILTO)
        except sources.SourceError as exc:
            errors.append(str(exc))
            continue
        if not work or work.get("citations") is None:
            continue
        db.execute(
            "UPDATE articles SET openalex_citations = ?, citations_updated_at = ? WHERE id = ?",
            (work["citations"], today, article["id"]),
        )
        db.execute(
            "INSERT OR REPLACE INTO citation_snapshots (article_id, source, citations, snapshot_on)"
            " VALUES (?, 'openalex', ?, ?)",
            (article["id"], work["citations"], today),
        )
        openalex_ok += 1
    db.conn.commit()

    proprietary = ingest_citations.update_citations(db, limit=limit, verbose=False)
    db.log_ingest(NAME, target="citations", rows_read=len(articles),
                  rows_written=openalex_ok + proprietary["scopus"] + proprietary["wos"],
                  status="parcial" if errors else "ok",
                  message=f"openalex={openalex_ok} scopus={proprietary['scopus']}"
                          f" wos={proprietary['wos']}")
    if verbose:
        print(f"  citações: openalex={openalex_ok} scopus={proprietary['scopus']}"
              f" wos={proprietary['wos']} (artigos com DOI: {len(articles)})")
        if not config.SCOPUS_API_KEY and not config.WOS_API_KEY:
            print("    (defina SCOPUS_API_KEY / WOS_API_KEY para as bases proprietárias)")
    return {"articles": len(articles), "openalex": openalex_ok, **proprietary, "errors": errors}


# ----------------------------------------------------------------------
# Perfis dos pesquisadores
# ----------------------------------------------------------------------
def profiles(db: Database, verbose: bool = True) -> dict[str, Any]:
    """Le o perfil publico de cada pesquisador e traz indice h global.

    O indice h do OpenAlex cobre toda a carreira, nao so o que esta neste
    banco. Quando o autor tem ORCID cadastrado a identificacao e exata;
    sem ORCID a busca e por nome + instituicao e pode falhar em homonimos,
    por isso o valor so e gravado quando o nome bate.
    """
    from ..util import author_key

    updated = 0
    errors: list[str] = []
    for member in db.dicts(
        "SELECT id, full_name, orcid, openalex_id FROM members"
        " WHERE active = 1 AND is_external = 0 ORDER BY full_name"
    ):
        try:
            profile = sources.openalex_author(
                orcid=clean_text(member["orcid"]),
                name=member["full_name"] if not member["orcid"] else None,
                institution=INSTITUTION_QUERY, mailto=MAILTO)
        except sources.SourceError as exc:
            errors.append(f"{member['full_name']}: {exc}")
            continue
        if not profile:
            continue
        if not member["orcid"] and author_key(profile["display_name"]) != author_key(member["full_name"]):
            continue  # provavel homonimo: nao grava
        db.execute(
            "UPDATE members SET openalex_id = COALESCE(openalex_id, ?), orcid = COALESCE(orcid, ?),"
            " h_index = ?, h_index_source = 'openalex_author', i10_index = ?,"
            " citations_total = ?, metrics_updated_at = date('now') WHERE id = ?",
            (profile["openalex_id"], profile["orcid"], profile["h_index"], profile["i10_index"],
             profile["citations_total"], member["id"]),
        )
        updated += 1
    db.conn.commit()
    db.log_ingest(NAME, target="members", rows_written=updated,
                  status="parcial" if errors else "ok", message="perfis OpenAlex")
    if verbose:
        print(f"  perfis: {updated} pesquisadores com índice h atualizado")
    return {"updated": updated, "errors": errors}


# ----------------------------------------------------------------------
# Execucao
# ----------------------------------------------------------------------
TASKS = ("descobrir", "enriquecer", "citar", "perfis")


def run(db: Database, tasks: tuple[str, ...] = TASKS, verbose: bool = True,
        **options: Any) -> dict[str, Any]:
    """Executa o agente rastreador."""
    if verbose:
        print(f"[agente:{NAME}] tarefas: {', '.join(tasks)}")
    report: dict[str, Any] = {"agent": NAME, "tasks": list(tasks), "at": date.today().isoformat()}
    if "enriquecer" in tasks:
        report["enrich"] = enrich(db, limit=options.get("limit"), verbose=verbose)
    if "citar" in tasks:
        report["citations"] = citations(db, limit=options.get("limit"), verbose=verbose)
    if "perfis" in tasks:
        report["profiles"] = profiles(db, verbose=verbose)
    if "descobrir" in tasks:
        report["discover"] = discover(db, since_year=options.get("since_year"), verbose=verbose)
    return report
