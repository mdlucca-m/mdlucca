"""Clientes das três APIs bibliográficas.

Cada cliente expõe a mesma interface:

    cliente.contar(consulta) -> int
    cliente.buscar(consulta) -> Iterator[dict]   # registros brutos da base

A normalização para o esquema da biblioteca fica em `normalizar.py`; aqui só
se resolve paginação, autenticação e formato de resposta de cada fornecedor.
"""
from __future__ import annotations

import os
import urllib.parse
from dataclasses import dataclass
from typing import Iterator
from xml.etree import ElementTree as ET

from .http import ErroHTTP, Sessao


class ChaveAusente(RuntimeError):
    pass


# ═══════════════════════════════════════════════════════ PubMed / MEDLINE ═══
@dataclass
class PubMed:
    """E-utilities. Funciona sem chave (3 req/s); com NCBI_API_KEY vai a 10 req/s.

    A consulta tem ~3,2 mil caracteres, acima do que muitos intermediários
    aceitam em URL, então tanto o esearch quanto o efetch são enviados por POST,
    como a própria NLM recomenda para termos longos.
    """
    chave: str | None = None
    email: str | None = None
    sessao: Sessao | None = None
    lote: int = 200

    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    nome = "PubMed"

    def __post_init__(self):
        self.chave = self.chave or os.environ.get("NCBI_API_KEY")
        self.email = self.email or os.environ.get("NCBI_EMAIL")
        if self.sessao is None:
            self.sessao = Sessao(req_por_segundo=10.0 if self.chave else 3.0)

    def _comuns(self, extra: dict) -> dict:
        d = {"db": "pubmed", "tool": "revisao-handebol", **extra}
        if self.chave:
            d["api_key"] = self.chave
        if self.email:
            d["email"] = self.email
        return d

    def _historico(self, consulta: str, janela: tuple[int, int] | None) -> tuple[int, str, str]:
        campos = self._comuns({
            "term": consulta, "retmode": "json", "retmax": "0", "usehistory": "y",
        })
        if janela:
            campos |= {"datetype": "pdat", "mindate": str(janela[0]), "maxdate": str(janela[1])}
        r = self.sessao.json(f"{self.BASE}/esearch.fcgi", dados=campos, rotulo="pubmed_esearch")
        res = r["esearchresult"]
        if "ERROR" in res:
            raise ErroHTTP(400, "esearch", res["ERROR"])
        return int(res["count"]), res["webenv"], res["querykey"]

    def contar(self, consulta: str, janela: tuple[int, int] | None = None) -> int:
        return self._historico(consulta, janela)[0]

    def buscar(self, consulta: str, janela: tuple[int, int] | None = None) -> Iterator[dict]:
        total, webenv, qk = self._historico(consulta, janela)
        for inicio in range(0, total, self.lote):
            bruto = self.sessao.pedir(
                f"{self.BASE}/efetch.fcgi",
                dados=self._comuns({
                    "WebEnv": webenv, "query_key": qk, "retstart": str(inicio),
                    "retmax": str(self.lote), "retmode": "xml",
                }),
                rotulo=f"pubmed_efetch_{inicio}",
            )
            raiz = ET.fromstring(bruto)
            for art in raiz.findall(".//PubmedArticle"):
                yield {"_fonte": "PubMed", "_xml": art}


# ══════════════════════════════════════════════════════════════════ Scopus ═══
@dataclass
class Scopus:
    """Scopus Search API. Exige SCOPUS_API_KEY; SCOPUS_INSTTOKEN habilita a
    view COMPLETE (resumo e lista completa de autores) fora da rede da assinante.

    Pagina por cursor, que é a única forma de passar do registro 5.000.
    """
    chave: str | None = None
    insttoken: str | None = None
    sessao: Sessao | None = None
    lote: int = 25
    view: str = "COMPLETE"

    URL = "https://api.elsevier.com/content/search/scopus"
    nome = "Scopus"

    def __post_init__(self):
        self.chave = self.chave or os.environ.get("SCOPUS_API_KEY")
        self.insttoken = self.insttoken or os.environ.get("SCOPUS_INSTTOKEN")
        if not self.chave:
            raise ChaveAusente(
                "SCOPUS_API_KEY não definida. Obtenha em https://dev.elsevier.com "
                "(chave gratuita para uso acadêmico; a view COMPLETE exige, além "
                "dela, um insttoken vinculado à assinatura institucional)."
            )
        if self.sessao is None:
            self.sessao = Sessao(req_por_segundo=6.0)

    @property
    def _cabecalhos(self) -> dict:
        c = {"X-ELS-APIKey": self.chave, "Accept": "application/json"}
        if self.insttoken:
            c["X-ELS-Insttoken"] = self.insttoken
        return c

    def _pagina(self, consulta: str, cursor: str, view: str) -> dict:
        params = urllib.parse.urlencode({
            "query": consulta, "count": str(self.lote), "cursor": cursor, "view": view,
        })
        return self.sessao.json(f"{self.URL}?{params}",
                                cabecalhos=self._cabecalhos, rotulo="scopus_search")

    def contar(self, consulta: str) -> int:
        r = self._pagina(consulta, "*", "STANDARD")
        return int(r["search-results"]["opensearch:totalResults"])

    def buscar(self, consulta: str) -> Iterator[dict]:
        view = self.view
        cursor, vistos = "*", 0
        while True:
            try:
                r = self._pagina(consulta, cursor, view)
            except ErroHTTP as e:
                # Sem entitlement para COMPLETE a API responde 401/403; cai para STANDARD.
                if view == "COMPLETE" and e.status in (401, 403):
                    view = "STANDARD"
                    continue
                raise
            res = r["search-results"]
            total = int(res["opensearch:totalResults"])
            entradas = res.get("entry") or []
            if entradas and "error" in entradas[0]:
                break
            for e in entradas:
                yield {"_fonte": "Scopus", "_view": view, **e}
            vistos += len(entradas)
            prox = (res.get("cursor") or {}).get("@next")
            if not prox or not entradas or vistos >= total:
                break
            cursor = prox


# ═════════════════════════════════════════════════════════ Web of Science ═══
@dataclass
class WebOfScience:
    """Clarivate. Tenta primeiro a Expanded API (traz resumo); se a chave não
    tiver entitlement, cai para a Starter API (sem resumo, mas com DOI, PMID e
    metadados de fonte). Exige WOS_API_KEY.
    """
    chave: str | None = None
    sessao: Sessao | None = None
    lote: int = 50
    base_dados: str = "WOS"

    URL_STARTER = "https://api.clarivate.com/apis/wos-starter/v1/documents"
    URL_EXPANDED = "https://api.clarivate.com/api/wos"
    nome = "Web of Science"

    def __post_init__(self):
        self.chave = self.chave or os.environ.get("WOS_API_KEY")
        if not self.chave:
            raise ChaveAusente(
                "WOS_API_KEY não definida. Obtenha em "
                "https://developer.clarivate.com (Web of Science Starter ou "
                "Expanded API; ambas exigem assinatura institucional ativa)."
            )
        if self.sessao is None:
            self.sessao = Sessao(req_por_segundo=2.0)

    @property
    def _cabecalhos(self) -> dict:
        return {"X-ApiKey": self.chave, "Accept": "application/json"}

    # ── Expanded ──
    def _expanded(self, consulta: str, primeiro: int, quantos: int) -> dict:
        params = urllib.parse.urlencode({
            "databaseId": self.base_dados, "usrQuery": consulta,
            "count": str(quantos), "firstRecord": str(primeiro),
        })
        return self.sessao.json(f"{self.URL_EXPANDED}?{params}",
                                cabecalhos=self._cabecalhos, rotulo="wos_expanded")

    # ── Starter ──
    def _starter(self, consulta: str, pagina: int) -> dict:
        params = urllib.parse.urlencode({
            "q": consulta, "db": self.base_dados,
            "limit": str(min(self.lote, 50)), "page": str(pagina),
        })
        return self.sessao.json(f"{self.URL_STARTER}?{params}",
                                cabecalhos=self._cabecalhos, rotulo="wos_starter")

    def contar(self, consulta: str) -> int:
        try:
            r = self._expanded(consulta, 1, 1)
            return int(r["QueryResult"]["RecordsFound"])
        except ErroHTTP as e:
            if e.status not in (401, 403, 404):
                raise
        return int(self._starter(consulta, 1)["metadata"]["total"])

    def buscar(self, consulta: str) -> Iterator[dict]:
        try:
            primeiro = 1
            total = None
            while total is None or primeiro <= total:
                r = self._expanded(consulta, primeiro, self.lote)
                qr = r["QueryResult"]
                total = int(qr["RecordsFound"])
                registros = r.get("Data", {}).get("Records", {}).get("records", {}).get("REC", [])
                if isinstance(registros, dict):
                    registros = [registros]
                if not registros:
                    break
                for reg in registros:
                    yield {"_fonte": "Web of Science", "_api": "expanded", **reg}
                primeiro += len(registros)
            return
        except ErroHTTP as e:
            if e.status not in (401, 403, 404):
                raise

        pagina, vistos, total = 1, 0, None
        while total is None or vistos < total:
            r = self._starter(consulta, pagina)
            total = int(r["metadata"]["total"])
            hits = r.get("hits") or []
            if not hits:
                break
            for h in hits:
                yield {"_fonte": "Web of Science", "_api": "starter", **h}
            vistos += len(hits)
            pagina += 1
