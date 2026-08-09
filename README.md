# mdlucca — Backend Biomecânico (Landmine Clean & Press)

Migração do dashboard biomecânico autocontido (`Dashboard_Atleta2.html`) para
um **backend de dados + API de alta qualidade**, com as análises reimplementadas
em **padrão-ouro** (rigor estatístico via `numpy`/`scipy`).

> **Etapa 1 (este repositório):** tirar os dados e as análises de dentro do HTML
> monolítico e colocá-los num backend próprio — schema relacional, ETL e API REST.
> A fonte de pose continua sendo o **MediaPipe** (monocular).
>
> **Etapa 2 (roadmap):** plugar uma **fonte de pose de qualidade superior**
> (markerless calibrada / multi-câmera) sem trocar o schema nem a API. Ver
> [Roadmap](#roadmap--etapa-2-fonte-de-pose-de-alta-qualidade).

---

## Por que migrar

O HTML original é brilhante como artefato único, mas tem tudo acoplado: ~40
estruturas de dados e 3 vídeos em base64 embutidos, e ~40 análises calculadas
**à mão em JavaScript** no navegador. Isso torna impossível: consultar os dados,
reprocessá-los, versionar as análises ou validar os números de forma
independente.

Aqui os dados viram um banco consultável e as análises viram funções puras,
testáveis e recalculadas sob demanda pela API — com correções de rigor
estatístico onde o JS aproximava (ver [Análises padrão-ouro](#análises-padrão-ouro)).

## Arquitetura

```
 HTML monolítico            Etapa 1 — backend
 ┌───────────────┐          ┌──────────────────────────────────────────┐
 │ dados + vídeos │  extract │ data/dashboard_extracted.json            │
 │ + análises JS  │ ───────► │        │ ingest (ETL)                    │
 └───────────────┘          │        ▼                                 │
                            │ sql/schema.sql ──► data/db.sqlite (SQLite)│
                            │                        │                  │
                            │        app/analyses.py │ (numpy/scipy)    │
                            │                        ▼                  │
                            │             app/api.py  (FastAPI + OpenAPI)│
                            └──────────────────────────────────────────┘
```

| Camada        | Arquivo                        | Papel |
|---------------|--------------------------------|-------|
| Extração      | `scripts/extract_dashboard.py` | Puxa as `const` JSON do HTML (ignora vídeos), normaliza via Node |
| Schema        | `sql/schema.sql`               | Modelo relacional (16 tabelas). Compatível com `migrate.R` **e** `ingest.py` |
| Migração (R)  | `scripts/migrate.R`            | Aplica só o schema num banco vazio (caminho R original) |
| ETL           | `scripts/ingest.py`            | Aplica schema + popula o SQLite (via `--json` ou `--source`) |
| Fontes de pose| `app/sources/`                 | Interface `PoseSource` — MediaPipe (Etapa 1) + stub de alta qualidade (Etapa 2) |
| Sinais        | `app/signals.py`               | Savitzky-Golay, integração trapezoidal, diferenciação, reamostragem 0-100% |
| Análises estat.| `app/analyses.py`             | CV, Grubbs, bootstrap, logística, lei de potência, alométrico — puras |
| Análises profundas | `app/biomech.py`          | Impulso, trabalho, eficiência, RFD/TDF, MPV, balístico, jerk, potência articular, SSC, sequenciamento — recomputadas das séries |
| API           | `app/api.py`                   | REST (FastAPI), leitura de dados + recomputo das análises + cliente web |
| Cliente web   | `web/index.html`               | Dashboard que consome a API via `fetch()` (gráfico SVG, sem dependências) |
| Testes        | `tests/`                       | Recomputam e comparam com os valores do dashboard (12 testes) |

### Modelo de dados (resumo)

Dimensões: `athlete` → `session` → `submovement` (as 6 repetições/sub-movimentos).
Sinais brutos: **`series`** (uma linha por sinal por sub-movimento, amostras em
JSON) — é a fonte de verdade para recomputar tudo. Resultados escalares em
**`metric`** (EAV, namespaced por `analysis`); ajustes de modelo em **`fit`**;
estruturas ricas (esqueleto, trajetória 3D, curvas) em **`dataset`** (JSON, sem
perda). Mais: `variable`/`variable_series`, `sequencing_event`,
`joint_confidence`, `phase`/`phase_segment`, `literature_reference`,
`consistency_source`.

## Como rodar

```bash
make install            # numpy, scipy, fastapi, uvicorn, pytest
make db                 # cria data/db.sqlite a partir do JSON versionado
make api                # sobe em http://localhost:8000
make test               # valida as análises contra os dados (12 testes)
```

Depois de `make api`, abra:
- **`/app`** — o dashboard refatorado (consome tudo via `fetch()`);
- **`/docs`** — documentação interativa (OpenAPI) de todos os endpoints.

O ETL aceita a fonte de pose explicitamente: `python3 scripts/ingest.py
--source mediapipe` (equivalente ao default). A Etapa 2 usará `--source
highquality` assim que o adaptador estiver implementado.

> `data/dashboard_extracted.json` já vem versionado (é a entrada do ETL). Para
> regenerá-lo a partir do HTML original (que **não** vai no repo por conter os
> vídeos, ~20 MB), use `make extract HTML=/caminho/Dashboard_Atleta2.html`
> (requer Node.js). O banco `data/db.sqlite` é gerado e não é versionado.

O caminho R original também funciona: `Rscript scripts/migrate.R` aplica o
`sql/schema.sql` (idêntico ao usado pelo `ingest.py`) num banco vazio.

## API — principais endpoints

Documentação interativa (OpenAPI) em **`/docs`**.

**Dados**
- `GET /sessions/{id}` — sessão + atleta + sub-movimentos
- `GET /submovements/{id}/series` · `GET /submovements/{id}/series/{name}` — sinais brutos (+ vetor `t`)
- `GET /submovements/{id}/metrics?analysis=moments` — escalares por análise
- `GET /metrics?analysis=&name=` · `GET /fits?analysis=` · `GET /variables`
- `GET /literature` · `GET /consistency` · `GET /datasets/{kind}`

**Análises estatísticas padrão-ouro (recomputadas sob demanda)**
- `GET /compute/cv?metric=&scope=` — CV% + **IC bootstrap**
- `GET /compute/grubbs?metric=&scope=` — Grubbs **bilateral, valor crítico exato**
- `GET /compute/force-velocity` — perfil F-V: linear + lei de potência + IC bootstrap do expoente
- `GET /submovements/{id}/logistic?series=hip_angle` — ajuste logístico (nls) da fase concêntrica
- `GET /submovements/{id}/peak?series=force` — pico robusto (mediana de janela)
- `POST /compute/{cv,grubbs,powerlaw,logistic,bootstrap-slope}` — genéricos (JSON no corpo)

**Análises biomecânicas profundas (recomputadas das séries brutas)**
- `GET /submovements/{id}/analysis` — **painel completo** (roda tudo abaixo de uma vez)
- `GET /sessions/{id}/analysis` — painel agregado de todos os submovimentos
- `.../compute/impulse-work` · `.../compute/efficiency` — impulso, trabalho, eficiência (mgh vs trabalho real)
- `.../compute/rfd-tdf?onset=bottom` — RFD de pico + TDF em janelas fixas (0-50/100/150/200 ms)
- `.../compute/velocity` — MPV/PPV/MCV (Sánchez-Medina) · `.../compute/ballistic`
- `.../compute/jerk` — 3ª derivada com Savitzky-Golay reforçado
- `.../compute/joint-power?joint=hip|knee|elbow` — potência articular (τ·ω), trabalho ±
- `.../compute/ssc?joint=hip|knee|elbow` — tempo de amortização + RSI-mod
- `.../compute/sequencing` — ordem dos picos de velocidade angular (proximal→distal)
- `.../compute/normalized-cycle?series=hip_angle` — reamostragem 0-100% do ciclo

Estes recomputam por **integração trapezoidal** (`scipy.integrate`) e
**diferenciação com Savitzky-Golay** (`scipy.signal`) diretamente das séries,
não leem escalares pré-calculados. A validação (`tests/test_biomech.py`)
confirma que o trabalho articular, o tempo de amortização do SSC, o jerk de
pico e a MCV batem com os valores do dashboard.

## Análises padrão-ouro

As funções em `app/analyses.py` recalculam as métricas de forma independente e
corrigem aproximações do JavaScript original:

| Análise | O que faz | Melhoria vs. HTML |
|---------|-----------|-------------------|
| **CV** | Coeficiente de variação | Adiciona **IC 95% por bootstrap** (o HTML só dava a estimativa pontual) |
| **Grubbs** | Teste de outlier | **Valor crítico bilateral exato** via distribuição t. O HTML usava `1.672` (valor *unilateral*); o correto para n=5, α=0,05 com desvio absoluto máximo é **`1.715`**. Também retorna p-valor |
| **Lei de potência** | `y = a·x^b` | OLS em log-log + p do expoente + **IC bootstrap** do slope |
| **Logística** | `θ = b + L/(1+e^(−k(t−t₀)))` | `curve_fit` (nls) com **limites físicos** que evitam a solução degenerada; taxa de pico analítica `L·k/4` |
| **Alométrico** | Normalização por massa (Jaric, 2002) | `valor / massa^b` |

Validação: `make test` recomputa a partir das séries/valores brutos e compara com
os números que o dashboard reportava. Ex.: CV (5 seg) = 28,93%, power-law
`F=a·v^b` com b=0,615 / R²=0,801 / p=0,040, e Grubbs G=1,625 — todos batem; a
única divergência é a correção deliberada do valor crítico de Grubbs.

## Roadmap — Etapa 2 (fonte de pose de alta qualidade)

O ponto fraco da Etapa 1 **não é a análise, é o dado de entrada**. O próprio
dashboard já documenta os limites do MediaPipe monocular: sem calibração de
câmera, pivô do landmine não estimável (0,02–1,14 m), torque de joelho no método
simplificado, correção de câmera-lenta 2x, e scores de visibilidade variáveis.

A Etapa 2 troca a fonte de pose mantendo schema e API intactos:

1. **Ingestão de fonte de pose superior** — markerless calibrada (multi-câmera /
   research-grade) ou serviço equivalente, com coordenadas 3D métricas reais.
   Basta um novo adaptador de ingestão que grave em `series`/`metric` com
   `session.pose_source` = nova fonte.
2. **Calibração de câmera** — habilita escala métrica real, dinâmica inversa com
   força de reação do solo e o torque de joelho por método completo (hoje frágil).
3. **Versionamento por fonte** — o schema já carrega `pose_source`/`pose_model`
   em `session`, permitindo comparar MediaPipe × nova fonte lado a lado.

O ponto de extensão já existe: `app/sources/PoseSource`. A nova fonte só
precisa implementar `bundle()` produzindo o formato canônico — todas as
análises padrão-ouro são recomputadas automaticamente pela API. O stub
`app/sources/highquality.py` documenta o contrato de entrada esperado.

> O **cliente web** (`web/index.html`) já foi refatorado nesta entrega:
> consome 100% da API via `fetch()`, sem dados embutidos.

## Estrutura do repositório

```
sql/schema.sql               modelo relacional
scripts/extract_dashboard.py extração HTML -> JSON
scripts/ingest.py            ETL JSON/fonte -> SQLite
scripts/migrate.R            aplicação do schema (caminho R)
app/db.py                    acesso ao SQLite (read-only)
app/signals.py               processamento de sinal (SG, integração, reamostragem)
app/analyses.py              análises estatísticas (numpy/scipy)
app/biomech.py               análises biomecânicas profundas (das séries)
app/api.py                   API REST (FastAPI) + mount do cliente web
app/sources/                 adaptadores de fonte de pose (base/mediapipe/highquality)
web/index.html               cliente que consome a API via fetch (gráfico SVG)
tests/test_analyses.py       validação estatística
tests/test_biomech.py        validação das análises profundas
data/dashboard_extracted.json entrada versionada do ETL
Makefile · requirements.txt
```
