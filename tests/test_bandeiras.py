#!/usr/bin/env python3
"""Testes das bandeiras desenhadas.

    python3 -m unittest tests.test_bandeiras -v

O Windows nao tem bandeira de pais no conjunto de emoji. O Segoe UI Emoji
desenha o par de indicadores regionais (BR = U+1F1E7 U+1F1F7) como as duas
LETRAS, e foi isso que apareceu na tela do laboratorio: "US", "BR", "AU"
onde deviam estar as bandeiras. Nenhum ajuste de CSS muda isso, e nenhuma
fonte padrao do Windows traz esses simbolos.

Por isso o desenho e feito em SVG, sem rede e sem fonte externa: o sistema
roda numa maquina que pode estar sem internet, e bandeira que depende de
CDN e bandeira que some.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
BANDEIRAS = TEMPLATES / "bandeiras.js"
NODE = shutil.which("node")


class TestOCodigoDoPais(unittest.TestCase):
    """`iso2` sai a parte do emoji porque e DELE que a tela desenha."""

    def test_devolve_o_codigo_de_duas_letras(self):
        from lape.variaveis import iso2
        self.assertEqual(iso2("Brasil"), "BR")
        self.assertEqual(iso2("Estados Unidos"), "US")

    def test_pais_desconhecido_devolve_vazio(self):
        from lape.variaveis import iso2
        self.assertEqual(iso2("Atlântida"), "")
        self.assertEqual(iso2(None), "")

    def test_o_emoji_continua_saindo_do_mesmo_codigo(self):
        # uma segunda tabela divergiria da primeira
        from lape.variaveis import bandeira, iso2
        self.assertTrue(bandeira("Brasil"))
        self.assertEqual(len(bandeira("Brasil")), 2)   # dois indicadores
        self.assertTrue(iso2("Brasil"))

    def test_o_codigo_viaja_com_os_paises_do_painel(self):
        fonte = (ROOT / "scripts" / "lape" / "analise.py").read_text(encoding="utf-8")
        self.assertIn('"iso": variaveis.iso2(', fonte)

    def test_o_codigo_viaja_com_os_paises_da_biblioteca(self):
        fonte = (ROOT / "scripts" / "lape" / "biblioteca.py").read_text(encoding="utf-8")
        self.assertIn('"iso": iso2(pais)', fonte)


class TestODesenho(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.js = BANDEIRAS.read_text(encoding="utf-8")

    def desenhadas(self):
        return set(re.findall(r"^    ([A-Z]{2}):", self.js, re.M))

    def test_os_paises_do_acervo_tem_desenho(self):
        """Os que apareceram na tela do laboratorio, um por um."""
        for iso in ("US", "BR", "AU", "ES", "TN", "IT", "FR", "JP", "CA", "DE",
                    "CN", "GB", "NZ", "QA", "PT", "IE", "PL", "CL", "SE", "CH",
                    "NL", "RO", "NO", "BE"):
            with self.subTest(pais=iso):
                self.assertIn(iso, self.desenhadas())

    def test_a_noruega_nao_e_a_dinamarca(self):
        """A cruz da Noruega e AZUL sobre contorno branco.

        Com branco nos dois, as duas bandeiras saiam identicas -- e uma
        bandeira trocada por outra e pior do que nenhuma bandeira.
        """
        linha = re.search(r"NO: nordica\(([^)]+)\)", self.js).group(1)
        self.assertIn("#00205b", linha)
        dinamarca = re.search(r"DK: nordica\(([^)]+)\)", self.js).group(1)
        self.assertNotEqual(linha, dinamarca)

    def sem_comentario(self):
        """O codigo sem os comentarios.

        A primeira versao deste teste procurava a palavra "cdn" no arquivo
        inteiro e acusava o proprio comentario que explica por que nao ha
        CDN nenhum. Um teste que so passa se a gente parar de escrever
        sobre o assunto nao esta medindo o codigo.
        """
        sem_bloco = re.sub(r"/\*.*?\*/", " ", self.js, flags=re.S)
        # o (?<!:) e obrigatorio: "http://" termina em // e a primeira
        # versao deste apagador comia o namespace do SVG, deixando o
        # teste do endereco passar por nao achar endereco nenhum
        return re.sub(r"(?<!:)//[^\n]*", " ", sem_bloco)

    def test_nao_busca_nada_na_rede(self):
        """Bandeira que depende de CDN e bandeira que some.

        A maquina do laboratorio pode estar sem internet, e o instantaneo
        viaja por e-mail. O que importa nao e a palavra "http" aparecer --
        o namespace do SVG e obrigatorio e e um identificador, nunca um
        endereco que o navegador visita. O que importa e o arquivo pedir
        alguma coisa para fora enquanto desenha.
        """
        codigo = self.sem_comentario()
        for proibido in ("@import", "twemoji", "fetch(", "XMLHttpRequest",
                         "new Image", "src=", "url(http", "importScripts",
                         "<link", "<script"):
            with self.subTest(alvo=proibido):
                self.assertNotIn(proibido.lower(), codigo.lower())

    def test_o_unico_endereco_e_o_namespace_do_svg(self):
        """createElementNS exige a URI -- ela identifica, nao baixa.

        Qualquer outro endereco no codigo seria uma dependencia de rede
        entrando sem ninguem notar, entao a lista fica com um item so.
        """
        codigo = self.sem_comentario()
        enderecos = set(re.findall(r"https?://[^\s\"\')]+", codigo))
        self.assertEqual(enderecos, {"http://www.w3.org/2000/svg"})

    def test_o_pais_sem_desenho_recebe_a_pastilha_do_codigo(self):
        """Inventar um desenho parecido seria pior.

        Bandeira errada e ofensa, e ninguem confere a bandeira de um pais
        que nao conhece.
        """
        self.assertIn("function pastilha(", self.js)
        self.assertIn("sem-desenho", self.js)

    def test_a_proporcao_e_a_mesma_para_todas(self):
        # proporcao fiel faz cada pastilha ter uma largura, e a coluna
        # de uma lista de trinta paises vira serra
        self.assertIn("const W = 30, H = 20;", self.js)

    def test_toda_bandeira_leva_rotulo_para_leitor_de_tela(self):
        self.assertIn('"aria-label"', self.js)
        self.assertIn("bandeira", self.js)


@unittest.skipIf(NODE is None, "node não está disponível nesta máquina")
class TestODesenhoRoda(unittest.TestCase):
    """Roda o desenho de verdade, num DOM de mentira."""

    def desenhar(self, iso):
        script = (
            "const feitos = [];\n"
            "const doc = { createElementNS(ns, tag){ const n = {tag, attrs:{}, filhos:[],"
            "   setAttribute(k,v){this.attrs[k]=String(v);},"
            "   appendChild(f){this.filhos.push(f); return f;},"
            "   set textContent(v){this.texto=v;} };"
            "   feitos.push(n); return n; } };\n"
            "globalThis.document = doc;\n"
            + BANDEIRAS.read_text(encoding="utf-8") + "\n"
            "const svg = Bandeiras.get(" + json.dumps(iso) + ");\n"
            "function contar(n){ return 1 + n.filhos.reduce((a,f)=>a+contar(f),0); }\n"
            "process.stdout.write(JSON.stringify({\n"
            "  classe: svg.attrs.class, viewBox: svg.attrs.viewBox,\n"
            "  nos: contar(svg) }));\n")
        pronto = subprocess.run([NODE, "--input-type=module", "-e", script],
                                capture_output=True, text=True)
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        return json.loads(pronto.stdout)

    def test_o_brasil_sai_desenhado(self):
        r = self.desenhar("BR")
        self.assertEqual(r["classe"], "bandeira-svg")
        self.assertGreater(r["nos"], 4)      # fundo, losango, disco, borda

    def test_a_bandeira_dos_estados_unidos_tem_listras_e_estrelas(self):
        r = self.desenhar("US")
        self.assertGreater(r["nos"], 30)     # 13 listras + 20 estrelas

    def test_pais_sem_desenho_cai_na_pastilha(self):
        r = self.desenhar("XX")
        self.assertIn("sem-desenho", r["classe"])

    def test_codigo_em_minusculas_tambem_acha(self):
        self.assertEqual(self.desenhar("br")["classe"], "bandeira-svg")

    def test_sem_codigo_nao_quebra(self):
        self.assertIn("sem-desenho", self.desenhar("")["classe"])


class TestAsTelasUsam(unittest.TestCase):

    def test_as_paginas_carregam_o_arquivo(self):
        for pagina in ("panorama.html", "app.html", "mural.html"):
            with self.subTest(pagina=pagina):
                corpo = (TEMPLATES / pagina).read_text(encoding="utf-8")
                self.assertIn("__BANDEIRAS_JS__", corpo)

    def test_o_servidor_injeta(self):
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        self.assertIn('"__BANDEIRAS_JS__"', fonte)
        self.assertIn('"bandeiras.js"', fonte)

    def test_o_painel_desenha_em_vez_de_escrever_o_emoji(self):
        corpo = (TEMPLATES / "panorama.js").read_text(encoding="utf-8")
        self.assertIn("Bandeiras.get(", corpo)
        # e o emoji nao volta por dentro de um rotulo de texto
        self.assertNotIn('x.bandeira + " "', corpo)

    def test_a_biblioteca_desenha(self):
        corpo = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        self.assertIn("Bandeiras.get(p.iso", corpo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
