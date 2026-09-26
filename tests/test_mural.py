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


def _bases() -> str:
    """A tabela BASES, lida do mural -- e não recopiada aqui.

    Recopiar faria o teste continuar verde no dia em que a ordem das bases
    mudasse no arquivo publicado.
    """
    texto = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
    inicio = texto.index("const BASES = [")
    fim = texto.index("];", inicio) + 1
    return texto[inicio + len("const BASES = "):fim]


def _no_node(fonte: str, expressao: str):
    return _roda(fonte + "\nprocess.stdout.write(JSON.stringify("
                 + expressao + "));\n")


def _recorta_3d(nome: str) -> str:
    """Mesma ideia de `_recorta`, para slides-avancados-3d.js (a lamina
    "Linhas de Pesquisa 3D" mora la, nao em mural.js)."""
    texto = (TEMPLATES / "slides-avancados-3d.js").read_text(encoding="utf-8")
    inicio = texto.index(f"function {nome}(")
    fim = texto.index("\n}\n", inicio) + 3
    return texto[inicio:fim]


class _SemRedirecionar(urllib.request.HTTPRedirectHandler):
    """Entrega o 302 em vez de segui-lo."""

    def redirect_request(self, *args, **kwargs):
        return None


class TestAFaixaDeCotacao(unittest.TestCase):
    """Os indicadores correndo no topo, no formato de painel de bolsa.

    Tres decisoes que nao sao esteticas, e sao o que estes testes guardam:

      1. variacao SO com duas medicoes. O `delta_30d` do payload e `null`
         enquanto o lakehouse tiver rodado uma vez so -- e um "▲ 0" ali
         diria a parede inteira que nada mudou, quando a verdade e que
         nada foi medido duas vezes;
      2. a BASE da comparacao vai escrita: "30 d" e medido, "vs 2025" e
         contado. Uma seta sem base e uma seta sobre o que a pessoa
         imaginar;
      3. subir nao e bom para todo indicador. Publicacao e citacao subindo
         e bom -- e ai o verde de painel de bolsa e legitimo. "Em escrita"
         subindo pode ser produtividade ou gargalo, e o laboratorio nao
         declarou qual: pintar de verde seria a tela julgando por conta
         propria.
    """

    @classmethod
    def setUpClass(cls):
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        cls.corpo = js[js.index("function cotacoes()"):js.index("function desenharFita()")]
        cls.html = (TEMPLATES / "mural.html").read_text(encoding="utf-8")

    def test_nulo_nao_vira_zero(self):
        """A trava mais importante: `!= null` e nao um teste de verdade.

        Com `if (x.delta)` um zero MEDIDO -- que e informacao, "nao mudou
        em 30 dias" -- desapareceria, e com `??` um nulo viraria zero. Os
        dois casos sao diferentes e a faixa tem de distingui-los.
        """
        self.assertIn("delta_30d !== null", self.corpo)
        self.assertIn("delta_30d !== undefined", self.corpo)
        # e na hora de desenhar, o mesmo cuidado
        self.assertIn("x.delta !== null", self.corpo)
        self.assertNotIn("x.delta ??", self.corpo)

    def test_sem_segunda_medicao_a_faixa_diz_em_vez_de_calar(self):
        self.assertIn('class: "var sem"', self.corpo)

    def test_a_base_da_comparacao_viaja_com_a_variacao(self):
        self.assertIn('base: "30 d"', self.corpo)
        self.assertIn('base: "vs "', self.corpo)
        # e e impressa junto do numero
        self.assertIn('+ " " + x.base', self.corpo)

    def test_indicador_ambiguo_nao_ganha_cor_de_estado(self):
        """"Em escrita" e "em avaliacao" sobem por motivos opostos."""
        for sigla in ('"ESCRITA"', '"AVAL"'):
            trecho = self.corpo[self.corpo.index("sigla: " + sigla):]
            trecho = trecho[:trecho.index("},")]
            with self.subTest(sigla=sigla):
                self.assertIn("bom: null", trecho)

    def test_indicador_de_direcao_acordada_ganha(self):
        for sigla in ('"ACERVO"', '"CIT"', '"H"'):
            trecho = self.corpo[self.corpo.index("sigla: " + sigla):]
            trecho = trecho[:trecho.index("},")]
            with self.subTest(sigla=sigla):
                self.assertIn('bom: "sobe"', trecho)

    def test_a_cor_de_estado_depende_do_bom_declarado(self):
        """Sem o `!x.bom`, todo indicador que sobe ficaria verde."""
        self.assertIn("!x.bom ? \"neutro\"", self.corpo)

    def test_indicador_que_o_laboratorio_nao_tem_sai_da_faixa(self):
        """Zero de indice h nao e zero -- e ninguem ter declarado."""
        self.assertIn("x.valor !== 0", self.corpo)

    def test_a_faixa_se_esconde_quando_nao_ha_o_que_cotar(self):
        self.assertIn("faixa.hidden = true", self.corpo)

    def test_a_faixa_acompanha_a_tela_de_parede_e_sai_na_pequena(self):
        """As duas regras que o resto do mural ja segue."""
        trecho = self.html[self.html.index(".cotacao {"):]
        trecho = trecho[:trecho.index("}")]
        self.assertIn("var(--zoom", trecho)
        self.assertIn(".fita, .cotacao { display: none; }", self.html)

    def test_quem_pede_menos_movimento_nao_recebe_a_faixa_correndo(self):
        self.assertIn(".cotacao .trilha { animation: none; }", self.html)


class TestOMuralNaTelaDeParede(unittest.TestCase):
    """4K: o texto tem de crescer junto com a tela.

    Medido antes de escrever: num monitor de 3840px o layout preenchia a
    largura inteira -- nao ha `max-width` --, mas o texto ficava nos
    MESMOS 15px de um Full HD, porque cada `clamp` tem um maximo e os
    maximos foram escolhidos para 1920. Os graficos, que sao SVG com
    viewBox, continuavam crescendo. O resultado era uma tela
    desequilibrada: uma rosca enorme e rotulos ilegiveis do outro lado da
    sala -- que e de onde um mural e lido.
    """

    @classmethod
    def setUpClass(cls):
        cls.css = (TEMPLATES / "mural.html").read_text(encoding="utf-8")

    def test_todo_teto_de_fonte_acompanha_a_tela(self):
        """Um teto esquecido e um rotulo que fica pequeno so naquele lugar."""
        sem_zoom = [t for t in re.findall(r"font-size: clamp\([^;]*", self.css)
                    if "var(--zoom" not in t]
        self.assertEqual(sem_zoom, [])

    def test_abaixo_da_tela_de_parede_nada_muda(self):
        """`--zoom` vale 1 por padrao, e por isso 1080 e 1440 ficam iguais.

        Sem o `, 1)` no `var()`, o navegador cai no valor inicial de uma
        propriedade nao registrada -- que e vazio -- e o `calc` inteiro se
        torna invalido: o teto desaparece e o texto cresce sem limite em
        QUALQUER largura.
        """
        for teto in re.findall(r"calc\([0-9.]+px \* var\(--zoom[^)]*\)\)", self.css):
            with self.subTest(teto=teto):
                self.assertIn("var(--zoom, 1)", teto)

    def test_o_zoom_so_liga_em_tela_larga(self):
        self.assertIn("@media (min-width: 2200px) { :root { --zoom: 1.65; } }", self.css)
        self.assertIn("@media (min-width: 3200px) { :root { --zoom: 1.95; } }", self.css)
        # e nao ha `--zoom` diferente de 1 fora de media query
        fora = re.search(r"^:root \{[^}]*--zoom", self.css, re.M)
        self.assertIsNone(fora, "--zoom declarado fora de media query")

    def test_a_faixa_de_noticias_nao_tem_altura_fixa(self):
        """Ela cortava a noticia no meio quando o texto cresceu.

        Foi o defeito que a propria mudanca causou: fonte ampliada dentro
        de uma faixa de 26px fixos. A altura passou a acompanhar o zoom.
        """
        trecho = self.css[self.css.index(".fita {"):]
        trecho = trecho[:trecho.index("}")]
        self.assertIn("var(--zoom", trecho)
        self.assertNotIn("height: 26px", trecho)

    def test_o_que_e_pequeno_de_longe_tambem_cresce(self):
        """Ponto de 9px numa parede de 4K nao existe para quem olha."""
        for alvo in (".pontos button {", ".selo.vivo .ponto {", ".trilho {"):
            with self.subTest(regra=alvo):
                trecho = self.css[self.css.index(alvo):]
                trecho = trecho[:trecho.index("}")]
                self.assertIn("var(--zoom", trecho)


class TestOHorarioNaPauta(unittest.TestCase):
    """"Esta cadastrado, mas nao aparece".

    A etiqueta de data mostrava dia e mes, e o horario ficava no banco sem
    chegar a parede -- e saber se a qualificacao e as 9h ou as 14h e
    exatamente para o que o mural serve.
    """

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("horaDe")

    def hora(self, iso, dia_inteiro=0):
        return _no_node(self.fonte,
                        f"horaDe({json.dumps(iso)}, {dia_inteiro})")

    def test_a_hora_marcada_aparece(self):
        self.assertEqual(self.hora("2026-09-17 09:00"), "09:00")
        self.assertEqual(self.hora("2026-09-16 14:00"), "14:00")

    def test_data_sem_hora_nao_inventa_hora(self):
        self.assertEqual(self.hora("2026-09-17"), "")

    def test_meia_noite_exata_nao_vira_00_00(self):
        """O campo aceita so a data, e ai a hora gravada e zero por omissao.

        Escrever "00:00" afirmaria uma hora que ninguem marcou -- e num
        mural de parede isso manda o laboratorio para a reuniao errada.
        """
        self.assertEqual(self.hora("2026-09-17 00:00"), "")

    def test_evento_de_dia_inteiro_nao_mostra_hora(self):
        """Mesmo com horario preenchido: `all_day` e uma declaracao."""
        self.assertEqual(self.hora("2026-10-02 09:00", 1), "")

    def test_lixo_no_campo_nao_estoura_nem_aparece(self):
        for ruim in ("", "2026-09-17 9:0", "sem data nenhuma"):
            with self.subTest(valor=ruim):
                self.assertEqual(self.hora(ruim), "")

    def test_a_pauta_passa_a_hora_para_a_etiqueta(self):
        """A funcao existir nao basta: alguem tem de chama-la."""
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        trecho = js[js.index("function linhaDePauta("):]
        trecho = trecho[:trecho.index("\n}")]
        self.assertIn("item.hora", trecho)
        montagem = js[js.index("const pauta = proximos.length"):]
        montagem = montagem[:montagem.index("vazio(")]
        self.assertIn("horaDe(e.start_at, e.all_day)", montagem)


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
        """Todo marcador do modelo tem de ter sido trocado por conteudo.

        A lista sai do PROPRIO modelo, e nao escrita a mao aqui. Escrita a
        mao ela envelhece calada: foi assim que `__BANDEIRAS_JS__` passou
        -- o marcador entrou no mural.html, a substituicao foi ligada so na
        outra rota, e o teste continuou verde conferindo os cinco de antes.
        Na parede, o marcador sobrevivia literal dentro do <script>, virava
        ReferenceError ao carregar, o bloco morria e `Bandeiras` ficava
        indefinido.
        """
        modelo = (TEMPLATES / "mural.html").read_text(encoding="utf-8")
        marcadores = set(re.findall(r"__[A-Z][A-Z0-9_]*__", modelo))
        self.assertIn("__DATA__", marcadores, "o modelo do mural mudou de forma")
        for marcador in sorted(marcadores):
            with self.subTest(marcador=marcador):
                self.assertNotIn(marcador, self.html,
                                 f"marcador {marcador} nao foi substituido")

    def test_a_parede_nao_conta_citacao_por_linha_de_pesquisa(self):
        """O número existe, mas só para o artigo com DOI indexado.

        Como boa parte do acervo não tem, a soma por linha sai por baixo.
        Na parede isso não se lê como "faltam DOIs": lê-se como "esta
        linha não é citada", que é uma afirmação que o dado não sustenta.
        """
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function graficoDasAreas()"):]
        corpo = corpo[:corpo.index("function slideCitados")]
        self.assertNotIn('text: "Citações"', corpo)

    def test_a_lamina_da_equipe_diz_quem_e_e_nao_quanto_produz(self):
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideDestaques()"):]
        corpo = corpo[:corpo.index("\nconst SLIDES")]
        self.assertIn("VINCULO_NOME", corpo)
        self.assertNotIn("produção por pessoa", corpo)
        self.assertNotIn("n_articles", corpo)
        # o maior indice h saiu: numa parede lida pela propria equipe ele e
        # sempre da mesma pessoa, e transforma a tela de quem-e-quem em podio
        self.assertNotIn("best_h_index", corpo)
        self.assertNotIn("h_index", corpo)

    def test_a_lamina_da_equipe_e_so_de_quem_e_do_lape(self):
        """Coautor de fora assina o artigo e nao e integrante.

        Ele entra na producao e na rede de colaboracao -- e a faixa de
        numeros desta mesma tela conta esses pares de proposito. O que ele
        nao pode e aparecer na lista de quem trabalha aqui, nem na conta
        de "8 de 20 integrantes", que e o que a sala confere de cabeca.
        """
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideDestaques()"):]
        corpo = corpo[:corpo.index("\nconst SLIDES")]
        self.assertIn("!m.is_external", corpo)
        # a mesma lista filtrada serve a tabela, a contagem do rodape e as
        # linhas de pesquisa: tres numeros que tem de fechar entre si
        self.assertEqual(corpo.count("!m.is_external"), 1,
                         "mais de um filtro de equipe: eles vao divergir")
        self.assertIn("doLape.length", corpo)
        self.assertIn("agrupadosPorLinha(doLape", corpo)

    def test_cada_linha_de_pesquisa_mostra_quem_trabalha_nela(self):
        """Era uma rosca de ARTIGOS por linha, e virou gente.

        Diante de uma linha de pesquisa, quem passa no corredor pergunta
        "quem toca isso" -- quantos papeis sairam dali a tela das citacoes
        ja responde, em barras.
        """
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideDestaques()"):]
        corpo = corpo[:corpo.index("\nconst SLIDES")]
        self.assertIn("Integrantes de cada linha", corpo)
        self.assertNotIn("Onde a produção está", corpo)
        self.assertNotIn("C.donut", corpo)

    def test_a_producao_por_area_e_renderizada_e_nao_so_calculada(self):
        """Calcular e nao desenhar deixaria a tela vazia sem erro nenhum."""
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideCitados"):js.index("function agrupadosPorLinha")]
        self.assertIn("area.grafico", corpo)
        self.assertIn("area.titulo", corpo)


    def test_leva_tudo_embutido(self):
        self.assertIn("const Icons", self.html)
        self.assertIn("const Charts", self.html)
        self.assertIn("const Bandeiras", self.html)
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


class TestIntegrantesDeCadaLinha(unittest.TestCase):
    """O agrupamento da equipe por linha de pesquisa, rodado de verdade."""

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("agrupadosPorLinha")

    def agrupa(self, gente, linhas):
        return _no_node(self.fonte, f"agrupadosPorLinha({json.dumps(gente)},"
                                    f" {json.dumps(linhas)})")

    # "Exergames" vem ANTES na lista da coordenacao e tem MENOS gente: e o
    # que separa "ordenou" de "saiu na ordem em que estava cadastrado"
    LINHAS = [{"name": "Exergames"}, {"name": "Dor crônica"}, {"name": "Câncer"}]
    EQUIPE = [
        {"short_name": "A", "research_line": "Dor crônica"},
        {"short_name": "B", "research_line": "Exergames"},
        {"short_name": "C", "research_line": "Dor crônica"},
        {"short_name": "D", "research_line": None},
    ]

    def test_da_linha_mais_cheia_para_a_mais_vazia(self):
        saida = self.agrupa(self.EQUIPE, self.LINHAS)
        self.assertEqual([x["nome"] for x in saida],
                         ["Dor crônica", "Exergames", "Sem linha declarada"])

    def test_linha_sem_ninguem_nao_vira_fileira_vazia(self):
        # "Câncer" está cadastrada e não tem ninguém: uma linha em branco
        # na parede ocupa a altura de quem tem gente e não diz nada
        nomes = [x["nome"] for x in self.agrupa(self.EQUIPE, self.LINHAS)]
        self.assertNotIn("Câncer", nomes)

    def test_quem_nao_tem_linha_declarada_nao_some_da_conta(self):
        """Escondido, a soma das linhas nao bate com o total da equipe.

        Quem confere de cabeca acharia que a parede perdeu alguem -- e a
        parede nao teria como avisar que nao perdeu. Hoje, no banco do
        LAPE, este e o caso de TODO MUNDO: ninguem tem linha declarada, e
        sem esta regra o quadro sairia vazio com quinze pessoas dentro.
        """
        saida = self.agrupa(self.EQUIPE, self.LINHAS)
        gente = [m["short_name"] for x in saida for m in x["gente"]]
        self.assertEqual(sorted(gente), ["A", "B", "C", "D"])
        self.assertEqual(saida[-1]["nome"], "Sem linha declarada")

    def test_o_balde_dos_sem_linha_fica_no_fim_mesmo_sendo_o_maior(self):
        """Ele e um resto, e nao a maior linha de pesquisa do laboratorio."""
        equipe = [{"short_name": str(i), "research_line": None} for i in range(9)]
        equipe.append({"short_name": "x", "research_line": "Dor crônica"})
        saida = self.agrupa(equipe, self.LINHAS)
        self.assertEqual(saida[0]["nome"], "Dor crônica")
        self.assertEqual(saida[-1]["nome"], "Sem linha declarada")

    def test_linha_que_a_pessoa_declara_e_que_nao_esta_na_lista_conta(self):
        """A pessoa esta la de todo jeito.

        Cair no "sem linha declarada" por causa de um nome que a
        coordenacao ainda nao cadastrou seria a parede dizer que ela nao
        declarou -- quando ela declarou.
        """
        saida = self.agrupa([{"short_name": "Z", "research_line": "Qualidade do ar"}],
                            self.LINHAS)
        self.assertEqual([x["nome"] for x in saida], ["Qualidade do ar"])

    def test_equipe_vazia_nao_inventa_balde(self):
        self.assertEqual(self.agrupa([], self.LINHAS), [])

    def test_linha_encerrada_e_vazia_sai_da_parede(self):
        """Encerrada COM artigo fica: a produção é história do laboratório."""
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function graficoDasAreas()"):]
        corpo = corpo[:corpo.index("function slideCitados")]
        self.assertIn("x.ativa || x.total > 0", corpo)


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
        corpo = js[js.index("function slideBancada"):js.index("function graficoDasAreas")]
        self.assertIn('a.status === "em_producao"', corpo)
        self.assertIn('a.status === "submetido" || a.status === "em_revisao"', corpo)
        # a data que cada lista promete no titulo e a data que ela usa
        self.assertIn('"started_on"', corpo)
        self.assertIn('"first_submission_on"', corpo)

    def test_o_artigo_sem_data_diz_que_esta_sem_data(self):
        # "1 jan" inventado seria pior do que nao mostrar nada
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideBancada"):js.index("function graficoDasAreas")]
        self.assertIn("sem data de início registrada", corpo)
        self.assertIn("sem data de submissão registrada", corpo)

    def test_a_espera_longa_vem_escrita_e_nao_so_colorida(self):
        # no tema escuro --series-4 e --warning sao quase a mesma cor: a
        # distincao precisa estar em palavra, ou nao existe a tres metros
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideBancada"):js.index("function graficoDasAreas")]
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


class TestCitacoesNaParede(unittest.TestCase):
    """Uma base por vez, e a tela diz qual.

    A regra antiga era "so a Web of Science", e ela guardava algo certo:
    exibir o maior de tres bases sob o rotulo de uma faria a parede
    anunciar um numero que ninguem encontra ao conferir. O que ela nao
    previa era o acervo sem WoS -- e foi o que aconteceu: um laboratorio
    com quatro mil citacoes na OpenAlex viu "0 citacoes" na parede, porque
    a tela perguntava a uma base so e a coluna dela estava em branco.

    A parede escolhia UMA base e mostrava o ranking dela. A coordenacao
    pediu as DUAS que a avaliacao usa, lado a lado, e tirou os dois quadros
    de artigo mais citado. Entao nao ha mais base escolhida -- ha WoS e
    Scopus, cada uma com o seu proprio numero. O que nao mudou, e e o que
    estes testes guardam: misturar continua proibido, e zero continua
    tendo de se distinguir de "nao perguntei a esta base".
    """

    @classmethod
    def setUpClass(cls):
        cls.fonte = ("const BASES = " + _bases() + ";\n"
                     + _recorta("citacoesDe") + "\n"
                     + _recorta("basesComNumero"))
        cls.js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")

    @property
    def tela(self):
        return self.js[self.js.index("function slideCitados"):
                       self.js.index("function slideDestaques")]

    # -- o numero de cada base -------------------------------------------
    def test_o_numero_e_o_da_base_pedida_e_nunca_o_maior(self):
        """Misturar continua proibido.

        Trocar em silencio pelo maior de tres faria a parede exibir um
        numero que ninguem encontra ao conferir na base escrita ao lado.
        """
        artigo = {"title": "so scopus", "wos_citations": 0,
                  "scopus_citations": 300, "openalex_citations": 280}
        wos = {"campo": "wos_citations", "rotulo": "Web of Science", "curto": "WoS"}
        scopus = {"campo": "scopus_citations", "rotulo": "Scopus", "curto": "Scopus"}
        self.assertEqual(
            _no_node(self.fonte, f"citacoesDe({json.dumps(artigo)}, {json.dumps(scopus)})"),
            300)
        # e a WoS continua zero, e nao os 300 da vizinha nem os 280 da outra
        self.assertEqual(
            _no_node(self.fonte, f"citacoesDe({json.dumps(artigo)}, {json.dumps(wos)})"),
            0)

    def test_a_tela_diz_quais_bases_tem_numero(self):
        # sem isso, quem le compara com o que viu no Lattes e nao entende a
        # diferenca -- e a diferenca entre bases e grande e legitima
        acervo = [{"title": "x", "wos_citations": 5, "openalex_citations": 9}]
        nomes = [b["curto"] for b in
                 _no_node(self.fonte, f"basesComNumero({json.dumps(acervo)})")]
        self.assertEqual(nomes, ["WoS", "OpenAlex"])

    def test_acervo_sem_base_nenhuma_nao_inventa_fonte(self):
        acervo = [{"title": "nada"}]
        self.assertEqual(_no_node(self.fonte, f"basesComNumero({json.dumps(acervo)})"), [])

    # -- o que a tela escreve --------------------------------------------
    def test_a_parede_mostra_as_duas_bases_da_avaliacao(self):
        """WoS e Scopus, cada uma com o seu numero e o seu nome escrito."""
        self.assertIn('"Citações na " + b.curto', self.tela)
        self.assertIn("wos_citations:", self.tela)
        self.assertIn("scopus_citations:", self.tela)

    def test_base_que_nao_respondeu_nao_anuncia_zero_calado(self):
        """O defeito que este teste guarda: 4.051 citacoes e "0" na parede.

        Com DUAS bases fixas na tela, o defeito voltaria pela porta da
        frente: a UDESC pode nao ter chave da WoS, e a coluna fica em
        branco para o acervo inteiro. Um "0" ali se le como "este
        laboratorio nao e citado". O pe do numero tem de dizer que a
        pergunta nao foi feita.
        """
        self.assertIn("esta base ainda não respondeu", self.tela)
        self.assertIn("respondeu ?", self.tela)

    def test_os_dois_quadros_de_ranking_sairam(self):
        """Nenhum artigo e destacado pelo nome na parede do corredor."""
        for sumiu in ("placarDeCitacoes", "maisCitados", "Artigos mais citados",
                      "Mais citado"):
            with self.subTest(sumiu=sumiu):
                self.assertNotIn(sumiu, self.js)

    def test_linha_cadastrada_sem_artigo_nao_vira_grafico_vazio(self):
        """Ter linha cadastrada e ter artigo LIGADO a ela sao coisas diferentes.

        Com as linhas declaradas e nenhum artigo apontando para elas, o
        grafico saia: um quadro do tamanho da parede, os nomes das linhas
        no eixo e nenhuma barra em cima. Quem olha nao le "ninguem
        classificou os artigos ainda" -- le "este laboratorio nao produziu
        nada". E o estado real do banco do LAPE hoje.
        """
        corpo = self.js[self.js.index("function graficoDasAreas"):
                        self.js.index("function slideCitados")]
        self.assertIn("comDado.length", corpo)
        self.assertIn("nenhum dos", corpo)

    def test_nenhuma_linha_ativa_some_por_causa_de_um_teto_arbitrario(self):
        """A lamina prometia "cada linha ATIVA aparece", e o codigo tinha
        um `.slice(0, 8)` que a contradizia: acima de 8 linhas ativas, as
        excedentes sumiam da parede sem aviso nenhum. `graficoDasAreas`
        nao pode mais cortar a lista -- so separa quem tem artigo (vira
        barra) de quem nao tem (vira nota, nunca desaparece)."""
        corpo = self.js[self.js.index("const porLinha ="):
                        self.js.index("function slideCitados")]
        self.assertNotIn(".slice(0, 8)", corpo)
        self.assertIn("comDado", corpo)
        self.assertIn("semDado", corpo)

    def test_linha_sem_artigo_vira_nota_nao_barra_vazia(self):
        corpo = self.js[self.js.index("function faixasPorLinha"):
                        self.js.index("function slideCitados")]
        self.assertIn("linhas-pesquisa-vazias", corpo)
        self.assertIn("sem artigo ainda", corpo)

    def test_a_dispersao_3d_saiu_e_a_faixa_horizontal_voltou(self):
        """Achado ao vivo (print do Mateus): com o acervo real, a maioria
        das linhas tem números baixos e parecidos -- a esfera 3D
        normalizava quase todo mundo perto da origem, e um quadro do
        tamanho da parede virava um amontoado ilegível no meio da tela,
        com os rótulos empilhados tentando escapar da colisão. A barra
        horizontal, que já existia e foi feita para exatamente esta
        distância de leitura, voltou a ser o gráfico desta lâmina."""
        corpo = self.js[self.js.index("function graficoDasAreas"):
                        self.js.index("function slideCitados")]
        self.assertIn("faixasPorLinha(comDado, semDado)", corpo)
        self.assertNotIn("matrizImpactoPorLinha", self.js)
        self.assertNotIn("scatter3d", self.js)
        chart_js = (TEMPLATES / "charts-enhanced.js").read_text(encoding="utf-8")
        self.assertNotIn("scatter3d", chart_js)

    def test_a_faixa_mostra_citacoes_da_linha_tambem(self):
        """O título promete "publicados, citações e produção por linha" --
        a faixa horizontal não pode ficar só com os três status e perder
        a citação que a dispersão 3D antes mostrava num eixo."""
        corpo = self.js[self.js.index("function faixasPorLinha"):
                        self.js.index("function slideCitados")]
        self.assertIn("total-citacoes", corpo)
        self.assertIn("x.citacoes", corpo)

    def test_linha_de_alto_potencial_continua_sinalizada(self):
        """O destaque ("poucos publicados, produção real em andamento")
        que a dispersão 3D piscava em ciano continua existindo -- só que
        na faixa, não na esfera."""
        corpo = self.js[self.js.index("function faixasPorLinha"):
                        self.js.index("function slideCitados")]
        self.assertIn("temPotencialAlto", corpo)
        self.assertIn("ponto-vivo", corpo)
        self.assertIn("produção real em andamento", corpo)

    def test_a_producao_por_area_mora_nesta_tela(self):
        """Era uma tela so dela, tres telas adiante; virou o grafico daqui."""
        self.assertIn("graficoDasAreas()", self.tela)
        roteiro = self.js[self.js.index("const SLIDES = ["):]
        roteiro = roteiro[:roteiro.index("];")]
        self.assertNotIn('id: "areas"', roteiro)


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

    def test_o_grafico_do_ano_e_de_barras_com_o_numero_escrito(self):
        """A parede e lida de longe e de passagem.

        A pergunta que se faz dela e "quantos naquele ano", nao "qual o
        desenho da curva" -- e uma area obriga quem olha a seguir a linha
        ate o eixo para responder. Com barras de uma serie so, o numero
        vai escrito em cima de cada uma.
        """
        corpo = self.js[self.js.index("function slideAgora"):
                        self.js.index("function slidePrazos")]
        self.assertIn("C.columns", corpo)
        self.assertNotIn("C.area", corpo)

    def test_a_janela_de_cinco_anos_e_uma_so(self):
        """Quem escreve "ultimos N anos" e quem corta em N e a mesma constante.

        Com duas, um dia alguem mexe numa e a parede passa a dizer
        "ultimos 5 anos" num quadro e mostrar oito no outro. O segundo
        dono da janela era o recorte dos mais citados, que saiu da parede
        junto com os dois quadros de ranking; sobrou o grafico por ano, e
        a constante continua uma so -- que e a regra, e nao o numero de
        quem a usa.
        """
        self.assertIn("const JANELA", self.js)
        self.assertIn("anos.slice(-JANELA)", self.js)
        self.assertEqual(self.js.count("JANELA"), 2,
                         "a janela ganhou outro dono: confira se os dois cortam igual")


class TestChegadaAoVivo(unittest.TestCase):
    """O cartão holográfico e o odômetro das citações: `/api/mural/chegadas`
    e as contas de progresso que alimentam esse cartão (route_mural_chegadas,
    _mediana_dias_escrita, _progresso_estimado em api.py)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "chegadas.sqlite")
        self.db.migrate()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _linha_pesquisa(self, nome="Linha de teste"):
        self.db.execute(
            "INSERT INTO research_lines (code, name) VALUES (?, ?)", (nome[:8], nome))
        self.db.conn.commit()
        return self.db.scalar("SELECT id FROM research_lines WHERE name = ?", (nome,))

    _contador_artigos = 0

    def _artigo(self, research_line_id, started_on, fim=None, status="em_producao"):
        TestChegadaAoVivo._contador_artigos += 1
        titulo = f"artigo {TestChegadaAoVivo._contador_artigos} {started_on} {fim}"
        self.db.execute(
            "INSERT INTO articles (title, title_key, status, research_line_id,"
            " started_on, first_submission_on) VALUES (?, ?, ?, ?, ?, ?)",
            (titulo, titulo.lower(), status, research_line_id, started_on, fim))
        self.db.conn.commit()
        return self.db.scalar("SELECT id FROM articles WHERE title_key = ?", (titulo.lower(),))

    def test_sem_data_de_inicio_nao_quebra_e_devolve_o_minimo(self):
        self.assertEqual(api._progresso_estimado(self.db, {"started_on": None}), 5)

    def test_sem_historico_na_linha_usa_180_dias_como_referencia(self):
        self.assertEqual(api._mediana_dias_escrita(self.db, None), 180.0)
        self.assertEqual(api._mediana_dias_escrita(self.db, 999999), 180.0)

    def test_mediana_e_a_do_meio_entre_os_artigos_concluidos_da_linha(self):
        linha = self._linha_pesquisa()
        # 30, 60 e 90 dias -- mediana e' 60, e o em_producao (sem "fim") nao entra na conta
        self._artigo(linha, "2024-01-01", "2024-01-31")
        self._artigo(linha, "2024-01-01", "2024-03-01")
        self._artigo(linha, "2024-01-01", "2024-04-01")
        self._artigo(linha, "2024-06-01", None)
        self.assertAlmostEqual(api._mediana_dias_escrita(self.db, linha), 60, delta=2)

    def test_progresso_nunca_passa_de_95_nem_fica_abaixo_de_5(self):
        linha = self._linha_pesquisa("Linha rapida")
        self._artigo(linha, "2024-01-01", "2024-01-11")  # mediana de 10 dias
        # comecado ha muitos anos: sem o teto, passaria de 100%
        antigo = {"started_on": "2015-01-01", "research_line_id": linha}
        self.assertEqual(api._progresso_estimado(self.db, antigo), 95)
        # comecado agora mesmo: sem o piso, seria 0%
        from datetime import datetime
        hoje = datetime.now().strftime("%Y-%m-%d")
        recente = {"started_on": hoje, "research_line_id": linha}
        self.assertEqual(api._progresso_estimado(self.db, recente), 5)

    def test_chegada_traz_no_maximo_dois_artigos_em_producao(self):
        membro_id = self.db.member_id("Fulana de Tal")
        linha = self._linha_pesquisa("Linha da Fulana")
        for i in range(3):
            artigo_id = self._artigo(linha, "2024-01-01", None)
            self.db.execute(
                "INSERT INTO article_authors (article_id, member_id, author_name, author_order)"
                " VALUES (?, ?, ?, 1)", (artigo_id, membro_id, "Fulana de Tal"))
        self.db.conn.commit()

        chegada = api._chegada_com_producao(self.db, {
            "id": 1, "entrada": "2026-01-01 08:00:00",
            "member_id": membro_id, "full_name": "Fulana de Tal", "photo_url": None,
        })
        self.assertEqual(chegada["nome"], "Fulana de Tal")
        self.assertEqual(len(chegada["artigos"]), 2)

    def test_desde_id_ausente_so_estabelece_o_marco_zero(self):
        membro_id = self.db.member_id("Beltrano Silva")
        self.db.execute("INSERT INTO ponto (member_id, entrada) VALUES (?, ?)",
                        (membro_id, "2026-01-01 08:00:00"))
        self.db.conn.commit()

        class ContextoFalso:
            db = self.db
            query = {}
            user = {}

        resultado = api.route_mural_chegadas(ContextoFalso())
        self.assertEqual(resultado["chegadas"], [])
        self.assertGreaterEqual(resultado["ultimo_id"], 1)


class TestQuebraDeNomeDaLinha3D(unittest.TestCase):
    """`quebrarEmDuasLinhas`, da lâmina "Linhas de Pesquisa 3D": rótulo em
    até 2 linhas, sem cortar o nome no meio nem embaralhar a ordem das
    palavras -- o bug real que motivou este teste trocava "Psicologia do
    exercício e saúde mental" por "Psicologia do e saúde" / "exercício
    mental", com "e" pulando na frente de "exercício"."""

    CORTAR_JS = ('function cortar(t, n) { const s = String(t || ""); '
                 'return s.length > n ? s.slice(0, n - 1) + "…" : s; }')

    def _quebrar(self, nome, maximo):
        fonte = self.CORTAR_JS + "\n" + _recorta_3d("quebrarEmDuasLinhas")
        return _no_node(fonte, f"quebrarEmDuasLinhas({json.dumps(nome)}, {maximo})")

    def test_nome_curto_nao_quebra(self):
        self.assertEqual(self._quebrar("Câncer", 22), ["Câncer", ""])

    def test_a_ordem_das_palavras_nunca_embaralha(self):
        nome = "Psicologia do exercício e saúde mental"
        linha1, linha2 = self._quebrar(nome, 22)
        # reconstruir linha1+linha2 tem de devolver as palavras na MESMA
        # ordem do nome original -- o bug real deixava "e" pular na frente
        # de "exercício" ao voltar para a linha 1 depois de já ter
        # transbordado para a linha 2.
        self.assertEqual((linha1 + " " + linha2).strip(), nome)

    def test_so_corta_em_ultimo_caso_quando_o_nome_e_bem_comprido(self):
        nome = ("Investigação longitudinal multicêntrica sobre biomarcadores "
                "inflamatórios crônicos associados ao treinamento físico intenso")
        linha1, linha2 = self._quebrar(nome, 22)
        self.assertIn("…", linha2)
        # mesmo cortada, a linha 1 e o comeco real do nome -- sem pular parte dele
        self.assertTrue(nome.startswith(linha1))


class TestQuemTemOrientadorNoOrganograma(unittest.TestCase):
    """`temOrientadorVisivel` -- decide quem NUNCA pode ser raiz solta no
    organograma do mural. Bug real: sem essa checagem, uma pessoa cuja
    orientadora aparece mais adiante na lista virava raiz por conta
    própria E também galho da orientadora, duplicada na tela (achado ao
    vivo: "Camila Deodoro Vasques" repetida, uma vez como raiz e outra
    como orientanda de "Marina Rossetto Cardoso")."""

    def _rodar(self, pessoas, edges):
        fonte = _recorta_3d("temOrientadorVisivel")
        return _no_node(fonte, f"[...temOrientadorVisivel({json.dumps(pessoas)}, {json.dumps(edges)})]")

    def test_quem_tem_orientador_entra_no_conjunto(self):
        pessoas = [{"id": 1}, {"id": 5}]
        edges = [{"from": 1, "to": 5, "kind": "orientacao"}]
        self.assertEqual(self._rodar(pessoas, edges), [5])

    def test_quem_nao_tem_orientador_nenhum_fica_de_fora(self):
        pessoas = [{"id": 1}, {"id": 2}]
        edges = []
        self.assertEqual(self._rodar(pessoas, edges), [])

    def test_aresta_de_coorientacao_tambem_conta(self):
        pessoas = [{"id": 1}, {"id": 9}]
        edges = [{"from": 1, "to": 9, "kind": "coorientacao"}]
        self.assertEqual(self._rodar(pessoas, edges), [9])

    def test_aresta_para_fora_do_organograma_publico_nao_conta(self):
        # o "orientador" nem está na lista de pessoas (ex.: coordenacao
        # sintetica do backend) -- a aresta nao pode fabricar um pai que
        # a tela nao vai desenhar em lugar nenhum
        pessoas = [{"id": 5}]
        edges = [{"from": 99, "to": 5, "kind": "orientacao"}]
        self.assertEqual(self._rodar(pessoas, edges), [])

    def test_outros_tipos_de_aresta_nao_contam(self):
        pessoas = [{"id": 1}, {"id": 2}]
        edges = [{"from": 1, "to": 2, "kind": "colaboracao"}]
        self.assertEqual(self._rodar(pessoas, edges), [])


class TestParetoTemLinhaDeCorteERotulos(unittest.TestCase):
    """`ChartsEnhanced.pareto` -- achado ao vivo: a lâmina "Análise Pareto"
    prometia (no texto ao lado) uma "linha vermelha" marcando o corte de
    80%, e o gráfico nunca desenhava nenhuma linha -- o `pct === 80` exato
    quase nunca bate com contagens inteiras reais. As barras também não
    tinham rótulo nenhum: impossível saber qual linha de pesquisa era
    qual sem adivinhar pela cor."""

    DOM_SHIM = """
    class NoFalso {
      constructor(tag) { this.tag = tag; this.attrs = {}; this.kids = []; this._text = ""; }
      setAttribute(k, v) { this.attrs[k] = String(v); }
      appendChild(kid) { this.kids.push(kid); return kid; }
      set textContent(v) { this._text = String(v); }
      get textContent() { return this._text; }
    }
    global.document = {
      createElementNS: (ns, tag) => new NoFalso(tag),
      createElement: (tag) => new NoFalso(tag),
    };
    function achar(no, tag, filtro) {
      if (no.tag === tag && (!filtro || filtro(no))) return no;
      for (const k of no.kids) { const r = achar(k, tag, filtro); if (r) return r; }
      return null;
    }
    function todos(no, tag, saida) {
      saida = saida || [];
      if (no.tag === tag) saida.push(no);
      no.kids.forEach((k) => todos(k, tag, saida));
      return saida;
    }
    """

    def _grafico(self, dados):
        texto = (TEMPLATES / "charts-enhanced.js").read_text(encoding="utf-8")
        inicio = texto.index("const ChartsEnhanced")
        fim = texto.index("\n})();", inicio) + len("\n})();")
        chart_src = texto[inicio:fim]
        script = (self.DOM_SHIM + "\n" + chart_src
                  + f"\nconst fig = ChartsEnhanced.pareto({json.dumps(dados)});"
                  + "\nconst linhaCorte = todos(fig, 'line').find(function (l) {"
                  + "  return l.attrs.stroke === 'var(--critical)'; });"
                  + "\nconst rotulos = todos(fig, 'text').filter(function (t) {"
                  + "  return t.attrs.transform && t.attrs.transform.indexOf('rotate') !== -1; })"
                  + "  .map(function (t) { return t.textContent; });"
                  + "\nprocess.stdout.write(JSON.stringify({"
                  + "  temLinhaDeCorte: !!linhaCorte, rotulos: rotulos }));")
        return _roda(script)

    def test_a_linha_de_corte_aparece_mesmo_quando_80_por_cento_exato_nunca_bate(self):
        # 45, 34, 33, 26, 22 -- acumulado: 25%,45%,64%,79%,92%: o "===80"
        # exato nunca acontece (79% pula direto para 92%)
        dados = [{"nome": "A", "valor": 45}, {"nome": "B", "valor": 34}, {"nome": "C", "valor": 33},
                 {"nome": "D", "valor": 26}, {"nome": "E", "valor": 22}]
        resultado = self._grafico(dados)
        self.assertTrue(resultado["temLinhaDeCorte"],
                        "a lâmina promete 'linha vermelha' e o gráfico não desenhou nenhuma")

    def test_cada_barra_tem_o_nome_da_linha_como_rotulo(self):
        dados = [{"nome": "Psicologia do exercício e saúde mental", "valor": 45},
                 {"nome": "Treinamento psicológico", "valor": 34},
                 {"nome": "Dor crônica", "valor": 33}]
        resultado = self._grafico(dados)
        self.assertEqual(len(resultado["rotulos"]), 3)
        self.assertTrue(any("Psicologia" in r for r in resultado["rotulos"]))


class TestFunilLiquidoDaProducao(unittest.TestCase):
    """`ChartsEnhanced.funilLiquido` -- substitui a rosca de "Agora no
    laboratório" por um funil líquido (sem nova dependência: só SVG +
    CSS). Cobre o bug achado ao vivo (figura/svg sem a classe que o CSS
    do `.quadro` espera, o que vazava o topo do funil por cima do
    cabeçalho do cartão) e a regra de negócio do nível do tanque."""

    DOM_SHIM = """
    class NoFalso {
      constructor(tag) {
        this.tag = tag; this.attrs = {}; this.kids = []; this._text = "";
        this.style = { setProperty: () => {} };
      }
      setAttribute(k, v) { this.attrs[k] = String(v); }
      appendChild(kid) { this.kids.push(kid); return kid; }
      set textContent(v) { this._text = String(v); }
      get textContent() { return this._text; }
    }
    global.document = {
      createElementNS: (ns, tag) => new NoFalso(tag),
      createElement: (tag) => new NoFalso(tag),
    };
    global.fmt = function (v) { return String(v); };
    function todos(no, tag, saida) {
      saida = saida || [];
      if (no.tag === tag) saida.push(no);
      no.kids.forEach((k) => todos(k, tag, saida));
      return saida;
    }
    """

    def _funil(self, estagios):
        texto = (TEMPLATES / "charts-enhanced.js").read_text(encoding="utf-8")
        inicio = texto.index("const ChartsEnhanced")
        fim = texto.index("\n})();", inicio) + len("\n})();")
        chart_src = texto[inicio:fim]
        script = (self.DOM_SHIM + "\n" + chart_src
                  + f"\nconst fig = ChartsEnhanced.funilLiquido({json.dumps(estagios)});"
                  + "\nif (fig === null) { process.stdout.write(JSON.stringify(null)); }"
                  + "\nelse {"
                  + "\nconst svg = fig.kids[0];"
                  + "\nconst onda = todos(fig, 'path').find(function (p) {"
                  + "  return p.attrs.class === 'onda-liquida'; });"
                  + "\nprocess.stdout.write(JSON.stringify({"
                  + "  figClasse: fig.attrs.class, svgClasse: svg.attrs.class,"
                  + "  textos: todos(fig, 'text').map(function (t) { return t.textContent; }),"
                  + "  ondaD: onda.attrs.d, ondaTitulo: onda.kids[0].textContent }));"
                  + "\n}")
        return _roda(script)

    def test_menos_de_dois_estagios_nao_desenha_nada(self):
        self.assertIsNone(self._funil([{"nome": "A", "valor": 1}]))

    def test_figura_e_svg_levam_as_classes_que_o_css_do_quadro_espera(self):
        # Achado ao vivo: a figura nunca tinha class="chart" e o svg tinha
        # class="chart X" em vez de "plot X" -- as regras `.quadro
        # figure.chart` / `.quadro svg.plot` nunca valiam, e o topo do
        # funil vazava por cima do cabeçalho do cartão.
        estagios = [{"nome": "Em escrita", "valor": 64, "cor": "var(--series-3)"},
                    {"nome": "Com o periódico", "valor": 21, "cor": "var(--series-4)"},
                    {"nome": "Publicados", "valor": 48, "total": 160, "cor": "var(--good)"}]
        resultado = self._funil(estagios)
        self.assertEqual(resultado["figClasse"], "chart")
        self.assertEqual(resultado["svgClasse"], "plot funil-liquido")

    def test_os_tres_valores_aparecem_no_grafico(self):
        estagios = [{"nome": "Em escrita", "valor": 64, "cor": "var(--series-3)"},
                    {"nome": "Com o periódico", "valor": 21, "cor": "var(--series-4)"},
                    {"nome": "Publicados", "valor": 48, "total": 160, "cor": "var(--good)"}]
        resultado = self._funil(estagios)
        self.assertIn("64", resultado["textos"])
        self.assertIn("21", resultado["textos"])
        self.assertIn("48", resultado["textos"])

    def test_nivel_do_tanque_e_fracao_do_total_do_acervo_nao_do_topo_do_funil(self):
        # "Publicados" acumula ao longo de anos -- comparar com a safra
        # atual de "em escrita" faria o tanque passar de 100% cheio, uma
        # leitura sem sentido. O nível certo é publicados / total do
        # acervo (aqui 48/160 = 30%), não publicados / topo do funil
        # (48/64 = 75%, que encheria o tanque quase todo).
        estagios = [{"nome": "Em escrita", "valor": 64, "cor": "x"},
                    {"nome": "Com o periódico", "valor": 21, "cor": "x"},
                    {"nome": "Publicados", "valor": 48, "total": 160, "cor": "x"}]
        resultado = self._funil(estagios)
        primeiro_m = re.match(r"M ([\-\d.]+) ([\-\d.]+)", resultado["ondaD"])
        self.assertIsNotNone(primeiro_m)
        y_onda = float(primeiro_m.group(2))
        y_tanque0, y_tanque1 = 273, 520
        fracao_esperada_pelo_total = 48 / 160
        fracao_esperada_pelo_topo = 48 / 64
        y_pelo_total = y_tanque1 - fracao_esperada_pelo_total * (y_tanque1 - y_tanque0)
        y_pelo_topo = y_tanque1 - fracao_esperada_pelo_topo * (y_tanque1 - y_tanque0)
        self.assertAlmostEqual(y_onda, y_pelo_total, delta=1.0)
        self.assertGreater(abs(y_onda - y_pelo_topo), 20,
                            "o nível não pode estar calculado contra o topo do funil")

    def test_tanque_nunca_fica_totalmente_vazio(self):
        estagios = [{"nome": "Em escrita", "valor": 10, "cor": "x"},
                    {"nome": "Com o periódico", "valor": 5, "cor": "x"},
                    {"nome": "Publicados", "valor": 0, "total": 160, "cor": "x"}]
        resultado = self._funil(estagios)
        self.assertIn("0", resultado["textos"])
        self.assertIn("de", resultado["ondaTitulo"])

    def test_quatro_estagios_mostra_aceitos_como_etapa_propria(self):
        # Achado ao vivo (feedback do Mateus): juntar "em avaliação" e
        # "aceitos" numa etapa só ("com o periódico") escondia informação
        # que os cartões acima do funil já mostram separada -- e com
        # posições fixas de altura, uma 3a etapa no meio (Aceitos) caía
        # numa tira de 24px, texto ilegível. Agora cada etapa recebe a
        # mesma fração da altura do funil, não importa quantas houver.
        estagios = [{"nome": "Em produção", "valor": 16, "cor": "x"},
                    {"nome": "Em avaliação", "valor": 3, "cor": "x"},
                    {"nome": "Aceitos", "valor": 2, "cor": "x"},
                    {"nome": "Publicados", "valor": 112, "total": 133, "cor": "x"}]
        resultado = self._funil(estagios)
        self.assertIn("Aceitos", resultado["textos"])
        self.assertIn("2", resultado["textos"])
        self.assertIn("16", resultado["textos"])
        self.assertIn("3", resultado["textos"])
        self.assertIn("112", resultado["textos"])


class TestLinhaMaisPresente(unittest.TestCase):
    """`linhaMaisPresente` -- o sinal real (não inventado) por trás da
    frase preditiva "Força de trabalho agora": qual linha de pesquisa
    mais aparece entre quem bateu ponto agora, contando o mesmo campo
    `research_line` que o organograma já usa."""

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("linhaMaisPresente")

    def _rodar(self, presentes):
        return _no_node(self.fonte, f"linhaMaisPresente({json.dumps(presentes)})")

    def test_sem_ninguem_presente_nao_ha_destaque(self):
        self.assertEqual(self._rodar([]), {"nome": None, "n": 0})

    def test_a_linha_com_mais_gente_presente_vence(self):
        presentes = [
            {"full_name": "A", "research_line": "Dor crônica"},
            {"full_name": "B", "research_line": "Dor crônica"},
            {"full_name": "C", "research_line": "Fibromialgia"},
        ]
        self.assertEqual(self._rodar(presentes), {"nome": "Dor crônica", "n": 2})

    def test_gente_sem_linha_declarada_agrupa_junto(self):
        presentes = [
            {"full_name": "A", "research_line": None},
            {"full_name": "B", "research_line": None},
        ]
        self.assertEqual(self._rodar(presentes), {"nome": "sem linha declarada", "n": 2})

    def test_uma_pessoa_so_nao_gera_destaque_de_linha(self):
        # A tela só mostra a leitura quando destaque.n >= 2 -- uma pessoa
        # sozinha não é "força de trabalho" de linha nenhuma.
        presentes = [{"full_name": "A", "research_line": "Dor crônica"}]
        self.assertEqual(self._rodar(presentes), {"nome": "Dor crônica", "n": 1})


class TestTemPotencialAlto(unittest.TestCase):
    """`temPotencialAlto` -- o sinal por trás da esfera piscando em ciano
    na dispersão 3D de "Citações e produção por área": sempre calculado
    (publicados <= 1 e produção > 0), nunca uma lista de nomes escolhida
    a dedo."""

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("temPotencialAlto")

    def _rodar(self, linha):
        return _no_node(self.fonte, f"temPotencialAlto({json.dumps(linha)})")

    def test_poucos_publicados_e_producao_em_andamento_e_destaque(self):
        self.assertTrue(self._rodar({"publicados": 0, "producao": 3}))
        self.assertTrue(self._rodar({"publicados": 1, "producao": 1}))

    def test_ja_publicou_bastante_nao_e_destaque_mesmo_com_producao(self):
        self.assertFalse(self._rodar({"publicados": 5, "producao": 3}))

    def test_pouco_publicado_mas_sem_producao_nao_e_destaque(self):
        # A linha parada não é "observem essa linha" -- é só uma linha
        # pequena, sem sinal nenhum de que algo está para sair dela.
        self.assertFalse(self._rodar({"publicados": 0, "producao": 0}))

    def test_campos_ausentes_nao_quebram(self):
        self.assertFalse(self._rodar({}))


class TestFraseMetaPublicacoes(unittest.TestCase):
    """`fraseMetaPublicacoes` -- a projeção de fim de ano do painel de
    insights. A frase segue sempre o `veredito` que vem pronto do
    back-end (metas.py): a tela nunca decide sozinha se "vai bater a
    meta", só traduz o veredito calculado lá em texto."""

    @classmethod
    def setUpClass(cls):
        cls.fonte = "global.fmt = function (v) { return String(v); };\n" + _recorta("fraseMetaPublicacoes")

    def _rodar(self, meta):
        return _no_node(self.fonte, f"fraseMetaPublicacoes({json.dumps(meta)})")

    def test_sem_meta_nenhuma_nao_quebra(self):
        self.assertIsNone(self._rodar(None))

    def test_sem_meta_declarada_ainda_mostra_a_projecao_em_faixa(self):
        meta = {"veredito": "sem meta declarada", "meta": None, "realizado": 12,
                "projecao": {"de": 14, "ate": 24, "central": 19}}
        frase = self._rodar(meta)
        self.assertIn("sem meta anual declarada", frase)
        self.assertIn("entre 14 e 24", frase)
        # nunca um numero so, sempre a faixa -- mesma regra do metas.py
        self.assertNotIn("19", frase)

    def test_meta_ja_alcancada(self):
        meta = {"veredito": "alcançada", "meta": 20, "realizado": 22, "projecao": {}}
        frase = self._rodar(meta)
        self.assertIn("já alcançada", frase)
        self.assertIn("22", frase)

    def test_no_ritmo_atual_alcanca(self):
        meta = {"veredito": "no ritmo atual, alcança", "meta": 15, "realizado": 10,
                "projecao": {"de": 16, "ate": 22}}
        frase = self._rodar(meta)
        self.assertIn("deve ser alcançada", frase)
        self.assertIn("entre 16 e 22", frase)

    def test_no_ritmo_atual_nao_alcanca_e_bem_explicito(self):
        meta = {"veredito": "no ritmo atual, não alcança", "meta": 40, "realizado": 10,
                "projecao": {"de": 16, "ate": 22}}
        frase = self._rodar(meta)
        self.assertIn("NÃO deve ser alcançada", frase)


class TestGaugeDeDiagnostico(unittest.TestCase):
    """`ChartsEnhanced.gaugeDiagnostico` -- o mostrador da taxa de aceite
    no painel de insights. Crítico é decidido por quem chama (nunca
    aqui dentro), e só troca a classe/cor -- a tela real nunca inventa
    um alarme por conta própria."""

    DOM_SHIM = """
    class NoFalso {
      constructor(tag) { this.tag = tag; this.attrs = {}; this.kids = []; this._text = ""; }
      setAttribute(k, v) { this.attrs[k] = String(v); }
      appendChild(kid) { this.kids.push(kid); return kid; }
      set textContent(v) { this._text = String(v); }
      get textContent() { return this._text; }
    }
    global.document = {
      createElementNS: (ns, tag) => new NoFalso(tag),
      createElement: (tag) => new NoFalso(tag),
    };
    global.fmt = function (v) { return String(v); };
    function todos(no, tag, saida) {
      saida = saida || [];
      if (no.tag === tag) saida.push(no);
      no.kids.forEach((k) => todos(k, tag, saida));
      return saida;
    }
    """

    def _gauge(self, valor, opts=None):
        texto = (TEMPLATES / "charts-enhanced.js").read_text(encoding="utf-8")
        inicio = texto.index("const ChartsEnhanced")
        fim = texto.index("\n})();", inicio) + len("\n})();")
        chart_src = texto[inicio:fim]
        valor_js = "null" if valor is None else json.dumps(valor)
        script = (self.DOM_SHIM + "\n" + chart_src
                  + f"\nconst fig = ChartsEnhanced.gaugeDiagnostico({valor_js}, {json.dumps(opts or {})});"
                  + "\nconst svg = fig.kids[0];"
                  + "\nconst arcoValor = todos(fig, 'path').find(function (p) {"
                  + "  return p.attrs.class === 'gauge-arco-valor'; });"
                  + "\nprocess.stdout.write(JSON.stringify({"
                  + "  svgClasse: svg.attrs.class,"
                  + "  temArcoValor: !!arcoValor,"
                  + "  dashArray: arcoValor ? arcoValor.attrs['stroke-dasharray'] : null,"
                  + "  textos: todos(fig, 'text').map(function (t) { return t.textContent; }) }));")
        return _roda(script)

    def test_svg_leva_a_classe_critico_so_quando_pedido(self):
        normal = self._gauge(45, {"rotulo": "Taxa de aceite"})
        self.assertNotIn("gauge-critico", normal["svgClasse"])
        critico = self._gauge(0, {"rotulo": "Taxa de aceite", "critico": True})
        self.assertIn("gauge-critico", critico["svgClasse"])

    def test_sem_dado_nao_desenha_arco_de_valor(self):
        resultado = self._gauge(None, {"rotulo": "Taxa de aceite"})
        self.assertFalse(resultado["temArcoValor"])
        self.assertIn("sem dado", resultado["textos"])

    def test_arco_de_valor_preenche_a_fracao_certa(self):
        resultado = self._gauge(30, {"rotulo": "Taxa de aceite"})
        self.assertEqual(resultado["dashArray"], "30 70")

    def test_numero_e_rotulo_aparecem(self):
        resultado = self._gauge(62, {"rotulo": "Taxa de aceite"})
        self.assertIn("62%", resultado["textos"])
        self.assertIn("Taxa de aceite", resultado["textos"])


class TestGloboNeonDoPeloMundo(unittest.TestCase):
    """`ChartsEnhanced.globoNeon` -- quarto item da lista de upgrades
    visuais: as duas telas de internacionalização viram uma só, com um
    globo (projeção ortográfica de verdade, a mesma matemática do globo
    do ao vivo) e arcos de voo saindo da sede, sem depender de nada
    novo (a "girada" é CSS puro, ver mural.html)."""

    DOM_SHIM = """
    class NoFalso {
      constructor(tag) {
        this.tag = tag; this.attrs = {}; this.kids = []; this._text = "";
        this.style = { _props: {}, setProperty(k, v) { this._props[k] = v; } };
      }
      setAttribute(k, v) { this.attrs[k] = String(v); }
      appendChild(kid) { this.kids.push(kid); return kid; }
      set textContent(v) { this._text = String(v); }
      get textContent() { return this._text; }
    }
    global.document = {
      createElementNS: (ns, tag) => new NoFalso(tag),
      createElement: (tag) => new NoFalso(tag),
    };
    global.fmt = function (v) { return String(v); };
    function todos(no, tag, saida) {
      saida = saida || [];
      if (no.tag === tag) saida.push(no);
      no.kids.forEach((k) => todos(k, tag, saida));
      return saida;
    }
    """

    def _globo(self, sede, paises):
        texto = (TEMPLATES / "charts-enhanced.js").read_text(encoding="utf-8")
        inicio = texto.index("const ChartsEnhanced")
        fim = texto.index("\n})();", inicio) + len("\n})();")
        chart_src = texto[inicio:fim]
        script = (self.DOM_SHIM + "\n" + chart_src
                  + f"\nconst fig = ChartsEnhanced.globoNeon({json.dumps(sede)}, {json.dumps(paises)});"
                  + "\nif (fig === null) { process.stdout.write(JSON.stringify(null)); }"
                  + "\nelse {"
                  + "\nconst arcos = todos(fig, 'path').filter(function (p) { return p.attrs.class === 'globo-neon-arco'; });"
                  + "\nconst pontos = todos(fig, 'circle').filter(function (c) { return c.attrs.class === 'globo-neon-pais'; });"
                  + "\nprocess.stdout.write(JSON.stringify({"
                  + "  figClasse: fig.attrs.class, svgClasse: fig.kids[0].attrs.class,"
                  + "  nArcos: arcos.length, nPontos: pontos.length,"
                  + "  larguras: arcos.map(function (a) { return a.attrs['stroke-width']; }),"
                  + "  titulos: todos(fig, 'title').map(function (t) { return t.textContent; }) }));"
                  + "\n}")
        return _roda(script)

    def test_sem_pais_nenhum_nao_desenha_nada(self):
        self.assertIsNone(self._globo({"nome": "UDESC", "latitude": -27.6, "longitude": -48.5}, []))

    def test_figura_e_svg_levam_as_classes_que_o_css_do_quadro_espera(self):
        sede = {"nome": "UDESC", "latitude": -27.6, "longitude": -48.5}
        paises = [{"pais": "Itália", "iso": "IT", "n": 29, "latitude": 41.9, "longitude": 12.5}]
        resultado = self._globo(sede, paises)
        self.assertEqual(resultado["figClasse"], "chart")
        self.assertEqual(resultado["svgClasse"], "plot globo-neon")

    def test_um_arco_e_um_ponto_por_pais(self):
        sede = {"nome": "UDESC", "latitude": -27.6, "longitude": -48.5}
        paises = [
            {"pais": "Itália", "iso": "IT", "n": 29, "latitude": 41.9, "longitude": 12.5},
            {"pais": "Canadá", "iso": "CA", "n": 2, "latitude": 56.1, "longitude": -106.3},
        ]
        resultado = self._globo(sede, paises)
        self.assertEqual(resultado["nArcos"], 2)
        self.assertEqual(resultado["nPontos"], 2)

    def test_espessura_do_arco_e_proporcional_ao_volume_de_artigos(self):
        # O pedido original: "a linha para a Itália com mais artigos deve
        # ser um feixe mais grosso que a de um país com poucos artigos".
        sede = {"nome": "UDESC", "latitude": -27.6, "longitude": -48.5}
        paises = [
            {"pais": "Itália", "iso": "IT", "n": 29, "latitude": 41.9, "longitude": 12.5},
            {"pais": "Canadá", "iso": "CA", "n": 2, "latitude": 56.1, "longitude": -106.3},
        ]
        resultado = self._globo(sede, paises)
        larguras = [float(x) for x in resultado["larguras"]]
        self.assertGreater(larguras[0], larguras[1])

    def test_pais_sem_coordenada_e_ignorado_sem_quebrar(self):
        sede = {"nome": "UDESC", "latitude": -27.6, "longitude": -48.5}
        paises = [
            {"pais": "Itália", "iso": "IT", "n": 29, "latitude": 41.9, "longitude": 12.5},
            {"pais": "Sem coordenada", "iso": None, "n": 3, "latitude": None, "longitude": None},
        ]
        resultado = self._globo(sede, paises)
        self.assertEqual(resultado["nArcos"], 1)
        self.assertEqual(resultado["nPontos"], 1)


class TestFeedEmCascata(unittest.TestCase):
    """`feedCascata` -- o Top 6 em estilo log de servidor, ao lado do
    globo em "Pelo mundo"."""

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("feedCascata")

    def _rodar(self, paises):
        return _no_node(
            'global.el = (tag, attrs, kids) => ({ tag, attrs, kids });\n'
            'global.fmt = (v) => String(v);\n'
            'global.Icons = { get: () => null };\n'
            + self.fonte,
            f"feedCascata({json.dumps(paises)})")

    def test_corta_no_top_6_mesmo_com_mais_paises(self):
        paises = [{"pais": f"País {i}", "n": 10 - i} for i in range(10)]
        resultado = self._rodar(paises)
        self.assertEqual(len(resultado["kids"]), 6)

    def test_com_menos_de_6_paises_mostra_todos(self):
        paises = [{"pais": "Itália", "n": 29}, {"pais": "Canadá", "n": 2}]
        resultado = self._rodar(paises)
        self.assertEqual(len(resultado["kids"]), 2)


class TestRaioOrbitaLinha(unittest.TestCase):
    """`raioOrbitaLinha` -- quinto e último item da lista de upgrades
    visuais: a distância de cada planeta ao centro, controlada pelo
    impacto real (artigos + citações), não mais um raio fixo igual para
    todo mundo."""

    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta_3d("raioOrbitaLinha")

    def _rodar(self, linha, maior_impacto, raio_min, raio_max):
        return _no_node(self.fonte,
            f"raioOrbitaLinha({json.dumps(linha)}, {maior_impacto}, {raio_min}, {raio_max})")

    def test_quem_lidera_em_impacto_orbita_mais_perto_do_centro(self):
        lider = {"artigos": 45, "citacoes": 120}
        pequena = {"artigos": 2, "citacoes": 0}
        maior_impacto = 45 + 120
        raio_lider = self._rodar(lider, maior_impacto, 100, 300)
        raio_pequena = self._rodar(pequena, maior_impacto, 100, 300)
        self.assertLess(raio_lider, raio_pequena)

    def test_o_lider_de_verdade_fica_no_raio_minimo(self):
        lider = {"artigos": 45, "citacoes": 120}
        raio = self._rodar(lider, 45 + 120, 100, 300)
        self.assertAlmostEqual(raio, 100, delta=0.01)

    def test_impacto_zero_fica_no_raio_maximo(self):
        vazia = {"artigos": 0, "citacoes": 0}
        raio = self._rodar(vazia, 165, 100, 300)
        self.assertAlmostEqual(raio, 300, delta=0.01)

    def test_nunca_sai_da_faixa_mesmo_com_impacto_maior_que_o_maior_impacto(self):
        # maiorImpacto vem de Math.max(...linhas) no chamador -- não pode
        # estourar aqui, mas a função não confia cegamente no chamador.
        estranha = {"artigos": 999, "citacoes": 999}
        raio = self._rodar(estranha, 10, 100, 300)
        self.assertGreaterEqual(raio, 100)
        self.assertLessEqual(raio, 300)
