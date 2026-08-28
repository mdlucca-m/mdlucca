"""Leitura dos formatos em que as bases entregam referencias.

Toda revisao sistematica comeca do mesmo jeito: buscar em cada base e
salvar o resultado num arquivo. Cada base entrega o seu formato, e e por
isso que este modulo existe -- para que ninguem tenha de digitar de novo
o que a PubMed ja escreveu.

  .ris   / .txt   RIS: Scopus, Web of Science, Embase, EBSCO, Zotero
  .nbib  / .txt   MEDLINE: e o formato "Send to > Citation manager" da PubMed
  .bib            BibTeX: Zotero, Mendeley, Google Academico
  .csv            planilha: Scopus, Web of Science, e a exportacao do Rayyan

O caso do Rayyan tem tratamento proprio. A exportacao dele guarda as
decisoes da equipe dentro da coluna de notas, num formato so dele:

    RAYYAN-INCLUSION: {"Ana"=>"Included","Marcos"=>"Excluded"}

Ler isso e o que permite trazer uma revisao ja comecada sem perder o
trabalho de triagem que ja foi feito -- que e a unica coisa que
realmente prende alguem a uma ferramenta.

Nada aqui inventa campo. O que o arquivo nao trouxer fica vazio: um
resumo que nao veio e um resumo para buscar, nao um resumo para supor.
"""
from __future__ import annotations

import csv
import io
import json
import re
from typing import Any, Iterable

from .util import clean_text, norm_doi, to_int

FORMATOS = ("ris", "nbib", "bibtex", "csv")

# ----------------------------------------------------------------------
# RIS
# ----------------------------------------------------------------------
# Uma etiqueta por linha, `XX  - valor`, e o registro fecha em `ER`. As
# bases divergem no nome do campo (o periodico e JO na Scopus, T2 na
# Web of Science, JF em outras), entao cada campo aceita varias etiquetas
# -- a primeira que vier com valor ganha.
RIS_CAMPOS: dict[str, tuple[str, ...]] = {
    "title": ("TI", "T1"),
    "abstract": ("AB", "N2"),
    "journal": ("JO", "JF", "T2", "JA"),
    "year": ("PY", "Y1", "DA"),
    "volume": ("VL",),
    "issue": ("IS",),
    "doi": ("DO", "DI"),
    "issn": ("SN",),
    "language": ("LA",),
    "url": ("UR", "L1"),
    "pub_type": ("TY", "M3"),
    "pmid": ("AN", "ID", "C7"),
}
RIS_MULTIPLOS = {"authors": ("AU", "A1", "A2", "A3"), "keywords": ("KW",)}


def _linhas_de_registro(texto: str) -> Iterable[list[tuple[str, str]]]:
    """Quebra um arquivo RIS/MEDLINE em registros de (etiqueta, valor).

    Linha continuada -- a que comeca com espaco -- pertence a etiqueta
    anterior. Resumo longo vem quase sempre assim, e perder a continuacao
    corta o resumo no meio sem avisar.
    """
    registro: list[tuple[str, str]] = []
    etiqueta = None
    for linha in texto.splitlines():
        casa = re.match(r"^([A-Z][A-Z0-9]{1,3})\s*-\s?(.*)$", linha)
        if casa:
            etiqueta, valor = casa.group(1), casa.group(2).rstrip()
            if etiqueta == "ER":
                if registro:
                    yield registro
                registro, etiqueta = [], None
                continue
            registro.append((etiqueta, valor))
        elif linha.strip() and registro:
            anterior, valor = registro[-1]
            registro[-1] = (anterior, (valor + " " + linha.strip()).strip())
    if registro:
        yield registro


def _primeiro(pares: list[tuple[str, str]], etiquetas: tuple[str, ...]) -> str | None:
    for alvo in etiquetas:
        for etiqueta, valor in pares:
            if etiqueta == alvo and valor.strip():
                return valor.strip()
    return None


def _todos(pares: list[tuple[str, str]], etiquetas: tuple[str, ...]) -> list[str]:
    return [v.strip() for e, v in pares if e in etiquetas and v.strip()]


def ler_ris(texto: str) -> list[dict[str, Any]]:
    saida = []
    for pares in _linhas_de_registro(texto):
        registro: dict[str, Any] = {}
        for campo, etiquetas in RIS_CAMPOS.items():
            registro[campo] = _primeiro(pares, etiquetas)
        for campo, etiquetas in RIS_MULTIPLOS.items():
            registro[campo] = "; ".join(_todos(pares, etiquetas)) or None
        inicio, fim = _primeiro(pares, ("SP",)), _primeiro(pares, ("EP",))
        registro["pages"] = "-".join(x for x in (inicio, fim) if x) or None
        registro["year"] = _ano(registro.get("year"))
        registro["doi"] = norm_doi(registro.get("doi"))
        if registro.get("title"):
            saida.append(registro)
    return saida


# ----------------------------------------------------------------------
# MEDLINE (.nbib) -- o formato da PubMed
# ----------------------------------------------------------------------
NBIB_CAMPOS = {
    "title": ("TI",), "abstract": ("AB",), "journal": ("JT", "TA"),
    "volume": ("VI",), "issue": ("IP",), "pages": ("PG",),
    "issn": ("IS",), "language": ("LA",), "pmid": ("PMID",),
    "year": ("DP", "DEP"), "pub_type": ("PT",),
}


def ler_nbib(texto: str) -> list[dict[str, Any]]:
    saida = []
    for pares in _linhas_de_registro(texto):
        if not any(e == "PMID" for e, _ in pares):
            continue
        registro: dict[str, Any] = {}
        for campo, etiquetas in NBIB_CAMPOS.items():
            registro[campo] = _primeiro(pares, etiquetas)
        # FAU e o nome por extenso, AU e a forma abreviada da MEDLINE. Os
        # dois vem no mesmo registro; juntar os dois duplicaria cada autor
        # ("Vilarino, Guilherme Torres; Vilarino GT").
        registro["authors"] = "; ".join(
            _todos(pares, ("FAU",)) or _todos(pares, ("AU",)))[:4000] or None
        registro["keywords"] = "; ".join(_todos(pares, ("MH", "OT"))) or None
        # o DOI vem escondido: `LID - 10.1016/x [doi]` ou `AID - 10.1016/x [doi]`
        registro["doi"] = None
        for etiqueta, valor in pares:
            if etiqueta in ("LID", "AID") and "[doi]" in valor:
                registro["doi"] = norm_doi(valor.split("[doi]")[0])
                break
        registro["year"] = _ano(registro.get("year"))
        # `IS - 1439-3964 (Electronic)`: o qualificador nao faz parte do ISSN
        registro["issn"] = re.sub(r"\s*\(.*\)\s*$", "", registro["issn"] or "") or None
        if registro.get("pmid"):
            registro["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{registro['pmid']}/"
        if registro.get("title"):
            saida.append(registro)
    return saida


# ----------------------------------------------------------------------
# BibTeX
# ----------------------------------------------------------------------
BIBTEX_CAMPOS = {
    "title": ("title",), "abstract": ("abstract",),
    "journal": ("journal", "journaltitle", "booktitle"),
    "year": ("year", "date"), "volume": ("volume",), "issue": ("number", "issue"),
    "pages": ("pages",), "doi": ("doi",), "issn": ("issn",),
    "language": ("language", "langid"), "url": ("url", "howpublished"),
    "keywords": ("keywords",), "pmid": ("pmid",),
}


def _desmarcar(valor: str) -> str:
    """Tira as chaves de agrupamento e os comandos mais comuns do LaTeX."""
    valor = re.sub(r"\\[a-zA-Z]+\{([^{}]*)\}", r"\1", valor)
    valor = valor.replace("{", "").replace("}", "").replace("\\&", "&")
    return re.sub(r"\s+", " ", valor).strip()


def ler_bibtex(texto: str) -> list[dict[str, Any]]:
    saida = []
    for bruto in re.finditer(r"@(\w+)\s*\{(.*?)\n\}", texto, re.S):
        corpo = bruto.group(2)
        campos: dict[str, str] = {}
        for casa in re.finditer(
                r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|[^,\n]+)", corpo):
            campos[casa.group(1).lower()] = _desmarcar(casa.group(2).strip().strip('",'))
        registro: dict[str, Any] = {}
        for campo, nomes in BIBTEX_CAMPOS.items():
            registro[campo] = next((campos[n] for n in nomes if campos.get(n)), None)
        autores = campos.get("author") or ""
        registro["authors"] = "; ".join(
            p.strip() for p in re.split(r"\s+and\s+", autores) if p.strip()) or None
        registro["year"] = _ano(registro.get("year"))
        registro["doi"] = norm_doi(registro.get("doi"))
        registro["pub_type"] = bruto.group(1).lower()
        if registro.get("title"):
            saida.append(registro)
    return saida


# ----------------------------------------------------------------------
# CSV -- Scopus, Web of Science e a exportacao do Rayyan
# ----------------------------------------------------------------------
CSV_ALIASES: dict[str, tuple[str, ...]] = {
    "title": ("title", "document title", "titulo", "ti"),
    "abstract": ("abstract", "resumo", "ab"),
    "authors": ("authors", "author full names", "author", "autores", "au", "af"),
    "journal": ("source title", "journal", "publication name", "periodico", "so", "j9"),
    "year": ("year", "publication year", "ano", "py"),
    "volume": ("volume", "vl"),
    "issue": ("issue", "is"),
    "pages": ("page start", "pages", "bp"),
    "doi": ("doi", "di"),
    "pmid": ("pubmed id", "pmid", "pm"),
    "issn": ("issn", "sn"),
    "language": ("language of original document", "language", "idioma", "la"),
    "keywords": ("author keywords", "keywords", "de", "palavras_chave"),
    "url": ("link", "url", "doi link"),
    "pub_type": ("document type", "publication type", "dt"),
    "notes": ("notes", "note", "observacoes"),
    "publisher": ("publisher",),
}


def _chave(nome: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", str(nome or "").strip().lower()).strip()


def ler_csv(texto: str) -> list[dict[str, Any]]:
    if texto.startswith("\ufeff"):
        texto = texto[1:]
    amostra = texto[:8192]
    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=",;\t")
        separador = dialeto.delimiter
    except csv.Error:
        separador = ";" if amostra.count(";") > amostra.count(",") else ","
    leitor = csv.DictReader(io.StringIO(texto), delimiter=separador)
    mapa: dict[str, str] = {}
    for cabecalho in leitor.fieldnames or []:
        chave = _chave(cabecalho)
        for campo, nomes in CSV_ALIASES.items():
            if chave in nomes and campo not in mapa.values():
                mapa[cabecalho] = campo
                break
    saida = []
    for linha in leitor:
        registro: dict[str, Any] = {campo: clean_text(linha.get(cabecalho))
                                    for cabecalho, campo in mapa.items()}
        registro["year"] = _ano(registro.get("year"))
        # O Rayyan nao tem coluna de DOI: ele poe o doi.org na coluna de
        # link. `norm_doi` devolve None para link que nao seja DOI, entao
        # tentar aqui nao estraga o CSV da Scopus, cujo link e outro.
        registro["doi"] = norm_doi(registro.get("doi")) or norm_doi(registro.get("url"))
        registro["rayyan"] = _decisoes_do_rayyan(registro.get("notes"))
        if registro.get("title"):
            saida.append(registro)
    return saida


RAYYAN_INCLUSAO = {"included": "incluir", "excluded": "excluir", "maybe": "talvez"}


def _decisoes_do_rayyan(notas: str | None) -> dict[str, Any] | None:
    """As decisoes que o Rayyan esconde na coluna de notas.

    O formato e o dele: `RAYYAN-INCLUSION: {"Ana"=>"Included"}` -- Ruby,
    nao JSON. Trocar `=>` por `:` faz virar JSON valido; quando nem isso
    resolve, cada par e lido no grito, porque perder a triagem ja feita
    seria o unico motivo de peso para nao largar a ferramenta.
    """
    if not notas or "RAYYAN-" not in notas:
        return None
    achado: dict[str, Any] = {}
    casa = re.search(r"RAYYAN-INCLUSION:\s*(\{.*?\})", notas, re.S)
    if casa:
        cru = casa.group(1)
        pessoas: dict[str, str] = {}
        try:
            pessoas = json.loads(cru.replace("=>", ":"))
        except (ValueError, TypeError):
            for quem, valor in re.findall(r'"([^"]+)"\s*=>\s*"([^"]+)"', cru):
                pessoas[quem] = valor
        achado["decisoes"] = {quem: RAYYAN_INCLUSAO.get(str(valor).strip().lower())
                              for quem, valor in pessoas.items()
                              if RAYYAN_INCLUSAO.get(str(valor).strip().lower())}
    etiquetas = re.search(r"RAYYAN-LABELS:\s*([^|]+)", notas)
    if etiquetas:
        achado["etiquetas"] = [x.strip() for x in etiquetas.group(1).split(",") if x.strip()]
    motivos = re.search(r"RAYYAN-EXCLUSION-REASONS:\s*([^|]+)", notas)
    if motivos:
        achado["motivos"] = [x.strip() for x in motivos.group(1).split(",") if x.strip()]
    return achado or None


# ----------------------------------------------------------------------
# Porta de entrada
# ----------------------------------------------------------------------
def formato_de(nome: str, texto: str) -> str:
    """Descobre o formato pelo nome do arquivo e, se preciso, pelo conteudo.

    A extensao mente com frequencia: a PubMed entrega MEDLINE em `.txt`, e
    ha quem salve RIS com `.txt` tambem. O conteudo nao mente.
    """
    sufixo = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
    if sufixo == "bib":
        return "bibtex"
    if sufixo == "nbib":
        return "nbib"
    if sufixo == "csv":
        return "csv"
    if sufixo == "ris":
        return "ris"
    cabeca = texto[:4000]
    if re.search(r"^PMID\s*-\s*\d+", cabeca, re.M):
        return "nbib"
    if re.search(r"^TY\s+-\s+", cabeca, re.M):
        return "ris"
    if re.search(r"^@\w+\s*\{", cabeca, re.M):
        return "bibtex"
    return "csv"


LEITORES = {"ris": ler_ris, "nbib": ler_nbib, "bibtex": ler_bibtex, "csv": ler_csv}


def ler(texto: str, nome: str = "", formato: str | None = None) -> list[dict[str, Any]]:
    """Le um arquivo de referencias em qualquer um dos formatos aceitos."""
    escolhido = formato or formato_de(nome, texto)
    if escolhido not in LEITORES:
        raise ValueError(f"formato desconhecido: {escolhido}. Use {', '.join(FORMATOS)}")
    return LEITORES[escolhido](texto)


def _ano(valor: Any) -> int | None:
    """O ano dentro de qualquer coisa: '2024', '2024/05/12', 'Jan 2024'."""
    texto = clean_text(valor)
    if texto is None:
        return None
    casa = re.search(r"(19|20)\d{2}", texto)
    return int(casa.group()) if casa else to_int(texto)
