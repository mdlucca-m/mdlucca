#!/usr/bin/env python3
"""Testes da revisão sistemática: leitura das bases, união e triagem.

    python3 -m unittest tests.test_revisao -v

Numa revisão, errar em silêncio é a regra do jogo: um registro perdido na
importação, dois iguais que não se juntaram, uma decisão que sumiu — nada
disso dá erro na tela, e todos mudam o número que vai para a publicação.
Por isso os testes aqui perseguem o silêncio, não a exceção.
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import referencias, revisao  # noqa: E402
from lape.db import Database  # noqa: E402


RIS = """TY  - JOUR
TI  - Mood profiles and performance in elite handball players: a longitudinal
      study across a competitive season
AU  - Vilarino, G.T.
AU  - Andrade, A.
JO  - Journal of Sports Sciences
PY  - 2023
VL  - 41
SP  - 655
EP  - 663
DO  - https://doi.org/10.1080/02640414.2023.1234567
SN  - 0264-0414
KW  - POMS
KW  - team sports
AB  - The purpose of this study was to examine mood profiles in elite handball
      players across a season.
ER  -

TY  - JOUR
TI  - Anxiety and mood in youth handball
AU  - Silva, M.
PY  - 2021
DO  - 10.1177/00315125211000001
ER  -
"""

NBIB = """PMID- 36789012
DP  - 2023 Apr
TI  - Profile of mood states in handball athletes: a systematic review and
      meta-analysis.
AB  - BACKGROUND: Mood states matter. OBJECTIVE: To synthesise evidence.
FAU - Vilarino, Guilherme Torres
AU  - Vilarino GT
FAU - Andrade, Alexandro
AU  - Andrade A
LA  - eng
JT  - International journal of sports medicine
IS  - 1439-3964 (Electronic)
LID - 10.1055/a-2000-1234 [doi]
MH  - Handball
"""

BIBTEX = """@article{vilarino2023,
  author = {Guilherme Torres Vilarino and Alexandro Andrade},
  title = {Mood profiles and performance in elite handball players},
  journal = {Journal of Sports Sciences},
  year = {2023},
  doi = {10.1080/02640414.2023.1234567},
  abstract = {A study of {POMS} in handball}
}
"""

RAYYAN = (
    'key,title,authors,journal,year,url,notes,abstract\n'
    '1,"Mood profiles and performance in elite handball players",'
    '"Vilarino G.T. and Andrade A.","Journal of Sports Sciences",2023,'
    'https://doi.org/10.1080/02640414.2023.1234567,'
    '"RAYYAN-INCLUSION: {""Guilherme""=>""Included"",""Ana""=>""Included""} '
    '| RAYYAN-LABELS: POMS, handebol","Mood."\n'
    '2,"Yoga for office workers","Souza R.","Other Journal",2019,,'
    '"RAYYAN-INCLUSION: {""Guilherme""=>""Excluded"",""Ana""=>""Excluded""} '
    '| RAYYAN-EXCLUSION-REASONS: população errada","Not handball."\n'
    '3,"Anxiety and mood in youth handball","Silva M.","Perceptual and Motor Skills",2021,,'
    '"RAYYAN-INCLUSION: {""Guilherme""=>""Included"",""Ana""=>""Excluded""}","Youth."\n'
)


class TestLeituraRIS(unittest.TestCase):
    def setUp(self):
        self.regs = referencias.ler(RIS, "scopus.ris")

    def test_um_registro_por_entrada(self):
        self.assertEqual(len(self.regs), 2)

    def test_titulo_continuado_nao_e_cortado(self):
        # linha continuada é a regra em título e resumo longos; perder a
        # continuação corta o texto no meio sem avisar
        self.assertIn("longitudinal study across", self.regs[0]["title"])
        self.assertIn("across a season", self.regs[0]["abstract"])

    def test_autores_viram_uma_lista(self):
        self.assertEqual(self.regs[0]["authors"], "Vilarino, G.T.; Andrade, A.")

    def test_paginas_se_juntam(self):
        self.assertEqual(self.regs[0]["pages"], "655-663")

    def test_doi_perde_o_prefixo_de_endereco(self):
        self.assertEqual(self.regs[0]["doi"], "10.1080/02640414.2023.1234567")

    def test_palavras_chave_se_acumulam(self):
        self.assertEqual(self.regs[0]["keywords"], "POMS; team sports")


class TestLeituraMedline(unittest.TestCase):
    def setUp(self):
        self.reg = referencias.ler(NBIB, "pubmed.nbib")[0]

    def test_autor_nao_sai_duplicado(self):
        # FAU é o nome por extenso e AU a forma abreviada, no mesmo registro:
        # juntar os dois duplicaria cada autor
        self.assertEqual(self.reg["authors"],
                         "Vilarino, Guilherme Torres; Andrade, Alexandro")

    def test_doi_escondido_no_lid(self):
        self.assertEqual(self.reg["doi"], "10.1055/a-2000-1234")

    def test_issn_sem_o_qualificador(self):
        self.assertEqual(self.reg["issn"], "1439-3964")

    def test_ano_sai_da_data_de_publicacao(self):
        self.assertEqual(self.reg["year"], 2023)

    def test_link_da_pubmed_pelo_pmid(self):
        self.assertEqual(self.reg["url"], "https://pubmed.ncbi.nlm.nih.gov/36789012/")


class TestLeituraBibTeX(unittest.TestCase):
    def setUp(self):
        self.reg = referencias.ler(BIBTEX, "zotero.bib")[0]

    def test_autores_separados_por_and(self):
        self.assertEqual(self.reg["authors"],
                         "Guilherme Torres Vilarino; Alexandro Andrade")

    def test_chaves_de_agrupamento_somem_do_texto(self):
        self.assertEqual(self.reg["abstract"], "A study of POMS in handball")

    def test_campos_basicos(self):
        self.assertEqual(self.reg["year"], 2023)
        self.assertEqual(self.reg["doi"], "10.1080/02640414.2023.1234567")


class TestFormatoPeloConteudo(unittest.TestCase):
    """A extensão mente: a PubMed entrega MEDLINE em .txt."""

    def test_medline_disfarcado_de_txt(self):
        self.assertEqual(referencias.formato_de("busca.txt", NBIB), "nbib")

    def test_ris_disfarcado_de_txt(self):
        self.assertEqual(referencias.formato_de("busca.txt", RIS), "ris")

    def test_bibtex_disfarcado_de_txt(self):
        self.assertEqual(referencias.formato_de("busca.txt", BIBTEX), "bibtex")

    def test_extensao_conhecida_manda(self):
        self.assertEqual(referencias.formato_de("x.ris", RIS), "ris")

    def test_formato_inventado_e_recusado(self):
        with self.assertRaises(ValueError):
            referencias.ler("qualquer coisa", "x.doc", formato="docx")


class TestDecisoesDoRayyan(unittest.TestCase):
    """A triagem já feita é a única coisa que prende alguém à ferramenta."""

    def setUp(self):
        self.regs = referencias.ler(RAYYAN, "rayyan.csv")

    def test_decisoes_de_cada_pessoa(self):
        self.assertEqual(self.regs[0]["rayyan"]["decisoes"],
                         {"Guilherme": "incluir", "Ana": "incluir"})

    def test_divergencia_e_preservada(self):
        self.assertEqual(self.regs[2]["rayyan"]["decisoes"],
                         {"Guilherme": "incluir", "Ana": "excluir"})

    def test_etiquetas_e_motivos(self):
        self.assertEqual(self.regs[0]["rayyan"]["etiquetas"], ["POMS", "handebol"])
        self.assertEqual(self.regs[1]["rayyan"]["motivos"], ["população errada"])

    def test_doi_vem_do_link(self):
        # o Rayyan não tem coluna de DOI: põe o doi.org na coluna de link
        self.assertEqual(self.regs[0]["doi"], "10.1080/02640414.2023.1234567")

    def test_registro_sem_rayyan_nao_ganha_campo(self):
        limpo = referencias.ler("title,year\n\"Um artigo\",2020\n", "x.csv")[0]
        self.assertIsNone(limpo["rayyan"])


class TestUniaoDeRegistros(unittest.TestCase):
    def chaves(self, **campos):
        return revisao.chaves_de_uniao(campos)

    def test_o_mesmo_estudo_com_e_sem_doi_se_encontra(self):
        # o defeito que este teste guarda: com uma chave só, o registro da
        # Scopus (com DOI) e o do Rayyan (sem) passavam por dois trabalhos,
        # a equipe lia o mesmo resumo duas vezes e o PRISMA jurava que eram
        # dois
        com = self.chaves(title="Anxiety and mood in youth handball", year=2021,
                          doi="10.1177/00315125211000001")
        sem = self.chaves(title="Anxiety and mood in youth handball", year=2021)
        self.assertTrue(set(com) & set(sem), "as duas formas do mesmo estudo não se cruzam")

    def test_titulo_com_acento_e_pontuacao_normaliza(self):
        a = self.chaves(title="Atenção plena: um ensaio!", year=2024)
        b = self.chaves(title="ATENCAO PLENA - UM ENSAIO", year=2024)
        self.assertTrue(set(a) & set(b))

    def test_mesmo_titulo_em_anos_diferentes_nao_se_juntam(self):
        # o resumo de congresso e o artigo saem com o mesmo título
        a = self.chaves(title="Mood in handball", year=2022)
        b = self.chaves(title="Mood in handball", year=2023)
        self.assertFalse(set(a) & set(b))

    def test_registro_sem_titulo_e_sem_doi_nao_ganha_chave(self):
        self.assertEqual(self.chaves(title=None), [])


class TestImportacao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.rev = revisao.criar(self.db, "handebol-humor",
                                 "Perfil de humor em atletas de handebol",
                                 reviewers_needed=2)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def importar_tudo(self):
        return [revisao.importar(self.db, self.rev, texto, nome)
                for texto, nome in ((RIS, "scopus.ris"), (NBIB, "pubmed.nbib"),
                                    (RAYYAN, "rayyan.csv"))]

    def sobreviventes(self):
        return self.db.dicts("SELECT * FROM v_refs WHERE duplicate_of IS NULL ORDER BY id")

    def test_a_revisao_nasce_com_motivos_de_exclusao(self):
        quantos = self.db.scalar(
            "SELECT COUNT(*) FROM exclusion_reasons WHERE review_id = ?", (self.rev,))
        self.assertEqual(quantos, len(revisao.MOTIVOS_PADRAO))

    def test_cada_base_entra_e_os_repetidos_se_juntam(self):
        self.importar_tudo()
        self.assertEqual(len(self.sobreviventes()), 4)   # 6 lidos, 2 repetidos
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM refs WHERE duplicate_of IS NOT NULL"), 2)

    def test_reimportar_o_mesmo_arquivo_nao_duplica(self):
        # numa revisão a mesma busca é refeita várias vezes até ficar boa
        revisao.importar(self.db, self.rev, RIS, "scopus.ris")
        antes = len(self.sobreviventes())
        de_novo = revisao.importar(self.db, self.rev, RIS, "scopus.ris")
        self.assertEqual(de_novo["novos"], 0)
        self.assertEqual(de_novo["duplicados"], 2)
        self.assertEqual(len(self.sobreviventes()), antes)

    def test_duplicado_nao_e_apagado(self):
        # o PRISMA precisa saber quantos foram removidos, e união errada
        # tem de poder ser desfeita
        self.importar_tudo()
        repetido = self.db.dicts(
            "SELECT duplicate_of FROM refs WHERE duplicate_of IS NOT NULL")[0]
        self.assertIsNotNone(repetido["duplicate_of"])

    def test_a_triagem_do_rayyan_chega_com_nome(self):
        self.importar_tudo()
        votos = self.db.dicts(
            "SELECT m.full_name AS quem, s.decision FROM screenings s"
            "  JOIN members m ON m.id = s.member_id ORDER BY quem, s.decision")
        self.assertTrue(votos)
        self.assertEqual({v["quem"] for v in votos}, {"Ana", "Guilherme"})

    def test_a_triagem_sobrevive_ao_registro_ser_repetido(self):
        # o defeito que este teste guarda: quem exportasse do Rayyan junto
        # com as buscas perdia a triagem justamente dos estudos que as duas
        # fontes tinham -- sem erro nenhum na tela
        self.importar_tudo()
        mood = [r for r in self.sobreviventes() if r["title"].startswith("Mood profiles")][0]
        self.assertEqual(mood["n_incluir"], 2)
        self.assertEqual(mood["decision"], "incluir")

    def test_a_base_e_reconhecida_pelo_nome_do_arquivo(self):
        self.importar_tudo()
        bases = {r["base"] for r in self.db.dicts(
            "SELECT base FROM review_searches WHERE review_id = ?", (self.rev,))}
        self.assertEqual(bases, {"Scopus", "PubMed", "Rayyan"})


class TestConsolidacao(unittest.TestCase):
    """A decisão da equipe é derivada, nunca digitada."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.rev = revisao.criar(self.db, "r", "Revisão", reviewers_needed=2)
        revisao.importar(self.db, self.rev, RIS, "scopus.ris")
        self.ref = self.db.scalar("SELECT id FROM refs ORDER BY id LIMIT 1")
        self.ana = self.db.member_id("Ana Souza")
        self.beto = self.db.member_id("Beto Lima")
        self.chefe = self.db.member_id("Carla Árbitra")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def estado(self):
        return self.db.dicts("SELECT * FROM v_refs WHERE id = ?", (self.ref,))[0]

    def test_uma_decisao_so_nao_fecha_quando_sao_precisas_duas(self):
        resultado = revisao.decidir(self.db, self.ref, self.ana, "incluir")
        self.assertEqual(resultado["faltam"], 1)
        self.assertIsNone(self.estado()["decision"])

    def test_duas_iguais_fecham(self):
        revisao.decidir(self.db, self.ref, self.ana, "incluir")
        revisao.decidir(self.db, self.ref, self.beto, "incluir")
        self.assertEqual(self.estado()["decision"], "incluir")

    def test_divergencia_vira_conflito_e_nao_maioria(self):
        # incluir por engano custa uma leitura; excluir por engano custa um
        # estudo. Empate não se resolve no voto.
        revisao.decidir(self.db, self.ref, self.ana, "incluir")
        resultado = revisao.decidir(self.db, self.ref, self.beto, "excluir")
        self.assertTrue(resultado["conflito"])
        self.assertIsNone(self.estado()["decision"])
        self.assertEqual(len(revisao.conflitos(self.db, self.rev)), 1)

    def test_na_duvida_sobe_para_texto_completo(self):
        revisao.decidir(self.db, self.ref, self.ana, "talvez")
        revisao.decidir(self.db, self.ref, self.beto, "talvez")
        self.assertEqual(self.estado()["decision"], "incluir")

    def test_a_pessoa_pode_mudar_de_ideia(self):
        revisao.decidir(self.db, self.ref, self.ana, "incluir")
        revisao.decidir(self.db, self.ref, self.ana, "excluir")
        self.assertEqual(self.estado()["n_triagens"], 1)
        self.assertEqual(self.estado()["n_incluir"], 0)

    def test_revisao_de_uma_pessoa_so_nunca_tem_conflito(self):
        sozinha = revisao.criar(self.db, "solo", "Escopo", reviewers_needed=1)
        revisao.importar(self.db, sozinha, RIS, "scopus.ris")
        ref = self.db.scalar("SELECT id FROM refs WHERE review_id = ? LIMIT 1", (sozinha,))
        revisao.decidir(self.db, ref, self.ana, "incluir")
        self.assertEqual(self.db.scalar("SELECT decision FROM refs WHERE id = ?", (ref,)),
                         "incluir")

    def test_arbitragem_decide_sem_apagar_a_divergencia(self):
        revisao.decidir(self.db, self.ref, self.ana, "incluir")
        revisao.decidir(self.db, self.ref, self.beto, "excluir")
        revisao.arbitrar(self.db, self.ref, self.chefe, "excluir")
        self.assertEqual(self.estado()["decision"], "excluir")
        # os votos originais continuam lá: é deles que sai a concordância
        self.assertEqual(self.db.scalar(
            "SELECT COUNT(*) FROM screenings WHERE ref_id = ?", (self.ref,)), 3)

    def test_decisao_inventada_e_recusada(self):
        with self.assertRaises(ValueError):
            revisao.decidir(self.db, self.ref, self.ana, "quem sabe")


class TestFilaAsCegas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.rev = revisao.criar(self.db, "r", "Revisão", reviewers_needed=2)
        revisao.importar(self.db, self.rev, RIS, "scopus.ris")
        self.ana = self.db.member_id("Ana Souza")
        self.beto = self.db.member_id("Beto Lima")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_cada_um_anda_no_proprio_ritmo(self):
        ref = revisao.fila(self.db, self.rev, self.ana)[0]["id"]
        revisao.decidir(self.db, ref, self.ana, "incluir")
        self.assertNotIn(ref, [r["id"] for r in revisao.fila(self.db, self.rev, self.ana)])
        self.assertIn(ref, [r["id"] for r in revisao.fila(self.db, self.rev, self.beto)])

    def test_a_fila_nao_traz_duplicado(self):
        revisao.importar(self.db, self.rev, RIS, "scopus.ris")   # tudo repetido
        ids = [r["id"] for r in revisao.fila(self.db, self.rev, self.ana)]
        repetidos = [r["id"] for r in self.db.dicts(
            "SELECT id FROM refs WHERE duplicate_of IS NOT NULL")]
        self.assertFalse(set(ids) & set(repetidos))

    def test_a_fila_traz_o_que_e_preciso_para_decidir(self):
        primeiro = revisao.fila(self.db, self.rev, self.ana)[0]
        for campo in ("title", "abstract", "authors", "journal", "year", "doi"):
            self.assertIn(campo, primeiro)


class TestEtapasEPrisma(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.rev = revisao.criar(self.db, "r", "Revisão", reviewers_needed=1)
        revisao.importar(self.db, self.rev, RIS, "scopus.ris")
        revisao.importar(self.db, self.rev, NBIB, "pubmed.nbib")
        self.ana = self.db.member_id("Ana Souza")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_o_prisma_conta_do_banco(self):
        p = revisao.prisma(self.db, self.rev)
        self.assertEqual(p["identificados"], 3)
        self.assertEqual(p["triados"], 3)
        self.assertEqual(p["pendentes"], 3)

    def test_a_etapa_avanca_so_com_o_que_foi_incluido(self):
        refs = revisao.fila(self.db, self.rev, self.ana)
        revisao.decidir(self.db, refs[0]["id"], self.ana, "incluir")
        motivo = self.db.scalar(
            "SELECT id FROM exclusion_reasons WHERE review_id = ? AND code = 'populacao'",
            (self.rev,))
        revisao.decidir(self.db, refs[1]["id"], self.ana, "excluir", reason_id=motivo)
        passou = revisao.avancar_etapa(self.db, self.rev)
        self.assertEqual(passou["para_texto_completo"], 1)
        self.assertEqual(self.db.scalar(
            "SELECT stage FROM refs WHERE id = ?", (refs[0]["id"],)), "texto_completo")

    def test_o_que_sobe_de_etapa_volta_a_ser_indeciso(self):
        # a decisão de título e resumo não vale como decisão de texto completo
        refs = revisao.fila(self.db, self.rev, self.ana)
        revisao.decidir(self.db, refs[0]["id"], self.ana, "incluir")
        revisao.avancar_etapa(self.db, self.rev)
        self.assertIsNone(self.db.scalar(
            "SELECT decision FROM refs WHERE id = ?", (refs[0]["id"],)))

    def test_o_ciclo_inteiro_chega_a_incluido(self):
        refs = revisao.fila(self.db, self.rev, self.ana)
        revisao.decidir(self.db, refs[0]["id"], self.ana, "incluir")
        revisao.avancar_etapa(self.db, self.rev)
        revisao.decidir(self.db, refs[0]["id"], self.ana, "incluir")
        revisao.fechar_texto_completo(self.db, self.rev)
        p = revisao.prisma(self.db, self.rev)
        self.assertEqual(p["incluidos"], 1)

    def test_os_motivos_de_exclusao_sao_contados(self):
        refs = revisao.fila(self.db, self.rev, self.ana)
        motivo = self.db.scalar(
            "SELECT id FROM exclusion_reasons WHERE review_id = ? AND code = 'populacao'",
            (self.rev,))
        revisao.decidir(self.db, refs[0]["id"], self.ana, "excluir", reason_id=motivo)
        p = revisao.prisma(self.db, self.rev)
        self.assertEqual(p["motivos"][0]["motivo"], "População não elegível")
        self.assertEqual(p["motivos"][0]["n"], 1)


class TestConcordancia(unittest.TestCase):
    """Kappa: a concordância bruta engana quando quase tudo é excluído."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.rev = revisao.criar(self.db, "r", "Revisão", reviewers_needed=2)
        linhas = "".join(
            f"TY  - JOUR\nTI  - Estudo número {i}\nPY  - 2020\nER  -\n\n" for i in range(20))
        revisao.importar(self.db, self.rev, linhas, "busca.ris")
        self.ana = self.db.member_id("Ana Souza")
        self.beto = self.db.member_id("Beto Lima")
        self.refs = [r["id"] for r in self.db.dicts("SELECT id FROM refs ORDER BY id")]

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_sem_par_triado_nao_se_inventa_numero(self):
        resultado = revisao.concordancia(self.db, self.rev, self.ana, self.beto)
        self.assertEqual(resultado["n"], 0)
        self.assertIsNone(resultado["kappa"])

    def test_concordancia_total(self):
        for ref in self.refs[:10]:
            revisao.decidir(self.db, ref, self.ana, "excluir")
            revisao.decidir(self.db, ref, self.beto, "excluir")
        for ref in self.refs[10:]:
            revisao.decidir(self.db, ref, self.ana, "incluir")
            revisao.decidir(self.db, ref, self.beto, "incluir")
        resultado = revisao.concordancia(self.db, self.rev, self.ana, self.beto)
        self.assertEqual(resultado["n"], 20)
        self.assertEqual(resultado["concordancia"], 1.0)
        self.assertEqual(resultado["kappa"], 1.0)

    def test_kappa_desconta_o_acaso(self):
        # as duas excluem quase tudo: 90% de concordância bruta, e um kappa
        # que revela que boa parte disso foi acaso
        for i, ref in enumerate(self.refs):
            revisao.decidir(self.db, ref, self.ana, "excluir" if i < 18 else "incluir")
            revisao.decidir(self.db, ref, self.beto, "excluir" if i < 16 else "incluir")
        resultado = revisao.concordancia(self.db, self.rev, self.ana, self.beto)
        self.assertEqual(resultado["concordancia"], 0.9)
        self.assertLess(resultado["kappa"], resultado["concordancia"])
        self.assertIn(resultado["leitura"],
                      ("leve", "razoável", "moderada", "substancial", "quase perfeita"))


class TestNomesUnicosNosModulos(unittest.TestCase):
    """Duas funções com o mesmo nome no mesmo arquivo: a segunda apaga a primeira.

    Aconteceu: `_chave` normalizava cabeçalho de CSV, e uma `_chave` nova
    para gerar chave de BibTeX tomou o nome. O módulo continuou importando
    sem erro; o que quebrou foi a leitura de CSV, longe dali.
    """

    def test_nenhum_modulo_define_o_mesmo_nome_duas_vezes(self):
        import ast

        pasta = ROOT / "scripts" / "lape"
        for arquivo in sorted(pasta.rglob("*.py")):
            arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
            vistos: dict[str, int] = {}
            for no in arvore.body:
                if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    with self.subTest(arquivo=arquivo.name, nome=no.name):
                        self.assertNotIn(
                            no.name, vistos,
                            f"{arquivo.name}: '{no.name}' definido na linha "
                            f"{vistos.get(no.name)} e de novo na {no.lineno}")
                    vistos[no.name] = no.lineno


class TestDuplicadosNaTela(unittest.TestCase):
    """União automática erra dos dois lados, e os dois erros são invisíveis."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.rev = revisao.criar(self.db, "r", "Revisão", reviewers_needed=1)
        revisao.importar(self.db, self.rev, RIS, "scopus.ris")
        revisao.importar(self.db, self.rev, RIS, "wos.ris")     # tudo repetido

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_a_uniao_mostra_a_evidencia(self):
        grupos = revisao.duplicados(self.db, self.rev)
        self.assertEqual(len(grupos), 2)
        for grupo in grupos:
            for repetido in grupo["repetidos"]:
                self.assertIn("DOI", repetido["casou_por"])

    def test_separar_devolve_a_referencia_para_a_fila(self):
        repetido = self.db.scalar("SELECT id FROM refs WHERE duplicate_of IS NOT NULL LIMIT 1")
        revisao.separar(self.db, repetido)
        linha = self.db.dicts("SELECT duplicate_of, stage FROM refs WHERE id = ?",
                              (repetido,))[0]
        self.assertIsNone(linha["duplicate_of"])
        self.assertEqual(linha["stage"], "titulo_resumo")

    def test_separar_o_que_nao_esta_unido_e_recusado(self):
        sozinha = self.db.scalar("SELECT id FROM refs WHERE duplicate_of IS NULL LIMIT 1")
        with self.assertRaises(ValueError):
            revisao.separar(self.db, sozinha)

    def test_unir_a_mao_o_que_a_chave_nao_pegou(self):
        a, b = [r["id"] for r in self.db.dicts(
            "SELECT id FROM refs WHERE duplicate_of IS NULL ORDER BY id")][:2]
        revisao.unir(self.db, b, a)
        self.assertEqual(self.db.scalar("SELECT duplicate_of FROM refs WHERE id = ?", (b,)), a)

    def test_nao_se_une_uma_referencia_a_si_mesma(self):
        sozinha = self.db.scalar("SELECT id FROM refs WHERE duplicate_of IS NULL LIMIT 1")
        with self.assertRaises(ValueError):
            revisao.unir(self.db, sozinha, sozinha)

    def test_suspeitas_pegam_o_titulo_quase_igual(self):
        # subtítulo cortado é o caso do mundo real: a chave exige igualdade
        quase = ("TY  - JOUR\nTI  - Anxiety and mood in youth handball players\n"
                 "PY  - 2021\nER  -\n")
        revisao.importar(self.db, self.rev, quase, "embase.ris")
        achados = revisao.suspeitas(self.db, self.rev)
        self.assertTrue(achados, "o título quase igual não foi apontado")
        self.assertGreaterEqual(achados[0]["semelhanca"], revisao.LIMIAR_SUSPEITA)

    def test_dois_dois_diferentes_nao_viram_suspeita(self):
        # DOIs diferentes provam que são trabalhos distintos, por parecido
        # que esteja o título
        outro = ("TY  - JOUR\nTI  - Anxiety and mood in youth handball\n"
                 "PY  - 2021\nDO  - 10.9999/outro.2021\nER  -\n")
        revisao.importar(self.db, self.rev, outro, "embase.ris")
        for achado in revisao.suspeitas(self.db, self.rev):
            self.assertFalse(achado["a"].get("doi") and achado["b"].get("doi")
                             and achado["a"]["doi"] != achado["b"]["doi"])


class TestExportar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.rev = revisao.criar(self.db, "r", "Revisão", reviewers_needed=1)
        revisao.importar(self.db, self.rev, RIS, "scopus.ris")
        self.ana = self.db.member_id("Ana Souza")
        refs = [r["id"] for r in self.db.dicts("SELECT id FROM refs ORDER BY id")]
        motivo = self.db.scalar(
            "SELECT id FROM exclusion_reasons WHERE review_id = ? AND code = 'populacao'",
            (self.rev,))
        revisao.decidir(self.db, refs[0], self.ana, "incluir")
        revisao.decidir(self.db, refs[1], self.ana, "excluir", reason_id=motivo)
        revisao.avancar_etapa(self.db, self.rev)
        revisao.decidir(self.db, refs[0], self.ana, "incluir")
        revisao.fechar_texto_completo(self.db, self.rev)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_o_recorte_de_incluidos_traz_so_o_que_entrou(self):
        linhas = revisao.para_exportar(self.db, self.rev, "incluidos")
        self.assertEqual(len(linhas), 1)
        self.assertTrue(linhas[0]["title"].startswith("Mood profiles"))

    def test_o_recorte_de_excluidos_traz_o_motivo(self):
        linhas = revisao.para_exportar(self.db, self.rev, "excluidos")
        self.assertEqual(linhas[0]["reason_label"], "População não elegível")

    def test_a_triagem_viaja_junto(self):
        linhas = revisao.para_exportar(self.db, self.rev, "todos")
        com_voto = [l for l in linhas if l["votos_texto"]]
        self.assertTrue(com_voto)
        self.assertIn("Ana Souza", com_voto[0]["votos_texto"])

    def test_recorte_inventado_e_recusado(self):
        with self.assertRaises(ValueError):
            revisao.para_exportar(self.db, self.rev, "os_bons")

    def test_ris_sai_no_formato_posicional(self):
        conteudo, nome, mime = revisao.exportar(self.db, self.rev, "ris", "todos")
        self.assertTrue(nome.endswith("-todos.ris"))
        self.assertIn("research-info", mime)
        for linha in conteudo.split("\r\n"):
            if linha:
                self.assertRegex(linha, r"^[A-Z][A-Z0-9]  - ")

    def test_bibtex_fecha_as_chaves(self):
        conteudo, nome, _ = revisao.exportar(self.db, self.rev, "bibtex", "todos")
        self.assertTrue(nome.endswith(".bib"))
        self.assertEqual(conteudo.count("{"), conteudo.count("}"))

    def test_csv_abre_no_excel_em_portugues(self):
        conteudo, nome, _ = revisao.exportar(self.db, self.rev, "csv", "todos")
        self.assertTrue(conteudo.startswith("\ufeff"))
        cabecalho = conteudo.splitlines()[0].lstrip("\ufeff")
        self.assertIn("Decisão", cabecalho)
        self.assertIn("Quem decidiu o quê", cabecalho)

    def test_o_que_sai_pode_voltar(self):
        # a prova de que não é jaula: o arquivo exportado é reimportável
        conteudo, _, _ = revisao.exportar(self.db, self.rev, "ris", "todos")
        volta = referencias.ler(conteudo, "volta.ris")
        self.assertEqual(len(volta), 2)
        self.assertTrue(all(r["title"] for r in volta))
        self.assertTrue(any(r["doi"] for r in volta))


class TestFluxogramaPrisma(unittest.TestCase):
    def setUp(self):
        from lape import prisma as desenho
        self.desenho = desenho
        self.dados = {"identificados": 1284, "duplicados": 312, "triados": 972,
                      "excluidos_triagem": 861, "texto_completo": 111,
                      "excluidos_texto": 74, "incluidos": 37,
                      "por_base": [{"base": "PubMed", "n": 540}],
                      "motivos": [{"motivo": "População não elegível", "n": 402}]}

    def test_todos_os_numeros_aparecem(self):
        svg = self.desenho.desenhar(self.dados, "Revisão")
        for valor in (1284, 312, 972, 861, 111, 74, 37):
            self.assertIn(f"(n = {valor})", svg)

    def test_e_um_svg_valido(self):
        import xml.etree.ElementTree as ET
        ET.fromstring(self.desenho.desenhar(self.dados, "Revisão"))

    def test_texto_com_e_comercial_nao_quebra_o_xml(self):
        import xml.etree.ElementTree as ET
        dados = dict(self.dados, motivos=[{"motivo": "Fora do P&D <interno>", "n": 3}])
        ET.fromstring(self.desenho.desenhar(dados, "Saúde & Esporte <2024>"))

    def test_revisao_recem_aberta_nao_quebra(self):
        vazio = {"identificados": 0, "duplicados": 0, "triados": 0,
                 "excluidos_triagem": 0, "texto_completo": 0, "excluidos_texto": 0,
                 "incluidos": 0, "por_base": [], "motivos": []}
        svg = self.desenho.desenhar(vazio, "Nova")
        self.assertIn("(n = 0)", svg)

    def test_o_titulo_nao_passa_por_cima_da_contagem(self):
        # foi o defeito da primeira versão: título e "(n = ...)" na mesma
        # linha, e o número saía ilegível quando o rótulo era longo
        svg = self.desenho.desenhar(self.dados, "Revisão")
        ys_titulo = re.findall(r'y="(\d+)" font-size="12.5"', svg)
        ys_valor = re.findall(r'y="(\d+)" font-size="17"', svg)
        self.assertTrue(ys_titulo and ys_valor)
        self.assertFalse(set(ys_titulo) & set(ys_valor),
                         "título e contagem caíram na mesma linha")


if __name__ == "__main__":
    unittest.main(verbosity=2)
