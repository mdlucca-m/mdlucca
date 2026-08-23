# -*- coding: utf-8 -*-
"""Orquestração mínima do lakehouse: bronze -> silver -> gold -> ML.

Para produção, troque este runner por Dagster (assets + agendamento + lineage)
ou dbt-duckdb (silver/gold como modelos SQL versionados). Aqui, um runner linear
mantém tudo executável com um só comando e zero dependências extras.
"""
import time
import ingest, transform, analytics, ml_risk, build_dashboard_data, export_dashboard, lh

def main():
    t0 = time.time()
    print("== 1/7 BRONZE (ingestão bruta) ==");   ingest.run()
    print("== 2/7 SILVER (conformar/dedup) ==");   transform.build_silver()
    print("== 3/7 GOLD (integração/features) =="); transform.build_gold()
    print("== 4/7 GOLD·ANÁLISES (todas as análises) =="); analytics.run()
    print("== 5/7 ML (risco do dia seguinte) =="); ml_risk.run()
    print("== 6/7 PAINEL ← GOLD (regenera constantes do painel) =="); build_dashboard_data.run()
    print("== 7/7 RECONCILIAÇÃO (painel × gold) ==")
    consistent = export_dashboard.run()
    print(f"\nlakehouse construído em {time.time()-t0:.1f}s. Tabelas Delta em warehouse/.")
    if not consistent:
        print("ATENÇÃO: painel divergiu do lakehouse — regenerar os dados do painel.")
    # amostra de governança: histórico (time-travel) da bronze
    try:
        h = lh.history("bronze", "brums_raw")
        print(f"governança: bronze.brums_raw tem {len(h)} versão(ões) no log Delta (time-travel disponível).")
    except Exception:
        pass

if __name__ == "__main__":
    main()
