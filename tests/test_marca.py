#!/usr/bin/env python3
"""Testes do logotipo do laboratorio.

    python3 -m unittest tests.test_marca -v

A marca aparece em cinco telas de tamanhos diferentes e em dois arquivos
que viajam sozinhos -- o instantaneo que vai por e-mail e o mural que roda
numa TV sem rede. O modo de errar aqui e sempre o mesmo: a imagem some, e
some CALADA, porque um <img> quebrado nao da erro nenhum na pagina.
"""
from __future__ import annotations

import base64
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import marca  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"

PNG_MINIMO = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmM"
    "IQAAAABJRU5ErkJggg==")
SVG_MINIMO = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>'


class BaseMarca(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pasta = Path(self.tmp.name)
        self.trocar(marca.config, "DATA_DIR", self.pasta)
        self.trocar(marca.config, "LOGO_PATH", "")
        marca._cache.clear()
        self.addCleanup(marca._cache.clear)

    def trocar(self, alvo, nome, valor):
        antigo = getattr(alvo, nome)
        setattr(alvo, nome, valor)
        self.addCleanup(setattr, alvo, nome, antigo)

    def por(self, nome, conteudo=PNG_MINIMO):
        alvo = self.pasta / nome
        alvo.write_bytes(conteudo)
        marca._cache.clear()
        return alvo


class TestOndeSeProcura(BaseMarca):
    def test_sem_arquivo_a_marca_continua_sendo_as_duas_letras(self):
        # nunca um <img> vazio nem um buraco: a marca fica na tela o tempo
        # todo, e um espaco em branco no canto e a primeira coisa que se ve
        self.assertIsNone(marca.caminho())
        self.assertIsNone(marca.fonte())
        self.assertEqual(marca.marcador(), "LP")

    def test_acha_o_arquivo_na_pasta_de_dados(self):
        alvo = self.por("logo.png")
        self.assertEqual(marca.caminho(), alvo)
        self.assertTrue(marca.fonte().startswith("data:image/png;base64,"))

    def test_o_svg_ganha_do_png(self):
        """Ordem, e não sorte: com dois arquivos, um deles tem de vencer.

        O SVG é o que não perde nitidez no mural, que roda numa tela grande.
        """
        self.por("logo.png")
        self.por("logo.svg", SVG_MINIMO)
        self.assertEqual(marca.caminho().name, "logo.svg")
        self.assertTrue(marca.fonte().startswith("data:image/svg+xml;base64,"))

    def test_a_variavel_de_ambiente_manda_mais(self):
        self.por("logo.png")
        outro = self.pasta / "outro-lugar.png"
        outro.write_bytes(PNG_MINIMO)
        self.trocar(marca.config, "LOGO_PATH", str(outro))
        marca._cache.clear()
        self.assertEqual(marca.caminho(), outro)

    def test_variavel_apontando_para_o_nada_nao_derruba_a_tela(self):
        self.trocar(marca.config, "LOGO_PATH", str(self.pasta / "nao-existe.png"))
        marca._cache.clear()
        self.assertIsNone(marca.caminho())
        self.assertEqual(marca.marcador(), "LP")


class TestComoAImagemViaja(BaseMarca):
    def test_vai_embutida_e_nao_como_endereco(self):
        """O instantâneo é um arquivo só, e o mural pode rodar sem rede.

        Um <img src="/logo.png"> sumiria dos dois -- e sumiria calado, que
        é o pior jeito de sumir.
        """
        self.por("logo.png")
        html = marca.marcador()
        self.assertIn("data:image/png;base64,", html)
        self.assertNotIn('src="/', html)

    def test_o_conteudo_embutido_e_o_arquivo(self):
        self.por("logo.png")
        dentro = marca.fonte().split("base64,", 1)[1]
        self.assertEqual(base64.b64decode(dentro), PNG_MINIMO)

    def test_o_nome_do_laboratorio_vira_o_texto_alternativo(self):
        self.por("logo.png")
        self.assertIn('alt="', marca.marcador())
        self.assertIn('alt="Um lab qualquer"', marca.marcador("Um lab qualquer"))

    def test_aspas_no_nome_nao_quebram_a_marcacao(self):
        self.por("logo.png")
        html = marca.marcador('Lab "das aspas"')
        self.assertNotIn('alt="Lab "das', html)
        self.assertIn("&quot;", html)


class TestOArquivoGrandeDemais(BaseMarca):
    def test_passar_do_limite_e_recusado_com_motivo(self):
        """Um logotipo de 4 MB engordaria TODA página e todo instantâneo.

        Aceitar em silêncio seria transformar um arquivo pesado num sistema
        lento sem ninguém conseguir ligar uma coisa à outra.
        """
        self.por("logo.png", b"x" * (marca.LIMITE_BYTES + 1))
        self.assertIsNone(marca.fonte())
        self.assertEqual(marca.marcador(), "LP")
        situacao = marca.situacao()
        self.assertFalse(situacao["tem"])
        self.assertIn("limite", situacao["erro"])

    def test_bem_no_limite_ainda_entra(self):
        self.por("logo.png", b"x" * marca.LIMITE_BYTES)
        self.assertIsNotNone(marca.fonte())


class TestOCacheNaoEnvelhece(BaseMarca):
    def test_trocar_o_arquivo_troca_a_marca(self):
        # sem olhar mtime e tamanho, quem trocasse o logotipo veria o antigo
        # ate reiniciar o sistema -- e reiniciaria sem saber que era isso
        self.por("logo.png", PNG_MINIMO)
        antes = marca.fonte()
        marca._cache.clear()
        (self.pasta / "logo.png").write_bytes(PNG_MINIMO + b"\x00")
        depois = marca.fonte()
        self.assertNotEqual(antes, depois)

    def test_ler_duas_vezes_nao_le_o_disco_duas_vezes(self):
        self.por("logo.png")
        primeira = marca.logo()
        self.assertIs(marca.logo(), primeira)


class TestAsTelasQueUsam(unittest.TestCase):
    """Os cinco lugares onde a marca aparece pedem o logotipo."""

    def test_todo_modelo_html_tem_o_marcador(self):
        for nome in ("dashboard.html", "app.html", "login.html", "convite.html"):
            with self.subTest(modelo=nome):
                texto = (TEMPLATES / nome).read_text(encoding="utf-8")
                self.assertIn("__LOGO__", texto)
                # o "LP" cru nao pode ter sobrado ao lado do marcador
                self.assertNotIn('class="logo">LP<', texto)

    def test_quem_serve_troca_o_marcador(self):
        """`__LOGO__` que sobra na página é a palavra impressa na tela.

        É o mesmo risco do `__DATA__`, e por isso vale um teste próprio.
        """
        for arquivo in ("api.py", "report.py"):
            with self.subTest(onde=arquivo):
                fonte = (ROOT / "scripts" / "lape" / arquivo).read_text(encoding="utf-8")
                self.assertIn('replace("__LOGO__", marca.marcador())', fonte)

    def test_o_mural_e_o_panorama_leem_do_payload(self):
        # essas duas montam a marca no navegador, e nao no modelo
        mural = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        self.assertIn("o.lab_logo", mural)
        self.assertIn('Icons.get("mural"', mural)      # o plano B continua lá
        panorama = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        self.assertIn("D.laboratorio.logo", panorama)
        self.assertIn('text: "LP"', panorama)

    def test_a_imagem_cabe_sem_deformar(self):
        """`contain`, e nunca `cover`.

        Um logotipo cortado ao meio para preencher o quadrado é pior do que
        um logotipo com margem -- e o corte cai justamente no desenho.
        """
        css = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
        regra = css[css.index(".logo-img {"):]
        regra = regra[:regra.index("}")]
        self.assertIn("object-fit: contain", regra)
        self.assertNotIn("cover", regra)

    def test_a_placa_branca_e_declarada_nos_dois_temas(self):
        # arte preta sobre fundo transparente some por inteiro no tema
        # escuro; a placa custa uma moldura, a falta dela custa a marca
        css = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
        self.assertIn(".logo-img { background: #fff; }", css)
        # e sem seguir o tema do sistema: o painel e escuro por padrao
        self.assertNotIn("prefers-color-scheme: light", css)


class TestReceberPelaTela(BaseMarca):
    """A imagem entra pelo navegador, de onde ela já está.

    "Abra o terminal e copie o arquivo para a pasta data" é um pedido que
    não se atende sozinho -- e quem cuida do laboratório usa este sistema
    pelo navegador, num computador Windows.
    """

    def uri(self, bruto, prefixo="data:image/png;base64,"):
        return prefixo + base64.b64encode(bruto).decode()

    def test_grava_o_png_com_a_extensao_certa(self):
        marca.gravar(self.uri(PNG_MINIMO))
        self.assertTrue((self.pasta / "logo.png").is_file())
        self.assertEqual((self.pasta / "logo.png").read_bytes(), PNG_MINIMO)

    def test_a_extensao_vem_dos_bytes_e_nao_do_nome(self):
        """Um PNG anunciado como SVG viraria data/logo.svg -- e um <img>
        quebrado, que não dá erro nenhum na página.
        """
        marca.gravar(self.uri(PNG_MINIMO, "data:image/svg+xml;base64,"))
        self.assertTrue((self.pasta / "logo.png").is_file())
        self.assertFalse((self.pasta / "logo.svg").exists())

    def test_o_svg_e_reconhecido_mesmo_com_declaracao_xml(self):
        bruto = b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"></svg>'
        marca.gravar(self.uri(bruto))
        self.assertTrue((self.pasta / "logo.svg").is_file())

    def test_o_arquivo_novo_apaga_o_antigo(self):
        """A procura tem ordem: SVG vence PNG.

        Sem apagar, quem enviasse um PNG novo continuaria vendo o SVG velho
        -- e não haveria nada na tela explicando por quê.
        """
        marca.gravar(self.uri(SVG_MINIMO))
        self.assertTrue((self.pasta / "logo.svg").is_file())
        marca.gravar(self.uri(PNG_MINIMO))
        self.assertFalse((self.pasta / "logo.svg").exists())
        self.assertTrue((self.pasta / "logo.png").is_file())
        self.assertEqual(marca.caminho().name, "logo.png")

    def test_o_que_nao_e_imagem_e_recusado_com_nome(self):
        with self.assertRaises(marca.Recusado) as caso:
            marca.gravar(self.uri(b"nao sou imagem nenhuma"))
        self.assertIn("PNG", str(caso.exception))
        self.assertEqual(list(self.pasta.iterdir()), [])

    def test_gif_e_recusado_dizendo_que_e_gif(self):
        # recusar "não reconheci" um formato que se reconhece perfeitamente
        # manda a pessoa procurar defeito no arquivo dela
        with self.assertRaises(marca.Recusado) as caso:
            marca.gravar(self.uri(b"GIF89a" + b"\x00" * 20))
        self.assertIn("GIF", str(caso.exception))

    def test_grande_demais_e_recusado_antes_de_gravar(self):
        with self.assertRaises(marca.Recusado) as caso:
            marca.gravar(self.uri(b"\x89PNG\r\n\x1a\n" + b"x" * marca.LIMITE_BYTES))
        self.assertIn("limite", str(caso.exception))
        self.assertEqual(list(self.pasta.iterdir()), [])

    def test_vazio_e_corrompido_nao_viram_arquivo(self):
        for ruim in ("", "data:image/png;base64,", "data:image/png;base64,%%%"):
            with self.subTest(entrada=ruim):
                with self.assertRaises(marca.Recusado):
                    marca.gravar(ruim)
        self.assertEqual(list(self.pasta.iterdir()), [])

    def test_remover_devolve_as_duas_letras(self):
        marca.gravar(self.uri(PNG_MINIMO))
        self.assertTrue(marca.situacao()["tem"])
        marca.remover()
        self.assertFalse(marca.situacao()["tem"])
        self.assertEqual(marca.marcador(), "LP")

    def test_remover_sem_nada_para_remover_nao_quebra(self):
        self.assertFalse(marca.remover()["tem"])


class TestAsRotasDaMarca(unittest.TestCase):
    """Quem pode trocar a marca, e o que a tela recebe de volta."""

    def test_a_rota_de_gravar_pede_coordenacao(self):
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        self.assertIn('("POST", r"^/api/marca/?$", route_marca_gravar, "coordenacao")',
                      fonte)
        self.assertIn('("GET", r"^/api/marca/?$", route_marca, "leitura")', fonte)

    def test_a_recusa_vira_400_e_nao_500(self):
        # erro de arquivo é do usuário, não do servidor: 500 mandaria a
        # pessoa procurar defeito no sistema em vez de no arquivo
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        corpo = fonte[fonte.index("def route_marca_gravar"):fonte.index("def route_citacoes")]
        self.assertIn("except marca.Recusado", corpo)
        self.assertIn("ApiError(400", corpo)

    def test_a_tela_confere_o_tamanho_antes_de_mandar(self):
        # mandar 4 MB pela rede para ouvir "não" é uma espera evitável
        js = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        corpo = js[js.index("function cartaoDaMarca"):js.index("function verLaboratorio")]
        self.assertIn("arquivo.size >", corpo)
        self.assertIn("readAsDataURL", corpo)
        self.assertIn('api("/api/marca", "POST"', corpo)
