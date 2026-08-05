# Análise dirigida — Baseline, carga interna e externa das sessões de HIIT e variáveis psicológicas (microciclo 21–28/04/2024)

> **Escopo.** Semana de 21–27/04/2024 (baseline em 21/04; HIIT em 22, 24 e 27/04). Reanálise independente em Python sobre as bases brutas. Protocolo de HIIT: **4 séries × 4 min a 104% da velocidade de pico (PV) do T-CAR**, com esforço intermitente (12 s corrida / 6 s pausa; ≈ 13,3 repetições por bloco). Atletas anonimizados (A01–A27).

---

## 1. Parâmetros e definições

| Bloco | Parâmetros analisados |
|---|---|
| **A. Baseline (21/04)** | Perfil BRUMS, fadiga física/mental, TQR, Epworth, PSS, perfil iceberg |
| **B. Carga interna (HIIT)** | FC de pico, FC média, PSE (session-RPE), TRIMP (Banister) |
| **C. Carga externa (HIIT)** | Velocidade média (= 104% da PV do T-CAR) e distância percorrida, derivadas do protocolo |
| **D. Variáveis psicológicas (dias de HIIT)** | Trajetória do humor e da fadiga nas três sessões |

A carga externa foi **derivada do T-CAR**: a velocidade de trabalho é 104% da PV individual; a distância percorrida decorre do protocolo (12 s de corrida por repetição × 13,3 repetições/bloco × 4 blocos = 640 s de corrida efetiva por sessão), com fator ida-e-volta 2 no vaivém.

---

## 2. A — Baseline (21/04, dia de repouso/linha de base)

O ponto de partida é o de um atleta **fresco e saudável**: vigor alto sobre dimensões negativas baixas (perfil iceberg em 93%), boa recuperação percebida (TQR alto), baixa sonolência e estresse moderado.

**Tabela A.** Estado psicológico e de recuperação no baseline (n = 42 obs, 27 atletas).

| Variável | Baseline (21/04) |
|---|---|
| Vigor | 7,52 ± 3,60 |
| Fadiga (BRUMS) | 3,74 ± 3,19 |
| Fadiga física (0–10) | 4,26 ± 2,22 |
| Fadiga mental (0–10) | 4,81 ± 2,47 |
| TMD (perturbação total) | 2,05 |
| Tensão / Depressão / Raiva / Confusão | 1,79 / 1,14 / 1,95 / 0,95 |
| **Perfil iceberg** | **93%** |
| TQR (recuperação 6–20) | 13,4 |
| Epworth (sonolência 0–18) | 8,1 |
| PSS (estresse) | 22,8 |

Este é o referencial contra o qual se lê toda a deterioração da semana.

---

## 3. C — Carga externa das sessões de HIIT (derivada do T-CAR)

Como a prescrição é **relativa** (104% da PV individual), a carga externa é, por construção, **idêntica nas três sessões** de cada atleta — o que a torna o "controle" perfeito para revelar a fadiga no lado interno.

**Tabela C.** Carga externa por atleta (n = 26 com dado; média ± amplitude).

| Parâmetro | Valor |
|---|---|
| **Velocidade média de trabalho** (= 104% PV) | **16,5 km/h** (4,58 m/s) [14,4–19,2] |
| PV do T-CAR implicada (vel ÷ 1,04) | 15,8 km/h |
| Distância por repetição de esforço (12 s) | 55 m |
| Distância por bloco (4 min) | 732 m |
| **Distância por sessão** | **≈ 2.929 m** [2.560–3.413] |
| **Distância total (3 sessões)** | **≈ 8.788 m (~8,8 km)** |

A amplitude de distância (2.560–3.413 m) reflete a aptidão: o atleta mais apto corre a 104% de uma PV maior e, portanto, cobre ~33% mais distância — mas ao **mesmo custo interno relativo**.

---

## 4. B — Carga interna das sessões de HIIT

Com a carga externa fixa, a carga interna revela a **assinatura da fadiga acumulada** ao longo da semana (Tabela B): a FC de pico e a FC média **declinam** sessão a sessão, enquanto a percepção de esforço **sobe**.

**Tabela B.** Carga interna por sessão de HIIT (S1 = 22/04, S2 = 24/04, S3 = 27/04).

| Sessão | FC média (bpm) | FC de pico (bpm) | PSE (média séries) | TRIMP (Banister) | session-RPE |
|---|---|---|---|---|---|
| S1 | 180,4 | 183,8 | 7,5 | 50,6 | 196 |
| S2 | 179,3 | 183,3 | 7,5 | 49,3 | 194 |
| S3 | 176,5 | **180,8** | **8,0** | **46,4** | **208** |
| **Tendência** | ↓ | ↓ (−3,0) | ↑ | ↓ | ↑ |

*TRIMP-Banister estimado com FC de repouso = 60, FC máxima = 195 e 16 min de trabalho; session-RPE = PSE × duração (~26 min). A PSE atinge 9–10 na última série de cada sessão.*

**Dissociação metodológica crítica.** A carga externa é constante e o esforço percebido cresce, mas o **TRIMP cardíaco cai** (50,6 → 46,4) — não porque o atleta trabalhe menos, mas porque a FC de pico é **suprimida** sob fadiga acumulada. O TRIMP baseado em FC, portanto, **subestima** a carga ao longo do microciclo; o **session-RPE** (que sobe, 196 → 208) e a percepção de esforço são os marcadores internos fiéis nesse contexto.

---

## 5. D — Variáveis psicológicas nos dias de HIIT

Sob carga externa idêntica, o estado psicológico **deteriora-se progressivamente**, precipitando-se na terceira sessão (Tabela D).

**Tabela D.** Humor e fadiga nas três sessões de HIIT (nível do dia).

| Momento | TMD | Vigor | Fadiga (BRUMS) | Fadiga física |
|---|---|---|---|---|
| Baseline (D1) | 2,05 | 7,52 | 3,74 | 4,26 |
| S1 (D2) | 4,66 | 5,81 | 5,21 | 5,66 |
| S2 (D4) | 5,70 | 5,28 | 6,27 | 6,87 |
| S3 (D7) | **8,00** | **4,70** | **7,48** | **7,57** |

O vigor cai quase pela metade (7,5 → 4,7) e a perturbação quase quadruplica (2,1 → 8,0) do baseline à última sessão, concentrada no eixo energia–fadiga.

---

## 6. Síntese integrada

Os quatro blocos contam uma única história, com uma arquitetura de evidência limpa graças à prescrição relativa:

1. **A carga externa é o controle**: idêntica nas três sessões (104% da PV; ~2.930 m/sessão; ~8,8 km na semana).
2. **A carga interna revela a fadiga**: com o trabalho externo fixo, a FC de pico **cai** (184 → 181 bpm) e a PSE **sobe** (7,5 → 8,0; 9–10 na última série).
3. **O estado psicológico acompanha e amplifica**: partindo de um baseline saudável (iceberg 93%, TMD 2,1), o humor deteriora-se até TMD 8,0 e vigor 4,7 na terceira sessão.
4. **Lição de mensuração**: sob fadiga acumulada, o **TRIMP cardíaco subestima** a carga (queda por supressão da FC), enquanto **session-RPE e BRUMS** a capturam — a carga interna perceptual e o autorrelato de humor são, aqui, os marcadores válidos.

Em síntese: **mesmo trabalho externo, custo interno e psicológico crescente** — a definição operacional de fadiga acumulada num microciclo de choque, documentada de forma convergente entre os domínios fisiológico, perceptual e psicológico.

---

*Reprodutibilidade: `../scripts/analise/loadprofile.py` (baseline, cargas, psicológico) sobre `ext_load.csv`, `hr_series.csv`, `humor.csv`, `wellness_all.csv`. Dados identificáveis não versionados.*
