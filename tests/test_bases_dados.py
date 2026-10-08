#!/usr/bin/env python3
"""Testes da integração com as bases de citações (sem rede).

    python3 -m unittest tests.test_bases_dados -v

Nada aqui fala com OpenAlex ou Scopus: o cliente HTTP é trocado por um
falso. O que se guarda é a lógica própria do módulo -- normalizar o DOI,
escolher o registro certo, não quebrar com campo nulo, tentar de novo e
desistir, e fechar as contas por linha de pesquisa.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import bases_dados, cache  # noqa: E402
from lape.bases_dados import ApiClient, OpenAlex, Scopus, SincronizadorCitacoes  # noqa: E402
from lape.db import Database  # noqa: E402


class ClienteFalso:
    """Devolve respostas prontas e guarda as chamadas."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def _get(self, url, headers=None, params=None):
        self.chamadas.append((url, headers, params))
        return self.respostas.pop(0) if self.respostas else None


def _openalex(respostas):
    oa = OpenAlex()
    oa.client = ClienteFalso(respostas)
    return oa


class TestApiClient(unittest.TestCase):
    def test_desiste_depois_das_tentativas_e_devolve_none(self):
        cliente = ApiClient(max_retries=3)
        with mock.patch.object(bases_dados, "urlopen", side_effect=URLError("sem rede")) as aberto, \
                mock.patch("time.sleep") as espera:
            self.assertIsNone(cliente._get("https://x.test/a"))
        self.assertEqual(aberto.call_count, 3)
        self.assertEqual(espera.call_count, 2)          # nao espera depois da ultima

    def test_junta_os_parametros_na_url(self):
        cliente = ApiClient(max_retries=1)
        with mock.patch.object(bases_dados, "urlopen", side_effect=URLError("x")) as aberto:
            cliente._get("https://x.test/a", params={"q": "mood handball"})
        pedido = aberto.call_args[0][0]
        self.assertIn("q=mood+handball", pedido.full_url)


class TestOpenAlex(unittest.TestCase):
    def test_doi_sem_prefixo_vira_url_do_doi(self):
        oa = _openalex([{"results": [{"id": "W1"}]}])
        self.assertEqual(oa.buscar_por_doi("10.1000/ABC")["id"], "W1")
        self.assertEqual(oa.client.chamadas[0][2]["filter"], "doi:https://doi.org/10.1000/abc")

    def test_doi_vazio_nao_consulta(self):
        oa = _openalex([])
        self.assertIsNone(oa.buscar_por_doi(""))
        self.assertEqual(oa.client.chamadas, [])

    def test_sem_resultado_devolve_none(self):
        self.assertIsNone(_openalex([{"results": []}]).buscar_por_doi("10.1/x"))
        self.assertIsNone(_openalex([None]).buscar_por_titulo("Algo"))

    def test_titulo_sem_autores_devolve_o_primeiro(self):
        oa = _openalex([{"results": [{"id": "W1"}, {"id": "W2"}]}])
        self.assertEqual(oa.buscar_por_titulo("Mood in handball")["id"], "W1")

    def test_metricas_de_um_registro_completo(self):
        m = OpenAlex().extrair_metricas({
            "id": "W1", "doi": "https://doi.org/10.1/x", "title": "T", "cited_by_count": 12,
            "publication_year": 2023, "type": "article",
            "primary_location": {"source": {"display_name": "J Sports Sci"}},
            "open_access": {"is_oa": True}})
        self.assertEqual((m["citacoes"], m["ano_publicacao"], m["revista"], m["acesso_aberto"], m["fonte"]),
                         (12, 2023, "J Sports Sci", True, "openalex"))

    def test_campos_nulos_do_openalex_nao_quebram(self):
        """O OpenAlex manda `null`, e nao a chave ausente: `.get(k, {})` quebrava."""
        m = OpenAlex().extrair_metricas({"id": "W2", "title": "T", "cited_by_count": 0,
                                         "primary_location": None, "open_access": None})
        self.assertIsNone(m["revista"])
        self.assertFalse(m["acesso_aberto"])
        m = OpenAlex().extrair_metricas({"id": "W3", "primary_location": {"source": None}})
        self.assertIsNone(m["revista"])

    def test_registro_vazio_da_dicionario_vazio(self):
        self.assertEqual(OpenAlex().extrair_metricas({}), {})

    def test_artigo_completo_cai_para_o_titulo_quando_o_doi_nao_acha(self):
        oa = _openalex([{"results": []}, {"results": [{"id": "W9", "cited_by_count": 3}]}])
        m = oa.artigo_completo(doi="10.1/x", titulo="Mood in handball")
        self.assertEqual(m["citacoes"], 3)
        self.assertEqual(len(oa.client.chamadas), 2)


class TestScopus(unittest.TestCase):
    def test_sem_credencial_nao_consulta(self):
        s = Scopus(api_key="", inst_token="")
        s.api_key = s.inst_token = ""
        s.client = ClienteFalso([])
        self.assertFalse(s.disponivel())
        self.assertIsNone(s.buscar_por_doi("10.1/x"))
        self.assertEqual(s.client.chamadas, [])

    def test_a_chave_vai_no_cabecalho_e_as_metricas_saem_tipadas(self):
        s = Scopus(api_key="K", inst_token="T")
        s.client = ClienteFalso([{"search-results": {"entry": [{
            "eid": "2-s2.0-1", "prism:doi": "10.1/x", "dc:title": "T", "citedby-count": "7",
            "prism:coverDate": "2022-05-01", "prism:publicationName": "J"}]}}])
        m = s.artigo_completo("10.1/x")
        self.assertEqual((m["citacoes"], m["ano_publicacao"], m["fonte"]), (7, 2022, "scopus"))
        cabecalho = s.client.chamadas[0][1]
        self.assertEqual((cabecalho["X-ELS-APIKey"], cabecalho["X-ELS-Insttoken"]), ("K", "T"))


class TestSincronizador(unittest.TestCase):
    def setUp(self):
        cache.limpar()
        self.addCleanup(cache.limpar)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "b.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.db.execute("INSERT INTO research_lines (code, name, active) VALUES ('humor', 'Humor', 1)")
        self.linha = self.db.scalar("SELECT id FROM research_lines WHERE code = 'humor'")
        self.db.execute("INSERT INTO articles (title, title_key, doi, status, research_line_id)"
                        " VALUES ('A', 'a', '10.1/a', 'publicado', ?)", (self.linha,))
        self.db.execute("INSERT INTO articles (title, title_key, doi, status, research_line_id)"
                        " VALUES ('B', 'b', '10.1/b', 'publicado', ?)", (self.linha,))
        self.db.conn.commit()
        self.sync = SincronizadorCitacoes(self.db)
        self.sync.scopus.api_key = self.sync.scopus.inst_token = ""

    def test_artigo_inexistente_devolve_none(self):
        self.assertIsNone(self.sync.atualizar_artigo(99999))

    def test_o_resultado_fica_em_cache(self):
        self.sync.openalex = _openalex([{"results": [{"id": "W1", "cited_by_count": 5}]}])
        aid = self.db.scalar("SELECT id FROM articles WHERE title_key = 'a'")
        primeiro = self.sync.atualizar_artigo(aid)
        segundo = self.sync.atualizar_artigo(aid)
        self.assertEqual(primeiro["citacoes"], 5)
        self.assertEqual(segundo, primeiro)
        self.assertEqual(len(self.sync.openalex.client.chamadas), 1)     # a segunda veio do cache

    def test_a_linha_soma_so_quem_tem_dado(self):
        # artigo mais novo (B, id maior) acha 10; o outro nao acha nada nem por titulo
        self.sync.openalex = _openalex([
            {"results": [{"id": "W1", "cited_by_count": 10}]},      # B por DOI
            {"results": []}, {"results": []},                         # A: DOI e titulo sem resultado
        ])
        r = self.sync.atualizar_linha_pesquisa(self.linha)
        self.assertEqual((r["total_artigos"], r["artigos_com_dados"], r["total_citacoes"], r["media_citacoes"]),
                         (2, 1, 10, 10.0))

    def test_o_painel_fecha_as_contas_do_laboratorio(self):
        self.sync.openalex = _openalex([
            {"results": [{"id": "W1", "cited_by_count": 10}]},
            {"results": [{"id": "W2", "cited_by_count": 20}]},
        ])
        d = self.sync.dashboard_citacoes()
        self.assertEqual(d["resumo"]["total_artigos"], 2)
        self.assertEqual(d["resumo"]["total_citacoes"], 30)
        self.assertEqual(d["resumo"]["media_citacoes"], 15.0)
        self.assertEqual(d["resumo"]["linhas_ativas"], 1)


if __name__ == "__main__":
    unittest.main()
