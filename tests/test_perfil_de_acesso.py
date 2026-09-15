#!/usr/bin/env python3
"""Testes do perfil de PERMISSAO -- que nao e o vinculo academico.

    python3 -m unittest tests.test_perfil_de_acesso -v

O sistema tem duas colunas de nome parecido em `members`, e confundi-las
custou tres defeitos nesta mesma semana:

  `user_role`  o perfil de permissao: leitura, integrante, coordenacao, admin
  `role`       o VINCULO academico: Professor(a), Mestrando(a), Bolsista

A lista de vinculo tem a opcao "Coordenação". Quem a marcasse acreditaria
ter dado acesso -- e o vinculo e o cargo na equipe, nao permite nada.

Estes testes entram pela ROTA, com sessao de verdade. Testar so a funcao
nao pega a troca de coluna: foi exatamente assim que ela passou.
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

from lape import api, auth, mapping  # noqa: E402
from lape.db import Database  # noqa: E402

SENHA = "SenhaDeTeste987!"


class BaseDasContas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "perfis.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        cls.chefe = auth.create_account(db, "Chefe", "chefe@udesc.br", SENHA,
                                        role="admin")["member_id"]
        cls.par = auth.create_account(db, "Par de coordenação", "par@udesc.br", SENHA,
                                      role="coordenacao")["member_id"]
        cls.gente = auth.create_account(db, "Integrante", "gente@udesc.br", SENHA,
                                        role="integrante")["member_id"]
        # ficha SEM conta: perfil nela e um numero que nao governa nada
        cls.sem_conta = db.insert("members", {
            "full_name": "Ficha sem login", "name_key": "ficha-sem-login"})
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
        corpo = json.dumps({"login": login, "senha": SENHA}).encode()
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login", data=corpo, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return (r.headers.get("Set-Cookie") or "").split("=")[1].split(";")[0]

    def mudar(self, cookie, alvo, perfil):
        corpo = json.dumps({"user_role": perfil}).encode()
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/equipe/{alvo}/perfil",
            data=corpo, method="POST",
            headers={"Cookie": f"{api.COOKIE_NAME}={cookie}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"{}")

    def perfil_de(self, member_id):
        db = Database(self.db_path)
        try:
            return db.scalar("SELECT user_role FROM members WHERE id = ?", (member_id,))
        finally:
            db.close()


class TestMudarOPerfil(BaseDasContas):

    def test_a_coordenacao_promove_e_o_banco_guarda(self):
        status, corpo = self.mudar(self.entrar("chefe@udesc.br"), self.gente,
                                   "coordenacao")
        self.assertEqual(status, 200)
        self.assertEqual(corpo["user_role"], "coordenacao")
        self.assertEqual(corpo["antes"], "integrante")
        self.assertEqual(self.perfil_de(self.gente), "coordenacao")
        # e volta, para os outros testes desta classe
        self.mudar(self.entrar("chefe@udesc.br"), self.gente, "integrante")

    def test_integrante_nao_muda_perfil_de_ninguem(self):
        status, _ = self.mudar(self.entrar("gente@udesc.br"), self.par, "leitura")
        self.assertEqual(status, 403)
        self.assertEqual(self.perfil_de(self.par), "coordenacao")

    def test_ninguem_muda_o_proprio_perfil(self):
        """Sem isto, quem tem coordenacao se promove a admin sozinho.

        E quem se rebaixa por engano nao tem como voltar: nao ha quem o
        promova se ele era o unico.
        """
        status, corpo = self.mudar(self.entrar("par@udesc.br"), self.par, "admin")
        self.assertEqual(status, 403)
        self.assertIn("próprio perfil", corpo["error"])
        self.assertEqual(self.perfil_de(self.par), "coordenacao")

    def test_ninguem_da_perfil_acima_do_proprio(self):
        """Coordenacao criando admin e coordenacao virando admin pela porta
        do lado: basta promover um aliado e pedir a ele."""
        status, corpo = self.mudar(self.entrar("par@udesc.br"), self.gente, "admin")
        self.assertEqual(status, 403)
        self.assertIn("acima do seu", corpo["error"])
        self.assertEqual(self.perfil_de(self.gente), "integrante")

    def test_perfil_desconhecido_e_recusado(self):
        for ruim in ("dono", "COORDENACAO", "", "root"):
            with self.subTest(perfil=ruim):
                status, _ = self.mudar(self.entrar("chefe@udesc.br"), self.gente, ruim)
                self.assertEqual(status, 400)

    def test_ficha_sem_conta_nao_recebe_perfil(self):
        """Perfil em ficha sem login e um numero que nao governa nada.

        E da a impressao de acesso concedido, que e o pior dos dois.
        """
        status, corpo = self.mudar(self.entrar("chefe@udesc.br"),
                                   self.sem_conta, "coordenacao")
        self.assertEqual(status, 400)
        self.assertIn("não tem conta", corpo["error"])

    def test_pessoa_que_nao_existe_responde_404(self):
        status, _ = self.mudar(self.entrar("chefe@udesc.br"), 999999, "leitura")
        self.assertEqual(status, 404)

    def test_a_mudanca_fica_no_log_de_auditoria(self):
        """Daqui a seis meses alguem vai perguntar quem deu esse acesso."""
        self.mudar(self.entrar("chefe@udesc.br"), self.gente, "coordenacao")
        db = Database(self.db_path)
        try:
            linhas = db.dicts(
                "SELECT action, detail FROM audit_log WHERE action = 'perfil_de_acesso'"
                " ORDER BY id DESC LIMIT 1")
        finally:
            db.close()
        self.assertTrue(linhas)
        self.assertIn("integrante -> coordenacao", linhas[0]["detail"])
        self.mudar(self.entrar("chefe@udesc.br"), self.gente, "integrante")

    def test_a_lista_traz_so_quem_tem_conta(self):
        cookie = self.entrar("chefe@udesc.br")
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/equipe/perfis",
            headers={"Cookie": f"{api.COOKIE_NAME}={cookie}"})
        with urllib.request.urlopen(pedido, timeout=30) as r:
            contas = json.loads(r.read())["contas"]
        nomes = {c["full_name"] for c in contas}
        self.assertIn("Chefe", nomes)
        self.assertNotIn("Ficha sem login", nomes)
        for c in contas:
            with self.subTest(pessoa=c["full_name"]):
                # a tela mostra os DOIS lado a lado: e a confusao entre eles
                # que faz alguem achar que ja deu acesso
                self.assertIn("user_role", c)
                self.assertIn("role", c)


class TestAsDuasTravasJuntas(BaseDasContas):
    """O laboratorio nao pode ficar sem ninguem que de acesso a alguem."""

    def test_a_trava_da_ultima_coordenacao_hoje_nao_dispara(self):
        """E ela e inalcancavel DE PROPOSITO, nao por descuido.

        Quem rebaixa precisa de coordenacao e nao pode se rebaixar, entao
        sobra sempre ele: a conta nunca chega a zero por esta rota. A trava
        fica porque a outra e uma escolha, e nao uma lei -- no dia em que
        alguem permitir mudar o proprio perfil, o travamento de fora volta
        na hora.

        O que este teste guarda e a INVARIANTE, e nao o caminho: depois de
        qualquer rebaixamento aceito, ainda existe conta que manda.
        """
        cookie = self.entrar("chefe@udesc.br")
        status, _ = self.mudar(cookie, self.par, "integrante")
        self.assertEqual(status, 200)
        db = Database(self.db_path)
        try:
            manda = db.scalar(
                "SELECT COUNT(*) FROM members WHERE login IS NOT NULL"
                "   AND user_role IN ('coordenacao', 'admin')")
        finally:
            db.close()
        self.assertGreaterEqual(manda, 1, "ficou sem ninguém que dê acesso")
        self.mudar(cookie, self.par, "coordenacao")

    def test_a_trava_esta_escrita_e_diz_que_nao_dispara(self):
        """Codigo defensivo inalcancavel sem explicacao se le como descuido.

        A proxima pessoa o apagaria -- e ela estaria certa, se nao houvesse
        o comentario dizendo para que ele serve.
        """
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        trecho = fonte[fonte.index("def route_perfil_de_acesso"):]
        trecho = trecho[:trecho.index("\ndef ")]
        self.assertIn("HOJE NAO DISPARA", trecho)
        self.assertIn("última conta com coordenação", trecho)


class TestPermissaoNaoEhCampoDeCadastro(unittest.TestCase):
    """`user_role` nao entra por planilha nem por cadastro.

    O mapeador casava `user_role` com o campo `role` pela correspondencia
    parcial ("user_role" contem "role"), que existe para cabecalho de
    planilha baguncado. Nao havia escalada -- `user_role` nao era escrito,
    e sim `role` --, e sim algo pior de achar: quem mandasse
    `user_role: "admin"` recebia "gravado", o VINCULO da pessoa virava
    "admin" (que nao existe na lista de vinculos) e a permissao nao mudava
    nada.
    """

    def test_o_mapeador_ignora_a_coluna_de_permissao(self):
        self.assertEqual(mapping.build_column_map("members", ["user_role"]), {})

    def test_o_vinculo_continua_entrando_pelos_apelidos_dele(self):
        for cabecalho in ("role", "funcao", "vinculo", "papel", "cargo"):
            with self.subTest(cabecalho=cabecalho):
                self.assertEqual(
                    mapping.build_column_map("members", [cabecalho]).get(cabecalho),
                    "role")

    def test_login_e_senha_tambem_ficam_fora(self):
        for cabecalho in ("login", "password_hash", "must_change_password"):
            with self.subTest(cabecalho=cabecalho):
                self.assertEqual(mapping.build_column_map("members", [cabecalho]), {})

    def test_a_lista_de_protegidas_e_declarada_e_nao_espalhada(self):
        self.assertIn("user_role", mapping.PROTEGIDAS["members"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
