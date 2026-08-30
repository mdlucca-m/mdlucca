#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A base do simulador de cenarios: o que e medido e o que e suposto.

Um simulador de cenarios e um lugar perigoso num painel. Ele desenha uma
linha para o futuro com a mesma tinta com que o painel desenha o passado,
e quem olha de longe nao distingue as duas. Este modulo existe para
manter a distincao explicita: ele devolve a serie REAL, os parametros que
puderam ser MEDIDOS na base do laboratorio, e a lista do que NAO tem base
-- que a tela e obrigada a apresentar como suposicao, nao como dado.

O modelo e deliberadamente simples:

    publicacoes(t) = ritmo x (pesquisadores(t) / pesquisadores(hoje))

O ritmo e publicacoes por ano; o segundo fator escala pelo tamanho da
equipe. Nao ha termo de submissao nem taxa de aceite, e a razao e
factual: o laboratorio nao registra submissoes. Um modelo com
`submissoes x taxa_de_aceite` pareceria mais serio e seria inteiramente
inventado -- todo parametro dele viria de mim, nenhum dos dados.

Quando o registro de submissoes existir, o modelo pode ganhar esses
termos; ate la, o simulador diz o que faz e o que nao sabe.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .db import Database

# O ano corrente ainda esta acontecendo: usa-lo como base do ritmo faria
# todo cenario partir de um ano pela metade.
ANOS_DE_BASE = 3
HORIZONTE_PADRAO = 5
ATRASO_PADRAO_MESES = 18


def _mediana(valores: list[float]) -> float | None:
    dados = sorted(v for v in valores if v is not None)
    if not dados:
        return None
    meio = len(dados) // 2
    return dados[meio] if len(dados) % 2 else (dados[meio - 1] + dados[meio]) / 2


def base(db: Database, horizonte: int = HORIZONTE_PADRAO) -> dict[str, Any]:
    """Serie real, parametros medidos e o que ficou sem base."""
    hoje = date.today().year
    serie = _serie_anual(db, hoje)
    anos = [a for a, _ in serie]
    valores = [n for _, n in serie]

    # O ritmo de partida vem dos ultimos anos COMPLETOS. Incluir o ano
    # corrente puxaria o ritmo para baixo em janeiro e para cima em
    # dezembro, e o cenario mudaria sozinho conforme o calendario.
    completos = [(a, n) for a, n in serie if a < hoje]
    recentes = [n for _, n in completos[-ANOS_DE_BASE:]]
    ritmo = round(sum(recentes) / len(recentes), 2) if recentes else 0.0

    ativos = _pesquisadores_ativos(db, hoje)
    equipe = int(db.scalar("SELECT COUNT(*) FROM members") or 0)
    pico = max(((a, n) for a, n in serie), key=lambda x: x[1], default=(None, 0))

    # Cada parametro carrega de onde veio. `medido` e o que a tela pode
    # apresentar como fato; o resto entra como suposicao, com o motivo.
    parametros = [
        {"chave": "ritmo", "rotulo": "Publicações por ano",
         "valor": ritmo, "unidade": "por ano", "unidade_um": "por ano",
         "medido": bool(recentes),
         "base": f"média dos últimos {len(recentes)} anos completos" if recentes
                 else "não há ano completo com produção",
         "minimo": 0, "maximo": max(round(ritmo * 3), 12), "passo": 0.5},
        {"chave": "pesquisadores", "rotulo": "Pesquisadores ativos",
         "valor": ativos or equipe, "unidade": "pessoas", "unidade_um": "pessoa",
         "medido": bool(ativos),
         "base": (f"{ativos} assinaram algo publicado nos últimos dois anos"
                  if ativos else
                  f"ninguém publicou nos últimos dois anos; usando os {equipe} "
                  "do cadastro"),
         "minimo": 1, "maximo": max((ativos or equipe) * 3, 12), "passo": 1},
        {"chave": "atraso", "rotulo": "Atraso até aparecer",
         "valor": ATRASO_PADRAO_MESES, "unidade": "meses", "unidade_um": "mês",
         # Isto NAO e medido, e dizer que e seria a mentira mais facil
         # desta tela: sem data de submissao no banco, nao ha como saber.
         "medido": False,
         "base": ("o banco não guarda data de submissão, então o intervalo "
                  "até a indexação não pôde ser medido"),
         "minimo": 0, "maximo": 36, "passo": 3},
    ]

    return {
        "anos": anos, "serie": valores, "ano_corrente": hoje,
        "horizonte": horizonte, "parametros": parametros,
        "pico": {"ano": pico[0], "valor": pico[1]} if pico[0] else None,
        "melhor_por_pesquisador": _melhor_por_pesquisador(serie, ativos or equipe),
        "sem_base": [p["chave"] for p in parametros if not p["medido"]],
        "submissoes_registradas": int(
            db.scalar("SELECT COUNT(*) FROM submissions") or 0),
    }


def _serie_anual(db: Database, hoje: int) -> list[tuple[int, int]]:
    """Publicacoes por ano, do primeiro ano com producao ate hoje."""
    linhas = db.dicts(
        "SELECT year_published AS ano, COUNT(*) AS n FROM articles"
        " WHERE status = 'publicado' AND year_published IS NOT NULL"
        " GROUP BY ano ORDER BY ano")
    if not linhas:
        return []
    primeiro = int(linhas[0]["ano"])
    conta = {int(l["ano"]): int(l["n"]) for l in linhas}
    return [(a, conta.get(a, 0)) for a in range(primeiro, hoje + 1)]


def _pesquisadores_ativos(db: Database, hoje: int) -> int:
    """Quem assinou algo publicado nos ultimos dois anos.

    Contar o cadastro inteiro inflaria o denominador com quem ja saiu do
    laboratorio, e o cenario diria que basta cada um publicar menos.
    """
    return int(db.scalar(
        "SELECT COUNT(DISTINCT aa.member_id) FROM article_authors aa"
        "  JOIN articles a ON a.id = aa.article_id"
        " WHERE a.status = 'publicado' AND a.year_published >= ?",
        (hoje - 2,)) or 0)


def _melhor_por_pesquisador(serie: list[tuple[int, int]], pessoas: int) -> dict[str, Any] | None:
    """O melhor ano do laboratorio, por pesquisador.

    E a regua contra a qual um cenario se mede: pedir tres artigos por
    pessoa por ano a um grupo que nunca passou de um e um numero, nao um
    plano. Sem essa comparacao, qualquer barra arrastada para a direita
    parece igualmente possivel.
    """
    if not serie or pessoas <= 0:
        return None
    ano, valor = max(serie, key=lambda x: x[1])
    return {"ano": ano, "valor": valor, "pessoas": pessoas,
            "por_pessoa": round(valor / pessoas, 2)}
