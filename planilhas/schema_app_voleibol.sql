-- =============================================================================
-- ESQUEMA DE BANCO DE DADOS — APP DE CONTROLE E PRESCRIÇÃO DE TREINAMENTO
-- Voleibol · espelha a Planilha_Voleibol_Forca_e_Potencia_v2.xlsx
-- PostgreSQL 13+
--
-- LGPD: as tabelas atleta, atleta_socioeconomico e atleta_saude guardam dados
-- pessoais e de saúde (dados sensíveis, art. 5º II). Colete com consentimento
-- por escrito, restrinja o acesso por papel e registre o log de quem lê.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS volei;
SET search_path TO volei, public;

-- -----------------------------------------------------------------------------
-- 0) DOMÍNIOS / LISTAS  (equivale à aba "Listas")
-- -----------------------------------------------------------------------------
CREATE TABLE lista (
    id          SERIAL PRIMARY KEY,
    dominio     TEXT NOT NULL,          -- 'posicao', 'escolaridade', 'tipo_sessao'...
    valor       TEXT NOT NULL,
    ordem       INT  NOT NULL DEFAULT 0,
    ativo       BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (dominio, valor)
);
COMMENT ON TABLE lista IS 'Opções dos menus suspensos do app. Um registro por opção de cada domínio.';

-- -----------------------------------------------------------------------------
-- 1) ESTRUTURA ORGANIZACIONAL
-- -----------------------------------------------------------------------------
CREATE TABLE clube (
    id          SERIAL PRIMARY KEY,
    nome        TEXT NOT NULL,
    cidade_uf   TEXT,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE equipe (
    id          SERIAL PRIMARY KEY,
    clube_id    INT  NOT NULL REFERENCES clube(id) ON DELETE CASCADE,
    nome        TEXT NOT NULL,
    categoria   TEXT NOT NULL,          -- Sub-15, Sub-17, Sub-19, Sub-21, Adulto...
    sexo        TEXT NOT NULL CHECK (sexo IN ('Masculino','Feminino','Misto')),
    temporada   TEXT NOT NULL,
    UNIQUE (clube_id, nome, temporada)
);

CREATE TABLE usuario (
    id            SERIAL PRIMARY KEY,
    nome          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    papel         TEXT NOT NULL CHECK (papel IN ('admin','tecnico','preparador','fisioterapeuta',
                                                 'nutricionista','atleta')),
    atleta_id     INT,                  -- preenchido quando papel = 'atleta'
    senha_hash    TEXT NOT NULL,
    ativo         BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em     TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON COLUMN usuario.papel IS 'Controla o que cada perfil enxerga. O papel "atleta" só deve acessar os próprios dados.';

-- -----------------------------------------------------------------------------
-- 2) CADASTRO DO ATLETA  (aba "Cadastro")
-- -----------------------------------------------------------------------------
CREATE TABLE atleta (
    id                    SERIAL PRIMARY KEY,
    equipe_id             INT  NOT NULL REFERENCES equipe(id),
    codigo                TEXT UNIQUE,              -- ATL-001
    nome_completo         TEXT NOT NULL,
    nome_equipe           TEXT,                     -- como é chamado
    data_nascimento       DATE NOT NULL,
    sexo                  TEXT NOT NULL CHECK (sexo IN ('Masculino','Feminino')),
    nacionalidade         TEXT,
    naturalidade          TEXT,
    documento             TEXT,                     -- DADO PESSOAL: criptografe em repouso
    numero_camisa         SMALLINT,
    categoria             TEXT,
    posicao               TEXT,                     -- Levantador, Oposto, Ponteiro, Central, Líbero
    dominancia_mao        TEXT CHECK (dominancia_mao IN ('Destro','Canhoto','Ambidestro')),
    perna_impulsao        TEXT CHECK (perna_impulsao IN ('Esquerda','Direita','Ambas')),
    telefone              TEXT,
    email                 TEXT,
    endereco              TEXT,
    cidade_uf             TEXT,
    cep                   TEXT,
    contato_emergencia    TEXT,
    telefone_emergencia   TEXT,
    parentesco_emergencia TEXT,
    data_entrada          DATE,
    status                TEXT NOT NULL DEFAULT 'Ativo'
                          CHECK (status IN ('Ativo','Lesionado','Departamento Médico',
                                            'Em transição','Afastado','Inativo')),
    observacoes           TEXT,
    criado_em             TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_atleta_equipe ON atleta(equipe_id);
ALTER TABLE usuario ADD CONSTRAINT fk_usuario_atleta
    FOREIGN KEY (atleta_id) REFERENCES atleta(id) ON DELETE SET NULL;

-- 2.1) Bloco socioeconômico ---------------------------------------------------
CREATE TABLE atleta_socioeconomico (
    id                        SERIAL PRIMARY KEY,
    atleta_id                 INT NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    data_referencia           DATE NOT NULL DEFAULT CURRENT_DATE,
    escolaridade              TEXT,
    situacao_estudo           TEXT,          -- Cursando, Concluído, Trancado, Não estuda
    turno_estudo              TEXT,
    instituicao_ensino        TEXT,
    trabalha                  BOOLEAN,
    horas_trabalho_semana     SMALLINT,
    ocupacao                  TEXT,
    renda_familiar            NUMERIC(10,2),
    pessoas_domicilio         SMALLINT CHECK (pessoas_domicilio > 0),
    renda_per_capita          NUMERIC(10,2)
                              GENERATED ALWAYS AS (renda_familiar / NULLIF(pessoas_domicilio,0)) STORED,
    classe_economica          TEXT CHECK (classe_economica IN ('A','B1','B2','C1','C2','D-E')),
    tipo_moradia              TEXT,
    reside_com                TEXT,
    transporte_treino         TEXT,
    tempo_deslocamento_min    SMALLINT,
    recebe_bolsa              BOOLEAN,
    valor_bolsa               NUMERIC(10,2),
    beneficio_social          BOOLEAN,
    plano_saude               BOOLEAN,
    internet_domicilio        BOOLEAN,
    refeicoes_dia             SMALLINT,
    acompanhamento_nutricional BOOLEAN,
    observacoes               TEXT,
    UNIQUE (atleta_id, data_referencia)
);
COMMENT ON TABLE atleta_socioeconomico IS
  'Histórico: um registro por atualização, para acompanhar mudança de condição ao longo das temporadas.';

-- 2.2) Bloco histórico esportivo ---------------------------------------------
CREATE TABLE atleta_historico_esportivo (
    atleta_id             INT PRIMARY KEY REFERENCES atleta(id) ON DELETE CASCADE,
    idade_inicio_volei    SMALLINT,
    anos_treino_forca     SMALLINT,
    nivel_competitivo_max TEXT,
    clubes_anteriores     TEXT,
    selecoes              TEXT
);

-- 2.3) Bloco saúde ------------------------------------------------------------
CREATE TABLE atleta_saude (
    atleta_id             INT PRIMARY KEY REFERENCES atleta(id) ON DELETE CASCADE,
    tipo_sanguineo        TEXT,
    alergias              TEXT,
    medicamentos_uso      TEXT,
    cirurgias_previas     TEXT,
    lesoes_previas        TEXT,
    lesoes_ultimos_12m    SMALLINT DEFAULT 0,
    queixa_atual          TEXT,
    data_atestado         DATE,
    validade_atestado     DATE,
    parq_respondido       BOOLEAN DEFAULT FALSE,
    usa_oculos_lentes     BOOLEAN
);

CREATE TABLE lesao (
    id                SERIAL PRIMARY KEY,
    atleta_id         INT NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    data_ocorrencia   DATE NOT NULL,
    regiao_corporal   TEXT NOT NULL,
    lado              TEXT CHECK (lado IN ('Direito','Esquerdo','Bilateral','N/A')),
    mecanismo         TEXT CHECK (mecanismo IN ('Sobrecarga','Trauma','Recidiva','Indeterminado')),
    diagnostico       TEXT,
    gravidade         TEXT CHECK (gravidade IN ('Leve','Moderada','Grave')),
    dias_afastamento  INT,
    data_retorno      DATE,
    contexto          TEXT CHECK (contexto IN ('Treino de quadra','Musculação','Jogo','Fora do clube')),
    observacoes       TEXT
);
CREATE INDEX idx_lesao_atleta_data ON lesao(atleta_id, data_ocorrencia);

-- -----------------------------------------------------------------------------
-- 3) ANTROPOMETRIA  (aba "Antropometria" — perfil restrito ISAK)
-- -----------------------------------------------------------------------------
CREATE TABLE antropometria (
    id                    SERIAL PRIMARY KEY,
    atleta_id             INT  NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    data_avaliacao        DATE NOT NULL,
    momento               TEXT,
    avaliador             TEXT,
    massa_kg              NUMERIC(5,1),
    estatura_cm           NUMERIC(5,1),
    estatura_sentado_cm   NUMERIC(5,1),
    envergadura_cm        NUMERIC(5,1),
    -- dobras cutâneas (mm)
    db_triceps            NUMERIC(4,1), db_subescapular NUMERIC(4,1), db_biceps       NUMERIC(4,1),
    db_peitoral           NUMERIC(4,1), db_axilar_media NUMERIC(4,1), db_suprailiaca  NUMERIC(4,1),
    db_supraespinhal      NUMERIC(4,1), db_abdominal    NUMERIC(4,1), db_coxa_medial  NUMERIC(4,1),
    db_perna_medial       NUMERIC(4,1),
    -- perímetros (cm)
    per_braco_relaxado    NUMERIC(4,1), per_braco_contraido NUMERIC(4,1), per_antebraco NUMERIC(4,1),
    per_torax             NUMERIC(5,1), per_cintura         NUMERIC(5,1), per_abdomen   NUMERIC(5,1),
    per_quadril           NUMERIC(5,1), per_coxa            NUMERIC(4,1), per_perna     NUMERIC(4,1),
    per_punho             NUMERIC(4,1),
    -- diâmetros ósseos (cm)
    diam_biacromial       NUMERIC(4,1), diam_biileocristal NUMERIC(4,1),
    diam_umero            NUMERIC(4,1), diam_femur         NUMERIC(4,1),
    -- calculados pela aplicação (Jackson & Pollock 7 dobras + Siri; Heath-Carter)
    soma_7_dobras         NUMERIC(5,1),
    densidade_corporal    NUMERIC(7,5),
    percentual_gordura    NUMERIC(4,1),
    massa_gorda_kg        NUMERIC(5,1),
    massa_magra_kg        NUMERIC(5,1),
    imc                   NUMERIC(4,1),
    indice_cormico        NUMERIC(4,1),
    endomorfia            NUMERIC(4,2),
    mesomorfia            NUMERIC(4,2),
    ectomorfia            NUMERIC(4,2),
    observacoes           TEXT,
    UNIQUE (atleta_id, data_avaliacao)
);
CREATE INDEX idx_antropo_atleta_data ON antropometria(atleta_id, data_avaliacao DESC);

-- -----------------------------------------------------------------------------
-- 4) TESTES FÍSICOS E PERFIL FORÇA-VELOCIDADE  (abas "Testes" e "Perfil F-V-P")
-- -----------------------------------------------------------------------------
CREATE TABLE teste_fisico (
    id                    SERIAL PRIMARY KEY,
    atleta_id             INT  NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    data_teste            DATE NOT NULL,
    momento               TEXT,
    avaliador             TEXT,
    massa_kg              NUMERIC(5,1),
    -- específico do voleibol
    alcance_pe_cm         SMALLINT,
    alcance_ataque_cm     SMALLINT,
    alcance_bloqueio_cm   SMALLINT,
    impulsao_ataque_cm    SMALLINT GENERATED ALWAYS AS (alcance_ataque_cm   - alcance_pe_cm) STORED,
    impulsao_bloqueio_cm  SMALLINT GENERATED ALWAYS AS (alcance_bloqueio_cm - alcance_pe_cm) STORED,
    -- saltos
    squat_jump_cm         NUMERIC(4,1),
    cmj_cm                NUMERIC(4,1),
    cmj_bracos_cm         NUMERIC(4,1),
    drop_jump_cm          NUMERIC(4,1),
    tempo_contato_dj_s    NUMERIC(5,3),
    rsi                   NUMERIC(5,2),   -- drop_jump_cm/100 / tempo_contato_dj_s
    indice_elastico       NUMERIC(5,3),   -- (cmj - sj) / sj
    salto_aproximacao_cm  NUMERIC(4,1),
    potencia_pico_w       NUMERIC(8,2),   -- Sayers: 60,7*CMJ + 45,3*massa - 2055
    -- velocidade, agilidade e outros
    sprint_5m_s           NUMERIC(4,2), sprint_10m_s NUMERIC(4,2),
    t_test_s              NUMERIC(4,2), sheppard_s   NUMERIC(4,2),
    medicine_ball_m       NUMERIC(4,1), sentar_alcancar_cm NUMERIC(4,1),
    yoyo_ir1_m            INT,
    imtp_pico_n           NUMERIC(8,1),
    observacoes           TEXT,
    UNIQUE (atleta_id, data_teste)
);
CREATE INDEX idx_teste_atleta_data ON teste_fisico(atleta_id, data_teste DESC);

CREATE TABLE perfil_fv (
    id                SERIAL PRIMARY KEY,
    atleta_id         INT  NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    data_teste        DATE NOT NULL,
    massa_kg          NUMERIC(5,1) NOT NULL,
    push_off_m        NUMERIC(4,3) NOT NULL,   -- hPO
    f0_n              NUMERIC(8,1),
    v0_ms             NUMERIC(5,2),
    sfv               NUMERIC(9,2),            -- inclinação real (N·s/m)
    sfv_opt           NUMERIC(6,2),            -- inclinação ótima teórica (N·s/m/kg)
    pmax_w            NUMERIC(8,1),
    fv_imb            NUMERIC(5,3),            -- |Sfv rel| / |SFvopt|
    perfil            TEXT CHECK (perfil IN ('Déficit de FORÇA','Equilibrado','Déficit de VELOCIDADE')),
    r2                NUMERIC(5,4),
    UNIQUE (atleta_id, data_teste)
);

CREATE TABLE perfil_fv_salto (
    id                SERIAL PRIMARY KEY,
    perfil_fv_id      INT NOT NULL REFERENCES perfil_fv(id) ON DELETE CASCADE,
    carga_adicional_kg NUMERIC(5,1) NOT NULL,
    altura_salto_cm   NUMERIC(4,1)  NOT NULL,
    forca_media_n     NUMERIC(8,1),
    velocidade_media_ms NUMERIC(5,3),
    potencia_media_w  NUMERIC(8,1)
);

-- -----------------------------------------------------------------------------
-- 5) PERIODIZAÇÃO  (abas "Macrociclo", "Mesociclo", "Bloco Base", "Microciclo")
-- -----------------------------------------------------------------------------
CREATE TABLE macrociclo (
    id              SERIAL PRIMARY KEY,
    equipe_id       INT  NOT NULL REFERENCES equipe(id) ON DELETE CASCADE,
    nome            TEXT NOT NULL,
    data_inicio     DATE NOT NULL,       -- âncora da numeração de semanas
    data_fim        DATE NOT NULL,
    objetivo        TEXT,
    competicao_alvo TEXT,
    CHECK (data_fim > data_inicio)
);

CREATE TABLE mesociclo (
    id                  SERIAL PRIMARY KEY,
    macrociclo_id       INT  NOT NULL REFERENCES macrociclo(id) ON DELETE CASCADE,
    ordem               SMALLINT NOT NULL,
    nome                TEXT NOT NULL,
    periodo             TEXT,   -- Preparatório Geral, Pré-Competitivo, Competitivo I...
    bloco               TEXT CHECK (bloco IN ('Acumulação','Transmutação','Realização','Descarga')),
    data_inicio         DATE NOT NULL,
    data_fim            DATE NOT NULL,
    volume_pct          NUMERIC(4,3),
    intensidade_pct     NUMERIC(4,3),
    enfase_fisica       TEXT,
    enfase_tecnica      TEXT,
    enfase_tatica       TEXT,
    carga_alvo_semanal  INT,
    situacao            TEXT CHECK (situacao IN ('Planejado','Em execução','Concluído','Cancelado')),
    UNIQUE (macrociclo_id, ordem)
);

CREATE TABLE microciclo (
    id                  SERIAL PRIMARY KEY,
    mesociclo_id        INT  NOT NULL REFERENCES mesociclo(id) ON DELETE CASCADE,
    numero_semana       SMALLINT NOT NULL,   -- semana dentro do macrociclo
    nome                TEXT,
    tipo                TEXT CHECK (tipo IN ('Incorporação','Ordinário','Choque','Recuperativo',
                                             'Pré-Competitivo','Competitivo','Polimento (Taper)')),
    data_inicio         DATE NOT NULL,
    data_fim            DATE NOT NULL,
    objetivo            TEXT,
    sessoes_previstas   SMALLINT,
    volume_previsto_min INT,
    pse_media_prevista  NUMERIC(3,1),
    contatos_plio_alvo  INT,
    acwr_alvo           NUMERIC(4,2),
    UNIQUE (mesociclo_id, numero_semana)
);

CREATE TABLE sessao (
    id              SERIAL PRIMARY KEY,
    microciclo_id   INT  REFERENCES microciclo(id) ON DELETE SET NULL,
    equipe_id       INT  NOT NULL REFERENCES equipe(id),
    data_sessao     DATE NOT NULL,
    turno           TEXT CHECK (turno IN ('Manhã','Tarde','Noite')),
    codigo          TEXT,               -- 'A', 'B', 'C', 'S1 — Força'
    tipo            TEXT NOT NULL,      -- Técnico-Tático, Físico (Força), Coletivo/Jogo...
    local           TEXT,
    duracao_prevista_min SMALLINT,
    pse_prevista    SMALLINT CHECK (pse_prevista BETWEEN 0 AND 10),
    objetivo        TEXT,
    observacoes     TEXT
);
CREATE INDEX idx_sessao_data ON sessao(equipe_id, data_sessao);

-- -----------------------------------------------------------------------------
-- 6) EXERCÍCIOS E PRESCRIÇÃO  (abas "Exercícios", "Prescrição", "Prescrição Força")
-- -----------------------------------------------------------------------------
CREATE TABLE exercicio (
    id                  SERIAL PRIMARY KEY,
    codigo              TEXT UNIQUE,
    nome                TEXT NOT NULL UNIQUE,
    categoria           TEXT NOT NULL,   -- Técnico, Tático, Físico, Preventivo, Recuperação, Cognitivo
    fundamento          TEXT,            -- Saque, Recepção, Levantamento, Ataque, Bloqueio, Defesa
    capacidade_fisica   TEXT,            -- Força Máxima, Potência, Pliometria, Velocidade...
    objetivo            TEXT,
    descricao           TEXT,
    material            TEXT,
    duracao_sugerida_min SMALLINT,
    intensidade_sugerida TEXT,
    pse_sugerida        SMALLINT,
    nivel               TEXT CHECK (nivel IN ('Iniciante','Intermediário','Avançado')),
    ref_vbt             TEXT CHECK (ref_vbt IN ('Agachamento','Supino','Terra','—')),
    exercicio_ref_1rm_id INT REFERENCES exercicio(id),  -- de qual 1RM a carga é calculada
    link_video          TEXT,
    ativo               BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE prescricao (
    id                  BIGSERIAL PRIMARY KEY,
    sessao_id           INT  NOT NULL REFERENCES sessao(id) ON DELETE CASCADE,
    exercicio_id        INT  NOT NULL REFERENCES exercicio(id),
    atleta_id           INT  REFERENCES atleta(id) ON DELETE CASCADE,  -- NULL = equipe toda
    ordem               SMALLINT NOT NULL,
    bloco_sessao        TEXT,     -- Aquecimento, Ativação/Prevenção, Parte Principal, Volta à Calma
    objetivo            TEXT,     -- Força Máxima, Potência, Pliometria...
    series              SMALLINT,
    repeticoes          TEXT,     -- texto: aceita '8', '30 s', '20 tentativas'
    percentual_1rm      NUMERIC(4,3),
    carga_prescrita_kg  NUMERIC(6,2),
    velocidade_alvo_ms  NUMERIC(4,2),
    perda_velocidade_limite NUMERIC(4,3),
    pausa_s             SMALLINT,
    duracao_min         SMALLINT,
    pse_prevista        SMALLINT CHECK (pse_prevista BETWEEN 0 AND 10),
    criterio_progressao TEXT,
    observacoes         TEXT
);
CREATE INDEX idx_prescricao_sessao ON prescricao(sessao_id);
CREATE INDEX idx_prescricao_atleta ON prescricao(atleta_id);

CREATE TABLE execucao_serie (
    id                  BIGSERIAL PRIMARY KEY,
    prescricao_id       BIGINT NOT NULL REFERENCES prescricao(id) ON DELETE CASCADE,
    atleta_id           INT    NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    numero_serie        SMALLINT NOT NULL,
    repeticoes_feitas   SMALLINT,
    carga_usada_kg      NUMERIC(6,2),
    velocidade_media_ms NUMERIC(4,2),
    perda_velocidade    NUMERIC(4,3),
    rir                 SMALLINT,
    pse                 SMALLINT CHECK (pse BETWEEN 0 AND 10),
    tonelagem_kg        NUMERIC(9,2)
        GENERATED ALWAYS AS (COALESCE(repeticoes_feitas,0) * COALESCE(carga_usada_kg,0)) STORED,
    observacoes         TEXT,
    UNIQUE (prescricao_id, atleta_id, numero_serie)
);
COMMENT ON TABLE execucao_serie IS 'Série a série: é daqui que saem tonelagem, intensidade relativa e o controle de VBT.';

-- -----------------------------------------------------------------------------
-- 7) FORÇA MÁXIMA  (aba "Força 1RM")
-- -----------------------------------------------------------------------------
CREATE TABLE teste_1rm (
    id                SERIAL PRIMARY KEY,
    atleta_id         INT  NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    exercicio_id      INT  NOT NULL REFERENCES exercicio(id),
    data_teste        DATE NOT NULL,
    metodo            TEXT NOT NULL CHECK (metodo IN ('Direto (1RM real)','Estimado por repetições',
                                                      'Estimado por velocidade (VBT)','Carga máxima em treino')),
    carga_kg          NUMERIC(6,2) NOT NULL,
    repeticoes        SMALLINT NOT NULL DEFAULT 1,
    rm_epley          NUMERIC(6,2) GENERATED ALWAYS AS (carga_kg * (1 + repeticoes / 30.0)) STORED,
    rm_brzycki        NUMERIC(6,2) GENERATED ALWAYS AS
                      (CASE WHEN repeticoes < 37 THEN carga_kg / (1.0278 - 0.0278 * repeticoes) END) STORED,
    rm_adotado_kg     NUMERIC(6,2) NOT NULL,
    massa_corporal_kg NUMERIC(5,1),
    velocidade_media_ms NUMERIC(4,2),
    observacoes       TEXT,
    UNIQUE (atleta_id, exercicio_id, data_teste)
);
CREATE INDEX idx_1rm_atleta_ex ON teste_1rm(atleta_id, exercicio_id, data_teste DESC);

CREATE TABLE perfil_carga_velocidade (
    id            SERIAL PRIMARY KEY,
    atleta_id     INT REFERENCES atleta(id) ON DELETE CASCADE,  -- NULL = tabela de referência geral
    exercicio_id  INT NOT NULL REFERENCES exercicio(id),
    percentual_1rm NUMERIC(4,3) NOT NULL,
    velocidade_ms NUMERIC(4,2)  NOT NULL,
    data_medicao  DATE,
    UNIQUE (atleta_id, exercicio_id, percentual_1rm)
);
COMMENT ON TABLE perfil_carga_velocidade IS
  'Relação carga-velocidade. Com atleta_id NULL guarda os valores de referência da literatura; '
  'com atleta_id preenchido, o perfil individual (sempre preferível).';

-- -----------------------------------------------------------------------------
-- 8) CONTROLE DE CARGA  (abas "Carga (PSE)", "Wellness", "Presença", "Saltos")
-- -----------------------------------------------------------------------------
CREATE TABLE carga_sessao (
    id            BIGSERIAL PRIMARY KEY,
    atleta_id     INT  NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    sessao_id     INT  REFERENCES sessao(id) ON DELETE SET NULL,
    data_registro DATE NOT NULL,
    tipo_sessao   TEXT,
    duracao_min   SMALLINT NOT NULL CHECK (duracao_min >= 0),
    pse           SMALLINT NOT NULL CHECK (pse BETWEEN 0 AND 10),
    carga_ua      INT GENERATED ALWAYS AS (duracao_min * pse) STORED,
    observacoes   TEXT
);
CREATE INDEX idx_carga_atleta_data ON carga_sessao(atleta_id, data_registro);

CREATE TABLE wellness (
    id            BIGSERIAL PRIMARY KEY,
    atleta_id     INT  NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    data_registro DATE NOT NULL,
    sono          SMALLINT NOT NULL CHECK (sono          BETWEEN 1 AND 7),
    estresse      SMALLINT NOT NULL CHECK (estresse      BETWEEN 1 AND 7),
    fadiga        SMALLINT NOT NULL CHECK (fadiga        BETWEEN 1 AND 7),
    dor_muscular  SMALLINT NOT NULL CHECK (dor_muscular  BETWEEN 1 AND 7),
    hooper        SMALLINT GENERATED ALWAYS AS (sono + estresse + fadiga + dor_muscular) STORED,
    local_dor     TEXT,
    observacoes   TEXT,
    UNIQUE (atleta_id, data_registro)
);
COMMENT ON COLUMN wellness.hooper IS 'Índice de Hooper: 4 a 28. QUANTO MAIOR, PIOR.';

CREATE TABLE presenca (
    id             BIGSERIAL PRIMARY KEY,
    atleta_id      INT NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    sessao_id      INT NOT NULL REFERENCES sessao(id) ON DELETE CASCADE,
    situacao       TEXT NOT NULL CHECK (situacao IN ('Presente','Falta Justificada','Falta Não Justificada',
                                                     'Lesionado','Departamento Médico','Liberado',
                                                     'Seleção/Convocado')),
    minutos_participados SMALLINT,
    justificativa  TEXT,
    UNIQUE (atleta_id, sessao_id)
);

CREATE TABLE salto (
    id             BIGSERIAL PRIMARY KEY,
    atleta_id      INT  NOT NULL REFERENCES atleta(id) ON DELETE CASCADE,
    sessao_id      INT  REFERENCES sessao(id) ON DELETE SET NULL,
    data_registro  DATE NOT NULL,
    origem         TEXT NOT NULL CHECK (origem IN ('Pliometria','Treino de quadra','Jogo','Musculação')),
    contexto       TEXT,
    contatos       INT  NOT NULL CHECK (contatos >= 0),
    intensidade    TEXT,
    superficie     TEXT,
    altura_caixa_cm SMALLINT,
    altura_media_cm SMALLINT,
    pct_acima_80   NUMERIC(4,3),
    qualidade      SMALLINT CHECK (qualidade BETWEEN 1 AND 5),
    observacoes    TEXT
);
CREATE INDEX idx_salto_atleta_data ON salto(atleta_id, data_registro);

-- =============================================================================
-- 9) VIEWS DE APOIO (KPIs)
-- =============================================================================

-- 1RM atual de cada atleta em cada exercício ---------------------------------
CREATE OR REPLACE VIEW vw_1rm_atual AS
SELECT DISTINCT ON (t.atleta_id, t.exercicio_id)
       t.atleta_id, t.exercicio_id, e.nome AS exercicio,
       t.data_teste, t.rm_adotado_kg,
       ROUND(t.rm_adotado_kg / NULLIF(t.massa_corporal_kg,0), 2) AS forca_relativa
FROM teste_1rm t
JOIN exercicio e ON e.id = t.exercicio_id
ORDER BY t.atleta_id, t.exercicio_id, t.data_teste DESC;

-- Carga aguda (7 d), crônica (28 d) e ACWR por atleta e dia -------------------
CREATE OR REPLACE VIEW vw_carga_acwr AS
WITH diaria AS (
    SELECT atleta_id, data_registro, SUM(carga_ua)::NUMERIC AS carga_dia
    FROM carga_sessao GROUP BY atleta_id, data_registro
)
SELECT d.atleta_id,
       d.data_registro,
       d.carga_dia,
       SUM(d2.carga_dia) FILTER (WHERE d2.data_registro > d.data_registro - 7)  AS carga_aguda_7d,
       SUM(d2.carga_dia) FILTER (WHERE d2.data_registro > d.data_registro - 28) / 4 AS carga_cronica_28d,
       ROUND(
         SUM(d2.carga_dia) FILTER (WHERE d2.data_registro > d.data_registro - 7)
         / NULLIF(SUM(d2.carga_dia) FILTER (WHERE d2.data_registro > d.data_registro - 28) / 4, 0), 2
       ) AS acwr,
       (d.data_registro - MIN(d2.data_registro) + 1) AS dias_historico
FROM diaria d
JOIN diaria d2 ON d2.atleta_id = d.atleta_id AND d2.data_registro <= d.data_registro
GROUP BY d.atleta_id, d.data_registro, d.carga_dia;
COMMENT ON VIEW vw_carga_acwr IS
  'Só classifique a zona de risco quando dias_historico >= 21: antes disso a carga crônica é artificialmente baixa.';

-- Monotonia e strain semanais (Foster) ---------------------------------------
CREATE OR REPLACE VIEW vw_carga_semanal AS
WITH dias AS (
    SELECT c.atleta_id,
           date_trunc('week', c.data_registro)::DATE AS semana,
           c.data_registro,
           SUM(c.carga_ua)::NUMERIC AS carga_dia
    FROM carga_sessao c
    GROUP BY 1, 2, 3
),
completo AS (   -- inclui os dias de folga como zero
    SELECT a.atleta_id, s.semana, g.dia,
           COALESCE(d.carga_dia, 0) AS carga_dia
    FROM (SELECT DISTINCT atleta_id FROM dias) a
    CROSS JOIN (SELECT DISTINCT semana FROM dias) s
    CROSS JOIN generate_series(0, 6) AS g(dia)
    LEFT JOIN dias d ON d.atleta_id = a.atleta_id AND d.semana = s.semana
                    AND d.data_registro = s.semana + g.dia
)
SELECT atleta_id, semana,
       SUM(carga_dia)                              AS carga_semanal,
       ROUND(AVG(carga_dia), 1)                    AS media_diaria,
       ROUND(STDDEV_SAMP(carga_dia), 1)            AS desvio_padrao,
       ROUND(AVG(carga_dia) / NULLIF(STDDEV_SAMP(carga_dia), 0), 2) AS monotonia,
       ROUND(SUM(carga_dia) * AVG(carga_dia) / NULLIF(STDDEV_SAMP(carga_dia), 0), 0) AS strain
FROM completo
GROUP BY atleta_id, semana;

-- Carga de saltos por atleta e semana ----------------------------------------
CREATE OR REPLACE VIEW vw_saltos_semana AS
SELECT atleta_id,
       date_trunc('week', data_registro)::DATE AS semana,
       SUM(contatos) FILTER (WHERE origem = 'Pliometria')       AS plio,
       SUM(contatos) FILTER (WHERE origem = 'Treino de quadra') AS quadra,
       SUM(contatos) FILTER (WHERE origem = 'Jogo')             AS jogo,
       SUM(contatos)                                            AS total
FROM salto GROUP BY 1, 2;

-- Tonelagem e intensidade relativa por atleta e semana ------------------------
CREATE OR REPLACE VIEW vw_forca_semana AS
SELECT ex.atleta_id,
       date_trunc('week', s.data_sessao)::DATE AS semana,
       SUM(ex.tonelagem_kg)                                        AS tonelagem_kg,
       SUM(ex.repeticoes_feitas)                                   AS repeticoes,
       ROUND(SUM(ex.repeticoes_feitas * p.percentual_1rm)
             / NULLIF(SUM(ex.repeticoes_feitas) FILTER (WHERE p.percentual_1rm IS NOT NULL), 0), 3)
                                                                   AS intensidade_media_relativa
FROM execucao_serie ex
JOIN prescricao p ON p.id = ex.prescricao_id
JOIN sessao     s ON s.id = p.sessao_id
GROUP BY 1, 2;

-- =============================================================================
-- 10) GATILHO DE ATUALIZAÇÃO
-- =============================================================================
CREATE OR REPLACE FUNCTION set_atualizado_em() RETURNS TRIGGER AS $$
BEGIN NEW.atualizado_em := now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_atleta_atualizado
    BEFORE UPDATE ON atleta
    FOR EACH ROW EXECUTE FUNCTION set_atualizado_em();
