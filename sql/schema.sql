-- Gerado por scripts/gerar_schema.py a partir de scripts/busca/deposito.py.
-- Não editar à mão: altere o DDL no módulo e regenere.

CREATE TABLE IF NOT EXISTS artigo (
    id INTEGER PRIMARY KEY, pmid TEXT, fonte TEXT, titulo TEXT, autores TEXT,
    pais TEXT, ano TEXT, revista TEXT, palavras_chave TEXT, instrumentos TEXT,
    variaveis_analisadas TEXT, populacao TEXT, amostra TEXT, estatistica TEXT,
    tipo_estudo TEXT, desenho_estudo TEXT, abordagem TEXT, pico_intervencao TEXT,
    pico_comparacao TEXT, pcc_conceito TEXT, pcc_contexto TEXT, sintese TEXT,
    resumo TEXT, doi TEXT, doi_suspeito INTEGER, citacoes INTEGER,
    fonte_metodos TEXT, link TEXT, volume TEXT, numero TEXT, paginas TEXT,
    referencia_abnt TEXT, referencia_vancouver TEXT, pmcid TEXT,
    tem_texto_completo INTEGER, texto_completo_arquivo TEXT, oa_status TEXT,
    oa_url TEXT
);
CREATE TABLE IF NOT EXISTS artigo_variavel (artigo_id INTEGER, variavel TEXT);
CREATE TABLE IF NOT EXISTS artigo_subvariavel (artigo_id INTEGER, subvariavel TEXT);
CREATE TABLE IF NOT EXISTS variavel (codigo TEXT PRIMARY KEY, rotulo TEXT, cor TEXT);
CREATE TABLE IF NOT EXISTS busca_execucao (
    id INTEGER PRIMARY KEY,
    quando TEXT NOT NULL,
    janela TEXT,
    identificados INTEGER,
    duplicatas INTEGER,
    unicos INTEGER,
    novos INTEGER,
    atualizados INTEGER,
    duracao_s INTEGER,
    consultas TEXT
);
CREATE TABLE IF NOT EXISTS busca_rendimento (
    execucao_id INTEGER NOT NULL REFERENCES busca_execucao(id),
    base TEXT NOT NULL,
    declarados INTEGER,
    recuperados INTEGER,
    erro TEXT,
    PRIMARY KEY (execucao_id, base)
);
CREATE TABLE IF NOT EXISTS busca_duplicata (
    execucao_id INTEGER NOT NULL REFERENCES busca_execucao(id),
    criterio TEXT NOT NULL,
    fonte TEXT,
    doi TEXT,
    pmid TEXT,
    titulo TEXT
);
CREATE VIEW IF NOT EXISTS v_rendimento_por_base AS
    SELECT e.quando, r.base, r.declarados, r.recuperados, r.erro
    FROM busca_rendimento r JOIN busca_execucao e ON e.id = r.execucao_id
    ORDER BY e.quando DESC, r.recuperados DESC;
CREATE UNIQUE INDEX IF NOT EXISTS ix_artigo_doi  ON artigo(doi)  WHERE doi  IS NOT NULL AND doi  <> '';
CREATE UNIQUE INDEX IF NOT EXISTS ix_artigo_pmid ON artigo(pmid) WHERE pmid IS NOT NULL AND pmid <> '';
CREATE INDEX IF NOT EXISTS ix_artigo_ano ON artigo(ano);
