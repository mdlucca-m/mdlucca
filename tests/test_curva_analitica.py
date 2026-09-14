"""Integral, derivada e limiar de uma serie no tempo.

Tres leituras que o valor final sozinho nao da. E tres modos de errar que
aparecem em artigo publicado:

  · comparar a area BRUTA entre grupos que partiram de niveis diferentes,
    e concluir sobre o efeito quando se esta medindo o ponto de partida;
  · tratar a data de cruzamento do limiar como MEDIDA, quando ela e
    interpolada entre duas coletas;
  · ignorar o sentido do instrumento -- cruzar 35 para baixo no VO2 e a
    ma noticia, e para baixo na dor e a boa.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import estatistica as E  # noqa: E402


class TestAIntegral(unittest.TestCase):

    def test_o_retangulo_conhecido(self):
        """Valor constante 5 por 10 dias são 50. Se esta falhar, nenhuma
        outra área deste arquivo quer dizer nada."""
        self.assertEqual(E.area_sob_a_curva([0, 10], [5, 5])["bruta"], 50.0)

    def test_o_trapezio_de_dois_trechos(self):
        r = E.area_sob_a_curva([0, 10, 20], [0, 10, 0])
        self.assertEqual(r["bruta"], 100.0)     # dois triângulos de 50

    def test_sem_mudanca_a_incremental_e_zero(self):
        self.assertEqual(E.area_sob_a_curva([0, 56, 112], [5, 5, 5])["incremental"], 0.0)

    def test_a_bruta_mede_o_ponto_de_partida_e_a_incremental_mede_a_mudanca(self):
        """É o erro que este módulo existe para evitar. Duas pessoas com a
        MESMA queda de 6 pontos, partindo de níveis diferentes: a área
        bruta difere em cinco vezes, e a incremental é idêntica.

        Comparar a bruta entre grupos que não partiram do mesmo lugar é
        concluir sobre o nível inicial achando que se conclui sobre o
        efeito."""
        alta = E.area_sob_a_curva([0, 56, 112], [8, 5, 2])
        baixa = E.area_sob_a_curva([0, 56, 112], [4, 1, -2])
        self.assertGreater(alta["bruta"], baixa["bruta"] * 4)
        self.assertEqual(alta["incremental"], baixa["incremental"])

    def test_a_media_no_tempo_volta_para_a_unidade_do_instrumento(self):
        """A área sai em "pontos × dia", que ninguém interpreta. Dividida
        pela duração, volta a ser um valor da escala."""
        r = E.area_sob_a_curva([0, 112], [8, 2])
        self.assertEqual(r["media_no_tempo"], 5.0)
        self.assertEqual(r["duracao"], 112.0)

    def test_a_base_pode_vir_de_fora(self):
        """A linha de base do GRUPO, e não a da pessoa, quando se quer
        comparar todo mundo contra o mesmo ponto."""
        propria = E.area_sob_a_curva([0, 10], [8, 8])
        do_grupo = E.area_sob_a_curva([0, 10], [8, 8], base=5)
        self.assertEqual(propria["incremental"], 0.0)
        self.assertEqual(do_grupo["incremental"], 30.0)

    def test_um_momento_so_nao_tem_area(self):
        r = E.area_sob_a_curva([0], [5])
        self.assertIsNone(r["bruta"])
        self.assertIn("dois momentos", r["aviso"])

    def test_momentos_na_mesma_data_nao_tem_area(self):
        r = E.area_sob_a_curva([10, 10], [5, 8])
        self.assertIsNone(r["bruta"])
        self.assertIn("mesma data", r["aviso"])

    def test_a_ordem_das_coletas_nao_muda_a_area(self):
        """A planilha pode vir em qualquer ordem; a área não pode depender
        disso -- fora de ordem, o trapézio sai com largura negativa."""
        certa = E.area_sob_a_curva([0, 56, 112], [8, 5, 2])
        trocada = E.area_sob_a_curva([112, 0, 56], [2, 8, 5])
        self.assertEqual(certa["bruta"], trocada["bruta"])

    def test_o_momento_faltante_nao_vira_zero(self):
        r = E.area_sob_a_curva([0, 56, 112], [8, None, 2])
        self.assertEqual(r["n_pontos"], 2)
        self.assertEqual(r["bruta"], (8 + 2) / 2 * 112)


class TestADerivada(unittest.TestCase):

    def test_a_taxa_sai_por_semana_e_nao_por_dia(self):
        """Numa intervenção de meses, "por dia" produz números com quatro
        zeros depois da vírgula, e ninguém compara números assim."""
        r = E.taxa_de_variacao([0, 7], [10, 3])
        self.assertEqual(r["trechos"][0]["taxa"], -7.0)
        self.assertEqual(r["por"], 7.0)

    def test_um_trecho_por_intervalo(self):
        r = E.taxa_de_variacao([0, 56, 112], [8, 5, 4])
        self.assertEqual(len(r["trechos"]), 2)
        self.assertEqual(r["trechos"][0]["delta"], -3.0)
        self.assertEqual(r["trechos"][1]["delta"], -1.0)

    def test_a_geral_vai_da_ponta_a_ponta(self):
        r = E.taxa_de_variacao([0, 56, 112], [8, 5, 4])
        self.assertAlmostEqual(r["geral"], (4 - 8) / 112 * 7, places=4)

    def test_acha_o_trecho_de_maior_queda(self):
        r = E.taxa_de_variacao([0, 28, 56, 112], [10, 9, 3, 2])
        self.assertEqual(r["maior_queda"]["de"], 28)

    def test_estagnou_quando_o_ultimo_trecho_quase_parou(self):
        """É a leitura que decide prorrogar ou não a intervenção."""
        r = E.taxa_de_variacao([0, 56, 112], [8, 5, 4.7])
        self.assertTrue(r["estagnou"])
        self.assertFalse(r["acelerou"])

    def test_acelerou_quando_o_ultimo_trecho_foi_mais_forte(self):
        r = E.taxa_de_variacao([0, 56, 112], [8, 7.5, 3])
        self.assertTrue(r["acelerou"])
        self.assertFalse(r["estagnou"])

    def test_um_momento_so_nao_tem_taxa(self):
        r = E.taxa_de_variacao([0], [5])
        self.assertIsNone(r["geral"])
        self.assertIn("dois momentos", r["aviso"])


class TestOLimiar(unittest.TestCase):

    def test_o_sentido_vem_do_instrumento_e_inverte_a_conclusao(self):
        """Cruzar 4 para baixo numa escala de dor é a boa notícia; cruzar
        35 para baixo no VO2 é a má. Errar isto inverte a conclusão do
        estudo sem mudar um número sequer."""
        tempos, valores = [0, 112], [8, 2]
        dor = E.cruzamento_do_limiar(tempos, valores, 4, menor_e_melhor=True)
        vo2 = E.cruzamento_do_limiar(tempos, valores, 4, menor_e_melhor=False)
        self.assertTrue(dor["terminou_do_lado_bom"])
        self.assertFalse(vo2["terminou_do_lado_bom"])

    def test_a_data_do_cruzamento_sai_marcada_como_estimada(self):
        """Entre duas coletas não há medida: há interpolação, e ela supõe
        que a mudança foi constante no intervalo -- o que quase nunca é
        verdade. Apresentar isso como data medida é inventar um dado."""
        r = E.cruzamento_do_limiar([0, 100], [10, 0], 5)
        self.assertEqual(r["cruzou_em"], 50.0)
        self.assertTrue(r["estimado"])

    def test_quem_ja_comecou_do_lado_bom_nao_cruzou_nada(self):
        r = E.cruzamento_do_limiar([0, 112], [3, 2], 4)
        self.assertTrue(r["comecou_do_lado_bom"])
        self.assertIsNone(r["cruzou_em"])

    def test_voltar_para_a_faixa_ruim_e_registrado(self):
        """Some quando se olha só o começo e o fim -- e é informação
        clínica: a pessoa melhorou e perdeu."""
        r = E.cruzamento_do_limiar([0, 56, 112], [8, 3, 6], 4)
        self.assertTrue(r["voltou"])
        self.assertFalse(r["terminou_do_lado_bom"])

    def test_quem_nunca_saiu_da_faixa_ruim(self):
        r = E.cruzamento_do_limiar([0, 112], [8, 7], 4)
        self.assertIsNone(r["cruzou_em"])
        self.assertEqual(r["tempo_do_lado_bom"], 0.0)

    def test_o_tempo_do_lado_bom_conta_so_a_fracao_apos_o_cruzamento(self):
        """Cruzou na metade do intervalo: metade do tempo conta."""
        r = E.cruzamento_do_limiar([0, 100], [10, 0], 5)
        self.assertEqual(r["tempo_do_lado_bom"], 50.0)

    def test_quem_passou_o_periodo_inteiro_do_lado_bom(self):
        r = E.cruzamento_do_limiar([0, 112], [2, 1], 4)
        self.assertEqual(r["tempo_do_lado_bom"], 112.0)


class TestOQueNaoDaParaDizerComTresMomentos(unittest.TestCase):

    def test_o_modulo_declara_quantos_pontos_um_ponto_de_quebra_exige(self):
        """Ajustar duas retas a três pontos é um exercício sem graus de
        liberdade: qualquer conjunto de três pontos tem uma quebra
        perfeita, e ela não quer dizer nada. O número está declarado para
        que ninguém implemente a quebra por cima de três pontos achando
        que dá."""
        self.assertGreaterEqual(E.N_MINIMO_PARA_QUEBRA, 5)

    def test_nao_existe_funcao_de_quebra_prometendo_o_que_o_dado_nao_da(self):
        self.assertFalse(hasattr(E, "ponto_de_quebra"),
                         "se um dia existir, precisa recusar abaixo de "
                         "N_MINIMO_PARA_QUEBRA pontos")


if __name__ == "__main__":
    unittest.main()
