-- Base única do estudo de humor em atletas de handebol.
-- Camada 1 (canônica): dados limpos, categorizados, prontos para análise.
-- Camada 2 (resultados): todo resultado estatístico em uma tabela longa e consultável.
-- Camada 3 (acervo): tudo o que existe nas planilhas, com procedência, para consulta.
PRAGMA journal_mode=WAL;

-- ---------------- camada 1: canônica ----------------
CREATE TABLE IF NOT EXISTS atleta (
  atleta        TEXT PRIMARY KEY,            -- A01..A27 (nenhum nome é armazenado)
  n_registros   INTEGER NOT NULL,
  n_dias        INTEGER NOT NULL,
  n_pre_pos     INTEGER NOT NULL,
  tem_d1        INTEGER NOT NULL,
  tem_d7        INTEGER NOT NULL,
  assiduidade   TEXT NOT NULL                -- 'completa' | 'parcial' | 'esparsa'
);

CREATE TABLE IF NOT EXISTS dia (
  dia            INTEGER PRIMARY KEY CHECK(dia BETWEEN 1 AND 7),
  data           TEXT NOT NULL,
  tipo_estimulo  TEXT NOT NULL,              -- Basal | HIIT | Amistoso | Técnico/força
  conteudo       TEXT NOT NULL,
  horas          REAL NOT NULL,
  sessoes        INTEGER NOT NULL,
  carga_acumulada REAL NOT NULL,
  n_registros    INTEGER NOT NULL,
  n_atletas      INTEGER NOT NULL,
  janela         TEXT NOT NULL               -- descrição da janela horária observada
);

CREATE TABLE IF NOT EXISTS variavel (
  variavel   TEXT PRIMARY KEY,
  rotulo     TEXT NOT NULL,
  familia    TEXT NOT NULL,                  -- BRUMS | composto | fadiga | sono | estresse
  minimo     REAL, maximo REAL,
  direcao    TEXT NOT NULL,                  -- 'alto pior' | 'alto melhor'
  norma_m    REAL, norma_dp REAL
);

CREATE TABLE IF NOT EXISTS registro (
  id          INTEGER PRIMARY KEY,
  atleta      TEXT NOT NULL REFERENCES atleta(atleta),
  dia         INTEGER NOT NULL REFERENCES dia(dia),
  carimbo     TEXT NOT NULL,
  hora        TEXT NOT NULL,
  periodo     TEXT NOT NULL,                 -- madrugada | manhã | tarde | noite
  momento     TEXT NOT NULL,                 -- pré | pós | único | intermediário
  ordem_no_dia INTEGER NOT NULL,
  tensao REAL, depressao REAL, raiva REAL, vigor REAL, fadiga REAL, confusao REAL, pth REAL,
  fadiga_fisica REAL, fadiga_mental REAL, epworth REAL, pss REAL,
  UNIQUE(atleta, carimbo)
);

CREATE TABLE IF NOT EXISTS atleta_dia (
  atleta   TEXT NOT NULL REFERENCES atleta(atleta),
  dia      INTEGER NOT NULL REFERENCES dia(dia),
  n_obs    INTEGER NOT NULL,
  tensao REAL, depressao REAL, raiva REAL, vigor REAL, fadiga REAL, confusao REAL, pth REAL,
  fadiga_fisica REAL, fadiga_mental REAL, epworth REAL, pss REAL,
  t_tensao REAL, t_depressao REAL, t_raiva REAL, t_vigor REAL, t_fadiga REAL, t_confusao REAL,
  perfil   TEXT NOT NULL,
  faixa    TEXT NOT NULL,                    -- Favorável | Neutra | De risco
  PRIMARY KEY (atleta, dia)
);

CREATE TABLE IF NOT EXISTS pre_pos (
  atleta TEXT NOT NULL REFERENCES atleta(atleta),
  dia    INTEGER NOT NULL REFERENCES dia(dia),
  hora_pre TEXT, hora_pos TEXT,
  variavel TEXT NOT NULL REFERENCES variavel(variavel),
  pre REAL, pos REAL, delta REAL,
  PRIMARY KEY (atleta, dia, variavel)
);

CREATE TABLE IF NOT EXISTS serie_diaria (
  variavel TEXT NOT NULL, dia INTEGER NOT NULL,
  media REAL, erro_padrao REAL, suavizado REAL,
  derivada1 REAL, derivada2 REAL,
  piso_ruido REAL, e_choque INTEGER,
  PRIMARY KEY (variavel, dia)
);

CREATE TABLE IF NOT EXISTS serie_perfil (
  perfil TEXT NOT NULL, dia INTEGER NOT NULL,
  prevalencia REAL, erro_padrao REAL, suavizado REAL, derivada1 REAL,
  piso_ruido REAL, e_choque INTEGER,
  PRIMARY KEY (perfil, dia)
);

-- ---------------- camada 2: resultados ----------------
CREATE TABLE IF NOT EXISTS unidade_analise (
  sigla TEXT PRIMARY KEY, nome TEXT, n INTEGER, regra TEXT, usada_em TEXT, vies TEXT
);

CREATE TABLE IF NOT EXISTS resultado (
  id INTEGER PRIMARY KEY,
  dominio    TEXT NOT NULL,     -- descritiva | tendência | contraste | associação | categórica | modelo | confiabilidade | série
  via        TEXT NOT NULL,     -- não paramétrica | paramétrica | robusta | descritiva
  unidade    TEXT REFERENCES unidade_analise(sigla),
  variavel   TEXT,
  recorte    TEXT,              -- p.ex. 'D1→D7', 'HIIT', 'pré×pós'
  teste      TEXT NOT NULL,
  estatistica REAL, rotulo_estatistica TEXT,
  gl         TEXT,
  p          REAL, p_ajustado REAL, metodo_ajuste TEXT,
  efeito     REAL, rotulo_efeito TEXT,
  ic_inf REAL, ic_sup REAL,
  n INTEGER,
  significativo INTEGER,
  artigo TEXT                   -- 'A1' | 'A2' | 'ambos'
);
CREATE INDEX IF NOT EXISTS ix_res ON resultado(dominio, variavel, via);

CREATE TABLE IF NOT EXISTS prevalencia (
  id INTEGER PRIMARY KEY,
  unidade TEXT, recorte_tipo TEXT, recorte TEXT,   -- 'dia'|'estimulo'|'momento'|'geral'
  perfil TEXT, prevalencia REAL, n INTEGER, erro_padrao REAL
);

CREATE TABLE IF NOT EXISTS auditoria (
  id TEXT PRIMARY KEY, titulo TEXT, achado TEXT, correcao TEXT, impacto TEXT, gravidade TEXT
);

CREATE TABLE IF NOT EXISTS referencia (
  id INTEGER PRIMARY KEY, autores TEXT, ano INTEGER, titulo TEXT, veiculo TEXT,
  doi TEXT, url_doi TEXT, pubmed TEXT, url_pubmed TEXT, open_access INTEGER, url_oa TEXT,
  abnt TEXT, usada_em TEXT
);

-- ---------------- camada 3: acervo das planilhas ----------------
CREATE TABLE IF NOT EXISTS fonte (
  id INTEGER PRIMARY KEY, arquivo TEXT, papel TEXT, sha256 TEXT, n_abas INTEGER, nota TEXT
);
CREATE TABLE IF NOT EXISTS aba (
  id INTEGER PRIMARY KEY, fonte_id INTEGER REFERENCES fonte(id),
  nome TEXT, linhas INTEGER, colunas INTEGER, categoria TEXT, tem_dados INTEGER
);
CREATE TABLE IF NOT EXISTS celula (
  aba_id INTEGER REFERENCES aba(id), linha INTEGER, coluna INTEGER,
  cabecalho TEXT, valor_txt TEXT, valor_num REAL
);
CREATE INDEX IF NOT EXISTS ix_cel ON celula(aba_id, linha);
CREATE INDEX IF NOT EXISTS ix_cel_txt ON celula(valor_txt);

-- ---------------- vistas de conveniência ----------------
CREATE VIEW IF NOT EXISTS v_significativos AS
  SELECT dominio, via, variavel, recorte, teste, p, p_ajustado, efeito, rotulo_efeito, n, artigo
  FROM resultado WHERE significativo=1 ORDER BY dominio, variavel;

CREATE VIEW IF NOT EXISTS v_confronto_vias AS
  SELECT variavel, recorte,
    MAX(CASE WHEN via='não paramétrica' THEN p END) AS p_nao_param,
    MAX(CASE WHEN via='paramétrica'     THEN p END) AS p_param,
    MAX(CASE WHEN via='modelo misto'    THEN p END) AS p_misto
  FROM resultado WHERE dominio='tendência' GROUP BY variavel, recorte;

CREATE VIEW IF NOT EXISTS v_painel_dia AS
  SELECT d.dia, d.data, d.tipo_estimulo, d.carga_acumulada, d.n_atletas,
         ROUND(AVG(ad.vigor),2) AS vigor, ROUND(AVG(ad.fadiga),2) AS fadiga,
         ROUND(AVG(ad.pth),2) AS pth,
         ROUND(100.0*SUM(ad.faixa='De risco')/COUNT(*),1) AS pct_risco,
         ROUND(100.0*SUM(ad.perfil='Iceberg')/COUNT(*),1) AS pct_iceberg
  FROM dia d JOIN atleta_dia ad ON ad.dia=d.dia GROUP BY d.dia;
