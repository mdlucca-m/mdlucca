/* ============================================================
   LAPE - Laboratorio de Psicologia do Esporte
   Esquema do banco de dados (SQLite)

   Compatibilidade: este arquivo e aplicado tanto pelo pipeline
   Python (scripts/lape/db.py) quanto pelo scripts/migrate.R.
   O migrate.R quebra o arquivo em statements usando ";" como
   separador e ignora blocos iniciados por "--", por isso aqui
   usamos apenas comentarios de bloco e nunca ";" dentro deles.
   ============================================================ */

PRAGMA foreign_keys = ON;

/* ---------- Catalogos ---------- */

CREATE TABLE IF NOT EXISTS research_lines (
  id            INTEGER PRIMARY KEY,
  code          TEXT UNIQUE NOT NULL,
  name          TEXT NOT NULL,
  description   TEXT,
  coordinator   TEXT,
  started_on    TEXT,
  keywords      TEXT,
  active        INTEGER NOT NULL DEFAULT 1,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS institutions (
  id            INTEGER PRIMARY KEY,
  name          TEXT NOT NULL,
  acronym       TEXT,
  city          TEXT,
  state         TEXT,
  country       TEXT DEFAULT 'Brasil',
  latitude      REAL,
  longitude     REAL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (name, city)
);

CREATE TABLE IF NOT EXISTS rejection_reasons (
  id            INTEGER PRIMARY KEY,
  code          TEXT UNIQUE NOT NULL,
  label         TEXT NOT NULL,
  category      TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

/* ---------- Pessoas ---------- */

CREATE TABLE IF NOT EXISTS members (
  id               INTEGER PRIMARY KEY,
  full_name        TEXT NOT NULL,
  short_name       TEXT,
  name_key         TEXT UNIQUE NOT NULL,
  lattes_id        TEXT,
  orcid            TEXT,
  email            TEXT,
  role             TEXT,
  research_line_id INTEGER REFERENCES research_lines(id) ON DELETE SET NULL,
  institution_id   INTEGER REFERENCES institutions(id) ON DELETE SET NULL,
  joined_on        TEXT,
  left_on          TEXT,
  is_external      INTEGER NOT NULL DEFAULT 0,
  active           INTEGER NOT NULL DEFAULT 1,
  openalex_id      TEXT,
  scopus_author_id TEXT,
  researcher_id    TEXT,
  bio              TEXT,
  photo_url        TEXT,
  phone            TEXT,
  degree           TEXT,

  /* Vinculo com o laboratorio e formacao em curso. O vocabulario de `role`
     esta em mapping.VINCULOS: doutorando, mestrando, bolsista de IC, de
     extensao, voluntario, professor, tecnico. E o `advisor_id` que liga
     cada orientando ao seu professor -- e dele sai o organograma, sem
     ninguem desenhar caixa nenhuma a mao. */
  advisor_id        INTEGER REFERENCES members(id) ON DELETE SET NULL,
  co_advisor_id     INTEGER REFERENCES members(id) ON DELETE SET NULL,
  thesis_title      TEXT,
  thesis_kind       TEXT,
  thesis_status     TEXT,
  thesis_due_on     TEXT,
  topics            TEXT,
  scholarship       TEXT,
  scholarship_until TEXT,

  h_index          INTEGER,
  h_index_source   TEXT,
  h_index_scopus   INTEGER,
  h_index_wos      INTEGER,
  i10_index        INTEGER,
  citations_total  INTEGER,
  metrics_updated_at TEXT,
  login            TEXT UNIQUE,
  password_hash    TEXT,
  user_role        TEXT NOT NULL DEFAULT 'integrante',
  must_change_password INTEGER NOT NULL DEFAULT 0,
  last_login_at    TEXT,
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

/* ---------- Projetos ---------- */

CREATE TABLE IF NOT EXISTS projects (
  id               INTEGER PRIMARY KEY,
  code             TEXT UNIQUE NOT NULL,
  name             TEXT NOT NULL,
  description      TEXT,
  research_line_id INTEGER REFERENCES research_lines(id) ON DELETE SET NULL,
  coordinator_id   INTEGER REFERENCES members(id) ON DELETE SET NULL,
  coordinator_name TEXT,
  kind             TEXT,
  funder           TEXT,
  grant_number     TEXT,
  amount           REAL,
  started_on       TEXT,
  ended_on         TEXT,
  status           TEXT NOT NULL DEFAULT 'em_andamento',
  ethics_approval  TEXT,
  url              TEXT,
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS project_members (
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  role       TEXT,
  joined_on  TEXT,
  PRIMARY KEY (project_id, member_id)
);

CREATE TABLE IF NOT EXISTS project_articles (
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, article_id)
);

/* ---------- Producao cientifica ---------- */

CREATE TABLE IF NOT EXISTS articles (
  id                  INTEGER PRIMARY KEY,
  internal_code       TEXT UNIQUE,
  title               TEXT NOT NULL,
  title_key           TEXT UNIQUE NOT NULL,
  status              TEXT NOT NULL DEFAULT 'em_producao',
  research_line_id    INTEGER REFERENCES research_lines(id) ON DELETE SET NULL,
  study_type          TEXT,
  language            TEXT,
  started_on          TEXT,
  first_submission_on TEXT,
  accepted_on         TEXT,
  published_on        TEXT,
  year_published      INTEGER,
  journal             TEXT,
  issn                TEXT,
  qualis              TEXT,
  impact_factor       REAL,
  doi                 TEXT,
  url                 TEXT,
  wos_id              TEXT,
  scopus_id           TEXT,
  pmid                TEXT,
  pmc                 TEXT,
  oa_status           TEXT,
  oa_url              TEXT,
  wos_citations       INTEGER,
  scopus_citations    INTEGER,
  openalex_citations  INTEGER,
  citations_updated_at TEXT,
  open_access         INTEGER,
  notes               TEXT,
  lead_member_id      INTEGER REFERENCES members(id) ON DELETE SET NULL,
  lead_name           TEXT,
  status_locked       INTEGER NOT NULL DEFAULT 0,
  internal_review_on  TEXT,
  source              TEXT DEFAULT 'planilha',
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS article_authors (
  article_id       INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  member_id        INTEGER REFERENCES members(id) ON DELETE SET NULL,
  author_name      TEXT NOT NULL,
  author_order     INTEGER NOT NULL DEFAULT 1,
  is_corresponding INTEGER NOT NULL DEFAULT 0,
  is_external      INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (article_id, author_order)
);

CREATE TABLE IF NOT EXISTS submissions (
  id                  INTEGER PRIMARY KEY,
  article_id          INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  attempt_no          INTEGER NOT NULL DEFAULT 1,
  journal             TEXT,
  issn                TEXT,
  submitted_on        TEXT,
  decision            TEXT,
  decision_on         TEXT,
  rejection_reason_id INTEGER REFERENCES rejection_reasons(id) ON DELETE SET NULL,
  rejection_notes     TEXT,
  desk_reject         INTEGER NOT NULL DEFAULT 0,
  review_rounds       INTEGER,
  created_at          TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (article_id, attempt_no)
);

CREATE TABLE IF NOT EXISTS article_milestones (
  id          INTEGER PRIMARY KEY,
  article_id  INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  milestone   TEXT NOT NULL,
  label       TEXT,
  occurred_on TEXT,
  seq         INTEGER NOT NULL DEFAULT 0,
  UNIQUE (article_id, milestone)
);

CREATE TABLE IF NOT EXISTS citation_snapshots (
  id           INTEGER PRIMARY KEY,
  article_id   INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  source       TEXT NOT NULL,
  citations    INTEGER NOT NULL,
  snapshot_on  TEXT NOT NULL,
  UNIQUE (article_id, source, snapshot_on)
);

/* ---------- Atividades, reunioes e calendario ---------- */

CREATE TABLE IF NOT EXISTS events (
  id               INTEGER PRIMARY KEY,
  external_key     TEXT UNIQUE,
  kind             TEXT NOT NULL DEFAULT 'reuniao',
  title            TEXT NOT NULL,
  description      TEXT,
  start_at         TEXT NOT NULL,
  end_at           TEXT,
  all_day          INTEGER NOT NULL DEFAULT 0,
  status           TEXT DEFAULT 'confirmado',
  location_name    TEXT,
  institution_id   INTEGER REFERENCES institutions(id) ON DELETE SET NULL,
  city             TEXT,
  state            TEXT,
  country          TEXT DEFAULT 'Brasil',
  latitude         REAL,
  longitude        REAL,
  research_line_id INTEGER REFERENCES research_lines(id) ON DELETE SET NULL,
  url              TEXT,
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS event_participants (
  event_id   INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  role       TEXT,
  attended   INTEGER,
  PRIMARY KEY (event_id, member_id)
);

/* ---------- Descobertas do agente rastreador ---------- */

CREATE TABLE IF NOT EXISTS discoveries (
  id                INTEGER PRIMARY KEY,
  source            TEXT NOT NULL,
  external_id       TEXT,
  doi               TEXT,
  title             TEXT NOT NULL,
  title_key         TEXT NOT NULL,
  authors           TEXT,
  journal           TEXT,
  year              INTEGER,
  citations         INTEGER,
  url               TEXT,
  matched_member_id INTEGER REFERENCES members(id) ON DELETE SET NULL,
  article_id        INTEGER REFERENCES articles(id) ON DELETE SET NULL,
  status            TEXT NOT NULL DEFAULT 'pendente',
  payload           TEXT,
  found_at          TEXT NOT NULL DEFAULT (datetime('now')),
  reviewed_at       TEXT,
  UNIQUE (source, title_key)
);

/* ---------- Convites: a pessoa se cadastra sozinha ----------

   A coordenacao gera um link e o envia ao grupo do laboratorio. Quem abre
   escolhe a propria senha e entra ja com o cadastro criado -- ninguem
   precisa transmitir senha por mensagem, e a coordenacao nao cria conta a
   conta. O link tem prazo e numero maximo de usos. */

CREATE TABLE IF NOT EXISTS invites (
  id          INTEGER PRIMARY KEY,
  token       TEXT NOT NULL UNIQUE,
  label       TEXT,
  user_role   TEXT NOT NULL DEFAULT 'integrante',
  max_uses    INTEGER NOT NULL DEFAULT 1,
  uses        INTEGER NOT NULL DEFAULT 0,
  expires_at  TEXT,
  revoked     INTEGER NOT NULL DEFAULT 0,
  created_by  INTEGER REFERENCES members(id) ON DELETE SET NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invite_uses (
  id         INTEGER PRIMARY KEY,
  invite_id  INTEGER NOT NULL REFERENCES invites(id) ON DELETE CASCADE,
  member_id  INTEGER REFERENCES members(id) ON DELETE SET NULL,
  at         TEXT NOT NULL DEFAULT (datetime('now')),
  ip         TEXT
);

CREATE INDEX IF NOT EXISTS idx_invite_uses ON invite_uses(invite_id, at);

CREATE INDEX IF NOT EXISTS idx_members_advisor ON members(advisor_id);
CREATE INDEX IF NOT EXISTS idx_members_role ON members(role, active);

/* ---------- Automacao: eventos e integracoes ---------- */

/* Fila de eventos do sistema. E dela que sai o streaming em tempo real do
   painel e o disparo dos webhooks para o n8n. */
CREATE TABLE IF NOT EXISTS change_log (
  id        INTEGER PRIMARY KEY,
  at        TEXT NOT NULL DEFAULT (datetime('now')),
  event     TEXT NOT NULL,
  entity    TEXT,
  entity_id TEXT,
  actor     TEXT,
  detail    TEXT
);

/* Destinos externos. Cada webhook do n8n vira uma linha aqui. */
CREATE TABLE IF NOT EXISTS webhooks (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL,
  url         TEXT NOT NULL,
  event       TEXT NOT NULL DEFAULT '*',
  secret      TEXT,
  active      INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  last_at     TEXT,
  last_status TEXT,
  failures    INTEGER NOT NULL DEFAULT 0,
  UNIQUE (url, event)
);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
  id         INTEGER PRIMARY KEY,
  webhook_id INTEGER REFERENCES webhooks(id) ON DELETE CASCADE,
  event      TEXT NOT NULL,
  at         TEXT NOT NULL DEFAULT (datetime('now')),
  status     TEXT NOT NULL,
  http_code  INTEGER,
  attempt    INTEGER NOT NULL DEFAULT 1,
  duration_ms INTEGER,
  error      TEXT
);

/* ---------- Acesso e auditoria ---------- */

CREATE TABLE IF NOT EXISTS sessions (
  token      TEXT PRIMARY KEY,
  member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  user_agent TEXT,
  ip         TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
  id         INTEGER PRIMARY KEY,
  at         TEXT NOT NULL DEFAULT (datetime('now')),
  member_id  INTEGER REFERENCES members(id) ON DELETE SET NULL,
  login      TEXT,
  action     TEXT NOT NULL,
  entity     TEXT,
  entity_id  TEXT,
  detail     TEXT,
  ip         TEXT
);

/* Contagem de falhas de login por janela de tempo: e daqui que sai o
   travamento por tentativa e erro. Fica no banco, e nao em memoria, para
   sobreviver a um reinicio do servico. */
CREATE INDEX IF NOT EXISTS idx_audit_login_negado ON audit_log(action, at);

/* ---------- Auditoria de ingestao ---------- */

CREATE TABLE IF NOT EXISTS ingest_log (
  id           INTEGER PRIMARY KEY,
  run_at       TEXT NOT NULL DEFAULT (datetime('now')),
  source       TEXT NOT NULL,
  target       TEXT,
  file         TEXT,
  rows_read    INTEGER DEFAULT 0,
  rows_written INTEGER DEFAULT 0,
  status       TEXT NOT NULL DEFAULT 'ok',
  message      TEXT
);

/* ---------- Revisao sistematica: triagem de referencias ----------

   O ciclo de uma revisao: a busca em cada base traz um monte de
   registros, os duplicados sao juntados, cada pessoa da equipe le
   titulo e resumo e decide, as divergencias vao para arbitragem, e o
   que sobrou vai para leitura de texto completo. O PRISMA e a conta
   desse caminho -- e por isso ele nao e digitado a mao em lugar
   nenhum: sai do proprio banco.

   Duas decisoes de esquema que sustentam o resto:

   1. A decisao de cada pessoa vive em `screenings`, uma linha por
      (referencia, pessoa, etapa). A decisao consolidada da referencia
      e DERIVADA disso, nunca digitada -- e o que permite triagem as
      cegas: ninguem ve o que o outro decidiu ate haver conflito.
   2. Duplicado nao e apagado. Ele aponta para o registro que ficou
      (`duplicate_of`), porque o PRISMA precisa saber quantos foram
      removidos, e porque juntar errado tem de poder ser desfeito.
   ---------- */

CREATE TABLE IF NOT EXISTS reviews (
  id               INTEGER PRIMARY KEY,
  code             TEXT UNIQUE NOT NULL,
  title            TEXT NOT NULL,
  question         TEXT,
  population       TEXT,
  intervention     TEXT,
  comparison       TEXT,
  outcome          TEXT,
  study_designs    TEXT,
  protocol_url     TEXT,
  blind            INTEGER NOT NULL DEFAULT 1,
  reviewers_needed INTEGER NOT NULL DEFAULT 2,
  status           TEXT NOT NULL DEFAULT 'triagem',
  research_line_id INTEGER REFERENCES research_lines(id) ON DELETE SET NULL,
  created_by       INTEGER REFERENCES members(id) ON DELETE SET NULL,
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS review_members (
  review_id  INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  role       TEXT NOT NULL DEFAULT 'triador',
  joined_on  TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (review_id, member_id)
);

CREATE TABLE IF NOT EXISTS review_searches (
  id          INTEGER PRIMARY KEY,
  review_id   INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  base        TEXT NOT NULL,
  query       TEXT,
  searched_on TEXT,
  file        TEXT,
  n_retrieved INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

/* `refs` e nao `references`: a segunda e palavra reservada em SQL. */
CREATE TABLE IF NOT EXISTS refs (
  id            INTEGER PRIMARY KEY,
  review_id     INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  search_id     INTEGER REFERENCES review_searches(id) ON DELETE SET NULL,
  title         TEXT,
  abstract      TEXT,
  authors       TEXT,
  journal       TEXT,
  year          INTEGER,
  volume        TEXT,
  issue         TEXT,
  pages         TEXT,
  doi           TEXT,
  pmid          TEXT,
  issn          TEXT,
  language      TEXT,
  keywords      TEXT,
  url           TEXT,
  pub_type      TEXT,
  dedup_key     TEXT,
  duplicate_of  INTEGER REFERENCES refs(id) ON DELETE SET NULL,
  stage         TEXT NOT NULL DEFAULT 'titulo_resumo',
  decision      TEXT,
  reason_id     INTEGER REFERENCES exclusion_reasons(id) ON DELETE SET NULL,
  decided_at    TEXT,
  full_text_url TEXT,
  affiliation   TEXT,
  country       TEXT,
  notes         TEXT,
  origem        TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS exclusion_reasons (
  id        INTEGER PRIMARY KEY,
  review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  code      TEXT NOT NULL,
  label     TEXT NOT NULL,
  seq       INTEGER NOT NULL DEFAULT 1,
  UNIQUE (review_id, code)
);

/* Uma linha por (referencia, pessoa, etapa). E daqui que sai tanto a
   decisao consolidada quanto a concordancia entre avaliadores. */
CREATE TABLE IF NOT EXISTS screenings (
  id         INTEGER PRIMARY KEY,
  ref_id     INTEGER NOT NULL REFERENCES refs(id) ON DELETE CASCADE,
  member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  stage      TEXT NOT NULL DEFAULT 'titulo_resumo',
  decision   TEXT NOT NULL,
  reason_id  INTEGER REFERENCES exclusion_reasons(id) ON DELETE SET NULL,
  notes      TEXT,
  seconds    REAL,
  decided_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (ref_id, member_id, stage)
);

/* Termos realcados no titulo e no resumo: o olho acha em um segundo o
   que levaria a leitura inteira para encontrar. */
CREATE TABLE IF NOT EXISTS review_terms (
  id        INTEGER PRIMARY KEY,
  review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  term      TEXT NOT NULL,
  tone      TEXT NOT NULL DEFAULT 'incluir',
  UNIQUE (review_id, term, tone)
);

/* ---------- Extracao de dados e risco de vies ----------

   Depois da triagem vem a parte que ninguem gosta: ler cada estudo
   incluido e tirar dele, campo a campo, o que a revisao precisa. Hoje
   isso e feito em planilha compartilhada, e a planilha nao sabe que duas
   pessoas deviam extrair em separado, nem onde as duas discordaram.

   O desenho aqui e o mesmo da triagem, e pela mesma razao: cada pessoa
   preenche a sua, e a versao final e uma terceira coisa, construida a
   partir das duas. Sem isso, "extracao em duplicata" vira uma pessoa
   conferindo o que a outra digitou -- que nao e a mesma coisa e nao vale
   como duplicata.
   ---------- */

CREATE TABLE IF NOT EXISTS extraction_fields (
  id         INTEGER PRIMARY KEY,
  review_id  INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  code       TEXT NOT NULL,
  label      TEXT NOT NULL,
  kind       TEXT NOT NULL DEFAULT 'texto',
  options    TEXT,
  help       TEXT,
  grupo      TEXT,
  seq        INTEGER NOT NULL DEFAULT 1,
  required   INTEGER NOT NULL DEFAULT 0,
  UNIQUE (review_id, code)
);

CREATE TABLE IF NOT EXISTS extractions (
  id         INTEGER PRIMARY KEY,
  ref_id     INTEGER NOT NULL REFERENCES refs(id) ON DELETE CASCADE,
  member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  field_id   INTEGER NOT NULL REFERENCES extraction_fields(id) ON DELETE CASCADE,
  value      TEXT,
  notes      TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (ref_id, member_id, field_id)
);

/* A versao que vai para a tabela do artigo. E uma terceira coisa: nao e a
   de ninguem, e a que as duas pessoas acordaram. */
CREATE TABLE IF NOT EXISTS extraction_final (
  ref_id     INTEGER NOT NULL REFERENCES refs(id) ON DELETE CASCADE,
  field_id   INTEGER NOT NULL REFERENCES extraction_fields(id) ON DELETE CASCADE,
  value      TEXT,
  decided_by INTEGER REFERENCES members(id) ON DELETE SET NULL,
  decided_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (ref_id, field_id)
);

CREATE TABLE IF NOT EXISTS rob_domains (
  id        INTEGER PRIMARY KEY,
  review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  code      TEXT NOT NULL,
  label     TEXT NOT NULL,
  help      TEXT,
  seq       INTEGER NOT NULL DEFAULT 1,
  UNIQUE (review_id, code)
);

CREATE TABLE IF NOT EXISTS rob_answers (
  id         INTEGER PRIMARY KEY,
  ref_id     INTEGER NOT NULL REFERENCES refs(id) ON DELETE CASCADE,
  member_id  INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  domain_id  INTEGER NOT NULL REFERENCES rob_domains(id) ON DELETE CASCADE,
  judgement  TEXT NOT NULL,
  support    TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (ref_id, member_id, domain_id)
);

CREATE TABLE IF NOT EXISTS rob_final (
  ref_id     INTEGER NOT NULL REFERENCES refs(id) ON DELETE CASCADE,
  domain_id  INTEGER NOT NULL REFERENCES rob_domains(id) ON DELETE CASCADE,
  judgement  TEXT NOT NULL,
  support    TEXT,
  decided_by INTEGER REFERENCES members(id) ON DELETE SET NULL,
  decided_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (ref_id, domain_id)
);

/* ---------- Variaveis psicologicas: o eixo tematico da revisao ----------

   Uma revisao sobre "variaveis psicologicas no handebol" nao e uma lista
   de artigos: e uma rede de variaveis estudadas ao longo do tempo, que se
   cruzam. Um artigo sobre ansiedade pre-competitiva, estresse e depressao
   pertence as tres -- e e justamente o artigo que liga as tres que conta
   a historia do campo.

   Por isso a ligacao e muitos-para-muitos, e nao uma coluna "variavel" na
   referencia. Uma coluna obrigaria a escolher uma, e a escolha apagaria a
   relacao, que e o que se quer ver.

   `origem` guarda quem disse: `auto` e o sistema tendo achado o termo no
   titulo ou no resumo, `confirmada` e alguem tendo olhado e concordado,
   `manual` e alguem tendo marcado a mao. A diferenca importa: numero de
   revisao que saiu de busca automatica sem revisao humana nao se publica.
   ---------- */

CREATE TABLE IF NOT EXISTS variables (
  id        INTEGER PRIMARY KEY,
  review_id INTEGER REFERENCES reviews(id) ON DELETE CASCADE,
  code      TEXT NOT NULL,
  label     TEXT NOT NULL,
  grupo     TEXT,
  icone     TEXT,
  cor       TEXT,
  seq       INTEGER NOT NULL DEFAULT 1,
  UNIQUE (review_id, code)
);

/* A mesma ligacao, do lado da producao do proprio laboratorio. Duas
   tabelas e nao uma com coluna de tipo: referencia de revisao e artigo do
   LAPE sao coisas diferentes, e uma chave estrangeira que aponta para
   "uma das duas" nao existe -- viraria integridade conferida a mao. */
CREATE TABLE IF NOT EXISTS article_variables (
  article_id  INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  variable_id INTEGER NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
  origem      TEXT NOT NULL DEFAULT 'auto',
  trecho      TEXT,
  criado_em   TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (article_id, variable_id)
);

CREATE TABLE IF NOT EXISTS ref_variables (
  ref_id      INTEGER NOT NULL REFERENCES refs(id) ON DELETE CASCADE,
  variable_id INTEGER NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
  origem      TEXT NOT NULL DEFAULT 'auto',
  trecho      TEXT,
  criado_em   TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (ref_id, variable_id)
);

/* ---------- Indices ---------- */

CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_year ON articles(year_published);
CREATE INDEX IF NOT EXISTS idx_articles_line ON articles(research_line_id);
CREATE INDEX IF NOT EXISTS idx_authors_member ON article_authors(member_id);
CREATE INDEX IF NOT EXISTS idx_submissions_article ON submissions(article_id);
CREATE INDEX IF NOT EXISTS idx_submissions_decision ON submissions(decision);
CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_at);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);
CREATE INDEX IF NOT EXISTS idx_citations_article ON citation_snapshots(article_id, source);
CREATE INDEX IF NOT EXISTS idx_milestones_article ON article_milestones(article_id, seq);
CREATE INDEX IF NOT EXISTS idx_discoveries_status ON discoveries(status, found_at);
CREATE INDEX IF NOT EXISTS idx_project_members ON project_members(member_id);
CREATE INDEX IF NOT EXISTS idx_sessions_member ON sessions(member_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_audit_at ON audit_log(at);
CREATE INDEX IF NOT EXISTS idx_change_at ON change_log(at);
CREATE INDEX IF NOT EXISTS idx_change_event ON change_log(event, at);
CREATE INDEX IF NOT EXISTS idx_delivery_hook ON webhook_deliveries(webhook_id, at);
CREATE INDEX IF NOT EXISTS idx_refs_review ON refs(review_id, stage);
CREATE INDEX IF NOT EXISTS idx_refs_dedup ON refs(review_id, dedup_key);
CREATE INDEX IF NOT EXISTS idx_refs_duplicate ON refs(duplicate_of);
CREATE INDEX IF NOT EXISTS idx_screenings_ref ON screenings(ref_id, stage);
CREATE INDEX IF NOT EXISTS idx_screenings_member ON screenings(member_id, stage);
CREATE INDEX IF NOT EXISTS idx_extractions_ref ON extractions(ref_id, field_id);
CREATE INDEX IF NOT EXISTS idx_rob_answers_ref ON rob_answers(ref_id, domain_id);
CREATE INDEX IF NOT EXISTS idx_ref_variables_var ON ref_variables(variable_id);
CREATE INDEX IF NOT EXISTS idx_article_variables_var ON article_variables(variable_id);

/* ---------- Views analiticas ---------- */

CREATE VIEW IF NOT EXISTS v_articles_full AS
SELECT
  a.*,
  rl.name AS research_line,
  rl.code AS research_line_code,
  (SELECT group_concat(aa.author_name, '; ')
     FROM (SELECT author_name, article_id FROM article_authors ORDER BY author_order) aa
    WHERE aa.article_id = a.id) AS authors,
  (SELECT COUNT(*) FROM submissions s WHERE s.article_id = a.id) AS submission_attempts,
  (SELECT COUNT(*) FROM submissions s WHERE s.article_id = a.id
     AND s.decision IN ('rejeitado', 'desk_reject')) AS rejections,
  CASE WHEN a.started_on IS NOT NULL AND a.published_on IS NOT NULL
       THEN CAST(julianday(a.published_on) - julianday(a.started_on) AS INTEGER)
  END AS days_start_to_publication,
  CASE WHEN a.first_submission_on IS NOT NULL AND a.accepted_on IS NOT NULL
       THEN CAST(julianday(a.accepted_on) - julianday(a.first_submission_on) AS INTEGER)
  END AS days_submission_to_acceptance,
  CASE WHEN a.accepted_on IS NOT NULL AND a.published_on IS NOT NULL
       THEN CAST(julianday(a.published_on) - julianday(a.accepted_on) AS INTEGER)
  END AS days_acceptance_to_publication
FROM articles a
LEFT JOIN research_lines rl ON rl.id = a.research_line_id;

CREATE VIEW IF NOT EXISTS v_member_productivity AS
SELECT
  m.id AS member_id,
  m.full_name,
  m.short_name,
  m.role,
  m.is_external,
  rl.name AS research_line,
  COUNT(DISTINCT aa.article_id) AS n_articles,
  SUM(CASE WHEN a.status = 'publicado' THEN 1 ELSE 0 END) AS n_published,
  SUM(CASE WHEN a.status IN ('submetido', 'em_revisao') THEN 1 ELSE 0 END) AS n_submitted,
  SUM(CASE WHEN a.status = 'em_producao' THEN 1 ELSE 0 END) AS n_in_progress,
  SUM(CASE WHEN aa.author_order = 1 THEN 1 ELSE 0 END) AS n_first_author,
  SUM(CASE WHEN aa.is_corresponding = 1 THEN 1 ELSE 0 END) AS n_corresponding,
  COALESCE(SUM(a.scopus_citations), 0) AS scopus_citations,
  COALESCE(SUM(a.wos_citations), 0) AS wos_citations
FROM members m
LEFT JOIN article_authors aa ON aa.member_id = m.id
LEFT JOIN articles a ON a.id = aa.article_id
LEFT JOIN research_lines rl ON rl.id = m.research_line_id
GROUP BY m.id;

CREATE VIEW IF NOT EXISTS v_publications_by_year AS
SELECT
  year_published AS year,
  COUNT(*) AS n_articles,
  COALESCE(SUM(scopus_citations), 0) AS scopus_citations,
  COALESCE(SUM(wos_citations), 0) AS wos_citations,
  COALESCE(SUM(openalex_citations), 0) AS openalex_citations
FROM articles
WHERE status = 'publicado' AND year_published IS NOT NULL
GROUP BY year_published;

CREATE VIEW IF NOT EXISTS v_rejection_reasons AS
SELECT
  COALESCE(rr.label, s.rejection_notes, 'Nao informado') AS reason,
  COALESCE(rr.category, 'Nao classificado') AS category,
  COUNT(*) AS n
FROM submissions s
LEFT JOIN rejection_reasons rr ON rr.id = s.rejection_reason_id
WHERE s.decision IN ('rejeitado', 'desk_reject')
GROUP BY reason, category;

CREATE VIEW IF NOT EXISTS v_resubmission_gaps AS
SELECT
  s.article_id,
  a.title,
  s.attempt_no,
  prev.submitted_on AS previous_submitted_on,
  prev.decision_on  AS previous_decision_on,
  s.submitted_on    AS submitted_on,
  CAST(julianday(s.submitted_on) - julianday(prev.submitted_on) AS INTEGER) AS days_between_submissions,
  CAST(julianday(s.submitted_on) - julianday(prev.decision_on) AS INTEGER) AS days_decision_to_resubmission
FROM submissions s
JOIN submissions prev
  ON prev.article_id = s.article_id AND prev.attempt_no = s.attempt_no - 1
JOIN articles a ON a.id = s.article_id
WHERE s.submitted_on IS NOT NULL AND prev.submitted_on IS NOT NULL;

CREATE VIEW IF NOT EXISTS v_article_progress AS
SELECT
  a.id AS article_id,
  a.internal_code,
  a.title,
  a.status,
  a.lead_name,
  (SELECT COUNT(*) FROM article_milestones m
     WHERE m.article_id = a.id AND m.milestone LIKE 'versao%' AND m.occurred_on IS NOT NULL) AS versions_done,
  (SELECT MAX(m.occurred_on) FROM article_milestones m
     WHERE m.article_id = a.id AND m.occurred_on IS NOT NULL) AS last_milestone_on,
  (SELECT m.milestone FROM article_milestones m
     WHERE m.article_id = a.id AND m.occurred_on IS NOT NULL
     ORDER BY m.occurred_on DESC, m.seq DESC LIMIT 1) AS last_milestone,
  CASE WHEN a.started_on IS NOT NULL
       THEN CAST(julianday('now') - julianday(a.started_on) AS INTEGER) END AS days_open
FROM articles a;

CREATE VIEW IF NOT EXISTS v_researcher AS
SELECT
  m.id,
  m.full_name,
  m.short_name,
  m.name_key,
  m.role,
  m.degree,
  m.email,
  m.phone,
  m.bio,
  m.photo_url,
  m.lattes_id,
  m.orcid,
  m.openalex_id,
  m.scopus_author_id,
  m.is_external,
  m.active,
  m.joined_on,
  m.login,
  m.user_role,
  m.must_change_password,
  m.last_login_at,
  m.h_index,
  m.h_index_source,
  m.h_index_scopus,
  m.h_index_wos,
  m.i10_index,
  m.citations_total,
  m.metrics_updated_at,
  /* vinculo, orientacao e prazos: e daqui que o mural tira as datas de
     defesa e o fim de bolsa, e o organograma tira quem orienta quem. */
  m.advisor_id,
  m.co_advisor_id,
  (SELECT o.full_name FROM members o WHERE o.id = m.advisor_id)    AS advisor,
  (SELECT o.full_name FROM members o WHERE o.id = m.co_advisor_id) AS co_advisor,
  m.thesis_title,
  m.thesis_kind,
  m.thesis_status,
  m.thesis_due_on,
  m.topics,
  m.scholarship,
  m.scholarship_until,
  rl.name AS research_line,
  rl.id   AS research_line_id,
  i.name  AS institution,
  (SELECT COUNT(DISTINCT aa.article_id) FROM article_authors aa
     WHERE aa.member_id = m.id) AS n_articles,
  (SELECT COUNT(DISTINCT aa.article_id) FROM article_authors aa
     JOIN articles a ON a.id = aa.article_id
    WHERE aa.member_id = m.id AND a.status = 'publicado') AS n_published,
  (SELECT COUNT(DISTINCT aa.article_id) FROM article_authors aa
     JOIN articles a ON a.id = aa.article_id
    WHERE aa.member_id = m.id AND a.status IN ('submetido','em_revisao')) AS n_submitted,
  (SELECT COUNT(DISTINCT aa.article_id) FROM article_authors aa
     JOIN articles a ON a.id = aa.article_id
    WHERE aa.member_id = m.id AND a.status = 'em_producao') AS n_in_progress,
  (SELECT COUNT(*) FROM project_members pm WHERE pm.member_id = m.id) AS n_projects,
  (SELECT group_concat(p.name, ' | ') FROM project_members pm
     JOIN projects p ON p.id = pm.project_id
    WHERE pm.member_id = m.id) AS projects,
  (SELECT COALESCE(SUM(a.scopus_citations), 0) FROM article_authors aa
     JOIN articles a ON a.id = aa.article_id WHERE aa.member_id = m.id) AS scopus_citations,
  (SELECT COALESCE(SUM(a.wos_citations), 0) FROM article_authors aa
     JOIN articles a ON a.id = aa.article_id WHERE aa.member_id = m.id) AS wos_citations,
  (SELECT COALESCE(SUM(a.openalex_citations), 0) FROM article_authors aa
     JOIN articles a ON a.id = aa.article_id WHERE aa.member_id = m.id) AS openalex_citations
FROM members m
LEFT JOIN research_lines rl ON rl.id = m.research_line_id
LEFT JOIN institutions i ON i.id = m.institution_id;

CREATE VIEW IF NOT EXISTS v_projects AS
SELECT
  p.*,
  rl.name AS research_line,
  COALESCE(p.coordinator_name, c.full_name) AS coordinator,
  (SELECT COUNT(*) FROM project_members pm WHERE pm.project_id = p.id) AS n_members,
  (SELECT group_concat(m.full_name, '; ') FROM project_members pm
     JOIN members m ON m.id = pm.member_id WHERE pm.project_id = p.id) AS members,
  (SELECT COUNT(*) FROM project_articles pa WHERE pa.project_id = p.id) AS n_articles
FROM projects p
LEFT JOIN research_lines rl ON rl.id = p.research_line_id
LEFT JOIN members c ON c.id = p.coordinator_id;

/* Referencia com o que a triagem ja disse sobre ela.

   `decision` na tabela e a decisao consolidada, gravada quando ha
   consenso. Aqui vem tudo o que permite calcular o estado sem
   depender dela: quantos ja opinaram, quantos incluiram, quantos
   excluiram, e se ha conflito. Triagem as cegas se apoia nisto --
   a lista de quem decidiu o que so e revelada quando o conflito
   aparece. */
CREATE VIEW IF NOT EXISTS v_refs AS
SELECT
  r.*,
  (SELECT COUNT(*) FROM screenings s
    WHERE s.ref_id = r.id AND s.stage = r.stage) AS n_triagens,
  (SELECT COUNT(*) FROM screenings s
    WHERE s.ref_id = r.id AND s.stage = r.stage AND s.decision = 'incluir') AS n_incluir,
  (SELECT COUNT(*) FROM screenings s
    WHERE s.ref_id = r.id AND s.stage = r.stage AND s.decision = 'excluir') AS n_excluir,
  (SELECT COUNT(*) FROM screenings s
    WHERE s.ref_id = r.id AND s.stage = r.stage AND s.decision = 'talvez') AS n_talvez,
  x.label AS reason_label,
  rv.reviewers_needed,
  rv.blind
FROM refs r
JOIN reviews rv ON rv.id = r.review_id
LEFT JOIN exclusion_reasons x ON x.id = r.reason_id;

/* O PRISMA, contado do banco. Nenhum destes numeros e digitado. */
CREATE VIEW IF NOT EXISTS v_prisma AS
SELECT
  rv.id AS review_id,
  rv.code,
  rv.title,
  (SELECT COALESCE(SUM(n_retrieved), 0) FROM review_searches s
    WHERE s.review_id = rv.id) AS identificados,
  (SELECT COUNT(*) FROM refs r WHERE r.review_id = rv.id) AS registros,
  (SELECT COUNT(*) FROM refs r
    WHERE r.review_id = rv.id AND r.duplicate_of IS NOT NULL) AS duplicados,
  (SELECT COUNT(*) FROM refs r
    WHERE r.review_id = rv.id AND r.duplicate_of IS NULL) AS triados,
  (SELECT COUNT(*) FROM refs r
    WHERE r.review_id = rv.id AND r.duplicate_of IS NULL
      AND r.stage = 'titulo_resumo' AND r.decision IS NULL) AS pendentes,
  (SELECT COUNT(*) FROM refs r
    WHERE r.review_id = rv.id AND r.duplicate_of IS NULL
      AND r.decision = 'excluir' AND r.stage = 'titulo_resumo') AS excluidos_triagem,
  (SELECT COUNT(*) FROM refs r
    WHERE r.review_id = rv.id AND r.duplicate_of IS NULL
      AND r.stage IN ('texto_completo', 'incluido')) AS texto_completo,
  (SELECT COUNT(*) FROM refs r
    WHERE r.review_id = rv.id AND r.duplicate_of IS NULL
      AND r.stage = 'texto_completo' AND r.decision = 'excluir') AS excluidos_texto,
  (SELECT COUNT(*) FROM refs r
    WHERE r.review_id = rv.id AND r.stage = 'incluido') AS incluidos
FROM reviews rv;
