#!/usr/bin/env python3
"""A bancada: participantes, medidas, buracos e tamanho de efeito.

    python3 -m unittest tests.test_coleta -v

Este modulo guarda dado de saude de pessoa identificavel, e faz conta em
cima dele. Os dois lados erram calado:

  - Do lado do dado: um campo com nome entra tao facil quanto um sem, e
    depois viaja no backup e no arquivo exportado.
  - Do lado da conta: um d de Cohen de 0,82 calculado com seis pessoas se
    parece exatamente com um calculado com sessenta, e vai para a
    dissertacao do mesmo jeito.

Daqui a divisao dos testes: o que o modulo recusa a guardar, o que ele
recusa a decidir, e o que ele tem de encontrar -- porque num painel de
coleta o que importa nao e o que foi coletado, e o que falta.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import coleta  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseDaColeta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "c.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.prot = coleta.declarar_protocolo(self.db, "fibro16", "Fibromialgia 16 semanas")
        self.m0 = coleta.declarar_momento(self.db, self.prot["id"], "base",
                                          "Linha de base", 1, dias_apos=0, janela_dias=7)
        self.m1 = coleta.declarar_momento(self.db, self.prot["id"], "s16",
                                          "16 semanas", 2, dias_apos=112, janela_dias=14)
        self.dor = coleta.declarar_instrumento(
            self.db, "eva", "Escala visual de dor", direcao="menor_melhor",
            minimo=0, maximo=10)

    def entrar(self, codigo, grupo="intervencao", entrou=None):
        return coleta.inscrever(self.db, codigo, self.prot["id"], grupo=grupo,
                                entrou_em=entrou or date.today().isoformat())

    def medir(self, pid, momento, valor):
        return coleta.registrar(self.db, pid, self.dor["id"], valor, momento["id"])


class TestOQueNaoEntra(BaseDaColeta):
    """Ninguem e nomeado, e quem tentar precisa receber um erro."""

    def test_campo_que_identifica_e_recusado(self):
        for campo in ("nome", "full_name", "email", "telefone", "cpf", "prontuario"):
            with self.subTest(campo=campo):
                with self.assertRaises(ValueError) as erro:
                    coleta.inscrever(self.db, "P%s" % campo, **{campo: "Maria"})
                self.assertIn("não guarda dado que identifique", str(erro.exception))

    def test_o_erro_nao_e_silencioso(self):
        """Sumir com o campo faria quem digitou achar que foi gravado."""
        with self.assertRaises(ValueError):
            coleta.inscrever(self.db, "P99", nome="Maria")
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM participantes WHERE codigo = 'P99'"), 0)

    def test_participante_sem_codigo_e_recusado(self):
        with self.assertRaises(ValueError):
            coleta.inscrever(self.db, "")

    def test_o_export_longo_nao_tem_de_onde_tirar_um_nome(self):
        p = self.entrar("P01")
        self.medir(p["id"], self.m0, 7)
        linhas = coleta.exportar_longo(self.db)
        self.assertTrue(linhas)
        for linha in linhas:
            for chave in linha:
                self.assertNotIn("nome", chave.replace("instrumento_nome", ""))


class TestOValorImpossivel(BaseDaColeta):

    def test_fora_da_faixa_do_instrumento_e_recusado(self):
        """77 numa escala de 0 a 10 é um dedo escorregando no teclado."""
        p = self.entrar("P01")
        with self.assertRaises(ValueError) as erro:
            self.medir(p["id"], self.m0, 77)
        self.assertIn("fora", str(erro.exception))

    def test_o_limite_vale_dos_dois_lados(self):
        p = self.entrar("P01")
        with self.assertRaises(ValueError):
            self.medir(p["id"], self.m0, -3)

    def test_a_borda_entra(self):
        p = self.entrar("P01")
        self.medir(p["id"], self.m0, 0)
        self.medir(p["id"], self.m1, 10)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM coletas"), 2)

    def test_instrumento_sem_faixa_aceita_qualquer_numero(self):
        livre = coleta.declarar_instrumento(self.db, "passos", "Passos por dia")
        p = self.entrar("P01")
        coleta.registrar(self.db, p["id"], livre["id"], 11421, self.m0["id"])
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM coletas"), 1)

    def test_regravar_a_mesma_medida_atualiza_em_vez_de_duplicar(self):
        p = self.entrar("P01")
        self.medir(p["id"], self.m0, 7)
        self.medir(p["id"], self.m0, 6)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM coletas"), 1)
        self.assertEqual(self.db.scalar("SELECT valor FROM coletas"), 6)


class TestOndeEstaOBuraco(BaseDaColeta):
    """Painel de coleta que só mostra o coletado serve para admirar."""

    def test_a_matriz_marca_o_que_falta(self):
        p = self.entrar("P01")
        self.medir(p["id"], self.m0, 7)
        m = coleta.matriz(self.db, self.prot["id"])
        estados = [c["estado"] for linha in m["linhas"] for c in linha["celulas"]]
        self.assertIn("feita", estados)
        self.assertIn("falta", estados)
        self.assertEqual(m["feitas"], 1)

    def test_passar_da_janela_vira_atraso(self):
        """Sem prazo declarado não há atraso: há o não coletado, para sempre."""
        antigo = (date.today() - timedelta(days=200)).isoformat()
        self.entrar("P02", entrou=antigo)
        m = coleta.matriz(self.db, self.prot["id"])
        estados = [c["estado"] for linha in m["linhas"] for c in linha["celulas"]]
        self.assertIn("atrasada", estados)
        self.assertGreaterEqual(m["atrasadas"], 1)

    def test_quem_saiu_do_estudo_nao_esta_atrasado(self):
        antigo = (date.today() - timedelta(days=200)).isoformat()
        p = self.entrar("P03", entrou=antigo)
        coleta.encerrar(self.db, p["id"], "desistiu", "mudou de cidade")
        m = coleta.matriz(self.db, self.prot["id"])
        estados = [c["estado"] for linha in m["linhas"] for c in linha["celulas"]]
        self.assertNotIn("atrasada", estados)
        self.assertIn("fora", estados)

    def test_a_completude_e_contada_e_nao_digitada(self):
        a, b = self.entrar("P01"), self.entrar("P02")
        self.medir(a["id"], self.m0, 7)
        self.medir(b["id"], self.m0, 5)
        m = coleta.matriz(self.db, self.prot["id"])
        self.assertEqual(m["total_celulas"], 4)
        self.assertEqual(m["completude"], 50.0)

    def test_protocolo_sem_momento_nao_quebra(self):
        vazio = coleta.declarar_protocolo(self.db, "solto", "Sem momentos")
        coleta.inscrever(self.db, "PX", vazio["id"])
        m = coleta.matriz(self.db, vazio["id"])
        self.assertEqual(m["total_celulas"], 0)
        self.assertIsNone(m["completude"])


class TestADesistencia(BaseDaColeta):

    def test_a_saida_guarda_data_e_motivo(self):
        """Desistência apagada vira n menor sem explicação."""
        p = self.entrar("P01")
        saiu = coleta.encerrar(self.db, p["id"], "desistiu", "dor ao exercitar")
        self.assertEqual(saiu["situacao"], "desistiu")
        self.assertEqual(saiu["motivo_saida"], "dor ao exercitar")
        self.assertTrue(saiu["saiu_em"])

    def test_a_perda_e_calculada(self):
        for i in range(4):
            self.entrar("P%02d" % i)
        gente = coleta.participantes(self.db, self.prot["id"])
        coleta.encerrar(self.db, gente[0]["id"], "desistiu", "sem tempo")
        a = coleta.aderencia(self.db, self.prot["id"])
        self.assertEqual(a["total"], 4)
        self.assertEqual(a["perda"], 25.0)

    def test_situacao_inventada_e_recusada(self):
        p = self.entrar("P01")
        with self.assertRaises(ValueError):
            coleta.encerrar(self.db, p["id"], "sumiu_no_mundo")


class TestOTamanhoDeEfeito(BaseDaColeta):

    def test_o_d_vem_com_o_n_ao_lado(self):
        e = coleta.efeito([8, 7, 9, 8, 7, 8], [4, 3, 5, 4, 3, 4])
        self.assertIsNotNone(e["d"])
        self.assertEqual(e["antes"]["n"], 6)
        self.assertEqual(e["depois"]["n"], 6)

    def test_pouca_gente_sai_marcada_como_instavel(self):
        """0,82 com seis pessoas se parece com 0,82 com sessenta."""
        e = coleta.efeito([8, 7, 9, 8, 7, 8], [4, 3, 5, 4, 3, 4])
        self.assertTrue(e["instavel"])
        self.assertIn("instável", e["motivo"])

    def test_gente_suficiente_nao_sai_marcada(self):
        antes = [8, 7, 9, 8, 7, 8, 9, 7, 8, 8, 7, 9]
        depois = [4, 3, 5, 4, 3, 4, 5, 3, 4, 4, 3, 5]
        e = coleta.efeito(antes, depois)
        self.assertFalse(e["instavel"])
        self.assertIsNone(e["motivo"])

    def test_sem_variacao_nao_inventa_efeito(self):
        e = coleta.efeito([5, 5, 5, 5], [5, 5, 5, 5])
        self.assertIsNone(e["d"])
        self.assertTrue(e["instavel"])

    def test_uma_pessoa_so_nao_da_desvio(self):
        e = coleta.efeito([7], [4])
        self.assertIsNone(e["d"])
        self.assertIn("menos", e["motivo"])

    def test_o_sinal_do_d_segue_a_medida_e_nao_a_melhora(self):
        """Em dor, d negativo é melhora. Quem interpreta é a direção
        declarada do instrumento, e não o sinal sozinho."""
        e = coleta.efeito([8, 8, 7, 9], [4, 4, 3, 5])
        self.assertLess(e["d"], 0)
        self.assertEqual(self.dor["direcao"], "menor_melhor")


class TestAAnalise(BaseDaColeta):

    def povoar(self):
        for i in range(6):
            p = self.entrar("I%02d" % i, grupo="intervencao")
            self.medir(p["id"], self.m0, 8)
            self.medir(p["id"], self.m1, 4 + (i % 2))
        for i in range(6):
            p = self.entrar("C%02d" % i, grupo="controle")
            self.medir(p["id"], self.m0, 8)
            self.medir(p["id"], self.m1, 7 + (i % 2))

    def test_cada_grupo_tem_a_propria_serie(self):
        self.povoar()
        a = coleta.analise(self.db, self.prot["id"], self.dor["id"])
        grupos = {s["grupo"] for s in a["series"]}
        self.assertEqual(grupos, {"intervencao", "controle"})

    def test_a_serie_percorre_os_momentos_declarados(self):
        self.povoar()
        a = coleta.analise(self.db, self.prot["id"], self.dor["id"])
        for serie in a["series"]:
            self.assertEqual([p["momento"] for p in serie["pontos"]],
                             ["Linha de base", "16 semanas"])

    def test_a_analise_diz_para_que_lado_e_melhora(self):
        self.povoar()
        a = coleta.analise(self.db, self.prot["id"], self.dor["id"])
        self.assertEqual(a["direcao"], "quanto menor, melhor")

    def test_protocolo_de_um_momento_so_nao_analisa(self):
        curto = coleta.declarar_protocolo(self.db, "curto", "Um momento só")
        coleta.declarar_momento(self.db, curto["id"], "base", "Base", 1)
        a = coleta.analise(self.db, curto["id"], self.dor["id"])
        self.assertEqual(a["series"], [])
        self.assertIn("dois momentos", a["aviso"])

    def test_momento_sem_medida_nao_vira_zero(self):
        """Ninguém medido é n=0, e não média zero."""
        p = self.entrar("P01")
        self.medir(p["id"], self.m0, 7)
        a = coleta.analise(self.db, self.prot["id"], self.dor["id"])
        ultimo = a["series"][0]["pontos"][-1]
        self.assertEqual(ultimo["n"], 0)
        self.assertIsNone(ultimo["media"])


class TestASaida(BaseDaColeta):

    def test_o_formato_longo_tem_uma_linha_por_medida(self):
        a = self.entrar("P01")
        self.medir(a["id"], self.m0, 7)
        self.medir(a["id"], self.m1, 4)
        linhas = coleta.exportar_longo(self.db)
        self.assertEqual(len(linhas), 2)
        self.assertEqual({l["momento"] for l in linhas}, {"base", "s16"})

    def test_o_longo_leva_o_que_a_analise_precisa(self):
        a = self.entrar("P01", grupo="intervencao")
        self.medir(a["id"], self.m0, 7)
        linha = coleta.exportar_longo(self.db)[0]
        for campo in ("participante", "grupo", "instrumento", "momento", "valor"):
            self.assertIn(campo, linha)

    def test_o_resumo_anual_conta_o_ano(self):
        hoje = date.today()
        p = self.entrar("P01")
        self.medir(p["id"], self.m0, 7)
        r = coleta.resumo_anual(self.db, hoje.year)
        self.assertEqual(r["entraram"], 1)
        self.assertEqual(r["medidas"], 1)
        self.assertEqual(len(r["por_mes"]), 12)
        self.assertEqual(r["por_mes"][hoje.month - 1], 1)

    def test_o_ano_vazio_nao_quebra(self):
        r = coleta.resumo_anual(self.db, 1999)
        self.assertEqual(r["entraram"], 0)
        self.assertEqual(r["medidas"], 0)


if __name__ == "__main__":
    unittest.main()
