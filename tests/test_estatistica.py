#!/usr/bin/env python3
"""Desvio padrao, erro padrao, intervalo de confianca e o limite central.

    python3 -m unittest tests.test_estatistica -v

Tres numeros que a area confunde o tempo todo, e que este modulo tem de
manter separados:

  DP descreve as PESSOAS, e nao encolhe com mais gente.
  EP descreve a MEDIA, e encolhe com a raiz de n.
  IC e a faixa construida a partir do EP.

E o teorema do limite central e o que autoriza a conta -- quando ele vale.
A tentacao aqui e enorme: a formula sai, o numero aparece com duas casas e
ninguem pergunta se a amostra dava para isso. Metade destes testes existe
para o caso em que nao dava.

Sem scipy na casa, o t de Student e implementado aqui. Um t errado nao da
erro: da um intervalo com o tamanho errado, e ninguem confere um numero
que ja veio impresso.
"""
from __future__ import annotations

import statistics
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import coleta  # noqa: E402

# Tabela publicada de t bicaudal a 95%, que e o que esta em qualquer
# apendice de livro de estatistica.
TABELA_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 10: 2.228,
              15: 2.131, 20: 2.086, 30: 2.042, 60: 2.000, 120: 1.980}


class TestOTDeStudent(unittest.TestCase):

    def test_bate_com_a_tabela_publicada(self):
        for gl, esperado in TABELA_T95.items():
            with self.subTest(gl=gl):
                self.assertAlmostEqual(coleta.t_critico(gl, 0.95), esperado, places=2)

    def test_converge_para_a_normal(self):
        """Com muitos graus de liberdade o t vira o 1,96 de sempre."""
        normal = statistics.NormalDist().inv_cdf(0.975)
        self.assertAlmostEqual(coleta.t_critico(100000, 0.95), normal, places=3)

    def test_e_maior_que_a_normal_em_amostra_pequena(self):
        """É essa folga que paga a incerteza de um desvio mal estimado."""
        normal = statistics.NormalDist().inv_cdf(0.975)
        for gl in (1, 2, 5, 10, 30):
            with self.subTest(gl=gl):
                self.assertGreater(coleta.t_critico(gl, 0.95), normal)

    def test_encolhe_conforme_os_graus_crescem(self):
        valores = [coleta.t_critico(gl, 0.95) for gl in (1, 5, 10, 30, 100)]
        self.assertEqual(valores, sorted(valores, reverse=True))

    def test_99_por_cento_e_mais_largo_que_95(self):
        self.assertGreater(coleta.t_critico(10, 0.99), coleta.t_critico(10, 0.95))
        self.assertAlmostEqual(coleta.t_critico(10, 0.99), 3.169, places=2)

    def test_a_distribuicao_e_simetrica(self):
        for gl in (1, 5, 30):
            with self.subTest(gl=gl):
                self.assertAlmostEqual(coleta.t_cdf(0, gl), 0.5, places=9)
                self.assertAlmostEqual(coleta.t_cdf(-2.0, gl),
                                       1 - coleta.t_cdf(2.0, gl), places=9)


class TestOsTresNumeros(unittest.TestCase):

    def test_o_erro_padrao_e_o_desvio_dividido_pela_raiz(self):
        valores = [7.5, 8, 6, 9, 7, 8, 7, 9, 6, 8]
        r = coleta._resumo(valores)
        self.assertAlmostEqual(r["erro_padrao"], r["dp"] / len(valores) ** 0.5, places=2)

    def test_o_desvio_nao_encolhe_com_mais_gente_e_o_erro_sim(self):
        """A diferença entre descrever pessoas e descrever a média."""
        poucos = [6, 7, 8, 9]
        muitos = poucos * 9              # mesma distribuição, 9x mais gente
        a, b = coleta._resumo(poucos), coleta._resumo(muitos)
        self.assertAlmostEqual(a["dp"], b["dp"], delta=0.2)
        self.assertLess(b["erro_padrao"], a["erro_padrao"] / 2.5)

    def test_o_intervalo_encolhe_com_mais_gente(self):
        poucos = coleta._resumo([6, 7, 8, 9])
        muitos = coleta._resumo([6, 7, 8, 9] * 9)
        largura = lambda r: r["ic"]["ate"] - r["ic"]["de"]  # noqa: E731
        self.assertLess(largura(muitos), largura(poucos) / 2.5)

    def test_o_intervalo_e_centrado_na_media(self):
        r = coleta._resumo([6, 7, 8, 9, 10, 5, 7, 8])
        centro = (r["ic"]["de"] + r["ic"]["ate"]) / 2
        self.assertAlmostEqual(centro, r["media"], places=2)

    def test_uma_medida_so_nao_tem_intervalo(self):
        """Com uma pessoa não há dispersão: um intervalo ali é inventado."""
        r = coleta._resumo([7])
        self.assertEqual(r["n"], 1)
        self.assertIsNone(r["dp"])
        self.assertIsNone(r["erro_padrao"])
        self.assertIsNone(r["ic"])

    def test_sem_medida_nenhuma_nada_e_zero(self):
        r = coleta._resumo([])
        self.assertEqual(r["n"], 0)
        for campo in ("media", "dp", "erro_padrao", "ic"):
            with self.subTest(campo=campo):
                self.assertIsNone(r[campo])

    def test_o_intervalo_guarda_o_t_que_usou(self):
        """Sem o t, o intervalo não se confere à mão."""
        r = coleta._resumo([6, 7, 8, 9, 10])
        self.assertAlmostEqual(r["ic"]["t"], coleta.t_critico(4, 0.95), places=3)
        self.assertEqual(r["gl"], 4)


class TestAReamostragem(unittest.TestCase):

    def test_o_desvio_das_medias_reamostradas_e_o_erro_padrao(self):
        """É o teorema do limite central visto de perto, e não suposto."""
        valores = [7, 8, 6, 9, 7, 8, 7, 9, 6, 8, 7, 8, 9, 6, 7, 8, 8, 7, 9, 6]
        r = coleta._resumo(valores)
        b = coleta.distribuicao_das_medias(valores, reamostras=4000)
        self.assertAlmostEqual(b["dp_das_medias"], r["erro_padrao"], delta=0.06)

    def test_a_media_das_medias_e_a_media(self):
        valores = [7, 8, 6, 9, 7, 8, 7, 9, 6, 8] * 2
        b = coleta.distribuicao_das_medias(valores, reamostras=4000)
        self.assertAlmostEqual(b["media_das_medias"],
                               coleta._resumo(valores)["media"], delta=0.06)

    def test_o_resultado_nao_muda_a_cada_chamada(self):
        """Intervalo que muda ao recarregar a tela não é intervalo: é sorteio."""
        valores = [7, 8, 6, 9, 7, 8, 7, 9, 6, 8]
        a = coleta.distribuicao_das_medias(valores)
        b = coleta.distribuicao_das_medias(valores)
        self.assertEqual(a["ic"], b["ic"])
        self.assertEqual(a["histograma"], b["histograma"])

    def test_o_histograma_conta_todas_as_reamostras(self):
        b = coleta.distribuicao_das_medias([6, 7, 8, 9, 10], reamostras=1000)
        self.assertEqual(sum(c["n"] for c in b["histograma"]), 1000)

    def test_gente_de_menos_nao_reamostra(self):
        self.assertEqual(coleta.distribuicao_das_medias([7])["medias"], [])
        self.assertIsNone(coleta.distribuicao_das_medias([7])["ic"])

    def test_valores_todos_iguais_nao_quebram(self):
        b = coleta.distribuicao_das_medias([5, 5, 5, 5, 5])
        self.assertEqual(b["dp_das_medias"], 0)
        self.assertEqual(b["ic"]["de"], 5)


class TestOVereditoDoTeorema(unittest.TestCase):
    """A pergunta que o cartão responde: dá para confiar na conta por t?"""

    def veredito(self, valores):
        return coleta.comparar_intervalos(
            coleta._resumo(valores), coleta.distribuicao_das_medias(valores))

    def test_amostra_pequena_nao_endossa_nenhum_dos_dois(self):
        """Com n=4 o t alarga demais E a reamostragem estreita demais.

        Endossar a reamostragem aqui -- que foi o que a primeira versão
        desta tela fazia -- é recomendar justamente o que falha pior, e de
        um jeito que não aparece: o intervalo sai estreito e bonito, e
        cobre menos do que promete.
        """
        v = self.veredito([5, 9, 6, 9])
        self.assertEqual(v["veredito"], "poucos")
        self.assertIn("nenhum dos dois", v["texto"])

    def test_amostra_simetrica_e_suficiente_concorda(self):
        v = self.veredito([7, 8, 6, 9, 7, 8, 7, 9, 6, 8, 7, 8])
        self.assertEqual(v["veredito"], "concordam")

    def test_amostra_muito_torta_discorda(self):
        v = self.veredito([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 40])
        self.assertEqual(v["veredito"], "discordam")
        self.assertIn("não vale", v["texto"])

    def test_a_comparacao_e_de_largura_e_nao_so_das_pontas(self):
        """Dois intervalos podem ter extremos parecidos e larguras muito
        diferentes -- e a largura é o que o intervalo afirma. Comparando só
        as pontas, um par com o dobro da largura passava por concordante."""
        estreito = {"ic": {"de": 5.0, "ate": 8.5}}
        largo = {"n": 20, "ic": {"de": 3.5, "ate": 10.0}}
        v = coleta.comparar_intervalos(largo, estreito)
        self.assertEqual(v["veredito"], "discordam")

    def test_o_piso_e_declarado_e_nao_escondido_no_codigo(self):
        self.assertGreaterEqual(coleta.N_MINIMO_PARA_INTERVALO, 10)
        v = self.veredito([6, 7] * (coleta.N_MINIMO_PARA_INTERVALO // 2 - 1))
        self.assertEqual(v["veredito"], "poucos")

    def test_sem_intervalo_nenhum_o_veredito_e_poucos(self):
        v = coleta.comparar_intervalos(coleta._resumo([7]), {"ic": None})
        self.assertEqual(v["veredito"], "poucos")


class TestOTamanhoDeEfeitoComIntervalo(unittest.TestCase):

    def test_hedges_corrige_o_cohen_para_baixo(self):
        """Cohen exagera em amostra pequena; a correção é de 1981."""
        e = coleta.efeito([8, 7, 9, 8, 7, 8], [4, 3, 5, 4, 3, 4])
        self.assertLess(abs(e["g"]), abs(e["d"]))
        gl = e["antes"]["n"] + e["depois"]["n"] - 2
        esperado = 1 - 3 / (4 * gl - 1)
        # `g` e `d` saem arredondados em tres casas; a razao entre os dois
        # herda esse arredondamento, e exigir a quarta casa aqui seria
        # testar o arredondamento e nao a correcao.
        self.assertAlmostEqual(e["g"] / e["d"], esperado, delta=0.001)

    def test_a_correcao_some_com_amostra_grande(self):
        grande = [8] * 100 + [7] * 100
        outro = [4] * 100 + [5] * 100
        e = coleta.efeito(grande, outro)
        self.assertAlmostEqual(e["g"] / e["d"], 1.0, places=2)

    def test_o_efeito_vem_com_intervalo(self):
        e = coleta.efeito([8, 7, 9, 8, 7, 8], [4, 3, 5, 4, 3, 4])
        self.assertIn("ic_d", e)
        self.assertLess(e["ic_d"]["de"], e["d"])
        self.assertGreater(e["ic_d"]["ate"], e["d"])

    def test_o_efeito_fraco_atravessa_o_zero(self):
        """"Pode não ter havido efeito nenhum" é a leitura que o d sozinho,
        com duas casas, não deixa ninguém fazer."""
        e = coleta.efeito([5, 6, 4, 5, 6, 4], [5, 5, 6, 4, 6, 5])
        self.assertTrue(e["cruza_zero"])

    def test_o_efeito_forte_nao_atravessa(self):
        e = coleta.efeito([8, 7, 9, 8, 7, 8, 9, 8], [3, 2, 4, 3, 2, 3, 4, 3])
        self.assertFalse(e["cruza_zero"])

    def test_o_intervalo_do_efeito_encolhe_com_mais_gente(self):
        pouco = coleta.efeito([8, 7, 9, 8], [5, 4, 6, 5])
        muito = coleta.efeito([8, 7, 9, 8] * 8, [5, 4, 6, 5] * 8)
        largura = lambda e: e["ic_d"]["ate"] - e["ic_d"]["de"]  # noqa: E731
        self.assertLess(largura(muito), largura(pouco) / 2)


if __name__ == "__main__":
    unittest.main()
