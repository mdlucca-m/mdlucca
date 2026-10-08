#!/usr/bin/env python3
"""Testes do robô de busca das revisões (sem rede).

    python3 -m unittest tests.test_busca_revisao -v

Só o que não depende das bases: leitura das estratégias, montagem da
sintaxe de cada base e a fusão dos registros. A parte que fala com a rede
(OpenAlex, Crossref, Europe PMC, PubMed, Scopus, WoS) não é testada aqui.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import busca_revisao as busca  # noqa: E402


class TestEstrategias(unittest.TestCase):
    def setUp(self):
        self.cfg = busca.carregar()

    def test_as_duas_revisoes_existem_com_estrategias(self):
        for nome in ("humor", "mapeamento"):
            self.assertTrue(self.cfg["revisoes"][nome]["estrategias"], nome)

    def test_todo_bloco_citado_existe(self):
        for revisao in self.cfg["revisoes"].values():
            for estr in revisao["estrategias"]:
                for grupo in estr["and"]:
                    for nome in grupo:
                        self.assertIn(nome, self.cfg["blocos"], f"{estr['id']}: {nome}")

    def test_blocos_viram_grupos_sem_termo_repetido(self):
        estr = {"and": [["handebol"], ["humor", "dimensoes"]]}
        grupos = busca.blocos_da(estr, self.cfg)
        self.assertEqual(len(grupos), 2)
        for g in grupos:
            self.assertEqual(len(g), len(set(g)))


class TestSintaxe(unittest.TestCase):
    GRUPOS = [["handball", "team handball"], ["mood"]]

    def test_pubmed_marca_titulo_e_resumo(self):
        q = busca.sintaxe("pubmed", self.GRUPOS)
        self.assertIn('"team handball"[tiab]', q)
        self.assertIn(" AND ", q)

    def test_scopus_e_wos_tem_o_envelope_proprio(self):
        self.assertTrue(busca.sintaxe("scopus", self.GRUPOS).startswith("TITLE-ABS-KEY("))
        self.assertTrue(busca.sintaxe("wos", self.GRUPOS).startswith("TS="))

    def test_europepmc_usa_o_campo_title_abs(self):
        self.assertIn("TITLE_ABS:", busca.sintaxe("europepmc", self.GRUPOS))


class TestFusao(unittest.TestCase):
    def reg(self, base, titulo, doi="", pmid=""):
        return busca._reg(base, "S1", doi=doi, pmid=pmid, titulo=titulo)

    def test_mesmo_doi_em_duas_bases_vira_um_registro(self):
        regs = [self.reg("pubmed", "Mood in handball", doi="https://doi.org/10.1/ABC"),
                self.reg("scopus", "Mood in handball players", doi="10.1/abc")]
        fundidos = busca.fundir(regs)
        self.assertEqual(len(fundidos), 1)
        self.assertEqual(fundidos[0]["bases"], {"pubmed", "scopus"})

    def test_titulo_normalizado_junta_quando_falta_doi(self):
        regs = [self.reg("openalex", "Mood: in Handball!"), self.reg("crossref", "mood in handball")]
        self.assertEqual(len(busca.fundir(regs)), 1)

    def test_trabalhos_diferentes_nao_se_juntam(self):
        regs = [self.reg("pubmed", "Mood in handball", doi="10.1/a"),
                self.reg("pubmed", "Anxiety in handball", doi="10.1/b")]
        self.assertEqual(len(busca.fundir(regs)), 2)

    def test_campo_vazio_e_preenchido_pelo_registro_repetido(self):
        regs = [self.reg("pubmed", "Mood in handball", pmid="123"),
                busca._reg("scopus", "S2", doi="10.1/x", pmid="123", titulo="Mood in handball", ano=2021)]
        f = busca.fundir(regs)[0]
        self.assertEqual(f["doi"], "10.1/x")
        self.assertEqual(f["ano"], 2021)


if __name__ == "__main__":
    unittest.main()
