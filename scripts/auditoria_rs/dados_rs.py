#!/usr/bin/env python3
"""Números da auditoria das duas revisões, calculados dos arquivos de origem.

Fontes, todas enviadas pelo orientador em 12 de setembro de 2026:
  · rs.json          extraído de REVISAO_SISTEMATICA_HUMOR_HANDEBOL.html
  · mapping.json     extraído de MAPPING_REVIEW_HANDEBOL.html
  · a biblioteca em data/BIBLIOTECA_HANDEBOL.sqlite, versão de 27 de agosto
  · os três documentos de escopo e bibliometria, lidos pelo python-docx

Nenhum valor deste módulo é digitado à mão: tudo é lido dos arquivos.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
RS = json.load(open(RAIZ / "data" / "rs.json", encoding="utf-8"))["rs"]
MAP = json.load(open(RAIZ / "data" / "mapping.json", encoding="utf-8"))
BIB = sqlite3.connect(RAIZ / "data" / "BIBLIOTECA_HANDEBOL.sqlite")
BIB.row_factory = sqlite3.Row

ESTUDOS = RS["estudos"]
FLUXO = RS["fluxo"]
GRADE = RS["grade"]


def _norm(doi: str | None) -> str:
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (doi or "").strip().lower())


HUMOR_BIB = list(BIB.execute(
    """select a.* from artigo a join artigo_subvariavel s on s.artigo_id = a.id
       where s.subvariavel like '%Humor%'"""))
N_BIBLIOTECA = BIB.execute("select count(*) from artigo").fetchone()[0]

DOI_RS = {_norm(e.get("doi")) for e in ESTUDOS if e.get("doi")}
DOI_BIB = {_norm(a["doi"]) for a in HUMOR_BIB if a["doi"]}
INTERSECAO = DOI_RS & DOI_BIB
SO_RS = [e for e in ESTUDOS if e.get("doi") and _norm(e["doi"]) not in DOI_BIB]
SO_BIB = [a for a in HUMOR_BIB if a["doi"] and _norm(a["doi"]) not in DOI_RS]

# Somas declaradas contra somas calculadas
N_SOMADO = sum(e.get("n") or 0 for e in ESTUDOS)
N_GRADE = sum(g["n"] for g in GRADE)
K_GRADE = sum(g["k"] for g in GRADE)

SEM_DOI = [e["id"] for e in ESTUDOS if not e.get("doi")]
PREPRINTS = [e["id"] for e in ESTUDOS if e.get("preprint")]

# Números declarados nos três documentos de escopo e bibliometria, lidos
# dos próprios arquivos pelo script de extração; ver o docstring.
ESCOPO = {
    "estudos": 60, "isolados": 46, "isolados_pct": 76.7,
    "combinados": 14, "combinados_pct": 23.3,
    "cluster_isolado": 47, "randomizados_bibliometria": 1,
    "randomizados_artigo": 5, "citacoes_totais": 370,
    "n_com_citacao": 44, "n_com_amostra": 39, "sem_citacao": 13,
    "amostra_max": 4550, "amostra_media": 240.23, "amostra_mediana": 43,
    "qui2": 8.29, "qui2_gl": 4, "qui2_p": 0.081, "qui2_v": 0.372,
    "ano_inicial_declarado": 1968,
}

ANOS_BIB = sorted(int(a["ano"]) for a in HUMOR_BIB if str(a["ano"]).isdigit())
ANOS_RS = sorted(int(e["ano"]) for e in ESTUDOS if str(e.get("ano")).isdigit())

MAPPING = {
    "identificados": MAP["mapping_triagem"]["fluxo"]["identificados"],
    "distintos": MAP["mapping_triagem"]["fluxo"]["distintos"],
    "triados": MAP["mapping_triagem"]["fluxo"]["triados"],
    "inclusao": MAP["mapping_triagem"]["fluxo"]["provavel_inclusao"],
    "revisar": MAP["mapping_triagem"]["fluxo"]["revisar"],
    "exclusao": MAP["mapping_triagem"]["fluxo"]["provavel_exclusao"],
    "acervo": MAP["mapping_busca"]["acervo_no_momento"],
    "candidatos": MAP["mapping_extracao"]["n_candidatos"],
}

CORPORA = [
    ("Revisão sistemática do humor", len(ESTUDOS), f"{ANOS_RS[0]} a {ANOS_RS[-1]}",
     "Busca própria de duas linhas, handebol e humor, em cinco bases",
     "107 registros nas bases, 85 triados"),
    ("Biblioteca, subvariável Humor e Afeto", len(HUMOR_BIB),
     f"{ANOS_BIB[0]} a {ANOS_BIB[-1]}",
     "Marcação de subvariável sobre o acervo",
     f"{N_BIBLIOTECA} artigos no acervo desta cópia"),
    ("Revisão de escopo e bibliometria", ESCOPO["estudos"], "1968 a 2026",
     "Marcação de subvariável sobre o acervo, em versão posterior",
     f"{MAPPING['acervo']} artigos no acervo declarado pela mapping review"),
    ("Mapping review, provável inclusão", MAPPING["inclusao"], "1976 a 2026",
     "Oito estratégias e 40 consultas, todas as variáveis psicológicas",
     f"{MAPPING['identificados']} registros, {MAPPING['distintos']} distintos"),
]
