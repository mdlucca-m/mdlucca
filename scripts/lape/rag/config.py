"""Configuracao da camada de recuperacao semantica.

Tudo aqui sai de variavel de ambiente, com padroes que funcionam sem
nenhuma chave: sem credencial, o sistema cai no embedder local e, na
ausencia dele, num embedder deterministico que ainda permite rodar os
testes e a busca lexica.
"""
from __future__ import annotations

import os
from pathlib import Path

from .. import config as base

ROOT = base.ROOT
SQL_RAG = base.SQL_DIR / "rag.sql"

# ---------------------------------------------------------------- embeddings
# voyage | openai | local | hash
EMBED_BACKEND = os.environ.get("LAPE_EMBED_BACKEND", "auto").strip().lower()
EMBED_MODEL = os.environ.get("LAPE_EMBED_MODEL", "").strip()
EMBED_BATCH = int(os.environ.get("LAPE_EMBED_BATCH", "64"))
EMBED_TIMEOUT = float(os.environ.get("LAPE_EMBED_TIMEOUT", "60"))

VOYAGE_API_KEY = os.environ.get("VOYAGE_API_KEY", "").strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

# Modelos padrao de cada backend. voyage-3.5 e multilingue e barato; o
# modelo local escolhido cobre portugues e ingles no mesmo espaco vetorial.
DEFAULT_MODELS = {
    "voyage": "voyage-3.5",
    "openai": "text-embedding-3-small",
    "local": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "hash": "hash-1024",
}

# ------------------------------------------------------------------- store
# sqlite | pgvector
STORE_BACKEND = os.environ.get("LAPE_VECTOR_STORE", "sqlite").strip().lower()
PG_DSN = os.environ.get("LAPE_PG_DSN", "").strip()
PG_TABLE = os.environ.get("LAPE_PG_TABLE", "rag_vectors").strip()

# ---------------------------------------------------------------- chunking
CHUNK_CHARS = int(os.environ.get("LAPE_CHUNK_CHARS", "1400"))
CHUNK_OVERLAP = int(os.environ.get("LAPE_CHUNK_OVERLAP", "220"))
CHUNK_MIN = int(os.environ.get("LAPE_CHUNK_MIN", "120"))

# ------------------------------------------------------------------ busca
TOP_K = int(os.environ.get("LAPE_RAG_TOP_K", "8"))
CANDIDATES = int(os.environ.get("LAPE_RAG_CANDIDATES", "60"))
RRF_K = int(os.environ.get("LAPE_RAG_RRF_K", "60"))
# Peso da metade densa na fusao. 1.0 usa so o vetor; 0.0 so o BM25.
DENSE_WEIGHT = float(os.environ.get("LAPE_RAG_DENSE_WEIGHT", "0.6"))

# ------------------------------------------------------------------ agentes
LLM_MODEL = os.environ.get("LAPE_LLM_MODEL", "claude-opus-5").strip()
LLM_EFFORT = os.environ.get("LAPE_LLM_EFFORT", "high").strip()
LLM_MAX_TOKENS = int(os.environ.get("LAPE_LLM_MAX_TOKENS", "16000"))

# Pastas varridas pelo indexador quando nenhuma e informada.
CORPUS_DIRS = [
    Path(p).expanduser()
    for p in os.environ.get("LAPE_CORPUS_DIRS", str(base.DATA_DIR / "corpus")).split(os.pathsep)
    if p.strip()
]

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".markdown", ".html", ".htm"}
