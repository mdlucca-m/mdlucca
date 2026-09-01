"""Agente de revisao sistematica.

Liga o indice semantico ao modulo PRISMA que ja existe no LAPE. Faz tres
coisas que economizam o tempo mais caro de uma revisao:

  ordenar    poe primeiro, na fila de triagem, as referencias que mais se
             parecem com os criterios de inclusao — o revisor humano
             decide, mas decide na ordem certa
  sugerir    propoe decisao com justificativa contra os criterios, sempre
             como sugestao gravada a parte, nunca como decisao final
  extrair    pre-preenche os campos de extracao a partir do resumo

A decisao final continua humana. O agente nunca escreve em screenings.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field

from .. import config
from ..llm import LLMIndisponivel, perguntar
from ..search import buscar
from ..store import Filtro, SqliteStore, VectorStore
from .base import DISCIPLINA, SaidaAgente, registrar

log = logging.getLogger("lape.rag.agents.revisao")

SISTEMA = DISCIPLINA + """
Voce assiste a triagem de titulo e resumo de uma revisao sistematica.

Para cada referencia, devolva uma linha no formato
  n | INCLUIR ou EXCLUIR ou DUVIDA | motivo em ate quinze palavras

Regras de decisao:
- EXCLUIR exige que o resumo contradiga um criterio de forma explicita.
- Resumo ausente ou vago nunca gera EXCLUIR; gera DUVIDA.
- DUVIDA e a resposta correta sempre que a decisao dependa do texto
  completo. Nao force uma escolha para parecer decidido.
- O motivo cita o criterio violado ou atendido, nao uma impressao geral.

Sua saida e sugestao. O revisor humano decide, e ele precisa que a
justificativa seja curta o bastante para conferir em segundos.
"""


@dataclass
class Criterios:
    pergunta: str = ""
    populacao: str = ""
    intervencao: str = ""
    comparacao: str = ""
    desfecho: str = ""
    desenhos: str = ""

    def texto(self) -> str:
        campos = [("Pergunta", self.pergunta), ("Populacao", self.populacao),
                  ("Intervencao", self.intervencao), ("Comparacao", self.comparacao),
                  ("Desfecho", self.desfecho), ("Desenhos aceitos", self.desenhos)]
        return "\n".join(f"{k}: {v}" for k, v in campos if v)

    def consulta(self) -> str:
        return " ".join(p for p in (self.pergunta, self.populacao, self.intervencao,
                                    self.desfecho) if p)


def criterios_da_revisao(conn: sqlite3.Connection, review: str | int) -> Criterios:
    conn.row_factory = sqlite3.Row
    campo = "id" if str(review).isdigit() else "code"
    linha = conn.execute(
        f"SELECT question, population, intervention, comparison, outcome,"
        f" study_designs FROM reviews WHERE {campo} = ?", (review,)).fetchone()
    if linha is None:
        raise LookupError(f"revisao '{review}' nao encontrada")
    return Criterios(pergunta=linha["question"] or "",
                     populacao=linha["population"] or "",
                     intervencao=linha["intervention"] or "",
                     comparacao=linha["comparison"] or "",
                     desfecho=linha["outcome"] or "",
                     desenhos=linha["study_designs"] or "")


def refs_pendentes(conn: sqlite3.Connection, review: str | int,
                   limite: int = 40) -> list[dict]:
    """Referencias da revisao ainda sem decisao de triagem."""
    conn.row_factory = sqlite3.Row
    campo = "r.id" if str(review).isdigit() else "r.code"
    linhas = conn.execute(
        "SELECT f.id, f.title, f.abstract, f.authors, f.year, f.journal, f.doi"
        "  FROM refs f JOIN reviews r ON r.id = f.review_id"
        f" WHERE {campo} = ?"
        "   AND NOT EXISTS (SELECT 1 FROM screenings s WHERE s.ref_id = f.id)"
        " ORDER BY f.id LIMIT ?", (review, limite)).fetchall()
    return [dict(l) for l in linhas]


def ordenar_por_afinidade(store: VectorStore, criterios: Criterios,
                          refs: list[dict]) -> list[dict]:
    """Poe na frente as referencias mais proximas dos criterios.

    A ordenacao usa o proprio indice: cada referencia e comparada com o
    resultado da busca pelos criterios. Sem indice util, devolve a ordem
    original em vez de inventar prioridade.
    """
    consulta = criterios.consulta()
    if not consulta:
        return refs
    try:
        r = buscar(store, consulta, k=200,
                   filtro=Filtro(ref_table="refs"))
    except Exception as exc:
        log.warning("ordenacao por afinidade indisponivel: %s", exc)
        return refs
    if not r.hits or not isinstance(store, SqliteStore):
        return refs
    # Do trecho recuperado ate a referencia de origem: rag_documents guarda
    # a tabela e o id da linha que deu origem ao documento.
    doc_ids = {h.doc_id for h in r.hits}
    marcas = ",".join("?" * len(doc_ids))
    mapa = {linha["id"]: linha["ref_id"] for linha in store.conn.execute(
        f"SELECT id, ref_id FROM rag_documents WHERE id IN ({marcas})"
        "   AND ref_table = 'refs' AND ref_id IS NOT NULL", list(doc_ids))}
    peso: dict[int, float] = {}
    for h in r.hits:
        ref_id = mapa.get(h.doc_id)
        if ref_id is not None:
            peso[ref_id] = max(peso.get(ref_id, 0.0), h.score)
    if not peso:
        return refs
    return sorted(refs, key=lambda ref: -peso.get(ref["id"], 0.0))


def executar(store: VectorStore, conn: sqlite3.Connection, review: str | int, *,
             limite: int = 30, gravar: bool = False) -> SaidaAgente:
    criterios = criterios_da_revisao(conn, review)
    refs = refs_pendentes(conn, review, limite)
    if not refs:
        return SaidaAgente(agente="revisao",
                           texto=f"A revisao '{review}' nao tem referencia pendente.")

    lista = "\n\n".join(
        f"[{i}] {r['title'] or '(sem titulo)'}\n"
        f"Autores: {r['authors'] or '?'} | Ano: {r['year'] or '?'} | "
        f"Periodico: {r['journal'] or '?'}\n"
        f"Resumo: {(r['abstract'] or '(resumo ausente)')[:1200]}"
        for i, r in enumerate(refs, 1))
    pedido = (f"Criterios da revisao:\n{criterios.texto()}\n\n"
              f"Referencias pendentes de triagem:\n\n{lista}")
    try:
        resposta = perguntar(SISTEMA, [{"role": "user", "content": pedido}])
    except LLMIndisponivel as exc:
        return SaidaAgente(
            agente="revisao",
            texto=(f"Triagem assistida indisponivel: {exc}\n\n"
                   f"{len(refs)} referencias pendentes nesta revisao."))

    uso = {"modelo": resposta.modelo, "entrada": resposta.entrada,
           "saida": resposta.saida, "cache_lido": resposta.cache_lido,
           "custo_estimado": round(resposta.custo_estimado, 4)}
    registrar(store, "revisao", str(review), uso)

    if gravar:
        _gravar_sugestoes(conn, refs, resposta.texto)

    cabecalho = (f"Revisao '{review}': {len(refs)} referencias pendentes analisadas.\n"
                 "As decisoes abaixo sao sugestoes; a triagem definitiva continua "
                 "com o revisor humano.\n")
    return SaidaAgente(agente="revisao", texto=cabecalho + "\n" + (resposta.recusa or resposta.texto),
                       consultas=[criterios.consulta()], uso=uso,
                       fontes=[{"n": i, "citacao": f"ref #{r['id']}", "uri":
                                f"lape://refs/{r['id']}", "titulo": r["title"],
                                "doi": r["doi"], "ano": r["year"], "secao": None,
                                "trecho": 0, "score": 0.0}
                               for i, r in enumerate(refs, 1)])


def _gravar_sugestoes(conn: sqlite3.Connection, refs: list[dict], texto: str) -> int:
    """Guarda a sugestao em rag_runs, jamais em screenings.

    A tabela de triagem e o registro do julgamento humano; poluir esse
    registro com sugestao de maquina destruiria a auditoria da revisao.
    """
    payload = {"refs": [r["id"] for r in refs], "sugestao": texto}
    conn.execute(
        "INSERT INTO rag_runs(kind, agent, query, detail) VALUES (?,?,?,?)",
        ("agent", "revisao_sugestoes", f"{len(refs)} refs",
         json.dumps(payload, ensure_ascii=False)))
    conn.commit()
    return len(refs)
