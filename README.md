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

## Licenciamento (white-label — vender acesso)

O produto exige uma **licença** assinada por você (Ed25519). Você emite
acesso para quem pagar — ou cortesias grátis — com validade a definir; sem
licença válida a API responde **402** (exceto `/health`, `/license`,
`/branding`, `/docs` e a interface web). Cada licenciado roda com a **marca**
dele. Passo a passo em **[LICENSING.md](LICENSING.md)**.

```bash
make license-genkey                 # 1x: gera seu par (guarde a privada!)
make license-issue LICENSEE="Academia X" BRAND="X Performance" DAYS=365 OUT=x.key
# cliente ativa: MDLUCCA_LICENSE=<token>  (ou data/license.key)
```
Endpoints abertos: `GET /license` (estado) e `GET /branding` (marca). Em
desenvolvimento, `MDLUCCA_DEV=1` libera tudo.

## Como rodar

**Mais fácil (1 clique):** no **Windows** dê duplo-clique em **`iniciar.bat`**;
no **Mac/Linux** rode **`bash iniciar.sh`**. Ele instala o necessário, prepara o
banco e abre `http://127.0.0.1:8000/app/gerir.html` no navegador. Para parar,
feche a janela.

**Manual:**
```bash
make install            # numpy, scipy, fastapi, uvicorn, pytest
make db                 # cria data/db.sqlite a partir do JSON versionado
make api                # sobe em http://localhost:8000
make test               # valida as análises contra os dados
```
No Windows sem `make`:
```powershell
pip install -r requirements.txt
python scripts\ingest.py --db data\db.sqlite
python -m uvicorn app.api:app --port 8000
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

**Avaliação completa (unificada — "gera tudo" numa chamada)**
- `GET /sessions/{id}/assessment` (`?deep=true` inclui o painel completo por rep)
  — devolve num só objeto: **classificação do movimento** (padrão + confiança),
  **score de qualidade** (nível + avisos), **checagens de literatura** (ISB,
  Atkinson & Nevill), **resumo por repetição** e **procedência** (fonte de pose,
  fps, calibração, versão do algoritmo).
- `POST /sessions/{id}/assessment` — **persiste** um `AnalysisRun` e devolve o id.
- `GET /assessments` · `GET /assessments/{id}` · `GET /assessments/{id}/report.md`
  — histórico e **relatório Markdown** pronto. Botão "Avaliar" em `/app/gerir.html`.

**Upload pelo atleta + fila de análise (o treinador analisa)**
- `POST /athletes/{id}/uploads` (multipart) — o **atleta envia o próprio vídeo**;
  entra na fila `queued`. Tela do atleta em **`/app/enviar.html`**.
- `GET /uploads` · `GET /uploads/{id}` · `GET /athletes/{id}/uploads` — status
  (`queued|processing|done|error`).
- `POST /uploads/{id}/analyze` — o **treinador dispara**: roda pose→sessão em
  background e **liga a sessão ao atleta dono**. Fila na tela `/app/gerir.html`.
- Requer no servidor: `mediapipe`, `opencv-python-headless` e a variável
  **`MDLUCCA_POSE_MODEL`** apontando para o `pose_landmarker_*.task`.

**Perfil Força-Velocidade-Potência (teste de cargas)**
- `POST /compute/fvp` `{loads_kg, velocities, bodyweight_kg?, v1rm?}` — traça o
  perfil de um teste de cargas incremental: **componente gravitacional** (F=m·g),
  regressão **Carga-Velocidade** (+1RM estimado), regressão **Força-Velocidade**
  (F0, V0, Sfv), **Potência-Velocidade** (Pmax, velocidade e carga ótimas),
  **ajuste quadrático** (comparação de modelos), **ajustes alométricos**
  (Pmax/kg e Pmax/kg^0.67 — Jaric) e interpretação automática. Equações de
  regressão retornadas como texto. Com **`com_displacement_m`** (deslocamento
  vertical do centro de massa) adiciona os **equivalentes**: trabalho mecânico
  (W=F·d), potência média na carga ótima, **altura equivalente** (h=v²/2g) e
  F0 em pesos corporais.
- `GET /athletes/{id}/fvp?exercise=&velocity_metric=vbt.MPV` — monta o teste de
  cargas a partir das **sessões do atleta** em cargas diferentes.
- Tela **`/app/fvp.html`** — insere cargas/velocidades (ou carrega do atleta) e
  **traça F-v e P-v** (gráficos), com Pmax, carga ótima e 1RM.
- `POST /compute/samozino` `{bodyweight_kg, added_loads_kg, jump_heights_m,
  push_off_m}` — **modelo balístico de Samozino**: perfil F-V-P a partir de
  saltos com cargas (F=m·g·(h/hPO+1); v=√(g·h/2)) e **FVimb** (desequilíbrio
  força-velocidade vs perfil ótimo). Devolve F0/v0/Pmax (absolutos e relativos),
  perfil ótimo (Sfv_opt), **déficit de força ou velocidade**, altura atual ×
  ótima e ganho potencial. O perfil ótimo é obtido maximizando a altura no
  próprio modelo de Samozino (m·g·(h/hPO+1)=F0−Sfv·√(g·h/2)), sem constantes de
  memória. Painel "Modo salto" em `/app/fvp.html`.

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

**Cinemática — recomputa ângulos/CoG a partir dos LANDMARKS de pose**
- `GET /submovements/{id}/kinematics/angles?aspect=auto` — ângulos articulares
  recalculados dos landmarks (`app/kinematics.py`)
- `GET /submovements/{id}/kinematics/cog?aspect=auto` — centro de gravidade (De Leva 1996)

**Configurável — escolha segmentos e o que medir**
- `GET /segments` — vocabulário de segmentos/pontos anatômicos e grupos
  (`all`, `sem_bracos`, `pernas`, `bracos`, ...). Base para incluir/excluir
  braços, pontos, etc.
- `POST /submovements/{id}/measure` — roda **apenas as medidas escolhidas**
  sobre os **segmentos escolhidos**, num único endpoint:
  ```json
  {"include_segments":"sem_bracos",
   "measures":["impulso_trabalho","velocidade_angular","fases","elastico"],
   "joint":"hip","phase_series":"cog_y"}
  ```
  Medidas disponíveis: `impulso_trabalho`, `velocidade_angular`, `velocidade`,
  `balistico`, `jerk`, `potencia_articular`, `ssc`, `fases`, `elastico`,
  `sequenciamento`.
- Nos vídeos: `render_legs3d_video.py --segments all|sem_bracos|pernas|bracos`
  (ou lista) controla **quais segmentos são desenhados** (com/sem braços).

**Produto — cadastro de alunos e link compartilhável** (escrita no banco)
- Tela web: **`/app/gerir.html`** — cadastrar aluno, listar alunos/sessões e
  gerar o **link do relatório** com um clique (para enviar por WhatsApp).
- `POST /athletes` — cadastra aluno (IMC calculado automaticamente).
  `POST /athletes/{id}/update` · `POST /athletes/{id}/delete`.
- `POST /sessions` — cria uma sessão manual (registro) para um aluno
  (`%peso corporal` calculado a partir da massa).
- `POST /shares` `{kind:"session",ref_id,audience}` → devolve `{token,url}`.
  `GET /r/{token}` — **relatório HTML autossuficiente** (gráfico de potência
  por repetição + tabela de métricas), sem senha, abre em qualquer celular.
  `GET /shares` lista os links criados (com contador de visualizações).
- A tabela `share` é criada automaticamente na 1ª escrita (idempotente); o
  motor de análise não muda. Escrita usa `db.connect_rw()`; leitura segue
  em modo somente-leitura.
- Tela **`/app/checklist.html`** — checklist visual de tudo que o sistema
  analisa em tempo real (com contadores ao vivo da API).

- Botão **"⚙ Gerar massa de teste"** na tela `/app/gerir.html` chama
  `POST /demo/seed` (não precisa de terminal).

**Deploy online** — ver **[DEPLOY.md](DEPLOY.md)**. `Dockerfile` + `render.yaml`
prontos; `scripts/start.sh` cria o banco no **disco persistente** só na 1ª vez e
**preserva** alunos/sessões/links nos deploys seguintes. O motor de análise é o
mesmo local e online.

**Massa de teste (dados fictícios)** — `make seed` (ou
`python3 scripts/seed_demo.py --reset --athletes 4 --reps 5 --shares`) popula
o banco com atletas/sessões/métricas sintéticas realistas e já imprime os
links dos relatórios, para testar o fluxo cadastro→análise→relatório de ponta
a ponta sem precisar de vídeo. Remove a massa anterior com `--reset` (atletas
`ext_key` `demo-*`). Coberto por `tests/test_product.py`.

**Fases e componente elástico (transições concêntrica↔excêntrica)**
- `GET /submovements/{id}/phases?series=cog_y` — segmenta **todo** o movimento
  em fases concêntrica/excêntrica/isométrica (robusto: suavização + histerese +
  fusão de trechos curtos) e lista as **transições** (marca as SSC
  excêntrica→concêntrica).
- `GET /submovements/{id}/elastic?series=cog_y&power=power` — **componente
  elástico** por transição: tempo de amortização, trabalho excêntrico
  (absorvido) × concêntrico (gerado) e **EUR** (razão de utilização elástica).

**Qualidade de sinal, calibração métrica e alometria**
- `POST /calibrate/reference` — escala (m/px) por **objeto de tamanho conhecido**
  no quadro (régua/barra): dois pontos em px + comprimento real.
- `POST /calibrate/stature` — escala pela **estatura real** do atleta
  (nariz→tornozelo em px). Converte as estimativas em medidas confiáveis.
- `GET /submovements/{id}/filtered?series=&cutoff=` — série **bruta × filtrada**
  (**Butterworth passa-baixa de fase zero**, padrão em biomecânica) + **métricas
  de ruído** (SNR) e **análise de resíduo** (Winter) para escolher a frequência
  de corte.
- `GET /sessions/{id}/allometric?b_force=0.67&b_power=1.0` — **ajuste alométrico**
  (Jaric, 2002): normaliza força/potência de pico pela massa^expoente, para
  comparar atletas de tamanhos diferentes de forma justa.

Correção de **quadros**: frames sem pose agora são **interpolados linearmente**
entre vizinhos (antes eram indevidamente preenchidos com o 1º quadro) — ver
`app/signals.stack_frames` / `interpolate_gaps`.

**Calibração integrada ao pipeline** — informe a **estatura real** do atleta e
todas as alturas (cm) passam a usar a escala calibrada em vez da estimativa:
```bash
make pipeline VIDEO=clip.mp4 MODEL=pose.task           # + no comando:
python3 scripts/pipeline.py --video clip.mp4 --model pose.task --stature 1.55 --legs3d
```
A sessão grava `meta.calibration` (fonte + cm/px) e o overlay 3D mostra a escala
usada. Ex.: no salto de ginástica, a altura do quadril passa de 107 cm
(estimado) para 128 cm (calibrado com estatura 1,55 m).

**Padrões de literatura internacional e valores de referência**
- `GET /standards` — os padrões metodológicos que o sistema segue, **com
  citação**: Butterworth 6 Hz (Winter 2009), antropometria De Leva (1996),
  ângulos ISB (Wu et al. 2002/2005), alometria (Jaric 2002), amostragem/Nyquist,
  MPV/VBT (Sánchez-Medina & González-Badillo 2011), RFD (Maffiuletti et al. 2016).
- `GET /reference-bands` · `POST /reference-check` — compara as medições às
  faixas de referência (critério técnico/estatístico) e devolve **status por
  métrica** com a fonte. Ex.: joelho 175° → *ótimo*; split 146° → *adequado*;
  CV 4,3% → *ótimo* (Atkinson & Nevill 1998).

> As referências **metodológicas** (como medir) são consolidadas e citadas.
> Faixas de **desempenho** vêm como critério técnico (ex.: extensão = 180°) ou
> indicativas — normas por modalidade/nível exigem base validada da população.

Esta é a ponte **landmarks → biomecânica** que a Etapa 2 usa: a fonte de pose
só fornece landmarks; este módulo produz as séries e o resto segue por cima.
Os landmarks do MediaPipe vêm normalizados por largura/altura separadamente
(distorce ângulos pelo aspect ratio, não gravado). `aspect=auto` **recupera**
esse fator ajustando aos ângulos armazenados — e a validação
(`tests/test_kinematics.py`) mostra **correlação > 0,98** entre os ângulos
recomputados dos landmarks e as séries do dashboard (quadril, joelho,
cotovelo). Sob a Etapa 2 (coordenadas métricas calibradas), o aspect vira 1
e a defasagem residual desaparece.

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

## Pipeline de vídeo (pose → biomecânica) — exemplo real

O backend não depende mais de dados pré-computados: dá para analisar um
**vídeo novo** de ponta a ponta.

```bash
pip install mediapipe opencv-python-headless
# baixe um modelo (ex.: pose_landmarker_full.task) de
#   https://storage.googleapis.com/mediapipe-models/pose_landmarker/
make video VIDEO=meu_video.mkv MODEL=pose_landmarker_full.task MASS=80
make api    # abra /app?session=2
```

Etapas (`scripts/pose_extract.py` + `scripts/build_session_from_pose.py`):
1. **ffmpeg** extrai os frames.
2. **MediaPipe PoseLandmarker** produz os **world landmarks 3D (metros)** por frame.
3. O construtor computa as séries a partir dos landmarks 3D (ângulos, velocidades
   angulares, velocidade da barra, CoG por De Leva) e **estima a cinética pelo
   método do centro de massa** (massa corporal assumida — sem plataforma de
   força), segmenta as repetições pela altura da barra e insere como nova sessão.
4. **Todas** as análises da API rodam sobre a nova sessão.

Exemplo já processado (vídeo 720×720, 25 fps, 20 s → 3 reps detectados,
pose em 502/502 frames): as análises cinemáticas (ROM, MPV/PPV, jerk, SSC,
sequenciamento, consistência entre reps) são sólidas; as métricas de força/
potência são **estimativas do método do CoM** (rótulo explícito) e viram
medidas exatas quando houver massa/carga reais e calibração — o alvo da Etapa 2.

### Figuras analíticas (força, potência, momentos, fadiga)

`scripts/plot_session.py` gera todas as figuras de uma sessão de vídeo e um
`metrics.json`:
```bash
python3 scripts/plot_session.py --session 16 \
  --pose data/out/pose_XXXX.json --mass 87 --load 90 --out data/out/analise_16
# ou: make plots SESSION=16 POSE=data/out/pose_XXXX.json MASS=87 LOAD=90
```
Produz: **força-potência** (séries com raw vs filtrado Butterworth 6 Hz),
**analítica** (F-v, potência×ângulo, picos/trabalho por rep), **momentos**
(torque quadril/joelho/tornozelo por dinâmica inversa quase-estática De Leva +
diagrama de aplicação de forças) e **fadiga** (pico de potência/velocidade,
concêntrico×excêntrico "pico de queda", curvas normalizadas e **índice de
fadiga**: perda de velocidade, queda de potência, FI). Filtros:
Butterworth 6 Hz zero-fase (Winter) + Savitzky-Golay.

### Vídeo anotado (pronto para postar)

`scripts/render_overlay.py` gera um vídeo com o **esqueleto de pose** e a
**biomecânica ao vivo** sobreposta: fase/repetição, velocidade das mãos e
ângulos articulares referenciados ao **padrão de extensão de 180°** (mostrando
o déficit de extensão), com identidade de marca.

```bash
make overlay SESSION=2 BRAND="De Lucca Esporte"   # -> data/overlay.mp4
```

## Automação (estilo n8n)

Todo o fluxo — vídeo → pose → sessão → análises → overlays → dashboard — roda
com **um comando** ou por **gatilho**, encadeando "nós" determinísticos
(`scripts/pipeline.py`), cada um idempotente e com status/tempo no manifest.

```
 vídeo ──► [pose] ──► [session] ──► [overlay] ──► [dashboard] ──► [legs3d] ──► manifest.json
           MediaPipe   SQLite        video          video           2 pernas
```

Três formas de disparar:

```bash
# 1) manual — um comando faz tudo
make pipeline VIDEO=clip.mp4 MODEL=pose_landmarker_full.task

# 2) API (para o n8n chamar via HTTP)
export MDLUCCA_POSE_MODEL=/caminho/pose_landmarker_full.task
make api
curl -X POST localhost:8000/pipeline/run \
     -H 'content-type: application/json' \
     -d '{"video":"/abs/clip.mp4","athlete":"Atleta X","legs3d":true}'
# -> {job_id}; acompanhe em GET /pipeline/jobs/{job_id} (devolve o manifest)

# 3) watcher — solte vídeos numa pasta e ela processa sozinha
make watch MODEL=pose_landmarker_full.task     # observa data/inbox/
```

O workflow do **n8n** já vem pronto em `n8n/delucca_pipeline.json` — importe no
n8n e você tem: **Webhook (novo vídeo) → POST /pipeline/run → Aguardar →
GET status (loop) → Responder com o manifest**. Troque a URL
`host.docker.internal:8000` pela do seu backend. Para rodar tudo dentro do n8n
sem a API, use um nó **Execute Command** chamando `python3 scripts/pipeline.py`.

## O que falta para ficar "perfeito" (roadmap de qualidade)

O pipeline é sólido, mas há gaps conhecidos — listados por honestidade e por
ordem de impacto:

**Qualidade do dado (maior impacto):**
- **Calibração métrica real** — hoje a escala (cm) vem estimada do tronco e o
  solo é inferido pela posição dos pés. Ideal: objeto de referência de tamanho
  conhecido no quadro ou calibração de câmera. Enquanto isso, alturas/forças
  são **estimativas**, não medidas.
- **3D verdadeiro (multi-câmera)** — uma câmera dá profundidade aproximada
  (world landmarks do modelo) e sofre com oclusão do lado afastado.
- **Força/potência reais** exigem **plataforma de força**; hoje é método do
  centro de massa com **massa assumida**.
- **Taxa de amostragem** — 20–30 fps limita eventos rápidos (RFD, impacto);
  o ideal para explosivos é 120–240 fps.

**Robustez do pipeline:**
- Interpolação de frames sem pose e rejeição de outliers de tracking.
- **Classificação automática do exercício** e contagem de reps mais robusta.
- **Validação contra ground-truth** (goniômetro/mocap) para reportar erro (±°).

**Engenharia/produto:**
- Fila de jobs real (Redis/RQ/Celery) + persistência/retry, no lugar do
  subprocess em memória; storage de objetos; banco de produção (Postgres).
- **Autenticação/multi-tenant** e **consentimento/LGPD** (atenção: imagem de
  menores). Notificações (e-mail/WhatsApp) ao concluir; UI de upload+galeria.
- Docker/compose, CI (GitHub Actions), versionamento de modelos, observabilidade.

**Análise:**
- Bandas de referência por modalidade/nível; **comparação temporal** (evolução
  do atleta entre datas); relatório PDF automático e export dos dados.

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

A camada **landmarks → biomecânica** (`app/kinematics.py`) já está construída
e validada (corr > 0,98 vs. dashboard): a nova fonte fornece landmarks 3D
métricos e o motor produz ângulos/CoG sem o ajuste de aspect ratio (que só
existe por causa da pose normalizada não-calibrada da Etapa 1).

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
app/kinematics.py            ângulos/CoG a partir dos landmarks (ponte Etapa 2)
app/api.py                   API REST (FastAPI) + mount do cliente web
app/sources/                 adaptadores de fonte de pose (base/mediapipe/highquality)
web/index.html               cliente que consome a API via fetch (gráfico SVG)
tests/test_analyses.py       validação estatística
tests/test_biomech.py        validação das análises profundas
data/dashboard_extracted.json entrada versionada do ETL
Makefile · requirements.txt
```
