#!/usr/bin/env python3
"""Testes do painel analítico: rota, exportação e a página.

    python3 -m unittest tests.test_panorama -v

O perigo aqui é o painel bonito que mente. Um gráfico que recebe o campo
com o nome errado não dá erro — ele desenha vazio, e ninguém percebe que
a rede temática está sem uma única linha. Foi o que aconteceu.
"""
from __future__ import annotations

import io
import json
import re
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

from lape import api, auth, ingest_excel, variaveis  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class BasePanorama(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "t.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        ingest_excel.ingest_articles(db, [
            {"title": "Treinamento resistido e ansiedade em fibromialgia",
             "authors": "Ana Souza; Beto Lima", "status": "Publicado",
             "year_published": 2024, "journal": "Pain", "doi": "10.1000/a.1"},
            {"title": "Dropout no treinamento resistido", "authors": "Ana Souza",
             "status": "Submetido", "first_submission_on": "2025-02-01"},
            {"title": "Um título sem variável nenhuma do vocabulário",
             "authors": "Beto Lima", "status": "Em produção", "started_on": "2023-05-01"},
        ])
        auth.create_account(db, "Ana Souza", "ana@udesc.br", "senhaforte123", role="admin")
        auth.create_account(db, "Curioso Silva", "curioso@udesc.br", "senhaforte123",
                            role="leitura")
        variaveis.instalar(db)
        variaveis.marcar_artigos(db)
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
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return r.headers.get("Set-Cookie", "").split(";")[0]

    def buscar(self, caminho, cookie=None, cru=False):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}{caminho}")
        if cookie:
            pedido.add_header("Cookie", cookie)
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                bruto = r.read()
                return r.status, r.headers, (bruto if cru else json.loads(bruto or b"{}"))
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, {}


class TestRotaDoPanorama(BasePanorama):
    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")
        self.curioso = self.entrar("curioso@udesc.br")

    def test_sem_entrar_nao_ve(self):
        self.assertEqual(self.buscar("/api/panorama")[0], 401)

    def test_quem_so_le_ve(self):
        # o panorama da produção é do laboratório inteiro
        self.assertEqual(self.buscar("/api/panorama", self.curioso)[0], 200)

    def test_traz_tudo_o_que_a_tela_precisa(self):
        _, _, dados = self.buscar("/api/panorama", self.ana)
        for chave in ("panorama", "sintese", "lacunas", "artigos", "linhas",
                      "laboratorio", "vocabulario"):
            self.assertIn(chave, dados)
        self.assertEqual(len(dados["artigos"]), 3)

    def test_cada_artigo_chega_com_as_suas_variaveis(self):
        _, _, dados = self.buscar("/api/panorama", self.ana)
        com_var = [a for a in dados["artigos"] if a["variaveis"]]
        self.assertEqual(len(com_var), 2)
        codigos = {v["code"] for v in com_var[0]["variaveis"]}
        self.assertTrue(codigos)

    def test_cada_variavel_diz_se_e_principal(self):
        # sem esse campo a tela não tem como destacar nada: todo selo
        # sairia igual, e "o artigo é sobre" viraria "o artigo cita"
        _, _, dados = self.buscar("/api/panorama", self.ana)
        for artigo in dados["artigos"]:
            for v in artigo["variaveis"]:
                with self.subTest(code=v["code"]):
                    self.assertIn(v["principal"], (0, 1))
                    self.assertIn("onde", v)

    def test_as_abas_novas_chegam_com_o_painel(self):
        # cada uma dessas abas precisaria de uma viagem própria se não
        # viesse aqui, e a tela abriria vazia por um instante
        _, _, dados = self.buscar("/api/panorama", self.ana)
        for chave in ("incidencia", "prevalencia", "triangulacao", "projetos"):
            with self.subTest(chave=chave):
                self.assertIn(chave, dados)

    def test_a_janela_pode_ser_apertada_pela_consulta(self):
        _, _, dados = self.buscar("/api/panorama?desde=2023&ate=2025", self.ana)
        self.assertEqual(dados["panorama"]["janela"]["anos"], [2023, 2024, 2025])

    def test_a_sintese_nao_afirma_tendencia_sem_serie(self):
        # três artigos em três anos diferentes, mas cada variável aparece
        # em poucos: nada aqui pode virar "subindo" com confiança
        _, _, dados = self.buscar("/api/panorama", self.ana)
        for v in dados["panorama"]["variaveis"]:
            if not v["confiavel"]:
                self.assertEqual(v["tendencia"], "sem série suficiente")
                self.assertIsNotNone(v["porque"])


class TestMapaMundiServido(BasePanorama):
    """O contorno do mundo é servido à parte da página, e guardado."""

    def test_o_contorno_sai_sem_login(self):
        # é geografia, não é dado do laboratório
        status, cab, corpo = self.buscar("/api/geo/mundo.json", cru=True)
        self.assertEqual(status, 200)
        self.assertIn("application/json", cab.get("Content-Type", ""))
        self.assertGreater(len(json.loads(corpo)["paises"]), 120)

    def test_o_contorno_e_guardado_pelo_navegador(self):
        # 70 KB que nunca mudam; sem cache, viajam a cada visita à aba
        _, cab, _ = self.buscar("/api/geo/mundo.json", cru=True)
        self.assertIn("max-age", cab.get("Cache-Control", ""))

    def test_o_contorno_nao_e_reserializado(self):
        # a regra era "o tipo é application/json, então serialize": um
        # JSON já pronto em disco só passava mentindo o tipo, ou inchado
        # com indentação a cada visita
        _, _, corpo = self.buscar("/api/geo/mundo.json", cru=True)
        self.assertNotIn(b'\n  ', corpo[:400])


class TestProducaoDasBases(BasePanorama):
    """O botão que traz a produção sem ninguém abrir um terminal."""

    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")
        self.curioso = self.entrar("curioso@udesc.br")

    def test_a_lista_de_quem_trazer_esta_na_rota(self):
        _, _, dados = self.buscar("/api/producao", self.ana)
        nomes = {p["nome"] for p in dados["pesquisadores"]}
        self.assertIn("Alexandro Andrade", nomes)
        self.assertIn("Guilherme Torres Vilarino", nomes)

    def test_o_link_do_lattes_vem_pronto(self):
        # o selo na tela vira o caminho para conferir se é a pessoa certa
        _, _, dados = self.buscar("/api/producao", self.ana)
        andrade = next(p for p in dados["pesquisadores"]
                       if p["nome"] == "Alexandro Andrade")
        self.assertEqual(andrade["link_lattes"],
                         "http://lattes.cnpq.br/5577164706111568")

    def test_o_painel_ja_chega_com_ela(self):
        # sem isso a aba precisaria de uma segunda viagem só para o botão
        _, _, dados = self.buscar("/api/panorama", self.ana)
        self.assertIn("producao", dados)
        self.assertIn("usuario", dados)

    def test_quem_so_le_nao_ve_botao_que_grava(self):
        # o botão que devolve 403 é pior que botão nenhum
        _, _, dados = self.buscar("/api/panorama", self.curioso)
        self.assertEqual(dados["usuario"]["papel"], "leitura")

    def test_importar_e_da_coordenacao(self):
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/producao/importar",
            data=b"{}", headers={"Content-Type": "application/json",
                                 "Cookie": self.curioso}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as caso:
            urllib.request.urlopen(pedido, timeout=30)
        self.assertEqual(caso.exception.code, 403)


class TestExportacaoDaExtracao(BasePanorama):
    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")

    def test_o_csv_abre_no_excel_em_portugues(self):
        status, cab, corpo = self.buscar("/api/panorama/extracao.csv", self.ana, cru=True)
        self.assertEqual(status, 200)
        self.assertIn("text/csv", cab.get("Content-Type", ""))
        texto = corpo.decode("utf-8")
        self.assertTrue(texto.startswith("﻿"))
        cabecalho = texto.splitlines()[0].lstrip("﻿")
        self.assertIn("Variáveis", cabecalho)
        self.assertIn("Nº de variáveis", cabecalho)

    def test_o_csv_separa_principal_de_secundaria(self):
        # quem filtra a planilha por assunto quer os artigos que SÃO
        # sobre o assunto, não os que o mencionam de passagem
        _, _, corpo = self.buscar("/api/panorama/extracao.csv", self.ana, cru=True)
        linhas = corpo.decode("utf-8").lstrip("\ufeff").splitlines()
        cabecalho = linhas[0].split(";")
        self.assertIn("Variáveis principais", cabecalho)
        self.assertIn("Variáveis secundárias", cabecalho)
        coluna = cabecalho.index("Variáveis principais")
        principais = [l.split(";")[coluna] for l in linhas[1:]]
        self.assertTrue(any(p.strip('"') for p in principais),
                        "nenhum artigo saiu com variável principal")

    def test_o_csv_traz_as_variaveis_escritas(self):
        _, _, corpo = self.buscar("/api/panorama/extracao.csv", self.ana, cru=True)
        self.assertIn("Fibromialgia", corpo.decode("utf-8"))

    def test_o_xlsx_tem_as_duas_abas(self):
        # a segunda não é recorte por comodidade: é a tabela que responde
        # "como estes assuntos se relacionam", que a primeira não responde
        status, cab, corpo = self.buscar("/api/panorama/extracao.xlsx", self.ana, cru=True)
        self.assertEqual(status, 200)
        self.assertIn("spreadsheetml", cab.get("Content-Type", ""))
        self.assertTrue(corpo.startswith(b"PK"))
        from openpyxl import load_workbook
        livro = load_workbook(io.BytesIO(corpo))
        self.assertEqual(livro.sheetnames, ["Todos os artigos", "Mais de uma variável"])
        todos = livro["Todos os artigos"]
        multi = livro["Mais de uma variável"]
        self.assertEqual(todos.max_row - 1, 3)
        self.assertLess(multi.max_row, todos.max_row)

    def test_o_link_do_artigo_vira_link_na_planilha(self):
        _, _, corpo = self.buscar("/api/panorama/extracao.xlsx", self.ana, cru=True)
        from openpyxl import load_workbook
        aba = load_workbook(io.BytesIO(corpo))["Todos os artigos"]
        colunas = [c.value for c in aba[1]]
        coluna = colunas.index("Link") + 1
        links = [aba.cell(row=i, column=coluna).hyperlink
                 for i in range(2, aba.max_row + 1)]
        self.assertTrue(any(links), "nenhuma célula de link virou hyperlink")

    def test_sem_entrar_nao_baixa(self):
        self.assertEqual(self.buscar("/api/panorama/extracao.csv")[0], 401)


class TestPaginaDoPanorama(BasePanorama):
    def pagina(self):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}/panorama")
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return r.read().decode("utf-8")

    def test_a_pagina_monta_inteira(self):
        html = self.pagina()
        for marcador in ("__BASE_CSS__", "__ICONS_JS__", "__CHARTS_JS__", "__PANORAMA_JS__"):
            self.assertNotIn(marcador, html, f"marcador não substituído: {marcador}")
        self.assertIn("const Charts", html)
        self.assertIn("const ABAS", html)

    def test_a_pagina_diz_qual_versao_esta_no_ar(self):
        # sem isso "atualizou?" só se responde abrindo um terminal, e
        # quem está no computador do laboratório não vai abrir
        html = self.pagina()
        self.assertIn('class="marca-versao"', html)
        self.assertLess(html.index('class="marca-versao"'), html.index("</body>"))

    def test_a_biblioteca_de_graficos_esta_ligada(self):
        # `C` não definido derrubava todo gráfico da tela, e a página
        # continuava de pé: cartões vazios, nenhum erro visível
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        self.assertIn("const C = Charts;", js)

    def test_a_rede_usa_o_campo_que_a_biblioteca_le(self):
        # com `value` em vez de `weight`, o cálculo de posição recebia
        # undefined, virava NaN, e a rede saía sem uma única linha
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        trecho = js[js.index("C.network({"):js.index("height: 440")]
        self.assertIn("weight:", trecho)
        self.assertNotIn("value:", trecho)

    def test_a_aba_do_ponto_so_aparece_para_quem_pode_abri_la(self):
        # aba que responde 403 é pior que aba nenhuma: promete e nega
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        corpo = js[js.index("function abasVisiveis"):]
        corpo = corpo[:corpo.index("\n}")]
        self.assertIn("coordenacao", corpo)
        self.assertIn("equipe", corpo)
        montar = js[js.index("function montarNav"):js.index("function contaDaAba")
                    if "function contaDaAba" in js else js.index("function montarNav") + 2000]
        self.assertIn("abasVisiveis()", montar)

    def test_toda_aba_declarada_tem_funcao(self):
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        bloco = js[js.index("const ABAS = ["):js.index("];", js.index("const ABAS = ["))]
        ids = re.findall(r'id: "(\w+)"', bloco)
        self.assertGreaterEqual(len(ids), 8)
        despacho = js[js.index("({ visao: verVisao"):js.index("[ST.aba] || verVisao)")]
        for identificador in ids:
            with self.subTest(aba=identificador):
                self.assertIn(identificador + ":", despacho)

    def test_todo_icone_da_navegacao_existe(self):
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        icones = (TEMPLATES / "icons.js").read_text(encoding="utf-8")
        for nome in re.findall(r'icone: "(\w+)"', js):
            with self.subTest(icone=nome):
                self.assertIn(f"{nome}:", icones)

    def test_nenhum_token_de_tema_indefinido(self):
        tema = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
        definidos = set(re.findall(r"(--[a-z0-9-]+)\s*:", tema))
        pagina = (TEMPLATES / "panorama.html").read_text(encoding="utf-8")
        definidos |= set(re.findall(r"(--[a-z0-9-]+)\s*:", pagina))
        usados = set(re.findall(r"var\((--[a-z0-9-]+)", pagina))
        self.assertEqual(usados - definidos, set())


class TestPecasNovasDaTela(unittest.TestCase):
    """Marcas na curva, tempo real e o mapa-múndi."""

    def js(self, nome):
        return (TEMPLATES / nome).read_text(encoding="utf-8")

    def test_a_biblioteca_desenha_marca_sobre_a_linha(self):
        # o ponto de inflexão só significa algo em cima da curva que o
        # gerou; numa tabela ao lado, é um número
        graficos = self.js("charts.js")
        trecho = graficos[graficos.index("(spec.marks || [])"):]
        trecho = trecho[:trecho.index("/* uma dica por X")]
        self.assertIn("svg.appendChild(g)", trecho)
        self.assertIn("stroke-dasharray", trecho)

    def test_a_marca_vai_depois_das_series(self):
        # marca escondida atrás de uma linha não marca nada
        graficos = self.js("charts.js")
        self.assertLess(graficos.index("serieSpec.values.forEach"),
                        graficos.index("(spec.marks || [])"))

    def test_o_panorama_marca_as_inflexoes_no_grafico(self):
        js = self.js("panorama.js")
        self.assertIn("marks: marcas", js)
        self.assertIn("inflexoes", js[js.index("const marcas = []"):js.index("marks: marcas")])

    def test_o_titulo_leva_a_editora_e_nao_a_copia(self):
        # "leva direto para o site onde foi publicado" é o DOI, que
        # resolve para a editora. O texto livre é outra coisa -- uma
        # cópia -- e fica no botão ao lado, não no título
        js = self.js("panorama.js")
        corpo = js[js.index("function destinoDoTitulo"):]
        corpo = corpo[:corpo.index("\n}")]
        self.assertIn("d.editora", corpo)
        editora = js[js.index("function destinosDoArtigo"):js.index("function destinoDoTitulo")]
        # só o DOI e a página própria do artigo são "editora"
        self.assertEqual(editora.count("editora: true"), 2)
        pmc = editora[editora.index('chave: "pmc"'):]
        self.assertNotIn("editora", pmc[:pmc.index('chave: "pubmed"')])

    def test_toda_base_pedida_tem_botao(self):
        js = self.js("panorama.js")
        editora = js[js.index("function destinosDoArtigo"):js.index("function destinoDoTitulo")]
        for base in ("DOI", "PMC", "PubMed", "Scopus", "Web of Science"):
            with self.subTest(base=base):
                self.assertIn('rotulo: "' + base + '"', editora)

    def test_a_busca_nao_se_disfarca_de_artigo(self):
        # prometer "abre o artigo" e cair numa lista de resultados é pior
        # que avisar antes: sem o id da base não há link direto
        js = self.js("panorama.js")
        editora = js[js.index("function destinosDoArtigo"):js.index("function destinoDoTitulo")]
        self.assertIn("busca: true", editora)
        css = (TEMPLATES / "panorama.html").read_text(encoding="utf-8")
        self.assertIn(".base.busca", css)
        self.assertIn("border-style: dashed", css[css.index(".base.busca"):][:200])

    def test_o_texto_livre_nao_e_so_uma_cor(self):
        css = (TEMPLATES / "panorama.html").read_text(encoding="utf-8")
        self.assertIn(".base.livre", css)
        js = self.js("panorama.js")
        self.assertIn('rotulo: "PMC"', js)   # o rótulo diz qual base é

    def test_o_titulo_e_clicavel_fora_da_tabela_tambem(self):
        # linha do tempo e organograma mostram título; clicar neles tem
        # de levar ao artigo como na tabela
        js = self.js("panorama.js")
        self.assertGreaterEqual(js.count("tituloClicavel("), 3)
        corpo = js[js.index("function tituloClicavel"):]
        corpo = corpo[:corpo.index("\n}")]
        self.assertIn("destino.busca", corpo)
        self.assertIn("stopPropagation", corpo)

    def test_o_selo_da_variavel_principal_se_distingue(self):
        # se o destaque fosse só cor, quem imprime em preto e branco ou
        # não separa bem as cores lê a tabela toda como se fosse igual
        css = (TEMPLATES / "panorama.html").read_text(encoding="utf-8")
        self.assertIn(".selo-var.principal", css)
        self.assertIn(".selo-var.principal::before", css)
        self.assertIn(".selo-var.secundaria", css)

    def test_a_tela_usa_o_campo_principal_que_a_rota_manda(self):
        js = self.js("panorama.js")
        trecho = js[js.index("function pesoDaVariavel"):js.index("function seloVariavel")]
        self.assertIn("v.principal", trecho)
        self.assertIn("principal", js[js.index("function seloVariavel"):][:900])

    def test_o_destaque_vem_com_legenda(self):
        # marca sem legenda é enfeite: ninguém sabe o que ela afirma
        js = self.js("panorama.js")
        self.assertIn("legendaDosSelos()", js)
        legenda = js[js.index("function legendaDosSelos"):]
        legenda = legenda[:legenda.index("\n}")]
        self.assertIn("principal", legenda)
        self.assertIn("secundária", legenda.lower())

    def test_a_cor_nao_e_ciclada_entre_as_variaveis(self):
        # o defeito que este teste guarda: 8 cores para 23 variáveis,
        # cicladas pelo índice — "Exercício" e "Saúde mental" saíram as
        # duas verdes no mesmo gráfico, e a legenda não ajudava
        js = self.js("panorama.js")
        corpo = js[js.index("function montarCores()"):js.index("function corDaVariavel")]
        self.assertIn("i < 8", corpo)
        self.assertIn("--ink-muted", corpo)
        self.assertNotIn("% 8", corpo)

    def test_o_tempo_real_usa_a_mesma_conexao_do_painel(self):
        js = self.js("panorama.js")
        self.assertIn('new EventSource("/api/stream")', js)
        self.assertIn('addEventListener("mudanca"', js)

    def test_a_rajada_de_eventos_vira_uma_recarga_so(self):
        # numa importação de planilha chegam dezenas de eventos; recarregar
        # a cada um faria o painel recalcular tudo dezenas de vezes
        js = self.js("panorama.js")
        trecho = js[js.index('addEventListener("mudanca"'):js.index("function desligarAoVivo")]
        self.assertIn("clearTimeout(recargaMarcada)", trecho)
        self.assertIn("setTimeout(recarregar", trecho)

    def test_a_recarga_preserva_onde_a_pessoa_estava(self):
        # painel que salta para o topo a cada mudança é painel que ninguém
        # consegue ler enquanto a equipe trabalha
        js = self.js("panorama.js")
        corpo = js[js.index("async function recarregar()"):js.index("function marcarPulso")]
        self.assertIn("window.scrollY", corpo)
        self.assertIn("window.scrollTo", corpo)

    def test_o_mapa_mundi_enquadra_o_planeta(self):
        # `geo` enquadra os pontos: cinco países espalhados viram cinco
        # bolhas soltas num plano, e some o que o mapa existe para dar
        graficos = self.js("charts.js")
        corpo = graficos[graficos.index("function mapaMundi(spec)"):]
        corpo = corpo[:corpo.index("\n  }\n")]
        self.assertIn("LON0 = -180", corpo)
        self.assertIn("LON1 = 180", corpo)

    def test_o_contorno_do_mundo_e_de_verdade(self):
        # antes eram dez manchas desenhadas à mão. Continente irreconhecível
        # com bolhas espetadas em cima não diz de onde vem a produção
        mundo = json.loads((ROOT / "data" / "geo" / "mundo.json")
                           .read_text(encoding="utf-8"))["paises"]
        self.assertGreater(len(mundo), 120, "poucos países para um mapa-múndi")
        pontos = 0
        for pais in mundo:
            self.assertTrue(pais["id"] and pais["nome"], pais)
            for anel in pais["d"]:
                self.assertGreaterEqual(len(anel), 4, f"anel degenerado em {pais['nome']}")
                for lon, lat in anel:
                    self.assertTrue(-180 <= lon <= 180, f"{pais['nome']}: longitude {lon}")
                    self.assertTrue(-90 <= lat <= 90, f"{pais['nome']}: latitude {lat}")
                pontos += len(anel)
        self.assertGreater(pontos, 3000, "contorno pobre demais para reconhecer o mundo")

    def test_todo_pais_esperado_esta_no_contorno(self):
        # apaguei a África sem querer ao trocar a Eurásia, e o mapa seguiu
        # desenhando sem reclamar de nada
        mundo = json.loads((ROOT / "data" / "geo" / "mundo.json")
                           .read_text(encoding="utf-8"))["paises"]
        nomes = {p["nome"] for p in mundo}
        for pais in ("Brasil", "Portugal", "Estados Unidos", "Espanha", "Austrália",
                     "China", "Reino Unido", "Noruega", "Canadá", "Nigéria",
                     "Índia", "Nova Zelândia"):
            with self.subTest(pais=pais):
                self.assertIn(pais, nomes)

    def test_o_contorno_cabe_numa_visita(self):
        # é servido à parte da página e guardado pelo navegador; ainda
        # assim, meio megabyte de litoral por causa de cinco países seria
        # pagar caro por detalhe que ninguém vê
        tamanho = (ROOT / "data" / "geo" / "mundo.json").stat().st_size
        self.assertLess(tamanho, 200 * 1024, "contorno pesado demais")

    def test_a_cor_do_pais_e_o_valor(self):
        # bolha espetada em cima do país não é escala: o coroplético diz
        # magnitude com um tom só, do claro ao escuro
        graficos = self.js("charts.js")
        corpo = graficos[graficos.index("function mapaMundi(spec)"):]
        corpo = corpo[:corpo.index("\n  }\n")]
        self.assertIn("PASSOS_MAPA", corpo)
        self.assertNotIn("serie(", corpo, "cor de série é identidade, não magnitude")
        passos = graficos[graficos.index("const PASSOS_MAPA"):]
        passos = passos[:passos.index("\n")]
        self.assertNotIn("--series-", passos, "a escala tem de sair da rampa sequencial")

    def test_a_escala_do_mapa_vem_com_legenda(self):
        graficos = self.js("charts.js")
        self.assertIn("legendaDoMapa", graficos)
        self.assertIn("sem registro", graficos)

    def test_o_mapa_esta_exposto_pela_biblioteca(self):
        graficos = self.js("charts.js")
        self.assertIn("mapaMundi: mapaMundi", graficos)
        self.assertIn("C.mapaMundi(", self.js("panorama.js"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
