#!/usr/bin/env python3
"""Testes do convite: o link que faz o laboratorio se cadastrar sozinho.

    python3 -m unittest discover -s tests -v

O convite e a unica porta do sistema que uma pessoa sem conta atravessa. Por
isso os testes aqui olham tanto o caminho feliz (abrir o link, escolher a
senha, cair no cadastro) quanto o que impede o link de virar porta aberta:
prazo, limite de usos, cancelamento e senha fraca. Nada sai para a rede.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth  # noqa: E402
from lape.db import Database  # noqa: E402


class TestConvite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "c.sqlite")
        self.db.migrate()
        self.chefe = auth.create_account(self.db, "Coordenacao", "coord@udesc.br",
                                         "Kx7m-Trilha-Serena-92", role="coordenacao")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_o_caminho_completo(self):
        convite = auth.create_invite(self.db, self.chefe["member_id"], "Equipe LAPE")
        self.assertTrue(auth.invite_state(self.db, convite["token"])["valid"])
        sessao = auth.accept_invite(self.db, convite["token"], "Julia Kunzler Amaral",
                                    "julia@udesc.br", "Vento-Claro-Sereno-7")
        # ja entra logada: nao precisa passar pela tela de login em seguida
        self.assertTrue(sessao["token"])
        self.assertEqual(sessao["user"]["user_role"], "integrante")
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM members WHERE login = 'julia@udesc.br'"), 1)

    def test_a_coordenacao_nunca_conhece_a_senha(self):
        """Quem convida nao escolhe a senha; ela nasce no navegador de quem aceita."""
        convite = auth.create_invite(self.db, self.chefe["member_id"])
        auth.accept_invite(self.db, convite["token"], "Julia", "julia@udesc.br",
                           "Vento-Claro-Sereno-7")
        guardado = self.db.scalar("SELECT password_hash FROM members WHERE login='julia@udesc.br'")
        self.assertNotIn("Vento-Claro-Sereno-7", guardado)
        self.assertTrue(guardado.startswith("pbkdf2_sha256$"))

    def test_limite_de_usos(self):
        convite = auth.create_invite(self.db, self.chefe["member_id"], max_uses=2)
        auth.accept_invite(self.db, convite["token"], "Um", "um@udesc.br", "Vento-Claro-1a")
        auth.accept_invite(self.db, convite["token"], "Dois", "dois@udesc.br", "Vento-Claro-2b")
        estado = auth.invite_state(self.db, convite["token"])
        self.assertFalse(estado["valid"])
        self.assertIn("limite", estado["reason"])
        with self.assertRaises(auth.AuthError):
            auth.accept_invite(self.db, convite["token"], "Tres", "tres@udesc.br", "Vento-Claro-3c")

    def test_convite_vencido(self):
        convite = auth.create_invite(self.db, self.chefe["member_id"])
        passado = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute("UPDATE invites SET expires_at = ?", (passado,))
        self.db.conn.commit()
        estado = auth.invite_state(self.db, convite["token"])
        self.assertFalse(estado["valid"])
        self.assertIn("venceu", estado["reason"])

    def test_convite_cancelado(self):
        convite = auth.create_invite(self.db, self.chefe["member_id"])
        alvo = self.db.scalar("SELECT id FROM invites WHERE token = ?", (convite["token"],))
        auth.revoke_invite(self.db, alvo, self.chefe["member_id"])
        self.assertFalse(auth.invite_state(self.db, convite["token"])["valid"])
        with self.assertRaises(auth.AuthError):
            auth.accept_invite(self.db, convite["token"], "Tarde", "tarde@udesc.br",
                               "Vento-Claro-4d")

    def test_token_inexistente(self):
        estado = auth.invite_state(self.db, "nao-existe-este-token-aqui")
        self.assertFalse(estado["valid"])

    def test_recusa_senha_fraca(self):
        convite = auth.create_invite(self.db, self.chefe["member_id"])
        for ruim in ("curta", "senha123", "aaaaaaaa"):
            with self.assertRaises(auth.AuthError, msg=f"aceitou '{ruim}'"):
                auth.accept_invite(self.db, convite["token"], "Alguem", "a@udesc.br", ruim)
        # nenhuma tentativa recusada pode ter gasto uma vaga
        self.assertEqual(auth.invite_state(self.db, convite["token"])["remaining"], 30)

    def test_email_ja_cadastrado(self):
        convite = auth.create_invite(self.db, self.chefe["member_id"])
        with self.assertRaises(auth.AuthError) as caso:
            auth.accept_invite(self.db, convite["token"], "Outro", "coord@udesc.br",
                               "Vento-Claro-5e")
        self.assertEqual(caso.exception.status, 409)

    def test_convite_nao_cria_administrador(self):
        """Elevar a admin exige a pessoa ja identificada, nunca um link em grupo."""
        with self.assertRaises(auth.AuthError):
            auth.create_invite(self.db, self.chefe["member_id"], role="admin")

    def test_tokens_nao_se_repetem_nem_sao_curtos(self):
        tokens = {auth.create_invite(self.db, self.chefe["member_id"])["token"]
                  for _ in range(20)}
        self.assertEqual(len(tokens), 20)
        self.assertTrue(all(len(t) >= 30 for t in tokens))

    def test_liga_ao_registro_que_a_planilha_ja_criou(self):
        """Quem se cadastra herda a producao que ja estava no banco.

        A planilha traz o autor como "Andrade"; a pessoa digita o nome
        inteiro. Se o cadastro criasse um segundo registro, os artigos dela
        ficariam orfaos no painel e a rede de coautoria se partiria.
        """
        from lape import ingest_excel

        ingest_excel.ingest_articles(self.db, [
            {"title": "Ansiedade competitiva em nadadores", "authors": "Andrade; Vilarino"},
            {"title": "Dor cronica e exercicio", "authors": "Andrade"},
        ])
        antes = self.db.scalar("SELECT COUNT(*) FROM members")
        convite = auth.create_invite(self.db, self.chefe["member_id"])
        auth.accept_invite(self.db, convite["token"], "Alexandro Andrade",
                           "alexandro@udesc.br", "Serra-do-Rio-do-Rastro-8")
        pessoa = self.db.dicts("SELECT id, full_name FROM members"
                               " WHERE login = 'alexandro@udesc.br'")[0]
        # nao criou registro novo: reaproveitou o da planilha
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM members"), antes)
        # e os artigos vieram junto
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM article_authors WHERE member_id = ?", (pessoa["id"],)), 2)
        # o nome digitado, mais completo, substitui a abreviacao da planilha
        self.assertEqual(pessoa["full_name"], "Alexandro Andrade")

    def test_nome_bom_nunca_e_trocado_por_um_pior(self):
        from lape import ingest_excel

        ingest_excel.ingest_members(self.db, [{"full_name": "Marina Rossetto Cardoso"}])
        convite = auth.create_invite(self.db, self.chefe["member_id"])
        auth.accept_invite(self.db, convite["token"], "Cardoso", "marina@udesc.br",
                           "Serra-do-Rio-do-Rastro-8")
        self.assertEqual(
            self.db.scalar("SELECT full_name FROM members WHERE login = 'marina@udesc.br'"),
            "Marina Rossetto Cardoso")

    def test_comparacao_de_nomes(self):
        melhor = auth._nome_mais_completo
        self.assertTrue(melhor("Andrade", "Alexandro Andrade"))
        self.assertTrue(melhor("Andrade A.", "Alexandro Andrade"))
        self.assertTrue(melhor("Cardoso", "Marina Rossetto Cardoso"))
        self.assertFalse(melhor("Alexandro Andrade", "Andrade"))
        self.assertFalse(melhor("Andrade", "Andrade"))
        self.assertFalse(melhor("Silva", "Alexandro Andrade"))
        self.assertFalse(melhor(None, "Alexandro Andrade"))

    def test_convite_com_perfil_de_coordenacao(self):
        """E o caso do professor: ele precisa convidar os outros e rodar agentes."""
        convite = auth.create_invite(self.db, self.chefe["member_id"],
                                     "Coordenacao", role="coordenacao", max_uses=1)
        sessao = auth.accept_invite(self.db, convite["token"], "Alexandro Andrade",
                                    "alexandro@udesc.br", "Serra-do-Rio-do-Rastro-8")
        self.assertEqual(sessao["user"]["user_role"], "coordenacao")
        # e ele ja consegue convidar a equipe
        equipe = auth.create_invite(self.db, sessao["user"]["id"], "Equipe", max_uses=30)
        self.assertTrue(auth.invite_state(self.db, equipe["token"])["valid"])

    def test_uso_fica_registrado(self):
        convite = auth.create_invite(self.db, self.chefe["member_id"])
        auth.accept_invite(self.db, convite["token"], "Julia", "julia@udesc.br",
                           "Vento-Claro-Sereno-7", ip="203.0.113.9")
        uso = self.db.dicts("SELECT * FROM invite_uses")[0]
        self.assertEqual(uso["ip"], "203.0.113.9")
        self.assertTrue(uso["member_id"])


class TestRotasDoConvite(unittest.TestCase):
    """Pelo HTTP, como o navegador de quem foi convidado faz."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "c.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Coordenacao", "coord@udesc.br", "Kx7m-Trilha-Serena-92",
                            role="coordenacao")
        auth.create_account(db, "Integrante", "membro@udesc.br", "Kx7m-Trilha-Serena-92",
                            role="integrante")
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

    def call(self, path, method="GET", body=None, cookie=None, headers=None):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(body).encode() if body is not None else None
        head = dict(headers or {})
        if data:
            head.setdefault("Content-Type", "application/json")
        if cookie:
            head["Cookie"] = f"{api.COOKIE_NAME}={cookie}"
        request = urllib.request.Request(url, data=data, method=method, headers=head)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                corpo = response.read().decode()
                set_cookie = response.headers.get("Set-Cookie") or ""
                token = set_cookie.split("=")[1].split(";")[0] if set_cookie else None
                return response.status, json.loads(corpo), token
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode()), None

    def entrar(self, login="coord@udesc.br"):
        _, _, token = self.call("/api/auth/login", "POST",
                                {"login": login, "senha": "Kx7m-Trilha-Serena-92"})
        return token

    def test_so_a_coordenacao_gera_convite(self):
        self.assertEqual(self.call("/api/invites", "POST", {})[0], 401)
        self.assertEqual(
            self.call("/api/invites", "POST", {}, cookie=self.entrar("membro@udesc.br"))[0], 403)
        self.assertEqual(self.call("/api/invites", "POST", {}, cookie=self.entrar())[0], 200)

    def test_o_link_usa_o_endereco_publico_e_nao_o_local(self):
        """Atras do tunel, o link tem de sair com o endereco por onde a pessoa chegou."""
        status, corpo, _ = self.call(
            "/api/invites", "POST", {"nome": "Equipe"}, cookie=self.entrar(),
            headers={"Host": "lape-do-lape.trycloudflare.com", "X-Forwarded-Proto": "https"})
        self.assertEqual(status, 200)
        self.assertTrue(corpo["link"].startswith("https://lape-do-lape.trycloudflare.com/convite/"),
                        corpo["link"])
        self.assertNotIn("127.0.0.1", corpo["link"])

    def test_a_pagina_do_convite_abre_sem_login(self):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/convite/qualquer")
        with urllib.request.urlopen(request, timeout=20) as response:
            html = response.read().decode()
        self.assertIn("Criar meu acesso", html)
        self.assertNotIn("__BASE_CSS__", html)

    def test_estado_e_aceite_sao_publicos(self):
        _, criado, _ = self.call("/api/invites", "POST", {"nome": "Equipe"},
                                 cookie=self.entrar())
        token = criado["token"]
        status, estado, _ = self.call(f"/api/convite/{token}")
        self.assertEqual(status, 200)
        self.assertTrue(estado["valid"])

        status, corpo, cookie = self.call(
            f"/api/convite/{token}/aceitar", "POST",
            {"nome": "Bruno Sartori", "email": "bruno@udesc.br", "senha": "Vento-Claro-Sereno-7"})
        self.assertEqual(status, 200, corpo)
        self.assertTrue(cookie, "deveria ja entrar logado")
        # e a sessao vale mesmo: consegue ler o proprio cadastro
        self.assertEqual(self.call("/api/auth/me", cookie=cookie)[1]["login"], "bruno@udesc.br")

    def test_o_estado_nao_vaza_o_que_nao_deve(self):
        _, criado, _ = self.call("/api/invites", "POST", {"nome": "Equipe"},
                                 cookie=self.entrar())
        _, estado, _ = self.call(f"/api/convite/{criado['token']}")
        for proibido in ("token", "created_by"):
            self.assertNotIn(proibido, estado, f"o estado publico expoe {proibido}")

    def test_token_malformado_nao_chega_na_rota(self):
        # espaco literal nem sai do urllib, entao vai codificado; o ponto e o
        # cifrao passam pelo cliente e tem de morrer no roteador do servidor
        for ruim in ("/api/convite/curto", "/api/convite/" + "x" * 200,
                     "/api/convite/com%20espaco", "/api/convite/token.com.ponto",
                     "/api/convite/token$cifrao"):
            self.assertEqual(self.call(ruim)[0], 404, ruim)

    def test_tentativa_em_massa_trava(self):
        """O convite e publico: sem travamento viraria fabrica de contas."""
        _, criado, _ = self.call("/api/invites", "POST", {"nome": "Equipe"},
                                 cookie=self.entrar())
        token = criado["token"]
        vistos = set()
        for i in range(auth.LOCK_AFTER_LOGIN + 2):
            status, _, _ = self.call(f"/api/convite/{token}/aceitar", "POST",
                                     {"nome": "X", "email": f"x{i}@udesc.br", "senha": "curta"})
            vistos.add(status)
        self.assertIn(429, vistos, "nunca travou")


class TestConviteNaConferencia(unittest.TestCase):
    """Convite em aberto e uma porta: a conferencia de publicacao tem de contar."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "c.sqlite")
        self.db.migrate()
        self.chefe = auth.create_account(self.db, "Coordenacao", "coord@udesc.br",
                                         "Kx7m-Trilha-Serena-92", role="admin")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_convite_em_aberto_aparece(self):
        from lape import preflight

        auth.create_invite(self.db, self.chefe["member_id"], "Equipe", max_uses=30)
        achados = preflight.conferir(self.db, {"LAPE_BEHIND_HTTPS": "1",
                                               "LAPE_TRUST_PROXY": "1"})
        casou = [a for a in achados if "convite" in a["titulo"]]
        self.assertTrue(casou, "a conferencia nao mencionou o convite aberto")
        self.assertIn("30 vaga", casou[0]["titulo"])

    def test_convite_cancelado_some_da_conferencia(self):
        from lape import preflight

        convite = auth.create_invite(self.db, self.chefe["member_id"], "Equipe")
        alvo = self.db.scalar("SELECT id FROM invites WHERE token = ?", (convite["token"],))
        auth.revoke_invite(self.db, alvo, self.chefe["member_id"])
        achados = preflight.conferir(self.db, {"LAPE_BEHIND_HTTPS": "1",
                                               "LAPE_TRUST_PROXY": "1"})
        self.assertFalse([a for a in achados if "convite" in a["titulo"]])


if __name__ == "__main__":
    unittest.main()
