#!/usr/bin/env python3
"""O painel ao vivo: os números de agora, e o que mudou.

    python3 -m unittest tests.test_aovivo -v

O modo de errar aqui é mentir com gráfico -- e há três jeitos fáceis:

1. comparar com zero e sair com "+infinito%": um laboratório que publicou
   1 depois de 0 não cresceu infinito;
2. espalhar por um mês qualquer o artigo que só tem o ano, para a curva
   mensal ficar cheia;
3. escrever uma "leitura" que ninguém consegue refazer a partir do banco.

Cada teste abaixo monta um banco pequeno com datas escolhidas a dedo e
cobra o número exato. O `hoje` é fixo: um painel que depende do relógio
não pode ser conferido.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import aovivo, api, auth  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
HOJE = date(2026, 9, 22)


def _abrir(caminho: Path) -> Database:
    db = Database(caminho)
    db.migrate()
    return db


def _linha(db: Database, nome: str) -> int:
    return db.upsert("research_lines", {"code": nome[:6].lower().replace(" ", "_"), "name": nome},
                     conflict=("code",))


def _artigo(db: Database, titulo: str, **campos) -> int:
    dados = {"title": titulo, "title_key": titulo.lower(), "status": "publicado"}
    dados.update(campos)
    return db.upsert("articles", dados, conflict=("title_key",))


def _submissao(db: Database, artigo: int, **campos) -> None:
    dados = {"article_id": artigo, "attempt_no": campos.pop("attempt_no", 1),
             "journal": "Revista", "decision": "em_avaliacao"}
    dados.update(campos)
    db.execute("INSERT INTO submissions (article_id, attempt_no, journal, decision, submitted_on,"
               " decision_on) VALUES (:article_id, :attempt_no, :journal, :decision,"
               " :submitted_on, :decision_on)",
               {"submitted_on": None, "decision_on": None, **dados})


class BaseComBanco(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = _abrir(Path(self.tmp.name) / "v.sqlite")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)

    def gravar(self):
        self.db.conn.commit()


class TestOPeriodo(BaseComBanco):
    """Alinhado ao ano, com o anterior do mesmo tamanho."""

    def test_este_ano_compara_com_o_ano_passado_inteiro(self):
        per = aovivo.periodo(self.db, "ano", HOJE)
        self.assertEqual((per["de"], per["ate"]), (2026, 2026))
        self.assertEqual(per["anterior"], (2025, 2025))
        self.assertTrue(per["mensal"])
        self.assertEqual(per["meses_restantes"], 3)

    def test_tres_anos_compara_com_os_tres_anteriores(self):
        per = aovivo.periodo(self.db, "3a", HOJE)
        self.assertEqual((per["de"], per["ate"]), (2024, 2026))
        self.assertEqual(per["anterior"], (2021, 2023))
        self.assertFalse(per["mensal"])

    def test_desde_o_inicio_comeca_no_dado_mais_antigo_e_nao_tem_anterior(self):
        _artigo(self.db, "velho", year_published=2019)
        self.gravar()
        per = aovivo.periodo(self.db, "tudo", HOJE)
        self.assertEqual(per["de"], 2019)
        self.assertIsNone(per["anterior"])

    def test_periodo_desconhecido_cai_no_padrao(self):
        self.assertEqual(aovivo.periodo(self.db, "semana", HOJE)["code"], aovivo.PADRAO)
        self.assertEqual(aovivo.periodo(self.db, None, HOJE)["code"], aovivo.PADRAO)


class TestAsSetas(BaseComBanco):
    """A seta só existe quando há com o que comparar."""

    def kpi(self, code, periodo="ano"):
        per = aovivo.periodo(self.db, periodo, HOJE)
        return next(k for k in aovivo.indicadores(self.db, per) if k["code"] == code)

    def test_publicados_contra_o_ano_anterior(self):
        for i in range(3):
            _artigo(self.db, f"a{i}", year_published=2026)
        for i in range(4):
            _artigo(self.db, f"b{i}", year_published=2025)
        self.gravar()
        k = self.kpi("publicacoes")
        self.assertEqual((k["valor"], k["anterior"], k["delta"], k["pct"]), (3, 4, -1, -25.0))

    def test_anterior_zero_nao_vira_infinito(self):
        """1 depois de 0 não é "+infinito%". A seta some, e o número fica."""
        _artigo(self.db, "so agora", year_published=2026)
        self.gravar()
        k = self.kpi("publicacoes")
        self.assertEqual(k["valor"], 1)
        self.assertEqual(k["anterior"], 0)
        self.assertIsNone(k["pct"])

    def test_sem_periodo_anterior_nao_ha_seta(self):
        _artigo(self.db, "x", year_published=2026)
        self.gravar()
        k = self.kpi("publicacoes", "tudo")
        self.assertIsNone(k["anterior"])
        self.assertIsNone(k["pct"])

    def test_publicado_conta_pelo_ano_e_nao_pela_data(self):
        """`year_published` é o campo que o laboratório preenche; a data
        completa nem sempre existe, e quem só tem o ano não pode sumir."""
        _artigo(self.db, "so ano", year_published=2026, published_on=None)
        self.gravar()
        self.assertEqual(self.kpi("publicacoes")["valor"], 1)

    def test_submissoes_e_aceites_pelo_ano_da_data(self):
        a = _artigo(self.db, "s", status="aceito", accepted_on="2026-03-01")
        _submissao(self.db, a, submitted_on="2025-12-30", decision="aceito", decision_on="2026-03-01")
        _submissao(self.db, a, attempt_no=2, submitted_on="2026-01-02")
        self.gravar()
        self.assertEqual(self.kpi("submissoes")["valor"], 1)
        self.assertEqual(self.kpi("submissoes")["anterior"], 1)
        self.assertEqual(self.kpi("aceites")["valor"], 1)

    def test_citacoes_comparam_com_o_instantaneo_do_comeco_do_periodo(self):
        a = _artigo(self.db, "c", year_published=2024, scopus_citations=10, wos_citations=4)
        for dia, n in (("2025-06-01", 3), ("2025-12-15", 6), ("2026-06-01", 9)):
            self.db.execute("INSERT INTO citation_snapshots (article_id, source, citations, snapshot_on)"
                            " VALUES (?, 'scopus', ?, ?)", (a, n, dia))
        self.gravar()
        k = self.kpi("citacoes")
        self.assertEqual(k["valor"], 10)          # a melhor base de hoje
        self.assertEqual(k["anterior"], 6)        # o último instantâneo antes de 2026
        self.assertEqual(k["delta"], 4)

    def test_sem_instantaneo_anterior_as_citacoes_nao_ganham_seta(self):
        _artigo(self.db, "c", year_published=2024, scopus_citations=10)
        self.gravar()
        k = self.kpi("citacoes")
        self.assertEqual(k["valor"], 10)
        self.assertIsNone(k["anterior"])
        self.assertIn("sem instantâneo", k["nota"])

    def test_a_faisca_cobre_seis_anos_com_zero_onde_nao_houve(self):
        _artigo(self.db, "x", year_published=2023)
        self.gravar()
        k = self.kpi("publicacoes")
        self.assertEqual(k["faisca"], [0, 0, 1, 0, 0, 0])
        self.assertEqual(k["faisca_de"], 2021)


class TestAEvolucao(BaseComBanco):

    def test_mes_a_mes_so_com_data_completa_e_o_resto_e_dito(self):
        """Espalhar por um mês qualquer quem só tem o ano daria uma curva
        bonita e falsa. Fica de fora, e a legenda diz quantos."""
        _artigo(self.db, "com data", year_published=2026, published_on="2026-03-10")
        _artigo(self.db, "so ano", year_published=2026)
        self.gravar()
        ev = aovivo.evolucao(self.db, aovivo.periodo(self.db, "ano", HOJE))
        self.assertEqual(ev["grao"], "mes")
        self.assertEqual(len(ev["labels"]), 12)
        publicados = next(s for s in ev["series"] if s["label"] == "Publicados")["values"]
        self.assertEqual(publicados, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(ev["sem_mes"], 1)

    def test_em_varios_anos_o_grao_e_o_ano(self):
        _artigo(self.db, "a", year_published=2024)
        _artigo(self.db, "b", year_published=2026)
        self.gravar()
        ev = aovivo.evolucao(self.db, aovivo.periodo(self.db, "3a", HOJE))
        self.assertEqual(ev["grao"], "ano")
        self.assertEqual(ev["labels"], ["2024", "2025", "2026"])
        publicados = next(s for s in ev["series"] if s["label"] == "Publicados")["values"]
        self.assertEqual(publicados, [1, 0, 1])


class TestOsRecortes(BaseComBanco):

    def test_por_linha_traz_o_anterior_para_a_cascata(self):
        l1 = _linha(self.db, "Motivação")
        l2 = _linha(self.db, "Humor")
        _artigo(self.db, "a", year_published=2026, research_line_id=l1)
        _artigo(self.db, "b", year_published=2026, research_line_id=l1)
        _artigo(self.db, "c", year_published=2025, research_line_id=l2)
        self.gravar()
        d = aovivo.por_linha(self.db, aovivo.periodo(self.db, "ano", HOJE))
        self.assertEqual(d["items"], [{"label": "Motivação", "value": 2, "pct": 100.0}])
        self.assertEqual(d["anterior"], {"Humor": 1})

    def test_por_situacao_e_um_retrato_de_hoje(self):
        _artigo(self.db, "a", status="em_producao")
        _artigo(self.db, "b", status="publicado", year_published=2019)
        self.gravar()
        d = aovivo.por_situacao(self.db)
        self.assertEqual([(s["code"], s["value"]) for s in d],
                         [("em_producao", 1), ("publicado", 1)])

    def test_o_caminho_nao_traz_porcentagem_entre_etapas(self):
        """Referência, registro triado e artigo não são a mesma unidade."""
        _artigo(self.db, "a", status="em_producao")
        _artigo(self.db, "b", status="submetido")
        _artigo(self.db, "c", status="em_revisao")
        self.gravar()
        etapas = aovivo.caminho(self.db)
        self.assertEqual([e["code"] for e in etapas],
                         ["biblioteca", "triagem", "producao", "submissao", "aceite", "publicacao"])
        self.assertEqual(next(e for e in etapas if e["code"] == "submissao")["valor"], 2)
        for e in etapas:
            with self.subTest(etapa=e["code"]):
                self.assertNotIn("pct", e)
                self.assertTrue(e["href"].startswith("/"))
                self.assertTrue(e["faz"])


class TestOsDozeOlhares(BaseComBanco):

    def montar(self, periodo="ano"):
        return {o["code"]: o for o in aovivo.montar(self.db, periodo, HOJE)["doze"]}

    def test_sao_doze_e_cada_um_faz_uma_pergunta(self):
        olhares = aovivo.montar(self.db, "ano", HOJE)["doze"]
        self.assertEqual(len(olhares), 12)
        self.assertEqual(len({o["code"] for o in olhares}), 12)
        for o in olhares:
            with self.subTest(olhar=o["code"]):
                self.assertTrue(o["pergunta"].endswith("?"))

    def test_a_cascata_fecha_a_conta_por_linha(self):
        l1 = _linha(self.db, "Motivação")
        l2 = _linha(self.db, "Humor")
        _artigo(self.db, "a", year_published=2026, research_line_id=l1)
        _artigo(self.db, "b", year_published=2026, research_line_id=l1)
        _artigo(self.db, "c", year_published=2025, research_line_id=l2)
        self.gravar()
        items = self.montar()["cascata"]["dados"]["items"]
        self.assertTrue(items[0]["total"] and items[-1]["total"])
        self.assertEqual((items[0]["value"], items[-1]["value"]), (1, 2))
        soma = items[0]["value"] + sum(i["value"] for i in items[1:-1])
        self.assertEqual(soma, items[-1]["value"])

    def test_sem_anterior_a_cascata_diz_por_que_esta_vazia(self):
        o = self.montar("tudo")["cascata"]
        self.assertIsNone(o["dados"])
        self.assertIn("anterior", o["vazio"])

    def test_o_histograma_soma_todos_os_publicados(self):
        """Cada artigo cai numa faixa só -- inclusive quem está na borda."""
        for i, c in enumerate((0, 3, 7, 30, 80, 100, 250)):
            _artigo(self.db, f"a{i}", year_published=2024, scopus_citations=c)
        self.gravar()
        d = self.montar()["histograma"]["dados"]
        self.assertEqual(d["values"], [1, 1, 1, 1, 2, 1])
        self.assertEqual(sum(d["values"]), d["n"])

    def test_as_faixas_do_histograma_sao_continuas_e_nao_se_sobrepoem(self):
        faixas = aovivo.FAIXAS_DE_CITACAO
        for anterior, esta in zip(faixas, faixas[1:]):
            with self.subTest(faixa=esta[0]):
                self.assertEqual(esta[1], anterior[2] + 1)
        self.assertIsNone(faixas[-1][2])

    def test_a_caixa_usa_dias_ate_a_decisao_por_decisao(self):
        a = _artigo(self.db, "a", status="publicado", year_published=2025)
        _submissao(self.db, a, submitted_on="2025-01-01", decision="aceito", decision_on="2025-04-11")
        _submissao(self.db, a, attempt_no=2, submitted_on="2025-05-01", decision="rejeitado",
                   decision_on="2025-05-31")
        _submissao(self.db, a, attempt_no=3, submitted_on="2025-06-01")       # sem decisão: fora
        # decisão ANTES do envio é erro de digitação, e não uma revista
        # que respondeu em tempo negativo: fica fora
        _submissao(self.db, a, attempt_no=4, submitted_on="2025-08-01", decision="aceito",
                   decision_on="2025-07-01")
        self.gravar()
        grupos = {g["code"]: g["values"] for g in self.montar()["caixa"]["dados"]["groups"]}
        self.assertEqual(grupos, {"aceito": [100], "rejeitado": [30]})

    def test_a_tendencia_calcula_a_media_movel_de_tres(self):
        a = _artigo(self.db, "a", status="submetido")
        """Três em julho, nenhuma em agosto, três em setembro: a média de
        três meses é 2; a de dois seria 1,5. O agosto vazio é o que
        separa uma janela da outra."""
        for n, dia in enumerate(("2026-07-03", "2026-07-20", "2026-07-25", "2026-09-01",
                                 "2026-09-02", "2026-09-03"), start=1):
            _submissao(self.db, a, attempt_no=n, submitted_on=dia)
        self.gravar()
        d = self.montar()["tendencia"]["dados"]
        self.assertEqual(len(d["labels"]), 24)
        self.assertEqual(d["labels"][-1], "set/26")
        bruto = d["series"][0]["values"]
        movel = d["series"][1]["values"]
        self.assertEqual(bruto[-3:], [3, 0, 3])
        self.assertEqual(movel[-1], 2.0)
        self.assertEqual(movel[-2], 1.0)          # (0 + 3 + 0) / 3; com janela de dois seria 1,5

    def test_o_funil_e_uma_coorte_que_so_afunila(self):
        _artigo(self.db, "p", status="publicado", year_published=2025)
        _artigo(self.db, "a", status="aceito")
        _artigo(self.db, "s", status="submetido")
        _artigo(self.db, "e", status="em_producao")
        _artigo(self.db, "x", status="arquivado")
        self.gravar()
        passos = [s["value"] for s in self.montar()["funil"]["dados"]["steps"]]
        self.assertEqual(passos, [4, 3, 2, 1])
        self.assertEqual(passos, sorted(passos, reverse=True))

    def test_o_bullet_diz_se_a_referencia_e_meta_ou_media(self):
        for ano in (2023, 2024, 2025):
            _artigo(self.db, f"a{ano}", year_published=ano)
        _artigo(self.db, "agora", year_published=2026)
        self.db.execute("INSERT INTO goals (year, code, target) VALUES (2026, 'submissoes', 20)")
        self.gravar()
        items = {i["label"]: i for i in self.montar()["bullet"]["dados"]["items"]}
        self.assertEqual(items["Publicações"]["referencia"], "média 3 anos")
        self.assertEqual(items["Publicações"]["target"], 1.0)
        self.assertEqual(items["Submissões"]["referencia"], "meta declarada")
        self.assertEqual(items["Submissões"]["target"], 20)

    def test_o_calor_so_conta_quem_tem_data_completa(self):
        _artigo(self.db, "a", year_published=2026, published_on="2026-02-14")
        _artigo(self.db, "b", year_published=2026)
        self.gravar()
        d = self.montar()["calor"]["dados"]
        self.assertEqual(d["years"], [2022, 2023, 2024, 2025, 2026])
        self.assertEqual(sum(d["values"]), 1)
        self.assertEqual(d["values"][4 * 12 + 1], 1)


class TestAsLeituras(BaseComBanco):
    """Cada frase traz o número e a regra. O que não pode ser refeito não entra."""

    def test_toda_leitura_tem_regra_e_numero(self):
        l1 = _linha(self.db, "Motivação")
        for i in range(3):
            _artigo(self.db, f"a{i}", year_published=2026, published_on=f"2026-0{i + 1}-10",
                    research_line_id=l1, qualis="A1")
        _artigo(self.db, "b", year_published=2025, research_line_id=l1)
        self.gravar()
        d = aovivo.montar(self.db, "ano", HOJE)
        self.assertTrue(d["leituras"])
        for l in d["leituras"]:
            with self.subTest(leitura=l["code"]):
                self.assertTrue(l["regra"])
                self.assertIsNotNone(l["valor"])
                self.assertIn(str(l["valor"]).replace(".", ","), l["texto"])

    def test_sem_anterior_nao_ha_frase_de_variacao(self):
        _artigo(self.db, "a", year_published=2026)
        self.gravar()
        codes = [l["code"] for l in aovivo.montar(self.db, "tudo", HOJE)["leituras"]]
        self.assertNotIn("maior_variacao", codes)
        self.assertNotIn("linha_que_cresceu", codes)

    def test_anterior_zero_tambem_nao_ganha_frase_de_variacao(self):
        _artigo(self.db, "a", year_published=2026)
        self.gravar()
        codes = [l["code"] for l in aovivo.montar(self.db, "ano", HOJE)["leituras"]]
        self.assertNotIn("maior_variacao", codes)

    def test_a_maior_variacao_e_em_modulo_e_avisa_que_o_ano_nao_acabou(self):
        """Uma queda de 50% é notícia maior que uma alta de 20%."""
        _artigo(self.db, "a", year_published=2026)
        _artigo(self.db, "b", year_published=2025)
        _artigo(self.db, "c", year_published=2025)
        s = _artigo(self.db, "s", status="submetido")
        for n, dia in enumerate(("2025-02-01", "2025-03-01", "2025-04-01", "2025-05-01", "2025-06-01",
                                 "2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01", "2026-06-01",
                                 "2026-07-01"), start=1):
            _submissao(self.db, s, attempt_no=n, submitted_on=dia)
        self.gravar()
        frase = next(l for l in aovivo.montar(self.db, "ano", HOJE)["leituras"]
                     if l["code"] == "maior_variacao")
        self.assertTrue(frase["texto"].startswith("Publicados"), frase["texto"])
        self.assertIn("-50,0%", frase["texto"])
        self.assertIn("ainda tem 3 mês", frase["texto"])

    def test_quando_nenhuma_linha_cresceu_nao_ha_linha_que_mais_cresceu(self):
        l1 = _linha(self.db, "Motivação")
        _artigo(self.db, "a", year_published=2025, research_line_id=l1)
        _artigo(self.db, "b", year_published=2025, research_line_id=l1)
        _artigo(self.db, "c", year_published=2026, research_line_id=l1)
        self.gravar()
        codes = [l["code"] for l in aovivo.montar(self.db, "ano", HOJE)["leituras"]]
        self.assertNotIn("linha_que_cresceu", codes)

    def test_o_mes_mais_forte_declara_o_empate_e_quem_ficou_de_fora(self):
        _artigo(self.db, "a", year_published=2026, published_on="2026-02-01")
        _artigo(self.db, "b", year_published=2026, published_on="2026-05-01")
        _artigo(self.db, "c", year_published=2026)
        self.gravar()
        frase = next(l for l in aovivo.montar(self.db, "ano", HOJE)["leituras"]
                     if l["code"] == "mes_mais_forte")
        self.assertIn("empatado", frase["texto"])
        self.assertIn("1 publicado(s) só têm o ano", frase["texto"])

    def test_a_espera_mais_longa_e_a_submissao_mais_antiga_em_avaliacao(self):
        a = _artigo(self.db, "Um título comprido", status="submetido")
        _submissao(self.db, a, submitted_on="2025-01-01", journal="BMC")
        _submissao(self.db, a, attempt_no=2, submitted_on="2024-01-01", decision="rejeitado",
                   decision_on="2024-03-01")
        self.gravar()
        frase = next(l for l in aovivo.montar(self.db, "ano", HOJE)["leituras"]
                     if l["code"] == "espera_mais_longa")
        self.assertEqual(frase["valor"], (HOJE - date(2025, 1, 1)).days)
        self.assertIn("BMC", frase["texto"])

    def test_o_aviso_diz_que_nao_ha_modelo_de_linguagem(self):
        self.assertIn("Não há modelo de linguagem", aovivo.montar(self.db, "ano", HOJE)["aviso"])


class TestOPainelPelaRede(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "l.sqlite"
        db = _abrir(cls.db_path)
        auth.create_account(db, "Loiane", "loiane@udesc.br", "senhaforte123", role="leitura")
        _artigo(db, "a", year_published=2026)
        db.conn.commit()
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

    def entrar(self):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"login": "loiane@udesc.br", "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return (r.headers.get("Set-Cookie") or "").split(";")[0]

    def chamar(self, caminho, cookie=None):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{caminho}",
            headers={**({"Cookie": cookie} if cookie else {})})
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                return r.status, r.headers.get("Content-Type", ""), r.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers.get("Content-Type", ""), exc.read()

    def test_sem_entrar_nao_ha_numeros(self):
        status, _, _ = self.chamar("/api/aovivo")
        self.assertEqual(status, 401)

    def test_quem_le_recebe_o_periodo_pedido(self):
        status, _, corpo = self.chamar("/api/aovivo?periodo=3a", self.entrar())
        self.assertEqual(status, 200)
        d = json.loads(corpo)
        self.assertEqual(d["periodo"]["code"], "3a")
        self.assertEqual(len(d["kpis"]), 4)
        self.assertEqual(len(d["doze"]), 12)
        self.assertEqual(len(d["caminho"]), 6)

    def test_periodo_estranho_cai_no_padrao_em_vez_de_400(self):
        status, _, corpo = self.chamar("/api/aovivo?periodo=ontem", self.entrar())
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(corpo)["periodo"]["code"], aovivo.PADRAO)

    def test_a_pagina_sai_montada_com_o_script_dentro(self):
        for caminho in ("/aovivo", "/ao-vivo"):
            with self.subTest(caminho=caminho):
                status, tipo, corpo = self.chamar(caminho)
                self.assertEqual(status, 200)
                self.assertIn("text/html", tipo)
                html = corpo.decode("utf-8")
                self.assertIn("function desenharPainel", html)
                self.assertNotIn("__AOVIVO_JS__", html)
                self.assertNotIn("__CHARTS_JS__", html)


class TestATela(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.js = (TEMPLATES / "aovivo.js").read_text(encoding="utf-8")
        cls.html = (TEMPLATES / "aovivo.html").read_text(encoding="utf-8")

    def test_as_abas_listadas_sao_as_desenhadas(self):
        for aba in ("painel", "caminho", "doze"):
            with self.subTest(aba=aba):
                self.assertIn(f'["{aba}", ', self.js)
        self.assertIn('ST.aba === "caminho"', self.js)
        self.assertIn('ST.aba === "doze"', self.js)

    def test_cada_olhar_do_servidor_tem_desenho(self):
        trecho = self.js[self.js.index("function figuraDoOlhar"):]
        trecho = trecho[:trecho.index("function desenharDoze")]
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = _abrir(Path(tmp.name) / "o.sqlite")
        self.addCleanup(db.close)
        for o in aovivo.montar(db, "ano", HOJE)["doze"]:
            with self.subTest(olhar=o["code"]):
                self.assertIn(f'case "{o["code"]}":', trecho)

    def test_a_seta_so_aparece_com_pct_e_o_zero_e_explicado(self):
        trecho = self.js[self.js.index("function cartaoKpi"):]
        trecho = trecho[:trecho.index("function cartao(")]
        self.assertIn("k.pct !== null", trecho)
        self.assertIn("sem base para comparar", trecho)

    def test_a_regra_de_cada_leitura_aparece_e_a_tela_diz_que_nao_e_ia(self):
        self.assertIn('"regra: " + l.regra', self.js)
        self.assertIn("sem modelo de linguagem", self.js)

    def test_o_ao_vivo_recarrega_uma_vez_depois_do_silencio(self):
        """Dez gravações seguidas viram um redesenho, e não dez."""
        self.assertIn('new EventSource("/api/stream")', self.js)
        self.assertIn("clearTimeout(recargaMarcada)", self.js)
        self.assertIn("setTimeout(carregar, 1200)", self.js)

    def test_o_caminho_nao_desenha_porcentagem(self):
        trecho = self.js[self.js.index("function desenharCaminho"):]
        trecho = trecho[:trecho.index("function figuraDoOlhar")]
        self.assertNotIn("%", trecho.split("aviso-rodape")[0].replace("100%", ""))

    def test_a_caixa_do_grafico_cresce_com_o_conteudo(self):
        """Com `flex: 1 1 0` a legenda, que vem depois do SVG, saía cortada."""
        self.assertIn(".olhar .plotbox { flex: 0 0 auto; }", self.html)

    def test_o_painel_e_a_area_levam_ao_ao_vivo(self):
        painel = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
        area = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        self.assertIn('href: "/aovivo"', painel)
        self.assertIn('href="/aovivo"', area)


if __name__ == "__main__":
    unittest.main()
