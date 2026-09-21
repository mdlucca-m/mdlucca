#!/usr/bin/env python3
"""Testes da extração de dados e do risco de viés.

    python3 -m unittest tests.test_extracao -v

O que se persegue aqui é a extração em duplicata virar teatro. Se o
sistema deixar uma pessoa ver o que a outra escreveu antes de escrever a
sua, ou se ele aceitar "conferi e está certo" como segunda extração, o
método vira uma pessoa conferindo digitação — que não é a mesma coisa e
não vale como duplicata na hora de publicar.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, auth, extracao, prisma, revisao  # noqa: E402
from lape.db import Database  # noqa: E402

RIS = "".join(f"""TY  - JOUR
TI  - Humor e desempenho no handebol: estudo {i}
AU  - Vilarino, G.T.
AU  - Andrade, A.
AU  - Coimbra, D.
JO  - Journal of Sports Sciences
PY  - {2019 + i}
DO  - 10.1000/hb.{i}
ER  -

""" for i in (1, 2, 3))


def revisao_com_incluidos(caminho: Path) -> tuple[Database, int, int, int]:
    db = Database(caminho)
    db.migrate()
    rev = revisao.criar(db, "r", "Revisão", reviewers_needed=1)
    revisao.importar(db, rev, RIS, "scopus.ris")
    ana = db.member_id("Ana Souza")
    beto = db.member_id("Beto Lima")
    for linha in db.dicts("SELECT id FROM refs"):
        revisao.decidir(db, linha["id"], ana, "incluir")
    revisao.avancar_etapa(db, rev)
    for linha in db.dicts("SELECT id FROM refs"):
        revisao.decidir(db, linha["id"], ana, "incluir")
    revisao.fechar_texto_completo(db, rev)
    extracao.preparar(db, rev, "rob2")
    return db, rev, ana, beto


class TestPreparar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db, self.rev, self.ana, self.beto = revisao_com_incluidos(
            Path(self.tmp.name) / "t.sqlite")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_o_formulario_nasce_com_os_campos_de_sempre(self):
        campos = extracao.campos(self.db, self.rev)
        self.assertEqual(len(campos), len(extracao.FORMULARIO_PADRAO))
        self.assertEqual({c["grupo"] for c in campos},
                         {"Identificação", "Participantes", "Intervenção",
                          "Desfechos", "Resultados"})

    def test_os_dominios_vem_do_instrumento_mais_o_geral(self):
        dominios = extracao.dominios(self.db, self.rev)
        self.assertEqual(len(dominios), len(extracao.FERRAMENTAS_ROB["rob2"]["dominios"]) + 1)
        self.assertEqual(dominios[-1]["code"], "geral")

    def test_preparar_de_novo_nao_apaga_o_que_ja_foi_mexido(self):
        self.db.execute("UPDATE extraction_fields SET label = ? WHERE code = ?",
                        ("País do estudo", "pais"))
        self.db.conn.commit()
        extracao.preparar(self.db, self.rev, "rob2")
        rotulo = self.db.scalar(
            "SELECT label FROM extraction_fields WHERE review_id = ? AND code = 'pais'",
            (self.rev,))
        self.assertEqual(rotulo, "País do estudo")

    def test_instrumento_inventado_e_recusado(self):
        with self.assertRaises(ValueError):
            extracao.preparar(self.db, self.rev, "meu_instrumento")

    def test_cada_instrumento_traz_o_seu_vocabulario(self):
        for codigo, ferramenta in extracao.FERRAMENTAS_ROB.items():
            with self.subTest(instrumento=codigo):
                self.assertTrue(ferramenta["dominios"])
                self.assertTrue(ferramenta["julgamentos"])
                tons = {t for _, _, t in ferramenta["julgamentos"]}
                self.assertTrue(tons <= set(prisma.TONS),
                                f"{codigo}: tom sem cor definida")


class TestGravarEComparar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db, self.rev, self.ana, self.beto = revisao_com_incluidos(
            Path(self.tmp.name) / "t.sqlite")
        self.ref = self.db.scalar("SELECT id FROM refs ORDER BY id LIMIT 1")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def duas_extracoes(self):
        extracao.gravar(self.db, self.ref, self.ana,
                        {"pais": "Brasil", "n_total": "64", "intervencao": "Mindfulness"},
                        {"d1": "baixo", "geral": "duvidas"})
        extracao.gravar(self.db, self.ref, self.beto,
                        {"pais": "Brasil", "n_total": "62", "intervencao": "Mindfulness"},
                        {"d1": "baixo", "geral": "alto"})

    def test_cada_pessoa_tem_a_sua(self):
        self.duas_extracoes()
        self.assertEqual(extracao.minha_extracao(self.db, self.ref, self.ana)
                         ["valores"]["n_total"], "64")
        self.assertEqual(extracao.minha_extracao(self.db, self.ref, self.beto)
                         ["valores"]["n_total"], "62")

    def test_campo_que_nao_existe_e_ignorado_sem_derrubar(self):
        # o formulário pode ganhar campo novo enquanto alguém está com a
        # tela aberta; o contrário também acontece
        resultado = extracao.gravar(self.db, self.ref, self.ana,
                                    {"pais": "Brasil", "campo_inventado": "x"})
        self.assertEqual(resultado["campos"], 1)

    def test_julgamento_fora_do_instrumento_e_recusado(self):
        with self.assertRaises(ValueError):
            extracao.gravar(self.db, self.ref, self.ana, {}, {"d1": "mais_ou_menos"})

    def test_so_se_compara_depois_de_duas(self):
        extracao.gravar(self.db, self.ref, self.ana, {"pais": "Brasil"})
        self.assertFalse(extracao.divergencias(self.db, self.ref)["pronto"])
        self.duas_extracoes()
        self.assertTrue(extracao.divergencias(self.db, self.ref)["pronto"])

    def test_a_divergencia_aponta_o_campo_certo(self):
        self.duas_extracoes()
        d = extracao.divergencias(self.db, self.ref)
        self.assertEqual([c["code"] for c in d["divergencias"]], ["n_total"])
        self.assertIn("pais", [c["code"] for c in d["acordo"]])
        self.assertEqual([x["code"] for x in d["risco_divergente"]], ["geral"])

    def test_conciliar_marca_a_divergencia_como_resolvida(self):
        self.duas_extracoes()
        extracao.acordar(self.db, self.ref, self.ana, {"n_total": "64"},
                         {"geral": "duvidas"})
        d = extracao.divergencias(self.db, self.ref)
        self.assertTrue(all(c["resolvida"] for c in d["divergencias"]))
        self.assertTrue(all(x["resolvida"] for x in d["risco_divergente"]))

    def test_conciliar_com_julgamento_invalido_e_recusado(self):
        self.duas_extracoes()
        with self.assertRaises(ValueError):
            extracao.acordar(self.db, self.ref, self.ana, {}, {"geral": "talvez"})


class TestConsenso(unittest.TestCase):
    """Quando as duas escrevem a mesma coisa, isso já é o consenso.

    Exigir um clique para confirmar o que ninguém contesta é trabalho
    inútil — e trabalho inútil é pulado, deixando a tabela do artigo vazia
    justamente nos campos em que a equipe concordou.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db, self.rev, self.ana, self.beto = revisao_com_incluidos(
            Path(self.tmp.name) / "t.sqlite")
        self.ref = self.db.scalar("SELECT id FROM refs ORDER BY id LIMIT 1")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_uma_pessoa_so_e_provisorio(self):
        extracao.gravar(self.db, self.ref, self.ana, {"pais": "Brasil"})
        self.assertEqual(extracao.consenso(self.db, self.ref)["pais"],
                         {"valor": "Brasil", "origem": "provisorio"})

    def test_duas_iguais_viram_unanime(self):
        extracao.gravar(self.db, self.ref, self.ana, {"pais": "Brasil"})
        extracao.gravar(self.db, self.ref, self.beto, {"pais": "Brasil"})
        self.assertEqual(extracao.consenso(self.db, self.ref)["pais"]["origem"], "unanime")

    def test_duas_diferentes_ficam_provisorias(self):
        extracao.gravar(self.db, self.ref, self.ana, {"n_total": "64"})
        extracao.gravar(self.db, self.ref, self.beto, {"n_total": "62"})
        self.assertEqual(extracao.consenso(self.db, self.ref)["n_total"]["origem"],
                         "provisorio")

    def test_o_acordo_manda_sobre_tudo(self):
        extracao.gravar(self.db, self.ref, self.ana, {"n_total": "64"})
        extracao.gravar(self.db, self.ref, self.beto, {"n_total": "62"})
        extracao.acordar(self.db, self.ref, self.ana, {"n_total": "63"})
        celula = extracao.consenso(self.db, self.ref)["n_total"]
        self.assertEqual((celula["valor"], celula["origem"]), ("63", "acordado"))

    def test_campo_nunca_preenchido_fica_vazio(self):
        self.assertEqual(extracao.consenso(self.db, self.ref)["idade"]["origem"], "vazio")

    def test_o_mesmo_vale_para_o_risco_de_vies(self):
        extracao.gravar(self.db, self.ref, self.ana, {}, {"d1": "baixo"})
        extracao.gravar(self.db, self.ref, self.beto, {}, {"d1": "baixo"})
        self.assertEqual(extracao.consenso_risco(self.db, self.ref)["d1"]["origem"],
                         "unanime")


class TestSaidas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db, self.rev, self.ana, self.beto = revisao_com_incluidos(
            Path(self.tmp.name) / "t.sqlite")
        refs = [r["id"] for r in self.db.dicts("SELECT id FROM refs ORDER BY id")]
        extracao.gravar(self.db, refs[0], self.ana,
                        {"pais": "Brasil", "n_total": "64"},
                        {"d1": "baixo", "d2": "alto", "geral": "duvidas"})
        extracao.gravar(self.db, refs[0], self.beto,
                        {"pais": "Brasil", "n_total": "64"},
                        {"d1": "baixo", "d2": "alto", "geral": "duvidas"})
        extracao.gravar(self.db, refs[1], self.ana, {"pais": "Portugal"})

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_a_tabela_tem_uma_linha_por_estudo_incluido(self):
        t = extracao.tabela(self.db, self.rev)
        self.assertEqual(len(t["estudos"]), 3)
        self.assertEqual(len(t["campos"]), len(extracao.FORMULARIO_PADRAO))

    def test_o_estudo_aparece_como_se_cita(self):
        t = extracao.tabela(self.db, self.rev)
        self.assertTrue(all("et al., " in e["estudo"] for e in t["estudos"]))

    def test_a_tabela_distingue_acordado_de_provisorio(self):
        t = extracao.tabela(self.db, self.rev)
        por_estudo = {e["estudo"]: e["celulas"] for e in t["estudos"]}
        origens = {c["pais"]["origem"] for c in por_estudo.values() if c["pais"]["valor"]}
        self.assertEqual(origens, {"unanime", "provisorio"})

    def test_o_semaforo_tem_uma_linha_por_estudo(self):
        s = extracao.semaforo(self.db, self.rev)
        self.assertEqual(len(s["estudos"]), 3)
        self.assertEqual(len(s["estudos"][0]["celulas"]), len(s["dominios"]))

    def test_a_legenda_cobre_todo_simbolo_que_aparece(self):
        # círculo cinza aparece onde ninguém julgou; sem legenda, é um
        # símbolo sem significado no papel de quem lê
        s = extracao.semaforo(self.db, self.rev)
        tons_na_grade = {c["tom"] for linha in s["estudos"] for c in linha["celulas"]}
        tons_na_legenda = {j["tom"] for j in s["julgamentos"]}
        self.assertTrue(tons_na_grade <= tons_na_legenda,
                        f"sem legenda: {tons_na_grade - tons_na_legenda}")

    def test_o_progresso_conta_o_que_falta(self):
        p = extracao.progresso(self.db, self.rev)
        self.assertEqual(p["incluidos"], 3)
        self.assertEqual(p["com_duas_extracoes"], 1)
        self.assertEqual({q["quem"] for q in p["por_pessoa"]}, {"Ana Souza", "Beto Lima"})


class TestSemaforoDesenhado(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db, self.rev, self.ana, self.beto = revisao_com_incluidos(
            Path(self.tmp.name) / "t.sqlite")
        ref = self.db.scalar("SELECT id FROM refs ORDER BY id LIMIT 1")
        extracao.gravar(self.db, ref, self.ana,
                        {}, {"d1": "baixo", "d2": "alto", "geral": "duvidas"})
        self.dados = extracao.semaforo(self.db, self.rev)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_e_um_svg_valido(self):
        ET.fromstring(prisma.semaforo(self.dados, "Risco de viés"))

    def test_a_cor_nunca_e_a_unica_informacao(self):
        # metade das revistas ainda imprime em preto e branco, e há quem
        # não distinga verde de vermelho: cada julgamento leva o símbolo
        svg = prisma.semaforo(self.dados, "Risco de viés")
        for simbolo in ("+", "?", "−"):
            self.assertIn(f">{simbolo}<", svg)

    def test_o_julgamento_vai_no_title_para_quem_usa_leitor(self):
        svg = prisma.semaforo(self.dados, "Risco de viés")
        self.assertIn("<title>Baixo risco</title>", svg)
        self.assertIn("<title>Sem julgamento</title>", svg)

    def test_revisao_sem_estudo_incluido_explica_em_vez_de_quebrar(self):
        vazio = {"dominios": [{"code": "d1", "label": "X"}], "estudos": [],
                 "julgamentos": [], "ferramenta": "RoB 2"}
        svg = prisma.semaforo(vazio, "Nada ainda")
        ET.fromstring(svg)
        self.assertIn("Nenhum estudo incluído", svg)

    def test_a_legenda_cabe_no_desenho(self):
        # com um número fixo de colunas, o último item saía para fora
        svg = prisma.semaforo(self.dados, "Risco de viés")
        raiz = ET.fromstring(svg)
        largura = float(raiz.get("width"))
        for texto in raiz.iter("{http://www.w3.org/2000/svg}text"):
            self.assertLess(float(texto.get("x", 0)), largura,
                            "há texto fora da área do desenho")


class TestExtracaoPelaApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "t.sqlite"
        db, cls.rev, _, _ = revisao_com_incluidos(cls.db_path)
        auth.create_account(db, "Ana Souza", "ana@udesc.br", "senhaforte123",
                            role="coordenacao")
        auth.create_account(db, "Beto Lima", "beto@udesc.br", "senhaforte123",
                            role="integrante")
        auth.create_account(db, "Curioso Silva", "curioso@udesc.br", "senhaforte123",
                            role="leitura")
        cls.code = db.scalar("SELECT code FROM reviews WHERE id = ?", (cls.rev,))
        db.close()
        cls.publico = api.PUBLIC_DASHBOARD
        api.PUBLIC_DASHBOARD = False
        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *a, **k: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        api.PUBLIC_DASHBOARD = cls.publico
        cls.tmp.cleanup()

    def entrar(self, login):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"login": login, "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return resposta.headers.get("Set-Cookie", "").split(";")[0]

    def chamar(self, caminho, cookie=None, corpo=None):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{caminho}",
            data=json.dumps(corpo).encode() if corpo is not None else None,
            headers={"Content-Type": "application/json",
                     **({"Cookie": cookie} if cookie else {})},
            method="POST" if corpo is not None else "GET")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as resposta:
                bruto = resposta.read()
                tipo = resposta.headers.get("Content-Type", "")
                return resposta.status, (json.loads(bruto or b"{}") if "json" in tipo
                                         else bruto.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, json.loads(exc.read() or b"{}")
            except ValueError:
                return exc.code, {}

    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")
        self.beto = self.entrar("beto@udesc.br")
        self.curioso = self.entrar("curioso@udesc.br")
        self.ref = self.chamar(f"/api/revisoes/{self.code}/formulario",
                               self.ana)[1]["incluidos"][0]["id"]

    def test_o_formulario_vem_com_o_instrumento(self):
        status, r = self.chamar(f"/api/revisoes/{self.code}/formulario", self.beto)
        self.assertEqual(status, 200)
        self.assertTrue(r["campos"])
        self.assertIn("RoB 2", r["ferramenta"]["nome"])

    def test_integrante_extrai(self):
        status, r = self.chamar(f"/api/revisoes/{self.code}/extracao", self.beto,
                                {"ref_id": self.ref, "valores": {"pais": "Brasil"}})
        self.assertEqual(status, 200)
        self.assertEqual(r["campos"], 1)

    def test_integrante_nao_concilia(self):
        # conciliar é decidir o que vai para o artigo
        status, _ = self.chamar(f"/api/revisoes/{self.code}/extracao", self.beto,
                                {"ref_id": self.ref, "acordar": True,
                                 "valores": {"pais": "Brasil"}})
        self.assertEqual(status, 403)

    def test_integrante_nao_troca_o_instrumento(self):
        status, _ = self.chamar(f"/api/revisoes/{self.code}/formulario", self.beto,
                                {"ferramenta": "robins"})
        self.assertEqual(status, 403)

    def test_quem_so_le_nao_extrai(self):
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}/formulario",
                                     self.curioso)[0], 403)

    def test_quem_so_le_ve_a_tabela(self):
        # o resultado da revisão é do laboratório inteiro
        status, r = self.chamar(f"/api/revisoes/{self.code}/caracteristicas", self.curioso)
        self.assertEqual(status, 200)
        self.assertIn("tabela", r)

    def test_julgamento_invalido_explica(self):
        status, r = self.chamar(f"/api/revisoes/{self.code}/extracao", self.ana,
                                {"ref_id": self.ref, "risco": {"d1": "mais_ou_menos"}})
        self.assertEqual(status, 400)
        self.assertIn("julgamento", r["error"])

    def test_sem_estudo_explica(self):
        status, r = self.chamar(f"/api/revisoes/{self.code}/extracao", self.ana,
                                {"valores": {"pais": "Brasil"}})
        self.assertEqual(status, 400)
        self.assertIn("estudo", r["error"])

    def test_o_semaforo_baixa_desenhado(self):
        status, corpo = self.chamar(f"/api/revisoes/{self.code}/semaforo.svg", self.ana)
        self.assertEqual(status, 200)
        ET.fromstring(corpo)

    def test_a_tabela_baixa_em_planilha(self):
        status, corpo = self.chamar(f"/api/revisoes/{self.code}/caracteristicas.csv",
                                    self.ana)
        self.assertEqual(status, 200)
        self.assertTrue(corpo.startswith("﻿"))
        self.assertIn("Estudo;", corpo)


class TestOsFormulariosDeclarados(unittest.TestCase):
    """A ficha fica ESCRITA, e nao montada a cada revisao.

    Pela mesma razao das estrategias de busca: uma ficha montada na hora
    sai diferente de uma revisao para a outra, e o campo que falta so
    aparece quando alguem tenta preenche-lo -- com metade dos estudos ja
    extraidos, e a unica saida sendo reler todos.
    """

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "r.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.rev = revisao.criar(self.db, "r", "Revisão")

    def test_o_completo_traz_o_que_o_prisma_pede_e_o_padrao_nao_tinha(self):
        """Nao e lista de desejos: cada um destes e pedido por norma.

        Financiamento e conflito de interesse sao exigencia de revista e
        nao se acham depois; o resultado NAO significativo e o item 10 do
        PRISMA 2020 -- sem campo proprio, a extracao copia o resumo, e o
        resumo conta o que deu certo.
        """
        codigos = {c["code"] for c in extracao.FORMULARIO_COMPLETO}
        for exigido in ("financiamento", "conflito", "etica", "registro",
                        "idioma", "pais", "nao_significativos", "tamanho_efeito",
                        "fidedignidade", "perdas", "n_analisado", "limitacoes",
                        "relatos_irmaos", "texto_completo"):
            with self.subTest(campo=exigido):
                self.assertIn(exigido, codigos)

    def test_a_ficha_da_autodeterminacao_contem_a_completa(self):
        """O recorte acrescenta; nao substitui.

        Uma ficha tematica que trocasse a generica perderia financiamento
        e tamanho de efeito para ganhar as regulacoes -- e a revisao
        deixaria de responder ao PRISMA para responder a teoria.
        """
        completo = [c["code"] for c in extracao.FORMULARIO_COMPLETO]
        tematico = [c["code"] for c in extracao.FORMULARIO_AUTODETERMINACAO]
        self.assertEqual(tematico[:len(completo)], completo)
        for proprio in ("construtos_tad", "papel_tad", "instrumento_tad",
                        "alfa_tad", "correlacoes_tad", "amostra_handebol",
                        "proporcao_handebol", "nivel", "quem_respondeu"):
            with self.subTest(campo=proprio):
                self.assertIn(proprio, tematico)

    def test_a_descricao_nao_promete_um_numero_de_campos_que_mudou(self):
        """A tela mostra a descricao E a contagem, lado a lado.

        A descricao diz "quarenta e oito campos" e a contagem vem de
        `len(campos)`: divergindo, a tela se contradiz sozinha na frente
        de quem esta escolhendo a ficha. Ja divergiu uma vez.
        """
        escrito = {
            "zero": 0, "vinte": 20, "quarenta e oito": 48, "sessenta e dois": 62,
            "cinquenta e um": 51,
        }
        for nome, forma in extracao.FORMULARIOS.items():
            texto = forma["descricao"].lower()
            ditos = [n for n, valor in escrito.items() if n in texto]
            for dito in ditos:
                with self.subTest(formulario=nome, numero=dito):
                    self.assertEqual(escrito[dito], len(forma["campos"]))

    def test_nenhum_formulario_tem_codigo_repetido(self):
        """Codigo repetido faz o segundo campo sumir no UNIQUE, calado."""
        for nome, forma in extracao.FORMULARIOS.items():
            with self.subTest(formulario=nome):
                codigos = [c["code"] for c in forma["campos"]]
                self.assertEqual(len(codigos), len(set(codigos)))

    def test_todo_campo_declarado_tem_tipo_que_a_tela_sabe_desenhar(self):
        for nome, forma in extracao.FORMULARIOS.items():
            for campo in forma["campos"]:
                with self.subTest(formulario=nome, campo=campo["code"]):
                    self.assertIn(campo.get("kind", "texto"), extracao.TIPOS)
                    self.assertTrue(campo.get("grupo"), "campo sem grupo cai em “Geral”")
                    if campo.get("kind") in ("escolha", "multipla"):
                        self.assertTrue(campo.get("options"),
                                        "escolha sem opções vira caixa vazia")

    def test_preparar_aceita_o_formulario_pelo_nome_e_guarda_qual_foi(self):
        extracao.preparar(self.db, self.rev, "mmat", formulario="autodeterminacao")
        campos = extracao.campos(self.db, self.rev)
        self.assertEqual(len(campos), len(extracao.FORMULARIO_AUTODETERMINACAO))
        self.assertEqual(extracao.formulario_de(self.db, self.rev)["codigo"],
                         "autodeterminacao")

    def test_formulario_que_nao_existe_reclama_e_nao_instala_meio(self):
        with self.assertRaises(ValueError) as erro:
            extracao.preparar(self.db, self.rev, "rob2", formulario="inventado")
        self.assertIn("inventado", str(erro.exception))
        self.assertEqual(extracao.campos(self.db, self.rev), [])

    def test_trocar_de_formulario_acrescenta_e_nao_apaga_o_que_foi_extraido(self):
        """Começar no padrão e passar para o completo nao pode custar releitura."""
        extracao.preparar(self.db, self.rev, "rob2", formulario="padrao")
        revisao.importar(self.db, self.rev, RIS, "scopus.ris")
        ref = self.db.scalar("SELECT id FROM refs LIMIT 1")
        ana = self.db.member_id("Ana Souza")
        extracao.gravar(self.db, ref, ana, {"n_total": "40"})

        extracao.preparar(self.db, self.rev, "rob2", formulario="completo")
        self.assertEqual(extracao.minha_extracao(self.db, ref, ana)["valores"]["n_total"],
                         "40")
        codigos = {c["code"] for c in extracao.campos(self.db, self.rev)}
        self.assertIn("nao_significativos", codigos)


class TestAMMAT(unittest.TestCase):
    """A ferramenta e UMA por revisao, e ha revisao de desenhos misturados.

    A da autodeterminacao no handebol e assim: transversais, um ensaio,
    uma coorte, qualitativos e validacoes. Julgar tudo aquilo pela RoB 2
    seria cobrar randomizacao de quem nao randomizou.
    """

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "r.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.rev = revisao.criar(self.db, "r", "Revisão")

    def test_tem_a_triagem_e_os_cinco_criterios_de_cada_categoria(self):
        codigos = [c for c, _ in extracao.FERRAMENTAS_ROB["mmat"]["dominios"]]
        self.assertEqual(codigos[:2], ["s1", "s2"])
        for letra in ("q", "r", "n", "d", "m"):
            with self.subTest(categoria=letra):
                self.assertEqual([c for c in codigos if c.startswith(letra)],
                                 [f"{letra}{i}" for i in range(1, 6)])
        self.assertEqual(len(codigos), 27)

    def test_tem_nao_se_aplica_porque_cada_estudo_responde_uma_categoria(self):
        """Sem "nao se aplica", o criterio de outra categoria vira lacuna.

        E lacuna, no semaforo, e circulo cinza -- indistinguivel de "a
        equipe ainda nao julgou".
        """
        julgamentos = {j[0] for j in extracao.FERRAMENTAS_ROB["mmat"]["julgamentos"]}
        self.assertEqual(julgamentos, {"sim", "nao", "indeterminado", "na"})

    def test_a_mmat_nao_ganha_dominio_geral(self):
        """A propria MMAT desaconselha o escore unico, por escrito.

        Um numero esconde QUAL criterio falhou -- e e o criterio que muda
        a leitura do estudo, nao a media dele.
        """
        extracao.preparar(self.db, self.rev, "mmat")
        codigos = [d["code"] for d in extracao.dominios(self.db, self.rev)]
        self.assertNotIn("geral", codigos)
        self.assertEqual(len(codigos), 27)

    def test_as_outras_ferramentas_continuam_com_o_geral(self):
        extracao.preparar(self.db, self.rev, "rob2")
        self.assertIn("geral", [d["code"] for d in extracao.dominios(self.db, self.rev)])

    def test_o_instrumento_escolhido_sobrevive_a_um_protocolo_em_texto(self):
        """`study_designs` e campo do protocolo, e foi usado como gaveta.

        Uma revisao que escrevesse ali "transversais e ensaios" -- que e o
        uso certo do campo -- voltava calada para a RoB 2, e passava a
        cobrar randomizacao de estudo transversal.
        """
        rev = revisao.criar(self.db, "r2", "Revisão",
                            study_designs="Transversais, ensaios e qualitativos")
        extracao.preparar(self.db, rev, "mmat", formulario="completo")
        self.assertEqual(extracao.ferramenta_da(self.db, rev)["codigo"], "mmat")
        self.assertEqual(
            self.db.scalar("SELECT study_designs FROM reviews WHERE id = ?", (rev,)),
            "Transversais, ensaios e qualitativos",
            "o protocolo nao pode ser sobrescrito pelo nome do instrumento")

    def test_revisao_antiga_continua_lendo_o_instrumento_do_campo_velho(self):
        """Antes da coluna propria, o instrumento morava em `study_designs`."""
        rev = revisao.criar(self.db, "r3", "Revisão")
        self.db.execute("UPDATE reviews SET study_designs = 'robins',"
                        "       rob_tool = NULL WHERE id = ?", (rev,))
        self.assertEqual(extracao.ferramenta_da(self.db, rev)["codigo"], "robins")

    def test_o_semaforo_desenha_com_a_mmat(self):
        extracao.preparar(self.db, self.rev, "mmat", formulario="autodeterminacao")
        grade = extracao.semaforo(self.db, self.rev)
        self.assertEqual(len(grade["dominios"]), 27)
        self.assertIn("MMAT", grade["ferramenta"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
