#!/usr/bin/env python3
"""Gera sql/schema.sql a partir das definições em scripts/busca/deposito.py,
que são a fonte única do esquema. Rode após alterar o DDL:

    python3 scripts/gerar_schema.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from busca import deposito  # noqa: E402

CABECALHO = (
    "-- Gerado por scripts/gerar_schema.py a partir de scripts/busca/deposito.py.\n"
    "-- Não editar à mão: altere o DDL no módulo e regenere.\n"
)


def conteudo() -> str:
    partes = [deposito.SCHEMA_ARTIGO, deposito.SCHEMA_PROVENIENCIA, deposito.INDICES]
    corpo = "\n".join(p.strip() for p in partes)
    return CABECALHO + "\n" + corpo + "\n"


if __name__ == "__main__":
    destino = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo())
    print(f"escrito: {destino} ({len(conteudo().splitlines())} linhas)")
