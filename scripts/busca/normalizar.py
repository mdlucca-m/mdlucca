"""Normalização dos registros brutos das três APIs para o esquema `artigo`,
e deduplicação na ordem de confiabilidade declarada no protocolo (§3.11):
DOI → PMID → título normalizado.

Preenche apenas os campos bibliográficos. Os campos de curadoria (variaveis,
subvariaveis, instrumentos, sintese) ficam a cargo das rotinas de
enriquecimento, que rodam depois.
"""
from __future__ import annotations

import re
import unicodedata
from xml.etree import ElementTree as ET

# País a partir da afiliação: casa o nome no fim do endereço, que é onde
# PubMed e Scopus o colocam.
PAISES = {
    "germany": "Alemanha", "spain": "Espanha", "norway": "Noruega",
    "brazil": "Brasil", "brasil": "Brasil", "tunisia": "Tunísia",
    "denmark": "Dinamarca", "poland": "Polônia", "france": "França",
    "portugal": "Portugal", "japan": "Japão", "turkey": "Turquia",
    "türkiye": "Turquia", "sweden": "Suécia", "hungary": "Hungria",
    "italy": "Itália", "croatia": "Croácia", "serbia": "Sérvia",
    "slovenia": "Eslovênia", "greece": "Grécia", "czech": "Tchéquia",
    "slovakia": "Eslováquia", "romania": "Romênia", "netherlands": "Países Baixos",
    "belgium": "Bélgica", "austria": "Áustria", "switzerland": "Suíça",
    "iceland": "Islândia", "finland": "Finlândia", "russia": "Rússia",
    "ukraine": "Ucrânia", "china": "China", "korea": "Coreia do Sul",
    "qatar": "Catar", "egypt": "Egito", "algeria": "Argélia",
    "morocco": "Marrocos", "saudi arabia": "Arábia Saudita", "iran": "Irã",
    "israel": "Israel", "united states": "Estados Unidos", "usa": "Estados Unidos",
    "canada": "Canadá", "mexico": "México", "argentina": "Argentina",
    "chile": "Chile", "colombia": "Colômbia", "australia": "Austrália",
    "united kingdom": "Reino Unido", "england": "Reino Unido",
    "scotland": "Reino Unido", "wales": "Reino Unido", "lithuania": "Lituânia",
    "latvia": "Letônia", "estonia": "Estônia", "bulgaria": "Bulgária",
    "north macedonia": "Macedônia do Norte", "montenegro": "Montenegro",
    "bosnia": "Bósnia e Herzegovina", "india": "Índia", "nigeria": "Nigéria",
    "south africa": "África do Sul", "kuwait": "Kuwait", "oman": "Omã",
}

CAMPOS = (
    "pmid", "fonte", "titulo", "autores", "pais", "ano", "revista",
    "palavras_chave", "tipo_estudo", "resumo", "doi", "citacoes", "link",
    "volume", "numero", "paginas", "pmcid", "idioma",
)


def _txt(el) -> str:
    """Texto de um elemento XML incluindo filhos (títulos trazem <i>, <sup>)."""
    return "".join(el.itertext()).strip() if el is not None else ""


def pais_de(texto: str) -> str:
    if not texto:
        return ""
    baixo = texto.lower()
    # Preferir a ocorrência mais ao fim: é onde fica o país no endereço postal.
    achado, pos = "", -1
    for chave, nome in PAISES.items():
        i = baixo.rfind(chave)
        if i > pos:
            achado, pos = nome, i
    return achado


def normalizar_doi(doi: str | None) -> str:
    if not doi:
        return ""
    d = doi.strip().lower()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", d)
    return d.rstrip(".").strip()


def chave_titulo(titulo: str | None) -> str:
    t = unicodedata.normalize("NFKD", titulo or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", t.lower())


# ═════════════════════════════════════════════════════════════════ PubMed ═══
def de_pubmed(reg: dict) -> dict:
    art: ET.Element = reg["_xml"]
    cit = art.find("MedlineCitation")
    artigo = cit.find("Article")

    autores = []
    afiliacoes = []
    for a in artigo.findall(".//Author"):
        sob, nome = _txt(a.find("LastName")), _txt(a.find("ForeName"))
        coletivo = _txt(a.find("CollectiveName"))
        if sob:
            autores.append(f"{nome} {sob}".strip())
        elif coletivo:
            autores.append(coletivo)
        afiliacoes += [_txt(x) for x in a.findall(".//Affiliation")]

    ids = {i.get("IdType"): _txt(i) for i in art.findall(".//ArticleIdList/ArticleId")}
    revista = artigo.find("Journal")
    pubdate = revista.find(".//PubDate") if revista is not None else None
    ano = _txt(pubdate.find("Year")) if pubdate is not None else ""
    if not ano and pubdate is not None:
        m = re.search(r"(19|20)\d{2}", _txt(pubdate.find("MedlineDate")))
        ano = m.group(0) if m else ""

    resumo = " ".join(
        (f"{x.get('Label')}: " if x.get("Label") else "") + _txt(x)
        for x in artigo.findall(".//Abstract/AbstractText")
    ).strip()

    pag = artigo.find(".//Pagination/MedlinePgn")
    tipos = [_txt(t) for t in artigo.findall(".//PublicationTypeList/PublicationType")]

    return {
        "pmid": _txt(cit.find("PMID")),
        "fonte": "PubMed",
        "titulo": _txt(artigo.find("ArticleTitle")),
        "autores": ", ".join(autores),
        "pais": pais_de(" | ".join(afiliacoes)),
        "ano": ano,
        "revista": _txt(revista.find(".//Title")) if revista is not None else "",
        "palavras_chave": ", ".join(
            _txt(k) for k in cit.findall(".//KeywordList/Keyword") if _txt(k)),
        "tipo_estudo": "; ".join(t for t in tipos if t != "Journal Article") or "Artigo de periódico",
        "resumo": resumo,
        "doi": normalizar_doi(ids.get("doi")),
        "citacoes": None,
        "link": f"https://pubmed.ncbi.nlm.nih.gov/{_txt(cit.find('PMID'))}/",
        "volume": _txt(revista.find(".//Volume")) if revista is not None else "",
        "numero": _txt(revista.find(".//Issue")) if revista is not None else "",
        "paginas": _txt(pag),
        "pmcid": ids.get("pmc", ""),
        "idioma": _txt(artigo.find(".//Language")),
    }


# ═════════════════════════════════════════════════════════════════ Scopus ═══
def de_scopus(reg: dict) -> dict:
    def g(*chaves, padrao=""):
        for c in chaves:
            v = reg.get(c)
            if v:
                return v
        return padrao

    autores = ""
    if isinstance(reg.get("author"), list):
        autores = ", ".join(
            f"{a.get('given-name','')} {a.get('surname','')}".strip()
            for a in reg["author"] if a.get("surname"))
    if not autores:
        autores = g("dc:creator")

    afil = reg.get("affiliation") or []
    if isinstance(afil, dict):
        afil = [afil]
    pais = ""
    for a in afil:
        pais = PAISES.get((a.get("affiliation-country") or "").lower()) or pais
    if not pais:
        pais = pais_de(" | ".join(a.get("affilname", "") for a in afil))

    data = g("prism:coverDate")
    link = ""
    for l in reg.get("link", []) or []:
        if l.get("@ref") in ("scopus", "self"):
            link = l.get("@href", "")
            if l.get("@ref") == "scopus":
                break

    citacoes = g("citedby-count", padrao=None)
    return {
        "pmid": g("pubmed-id"),
        "fonte": "Scopus",
        "titulo": g("dc:title"),
        "autores": autores,
        "pais": pais,
        "ano": data[:4] if data else "",
        "revista": g("prism:publicationName"),
        "palavras_chave": ", ".join(
            p.strip() for p in g("authkeywords").split("|") if p.strip()),
        "tipo_estudo": g("subtypeDescription", "subtype", padrao="Artigo de periódico"),
        "resumo": g("dc:description"),
        "doi": normalizar_doi(g("prism:doi")),
        "citacoes": int(citacoes) if citacoes not in (None, "") else None,
        "link": link,
        "volume": g("prism:volume"),
        "numero": g("prism:issueIdentifier"),
        "paginas": g("prism:pageRange"),
        "pmcid": "",
        "idioma": g("language", padrao=""),
    }


# ════════════════════════════════════════════════════════ Web of Science ═══
def de_wos(reg: dict) -> dict:
    if reg.get("_api") == "starter":
        fonte = reg.get("source") or {}
        nomes = (reg.get("names") or {}).get("authors") or []
        ident = reg.get("identifiers") or {}
        paginas = fonte.get("pages") or {}
        return {
            "pmid": (ident.get("pmid") or "").replace("MEDLINE:", ""),
            "fonte": "Web of Science",
            "titulo": reg.get("title", ""),
            "autores": ", ".join(a.get("displayName", "") for a in nomes),
            "pais": "",  # a Starter API não devolve afiliação
            "ano": str(fonte.get("publishYear") or ""),
            "revista": fonte.get("sourceTitle", ""),
            "palavras_chave": ", ".join((reg.get("keywords") or {}).get("authorKeywords") or []),
            "tipo_estudo": "; ".join(reg.get("types") or []) or "Artigo de periódico",
            "resumo": "",
            "doi": normalizar_doi(ident.get("doi")),
            "citacoes": (reg.get("citations") or [{}])[0].get("count"),
            "link": (reg.get("links") or {}).get("record", ""),
            "volume": str(fonte.get("volume") or ""),
            "numero": str(fonte.get("issue") or ""),
            "paginas": f"{paginas.get('begin','')}-{paginas.get('end','')}".strip("-"),
            "pmcid": "",
            "idioma": "",
        }

    # Expanded API: estrutura static_data / dynamic_data
    static = reg.get("static_data") or {}
    resumo_ = static.get("summary") or {}
    fullrec = static.get("fullrecord_metadata") or {}
    itens = static.get("item") or {}
    dyn = reg.get("dynamic_data") or {}

    def titulos(tipo: str) -> str:
        t = (resumo_.get("titles") or {}).get("title") or []
        if isinstance(t, dict):
            t = [t]
        for x in t:
            if x.get("type") == tipo:
                return x.get("content", "")
        return ""

    nomes = ((resumo_.get("names") or {}).get("name")) or []
    if isinstance(nomes, dict):
        nomes = [nomes]
    autores = ", ".join(n.get("full_name", "") for n in nomes if n.get("role") == "author")

    ids = ((dyn.get("cluster_related") or {}).get("identifiers") or {}).get("identifier") or []
    if isinstance(ids, dict):
        ids = [ids]
    mapa = {i.get("type"): i.get("value") for i in ids}

    pub = (resumo_.get("pub_info") or {})
    paginas = pub.get("page") or {}
    enderecos = ((fullrec.get("addresses") or {}).get("address_name")) or []
    if isinstance(enderecos, dict):
        enderecos = [enderecos]
    end_txt = " | ".join(
        (e.get("address_spec") or {}).get("full_address", "") for e in enderecos)

    resumo_txt = ""
    ab = ((fullrec.get("abstracts") or {}).get("abstract") or {})
    if ab:
        p = (ab.get("abstract_text") or {}).get("p")
        resumo_txt = " ".join(p) if isinstance(p, list) else (p or "")

    kw = ((fullrec.get("keywords") or {}).get("keyword")) or []
    if isinstance(kw, str):
        kw = [kw]

    contagem = ((dyn.get("citation_related") or {}).get("tc_list") or {}).get("silo_tc") or {}
    return {
        "pmid": str(mapa.get("pmid", "")).replace("MEDLINE:", ""),
        "fonte": "Web of Science",
        "titulo": titulos("item"),
        "autores": autores,
        "pais": pais_de(end_txt),
        "ano": str(pub.get("pubyear") or ""),
        "revista": titulos("source"),
        "palavras_chave": ", ".join(kw),
        "tipo_estudo": (itens.get("doctype") or "Artigo de periódico"),
        "resumo": resumo_txt,
        "doi": normalizar_doi(mapa.get("doi") or mapa.get("xref_doi")),
        "citacoes": contagem.get("local_count"),
        "link": f"https://www.webofscience.com/wos/woscc/full-record/{reg.get('UID','')}",
        "volume": str(pub.get("vol") or ""),
        "numero": str(pub.get("issue") or ""),
        "paginas": f"{paginas.get('begin','')}-{paginas.get('end','')}".strip("-"),
        "pmcid": "",
        "idioma": ((fullrec.get("normalized_languages") or {}).get("language") or {}).get("content", ""),
    }


NORMALIZADORES = {
    "PubMed": de_pubmed,
    "Scopus": de_scopus,
    "Web of Science": de_wos,
}


def normalizar(reg: dict) -> dict:
    r = NORMALIZADORES[reg["_fonte"]](reg)
    return {c: r.get(c, "") for c in CAMPOS}


# ══════════════════════════════════════════════════════════ Deduplicação ═══
def deduplicar(registros: list[dict]) -> tuple[list[dict], list[dict]]:
    """Devolve (únicos, duplicatas). Ordem de confiabilidade: DOI, PMID, título.

    Ao fundir duplicatas, mantém o primeiro registro e completa seus campos
    vazios com os do duplicado — assim um registro da Starter API (sem resumo)
    herda o resumo da versão do PubMed.
    """
    unicos: list[dict] = []
    duplicatas: list[dict] = []
    por_doi: dict[str, int] = {}
    por_pmid: dict[str, int] = {}
    por_titulo: dict[str, int] = {}

    for r in registros:
        doi, pmid, tit = r.get("doi", ""), r.get("pmid", ""), chave_titulo(r.get("titulo"))
        idx = None
        criterio = ""
        if doi and doi in por_doi:
            idx, criterio = por_doi[doi], "doi"
        elif pmid and pmid in por_pmid:
            idx, criterio = por_pmid[pmid], "pmid"
        elif tit and len(tit) > 15 and tit in por_titulo:
            idx, criterio = por_titulo[tit], "titulo"

        if idx is not None:
            alvo = unicos[idx]
            for campo, valor in r.items():
                if valor not in (None, "") and alvo.get(campo) in (None, ""):
                    alvo[campo] = valor
            fontes = set(alvo["fonte"].split("; ")) | {r["fonte"]}
            alvo["fonte"] = "; ".join(sorted(fontes))
            duplicatas.append({**r, "_criterio": criterio})
            # o registro fundido pode ter ganhado identificadores; reindexa
            if alvo.get("doi"):
                por_doi.setdefault(alvo["doi"], idx)
            if alvo.get("pmid"):
                por_pmid.setdefault(alvo["pmid"], idx)
            continue

        unicos.append(dict(r))
        i = len(unicos) - 1
        if doi:
            por_doi.setdefault(doi, i)
        if pmid:
            por_pmid.setdefault(pmid, i)
        if tit and len(tit) > 15:
            por_titulo.setdefault(tit, i)

    return unicos, duplicatas
