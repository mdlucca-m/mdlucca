#!/usr/bin/env python3
"""Testes do painel analítico: rota, exportação e a página.

    python3 -m unittest tests.test_panorama -v

O perigo aqui é o painel bonito que mente. Um gráfico que recebe o campo
com o nome errado não dá erro — ele desenha vazio, e ninguém percebe que
a rede temática está sem uma única linha. Foi o que aconteceu.
"""
from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth, ingest_excel, variaveis  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class BasePanorama(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "t.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        ingest_excel.ingest_articles(db, [
            {"title": "Treinamento resistido e ansiedade em fibromialgia",
             "authors": "Ana Souza; Beto Lima", "status": "Publicado",
             "year_published": 2024, "journal": "Pain", "doi": "10.1000/a.1"},
            {"title": "Dropout no treinamento resistido", "authors": "Ana Souza",
             "status": "Submetido", "first_submission_on": "2025-02-01"},
            {"title": "Um título sem variável nenhuma do vocabulário",
             "authors": "Beto Lima", "status": "Em produção", "started_on": "2023-05-01"},
        ])
        auth.create_account(db, "Ana Souza", "ana@udesc.br", "senhaforte123", role="admin")
        auth.create_account(db, "Curioso Silva", "curioso@udesc.br", "senhaforte123",
                            role="leitura")
        variaveis.instalar(db)
        variaveis.marcar_artigos(db)
        db.close()
        cls.publico = api.PUBLIC_DASHBOARD
        api.PUBLIC_DASHBOARD = False
        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *a, **k: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        api.PUBLIC_DASHBOARD = cls.publico
        cls.tmp.cleanup()

    def entrar(self, login):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"login": login, "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return r.headers.get("Set-Cookie", "").split(";")[0]

    def buscar(self, caminho, cookie=None, cru=False):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}{caminho}")
        if cookie:
            pedido.add_header("Cookie", cookie)
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                bruto = r.read()
                return r.status, r.headers, (bruto if cru else json.loads(bruto or b"{}"))
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, {}


class TestRotaDoPanorama(BasePanorama):
    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")
        self.curioso = self.entrar("curioso@udesc.br")

    def test_sem_entrar_nao_ve(self):
        self.assertEqual(self.buscar("/api/panorama")[0], 401)

    def test_quem_so_le_ve(self):
        # o panorama da produção é do laboratório inteiro
        self.assertEqual(self.buscar("/api/panorama", self.curioso)[0], 200)

    def test_traz_tudo_o_que_a_tela_precisa(self):
        _, _, dados = self.buscar("/api/panorama", self.ana)
        for chave in ("panorama", "sintese", "lacunas", "artigos", "linhas",
                      "laboratorio", "vocabulario"):
            self.assertIn(chave, dados)
        self.assertEqual(len(dados["artigos"]), 3)

    def test_cada_artigo_chega_com_as_suas_variaveis(self):
        _, _, dados = self.buscar("/api/panorama", self.ana)
        com_var = [a for a in dados["artigos"] if a["variaveis"]]
        self.assertEqual(len(com_var), 2)
        codigos = {v["code"] for v in com_var[0]["variaveis"]}
        self.assertTrue(codigos)

    def test_a_janela_pode_ser_apertada_pela_consulta(self):
        _, _, dados = self.buscar("/api/panorama?desde=2023&ate=2025", self.ana)
        self.assertEqual(dados["panorama"]["janela"]["anos"], [2023, 2024, 2025])

    def test_a_sintese_nao_afirma_tendencia_sem_serie(self):
        # três artigos em três anos diferentes, mas cada variável aparece
        # em poucos: nada aqui pode virar "subindo" com confiança
        _, _, dados = self.buscar("/api/panorama", self.ana)
        for v in dados["panorama"]["variaveis"]:
            if not v["confiavel"]:
                self.assertEqual(v["tendencia"], "sem série suficiente")
                self.assertIsNotNone(v["porque"])


class TestExportacaoDaExtracao(BasePanorama):
    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")

    def test_o_csv_abre_no_excel_em_portugues(self):
        status, cab, corpo = self.buscar("/api/panorama/extracao.csv", self.ana, cru=True)
        self.assertEqual(status, 200)
        self.assertIn("text/csv", cab.get("Content-Type", ""))
        texto = corpo.decode("utf-8")
        self.assertTrue(texto.startswith("﻿"))
        cabecalho = texto.splitlines()[0].lstrip("﻿")
        self.assertIn("Variáveis", cabecalho)
        self.assertIn("Nº de variáveis", cabecalho)

    def test_o_csv_traz_as_variaveis_escritas(self):
        _, _, corpo = self.buscar("/api/panorama/extracao.csv", self.ana, cru=True)
        self.assertIn("Fibromialgia", corpo.decode("utf-8"))

    def test_o_xlsx_tem_as_duas_abas(self):
        # a segunda não é recorte por comodidade: é a tabela que responde
        # "como estes assuntos se relacionam", que a primeira não responde
        status, cab, corpo = self.buscar("/api/panorama/extracao.xlsx", self.ana, cru=True)
        self.assertEqual(status, 200)
        self.assertIn("spreadsheetml", cab.get("Content-Type", ""))
        self.assertTrue(corpo.startswith(b"PK"))
        from openpyxl import load_workbook
        livro = load_workbook(io.BytesIO(corpo))
        self.assertEqual(livro.sheetnames, ["Todos os artigos", "Mais de uma variável"])
        todos = livro["Todos os artigos"]
        multi = livro["Mais de uma variável"]
        self.assertEqual(todos.max_row - 1, 3)
        self.assertLess(multi.max_row, todos.max_row)

    def test_o_link_do_artigo_vira_link_na_planilha(self):
        _, _, corpo = self.buscar("/api/panorama/extracao.xlsx", self.ana, cru=True)
        from openpyxl import load_workbook
        aba = load_workbook(io.BytesIO(corpo))["Todos os artigos"]
        colunas = [c.value for c in aba[1]]
        coluna = colunas.index("Link") + 1
        links = [aba.cell(row=i, column=coluna).hyperlink
                 for i in range(2, aba.max_row + 1)]
        self.assertTrue(any(links), "nenhuma célula de link virou hyperlink")

    def test_sem_entrar_nao_baixa(self):
        self.assertEqual(self.buscar("/api/panorama/extracao.csv")[0], 401)


class TestPaginaDoPanorama(BasePanorama):
    def pagina(self):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}/panorama")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return r.read().decode("utf-8")

    def test_a_pagina_monta_inteira(self):
        html = self.pagina()
        for marcador in ("__BASE_CSS__", "__ICONS_JS__", "__CHARTS_JS__", "__PANORAMA_JS__"):
            self.assertNotIn(marcador, html, f"marcador não substituído: {marcador}")
        self.assertIn("const Charts", html)
        self.assertIn("const ABAS", html)

    def test_a_biblioteca_de_graficos_esta_ligada(self):
        # `C` não definido derrubava todo gráfico da tela, e a página
        # continuava de pé: cartões vazios, nenhum erro visível
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        self.assertIn("const C = Charts;", js)

    def test_a_rede_usa_o_campo_que_a_biblioteca_le(self):
        # com `value` em vez de `weight`, o cálculo de posição recebia
        # undefined, virava NaN, e a rede saía sem uma única linha
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        trecho = js[js.index("C.network({"):js.index("height: 440")]
        self.assertIn("weight:", trecho)
        self.assertNotIn("value:", trecho)

    def test_toda_aba_declarada_tem_funcao(self):
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        bloco = js[js.index("const ABAS = ["):js.index("];", js.index("const ABAS = ["))]
        ids = re.findall(r'id: "(\w+)"', bloco)
        self.assertGreaterEqual(len(ids), 8)
        despacho = js[js.index("({ visao: verVisao"):js.index("[ST.aba] || verVisao)")]
        for identificador in ids:
            with self.subTest(aba=identificador):
                self.assertIn(identificador + ":", despacho)

    def test_todo_icone_da_navegacao_existe(self):
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        icones = (TEMPLATES / "icons.js").read_text(encoding="utf-8")
        for nome in re.findall(r'icone: "(\w+)"', js):
            with self.subTest(icone=nome):
                self.assertIn(f"{nome}:", icones)

    def test_nenhum_token_de_tema_indefinido(self):
        tema = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
        definidos = set(re.findall(r"(--[a-z0-9-]+)\s*:", tema))
        pagina = (TEMPLATES / "panorama.html").read_text(encoding="utf-8")
        definidos |= set(re.findall(r"(--[a-z0-9-]+)\s*:", pagina))
        usados = set(re.findall(r"var\((--[a-z0-9-]+)", pagina))
        self.assertEqual(usados - definidos, set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
