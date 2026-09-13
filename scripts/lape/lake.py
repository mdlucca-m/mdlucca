"""Lakehouse do LAPE — três camadas sobre o mesmo banco.

    BRONZE   data/lake/bronze/<data>/     arquivo cru, como chegou, com hash
    PRATA    data/db.sqlite (schema.sql)  dado operacional, normalizado
    OURO     tabelas fact_/dim_ + Parquet modelo dimensional para consulta

Por que separar
  A camada bronze existe para poder refazer tudo: se amanhã o importador
  mudar, a planilha daquele dia continua guardada, com sha256, para
  reprocessar. A camada ouro existe para responder rápido: um cruzamento
  "medida x recorte" vira um JOIN, sem percorrer o modelo operacional.
  Apagar bronze ou ouro nunca perde dado — só a prata é fonte de verdade.

Histórico
  `metric_snapshot` guarda o valor dos indicadores a cada execução. É o que
  permite dizer "subiu tanto desde o mês passado" com número medido, e não
  estimado. Sobrevive à reconstrução da camada ouro.

Uso
    python3 scripts/lape_agent.py lake                 # bronze + ouro + snapshot
    python3 scripts/lape_agent.py lake --exportar      # também grava Parquet/CSV
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from . import config
from .db import Database
from .util import norm_key

# O lake vive ao lado do banco. Em contêiner, LAPE_DB aponta para o volume,
# então bronze e ouro persistem junto com a fonte de verdade — e não somem
# quando a imagem é reconstruída.
LAKE_DIR = config.DB_PATH.parent / "lake"
BRONZE_DIR = LAKE_DIR / "bronze"
GOLD_DIR = LAKE_DIR / "gold"
GOLD_SCHEMA = config.SQL_DIR / "gold.sql"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

# Célula agregada de uma pessoa só É aquela pessoa: a média de n=1 é o
# valor dela. Abaixo deste n as estatísticas saem nulas e sobra o n, para
# que a contagem continue honesta sem que o valor de ninguém apareça.
# Isto não é excesso de zelo: a camada ouro mora em data/db.sqlite, que é
# um arquivo versionado.
N_MINIMO_DA_CELULA = 3


# ----------------------------------------------------------------------
# Esquema
# ----------------------------------------------------------------------
def ensure_schema(db: Database) -> None:
    """Aplica sql/gold.sql.

    O arquivo é idempotente por construção: derruba e recria as tabelas
    derivadas (fact_/dim_) e cria com IF NOT EXISTS as que guardam
    histórico (metric_snapshot, lake_manifest), que nunca são perdidas.
    """
    if not GOLD_SCHEMA.exists():
        raise FileNotFoundError(f"esquema da camada ouro não encontrado: {GOLD_SCHEMA}")
    db.conn.executescript(GOLD_SCHEMA.read_text(encoding="utf-8"))
    db.conn.commit()


def _ready(db: Database) -> None:
    """Garante o esquema sem recriar tudo a cada chamada."""
    exists = db.scalar(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'lake_manifest'")
    if not exists:
        ensure_schema(db)


# ----------------------------------------------------------------------
# BRONZE — preserva o arquivo cru
# ----------------------------------------------------------------------
def _rel(path: Path) -> str:
    """Caminho relativo ao repositório quando faz sentido, absoluto quando não.

    Em produção o lake fica no volume (/dados/lake), fora da árvore do
    projeto — e `relative_to` levanta erro nesse caso.
    """
    try:
        return str(Path(path).relative_to(config.ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_bronze(db: Database, raw_dir: Path = config.RAW_DIR,
                   verbose: bool = True) -> dict[str, Any]:
    """Copia cada arquivo de entrada para a camada bronze, uma vez por conteúdo.

    A deduplicação é por sha256: reexecutar sem trocar as planilhas não
    cria cópia nova. Trocar uma linha da planilha cria — e as duas versões
    ficam disponíveis para comparação.
    """
    _ready(db)
    if not raw_dir.exists():
        return {"captured": 0, "skipped": 0}

    stamp = date.today().isoformat()
    target_dir = BRONZE_DIR / stamp
    known = {row["sha256"] for row in db.dicts(
        "SELECT sha256 FROM lake_manifest WHERE layer = 'bronze' AND sha256 IS NOT NULL")}

    captured = skipped = 0
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("~$") or path.name == ".gitkeep":
            continue
        digest = sha256(path)
        if digest in known:
            skipped += 1
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        stored = target_dir / f"{digest[:12]}_{path.name}"
        shutil.copy2(path, stored)
        db.execute(
            "INSERT INTO lake_manifest (layer, source_path, stored_path, sha256, bytes, note)"
            " VALUES ('bronze', ?, ?, ?, ?, ?)",
            (_rel(path), _rel(stored), digest, path.stat().st_size, "captura automática"),
        )
        known.add(digest)
        captured += 1

    db.conn.commit()
    if verbose:
        print(f"  bronze: {captured} arquivo(s) novo(s), {skipped} já preservado(s)")
    return {"captured": captured, "skipped": skipped, "dir": str(target_dir)}


# ----------------------------------------------------------------------
# OURO — modelo dimensional
# ----------------------------------------------------------------------
def build_gold(db: Database, verbose: bool = True) -> dict[str, int]:
    """Reconstrói as tabelas fato/dimensão a partir da camada prata."""
    ensure_schema(db)

    counts: dict[str, int] = {}
    counts["dim_date"] = _build_dim_date(db)
    counts["dim_line"] = db.execute(
        "INSERT INTO dim_line (line_id, code, name, coordinator, active)"
        " SELECT id, code, name, coordinator, active FROM research_lines").rowcount
    counts["dim_researcher"] = db.execute(
        "INSERT INTO dim_researcher (member_id, full_name, short_name, name_key, role, degree,"
        "  research_line, institution, is_external, active, h_index, h_index_source, i10_index,"
        "  citations_total, n_projects, orcid, lattes_id)"
        " SELECT id, full_name, short_name, name_key, role, degree, research_line, institution,"
        "        is_external, active, h_index, h_index_source, i10_index, citations_total,"
        "        n_projects, orcid, lattes_id"
        " FROM v_researcher").rowcount
    counts["dim_project"] = db.execute(
        "INSERT INTO dim_project (project_id, code, name, funder, status, coordinator,"
        "  started_on, ended_on, amount)"
        " SELECT id, code, name, funder, status, coordinator, started_on, ended_on, amount"
        " FROM v_projects").rowcount
    counts["dim_journal"] = _build_dim_journal(db)
    counts["fact_article"] = _build_fact_article(db)
    counts["fact_authorship"] = db.execute(
        "INSERT OR REPLACE INTO fact_authorship"
        "  (article_id, member_id, author_order, is_first_author, is_corresponding, is_external)"
        " SELECT article_id, member_id, author_order,"
        "        CASE WHEN author_order = 1 THEN 1 ELSE 0 END, is_corresponding, is_external"
        " FROM article_authors WHERE member_id IS NOT NULL").rowcount
    counts["fact_submission"] = _build_fact_submission(db)
    counts["fact_citation"] = _build_fact_citation(db)
    counts["fact_event"] = db.execute(
        "INSERT INTO fact_event (event_id, kind, title, start_date, year, year_month, city,"
        "  state, country, latitude, longitude, research_line, n_participants)"
        " SELECT e.id, e.kind, e.title, substr(e.start_at, 1, 10),"
        "        CAST(substr(e.start_at, 1, 4) AS INTEGER), substr(e.start_at, 1, 7),"
        "        e.city, e.state, e.country, e.latitude, e.longitude, rl.name,"
        "        (SELECT COUNT(*) FROM event_participants ep WHERE ep.event_id = e.id)"
        " FROM events e LEFT JOIN research_lines rl ON rl.id = e.research_line_id").rowcount

    counts["dim_instrument"] = _build_dim_instrument(db)
    counts["dim_protocol"] = _build_dim_protocol(db)
    counts["fact_measurement"] = _build_fact_measurement(db)
    counts["dim_agency"] = _build_dim_agency(db)
    counts["fact_funding"] = _build_fact_funding(db)

    db.conn.commit()
    db.log_ingest("lake", target="gold", rows_written=sum(counts.values()),
                  message=", ".join(f"{k}={v}" for k, v in counts.items()))
    if verbose:
        print("  ouro: " + " · ".join(f"{k.replace('_', ' ')} {v}" for k, v in counts.items()))
    return counts


def _build_dim_date(db: Database) -> int:
    """Calendário cobrindo todas as datas que aparecem no banco."""
    bounds = db.dicts(
        "SELECT MIN(d) AS lo, MAX(d) AS hi FROM ("
        "  SELECT started_on AS d FROM articles WHERE started_on IS NOT NULL"
        "  UNION SELECT published_on FROM articles WHERE published_on IS NOT NULL"
        "  UNION SELECT submitted_on FROM submissions WHERE submitted_on IS NOT NULL"
        "  UNION SELECT substr(start_at, 1, 10) FROM events)")
    low = (bounds[0]["lo"] or date.today().isoformat())[:10]
    high = (bounds[0]["hi"] or date.today().isoformat())[:10]
    start_year = max(1990, int(low[:4]))
    end_year = min(2100, max(int(high[:4]), date.today().year))

    rows = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    current = date(year, month, day)
                except ValueError:
                    continue
                rows.append((current.isoformat(), year, (month - 1) // 3 + 1, month,
                             MESES[month - 1], f"{year:04d}-{month:02d}", day,
                             current.weekday()))
    db.conn.executemany(
        "INSERT OR REPLACE INTO dim_date (date_key, year, quarter, month, month_name,"
        " year_month, day, weekday) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
    return len(rows)


def _build_dim_journal(db: Database) -> int:
    seen: dict[str, dict] = {}
    for row in db.dicts(
        "SELECT journal, issn, qualis, impact_factor FROM articles WHERE journal IS NOT NULL"
        " UNION ALL SELECT journal, issn, NULL, NULL FROM submissions WHERE journal IS NOT NULL"
    ):
        key = norm_key(row["journal"])[:80]
        if not key:
            continue
        current = seen.setdefault(key, {"name": row["journal"], "issn": None,
                                        "qualis": None, "impact_factor": None})
        for field in ("issn", "qualis", "impact_factor"):
            if current[field] is None and row[field] is not None:
                current[field] = row[field]
    db.conn.executemany(
        "INSERT OR REPLACE INTO dim_journal (journal_key, name, issn, qualis, impact_factor)"
        " VALUES (?, ?, ?, ?, ?)",
        [(k, v["name"], v["issn"], v["qualis"], v["impact_factor"]) for k, v in seen.items()])
    return len(seen)


def _build_fact_article(db: Database) -> int:
    rows = db.dicts(
        """
        SELECT a.*, rl.name AS research_line_name,
               (SELECT COUNT(*) FROM article_authors aa WHERE aa.article_id = a.id) AS n_authors,
               (SELECT COUNT(*) FROM article_authors aa JOIN members m ON m.id = aa.member_id
                 WHERE aa.article_id = a.id AND m.is_external = 0) AS n_internal,
               (SELECT COUNT(*) FROM submissions s WHERE s.article_id = a.id) AS attempts,
               (SELECT COUNT(*) FROM submissions s WHERE s.article_id = a.id
                  AND s.decision IN ('rejeitado', 'desk_reject')) AS rejections
        FROM articles a
        LEFT JOIN research_lines rl ON rl.id = a.research_line_id
        """
    )
    payload = []
    for row in rows:
        payload.append((
            row["id"], row["internal_code"], row["title"], row["status"],
            row["research_line_id"], row["research_line_name"],
            norm_key(row["journal"])[:80] if row["journal"] else None, row["journal"],
            row["qualis"], row["study_type"], row["language"],
            row["lead_member_id"], row["lead_name"],
            row["started_on"], row["first_submission_on"], row["accepted_on"], row["published_on"],
            row["year_published"],
            int(row["started_on"][:4]) if row["started_on"] else None,
            _days(row["started_on"], row["published_on"]),
            _days(row["first_submission_on"], row["accepted_on"]),
            _days(row["accepted_on"], row["published_on"]),
            _days(row["started_on"], date.today().isoformat()) if row["status"] == "em_producao" else None,
            row["attempts"], row["rejections"],
            row["wos_citations"], row["scopus_citations"], row["openalex_citations"],
            max(row["wos_citations"] or 0, row["scopus_citations"] or 0,
                row["openalex_citations"] or 0),
            row["n_authors"], row["n_internal"], row["doi"], row["source"],
        ))
    columns = [
        "article_id", "internal_code", "title", "status", "line_id", "research_line",
        "journal_key", "journal", "qualis", "study_type", "language",
        "lead_member_id", "lead_name", "started_on", "first_submission_on", "accepted_on",
        "published_on", "year_published", "year_started", "days_start_to_publication",
        "days_submission_to_acceptance", "days_acceptance_to_publication", "days_open",
        "submission_attempts", "rejections", "wos_citations", "scopus_citations",
        "openalex_citations", "best_citations", "n_authors", "n_internal_authors",
        "doi", "source",
    ]
    db.conn.executemany(
        f"INSERT INTO fact_article ({', '.join(columns)})"
        f" VALUES ({', '.join('?' * len(columns))})", payload)
    return len(payload)


def _build_fact_submission(db: Database) -> int:
    rows = db.dicts(
        """
        SELECT s.*, r.label AS reason, r.category AS reason_category,
               rl.name AS research_line,
               prev.submitted_on AS prev_submitted, prev.decision_on AS prev_decision
        FROM submissions s
        LEFT JOIN rejection_reasons r ON r.id = s.rejection_reason_id
        LEFT JOIN articles a ON a.id = s.article_id
        LEFT JOIN research_lines rl ON rl.id = a.research_line_id
        LEFT JOIN submissions prev
               ON prev.article_id = s.article_id AND prev.attempt_no = s.attempt_no - 1
        ORDER BY s.article_id, s.attempt_no
        """
    )
    payload = [(
        row["id"], row["article_id"], row["attempt_no"],
        norm_key(row["journal"])[:80] if row["journal"] else None, row["journal"],
        row["submitted_on"], row["decision_on"], row["decision"],
        row["reason"] or row["rejection_notes"], row["reason_category"], row["desk_reject"],
        _days(row["submitted_on"], row["decision_on"]),
        _days(row["prev_submitted"], row["submitted_on"]),
        _days(row["prev_decision"], row["submitted_on"]),
        int(row["submitted_on"][:4]) if row["submitted_on"] else None,
        row["research_line"],
    ) for row in rows]
    columns = [
        "submission_id", "article_id", "attempt_no", "journal_key", "journal",
        "submitted_on", "decision_on", "decision", "rejection_reason", "rejection_category",
        "desk_reject", "days_to_decision", "days_since_previous",
        "days_decision_to_resubmit", "year_submitted", "research_line",
    ]
    db.conn.executemany(
        f"INSERT INTO fact_submission ({', '.join(columns)})"
        f" VALUES ({', '.join('?' * len(columns))})", payload)
    return len(payload)


def _build_fact_citation(db: Database) -> int:
    """Snapshots de citação com a variação desde a medição anterior."""
    rows = db.dicts(
        "SELECT article_id, source, snapshot_on, citations FROM citation_snapshots"
        " ORDER BY article_id, source, snapshot_on")
    payload = []
    previous: dict[tuple[int, str], int] = {}
    for row in rows:
        key = (row["article_id"], row["source"])
        delta = None if key not in previous else row["citations"] - previous[key]
        previous[key] = row["citations"]
        payload.append((row["article_id"], row["source"], row["snapshot_on"],
                        row["citations"], delta))
    db.conn.executemany("INSERT OR REPLACE INTO fact_citation VALUES (?, ?, ?, ?, ?)", payload)
    return len(payload)


def _days(start: str | None, end: str | None) -> int | None:
    if not start or not end:
        return None
    try:
        a = date.fromisoformat(str(start)[:10])
        b = date.fromisoformat(str(end)[:10])
    except ValueError:
        return None
    return (b - a).days


# ----------------------------------------------------------------------
# Histórico de indicadores
# ----------------------------------------------------------------------
SNAPSHOT_METRICS: dict[str, str] = {
    "artigos": "SELECT COUNT(*) FROM fact_article",
    "publicados": "SELECT COUNT(*) FROM fact_article WHERE status = 'publicado'",
    "em_producao": "SELECT COUNT(*) FROM fact_article WHERE status = 'em_producao'",
    "submetidos": "SELECT COUNT(*) FROM fact_article WHERE status IN ('submetido','em_revisao')",
    "rejeitados": "SELECT COUNT(*) FROM fact_article WHERE status = 'rejeitado'",
    "submissoes": "SELECT COUNT(*) FROM fact_submission",
    "citacoes": "SELECT COALESCE(SUM(best_citations), 0) FROM fact_article",
    "integrantes": "SELECT COUNT(*) FROM dim_researcher WHERE is_external = 0",
    "projetos": "SELECT COUNT(*) FROM dim_project",
    "atividades": "SELECT COUNT(*) FROM fact_event",
    "indice_h_maximo": "SELECT COALESCE(MAX(h_index), 0) FROM dim_researcher",
    "dias_ate_publicar_mediana": (
        "SELECT COALESCE(AVG(days_start_to_publication), 0) FROM fact_article"
        " WHERE days_start_to_publication IS NOT NULL"),

    # Bancada e fomento. Sao CONTAGENS e TOTAIS, nunca um valor medido de
    # alguem: o historico e publico dentro do laboratorio, e "quantas
    # medicoes ja foram feitas" nao conta nada sobre ninguem.
    "medicoes": "SELECT COALESCE(SUM(n), 0) FROM fact_measurement",
    # Sem guarda de tabela ausente: a consulta falha, e quem trata isso e
    # o try de take_snapshot. Um EXISTS aqui NAO protegeria -- o FROM e
    # resolvido antes do WHERE --, e guarda que nao guarda e pior do que
    # nenhuma, porque parece protecao.
    "participantes_medidos": "SELECT COUNT(DISTINCT participante_id) FROM coletas",
    "propostas": "SELECT COUNT(*) FROM fact_funding",
    "propostas_aprovadas": "SELECT COALESCE(SUM(is_approved), 0) FROM fact_funding",
    "captado": "SELECT COALESCE(SUM(amount_granted), 0) FROM fact_funding",
    "editais_abertos": (
        "SELECT COUNT(*) FROM editais WHERE arquivado = 0"
        "   AND (fecha_em IS NULL OR fecha_em >= date('now'))"),
}


# ----------------------------------------------------------------------
# Bancada e fomento
# ----------------------------------------------------------------------
def _tem_tabela(db: Database, nome: str) -> bool:
    """A camada ouro nao pode exigir que a prata ja tenha migrado tudo.

    Um banco antigo, aberto antes de a bancada existir, nao tem `coletas`
    -- e a reconstrucao do ouro nao pode quebrar por isso. Devolve zero
    linhas em vez de explodir.
    """
    return bool(db.dicts(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (nome,)))


def _build_dim_instrument(db: Database) -> int:
    if not _tem_tabela(db, "instrumentos"):
        return 0
    return db.execute(
        "INSERT INTO dim_instrument"
        "  (instrument_id, code, name, unit, direction, min_value, max_value, active)"
        " SELECT id, code, nome, unidade, direcao, minimo, maximo, ativo"
        " FROM instrumentos").rowcount


def _build_dim_protocol(db: Database) -> int:
    """Uma linha por protocolo E por momento.

    O protocolo sem momento tambem entra (chave `<id>:-`), porque existe
    medida coletada fora de um momento declarado, e ela nao pode sumir da
    camada ouro so por nao ter etapa.
    """
    if not _tem_tabela(db, "protocolos"):
        return 0
    linhas = db.execute(
        "INSERT INTO dim_protocol"
        "  (protocol_key, protocol_id, protocol_code, protocol_name,"
        "   moment_id, moment_name, moment_order, days_after)"
        " SELECT p.id || ':' || m.id, p.id, p.code, p.nome,"
        "        m.id, m.nome, m.ordem, m.dias_apos"
        "   FROM protocolos p JOIN momentos m ON m.protocolo_id = p.id").rowcount
    linhas += db.execute(
        "INSERT INTO dim_protocol"
        "  (protocol_key, protocol_id, protocol_code, protocol_name,"
        "   moment_id, moment_name, moment_order, days_after)"
        " SELECT p.id || ':-', p.id, p.code, p.nome, NULL, 'Sem momento', NULL, NULL"
        "   FROM protocolos p").rowcount
    return linhas


def _build_fact_measurement(db: Database) -> int:
    """Medida AGREGADA por protocolo, momento, instrumento, subescala e grupo.

    Nao existe aqui uma linha que seja de alguem -- ver o comentario da
    tabela em sql/gold.sql. A supressao de celula pequena e feita em
    Python, e nao em SQL, porque precisa apagar as estatisticas MANTENDO
    o n: um CASE no SELECT faria isso tambem, mas espalhado por cinco
    colunas, e a regra ficaria facil de quebrar sem querer.
    """
    if not _tem_tabela(db, "coletas"):
        return 0
    linhas = db.dicts(
        "SELECT p.protocolo_id AS protocolo_id,"
        "       p.protocolo_id || ':' || COALESCE(c.momento_id, '-') AS chave,"
        "       c.momento_id AS momento_id, c.instrumento_id AS instrumento_id,"
        "       COALESCE(c.subescala, '') AS subescala,"
        "       COALESCE(p.grupo, 'sem grupo') AS grupo,"
        "       COUNT(*) AS n, AVG(c.valor) AS media,"
        "       MIN(c.valor) AS minimo, MAX(c.valor) AS maximo,"
        "       SUM(c.valor) AS soma, SUM(c.valor * c.valor) AS soma2"
        "  FROM coletas c JOIN participantes p ON p.id = c.participante_id"
        " WHERE c.valor IS NOT NULL"
        " GROUP BY chave, c.instrumento_id, subescala, grupo")
    gravadas = 0
    for linha in linhas:
        n = int(linha["n"])
        pequena = n < N_MINIMO_DA_CELULA
        dp = None
        if not pequena and n > 1:
            # variancia amostral a partir das somas, sem trazer os valores
            var = (linha["soma2"] - linha["soma"] ** 2 / n) / (n - 1)
            dp = round(var ** 0.5, 4) if var > 0 else 0.0
        db.execute(
            "INSERT OR REPLACE INTO fact_measurement"
            "  (protocol_key, protocol_id, moment_id, instrument_id, subscale,"
            "   group_name, n, mean, sd, min_value, max_value, suppressed)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (linha["chave"], linha["protocolo_id"], linha["momento_id"],
             linha["instrumento_id"], linha["subescala"] or "", linha["grupo"], n,
             None if pequena else round(linha["media"], 4), dp,
             None if pequena else linha["minimo"],
             None if pequena else linha["maximo"], 1 if pequena else 0))
        gravadas += 1
    return gravadas


def _build_dim_agency(db: Database) -> int:
    if not _tem_tabela(db, "editais"):
        return 0
    return db.execute(
        "INSERT OR REPLACE INTO dim_agency (agency_key, agency)"
        " SELECT DISTINCT LOWER(TRIM(agencia)), TRIM(agencia) FROM editais"
        "  WHERE agencia IS NOT NULL AND TRIM(agencia) <> ''").rowcount


def _build_fact_funding(db: Database) -> int:
    if not _tem_tabela(db, "submissoes_fomento"):
        return 0
    linhas = db.dicts(
        "SELECT s.*, e.nome AS edital, e.agencia, e.modalidade,"
        "       m.full_name AS proponente, l.name AS linha"
        "  FROM submissoes_fomento s"
        "  LEFT JOIN editais e ON e.id = s.edital_id"
        "  LEFT JOIN members m ON m.id = s.proponente_id"
        "  LEFT JOIN research_lines l ON l.id = s.linha_id")
    gravadas = 0
    for x in linhas:
        decidida = x["situacao"] in ("aprovada", "recusada")
        agencia = (x["agencia"] or "").strip()
        db.execute(
            "INSERT OR REPLACE INTO fact_funding"
            "  (submission_id, call_id, call_name, agency_key, agency, modality,"
            "   project_id, line_id, research_line, proposer_id, proposer_name, title,"
            "   submitted_on, decided_on, situation, is_decided, is_approved,"
            "   amount_asked, amount_granted, days_to_decide, year_submitted, year_decided)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (x["id"], x["edital_id"], x["edital"], agencia.lower() or None,
             agencia or None, x["modalidade"], x["project_id"], x["linha_id"], x["linha"],
             x["proponente_id"], x["proponente"], x["titulo"],
             x["submetido_em"], x["decidido_em"], x["situacao"],
             1 if decidida else 0, 1 if x["situacao"] == "aprovada" else 0,
             x["valor_pedido"], x["valor_aprovado"],
             _days(x["submetido_em"], x["decidido_em"]),
             _ano(x["submetido_em"]), _ano(x["decidido_em"])))
        gravadas += 1
    return gravadas


def _ano(valor: Any) -> int | None:
    try:
        return int(str(valor)[:4]) if valor else None
    except (TypeError, ValueError):
        return None


def take_snapshot(db: Database, when: str | None = None, verbose: bool = True) -> dict[str, Any]:
    """Grava o valor de cada indicador hoje — total e por linha de pesquisa."""
    _ready(db)
    stamp = when or date.today().isoformat()
    payload: list[tuple] = []
    for metric, sql in SNAPSHOT_METRICS.items():
        try:
            valor = float(db.scalar(sql) or 0)
        except Exception:
            # Banco anterior a bancada ou ao fomento nao tem a tabela. Um
            # indicador que ainda nao existe nao pode derrubar o historico
            # inteiro dos que existem -- e gravar zero seria mentira, entao
            # ele simplesmente nao entra na serie.
            continue
        payload.append((stamp, metric, "total", "total", valor))
    for row in db.dicts(
        "SELECT COALESCE(research_line, 'Sem linha') AS linha, COUNT(*) AS n,"
        "       SUM(CASE WHEN status = 'publicado' THEN 1 ELSE 0 END) AS publicados"
        " FROM fact_article GROUP BY linha"
    ):
        payload.append((stamp, "artigos", "linha", row["linha"], float(row["n"])))
        payload.append((stamp, "publicados", "linha", row["linha"], float(row["publicados"] or 0)))

    db.conn.executemany(
        "INSERT OR REPLACE INTO metric_snapshot (snapshot_on, metric, dimension, dim_value, value)"
        " VALUES (?, ?, ?, ?, ?)", payload)
    db.conn.commit()
    if verbose:
        print(f"  histórico: {len(payload)} indicador(es) registrados em {stamp}")
    return {"snapshot_on": stamp, "metrics": len(payload)}


def metric_history(db: Database, metric: str, dimension: str = "total",
                   limit: int = 60) -> list[dict]:
    _ready(db)
    return db.dicts(
        "SELECT snapshot_on, dim_value, value FROM metric_snapshot"
        " WHERE metric = ? AND dimension = ? ORDER BY snapshot_on DESC LIMIT ?",
        (metric, dimension, limit))[::-1]


def metric_delta(db: Database, metric: str, days: int = 30) -> dict[str, Any]:
    """Variação do indicador em relação à medição mais próxima de N dias atrás."""
    rows = metric_history(db, metric, "total", 400)
    if not rows:
        return {"metric": metric, "current": None, "previous": None, "delta": None}
    current = rows[-1]
    target = (date.fromisoformat(current["snapshot_on"]).toordinal() - days)
    previous = min(
        rows[:-1],
        key=lambda r: abs(date.fromisoformat(r["snapshot_on"]).toordinal() - target),
        default=None)
    return {
        "metric": metric,
        "current": current["value"],
        "current_on": current["snapshot_on"],
        "previous": previous["value"] if previous else None,
        "previous_on": previous["snapshot_on"] if previous else None,
        "delta": (current["value"] - previous["value"]) if previous else None,
    }


# ----------------------------------------------------------------------
# Consulta analítica: medida × recorte
# ----------------------------------------------------------------------
# Só o que está nestas listas pode ser consultado. O parâmetro do usuário
# nunca vira SQL: ele escolhe uma chave, e a chave traz a expressão pronta.
DIMENSIONS: dict[str, dict[str, str]] = {
    "linha":       {"sql": "COALESCE(a.research_line, 'Sem linha')", "label": "Linha de pesquisa"},
    "status":      {"sql": "a.status", "label": "Situação"},
    "ano":         {"sql": "CAST(COALESCE(a.year_published, a.year_started) AS TEXT)", "label": "Ano"},
    "ano_publicacao": {"sql": "CAST(a.year_published AS TEXT)", "label": "Ano de publicação"},
    "periodico":   {"sql": "COALESCE(a.journal, 'Sem periódico')", "label": "Periódico"},
    "qualis":      {"sql": "COALESCE(a.qualis, 'Sem Qualis')", "label": "Qualis"},
    "tipo_estudo": {"sql": "COALESCE(a.study_type, 'Não informado')", "label": "Tipo de estudo"},
    "responsavel": {"sql": "COALESCE(a.lead_name, 'Sem responsável')", "label": "Responsável"},
    "idioma":      {"sql": "COALESCE(a.language, 'Não informado')", "label": "Idioma"},
    "fonte":       {"sql": "COALESCE(a.source, 'planilha')", "label": "Origem do registro"},
    "total":       {"sql": "'Total'", "label": "Total"},
}

MEASURES: dict[str, dict[str, Any]] = {
    "artigos":        {"sql": "COUNT(*)", "label": "Artigos", "unit": "artigos"},
    "publicados":     {"sql": "SUM(CASE WHEN a.status = 'publicado' THEN 1 ELSE 0 END)",
                       "label": "Publicados", "unit": "artigos"},
    "submetidos":     {"sql": "SUM(CASE WHEN a.status IN ('submetido','em_revisao') THEN 1 ELSE 0 END)",
                       "label": "Submetidos", "unit": "artigos"},
    "em_producao":    {"sql": "SUM(CASE WHEN a.status = 'em_producao' THEN 1 ELSE 0 END)",
                       "label": "Em produção", "unit": "artigos"},
    "citacoes":       {"sql": "COALESCE(SUM(a.best_citations), 0)",
                       "label": "Citações", "unit": "citações"},
    "citacoes_media": {"sql": "ROUND(AVG(a.best_citations), 2)",
                       "label": "Citações por artigo", "unit": "citações", "somavel": False},
    "tentativas":     {"sql": "COALESCE(SUM(a.submission_attempts), 0)",
                       "label": "Tentativas de submissão", "unit": "tentativas"},
    "recusas":        {"sql": "COALESCE(SUM(a.rejections), 0)", "label": "Recusas", "unit": "recusas"},
    "dias_ate_publicar": {"sql": "ROUND(AVG(a.days_start_to_publication), 1)",
                          "label": "Dias do início à publicação", "unit": "dias", "somavel": False},
    "dias_ate_aceite":   {"sql": "ROUND(AVG(a.days_submission_to_acceptance), 1)",
                          "label": "Dias da submissão ao aceite", "unit": "dias", "somavel": False},
    "autores_medio":  {"sql": "ROUND(AVG(a.n_authors), 2)", "label": "Autores por artigo",
                       "unit": "autores", "somavel": False},
}

FILTERS: dict[str, str] = {
    "linha": "a.research_line = ?",
    "status": "a.status = ?",
    "ano": "CAST(a.year_published AS TEXT) = ?",
    "periodico": "a.journal = ?",
    "qualis": "a.qualis = ?",
    "responsavel": "a.lead_name = ?",
    "integrante": "a.article_id IN (SELECT article_id FROM fact_authorship WHERE member_id = ?)",
    "de": "COALESCE(a.published_on, a.started_on) >= ?",
    "ate": "COALESCE(a.published_on, a.started_on) <= ?",
}

# ----------------------------------------------------------------------
# Os tres conjuntos que o explorador alcanca
# ----------------------------------------------------------------------
# Ate aqui `query` respondia por UM fato -- o artigo -- com o FROM escrito
# na mao. Medida de participante e dinheiro de edital ficavam de fora, e
# nao por decisao: por nao haver onde encaixa-los. DATASETS da a cada
# dominio o seu proprio conjunto de medidas, recortes e filtros, e o SQL
# continua sendo montado num lugar so.
#
# `artigos` e o padrao, e as constantes MEASURES/DIMENSIONS/FILTERS
# continuam sendo as dele: quem ja chamava `query(medida, por)` nao muda.

MEDIDAS_BANCADA: dict[str, dict[str, Any]] = {
    "medicoes":   {"sql": "COALESCE(SUM(f.n), 0)", "label": "Medições", "unit": "medições"},
    "media":      {"sql": "ROUND(AVG(f.mean), 3)", "label": "Média do valor", "unit": "",
                 "somavel": False},
    "desvio":     {"sql": "ROUND(AVG(f.sd), 3)", "label": "Desvio-padrão médio", "unit": "",
                 "somavel": False},
    "celulas":    {"sql": "COUNT(*)", "label": "Células", "unit": "células"},
    "suprimidas": {"sql": "SUM(f.suppressed)", "label": "Células suprimidas",
                   "unit": "células"},
}
RECORTES_BANCADA: dict[str, dict[str, str]] = {
    "protocolo":  {"sql": "d.protocol_name", "label": "Protocolo"},
    "momento":    {"sql": "COALESCE(d.moment_name, 'Sem momento')", "label": "Momento"},
    "instrumento": {"sql": "i.name", "label": "Instrumento"},
    "subescala":  {"sql": "CASE WHEN COALESCE(f.subscale, '') = '' THEN 'Escala única'"
                          " ELSE f.subscale END", "label": "Subescala"},
    "grupo":      {"sql": "COALESCE(f.group_name, 'sem grupo')", "label": "Grupo"},
    "total":      {"sql": "'Total'", "label": "Total"},
}
FILTROS_BANCADA: dict[str, str] = {
    "protocolo": "d.protocol_name = ?",
    "instrumento": "i.name = ?",
    "momento": "d.moment_name = ?",
    "grupo": "f.group_name = ?",
}

MEDIDAS_FOMENTO: dict[str, dict[str, Any]] = {
    "propostas":  {"sql": "COUNT(*)", "label": "Propostas", "unit": "propostas"},
    "aprovadas":  {"sql": "SUM(a.is_approved)", "label": "Aprovadas", "unit": "propostas"},
    "julgadas":   {"sql": "SUM(a.is_decided)", "label": "Julgadas", "unit": "propostas"},
    "captado":    {"sql": "COALESCE(SUM(a.amount_granted), 0)", "label": "Valor aprovado",
                   "unit": "R$"},
    "pedido":     {"sql": "COALESCE(SUM(a.amount_asked), 0)", "label": "Valor pedido",
                   "unit": "R$"},
    # Aprovadas sobre JULGADAS, e nunca sobre o total: quem ainda nao foi
    # julgado nao e recusa. E a mesma regra do modulo de fomento -- se as
    # duas divergirem, a tela e o lake passam a discordar sobre o mesmo
    # numero, e ninguem sabe qual esta certo.
    "taxa":       {"sql": "CASE WHEN SUM(a.is_decided) > 0 THEN"
                          " ROUND(100.0 * SUM(a.is_approved) / SUM(a.is_decided), 1) END",
                   "label": "Taxa de aprovação", "unit": "%", "somavel": False},
    "dias_decisao": {"sql": "ROUND(AVG(a.days_to_decide), 1)",
                     "label": "Dias até a decisão", "unit": "dias", "somavel": False},
}
RECORTES_FOMENTO: dict[str, dict[str, str]] = {
    "agencia":   {"sql": "COALESCE(a.agency, 'Sem agência')", "label": "Agência"},
    "edital":    {"sql": "COALESCE(a.call_name, 'Sem edital')", "label": "Edital"},
    "situacao":  {"sql": "a.situation", "label": "Situação"},
    "linha":     {"sql": "COALESCE(a.research_line, 'Sem linha')", "label": "Linha de pesquisa"},
    "modalidade": {"sql": "COALESCE(a.modality, 'Não informada')", "label": "Modalidade"},
    "proponente": {"sql": "COALESCE(a.proposer_name, 'Sem proponente')", "label": "Proponente"},
    "ano":       {"sql": "CAST(COALESCE(a.year_decided, a.year_submitted) AS TEXT)",
                  "label": "Ano"},
    "total":     {"sql": "'Total'", "label": "Total"},
}
FILTROS_FOMENTO: dict[str, str] = {
    "agencia": "a.agency = ?",
    "situacao": "a.situation = ?",
    "linha": "a.research_line = ?",
    "ano": "CAST(COALESCE(a.year_decided, a.year_submitted) AS TEXT) = ?",
    "de": "COALESCE(a.decided_on, a.submitted_on) >= ?",
    "ate": "COALESCE(a.decided_on, a.submitted_on) <= ?",
}

DATASETS: dict[str, dict[str, Any]] = {
    "artigos": {
        "label": "Artigos", "from": "fact_article a",
        "measures": MEASURES, "dimensions": DIMENSIONS, "filters": FILTERS,
    },
    "medidas": {
        "label": "Medidas da bancada",
        "from": ("fact_measurement f"
                 " JOIN dim_protocol d ON d.protocol_key = f.protocol_key"
                 " JOIN dim_instrument i ON i.instrument_id = f.instrument_id"),
        "measures": MEDIDAS_BANCADA, "dimensions": RECORTES_BANCADA,
        "filters": FILTROS_BANCADA,
        # A bancada e da coordenacao em toda parte do sistema; aqui nao
        # seria diferente so por ser o lake.
        "restrito": True,
        "nota": "valores agregados: não há linha por participante, e célula "
                "com menos de %d medições sai sem estatística" % N_MINIMO_DA_CELULA,
    },
    "fomento": {
        "label": "Fomento", "from": "fact_funding a",
        "measures": MEDIDAS_FOMENTO, "dimensions": RECORTES_FOMENTO,
        "filters": FILTROS_FOMENTO,
    },
}


class QueryError(ValueError):
    """Pedido de consulta fora do que a camada ouro expõe."""


def query(db: Database, measure: str = "artigos", by: str = "linha",
          split: str | None = None, filters: dict[str, Any] | None = None,
          limit: int = 40, order: str = "valor",
          dataset: str = "artigos") -> dict[str, Any]:
    """Agrega uma medida por uma (ou duas) dimensões, num dos conjuntos.

    `split` produz uma segunda quebra — é o que permite barras empilhadas
    e tabelas cruzadas no painel sem escrever SQL novo a cada gráfico.

    `dataset` escolhe o fato: artigos (o padrão, e o que sempre existiu),
    medidas da bancada ou fomento. Só o conjunto muda; a montagem do SQL
    é a mesma, e é isso que impede que cada domínio ganhe um dialeto
    próprio de filtro.
    """
    _ready(db)
    if dataset not in DATASETS:
        raise QueryError(
            f"conjunto desconhecido: {dataset}. Use um de: {', '.join(sorted(DATASETS))}")
    conj = DATASETS[dataset]
    medidas, recortes, filtros = conj["measures"], conj["dimensions"], conj["filters"]

    if measure not in medidas:
        raise QueryError(f"medida desconhecida em {dataset}: {measure}."
                         f" Use uma de: {', '.join(sorted(medidas))}")
    if by not in recortes:
        raise QueryError(f"dimensão desconhecida em {dataset}: {by}."
                         f" Use uma de: {', '.join(sorted(recortes))}")
    if split is not None and split not in recortes:
        raise QueryError(f"dimensão de quebra desconhecida em {dataset}: {split}")

    where: list[str] = []
    params: list[Any] = []
    for key, value in (filters or {}).items():
        if value in (None, "", []):
            continue
        if key not in filtros:
            raise QueryError(f"filtro desconhecido em {dataset}: {key}."
                             f" Use um de: {', '.join(sorted(filtros))}")
        where.append(filtros[key])
        params.append(value)

    select = [recortes[by]["sql"] + " AS dim1"]
    group = ["dim1"]
    if split:
        select.append(recortes[split]["sql"] + " AS dim2")
        group.append("dim2")
    select.append(medidas[measure]["sql"] + " AS valor")

    sql = (
        "SELECT " + ", ".join(select) + " FROM " + conj["from"]
        + (" WHERE " + " AND ".join(where) if where else "")
        + " GROUP BY " + ", ".join(group)
        + (" ORDER BY valor DESC" if order == "valor" else " ORDER BY dim1")
        + f" LIMIT {max(1, min(int(limit), 500))}"
    )
    rows = db.dicts(sql, params)
    return {
        "dataset": dataset, "dataset_label": conj["label"],
        "measure": measure, "measure_label": medidas[measure]["label"],
        "unit": medidas[measure]["unit"],
        "by": by, "by_label": recortes[by]["label"],
        "split": split, "split_label": recortes[split]["label"] if split else None,
        "filters": {k: v for k, v in (filters or {}).items() if v not in (None, "", [])},
        "nota": conj.get("nota"),
        "rows": rows,
        # Somar uma taxa ou uma média entre os recortes dá um número sem
        # sentido: 40% + 60% não são 100% de nada. O total só sai quando
        # a medida é somável.
        "total": (sum(float(r["valor"] or 0) for r in rows)
                  if medidas[measure].get("somavel", True) else None),
    }


# O que cada conjunto mostra quando ninguem pediu nada.
PADRAO_DA_MEDIDA = {"artigos": "artigos", "medidas": "medicoes", "fomento": "propostas"}
PADRAO_DO_RECORTE = {"artigos": "linha", "medidas": "instrumento", "fomento": "agencia"}


def catalog(com_restritos: bool = True) -> dict[str, Any]:
    """O que a camada ouro aceita — o painel monta o explorador a partir disto.

    As chaves `measures`, `dimensions` e `filters` no topo continuam sendo
    as de ARTIGO, e de propósito: quem já lia este catálogo antes dos
    outros conjuntos existirem continua lendo a mesma coisa.
    """
    conjuntos = []
    for chave, conj in DATASETS.items():
        if conj.get("restrito") and not com_restritos:
            continue
        conjuntos.append({
            "id": chave, "label": conj["label"],
            "restrito": bool(conj.get("restrito")), "nota": conj.get("nota"),
            "padrao_medida": PADRAO_DA_MEDIDA[chave],
            "padrao_recorte": PADRAO_DO_RECORTE[chave],
            "measures": [{"id": k, "label": v["label"], "unit": v["unit"],
                          "somavel": v.get("somavel", True)}
                         for k, v in conj["measures"].items()],
            "dimensions": [{"id": k, "label": v["label"]}
                           for k, v in conj["dimensions"].items() if k != "total"],
            "filters": sorted(conj["filters"]),
        })
    return {
        "measures": [{"id": k, "label": v["label"], "unit": v["unit"]} for k, v in MEASURES.items()],
        "dimensions": [{"id": k, "label": v["label"]} for k, v in DIMENSIONS.items() if k != "total"],
        "filters": sorted(FILTERS),
        "datasets": conjuntos,
    }


# ----------------------------------------------------------------------
# Exportação
# ----------------------------------------------------------------------
GOLD_TABLES = ("dim_date", "dim_researcher", "dim_line", "dim_journal", "dim_project",
               "fact_article", "fact_authorship", "fact_submission", "fact_citation",
               "fact_event", "dim_instrument", "dim_protocol", "dim_agency",
               "fact_measurement", "fact_funding", "metric_snapshot")


def export(db: Database, out_dir: Path = GOLD_DIR, verbose: bool = True) -> dict[str, Any]:
    """Grava a camada ouro em Parquet (ou CSV, se pyarrow não estiver instalado).

    Parquet é colunar: abre no pandas, no R (arrow), no Power BI e no DuckDB
    sem precisar do SQLite — é a porta de saída para quem quiser analisar
    os dados fora daqui.
    """
    _ready(db)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        import pandas as pd
    except ImportError:
        if verbose:
            print("  ! pandas ausente: exportação ignorada")
        return {"written": 0, "format": None}

    try:
        import pyarrow  # noqa: F401
        fmt = "parquet"
    except ImportError:
        fmt = "csv"

    written = 0
    for table in GOLD_TABLES:
        try:
            frame = pd.read_sql_query(f"SELECT * FROM {table}", db.conn)
        except Exception:
            continue
        target = out_dir / f"{table}.{fmt}"
        if fmt == "parquet":
            frame.to_parquet(target, index=False)
        else:
            frame.to_csv(target, index=False, encoding="utf-8")
        db.execute(
            "INSERT INTO lake_manifest (layer, source_path, stored_path, bytes, rows, note)"
            " VALUES ('gold', ?, ?, ?, ?, ?)",
            (table, _rel(target), target.stat().st_size, len(frame), f"exportação {fmt}"))
        written += 1
    db.conn.commit()
    if verbose:
        print(f"  exportação: {written} tabela(s) em {fmt} → {out_dir.relative_to(config.ROOT)}")
    return {"written": written, "format": fmt, "dir": str(out_dir)}


def lineage(db: Database, limit: int = 50) -> list[dict]:
    _ready(db)
    return db.dicts(
        "SELECT captured_at, layer, source_path, stored_path, sha256, bytes, rows, note"
        " FROM lake_manifest ORDER BY id DESC LIMIT ?", (limit,))


# ----------------------------------------------------------------------
# Execução
# ----------------------------------------------------------------------
def run(db: Database, raw_dir: Path = config.RAW_DIR, with_export: bool = False,
        verbose: bool = True) -> dict[str, Any]:
    if verbose:
        print("[lakehouse] bronze → ouro → histórico")
    result: dict[str, Any] = {"at": datetime.now().isoformat(timespec="seconds")}
    result["bronze"] = capture_bronze(db, raw_dir, verbose=verbose)
    result["gold"] = build_gold(db, verbose=verbose)
    result["snapshot"] = take_snapshot(db, verbose=verbose)
    if with_export:
        result["export"] = export(db, verbose=verbose)
    from . import hooks

    hooks.emit(db, "lake.atualizado", entity="lake",
               detail=f"{sum(result['gold'].values())} linhas na camada ouro",
               payload={"gold": result["gold"], "snapshot": result["snapshot"]})
    return result
