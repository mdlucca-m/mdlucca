#!/usr/bin/env python3
"""Testes da massa de teste: ela precisa ser coerente para servir de teste.

    python3 -m unittest discover -s tests -v

Massa incoerente esconde defeito em vez de revelar. Estes testes conferem o
que o painel assume: nenhuma data no futuro, nenhum artigo com aceite sem
submissao, series historicas que batem com os indicadores e reprodutibilidade
pela semente. Nada aqui vai a rede nem toca o banco de producao.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import demo, lake  # noqa: E402
from lape.db import Database  # noqa: E402

HOJE = date(2026, 6, 15)      # data fixa: a massa nao muda de um dia para o outro


class TestGeracao(unittest.TestCase):
    """A massa antes de entrar no banco."""

    @classmethod
    def setUpClass(cls):
        cls.massa = demo.build(seed=7, n_artigos=90, hoje=HOJE)

    def test_mesma_semente_mesma_massa(self):
        outra = demo.build(seed=7, n_artigos=90, hoje=HOJE)
        self.assertEqual(self.massa["articles"], outra["articles"])
        self.assertEqual(self.massa["submissions"], outra["submissions"])

    def test_sementes_diferentes_massas_diferentes(self):
        outra = demo.build(seed=8, n_artigos=90, hoje=HOJE)
        self.assertNotEqual(self.massa["articles"], outra["articles"])

    def test_titulos_nao_se_repetem(self):
        # o titulo e a chave do artigo no banco: repetir viraria um registro so
        titulos = [a["Título"] for a in self.massa["articles"]]
        self.assertEqual(len(titulos), len(set(titulos)))

    def test_nenhuma_data_no_futuro(self):
        limite = HOJE.isoformat()
        for artigo in self.massa["articles"]:
            for campo in ("Data de início", "Data de submissão", "Data do aceite",
                          "Data de publicação"):
                valor = artigo.get(campo)
                if valor:
                    self.assertLessEqual(valor, limite, f"{campo} de {artigo['Título'][:40]}")
        for envio in self.massa["submissions"]:
            self.assertLessEqual(envio["Data de submissão"], limite)
            if envio["Data da decisão"]:
                self.assertLessEqual(envio["Data da decisão"], limite)

    def test_decisao_vem_depois_da_submissao(self):
        for envio in self.massa["submissions"]:
            if envio["Data da decisão"]:
                self.assertGreater(envio["Data da decisão"], envio["Data de submissão"])

    def test_em_avaliacao_nao_tem_data_de_decisao(self):
        # se houve decisao, o artigo nao esta mais em avaliacao
        for envio in self.massa["submissions"]:
            if envio["Decisão"] == "Em avaliação":
                self.assertIsNone(envio["Data da decisão"])

    def test_manuscrito_em_escrita_nao_tem_submissao(self):
        em_escrita = {a["Título"] for a in self.massa["articles"]
                      if a["Situação"] == "Em produção"}
        enviados = {s["Artigo"] for s in self.massa["submissions"]}
        self.assertEqual(em_escrita & enviados, set())

    def test_publicado_tem_o_ciclo_completo(self):
        for artigo in self.massa["articles"]:
            if artigo["Situação"] != "Publicado":
                continue
            self.assertIn("Data de submissão", artigo)
            self.assertIn("Data do aceite", artigo)
            self.assertIn("Data de publicação", artigo)
            self.assertLessEqual(artigo["Data de início"], artigo["Data de submissão"])
            self.assertLessEqual(artigo["Data de submissão"], artigo["Data do aceite"])
            self.assertLessEqual(artigo["Data do aceite"], artigo["Data de publicação"])
            self.assertTrue(artigo["DOI"].startswith("10."))

    def test_recusa_tem_motivo(self):
        for envio in self.massa["submissions"]:
            if envio["Decisão"] in ("Rejeitado", "Desk reject"):
                self.assertTrue(envio["Motivo da recusa"])

    def test_todas_as_colunas_sao_reconhecidas(self):
        # a massa sai com os nomes de coluna das planilhas: se o mapa de
        # sinonimos perder um nome, o teste acusa aqui e nao no painel vazio
        for entidade in ("research_lines", "institutions", "rejection_reasons", "members",
                         "projects", "project_members", "articles", "submissions", "events"):
            demo.mapear(entidade, self.massa[entidade])

    def test_agenda_cobre_passado_e_futuro(self):
        datas = [e["Data"][:10] for e in self.massa["events"]]
        self.assertTrue(any(d < HOJE.isoformat() for d in datas))
        self.assertTrue(any(d > HOJE.isoformat() for d in datas))


class TestCarga(unittest.TestCase):
    """A massa depois de passar pelos ingestores de verdade."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Database(Path(cls.tmp.name) / "demo.sqlite")
        demo.seed(cls.db, seed_value=11, n_artigos=90, hoje=HOJE, verbose=False)
        lake.ensure_schema(cls.db)
        lake.build_gold(cls.db, verbose=False)
        lake.take_snapshot(cls.db, verbose=False)
        demo._historico(cls.db, hoje=HOJE)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.tmp.cleanup()

    def test_tudo_foi_gravado(self):
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM articles"), 90)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM research_lines"), len(demo.LINHAS))
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM members"), len(demo.PESSOAS))
        self.assertGreater(self.db.scalar("SELECT COUNT(*) FROM submissions"), 40)
        self.assertGreater(self.db.scalar("SELECT COUNT(*) FROM events"), 100)

    def test_todo_artigo_tem_autoria(self):
        orfaos = self.db.scalar(
            "SELECT COUNT(*) FROM articles a WHERE NOT EXISTS"
            " (SELECT 1 FROM article_authors x WHERE x.article_id = a.id)")
        self.assertEqual(orfaos, 0)

    def test_status_e_datas_nao_se_contradizem(self):
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM articles WHERE status = 'em_producao'"
            " AND first_submission_on IS NOT NULL"), 0)
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM articles WHERE status = 'publicado'"
            " AND published_on IS NULL"), 0)
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM submissions WHERE submitted_on > ?", (HOJE.isoformat(),)), 0)

    def test_indice_h_foi_calculado(self):
        self.assertGreater(self.db.scalar("SELECT MAX(h_index) FROM members") or 0, 0)

    def test_a_rede_de_coautoria_tem_ligacoes(self):
        pares = self.db.scalar(
            "SELECT COUNT(*) FROM article_authors a JOIN article_authors b"
            " ON a.article_id = b.article_id AND a.member_id < b.member_id")
        self.assertGreater(pares, 50)

    def test_ha_achados_pendentes_para_revisar(self):
        self.assertGreater(self.db.scalar(
            "SELECT COUNT(*) FROM discoveries WHERE status = 'pendente'"), 0)

    def test_serie_historica_bate_com_o_indicador_de_hoje(self):
        """O ultimo ponto da serie tem de ser o numero que o painel mostra.

        E o que faz a seta de variacao querer dizer alguma coisa: se a serie
        contasse outra coisa, o delta seria a diferenca entre duas definicoes.
        """
        atual = {
            "publicados": self.db.scalar(
                "SELECT COUNT(*) FROM articles WHERE status = 'publicado'"),
            "em_producao": self.db.scalar(
                "SELECT COUNT(*) FROM articles WHERE status = 'em_producao'"),
            "submetidos": self.db.scalar(
                "SELECT COUNT(*) FROM articles WHERE status IN ('submetido','em_revisao')"),
            "artigos": self.db.scalar("SELECT COUNT(*) FROM articles"),
        }
        for metrica, esperado in atual.items():
            serie = lake.metric_history(self.db, metrica, "total", 60)
            self.assertTrue(serie, f"serie vazia: {metrica}")
            self.assertEqual(int(serie[-1]["value"]), esperado, f"ultimo ponto de {metrica}")

    def test_serie_historica_nao_anda_para_tras(self):
        # o que ja foi publicado nao despublica: a serie so cresce
        for metrica in ("artigos", "publicados", "submissoes", "atividades"):
            valores = [r["value"] for r in lake.metric_history(self.db, metrica, "total", 60)]
            self.assertEqual(valores, sorted(valores), f"{metrica} regride")

    def test_citacoes_crescem_com_o_tempo(self):
        artigo = self.db.dicts(
            "SELECT article_id FROM citation_snapshots WHERE source = 'openalex'"
            " GROUP BY article_id HAVING COUNT(*) >= 3 LIMIT 1")
        self.assertTrue(artigo, "nenhum artigo com serie de citacoes")
        serie = [r["citations"] for r in self.db.dicts(
            "SELECT citations FROM citation_snapshots WHERE article_id = ?"
            " AND source = 'openalex' ORDER BY snapshot_on", (artigo[0]["article_id"],))]
        self.assertEqual(serie, sorted(serie))

    def test_o_lakehouse_ficou_completo(self):
        for tabela in ("fact_article", "fact_authorship", "fact_submission",
                       "fact_event", "dim_researcher", "dim_line", "dim_journal"):
            self.assertGreater(self.db.scalar(f"SELECT COUNT(*) FROM {tabela}"), 0, tabela)


class TestPainel(unittest.TestCase):
    """O payload que o painel recebe: todo bloco precisa ter o que desenhar.

    Aqui a massa e ancorada em `date.today()`, e nao na data fixa das outras
    classes: o painel chama de "proximas atividades" o que vem depois de hoje
    de verdade, e uma agenda ancorada no passado nunca teria nenhuma.
    """

    @classmethod
    def setUpClass(cls):
        from lape import metrics

        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Database(Path(cls.tmp.name) / "demo.sqlite")
        demo.run(cls.db, seed_value=3, n_artigos=80,
                 report=Path(cls.tmp.name) / "demo.html", verbose=False)
        cls.payload = metrics.build_payload(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.tmp.cleanup()

    def test_o_painel_foi_gerado(self):
        html = (Path(self.tmp.name) / "demo.html").read_text(encoding="utf-8")
        self.assertIn("MASSA DE TESTE", html)
        self.assertIn("Charts", html)
        self.assertIn("Icons", html)

    def test_republicar_nao_apaga_o_aviso_de_massa_de_teste(self):
        """Republicar pelo curador tem de manter o aviso.

        Sem isto, um `curador` rodado sobre o banco de demonstracao troca um
        painel avisado por um que parece dado de verdade do laboratorio.
        """
        from lape.agents import curator

        destino = Path(self.tmp.name) / "republicado.html"
        curator.publish(self.db, output=destino)
        self.assertIn("MASSA DE TESTE", destino.read_text(encoding="utf-8"))

    def test_banco_de_verdade_nao_ganha_o_aviso(self):
        """E o contrario tambem: banco normal nao pode sair marcado como teste."""
        from lape.agents import curator
        from lape import ingest_excel

        outro = tempfile.TemporaryDirectory()
        db = Database(Path(outro.name) / "real.sqlite")
        db.migrate()
        ingest_excel.ingest_articles(db, [{"title": "Artigo de verdade", "authors": "Andrade"}])
        destino = Path(outro.name) / "painel.html"
        try:
            curator.publish(db, output=destino)
            self.assertNotIn("MASSA DE TESTE", destino.read_text(encoding="utf-8"))
        finally:
            db.close()
            outro.cleanup()

    def test_nenhum_bloco_do_painel_esta_vazio(self):
        p = self.payload
        self.assertGreater(p["overview"]["n_articles"], 0)
        self.assertGreater(p["overview"]["n_published"], 0)
        self.assertGreater(p["overview"]["best_h_index"], 0)
        for bloco in ("articles", "researchers", "research_lines", "projects",
                      "submissions", "network", "timeline", "spatial", "quality",
                      "most_cited_scopus", "most_cited_wos", "acceptances", "rejected"):
            self.assertTrue(p.get(bloco), f"bloco vazio no painel: {bloco}")
        self.assertTrue(p["agenda"]["events"])
        self.assertTrue(p["agenda"]["upcoming"], "sem atividade futura: o calendario fica vazio")
        self.assertTrue(p["history"]["available"], "sem historico medido: sem setas de variacao")

    def test_a_producao_esta_espalhada_pelos_anos(self):
        anos = {a["year_published"] for a in self.payload["articles"] if a.get("year_published")}
        self.assertGreaterEqual(len(anos), 4, "producao concentrada num ano so")

    def test_todas_as_linhas_de_pesquisa_tem_artigo(self):
        for linha in self.payload["research_lines"]:
            self.assertGreater(linha["n_articles"], 0, linha["name"])


if __name__ == "__main__":
    unittest.main()
