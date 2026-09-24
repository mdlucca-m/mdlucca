#!/usr/bin/env python3
"""A rotina que roda sozinha, e a coorientação que inclui os pós-graduandos.

    python3 -m unittest tests.test_rotina -v

A pergunta veio pelo WhatsApp: "novos artigos publicados, adicionados no
Lattes do professor, são captados automaticamente? Ou vamos alimentando
manual?". Era manual: os botões existiam e ninguém os apertava sem uma
pessoa na frente da tela. O Lattes não tem API; a mesma produção está
na PubMed e na OpenAlex, e é de lá que a rotina traz.

O que se guarda aqui: cada passo roda quando VENCE (contado da última
rodada boa, gravada no banco, e não da subida do servidor); um passo que
falha vira registro e não derruba os outros; a tela vê o estado; só a
coordenação manda rodar; e o seletor de coorientador oferece mestrandos
e doutorandos.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth, ingest_autor, ingest_citations, linhas, mapping, rotina  # noqa: E402
from lape.agents import tracker  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


def _sem_rede(caso: unittest.TestCase, novos: int = 2, falhar: str | None = None):
    """Os cinco passos sem sair para a rede, com o que cada um devolveria."""
    def trazer_todos(db, desde=None):
        if falhar == "producao":
            return {"pessoas": [{"quem": "Alexandro Andrade", "erro": "rede caiu"}], "variaveis": 0}
        return {"pessoas": [{"quem": "Alexandro Andrade", "gravado": {"novos": novos, "ja_havia": 3}}],
                "variaveis": 0}

    def update_citations(db, limit=None, verbose=True):
        if falhar == "citacoes":
            raise ConnectionError("openalex fora do ar")
        return {"scopus": 0, "wos": 0, "openalex": 4, "consultados": 5, "erros": 0}

    def atualizar(db, code, **kw):
        if falhar == "acervos":
            raise ConnectionError("pubmed fora do ar")
        return {"novos": 1, "achados": 3}

    def discover(db, since_year=None, limit_per_author=60, verbose=True):
        if falhar == "descobrir":
            raise ConnectionError("openalex fora do ar")
        return {"authors": 2, "seen": 3, "new": novos, "errors": []}

    def profiles(db, verbose=True):
        if falhar == "perfis":
            raise ConnectionError("openalex fora do ar")
        return {"updated": novos, "errors": []}

    for alvo, nome, falso in ((ingest_autor, "trazer_todos", trazer_todos),
                              (ingest_citations, "update_citations", update_citations),
                              (tracker, "discover", discover),
                              (tracker, "profiles", profiles)):
        p = mock.patch.object(alvo, nome, falso)
        p.start()
        caso.addCleanup(p.stop)
    from lape import biblioteca
    p = mock.patch.object(biblioteca, "atualizar", atualizar)
    p.start()
    caso.addCleanup(p.stop)


class BaseDaRotina(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "r.sqlite")
        self.db.migrate()
        linhas.instalar(self.db)
        from lape import biblioteca
        biblioteca.instalar(self.db)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)

    def registros(self):
        return self.db.dicts("SELECT target, status, rows_written, message FROM ingest_log"
                             " WHERE source = 'rotina' ORDER BY id")


class TestOsPassosVencem(BaseDaRotina):

    def test_nunca_rodou_vence_tudo(self):
        self.assertEqual(rotina.vencidos(self.db),
                         ["producao", "citacoes", "acervos", "descobrir", "perfis"])

    def test_depois_de_rodar_nada_vence_ate_o_intervalo(self):
        _sem_rede(self)
        feitos = rotina.rodar_vencidos(self.db)
        self.assertEqual([f["status"] for f in feitos], ["ok", "ok", "ok", "ok", "ok"])
        self.assertEqual(rotina.vencidos(self.db), [])
        # um dia e um minuto depois, os diarios vencem e os semanais nao
        depois = datetime.now() + timedelta(hours=24, minutes=1)
        self.assertEqual(rotina.vencidos(self.db, depois), ["producao", "citacoes", "descobrir"])
        semana = datetime.now() + timedelta(days=7, minutes=1)
        self.assertEqual(rotina.vencidos(self.db, semana),
                         ["producao", "citacoes", "acervos", "descobrir", "perfis"])

    def test_o_intervalo_conta_da_ultima_rodada_boa_e_nao_da_subida(self):
        """Um computador que reinicia todo dia não pode reimportar tudo a
        cada subida; um que ficou um mês desligado roda assim que volta."""
        _sem_rede(self)
        rotina.rodar_passo(self.db, "producao")
        self.db.execute("UPDATE ingest_log SET run_at = ? WHERE source = 'rotina' AND target = 'producao'",
                        ((datetime.now() - timedelta(days=30)).isoformat(timespec="seconds"),))
        self.db.conn.commit()
        self.assertIn("producao", rotina.vencidos(self.db))

    def test_o_intervalo_pode_ser_ajustado_pelo_ambiente(self):
        _sem_rede(self)
        rotina.rodar_passo(self.db, "citacoes")
        with mock.patch.dict(os.environ, {"LAPE_ROTINA_CITACOES_H": "1"}):
            self.assertIn("citacoes", rotina.vencidos(self.db, datetime.now() + timedelta(hours=2)))
        with mock.patch.dict(os.environ, {"LAPE_ROTINA_CITACOES_H": "0"}):
            self.assertNotIn("citacoes", rotina.vencidos(self.db, datetime.now() + timedelta(days=400)))


class TestCadaPassoGravaOQueFez(BaseDaRotina):

    def test_a_producao_nova_e_registrada_e_avisa_o_painel(self):
        _sem_rede(self, novos=2)
        feito = rotina.rodar_passo(self.db, "producao")
        self.assertEqual(feito["status"], "ok")
        self.assertEqual(feito["n"], 2)
        r = self.registros()
        self.assertEqual((r[0]["target"], r[0]["status"], r[0]["rows_written"]), ("producao", "ok", 2))
        evento = self.db.scalar("SELECT event FROM change_log WHERE event = 'producao.importada'")
        self.assertEqual(evento, "producao.importada")

    def test_sem_nada_novo_nao_avisa_o_painel(self):
        _sem_rede(self, novos=0)
        rotina.rodar_passo(self.db, "producao")
        self.assertIsNone(self.db.scalar("SELECT event FROM change_log WHERE event = 'producao.importada'"))

    def test_o_passo_que_falha_vira_registro_e_nao_derruba_os_outros(self):
        _sem_rede(self, falhar="citacoes")
        feitos = rotina.rodar_vencidos(self.db)
        self.assertEqual([f["status"] for f in feitos], ["ok", "erro", "ok", "ok", "ok"])
        erro = next(r for r in self.registros() if r["target"] == "citacoes")
        self.assertEqual(erro["status"], "erro")
        self.assertIn("openalex fora do ar", erro["message"])
        # o passo com erro continua vencido: tenta de novo na proxima checagem
        self.assertEqual(rotina.vencidos(self.db), ["citacoes"])

    def test_a_producao_com_todo_mundo_em_erro_e_erro(self):
        _sem_rede(self, falhar="producao")
        feito = rotina.rodar_passo(self.db, "producao")
        self.assertEqual(feito["status"], "erro")
        self.assertIn("rede caiu", feito["mensagem"])

    def test_os_acervos_rodam_todos_mesmo_com_um_em_erro(self):
        _sem_rede(self)
        from lape import biblioteca
        chamados = []
        original = biblioteca.atualizar

        def um_falha(db, code, **kw):
            chamados.append(code)
            if len(chamados) == 1:
                raise ConnectionError("a primeira cai")
            return original(db, code, **kw)
        with mock.patch.object(biblioteca, "atualizar", um_falha):
            feito = rotina.rodar_passo(self.db, "acervos")
        self.assertEqual(feito["status"], "ok")
        self.assertEqual(len(chamados), len(biblioteca.BIBLIOTECAS))
        self.assertIn("a primeira cai", feito["mensagem"])

    def test_passo_desconhecido_e_recusado(self):
        with self.assertRaises(ValueError):
            rotina.rodar_passo(self.db, "lattes")


class TestASituacaoParaATela(BaseDaRotina):

    def test_diz_cada_passo_quando_rodou_e_quando_volta(self):
        _sem_rede(self)
        rotina.rodar_passo(self.db, "producao")
        s = rotina.situacao(self.db)
        self.assertTrue(s["ligada"])
        por = {p["passo"]: p for p in s["passos"]}
        self.assertEqual(por["producao"]["status"], "ok")
        self.assertEqual(por["producao"]["trouxe"], 2)
        self.assertIsNotNone(por["producao"]["proxima"])
        self.assertFalse(por["producao"]["vencido"])
        self.assertEqual(por["citacoes"]["status"], "nunca rodou")
        self.assertTrue(por["citacoes"]["vencido"])

    def test_desligada_pelo_ambiente_nao_agenda_nem_promete_proxima(self):
        with mock.patch.dict(os.environ, {"LAPE_ROTINA": "0"}):
            self.assertFalse(rotina.ligada())
            parar = rotina.agendar(self.db.path)
            self.assertFalse(parar.is_set())
            self.assertFalse(any(t.name == "lape-rotina" for t in threading.enumerate()))
            self.assertTrue(all(p["proxima"] is None for p in rotina.situacao(self.db)["passos"]))

    def test_a_subida_do_servidor_agenda_a_rotina(self):
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        self.assertIn("_rotina.agendar(Path(db_path))", fonte)
        self.assertIn("parar_rotina.set()", fonte)


class TestARotinaPelaRede(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "rotas.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        linhas.instalar(db)
        auth.create_account(db, "Coordena", "coord@udesc.br", "senhaforte123", role="coordenacao")
        auth.create_account(db, "Mestranda", "mest@udesc.br", "senhaforte123", role="integrante")
        db.execute("UPDATE members SET role = 'coordenacao' WHERE login = 'coord@udesc.br'")
        db.execute("UPDATE members SET role = 'mestrando' WHERE login = 'mest@udesc.br'")
        db.upsert("members", {"full_name": "Doutorando Um", "name_key": "doutorando_um", "role": "doutorando"},
                  conflict=("name_key",))
        db.upsert("members", {"full_name": "Tecnico Um", "name_key": "tecnico_um", "role": "tecnico"},
                  conflict=("name_key",))
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

    def pedir(self, cookie, caminho, corpo=None):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{caminho}",
            data=json.dumps(corpo).encode() if corpo is not None else None,
            headers={"Content-Type": "application/json", "Cookie": cookie},
            method="POST" if corpo is not None else "GET")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"{}")

    def test_quem_le_ve_a_situacao(self):
        status, corpo = self.pedir(self.entrar("mest@udesc.br"), "/api/rotina")
        self.assertEqual(status, 200)
        self.assertEqual([p["passo"] for p in corpo["passos"]],
                         ["producao", "citacoes", "acervos", "descobrir", "perfis"])

    def test_so_a_coordenacao_manda_rodar(self):
        status, _ = self.pedir(self.entrar("mest@udesc.br"), "/api/rotina/rodar", {})
        self.assertEqual(status, 403)

    def test_passo_desconhecido_e_400(self):
        status, corpo = self.pedir(self.entrar("coord@udesc.br"), "/api/rotina/rodar", {"passos": ["lattes"]})
        self.assertEqual(status, 400)

    def test_a_coordenacao_roda_ao_lado_e_o_registro_fica(self):
        _sem_rede(self)
        status, corpo = self.pedir(self.entrar("coord@udesc.br"), "/api/rotina/rodar", {"passos": ["producao"]})
        self.assertEqual(status, 200, corpo)
        self.assertTrue(corpo["iniciada"])
        for t in threading.enumerate():
            if t.name == "lape-rotina-agora":
                t.join(timeout=30)
        db = Database(self.db_path)
        try:
            self.assertEqual(db.scalar("SELECT status FROM ingest_log WHERE source = 'rotina' AND target = 'producao'"), "ok")
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM audit_log WHERE action = 'rotina_rodada'"), 1)
        finally:
            db.close()

    def test_a_equipe_diz_quem_coorienta(self):
        """Mestrandos e doutorandos coorientam os bolsistas; o técnico não."""
        status, corpo = self.pedir(self.entrar("mest@udesc.br"), "/api/equipe")
        self.assertEqual(status, 200)
        por = {p["full_name"]: p for p in corpo["items"]}
        self.assertTrue(por["Coordena"]["orienta"] and por["Coordena"]["coorienta"])
        self.assertFalse(por["Mestranda"]["orienta"])
        self.assertTrue(por["Mestranda"]["coorienta"])
        self.assertTrue(por["Doutorando Um"]["coorienta"])
        self.assertFalse(por["Tecnico Um"]["coorienta"])


class TestATelaDaCoorientacao(unittest.TestCase):

    def test_quem_coorienta_inclui_mestrandos_e_doutorandos(self):
        self.assertEqual(set(mapping.COORIENTAM) - set(mapping.ORIENTAM), {"mestrando", "doutorando"})

    def test_o_seletor_de_coorientador_usa_a_lista_larga(self):
        fonte = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        self.assertIn("CACHE.coorientadores = equipe.items", fonte)
        self.assertIn("return (p.coorienta || p.orienta) && p.id !== ME.id;", fonte)
        campo = fonte[fonte.index('field("Coorientador"'):]
        campo = campo[:campo.index("}),")]
        self.assertIn("CACHE.coorientadores", campo)
        self.assertNotIn("Mesma lista do orientador", campo)

    def test_a_administracao_mostra_a_rotina(self):
        fonte = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        self.assertIn('api("/api/rotina")', fonte)
        self.assertIn('api("/api/rotina/rodar", "POST"', fonte)
        self.assertIn("await desenharRotina(rotBox);", fonte)


if __name__ == "__main__":
    unittest.main()
