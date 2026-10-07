#!/usr/bin/env python3
"""Testes da aba privada "Apresentação: Humor na Ginástica Rítmica".

    python3 -m unittest tests.test_apresentacao_humor -v

Pedido do Mateus: "crie essa apresentação no painel do lape somente para
quem eu autorizar". O que se cobra aqui é o mesmo da ginástica rítmica
(ver test_ginastica_ritmica.py) -- em vez de "todo integrante lê isto", é
"ninguém lê isto a menos que tenha sido autorizado por nome", e uma aba
de verdade privada não pode nem CONFIRMAR que existe para quem não foi
autorizado.
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

from lape import apresentacao_humor, api, auth  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseApresentacaoHumor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.mateus = self.db.member_id("Mateus Lucca")
        self.maria_helena = self.db.member_id("Maria Helena")
        self.alheio = self.db.member_id("Alguem De Fora")


class TestAcessoApresentacaoHumor(BaseApresentacaoHumor):
    def test_ninguem_tem_acesso_por_padrao(self):
        self.assertFalse(apresentacao_humor.tem_acesso(self.db, self.mateus))

    def test_admin_sempre_tem_acesso_mesmo_sem_autorizacao(self):
        self.assertTrue(apresentacao_humor.tem_acesso(self.db, self.alheio, user_role="admin"))

    def test_conceder_da_acesso(self):
        apresentacao_humor.conceder(self.db, self.mateus, concedido_por=self.mateus)
        self.assertTrue(apresentacao_humor.tem_acesso(self.db, self.mateus))

    def test_conceder_duas_vezes_nao_quebra(self):
        apresentacao_humor.conceder(self.db, self.mateus, concedido_por=self.mateus)
        apresentacao_humor.conceder(self.db, self.mateus, concedido_por=self.mateus)
        self.assertTrue(apresentacao_humor.tem_acesso(self.db, self.mateus))

    def test_revogar_tira_o_acesso(self):
        apresentacao_humor.conceder(self.db, self.maria_helena, concedido_por=self.mateus)
        apresentacao_humor.revogar(self.db, self.maria_helena)
        self.assertFalse(apresentacao_humor.tem_acesso(self.db, self.maria_helena))

    def test_quem_tem_acesso_lista_os_autorizados(self):
        apresentacao_humor.conceder(self.db, self.mateus, concedido_por=self.mateus)
        apresentacao_humor.conceder(self.db, self.maria_helena, concedido_por=self.mateus)
        nomes = sorted(p["full_name"] for p in apresentacao_humor.quem_tem_acesso(self.db))
        self.assertEqual(nomes, ["Maria Helena", "Mateus Lucca"])


class TestConteudoDosSlides(unittest.TestCase):
    """Integridade da síntese: nenhum número nos slides pode contradizer
    os outros -- a mesma régua usada no resto do sistema (ver ana.py,
    ginastica_ritmica.py): um número que não bate é pior que nenhum."""

    def test_total_de_estudos_por_tema_soma_vinte_e_cinco(self):
        arvore = next(s for s in apresentacao_humor.SLIDES if s["tipo"] == "arvore")
        self.assertEqual(sum(f["n"] for f in arvore["folhas"]), 25)

    def test_funil_termina_em_vinte_e_cinco_estudos(self):
        funil = next(s for s in apresentacao_humor.SLIDES if s["tipo"] == "funil")
        self.assertEqual(funil["passos"][-1]["numero"], "25")

    def test_dendrograma_soma_vinte_e_cinco_e_bate_com_as_folhas(self):
        dendro = next(s for s in apresentacao_humor.SLIDES if s["tipo"] == "dendrograma")
        self.assertEqual(sum(c["n"] for c in dendro["clusters"]), 25)
        for cluster in dendro["clusters"]:
            self.assertEqual(sum(f["n"] for f in cluster["folhas"]), cluster["n"])

    def test_slides_de_achado_batem_com_as_folhas_da_arvore(self):
        arvore = next(s for s in apresentacao_humor.SLIDES if s["tipo"] == "arvore")
        achados = [s for s in apresentacao_humor.SLIDES if s["tipo"] == "achado"]
        self.assertEqual(len(achados), len(arvore["folhas"]))
        self.assertEqual(sorted(a["n"] for a in achados), sorted(f["n"] for f in arvore["folhas"]))

    def test_listar_slides_devolve_copia_nao_a_tupla_original(self):
        copia = apresentacao_humor.listar_slides()
        copia[0]["titulo"] = "alterado só na cópia"
        self.assertNotEqual(apresentacao_humor.SLIDES[0]["titulo"], "alterado só na cópia")


class TestRotasDaAbaPrivadaApresentacaoHumor(unittest.TestCase):
    """O que a rota devolve para quem tem acesso, e o que ela NUNCA revela
    para quem não tem."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "t.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Mateus Lucca", "mateus@udesc.br", "senhaforte123",
                            role="admin")
        auth.create_account(db, "Maria Helena", "maria@udesc.br", "senhaforte123",
                            role="integrante")
        auth.create_account(db, "Alguem De Fora", "fora@udesc.br", "senhaforte123",
                            role="coordenacao")
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

    def entrar_no_sistema(self, login):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"login": login, "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return r.headers.get("Set-Cookie", "").split(";")[0]

    def chamar(self, caminho, cookie=None, metodo="GET", corpo=None):
        dados = json.dumps(corpo or {}).encode() if metodo in ("POST",) or corpo is not None else None
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}{caminho}",
                                        data=dados, method=metodo)
        if cookie:
            pedido.add_header("Cookie", cookie)
        if dados:
            pedido.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            return exc.code, {}

    def setUp(self):
        self.mateus = self.entrar_no_sistema("mateus@udesc.br")
        self.maria = self.entrar_no_sistema("maria@udesc.br")
        self.fora = self.entrar_no_sistema("fora@udesc.br")

    def test_admin_ve_os_slides_mesmo_sem_autorizacao_explicita(self):
        status, dados = self.chamar("/api/apresentacao-humor", self.mateus)
        self.assertEqual(status, 200)
        self.assertIsInstance(dados["slides"], list)
        self.assertTrue(dados["slides"])

    def test_quem_nao_foi_autorizado_recebe_nao_encontrado_nao_403(self):
        # uma aba de verdade privada nao confirma nem que existe -- 404,
        # nao 403 (que diria "existe, mas voce nao pode")
        status, _ = self.chamar("/api/apresentacao-humor", self.fora)
        self.assertEqual(status, 404)

    def test_coordenacao_sozinha_nao_basta_sem_autorizacao(self):
        status, _ = self.chamar("/api/apresentacao-humor/acesso", self.fora)
        self.assertEqual(status, 404)

    def test_admin_autoriza_alguem_e_o_autorizado_passa_a_ver(self):
        maria_id = self.chamar("/api/auth/me", self.maria)[1]["id"]
        status, resultado = self.chamar("/api/apresentacao-humor/acesso", self.mateus,
                                        "POST", {"member_id": maria_id})
        self.assertEqual(status, 200)
        self.assertEqual(len(resultado["items"]), 1)

        status, dados = self.chamar("/api/apresentacao-humor", self.maria)
        self.assertEqual(status, 200)

    def test_me_traz_a_flag_de_acesso(self):
        _, dados = self.chamar("/api/auth/me", self.mateus)
        self.assertTrue(dados["acesso_apresentacao_humor"])
        _, dados = self.chamar("/api/auth/me", self.fora)
        self.assertFalse(dados["acesso_apresentacao_humor"])

    def test_revoga_o_acesso_de_quem_foi_autorizado(self):
        maria_id = self.chamar("/api/auth/me", self.maria)[1]["id"]
        self.chamar("/api/apresentacao-humor/acesso", self.mateus, "POST",
                   {"member_id": maria_id})
        status, _ = self.chamar(f"/api/apresentacao-humor/acesso/{maria_id}",
                                self.mateus, "DELETE")
        self.assertEqual(status, 200)
        self.assertEqual(self.chamar("/api/apresentacao-humor", self.maria)[0], 404)

    def test_sem_entrar_no_sistema_nao_acessa_nada(self):
        self.assertEqual(self.chamar("/api/apresentacao-humor")[0], 401)


if __name__ == "__main__":
    unittest.main()
