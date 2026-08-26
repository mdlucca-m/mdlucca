"""Agentes digitais do LAPE.

rastreador  (tracker.py)  busca informacao nova nas bases bibliograficas
                          em tempo real e a deixa pronta para revisao.
curador     (curator.py)  mantem o banco: cadastra, normaliza, valida,
                          recalcula indicadores e publica o painel.
"""
from . import curator, tracker

__all__ = ["tracker", "curator"]
