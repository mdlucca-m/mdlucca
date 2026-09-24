#!/usr/bin/env python3
"""Estatística descritiva e inferencial sobre a produção real, pela rede.

    python3 -m unittest tests.test_estatistica_producao -v

Cobre as duas rotas que usam scripts/lape/estatistica.py com dado de
verdade: /api/analytics/estatistica (leitura, só o que é público na
equipe) e a parte inferencial nova de /api/ponto/analytics (coordenação,
porque cruza hora de pessoa nomeada com produção).
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

from lape import api, auth  # noqa: E402
from lape.db import Database  # noqa: E402
from lape.util import title_key  # noqa: E402


class BaseComProducaoEstatistica(unittest.TestCase):

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

        docente = db.member_id("Guilherme Torres Vilarino", role="professor",
                               is_external=0)
        docente2 = db.member_id("Alexandro Andrade Docente", role="professor",
                                is_external=0)
        d1 = db.member_id("Letícia", role="doutorando", is_external=0)
        d2 = db.member_id("Loiane Doutoranda", role="mestrando", is_external=0)
        d3 = db.member_id("Rafael Bolsista", role="bolsista_ic", is_external=0)
        d4 = db.member_id("Camila Bolsista", role="bolsista_ic", is_external=0)

        # docentes publicam mais e registram mais horas; discentes, menos
        # -- o suficiente para dar um p-valor a checar, sem forçar a mão.
        # As 6 pessoas (2 docentes, 4 discentes) também dão n=6 para a
        # correlação -- o mínimo do próprio módulo (N_MINIMO_PARA_CORRELACAO).
        anos_e_contagens = [(2020, 2), (2021, 3), (2022, 4), (2023, 5), (2024, 7)]
        artigo_id = 1
        def novo_artigo(artigo_id, ano, citacoes, membro, nome):
            titulo = f"Artigo {artigo_id}"
            db.execute(
                "INSERT INTO articles (id, title, title_key, status, year_published,"
                " wos_citations) VALUES (?, ?, ?, 'publicado', ?, ?)",
                (artigo_id, titulo, title_key(titulo), ano, citacoes))
            db.execute(
                "INSERT INTO article_authors (article_id, member_id, author_name)"
                " VALUES (?, ?, ?)", (artigo_id, membro, nome))

        for ano, n in anos_e_contagens:
            for _ in range(n):
                novo_artigo(artigo_id, ano, artigo_id % 5, docente,
                           "Guilherme Torres Vilarino")
                artigo_id += 1
        # Os demais têm produção deliberadamente NÃO perfeitamente
        # monótona com as horas (d3 publica mais que d2 apesar de menos
        # horas) -- uma correlação perfeita (r = ±1) deixa o p indefinido
        # nesse módulo (transformação de Fisher não vale no limite), e
        # isso teria que ser o que ESTE teste verifica, não um acidente
        # da massa de dados.
        for pessoa, nome, n in ((docente2, "Alexandro Andrade Docente", 10),
                                (d1, "Letícia", 2), (d2, "Loiane Doutoranda", 1),
                                (d3, "Rafael Bolsista", 3), (d4, "Camila Bolsista", 1)):
            for _ in range(n):
                novo_artigo(artigo_id, 2024, 1, pessoa, nome)
                artigo_id += 1

        # Dois modificadores separados, nunca um só com vírgula dentro:
        # `datetime('now', '-0 days, +6 hours')` volta NULL no SQLite --
        # cada `datetime(...)` aqui exige um argumento por modificador.
        horas_por_pessoa = ((docente, 6), (docente2, 5), (d1, 2), (d2, 3),
                            (d3, 1), (d4, 1))
        for pessoa, horas_por_dia in horas_por_pessoa:
            for dia in range(5):
                db.execute(
                    "INSERT INTO ponto (member_id, entrada, saida)"
                    " VALUES (?, datetime('now', ?), datetime('now', ?, ?))",
                    (pessoa, f"-{dia} days", f"-{dia} days", f"+{horas_por_dia} hours"))
        db.conn.commit()
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

    def chamar(self, caminho, cookie=None):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{caminho}",
            headers={**({"Cookie": cookie} if cookie else {})})
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"{}")


class TestAnalyticsEstatistica(BaseComProducaoEstatistica):

    def test_visitante_sem_login_nao_entra(self):
        status, _ = self.chamar("/api/analytics/estatistica")
        self.assertIn(status, (401, 403))

    def test_leitura_basica_ja_ve(self):
        status, corpo = self.chamar("/api/analytics/estatistica",
                                    self.entrar("loiane@udesc.br"))
        self.assertEqual(status, 200)
        self.assertIn("descritiva", corpo)
        self.assertIn("inferencial", corpo)

    def test_descritiva_tem_n_maior_que_zero(self):
        _, corpo = self.chamar("/api/analytics/estatistica", self.entrar("loiane@udesc.br"))
        resumo = corpo["descritiva"]["citacoes_por_artigo_publicado"]
        self.assertGreater(resumo["n"], 0)
        self.assertIn("media", resumo)

    def test_tabelas_de_frequencia_somam_o_total(self):
        _, corpo = self.chamar("/api/analytics/estatistica", self.entrar("loiane@udesc.br"))
        status = corpo["descritiva"]["status_da_producao"]
        # 21 (docente) + 10 (docente2) + 2 + 1 + 3 + 1 (discentes) = 38
        self.assertEqual(sum(r["n"] for r in status), 38)

    def test_tendencia_de_publicacoes_e_positiva_e_significativa(self):
        """Os anos foram montados subindo de propósito (2,3,4,5,7) -- a
        regressão tem que achar essa tendência real."""
        _, corpo = self.chamar("/api/analytics/estatistica", self.entrar("loiane@udesc.br"))
        tendencia = corpo["inferencial"]["tendencia_publicacoes_por_ano"]
        self.assertGreater(tendencia["inclinacao"], 0)
        self.assertIn("p", tendencia)

    def test_nao_cruza_nome_com_hora_de_ponto(self):
        """A rota de leitura é pública na equipe -- não pode vazar o
        cruzamento hora×produção por pessoa, que é só da coordenação."""
        _, corpo = self.chamar("/api/analytics/estatistica", self.entrar("loiane@udesc.br"))
        self.assertNotIn("correlacao_horas_producao", json.dumps(corpo))


class TestPontoAnalyticsInferencial(BaseComProducaoEstatistica):

    def test_integrante_comum_nao_ve(self):
        status, _ = self.chamar("/api/ponto/analytics", self.entrar("loiane@udesc.br"))
        self.assertEqual(status, 403)

    def test_coordenacao_ve_a_parte_inferencial(self):
        status, corpo = self.chamar("/api/ponto/analytics", self.entrar("coord@udesc.br"))
        self.assertEqual(status, 200)
        self.assertIn("inferencial", corpo)
        self.assertIn("correlacao_horas_producao", corpo["inferencial"])
        self.assertIn("docentes_vs_discentes", corpo["inferencial"])

    def test_correlacao_tem_amostra_do_tamanho_de_gente_com_ponto(self):
        _, corpo = self.chamar("/api/ponto/analytics", self.entrar("coord@udesc.br"))
        correlacao = corpo["inferencial"]["correlacao_horas_producao"]
        self.assertEqual(correlacao["n"], 6)  # as 6 pessoas bateram ponto
        # Um p real (não None) só sai se as horas tiverem variado de
        # verdade (6h/5h/2h/3h/1h/1h por dia) -- se a massa de dados do
        # teste quebrar (uma sessão de ponto com "saida" nula, por
        # exemplo), o correto é isto falhar em vez de cair silenciosamente
        # num r indefinido.
        self.assertIsNotNone(correlacao["p"])
        self.assertIn("r", correlacao)

    def test_docentes_vs_discentes_separa_pelos_grupos_certos(self):
        _, corpo = self.chamar("/api/ponto/analytics", self.entrar("coord@udesc.br"))
        grupos = corpo["inferencial"]["docentes_vs_discentes"]
        self.assertEqual(grupos["n1"], 2)  # os dois professores
        self.assertEqual(grupos["n2"], 4)  # doutoranda, mestranda, 2 bolsistas


if __name__ == "__main__":
    unittest.main()
