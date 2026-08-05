# Análises post hoc — comparações par a par entre dias e entre sessões (microciclo 21–28/04/2024)

> **Escopo.** Post hoc após os modelos mistos com efeito de dia significativo (janela 21–27/04). Médias marginais estimadas (EMM) do modelo `y ~ C(dia) + (1|atleta)`; contrastes par a par (21 pares) corrigidos por **Tukey** (amplitude estudentizada) e **Holm**. Sessões de HIIT (S1/S2/S3) por contraste pareado com correção de Holm e confirmação de Wilcoxon. Reprodutibilidade: `../scripts/analise/posthoc.py`. Atletas anonimizados.

---

## 1. Médias marginais por dia (EMM)

**Tabela 1.** EMM por dia e nº de pares significativos (Tukey p < 0,05).

| Variável | D1 | D2* | D3 | D4* | D5 | D6 | D7* | Pares sig. (de 21) |
|---|---|---|---|---|---|---|---|---|
| Fadiga física | 4,16 | 5,56 | 6,01 | 6,73 | 5,82 | 6,13 | **7,60** | **12** |
| Fadiga (BRUMS) | 3,71 | 4,97 | 5,26 | 5,88 | 4,89 | 5,51 | **7,14** | 8 |
| Vigor | 7,45 | 5,80 | 5,50 | 5,13 | 5,56 | 5,60 | **4,44** | 7 |
| TMD | 2,26 | 4,17 | 3,60 | 4,66 | 2,03 | 4,35 | **7,80** | 5 |

*(\* = dia de HIIT)*

## 2. Cada dia versus o baseline (D1)

O padrão distingue nitidamente as variáveis **sensíveis desde cedo** das que só se separam do baseline **no fim** (Tabela 2).

**Tabela 2.** Contraste de cada dia contra o baseline (D1); ✔ = Tukey p < 0,05.

| Variável | D2 | D3 | D4 | D5 | D6 | D7 |
|---|---|---|---|---|---|---|
| **Fadiga física** | ✔ (+1,40) | ✔ (+1,85) | ✔ (+2,57) | ✔ (+1,66) | ✔ (+1,97) | ✔ (+3,44) |
| **Vigor** | ✔ (−1,65) | ✔ (−1,95) | ✔ (−2,32) | ✔ (−1,89) | ✔ (−1,85) | ✔ (−3,01) |
| Fadiga (BRUMS) | — | ✔ (+1,56) | ✔ (+2,17) | — | ✔ (+1,80) | ✔ (+3,43) |
| **TMD** | — | — | — | — | — | ✔ (+5,53) |

- A **fadiga física** e o **vigor** já diferem do baseline **desde o primeiro dia de treino (D2)** e em todos os dias seguintes — são os marcadores mais precoces e sensíveis.
- O **TMD** só se distingue do baseline **no Dia 7** — a perturbação total é ruidosa e só "acende" na precipitação final.

## 3. O Dia 7 e a precipitação final

Para o TMD, **todos** os 5 pares significativos envolvem o Dia 7, e o **maior contraste de toda a análise** é **D5 → D7 (Δ = +5,77; Tukey p < 0,001)** — o salto do vale do meio de semana (D5) ao pico do fim. Isso confirma, por comparação múltipla corrigida, o que as derivadas e o ajuste cúbico indicaram: a deterioração do humor global **se precipita no Dia 7**, não se distribui uniformemente. A fadiga física, por sua vez, mostra a **gangorra** explicitamente — o contraste **D4 → D5 é significativo e negativo** (Δ = −0,91; p = 0,030): há alívio real no meio da semana, seguido de nova subida.

## 4. Post hoc da carga interna entre sessões de HIIT

A queda da FC de pico **concentra-se na sessão final** (Tabela 3): S1→S2 não difere, mas **S2→S3 (Δ = −3,04; dz = −0,89; p = 0,003)** e **S1→S3 (Δ = −3,79; p < 0,001)** são significativos (confirmados por Wilcoxon). A percepção de esforço sobe sobretudo na última sessão (S2→S3 Δ = +0,53), mas não sobrevive à correção de Holm.

**Tabela 3.** Contrastes pareados entre sessões (S1 = 22/04, S2 = 24/04, S3 = 27/04; n = 24).

| Métrica | S1→S2 | S2→S3 | S1→S3 |
|---|---|---|---|
| FC de pico (bpm) | −0,75 (n.s.) | **−3,04** (p_Holm = 0,003) | **−3,79** (p_Holm = 0,001) |
| PSE | −0,02 (n.s.) | +0,53 (p_Holm = 0,057) | +0,51 (n.s.) |

O sinal objetivo de fadiga (rebaixamento do pico cardíaco) é, portanto, um fenômeno da **terceira sessão** — coerente com a precipitação do humor no mesmo Dia 7.

---

## 5. Síntese

O post hoc corrigido para multiplicidade cristaliza três padrões:

1. **Precocidade diferencial** — fadiga física e vigor diferem do baseline **já no D2** e em todos os dias; o TMD só no **D7**. A escolha do marcador determina quão cedo o monitoramento "enxerga" a fadiga.
2. **Precipitação final** — o maior contraste de humor é **D5 → D7**, e a queda da FC de pico ocorre em **S2 → S3**: o custo do microciclo dispara na última sessão, não se acumula linearmente.
3. **Gangorra real** — o contraste significativo **D4 → D5** na fadiga física confirma alívio parcial no meio da semana, antes da subida final.

Estes resultados reforçam, com comparações múltiplas controladas, a recomendação central: monitorar a **tendência** (com a fadiga física como sentinela precoce), atento à **precipitação do fim do microciclo**.
