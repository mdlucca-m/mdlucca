"""Os dois dominios que a camada ouro nao via: bancada e fomento.

O lakehouse ja existia -- bronze, prata, ouro, snapshot, linhagem --, mas
o modelo dimensional cobria SO artigo. Medida de participante e dinheiro
de edital ficavam de fora, e com eles ficava de fora metade do que o
laboratorio faz.

O risco de trazer a bancada para ca nao e de conta: e de VAZAMENTO. A
camada ouro mora dentro de data/db.sqlite, que e um arquivo versionado, e
o repositorio e publico. Por isso metade destes testes nao confere numero
nenhum -- confere que nao existe linha que seja de alguem.
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

from lape import coleta, fomento, lake, metrics  # noqa: E402
from lape.db import Database  # noqa: E402

DASHBOARD = (ROOT / "scripts" / "lape" / "templates" / "dashboard.js").read_text(encoding="utf-8")
API = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
GOLD = (ROOT / "sql" / "gold.sql").read_text(encoding="utf-8")


class BaseDoLakehouse(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "l.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()

    def bancada(self, valores_por_grupo):
        """valores_por_grupo: {grupo: [valores]} num unico momento."""
        prot = coleta.declarar_protocolo(self.db, "p", "Protocolo")
        mom = coleta.declarar_momento(self.db, prot["id"], "base", "Base", 1, dias_apos=0)
        inst = coleta.declarar_instrumento(self.db, "eva", "Dor")
        i = 0
        for grupo, valores in valores_por_grupo.items():
            for valor in valores:
                p = coleta.inscrever(self.db, "P%03d" % i, prot["id"], grupo=grupo,
                                     entrou_em=date.today().isoformat())
                coleta.registrar(self.db, p["id"], inst["id"], valor, mom["id"])
                i += 1
        return prot, mom, inst


class TestAMedidaNaoVazaNinguem(BaseDoLakehouse):
    """A camada ouro vive num arquivo versionado. Nada aqui pode ser de
    uma pessoa identificavel."""

    def test_a_celula_de_uma_pessoa_so_sai_sem_estatistica(self):
        """Média de n=1 É o valor daquela pessoa. Com uma pessoa só no
        grupo, o número dela não pode aparecer em lugar nenhum."""
        self.bancada({"raro": [42.0], "cheio": [10.0, 11.0, 12.0, 13.0]})
        lake.build_gold(self.db, verbose=False)
        sozinha = self.db.dicts(
            "SELECT * FROM fact_measurement WHERE group_name = 'raro'")[0]
        self.assertEqual(sozinha["n"], 1)
        self.assertEqual(sozinha["suppressed"], 1)
        for campo in ("mean", "sd", "min_value", "max_value"):
            with self.subTest(campo=campo):
                self.assertIsNone(sozinha[campo])

    def test_o_valor_da_pessoa_sozinha_nao_esta_em_lugar_nenhum(self):
        self.bancada({"raro": [42.0], "cheio": [10.0, 11.0, 12.0, 13.0]})
        lake.build_gold(self.db, verbose=False)
        achado = self.db.dicts(
            "SELECT 1 FROM fact_measurement"
            " WHERE mean = 42.0 OR min_value = 42.0 OR max_value = 42.0")
        self.assertEqual(achado, [])

    def test_o_n_continua_honesto_mesmo_suprimido(self):
        """Apagar a linha inteira esconderia que o grupo existe. A
        contagem fica; o valor é que sai."""
        self.bancada({"raro": [42.0], "cheio": [10.0, 11.0, 12.0, 13.0]})
        lake.build_gold(self.db, verbose=False)
        total = self.db.scalar("SELECT SUM(n) FROM fact_measurement")
        self.assertEqual(total, 5)

    def test_no_limite_a_celula_ja_aparece(self):
        self.bancada({"g": [10.0] * lake.N_MINIMO_DA_CELULA})
        lake.build_gold(self.db, verbose=False)
        linha = self.db.dicts("SELECT * FROM fact_measurement")[0]
        self.assertEqual(linha["suppressed"], 0)
        self.assertIsNotNone(linha["mean"])

    def test_uma_a_menos_que_o_limite_ainda_e_suprimida(self):
        self.bancada({"g": [10.0] * (lake.N_MINIMO_DA_CELULA - 1)})
        lake.build_gold(self.db, verbose=False)
        self.assertEqual(self.db.dicts("SELECT * FROM fact_measurement")[0]["suppressed"], 1)

    def test_o_fato_nao_tem_coluna_que_aponte_para_uma_pessoa(self):
        """Grão de grupo, e não de participante: não existe aqui uma
        linha que seja de alguém."""
        lake.ensure_schema(self.db)
        colunas = {c["name"] for c in self.db.dicts("PRAGMA table_info(fact_measurement)")}
        for proibida in ("participante_id", "participant_id", "codigo", "code",
                         "ano_nascimento", "birth_year"):
            with self.subTest(coluna=proibida):
                self.assertNotIn(proibida, colunas)

    def test_o_desvio_sai_das_somas_e_bate_com_a_conta_direta(self):
        import statistics
        valores = [10.0, 12.0, 15.0, 11.0, 14.0, 9.0]
        self.bancada({"g": valores})
        lake.build_gold(self.db, verbose=False)
        linha = self.db.dicts("SELECT mean, sd FROM fact_measurement")[0]
        self.assertAlmostEqual(linha["mean"], statistics.fmean(valores), places=3)
        self.assertAlmostEqual(linha["sd"], statistics.stdev(valores), places=3)


class TestAChaveDoFato(BaseDoLakehouse):

    def test_escala_unica_nao_duplica(self):
        """Em SQL, NULL não colide com NULL nem numa PRIMARY KEY. Com
        `subscale` anulável, dois builds do mesmo instrumento de escala
        única entrariam como duas linhas -- e é o caso mais comum."""
        lake.ensure_schema(self.db)
        ins = ("INSERT OR REPLACE INTO fact_measurement (protocol_key, protocol_id,"
               " instrument_id, subscale, group_name, n) VALUES ('1:1', 1, 1, '', 'g', ?)")
        self.db.conn.execute(ins, (10,))
        self.db.conn.execute(ins, (99,))
        self.db.conn.commit()
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM fact_measurement"), 1)
        self.assertEqual(self.db.scalar("SELECT n FROM fact_measurement"), 99)

    def test_a_coluna_nao_aceita_nulo(self):
        lake.ensure_schema(self.db)
        info = {c["name"]: c for c in self.db.dicts("PRAGMA table_info(fact_measurement)")}
        self.assertEqual(info["subscale"]["notnull"], 1)
        self.assertEqual(info["group_name"]["notnull"], 1)

    def test_o_construtor_grava_vazio_e_nunca_nulo(self):
        self.bancada({"g": [1.0, 2.0, 3.0]})
        lake.build_gold(self.db, verbose=False)
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM fact_measurement WHERE subscale IS NULL"), 0)


class TestOFatoDeFomento(BaseDoLakehouse):

    def semear(self):
        e = fomento.declarar_edital(self.db, "cnpq", "Universal", agencia="CNPq",
                                    modalidade="projeto", fecha_em="2026-12-01")
        fomento.registrar_submissao(self.db, "Aprovada", edital_id=e["id"],
                                    submetido_em="2026-01-10", situacao="aprovada",
                                    decidido_em="2026-05-10", valor_pedido=100.0,
                                    valor_aprovado=80.0)
        fomento.registrar_submissao(self.db, "Recusada", edital_id=e["id"],
                                    submetido_em="2026-01-11", situacao="recusada",
                                    decidido_em="2026-05-10", valor_pedido=90.0)
        fomento.registrar_submissao(self.db, "Pendente", edital_id=e["id"],
                                    submetido_em="2026-08-01")
        lake.build_gold(self.db, verbose=False)

    def test_a_recusada_entra_no_fato(self):
        """Ela nunca vira projeto, e é metade da informação: sem ela não
        existe taxa de aprovação."""
        self.semear()
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM fact_funding"), 3)
        self.assertEqual(
            self.db.scalar("SELECT COUNT(*) FROM fact_funding WHERE situation='recusada'"), 1)

    def test_pendente_nao_e_julgada_nem_aprovada(self):
        self.semear()
        linha = self.db.dicts("SELECT * FROM fact_funding WHERE title='Pendente'")[0]
        self.assertEqual(linha["is_decided"], 0)
        self.assertEqual(linha["is_approved"], 0)

    def test_a_taxa_do_lake_bate_com_a_do_modulo_de_fomento(self):
        """Se as duas divergirem, a tela e o lake passam a discordar sobre
        o mesmo número e ninguém sabe qual está certo."""
        self.semear()
        do_lake = lake.query(self.db, dataset="fomento", measure="taxa", by="total")
        # o módulo recusa a taxa com poucas julgadas; a conta crua é a mesma
        julgadas = self.db.scalar("SELECT SUM(is_decided) FROM fact_funding")
        aprovadas = self.db.scalar("SELECT SUM(is_approved) FROM fact_funding")
        self.assertEqual(do_lake["rows"][0]["valor"],
                         round(100.0 * aprovadas / julgadas, 1))

    def test_os_dias_ate_decidir_saem_do_par_de_datas(self):
        self.semear()
        linha = self.db.dicts("SELECT * FROM fact_funding WHERE title='Aprovada'")[0]
        self.assertEqual(linha["days_to_decide"], 120)   # 10/01 a 10/05 de 2026
        self.assertEqual(linha["year_decided"], 2026)

    def test_sem_decisao_nao_ha_dias(self):
        self.semear()
        linha = self.db.dicts("SELECT * FROM fact_funding WHERE title='Pendente'")[0]
        self.assertIsNone(linha["days_to_decide"])
        self.assertIsNone(linha["year_decided"])


class TestOExploradorDosTresConjuntos(BaseDoLakehouse):

    def test_o_padrao_continua_sendo_artigos(self):
        """Quem já chamava query(medida, por) antes de os outros conjuntos
        existirem não pode mudar de resposta."""
        lake.build_gold(self.db, verbose=False)
        r = lake.query(self.db, measure="artigos", by="linha")
        self.assertEqual(r["dataset"], "artigos")

    def test_medida_de_um_conjunto_nao_vale_no_outro(self):
        lake.build_gold(self.db, verbose=False)
        with self.assertRaises(lake.QueryError) as erro:
            lake.query(self.db, dataset="fomento", measure="citacoes", by="agencia")
        self.assertIn("fomento", str(erro.exception))

    def test_recorte_de_um_conjunto_nao_vale_no_outro(self):
        lake.build_gold(self.db, verbose=False)
        with self.assertRaises(lake.QueryError):
            lake.query(self.db, dataset="medidas", measure="medicoes", by="qualis")

    def test_filtro_desconhecido_e_recusado_com_a_lista_certa(self):
        lake.build_gold(self.db, verbose=False)
        with self.assertRaises(lake.QueryError) as erro:
            lake.query(self.db, dataset="fomento", measure="propostas", by="agencia",
                       filters={"qualis": "A1"})
        self.assertIn("agencia", str(erro.exception))

    def test_conjunto_desconhecido_e_recusado(self):
        lake.build_gold(self.db, verbose=False)
        with self.assertRaises(lake.QueryError):
            lake.query(self.db, dataset="inventado", measure="artigos", by="linha")

    def test_media_e_taxa_nao_ganham_total(self):
        """Somar médias entre recortes dá número sem sentido: 40% + 60%
        não são 100% de nada."""
        self.bancada({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        lake.build_gold(self.db, verbose=False)
        soma = lake.query(self.db, dataset="medidas", measure="medicoes", by="grupo")
        media = lake.query(self.db, dataset="medidas", measure="media", by="grupo")
        self.assertEqual(soma["total"], 6)
        self.assertIsNone(media["total"])

    def test_o_conjunto_da_bancada_vem_marcado_como_restrito(self):
        self.assertTrue(lake.DATASETS["medidas"]["restrito"])
        self.assertFalse(lake.DATASETS["fomento"].get("restrito"))
        self.assertFalse(lake.DATASETS["artigos"].get("restrito"))

    def test_a_nota_da_supressao_viaja_na_resposta(self):
        """Quem lê o número precisa saber que célula pequena saiu fora."""
        self.bancada({"g": [1.0, 2.0, 3.0]})
        lake.build_gold(self.db, verbose=False)
        r = lake.query(self.db, dataset="medidas", measure="media", by="grupo")
        self.assertIn("não há linha por participante", r["nota"])


class TestQuemAlcancaOConjuntoRestrito(BaseDoLakehouse):

    def test_o_catalogo_esconde_a_bancada_de_quem_nao_alcanca(self):
        """Um seletor com uma opção que o servidor vai recusar é pior do
        que um seletor sem ela."""
        sem = [d["id"] for d in lake.catalog(com_restritos=False)["datasets"]]
        com = [d["id"] for d in lake.catalog(com_restritos=True)["datasets"]]
        self.assertNotIn("medidas", sem)
        self.assertIn("medidas", com)
        self.assertIn("fomento", sem)

    def test_o_payload_nunca_leva_o_conjunto_restrito_nem_para_a_coordenacao(self):
        """O corte aqui não é de PERFIL, é de DESTINO: este payload viaja
        inteiro para docs/, para o mural e para o link público, e o que
        entra nele deixa de ter dono. Cortá-lo só para quem não é
        coordenação deixaria o nome das dimensões da bancada
        ("subescala") dentro do arquivo que vai para a web -- foi
        exatamente o que o guardião do painel pegou."""
        for flag in (False, True):
            with self.subTest(coordenacao=flag):
                payload = metrics.build_payload(self.db, 5, com_dados_da_coordenacao=flag)
                ids = [d["id"] for d in payload["catalog"]["datasets"]]
                self.assertNotIn("medidas", ids)
                self.assertIn("artigos", ids)
                self.assertNotIn("subescala", repr(payload["catalog"]))

    def test_a_tela_busca_o_conjunto_restrito_no_servidor(self):
        """Como ele não vem no arquivo, quem alcança a bancada precisa
        descobri-lo perguntando a quem sabe quem está perguntando."""
        bloco = DASHBOARD[DASHBOARD.index('view("explorar"'):]
        bloco = bloco[:bloco.index('view("organograma"')]
        self.assertIn('fetch("/api/catalog"', bloco)
        self.assertIn("if (LIVE) {", bloco)

    def test_a_rota_de_consulta_exige_coordenacao_para_a_bancada(self):
        """A rota é de LEITURA. Sem esta verificação, o agregado sairia
        para qualquer um que soubesse trocar um parâmetro na URL."""
        bloco = API[API.index("def route_query"):]
        bloco = bloco[:bloco.index("\ndef ", 10)]
        self.assertIn('conj.get("restrito")', bloco)
        self.assertIn('auth.require(ctx.user, "coordenacao")', bloco)

    def test_o_catalogo_continua_entregando_as_chaves_antigas(self):
        """Quem lia este catálogo antes dos conjuntos continua lendo."""
        c = lake.catalog()
        for chave in ("measures", "dimensions", "filters"):
            self.assertIn(chave, c)
        self.assertTrue(any(m["id"] == "artigos" for m in c["measures"]))


class TestOLakeAguentaBancoAntigo(BaseDoLakehouse):

    def apagar_bancada(self):
        self.db.conn.executescript(
            "DROP TABLE IF EXISTS coletas; DROP TABLE IF EXISTS participantes;"
            " DROP TABLE IF EXISTS momentos; DROP TABLE IF EXISTS protocolos;"
            " DROP TABLE IF EXISTS instrumentos; DROP TABLE IF EXISTS editais;"
            " DROP TABLE IF EXISTS submissoes_fomento;")

    def test_construir_o_ouro_sem_as_tabelas_novas_nao_quebra(self):
        """Um banco aberto antes de a bancada existir não pode impedir a
        reconstrução do ouro dos artigos."""
        self.apagar_bancada()
        contagens = lake.build_gold(self.db, verbose=False)
        self.assertEqual(contagens["fact_measurement"], 0)
        self.assertEqual(contagens["fact_funding"], 0)
        self.assertIn("fact_article", contagens)

    def test_o_indicador_que_falta_nao_derruba_o_historico_dos_outros(self):
        """Um indicador que ainda não existe não pode apagar a série dos
        que existem -- e gravar zero seria mentira, então ele não entra."""
        self.apagar_bancada()
        lake.build_gold(self.db, verbose=False)
        lake.take_snapshot(self.db, verbose=False)
        gravados = {x["metric"] for x in
                    self.db.dicts("SELECT DISTINCT metric FROM metric_snapshot")}
        self.assertIn("artigos", gravados)
        self.assertNotIn("participantes_medidos", gravados)


class TestATelaDoExplorador(unittest.TestCase):

    def test_a_barra_de_artigo_some_fora_de_artigos(self):
        """Ela anunciava '19 de 19 artigos' ao lado de um gráfico de 461
        medições: dois números verdadeiros se contradizendo."""
        bloco = DASHBOARD[DASHBOARD.index("function ajustarBarra()"):]
        bloco = bloco[:bloco.index("function montarControles()")]
        self.assertIn('state.conjunto !== "artigos"', bloco)

    def test_os_filtros_do_painel_so_vao_para_artigos(self):
        """A checagem tem de estar em volta DOS FILTROS. Procurar só a
        frase não bastava: ela aparece três vezes nesta tela, e apagar a
        que importa deixava as outras duas para o teste achar."""
        bloco = DASHBOARD[DASHBOARD.index('view("explorar"'):]
        bloco = bloco[:bloco.index('view("organograma"')]
        guardado = re.search(
            r'if \(state\.conjunto === "artigos"\) \{(.*?)\n        \}', bloco, re.S)
        self.assertIsNotNone(guardado, "os filtros do painel não estão sob guarda")
        dentro = guardado.group(1)
        for filtro in ("STATE.linha", "STATE.ano", "STATE.status", "STATE.integrante"):
            with self.subTest(filtro=filtro):
                self.assertIn(filtro, dentro)

    def test_trocar_de_conjunto_troca_medida_e_recorte_junto(self):
        """Uma medida de fomento com um recorte de artigo não é uma
        combinação inválida: é uma tela oferecendo o que não existe."""
        bloco = DASHBOARD[DASHBOARD.index('view("explorar"'):]
        bloco = bloco[:bloco.index('view("organograma"')]
        self.assertIn("state.medida = novo.padrao_medida", bloco)
        self.assertIn("state.por = novo.padrao_recorte", bloco)

    def test_fora_de_artigos_nao_cai_no_calculo_local(self):
        """O cálculo no navegador só sabe somar artigo. Cair nele para
        bancada devolveria números de outro assunto com cara de resposta."""
        bloco = DASHBOARD[DASHBOARD.index('view("explorar"'):]
        bloco = bloco[:bloco.index('view("organograma"')]
        self.assertIn('state.conjunto === "artigos"\n            ? localQuery', bloco)

    def test_a_tela_nao_soma_o_que_nao_se_soma(self):
        bloco = DASHBOARD[DASHBOARD.index('view("explorar"'):]
        bloco = bloco[:bloco.index('view("organograma"')]
        self.assertIn("não se soma entre recortes", bloco)


class TestOEsquemaOuro(unittest.TestCase):

    def test_as_tabelas_novas_sao_derrubadas_e_recriadas(self):
        """A camada ouro é reconstruída inteira: tabela que não cai vira
        acúmulo de linha velha a cada execução."""
        for tabela in ("fact_measurement", "fact_funding", "dim_instrument",
                       "dim_protocol", "dim_agency"):
            with self.subTest(tabela=tabela):
                self.assertIn("DROP TABLE IF EXISTS %s;" % tabela, GOLD)

    def test_as_novas_entram_na_exportacao(self):
        for tabela in ("fact_measurement", "fact_funding", "dim_instrument",
                       "dim_protocol", "dim_agency"):
            with self.subTest(tabela=tabela):
                self.assertIn(tabela, lake.GOLD_TABLES)

    def test_o_historico_nunca_e_derrubado(self):
        """metric_snapshot sobrevive à reconstrução: é medição, não
        derivação."""
        self.assertNotIn("DROP TABLE IF EXISTS metric_snapshot", GOLD)
        self.assertIn("CREATE TABLE IF NOT EXISTS metric_snapshot", GOLD)


if __name__ == "__main__":
    unittest.main()
