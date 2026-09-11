#!/usr/bin/env python3
"""O painel por linha de pesquisa, os KPIs novos e a árvore da automação.

    python3 -m unittest tests.test_painel_linhas -v

Três coisas entraram no painel e as três erram calado:

  - O ícone de cada linha vem de uma tabela de palavras. Com busca por
    trecho solto, "ar" achava "sedentário" e "declarada", e duas linhas
    que nada têm com qualidade do ar ganhavam desenho de pulmão. Ninguém
    percebe olhando -- o cartão continua lá, bonito e errado.
  - Os KPIs novos são contas, e conta errada não dá erro: ela exibe um
    número. O mais perigoso é o de autoria, que mede menos do que a área
    chama de liderança, e por isso tem de se chamar pelo que mede.
  - A árvore da automação é hierarquia; uma folha pendurada no ramo
    errado desenha igual à certa.
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
DASHBOARD = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
TEMA = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
NODE = shutil.which("node")


def recorte(inicio: str, fim: str) -> str:
    return DASHBOARD[DASHBOARD.index(inicio):DASHBOARD.index(fim)]


@unittest.skipIf(NODE is None, "node não instalado")
class TestODesenhoDeCadaLinha(unittest.TestCase):
    """A tabela de ícones roda de verdade, com os nomes reais das linhas."""

    @classmethod
    def setUpClass(cls):
        cls.js = recorte("const ICONE_DA_LINHA = [",
                         "/* A tabela dinâmica de uma linha")

    def setUp(self):
        self.js = type(self).js

    def resolver(self, nomes):
        script = self.js + "\nconsole.log(JSON.stringify(%s.map(iconeDaLinha)));" % (
            json.dumps(nomes))
        pronto = subprocess.run([NODE, "--input-type=module", "-e", script],
                                capture_output=True, text=True)
        if pronto.returncode != 0:
            raise AssertionError(pronto.stderr)
        return json.loads(pronto.stdout)

    def test_as_oito_linhas_declaradas_tem_desenho_proprio(self):
        from lape import linhas
        nomes = [nome for _, nome, _, _, _ in linhas.LINHAS]
        desenhos = self.resolver(nomes)
        for nome, desenho in zip(nomes, desenhos):
            with self.subTest(linha=nome):
                self.assertNotEqual(desenho, "linhas",
                                    "%s ficou sem desenho próprio" % nome)

    def test_a_palavra_so_casa_inteira(self):
        """A busca por trecho solto achava "ar" dentro de "sedentário" e de
        "declarada", e duas linhas ganhavam desenho de pulmão. A guarda é a
        fronteira de palavra -- e é ela que este caso exercita: "dormir"
        contém "dor", e não é a linha da dor."""
        self.assertEqual(self.resolver(["Sono e o ato de dormir"]), ["linhas"])
        self.assertEqual(self.resolver(["Dor crônica"]), ["dor"])

    def test_a_lista_nao_tem_chave_curta_demais(self):
        """Fronteira de palavra não salva de uma chave como "ar", que é
        palavra inteira dentro de "ar livre", "ar condicionado" e "ao ar
        de qualquer frase". Chave de duas letras só vale acompanhada."""
        chaves = re.findall(r'\["([^"]+)",\s*"\w+"\]', self.js)
        curtas = [c for parte in chaves for c in parte.split("|")
                  if len(c) <= 2]
        self.assertEqual(curtas, [])

    def test_sem_linha_declarada_nao_ganha_desenho_de_assunto(self):
        self.assertEqual(self.resolver(["Sem linha declarada"]), ["aviso"])

    def test_a_mais_especifica_ganha(self):
        """"Desempenho no Esporte" tem as duas palavras; vence desempenho."""
        self.assertEqual(self.resolver(["Desempenho no Esporte"]), ["subida"])

    def test_linha_desconhecida_nao_fica_sem_cartao(self):
        self.assertEqual(self.resolver(["Linha nova sobre robótica"]), ["linhas"])


class TestOMosaicoDasLinhas(unittest.TestCase):

    def setUp(self):
        self.bloco = recorte("function infograficoDasLinhas(rows) {",
                             "/* Quantas publicações cada linha somou")

    def test_o_cartao_e_botao_de_verdade(self):
        """Cartão que parece clicável e não é custa mais que cartão inerte."""
        self.assertIn('class: "linhacard", type: "button"', self.bloco)
        self.assertIn("abrirLinha(nome, doSet)", self.bloco)

    def test_a_barra_usa_escala_comum(self):
        """Sem escala comum, doze caixas iguais dizem que as linhas pesam igual."""
        self.assertIn("const maior = linhas[0][1].length", self.bloco)
        self.assertIn("/ maior", self.bloco)

    def test_o_mosaico_e_cortado(self):
        """Quarenta cartões não são infográfico: são lista."""
        self.assertIn(".slice(0, 12)", self.bloco)

    def test_o_foco_do_teclado_e_visivel(self):
        self.assertRegex(TEMA, r"\.linhacard:focus-visible\s*\{[^}]*outline")

    def test_a_gaveta_traz_tabela_que_trabalha(self):
        gaveta = recorte("function abrirLinha(nome, doSet) {",
                         "/* Os cartões, um por linha")
        self.assertIn("dataTable(", gaveta)
        self.assertIn("onRow:", gaveta)
        self.assertIn("STATE.linha = nome", gaveta)


class TestOsIndicadoresNovos(unittest.TestCase):

    def setUp(self):
        self.painel = recorte('view("visao", "Painel"', 'view("metas"')

    def test_o_indice_h_e_da_colecao_e_nao_de_uma_pessoa(self):
        self.assertIn("while (hLab < ordenadas.length && ordenadas[hLab] >= hLab + 1)",
                      self.painel)
        self.assertIn("Índice h do laboratório", self.painel)

    def test_a_autoria_se_chama_pelo_que_mede(self):
        """Sênior exigiria saber quantos autores o artigo tem ao todo, e o
        banco só guarda os nossos -- então o rótulo é "Primeira autoria"."""
        self.assertIn("Primeira autoria", self.painel)
        self.assertNotIn("Liderança na autoria", self.painel)
        self.assertIn("l.o === 1", self.painel)

    def test_citacao_por_artigo_usa_mediana(self):
        """A média se deixa levar por um artigo muito citado; a mediana não."""
        self.assertIn("median(published.map(bestCitations))", self.painel)
        self.assertIn("sem citação", self.painel)

    def test_a_concentracao_mede_as_tres_mais_ativas(self):
        self.assertIn(".slice(0, 3)", self.painel)
        self.assertIn("Concentração da produção", self.painel)

    def test_a_renovacao_olha_o_trienio(self):
        self.assertIn("currentYear - 2", self.painel)

    def test_todo_indicador_novo_leva_a_algum_lugar(self):
        """Um número grande levanta sempre "quais são esses?"."""
        fileira = self.painel[
            self.painel.index('class: "grid g4 fixed4", style: "margin-top:13px"'):
            self.painel.index("const segItems")]
        chamadas = re.findall(r"kpi\(\{(.*?)\}\),\n", fileira, re.S)
        self.assertEqual(len(chamadas), 8, "a segunda fileira mudou de tamanho")
        for chamada in chamadas:
            rotulo = re.search(r'label: "([^"]+)"', chamada)
            with self.subTest(kpi=rotulo.group(1) if rotulo else "?"):
                self.assertIn("ir:", chamada)
                self.assertIn("leitura:", chamada)


class TestAArvoreDaAutomacao(unittest.TestCase):

    def setUp(self):
        self.bloco = recorte("function arvoreDaAutomacao(a) {",
                             'view("automacao"')

    def test_toda_familia_de_evento_do_servidor_tem_verbete(self):
        """Sem verbete, a família aparece com o nome cru e ícone genérico."""
        from lape import hooks
        familias = {chave.split(".")[0] for chave in hooks.EVENTS}
        mapa = recorte("const FAMILIA_DO_EVENTO = {", "/* Para onde cada família leva")
        declaradas = set(re.findall(r"^\s*(\w+):\s*\{", mapa, re.M))
        self.assertEqual(familias - declaradas, set())

    def test_toda_familia_leva_a_uma_aba_que_existe(self):
        mapa = recorte("const ABA_DA_FAMILIA = {", "function arvoreDaAutomacao")
        alvos = set(re.findall(r'"(\w+)"', mapa.split("{", 1)[1]))
        existentes = set(re.findall(r'view\("(\w+)"', DASHBOARD))
        self.assertEqual(alvos - existentes - {"artigo", "submissao", "projeto",
                                               "integrante", "evento", "descoberta",
                                               "agente", "lake", "dados"}, set())

    def test_quem_assina_tudo_aparece_em_cada_evento(self):
        """Um fluxo que escuta "*" parecia não escutar nada."""
        self.assertIn('w.event === ev.id || w.event === "*"', self.bloco)

    def test_o_evento_sem_ouvinte_se_explica(self):
        """Opacidade baixa sozinha não é informação."""
        self.assertIn('"mudo"', self.bloco)
        self.assertIn("Nenhum destino escuta este evento", self.bloco)

    def test_a_arvore_e_peca_reaproveitavel(self):
        """Não é desenho de uma tela: recebe raiz e desenha qualquer hierarquia."""
        comp = recorte("function arvoreDeIcones(raiz, opts) {",
                       "/* O caminho de um evento até o n8n")
        self.assertIn("no(f, nivel + 1)", comp)      # recursão de verdade
        self.assertIn("navega ? \"button\" : \"div\"", comp)


class TestAHistoriaEmCapitulos(unittest.TestCase):

    def test_o_endereco_carrega_o_capitulo(self):
        """#historia/equipe tem de abrir a equipe, e não o Resumo."""
        self.assertIn("function abaDe(hash)", DASHBOARD)
        self.assertIn('.split("/")[0]', DASHBOARD)
        self.assertIn("if (!viewOf(abaDe(id))) id = ORDER[0];", DASHBOARD)

    def test_o_boot_tambem_separa(self):
        boot = recorte("function boot() {", "boot();")
        self.assertIn("abaDe(location.hash)", boot)

    def test_trocar_so_o_capitulo_redesenha(self):
        boot = recorte("function boot() {", "boot();")
        self.assertIn("else if (id === current) render();", boot)

    def test_cada_capitulo_tem_conteudo(self):
        caps = re.search(r"const CAPITULOS = \[(.*?)\n\];", DASHBOARD, re.S)
        self.assertIsNotNone(caps)
        ids = re.findall(r'id: "(\w+)"', caps.group(1))
        self.assertEqual(len(ids), 7)
        inicio = DASHBOARD.index("function desenharCapitulo(id, host) {")
        desenho = DASHBOARD[inicio:DASHBOARD.index("\nfunction ", inicio + 10)]
        for cap in ids:
            with self.subTest(capitulo=cap):
                self.assertIn('id === "%s"' % cap, desenho)

    def test_o_indice_e_feito_de_botoes(self):
        self.assertIn('class: "capcard", type: "button"', DASHBOARD)

    def test_o_capitulo_tem_como_voltar(self):
        self.assertIn("capvoltar", DASHBOARD)
        self.assertIn("capnav", DASHBOARD)


if __name__ == "__main__":
    unittest.main()
