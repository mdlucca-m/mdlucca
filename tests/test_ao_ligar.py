#!/usr/bin/env python3
"""Subir sozinho ao ligar o computador, pela tela.

    python3 -m unittest tests.test_ao_ligar -v

O agendamento já existia nos dois `.bat`. O que se cobra aqui é o botão:
que ele diga a verdade sobre o que está valendo agora (inclusive quando o
Windows caiu no atalho em vez da tarefa agendada), que ele chame o MESMO
script que os `.bat` chamam, e que uma recusa da máquina chegue como
recado e não como erro do sistema.

Nada aqui roda no Windows de verdade: o que o sistema operacional
responderia é substituído, e o que se verifica é a decisão que o sistema
toma com a resposta.
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

from lape import aoligar, api, auth  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class BaseFingindoWindows(unittest.TestCase):
    def trocar(self, modulo, nome, valor):
        antigo = getattr(modulo, nome)
        setattr(modulo, nome, valor)
        self.addCleanup(setattr, modulo, nome, antigo)

    def windows(self, *, tarefa=False, atalho=False):
        """Um Windows de mentira, com as duas formas de agendar."""
        self.trocar(aoligar, "_e_windows", lambda: True)
        self.rodados = []

        def rodar(comando):
            self.rodados.append(comando)
            if comando[0] == "schtasks":
                return (0 if self.tarefa else 1), ""
            return 0, "Pronto."

        self.tarefa = tarefa
        self.atalho = atalho
        self.trocar(aoligar, "_rodar", rodar)
        pasta = Path(tempfile.mkdtemp())
        self.trocar(aoligar, "_pasta_inicializar", lambda: pasta)
        if atalho:
            (pasta / aoligar.NOME_DO_ATALHO).write_text("atalho", encoding="utf-8")
        self.pasta = pasta


class TestOQueOSistemaVe(BaseFingindoWindows):

    def test_fora_do_windows_nao_finge_que_da(self):
        self.trocar(aoligar, "_e_windows", lambda: False)
        d = aoligar.situacao()
        self.assertFalse(d["windows"])
        self.assertFalse(d["ligado"])
        self.assertIn("Windows", d["aviso"])

    def test_a_tarefa_agendada_conta(self):
        self.windows(tarefa=True)
        d = aoligar.situacao()
        self.assertTrue(d["ligado"])
        self.assertEqual(d["como"], "tarefa")

    def test_o_ATALHO_tambem_conta(self):
        """Ver só a tarefa diria "desligado" com o sistema subindo sozinho.

        E quem lesse isso ligaria de novo, ficando com dois LAPE
        tentando subir na mesma porta.
        """
        self.windows(tarefa=False, atalho=True)
        d = aoligar.situacao()
        self.assertTrue(d["ligado"])
        self.assertEqual(d["como"], "atalho")

    def test_sem_nenhum_dos_dois_esta_desligado(self):
        self.windows()
        d = aoligar.situacao()
        self.assertFalse(d["ligado"])
        self.assertIsNone(d["como"])

    def test_procura_a_tarefa_pelo_nome_que_o_script_registra(self):
        """Nome diferente do registrado = "desligado" para sempre."""
        self.windows()
        aoligar.situacao()
        chamada = next(c for c in self.rodados if c[0] == "schtasks")
        self.assertIn(aoligar.NOME_DA_TAREFA, chamada)
        ps1 = (ROOT / "deploy" / "publicar.ps1").read_text(encoding="utf-8",
                                                           errors="replace")
        self.assertIn(f'"{aoligar.NOME_DA_TAREFA}"', ps1)


class TestLigarEDesligar(BaseFingindoWindows):

    def test_ligar_chama_o_MESMO_script_do_bat(self):
        """Um segundo jeito de agendar divergiria do .bat na primeira mexida."""
        self.windows()
        self.tarefa = True          # o Windows aceita, e passa a existir
        saida = aoligar.definir(True)
        self.assertTrue(saida["ok"])
        comando = self.rodados[-1] if self.rodados[-1][0] != "schtasks" else self.rodados[-2]
        self.assertIn("powershell", comando[0])
        self.assertIn("-AoLigar", comando)
        self.assertTrue(any(c.endswith("publicar.ps1") for c in comando))

    def test_desligar_manda_o_outro_sinal(self):
        self.windows(tarefa=True)
        self.tarefa = False
        saida = aoligar.definir(False)
        self.assertTrue(saida["ok"])
        comando = [c for c in self.rodados if c[0] != "schtasks"][-1]
        self.assertIn("-NaoAoLigar", comando)

    def test_confere_DEPOIS_em_vez_de_confiar_no_codigo_de_saida(self):
        """O publicar.ps1 sai com zero mesmo quando cai no atalho.

        Sem reler o estado, a tela diria "agendado" tendo acontecido
        outra coisa -- ou nada.
        """
        self.windows()
        self.tarefa = False         # o comando "deu certo" e nada mudou
        saida = aoligar.definir(True)
        self.assertFalse(saida["ok"])
        self.assertIn("não mudou", saida["recado"])

    def test_a_recusa_do_windows_vira_recado_com_o_que_ele_disse(self):
        self.windows()

        def rodar(comando):
            if comando[0] == "schtasks":
                return 1, ""
            return 1, "Acesso negado."

        self.trocar(aoligar, "_rodar", rodar)
        saida = aoligar.definir(True)
        self.assertFalse(saida["ok"])
        self.assertIn("Acesso negado", saida["recado"])

    def test_nada_do_que_vem_de_fora_entra_no_comando(self):
        """Lista de argumentos, e nunca `shell=True`.

        A conferência é pela ÁRVORE do código, e não por procurar o texto
        "shell=True" no arquivo: o próprio comentário que explica por que
        não usá-lo contém essa palavra, e um teste que lê prosa reprova o
        comentário em vez do código. Já aconteceu nesta casa.
        """
        import ast

        fonte = (ROOT / "scripts" / "lape" / "aoligar.py").read_text(encoding="utf-8")
        chamadas = [n for n in ast.walk(ast.parse(fonte))
                    if isinstance(n, ast.Call)
                    and ast.unparse(n.func) == "subprocess.run"]
        self.assertTrue(chamadas, "ninguém está rodando nada")
        for chamada in chamadas:
            with self.subTest(linha=chamada.lineno):
                shell = [k for k in chamada.keywords if k.arg == "shell"]
                self.assertFalse(shell, "shell=True interpreta a linha pelo cmd")
                self.assertTrue(chamada.args, "o comando tem de ser uma lista")


class TestPelaRede(unittest.TestCase):
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
        status, _ = self.chamar("/api/ao-ligar", self.entrar("loiane@udesc.br"))
        self.assertEqual(status, 403)

    def test_a_coordenacao_ve_a_situacao(self):
        status, corpo = self.chamar("/api/ao-ligar", self.entrar("coord@udesc.br"))
        self.assertEqual(status, 200)
        self.assertIn("ligado", corpo)
        self.assertIn("windows", corpo)

    def test_sem_dizer_ligar_ou_desligar_e_recusado(self):
        status, corpo = self.chamar("/api/ao-ligar", self.entrar("coord@udesc.br"),
                                    {})
        self.assertEqual(status, 400)
        self.assertIn("ligar", corpo["error"])

    def test_a_maquina_recusar_e_409_e_nao_500(self):
        """O pedido está certo; quem recusou foi o Windows.

        500 mandaria procurar defeito no sistema, quando o que há é uma
        política da máquina -- e aqui, no Linux da suíte, nem Windows é.
        """
        status, corpo = self.chamar("/api/ao-ligar", self.entrar("coord@udesc.br"),
                                    {"ligar": True})
        self.assertEqual(status, 409)
        self.assertTrue(corpo["error"])


class TestOBotaoNaTela(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        cls.trecho = cls.html[cls.html.index("async function subirSozinho"):]
        cls.trecho = cls.trecho[:cls.trecho.index("async function perfilDeAcesso")]

    def test_o_botao_esta_na_administracao(self):
        admin = self.html[self.html.index("VIEWS.admin = {"):]
        admin = admin[:admin.index("const ICONE")]
        self.assertIn("subirSozinho()", admin)

    def test_fora_do_windows_a_tela_explica_em_vez_de_mostrar_o_botao(self):
        self.assertIn("if (!d.windows)", self.trecho)
        self.assertIn("d.aviso", self.trecho)

    def test_a_tela_distingue_a_tarefa_do_atalho(self):
        """São dois agendamentos diferentes, e um deles não se reergue."""
        self.assertIn('x.como === "tarefa"', self.trecho)
        self.assertIn("Inicializar", self.trecho)

    def test_o_que_o_windows_respondeu_aparece(self):
        self.assertIn("r.recado", self.trecho)


if __name__ == "__main__":
    unittest.main()
