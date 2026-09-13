"""A matriz de correlacao e o grafico mais facil de fazer errado.

Ela produz, de uma vez, dezenas de numeros com aparencia de achado, e
quase toda ferramenta os mostra sem tres coisas: o n de cada par, a
correcao de multiplos testes e o intervalo. Sem as tres, a tela fabrica
descoberta -- e a descoberta fabricada vai para o artigo.

Os testes abaixo cobrem justamente as tres, e mais a que ninguem lembra:
correlacao so tem sentido DENTRO de um mesmo momento.
"""
from __future__ import annotations

import math
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

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
DASHBOARD = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
CHARTS = (TEMPLATES / "charts.js").read_text(encoding="utf-8")
TEMA = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
API = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")


class TestOCoeficiente(unittest.TestCase):

    def test_reta_perfeita_da_um(self):
        self.assertEqual(E.correlacao([1, 2, 3, 4, 5], [3, 5, 7, 9, 11])["r"], 1.0)

    def test_reta_invertida_da_menos_um(self):
        self.assertEqual(E.correlacao([1, 2, 3, 4, 5], [10, 8, 6, 4, 2])["r"], -1.0)

    def test_spearman_ve_curva_que_pearson_nao_ve(self):
        """Spearman mede se SOBE junto; Pearson, se sobe EM LINHA RETA.
        Numa curva que só sobe, o primeiro dá 1 e o segundo não."""
        x, y = [1, 2, 3, 4, 5], [1, 4, 9, 16, 25]
        self.assertEqual(E.correlacao(x, y, "spearman")["r"], 1.0)
        self.assertLess(E.correlacao(x, y, "pearson")["r"], 1.0)

    def test_sem_variacao_nao_ha_correlacao(self):
        r = E.correlacao([5, 5, 5, 5], [1, 2, 3, 4])
        self.assertIsNone(r["r"])
        self.assertIn("não variou", r["aviso"])

    def test_o_intervalo_confere_com_a_conta_a_mao(self):
        r, n = 0.6, 30
        z = 0.5 * math.log((1 + r) / (1 - r))
        erro = 1.0 / math.sqrt(n - 3)
        corte = statistics.NormalDist().inv_cdf(0.975)
        esperado = (math.tanh(z - corte * erro), math.tanh(z + corte * erro))
        achado = E._fisher_ic(r, n)
        self.assertAlmostEqual(achado[0], esperado[0], places=10)
        self.assertAlmostEqual(achado[1], esperado[1], places=10)

    def test_o_p_vem_do_t_com_n_menos_dois(self):
        """Um coeficiente vira teste pelo t com n-2 graus de liberdade --
        dois, porque a reta gasta dois parâmetros. Usar n infla o p e
        faz achado aparecer onde não há."""
        x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y = [2, 1, 4, 3, 6, 5, 8, 7, 10, 9]
        achado = E.correlacao(x, y, "pearson")
        n, r = achado["n"], achado["r"]
        t = r * math.sqrt((n - 2) / (1 - r * r))
        self.assertEqual(achado["p"], round(E.p_bicaudal_t(t, n - 2), 4))
        self.assertNotAlmostEqual(E.p_bicaudal_t(t, n - 2),
                                  E.p_bicaudal_t(t, n), places=6)

    def test_mais_gente_estreita_o_intervalo(self):
        largo = E._fisher_ic(0.5, 12)
        estreito = E._fisher_ic(0.5, 120)
        self.assertLess(estreito[1] - estreito[0], largo[1] - largo[0])

    def test_o_intervalo_de_amostra_pequena_cruza_o_zero(self):
        """Um r de 0,45 com doze pessoas não é achado: o intervalo vai de
        um lado ao outro do zero, e não se sabe nem o SINAL da relação."""
        baixo, alto = E._fisher_ic(0.45, 12)
        self.assertLess(baixo, 0)
        self.assertGreater(alto, 0)


class TestOParCompleto(unittest.TestCase):

    def test_descarta_so_o_par_incompleto(self):
        """Quem não tem os dois valores não forma par -- mas continua nos
        pares que consegue formar com os outros instrumentos."""
        r = E.correlacao([1, 2, 3, None, 5], [2, 4, 6, 8, 10])
        self.assertEqual(r["n"], 4)
        self.assertEqual(r["r"], 1.0)

    def test_o_n_muda_de_par_para_par(self):
        """É a razão de o n aparecer em CADA célula: quem respondeu A e B
        não é o mesmo conjunto de quem respondeu A e C."""
        colunas = {"a": [1, 2, 3, 4, 5], "b": [2, 4, 6, None, None],
                   "c": [1, 3, 2, 5, 4]}
        m = E.matriz_de_correlacao(colunas)
        ns = {(p["a"], p["b"]): p["n"] for p in m["pares"]}
        self.assertEqual(ns[("a", "b")], 3)
        self.assertEqual(ns[("a", "c")], 5)
        self.assertNotEqual(ns[("a", "b")], ns[("a", "c")])


class TestAsMultiplasComparacoes(unittest.TestCase):

    def test_o_maior_p_nao_muda(self):
        ajuste = E.benjamini_hochberg([0.2, 0.5, 0.9])
        self.assertEqual(ajuste[2]["p_ajustado"], 0.9)

    def test_p_iguais_a_posto_sobre_total_caem_todos_no_alfa(self):
        ajuste = E.benjamini_hochberg([0.01, 0.02, 0.03, 0.04, 0.05])
        self.assertEqual([x["p_ajustado"] for x in ajuste], [0.05] * 5)

    def test_o_ajustado_nunca_decresce_quando_o_p_cresce(self):
        ps = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205]
        ajustados = [x["p_ajustado"] for x in E.benjamini_hochberg(ps)]
        self.assertEqual(ajustados, sorted(ajustados))

    def test_a_correcao_derruba_o_achado_marginal_solitario(self):
        """UM p de 0,04 no meio de vinte testes é o que o sorteio produz:
        a 5%, espera-se um. Sem correção ele viraria achado; com ela,
        não sobrevive."""
        ajuste = E.benjamini_hochberg([0.04] + [0.8] * 19)
        self.assertLessEqual(ajuste[0]["p"], 0.05)       # passaria sem correção
        self.assertFalse(ajuste[0]["sobrevive"])         # mas não passa com ela

    def test_muitos_p_pequenos_juntos_sobrevivem(self):
        """O contrário também tem de valer, e é o que separa esta
        correção de Bonferroni: vinte p de 0,04 em vinte testes NÃO são
        sorteio -- sob a hipótese nula esperava-se um, não vinte. A
        correção controla a proporção de falsos ENTRE OS ACHADOS, e não a
        chance de existir qualquer falso; derrubar os vinte seria o
        comportamento de Bonferroni, severo demais para exploração."""
        ajuste = E.benjamini_hochberg([0.04] * 20)
        self.assertTrue(all(x["sobrevive"] for x in ajuste))

    def test_p_muito_pequeno_sobrevive_mesmo_corrigido(self):
        ajuste = E.benjamini_hochberg([0.00001] + [0.4] * 19)
        self.assertTrue(ajuste[0]["sobrevive"])

    def test_a_matriz_conta_quantos_esperava_por_sorteio(self):
        colunas = {c: [1, 2, 3, 4, 5, 6, 7, 8] for c in "abcde"}
        m = E.matriz_de_correlacao(colunas)
        self.assertEqual(m["testes"], 10)                  # 5*4/2
        self.assertAlmostEqual(m["esperados_por_sorteio"], 0.5)

    def test_sem_p_nenhum_a_correcao_nao_quebra(self):
        self.assertEqual(E.benjamini_hochberg([None, None]),
                         [{"p": None, "p_ajustado": None, "sobrevive": None}] * 2)


class TestADiscordanciaEntreMetodos(unittest.TestCase):

    def test_um_valor_distante_faz_os_dois_discordarem(self):
        """Um ponto longe puxa a reta de Pearson e quase não mexe nos
        postos de Spearman. A discordância é o aviso de que o número
        depende de uma pessoa só."""
        x = [1, 2, 3, 4, 5, 6, 7, 50]
        y = [8, 7, 6, 5, 4, 3, 2, 90]
        m = E.matriz_de_correlacao({"x": x, "y": y}, "spearman")
        par = m["pares"][0]
        self.assertTrue(par["discorda"])
        self.assertGreater(abs(par["r"] - par["r_alternativo"]), 0.2)

    def test_dado_comportado_nao_acusa_discordancia(self):
        x = [1, 2, 3, 4, 5, 6, 7, 8]
        y = [2, 4, 5, 8, 9, 12, 13, 16]
        self.assertFalse(E.matriz_de_correlacao({"x": x, "y": y})["pares"][0]["discorda"])


class BaseComBancada(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "c.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.prot = coleta.declarar_protocolo(self.db, "p", "Protocolo")
        self.m0 = coleta.declarar_momento(self.db, self.prot["id"], "base",
                                          "Linha de base", 1, dias_apos=0)
        self.m1 = coleta.declarar_momento(self.db, self.prot["id"], "fim",
                                          "Fim", 2, dias_apos=90)
        self.dor = coleta.declarar_instrumento(self.db, "eva", "Dor")
        self.humor = coleta.declarar_instrumento(self.db, "brums", "Humor")

    def pessoa(self, codigo):
        return coleta.inscrever(self.db, codigo, self.prot["id"],
                                entrou_em=date.today().isoformat())


class TestACorrelacaoNaBancada(BaseComBancada):

    def test_so_cruza_medidas_do_mesmo_momento(self):
        """Misturar momentos infla a correlação: o que os dois
        instrumentos passam a ter em comum é a intervenção que mexeu nos
        dois, e não a relação entre eles."""
        for i in range(8):
            p = self.pessoa("P%d" % i)
            # na base, dor e humor NAO tem relacao nenhuma
            coleta.registrar(self.db, p["id"], self.dor["id"], [3, 9, 4, 8, 5, 7, 6, 6][i], self.m0["id"])
            coleta.registrar(self.db, p["id"], self.humor["id"], [7, 6, 8, 5, 9, 4, 6, 7][i], self.m0["id"])
            # no fim ambos caem muito, o que criaria relacao falsa se
            # os dois momentos fossem jogados no mesmo saco
            coleta.registrar(self.db, p["id"], self.dor["id"], 1.0, self.m1["id"])
            coleta.registrar(self.db, p["id"], self.humor["id"], 1.0, self.m1["id"])
        so_base = coleta.correlacoes(self.db, self.prot["id"], self.m0["id"])
        self.assertEqual(so_base["momento"], "Linha de base")
        self.assertEqual(so_base["pares"][0]["n"], 8)
        self.assertLess(abs(so_base["pares"][0]["r"]), 0.9)

    def test_sem_momento_escolhido_usa_o_primeiro(self):
        for i in range(5):
            p = self.pessoa("Q%d" % i)
            coleta.registrar(self.db, p["id"], self.dor["id"], i + 1, self.m0["id"])
            coleta.registrar(self.db, p["id"], self.humor["id"], i + 2, self.m0["id"])
        r = coleta.correlacoes(self.db, self.prot["id"])
        self.assertEqual(r["momento_id"], self.m0["id"])

    def test_a_coluna_alinha_pela_pessoa_e_nao_pela_posicao(self):
        """Se cada coluna fosse preenchida na ordem em que as medidas
        chegam, uma FALTA no meio deslocaria tudo dali para baixo, e o
        par passaria a juntar a dor de um com o humor de outro.

        Aqui a primeira pessoa não fez a dor. Alinhado pela pessoa, os
        quatro pares restantes são perfeitos (r = 1). Alinhado pela
        posição, o humor dela entraria no lugar do da segunda e arrastaria
        a coluna inteira."""
        gente = [self.pessoa("R%d" % i) for i in range(5)]
        for valor, p in enumerate(gente[1:], start=1):     # a primeira não fez
            coleta.registrar(self.db, p["id"], self.dor["id"], valor, self.m0["id"])
        coleta.registrar(self.db, gente[0]["id"], self.humor["id"], 99, self.m0["id"])
        for valor, p in enumerate(gente[1:], start=1):
            coleta.registrar(self.db, p["id"], self.humor["id"], valor, self.m0["id"])
        r = coleta.correlacoes(self.db, self.prot["id"], self.m0["id"])
        self.assertEqual(r["pares"][0]["n"], 4)            # a primeira não forma par
        self.assertEqual(r["pares"][0]["r"], 1.0)

    def test_instrumento_com_pouca_gente_fica_de_fora(self):
        outro = coleta.declarar_instrumento(self.db, "raro", "Raro")
        for i in range(6):
            p = self.pessoa("S%d" % i)
            coleta.registrar(self.db, p["id"], self.dor["id"], i + 1, self.m0["id"])
            coleta.registrar(self.db, p["id"], self.humor["id"], i + 2, self.m0["id"])
            if i == 0:
                coleta.registrar(self.db, p["id"], outro["id"], 9, self.m0["id"])
        r = coleta.correlacoes(self.db, self.prot["id"], self.m0["id"])
        self.assertNotIn("Raro", r["nomes"])

    def test_com_um_instrumento_so_a_tela_diz_por_que_esta_vazia(self):
        for i in range(4):
            p = self.pessoa("T%d" % i)
            coleta.registrar(self.db, p["id"], self.dor["id"], i + 1, self.m0["id"])
        r = coleta.correlacoes(self.db, self.prot["id"], self.m0["id"])
        self.assertEqual(r["pares"], [])
        self.assertIn("dois instrumentos", r["aviso"])


class TestAMatrizDesenhada(unittest.TestCase):

    def test_a_escala_e_divergente_e_nao_sequencial(self):
        """-1 e +1 são fenômenos opostos, não 'pouco' e 'muito' da mesma
        coisa. Escala sequencial aqui pintaria os dois extremos como se
        um fosse mais do outro."""
        bloco = CHARTS[CHARTS.index("function divCor("):CHARTS.index("function matriz(")]
        self.assertIn("--div-neg-", bloco)
        self.assertIn("--div-pos-", bloco)
        self.assertNotIn("--seq-", bloco)

    def test_nao_usa_cor_de_estado(self):
        """Correlação negativa não é 'ruim': no VO2 ela é a boa notícia.
        Pintar de vermelho-crítico diria o contrário."""
        bloco = CHARTS[CHARTS.index("function matriz("):]
        bloco = bloco[:bloco.index("\n  return {")]
        for reservada in ("--good", "--warning", "--critical", "--serious"):
            self.assertNotIn(reservada, bloco)

    def test_os_dois_polos_e_o_meio_existem_nos_dois_temas(self):
        for modo in ("dark", "light"):
            bloco = TEMA.split(':root[data-theme="%s"]' % modo)[-1] if modo == "light" \
                else TEMA[:TEMA.index(':root[data-theme="light"]')]
            for token in ("--div-mid", "--div-neg-4", "--div-pos-4",
                          "--div-tinta-fraca", "--div-tinta-forte"):
                with self.subTest(modo=modo, token=token):
                    self.assertIn(token, bloco)

    def test_cada_celula_mostra_o_proprio_n(self):
        bloco = CHARTS[CHARTS.index("function matriz("):]
        self.assertIn('"n=" + par.n', bloco)

    def test_o_que_nao_sobrevive_sai_hachurado_e_nao_sumido(self):
        """Esconder o que não passou seria pior: quem lê não saberia que
        o par foi testado."""
        bloco = CHARTS[CHARTS.index("function matriz("):]
        self.assertIn("par.sobrevive", bloco)
        self.assertIn("tramaFraca", bloco)

    def test_a_largura_reserva_espaco_para_o_rotulo_inclinado(self):
        """Texto inclinado ocupa largura à direita de onde começa. Sem
        essa reserva o nome da última coluna sai cortado -- e saía."""
        bloco = CHARTS[CHARTS.index("function matriz("):]
        self.assertIn("const MR = Math.max", bloco)
        self.assertIn("ML + nomes.length * cell + MR", bloco)
        self.assertIn("Math.cos(GRAU", bloco)


class TestATelaDeCorrelacoes(unittest.TestCase):

    def test_a_tela_existe_e_esta_na_bancada(self):
        self.assertIn('view("correlacoes"', DASHBOARD)
        secoes = DASHBOARD[DASHBOARD.index("const SECTIONS = ["):
                           DASHBOARD.index("const VIEW_ICON = {")]
        bancada = re.search(r'id: "bancada".*?views: \[(.*?)\]', secoes, re.S)
        self.assertIn("correlacoes", bancada.group(1))

    def test_nao_responde_aos_filtros_do_painel(self):
        lista = re.search(r"const SEM_FILTROS = \[(.*?)\];", DASHBOARD, re.S)
        self.assertIn("correlacoes", lista.group(1))

    def test_tem_icone_e_vizinhas(self):
        self.assertRegex(DASHBOARD, r'correlacoes:\s*"\w+"')
        self.assertRegex(DASHBOARD, r"\n  correlacoes:\s*\[")

    def test_sem_protocolo_nenhum_a_tela_diz_onde_declarar(self):
        """"Escolha um protocolo" é um beco sem saída quando não existe
        protocolo nenhum: manda fazer, nesta tela, o que só dá para fazer
        em outra. A mensagem precisa dizer onde."""
        bloco = API[API.index("def route_bancada_correlacoes"):]
        bloco = bloco[:bloco.index("\ndef ", 10)]
        self.assertIn("Nenhum protocolo declarado", bloco)
        self.assertIn("Coleta de dados", bloco)

    def test_a_rota_exige_coordenacao(self):
        linha = [l for l in API.splitlines() if "bancada/correlacoes" in l and "ROUTES" not in l]
        self.assertTrue(linha)
        self.assertIn('"coordenacao"', linha[-1])

    def test_sem_servidor_a_tela_diz_por_que_esta_vazia(self):
        bloco = DASHBOARD[DASHBOARD.index('view("correlacoes"'):]
        bloco = bloco[:bloco.index("function _leituraDoPoder")]
        self.assertIn("if (!LIVE)", bloco)
        self.assertIn("não viaja em arquivo", bloco)

    def test_a_frase_segue_o_sinal_da_correlacao(self):
        """"Andam juntos" com r negativo diz o contrário do número. E o
        caso aparece de verdade: mais aptidão aeróbia, menos dor."""
        bloco = DASHBOARD[DASHBOARD.index("function leituraDaMatriz("):]
        bloco = bloco[:bloco.index('view("correlacoes"')]
        self.assertIn("sentidos opostos", bloco)
        self.assertIn("forte.r < 0", bloco)

    def test_a_tela_avisa_que_correlacao_nao_e_causa(self):
        bloco = DASHBOARD[DASHBOARD.index('view("correlacoes"'):]
        bloco = bloco[:bloco.index("function _leituraDoPoder")]
        self.assertIn("não é causa", bloco)

    def test_o_padrao_e_spearman_em_TODO_lugar_que_escolhe(self):
        """Escala clínica é ordinal: humor, dor, percepção de esforço.

        O padrão é escolhido em mais de um ponto -- o que a tela pede ao
        servidor e o que ela pinta no botão. Conferir só um deles deixaria
        passar o pior caso: buscar Pearson e escrever Spearman no botão.
        Por isso a asserção é sobre TODAS as escolhas, e não sobre uma."""
        escolhas = re.findall(r'BANCADA\.metodoCorr \|\| "(\w+)"', DASHBOARD)
        self.assertGreaterEqual(len(escolhas), 2)
        self.assertEqual(set(escolhas), {"spearman"})
        self.assertIn('metodo = "spearman"', API)     # e o servidor concorda


if __name__ == "__main__":
    unittest.main()
