#!/usr/bin/env python3
"""Testes da fase real do artigo (o que o mural conta).

    python3 -m unittest tests.test_fase_do_artigo -v

O defeito: o status de `articles` sobe a mão, e muita gente deixa "submetido"
depois de o periódico pedir revisão. A parede mostrava "submetido" para o
que já estava em revisão. A fase vem da submissão mais recente.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import metrics  # noqa: E402
from lape.db import Database  # noqa: E402
from lape.util import title_key  # noqa: E402


class TestFaseDoArtigo(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "f.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()

    def artigo(self, titulo, status, *submissoes):
        aid = self.db.execute("INSERT INTO articles (title, title_key, status) VALUES (?, ?, ?)",
                              (titulo, title_key(titulo), status)).lastrowid
        for n, (decisao, rodadas) in enumerate(submissoes, 1):
            self.db.execute(
                "INSERT INTO submissions (article_id, attempt_no, journal, submitted_on, decision, review_rounds)"
                " VALUES (?, ?, 'J', '2026-01-01', ?, ?)", (aid, n, decisao, rodadas))
        self.db.conn.commit()
        return aid

    def fases(self):
        return {r["title"]: r["fase"] for r in metrics.article_rows(self.db)}

    def test_revisao_solicitada_vira_em_revisao(self):
        self.artigo("A", "submetido", ("revisao_solicitada", None))
        self.assertEqual(self.fases()["A"], "em_revisao")

    def test_rodada_de_revisao_contada_vira_em_revisao(self):
        self.artigo("B", "submetido", ("em_avaliacao", 1))
        self.assertEqual(self.fases()["B"], "em_revisao")

    def test_em_avaliacao_sem_rodada_continua_submetido(self):
        self.artigo("C", "submetido", ("em_avaliacao", None))
        self.assertEqual(self.fases()["C"], "submetido")

    def test_vale_a_submissao_mais_recente(self):
        # revisao na 1a tentativa, mas ja foi resubmetido a outro periodico
        self.artigo("D", "submetido", ("revisao_solicitada", 1), ("em_avaliacao", None))
        self.assertEqual(self.fases()["D"], "submetido")

    def test_outros_status_nao_mudam(self):
        for titulo, status in (("E", "em_producao"), ("F", "aceito"), ("G", "publicado"), ("H", "em_revisao")):
            self.artigo(titulo, status, ("revisao_solicitada", 2))
        f = self.fases()
        self.assertEqual((f["E"], f["F"], f["G"], f["H"]), ("em_producao", "aceito", "publicado", "em_revisao"))

    def test_a_lista_de_submetidos_tambem_traz_a_fase(self):
        self.artigo("I", "submetido", ("revisao_solicitada", None))
        self.assertEqual(metrics.articles_by_status(self.db, metrics.UNDER_REVIEW, "id")[0]["fase"], "em_revisao")


if __name__ == "__main__":
    unittest.main()
