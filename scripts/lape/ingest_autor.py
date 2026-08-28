"""Importa a producao de um pesquisador a partir das bases publicas.

O Lattes precisa de captcha e so sai do navegador. A PubMed e o OpenAlex
entregam a mesma producao por programa -- e com o que o Lattes nao tem:
DOI conferido, resumo, afiliacao (que vira o pais no mapa) e contagem de
citacoes.

Duas cautelas governam o modulo, e as duas existem porque o erro aqui e
silencioso:

  1. **Nome nao identifica pessoa.** "Andrade A" traz milhares de artigos
     de dezenas de pessoas. Por isso a afiliacao e obrigatoria na pratica,
     e a conferencia mostra a afiliacao de cada registro antes de gravar.
  2. **Nada e gravado por cima.** O que o laboratorio digitou continua
     valendo; a base preenche lacuna, nao corrige ninguem.
"""
from __future__ import annotations

from typing import Any

from . import referencias, sources, variaveis
from .db import Database
from .util import clean_text, norm_doi, title_key


# Quem o laboratorio pediu para trazer das bases. Fica escrito aqui, e
# nao digitado a cada vez, porque a busca certa e o resultado de conferir
# quantos artigos cada forma do nome traz -- nao e coisa de improvisar na
# hora. Acrescentar alguem e uma linha.
PESQUISADORES: tuple[dict[str, Any], ...] = (
    {"nome": "Alexandro Andrade", "afiliacao": "UDESC",
     "papel": "Coordenador do LAPE"},
    {"nome": "Guilherme Torres Vilarino", "afiliacao": "UDESC",
     "papel": "Pesquisador do LAPE"},
)


def buscar(nome: str, afiliacao: str | None = None, desde: int | None = None,
           limite: int = 400) -> dict[str, Any]:
    """Procura a producao na PubMed e devolve os registros completos.

    Volta em MEDLINE e passa pelo mesmo leitor de `.nbib` que a triagem
    usa -- um formato, um leitor.
    """
    termo = sources.termo_de_autor(nome, afiliacao, desde)
    pmids = sources.pubmed_search(termo, retmax=limite)
    if not pmids:
        return {"termo": termo, "pmids": [], "registros": []}
    bruto = sources.pubmed_medline(pmids)
    registros = referencias.ler_nbib(bruto)
    for registro in registros:
        # Todos os paises do registro, nao so o do primeiro autor: e a
        # colaboracao internacional que o mapa da producao mostra.
        registro["paises"] = variaveis.paises_da_afiliacao(
            registro.get("afiliacoes") or registro.get("affiliation"))
        registro["pais"] = registro["paises"][0] if registro["paises"] else None
    return {"termo": termo, "pmids": pmids, "registros": registros}


def resumir(achado: dict[str, Any]) -> dict[str, Any]:
    """O que a busca traria, em numeros -- para conferir antes de gravar."""
    registros = achado["registros"]
    anos = sorted(r["year"] for r in registros if r.get("year"))
    por_ano: dict[int, int] = {}
    for ano in anos:
        por_ano[ano] = por_ano.get(ano, 0) + 1
    revistas: dict[str, int] = {}
    for r in registros:
        chave = clean_text(r.get("journal")) or "sem revista"
        revistas[chave] = revistas.get(chave, 0) + 1
    paises: dict[str, int] = {}
    for r in registros:
        for pais in r.get("paises") or ([r["pais"]] if r.get("pais") else []):
            paises[pais] = paises.get(pais, 0) + 1
    return {
        "termo": achado["termo"],
        "encontrados": len(registros),
        "com_doi": sum(1 for r in registros if r.get("doi")),
        "com_resumo": sum(1 for r in registros if r.get("abstract")),
        "primeiro_ano": anos[0] if anos else None,
        "ultimo_ano": anos[-1] if anos else None,
        "anos_com_producao": len(por_ano),
        "por_ano": dict(sorted(por_ano.items())),
        "revistas": sorted(revistas.items(), key=lambda x: -x[1])[:8],
        "paises": sorted(paises.items(), key=lambda x: -x[1]),
    }


def importar(db: Database, achado: dict[str, Any], quem: str | None = None,
             fonte: str = "pubmed") -> dict[str, int]:
    """Grava o que a busca trouxe, sem passar por cima do que ja existe."""
    member_id = db.member_id(quem) if quem else None
    novos, ja_havia = 0, 0
    for registro in achado["registros"]:
        titulo = clean_text(registro.get("title"))
        chave = title_key(titulo)
        if not chave:
            continue
        existia = db.scalar("SELECT id FROM articles WHERE title_key = ?", (chave,))
        article_id = db.upsert("articles", {
            "title": titulo,
            "title_key": chave,
            "status": "publicado",
            "year_published": registro.get("year"),
            "published_on": f"{registro['year']}-01-01" if registro.get("year") else None,
            "journal": clean_text(registro.get("journal")),
            "issn": clean_text(registro.get("issn")),
            "doi": norm_doi(registro.get("doi")),
            "url": clean_text(registro.get("url")),
            "language": clean_text(registro.get("language")),
            "notes": clean_text(registro.get("abstract")),
            "pmid": clean_text(registro.get("pmid")),
            "pmc": clean_text(registro.get("pmc")),
            "oa_url": clean_text(registro.get("oa_url")),
            # PMC e texto completo livre. Nao e a definicao inteira de
            # acesso aberto, mas e a parte que se pode afirmar daqui.
            "open_access": 1 if registro.get("pmc") else None,
            "source": fonte,
        }, conflict=("title_key",), fill_only=True)
        for pais in registro.get("paises") or []:
            db.execute("INSERT OR IGNORE INTO article_countries (article_id, country)"
                       " VALUES (?, ?)", (article_id, pais))
        if existia:
            ja_havia += 1
        else:
            novos += 1
        for ordem, autor in enumerate(
                [a.strip() for a in str(registro.get("authors") or "").split(";") if a.strip()],
                start=1):
            autor_id = db.member_id(autor, create=False)
            db.execute(
                "INSERT OR IGNORE INTO article_authors"
                " (article_id, member_id, author_name, author_order, is_external)"
                " VALUES (?, ?, ?, ?, ?)",
                (article_id, autor_id, autor, ordem, 0 if autor_id else 1))
        if member_id and quem:
            db.execute(
                "UPDATE article_authors SET member_id = ? WHERE article_id = ?"
                "   AND member_id IS NULL AND lower(author_name) LIKE ?",
                (member_id, article_id, f"%{clean_text(quem).split()[-1].lower()}%"))
    db.conn.commit()
    return {"novos": novos, "ja_havia": ja_havia,
            "total": len(achado["registros"])}


def trazer(db: Database, nome: str, afiliacao: str | None = None,
           desde: int | None = None) -> dict[str, Any]:
    """Busca e grava de uma vez -- o que o botao da tela chama."""
    achado = buscar(nome, afiliacao, desde)
    resumo_ = resumir(achado)
    gravado = importar(db, achado, quem=nome)
    return {"quem": nome, "resumo": resumo_, "gravado": gravado}


def trazer_todos(db: Database, desde: int | None = None) -> dict[str, Any]:
    """A producao de todo mundo da lista.

    Uma pessoa falhar nao pode derrubar as outras: a rede cai no meio, e
    quem ja entrou fica. O erro vira texto ao lado do nome, nao um 500.
    """
    from . import variaveis

    saida = []
    for pessoa in PESQUISADORES:
        try:
            saida.append(trazer(db, pessoa["nome"], pessoa.get("afiliacao"), desde))
        except Exception as erro:  # noqa: BLE001 -- vira recado, nao rastreio
            saida.append({"quem": pessoa["nome"], "erro": str(erro)})
    variaveis.instalar(db)
    marcadas = variaveis.marcar_artigos(db)
    return {"pessoas": saida, "variaveis": marcadas}
