#!/usr/bin/env python3
"""Resolvers de `lape/db.py`: `institution_id`, quem transforma um nome de
planilha num id de linha do banco, criando a linha quando é preciso.

    python3 -m unittest tests.test_db -v

O que se guarda: `institution_id` não pode CRIAR uma instituição de novo só
porque a ingestão de MEMBROS não trouxe a cidade -- a aba "Instituições" já
tinha cadastrado aquela instituição, com cidade e país de verdade, e o
conflito (name, city) do upsert não batia com `city=None`. O resultado era
uma segunda linha, sem país nenhum informado, caindo no DEFAULT 'Brasil' do
schema -- uma universidade estrangeira virando brasileira, achado ao vivo na
lâmina "Pelo mundo" do mural (Universitat de Barcelona, University of
Birmingham, ambas com country='Brasil' na segunda linha).
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape.db import Database  # noqa: E402


def _abrir(caminho: Path) -> Database:
    db = Database(caminho)
    db.migrate()
    return db


class TestInstitutionId(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = _abrir(Path(self.tmp.name) / "db.sqlite")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)

    def test_cria_com_os_dados_completos_da_aba_instituicoes(self):
        iid = self.db.institution_id(
            "Universitat de Barcelona", "Barcelona",
            country="Espanha", latitude=41.3874, longitude=2.1686)
        linha = self.db.dicts("SELECT * FROM institutions WHERE id = ?", (iid,))[0]
        self.assertEqual(linha["country"], "Espanha")
        self.assertEqual(linha["city"], "Barcelona")

    def test_sem_cidade_acha_a_instituicao_ja_cadastrada_pelo_nome(self):
        """O caso real: a aba de Instituições cadastra com cidade e país;
        a aba de Membros, ao ligar uma pessoa à instituição, só manda o
        nome. As duas chamadas têm de resolver para a MESMA linha."""
        criado = self.db.institution_id(
            "Universitat de Barcelona", "Barcelona",
            country="Espanha", latitude=41.3874, longitude=2.1686)
        de_novo = self.db.institution_id("Universitat de Barcelona")
        self.assertEqual(de_novo, criado)
        # e o pais continua Espanha -- nao virou 'Brasil' na segunda chamada
        linha = self.db.dicts("SELECT * FROM institutions WHERE id = ?", (de_novo,))[0]
        self.assertEqual(linha["country"], "Espanha")

    def test_sem_cidade_e_sem_instituicao_previa_cria_uma_nova(self):
        iid = self.db.institution_id("Instituição Nova Sem Cadastro Prévio")
        self.assertIsNotNone(iid)
        linha = self.db.dicts("SELECT * FROM institutions WHERE id = ?", (iid,))[0]
        self.assertEqual(linha["name"], "Instituição Nova Sem Cadastro Prévio")

    def test_a_busca_por_nome_ignora_caixa(self):
        criado = self.db.institution_id(
            "University of Birmingham", "Birmingham",
            country="Reino Unido", latitude=52.4508, longitude=-1.9305)
        de_novo = self.db.institution_id("UNIVERSITY OF BIRMINGHAM")
        self.assertEqual(de_novo, criado)

    def test_duas_instituicoes_de_nomes_diferentes_nunca_se_confundem(self):
        a = self.db.institution_id("Universidade Federal de Santa Catarina", "Florianópolis",
                                   country="Brasil")
        b = self.db.institution_id("Universidade Federal do Rio Grande do Sul", "Porto Alegre",
                                   country="Brasil")
        self.assertNotEqual(a, b)

    def test_com_cidade_informada_o_conflito_continua_por_nome_e_cidade(self):
        """Duas instituições homônimas em cidades diferentes são registros
        distintos -- o comportamento de antes desta correção, que não muda
        quando a cidade É informada."""
        a = self.db.institution_id("Instituto Federal", "Cidade A", country="Brasil")
        b = self.db.institution_id("Instituto Federal", "Cidade B", country="Brasil")
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
