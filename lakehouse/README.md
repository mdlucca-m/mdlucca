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
| Motor SQL | **DuckDB** | consultas e transformações in-process, zero-config, muito rápido |
| ML | **scikit-learn** | classificador de risco (já usado no estudo) |
| Ingestão IoT | **FastAPI** (opcional) | um endpoint HTTP grava eventos na mesma bronze |
| Orquestração | runner Python (→ **Dagster**/**dbt** ao crescer) | um comando hoje; assets/lineage depois |

## Arquitetura medallion

```
fontes (CSV/IoT anonimizados, A01–A27)
   │  ingest.py  (append-only + metadados de carga)
   ▼
BRONZE  bruto, fiel ao que chegou      warehouse/bronze/{brums_raw, hiit_raw, wellbeing_raw}
   │  transform.build_silver()  (conformar · tipar · DEDUPLICAR · pré/pós)
   ▼
SILVER  limpo e conformado             warehouse/silver/{mood, wellbeing, hiit}
   │  transform.build_gold()   (agregar · features)
   ▼
GOLD    pronto p/ análise, painel, ML  warehouse/gold/{athlete_day, daily_group, acute_prepos, risk_features}
   │
   ├──►  painel do humor / SQL (DuckDB)
   └──►  ml_risk.py  →  ml/risk_model.pkl  (+ metrics.json)
```

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
python run_pipeline.py          # bronze → silver → gold → ML (constrói warehouse/)
```

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
