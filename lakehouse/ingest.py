# -*- coding: utf-8 -*-
"""BRONZE — ingestão bruta (append-only) das fontes para tabelas Delta.

Cada fonte é aterrissada COMO ESTÁ, acrescentando apenas metadados de ingestão:
  _source      origem do dado
  _load_id     identificador do lote de carga
  _ingested_at carimbo de ingestão
  _row_hash    hash da linha (idempotência a jusante)
Nenhuma limpeza aqui — a bronze é o registro fiel do que chegou (auditoria/replay).
A mesma função serve para carga em lote (CSV) e para eventos de IoT (ver ingestion_api.py).
"""
from __future__ import annotations
import os, uuid
import pandas as pd
import lh

SOURCES = {
    # tabela bronze        arquivo bruto (anonimizado A01–A27)
    "brums_raw":  "humor_anon.csv",            # BRUMS + momento (pré/pós) + flag HIIT do dia
    "hiit_raw":   "hiit_fcpse_anon.csv",       # carga interna do HIIT (FC/PSE por sessão×fase)
    "wellbeing_raw": "humor_epworth_pss_anon.csv",  # sonolência (Epworth) + estresse (PSS)
}

def land(table: str, filename: str, load_id: str) -> int:
    df = pd.read_csv(os.path.join(lh.SOURCES, filename))
    df["_source"] = filename
    df["_load_id"] = load_id
    df["_ingested_at"] = lh.now_iso()
    df["_row_hash"] = lh.row_hash(df)
    # append-only: cada carga é uma nova versão Delta (histórico preservado)
    mode = "append" if lh.exists("bronze", table) else "overwrite"
    lh.write_delta("bronze", table, df, mode=mode)
    return len(df)

def run() -> None:
    load_id = uuid.uuid4().hex[:12]
    print(f"[bronze] lote de carga _load_id={load_id}")
    for table, filename in SOURCES.items():
        n = land(table, filename, load_id)
        print(f"[bronze] {table:14s} <- {filename:28s} {n} linhas")

if __name__ == "__main__":
    run()
