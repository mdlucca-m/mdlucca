#!/usr/bin/env python3
"""Testes dos links externos do artigo, rodando o JavaScript de verdade.

    python3 -m unittest tests.test_links -v

`linksDoArtigo` decide para onde o clique leva. Errar aqui não dá erro na
tela: o link simplesmente cai numa página de erro do doi.org, ou não
aparece nenhum -- e nos dois casos quem usa conclui, com razão, que o
sistema está quebrado. Foi o que aconteceu.

O teste chama a função do próprio `dashboard.js` no Node, sem reescrevê-la
em Python: uma cópia da regra em outra linguagem passaria a valer sozinha
no dia em que a original mudasse.
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
DASHBOARD_JS = ROOT / "scripts" / "lape" / "templates" / "dashboard.js"
NODE = shutil.which("node")


def _recorta(nome: str) -> str:
    """Recorta uma função do dashboard.js para rodá-la isolada."""
    texto = DASHBOARD_JS.read_text(encoding="utf-8")
    inicio = texto.index(f"function {nome}(")
    fim_da_linha = texto.index("\n", inicio)
    primeira = texto[inicio:fim_da_linha]
    if primeira.rstrip().endswith("}"):        # função de uma linha só
        return primeira
    return texto[inicio:texto.index("\n}\n", inicio) + 3]


def _sem_comentarios(texto: str) -> str:
    """Comentário citando `window.open` não é `window.open` sendo chamado."""
    return re.sub(r"/\*.*?\*/", "", texto, flags=re.S)


@unittest.skipIf(NODE is None, "node não está disponível nesta máquina")
class TestLinksDoArtigo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fonte = _recorta("doiDeExemplo") + "\n" + _recorta("linksDoArtigo")

    def links(self, artigo: dict) -> list[dict]:
        script = (self.fonte + "\nconst artigo = " + json.dumps(artigo)
                  + ";\nprocess.stdout.write(JSON.stringify(linksDoArtigo(artigo)));\n")
        pronto = subprocess.run([NODE, "--input-type=module", "-e", script],
                                capture_output=True, text=True)
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        return json.loads(pronto.stdout)

    def rotulos(self, artigo: dict) -> list[str]:
        return [d["rotulo"] for d in self.links(artigo)]

    # -- o caminho feliz ------------------------------------------------
    def test_doi_vira_o_primeiro_destino(self):
        links = self.links({"title": "Um artigo", "doi": "10.1016/j.psychsport.2024.102631"})
        self.assertEqual(links[0]["rotulo"], "Abrir o artigo")
        self.assertEqual(links[0]["url"], "https://doi.org/10.1016/j.psychsport.2024.102631")
        self.assertTrue(links[0]["forte"])

    def test_doi_ja_em_forma_de_endereco_nao_duplica_o_prefixo(self):
        links = self.links({"title": "Um artigo", "doi": "https://doi.org/10.1016/x.2024.1"})
        self.assertEqual(links[0]["url"], "https://doi.org/10.1016/x.2024.1")
        self.assertNotIn("doi.org/https", links[0]["url"])

    def test_bases_entram_quando_ha_identificador(self):
        rotulos = self.rotulos({"title": "Um artigo", "doi": "10.1016/x.2024.1",
                                "scopus_id": "2-s2.0-85123", "wos_id": "WOS:000123"})
        self.assertEqual(rotulos, ["Abrir o artigo", "Scopus", "Web of Science", "OpenAlex"])

    def test_link_cadastrado_serve_quando_nao_ha_doi(self):
        links = self.links({"title": "Um artigo", "url": "https://revista.org/artigo/12"})
        self.assertEqual(links[0]["rotulo"], "Abrir o artigo")
        self.assertEqual(links[0]["url"], "https://revista.org/artigo/12")

    # -- o caso que motivou tudo ---------------------------------------
    def test_artigo_sem_nada_cai_na_busca_pelo_titulo(self):
        # 16 dos 19 artigos do laboratório estão em produção: não existe DOI
        # para eles em lugar nenhum, e o painel não pode fingir que existe
        links = self.links({"title": "Ansiedade em atletas de base", "status": "em_producao"})
        self.assertTrue(links)
        self.assertTrue(all(d.get("busca") for d in links),
                        "busca por título não pode passar por link do artigo")
        self.assertIn("Ansiedade", links[0]["url"])

    def test_a_busca_procura_o_titulo_entre_aspas(self):
        links = self.links({"title": "Atenção plena e desempenho"})
        self.assertIn("%22", links[0]["url"], "sem aspas a busca traz qualquer coisa")

    def test_titulo_com_caractere_especial_nao_quebra_o_endereco(self):
        links = self.links({"title": 'Efeito & impacto: 50% + "algo"'})
        for destino in links:
            self.assertNotIn(" ", destino["url"])
            self.assertNotIn("&algo", destino["url"])

    # -- DOI de mentira -------------------------------------------------
    def test_doi_de_exemplo_nao_vira_link_para_o_artigo(self):
        # 10.5555 é o prefixo de teste da Crossref: a massa de demonstração
        # usa esse, e clicar num DOI que não existe leva à página de erro do
        # doi.org -- que parece defeito do sistema, não dado de mentira
        links = self.links({"title": "Artigo de demonstração", "doi": "10.5555/lape.2026.0115",
                            "url": "https://doi.org/10.5555/lape.2026.0115"})
        self.assertTrue(all(d.get("busca") for d in links))

    def test_um_doi_de_verdade_continua_valendo(self):
        links = self.links({"title": "Artigo", "doi": "10.5556/algo.2024.1"})
        self.assertEqual(links[0]["rotulo"], "Abrir o artigo")

    def test_sem_titulo_e_sem_identificador_nao_se_inventa_destino(self):
        self.assertEqual(self.links({"title": None}), [])


@unittest.skipIf(NODE is None, "node não está disponível nesta máquina")
class TestOsDestinosSaoAncoras(unittest.TestCase):
    """Bloqueador de pop-up derruba janela aberta por script.

    A primeira versão abria os destinos com `window.open` num <button>. Com
    o bloqueador ligado o botão não fazia nada -- que é exatamente como um
    link quebrado se parece.
    """

    def test_a_gaveta_usa_ancora_e_nao_window_open(self):
        texto = DASHBOARD_JS.read_text(encoding="utf-8")
        trecho = texto[texto.index("const destinos = linksDoArtigo(article)"):]
        trecho = _sem_comentarios(trecho[:trecho.index("openDrawer(")])
        self.assertNotIn("window.open", trecho)
        self.assertIn('el("a"', trecho)
        self.assertIn('rel: "noopener"', trecho)

    def test_o_atalho_da_tabela_tambem_aparece_para_busca(self):
        # sem ícone nenhum, a linha não explica coisa alguma: quem procura o
        # link conclui que ele está quebrado
        fonte = _sem_comentarios(_recorta("atalhoExterno"))
        self.assertIn("destino.busca ?", fonte)
        self.assertNotIn("if (!destino || destino.busca) return null;", fonte)


class TestMassaDeDemonstracao(unittest.TestCase):
    def test_o_gerador_usa_o_prefixo_reservado_para_teste(self):
        demo = (ROOT / "scripts" / "lape" / "demo.py").read_text(encoding="utf-8")
        self.assertIn("10.5555/", demo)
        # um prefixo sorteado produzia DOI de mentira indistinguível de um
        # de verdade
        self.assertNotIn('10.{rng.randint(1000, 9999)}/', demo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
