"""Camada de recuperacao semantica do LAPE.

Quatro pecas, cada uma substituivel sem tocar nas outras:

    chunk.py   extrai texto de pdf, docx, html, markdown e texto puro
    embed.py   transforma texto em vetor (Voyage, OpenAI, local ou hash)
    store.py   guarda e busca vetores (SQLite hoje, pgvector quando crescer)
    search.py  funde busca densa e BM25 num unico ranking

Sobre elas ficam os agentes (agents/) e o servidor MCP (mcp_server.py).
"""
from __future__ import annotations

__all__ = ["config", "chunk", "embed", "store", "index", "search"]
