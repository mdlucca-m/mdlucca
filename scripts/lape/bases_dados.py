"""Integração com bases de dados de citações: OpenAlex, Scopus, Web of Science.

Este módulo coleta dados de citações e impacto de publicações em tempo real,
sincronizando com as bases externas. Cada artigo é buscado por DOI, quando
disponível, ou por título + autores. Os resultados são cacheados para evitar
sobrecarga nas APIs.

OpenAlex (https://openalex.org) é de acesso livre e não requer credenciais.
Scopus e Web of Science requerem chaves de API (variáveis de ambiente).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from . import cache, config
from .db import Database

logger = logging.getLogger(__name__)

# URLs das APIs
OPENALEX_BASE = "https://api.openalex.org/v1"
SCOPUS_BASE = "https://api.elsevier.com/content/search/scopus"
WOS_BASE = "https://api.clarivate.com/api/wos"


class ApiClient:
    """Cliente HTTP com retry e tratamento de erros."""

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.contact_email = config.CONTACT_EMAIL

    def _get(self, url: str, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> Any:
        """Faz requisição GET com retry automático."""
        if params:
            url = f"{url}?{urlencode(params)}"

        headers = headers or {}
        if self.contact_email and "User-Agent" not in headers:
            headers["User-Agent"] = f"LAPE-Lab ({self.contact_email})"

        for tentativa in range(self.max_retries):
            try:
                req = Request(url, headers=headers)
                with urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data
            except (HTTPError, URLError, json.JSONDecodeError) as e:
                if tentativa == self.max_retries - 1:
                    logger.warning(f"Falha ao buscar {url}: {e}")
                    return None
                import time
                time.sleep(2 ** tentativa)
        return None


class OpenAlex:
    """Cliente para OpenAlex (base de dados de citações aberta)."""

    def __init__(self):
        self.client = ApiClient()

    def buscar_por_doi(self, doi: str) -> dict[str, Any] | None:
        """Busca artigo por DOI no OpenAlex."""
        if not doi:
            return None
        # Normalizar DOI
        doi = doi.lower().strip()
        if not doi.startswith("http"):
            doi = f"https://doi.org/{doi}" if not doi.startswith("doi.org") else f"https://{doi}"
        if not doi.startswith("https://"):
            doi = f"https://doi.org/{doi}"

        params = {"filter": f"doi:{doi}", "per-page": 1}
        data = self.client._get(f"{OPENALEX_BASE}/works", params=params)
        if data and data.get("results"):
            return data["results"][0]
        return None

    def buscar_por_titulo(self, titulo: str, autores: list[str] | None = None) -> dict[str, Any] | None:
        """Busca artigo por título (e opcionalmente autores) no OpenAlex."""
        if not titulo:
            return None

        # Buscar por título exato
        params = {"filter": f"title.search:{titulo}", "per-page": 10}
        data = self.client._get(f"{OPENALEX_BASE}/works", params=params)

        if not data or not data.get("results"):
            return None

        # Se há autores, tentar encontrar match mais preciso
        if autores:
            for work in data.get("results", []):
                work_autores = [a.get("au", "") for a in work.get("authorships", [])]
                if any(autor.lower() in " ".join(work_autores).lower() for autor in autores):
                    return work
        # Senão, retornar o primeiro
        return data["results"][0] if data["results"] else None

    def extrair_metricas(self, work: dict[str, Any]) -> dict[str, Any]:
        """Extrai métricas de impacto de um registro do OpenAlex."""
        if not work:
            return {}

        return {
            "openalex_id": work.get("id"),
            "doi": work.get("doi"),
            "titulo": work.get("title"),
            "citacoes": work.get("cited_by_count", 0),
            "ano_publicacao": work.get("publication_year"),
            "revista": work.get("primary_location", {}).get("source", {}).get("display_name"),
            "acesso_aberto": work.get("open_access", {}).get("is_oa", False),
            "tipo": work.get("type"),
            "fonte": "openalex",
        }

    def artigo_completo(self, doi: str | None = None, titulo: str | None = None, autores: list[str] | None = None) -> dict[str, Any] | None:
        """Busca artigo no OpenAlex por DOI ou título, retornando métricas completas."""
        work = None
        if doi:
            work = self.buscar_por_doi(doi)
        if not work and titulo:
            work = self.buscar_por_titulo(titulo, autores)
        if not work:
            return None
        return self.extrair_metricas(work)


class Scopus:
    """Cliente para Scopus (requer credenciais)."""

    def __init__(self, api_key: str | None = None, inst_token: str | None = None):
        self.api_key = api_key or config.SCOPUS_API_KEY
        self.inst_token = inst_token or config.SCOPUS_INST_TOKEN
        self.client = ApiClient()

    def disponivel(self) -> bool:
        """Verifica se credenciais estão configuradas."""
        return bool(self.api_key or self.inst_token)

    def buscar_por_doi(self, doi: str) -> dict[str, Any] | None:
        """Busca artigo por DOI no Scopus."""
        if not self.disponivel() or not doi:
            return None

        headers = {}
        if self.api_key:
            headers["X-ELS-APIKey"] = self.api_key
        if self.inst_token:
            headers["X-ELS-Insttoken"] = self.inst_token

        params = {"query": f"DOI({doi})", "view": "STANDARD"}
        data = self.client._get(f"{SCOPUS_BASE}", headers=headers, params=params)
        if data and data.get("search-results", {}).get("entry"):
            return data["search-results"]["entry"][0]
        return None

    def extrair_metricas(self, entry: dict[str, Any]) -> dict[str, Any]:
        """Extrai métricas de um resultado do Scopus."""
        if not entry:
            return {}

        return {
            "scopus_id": entry.get("eid"),
            "doi": entry.get("prism:doi"),
            "titulo": entry.get("dc:title"),
            "citacoes": int(entry.get("citedby-count", 0)),
            "ano_publicacao": int(entry.get("prism:coverDate", "0000").split("-")[0]),
            "revista": entry.get("prism:publicationName"),
            "fonte": "scopus",
        }

    def artigo_completo(self, doi: str) -> dict[str, Any] | None:
        """Busca artigo no Scopus por DOI, retornando métricas completas."""
        entry = self.buscar_por_doi(doi)
        if not entry:
            return None
        return self.extrair_metricas(entry)


class SincronizadorCitacoes:
    """Sincroniza dados de citações de artigos com bases externas."""

    def __init__(self, db: Database):
        self.db = db
        self.openalex = OpenAlex()
        self.scopus = Scopus()

    def atualizar_artigo(self, article_id: int, force: bool = False) -> dict[str, Any] | None:
        """Atualiza dados de citação para um artigo específico."""
        linhas = self.db.dicts(
            "SELECT id, doi, title FROM articles WHERE id = ?",
            (article_id,)
        )
        if not linhas:
            return None
        artigo = linhas[0]

        cache_key = f"citacoes_artigo_{article_id}"
        if not force:
            em_cache = cache.get(cache_key, ttl=86400)
            if em_cache is not None:
                return em_cache

        # Tentar OpenAlex primeiro (mais confiável)
        metricas = None
        if artigo.get("doi"):
            metricas = self.openalex.artigo_completo(doi=artigo["doi"])
        if not metricas and artigo.get("title"):
            metricas = self.openalex.artigo_completo(titulo=artigo["title"])

        # Fallback para Scopus se disponível
        if not metricas and self.scopus.disponivel() and artigo.get("doi"):
            metricas = self.scopus.artigo_completo(artigo["doi"])

        if metricas:
            cache.set(cache_key, metricas)
            return metricas
        return None

    def atualizar_linha_pesquisa(self, research_line_id: int, force: bool = False) -> dict[str, Any]:
        """Atualiza métricas de citação para todos os artigos de uma linha de pesquisa."""
        cache_key = f"citacoes_linha_{research_line_id}"
        if not force:
            em_cache = cache.get(cache_key, ttl=604800)  # 7 dias
            if em_cache is not None:
                return em_cache

        artigos = self.db.dicts(
            "SELECT id FROM articles WHERE research_line_id = ? ORDER BY id DESC",
            (research_line_id,)
        )

        metricas_agrupadas = {
            "total_artigos": len(artigos),
            "total_citacoes": 0,
            "media_citacoes": 0,
            "artigos_com_dados": 0,
            "artigos": [],
        }

        for artigo in artigos:
            m = self.atualizar_artigo(artigo["id"])
            if m:
                metricas_agrupadas["artigos"].append(m)
                metricas_agrupadas["total_citacoes"] += m.get("citacoes", 0)
                metricas_agrupadas["artigos_com_dados"] += 1

        if metricas_agrupadas["artigos_com_dados"] > 0:
            metricas_agrupadas["media_citacoes"] = round(
                metricas_agrupadas["total_citacoes"] / metricas_agrupadas["artigos_com_dados"],
                2
            )

        cache.set(cache_key, metricas_agrupadas)
        return metricas_agrupadas

    def dashboard_citacoes(self, force: bool = False) -> dict[str, Any]:
        """Dashboard com estatísticas de citações de todo o laboratório."""
        cache_key = "dashboard_citacoes"
        if not force:
            em_cache = cache.get(cache_key, ttl=604800)  # 7 dias
            if em_cache is not None:
                return em_cache

        # Carregar todas as linhas de pesquisa
        linhas = self.db.dicts(
            "SELECT id, name FROM research_lines WHERE active ORDER BY name"
        )

        resultado = {
            "gerado_em": datetime.now().isoformat(timespec="seconds"),
            "linhas": [],
            "resumo": {
                "total_artigos": 0,
                "total_citacoes": 0,
                "media_citacoes": 0,
                "linhas_ativas": len(linhas),
            },
        }

        total_citacoes_lab = 0
        total_artigos_lab = 0
        artigos_com_dados = 0

        for linha in linhas:
            m = self.atualizar_linha_pesquisa(linha["id"])
            resultado["linhas"].append({
                "id": linha["id"],
                "nome": linha["name"],
                **m,
            })
            total_citacoes_lab += m.get("total_citacoes", 0)
            total_artigos_lab += m.get("total_artigos", 0)
            artigos_com_dados += m.get("artigos_com_dados", 0)

        if artigos_com_dados > 0:
            resultado["resumo"]["media_citacoes"] = round(
                total_citacoes_lab / artigos_com_dados,
                2
            )

        resultado["resumo"]["total_artigos"] = total_artigos_lab
        resultado["resumo"]["total_citacoes"] = total_citacoes_lab

        cache.set(cache_key, resultado)
        return resultado


def sincronizar_citacoes(db: Database, research_line_id: int | None = None, force: bool = False) -> dict[str, Any]:
    """Função de conveniência para sincronizar dados de citações."""
    sync = SincronizadorCitacoes(db)
    if research_line_id:
        return sync.atualizar_linha_pesquisa(research_line_id, force=force)
    return sync.dashboard_citacoes(force=force)
