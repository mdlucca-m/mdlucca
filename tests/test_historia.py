#!/usr/bin/env python3
"""A aba de historia: a unica tela que responde "quem somos".

    python3 -m unittest tests.test_historia -v

Esta tela nao tem grafico, e por isso nao tem erro barulhento. Tudo o que
pode dar errado nela da errado CALADO:

  - um nome de icone escrito torto vira um pontinho cinza (o `Icons.get`
    tem fallback de proposito, para que a aba nao quebre) -- e a aba que
    se le por desenho perde o desenho sem avisar ninguem;
  - um icone novo sem tom declarado sai azul como todos os outros, e as
    dezoito caixas viram uma parede de uma cor so;
  - uma classe CSS sem regra nenhuma renderiza texto solto no meio do
    cartao, sem nenhum sinal de que faltou folha;
  - a barra de filtros escondida com [hidden] continua na tela se a folha
    disser `display: flex`, porque `[hidden]` e so `display: none` na
    folha do navegador;
  - e a view declarada mas nao registrada em SECTIONS simplesmente nao
    existe, porque a ordem do painel e construida a partir de SECTIONS.

Daí o teste ler a fonte em vez de confiar na tela.
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

TEMPLATES = ROOT / "scripts" / "lape" / "templates"

DASHBOARD = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
ICONES = (TEMPLATES / "icons.js").read_text(encoding="utf-8")
TEMA = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
PAGINA = (TEMPLATES / "dashboard.html").read_text(encoding="utf-8")


def bloco_historia() -> str:
    """O literal `const HISTORIA = { ... }` e a view que o desenha."""
    inicio = DASHBOARD.index("const HISTORIA = {")
    fim = DASHBOARD.index('view("visao"', inicio)
    return DASHBOARD[inicio:fim]


BLOCO = bloco_historia()


def icones_do_set() -> set[str]:
    """Os nomes que `icons.js` sabe desenhar."""
    corpo = ICONES[ICONES.index("const SET = {"):ICONES.index("const TOM = {")]
    return set(re.findall(r"^\s{4}([A-Za-z][A-Za-z0-9_]*):\s*\[", corpo, re.M))


def tons_declarados() -> set[str]:
    corpo = ICONES[ICONES.index("const TOM = {"):ICONES.index("function draw(")]
    return set(re.findall(r"([A-Za-z][A-Za-z0-9_]*):\s*\"", corpo))


class TestAAbaExiste(unittest.TestCase):
    """Declarada, registrada e alcancavel -- as tres coisas."""

    def test_a_view_e_declarada(self):
        self.assertIn('view("historia"', DASHBOARD)

    def test_a_aba_entra_numa_secao_do_menu(self):
        """View fora de SECTIONS nao aparece: ORDER nasce de SECTIONS."""
        secoes = DASHBOARD[DASHBOARD.index("const SECTIONS = ["):
                           DASHBOARD.index("const VIEW_ICON = {")]
        self.assertIn('"historia"', secoes)

    def test_a_aba_tem_icone_proprio(self):
        mapa = DASHBOARD[DASHBOARD.index("const VIEW_ICON = {"):
                         DASHBOARD.index("const SEM_FILTROS")]
        self.assertRegex(mapa, r"historia:\s*\"[a-z]+\"")

    def test_a_aba_aponta_para_telas_vizinhas(self):
        self.assertRegex(DASHBOARD, r"historia:\s*\[[^\]]+\]")


class TestOsIcones(unittest.TestCase):
    """Nome de icone errado nao levanta excecao -- vira um ponto."""

    def setUp(self):
        self.set = icones_do_set()

    def usados(self) -> set[str]:
        nomes = set(re.findall(r"icone:\s*\"([A-Za-z0-9_]+)\"", BLOCO))
        nomes |= set(re.findall(r"Icons\.(?:get|badge)\(\"([A-Za-z0-9_]+)\"", BLOCO))
        nomes |= set(re.findall(r"historia:\s*\"([a-z]+)\"", DASHBOARD))
        return nomes

    def test_a_historia_usa_mais_de_um_punhado_de_icones(self):
        """Se a extracao parar de achar nomes, os testes abaixo passam vazios."""
        self.assertGreaterEqual(len(self.usados()), 12)

    def test_todo_icone_da_historia_sabe_se_desenhar(self):
        faltam = sorted(self.usados() - self.set)
        self.assertEqual(faltam, [], "icone sem desenho em icons.js: %s" % faltam)

    def test_todo_icone_tem_tom_declarado(self):
        """Sem tom, o badge cai no azul padrao e a parede fica monocromatica."""
        faltam = sorted(self.usados() - tons_declarados())
        self.assertEqual(faltam, [], "icone sem tom em TOM: %s" % faltam)

    def test_os_icones_novos_mantem_a_caixa_de_24(self):
        """Um traco fora da caixa sai da fila e vira erro de impressao."""
        corpo = ICONES[ICONES.index("const SET = {"):ICONES.index("const TOM = {")]
        for nome in ["raizes", "semente", "sono", "humor", "serenidade", "comunidade"]:
            verbete = re.search(r"^\s{4}%s: (\[.*?\]),\n(?=\s{4}[A-Za-z/]|\s*$)" % nome,
                                corpo, re.S | re.M)
            self.assertIsNotNone(verbete, "verbete %s nao encontrado" % nome)
            numeros = [float(n) for n in re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])",
                                                    verbete.group(1))]
            self.assertTrue(numeros, nome)
            self.assertGreaterEqual(min(numeros), -1, "%s sai da caixa" % nome)
            self.assertLessEqual(max(numeros), 25, "%s sai da caixa" % nome)


class TestOsFatos(unittest.TestCase):
    """O texto e da coordenacao. As datas nao podem escorregar numa revisao."""

    def test_as_tres_datas_da_fundacao(self):
        for marco in ["1989", "1990", "1999"]:
            self.assertIn(marco, BLOCO, "marco %s sumiu da linha do tempo" % marco)

    def test_o_ano_de_fundacao_e_um_numero_e_nao_um_texto(self):
        """`anos de historia` e conta, e nao frase: corrige-se sozinho."""
        self.assertRegex(BLOCO, r"fundado_em:\s*1989")
        self.assertIn("ano - HISTORIA.fundado_em", BLOCO)

    def test_o_fundador_e_nomeado(self):
        self.assertIn("Alexandro Andrade", BLOCO)

    def test_as_cinco_linhas_de_pesquisa_da_pee(self):
        linhas = re.search(r"linhas: \[(.*?)\n  \],", BLOCO, re.S)
        self.assertIsNotNone(linhas)
        self.assertEqual(len(re.findall(r"titulo:", linhas.group(1))), 5)

    def test_o_tripe_universitario_esta_inteiro(self):
        for perna in ["Pesquisa", "Ensino", "Extensão"]:
            self.assertRegex(BLOCO, r"titulo: \"%s\"" % perna)

    def test_todo_beneficio_diz_o_sentido_do_efeito(self):
        """Seta sem rumo nao informa: cada efeito sobe ou desce."""
        trecho = re.search(r"beneficios: \[(.*?)\n  \],", BLOCO, re.S)
        self.assertIsNotNone(trecho)
        itens = re.findall(r"\{[^}]*\}", trecho.group(1))
        self.assertEqual(len(itens), 8)
        for item in itens:
            self.assertRegex(item, r"seta: \"(sobe|desce)\"", item)

    def test_a_seta_vem_acompanhada_de_palavra(self):
        """Forma sozinha nao se le impressa nem por quem nao ve a cor."""
        self.assertIn("aumenta", BLOCO)
        self.assertIn("reduz", BLOCO)


class TestAFolhaDeEstilo(unittest.TestCase):
    """Classe sem regra vira texto solto, e ninguem ve o erro."""

    def classes_usadas(self) -> set[str]:
        nomes: set[str] = set()
        for valor in re.findall(r"class: \"([^\"]+)\"", BLOCO):
            nomes |= {p for p in valor.split() if p.startswith("h")}
        return nomes

    def test_a_extracao_acha_as_classes(self):
        self.assertGreaterEqual(len(self.classes_usadas()), 8)

    def test_toda_classe_da_historia_tem_regra_no_tema(self):
        faltam = sorted(c for c in self.classes_usadas()
                        if ("." + c) not in TEMA)
        self.assertEqual(faltam, [], "classe sem regra no tema: %s" % faltam)

    def test_a_cascata_nao_congela_o_transform(self):
        """`both`/`forwards` fixaria o transform do ultimo quadro e mataria o
        levantar do :hover -- a animacao venceria a regra no cascata."""
        regra = re.search(r"\.hcaixa\.entrando[^{]*\{([^}]*)\}", TEMA)
        self.assertIsNotNone(regra)
        self.assertIn("backwards", regra.group(1))
        self.assertNotRegex(regra.group(1), r"\b(both|forwards)\b")

    def test_o_movimento_da_historia_e_desligavel(self):
        """Quem pediu menos movimento nao pode receber cascata nenhuma.

        A guarda e procurada em TODOS os blocos de `prefers-reduced-motion`,
        e nao no ultimo: o tema cresce por baixo, e ancorar no ultimo bloco
        fazia este teste quebrar sempre que outra tela acrescentava CSS --
        sem nada ter acontecido com a historia.
        """
        guardas = "\n".join(
            TEMA[m.start():].split("\n}\n")[0]
            for m in re.finditer(r"@media \(prefers-reduced-motion: reduce\)", TEMA))
        self.assertIn(".hcaixa.entrando", guardas)
        self.assertIn(".hmarco.entrando", guardas)
        self.assertIn("animation: none", guardas)

    def test_nada_da_historia_fica_invisivel_sem_animacao(self):
        """A caixa entra de uma opacidade 0; se a animacao nao rodar, ela
        precisa estar visivel do mesmo jeito -- por isso a opacidade 0 mora
        SO no keyframe, e nunca na regra da caixa."""
        regra = re.search(r"^\.hcaixa \{([^}]*)\}", TEMA, re.M)
        self.assertIsNotNone(regra)
        self.assertNotIn("opacity", regra.group(1))


class TestABarraDeFiltros(unittest.TestCase):
    """Seletor de ano sobre uma pagina que nao muda com ele e controle que mente."""

    def test_a_historia_esta_na_lista_de_telas_sem_filtro(self):
        lista = re.search(r"const SEM_FILTROS = \[(.*?)\];", DASHBOARD, re.S)
        self.assertIsNotNone(lista)
        self.assertIn('"historia"', lista.group(1))

    def test_o_desenho_consulta_a_lista(self):
        self.assertIn("SEM_FILTROS.indexOf(v.id)", DASHBOARD)

    def test_esconder_a_barra_realmente_esconde(self):
        """Sem esta regra, o `display: flex` da barra vence o [hidden]."""
        self.assertRegex(PAGINA, r"\.toolbar\[hidden\]\s*\{[^}]*display:\s*none")


if __name__ == "__main__":
    unittest.main()
