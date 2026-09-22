#!/usr/bin/env python3
"""Sinais e cálculo, temas, o globo e o buscador do painel ao vivo.

    python3 -m unittest tests.test_sinais -v

O cálculo é discreto e escrito à mão, então cada peça é conferida
contra um caso em que a resposta se sabe de cabeça: a derivada de uma
reta é constante, a integral de uma constante é a área do retângulo, a
tendência de uma série reta é a própria série, a estação de uma série
sem estação é zero, e uma reta não tem inflexão nem teto.
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

from lape import aovivo, api, auth, biblioteca, linhas, sinais  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
HOJE = date(2026, 9, 22)


class TestOCalculoDiscreto(unittest.TestCase):

    def test_a_derivada_de_uma_reta_e_constante(self):
        self.assertEqual(sinais.derivada([0, 2, 4, 6, 8]), [2.0, 2.0, 2.0, 2.0, 2.0])

    def test_a_derivada_e_central_no_meio_e_simples_nas_pontas(self):
        self.assertEqual(sinais.derivada([0, 1, 4, 9]), [1.0, 2.0, 4.0, 5.0])
        self.assertEqual(sinais.derivada([3]), [0.0])
        self.assertEqual(sinais.derivada([]), [])

    def test_a_integral_de_uma_constante_e_o_retangulo(self):
        i = sinais.integral([2, 2, 2, 2])
        self.assertEqual(i["area"], 6.0)               # 3 intervalos x 2
        self.assertEqual(i["acumulada"], [0.0, 2.0, 4.0, 6.0])

    def test_o_acumulado_parte_da_base(self):
        self.assertEqual(sinais.acumulado([1, 0, 2], base=10), [11.0, 11.0, 13.0])

    def test_a_tendencia_de_uma_reta_e_a_propria_reta_no_meio(self):
        v = [float(i) for i in range(30)]
        t = sinais.media_movel_centrada(v, 12)
        for i in range(6, 24):
            self.assertAlmostEqual(t[i], v[i], places=3)
        # nas pontas a janela encolhe em vez de sumir: nada fica em branco
        self.assertEqual(len(t), 30)
        self.assertTrue(all(isinstance(x, float) for x in t))

    def test_sem_estacao_a_estacao_e_zero(self):
        v = [float(i) for i in range(36)]
        d = sinais.decompor(v, [f"2024-{m:02d}" for m in range(1, 13)] * 3)
        self.assertTrue(all(abs(s) < 1e-6 for s in d["sazonal"]))

    def test_uma_estacao_forte_aparece_no_perfil(self):
        rotulos = [f"{2021 + i // 12}-{i % 12 + 1:02d}" for i in range(48)]
        v = [5.0 if (i % 12) == 11 else 1.0 for i in range(48)]   # dezembro publica mais
        d = sinais.decompor(v, rotulos)
        self.assertEqual(max(range(12), key=lambda m: d["perfil_sazonal"][m]), 11)
        self.assertAlmostEqual(sum(d["perfil_sazonal"]), 0.0, places=3)

    def test_a_razao_sinal_ruido_e_none_sem_ruido(self):
        d = sinais.decompor([2.0] * 24, [f"2024-{m:02d}" for m in range(1, 13)] * 2)
        self.assertIsNone(d["sinal_ruido"])

    def test_uma_reta_nao_tem_inflexao_e_uma_curva_em_s_tem_uma(self):
        self.assertEqual(sinais.inflexoes([float(i) for i in range(20)]), [])
        import math
        s = [10 / (1 + math.exp(-(i - 10) / 2)) for i in range(21)]
        achadas = sinais.inflexoes(s, [str(i) for i in range(21)])
        self.assertEqual(len(achadas), 1)
        self.assertEqual(achadas[0]["sentido"], "passa a desacelerar")
        self.assertIn(achadas[0]["i"], (9, 10, 11))

    def test_uma_reta_nao_tem_teto_e_uma_logistica_tem(self):
        reta = [float(i) for i in range(1, 40)]
        self.assertIsNone(sinais.limite(reta)["K"])
        import math
        curva = [100 / (1 + math.exp(-0.2 * (i - 25))) for i in range(60)]
        lim = sinais.limite(curva)
        self.assertIsNotNone(lim["K"])
        self.assertLess(abs(lim["K"] - 100) / 100, 0.15)
        self.assertGreater(lim["atingido"], 90)

    def test_poucos_pontos_nao_ajustam_curva(self):
        self.assertIsNone(sinais.limite([1, 2, 3])["K"])


class BaseComProducao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "s.sqlite")
        self.db.migrate()
        linhas.instalar(self.db)
        biblioteca.instalar(self.db)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)
        self.linha = int(self.db.scalar("SELECT id FROM research_lines WHERE code = 'psicologia_do_esporte'"))
        for i in range(24):
            ano, mes = 2025 + i // 12, i % 12 + 1
            for j in range(1 + (i % 3)):
                self.db.upsert("articles", {"title": f"art {i}-{j}", "title_key": f"art_{i}_{j}", "status": "publicado",
                                            "published_on": f"{ano}-{mes:02d}-10", "year_published": ano,
                                            "research_line_id": self.linha, "journal": "Rev " + str(j),
                                            "study_type": "Estudo transversal", "open_access": j % 2, "doi": f"10.1/{i}{j}"},
                               conflict=("title_key",))
        self.db.upsert("articles", {"title": "so ano", "title_key": "so_ano", "status": "publicado", "year_published": 2025},
                       conflict=("title_key",))
        self.db.conn.commit()


class TestASerieMensal(BaseComProducao):

    def test_conta_por_mes_e_diz_quem_so_tem_o_ano(self):
        s = sinais.serie_mensal(self.db, HOJE, meses=12)
        self.assertEqual(s["labels"][0], "2025-10")
        self.assertEqual(s["labels"][-1], "2026-09")
        self.assertEqual(s["sem_mes"], 1)
        # de 2025-10 (i = 9) a 2026-09 (i = 20); o que vem depois fica fora
        self.assertEqual(sum(s["valores"]), sum(1 + (i % 3) for i in range(9, 21)))
        self.assertEqual(s["base_antes"], sum(1 + (i % 3) for i in range(9)))

    def test_analisar_devolve_tudo_o_que_a_tela_desenha(self):
        a = sinais.analisar(self.db, HOJE)
        for chave in ("labels", "meses", "valores", "acumulado", "derivada", "segunda_derivada", "integral",
                      "tendencia", "sazonal", "ruido", "perfil_sazonal", "sinal_ruido", "inflexoes", "limite",
                      "ritmo", "soma", "leituras"):
            with self.subTest(chave=chave):
                self.assertIn(chave, a)
        self.assertEqual(len(a["labels"]), len(a["valores"]))
        self.assertEqual(len(a["perfil_sazonal"]), 12)
        self.assertEqual(a["meses"][-1], "set/26")
        self.assertTrue(a["leituras"])


class TestOsTemasEOMundo(BaseComProducao):

    def test_os_kpis_tematicos_saem_do_banco(self):
        per = aovivo.periodo(self.db, "ano", HOJE)
        t = aovivo.temas(self.db, per, HOJE)
        por = {k["code"]: k for k in t["kpis"]}
        pares = [(i, j) for i in range(12, 24) for j in range(1 + (i % 3))]      # os de 2026
        abertos = sum(1 for _, j in pares if j % 2)
        self.assertEqual(por["acesso_aberto"]["valor"], round(100.0 * abertos / len(pares), 1))
        self.assertEqual(por["tipo"]["valor"], "Estudo transversal")
        self.assertEqual(por["internacional"]["valor"], 0.0)
        self.assertEqual(por["revistas"]["valor"], 3)
        self.assertEqual(t["radar"]["axes"], list(aovivo.EIXOS_DO_RADAR))
        self.assertEqual(len(t["radar"]["series"]), 1)
        self.assertEqual(len(t["radar"]["series"][0]["values"]), 5)
        self.assertEqual(t["haltere"][0]["from"], sum(1 + (i % 3) for i in range(12)))
        self.assertEqual(t["bump"]["labels"][-1], "2026")
        self.assertTrue(t["sankey"]["links"])
        self.assertTrue(t["treemap"])
        self.assertEqual(t["calendario"]["year"], 2026)
        self.assertGreater(t["calendario"]["total"], 0)

    def test_colaboracao_internacional_le_o_pais_da_afiliacao(self):
        artigo = int(self.db.scalar("SELECT id FROM articles WHERE title_key = 'art_23_0'"))
        self.db.execute("INSERT INTO article_countries (article_id, country) VALUES (?, 'Portugal')", (artigo,))
        self.db.conn.commit()
        per = aovivo.periodo(self.db, "ano", HOJE)
        por = {k["code"]: k for k in aovivo.temas(self.db, per, HOJE)["kpis"]}
        self.assertGreater(por["internacional"]["valor"], 0)
        self.assertEqual(por["paises"]["valor"], 1)

    def test_o_mundo_tem_a_sede_e_so_paises_com_coordenada(self):
        m = aovivo.mundo(self.db)
        self.assertEqual(m["sede"]["pais"], "Brasil")
        self.assertIsInstance(m["paises"], list)
        for p in m["paises"]:
            self.assertIsNotNone(p["latitude"])
        self.assertIn("instituicoes", m)

    def test_montar_leva_as_tres_pecas_novas(self):
        d = aovivo.montar(self.db, "ano", HOJE)
        for chave in ("temas", "mundo", "sinais"):
            self.assertIn(chave, d)


class TestOBuscador(BaseComProducao):

    def test_acha_sem_caixa_e_sem_acento_e_em_cada_grupo(self):
        self.db.upsert("projects", {"code": "p1", "name": "Motivação no handebol escolar"}, conflict=("code",))
        pessoa = self.db.member_id("Joana Motivação")
        self.db.conn.commit()
        r = aovivo.buscar(self.db, "MOTIVACAO", quem=pessoa, perfil="coordenacao")
        self.assertTrue(any("handebol" in p["nome"].lower() for p in r["projetos"]))
        self.assertTrue(any(l["code"] == "psicologia_exercicio" for l in r["linhas"]))   # palavra-chave "motivação"
        self.assertTrue(any(a["code"] == "motivacao_handebol" for a in r["acervos"]))
        self.assertTrue(any(p["nome"] == "Joana Motivação" for p in r["pessoas"]))
        self.assertGreater(r["total"], 0)
        # "HANDEBOL" acha os segmentos ("Handebol feminino") sem caixa
        segmentos = [t for t in aovivo.buscar(self.db, "HANDEBOL", perfil="coordenacao")["temas"] if t["tipo"] == "segmento"]
        self.assertTrue(segmentos)
        self.assertTrue(any(s["acervo"] == "motivacao_handebol" for s in segmentos))

    def test_termo_curto_nao_busca(self):
        self.assertEqual(aovivo.buscar(self.db, "m")["total"], 0)

    def test_cada_grupo_para_em_oito(self):
        r = aovivo.buscar(self.db, "art")
        self.assertLessEqual(len(r["artigos"]), aovivo.POR_GRUPO)
        self.assertGreater(r["total"], aovivo.POR_GRUPO)

    def test_acervo_restrito_nao_aparece_para_quem_nao_pode(self):
        self.db.execute("UPDATE biblioteca SET restrita = 1 WHERE code = 'motivacao_handebol'")
        self.db.conn.commit()
        self.assertFalse(any(a["code"] == "motivacao_handebol" for a in aovivo.buscar(self.db, "handebol")["acervos"]))
        self.assertTrue(any(a["code"] == "motivacao_handebol"
                            for a in aovivo.buscar(self.db, "handebol", perfil="coordenacao")["acervos"]))


class TestOBuscadorPelaRede(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "r.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        linhas.instalar(db)
        biblioteca.instalar(db)
        auth.create_account(db, "Leitora", "leitora@udesc.br", "senhaforte123", role="leitura")
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
            data=json.dumps({"login": "leitora@udesc.br", "senha": "senhaforte123"}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return (r.headers.get("Set-Cookie") or "").split(";")[0]

    def test_a_rota_responde_com_os_grupos(self):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/buscar?q=handebol",
                                        headers={"Cookie": self.entrar()})
        with urllib.request.urlopen(pedido, timeout=30) as r:
            corpo = json.loads(r.read())
        self.assertEqual(corpo["q"], "handebol")
        for grupo in ("artigos", "pessoas", "projetos", "linhas", "acervos", "temas"):
            self.assertIn(grupo, corpo)
        self.assertTrue(corpo["acervos"])

    def test_sem_login_e_recusado(self):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/api/buscar?q=handebol", timeout=30)
        except urllib.error.HTTPError as exc:
            self.assertIn(exc.code, (401, 403))
        else:
            self.fail("respondeu sem login")


class TestATelaDasPaginasNovas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.js = (TEMPLATES / "aovivo.js").read_text(encoding="utf-8")
        cls.html = (TEMPLATES / "aovivo.html").read_text(encoding="utf-8")
        cls.painel_js = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
        cls.painel_html = (TEMPLATES / "dashboard.html").read_text(encoding="utf-8")
        cls.mural = (TEMPLATES / "mural.html").read_text(encoding="utf-8")

    def test_as_quatro_paginas_novas_estao_no_menu_e_sao_desenhadas(self):
        for aba, fn in (("temas", "desenharTemas"), ("sinais", "desenharSinais"), ("mundo", "desenharMundo"), ("busca", "desenharBusca")):
            with self.subTest(aba=aba):
                self.assertIn(f'["{aba}", ', self.js)
                self.assertIn(f'ST.aba === "{aba}"', self.js)
                self.assertIn(f"function {fn}(", self.js)

    def test_o_globo_e_canvas_gira_e_para_quando_ninguem_ve(self):
        corpo = self.js[self.js.index("Globo.prototype.laco"):]
        self.assertIn("document.hidden", corpo[:400])
        self.assertIn('el("canvas"', self.js)
        self.assertIn("requestAnimationFrame(this.laco.bind(this))", self.js)
        # sai da página: o laço para
        self.assertIn('if (ST.aba !== "mundo") pararGlobo();', self.js)
        self.assertIn("__BANDEIRAS_JS__", self.html)

    def test_cada_analise_tem_botao_tematico_com_icone_existente(self):
        import re
        icones = (TEMPLATES / "icons.js").read_text(encoding="utf-8")
        trecho = self.js[self.js.index("const ANALISES = ["):]
        trecho = trecho[:trecho.index("];")]
        nomes = re.findall(r'^  \["([a-z]+)", "[^"]+", "([a-z]+)"', trecho, re.M)
        self.assertGreaterEqual(len(nomes), 7)
        for code, icone in nomes:
            with self.subTest(analise=code):
                self.assertIn(f"{icone}:", icones)
                self.assertIn(f'case "{code}":', self.js)
        self.assertIn("AUTO_ANALISE_SEGUNDOS", self.js)
        self.assertIn('text: "Rodar ▶"', self.js)

    def test_a_caixa_de_apresentacao_explica_mais_e_pausa_no_ponteiro(self):
        self.assertIn("const EXPLICA = {", self.js)
        self.assertIn('class: "mais"', self.js)
        self.assertIn("caixa.onmouseenter", self.js)
        self.assertIn("if (!ST.pausada) decorrido += agora - ultimo;", self.js)
        self.assertIn(".apresentacao::before", self.html)
        self.assertIn("conic-gradient(from var(--ang, 0deg)", self.html)
        self.assertIn("animation: contorno-gira 2.4s ease-out 1;", self.html)
        import re
        bloco = self.js[self.js.index("const ABAS = ["):]
        bloco = bloco[:bloco.index("];")]
        abas = re.findall(r'^  \["([a-z]+)", "', bloco, re.M)
        trecho = self.js[self.js.index("const EXPLICA = {"):]
        trecho = trecho[:trecho.index("};")]
        for aba in abas:
            with self.subTest(aba=aba):
                self.assertIn(f"  {aba}: [", trecho)

    def test_o_buscador_do_painel_pergunta_ao_servidor_e_le_o_endereco(self):
        self.assertIn('fetch("/api/buscar?q="', self.painel_js)
        self.assertIn("function montarBuscador()", self.painel_js)
        self.assertIn("function recortesDoEndereco()", self.painel_js)
        self.assertIn('if (p.get("q")) STATE.busca', self.painel_js)
        self.assertIn(".omni-lista", self.painel_html)
        # o ao vivo aponta para o painel com o recorte no endereço
        self.assertIn('"/?q=" + q', self.js)

    def test_o_mural_tambem_ganhou_o_contorno(self):
        self.assertIn(":root[data-paleta] .mtopo .titulo .apresenta", self.mural)


if __name__ == "__main__":
    unittest.main()
