#!/usr/bin/env python3
"""O que a coordenacao declara, e o que o sistema nao pode decidir sozinho.

    python3 -m unittest tests.test_cadastro -v

Quatro campos que estavam errados pelo mesmo motivo de fundo: o sistema
preenchia, por conta propria, coisas que so quem conhece o laboratorio
sabe. A linha de pesquisa oferecia opcoes que ninguem usa mais; o tipo de
estudo era texto livre, e texto livre nao classifica nada; qualquer nome
numa lista de autores virava integrante do laboratorio; e o indice h era
uma estimativa que se sobrescrevia sozinha por cima do numero conferido.
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import (indice_h, ingest_excel, linhas, mapping, metrics,  # noqa: E402
                  vinculo)
from lape.agents import curator  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "cad.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()


# ----------------------------------------------------------------------
# 1. Linhas de pesquisa
# ----------------------------------------------------------------------
class TestAsLinhasQueSairam(Base):

    def _instalar_as_antigas(self):
        for codigo, nome in (
            ("atividade_fisica_saude", "Atividade Física e Saúde"),
            ("exercicio_fibromialgia", "Exercício na saúde física e mental na Fibromialgia"),
            ("exercicio_cancer", "Exercício na saúde mental no tratamento do câncer"),
        ):
            self.db.upsert("research_lines", {"code": codigo, "name": nome, "active": 1},
                           conflict=("code",))
        self.db.conn.commit()

    def test_a_linha_renomeada_leva_junto_os_artigos(self):
        """Renomear nao pode soltar o que estava pendurado.

        Se a linha nova entrasse como registro novo em vez de renomear o
        existente, os artigos ficariam apontando para a linha velha e o
        painel mostraria a nova vazia -- com a producao toda no lugar
        errado e ninguem percebendo, porque as duas existem.
        """
        self._instalar_as_antigas()
        antiga = self.db.scalar(
            "SELECT id FROM research_lines WHERE code = 'exercicio_fibromialgia'")
        for titulo in ("Dor e exercício", "Sono na fibromialgia"):
            self.db.insert("articles", {"title": titulo, "title_key": titulo.lower(),
                                        "research_line_id": antiga})
        self.db.conn.commit()

        linhas.instalar(self.db)

        self.assertEqual(
            self.db.scalar("SELECT name FROM research_lines WHERE id = ?", (antiga,)),
            "Fibromialgia e doenças reumáticas")
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM articles WHERE research_line_id = ?",
                           (antiga,)), 2)

    def test_a_linha_que_saiu_da_lista_nao_e_apagada(self):
        """Apagar levaria junto a historia de quem publicou nela."""
        self._instalar_as_antigas()
        saiu = self.db.scalar(
            "SELECT id FROM research_lines WHERE code = 'atividade_fisica_saude'")
        self.db.insert("articles", {"title": "Caminhada e saúde", "title_key": "caminhada",
                                    "research_line_id": saiu})
        self.db.conn.commit()

        resultado = linhas.instalar(self.db, encerrar_as_que_sairam=True)

        self.assertEqual(
            self.db.scalar("SELECT active FROM research_lines WHERE id = ?", (saiu,)), 0)
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM articles WHERE research_line_id = ?",
                           (saiu,)), 1)
        fora = {d["nome"]: d["aponta"] for d in resultado["desativadas"]}
        self.assertIn("Atividade Física e Saúde", fora)
        self.assertEqual(fora["Atividade Física e Saúde"], {"Artigos": 1})

    def test_reiniciar_o_servidor_nao_encerra_linha_nenhuma(self):
        """`instalar` roda a cada subida.

        Uma linha que o laboratorio criou na tela nao pode sumir do
        seletor porque a maquina foi religada.
        """
        self.db.upsert("research_lines", {"code": "linha_da_casa",
                                          "name": "Linha criada na tela", "active": 1},
                       conflict=("code",))
        self.db.conn.commit()
        linhas.instalar(self.db)
        self.assertEqual(
            self.db.scalar("SELECT active FROM research_lines WHERE code = 'linha_da_casa'"), 1)

    def test_a_tela_so_oferece_linha_ativa(self):
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index("CACHE.lines ="):]
        trecho = trecho[:trecho.index("CACHE.articles")]
        self.assertIn("filter", trecho)
        self.assertIn("active", trecho)

    def test_o_valor_gravado_fora_da_lista_sobrevive_a_edicao(self):
        """Um seletor apaga o que nao reconhece, e salvar leva o dado junto.

        Vale para o artigo cuja linha de pesquisa foi encerrada e para o
        tipo de estudo digitado antes de o campo virar lista.
        """
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index('} else if (f.type === "select"){'):]
        trecho = trecho[:trecho.index('} else if (f.type === "checkbox")')]
        self.assertIn("fora da lista", trecho)


class TestOFormularioDeEdicao(Base):
    """A metade da correção que mora no navegador.

    O servidor já sabe editar por id e apagar com vazio, mas quem decide
    mandar o id e mandar o vazio é o formulário. Sem esta metade o
    servidor nunca recebe nem um nem outro, e o defeito continua igual --
    foi o que as mutações mostraram: revertendo só o formulário, todo
    teste de servidor continuava passando.
    """

    def setUp(self):
        super().setUp()
        self.html = (TEMPLATES / "app.html").read_text(encoding="utf-8")

    def test_o_campo_vazio_e_sempre_enviado(self):
        """Sem ele o servidor não distingue "apaguei" de "não veio".

        No cadastro de registro novo mandar o vazio não muda nada -- aquele
        caminho descarta vazio de qualquer jeito. Mandar sempre é o que faz
        o formulário de cima também apagar, quando descobre que o título já
        existe e a pessoa confirma que quer atualizar.
        """
        trecho = self.html[self.html.index("const payload = {};"):]
        trecho = trecho[:trecho.index("if (spec.extra)")]
        self.assertIn("payload[key] = value;", trecho)
        self.assertNotIn('if (value !== "")', trecho)

    def test_o_titulo_repetido_pergunta_antes_de_atualizar(self):
        """Gravar um título que já existe alterava outro registro em silêncio.

        Na importação de planilha isso é a regra certa; na tela é
        armadilha -- a pessoa acha que está criando, está editando, e o
        campo que ela esvaziou não some.
        """
        trecho = self.html[self.html.index("const gravar = async function"):]
        trecho = trecho[:trecho.index("let formulario")]
        self.assertIn("config.mesmoNome", trecho)
        self.assertIn("registro_id: achado.id", trecho)
        self.assertIn("confirm(", trecho)

    def test_a_ficha_aberta_manda_o_proprio_id(self):
        trecho = self.html[self.html.index("config.__carregar = function"):]
        trecho = trecho[:trecho.index("titulo.textContent")]
        self.assertIn("registro_id: row.id", trecho)

    def test_o_cadastro_novo_nao_entra_em_modo_de_edicao(self):
        """`row` nulo é o formulário em branco: não há id nem o que apagar."""
        trecho = self.html[self.html.index("config.__carregar = function"):]
        trecho = trecho[:trecho.index("titulo.textContent")]
        self.assertIn("row ?", trecho)

    def test_o_artigo_novo_recebe_codigo(self):
        """A coluna "ID" ficava vazia justamente nos artigos da tela."""
        from lape.ingest_excel import proximo_codigo

        for titulo, codigo in (("A", "LAPE-06"), ("B", "LAPE-09"), ("C", "LAPE-14")):
            self.db.insert("articles", {"title": titulo, "title_key": titulo.lower(),
                                        "internal_code": codigo})
        self.db.conn.commit()
        self.assertEqual(proximo_codigo(self.db), "LAPE-15")
        curator.register(self.db, "articles", {"Título": "Novo na tela", "Autores": "X"})
        self.assertEqual(self.db.scalar(
            "SELECT internal_code FROM articles WHERE title = 'Novo na tela'"), "LAPE-15")

    def test_o_codigo_digitado_manda_mais_que_a_sequencia(self):
        curator.register(self.db, "articles", {"Título": "Com código", "Autores": "X",
                                               "Código": "TCC-2026-1"})
        self.assertEqual(self.db.scalar(
            "SELECT internal_code FROM articles WHERE title = 'Com código'"), "TCC-2026-1")

    def test_o_codigo_de_um_artigo_nunca_muda(self):
        """"LAPE-14" citado num e-mail não pode passar a ser outro artigo."""
        curator.register(self.db, "articles", {"Título": "Estável", "Autores": "X"})
        alvo = self.db.scalar("SELECT id FROM articles WHERE title = 'Estável'")
        antes = self.db.scalar("SELECT internal_code FROM articles WHERE id = ?", (alvo,))
        curator.register(self.db, "articles", {"Título": "Estável", "Autores": "X; Y"})
        self.assertEqual(
            self.db.scalar("SELECT internal_code FROM articles WHERE id = ?", (alvo,)), antes)

    def test_a_exclusao_nao_depende_do_esquema_ter_cascata(self):
        """Tabela criada por versão anterior ficou com a chave em NO ACTION.

        `CREATE TABLE IF NOT EXISTS` nunca recria uma tabela que já existe
        para acrescentar `ON DELETE CASCADE` -- e num banco em uso desde
        antes da regra, apagar um artigo devolvia "FOREIGN KEY constraint
        failed": erro 500 na tela de quem só queria tirar uma ficha
        repetida.
        """
        import sqlite3
        import tempfile as _tmp
        from pathlib import Path as _Path

        from lape.db import Database as _Db

        caminho = _Path(_tmp.mkdtemp()) / "velho.sqlite"
        cru = sqlite3.connect(caminho)
        cru.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE articles (id INTEGER PRIMARY KEY, title TEXT NOT NULL,
              title_key TEXT UNIQUE NOT NULL, status TEXT DEFAULT 'em_producao');
            CREATE TABLE article_authors (
              article_id INTEGER NOT NULL REFERENCES articles(id),
              member_id INTEGER, author_name TEXT NOT NULL,
              author_order INTEGER NOT NULL DEFAULT 1,
              PRIMARY KEY (article_id, author_order));
            CREATE TABLE events (id INTEGER PRIMARY KEY, title TEXT,
              article_id INTEGER REFERENCES articles(id));
            INSERT INTO articles (title, title_key) VALUES ('X','x');
            INSERT INTO article_authors (article_id, author_name) VALUES (1,'Andrade');
            INSERT INTO events (title, article_id) VALUES ('Reunião', 1);
        """)
        cru.commit()
        cru.close()
        antigo = _Db(caminho)
        self.addCleanup(antigo.close)
        antigo.migrate()
        self.assertEqual(
            [dict(r)["on_delete"] for r in
             antigo.query("PRAGMA foreign_key_list(article_authors)")],
            ["NO ACTION"], "o cenário do teste deixou de ser o cenário real")

        levados = antigo.apagar_em_cascata("articles", 1)
        self.assertEqual(antigo.scalar("SELECT COUNT(*) FROM articles"), 0)
        self.assertEqual(antigo.scalar("SELECT COUNT(*) FROM article_authors"), 0)
        self.assertEqual(levados.get("article_authors"), 1)
        # coluna opcional: a reunião aconteceu, e continua tendo acontecido
        self.assertEqual(antigo.scalar("SELECT COUNT(*) FROM events"), 1)
        self.assertIsNone(antigo.scalar("SELECT article_id FROM events"))

    def test_ha_como_excluir_um_artigo(self):
        """Sem exclusão, as cópias que o defeito criou não saem da tela."""
        trecho = self.html[self.html.index("VIEWS.artigos = crudView"):]
        trecho = trecho[:trecho.index("columns: [")]
        self.assertIn('"/api/articles/"', trecho)
        self.assertIn('"DELETE"', trecho)
        self.assertIn("confirm(", trecho)
        self.assertIn('can("coordenacao")', trecho)


class TestOCodigoInternoRepetido(Base):
    """Uma célula errada derrubava a importação inteira.

    `internal_code` é UNIQUE -- e tem de ser, porque "LAPE-14" citado num
    e-mail precisa apontar para um artigo só. Quando a planilha trazia um
    código que já era de outro artigo, o `INSERT` estourava
    `IntegrityError: UNIQUE constraint failed: articles.internal_code`, o
    curador morria no meio e NENHUM artigo entrava -- nem os duzentos
    corretos. E a mensagem citava uma coluna do banco, não os dois artigos.
    """

    def _codigos(self):
        return dict(self.db.conn.execute(
            "SELECT title, internal_code FROM articles ORDER BY id").fetchall())

    def test_a_planilha_com_codigo_de_outro_artigo_nao_derruba_a_importacao(self):
        curator.register(self.db, "articles", {"Título": "Dono", "Código": "LAPE-14"})
        with contextlib.redirect_stdout(io.StringIO()):
            ingest_excel.ingest_articles(self.db, [
                {"title": "Repetido", "internal_code": "LAPE-14"},
                {"title": "Seguinte", "internal_code": "LAPE-99"},
            ])
        codigos = self._codigos()
        self.assertEqual(codigos["Dono"], "LAPE-14")
        # a linha seguinte entrou: e ela que o IntegrityError levava junto
        self.assertEqual(codigos["Seguinte"], "LAPE-99")

    def test_reimportar_a_mesma_planilha_nao_apaga_os_codigos(self):
        """O artigo não é repetição de si mesmo.

        A primeira versão da conferência comparava o código contra
        QUALQUER artigo -- inclusive o próprio, que a linha estava
        atualizando. Reimportar a planilha, que é a operação mais comum do
        curador, limpava o código de todos os dezenove artigos.
        """
        linhas = [{"title": "Primeiro", "internal_code": "LAPE-06"},
                  {"title": "Segundo", "internal_code": "LAPE-09"}]
        ingest_excel.ingest_articles(self.db, linhas)
        with contextlib.redirect_stdout(io.StringIO()) as saida:
            ingest_excel.ingest_articles(self.db, linhas)
        self.assertEqual(self._codigos(), {"Primeiro": "LAPE-06", "Segundo": "LAPE-09"})
        self.assertNotIn("repetido", saida.getvalue())

    def test_regravar_pela_tela_com_o_proprio_codigo_nao_e_repeticao(self):
        """Sem registro_id, quem identifica a ficha é o título."""
        curator.register(self.db, "articles", {"Título": "Único", "Código": "LAPE-14"})
        curator.register(self.db, "articles", {"Título": "Único", "Código": "LAPE-14",
                                               "Revista": "Motriz"})
        self.assertEqual(self._codigos(), {"Único": "LAPE-14"})

    def test_o_artigo_da_linha_repetida_entra_sem_codigo(self):
        """Sem código, e não com "o próximo livre".

        Um código inventado aqui passaria a valer como se fosse do
        laboratório -- alguém o citaria num e-mail -- e taparia o erro de
        digitação em vez de mostrá-lo.
        """
        curator.register(self.db, "articles", {"Título": "Dono", "Código": "LAPE-14"})
        with contextlib.redirect_stdout(io.StringIO()):
            ingest_excel.ingest_articles(self.db, [
                {"title": "Repetido", "internal_code": "LAPE-14"}])
        self.assertIsNone(self._codigos()["Repetido"])

    def test_duas_linhas_da_mesma_planilha_com_o_mesmo_codigo(self):
        """A colisão não precisa de um artigo antigo para acontecer."""
        with contextlib.redirect_stdout(io.StringIO()):
            ingest_excel.ingest_articles(self.db, [
                {"title": "Primeira", "internal_code": "LAPE-07"},
                {"title": "Segunda", "internal_code": "LAPE-07"},
            ])
        codigos = self._codigos()
        self.assertEqual(codigos["Primeira"], "LAPE-07")
        self.assertIsNone(codigos["Segunda"])

    def test_o_espaco_em_branco_conta_como_repeticao(self):
        """" LAPE-09 " chega da planilha e o clean_text apara -- então colide."""
        curator.register(self.db, "articles", {"Título": "Dono", "Código": "LAPE-09"})
        with contextlib.redirect_stdout(io.StringIO()):
            ingest_excel.ingest_articles(self.db, [
                {"title": "Com espaço", "internal_code": "  LAPE-09  "}])
        self.assertIsNone(self._codigos()["Com espaço"])

    def test_o_aviso_nomeia_os_dois_artigos_e_fica_no_log(self):
        """Quem lê o aviso precisa saber QUAL código e QUAIS artigos."""
        curator.register(self.db, "articles", {"Título": "Dono", "Código": "LAPE-14"})
        with contextlib.redirect_stdout(io.StringIO()) as saida:
            ingest_excel.ingest_articles(self.db, [
                {"title": "Repetido", "internal_code": "LAPE-14"}])
        impresso = saida.getvalue()
        for pedaco in ("LAPE-14", "Dono", "Repetido"):
            self.assertIn(pedaco, impresso)
        registrado = self.db.scalar(
            "SELECT message FROM ingest_log WHERE status = 'aviso'"
            " ORDER BY id DESC LIMIT 1")
        self.assertIsNotNone(registrado)
        for pedaco in ("LAPE-14", "Dono", "Repetido"):
            self.assertIn(pedaco, registrado)

    def test_a_tela_e_recusada_em_voz_alta_ao_cadastrar(self):
        """Quem está com o formulário aberto corrige agora.

        Gravar a ficha sem o código que a pessoa digitou seria pior: ela
        não veria, e o dado que ela declarou não estaria lá.
        """
        curator.register(self.db, "articles", {"Título": "Dono", "Código": "LAPE-14"})
        with self.assertRaises(ValueError) as caso:
            curator.register(self.db, "articles",
                             {"Título": "Novo na tela", "Código": "LAPE-14"})
        self.assertIn("LAPE-14", str(caso.exception))
        self.assertIn("Dono", str(caso.exception))
        self.assertIsNone(self.db.scalar(
            "SELECT 1 FROM articles WHERE title = 'Novo na tela'"))

    def test_a_tela_e_recusada_em_voz_alta_ao_editar(self):
        curator.register(self.db, "articles", {"Título": "Dono", "Código": "LAPE-14"})
        curator.register(self.db, "articles", {"Título": "Outro", "Código": "LAPE-15"})
        alvo = self.db.scalar("SELECT id FROM articles WHERE title = 'Outro'")
        with self.assertRaises(ValueError):
            curator.register(self.db, "articles", {"registro_id": alvo, "Título": "Outro",
                                                   "Código": "LAPE-14"})
        self.assertEqual(self._codigos()["Outro"], "LAPE-15")

    def test_editar_mantendo_o_proprio_codigo_continua_valendo(self):
        """A recusa não pode pegar o artigo no próprio código."""
        curator.register(self.db, "articles", {"Título": "Dono", "Código": "LAPE-14"})
        alvo = self.db.scalar("SELECT id FROM articles WHERE title = 'Dono'")
        curator.register(self.db, "articles", {"registro_id": alvo, "Título": "Dono",
                                               "Código": "LAPE-14", "Revista": "Motriz"})
        self.assertEqual(self.db.scalar(
            "SELECT journal FROM articles WHERE id = ?", (alvo,)), "Motriz")
        self.assertEqual(self.db.scalar(
            "SELECT internal_code FROM articles WHERE id = ?", (alvo,)), "LAPE-14")

    def test_a_sequencia_respeita_o_zero_da_frente(self):
        """Um laboratório que numera "LAPE-07" recebia "LAPE-8" de volta.

        A largura saía de `len(str(7))`, e o zero se perdia no `int`. Além
        de feio, o formato misturado é o que produz dois códigos para o
        mesmo número ("LAPE-08" e "LAPE-8") -- cada um livre para o UNIQUE,
        e os dois iguais para quem lê.
        """
        curator.register(self.db, "articles", {"Título": "Base", "Código": "LAPE-07"})
        self.assertEqual(ingest_excel.proximo_codigo(self.db), "LAPE-08")

    def test_a_sequencia_continua_do_maior_e_nao_da_quantidade(self):
        """Com uma lacuna no meio, contar os artigos devolveria um código já usado."""
        for codigo in ("LAPE-01", "LAPE-02", "LAPE-40"):
            curator.register(self.db, "articles",
                             {"Título": f"Artigo {codigo}", "Código": codigo})
        self.assertEqual(ingest_excel.proximo_codigo(self.db), "LAPE-41")


class TestOQueOAgenteNaoPodeInventar(Base):
    """Manuscrito em produção não tem DOI, e apagar é uma decisão.

    Os dois defeitos foram relatados juntos: "aparece o DOI e o link, só
    que esse artigo não foi publicado ainda [...] e quando eu apago,
    continua com DOI e com o link".
    """

    def test_manuscrito_nao_e_procurado_pelo_titulo_nas_bases(self):
        """Procurar o que não existe só pode achar outra coisa.

        Um manuscrito ainda em produção não tem registro em base nenhuma,
        então todo casamento por título ali é falso por construção -- e
        carimba o DOI, o periódico e o link de OUTRO artigo num trabalho
        que a equipe ainda está escrevendo.
        """
        from lape.agents import tracker

        chamadas = []

        def espiao(doi=None, title=None, mailto=None):
            chamadas.append({"doi": doi, "title": title})
            return None

        curator.register(self.db, "articles", {
            "Título": "Manuscrito em produção", "Autores": "Andrade"})
        curator.register(self.db, "articles", {
            "Título": "Artigo já publicado", "Autores": "Andrade",
            "Status": "Publicado", "Ano": "2025"})

        original = tracker.sources.best_metadata
        tracker.sources.best_metadata = espiao
        try:
            tracker.enrich(self.db, verbose=False)
        finally:
            tracker.sources.best_metadata = original

        procurados = [c["title"] for c in chamadas if c["title"]]
        self.assertIn("Artigo já publicado", procurados)
        self.assertNotIn("Manuscrito em produção", procurados)

    def test_manuscrito_com_doi_digitado_ainda_e_consultado(self):
        """O DOI que o laboratório digitou é legítimo em qualquer situação.

        Cortar a consulta inteira para quem não publicou tiraria também o
        caminho certo -- e um artigo aceito com DOI emitido ficaria sem
        periódico para sempre.
        """
        from lape.agents import tracker

        chamadas = []

        def espiao(doi=None, title=None, mailto=None):
            chamadas.append({"doi": doi, "title": title})
            return None

        curator.register(self.db, "articles", {
            "Título": "Em produção mas com DOI", "Autores": "Andrade", "DOI": "10.1/x"})
        original = tracker.sources.best_metadata
        tracker.sources.best_metadata = espiao
        try:
            tracker.enrich(self.db, verbose=False)
        finally:
            tracker.sources.best_metadata = original
        self.assertEqual([c["doi"] for c in chamadas], ["10.1/x"])
        self.assertEqual([c["title"] for c in chamadas], [None])

    def _artigo_com_doi(self):
        curator.register(self.db, "articles", {
            "Título": "Com DOI e link", "Autores": "Andrade",
            "DOI": "10.9/errado", "Link": "https://errado.org"})
        return self.db.scalar("SELECT id FROM articles WHERE title = 'Com DOI e link'")

    def test_o_campo_apagado_na_tela_nao_volta_no_enriquecimento(self):
        from lape.agents import tracker

        alvo = self._artigo_com_doi()
        curator.register(self.db, "articles", {
            "registro_id": alvo, "Título": "Com DOI e link", "Autores": "Andrade",
            "DOI": "", "Link": ""})
        tracker._fill_missing(self.db, alvo, {"doi": "10.1/palpite",
                                              "url": "https://palpite.org"})
        self.db.conn.commit()
        self.assertIsNone(self.db.scalar("SELECT doi FROM articles WHERE id = ?", (alvo,)))
        self.assertIsNone(self.db.scalar("SELECT url FROM articles WHERE id = ?", (alvo,)))

    def test_campo_que_ninguem_apagou_continua_sendo_preenchido(self):
        """A anotação não pode virar um freio geral no enriquecimento."""
        from lape.agents import tracker

        alvo = self._artigo_com_doi()
        curator.register(self.db, "articles", {
            "registro_id": alvo, "Título": "Com DOI e link", "Autores": "Andrade",
            "DOI": "", "Link": ""})
        tracker._fill_missing(self.db, alvo, {"journal": "Revista que faltava"})
        self.db.conn.commit()
        self.assertEqual(
            self.db.scalar("SELECT journal FROM articles WHERE id = ?", (alvo,)),
            "Revista que faltava")

    def test_digitar_o_valor_de_novo_desfaz_a_anotacao(self):
        alvo = self._artigo_com_doi()
        curator.register(self.db, "articles", {
            "registro_id": alvo, "Título": "Com DOI e link", "Autores": "Andrade",
            "DOI": "", "Link": ""})
        curator.register(self.db, "articles", {
            "registro_id": alvo, "Título": "Com DOI e link", "Autores": "Andrade",
            "DOI": "10.5/certo", "Link": ""})
        apagados = {r["field"] for r in self.db.dicts(
            "SELECT field FROM cleared_fields WHERE record_id = ?", (alvo,))}
        self.assertNotIn("doi", apagados)
        self.assertIn("url", apagados)


# ----------------------------------------------------------------------
# 2. Tipo de estudo
# ----------------------------------------------------------------------
class TestOTipoDeEstudo(Base):

    def test_as_doze_opcoes_declaradas(self):
        """A ordem tambem esta no teste, e nao so o conjunto.

        Os botoes de filtro da lista de artigos saem desta ordem. Ordenar
        por contagem faria um botao mudar de lugar quando alguem cadastra
        um artigo -- e quem clicou em "Revisao de escopo" na semana
        passada teria de procurar de novo.
        """
        self.assertEqual([r for _c, r, _g in mapping.DESENHOS_DE_ESTUDO], [
            "Ensaio clínico controlado e randomizado", "Estudo transversal",
            "Estudo de coorte", "Revisão sistemática", "Meta-análise",
            "Revisão de escopo", "Revisão narrativa", "Bibliometria",
            "Editorial", "Carta ao editor",
            "Comunicação curta", "Estudo de protocolo",
        ])

    def test_revisao_de_escopo_nao_cai_em_narrativa(self):
        """Era onde ela caia antes de existir na lista.

        Escopo tem protocolo proprio (PRISMA-ScR) e nao julga risco de
        vies. Contada como narrativa, o painel dizia narrativa onde havia
        escopo -- e a diferenca e justamente o que uma revisao de escopo
        se propoe a nao fazer.
        """
        for grafia in ("revisão de escopo", "Scoping Review", "scoping",
                       "revisão exploratória", "PRISMA-ScR"):
            with self.subTest(grafia=grafia):
                self.assertEqual(mapping.desenho_de_estudo(grafia),
                                 "Revisão de escopo")

    def test_bibliometria_tem_lugar_proprio(self):
        """Ela mede a LITERATURA, e nao o efeito de algo em pessoas."""
        # "Estudo bibliométrico" foi o rotulo por algumas horas. Continua
        # na lista de grafias de proposito: planilha que ja tenha esse
        # texto tem de cair no mesmo lugar, e nao virar um tipo a parte.
        for grafia in ("bibliometria", "Estudo bibliométrico",
                       "análise bibliométrica", "bibliometric analysis",
                       "cientometria", "scientometrics"):
            with self.subTest(grafia=grafia):
                self.assertEqual(mapping.desenho_de_estudo(grafia),
                                 "Bibliometria")

    def test_nenhuma_grafia_serve_a_dois_delineamentos(self):
        """Duas entradas disputando a mesma grafia: a primeira ganha.

        `ESTUDO_MAP` usa `setdefault`, entao a colisao nao estoura -- ela
        fica silenciosa, e o delineamento que perdeu passa a ser
        inalcancavel por aquela palavra. Este teste e o que faz a colisao
        falar.
        """
        from lape.mapping import norm_key

        # Colisao e a mesma grafia servindo a CODIGOS DIFERENTES. O rotulo
        # repetir uma das grafias do proprio delineamento e normal --
        # "Comunicação curta" e "comunicacao curta" dao a mesma chave, e
        # apontam para o mesmo lugar.
        visto: dict[str, str] = {}
        colisoes = []
        for codigo, rotulo, grafias in mapping.DESENHOS_DE_ESTUDO:
            for grafia in (rotulo,) + grafias:
                chave = norm_key(grafia)
                if chave in visto and visto[chave] != codigo:
                    colisoes.append(f"“{grafia}”: {visto[chave]} / {codigo}")
                visto.setdefault(chave, codigo)
        self.assertEqual(colisoes, [])

    def test_a_tela_oferece_exatamente_as_mesmas(self):
        """Duas listas que divergem sao pior do que uma lista so.

        A tela grava o rotulo direto; se ele nao existir no vocabulario, a
        importacao da planilha deixa de reconhecer o que a propria tela
        escreveu.
        """
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index("const DESENHO_OPTS"):]
        trecho = trecho[:trecho.index("];") + 2]
        for _codigo, rotulo, _grafias in mapping.DESENHOS_DE_ESTUDO:
            with self.subTest(desenho=rotulo):
                self.assertIn('"' + rotulo + '"', trecho)

    def test_as_grafias_do_mesmo_delineamento_viram_uma_so(self):
        for grafia in ("ECR", "rct", "Randomized Controlled Trial",
                       "ensaio clínico randomizado", "Ensaio Clinico Controlado e Randomizado"):
            with self.subTest(grafia=grafia):
                self.assertEqual(mapping.desenho_de_estudo(grafia),
                                 "Ensaio clínico controlado e randomizado")

    def test_o_que_nao_esta_na_lista_volta_intacto(self):
        """Trocar por vazio seria perder dado para ganhar arrumacao."""
        for texto in ("estudo piloto com adolescentes", "revisão integrativa"):
            with self.subTest(texto=texto):
                self.assertEqual(mapping.desenho_de_estudo(texto), texto)

    def test_o_campo_e_um_seletor_e_nao_texto_livre(self):
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index('field("Tipo de estudo"'):]
        trecho = trecho[:trecho.index("\n")+200]
        self.assertIn('"select"', trecho)
        self.assertIn("DESENHO_OPTS", trecho)

    def test_o_banco_acompanha_quando_o_rotulo_e_renomeado(self):
        """Renomear o rotulo sem tocar no banco deixa dois tipos na tela.

        "Estudo bibliometrico" foi rotulo por algumas horas e virou
        "Bibliometria". As linhas gravadas com o texto velho apareciam
        como um tipo A PARTE, com contagem propria, ao lado do tipo certo
        com zero: dois botoes para a mesma coisa, e a soma certa pelo
        motivo errado.
        """
        for titulo, tipo in (("A", "Estudo bibliométrico"),
                             ("B", "Bibliometria"),
                             ("C", "ECR")):
            curator.register(self.db, "articles",
                             {"Título": titulo, "Tipo de estudo": tipo})
        # grava o rotulo velho direto, por baixo do mapeador -- e o estado
        # em que um banco de ontem esta
        self.db.execute("UPDATE articles SET study_type = ?"
                        " WHERE title = ?", ("Estudo bibliométrico", "A"))
        self.db.conn.commit()

        mudadas = mapping.renormalizar_delineamentos(self.db)
        self.assertEqual([m["para"] for m in mudadas], ["Bibliometria"])
        tipos = {r["title"]: r["study_type"] for r in
                 self.db.dicts("SELECT title, study_type FROM articles")}
        self.assertEqual(tipos["A"], "Bibliometria")
        self.assertEqual(tipos["B"], "Bibliometria")
        self.assertEqual(tipos["C"], "Ensaio clínico controlado e randomizado")

    def test_a_renormalizacao_nao_encosta_no_que_alguem_escreveu(self):
        """Mesma regra de `desenho_de_estudo`, um nivel acima.

        "estudo piloto com adolescentes" nao esta na lista e e a unica
        descricao que existe daquele artigo. Trocar por vazio -- ou por um
        palpite -- e perder dado para ganhar arrumacao.
        """
        curator.register(self.db, "articles",
                         {"Título": "Z", "Tipo de estudo": "estudo piloto com adolescentes"})
        self.assertEqual(mapping.renormalizar_delineamentos(self.db), [])
        self.assertEqual(
            self.db.scalar("SELECT study_type FROM articles WHERE title = 'Z'"),
            "estudo piloto com adolescentes")

    def test_rodar_duas_vezes_nao_muda_mais_nada(self):
        """A subida roda isto sempre -- na segunda tem de ficar calada."""
        # pelo `register`, e nao por INSERT cru: o `title_key` sai de la, e
        # sem ele o banco recusa a linha
        curator.register(self.db, "articles", {"Título": "Y"})
        self.db.execute("UPDATE articles SET study_type = ? WHERE title = ?",
                        ("scoping review", "Y"))
        self.db.conn.commit()
        self.assertEqual(len(mapping.renormalizar_delineamentos(self.db)), 1)
        self.assertEqual(mapping.renormalizar_delineamentos(self.db), [])

    def test_a_subida_reaplica_o_vocabulario(self):
        """Se nao rodar na subida, quem nunca reimporta planilha nao vê."""
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        self.assertIn("renormalizar_delineamentos(db)", fonte)

    def test_a_lista_de_artigos_tem_um_botao_por_delineamento(self):
        """Filtrar por tipo era digitar no campo de busca e torcer.

        A busca livre procura o termo no registro inteiro: "revisão"
        traz sistemática, narrativa e de escopo juntas, e nada diz
        QUANTOS ha de cada. Os botoes saem da mesma lista declarada, com
        a contagem de cada um.
        """
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index("VIEWS.artigos = crudView({"):]
        trecho = trecho[:trecho.index("\n  fields:")]
        self.assertIn("chips:", trecho)
        self.assertIn('campo: "study_type"', trecho)
        # da MESMA lista do seletor -- duas listas divergem
        self.assertIn("valores: DESENHO_OPTS", trecho)

    def test_os_botoes_e_a_busca_se_combinam(self):
        """Um filtro que zera o outro faz a pessoa perder o que ja tinha."""
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index("function visiveis()"):]
        trecho = trecho[:trecho.index("function repintar()")]
        # o botao recorta, e a busca recorta DEPOIS, no que sobrou
        self.assertIn("filtro.valor", trecho)
        self.assertIn("filtro.termo", trecho)

    def test_ha_um_botao_para_quem_nao_tem_tipo_declarado(self):
        """Sem ele, esses artigos so aparecem em "Todos" -- e se perdem.

        E sao justamente os que precisam de alguem: artigo sem
        delineamento declarado nao entra em nenhuma contagem do painel.
        """
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index("VIEWS.artigos = crudView({"):]
        trecho = trecho[:trecho.index("\n  fields:")]
        self.assertIn("sem tipo declarado", trecho)

    def test_valor_fora_da_lista_tambem_ganha_botao(self):
        """O que alguem escreveu a mao antes de o campo virar seletor.

        Esconder esses registros faria a soma dos botoes nao fechar com o
        total -- e quem olha confere a soma.
        """
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index("let botoes = null;"):]
        trecho = trecho[:trecho.index("const bar = h(")]
        self.assertIn("declarados.indexOf(v) < 0", trecho)

    def test_o_caminho_de_gravacao_normaliza(self):
        """Tela, planilha e API entram todas pelo mesmo `ingest_articles`."""
        for titulo, tipo in (("A", "ECR"), ("B", "RCT"), ("C", "ensaio clínico randomizado")):
            curator.register(self.db, "articles", {"Título": titulo, "Tipo de estudo": tipo})
        tipos = self.db.dicts(
            "SELECT DISTINCT study_type FROM articles WHERE study_type IS NOT NULL")
        self.assertEqual([t["study_type"] for t in tipos],
                         ["Ensaio clínico controlado e randomizado"])


# ----------------------------------------------------------------------
# 3. Pesquisador do LAPE x coautor
# ----------------------------------------------------------------------
class TestQuemEDoLaboratorio(Base):

    def test_quem_so_assina_um_artigo_nasce_coautor(self):
        """Publicar com o LAPE nao torna ninguem integrante do LAPE."""
        curator.register(self.db, "articles", {
            "Título": "Humor e natação", "Autores": "Sofia Verschuren; Erik Lindqvist"})
        for nome in ("Sofia Verschuren", "Erik Lindqvist"):
            with self.subTest(quem=nome):
                self.assertEqual(
                    self.db.scalar("SELECT is_external FROM members WHERE full_name = ?",
                                   (nome,)), 1)

    def test_assinar_mais_um_artigo_nao_rebaixa_quem_e_da_casa(self):
        """O erro simetrico, e o pior dos dois.

        Passar o vinculo como valor comum faria a professora do
        laboratorio virar coautora no dia em que assinasse outro artigo.
        """
        curator.register(self.db, "members", {"Nome": "Alexandro Andrade",
                                              "Função": "professor"})
        curator.register(self.db, "articles", {"Título": "Um", "Autores": "Alexandro Andrade"})
        curator.register(self.db, "articles", {"Título": "Dois", "Autores": "Alexandro Andrade"})
        self.assertEqual(
            self.db.scalar("SELECT is_external FROM members WHERE name_key = 'andrade_a'"), 0)

    def test_o_artigo_e_a_ficha_contam_a_mesma_historia(self):
        curator.register(self.db, "articles", {"Título": "Três", "Autores": "Sofia Verschuren"})
        pessoa = self.db.scalar("SELECT id FROM members WHERE full_name = 'Sofia Verschuren'")
        self.assertEqual(
            self.db.scalar("SELECT is_external FROM article_authors WHERE member_id = ?",
                           (pessoa,)), 1)

    def test_a_revisao_nao_acusa_quem_tem_qualquer_sinal_de_vinculo(self):
        """Um sinal basta. Nao se propoe rebaixar quem foi cadastrado."""
        curator.register(self.db, "articles", {"Título": "Quatro", "Autores": "Marina"})
        pessoa = self.db.scalar("SELECT id FROM members WHERE full_name = 'Marina'")
        self.db.execute("UPDATE members SET is_external = 0 WHERE id = ?", (pessoa,))
        self.db.conn.commit()
        self.assertIn("Marina", [c["full_name"] for c in vinculo.candidatos(self.db)])

        self.db.execute("UPDATE members SET email = ? WHERE id = ?", ("m@udesc.br", pessoa))
        self.db.conn.commit()
        self.assertNotIn("Marina", [c["full_name"] for c in vinculo.candidatos(self.db)])
        self.assertIn("e-mail", vinculo.sinais_de(self.db, pessoa))

    def test_a_ficha_sem_artigo_nenhum_nao_e_proposta(self):
        """Ela nao e coautora de coisa nenhuma -- e um registro solto."""
        self.db.member_id("Ninguém Aqui", create=True)
        self.db.conn.commit()
        self.assertNotIn("Ninguém Aqui",
                         [c["full_name"] for c in vinculo.candidatos(self.db)])

    def test_dar_conta_a_alguem_e_declarar_que_e_do_laboratorio(self):
        """Encontrado pelo próprio teste de rede, e era defeito de verdade.

        Quem aparece primeiro como autor nasce coautor. Sem esta regra
        continuaria coautor depois de entrar no sistema com senha própria
        -- fora da contagem da equipe e fora do organograma.
        """
        from lape import auth

        curator.register(self.db, "articles", {"Título": "Seis", "Autores": "Camile Ramos"})
        self.assertEqual(self.db.scalar(
            "SELECT is_external FROM members WHERE full_name = 'Camile Ramos'"), 1)
        auth.create_account(self.db, "Camile Ramos", "camile@udesc.br", "senhaforte123")
        pessoa = self.db.scalar("SELECT id FROM members WHERE full_name = 'Camile Ramos'")
        self.assertEqual(
            self.db.scalar("SELECT is_external FROM members WHERE id = ?", (pessoa,)), 0)
        self.assertEqual(
            self.db.scalar("SELECT is_external FROM article_authors WHERE member_id = ?",
                           (pessoa,)), 0)

    def test_marcar_vale_nos_dois_sentidos(self):
        curator.register(self.db, "articles", {"Título": "Cinco", "Autores": "Nayara"})
        pessoa = self.db.scalar("SELECT id FROM members WHERE full_name = 'Nayara'")
        vinculo.marcar(self.db, pessoa, coautor=False)
        self.assertEqual(
            self.db.scalar("SELECT is_external FROM members WHERE id = ?", (pessoa,)), 0)
        self.assertEqual(
            self.db.scalar("SELECT is_external FROM article_authors WHERE member_id = ?",
                           (pessoa,)), 0)
        vinculo.marcar(self.db, pessoa, coautor=True)
        self.assertEqual(
            self.db.scalar("SELECT is_external FROM members WHERE id = ?", (pessoa,)), 1)


# ----------------------------------------------------------------------
# 4. Indice h
# ----------------------------------------------------------------------
class TestOIndiceH(Base):

    def _pessoa_com_artigos(self, nome="Guilherme Torres"):
        pessoa = self.db.member_id(nome, create=True)
        for i, citacoes in enumerate((30, 20, 10, 5, 1), start=1):
            artigo = self.db.insert("articles", {
                "title": f"Artigo {i}", "title_key": f"artigo-{i}",
                "scopus_citations": citacoes, "openalex_citations": citacoes})
            self.db.execute(
                "INSERT INTO article_authors (article_id, member_id, author_name, author_order)"
                " VALUES (?, ?, ?, ?)", (artigo, pessoa, nome, 1))
        self.db.conn.commit()
        return pessoa

    def test_o_curador_nao_encosta_no_declarado(self):
        """Bastava rodar o curador para o numero conferido sumir."""
        pessoa = self._pessoa_com_artigos()
        indice_h.declarar(self.db, pessoa, 16, base="Scopus", por="coordenação")
        metrics.compute_h_indexes(self.db)
        self.assertEqual(
            self.db.scalar("SELECT h_index FROM members WHERE id = ?", (pessoa,)), 16)

    def test_o_perfil_publico_nao_encosta_no_declarado(self):
        """O OpenAlex junta homonimo e conta duplicata.

        Reproduz o UPDATE do rastreador: e ele que trazia 17 onde o
        conferido na Scopus e 16.
        """
        pessoa = self._pessoa_com_artigos()
        indice_h.declarar(self.db, pessoa, 16, base="Scopus", por="coordenação")
        self.db.execute(
            "UPDATE members SET"
            " h_index = CASE WHEN h_index_declarado IS NOT NULL"
            "                THEN h_index_declarado ELSE ? END,"
            " h_index_source = CASE WHEN h_index_declarado IS NOT NULL"
            "                       THEN 'declarado' ELSE 'openalex_author' END"
            " WHERE id = ?", (17, pessoa))
        self.db.conn.commit()
        self.assertEqual(
            self.db.scalar("SELECT h_index FROM members WHERE id = ?", (pessoa,)), 16)

    def test_apagar_a_declaracao_nao_deixa_o_numero_orfao(self):
        """Senao o valor declarado seguia na tela, sem origem e sem data."""
        pessoa = self.db.member_id("Sem Artigo", create=True)
        self.db.conn.commit()
        indice_h.declarar(self.db, pessoa, 16, base="Scopus")
        indice_h.declarar(self.db, pessoa, None)
        self.assertIsNone(
            self.db.scalar("SELECT h_index FROM members WHERE id = ?", (pessoa,)))

    def test_apagar_devolve_a_estimativa_de_quem_tem_artigo(self):
        pessoa = self._pessoa_com_artigos()
        metrics.compute_h_indexes(self.db)
        estimado = self.db.scalar("SELECT h_index FROM members WHERE id = ?", (pessoa,))
        indice_h.declarar(self.db, pessoa, 16, base="Scopus")
        indice_h.declarar(self.db, pessoa, None)
        self.assertEqual(
            self.db.scalar("SELECT h_index FROM members WHERE id = ?", (pessoa,)), estimado)
        self.assertEqual(
            self.db.scalar("SELECT h_index_source FROM members WHERE id = ?", (pessoa,)),
            "banco_lape")

    def test_a_declaracao_guarda_base_e_data(self):
        """Indice h sem fonte e sem data nao se confere."""
        pessoa = self._pessoa_com_artigos()
        indice_h.declarar(self.db, pessoa, 16, base="Scopus", por="Ana")
        linha = self.db.dicts("SELECT * FROM members WHERE id = ?", (pessoa,))[0]
        self.assertEqual(linha["h_index_declarado_base"], "Scopus")
        self.assertEqual(linha["h_index_declarado_por"], "Ana")
        self.assertTrue(linha["h_index_declarado_em"])

    def test_a_declaracao_velha_e_avisada_e_nao_descartada(self):
        pessoa = self._pessoa_com_artigos()
        indice_h.declarar(self.db, pessoa, 16, base="Scopus", em="2019-01-01")
        linha = self.db.dicts("SELECT * FROM members WHERE id = ?", (pessoa,))[0]
        situacao = indice_h.situacao(linha)
        self.assertEqual(situacao["valor"], 16)
        self.assertTrue(situacao["a_conferir"])
        self.assertIn("reconferir", situacao["recado"])

    def test_o_numero_absurdo_e_recusado(self):
        """Um h de 1600 na tela desmoraliza o painel para quem olha."""
        pessoa = self._pessoa_com_artigos()
        with self.assertRaises(ValueError):
            indice_h.declarar(self.db, pessoa, 1600)
        with self.assertRaises(ValueError):
            indice_h.declarar(self.db, pessoa, -3)

    def test_os_declarados_entram_onde_ninguem_declarou(self):
        self.db.member_id("Guilherme Torres", create=True)
        self.db.member_id("Darlan Silva", create=True)
        self.db.conn.commit()
        indice_h.instalar_declarados(self.db)
        self.assertEqual(self.db.scalar(
            "SELECT h_index_declarado FROM members WHERE full_name = 'Guilherme Torres'"), 16)
        self.assertEqual(self.db.scalar(
            "SELECT h_index_declarado FROM members WHERE full_name = 'Darlan Silva'"), 11)

    def test_os_declarados_nao_passam_por_cima_da_tela(self):
        """Uma vez gravado pela coordenacao, a lista do codigo se cala."""
        pessoa = self.db.member_id("Guilherme Torres", create=True)
        self.db.conn.commit()
        indice_h.declarar(self.db, pessoa, 19, base="Lattes")
        indice_h.instalar_declarados(self.db)
        self.assertEqual(
            self.db.scalar("SELECT h_index_declarado FROM members WHERE id = ?", (pessoa,)), 19)

    def test_quem_nao_esta_no_banco_nao_vira_ficha(self):
        indice_h.instalar_declarados(self.db)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM members"), 0)


# ----------------------------------------------------------------------
# 5. O rotulo, e nao a forma canonica
# ----------------------------------------------------------------------
class TestORotuloNaTela(unittest.TestCase):
    """O banco guarda "em_producao"; a tela mostrava esse mesmo texto.

    Em cinco lugares -- lista de artigos, meus artigos, submissoes e as
    duas de projetos -- a etiqueta imprimia a forma canonica. Quem le
    "em_producao" no painel do laboratorio le um erro de sistema; e nao
    era erro, era a traducao que faltava. Os mapas ja existiam e eram
    usados so no formulario.
    """

    @classmethod
    def setUpClass(cls):
        cls.html = (TEMPLATES / "app.html").read_text(encoding="utf-8")

    def test_nenhuma_etiqueta_imprime_a_forma_canonica(self):
        for cru in ("text: r.status", "text: r.decision",
                    "text: row.status", "text: row.decision"):
            with self.subTest(trecho=cru):
                self.assertNotIn(cru, self.html)

    def test_as_tres_situacoes_tem_mapa(self):
        for mapa in ("SITUACAO_ROTULO", "DECISAO_ROTULO", "PROJETO_ROTULO"):
            with self.subTest(mapa=mapa):
                self.assertIn("const " + mapa + " = {", self.html)

    def test_o_mapa_de_projetos_cobre_o_que_a_tela_oferece(self):
        """Duas listas que divergem devolvem a forma canonica na tela."""
        trecho = self.html[self.html.index("const PROJETO_ROTULO = {"):]
        trecho = trecho[:trecho.index("};")]
        for rotulo in ("Em andamento", "Planejado", "Concluído", "Suspenso"):
            with self.subTest(rotulo=rotulo):
                self.assertIn(rotulo, trecho)
        opcoes = self.html[self.html.index("const PROJECT_OPTS = ["):]
        opcoes = opcoes[:opcoes.index("];")]
        for rotulo in ("Em andamento", "Planejado", "Concluído", "Suspenso"):
            self.assertIn(rotulo, opcoes)

    def test_valor_sem_traducao_volta_como_veio(self):
        """Nunca desaparecer da tela por nao estar no mapa.

        Um status novo no banco e um rotulo que falta -- e melhor mostrar
        "em_analise" do que mostrar nada, que e o que `mapa[valor]`
        sozinho faria.
        """
        trecho = self.html[self.html.index("function rotuloDe("):]
        trecho = trecho[:trecho.index("\n}")]
        self.assertIn("mapa[valor] || valor", trecho)


if __name__ == "__main__":
    unittest.main()
