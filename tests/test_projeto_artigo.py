#!/usr/bin/env python3
"""Vínculo entre projeto e artigo, e o que ele puxa junto.

    python3 -m unittest tests.test_projeto_artigo -v

O pedido do Mateus: cadastrar um artigo e escolher o projeto de pesquisa
que o gerou -- e a equipe desse projeto (responsável e bolsistas) aparecer
sozinha, em vez de redigitada. E o caminho inverso: da aba de Projetos,
dizer a quais artigos aquele projeto já deu origem.

O que se guarda aqui:

  1. a aba de Artigos grava o vínculo (`project` -> `project_articles`),
     a aba de Projetos também (`articles_linked` -> `project_articles`),
     e as duas enxergam o que a outra gravou;
  2. a equipe do projeto (`v_projects.members`, `v_projects.coordinator`)
     é o que o navegador usa para preencher Autores e Responsável -- este
     módulo não decide isso (é a tela), só garante que o dado chega pronto;
  3. campo vazio é "não mexi nisto", nunca "desfaça o vínculo que já
     existia" -- a mesma regra que já valia para autoria;
  4. um nome de projeto ou título de artigo que não bate com nada
     cadastrado fica de fora, em silêncio: o sistema não inventa projeto
     nem artigo só porque alguém digitou errado.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_excel  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseProjetoArtigo(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "t.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()

    def projeto(self, **campos):
        ingest_excel.ingest_projects(self.db, [campos])
        self.db.conn.commit()
        return self.db.dicts("SELECT * FROM v_projects WHERE name = ?", (campos["name"],))[0]

    def artigo(self, **campos):
        ingest_excel.ingest_articles(self.db, [campos])
        self.db.conn.commit()
        return self.db.dicts("SELECT * FROM v_articles_full WHERE title = ?",
                             (campos["title"],))[0]


class TestDoArtigoParaOProjeto(BaseProjetoArtigo):
    """A aba de Artigos grava o vínculo, com o nome do projeto."""

    def test_escolher_o_projeto_liga_o_artigo_a_ele(self):
        self.projeto(name="Exercício e câncer de mama", coordinator="Maria Helena")
        a = self.artigo(title="Fadiga em pacientes oncológicas",
                        project="Exercício e câncer de mama")
        self.assertEqual(a["project"], "Exercício e câncer de mama")

    def test_o_projeto_tambem_enxerga_o_artigo(self):
        p = self.projeto(name="Exercício e câncer de mama", coordinator="Maria Helena")
        self.artigo(title="Fadiga em pacientes oncológicas",
                   project="Exercício e câncer de mama")
        de_novo = self.db.dicts("SELECT * FROM v_projects WHERE id = ?", (p["id"],))[0]
        self.assertEqual(de_novo["articles_linked"], "Fadiga em pacientes oncológicas")
        self.assertEqual(de_novo["n_articles"], 1)

    def test_projeto_que_nao_existe_nao_trava_o_cadastro_do_artigo(self):
        a = self.artigo(title="Artigo solto", project="Projeto que ninguém cadastrou")
        self.assertIsNone(a["project"])

    def test_campo_vazio_nao_desfaz_o_vinculo_que_ja_existia(self):
        self.projeto(name="Exercício e câncer de mama", coordinator="Maria Helena")
        self.artigo(title="Fadiga em pacientes oncológicas",
                   project="Exercício e câncer de mama")
        # regrava o MESMO artigo sem mandar "project" -- igual ao formulário
        # reenviando um campo que a pessoa não tocou
        a = self.artigo(title="Fadiga em pacientes oncológicas", notes="revisado")
        self.assertEqual(a["project"], "Exercício e câncer de mama")

    def test_dois_projetos_podem_apontar_pro_mesmo_artigo(self):
        # um artigo fruto de dois editais -- a aba de Artigos so oferece UM
        # seletor, mas o vinculo feito pela aba de Projetos nao se perde
        self.projeto(name="Projeto A", coordinator="Maria Helena")
        self.projeto(name="Projeto B", coordinator="Alexandro Andrade")
        self.artigo(title="Artigo de dois editais", project="Projeto A")
        self.projeto(name="Projeto B", articles_linked="Artigo de dois editais")
        ligados = self.db.scalar(
            "SELECT COUNT(*) FROM project_articles pa JOIN articles a ON a.id = pa.article_id"
            " WHERE a.title = ?", ("Artigo de dois editais",))
        self.assertEqual(ligados, 2)


class TestDoProjetoParaOArtigo(BaseProjetoArtigo):
    """A aba de Projetos grava o mesmo vínculo, pelo título do artigo."""

    def test_articles_linked_liga_um_artigo_ja_cadastrado(self):
        self.artigo(title="Fadiga em pacientes oncológicas")
        p = self.projeto(name="Exercício e câncer de mama", coordinator="Maria Helena",
                         articles_linked="Fadiga em pacientes oncológicas")
        self.assertEqual(p["articles_linked"], "Fadiga em pacientes oncológicas")

    def test_varios_artigos_separados_por_ponto_e_virgula(self):
        self.artigo(title="Artigo um")
        self.artigo(title="Artigo dois")
        p = self.projeto(name="Projeto com dois artigos", coordinator="Maria Helena",
                         articles_linked="Artigo um; Artigo dois")
        self.assertEqual(p["n_articles"], 2)

    def test_titulo_que_nao_bate_com_nenhum_artigo_fica_de_fora_em_silencio(self):
        p = self.projeto(name="Projeto solto", coordinator="Maria Helena",
                         articles_linked="Um título que não existe")
        self.assertEqual(p["n_articles"], 0)


class TestAEquipeQueATelaUsaPraPreencher(BaseProjetoArtigo):
    """`v_projects.members`/`coordinator` é o que o formulário de Artigos lê
    para preencher Autores e Responsável sozinho -- conferido aqui como
    contrato de dados, não como tela (isso é `test_web.py`)."""

    def test_o_coordenador_entra_na_lista_de_membros(self):
        p = self.projeto(name="Exercício e câncer de mama", coordinator="Maria Helena",
                         members="João Bolsista; Ana Bolsista")
        self.assertIn("Maria Helena", p["members"])
        self.assertIn("João Bolsista", p["members"])
        self.assertEqual(p["coordinator"], "Maria Helena")

    def test_projeto_sem_equipe_declarada_nao_quebra(self):
        p = self.projeto(name="Projeto recém-criado", coordinator="Maria Helena")
        self.assertEqual(p["members"], "Maria Helena")


if __name__ == "__main__":
    unittest.main()
