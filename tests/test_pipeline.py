#!/usr/bin/env python3
"""Testes do pipeline do LAPE.

    python3 -m unittest discover -s tests -v

Nao acessam a rede: as consultas as bases bibliograficas sao substituidas
por respostas gravadas, o que mantem os testes rapidos e deterministicos.
"""
from __future__ import annotations

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_excel, ingest_lattes, metrics, report, sources  # noqa: E402
from lape.agents import curator, tracker  # noqa: E402
from lape.db import Database  # noqa: E402
from lape.mapping import build_column_map, resolve_sheet  # noqa: E402
from lape.util import (  # noqa: E402
    author_key, clean_text, parse_date, parse_datetime, split_authors, title_key,
)

WORKBOOK = ROOT / "data" / "raw" / "LAPE_Gestao_Indicadores_Cientificos_v3.xlsx"
LATTES_XML = ROOT / "tests" / "fixtures" / "curriculo_exemplo.xml"


def fresh_db() -> tuple[Database, tempfile.TemporaryDirectory]:
    tmp = tempfile.TemporaryDirectory()
    db = Database(Path(tmp.name) / "test.sqlite")
    db.migrate()
    return db, tmp


class TestNormalizacao(unittest.TestCase):
    def test_chave_de_autor_une_grafias(self):
        for name in ["Alexandro Andrade", "ANDRADE, A.", "Andrade, Alexandro",
                     "Andrade A.", "ANDRADE A"]:
            self.assertEqual(author_key(name), "andrade_a", name)
        for name in ["Guilherme Torres Vilarino", "VILARINO, G. T.", "Vilarino GT"]:
            self.assertEqual(author_key(name), "vilarino_gt", name)

    def test_chave_de_autor_preserva_sobrenomes_curtos(self):
        self.assertEqual(author_key("Jose Sa"), "sa_j")
        self.assertEqual(author_key("Wu"), "wu")

    def test_divisao_de_autores(self):
        self.assertEqual(split_authors("Loiane, Nayara, Vilarino, Andrade"),
                         ["Loiane", "Nayara", "Vilarino", "Andrade"])
        self.assertEqual(split_authors("ANDRADE, A., VILARINO, G. T."),
                         ["ANDRADE, A.", "VILARINO, G. T."])
        self.assertEqual(split_authors("Andrade, A.; Vilarino, G. T."),
                         ["Andrade, A.", "Vilarino, G. T."])
        self.assertEqual(split_authors(None), [])

    def test_datas(self):
        self.assertEqual(parse_date("12/03/2024"), "2024-03-12")
        self.assertEqual(parse_date("2024-03-12"), "2024-03-12")
        self.assertEqual(parse_date("mar/2024"), "2024-03-01")
        self.assertEqual(parse_date("2021"), "2021-01-01")
        self.assertEqual(parse_date(45000), "2023-03-15")
        self.assertEqual(parse_datetime("12/03/2024 14h30"), "2024-03-12 14:30")

    def test_valores_ausentes_do_pandas(self):
        import pandas as pd

        self.assertIsNone(parse_date(pd.NaT))
        self.assertIsNone(parse_datetime(pd.NaT))
        self.assertIsNone(clean_text(float("nan")))
        self.assertIsNone(parse_date(None))


class TestMapeamento(unittest.TestCase):
    def test_abas_reais(self):
        self.assertEqual(resolve_sheet("Pipeline de Artigos"), "articles")
        self.assertEqual(resolve_sheet("Tentativas de Submissão"), "submissions")
        self.assertEqual(resolve_sheet("Linhas de Pesquisa"), "research_lines")
        self.assertIsNone(resolve_sheet("Métricas"))
        self.assertIsNone(resolve_sheet("Como usar"))

    def test_colunas_reais(self):
        mapping = build_column_map("articles", [
            "ID", "Título", "Responsável", "Equipe", "Data de início",
            "Data da primeira versão", "Data versão final", "Revisão interna"])
        self.assertEqual(mapping["Título"], "title")
        self.assertEqual(mapping["Equipe"], "authors")
        self.assertEqual(mapping["Responsável"], "lead")
        self.assertEqual(mapping["Data de início"], "started_on")
        self.assertEqual(mapping["Data da primeira versão"], "version_1")


class TestPlanilhaReal(unittest.TestCase):
    """Le a planilha do laboratorio e confere com os valores que ela mesma calcula."""

    @classmethod
    def setUpClass(cls):
        if not WORKBOOK.exists():
            raise unittest.SkipTest(f"planilha nao encontrada: {WORKBOOK}")
        cls.db, cls._tmp = fresh_db()
        ingest_excel.ingest_all(cls.db, WORKBOOK.parent, verbose=False)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls._tmp.cleanup()

    def test_artigos_do_pipeline(self):
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM articles"), 19)
        self.assertEqual(
            self.db.scalar("SELECT title FROM articles WHERE internal_code = 'LAPE-02'")[:22],
            "Determinantes do dropo")

    def test_formato_largo_vira_uma_linha_por_tentativa(self):
        attempts = self.db.dicts(
            "SELECT s.attempt_no, s.journal, s.decision FROM submissions s"
            " JOIN articles a ON a.id = s.article_id WHERE a.internal_code = 'LAPE-15'"
            " ORDER BY s.attempt_no")
        self.assertEqual(len(attempts), 3)
        self.assertEqual(attempts[0]["decision"], "desk_reject")
        self.assertEqual(attempts[2]["journal"], "International Journal of Rheumatic Diseases")

    def test_blocos_de_tentativa_vazios_sao_ignorados(self):
        # 18 artigos x 3 blocos = 54 linhas lidas, mas so 5 tentativas reais
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM submissions"), 5)

    def test_status_derivado_das_submissoes(self):
        counts = dict(self.db.query(
            "SELECT status, COUNT(*) FROM articles GROUP BY status"))
        self.assertEqual(counts["submetido"], 3)
        self.assertEqual(counts["em_producao"], 16)

    def test_intervalos_batem_com_a_planilha(self):
        # a aba "Métricas" da planilha declara 12,5 dias entre recusa e nova submissao
        gaps = self.db.dicts("SELECT days_decision_to_resubmission FROM v_resubmission_gaps")
        media = sum(g["days_decision_to_resubmission"] for g in gaps) / len(gaps)
        self.assertEqual(len(gaps), 2)
        self.assertAlmostEqual(media, 12.5, places=2)

    def test_marcos_de_versao(self):
        marcos = self.db.dicts(
            "SELECT milestone FROM article_milestones m JOIN articles a ON a.id = m.article_id"
            " WHERE a.internal_code = 'LAPE-18' ORDER BY m.seq")
        codigos = [m["milestone"] for m in marcos]
        self.assertIn("versao_1", codigos)
        self.assertIn("versao_final", codigos)

    def test_equipe_por_primeiro_nome_gera_autoria(self):
        autores = self.db.dicts(
            "SELECT author_name FROM article_authors aa JOIN articles a ON a.id = aa.article_id"
            " WHERE a.internal_code = 'LAPE-02' ORDER BY aa.author_order")
        self.assertGreaterEqual(len(autores), 4)
        self.assertEqual(autores[0]["author_name"], "Loiane")  # responsavel vem primeiro

    def test_indicadores_completos(self):
        payload = metrics.build_payload(self.db)
        for bloco in ("overview", "research_lines", "in_progress", "submitted", "publications",
                      "members", "network", "timeline", "submissions", "agenda", "spatial",
                      "temporal", "quality", "discoveries"):
            self.assertIn(bloco, payload)
        self.assertEqual(payload["overview"]["n_articles"], 19)
        self.assertEqual(len(payload["submitted"]), 3)
        self.assertGreater(payload["network"]["n_edges"], 0)

    def test_painel_html_e_autocontido(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = report.render(metrics.build_payload(self.db), Path(tmp) / "index.html")
            html = out.read_text(encoding="utf-8")
        self.assertNotIn("__DATA__", html)
        self.assertNotIn("__SCRIPT__", html)
        self.assertNotIn("<script src=", html)   # nenhum JavaScript externo
        self.assertNotIn("stylesheet", html)     # nenhum CSS externo
        self.assertIn("LAPE", html)


class TestIdempotencia(unittest.TestCase):
    def test_reimportar_nao_duplica(self):
        if not WORKBOOK.exists():
            self.skipTest("planilha nao encontrada")
        db, tmp = fresh_db()
        try:
            ingest_excel.ingest_all(db, WORKBOOK.parent, verbose=False)
            primeiro = db.scalar("SELECT COUNT(*) FROM articles")
            ingest_excel.ingest_all(db, WORKBOOK.parent, verbose=False)
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM articles"), primeiro)
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM submissions"), 5)
        finally:
            db.close()
            tmp.cleanup()

    def test_fonte_externa_nao_sobrescreve_a_planilha(self):
        db, tmp = fresh_db()
        try:
            db.upsert("articles", {"title": "Estudo X", "title_key": "estudox",
                                   "journal": "Revista do laboratorio"}, conflict=("title_key",))
            db.upsert("articles", {"title": "Estudo X", "title_key": "estudox",
                                   "journal": "Outra revista", "doi": "10.1/z"},
                      conflict=("title_key",), fill_only=True)
            row = db.dicts("SELECT journal, doi FROM articles")[0]
            self.assertEqual(row["journal"], "Revista do laboratorio")
            self.assertEqual(row["doi"], "10.1/z")
        finally:
            db.close()
            tmp.cleanup()


class TestLattes(unittest.TestCase):
    def test_leitura_do_xml(self):
        db, tmp = fresh_db()
        try:
            resultado = ingest_lattes.ingest_file(db, LATTES_XML, verbose=False)
            self.assertEqual(resultado["articles"], 3)
            publicados = db.dicts(
                "SELECT title, year_published, doi FROM articles WHERE status = 'publicado'"
                " ORDER BY year_published DESC")
            self.assertEqual(len(publicados), 2)
            self.assertEqual(publicados[0]["year_published"], 2024)
            self.assertEqual(publicados[0]["doi"], "10.1016/j.psychsport.2024.102500")
            self.assertEqual(db.scalar("SELECT lattes_id FROM members WHERE name_key='andrade_a'"),
                             "1234567890123456")
            ordem = db.dicts(
                "SELECT author_order, author_name FROM article_authors aa"
                " JOIN articles a ON a.id = aa.article_id"
                " WHERE a.title LIKE 'Qualidade do sono%' ORDER BY author_order")
            self.assertEqual(ordem[0]["author_name"], "Danilo Reis Coimbra")
        finally:
            db.close()
            tmp.cleanup()


class TestAgenteRastreador(unittest.TestCase):
    """As bases externas sao substituidas por respostas gravadas."""

    OPENALEX_WORK = {
        "id": "https://openalex.org/W123", "doi": "https://doi.org/10.1000/abc",
        "title": "Exercise and anxiety in athletes", "publication_year": 2023,
        "publication_date": "2023-05-02", "cited_by_count": 42, "type": "article",
        "open_access": {"is_oa": True},
        "primary_location": {"source": {"display_name": "Sports Medicine", "issn_l": "0112-1642"},
                             "landing_page_url": "https://example.org/abc"},
        "authorships": [
            {"author": {"display_name": "Alexandro Andrade"},
             "institutions": [{"display_name": "UDESC", "country_code": "BR"}]},
            {"author": {"display_name": "Guilherme Torres Vilarino"}, "institutions": []},
        ],
    }

    def test_enriquecimento_preenche_doi_e_periodico(self):
        db, tmp = fresh_db()
        try:
            db.upsert("articles", {"title": "Exercise and anxiety in athletes",
                                   "title_key": title_key("Exercise and anxiety in athletes"),
                                   "status": "publicado"}, conflict=("title_key",))
            with mock.patch.object(sources, "crossref_by_doi", return_value=None), \
                 mock.patch.object(sources, "openalex_by_doi", return_value=None), \
                 mock.patch.object(sources, "crossref_search_title", return_value=None), \
                 mock.patch.object(sources, "openalex_search_title",
                                   return_value=sources._openalex_work(self.OPENALEX_WORK)):
                resultado = tracker.enrich(db, verbose=False)
            self.assertEqual(resultado["updated"], 1)
            row = db.dicts("SELECT doi, journal, year_published FROM articles")[0]
            self.assertEqual(row["doi"], "10.1000/abc")
            self.assertEqual(row["journal"], "Sports Medicine")
            self.assertEqual(row["year_published"], 2023)
        finally:
            db.close()
            tmp.cleanup()

    def test_citacoes_gravam_historico(self):
        db, tmp = fresh_db()
        try:
            db.upsert("articles", {"title": "A", "title_key": "a", "doi": "10.1000/abc",
                                   "status": "publicado"}, conflict=("title_key",))
            with mock.patch.object(sources, "openalex_by_doi",
                                   return_value=sources._openalex_work(self.OPENALEX_WORK)):
                resultado = tracker.citations(db, verbose=False)
            self.assertEqual(resultado["openalex"], 1)
            self.assertEqual(db.scalar("SELECT openalex_citations FROM articles"), 42)
            snapshot = db.dicts("SELECT source, citations FROM citation_snapshots")[0]
            self.assertEqual((snapshot["source"], snapshot["citations"]), ("openalex", 42))
        finally:
            db.close()
            tmp.cleanup()

    def test_descoberta_registra_sem_tocar_nos_artigos(self):
        db, tmp = fresh_db()
        try:
            db.member_id("Alexandro Andrade", orcid="0000-0002-0000-0000")
            with mock.patch.object(sources, "openalex_works_by_author",
                                   return_value=[sources._openalex_work(self.OPENALEX_WORK)]):
                resultado = tracker.discover(db, verbose=False)
            self.assertEqual(resultado["new"], 1)
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM articles"), 0)
            achado = db.dicts("SELECT title, citations, status FROM discoveries")[0]
            self.assertEqual(achado["status"], "pendente")
            self.assertEqual(achado["citations"], 42)
        finally:
            db.close()
            tmp.cleanup()

    def test_descoberta_ignora_artigo_ja_cadastrado(self):
        db, tmp = fresh_db()
        try:
            db.member_id("Alexandro Andrade", orcid="0000-0002-0000-0000")
            db.upsert("articles", {"title": "Exercise and anxiety in athletes",
                                   "title_key": title_key("Exercise and anxiety in athletes")},
                      conflict=("title_key",))
            with mock.patch.object(sources, "openalex_works_by_author",
                                   return_value=[sources._openalex_work(self.OPENALEX_WORK)]):
                resultado = tracker.discover(db, verbose=False)
            self.assertEqual(resultado["new"], 0)
        finally:
            db.close()
            tmp.cleanup()


class TestAgenteCurador(unittest.TestCase):
    def test_cadastro_aceita_nomes_de_coluna_da_planilha(self):
        db, tmp = fresh_db()
        try:
            resultado = curator.register(db, "articles", {
                "Título": "Treinamento mental e desempenho",
                "Autores": "Andrade; Vilarino",
                "Status": "Publicado", "Ano": 2025,
                "Periódico": "Motriz", "DOI": "10.1590/xyz",
                "Data de publicação": "2025-02-10",
            })
            self.assertEqual(resultado["written"], 1)
            artigo = resultado["records"][0]
            self.assertEqual(artigo["status"], "publicado")
            self.assertEqual(artigo["year_published"], 2025)
            self.assertEqual(artigo["authors"], "Andrade; Vilarino")
        finally:
            db.close()
            tmp.cleanup()

    def test_promocao_de_descoberta_vira_artigo(self):
        db, tmp = fresh_db()
        try:
            db.upsert("discoveries", {
                "source": "openalex", "title": "Sono e desempenho", "title_key": "sonoedesempenho",
                "authors": "Andrade; Vilarino", "journal": "Sleep Science", "year": 2024,
                "citations": 7, "doi": "10.1000/sono"}, conflict=("source", "title_key"))
            achado = db.dicts("SELECT id FROM discoveries")[0]["id"]
            resultado = curator.review_discovery(db, achado, "aceitar")
            self.assertEqual(resultado["status"], "aceito")
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM articles"), 1)
            self.assertEqual(db.scalar("SELECT openalex_citations FROM articles"), 7)
            self.assertEqual(db.scalar("SELECT status FROM discoveries"), "aceito")
        finally:
            db.close()
            tmp.cleanup()

    def test_descarte_de_descoberta(self):
        db, tmp = fresh_db()
        try:
            db.upsert("discoveries", {"source": "openalex", "title": "Homonimo",
                                      "title_key": "homonimo"}, conflict=("source", "title_key"))
            achado = db.dicts("SELECT id FROM discoveries")[0]["id"]
            curator.review_discovery(db, achado, "ignorar")
            self.assertEqual(db.scalar("SELECT status FROM discoveries"), "ignorado")
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM articles"), 0)
        finally:
            db.close()
            tmp.cleanup()

    def test_aceite_automatico_exige_dois_autores_conhecidos(self):
        db, tmp = fresh_db()
        try:
            db.member_id("Alexandro Andrade")
            db.upsert("discoveries", {"source": "openalex", "title": "So um conhecido",
                                      "title_key": "soumconhecido",
                                      "authors": "Alexandro Andrade; Fulano de Tal"},
                      conflict=("source", "title_key"))
            self.assertEqual(curator.auto_review(db)["accepted"], 0)
            db.member_id("Guilherme Torres Vilarino")
            db.upsert("discoveries", {"source": "openalex", "title": "Dois conhecidos",
                                      "title_key": "doisconhecidos",
                                      "authors": "Alexandro Andrade; Guilherme Torres Vilarino"},
                      conflict=("source", "title_key"))
            self.assertEqual(curator.auto_review(db)["accepted"], 1)
        finally:
            db.close()
            tmp.cleanup()

    def test_fusao_de_integrantes_por_variacao_de_grafia(self):
        db, tmp = fresh_db()
        try:
            ingest_excel.ingest_articles(db, [
                {"title": "Estudo 1", "authors": "Alexandro; Vilarino"},
                {"title": "Estudo 2", "authors": "Andrade; Vilarino"},
            ])
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM members"), 3)
            ingest_excel.ingest_members(db, [
                {"full_name": "Alexandro Andrade", "aliases": "Alexandro; Andrade"},
            ])
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM members"), 2)
            artigos = db.scalar(
                "SELECT COUNT(DISTINCT article_id) FROM article_authors aa"
                " JOIN members m ON m.id = aa.member_id WHERE m.full_name = 'Alexandro Andrade'")
            self.assertEqual(artigos, 2)
        finally:
            db.close()
            tmp.cleanup()


class TestRecusaRegistradaPelaArea(unittest.TestCase):
    """Registrar a recusa tem de mudar a situação do artigo, e só ela.

    O status vindo da planilha fica travado, para que reimportar não apague
    o que o laboratório escreveu à mão. Só que registrar a recusa pela área
    do integrante também é escrever à mão — e é a declaração mais recente.
    Sem destravar, a pessoa registrava a recusa, via a tentativa na lista, e
    o artigo continuava "submetido" para sempre.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "db.sqlite")
        self.db.migrate()
        # artigo vindo da planilha COM situação declarada: fica travado
        ingest_excel.ingest_articles(self.db, [
            {"title": "Ansiedade em atletas de base", "authors": "Cardoso",
             "status": "Submetido", "first_submission_on": "2026-01-10"},
        ])

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def situacao(self):
        return self.db.scalar("SELECT status FROM articles WHERE title = ?",
                              ("Ansiedade em atletas de base",))

    def test_a_planilha_continua_mandando(self):
        # reimportar a mesma aba de submissões não pode mexer no que a
        # coluna de situação declarou
        ingest_excel.ingest_submissions(self.db, [
            {"article": "Ansiedade em atletas de base", "journal": "Revista X",
             "submitted_on": "2026-01-10", "decision": "Rejeitado",
             "decision_on": "2026-04-02"},
        ])
        self.assertEqual(self.situacao(), "submetido")

    def test_recusa_registrada_pela_api_muda_a_situacao(self):
        curator.register(self.db, "submissions", {
            "Artigo": "Ansiedade em atletas de base",
            "Revista": "Revista X",
            "Data de submissão": "2026-01-10",
            "Decisão": "Rejeitado",
            "Data da decisão": "2026-04-02",
        })
        self.assertEqual(self.situacao(), "rejeitado")

    def test_aceite_registrado_pela_api_tambem_vale(self):
        curator.register(self.db, "submissions", {
            "Artigo": "Ansiedade em atletas de base",
            "Revista": "Revista X",
            "Data de submissão": "2026-01-10",
            "Decisão": "Aceito",
            "Data da decisão": "2026-05-20",
        })
        self.assertEqual(self.situacao(), "aceito")

    def test_envio_sem_parecer_nao_destrava(self):
        # "em avaliação" não é desfecho: não há o que declarar ainda
        curator.register(self.db, "submissions", {
            "Artigo": "Ansiedade em atletas de base",
            "Revista": "Revista X",
            "Data de submissão": "2026-06-01",
            "Tentativa": 2,
        })
        self.assertEqual(self.situacao(), "submetido")

    def test_a_recusa_avisa_quem_estiver_olhando(self):
        # é este registro que vira o empurrão do tempo real para o painel
        antes = int(self.db.scalar("SELECT COUNT(*) FROM change_log") or 0)
        curator.register(self.db, "submissions", {
            "Artigo": "Ansiedade em atletas de base",
            "Revista": "Revista X",
            "Data de submissão": "2026-01-10",
            "Decisão": "Rejeitado",
        })
        depois = self.db.dicts(
            "SELECT event FROM change_log ORDER BY id DESC LIMIT 1")
        self.assertGreater(int(self.db.scalar("SELECT COUNT(*) FROM change_log") or 0), antes)
        self.assertEqual(depois[0]["event"], "submissao.registrada")


class TestDesfechoDeTentativaExistente(unittest.TestCase):
    """Registrar o desfecho não pode criar uma submissão nova.

    Foi o que o laboratório reportou: para dizer que a terceira tentativa
    voltou negativa, era preciso preencher outra submissão inteira — revista
    e data de novo. Ou nascia uma tentativa duplicada, ou a pessoa desistia
    e o dado não entrava.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "db.sqlite")
        self.db.migrate()
        ingest_excel.ingest_articles(self.db, [
            {"title": "Fibromialgia e exercício", "authors": "Sampaio", "status": "Submetido"},
        ])
        curator.register(self.db, "submissions", {
            "Artigo": "Fibromialgia e exercício",
            "Revista": "International Journal of Rheumatic Diseases",
            "Data de submissão": "2026-02-14",
            "Tentativa": 3,
        })

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def tentativas(self):
        return self.db.dicts(
            "SELECT attempt_no, journal, submitted_on, decision, decision_on"
            " FROM submissions ORDER BY attempt_no")

    def test_so_o_desfecho_basta(self):
        # a chave é artigo + tentativa; o resto do registro fica onde está
        curator.register(self.db, "submissions", {
            "Artigo": "Fibromialgia e exercício",
            "Tentativa": 3,
            "Decisão": "Rejeitado",
            "Data da decisão": "2026-07-30",
        })
        linhas = self.tentativas()
        self.assertEqual(len(linhas), 1, "nasceu uma tentativa duplicada")
        self.assertEqual(linhas[0]["attempt_no"], 3)
        self.assertEqual(linhas[0]["decision"], "rejeitado")
        self.assertEqual(linhas[0]["decision_on"], "2026-07-30")

    def test_revista_e_data_de_envio_sobrevivem(self):
        curator.register(self.db, "submissions", {
            "Artigo": "Fibromialgia e exercício", "Tentativa": 3, "Decisão": "Rejeitado"})
        linha = self.tentativas()[0]
        self.assertEqual(linha["journal"], "International Journal of Rheumatic Diseases")
        self.assertEqual(linha["submitted_on"], "2026-02-14")

    def test_o_artigo_passa_a_rejeitado(self):
        curator.register(self.db, "submissions", {
            "Artigo": "Fibromialgia e exercício", "Tentativa": 3, "Decisão": "Rejeitado"})
        self.assertEqual(
            self.db.scalar("SELECT status FROM articles WHERE title = ?",
                           ("Fibromialgia e exercício",)),
            "rejeitado")

    def test_a_tentativa_seguinte_e_uma_submissao_nova(self):
        # reenviar a outro periódico é outro evento, e aí sim nasce linha
        curator.register(self.db, "submissions", {
            "Artigo": "Fibromialgia e exercício", "Tentativa": 3, "Decisão": "Rejeitado"})
        curator.register(self.db, "submissions", {
            "Artigo": "Fibromialgia e exercício", "Tentativa": 4,
            "Revista": "Pain Medicine", "Data de submissão": "2026-08-20"})
        linhas = self.tentativas()
        self.assertEqual([l["attempt_no"] for l in linhas], [3, 4])
        self.assertEqual(
            self.db.scalar("SELECT status FROM articles WHERE title = ?",
                           ("Fibromialgia e exercício",)),
            "submetido")


class TestJanelaDeAnalise(unittest.TestCase):
    def test_media_por_ano_usa_a_janela_completa(self):
        db, tmp = fresh_db()
        try:
            ano = dt.date.today().year
            for i in range(6):
                db.upsert("articles", {"title": f"T{i}", "title_key": f"t{i}",
                                       "status": "publicado", "year_published": ano - (i % 3),
                                       "published_on": f"{ano - (i % 3)}-06-01"},
                          conflict=("title_key",))
            pubs = metrics.publications_by_year(db, window=5)
            self.assertEqual(pubs["total_window"], 6)
            self.assertEqual(pubs["mean_per_year"], round(6 / 5, 2))
            self.assertEqual(len(pubs["series"]), 5)
            self.assertEqual(pubs["series"][-1]["year"], ano)
        finally:
            db.close()
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
