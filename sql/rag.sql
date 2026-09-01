-- Camada de recuperacao semantica (RAG) do LAPE.
-- Carregada sob demanda por scripts/lape/rag/store.py; nao faz parte do
-- schema.sql principal para que o sistema continue a funcionar sem ela.

-- Um documento e qualquer fonte indexavel: um artigo do banco, uma
-- referencia de revisao, um PDF da tese, um capitulo em .docx.
CREATE TABLE IF NOT EXISTS rag_documents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    uri           TEXT NOT NULL UNIQUE,   -- caminho, DOI ou lape://articles/12
    kind          TEXT NOT NULL,          -- article | ref | tese | nota | externo
    title         TEXT,
    authors       TEXT,
    year          INTEGER,
    source        TEXT,                   -- periodico, base ou pasta de origem
    doi           TEXT,
    lang          TEXT,
    ref_table     TEXT,                   -- tabela do banco de origem, se houver
    ref_id        INTEGER,                -- id na tabela de origem
    content_hash  TEXT NOT NULL,          -- sha256 do texto extraido
    n_chars       INTEGER NOT NULL DEFAULT 0,
    n_chunks      INTEGER NOT NULL DEFAULT 0,
    meta          TEXT,                   -- JSON livre
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rag_docs_kind ON rag_documents(kind, year);
CREATE INDEX IF NOT EXISTS idx_rag_docs_ref ON rag_documents(ref_table, ref_id);
CREATE INDEX IF NOT EXISTS idx_rag_docs_hash ON rag_documents(content_hash);

-- Cada trecho e a unidade recuperada. O texto fica aqui; o vetor, ao lado.
CREATE TABLE IF NOT EXISTS rag_chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      INTEGER NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    ordinal     INTEGER NOT NULL,         -- posicao do trecho no documento
    section     TEXT,                     -- titulo da secao, quando detectavel
    text        TEXT NOT NULL,
    n_tokens    INTEGER NOT NULL DEFAULT 0,
    char_start  INTEGER NOT NULL DEFAULT 0,
    char_end    INTEGER NOT NULL DEFAULT 0,
    UNIQUE(doc_id, ordinal)
);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc ON rag_chunks(doc_id);

-- Vetores em BLOB float32. model + dim ficam gravados para que uma troca de
-- modelo seja detectada em vez de produzir busca silenciosamente errada.
CREATE TABLE IF NOT EXISTS rag_vectors (
    chunk_id  INTEGER PRIMARY KEY REFERENCES rag_chunks(id) ON DELETE CASCADE,
    model     TEXT NOT NULL,
    dim       INTEGER NOT NULL,
    norm      REAL NOT NULL,              -- norma L2 antes da normalizacao
    vec       BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rag_vectors_model ON rag_vectors(model);

-- Indice lexico. FTS5 acompanha o SQLite; sustenta a metade BM25 da busca.
CREATE VIRTUAL TABLE IF NOT EXISTS rag_fts USING fts5(
    text,
    content='rag_chunks',
    content_rowid='id',
    tokenize="unicode61 remove_diacritics 2"
);

CREATE TRIGGER IF NOT EXISTS rag_fts_ai AFTER INSERT ON rag_chunks BEGIN
    INSERT INTO rag_fts(rowid, text) VALUES (new.id, new.text);
END;
CREATE TRIGGER IF NOT EXISTS rag_fts_ad AFTER DELETE ON rag_chunks BEGIN
    INSERT INTO rag_fts(rag_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;
CREATE TRIGGER IF NOT EXISTS rag_fts_au AFTER UPDATE ON rag_chunks BEGIN
    INSERT INTO rag_fts(rag_fts, rowid, text) VALUES ('delete', old.id, old.text);
    INSERT INTO rag_fts(rowid, text) VALUES (new.id, new.text);
END;

-- Registro de cada indexacao e de cada consulta, para auditoria e custo.
CREATE TABLE IF NOT EXISTS rag_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,            -- index | search | agent
    agent       TEXT,
    query       TEXT,
    model       TEXT,
    n_docs      INTEGER DEFAULT 0,
    n_chunks    INTEGER DEFAULT 0,
    n_tokens    INTEGER DEFAULT 0,
    ms          INTEGER DEFAULT 0,
    detail      TEXT,
    at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rag_runs_kind ON rag_runs(kind, at);
