"""Servidor MCP do corpus do LAPE.

Fala JSON-RPC 2.0 sobre stdin e stdout, sem dependencia alem da biblioteca
padrao. Qualquer cliente MCP — Claude Code, Claude Desktop, um agente
proprio — ganha acesso ao indice semantico do laboratorio.

Registro no cliente:

    {
      "mcpServers": {
        "lape-corpus": {
          "command": "python3",
          "args": ["/caminho/scripts/lape_agent.py", "rag", "mcp"],
          "env": {"VOYAGE_API_KEY": "...", "LAPE_DB": "/dados/db.sqlite"}
        }
      }
    }

Todo erro de ferramenta volta como resultado com ``isError``, e nao como
erro de protocolo: um cliente nunca deve perder a sessao porque uma busca
falhou.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

from .. import config as base_config
from . import config
from .chunk import ExtractionError, load
from .index import indexar_documentos
from .search import buscar, vizinhos
from .store import Filtro, SqliteStore

log = logging.getLogger("lape.rag.mcp")

NOME = "lape-corpus"
VERSAO = "1.0.0"
PROTOCOLO_PADRAO = "2025-06-18"

FERRAMENTAS: list[dict] = [
    {
        "name": "buscar_corpus",
        "description": (
            "Busca semantica e lexica no corpus do laboratorio: artigos, "
            "referencias de revisoes sistematicas, capitulos da tese e notas. "
            "Devolve os trechos mais relevantes com a citacao rastreavel de "
            "cada um. Use antes de afirmar qualquer coisa sobre o que a "
            "literatura do grupo diz."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "consulta": {"type": "string",
                             "description": "pergunta ou tema, em linguagem natural"},
                "k": {"type": "integer", "default": 8,
                      "description": "quantos trechos devolver (1 a 30)"},
                "tipos": {"type": "array", "items": {"type": "string"},
                          "description": "filtra por tipo: article, ref, tese, nota, externo"},
                "ano_de": {"type": "integer"},
                "ano_ate": {"type": "integer"},
            },
            "required": ["consulta"],
        },
    },
    {
        "name": "checar_afirmacao",
        "description": (
            "Verifica se o corpus sustenta uma afirmacao. Devolve os trechos "
            "que a apoiam, os que a contradizem e um veredito sobre a "
            "cobertura. Use para conferir frases de um manuscrito antes de "
            "submeter."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "afirmacao": {"type": "string"},
                "k": {"type": "integer", "default": 6},
            },
            "required": ["afirmacao"],
        },
    },
    {
        "name": "listar_fontes",
        "description": ("Inventario do indice: quantos documentos, trechos e "
                        "vetores, por tipo, e qual modelo de embedding esta em uso."),
        "inputSchema": {"type": "object", "properties": {
            "tipo": {"type": "string"},
            "limite": {"type": "integer", "default": 50}}},
    },
    {
        "name": "ler_documento",
        "description": ("Le um documento indexado por inteiro ou por faixa de "
                        "trechos. Use depois da busca, quando um trecho isolado "
                        "nao bastar."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "uri": {"type": "string", "description": "uri devolvida pela busca"},
                "de": {"type": "integer", "default": 0},
                "ate": {"type": "integer", "default": 20},
            },
            "required": ["uri"],
        },
    },
    {
        "name": "vizinhos_do_trecho",
        "description": ("Trechos semanticamente proximos de um trecho ja "
                        "conhecido. Serve para achar repeticao entre capitulos "
                        "e para reunir tudo o que o corpus diz sobre um ponto."),
        "inputSchema": {
            "type": "object",
            "properties": {"chunk_id": {"type": "integer"},
                           "k": {"type": "integer", "default": 5}},
            "required": ["chunk_id"],
        },
    },
    {
        "name": "indexar_arquivo",
        "description": ("Acrescenta um arquivo ao indice: pdf, docx, md, html ou "
                        "txt. Idempotente — reindexar o mesmo arquivo sem "
                        "mudanca nao custa nada."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "caminho": {"type": "string"},
                "tipo": {"type": "string", "default": "externo"},
            },
            "required": ["caminho"],
        },
    },
]


class Servidor:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path or base_config.DB_PATH)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.store = SqliteStore(self.conn)
        self.store.ensure_schema()
        self.protocolo = PROTOCOLO_PADRAO

    # ------------------------------------------------------------ protocolo
    def atender(self, pedido: dict) -> dict | None:
        metodo = pedido.get("method", "")
        pid = pedido.get("id")
        try:
            if metodo == "initialize":
                pedido_versao = (pedido.get("params") or {}).get("protocolVersion")
                if isinstance(pedido_versao, str) and pedido_versao:
                    self.protocolo = pedido_versao
                return _ok(pid, {
                    "protocolVersion": self.protocolo,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": NOME, "version": VERSAO},
                    "instructions": (
                        "Corpus do LAPE. Consulte buscar_corpus antes de afirmar o "
                        "que a literatura do grupo diz, e checar_afirmacao antes de "
                        "dar por boa uma frase de manuscrito."),
                })
            if metodo in ("notifications/initialized", "initialized"):
                return None
            if metodo == "ping":
                return _ok(pid, {})
            if metodo == "tools/list":
                return _ok(pid, {"tools": FERRAMENTAS})
            if metodo == "tools/call":
                params = pedido.get("params") or {}
                nome = params.get("name", "")
                args = params.get("arguments") or {}
                return _ok(pid, self._chamar(nome, args))
            if pid is None:
                return None
            return _erro(pid, -32601, f"metodo nao suportado: {metodo}")
        except Exception as exc:                      # pragma: no cover
            log.exception("falha ao atender %s", metodo)
            if pid is None:
                return None
            return _erro(pid, -32603, f"{type(exc).__name__}: {exc}")

    def _chamar(self, nome: str, args: dict) -> dict:
        acao: Callable[[dict], str] | None = {
            "buscar_corpus": self._buscar,
            "checar_afirmacao": self._checar,
            "listar_fontes": self._listar,
            "ler_documento": self._ler,
            "vizinhos_do_trecho": self._vizinhos,
            "indexar_arquivo": self._indexar,
        }.get(nome)
        if acao is None:
            return _texto(f"ferramenta desconhecida: {nome}", erro=True)
        try:
            return _texto(acao(args))
        except Exception as exc:
            log.warning("ferramenta %s falhou: %s", nome, exc)
            return _texto(f"{type(exc).__name__}: {exc}\n\n"
                          f"{traceback.format_exc(limit=3)}", erro=True)

    # ---------------------------------------------------------- ferramentas
    def _filtro(self, args: dict) -> Filtro | None:
        tipos = args.get("tipos")
        de, ate = args.get("ano_de"), args.get("ano_ate")
        if not tipos and de is None and ate is None:
            return None
        return Filtro(kinds=tipos or None,
                      anos=(de, ate) if (de is not None or ate is not None) else None)

    def _buscar(self, args: dict) -> str:
        consulta = (args.get("consulta") or "").strip()
        if not consulta:
            return "consulta vazia."
        k = max(1, min(int(args.get("k", config.TOP_K)), 30))
        r = buscar(self.store, consulta, k=k, filtro=self._filtro(args))
        if not r.hits:
            return (f"Nenhum trecho para {consulta!r}. "
                    "O indice pode estar vazio: veja listar_fontes.")
        linhas = [f"{len(r.hits)} trechos para {consulta!r} "
                  f"({r.ms} ms, {r.densa} densos, {r.lexica} lexicos)."]
        if r.aviso:
            linhas.append(f"AVISO: {r.aviso}")
        linhas.append("")
        for i, h in enumerate(r.hits, 1):
            linhas.append(
                f"[{i}] {h.citacao()}  (score {h.score:.4f}, via {h.origem}, "
                f"chunk_id {h.chunk_id})\n"
                f"     fonte: {h.title or h.uri}\n"
                f"     uri: {h.uri}\n{h.text}\n")
        return "\n".join(linhas)

    def _checar(self, args: dict) -> str:
        afirmacao = (args.get("afirmacao") or "").strip()
        if not afirmacao:
            return "afirmacao vazia."
        k = max(1, min(int(args.get("k", 6)), 20))
        r = buscar(self.store, afirmacao, k=k)
        if not r.hits:
            return (f"O corpus nao tem nenhum trecho relacionado a: {afirmacao!r}\n"
                    "Veredito: SEM COBERTURA. Nao afirme isto com base neste corpus.")
        denso = [h for h in r.hits if h.detalhe.get("score_densa") is not None]
        melhor = max((h.detalhe.get("score_densa", 0.0) for h in denso), default=0.0)
        if melhor >= 0.75:
            veredito = "COBERTURA FORTE: ha trecho diretamente sobre o ponto."
        elif melhor >= 0.5 or r.hits:
            veredito = ("COBERTURA PARCIAL: ha trechos proximos, mas confira se "
                        "cada elemento da afirmacao aparece de fato abaixo.")
        else:
            veredito = "COBERTURA FRACA: os trechos apenas tangenciam a afirmacao."
        corpo = "\n\n".join(
            f"[{i}] {h.citacao()} (chunk_id {h.chunk_id})\n{h.text}"
            for i, h in enumerate(r.hits, 1))
        return (f"Afirmacao: {afirmacao}\n\nVeredito: {veredito}\n\n"
                f"Trechos a conferir:\n\n{corpo}\n\n"
                "Leia cada trecho antes de dar a afirmacao por sustentada: "
                "proximidade semantica nao e prova.")

    def _listar(self, args: dict) -> str:
        s = self.store.stats()
        limite = max(1, min(int(args.get("limite", 50)), 500))
        tipo = args.get("tipo")
        linhas = [
            f"Indice em {self.db_path}",
            f"  {s['documentos']} documentos, {s['trechos']} trechos, "
            f"{s['vetores']} vetores, {s['caracteres']} caracteres",
            f"  backend: {s['backend']}",
        ]
        for m in s.get("modelos", []):
            linhas.append(f"  modelo: {m['model']} ({m['dim']} dimensoes, {m['n']} vetores)")
        for t in s.get("por_tipo", []):
            linhas.append(f"  tipo {t['kind']}: {t['n']} documentos, {t['trechos']} trechos")
        onde, args_sql = ("kind = ?", [tipo]) if tipo else ("1=1", [])
        linhas.append("\nDocumentos:")
        for d in self.conn.execute(
                f"SELECT uri, kind, title, year, n_chunks FROM rag_documents"
                f" WHERE {onde} ORDER BY updated_at DESC LIMIT ?",
                args_sql + [limite]):
            linhas.append(f"  [{d['kind']}] {d['title'] or d['uri']} "
                          f"({d['year'] or 's.d.'}, {d['n_chunks']} trechos)\n"
                          f"      {d['uri']}")
        return "\n".join(linhas)

    def _ler(self, args: dict) -> str:
        uri = (args.get("uri") or "").strip()
        de = max(0, int(args.get("de", 0)))
        ate = max(de, int(args.get("ate", de + 20)))
        doc = self.conn.execute(
            "SELECT id, title, authors, year, kind, n_chunks FROM rag_documents"
            " WHERE uri = ?", (uri,)).fetchone()
        if doc is None:
            return f"documento nao indexado: {uri}"
        linhas = self.conn.execute(
            "SELECT ordinal, section, text FROM rag_chunks"
            " WHERE doc_id = ? AND ordinal BETWEEN ? AND ? ORDER BY ordinal",
            (doc["id"], de, ate)).fetchall()
        cabeca = (f"{doc['title'] or uri}\n{doc['authors'] or ''} "
                  f"({doc['year'] or 's.d.'}) — {doc['kind']}, "
                  f"{doc['n_chunks']} trechos no total\n")
        corpo = "\n\n".join(
            f"— trecho {l['ordinal']}"
            + (f" ({l['section']})" if l["section"] else "") + f" —\n{l['text']}"
            for l in linhas)
        return cabeca + "\n" + corpo

    def _vizinhos(self, args: dict) -> str:
        chunk_id = int(args.get("chunk_id", 0))
        k = max(1, min(int(args.get("k", 5)), 20))
        achados = vizinhos(self.store, chunk_id, k)
        if not achados:
            return f"nenhum vizinho para o trecho {chunk_id}."
        return "\n\n".join(
            f"[{i}] {h.citacao()} (score {h.score:.4f}, chunk_id {h.chunk_id})\n{h.text}"
            for i, h in enumerate(achados, 1))

    def _indexar(self, args: dict) -> str:
        caminho = Path(args.get("caminho", "")).expanduser()
        if not caminho.exists():
            return f"arquivo inexistente: {caminho}"
        try:
            doc = load(caminho, kind=args.get("tipo", "externo"))
        except ExtractionError as exc:
            return str(exc)
        rel = indexar_documentos(self.store, [doc], verbose=False)
        return (f"{rel.resumo()}\n" + ("\n".join(rel.erros) if rel.erros else ""))

    # ------------------------------------------------------------- laco
    def servir(self, entrada=None, saida=None) -> int:
        entrada = entrada or sys.stdin
        saida = saida or sys.stdout
        for linha in entrada:
            linha = linha.strip()
            if not linha:
                continue
            try:
                pedido = json.loads(linha)
            except json.JSONDecodeError as exc:
                _escrever(saida, _erro(None, -32700, f"JSON invalido: {exc}"))
                continue
            for p in (pedido if isinstance(pedido, list) else [pedido]):
                resposta = self.atender(p)
                if resposta is not None:
                    _escrever(saida, resposta)
        return 0


def _ok(pid, resultado: dict) -> dict:
    return {"jsonrpc": "2.0", "id": pid, "result": resultado}


def _erro(pid, codigo: int, mensagem: str) -> dict:
    return {"jsonrpc": "2.0", "id": pid, "error": {"code": codigo, "message": mensagem}}


def _texto(conteudo: str, erro: bool = False) -> dict:
    return {"content": [{"type": "text", "text": conteudo}], "isError": erro}


def _escrever(saida, obj: dict) -> None:
    saida.write(json.dumps(obj, ensure_ascii=False) + "\n")
    saida.flush()


def main(db_path: Path | str | None = None) -> int:
    # O log vai para stderr: stdout pertence ao protocolo.
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr,
                        format="%(levelname)s %(name)s: %(message)s")
    return Servidor(db_path).servir()


if __name__ == "__main__":                            # pragma: no cover
    sys.exit(main())
