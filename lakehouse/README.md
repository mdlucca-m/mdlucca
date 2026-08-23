# Lakehouse — Monitoramento de Atletas (local, gratuito, open-source)

Espinha dorsal de dados do sistema de monitoramento do humor/carga (BRUMS, HIIT,
sono/estresse, T-CAR, IoT). É um **lakehouse de verdade** — camadas medallion,
formato de tabela ACID com *time-travel*, transformações declarativas e trilha de
governança — mas **dimensionado para rodar na sua máquina, sem nuvem, sem Spark e
sem custo**.

> Validação: a camada **gold** reproduz exatamente os números do painel
> (vigor D1 7,6 → D7 4,5 · fadiga 4,0 → 7,5 · PTH 2,5 → 8,3), e o modelo de risco
> dá **AUC ≈ 0,82** (GroupKFold por atleta) — o mesmo achado do alerta precoce.

## Stack (por que cada peça)

| Papel | Ferramenta | Por quê |
|---|---|---|
| Formato de tabela | **Delta Lake** (`deltalake`/delta-rs) | ACID + *time-travel* (versão/auditoria/replay) sem JVM/Spark |
| Armazenamento | **Parquet** (dentro do Delta) | colunar, comprimido, aberto |
| Transformação silver/gold | **dbt-duckdb** | modelos SQL declarativos + testes de qualidade + lineage + docs (lê a bronze Delta pelo plugin `delta`) |
| Motor SQL | **DuckDB** | consultas in-process, zero-config, muito rápido |
| ML | **scikit-learn** | classificador de risco (já usado no estudo) |
| Ingestão IoT | **FastAPI** (opcional) | um endpoint HTTP grava eventos na mesma bronze |
| Orquestração | runner Python (→ **Dagster**/**dbt** ao crescer) | um comando hoje; assets/lineage depois |

## Arquitetura medallion

```
7 fontes anonimizadas (CSV/IoT)
   │  ingest.py  (append-only + metadados de carga)
   ▼
BRONZE  bruto, fiel ao que chegou
        brums_raw · wellbeing_raw · hiit_raw · rsa_raw · mdc_raw · physical_raw · brums_items_raw
   │  dbt-duckdb  (models/silver/*.sql · conformar · tipar · DEDUPLICAR · pré/pós · TESTES)
   ▼
SILVER  limpo e conformado
        mood · wellbeing · hiit · rsa · mdc · physical(P-code) · brums_items
   │  dbt-duckdb (models/gold/*.sql)  +  analytics.run()   (integrar · agregar · analisar)
   ▼
GOLD    pronto p/ análise, painel, ML
        integração:  athlete_day · daily_group · acute_prepos · risk_features
                     athlete_day_unified (OBT: humor+sono+estresse+HIIT) · athlete_profile
        análises:    an_d17 · an_friedman · an_spearman · an_profiles(+byday)
                     an_snr · an_negatives_daytype · an_wellbeing(+corr)
   │
   ├──►  painel do humor / SQL (DuckDB)   [reconciliado: DIM · dz · SNR]
   └──►  ml_risk.py  →  ml/risk_model.pkl  (+ metrics.json)
```

### Bases unificadas
Tudo que compartilha o código **A01–A27** é integrado por atleta-dia/atleta:
humor (BRUMS), sono/estresse (Epworth/PSS), carga do HIIT (FC/PSE), RSA e a
classificação MDC. A **bateria física** (`phys_anon`) usa um esquema de
anonimização **separado (P01–P24, com grupo controle/experimental)** e por isso
entra como tabela própria — sem junção fabricada com os A-codes. Os **itens do
BRUMS** (sem ID) ficam à parte para psicometria. Assim a unificação é honesta:
junta o que é ligável, isola o que não é.

- **Bronze** — cada carga entra como está, com `_source / _load_id / _ingested_at /
  _row_hash`. Nada é limpo aqui: é o registro auditável (permite *replay*).
- **Silver** — uma linha por atleta-momento, tipada e **deduplicada** por
  `(ID, dia, seq)` (idempotente: recarregar não duplica). Aqui vale a regra do
  estudo: **pré** = primeira resposta do dia, **pós** = a última.
- **Gold** — tabelas de consumo: médias atleta-dia, trajetória diária do grupo,
  efeito agudo pré→pós e a tabela de *features* de risco (marcadores de hoje +
  rótulo do dia seguinte).

## Como os seus 4 objetivos são atendidos

1. **Análises & painéis** — `gold.*` é SQL puro no DuckDB; alimenta o painel e
   qualquer relatório reprodutível (a `daily_group` já bate com o painel).
2. **Ingestão IoT / tempo real** — `ingestion_api.py` recebe respostas/sensores
   por HTTP e grava na **mesma** bronze Delta (lote e streaming, uma fonte só).
3. **Governança & histórico** — Delta guarda **todas as versões** (time-travel:
   `lh.read_delta('bronze','brums_raw', version=0)`); a fronteira de anonimização
   fica na bronze→silver (só códigos A01–A27 seguem adiante); `catalog/` documenta
   cada tabela.
4. **ML & predição** — `ml_risk.py` treina sobre `gold.risk_features` com
   validação **por atleta** (sem vazamento) e salva modelo + métricas.

## Rodar

```bash
pip install -r requirements.txt
python run_pipeline.py          # bronze → (dbt) silver/gold → análises → ML → painel←gold → reconciliação
```

### dbt-duckdb (silver + gold)

Os modelos SQL vivem em `dbt/models/{silver,gold}`; a bronze Delta entra como
*source* pelo plugin `delta` (sem extensão do DuckDB). `dbt_run.py` roda
`dbt build` (modelos + testes) e exporta o resultado para Delta, mantendo a
interface usada pelas análises/ML/painel. Para rodar o dbt isolado:

```bash
cd lakehouse && export LH_BRONZE="$PWD/warehouse/bronze" LH_DUCKDB="$PWD/warehouse/lakehouse.duckdb"
cd dbt && dbt build --profiles-dir .     # 13 modelos + 16 testes de qualidade
dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .   # lineage + docs no navegador
```

As **análises estatísticas** (`an_*`: Friedman, Wilcoxon, perfis, SNR…) usam
scipy e continuam em `analytics.py` (não são SQL). `transform.py` é a versão
Python anterior de silver/gold — mantida como referência; o pipeline usa o dbt.

### Robustez (portão único)

```bash
python verify.py     # build + determinismo + idempotência + auditoria → "LAKEHOUSE ROBUSTO ✓"
```

Garante, além dos **16 testes dbt** (na build) e das **19 checagens** de
`tests/audit.py`: **determinismo** (reconstruir dá conteúdo idêntico — o gold é
arredondado a 4 casas para reprodutibilidade), **idempotência** (reingerir não
altera silver/gold) e a **reconciliação** painel × gold. Sai com código ≠ 0 se
algo falhar (pronto para CI).

## Painel + lakehouse: manter os dois em sincronia

O lakehouse é a **fonte única da verdade** dos números; o painel os apresenta.
`export_dashboard.py` (rodado no fim do `run_pipeline.py`) faz duas coisas:

1. **Exporta** a trajetória diária de `gold.daily_group` para
   `exports/dashboard_daily.json` (o painel pode consumir daí).
2. **Reconcilia** o gold contra a constante `DIM` embutida no
   `dashboard_humor.html` e falha se divergirem (guarda de deriva).

Fluxo de manutenção: chegou dado novo → `python run_pipeline.py` → se a
reconciliação apontar diferença, os dados do painel são regenerados a partir do
gold. Hoje os dois estão **consistentes** (as 7 variáveis batem, tolerância 0,1).

Consultar em SQL:

```python
import lh
lh.read_delta("gold", "daily_group")                 # trajetória diária do grupo
lh.sql("SELECT day_type, AVG(fadiga) FROM ad GROUP BY 1",
       ad=lh.read_delta("gold","athlete_day"))
lh.read_delta("bronze","brums_raw", version=0)        # time-travel (governança)
lh.history("bronze","brums_raw")                      # trilha de versões
```

## Crescer (quando precisar)

- **dbt-duckdb**: transforme `silver`/`gold` em modelos SQL versionados, com
  testes de qualidade, *lineage* e docs geradas automaticamente.
- **Dagster**: orquestração por *assets* (agenda micro-lotes da IoT, mostra a
  linhagem visual e re-executa só o que mudou).
- **MLflow**: registra experimentos e versões do modelo de risco.
- **Nuvem**: o mesmo código sobe sem reescrita — troque o caminho local por
  `s3://…`/`gs://…` no Delta e mantenha DuckDB/dbt.

Nada disso é necessário para começar: o núcleo (Delta + DuckDB) já entrega um
lakehouse funcional e reprodutível.
