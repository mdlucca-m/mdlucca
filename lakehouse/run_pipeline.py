# -*- coding: utf-8 -*-
"""Orquestração mínima do lakehouse: bronze -> silver -> gold -> ML.

Para produção, troque este runner por Dagster (assets + agendamento + lineage)
ou dbt-duckdb (silver/gold como modelos SQL versionados). Aqui, um runner linear
mantém tudo executável com um só comando e zero dependências extras.
"""
import time
import ingest, dbt_run, analytics, analytics_physical, analytics_panel, analytics_tri, analytics_twopaths, analytics_norm, analytics_tri_confirm, analytics_factorial, analytics_dynamics, analytics_load, ml_risk, build_dashboard_data, export_dashboard, lh

def main():
    t0 = time.time()
    print("== 1/6 BRONZE (ingestão bruta) ==");   ingest.run()
    print("== 2/6 SILVER+GOLD via dbt-duckdb (SQL + testes) =="); dbt_run.run()
    print("== 3/6 GOLD·ANÁLISES (todas as análises) =="); analytics.run(); analytics_physical.run(); analytics_panel.run(); analytics_tri.run(); analytics_twopaths.run(); analytics_norm.run(); analytics_tri_confirm.run(); analytics_factorial.run(); analytics_dynamics.run(); analytics_load.run()
    print("== 4/6 ML (risco do dia seguinte) =="); ml_risk.run()
    print("== 5/6 PAINEL ← GOLD (regenera constantes do painel) =="); build_dashboard_data.run()
    print("== 6/6 RECONCILIAÇÃO (painel × gold) ==")
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
