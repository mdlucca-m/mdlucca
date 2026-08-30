#!/usr/bin/env python3
"""Testes do simulador de cenários.

    python3 -m unittest tests.test_cenario -v

O risco desta tela não é errar a conta — a conta é uma rampa linear. É
apresentar suposição como medida. Metade destes testes guarda a
aritmética; a outra metade guarda a honestidade da apresentação.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import cenario, ingest_excel  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
DASHBOARD_JS = TEMPLATES / "dashboard.js"
NODE = shutil.which("node")


def _recorta(nome: str) -> str:
    texto = DASHBOARD_JS.read_text(encoding="utf-8")
    inicio = texto.index(f"function {nome}(")
    fim = texto.index("\n", inicio)
    if texto[inicio:fim].rstrip().endswith("}"):
        return texto[inicio:fim]
    return texto[inicio:texto.index("\n}\n", inicio) + 3]


class BaseCenario(unittest.TestCase):
    def monta(self, por_ano: dict[int, int]):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Database(Path(tmp.name) / "t.sqlite")
        self.addCleanup(db.close)
        db.migrate()
        linhas = []
        for ano, n in por_ano.items():
            for i in range(n):
                linhas.append({"title": f"Artigo {ano}-{i}", "status": "Publicado",
                               "year_published": ano, "published_on": f"{ano}-06-01",
                               "lead": f"Pessoa {i % 3}"})
        ingest_excel.ingest_articles(db, linhas)
        return db


class TestABase(BaseCenario):
    def test_o_ritmo_ignora_o_ano_corrente(self):
        """Um ano pela metade puxaria o ritmo para baixo em janeiro.

        Sem isto o cenário mudaria sozinho conforme o calendário, e a
        mesma tela daria respostas diferentes em meses diferentes.
        """
        hoje = date.today().year
        db = self.monta({hoje - 3: 10, hoje - 2: 10, hoje - 1: 10, hoje: 1})
        b = cenario.base(db)
        ritmo = next(p for p in b["parametros"] if p["chave"] == "ritmo")
        self.assertEqual(ritmo["valor"], 10.0)
        self.assertTrue(ritmo["medido"])

    def test_a_serie_nao_tem_buraco(self):
        # ano sem publicação é zero, não ausência: o gráfico precisa do eixo
        hoje = date.today().year
        db = self.monta({hoje - 4: 3, hoje - 1: 5})
        b = cenario.base(db)
        self.assertEqual(b["anos"], list(range(hoje - 4, hoje + 1)))
        self.assertEqual(len(b["serie"]), len(b["anos"]))
        self.assertEqual(b["serie"][1], 0)

    def test_o_que_nao_pode_ser_medido_e_declarado(self):
        """O atraso é a mentira mais fácil desta tela.

        Sem data de submissão no banco não há como medir o intervalo até a
        indexação. Ele entra como suposição, e a tela é obrigada a dizer.
        """
        hoje = date.today().year
        db = self.monta({hoje - 2: 4, hoje - 1: 5})
        b = cenario.base(db)
        atraso = next(p for p in b["parametros"] if p["chave"] == "atraso")
        self.assertFalse(atraso["medido"])
        # a procedência diz POR QUE não pôde ser medido; quem escreve a
        # palavra "suposição" na frente é a tela, e não o dado -- senão
        # ela sai duplicada
        self.assertIn("data de submissão", atraso["base"])
        self.assertNotIn("suposição", atraso["base"])
        self.assertIn("atraso", b["sem_base"])

    def test_todo_parametro_diz_de_onde_veio(self):
        hoje = date.today().year
        db = self.monta({hoje - 2: 4, hoje - 1: 5})
        for p in cenario.base(db)["parametros"]:
            with self.subTest(par=p["chave"]):
                self.assertTrue(p["base"], "parâmetro sem procedência declarada")
                self.assertIn("medido", p)
                self.assertLess(p["minimo"], p["maximo"])

    def test_a_regua_e_o_melhor_ano_do_proprio_laboratorio(self):
        # pedir três por pessoa a um grupo que nunca passou de um é um
        # número, não um plano
        hoje = date.today().year
        db = self.monta({hoje - 3: 2, hoje - 2: 9, hoje - 1: 4})
        b = cenario.base(db)
        self.assertEqual(b["pico"]["valor"], 9)
        self.assertEqual(b["pico"]["ano"], hoje - 2)
        self.assertIsNotNone(b["melhor_por_pesquisador"])

    def test_sem_ninguem_cadastrado_nao_ha_por_pessoa(self):
        """Dividir por zero pessoas daria infinito, e infinito vira "—".

        Sem saber quantos são, "publicações por pessoa" não tem valor
        possível — e chutar um denominador seria inventar a régua contra a
        qual todo cenário se mede.
        """
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Database(Path(tmp.name) / "vazio.sqlite")
        self.addCleanup(db.close)
        db.migrate()
        hoje = date.today().year
        ingest_excel.ingest_articles(db, [
            {"title": "Sozinho", "status": "Publicado", "year_published": hoje - 1}])
        self.assertIsNone(cenario.base(db)["melhor_por_pesquisador"])

    def test_banco_sem_publicacao_nao_quebra(self):
        db = self.monta({})
        b = cenario.base(db)
        self.assertEqual(b["anos"], [])
        self.assertEqual(b["serie"], [])
        ritmo = next(p for p in b["parametros"] if p["chave"] == "ritmo")
        self.assertEqual(ritmo["valor"], 0.0)
        self.assertFalse(ritmo["medido"])

    def test_o_cenario_vai_no_payload(self):
        from lape import metrics
        hoje = date.today().year
        db = self.monta({hoje - 2: 4, hoje - 1: 5})
        self.assertIn("cenario", metrics.build_payload(db))


@unittest.skipIf(NODE is None, "node não está disponível nesta máquina")
class TestAProjecao(unittest.TestCase):
    """A conta, rodada no Node a partir do próprio dashboard.js."""

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("round1") + "\n" + _recorta("projetarCenario")

    def projeta(self, base, ajuste):
        script = (self.fonte + "\nprocess.stdout.write(JSON.stringify("
                  + "projetarCenario(" + json.dumps(base) + ", "
                  + json.dumps(ajuste) + ")));\n")
        pronto = subprocess.run([NODE, "--input-type=module", "-e", script],
                                capture_output=True, text=True)
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        return json.loads(pronto.stdout)

    BASE = {"anos": [2021, 2022, 2023, 2024], "serie": [8, 12, 9, 6],
            "ano_corrente": 2024}
    AJUSTE = {"ritmo": 10, "pesquisadores": 5, "pesquisadoresBase": 5,
              "atraso": 12, "horizonte": 4}

    def test_o_realizado_nao_e_reescrito(self):
        # a linha do cenário repete o medido até hoje e só então se separa
        p = self.projeta(self.BASE, self.AJUSTE)
        self.assertEqual(p["linha"][:4], self.BASE["serie"])
        self.assertEqual(p["corte"], 4)

    def test_a_mudanca_nao_acontece_no_dia_em_que_se_decide(self):
        """Com atraso de 12 meses o primeiro ano ainda está a caminho.

        Um cenário que salta do valor de hoje para o alvo no ano seguinte
        promete uma resposta instantânea que nenhum laboratório tem.
        """
        p = self.projeta(self.BASE, self.AJUSTE)
        # último real 6, alvo 10: em 1 ano a rampa completa, então 10
        self.assertEqual(p["linha"][4], 10.0)
        lento = self.projeta(self.BASE, dict(self.AJUSTE, atraso=36))
        self.assertLess(lento["linha"][4], 10.0)      # ainda subindo
        self.assertGreater(lento["linha"][4], 6.0)

    def test_atraso_zero_nao_divide_por_zero(self):
        p = self.projeta(self.BASE, dict(self.AJUSTE, atraso=0))
        self.assertEqual(p["linha"][4], 10.0)

    def test_a_equipe_escala_o_ritmo(self):
        dobro = self.projeta(self.BASE, dict(self.AJUSTE, pesquisadores=10))
        self.assertEqual(dobro["alvo"], 20.0)
        metade = self.projeta(self.BASE, dict(self.AJUSTE, pesquisadores=2))
        self.assertEqual(metade["alvo"], 4.0)

    def test_a_faixa_cerca_a_linha(self):
        # nenhum ano projetado sai com um número só
        p = self.projeta(self.BASE, self.AJUSTE)
        for i in range(p["corte"], len(p["linha"])):
            with self.subTest(i=i):
                self.assertLessEqual(p["baixo"][i], p["linha"][i])
                self.assertGreaterEqual(p["alto"][i], p["linha"][i])
        self.assertGreater(p["alto"][-1], p["baixo"][-1])

    def test_diz_quando_a_curva_volta_a_subir(self):
        p = self.projeta(self.BASE, self.AJUSTE)
        self.assertEqual(p["viraEm"], 2025)

    def test_cenario_que_nao_vira_admite_que_nao_vira(self):
        # ritmo abaixo do último ano: a curva desce e o campo fica nulo
        p = self.projeta(self.BASE, dict(self.AJUSTE, ritmo=3))
        self.assertIsNone(p["viraEm"])

    def test_a_conta_por_pesquisador_sai_junto(self):
        p = self.projeta(self.BASE, self.AJUSTE)
        self.assertEqual(p["porPessoa"], 2.0)      # 10 publicações / 5 pessoas


class TestAApresentacao(unittest.TestCase):
    """O que separa um simulador de uma promessa."""

    def js(self):
        return DASHBOARD_JS.read_text(encoding="utf-8")

    def corpo(self):
        t = self.js()
        return t[t.index('view("cenarios"'):t.index('view("descobertas"')]

    def test_o_projetado_e_tracejado_e_sem_marcador(self):
        # o ponto redondo é reservado ao que foi medido
        self.assertIn('dash: "6 4"', self.corpo())
        graficos = (TEMPLATES / "charts.js").read_text(encoding="utf-8")
        linhas = graficos[graficos.index("function lines(spec)"):]
        linhas = linhas[:linhas.index("(spec.marks || [])")]
        self.assertIn("if (serieSpec.dash) return;", linhas)

    def test_nenhum_ano_projetado_sai_com_um_numero_so(self):
        self.assertIn("band: { baixo: p.baixo, alto: p.alto }", self.corpo())
        graficos = (TEMPLATES / "charts.js").read_text(encoding="utf-8")
        self.assertIn("serieSpec.band", graficos)

    def test_a_procedencia_aparece_no_proprio_controle(self):
        # nota de rodapé não impede ninguém de ler a linha como previsão
        js = self.js()
        corpo = js[js.index("function controleDeCenario"):js.index('view("cenarios"')]
        self.assertIn('par.medido ? "medido: " : "suposição: "', corpo)
        self.assertIn("par.base", corpo)
        css = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
        self.assertIn(".cen-base.suposicao", css)

    def test_o_cenario_se_mede_contra_o_melhor_ano_real(self):
        corpo = self.corpo()
        self.assertIn("melhor.por_pessoa", corpo)
        self.assertIn("pede mais do que o laboratório já fez", corpo)

    def test_o_estado_sobrevive_ao_redesenho_ao_vivo(self):
        # o painel se redesenha a cada evento; um cenário que se apaga
        # sozinho não serve para conversar com ninguém
        js = self.js()
        self.assertLess(js.index("const CENARIO = {"), js.index('view("cenarios"'))

    def test_a_limitacao_do_modelo_esta_na_tela(self):
        self.assertIn("submissoes_registradas", self.corpo())
        self.assertIn("O modelo é simples porque a base é", self.corpo())


if __name__ == "__main__":
    unittest.main(verbosity=2)
