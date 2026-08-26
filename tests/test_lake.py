#!/usr/bin/env python3
"""Testes do lakehouse: camadas, modelo dimensional, histórico e consultas.

    python3 -m unittest discover -s tests -v

Nenhum acesso à rede. As camadas são construídas em diretório temporário.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth, ingest_excel, lake, metrics  # noqa: E402
from lape.db import Database  # noqa: E402


def povoar(db: Database) -> None:
    """Um laboratório pequeno, mas com todos os casos que as consultas cruzam."""
    ingest_excel.ingest_research_lines(db, [
        {"name": "Psicologia do Esporte", "code": "PSI"},
        {"name": "Dor Crônica", "code": "DOR"},
    ])
    ingest_excel.ingest_articles(db, [
        {"title": "Ansiedade em atletas", "authors": "Andrade; Vilarino",
         "status": "Publicado", "year_published": "2025", "doi": "10.1/a",
         "journal": "Journal of Sports Sciences", "scopus_citations": "12",
         "research_line": "Psicologia do Esporte", "started_on": "01/02/2023",
         "first_submission_on": "10/11/2023", "accepted_on": "15/03/2024",
         "published_on": "01/05/2025", "study_type": "Ensaio clínico"},
        {"title": "Sono e desempenho", "authors": "Loiane; Andrade",
         "status": "Publicado", "year_published": "2024", "doi": "10.1/b",
         "journal": "Sleep Science", "scopus_citations": "3",
         "research_line": "Psicologia do Esporte", "published_on": "10/06/2024"},
        {"title": "Fibromialgia e exercício", "authors": "Vilarino; Loiane",
         "research_line": "Dor Crônica", "started_on": "01/03/2025"},
    ])
    ingest_excel.ingest_submissions(db, [
        {"article": "Fibromialgia e exercício", "attempt_no": "1",
         "journal": "Rheumatology International", "submitted_on": "14/07/2026",
         "decision": "Desk rejection", "decision_on": "17/07/2026"},
        {"article": "Fibromialgia e exercício", "attempt_no": "2",
         "journal": "Physiotherapy Research", "submitted_on": "22/07/2026"},
    ])
    ingest_excel.ingest_projects(db, [
        {"code": "P1", "name": "Exercício e dor", "funder": "CNPq",
         "members": "Andrade; Vilarino", "status": "Em andamento"},
    ])
    ingest_excel.ingest_events(db, [
        {"title": "Reunião do LAPE", "kind": "Reunião", "start_at": "02/09/2026 14:00",
         "city": "Florianópolis", "state": "SC"},
    ])
    metrics.compute_h_indexes(db)


class LakeCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.db = Database(self.base / "db.sqlite")
        self.db.migrate()
        povoar(self.db)
        # o lake acompanha o banco: aqui, o diretório temporário
        self._lake_dir = lake.LAKE_DIR
        self._bronze = lake.BRONZE_DIR
        self._gold = lake.GOLD_DIR
        lake.LAKE_DIR = self.base / "lake"
        lake.BRONZE_DIR = lake.LAKE_DIR / "bronze"
        lake.GOLD_DIR = lake.LAKE_DIR / "gold"

    def tearDown(self):
        lake.LAKE_DIR, lake.BRONZE_DIR, lake.GOLD_DIR = self._lake_dir, self._bronze, self._gold
        self.db.close()
        self.tmp.cleanup()


class TestCamadaBronze(LakeCase):
    def test_preserva_o_arquivo_cru_com_impressao_digital(self):
        raw = self.base / "raw"
        raw.mkdir()
        (raw / "planilha.csv").write_text("titulo;ano\nEstudo;2025\n", encoding="utf-8")
        resultado = lake.capture_bronze(self.db, raw, verbose=False)
        self.assertEqual(resultado["captured"], 1)
        registro = self.db.dicts("SELECT * FROM lake_manifest WHERE layer = 'bronze'")[0]
        self.assertEqual(len(registro["sha256"]), 64)
        guardado = Path(registro["stored_path"])
        self.assertTrue(guardado.exists() or (ROOT / guardado).exists())

    def test_nao_duplica_o_mesmo_conteudo(self):
        raw = self.base / "raw"
        raw.mkdir()
        (raw / "planilha.csv").write_text("a;b\n1;2\n", encoding="utf-8")
        lake.capture_bronze(self.db, raw, verbose=False)
        segunda = lake.capture_bronze(self.db, raw, verbose=False)
        self.assertEqual(segunda["captured"], 0)
        self.assertEqual(segunda["skipped"], 1)

    def test_conteudo_diferente_gera_nova_captura(self):
        raw = self.base / "raw"
        raw.mkdir()
        arquivo = raw / "planilha.csv"
        arquivo.write_text("a;b\n1;2\n", encoding="utf-8")
        lake.capture_bronze(self.db, raw, verbose=False)
        arquivo.write_text("a;b\n1;3\n", encoding="utf-8")   # uma célula mudou
        self.assertEqual(lake.capture_bronze(self.db, raw, verbose=False)["captured"], 1)
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM lake_manifest WHERE layer = 'bronze'"), 2)


class TestCamadaOuro(LakeCase):
    def test_constroi_fatos_e_dimensoes(self):
        counts = lake.build_gold(self.db, verbose=False)
        self.assertEqual(counts["fact_article"], 3)
        # 2 tentativas da aba de submissoes + a 1a tentativa derivada da
        # propria linha do artigo publicado (que traz data de submissao)
        self.assertEqual(counts["fact_submission"], 3)
        derivada = self.db.dicts(
            "SELECT journal FROM fact_submission WHERE article_id ="
            " (SELECT article_id FROM fact_article WHERE title = 'Ansiedade em atletas')")
        self.assertEqual(len(derivada), 1)
        self.assertEqual(counts["dim_line"], 2)
        self.assertGreaterEqual(counts["dim_journal"], 3)
        self.assertEqual(counts["fact_event"], 1)

    def test_calcula_as_durações_do_ciclo(self):
        lake.build_gold(self.db, verbose=False)
        row = self.db.dicts(
            "SELECT days_start_to_publication, days_submission_to_acceptance,"
            "       best_citations, n_authors"
            " FROM fact_article WHERE title = 'Ansiedade em atletas'")[0]
        # 01/02/2023 -> 01/05/2025
        self.assertEqual(row["days_start_to_publication"], (date(2025, 5, 1) - date(2023, 2, 1)).days)
        # 10/11/2023 -> 15/03/2024
        self.assertEqual(row["days_submission_to_acceptance"],
                         (date(2024, 3, 15) - date(2023, 11, 10)).days)
        self.assertEqual(row["best_citations"], 12)
        self.assertEqual(row["n_authors"], 2)

    def test_intervalo_entre_tentativas(self):
        lake.build_gold(self.db, verbose=False)
        segunda = self.db.dicts(
            "SELECT days_since_previous, days_decision_to_resubmit, decision"
            " FROM fact_submission WHERE attempt_no = 2")[0]
        self.assertEqual(segunda["days_since_previous"], 8)        # 14/07 -> 22/07
        self.assertEqual(segunda["days_decision_to_resubmit"], 5)  # 17/07 -> 22/07

    def test_reconstruir_nao_duplica(self):
        lake.build_gold(self.db, verbose=False)
        lake.build_gold(self.db, verbose=False)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM fact_article"), 3)

    def test_reconstruir_preserva_o_historico(self):
        lake.build_gold(self.db, verbose=False)
        lake.take_snapshot(self.db, "2026-01-01", verbose=False)
        lake.build_gold(self.db, verbose=False)   # derruba fatos e dimensões
        self.assertGreater(self.db.scalar(
            "SELECT COUNT(*) FROM metric_snapshot WHERE snapshot_on = '2026-01-01'"), 0)


class TestHistorico(LakeCase):
    def test_mede_e_calcula_variacao(self):
        lake.build_gold(self.db, verbose=False)
        antigo = (date.today() - timedelta(days=30)).isoformat()
        lake.take_snapshot(self.db, antigo, verbose=False)
        # um artigo a mais entre as duas medições
        ingest_excel.ingest_articles(self.db, [{"title": "Novo estudo", "authors": "Andrade"}])
        lake.build_gold(self.db, verbose=False)
        lake.take_snapshot(self.db, verbose=False)

        delta = lake.metric_delta(self.db, "artigos", 30)
        self.assertEqual(delta["current"], 4)
        self.assertEqual(delta["previous"], 3)
        self.assertEqual(delta["delta"], 1)

    def test_serie_por_linha_de_pesquisa(self):
        lake.build_gold(self.db, verbose=False)
        lake.take_snapshot(self.db, verbose=False)
        serie = lake.metric_history(self.db, "artigos", "linha")
        linhas = {row["dim_value"] for row in serie}
        self.assertIn("Psicologia do Esporte", linhas)
        self.assertIn("Dor Crônica", linhas)

    def test_payload_expoe_o_historico(self):
        lake.build_gold(self.db, verbose=False)
        lake.take_snapshot(self.db, verbose=False)
        historico = metrics.measured_history(self.db)
        self.assertTrue(historico["available"])
        self.assertEqual(historico["snapshots"], 1)
        self.assertIn("publicados", historico["series"])


class TestConsulta(LakeCase):
    def setUp(self):
        super().setUp()
        lake.build_gold(self.db, verbose=False)

    def test_agrega_por_dimensao(self):
        result = lake.query(self.db, "artigos", "linha")
        valores = {row["dim1"]: row["valor"] for row in result["rows"]}
        self.assertEqual(valores["Psicologia do Esporte"], 2)
        self.assertEqual(valores["Dor Crônica"], 1)
        self.assertEqual(result["total"], 3)

    def test_medida_derivada(self):
        result = lake.query(self.db, "citacoes", "linha")
        valores = {row["dim1"]: row["valor"] for row in result["rows"]}
        self.assertEqual(valores["Psicologia do Esporte"], 15)   # 12 + 3

    def test_quebra_em_duas_dimensoes(self):
        result = lake.query(self.db, "artigos", "linha", split="status")
        pares = {(row["dim1"], row["dim2"]): row["valor"] for row in result["rows"]}
        self.assertEqual(pares[("Psicologia do Esporte", "publicado")], 2)
        self.assertEqual(pares[("Dor Crônica", "submetido")], 1)

    def test_filtro(self):
        result = lake.query(self.db, "artigos", "status", filters={"linha": "Dor Crônica"})
        self.assertEqual(result["total"], 1)

    def test_filtro_por_integrante(self):
        andrade = self.db.scalar("SELECT id FROM members WHERE name_key LIKE 'andrade%'")
        result = lake.query(self.db, "artigos", "linha", filters={"integrante": andrade})
        self.assertEqual(result["total"], 2)

    def test_medida_desconhecida_e_recusada(self):
        with self.assertRaises(lake.QueryError):
            lake.query(self.db, "faturamento", "linha")

    def test_dimensao_desconhecida_e_recusada(self):
        with self.assertRaises(lake.QueryError):
            lake.query(self.db, "artigos", "signo")

    def test_filtro_desconhecido_e_recusado(self):
        with self.assertRaises(lake.QueryError):
            lake.query(self.db, "artigos", "linha", filters={"drop": "table"})

    def test_nao_ha_injecao_pela_dimensao(self):
        # o cliente escolhe chaves, nunca escreve SQL
        with self.assertRaises(lake.QueryError):
            lake.query(self.db, "artigos", "linha) UNION SELECT 1,2 --")
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM fact_article"), 3)

    def test_valor_de_filtro_perigoso_e_tratado_como_dado(self):
        result = lake.query(self.db, "artigos", "linha",
                            filters={"linha": "'; DROP TABLE fact_article; --"})
        self.assertEqual(result["total"], 0)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM fact_article"), 3)

    def test_catalogo_descreve_o_que_existe(self):
        catalogo = lake.catalog()
        ids = {m["id"] for m in catalogo["measures"]}
        self.assertIn("artigos", ids)
        self.assertIn("dias_ate_publicar", ids)
        self.assertNotIn("total", {d["id"] for d in catalogo["dimensions"]})


class TestExportacao(LakeCase):
    def test_grava_a_camada_ouro_em_arquivo(self):
        lake.build_gold(self.db, verbose=False)
        resultado = lake.export(self.db, lake.GOLD_DIR, verbose=False)
        if not resultado["format"]:
            self.skipTest("pandas ausente")
        self.assertGreaterEqual(resultado["written"], 8)
        arquivos = list(lake.GOLD_DIR.glob("fact_article.*"))
        self.assertTrue(arquivos, "fact_article não foi exportado")
        self.assertGreater(arquivos[0].stat().st_size, 0)


class TestApiAnalitica(unittest.TestCase):
    """A rota /api/query, conversando por HTTP como o painel faz."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "api.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        povoar(db)
        lake_dir = Path(cls.tmp.name) / "lake"
        cls._dirs = (lake.LAKE_DIR, lake.BRONZE_DIR, lake.GOLD_DIR)
        lake.LAKE_DIR, lake.BRONZE_DIR, lake.GOLD_DIR = (
            lake_dir, lake_dir / "bronze", lake_dir / "gold")
        lake.build_gold(db, verbose=False)
        lake.take_snapshot(db, verbose=False)
        auth.create_account(db, "Alexandro Andrade", "admin@udesc.br", "senhaforte123",
                            role="admin")
        db.close()

        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *a, **k: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        lake.LAKE_DIR, lake.BRONZE_DIR, lake.GOLD_DIR = cls._dirs
        cls.tmp.cleanup()

    def call(self, path, method="GET", body=None, cookie=None):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        if cookie:
            headers["Cookie"] = f"{api.COOKIE_NAME}={cookie}"
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode())
                raw_cookie = response.headers.get("Set-Cookie") or ""
                token = raw_cookie.split("=")[1].split(";")[0] if raw_cookie else None
                return response.status, payload, token
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode()), None

    def entrar(self):
        _, _, token = self.call("/api/auth/login", "POST",
                                {"login": "admin@udesc.br", "senha": "senhaforte123"})
        return token

    def test_consulta_exige_login(self):
        status, _, _ = self.call("/api/query?medida=artigos&por=linha")
        self.assertEqual(status, 401)

    def test_consulta_agrega(self):
        token = self.entrar()
        status, body, _ = self.call("/api/query?medida=artigos&por=linha", cookie=token)
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 3)
        self.assertEqual(body["by_label"], "Linha de pesquisa")

    def test_consulta_com_quebra_e_filtro(self):
        token = self.entrar()
        status, body, _ = self.call(
            "/api/query?medida=citacoes&por=ano_publicacao&quebra=linha&linha=Psicologia%20do%20Esporte",
            cookie=token)
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 15)
        self.assertEqual(body["split"], "linha")

    def test_medida_invalida_devolve_400(self):
        token = self.entrar()
        status, body, _ = self.call("/api/query?medida=lucro&por=linha", cookie=token)
        self.assertEqual(status, 400)
        self.assertIn("medida desconhecida", body["error"])

    def test_catalogo(self):
        token = self.entrar()
        status, body, _ = self.call("/api/catalog", cookie=token)
        self.assertEqual(status, 200)
        self.assertTrue(body["measures"])
        self.assertTrue(body["dimensions"])

    def test_state_e_barato_e_completo(self):
        token = self.entrar()
        status, body, _ = self.call("/api/state", cookie=token)
        self.assertEqual(status, 200)
        for key in ("articles", "members", "submissions", "events", "projects", "server_time"):
            self.assertIn(key, body)

    def test_historico(self):
        token = self.entrar()
        status, body, _ = self.call("/api/history?metrica=publicados", cookie=token)
        self.assertEqual(status, 200)
        self.assertEqual(body["metric"], "publicados")
        self.assertTrue(body["series"])

    def test_historico_de_indicador_inexistente(self):
        token = self.entrar()
        status, _, _ = self.call("/api/history?metrica=inventado", cookie=token)
        self.assertEqual(status, 400)

    def test_linhagem_exige_coordenacao(self):
        status, _, _ = self.call("/api/lake/lineage")
        self.assertEqual(status, 401)
        token = self.entrar()
        status, body, _ = self.call("/api/lake/lineage", cookie=token)
        self.assertEqual(status, 200)
        self.assertIn("items", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
