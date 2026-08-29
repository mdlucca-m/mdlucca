#!/usr/bin/env python3
"""Testes do instantâneo: o painel numa página só, sem servidor.

    python3 -m unittest tests.test_instantaneo -v

O perigo aqui é a página que abre bonita e mente. Um instantâneo sem data
parece o painel ao vivo; um botão de gravar que não grava parece defeito;
um link para /painel num arquivo solto dá na parede. Cada teste guarda
uma dessas.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_excel, instantaneo, variaveis  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseInstantaneo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = Database(Path(cls.tmp.name) / "t.sqlite")
        db.migrate()
        ingest_excel.ingest_articles(db, [
            {"title": "Treinamento resistido e ansiedade em fibromialgia",
             "authors": "Ana Souza", "status": "Publicado", "year_published": 2024,
             "doi": "10.1000/a.1"},
            {"title": "Dropout no treinamento resistido", "authors": "Beto Lima",
             "status": "Submetido", "first_submission_on": "2025-02-01"},
        ])
        variaveis.instalar(db)
        variaveis.marcar_artigos(db)
        cls.pagina = instantaneo.montar(db, quando=datetime(2026, 8, 28, 19, 30))
        db.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class TestOQueVaiDentro(BaseInstantaneo):
    def test_o_estilo_os_icones_e_os_graficos_vao_juntos(self):
        # nada pode depender de um arquivo ao lado: é uma página só
        for marcador in ("__BASE_CSS__", "__ICONS_JS__", "__CHARTS_JS__",
                         "__PANORAMA_JS__"):
            with self.subTest(marcador=marcador):
                self.assertNotIn(marcador, self.pagina)
        self.assertIn("const Charts", self.pagina)
        self.assertIn("const ABAS", self.pagina)

    def test_os_dados_ja_estao_na_pagina(self):
        self.assertIn("window.__LAPE__", self.pagina)
        bruto = self.pagina.split("window.__LAPE__ = ", 1)[1].split(";</script>", 1)[0]
        dados = json.loads(bruto)
        for chave in ("panorama", "artigos", "incidencia", "prevalencia",
                      "triangulacao", "projetos", "vocabulario"):
            with self.subTest(chave=chave):
                self.assertIn(chave, dados["painel"])
        self.assertEqual(len(dados["painel"]["artigos"]), 2)

    def test_a_tela_le_os_dados_de_dentro_e_nao_do_servidor(self):
        # senão ela abre vazia e não enche nunca
        self.assertIn("const dados = window.__LAPE__.painel;", self.pagina)
        self.assertNotIn('const dados = await api("/api/panorama");', self.pagina)

    def test_o_contorno_do_mundo_viaja_junto(self):
        bruto = self.pagina.split("window.__LAPE__ = ", 1)[1].split(";</script>", 1)[0]
        self.assertGreater(len(json.loads(bruto)["mundo"]["paises"]), 100)


class TestOQueAPaginaAdmite(BaseInstantaneo):
    def test_a_data_do_retrato_esta_escrita(self):
        # instantâneo sem data parece o painel ao vivo, e envelhece calado
        self.assertIn("28/08/2026", self.pagina)
        self.assertIn("instantâneo", self.pagina.lower())

    def test_o_selo_ao_vivo_nao_aparece(self):
        # num retrato ele só poderia mentir
        self.assertIn(".pulso { display: none !important; }", self.pagina)
        self.assertIn("let aoVivo = false;", self.pagina)

    def test_gravar_devolve_motivo_e_nao_silencio(self):
        # botão que não faz nada é pior que botão que explica
        self.assertIn("só o sistema no computador do laboratório grava", self.pagina)

    def test_nenhuma_porta_da_na_parede(self):
        # /painel, /triagem e /app não existem num arquivo solto
        for morto in ('href: "/painel"', 'href: "/triagem"', '"/app", "pessoa"'):
            with self.subTest(link=morto):
                self.assertNotIn(morto, self.pagina)

    def test_o_que_e_de_olhar_continua_inteiro(self):
        # o instantâneo tira o que grava, não o que se lê
        for aba in ("extracao", "triangulo", "funil", "mapa", "rede"):
            with self.subTest(aba=aba):
                self.assertIn('id: "' + aba + '"', self.pagina)


class TestArquivoCompleto(unittest.TestCase):
    def test_escreve_um_documento_que_abre_sozinho(self):
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "t.sqlite")
        db.migrate()
        destino = Path(tmp.name) / "sub" / "panorama.html"
        try:
            resultado = instantaneo.escrever(db, destino)
        finally:
            db.close()
        self.assertTrue(destino.exists())
        texto = destino.read_text(encoding="utf-8")
        self.assertTrue(texto.startswith("<!doctype html>"))
        self.assertIn('<meta name="viewport"', texto)   # abre no celular
        self.assertIn("</html>", texto)
        self.assertGreater(resultado["bytes"], 50_000)
        tmp.cleanup()

    def test_banco_vazio_nao_quebra_a_pagina(self):
        # laboratório novo, sem nada cadastrado: a página tem de abrir
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "t.sqlite")
        db.migrate()
        try:
            pagina = instantaneo.montar(db)
        finally:
            db.close()
        self.assertIn("window.__LAPE__", pagina)
        tmp.cleanup()

    def test_o_remendo_da_tela_ainda_encaixa(self):
        # se panorama.js mudar essas linhas, o instantâneo silenciosamente
        # volta a pedir dados ao servidor -- e abre vazio
        tela = (ROOT / "scripts" / "lape" / "templates" / "panorama.js").read_text(
            encoding="utf-8")
        self.assertIn('const dados = await api("/api/panorama");', tela)
        self.assertIn("let aoVivo = true;", tela)
        for trecho, _ in instantaneo.LINKS_MORTOS:
            with self.subTest(trecho=trecho[:40]):
                self.assertIn(trecho, tela)


class TestComandoDeLinha(unittest.TestCase):
    def test_o_comando_esta_registrado(self):
        agente = (ROOT / "scripts" / "lape_agent.py").read_text(encoding="utf-8")
        self.assertIn('"instantaneo"', agente)
        self.assertIn("func=cmd_instantaneo", agente)
        self.assertTrue(re.search(r"def cmd_instantaneo", agente))


class TestUmaFonteSo(unittest.TestCase):
    """O instantâneo e a rota servem o MESMO conteúdo.

    Enquanto eram dois dicionários montados à mão, toda análise nova
    entrava num e esquecia do outro: o raio-x analítico foi para a rota e
    nunca chegou ao arquivo que sai por e-mail. O cartão saía vazio, sem
    erro nenhum na tela.
    """

    def setUp(self):
        from lape import ingest_excel, variaveis
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        ingest_excel.ingest_articles(self.db, [
            {"title": "Exercício físico na fibromialgia", "status": "Publicado",
             "year_published": 2023, "doi": "10.1000/a.1"},
            {"title": "Ansiedade e treinamento resistido", "status": "Publicado",
             "year_published": 2024},
        ])
        variaveis.instalar(self.db)
        variaveis.marcar_artigos(self.db)

    def test_o_instantaneo_nao_remonta_o_painel_a_mao(self):
        fonte = (ROOT / "scripts" / "lape" / "instantaneo.py").read_text(encoding="utf-8")
        self.assertIn("payload_do_panorama", fonte)
        # o que caracterizava a copia: chamar cada analise de novo aqui
        for analise in ("analise.sintese(", "analise.lacunas(", "analise.raio_x(",
                        "analise.triangulacao("):
            with self.subTest(chamada=analise):
                self.assertNotIn(analise, fonte)

    def test_toda_analise_da_rota_chega_ao_arquivo(self):
        from lape import instantaneo
        from lape.api import payload_do_panorama

        embutido = instantaneo._dados(self.db)
        for chave in payload_do_panorama(self.db):
            with self.subTest(chave=chave):
                self.assertIn(chave, embutido)

    def test_o_raio_x_e_a_arvore_estao_no_arquivo(self):
        # as duas que faltavam, nomeadas: um teste generico passa mesmo
        # quando as duas somem juntas da rota
        from lape import instantaneo
        embutido = instantaneo._dados(self.db)
        self.assertIn("medidas", embutido["raio_x"])
        self.assertIn("raiz", embutido["dendrograma"])

    def test_o_arquivo_continua_sendo_de_leitura(self):
        # a fonte comum nao pode trazer papel de quem grava para dentro
        # de um retrato que nao grava nada
        from lape import instantaneo
        embutido = instantaneo._dados(self.db)
        self.assertEqual(embutido["usuario"]["papel"], "leitura")

if __name__ == "__main__":
    unittest.main(verbosity=2)
