"""Alfa de Cronbach, e o que faltava para ele existir.

`coletas` guarda UM escore por instrumento. Consistencia interna e a
relacao ENTRE OS ITENS -- e um escore ja e a soma deles. Sem item nao ha
alfa, e por isso metade deste arquivo testa o armazenamento de item, e
nao a conta.

Da conta, o que mais se erra:

  · nao inverter o item redigido ao contrario, e culpar o instrumento;
  · ler o alfa como A confiabilidade, quando ele e um LIMITE INFERIOR;
  · comparar alfas de instrumentos com numeros de itens diferentes;
  · correlacionar o item com um total que o CONTEM.
"""
from __future__ import annotations

import math
import random
import re
import statistics
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import coleta  # noqa: E402
from lape import estatistica as E  # noqa: E402
from lape.db import Database  # noqa: E402

DASHBOARD = (ROOT / "scripts" / "lape" / "templates" / "dashboard.js").read_text(encoding="utf-8")
API = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
SCHEMA = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")


class TestOAlfaContraAFormula(unittest.TestCase):

    def test_bate_com_a_formula_da_covariancia(self):
        """Caminho totalmente outro: k·c̄ / (v̄ + (k-1)·c̄). As duas
        expressões são algebricamente a mesma, e é isso que se confere."""
        s = random.Random(4)
        m = [[s.gauss(0, 1) + s.gauss(0, 1) for _ in range(6)] for _ in range(40)]
        k = 6
        colunas = [[linha[j] for linha in m] for j in range(k)]
        covs = [statistics.covariance(colunas[a], colunas[b])
                for a in range(k) for b in range(k) if a != b]
        cov_media = sum(covs) / len(covs)
        var_media = sum(statistics.variance(c) for c in colunas) / k
        esperado = (k * cov_media) / (var_media + (k - 1) * cov_media)
        self.assertAlmostEqual(E.alfa_de_cronbach(m)["alfa"], esperado, places=4)

    def test_itens_identicos_dao_um(self):
        iguais = [[v, v, v] for v in (3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0)]
        self.assertEqual(E.alfa_de_cronbach(iguais)["alfa"], 1.0)

    def test_itens_independentes_ficam_perto_de_zero(self):
        s = random.Random(9)
        m = [[s.gauss(0, 1) for _ in range(5)] for _ in range(300)]
        self.assertLess(abs(E.alfa_de_cronbach(m)["alfa"]), 0.15)

    def test_sem_variacao_no_total_nao_ha_alfa(self):
        r = E.alfa_de_cronbach([[1.0, 2.0], [2.0, 1.0], [1.5, 1.5]])
        self.assertIsNone(r["alfa"])
        self.assertIn("sem variação", r["aviso"])

    def test_um_item_so_nao_tem_consistencia_interna(self):
        r = E.alfa_de_cronbach([[1.0], [2.0], [3.0]])
        self.assertIsNone(r["alfa"])
        self.assertIn("dois itens", r["aviso"])

    def test_quem_deixou_item_em_branco_nao_entra(self):
        """Alfa se calcula sobre a matriz de covariância, e matriz com
        buraco não tem covariância definida. Imputar a média aqui
        inflaria o alfa de graça."""
        cheio = [[1.0, 2.0, 3.0], [2.0, 3.0, 4.0], [5.0, 4.0, 6.0], [1.0, 1.0, 2.0]]
        com_falta = cheio + [[9.0, None, 1.0]]
        self.assertEqual(E.alfa_de_cronbach(com_falta)["n"], 4)
        self.assertEqual(E.alfa_de_cronbach(com_falta)["alfa"],
                         E.alfa_de_cronbach(cheio)["alfa"])


class TestOItemInvertido(unittest.TestCase):
    """Sem inverter, o alfa despenca e o instrumento leva a culpa por um
    erro de digitacao. E o erro mais comum da planilha de alfa."""

    def matriz(self):
        s = random.Random(2)
        linhas = []
        for _ in range(60):
            bem = s.gauss(3, 1)
            itens = [max(1, min(5, round(bem + s.gauss(0, 0.4)))) for _ in range(3)]
            itens.append(max(1, min(5, round(6 - bem + s.gauss(0, 0.4)))))
            linhas.append(itens)
        return linhas

    def test_sem_inverter_o_alfa_despenca(self):
        self.assertLess(E.alfa_de_cronbach(self.matriz())["alfa"], 0.2)

    def test_invertendo_o_alfa_aparece(self):
        r = E.alfa_de_cronbach(self.matriz(), [False, False, False, True], (1, 5))
        self.assertGreater(r["alfa"], 0.8)
        self.assertEqual(r["invertidos"], 1)

    def test_o_diagnostico_denuncia_o_item_nao_invertido(self):
        """É o valor da tela: sem inverter, o item aparece com correlação
        NEGATIVA com o resto, e tirá-lo subiria muito o alfa."""
        r = E.alfa_de_cronbach(self.matriz())
        culpado = r["itens"][3]
        self.assertLess(culpado["r_com_o_resto"], 0)
        self.assertGreater(culpado["alfa_sem_ele"], r["alfa"] + 0.5)

    def test_a_inversao_espelha_dentro_da_escala(self):
        self.assertEqual(E._inverter(1, 1, 5), 5)
        self.assertEqual(E._inverter(5, 1, 5), 1)
        self.assertEqual(E._inverter(3, 1, 5), 3)
        self.assertEqual(E._inverter(0, 0, 4), 4)

    def test_sem_escala_declarada_nao_se_inverte_nada(self):
        """Inverter sem saber mínimo e máximo é impossível, e adivinhar
        pelo maior valor observado inventaria um teto."""
        m = self.matriz()
        com = E.alfa_de_cronbach(m, [False, False, False, True], None)
        sem = E.alfa_de_cronbach(m)
        self.assertEqual(com["alfa"], sem["alfa"])


class TestODiagnosticoDoItem(unittest.TestCase):

    def test_a_correlacao_e_com_o_resto_e_nao_com_o_total(self):
        """Correlacionar o item com um total que o contém infla a conta --
        o item está correlacionado consigo mesmo --, e o efeito é maior
        justamente onde há poucos itens."""
        s = random.Random(5)
        m = [[s.gauss(0, 1) for _ in range(3)] for _ in range(50)]
        r = E.alfa_de_cronbach(m)
        colunas = [[linha[j] for linha in m] for j in range(3)]
        totais = [sum(linha) for linha in m]
        for j in range(3):
            resto = [totais[i] - colunas[j][i] for i in range(50)]
            esperado = E.correlacao(colunas[j], resto, "pearson")["r"]
            com_total = E.correlacao(colunas[j], totais, "pearson")["r"]
            with self.subTest(item=j):
                self.assertEqual(r["itens"][j]["r_com_o_resto"], esperado)
                self.assertNotEqual(esperado, com_total)

    def test_alfa_sem_ele_bate_com_o_alfa_da_matriz_sem_a_coluna(self):
        s = random.Random(6)
        m = [[s.gauss(0, 1) + s.gauss(0, 1) for _ in range(4)] for _ in range(50)]
        r = E.alfa_de_cronbach(m)
        for j in range(4):
            sem_coluna = [[v for i, v in enumerate(linha) if i != j] for linha in m]
            with self.subTest(item=j):
                self.assertAlmostEqual(r["itens"][j]["alfa_sem_ele"],
                                       E.alfa_de_cronbach(sem_coluna)["alfa"], places=3)

    def test_com_dois_itens_nao_ha_alfa_sem_ele(self):
        """Tirar um de dois deixa um item só, e um item só não tem
        consistência interna."""
        r = E.alfa_de_cronbach([[1.0, 2.0], [3.0, 5.0], [2.0, 3.0], [6.0, 9.0]])
        self.assertTrue(all(i["alfa_sem_ele"] is None for i in r["itens"]))


class TestOIntervaloDoAlfa(unittest.TestCase):

    def test_o_intervalo_contem_o_alfa(self):
        s = random.Random(3)
        m = [[s.gauss(0, 1) + s.gauss(0, 1) for _ in range(5)] for _ in range(40)]
        r = E.alfa_de_cronbach(m)
        self.assertLessEqual(r["ic"][0], r["alfa"])
        self.assertGreaterEqual(r["ic"][1], r["alfa"])

    def test_bate_com_a_definicao_de_feldt(self):
        """(1 - alfa) segue uma F com (n-1) e (n-1)(k-1) graus de
        liberdade. Trocar o primeiro por (k-1) -- o engano fácil --
        continuava dando um intervalo plausível, que continha o alfa e
        estreitava com mais gente: só a conta refeita pega."""
        alfa, n, k = 0.82, 45, 6
        gl1, gl2 = n - 1, (n - 1) * (k - 1)
        baixo = 1.0 - (1.0 - alfa) * E._f_critico(gl1, gl2, 0.975)
        alto = 1.0 - (1.0 - alfa) * E._f_critico(gl1, gl2, 0.025)
        achado = E._ic_do_alfa(alfa, n, k)
        self.assertAlmostEqual(achado[0], round(baixo, 4), places=4)
        self.assertAlmostEqual(achado[1], round(alto, 4), places=4)

    def test_mais_itens_tambem_estreitam_o_intervalo(self):
        """É o segundo grau de liberdade: (n-1)(k-1) cresce com k."""
        poucos = E._ic_do_alfa(0.8, 40, 3)
        muitos = E._ic_do_alfa(0.8, 40, 20)
        self.assertLess(muitos[1] - muitos[0], poucos[1] - poucos[0])

    def test_mais_gente_estreita_o_intervalo(self):
        estreito = E._ic_do_alfa(0.8, 200, 5)
        largo = E._ic_do_alfa(0.8, 15, 5)
        self.assertLess(estreito[1] - estreito[0], largo[1] - largo[0])

    def test_o_quantil_da_f_inverte_a_propria_cdf(self):
        for gl1, gl2, p in ((5, 20, 0.95), (10, 30, 0.975), (3, 8, 0.025)):
            with self.subTest(gl=(gl1, gl2), p=p):
                x = E._f_critico(gl1, gl2, p)
                self.assertAlmostEqual(E.f_cdf(x, gl1, gl2), p, places=4)


class TestOsAvisos(unittest.TestCase):

    def test_poucas_pessoas_ganham_aviso(self):
        s = random.Random(8)
        m = [[s.gauss(0, 1) + s.gauss(0, 1) for _ in range(4)] for _ in range(6)]
        self.assertIn("balança muito", E.alfa_de_cronbach(m)["aviso"])

    def test_alfa_altissimo_avisa_redundancia(self):
        """Acima de 0,95 costuma ser vários itens perguntando a mesma
        coisa com outras palavras -- não excelência."""
        s = random.Random(11)
        quase = [[v + s.gauss(0, 0.01) for _ in range(5)]
                 for v in [s.gauss(0, 1) for _ in range(40)]]
        r = E.alfa_de_cronbach(quase)
        self.assertGreater(r["alfa"], E.ALFA_REDUNDANTE)
        self.assertIn("redundância", r["aviso"])

    def test_muitos_itens_avisam_que_o_alfa_sobe_por_tamanho(self):
        s = random.Random(12)
        m = [[s.gauss(0, 1) + s.gauss(0, 1) for _ in range(25)] for _ in range(40)]
        self.assertIn("sobe por tamanho", E.alfa_de_cronbach(m)["aviso"])


class BaseComItens(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "i.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.prot = coleta.declarar_protocolo(self.db, "p", "Protocolo")
        self.m0 = coleta.declarar_momento(self.db, self.prot["id"], "b", "Base", 1,
                                          dias_apos=0)
        self.inst = coleta.declarar_instrumento(self.db, "q", "Questionário",
                                                minimo=1, maximo=5)
        # conta de verdade: a gravação registra auditoria, e auditoria tem
        # chave estrangeira para members. Um usuário inventado faz o teste
        # quebrar por um motivo que não é o que se está testando.
        from lape import auth
        self.conta = auth.create_account(self.db, "Coord Teste", "coord@udesc.br",
                                         "SenhaDeTeste123!", role="coordenacao")

    def pessoa(self, codigo):
        return coleta.inscrever(self.db, codigo, self.prot["id"],
                                entrou_em=date.today().isoformat())


class TestOArmazenamentoDoItem(BaseComItens):

    def test_o_mesmo_item_nao_entra_duas_vezes(self):
        coleta.declarar_item(self.db, self.inst["id"], "Q1", subescala="A")
        coleta.declarar_item(self.db, self.inst["id"], "Q1", subescala="B")
        itens = coleta.itens(self.db, self.inst["id"])
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["subescala"], "B")

    def test_a_ordem_se_declara_sozinha(self):
        for code in ("Q1", "Q2", "Q3"):
            coleta.declarar_item(self.db, self.inst["id"], code)
        self.assertEqual([i["ordem"] for i in coleta.itens(self.db, self.inst["id"])],
                         [1, 2, 3])

    def test_a_mesma_resposta_nao_entra_duas_vezes(self):
        """NULL não colide com NULL num índice comum, e `momento_id` fica
        em branco no instrumento aplicado fora de protocolo -- que é onde
        a duplicata é mais provável."""
        item = coleta.declarar_item(self.db, self.inst["id"], "Q1")
        p = self.pessoa("P1")
        coleta.responder(self.db, p["id"], item["id"], 3.0)
        coleta.responder(self.db, p["id"], item["id"], 5.0)
        linhas = self.db.dicts("SELECT * FROM respostas_itens")
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["valor"], 5.0)

    def test_a_resposta_com_momento_e_outra_linha(self):
        item = coleta.declarar_item(self.db, self.inst["id"], "Q1")
        p = self.pessoa("P1")
        coleta.responder(self.db, p["id"], item["id"], 3.0)
        coleta.responder(self.db, p["id"], item["id"], 4.0, self.m0["id"])
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM respostas_itens"), 2)

    def test_apagar_o_participante_leva_as_respostas(self):
        item = coleta.declarar_item(self.db, self.inst["id"], "Q1")
        p = self.pessoa("P1")
        coleta.responder(self.db, p["id"], item["id"], 3.0, self.m0["id"])
        self.db.conn.execute("PRAGMA foreign_keys = ON")
        self.db.conn.execute("DELETE FROM participantes WHERE id = ?", (p["id"],))
        self.db.conn.commit()
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM respostas_itens"), 0)

    def test_o_indice_de_resposta_usa_coalesce(self):
        self.assertIn("idx_resposta_unica", SCHEMA)
        bloco = SCHEMA[SCHEMA.index("idx_resposta_unica"):]
        self.assertIn("COALESCE(momento_id, -1)", bloco[:220])

    def test_o_item_nao_guarda_nada_de_pessoa(self):
        colunas = {c["name"] for c in
                   self.db.dicts("PRAGMA table_info(itens_instrumento)")}
        for proibida in ("nome", "email", "telefone", "participante_id"):
            with self.subTest(coluna=proibida):
                self.assertNotIn(proibida, colunas)


class TestAConfiabilidadeDoInstrumento(BaseComItens):

    def semear(self, com_subescalas=True):
        decl = [("T1", "Tensão", 0), ("T2", "Tensão", 0), ("T3", "Tensão", 1),
                ("V1", "Vigor", 0), ("V2", "Vigor", 0), ("V3", "Vigor", 0)]
        if not com_subescalas:
            decl = [(c, None, i) for c, _, i in decl]
        itens = [coleta.declarar_item(self.db, self.inst["id"], c,
                                      subescala=s, invertido=i)
                 for c, s, i in decl]
        sorteio = random.Random(7)
        for k in range(40):
            p = self.pessoa("P%02d" % k)
            fatores = {"Tensão": sorteio.gauss(3, 1), "Vigor": sorteio.gauss(3, 1),
                       None: sorteio.gauss(3, 1)}
            for item, (c, s, inv) in zip(itens, decl):
                v = max(1, min(5, round(fatores[s] + sorteio.gauss(0, 0.4))))
                if inv:
                    v = 6 - v
                coleta.responder(self.db, p["id"], item["id"], float(v), self.m0["id"])
        return itens

    def test_sai_uma_escala_por_subescala_mais_o_total(self):
        """Subescalas medem coisas diferentes de propósito: o alfa do
        instrumento inteiro mistura construtos e diz pouco. O número que
        o revisor pede é o de cada subescala."""
        self.semear()
        r = coleta.confiabilidade(self.db, self.inst["id"])
        nomes = [e["escala"] for e in r["escalas"]]
        self.assertEqual(nomes, ["Instrumento inteiro", "Tensão", "Vigor"])

    def test_cada_subescala_tem_alfa_maior_que_a_mistura(self):
        self.semear()
        r = coleta.confiabilidade(self.db, self.inst["id"])
        por_nome = {e["escala"]: e["alfa"] for e in r["escalas"]}
        self.assertGreater(por_nome["Tensão"], por_nome["Instrumento inteiro"])
        self.assertGreater(por_nome["Vigor"], por_nome["Instrumento inteiro"])

    def test_o_item_invertido_chega_invertido_na_conta(self):
        self.semear()
        r = coleta.confiabilidade(self.db, self.inst["id"])
        tensao = [e for e in r["escalas"] if e["escala"] == "Tensão"][0]
        invertido = [i for i in tensao["itens"] if i["code"] == "T3"][0]
        self.assertTrue(invertido["invertido"])
        self.assertGreater(invertido["r_com_o_resto"], 0)

    def test_sem_itens_a_tela_diz_por_que_nao_ha_alfa(self):
        r = coleta.confiabilidade(self.db, self.inst["id"])
        self.assertEqual(r["escalas"], [])
        self.assertIn("ENTRE OS ITENS", r["aviso"])

    def test_item_invertido_sem_escala_declarada_e_recusado_com_motivo(self):
        outro = coleta.declarar_instrumento(self.db, "sem", "Sem escala")
        for code, inv in (("A", 0), ("B", 1)):
            item = coleta.declarar_item(self.db, outro["id"], code, invertido=inv)
            for k in range(5):
                p = coleta.inscrever(self.db, "X%d%s" % (k, code), self.prot["id"],
                                     entrou_em=date.today().isoformat())
                coleta.responder(self.db, p["id"], item["id"], float(k + 1), self.m0["id"])
        r = coleta.confiabilidade(self.db, outro["id"])
        inteiro = r["escalas"][0]
        self.assertIsNone(inteiro["alfa"])
        self.assertIn("mínimo e máximo", inteiro["aviso"])

    def test_o_codigo_e_o_enunciado_viajam_junto_do_diagnostico(self):
        """Uma tabela de itens com 'item 0, item 1' não se lê: quem
        confere precisa ver a pergunta."""
        self.semear()
        r = coleta.confiabilidade(self.db, self.inst["id"])
        for item in r["escalas"][0]["itens"]:
            self.assertIn("code", item)
            self.assertIn("enunciado", item)


class TestATelaDeConfiabilidade(unittest.TestCase):

    def test_a_tela_existe_e_esta_na_bancada(self):
        self.assertIn('view("confiabilidade"', DASHBOARD)
        secoes = DASHBOARD[DASHBOARD.index("const SECTIONS = ["):
                           DASHBOARD.index("const VIEW_ICON = {")]
        bancada = re.search(r'id: "bancada".*?views: \[(.*?)\]', secoes, re.S)
        self.assertIn("confiabilidade", bancada.group(1))

    def test_tem_icone_vizinhas_e_nao_responde_aos_filtros(self):
        self.assertRegex(DASHBOARD, r'confiabilidade:\s*"\w+"')
        self.assertRegex(DASHBOARD, r"\n  confiabilidade:\s*\[")
        lista = re.search(r"const SEM_FILTROS = \[(.*?)\];", DASHBOARD, re.S)
        self.assertIn("confiabilidade", lista.group(1))

    def test_a_rota_exige_coordenacao(self):
        linha = [l for l in API.splitlines()
                 if "bancada/confiabilidade" in l and 'r"^' in l]
        self.assertTrue(linha)
        self.assertIn('"coordenacao"', linha[-1])

    def test_a_tela_diz_que_o_alfa_e_limite_inferior(self):
        """Ler 0,68 como 'ruim' é o erro comum. É 'pelo menos 0,68'."""
        bloco = DASHBOARD[DASHBOARD.index("function blocoDaEscala("):]
        bloco = bloco[:bloco.index('view("confiabilidade"')]
        self.assertIn("LIMITE INFERIOR", bloco)
        self.assertIn("subestima", bloco)

    def test_a_tela_mostra_o_k_junto_do_alfa(self):
        """0,70 com quatro itens é outra coisa que 0,70 com quarenta."""
        bloco = DASHBOARD[DASHBOARD.index("function blocoDaEscala("):]
        bloco = bloco[:bloco.index('view("confiabilidade"')]
        # nos dois lugares: no cartão e na frase que se lê em voz alta
        self.assertIn('kpi({ label: "Itens", value: C.fmt(e.k) })', bloco)
        self.assertIn('e.k + " itens)."', bloco)

    def test_a_faixa_trata_alfa_altissimo_como_alerta(self):
        bloco = DASHBOARD[DASHBOARD.index("function faixaDoAlfa("):]
        bloco = bloco[:bloco.index("function blocoDaEscala(")]
        self.assertIn("redundante", bloco)
        self.assertIn("0.95", bloco)

    def test_declarar_itens_aceita_a_lista_colada(self):
        """Trinta perguntas em trinta formulários ninguém preenche."""
        bloco = DASHBOARD[DASHBOARD.index("function formularioDeItens("):]
        self.assertIn('area.value.split("\\n")', bloco)
        self.assertIn('o_que: "itens"', bloco)

    def test_o_asterisco_marca_item_invertido(self):
        bloco = DASHBOARD[DASHBOARD.index("function formularioDeItens("):]
        self.assertIn("invertido: invertido", bloco)
        self.assertIn("replace(/\\*\\s*$/", bloco)

    def test_o_asterisco_vira_invertido_de_verdade(self):
        """Conferir só que a expressão existe no arquivo não bastava: a
        mesma expressão aparece na linha de baixo, que limpa o código."""
        bloco = DASHBOARD[DASHBOARD.index("function formularioDeItens("):]
        marcacao = re.search(r"const invertido = (.+?);", bloco)
        self.assertIsNotNone(marcacao)
        self.assertIn("test(partes[0])", marcacao.group(1))
        self.assertNotIn("false", marcacao.group(1))


class TestARotaDeItens(BaseComItens):
    """Chamar a porta, e nao ler o codigo dela.

    O teto de 300 itens estava testado por `assertIn("300", ...)` -- e a
    mensagem de erro tambem contem "300", entao apagar a verificacao
    inteira nao quebrava teste nenhum. Foi a mutacao que mostrou.
    """

    def chamar(self, corpo, papel="coordenacao"):
        from lape import api
        ctx = api.Context.__new__(api.Context)
        ctx.db, ctx.query, ctx.body = self.db, {}, corpo
        ctx.user = {"id": self.conta["member_id"], "login": "coord@udesc.br",
                    "user_role": papel}
        return api.route_bancada_gravar(ctx)

    def test_grava_a_lista_inteira_de_uma_vez(self):
        r = self.chamar({"o_que": "itens", "instrumento_id": self.inst["id"],
                         "itens": [{"code": "Q1", "subescala": "A"},
                                   {"code": "Q2", "subescala": "A", "invertido": True}]})
        self.assertEqual(r["n"], 2)
        itens = coleta.itens(self.db, self.inst["id"])
        self.assertEqual([i["code"] for i in itens], ["Q1", "Q2"])
        self.assertEqual(itens[1]["invertido"], 1)

    def test_a_ordem_vem_da_posicao_na_lista(self):
        self.chamar({"o_que": "itens", "instrumento_id": self.inst["id"],
                     "itens": [{"code": c} for c in ("A", "B", "C")]})
        self.assertEqual([i["ordem"] for i in coleta.itens(self.db, self.inst["id"])],
                         [1, 2, 3])

    def test_trezentos_e_um_itens_sao_recusados(self):
        from lape.api import ApiError
        with self.assertRaises(ApiError) as erro:
            self.chamar({"o_que": "itens", "instrumento_id": self.inst["id"],
                         "itens": [{"code": "Q%d" % i} for i in range(301)]})
        self.assertEqual(erro.exception.status, 400)
        self.assertIn("300", erro.exception.message)

    def test_trezentos_passam(self):
        r = self.chamar({"o_que": "itens", "instrumento_id": self.inst["id"],
                         "itens": [{"code": "Q%d" % i} for i in range(300)]})
        self.assertEqual(r["n"], 300)

    def test_item_sem_codigo_e_recusado_com_motivo(self):
        from lape.api import ApiError
        with self.assertRaises(ApiError) as erro:
            self.chamar({"o_que": "itens", "instrumento_id": self.inst["id"],
                         "itens": [{"enunciado": "sem código"}]})
        self.assertIn("code", erro.exception.message)

    def test_lista_vazia_e_recusada(self):
        from lape.api import ApiError
        with self.assertRaises(ApiError):
            self.chamar({"o_que": "itens", "instrumento_id": self.inst["id"],
                         "itens": []})

    def test_sem_instrumento_e_recusado(self):
        from lape.api import ApiError
        with self.assertRaises(ApiError) as erro:
            self.chamar({"o_que": "itens", "itens": [{"code": "Q1"}]})
        self.assertIn("instrumento_id", erro.exception.message)

    def test_gravar_item_e_da_coordenacao(self):
        from lape.auth import AuthError
        with self.assertRaises(AuthError):
            self.chamar({"o_que": "itens", "instrumento_id": self.inst["id"],
                         "itens": [{"code": "Q1"}]}, papel="integrante")

    def test_a_resposta_tambem_entra_pela_mesma_porta(self):
        item = coleta.declarar_item(self.db, self.inst["id"], "Q1")
        p = self.pessoa("P1")
        r = self.chamar({"o_que": "resposta", "participante_id": p["id"],
                         "item_id": item["id"], "valor": 4.0,
                         "momento_id": self.m0["id"]})
        self.assertEqual(r["valor"], 4.0)


if __name__ == "__main__":
    unittest.main()
