#!/usr/bin/env python3
"""Atualizar o sistema pelo botão da tela, sem abrir o CMD.

    python3 -m unittest tests.test_atualizar -v

O que se cobra aqui: que o botão chame o MESMO publicar.ps1 que o .bat
chama, sem flag nenhuma (o script decide o modo sozinho pelo que já está
gravado); que a chamada nunca use shell=True nem espere o processo
terminar (o worker que atende o clique é o mesmo que a troca de verdade
derruba); e que só a coordenação possa disparar, porque é uma ação que
reinicia o serviço para todo mundo.

Nada aqui roda um PowerShell de verdade: o que o sistema operacional
faria é substituído, e o que se verifica é a decisão que o código toma.
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

from lape import api, atualizar, auth  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class BaseFingindoWindowsParaAtualizar(unittest.TestCase):
    def trocar(self, modulo, nome, valor):
        antigo = getattr(modulo, nome)
        setattr(modulo, nome, valor)
        self.addCleanup(setattr, modulo, nome, antigo)

    def windows(self):
        self.trocar(atualizar, "_e_windows", lambda: True)
        self.disparados = []
        self.trocar(atualizar, "_disparar", lambda comando: self.disparados.append(comando))


class TestDisparar(BaseFingindoWindowsParaAtualizar):

    def test_fora_do_windows_nao_finge_que_da(self):
        self.trocar(atualizar, "_e_windows", lambda: False)
        saida = atualizar.disparar()
        self.assertFalse(saida["ok"])
        self.assertIn("Windows", saida["recado"])

    def test_no_windows_chama_o_MESMO_script_do_bat_sem_flag(self):
        """Um segundo jeito de escolher o modo divergiria do .bat na
        primeira vez que alguém mexesse só num dos dois."""
        self.windows()
        saida = atualizar.disparar()
        self.assertTrue(saida["ok"])
        self.assertEqual(len(self.disparados), 1)
        comando = self.disparados[0]
        self.assertIn("powershell", comando[0])
        self.assertTrue(any(c.endswith("publicar.ps1") for c in comando))
        for flag in ("-Fixo", "-Permanente", "-Sorteado", "-AoLigar", "-NaoAoLigar"):
            self.assertNotIn(flag, comando)

    def test_pasta_do_deploy_sumida_vira_recado_e_nao_excecao(self):
        self.windows()
        self.trocar(atualizar, "_publicar_ps1", lambda: Path("/nao/existe/publicar.ps1"))
        saida = atualizar.disparar()
        self.assertFalse(saida["ok"])
        self.assertIn("não encontrei", saida["recado"])
        self.assertEqual(self.disparados, [])

    def test_falha_ao_soltar_o_processo_vira_recado_e_nao_excecao(self):
        self.windows()

        def explode(comando):
            raise OSError("recusado")

        self.trocar(atualizar, "_disparar", explode)
        saida = atualizar.disparar()
        self.assertFalse(saida["ok"])
        self.assertIn("recusado", saida["recado"])

    def test_nao_usa_shell_true_nem_espera_o_processo(self):
        """A conferência é pela ÁRVORE do código, não por procurar texto:
        um comentário explicando por que não usar shell=True conteria a
        própria palavra e enganaria um teste que lê prosa."""
        import ast

        fonte = (ROOT / "scripts" / "lape" / "atualizar.py").read_text(encoding="utf-8")
        arvore = ast.parse(fonte)
        chamadas = [n for n in ast.walk(arvore) if isinstance(n, ast.Call)]
        populares = [n for n in chamadas if ast.unparse(n.func) == "subprocess.Popen"]
        self.assertTrue(populares, "ninguém está soltando processo nenhum")
        for chamada in populares:
            with self.subTest(linha=chamada.lineno):
                shell = [k for k in chamada.keywords if k.arg == "shell"]
                self.assertFalse(shell, "shell=True interpreta a linha pelo cmd")
                self.assertTrue(chamada.args, "o comando tem de ser uma lista")
        esperados = [n for n in chamadas if ast.unparse(n.func) in
                     ("subprocess.run", "subprocess.call", "subprocess.check_call",
                      "subprocess.check_output", "proc.wait", "p.wait")]
        self.assertFalse(esperados, "disparar() não pode esperar o processo terminar")


class TestPelaRedeAtualizar(unittest.TestCase):
    """Quem pode apertar, e o que a rota responde quando a máquina recusa."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "l.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Alexandro Andrade", "coord@udesc.br",
                            "senhaforte123", role="coordenacao")
        auth.create_account(db, "Loiane", "loiane@udesc.br", "senhaforte123",
                            role="integrante")
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

    def chamar(self, caminho, cookie=None, corpo=None):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{caminho}",
            data=json.dumps(corpo).encode() if corpo is not None else None,
            headers={"Content-Type": "application/json",
                     **({"Cookie": cookie} if cookie else {})},
            method="POST" if corpo is not None else "GET")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"{}")

    def test_o_integrante_nao_mexe_na_maquina(self):
        """Mexe na MÁQUINA, e não no banco: é decisão da coordenação."""
        status, _ = self.chamar("/api/sistema/atualizar", self.entrar("loiane@udesc.br"), {})
        self.assertEqual(status, 403)

    def test_visitante_sem_login_nem_chega_perto(self):
        status, _ = self.chamar("/api/sistema/atualizar", None, {})
        self.assertIn(status, (401, 403))

    def test_a_maquina_recusar_e_409_e_nao_500(self):
        """O pedido está certo; quem recusou foi o sistema operacional --
        500 mandaria procurar defeito no sistema, quando o que há é o
        Linux da suíte não sendo Windows."""
        status, corpo = self.chamar("/api/sistema/atualizar", self.entrar("coord@udesc.br"), {})
        self.assertEqual(status, 409)
        self.assertTrue(corpo["error"])


class TestOBotaoAtualizarNaTela(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        cls.trecho = cls.html[cls.html.index("async function atualizarSistema"):]
        cls.trecho = cls.trecho[:cls.trecho.index("async function perfilDeAcesso")]

    def test_o_botao_esta_na_administracao(self):
        admin = self.html[self.html.index("VIEWS.admin = {"):]
        admin = admin[:admin.index("const ICONE")]
        self.assertIn("atualizarSistema()", admin)

    def test_chama_a_rota_certa(self):
        self.assertIn("/api/sistema/atualizar", self.trecho)

    def test_acompanha_a_troca_em_vez_de_dizer_pronto_na_hora(self):
        """Sem acompanhar /api/health, o botão diria "pronto" no instante
        em que só o PEDIDO foi aceito -- antes de a troca acontecer."""
        self.assertIn("/api/health", self.trecho)
        self.assertIn("location.reload", self.trecho)

    def test_tem_um_teto_para_nao_esperar_para_sempre(self):
        self.assertIn("TENTATIVAS", self.trecho)


if __name__ == "__main__":
    unittest.main()
