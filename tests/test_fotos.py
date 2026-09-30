#!/usr/bin/env python3
"""Testes da foto de perfil de integrante.

    python3 -m unittest tests.test_fotos -v

Mesmo risco de `marca.py`, num arquivo por pessoa em vez de um só para o
laboratório: um data: URI mal formado ou grande demais nunca pode entrar
em `members.photo_url`, porque ele viaja embutido em cada página, no
cartão de chegada do mural e no instantâneo por e-mail.
"""
from __future__ import annotations

import base64
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import fotos  # noqa: E402

PNG_MINIMO = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmM"
    "IQAAAABJRU5ErkJggg==")
SVG_MINIMO = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>'


def uri(bruto, prefixo="data:image/png;base64,"):
    return prefixo + base64.b64encode(bruto).decode()


class TestGravarAFoto(unittest.TestCase):
    def test_um_png_valido_vira_data_uri_pronto(self):
        resultado = fotos.gravar(uri(PNG_MINIMO))
        self.assertTrue(resultado.startswith("data:image/png;base64,"))
        dentro = resultado.split("base64,", 1)[1]
        self.assertEqual(base64.b64decode(dentro), PNG_MINIMO)

    def test_a_extensao_vem_dos_bytes_e_nao_do_prefixo_declarado(self):
        # um PNG anunciado como se fosse outra coisa ainda tem de virar PNG --
        # confiar no prefixo do navegador seria confiar em quem pode mentir
        resultado = fotos.gravar(uri(PNG_MINIMO, "data:image/jpeg;base64,"))
        self.assertTrue(resultado.startswith("data:image/png;base64,"))

    def test_svg_e_recusado_mesmo_sendo_imagem_valida(self):
        # SVG serve a um logotipo (marca.py aceita), mas não a uma foto de
        # rosto -- e um SVG pode trazer <script> embutido
        with self.assertRaises(fotos.Recusado) as caso:
            fotos.gravar(uri(SVG_MINIMO, "data:image/svg+xml;base64,"))
        self.assertIn("SVG", str(caso.exception))

    def test_gif_e_recusado_dizendo_que_e_gif(self):
        with self.assertRaises(fotos.Recusado) as caso:
            fotos.gravar(uri(b"GIF89a" + b"\x00" * 20))
        self.assertIn("GIF", str(caso.exception))

    def test_o_que_nao_e_imagem_e_recusado(self):
        with self.assertRaises(fotos.Recusado):
            fotos.gravar(uri(b"nao sou imagem nenhuma"))

    def test_grande_demais_e_recusado_com_o_limite_na_mensagem(self):
        # o teto aqui e bem menor que o da marca: uma foto por PESSOA, nao
        # uma so para o laboratorio inteiro
        with self.assertRaises(fotos.Recusado) as caso:
            fotos.gravar(uri(b"\x89PNG\r\n\x1a\n" + b"x" * fotos.LIMITE_BYTES))
        self.assertIn("kB", str(caso.exception))
        self.assertLess(fotos.LIMITE_BYTES, 512 * 1024)  # bem abaixo do teto da marca

    def test_bem_no_limite_ainda_entra(self):
        resultado = fotos.gravar(uri(b"\x89PNG\r\n\x1a\n" + b"x" * (fotos.LIMITE_BYTES - 8)))
        self.assertTrue(resultado.startswith("data:image/png;base64,"))

    def test_vazio_e_corrompido_sao_recusados(self):
        for ruim in ("", "data:image/png;base64,", "data:image/png;base64,%%%"):
            with self.subTest(entrada=ruim):
                with self.assertRaises(fotos.Recusado):
                    fotos.gravar(ruim)


class TestARotaDaFoto(unittest.TestCase):
    """Quem pode trocar a foto de quem, e o que a tela recebe de volta."""

    def setUp(self):
        self.fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")

    def test_a_rota_esta_registrada_para_qualquer_integrante(self):
        # o MINIMO da rota e "integrante" -- quem decide se pode mexer na
        # foto de OUTRA pessoa e o corpo da funcao, checando coordenacao
        self.assertIn(
            '("POST", r"^/api/members/foto/?$", route_member_foto, "integrante")',
            self.fonte)

    def test_so_a_propria_pessoa_ou_coordenacao_troca_a_foto(self):
        corpo = self.fonte[self.fonte.index("def route_member_foto"):
                            self.fonte.index("def route_curva")]
        self.assertIn('ROLE_RANK["coordenacao"]', corpo)
        self.assertIn("ApiError(403", corpo)

    def test_a_recusa_vira_400_e_nao_500(self):
        corpo = self.fonte[self.fonte.index("def route_member_foto"):
                            self.fonte.index("def route_curva")]
        self.assertIn("except fotos.Recusado", corpo)
        self.assertIn("ApiError(400", corpo)


if __name__ == "__main__":
    unittest.main()
