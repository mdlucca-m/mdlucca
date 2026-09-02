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
# O ID Lattes vai junto quando se sabe: e o unico identificador que nao
# se repete e nao depende de como a pessoa assina. Serve para achar o
# curriculo certo entre os arquivos de data/raw/ e para montar o link do
# CV na tela. Nao substitui a busca da PubMed -- o Lattes exige captcha e
# so sai do navegador.
# `grafias` sao as assinaturas com que a pessoa aparece nos artigos, e a
# lista saiu de uma auditoria dos registros da PubMed, nao de palpite. Elas
# existem porque a chave canonica de autor le "Torres Vilarino" como nome
# proprio + sobrenome, e nao como sobrenome composto:
#
#   "Vilarino, Guilherme Torres"  -> vilarino_gt   (17 registros)
#   "Vilarino, Guilherme T"       -> vilarino_gt   (1)
#   "Torres Vilarino, Guilherme"  -> torres_g      (1)   <- outra pessoa, para o programa
#   "Torres Vilarino, G"          -> torres_g      (1)   <-
#
# Sem declarar isso, a importacao criava um integrante fantasma e repartia
# a producao de uma pessoa entre dois nomes no painel.
#
# `vinculo` e o que faz os dois aparecerem na lista de orientadores da ficha
# de cadastro -- a lista sai de quem tem vinculo de coordenacao, professor
# ou pos-doutorado (mapping.ORIENTAM). Sem isso, quem se cadastra encontra
# um campo "Orientador" sem uma unica opcao, e nao ha o que escolher.
PESQUISADORES: tuple[dict[str, Any], ...] = (
    {"nome": "Alexandro Andrade", "afiliacao": "UDESC",
     "papel": "Coordenador do LAPE", "lattes": "5577164706111568",
     "vinculo": "coordenacao", "orienta_por_padrao": True,
     "grafias": ("Andrade A", "Andrade, Alexandro")},
    {"nome": "Guilherme Torres Vilarino", "afiliacao": "UDESC",
     "papel": "Pesquisador do LAPE", "lattes": None,
     "vinculo": "professor",
     "grafias": ("Torres Vilarino G", "Torres Vilarino, G",
                 "Torres Vilarino, Guilherme", "Vilarino GT",
                 "Vilarino, Guilherme T")},
)


def orientador_padrao() -> str | None:
    """Quem vem preenchido na ficha de quem se cadastra.

    No LAPE, a orientacao e de uma pessoa so, e obrigar cada integrante a
    escolher o mesmo nome numa lista de dois e trabalho sem informacao. O
    campo continua sendo um select: quem tiver outro orientador troca.
    """
    for pessoa in PESQUISADORES:
        if pessoa.get("orienta_por_padrao"):
            return pessoa["nome"]
    return None


def link_do_lattes(lattes_id: Any) -> str | None:
    """O endereco publico do curriculo, para quem quiser abrir e conferir."""
    from .ingest_lattes import e_id_lattes

    return f"http://lattes.cnpq.br/{lattes_id}" if e_id_lattes(lattes_id) else None


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


def garantir_professores(db: Database, criar: bool = True) -> dict[str, Any]:
    """Poe os dois professores no banco, com vinculo, nome inteiro e grafias.

    Existe para uma coisa concreta: a ficha de cadastro tem um campo
    "Orientador" que so lista quem tem vinculo de coordenacao, professor ou
    pos-doutorado. Numa instalacao nova ninguem tem vinculo, entao o campo
    abre sem uma opcao -- e quem chega pelo link de convite nao tem como
    dizer quem o orienta.

    Nao passa por cima do que houver: se a coordenacao ja marcou outro
    vinculo para alguem, o dela fica.
    """
    saida = []
    for pessoa in PESQUISADORES:
        # `criar=False` na subida do servico: ajustar quem ja esta cadastrado
        # e conserto; INVENTAR duas pessoas num banco recem-instalado seria
        # outra coisa -- um laboratorio vazio ganharia dois integrantes que
        # ninguem cadastrou. Pelo botao, criar e o que se quer.
        membro = db.member_id(pessoa["nome"], create=criar)
        if not membro:
            continue
        atual = db.dicts("SELECT full_name, role FROM members WHERE id = ?", (membro,))[0]
        mudou = []
        # O nome inteiro: quem veio da planilha entrou como "Andrade", e um
        # orientador chamado "Andrade" numa lista nao diz de quem se trata.
        if (atual["full_name"] or "").strip() != pessoa["nome"]:
            db.execute("UPDATE members SET full_name = ? WHERE id = ?",
                       (pessoa["nome"], membro))
            mudou.append("nome")
        if not (atual["role"] or "").strip():
            db.execute("UPDATE members SET role = ? WHERE id = ?",
                       (pessoa["vinculo"], membro))
            mudou.append("vínculo")
        grafias = declarar_grafias(db, pessoa)
        saida.append({"quem": pessoa["nome"], "id": membro,
                      "vinculo": atual["role"] or pessoa["vinculo"],
                      "ajustes": mudou, "grafias": len(grafias)})
    db.conn.commit()
    return {"professores": saida, "orientador_padrao": orientador_padrao()}


def declarar_grafias(db: Database, pessoa: dict[str, Any]) -> list[str]:
    """Garante o cadastro da pessoa e prega nele as grafias conhecidas.

    Nao apaga o que ja existir: a coordenacao pode ter acrescentado outras
    grafias pela tela, e uma importacao nao tem por que desfazer isso.
    """
    grafias = tuple(pessoa.get("grafias") or ())
    if not grafias:
        return []
    membro = db.member_id(pessoa["nome"])
    if not membro:
        return []
    postas = []
    for grafia in grafias:
        try:
            db.register_alias(grafia, membro)
        except ValueError:
            # a grafia ja e o nome de outra pessoa: juntar cadastros e
            # destrutivo e nao se faz sozinho, no meio de uma importacao
            continue
        postas.append(grafia)
    db.conn.commit()
    return postas


def trazer_todos(db: Database, desde: int | None = None) -> dict[str, Any]:
    """A producao de todo mundo da lista.

    Uma pessoa falhar nao pode derrubar as outras: a rede cai no meio, e
    quem ja entrou fica. O erro vira texto ao lado do nome, nao um 500.
    """
    from . import variaveis

    saida = []
    for pessoa in PESQUISADORES:
        try:
            # As grafias entram ANTES da busca: se entrassem depois, os
            # registros indexados pela forma composta ja teriam criado o
            # integrante fantasma que elas existem para evitar.
            garantir_professores(db)
            saida.append(trazer(db, pessoa["nome"], pessoa.get("afiliacao"), desde))
        except Exception as erro:  # noqa: BLE001 -- vira recado, nao rastreio
            saida.append({"quem": pessoa["nome"], "erro": str(erro)})
    variaveis.instalar(db)
    marcadas = variaveis.marcar_artigos(db)
    return {"pessoas": saida, "variaveis": marcadas}
