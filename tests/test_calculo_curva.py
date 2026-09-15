#!/usr/bin/env python3
"""Testes do calculo sobre as curvas do laboratorio.

    python3 -m unittest tests.test_calculo_curva -v

Quatro operacoes sobre a mesma curva: nivel, derivada, aceleracao e
acumulado. O que estes testes guardam nao e a aritmetica -- e QUAL
operacao se aplica a QUAL curva, que e a parte que faz um painel mentir
bonito quando esta errada.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import curva, estatistica, ingest_excel, metas  # noqa: E402
from lape.db import Database  # noqa: E402


class TestASegundaDerivada(unittest.TestCase):
    """Aceleracao: a derivada esta mudando?

    E outra pergunta, e e a que decide prorrogar ou encerrar. Uma serie
    pode estar subindo (derivada positiva) e desacelerando (aceleracao
    negativa) ao mesmo tempo: continua melhorando, mas cada vez menos.
    Olhando so a derivada isso passa como "vai bem" ate o dia em que para.
    """

    # taxas 1,0 -> 0,6 -> 0,3 por dia: sobe sempre, e cada vez menos
    T = [0, 10, 20, 30]
    V = [0, 10, 16, 19]

    def test_sobe_e_desacelera_ao_mesmo_tempo(self):
        taxa = estatistica.taxa_de_variacao(self.T, self.V, por=1)
        ace = estatistica.aceleracao(self.T, self.V, por=1)
        self.assertGreater(taxa["geral"], 0, "a serie sobe")
        self.assertLess(ace["agora"], 0, "e esta perdendo forca")

    def test_a_conta_bate_com_a_diferenca_das_taxas(self):
        """Conferida contra a formula, e nao contra a memoria.

        As taxas 0,6 e 0,3 pertencem aos trechos 10-20 e 20-30, cujos
        MEIOS sao 15 e 25. A aceleracao entre elas e (0,3 - 0,6)/(25-15).
        """
        ace = estatistica.aceleracao(self.T, self.V, por=1)
        self.assertAlmostEqual(ace["agora"], (0.3 - 0.6) / (25 - 15), places=4)

    def test_a_taxa_e_ancorada_no_MEIO_do_trecho(self):
        """Ancorar na ponta desloca a segunda derivada meio intervalo.

        Numa serie anual isso e seis meses de erro na resposta a "quando
        comecou a desacelerar" -- e a resposta certa e o que decide se a
        intervencao continua.
        """
        ace = estatistica.aceleracao(self.T, self.V, por=1)
        primeiro = ace["trechos"][0]
        self.assertEqual(primeiro["de"], 5.0)    # meio de 0-10
        self.assertEqual(primeiro["ate"], 15.0)  # meio de 10-20

    def test_serie_reta_nao_acelera(self):
        ace = estatistica.aceleracao([0, 10, 20, 30], [0, 5, 10, 15], por=1)
        self.assertEqual(ace["agora"], 0.0)
        self.assertEqual(ace["geral"], 0.0)

    def test_dois_momentos_nao_sustentam_aceleracao(self):
        """Duas taxas para comparar exigem tres momentos.

        Devolver zero aqui seria pior do que devolver aviso: zero num
        ponteiro se le "ritmo constante", que e uma afirmacao -- e nao ha
        dado para afirmar nada.
        """
        ace = estatistica.aceleracao([0, 10], [1, 2])
        self.assertIsNone(ace["agora"])
        self.assertIn("três momentos", ace["aviso"])

    def test_agora_e_geral_podem_discordar_e_a_discordancia_e_informacao(self):
        """Desacelerou por anos e voltou a ganhar forca."""
        # taxas 5, 1, 1, 4 -> geral cai (5 para 4), mas o ultimo passo sobe
        ace = estatistica.aceleracao([0, 1, 2, 3, 4], [0, 5, 6, 7, 11], por=1)
        self.assertGreater(ace["agora"], 0)
        self.assertLess(ace["geral"], 0)


class BaseDoBanco(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Database(Path(cls.tmp.name) / "c.sqlite")
        cls.db.migrate()
        ingest_excel.ingest_articles(cls.db, [
            {"title": "a", "status": "Publicado", "published_on": "2022-03-01"},
            {"title": "b", "status": "Publicado", "published_on": "2023-03-01"},
            {"title": "c", "status": "Publicado", "published_on": "2023-06-01"},
            {"title": "d", "status": "Publicado", "published_on": "2024-01-01"},
            {"title": "e", "status": "Em produção"},
        ])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class TestFluxoEEstoque(BaseDoBanco):
    """A integral so e oferecida onde ela significa alguma coisa.

    Numa serie de ESTOQUE -- o acervo tem 141 artigos hoje -- a area sob a
    curva e exposicao: quanto de producao o laboratorio manteve de pe ao
    longo do tempo.

    Numa serie de FLUXO -- 12 publicacoes em 2026 -- a area E o proprio
    acumulado, e o acumulado se sabe pela SOMA. Apresentar o trapezio como
    total publicado troca um numero exato por uma aproximacao e chama a
    aproximacao de integral: entre 9 e 12 o trapezio devolve 10,5 onde a
    resposta e 12.
    """

    def test_o_estoque_ganha_integral(self):
        d = curva.analisar(self.db, "acervo", janela=6)
        self.assertEqual(d["serie"]["kind"], "estoque")
        self.assertIsNotNone(d["integral"])
        self.assertIsNone(d["soma"])
        self.assertIn("-ano", d["integral"]["unidade"])

    def test_o_fluxo_ganha_soma_e_nao_integral(self):
        d = curva.analisar(self.db, "publicacoes", janela=6)
        self.assertEqual(d["serie"]["kind"], "fluxo")
        self.assertIsNone(d["integral"])
        self.assertIsNotNone(d["soma"])

    def test_a_soma_do_fluxo_e_a_soma_exata_da_serie_que_ela_relata(self):
        d = curva.analisar(self.db, "publicacoes", janela=6)
        self.assertEqual(d["soma"]["total"], sum(p["v"] for p in d["pontos"]))
        self.assertEqual(d["soma"]["total"], 4.0)

    def test_o_trapezio_e_a_soma_divergem_e_por_isso_um_e_escolhido(self):
        """Onde os dois coincidem, escolher nao muda nada -- e engana.

        Este teste usa a serie em que eles DIVERGEM, para provar que o
        modulo devolve a soma e nao o trapezio: com 9 e 12 num ano de
        intervalo, o trapezio da 10,5 e a resposta e 21. Nao ha nada de
        errado com o trapezio; ele so nao responde esta pergunta.
        """
        trapezio = estatistica.area_sob_a_curva([2025, 2026], [9, 12])
        self.assertEqual(trapezio["bruta"], 10.5)
        self.assertNotEqual(trapezio["bruta"], 9 + 12)

    def test_o_acervo_nunca_desce(self):
        d = curva.analisar(self.db, "acervo", janela=6)
        valores = [p["v"] for p in d["pontos"]]
        self.assertEqual(valores, sorted(valores))

    def test_ano_sem_publicacao_vale_zero_e_nao_buraco(self):
        """Ano vazio e informacao: e uma queda a explicar.

        Pular o ano faria a derivada passar reto por cima dela, e a curva
        sairia mais lisa do que o trabalho foi.
        """
        d = curva.analisar(self.db, "publicacoes", janela=6)
        anos = [p["t"] for p in d["pontos"]]
        self.assertEqual(anos, sorted(anos))
        self.assertEqual(len(anos), 6)
        self.assertEqual(len(set(anos)), 6, "nenhum ano repetido nem faltando")
        self.assertIn(0.0, [p["v"] for p in d["pontos"]])

    def test_o_que_foi_publicado_ANTES_da_janela_entra_no_nivel(self):
        """Senao a curva comeca em zero num laboratorio de vinte anos.

        E a derivada do primeiro ano sai gigante -- um artefato do recorte,
        lido como um ano historico.
        """
        curta = curva.series(self.db, janela=2)
        acervo = next(s for s in curta if s["code"] == "acervo")
        self.assertGreater(acervo["base_fora_da_janela"], 0)
        self.assertGreaterEqual(acervo["valores"][0], acervo["base_fora_da_janela"])


class TestOLimiarVemDaMetaDeclarada(BaseDoBanco):
    """Linha de corte inventada e pior do que nenhuma.

    Quem olha supoe que o laboratorio a declarou, e passa a se comparar
    com ela.
    """

    def test_sem_meta_declarada_nao_ha_limiar(self):
        d = curva.analisar(self.db, "publicacoes", janela=6)
        self.assertIsNone(d["limiar"])

    def test_com_meta_declarada_o_limiar_aparece_e_diz_de_onde_veio(self):
        from datetime import date

        ano = date.today().year
        metas.declarar(self.db, ano, "publicacoes", 3, por="teste")
        try:
            d = curva.analisar(self.db, "publicacoes", janela=6)
            self.assertIsNotNone(d["limiar"])
            self.assertEqual(d["limiar"]["valor"], 3.0)
            self.assertIn("meta declarada", d["limiar"]["de_onde"])
            # numa meta de publicacao, MAIS e melhor -- e errar isto
            # inverteria a conclusao sem mudar um numero
            self.assertFalse(d["limiar"]["menor_e_melhor"])
        finally:
            metas.declarar(self.db, ano, "publicacoes", None, por="teste")

    def test_o_acervo_nao_recebe_a_meta_de_publicacoes(self):
        """Sao unidades diferentes: 3 publicacoes/ano nao e 3 de acervo."""
        from datetime import date

        ano = date.today().year
        metas.declarar(self.db, ano, "publicacoes", 3, por="teste")
        try:
            self.assertIsNone(curva.analisar(self.db, "acervo", janela=6)["limiar"])
        finally:
            metas.declarar(self.db, ano, "publicacoes", None, por="teste")


class TestOQueATelaRecebe(BaseDoBanco):

    def test_serie_desconhecida_cai_na_primeira_e_nao_estoura(self):
        d = curva.analisar(self.db, "nao-existe", janela=6)
        self.assertEqual(d["serie"]["code"], "acervo")

    def test_a_tela_recebe_a_lista_para_o_seletor(self):
        d = curva.analisar(self.db, "acervo", janela=6)
        codes = [x["code"] for x in d["disponiveis"]]
        self.assertIn("acervo", codes)
        self.assertIn("publicacoes", codes)
        self.assertIn("citacoes", codes)
        for x in d["disponiveis"]:
            with self.subTest(serie=x["code"]):
                self.assertIn(x["kind"], ("estoque", "fluxo"))

    def test_cada_curva_traz_a_unidade_das_TRES_leituras(self):
        """Derivar muda a unidade -- e a tela reaproveitava a mesma.

        O acelerometro do painel era rotulado com `unidade_taxa`, a
        unidade da VELOCIDADE: o ponteiro mostrava aceleracao e o rotulo
        dizia "artigos/ano". Ponteiro certo com rotulo errado e o pior
        dos dois, porque quem le confere o numero no rotulo.
        """
        d = curva.analisar(self.db, "acervo", janela=6)
        for x in curva.series(self.db, janela=6):
            with self.subTest(serie=x["code"]):
                self.assertTrue(x["unidade"])
                self.assertTrue(x["unidade_taxa"])
                self.assertTrue(x["unidade_aceleracao"])
                # as tres sao diferentes entre si: sao tres grandezas
                self.assertEqual(len({x["unidade"], x["unidade_taxa"],
                                      x["unidade_aceleracao"]}), 3)
        self.assertEqual(d["serie"]["unidade_aceleracao"], "artigos/ano²")

    def test_num_fluxo_a_unidade_ja_comeca_um_degrau_adiante(self):
        """"Publicacoes por ano" e ela mesma um ritmo.

        Logo a derivada dela e uma aceleracao (ano^2) e a segunda
        derivada vai a ano^3. Tratar as duas curvas com a mesma regra
        faria o painel rotular a derivada do fluxo como se fosse
        velocidade de um nivel.
        """
        por_code = {x["code"]: x for x in curva.series(self.db, janela=6)}
        self.assertEqual(por_code["acervo"]["unidade_taxa"], "artigos/ano")
        self.assertEqual(por_code["publicacoes"]["unidade_taxa"],
                         "publicações/ano²")
        self.assertEqual(por_code["publicacoes"]["unidade_aceleracao"],
                         "publicações/ano³")

    def test_banco_sem_artigo_nenhum_nao_derruba_o_calculo(self):
        vazio = Database(Path(self.tmp.name) / "vazio.sqlite")
        vazio.migrate()
        d = curva.analisar(vazio, "acervo", janela=6)
        self.assertEqual([p["v"] for p in d["pontos"]], [0.0] * 6)
        # serie reta em zero: derivada zero, e nenhuma afirmacao alem disso
        self.assertEqual(d["derivada"]["geral"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
