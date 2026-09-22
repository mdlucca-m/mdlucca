#!/usr/bin/env python3
"""Três Vieiras, uma ficha: o cadastro que caía na pessoa errada.

    python3 -m unittest tests.test_contas_separadas -v

Veio pelo WhatsApp: "eu que entrei agora, e meu nome não aparece" -- o
ponto saía como "Ericles de P Vieira". Ao criar o acesso, o sistema
procurava a ficha pelo palpite de sobrenome, feito para casar autoria
vinda de três fontes: sendo Ericles o único Vieira do banco, "Fulano
Vieira" caía na ficha dele. Com três alunos do mesmo sobrenome, o
palpite errava sempre.

O que se guarda: criar acesso nunca usa o palpite; a ficha de sobrenome
sozinho da planilha continua sendo reaproveitada; duas pessoas de mesma
chave ganham fichas distintas; a importação não junta iniciais que
começam diferente; e há como desfazer o que já aconteceu.
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

from lape import api, auth, ponto  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
SENHA = "Kx7m-Trilha-Serena-92"


class BaseComFichas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "c.sqlite")
        self.db.migrate()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)

    def ficha(self, member_id):
        return self.db.dicts("SELECT id, full_name, name_key, login FROM members WHERE id = ?",
                             (member_id,))[0]


class TestOCadastroNaoCaiNaFichaDoOutro(BaseComFichas):

    def test_o_segundo_vieira_ganha_a_propria_ficha(self):
        ericles = self.db.member_id("Ericles de P Vieira")      # veio da planilha
        self.db.conn.commit()
        conta = auth.create_account(self.db, "Fulano Vieira", "fulano@udesc.br", SENHA)
        self.assertNotEqual(conta["member_id"], ericles)
        self.assertEqual(self.ficha(ericles)["full_name"], "Ericles de P Vieira")
        self.assertIsNone(self.ficha(ericles)["login"])
        self.assertEqual(self.ficha(conta["member_id"])["full_name"], "Fulano Vieira")

    def test_tres_vieiras_sao_tres_fichas(self):
        ids = {auth.create_account(self.db, nome, f"{i}@udesc.br", SENHA)["member_id"]
               for i, nome in enumerate(("Ericles de P Vieira", "Eduardo Vieira", "Elisa Vieira"))}
        self.assertEqual(len(ids), 3)
        nomes = sorted(r["full_name"] for r in self.db.dicts("SELECT full_name FROM members WHERE login IS NOT NULL"))
        self.assertEqual(nomes, ["Eduardo Vieira", "Elisa Vieira", "Ericles de P Vieira"])

    def test_a_mesma_chave_com_outro_login_nao_e_a_mesma_pessoa(self):
        """"Eduardo Vieira" e "Elisa Vieira" dão a mesma chave `vieira_e`."""
        um = auth.create_account(self.db, "Eduardo Vieira", "eduardo@udesc.br", SENHA)["member_id"]
        dois = auth.create_account(self.db, "Elisa Vieira", "elisa@udesc.br", SENHA)["member_id"]
        self.assertNotEqual(um, dois)
        self.assertEqual(self.ficha(um)["login"], "eduardo@udesc.br")
        self.assertEqual(self.ficha(dois)["login"], "elisa@udesc.br")
        self.assertNotEqual(self.ficha(um)["name_key"], self.ficha(dois)["name_key"])

    def test_a_ficha_de_sobrenome_sozinho_da_planilha_continua_sendo_reaproveitada(self):
        """"Andrade" na planilha e "Alexandro Andrade" no cadastro são a mesma
        pessoa -- e os artigos dela já estão ligados àquela ficha."""
        andrade = self.db.member_id("Andrade")
        self.db.conn.commit()
        conta = auth.create_account(self.db, "Alexandro Andrade", "andrade@udesc.br", SENHA)
        self.assertEqual(conta["member_id"], andrade)
        self.assertEqual(self.ficha(andrade)["full_name"], "Alexandro Andrade")
        self.assertEqual(self.ficha(andrade)["name_key"], "andrade_a")

    def test_a_grafia_declarada_leva_a_ficha_certa(self):
        pessoa = self.db.member_id("Guilherme Torres Vilarino")
        self.db.register_alias("Torres Vilarino, Guilherme", pessoa)
        self.db.conn.commit()
        conta = auth.create_account(self.db, "Torres Vilarino, Guilherme", "gtv@udesc.br", SENHA)
        self.assertEqual(conta["member_id"], pessoa)

    def test_a_mesma_pessoa_de_novo_reaproveita_a_ficha_sem_login(self):
        pessoa = self.db.member_id("Carla Souza")
        self.db.conn.commit()
        conta = auth.create_account(self.db, "Carla Souza", "carla@udesc.br", SENHA)
        self.assertEqual(conta["member_id"], pessoa)


class TestAImportacaoNaoJuntaIniciaisDiferentes(BaseComFichas):

    def test_vieira_ep_nao_e_vieira_f(self):
        ericles = self.db.member_id("Ericles de P Vieira")
        fulano = self.db.member_id("Fulano Vieira")
        self.assertNotEqual(ericles, fulano)

    def test_o_sobrenome_sozinho_ainda_casa_com_o_unico(self):
        andrade = self.db.member_id("Andrade")
        self.assertEqual(self.db.member_id("Alexandro Andrade"), andrade)

    def test_a_mesma_inicial_ainda_casa(self):
        # "Vieira E" e "Ericles de P Vieira" continuam a mesma pessoa
        ericles = self.db.member_id("Ericles de P Vieira")
        self.assertEqual(self.db.member_id("Vieira E", create=False), ericles)


class TestSepararAConta(BaseComFichas):
    """O conserto do que já aconteceu."""

    def setUp(self):
        super().setUp()
        # a ficha que virou de duas pessoas: o nome de um, o login do outro
        self.ericles = self.db.member_id("Ericles de P Vieira")
        self.db.conn.commit()
        auth.set_credentials(self.db, self.ericles, "fulano@udesc.br", SENHA, role="integrante")
        self.sessao = auth.login(self.db, "fulano@udesc.br", SENHA)
        ponto.entrar(self.db, self.ericles, atividade="lendo")
        self.db.conn.commit()

    def test_o_acesso_vai_para_a_ficha_nova_e_os_artigos_ficam(self):
        artigo = self.db.upsert("articles", {"title": "Um artigo", "title_key": "um_artigo", "status": "publicado"},
                                conflict=("title_key",))
        self.db.execute("INSERT INTO article_authors (article_id, member_id, author_name, author_order)"
                        " VALUES (?, ?, 'Vieira EP', 1)", (artigo, self.ericles))
        self.db.conn.commit()
        saida = auth.separar_conta(self.db, "fulano@udesc.br", "Fulano Vieira")
        nova = saida["para"]["id"]
        self.assertNotEqual(nova, self.ericles)
        self.assertEqual(self.ficha(nova)["login"], "fulano@udesc.br")
        self.assertIsNone(self.ficha(self.ericles)["login"])
        self.assertEqual(self.ficha(self.ericles)["full_name"], "Ericles de P Vieira")
        self.assertEqual(self.db.scalar("SELECT member_id FROM article_authors WHERE article_id = ?", (artigo,)),
                         self.ericles)
        self.assertEqual(saida["movidos"]["ponto"], 1)
        self.assertEqual(self.db.scalar("SELECT member_id FROM ponto"), nova)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM sessions WHERE member_id = ?", (nova,)), 1)

    def test_a_pessoa_continua_entrando_com_a_mesma_senha(self):
        auth.separar_conta(self.db, "fulano@udesc.br", "Fulano Vieira")
        sessao = auth.login(self.db, "fulano@udesc.br", SENHA)
        self.assertEqual(sessao["user"]["full_name"], "Fulano Vieira")

    def test_o_ponto_de_agora_sai_com_o_nome_certo(self):
        auth.separar_conta(self.db, "fulano@udesc.br", "Fulano Vieira")
        nomes = [p["quem"] for p in ponto.agora(self.db)]
        self.assertEqual(nomes, ["Fulano Vieira"])

    def test_login_desconhecido_e_nome_vazio_sao_recusados(self):
        with self.assertRaises(auth.AuthError):
            auth.separar_conta(self.db, "ninguem@udesc.br", "Alguém")
        with self.assertRaises(auth.AuthError):
            auth.separar_conta(self.db, "fulano@udesc.br", "  ")

    def test_fica_registrado(self):
        auth.separar_conta(self.db, "fulano@udesc.br", "Fulano Vieira")
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM audit_log WHERE action = 'conta_separada'"), 1)


class TestSepararPelaRedeEPelaTela(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "r.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Coordena", "coord@udesc.br", SENHA, role="coordenacao")
        cls.ericles = db.member_id("Ericles de P Vieira")
        db.conn.commit()
        auth.set_credentials(db, cls.ericles, "fulano@udesc.br", SENHA, role="integrante")
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
            data=json.dumps({"login": login, "senha": SENHA}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return (r.headers.get("Set-Cookie") or "").split(";")[0]

    def separar(self, cookie, corpo):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/equipe/separar",
            data=json.dumps(corpo).encode(),
            headers={"Content-Type": "application/json", "Cookie": cookie}, method="POST")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"{}")

    def test_o_integrante_nao_separa(self):
        status, _ = self.separar(self.entrar("fulano@udesc.br"), {"login": "fulano@udesc.br", "nome": "Fulano Vieira"})
        self.assertEqual(status, 403)

    def test_a_coordenacao_separa(self):
        status, corpo = self.separar(self.entrar("coord@udesc.br"), {"login": "fulano@udesc.br", "nome": "Fulano Vieira"})
        self.assertEqual(status, 200, corpo)
        self.assertEqual(corpo["para"]["nome"], "Fulano Vieira")
        self.assertEqual(corpo["de"]["id"], self.ericles)

    def test_a_tela_tem_o_conserto(self):
        fonte = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        self.assertIn('api("/api/equipe/separar", "POST", {login: sel.value, nome: nome.value.trim()})', fonte)
        self.assertIn("await desenharSepararConta(sepBox);", fonte)
        self.assertIn('(await api("/api/equipe/perfis")).contas', fonte)


if __name__ == "__main__":
    unittest.main()
