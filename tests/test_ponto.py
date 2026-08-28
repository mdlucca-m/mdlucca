#!/usr/bin/env python3
"""Testes do ponto: entrada, saída e as horas que saem daí.

    python3 -m unittest tests.test_ponto -v

Um ponto mal feito mente com cara de número. Os testes aqui são as três
maneiras de ele mentir: o check-out esquecido que vira setenta e duas
horas de trabalho, a semana de três dias comparada com uma de sete, e a
hora presente lida como se fosse produção.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth, ponto  # noqa: E402
from lape.db import Database  # noqa: E402


class BasePonto(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.eu = self.db.member_id("Fulana de Tal")
        self.outra = self.db.member_id("Beltrano Silva")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def sessao(self, dia, hora_ini, hora_fim, member_id=None, atividade="trabalho"):
        self.db.execute(
            "INSERT INTO ponto (member_id, entrada, saida, atividade) VALUES (?, ?, ?, ?)",
            (member_id or self.eu, f"{dia} {hora_ini}:00", f"{dia} {hora_fim}:00", atividade))
        self.db.conn.commit()

    def aberta(self, quando, member_id=None):
        self.db.execute("INSERT INTO ponto (member_id, entrada) VALUES (?, ?)",
                        (member_id or self.eu, quando))
        self.db.conn.commit()


class TestBaterPonto(BasePonto):
    def test_entrar_e_sair_registra_a_sessao(self):
        ponto.entrar(self.db, self.eu, "escrevendo")
        aberto = ponto.aberto(self.db, self.eu)
        self.assertIsNotNone(aberto)
        self.assertEqual(aberto["atividade"], "escrevendo")

    def test_recem_entrado_esta_ha_zero_horas_e_nao_ha_nada(self):
        # a tela dizia "há —" no primeiro minuto, como se não soubesse
        ponto.entrar(self.db, self.eu)
        self.assertEqual(ponto.aberto(self.db, self.eu)["ha_horas"], 0)

    def test_bater_entrada_duas_vezes_nao_abre_duas(self):
        ponto.entrar(self.db, self.eu)
        ponto.entrar(self.db, self.eu)
        abertas = self.db.scalar(
            "SELECT COUNT(*) FROM ponto WHERE member_id = ? AND saida IS NULL", (self.eu,))
        self.assertEqual(abertas, 1)

    def test_clique_errado_e_descartado_e_nao_vira_zero_minuto(self):
        # gravar zero minuto entra na média depois e a puxa para baixo
        ponto.entrar(self.db, self.eu)
        resultado = ponto.sair(self.db, self.eu)
        self.assertFalse(resultado["fechou"])
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM ponto"), 0)

    def test_sair_sem_entrar_nao_inventa_sessao(self):
        resultado = ponto.sair(self.db, self.eu)
        self.assertFalse(resultado["fechou"])
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM ponto"), 0)

    def test_anotar_troca_a_atividade_sem_fechar(self):
        ponto.entrar(self.db, self.eu, "leitura")
        ponto.anotar(self.db, self.eu, "análise dos dados")
        aberto = ponto.aberto(self.db, self.eu)
        self.assertEqual(aberto["atividade"], "análise dos dados")
        self.assertIsNone(aberto["saida"])


class TestCheckOutEsquecido(BasePonto):
    """A falha clássica de todo ponto, e a única que estraga o número."""

    def test_sessao_longa_demais_e_fechada_e_marcada(self):
        # entra na sexta, esquece, e a segunda mostra setenta e duas horas
        tres_dias = (datetime.now() - timedelta(days=3)).strftime(ponto.FORMATO)
        self.aberta(tres_dias)
        self.assertEqual(ponto.fechar_esquecidos(self.db), 1)
        linha = self.db.dicts("SELECT saida, fechado_sozinho FROM ponto")[0]
        self.assertIsNotNone(linha["saida"])
        self.assertEqual(linha["fechado_sozinho"], 1)

    def test_a_duracao_inventada_nao_entra_na_soma(self):
        # houve trabalho, mas não dá para dizer quanto: contar seria mentir
        tres_dias = (datetime.now() - timedelta(days=3)).strftime(ponto.FORMATO)
        self.aberta(tres_dias)
        hoje = date.today()
        self.sessao(hoje.isoformat(), "09:00", "12:00")
        resumo = ponto.resumo(self.db, self.eu, hoje=hoje)
        self.assertEqual(resumo["mes"]["horas"], 3.0)
        self.assertGreaterEqual(resumo["mes"]["esquecidas"], 1)

    def test_sessao_dentro_do_limite_continua_aberta(self):
        # quem entrou hoje de manhã ainda está trabalhando
        duas_horas = (datetime.now() - timedelta(hours=2)).strftime(ponto.FORMATO)
        self.aberta(duas_horas)
        self.assertEqual(ponto.fechar_esquecidos(self.db), 0)
        self.assertIsNotNone(ponto.aberto(self.db, self.eu))


class TestComparacaoDePeriodos(BasePonto):
    def test_a_semana_e_comparada_ate_o_mesmo_ponto(self):
        # comparar uma semana de três dias com uma de sete acusa queda toda
        # segunda-feira, e a queda seria do calendário, não do trabalho
        quarta = date(2026, 8, 26)
        for d in range(3):                       # segunda, terça, quarta desta semana
            self.sessao((quarta - timedelta(days=2 - d)).isoformat(), "09:00", "12:00")
        semana_passada = quarta - timedelta(days=7)
        for d in range(5):                       # a semana passada inteira
            self.sessao((semana_passada - timedelta(days=2 - d)).isoformat(), "09:00", "12:00")
        resumo = ponto.resumo(self.db, self.eu, hoje=quarta)
        # três dias contra os três dias equivalentes: empate, não queda
        self.assertEqual(resumo["semana"]["horas"], 9.0)
        self.assertEqual(resumo["semana"]["antes"], 9.0)
        self.assertEqual(resumo["semana"]["variacao"], 0.0)

    def test_sem_base_anterior_nao_se_inventa_aumento(self):
        # "aumento infinito" não diz nada a ninguém
        hoje = date(2026, 8, 26)
        self.sessao(hoje.isoformat(), "09:00", "12:00")
        self.assertIsNone(ponto.resumo(self.db, self.eu, hoje=hoje)["dia"]["variacao"])

    def test_o_dia_de_ontem_e_a_base_de_hoje(self):
        hoje = date(2026, 8, 26)
        self.sessao(hoje.isoformat(), "09:00", "13:00")
        self.sessao((hoje - timedelta(days=1)).isoformat(), "09:00", "11:00")
        dia = ponto.resumo(self.db, self.eu, hoje=hoje)["dia"]
        self.assertEqual(dia["horas"], 4.0)
        self.assertEqual(dia["antes"], 2.0)
        self.assertEqual(dia["variacao"], 100.0)


class TestSerieEQuadro(BasePonto):
    def test_dia_sem_registro_entra_com_zero(self):
        # série que pula os dias vazios desenha uma linha contínua de
        # trabalho que nunca houve
        hoje = date(2026, 8, 26)
        self.sessao(hoje.isoformat(), "09:00", "12:00")
        serie = ponto.serie(self.db, self.eu, dias=5, hoje=hoje)
        self.assertEqual(len(serie), 5)
        self.assertEqual([x["horas"] for x in serie], [0, 0, 0, 0, 3.0])

    def test_o_quadro_de_agora_mostra_quem_esta_dentro(self):
        ponto.entrar(self.db, self.eu, "coleta")
        agora = ponto.agora(self.db)
        self.assertEqual(len(agora), 1)
        self.assertEqual(agora[0]["quem"], "Fulana de Tal")
        self.assertEqual(agora[0]["atividade"], "coleta")

    def test_quem_saiu_some_do_quadro(self):
        self.sessao(date.today().isoformat(), "09:00", "12:00")
        self.assertEqual(ponto.agora(self.db), [])

    def test_horas_por_pessoa_separa_quem_e_quem(self):
        hoje = date.today()
        self.sessao(hoje.isoformat(), "09:00", "13:00")
        self.sessao(hoje.isoformat(), "09:00", "11:00", member_id=self.outra)
        pessoas = {p["quem"]: p["horas"] for p in ponto.por_pessoa(self.db, hoje=hoje)}
        self.assertEqual(pessoas["Fulana de Tal"], 4.0)
        self.assertEqual(pessoas["Beltrano Silva"], 2.0)


class TestHoraNaoEProducao(BasePonto):
    def test_a_producao_vem_ao_lado_e_nao_dentro(self):
        # juntar hora e produção num índice só esconderia qual das duas
        # mudou -- e é justamente a diferença entre elas que interessa
        from lape import ingest_excel
        ingest_excel.ingest_articles(self.db, [
            {"title": "Um artigo publicado agora", "status": "Publicado",
             "published_on": date.today().isoformat()}])
        producao = ponto.producao_no_periodo(self.db, dias=30)
        self.assertEqual(producao["publicados"], 1)
        self.assertNotIn("horas", producao)


class TestRotasDoPonto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "t.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Ana Souza", "ana@udesc.br", "senhaforte123", role="admin")
        auth.create_account(db, "Bento Lima", "bento@udesc.br", "senhaforte123",
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

    def entrar_no_sistema(self, login):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"login": login, "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return r.headers.get("Set-Cookie", "").split(";")[0]

    def chamar(self, caminho, cookie=None, metodo="GET", corpo=None):
        dados = json.dumps(corpo or {}).encode() if metodo == "POST" else None
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
        self.ana = self.entrar_no_sistema("ana@udesc.br")
        self.bento = self.entrar_no_sistema("bento@udesc.br")

    def test_sem_entrar_no_sistema_nao_bate_ponto(self):
        self.assertEqual(self.chamar("/api/ponto")[0], 401)

    def test_o_ciclo_completo_pela_rota(self):
        self.assertEqual(self.chamar("/api/ponto/entrar", self.bento, "POST",
                                     {"atividade": "leitura"})[0], 200)
        _, dados = self.chamar("/api/ponto", self.bento)
        self.assertEqual(dados["resumo"]["aberto"]["atividade"], "leitura")
        self.assertTrue(dados["sou_eu"])
        self.assertEqual(self.chamar("/api/ponto/sair", self.bento, "POST")[0], 200)

    def test_ninguem_le_o_ponto_de_outra_pessoa(self):
        # a rotina de cada um é dela; ver a dos outros é coisa de coordenação
        _, da_ana = self.chamar("/api/ponto", self.ana)
        _, do_bento = self.chamar("/api/ponto", self.bento)
        self.assertNotEqual(da_ana["de"], do_bento["de"])
        alheio = da_ana["de"]
        self.assertEqual(self.chamar(f"/api/ponto?de={alheio}", self.bento)[0], 403)
        # o próprio, pelo id, continua valendo
        self.assertEqual(self.chamar(f"/api/ponto?de={do_bento['de']}", self.bento)[0], 200)

    def test_a_coordenacao_ve_a_equipe(self):
        status, dados = self.chamar("/api/ponto/equipe", self.ana)
        self.assertEqual(status, 200)
        for chave in ("pessoas", "agora", "serie", "resumo", "producao"):
            self.assertIn(chave, dados)

    def test_quem_so_e_integrante_nao_ve_a_equipe(self):
        self.assertEqual(self.chamar("/api/ponto/equipe", self.bento)[0], 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
