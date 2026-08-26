/* ============================================================
   LAPE — camada OURO do lakehouse

   A camada PRATA (sql/schema.sql) guarda o dado operacional: é onde
   o laboratório escreve, com chaves, restrições e histórico.
   Esta camada OURO é derivada dela, reconstruída inteira a cada
   execução, e existe para uma coisa só: responder perguntas rápido.
   Modelo dimensional clássico — fatos numéricos no centro, dimensões
   descritivas em volta — para que qualquer cruzamento (medida × recorte)
   seja um único JOIN.

   Nada aqui é fonte de verdade: apagar a camada ouro não perde dado.
   Aplicada por scripts/lape/lake.py, nunca pelo migrate.R.
   ============================================================ */

DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_researcher;
DROP TABLE IF EXISTS dim_line;
DROP TABLE IF EXISTS dim_journal;
DROP TABLE IF EXISTS dim_project;
DROP TABLE IF EXISTS fact_article;
DROP TABLE IF EXISTS fact_authorship;
DROP TABLE IF EXISTS fact_submission;
DROP TABLE IF EXISTS fact_citation;
DROP TABLE IF EXISTS fact_event;

/* ---------- dimensões ---------- */

CREATE TABLE dim_date (
  date_key   TEXT PRIMARY KEY,   /* AAAA-MM-DD */
  year       INTEGER NOT NULL,
  quarter    INTEGER NOT NULL,
  month      INTEGER NOT NULL,
  month_name TEXT NOT NULL,
  year_month TEXT NOT NULL,
  day        INTEGER NOT NULL,
  weekday    INTEGER NOT NULL
);

CREATE TABLE dim_researcher (
  member_id       INTEGER PRIMARY KEY,
  full_name       TEXT NOT NULL,
  short_name      TEXT,
  name_key        TEXT,
  role            TEXT,
  degree          TEXT,
  research_line   TEXT,
  institution     TEXT,
  is_external     INTEGER NOT NULL DEFAULT 0,
  active          INTEGER NOT NULL DEFAULT 1,
  h_index         INTEGER,
  h_index_source  TEXT,
  i10_index       INTEGER,
  citations_total INTEGER,
  n_projects      INTEGER NOT NULL DEFAULT 0,
  orcid           TEXT,
  lattes_id       TEXT
);

CREATE TABLE dim_line (
  line_id     INTEGER PRIMARY KEY,
  code        TEXT,
  name        TEXT NOT NULL,
  coordinator TEXT,
  active      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE dim_journal (
  journal_key   TEXT PRIMARY KEY,   /* nome normalizado */
  name          TEXT NOT NULL,
  issn          TEXT,
  qualis        TEXT,
  impact_factor REAL
);

CREATE TABLE dim_project (
  project_id  INTEGER PRIMARY KEY,
  code        TEXT,
  name        TEXT NOT NULL,
  funder      TEXT,
  status      TEXT,
  coordinator TEXT,
  started_on  TEXT,
  ended_on    TEXT,
  amount      REAL
);

/* ---------- fatos ---------- */

CREATE TABLE fact_article (
  article_id                  INTEGER PRIMARY KEY,
  internal_code               TEXT,
  title                       TEXT NOT NULL,
  status                      TEXT NOT NULL,
  line_id                     INTEGER,
  research_line               TEXT,
  journal_key                 TEXT,
  journal                     TEXT,
  qualis                      TEXT,
  study_type                  TEXT,
  language                    TEXT,
  lead_member_id              INTEGER,
  lead_name                   TEXT,
  started_on                  TEXT,
  first_submission_on         TEXT,
  accepted_on                 TEXT,
  published_on                TEXT,
  year_published              INTEGER,
  year_started                INTEGER,
  days_start_to_publication   INTEGER,
  days_submission_to_acceptance INTEGER,
  days_acceptance_to_publication INTEGER,
  days_open                   INTEGER,
  submission_attempts         INTEGER NOT NULL DEFAULT 0,
  rejections                  INTEGER NOT NULL DEFAULT 0,
  wos_citations               INTEGER,
  scopus_citations            INTEGER,
  openalex_citations          INTEGER,
  best_citations              INTEGER NOT NULL DEFAULT 0,
  n_authors                   INTEGER NOT NULL DEFAULT 0,
  n_internal_authors          INTEGER NOT NULL DEFAULT 0,
  doi                         TEXT,
  source                      TEXT
);

CREATE TABLE fact_authorship (
  article_id       INTEGER NOT NULL,
  member_id        INTEGER NOT NULL,
  author_order     INTEGER,
  is_first_author  INTEGER NOT NULL DEFAULT 0,
  is_corresponding INTEGER NOT NULL DEFAULT 0,
  is_external      INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (article_id, member_id)
);

CREATE TABLE fact_submission (
  submission_id            INTEGER PRIMARY KEY,
  article_id               INTEGER NOT NULL,
  attempt_no               INTEGER NOT NULL,
  journal_key              TEXT,
  journal                  TEXT,
  submitted_on             TEXT,
  decision_on              TEXT,
  decision                 TEXT,
  rejection_reason         TEXT,
  rejection_category       TEXT,
  desk_reject              INTEGER NOT NULL DEFAULT 0,
  days_to_decision         INTEGER,
  days_since_previous      INTEGER,
  days_decision_to_resubmit INTEGER,
  year_submitted           INTEGER,
  research_line            TEXT
);

CREATE TABLE fact_citation (
  article_id  INTEGER NOT NULL,
  source      TEXT NOT NULL,
  snapshot_on TEXT NOT NULL,
  citations   INTEGER NOT NULL,
  delta       INTEGER,
  PRIMARY KEY (article_id, source, snapshot_on)
);

CREATE TABLE fact_event (
  event_id       INTEGER PRIMARY KEY,
  kind           TEXT NOT NULL,
  title          TEXT,
  start_date     TEXT,
  year           INTEGER,
  year_month     TEXT,
  city           TEXT,
  state          TEXT,
  country        TEXT,
  latitude       REAL,
  longitude      REAL,
  research_line  TEXT,
  n_participants INTEGER NOT NULL DEFAULT 0
);

/* ---------- histórico de indicadores ----------
   Sobrevive à reconstrução da camada ouro: é o que permite dizer
   "cresceu tanto desde o mês passado" com dado medido, não estimado. */

CREATE TABLE IF NOT EXISTS metric_snapshot (
  snapshot_on TEXT NOT NULL,
  metric      TEXT NOT NULL,
  dimension   TEXT NOT NULL DEFAULT 'total',
  dim_value   TEXT NOT NULL DEFAULT 'total',
  value       REAL NOT NULL,
  PRIMARY KEY (snapshot_on, metric, dimension, dim_value)
);

/* ---------- linhagem: de qual arquivo veio cada carga ---------- */

CREATE TABLE IF NOT EXISTS lake_manifest (
  id          INTEGER PRIMARY KEY,
  captured_at TEXT NOT NULL DEFAULT (datetime('now')),
  layer       TEXT NOT NULL,
  source_path TEXT NOT NULL,
  stored_path TEXT,
  sha256      TEXT,
  bytes       INTEGER,
  rows        INTEGER,
  note        TEXT
);

/* ---------- índices ---------- */

CREATE INDEX idx_fa_status ON fact_article(status);
CREATE INDEX idx_fa_year ON fact_article(year_published);
CREATE INDEX idx_fa_line ON fact_article(research_line);
CREATE INDEX idx_fa_journal ON fact_article(journal_key);
CREATE INDEX idx_fau_member ON fact_authorship(member_id);
CREATE INDEX idx_fs_article ON fact_submission(article_id);
CREATE INDEX idx_fs_decision ON fact_submission(decision);
CREATE INDEX idx_fe_year ON fact_event(year_month);
CREATE INDEX IF NOT EXISTS idx_ms_metric ON metric_snapshot(metric, snapshot_on);
