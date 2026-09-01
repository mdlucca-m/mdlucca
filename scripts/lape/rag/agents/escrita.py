"""Agente de escrita com fundamentacao.

Redige ou revisa um trecho academico sempre ancorado no corpus indexado.
A diferenca em relacao a pedir texto a um modelo qualquer esta em duas
travas: o contexto vem da busca, e o agente recusa afirmacao que nenhum
trecho recuperado sustente.
"""
from __future__ import annotations

from .. import config
from ..llm import LLMIndisponivel, perguntar
from ..store import Filtro, VectorStore
from .base import DISCIPLINA, SaidaAgente, recuperar, registrar

SISTEMA = DISCIPLINA + """
Voce redige trechos de artigo cientifico e de tese em portugues do Brasil.

Estrutura da sua resposta:
- O texto pedido, pronto para colar no manuscrito, sem titulo inventado e
  sem meta-comentario.
- Depois, sob o rotulo "Lacunas", a lista do que o corpus nao sustentou e
  que portanto ficou de fora, com a busca que faltaria fazer.

Estilo: periodos de extensao variada, conectivos que ligam paragrafo a
paragrafo, verbos precisos e variados, voz ativa sempre que possivel,
nenhum gerundio. Nao use adjetivo de enfase sem dado que o justifique.
"""

MODOS = {
    "redigir": "Redija o trecho solicitado.",
    "revisar": ("Revise o texto fornecido: corrija a gramatica, melhore a "
                "fluidez e confira cada afirmacao contra os trechos "
                "recuperados. Marque com [?] toda afirmacao do texto "
                "original que o corpus nao sustenta."),
    "expandir": ("Amplie o texto fornecido com o que os trechos recuperados "
                 "acrescentam, sem repetir o que ja esta dito."),
    "resumir": "Condense o texto fornecido sem perder nenhuma afirmacao com fonte.",
}


def executar(store: VectorStore, instrucao: str, *,
             modo: str = "redigir",
             texto_base: str | None = None,
             consultas: list[str] | None = None,
             k: int = 10,
             filtro: Filtro | None = None,
             palavras: int | None = None,
             embedder=None) -> SaidaAgente:
    if modo not in MODOS:
        raise ValueError(f"modo '{modo}' desconhecido; use {', '.join(MODOS)}")

    buscas = consultas or [instrucao]
    if texto_base:
        buscas = buscas + [texto_base[:400]]
    contexto, fontes, aviso = recuperar(store, buscas, k=k, filtro=filtro,
                                        embedder=embedder)
    if not fontes:
        return SaidaAgente(
            agente="escrita",
            texto=("Nenhum trecho do corpus responde a esta instrucao. "
                   "Indexe as fontes pertinentes antes de pedir o texto: "
                   "'lape_agent.py rag indexar --pasta <caminho>'."),
            consultas=buscas, aviso=aviso)

    alvo = f"\nExtensao alvo: cerca de {palavras} palavras." if palavras else ""
    partes = [f"Instrucao: {instrucao}", f"Modo: {MODOS[modo]}{alvo}"]
    if texto_base:
        partes.append(f"\nTexto de partida:\n\"\"\"\n{texto_base}\n\"\"\"")
    partes.append(f"\nTrechos recuperados do corpus:\n\n{contexto}")

    try:
        r = perguntar(SISTEMA, [{"role": "user", "content": "\n".join(partes)}],
                      max_tokens=config.LLM_MAX_TOKENS)
    except LLMIndisponivel as exc:
        return SaidaAgente(agente="escrita", fontes=fontes, consultas=buscas,
                           texto=(f"O modelo nao esta acessivel: {exc}\n\n"
                                  "O contexto recuperado segue abaixo para uso "
                                  f"manual.\n\n{contexto}"), aviso=aviso)
    uso = {"modelo": r.modelo, "entrada": r.entrada, "saida": r.saida,
           "cache_lido": r.cache_lido, "custo_estimado": round(r.custo_estimado, 4)}
    registrar(store, "escrita", instrucao, uso)
    return SaidaAgente(agente="escrita", texto=r.recusa or r.texto, fontes=fontes,
                       consultas=buscas, uso=uso, aviso=aviso)
