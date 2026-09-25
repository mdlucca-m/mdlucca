#!/usr/bin/env python3
"""Testes da lógica de dados do painel 4K (scripts/lape_streamlit_4k.py).

    python3 -m unittest tests.test_streamlit_4k -v

Cobre só as funções PURAS (recebem DataFrame, devolvem número/dict) --
KPIs, alerta de latência, sugestão metodológica e projeção de ritmo. Nada
de renderização (isso já foi conferido ao vivo, com Playwright, contra um
Streamlit de verdade); o que entra aqui é a REGRA por trás de cada
número, que é o que quebra em silêncio se alguém mexer sem querer.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lape_streamlit_4k as painel  # noqa: E402


def artigo(status, started=None, first_sub=None, published=None, ano=None,
           wos=0, scopus=0, linha="Linha A", study_type="experimental"):
    return {
        "status": status, "linha": linha, "study_type": study_type,
        "started_on": pd.Timestamp(started) if started else pd.NaT,
        "first_submission_on": pd.Timestamp(first_sub) if first_sub else pd.NaT,
        "published_on": pd.Timestamp(published) if published else pd.NaT,
        "year_published": ano,
        "wos_citations": wos, "scopus_citations": scopus, "openalex_citations": 0,
    }


def submissao(article_id, decision=None, submitted=None, decision_on=None, journal=None, title=None):
    return {
        "article_id": article_id, "decision": decision, "journal": journal,
        "submitted_on": pd.Timestamp(submitted) if submitted else pd.NaT,
        "decision_on": pd.Timestamp(decision_on) if decision_on else pd.NaT,
        "title": title or f"artigo {article_id}", "internal_code": f"ART-{article_id:04d}",
        "research_line_id": 1,
    }


AGORA = pd.Timestamp.now()


class TestCalcularKpis(unittest.TestCase):
    def test_total_e_em_producao_contam_por_status(self):
        artigos = pd.DataFrame([artigo("em_producao"), artigo("em_producao"), artigo("publicado")])
        kpis = painel.calcular_kpis(artigos, pd.DataFrame(columns=["decision", "submitted_on", "decision_on"]))
        self.assertEqual(kpis["total_artigos"], 3)
        self.assertEqual(kpis["em_producao"], 2)

    def test_tempo_de_escrita_e_a_mediana_entre_inicio_e_primeira_submissao(self):
        artigos = pd.DataFrame([
            artigo("submetido", started="2024-01-01", first_sub="2024-04-01"),   # 3 meses
            artigo("submetido", started="2024-01-01", first_sub="2024-07-01"),   # 6 meses
        ])
        kpis = painel.calcular_kpis(artigos, pd.DataFrame(columns=["decision", "submitted_on", "decision_on"]))
        self.assertAlmostEqual(kpis["tempo_escrita_meses"], 4.5, delta=0.3)

    def test_sem_decisao_nenhuma_taxa_de_aceite_e_none_nao_zero(self):
        # "sem dado" e "reprovacao total" sao coisas diferentes -- a
        # primeira nao pode disparar a sugestao metodologica de 0%
        artigos = pd.DataFrame([artigo("em_producao")])
        subs = pd.DataFrame([submissao(1, decision=None, submitted="2026-01-01")])
        kpis = painel.calcular_kpis(artigos, subs)
        self.assertIsNone(kpis["taxa_aceite"])

    def test_taxa_de_aceite_conta_so_decisoes_tomadas(self):
        artigos = pd.DataFrame([artigo("publicado"), artigo("rejeitado")])
        hoje = AGORA.strftime("%Y-%m-%d")
        subs = pd.DataFrame([
            submissao(1, decision="aceito", decision_on=hoje),
            submissao(2, decision="rejeitado", decision_on=hoje),
        ])
        kpis = painel.calcular_kpis(artigos, subs)
        self.assertAlmostEqual(kpis["taxa_aceite"], 0.5)

    def test_espera_mediana_so_conta_quem_ainda_nao_tem_decisao(self):
        subs = pd.DataFrame([
            submissao(1, decision=None, submitted=(AGORA - pd.Timedelta(days=60)).strftime("%Y-%m-%d")),
            submissao(2, decision="aceito", submitted=(AGORA - pd.Timedelta(days=400)).strftime("%Y-%m-%d"),
                      decision_on=AGORA.strftime("%Y-%m-%d")),
        ])
        artigos = pd.DataFrame([artigo("submetido"), artigo("publicado")])
        kpis = painel.calcular_kpis(artigos, subs)
        self.assertAlmostEqual(kpis["espera_mediana_meses"], 60 / 30.44, delta=0.1)


class TestAlertaDeLatencia(unittest.TestCase):
    def test_abaixo_do_limite_nao_gera_alerta(self):
        pendentes = pd.DataFrame([{
            "article_id": 1, "title": "X", "internal_code": "ART-0001", "journal": "Rev",
            "submitted_on": AGORA - pd.Timedelta(days=90), "meses_de_espera": 90 / 30.44,
        }])
        self.assertEqual(painel.gerar_alertas_latencia(pendentes, limite_meses=6.0), [])

    def test_acima_do_limite_gera_alerta_com_o_texto_pedido(self):
        pendentes = pd.DataFrame([{
            "article_id": 1, "title": "Efeitos do treino", "internal_code": "ART-0001",
            "journal": "Journal of Sport Science",
            "submitted_on": AGORA - pd.Timedelta(days=250), "meses_de_espera": 250 / 30.44,
        }])
        alertas = painel.gerar_alertas_latencia(pendentes, limite_meses=6.0)
        self.assertEqual(len(alertas), 1)
        self.assertIn("⚠️ ALERTA DE LATÊNCIA ACADÊMICA:", alertas[0]["mensagem"])
        self.assertIn("Efeitos do treino", alertas[0]["mensagem"])
        self.assertIn("Journal of Sport Science", alertas[0]["mensagem"])

    def test_mais_espera_vem_primeiro(self):
        pendentes = pd.DataFrame([
            {"article_id": 1, "title": "Curto", "internal_code": "A1", "journal": "R1",
             "submitted_on": AGORA - pd.Timedelta(days=200), "meses_de_espera": 200 / 30.44},
            {"article_id": 2, "title": "Longo", "internal_code": "A2", "journal": "R2",
             "submitted_on": AGORA - pd.Timedelta(days=400), "meses_de_espera": 400 / 30.44},
        ])
        alertas = painel.gerar_alertas_latencia(pendentes, limite_meses=6.0)
        self.assertIn("Longo", alertas[0]["mensagem"])
        self.assertIn("Curto", alertas[1]["mensagem"])


class TestSugestaoMetodologica(unittest.TestCase):
    def test_sem_nenhuma_decisao_no_ano_nao_sugere_nada(self):
        artigos = pd.DataFrame([artigo("em_producao", linha="Linha A")])
        subs = pd.DataFrame(columns=["article_id", "decision", "decision_on", "linha", "study_type"])
        self.assertIsNone(painel.sugerir_mudanca_metodologica(artigos, subs))

    def test_com_algum_aceite_no_ano_nao_sugere_nada(self):
        artigos = pd.DataFrame([artigo("publicado")]).assign(id=[1])
        hoje = AGORA.strftime("%Y-%m-%d")
        subs = pd.DataFrame([submissao(1, decision="aceito", decision_on=hoje)])
        self.assertIsNone(painel.sugerir_mudanca_metodologica(artigos, subs))

    def test_taxa_zero_de_verdade_sugere_as_linhas_historicamente_aceitas(self):
        artigos = pd.DataFrame([
            artigo("rejeitado", linha="Linha nova"),
            artigo("publicado", linha="Linha consolidada"),
        ]).assign(id=[1, 2])
        hoje = AGORA.strftime("%Y-%m-%d")
        ano_passado = (AGORA - pd.Timedelta(days=400)).strftime("%Y-%m-%d")
        subs = pd.DataFrame([
            submissao(1, decision="rejeitado", decision_on=hoje),
            submissao(2, decision="aceito", decision_on=ano_passado),
        ])
        sugestao = painel.sugerir_mudanca_metodologica(artigos, subs)
        self.assertIsNotNone(sugestao)
        self.assertEqual(sugestao["linhas_mais_aceitas"][0][0], "Linha consolidada")


class TestProjecaoDeRitmo(unittest.TestCase):
    def test_sem_meta_declarada_vem_none(self):
        artigos = pd.DataFrame([artigo("publicado", ano=AGORA.year)])
        projecao = painel.projetar_ritmo(artigos, pd.DataFrame(columns=["code", "target"]), AGORA.year)
        self.assertIsNone(projecao["meta_declarada"])

    def test_meta_declarada_e_lida_da_tabela_goals(self):
        artigos = pd.DataFrame([artigo("publicado", ano=AGORA.year)])
        meta = pd.DataFrame([{"code": "artigos_publicados", "target": 20}])
        projecao = painel.projetar_ritmo(artigos, meta, AGORA.year)
        self.assertEqual(projecao["meta_declarada"], 20)

    def test_projecao_nunca_e_negativa_mesmo_sem_publicacao_nenhuma(self):
        artigos = pd.DataFrame([artigo("em_producao")])
        projecao = painel.projetar_ritmo(artigos, pd.DataFrame(columns=["code", "target"]), AGORA.year)
        self.assertGreaterEqual(projecao["projecao_fim_de_ano"], 0)


if __name__ == "__main__":
    unittest.main()
