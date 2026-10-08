#!/usr/bin/env python3
"""Testes da aba privada de Ginástica Rítmica.

    python3 -m unittest tests.test_ginastica_ritmica -v

Pedido do Mateus: "crie uma aba que sómente a Maria Helena, eu e o
Vilarino temos acesso". O que se cobra aqui é o oposto do resto do
sistema -- em vez de "todo integrante lê isto", é "ninguém lê isto a
menos que tenha sido convidado por nome", e uma revisão privada não
pode nem CONFIRMAR que existe para quem não foi convidado.
"""
from __future__ import annotations

import json
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

from lape import api, auth, ginastica_ritmica  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseGinasticaRitmica(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.mateus = self.db.member_id("Mateus Lucca")
        self.maria_helena = self.db.member_id("Maria Helena")
        self.vilarino = self.db.member_id("Guilherme Torres Vilarino")
        self.alheio = self.db.member_id("Alguem De Fora")


class TestAcesso(BaseGinasticaRitmica):
    def test_ninguem_tem_acesso_por_padrao(self):
        self.assertFalse(ginastica_ritmica.tem_acesso(self.db, self.mateus))

    def test_admin_sempre_tem_acesso_mesmo_sem_convite(self):
        self.assertTrue(ginastica_ritmica.tem_acesso(self.db, self.alheio, user_role="admin"))

    def test_conceder_da_acesso(self):
        ginastica_ritmica.conceder(self.db, self.mateus, concedido_por=self.mateus)
        self.assertTrue(ginastica_ritmica.tem_acesso(self.db, self.mateus))

    def test_conceder_duas_vezes_nao_quebra(self):
        ginastica_ritmica.conceder(self.db, self.mateus, concedido_por=self.mateus)
        ginastica_ritmica.conceder(self.db, self.mateus, concedido_por=self.mateus)
        self.assertTrue(ginastica_ritmica.tem_acesso(self.db, self.mateus))

    def test_revogar_tira_o_acesso(self):
        ginastica_ritmica.conceder(self.db, self.maria_helena, concedido_por=self.mateus)
        ginastica_ritmica.revogar(self.db, self.maria_helena)
        self.assertFalse(ginastica_ritmica.tem_acesso(self.db, self.maria_helena))

    def test_quem_tem_acesso_lista_os_convidados(self):
        ginastica_ritmica.conceder(self.db, self.mateus, concedido_por=self.mateus)
        ginastica_ritmica.conceder(self.db, self.vilarino, concedido_por=self.mateus)
        nomes = sorted(p["full_name"] for p in ginastica_ritmica.quem_tem_acesso(self.db))
        self.assertEqual(nomes, ["Guilherme Torres Vilarino", "Mateus Lucca"])


class TestEstudos(BaseGinasticaRitmica):
    def test_cadastra_um_estudo_novo(self):
        estudo_id = ginastica_ritmica.gravar_estudo(
            self.db, criado_por=self.mateus, titulo="Ansiedade pré-competitiva na GR",
            autores="Fulana; Beltrana", ano_publicacao="2024", study_type="Estudo transversal",
            qualis="A2", fator_impacto="2,35", observacoes="triagem inicial")
        estudos = ginastica_ritmica.listar_estudos(self.db)
        self.assertEqual(len(estudos), 1)
        self.assertEqual(estudos[0]["id"], estudo_id)
        self.assertEqual(estudos[0]["titulo"], "Ansiedade pré-competitiva na GR")
        self.assertEqual(estudos[0]["ano_publicacao"], 2024)
        self.assertEqual(estudos[0]["fator_impacto"], 2.35)  # vírgula decimal também entra

    def test_titulo_e_obrigatorio_para_cadastrar(self):
        with self.assertRaises(ValueError):
            ginastica_ritmica.gravar_estudo(self.db, criado_por=self.mateus, titulo="   ")

    def test_editar_um_estudo_existente(self):
        estudo_id = ginastica_ritmica.gravar_estudo(
            self.db, criado_por=self.mateus, titulo="Rascunho")
        ginastica_ritmica.gravar_estudo(
            self.db, criado_por=self.mateus, registro_id=estudo_id,
            titulo="Título revisado", ano_publicacao="2025")
        estudos = ginastica_ritmica.listar_estudos(self.db)
        self.assertEqual(len(estudos), 1)  # editar não duplica
        self.assertEqual(estudos[0]["titulo"], "Título revisado")
        self.assertEqual(estudos[0]["ano_publicacao"], 2025)

    def test_editar_com_campo_vazio_apaga_o_que_ja_estava_la(self):
        # mesmo contrato do formulário de Artigos: todo campo viaja sempre,
        # e o que a pessoa apagou na tela apaga no banco (ver buildForm em app.html)
        estudo_id = ginastica_ritmica.gravar_estudo(
            self.db, criado_por=self.mateus, titulo="Estudo", qualis="A1")
        ginastica_ritmica.gravar_estudo(
            self.db, criado_por=self.mateus, registro_id=estudo_id, titulo="Estudo", qualis="")
        self.assertIsNone(ginastica_ritmica.listar_estudos(self.db)[0]["qualis"])

    def test_excluir_um_estudo(self):
        estudo_id = ginastica_ritmica.gravar_estudo(
            self.db, criado_por=self.mateus, titulo="Para apagar")
        self.assertTrue(ginastica_ritmica.excluir_estudo(self.db, estudo_id))
        self.assertEqual(ginastica_ritmica.listar_estudos(self.db), [])

    def test_excluir_inexistente_devolve_falso(self):
        self.assertFalse(ginastica_ritmica.excluir_estudo(self.db, 999999))

    def test_lista_vem_do_ano_mais_novo_para_o_mais_velho(self):
        ginastica_ritmica.gravar_estudo(self.db, criado_por=self.mateus,
                                        titulo="Antigo", ano_publicacao="2018")
        ginastica_ritmica.gravar_estudo(self.db, criado_por=self.mateus,
                                        titulo="Novo", ano_publicacao="2024")
        titulos = [e["titulo"] for e in ginastica_ritmica.listar_estudos(self.db)]
        self.assertEqual(titulos, ["Novo", "Antigo"])


class TestSemeaduraDaBuscaPesquisada(BaseGinasticaRitmica):
    """Pedido do Mateus: "pesquisa e cadastra uns estudos e refaça as
    buscas". `ESTUDOS_SEMEADOS` vem de busca aberta na web -- não uma
    busca sistemática reproduzível -- por isso cada um carrega o link
    real na observação, e nenhum tem Qualis/fator de impacto chutado."""

    def test_semear_cadastra_todos_os_estudos_pesquisados(self):
        saida = ginastica_ritmica.semear_estudos_iniciais(self.db, criado_por=self.mateus)
        self.assertEqual(len(saida["novos"]), len(ginastica_ritmica.ESTUDOS_SEMEADOS))
        self.assertEqual(saida["ja_existiam"], [])
        self.assertEqual(len(ginastica_ritmica.listar_estudos(self.db)),
                         len(ginastica_ritmica.ESTUDOS_SEMEADOS))

    def test_semear_de_novo_nao_duplica(self):
        # "refaça as buscas" tem de poder rodar de novo sem duplicar o que
        # já está cadastrado -- é a própria busca que pode trazer repetido
        ginastica_ritmica.semear_estudos_iniciais(self.db, criado_por=self.mateus)
        saida = ginastica_ritmica.semear_estudos_iniciais(self.db, criado_por=self.mateus)
        self.assertEqual(saida["novos"], [])
        self.assertEqual(len(saida["ja_existiam"]), len(ginastica_ritmica.ESTUDOS_SEMEADOS))
        self.assertEqual(len(ginastica_ritmica.listar_estudos(self.db)),
                         len(ginastica_ritmica.ESTUDOS_SEMEADOS))

    def test_todo_estudo_semeado_tem_titulo_autores_ano_e_link_na_observacao(self):
        for estudo in ginastica_ritmica.ESTUDOS_SEMEADOS:
            with self.subTest(titulo=estudo["titulo"]):
                self.assertTrue(estudo.get("titulo"))
                self.assertTrue(estudo.get("autores"))
                self.assertTrue(estudo.get("ano_publicacao"))
                self.assertIn("http", estudo.get("observacoes") or "",
                              "sem link/DOI verificável na observação")

    def test_nenhum_estudo_semeado_chuta_qualis_ou_fator_de_impacto(self):
        # o mesmo principio da Ana (ana.py): um numero chutado e pior que
        # nenhum. Qualis nunca foi conferido em nenhuma das tres rodadas de
        # busca, e fica sempre de fora. Fator de impacto virou confiavel na
        # terceira rodada -- veio da planilha real da propria revisao do
        # Mateus (nao de uma leitura nossa), entao pode entrar, mas so como
        # numero plausivel (nunca zero/negativo, o que indicaria campo
        # mal copiado em vez de valor real).
        for estudo in ginastica_ritmica.ESTUDOS_SEMEADOS:
            with self.subTest(titulo=estudo["titulo"]):
                self.assertNotIn("qualis", estudo)
                if "fator_impacto" in estudo:
                    self.assertGreater(estudo["fator_impacto"], 0)


class TestComandoRitmica(unittest.TestCase):
    """`lape_agent.py ritmica` -- a mesma semeadura, pela linha de comando."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.caminho = Path(self.tmp.name) / "r.sqlite"
        db = Database(self.caminho)
        db.migrate()
        db.close()

    def rodar(self, semear):
        import argparse
        import io
        from contextlib import redirect_stdout

        sys.path.insert(0, str(ROOT / "scripts"))
        import lape_agent

        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = lape_agent.cmd_ritmica(argparse.Namespace(db=self.caminho, semear=semear))
        return codigo, saida.getvalue()

    def test_lista_vazia_sugere_semear(self):
        codigo, texto = self.rodar(semear=False)
        self.assertEqual(codigo, 0)
        self.assertIn("--semear", texto)

    def test_semear_cadastra_e_listar_mostra_os_titulos(self):
        codigo, texto = self.rodar(semear=True)
        self.assertEqual(codigo, 0)
        self.assertIn(f"{len(ginastica_ritmica.ESTUDOS_SEMEADOS)} estudo(s) novo(s)", texto)
        codigo, texto = self.rodar(semear=False)
        self.assertEqual(codigo, 0)
        self.assertIn("Competitive State Anxiety", texto)

    def test_semear_de_novo_pela_linha_de_comando_nao_duplica(self):
        self.rodar(semear=True)
        codigo, texto = self.rodar(semear=True)
        self.assertEqual(codigo, 0)
        self.assertIn("0 estudo(s) novo(s)", texto)
        self.assertIn(f"{len(ginastica_ritmica.ESTUDOS_SEMEADOS)} já estavam no banco", texto)


class TestRotasDaAbaPrivada(unittest.TestCase):
    """O que a rota devolve para quem tem acesso, e o que ela NUNCA revela
    para quem não tem."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "t.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Mateus Lucca", "mateus@udesc.br", "senhaforte123",
                            role="admin")
        auth.create_account(db, "Maria Helena", "maria@udesc.br", "senhaforte123",
                            role="integrante")
        auth.create_account(db, "Alguem De Fora", "fora@udesc.br", "senhaforte123",
                            role="coordenacao")
        db.close()
        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *a, **k: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def entrar_no_sistema(self, login):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"login": login, "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return r.headers.get("Set-Cookie", "").split(";")[0]

    def chamar(self, caminho, cookie=None, metodo="GET", corpo=None):
        dados = json.dumps(corpo or {}).encode() if metodo in ("POST",) or corpo is not None else None
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}{caminho}",
                                        data=dados, method=metodo)
        if cookie:
            pedido.add_header("Cookie", cookie)
        if dados:
            pedido.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            return exc.code, {}

    def setUp(self):
        self.mateus = self.entrar_no_sistema("mateus@udesc.br")
        self.maria = self.entrar_no_sistema("maria@udesc.br")
        self.fora = self.entrar_no_sistema("fora@udesc.br")

    def test_admin_ve_a_lista_mesmo_sem_convite_explicito(self):
        status, dados = self.chamar("/api/ginastica-ritmica", self.mateus)
        self.assertEqual(status, 200)
        self.assertIsInstance(dados["items"], list)

    def test_quem_nao_foi_convidado_recebe_nao_encontrado_nao_403(self):
        # uma aba de verdade privada nao confirma nem que existe -- 404,
        # nao 403 (que diria "existe, mas voce nao pode")
        status, _ = self.chamar("/api/ginastica-ritmica", self.fora)
        self.assertEqual(status, 404)

    def test_coordenacao_sozinha_nao_basta_sem_convite(self):
        # "fora" e coordenacao, e mesmo assim nao ve -- o pedido foi
        # "SOMENTE" as tres pessoas, nao "qualquer coordenacao"
        status, _ = self.chamar("/api/ginastica-ritmica/acesso", self.fora)
        self.assertEqual(status, 404)

    def test_admin_convida_alguem_e_o_convidado_passa_a_ver(self):
        maria_id = self.chamar("/api/auth/me", self.maria)[1]["id"]
        status, resultado = self.chamar("/api/ginastica-ritmica/acesso", self.mateus,
                                        "POST", {"member_id": maria_id})
        self.assertEqual(status, 200)
        self.assertEqual(len(resultado["items"]), 1)

        status, dados = self.chamar("/api/ginastica-ritmica", self.maria)
        self.assertEqual(status, 200)

    def test_me_traz_a_flag_de_acesso(self):
        _, dados = self.chamar("/api/auth/me", self.mateus)
        self.assertTrue(dados["acesso_ginastica_ritmica"])
        _, dados = self.chamar("/api/auth/me", self.fora)
        self.assertFalse(dados["acesso_ginastica_ritmica"])

    def test_cadastra_e_le_um_estudo_pela_rota(self):
        status, gravado = self.chamar(
            "/api/ginastica-ritmica", self.mateus, "POST",
            {"titulo": "Coping em ginastas de elite", "ano_publicacao": "2023"})
        self.assertEqual(status, 200)
        self.assertEqual(gravado["written"], 1)

        _, dados = self.chamar("/api/ginastica-ritmica", self.mateus)
        self.assertEqual(len(dados["items"]), 1)
        self.assertEqual(dados["items"][0]["titulo"], "Coping em ginastas de elite")

    def test_quem_nao_tem_acesso_nao_consegue_cadastrar(self):
        status, _ = self.chamar("/api/ginastica-ritmica", self.fora, "POST",
                                {"titulo": "Não deveria entrar"})
        self.assertEqual(status, 404)

    def test_exclui_um_estudo_pela_rota(self):
        _, gravado = self.chamar("/api/ginastica-ritmica", self.mateus, "POST",
                                 {"titulo": "Vai ser apagado"})
        status, resultado = self.chamar(
            f"/api/ginastica-ritmica/{gravado['id']}", self.mateus, "DELETE")
        self.assertEqual(status, 200)
        self.assertTrue(resultado["excluido"])
        ids = [x["id"] for x in self.chamar("/api/ginastica-ritmica", self.mateus)[1]["items"]]
        self.assertNotIn(gravado["id"], ids)

    def test_excluir_grava_no_log_de_auditoria(self):
        # Mesma lacuna que existia na exclusao de ponto: apagar um estudo
        # sem deixar rastro de quem apagou e o que era.
        _, gravado = self.chamar("/api/ginastica-ritmica", self.mateus, "POST",
                                 {"titulo": "Vai ser apagado com log"})
        db = Database(self.db_path)
        antes = db.scalar(
            "SELECT COUNT(*) FROM audit_log WHERE action = 'ginastica_ritmica_estudo_excluido'")
        db.close()

        status, resultado = self.chamar(
            f"/api/ginastica-ritmica/{gravado['id']}", self.mateus, "DELETE")
        self.assertEqual(status, 200)
        self.assertTrue(resultado["excluido"])

        db = Database(self.db_path)
        depois = db.scalar(
            "SELECT COUNT(*) FROM audit_log WHERE action = 'ginastica_ritmica_estudo_excluido'")
        self.assertEqual(depois, antes + 1)
        linha = db.dicts(
            "SELECT entity_id, detail FROM audit_log"
            " WHERE action = 'ginastica_ritmica_estudo_excluido' ORDER BY id DESC LIMIT 1")[0]
        self.assertEqual(linha["entity_id"], str(gravado["id"]))
        self.assertEqual(linha["detail"], "Vai ser apagado com log")
        db.close()

    def test_revoga_o_acesso_de_quem_foi_convidado(self):
        maria_id = self.chamar("/api/auth/me", self.maria)[1]["id"]
        self.chamar("/api/ginastica-ritmica/acesso", self.mateus, "POST",
                   {"member_id": maria_id})
        status, _ = self.chamar(f"/api/ginastica-ritmica/acesso/{maria_id}",
                                self.mateus, "DELETE")
        self.assertEqual(status, 200)
        self.assertEqual(self.chamar("/api/ginastica-ritmica", self.maria)[0], 404)

    def test_sem_entrar_no_sistema_nao_acessa_nada(self):
        self.assertEqual(self.chamar("/api/ginastica-ritmica")[0], 401)


if __name__ == "__main__":
    unittest.main()
