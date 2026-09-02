#!/usr/bin/env python3
"""Testes da importação da produção pelas bases públicas.

    python3 -m unittest tests.test_autor -v

O erro caro aqui é importar a produção de outra pessoa: "Andrade A" traz
milhares de artigos de dezenas de gente diferente, e ninguém percebe até
o painel ter o dobro de artigos. Por isso a afiliação, a conferência
antes de gravar, e estes testes.

A fixture é MEDLINE de verdade, com registros reais do LAPE recuperados
do PubMed.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_autor, referencias, sources, variaveis  # noqa: E402
from lape.db import Database  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "pubmed_lape.nbib"


class TestTermoDeBusca(unittest.TestCase):
    def test_o_nome_vira_o_formato_da_pubmed(self):
        # a PubMed indexa "Sobrenome Nome" e "Sobrenome Iniciais"; buscar
        # "Alexandro Andrade" como está escrito não acha nada, e o
        # silêncio parece "esta pessoa não publicou"
        self.assertEqual(sources.termo_de_autor("Alexandro Andrade"),
                         "Andrade Alexandro[Author]")
        self.assertIn("Vilarino Guilherme[Author]",
                      sources.termo_de_autor("Guilherme Torres Vilarino"))

    def test_so_o_primeiro_nome_entra_na_forma_por_extenso(self):
        # "Vilarino Guilherme Torres" exige que o registro traga o nome do
        # meio; os que não trazem somem — some um décimo da produção
        self.assertNotIn("Vilarino Guilherme Torres",
                         sources.termo_de_autor("Guilherme Torres Vilarino"))

    def test_o_sobrenome_composto_tambem_e_procurado(self):
        """A PubMed indexa o sobrenome como o periódico mandou.

        "Guilherme Torres Vilarino" aparece ora como "Vilarino GT", ora
        como "Torres Vilarino G" -- são duas entradas diferentes no índice.
        Procurando só pela última palavra vinham 30 dos 34 artigos dele, e
        os quatro que faltavam estavam todos na forma composta. O silêncio
        parecia "só publicou 30".
        """
        termo = sources.termo_de_autor("Guilherme Torres Vilarino", "UDESC")
        self.assertIn("Torres Vilarino G[Author]", termo)

    def test_o_composto_nao_depende_da_afiliacao(self):
        # dos quatro artigos perdidos, dois não trazem "UDESC" em afiliação
        # nenhuma: prender a forma composta à afiliação recuperaria só metade
        termo = sources.termo_de_autor("Guilherme Torres Vilarino", "UDESC")
        antes = termo.index("Torres Vilarino G[Author]")
        self.assertNotIn("Affiliation", termo[:antes])

    def test_nome_de_duas_partes_nao_inventa_composto(self):
        # "Alexandro Andrade" não tem sobrenome composto para procurar
        termo = sources.termo_de_autor("Alexandro Andrade", "UDESC")
        self.assertEqual(termo,
                         "Andrade Alexandro[Author]"
                         " OR (Andrade A[Author] AND UDESC[Affiliation])")

    def test_quatro_partes_juntam_as_iniciais_do_comeco(self):
        termo = sources.termo_de_autor("Ana Paula Silva Souza")
        self.assertIn("Silva Souza AP[Author]", termo)

    def test_sem_afiliacao_a_forma_abreviada_nao_e_usada_sozinha(self):
        # "Andrade A[Author]" sem afiliação traz milhares de artigos de
        # dezenas de pessoas, e a importação enche o banco de produção alheia
        self.assertNotIn("Andrade A[Author]",
                         sources.termo_de_autor("Alexandro Andrade"))

    def test_com_afiliacao_os_dois_caminhos_valem(self):
        # o nome por extenso acerta a pessoa mesmo quando ela assinou por
        # outra instituição; o abreviado alcança os registros antigos
        termo = sources.termo_de_autor("Alexandro Andrade", "UDESC")
        self.assertIn("Andrade Alexandro[Author]", termo)
        self.assertIn("Andrade A[Author] AND UDESC[Affiliation]", termo)

    def test_o_recorte_de_data_vale_para_a_busca_toda(self):
        # sem parênteses, o AND gruda só no último ramo do OR e o outro
        # volta a produção inteira
        termo = sources.termo_de_autor("Alexandro Andrade", "UDESC", 2006)
        self.assertTrue(termo.startswith("("), termo)
        self.assertIn(") AND (\"2006\"", termo)

    def test_a_afiliacao_entra_na_busca(self):
        termo = sources.termo_de_autor("Alexandro Andrade", "UDESC")
        self.assertIn("UDESC[Affiliation]", termo)

    def test_o_ano_inicial_entra_na_busca(self):
        self.assertIn("2006", sources.termo_de_autor("Fulano Silva", None, 2006))

    def test_nome_de_uma_palavra_nao_quebra(self):
        self.assertEqual(sources.termo_de_autor("Andrade"), "Andrade[Author]")


class TestLeituraDoMedline(unittest.TestCase):
    """O arquivo que a PubMed entrega no botão 'Send to'."""

    def setUp(self):
        self.registros = referencias.ler_nbib(FIXTURE.read_text(encoding="utf-8"))

    def test_cada_registro_e_um_registro(self):
        # o defeito que este teste guarda: o MEDLINE não fecha com `ER`,
        # separa por linha em branco. Sem isso, um .nbib com cem artigos
        # virava UM registro só — com o título do primeiro e os autores de
        # todos — e a importação dizia "1 artigo lido", sem erro nenhum
        self.assertEqual(len(self.registros), 3)
        titulos = {r["title"][:20] for r in self.registros}
        self.assertEqual(len(titulos), 3)

    def test_o_doi_vem_do_lid(self):
        self.assertEqual(self.registros[0]["doi"], "10.3389/fpsyg.2023.1295652")

    def test_a_afiliacao_e_lida(self):
        # é dela que sai o país no mapa
        self.assertIn("UDESC", self.registros[0]["affiliation"])

    def test_o_pais_sai_da_afiliacao(self):
        for registro in self.registros:
            with self.subTest(titulo=registro["title"][:30]):
                achado = variaveis.pais_da_afiliacao(registro["affiliation"])
                self.assertIsNotNone(achado)
                self.assertEqual(achado[0], "Brasil")

    def test_o_ris_continua_fechando_por_er(self):
        # a regra nova não pode quebrar o formato que já funcionava
        ris = ("TY  - JOUR\nTI  - Primeiro\nPY  - 2020\nER  -\n\n"
               "TY  - JOUR\nTI  - Segundo\nPY  - 2021\nER  -\n")
        self.assertEqual(len(referencias.ler(ris, "x.ris")), 2)

    def test_linha_em_branco_no_fim_nao_cria_registro_vazio(self):
        texto = FIXTURE.read_text(encoding="utf-8") + "\n\n\n"
        self.assertEqual(len(referencias.ler_nbib(texto)), 3)


class TestResumoAntesDeGravar(unittest.TestCase):
    def setUp(self):
        registros = referencias.ler_nbib(FIXTURE.read_text(encoding="utf-8"))
        for r in registros:
            achado = variaveis.pais_da_afiliacao(r.get("affiliation"))
            r["pais"] = achado[0] if achado else None
        self.achado = {"termo": "Andrade A[Author]", "pmids": [], "registros": registros}

    def test_conta_o_que_traria(self):
        resumo = ingest_autor.resumir(self.achado)
        self.assertEqual(resumo["encontrados"], 3)
        self.assertEqual(resumo["com_doi"], 3)
        self.assertEqual(resumo["com_resumo"], 3)

    def test_mostra_o_periodo(self):
        resumo = ingest_autor.resumir(self.achado)
        self.assertEqual(resumo["primeiro_ano"], 2024)
        self.assertEqual(resumo["ultimo_ano"], 2025)

    def test_mostra_as_revistas_e_os_paises(self):
        # é por revista e país que se confere se é a pessoa certa
        resumo = ingest_autor.resumir(self.achado)
        self.assertTrue(resumo["revistas"])
        self.assertEqual(resumo["paises"], [("Brasil", 3)])

    def test_o_resumo_nao_toca_no_banco(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "t.sqlite")
            db.migrate()
            ingest_autor.resumir(self.achado)
            self.assertEqual(db.scalar("SELECT COUNT(*) FROM articles"), 0)
            db.close()


class TestImportacaoDaProducao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        registros = referencias.ler_nbib(FIXTURE.read_text(encoding="utf-8"))
        self.achado = {"termo": "t", "pmids": [], "registros": registros}

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_grava_cada_artigo_uma_vez(self):
        primeira = ingest_autor.importar(self.db, self.achado, quem="Alexandro Andrade")
        self.assertEqual(primeira["novos"], 3)
        segunda = ingest_autor.importar(self.db, self.achado, quem="Alexandro Andrade")
        self.assertEqual(segunda["novos"], 0)
        self.assertEqual(segunda["ja_havia"], 3)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM articles"), 3)

    def test_os_autores_entram_na_ordem(self):
        ingest_autor.importar(self.db, self.achado, quem="Alexandro Andrade")
        autores = [linha["author_name"] for linha in self.db.dicts(
            "SELECT aa.author_name FROM article_authors aa JOIN articles a ON a.id = aa.article_id"
            " WHERE a.title LIKE 'Impact of the COVID%' ORDER BY aa.author_order")]
        self.assertEqual(autores[0], "Andrade, Alexandro")
        self.assertIn("Neiva, Henrique Pereira", autores)

    def test_o_resumo_vem_junto(self):
        # é ele que alimenta o reconhecimento de variáveis
        ingest_autor.importar(self.db, self.achado)
        notas = self.db.scalar("SELECT notes FROM articles WHERE title LIKE 'Impact%'")
        self.assertIn("mental health", notas)

    def test_as_variaveis_sao_reconhecidas_no_que_chegou(self):
        ingest_autor.importar(self.db, self.achado)
        variaveis.instalar(self.db)
        resultado = variaveis.marcar_artigos(self.db)
        self.assertEqual(resultado["com_variavel"], 3)
        codigos = {linha["code"] for linha in self.db.dicts(
            "SELECT v.code FROM article_variables av JOIN variables v ON v.id = av.variable_id")}
        self.assertIn("ansiedade", codigos)
        self.assertIn("fibromialgia", codigos)

    def test_nao_passa_por_cima_do_que_o_laboratorio_digitou(self):
        from lape import ingest_excel
        ingest_excel.ingest_articles(self.db, [
            {"title": "Impact of the COVID-19 pandemic on the psychological aspects and "
                      "mental health of elite soccer athletes: a systematic review.",
             "authors": "Quem digitou", "status": "Em produção",
             "journal": "Revista digitada à mão"}])
        ingest_autor.importar(self.db, self.achado)
        self.assertEqual(
            self.db.scalar("SELECT journal FROM articles WHERE title LIKE 'Impact%'"),
            "Revista digitada à mão")

    def test_o_pais_de_cada_coautor_e_gravado(self):
        # um artigo Brasil-Portugal foi produzido nos dois. Lendo só a
        # primeira afiliação ele vira brasileiro, e a colaboração
        # internacional some justamente do mapa que existe para mostrá-la
        for registro in self.achado["registros"]:
            registro["paises"] = variaveis.paises_da_afiliacao(registro.get("afiliacoes"))
        ingest_autor.importar(self.db, self.achado)
        paises = {linha["country"] for linha in self.db.dicts(
            "SELECT country FROM article_countries")}
        self.assertIn("Brasil", paises)
        self.assertIn("Portugal", paises)

    def test_o_pais_alimenta_o_mapa(self):
        from lape import analise
        for registro in self.achado["registros"]:
            registro["paises"] = variaveis.paises_da_afiliacao(registro.get("afiliacoes"))
        ingest_autor.importar(self.db, self.achado)
        # sem isto o mapa fica vazio até alguém ligar cada integrante à
        # sua instituição, um por um -- e ninguém liga
        nomes = {x["pais"]: x["n"] for x in analise.paises(self.db)["todos"]}
        self.assertEqual(nomes.get("Brasil"), 3)
        self.assertEqual(nomes.get("Portugal"), 1)

    def test_o_identificador_da_base_vem_junto(self):
        # sem PMID e PMC gravados, o clique no título leva ao resumo em
        # vez do texto completo -- e a coluna do Excel sai vazia
        registro = dict(self.achado["registros"][0], pmid="12345678", pmc="PMC7654321",
                        oa_url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7654321/")
        ingest_autor.importar(self.db, {"termo": "t", "pmids": [], "registros": [registro]})
        linha = self.db.dicts("SELECT pmid, pmc, oa_url, open_access FROM articles")[0]
        self.assertEqual(linha["pmid"], "12345678")
        self.assertEqual(linha["pmc"], "PMC7654321")
        self.assertIn("PMC7654321", linha["oa_url"])
        self.assertEqual(linha["open_access"], 1)

    def test_artigo_sem_titulo_e_ignorado(self):
        vazio = {"termo": "t", "pmids": [], "registros": [{"title": None, "year": 2020}]}
        resultado = ingest_autor.importar(self.db, vazio)
        self.assertEqual(resultado["novos"], 0)


class TestListaDePesquisadores(unittest.TestCase):
    """Quem o laboratório pediu para trazer das bases.

    A busca certa é o resultado de conferir quantos artigos cada forma do
    nome traz -- não é coisa de improvisar na hora, então fica escrita.
    """

    def test_os_dois_professores_estao_na_lista(self):
        nomes = {p["nome"] for p in ingest_autor.PESQUISADORES}
        self.assertIn("Alexandro Andrade", nomes)
        self.assertIn("Guilherme Torres Vilarino", nomes)

    def test_o_id_lattes_do_coordenador_esta_gravado(self):
        # é ele que acha o currículo certo entre os arquivos de data/raw/
        # e que monta o link do CV na tela
        andrade = next(p for p in ingest_autor.PESQUISADORES
                       if p["nome"] == "Alexandro Andrade")
        self.assertEqual(andrade["lattes"], "5577164706111568")
        self.assertEqual(ingest_autor.link_do_lattes(andrade["lattes"]),
                         "http://lattes.cnpq.br/5577164706111568")

    def test_sem_id_lattes_nao_se_inventa_link(self):
        # link para currículo errado é pior que link nenhum
        self.assertIsNone(ingest_autor.link_do_lattes(None))
        self.assertIsNone(ingest_autor.link_do_lattes("Alexandro Andrade"))

    def test_toda_pessoa_da_lista_tem_afiliacao(self):
        # sem afiliação a busca traz produção alheia, e ninguém percebe
        # até o painel ter o dobro de artigos
        for pessoa in ingest_autor.PESQUISADORES:
            with self.subTest(quem=pessoa["nome"]):
                self.assertTrue(pessoa.get("afiliacao"))

    def test_uma_falha_nao_derruba_as_outras(self):
        # a rede cai no meio da segunda busca; quem já entrou tem de ficar
        tmp = tempfile.TemporaryDirectory()
        db = Database(Path(tmp.name) / "t.sqlite")
        db.migrate()
        original = ingest_autor.buscar
        chamadas = []

        def falso(nome, afiliacao=None, desde=None, limite=400):
            chamadas.append(nome)
            if len(chamadas) > 1:
                raise RuntimeError("sem internet")
            return {"termo": "t", "pmids": [],
                    "registros": referencias.ler_nbib(FIXTURE.read_text(encoding="utf-8"))}

        ingest_autor.buscar = falso
        try:
            resultado = ingest_autor.trazer_todos(db)
        finally:
            ingest_autor.buscar = original
            db.close()
            tmp.cleanup()
        self.assertEqual(len(resultado["pessoas"]), len(ingest_autor.PESQUISADORES))
        self.assertIn("erro", resultado["pessoas"][1])
        self.assertEqual(resultado["pessoas"][0]["gravado"]["novos"], 3)


class TestIdentificadores(unittest.TestCase):
    """DOI, PMID, PMC e acesso aberto — o que faz o clique abrir o artigo."""

    def test_o_pmid_sai_do_endereco(self):
        self.assertEqual(
            sources._so_numero("https://pubmed.ncbi.nlm.nih.gov/38333426"), "38333426")
        self.assertIsNone(sources._so_numero(None))

    def test_o_pmc_sai_normalizado(self):
        # vem em três formas diferentes das três fontes
        for bruto in ("PMC10850388", "pmc10850388",
                      "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10850388"):
            with self.subTest(bruto=bruto):
                self.assertEqual(sources._pmc(bruto), "PMC10850388")
        self.assertIsNone(sources._pmc("sem identificador"))

    def test_o_openalex_entrega_os_quatro(self):
        obra = sources._openalex_work({
            "id": "https://openalex.org/W1", "doi": "https://doi.org/10.1/x",
            "title": "Um artigo", "publication_year": 2024,
            "ids": {"pmid": "https://pubmed.ncbi.nlm.nih.gov/38333426",
                    "pmcid": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10850388"},
            "open_access": {"is_oa": True, "oa_status": "gold",
                            "oa_url": "https://exemplo.org/artigo.pdf"},
            "authorships": [], "primary_location": {},
        })
        self.assertEqual(obra["pmid"], "38333426")
        self.assertEqual(obra["pmc"], "PMC10850388")
        self.assertEqual(obra["oa_status"], "gold")
        self.assertTrue(obra["open_access"])
        self.assertEqual(obra["oa_url"], "https://exemplo.org/artigo.pdf")

    def test_artigo_fechado_nao_vira_aberto(self):
        obra = sources._openalex_work({
            "id": "W2", "title": "Outro", "open_access": {"is_oa": False},
            "authorships": [], "primary_location": {}, "ids": {},
        })
        self.assertFalse(obra["open_access"])
        self.assertIsNone(obra["oa_url"])

    def test_o_medline_entrega_o_pmc_como_texto_livre(self):
        texto = ("PMID- 39845808\nTI  - Um artigo qualquer.\n"
                 "PMC - PMC11751499\nDP  - 2024\nLA  - eng\n")
        registro = referencias.ler_nbib(texto)[0]
        self.assertEqual(registro["pmc"], "PMC11751499")
        self.assertIn("PMC11751499", registro["oa_url"])

    def test_sem_pmc_nao_se_inventa_texto_livre(self):
        registro = referencias.ler_nbib(
            "PMID- 1\nTI  - Sem PMC.\nDP  - 2024\nLA  - eng\n")[0]
        self.assertIsNone(registro.get("oa_url"))


class TestOrdemDosDestinos(unittest.TestCase):
    """Para onde o clique leva, na ordem de quem quer LER."""

    def js(self):
        return (ROOT / "scripts" / "lape" / "templates" / "panorama.js").read_text(
            encoding="utf-8")

    def corpo(self):
        js = self.js()
        return js[js.index("function destinosDoArtigo(a)"):js.index("function artigosFiltrados")]

    def test_o_titulo_leva_a_onde_o_artigo_saiu(self):
        # o pedido é "clicar no título abre o site onde foi publicado":
        # isso é o DOI, que resolve para a editora. O PMC é uma cópia --
        # abrir a cópia no lugar da fonte faria o título mentir
        corpo = self.corpo()
        doi = corpo[corpo.index('chave: "doi"'):corpo.index('chave: "pmc"')]
        pmc = corpo[corpo.index('chave: "pmc"'):corpo.index('chave: "pubmed"')]
        self.assertIn("editora: true", doi)
        self.assertNotIn("editora", pmc)

    def test_o_texto_livre_nunca_fica_escondido(self):
        # mandar quem vai ler para o resumo atrás do paywall quando há PDF
        # livre no PMC é o detalhe que faz a pessoa desistir. O título vai
        # para a editora, mas o texto livre continua a UM clique, marcado
        corpo = self.corpo()
        pmc = corpo[corpo.index('chave: "pmc"'):corpo.index('chave: "pubmed"')]
        self.assertIn("livre: true", pmc)
        css = (ROOT / "scripts" / "lape" / "templates" / "panorama.html").read_text(
            encoding="utf-8")
        self.assertIn(".base.livre", css)

    def test_o_pmc_vira_endereco_do_pmc(self):
        self.assertIn("ncbi.nlm.nih.gov/pmc/articles/", self.corpo())

    def test_sem_id_da_base_a_busca_vem_marcada_como_busca(self):
        # o Scopus só abre o registro pelo id dele; pelo DOI dá para
        # procurar, e procurar não é abrir
        corpo = self.corpo()
        scopus = corpo[corpo.index("scopus.com/results/results.uri"):]
        self.assertIn("busca: true", corpo[:corpo.index("scopus.com/results/results.uri")]
                      [-400:] + scopus[:200])
        wos = corpo[corpo.index("general-search"):]
        self.assertIn("busca", corpo[:corpo.index("general-search")][-400:] + wos[:200])

    def test_a_exportacao_leva_os_identificadores(self):
        api_py = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        bloco = api_py[api_py.index("COLUNAS_EXTRACAO"):api_py.index("def _linhas_de_extracao")]
        for coluna in ("PMID", "PMC", "Texto completo livre", "Acesso aberto"):
            with self.subTest(coluna=coluna):
                self.assertIn(coluna, bloco)


if __name__ == "__main__":
    unittest.main(verbosity=2)
