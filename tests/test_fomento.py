"""Fomento: editais, prazos, vigencia e o que NAO foi aprovado.

O modo de errar aqui nao e a conta, e o recorte. Tres recortes errados
sao tao comuns que mereceram teste proprio:

  · contar a submissao pendente como recusa, o que faz a taxa despencar
    toda vez que o laboratorio submete algo novo;
  · tratar "sem prazo declarado" como "prazo longe", escondendo o edital
    cuja data ninguem foi conferir;
  · somar reais de anos diferentes num total unico, que infla sem que
    ninguem perceba.
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import fomento  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
DASHBOARD = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
TEMA = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
API = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")


def daqui(dias: int) -> str:
    return (date.today() + timedelta(days=dias)).isoformat()


class BaseDoFomento(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "f.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()


class TestATaxaDeAprovacao(unittest.TestCase):

    def sub(self, situacao):
        return {"situacao": situacao}

    def test_pendente_nao_e_recusa(self):
        """Contar quem ainda não foi julgado como recusa faria a taxa cair
        toda vez que o laboratório submete algo novo -- o contrário do que
        a taxa deveria dizer."""
        linhas = [self.sub("aprovada")] * 5 + [self.sub("recusada")] * 5 \
            + [self.sub("submetida")] * 10
        r = fomento.taxa_de_aprovacao(linhas)
        self.assertEqual(r["decididas"], 10)
        self.assertEqual(r["pendentes"], 10)
        self.assertEqual(r["taxa"], 50.0)

    def test_retirada_tambem_fica_de_fora(self):
        linhas = [self.sub("aprovada")] * 4 + [self.sub("recusada")] * 4 \
            + [self.sub("retirada")] * 6
        self.assertEqual(fomento.taxa_de_aprovacao(linhas)["decididas"], 8)

    def test_poucas_julgadas_nao_viram_taxa(self):
        """Com três julgadas a taxa só pode ser 0, 33, 67 ou 100 por cento,
        e nenhum desses números diz nada sobre o próximo edital."""
        linhas = [self.sub("aprovada")] * 2 + [self.sub("recusada")]
        r = fomento.taxa_de_aprovacao(linhas)
        self.assertIsNone(r["taxa"])
        self.assertIn("não há taxa", r["aviso"])

    def test_o_aviso_mostra_o_quanto_a_proxima_mexeria(self):
        linhas = [self.sub("aprovada"), self.sub("recusada")]
        aviso = fomento.taxa_de_aprovacao(linhas)["aviso"]
        self.assertIn("33%", aviso)     # se a próxima for recusada
        self.assertIn("67%", aviso)     # se a próxima for aprovada

    def test_no_minimo_a_taxa_aparece(self):
        linhas = [self.sub("aprovada")] * 4 + [self.sub("recusada")] * 4
        self.assertEqual(len(linhas), fomento.N_MINIMO_PARA_TAXA)
        self.assertEqual(fomento.taxa_de_aprovacao(linhas)["taxa"], 50.0)

    def test_uma_a_menos_que_o_minimo_ainda_nao_aparece(self):
        linhas = [{"situacao": "aprovada"}] * (fomento.N_MINIMO_PARA_TAXA - 1)
        self.assertIsNone(fomento.taxa_de_aprovacao(linhas)["taxa"])

    def test_sem_nenhuma_submissao_nao_quebra(self):
        r = fomento.taxa_de_aprovacao([])
        self.assertIsNone(r["taxa"])
        self.assertEqual(r["decididas"], 0)


class TestOsPrazos(BaseDoFomento):

    def test_sem_prazo_declarado_nao_e_prazo_longe(self):
        """São coisas diferentes, e a tela precisa distinguir: um é 'há
        tempo', o outro é 'ninguém foi conferir a data'."""
        fomento.declarar_edital(self.db, "a", "Com prazo", fecha_em=daqui(300))
        fomento.declarar_edital(self.db, "b", "Sem prazo")
        estados = {e["nome"]: e["estado"] for e in fomento.editais(self.db)}
        self.assertEqual(estados["Com prazo"], "aberto")
        self.assertEqual(estados["Sem prazo"], "sem_prazo")

    def test_o_que_fecha_logo_sai_separado(self):
        fomento.declarar_edital(self.db, "perto", "Fecha já", fecha_em=daqui(10))
        fomento.declarar_edital(self.db, "longe", "Fecha depois", fecha_em=daqui(300))
        p = fomento.painel(self.db)
        self.assertEqual([e["nome"] for e in p["fecham_logo"]], ["Fecha já"])

    def test_edital_vencido_nao_entra_como_urgente(self):
        fomento.declarar_edital(self.db, "velho", "Já fechou", fecha_em=daqui(-5))
        p = fomento.painel(self.db)
        self.assertEqual(p["fecham_logo"], [])
        self.assertEqual(fomento.editais(self.db)[0]["estado"], "fechado")

    def test_o_aviso_de_edital_da_tempo_de_escrever(self):
        """45 dias, e o número é a promessa da tela: um edital de projeto
        pede semanas de escrita, e avisar em cima da hora é o mesmo que
        não avisar. O valor vai preso aqui de propósito -- afrouxá-lo para
        uma semana passaria despercebido, e é justamente o que tornaria a
        aba inútil."""
        self.assertEqual(fomento.DIAS_EDITAL_PROXIMO, 45)
        fomento.declarar_edital(self.db, "dentro", "Dentro", fecha_em=daqui(45))
        fomento.declarar_edital(self.db, "fora", "Fora", fecha_em=daqui(46))
        estados = {e["nome"]: e["estado"] for e in fomento.editais(self.db)}
        self.assertEqual(estados["Dentro"], "fecha_logo")
        self.assertEqual(estados["Fora"], "aberto")

    def test_o_aviso_de_vigencia_da_tempo_de_prestar_contas(self):
        """120 dias: prestação de contas é trabalho de trimestre."""
        self.assertEqual(fomento.DIAS_VIGENCIA_PROXIMA, 120)

    def test_edital_arquivado_some_da_lista(self):
        fomento.declarar_edital(self.db, "x", "Arquivado", fecha_em=daqui(5),
                                arquivado=1)
        self.assertEqual(fomento.editais(self.db), [])
        self.assertEqual(len(fomento.editais(self.db, incluir_arquivados=True)), 1)

    def test_data_estragada_nao_derruba_a_tela(self):
        fomento.declarar_edital(self.db, "torto", "Data ruim", fecha_em="30/12/2026")
        self.assertEqual(fomento.editais(self.db)[0]["estado"], "sem_prazo")


class TestAVigencia(BaseDoFomento):

    def projeto(self, code, nome, **extra):
        campos = {"code": code, "name": nome}
        campos.update(extra)
        return self.db.insert("projects", campos)

    def test_so_entra_projeto_com_financiador(self):
        """Projeto sem financiador não tem vigência de recurso para
        acompanhar: listá-lo encheria a tela de linha sem prazo."""
        self.projeto("a", "Com dinheiro", funder="CNPq", ended_on=daqui(30))
        self.projeto("b", "Sem dinheiro", ended_on=daqui(30))
        self.projeto("c", "Financiador em branco", funder="   ", ended_on=daqui(30))
        nomes = [v["name"] for v in fomento.vigencias(self.db)]
        self.assertEqual(nomes, ["Com dinheiro"])

    def test_a_que_termina_logo_sai_separada(self):
        self.projeto("a", "Termina já", funder="CNPq", ended_on=daqui(30))
        self.projeto("b", "Termina longe", funder="CNPq", ended_on=daqui(900))
        p = fomento.painel(self.db)
        self.assertEqual([v["name"] for v in p["terminam_logo"]], ["Termina já"])

    def test_vigencia_encerrada_nao_e_urgencia(self):
        self.projeto("a", "Acabou", funder="CNPq", ended_on=daqui(-40))
        self.assertEqual(fomento.vigencias(self.db)[0]["estado"], "encerrada")
        self.assertEqual(fomento.painel(self.db)["terminam_logo"], [])


class TestOValorPorAno(BaseDoFomento):

    def test_soma_pelo_ano_da_decisao(self):
        for titulo, decidido, valor in [
                ("a", "2024-05-01", 100.0), ("b", "2024-11-01", 50.0),
                ("c", "2025-02-01", 30.0)]:
            fomento.registrar_submissao(self.db, titulo, situacao="aprovada",
                                        decidido_em=decidido, valor_aprovado=valor)
        por_ano = fomento.painel(self.db)["captado_por_ano"]
        self.assertEqual(por_ano, [{"ano": 2024, "valor": 150.0, "n": 2},
                                   {"ano": 2025, "valor": 30.0, "n": 1}])

    def test_recusada_nao_entra_no_captado(self):
        """Nem quando alguém preencheu o valor aprovado por engano, ou
        quando o recurso foi concedido e depois cancelado: quem manda é a
        SITUAÇÃO, e não o campo de valor estar preenchido."""
        fomento.registrar_submissao(self.db, "recusada", situacao="recusada",
                                    decidido_em="2024-05-01", valor_pedido=900.0,
                                    valor_aprovado=900.0)
        fomento.registrar_submissao(self.db, "retirada", situacao="retirada",
                                    decidido_em="2024-05-01", valor_aprovado=500.0)
        self.assertEqual(fomento.painel(self.db)["captado_por_ano"], [])
        self.assertEqual(fomento.painel(self.db)["captado_total"], 0.0)

    def test_aprovada_sem_valor_nao_vira_zero(self):
        """Valor não declarado é desconhecido, e não zero: somá-lo como
        zero faria parecer que o edital não deu dinheiro."""
        fomento.registrar_submissao(self.db, "sem valor", situacao="aprovada",
                                    decidido_em="2024-05-01")
        fomento.registrar_submissao(self.db, "com valor", situacao="aprovada",
                                    decidido_em="2024-05-01", valor_aprovado=80.0)
        por_ano = fomento.painel(self.db)["captado_por_ano"]
        self.assertEqual(por_ano, [{"ano": 2024, "valor": 80.0, "n": 1}])

    def test_o_total_vem_com_os_anos_que_o_formam(self):
        """Somar reais de 2018 com reais de hoje infla o total e ninguém
        percebe. Não há deflator nesta casa, então o mínimo honesto é
        entregar o intervalo junto -- e a tela é obrigada a mostrá-lo."""
        for ano in ("2018", "2026"):
            fomento.registrar_submissao(self.db, "p" + ano, situacao="aprovada",
                                        decidido_em=ano + "-03-01", valor_aprovado=100.0)
        p = fomento.painel(self.db)
        self.assertEqual(p["captado_total"], 200.0)
        self.assertEqual(p["captado_anos"], [2018, 2026])

    def test_sem_nada_captado_o_intervalo_e_nulo(self):
        p = fomento.painel(self.db)
        self.assertEqual(p["captado_total"], 0.0)
        self.assertIsNone(p["captado_anos"])


class TestOQueSeGrava(BaseDoFomento):

    def test_situacao_desconhecida_e_recusada(self):
        with self.assertRaises(ValueError):
            fomento.registrar_submissao(self.db, "x", situacao="talvez")

    def test_declarar_o_mesmo_edital_duas_vezes_nao_duplica(self):
        fomento.declarar_edital(self.db, "cnpq", "Universal", fecha_em=daqui(30))
        fomento.declarar_edital(self.db, "cnpq", "Universal 2026", fecha_em=daqui(40))
        lista = fomento.editais(self.db)
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]["nome"], "Universal 2026")

    def test_a_submissao_existe_sem_projeto(self):
        """É o ponto de a submissão ser entidade própria: a recusada nunca
        vira projeto, e sem ela não há taxa de aprovação nenhuma."""
        linha = fomento.registrar_submissao(self.db, "Recusada", situacao="recusada")
        self.assertIsNone(linha["project_id"])
        self.assertEqual(fomento.taxa_de_aprovacao(
            fomento.submissoes(self.db))["recusadas"], 1)


class TestARotaDeVerdade(BaseDoFomento):
    """Chamar a rota, e nao so ler o codigo dela.

    Os outros testes de tela conferem o FONTE -- que a rota existe, que
    exige coordenacao. Nenhum deles chamava a rota, e por isso um erro de
    chamada passou batido: `code` ia como argumento posicional E dentro
    do resto, e o Python recusava com "argumento repetido". O formulario
    devolvia 400 e a tela ficava muda. Estes testes exercitam o caminho
    que o formulario realmente percorre.
    """

    def chamar(self, corpo, papel="coordenacao"):
        from lape import api
        ctx = api.Context.__new__(api.Context)
        ctx.db = self.db
        ctx.query = {}
        ctx.body = corpo
        ctx.user = {"id": 1, "user_role": papel}
        return api.route_fomento_gravar(ctx)

    def ler(self, papel="coordenacao"):
        from lape import api
        ctx = api.Context.__new__(api.Context)
        ctx.db = self.db
        ctx.query = {}
        ctx.body = None
        ctx.user = {"id": 1, "user_role": papel}
        return api.route_fomento(ctx)

    def test_gravar_edital_com_o_corpo_que_o_formulario_manda(self):
        """O formulário manda `o_que`, `code` e `nome` junto de todo o
        resto, num objeto só. É essa forma que a rota tem de aceitar."""
        r = self.chamar({"o_que": "edital", "code": "cnpq-26",
                         "nome": "Universal 2026", "agencia": "CNPq",
                         "fecha_em": daqui(30), "valor_teto": 150000})
        self.assertTrue(r["ok"])
        self.assertEqual(r["edital"]["nome"], "Universal 2026")
        self.assertEqual(len(fomento.editais(self.db)), 1)

    def test_gravar_submissao_com_o_corpo_que_o_formulario_manda(self):
        r = self.chamar({"o_que": "submissao", "titulo": "Proposta",
                         "submetido_em": "2026-03-01", "situacao": "aprovada",
                         "decidido_em": "2026-06-01", "valor_aprovado": 5000})
        self.assertTrue(r["ok"])
        self.assertEqual(self.ler()["captado_total"], 5000.0)

    def test_sem_o_que_a_rota_explica_em_vez_de_quebrar(self):
        from lape.api import ApiError
        with self.assertRaises(ApiError) as erro:
            self.chamar({"code": "x", "nome": "y"})
        self.assertEqual(erro.exception.status, 400)

    def test_edital_sem_nome_e_recusado_com_motivo(self):
        from lape.api import ApiError
        with self.assertRaises(ApiError) as erro:
            self.chamar({"o_que": "edital", "code": "x"})
        self.assertIn("nome", erro.exception.message)

    def test_situacao_invalida_vira_400_e_nao_500(self):
        from lape.api import ApiError
        with self.assertRaises(ApiError) as erro:
            self.chamar({"o_que": "submissao", "titulo": "t", "situacao": "talvez"})
        self.assertEqual(erro.exception.status, 400)

    def test_integrante_le_mas_nao_grava(self):
        from lape.auth import AuthError
        self.assertIn("editais", self.ler(papel="integrante"))
        with self.assertRaises(AuthError):
            self.chamar({"o_que": "edital", "code": "x", "nome": "y"},
                        papel="integrante")

    def test_a_tela_sabe_quem_pode_declarar(self):
        """Mostrar o formulário para quem não pode gravar é pior do que
        não mostrar: a pessoa preenche tudo e só descobre no botão."""
        self.assertTrue(self.ler(papel="coordenacao")["pode_declarar"])
        self.assertFalse(self.ler(papel="integrante")["pode_declarar"])


class TestATelaDeFomento(unittest.TestCase):

    def test_a_tela_existe_e_fica_em_processo(self):
        self.assertIn('view("fomento"', DASHBOARD)
        secoes = DASHBOARD[DASHBOARD.index("const SECTIONS = ["):
                           DASHBOARD.index("const VIEW_ICON = {")]
        processo = re.search(r'id: "processo".*?views: \[(.*?)\]', secoes, re.S)
        self.assertIn("fomento", processo.group(1))

    def test_nao_responde_aos_filtros_de_artigo(self):
        """Ano, linha e integrante recortam artigo; não recortam edital."""
        lista = re.search(r"const SEM_FILTROS = \[(.*?)\];", DASHBOARD, re.S)
        self.assertIn("fomento", lista.group(1))

    def test_tem_icone(self):
        self.assertRegex(DASHBOARD, r'fomento:\s*"\w+"')

    def test_usa_o_mesmo_chip_de_prazo_da_formacao(self):
        """Bolsa que vence e edital que fecha são a mesma pergunta. Dois
        chips diferentes divergiriam na primeira mudança."""
        bloco = DASHBOARD[DASHBOARD.index("function chipDePrazo("):]
        bloco = bloco[:bloco.index("function linhaDeEdital(")]
        self.assertIn("faixaDe(dias)", bloco)
        self.assertIn("quantoFalta(dias)", bloco)

    def test_a_tela_avisa_da_inflacao_quando_os_anos_diferem(self):
        bloco = DASHBOARD[DASHBOARD.index('view("fomento"'):]
        bloco = bloco[:bloco.index('/* ======')]
        self.assertIn("captado_anos[0] !== f.captado_anos[1]", bloco)
        self.assertIn("inflação", bloco)

    def test_a_taxa_nao_ganha_seta_de_bom_ou_ruim(self):
        """Não há valor de referência para taxa de aprovação em edital:
        50% pode ser excelente num Universal e ruim num interno."""
        bloco = DASHBOARD[DASHBOARD.index("function blocoDeAprovacao("):]
        bloco = bloco[:bloco.index('view("fomento"')]
        self.assertIn('sinal: "neutro"', bloco)
        self.assertNotIn('"sobe"', bloco)

    def test_ler_e_de_integrante_mas_gravar_e_da_coordenacao(self):
        rotas = [l for l in API.splitlines() if '/api/fomento' in l and 'r"^' in l]
        self.assertEqual(len(rotas), 2)
        leitura = [l for l in rotas if '"GET"' in l][0]
        escrita = [l for l in rotas if '"POST"' in l][0]
        self.assertIn('"integrante"', leitura)
        self.assertIn('"coordenacao"', escrita)

    def test_o_css_da_lista_existe(self):
        for regra in (".fom-lista", ".fom-item", ".fom-corpo"):
            with self.subTest(regra=regra):
                self.assertIn(regra, TEMA)


if __name__ == "__main__":
    unittest.main()
