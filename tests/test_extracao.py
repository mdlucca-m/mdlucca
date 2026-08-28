#!/usr/bin/env python3
"""Testes da tabela de extracao: CSV modelo Scopus/WoS, BibTeX e RIS.

    python3 -m unittest tests.test_extracao -v

A extracao e o que sai do laboratorio para o mundo -- vai para o Zotero
de um orientando, para o relatorio da coordenacao, para o anexo de um
projeto. Por isso os testes olham duas coisas: se o formato e mesmo o
formato (um .ris que o EndNote nao le nao serve de nada) e se nenhuma
coluna vazia foi preenchida com suposicao.
"""
from __future__ import annotations

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

from lape import api, auth, export, ingest_excel  # noqa: E402
from lape.db import Database  # noqa: E402


ARTIGOS = [
    {"title": "Atenção plena e desempenho em atletas de base",
     "authors": "Marina Rossetto Cardoso; Alexandro Andrade",
     "status": "Publicado", "journal": "Journal of Sport Psychology",
     "year_published": 2024, "doi": "https://doi.org/10.1000/lape.2024.0001",
     "issn": "0123-4567", "language": "Inglês", "qualis": "A2",
     "scopus_citations": 7, "wos_citations": 5,
     "research_line": "Psicologia do Esporte", "study_type": "Ensaio clínico"},
    {"title": "Ansiedade competitiva: revisão sistemática",
     "authors": "Nathália Bregantin Costa",
     "status": "Submetido", "journal": "Revista Brasileira de Psicologia do Esporte",
     "first_submission_on": "2026-02-10"},
]


def banco_com_artigos(caminho: Path) -> Database:
    db = Database(caminho)
    db.migrate()
    ingest_excel.ingest_articles(db, ARTIGOS)
    # citacoes do OpenAlex nao vem da planilha e sim do rastreador: entram
    # aqui direto, para o teste da "melhor base" ter as tres para comparar
    db.execute("UPDATE articles SET openalex_citations = 9 WHERE scopus_citations = 7")
    db.conn.commit()
    return db


class TestConteudoDaExtracao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = banco_com_artigos(Path(self.tmp.name) / "e.sqlite")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_recorte_de_publicados(self):
        todos = export.linhas(self.db)
        publicados = export.linhas(self.db, apenas_publicados=True)
        self.assertEqual(len(todos), 2)
        self.assertEqual(len(publicados), 1)
        self.assertEqual(publicados[0]["status"], "publicado")

    def test_doi_sai_sem_o_prefixo_e_o_link_com_ele(self):
        # a coluna DOI das bases guarda o identificador puro; o link e derivado
        r = export.linhas(self.db, apenas_publicados=True)[0]
        self.assertEqual(r["doi"], "10.1000/lape.2024.0001")
        self.assertEqual(r["link"], "https://doi.org/10.1000/lape.2024.0001")

    def test_citacoes_usam_a_melhor_base(self):
        r = export.linhas(self.db, apenas_publicados=True)[0]
        self.assertEqual(r["citations"], 9)   # OpenAlex, a maior das tres

    def test_autores_no_formato_de_citacao(self):
        r = export.linhas(self.db, apenas_publicados=True)[0]
        self.assertEqual(r["authors_citacao"], "Cardoso M.R.; Andrade A.")
        self.assertIn("Marina Rossetto Cardoso", r["authors"])   # nome inteiro preservado

    def test_nada_e_inventado(self):
        # o artigo submetido nao tem revista indexada, DOI, ISSN nem citacao:
        # essas colunas tem de sair vazias, nunca com um valor plausivel
        submetido = [r for r in export.linhas(self.db) if r["status"] != "publicado"][0]
        for campo in ("doi", "link", "issn", "language", "qualis"):
            self.assertIn(submetido.get(campo), (None, ""), f"campo inventado: {campo}")
        self.assertEqual(submetido["citations"], 0)


class TestFormatoCSV(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = banco_com_artigos(Path(self.tmp.name) / "e.sqlite")
        self.texto = export.para_csv(export.linhas(self.db))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_abre_no_excel_em_portugues(self):
        # BOM e ponto e virgula: sem isso o Excel pt-BR joga tudo numa coluna
        # e come os acentos
        self.assertTrue(self.texto.startswith("﻿"))
        cabecalho = self.texto.splitlines()[0].lstrip("﻿")
        self.assertIn(";", cabecalho)
        self.assertNotIn("\t", cabecalho)

    def test_cabecalhos_do_modelo_scopus_e_wos(self):
        cabecalho = self.texto.splitlines()[0].lstrip("﻿").split(";")
        for esperado in ("Authors", "Author full names", "Title", "Year", "Source title",
                         "DOI", "Document Type", "Cited by", "EID", "UT (Unique WOS ID)"):
            self.assertIn(esperado, cabecalho)

    def test_uma_linha_por_artigo(self):
        # csv.reader porque um titulo com ponto e virgula quebraria a contagem
        import csv as _csv
        import io as _io
        linhas = list(_csv.reader(_io.StringIO(self.texto.lstrip("﻿")), delimiter=";"))
        self.assertEqual(len(linhas), 3)   # cabecalho + dois artigos
        self.assertEqual(len(linhas[1]), len(export.COLUNAS))


class TestFormatoBibTeX(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = banco_com_artigos(Path(self.tmp.name) / "e.sqlite")
        self.texto = export.para_bibtex(export.linhas(self.db))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_uma_entrada_por_artigo_com_chave_unica(self):
        chaves = re.findall(r"@article\{([^,]+),", self.texto)
        self.assertEqual(len(chaves), 2)
        self.assertEqual(len(set(chaves)), 2)

    def test_chaves_balanceadas(self):
        # um .bib com chave sobrando nao importa em lugar nenhum
        self.assertEqual(self.texto.count("{"), self.texto.count("}"))

    def test_autores_separados_por_and(self):
        self.assertIn("author = {Marina Rossetto Cardoso and Alexandro Andrade}", self.texto)

    def test_campo_vazio_nao_aparece(self):
        # o submetido nao tem DOI: nao pode sair `doi = {}`
        self.assertNotIn("= {}", self.texto)

    def test_o_que_nao_foi_publicado_vem_avisado(self):
        self.assertIn("note = {", self.texto)


class TestFormatoRIS(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = banco_com_artigos(Path(self.tmp.name) / "e.sqlite")
        self.texto = export.para_ris(export.linhas(self.db))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_abre_e_fecha_cada_registro(self):
        self.assertEqual(self.texto.count("TY  - JOUR"), 2)
        self.assertEqual(self.texto.count("ER  - "), 2)

    def test_toda_linha_tem_etiqueta_de_seis_colunas(self):
        # o RIS e posicional: `XX  - valor`. Uma linha fora do formato faz o
        # EndNote descartar o registro inteiro, sem avisar.
        for linha in self.texto.split("\r\n"):
            if not linha:
                continue
            self.assertRegex(linha, r"^[A-Z][A-Z0-9]  - ")

    def test_um_autor_por_linha(self):
        self.assertIn("AU  - Cardoso M.R.", self.texto)
        self.assertIn("AU  - Andrade A.", self.texto)


class TestFormatoDesconhecido(unittest.TestCase):
    def test_recusa_em_vez_de_devolver_csv_calado(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = banco_com_artigos(Path(tmp) / "e.sqlite")
            try:
                with self.assertRaises(ValueError):
                    export.extrair(db, "docx")
            finally:
                db.close()


class TestRotaDeExtracao(unittest.TestCase):
    """O download pelo painel: cabecalhos, permissao e formato."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "web.sqlite"
        db = banco_com_artigos(cls.db_path)
        auth.create_account(db, "Coordenação", "coord@udesc.br", "senhaforte123", role="admin")
        db.close()
        cls.publico = api.PUBLIC_DASHBOARD
        api.PUBLIC_DASHBOARD = False
        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *args, **kwargs: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        api.PUBLIC_DASHBOARD = cls.publico
        cls.tmp.cleanup()

    def setUp(self):
        self.cookie = self.entrar()

    def entrar(self):
        import json as _json
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=_json.dumps({"login": "coord@udesc.br", "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return resposta.headers.get("Set-Cookie", "").split(";")[0]

    def baixar(self, consulta, cookie=True):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/export/artigos?{consulta}")
        if cookie:
            pedido.add_header("Cookie", self.cookie)
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                return resposta.status, resposta.headers, resposta.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read().decode("utf-8")

    def test_sem_entrar_nao_baixa(self):
        status, _, _ = self.baixar("formato=csv", cookie=False)
        self.assertEqual(status, 401)

    def test_csv_vem_como_anexo(self):
        status, cabecalhos, corpo = self.baixar("formato=csv&publicados=1")
        self.assertEqual(status, 200)
        self.assertIn("text/csv", cabecalhos.get("Content-Type", ""))
        self.assertIn('attachment; filename="lape-producao-publicados.csv"',
                      cabecalhos.get("Content-Disposition", ""))
        self.assertIn("Atenção plena", corpo)
        self.assertNotIn("Ansiedade competitiva", corpo)   # nao publicado

    def test_bibtex_e_ris_tem_o_proprio_tipo(self):
        for consulta, mime, nome in (
            ("formato=bibtex", "application/x-bibtex", "lape-producao.bib"),
            ("formato=ris", "application/x-research-info-systems", "lape-producao.ris"),
        ):
            with self.subTest(consulta=consulta):
                status, cabecalhos, corpo = self.baixar(consulta)
                self.assertEqual(status, 200)
                self.assertIn(mime, cabecalhos.get("Content-Type", ""))
                self.assertIn(nome, cabecalhos.get("Content-Disposition", ""))
                self.assertTrue(corpo.strip())

    def test_formato_invalido_explica_o_que_serve(self):
        status, _, corpo = self.baixar("formato=xlsx")
        self.assertEqual(status, 400)
        for formato in export.FORMATOS:
            self.assertIn(formato, corpo)

    def test_a_planilha_do_laboratorio_baixa_como_xlsx(self):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/export/planilha")
        pedido.add_header("Cookie", self.cookie)
        with urllib.request.urlopen(pedido, timeout=60) as resposta:
            corpo = resposta.read()
            cabecalhos = resposta.headers
        self.assertIn("spreadsheetml", cabecalhos.get("Content-Type", ""))
        self.assertIn(".xlsx", cabecalhos.get("Content-Disposition", ""))
        # PK: todo .xlsx e um zip; um HTML de erro devolvido com 200 nao seria
        self.assertTrue(corpo.startswith(b"PK"), "não veio um arquivo do Excel")

    def test_a_planilha_tambem_pede_para_entrar(self):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/export/planilha")
        with self.assertRaises(urllib.error.HTTPError) as erro:
            urllib.request.urlopen(pedido, timeout=30)
        self.assertEqual(erro.exception.code, 401)

    def test_sem_formato_o_padrao_e_planilha(self):
        status, cabecalhos, _ = self.baixar("")
        self.assertEqual(status, 200)
        self.assertIn("text/csv", cabecalhos.get("Content-Type", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
