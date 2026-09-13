"""Importar a planilha da bancada, e a massa de teste que a cobre.

A Bancada tinha onze telas e nenhum jeito de encher. Sem importador, um
estudo de 40 pessoas sao 1.200 digitacoes -- e as telas de correlacao,
confiabilidade e poder ficam bonitas e vazias.

O risco de um importador nao e errar a conta: e GRAVAR ERRADO EM
SILENCIO. Dado de participante nao se desfaz com Ctrl+Z. Por isso a
maior parte destes testes cobre o que o importador RECUSA a fazer, e o
que ele mostra antes de gravar.
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import coleta, demo, fomento  # noqa: E402
from lape import ingest_bancada as I  # noqa: E402
from lape.db import Database  # noqa: E402

DASHBOARD = (ROOT / "scripts" / "lape" / "templates" / "dashboard.js").read_text(encoding="utf-8")
API = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")


def colado(*linhas: str) -> str:
    return "\n".join(linhas)


class TestOQueEleSeRecusaAFazer(unittest.TestCase):

    def test_sem_coluna_de_codigo_ele_para(self):
        """Numerar as linhas 1..n pareceria funcionar e quebraria na
        segunda importação: a mesma pessoa viraria outra, e o antes e
        depois deixariam de ser da mesma pessoa -- que é exatamente o que
        o teste pareado precisa que seja verdade."""
        with self.assertRaises(I.ImportError_) as erro:
            I.planejar(I.ler_texto(colado("EVA;PSS", "7;22", "6;20")))
        self.assertIn("identifica o participante", str(erro.exception))

    def test_nao_inventa_numero_a_partir_de_texto(self):
        plano = I.planejar(I.ler_texto(colado(
            "Codigo;EVA", "P01;7", "P02;muito alta", "P03;8")))
        self.assertEqual(plano["n_medidas"], 2)
        self.assertTrue(any("muito alta" in p for p in plano["problemas"]))

    def test_linha_sem_codigo_e_relatada_e_nao_engolida(self):
        plano = I.planejar(I.ler_texto(colado(
            "Codigo;EVA", "P01;7", ";8", "P03;6")))
        self.assertEqual(len(plano["participantes"]), 2)
        self.assertTrue(any("sem código" in p for p in plano["problemas"]))

    def test_colunas_de_identificacao_pessoal_sao_ignoradas(self):
        """O esquema da bancada não tem nome nem e-mail de propósito.
        Uma planilha real traz os dois, e eles não podem entrar.

        Telefone e ano de nascimento são NÚMEROS: a regra "coluna sem
        número não é medida" não salva deles. Só a lista de nomes salva,
        e é por isso que ela existe -- um telefone entraria como um
        instrumento chamado "Telefone", com média e desvio-padrão."""
        plano = I.planejar(I.ler_texto(colado(
            "Codigo;Nome;Email;Telefone;Nascimento;EVA",
            "P01;Ana;a@b.c;48999998888;1985;7",
            "P02;Bia;b@b.c;48999997777;1990;6")))
        for proibida in ("Nome", "Email", "Telefone", "Nascimento"):
            with self.subTest(coluna=proibida):
                self.assertIn(proibida, plano["ignoradas"])
        self.assertEqual(plano["instrumentos"], ["EVA"])

    def test_cabecalho_sozinho_e_recusado(self):
        with self.assertRaises(I.ImportError_):
            I.ler_texto("Codigo;EVA")

    def test_texto_sem_separador_e_recusado_com_instrucao(self):
        with self.assertRaises(I.ImportError_) as erro:
            I.ler_texto(colado("uma coisa so", "outra"))
        self.assertIn("Copie do Excel", str(erro.exception))


class TestOsFormatos(unittest.TestCase):

    def test_largo_com_momento_no_nome_da_coluna(self):
        plano = I.planejar(I.ler_texto(colado(
            "Codigo;Grupo;EVA_pre;EVA_pos", "P01;A;7;4", "P02;B;6;6")))
        self.assertEqual(plano["formato"], "largo")
        self.assertEqual(plano["instrumentos"], ["EVA"])
        self.assertEqual(plano["momentos"], ["Pré", "Pós"])
        self.assertEqual(plano["n_medidas"], 4)

    def test_largo_com_coluna_de_momento(self):
        plano = I.planejar(I.ler_texto(colado(
            "Codigo;Momento;EVA;PSS", "P01;Base;7;22", "P01;Final;4;18")))
        self.assertEqual(sorted(plano["instrumentos"]), ["EVA", "PSS"])
        self.assertEqual(plano["momentos"], ["Base", "Final"])

    def test_longo(self):
        plano = I.planejar(I.ler_texto(colado(
            "Participante;Momento;Instrumento;Valor",
            "P01;Base;EVA;7", "P01;Base;PSS;22", "P02;Base;EVA;6")))
        self.assertEqual(plano["formato"], "longo")
        self.assertEqual(plano["n_medidas"], 3)

    def test_o_nome_do_instrumento_preserva_o_texto_da_coluna(self):
        """"EVA" declarado como "eva" apareceria assim em todo relatório,
        e o pesquisador não reconhece o próprio instrumento."""
        plano = I.planejar(I.ler_texto(colado("Codigo;EVA_pre;PSQI_pre", "P01;7;11")))
        self.assertEqual(sorted(plano["instrumentos"]), ["EVA", "PSQI"])

    def test_o_excel_cola_separado_por_tabulacao(self):
        plano = I.planejar(I.ler_texto("Codigo\tEVA\nP01\t7\nP02\t6"))
        self.assertEqual(plano["n_medidas"], 2)

    def test_celula_vazia_no_fim_da_linha_nao_quebra(self):
        """O Excel corta os tabs finais: linha mais curta que o cabeçalho
        é linha com célula vazia, e não linha inválida."""
        plano = I.planejar(I.ler_texto("Codigo\tEVA\tPSS\nP01\t7\t22\nP02\t6"))
        self.assertEqual(len(plano["participantes"]), 2)
        self.assertEqual(plano["n_medidas"], 3)

    def test_a_primeira_linha_curta_nao_apaga_a_coluna(self):
        """As colunas são descobertas na PRIMEIRA linha. Se ela vier
        curta -- e vem, porque o Excel corta os tabs finais --, a coluna
        que falta some do cabeçalho inteiro, e com ela some um
        instrumento do estudo, sem aviso nenhum."""
        plano = I.planejar(I.ler_texto("Codigo\tEVA\tPSS\nP01\t7\nP02\t6\t22"))
        self.assertEqual(plano["instrumentos"], ["EVA", "PSS"])
        self.assertEqual(plano["n_medidas"], 3)


class TestAOrdemDosMomentos(unittest.TestCase):
    """A ordem decide o que e ANTES e o que e DEPOIS no grafico e no
    teste pareado. Errar aqui inverte o estudo."""

    def test_sufixo_conhecido_da_ordem_cronologica(self):
        plano = I.planejar(I.ler_texto(colado("Codigo;EVA_pos;EVA_pre", "P01;4;7")))
        self.assertEqual(plano["momentos"], ["Pré", "Pós"])
        self.assertEqual(plano["ordem_dos_momentos"], "sufixo das colunas")

    def test_momento_de_coluna_fica_na_ordem_da_planilha(self):
        """Não sei a ordem de nomes que eu não escolhi, e não vou fingir
        que sei: ordenar por alfabeto poria "Final" antes de "Base"."""
        plano = I.planejar(I.ler_texto(colado(
            "Codigo;Momento;EVA", "P01;Base;7", "P01;Final;3")))
        self.assertEqual(plano["momentos"], ["Base", "Final"])
        self.assertEqual(plano["ordem_dos_momentos"], "ordem de aparição na planilha")

    def test_a_ordem_da_planilha_e_respeitada_mesmo_invertida(self):
        plano = I.planejar(I.ler_texto(colado(
            "Codigo;Momento;EVA", "P01;Final;3", "P01;Base;7")))
        self.assertEqual(plano["momentos"], ["Final", "Base"])

    def test_nome_conhecido_em_coluna_nao_dispara_a_cronologia(self):
        """Metade dos nomes reconhecidos é pior que nenhum: "Final" viria
        antes de "Base" porque só um deles está na tabela."""
        plano = I.planejar(I.ler_texto(colado(
            "Codigo;Momento;EVA", "P01;Base;7", "P01;Final;3")))
        self.assertNotEqual(plano["momentos"], ["Final", "Base"])


class TestOQuantoFalta(unittest.TestCase):

    def test_a_coluna_pela_metade_aparece(self):
        """O leitor de planilha converte "n/a" e "NA" em célula vazia
        ANTES de o importador ver, então não dá para reclamar de cada
        uma -- mas dá para dizer que a coluna está pela metade."""
        plano = I.planejar(I.ler_texto(colado(
            "Codigo;EVA;PSS", "P01;7;22", "P02;6;", "P03;8;")))
        por_coluna = {p["coluna"]: p for p in plano["preenchimento"]}
        self.assertEqual(por_coluna["EVA"]["faltam"], 0)
        self.assertEqual(por_coluna["PSS"]["faltam"], 2)


class BaseDeImportacao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "i.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        self.prot = coleta.declarar_protocolo(self.db, "e", "Estudo")

    def importar(self, texto, **kw):
        plano = I.planejar(I.ler_texto(texto))
        return I.aplicar(self.db, plano, self.prot["id"], **kw)


class TestAConferenciaAntesDeGravar(BaseDeImportacao):

    def test_conferir_nao_grava_nada(self):
        """É a regra que manda no desenho: importador que grava direto
        estraga o banco em silêncio."""
        plano = I.planejar(I.ler_texto(colado("Codigo;EVA", "P01;7", "P02;6")))
        I.conferir(self.db, plano, self.prot["id"])
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM participantes"), 0)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM coletas"), 0)

    def test_a_conferencia_separa_o_novo_do_que_ja_existe(self):
        self.importar(colado("Codigo;EVA", "P01;7"))
        plano = I.planejar(I.ler_texto(colado("Codigo;EVA", "P01;9", "P02;6")))
        c = I.conferir(self.db, plano, self.prot["id"])
        self.assertEqual(c["participantes_novos"], 1)
        self.assertEqual(c["participantes_existentes"], 1)

    def test_a_conferencia_avisa_o_que_sera_sobrescrito(self):
        """A diferença entre "carregar" e "corrigir" precisa aparecer
        ANTES de a pessoa apertar o botão."""
        self.importar(colado("Codigo;EVA", "P01;7"))
        plano = I.planejar(I.ler_texto(colado("Codigo;EVA", "P01;9")))
        c = I.conferir(self.db, plano, self.prot["id"])
        self.assertEqual(c["medidas_a_sobrescrever"], 1)
        self.assertEqual(c["medidas_a_criar"], 0)

    def test_a_conferencia_lista_o_que_vai_declarar(self):
        plano = I.planejar(I.ler_texto(colado("Codigo;EVA_pre;EVA_pos", "P01;7;4")))
        c = I.conferir(self.db, plano, self.prot["id"])
        self.assertEqual(c["instrumentos_novos"], ["EVA"])
        self.assertEqual(c["momentos_novos"], ["Pré", "Pós"])


class TestOQueGrava(BaseDeImportacao):

    def test_importar_duas_vezes_nao_duplica(self):
        texto = colado("Codigo;Grupo;EVA_pre;EVA_pos", "P01;A;7;4", "P02;B;6;6")
        self.importar(texto)
        antes = self.db.scalar("SELECT COUNT(*) FROM coletas")
        self.importar(texto)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM coletas"), antes)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM participantes"), 2)

    def test_reimportar_corrige_o_valor(self):
        self.importar(colado("Codigo;EVA", "P01;7"))
        self.importar(colado("Codigo;EVA", "P01;9"))
        self.assertEqual(self.db.scalar("SELECT valor FROM coletas"), 9.0)

    def test_o_grupo_vem_da_planilha(self):
        self.importar(colado("Codigo;Grupo;EVA", "P01;intervencao;7", "P02;controle;6"))
        grupos = {p["codigo"]: p["grupo"]
                  for p in coleta.participantes(self.db, self.prot["id"])}
        self.assertEqual(grupos, {"P01": "intervencao", "P02": "controle"})

    def test_os_momentos_entram_na_ordem_do_plano(self):
        self.importar(colado("Codigo;EVA_pos;EVA_pre", "P01;4;7"))
        momentos = self.db.dicts(
            "SELECT nome FROM momentos WHERE protocolo_id = ? ORDER BY ordem",
            (self.prot["id"],))
        self.assertEqual([m["nome"] for m in momentos], ["Pré", "Pós"])

    def test_sem_criar_faltantes_ele_recusa_em_vez_de_inventar(self):
        """O modo para quem já tem o protocolo montado: um erro de
        digitação no cabeçalho não pode virar um instrumento novo."""
        with self.assertRaises(I.ImportError_) as erro:
            self.importar(colado("Codigo;EVAA", "P01;7"), criar_faltantes=False)
        self.assertIn("EVAA", str(erro.exception))
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM instrumentos"), 0)

    def test_a_importacao_alimenta_as_telas_de_analise(self):
        """É a razão de o importador existir: sem ele, correlação,
        confiabilidade e poder ficam vazias."""
        linhas = ["Codigo;Grupo;EVA_pre;EVA_pos;PSS_pre;PSS_pos"]
        for k in range(14):
            g = "intervencao" if k % 2 else "controle"
            linhas.append("P%02d;%s;%d;%d;%d;%d"
                          % (k, g, 7 + k % 3, 4 + k % 4, 22 + k % 5, 18 + k % 3))
        self.importar(colado(*linhas))
        m = coleta.matriz(self.db, self.prot["id"])
        self.assertEqual(m["completude"], 100.0)
        c = coleta.correlacoes(self.db, self.prot["id"])
        self.assertGreaterEqual(c["testes"], 1)
        p = coleta.poder_do_estudo(self.db, self.prot["id"], pareado=True)
        self.assertGreater(p["menor_grupo"], 0)


class TestAMassaDeTeste(unittest.TestCase):
    """A demonstracao cobria artigo e citacao, e nada da bancada -- entao
    as onze telas so podiam ser vistas por quem ja tivesse dado real, que
    e exatamente quem ainda nao tem."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Database(Path(cls.tmp.name) / "d.sqlite")
        cls.db.migrate()
        demo.seed(cls.db, n_artigos=40, verbose=False)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.tmp.cleanup()

    def test_a_demonstracao_gera_um_protocolo_completo(self):
        protocolos = coleta.protocolos(self.db)
        self.assertTrue(protocolos)
        momentos = self.db.dicts("SELECT * FROM momentos WHERE protocolo_id = ?",
                                 (protocolos[0]["id"],))
        self.assertGreaterEqual(len(momentos), 3)

    def test_gera_medida_e_resposta_de_item(self):
        self.assertGreater(self.db.scalar("SELECT COUNT(*) FROM coletas"), 300)
        self.assertGreater(self.db.scalar("SELECT COUNT(*) FROM respostas_itens"), 800)

    def test_tem_perda_de_seguimento_de_proposito(self):
        """Massa perfeita esconde exatamente os avisos que essas telas
        existem para dar."""
        fora = self.db.scalar(
            "SELECT COUNT(*) FROM participantes WHERE situacao <> 'ativo'")
        self.assertGreater(fora, 0)
        m = coleta.matriz(self.db, coleta.protocolos(self.db)[0]["id"])
        self.assertGreater(m["fora"], 0)
        self.assertLess(m["completude"], 100.0)

    def test_falta_celula_tambem_de_quem_continua_no_estudo(self):
        """Célula faltando e perda de seguimento são coisas diferentes:
        uma é a pessoa que saiu, a outra é o dia em que o aparelho
        falhou. Contar só a primeira faria a completude parecer perfeita
        entre quem ficou -- e é justamente a segunda que faz o `n` mudar
        de um instrumento para outro na mesma tela."""
        prot = coleta.protocolos(self.db)[0]
        ativos = {p["id"] for p in coleta.participantes(self.db, prot["id"])
                  if p["situacao"] == "ativo"}
        momentos = self.db.scalar(
            "SELECT COUNT(*) FROM momentos WHERE protocolo_id = ?", (prot["id"],))
        instrumentos = self.db.scalar(
            "SELECT COUNT(DISTINCT instrumento_id) FROM coletas")
        marcas = ",".join("?" * len(ativos))
        feitas = self.db.scalar(
            "SELECT COUNT(*) FROM coletas WHERE participante_id IN (%s)" % marcas,
            tuple(ativos))
        self.assertLess(feitas, len(ativos) * momentos * instrumentos)

    def test_o_efeito_aparece_no_grupo_de_intervencao_e_nao_no_controle(self):
        prot = coleta.protocolos(self.db)[0]
        eva = [i for i in coleta.instrumentos(self.db) if i["code"] == "eva"][0]
        t = coleta.testar(self.db, prot["id"], eva["id"])
        por_grupo = {d["grupo"]: (d.get("teste") or {}) for d in t["dentro"]}
        self.assertLess(por_grupo["intervencao"].get("p"), 0.05)
        self.assertGreater(por_grupo["controle"].get("p"), 0.05)

    def test_o_brums_tem_subescalas_com_alfa_melhor_que_o_total(self):
        brums = [i for i in coleta.instrumentos(self.db) if i["code"] == "brums"][0]
        r = coleta.confiabilidade(self.db, brums["id"])
        por_nome = {e["escala"]: e["alfa"] for e in r["escalas"]}
        self.assertIn("Tensão", por_nome)
        self.assertGreater(por_nome["Tensão"], por_nome["Instrumento inteiro"])

    def test_os_itens_invertidos_estao_marcados_na_massa(self):
        """Dois, e não "algum": a massa existe para exercitar a inversão,
        e com um só uma metade do caminho fica sem teste."""
        brums = [i for i in coleta.instrumentos(self.db) if i["code"] == "brums"][0]
        itens = coleta.itens(self.db, brums["id"])
        invertidos = sorted(i["code"] for i in itens if i["invertido"])
        self.assertEqual(invertidos, ["F3", "T3"])
        # e a inversão precisa estar dando certo: o item invertido tem de
        # correlacionar POSITIVO com o resto da sua subescala
        r = coleta.confiabilidade(self.db, brums["id"])
        tensao = [e for e in r["escalas"] if e["escala"] == "Tensão"][0]
        t3 = [i for i in tensao["itens"] if i["code"] == "T3"][0]
        self.assertGreater(t3["r_com_o_resto"], 0)

    def test_o_fomento_tem_recusa_de_proposito(self):
        """Sem as recusadas não existe taxa de aprovação: existe a
        lembrança de quem aprovou."""
        p = fomento.painel(self.db)
        self.assertGreater(p["aprovacao"]["recusadas"], 0)
        self.assertGreater(p["aprovacao"]["aprovadas"], 0)
        self.assertIsNotNone(p["aprovacao"]["taxa"])

    def test_ha_edital_com_prazo_proximo(self):
        p = fomento.painel(self.db)
        self.assertTrue(p["fecham_logo"])


class TestATelaDeImportacao(unittest.TestCase):

    def test_a_tela_existe_e_esta_na_bancada(self):
        self.assertIn('view("importar_bancada"', DASHBOARD)
        secoes = DASHBOARD[DASHBOARD.index("const SECTIONS = ["):
                           DASHBOARD.index("const VIEW_ICON = {")]
        bancada = re.search(r'id: "bancada".*?views: \[(.*?)\]', secoes, re.S)
        self.assertIn("importar_bancada", bancada.group(1))

    def test_tem_icone_vizinhas_e_nao_responde_aos_filtros(self):
        self.assertRegex(DASHBOARD, r'importar_bancada:\s*"\w+"')
        self.assertRegex(DASHBOARD, r"\n  importar_bancada:\s*\[")
        lista = re.search(r"const SEM_FILTROS = \[(.*?)\];", DASHBOARD, re.S)
        self.assertIn("importar_bancada", lista.group(1))

    def test_conferir_e_aplicar_sao_dois_botoes(self):
        """Um botão só seria "gravar e torcer"."""
        bloco = DASHBOARD[DASHBOARD.index('view("importar_bancada"'):]
        bloco = bloco[:bloco.index('/* ======')]
        self.assertIn('text: "Conferir"', bloco)
        self.assertIn('text: "Aplicar ao banco"', bloco)
        self.assertIn("chamar(false)", bloco)
        self.assertIn("chamar(true)", bloco)

    def test_a_tela_avisa_da_sobrescrita(self):
        bloco = DASHBOARD[DASHBOARD.index("function blocoDaConferencia("):]
        bloco = bloco[:bloco.index('view("importar_bancada"')]
        self.assertIn("vai por cima de medida que já existe", bloco)

    def test_a_rota_so_grava_quando_mandam(self):
        bloco = API[API.index("def route_bancada_importar"):]
        bloco = bloco[:bloco.index("\ndef ", 10)]
        self.assertIn('if not corpo.get("aplicar"):', bloco)
        self.assertIn('"passo": "conferencia"', bloco)

    def test_a_rota_exige_coordenacao(self):
        linha = [l for l in API.splitlines() if "bancada/importar" in l and 'r"^' in l]
        self.assertTrue(linha)
        self.assertIn('"coordenacao"', linha[-1])


if __name__ == "__main__":
    unittest.main()
