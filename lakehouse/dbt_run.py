# -*- coding: utf-8 -*-
"""SILVER + GOLD via dbt-duckdb (substitui o transform.py em Python).

Roda `dbt build` (modelos SQL declarativos + testes de qualidade + lineage/docs)
lendo a bronze Delta pelo plugin `delta`; materializa silver/gold como tabelas no
DuckDB e as EXPORTA para Delta, mantendo a interface Delta usada pelas análises
(analytics.py), pelo ML, pela auditoria e pela ponte com o painel.
"""
from __future__ import annotations
import os, subprocess
import duckdb
import lh

DBT_DIR = os.path.join(lh.ROOT, "dbt")
DUCKDB = os.path.join(lh.WAREHOUSE, "lakehouse.duckdb")
SILVER = ["mood", "wellbeing", "hiit", "rsa", "mdc", "physical", "brums_items"]
GOLD = ["athlete_day", "daily_group", "acute_prepos", "risk_features",
        "athlete_day_unified", "athlete_profile"]

def run():
    os.makedirs(lh.WAREHOUSE, exist_ok=True)
    env = dict(os.environ, LH_BRONZE=os.path.join(lh.WAREHOUSE, "bronze"), LH_DUCKDB=DUCKDB)
    r = subprocess.run(["dbt", "build", "--profiles-dir", ".", "--no-partial-parse"],
                       cwd=DBT_DIR, env=env, capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if any(k in line for k in ("PASS=", "Completed", "ERROR")):
            print("[dbt]", line.split("]", 1)[-1].strip() if "]" in line else line.strip())
    if r.returncode != 0:
        print(r.stdout[-2500:]); raise SystemExit("dbt build falhou")
    # exporta as tabelas dbt (DuckDB) para Delta — mantém a interface a jusante
    con = duckdb.connect(DUCKDB)
    try:
        for layer, tables in [("silver", SILVER), ("gold", GOLD)]:
            for t in tables:
                df = con.execute(f"select * from main_{layer}.{t}").fetch_df()
                lh.write_delta(layer, t, df, mode="overwrite")
    finally:
        con.close()
    print(f"[dbt→delta] {len(SILVER)} silver + {len(GOLD)} gold exportados para Delta")

if __name__ == "__main__":
    run()
