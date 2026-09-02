"""Calculo de todos os indicadores do painel do LAPE.

`build_payload()` devolve um dicionario JSON-serializavel que alimenta o
dashboard HTML. Cada chave corresponde a um bloco do painel.
"""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from datetime import date, datetime
from itertools import combinations
from typing import Any, Iterable, Sequence

from . import config
from .db import Database

TODAY = date.today()
IN_PROGRESS = ("em_producao",)
UNDER_REVIEW = ("submetido", "em_revisao")


# ----------------------------------------------------------------------
# Estatistica descritiva
# ----------------------------------------------------------------------
def describe(values: Iterable[Any], unit: str = "dias") -> dict[str, Any]:
    data = sorted(float(v) for v in values if v is not None)
    if not data:
        return {"n": 0, "unit": unit}
    return {
        "n": len(data),
        "unit": unit,
        "min": round(data[0], 1),
        "max": round(data[-1], 1),
        "mean": round(statistics.fmean(data), 1),
        "median": round(statistics.median(data), 1),
        "p25": round(_percentile(data, 25), 1),
        "p75": round(_percentile(data, 75), 1),
        "sd": round(statistics.stdev(data), 1) if len(data) > 1 else 0.0,
        "values": [round(v, 1) for v in data],
    }


def _percentile(sorted_data: Sequence[float], pct: float) -> float:
    if not sorted_data:
        return 0.0
    if len(sorted_data) == 1:
        return sorted_data[0]
    position = (len(sorted_data) - 1) * pct / 100
    low, high = int(position), min(int(position) + 1, len(sorted_data) - 1)
    return sorted_data[low] + (sorted_data[high] - sorted_data[low]) * (position - low)


def _histogram(values: Iterable[float], bins: Sequence[tuple[float, float, str]]) -> list[dict]:
    data = [v for v in values if v is not None]
    out = []
    for low, high, label in bins:
        count = sum(1 for v in data if low <= v < high)
        out.append({"label": label, "n": count})
    return out


# ----------------------------------------------------------------------
# Blocos do painel
# ----------------------------------------------------------------------
def research_lines(db: Database) -> list[dict]:
    """Indice das linhas de pesquisa com producao associada."""
    return db.dicts(
        """
        SELECT rl.id, rl.code, rl.name, rl.description, rl.coordinator,
               rl.keywords, rl.started_on, rl.active,
               (SELECT COUNT(*) FROM articles a WHERE a.research_line_id = rl.id) AS n_articles,
               (SELECT COUNT(*) FROM articles a WHERE a.research_line_id = rl.id
                  AND a.status = 'publicado') AS n_published,
               (SELECT COUNT(*) FROM articles a WHERE a.research_line_id = rl.id
                  AND a.status IN ('em_producao')) AS n_in_progress,
               (SELECT COUNT(*) FROM articles a WHERE a.research_line_id = rl.id
                  AND a.status IN ('submetido','em_revisao')) AS n_submitted,
               (SELECT COUNT(*) FROM members m WHERE m.research_line_id = rl.id) AS n_members,
               (SELECT COUNT(*) FROM events e WHERE e.research_line_id = rl.id) AS n_events,
               (SELECT COALESCE(SUM(a.scopus_citations),0) FROM articles a
                  WHERE a.research_line_id = rl.id) AS scopus_citations
        FROM research_lines rl
        ORDER BY n_articles DESC, rl.name
        """
    )


def articles_by_status(db: Database, statuses: Sequence[str], order_by: str) -> list[dict]:
    placeholders = ", ".join("?" for _ in statuses)
    return db.dicts(
        f"""
        SELECT id, internal_code, title, authors, research_line, status, study_type,
               started_on, first_submission_on, accepted_on, published_on, year_published,
               journal, doi, url, submission_attempts, rejections,
               days_start_to_publication, days_submission_to_acceptance,
               (SELECT s.journal FROM submissions s WHERE s.article_id = v_articles_full.id
                  ORDER BY s.attempt_no DESC LIMIT 1) AS current_journal,
               (SELECT s.submitted_on FROM submissions s WHERE s.article_id = v_articles_full.id
                  ORDER BY s.attempt_no DESC LIMIT 1) AS last_submitted_on,
               CASE WHEN started_on IS NOT NULL
                    THEN CAST(julianday('now') - julianday(started_on) AS INTEGER) END AS days_open
        FROM v_articles_full
        WHERE status IN ({placeholders})
        ORDER BY {order_by}
        """,
        list(statuses),
    )


def publications_by_year(db: Database, window: int = config.WINDOW_YEARS) -> dict[str, Any]:
    rows = db.dicts("SELECT * FROM v_publications_by_year ORDER BY year")
    by_year = {int(r["year"]): r for r in rows if r["year"]}
    current = TODAY.year
    years = list(range(current - window + 1, current + 1))
    series = [
        {
            "year": year,
            "n_articles": int(by_year.get(year, {}).get("n_articles", 0)),
            "scopus_citations": int(by_year.get(year, {}).get("scopus_citations", 0)),
            "wos_citations": int(by_year.get(year, {}).get("wos_citations", 0)),
        }
        for year in years
    ]
    total_window = sum(item["n_articles"] for item in series)
    return {
        "window": window,
        "years": years,
        "series": series,
        "full_series": [
            {"year": int(r["year"]), "n_articles": int(r["n_articles"])} for r in rows if r["year"]
        ],
        "total_window": total_window,
        "mean_per_year": round(total_window / window, 2) if window else 0,
        "total_all_time": int(db.scalar("SELECT COUNT(*) FROM articles WHERE status = 'publicado'") or 0),
    }


CITATION_COLUMNS = {
    "scopus": "scopus_citations",
    "wos": "wos_citations",
    "openalex": "openalex_citations",
}


def most_cited(db: Database, source: str, window: int | None = None, limit: int = 10) -> list[dict]:
    column = CITATION_COLUMNS.get(source, "scopus_citations")
    clause = ""
    params: list[Any] = []
    if window:
        clause = "AND year_published >= ?"
        params.append(TODAY.year - window + 1)
    return db.dicts(
        f"""
        SELECT id, title, authors, journal, year_published, doi, url, research_line,
               {column} AS citations, scopus_citations, wos_citations, openalex_citations
        FROM v_articles_full
        WHERE status = 'publicado' AND {column} IS NOT NULL AND {column} > 0 {clause}
        ORDER BY {column} DESC, year_published DESC
        LIMIT {int(limit)}
        """,
        params,
    )


def h_index(citations: Iterable[Any]) -> int:
    """Indice h: maior h tal que h trabalhos tenham ao menos h citacoes."""
    counts = sorted((int(c) for c in citations if c is not None), reverse=True)
    h = 0
    for position, value in enumerate(counts, start=1):
        if value >= position:
            h = position
        else:
            break
    return h


def i10_index(citations: Iterable[Any]) -> int:
    """Numero de trabalhos com 10 ou mais citacoes."""
    return sum(1 for c in citations if c is not None and int(c) >= 10)


def compute_h_indexes(db: Database) -> dict[str, int]:
    """Recalcula indice h, i10 e citacoes de cada integrante a partir do banco.

    O calculo usa apenas os artigos cadastrados aqui. Quando o agente
    rastreador consegue ler o perfil publico do autor no OpenAlex, ele
    sobrescreve `h_index` com o valor global (que inclui producao anterior
    ao laboratorio) e marca a origem em `h_index_source`.
    """
    updated = 0
    for member in db.dicts("SELECT id FROM members"):
        rows = db.dicts(
            "SELECT a.scopus_citations, a.wos_citations, a.openalex_citations"
            " FROM article_authors aa JOIN articles a ON a.id = aa.article_id"
            " WHERE aa.member_id = ?", (member["id"],))
        if not rows:
            continue
        best = [max((r["openalex_citations"] or 0, r["scopus_citations"] or 0,
                     r["wos_citations"] or 0)) for r in rows]
        db.execute(
            "UPDATE members SET h_index = COALESCE(CASE WHEN h_index_source = 'openalex_author'"
            "   THEN h_index ELSE ? END, ?),"
            " h_index_source = COALESCE(h_index_source, 'banco_lape'),"
            " h_index_scopus = ?, h_index_wos = ?, i10_index = ?, citations_total = ?,"
            " metrics_updated_at = date('now') WHERE id = ?",
            (h_index(best), h_index(best),
             h_index(r["scopus_citations"] for r in rows),
             h_index(r["wos_citations"] for r in rows),
             i10_index(best), sum(best), member["id"]),
        )
        updated += 1
    db.conn.commit()
    return {"members": updated}


def researchers(db: Database) -> list[dict]:
    """Ficha completa de cada pesquisador, com projetos e indice h."""
    rows = db.dicts(
        "SELECT * FROM v_researcher ORDER BY is_external, n_articles DESC, full_name")
    projects = {}
    for link in db.dicts(
        "SELECT pm.member_id, p.id, p.name, p.code, p.status, pm.role"
        " FROM project_members pm JOIN projects p ON p.id = pm.project_id"
    ):
        projects.setdefault(link["member_id"], []).append({
            "id": link["id"], "name": link["name"], "code": link["code"],
            "status": link["status"], "role": link["role"],
        })
    for row in rows:
        row["project_list"] = projects.get(row["id"], [])
        row["articles_recent"] = db.dicts(
            "SELECT a.id, a.title, a.status, a.year_published, a.journal, a.doi,"
            "       a.scopus_citations, a.wos_citations, a.openalex_citations,"
            "       aa.author_order"
            " FROM article_authors aa JOIN articles a ON a.id = aa.article_id"
            " WHERE aa.member_id = ?"
            " ORDER BY COALESCE(a.year_published, 9999) DESC, a.title LIMIT 25",
            (row["id"],))
    return rows


def projects_overview(db: Database) -> dict[str, Any]:
    rows = db.dicts("SELECT * FROM v_projects ORDER BY status, COALESCE(started_on,'') DESC")
    by_status = Counter(r["status"] for r in rows)
    by_funder = Counter(r["funder"] for r in rows if r["funder"])
    return {
        "items": rows,
        "total": len(rows),
        "by_status": [{"status": k, "n": v} for k, v in by_status.most_common()],
        "by_funder": [{"funder": k, "n": v} for k, v in by_funder.most_common(10)],
        "active": by_status.get("em_andamento", 0),
        "total_amount": round(sum(r["amount"] or 0 for r in rows), 2),
    }


def member_productivity(db: Database) -> list[dict]:
    rows = db.dicts(
        """
        SELECT v.*, m.active, m.left_on, m.institution_id,
               (SELECT COUNT(DISTINCT ep.event_id) FROM event_participants ep
                  WHERE ep.member_id = v.member_id) AS n_events
        FROM v_member_productivity v
        JOIN members m ON m.id = v.member_id
        ORDER BY n_articles DESC, full_name
        """
    )
    return [r for r in rows if (r["n_articles"] or 0) > 0 or not r["is_external"]]


def organograma(db: Database) -> dict[str, Any]:
    """Quem orienta quem, e o que cada pessoa esta tocando.

    O desenho nao e mantido a mao: ele cai do `advisor_id` de cada ficha.
    Quem se cadastra apontando o orientador ja entra no lugar certo, e o
    que fica de fora -- orientando sem orientador, gente sem vinculo --
    aparece listado, porque um organograma so serve se disser tambem o
    que esta faltando.
    """
    from .mapping import ORIENTADOS, ROLE_LABEL, VINCULOS

    ordem = {codigo: i for i, (codigo, _, _) in enumerate(VINCULOS)}
    pessoas = db.dicts(
        """
        SELECT m.id, m.full_name, m.short_name, m.role, m.degree, m.active,
               m.advisor_id, m.co_advisor_id, m.thesis_title, m.thesis_kind,
               m.thesis_status, m.thesis_due_on, m.topics, m.scholarship,
               m.scholarship_until, m.is_external,
               rl.name AS research_line,
               (SELECT COUNT(DISTINCT aa.article_id) FROM article_authors aa
                  WHERE aa.member_id = m.id) AS n_articles,
               (SELECT COUNT(*) FROM project_members pm WHERE pm.member_id = m.id) AS n_projects,
               (SELECT group_concat(p.name, ' | ') FROM project_members pm
                  JOIN projects p ON p.id = pm.project_id
                 WHERE pm.member_id = m.id AND p.status = 'em_andamento') AS projetos
        FROM members m
        LEFT JOIN research_lines rl ON rl.id = m.research_line_id
        WHERE m.is_external = 0
        ORDER BY m.full_name
        """
    )
    por_id = {p["id"]: p for p in pessoas}
    for pessoa in pessoas:
        pessoa["role_label"] = ROLE_LABEL.get(pessoa["role"] or "", pessoa["role"] or "Sem vínculo")
        pessoa["level"] = ordem.get(pessoa["role"] or "", len(ordem))
        pessoa["advisor"] = (por_id.get(pessoa["advisor_id"]) or {}).get("full_name")
        pessoa["co_advisor"] = (por_id.get(pessoa["co_advisor_id"]) or {}).get("full_name")
        pessoa["orientandos"] = 0

    arestas = []
    for pessoa in pessoas:
        if pessoa["advisor_id"] in por_id:
            arestas.append({"from": pessoa["advisor_id"], "to": pessoa["id"], "kind": "orientacao"})
            por_id[pessoa["advisor_id"]]["orientandos"] += 1
        if pessoa["co_advisor_id"] in por_id:
            arestas.append({"from": pessoa["co_advisor_id"], "to": pessoa["id"],
                            "kind": "coorientacao"})

    # Raiz e quem nao tem orientador dentro do laboratorio. Sem essa regra,
    # um professor orientado por outro sumiria do topo do desenho.
    raizes = [p["id"] for p in pessoas if p["advisor_id"] not in por_id]
    raizes.sort(key=lambda i: (por_id[i]["level"], por_id[i]["full_name"]))

    # Uma coordenacao sozinha no topo puxa as demais raizes para baixo dela.
    # Nao e orientacao -- e coordenacao, e a aresta diz isso --, mas e assim
    # que um laboratorio se desenha, e uma floresta de arvores soltas nao
    # responderia a pergunta "quem responde a quem".
    chefes = [i for i in raizes if por_id[i]["role"] == "coordenacao"]
    if len(chefes) == 1 and len(raizes) > 1:
        topo = chefes[0]
        for outro in raizes:
            if outro != topo:
                arestas.append({"from": topo, "to": outro, "kind": "coordenacao"})
        raizes = [topo]

    contagem = Counter(p["role"] or "sem_vinculo" for p in pessoas)
    esperam_orientador = [
        {"id": p["id"], "full_name": p["full_name"], "role_label": p["role_label"]}
        for p in pessoas
        if p["role"] in ORIENTADOS and p["advisor_id"] not in por_id
    ]
    return {
        "people": pessoas,
        "edges": arestas,
        "roots": raizes,
        "by_role": [
            {"role": codigo, "label": ROLE_LABEL.get(codigo, codigo), "n": contagem.get(codigo, 0)}
            for codigo, _, _ in VINCULOS if contagem.get(codigo)
        ] + ([{"role": "sem_vinculo", "label": "Sem vínculo declarado",
               "n": contagem["sem_vinculo"]}] if contagem.get("sem_vinculo") else []),
        "sem_orientador": esperam_orientador,
        "sem_vinculo": [{"id": p["id"], "full_name": p["full_name"]}
                        for p in pessoas if not p["role"]],
        "orientadores": sorted(
            ({"id": p["id"], "full_name": p["full_name"], "role_label": p["role_label"],
              "n": p["orientandos"], "research_line": p["research_line"]}
             for p in pessoas if p["orientandos"]),
            key=lambda x: (-x["n"], x["full_name"])),
        "teses": sorted(
            ({"id": p["id"], "full_name": p["full_name"], "role_label": p["role_label"],
              "title": p["thesis_title"], "kind": p["thesis_kind"],
              "status": p["thesis_status"], "due_on": p["thesis_due_on"],
              "advisor": p["advisor"], "research_line": p["research_line"]}
             for p in pessoas
             if p["thesis_title"] or p["thesis_due_on"]),
            key=lambda x: (x["due_on"] or "9999")),
    }


def collaboration_network(db: Database, min_weight: int = 1) -> dict[str, Any]:
    """Rede de coautoria: nos = integrantes, arestas = artigos em comum."""
    rows = db.dicts(
        """
        SELECT aa.article_id, aa.member_id, m.full_name, m.short_name, m.is_external,
               m.role, rl.name AS research_line
        FROM article_authors aa
        JOIN members m ON m.id = aa.member_id
        LEFT JOIN research_lines rl ON rl.id = m.research_line_id
        WHERE aa.member_id IS NOT NULL
        """
    )
    per_article: dict[int, set[int]] = defaultdict(set)
    info: dict[int, dict] = {}
    for row in rows:
        per_article[row["article_id"]].add(row["member_id"])
        info.setdefault(
            row["member_id"],
            {
                "id": row["member_id"],
                "name": row["short_name"] or row["full_name"],
                "full_name": row["full_name"],
                "role": row["role"],
                "research_line": row["research_line"],
                "is_external": int(row["is_external"] or 0),
                "degree": 0,
                "articles": 0,
            },
        )

    edges: Counter[tuple[int, int]] = Counter()
    for members in per_article.values():
        for member in members:
            info[member]["articles"] += 1
        for a, b in combinations(sorted(members), 2):
            edges[(a, b)] += 1

    edge_list = [
        {"source": a, "target": b, "weight": w}
        for (a, b), w in edges.items()
        if w >= min_weight
    ]
    for edge in edge_list:
        info[edge["source"]]["degree"] += 1
        info[edge["target"]]["degree"] += 1

    nodes = sorted(info.values(), key=lambda n: (-n["articles"], n["name"]))
    density = 0.0
    n = len(nodes)
    if n > 1:
        density = round(2 * len(edge_list) / (n * (n - 1)), 3)
    return {
        "nodes": nodes,
        "edges": sorted(edge_list, key=lambda e: -e["weight"]),
        "density": density,
        "n_nodes": n,
        "n_edges": len(edge_list),
        "mean_degree": round(statistics.fmean([x["degree"] for x in nodes]), 2) if nodes else 0,
        "top_pairs": [
            {
                "a": info[e["source"]]["name"],
                "b": info[e["target"]]["name"],
                "weight": e["weight"],
            }
            for e in sorted(edge_list, key=lambda e: -e["weight"])[:10]
        ],
    }


def publication_timeline(db: Database) -> dict[str, Any]:
    """Tempo entre etapas do ciclo de vida dos artigos."""
    rows = db.dicts(
        """
        SELECT id, title, journal, year_published, started_on, first_submission_on,
               accepted_on, published_on, days_start_to_publication,
               days_submission_to_acceptance, days_acceptance_to_publication,
               submission_attempts
        FROM v_articles_full
        WHERE status IN ('publicado', 'aceito')
        ORDER BY published_on DESC, accepted_on DESC
        """
    )
    start_to_pub = [r["days_start_to_publication"] for r in rows]
    sub_to_acc = [r["days_submission_to_acceptance"] for r in rows]
    acc_to_pub = [r["days_acceptance_to_publication"] for r in rows]
    return {
        "articles": rows,
        "start_to_publication": describe(start_to_pub),
        "submission_to_acceptance": describe(sub_to_acc),
        "acceptance_to_publication": describe(acc_to_pub),
        "histogram_start_to_publication": _histogram(
            [v for v in start_to_pub if v is not None],
            [(0, 180, "< 6 meses"), (180, 365, "6-12 meses"), (365, 730, "1-2 anos"),
             (730, 1095, "2-3 anos"), (1095, 10**6, "> 3 anos")],
        ),
    }


def submission_metrics(db: Database) -> dict[str, Any]:
    """Tentativas de submissao, intervalos entre elas e motivos de recusa."""
    attempts = db.dicts(
        """
        SELECT a.id, a.title, a.status,
               COUNT(s.id) AS attempts,
               SUM(CASE WHEN s.decision IN ('rejeitado','desk_reject') THEN 1 ELSE 0 END) AS rejections,
               MIN(s.submitted_on) AS first_submitted_on,
               MAX(s.submitted_on) AS last_submitted_on
        FROM articles a
        JOIN submissions s ON s.article_id = a.id
        GROUP BY a.id
        ORDER BY attempts DESC, a.title
        """
    )
    gaps = db.dicts("SELECT * FROM v_resubmission_gaps ORDER BY article_id, attempt_no")
    reasons = db.dicts("SELECT * FROM v_rejection_reasons ORDER BY n DESC, reason")
    per_journal = db.dicts(
        """
        SELECT journal,
               COUNT(*) AS n,
               SUM(CASE WHEN decision = 'aceito' THEN 1 ELSE 0 END) AS accepted,
               SUM(CASE WHEN decision IN ('rejeitado','desk_reject') THEN 1 ELSE 0 END) AS rejected
        FROM submissions
        WHERE journal IS NOT NULL
        GROUP BY journal
        ORDER BY n DESC
        LIMIT 15
        """
    )
    decisions = db.dicts(
        "SELECT COALESCE(decision, 'sem_registro') AS decision, COUNT(*) AS n"
        " FROM submissions GROUP BY decision ORDER BY n DESC"
    )
    total = int(db.scalar("SELECT COUNT(*) FROM submissions") or 0)
    rejected = int(
        db.scalar("SELECT COUNT(*) FROM submissions WHERE decision IN ('rejeitado','desk_reject')") or 0
    )
    accepted = int(db.scalar("SELECT COUNT(*) FROM submissions WHERE decision = 'aceito'") or 0)
    return {
        "per_article": attempts,
        "attempts_distribution": Counter(int(a["attempts"]) for a in attempts),
        "attempts_summary": describe([a["attempts"] for a in attempts], unit="tentativas"),
        "gaps": gaps,
        "gap_summary": describe([g["days_between_submissions"] for g in gaps]),
        "decision_to_resubmission": describe([g["days_decision_to_resubmission"] for g in gaps]),
        "rejection_reasons": reasons,
        "per_journal": per_journal,
        "decisions": decisions,
        "total": total,
        "accepted": accepted,
        "rejected": rejected,
        "acceptance_rate": round(100 * accepted / total, 1) if total else 0.0,
        "rejection_rate": round(100 * rejected / total, 1) if total else 0.0,
        "desk_rejects": int(db.scalar("SELECT COUNT(*) FROM submissions WHERE desk_reject = 1") or 0),
    }


def acceptance_log(db: Database, limit: int = 40) -> list[dict]:
    """Datas de aceite mais recentes."""
    return db.dicts(
        """
        SELECT id, title, authors, journal, accepted_on, published_on, year_published,
               first_submission_on, days_submission_to_acceptance, submission_attempts
        FROM v_articles_full
        WHERE accepted_on IS NOT NULL
        ORDER BY accepted_on DESC
        LIMIT ?
        """,
        (limit,),
    )


def agenda(db: Database, window: int = config.WINDOW_YEARS) -> dict[str, Any]:
    """Calendario, atividades e distribuicao temporal."""
    events = db.dicts(
        """
        SELECT e.id, e.kind, e.title, e.description, e.start_at, e.end_at, e.all_day,
               e.status, e.location_name, e.city, e.state, e.country,
               e.latitude, e.longitude, e.url,
               rl.name AS research_line,
               i.name AS institution,
               (SELECT COUNT(*) FROM event_participants ep WHERE ep.event_id = e.id) AS n_participants
        FROM events e
        LEFT JOIN research_lines rl ON rl.id = e.research_line_id
        LEFT JOIN institutions i ON i.id = e.institution_id
        ORDER BY e.start_at
        """
    )
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    upcoming = [e for e in events if e["start_at"] >= now][:20]
    past = [e for e in events if e["start_at"] < now]
    by_kind = Counter(e["kind"] for e in events)
    by_year = Counter(e["start_at"][:4] for e in events if e["start_at"])
    heatmap = Counter(e["start_at"][:7] for e in events if e["start_at"])
    cutoff = str(TODAY.year - window + 1)
    return {
        "events": events,
        "upcoming": upcoming,
        "past_count": len(past),
        "total": len(events),
        "by_kind": [{"kind": k, "n": v} for k, v in by_kind.most_common()],
        "by_year": [{"year": y, "n": n} for y, n in sorted(by_year.items()) if y >= cutoff],
        "heatmap": [{"month": m, "n": n} for m, n in sorted(heatmap.items()) if m[:4] >= cutoff],
        "next_event": upcoming[0] if upcoming else None,
    }


def _cenario(db: Database) -> dict[str, Any]:
    from . import cenario

    return cenario.base(db)


def spatial(db: Database) -> dict[str, Any]:
    """Distribuicao geografica de atividades e colaboracoes."""
    places = db.dicts(
        """
        SELECT COALESCE(e.city, i.city, 'Nao informado') AS city,
               COALESCE(e.state, i.state) AS state,
               COALESCE(e.country, i.country, 'Brasil') AS country,
               AVG(COALESCE(e.latitude, i.latitude)) AS latitude,
               AVG(COALESCE(e.longitude, i.longitude)) AS longitude,
               COUNT(*) AS n_events,
               COUNT(DISTINCT e.kind) AS n_kinds
        FROM events e
        LEFT JOIN institutions i ON i.id = e.institution_id
        GROUP BY 1, 2, 3
        ORDER BY n_events DESC
        """
    )
    institutions = db.dicts(
        """
        SELECT i.id, i.name, i.acronym, i.city, i.state, i.country, i.latitude, i.longitude,
               (SELECT COUNT(*) FROM members m WHERE m.institution_id = i.id) AS n_members,
               (SELECT COUNT(DISTINCT aa.article_id) FROM members m
                  JOIN article_authors aa ON aa.member_id = m.id
                 WHERE m.institution_id = i.id) AS n_articles
        FROM institutions i
        ORDER BY n_articles DESC, n_members DESC
        """
    )
    return {
        "places": [p for p in places if p["city"] != "Nao informado" or p["n_events"]],
        "institutions": institutions,
        "geolocated": [p for p in places if p["latitude"] is not None],
        # Contar INSTITUICOES por pais, que era o que estava aqui, responde
        # outra pergunta -- quantas parceiras temos la -- e enche o mapa de
        # 1 onde ha dez artigos. A pergunta do mapa e "de onde saiu a
        # producao", e quem responde e `analise.paises`, a mesma funcao que
        # o Panorama usa. Uma medida so, dois consumidores.
        "countries": _paises_com_artigo(db),
    }


def _logo() -> str | None:
    from . import marca

    return marca.fonte()


def _paises_com_artigo(db: Database) -> list[dict[str, Any]]:
    from . import analise

    return [{"country": p["pais"], "n": p["n"],
             "institutions": p.get("instituicoes") or []}
            for p in analise.paises(db).get("todos", [])]


def temporal_grid(db: Database, window: int = config.WINDOW_YEARS) -> dict[str, Any]:
    """Matriz ano x mes combinando publicacoes, submissoes e atividades."""
    first_year = TODAY.year - window + 1
    def grid(sql: str) -> dict[str, int]:
        return {r["ym"]: int(r["n"]) for r in db.dicts(sql, (f"{first_year}-01",))}

    publications = grid(
        "SELECT substr(published_on,1,7) AS ym, COUNT(*) AS n FROM articles"
        " WHERE published_on IS NOT NULL AND substr(published_on,1,7) >= ? GROUP BY ym"
    )
    submissions = grid(
        "SELECT substr(submitted_on,1,7) AS ym, COUNT(*) AS n FROM submissions"
        " WHERE submitted_on IS NOT NULL AND substr(submitted_on,1,7) >= ? GROUP BY ym"
    )
    activities = grid(
        "SELECT substr(start_at,1,7) AS ym, COUNT(*) AS n FROM events"
        " WHERE substr(start_at,1,7) >= ? GROUP BY ym"
    )
    months = [f"{y:04d}-{m:02d}" for y in range(first_year, TODAY.year + 1) for m in range(1, 13)]
    return {
        "months": months,
        "years": list(range(first_year, TODAY.year + 1)),
        "publications": [publications.get(m, 0) for m in months],
        "submissions": [submissions.get(m, 0) for m in months],
        "activities": [activities.get(m, 0) for m in months],
    }


def data_quality(db: Database) -> dict[str, Any]:
    """Lacunas que o laboratorio precisa preencher nas planilhas."""
    total = int(db.scalar("SELECT COUNT(*) FROM articles") or 0)
    checks = [
        ("Artigos sem DOI", "SELECT COUNT(*) FROM articles WHERE status='publicado' AND (doi IS NULL OR doi='')"),
        ("Artigos sem data de inicio", "SELECT COUNT(*) FROM articles WHERE started_on IS NULL"),
        ("Publicados sem data de publicacao", "SELECT COUNT(*) FROM articles WHERE status='publicado' AND published_on IS NULL"),
        ("Artigos sem autoria registrada", "SELECT COUNT(*) FROM articles a WHERE NOT EXISTS (SELECT 1 FROM article_authors aa WHERE aa.article_id=a.id)"),
        ("Artigos sem linha de pesquisa", "SELECT COUNT(*) FROM articles WHERE research_line_id IS NULL"),
        ("Submissoes sem decisao", "SELECT COUNT(*) FROM submissions WHERE decision IS NULL"),
        ("Recusas sem motivo", "SELECT COUNT(*) FROM submissions WHERE decision IN ('rejeitado','desk_reject') AND rejection_reason_id IS NULL AND rejection_notes IS NULL"),
        ("Atividades sem local", "SELECT COUNT(*) FROM events WHERE city IS NULL AND location_name IS NULL"),
        ("Artigos publicados sem citacoes coletadas", "SELECT COUNT(*) FROM articles WHERE status='publicado' AND scopus_citations IS NULL AND wos_citations IS NULL"),
    ]
    return {
        "total_articles": total,
        "issues": [{"label": label, "n": int(db.scalar(sql) or 0)} for label, sql in checks],
        "last_runs": db.dicts(
            "SELECT run_at, source, target, file, rows_read, rows_written, status, message"
            " FROM ingest_log ORDER BY id DESC LIMIT 25"
        ),
    }


def overview(db: Database, pubs: dict, subs: dict, network: dict, agenda_data: dict) -> dict[str, Any]:
    counts = {
        row["status"]: int(row["n"])
        for row in db.dicts("SELECT status, COUNT(*) AS n FROM articles GROUP BY status")
    }
    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "lab_name": config.LAB_NAME,
        # embutido, e nao um endereco: o mural roda numa TV que pode estar
        # sem rede, e o instantaneo e um arquivo unico que viaja por e-mail
        "lab_logo": _logo(),
        "institution": config.LAB_INSTITUTION,
        "site": config.LAB_SITE,
        "window": config.WINDOW_YEARS,
        "n_articles": sum(counts.values()),
        "n_published": counts.get("publicado", 0),
        "n_in_progress": counts.get("em_producao", 0),
        "n_submitted": counts.get("submetido", 0) + counts.get("em_revisao", 0),
        "n_accepted": counts.get("aceito", 0),
        "n_rejected": counts.get("rejeitado", 0),
        "n_members": int(db.scalar("SELECT COUNT(*) FROM members WHERE is_external = 0") or 0),
        "n_collaborators": int(db.scalar("SELECT COUNT(*) FROM members WHERE is_external = 1") or 0),
        "n_research_lines": int(db.scalar("SELECT COUNT(*) FROM research_lines") or 0),
        "n_projects": int(db.scalar("SELECT COUNT(*) FROM projects") or 0),
        "n_projects_active": int(db.scalar(
            "SELECT COUNT(*) FROM projects WHERE status = 'em_andamento'") or 0),
        "best_h_index": int(db.scalar("SELECT COALESCE(MAX(h_index), 0) FROM members") or 0),
        "n_events": agenda_data["total"],
        "published_window": pubs["total_window"],
        "mean_per_year": pubs["mean_per_year"],
        "scopus_total": int(db.scalar("SELECT COALESCE(SUM(scopus_citations),0) FROM articles") or 0),
        "wos_total": int(db.scalar("SELECT COALESCE(SUM(wos_citations),0) FROM articles") or 0),
        "openalex_total": int(db.scalar("SELECT COALESCE(SUM(openalex_citations),0) FROM articles") or 0),
        "n_discoveries": int(db.scalar("SELECT COUNT(*) FROM discoveries WHERE status = 'pendente'") or 0),
        "acceptance_rate": subs["acceptance_rate"],
        "network_density": network["density"],
        "status_counts": [{"status": k, "n": v} for k, v in sorted(counts.items(), key=lambda kv: -kv[1])],
    }


# ----------------------------------------------------------------------
# Payload completo
# ----------------------------------------------------------------------
def article_rows(db: Database) -> list[dict]:
    """Lista achatada de artigos: base do cruzamento interativo do painel."""
    return db.dicts(
        """
        SELECT id, internal_code, title, authors, status, research_line, research_line_code,
               study_type, language, started_on, first_submission_on, accepted_on, published_on,
               year_published, journal, qualis, impact_factor, doi, url, lead_name,
               wos_citations, scopus_citations, openalex_citations,
               wos_id, scopus_id,
               submission_attempts, rejections,
               days_start_to_publication, days_submission_to_acceptance,
               days_acceptance_to_publication
        FROM v_articles_full
        ORDER BY COALESCE(year_published, 9999) DESC, title
        """
    )


def authorship_rows(db: Database) -> list[dict]:
    """Ligacao artigo-integrante, em formato compacto para o navegador."""
    return [
        {"a": r["article_id"], "m": r["member_id"], "o": r["author_order"]}
        for r in db.dicts(
            "SELECT article_id, member_id, author_order FROM article_authors"
            " WHERE member_id IS NOT NULL")
    ]


HISTORY_METRICS = ("artigos", "publicados", "em_producao", "submetidos", "submissoes",
                   "citacoes", "integrantes", "projetos", "atividades", "indice_h_maximo")


def measured_history(db: Database, limit: int = 60) -> dict[str, Any]:
    """Série histórica dos indicadores, medida a cada execução do lakehouse.

    É o que permite mostrar variação com número medido, e não estimado.
    Se o lakehouse nunca rodou, devolve vazio e o painel apenas não mostra
    as setas de variação.
    """
    try:
        from . import lake
    except ImportError:
        return {"available": False, "series": {}}
    exists = db.scalar(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'metric_snapshot'")
    if not exists:
        return {"available": False, "series": {}}
    series: dict[str, Any] = {}
    for metric in HISTORY_METRICS:
        rows = lake.metric_history(db, metric, "total", limit)
        if rows:
            series[metric] = {
                "dates": [r["snapshot_on"] for r in rows],
                "values": [r["value"] for r in rows],
                "delta_30d": lake.metric_delta(db, metric, 30)["delta"],
            }
    return {"available": bool(series), "series": series,
            "snapshots": int(db.scalar(
                "SELECT COUNT(DISTINCT snapshot_on) FROM metric_snapshot") or 0)}


def _catalog() -> dict[str, Any]:
    """Medidas e dimensões do explorador — também na exportação estática."""
    try:
        from . import lake

        return lake.catalog()
    except Exception:
        return {"measures": [], "dimensions": [], "filters": []}


def build_payload(db: Database, window: int = config.WINDOW_YEARS) -> dict[str, Any]:
    pubs = publications_by_year(db, window)
    subs = submission_metrics(db)
    network = collaboration_network(db)
    agenda_data = agenda(db, window)
    payload: dict[str, Any] = {
        "overview": overview(db, pubs, subs, network, agenda_data),
        "articles": article_rows(db),
        "authorship": authorship_rows(db),
        "research_lines": research_lines(db),
        "in_progress": articles_by_status(db, IN_PROGRESS, "COALESCE(started_on,'9999') DESC"),
        "submitted": articles_by_status(db, UNDER_REVIEW, "COALESCE(first_submission_on,'0000') DESC"),
        "accepted": articles_by_status(db, ("aceito",), "COALESCE(accepted_on,'0000') DESC"),
        "rejected": articles_by_status(db, ("rejeitado",), "COALESCE(first_submission_on,'0000') DESC"),
        "publications": pubs,
        "most_cited_scopus": most_cited(db, "scopus"),
        "most_cited_wos": most_cited(db, "wos"),
        "most_cited_scopus_recent": most_cited(db, "scopus", window=window),
        "most_cited_wos_recent": most_cited(db, "wos", window=window),
        "most_cited_openalex": most_cited(db, "openalex"),
        "most_cited_openalex_recent": most_cited(db, "openalex", window=window),
        "members": member_productivity(db),
        "researchers": researchers(db),
        "projects": projects_overview(db),
        "network": network,
        "org": organograma(db),
        "timeline": publication_timeline(db),
        "submissions": subs,
        "acceptances": acceptance_log(db),
        "agenda": agenda_data,
        "spatial": spatial(db),
        "cenario": _cenario(db),
        "temporal": temporal_grid(db, window),
        "quality": data_quality(db),
        "history": measured_history(db),
        "catalog": _catalog(),
        "discoveries": db.dicts(
            "SELECT id, source, title, authors, journal, year, citations, doi, url, status, found_at"
            " FROM discoveries WHERE status = 'pendente' ORDER BY COALESCE(citations,0) DESC,"
            " COALESCE(year,0) DESC LIMIT 60"
        ),
    }
    payload["submissions"]["attempts_distribution"] = [
        {"attempts": k, "n": v}
        for k, v in sorted(payload["submissions"]["attempts_distribution"].items())
    ]
    return payload
