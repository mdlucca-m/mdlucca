# Pipeline BRUMS × HIIT — sumário de execução

- **ingest** — OK — {"rows": 456, "athletes": 27, "pairs": 135}
- **descriptives** — OK — {"vars": 9}
- **reliability** — OK — {"subs": 6}
- **correlations** — OK — {"ok": true}
- **day_effect** — OK — {"iceberg_D1": 71.4, "iceberg_D7": 32.6}
- **acute** — OK — {"fadfis_dz": 0.76}
- **hiit** — OK — {"dPTH": 2.47}
- **multivariate** — OK — {"hotelling6_F": 2.52, "hotelling6_p": 0.054}
- **variance** — OK — {"ok": true}
- **complementary** — OK — {"cluster_sizes": {"2": 6, "0": 20, "1": 1}, "weekly_fadfis_dz": 1.74}
- **charts** — OK — {"charts": ["trajetoria", "efeito_piso", "resposta_aguda", "iceberg", "mudanca_semanal"]}
- **export_excel** — OK — {"arquivo": "BRUMS_HIIT_resultados.xlsx", "abas": 13}
- **export_pdf** — OK — {"arquivo": "BRUMS_HIIT_relatorio.pdf"}
- **publish** — OK — {"arquivo": "relatorio.html"}

## Tabelas geradas
- tables/00_base_limpa.csv
- tables/01_descritivas.csv
- tables/02_confiabilidade.csv
- tables/03_correlacoes.csv
- tables/04_medias_diarias.csv
- tables/04b_iceberg.csv
- tables/05_resposta_aguda.csv
- tables/06_hiit_vs_sem.csv
- tables/07_multivariada.csv
- tables/08_variancia.csv
- tables/09_mudanca_semanal.csv
- tables/10_tipologia.csv
- tables/11_rede.csv

## Gráficos gerados
- charts/efeito_piso.png
- charts/iceberg.png
- charts/mudanca_semanal.png
- charts/resposta_aguda.png
- charts/trajetoria.png