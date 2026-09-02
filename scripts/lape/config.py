"""Caminhos e constantes de configuracao do pipeline."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
GEO_DIR = DATA_DIR / "geo"
SQL_DIR = ROOT / "sql"
DOCS_DIR = ROOT / "docs"

DB_PATH = Path(os.environ.get("LAPE_DB", DATA_DIR / "db.sqlite"))
SCHEMA_PATH = SQL_DIR / "schema.sql"
REPORT_PATH = Path(os.environ.get("LAPE_REPORT", DOCS_DIR / "index.html"))

LAB_NAME = os.environ.get("LAPE_LAB_NAME", "LAPE - Laboratorio de Psicologia do Esporte e do Exercicio")
LAB_INSTITUTION = os.environ.get("LAPE_INSTITUTION", "UDESC / CEFID")
LAB_SITE = os.environ.get("LAPE_SITE", "https://www.udesc.br/cefid/lape")

# Logotipo do laboratorio. Vazio: procura-se data/logo.svg|png|webp|jpg.
# O arquivo viaja EMBUTIDO nas paginas -- ver marca.py.
LOGO_PATH = os.environ.get("LAPE_LOGO", "")

# Janela padrao das analises "ultimos N anos"
WINDOW_YEARS = int(os.environ.get("LAPE_WINDOW_YEARS", "5"))

# Credenciais das bases de citacao (opcionais)
SCOPUS_API_KEY = os.environ.get("SCOPUS_API_KEY", "")
SCOPUS_INST_TOKEN = os.environ.get("SCOPUS_INST_TOKEN", "")
WOS_API_KEY = os.environ.get("WOS_API_KEY", "")

# Status canonicos
ARTICLE_STATUS = (
    "em_producao",
    "submetido",
    "em_revisao",
    "aceito",
    "publicado",
    "rejeitado",
    "arquivado",
)

SUBMISSION_DECISION = (
    "em_avaliacao",
    "revisao_solicitada",
    "aceito",
    "rejeitado",
    "desk_reject",
    "retirado",
)

EVENT_KINDS = (
    "reuniao",
    "coleta",
    "defesa",
    "qualificacao",
    "congresso",
    "curso",
    "seminario",
    "visita_tecnica",
    "extensao",
    "outro",
)
