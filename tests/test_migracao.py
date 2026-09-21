#!/usr/bin/env python3
"""A migracao roda com o LAPE no ar? -- e o que fazer quando nao roda.

    python3 -m unittest tests.test_migracao -v

`python scripts/lape_agent.py curador` morria com um traceback de
"database is locked" sempre que o sistema estivesse de pe E escrevendo.
A saida era desligar o laboratorio para rodar o curador -- o que ninguem
faz no meio do dia, entao o curador simplesmente deixava de rodar.

A causa, medida: `DROP VIEW` e a UNICA operacao da migracao que precisa da
trava exclusiva do banco. O `executescript` inteiro passa com o servidor
gravando, porque e tudo `CREATE ... IF NOT EXISTS`. E a migracao derrubava
TODAS as views a cada execucao, mudassem elas ou nao.

Dois testes guardam as duas metades: a migracao comum nao derruba nada e
convive com o sistema no ar; e a migracao que PRECISA derrubar, quando nao
consegue, diz o que fazer em vez de despejar uma pilha de chamada.
"""
from __future__ import annotations

import contextlib
import io
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest.mock
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape.db import BancoOcupado, Database, _so_o_essencial  # noqa: E402


class BaseDoBancoMigrado(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.caminho = Path(tmp.name) / "m.sqlite"
        db = Database(self.caminho)
        db.migrate()
        db.close()

    def escrita_aberta(self):
        """Um "servidor" com transacao de escrita aberta, como o LAPE no ar."""
        servidor = sqlite3.connect(self.caminho, timeout=1)
        servidor.execute("PRAGMA journal_mode = WAL")
        servidor.execute("BEGIN IMMEDIATE")
        servidor.execute("INSERT INTO articles (title, title_key) VALUES ('x','x')")
        self.addCleanup(servidor.close)
        self.addCleanup(servidor.rollback)
        return servidor

    def migrar(self, espera_ms=1500):
        db = Database(self.caminho)
        self.addCleanup(db.close)
        db.conn.execute(f"PRAGMA busy_timeout = {espera_ms}")
        db.migrate()
        return db


class TestAMigracaoComOSistemaNoAr(BaseDoBancoMigrado):

    def test_nada_mudou_entao_roda_com_o_sistema_gravando(self):
        """O caso de todo dia -- e o que estava quebrado."""
        self.escrita_aberta()
        self.migrar()          # nao levanta

    def test_nada_mudou_entao_nenhuma_view_e_derrubada(self):
        """O DROP e o que pede a trava; nao pedir e o conserto.

        Testar so "rodou" deixaria passar uma implementacao que derruba e
        recria rapido o bastante para caber na espera -- e que voltaria a
        falhar num dia de escrita mais longa.
        """
        # `set_trace_callback` ve TODA instrucao que a conexao executa --
        # inclusive as de dentro do `executescript`. Trocar o `execute` por
        # um espiao nao da: em sqlite3 ele e somente leitura.
        executadas = []
        db = Database(self.caminho)
        self.addCleanup(db.close)
        db.conn.set_trace_callback(executadas.append)
        db.migrate()
        db.conn.set_trace_callback(None)
        derrubadas = [x for x in executadas
                      if x.strip().upper().startswith("DROP VIEW")]
        self.assertEqual(derrubadas, [])
        # e a prova de que o espiao estava vendo algo
        self.assertTrue(executadas)

    def test_view_que_mudou_e_derrubada_e_recriada(self):
        """Sem isso, a view velha esconde coluna nova em silencio."""
        c = sqlite3.connect(self.caminho)
        c.execute("DROP VIEW v_publications_by_year")
        c.execute("CREATE VIEW v_publications_by_year AS SELECT 1 AS diferente")
        c.commit()
        c.close()
        self.migrar()
        c = sqlite3.connect(self.caminho)
        sql = c.execute("SELECT sql FROM sqlite_master WHERE name = ?",
                        ("v_publications_by_year",)).fetchone()[0]
        c.close()
        self.assertNotIn("diferente", sql)

    def test_view_que_saiu_do_esquema_tambem_cai(self):
        c = sqlite3.connect(self.caminho)
        c.execute("CREATE VIEW v_inventada AS SELECT 1 AS x")
        c.commit()
        c.close()
        self.migrar()
        c = sqlite3.connect(self.caminho)
        resta = c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name = ?",
                          ("v_inventada",)).fetchone()[0]
        c.close()
        self.assertEqual(resta, 0)

    def test_a_espera_pelo_banco_e_maior_que_o_padrao(self):
        """Cinco segundos e o padrao do sqlite3, e e pouco para este uso."""
        db = Database(self.caminho)
        self.addCleanup(db.close)
        self.assertGreaterEqual(
            int(db.conn.execute("PRAGMA busy_timeout").fetchone()[0]), 30000)


class TestORecadoQuandoNaoDa(BaseDoBancoMigrado):

    def test_diz_o_que_fazer_em_vez_de_database_is_locked(self):
        """A mensagem crua nao diz a quem perguntar. Esta diz."""
        c = sqlite3.connect(self.caminho)
        c.execute("DROP VIEW v_publications_by_year")
        c.execute("CREATE VIEW v_publications_by_year AS SELECT 1 AS diferente")
        c.commit()
        c.close()
        self.escrita_aberta()
        with self.assertRaises(BancoOcupado) as caso:
            self.migrar(espera_ms=800)
        recado = str(caso.exception)
        self.assertIn("feche a janela preta", recado)
        self.assertIn("suba o LAPE de novo", recado)

    def test_outro_erro_de_banco_nao_e_disfarcado(self):
        """So "locked" vira recado; o resto sobe como veio."""
        db = Database(self.caminho)
        self.addCleanup(db.close)
        db.conn.execute("PRAGMA query_only = ON")
        c = sqlite3.connect(self.caminho)
        c.execute("DROP VIEW v_publications_by_year")
        c.execute("CREATE VIEW v_publications_by_year AS SELECT 1 AS diferente")
        c.commit()
        c.close()
        with self.assertRaises(sqlite3.OperationalError) as caso:
            db.migrate()
        self.assertNotIsInstance(caso.exception, BancoOcupado)

    def test_a_linha_de_comando_nao_despeja_pilha_de_chamada(self):
        """Quem roda isto nao le traceback -- le a primeira linha."""
        fonte = (ROOT / "scripts" / "lape_agent.py").read_text(encoding="utf-8")
        trecho = fonte[fonte.index("def main()"):]
        self.assertIn("except BancoOcupado", trecho)
        self.assertIn("return 1", trecho)


class TestOBancoTravadoNaLinhaDeComando(unittest.TestCase):
    """A janela preta também não pode responder com rastreio de pilha.

    O `BancoOcupado` cobre o momento de trocar as views. A trava aparece
    também numa gravação comum -- foi o que aconteceu com
    `biblioteca --atualizar`, que morreu com vinte linhas de rastreio
    terminando em "database is locked". Rastreio de pilha não diz a
    ninguém o que fazer.
    """

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.caminho = Path(tmp.name) / "trava.sqlite"
        Database(self.caminho).migrate()

    def _rodar(self, explodir):
        import lape_agent

        args = lape_agent.build_parser().parse_args(["--db", str(self.caminho), "status"])
        args.func = lambda _args: explodir()
        with contextlib.redirect_stdout(io.StringIO()) as saida:
            with unittest.mock.patch.object(lape_agent, "build_parser",
                                            return_value=_ParserFixo(args)):
                codigo = lape_agent.main()
        return codigo, saida.getvalue()

    def test_o_banco_travado_vira_recado_e_nao_rastreio(self):
        def explodir():
            raise sqlite3.OperationalError("database is locked")

        codigo, saida = self._rodar(explodir)
        self.assertEqual(codigo, 1)
        self.assertIn("ocupado", saida.lower())
        self.assertNotIn("Traceback", saida)

    def test_o_recado_diz_quem_costuma_estar_segurando(self):
        def explodir():
            raise sqlite3.OperationalError("database is locked")

        _, saida = self._rodar(explodir)
        self.assertIn("LAPE", saida)
        self.assertIn("biblioteca", saida.lower())

    def test_outro_erro_de_banco_continua_subindo(self):
        """Engolir tudo esconderia defeito de verdade.

        "no such column" é bug, e bug tem de aparecer inteiro -- com o
        rastreio, que é o que diz onde consertar.
        """
        def explodir():
            raise sqlite3.OperationalError("no such column: inventada")

        with self.assertRaises(sqlite3.OperationalError):
            self._rodar(explodir)


class _ParserFixo:
    """Devolve os argumentos já montados, sem reler a linha de comando."""

    def __init__(self, args):
        self._args = args

    def parse_args(self):
        return self._args


class TestAComparacaoDeDefinicao(unittest.TestCase):
    """Comparar texto cru acusaria diferenca em toda reindentacao."""

    def test_espaco_e_if_not_exists_nao_contam(self):
        guardada = "CREATE VIEW v AS\n  SELECT 1 AS x;"
        declarada = "CREATE VIEW IF NOT EXISTS v AS SELECT 1   AS x"
        self.assertEqual(_so_o_essencial(guardada), _so_o_essencial(declarada))

    def test_mudanca_de_verdade_conta(self):
        self.assertNotEqual(
            _so_o_essencial("CREATE VIEW v AS SELECT 1 AS x"),
            _so_o_essencial("CREATE VIEW v AS SELECT 2 AS x"))

    def test_nulo_nao_estoura(self):
        self.assertEqual(_so_o_essencial(None), "")

    def test_view_que_nao_da_para_recortar_e_derrubada(self):
        """O padrao seguro e o comportamento antigo.

        View com definicao velha esconde coluna nova e o painel mostra
        dado errado em silencio -- pior do que um comando que espera.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        esquema = Path(tmp.name) / "e.sql"
        esquema.write_text(
            "CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY);\n"
            "CREATE VIEW IF NOT EXISTS v_ok AS SELECT id FROM t;\n",
            encoding="utf-8")
        banco = Path(tmp.name) / "b.sqlite"
        db = Database(banco)
        self.addCleanup(db.close)
        db.migrate(esquema)
        declaradas = db._views_declaradas(esquema)
        self.assertIn("v_ok", declaradas)
        # uma view que o esquema nao declara nao esta no dicionario, e por
        # isso quem chama a derruba
        self.assertNotIn("v_nao_declarada", declaradas)


if __name__ == "__main__":
    unittest.main()
