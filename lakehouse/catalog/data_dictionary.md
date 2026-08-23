# Dicionário de dados & governança

Coorte: **27 atletas** de handebol masculino de elite (A01–A27), microciclo
**21–27/04/2024**, **2 respostas/dia** (pré = primeira da manhã, pós = última).
Todos os dados já são **anonimizados**: nenhum nome real entra no lakehouse.

## Fronteira de anonimização
- Nomes reais → códigos A01–A27 são resolvidos por uma **chave confidencial**
  que **não** faz parte do repositório. Só derivados anonimizados são ingeridos.
- Regra: identificadores diretos jamais passam da fonte para a bronze.

## Camadas

### BRONZE (bruto, append-only, auditável)
| Tabela | Grão | Origem | Observações |
|---|---|---|---|
| `brums_raw` | resposta (atleta×dia×seq×momento) | `humor_anon.csv` | BRUMS + FadFísica/Mental + flag HIIT |
| `hiit_raw` | sessão×fase | `hiit_fcpse_anon.csv` | FC pré/pós, ΔFC, PSE |
| `wellbeing_raw` | resposta | `humor_epworth_pss_anon.csv` | Epworth (sonolência), PSS (estresse) |

Metadados em toda linha bronze: `_source`, `_load_id`, `_ingested_at`, `_row_hash`.

### SILVER (conformado, deduplicado)
| Tabela | Grão | Chave | Notas |
|---|---|---|---|
| `mood` | atleta-momento | (ID, dia, seq) | tipado; `is_pre`/`is_pos`; `day_type` |
| `wellbeing` | atleta-dia | (ID, dia) | Epworth, PSS médios do dia |
| `hiit` | sessão×fase | (ID, sessao, fase) | carga interna (S1→D2, S2→D4, S3→D7) |
| `rsa` | atleta (A-code) | (ID) | sprints repetidos (Bosco: BkMel/BkSoma/BkF) |
| `mdc` | atleta (A-code) | (ID) | mudança confiável (classe vigor/fadiga) |
| `physical` | atleta (**P-code**) | (id) | bateria física/T-CAR + grupo — esquema separado |
| `brums_items` | resposta (sem ID) | `_row_hash` | 24 itens do BRUMS (psicometria) |

Deduplicação idempotente: em `(chave)` mantém-se a carga mais recente
(`_ingested_at` máximo). Recarregar a mesma fonte **não** duplica linhas.

### GOLD — integração (consumo: painel · ML)
| Tabela | Grão | Conteúdo |
|---|---|---|
| `athlete_day` | atleta-dia | médias de todos os momentos (unidade de análise) |
| `daily_group` | dia | trajetória diária do grupo (bate com o painel) |
| `acute_prepos` | atleta-dia | efeito agudo pré→pós (Δ vigor/fadiga/PTH) |
| `athlete_day_unified` | atleta-dia | **OBT**: humor + Epworth/PSS + carga HIIT do dia |
| `athlete_profile` | atleta | humor semanal + RSA + classificação MDC |
| `risk_features` | atleta-dia | marcadores de hoje + `risco_amanha` (rótulo p/ ML) |

### GOLD — análises (reproduzem o painel, versionadas)
| Tabela | Conteúdo |
|---|---|
| `an_d17` | D1→D7 por dimensão: d1/d7 (todos por dia), Δ%, **dz** (Wilcoxon pareado), p |
| `an_friedman` | Friedman χ²/p/**W** (7 dias, casos completos n=19) |
| `an_spearman` | correlações de Spearman significativas entre dimensões |
| `an_profiles` / `an_profiles_byday` | perfis Terry: centroide-T, prevalência; dominante por dia |
| `an_snr` | decomposição de variância: tendência + HIIT + ruído + **SNR** |
| `an_negatives_daytype` | negativas em dias de HIIT × jogo (meio de semana, pareado) |
| `an_wellbeing` / `an_wellbeing_corr` | Epworth/PSS D1→D7 + correlações com o humor |

> Reconciliação automática (`export_dashboard.py`): **DIM · dz · SNR** do gold
> conferem com o painel a cada execução (21 checagens; hoje todas OK).

## Definições-chave
- **PTH** — Perturbação Total do Humor (TMD): soma das negativas − vigor.
- **day_type** — 1 Baseline · 2/4/7 HIIT · 3/5 Jogo (amistoso) · 6 Força.
- **risco_amanha** — 1 se a PTH do dia seguinte do atleta ≥ tercil superior
  (P66) da distribuição atleta-dia; senão 0 (nulo no último dia de cada atleta).

## Linhagem & histórico
- **Time-travel**: cada carga gera uma versão no log Delta
  (`lh.read_delta(camada, tabela, version=N)`; `lh.history(...)`).
- **Reprodutibilidade**: `run_pipeline.py` reconstrói bronze→silver→gold→ML de
  forma determinística a partir das fontes anonimizadas.
