"""Ingestao do Curriculo Lattes (XML oficial do CNPq).

Como obter o arquivo:
  1. Acesse o curriculo em lattes.cnpq.br e clique no icone XML
     ("Exportar / Curriculo em XML") -- baixa um .zip com curriculo.xml.
  2. Salve o .zip (ou o .xml) em data/raw/ com um nome que contenha
     'lattes', por exemplo data/raw/lattes_alexandro_andrade.zip.

O parser aceita .zip e .xml, nas codificacoes ISO-8859-1 e UTF-8, e le:
  - ARTIGOS-PUBLICADOS         -> artigos com status 'publicado'
  - ARTIGOS-ACEITOS-...        -> artigos com status 'aceito'
  - TRABALHOS-EM-EVENTOS       -> eventos do tipo 'congresso' (opcional)

Os dados do Lattes sao complementares: eles preenchem lacunas dos
registros vindos das planilhas, mas nunca sobrescrevem o que o
laboratorio digitou.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any, Iterable, Iterator
from xml.etree import ElementTree as ET

from . import config
from .db import Database
from .util import clean_text, display_name, norm_doi, title_key, to_int


def _dobra(texto: Any) -> str:
    """Sem acento e em minuscula, para comparar nome com nome de arquivo."""
    import unicodedata

    limpo = str(texto or "")
    sem = "".join(c for c in unicodedata.normalize("NFKD", limpo)
                  if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sem.lower()).strip()


def confere(path: Path, with_conferences: bool = True) -> dict[str, Any]:
    """Le o curriculo e diz o que ele TRARIA -- sem gravar nada.

    Um Lattes de professor titular traz decadas de producao, e boa parte
    dela nao e do laboratorio. Deixar isso entrar sem olhar antes e o tipo
    de coisa que so se descobre depois, quando o painel ja esta com o
    dobro de artigos e ninguem sabe de onde vieram.
    """
    root = load_xml(path)
    info = researcher_info(root)
    artigos = list(iter_articles(root))
    anos = sorted(a["year"] for a in artigos if a["year"])
    por_ano: dict[int, int] = {}
    for ano in anos:
        por_ano[ano] = por_ano.get(ano, 0) + 1
    eventos = list(iter_conference_papers(root)) if with_conferences else []
    return {
        "arquivo": path.name,
        "de_quem": info["full_name"] or "(sem nome no currículo)",
        "lattes_id": info["lattes_id"],
        "nomes_de_citacao": info["citation_names"],
        "artigos": len(artigos),
        "publicados": sum(1 for a in artigos if a["status"] == "publicado"),
        "com_doi": sum(1 for a in artigos if a["doi"]),
        "eventos": len(eventos),
        "primeiro_ano": anos[0] if anos else None,
        "ultimo_ano": anos[-1] if anos else None,
        "anos_com_producao": len(por_ano),
        "por_ano": dict(sorted(por_ano.items())),
    }


def de_quem(path: Path) -> str:
    """O nome de quem e o curriculo, sem carregar o resto."""
    try:
        return researcher_info(load_xml(path))["full_name"] or ""
    except Exception:
        return ""


def identificador(path: Path) -> str:
    """O ID Lattes gravado dentro do curriculo.

    E o unico jeito de ter certeza de quem e o arquivo: nome de arquivo
    se renomeia, nome de pessoa se repete, ID nao.
    """
    try:
        return researcher_info(load_xml(path))["lattes_id"] or ""
    except Exception:
        return ""


def e_id_lattes(texto: Any) -> bool:
    """Um ID Lattes sao 16 digitos -- nunca um nome."""
    return bool(re.fullmatch(r"\d{16}", str(texto or "").strip()))


def filtrar(arquivos: list[Path], somente: Iterable[str]) -> list[Path]:
    """Fica so com os curriculos das pessoas pedidas.

    Aceita ID Lattes ou nome. O ID vale mais: casa com o
    NUMERO-IDENTIFICADOR gravado dentro do proprio curriculo, entao nao
    depende de como o arquivo foi salvo nem de como a pessoa assina.

    Sem ID, casa pelo nome do arquivo E pelo nome de dentro do curriculo:
    quem exporta do Lattes recebe um `curriculo.xml` sem nome nenhum, e
    quem renomeia o arquivo raramente escreve o nome completo. Bastar um
    dos dois evita a importacao silenciosa de quem nao foi pedido -- que
    e o erro caro aqui, porque desfazer significa apagar artigo do banco.
    """
    pedidos = [str(x).strip() for x in somente if str(x).strip()]
    if not pedidos:
        return list(arquivos)
    # ID Lattes tem preferencia sobre nome: e o unico identificador que
    # nao se repete e nao depende de como a pessoa assina.
    ids = {x for x in pedidos if e_id_lattes(x)}
    alvos = [_dobra(x) for x in pedidos if not e_id_lattes(x)]
    escolhidos = []
    for caminho in arquivos:
        if ids and identificador(caminho) in ids:
            escolhidos.append(caminho)
            continue
        nome_arquivo = _dobra(caminho.stem)
        dono = _dobra(de_quem(caminho))
        for alvo in alvos:
            partes = [p for p in alvo.split() if len(p) > 2]
            if not partes:
                continue
            if (all(p in nome_arquivo for p in partes)
                    or all(p in dono for p in partes)):
                escolhidos.append(caminho)
                break
    return escolhidos


def discover_lattes_files(raw_dir: Path = config.RAW_DIR) -> list[Path]:
    if not raw_dir.exists():
        return []
    found = [
        p for p in sorted(raw_dir.rglob("*"))
        if p.suffix.lower() in {".zip", ".xml"} and not p.name.startswith("~$")
    ]
    named = [p for p in found if "lattes" in p.name.lower() or "curriculo" in p.name.lower()]
    return named or [p for p in found if p.suffix.lower() == ".xml"]


def load_xml(path: Path) -> ET.Element:
    """Le o XML do Lattes de um .xml ou de dentro de um .zip."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith(".xml")]
            if not names:
                raise ValueError(f"{path.name} nao contem XML")
            payload = archive.read(names[0])
    else:
        payload = path.read_bytes()
    return _parse_bytes(payload)


def _parse_bytes(payload: bytes) -> ET.Element:
    for encoding in ("iso-8859-1", "utf-8", "cp1252"):
        try:
            text = payload.decode(encoding)
        except UnicodeDecodeError:
            continue
        text = re.sub(r'^<\?xml[^>]*\?>', '', text, count=1).lstrip("﻿ \n\r\t")
        try:
            return ET.fromstring(text)
        except ET.ParseError:
            continue
    raise ValueError("nao foi possivel decodificar/parsear o XML do Lattes")


def _attr(node: ET.Element | None, name: str) -> str | None:
    if node is None:
        return None
    return clean_text(node.get(name))


def researcher_info(root: ET.Element) -> dict[str, Any]:
    general = root.find("DADOS-GERAIS")
    citations = _attr(general, "NOME-EM-CITACOES-BIBLIOGRAFICAS") or ""
    return {
        "lattes_id": clean_text(root.get("NUMERO-IDENTIFICADOR")),
        "full_name": display_name(_attr(general, "NOME-COMPLETO")),
        "raw_name": _attr(general, "NOME-COMPLETO"),
        "citation_names": [c.strip() for c in citations.split(";") if c.strip()],
        "updated_at": clean_text(root.get("DATA-ATUALIZACAO")),
    }


def iter_articles(root: ET.Element) -> Iterator[dict[str, Any]]:
    """Percorre artigos publicados e aceitos."""
    sections = (
        ("PRODUCAO-BIBLIOGRAFICA/ARTIGOS-PUBLICADOS/ARTIGO-PUBLICADO", "publicado"),
        ("PRODUCAO-BIBLIOGRAFICA/ARTIGOS-ACEITOS-PARA-PUBLICACAO/ARTIGO-ACEITO-PARA-PUBLICACAO", "aceito"),
    )
    for xpath, status in sections:
        for node in root.findall(xpath):
            basics = node.find("DADOS-BASICOS-DO-ARTIGO")
            detail = node.find("DETALHAMENTO-DO-ARTIGO")
            title = _attr(basics, "TITULO-DO-ARTIGO")
            if not title:
                continue
            authors = []
            for author in node.findall("AUTORES"):
                name = _attr(author, "NOME-COMPLETO-DO-AUTOR") or _attr(author, "NOME-PARA-CITACAO")
                if name:
                    order = to_int(_attr(author, "ORDEM-DE-AUTORIA")) or len(authors) + 1
                    authors.append((order, name.split(";")[0].strip()))
            authors.sort(key=lambda pair: pair[0])
            yield {
                "title": title,
                "status": status,
                "year": to_int(_attr(basics, "ANO-DO-ARTIGO")),
                "doi": norm_doi(_attr(basics, "DOI")),
                "language": _attr(basics, "IDIOMA"),
                "url": _attr(basics, "HOME-PAGE-DO-TRABALHO"),
                "nature": _attr(basics, "NATUREZA"),
                "journal": _attr(detail, "TITULO-DO-PERIODICO-OU-REVISTA"),
                "issn": _attr(detail, "ISSN"),
                "authors": [name for _, name in authors],
            }


def iter_conference_papers(root: ET.Element) -> Iterator[dict[str, Any]]:
    xpath = "PRODUCAO-BIBLIOGRAFICA/TRABALHOS-EM-EVENTOS/TRABALHO-EM-EVENTOS"
    for node in root.findall(xpath):
        basics = node.find("DADOS-BASICOS-DO-TRABALHO")
        detail = node.find("DETALHAMENTO-DO-TRABALHO")
        title = _attr(basics, "TITULO-DO-TRABALHO")
        year = to_int(_attr(basics, "ANO-DO-TRABALHO"))
        if not title or not year:
            continue
        yield {
            "title": title,
            "year": year,
            "event": _attr(detail, "NOME-DO-EVENTO") or "Evento cientifico",
            "city": _attr(detail, "CIDADE-DO-EVENTO"),
            "country": _attr(basics, "PAIS-DO-EVENTO"),
        }


def ingest_file(db: Database, path: Path, with_conferences: bool = True,
                verbose: bool = True) -> dict[str, int]:
    root = load_xml(path)
    info = researcher_info(root)
    owner_id = None
    dono = info["full_name"] or ""
    if info["full_name"]:
        owner_id = db.member_id(
            info["raw_name"],
            lattes_id=info["lattes_id"],
            role="Pesquisador (Lattes)",
        )
        if owner_id:
            db.execute("UPDATE members SET full_name = ? WHERE id = ?", (info["full_name"], owner_id))
            for alias in info["citation_names"]:
                db.register_alias(alias, owner_id)

    written = 0
    for article in iter_articles(root):
        key = title_key(article["title"])
        if not key:
            continue
        published_on = f"{article['year']}-01-01" if article["year"] else None
        article_id = db.upsert(
            "articles",
            {
                "title": article["title"],
                "title_key": key,
                "status": article["status"],
                "year_published": article["year"] if article["status"] == "publicado" else None,
                "published_on": published_on if article["status"] == "publicado" else None,
                "journal": article["journal"],
                "issn": article["issn"],
                "doi": article["doi"],
                "url": article["url"],
                "language": article["language"],
                "study_type": article["nature"],
                "source": "lattes",
            },
            conflict=("title_key",),
            fill_only=True,
        )
        existing_authors = db.scalar(
            "SELECT COUNT(*) FROM article_authors WHERE article_id = ?", (article_id,)
        )
        if not existing_authors and article["authors"]:
            for order, name in enumerate(article["authors"], start=1):
                member_id = db.member_id(name, create=True)
                db.execute(
                    "INSERT OR REPLACE INTO article_authors"
                    " (article_id, member_id, author_name, author_order, is_corresponding, is_external)"
                    " VALUES (?, ?, ?, ?, 0, 0)",
                    (article_id, member_id, display_name(name) or name, order),
                )
        written += 1

    events_written = 0
    if with_conferences:
        for paper in iter_conference_papers(root):
            key = f"lattes_evt_{title_key(paper['title'])[:60]}"
            db.upsert(
                "events",
                {
                    "external_key": key,
                    "kind": "congresso",
                    "title": paper["event"],
                    "description": f"Trabalho apresentado: {paper['title']}",
                    "start_at": f"{paper['year']}-01-01 00:00",
                    "all_day": 1,
                    "city": paper["city"],
                    "country": paper["country"] or "Brasil",
                },
                conflict=("external_key",),
                fill_only=True,
            )
            events_written += 1

    db.conn.commit()
    db.log_ingest("lattes", target="articles", file=path.name,
                  rows_read=written + events_written, rows_written=written)
    if verbose:
        print(f"  lattes {path.name}: {written} artigos, {events_written} trabalhos em evento"
              f" (curriculo: {info['full_name'] or '?'} / ID {info['lattes_id'] or '?'})")
    return {"articles": written, "events": events_written, "de_quem": dono}


def ingest_all(db: Database, raw_dir: Path = config.RAW_DIR, verbose: bool = True,
               somente: Iterable[str] | None = None,
               arquivos: Iterable[Path] | None = None) -> dict[str, int]:
    """Importa os curriculos encontrados -- ou so os de quem foi pedido."""
    totals: dict[str, Any] = {"articles": 0, "events": 0, "de_quem": []}
    files = [Path(a) for a in arquivos] if arquivos else discover_lattes_files(raw_dir)
    if somente:
        pedidos = list(somente)
        files = filtrar(files, pedidos)
        if not files and verbose:
            print(f"  ! nenhum currículo encontrado para: {', '.join(pedidos)}")
    if not files:
        if verbose:
            print("  ! nenhum XML/ZIP do Lattes encontrado em data/raw/"
                  " (exporte o curriculo em XML no lattes.cnpq.br)")
        return totals
    for path in files:
        try:
            result = ingest_file(db, path, verbose=verbose)
        except Exception as exc:
            db.log_ingest("lattes", file=path.name, status="erro", message=str(exc))
            if verbose:
                print(f"  ! erro lendo {path.name}: {exc}")
            continue
        totals["articles"] += result["articles"]
        totals["events"] += result["events"]
        dono = result.get("de_quem")
        if dono:
            totals["de_quem"].append(dono)
    return totals
