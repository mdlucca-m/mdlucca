#!/usr/bin/env python3
"""Testes do modo mural: a tela que fica ligada na sala.

    python3 -m unittest discover -s tests -v

O mural nao tem operador. Se ele quebrar, ninguem clica em nada para
consertar -- fica uma tela preta na parede ate alguem reparar. Por isso o
que se checa aqui e o que impede a tela de subir: marcador de modelo que
sobrou, dado que nao chegou, rota que nao responde e icone chamado por um
nome que nao existe no conjunto.
"""
from __future__ import annotations

import json
import re
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

from lape import api, auth, metrics, report  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class _SemRedirecionar(urllib.request.HTTPRedirectHandler):
    """Entrega o 302 em vez de segui-lo."""

    def redirect_request(self, *args, **kwargs):
        return None


class TestMontagemDoMural(unittest.TestCase):
    """A pagina sai inteira do renderizador, sem depender de rede."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = Database(Path(cls.tmp.name) / "mural.sqlite")
        db.migrate()
        cls.html = report.render_mural(metrics.build_payload(db))
        db.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_nenhum_marcador_sobrou(self):
        # um "__DATA__" na pagina publicada seria a tela em branco na parede
        for marcador in ("__TITLE__", "__THEME_CSS__", "__ICONS_JS__",
                         "__CHARTS_JS__", "__SCRIPT__", "__DATA__"):
            self.assertNotIn(marcador, self.html, f"marcador {marcador} nao foi substituido")

    def test_leva_tudo_embutido(self):
        self.assertIn("const Icons", self.html)
        self.assertIn("const Charts", self.html)
        self.assertIn("const ROTEIRO", self.html)
        self.assertIn("--surface-sunken", self.html)

    def test_o_dado_e_json_valido(self):
        bruto = re.search(
            r'<script id="payload" type="application/json">(.*?)</script>',
            self.html, re.S).group(1)
        dado = json.loads(bruto.replace("<\\/", "</"))
        self.assertIn("overview", dado)
        self.assertIn("agenda", dado)
        self.assertIn("research_lines", dado)

    def test_o_banco_vazio_nao_derruba_a_montagem(self):
        # laboratorio recem-instalado: zero artigos, zero eventos, e a tela sobe
        self.assertIn("Agora no laboratório", self.html)


class TestIconesChamadosPeloMural(unittest.TestCase):
    """Todo icone pedido pelo mural existe no conjunto.

    `Icons.get` de um nome desconhecido devolve um ponto discreto em vez de
    quebrar -- o que e bom para a pagina e pessimo para quem revisa: o erro
    de digitacao passa despercebido ate alguem notar a bolinha na tela.
    """

    def nomes_do_conjunto(self) -> set[str]:
        fonte = (TEMPLATES / "icons.js").read_text(encoding="utf-8")
        corpo = fonte.split("const SET = {", 1)[1].split("\n  };", 1)[0]
        return set(re.findall(r"^\s{4}([A-Za-z][A-Za-z0-9]*):\s*\[", corpo, re.M))

    def test_o_conjunto_foi_lido(self):
        nomes = self.nomes_do_conjunto()
        self.assertIn("painel", nomes)
        self.assertGreater(len(nomes), 40)

    def test_todo_icone_pedido_existe(self):
        nomes = self.nomes_do_conjunto()
        for arquivo in ("mural.js", "dashboard.js"):
            texto = (TEMPLATES / arquivo).read_text(encoding="utf-8")
            pedidos = set(re.findall(r'Icons\.(?:get|badge)\("([A-Za-z0-9]+)"', texto))
            faltando = pedidos - nomes
            self.assertEqual(faltando, set(),
                             f"icone inexistente em {arquivo}: {sorted(faltando)}")

    def test_todo_tom_tem_regra_no_tema(self):
        # a pastilha e cromo: o tom precisa existir como classe, senao a cor
        # cai no acento e dois cartoes diferentes ficam iguais
        fonte = (TEMPLATES / "icons.js").read_text(encoding="utf-8")
        tons = set(re.findall(r':\s*"([a-z]+)",', fonte.split("const TOM = {", 1)[1]
                              .split("\n  };", 1)[0]))
        tema = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
        for tom in tons:
            self.assertIn(f".ibadge.t-{tom}", tema, f"tom sem regra no tema: {tom}")


class TestRotaDoMural(unittest.TestCase):
    """A rota responde, e responde protegida como o painel."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "api.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Coordenação", "coord@udesc.br", "senhaforte123",
                            role="admin")
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

    def buscar(self, caminho, cookie=None, seguir=True):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}{caminho}")
        if cookie:
            pedido.add_header("Cookie", f"{api.COOKIE_NAME}={cookie}")
        # sem `seguir`, o urllib segue o 302 sozinho e o teste enxergaria o 200
        # do login -- exatamente o contrario do que ele quer provar
        abridor = (urllib.request.build_opener() if seguir
                   else urllib.request.build_opener(_SemRedirecionar))
        try:
            with abridor.open(pedido, timeout=30) as resposta:
                return resposta.status, resposta.read().decode(), resposta
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode(), exc

    def entrar(self):
        corpo = json.dumps({"login": "coord@udesc.br", "senha": "senhaforte123"}).encode()
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login", data=corpo, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return (resposta.headers.get("Set-Cookie") or "").split("=")[1].split(";")[0]

    def test_sem_sessao_o_mural_manda_entrar(self):
        # a tela da sala mostra dado interno: sem cookie, vai para o login
        status, _, resposta = self.buscar("/mural", seguir=False)
        self.assertIn(status, (302, 303))
        self.assertEqual(resposta.headers.get("Location"), "/entrar")

    def test_com_sessao_a_tela_vem_inteira(self):
        status, corpo, _ = self.buscar("/mural", cookie=self.entrar())
        self.assertEqual(status, 200)
        self.assertIn("const ROTEIRO", corpo)
        self.assertNotIn("__DATA__", corpo)

    def test_tv_e_o_mesmo_endereco(self):
        status, corpo, _ = self.buscar("/tv", cookie=self.entrar())
        self.assertEqual(status, 200)
        self.assertIn("const ROTEIRO", corpo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
