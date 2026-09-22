#!/usr/bin/env python3
"""Um acervo para cada linha de pesquisa, e mais segmentos nos que já havia.

    python3 -m unittest tests.test_acervos_novos -v

Até aqui dois das oito linhas tinham acervo; as outras seis não liam
nada. O que se guarda: toda linha declarada tem ao menos um acervo; todo
segmento tem palavra e nome; nenhum código se repete; a busca de cada
acervo se monta em cada base sem bloco vazio; e os segmentos novos dos
acervos antigos (aventura, inverno, eletrônicos; goleiros e pais) estão lá.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import biblioteca, linhas  # noqa: E402
from lape.db import Database  # noqa: E402

NOVOS = ("ansiedade_competitiva", "coesao_equipe", "adesao_exercicio", "cinesiofobia",
         "ar_exercicio", "cancer_exercicio", "envelhecimento_exercicio", "exergames_escola")


class TestUmAcervoPorLinha(unittest.TestCase):

    def test_toda_linha_declarada_tem_acervo(self):
        com_acervo = {d["linha"] for d in biblioteca.BIBLIOTECAS}
        for code, nome, *_ in linhas.LINHAS:
            with self.subTest(linha=nome):
                self.assertIn(code, com_acervo)

    def test_os_oito_novos_estao_declarados_e_nao_repetem_codigo(self):
        codes = [d["code"] for d in biblioteca.BIBLIOTECAS]
        self.assertEqual(len(codes), len(set(codes)))
        for code in NOVOS:
            with self.subTest(acervo=code):
                self.assertIn(code, codes)

    def test_todo_segmento_tem_nome_e_palavras(self):
        for d in biblioteca.BIBLIOTECAS:
            nomes = [n for n, _ in d["segmentos"]]
            self.assertEqual(len(nomes), len(set(nomes)), f"segmento repetido em {d['code']}")
            for nome, termos in d["segmentos"]:
                with self.subTest(acervo=d["code"], segmento=nome):
                    self.assertTrue(nome.strip())
                    self.assertTrue(termos)
                    self.assertTrue(all(t.strip() for t in termos))

    def test_todo_acervo_novo_tem_construto_populacao_regionais_e_manuais(self):
        for d in biblioteca.BIBLIOTECAS:
            if d["code"] not in NOVOS:
                continue
            with self.subTest(acervo=d["code"]):
                self.assertTrue(d["construto"])
                self.assertTrue(d["populacao"])
                self.assertTrue(d.get("regionais"))
                self.assertEqual(d["manuais"], biblioteca.BASES_MANUAIS)
                self.assertIn(d["eixo"], ("tema", "esporte"))
                self.assertGreaterEqual(len(d["segmentos"]), 8)

    def test_a_busca_se_monta_em_toda_base_sem_bloco_vazio(self):
        bases = tuple(biblioteca.BASES) + tuple(biblioteca.BASES_MANUAIS)
        for d in biblioteca.BIBLIOTECAS:
            for base in bases:
                with self.subTest(acervo=d["code"], base=base):
                    q = biblioteca.query_de(d, base=base)
                    self.assertNotIn("()", q)
                    self.assertNotIn("AND  AND", q)
                    self.assertTrue(q.strip())
                    seg = biblioteca.query_de(d, d["segmentos"][0][1], base=base)
                    self.assertGreater(len(seg), len(q))

    def test_o_mesh_so_vai_para_a_pubmed(self):
        for d in biblioteca.BIBLIOTECAS:
            if not d.get("mesh"):
                continue
            with self.subTest(acervo=d["code"]):
                self.assertIn("[MeSH Terms]", biblioteca.query_de(d, base=biblioteca.PUBMED))
                self.assertNotIn("[MeSH Terms]", biblioteca.query_de(d, base=biblioteca.SCOPUS))

    def test_a_adesao_nao_usa_adherence_solto(self):
        """"adherence" sozinho traz a adesão a remédio: 46 mil registros contra 5.400."""
        d = next(x for x in biblioteca.BIBLIOTECAS if x["code"] == "adesao_exercicio")
        self.assertNotIn("adherence", d["construto"])
        self.assertIn("exercise adherence", d["construto"])

    def test_o_cancer_e_o_envelhecimento_recortam_a_saude_mental_no_construto(self):
        cancer = next(x for x in biblioteca.BIBLIOTECAS if x["code"] == "cancer_exercicio")
        self.assertIn("exercise oncology", cancer["construto"])
        self.assertNotIn("exercise", next(x for x in biblioteca.BIBLIOTECAS
                                          if x["code"] == "envelhecimento_exercicio")["construto"])

    def test_a_ansiedade_por_modalidade_deixa_de_fora_o_que_nao_tem_literatura(self):
        nomes = [n for n, _ in biblioteca.ESPORTES_ANSIEDADE]
        self.assertNotIn("Triatlo", nomes)
        self.assertIn("Golfe, tiro e arco", nomes)
        self.assertIn("Handebol", nomes)


class TestOsSegmentosNovosDosAcervosAntigos(unittest.TestCase):

    def test_o_humor_no_esporte_ganhou_aventura_inverno_e_eletronicos(self):
        nomes = [n for n, _ in biblioteca.ESPORTES]
        for nome in ("Esportes de aventura", "Esportes de inverno", "Esportes eletrônicos"):
            with self.subTest(segmento=nome):
                self.assertIn(nome, nomes)
        self.assertGreaterEqual(len(nomes), 17)

    def test_a_motivacao_no_handebol_ganhou_goleiros_e_pais(self):
        nomes = [n for n, _ in biblioteca.TEMAS_MOTIVACAO_HANDEBOL]
        self.assertIn("Goleiros e árbitros", nomes)
        self.assertIn("Pais, família e pares", nomes)


class TestInstalarComOsNovos(unittest.TestCase):

    def test_instala_os_treze_e_liga_cada_um_a_sua_linha(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Database(Path(tmp.name) / "a.sqlite")
        self.addCleanup(db.close)
        db.migrate()
        linhas.instalar(db)
        r = biblioteca.instalar(db)
        self.assertEqual(len(r["novas"]), len(biblioteca.BIBLIOTECAS))
        pares = {l["code"]: l["linha"] for l in db.dicts(
            "SELECT b.code, rl.code AS linha FROM biblioteca b"
            " JOIN research_lines rl ON rl.id = b.research_line_id")}
        for d in biblioteca.BIBLIOTECAS:
            with self.subTest(acervo=d["code"]):
                self.assertEqual(pares.get(d["code"]), d["linha"])
        # uma busca geral mais uma por segmento, em cada base -- para todos
        esperadas = sum((1 + len(d["segmentos"])) * (len(biblioteca.BASES) + len(d.get("manuais") or ()))
                        for d in biblioteca.BIBLIOTECAS)
        self.assertEqual(db.scalar("SELECT COUNT(*) FROM biblioteca_busca"), esperadas)


if __name__ == "__main__":
    unittest.main()
