#!/usr/bin/env python3
"""Testes da importação seletiva do Lattes.

    python3 -m unittest tests.test_lattes_seletivo -v

O erro caro aqui é importar o currículo de quem não foi pedido. Um Lattes
de professor titular traz décadas de produção; desfazer significa apagar
artigo do banco, um a um, sem saber ao certo quais vieram de onde. Por
isso o filtro casa por dois caminhos e a conferência existe.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_lattes  # noqa: E402
from lape.db import Database  # noqa: E402


def curriculo(nome: str, citacao: str, lattes_id: str,
              anos: dict[int, int]) -> str:
    artigos = []
    n = 0
    for ano, quantos in sorted(anos.items()):
        for _ in range(quantos):
            n += 1
            artigos.append(
                f'<ARTIGO-PUBLICADO><DADOS-BASICOS-DO-ARTIGO '
                f'TITULO-DO-ARTIGO="Ansiedade e exercício: estudo {lattes_id[:3]}-{n}" '
                f'ANO-DO-ARTIGO="{ano}" IDIOMA="Português" '
                f'DOI="10.1000/x.{lattes_id[:3]}.{n}" NATUREZA="COMPLETO" />'
                f'<DETALHAMENTO-DO-ARTIGO TITULO-DO-PERIODICO-OU-REVISTA="Revista X" '
                f'ISSN="12345678" />'
                f'<AUTORES NOME-COMPLETO-DO-AUTOR="{nome}" NOME-PARA-CITACAO="{citacao}" '
                f'ORDEM-DE-AUTORIA="1" /></ARTIGO-PUBLICADO>')
    return ('<?xml version="1.0" encoding="ISO-8859-1"?>'
            f'<CURRICULO-VITAE NUMERO-IDENTIFICADOR="{lattes_id}">'
            f'<DADOS-GERAIS NOME-COMPLETO="{nome}" '
            f'NOME-EM-CITACOES-BIBLIOGRAFICAS="{citacao}" />'
            '<PRODUCAO-BIBLIOGRAFICA><ARTIGOS-PUBLICADOS>'
            + "".join(artigos) +
            '</ARTIGOS-PUBLICADOS></PRODUCAO-BIBLIOGRAFICA></CURRICULO-VITAE>')


class BaseCurriculos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.tmp.name)
        (self.pasta / "lattes_alexandro_andrade.xml").write_text(
            curriculo("Alexandro Andrade", "ANDRADE, A.", "1111111111111111",
                      {ano: 2 for ano in range(2006, 2027)}), encoding="iso-8859-1")
        (self.pasta / "lattes_guilherme_vilarino.xml").write_text(
            curriculo("Guilherme Torres Vilarino", "VILARINO, G. T.", "2222222222222222",
                      {ano: 1 for ano in range(2016, 2027)}), encoding="iso-8859-1")
        # o currículo de alguém que NÃO foi pedido, e cujo arquivo não traz
        # o nome — só o conteúdo denuncia de quem é
        (self.pasta / "curriculo.xml").write_text(
            curriculo("Fulana de Tal Silva", "SILVA, F. T.", "3333333333333333",
                      {2020: 5}), encoding="iso-8859-1")

    def tearDown(self):
        self.tmp.cleanup()

    def arquivos(self):
        return ingest_lattes.discover_lattes_files(self.pasta)


class TestFiltro(BaseCurriculos):
    def nomes(self, escolhidos):
        return sorted(p.name for p in escolhidos)

    def test_acha_os_tres_sem_filtro(self):
        self.assertEqual(len(self.arquivos()), 3)

    def test_o_filtro_deixa_so_quem_foi_pedido(self):
        escolhidos = ingest_lattes.filtrar(
            self.arquivos(), ["Alexandro Andrade", "Guilherme Vilarino"])
        self.assertEqual(self.nomes(escolhidos),
                         ["lattes_alexandro_andrade.xml", "lattes_guilherme_vilarino.xml"])

    def test_casa_pelo_nome_de_dentro_quando_o_arquivo_nao_diz(self):
        # quem exporta do Lattes recebe um `curriculo.xml` sem nome nenhum
        escolhidos = ingest_lattes.filtrar(self.arquivos(), ["Fulana Silva"])
        self.assertEqual(self.nomes(escolhidos), ["curriculo.xml"])

    def test_sobrenome_sozinho_basta(self):
        escolhidos = ingest_lattes.filtrar(self.arquivos(), ["Vilarino"])
        self.assertEqual(self.nomes(escolhidos), ["lattes_guilherme_vilarino.xml"])

    def test_nome_que_nao_existe_nao_traz_ninguem(self):
        # o erro caro é o contrário: pedir uma pessoa e importar todas
        self.assertEqual(ingest_lattes.filtrar(self.arquivos(), ["Zoroastro"]), [])

    def test_lista_vazia_nao_filtra_nada(self):
        self.assertEqual(len(ingest_lattes.filtrar(self.arquivos(), [])), 3)

    def test_acento_e_caixa_nao_atrapalham(self):
        self.assertEqual(
            self.nomes(ingest_lattes.filtrar(self.arquivos(), ["ALEXANDRO ANDRADÉ"])),
            ["lattes_alexandro_andrade.xml"])


class TestConferencia(BaseCurriculos):
    def test_diz_o_que_traria_sem_gravar(self):
        resumo = ingest_lattes.confere(self.pasta / "lattes_alexandro_andrade.xml")
        self.assertEqual(resumo["de_quem"], "Alexandro Andrade")
        self.assertEqual(resumo["artigos"], 42)
        self.assertEqual(resumo["primeiro_ano"], 2006)
        self.assertEqual(resumo["ultimo_ano"], 2026)
        self.assertEqual(resumo["anos_com_producao"], 21)

    def test_a_conferencia_nao_toca_no_banco(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "t.sqlite")
            db.migrate()
            antes = db.scalar("SELECT COUNT(*) FROM articles")
            ingest_lattes.confere(self.pasta / "lattes_alexandro_andrade.xml")
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM articles"), antes)
            db.close()

    def test_a_serie_por_ano_vem_junto(self):
        resumo = ingest_lattes.confere(self.pasta / "lattes_guilherme_vilarino.xml")
        self.assertEqual(sorted(resumo["por_ano"]), list(range(2016, 2027)))


class TestImportacaoSeletiva(unittest.TestCase):
    def setUp(self):
        self.base = BaseCurriculos("run")
        self.base.setUp()
        self.pasta = self.base.pasta
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
        self.base.tearDown()

    def autores(self):
        return {linha["full_name"] for linha in self.db.dicts(
            "SELECT full_name FROM members")}

    def test_importa_so_os_pedidos(self):
        resultado = ingest_lattes.ingest_all(
            self.db, raw_dir=self.pasta, verbose=False,
            somente=["Alexandro Andrade", "Guilherme Vilarino"])
        self.assertEqual(sorted(resultado["de_quem"]),
                         ["Alexandro Andrade", "Guilherme Torres Vilarino"])
        self.assertNotIn("Fulana de Tal Silva", self.autores())

    def test_quem_nao_foi_pedido_nao_entra(self):
        ingest_lattes.ingest_all(self.db, raw_dir=self.pasta, verbose=False,
                                 somente=["Vilarino"])
        titulos = [t[0] for t in self.db.conn.execute("SELECT title FROM articles")]
        self.assertTrue(titulos)
        self.assertFalse(any("111-" in t for t in titulos), "entrou artigo do Andrade")
        self.assertFalse(any("333-" in t for t in titulos), "entrou artigo de quem não foi pedido")

    def test_a_serie_temporal_chega_inteira(self):
        # é isto que o painel esperava: anos distintos de produção
        ingest_lattes.ingest_all(self.db, raw_dir=self.pasta, verbose=False,
                                 somente=["Alexandro Andrade"])
        anos = {linha["year_published"] for linha in self.db.dicts(
            "SELECT DISTINCT year_published FROM articles WHERE year_published IS NOT NULL")}
        self.assertGreaterEqual(len(anos), 20)

    def test_pedir_ninguem_conhecido_nao_importa_todo_mundo(self):
        resultado = ingest_lattes.ingest_all(self.db, raw_dir=self.pasta, verbose=False,
                                             somente=["Zoroastro"])
        self.assertEqual(resultado["articles"], 0)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM articles"), 0)

    def test_arquivos_explicitos_ignoram_a_pasta(self):
        resultado = ingest_lattes.ingest_all(
            self.db, verbose=False,
            arquivos=[self.pasta / "lattes_guilherme_vilarino.xml"])
        self.assertEqual(resultado["de_quem"], ["Guilherme Torres Vilarino"])

    def test_o_lattes_nao_sobrescreve_o_que_o_laboratorio_digitou(self):
        from lape import ingest_excel
        ingest_excel.ingest_articles(self.db, [
            {"title": "Ansiedade e exercício: estudo 111-1", "authors": "Quem digitou",
             "status": "Em produção", "journal": "Revista digitada à mão"}])
        ingest_lattes.ingest_all(self.db, raw_dir=self.pasta, verbose=False,
                                 somente=["Alexandro Andrade"])
        revista = self.db.scalar(
            "SELECT journal FROM articles WHERE title LIKE '%estudo 111-1'")
        self.assertEqual(revista, "Revista digitada à mão")


if __name__ == "__main__":
    unittest.main(verbosity=2)
