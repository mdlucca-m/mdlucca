#!/usr/bin/env python3
"""Formacao e prazos: quem pode ver, e o que a tela promete.

    python3 -m unittest tests.test_formacao -v

Esta aba mexe no unico dado do painel que nao e sobre producao: bolsa e
prazo de defesa sao sobre a vida de uma pessoa. O codigo ja tinha essa
decisao tomada (SO_DA_COORDENACAO, em metrics.py) e a aplicava so no
organograma publico -- o payload do painel levava tudo, e o payload vai
inteiro para dentro do HTML: para o arquivo exportado que e commitado em
docs/, para o mural que fica numa TV e, com LAPE_PUBLIC_DASHBOARD, para
quem abrir o link. Ver a tela nao e a unica forma de ler um JSON.

Por isso metade destes testes e sobre quem NAO ve. Vazamento de payload e
o erro mais silencioso que existe: ninguem percebe olhando a tela.
"""
from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import mapping, metrics  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
DASHBOARD = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
TEMA = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
API = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")

SENSIVEIS = set(metrics.SO_DA_COORDENACAO)


def bloco() -> str:
    inicio = DASHBOARD.index("/* formação e prazos")
    return DASHBOARD[inicio:DASHBOARD.index("const TESE_SITUACAO = {", inicio)]


BLOCO = bloco()


class BaseDaFormacao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "f.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()

    def pessoa(self, nome, **extra):
        campos = {"full_name": nome, "name_key": nome.lower().replace(" ", "_"),
                  "is_external": 0, "active": 1}
        campos.update(extra)
        cols = ", ".join(campos)
        self.db.execute("INSERT INTO members (%s) VALUES (%s)"
                        % (cols, ", ".join("?" * len(campos))), tuple(campos.values()))
        return self.db.scalar("SELECT id FROM members WHERE name_key = ?",
                              (campos["name_key"],))

    def com_dados(self):
        chefe = self.pessoa("Alexandro Andrade", role="coordenacao")
        self.pessoa("Ana Orientanda", role="doutorando", advisor_id=chefe,
                    thesis_title="Exercício e dor", thesis_status="em_andamento",
                    thesis_due_on="2027-03-30", scholarship="CAPES",
                    scholarship_until="2027-01-10")
        return chefe


class TestOCorteDoPayload(BaseDaFormacao):
    """Bolsa e prazo saem por padrao, e entram so quando alguem pede."""

    def test_o_padrao_e_nao_levar(self):
        self.com_dados()
        org = metrics.build_payload(self.db)["org"]
        presentes = {k for p in org["people"] for k, v in p.items()
                     if k in SENSIVEIS and v not in (None, "")}
        self.assertEqual(presentes, set())
        self.assertEqual(org["teses"], [])

    def test_quem_pede_recebe(self):
        self.com_dados()
        org = metrics.build_payload(self.db, com_dados_da_coordenacao=True)["org"]
        presentes = {k for p in org["people"] for k, v in p.items()
                     if k in SENSIVEIS and v not in (None, "")}
        self.assertIn("thesis_due_on", presentes)
        self.assertIn("scholarship", presentes)
        self.assertTrue(org["teses"])

    def test_o_corte_se_anuncia(self):
        """"Ninguem declarou" e "voce nao pode ver" sao coisas diferentes."""
        self.com_dados()
        self.assertTrue(metrics.build_payload(self.db)["org"].get("restrito"))
        self.assertFalse(metrics.build_payload(
            self.db, com_dados_da_coordenacao=True)["org"].get("restrito"))

    def test_o_corte_nao_leva_junto_o_resto_do_organograma(self):
        """Cortar demais quebraria o desenho de quem responde a quem."""
        self.com_dados()
        org = metrics.build_payload(self.db)["org"]
        self.assertEqual(len(org["people"]), 2)
        self.assertTrue(org["edges"])
        self.assertTrue(org["by_role"])
        self.assertTrue(all(p.get("full_name") for p in org["people"]))
        self.assertTrue(any(p.get("advisor") for p in org["people"]))

    def test_a_funcao_de_corte_nao_altera_o_original(self):
        self.com_dados()
        org = metrics.organograma(self.db)
        limpo = metrics.sem_dados_da_coordenacao(org)
        self.assertTrue(any(p.get("thesis_due_on") for p in org["people"]))
        self.assertFalse(any(p.get("thesis_due_on") for p in limpo["people"]))


class TestQuemPodeVer(unittest.TestCase):
    """A rota decide; a tela so obedece."""

    def test_o_painel_so_pede_os_campos_para_a_coordenacao(self):
        trecho = API[API.index("def _serve_dashboard"):]
        trecho = trecho[:trecho.index("def _serve_stream")]
        self.assertIn("com_dados_da_coordenacao=", trecho)
        self.assertIn('auth.ROLE_RANK["coordenacao"]', trecho)

    def test_o_mural_nunca_recebe_os_campos(self):
        """Numa TV, quem esta na sala nao fez login nenhum."""
        trecho = API[API.index("def _serve_dashboard"):]
        trecho = trecho[:trecho.index("def _serve_stream")]
        self.assertRegex(trecho, r"da_coordenacao = not mural")

    def test_integrante_comum_nao_alcanca_o_nivel(self):
        from lape import auth
        self.assertLess(auth.ROLE_RANK["integrante"], auth.ROLE_RANK["coordenacao"])
        self.assertGreaterEqual(auth.ROLE_RANK["admin"], auth.ROLE_RANK["coordenacao"])

    def test_a_tela_diz_o_motivo_de_estar_vazia(self):
        self.assertIn("org.restrito", BLOCO)
        self.assertIn("só para a coordenação", BLOCO)

    def test_o_organograma_tambem_explica_a_tabela_vazia(self):
        """Antes deste corte a tabela de teses vivia la, e ficaria muda."""
        org = DASHBOARD[DASHBOARD.index('view("organograma"'):
                        DASHBOARD.index("/* Organograma em colunas")]
        self.assertIn("org.restrito", org)


class TestOVocabularioDaFormacao(unittest.TestCase):

    def test_em_formacao_e_a_mesma_lista_do_servidor(self):
        """Quarta copia deste vocabulario; divergir e o modo de errar."""
        achado = re.search(r"const EM_FORMACAO = \[(.*?)\];", DASHBOARD, re.S)
        self.assertIsNotNone(achado)
        na_tela = set(re.findall(r'"([a-z_]+)"', achado.group(1)))
        self.assertEqual(na_tela, set(mapping.ORIENTADOS))

    def test_o_resumo_usa_a_mesma_lista(self):
        """Antes ele tinha a propria copia, sem pos-doutorado nem voluntario."""
        resumo = DASHBOARD[DASHBOARD.index('view("resumo"'):
                           DASHBOARD.index('view("historia"')]
        self.assertIn("EM_FORMACAO.indexOf(m.role)", resumo)

    def test_tese_encerrada_nao_conta_como_atraso(self):
        """Quem defendeu virava 'prazo vencido' -- entregou e virou pendencia."""
        achado = re.search(r"const TESE_ENCERRADA = \[(.*?)\];", DASHBOARD, re.S)
        self.assertIsNotNone(achado)
        self.assertEqual(set(re.findall(r'"([a-z_]+)"', achado.group(1))),
                         {"concluida", "trancada"})
        self.assertIn("TESE_ENCERRADA.indexOf(p.thesis_status)", BLOCO)

    def test_as_situacoes_da_tese_sao_as_do_servidor(self):
        mapa = DASHBOARD[DASHBOARD.index("const TESE_SITUACAO = {"):]
        mapa = mapa[:mapa.index("};")]
        na_tela = set(re.findall(r"([a-z_]+):\s*\"", mapa))
        self.assertEqual(na_tela, set(mapping.THESIS_STATUS_MAP.values()))


class TestAsFaixasDePrazo(unittest.TestCase):
    """Vencido, 90 dias, um ano, mais que isso, e sem prazo -- sem buraco."""

    def faixas(self) -> list[tuple[str, str]]:
        trecho = re.search(r"const FAIXAS_DE_PRAZO = \[(.*?)\n\];", BLOCO, re.S)
        self.assertIsNotNone(trecho)
        return re.findall(r'id: "(\w+)".*?cor: "([\w-]+)"', trecho.group(1), re.S)

    def test_ha_cinco_faixas(self):
        self.assertEqual(len(self.faixas()), 5)

    def test_toda_faixa_tem_rotulo_e_desenho(self):
        """Cor de estado sozinha nao se le impressa nem sem enxergar vermelho."""
        trecho = re.search(r"const FAIXAS_DE_PRAZO = \[(.*?)\n\];", BLOCO, re.S).group(1)
        for item in re.findall(r"\{.*?cabe:.*?\}", trecho, re.S):
            self.assertRegex(item, r'rotulo: "[^"]+"', item)
            self.assertRegex(item, r'icone: "\w+"', item)

    def test_a_cor_de_estado_e_usada_como_estado(self):
        """`--critical` e `--warning` sao reservados: nunca cor de serie."""
        cores = [c for _, c in self.faixas()]
        self.assertIn("--critical", cores)
        self.assertIn("--warning", cores)

    def test_sem_prazo_nao_e_urgencia(self):
        """Prazo em branco nao pode entrar na faixa de vencido."""
        trecho = re.search(r'id: "sem".*?cabe: function \(d\) \{ return ([^;]+); \}',
                           BLOCO, re.S)
        self.assertIsNotNone(trecho)
        self.assertEqual(trecho.group(1).strip(), "d === null")

    def test_sem_prazo_vai_para_o_fim_da_fila(self):
        """Ordenar 'sem prazo' como zero o poria no topo dos urgentes."""
        self.assertIn("r.dias === null ? 1e9 : r.dias", BLOCO)

    def test_o_atraso_e_dito_por_extenso(self):
        """"faltam -40 dias" e a mesma conta de "venceu ha 40 dias"."""
        self.assertIn("venceu há", BLOCO)
        self.assertIn("faltam", BLOCO)


class TestAFolhaDaEtiqueta(unittest.TestCase):

    def regra(self) -> str:
        achado = re.search(r"\.prazo-chip \{([^}]*)\}", TEMA)
        self.assertIsNotNone(achado)
        return achado.group(1)

    def test_o_texto_da_etiqueta_nao_veste_a_cor_do_estado(self):
        """Âmbar sobre fundo claro da 1,9:1. O tom fica no aro e no desenho."""
        self.assertRegex(self.regra(), r"color:\s*var\(--ink\)")
        self.assertNotRegex(self.regra(), r"color:\s*var\(--faixa")

    def test_o_desenho_carrega_o_tom(self):
        achado = re.search(r"\.prazo-chip svg\.icon \{([^}]*)\}", TEMA)
        self.assertIsNotNone(achado)
        self.assertIn("--faixa", achado.group(1))


class TestABarraDeFiltrosNaFormacao(unittest.TestCase):

    def test_a_tela_nao_responde_a_filtro_nenhum(self):
        """Ela le D.org, e nao articles(): os seletores seriam inertes."""
        self.assertNotIn("articles()", BLOCO)
        lista = re.search(r"const SEM_FILTROS = \[(.*?)\];", DASHBOARD, re.S)
        self.assertIn('"formacao"', lista.group(1))


class TestARegistroDaAba(unittest.TestCase):

    def test_a_aba_entra_na_secao_de_pessoas(self):
        secoes = DASHBOARD[DASHBOARD.index("const SECTIONS = ["):
                           DASHBOARD.index("const VIEW_ICON = {")]
        pessoas = re.search(r'id: "pessoas".*?views: \[(.*?)\]', secoes, re.S)
        self.assertIsNotNone(pessoas)
        self.assertIn('"formacao"', pessoas.group(1))

    def test_a_aba_tem_icone(self):
        self.assertRegex(DASHBOARD, r"formacao:\s*\"\w+\"")


if __name__ == "__main__":
    unittest.main()
