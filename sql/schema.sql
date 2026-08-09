/*
  sql/schema.sql
  Modelo relacional do backend biomecanico (Landmine Clean & Press).

  Compativel com scripts/migrate.R (R/RSQLite) e com scripts/ingest.py
  (Python/sqlite3). Regras para o executor statement-a-statement do
  migrate.R: um unico ponto-e-virgula por statement, sem ponto-e-virgula
  dentro de strings ou comentarios, e comentarios sempre em bloco (nao usar
  hifen-duplo de linha, pois o migrate.R descarta chunks que comecam assim).

  Convencoes:
    * Toda serie temporal bruta vive em `series` (amostras em JSON) — e a
      fonte de verdade para recomputar as analises padrao-ouro na API.
    * Resultados escalares por submovimento/sessao vivem em `metric` (EAV),
      namespaced por `analysis`.
    * Ajustes de modelo (regressao, logistica, lei de potencia, bootstrap)
      vivem em `fit`.
    * Estruturas ricas nao-tabulares (esqueleto, trajetoria 3D, curvas de
      ajuste, blobs de metodologia) vivem em `dataset` como JSON, sem perda.
*/

CREATE TABLE IF NOT EXISTS schema_meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS athlete (
  id            INTEGER PRIMARY KEY,
  ext_key       TEXT UNIQUE,
  name          TEXT NOT NULL,
  body_mass_kg  REAL CHECK (body_mass_kg > 0),
  height_m      REAL CHECK (height_m > 0),
  bmi           REAL,
  sex           TEXT,
  notes         TEXT
);

CREATE TABLE IF NOT EXISTS session (
  id                INTEGER PRIMARY KEY,
  athlete_id        INTEGER NOT NULL REFERENCES athlete(id) ON DELETE CASCADE,
  exercise          TEXT NOT NULL,
  load_kg           REAL CHECK (load_kg >= 0),
  pct_bodyweight    REAL,
  load_per_height   REAL,
  gravity           REAL NOT NULL DEFAULT 9.81,
  pose_source       TEXT NOT NULL DEFAULT 'mediapipe',
  pose_model        TEXT,
  n_submovements    INTEGER,
  captured_at       TEXT,
  meta              TEXT,
  notes             TEXT
);

CREATE TABLE IF NOT EXISTS submovement (
  id            INTEGER PRIMARY KEY,
  session_id    INTEGER NOT NULL REFERENCES session(id) ON DELETE CASCADE,
  ordinal       INTEGER NOT NULL,
  label         TEXT NOT NULL,
  kind          TEXT NOT NULL DEFAULT 'pull' CHECK (kind IN ('pull','press','composite')),
  frame_start   INTEGER,
  frame_end     INTEGER,
  n_frames      INTEGER,
  dt            REAL,
  is_slowmo_2x  INTEGER NOT NULL DEFAULT 0 CHECK (is_slowmo_2x IN (0,1)),
  idx_transicao INTEGER,
  meta          TEXT,
  UNIQUE (session_id, ordinal)
);

/* Dicionario de variaveis (metadado de apresentacao das series). */
CREATE TABLE IF NOT EXISTS variable (
  key        TEXT PRIMARY KEY,
  title      TEXT NOT NULL,
  unit       TEXT,
  multi_axis INTEGER NOT NULL DEFAULT 0 CHECK (multi_axis IN (0,1))
);

CREATE TABLE IF NOT EXISTS variable_series (
  id           INTEGER PRIMARY KEY,
  variable_key TEXT NOT NULL REFERENCES variable(key) ON DELETE CASCADE,
  series_key   TEXT NOT NULL,
  label        TEXT,
  color        TEXT,
  ord          INTEGER NOT NULL DEFAULT 0
);

/* Series temporais brutas: uma linha por (submovimento, sinal). */
CREATE TABLE IF NOT EXISTS series (
  id             INTEGER PRIMARY KEY,
  submovement_id INTEGER NOT NULL REFERENCES submovement(id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  unit           TEXT,
  n              INTEGER,
  samples        TEXT NOT NULL,
  UNIQUE (submovement_id, name)
);

/* EAV para resultados escalares. submovement_id NULO = escopo de sessao. */
CREATE TABLE IF NOT EXISTS metric (
  id             INTEGER PRIMARY KEY,
  session_id     INTEGER NOT NULL REFERENCES session(id) ON DELETE CASCADE,
  submovement_id INTEGER REFERENCES submovement(id) ON DELETE CASCADE,
  analysis       TEXT NOT NULL,
  name           TEXT NOT NULL,
  value_num      REAL,
  value_text     TEXT,
  unit           TEXT
);

/* Ajustes de modelo (regressao/logistica/lei de potencia/bootstrap). */
CREATE TABLE IF NOT EXISTS fit (
  id             INTEGER PRIMARY KEY,
  session_id     INTEGER NOT NULL REFERENCES session(id) ON DELETE CASCADE,
  submovement_id INTEGER REFERENCES submovement(id) ON DELETE CASCADE,
  analysis       TEXT NOT NULL,
  model          TEXT,
  r2             REAL,
  p_value        REAL,
  params         TEXT,
  meta           TEXT
);

/* Sequenciamento cinetico: ordem de pico de velocidade angular por fase. */
CREATE TABLE IF NOT EXISTS sequencing_event (
  id             INTEGER PRIMARY KEY,
  submovement_id INTEGER NOT NULL REFERENCES submovement(id) ON DELETE CASCADE,
  phase          TEXT NOT NULL CHECK (phase IN ('subida','descida')),
  joint          TEXT NOT NULL,
  peak_angvel    REAL,
  ord            INTEGER NOT NULL
);

/* Confianca de rastreamento (visibilidade MediaPipe) por articulacao. */
CREATE TABLE IF NOT EXISTS joint_confidence (
  id                 INTEGER PRIMARY KEY,
  submovement_id     INTEGER NOT NULL REFERENCES submovement(id) ON DELETE CASCADE,
  joint              TEXT NOT NULL,
  mean_vis           REAL,
  min_vis            REAL,
  pct_low_confidence REAL
);

CREATE TABLE IF NOT EXISTS phase (
  name  TEXT PRIMARY KEY,
  color TEXT
);

CREATE TABLE IF NOT EXISTS phase_segment (
  id             INTEGER PRIMARY KEY,
  submovement_id INTEGER NOT NULL REFERENCES submovement(id) ON DELETE CASCADE,
  phase          TEXT NOT NULL,
  frames         INTEGER,
  pct            REAL,
  duration_s     REAL,
  ord            INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS literature_reference (
  id          INTEGER PRIMARY KEY,
  session_id  INTEGER REFERENCES session(id) ON DELETE CASCADE,
  metric_name TEXT NOT NULL,
  ours        TEXT,
  literature  TEXT,
  source      TEXT,
  rating      TEXT,
  color       TEXT,
  note        TEXT
);

/* Valores-fonte para recomputo de consistencia (CV / Grubbs / bootstrap). */
CREATE TABLE IF NOT EXISTS consistency_source (
  id          INTEGER PRIMARY KEY,
  session_id  INTEGER NOT NULL REFERENCES session(id) ON DELETE CASCADE,
  analysis    TEXT NOT NULL,
  metric_name TEXT NOT NULL,
  scope       TEXT NOT NULL,
  labels      TEXT,
  values_json TEXT NOT NULL,
  mean        REAL,
  std         REAL,
  cv_pct      REAL
);

/* Escape hatch sem perda para estruturas ricas nao-tabulares (JSON). */
CREATE TABLE IF NOT EXISTS dataset (
  id             INTEGER PRIMARY KEY,
  session_id     INTEGER REFERENCES session(id) ON DELETE CASCADE,
  submovement_id INTEGER REFERENCES submovement(id) ON DELETE CASCADE,
  kind           TEXT NOT NULL,
  name           TEXT NOT NULL,
  payload        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_submovement_session ON submovement(session_id);
CREATE INDEX IF NOT EXISTS idx_series_submovement ON series(submovement_id);
CREATE INDEX IF NOT EXISTS idx_series_name ON series(name);
CREATE INDEX IF NOT EXISTS idx_metric_analysis ON metric(analysis);
CREATE INDEX IF NOT EXISTS idx_metric_submovement ON metric(submovement_id);
CREATE INDEX IF NOT EXISTS idx_metric_session ON metric(session_id);
CREATE INDEX IF NOT EXISTS idx_fit_analysis ON fit(analysis);
CREATE INDEX IF NOT EXISTS idx_seq_submovement ON sequencing_event(submovement_id);
CREATE INDEX IF NOT EXISTS idx_conf_submovement ON joint_confidence(submovement_id);
CREATE INDEX IF NOT EXISTS idx_phaseseg_submovement ON phase_segment(submovement_id);
CREATE INDEX IF NOT EXISTS idx_dataset_kind ON dataset(kind);
CREATE INDEX IF NOT EXISTS idx_dataset_submovement ON dataset(submovement_id);
