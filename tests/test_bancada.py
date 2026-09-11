#!/usr/bin/env python3
"""As tabelas da coleta com participantes: o que elas NAO podem guardar.

    python3 -m unittest tests.test_bancada -v

Aqui o banco deixa de ser bibliometria e passa a guardar dado de saude de
pessoa identificavel -- escala de dor, sintomas depressivos, qualidade do
sono de alguem. As regras mudam, e a unica forma segura de nao vazar um
nome e nao ter onde guarda-lo.

Este arquivo e commitado num repositorio, viaja em backup e ja esteve
publico. Por isso o esquema nao tem coluna de nome, de e-mail, de telefone
nem de documento: o participante e um codigo, e a lista que liga o codigo
a pessoa fica fora daqui, com quem coordena o estudo.

Estes testes existem para que ninguem acrescente essas colunas depois "so
para facilitar" -- que e exatamente como isso acontece.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape.db import Database  # noqa: E402

# O que identifica uma pessoa, escrito como costuma aparecer numa coluna.
IDENTIFICA = ("nome", "name", "email", "e_mail", "telefone", "phone", "celular",
              "cpf", "rg", "documento", "endereco", "address", "nascimento_data",
              "data_nascimento", "birth_date", "prontuario", "matricula")


class BaseDaBancada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Database(Path(cls.tmp.name) / "b.sqlite")
        cls.db.migrate()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.tmp.cleanup()

    def colunas(self, tabela: str) -> list[str]:
        return [c["name"] for c in self.db.query("PRAGMA table_info(%s)" % tabela)]


class TestOQueOEsquemaNaoGuarda(BaseDaBancada):

    def test_o_participante_nao_tem_onde_guardar_um_nome(self):
        colunas = self.colunas("participantes")
        achadas = [c for c in colunas
                   if any(marca in c.lower() for marca in IDENTIFICA)]
        self.assertEqual(achadas, [],
                         "coluna que identifica pessoa em participantes: %s" % achadas)

    def test_a_medida_tambem_nao(self):
        colunas = self.colunas("coletas")
        achadas = [c for c in colunas
                   if any(marca in c.lower() for marca in IDENTIFICA)]
        self.assertEqual(achadas, [])

    def test_so_o_ano_de_nascimento(self):
        """Dia e mês reidentificam; ano basta para calcular idade."""
        colunas = self.colunas("participantes")
        self.assertIn("ano_nascimento", colunas)
        self.assertNotIn("data_nascimento", colunas)

    def test_o_codigo_e_unico(self):
        """Dois participantes com o mesmo código misturam duas pessoas."""
        self.db.execute("INSERT INTO participantes (codigo) VALUES ('P01')")
        self.db.conn.commit()
        with self.assertRaises(Exception):
            self.db.execute("INSERT INTO participantes (codigo) VALUES ('P01')")
        self.db.conn.rollback()


class TestOQueOEsquemaGarante(BaseDaBancada):

    def test_apagar_o_participante_leva_as_medidas(self):
        """Medida órfã é dado de saúde sem dono nem consentimento."""
        self.db.execute("INSERT INTO participantes (codigo) VALUES ('P90')")
        self.db.execute("INSERT INTO instrumentos (code, nome) VALUES ('brums', 'BRUMS')")
        self.db.conn.commit()
        pid = self.db.scalar("SELECT id FROM participantes WHERE codigo = 'P90'")
        iid = self.db.scalar("SELECT id FROM instrumentos WHERE code = 'brums'")
        self.db.execute(
            "INSERT INTO coletas (participante_id, instrumento_id, valor) VALUES (?, ?, 12)",
            (pid, iid))
        self.db.conn.commit()
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM coletas WHERE participante_id = ?", (pid,)), 1)
        self.db.execute("DELETE FROM participantes WHERE id = ?", (pid,))
        self.db.conn.commit()
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM coletas WHERE participante_id = ?", (pid,)), 0)

    def test_o_instrumento_declara_para_que_lado_e_melhora(self):
        """"Caiu 4 pontos" é bom em dor e ruim em qualidade de vida."""
        self.assertIn("direcao", self.colunas("instrumentos"))
        self.assertEqual(
            self.db.scalar("SELECT direcao FROM instrumentos WHERE code = 'brums'")
            or "maior_melhor", "maior_melhor")

    def test_o_momento_tem_janela(self):
        """Sem janela declarada não existe "atrasado": só existe o coletado."""
        self.assertIn("janela_dias", self.colunas("momentos"))
        self.assertIn("dias_apos", self.colunas("momentos"))

    def test_a_mesma_medida_nao_entra_duas_vezes(self):
        self.db.execute("INSERT INTO participantes (codigo) VALUES ('P91')")
        self.db.execute("INSERT INTO instrumentos (code, nome) VALUES ('dor', 'EVA')")
        self.db.conn.commit()
        pid = self.db.scalar("SELECT id FROM participantes WHERE codigo = 'P91'")
        iid = self.db.scalar("SELECT id FROM instrumentos WHERE code = 'dor'")
        self.db.execute(
            "INSERT INTO coletas (participante_id, instrumento_id, valor) VALUES (?, ?, 5)",
            (pid, iid))
        self.db.conn.commit()
        with self.assertRaises(Exception):
            self.db.execute(
                "INSERT INTO coletas (participante_id, instrumento_id, valor) VALUES (?, ?, 7)",
                (pid, iid))
        self.db.conn.rollback()


class TestAMigracaoDeBancoAntigo(unittest.TestCase):
    """As tabelas novas precisam entrar num banco que já existe."""

    def test_um_banco_antigo_ganha_as_tabelas(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        caminho = Path(tmp.name) / "antigo.sqlite"
        velho = Database(caminho)
        velho.execute("CREATE TABLE articles (id INTEGER PRIMARY KEY, title TEXT)")
        velho.conn.commit()
        velho.close()

        novo = Database(caminho)
        self.addCleanup(novo.close)
        novo.migrate()
        tabelas = {r["name"] for r in novo.query(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        for nova in ("instrumentos", "protocolos", "momentos", "participantes", "coletas"):
            with self.subTest(tabela=nova):
                self.assertIn(nova, tabelas)


if __name__ == "__main__":
    unittest.main()
