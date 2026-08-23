# -*- coding: utf-8 -*-
"""Ingestão IoT / tempo real — endpoint HTTP que aterrissa eventos na BRONZE.

Um questionário respondido no celular ou um sensor (FC/PSE) faz POST aqui; o
evento é gravado na mesma tabela Delta append-only da carga em lote — sem
esquema separado para streaming (arquitetura de lakehouse: uma fonte da verdade).
Rode as transformações (silver/gold) em micro-lotes agendados.

Requer:  pip install fastapi uvicorn
Rodar:   uvicorn ingestion_api:app --reload
Testar:  curl -X POST localhost:8000/ingest/brums -H 'content-type: application/json' \\
             -d '{"ID":"A01","data":"2024-04-28","dia":8,"seq":0,"momento":"pre",
                  "HIIT":0,"Tensao":3,"Depressao":0,"Raiva":1,"Vigor":10,"Fadiga":2,
                  "Confusao":0,"TMD":-4,"FadFisica":2,"FadMental":1}'
"""
from __future__ import annotations
import uuid
import pandas as pd
from fastapi import FastAPI
import lh

app = FastAPI(title="Lakehouse — ingestão de monitoramento de atletas")

def _land_event(table: str, payload: dict, source: str) -> dict:
    df = pd.DataFrame([payload])
    df["_source"] = source
    df["_load_id"] = "iot-" + uuid.uuid4().hex[:10]
    df["_ingested_at"] = lh.now_iso()
    df["_row_hash"] = lh.row_hash(df)
    mode = "append" if lh.exists("bronze", table) else "overwrite"
    lh.write_delta("bronze", table, df, mode=mode)
    return {"status": "ok", "table": f"bronze.{table}", "load_id": df["_load_id"].iloc[0]}

@app.post("/ingest/brums")
def ingest_brums(payload: dict):
    """Recebe uma resposta BRUMS (pré ou pós) e grava na bronze."""
    return _land_event("brums_raw", payload, source="iot/brums")

@app.post("/ingest/hiit")
def ingest_hiit(payload: dict):
    """Recebe um registro de carga interna do HIIT (FC/PSE)."""
    return _land_event("hiit_raw", payload, source="iot/hiit")

@app.get("/health")
def health():
    return {"ok": True}
