#!/usr/bin/env python3
"""Atualizar todos os acervos de uma vez, sem travar a tela.

    python3 -m unittest tests.test_atualizar_tudo -v

Tres acervos, noventa buscas, dez minutos. Antes disto a unica maneira
era apertar "Atualizar agora" tres vezes e esperar dentro de cada
requisicao -- e uma requisicao de dez minutos nao chega ao fim: o
navegador desiste, o pedido morre no caminho, e quem apertou nao tem
como saber se as buscas aconteceram. O jeito de descobrir era apertar de
novo, o que gasta a cota da base pela segunda vez pela mesma duvida.

O que estes testes guardam, nesta ordem de importancia:

  1. a barra chega ao fim -- inclusive quando uma base esta desligada por
     falta de chave, que e o caso de cinco das oito;
  2. um acervo falhar nao cancela os outros, e nao deixa a tela dizendo
     "atualizando" para sempre;
  3. duas pessoas nao disparam as mesmas noventa buscas em paralelo;
  4. quem nao pode VER um acervo restrito nao pode mandar atualiza-lo --
     nem descobrir que ele existe pela resposta.
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
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, atualizacao, auth, biblioteca, linhas  # noqa: E402
from lape.db import Database  # noqa: E402


def _registro(n: int) -> dict:
    return {"title": f"Artigo {n}", "doi": f"10.1234/t{n}", "year": 2024,
            "journal": "Revista", "authors": "Alguem A", "abstract": "",
            "source": "pubmed"}


class BaseDosAcervos(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db_path = Path(tmp.name) / "a.sqlite"
        self.db = Database(self.db_path)
        self.addCleanup(self.db.close)
        self.db.migrate()
        linhas.instalar(self.db)
        biblioteca.instalar(self.db)
        # O estado da atualizacao e de modulo -- um servidor, uma
        # atualizacao. Entre testes ele precisa voltar ao inicio, ou o
        # segundo teste encontra o resultado do primeiro.
        self.addCleanup(atualizacao._estado.clear)
        atualizacao._estado.clear()
        atualizacao._estado["rodando"] = False

    def trocar(self, modulo, nome, valor):
        antigo = getattr(modulo, nome)
        setattr(modulo, nome, valor)
        self.addCleanup(setattr, modulo, nome, antigo)

    def sem_traceback(self):
        """Cala o `print_exc` de um estouro PROVOCADO por este teste.

        Calado sempre, um estouro de verdade passaria em branco na saida
        da suite. Calado aqui, o que sobra na tela e so o inesperado.
        """
        self.trocar(atualizacao.traceback, "print_exc", lambda *a, **k: None)

    def sem_rede(self, colher):
        """Troca o unico ponto que vai a rede, e tira a espera entre buscas."""
        self.trocar(biblioteca, "_colher", colher)
        self.trocar(biblioteca, "THROTTLE", 0)

    def esperar_o_fim(self, limite=30.0):
        comeco = time.monotonic()
        while time.monotonic() - comeco < limite:
            e = atualizacao.estado()
            if not e["rodando"] and e.get("terminou_em"):
                return e
            time.sleep(0.02)
        self.fail("a atualização não terminou no tempo previsto")


class TestOTamanhoDaTarefa(BaseDosAcervos):
    """Quantas buscas faltam -- a conta que a barra precisa antes de andar."""

    def test_conta_as_buscas_guardadas_do_acervo(self):
        n = biblioteca.quantas_buscas(self.db, "humor_esporte")
        guardadas = self.db.scalar(
            "SELECT COUNT(*) FROM biblioteca_busca bb JOIN biblioteca b"
            "    ON b.id = bb.biblioteca_id WHERE b.code = ?", ("humor_esporte",))
        self.assertEqual(n, guardadas)
        self.assertGreater(n, 1)

    def test_da_para_contar_so_uma_base(self):
        so_pubmed = biblioteca.quantas_buscas(self.db, "humor_esporte",
                                              bases=(biblioteca.PUBMED,))
        todas = biblioteca.quantas_buscas(self.db, "humor_esporte")
        self.assertLess(so_pubmed, todas)
        self.assertGreater(so_pubmed, 0)

    def test_acervo_que_nao_existe_reclama(self):
        with self.assertRaises(ValueError):
            biblioteca.quantas_buscas(self.db, "nao_existe")


class TestABarraChegaAoFim(BaseDosAcervos):
    """O aviso de progresso sai uma vez por busca, e a conta fecha.

    Fecha inclusive com base desligada: cinco das oito bases de
    fibromialgia nao tem API, e a primeira busca de cada uma desliga a
    base inteira. Se as puladas nao avisassem, a barra pararia em 60% e
    ficaria lá -- o que, na tela, e indistinguivel de travamento.
    """

    def test_um_aviso_por_busca_e_o_total_bate(self):
        self.sem_rede(lambda base, query, limite: [_registro(1)])
        passos = []
        total = biblioteca.quantas_buscas(self.db, "humor_estetico")
        biblioteca.atualizar(self.db, "humor_estetico",
                             progresso=passos.append)
        self.assertEqual(len(passos), total)
        self.assertEqual([p["feitas"] for p in passos],
                         list(range(1, total + 1)))
        self.assertEqual(passos[-1]["feitas"], passos[-1]["total"])

    def test_base_sem_chave_avisa_das_puladas_tambem(self):
        def colher(base, query, limite):
            if base == biblioteca.PUBMED:
                return [_registro(1)]
            raise biblioteca.SemChave(f"{base}: sem chave")

        self.sem_rede(colher)
        passos = []
        total = biblioteca.quantas_buscas(self.db, "humor_estetico")
        biblioteca.atualizar(self.db, "humor_estetico", progresso=passos.append)
        self.assertEqual(len(passos), total)
        self.assertEqual(passos[-1]["feitas"], total)
        situacoes = {p["situacao"] for p in passos}
        self.assertIn("sem_chave", situacoes)
        self.assertIn("pulada", situacoes)

    def test_a_busca_que_falhou_avisa_e_as_outras_seguem(self):
        chamadas = {"n": 0}

        def colher(base, query, limite):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                raise RuntimeError("a rede caiu")
            return [_registro(chamadas["n"])]

        self.sem_rede(colher)
        passos = []
        r = biblioteca.atualizar(self.db, "humor_estetico", progresso=passos.append)
        self.assertEqual(r["erros"], 1)
        self.assertEqual([p["situacao"] for p in passos].count("erro"), 1)
        self.assertGreater(r["novos"], 0)

    def test_sem_progresso_nada_muda(self):
        """O parametro e opcional, e quem chama de um script nao o passa."""
        self.sem_rede(lambda base, query, limite: [_registro(1)])
        r = biblioteca.atualizar(self.db, "humor_estetico")
        self.assertGreater(r["novos"], 0)


class TestAAtualizacaoDeTudo(BaseDosAcervos):
    """Os tres acervos numa tacada, acompanhados de fora."""

    def test_roda_os_tres_e_soma_o_resultado(self):
        self.sem_rede(lambda base, query, limite: [_registro(1), _registro(2)])
        codes = [x["code"] for x in biblioteca.todas(self.db, perfil="admin")]
        atualizacao.iniciar(self.db_path, codes)
        fim = self.esperar_o_fim()
        self.assertEqual(len(fim["acervos"]), len(codes))
        self.assertEqual({x["code"] for x in fim["acervos"]}, set(codes))
        self.assertGreater(fim["novos"], 0)
        self.assertEqual(fim["feitas"], fim["total"])
        self.assertIsNone(fim["erro"])

    def test_o_estado_comeca_rodando_e_volta_ao_fim(self):
        liberar = threading.Event()

        def colher(base, query, limite):
            liberar.wait(10)
            return [_registro(1)]

        self.sem_rede(colher)
        inicio = atualizacao.iniciar(self.db_path, ["humor_estetico"])
        self.assertTrue(inicio["rodando"])
        self.assertTrue(atualizacao.estado()["rodando"])
        liberar.set()
        fim = self.esperar_o_fim()
        self.assertFalse(fim["rodando"])
        self.assertTrue(fim["terminou_em"])

    def test_duas_ao_mesmo_tempo_nao(self):
        """Duas pessoas apertando fariam as mesmas buscas em paralelo.

        A base responde a isso com bloqueio, e nao com o dobro de artigos.
        """
        liberar = threading.Event()
        self.addCleanup(liberar.set)

        def colher(base, query, limite):
            liberar.wait(10)
            return [_registro(1)]

        self.sem_rede(colher)
        atualizacao.iniciar(self.db_path, ["humor_estetico"])
        with self.assertRaises(atualizacao.JaRodando):
            atualizacao.iniciar(self.db_path, ["humor_esporte"])
        liberar.set()
        self.esperar_o_fim()

    def test_depois_de_terminar_da_para_rodar_de_novo(self):
        self.sem_rede(lambda base, query, limite: [])
        atualizacao.iniciar(self.db_path, ["humor_estetico"])
        self.esperar_o_fim()
        atualizacao.iniciar(self.db_path, ["humor_estetico"])
        self.esperar_o_fim()

    def test_um_acervo_estourando_nao_cancela_os_outros(self):
        de_verdade = biblioteca.atualizar

        def atualizar(db, code, **kw):
            if code == "humor_estetico":
                raise RuntimeError("estourou aqui")
            return de_verdade(db, code, **kw)

        self.sem_traceback()
        self.sem_rede(lambda base, query, limite: [_registro(1)])
        self.trocar(biblioteca, "atualizar", atualizar)
        atualizacao.iniciar(self.db_path,
                            ["humor_estetico", "humor_esporte"])
        fim = self.esperar_o_fim()
        por_code = {x["code"]: x for x in fim["acervos"]}
        self.assertIn("estourou aqui", por_code["humor_estetico"]["erro"])
        self.assertGreater(por_code["humor_esporte"]["novos"], 0)

    def test_erro_inesperado_nao_deixa_a_tela_dizendo_atualizando(self):
        """O `finally` e o que impede o "atualizando" eterno."""
        def explodir(db, code, **kw):
            raise RuntimeError("qualquer coisa")

        self.sem_traceback()
        self.trocar(biblioteca, "atualizar", explodir)
        atualizacao.iniciar(self.db_path, ["humor_estetico"])
        fim = self.esperar_o_fim()
        self.assertFalse(fim["rodando"])

    def test_sem_acervo_nenhum_reclama_na_hora(self):
        with self.assertRaises(ValueError):
            atualizacao.iniciar(self.db_path, [])
        self.assertFalse(atualizacao.estado()["rodando"])

    def test_o_estado_devolvido_e_uma_copia(self):
        """Quem le esta noutra linha de execucao.

        Devolver o dicionario vivo faria a tela ler um numero que muda no
        meio da serializacao -- e mexer no que ela leu mexeria no estado.
        """
        self.sem_rede(lambda base, query, limite: [])
        atualizacao.iniciar(self.db_path, ["humor_estetico"])
        self.esperar_o_fim()
        copia = atualizacao.estado()
        copia["novos"] = 999999
        copia["acervos"].clear()
        self.assertNotEqual(atualizacao.estado()["novos"], 999999)
        self.assertTrue(atualizacao.estado()["acervos"])


class TestARotaDeAtualizarTudo(unittest.TestCase):
    """A rota, com sessao de verdade -- e nao so a funcao.

    Duas coisas so aparecem aqui. A primeira e a ORDEM das rotas:
    "atualizar" casa com `[\\w-]+`, e registrada depois da rota de um
    acervo so, um GET aqui viraria "mostre o acervo de codigo atualizar"
    e responderia 404 sem nunca chegar nesta funcao. A segunda e o campo
    do usuario que decide o acesso: `user_role` e o perfil de permissao,
    `role` e o vinculo academico -- ler o segundo ja custou um defeito.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "rotas.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        linhas.instalar(db)
        biblioteca.instalar(db)
        auth.create_account(db, "Coordena", "coord@udesc.br", "senhaforte123",
                            role="coordenacao")
        cls.dono = auth.create_account(db, "Dona", "dona@udesc.br", "senhaforte123",
                                       role="integrante")["member_id"]
        auth.create_account(db, "Outra", "outra@udesc.br", "senhaforte123",
                            role="integrante")
        # vinculo academico de propósito diferente do perfil de permissao
        db.execute("UPDATE members SET role = 'professor' WHERE login = ?",
                   ("coord@udesc.br",))
        biblioteca.declarar_dono(db, "fibromialgia", cls.dono)
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
        # Sem rede: a rota de verdade seria noventa buscas.
        antigo = biblioteca._colher
        biblioteca._colher = lambda base, query, limite: []
        self.addCleanup(setattr, biblioteca, "_colher", antigo)
        passo = biblioteca.THROTTLE
        biblioteca.THROTTLE = 0
        self.addCleanup(setattr, biblioteca, "THROTTLE", passo)
        self.addCleanup(self.esperar_o_fim)
        atualizacao._estado.clear()
        atualizacao._estado["rodando"] = False

    def esperar_o_fim(self, limite=30.0):
        comeco = time.monotonic()
        while time.monotonic() - comeco < limite:
            if not atualizacao.estado()["rodando"]:
                return
            time.sleep(0.02)

    def entrar(self, login):
        corpo = json.dumps({"login": login, "senha": "senhaforte123"}).encode()
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login", data=corpo, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return (r.headers.get("Set-Cookie") or "").split("=")[1].split(";")[0]

    def pedir(self, caminho, cookie, corpo=None):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{caminho}", data=dados,
            method="POST" if dados is not None else "GET",
            headers={"Cookie": f"{api.COOKIE_NAME}={cookie}",
                     **({"Content-Type": "application/json"} if dados else {})})
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode() or "{}")

    def test_a_coordenacao_dispara_todos_os_acervos(self):
        status, corpo = self.pedir("/api/bibliotecas/atualizar",
                                   self.entrar("coord@udesc.br"), {})
        self.assertEqual(status, 200)
        self.assertTrue(corpo["rodando"])
        # TODOS os acervos declarados, inclusive o restrito: a
        # coordenacao o ve. O numero vem da declaracao, e nao escrito
        # aqui: com "3" na mao, cada acervo novo quebrava este teste sem
        # que nada estivesse errado -- e um teste que quebra por motivo
        # certo ensina a ignora-lo.
        self.assertEqual(len(corpo["pedidos"]), len(biblioteca.BIBLIOTECAS))

    def test_o_GET_devolve_o_estado_e_nao_um_acervo_de_codigo_atualizar(self):
        """A ordem das rotas, que e o que faz esta rota existir."""
        status, corpo = self.pedir("/api/bibliotecas/atualizar",
                                   self.entrar("coord@udesc.br"))
        self.assertEqual(status, 200)
        self.assertIn("rodando", corpo)
        self.assertNotIn("biblioteca", corpo)

    def test_da_para_pedir_um_acervo_so(self):
        status, corpo = self.pedir("/api/bibliotecas/atualizar",
                                   self.entrar("coord@udesc.br"),
                                   {"acervos": ["humor_estetico"]})
        self.assertEqual(status, 200)
        self.assertEqual(corpo["pedidos"], ["humor_estetico"])

    def test_quem_nao_ve_o_acervo_restrito_nao_o_atualiza(self):
        """E a resposta nao conta que ele existe.

        Este teste prova o que de fato fecha a porta hoje: a rota e da
        coordenacao, e o pedido morre em `auth.require` antes de chegar ao
        filtro de visibilidade. O filtro tambem esta lá, e HOJE NAO
        DISPARA para acervo restrito -- conferido: quem passa por
        `auth.require("coordenacao")` ve todos os acervos, restritos
        inclusive, logo `permitidos` e sempre a lista inteira.

        Ele fica por duas razoes concretas, e nao por precaucao vaga: (1) e
        ele que recusa um codigo que nao existe, o que o teste seguinte
        cobre; (2) se um dia a rota descer para "integrante", ou um acervo
        restrito passar a excluir alguem da coordenacao, ele e a unica
        coisa entre o pedido e a busca. Tirar o filtro nao quebra nenhum
        teste de acervo restrito -- por isso este comentario existe.
        """
        status, corpo = self.pedir("/api/bibliotecas/atualizar",
                                   self.entrar("outra@udesc.br"),
                                   {"acervos": ["fibromialgia"]})
        self.assertEqual(status, 403)
        self.assertNotIn("fibromialgia", json.dumps(corpo))

    def test_a_rota_e_da_coordenacao_na_lista_de_rotas(self):
        """A trava que o teste acima de fato exerce, olhada de frente."""
        minimos = {(v, p): m for v, p, _, m in api.ROUTES}
        self.assertEqual(minimos[("POST", r"^/api/bibliotecas/atualizar/?$")],
                         "coordenacao")

    def test_codigo_que_nao_existe_nao_vira_atualizacao_vazia(self):
        """Sem o filtro, isto respondia 200 e nao atualizava nada.

        E o pior dos dois mundos: a tela mostra a barra andando, chega ao
        fim, e o acervo continua do tamanho que estava. Um 404 na hora diz
        que o codigo esta errado, que e a informacao util.
        """
        status, corpo = self.pedir("/api/bibliotecas/atualizar",
                                   self.entrar("coord@udesc.br"),
                                   {"acervos": ["nao_existe"]})
        self.assertEqual(status, 404)
        self.assertFalse(atualizacao.estado()["rodando"])

    def test_integrante_nao_atualiza_nem_os_abertos(self):
        """Sair para a rede noventa vezes e decisao da coordenacao."""
        status, _ = self.pedir("/api/bibliotecas/atualizar",
                               self.entrar("outra@udesc.br"),
                               {"acervos": ["humor_esporte"]})
        self.assertEqual(status, 403)

    def test_a_segunda_pessoa_recebe_409_e_nao_dispara_de_novo(self):
        liberar = threading.Event()
        self.addCleanup(liberar.set)

        def colher(base, query, limite):
            liberar.wait(10)
            return []

        antigo = biblioteca._colher
        biblioteca._colher = colher
        self.addCleanup(setattr, biblioteca, "_colher", antigo)

        cookie = self.entrar("coord@udesc.br")
        status, _ = self.pedir("/api/bibliotecas/atualizar", cookie, {})
        self.assertEqual(status, 200)
        status, corpo = self.pedir("/api/bibliotecas/atualizar", cookie, {})
        self.assertEqual(status, 409)
        self.assertIn("andamento", corpo["error"])
        liberar.set()

    def test_a_mudanca_fica_no_log(self):
        self.pedir("/api/bibliotecas/atualizar",
                   self.entrar("coord@udesc.br"), {})
        self.esperar_o_fim()
        db = Database(self.db_path)
        self.addCleanup(db.close)
        acoes = db.dicts("SELECT action, detail FROM audit_log"
                         " WHERE action = 'acervos_atualizando'")
        self.assertTrue(acoes)
        self.assertIn("humor_esporte", acoes[-1]["detail"])


class TestAOrdemDasRotas(unittest.TestCase):
    """A ordem e o que faz a rota existir -- e ordem nao se ve rodando.

    Um teste de rota passa com a ordem certa e com a errada em dias
    diferentes, porque quem casa primeiro depende da posicao na lista.
    Este olha a lista.
    """

    def test_atualizar_vem_antes_do_acervo_generico(self):
        caminhos = [p for verbo, p, *_ in api.ROUTES if verbo == "GET"]
        atualizar = caminhos.index(r"^/api/bibliotecas/atualizar/?$")
        generico = caminhos.index(r"^/api/bibliotecas/(?P<code>[\w-]+)/?$")
        self.assertLess(atualizar, generico)

    def test_nenhum_acervo_se_chama_atualizar(self):
        """O preco da ordem acima -- escrito, para nao ser descoberto depois."""
        codes = {d["code"] for d in biblioteca.BIBLIOTECAS}
        self.assertNotIn("atualizar", codes)


if __name__ == "__main__":
    unittest.main()
