#!/usr/bin/env python3
"""As linhas antigas que voltavam, e o fundir que as resolve.

    python3 -m unittest tests.test_linhas_fundidas -v

O defeito tinha duas metades. A planilha antiga ainda traz "Psicologia do
Esporte e do Exercício", "Saúde Mental e Exercício Físico" e "Dor Crônica e
Fibromialgia"; a coordenação encerrou as três na tela, e a cada rodada do
curador elas voltavam ao seletor de artigo -- porque a reimportação
escrevia `active = 1` quando a célula estava vazia. E mesmo encerradas,
os artigos que apontavam para elas ficavam pendurados lá: o mural mostrava
"Dor Crônica e Fibromialgia" com 6 artigos ao lado de "Fibromialgia e
doenças reumáticas" com 21 -- duas colunas para uma linha.

Fundir leva os artigos junto e encerra a antiga. Nada é apagado.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth, ingest_excel, linhas, metrics  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


def _linha(db: Database, code: str, nome: str, active: int = 1) -> int:
    return db.upsert("research_lines", {"code": code, "name": nome, "active": active},
                     conflict=("code",))


def _artigo(db: Database, titulo: str, linha: int, status: str = "publicado") -> int:
    return db.upsert("articles", {"title": titulo, "title_key": titulo.lower(),
                                  "status": status, "research_line_id": linha},
                     conflict=("title_key",))


class BaseComDuasLinhas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "l.sqlite")
        self.db.migrate()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)
        self.antiga = _linha(self.db, "dor_cronica", "Dor Crônica e Fibromialgia")
        self.nova = _linha(self.db, "exercicio_fibromialgia", "Fibromialgia e doenças reumáticas")
        self.db.conn.commit()

    def ativa(self, linha_id):
        return int(self.db.scalar("SELECT active FROM research_lines WHERE id = ?", (linha_id,)))


class TestAReimportacaoNaoReativa(BaseComDuasLinhas):
    """A célula vazia da planilha não é uma opinião sobre a linha."""

    def test_linha_encerrada_continua_encerrada_quando_a_planilha_nao_diz(self):
        self.db.execute("UPDATE research_lines SET active = 0 WHERE id = ?", (self.antiga,))
        self.db.conn.commit()
        ingest_excel.ingest_research_lines(self.db, [
            {"code": "dor_cronica", "name": "Dor Crônica e Fibromialgia", "active": None},
            {"code": "dor_cronica", "name": "Dor Crônica e Fibromialgia", "active": ""},
        ])
        self.db.conn.commit()
        self.assertEqual(self.ativa(self.antiga), 0)
        # e nao criou uma segunda "Dor Cronica" para contornar a encerrada
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM research_lines"), 2)

    def test_a_planilha_que_diz_sim_reativa(self):
        self.db.execute("UPDATE research_lines SET active = 0 WHERE id = ?", (self.antiga,))
        self.db.conn.commit()
        ingest_excel.ingest_research_lines(self.db, [
            {"code": "dor_cronica", "name": "Dor Crônica e Fibromialgia", "active": "sim"}])
        self.db.conn.commit()
        self.assertEqual(self.ativa(self.antiga), 1)

    def test_a_planilha_que_diz_nao_encerra(self):
        ingest_excel.ingest_research_lines(self.db, [
            {"code": "dor_cronica", "name": "Dor Crônica e Fibromialgia", "active": "não"}])
        self.db.conn.commit()
        self.assertEqual(self.ativa(self.antiga), 0)

    def test_linha_nova_nasce_ativa(self):
        ingest_excel.ingest_research_lines(self.db, [{"name": "Qualidade do ar"}])
        self.db.conn.commit()
        nova = self.db.scalar("SELECT active FROM research_lines WHERE name = 'Qualidade do ar'")
        self.assertEqual(int(nova), 1)


class TestFundir(BaseComDuasLinhas):

    def test_tudo_o_que_apontava_passa_e_a_antiga_sai_das_opcoes(self):
        for i in range(6):
            _artigo(self.db, f"artigo {i}", self.antiga)
        pessoa = self.db.member_id("Ana Souza")
        self.db.execute("UPDATE members SET research_line_id = ? WHERE id = ?", (self.antiga, pessoa))
        self.db.execute("INSERT INTO projects (code, name, research_line_id) VALUES ('p1', 'Projeto', ?)",
                        (self.antiga,))
        self.db.execute("INSERT INTO events (kind, title, start_at, research_line_id)"
                        " VALUES ('reuniao', 'Reunião', '2026-01-01', ?)", (self.antiga,))
        self.db.conn.commit()
        saida = linhas.fundir(self.db, self.antiga, self.nova)
        self.assertEqual(saida["movidos"]["Artigos"], 6)
        self.assertEqual(saida["movidos"]["Pessoas"], 1)
        self.assertEqual(saida["movidos"]["Projetos"], 1)
        self.assertEqual(saida["movidos"]["Atividades"], 1)
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM articles WHERE research_line_id = ?", (self.nova,)), 6)
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM articles WHERE research_line_id = ?", (self.antiga,)), 0)
        self.assertEqual(self.ativa(self.antiga), 0)
        self.assertEqual(self.ativa(self.nova), 1)

    def test_nada_e_apagado(self):
        """A antiga fica, inativa, com o nome que tinha: é por ela que se
        sabe de onde os artigos vieram."""
        linhas.fundir(self.db, self.antiga, self.nova)
        nome = self.db.scalar("SELECT name FROM research_lines WHERE id = ?", (self.antiga,))
        self.assertEqual(nome, "Dor Crônica e Fibromialgia")

    def test_aceita_id_codigo_ou_nome_sem_caixa_e_sem_acento(self):
        _artigo(self.db, "a", self.antiga)
        saida = linhas.fundir(self.db, "dor cronica e fibromialgia", "EXERCICIO_FIBROMIALGIA")
        self.assertEqual(saida["de"]["id"], self.antiga)
        self.assertEqual(saida["para"]["id"], self.nova)

    def test_a_mesma_linha_dos_dois_lados_e_recusada(self):
        with self.assertRaises(ValueError):
            linhas.fundir(self.db, self.antiga, self.antiga)

    def test_linha_que_nao_existe_e_recusada_antes_de_mexer(self):
        _artigo(self.db, "a", self.antiga)
        with self.assertRaises(ValueError):
            linhas.fundir(self.db, self.antiga, "linha que não há")
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM articles WHERE research_line_id = ?", (self.antiga,)), 1)
        self.assertEqual(self.ativa(self.antiga), 1)

    def test_o_mural_e_o_painel_veem_uma_linha_so_depois(self):
        """O sintoma da parede: duas colunas para uma linha."""
        for i in range(6):
            _artigo(self.db, f"velho {i}", self.antiga)
        for i in range(21):
            _artigo(self.db, f"novo {i}", self.nova)
        self.db.conn.commit()
        antes = {l["name"]: l["n_articles"] for l in metrics.research_lines(self.db)}
        self.assertEqual(antes["Dor Crônica e Fibromialgia"], 6)
        linhas.fundir(self.db, self.antiga, self.nova)
        depois = {l["name"]: (l["n_articles"], l["active"]) for l in metrics.research_lines(self.db)}
        self.assertEqual(depois["Fibromialgia e doenças reumáticas"], (27, 1))
        self.assertEqual(depois["Dor Crônica e Fibromialgia"], (0, 0))

    def test_o_payload_leva_o_icone_da_linha(self):
        """O mural desenha cada linha com o seu ícone, sem calcular nada lá."""
        icones = {l["code"]: l["icone"] for l in metrics.research_lines(self.db)}
        self.assertEqual(icones["exercicio_fibromialgia"], linhas.icone_de("exercicio_fibromialgia", None))
        self.assertEqual(icones["dor_cronica"], "linha")


class TestPelaLinhaDeComando(BaseComDuasLinhas):

    def test_lista_e_funde(self):
        _artigo(self.db, "a", self.antiga)
        self.db.conn.commit()
        caminho = Path(self.tmp.name) / "l.sqlite"
        sys.path.insert(0, str(ROOT / "scripts"))
        import lape_agent
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = lape_agent.cmd_linhas(argparse.Namespace(db=caminho, fundir=None, em=None))
        self.assertEqual(codigo, 0)
        self.assertIn("Dor Crônica e Fibromialgia", saida.getvalue())
        with redirect_stdout(saida):
            codigo = lape_agent.cmd_linhas(argparse.Namespace(
                db=caminho, fundir="Dor Crônica e Fibromialgia", em="Fibromialgia e doenças reumáticas"))
        self.assertEqual(codigo, 0)
        self.assertIn("fundida em", saida.getvalue())
        self.assertIn("nada foi apagado", saida.getvalue())
        self.assertEqual(self.ativa(self.antiga), 0)

    def test_fundir_sem_dizer_em_qual_nao_mexe(self):
        import lape_agent
        with redirect_stdout(io.StringIO()):
            codigo = lape_agent.cmd_linhas(argparse.Namespace(
                db=Path(self.tmp.name) / "l.sqlite", fundir="Dor Crônica e Fibromialgia", em=None))
        self.assertEqual(codigo, 2)
        self.assertEqual(self.ativa(self.antiga), 1)


class TestFundirPelaRede(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "r.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Alexandro Andrade", "coord@udesc.br", "senhaforte123",
                            role="coordenacao")
        auth.create_account(db, "Loiane", "loiane@udesc.br", "senhaforte123", role="integrante")
        cls.antiga = _linha(db, "dor_cronica", "Dor Crônica e Fibromialgia")
        cls.nova = _linha(db, "exercicio_fibromialgia", "Fibromialgia e doenças reumáticas")
        _artigo(db, "a", cls.antiga)
        db.conn.commit()
        db.close()
        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *a, **k: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def entrar(self, login):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"login": login, "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return (r.headers.get("Set-Cookie") or "").split(";")[0]

    def fundir(self, cookie, corpo):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/linhas/fundir",
            data=json.dumps(corpo).encode(),
            headers={"Content-Type": "application/json", "Cookie": cookie}, method="POST")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"{}")

    def test_o_integrante_nao_funde(self):
        status, _ = self.fundir(self.entrar("loiane@udesc.br"), {"de": self.antiga, "para": self.nova})
        self.assertEqual(status, 403)

    def test_a_mesma_linha_e_400_e_nao_500(self):
        status, corpo = self.fundir(self.entrar("coord@udesc.br"), {"de": self.antiga, "para": self.antiga})
        self.assertEqual(status, 400)
        self.assertIn("mesma", corpo["error"])

    def test_a_coordenacao_funde_e_o_registro_fica(self):
        status, corpo = self.fundir(self.entrar("coord@udesc.br"), {"de": self.antiga, "para": self.nova})
        self.assertEqual(status, 200)
        self.assertEqual(corpo["movidos"]["Artigos"], 1)
        db = Database(self.db_path)
        try:
            self.assertEqual(db.scalar("SELECT active FROM research_lines WHERE id = ?", (self.antiga,)), 0)
            self.assertTrue(db.scalar("SELECT COUNT(*) FROM audit_log WHERE action = 'linha_fundida'"))
        finally:
            db.close()


class TestATelaDasLinhas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        cls.mural_js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        cls.mural_html = (TEMPLATES / "mural.html").read_text(encoding="utf-8")

    def test_o_fundir_pede_confirmacao_e_so_oferece_destino_ativo(self):
        trecho = self.html[self.html.index("painel: async function (casa)"):]
        trecho = trecho[:trecho.index("formTitle: \"Nova linha de pesquisa\"")]
        self.assertIn('api("/api/linhas/fundir", "POST"', trecho)
        self.assertIn("confirm(", trecho)
        self.assertIn("linhas.filter(function (l){ return l.active; })", trecho)

    def test_o_seletor_de_artigo_so_traz_linha_ativa(self):
        self.assertIn("CACHE.lines = lines.items.filter(function (l){", self.html)

    def test_o_mural_desenha_faixas_com_todas_as_linhas_ativas(self):
        """Duas colunas magras num quadro do tamanho da parede não são um gráfico."""
        self.assertIn("function faixasPorLinha", self.mural_js)
        self.assertIn("return x.ativa || x.total > 0;", self.mural_js)
        self.assertIn("Icons.badge(x.icone", self.mural_js)
        self.assertNotIn('mode: "empilhado", fill: true, height: 520, caption: "produção por linha de pesquisa"',
                         self.mural_js)

    def test_o_cabecalho_da_tabela_nao_cobre_o_primeiro_nome(self):
        """O "bugzinho": a folha geral prende o cabeçalho no topo, e no mural
        sem rolagem ele passava por cima do primeiro integrante."""
        self.assertIn(".quadro .placar th { position: static; }", self.mural_html)
        self.assertIn("window.innerHeight", self.mural_js[self.mural_js.index("function slideDestaques"):])


if __name__ == "__main__":
    unittest.main()
