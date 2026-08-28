#!/usr/bin/env python3
"""Testes da planilha que se atualiza sozinha.

    python3 -m unittest tests.test_planilha -v

O laboratorio trabalha em Excel. Esta planilha e o espelho do banco naquele
formato, reescrita a cada cadastro. Dois riscos governam os testes:

  1. **Perder coluna no caminho.** Uma aba que sai vazia, ou um codigo que
     nao volta ao codigo certo, parece dado -- nao parece defeito. Por isso
     o teste central e a ida e volta: gerar o arquivo, reimportar e conferir
     que o banco novo tem o mesmo conteudo.
  2. **Reescrever demais.** Um arquivo por cadastro travaria o Excel de quem
     estivesse com ele aberto. O gatilho e o mesmo da copia de seguranca --
     o `change_log` -- e tem de respeitar o intervalo minimo.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_excel, mapping, planilha  # noqa: E402
from lape.db import Database  # noqa: E402
from lape.util import norm_key  # noqa: E402


INTEGRANTES = [
    {"full_name": "Marina Rossetto Cardoso", "role": "Coordenação",
     "email": "marina@udesc.br", "research_line": "Psicologia do Esporte"},
    {"full_name": "Nathália Bregantin Costa", "role": "Mestranda",
     "advisor": "Marina Rossetto Cardoso", "thesis_title": "Ansiedade competitiva",
     "thesis_kind": "Dissertação", "thesis_status": "Coleta"},
    {"full_name": "Pedro Lauth Meurer", "role": "Bolsista de IC",
     "advisor": "Marina Rossetto Cardoso"},
]
ARTIGOS = [
    {"title": "Atenção plena e desempenho em atletas de base",
     "authors": "Marina Rossetto Cardoso; Pedro Lauth Meurer",
     "status": "Publicado", "journal": "Journal of Sport Psychology",
     "year_published": 2024, "doi": "10.1000/lape.2024.0001"},
    {"title": "Ansiedade competitiva: revisão sistemática",
     "authors": "Nathália Bregantin Costa", "status": "Submetido",
     "first_submission_on": "2026-02-10"},
]
EVENTOS = [
    {"title": "Reunião semanal", "kind": "Reunião", "start_at": "2026-03-02",
     "participants": "Marina Rossetto Cardoso; Pedro Lauth Meurer"},
    # mesmo titulo, outra data: e o caso que quebrava a participação
    {"title": "Reunião semanal", "kind": "Reunião", "start_at": "2026-03-09",
     "participants": "Nathália Bregantin Costa"},
]


def banco(caminho: Path) -> Database:
    db = Database(caminho)
    db.migrate()
    ingest_excel.ingest_members(db, INTEGRANTES)
    ingest_excel.ingest_articles(db, ARTIGOS)
    ingest_excel.ingest_events(db, EVENTOS)
    db.conn.commit()
    return db


class TestConteudoDaPlanilha(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.db = banco(self.base / "db.sqlite")
        self.arquivo = planilha.gerar(self.db, destino=self.base / "p.xlsx")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def abas(self):
        import pandas as pd
        return pd.read_excel(self.arquivo, sheet_name=None, dtype=object, engine="openpyxl")

    def test_toda_aba_declarada_aparece(self):
        presentes = set(self.abas())
        for nome, _, _ in planilha.ABAS:
            self.assertIn(nome, presentes)
        self.assertIn("Instruções", presentes)

    def test_nenhuma_consulta_esta_quebrada(self):
        # a primeira versao engolia o erro e escrevia a aba vazia: uma
        # planilha com Publicações em branco parece um laboratório sem
        # produção, não um defeito
        for nome, cabecalhos, linhas in planilha.dados(self.db):
            self.assertTrue(cabecalhos, f"aba sem cabeçalho: {nome}")
        vistas = {nome: linhas for nome, _, linhas in planilha.dados(self.db)}
        self.assertEqual(len(vistas["Publicações"]), 2)
        self.assertEqual(len(vistas["Integrantes"]), 3)

    def test_a_primeira_aba_avisa_que_o_arquivo_e_reescrito(self):
        guia = self.abas()["Instruções"]
        texto = " ".join(str(v) for v in guia.to_numpy().ravel())
        self.assertIn("reescrita", texto)
        self.assertIn("Atualizada em", str(guia.columns) + texto)

    def test_codigos_viram_rotulos_legiveis(self):
        publicacoes = self.abas()["Publicações"]
        self.assertIn("Publicado", list(publicacoes["Status"]))
        integrantes = self.abas()["Integrantes"]
        self.assertIn("Coordenação", list(integrantes["Função"]))

    def test_booleanos_saem_como_sim_e_nao(self):
        autoria = self.abas()["Autoria"]
        self.assertTrue(set(autoria["Correspondente"].dropna()) <= {"Sim", "Não"})

    def test_a_planilha_de_entrada_nunca_e_tocada(self):
        # `data/raw/` é o que o laboratório digita; o espelho mora noutro lugar
        alvo = planilha.caminho(self.base / "db.sqlite")
        self.assertNotIn("raw", alvo.parts)
        self.assertTrue(alvo.name.endswith(".xlsx"))


class TestRotulosVoltam(unittest.TestCase):
    """Todo rótulo bonito tem de voltar ao mesmo código na reimportação.

    Um rótulo que não volta não dá erro: o campo simplesmente chega vazio,
    e o dado se perde sem ninguém ver.
    """

    MAPAS = {
        "status": mapping.STATUS_MAP,
        "decision": mapping.DECISION_MAP,
        "project_status": mapping.PROJECT_STATUS_MAP,
        "thesis_kind": mapping.THESIS_KIND_MAP,
        "thesis_status": mapping.THESIS_STATUS_MAP,
        "kind_evento": mapping.EVENT_KIND_MAP,
        "role": mapping.ROLE_MAP,
    }

    def test_cada_rotulo_volta_ao_seu_codigo(self):
        for grupo, rotulos in planilha.ROTULOS.items():
            mapa = self.MAPAS[grupo]
            for codigo, rotulo in rotulos.items():
                with self.subTest(grupo=grupo, rotulo=rotulo):
                    self.assertEqual(mapa.get(norm_key(rotulo)), codigo)

    def test_todo_grupo_de_rotulos_e_conferido(self):
        # um grupo novo sem mapa correspondente passaria despercebido
        self.assertEqual(set(planilha.ROTULOS), set(self.MAPAS))

    def test_sim_e_nao_sao_lidos_de_volta(self):
        from lape.util import to_bool
        self.assertEqual(to_bool(planilha.SIM_NAO[0]), 1)
        self.assertEqual(to_bool(planilha.SIM_NAO[1]), 0)


class TestIdaEVolta(unittest.TestCase):
    """Gerar, reimportar, conferir. É a prova de que nada se perdeu."""

    TABELAS = ("members", "articles", "article_authors", "submissions",
               "projects", "project_members", "events", "event_participants",
               "research_lines", "institutions", "rejection_reasons")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.origem = banco(self.base / "origem.sqlite")
        pasta = self.base / "raw"
        pasta.mkdir()
        planilha.gerar(self.origem, destino=pasta / "LAPE.xlsx")
        self.volta = Database(self.base / "volta.sqlite")
        self.volta.migrate()
        ingest_excel.ingest_all(self.volta, raw_dir=pasta, verbose=False)

    def tearDown(self):
        self.origem.close()
        self.volta.close()
        self.tmp.cleanup()

    def quantos(self, db, tabela):
        return db.scalar(f"SELECT COUNT(*) FROM {tabela}")

    def test_mesmas_quantidades_em_toda_tabela(self):
        for tabela in self.TABELAS:
            with self.subTest(tabela=tabela):
                self.assertEqual(self.quantos(self.origem, tabela),
                                 self.quantos(self.volta, tabela))

    def test_funcao_de_quem_orienta_sobrevive(self):
        # o defeito que este teste guarda: quem aparecia primeiro como
        # orientador de outra pessoa entrava no banco só com o nome, e a
        # linha de cadastro dela era engolida pelo atalho do cache --
        # a coordenadora acabava sem função nenhuma
        papel = self.volta.scalar(
            "SELECT role FROM members WHERE full_name = ?", ("Marina Rossetto Cardoso",))
        self.assertEqual(papel, "coordenacao")

    def test_presenca_nao_desaba_em_evento_de_titulo_repetido(self):
        # duas reuniões com o mesmo título: pelo título, toda a presença
        # cairia na primeira
        self.assertEqual(self.quantos(self.volta, "event_participants"),
                         self.quantos(self.origem, "event_participants"))
        por_evento = dict(self.volta.conn.execute(
            "SELECT event_id, COUNT(*) FROM event_participants GROUP BY 1").fetchall())
        self.assertEqual(len(por_evento), 2)

    def test_orientacao_e_tese_atravessam(self):
        pessoa = self.volta.dicts(
            "SELECT m.thesis_title, m.thesis_kind, m.thesis_status, o.full_name AS orientador"
            "  FROM members m LEFT JOIN members o ON o.id = m.advisor_id"
            " WHERE m.full_name = ?", ("Nathália Bregantin Costa",))[0]
        self.assertEqual(pessoa["thesis_kind"], "dissertacao")
        self.assertEqual(pessoa["thesis_status"], "coleta")
        self.assertEqual(pessoa["orientador"], "Marina Rossetto Cardoso")

    def test_autoria_mantem_a_ordem(self):
        autores = [r["author_name"] for r in self.volta.dicts(
            "SELECT aa.author_name FROM article_authors aa JOIN articles a ON a.id = aa.article_id"
            " WHERE a.title LIKE 'Atenção plena%' ORDER BY aa.author_order")]
        self.assertEqual(autores, ["Marina Rossetto Cardoso", "Pedro Lauth Meurer"])


class TestQuandoReescrever(unittest.TestCase):
    """O gatilho: cadastro novo escreve, cadastro parado não."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.db = banco(self.base / "db.sqlite")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_a_primeira_sempre_sai(self):
        feita = planilha.rodar(self.db, db_path=self.base / "db.sqlite")
        self.assertTrue(feita["gerou"])
        self.assertEqual(feita["motivo"], "primeira planilha")
        self.assertTrue(Path(feita["arquivo"]).exists())

    def test_logo_depois_nao_sai_de_novo(self):
        planilha.rodar(self.db, db_path=self.base / "db.sqlite")
        de_novo = planilha.rodar(self.db, db_path=self.base / "db.sqlite")
        self.assertFalse(de_novo["gerou"])
        self.assertIn("min atrás", de_novo["motivo"])

    def test_forcar_escreve_assim_mesmo(self):
        planilha.rodar(self.db, db_path=self.base / "db.sqlite")
        forcada = planilha.rodar(self.db, forcar=True, db_path=self.base / "db.sqlite")
        self.assertTrue(forcada["gerou"])

    def test_a_marca_guardada_e_a_do_change_log(self):
        # é assim que a próxima passagem sabe se houve cadastro novo
        feita = planilha.rodar(self.db, db_path=self.base / "db.sqlite")
        registrada = self.db.scalar(
            "SELECT rows_read FROM ingest_log WHERE source = 'planilha'"
            " ORDER BY id DESC LIMIT 1")
        self.assertEqual(registrada, feita["marca"])
        self.assertEqual(registrada, planilha.marca_atual(self.db))

    def test_o_resumo_conta_o_estado(self):
        planilha.rodar(self.db, db_path=self.base / "db.sqlite")
        resumo = planilha.resumo(self.db, db_path=self.base / "db.sqlite")
        self.assertTrue(resumo["existe"])
        self.assertGreater(resumo["bytes"], 0)
        self.assertIsNotNone(resumo["atualizada_em"])


class TestArquivoOcupado(unittest.TestCase):
    def test_troca_atomica_nao_deixa_arquivo_pela_metade(self):
        # a versão nova é escrita ao lado e só então trocada: se o processo
        # morre no meio, o que sobra é o arquivo velho inteiro
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            db = banco(base / "db.sqlite")
            try:
                alvo = base / "planilha" / "LAPE.xlsx"
                primeira = planilha.gerar(db, destino=alvo)
                tamanho = primeira.stat().st_size
                segunda = planilha.gerar(db, destino=alvo)
                self.assertEqual(primeira, segunda)
                self.assertGreaterEqual(segunda.stat().st_size, tamanho // 2)
                self.assertFalse(alvo.with_suffix(".novo.xlsx").exists())
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
