#!/usr/bin/env python3
"""Ligar artigo a linha de pesquisa pelo titulo.

    python3 -m unittest tests.test_classificar -v

O titulo de um artigo cientifico e um resumo escrito por quem conhece o
assunto, e cada linha do LAPE ja declara as suas palavras-chave. Ligar as
duas coisas e barato -- e e por isso que o perigo aqui e ligar demais.

Um palpite errado em silencio e pior do que um campo vazio: o campo vazio
aparece na aba de qualidade e alguem o preenche; o palpite errado passa
por dado conferido e entra no relatorio do avaliador. Dai metade destes
testes ser sobre o que o modulo TEM de recusar a decidir.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import classificar, linhas  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseDoClassificador(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "cl.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        linhas.instalar(self.db)
        self.linhas = self.db.dicts(
            "SELECT id, name, keywords FROM research_lines WHERE active = 1")

    def linha_id(self, nome: str) -> int:
        return self.db.scalar("SELECT id FROM research_lines WHERE name = ?", (nome,))

    def artigo(self, titulo: str, linha_id=None) -> int:
        from lape.util import norm_key
        self.db.execute(
            "INSERT INTO articles (title, title_key, status, research_line_id)"
            " VALUES (?, ?, 'em_producao', ?)", (titulo, norm_key(titulo), linha_id))
        self.db.conn.commit()
        return self.db.scalar("SELECT id FROM articles WHERE title_key = ?",
                              (norm_key(titulo),))

    def veredito(self, titulo: str):
        """O que `sugerir` faria com este titulo: liga, ambiguo ou nada."""
        placar = classificar.pontuar(titulo, self.linhas)
        topo = placar[0] if placar else None
        segundo = placar[1] if len(placar) > 1 else None
        if topo is None or topo["peso"] < classificar.PESO_MINIMO:
            return ("sem_indicio", None)
        if segundo and topo["peso"] - segundo["peso"] < classificar.MARGEM_MINIMA:
            return ("ambiguo", topo["linha"])
        return ("liga", topo["linha"])


class TestOQueOTituloDiz(BaseDoClassificador):

    def test_o_titulo_que_nomeia_a_linha_e_ligado(self):
        casos = [
            ("Efeitos do exercício aeróbico na dor e no sono de mulheres com fibromialgia",
             "Fibromialgia e doenças reumáticas"),
            ("Qualidade do ar e desempenho de corredores em ambiente urbano",
             "Qualidade do ar"),
            ("Ansiedade pré-competitiva em atletas de judô de alto rendimento",
             "Psicologia do esporte"),
            ("Exercício físico e fadiga em sobreviventes de câncer de mama", "Câncer"),
            ("Cognição e autonomia funcional em idosos praticantes de caminhada",
             "Envelhecimento"),
            ("Motivação e aderência ao exercício em adultos sedentários",
             "Psicologia do exercício"),
            ("Exergames na escola e comportamento sedentário de adolescentes",
             "Exergames e escolas"),
            ("Reabilitação fisioterapêutica após lesão do ligamento cruzado anterior",
             "Fisioterapia"),
        ]
        for titulo, esperada in casos:
            with self.subTest(titulo=titulo[:40]):
                self.assertEqual(self.veredito(titulo), ("liga", esperada))

    def test_a_expressao_sobrevive_a_preposicao(self):
        """"qualidade do ar" tem de casar com a linha "Qualidade do ar".

        Enquanto so a palavra-chave perdia as palavras vazias, a expressao
        virava "qualidade ar" de um lado e continuava "qualidade do ar" do
        outro -- e a linha nao casava com um titulo que a nomeia inteira.
        """
        placar = classificar.pontuar(
            "Qualidade do ar em ginásios fechados", self.linhas)
        self.assertEqual(placar[0]["linha"], "Qualidade do ar")
        self.assertIn("qualidade ar", placar[0]["termos"])

    def test_palavra_de_duas_letras_so_vale_dentro_da_expressao(self):
        """"ar" sozinho nao caracteriza linha nenhuma."""
        placar = classificar.pontuar("Treino ao ar livre e humor", self.linhas)
        nomes = [x["linha"] for x in placar]
        if "Qualidade do ar" in nomes:
            achado = next(x for x in placar if x["linha"] == "Qualidade do ar")
            self.assertNotIn("ar", achado["termos"])

    def test_o_nome_da_linha_pesa_mais_que_a_palavra_chave(self):
        """"cancer" nomeia a linha Cancer; "exercicio" e palavra de todas."""
        placar = classificar.pontuar(
            "Exercício físico e fadiga em sobreviventes de câncer de mama", self.linhas)
        pesos = {x["linha"]: x["peso"] for x in placar}
        self.assertGreater(pesos["Câncer"], pesos.get("Psicologia do exercício", 0))

    def test_a_palavra_inteira_e_nao_o_pedaco(self):
        """"dor" nao pode casar dentro de "dormir"."""
        self.assertFalse(classificar._casa("dor", classificar._reduzir("Dormir bem")))
        self.assertTrue(classificar._casa("dor", classificar._reduzir("A dor crônica")))

    def test_o_acento_nao_atrapalha(self):
        a = classificar.pontuar("Fibromialgia e dor", self.linhas)
        b = classificar.pontuar("FIBROMIALGIA E DOR", self.linhas)
        self.assertEqual(a[0]["linha"], b[0]["linha"])


class TestOTituloEmIngles(BaseDoClassificador):
    """Boa parte da producao do LAPE sai em ingles, e as palavras-chave das
    linhas estao todas em portugues. Sem equivalencia, esses artigos caiam
    todos em "sem indicio" -- e o metodo parecia funcionar, porque a lista
    de sugestoes vinha cheia com os titulos em portugues."""

    def test_o_titulo_em_ingles_e_reconhecido(self):
        casos = [
            ("Resistance training protocol with low and high intensity for fibromyalgia",
             "Fibromialgia e doenças reumáticas"),
            ("Cognition and functional capacity in older adults", "Envelhecimento"),
            ("Air quality and running performance in urban environments",
             "Qualidade do ar"),
        ]
        for titulo, esperada in casos:
            with self.subTest(titulo=titulo[:40]):
                self.assertEqual(self.veredito(titulo), ("liga", esperada))

    def test_o_idioma_nao_muda_o_peso(self):
        """Um artigo nao pertence menos a uma linha por estar em ingles."""
        pt = classificar.pontuar("Fibromialgia e treinamento resistido", self.linhas)
        en = classificar.pontuar("Fibromyalgia and resistance training", self.linhas)
        self.assertEqual(pt[0]["linha"], en[0]["linha"])
        self.assertEqual(pt[0]["peso"], en[0]["peso"])

    def test_as_chaves_da_tabela_sao_normalizadas_no_carregamento(self):
        """"qualidade do ar" vira "qualidade ar" de um lado so, e a
        equivalencia nunca era encontrada."""
        self.assertIn("qualidade ar", classificar._EQUIV)
        self.assertIn("qualidade vida", classificar._EQUIV)
        self.assertEqual(len(classificar._EQUIV), len(classificar.EQUIVALENTES))

    def test_toda_equivalencia_tem_termo_do_lado_de_la(self):
        for chave, valores in classificar.EQUIVALENTES.items():
            with self.subTest(termo=chave):
                self.assertTrue(valores)
                for valor in valores:
                    self.assertTrue(classificar._reduzir(valor).strip(), valor)


class TestOQueEleRecusaDecidir(BaseDoClassificador):
    """Recusar e o comportamento certo, e nao uma limitacao."""

    def test_titulo_generico_nao_liga_nada(self):
        self.assertEqual(self.veredito("Um estudo sobre coisas em geral")[0],
                         "sem_indicio")

    def test_titulo_de_duas_linhas_fica_ambiguo(self):
        """Dor e envelhecimento no mesmo titulo: quem decide e quem escreveu."""
        self.assertEqual(
            self.veredito("Dor e envelhecimento: exercício em idosos com fibromialgia")[0],
            "ambiguo")

    def test_uma_palavra_solta_nao_basta(self):
        """Uma palavra num titulo de quinze nao liga artigo a linha."""
        self.assertLess(classificar.PESO_PALAVRA, classificar.PESO_MINIMO)

    def test_as_palavras_de_todo_titulo_nao_pontuam(self):
        """"efeitos", "estudo", "analise" aparecem em toda a area."""
        for vazia in ("efeitos", "estudo", "analise", "revisao", "impacto"):
            with self.subTest(palavra=vazia):
                self.assertIn(vazia, classificar.VAZIAS)

    def test_a_expressao_nao_pontua_duas_vezes(self):
        """"dor cronica" nao pode valer pela expressao E pelas palavras."""
        placar = classificar.pontuar("Dor crônica e exercício", self.linhas)
        for item in placar:
            termos = item["termos"]
            for a in termos:
                for b in termos:
                    if a != b:
                        self.assertNotIn(" " + a + " ", " " + b + " ",
                                         "%r foi contado dentro de %r" % (a, b))


class TestOQueEleNuncaSobrescreve(BaseDoClassificador):

    def test_artigo_com_linha_nao_entra_na_proposta(self):
        alvo = self.linha_id("Câncer")
        self.artigo("Exercício e fadiga em sobreviventes de câncer de mama", alvo)
        saida = classificar.sugerir(self.db)
        self.assertEqual(saida["total_sem_linha"], 0)
        self.assertEqual(saida["sugestoes"], [])

    def test_aplicar_nao_encosta_em_linha_ja_declarada(self):
        """Entre a sugestão e o clique, alguém pode ter cadastrado na mão."""
        certa = self.linha_id("Câncer")
        outra = self.linha_id("Fisioterapia")
        artigo = self.artigo("Exercício e câncer de mama", certa)
        saida = classificar.aplicar(self.db, [{"artigo_id": artigo, "linha_id": outra}])
        self.assertEqual(saida["ligados"], 0)
        self.assertEqual(
            self.db.scalar("SELECT research_line_id FROM articles WHERE id = ?", (artigo,)),
            certa)
        self.assertIn("já ganhou linha", saida["pulados"][0]["motivo"])

    def test_aplicar_grava_o_que_estava_vazio(self):
        artigo = self.artigo("Exercício e câncer de mama")
        alvo = self.linha_id("Câncer")
        saida = classificar.aplicar(self.db, [{"artigo_id": artigo, "linha_id": alvo}])
        self.assertEqual(saida["ligados"], 1)
        self.assertEqual(
            self.db.scalar("SELECT research_line_id FROM articles WHERE id = ?", (artigo,)),
            alvo)

    def test_linha_inexistente_e_recusada(self):
        artigo = self.artigo("Exercício e câncer de mama")
        saida = classificar.aplicar(self.db, [{"artigo_id": artigo, "linha_id": 99999}])
        self.assertEqual(saida["ligados"], 0)
        self.assertIn("linha não existe", saida["pulados"][0]["motivo"])

    def test_artigo_inexistente_e_recusado(self):
        saida = classificar.aplicar(
            self.db, [{"artigo_id": 99999, "linha_id": self.linha_id("Câncer")}])
        self.assertEqual(saida["ligados"], 0)

    def test_lista_vazia_nao_quebra(self):
        self.assertEqual(classificar.aplicar(self.db, [])["ligados"], 0)
        self.assertEqual(classificar.aplicar(self.db, None)["ligados"], 0)


class TestAProposta(BaseDoClassificador):

    def test_as_tres_listas_somam_o_total(self):
        """Nenhum artigo pode sumir entre as três respostas."""
        self.artigo("Exercício e fadiga em sobreviventes de câncer de mama")
        self.artigo("Um estudo sobre coisas em geral")
        self.artigo("Dor e envelhecimento: exercício em idosos com fibromialgia")
        s = classificar.sugerir(self.db)
        self.assertEqual(
            len(s["sugestoes"]) + len(s["ambiguos"]) + len(s["sem_indicio"]),
            s["total_sem_linha"])

    def test_a_proposta_traz_a_evidencia(self):
        """Proposta sem evidência ao lado não se confere: só se aceita no escuro."""
        self.artigo("Exercício e fadiga em sobreviventes de câncer de mama")
        sugestao = classificar.sugerir(self.db)["sugestoes"][0]
        self.assertTrue(sugestao["termos"])
        self.assertIn("cancer", sugestao["termos"])
        self.assertIn("linha_id", sugestao)
        self.assertIn("margem", sugestao)

    def test_sem_linha_cadastrada_nao_propoe_nada(self):
        self.db.execute("UPDATE research_lines SET active = 0")
        self.db.conn.commit()
        self.artigo("Exercício e fadiga em sobreviventes de câncer de mama")
        self.assertEqual(classificar.sugerir(self.db)["sugestoes"], [])

    def test_linha_encerrada_nao_recebe_artigo(self):
        self.db.execute("UPDATE research_lines SET active = 0 WHERE name = 'Câncer'")
        self.db.conn.commit()
        self.artigo("Exercício e fadiga em sobreviventes de câncer de mama")
        for sugestao in classificar.sugerir(self.db)["sugestoes"]:
            self.assertNotEqual(sugestao["linha"], "Câncer")


class TestARotaDeLigacao(unittest.TestCase):
    """A rota é de coordenação, e a proposta nunca grava sozinha."""

    def test_as_duas_rotas_pedem_coordenacao(self):
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        import re
        for caminho in (r"linhas/sugerir", r"linhas/ligar"):
            achado = re.search(r'\^/api/' + caminho + r'/\?\$",\s*(\w+),\s*"(\w+)"', fonte)
            self.assertIsNotNone(achado, caminho)
            self.assertEqual(achado.group(2), "coordenacao")

    def test_o_get_nao_grava(self):
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        corpo = fonte[fonte.index("def route_linhas_sugerir"):
                      fonte.index("def route_linhas_ligar")]
        self.assertNotIn("aplicar", corpo)
        self.assertIn("sugerir", corpo)

    def test_a_tela_manda_so_o_que_foi_marcado(self):
        tela = (ROOT / "scripts" / "lape" / "templates" / "app.html").read_text(
            encoding="utf-8")
        corpo = tela[tela.index("async function desenharLinhasPorTitulo"):
                     tela.index("async function desenharVinculo")]
        self.assertIn("/api/linhas/ligar", corpo)
        self.assertIn("marcados", corpo)
        self.assertIn("termos", corpo)      # a evidência aparece na tela


if __name__ == "__main__":
    unittest.main()
