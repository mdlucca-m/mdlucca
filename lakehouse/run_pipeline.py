# -*- coding: utf-8 -*-
"""Orquestração mínima do lakehouse: bronze -> silver -> gold -> ML.

Para produção, troque este runner por Dagster (assets + agendamento + lineage)
ou dbt-duckdb (silver/gold como modelos SQL versionados). Aqui, um runner linear
mantém tudo executável com um só comando e zero dependências extras.
"""
import time
import ingest, transform, ml_risk, lh

def main():
    t0 = time.time()
    print("== 1/4 BRONZE (ingestão bruta) ==");   ingest.run()
    print("== 2/4 SILVER (conformar/dedup) ==");   transform.build_silver()
    print("== 3/4 GOLD (analítico/features) =="); transform.build_gold()
    print("== 4/4 ML (risco do dia seguinte) =="); ml_risk.run()
    print(f"\nlakehouse construído em {time.time()-t0:.1f}s. Tabelas Delta em warehouse/.")
    # amostra de governança: histórico (time-travel) da bronze
    try:
        h = lh.history("bronze", "brums_raw")
        print(f"governança: bronze.brums_raw tem {len(h)} versão(ões) no log Delta (time-travel disponível).")
    except Exception:
        pass

if __name__ == "__main__":
    main()
