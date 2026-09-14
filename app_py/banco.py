"""Banco de dados do ELASE — SQLite, esquema normalizado.

Só biblioteca padrão. O arquivo do banco é um só (`elase.db`) e pode ser
copiado, versionado ou aberto em qualquer ferramenta que leia SQLite.

Duas decisões que valem explicação:

* **Chaves estrangeiras ligadas.** SQLite as ignora por padrão, e aí uma série
  pode apontar para uma sessão que não existe mais sem ninguém reclamar. Aqui
  `PRAGMA foreign_keys=ON` vai em toda conexão.

* **Nada de dinheiro.** Não há coluna de salário, renda ou valor. Não é
  esquecimento: é regra do projeto, e a ausência da coluna é o que garante que
  ninguém guarde isso por engano.
"""

import sqlite3
import os
import json
from contextlib import contextmanager
from datetime import date, timedelta

CAMINHO = os.environ.get("ELASE_DB", os.path.join(os.path.dirname(__file__), "elase.db"))

ESQUEMA = """
PRAGMA journal_mode = WAL;

-- ── Configuração da equipe, uma linha só ────────────────────────────────────
CREATE TABLE IF NOT EXISTS config (
  id                INTEGER PRIMARY KEY CHECK (id = 1),
  equipe            TEXT    NOT NULL DEFAULT 'ELASE Voleibol Masculino',
  categoria         TEXT    NOT NULL DEFAULT 'Adulto',
  temporada         TEXT    NOT NULL DEFAULT '2026',
  macro_inicio      TEXT    NOT NULL,              -- 'aaaa-mm-dd', segunda-feira
  cadastro_liberado INTEGER NOT NULL DEFAULT 1,    -- 1 = atleta entra sem esperar
  pin_treinador     TEXT    NOT NULL DEFAULT '1234'
);

-- ── Periodização: um macrociclo de N blocos, que se repete sem teto ─────────
CREATE TABLE IF NOT EXISTS blocos (
  posicao      INTEGER PRIMARY KEY,   -- 1..N dentro do macrociclo
  bloco        TEXT    NOT NULL,
  micro        TEXT    NOT NULL,
  enfase       TEXT    NOT NULL,
  intensidade  REAL    NOT NULL CHECK (intensidade > 0 AND intensidade < 1),
  volume       REAL    NOT NULL CHECK (volume > 0),
  plio         INTEGER NOT NULL CHECK (plio >= 0)   -- contatos-alvo na semana
);

-- ── Biblioteca de exercícios ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS exercicios (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  nome    TEXT NOT NULL UNIQUE,
  grupo   TEXT NOT NULL CHECK (grupo IN
            ('Força','Potência','LPO','Pliometria','Técnico-Tático','Recuperação')),
  ref1rm  TEXT
);

-- ── Elenco ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS atletas (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  nome              TEXT    NOT NULL,
  apelido           TEXT    NOT NULL,
  nasc              TEXT,
  posicao           TEXT    CHECK (posicao IN
                      ('Levantador','Oposto','Ponteiro (Ponta)','Central','Líbero')),
  camisa            INTEGER,
  telefone          TEXT,
  estatura          REAL,                    -- cm
  massa             REAL,                    -- kg
  alcance_pe        REAL,
  alcance_ataque    REAL,
  alcance_bloqueio  REAL,
  anos_pratica      INTEGER,
  dominancia        TEXT,
  perna_impulsao    TEXT,
  escolaridade      TEXT,
  emergencia        TEXT,
  lesoes            TEXT,
  obs               TEXT,
  status            TEXT    NOT NULL DEFAULT 'Ativo'
                      CHECK (status IN ('Ativo','Inativo','Pendente')),
  criado_em         TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_atletas_status ON atletas(status);

-- ── Prescrição ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prescricoes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  data       TEXT    NOT NULL,                 -- 'aaaa-mm-dd'
  hora       TEXT    NOT NULL DEFAULT '09:00',
  tipo       TEXT    NOT NULL,
  objetivo   TEXT    NOT NULL DEFAULT '',
  bloco      TEXT    NOT NULL DEFAULT '',
  notas      TEXT    NOT NULL DEFAULT '',
  atleta_id  INTEGER REFERENCES atletas(id) ON DELETE CASCADE,  -- NULL = equipe
  dur_prev   INTEGER,
  criado_em  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_presc_data ON prescricoes(data);
-- Um dia, uma sessão de equipe: é o que o gerador usa para não duplicar.
CREATE UNIQUE INDEX IF NOT EXISTS ux_presc_dia_equipe
  ON prescricoes(data) WHERE atleta_id IS NULL;

CREATE TABLE IF NOT EXISTS presc_exercicios (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  prescricao_id INTEGER NOT NULL REFERENCES prescricoes(id) ON DELETE CASCADE,
  ordem         INTEGER NOT NULL,
  nome          TEXT    NOT NULL,
  grupo         TEXT    NOT NULL,
  series        INTEGER NOT NULL CHECK (series > 0),
  reps          TEXT    NOT NULL,
  pausa         INTEGER NOT NULL DEFAULT 90,
  pct_rm        REAL,
  ref1rm        TEXT,
  tempo         TEXT,
  rir           REAL,
  vel           TEXT,
  obs           TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_pex_presc ON presc_exercicios(prescricao_id);

-- ── Execução: uma linha por sessão de um atleta ─────────────────────────────
CREATE TABLE IF NOT EXISTS sessoes (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  atleta_id     INTEGER NOT NULL REFERENCES atletas(id) ON DELETE CASCADE,
  prescricao_id INTEGER REFERENCES prescricoes(id) ON DELETE SET NULL,
  data          TEXT    NOT NULL,
  tipo          TEXT    NOT NULL DEFAULT '',
  check_in      TEXT,
  check_out     TEXT,
  dur_min       INTEGER NOT NULL DEFAULT 0,
  pse           REAL,
  carga_ua      REAL    NOT NULL DEFAULT 0,
  tonelagem     REAL    NOT NULL DEFAULT 0,
  contatos      INTEGER NOT NULL DEFAULT 0,
  UNIQUE (atleta_id, prescricao_id)
);
CREATE INDEX IF NOT EXISTS ix_ses_atleta_data ON sessoes(atleta_id, data);

CREATE TABLE IF NOT EXISTS series (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  sessao_id  INTEGER NOT NULL REFERENCES sessoes(id) ON DELETE CASCADE,
  exercicio  INTEGER NOT NULL,          -- índice do exercício na prescrição
  numero     INTEGER NOT NULL,          -- 1ª, 2ª, 3ª série
  carga      REAL,
  reps       INTEGER,
  rir        REAL,
  vel        REAL,
  feita      INTEGER NOT NULL DEFAULT 0,
  UNIQUE (sessao_id, exercicio, numero)
);

-- ── Bem-estar diário e humor ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wellness (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  atleta_id   INTEGER NOT NULL REFERENCES atletas(id) ON DELETE CASCADE,
  data        TEXT    NOT NULL,
  sono_qual   INTEGER CHECK (sono_qual BETWEEN 1 AND 5),
  sono_horas  REAL,
  estresse    INTEGER CHECK (estresse BETWEEN 0 AND 10),
  dor         INTEGER CHECK (dor BETWEEN 0 AND 10),
  kss         INTEGER CHECK (kss BETWEEN 1 AND 9),
  UNIQUE (atleta_id, data)
);

-- A BRUMS tem 24 itens em 6 subescalas. Guardar item a item, e não só o total,
-- é o que permite ver uma Tensão alta escondida atrás de um Vigor alto.
CREATE TABLE IF NOT EXISTS brums (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  atleta_id  INTEGER NOT NULL REFERENCES atletas(id) ON DELETE CASCADE,
  data       TEXT    NOT NULL,
  momento    TEXT    NOT NULL DEFAULT 'pre' CHECK (momento IN ('pre','pos')),
  item       TEXT    NOT NULL,
  subescala  TEXT    NOT NULL,
  valor      INTEGER NOT NULL CHECK (valor BETWEEN 0 AND 4),
  UNIQUE (atleta_id, data, momento, item)
);
CREATE INDEX IF NOT EXISTS ix_brums_atleta ON brums(atleta_id, data);

-- ── Testes de campo ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS testes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  atleta_id  INTEGER NOT NULL REFERENCES atletas(id) ON DELETE CASCADE,
  data       TEXT    NOT NULL,
  tipo       TEXT    NOT NULL,              -- '1RM', 'Salto', 'Velocidade'
  exercicio  TEXT    NOT NULL,
  valor      REAL    NOT NULL,
  unidade    TEXT    NOT NULL DEFAULT 'kg'
);
CREATE INDEX IF NOT EXISTS ix_testes_atleta ON testes(atleta_id, tipo, exercicio, data);
"""

# ── BRUMS: os 24 itens e a subescala de cada um ──────────────────────────────
BRUMS_ITENS = [
    ("Tensão", ["Apreensivo", "Nervoso", "Ansioso", "Preocupado"]),
    ("Depressão", ["Deprimido", "Infeliz", "Desanimado", "Triste"]),
    ("Raiva", ["Irritado", "Zangado", "Mal-humorado", "Com raiva"]),
    ("Vigor", ["Animado", "Com energia", "Ativo", "Disposto"]),
    ("Fadiga", ["Esgotado", "Sonolento", "Cansado", "Sem energia"]),
    ("Confusão", ["Confuso", "Indeciso", "Desnorteado", "Inseguro"]),
]
SUBESCALAS = [s for s, _ in BRUMS_ITENS]
NEGATIVAS = ["Tensão", "Depressão", "Raiva", "Fadiga", "Confusão"]
ITEM_SUB = {i: s for s, itens in BRUMS_ITENS for i in itens}

POSICOES = ["Levantador", "Oposto", "Ponteiro (Ponta)", "Central", "Líbero"]
TIPOS = ["Força", "Potência", "LPO", "Pliometria", "Técnico-Tático", "Recuperação"]
# PSE presumida por tipo, usada só para ESTIMAR a carga da sessão prescrita.
# A carga que vale é a do check-out, com a PSE que o atleta informou.
PSE_TIPO = {"Força": 7, "Potência": 6.5, "LPO": 7, "Pliometria": 7,
            "Técnico-Tático": 7, "Recuperação": 3}

BLOCOS_PADRAO = [
    (1, "Acumulação", "Incorporação", "Adaptação anatômica e técnica de LPO", 0.62, 0.75, 60),
    (2, "Acumulação", "Ordinário", "Força máxima de base", 0.72, 0.88, 90),
    (3, "Acumulação", "CHOQUE", "Pico de volume da acumulação", 0.78, 1.00, 120),
    (4, "Descarga", "Recuperativo", "Assimilação e supercompensação", 0.66, 0.45, 45),
    (5, "Transmutação", "Ordinário", "Força máxima", 0.85, 0.75, 90),
    (6, "Transmutação", "Ordinário", "Força-velocidade", 0.90, 0.70, 110),
    (7, "Transmutação", "CHOQUE", "Sobrecarga concentrada de potência", 0.93, 0.85, 140),
    (8, "Realização", "Polimento", "Expressão de potência", 0.95, 0.42, 70),
]

EXERCICIOS_PADRAO = [
    ("Agachamento", "Força", "Agachamento"),
    ("Agachamento frontal", "Força", "Agachamento frontal"),
    ("Supino", "Força", "Supino"),
    ("Stiff com barra", "Força", "Stiff com barra"),
    ("Remada serrote", "Força", "Remada serrote"),
    ("Afundo frontal sem passada", "Força", None),
    ("Elevação de calcanhares", "Força", None),
    ("Nórdico de isquiotibiais (excêntrico)", "Força", None),
    ("Rotadores do ombro com elástico", "Força", None),
    ("Abdominal reto com braços esticados", "Força", None),
    ("Dorsal perdigueiro", "Força", None),
    ("Arranco", "LPO", "Arranco"),
    ("Clean", "LPO", "Clean"),
    ("Snatch pull / Hang high pull", "LPO", "Clean pull"),
    ("Agachamento com salto sob carga (jump squat)", "Potência", "Agachamento"),
    ("Sprints de 10 e 20 m com mudança de direção", "Potência", None),
    ("Drop jump 40 cm", "Pliometria", None),
    ("Salto no caixote", "Pliometria", None),
    ("Saltos consecutivos sobre barreiras", "Pliometria", None),
    ("Mobilidade de tornozelo e quadril", "Recuperação", None),
]


def segunda_desta_semana(hoje=None):
    """A segunda-feira da semana de `hoje`. O macrociclo sempre começa numa."""
    h = hoje or date.today()
    return (h - timedelta(days=h.weekday())).isoformat()


@contextmanager
def conectar(caminho=None):
    """Conexão com chaves estrangeiras LIGADAS e linhas como dicionário."""
    con = sqlite3.connect(caminho or CAMINHO)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def criar(caminho=None, macro_inicio=None):
    """Cria o esquema e semeia config, blocos e biblioteca. Idempotente."""
    with conectar(caminho) as con:
        con.executescript(ESQUEMA)
        if not con.execute("SELECT 1 FROM config WHERE id=1").fetchone():
            con.execute(
                "INSERT INTO config (id, macro_inicio) VALUES (1, ?)",
                (macro_inicio or segunda_desta_semana(),),
            )
        if not con.execute("SELECT 1 FROM blocos").fetchone():
            con.executemany(
                "INSERT INTO blocos (posicao,bloco,micro,enfase,intensidade,volume,plio)"
                " VALUES (?,?,?,?,?,?,?)", BLOCOS_PADRAO)
        if not con.execute("SELECT 1 FROM exercicios").fetchone():
            con.executemany(
                "INSERT INTO exercicios (nome,grupo,ref1rm) VALUES (?,?,?)",
                EXERCICIOS_PADRAO)


def dic(linha):
    return dict(linha) if linha is not None else None


def dics(linhas):
    return [dict(x) for x in linhas]


def config(con):
    return dic(con.execute("SELECT * FROM config WHERE id=1").fetchone())


def blocos(con):
    return dics(con.execute("SELECT * FROM blocos ORDER BY posicao").fetchall())


# ── Datas ────────────────────────────────────────────────────────────────────
def d(s):
    return date.fromisoformat(s)


def mais_dias(s, n):
    return (d(s) + timedelta(days=n)).isoformat()


def semana_de(data, macro_inicio):
    """Em que semana da temporada cai `data`. 1 é a primeira. Pode passar de 8:
    o macrociclo se repete, e a semana da temporada continua contando."""
    return (d(data) - d(macro_inicio)).days // 7 + 1


def plano_sessao(exercicios, tipo, dur_prev=None):
    """Duração, séries, contatos e carga prevista de uma sessão prescrita.

    A UA sai da duração ARREDONDADA de propósito: é o número que aparece na
    tela, e quem refizer a conta na mão tem de chegar no mesmo lugar."""
    series = sum(int(e["series"]) for e in exercicios)
    seg = 0.0
    for e in exercicios:
        r = _primeiro_numero(e["reps"]) or 6
        seg += int(e["series"]) * ((e.get("pausa") or 90) + r * 4)
    minutos = int(round(dur_prev if dur_prev else seg / 60))
    contatos = sum(int(e["series"]) * (_primeiro_numero(e["reps"]) or 0)
                   for e in exercicios if e["grupo"] == "Pliometria")
    pse = PSE_TIPO.get(tipo, 6)
    return {"series": series, "dur": minutos, "contatos": contatos,
            "pse": pse, "ua": int(round(minutos * pse)),
            "estimada": not dur_prev}


def _primeiro_numero(texto):
    """'3', '8 cada lado', '20 min' → 3, 8, 20. Nada de número → 0."""
    n = ""
    for ch in str(texto):
        if ch.isdigit():
            n += ch
        elif n:
            break
    return int(n) if n else 0
