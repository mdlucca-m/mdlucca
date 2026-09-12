#!/usr/bin/env python3
"""Separar cinquenta e quatro fichas sem apagar nenhuma.

    python3 -m unittest tests.test_vinculo_lote -v

O painel do laboratorio mostrava "58 integrantes e 0 coautores", com 54
deles sem vinculo declarado. Zero coautores num grupo com centena de
artigos e impossivel: aqueles 54 eram coautores que nunca foram separados.

O pedido que chegou foi "exclua". Apagar nao apaga o nome do artigo -- ele
fica escrito em `author_name` --, mas corta a ligacao pessoa<->artigo, e
essa nao volta: a pessoa some de "Por integrante", da rede de coautoria e
da atribuicao de citacoes, e so volta redigitada.

Entao aqui nada e apagado. Ha dois destinos, e os dois sao reversiveis:

  COAUTOR      para quem assinou artigo conosco sem ser do grupo. Some da
               equipe e do organograma, continua ligado aos artigos.
  ARQUIVADA    para a ficha sem vinculo E sem artigo nenhum -- resto de
               importacao, nome digitado duas vezes. Nao e coautor de
               coisa alguma: chamar assim inventaria uma autoria.

Estes testes existem para que "em lote" continue sendo rapido sem virar
descuidado.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import vinculo  # noqa: E402
from lape.db import Database  # noqa: E402
from lape.util import norm_key  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class BaseDoLote(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "v.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()

    def ficha(self, nome: str, **extra) -> int:
        campos = {"full_name": nome, "name_key": norm_key(nome),
                  "is_external": 0, "active": 1}
        campos.update(extra)
        self.db.execute("INSERT INTO members (%s) VALUES (%s)"
                        % (", ".join(campos), ", ".join("?" * len(campos))),
                        tuple(campos.values()))
        self.db.conn.commit()
        return self.db.scalar("SELECT id FROM members WHERE name_key = ?",
                              (norm_key(nome),))

    def artigo(self, titulo: str, member_id: int, ordem: int = 1) -> int:
        chave = norm_key(titulo)
        existe = self.db.scalar("SELECT id FROM articles WHERE title_key = ?", (chave,))
        if not existe:
            self.db.execute(
                "INSERT INTO articles (title, title_key, status) VALUES (?, ?, 'publicado')",
                (titulo, chave))
            existe = self.db.scalar("SELECT id FROM articles WHERE title_key = ?", (chave,))
        self.db.execute(
            "INSERT INTO article_authors (article_id, member_id, author_name, author_order)"
            " VALUES (?, ?, ?, ?)", (existe, member_id, "x", ordem))
        self.db.conn.commit()
        return existe


class TestOLoteDeCoautores(BaseDoLote):

    def povoar(self, quantos=6):
        ids = []
        for i in range(quantos):
            pessoa = self.ficha("Coautor %02d" % i)
            self.artigo("Artigo %02d" % i, pessoa)
            ids.append(pessoa)
        return ids

    def test_move_todos_de_uma_vez(self):
        ids = self.povoar()
        saida = vinculo.marcar_em_lote(self.db, ids, coautor=True)
        self.assertEqual(saida["movidos"], len(ids))
        self.assertEqual(vinculo.contagem(self.db)["coautores"], len(ids))

    def test_nao_apaga_ficha_nenhuma(self):
        """Apagar corta a ligação pessoa↔artigo, e essa não volta."""
        ids = self.povoar()
        vinculo.marcar_em_lote(self.db, ids, coautor=True)
        vivas = self.db.scalar("SELECT COUNT(*) FROM members WHERE id IN (%s)"
                               % ",".join("?" * len(ids)), tuple(ids))
        self.assertEqual(vivas, len(ids))

    def test_a_autoria_acompanha(self):
        """Senão a tela do artigo diz "externo" e a ficha diz "do LAPE"."""
        ids = self.povoar(3)
        vinculo.marcar_em_lote(self.db, ids, coautor=True)
        externas = self.db.scalar(
            "SELECT COUNT(*) FROM article_authors WHERE member_id IN (%s)"
            "   AND is_external = 1" % ",".join("?" * len(ids)), tuple(ids))
        self.assertEqual(externas, len(ids))

    def test_devolve_o_que_desfazer(self):
        """Voltar tem de ser um pedido só, e não cinquenta e quatro."""
        ids = self.povoar(4)
        saida = vinculo.marcar_em_lote(self.db, ids, coautor=True)
        self.assertEqual(sorted(saida["desfazer"]), sorted(ids))
        vinculo.marcar_em_lote(self.db, saida["desfazer"], coautor=False)
        self.assertEqual(vinculo.contagem(self.db)["coautores"], 0)

    def test_quem_ganhou_vinculo_no_meio_e_recusado(self):
        """Entre a tela abrir e o botão ser clicado, a pessoa pode ter se
        cadastrado — e aí ela não é mais candidata a coautora."""
        ids = self.povoar(3)
        self.db.execute("UPDATE members SET role = 'doutorando' WHERE id = ?", (ids[0],))
        self.db.conn.commit()
        saida = vinculo.marcar_em_lote(self.db, ids, coautor=True)
        self.assertEqual(saida["movidos"], 2)
        self.assertEqual(len(saida["recusados"]), 1)
        self.assertEqual(
            self.db.scalar("SELECT is_external FROM members WHERE id = ?", (ids[0],)), 0)

    def test_id_que_nao_existe_nao_quebra(self):
        saida = vinculo.marcar_em_lote(self.db, [999999], coautor=True)
        self.assertEqual(saida["movidos"], 0)
        self.assertTrue(saida["recusados"])

    def test_lista_vazia_nao_faz_nada(self):
        self.assertEqual(vinculo.marcar_em_lote(self.db, [])["movidos"], 0)
        self.assertEqual(vinculo.marcar_em_lote(self.db, None)["movidos"], 0)

    def test_a_volta_nao_exige_ser_candidato(self):
        """Promover de volta é sempre possível: é a correção de um engano."""
        ids = self.povoar(2)
        vinculo.marcar_em_lote(self.db, ids, coautor=True)
        volta = vinculo.marcar_em_lote(self.db, ids, coautor=False)
        self.assertEqual(volta["movidos"], 2)


class TestAsFichasVazias(BaseDoLote):
    """Sem vínculo E sem artigo: não é coautor de coisa alguma."""

    def test_quem_assinou_artigo_nao_e_ficha_vazia(self):
        com = self.ficha("Assinou Algo")
        self.artigo("Um artigo", com)
        self.ficha("Nao Assinou Nada")
        soltas = vinculo.soltas(self.db)
        nomes = {f["full_name"] for f in soltas}
        self.assertIn("Nao Assinou Nada", nomes)
        self.assertNotIn("Assinou Algo", nomes)

    def test_quem_tem_vinculo_nao_e_ficha_vazia(self):
        self.ficha("Tem Funcao", role="professor")
        self.ficha("Tem Email", email="x@udesc.br")
        self.assertEqual(vinculo.soltas(self.db), [])

    def test_as_duas_listas_nao_se_sobrepoem(self):
        """Uma ficha não pode ser proposta como coautora E como vazia."""
        com = self.ficha("Assinou")
        self.artigo("Artigo", com)
        self.ficha("Vazia")
        candidatos = {c["id"] for c in vinculo.candidatos(self.db)}
        vazias = {f["id"] for f in vinculo.soltas(self.db)}
        self.assertEqual(candidatos & vazias, set())

    def test_arquivar_tira_da_equipe_sem_apagar(self):
        ids = [self.ficha("Vazia %d" % i) for i in range(5)]
        antes = vinculo.contagem(self.db)["pesquisadores"]
        saida = vinculo.arquivar_em_lote(self.db, ids)
        self.assertEqual(saida["movidas"], 5)
        self.assertEqual(vinculo.contagem(self.db)["pesquisadores"], antes - 5)
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM members WHERE id IN (%s)"
                           % ",".join("?" * len(ids)), tuple(ids)), 5)

    def test_arquivar_se_desfaz(self):
        ids = [self.ficha("Vazia %d" % i) for i in range(3)]
        antes = vinculo.contagem(self.db)["pesquisadores"]
        saida = vinculo.arquivar_em_lote(self.db, ids)
        vinculo.arquivar_em_lote(self.db, saida["desfazer"], ativo=True)
        self.assertEqual(vinculo.contagem(self.db)["pesquisadores"], antes)

    def test_nao_arquiva_quem_deixou_de_ser_vazia(self):
        """Arquivar gente de verdade é escondê-la, e não limpá-la."""
        ids = [self.ficha("Vazia %d" % i) for i in range(3)]
        self.artigo("Apareceu um artigo", ids[0])
        saida = vinculo.arquivar_em_lote(self.db, ids)
        self.assertEqual(saida["movidas"], 2)
        self.assertEqual(
            self.db.scalar("SELECT active FROM members WHERE id = ?", (ids[0],)), 1)

    def test_a_contagem_anuncia_as_vazias(self):
        self.ficha("Vazia")
        self.assertEqual(vinculo.contagem(self.db)["soltas"], 1)


class TestARotaDeLote(unittest.TestCase):

    def setUp(self):
        self.api = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")

    def test_e_de_coordenacao(self):
        import re
        achado = re.search(r'\^/api/equipe/vinculo/lote/\?\$",\s*\w+,\s*"(\w+)"', self.api)
        self.assertIsNotNone(achado)
        self.assertEqual(achado.group(1), "coordenacao")

    def test_tem_teto_de_tamanho(self):
        corpo = self.api[self.api.index("def route_vinculo_lote"):]
        corpo = corpo[:corpo.index("\ndef ")]
        self.assertIn("500", corpo)

    def test_as_duas_acoes_passam_pela_mesma_porta(self):
        corpo = self.api[self.api.index("def route_vinculo_lote"):]
        corpo = corpo[:corpo.index("\ndef ")]
        self.assertIn('acao") == "arquivar"', corpo)
        self.assertIn("marcar_em_lote", corpo)


class TestOCartaoDaEquipe(unittest.TestCase):
    """Era uma tabela de duas colunas num cartão de 300px."""

    def setUp(self):
        self.dash = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
        self.bloco = self.dash[self.dash.index('const pessoas = card("Nossa equipe"'):
                               self.dash.index("/* ---------------- objetivos")]

    def test_nao_e_mais_tabelinha(self):
        self.assertNotIn('class: "facts"', self.bloco)

    def test_cada_vinculo_virou_cartao(self):
        self.assertIn("kpi({", self.bloco)
        self.assertIn('class: "grid g4"', self.bloco)

    def test_o_cartao_ocupa_a_largura_toda(self):
        self.assertIn('pessoas.className = "card largo"', self.dash)

    def test_todo_vinculo_tem_desenho(self):
        import re
        mapa = self.dash[self.dash.index("const ICONE_DO_VINCULO = {"):
                         self.dash.index("const VINCULO_NOME = {")]
        desenhados = set(re.findall(r'"([^"]+)": "\w+"', mapa))
        nomes = self.dash[self.dash.index("const VINCULO_NOME = {"):]
        nomes = nomes[:nomes.index("};")]
        rotulos = set(re.findall(r'"([^"]+)"', nomes))
        self.assertEqual(rotulos - desenhados, set())

    def test_a_leitura_diz_onde_resolver(self):
        """Diagnóstico sem saída deixa o número piscando para sempre."""
        self.assertIn("Administração", self.bloco)
        self.assertIn("sem apagar ficha nenhuma", self.bloco)


if __name__ == "__main__":
    unittest.main()
