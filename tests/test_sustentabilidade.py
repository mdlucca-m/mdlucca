#!/usr/bin/env python3
"""O laboratorio se sustenta? -- pessoas com prazo, e o que fica sem dono.

    python3 -m unittest tests.test_sustentabilidade -v

O `fomento.py` responde pelo dinheiro. Este modulo responde pelo que de
fato limita um laboratorio academico: gente com prazo. A pergunta nao e
"quantos vao sair" -- a lista de integrantes ja responde --, e sim
quantos manuscritos em curso ficam SEM NINGUEM quando os prazos
chegarem.

O que estes testes guardam, por ordem de importancia:

  1. quem nao tem prazo declarado nao conta como quem FICA. Tratar
     ausencia de data como permanencia faria a tela afirmar que o
     laboratorio esta seguro justamente onde ele nao sabe;
  2. o orfao -- todos os autores internos saindo -- e separado do
     parcial. E a unica distincao nesta tela que muda uma decisao;
  3. coautor externo nao salva um manuscrito de ficar orfao: ele nao
     responde por ele aqui dentro;
  4. valendo a PRIMEIRA data, e nao a ultima: e ela que tira a pessoa.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import linhas, sustentabilidade as S  # noqa: E402
from lape.agents import curator  # noqa: E402
from lape.db import Database  # noqa: E402

HOJE = date(2026, 9, 16)


class BaseDosPrazos(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "s.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        linhas.instalar(self.db)

    def pessoa(self, nome, externo=0, **campos):
        mid = self.db.member_id(nome, create=True, ao_criar={"is_external": externo})
        sets = ", ".join(f"{k} = ?" for k in campos)
        self.db.execute(
            f"UPDATE members SET is_external = ?, active = 1, left_on = NULL"
            + (f", {sets}" if sets else "") + " WHERE id = ?",
            (externo, *campos.values(), mid))
        return mid

    def artigo(self, titulo, autores, status="em_producao"):
        curator.register(self.db, "articles",
                         {"Título": titulo, "Autores": "; ".join(autores)})
        aid = self.db.scalar("SELECT id FROM articles WHERE title = ?", (titulo,))
        self.db.execute("UPDATE articles SET status = ? WHERE id = ?", (status, aid))
        self.db.conn.commit()
        return aid

    def risco(self, meses=12):
        return S.trabalho_em_risco(self.db, meses=meses, hoje=HOJE)


class TestQuemTemPrazoParaSair(BaseDosPrazos):

    def test_dentro_e_fora_da_janela(self):
        self.pessoa("Loiane", thesis_due_on="2026-11-30")
        self.pessoa("Marcele", scholarship_until="2029-06-30")
        saidas = S.saidas_previstas(self.db, hoje=HOJE)
        self.assertEqual([x["quem"] for x in saidas["saem"]], ["Loiane"])
        self.assertEqual([x["quem"] for x in saidas["depois"]], ["Marcele"])

    def test_sem_prazo_declarado_nao_conta_como_quem_fica(self):
        """A trava de honestidade desta tela.

        Ausencia de data nao e permanencia: e ausencia de data. Somar
        essas pessoas a quem fica faria a tela dizer "esta tudo sob
        controle" justamente onde o laboratorio nao sabe.
        """
        self.pessoa("Vilarino")
        saidas = S.saidas_previstas(self.db, hoje=HOJE)
        self.assertEqual([x["quem"] for x in saidas["sem_prazo"]], ["Vilarino"])
        self.assertEqual(saidas["saem"], [])
        self.assertEqual(saidas["depois"], [])

    def test_vale_a_primeira_data_e_nao_a_ultima(self):
        """E a primeira que tira a pessoa do laboratorio."""
        self.pessoa("Nayara", scholarship_until="2026-10-31",
                    thesis_due_on="2027-08-31")
        saem = S.saidas_previstas(self.db, hoje=HOJE)["saem"]
        self.assertEqual(saem[0]["quando"], "2026-10-31")
        self.assertEqual(saem[0]["motivo"], "fim da bolsa")

    def test_prazo_que_ja_venceu_aparece_marcado(self):
        """Bolsa vencida e o caso mais urgente, e nao o menos."""
        self.pessoa("Atrasada", scholarship_until="2026-03-01")
        saem = S.saidas_previstas(self.db, hoje=HOJE)["saem"]
        self.assertTrue(saem[0]["ja_passou"])
        self.assertLess(saem[0]["dias"], 0)

    def test_quem_saiu_e_quem_e_externo_ficam_de_fora(self):
        self.pessoa("Externa", externo=1, thesis_due_on="2026-10-01")
        saiu = self.pessoa("Foi_embora", thesis_due_on="2026-10-01")
        self.db.execute("UPDATE members SET left_on = '2026-01-01' WHERE id = ?", (saiu,))
        saidas = S.saidas_previstas(self.db, hoje=HOJE)
        nomes = [x["quem"] for x in saidas["saem"] + saidas["depois"]
                 + saidas["sem_prazo"]]
        self.assertNotIn("Externa", nomes)
        self.assertNotIn("Foi_embora", nomes)


class TestOQueFicaSemDono(BaseDosPrazos):

    def test_orfao_e_o_manuscrito_em_que_todos_saem(self):
        self.pessoa("Loiane", thesis_due_on="2026-11-30")
        self.pessoa("Nayara", scholarship_until="2027-01-31")
        self.artigo("Orfao", ["Loiane", "Nayara"])
        r = self.risco()
        self.assertEqual([x["titulo"] for x in r["orfaos"]], ["Orfao"])
        self.assertEqual(r["orfaos"][0]["ficam"], [])
        self.assertEqual(len(r["orfaos"][0]["saindo"]), 2)

    def test_parcial_e_quando_alguem_fica(self):
        """Perde tempo, nao perde dono -- e e outra decisao."""
        self.pessoa("Loiane", thesis_due_on="2026-11-30")
        self.pessoa("Vilarino")
        self.artigo("Parcial", ["Loiane", "Vilarino"])
        r = self.risco()
        self.assertEqual(r["orfaos"], [])
        self.assertEqual([x["titulo"] for x in r["parciais"]], ["Parcial"])
        self.assertEqual(r["parciais"][0]["ficam"], ["Vilarino"])

    def test_coautor_externo_nao_salva_do_orfao(self):
        """Ele nao responde pelo manuscrito aqui dentro.

        Conta-lo como quem fica transformaria um orfao em "parcial" sem
        que ninguem tivesse assumido nada -- e o orfao e justamente o que
        precisa de decisao.
        """
        self.pessoa("Loiane", thesis_due_on="2026-11-30")
        self.pessoa("DeFora", externo=1)
        self.artigo("Com externo", ["Loiane", "DeFora"])
        r = self.risco()
        self.assertEqual([x["titulo"] for x in r["orfaos"]], ["Com externo"])

    def test_publicado_e_rejeitado_nao_estao_em_curso(self):
        """Um nao precisa de ninguem; o outro nao tem para onde ir."""
        self.pessoa("Loiane", thesis_due_on="2026-11-30")
        self.artigo("Saiu", ["Loiane"], status="publicado")
        self.artigo("Recusado", ["Loiane"], status="rejeitado")
        self.artigo("Em curso", ["Loiane"])
        r = self.risco()
        self.assertEqual(r["em_curso"], 1)
        self.assertEqual([x["titulo"] for x in r["orfaos"]], ["Em curso"])

    def test_sem_autoria_interna_nao_e_orfao_nem_firme(self):
        """Nao ha o que afirmar: e autoria nao cadastrada, e nao risco.

        Chamar de firme diria que esta seguro; de orfao, que esta
        perdido. A contagem sai a parte para a tela poder dizer
        "confira a autoria destes".
        """
        self.pessoa("SoExterno", externo=1)
        self.artigo("Sem ninguem de dentro", ["SoExterno"])
        r = self.risco()
        self.assertEqual(r["sem_autoria_interna"], 1)
        self.assertEqual(r["orfaos"], [])
        self.assertEqual(r["firmes"], [])

    def test_a_janela_muda_o_resultado(self):
        """Seis meses e doze meses respondem perguntas diferentes."""
        self.pessoa("Loiane", thesis_due_on="2027-06-30")
        self.artigo("Depende da janela", ["Loiane"])
        self.assertEqual(self.risco(meses=6)["orfaos"], [])
        self.assertEqual(len(self.risco(meses=12)["orfaos"]), 1)

    def test_as_tres_caixas_somam_com_o_total(self):
        """Se nao somam, alguma coisa desapareceu da tela."""
        self.pessoa("Loiane", thesis_due_on="2026-11-30")
        self.pessoa("Vilarino")
        self.pessoa("DeFora", externo=1)
        self.artigo("A", ["Loiane"])
        self.artigo("B", ["Loiane", "Vilarino"])
        self.artigo("C", ["Vilarino"])
        self.artigo("D", ["DeFora"])
        r = self.risco()
        self.assertEqual(
            len(r["orfaos"]) + len(r["parciais"]) + len(r["firmes"])
            + r["sem_autoria_interna"], r["em_curso"])


class TestReposicao(BaseDosPrazos):

    def test_entradas_e_saidas_por_ano(self):
        a = self.pessoa("Entrou", joined_on="2025-03-01")
        b = self.pessoa("Saiu", joined_on="2023-03-01")
        self.db.execute("UPDATE members SET left_on = '2025-12-01' WHERE id = ?", (b,))
        self.db.conn.commit()
        por_ano = {x["ano"]: x for x in S.renovacao(self.db, hoje=HOJE)}
        self.assertEqual(por_ano[2025]["entraram"], 1)
        self.assertEqual(por_ano[2025]["sairam"], 1)
        self.assertEqual(por_ano[2025]["saldo"], 0)
        self.assertEqual(por_ano[2023]["entraram"], 1)

    def test_a_janela_cobre_os_cinco_anos_ate_hoje(self):
        anos = [x["ano"] for x in S.renovacao(self.db, hoje=HOJE)]
        self.assertEqual(anos, [2022, 2023, 2024, 2025, 2026])


class TestOPanorama(BaseDosPrazos):

    def test_junta_pessoas_trabalho_reposicao_e_dinheiro(self):
        self.pessoa("Loiane", thesis_due_on="2026-11-30")
        self.artigo("Um", ["Loiane"])
        p = S.panorama(self.db, hoje=HOJE)
        for chave in ("pessoas", "trabalho", "renovacao", "dinheiro", "hoje"):
            with self.subTest(chave=chave):
                self.assertIn(chave, p)
        self.assertEqual(len(p["trabalho"]["orfaos"]), 1)

    def test_o_dinheiro_vem_do_fomento_e_nao_e_refeito_aqui(self):
        """Duas contas para a mesma pergunta divergem no primeiro conserto.

        O teste olha as TABELAS consultadas, e nao palavras: "captado"
        aparece na docstring deste modulo justamente para explicar que o
        dinheiro e do `fomento` -- e procurar a palavra reprovava a
        explicacao.
        """
        fonte = (ROOT / "scripts" / "lape" / "sustentabilidade.py").read_text(
            encoding="utf-8")
        self.assertIn("fomento.painel(db)", fonte)
        for tabela in ("editais", "submissoes_fomento", "valor_aprovado"):
            with self.subTest(tabela=tabela):
                self.assertNotIn(f"FROM {tabela}", fonte)
                self.assertNotIn(f"JOIN {tabela}", fonte)

    def test_banco_vazio_nao_estoura(self):
        p = S.panorama(self.db, hoje=HOJE)
        self.assertEqual(p["pessoas"]["n_ativos"], 0)
        self.assertEqual(p["trabalho"]["em_curso"], 0)


class TestARotaEATela(unittest.TestCase):
    """A rota, com sessao de verdade -- e a tela, olhada na fonte.

    Bolsa e prazo de tese sao dado da vida de uma pessoa, e nao de
    producao. O `metrics.SO_DA_COORDENACAO` ja declara isso, e a razao
    esta escrita la: o payload do painel vai INTEIRO para dentro do HTML
    -- para o arquivo exportado em docs/, para o mural que fica numa TV, e
    para qualquer um que abra o painel com LAPE_PUBLIC_DASHBOARD ligado.
    Ver a tela nao e a unica forma de ler um JSON embutido na pagina.

    Por isso esta tela e rota AO VIVO e so da coordenacao -- e os testes
    guardam as duas coisas.
    """

    @classmethod
    def setUpClass(cls):
        import json
        import threading
        from http.server import ThreadingHTTPServer

        from lape import api, auth

        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "rotas.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        linhas.instalar(db)
        auth.create_account(db, "Coordena", "coord@udesc.br", "senhaforte123",
                            role="coordenacao")
        auth.create_account(db, "Integra", "integra@udesc.br", "senhaforte123",
                            role="integrante")
        # vinculo academico de proposito diferente do perfil de permissao
        db.execute("UPDATE members SET role = 'professor' WHERE login = ?",
                   ("coord@udesc.br",))
        db.close()

        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *a, **k: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.json = json

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def pedir(self, caminho, login):
        import urllib.error
        import urllib.request

        from lape import api

        corpo = self.json.dumps({"login": login, "senha": "senhaforte123"}).encode()
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login", data=corpo,
            method="POST", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=30) as r:
            cookie = (r.headers.get("Set-Cookie") or "").split("=")[1].split(";")[0]
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{caminho}",
            headers={"Cookie": f"{api.COOKIE_NAME}={cookie}"})
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, self.json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            return exc.code, self.json.loads(exc.read().decode() or "{}")

    def test_a_coordenacao_ve(self):
        status, corpo = self.pedir("/api/sustentabilidade", "coord@udesc.br")
        self.assertEqual(status, 200)
        for chave in ("pessoas", "trabalho", "renovacao"):
            self.assertIn(chave, corpo)

    def test_integrante_nao_ve(self):
        """E dado da vida de alguem, e nao de producao."""
        status, _ = self.pedir("/api/sustentabilidade", "integra@udesc.br")
        self.assertEqual(status, 403)

    def test_a_janela_pedida_e_respeitada_e_limitada(self):
        _, corpo = self.pedir("/api/sustentabilidade?meses=6", "coord@udesc.br")
        self.assertEqual(corpo["janela_meses"], 6)
        # janela negativa olharia para tras; de dez anos e ficcao
        for pedido, esperado in (("meses=-3", 1), ("meses=999", 60),
                                 ("meses=abacaxi", S.MESES_DA_JANELA)):
            with self.subTest(pedido=pedido):
                _, c = self.pedir("/api/sustentabilidade?" + pedido, "coord@udesc.br")
                self.assertEqual(c["janela_meses"], esperado)

    def test_a_tela_le_o_perfil_de_PERMISSAO_e_nao_o_vinculo(self):
        """`role` e "Professor(a)" e nao concede nada; `user_role` concede.

        Ler o campo errado ja custou dois defeitos nesta casa, nos dois
        casos deixando a coordenacao sem ver o que e dela -- e o teste de
        rota acima nao pega este, porque ele mora no JavaScript.
        """
        js = (ROOT / "scripts" / "lape" / "templates" / "dashboard.js").read_text(
            encoding="utf-8")
        corpo = js[js.index("function podeVer("):]
        corpo = corpo[:corpo.index("\n}")]
        self.assertIn("USER.user_role", corpo)
        self.assertNotIn("USER.role", corpo)

    def test_a_tela_nao_aparece_sem_servidor_nem_sem_coordenacao(self):
        js = (ROOT / "scripts" / "lape" / "templates" / "dashboard.js").read_text(
            encoding="utf-8")
        corpo = js[js.index('view("sustenta"'):]
        corpo = corpo[:corpo.index('view("correlacoes"')]
        self.assertIn("if (!LIVE)", corpo)
        self.assertIn('podeVer("coordenacao")', corpo)

    def test_a_tela_nao_refaz_a_conta_no_navegador(self):
        """Duas contas para a mesma pergunta divergem no primeiro conserto."""
        js = (ROOT / "scripts" / "lape" / "templates" / "dashboard.js").read_text(
            encoding="utf-8")
        corpo = js[js.index('view("sustenta"'):]
        corpo = corpo[:corpo.index('view("correlacoes"')]
        self.assertIn("/api/sustentabilidade", corpo)
        # nenhuma data comparada no navegador
        for conta in ("new Date(", "scholarship_until", "thesis_due_on"):
            with self.subTest(conta=conta):
                self.assertNotIn(conta, corpo)


if __name__ == "__main__":
    unittest.main()
