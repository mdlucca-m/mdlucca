#!/usr/bin/env python3
"""Testes do modo mural: a tela que fica ligada na sala.

    python3 -m unittest discover -s tests -v

O mural nao tem operador. Se ele quebrar, ninguem clica em nada para
consertar -- fica uma tela preta na parede ate alguem reparar. Por isso o
que se checa aqui e o que impede a tela de subir: marcador de modelo que
sobrou, dado que nao chegou, rota que nao responde e icone chamado por um
nome que nao existe no conjunto.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
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

from lape import api, auth, metrics, report  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
NODE = shutil.which("node")


def _recorta(nome: str) -> str:
    """Uma funcao do mural.js, recortada do arquivo para rodar sozinha.

    O mural e um IIFE que so vive dentro da pagina. Recortar a funcao pura
    e roda-la no Node testa o codigo que esta publicado -- e nao uma copia
    reescrita no teste, que envelhece calada.
    """
    texto = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
    inicio = texto.index(f"function {nome}(")
    fim = texto.index("\n", inicio)
    if texto[inicio:fim].rstrip().endswith("}"):
        return texto[inicio:fim]
    return texto[inicio:texto.index("\n}\n", inicio) + 3]


def _roda(fonte: str):
    if NODE is None:
        raise unittest.SkipTest("node nao esta disponivel nesta maquina")
    pronto = subprocess.run([NODE, "--input-type=module", "-e", fonte],
                            capture_output=True, text=True)
    if pronto.returncode != 0:
        raise AssertionError(pronto.stderr)
    return json.loads(pronto.stdout)


def _no_node(fonte: str, expressao: str):
    return _roda(fonte + "\nprocess.stdout.write(JSON.stringify("
                 + expressao + "));\n")


class _SemRedirecionar(urllib.request.HTTPRedirectHandler):
    """Entrega o 302 em vez de segui-lo."""

    def redirect_request(self, *args, **kwargs):
        return None


class TestMontagemDoMural(unittest.TestCase):
    """A pagina sai inteira do renderizador, sem depender de rede."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        db = Database(Path(cls.tmp.name) / "mural.sqlite")
        db.migrate()
        cls.html = report.render_mural(metrics.build_payload(db))
        db.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_nenhum_marcador_sobrou(self):
        # um "__DATA__" na pagina publicada seria a tela em branco na parede
        for marcador in ("__TITLE__", "__THEME_CSS__", "__ICONS_JS__",
                         "__CHARTS_JS__", "__SCRIPT__", "__DATA__"):
            self.assertNotIn(marcador, self.html, f"marcador {marcador} nao foi substituido")

    def test_leva_tudo_embutido(self):
        self.assertIn("const Icons", self.html)
        self.assertIn("const Charts", self.html)
        self.assertIn("const ROTEIRO", self.html)
        self.assertIn("--surface-sunken", self.html)

    def test_o_dado_e_json_valido(self):
        bruto = re.search(
            r'<script id="payload" type="application/json">(.*?)</script>',
            self.html, re.S).group(1)
        dado = json.loads(bruto.replace("<\\/", "</"))
        self.assertIn("overview", dado)
        self.assertIn("agenda", dado)
        self.assertIn("research_lines", dado)

    def test_o_banco_vazio_nao_derruba_a_montagem(self):
        # laboratorio recem-instalado: zero artigos, zero eventos, e a tela sobe
        self.assertIn("Agora no laboratório", self.html)


class TestIconesChamadosPeloMural(unittest.TestCase):
    """Todo icone pedido pelo mural existe no conjunto.

    `Icons.get` de um nome desconhecido devolve um ponto discreto em vez de
    quebrar -- o que e bom para a pagina e pessimo para quem revisa: o erro
    de digitacao passa despercebido ate alguem notar a bolinha na tela.
    """

    def nomes_do_conjunto(self) -> set[str]:
        fonte = (TEMPLATES / "icons.js").read_text(encoding="utf-8")
        corpo = fonte.split("const SET = {", 1)[1].split("\n  };", 1)[0]
        return set(re.findall(r"^\s{4}([A-Za-z][A-Za-z0-9]*):\s*\[", corpo, re.M))

    def test_o_conjunto_foi_lido(self):
        nomes = self.nomes_do_conjunto()
        self.assertIn("painel", nomes)
        self.assertGreater(len(nomes), 40)

    def test_todo_icone_pedido_existe(self):
        nomes = self.nomes_do_conjunto()
        for arquivo in ("mural.js", "dashboard.js"):
            texto = (TEMPLATES / arquivo).read_text(encoding="utf-8")
            pedidos = set(re.findall(r'Icons\.(?:get|badge)\("([A-Za-z0-9]+)"', texto))
            faltando = pedidos - nomes
            self.assertEqual(faltando, set(),
                             f"icone inexistente em {arquivo}: {sorted(faltando)}")

    def test_todo_tom_tem_regra_no_tema(self):
        # a pastilha e cromo: o tom precisa existir como classe, senao a cor
        # cai no acento e dois cartoes diferentes ficam iguais
        fonte = (TEMPLATES / "icons.js").read_text(encoding="utf-8")
        tons = set(re.findall(r':\s*"([a-z]+)",', fonte.split("const TOM = {", 1)[1]
                              .split("\n  };", 1)[0]))
        tema = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
        for tom in tons:
            self.assertIn(f".ibadge.t-{tom}", tema, f"tom sem regra no tema: {tom}")


class TestRotaDoMural(unittest.TestCase):
    """A rota responde, e responde protegida como o painel."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmp.name) / "api.sqlite"
        db = Database(cls.db_path)
        db.migrate()
        auth.create_account(db, "Coordenação", "coord@udesc.br", "senhaforte123",
                            role="admin")
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
        # sem `seguir`, o urllib segue o 302 sozinho e o teste enxergaria o 200
        # do login -- exatamente o contrario do que ele quer provar
        abridor = (urllib.request.build_opener() if seguir
                   else urllib.request.build_opener(_SemRedirecionar))
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

    def test_sem_sessao_o_mural_manda_entrar(self):
        # a tela da sala mostra dado interno: sem cookie, vai para o login
        status, _, resposta = self.buscar("/mural", seguir=False)
        self.assertIn(status, (302, 303))
        self.assertEqual(resposta.headers.get("Location"), "/entrar")

    def test_com_sessao_a_tela_vem_inteira(self):
        status, corpo, _ = self.buscar("/mural", cookie=self.entrar())
        self.assertEqual(status, 200)
        self.assertIn("const ROTEIRO", corpo)
        self.assertNotIn("__DATA__", corpo)

    def test_tv_e_o_mesmo_endereco(self):
        status, corpo, _ = self.buscar("/tv", cookie=self.entrar())
        self.assertEqual(status, 200)
        self.assertIn("const ROTEIRO", corpo)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestNaBancada(unittest.TestCase):
    """As duas listas de nome e data: em produção e submetidos.

    O que estes testes guardam nao e o desenho: e a ordem. Uma lista que
    poe o artigo sem data no topo anuncia como "o mais antigo" justamente
    o que ninguem datou -- e ninguem na sala tem como saber disso olhando.
    """

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("emOrdemDeData")

    def ordena(self, lista, campo):
        return _no_node(self.fonte, f"emOrdemDeData({json.dumps(lista)},"
                                    f" {json.dumps(campo)})")

    def test_do_mais_antigo_para_o_mais_novo(self):
        fila = self.ordena([{"title": "B", "started_on": "2024-05-01"},
                            {"title": "A", "started_on": "2022-01-10"},
                            {"title": "C", "started_on": "2023-09-30"}], "started_on")
        self.assertEqual([x["title"] for x in fila], ["A", "C", "B"])

    def test_sem_data_vai_para_o_fim(self):
        fila = self.ordena([{"title": "sem data"},
                            {"title": "com data", "started_on": "2025-03-03"}], "started_on")
        self.assertEqual([x["title"] for x in fila], ["com data", "sem data"])

    def test_dois_sem_data_saem_em_ordem_de_titulo(self):
        # empate resolvido por algo estavel, para a tela nao trocar a ordem
        # sozinha a cada redesenho do mural
        fila = self.ordena([{"title": "Zebra"}, {"title": "Abelha"}], "started_on")
        self.assertEqual([x["title"] for x in fila], ["Abelha", "Zebra"])

    def test_a_lista_original_nao_e_remexida(self):
        # `artigos()` devolve o array do payload; ordenar no lugar mudaria a
        # ordem para todos os outros slides
        fonte = self.fonte + """
const original = [{title: "B", started_on: "2024-01-01"},
                  {title: "A", started_on: "2020-01-01"}];
emOrdemDeData(original, "started_on");
process.stdout.write(JSON.stringify(original.map(function (x) { return x.title; })));
"""
        self.assertEqual(_roda(fonte), ["B", "A"])

    def test_as_duas_listas_saem_de_status_diferentes(self):
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideBancada"):js.index("function maisCitados")]
        self.assertIn('a.status === "em_producao"', corpo)
        self.assertIn('a.status === "submetido" || a.status === "em_revisao"', corpo)
        # a data que cada lista promete no titulo e a data que ela usa
        self.assertIn('"started_on"', corpo)
        self.assertIn('"first_submission_on"', corpo)

    def test_o_artigo_sem_data_diz_que_esta_sem_data(self):
        # "1 jan" inventado seria pior do que nao mostrar nada
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideBancada"):js.index("function maisCitados")]
        self.assertIn("sem data de início registrada", corpo)
        self.assertIn("sem data de submissão registrada", corpo)

    def test_a_espera_longa_vem_escrita_e_nao_so_colorida(self):
        # no tema escuro --series-4 e --warning sao quase a mesma cor: a
        # distincao precisa estar em palavra, ou nao existe a tres metros
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideBancada"):js.index("function maisCitados")]
        self.assertIn("ESPERA_LONGA", corpo)
        self.assertIn("sem resposta", corpo)


class TestTempoDecorrido(unittest.TestCase):
    """"ha 780 dias" nao e um numero que alguem leia de pe, a tres metros."""

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("haQuanto")

    def diz(self, dias):
        return _no_node(self.fonte, f"haQuanto({json.dumps(dias)})")

    def test_a_escala_muda_com_a_distancia(self):
        self.assertEqual(self.diz(0), "hoje")
        self.assertEqual(self.diz(-1), "ontem")
        self.assertEqual(self.diz(-10), "há 10 dias")
        self.assertEqual(self.diz(-90), "há 3 meses")
        self.assertEqual(self.diz(-760), "há 2 anos e 1 mês")

    def test_o_passado_e_o_futuro_contam_igual(self):
        # data de inicio vem negativa de `diasAte`; o texto e sempre "ha"
        self.assertEqual(self.diz(-90), self.diz(90))

    def test_sem_data_nao_vira_hoje(self):
        self.assertEqual(self.diz(None), "sem data")

    def test_o_singular_e_o_plural_saem_certos(self):
        self.assertEqual(self.diz(-45), "há 1 mês")
        self.assertEqual(self.diz(-60), "há 2 meses")
        self.assertEqual(self.diz(-730), "há 2 anos")     # sem "e 0 meses"
        self.assertEqual(self.diz(-760), "há 2 anos e 1 mês")

    def test_a_troca_de_escala_nao_deixa_buraco(self):
        """Nenhuma virada de faixa pula um numero ou repete o anterior.

        Em 44 dias a tela diz "44 dias"; em 45, "1 mes". O erro classico
        aqui e a faixa de meses comecar antes do fim da de dias e a parede
        anunciar "ha 1 mes" para tres semanas.
        """
        self.assertEqual(self.diz(-44), "há 44 dias")
        self.assertEqual(self.diz(-45), "há 1 mês")
        self.assertEqual(self.diz(-532), "há 17 meses")   # ultimo mes da faixa
        self.assertEqual(self.diz(-533), "há 1 ano e 6 meses")


class TestOsMaisCitados(unittest.TestCase):
    """Titulo, ano e o numero da Web of Science -- e so o dela."""

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("citacoesWos") + "\n" + _recorta("maisCitados")

    def ranking(self, arts, desde=None):
        return _no_node(self.fonte, f"maisCitados({json.dumps(arts)}, {json.dumps(desde)})")

    ACERVO = [
        {"title": "velho", "year_published": 2011, "wos_citations": 90},
        {"title": "novo", "year_published": 2024, "wos_citations": 40},
        {"title": "recente", "year_published": 2023, "wos_citations": 55},
        {"title": "sem citacao", "year_published": 2022, "wos_citations": 0},
    ]

    def test_do_mais_citado_para_o_menos(self):
        self.assertEqual([a["title"] for a in self.ranking(self.ACERVO)],
                         ["velho", "recente", "novo"])

    def test_artigo_sem_citacao_fica_fora_do_podio(self):
        self.assertNotIn("sem citacao", [a["title"] for a in self.ranking(self.ACERVO)])

    def test_a_janela_corta_pelo_ano_de_publicacao(self):
        recentes = [a["title"] for a in self.ranking(self.ACERVO, 2022)]
        self.assertEqual(recentes, ["recente", "novo"])

    def test_a_wos_nao_e_substituida_pela_melhor_fonte(self):
        """O numero prometido na tela e o da WoS, e ele costuma ser o menor.

        Trocar em silencio pelo maior de tres bases faria a parede exibir
        um numero que ninguem encontra ao conferir na Web of Science.
        """
        acervo = [{"title": "so scopus", "year_published": 2024,
                   "wos_citations": 0, "scopus_citations": 300,
                   "openalex_citations": 280}]
        self.assertEqual(self.ranking(acervo), [])

    def test_wos_ausente_conta_como_zero_e_nao_quebra(self):
        acervo = [{"title": "sem campo", "year_published": 2024},
                  {"title": "com campo", "year_published": 2024, "wos_citations": 3}]
        self.assertEqual([a["title"] for a in self.ranking(acervo)], ["com campo"])

    def test_acervo_sem_wos_explica_de_onde_viria_o_numero(self):
        # zero na parede seria mentira sobre o laboratorio: o campo esta em
        # branco, e a tela precisa dizer isso e por onde ele entra
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideCitados"):js.index("function slideDestaques")]
        self.assertIn("citacoes_wos", corpo)
        self.assertIn("Nenhum artigo com citações da Web of Science", corpo)


class TestOQueAParedeSempreMostra(unittest.TestCase):
    """A marca no topo e as telas do roteiro."""

    @classmethod
    def setUpClass(cls):
        cls.js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        cls.html = (TEMPLATES / "mural.html").read_text(encoding="utf-8")

    def test_a_marca_fica_fora_do_palco(self):
        # o cabecalho e irmao do palco, e nao filho: quem troca de slide
        # esvazia o palco, e a marca precisa sobreviver a isso
        topo = self.html.index('<header class="mtopo">')
        palco = self.html.index('<div class="palco"')
        self.assertLess(topo, palco)
        self.assertIn('id="labNome"', self.html[topo:palco])

    def test_o_nome_do_laboratorio_e_escrito_uma_vez_so(self):
        self.assertIn('document.getElementById("labNome").textContent', self.js)
        self.assertNotIn('palco.appendChild(document.getElementById("labNome")', self.js)

    def test_o_roteiro_cobre_o_que_a_sala_pediu(self):
        roteiro = self.js[self.js.index("const SLIDES = ["):]
        roteiro = roteiro[:roteiro.index("];")]
        for tela in ("bancada", "citados", "agenda"):
            with self.subTest(tela=tela):
                self.assertIn('id: "' + tela + '"', roteiro)

    def test_a_janela_de_cinco_anos_e_uma_so(self):
        """O grafico por ano e o recorte dos mais citados andam juntos.

        Com duas constantes, um dia alguem mexe numa e a parede passa a
        dizer "ultimos 5 anos" num quadro e mostrar oito no outro.
        """
        self.assertIn("const JANELA", self.js)
        self.assertIn("anos.slice(-JANELA)", self.js)
        self.assertIn("JANELA - 1", self.js)
        self.assertIn('"Mais citados nos últimos " + JANELA + " anos"', self.js)
