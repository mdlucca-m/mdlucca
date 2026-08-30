#!/usr/bin/env python3
"""Registrar submissões: o histórico que alimenta tudo o mais.

    python3 -m unittest tests.test_submissoes -v

A tela de submissões já existia e parecia funcionar: o formulário
gravava, a linha aparecia na lista, o aviso dizia "a situação do artigo
foi atualizada". Dois defeitos moravam embaixo disso, e os dois eram
silenciosos — nenhum dava erro, nenhum aparecia no console:

  1. a situação NÃO era atualizada. Registrar o envio deixava o artigo em
     "em produção" para sempre, e o aviso mentia;
  2. a segunda submissão gravava POR CIMA da primeira, porque a numeração
     automática recomeçava em 1 a cada chamada. Quem ressubmetia perdia a
     recusa anterior — justamente o dado que se queria construir.

Estes testes existem para que nenhum dos dois volte.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_excel, metrics  # noqa: E402
from lape.agents import curator  # noqa: E402
from lape.db import Database  # noqa: E402


class BaseSubmissao(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Database(Path(tmp.name) / "t.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()
        ingest_excel.ingest_articles(self.db, [
            {"title": "Exercício e fibromialgia", "status": "Em produção",
             "started_on": "2026-01-10"},
            {"title": "Um artigo engavetado", "status": "Arquivado"},
        ])
        ingest_excel.ingest_rejection_reasons(self.db, [
            {"Código": "escopo", "Motivo": "Fora do escopo", "Categoria": "editorial"}])
        self.db.conn.commit()

    def pela_tela(self, **campos):
        """O mesmo caminho da Área do integrante: POST /api/submissions."""
        return curator.register(self.db, "submissions", campos)

    def situacao(self, titulo="Exercício e fibromialgia"):
        return self.db.scalar("SELECT status FROM articles WHERE title = ?", (titulo,))

    def tentativas(self):
        return self.db.dicts(
            "SELECT attempt_no, journal, submitted_on, decision, decision_on"
            "  FROM submissions ORDER BY attempt_no")


class TestASituacaoAcompanha(BaseSubmissao):
    def test_registrar_o_envio_move_o_artigo_para_submetido(self):
        """O defeito nº 1, e o mais grave: a tela prometia e não cumpria.

        `derive_status` só mexe em artigo destravado, e o destravamento
        exigia um DESFECHO — mas uma submissão recém-registrada não tem
        desfecho nenhum, ela está em avaliação. O artigo ficava parado.
        """
        self.assertEqual(self.situacao(), "em_producao")
        self.pela_tela(Artigo="Exercício e fibromialgia", Revista="Pain",
                       **{"Data de submissão": "2026-03-02"})
        self.assertEqual(self.situacao(), "submetido")

    def test_a_data_da_primeira_submissao_entra_no_artigo(self):
        # é dela que sai o tempo de submissão até o aceite
        self.pela_tela(Artigo="Exercício e fibromialgia", Revista="Pain",
                       **{"Data de submissão": "2026-03-02"})
        self.assertEqual(
            self.db.scalar("SELECT first_submission_on FROM articles WHERE id = 1"),
            "2026-03-02")

    def test_a_situacao_percorre_o_caminho_inteiro(self):
        submeter = lambda rev, dia: self.pela_tela(
            Artigo="Exercício e fibromialgia", Revista=rev,
            **{"Data de submissão": dia})
        decidir = lambda n, dec, dia: self.pela_tela(
            Artigo="Exercício e fibromialgia", Tentativa=n,
            **{"Decisão": dec, "Data da decisão": dia})
        submeter("Pain", "2026-03-02")
        self.assertEqual(self.situacao(), "submetido")
        decidir(1, "Rejeitado", "2026-05-10")
        self.assertEqual(self.situacao(), "rejeitado")
        submeter("Rheumatology", "2026-06-01")
        self.assertEqual(self.situacao(), "submetido")
        decidir(2, "Aceito", "2026-09-15")
        self.assertEqual(self.situacao(), "aceito")
        self.assertEqual(
            self.db.scalar("SELECT accepted_on FROM articles WHERE id = 1"), "2026-09-15")

    def test_artigo_arquivado_nao_e_desengavetado(self):
        """`arquivado` é a única situação que o histórico não deduz.

        É decisão de quem coordena — "este não vai adiante" —, e nenhuma
        tentativa a contradiz. Sem a guarda, registrar uma submissão
        antiga trazia o artigo de volta para "submetido" sozinho.
        """
        self.pela_tela(Artigo="Um artigo engavetado", Revista="Pain",
                       **{"Data de submissão": "2025-01-10"})
        self.assertEqual(self.situacao("Um artigo engavetado"), "arquivado")


class TestONumeroDaTentativa(BaseSubmissao):
    def test_a_segunda_submissao_nao_apaga_a_primeira(self):
        """O defeito nº 2, e era perda de dado.

        A chave da tabela é (artigo, tentativa). Numerando de 1 a cada
        chamada, a ressubmissão caía por cima da tentativa anterior: a
        linha ficava com a revista nova, a data de decisão antiga e um
        motivo de recusa que já não correspondia a nada.
        """
        self.pela_tela(Artigo="Exercício e fibromialgia", Revista="Pain",
                       **{"Data de submissão": "2026-03-02"})
        self.pela_tela(Artigo="Exercício e fibromialgia", Tentativa=1,
                       **{"Decisão": "Rejeitado", "Data da decisão": "2026-05-10",
                          "Motivo da recusa": "Fora do escopo"})
        self.pela_tela(Artigo="Exercício e fibromialgia", Revista="Rheumatology",
                       **{"Data de submissão": "2026-06-01"})

        linhas = self.tentativas()
        self.assertEqual(len(linhas), 2, "a ressubmissão gravou por cima da primeira")
        self.assertEqual(linhas[0]["journal"], "Pain")
        self.assertEqual(linhas[0]["decision"], "rejeitado")
        self.assertEqual(linhas[0]["decision_on"], "2026-05-10")
        self.assertEqual(linhas[1]["attempt_no"], 2)
        self.assertEqual(linhas[1]["journal"], "Rheumatology")
        self.assertIsNone(linhas[1]["decision_on"])

    def test_o_desfecho_cai_sobre_a_tentativa_certa(self):
        # registrar a recusa não pode criar uma tentativa nova
        self.pela_tela(Artigo="Exercício e fibromialgia", Revista="Pain",
                       **{"Data de submissão": "2026-03-02"})
        self.pela_tela(Artigo="Exercício e fibromialgia", Revista="Rheumatology",
                       **{"Data de submissão": "2026-06-01"})
        self.pela_tela(Artigo="Exercício e fibromialgia", Tentativa=1,
                       **{"Decisão": "Rejeitado", "Data da decisão": "2026-05-10"})
        linhas = self.tentativas()
        self.assertEqual(len(linhas), 2)
        self.assertEqual(linhas[0]["decision"], "rejeitado")
        self.assertEqual(linhas[0]["journal"], "Pain")   # a revista não se perdeu
        self.assertEqual(linhas[1]["decision"], "em_avaliacao")

    def test_a_planilha_continua_idempotente(self):
        """A planilha é a declaração COMPLETA do histórico do artigo.

        Numerar de 1 lá é o que faz reimportar não criar tentativa nova —
        e é por isso que o caminho da planilha não continua a numeração.
        """
        linhas = [
            {"article": "Exercício e fibromialgia", "journal": "A",
             "submitted_on": "2025-01-10", "decision": "Rejeitado"},
            {"article": "Exercício e fibromialgia", "journal": "B",
             "submitted_on": "2025-04-10"},
        ]
        ingest_excel.ingest_submissions(self.db, linhas)
        ingest_excel.ingest_submissions(self.db, linhas)
        ingest_excel.ingest_submissions(self.db, linhas)
        self.assertEqual(len(self.tentativas()), 2)

    def test_a_api_continua_de_onde_a_planilha_parou(self):
        ingest_excel.ingest_submissions(self.db, [
            {"article": "Exercício e fibromialgia", "journal": "A",
             "submitted_on": "2025-01-10", "decision": "Rejeitado"},
            {"article": "Exercício e fibromialgia", "journal": "B",
             "submitted_on": "2025-04-10", "decision": "Rejeitado"}])
        self.pela_tela(Artigo="Exercício e fibromialgia", Revista="C",
                       **{"Data de submissão": "2026-01-10"})
        linhas = self.tentativas()
        self.assertEqual([l["attempt_no"] for l in linhas], [1, 2, 3])
        self.assertEqual(linhas[2]["journal"], "C")


class TestOQueIssoDestrava(BaseSubmissao):
    """Registrar submissão é o que faz metade do painel sair do zero."""

    def historico(self):
        submeter = lambda rev, dia: self.pela_tela(
            Artigo="Exercício e fibromialgia", Revista=rev,
            **{"Data de submissão": dia})
        submeter("Pain", "2026-03-02")
        self.pela_tela(Artigo="Exercício e fibromialgia", Tentativa=1,
                       **{"Decisão": "Rejeitado", "Data da decisão": "2026-05-10",
                          "Motivo da recusa": "Fora do escopo"})
        submeter("Rheumatology", "2026-06-01")
        self.pela_tela(Artigo="Exercício e fibromialgia", Tentativa=2,
                       **{"Decisão": "Aceito", "Data da decisão": "2026-09-15"})

    def test_a_taxa_de_aceite_deixa_de_ser_zero(self):
        self.historico()
        s = metrics.submission_metrics(self.db)
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["accepted"], 1)
        self.assertEqual(s["rejected"], 1)
        self.assertEqual(s["acceptance_rate"], 50.0)

    def test_o_motivo_da_recusa_alimenta_o_grafico(self):
        self.historico()
        motivos = metrics.submission_metrics(self.db)["rejection_reasons"]
        self.assertTrue(motivos, "a recusa não chegou ao gráfico de motivos")

    def test_o_tempo_ate_o_aceite_passa_a_existir(self):
        # 2026-03-02 -> 2026-09-15
        self.historico()
        dias = self.db.scalar(
            "SELECT days_submission_to_acceptance FROM v_articles_full WHERE id = 1")
        self.assertEqual(dias, 197)

    def test_a_contagem_de_tentativas_sai_da_view(self):
        self.historico()
        linha = self.db.dicts(
            "SELECT submission_attempts, rejections FROM v_articles_full WHERE id = 1")[0]
        self.assertEqual(linha["submission_attempts"], 2)
        self.assertEqual(linha["rejections"], 1)

    def test_o_simulador_de_cenarios_para_de_avisar_que_falta_base(self):
        self.historico()
        self.assertEqual(
            metrics.build_payload(self.db)["cenario"]["submissoes_registradas"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
