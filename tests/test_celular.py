#!/usr/bin/env python3
"""Testes do aplicativo de celular — o painel para MOSTRAR a alguém.

    python3 -m unittest tests.test_celular -v

Quem recebe este arquivo abre no celular, sem contexto nenhum, e decide
em trinta segundos se vale a pena. Os riscos são outros que os do painel:
título de artigo com `<` que quebra a página, um gráfico de uma coluna só
que vira um bloco azul, e um retrato sem data que envelhece calado.
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import celular, ingest_excel, variaveis  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = Database(Path(cls.tmp.name) / "t.sqlite")
        db.migrate()
        ingest_excel.ingest_articles(db, [
            {"title": "Treinamento resistido e ansiedade em fibromialgia",
             "status": "Publicado", "year_published": 2024,
             "doi": "10.1000/a.1", "journal": "Pain"},
            {"title": "Exercício & dor <crônica>: revisão",
             "status": "Submetido", "year_published": 2023},
            {"title": "Dropout no treinamento resistido",
             "status": "Publicado", "year_published": 2022},
        ])
        variaveis.instalar(db)
        variaveis.marcar_artigos(db)
        cls.pagina = celular.montar(db, quando=datetime(2026, 8, 28, 20, 15))
        db.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class TestFormaDeAplicativo(BaseApp):
    def test_a_navegacao_fica_embaixo(self):
        # no celular, coluna lateral vira tira de rolagem horizontal e o
        # polegar não alcança
        self.assertIn('<nav class="abas"', self.pagina)
        self.assertIn("position: fixed; left: 0; right: 0; bottom: 0", self.pagina)

    def test_cada_aba_e_uma_tela_inteira(self):
        for ident, _, _ in celular.ABAS:
            with self.subTest(aba=ident):
                self.assertIn(f'data-tela="{ident}"', self.pagina)
                self.assertIn(f'data-ir="{ident}"', self.pagina)

    def test_o_alvo_do_dedo_tem_tamanho_de_dedo(self):
        # botão de 30px é um botão que erra
        self.assertIn("min-height: 52px", self.pagina)

    def test_a_barra_respeita_o_recorte_do_aparelho(self):
        # sem isso a aba de baixo fica atrás da barra do iPhone
        self.assertIn("env(safe-area-inset-bottom)", self.pagina)
        self.assertIn("env(safe-area-inset-top)", self.pagina)

    def test_a_aba_ativa_nao_se_anuncia_so_pela_cor(self):
        self.assertIn('aria-selected', self.pagina)
        self.assertIn('role="tablist"', self.pagina)

    def test_quem_pediu_menos_movimento_recebe_menos(self):
        self.assertIn("prefers-reduced-motion", self.pagina)


class TestOQueAparece(BaseApp):
    def test_o_numero_vem_antes_da_explicacao(self):
        # a tela de abertura é o acervo em um número grande
        visao = self.pagina[self.pagina.index('data-tela="visao"'):]
        visao = visao[:visao.index('data-tela="temas"')]
        self.assertIn("grandao", visao)
        self.assertIn("artigos do laboratório", visao)

    def test_o_titulo_com_sinal_de_menor_nao_quebra_a_pagina(self):
        # "Exercício & dor <crônica>" é título de verdade, e sem escapar
        # ele fecha uma tag no meio da lista
        self.assertNotIn("dor <crônica>", self.pagina)
        self.assertIn("dor &lt;crônica&gt;", self.pagina)
        self.assertIn("&amp;", self.pagina)

    def test_o_artigo_com_doi_ganha_botao_e_o_sem_doi_nao(self):
        # link quebrado custa mais que a ausência dele
        self.assertIn("https://doi.org/10.1000/a.1", self.pagina)
        self.assertEqual(self.pagina.count('class="base"'), 1)

    def test_a_data_do_retrato_esta_na_tela(self):
        self.assertIn("28/08/2026", self.pagina)

    def test_a_pagina_admite_que_nao_esta_ao_vivo(self):
        sobre = self.pagina[self.pagina.index('data-tela="sobre"'):]
        self.assertIn("retrato", sobre.lower())
        self.assertIn("não grava", sobre)


class TestQuandoNaoHaCurva(unittest.TestCase):
    """Uma coluna sozinha ocupa a tela e parece defeito, não dado."""

    def monta(self, artigos):
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "t.sqlite")
        db.migrate()
        ingest_excel.ingest_articles(db, artigos)
        try:
            return celular.montar(db)
        finally:
            db.close()
            tmp.cleanup()

    def test_um_ano_so_vira_frase_e_nao_grafico(self):
        pagina = self.monta([
            {"title": f"Artigo {i}", "status": "Publicado", "year_published": 2026}
            for i in range(4)])
        self.assertIn("Toda a produção cadastrada está em um ano", pagina)
        self.assertNotIn('<ul class="colunas">', pagina)

    def test_com_anos_de_sobra_o_grafico_volta(self):
        pagina = self.monta([
            {"title": f"Artigo {ano}", "status": "Publicado", "year_published": ano}
            for ano in (2021, 2022, 2023, 2024)])
        self.assertIn('<ul class="colunas">', pagina)

    def test_banco_vazio_nao_quebra(self):
        pagina = self.monta([])
        self.assertIn('<nav class="abas"', pagina)
        self.assertIn("Nenhum artigo com ano de referência.", pagina)


class TestArquivoParaMandar(unittest.TestCase):
    def test_escreve_um_documento_que_abre_sozinho(self):
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "t.sqlite")
        db.migrate()
        destino = Path(tmp.name) / "sub" / "app.html"
        try:
            resultado = celular.escrever(db, destino)
        finally:
            db.close()
        texto = destino.read_text(encoding="utf-8")
        self.assertTrue(texto.startswith("<!doctype html>"))
        self.assertIn("viewport-fit=cover", texto)     # respeita o recorte da tela
        self.assertIn('name="theme-color"', texto)     # a barra do navegador acompanha
        self.assertIn("</html>", texto)
        self.assertGreater(resultado["bytes"], 10_000)
        tmp.cleanup()

    def test_cabe_num_anexo_de_e_mail(self):
        # o ponto deste arquivo é ser mandado; megabytes o inviabilizam
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "t.sqlite")
        db.migrate()
        ingest_excel.ingest_articles(db, [
            {"title": f"Artigo número {i}", "status": "Publicado",
             "year_published": 2020 + i % 6} for i in range(120)])
        destino = Path(tmp.name) / "app.html"
        try:
            resultado = celular.escrever(db, destino)
        finally:
            db.close()
        self.assertLess(resultado["bytes"], 900_000)
        tmp.cleanup()

    def test_o_nome_do_laboratorio_cabe_no_topo(self):
        self.assertEqual(
            celular._curto("LAPE - Laboratorio de Psicologia do Esporte"), "LAPE")
        self.assertEqual(celular._curto("Laboratório X"), "Laboratório X")
        self.assertEqual(celular._curto(None), "")

    def test_o_comando_esta_registrado(self):
        agente = (ROOT / "scripts" / "lape_agent.py").read_text(encoding="utf-8")
        self.assertIn('"app"', agente)
        self.assertIn("func=cmd_app", agente)
        self.assertTrue(re.search(r"def cmd_app", agente))


class TestOsIconesSaoOsDoSistema(BaseApp):
    def test_a_biblioteca_de_icones_viaja_junto(self):
        # sem ela os lugares ficam vazios e a tela perde metade da leitura
        self.assertIn("const Icons", self.pagina)
        self.assertIn('data-icone=', self.pagina)

    def test_todo_icone_pedido_existe_na_biblioteca(self):
        # ícone inexistente não dá erro: some, e ninguém percebe
        icones = (ROOT / "scripts" / "lape" / "templates" / "icons.js").read_text(
            encoding="utf-8")
        for nome in set(re.findall(r'data-icone="(\w+)"', self.pagina)):
            with self.subTest(icone=nome):
                self.assertRegex(icones, r"\n\s+" + nome + r":\s*\[")


if __name__ == "__main__":
    unittest.main(verbosity=2)
