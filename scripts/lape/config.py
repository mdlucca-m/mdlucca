"""Caminhos e constantes de configuracao do pipeline."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _carregar_env(raiz: Path) -> str:
    """Le o `.env` para dentro do ambiente, antes de qualquer leitura abaixo.

    Isto morava so nos scripts de subida -- `publicar.sh` fazia `set -a`,
    `publicar.ps1` fazia SetEnvironmentVariable, o systemd tinha
    EnvironmentFile. Quem subia o sistema por qualquer OUTRO caminho --
    `Abrir LAPE.bat`, `python scripts/lape_agent.py api`, um teste, o
    agente rastreador -- rodava sem chave nenhuma, e a tela de citacoes
    respondia "falta configurar" com a chave escrita ali na raiz. O
    remedio nao e mais um script: e ler aqui, no unico lugar por onde
    todos passam.

    O ambiente de verdade VENCE o arquivo. Um `SCOPUS_API_KEY=...` posto
    na mao antes do comando tem de valer, e e assim que os tres scripts
    de subida continuam mandando no que ja mandavam.

    Devolve o nome do arquivo lido, ou "" -- e o que a tela mostra para
    responder "de onde saiu essa chave?" sem abrir o arquivo.
    """
    # O Bloco de Notas grava ".env.txt" quando se pede ".env", e nao avisa.
    # Aceitar os dois e mais barato do que explicar a extensao escondida.
    for nome in (".env", ".env.txt"):
        alvo = raiz / nome
        if not alvo.is_file():
            continue
        try:
            # utf-8-sig: o Bloco de Notas ainda poe BOM, e com ele a
            # PRIMEIRA linha do arquivo vira uma chave com lixo na frente
            # -- some so a de cima, o que e pior do que sumirem todas.
            linhas = alvo.read_text(encoding="utf-8-sig").splitlines()
        except (OSError, UnicodeDecodeError):
            return ""
        for linha in linhas:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            if linha.startswith("export "):
                linha = linha[7:].lstrip()
            chave, _, valor = linha.partition("=")
            chave = chave.strip()
            if not chave.replace("_", "").isalnum():
                continue
            valor = valor.strip()
            if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
                valor = valor[1:-1]
            os.environ.setdefault(chave, valor)
        return nome
    return ""


ENV_LIDO = _carregar_env(ROOT)

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

# E-mail de contato. A OpenAlex e a Crossref atendem numa fila mais rapida
# quem se identifica ("polite pool"), e `sources.py` ja passa o parametro
# `mailto` em toda consulta -- mas o unico lugar que o PRODUZ e este. Sem a
# constante aqui, o `getattr(config, "CONTACT_EMAIL", None)` devolvia None
# em silencio, e o laboratorio ficava na fila anonima com o e-mail ja
# escrito no `.env`.
CONTACT_EMAIL = os.environ.get("LAPE_CONTACT_EMAIL", "")

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
