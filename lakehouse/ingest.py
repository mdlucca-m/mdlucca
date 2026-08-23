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
    # tabela bronze          arquivo bruto            grão / chave
    "brums_raw":     "humor_anon.csv",            # atleta-momento (A-code) · BRUMS + momento + HIIT
    "wellbeing_raw": "humor_epworth_pss_anon.csv", # atleta-dia (A-code) · Epworth + PSS
    "hiit_raw":      "hiit_fcpse_anon.csv",       # atleta-sessão×fase (A-code) · FC/PSE
    "rsa_raw":       "rsa_anon.csv",              # atleta (A-code) · sprints repetidos (Bosco)
    "mdc_raw":       "mdc_class_anon.csv",        # atleta (A-code) · mudança confiável (MDC)
    "physical_raw":  "phys_anon.csv",             # atleta (P-code!) · bateria física/T-CAR + grupo
    "brums_items_raw": "brums_itens_anon.csv",    # resposta (sem ID) · 24 itens BRUMS (psicometria)
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
