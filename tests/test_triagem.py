#!/usr/bin/env python3
"""Testes da tela de triagem: rotas, permissões e o sigilo das cegas.

    python3 -m unittest tests.test_triagem -v

Aqui o que se persegue é o vazamento. Triagem às cegas não é enfeite
metodológico: ver o voto do outro contamina o próprio, e a revisão perde
o valor. Se a rota da fila devolver a decisão alheia junto, o sigilo
acaba sem ninguém perceber — a tela não mostra, mas o dado foi.
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

from lape import api, auth, revisao  # noqa: E402
from lape.db import Database  # noqa: E402

RIS = "".join(
    f"""TY  - JOUR
TI  - Estudo sobre humor número {i}
AU  - Autor, N.
JO  - Journal of Sports Sciences
PY  - 2020
DO  - 10.1000/teste.{i:04d}
AB  - Resumo do estudo {i} com atletas de handebol.
ER  -

""" for i in range(1, 11))


class BaseWeb(unittest.TestCase):
    """Sobe a API de verdade e conversa com ela como o navegador conversa."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "t.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Ana Souza", "ana@udesc.br", "senhaforte123", role="coordenacao")
        auth.create_account(db, "Beto Lima", "beto@udesc.br", "senhaforte123", role="integrante")
        auth.create_account(db, "Curioso Silva", "curioso@udesc.br", "senhaforte123", role="leitura")
        db.close()
        cls.publico = api.PUBLIC_DASHBOARD
        api.PUBLIC_DASHBOARD = False
        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *a, **k: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        api.PUBLIC_DASHBOARD = cls.publico
        cls.tmp.cleanup()

    def entrar(self, login):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"login": login, "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return resposta.headers.get("Set-Cookie", "").split(";")[0]

    def chamar(self, caminho, cookie=None, corpo=None):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{caminho}",
            data=json.dumps(corpo).encode() if corpo is not None else None,
            headers={"Content-Type": "application/json", **({"Cookie": cookie} if cookie else {})},
            method="POST" if corpo is not None else "GET")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                return resposta.status, json.loads(resposta.read() or b"{}")
        except urllib.error.HTTPError as exc:
            corpo_erro = exc.read()
            try:
                return exc.code, json.loads(corpo_erro or b"{}")
            except ValueError:
                return exc.code, {"bruto": corpo_erro.decode("utf-8", "replace")}


class TestCicloPelaApi(BaseWeb):
    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")
        self.beto = self.entrar("beto@udesc.br")
        self.curioso = self.entrar("curioso@udesc.br")
        self.code = f"rev-{self._testMethodName}"[:40]
        status, _ = self.chamar("/api/revisoes", self.ana,
                                {"titulo": "Humor em handebol", "codigo": self.code,
                                 "avaliadores": 2})
        self.assertEqual(status, 200)
        self.chamar(f"/api/revisoes/{self.code}/importar", self.ana,
                    {"nome": "scopus.ris", "conteudo": RIS})

    def fila(self, cookie):
        return self.chamar(f"/api/revisoes/{self.code}/fila", cookie)[1]

    def test_importar_conta_o_que_entrou(self):
        status, r = self.chamar(f"/api/revisoes/{self.code}/importar", self.ana,
                                {"nome": "de-novo.ris", "conteudo": RIS})
        self.assertEqual(status, 200)
        self.assertEqual(r["novos"], 0)          # tudo repetido
        self.assertEqual(r["duplicados"], 10)

    def test_importar_arquivo_vazio_explica(self):
        status, r = self.chamar(f"/api/revisoes/{self.code}/importar", self.ana,
                                {"nome": "x.ris", "conteudo": "   "})
        self.assertEqual(status, 400)
        self.assertIn("conteúdo", r["error"])

    def test_a_fila_e_de_quem_pergunta(self):
        primeira = self.fila(self.ana)
        self.assertEqual(primeira["faltam"], 10)
        ref = primeira["fila"][0]["id"]
        self.chamar(f"/api/revisoes/{self.code}/decidir", self.ana,
                    {"ref_id": ref, "decisao": "incluir"})
        self.assertEqual(self.fila(self.ana)["faltam"], 9)
        self.assertEqual(self.fila(self.beto)["faltam"], 10)   # o Beto não perdeu nada

    def test_a_fila_nao_entrega_o_voto_alheio(self):
        # o vazamento que este teste guarda: a tela não mostra, mas o dado
        # ia junto na resposta -- e às cegas deixaria de ser às cegas
        ref = self.fila(self.ana)["fila"][0]["id"]
        self.chamar(f"/api/revisoes/{self.code}/decidir", self.ana,
                    {"ref_id": ref, "decisao": "incluir"})
        bruto = json.dumps(self.fila(self.beto), ensure_ascii=False)
        self.assertNotIn("incluir", bruto)
        self.assertNotIn("Ana Souza", bruto)
        for chave in ("decision", "n_incluir", "n_excluir", "screenings"):
            self.assertNotIn(chave, bruto, f"a fila vazou {chave}")

    def test_decidir_em_lote(self):
        refs = [r["id"] for r in self.fila(self.ana)["fila"][:4]]
        status, r = self.chamar(f"/api/revisoes/{self.code}/decidir", self.ana,
                                {"decisoes": [{"ref_id": i, "decisao": "excluir"} for i in refs]})
        self.assertEqual(status, 200)
        self.assertEqual(r["gravadas"], 4)

    def test_decisao_inventada_e_recusada(self):
        ref = self.fila(self.ana)["fila"][0]["id"]
        status, r = self.chamar(f"/api/revisoes/{self.code}/decidir", self.ana,
                                {"ref_id": ref, "decisao": "quem sabe"})
        self.assertEqual(status, 400)
        self.assertIn("decisão", r["error"])

    def test_conflito_aparece_com_nome_so_depois_de_haver_conflito(self):
        ref = self.fila(self.ana)["fila"][0]["id"]
        self.chamar(f"/api/revisoes/{self.code}/decidir", self.ana,
                    {"ref_id": ref, "decisao": "incluir"})
        vazio = self.chamar(f"/api/revisoes/{self.code}/conflitos", self.beto)[1]
        self.assertEqual(vazio["conflitos"], [])
        self.chamar(f"/api/revisoes/{self.code}/decidir", self.beto,
                    {"ref_id": ref, "decisao": "excluir"})
        agora = self.chamar(f"/api/revisoes/{self.code}/conflitos", self.beto)[1]
        self.assertEqual(len(agora["conflitos"]), 1)
        quem = {v["quem"] for v in agora["conflitos"][0]["votos"]}
        self.assertEqual(quem, {"Ana Souza", "Beto Lima"})

    def test_o_prisma_acompanha(self):
        refs = [r["id"] for r in self.fila(self.ana)["fila"][:3]]
        for ref in refs:
            for cookie in (self.ana, self.beto):
                self.chamar(f"/api/revisoes/{self.code}/decidir", cookie,
                            {"ref_id": ref, "decisao": "incluir"})
        p = self.chamar(f"/api/revisoes/{self.code}", self.curioso)[1]["prisma"]
        self.assertEqual(p["identificados"], 10)
        self.assertEqual(p["triados"], 10)
        self.assertEqual(p["pendentes"], 7)

    def test_avancar_leva_o_incluido_para_texto_completo(self):
        ref = self.fila(self.ana)["fila"][0]["id"]
        for cookie in (self.ana, self.beto):
            self.chamar(f"/api/revisoes/{self.code}/decidir", cookie,
                        {"ref_id": ref, "decisao": "incluir"})
        status, r = self.chamar(f"/api/revisoes/{self.code}/avancar", self.ana, {})
        self.assertEqual(status, 200)
        self.assertEqual(r["para_texto_completo"], 1)
        self.assertEqual(r["prisma"]["texto_completo"], 1)

    def test_concordancia_entre_quem_triou(self):
        refs = [r["id"] for r in self.fila(self.ana)["fila"][:5]]
        for i, ref in enumerate(refs):
            self.chamar(f"/api/revisoes/{self.code}/decidir", self.ana,
                        {"ref_id": ref, "decisao": "incluir"})
            self.chamar(f"/api/revisoes/{self.code}/decidir", self.beto,
                        {"ref_id": ref, "decisao": "incluir" if i < 4 else "excluir"})
        r = self.chamar(f"/api/revisoes/{self.code}/concordancia", self.ana)[1]
        self.assertEqual(len(r["pares"]), 1)
        self.assertEqual(r["pares"][0]["n"], 5)
        self.assertEqual(r["pares"][0]["concordancia"], 0.8)

    def test_revisao_que_nao_existe_da_404(self):
        status, _ = self.chamar("/api/revisoes/nao-existe", self.ana)
        self.assertEqual(status, 404)


class TestPermissoes(BaseWeb):
    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")
        self.beto = self.entrar("beto@udesc.br")
        self.curioso = self.entrar("curioso@udesc.br")
        self.code = f"perm-{self._testMethodName}"[:40]
        self.chamar("/api/revisoes", self.ana,
                    {"titulo": "Permissões", "codigo": self.code, "avaliadores": 2})
        self.chamar(f"/api/revisoes/{self.code}/importar", self.ana,
                    {"nome": "s.ris", "conteudo": RIS})

    def test_sem_entrar_nao_ve_nada(self):
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}")[0], 401)
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}/fila")[0], 401)

    def test_quem_so_le_nao_tria(self):
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}/fila", self.curioso)[0], 403)

    def test_quem_so_le_ve_o_prisma(self):
        # o número da revisão é do laboratório inteiro
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}", self.curioso)[0], 200)

    def test_integrante_nao_arbitra(self):
        # arbitragem é decisão de quem coordena, não de quem tria
        ref = self.chamar(f"/api/revisoes/{self.code}/fila", self.beto)[1]["fila"][0]["id"]
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}/arbitrar", self.beto,
                                     {"ref_id": ref, "decisao": "incluir"})[0], 403)
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}/arbitrar", self.ana,
                                     {"ref_id": ref, "decisao": "incluir"})[0], 200)

    def test_integrante_nao_abre_revisao(self):
        self.assertEqual(self.chamar("/api/revisoes", self.beto,
                                     {"titulo": "Minha revisão"})[0], 403)

    def test_arbitragem_precisa_de_decisao_valida(self):
        ref = self.chamar(f"/api/revisoes/{self.code}/fila", self.ana)[1]["fila"][0]["id"]
        status, r = self.chamar(f"/api/revisoes/{self.code}/arbitrar", self.ana,
                                {"ref_id": ref, "decisao": "talvez"})
        self.assertEqual(status, 400)


class TestPaginaDeTriagem(BaseWeb):
    def pagina(self):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}/triagem")
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return resposta.read().decode("utf-8")

    def test_a_pagina_monta_inteira(self):
        html = self.pagina()
        for marcador in ("__BASE_CSS__", "__ICONS_JS__", "__TRIAGEM_JS__"):
            self.assertNotIn(marcador, html, f"marcador não substituído: {marcador}")
        self.assertIn("const ESTADO", html)      # o script de triagem entrou
        self.assertIn("const Icons", html)

    def test_os_atalhos_estao_documentados_na_propria_tela(self):
        html = self.pagina()
        for tecla in ("<kbd>I</kbd>", "<kbd>E</kbd>", "<kbd>T</kbd>", "<kbd>Z</kbd>"):
            self.assertIn(tecla, html)

    def test_o_teclado_cobre_as_tres_decisoes(self):
        js = (ROOT / "scripts" / "lape" / "templates" / "triagem.js").read_text(encoding="utf-8")
        for trecho in ('tecla === "i"', 'tecla === "e"', 'tecla === "t"', 'tecla === "z"'):
            self.assertIn(trecho, js)

    def test_o_resumo_e_escapado_antes_de_realcar(self):
        # título de artigo com "<" existe; um resumo não pode virar HTML
        js = (ROOT / "scripts" / "lape" / "templates" / "triagem.js").read_text(encoding="utf-8")
        corpo = js[js.index("function realcar("):js.index("function atual(")]
        self.assertIn("escapar(texto)", corpo)

    def test_decisao_pendente_nao_some_ao_falhar(self):
        js = (ROOT / "scripts" / "lape" / "templates" / "triagem.js").read_text(encoding="utf-8")
        corpo = js[js.index("async function enviarPendentes"):js.index("function desfazer")]
        self.assertIn("ESTADO.pendentes = lote.concat", corpo)


class TestDownloadsDaRevisao(BaseWeb):
    """Exportar e o fluxograma: os dois respondem arquivo, não JSON."""

    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")
        self.curioso = self.entrar("curioso@udesc.br")
        self.code = f"baixar-{self._testMethodName}"[:40]
        self.chamar("/api/revisoes", self.ana,
                    {"titulo": "Para baixar", "codigo": self.code, "avaliadores": 1})
        self.chamar(f"/api/revisoes/{self.code}/importar", self.ana,
                    {"nome": "s.ris", "conteudo": RIS})
        fila = self.chamar(f"/api/revisoes/{self.code}/fila", self.ana)[1]["fila"]
        self.chamar(f"/api/revisoes/{self.code}/decidir", self.ana,
                    {"ref_id": fila[0]["id"], "decisao": "incluir"})

    def baixar(self, caminho, cookie=None):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}{caminho}")
        if cookie:
            pedido.add_header("Cookie", cookie)
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                return resposta.status, resposta.headers, resposta.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read().decode("utf-8")

    def test_o_ris_vem_como_anexo(self):
        status, cab, corpo = self.baixar(
            f"/api/revisoes/{self.code}/exportar?formato=ris&recorte=todos", self.ana)
        self.assertEqual(status, 200)
        self.assertIn("research-info", cab.get("Content-Type", ""))
        # o código é gravado normalizado; o nome do arquivo sai dele
        self.assertIn("-todos.ris\"", cab.get("Content-Disposition", ""))
        self.assertIn("attachment;", cab.get("Content-Disposition", ""))
        self.assertIn("TY  - JOUR", corpo)

    def test_formato_e_recorte_inventados_explicam(self):
        for consulta in ("formato=docx", "recorte=os_bons"):
            with self.subTest(consulta=consulta):
                status, _, corpo = self.baixar(
                    f"/api/revisoes/{self.code}/exportar?{consulta}", self.ana)
                self.assertEqual(status, 400)
                self.assertIn("desconhecid", corpo)

    def test_o_fluxograma_sai_desenhado(self):
        status, cab, corpo = self.baixar(f"/api/revisoes/{self.code}/prisma.svg", self.ana)
        self.assertEqual(status, 200)
        self.assertIn("image/svg+xml", cab.get("Content-Type", ""))
        self.assertIn("<svg", corpo)
        self.assertIn("(n = 10)", corpo)      # os 10 registros importados

    def test_o_fluxograma_nao_e_guardado_pelo_navegador(self):
        # ele muda a cada decisão: um dia de cache mostraria número velho
        _, cab, _ = self.baixar(f"/api/revisoes/{self.code}/prisma.svg", self.ana)
        self.assertEqual(cab.get_all("Cache-Control"), ["no-store, must-revalidate"])

    def test_quem_so_le_tambem_baixa(self):
        # o resultado da revisão é do laboratório inteiro
        self.assertEqual(self.baixar(
            f"/api/revisoes/{self.code}/prisma.svg", self.curioso)[0], 200)

    def test_sem_entrar_nao_baixa(self):
        self.assertEqual(self.baixar(f"/api/revisoes/{self.code}/exportar")[0], 401)

    def test_revisao_que_nao_existe_da_404(self):
        self.assertEqual(self.baixar("/api/revisoes/nao-existe/prisma.svg", self.ana)[0], 404)


class TestDuplicadosPelaApi(BaseWeb):
    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")
        self.beto = self.entrar("beto@udesc.br")
        self.code = f"dups-{self._testMethodName}"[:40]
        self.chamar("/api/revisoes", self.ana,
                    {"titulo": "Duplicados", "codigo": self.code, "avaliadores": 1})
        for nome in ("scopus.ris", "wos.ris"):
            self.chamar(f"/api/revisoes/{self.code}/importar", self.ana,
                        {"nome": nome, "conteudo": RIS})

    def test_a_uniao_fica_exposta_com_a_evidencia(self):
        status, r = self.chamar(f"/api/revisoes/{self.code}/duplicados", self.beto)
        self.assertEqual(status, 200)
        self.assertEqual(len(r["unidos"]), 10)
        self.assertIn("DOI", r["unidos"][0]["repetidos"][0]["casou_por"])

    def test_separar_devolve_para_a_fila(self):
        r = self.chamar(f"/api/revisoes/{self.code}/duplicados", self.ana)[1]
        repetido = r["unidos"][0]["repetidos"][0]["id"]
        antes = self.chamar(f"/api/revisoes/{self.code}/fila", self.ana)[1]["faltam"]
        status, resultado = self.chamar(f"/api/revisoes/{self.code}/duplicados", self.ana,
                                        {"ref_id": repetido})
        self.assertEqual(status, 200)
        self.assertEqual(resultado["prisma"]["duplicados"], 9)
        self.assertEqual(
            self.chamar(f"/api/revisoes/{self.code}/fila", self.ana)[1]["faltam"], antes + 1)

    def test_separar_o_que_nao_esta_unido_explica(self):
        sozinha = self.chamar(f"/api/revisoes/{self.code}/fila", self.ana)[1]["fila"][0]["id"]
        status, r = self.chamar(f"/api/revisoes/{self.code}/duplicados", self.ana,
                                {"ref_id": sozinha})
        self.assertEqual(status, 400)
        self.assertIn("não está unida", r["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
