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
- **carga** — OK — {"fases": 5, "sessoes": 4, "r_FC_PSE": 0.73, "FC_pre_pos": "118.2->174.8", "atletas_cruzados": 25}
- **charts** — OK — {"charts": ["trajetoria", "efeito_piso", "resposta_aguda", "iceberg", "mudanca_semanal", "carga_fc_por_fase", "carga_pse_fc_sessao", "carga_x_humor"]}
- **export_excel** — OK — {"arquivo": "BRUMS_HIIT_resultados.xlsx", "abas": 17}
- **export_pdf** — OK — {"arquivo": "BRUMS_HIIT_relatorio.pdf"}
- **publish** — OK — {"arquivo": "relatorio.html"}
- **app** — OK — {"status": "ok", "app": "Sistema_Analista_BRUMS_HIIT.html", "appdata": "appdata.json", "bytes": 186239, "log": ["appdata.json: 456 obs, 27 atletas, 135 pares", "carga: n_ath=26 matched=25", "HTML: /home/user/mdlucca/HANDEBOL/pipeline/pipe/Sistema_Analista_BRUMS_HIIT.html"]}

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
- tables/12_carga_por_fase.csv
- tables/13_carga_por_sessao.csv
- tables/14_fc_pre_pos_fase.csv
- tables/15_carga_x_humor.csv

## Gráficos gerados
- charts/carga_fc_por_fase.png
- charts/carga_pse_fc_sessao.png
- charts/carga_x_humor.png
- charts/efeito_piso.png
- charts/iceberg.png
- charts/mudanca_semanal.png
- charts/resposta_aguda.png
- charts/trajetoria.png