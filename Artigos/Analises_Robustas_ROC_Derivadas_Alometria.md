# Análises estatísticas robustas — tamanhos de efeito, ROC, derivadas, curvas não lineares, ajustes logísticos e alometria (microciclo 21–28/04/2024)

> **Escopo.** Semana de 21–27/04 (baseline 21/04; HIIT 22, 24, 27/04). Reanálise independente em Python (numpy, scipy, statsmodels). Atletas anonimizados. Reprodutibilidade: `../scripts/analise/robust.py`.

---

## 1. Tamanhos de efeito D1 → D7 (por atleta, IC bootstrap 95%)

O acúmulo do baseline à última sessão é **grande** no eixo energia–fadiga, com a fadiga física à frente (Tabela 1). O TMD, mais ruidoso, tem IC que toca zero — coerente com sua alta variância.

**Tabela 1.** Efeito do acúmulo D1 → D7 (n = 21; dz e Hedges g com IC bootstrap).

| Variável | dz [IC 95%] | Hedges g | Magnitude |
|---|---|---|---|
| **Fadiga física** | **+1,74** [+1,32; +2,62] | +1,74 | muito grande |
| Vigor | **−0,95** [−1,60; −0,56] | −1,03 | grande |
| Fadiga (BRUMS) | +0,72 [+0,31; +1,38] | +0,78 | médio–grande |
| TMD | +0,41 [−0,01; +0,87] | +0,44 | pequeno–médio |
| **Multivariado (6 subescalas)** | **D de Mahalanobis = 1,55** [1,24; 4,25] | — | grande |

## 2. Limites e derivadas da trajetória (velocidade e aceleração da mudança)

Diferenciando numericamente as médias diárias, localiza-se **onde** a mudança se concentra (Tabela 2). A **velocidade** (1ª derivada) do TMD é máxima **no Dia 7** (+3,5/dia) — a deterioração se precipita no fim; a **aceleração** (2ª derivada) do TMD e da fadiga física é máxima nos **dias 5–6**, ponto de inflexão a partir do qual a curva dispara rumo ao Dia 7. O vigor cai mais rápido logo no início (D1→D2, primeiro choque) e novamente no fim.

**Tabela 2.** Derivadas da trajetória diária.

| Variável | Trajetória D1…D7 | Velocidade máx. | Aceleração máx. |
|---|---|---|---|
| TMD | 2,0 → 4,7 → 4,5 → 5,7 → 1,8 → 4,5 → **8,0** | Dia 7 (+3,5/dia) | Dia 5 |
| Fadiga física | 4,3 → … → **7,6** | Dia 1 (+1,4/dia) | Dia 6 |
| Vigor | 7,5 → 5,8 → … → **4,7** | Dia 1 (−1,7/dia) | Dia 3 |

Substantivamente: a semana não é uma reta descendente, mas uma **gangorra com precipitação final** — o alívio parcial do meio da semana (Dia 5) é seguido de aceleração da fadiga até o Dia 7.

## 3. Curvas não lineares (comparação por AIC)

Ajustando modelos concorrentes às médias diárias, o **cúbico** vence tanto para o TMD quanto para a fadiga física (Tabela 3) — reflexo direto do padrão em gangorra (queda, alívio no meio, disparo final), que nem a reta nem a exponencial nem a logística capturam. Confirma-se, por seleção de modelo, a **não-linearidade** da trajetória.

**Tabela 3.** AIC dos ajustes por dia (menor = melhor).

| Variável | Linear | Quadrático | Cúbico | Exponencial | Logístico | Melhor |
|---|---|---|---|---|---|---|
| TMD | 11,1 | 12,8 | **6,2** | 10,0 | 11,8 | **cúbico** |
| Fadiga física | −3,9 | −2,9 | **−11,9** | −1,9 | −2,7 | **cúbico** |

## 4. Ajustes logísticos

**Crescimento do perfil "não-iceberg".** A proporção de atletas fora do perfil iceberg cresce de 7% (D1) a 33% (D7); o ajuste logístico situa o **ponto médio da transição por volta do Dia 6** (t₀ ≈ 6,0), com inclinação acentuada — a "quebra" do perfil concentra-se no fim da semana.

**Regressão logística (nível de observação).** A probabilidade de um estado de **fadiga física alta (≥ 8/10)** cresce com o dia e cai com a aptidão prévia (Tabela 4): cada dia multiplica as chances por **1,31** (+31%/dia; *p* < 0,001) e cada km/h a mais de PV do T-CAR as **reduz à metade** (OR = 0,50; *p* < 0,001). Em dose-resposta, cada ponto de fadiga física eleva em **59%** as chances de perturbação de humor acima da mediana (OR = 1,59; *p* < 0,0001).

**Tabela 4.** Modelos logísticos.

| Modelo | Preditor | OR | *p* |
|---|---|---|---|
| P(fadiga física ≥ 8) | Dia (por dia) | 1,31 | < 0,001 |
| P(fadiga física ≥ 8) | PV do T-CAR (por km/h) | 0,50 | < 0,001 |
| P(TMD > mediana) | Fadiga física (por ponto) | 1,59 | < 0,0001 |

## 5. Escalonamento alométrico (log-log: Y = a·massa^b)

A carga externa e a aptidão escalam **negativamente** com a massa corporal (Tabela 5): atletas mais pesados têm menor PV do T-CAR (expoente −0,19) e, por decorrência da prescrição relativa, menor velocidade e distância — a massa é um ônus na corrida de campo. Crucialmente, ao **escalar a aptidão alometricamente** (PV/massa^0,5), a relação protetora com a fadiga da semana **permanece** (ρ = −0,52 vs −0,54 na PV bruta): o efeito "mais apto → fadiga menos" **não é artefato de tamanho corporal**.

**Tabela 5.** Expoentes alométricos e robustez da moderação.

| Relação | Expoente *b* (massa) | *r* log-log |
|---|---|---|
| PV do T-CAR ~ massa^b | −0,19 | −0,48 |
| Velocidade (104%) ~ massa^b | −0,17 | −0,42 |
| Distância/sessão ~ massa^b | −0,17 | −0,42 |
| Fadiga física (semana) ~ PV **bruta** | ρ = −0,54 (*p* = 0,005) | |
| Fadiga física (semana) ~ PV **escalada** (/massa^0,5) | ρ = −0,52 (*p* = 0,007) | |

## 6. Curvas ROC (AUC, IC 95% bootstrap, corte de Youden)

O contraste entre as três tarefas é **o achado central** (Tabela 6): as variáveis de humor/fadiga **não** discriminam a sessão de HIIT isolada (AUC ≈ 0,52–0,56, IC tocando 0,50), mas discriminam **fortemente** o **acúmulo** (D7 vs D1: fadiga física **AUC = 0,86**) e o **dia de fadiga alta** (fadiga do BRUMS AUC = 0,84; TMD 0,79). Isto é, o sinal do monitoramento **não está na sessão, mas na tendência**.

**Tabela 6.** ROC em três tarefas (obs; AUC [IC 95%]).

| Variável | T1: dia de HIIT | T2: D7 vs D1 (acúmulo) | T3: dia de fadiga alta |
|---|---|---|---|
| Fadiga física | 0,54 [0,48; 0,60] | **0,86** [0,77; 0,92] | — |
| Fadiga (BRUMS) | 0,53 | 0,75 [0,65; 0,84] | **0,84** [0,80; 0,88] |
| TMD | 0,56 [0,51; 0,62] | 0,68 [0,56; 0,78] | 0,79 [0,74; 0,83] |
| Vigor | 0,52 | 0,72 [0,61; 0,82] | 0,72 [0,68; 0,77] |

Corte de Youden da fadiga física para o acúmulo (T2): sensibilidade 0,74 / especificidade 0,83 — um limiar operacional útil para sinalizar o estado de fadiga do fim do microciclo.

---

## 7. Síntese

As análises robustas convergem para três conclusões, cada uma reforçada por método próprio:

1. **A magnitude é grande, mas concentrada** — dz D1→D7 de +1,74 (fadiga física) e −0,95 (vigor), D de Mahalanobis = 1,55; e as **derivadas** e o **melhor ajuste cúbico** localizam a deterioração numa **precipitação final** (aceleração nos dias 5–6, velocidade máxima no Dia 7), não numa reta.
2. **A aptidão protege, e não é artefato de tamanho** — a **logística** quantifica (OR = 0,50 por km/h de PV) e a **alometria** confirma que escalar pela massa não dissolve o efeito.
3. **O sinal está na tendência, não na sessão** — a **ROC** é inequívoca: humor/fadiga são quase inúteis para flagrar a sessão de HIIT (AUC ≈ 0,5), mas excelentes para o acúmulo (AUC até 0,86). Monitorar por tendência ao longo do microciclo, não por evento isolado.

---

*Reprodutibilidade: `../scripts/analise/robust.py` (efeitos + BCa, derivadas por diferenças finitas, curve_fit não linear, sm.Logit, alometria log-log, ROC com IC bootstrap e Youden). Bootstrap com semente fixa.*
