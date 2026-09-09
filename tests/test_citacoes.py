#!/usr/bin/env python3
"""Testes da coleta de citacoes na Scopus e na Web of Science.

    python3 -m unittest tests.test_citacoes -v

Sao as duas unicas bases do sistema que exigem chave, e o modo de falhar
delas e sempre o mesmo: devolver zero. Zero porque nao ha chave, zero
porque nao ha DOI, zero porque a chave nao vale, zero porque a biblioteca
de rede nao estava instalada. Quatro causas, uma tela. O que estes testes
guardam e a diferenca entre elas.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_citations  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseFalsa(BaseHTTPRequestHandler):
    """Uma Scopus e uma WoS de mentira, com as respostas de verdade."""

    respostas: dict = {}
    pedidos: list = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        partes = urlparse(self.path)
        self.pedidos.append({"caminho": partes.path,
                             "params": parse_qs(partes.query),
                             # nome de cabecalho nao tem caixa (RFC 9110), e
                             # urllib normaliza a sua: X-ELS-APIKey chega como
                             # X-els-apikey. Comparar em minusculas e o certo.
                             "cabecalhos": {k.lower(): v
                                            for k, v in self.headers.items()}})
        codigo, corpo = self.respostas.get(partes.path, (404, {}))
        bruto = json.dumps(corpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(bruto)))
        self.end_headers()
        self.wfile.write(bruto)


class BaseComServidor(unittest.TestCase):
    SCOPUS = "/content/search/scopus"
    WOS = "/apis/wos-starter/v1/documents"

    def setUp(self):
        BaseFalsa.respostas = {}
        BaseFalsa.pedidos = []
        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), BaseFalsa)
        porta = self.servidor.server_address[1]
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.addCleanup(self.servidor.server_close)
        self.addCleanup(self.servidor.shutdown)
        base = f"http://127.0.0.1:{porta}"
        self.trocar(ingest_citations, "SCOPUS_SEARCH", base + self.SCOPUS)
        self.trocar(ingest_citations, "WOS_SEARCH", base + self.WOS)
        # sem espera entre chamadas: o teste nao precisa ser gentil com um
        # servidor que roda dentro dele
        self.trocar(ingest_citations, "THROTTLE_SECONDS", 0)

        # A OpenAlex nao pede chave, e por isso responde em TODA rodada.
        # Deixa-la sair para a rede de verdade dentro do teste faria o
        # resultado depender da internet e de uma contagem que muda sozinha.
        # Por padrao ela nao acha nada, que e o comportamento antigo destes
        # testes; quem quiser um numero chama `responder_openalex`.
        import lape.sources as fontes
        self.openalex = None
        self.trocar(fontes, "openalex_by_doi",
                    lambda doi, mailto=None: self.openalex)

    def trocar(self, modulo, nome, valor):
        antigo = getattr(modulo, nome)
        setattr(modulo, nome, valor)
        self.addCleanup(setattr, modulo, nome, antigo)

    def chaves(self, scopus="chave-scopus", wos="chave-wos", inst=""):
        # troca-se o `config` que o coletor lê, e não o módulo importado
        # aqui: é o mesmo objeto, e assim o teste não finge testar o config
        alvo = ingest_citations.config
        self.trocar(alvo, "SCOPUS_API_KEY", scopus)
        self.trocar(alvo, "WOS_API_KEY", wos)
        self.trocar(alvo, "SCOPUS_INST_TOKEN", inst)

    def banco(self, artigos):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Database(Path(tmp.name) / "c.sqlite")
        self.addCleanup(db.close)
        db.migrate()
        from lape.util import title_key
        for i, a in enumerate(artigos, 1):
            titulo = a.get("title", f"Artigo {i}")
            db.execute("INSERT INTO articles (title, title_key, status, doi,"
                       " year_published) VALUES (?, ?, 'publicado', ?, 2023)",
                       (titulo, title_key(titulo), a.get("doi")))
        db.conn.commit()
        return db

    def responder_scopus(self, citacoes, eid="2-s2.0-1"):
        BaseFalsa.respostas[self.SCOPUS] = (200, {"search-results": {"entry": [
            {"citedby-count": str(citacoes), "eid": eid}]}})

    def responder_openalex(self, citacoes):
        self.openalex = {"citations": citacoes, "external_id": "https://openalex.org/W1"}

    def responder_wos(self, citacoes, uid="WOS:000123"):
        BaseFalsa.respostas[self.WOS] = (200, {"hits": [
            {"uid": uid, "citations": [{"db": "WOS", "count": citacoes}]}]})


class TestLeituraDasRespostas(BaseComServidor):
    """O numero que sai de cada base e o numero que ela mandou."""

    def test_scopus_devolve_a_contagem_e_o_eid(self):
        self.responder_scopus(42)
        achado = ingest_citations.fetch_scopus("10.1000/x", "chave")
        self.assertEqual(achado, {"citations": 42, "scopus_id": "2-s2.0-1"})

    def test_a_chave_da_scopus_vai_no_cabecalho_certo(self):
        self.responder_scopus(1)
        ingest_citations.fetch_scopus("10.1000/x", "minha-chave", "meu-token")
        cabecalhos = BaseFalsa.pedidos[0]["cabecalhos"]
        self.assertEqual(cabecalhos.get("x-els-apikey"), "minha-chave")
        self.assertEqual(cabecalhos.get("x-els-insttoken"), "meu-token")

    def test_a_busca_da_scopus_e_por_doi(self):
        self.responder_scopus(1)
        ingest_citations.fetch_scopus("10.1016/j.psychsport.2020.101", "k")
        query = BaseFalsa.pedidos[0]["params"]["query"][0]
        self.assertEqual(query, 'DOI("10.1016/j.psychsport.2020.101")')

    def test_artigo_desconhecido_da_none_e_nao_zero(self):
        """Zero e um numero; "nao achei" nao e.

        Gravar zero apagaria a contagem que veio da planilha e poria na
        tela um numero que a base nunca disse.
        """
        BaseFalsa.respostas[self.SCOPUS] = (200, {"search-results": {"entry": []}})
        self.assertIsNone(ingest_citations.fetch_scopus("10.1000/x", "k"))
        BaseFalsa.respostas[self.WOS] = (200, {"hits": []})
        self.assertIsNone(ingest_citations.fetch_wos("10.1000/x", "k"))

    def test_o_erro_da_scopus_dentro_do_200_tambem_e_nao_achei(self):
        BaseFalsa.respostas[self.SCOPUS] = (200, {"search-results": {"entry": [
            {"error": "Result set was empty"}]}})
        self.assertIsNone(ingest_citations.fetch_scopus("10.1000/x", "k"))

    def test_wos_devolve_a_contagem_e_o_uid(self):
        self.responder_wos(17)
        achado = ingest_citations.fetch_wos("10.1000/x", "chave")
        self.assertEqual(achado, {"citations": 17, "wos_id": "WOS:000123"})

    def test_wos_conta_a_base_wos_e_nao_a_soma_das_bases(self):
        """`citations` vem por indice, e a tela promete o numero da WoS.

        Somar tudo inflaria a contagem com o que ninguem foi conferir na
        Web of Science -- e o mural mostra esse numero com o nome dela.
        """
        BaseFalsa.respostas[self.WOS] = (200, {"hits": [{"uid": "W1", "citations": [
            {"db": "WOS", "count": 10}, {"db": "BCI", "count": 7},
            {"db": "PPRN", "count": 3}]}]})
        self.assertEqual(ingest_citations.fetch_wos("10.1000/x", "k")["citations"], 10)

    def test_wos_sem_a_base_wos_na_lista_ainda_devolve_algo(self):
        BaseFalsa.respostas[self.WOS] = (200, {"hits": [
            {"uid": "W1", "citations": [{"db": "BCI", "count": 4}]}]})
        self.assertEqual(ingest_citations.fetch_wos("10.1000/x", "k")["citations"], 4)

    def test_a_chave_da_wos_vai_no_cabecalho_certo(self):
        self.responder_wos(1)
        ingest_citations.fetch_wos("10.1000/x", "chave-clarivate")
        self.assertEqual(BaseFalsa.pedidos[0]["cabecalhos"].get("x-apikey"),
                         "chave-clarivate")


class TestChaveRecusada(BaseComServidor):
    """401, 403 e 429 nao se resolvem tentando o proximo artigo."""

    def test_chave_invalida_desliga_a_fonte_na_hora(self):
        BaseFalsa.respostas[self.SCOPUS] = (401, {"error": "invalid key"})
        self.responder_wos(5)
        self.chaves()
        db = self.banco([{"doi": f"10.1000/{i}"} for i in range(6)])
        r = ingest_citations.update_citations(db, verbose=False)
        # uma tentativa na Scopus, seis na WoS -- e nao seis em cada
        scopus = [p for p in BaseFalsa.pedidos if p["caminho"] == self.SCOPUS]
        self.assertEqual(len(scopus), 1)
        self.assertIn("scopus", r["recusadas"])
        self.assertEqual(r["scopus"], 0)

    def test_uma_base_recusada_nao_leva_a_outra_junto(self):
        BaseFalsa.respostas[self.SCOPUS] = (403, {"error": "no permission"})
        self.responder_wos(9)
        self.chaves()
        db = self.banco([{"doi": "10.1000/a"}, {"doi": "10.1000/b"}])
        r = ingest_citations.update_citations(db, verbose=False)
        self.assertEqual(r["wos"], 2)
        self.assertEqual(db.scalar("SELECT SUM(wos_citations) FROM articles"), 18)

    def test_o_motivo_da_recusa_chega_em_palavras(self):
        BaseFalsa.respostas[self.SCOPUS] = (429, {"error": "quota"})
        BaseFalsa.respostas[self.WOS] = (429, {"error": "quota"})
        self.chaves()
        db = self.banco([{"doi": "10.1000/a"}])
        r = ingest_citations.update_citations(db, verbose=False)
        self.assertIn("cota do dia esgotada", r["recusadas"]["scopus"])
        self.assertIn("cota do dia esgotada", r["recusadas"]["wos"])

    def test_erro_passageiro_nao_desliga_a_fonte(self):
        # 500 e do outro lado e pode passar; a proxima linha ainda tenta
        BaseFalsa.respostas[self.SCOPUS] = (500, {"error": "oops"})
        self.chaves(wos="")
        db = self.banco([{"doi": "10.1000/a"}, {"doi": "10.1000/b"}])
        r = ingest_citations.update_citations(db, verbose=False)
        self.assertEqual(r["erros"], 2)
        self.assertEqual(r["recusadas"], {})


class TestAColeta(BaseComServidor):
    """De ponta a ponta: o banco, o snapshot e o que se responde a tela."""

    def test_grava_os_dois_numeros_e_os_dois_ids(self):
        self.responder_scopus(30, eid="2-s2.0-777")
        self.responder_wos(21, uid="WOS:000999")
        self.chaves()
        db = self.banco([{"doi": "10.1000/a"}])
        ingest_citations.update_citations(db, verbose=False)
        linha = db.dicts("SELECT scopus_citations, wos_citations, scopus_id, wos_id,"
                         " citations_updated_at FROM articles")[0]
        self.assertEqual(linha["scopus_citations"], 30)
        self.assertEqual(linha["wos_citations"], 21)
        self.assertEqual(linha["scopus_id"], "2-s2.0-777")
        self.assertEqual(linha["wos_id"], "WOS:000999")
        self.assertTrue(linha["citations_updated_at"])

    def test_cada_coleta_deixa_um_retrato_no_tempo(self):
        self.responder_scopus(30)
        self.responder_wos(21)
        self.chaves()
        db = self.banco([{"doi": "10.1000/a"}])
        ingest_citations.update_citations(db, verbose=False)
        fontes = {r["source"]: r["citations"] for r in
                  db.dicts("SELECT source, citations FROM citation_snapshots")}
        self.assertEqual(fontes, {"scopus": 30, "wos": 21})

    def test_artigo_sem_doi_nao_e_consultado(self):
        self.responder_scopus(1)
        self.responder_wos(1)
        self.chaves()
        db = self.banco([{"doi": None}, {"doi": "   "}, {"doi": "10.1000/a"}])
        r = ingest_citations.update_citations(db, verbose=False)
        self.assertEqual(r["consultados"], 1)
        self.assertEqual(r["sem_doi"], 2)

    def test_acervo_inteiro_sem_doi_diz_isso_em_vez_de_zero(self):
        """O caso do laboratorio hoje: 19 artigos, nenhum DOI.

        Sem esta saida a coleta responderia "scopus=0 wos=0 erros=0" --
        o relatorio de quem procurou e nao achou, dado por quem nao
        chegou a perguntar nada.
        """
        self.chaves()
        db = self.banco([{"doi": None}, {"doi": None}])
        r = ingest_citations.update_citations(db, verbose=False)
        self.assertEqual(BaseFalsa.pedidos, [])
        self.assertEqual(r["sem_doi"], 2)
        ultimo = db.dicts("SELECT status, message FROM ingest_log"
                          " ORDER BY id DESC LIMIT 1")[0]
        self.assertEqual(ultimo["status"], "ignorado")
        self.assertIn("DOI", ultimo["message"])

    def test_sem_chave_nao_se_bate_na_porta_de_quem_pede_chave(self):
        self.chaves(scopus="", wos="")
        db = self.banco([{"doi": "10.1000/a"}])
        r = ingest_citations.update_citations(db, verbose=False)
        self.assertEqual(BaseFalsa.pedidos, [])       # Scopus e WoS, intactas
        self.assertEqual((r["scopus"], r["wos"]), (0, 0))

    def test_sem_chave_a_openalex_ainda_responde(self):
        """A rodada nao para mais por falta de chave.

        Parava, e parava junto a OpenAlex, que nao pede chave nenhuma. Um
        laboratorio sem convenio apertava o botao, lia "chaves ausentes" e
        ficava com a coluna em branco tendo, na base aberta, milhares de
        citacoes -- foi o que pos "0 citacoes" numa parede com quatro mil.
        """
        self.chaves(scopus="", wos="")
        self.responder_openalex(137)
        db = self.banco([{"doi": "10.1000/a"}])
        r = ingest_citations.update_citations(db, verbose=False)
        self.assertEqual(r["openalex"], 1)
        self.assertEqual(db.scalar("SELECT openalex_citations FROM articles"), 137)
        self.assertEqual(BaseFalsa.pedidos, [])       # e sem tocar nas outras duas

    def test_a_openalex_grava_na_coluna_dela_e_nao_na_das_outras(self):
        self.chaves(scopus="", wos="")
        self.responder_openalex(50)
        db = self.banco([{"doi": "10.1000/a"}])
        ingest_citations.update_citations(db, verbose=False)
        linha = db.dicts("SELECT openalex_citations, scopus_citations,"
                         "       wos_citations FROM articles")[0]
        self.assertEqual(linha["openalex_citations"], 50)
        self.assertIsNone(linha["scopus_citations"] or None)
        self.assertIsNone(linha["wos_citations"] or None)

    def test_as_tres_bases_convivem_no_mesmo_artigo(self):
        # numeros diferentes na mesma referencia sao legitimos: cada base
        # indexa um conjunto diferente de revistas
        self.chaves()
        self.responder_scopus(30)
        self.responder_wos(21)
        self.responder_openalex(44)
        db = self.banco([{"doi": "10.1000/a"}])
        r = ingest_citations.update_citations(db, verbose=False)
        self.assertEqual((r["scopus"], r["wos"], r["openalex"]), (1, 1, 1))
        linha = db.dicts("SELECT scopus_citations, wos_citations,"
                         "       openalex_citations FROM articles")[0]
        self.assertEqual((linha["scopus_citations"], linha["wos_citations"],
                          linha["openalex_citations"]), (30, 21, 44))

    def test_a_openalex_sem_resposta_nao_zera_o_que_ja_havia(self):
        # artigo que a base aberta nao conhece nao pode apagar a contagem
        # que a planilha ou outra rodada ja tinham posto ali
        self.chaves(scopus="", wos="")
        db = self.banco([{"doi": "10.1000/a"}])
        db.execute("UPDATE articles SET openalex_citations = 12")
        db.conn.commit()
        self.openalex = None
        ingest_citations.update_citations(db, verbose=False)
        self.assertEqual(db.scalar("SELECT openalex_citations FROM articles"), 12)

    def test_so_uma_chave_configurada_consulta_so_aquela_base(self):
        self.responder_scopus(11)
        self.responder_wos(99)
        self.chaves(wos="")
        db = self.banco([{"doi": "10.1000/a"}])
        ingest_citations.update_citations(db, verbose=False)
        self.assertEqual([p["caminho"] for p in BaseFalsa.pedidos], [self.SCOPUS])
        # segue nulo: nunca foi consultado, e nulo nao e zero
        self.assertIsNone(db.scalar("SELECT wos_citations FROM articles"))
        self.assertEqual(db.scalar("SELECT scopus_citations FROM articles"), 11)

    def test_o_limite_e_respeitado(self):
        self.responder_scopus(1)
        self.chaves(wos="")
        db = self.banco([{"doi": f"10.1000/{i}"} for i in range(5)])
        r = ingest_citations.update_citations(db, limit=2, verbose=False)
        self.assertEqual(r["consultados"], 2)


class TestORetratoAntesDeApertar(BaseComServidor):
    """`situacao()` responde o que a tela precisa dizer sem tentar nada."""

    def test_diz_quais_chaves_estao_presentes_sem_mostrar_nenhuma(self):
        self.chaves(scopus="segredo-que-nao-pode-vazar", wos="")
        db = self.banco([{"doi": "10.1000/a"}])
        s = ingest_citations.situacao(db)
        por_chave = {f["chave"]: f for f in s["fontes"]}
        self.assertTrue(por_chave["scopus"]["configurada"])
        self.assertFalse(por_chave["wos"]["configurada"])
        self.assertNotIn("segredo-que-nao-pode-vazar", json.dumps(s))

    def test_conta_os_artigos_com_e_sem_doi(self):
        self.chaves()
        db = self.banco([{"doi": "10.1000/a"}, {"doi": None}, {"doi": ""}])
        s = ingest_citations.situacao(db)
        self.assertEqual((s["com_doi"], s["sem_doi"], s["artigos"]), (1, 2, 3))

    def test_diz_o_nome_da_variavel_que_falta(self):
        # sem isso, "sem chave" na tela nao ensina o que fazer a respeito
        self.chaves(scopus="", wos="")
        db = self.banco([])
        variaveis = {f["variavel"] for f in ingest_citations.situacao(db)["fontes"]
                     if f["pede_chave"]}
        self.assertEqual(variaveis, {"SCOPUS_API_KEY", "WOS_API_KEY"})

    def test_a_base_que_nao_pede_chave_ja_esta_configurada(self):
        """Marca-la como "falta configurar" bloquearia o botao a toa.

        A tela pediria uma chave que nao existe, e quem lesse iria procurar
        um convenio para uma base aberta.
        """
        self.chaves(scopus="", wos="")
        db = self.banco([])
        fontes = {f["chave"]: f for f in ingest_citations.situacao(db)["fontes"]}
        self.assertFalse(fontes["openalex"]["pede_chave"])
        self.assertTrue(fontes["openalex"]["configurada"])
        self.assertFalse(fontes["scopus"]["configurada"])


class TestOCartaoDaTela(unittest.TestCase):
    """O que o cartao do painel diz agora que ha uma base sem chave."""

    @classmethod
    def setUpClass(cls):
        js = (ROOT / "scripts" / "lape" / "templates" / "panorama.js").read_text(
            encoding="utf-8")
        # so a funcao, e nao ate o proximo divisor do arquivo: um recorte
        # largo faria "o botao nao some" passar por causa de um `return`
        # de outra funcao qualquer no meio do caminho
        inicio = js.index("function cartaoDasCitacoes()")
        cls.corpo = js[inicio:js.index("\n}\n", inicio) + 3]

    def test_sem_chave_conta_so_quem_pede_chave(self):
        """Contar a OpenAlex aqui tornaria a condicao impossivel.

        Ela esta sempre configurada, e as instrucoes de como ligar Scopus
        e WoS nunca mais apareceriam na tela.
        """
        self.assertIn("f.pede_chave", self.corpo)
        self.assertNotIn(
            'const semChave = (cit.fontes || []).every(function (f) { return !f.configurada; });',
            self.corpo)

    def test_a_base_aberta_nao_pede_variavel_de_ambiente(self):
        # "falta a variavel null" mandaria alguem procurar convenio para
        # uma base que responde a qualquer um
        self.assertIn('!f.pede_chave ? " · aberta"', self.corpo)

    def test_o_resultado_mostra_as_tres_bases(self):
        self.assertIn('"OpenAlex: " + (r.openalex || 0)', self.corpo)

    def test_o_botao_nao_some_mais_por_falta_de_chave(self):
        # sem chave a rodada nao e vazia: ela consulta a base aberta
        antes = self.corpo.index("if (semChave) {")
        trecho = self.corpo[antes:self.corpo.index("Conferir as citações agora")]
        self.assertNotIn("return corpo;", trecho,
                         "o cartão volta antes do botão quando falta chave")


class TestSemDependenciaDeRede(unittest.TestCase):
    """A coleta roda com a biblioteca padrao, e so com ela."""

    def test_nada_de_requests(self):
        """`import requests` num `try` era uma falha silenciosa esperando.

        Sem a biblioteca instalada, a funcao devolvia None -- o mesmo que
        "a base nao conhece este artigo". A maquina do laboratorio
        respondia "0 atualizados" com a chave certa e a rede boa.
        """
        fonte = (ROOT / "scripts" / "lape" / "ingest_citations.py").read_text(
            encoding="utf-8")
        # so as linhas de import de verdade: a palavra ainda aparece na
        # explicacao de por que ela saiu, e isso e comentario, nao codigo
        imports = [l for l in fonte.splitlines()
                   if l.startswith(("import ", "from ")) or l.strip().startswith(
                       ("import ", "from "))]
        self.assertNotIn("requests", " ".join(imports))
        self.assertIn("import urllib.request", fonte)

    def test_requirements_nao_pede_o_que_ninguem_usa(self):
        pedidos = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotIn("requests", pedidos)
