#!/usr/bin/env python3
"""As sete telas da bancada e as rotas que as alimentam.

    python3 -m unittest tests.test_bancada_telas -v

A bancada guarda escala de dor e sintoma depressivo de gente. O resto do
painel e producao cientifica, que e publica por natureza; isto nao e. Daí
os testes se dividirem em duas perguntas:

  - Quem alcanca? Todas as rotas sao de coordenacao, INCLUSIVE as de
    leitura, e nada da bancada entra no payload do painel -- que e o que
    viaja para docs/, para o mural e para quem abrir o link com
    LAPE_PUBLIC_DASHBOARD ligado.
  - A tela conta a verdade? Um painel de coleta que soma 38 de 42 e
    esconde quatro celulas nao e um painel: e uma conta pela metade.
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import coleta, metrics  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
DASHBOARD = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
TEMA = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
API = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")

AS_SETE = ["coleta", "monitoramento", "medidas", "ano_bancada",
           "relatorios", "exportar", "bancada_admin"]


class TestQuemAlcanca(unittest.TestCase):

    def test_toda_rota_da_bancada_exige_coordenacao(self):
        """Inclusive as de leitura: ler a dor de alguém não é ler um artigo."""
        rotas = re.findall(
            r'\("(GET|POST)",\s*r"\^/api/bancada[^"]*",\s*\w+,\s*("?\w+"?)\)', API)
        self.assertGreaterEqual(len(rotas), 5)
        for metodo, perfil in rotas:
            with self.subTest(rota=metodo):
                self.assertEqual(perfil, '"coordenacao"')

    def test_cada_funcao_confere_por_conta_propria(self):
        """A tabela de rotas pode ser reordenada; a função não."""
        for nome in ("route_bancada", "route_bancada_analise", "route_bancada_ano",
                     "route_bancada_exportar", "route_bancada_gravar"):
            with self.subTest(funcao=nome):
                corpo = API[API.index("def %s(" % nome):]
                corpo = corpo[:corpo.index("\ndef ")]
                self.assertIn('auth.require(ctx.user, "coordenacao")', corpo)

    def test_nada_da_bancada_entra_no_payload_do_painel(self):
        """O payload vai inteiro para docs/, para o mural e para o link público."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Database(Path(tmp.name) / "p.sqlite")
        self.addCleanup(db.close)
        db.migrate()
        prot = coleta.declarar_protocolo(db, "x", "Estudo X")
        inst = coleta.declarar_instrumento(db, "eva", "Dor", minimo=0, maximo=10)
        p = coleta.inscrever(db, "P01", prot["id"], grupo="intervencao")
        coleta.registrar(db, p["id"], inst["id"], 7)

        # As marcas sao o DADO e as CHAVES que so a bancada produz. Procurar
        # a palavra "coleta" daria falso positivo em "citacoes coletadas",
        # que e um rotulo da aba de qualidade e nao tem nada com isto.
        marcas = ("'P01'", "participante_id", "instrumento_id", "protocolo_id",
                  "coletado_em", "subescala", "ano_nascimento", "motivo_saida")
        for kwargs in ({}, {"com_dados_da_coordenacao": True}):
            with self.subTest(payload=kwargs or "padrão"):
                bruto = repr(metrics.build_payload(db, **kwargs))
                for marca in marcas:
                    self.assertNotIn(marca, bruto, "%r vazou no payload" % marca)
                # e as chaves de topo tambem nao existem
                for chave in ("participantes", "coletas", "instrumentos",
                              "protocolos", "bancada"):
                    self.assertNotIn("'%s'" % chave, bruto)

    def test_as_telas_leem_do_servidor_e_nao_do_payload(self):
        """É o que faz a bancada não existir dentro do arquivo exportado."""
        bloco = DASHBOARD[DASHBOARD.index("const BANCADA = {"):
                          DASHBOARD.index("/* ============================"
                                          "======================================== */\n"
                                          "/* navegação")]
        self.assertIn("/api/bancada", bloco)
        self.assertNotIn("D.participantes", bloco)
        self.assertNotIn("D.coletas", bloco)

    def test_sem_servidor_a_tela_diz_por_que_esta_vazia(self):
        bloco = DASHBOARD[DASHBOARD.index("function bancadaTela("):]
        bloco = bloco[:bloco.index("\nfunction seletorDeProtocolo")]
        self.assertIn("if (!LIVE)", bloco)
        self.assertIn("não viaja em arquivo", bloco)


class TestAsSeteTelas(unittest.TestCase):

    def test_as_sete_existem(self):
        for tela in AS_SETE:
            with self.subTest(tela=tela):
                self.assertIn('view("%s"' % tela, DASHBOARD)

    def test_as_sete_estao_na_secao_da_bancada(self):
        secoes = DASHBOARD[DASHBOARD.index("const SECTIONS = ["):
                           DASHBOARD.index("const VIEW_ICON = {")]
        bancada = re.search(r'id: "bancada".*?views: \[(.*?)\]', secoes, re.S)
        self.assertIsNotNone(bancada)
        declaradas = set(re.findall(r'"(\w+)"', bancada.group(1)))
        self.assertEqual(declaradas, set(AS_SETE))

    def test_cada_uma_tem_icone(self):
        mapa = DASHBOARD[DASHBOARD.index("const VIEW_ICON = {"):
                         DASHBOARD.index("/* A bancada inteira também")]
        for tela in AS_SETE:
            with self.subTest(tela=tela):
                self.assertRegex(mapa, tela + r':\s*"\w+"')

    def test_nenhuma_responde_aos_filtros_do_painel(self):
        """Ano, linha de pesquisa e integrante não recortam participante."""
        lista = re.search(r"const SEM_FILTROS = \[(.*?)\];", DASHBOARD, re.S)
        declaradas = set(re.findall(r'"(\w+)"', lista.group(1)))
        for tela in AS_SETE:
            with self.subTest(tela=tela):
                self.assertIn(tela, declaradas)

    def test_cada_uma_aponta_para_vizinhas(self):
        for tela in AS_SETE:
            with self.subTest(tela=tela):
                self.assertRegex(DASHBOARD, r"\n  " + tela + r":\s*\[")


class TestAContaQueFecha(unittest.TestCase):
    """38 de 42 não é um painel: é uma conta pela metade."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "m.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.prot = coleta.declarar_protocolo(self.db, "p", "Protocolo")
        self.m0 = coleta.declarar_momento(self.db, self.prot["id"], "a", "Base", 1, 0, 7)
        self.m1 = coleta.declarar_momento(self.db, self.prot["id"], "b", "Fim", 2, 60, 7)
        self.inst = coleta.declarar_instrumento(self.db, "eva", "Dor", minimo=0, maximo=10)

    def test_os_quatro_estados_somam_o_total(self):
        antigo = (date.today() - timedelta(days=200)).isoformat()
        a = coleta.inscrever(self.db, "P1", self.prot["id"], entrou_em=antigo)
        coleta.inscrever(self.db, "P2", self.prot["id"], entrou_em=antigo)
        saiu = coleta.inscrever(self.db, "P3", self.prot["id"], entrou_em=antigo)
        coleta.encerrar(self.db, saiu["id"], "desistiu", "mudou de cidade")
        coleta.registrar(self.db, a["id"], self.inst["id"], 7, self.m0["id"])

        m = coleta.matriz(self.db, self.prot["id"])
        soma = m["feitas"] + m["faltam"] + m["atrasadas"] + m["fora"]
        self.assertEqual(soma, m["total_celulas"],
                         "os estados não fecham: %r" % m)

    def test_a_faixa_do_kpi_mostra_os_quatro(self):
        painel = DASHBOARD[DASHBOARD.index('view("coleta"'):
                           DASHBOARD.index("const ESTADO_DA_CELULA")]
        for rotulo in ("feitas", "a fazer", "atrasadas", "fora do estudo"):
            with self.subTest(segmento=rotulo):
                self.assertIn('rotulo: "%s"' % rotulo, painel)


class TestAMatrizNaTela(unittest.TestCase):

    def test_a_celula_carrega_a_palavra_e_nao_so_a_cor(self):
        """A matriz é impressa para levar à sala de coleta, em preto e branco."""
        mapa = re.search(r"const ESTADO_DA_CELULA = \{(.*?)\};", DASHBOARD, re.S)
        self.assertIsNotNone(mapa)
        estados = dict(re.findall(r'(\w+): "([^"]+)"', mapa.group(1)))
        self.assertEqual(set(estados), {"feita", "falta", "atrasada", "fora"})
        for palavra in estados.values():
            self.assertTrue(palavra.strip())

    def test_cada_estado_tem_tom_proprio_na_folha(self):
        for estado in ("feita", "falta", "atrasada", "fora"):
            with self.subTest(estado=estado):
                self.assertRegex(TEMA, r"\.cel-" + estado + r"\s*\{[^}]*--tomcel")

    def test_a_legenda_existe(self):
        self.assertIn("legenda-cel", DASHBOARD)
        self.assertIn(".legenda-cel", TEMA)


class TestOPrimeiroAcesso(unittest.TestCase):
    """A primeira tela aberta não tinha protocolo escolhido, e desenhava
    "sem momentos declarados" num protocolo com três."""

    def test_o_protocolo_e_decidido_antes_da_busca(self):
        bloco = DASHBOARD[DASHBOARD.index("function bancadaTela("):]
        bloco = bloco[:bloco.index("\nfunction seletorDeProtocolo")]
        self.assertIn("function buscar(segundaTentativa)", bloco)
        self.assertIn("return buscar(true);", bloco)

    def test_a_segunda_tentativa_nao_se_repete(self):
        """Sem a guarda, um catálogo sem protocolo daria laço infinito."""
        bloco = DASHBOARD[DASHBOARD.index("function bancadaTela("):]
        bloco = bloco[:bloco.index("\nfunction seletorDeProtocolo")]
        self.assertIn("&& !segundaTentativa", bloco)


class TestOQueORelatorioNaoPromete(unittest.TestCase):
    """Não inventar um agendador que não foi escrito."""

    def test_a_tela_diz_quem_agenda_de_verdade(self):
        bloco = DASHBOARD[DASHBOARD.index('view("relatorios"'):
                          DASHBOARD.index('view("exportar"')]
        self.assertIn("não tem agendador próprio", bloco)
        self.assertIn("Agendador de Tarefas", bloco)
        self.assertIn("lape_agent.py instantaneo", bloco)


if __name__ == "__main__":
    unittest.main()
