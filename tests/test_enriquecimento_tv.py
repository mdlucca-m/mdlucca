"""Testes para enriquecimento de dados da TV."""
import sys
from datetime import date, timedelta
sys.path.insert(0, "scripts")

from lape import tv
from lape.db import Database


class TestComparacoes:
    """Valida cálculo de comparações (este mês vs. anterior)."""

    def test_comparacoes_publica_ou_nao(self):
        """Retorna comparações mesmo com zero publicações."""
        db = Database(":memory:")
        db.exec("CREATE TABLE articles (id INTEGER, title TEXT, journal TEXT, status TEXT, published_on TEXT, year_published INTEGER, accepted_on TEXT)")
        db.exec("CREATE TABLE submissions (id INTEGER, article_id INTEGER, journal TEXT, submitted_on TEXT)")

        comp = tv._comparacoes(db, date(2026, 9, 23))
        assert "mes_atual" in comp
        assert "publicacoes" in comp
        assert "aceites" in comp
        assert "taxa_aceite_anual" in comp


class TestSazonalidade:
    """Analisa padrões sazonais."""

    def test_sazonalidade_estrutura(self):
        """Retorna estrutura esperada."""
        db = Database(":memory:")
        db.exec("CREATE TABLE articles (id INTEGER, title TEXT, journal TEXT, status TEXT, published_on TEXT, year_published INTEGER, accepted_on TEXT)")

        saz = tv._sazonalidade(db, date(2026, 9, 23))
        assert "picos_publicacao" in saz
        assert "picos_aceite" in saz
        assert isinstance(saz["picos_publicacao"], list)
        assert isinstance(saz["picos_aceite"], list)


class TestAlertas:
    """Identifica eventos urgentes."""

    def test_alertas_estrutura(self):
        """Retorna alertas esperados."""
        db = Database(":memory:")
        db.exec("CREATE TABLE articles (id INTEGER, title TEXT, journal TEXT, status TEXT, published_on TEXT, year_published INTEGER, accepted_on TEXT)")
        db.exec("CREATE TABLE submissions (id INTEGER, article_id INTEGER, journal TEXT, submitted_on TEXT)")

        ale = tv._alertas(db, date(2026, 9, 23))
        assert "aceites_ultimos_7d" in ale
        assert "pubs_recentes" in ale
        assert "revistas_em_processo" in ale
        assert "dias_sem_submissao" in ale


class TestHealthRotina:
    """Verifica saúde da rotina automática."""

    def test_health_rotina_estrutura(self):
        """Retorna health checks."""
        db = Database(":memory:")
        # Simula tabelas mínimas
        db.exec("CREATE TABLE IF NOT EXISTS tarefas (codigo TEXT, ultima_rodada TEXT, erro TEXT, proxima_rodada TEXT)")
        db.exec("CREATE TABLE IF NOT EXISTS log_tarefas (tarefa_codigo TEXT, criado_em TEXT, sucesso INTEGER)")

        health = tv._health_rotina(db)
        assert "tarefas_ok" in health
        assert "tarefas_total" in health
        assert "erros" in health
        assert "proximos_em_horas" in health
