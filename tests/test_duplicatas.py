#!/usr/bin/env python3
"""Testes das fichas repetidas da mesma pessoa.

    python3 -m unittest tests.test_duplicatas -v

O defeito que originou este módulo: a planilha listava os autores em
formato livre, e num artigo saiu "Alexandro" onde em dezoito saiu
"Andrade". Viraram duas fichas -- a chave de autor é montada sobre o
sobrenome, e "alexandro" não encontra "andrade_a" de maneira nenhuma.

O perigo do conserto é maior que o defeito. "Henrique" e "Henrique
Fukumasa" têm exatamente a mesma cara que "Alexandro" e "Alexandro
Andrade", e podem ser duas pessoas: um laboratório de vinte integrantes
tem dois Henriques com facilidade. Fundir por conta própria juntaria a
produção de duas pessoas num nome só, e desfazer isso depois exige saber
qual artigo era de quem -- que é justamente o que a fusão apaga.

Por isso o que estes testes guardam é a fronteira: o que se propõe, o que
não se propõe, e o que a fusão faz quando alguém confirma.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import duplicatas  # noqa: E402
from lape.db import Database  # noqa: E402
from lape.util import title_key  # noqa: E402


class BaseFichas(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "d.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()

    def pessoa(self, nome, artigos=()):
        mid = self.db.member_id(nome, create=True)
        for titulo in artigos:
            achado = self.db.dicts("SELECT id FROM articles WHERE title_key = ?",
                                   (title_key(titulo),))
            if achado:
                aid = achado[0]["id"]
            else:
                aid = self.db.execute(
                    "INSERT INTO articles (title, title_key, status)"
                    " VALUES (?, ?, 'publicado')", (titulo, title_key(titulo))).lastrowid
            self.db.execute(
                "INSERT INTO article_authors (article_id, member_id, author_name,"
                "                             author_order) VALUES (?, ?, ?, 1)",
                (aid, mid, nome))
        self.db.conn.commit()
        return mid

    def pares(self):
        return [(c["sumir"]["nome"], c["manter"]["nome"])
                for c in duplicatas.candidatos(self.db)]


class TestOQueSePropoe(BaseFichas):

    def test_o_primeiro_nome_solto_encontra_a_ficha_inteira(self):
        # o caso real: "Alexandro" num artigo, "Andrade" em dezoito
        self.pessoa("Alexandro", ["Um artigo"])
        self.pessoa("Alexandro Andrade", ["Outro artigo"])
        self.assertEqual(self.pares(), [("Alexandro", "Alexandro Andrade")])

    def test_a_ficha_com_mais_artigos_e_a_que_fica(self):
        self.pessoa("Alexandro", ["A"])
        self.pessoa("Alexandro Andrade", ["B", "C", "D"])
        proposta = duplicatas.candidatos(self.db)[0]
        self.assertEqual(proposta["manter"]["nome"], "Alexandro Andrade")
        self.assertEqual(proposta["manter"]["artigos"], 3)
        self.assertEqual(proposta["sumir"]["artigos"], 1)

    def test_a_proposta_diz_por_que(self):
        # botão que junta duas pessoas sem dizer no que se baseou é pior
        # que nenhum botão
        self.pessoa("Alexandro", ["A"])
        self.pessoa("Alexandro Andrade", ["B"])
        self.assertIn("nunca", duplicatas.candidatos(self.db)[0]["porque"])

    def test_o_par_ambiguo_tambem_aparece(self):
        """"Henrique" e "Henrique Fukumasa" podem ser duas pessoas.

        Aparecer é o certo: quem conhece a equipe decide. O que seria
        errado é o sistema decidir por conta própria -- e é por isso que
        esta é uma lista de propostas, e não uma rotina que roda sozinha.
        """
        self.pessoa("Henrique", ["A"])
        self.pessoa("Henrique Fukumasa", ["B"])
        self.assertEqual(self.pares(), [("Henrique", "Henrique Fukumasa")])


class TestOQueNaoSePropoe(BaseFichas):

    def test_quem_assina_o_mesmo_artigo_nao_e_a_mesma_pessoa(self):
        """A trava de segurança.

        Se as duas fichas assinam o mesmo artigo, ou são pessoas
        diferentes, ou a lista de autores daquele artigo está errada. Nos
        dois casos fundir apagaria a evidência.
        """
        mid = self.pessoa("Marina", ["Artigo dividido"])
        artigo = self.db.scalar("SELECT article_id FROM article_authors WHERE member_id = ?",
                                (mid,))
        outra = self.db.member_id("Marina Rossetto", create=True)
        self.db.execute(
            "INSERT INTO article_authors (article_id, member_id, author_name,"
            "                             author_order) VALUES (?, ?, ?, 2)",
            (artigo, outra, "Marina Rossetto"))
        self.db.conn.commit()
        self.assertEqual(self.pares(), [])

    def test_dois_nomes_completos_diferentes_nao_se_juntam(self):
        self.pessoa("Alexandro Andrade", ["A"])
        self.pessoa("Alexandro Vilarino", ["B"])
        self.assertEqual(self.pares(), [])

    def test_primeiro_nome_que_nao_bate_fica_de_fora(self):
        self.pessoa("Carla", ["A"])
        self.pessoa("Alexandro Andrade", ["B"])
        self.assertEqual(self.pares(), [])

    def test_quem_e_de_fora_do_laboratorio_nao_entra(self):
        # coautor externo não é ficha de integrante para arrumar
        self.pessoa("Alexandro Andrade", ["A"])
        fora = self.db.member_id("Alexandro", create=True)
        self.db.execute("UPDATE members SET is_external = 1 WHERE id = ?", (fora,))
        self.db.conn.commit()
        self.assertEqual(self.pares(), [])

    def test_banco_sem_repetida_devolve_lista_vazia(self):
        self.pessoa("Alexandro Andrade", ["A"])
        self.pessoa("Guilherme Torres Vilarino", ["B"])
        self.assertEqual(duplicatas.candidatos(self.db), [])


class TestAFusao(BaseFichas):

    def test_os_artigos_passam_para_a_ficha_que_fica(self):
        sumir = self.pessoa("Alexandro", ["Só dele"])
        manter = self.pessoa("Alexandro Andrade", ["A", "B"])
        r = duplicatas.fundir(self.db, manter_id=manter, sumir_id=sumir)
        self.assertEqual(r["artigos_agora"], 3)
        self.assertEqual(r["artigos_movidos"], 1)

    def test_a_ficha_antiga_deixa_de_existir(self):
        sumir = self.pessoa("Alexandro", ["A"])
        manter = self.pessoa("Alexandro Andrade", ["B"])
        duplicatas.fundir(self.db, manter_id=manter, sumir_id=sumir)
        self.assertEqual(self.db.dicts("SELECT id FROM members WHERE id = ?", (sumir,)), [])

    def test_a_grafia_que_sumiu_vira_variacao_do_nome(self):
        """Sem isto o trabalho se refaz todo mês.

        A próxima importação da mesma planilha reencontra "Alexandro", não
        acha ninguém com essa chave, e cria a ficha de novo -- sem nada na
        tela dizendo por que a duplicata voltou.
        """
        sumir = self.pessoa("Alexandro", ["A"])
        manter = self.pessoa("Alexandro Andrade", ["B"])
        duplicatas.fundir(self.db, manter_id=manter, sumir_id=sumir)
        self.assertEqual(self.db.member_id("Alexandro", create=True), manter)

    def test_fundir_de_novo_nao_multiplica_a_coautoria(self):
        # o mesmo integrante duas vezes no mesmo artigo contaria em dobro
        # em toda métrica de produção
        sumir = self.pessoa("Alexandro", ["Artigo comum"])
        manter = self.pessoa("Alexandro Andrade", ["Outro"])
        duplicatas.fundir(self.db, manter_id=manter, sumir_id=sumir)
        por_artigo = self.db.dicts(
            "SELECT article_id, COUNT(*) AS n FROM article_authors"
            " WHERE member_id = ? GROUP BY article_id", (manter,))
        self.assertTrue(all(linha["n"] == 1 for linha in por_artigo), por_artigo)

    def test_a_proposta_some_da_lista_depois_de_aplicada(self):
        sumir = self.pessoa("Alexandro", ["A"])
        manter = self.pessoa("Alexandro Andrade", ["B"])
        duplicatas.fundir(self.db, manter_id=manter, sumir_id=sumir)
        self.assertEqual(duplicatas.candidatos(self.db), [])

    def test_uma_ficha_nao_se_funde_com_ela_mesma(self):
        mid = self.pessoa("Alexandro Andrade", ["A"])
        with self.assertRaises(ValueError):
            duplicatas.fundir(self.db, manter_id=mid, sumir_id=mid)

    def test_ficha_inexistente_da_erro_e_nao_silencio(self):
        mid = self.pessoa("Alexandro Andrade", ["A"])
        with self.assertRaises(ValueError):
            duplicatas.fundir(self.db, manter_id=mid, sumir_id=99999)


class TestAGrafiaDeclaradaJuntaSozinha(BaseFichas):
    """A coordenacao escreveu que a grafia e daquela pessoa.

    Quando isso esta declarado em `PESQUISADORES`, nao ha o que propor a
    ninguem: a resposta ja foi dada por escrito, e a fusao so obedece. Foi
    assim que a ficha "Alexandro" se juntou a "Alexandro Andrade" sem
    ninguem precisar clicar em nada.

    O que NAO pode e a declaracao virar licenca para juntar qualquer
    coisa: o encaixe continua exigindo ficha de um nome so, primeiro nome
    igual, e nenhum artigo assinado em comum.
    """

    def declarar(self, nome, grafias):
        from lape import ingest_autor
        pessoa = {"nome": nome, "vinculo": "coordenacao", "grafias": grafias}
        return ingest_autor.declarar_grafias(self.db, pessoa)

    def test_o_fantasma_declarado_e_absorvido(self):
        fantasma = self.pessoa("Alexandro", ["Artigo solto"])
        andrade = self.pessoa("Alexandro Andrade", ["A", "B"])
        self.declarar("Alexandro Andrade", ("Alexandro",))
        self.assertEqual(self.db.dicts("SELECT id FROM members WHERE id = ?",
                                       (fantasma,)), [])
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM article_authors WHERE member_id = ?",
                           (andrade,)), 3)

    def test_declarar_de_novo_nao_quebra(self):
        # roda a cada arranque do servico: tem de ser inofensivo na segunda vez
        self.pessoa("Alexandro", ["A"])
        andrade = self.pessoa("Alexandro Andrade", ["B"])
        self.declarar("Alexandro Andrade", ("Alexandro",))
        self.declarar("Alexandro Andrade", ("Alexandro",))
        self.assertEqual(self.db.member_id("Alexandro", create=False), andrade)

    def test_nao_absorve_quem_assina_o_mesmo_artigo(self):
        """A trava vale tambem para a grafia declarada.

        Se as duas fichas dividem um artigo, ou sao pessoas diferentes ou
        a autoria esta errada -- e uma declaracao no codigo nao sabe qual
        das duas coisas e.
        """
        fantasma = self.pessoa("Alexandro", ["Artigo dividido"])
        artigo = self.db.scalar(
            "SELECT article_id FROM article_authors WHERE member_id = ?", (fantasma,))
        andrade = self.pessoa("Alexandro Andrade", ["Outro"])
        self.db.execute(
            "INSERT INTO article_authors (article_id, member_id, author_name,"
            "                             author_order) VALUES (?, ?, ?, 2)",
            (artigo, andrade, "Alexandro Andrade"))
        self.db.conn.commit()
        self.declarar("Alexandro Andrade", ("Alexandro",))
        self.assertTrue(self.db.dicts("SELECT id FROM members WHERE id = ?", (fantasma,)))

    def test_nao_absorve_ficha_de_nome_completo(self):
        # "Alexandro Vilarino" nao e um pedaco de "Alexandro Andrade"
        outro = self.pessoa("Alexandro Vilarino", ["A"])
        self.pessoa("Alexandro Andrade", ["B"])
        self.declarar("Alexandro Andrade", ("Alexandro Vilarino",))
        self.assertTrue(self.db.dicts("SELECT id FROM members WHERE id = ?", (outro,)))

    def test_o_par_ambiguo_continua_esperando_gente(self):
        """"Henrique" e "Henrique Fukumasa" nao estao declarados.

        Ninguem escreveu que sao a mesma pessoa, e o sistema nao decide
        isso sozinho -- continua na lista de propostas, para quem conhece
        a equipe resolver.
        """
        from lape import ingest_autor
        self.pessoa("Henrique", ["A"])
        self.pessoa("Henrique Fukumasa", ["B"])
        ingest_autor.garantir_professores(self.db, criar=False)
        self.assertEqual(self.pares(), [("Henrique", "Henrique Fukumasa")])


class TestAPorta(unittest.TestCase):
    """As rotas existem, e só a coordenação chega nelas."""

    def test_as_rotas_estao_registradas_para_a_coordenacao(self):
        from lape import api
        achadas = {(metodo, perfil) for metodo, padrao, _f, perfil in api.ROUTES
                   if "equipe/duplicatas" in padrao}
        self.assertEqual(achadas, {("GET", "coordenacao"), ("POST", "coordenacao")})

    def test_a_tela_da_administracao_desenha_o_painel(self):
        corpo = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        self.assertIn("desenharDuplicatas(", corpo)
        self.assertIn("/api/equipe/duplicatas", corpo)
        # fundir apaga uma ficha: o aviso vem antes, que e quando ainda da
        # para nao fazer
        self.assertIn("Isto não se desfaz sozinho", corpo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
