#!/usr/bin/env python3
"""Testes da camada web do LAPE: acesso, permissoes, projetos e indice h.

    python3 -m unittest discover -s tests -v

Sobem um servidor HTTP real numa porta livre, sobre um banco temporario,
e conversam com ele exatamente como o navegador faz -- inclusive com o
cookie de sessao. Nenhuma chamada sai para a internet.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import time
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth, ingest_excel, metrics, preflight  # noqa: E402
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

    def test_area_do_integrante_vem_montada(self):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/app")
        with urllib.request.urlopen(request, timeout=20) as response:
            html = response.read().decode()
        self.assertIn("Área do integrante", html)
        for marcador in ("__BASE_CSS__", "__ICONS_JS__"):
            self.assertNotIn(marcador, html, f"marcador nao substituido: {marcador}")
        self.assertIn("const Icons", html)   # o menu monta os icones a partir daqui


class TestCacheDoNavegador(unittest.TestCase):
    """Nada do que a API devolve pode ser guardado pelo navegador.

    O painel e remontado do banco a cada acesso. Sem `no-store`, o navegador
    guarda por conta propria e devolve a versao velha -- e quem acabou de
    atualizar o sistema recarrega a pagina e jura que nada mudou. Foi
    exatamente o que aconteceu.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "cache.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Coordenação", "coord@udesc.br", "senhaforte123", role="admin")
        db.close()
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
        cls.tmp.cleanup()

    def cabecalhos(self, caminho):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}{caminho}")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                return resposta.headers
        except urllib.error.HTTPError as exc:
            return exc.headers

    def test_paginas_e_api_nao_sao_guardadas(self):
        for caminho in ("/entrar", "/app", "/api/health", "/api"):
            with self.subTest(caminho=caminho):
                cache = self.cabecalhos(caminho).get("Cache-Control") or ""
                self.assertIn("no-store", cache, f"{caminho} pode ser guardada pelo navegador")

    def test_o_favicon_pode_ser_guardado(self):
        # nunca muda; buscar de novo a cada tela e desperdicio
        cache = self.cabecalhos("/favicon.ico").get("Cache-Control") or ""
        self.assertIn("max-age", cache)


class TestPublicacao(unittest.TestCase):
    """O que so passa a importar quando o endereco deixa de ser 127.0.0.1.

    Servidor proprio, banco proprio: os testes de travamento sujam o
    audit_log de proposito e nao podem contaminar as outras classes.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "pub.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Coordenacao", "coord@udesc.br", "senhaforte123",
                            role="coordenacao")
        db.close()
        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *a, **k: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def setUp(self):
        db = Database(self.db_path)
        db.execute("DELETE FROM audit_log")
        db.conn.commit()
        db.close()

    def tentar(self, login_value, senha, headers=None):
        url = f"http://127.0.0.1:{self.port}/api/auth/login"
        data = json.dumps({"login": login_value, "senha": senha}).encode()
        head = {"Content-Type": "application/json"}
        head.update(headers or {})
        request = urllib.request.Request(url, data=data, method="POST", headers=head)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read().decode()), response.headers
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode()), exc.headers

    # -- forca bruta --
    def test_trava_depois_de_muitas_tentativas(self):
        for _ in range(auth.LOCK_AFTER_LOGIN):
            status, _, _ = self.tentar("coord@udesc.br", "chute-errado")
            self.assertEqual(status, 401)
        status, body, _ = self.tentar("coord@udesc.br", "chute-errado")
        self.assertEqual(status, 429, "a conta deveria estar travada")
        self.assertIn("tentativas", body["error"])
        # travado vale ate para a senha certa: quem esta martelando nao passa
        status, _, _ = self.tentar("coord@udesc.br", "senhaforte123")
        self.assertEqual(status, 429)

    def test_acerto_zera_o_contador(self):
        for _ in range(3):
            self.tentar("coord@udesc.br", "chute-errado")
        status, _, _ = self.tentar("coord@udesc.br", "senhaforte123")
        self.assertEqual(status, 200)
        db = Database(self.db_path)
        try:
            self.assertEqual(auth.recent_failures(db, login_value="coord@udesc.br"), 0)
        finally:
            db.close()

    def test_travamento_por_login_nao_derruba_os_outros(self):
        for _ in range(auth.LOCK_AFTER_LOGIN + 1):
            self.tentar("alvo@udesc.br", "chute")
        # o alvo trava, mas quem tem a senha certa continua entrando
        self.assertEqual(self.tentar("alvo@udesc.br", "chute")[0], 429)
        self.assertEqual(self.tentar("coord@udesc.br", "senhaforte123")[0], 200)

    # -- enumeracao de contas --
    def test_login_inexistente_e_senha_errada_respondem_igual(self):
        inexistente = self.tentar("ninguem@udesc.br", "qualquer")
        errada = self.tentar("coord@udesc.br", "qualquer")
        self.assertEqual(inexistente[0], errada[0])
        self.assertEqual(inexistente[1]["error"], errada[1]["error"])

    def test_login_inexistente_nao_responde_instantaneamente(self):
        """O hash descartavel precisa rodar, senao a demora entrega quem tem conta."""
        comeco = time.perf_counter()
        self.tentar("ninguem-mesmo@udesc.br", "qualquer")
        gasto = time.perf_counter() - comeco
        # o PBKDF2 leva ~100ms; 20ms ja prova que ele nao foi pulado
        self.assertGreater(gasto, 0.02, "resposta rapida demais: o hash foi pulado")

    def test_a_origem_fica_registrada(self):
        self.tentar("coord@udesc.br", "chute-errado")
        db = Database(self.db_path)
        try:
            linha = db.dicts("SELECT ip, detail FROM audit_log WHERE action = 'login_negado'")[0]
            self.assertTrue(linha["ip"], "sem origem nao da para contar por IP")
        finally:
            db.close()

    # -- cabecalhos --
    def test_cabecalhos_de_seguranca_em_toda_resposta(self):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/health")
        with urllib.request.urlopen(request, timeout=20) as response:
            headers = response.headers
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertIn("frame-ancestors 'none'", headers.get("Content-Security-Policy", ""))
        self.assertIn("connect-src 'self'", headers.get("Content-Security-Policy", ""))

    def test_cookie_marcado_como_secure_atras_de_https(self):
        anterior = api.BEHIND_HTTPS
        api.BEHIND_HTTPS = True
        try:
            _, _, headers = self.tentar("coord@udesc.br", "senhaforte123")
            cookie = headers.get("Set-Cookie", "")
        finally:
            api.BEHIND_HTTPS = anterior
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        self.assertIn("Secure", cookie)

    def test_sem_https_o_cookie_nao_finge_ser_secure(self):
        anterior = api.BEHIND_HTTPS
        api.BEHIND_HTTPS = False
        try:
            _, _, headers = self.tentar("coord@udesc.br", "senhaforte123")
            cookie = headers.get("Set-Cookie", "")
        finally:
            api.BEHIND_HTTPS = anterior
        self.assertIn("HttpOnly", cookie)
        self.assertNotIn("Secure", cookie)

    # -- primeiro administrador --
    def test_recusa_senha_de_exemplo_no_primeiro_admin(self):
        """Falha fechado: melhor nao subir do que subir com a senha do tutorial."""
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "novo.sqlite")
        db.migrate()
        try:
            for ruim in ("troque-por-uma-senha-longa", "senha123", "12345678", "aaaaaaaa"):
                with self.assertRaises(auth.AuthError, msg=f"aceitou '{ruim}'"):
                    auth.bootstrap_admin(db, "admin@udesc.br", ruim)
            criado = auth.bootstrap_admin(db, "admin@udesc.br", "Kx7m-Trilha-Serena-92")
            self.assertEqual(criado["login"], "admin@udesc.br")
            self.assertEqual(criado["role"], "admin")
        finally:
            db.close()
            tmp.cleanup()

    def test_senha_fraca_reconhece_os_casos(self):
        self.assertIsNone(auth.senha_fraca("Kx7m-Trilha-Serena-92"))
        self.assertIsNotNone(auth.senha_fraca("curta"))
        self.assertIsNotNone(auth.senha_fraca("SENHA123"))
        self.assertIsNotNone(auth.senha_fraca("aaaabbbb"))
        self.assertIsNotNone(auth.senha_fraca(None))

    # -- proxy --
    def test_cabecalho_de_proxy_so_e_aceito_quando_ha_proxy(self):
        """Sem proxy na frente, X-Forwarded-For e escrito pelo proprio cliente.

        Aceita-lo sempre daria a qualquer um a chave para escapar do
        travamento por IP: bastaria mudar o cabecalho a cada tentativa.
        """
        anterior = api.TRUST_PROXY
        api.TRUST_PROXY = False
        try:
            self.tentar("coord@udesc.br", "chute", {"X-Forwarded-For": "203.0.113.9"})
            db = Database(self.db_path)
            try:
                ip = db.scalar("SELECT ip FROM audit_log WHERE action = 'login_negado'"
                               " ORDER BY id DESC LIMIT 1")
            finally:
                db.close()
            self.assertEqual(ip, "127.0.0.1", "o cabecalho do cliente foi acreditado")
        finally:
            api.TRUST_PROXY = anterior

    def test_com_proxy_confiavel_o_endereco_real_e_usado(self):
        anterior = api.TRUST_PROXY
        api.TRUST_PROXY = True
        try:
            self.tentar("coord@udesc.br", "chute",
                        {"X-Forwarded-For": "203.0.113.9, 10.0.0.1"})
            db = Database(self.db_path)
            try:
                ip = db.scalar("SELECT ip FROM audit_log WHERE action = 'login_negado'"
                               " ORDER BY id DESC LIMIT 1")
            finally:
                db.close()
            self.assertEqual(ip, "203.0.113.9")
        finally:
            api.TRUST_PROXY = anterior


class TestConferenciaDePublicacao(unittest.TestCase):
    """A conferencia precisa acusar o que realmente impede a publicacao."""

    # A conferencia marca /tmp e /app como caminho efemero, de proposito. Um
    # banco de teste vive sempre num diretorio temporario, e o proprio
    # repositorio pode estar sob /tmp (clone descartavel, CI). Entao este
    # achado e ruido AQUI -- e tem teste proprio, o test_banco_em_caminho_efemero_impede.
    RUIDO_DO_AMBIENTE = "efêmero"

    def impedimentos(self, ambiente):
        return [a["titulo"] for a in preflight.conferir(self.db, ambiente)
                if a["nivel"] == "impede" and self.RUIDO_DO_AMBIENTE not in a["titulo"]]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "pf.sqlite")
        self.db.migrate()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def niveis(self, ambiente):
        achados = preflight.conferir(self.db, ambiente)
        return {a["titulo"]: a["nivel"] for a in achados}

    AMBIENTE_BOM = {"LAPE_BEHIND_HTTPS": "1", "LAPE_TRUST_PROXY": "1"}

    def test_sem_https_impede(self):
        achados = preflight.conferir(self.db, {})
        impedimentos = [a["titulo"] for a in achados if a["nivel"] == "impede"]
        self.assertTrue(any("HTTPS" in t for t in impedimentos))
        self.assertFalse(preflight.resumo(achados)["pronto"])

    def test_sem_administrador_impede(self):
        self.assertTrue(any("administrador" in t for t in self.impedimentos(self.AMBIENTE_BOM)))

    def test_ambiente_completo_libera(self):
        auth.create_account(self.db, "Chefia", "chefe@udesc.br", "Kx7m-Trilha-Serena-92",
                            role="admin")
        self.db.execute("UPDATE members SET must_change_password = 0")
        self.db.conn.commit()
        restantes = self.impedimentos(self.AMBIENTE_BOM)
        self.assertEqual(restantes, [], f"impedimentos inesperados: {restantes}")

    def test_senha_de_exemplo_no_ambiente_impede(self):
        auth.create_account(self.db, "Chefia", "chefe@udesc.br", "Kx7m-Trilha-Serena-92",
                            role="admin")
        ambiente = dict(self.AMBIENTE_BOM, LAPE_ADMIN_PASSWORD="troque-por-uma-senha-longa")
        self.assertTrue(any("LAPE_ADMIN_PASSWORD" in t for t in self.impedimentos(ambiente)))

    def test_painel_publico_e_apontado_como_risco(self):
        ambiente = dict(self.AMBIENTE_BOM, LAPE_PUBLIC_DASHBOARD="1")
        self.assertIn("risco", self.niveis(ambiente).get("Painel visível sem login", ""))

    def test_webhook_sem_segredo_e_risco(self):
        from lape import hooks

        hooks.register(self.db, "n8n", "https://n8n.exemplo/webhook/lape")
        achados = preflight.conferir(self.db, self.AMBIENTE_BOM)
        self.assertTrue(any(a["nivel"] == "risco" and "assinatura" in a["titulo"]
                            for a in achados))

    def test_banco_em_caminho_efemero_impede(self):
        efemero = tempfile.TemporaryDirectory(dir="/tmp")
        db = Database(Path(efemero.name) / "pf.sqlite")
        db.migrate()
        auth.create_account(db, "Chefia", "chefe@udesc.br", "Kx7m-Trilha-Serena-92",
                            role="admin")
        try:
            achados = preflight.conferir(db, self.AMBIENTE_BOM)
            self.assertTrue(any(a["nivel"] == "impede" and "efêmero" in a["titulo"]
                                for a in achados))
        finally:
            db.close()
            efemero.cleanup()

    def test_a_conferencia_nao_escreve_no_banco(self):
        antes = self.db.scalar("SELECT COUNT(*) FROM audit_log")
        preflight.conferir(self.db, self.AMBIENTE_BOM)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM audit_log"), antes)


class TestTokensDoTema(unittest.TestCase):
    """Todo var(--token) usado nas paginas precisa existir no tema.

    Um var() indefinido nao pinta nada e nao levanta erro: a pagina continua
    de pe, so que sem hierarquia -- rotulo, dica e cabecalho ficam com a
    mesma cor. Foi assim que a area do integrante quebrou quando o tema
    trocou de vocabulario, e e por isso que a checagem virou teste.
    """

    TEMPLATES = ROOT / "scripts" / "lape" / "templates"

    def definidos(self) -> set[str]:
        tema = (self.TEMPLATES / "theme.css").read_text(encoding="utf-8")
        # sem ancora de inicio de linha: o tema declara varios tokens na mesma
        # linha, e um `var(--x)` nunca casa aqui porque nao vem seguido de ":"
        return set(re.findall(r"(--[a-z0-9-]+)\s*:", tema))

    def test_nenhum_token_indefinido(self):
        definidos = self.definidos()
        self.assertIn("--ink", definidos, "o proprio tema nao foi lido")
        for nome in ("dashboard.html", "app.html", "login.html", "convite.html",
                     "mural.html", "theme.css", "charts.js"):
            texto = (self.TEMPLATES / nome).read_text(encoding="utf-8")
            # so o uso sem reserva precisa existir no tema: `var(--tom, var(--x))`
            # e uma variavel escrita pelo JS, e a reserva e justamente o plano B
            usados = set(re.findall(r"var\((--[a-z0-9-]+)\s*\)", texto))
            locais = set(re.findall(r"(--[a-z0-9-]+)\s*:", texto))
            # series-N e seq-N sao montados em tempo de execucao pelo charts.js
            faltando = {t for t in usados - definidos - locais
                        if not re.match(r"^--(series|seq|ord)-\d+$", t)}
            self.assertEqual(faltando, set(), f"tokens indefinidos em {nome}: {sorted(faltando)}")

    def test_o_tema_define_os_dois_modos(self):
        tema = (self.TEMPLATES / "theme.css").read_text(encoding="utf-8")
        self.assertIn("prefers-color-scheme: light", tema)
        self.assertIn('[data-theme="light"]', tema)
        self.assertIn('[data-theme="dark"]', tema)


if __name__ == "__main__":
    unittest.main(verbosity=2)
