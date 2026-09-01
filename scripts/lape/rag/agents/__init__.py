"""Agentes que trabalham sobre o indice semantico.

    literatura  vigia as bases, indexa o que aparece e separa o que e novo
    escrita     redige e revisa sempre ancorado no corpus, com fonte
    coerencia   confere consistencia interna entre capitulos da tese
    revisao     liga o indice ao modulo PRISMA que ja existe no LAPE

Todos partilham a mesma disciplina: nenhuma afirmacao sem trecho de origem
recuperado, e toda saida traz as fontes que a sustentam.
"""
from __future__ import annotations

__all__ = ["base", "literatura", "escrita", "coerencia", "revisao"]
