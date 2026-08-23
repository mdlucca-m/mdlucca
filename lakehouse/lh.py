# -*- coding: utf-8 -*-
"""Utilitários do lakehouse local: caminhos, IO Delta e execução SQL no DuckDB.

Padrão de arquitetura:
  - Delta Lake (delta-rs, sem Spark/JVM) = formato de tabela ACID com time-travel.
  - DuckDB = motor SQL de leitura/transformação (in-process, zero-config).
  - Camadas medallion: bronze (bruto) -> silver (conformado) -> gold (analítico).
Cada tabela é uma pasta Delta em warehouse/<camada>/<tabela>.
"""
from __future__ import annotations
import os, hashlib, datetime as _dt
import pandas as pd
import duckdb
from deltalake import write_deltalake, DeltaTable

ROOT = os.path.dirname(os.path.abspath(__file__))
WAREHOUSE = os.path.join(ROOT, "warehouse")
SOURCES = os.path.abspath(os.path.join(ROOT, "..", "scripts", "analise"))  # fontes brutas (anonimizadas)

def tpath(layer: str, table: str) -> str:
    return os.path.join(WAREHOUSE, layer, table)

def now_iso() -> str:
    # timestamp de ingestão (passado explicitamente para manter reprodutibilidade)
    return _dt.datetime.now().replace(microsecond=0).isoformat()

def row_hash(df: pd.DataFrame) -> pd.Series:
    """Hash estável por linha — usado para deduplicação idempotente na prata."""
    from pandas.util import hash_pandas_object
    cols = [c for c in df.columns if not c.startswith("_")]
    return hash_pandas_object(df[cols], index=False).astype("uint64").map(lambda x: f"{x:016x}")

def write_delta(layer: str, table: str, df: pd.DataFrame, mode: str = "overwrite"):
    """Grava um DataFrame como tabela Delta (cria versão nova no log de transações)."""
    path = tpath(layer, table)
    os.makedirs(path, exist_ok=True)
    write_deltalake(path, df, mode=mode)
    return path

def read_delta(layer: str, table: str, version: int | None = None) -> pd.DataFrame:
    """Lê uma tabela Delta; version=N faz time-travel (governança/histórico)."""
    dt = DeltaTable(tpath(layer, table))
    if version is not None:
        dt.load_as_version(version)
    return dt.to_pandas()

def history(layer: str, table: str) -> pd.DataFrame:
    return pd.DataFrame(DeltaTable(tpath(layer, table)).history())

def sql(query: str, **frames) -> pd.DataFrame:
    """Roda SQL no DuckDB sobre DataFrames registrados por nome."""
    con = duckdb.connect()
    try:
        for name, df in frames.items():
            con.register(name, df)
        return con.execute(query).fetch_df()
    finally:
        con.close()

def exists(layer: str, table: str) -> bool:
    return os.path.exists(os.path.join(tpath(layer, table), "_delta_log"))
