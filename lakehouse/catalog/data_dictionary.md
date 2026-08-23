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
| `mood` | atleta-momento | (ID, dia, seq) | tipado; `is_pre`/`is_pos`; `day_type` (Baseline/HIIT/Jogo/Forca) |
| `wellbeing` | atleta-dia | (ID, dia) | Epworth, PSS médios do dia |
| `hiit` | sessão×fase | (ID, sessao, fase) | carga interna |

Deduplicação idempotente: em `(chave)` mantém-se a carga mais recente
(`_ingested_at` máximo). Recarregar a mesma fonte **não** duplica linhas.

### GOLD (consumo: análise · painel · ML)
| Tabela | Grão | Conteúdo |
|---|---|---|
| `athlete_day` | atleta-dia | médias de todos os momentos (unidade de análise) |
| `daily_group` | dia | trajetória diária do grupo (bate com o painel) |
| `acute_prepos` | atleta-dia | efeito agudo pré→pós (Δ vigor/fadiga/PTH) |
| `risk_features` | atleta-dia | marcadores de hoje + `risco_amanha` (rótulo p/ ML) |

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
