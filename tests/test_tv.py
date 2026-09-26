#!/usr/bin/env python3
"""A TV: mais informação no mural e no ao vivo que fica passando na parede.

    python3 -m unittest tests.test_tv -v

O que se guarda:

1. `tv.para_a_tv` junta, numa chamada só, o que as telas da parede
   acrescentam: temas, ritmo, mundo, acervos, rotina e notícias -- e nada
   ali é texto de modelo: cada número sai do banco;
2. as notícias saem na ordem do tempo e com a data: "Publicado" sem data
   seria manchete velha passando por nova;
3. a rota `/api/tv` responde protegida como o painel, e o mural leva `tv`
   embutido -- e sobe sem ela se ela falhar;
4. o mural tem as quatro telas novas, e elas só entram no ciclo quando o
   dado chegou; a fita e a cotação ganham o que só a TV tem;
5. o ao vivo em `?tv=1` entra apresentando e no automático, sem menu, com
   a faixa do relógio e das notícias, os fatos de cada página na caixa e
   o tempo de cada página -- o cálculo roda as suas análises.
"""
from __future__ import annotations

import json
import re
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

from lape import api, auth, biblioteca, linhas, report, tv  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
HOJE = date(2026, 9, 22)


def _abrir(caminho: Path) -> Database:
    db = Database(caminho)
    db.migrate()
    return db


def _artigo(db: Database, titulo: str, **campos) -> int:
    dados = {"title": titulo, "title_key": titulo.lower(), "status": "publicado"}
    dados.update(campos)
    return db.upsert("articles", dados, conflict=("title_key",))


class BaseDaTv(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = _abrir(Path(self.tmp.name) / "tv.sqlite")
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.db.close)
        linhas.instalar(self.db)
        biblioteca.instalar(self.db)
        _artigo(self.db, "Publicado em agosto", published_on="2026-08-10", year_published=2026,
                journal="Revista A", open_access=1, started_on="2025-01-10")
        _artigo(self.db, "Publicado em maio", published_on="2026-05-03", year_published=2026,
                journal="Revista B", started_on="2025-06-01")
        _artigo(self.db, "Publicado só com o ano", year_published=2024, journal="Revista A")
        _artigo(self.db, "Aceito em julho", status="aceito", accepted_on="2026-07-01", journal="Revista C")
        sub = _artigo(self.db, "Submetido em junho", status="submetido", journal="Revista D")
        self.db.execute(
            "INSERT INTO submissions (article_id, attempt_no, journal, decision, submitted_on)"
            " VALUES (?, 1, 'Revista D', 'em_avaliacao', '2026-06-15')", (sub,))
        for titulo, kind, quando in (("Defesa amanhã", "defesa", "2026-09-23 14:00"),
                                     ("Reunião de ontem", "reuniao", "2026-09-21 10:00"),
                                     ("Curso no mês que vem", "curso", "2026-10-10")):
            self.db.execute(
                "INSERT INTO events (external_key, kind, title, start_at, all_day, status)"
                " VALUES (?, ?, ?, ?, 0, 'confirmado')", (titulo.lower(), kind, titulo, quando))
        self.db.conn.commit()


class TestOQueATvJunta(BaseDaTv):

    def test_traz_as_seis_partes_e_o_periodo_do_ano(self):
        d = tv.para_a_tv(self.db, HOJE)
        for chave in ("periodo", "temas", "mundo", "sinais", "acervos", "rotina", "noticias", "gerado_em"):
            with self.subTest(parte=chave):
                self.assertIn(chave, d)
        self.assertEqual(d["periodo"]["ate"], 2026)
        self.assertEqual(d["periodo"]["code"], "ano")

    def test_os_kpis_tematicos_sao_os_do_ao_vivo(self):
        codes = [k["code"] for k in tv.para_a_tv(self.db, HOJE)["temas"]["kpis"]]
        for code in ("tempo", "aceite", "acesso_aberto", "internacional", "revistas", "paises"):
            self.assertIn(code, codes)
        revistas = tv.para_a_tv(self.db, HOJE)["temas"]["revistas"]
        self.assertTrue(all("label" in r and "value" in r for r in revistas))

    def test_o_ritmo_traz_a_curva_curta_com_tendencia_faixa_e_projecao(self):
        s = tv.para_a_tv(self.db, HOJE)["sinais"]
        self.assertLessEqual(len(s["labels"]), tv.MESES_NA_TV)
        self.assertEqual(len(s["labels"]), len(s["valores"]))
        self.assertEqual(len(s["labels"]), len(s["tendencia"]))
        self.assertEqual(len(s["labels"]), len(s["tendencia_alto"]))
        self.assertEqual(len(s["labels"]), len(s["tendencia_baixo"]))
        self.assertIn("projecao", s)
        self.assertIn("ritmo", s)
        self.assertIn("deriva_ano", s)
        self.assertLessEqual(len(s["leituras"]), tv.LEITURAS_NA_TV)
        # a faixa nunca fica abaixo da tendência nem acima dela invertida
        for alto, meio, baixo in zip(s["tendencia_alto"], s["tendencia"], s["tendencia_baixo"]):
            self.assertGreaterEqual(alto, meio)
            self.assertLessEqual(baixo, meio)

    def test_os_acervos_sao_so_os_abertos_e_vem_com_tamanho_e_segmentos(self):
        acervos = tv.para_a_tv(self.db, HOJE)["acervos"]
        self.assertEqual(len(acervos), len(biblioteca.BIBLIOTECAS))
        for a in acervos:
            with self.subTest(acervo=a["code"]):
                for chave in ("title", "total", "segmentos", "bases_ok", "bases", "rodada_em"):
                    self.assertIn(chave, a)
                self.assertGreater(a["segmentos"], 0)
        # um acervo restrito não vai para a parede
        self.db.execute("UPDATE biblioteca SET restrita = 1 WHERE code = ?", (acervos[0]["code"],))
        self.db.conn.commit()
        depois = tv.para_a_tv(self.db, HOJE)["acervos"]
        self.assertEqual(len(depois), len(biblioteca.BIBLIOTECAS) - 1)
        self.assertNotIn(acervos[0]["code"], [a["code"] for a in depois])

    def test_o_mundo_traz_os_paises_ordenados_e_a_sede(self):
        m = tv.para_a_tv(self.db, HOJE)["mundo"]
        self.assertIn("sede", m)
        self.assertLessEqual(len(m["paises"]), tv.PAISES_NA_TV)
        ns = [p["n"] for p in m["paises"]]
        self.assertEqual(ns, sorted(ns, reverse=True))
        for chave in ("n_paises", "n_fora_do_brasil", "artigos_com_pais", "instituicoes"):
            self.assertIn(chave, m)

    def test_a_rotina_e_a_situacao_dos_cinco_passos(self):
        r = tv.para_a_tv(self.db, HOJE)["rotina"]
        self.assertEqual([p["passo"] for p in r["passos"]],
                         ["producao", "citacoes", "acervos", "descobrir", "perfis"])
        self.assertIn("ligada", r)


class TestLinhasDePesquisaParaOMural(BaseDaTv):
    """`_linhas_pesquisa` alimenta a lâmina "Linhas de Pesquisa 3D" do
    mural -- publicados e citações são as duas informações que a lâmina
    passou a mostrar por linha (antes só tinha total de artigos e taxa)."""

    def _linha(self, code, name):
        self.db.execute(
            "INSERT INTO research_lines (code, name, active) VALUES (?, ?, 1)", (code, name))
        self.db.conn.commit()
        return self.db.scalar("SELECT id FROM research_lines WHERE code = ?", (code,))

    def test_traz_publicados_e_citacoes_por_linha(self):
        lid = self._linha("linha-teste", "Linha de Teste")
        _artigo(self.db, "Artigo publicado com citações", research_line_id=lid,
                status="publicado", openalex_citations=12)
        _artigo(self.db, "Artigo ainda em produção", research_line_id=lid,
                status="em_producao", openalex_citations=0)
        linha = next(l for l in tv._linhas_pesquisa(self.db) if l["id"] == lid)
        self.assertEqual(linha["artigos"], 2)
        self.assertEqual(linha["publicados"], 1)
        self.assertEqual(linha["citacoes"], 12)
        self.assertEqual(linha["em_producao"], 1)

    def test_em_producao_e_o_esforco_de_agora_nao_o_volume_historico(self):
        """A lâmina "Impacto x esforço" usa `em_producao` como o esforço
        ATUAL da linha -- uma linha com muitos artigos publicados ao
        longo dos anos mas nada em andamento agora não pode aparecer
        como "muito esforço" só por ter um histórico grande."""
        lid = self._linha("linha-historica", "Linha Histórica")
        for i in range(5):
            _artigo(self.db, f"Publicado antigo {i}", research_line_id=lid, status="publicado")
        linha = next(l for l in tv._linhas_pesquisa(self.db) if l["id"] == lid)
        self.assertEqual(linha["artigos"], 5)
        self.assertEqual(linha["em_producao"], 0)

    def test_linha_sem_nenhum_artigo_vem_zerada_nao_ausente(self):
        lid = self._linha("linha-vazia", "Linha Vazia")
        linha = next(l for l in tv._linhas_pesquisa(self.db) if l["id"] == lid)
        self.assertEqual(linha["artigos"], 0)
        self.assertEqual(linha["publicados"], 0)
        self.assertEqual(linha["citacoes"], 0)
        self.assertEqual(linha["taxa_publicacao"], 0)


class TestOrganogramaDaParedeSoQuemTemVinculo(BaseDaTv):
    """`_organograma_para_tv` -- achado ao vivo (print do Mateus): a parede
    mostrava também quem não tem `role` nenhum (coautor importado junto de
    artigo, nunca cadastrado como integrante de verdade) numa grade sem
    hierarquia, abafando a árvore de quem tem vínculo real. `organograma`
    e `organograma_publico` continuam mostrando todo mundo -- é a
    ferramenta da coordenação para achar cadastro incompleto -- só a
    versão que vai para a TV corta quem não tem vínculo."""

    def test_quem_nao_tem_vinculo_fica_de_fora_da_parede(self):
        self.db.member_id("Professora Com Vínculo", role="professor")
        self.db.member_id("Coautor Sem Vínculo")
        org = tv._organograma_para_tv(self.db)
        nomes = [p["full_name"] for p in org["people"]]
        self.assertIn("Professora Com Vínculo", nomes)
        self.assertNotIn("Coautor Sem Vínculo", nomes)

    def test_organograma_publico_continua_mostrando_todo_mundo(self):
        """A ferramenta da coordenação não perde o sinal de cadastro
        incompleto -- só a parede corta."""
        from lape import metrics

        self.db.member_id("Coautor Sem Vínculo")
        publico = metrics.organograma_publico(self.db)
        self.assertIn("Coautor Sem Vínculo", [p["full_name"] for p in publico["people"]])

    def test_atualiza_sozinho_conforme_o_cadastro_muda(self):
        """Não é lista fixa: dar um vínculo a alguém já cadastrado faz a
        pessoa entrar na próxima vez que a parede pedir o organograma."""
        mid = self.db.member_id("Vai Ganhar Vínculo")
        self.assertNotIn("Vai Ganhar Vínculo",
                        [p["full_name"] for p in tv._organograma_para_tv(self.db)["people"]])
        self.db.execute("UPDATE members SET role = 'bolsista_ic' WHERE id = ?", (mid,))
        self.db.conn.commit()
        self.assertIn("Vai Ganhar Vínculo",
                      [p["full_name"] for p in tv._organograma_para_tv(self.db)["people"]])


class TestAsNoticias(BaseDaTv):

    def test_publicados_do_mais_novo_para_o_mais_velho_e_o_sem_data_pelo_ano(self):
        n = tv.noticias(self.db, HOJE)
        self.assertEqual([p["titulo"] for p in n["publicados"]],
                         ["Publicado em agosto", "Publicado em maio", "Publicado só com o ano"])
        self.assertEqual(n["publicados"][0]["data"], "2026-08-10")
        self.assertIsNone(n["publicados"][2]["data"])
        self.assertEqual(n["publicados"][2]["ano"], 2024)

    def test_aceites_e_submissoes_com_a_data_e_a_revista(self):
        n = tv.noticias(self.db, HOJE)
        self.assertEqual(n["aceitos"][0]["titulo"], "Aceito em julho")
        self.assertEqual(n["aceitos"][0]["data"], "2026-07-01")
        self.assertEqual(n["submetidos"][0]["titulo"], "Submetido em junho")
        self.assertEqual(n["submetidos"][0]["data"], "2026-06-15")
        self.assertEqual(n["submetidos"][0]["revista"], "Revista D")

    def test_os_compromissos_sao_de_hoje_em_diante_na_ordem(self):
        n = tv.noticias(self.db, HOJE)
        self.assertEqual([e["titulo"] for e in n["eventos"]], ["Defesa amanhã", "Curso no mês que vem"])
        self.assertEqual(n["eventos"][0]["tipo"], "defesa")

    def test_o_limite_por_grupo_vale(self):
        for i in range(10):
            _artigo(self.db, f"Publicado {i}", published_on=f"2026-03-{i + 1:02d}", year_published=2026)
        self.db.conn.commit()
        self.assertEqual(len(tv.noticias(self.db, HOJE, n=3)["publicados"]), 3)
        self.assertEqual(len(tv.noticias(self.db, HOJE)["publicados"]), tv.NOTICIAS)

    def test_o_titulo_longo_e_cortado_para_a_faixa(self):
        _artigo(self.db, "T" * 300, published_on="2026-09-01", year_published=2026)
        self.db.conn.commit()
        titulo = tv.noticias(self.db, HOJE)["publicados"][0]["titulo"]
        self.assertLessEqual(len(titulo), 90)
        self.assertTrue(titulo.endswith("…"))

    def test_o_ao_vivo_leva_as_noticias(self):
        from lape import aovivo
        d = aovivo.montar(self.db, "ano", HOJE)
        self.assertIn("noticias", d)
        self.assertEqual(d["noticias"]["publicados"][0]["titulo"], "Publicado em agosto")


class _SemSeguirODesvio(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class TestARotaEOMural(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "api.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        linhas.instalar(db)
        biblioteca.instalar(db)
        _artigo(db, "Um publicado", published_on="2026-08-10", year_published=2026, journal="Revista A")
        db.conn.commit()
        auth.create_account(db, "Coordenação", "coord@udesc.br", "senhaforte123", role="admin")
        db.close()
        api.Handler.db_path = cls.db_path
        api.Handler.log_message = lambda *args, **kwargs: None
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api.Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def buscar(self, caminho, cookie=None, seguir=True):
        pedido = urllib.request.Request(f"http://127.0.0.1:{self.port}{caminho}")
        if cookie:
            pedido.add_header("Cookie", f"{api.COOKIE_NAME}={cookie}")
        abridor = (urllib.request.build_opener() if seguir
                   else urllib.request.build_opener(_SemSeguirODesvio))
        try:
            with abridor.open(pedido, timeout=30) as resposta:
                return resposta.status, resposta.read().decode(), resposta
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode(), exc

    def entrar(self):
        corpo = json.dumps({"login": "coord@udesc.br", "senha": "senhaforte123"}).encode()
        pedido = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login", data=corpo, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return (resposta.headers.get("Set-Cookie") or "").split("=")[1].split(";")[0]

    def test_a_rota_exige_sessao(self):
        status, _, _ = self.buscar("/api/tv", seguir=False)
        self.assertEqual(status, 401)

    def test_a_rota_responde_com_as_seis_partes(self):
        status, corpo, _ = self.buscar("/api/tv", cookie=self.entrar())
        self.assertEqual(status, 200)
        d = json.loads(corpo)
        for chave in ("temas", "mundo", "sinais", "acervos", "rotina", "noticias"):
            self.assertIn(chave, d)
        self.assertEqual(d["noticias"]["publicados"][0]["titulo"], "Um publicado")

    def test_o_mural_leva_a_tv_embutida(self):
        status, corpo, _ = self.buscar("/mural", cookie=self.entrar())
        self.assertEqual(status, 200)
        dado = corpo.split('<script id="payload" type="application/json">', 1)[1].split("</script>", 1)[0]
        payload = json.loads(dado)
        self.assertIn("tv", payload)
        self.assertEqual(payload["tv"]["noticias"]["publicados"][0]["titulo"], "Um publicado")

    def test_o_mural_sobe_sem_a_tv(self):
        """O mural exportado (ou a rota que falhou) não tem `tv`, e a tela
        precisa montar do mesmo jeito: as telas da TV saem do ciclo."""
        html = report.render_mural({"overview": {"lab_name": "LAPE"}, "articles": []})
        self.assertIn("const ROTEIRO", html)
        self.assertNotIn('"tv":', html.split("__DATA__")[0] if "__DATA__" in html else "")


class TestOMuralNaTv(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        cls.html = (TEMPLATES / "mural.html").read_text(encoding="utf-8")

    def slides(self):
        trecho = self.js[self.js.index("const SLIDES = ["):]
        return trecho[:trecho.index("];")]

    def test_as_quatro_telas_novas_estao_no_ciclo_e_apresentam(self):
        trecho = self.slides()
        for id_ in ("temas", "ritmo", "mundo", "acervos"):
            with self.subTest(tela=id_):
                self.assertIn(f'id: "{id_}"', trecho)
        # cada uma marcada como da TV, com a frase de apresentação
        self.assertEqual(trecho.count("tv: true"), 4)
        ids = re.findall(r'id: "([a-z]+)"', trecho)
        self.assertEqual(len(re.findall(r'apresenta: "', trecho)), len(ids))
        for nome in ("slideTemas", "slideRitmo", "slideMundo", "slideAcervos"):
            self.assertIn(f"function {nome}()", self.js)

    def test_sem_a_tv_as_telas_dela_saem_do_ciclo(self):
        trecho = self.js[self.js.index("function ciclo()"):self.js.index("const ROTEIRO")]
        self.assertIn("!s.tv || D.tv", trecho)

    def test_o_roteiro_e_refeito_quando_a_tv_chega(self):
        trecho = self.js[self.js.index("function rebuscar()"):]
        trecho = trecho[:trecho.index("\n}\n")]
        self.assertIn('pega("/api/tv")', trecho)
        self.assertIn("ROTEIRO.splice.apply(ROTEIRO, [0, ROTEIRO.length].concat(ciclo()))", trecho)
        # a TV que falha não derruba o painel: fica a última boa
        self.assertIn("return D.tv || null;", trecho)

    def test_a_fita_ganha_as_noticias_com_a_data(self):
        self.assertIn("noticiasDaTv().forEach", self.js)
        trecho = self.js[self.js.index("function noticiasDaTv()"):]
        trecho = trecho[:trecho.index("\n}\n")]
        self.assertIn('"Publicado: "', trecho)
        self.assertIn('"Aceito: "', trecho)
        self.assertIn('"Submetido: "', trecho)
        self.assertIn("dataCurta(a.data)", trecho)
        self.assertIn('"Rotina · "', trecho)

    def test_a_cotacao_ganha_paises_e_biblioteca_sem_seta(self):
        trecho = self.js[self.js.index("function cotacoes()"):self.js.index("function desenharCotacao()")]
        self.assertIn('sigla: "PAISES"', trecho)
        self.assertIn('sigla: "BIBLIO"', trecho)
        # sem segunda medição, sem seta: delta nulo, e a faixa diz "—"
        self.assertEqual(trecho.count("delta: null, base: \"\""), 2)

    def test_o_azulejo_aceita_texto_decimais_e_prefixo(self):
        trecho = self.js[self.js.index("function tile(spec)"):self.js.index("function quadro(")]
        self.assertIn('typeof spec.valor === "string"', trecho)
        self.assertIn("dataset.decimais", trecho)
        self.assertIn("dataset.prefixo", trecho)
        anima = self.js[self.js.index("function animarNumeros("):self.js.index("function animarGraficos(")]
        self.assertIn('if (node.dataset.alvo === undefined) return;', anima)
        self.assertIn('.replace(".", ",")', anima)

    def test_o_ritmo_desenha_a_tendencia_com_a_faixa(self):
        trecho = self.js[self.js.index("function slideRitmo()"):self.js.index("function rankingDePaises(")]
        self.assertIn("band:", trecho)
        self.assertIn("s.tendencia_alto", trecho)
        self.assertIn("area: true", trecho)

    def test_o_ranking_dos_paises_usa_a_bandeira(self):
        trecho = self.js[self.js.index("function rankingDePaises("):self.js.index("function slideMundo()")]
        self.assertIn("Bandeiras.get(p.iso, p.pais)", trecho)
        for regra in (".ranking li {", ".ranking .trilho i {", ".frases li {", ".tile .n.texto {"):
            with self.subTest(regra=regra):
                self.assertIn(regra, self.html)

    def test_a_tela_de_acervos_diz_se_a_rotina_esta_ligada(self):
        trecho = self.js[self.js.index("function slideAcervos()"):self.js.index("/* A ordem é a de quem passa")]
        self.assertIn('"Rotina ligada:"', trecho)
        self.assertIn('"Rotina desligada:"', trecho)
        self.assertIn("p.ultima_boa", trecho)


class TestOAoVivoNaTv(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.js = (TEMPLATES / "aovivo.js").read_text(encoding="utf-8")
        cls.html = (TEMPLATES / "aovivo.html").read_text(encoding="utf-8")

    def abas(self):
        bloco = self.js[self.js.index("const ABAS = ["):]
        bloco = bloco[:bloco.index("];")]
        return re.findall(r'^  \["([a-z]+)", "', bloco, re.M)

    def test_tv_igual_a_um_entra_apresentando_e_no_automatico(self):
        trecho = self.js[self.js.index("(function iniciar()"):]
        self.assertIn('params.get("tv")', trecho)
        self.assertIn("ST.tv = true; ST.apresentando = true; ST.auto = true;", trecho)
        # o cursor some quando ninguém mexe
        self.assertIn('document.body.classList.add("quieto")', trecho)
        self.assertIn("body.tv.quieto { cursor: none; }", self.html)

    def test_sem_menu_nem_cabecalho_e_com_a_faixa(self):
        self.assertIn("body.tv nav.lado, body.tv header.topo { display: none; }", self.html)
        self.assertIn("function desenharFaixaTv()", self.js)
        self.assertIn('id: "faixaTv"', self.js)
        for regra in (".faixa-tv {", ".faixa-tv .noticias .trem {", ".faixa-tv .relogio-tv .hora {", "@keyframes corre-tv"):
            with self.subTest(regra=regra):
                self.assertIn(regra, self.html)
        # quem pede menos movimento não vê a faixa correr
        self.assertIn(".faixa-tv .noticias .trem { animation: none; }", self.html)

    def test_cada_pagina_tem_fatos_ao_vivo(self):
        trecho = self.js[self.js.index("function fatosDaAba(aba)"):self.js.index("function fileiraDeFatos(")]
        for aba in self.abas():
            with self.subTest(aba=aba):
                self.assertIn(f'aba === "{aba}"', trecho)
        self.assertIn("fatos.slice(0, 7)", trecho)
        # os fatos vão para a caixa, e só quando o dado chegou
        self.assertIn("const fatos = D.pronto ? fileiraDeFatos(ST.aba) : null;", self.js)
        self.assertIn(".apresentacao .fatos {", self.html)

    def test_um_fato_nulo_nao_vira_zero(self):
        trecho = self.js[self.js.index("function fatoDe("):self.js.index("function fatosDaAba(")]
        self.assertIn('if (valor === null || valor === undefined || valor === "") return null;', trecho)

    def test_o_tempo_e_por_pagina_e_o_calculo_roda_as_analises(self):
        self.assertIn("const SEGUNDOS_DA_ABA = {", self.js)
        self.assertIn("segundosDa(ST.aba) * 1000", self.js)
        self.assertIn("if (ST.tv) { ST.autoAnalise = true; ST.analise = ANALISES[0][0]; }", self.js)
        # fora da TV o tempo continua o de sempre
        self.assertIn("return (ST.tv && SEGUNDOS_DA_ABA[aba]) || AUTO_SEGUNDOS;", self.js)

    def test_a_pagina_rola_sozinha_na_tv(self):
        self.assertIn("function passearPelaPagina(k)", self.js)
        self.assertIn("if (ST.tv) passearPelaPagina(k);", self.js)

    def test_as_noticias_correm_com_a_data(self):
        trecho = self.js[self.js.index("function noticiasDaTv()"):self.js.index("let relogioTv")]
        self.assertIn("D.noticias", trecho)
        self.assertIn('"Publicado: "', trecho)
        self.assertIn("data(a.data)", trecho)
        self.assertIn("n.eventos", trecho)

    def test_escape_sai_da_tv(self):
        self.assertIn('ev.key === "Escape") { ST.apresentando = false; ST.auto = false; ST.tv = false;', self.js)


if __name__ == "__main__":
    unittest.main()
