#!/usr/bin/env python3
"""Agrupamento: os temas que o acervo forma sozinho.

    python3 -m unittest tests.test_agrupamento -v

Agrupamento é fácil de fazer errado, e errado ele é convincente: três
caixas com palavras dentro parecem um achado mesmo quando saíram de um
borrão. O que se cobra aqui é isso -- que o módulo recuse dado de menos,
que diga em palavras quando a separação é fraca, e que a MESMA pergunta
devolva a MESMA resposta, hoje e amanhã.
"""
from __future__ import annotations

import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import agrupamento, biblioteca, linhas  # noqa: E402
from lape.db import Database  # noqa: E402

# Três assuntos que não se confundem. Se o agrupamento não achar estes,
# não vai achar nada numa literatura de verdade.
TEMAS = {
    "Treinador, liderança e relação":
        "coach coaching leadership autonomy controlling athlete trainer feedback",
    "Lesão e retorno ao jogo":
        "injury shoulder knee rehabilitation return pain prevention surgery",
    "Burnout, abandono e permanência":
        "burnout dropout exhaustion attrition withdrawal commitment engagement",
}


class BaseDoAcervo(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "g.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        linhas.instalar(self.db)
        biblioteca.instalar(self.db)
        self.acervo = self.db.scalar(
            "SELECT id FROM biblioteca WHERE code = ?", ("motivacao_handebol",))
        self.n = 0

    def semear(self, quantos_por_tema=12, temas=None):
        sorteio = random.Random(7)
        for segmento, texto in (temas or TEMAS).items():
            palavras = texto.split()
            for _ in range(quantos_por_tema):
                self.n += 1
                self.db.execute(
                    "INSERT INTO biblioteca_item (biblioteca_id, chave, segmento,"
                    " title, abstract, year, doi, base)"
                    " VALUES (?,?,?,?,?,?,?,?)",
                    (self.acervo, f"k{self.n}", segmento, f"Estudo {self.n}",
                     " ".join(sorteio.sample(palavras, 5)), 2018 + self.n % 8,
                     f"10.5/{self.n}", "pubmed"))
        self.db.conn.commit()


class TestOQueEleEncontra(BaseDoAcervo):

    def test_acha_os_assuntos_que_estao_la(self):
        self.semear()
        d = agrupamento.agrupar(self.db, "motivacao_handebol")
        self.assertIsNone(d["aviso"])
        self.assertGreaterEqual(d["k"], 3)
        self.assertEqual(sum(g["n"] for g in d["grupos"]), 36)

    def test_cada_grupo_diz_em_que_segmentos_cai(self):
        """É a ponte com o que o laboratório declarou.

        Sem ela o agrupamento é um segundo recorte solto ao lado do
        primeiro, e ninguém sabe o que fazer com os dois.
        """
        self.semear()
        d = agrupamento.agrupar(self.db, "motivacao_handebol")
        for g in d["grupos"]:
            with self.subTest(termos=g["termos"][:3]):
                self.assertTrue(g["segmentos"])
                self.assertEqual(sum(s["n"] for s in g["segmentos"]), g["n"])

    def test_os_grupos_sao_ordenados_do_maior_para_o_menor(self):
        self.semear()
        d = agrupamento.agrupar(self.db, "motivacao_handebol")
        tamanhos = [g["n"] for g in d["grupos"]]
        self.assertEqual(tamanhos, sorted(tamanhos, reverse=True))

    def test_da_para_agrupar_dentro_de_um_segmento(self):
        self.semear(quantos_por_tema=30)
        d = agrupamento.agrupar(self.db, "motivacao_handebol",
                                segmento="Lesão e retorno ao jogo")
        self.assertEqual(d["n"], 30)
        self.assertEqual(d["segmento"], "Lesão e retorno ao jogo")

    def test_nenhum_grupo_de_um_artigo_so(self):
        """Grupo de um artigo é um artigo.

        A silhueta ADORA esses -- um ponto sozinho longe de todos tem
        silhueta quase 1 e puxa a média para cima --, e a tela ficava com
        "grupo de 1" ao lado de grupos de doze. Por isso o acervo deste
        teste tem um FORASTEIRO: um artigo de vocabulário próprio, que é
        exatamente o que vira grupo solitário quando nada impede.
        """
        self.semear()
        self.db.execute(
            "INSERT INTO biblioteca_item (biblioteca_id, chave, segmento,"
            " title, abstract, year, doi, base) VALUES (?,?,?,?,?,?,?,?)",
            (self.acervo, "forasteiro", "Praia e handebol adaptado", "Forasteiro",
             "wheelchair goalball paralympic adapted classification boccia",
             2024, "10.6/1", "pubmed"))
        self.db.conn.commit()
        d = agrupamento.agrupar(self.db, "motivacao_handebol")
        self.assertTrue(all(g["n"] >= 2 for g in d["grupos"]),
                        [g["n"] for g in d["grupos"]])


class TestAEscolhaDoNumeroDeGrupos(unittest.TestCase):
    """A regra que decide quantos grupos ficam, testada sozinha.

    Montar aqui um caso com grupo solitário custa três linhas; fazê-lo
    aparecer num agrupamento de verdade depende da paisagem dos dados, e
    ela muda com o acervo -- o teste passaria a depender da sorte.
    """

    def test_ganha_a_melhor_silhueta(self):
        escolhido = agrupamento._melhor_k([
            (2, [0, 0, 1, 1], 0.3),
            (3, [0, 0, 1, 2], 0.2),
        ])
        self.assertEqual(escolhido[0], 2)

    def test_grupo_de_um_artigo_perde_mesmo_com_nota_melhor(self):
        """A silhueta adora ponto solitário, e ele não é um grupo."""
        escolhido = agrupamento._melhor_k([
            (2, [0, 0, 0, 1, 1, 1], 0.40),     # sem solitário
            (3, [0, 0, 0, 1, 1, 2], 0.95),     # um grupo de UM
        ])
        self.assertEqual(escolhido[0], 2)

    def test_quando_todos_tem_solitario_a_nota_volta_a_decidir(self):
        """Esconder o resultado seria pior do que mostrá-lo."""
        escolhido = agrupamento._melhor_k([
            (2, [0, 0, 0, 0, 1], 0.2),
            (3, [0, 0, 0, 1, 2], 0.6),
        ])
        self.assertEqual(escolhido[0], 3)

    def test_sem_candidato_nenhum_devolve_nada(self):
        self.assertIsNone(agrupamento._melhor_k([]))


class TestOQueEleRecusa(BaseDoAcervo):

    def test_acervo_pequeno_e_recusado_em_vez_de_desenhado(self):
        """Três grupos de quatro artigos têm cara de achado e não são."""
        self.semear(quantos_por_tema=4)
        d = agrupamento.agrupar(self.db, "motivacao_handebol")
        self.assertEqual(d["grupos"], [])
        self.assertIn("pouco para agrupar", d["aviso"])
        self.assertIn(str(agrupamento.MINIMO), d["aviso"])

    def test_acervo_sem_resumo_diz_que_falta_resumo(self):
        for i in range(40):
            self.db.execute(
                "INSERT INTO biblioteca_item (biblioteca_id, chave, title, base)"
                " VALUES (?,?,?,'pubmed')", (self.acervo, f"x{i}", ""))
        self.db.conn.commit()
        d = agrupamento.agrupar(self.db, "motivacao_handebol")
        self.assertTrue(d["aviso"])
        self.assertEqual(d["grupos"], [])

    def test_acervo_que_nao_existe_e_erro(self):
        with self.assertRaises(ValueError):
            agrupamento.agrupar(self.db, "nao-existe")

    def test_a_separacao_fraca_e_dita_em_palavras(self):
        """Silhueta ninguém lê de cabeça, e um número sozinho não avisa nada."""
        self.assertIn("bem", agrupamento._ler_silhueta(0.7))
        for valor in (0.3, 0.15, 0.02):
            with self.subTest(valor=valor):
                self.assertTrue(agrupamento._ler_silhueta(valor))
        self.assertIn("não", agrupamento._ler_silhueta(0.02))
        self.assertIn("fraca", agrupamento._ler_silhueta(0.15))


class TestAMesmaPerguntaAMesmaResposta(BaseDoAcervo):
    """Um painel que muda sozinho entre dois cliques destrói a confiança
    em tudo o mais que está na tela.
    """

    def test_duas_rodadas_dao_o_mesmo_agrupamento(self):
        self.semear()
        uma = agrupamento.agrupar(self.db, "motivacao_handebol")
        outra = agrupamento.agrupar(self.db, "motivacao_handebol")
        self.assertEqual(uma["k"], outra["k"])
        self.assertEqual([g["termos"] for g in uma["grupos"]],
                         [g["termos"] for g in outra["grupos"]])
        self.assertEqual(uma["silhueta"], outra["silhueta"])

    def test_a_consulta_pede_ordem_explicita(self):
        """Sem ORDER BY, o plano do sqlite escolhe a ordem -- e a ordem
        de entrada muda o resultado do k-médias.
        """
        fonte = (ROOT / "scripts" / "lape" / "agrupamento.py").read_text(
            encoding="utf-8")
        trecho = fonte[fonte.index("FROM biblioteca_item"):]
        self.assertIn("ORDER BY id", trecho[:400])

    def test_a_semente_do_sorteio_e_fixa(self):
        import ast

        fonte = (ROOT / "scripts" / "lape" / "agrupamento.py").read_text(
            encoding="utf-8")
        arvore = ast.parse(fonte)
        kmedias = next(n for n in ast.walk(arvore)
                       if isinstance(n, ast.FunctionDef) and n.name == "_kmedias")
        nomes = [a.arg for a in kmedias.args.args + kmedias.args.kwonlyargs]
        self.assertIn("semente", nomes, "a semente tem de ser um parâmetro declarado")
        for chamada in ast.walk(arvore):
            if not isinstance(chamada, ast.Call):
                continue
            funcao = ast.unparse(chamada.func)
            # `random.Random()` SEM argumento sorteia a semente do relógio,
            # e aí a mesma pergunta responde diferente a cada clique. O
            # teste de duas rodadas não pega isso sozinho: com dados bem
            # separados o k-médias converge para a mesma solução de
            # qualquer ponto de partida, e a falha só apareceria na
            # literatura de verdade, que é embolada.
            if funcao == "random.Random":
                with self.subTest(linha=chamada.lineno):
                    self.assertTrue(chamada.args, "sorteio sem semente declarada")
            self.assertNotIn(funcao, ("random.random", "random.shuffle",
                                      "random.choice", "random.sample"))


class TestOQueNaoEntraNaConta(BaseDoAcervo):

    def test_autor_e_revista_ficam_de_fora(self):
        """Com eles, o agrupamento sairia por grupo de pesquisa ou por
        revista -- duas perguntas legítimas, e outras.
        """
        texto = agrupamento._texto_do_item(
            {"title": "Motivação", "abstract": "resumo", "keywords": "chave",
             "authors": "Vilarino G", "journal": "Motriz"})
        self.assertIn("Motivação", texto)
        self.assertNotIn("Vilarino", texto)
        self.assertNotIn("Motriz", texto)

    def test_a_palavra_que_esta_em_quase_tudo_nao_separa_nada(self):
        """"handball" num acervo de handebol não agrupa ninguém."""
        itens = [{"title": "handball motivation coach", "abstract": "", "keywords": ""},
                 {"title": "handball injury shoulder", "abstract": "", "keywords": ""},
                 {"title": "handball burnout dropout", "abstract": "", "keywords": ""},
                 {"title": "handball coach feedback", "abstract": "", "keywords": ""}]
        _, vocabulario = agrupamento._vetores(itens)
        self.assertNotIn("handball", vocabulario)
        self.assertIn("coach", vocabulario)

    def test_palavra_de_metodo_nao_vira_tema(self):
        for vazia in ("results", "study", "analysis", "resultados", "estudo"):
            with self.subTest(palavra=vazia):
                self.assertEqual(agrupamento._termos(f"the {vazia} of motivation"),
                                 ["motivation"])


if __name__ == "__main__":
    unittest.main()
