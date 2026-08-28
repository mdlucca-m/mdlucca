#!/usr/bin/env python3
"""Testes da importação da produção pelas bases públicas.

    python3 -m unittest tests.test_autor -v

O erro caro aqui é importar a produção de outra pessoa: "Andrade A" traz
milhares de artigos de dezenas de gente diferente, e ninguém percebe até
o painel ter o dobro de artigos. Por isso a afiliação, a conferência
antes de gravar, e estes testes.

A fixture é MEDLINE de verdade, com registros reais do LAPE recuperados
do PubMed.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_autor, referencias, sources, variaveis  # noqa: E402
from lape.db import Database  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "pubmed_lape.nbib"


class TestTermoDeBusca(unittest.TestCase):
    def test_o_nome_vira_o_formato_da_pubmed(self):
        # a PubMed indexa "Sobrenome Iniciais"; buscar pelo nome inteiro
        # não acha nada, e o silêncio parece "esta pessoa não publicou"
        self.assertEqual(sources.termo_de_autor("Alexandro Andrade"), "Andrade A[Author]")
        self.assertEqual(sources.termo_de_autor("Guilherme Torres Vilarino"),
                         "Vilarino GT[Author]")

    def test_a_afiliacao_entra_na_busca(self):
        termo = sources.termo_de_autor("Alexandro Andrade", "UDESC")
        self.assertIn("UDESC[Affiliation]", termo)

    def test_o_ano_inicial_entra_na_busca(self):
        self.assertIn("2006", sources.termo_de_autor("Fulano Silva", None, 2006))

    def test_nome_de_uma_palavra_nao_quebra(self):
        self.assertEqual(sources.termo_de_autor("Andrade"), "Andrade[Author]")


class TestLeituraDoMedline(unittest.TestCase):
    """O arquivo que a PubMed entrega no botão 'Send to'."""

    def setUp(self):
        self.registros = referencias.ler_nbib(FIXTURE.read_text(encoding="utf-8"))

    def test_cada_registro_e_um_registro(self):
        # o defeito que este teste guarda: o MEDLINE não fecha com `ER`,
        # separa por linha em branco. Sem isso, um .nbib com cem artigos
        # virava UM registro só — com o título do primeiro e os autores de
        # todos — e a importação dizia "1 artigo lido", sem erro nenhum
        self.assertEqual(len(self.registros), 3)
        titulos = {r["title"][:20] for r in self.registros}
        self.assertEqual(len(titulos), 3)

    def test_o_doi_vem_do_lid(self):
        self.assertEqual(self.registros[0]["doi"], "10.3389/fpsyg.2023.1295652")

    def test_a_afiliacao_e_lida(self):
        # é dela que sai o país no mapa
        self.assertIn("UDESC", self.registros[0]["affiliation"])

    def test_o_pais_sai_da_afiliacao(self):
        for registro in self.registros:
            with self.subTest(titulo=registro["title"][:30]):
                achado = variaveis.pais_da_afiliacao(registro["affiliation"])
                self.assertIsNotNone(achado)
                self.assertEqual(achado[0], "Brasil")

    def test_o_ris_continua_fechando_por_er(self):
        # a regra nova não pode quebrar o formato que já funcionava
        ris = ("TY  - JOUR\nTI  - Primeiro\nPY  - 2020\nER  -\n\n"
               "TY  - JOUR\nTI  - Segundo\nPY  - 2021\nER  -\n")
        self.assertEqual(len(referencias.ler(ris, "x.ris")), 2)

    def test_linha_em_branco_no_fim_nao_cria_registro_vazio(self):
        texto = FIXTURE.read_text(encoding="utf-8") + "\n\n\n"
        self.assertEqual(len(referencias.ler_nbib(texto)), 3)


class TestResumoAntesDeGravar(unittest.TestCase):
    def setUp(self):
        registros = referencias.ler_nbib(FIXTURE.read_text(encoding="utf-8"))
        for r in registros:
            achado = variaveis.pais_da_afiliacao(r.get("affiliation"))
            r["pais"] = achado[0] if achado else None
        self.achado = {"termo": "Andrade A[Author]", "pmids": [], "registros": registros}

    def test_conta_o_que_traria(self):
        resumo = ingest_autor.resumir(self.achado)
        self.assertEqual(resumo["encontrados"], 3)
        self.assertEqual(resumo["com_doi"], 3)
        self.assertEqual(resumo["com_resumo"], 3)

    def test_mostra_o_periodo(self):
        resumo = ingest_autor.resumir(self.achado)
        self.assertEqual(resumo["primeiro_ano"], 2024)
        self.assertEqual(resumo["ultimo_ano"], 2025)

    def test_mostra_as_revistas_e_os_paises(self):
        # é por revista e país que se confere se é a pessoa certa
        resumo = ingest_autor.resumir(self.achado)
        self.assertTrue(resumo["revistas"])
        self.assertEqual(resumo["paises"], [("Brasil", 3)])

    def test_o_resumo_nao_toca_no_banco(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "t.sqlite")
            db.migrate()
            ingest_autor.resumir(self.achado)
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM articles"), 0)
            db.close()


class TestImportacaoDaProducao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        registros = referencias.ler_nbib(FIXTURE.read_text(encoding="utf-8"))
        self.achado = {"termo": "t", "pmids": [], "registros": registros}

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_grava_cada_artigo_uma_vez(self):
        primeira = ingest_autor.importar(self.db, self.achado, quem="Alexandro Andrade")
        self.assertEqual(primeira["novos"], 3)
        segunda = ingest_autor.importar(self.db, self.achado, quem="Alexandro Andrade")
        self.assertEqual(segunda["novos"], 0)
        self.assertEqual(segunda["ja_havia"], 3)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM articles"), 3)

    def test_os_autores_entram_na_ordem(self):
        ingest_autor.importar(self.db, self.achado, quem="Alexandro Andrade")
        autores = [linha["author_name"] for linha in self.db.dicts(
            "SELECT aa.author_name FROM article_authors aa JOIN articles a ON a.id = aa.article_id"
            " WHERE a.title LIKE 'Impact of the COVID%' ORDER BY aa.author_order")]
        self.assertEqual(autores[0], "Andrade, Alexandro")
        self.assertIn("Neiva, Henrique Pereira", autores)

    def test_o_resumo_vem_junto(self):
        # é ele que alimenta o reconhecimento de variáveis
        ingest_autor.importar(self.db, self.achado)
        notas = self.db.scalar("SELECT notes FROM articles WHERE title LIKE 'Impact%'")
        self.assertIn("mental health", notas)

    def test_as_variaveis_sao_reconhecidas_no_que_chegou(self):
        ingest_autor.importar(self.db, self.achado)
        variaveis.instalar(self.db)
        resultado = variaveis.marcar_artigos(self.db)
        self.assertEqual(resultado["com_variavel"], 3)
        codigos = {linha["code"] for linha in self.db.dicts(
            "SELECT v.code FROM article_variables av JOIN variables v ON v.id = av.variable_id")}
        self.assertIn("ansiedade", codigos)
        self.assertIn("fibromialgia", codigos)

    def test_nao_passa_por_cima_do_que_o_laboratorio_digitou(self):
        from lape import ingest_excel
        ingest_excel.ingest_articles(self.db, [
            {"title": "Impact of the COVID-19 pandemic on the psychological aspects and "
                      "mental health of elite soccer athletes: a systematic review.",
             "authors": "Quem digitou", "status": "Em produção",
             "journal": "Revista digitada à mão"}])
        ingest_autor.importar(self.db, self.achado)
        self.assertEqual(
            self.db.scalar("SELECT journal FROM articles WHERE title LIKE 'Impact%'"),
            "Revista digitada à mão")

    def test_artigo_sem_titulo_e_ignorado(self):
        vazio = {"termo": "t", "pmids": [], "registros": [{"title": None, "year": 2020}]}
        resultado = ingest_autor.importar(self.db, vazio)
        self.assertEqual(resultado["novos"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
