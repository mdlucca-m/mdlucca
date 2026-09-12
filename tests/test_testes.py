#!/usr/bin/env python3
"""Testes de hipotese: as contas, e a ESCOLHA das contas.

    python3 -m unittest tests.test_testes -v

O modo de errar aqui nao e a conta -- e escolher a conta errada. Roda-se
teste t por habito, sem conferir se os dados permitiam, e o resultado sai
com quatro casas decimais e aparencia de verdade. Depois vai para o
artigo.

Sem scipy na casa, as tres distribuicoes sao implementadas aqui. Uma
distribuicao errada nao da erro: da um valor-p com o tamanho errado, e
ninguem confere um numero que ja veio impresso. Por isso a primeira classe
confere qui-quadrado, F e t contra a tabela publicada, e as demais
conferem as estatisticas contra a formula calculada a parte.
"""
from __future__ import annotations

import math
import statistics
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import estatistica as E  # noqa: E402

# Valores criticos a 5%, de apendice de livro.
QUI2_95 = {1: 3.841, 2: 5.991, 5: 11.070, 10: 18.307, 20: 31.410}
F_95 = {(1, 10): 4.965, (3, 20): 3.098, (5, 10): 3.326, (2, 30): 3.316, (10, 10): 2.978}


def _inverter(cdf, alvo=0.95, teto=200.0):
    baixo, alto = 0.0, teto
    for _ in range(200):
        meio = (baixo + alto) / 2
        if cdf(meio) < alvo:
            baixo = meio
        else:
            alto = meio
    return (baixo + alto) / 2


class TestAsDistribuicoes(unittest.TestCase):
    """Distribuição errada não dá erro: dá um valor-p do tamanho errado."""

    def test_qui_quadrado_bate_com_a_tabela(self):
        for gl, esperado in QUI2_95.items():
            with self.subTest(gl=gl):
                achado = _inverter(lambda x, g=gl: E.qui2_cdf(x, g))
                self.assertAlmostEqual(achado, esperado, places=2)

    def test_f_bate_com_a_tabela(self):
        for (gl1, gl2), esperado in F_95.items():
            with self.subTest(gl=(gl1, gl2)):
                achado = _inverter(lambda x, a=gl1, b=gl2: E.f_cdf(x, a, b), teto=100.0)
                self.assertAlmostEqual(achado, esperado, places=2)

    def test_t_bate_com_a_tabela(self):
        for gl, esperado in {1: 12.706, 5: 2.571, 10: 2.228, 30: 2.042}.items():
            with self.subTest(gl=gl):
                self.assertAlmostEqual(E.t_critico(gl, 0.95), esperado, places=2)

    def test_as_cdf_sao_monotonas_e_vao_de_zero_a_um(self):
        for nome, cdf in (("qui2", lambda x: E.qui2_cdf(x, 3)),
                          ("F", lambda x: E.f_cdf(x, 3, 10)),
                          ("t", lambda x: E.t_cdf(x, 5))):
            with self.subTest(dist=nome):
                self.assertAlmostEqual(cdf(0.0), 0.0 if nome != "t" else 0.5, places=6)
                self.assertAlmostEqual(cdf(500.0), 1.0, places=4)
                valores = [cdf(x) for x in (0.5, 1, 2, 5, 10)]
                self.assertEqual(valores, sorted(valores))


class TestOsTestesContraAFormula(unittest.TestCase):
    """Cada estatística conferida contra a fórmula calculada aqui."""

    A = [27.5, 21.0, 19.0, 23.6, 17.0, 17.9, 16.9, 15.4, 19.4, 13.4]
    B = [27.1, 22.0, 20.8, 23.4, 23.4, 23.5, 25.8, 22.0, 24.7, 21.2]

    def test_t_de_student(self):
        nx, ny = len(self.A), len(self.B)
        vx, vy = statistics.variance(self.A), statistics.variance(self.B)
        agrupada = ((nx - 1) * vx + (ny - 1) * vy) / (nx + ny - 2)
        esperado = ((statistics.fmean(self.A) - statistics.fmean(self.B))
                    / math.sqrt(agrupada * (1 / nx + 1 / ny)))
        achado = E.t_independente(self.A, self.B)
        self.assertAlmostEqual(achado["t"], esperado, places=4)
        self.assertEqual(achado["gl"], 18)

    def test_welch_tem_graus_de_liberdade_proprios(self):
        nx, ny = len(self.A), len(self.B)
        vx, vy = statistics.variance(self.A), statistics.variance(self.B)
        esperado = ((vx / nx + vy / ny) ** 2
                    / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1)))
        achado = E.t_independente(self.A, self.B, variancias_iguais=False)
        self.assertAlmostEqual(achado["gl"], esperado, places=2)
        self.assertLess(achado["gl"], 18)      # Welch nunca dá mais que o agrupado

    def test_t_pareado(self):
        antes = [200, 210, 205, 190, 220, 215, 195, 205]
        depois = [190, 200, 195, 185, 205, 200, 190, 195]
        dif = [b - a for a, b in zip(antes, depois)]
        esperado = statistics.fmean(dif) / (statistics.stdev(dif) / math.sqrt(len(dif)))
        self.assertAlmostEqual(E.t_pareado(antes, depois)["t"], esperado, places=4)

    def test_pareado_descarta_par_incompleto(self):
        """Quem não foi medido nos dois momentos não forma par. O 9 do fim
        não pode entrar sozinho: entrar sozinho seria comparar a média de
        umas pessoas com a média de outras, e isso não é teste pareado."""
        com_falta = E.t_pareado([1, 2, 3, None], [2, 4, 9, 9])
        so_os_pares = E.t_pareado([1, 2, 3], [2, 4, 9])
        self.assertEqual(com_falta["n"], 3)
        self.assertEqual(com_falta["t"], so_os_pares["t"])
        self.assertEqual(com_falta["diferenca"], so_os_pares["diferenca"])

    def test_mann_whitney_contra_a_contagem_direta(self):
        """U é, por definição, quantas vezes alguém de x supera alguém de y.
        Os grupos têm tamanhos diferentes de propósito: com nx == ny a
        fórmula fica simétrica e um erro de qual grupo descontar some."""
        x, y = [3, 9, 11, 14], [1, 2, 4, 5, 6, 7, 8]
        direto = sum(1 for i in x for j in y if i > j) \
            + 0.5 * sum(1 for i in x for j in y if i == j)
        self.assertNotEqual(len(x), len(y))
        self.assertEqual(E.mann_whitney(x, y)["u"], direto)

    def test_mann_whitney_em_grupos_iguais_da_o_meio(self):
        x = [1, 2, 3, 4, 5, 6]
        r = E.mann_whitney(x, list(x))
        self.assertEqual(r["u"], len(x) * len(x) / 2)
        self.assertGreater(r["p"], 0.9)

    def test_wilcoxon_contra_a_soma_de_postos(self):
        antes = [200, 210, 205, 190, 220, 215, 195, 205]
        depois = [190, 200, 195, 185, 205, 200, 190, 195]
        # todas as diferenças são negativas: a soma positiva é zero
        self.assertEqual(E.wilcoxon(antes, depois)["w"], 0)

    def test_wilcoxon_descarta_empate(self):
        """O método descarta o par sem diferença — é o que ele faz."""
        r = E.wilcoxon([1, 2, 3, 4], [1, 3, 4, 5])
        self.assertEqual(r["n"], 3)

    def test_anova_e_friedman_concordam_no_obvio(self):
        linhas = [[8, 6, 4], [7, 5, 3], [9, 7, 5], [8, 6, 5],
                  [7, 6, 4], [9, 8, 6], [8, 7, 5], [7, 5, 4]]
        self.assertLess(E.anova_medidas_repetidas(linhas)["p"], 0.01)
        self.assertLess(E.friedman(linhas)["p"], 0.05)

    def test_anova_sem_efeito_nao_inventa(self):
        linhas = [[5, 5, 5], [6, 6, 6], [4, 4, 4], [7, 7, 7], [5, 5, 5]]
        r = E.anova_medidas_repetidas(linhas)
        self.assertTrue(r["p"] is None or r["p"] > 0.9)

    def test_levene_acusa_variancia_diferente(self):
        igual = E.levene([1, 2, 3, 4, 5, 6, 7, 8], [2, 3, 4, 5, 6, 7, 8, 9])
        diferente = E.levene([5, 5, 5, 5, 5, 6, 5, 5],
                             [1, 20, 3, 40, 5, 60, 7, 80])
        self.assertTrue(igual["iguais"])
        self.assertFalse(diferente["iguais"])

    def test_levene_centra_na_mediana_e_nao_na_media(self):
        """Brown-Forsythe é Levene centrado na MEDIANA — é essa troca que
        segura o teste quando o dado é torto, e dado de escala clínica é
        torto quase sempre. Aqui a conta é refeita à mão com a mediana:
        num grupo com um valor distante, média e mediana se separam, e a
        versão da média devolve outro número."""
        grupos = [[1, 2, 3, 4, 5, 6, 40], [2, 3, 4, 5, 6, 7, 8]]
        z = [[abs(v - statistics.median(g)) for v in g] for g in grupos]
        k, n = 2, sum(len(g) for g in grupos)
        mz = [statistics.fmean(g) for g in z]
        mg = statistics.fmean([v for g in z for v in g])
        entre = sum(len(g) * (m - mg) ** 2 for g, m in zip(z, mz))
        dentro = sum((v - m) ** 2 for g, m in zip(z, mz) for v in g)
        esperado = (n - k) / (k - 1.0) * entre / dentro
        # a média do primeiro grupo é puxada pelo 40; a mediana, não
        self.assertNotEqual(statistics.median(grupos[0]),
                            statistics.fmean(grupos[0]))
        self.assertAlmostEqual(E.levene(*grupos)["w"], esperado, places=4)


class TestAsSuposicoes(unittest.TestCase):

    def test_dado_normal_passa_na_normalidade(self):
        import random
        sorteio = random.Random(7)
        dados = [sorteio.gauss(10, 2) for _ in range(120)]
        self.assertTrue(E.normalidade(dados)["normal"])

    def test_dado_muito_torto_nao_passa(self):
        import random
        sorteio = random.Random(7)
        dados = [sorteio.expovariate(0.5) for _ in range(120)]
        self.assertFalse(E.normalidade(dados)["normal"])

    def test_a_assimetria_sozinha_reprova(self):
        """K² soma dois termos, assimetria e curtose. Este dado tem cauda
        de peso quase normal (z de curtose abaixo de 1,96): quem o reprova
        é só a assimetria. Se o termo de assimetria sumisse do K², o dado
        passaria — e um dado torto seria tratado como normal."""
        import random
        sorteio = random.Random(5)
        dados = [sorteio.gauss(0, 1) ** 2 for _ in range(90)]
        achado = E.normalidade(dados)
        self.assertLess(abs(achado["z_curtose"]), 1.96)
        self.assertGreater(achado["z_assimetria"], 3)
        self.assertFalse(achado["normal"])

    def test_amostra_pequena_diz_que_nao_da_para_testar(self):
        """Testar normalidade com cinco valores é teatro."""
        r = E.normalidade([1, 2, 3, 4, 5])
        self.assertIsNone(r["normal"])
        self.assertIn("não há como testar", r["aviso"])

    def test_amostra_media_avisa_que_detecta_pouco(self):
        r = E.normalidade([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertIsNotNone(r["p"])
        self.assertIn("detecta pouco", r["aviso"])

    def test_o_qq_sai_junto_do_teste(self):
        """O desenho é mais honesto que o valor-p nos dois extremos de n."""
        r = E.normalidade([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(len(r["qq"]), 10)
        for ponto in r["qq"]:
            self.assertIn("esperado", ponto)
            self.assertIn("observado", ponto)

    def test_o_qq_sai_ordenado(self):
        r = E.normalidade([9, 1, 5, 3, 7, 2, 8, 4, 6, 10])
        observados = [p["observado"] for p in r["qq"]]
        self.assertEqual(observados, sorted(observados))


class TestPoderEAmostra(unittest.TestCase):
    """Os números de planejamento, contra a tabela publicada de Cohen."""

    def test_bate_com_a_tabela_de_cohen(self):
        for d, esperado in ((0.2, 394), (0.5, 64), (0.8, 26)):
            with self.subTest(d=d):
                self.assertEqual(E.amostra_necessaria(d, 0.80)["n"], esperado)

    def test_o_n_devolvido_e_o_menor_que_serve(self):
        for d in (0.3, 0.5, 0.8):
            with self.subTest(d=d):
                n = E.amostra_necessaria(d, 0.80)["n"]
                self.assertGreaterEqual(E.poder(d, n), 0.80)
                self.assertLess(E.poder(d, n - 1), 0.80)

    def test_pareado_precisa_de_menos_gente(self):
        """Cada pessoa é o próprio controle."""
        for d in (0.5, 0.8):
            with self.subTest(d=d):
                self.assertLess(E.amostra_necessaria(d, 0.80, pareado=True)["n"],
                                E.amostra_necessaria(d, 0.80)["n"])

    def test_mais_poder_exige_mais_gente(self):
        self.assertGreater(E.amostra_necessaria(0.5, 0.90)["n"],
                           E.amostra_necessaria(0.5, 0.80)["n"])

    def test_o_menor_detectavel_e_o_inverso_da_amostra(self):
        """Com 64 por grupo o menor efeito detectável tem de voltar a 0,5."""
        self.assertAlmostEqual(E.menor_efeito_detectavel(64, 0.80), 0.5, delta=0.02)

    def test_amostra_pequena_so_detecta_efeito_enorme(self):
        self.assertGreater(E.menor_efeito_detectavel(6, 0.80), 1.5)

    def test_o_plano_traz_as_duas_leituras(self):
        plano = E.plano_amostral(14)
        self.assertEqual(len(plano["linhas"]), 4)
        for linha in plano["linhas"]:
            self.assertIn("n80", linha)
            self.assertIn("poder_atual", linha)
        self.assertIn("menor_detectavel_80", plano)

    def test_sem_amostra_o_plano_ainda_serve_para_planejar(self):
        plano = E.plano_amostral(None)
        self.assertEqual(len(plano["linhas"]), 4)
        self.assertNotIn("n_atual", plano)
        for linha in plano["linhas"]:
            self.assertNotIn("poder_atual", linha)

    def test_nao_existe_poder_observado(self):
        """Poder calculado do efeito medido é função monótona do valor-p:
        não acrescenta informação, e soa como "faltou gente" mesmo quando
        a leitura certa é "não há efeito"."""
        fonte = (ROOT / "scripts" / "lape" / "estatistica.py").read_text(encoding="utf-8")
        self.assertNotIn("poder_observado", fonte)
        self.assertIn("funcao\n    # monotona do proprio valor-p".replace("\n    # ", " "),
                      fonte.replace("\n    # ", " "))


if __name__ == "__main__":
    unittest.main()
