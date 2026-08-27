"""Extracao da producao em formatos de troca internacionais.

O painel serve para olhar; isto serve para levar embora. Sao os tres
formatos que qualquer gestor de referencias e qualquer base aceitam:

  csv      planilha com os cabecalhos do modelo Scopus/WoS, em ingles
  bibtex   .bib, o padrao de LaTeX e do Zotero/Mendeley
  ris      .ris, o padrao do EndNote e da maioria dos gestores

Nada aqui inventa dado. Coluna sem valor sai vazia -- uma tabela de
extracao que preenche buraco com suposicao e pior do que uma com buraco,
porque o buraco pelo menos se ve.
"""
from __future__ import annotations

import csv
import io
import re
from typing import Any, Iterable

from .db import Database
from .util import author_key

FORMATOS = ("csv", "bibtex", "ris")

# Cabecalhos no modelo das exportacoes do Scopus e da Web of Science, para a
# planilha abrir reconhecivel em qualquer lugar. Os campos proprios do
# laboratorio vao depois, para nao atrapalhar quem importa a parte padrao.
COLUNAS: tuple[tuple[str, str], ...] = (
    ("Authors", "authors_citacao"),
    ("Author full names", "authors"),
    ("Title", "title"),
    ("Year", "year_published"),
    ("Source title", "journal"),
    ("DOI", "doi"),
    ("Link", "link"),
    ("Document Type", "document_type"),
    ("Language of Original Document", "language"),
    ("ISSN", "issn"),
    ("Cited by", "citations"),
    ("Cited by (Scopus)", "scopus_citations"),
    ("Cited by (WoS)", "wos_citations"),
    ("Cited by (OpenAlex)", "openalex_citations"),
    ("Open Access", "open_access_texto"),
    ("EID", "scopus_id"),
    ("UT (Unique WOS ID)", "wos_id"),
    ("Publication Stage", "estagio"),
    # --- campos do laboratorio, fora do padrao ---
    ("LAPE — Código interno", "internal_code"),
    ("LAPE — Linha de pesquisa", "research_line"),
    ("LAPE — Situação", "status"),
    ("LAPE — Tipo de estudo", "study_type"),
    ("LAPE — Qualis", "qualis"),
    ("LAPE — Fator de impacto", "impact_factor"),
    ("LAPE — Início", "started_on"),
    ("LAPE — 1ª submissão", "first_submission_on"),
    ("LAPE — Aceite", "accepted_on"),
    ("LAPE — Publicação", "published_on"),
    ("LAPE — Tentativas", "submission_attempts"),
    ("LAPE — Recusas", "rejections"),
)

TIPO_DE_DOCUMENTO = {
    "revisao sistematica": "Review",
    "revisao": "Review",
    "metanalise": "Review",
    "protocolo de estudo": "Article",
}

ESTAGIO = {
    "publicado": "Final",
    "aceito": "Article in Press",
    "submetido": "Submitted",
    "em_revisao": "Under review",
    "em_producao": "In preparation",
    "rejeitado": "Rejected",
    "arquivado": "Withdrawn",
}


def _citacao(nome: str) -> str:
    """'Marina Rossetto Cardoso' -> 'Cardoso M.R.' — a forma de citacao."""
    chave = author_key(nome)
    if not chave:
        return (nome or "").strip()
    sobrenome, _, iniciais = chave.partition("_")
    sobrenome = sobrenome.replace("-", " ").title().replace(" ", "-")
    if not iniciais:
        return sobrenome
    return sobrenome + " " + ".".join(letra.upper() for letra in iniciais) + "."


def _autores_citacao(texto: str | None) -> str:
    partes = [p.strip() for p in (texto or "").split(";") if p.strip()]
    return "; ".join(_citacao(p) for p in partes)


def linhas(db: Database, apenas_publicados: bool = False) -> list[dict[str, Any]]:
    """A producao, com as colunas derivadas que a extracao precisa."""
    filtro = " WHERE status = 'publicado'" if apenas_publicados else ""
    registros = db.dicts(
        "SELECT id, internal_code, title, authors, status, research_line, study_type, language,"
        "       started_on, first_submission_on, accepted_on, published_on, year_published,"
        "       journal, issn, qualis, impact_factor, doi, url, open_access,"
        "       wos_id, scopus_id, wos_citations, scopus_citations, openalex_citations,"
        "       submission_attempts, rejections"
        f" FROM v_articles_full{filtro}"
        " ORDER BY COALESCE(year_published, 9999) DESC, title")
    # A ordem dos autores nao e detalhe: primeiro autor e ultimo autor sao o
    # que a avaliacao le. A view monta a lista com group_concat, e o SQLite
    # nao garante a ordem de uma agregacao -- entao aqui a lista e remontada
    # a partir de article_authors, com ORDER BY explicito.
    por_artigo: dict[int, list[str]] = {}
    for linha in db.dicts("SELECT article_id, author_name FROM article_authors"
                          " ORDER BY article_id, author_order"):
        por_artigo.setdefault(linha["article_id"], []).append(linha["author_name"])

    for r in registros:
        ordenados = por_artigo.get(r.get("id"))
        if ordenados:
            r["authors"] = "; ".join(ordenados)
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", (r.get("doi") or "").strip(), flags=re.I)
        r["doi"] = doi
        r["authors_citacao"] = _autores_citacao(r.get("authors"))
        r["link"] = ("https://doi.org/" + doi) if doi else (r.get("url") or "")
        r["citations"] = max(int(r.get("scopus_citations") or 0),
                             int(r.get("wos_citations") or 0),
                             int(r.get("openalex_citations") or 0))
        r["document_type"] = TIPO_DE_DOCUMENTO.get(
            (r.get("study_type") or "").strip().lower(), "Article")
        r["estagio"] = ESTAGIO.get(r.get("status") or "", "")
        aberto = r.get("open_access")
        r["open_access_texto"] = "" if aberto is None else ("All Open Access" if aberto else "")
    return registros


def para_csv(registros: Iterable[dict[str, Any]]) -> str:
    saida = io.StringIO()
    # ponto e virgula e BOM: e assim que o Excel em portugues abre sem
    # embaralhar coluna e sem comer acento
    escritor = csv.writer(saida, delimiter=";", quoting=csv.QUOTE_MINIMAL,
                          lineterminator="\r\n")
    escritor.writerow([titulo for titulo, _ in COLUNAS])
    for r in registros:
        escritor.writerow(["" if r.get(campo) is None else str(r.get(campo))
                           for _, campo in COLUNAS])
    return "﻿" + saida.getvalue()


def _chave_bibtex(r: dict[str, Any], usadas: set[str]) -> str:
    primeiro = (r.get("authors") or "").split(";")[0]
    sobrenome = (author_key(primeiro).partition("_")[0] or "lape")
    base = f"{sobrenome}{r.get('year_published') or 'sd'}"
    chave, n = base, 1
    while chave in usadas:
        n += 1
        chave = f"{base}{chr(ord('a') + n - 2)}"
    usadas.add(chave)
    return chave


def _escapar_bibtex(texto: Any) -> str:
    return str(texto or "").replace("\\", r"\textbackslash{}").replace("{", r"\{") \
        .replace("}", r"\}").replace("&", r"\&").replace("%", r"\%").replace("$", r"\$") \
        .replace("#", r"\#").replace("_", r"\_")


def para_bibtex(registros: Iterable[dict[str, Any]]) -> str:
    blocos, usadas = [], set()
    for r in registros:
        campos = [
            ("author", " and ".join(p.strip() for p in (r.get("authors") or "").split(";") if p.strip())),
            ("title", r.get("title")),
            ("journal", r.get("journal")),
            ("year", r.get("year_published")),
            ("doi", r.get("doi")),
            ("url", r.get("link")),
            ("issn", r.get("issn")),
            ("language", r.get("language")),
            ("note", r.get("estagio") if (r.get("status") or "") != "publicado" else None),
        ]
        corpo = ",\n".join(f"  {nome} = {{{_escapar_bibtex(valor)}}}"
                           for nome, valor in campos if valor not in (None, "", 0))
        blocos.append(f"@article{{{_chave_bibtex(r, usadas)},\n{corpo}\n}}")
    return "\n\n".join(blocos) + "\n"


def para_ris(registros: Iterable[dict[str, Any]]) -> str:
    linhas_ris: list[str] = []
    for r in registros:
        linhas_ris.append("TY  - JOUR")
        for autor in [p.strip() for p in (r.get("authors") or "").split(";") if p.strip()]:
            linhas_ris.append(f"AU  - {_citacao(autor)}")
        for etiqueta, valor in (
            ("TI", r.get("title")), ("PY", r.get("year_published")),
            ("JO", r.get("journal")), ("SN", r.get("issn")),
            ("DO", r.get("doi")), ("UR", r.get("link")),
            ("LA", r.get("language")), ("KW", r.get("research_line")),
            ("N1", r.get("estagio") if (r.get("status") or "") != "publicado" else None),
        ):
            if valor not in (None, "", 0):
                linhas_ris.append(f"{etiqueta}  - {valor}")
        linhas_ris.append("ER  - ")
        linhas_ris.append("")
    return "\r\n".join(linhas_ris)


def extrair(db: Database, formato: str = "csv",
            apenas_publicados: bool = False) -> tuple[str, str, str]:
    """Devolve (conteudo, nome do arquivo, tipo MIME)."""
    if formato not in FORMATOS:
        raise ValueError(f"formato desconhecido: {formato}. Use {', '.join(FORMATOS)}")
    registros = linhas(db, apenas_publicados)
    sufixo = "-publicados" if apenas_publicados else ""
    if formato == "bibtex":
        return para_bibtex(registros), f"lape-producao{sufixo}.bib", "application/x-bibtex"
    if formato == "ris":
        return para_ris(registros), f"lape-producao{sufixo}.ris", "application/x-research-info-systems"
    return para_csv(registros), f"lape-producao{sufixo}.csv", "text/csv"
