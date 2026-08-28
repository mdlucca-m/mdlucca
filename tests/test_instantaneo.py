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


if __name__ == "__main__":
    unittest.main(verbosity=2)
