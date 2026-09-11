#!/usr/bin/env python3
"""Testes da biblioteca: o acervo de leitura atualizado sozinho.

    python3 -m unittest tests.test_biblioteca -v

A biblioteca nao e uma revisao, e a diferenca e o que estes testes
guardam primeiro. A revisao responde UMA pergunta, tria em duplicata e
fecha; a biblioteca fica aberta e so recolhe. Um artigo entrar aqui nao
diz que ele responde a pergunta de ninguem -- diz que a equipe deveria
saber que ele existe.

Depois vem a parte que ja custou caro em buscas de verdade: `POMS` solto
na PubMed e traduzido para `"prod oper manag"[Journal]`, e a revista
Production & Operations Management entra num acervo de psicologia do
esporte sem nenhum aviso.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import biblioteca, linhas  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseBiblioteca(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "b.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        linhas.instalar(self.db)

    def trocar(self, modulo, nome, valor):
        antigo = getattr(modulo, nome)
        setattr(modulo, nome, valor)
        self.addCleanup(setattr, modulo, nome, antigo)


class TestAEstrategiaDeBusca(unittest.TestCase):
    """A busca fica escrita, e nao digitada a cada vez."""

    def test_poms_nunca_vai_solto(self):
        """Solto, a PubMed o confunde com o nome de uma revista.

        `POMS AND athletes` traduz para `("prod oper manag"[Journal] OR
        "poms"[All Fields]) AND ...` e devolve 362 registros, entre eles
        artigos de Production & Operations Management. Medido na base, nao
        suposto. O recorte em titulo-resumo e o que resolve, e ele sai da
        `frase` -- por isso o teste olha a query montada, e nao a lista.
        """
        decl = biblioteca.BIBLIOTECAS[0]
        self.assertIn("POMS", decl["construto"])
        for base in biblioteca.BASES:
            with self.subTest(base=base):
                query = biblioteca.query_de(decl, base=base)
                self.assertNotIn('"POMS"[All Fields]', query)
                self.assertNotIn("ALL(", query)

    def test_a_busca_e_sempre_em_titulo_e_resumo(self):
        """"Todos os campos" acha o termo em volta do texto, e nao nele.

        Na Scopus, `ALL()` casa com a lista de referencias de artigos que
        nao sao do assunto: um artigo de cardiologia que cita um estudo de
        humor entraria no acervo de psicologia do esporte.
        """
        campos = {biblioteca.PUBMED: "[Title/Abstract]",
                  biblioteca.SCOPUS: "TITLE-ABS-KEY(",
                  biblioteca.WOS: "TS=("}
        decl = biblioteca.BIBLIOTECAS[0]
        for base, marca in campos.items():
            with self.subTest(base=base):
                self.assertIn(marca, biblioteca.query_de(decl, base=base))

    def test_a_populacao_e_atleta_e_nao_esporte_em_geral(self):
        """`"sports"[MeSH]` traz programa comunitario de caminhada.

        Sao estudos com estado de humor medido e nenhum atleta dentro. A
        busca dobrava de 431 para 847 registros por causa disso.
        """
        query = biblioteca.query_de(biblioteca.BIBLIOTECAS[0], base=biblioteca.PUBMED)
        self.assertNotIn('"sports"[MeSH Terms]', query)
        self.assertIn('"athletes"[MeSH Terms]', query)

    def test_o_mesh_so_vai_para_a_pubmed(self):
        """`TITLE-ABS-KEY("athletes[MeSH Terms]")` nao acha nada.

        A Scopus procuraria essa sequencia literal de caracteres num
        resumo. Nao daria erro -- daria zero, que e pior.
        """
        decl = biblioteca.BIBLIOTECAS[0]
        for base in (biblioteca.SCOPUS, biblioteca.WOS):
            with self.subTest(base=base):
                self.assertNotIn("MeSH", biblioteca.query_de(decl, base=base))

    def test_a_query_junta_construto_populacao_e_segmento(self):
        decl = biblioteca.BIBLIOTECAS[0]
        geral = biblioteca.query_de(decl)
        self.assertEqual(geral.count(" AND "), 1)
        com_segmento = biblioteca.query_de(decl, ("handball",))
        self.assertEqual(com_segmento.count(" AND "), 2)
        self.assertTrue(com_segmento.startswith(geral))

    def test_o_vocabulario_e_declarado_uma_vez_para_as_tres_bases(self):
        """Escrever a estrategia tres vezes seria garantir que divergissem.

        Alguem acrescenta um termo na da PubMed, esquece as outras duas, e
        o acervo passa a ter tres tamanhos sem que nada explique por que.
        """
        decl = biblioteca.BIBLIOTECAS[0]
        for termo in decl["construto"]:
            for base in biblioteca.BASES:
                with self.subTest(termo=termo, base=base):
                    self.assertIn(termo, biblioteca.query_de(decl, base=base))

    def test_todo_segmento_tem_palavra(self):
        # segmento sem palavra viraria a busca geral com outro nome, e o
        # mesmo acervo apareceria repetido em quatorze abas
        for nome, palavras in biblioteca.ESPORTES:
            with self.subTest(esporte=nome):
                self.assertTrue(palavras)
                self.assertTrue(all(p.strip() for p in palavras))

    def test_toda_biblioteca_aponta_para_uma_linha_de_pesquisa(self):
        codigos = {c for c, *_ in linhas.LINHAS}
        for decl in biblioteca.BIBLIOTECAS:
            with self.subTest(acervo=decl["code"]):
                self.assertIn(decl["linha"], codigos)


class TestOsLinksParaAsBases(unittest.TestCase):
    """Cada artigo, e o caminho ate ele em cada base."""

    def test_o_doi_vem_primeiro_porque_nao_erra(self):
        """A ordem e a da certeza, e nao a do prestigio da base.

        O DOI aponta para UM artigo; a busca por titulo na Scopus pode
        trazer outro. Pôr a Scopus em primeiro mandaria a pessoa para o
        caminho mais incerto primeiro.
        """
        achados = biblioteca.links({"doi": "10.1000/x", "title": "Um estudo"})
        self.assertEqual(achados[0]["base"], "DOI")
        self.assertTrue(achados[0]["forte"])

    def test_as_cinco_bases_aparecem(self):
        bases = {l["base"] for l in biblioteca.links(
            {"doi": "10.1000/x", "pmid": "1", "title": "Um estudo"})}
        for esperada in ("DOI", "PubMed", "Scopus", "Web of Science", "LILACS"):
            with self.subTest(base=esperada):
                self.assertIn(esperada, bases)

    def test_a_busca_nao_se_disfarca_de_link_direto(self):
        # quem clica esperando o artigo e cai numa busca perde a confianca
        # no botao, e passa a conferir todos
        for link in biblioteca.links({"doi": "10.1000/x", "title": "Um estudo"}):
            with self.subTest(base=link["base"]):
                if link["base"] in ("Scopus", "Web of Science", "LILACS",
                                    "Google Acadêmico"):
                    self.assertEqual(link["tipo"], biblioteca.BUSCA)
                    self.assertTrue(link["dica"])

    def test_sem_doi_a_scopus_vai_por_titulo_e_avisa(self):
        achados = {l["base"]: l for l in biblioteca.links({"title": "Um estudo"})}
        self.assertIn("Scopus", achados)
        self.assertIn("confira", achados["Scopus"]["dica"])
        self.assertNotIn("Web of Science", achados)   # sem DOI nao ha busca confiavel

    def test_o_texto_livre_e_marcado(self):
        # a equipe procura primeiro o que da para ler hoje
        achados = biblioteca.links({"pmc": "PMC123", "title": "Um estudo"})
        pmc = next(l for l in achados if l["base"] == "PMC")
        self.assertTrue(pmc["livre"])

    def test_artigo_sem_nada_nao_inventa_link(self):
        self.assertEqual(biblioteca.links({}), [])

    def test_o_doi_entra_normalizado(self):
        achados = biblioteca.links({"doi": "https://doi.org/10.1000/X", "title": "t"})
        self.assertEqual(achados[0]["url"], "https://doi.org/10.1000/x")


class TestInstalar(BaseBiblioteca):

    def test_o_acervo_entra_com_uma_busca_por_segmento(self):
        biblioteca.instalar(self.db)
        n = self.db.scalar("SELECT COUNT(*) FROM biblioteca_busca")
        # uma geral mais uma por esporte, em cada uma das tres bases
        por_base = 1 + len(biblioteca.ESPORTES)
        self.assertEqual(n, por_base * len(biblioteca.BASES))

    def test_instalar_de_novo_nao_duplica(self):
        biblioteca.instalar(self.db)
        segunda = biblioteca.instalar(self.db)
        self.assertEqual(segunda["novas"], [])
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM biblioteca"), 1)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM biblioteca_busca"),
                         (1 + len(biblioteca.ESPORTES)) * len(biblioteca.BASES))

    def test_o_acervo_fica_ligado_a_linha_de_pesquisa(self):
        biblioteca.instalar(self.db)
        linha = self.db.scalar(
            "SELECT rl.code FROM biblioteca b"
            " JOIN research_lines rl ON rl.id = b.research_line_id")
        self.assertEqual(linha, "psicologia_do_esporte")


MEDLINE_HANDEBOL = """PMID- 42506832
TI  - Associations Between Endocrine Status and Stress, Mood and Psychosomatic
      Status in Elite Handball Players.
AB  - This study aimed to investigate the associations between endocrine status
      and mood in elite handball players.
FAU - Ratz-Sulyok, Fanny Zselyke
FAU - Zsakai, Annamaria
AD  - Hungarian Handball Federation, Budapest, Hungary.
TA  - Sports (Basel)
DP  - 2026 Jul 8
LID - 10.3390/sports14070289 [doi]
PMC - PMC13417319

"""

MEDLINE_NATACAO = """PMID- 41889694
TI  - Mood states across a competitive season in elite swimmers.
AB  - Mood was measured with BRUMS across a season in elite swimmers.
FAU - Silva, Ana
AD  - Universidade do Estado de Santa Catarina, Florianopolis, Brazil.
TA  - J Sports Sci
DP  - 2025
LID - 10.1000/swim.2025 [doi]

"""


class TestAAtualizacao(BaseBiblioteca):
    """O motor que recolhe, sem sair para a rede de verdade.

    A base fica de mentira de proposito: o teste nao pode depender da
    internet nem de uma contagem que muda sozinha na PubMed. O que se
    verifica aqui e o que o sistema FAZ com o que a base devolve.
    """

    def setUp(self):
        super().setUp()
        biblioteca.instalar(self.db)
        from lape import sources
        self.respostas = {}
        self.pedidos = []

        def busca_falsa(query, retmax=400, **kwargs):
            self.pedidos.append(query)
            return list(self.respostas.get(query, {}).keys())

        def medline_falsa(pmids):
            texto = ""
            for resposta in self.respostas.values():
                for pmid, corpo in resposta.items():
                    if pmid in pmids:
                        texto += corpo
            return texto

        self.trocar(sources, "pubmed_search", busca_falsa)
        self.trocar(sources, "pubmed_medline", medline_falsa)

    def responder(self, segmento, registros, base=None):
        """Liga uma resposta a busca daquele segmento, numa base.

        A base e obrigatoria na pratica: depois que o acervo passou a ter
        tres, `WHERE segmento IS ?` casava com tres linhas e o teste
        passava pela primeira que o SQLite devolvesse. Passar acertando
        por acidente e pior do que falhar.
        """
        base = base or biblioteca.PUBMED
        query = self.db.scalar(
            "SELECT query FROM biblioteca_busca WHERE base = ? AND segmento IS ?",
            (base, segmento))
        self.assertIsNotNone(query, f"não há busca de {segmento} em {base}")
        self.respostas[query] = registros

    def test_o_que_a_base_devolve_entra_no_acervo(self):
        self.responder("Handebol", {"42506832": MEDLINE_HANDEBOL})
        r = biblioteca.atualizar(self.db, "humor_esporte", bases=(biblioteca.PUBMED,))
        self.assertEqual(r["novos"], 1)
        item = self.db.dicts("SELECT * FROM biblioteca_item")[0]
        self.assertIn("Handball", item["title"])
        self.assertEqual(item["doi"], "10.3390/sports14070289")
        self.assertEqual(item["segmento"], "Handebol")

    def test_rodar_de_novo_nao_traz_o_mesmo_artigo_duas_vezes(self):
        self.responder("Handebol", {"42506832": MEDLINE_HANDEBOL})
        biblioteca.atualizar(self.db, "humor_esporte", bases=(biblioteca.PUBMED,))
        segunda = biblioteca.atualizar(self.db, "humor_esporte", bases=(biblioteca.PUBMED,))
        self.assertEqual(segunda["novos"], 0)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM biblioteca_item"), 1)

    def test_artigo_de_dois_esportes_pertence_aos_dois(self):
        """Um estudo com nadadores E handebolistas e dos dois segmentos.

        Guardar so o primeiro faria o segundo parecer vazio -- e quem
        abrisse "Natação" nao encontraria um artigo sobre natacao que o
        sistema tinha.
        """
        self.responder("Handebol", {"42506832": MEDLINE_HANDEBOL})
        self.responder("Natação", {"42506832": MEDLINE_HANDEBOL})
        r = biblioteca.atualizar(self.db, "humor_esporte", bases=(biblioteca.PUBMED,))
        self.assertEqual(r["novos"], 1)          # um artigo, nao dois
        item = self.db.dicts("SELECT segmento FROM biblioteca_item")[0]
        self.assertEqual(item["segmento"], "Handebol; Natação")

    def test_o_recorte_por_segmento_acha_o_artigo_nos_dois(self):
        self.responder("Handebol", {"42506832": MEDLINE_HANDEBOL})
        self.responder("Natação", {"42506832": MEDLINE_HANDEBOL})
        biblioteca.atualizar(self.db, "humor_esporte", bases=(biblioteca.PUBMED,))
        for esporte in ("Handebol", "Natação"):
            with self.subTest(esporte=esporte):
                achado = biblioteca.listar(self.db, "humor_esporte", segmento=esporte)
                self.assertEqual(len(achado["itens"]), 1)

    def test_uma_busca_que_falha_nao_derruba_as_outras(self):
        """A rede cai no meio de quatorze modalidades.

        Perder as treze que ja tinham voltado por causa da decima quarta
        seria trocar um acervo por um erro.
        """
        from lape import sources

        def as_vezes_quebra(query, retmax=400, **kwargs):
            if "handball" in query:
                raise RuntimeError("a rede caiu")
            return list(self.respostas.get(query, {}).keys())

        self.responder("Natação", {"41889694": MEDLINE_NATACAO})
        self.trocar(sources, "pubmed_search", as_vezes_quebra)
        r = biblioteca.atualizar(self.db, "humor_esporte", bases=(biblioteca.PUBMED,))
        self.assertEqual(r["erros"], 1)
        self.assertEqual(r["novos"], 1)
        erro = self.db.scalar(
            "SELECT erro FROM biblioteca_busca WHERE segmento = 'Handebol'")
        self.assertIn("a rede caiu", erro)

    def test_o_erro_fica_gravado_ao_lado_da_busca_que_falhou(self):
        # sem isso, "0 achados" e indistinguivel de "a base nao respondeu"
        from lape import sources
        self.trocar(sources, "pubmed_search",
                    lambda *a, **k: (_ for _ in ()).throw(RuntimeError("403")))
        biblioteca.atualizar(self.db, "humor_esporte", bases=(biblioteca.PUBMED,))
        p = biblioteca.panorama(self.db, "humor_esporte")
        self.assertTrue(all(s["erro"] for s in p["segmentos"]))

    def test_o_erro_some_quando_a_busca_volta_a_funcionar(self):
        from lape import sources
        self.trocar(sources, "pubmed_search",
                    lambda *a, **k: (_ for _ in ()).throw(RuntimeError("403")))
        biblioteca.atualizar(self.db, "humor_esporte", bases=(biblioteca.PUBMED,))
        self.trocar(sources, "pubmed_search", lambda q, retmax=400, **k: [])
        biblioteca.atualizar(self.db, "humor_esporte", bases=(biblioteca.PUBMED,))
        self.assertIsNone(self.db.scalar(
            "SELECT erro FROM biblioteca_busca WHERE segmento = 'Handebol'"))


class TestAsBasesQuePedemChave(BaseBiblioteca):
    """Scopus e WoS como FONTE do acervo, e nao so como link de saida.

    E o que faz a biblioteca cobrir o que a PubMed nao indexa -- e a
    psicologia do esporte publica bastante fora dela, em revistas de
    ciencias do esporte que so a Scopus cataloga.
    """

    def setUp(self):
        super().setUp()
        biblioteca.instalar(self.db)

    def sem_chaves(self):
        alvo = biblioteca.config
        for nome in ("SCOPUS_API_KEY", "WOS_API_KEY", "SCOPUS_INST_TOKEN"):
            self.trocar(alvo, nome, "")

    def test_sem_chave_a_base_e_pulada_com_o_nome_da_variavel(self):
        """Zero calado seria indistinguivel de "a base nao tem o assunto".

        E quem lesse iria procurar termos melhores para uma busca que
        nunca saiu da maquina.
        """
        self.sem_chaves()
        from lape import sources
        self.trocar(sources, "pubmed_search", lambda *a, **k: [])
        r = biblioteca.atualizar(self.db, "humor_esporte")
        faltando = {x["base"]: x["porque"] for x in r["sem_chave"]}
        self.assertIn("scopus", faltando)
        self.assertIn("SCOPUS_API_KEY", faltando["scopus"])
        self.assertIn("wos", faltando)
        self.assertIn("WOS_API_KEY", faltando["wos"])

    def test_a_chave_que_falta_e_uma_noticia_so_e_nao_quinze(self):
        """Sao quinze buscas por base.

        Sem desligar a base na primeira, a tela mostraria a mesma frase
        quinze vezes e a pessoa leria quinze erros onde ha um recado.
        """
        self.sem_chaves()
        from lape import sources
        self.trocar(sources, "pubmed_search", lambda *a, **k: [])
        r = biblioteca.atualizar(self.db, "humor_esporte")
        bases = [x["base"] for x in r["sem_chave"]]
        self.assertEqual(sorted(bases), ["scopus", "wos"])   # uma linha por base

    def test_falta_de_chave_nao_conta_como_erro_de_busca(self):
        # "3 buscas falharam" sugere defeito; "falta a chave" diz o que fazer
        self.sem_chaves()
        from lape import sources
        self.trocar(sources, "pubmed_search", lambda *a, **k: [])
        r = biblioteca.atualizar(self.db, "humor_esporte")
        self.assertEqual(r["erros"], 0)
        self.assertTrue(r["sem_chave"])

    def test_a_pubmed_roda_mesmo_sem_as_outras_duas(self):
        # a base aberta nao pode ficar de fora por falta de convenio
        self.sem_chaves()
        from lape import sources
        chamou = []
        self.trocar(sources, "pubmed_search",
                    lambda q, retmax=400, **k: chamou.append(q) or [])
        biblioteca.atualizar(self.db, "humor_esporte")
        self.assertEqual(len(chamou), 1 + len(biblioteca.ESPORTES))

    # -- a leitura do que cada base devolve ------------------------------
    def test_a_scopus_vira_registro(self):
        entrada = {
            "dc:title": "Mood states in elite rowers",
            "dc:creator": "Silva A.",
            "prism:publicationName": "J Sports Sci",
            "prism:coverDate": "2024-03-01",
            "prism:doi": "10.1000/row.2024",
            "pubmed-id": "39999999",
        }
        achado = biblioteca._do_scopus(entrada)
        self.assertEqual(achado["title"], "Mood states in elite rowers")
        self.assertEqual(achado["year"], 2024)
        self.assertEqual(achado["doi"], "10.1000/row.2024")
        self.assertEqual(achado["base"], biblioteca.SCOPUS)

    def test_a_scopus_sem_data_nao_inventa_ano(self):
        achado = biblioteca._do_scopus({"dc:title": "x", "prism:coverDate": ""})
        self.assertIsNone(achado["year"])

    def test_a_wos_vira_registro(self):
        hit = {
            "title": "Mood profile across a season",
            "source": {"sourceTitle": "Front Psychol", "publishYear": "2023"},
            "identifiers": {"doi": "10.1000/wos.1", "pmid": "12345"},
            "names": {"authors": [{"displayName": "Andrade A"},
                                  {"displayName": "Vilarino GT"}]},
        }
        achado = biblioteca._do_wos(hit)
        self.assertEqual(achado["year"], 2023)
        self.assertEqual(achado["authors"], "Andrade A; Vilarino GT")
        self.assertEqual(achado["base"], biblioteca.WOS)

    def test_o_registro_guarda_de_qual_base_veio(self):
        """Saber a origem e o que permite conferir e comparar depois.

        Sem isso, um acervo de tres fontes viraria um acervo sem fonte, e
        nao haveria como responder "quanto a Scopus acrescentou".
        """
        bid = self.db.scalar("SELECT id FROM biblioteca")
        from lape.revisao import chave_de_uniao
        biblioteca._gravar(self.db, bid, "Remo e canoagem",
                           {"title": "Da Scopus", "base": biblioteca.SCOPUS},
                           chave_de_uniao)
        self.db.conn.commit()
        self.assertEqual(self.db.scalar("SELECT base FROM biblioteca_item"),
                         biblioteca.SCOPUS)


class TestOMesmoArtigoVindoDeDuasBases(BaseBiblioteca):
    """As bases discordam sobre o DOI, e isso ja gravou dado errado.

    A PubMed traz o artigo com DOI; a Scopus traz o mesmo sem. A primeira
    versao comparava so a chave principal -- que e o DOI quando existe --,
    e o segundo virava artigo novo. O acervo contava duas vezes a mesma
    leitura, e a equipe leria o mesmo resumo duas vezes achando que sao
    dois estudos.

    O modulo de revisao ja sabia disso e resolvia com DUAS chaves. O
    defeito foi usar a funcao errada das duas.
    """

    def setUp(self):
        super().setUp()
        biblioteca.instalar(self.db)
        self.bid = self.db.scalar("SELECT id FROM biblioteca")

    def gravar(self, registro, segmento="Handebol"):
        from lape.revisao import chaves_de_uniao
        novo = biblioteca._gravar(self.db, self.bid, segmento, registro, chaves_de_uniao)
        self.db.conn.commit()
        return novo

    MESMO = {"title": "Mood states across a season in elite swimmers", "year": 2024}

    def test_com_doi_e_sem_doi_sao_o_mesmo_artigo(self):
        self.assertTrue(self.gravar({**self.MESMO, "doi": "10.1000/a"}))
        self.assertFalse(self.gravar({**self.MESMO}))          # sem DOI, da Scopus
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM biblioteca_item"), 1)

    def test_a_ordem_inversa_tambem_une(self):
        # sem DOI primeiro, com DOI depois: a base lenta nao pode duplicar
        self.assertTrue(self.gravar({**self.MESMO}))
        self.assertFalse(self.gravar({**self.MESMO, "doi": "10.1000/a"}))
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM biblioteca_item"), 1)

    def test_o_segmento_da_segunda_base_e_somado(self):
        self.gravar({**self.MESMO, "doi": "10.1000/a"}, segmento="Natação")
        self.gravar({**self.MESMO}, segmento="Handebol")
        self.assertEqual(self.db.scalar("SELECT segmento FROM biblioteca_item"),
                         "Handebol; Natação")

    def test_as_duas_chaves_ficam_gravadas(self):
        # guardar so a principal e o que impedia o casamento pela outra
        self.gravar({**self.MESMO, "doi": "10.1000/a"})
        linha = self.db.dicts("SELECT chave, chave_titulo FROM biblioteca_item")[0]
        self.assertTrue(linha["chave"].startswith("doi:"))
        self.assertTrue(linha["chave_titulo"].startswith("tit:"))

    def test_o_ano_separa_o_resumo_de_congresso_do_artigo(self):
        """Saem com o mesmo titulo em anos diferentes.

        Junta-los esconderia um dos dois -- e o ano entra na chave de
        titulo justamente por isso.
        """
        self.assertTrue(self.gravar({"title": "Mood and performance", "year": 2023}))
        self.assertTrue(self.gravar({"title": "Mood and performance", "year": 2024}))
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM biblioteca_item"), 2)

    def test_dois_dois_artigos_diferentes_continuam_dois(self):
        self.assertTrue(self.gravar({"title": "Humor em nadadores", "year": 2024}))
        self.assertTrue(self.gravar({"title": "Humor em ciclistas", "year": 2024}))
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM biblioteca_item"), 2)


class TestLimparOQueJaEntrouRepetido(BaseBiblioteca):
    """O conserto na gravacao nao desfaz o que ja esta no banco.

    E refazer o acervo inteiro nao e resposta: sao quarenta e cinco buscas
    e alguns minutos.
    """

    def setUp(self):
        super().setUp()
        biblioteca.instalar(self.db)
        self.bid = self.db.scalar("SELECT id FROM biblioteca")

    def antigo(self, chave, titulo, ano, doi=None, segmento=None, abstract=None):
        """Item como a versao ANTIGA gravava: sem `chave_titulo`."""
        self.db.execute(
            "INSERT INTO biblioteca_item (biblioteca_id, chave, segmento, title,"
            "        year, doi, abstract) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.bid, chave, segmento, titulo, ano, doi, abstract))
        self.db.conn.commit()

    def test_junta_o_que_a_versao_antiga_duplicou(self):
        self.antigo("doi:10.1000/a", "Mood in swimmers", 2024, doi="10.1000/a",
                    segmento="Natação")
        self.antigo("tit:mood in swimmers|2024", "Mood in swimmers", 2024,
                    segmento="Handebol")
        r = biblioteca.limpar_duplicatas(self.db, "humor_esporte")
        self.assertEqual(r["juntados"], 1)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM biblioteca_item"), 1)

    def test_o_registro_mais_completo_e_o_que_fica(self):
        """Ficar com o pior seria trocar o DOI por nada.

        Com DOI primeiro; entre os que tem, o que tem resumo.
        """
        self.antigo("tit:x|2024", "Mood in swimmers", 2024)               # sem DOI
        self.antigo("doi:10.1000/a", "Mood in swimmers", 2024, doi="10.1000/a",
                    abstract="Mood was measured.")
        biblioteca.limpar_duplicatas(self.db, "humor_esporte")
        linha = self.db.dicts("SELECT doi, abstract FROM biblioteca_item")[0]
        self.assertEqual(linha["doi"], "10.1000/a")
        self.assertTrue(linha["abstract"])

    def test_os_segmentos_dos_dois_sobrevivem(self):
        # um item achado em Natação por uma base e em Handebol por outra
        # pertence aos dois, e a fusao nao pode perder metade
        self.antigo("doi:10.1000/a", "Mood in swimmers", 2024, doi="10.1000/a",
                    segmento="Natação")
        self.antigo("tit:x|2024", "Mood in swimmers", 2024, segmento="Handebol")
        biblioteca.limpar_duplicatas(self.db, "humor_esporte")
        self.assertEqual(self.db.scalar("SELECT segmento FROM biblioteca_item"),
                         "Handebol; Natação")

    def test_rodar_duas_vezes_da_o_mesmo(self):
        self.antigo("doi:10.1000/a", "Mood in swimmers", 2024, doi="10.1000/a")
        self.antigo("tit:x|2024", "Mood in swimmers", 2024)
        biblioteca.limpar_duplicatas(self.db, "humor_esporte")
        segunda = biblioteca.limpar_duplicatas(self.db, "humor_esporte")
        self.assertEqual(segunda["juntados"], 0)

    def test_acervo_limpo_nao_perde_nada(self):
        self.antigo("doi:10.1000/a", "Humor em nadadores", 2024, doi="10.1000/a")
        self.antigo("doi:10.1000/b", "Humor em ciclistas", 2023, doi="10.1000/b")
        r = biblioteca.limpar_duplicatas(self.db, "humor_esporte")
        self.assertEqual(r["juntados"], 0)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM biblioteca_item"), 2)

    def test_a_limpeza_preenche_a_chave_que_faltava(self):
        # item da versao antiga nao tem `chave_titulo`; sem preenche-la, a
        # proxima gravacao duplicaria de novo pelo mesmo motivo
        self.antigo("doi:10.1000/a", "Humor em nadadores", 2024, doi="10.1000/a")
        biblioteca.limpar_duplicatas(self.db, "humor_esporte")
        self.assertTrue(self.db.scalar("SELECT chave_titulo FROM biblioteca_item"))

    def test_atualizar_limpa_antes_de_trazer_mais(self):
        """Acervo com duplicata recebendo artigo novo so acumula duplicata."""
        fonte = (ROOT / "scripts" / "lape" / "biblioteca.py").read_text(encoding="utf-8")
        corpo = fonte[fonte.index("def atualizar("):fonte.index("def limpar_duplicatas(")]
        self.assertIn("limpar_duplicatas(db, code)", corpo)
        self.assertIn("repetidos_juntados", corpo)


class TestOQueATelaLe(BaseBiblioteca):

    def setUp(self):
        super().setUp()
        biblioteca.instalar(self.db)
        bid = self.db.scalar("SELECT id FROM biblioteca")
        for i, (titulo, ano, seg, doi, pais) in enumerate((
                ("Humor em handebol", 2024, "Handebol", "10.1/a", '["Hungria"]'),
                ("Humor em natação", 2023, "Natação", "10.1/b", '["Brasil"]'),
                ("Humor em nadadores brasileiros", 2025, "Natação", None, '["Brasil"]'),
        ), 1):
            self.db.execute(
                "INSERT INTO biblioteca_item (biblioteca_id, chave, segmento, title,"
                "        year, doi, paises) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (bid, f"k{i}", seg, titulo, ano, doi, pais))
        self.db.conn.commit()

    def test_o_segmento_vazio_aparece_com_zero(self):
        """Some-lo faria a tela dizer que ninguem estuda humor no remo.

        O certo e que a busca nao achou -- que e outra coisa, e e a que
        merece uma busca melhor.
        """
        p = biblioteca.panorama(self.db, "humor_esporte")
        nomes = {s["segmento"] for s in p["segmentos"]}
        self.assertEqual(nomes, {nome for nome, _ in biblioteca.ESPORTES})
        remo = next(s for s in p["segmentos"] if s["segmento"] == "Remo e canoagem")
        self.assertEqual(remo["n"], 0)

    def test_o_segmento_aparece_uma_vez_e_nao_uma_por_base(self):
        """Ha uma busca por segmento POR BASE, e o segmento e um so.

        Sem juntar, a tela listava "Handebol" tres vezes seguidas, e o que
        era divisao por modalidade virava lista com repeticao.
        """
        p = biblioteca.panorama(self.db, "humor_esporte")
        nomes = [s["segmento"] for s in p["segmentos"]]
        self.assertEqual(len(nomes), len(set(nomes)))
        self.assertEqual(len(nomes), len(biblioteca.ESPORTES))

    def test_a_data_do_segmento_e_a_mais_recente_das_bases(self):
        """Se a PubMed rodou hoje e a Scopus na semana passada, vale hoje.

        Dizer "semana passada" faria o acervo parecer mais velho do que e.
        """
        self.db.execute(
            "UPDATE biblioteca_busca SET rodada_em = '2026-01-01'"
            " WHERE segmento = 'Handebol' AND base = ?", (biblioteca.SCOPUS,))
        self.db.execute(
            "UPDATE biblioteca_busca SET rodada_em = '2026-09-11'"
            " WHERE segmento = 'Handebol' AND base = ?", (biblioteca.PUBMED,))
        self.db.conn.commit()
        p = biblioteca.panorama(self.db, "humor_esporte")
        handebol = next(s for s in p["segmentos"] if s["segmento"] == "Handebol")
        self.assertEqual(handebol["rodada_em"], "2026-09-11")

    def test_o_erro_do_segmento_diz_qual_base_falhou(self):
        # erro solto nao diz onde procurar
        self.db.execute(
            "UPDATE biblioteca_busca SET erro = 'cota estourada'"
            " WHERE segmento = 'Handebol' AND base = ?", (biblioteca.SCOPUS,))
        self.db.conn.commit()
        p = biblioteca.panorama(self.db, "humor_esporte")
        handebol = next(s for s in p["segmentos"] if s["segmento"] == "Handebol")
        self.assertIn("Scopus", handebol["erro"])
        self.assertIn("cota estourada", handebol["erro"])

    def test_o_panorama_conta_o_que_da_para_ler_hoje(self):
        p = biblioteca.panorama(self.db, "humor_esporte")
        self.assertEqual(p["total"], 3)
        self.assertEqual(p["com_doi"], 2)

    def test_a_busca_em_texto_procura_titulo_e_autor(self):
        achado = biblioteca.listar(self.db, "humor_esporte", busca="nadadores")
        self.assertEqual(len(achado["itens"]), 1)

    def test_cada_item_ja_vem_com_os_links(self):
        achado = biblioteca.listar(self.db, "humor_esporte", segmento="Handebol")
        item = achado["itens"][0]
        self.assertTrue(item["links"])
        self.assertEqual(item["direto"], "https://doi.org/10.1/a")

    def test_os_paises_saem_da_afiliacao(self):
        p = biblioteca.panorama(self.db, "humor_esporte")
        contagem = {x["pais"]: x["n"] for x in p["paises"]}
        self.assertEqual(contagem, {"Brasil": 2, "Hungria": 1})

    def test_acervo_que_nao_existe_da_erro_e_nao_lista_vazia(self):
        # lista vazia seria indistinguivel de acervo ainda nao atualizado
        with self.assertRaises(ValueError):
            biblioteca.listar(self.db, "nao_existe")


class TestOMapeamentoAnalitico(BaseBiblioteca):
    """As contas sao as MESMAS do painel da producao, e nao uma copia.

    Uma segunda implementacao de mediana movel divergiria da primeira no
    dia em que alguem corrigisse uma das duas, e o sistema passaria a ter
    duas definicoes de "curva legivel" -- uma para a producao do
    laboratorio e outra para a literatura -- sem nada na tela dizendo isso.
    """

    def setUp(self):
        super().setUp()
        biblioteca.instalar(self.db)
        self.bid = self.db.scalar("SELECT id FROM biblioteca")

    def artigo(self, ano, segmento="Handebol", paises=("Brasil",), autores="A B; C D"):
        import json
        n = self.db.scalar("SELECT COUNT(*) FROM biblioteca_item") or 0
        self.db.execute(
            "INSERT INTO biblioteca_item (biblioteca_id, chave, segmento, title,"
            "        year, authors, paises) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.bid, f"x{n}", segmento, f"Estudo {n}", ano, autores,
             json.dumps(list(paises), ensure_ascii=False)))
        self.db.conn.commit()

    def test_os_limiares_nao_sao_redeclarados(self):
        """Uma segunda copia de "0,8" divergiria da primeira."""
        fonte = (ROOT / "scripts" / "lape" / "biblioteca.py").read_text(encoding="utf-8")
        self.assertNotIn("RUIDO_ALTO = ", fonte)
        self.assertNotIn("MIN_ANOS = ", fonte)
        self.assertIn("analise.RUIDO_ALTO", fonte)
        self.assertIn("analise.MIN_ANOS_COM_DADO", fonte)

    def test_a_serie_nao_passa_pelo_filtro_duas_vezes(self):
        """`sinal_e_ruido` ja aplica a mediana movel por dentro.

        Filtrar antes de chama-la daria uma curva mais lisa do que o dado
        permite -- menos ruido medido e menos inflexoes do que existem --,
        e o campo pareceria mais estavel do que e.
        """
        fonte = (ROOT / "scripts" / "lape" / "biblioteca.py").read_text(encoding="utf-8")
        corpo = fonte[fonte.index("def _curva("):fonte.index("def analitico(")]
        self.assertNotIn("mediana_movel", corpo)
        self.assertIn("analise.sinal_e_ruido(serie)", corpo)

    def test_acervo_sem_ano_diz_por_que_nao_da_para_mapear(self):
        # cartao vazio faria quem olha concluir que o assunto nao existe
        self.artigo(None)
        a = biblioteca.analitico(self.db, "humor_esporte")
        self.assertTrue(a["vazio"])
        self.assertIn("ano", a["porque"])

    def test_a_curva_traz_derivadas_ruido_e_inflexoes(self):
        for ano in range(2012, 2026):
            for _ in range(1 + (ano % 4)):
                self.artigo(ano)
        a = biblioteca.analitico(self.db, "humor_esporte")
        g = a["geral"]
        for chave in ("suave", "velocidade", "aceleracao", "ruido", "inflexoes",
                      "tendencia", "faixa"):
            with self.subTest(chave=chave):
                self.assertIn(chave, g)
        self.assertEqual(len(g["velocidade"]), len(g["suave"]))

    def test_serie_curta_nao_ganha_inflexao_nem_curva(self):
        """Duas inflexoes sobre dois pontos seriam desenho, nao achado."""
        self.artigo(2024)
        self.artigo(2025)
        a = biblioteca.analitico(self.db, "humor_esporte")
        self.assertFalse(a["geral"]["legivel"])
        self.assertEqual(a["geral"]["inflexoes"], [])
        self.assertTrue(a["geral"]["porque"])

    def test_o_recorte_por_ano_deixa_a_literatura_antiga_de_fora(self):
        """O POMS de 65 itens e outro instrumento, e a populacao e outra."""
        self.artigo(1978)
        self.artigo(2024)
        a = biblioteca.analitico(self.db, "humor_esporte")
        self.assertEqual(a["total"], 2)
        self.assertEqual(a["no_recorte"], 1)

    def test_o_pais_vem_da_afiliacao_e_leva_os_artigos(self):
        self.artigo(2024, paises=("Brasil", "Espanha"))
        self.artigo(2024, paises=("Brasil",))
        a = biblioteca.analitico(self.db, "humor_esporte")
        contagem = {p["pais"]: p["n"] for p in a["paises"]["todos"]}
        self.assertEqual(contagem, {"Brasil": 2, "Espanha": 1})
        brasil = next(p for p in a["paises"]["todos"] if p["pais"] == "Brasil")
        self.assertEqual(len(brasil["artigos"]), 2)

    def test_artigo_sem_pais_e_contado_a_parte_e_nao_somem(self):
        # "sem pais" nao e "sem importancia": e o que a base nao trouxe
        self.artigo(2024, paises=())
        a = biblioteca.analitico(self.db, "humor_esporte")
        self.assertEqual(a["paises"]["sem_pais"], 1)

    def test_a_rede_avisa_que_os_nos_sao_grafias_e_nao_pessoas(self):
        """Uma rede apresentada como verdade sobre pessoas, construida
        sobre grafias, e uma afirmacao que o dado nao sustenta."""
        for _ in range(3):
            self.artigo(2024, autores="Andrade A; Vilarino GT")
        a = biblioteca.analitico(self.db, "humor_esporte")
        self.assertIn("grafias", a["rede"]["ressalva"])
        self.assertTrue(a["rede"]["nos"])

    def test_a_rede_so_liga_quem_assina_junto_o_bastante(self):
        # um par que dividiu UM artigo nao e colaboracao, e coincidencia
        self.artigo(2024, autores="Solo X; Outro Y")
        a = biblioteca.analitico(self.db, "humor_esporte")
        self.assertEqual(a["rede"]["arestas"], [])

    def test_o_triangulo_cruza_o_que_o_acervo_sustenta(self):
        """Construto x intervencao x desfecho exigiria ler os metodos.

        Titulo e resumo nao dizem isso de maneira confiavel, e prometer a
        triangulacao completa a partir do resumo seria dar rigor de
        fachada a um palpite.
        """
        self.artigo(2024, segmento="Handebol", paises=("Brasil",))
        a = biblioteca.analitico(self.db, "humor_esporte")
        self.assertEqual(a["triangulo"]["eixo_y"], "modalidade")
        self.assertEqual(a["triangulo"]["eixo_x"], "país")

    def test_a_arvore_reparte_as_modalidades_sem_perder_nenhuma(self):
        for ano in range(2015, 2026):
            self.artigo(ano, segmento="Handebol")
        self.artigo(2024, segmento="Natação")
        a = biblioteca.analitico(self.db, "humor_esporte")
        d = a["decisao"]
        somado = d["curtos"]["n"] + d["ruidosos"]["n"] + d["viraram"]["n"] + d["lisos"]["n"]
        self.assertEqual(somado, d["total"])

    def test_a_arvore_diz_QUAIS_modalidades_cairam_de_cada_lado(self):
        # o numero sozinho manda a pessoa procurar na mao quais sao
        self.artigo(2024, segmento="Natação")
        a = biblioteca.analitico(self.db, "humor_esporte")
        self.assertIn("Natação", a["decisao"]["curtos"]["quais"])


class TestOQueABaseDeclara(BaseBiblioteca):
    """Desenho e intervencao saem do que a BASE declara.

    Dizer "ensaio randomizado" porque o resumo tem a palavra "randomized"
    erraria justamente nos artigos que DISCUTEM randomizacao sem serem
    randomizados. Tipo de publicacao e descritor MeSH sao curadoria da
    PubMed, feita por indexador humano.
    """

    def test_o_desenho_e_um_so_e_o_mais_forte(self):
        """Um artigo tem UM desenho.

        "Meta-analise e tambem transversal" nao e frase sobre metodo, e
        somar as duas contagens faria o total dos desenhos passar do total
        de artigos -- o que deixa qualquer percentual sem sentido.
        """
        lido = biblioteca.classificar({
            "pub_types": "Journal Article; Meta-Analysis",
            "keywords": "Cross-Sectional Studies; Cohort Studies"})
        self.assertEqual(lido["desenho"], "Meta-análise")

    def test_o_ensaio_ganha_do_transversal(self):
        lido = biblioteca.classificar({
            "pub_types": "Journal Article; Randomized Controlled Trial",
            "keywords": "Cross-Sectional Studies"})
        self.assertEqual(lido["desenho"], "Ensaio randomizado")

    def test_a_intervencao_pode_ser_varias(self):
        # um ensaio compara treino resistido com mindfulness, e e dos dois
        lido = biblioteca.classificar({
            "pub_types": "", "keywords": "Resistance Training; Mindfulness"})
        self.assertIn("Treinamento resistido", lido["intervencao"])
        self.assertIn("Mindfulness e meditação", lido["intervencao"])

    def test_sem_curadoria_nao_se_chuta(self):
        """Artigo da Scopus vem sem tipo e sem descritor.

        Marca-lo como transversal por omissao encheria o acervo de um
        desenho que ninguem declarou.
        """
        lido = biblioteca.classificar({"pub_types": None, "keywords": None})
        self.assertIsNone(lido["desenho"])
        self.assertIsNone(lido["intervencao"])

    def test_a_leitura_nao_olha_o_resumo(self):
        # a palavra no resumo nao vale: "we did not randomize" viraria
        # ensaio randomizado
        lido = biblioteca.classificar({
            "pub_types": "Journal Article", "keywords": "",
            "abstract": "This was not a randomized controlled trial.",
            "title": "A systematic review is needed"})
        self.assertIsNone(lido["desenho"])

    def test_todos_os_tipos_de_publicacao_sao_guardados(self):
        """O primeiro PT e quase sempre "Journal Article", que nao diz nada.

        Os que dizem vem depois, e eram descartados por `_primeiro`.
        """
        from lape import referencias
        medline = ("PMID- 1\nTI  - Um estudo.\nPT  - Journal Article\n"
                   "PT  - Randomized Controlled Trial\nDP  - 2024\n\n")
        r = referencias.ler_nbib(medline)[0]
        self.assertIn("Randomized Controlled Trial", r["pub_types"])

    def test_o_cru_fica_guardado_para_reclassificar_sem_rede(self):
        """Quando o vocabulario ganha um termo, o acervo se atualiza em
        segundos -- e nao em quarenta e cinco buscas."""
        biblioteca.instalar(self.db)
        bid = self.db.scalar("SELECT id FROM biblioteca")
        self.db.execute(
            "INSERT INTO biblioteca_item (biblioteca_id, chave, title, year,"
            "        pub_types, keywords) VALUES (?, 'k1', 'Um estudo', 2024, ?, ?)",
            (bid, "Journal Article; Meta-Analysis", "Mindfulness"))
        self.db.conn.commit()
        r = biblioteca.reclassificar(self.db, "humor_esporte")
        self.assertEqual(r["mudaram"], 1)
        linha = self.db.dicts("SELECT desenho, intervencao FROM biblioteca_item")[0]
        self.assertEqual(linha["desenho"], "Meta-análise")
        self.assertEqual(linha["intervencao"], "Mindfulness e meditação")

    def test_o_sem_leitura_sai_a_parte_e_nao_vira_outros(self):
        itens = [{"id": 1, "desenho": "Coorte"}, {"id": 2, "desenho": None},
                 {"id": 3, "desenho": None}]
        r = biblioteca._contar(itens, "desenho", biblioteca.DESENHOS)
        self.assertEqual(r["sem_leitura"], 2)
        self.assertEqual(r["com_leitura"], 1)
        rotulos = [x["rotulo"] for x in r["todos"]]
        self.assertNotIn("Outros", rotulos)
        self.assertNotIn(biblioteca.NAO_CLASSIFICADO, rotulos)


class TestOEspacoTempo(BaseBiblioteca):

    def test_o_quadro_do_ano_e_acumulado(self):
        """O mapa de um ano so pisca.

        A maior parte dos paises publica um artigo a cada tres anos, e um
        mapa que acende e apaga nao se le.
        """
        itens = [{"id": 1, "year": 2020, "paises": ["Brasil"]},
                 {"id": 2, "year": 2022, "paises": ["Brasil", "Espanha"]}]
        r = biblioteca._espaco_tempo(itens, [2020, 2021, 2022])
        quadros = {q["ano"]: q for q in r["quadros"]}
        self.assertEqual(quadros[2020]["paises"], {"Brasil": 1})
        self.assertEqual(quadros[2021]["paises"], {"Brasil": 1})   # nao zera
        self.assertEqual(quadros[2022]["paises"], {"Brasil": 2, "Espanha": 1})

    def test_o_ano_a_ano_fica_do_lado_do_acumulado(self):
        # "quem estuda isso" e "quem passou a estudar isso" sao perguntas
        # diferentes, e a segunda diz para onde o campo esta indo
        itens = [{"id": 1, "year": 2020, "paises": ["Brasil"]}]
        r = biblioteca._espaco_tempo(itens, [2020, 2021])
        quadros = {q["ano"]: q for q in r["quadros"]}
        self.assertEqual(quadros[2020]["no_ano"], {"Brasil": 1})
        self.assertEqual(quadros[2021]["no_ano"], {})


class TestOGlobo(unittest.TestCase):
    """A projecao ortografica, e o que ela nao pode desenhar."""

    @classmethod
    def setUpClass(cls):
        cls.js = (ROOT / "scripts" / "lape" / "templates" / "charts.js").read_text(
            encoding="utf-8")
        inicio = cls.js.index("function globo(spec)")
        cls.corpo = cls.js[inicio:cls.js.index("function dendrograma(spec)")]

    def test_o_globo_esta_na_api(self):
        self.assertIn("globo: globo", self.js)

    def test_a_face_oculta_nao_e_desenhada(self):
        """Desenhar os dois lados sobrepostos poria o Brasil em cima da
        Indonesia, e o leitor nao teria como saber qual esta na frente."""
        self.assertIn("if (cosC < 0) return null;", self.corpo)

    def test_o_poligono_que_cruza_o_horizonte_vira_varios_tracos(self):
        """Ligar o ultimo ponto visivel ao primeiro do outro lado
        desenharia uma corda atravessando o planeta."""
        self.assertIn("partes.push(atual)", self.corpo)
        self.assertIn("parte.length === anel.length", self.corpo)

    def test_o_svg_tem_tamanho(self):
        """Sem largura e altura, o SVG ocupa zero e os trezentos caminhos
        ficam no DOM sem aparecer -- um grafico invisivel que nao da erro."""
        self.assertIn('svg.setAttribute("width", W)', self.corpo)
        self.assertIn('svg.setAttribute("height", H)', self.corpo)

    def test_a_magnitude_e_um_matiz_so(self):
        # cor por categoria num mapa de quantidade e o erro classico
        self.assertIn("--accent-strong", self.corpo)
        self.assertNotIn("serie(", self.corpo)

    def test_pais_sem_registro_fica_sem_tinta(self):
        # zero nao e o tom mais claro, e a ausencia de dado
        self.assertIn('n ? "color-mix', self.corpo)

    def test_o_contorno_vem_do_campo_que_existe(self):
        # `d` ja e lista de aneis de [lon, lat]: sao as coordenadas cruas,
        # e e o que permite reprojetar para a esfera
        self.assertIn("(pais.d || [])", self.corpo)


class TestOMovimentoRespeitaAPreferencia(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")

    def test_o_giro_tem_guarda_propria(self):
        """A bandeira tem guarda no CSS; o giro e um relogio em JavaScript.

        Uma animacao que o CSS nao ve e uma animacao que a preferencia de
        acessibilidade nao alcanca.
        """
        self.assertIn("MENOS_MOVIMENTO", self.tela)
        self.assertIn("if (MENOS_MOVIMENTO) return;", self.tela)

    def test_a_bandeira_para_de_tremer(self):
        # a animacao mora no tema, que as duas telas usam -- a guarda com ela
        tema = (ROOT / "scripts" / "lape" / "templates" / "theme.css").read_text(
            encoding="utf-8")
        corpo = tema[tema.index("@keyframes tremular"):]
        self.assertIn("prefers-reduced-motion", corpo)
        self.assertIn(".tremula { animation: none; }", corpo)

    def test_aba_escondida_nao_gira(self):
        # girar um globo que ninguem ve gasta bateria para nada
        corpo = self.tela[self.tela.index("function girar()"):]
        self.assertIn("document.hidden", corpo[:600])

    def test_nenhuma_marca_de_grafico_treme(self):
        """Numero que balanca e numero dificil de ler.

        O enfeite fica longe do dado: a bandeira treme, a barra nao.
        """
        tema = (ROOT / "scripts" / "lape" / "templates" / "theme.css").read_text(
            encoding="utf-8")
        bloco = tema[tema.index("@keyframes tremular"):]
        bloco = bloco[:bloco.index("}\n}") + 3]
        for proibido in (".bar", ".mark", "svg", ".plot"):
            with self.subTest(alvo=proibido):
                self.assertNotIn(proibido, bloco)


class TestAsPortas(unittest.TestCase):

    def test_as_rotas_existem_com_o_perfil_certo(self):
        from lape import api
        achadas = {(m, padrao.split("(?P")[0], perfil)
                   for m, padrao, _f, perfil in api.ROUTES if "bibliotecas" in padrao}
        # ler e de quem tem leitura; sair para a rede quatorze vezes e da
        # coordenacao -- duas pessoas apertando ao mesmo tempo so gastariam
        # a cota da base
        perfis = {(m, perfil) for m, _p, perfil in achadas}
        self.assertIn(("GET", "leitura"), perfis)
        self.assertIn(("POST", "coordenacao"), perfis)

    def test_a_subida_instala_os_acervos_sem_sair_para_a_rede(self):
        """Instalar deixa as buscas prontas; quem sai e o botao.

        Sair para a PubMed a cada arranque do servico atrasaria a subida em
        minutos e gastaria a cota da base sem ninguem ter pedido.
        """
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        self.assertIn("_biblioteca.instalar(db)", fonte)
        self.assertNotIn("_biblioteca.atualizar(db", fonte)

    def test_a_tela_esta_na_ordem_do_menu(self):
        """Registrar em VIEWS nao basta: a ordem do menu e explicita.

        Uma tela que nao esteja na lista simplesmente nao aparece, e nao
        ha erro nenhum dizendo isso.
        """
        tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        ordem = tela[tela.index("const ORDER = ["):]
        ordem = ordem[:ordem.index("];")]
        self.assertIn('"biblioteca"', ordem)
        self.assertIn("VIEWS.biblioteca = {", tela)

    def test_a_tela_separa_o_link_direto_da_busca(self):
        # quem clica esperando o artigo e cai numa busca passa a conferir
        # todos os botoes, e ai nenhum serve
        tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        self.assertIn('l.tipo === "direto" ? " direto"', tela)
        self.assertIn(".bib-link.direto{", tela)

    def test_o_segmento_vazio_fica_na_tela_apagado(self):
        tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        self.assertIn('(s.n ? "" : " vazio")', tela)
        self.assertIn(".chip.vazio{", tela)

    def test_a_rota_da_analise_existe(self):
        from lape import api
        achadas = {(m, perfil) for m, padrao, _f, perfil in api.ROUTES
                   if "analise" in padrao and "biblioteca" in padrao}
        self.assertEqual(achadas, {("GET", "leitura")})

    def test_o_clique_no_mapa_recorta_por_pais_e_nao_por_texto(self):
        """"Itália" nao esta no titulo nem no resumo da maioria dos
        artigos feitos na Italia.

        Escrever o nome numa caixa de busca devolveria lista vazia com o
        nome do pais escrito em cima -- foi o defeito do mapa do painel.
        """
        tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        corpo = tela[tela.index("function cartaoDoMapa("):
                     tela.index("function cartaoDasLeituras(")]
        self.assertIn("BIB.pais = p.pais", corpo)
        self.assertNotIn("BIB.q =", corpo)

    def test_todo_recorte_desliga_no_mesmo_lugar(self):
        """Lista com 12 de 689 e nada explicando o sumico dos outros 677.

        Quem chegou pelo globo sabe por que; quem voltou dez minutos
        depois, nao -- e a pastilha e onde ele desliga.
        """
        tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        corpo = tela[tela.index('[["pais", "mapa"'):]
        # o fim e a linha que fecha o forEach, e nao o primeiro "});" -- que
        # aparece antes, dentro de `h("span", {...}))`
        corpo = corpo[:corpo.index("linhaDeBusca.push(chip);")]
        for recorte in ("pais", "desenho", "intervencao"):
            with self.subTest(recorte=recorte):
                self.assertIn(f'"{recorte}"', corpo)
        self.assertIn("BIB[x[0]] = null; show(\"biblioteca\")", corpo)

    def test_o_mapa_nao_gira_com_a_aba_escondida(self):
        # girar um mapa que ninguem ve e gastar bateria para nada
        tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        corpo = tela[tela.index("function girar()"):]
        corpo = corpo[:corpo.index("\n  }")]
        self.assertIn("document.hidden", corpo)

    def test_a_rede_usa_o_contrato_do_grafico(self):
        """Com os nomes errados o desenho nao da erro: calcula raio de
        `undefined` e escreve NaN no atributo, e o circulo some."""
        tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        corpo = tela[tela.index("function cartaoDaRede("):]
        corpo = corpo[:corpo.index("function cartaoDeArtigo(")]
        self.assertIn("source:", corpo)
        self.assertIn("weight:", corpo)
        self.assertNotIn("edges:", corpo)

    def test_a_tela_diz_que_nao_e_triagem(self):
        """A confusao com revisao sistematica custaria caro.

        Alguem trataria o acervo como "estudos incluidos" e citaria como
        se tivesse havido triagem -- que nao houve.
        """
        tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        self.assertIn("Não é triagem de revisão", tela)


if __name__ == "__main__":
    unittest.main(verbosity=2)
