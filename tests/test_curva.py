#!/usr/bin/env python3
"""A leitura da curva: viradas, cruzamentos e travessias de limite.

    python3 -m unittest tests.test_curva -v

Um grafico de linhas mostra o percurso e cala sobre o percurso. Quem le
tem de achar a olho onde a serie virou, onde duas trocaram de posicao e
onde uma passou da meta -- e e exatamente nesses tres pontos que esta a
noticia.

Anotar automaticamente tem dois modos de errar, e os dois sao piores do
que nao anotar:

  - Anotar ruido. Uma serie que faz 4, 5, 4, 5 tem tres viradas e nenhuma
    noticia; o grafico fica pintado de anel e ninguem le nenhum.
  - Anotar o que nao aconteceu. `3 - null` da 3 em JavaScript, entao um
    mes sem coleta virava um vale inventado.

A conta roda no Node, recortada do proprio `charts.js`: reescreve-la aqui
testaria a copia, e nao o que o painel desenha.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

CHARTS = (ROOT / "scripts" / "lape" / "templates" / "charts.js").read_text(encoding="utf-8")
NODE = shutil.which("node")


def _funcao() -> str:
    """A funcao recortada do charts.js, com o mínimo para rodar sozinha."""
    ini = CHARTS.index("  function marcosDaCurva(labels, series, opts) {")
    fim = CHARTS.index("\n  /* ====================================", ini)
    corpo = CHARTS[ini:fim].replace("  function marcosDaCurva", "function marcosDaCurva", 1)
    return "const fmt = (n) => String(n);\n" + corpo


def ler(labels, series, opts=None):
    script = _funcao() + "\nconsole.log(JSON.stringify(marcosDaCurva(%s, %s, %s)));" % (
        json.dumps(labels), json.dumps(series), json.dumps(opts or {}))
    pronto = subprocess.run([NODE, "--input-type=module", "-e", script],
                            capture_output=True, text=True)
    if pronto.returncode != 0:
        raise AssertionError(pronto.stderr)
    return json.loads(pronto.stdout)


ANOS = ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]


@unittest.skipIf(NODE is None, "node não instalado")
class TestAsViradas(unittest.TestCase):

    def test_pico_e_vale_saem_no_ponto_certo(self):
        serie = {"label": "A", "values": [2, 6, 10, 4, 5, 9, 14, 18]}
        saida = ler(ANOS, [serie])
        achados = {m["label"]: m["i"] for m in saida["marks"]}
        self.assertEqual(achados.get("pico"), 2)
        self.assertEqual(achados.get("vale"), 3)

    def test_serie_que_so_sobe_nao_tem_virada(self):
        """Uma acumulada nunca vira -- e marcar nela seria marcar nada."""
        saida = ler(ANOS, [{"label": "A", "values": [1, 2, 3, 4, 5, 6, 7, 8]}])
        self.assertEqual(saida["marks"], [])

    def test_ruido_nao_e_virada(self):
        """4, 5, 4, 5 tem tres viradas e nenhuma noticia."""
        saida = ler(ANOS, [{"label": "R", "values": [4, 5, 4, 5, 4, 5, 4, 40]}])
        self.assertLessEqual(len(saida["marks"]), 1)

    def test_serie_curta_nao_e_analisada(self):
        self.assertEqual(ler(["a", "b"], [{"label": "C", "values": [1, 2]}])["marks"], [])


@unittest.skipIf(NODE is None, "node não instalado")
class TestOsCruzamentos(unittest.TestCase):

    def test_quem_passou_quem_e_em_que_ano(self):
        a = {"label": "A", "values": [2, 6, 10, 4, 5, 9, 14, 18]}
        b = {"label": "B", "values": [20, 17, 14, 11, 8, 6, 4, 2]}
        saida = ler(ANOS, [a, b])
        cruzou = [m for m in saida["marks"] if m["label"] == "cruzou"]
        self.assertTrue(cruzou)
        self.assertIn("A passou B", " ".join(saida["notas"]))

    def test_series_paralelas_nao_cruzam(self):
        a = {"label": "A", "values": [1, 2, 3, 4, 5, 6, 7, 8]}
        b = {"label": "B", "values": [11, 12, 13, 14, 15, 16, 17, 18]}
        saida = ler(ANOS, [a, b])
        self.assertEqual([m for m in saida["marks"] if m["label"] == "cruzou"], [])


@unittest.skipIf(NODE is None, "node não instalado")
class TestOsLimites(unittest.TestCase):

    def test_a_travessia_da_meta_e_marcada(self):
        saida = ler(ANOS, [{"label": "Publicados", "values": [2, 4, 6, 8, 11, 13, 14, 15]}],
                    {"limites": [{"valor": 10, "rotulo": "meta"}]})
        passou = [m for m in saida["marks"] if m["label"] == "passou"]
        self.assertEqual(len(passou), 1)
        self.assertEqual(passou[0]["i"], 4)
        self.assertIn("passou de meta", " ".join(saida["notas"]))

    def test_a_queda_abaixo_do_piso_tambem(self):
        saida = ler(ANOS, [{"label": "X", "values": [20, 18, 16, 14, 9, 8, 7, 6]}],
                    {"limites": [{"valor": 10, "rotulo": "piso"}]})
        self.assertTrue([m for m in saida["marks"] if m["label"] == "caiu"])

    def test_limite_nunca_alcancado_nao_marca(self):
        saida = ler(ANOS, [{"label": "X", "values": [1, 2, 3, 4, 5, 6, 7, 8]}],
                    {"limites": [{"valor": 900, "rotulo": "meta"}]})
        self.assertEqual([m for m in saida["marks"] if m["label"] in ("passou", "caiu")], [])


@unittest.skipIf(NODE is None, "node não instalado")
class TestOsBuracosNaSerie(unittest.TestCase):
    """`3 - null` da 3: um mes sem coleta virava um vale inventado."""

    def test_o_nulo_nao_vira_zero(self):
        com = ler(ANOS, [{"label": "N", "values": [1, None, 3, 1, 5, 2, 8, 1]}])
        for marca in com["marks"]:
            self.assertNotIn(marca["i"], (0, 1),
                             "marca em cima do buraco: %r" % (marca,))

    def test_serie_toda_nula_nao_quebra_nem_marca(self):
        self.assertEqual(ler(ANOS, [{"label": "Z", "values": [None] * 8}])["marks"], [])


@unittest.skipIf(NODE is None, "node não instalado")
class TestOCorteEOPareamento(unittest.TestCase):

    def test_marca_e_frase_saem_do_mesmo_corte(self):
        """Listas cortadas em separado descreviam pontos que o gráfico não marcava."""
        serra = {"label": "S", "values": [0, 50, 0, 50, 0, 50, 0, 50]}
        saida = ler(ANOS, [serra], {"maximo": 3})
        self.assertEqual(len(saida["marks"]), len(saida["notas"]))
        self.assertEqual(len(saida["marks"]), 3)

    def test_o_corte_fica_com_o_fim_da_serie(self):
        """O que aconteceu ano passado interessa mais que há oito anos."""
        serra = {"label": "S", "values": [0, 50, 0, 50, 0, 50, 0, 50]}
        saida = ler(ANOS, [serra], {"maximo": 2})
        self.assertEqual([m["i"] for m in saida["marks"]], [5, 6])
        self.assertGreater(saida["total"], len(saida["marks"]))

    def test_as_marcas_saem_em_ordem_de_tempo(self):
        a = {"label": "A", "values": [2, 6, 10, 4, 5, 9, 14, 18]}
        b = {"label": "B", "values": [20, 17, 14, 11, 8, 6, 4, 2]}
        indices = [m["i"] for m in ler(ANOS, [a, b], {"limites": [{"valor": 12}]})["marks"]]
        self.assertEqual(indices, sorted(indices))

    def test_toda_marca_tem_rotulo_curto_e_frase_longa(self):
        a = {"label": "A", "values": [2, 6, 10, 4, 5, 9, 14, 18]}
        saida = ler(ANOS, [a])
        for marca in saida["marks"]:
            self.assertLessEqual(len(marca["label"]), 8, marca)
            self.assertIn("title", marca)


class TestOGraficoDeLinhas(unittest.TestCase):
    """O que o `lines` passou a saber desenhar."""

    def test_o_traco_engrossou(self):
        """2px era traço de papel; na tela de parede a curva sumia."""
        corpo = CHARTS[CHARTS.index("  function lines(spec) {"):
                       CHARTS.index("  function donut(spec) {")]
        self.assertIn('"stroke-width": serieSpec.width || spec.traco || 2.6', corpo)

    def test_o_limite_fica_atras_das_series(self):
        """Referência não disputa tinta com o dado."""
        corpo = CHARTS[CHARTS.index("  function lines(spec) {"):
                       CHARTS.index("  function donut(spec) {")]
        self.assertLess(corpo.index("spec.limites"), corpo.index("series.forEach"))

    def test_o_limite_fora_da_escala_nao_e_desenhado(self):
        corpo = CHARTS[CHARTS.index("  function lines(spec) {"):
                       CHARTS.index("  function donut(spec) {")]
        self.assertIn("if (y < MT - 1 || y > MT + ih + 1) return;", corpo)

    def test_a_dica_mostra_a_variacao(self):
        """A derivada dita onde alguém pergunta "e aí, subiu?" -- sem 2º eixo."""
        corpo = CHARTS[CHARTS.index("  function lines(spec) {"):
                       CHARTS.index("  function donut(spec) {")]
        self.assertIn("const delta =", corpo)
        self.assertIn("vs. ", corpo)

    def test_nenhum_grafico_ganhou_segundo_eixo(self):
        """O erro clássico do gráfico de linhas, e o que ele nunca pode virar."""
        self.assertNotIn("eixoDireito", CHARTS)
        self.assertNotIn("y2Scale", CHARTS)

    def test_a_funcao_e_exportada(self):
        bloco = CHARTS[CHARTS.rindex("  return {"):]
        self.assertIn("marcosDaCurva: marcosDaCurva", bloco)


if __name__ == "__main__":
    unittest.main()
