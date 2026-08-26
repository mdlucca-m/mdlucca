#!/usr/bin/env python3
"""Testes da camada web do LAPE: acesso, permissoes, projetos e indice h.

    python3 -m unittest discover -s tests -v

Sobem um servidor HTTP real numa porta livre, sobre um banco temporario,
e conversam com ele exatamente como o navegador faz -- inclusive com o
cookie de sessao. Nenhuma chamada sai para a internet.
"""
from __future__ import annotations

import json
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

from lape import api, auth, ingest_excel, metrics  # noqa: E402
from lape.db import Database  # noqa: E402


class TestSenhas(unittest.TestCase):
    def test_hash_nao_guarda_a_senha(self):
        stored = auth.hash_password("segredo-do-lape")
        self.assertNotIn("segredo-do-lape", stored)
        self.assertTrue(stored.startswith("pbkdf2_sha256$"))

    def test_verificacao(self):
        stored = auth.hash_password("segredo-do-lape")
        self.assertTrue(auth.verify_password("segredo-do-lape", stored))
        self.assertFalse(auth.verify_password("outra-coisa", stored))
        self.assertFalse(auth.verify_password("segredo-do-lape", None))
        self.assertFalse(auth.verify_password("", stored))

    def test_hashes_diferentes_para_a_mesma_senha(self):
        # sal aleatorio: dois cadastros com a mesma senha nao se parecem
        self.assertNotEqual(auth.hash_password("mesma-senha-123"),
                            auth.hash_password("mesma-senha-123"))

    def test_senha_curta_e_recusada(self):
        with self.assertRaises(auth.AuthError):
            auth.hash_password("curta")

    def test_login_normalizado(self):
        self.assertEqual(auth.normalize_login("  ANDRADE@Udesc.BR "), "andrade@udesc.br")
        with self.assertRaises(auth.AuthError):
            auth.normalize_login("nao é um login")


class TestContas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_criar_e_entrar(self):
        auth.create_account(self.db, "Alexandro Andrade", "andrade@udesc.br",
                            "senhaforte123", role="admin")
        session = self.db and auth.login(self.db, "ANDRADE@udesc.br", "senhaforte123")
        self.assertEqual(session["user"]["user_role"], "admin")
        self.assertEqual(auth.current_user(self.db, session["token"])["login"], "andrade@udesc.br")
        auth.logout(self.db, session["token"])
        self.assertIsNone(auth.current_user(self.db, session["token"]))

    def test_senha_errada(self):
        auth.create_account(self.db, "Fulano de Tal", "fulano@udesc.br", "senhaforte123")
        with self.assertRaises(auth.AuthError) as ctx:
            auth.login(self.db, "fulano@udesc.br", "chute")
        self.assertEqual(ctx.exception.status, 401)

    def test_login_duplicado(self):
        auth.create_account(self.db, "Pessoa Um", "mesmo@udesc.br", "senhaforte123")
        with self.assertRaises(auth.AuthError) as ctx:
            auth.create_account(self.db, "Pessoa Dois", "mesmo@udesc.br", "senhaforte123")
        self.assertEqual(ctx.exception.status, 409)

    def test_conta_reaproveita_integrante_existente(self):
        # a planilha ja tinha "Andrade"; o acesso nao pode criar uma segunda pessoa
        ingest_excel.ingest_articles(self.db, [{"title": "Estudo", "authors": "Andrade; Vilarino"}])
        antes = self.db.scalar("SELECT COUNT(*) FROM members")
        auth.create_account(self.db, "Alexandro Andrade", "andrade@udesc.br", "senhaforte123")
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM members"), antes)
        self.assertEqual(
            self.db.scalar("SELECT full_name FROM members WHERE login = 'andrade@udesc.br'"),
            "Alexandro Andrade")

    def test_troca_de_senha(self):
        conta = auth.create_account(self.db, "Fulano de Tal", "fulano@udesc.br", "senhaforte123")
        with self.assertRaises(auth.AuthError):
            auth.change_password(self.db, conta["member_id"], "errada", "novasenha123")
        auth.change_password(self.db, conta["member_id"], "senhaforte123", "novasenha123")
        self.assertTrue(auth.login(self.db, "fulano@udesc.br", "novasenha123"))

    def test_senha_gerada_exige_troca(self):
        conta = auth.create_account(self.db, "Fulano de Tal", "fulano@udesc.br")
        self.assertIn("senha_inicial", conta)
        self.assertTrue(conta["must_change_password"])

    def test_perfis(self):
        integrante = {"id": 5, "user_role": "integrante"}
        coordenacao = {"id": 9, "user_role": "coordenacao"}
        self.assertTrue(auth.can_edit_member(integrante, 5))
        self.assertFalse(auth.can_edit_member(integrante, 6))
        self.assertTrue(auth.can_edit_member(coordenacao, 6))
        auth.require(integrante, "integrante")
        with self.assertRaises(auth.AuthError):
            auth.require(integrante, "coordenacao")
        with self.assertRaises(auth.AuthError):
            auth.require(None, "leitura")


class TestIndiceH(unittest.TestCase):
    def test_calculo(self):
        self.assertEqual(metrics.h_index([10, 8, 5, 4, 3]), 4)
        self.assertEqual(metrics.h_index([50, 40, 30, 20, 10, 5, 4, 3, 2, 1]), 5)
        self.assertEqual(metrics.h_index([1, 1, 1]), 1)
        self.assertEqual(metrics.h_index([0, 0]), 0)
        self.assertEqual(metrics.h_index([]), 0)
        self.assertEqual(metrics.i10_index([50, 12, 9, 10, None]), 3)

    def test_calculo_a_partir_do_banco(self):
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "t.sqlite")
        db.migrate()
        try:
            citacoes = [12, 8, 5, 2, 1]
            for i, n in enumerate(citacoes):
                db.upsert("articles", {"title": f"A{i}", "title_key": f"a{i}",
                                       "status": "publicado", "scopus_citations": n,
                                       "openalex_citations": n}, conflict=("title_key",))
            ingest_excel.ingest_authors(db, [
                {"article": f"A{i}", "author_name": "Alexandro Andrade", "author_order": 1}
                for i in range(len(citacoes))])
            metrics.compute_h_indexes(db)
            pessoa = db.dicts("SELECT h_index, h_index_scopus, i10_index, citations_total"
                              " FROM members")[0]
            self.assertEqual(pessoa["h_index"], 3)          # 12, 8 e 5 >= 3
            self.assertEqual(pessoa["h_index_scopus"], 3)
            self.assertEqual(pessoa["i10_index"], 1)        # so o de 12 citacoes
            self.assertEqual(pessoa["citations_total"], sum(citacoes))
        finally:
            db.close()
            tmp.cleanup()


class TestProjetos(unittest.TestCase):
    def test_projeto_liga_pesquisadores(self):
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "t.sqlite")
        db.migrate()
        try:
            ingest_excel.ingest_projects(db, [{
                "code": "PROJ-01", "name": "Exercício e fibromialgia",
                "coordinator": "Alexandro Andrade", "funder": "CNPq", "amount": "120000",
                "started_on": "01/03/2025", "status": "Em andamento",
                "members": "Guilherme Vilarino; Loiane",
            }])
            projeto = db.dicts("SELECT * FROM v_projects")[0]
            self.assertEqual(projeto["status"], "em_andamento")
            self.assertEqual(projeto["n_members"], 3)   # coordenador entra na equipe
            self.assertEqual(projeto["amount"], 120000.0)
            self.assertEqual(projeto["started_on"], "2025-03-01")

            pessoa = db.dicts("SELECT n_projects, projects FROM v_researcher"
                              " WHERE name_key = 'andrade_a'")[0]
            self.assertEqual(pessoa["n_projects"], 1)
            self.assertIn("fibromialgia", pessoa["projects"])
        finally:
            db.close()
            tmp.cleanup()

    def test_reimportar_nao_duplica_equipe(self):
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "t.sqlite")
        db.migrate()
        try:
            linha = {"code": "PROJ-01", "name": "Projeto", "members": "Andrade; Vilarino"}
            ingest_excel.ingest_projects(db, [linha])
            ingest_excel.ingest_projects(db, [linha])
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM projects"), 1)
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM project_members"), 2)
        finally:
            db.close()
            tmp.cleanup()


class TestApi(unittest.TestCase):
    """Servidor HTTP real, conversando por cookie como o navegador."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "api.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        ingest_excel.ingest_articles(db, [
            {"title": "Ansiedade em atletas", "authors": "Andrade; Vilarino",
             "status": "Publicado", "year_published": "2025", "doi": "10.1/a",
             "scopus_citations": "9"},
            {"title": "Sono e desempenho", "authors": "Loiane; Andrade"},
        ])
        auth.create_account(db, "Alexandro Andrade", "admin@udesc.br", "senhaforte123",
                            role="admin")
        auth.create_account(db, "Loiane", "loiane@udesc.br", "senhaforte123",
                            role="integrante")
        db.close()

        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *args, **kwargs: None   # silencia o log nos testes
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def call(self, path, method="GET", body=None, cookie=None):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        if cookie:
            headers["Cookie"] = f"{api.COOKIE_NAME}={cookie}"
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read().decode()
                set_cookie = response.headers.get("Set-Cookie") or ""
                token = set_cookie.split("=")[1].split(";")[0] if set_cookie else None
                return response.status, json.loads(payload), token
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode()), None

    def entrar(self, login="admin@udesc.br", senha="senhaforte123"):
        status, _, token = self.call("/api/auth/login", "POST", {"login": login, "senha": senha})
        self.assertEqual(status, 200)
        return token

    # -- acesso --
    def test_health_e_publico(self):
        status, body, _ = self.call("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertFalse(body["authenticated"])

    def test_metricas_exigem_login(self):
        status, body, _ = self.call("/api/metrics/overview")
        self.assertEqual(status, 401)
        self.assertIn("entrar", body["error"])

    def test_login_devolve_cookie_e_libera_leitura(self):
        token = self.entrar()
        self.assertTrue(token)
        status, body, _ = self.call("/api/metrics/overview", cookie=token)
        self.assertEqual(status, 200)
        # >= 2 e nao == 2: outros testes desta classe cadastram artigos
        self.assertGreaterEqual(body["n_articles"], 2)

    def test_login_invalido(self):
        status, body, _ = self.call("/api/auth/login", "POST",
                                    {"login": "admin@udesc.br", "senha": "chute"})
        self.assertEqual(status, 401)
        self.assertIn("incorretos", body["error"])

    def test_me(self):
        token = self.entrar()
        status, body, _ = self.call("/api/auth/me", cookie=token)
        self.assertEqual(status, 200)
        self.assertEqual(body["login"], "admin@udesc.br")
        self.assertEqual(body["user_role"], "admin")

    def test_logout_encerra_a_sessao(self):
        token = self.entrar()
        self.call("/api/auth/logout", "POST", {}, cookie=token)
        status, _, _ = self.call("/api/auth/me", cookie=token)
        self.assertEqual(status, 401)

    # -- cadastro --
    def test_cadastro_aceita_colunas_em_portugues(self):
        token = self.entrar()
        status, body, _ = self.call("/api/articles", "POST", {
            "Título": "Treinamento mental em ginastas",
            "Autores": "Andrade; Vilarino",
            "Status": "Publicado", "Ano": 2026, "Periódico": "Motriz",
        }, cookie=token)
        self.assertEqual(status, 200)
        self.assertEqual(body["written"], 1)
        self.assertEqual(body["records"][0]["status"], "publicado")

    def test_integrante_nao_edita_cadastro_de_outro(self):
        token = self.entrar("loiane@udesc.br")
        status, body, _ = self.call("/api/members", "POST",
                                    {"Nome completo": "Alexandro Andrade", "Telefone": "999"},
                                    cookie=token)
        self.assertEqual(status, 403)
        self.assertIn("próprio", body["error"])

    def test_integrante_edita_o_proprio_cadastro(self):
        token = self.entrar("loiane@udesc.br")
        status, _, _ = self.call("/api/members", "POST",
                                 {"Nome completo": "Loiane", "Telefone": "48 99999-0000"},
                                 cookie=token)
        self.assertEqual(status, 200)

    def test_integrante_nao_roda_agentes(self):
        token = self.entrar("loiane@udesc.br")
        status, body, _ = self.call("/api/agents/tracker", "POST", {"tasks": ["citar"]},
                                    cookie=token)
        self.assertEqual(status, 403)

    def test_integrante_nao_cria_usuarios(self):
        token = self.entrar("loiane@udesc.br")
        status, _, _ = self.call("/api/auth/usuarios", "POST",
                                 {"nome": "Intruso", "login": "intruso@udesc.br"}, cookie=token)
        self.assertEqual(status, 403)

    def test_admin_cria_usuario_com_senha_gerada(self):
        token = self.entrar()
        status, body, _ = self.call("/api/auth/usuarios", "POST",
                                    {"nome": "Nayara", "login": "nayara@udesc.br"}, cookie=token)
        self.assertEqual(status, 200)
        self.assertIn("senha_inicial", body)
        self.assertGreaterEqual(len(body["senha_inicial"]), 12)

    # -- leitura --
    def test_listagem_com_filtro(self):
        token = self.entrar()
        status, body, _ = self.call("/api/articles?status=publicado", cookie=token)
        self.assertEqual(status, 200)
        self.assertTrue(all(item["status"] == "publicado" for item in body["items"]))

    def test_detalhe_do_pesquisador(self):
        token = self.entrar()
        status, body, _ = self.call("/api/researchers/1", cookie=token)
        self.assertEqual(status, 200)
        self.assertIn("articles", body)
        self.assertIn("project_list", body)
        self.assertIn("coauthors", body)

    def test_listagem_de_membros_nao_vaza_hash_de_senha(self):
        token = self.entrar()
        _, body, _ = self.call("/api/members", cookie=token)
        for item in body["items"]:
            self.assertNotIn("password_hash", item)

    def test_rota_inexistente(self):
        status, body, _ = self.call("/api/nao-existe")
        self.assertEqual(status, 404)
        self.assertIn("não encontrada", body["error"])

    # -- paginas --
    def test_painel_redireciona_sem_login(self):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/")

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None

        opener = urllib.request.build_opener(NoRedirect)
        try:
            with opener.open(request, timeout=20) as response:
                self.assertEqual(response.status, 303)
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 303)
            self.assertEqual(exc.headers.get("Location"), "/entrar")

    def test_painel_ao_vivo_para_quem_entrou(self):
        token = self.entrar()
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/",
                                         headers={"Cookie": f"{api.COOKIE_NAME}={token}"})
        with urllib.request.urlopen(request, timeout=30) as response:
            html = response.read().decode()
        self.assertEqual(response.status, 200)
        self.assertIn("<title>", html)
        self.assertNotIn("__DATA__", html)
        self.assertIn('"live":true', html.replace(" ", ""))

    def test_pagina_de_login(self):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/entrar")
        with urllib.request.urlopen(request, timeout=20) as response:
            html = response.read().decode()
        self.assertIn("Entrar", html)
        self.assertNotIn("__BASE_CSS__", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
