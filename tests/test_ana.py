#!/usr/bin/env python3
"""Testes da Ana -- a assistente que responde sem inventar.

    python3 -m unittest tests.test_ana -v

O que se cobra aqui não é "ela responde bonito". É o contrário: que o
número venha de uma consulta e não de uma estimativa, que a resposta diga
de onde ele saiu, que a pergunta que ela não entende receba um "não sei"
em vez de um chute, e que a pergunta da coordenação seja RECUSADA a quem
tem leitura -- e não respondida pela metade, que é o jeito de vazar um
total sem parecer que vazou.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ana, api, auth, ingest_excel  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class BaseDaAna(unittest.TestCase):
    """Um laboratório pequeno, mas com todas as formas que Ana lê."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "ana.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.hoje = date.today()
        ingest_excel.ingest_articles(self.db, [
            {"title": "Ansiedade em atletas", "authors": "Guilherme Vilarino; Andrade",
             "status": "Publicado", "year_published": str(self.hoje.year),
             "journal": "Motriz"},
            {"title": "Humor e natação", "authors": "Andrade",
             "status": "Publicado", "year_published": "2019", "journal": "JSEP"},
            {"title": "Dropout na fibromialgia", "authors": "Andrade",
             "status": "Submetido"},
            {"title": "Sono e desempenho", "authors": "Andrade",
             "status": "Em produção", "started_on": "2019-01-10"},
        ])
        self.db.conn.commit()

    def perguntar(self, pergunta, perfil="leitura"):
        return ana.responder(self.db, pergunta, perfil)


class TestOQueAnaEntende(BaseDaAna):

    def test_o_acervo_inteiro(self):
        r = self.perguntar("quantos artigos o laboratório tem?")
        self.assertEqual(r["intencao"], "acervo")
        self.assertEqual(r["numero"], 4)

    def test_publicados_no_ano_citado(self):
        r = self.perguntar("quantos artigos publicamos em 2019?")
        self.assertEqual(r["intencao"], "publicados")
        self.assertEqual(r["numero"], 1)
        self.assertIn("Humor e natação", [i["rotulo"] for i in r["itens"]])

    def test_sem_ano_ela_avisa_qual_ano_usou(self):
        """Responder sobre o ano corrente calada seria responder outra pergunta."""
        r = self.perguntar("quantos artigos publicamos?")
        self.assertEqual(r["numero"], 1)
        self.assertIn(str(self.hoje.year), r["resposta"])
        self.assertIn("não disse o ano", r["resposta"])

    def test_a_situacao_no_plural(self):
        """Ninguém pergunta "quais artigos submetido"."""
        r = self.perguntar("quais artigos estão submetidos?")
        self.assertEqual(r["intencao"], "situacao")
        self.assertEqual(r["numero"], 1)

    def test_com_duas_situacoes_ganha_a_primeira_citada(self):
        """A mesma pergunta não pode responder uma coisa hoje e outra amanhã.

        Com as palavras num conjunto, quem desempatava era a ordem interna
        do Python -- que muda entre execuções.
        """
        r = self.perguntar("quais artigos estão submetidos ou aceitos?")
        self.assertIn("submetido", r["fonte"])
        outra = self.perguntar("quais artigos estão aceitos ou submetidos?")
        self.assertIn("aceito", outra["fonte"])

    def test_a_pergunta_mais_especifica_ganha(self):
        """"publicados em 2019" tem "artigos" e "quantos" -- e não é o acervo."""
        r = self.perguntar("quantos artigos publicados em 2019?")
        self.assertEqual(r["intencao"], "publicados")

    def test_quem_decide_e_a_especificidade_e_nao_a_ordem_da_lista(self):
        """O acervo está declarado ANTES, e mesmo assim não ganha.

        Sem o peso, quem responderia seria a primeira pergunta da lista
        que casasse -- e inserir uma pergunta nova no meio mudaria, em
        silêncio, a resposta de outra.
        """
        pergunta = "quantos artigos publicados em 2019?"
        palavras = ana._palavras(pergunta)
        casadas = [i["code"] for i in ana.PERGUNTAS
                   if all(any(p in palavras for p in grupo) for grupo in i["grupos"])]
        self.assertIn("acervo", casadas)          # há empate de verdade a resolver
        self.assertEqual(casadas[0], "acervo")    # e o acervo é o primeiro da lista
        escolhida, _ = ana.entender(self.db, pergunta)
        self.assertEqual(escolhida["code"], "publicados")

    def test_a_producao_de_uma_pessoa(self):
        r = self.perguntar("quantos artigos do Vilarino?")
        self.assertEqual(r["intencao"], "pessoa")
        self.assertEqual(r["numero"], 1)
        self.assertIn("Vilarino", r["fonte"])

    def test_o_acento_nao_muda_a_resposta(self):
        com = self.perguntar("quantas pessoas têm no laboratório?")
        sem = self.perguntar("quantas pessoas tem no laboratorio?")
        self.assertEqual(com["intencao"], sem["intencao"])
        self.assertEqual(com["numero"], sem["numero"])

    def test_os_manuscritos_parados(self):
        r = self.perguntar("quais artigos estão parados?", "integrante")
        self.assertEqual(r["intencao"], "parados")
        # "Sono e desempenho" começou em 2019 e não tem data nova desde então
        self.assertIn("Sono e desempenho", [i["rotulo"] for i in r["itens"]])

    def test_a_agenda_de_hoje_e_a_da_semana_sao_recortes_diferentes(self):
        self.db.execute(
            "INSERT INTO events (kind, title, start_at) VALUES ('reuniao', ?, ?)",
            ("Reunião do grupo", f"{self.hoje + timedelta(days=3)}T14:00:00"))
        self.db.conn.commit()
        hoje = self.perguntar("qual é a agenda de hoje?")
        semana = self.perguntar("quais compromissos temos?")
        self.assertEqual(hoje["numero"], 0)
        self.assertEqual(semana["numero"], 1)

    def test_a_hora_do_compromisso_aparece(self):
        self.db.execute(
            "INSERT INTO events (kind, title, start_at) VALUES ('reuniao', ?, ?)",
            ("Qualificação", f"{self.hoje}T14:30:00"))
        self.db.conn.commit()
        r = self.perguntar("o que tem na agenda hoje?")
        self.assertIn("14:30", r["itens"][0]["valor"])

    def test_o_dia_inteiro_nao_vira_meia_noite(self):
        """"00:00" na frente faz quem lê entender que a reunião é à meia-noite."""
        self.db.execute(
            "INSERT INTO events (kind, title, start_at, all_day)"
            " VALUES ('congresso', ?, ?, 1)", ("Congresso", f"{self.hoje}T00:00:00"))
        self.db.conn.commit()
        r = self.perguntar("o que tem na agenda hoje?")
        self.assertNotIn("00:00", r["itens"][0]["valor"])
        self.assertIn("dia inteiro", r["itens"][0]["valor"])


class TestOQueAnaNaoFaz(BaseDaAna):
    """A parte que importa: ela não inventa, e não vaza."""

    def test_a_pergunta_que_ela_nao_entende_vira_um_nao_sei(self):
        r = self.perguntar("qual a cor do céu?")
        self.assertFalse(r["entendi"])
        self.assertIsNone(r["numero"])
        self.assertEqual(r["itens"], [])
        self.assertIn("não sei", r["resposta"].lower())

    def test_o_nao_sei_vem_com_o_que_ela_sabe(self):
        """Um "não sei" sozinho ensina a desistir."""
        r = self.perguntar("me fala do universo")
        self.assertTrue(r["exemplos"])
        self.assertTrue(all(e["pergunta"] for e in r["exemplos"]))

    def test_toda_resposta_diz_de_onde_saiu_o_numero(self):
        """Número sem fonte na tela é indistinguível de palpite."""
        for pergunta in ("quantos artigos o laboratório tem?",
                         "quais artigos estão submetidos?",
                         "quantas pessoas tem o laboratório?",
                         "quais são as linhas de pesquisa?"):
            with self.subTest(pergunta=pergunta):
                r = self.perguntar(pergunta)
                self.assertTrue(r["entendi"])
                self.assertTrue(r["fonte"], f"sem fonte: {pergunta}")

    def test_a_coluna_nao_mente_sobre_o_que_ha_nela(self):
        """"Motriz" embaixo de "Quanto" não é leitura, é ruído."""
        publicados = self.perguntar("quantos artigos publicamos em 2019?")
        self.assertEqual(list(publicados["colunas"]), ["Artigo", "Revista"])
        acervo = self.perguntar("quantos artigos o laboratório tem?")
        self.assertEqual(list(acervo["colunas"]), ["Situação", "Quantos"])

    def test_toda_resposta_com_lista_declara_as_colunas(self):
        for pergunta, perfil in (("quantos artigos o laboratório tem?", "leitura"),
                                 ("quantos artigos publicamos em 2019?", "leitura"),
                                 ("quais artigos estão submetidos?", "leitura"),
                                 ("quais artigos estão parados?", "integrante"),
                                 ("o que tem na agenda?", "leitura"),
                                 ("quantas pessoas tem o laboratório?", "leitura"),
                                 ("quais são as linhas de pesquisa?", "leitura"),
                                 ("o que falta preencher?", "integrante"),
                                 ("quem sai do laboratório?", "coordenacao")):
            with self.subTest(pergunta=pergunta):
                r = self.perguntar(pergunta, perfil)
                self.assertTrue(r["entendi"])
                self.assertEqual(len(r["colunas"]), 2)

    def test_a_pergunta_da_coordenacao_e_recusada_a_quem_tem_leitura(self):
        r = self.perguntar("quem sai do laboratório este ano?", "leitura")
        self.assertTrue(r["entendi"])      # entendeu; o que não pode é responder
        self.assertTrue(r.get("negado"))
        self.assertIsNone(r["numero"])
        self.assertEqual(r["itens"], [])

    def test_a_recusa_nao_se_confunde_com_o_nao_sei(self):
        """Quem recebe "não entendi" repete a pergunta de dez maneiras."""
        negada = self.perguntar("quem sai do laboratório este ano?", "leitura")
        ignorada = self.perguntar("qual a cor do céu?", "leitura")
        self.assertTrue(negada["entendi"])
        self.assertFalse(ignorada["entendi"])
        self.assertIn("coordenacao", negada["resposta"])

    def test_a_coordenacao_recebe_a_mesma_pergunta_respondida(self):
        r = self.perguntar("quem sai do laboratório este ano?", "coordenacao")
        self.assertTrue(r["entendi"])
        self.assertFalse(r.get("negado"))
        self.assertIsNotNone(r["numero"])

    def test_os_exemplos_nao_oferecem_o_que_sera_recusado(self):
        leitura = {e["code"] for e in ana.exemplos("leitura")}
        coordenacao = {e["code"] for e in ana.exemplos("coordenacao")}
        self.assertNotIn("prazos", leitura)
        self.assertIn("prazos", coordenacao)
        self.assertTrue(leitura < coordenacao)

    def test_a_pergunta_vazia_nao_estoura(self):
        r = self.perguntar("")
        self.assertFalse(r["entendi"])
        self.assertTrue(r["exemplos"])

    def test_a_particula_do_nome_nao_aponta_ninguem(self):
        """"Maria DAS Graças" e "quantos artigos DAS linhas" casariam pelo "das".

        E a resposta sairia com o nome dela, sobre uma pergunta que não
        era sobre ela -- que é a forma mais convincente de estar errado.
        """
        self.db.execute("INSERT INTO members (full_name, name_key) VALUES (?, ?)",
                        ("Maria das Graças Silva", "maria_gracas"))
        self.db.conn.commit()
        palavras = ana._palavras("quantos artigos das linhas de pesquisa?")
        self.assertIsNone(ana._pessoa_da_pergunta(self.db, palavras))
        # e o nome de verdade continua achando a pessoa
        self.assertIsNotNone(ana._pessoa_da_pergunta(
            self.db, ana._palavras("quantos artigos da Maria?")))

    def test_um_pedaco_de_nome_nao_aponta_ninguem(self):
        """"ana" dentro de "Juliana" apontaria a pessoa errada com toda a certeza."""
        self.db.execute("INSERT INTO members (full_name, name_key) VALUES (?, ?)",
                        ("Juliana", "juliana"))
        self.db.conn.commit()
        palavras = ana._palavras("quantos artigos da ana?")
        self.assertIsNone(ana._pessoa_da_pergunta(self.db, palavras))

    def test_o_nome_desconhecido_nao_vira_zero(self):
        """"0 artigos" e "não sei quem é" são respostas diferentes."""
        r = self.perguntar("quantos artigos do Fulano de Tal?")
        self.assertNotEqual(r["intencao"], "pessoa")


class TestAnaPelaRede(unittest.TestCase):
    """O caminho inteiro, com cookie, como o navegador faz."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "rede.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        ingest_excel.ingest_articles(db, [
            {"title": "Ansiedade em atletas", "authors": "Andrade",
             "status": "Publicado", "year_published": "2019"},
        ])
        auth.create_account(db, "Alexandro Andrade", "coord@udesc.br", "senhaforte123",
                            role="coordenacao")
        auth.create_account(db, "Visitante", "visita@udesc.br", "senhaforte123",
                            role="leitura")
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

    def call(self, path, cookie=None):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}")
        if cookie:
            request.add_header("Cookie", f"{api.COOKIE_NAME}={cookie}")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    def entrar(self, login):
        dados = json.dumps({"login": login, "senha": "senhaforte123"}).encode()
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login", data=dados,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            return (response.headers.get("Set-Cookie") or "").split("=")[1].split(";")[0]

    def test_sem_entrar_nao_responde(self):
        status, _ = self.call("/api/ana?pergunta=quantos%20artigos")
        self.assertEqual(status, 401)

    def test_responde_com_a_fonte(self):
        token = self.entrar("coord@udesc.br")
        status, body = self.call("/api/ana?pergunta=quantos+artigos+o+laboratorio+tem",
                                 cookie=token)
        self.assertEqual(status, 200)
        self.assertEqual(body["numero"], 1)
        self.assertTrue(body["fonte"])

    def test_o_perfil_vale_na_rede_tambem(self):
        """O perfil vai para dentro da Ana: a recusa é dela, não da rota."""
        leitura = self.entrar("visita@udesc.br")
        status, body = self.call("/api/ana?pergunta=quem+sai+do+laboratorio+este+ano",
                                 cookie=leitura)
        self.assertEqual(status, 200)
        self.assertTrue(body["negado"])
        self.assertIsNone(body["numero"])

    def test_a_pergunta_vazia_devolve_o_que_ela_sabe(self):
        token = self.entrar("coord@udesc.br")
        status, body = self.call("/api/ana?pergunta=", cookie=token)
        self.assertEqual(status, 200)
        self.assertTrue(body["exemplos"])


class TestOComandoDaAna(BaseDaAna):
    """Ana pela janela preta, para quem está com o cmd aberto.

    A tela exige servidor de pé e alguém logado, e nem sempre está --
    quem quer conferir um número antes de uma reunião pergunta daqui.
    """

    def rodar(self, *pergunta):
        import lape_agent

        args = lape_agent.build_parser().parse_args(
            ["--db", str(self.db.path), "ana", *pergunta])
        with contextlib.redirect_stdout(io.StringIO()) as saida:
            codigo = args.func(args)
        return codigo, saida.getvalue()

    def test_responde_e_diz_de_onde_saiu(self):
        codigo, saida = self.rodar("quantos", "artigos", "o", "laboratorio", "tem")
        self.assertEqual(codigo, 0)
        self.assertIn("4 artigo(s)", saida)
        self.assertIn("de onde saiu", saida)

    def test_a_pergunta_que_ela_nao_entende_lista_o_que_da_para_perguntar(self):
        codigo, saida = self.rodar("qual", "a", "cor", "do", "ceu")
        self.assertEqual(codigo, 0)
        self.assertIn("nao sei" if "nao sei" in saida.lower() else "não sei",
                      saida.lower())
        self.assertIn("quantos artigos o laboratório tem?", saida)

    def test_sem_pergunta_nenhuma_nao_estoura(self):
        codigo, saida = self.rodar()
        self.assertEqual(codigo, 0)
        self.assertTrue(saida.strip())


class TestATelaDaAna(unittest.TestCase):
    """A metade que mora no navegador."""

    @classmethod
    def setUpClass(cls):
        cls.html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        cls.trecho = cls.html[cls.html.index("VIEWS.ana = {"):]
        cls.trecho = cls.trecho[:cls.trecho.index("VIEWS.senha = {")]

    def test_a_tela_esta_no_menu(self):
        """Registrar em VIEWS não basta: a ordem do menu é explícita."""
        ordem = self.html[self.html.index("const ORDER ="):]
        self.assertIn('"ana"', ordem[:ordem.index("]")])

    def test_a_tela_tem_icone(self):
        icones = self.html[self.html.index("const ICONE = {"):]
        self.assertIn("ana:", icones[:icones.index("};")])

    def test_a_tela_mostra_a_fonte_da_resposta(self):
        self.assertIn("de onde saiu", self.trecho)
        self.assertIn("d.fonte", self.trecho)

    def test_os_exemplos_vem_do_servidor(self):
        """Uma lista escrita na tela envelhece em silêncio a cada pergunta nova."""
        self.assertIn("d.exemplos", self.trecho)
        self.assertIn("/api/ana", self.trecho)

    def test_a_pergunta_vai_codificada(self):
        """"quantos artigos & submissões" quebraria a query string."""
        self.assertIn("encodeURIComponent", self.trecho)


if __name__ == "__main__":
    unittest.main()
