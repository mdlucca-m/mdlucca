"""Agente de coerencia da tese.

Le os capitulos ja indexados e procura o que so aparece na comparacao
entre eles: objetivo anunciado que nenhum resultado responde, metodo
descrito de um jeito e aplicado de outro, numero que muda de valor entre
secoes, afirmacao da discussao sem respaldo nos resultados.
"""
from __future__ import annotations

from .. import config
from ..llm import LLMIndisponivel, perguntar
from ..store import Filtro, VectorStore
from .base import DISCIPLINA, SaidaAgente, recuperar, registrar

SISTEMA = DISCIPLINA + """
Voce audita a consistencia interna de um trabalho academico longo.

Procure, nesta ordem de prioridade:
1. Objetivo especifico anunciado que nenhum resultado responde, e resultado
   apresentado que nenhum objetivo previa.
2. Divergencia numerica: o mesmo indicador com valores diferentes em
   secoes diferentes.
3. Afirmacao da discussao ou da conclusao que os resultados nao sustentam.
4. Metodo descrito de um modo e relatado de outro.
5. Termo tecnico usado com dois sentidos ao longo do texto.

Formato da resposta: uma lista numerada. Cada item traz o achado em uma
frase, os trechos [n] que o revelam e a correcao sugerida. Ordene por
gravidade. Quando nada aparecer numa categoria, diga isso em uma linha, e
nao invente achado para preencher.
"""

EIXOS = [
    ("objetivos", ["objetivo geral do estudo", "objetivos especificos",
                   "o estudo se propoe a", "a pergunta de pesquisa"]),
    ("metodo", ["delineamento do estudo", "participantes e amostra",
                "procedimento de coleta", "analise estatistica adotada"]),
    ("resultados", ["os resultados mostram", "a tabela apresenta",
                    "diferenca significativa", "tamanho de efeito"]),
    ("discussao", ["a discussao interpreta", "estes achados indicam",
                   "em comparacao com a literatura", "limitacoes do estudo"]),
    ("conclusao", ["conclui-se que", "sintese dos achados"]),
]


def executar(store: VectorStore, *, k: int = 6,
             filtro: Filtro | None = None,
             foco: str | None = None,
             embedder=None) -> SaidaAgente:
    consultas = [c for _, cs in EIXOS for c in cs]
    if foco:
        consultas = [foco] + consultas
    contexto, fontes, aviso = recuperar(store, consultas, k=k, filtro=filtro,
                                        embedder=embedder)
    if not fontes:
        return SaidaAgente(agente="coerencia", consultas=consultas, aviso=aviso,
                           texto=("Nenhum capitulo indexado. Rode "
                                  "'lape_agent.py rag indexar --pasta <tese>' antes."))
    pedido = (
        "Audite a consistencia interna do trabalho a partir dos trechos abaixo. "
        "Eles vem de secoes diferentes do mesmo documento ou de documentos do "
        "mesmo projeto.\n\n"
        + (f"Foco pedido pelo autor: {foco}\n\n" if foco else "")
        + contexto
    )
    try:
        r = perguntar(SISTEMA, [{"role": "user", "content": pedido}],
                      max_tokens=config.LLM_MAX_TOKENS)
    except LLMIndisponivel as exc:
        return SaidaAgente(agente="coerencia", fontes=fontes, consultas=consultas,
                           aviso=aviso,
                           texto=f"O modelo nao esta acessivel: {exc}")
    uso = {"modelo": r.modelo, "entrada": r.entrada, "saida": r.saida,
           "cache_lido": r.cache_lido, "custo_estimado": round(r.custo_estimado, 4)}
    registrar(store, "coerencia", foco or "auditoria completa", uso)
    return SaidaAgente(agente="coerencia", texto=r.recusa or r.texto, fontes=fontes,
                       consultas=consultas, uso=uso, aviso=aviso)
