#!/usr/bin/env python3
"""O padrão que cada tipo de revisão cobra, e o que o sistema já conferiu.

    python3 -m unittest tests.test_padrao -v

Sistemática, revisão de escopo e mapping review não são a mesma coisa com
nomes diferentes: seguem padrões de relato diferentes e cobram coisas
diferentes. O modo de errar aqui é tratar as três como uma só -- pedindo
risco de viés a uma revisão de escopo, que não o faz por definição, ou
deixando uma sistemática chegar ao fim sem ninguém ter cobrado a avaliação
de qualidade, que nela é obrigatória.

O segundo modo de errar é a conferência mentir. Uma checklist que marca
tudo como pendente é um PDF; uma que marca tudo como feito é pior que
nenhuma, porque quem lê acredita. O que se cobra aqui é que "feito" tenha
sido CONFERIDO no banco, que "falta" também, e que o que só uma pessoa
pode dizer saia marcado como tal em vez de virar meio-feito.

Os modelos de extração seguem a mesma regra: extrair um estudo transversal
com campos de ensaio clínico produz coluna após coluna de "não se aplica",
e o erro só aparece na tabela de características, com metade dos estudos
já extraída.
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

from lape import api, auth, extracao, padrao, revisao  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"

RIS = "".join(f"""TY  - JOUR
TI  - Motivação e handebol: estudo {i}
AU  - Vilarino, G.T.
AU  - Andrade, A.
JO  - Journal of Sports Sciences
PY  - {2019 + i}
DO  - 10.1000/hb.{i}
ER  -

""" for i in (1, 2, 3))


def como_esta(conferencia, code):
    return next(i for i in conferencia["itens"] if i["code"] == code)


class BaseComRevisao(unittest.TestCase):
    """Uma revisão recém-aberta: nada foi feito ainda, e a conferência sabe."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)

    def abrir(self, tipo=None, **campos):
        return revisao.criar(self.db, campos.pop("code", "r"), "Revisão",
                             tipo=tipo, **campos)


class TestOTipoDaRevisao(BaseComRevisao):

    def test_tipo_desconhecido_cai_no_padrao_em_vez_de_estourar(self):
        """Um banco de antes deste campo tem revisões sem tipo.

        Uma revisão aberta antes de o campo existir não pode deixar de
        abrir por causa dele -- e "sistemática" digitada com acento pela
        tela de outra pessoa também não.
        """
        for entrada in (None, "", "sistemática", "guarda-chuva"):
            with self.subTest(entrada=entrada):
                self.assertEqual(padrao.tipo(entrada)["code"], padrao.PADRAO)

    def test_cada_tipo_se_devolve(self):
        for t in padrao.TIPOS:
            with self.subTest(tipo=t["code"]):
                self.assertIs(padrao.tipo(t["code"]), t)

    def test_os_tipos_que_os_itens_citam_existem(self):
        """Um code com erro de digitação some do sistema para sempre.

        O item não daria erro: ele simplesmente nunca casaria com tipo
        nenhum, e sairia como "não se aplica" em todas as revisões.
        """
        codes = {t["code"] for t in padrao.TIPOS}
        for item in padrao.ITENS:
            with self.subTest(item=item["code"]):
                self.assertTrue(set(item["tipos"]) <= codes,
                                f"{item['code']} cita tipo que não existe")
                self.assertTrue(item["tipos"], "item que não vale para ninguém")

    def test_cada_tipo_leva_ao_instrumento_oficial(self):
        for t in padrao.TIPOS:
            with self.subTest(tipo=t["code"]):
                self.assertTrue(t["url"].startswith("https://"))
                self.assertTrue(t["padrao"] and t["rotulo"] and t["resumo"])

    def test_cada_item_diz_por_que(self):
        """Sem o porquê, a checklist vira uma lista de tarefas sem dono."""
        codes = [i["code"] for i in padrao.ITENS]
        self.assertEqual(len(codes), len(set(codes)), "item repetido")
        for item in padrao.ITENS:
            with self.subTest(item=item["code"]):
                self.assertTrue(item["porque"].strip())
                self.assertTrue(item["rotulo"].strip())

    def test_a_revisao_guarda_o_tipo_escolhido(self):
        rev = self.abrir("escopo")
        self.assertEqual(
            self.db.scalar("SELECT tipo FROM reviews WHERE id = ?", (rev,)),
            "escopo")

    def test_tipo_estranho_nao_impede_de_criar(self):
        rev = self.abrir("qualquer coisa")
        self.assertEqual(
            self.db.scalar("SELECT tipo FROM reviews WHERE id = ?", (rev,)),
            padrao.PADRAO)


class TestOQueCadaTipoCobra(BaseComRevisao):
    """O que muda entre os três -- que é a razão de o campo existir."""

    def test_a_sistematica_cobra_risco_de_vies(self):
        d = padrao.conferir(self.db, self.abrir("sistematica"))
        self.assertEqual(como_esta(d, "rob")["situacao"], padrao.FALTA)

    def test_a_revisao_de_escopo_nao_cobra_risco_de_vies(self):
        """Ela não o faz por definição: descreve o campo, não decide.

        Cobrá-lo seria mandar a pessoa fazer trabalho que o padrão dela
        não pede -- e, pior, sugerir que a revisão está incompleta.
        """
        d = padrao.conferir(self.db, self.abrir("escopo"))
        item = como_esta(d, "rob")
        self.assertEqual(item["situacao"], padrao.NAO_SE_APLICA)
        self.assertIn("opcional", item["detalhe"])

    def test_a_mapping_tambem_nao_cobra_extracao_em_duplicata(self):
        """Ela fica no título e resumo: não há o que extrair em duplicata."""
        d = padrao.conferir(self.db, self.abrir("mapping"))
        self.assertEqual(como_esta(d, "rob")["situacao"], padrao.NAO_SE_APLICA)
        self.assertEqual(como_esta(d, "extracao")["situacao"], padrao.NAO_SE_APLICA)

    def test_o_que_vale_para_as_tres_aparece_nas_tres(self):
        comuns = ("protocolo", "pergunta", "fontes", "estrategia", "data")
        for t in padrao.TIPOS:
            d = padrao.conferir(self.db, self.abrir(t["code"], code=t["code"]))
            for code in comuns:
                with self.subTest(tipo=t["code"], item=code):
                    self.assertNotEqual(como_esta(d, code)["situacao"],
                                        padrao.NAO_SE_APLICA)

    def test_a_conta_fecha_com_o_numero_de_itens(self):
        """Um item sem situação sumiria da conta sem ninguém notar."""
        for t in padrao.TIPOS:
            d = padrao.conferir(self.db, self.abrir(t["code"], code=t["code"]))
            with self.subTest(tipo=t["code"]):
                self.assertEqual(sum(d["conta"].values()), len(padrao.ITENS))
                self.assertEqual(len(d["itens"]), len(padrao.ITENS))

    def test_o_aviso_leva_a_checklist_DESTE_tipo(self):
        """Mandar quem faz revisão de escopo conferir o PRISMA 2020 é
        mandá-la ao instrumento errado -- e ela vai conferir."""
        d = padrao.conferir(self.db, self.abrir("escopo"))
        self.assertIn(padrao.tipo("escopo")["url"], d["aviso"])
        self.assertNotIn(padrao.tipo("sistematica")["url"], d["aviso"])

    def test_revisao_que_nao_existe_e_erro_e_nao_conferencia_vazia(self):
        with self.assertRaises(ValueError):
            padrao.conferir(self.db, 9999)


class TestOQueOSistemaConfereSozinho(BaseComRevisao):
    """"Feito" tem de ter sido conferido no banco. Senão é decoração."""

    def test_o_protocolo_so_fica_feito_com_o_link_gravado(self):
        rev = self.abrir()
        self.assertEqual(
            como_esta(padrao.conferir(self.db, rev), "protocolo")["situacao"],
            padrao.FALTA)
        self.db.execute("UPDATE reviews SET protocol_url = ? WHERE id = ?",
                        ("https://osf.io/abcde", rev))
        self.db.conn.commit()
        item = como_esta(padrao.conferir(self.db, rev), "protocolo")
        self.assertEqual(item["situacao"], padrao.FEITO)
        self.assertIn("osf.io", item["detalhe"])

    def test_meia_pergunta_nao_e_pergunta(self):
        """Três dos quatro campos é o mínimo; um título não é pergunta."""
        rev = self.abrir(question="Qual o efeito?")
        self.assertEqual(
            como_esta(padrao.conferir(self.db, rev), "pergunta")["situacao"],
            padrao.FALTA)
        self.db.execute(
            "UPDATE reviews SET population = ?, outcome = ? WHERE id = ?",
            ("atletas de handebol", "motivação", rev))
        self.db.conn.commit()
        self.assertEqual(
            como_esta(padrao.conferir(self.db, rev), "pergunta")["situacao"],
            padrao.FEITO)

    def test_um_avaliador_so_e_falta_e_nao_feito(self):
        """Uma pessoa sozinha erra, e erra sempre para o mesmo lado.

        O sistema aceita rodar assim -- há revisão de escopo que roda --,
        mas não pode dizer que o padrão foi cumprido.
        """
        rev = self.abrir(reviewers_needed=1)
        item = como_esta(padrao.conferir(self.db, rev), "duplicata")
        self.assertEqual(item["situacao"], padrao.FALTA)
        self.assertIn("dois", item["detalhe"])

    def test_a_estrategia_que_falta_diz_QUAL_base(self):
        """"Falta a estratégia" sem dizer onde é uma tarefa sem endereço."""
        rev = self.abrir()
        revisao.importar(self.db, rev, RIS, "scopus.ris")
        self.db.execute(
            "INSERT INTO review_searches (review_id, base, query, searched_on)"
            " VALUES (?, 'PubMed', 'handball AND motivation', '2026-09-01')",
            (rev,))
        self.db.execute(
            "INSERT INTO review_searches (review_id, base, query, searched_on)"
            " VALUES (?, 'SPORTDiscus', '', '2026-09-01')", (rev,))
        self.db.conn.commit()
        item = como_esta(padrao.conferir(self.db, rev), "estrategia")
        self.assertEqual(item["situacao"], padrao.FALTA)
        self.assertIn("SPORTDiscus", item["detalhe"])
        self.assertNotIn("PubMed", item["detalhe"])

    def test_sem_busca_nenhuma_as_fontes_faltam(self):
        rev = self.abrir()
        d = padrao.conferir(self.db, rev)
        for code in ("fontes", "estrategia", "data"):
            with self.subTest(item=code):
                self.assertEqual(como_esta(d, code)["situacao"], padrao.FALTA)

    def test_a_data_da_busca_aparece_quando_esta_la(self):
        rev = self.abrir()
        self.db.execute(
            "INSERT INTO review_searches (review_id, base, query, searched_on)"
            " VALUES (?, 'PubMed', 'handball', '2026-09-01')", (rev,))
        self.db.conn.commit()
        item = como_esta(padrao.conferir(self.db, rev), "data")
        self.assertEqual(item["situacao"], padrao.FEITO)
        self.assertIn("2026-09-01", item["detalhe"])

    def test_ninguem_excluido_ainda_e_manual_e_nao_feito(self):
        """Marcar como feito o que não aconteceu é a mentira mais fácil.

        Ninguém excluído no texto completo não é "os motivos estão todos
        lá": é que ainda não há nada para conferir.
        """
        rev = self.abrir()
        item = como_esta(padrao.conferir(self.db, rev), "motivos")
        self.assertEqual(item["situacao"], padrao.MANUAL)

    def test_o_risco_de_vies_sem_instrumento_diz_quais_existem(self):
        rev = self.abrir()
        item = como_esta(padrao.conferir(self.db, rev), "rob")
        self.assertEqual(item["situacao"], padrao.FALTA)
        for nome in ("ROB 2", "ROBINS-I", "JBI"):
            self.assertIn(nome, item["detalhe"])

    def test_o_que_so_uma_pessoa_pode_dizer_sai_como_manual(self):
        """Síntese e limitações vão no artigo, e o sistema não os vê.

        Marcá-los como "falta" encheria a tela de pendência eterna; como
        "feito", seria invenção.
        """
        d = padrao.conferir(self.db, self.abrir())
        sem_conferencia = [i["code"] for i in padrao.ITENS if i["confere"] is None]
        self.assertTrue(sem_conferencia)
        for code in sem_conferencia:
            with self.subTest(item=code):
                self.assertEqual(como_esta(d, code)["situacao"], padrao.MANUAL)

    def test_todo_item_diz_onde_o_sistema_olhou(self):
        for t in padrao.TIPOS:
            d = padrao.conferir(self.db, self.abrir(t["code"], code=t["code"]))
            for item in d["itens"]:
                with self.subTest(tipo=t["code"], item=item["code"]):
                    self.assertTrue(str(item["detalhe"]).strip(),
                                    "situação sem explicação nenhuma")


class TestOsModelosDeExtracao(unittest.TestCase):
    """Extrair transversal com campo de ensaio clínico produz vazio."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "m.sqlite")
        self.db.migrate()
        self.rev = revisao.criar(self.db, "m", "Revisão")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)

    def test_cada_modelo_se_descreve_e_diz_para_que_serve(self):
        for code, m in extracao.MODELOS.items():
            with self.subTest(modelo=code):
                self.assertTrue(m["nome"].strip())
                self.assertTrue(m["para"].strip())
                self.assertTrue(m["campos"], "modelo sem campo nenhum")

    def test_os_campos_de_cada_modelo_nao_se_repetem(self):
        """Dois campos com o mesmo code viram um só no banco: a chave é
        (revisão, code), e o segundo sobrescreveria o primeiro."""
        for code, m in extracao.MODELOS.items():
            with self.subTest(modelo=code):
                codes = [c["code"] for c in m["campos"]]
                self.assertEqual(len(codes), len(set(codes)))

    def test_todo_campo_tem_rotulo_e_grupo(self):
        """Sem grupo o formulário sai como uma coluna de 20 caixas."""
        for code, m in extracao.MODELOS.items():
            for campo in m["campos"]:
                with self.subTest(modelo=code, campo=campo["code"]):
                    self.assertTrue(campo["label"].strip())
                    self.assertTrue(str(campo.get("grupo") or "").strip())

    def test_so_ha_tipos_de_campo_que_a_tela_sabe_desenhar(self):
        """Um kind que a tela não conhece vira caixa de texto sem aviso."""
        js = (TEMPLATES / "triagem.js").read_text(encoding="utf-8")
        # `multipla` entrou quando um campo precisou de MAIS DE UMA resposta
        # de vocabulário fechado (os construtos da TAD que um estudo mede).
        # Ela só pode estar aqui porque a tela a desenha de verdade, em
        # caixas de marcar -- a asserção logo abaixo é o que garante isso.
        conhecidos = {"texto", "texto_longo", "escolha", "sim_nao", "numero",
                      "data", "multipla"}
        for kind in conhecidos - {"texto"}:
            self.assertIn(f'"{kind}"', js, f"a tela não trata {kind}")
        for code, m in extracao.MODELOS.items():
            for campo in m["campos"]:
                with self.subTest(modelo=code, campo=campo["code"]):
                    self.assertIn(campo.get("kind", "texto"), conhecidos)

    def test_campo_de_escolha_sem_opcoes_e_campo_morto(self):
        for code, m in extracao.MODELOS.items():
            for campo in m["campos"]:
                if campo.get("kind") == "escolha":
                    with self.subTest(modelo=code, campo=campo["code"]):
                        self.assertTrue(str(campo.get("options") or "").strip())

    def test_o_modelo_de_escopo_mapeia_populacao_conceito_contexto(self):
        """É o PCC do JBI: numa revisão de escopo não se extrai efeito,
        mapeia-se característica -- e sem os três não há mapa."""
        codes = {c["code"] for c in extracao.MODELO_ESCOPO}
        self.assertTrue({"populacao", "conceito", "contexto"} <= codes)
        self.assertNotIn("medida", codes)

    def test_o_observacional_cobra_confundidores_e_medida_de_associacao(self):
        """É o que o STROBE pede, e é o que falta quando se usa o
        formulário de ensaio: lá não há confundidor nenhum."""
        codes = {c["code"] for c in extracao.MODELO_OBSERVACIONAL}
        self.assertTrue({"confundidores", "medida", "exposicao"} <= codes)

    def test_preparar_instala_os_campos_do_modelo_escolhido(self):
        saida = extracao.preparar(self.db, self.rev, "rob2", modelo="observacional")
        self.assertEqual(saida["campos"], len(extracao.MODELO_OBSERVACIONAL))
        campos = extracao.campos(self.db, self.rev)
        self.assertEqual({c["code"] for c in campos},
                         {c["code"] for c in extracao.MODELO_OBSERVACIONAL})

    def test_sem_modelo_continua_vindo_o_de_sempre(self):
        """Quem já usava o sistema não pode ver o formulário mudar."""
        extracao.preparar(self.db, self.rev, "rob2")
        self.assertEqual({c["code"] for c in extracao.campos(self.db, self.rev)},
                         {c["code"] for c in extracao.FORMULARIO_PADRAO})

    def test_modelo_desconhecido_e_recusado_em_vez_de_virar_o_padrao(self):
        """Cair no padrão em silêncio faria a pessoa extrair meia revisão
        com o formulário errado antes de perceber."""
        with self.assertRaises(ValueError) as erro:
            extracao.preparar(self.db, self.rev, "rob2", modelo="transversal")
        self.assertIn("transversal", str(erro.exception))
        self.assertEqual(extracao.campos(self.db, self.rev), [])

    def test_campos_escritos_a_mao_ganham_do_modelo(self):
        meus = ({"code": "so_esse", "label": "Só esse", "grupo": "Meu"},)
        extracao.preparar(self.db, self.rev, "rob2", campos=meus,
                          modelo="qualitativo")
        self.assertEqual([c["code"] for c in extracao.campos(self.db, self.rev)],
                         ["so_esse"])

    def test_todos_os_modelos_instalam_sem_erro(self):
        for code, m in extracao.MODELOS.items():
            with self.subTest(modelo=code):
                rev = revisao.criar(self.db, f"r-{code}", f"Revisão {code}")
                saida = extracao.preparar(self.db, rev, "rob2", modelo=code)
                self.assertEqual(saida["campos"], len(m["campos"]))
                self.assertEqual(len(extracao.campos(self.db, rev)), len(m["campos"]))


class TestAConferenciaPelaRede(unittest.TestCase):
    """A conferência e os modelos pela rota, com sessão de verdade."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "l.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Alexandro Andrade", "coord@udesc.br",
                            "senhaforte123", role="coordenacao")
        auth.create_account(db, "Loiane", "loiane@udesc.br", "senhaforte123",
                            role="integrante")
        revisao.criar(db, "escopo-hb", "Mapa do handebol", tipo="escopo")
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

    def entrar(self, login):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"login": login, "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return (r.headers.get("Set-Cookie") or "").split(";")[0]

    def chamar(self, caminho, cookie=None, corpo=None):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{caminho}",
            data=json.dumps(corpo).encode() if corpo is not None else None,
            headers={"Content-Type": "application/json",
                     **({"Cookie": cookie} if cookie else {})},
            method="POST" if corpo is not None else "GET")
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"{}")

    def test_a_conferencia_sai_pela_rota_com_o_tipo_certo(self):
        status, corpo = self.chamar("/api/revisoes/escopo-hb/padrao",
                                    self.entrar("loiane@udesc.br"))
        self.assertEqual(status, 200)
        self.assertEqual(corpo["tipo"]["code"], "escopo")
        self.assertEqual(len(corpo["itens"]), len(padrao.ITENS))
        self.assertIn("conta", corpo)

    def test_sem_entrar_ninguem_confere(self):
        status, _ = self.chamar("/api/revisoes/escopo-hb/padrao")
        self.assertEqual(status, 401)

    def test_revisao_que_nao_existe_e_404(self):
        status, _ = self.chamar("/api/revisoes/nao-existe/padrao",
                                self.entrar("loiane@udesc.br"))
        self.assertEqual(status, 404)

    def test_a_tela_recebe_todos_os_modelos_com_quantos_campos_tem(self):
        status, corpo = self.chamar("/api/extracao/modelos",
                                    self.entrar("loiane@udesc.br"))
        self.assertEqual(status, 200)
        self.assertEqual({m["code"] for m in corpo["modelos"]},
                         set(extracao.MODELOS))
        for m in corpo["modelos"]:
            with self.subTest(modelo=m["code"]):
                self.assertEqual(m["campos"],
                                 len(extracao.MODELOS[m["code"]]["campos"]))
                self.assertTrue(m["grupos"])

    def test_criar_pela_tela_guarda_o_tipo_escolhido(self):
        cookie = self.entrar("coord@udesc.br")
        status, corpo = self.chamar("/api/revisoes", cookie, {
            "titulo": "Mapa da cobertura", "tipo": "mapping"})
        self.assertEqual(status, 200)
        status, d = self.chamar(f"/api/revisoes/{corpo['code']}/padrao", cookie)
        self.assertEqual(d["tipo"]["code"], "mapping")

    def test_sem_dizer_o_tipo_a_revisao_nasce_sistematica(self):
        cookie = self.entrar("coord@udesc.br")
        _, corpo = self.chamar("/api/revisoes", cookie, {"titulo": "Sem tipo"})
        _, d = self.chamar(f"/api/revisoes/{corpo['code']}/padrao", cookie)
        self.assertEqual(d["tipo"]["code"], padrao.PADRAO)


class TestAAbaNaTela(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.js = (TEMPLATES / "triagem.js").read_text(encoding="utf-8")

    def test_a_aba_esta_na_barra_E_no_desenho(self):
        """Aba listada e não roteada abre a triagem, sem dizer por quê."""
        self.assertIn('["padrao", "Padrão"]', self.js)
        self.assertIn('ESTADO.aba === "padrao"', self.js)
        self.assertIn("function desenharPadrao", self.js)

    def test_a_tela_distingue_falta_de_confira_voce(self):
        """São coisas diferentes: uma é pendência, a outra é trabalho que
        o sistema não tem como ver."""
        trecho = self.js[self.js.index("const SITUACAO = {"):]
        trecho = trecho[:trecho.index("\n};")]
        for code in (padrao.FEITO, padrao.FALTA, padrao.MANUAL,
                     padrao.NAO_SE_APLICA):
            with self.subTest(situacao=code):
                self.assertIn(code + ":", trecho)
        self.assertIn("confira você", trecho)

    def test_o_aviso_de_que_isto_nao_e_a_checklist_oficial_aparece(self):
        trecho = self.js[self.js.index("async function desenharPadrao"):]
        trecho = trecho[:trecho.index("function desenharImportar")]
        self.assertIn("d.aviso", trecho)
        self.assertIn("d.tipo.url", trecho)
        self.assertIn("item.porque", trecho)

    def test_os_tipos_oferecidos_sao_os_que_o_sistema_conhece(self):
        """Um value com erro de digitação criaria tudo como sistemática,
        em silêncio: o servidor cai no padrão de propósito."""
        trecho = self.js[self.js.index("const tipo = el(\"select\""):]
        trecho = trecho[:trecho.index("const quantos")]
        for t in padrao.TIPOS:
            with self.subTest(tipo=t["code"]):
                self.assertIn(f'value: "{t["code"]}"', trecho)
                self.assertIn(f"{t['code']}:", trecho)

    def test_a_tela_manda_o_tipo_ao_criar(self):
        trecho = self.js[self.js.index("async function desenharEscolha"):]
        self.assertIn("tipo: tipo.value", trecho)


if __name__ == "__main__":
    unittest.main()


class TestOsSegmentosDeclarados(unittest.TestCase):
    """Segmento repetido some no banco, e some calado.

    A busca e guardada por (biblioteca, base, segmento). Declarar o mesmo
    nome duas vezes nao cria duas buscas: a segunda sobrescreve a
    primeira, e o acervo fica com um segmento a menos do que a lista diz
    ter -- sem erro nenhum, e sem nada na tela que explique a diferenca.

    Este teste existe porque aconteceu: ao juntar duas linhas de trabalho
    que mexeram nos mesmos segmentos, dois nomes ficaram duplicados no
    acervo de motivacao e um no da autodeterminacao. Todos os quatro
    conflitos tinham sido resolvidos, o arquivo importava, a suite passava
    -- e a lista estava errada.
    """

    def test_nenhum_acervo_declara_o_mesmo_segmento_duas_vezes(self):
        from collections import Counter

        from lape import biblioteca

        for decl in biblioteca.BIBLIOTECAS:
            nomes = [nome for nome, _ in decl["segmentos"]]
            repetidos = [n for n, quantos in Counter(nomes).items() if quantos > 1]
            with self.subTest(acervo=decl["code"]):
                self.assertEqual(repetidos, [],
                                 "segmento repetido vira um só no banco")

    def test_nenhum_segmento_esta_sem_termo(self):
        """Segmento sem termo gera `(...) AND ()`, que a base recusa."""
        from lape import biblioteca

        for decl in biblioteca.BIBLIOTECAS:
            for nome, termos in decl["segmentos"]:
                with self.subTest(acervo=decl["code"], segmento=nome):
                    self.assertTrue([x for x in termos if x and x.strip()])
