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

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import indice_h, linhas, mapping, metrics, vinculo  # noqa: E402
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

    def test_o_campo_vazio_e_enviado_quando_se_edita(self):
        trecho = self.html[self.html.index("const payload = {};"):]
        trecho = trecho[:trecho.index("if (spec.extra)")]
        self.assertIn("spec.edicao", trecho,
                      "o campo vazio não é enviado, então apagar na tela não apaga")

    def test_a_ficha_aberta_manda_o_proprio_id(self):
        trecho = self.html[self.html.index("config.__carregar = function"):]
        trecho = trecho[:trecho.index("titulo.textContent")]
        self.assertIn("edicao: true", trecho)
        self.assertIn("registro_id: row.id", trecho)

    def test_o_cadastro_novo_nao_entra_em_modo_de_edicao(self):
        """`row` nulo é o formulário em branco: não há id nem o que apagar."""
        trecho = self.html[self.html.index("config.__carregar = function"):]
        trecho = trecho[:trecho.index("titulo.textContent")]
        self.assertIn("row ?", trecho)

    def test_ha_como_excluir_um_artigo(self):
        """Sem exclusão, as cópias que o defeito criou não saem da tela."""
        trecho = self.html[self.html.index("VIEWS.artigos = crudView"):]
        trecho = trecho[:trecho.index("columns: [")]
        self.assertIn('"/api/articles/"', trecho)
        self.assertIn('"DELETE"', trecho)
        self.assertIn("confirm(", trecho)
        self.assertIn('can("coordenacao")', trecho)


# ----------------------------------------------------------------------
# 2. Tipo de estudo
# ----------------------------------------------------------------------
class TestOTipoDeEstudo(Base):

    def test_as_dez_opcoes_declaradas(self):
        self.assertEqual([r for _c, r, _g in mapping.DESENHOS_DE_ESTUDO], [
            "Ensaio clínico controlado e randomizado", "Estudo transversal",
            "Estudo de coorte", "Revisão sistemática", "Meta-análise",
            "Revisão narrativa", "Editorial", "Carta ao editor",
            "Comunicação curta", "Estudo de protocolo",
        ])

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


if __name__ == "__main__":
    unittest.main()
