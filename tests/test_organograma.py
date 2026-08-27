#!/usr/bin/env python3
"""Testes do organograma: vinculo, orientacao e ligacao automatica.

    python3 -m unittest discover -s tests -v

O organograma nao e desenhado a mao: ele cai do `advisor_id` de cada ficha.
Isso o torna barato de manter e caro de errar -- um vinculo mal normalizado
espalha a mesma pessoa por tres caixas, e uma ligacao automatica generosa
demais coloca gente em projeto que nao e dela. E o que se checa aqui.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth, ingest_excel, mapping, metrics  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class TestVocabularioDeVinculo(unittest.TestCase):
    def test_sinonimos_caem_na_mesma_forma(self):
        from lape.mapping import map_value

        for escrito, esperado in [
            ("IC", "bolsista_ic"),
            ("iniciação científica", "bolsista_ic"),
            ("Bolsista de IC", "bolsista_ic"),
            ("PIBIC", "bolsista_ic"),
            ("Doutorado", "doutorando"),
            ("doutoranda", "doutorando"),
            ("Mestranda", "mestrando"),
            ("professora", "professor"),
            ("orientadora", "professor"),
            ("PIBEX", "bolsista_extensao"),
            ("voluntária", "voluntario"),
            ("pós-doc", "pos_doutorado"),
        ]:
            with self.subTest(escrito=escrito):
                self.assertEqual(map_value(escrito, mapping.ROLE_MAP), esperado)

    def test_todo_vinculo_tem_rotulo(self):
        for codigo, rotulo, _ in mapping.VINCULOS:
            self.assertEqual(mapping.ROLE_LABEL[codigo], rotulo)

    def test_quem_orienta_e_quem_e_orientado_nao_se_misturam(self):
        # tecnico nao orienta e nao e orientado: nao pode estar em nenhum dos dois
        self.assertNotIn("tecnico", mapping.ORIENTAM)
        self.assertNotIn("tecnico", mapping.ORIENTADOS)
        self.assertNotIn("colaborador", mapping.ORIENTADOS)


class TestLigacaoAutomatica(unittest.TestCase):
    """Quem se cadastra apontando o orientador ja entra no trabalho dele."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "org.sqlite")
        self.db.migrate()
        ingest_excel.ingest_research_lines(self.db, [
            {"code": "PEX", "name": "Psicologia do exercício"},
            {"code": "DOR", "name": "Dor crônica"},
        ])
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Marina Rossetto Cardoso", "role": "professor",
             "research_line": "Psicologia do exercício"},
            {"full_name": "Helena Krieger Sampaio", "role": "professora",
             "research_line": "Dor crônica"},
        ])
        ingest_excel.ingest_projects(self.db, [
            {"code": "PEX-1", "name": "Exercício e saúde mental",
             "research_line": "Psicologia do exercício", "status": "em andamento",
             "coordinator": "Marina Rossetto Cardoso"},
            {"code": "DOR-1", "name": "Dor e movimento", "research_line": "Dor crônica",
             "status": "em andamento", "coordinator": "Helena Krieger Sampaio"},
            {"code": "PEX-0", "name": "Projeto encerrado",
             "research_line": "Psicologia do exercício", "status": "concluído",
             "coordinator": "Marina Rossetto Cardoso"},
        ])

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def projetos_de(self, nome: str) -> set[str]:
        return {r["name"] for r in self.db.dicts(
            "SELECT p.name FROM project_members pm JOIN projects p ON p.id = pm.project_id"
            " JOIN members m ON m.id = pm.member_id WHERE m.full_name = ?", (nome,))}

    def test_entra_no_projeto_em_andamento_do_orientador(self):
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Eduardo Rampinelli Souza", "role": "mestrando",
             "advisor": "Marina Rossetto Cardoso",
             "research_line": "Psicologia do exercício"},
        ])
        self.assertEqual(self.projetos_de("Eduardo Rampinelli Souza"),
                         {"Exercício e saúde mental"})

    def test_projeto_concluido_fica_de_fora(self):
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Ana Clara Ribas", "role": "IC",
             "advisor": "Marina Rossetto Cardoso",
             "research_line": "Psicologia do exercício"},
        ])
        self.assertNotIn("Projeto encerrado", self.projetos_de("Ana Clara Ribas"))

    def test_projeto_de_outra_linha_nao_e_ligado(self):
        # o orientador coordena projeto nas duas linhas; so o da linha da
        # pessoa conta -- senao a rede vira uma teia sem significado
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Vinicius Portela", "role": "mestrando",
             "advisor": "Helena Krieger Sampaio", "research_line": "Dor crônica"},
        ])
        self.assertEqual(self.projetos_de("Vinicius Portela"), {"Dor e movimento"})

    def test_a_linha_desce_do_orientador(self):
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Pedro Lauth Meurer", "role": "bolsista de IC",
             "advisor": "Helena Krieger Sampaio"},
        ])
        linha = self.db.scalar(
            "SELECT rl.name FROM members m JOIN research_lines rl"
            " ON rl.id = m.research_line_id WHERE m.full_name = ?", ("Pedro Lauth Meurer",))
        self.assertEqual(linha, "Dor crônica")

    def test_papel_ja_registrado_nao_e_sobrescrito(self):
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Bruno Cavalheiro", "role": "doutorando",
             "advisor": "Marina Rossetto Cardoso",
             "research_line": "Psicologia do exercício"},
        ])
        membro = self.db.scalar("SELECT id FROM members WHERE full_name = ?",
                                ("Bruno Cavalheiro",))
        # busca pelo nome: o `code` e normalizado na ingestao ("PEX-1" vira "pex_1")
        projeto = self.db.scalar("SELECT id FROM projects WHERE name = ?",
                                 ("Exercício e saúde mental",))
        self.db.execute("UPDATE project_members SET role = 'coordenacao'"
                        " WHERE member_id = ? AND project_id = ?", (membro, projeto))
        self.db.conn.commit()
        # segunda passagem da mesma planilha: a correcao a mao tem de sobreviver
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Bruno Cavalheiro", "role": "doutorando",
             "advisor": "Marina Rossetto Cardoso",
             "research_line": "Psicologia do exercício"},
        ])
        papel = self.db.scalar(
            "SELECT role FROM project_members WHERE member_id = ? AND project_id = ?",
            (membro, projeto))
        self.assertEqual(papel, "coordenacao")

    def test_sem_orientador_nada_acontece(self):
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Beatriz Delgado", "role": "técnica"},
        ])
        self.assertEqual(self.projetos_de("Beatriz Delgado"), set())


class TestDesenhoDoOrganograma(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "org.sqlite")
        self.db.migrate()
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Marina Rossetto Cardoso", "role": "coordenacao"},
            {"full_name": "Otávio Bernardes Lemos", "role": "professor"},
            {"full_name": "Tiago Meireles Farias", "role": "doutorando",
             "advisor": "Otávio Bernardes Lemos", "thesis_title": "Uma tese",
             "thesis_kind": "doutorado", "thesis_due_on": "2027-07-31"},
            {"full_name": "Nathália Costa", "role": "mestranda",
             "advisor": "Marina Rossetto Cardoso"},
            {"full_name": "Beatriz Delgado", "role": "técnica"},
        ])

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_a_coordenacao_e_a_unica_raiz(self):
        org = metrics.organograma(self.db)
        chefe = self.db.scalar("SELECT id FROM members WHERE full_name = ?",
                               ("Marina Rossetto Cardoso",))
        self.assertEqual(org["roots"], [chefe])
        # o professor desceu para debaixo dela, por uma aresta de coordenacao
        # -- que nao e orientacao, e o desenho distingue as duas
        tipos = {e["kind"] for e in org["edges"]}
        self.assertIn("coordenacao", tipos)
        self.assertIn("orientacao", tipos)

    def test_tecnico_nao_entra_na_lista_de_pendencias(self):
        org = metrics.organograma(self.db)
        nomes = {p["full_name"] for p in org["sem_orientador"]}
        self.assertNotIn("Beatriz Delgado", nomes)

    def test_orientando_sem_orientador_aparece_como_pendencia(self):
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Solto da Silva", "role": "mestrando"},
        ])
        org = metrics.organograma(self.db)
        self.assertIn("Solto da Silva",
                      {p["full_name"] for p in org["sem_orientador"]})

    def test_tese_entra_na_lista_com_orientador(self):
        org = metrics.organograma(self.db)
        teses = {t["full_name"]: t for t in org["teses"]}
        self.assertIn("Tiago Meireles Farias", teses)
        self.assertEqual(teses["Tiago Meireles Farias"]["kind"], "tese")
        self.assertEqual(teses["Tiago Meireles Farias"]["advisor"], "Otávio Bernardes Lemos")

    def test_ciclo_de_orientacao_nao_trava_o_desenho(self):
        # A orienta B e B orienta A: nao deveria acontecer, mas se acontecer
        # o painel nao pode entrar em laco -- ele mostra o que der e segue
        a = self.db.scalar("SELECT id FROM members WHERE full_name = ?",
                           ("Marina Rossetto Cardoso",))
        b = self.db.scalar("SELECT id FROM members WHERE full_name = ?",
                           ("Otávio Bernardes Lemos",))
        self.db.execute("UPDATE members SET advisor_id = ? WHERE id = ?", (b, a))
        self.db.execute("UPDATE members SET advisor_id = ? WHERE id = ?", (a, b))
        self.db.conn.commit()
        org = metrics.organograma(self.db)
        self.assertEqual(len(org["people"]), 5)


class TestVocabularioDaPagina(unittest.TestCase):
    """A lista do formulario e a do servidor tem de ser a mesma lista.

    A pagina repete o vocabulario para abrir sem consultar o servidor. O
    preco disso e a divergencia silenciosa: alguem acrescenta um vinculo no
    Python, o formulario continua sem ele, e ninguem percebe ate faltar uma
    opcao na tela. Este teste e o que cobra a segunda copia.
    """

    def opcoes(self, nome: str) -> list[str]:
        texto = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        bloco = texto.split("const " + nome + " = [", 1)[1].split("\n];", 1)[0]
        return re.findall(r'\{value: "([a-z_]+)"', bloco)

    def test_vinculos(self):
        self.assertEqual(self.opcoes("VINCULO_OPTS"),
                         [codigo for codigo, _, _ in mapping.VINCULOS])

    def test_tipos_de_trabalho(self):
        self.assertEqual(set(self.opcoes("TESE_TIPO_OPTS")),
                         set(mapping.THESIS_KIND_MAP.values()))

    def test_situacoes_do_trabalho(self):
        self.assertEqual(set(self.opcoes("TESE_SITUACAO_OPTS")),
                         set(mapping.THESIS_STATUS_MAP.values()))

    def test_o_mural_sabe_nomear_todo_tipo_de_trabalho(self):
        # sem o mapa completo, o relatorio de um bolsista de IC ia para a
        # parede anunciado como "Tese" -- e quem passa na frente acredita
        texto = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        bloco = texto.split("const TIPO_TRABALHO = {", 1)[1].split("\n};", 1)[0]
        nomeados = set(re.findall(r"(\w+):", bloco))
        self.assertEqual(nomeados, set(mapping.THESIS_KIND_MAP.values()))

    def test_rotulos_do_painel_cobrem_as_situacoes(self):
        texto = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
        bloco = texto.split("const TESE_SITUACAO = {", 1)[1].split("\n};", 1)[0]
        rotulados = set(re.findall(r"(\w+):", bloco))
        self.assertEqual(rotulados, set(mapping.THESIS_STATUS_MAP.values()))


class TestRotaDaEquipe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "api.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        ingest_excel.ingest_members(db, [
            {"full_name": "Marina Rossetto Cardoso", "role": "professor"},
            {"full_name": "Tiago Meireles Farias", "role": "doutorando"},
            {"full_name": "Parceiro de Fora", "role": "colaborador", "is_external": "Sim"},
        ])
        auth.create_account(db, "Tiago Meireles Farias", "tiago@udesc.br", "senhaforte123",
                            role="integrante")
        db.close()
        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *args, **kwargs: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def buscar(self, caminho, cookie=None):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}{caminho}")
        if cookie:
            pedido.add_header("Cookie", f"{api.COOKIE_NAME}={cookie}")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                return resposta.status, json.loads(resposta.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    def entrar(self):
        corpo = json.dumps({"login": "tiago@udesc.br", "senha": "senhaforte123"}).encode()
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login", data=corpo, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return (resposta.headers.get("Set-Cookie") or "").split("=")[1].split(";")[0]

    def test_sem_sessao_nao_lista_a_equipe(self):
        status, _ = self.buscar("/api/equipe")
        self.assertEqual(status, 401)

    def test_integrante_ve_a_equipe_e_quem_orienta(self):
        status, corpo = self.buscar("/api/equipe", cookie=self.entrar())
        self.assertEqual(status, 200)
        por_nome = {p["full_name"]: p for p in corpo["items"]}
        self.assertIn("Marina Rossetto Cardoso", por_nome)
        self.assertTrue(por_nome["Marina Rossetto Cardoso"]["orienta"])
        self.assertFalse(por_nome["Tiago Meireles Farias"]["orienta"])
        # colaborador externo nao entra: a lista e de quem esta no laboratorio
        self.assertNotIn("Parceiro de Fora", por_nome)

    def test_a_lista_nao_carrega_dado_pessoal(self):
        _, corpo = self.buscar("/api/equipe", cookie=self.entrar())
        for pessoa in corpo["items"]:
            self.assertEqual(set(pessoa),
                             {"id", "full_name", "short_name", "role", "role_label", "orienta"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
