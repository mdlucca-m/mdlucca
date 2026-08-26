#!/usr/bin/env python3
"""Testes do barramento de eventos: assinatura, entrega, streaming e n8n.

    python3 -m unittest discover -s tests -v

Nenhuma chamada sai para a internet. Onde e preciso um destino de webhook,
sobe-se um servidor HTTP local que grava o que recebeu -- e assim da para
conferir a assinatura HMAC exatamente como o n8n conferiria.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth, hooks, ingest_excel  # noqa: E402
from lape.db import Database  # noqa: E402


class Receptor(BaseHTTPRequestHandler):
    """Um n8n de mentira: guarda corpo e cabecalhos de cada entrega."""

    recebidos: list[dict] = []
    status_code = 200

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        Receptor.recebidos.append({
            "raw": raw,
            "body": json.loads(raw.decode("utf-8")) if raw else None,
            "event": self.headers.get("X-LAPE-Event"),
            "signature": self.headers.get("X-LAPE-Signature"),
        })
        self.send_response(Receptor.status_code)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args, **kwargs):
        pass


class TestAssinatura(unittest.TestCase):
    def test_assinatura_confere(self):
        corpo = b'{"event":"artigo.publicado"}'
        assinatura = hooks.sign("segredo", corpo)
        self.assertTrue(assinatura.startswith("sha256="))
        self.assertTrue(hooks.verify("segredo", corpo, assinatura))

    def test_assinatura_muda_com_o_corpo(self):
        self.assertNotEqual(hooks.sign("segredo", b"a"), hooks.sign("segredo", b"b"))

    def test_assinatura_muda_com_o_segredo(self):
        self.assertNotEqual(hooks.sign("um", b"a"), hooks.sign("outro", b"a"))

    def test_recusa_sem_segredo_ou_sem_cabecalho(self):
        corpo = b"{}"
        self.assertFalse(hooks.verify("", corpo, hooks.sign("s", corpo)))
        self.assertFalse(hooks.verify("s", corpo, None))
        self.assertFalse(hooks.verify("s", corpo, "sha256=oquefor"))

    def test_espaco_em_volta_nao_derruba(self):
        corpo = b'{"x":1}'
        self.assertTrue(hooks.verify("s", corpo, "  " + hooks.sign("s", corpo) + "  "))


class TestEventos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_evento_entra_no_historico(self):
        hooks.emit(self.db, "artigo.publicado", entity="articles", entity_id=7,
                   detail="Ansiedade em atletas")
        linhas = self.db.dicts("SELECT * FROM change_log")
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["event"], "artigo.publicado")
        self.assertEqual(linhas[0]["entity_id"], "7")

    def test_assinante_do_streaming_recebe(self):
        canal = hooks.subscribe()
        try:
            hooks.emit(self.db, "lake.atualizado", detail="reconstruido")
            mensagem = canal.get(timeout=2)
            self.assertEqual(mensagem["event"], "lake.atualizado")
            self.assertEqual(mensagem["detail"], "reconstruido")
        finally:
            hooks.unsubscribe(canal)
        self.assertEqual(hooks.subscriber_count(), 0)

    def test_since_devolve_o_que_veio_depois(self):
        hooks.emit(self.db, "artigo.cadastrado", detail="um")
        marco = hooks.latest_id(self.db)
        hooks.emit(self.db, "artigo.cadastrado", detail="dois")
        novos = hooks.since(self.db, marco)
        self.assertEqual([x["detail"] for x in novos], ["dois"])

    def test_bump_nao_entrega_mas_avisa_o_painel(self):
        canal = hooks.subscribe()
        try:
            hooks.bump(self.db, "recarga")
            self.assertEqual(canal.get(timeout=2)["event"], "dados.alterados")
        finally:
            hooks.unsubscribe(canal)

    def test_cadastro_recusa_url_invalida(self):
        with self.assertRaises(ValueError):
            hooks.register(self.db, "n8n", "ftp://exemplo/hook")

    def test_cadastro_recusa_evento_desconhecido(self):
        with self.assertRaises(ValueError):
            hooks.register(self.db, "n8n", "https://exemplo/hook", "artigo.inventado")

    def test_cadastro_e_remocao(self):
        criado = hooks.register(self.db, "n8n", "https://exemplo/hook", "artigo.publicado")
        self.assertEqual(criado["event"], "artigo.publicado")
        self.assertEqual(len(hooks.targets_for(self.db, "artigo.publicado")), 1)
        # quem assina um evento so nao recebe os outros
        self.assertEqual(hooks.targets_for(self.db, "lake.atualizado"), [])
        hooks.remove(self.db, criado["id"])
        self.assertEqual(hooks.targets_for(self.db, "artigo.publicado"), [])

    def test_curinga_recebe_qualquer_evento(self):
        hooks.register(self.db, "tudo", "https://exemplo/hook", "*")
        self.assertEqual(len(hooks.targets_for(self.db, "descoberta.encontrada")), 1)

    def test_status_traz_catalogo_e_cadastros(self):
        hooks.register(self.db, "n8n", "https://exemplo/hook")
        estado = hooks.status(self.db)
        self.assertEqual(len(estado["webhooks"]), 1)
        self.assertIn("artigo.publicado", [e["id"] for e in estado["events"]])


class TestEntrega(unittest.TestCase):
    """A entrega de verdade, contra um servidor local."""

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Receptor)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Receptor.recebidos = []
        Receptor.status_code = 200
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.url = f"http://127.0.0.1:{self.port}/hook"

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_entrega_assinada_e_registrada(self):
        hooks.register(self.db, "n8n", self.url, "*", secret="segredo-do-lape")
        hooks.dispatch(self.db, "artigo.publicado",
                       {"event": "artigo.publicado", "detail": "Ansiedade"},
                       background=False)
        self.assertEqual(len(Receptor.recebidos), 1)
        recebido = Receptor.recebidos[0]
        self.assertEqual(recebido["event"], "artigo.publicado")
        # e a conferencia que o n8n faz do outro lado
        self.assertTrue(hooks.verify("segredo-do-lape", recebido["raw"], recebido["signature"]))
        entregas = self.db.dicts("SELECT * FROM webhook_deliveries")
        self.assertEqual(len(entregas), 1)
        self.assertEqual(entregas[0]["status"], "ok")
        self.assertEqual(entregas[0]["http_code"], 200)
        self.assertEqual(self.db.scalar("SELECT last_status FROM webhooks"), "ok")

    def test_erro_no_destino_tenta_de_novo_e_registra(self):
        Receptor.status_code = 500
        hooks.register(self.db, "n8n", self.url, "*")
        hooks.DELIVERY_RETRIES, original = 2, hooks.DELIVERY_RETRIES
        try:
            hooks.dispatch(self.db, "artigo.publicado", {"event": "artigo.publicado"},
                           background=False)
        finally:
            hooks.DELIVERY_RETRIES = original
        entregas = self.db.dicts("SELECT * FROM webhook_deliveries ORDER BY id")
        self.assertEqual(len(entregas), 2)
        self.assertTrue(all(e["status"] == "erro" for e in entregas))
        self.assertEqual(entregas[0]["http_code"], 500)
        self.assertEqual(self.db.scalar("SELECT failures FROM webhooks"), 1)

    def test_destino_fora_do_ar_nao_derruba_o_cadastro(self):
        # porta fechada de proposito: emitir tem de continuar funcionando
        hooks.register(self.db, "morto", "http://127.0.0.1:9/hook", "*")
        hooks.DELIVERY_RETRIES, original = 1, hooks.DELIVERY_RETRIES
        try:
            hooks.emit(self.db, "artigo.publicado", detail="segue o baile")
            # a entrega roda em segundo plano; esperamos por ela para nao apagar
            # o banco temporario debaixo da thread
            for _ in range(100):
                if not any(t.name == "lape-webhooks" and t.is_alive()
                           for t in threading.enumerate()):
                    break
                time.sleep(0.05)
        finally:
            hooks.DELIVERY_RETRIES = original
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM change_log"), 1)
        # a tentativa falhou e ficou registrada -- o cadastro seguiu mesmo assim
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM webhook_deliveries WHERE status = 'erro'"), 1)


class TestRotas(unittest.TestCase):
    """As rotas de automacao, streaming e a porta de entrada do n8n."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "api.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        ingest_excel.ingest_articles(db, [
            {"title": "Ansiedade em atletas", "authors": "Andrade; Vilarino",
             "status": "Publicado", "year_published": "2025"},
        ])
        auth.create_account(db, "Coordenacao", "coord@udesc.br", "senhaforte123",
                            role="coordenacao")
        auth.create_account(db, "Integrante", "membro@udesc.br", "senhaforte123",
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

    def call(self, path, method="GET", body=None, cookie=None, headers=None, raw=None):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        head = dict(headers or {})
        if data:
            head.setdefault("Content-Type", "application/json")
        if cookie:
            head["Cookie"] = f"{api.COOKIE_NAME}={cookie}"
        request = urllib.request.Request(url, data=data, method=method, headers=head)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    def entrar(self, login="coord@udesc.br"):
        url = f"http://127.0.0.1:{self.port}/api/auth/login"
        data = json.dumps({"login": login, "senha": "senhaforte123"}).encode()
        request = urllib.request.Request(url, data=data, method="POST",
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            cookie = response.headers.get("Set-Cookie") or ""
        return cookie.split("=")[1].split(";")[0]

    def test_automacao_exige_coordenacao(self):
        status, _ = self.call("/api/automation")
        self.assertEqual(status, 401)
        status, _ = self.call("/api/automation", cookie=self.entrar("membro@udesc.br"))
        self.assertEqual(status, 403)

    def test_automacao_devolve_catalogo(self):
        status, body = self.call("/api/automation", cookie=self.entrar())
        self.assertEqual(status, 200)
        self.assertIn("artigo.publicado", [e["id"] for e in body["events"]])
        self.assertIn("webhooks", body)
        self.assertIn("deliveries", body)

    def test_cadastro_de_webhook_pela_rota(self):
        token = self.entrar()
        status, body = self.call("/api/webhooks", "POST",
                                 {"nome": "n8n", "url": "https://n8n.exemplo/webhook/lape",
                                  "evento": "artigo.publicado"}, cookie=token)
        self.assertEqual(status, 200)
        self.assertEqual(body["event"], "artigo.publicado")
        status, _ = self.call(f"/api/webhooks/{body['id']}/remover", "POST", {}, cookie=token)
        self.assertEqual(status, 200)

    def test_cadastro_sem_url_e_recusado(self):
        status, body = self.call("/api/webhooks", "POST", {"nome": "n8n"}, cookie=self.entrar())
        self.assertEqual(status, 400)
        self.assertIn("url", body["error"])

    def test_porta_do_n8n_recusa_sem_credencial(self):
        status, _ = self.call("/api/hooks/n8n", "POST", {"acao": "lake"})
        self.assertIn(status, (401, 403))

    def test_porta_do_n8n_aceita_assinatura(self):
        segredo = "segredo-de-teste-do-n8n"
        anterior = hooks.WEBHOOK_SECRET
        hooks.WEBHOOK_SECRET = segredo
        try:
            corpo = json.dumps({"acao": "cadastrar", "entidade": "articles",
                                "dados": [{"Título": "Vindo do n8n", "Autores": "Andrade"}]}
                               ).encode("utf-8")
            status, body = self.call(
                "/api/hooks/n8n", "POST", raw=corpo,
                headers={"Content-Type": "application/json",
                         "X-LAPE-Signature": hooks.sign(segredo, corpo)})
        finally:
            hooks.WEBHOOK_SECRET = anterior
        self.assertEqual(status, 200, body)
        db = Database(self.db_path)
        try:
            self.assertEqual(db.scalar(
                "SELECT COUNT(*) FROM articles WHERE title = 'Vindo do n8n'"), 1)
        finally:
            db.close()

    def test_porta_do_n8n_recusa_assinatura_errada(self):
        anterior = hooks.WEBHOOK_SECRET
        hooks.WEBHOOK_SECRET = "segredo-de-teste-do-n8n"
        try:
            corpo = json.dumps({"acao": "lake"}).encode("utf-8")
            status, _ = self.call(
                "/api/hooks/n8n", "POST", raw=corpo,
                headers={"Content-Type": "application/json",
                         "X-LAPE-Signature": hooks.sign("outro-segredo", corpo)})
        finally:
            hooks.WEBHOOK_SECRET = anterior
        self.assertIn(status, (401, 403))

    def test_streaming_exige_login(self):
        status, body = self.call("/api/stream")
        self.assertEqual(status, 401)
        self.assertIn("entrar", body["error"])

    def test_streaming_abre_e_empurra_o_evento(self):
        """Assina /api/stream e confere que um evento emitido chega pela conexao."""
        url = f"http://127.0.0.1:{self.port}/api/stream"
        request = urllib.request.Request(url, headers={
            "Accept": "text/event-stream",
            "Cookie": f"{api.COOKIE_NAME}={self.entrar()}"})
        response = urllib.request.urlopen(request, timeout=30)
        try:
            self.assertEqual(response.status, 200)
            self.assertIn("text/event-stream", response.headers.get("Content-Type", ""))
            abertura = response.readline() + response.readline() + response.readline()
            self.assertIn(b"pronto", abertura)

            # o servidor so empurra depois que a assinatura existe do lado dele
            for _ in range(50):
                if hooks.subscriber_count():
                    break
                time.sleep(0.05)
            db = Database(self.db_path)
            try:
                hooks.emit(db, "artigo.publicado", detail="empurrado pelo teste", deliver=False)
            finally:
                db.close()

            recebido = b""
            for _ in range(12):
                linha = response.readline()
                recebido += linha
                if b"empurrado pelo teste" in recebido:
                    break
            self.assertIn(b"mudanca", recebido)
            self.assertIn(b"empurrado pelo teste", recebido)
        finally:
            response.close()


if __name__ == "__main__":
    unittest.main()
