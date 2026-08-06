# Análise estatística consolidada — Monitoramento do humor e da carga num microciclo de choque de HIIT (handebol de elite, 21–28/04/2024)

> Documento-síntese da análise estatística do estudo. Todos os valores foram computados de forma independente em Python (numpy, scipy, statsmodels) sobre as bases brutas (27 atletas, 456 observações) e reproduzem o relatório original. Atletas anonimizados (A01–A27).

---

## 1. Abordagem estatística

**Delineamento.** Estudo observacional longitudinal, medidas repetidas intraindividuais (observações ⊂ dias ⊂ atletas), microciclo de sete dias com três sessões de HIIT (dias 2, 4, 7). Nível de significância α = 0,05; software Python 3 (pandas, numpy, scipy, statsmodels). Dada a estrutura aninhada, a unidade amostral para os contrastes é **o atleta** (agregação por atleta), corrigindo a pseudorreplicação.

**Teste de pressupostos (normalidade).** Shapiro–Wilk (com assimetria/curtose) em dois níveis: distribuição bruta e escores de mudança por atleta.
- **Distribuição:** 14/18 variáveis **não normais** — todas as de humor/bem-estar (Shapiro *p* de 3×10⁻⁴ a 3×10⁻³⁵). Normais apenas: velocidade, distância, T-CAR PV, CMJ.
- **Mudança (D7−D1) por atleta:** eixo energia–fadiga aproximadamente normal; subescalas negativas não normais.

**Rota adotada — NÃO PARAMÉTRICA para humor/bem-estar:** descritivas por **mediana (IQR)**; associações por **Spearman (ρ)** e correlação de medidas repetidas (**rmcorr**); contrastes por **Wilcoxon/Mann–Whitney**; comparação de grupos por **Kruskal–Wallis**; multivariada por **PERMANOVA** (permutação restrita ao atleta); intervalos por **bootstrap**; e, para qualificar a ausência de efeito, **fatores de Bayes** e teste de equivalência (ROPE). Variáveis contínuas normais (aptidão/antropometria) admitem via paramétrica.

---

## 2. Estatística descritiva (mediana [IQR]; % piso)

| Variável | Mediana [IQR] | Assimetria | % piso | Normal? |
|---|---|---|---|---|
| Vigor | 6 [4] | 0,03 | 8,6 | não |
| Fadiga (BRUMS) | 5 [5] | 0,59 | 7,7 | não |
| Fadiga física (0–10) | 6 [3] | −0,37 | 0,7 | não |
| PTH/TMD | 2 [10] | 1,48 | 21,9 | não |
| Tensão | 1 [2] | 1,43 | 49,6 | não |
| Depressão | 0 [1] | 3,63 | 67,1 | não |
| Raiva | 0 [2] | 2,07 | 59,6 | não |
| Confusão | 0 [0] | 3,73 | 80,5 | não |

As subescalas negativas concentram-se no piso (50–80% no zero) — o que fundamenta a via não paramétrica e antecipa sua baixa responsividade.

---

## 3. Confiabilidade e estrutura (psicometria)

- **Consistência interna** (α; ω): boa para Fadiga (0,80; 0,87), Depressão (0,85), Raiva (0,87); frágil para **Tensão (α = 0,43)** por efeito piso (não defeito de construto — ω ordinal ≈ 0,79).
- **Adequação fatorial:** KMO = 0,835; Bartlett χ²(276) = 5.228; *p* < 0,001. Estrutura de **6 fatores** (análise paralela; RMSR 1→6 fatores: 0,131 → 0,028).
- **Decomposição de variância (traço/dia/estado):** o humor é dominantemente **traço** (ICC de atleta 0,26–0,67).
- **Precisão da decisão:** 1 coleta rende dependabilidade Φ = 0,57; **≥ 3 coletas → Φ ≥ 0,80** (ICC(1,7) = 0,76–0,94).
- **Lei do piso:** |dz| da resposta aguda = 0,588 − 0,0063·(%piso); **ρ = −0,92; R² = 0,85** — o efeito piso prediz a não-responsividade.

---

## 4. Efeito do dia (modelo misto + tendência polinomial)

Modelo linear misto (intercepto aleatório de atleta), correção FDR entre variáveis.

| Variável | *F* (aprox.) | *p* (FDR) | ICC atleta |
|---|---|---|---|
| Fadiga física | 18,9 | < 0,001 | 0,46 |
| Vigor | 8,4 | < 0,001 | 0,57 |
| Fadiga (BRUMS) | 8,2 | < 0,001 | 0,59 |
| PTH/TMD | 5,1 | < 0,001 | 0,59 |
| Depressão | 1,6 | 0,150 (n.s.) | 0,68 |

**Forma da trajetória (polinômios ortogonais no misto):** componentes **linear + cúbica significativas** em todas as variáveis (quadrática ausente); **crescimento cúbico** vence por AIC/LRT (cúbico vs quadrático *p* < 0,001). A trajetória tem três fases: subida → alívio no meio da semana → **precipitação no Dia 7**. Derivadas: velocidade máxima no Dia 7; aceleração muda de sinal nos dias 5–6.

---

## 5. Resposta aguda pré→pós (agregada por atleta, Wilcoxon + dz, FDR)

| Variável | Δ | dz [IC 95% bootstrap] | *p* (FDR) | |
|---|---|---|---|---|
| Fadiga física | +1,81 | +0,97 [+0,69; +1,37] | < 0,001 | ✔ |
| Fadiga (BRUMS) | +1,76 | +0,59 [+0,36; +0,88] | 0,019 | ✔ |
| PTH/TMD | +3,14 | +0,57 [+0,29; +0,89] | 0,019 | ✔ |
| Vigor | −0,80 | −0,45 [−0,80; −0,12] | 0,061 | (limítrofe) |
| Subescalas negativas | — | |dz| ≤ 0,40 | n.s. | ✗ |

Só o eixo energia–fadiga sobrevive à correção. **Post-hoc por dia (Wilcoxon):** a fadiga física responde pré→pós em **todos** os dias de treino (dz 0,47–0,97).

---

## 6. Post-hoc entre dias (EMM do misto; Tukey/Holm)

- **Fadiga física:** 12/21 pares significativos; difere do baseline **desde o D2**.
- **Vigor:** difere do baseline em **todos** os dias.
- **PTH/TMD:** só o **D7** se distingue; **maior contraste D5→D7 (Δ = +5,77; p < 0,001)** — a precipitação.
- **Carga interna (S1/S2/S3):** queda da FC de pico concentrada em **S2→S3** (Δ = −3,04; dz = −0,89; p = 0,003).

---

## 7. Confirmação multivariada

| Teste | Estatística | *p* |
|---|---|---|
| PERMANOVA — pré vs pós (permutação restrita ao atleta) | pseudo-*F* = 1,75 | 0,003 |
| PERMANOVA — HIIT vs não-HIIT | pseudo-*F* = 2,71 | 0,008 |
| Hotelling T² — 6 subescalas | *F*(6,21) = 2,52 | 0,054 (limítrofe) |
| Hotelling T² — eixo energia–fadiga | *F*(2,25) = 5,59 | **0,010** |
| **Modelo misto multivariado** — LRT do efeito do dia | χ²(4) = 118,9 | **≈ 9×10⁻²⁵** |

**Estrutura entre-atletas** (efeitos aleatórios não estruturados): fadiga↔vigor = **−0,65**; fadiga↔TMD = +0,86 → **eixo bipolar energia↔fadiga** como dimensão de traço. Tamanho de efeito multivariado (D de Mahalanobis) D1→D7 = 1,55 [1,24; 4,25].

---

## 8. Análise bayesiana e equivalência

Fatores de Bayes JZS sobre os deltas agregados por atleta:
- **Fadiga física** BF₁₀ ≈ 2.444 (extrema), PTH 22,4 (forte), Fadiga 11,3 (forte), Vigor 5,9 (moderada) → **evidência para efeito**.
- **Confusão** BF₁₀ ≈ 0,23 e 93% do posterior na ROPE → **evidência para equivalência prática** (ausência de efeito, não só p>0,05).
- Tensão/Depressão/Raiva/Fadiga mental: indeterminadas (falta de poder + piso).

---

## 9. Discriminância (ROC) e o eixo do sinal

| Tarefa | Melhor variável | AUC [IC 95%] |
|---|---|---|
| Discriminar **sessão de HIIT** | Fadiga física | 0,54 [0,48; 0,60] |
| Discriminar **acúmulo (D7 vs D1)** | Fadiga física | **0,86** [0,77; 0,92] |
| Discriminar **dia de fadiga alta** | Fadiga (BRUMS) | **0,84** [0,80; 0,88] |
| Autoavaliação física (item único) → dia de fadiga alta | — | 0,83 |

**O sinal está na tendência (acúmulo), não na sessão isolada.**

---

## 10. Carga interna e externa

- **Externa (derivada do T-CAR; 4×4 min a 104% PV):** velocidade média **16,5 ± 1,2 km/h**; distância **2.929 ± 207 m/sessão**; total **≈ 8,8 km**. Prescrição relativa ⇒ carga externa **fixa** entre sessões.
- **Interna (S1→S3):** FC de pico **184 → 181 bpm** (Friedman *p* < 0,001), **TRIMP cardíaco cai** (50,6 → 46,4) enquanto **PSE/session-RPE sobem** (196 → 208). **Dissociação:** o TRIMP subestima a carga sob fadiga; o session-RPE é o marcador interno fiel.
- **Acoplamento intra-atleta (rmcorr):** FC de pico × vigor = +0,57; × TMD = −0,48; × fadiga física = −0,51.
- **TQR (recuperação):** responde ao microciclo (agudo dz = −0,64; acoplado ao eixo, ρ = −0,65). **PSS (estresse)** não rastreia o microciclo (traço).

---

## 11. Moderação e segmentação (não paramétrica)

- **Aptidão prévia (T-CAR PV) × fadiga da semana:** ρ = **−0,54** (*p* = 0,005) — o mais apto fadiga menos; robusto ao **escalonamento alométrico** (PV/massa^0,5: ρ = −0,52).
- **Logística:** P(fadiga física ≥ 8) — OR/dia = 1,31 (*p* < 0,001); OR/PV = 0,50 (*p* < 0,001).
- **Kruskal–Wallis (D7, por tercil de aptidão):** diferenças **não** significativas com n≈8–10/grupo (ex.: fadiga física H = 4,46; *p* = 0,107), embora o tamanho de efeito entre extremos seja grande (**g = −1,18** no D7) — resultado nulo por baixa potência, não por ausência de tendência.

---

## 12. Conclusão estatística

1. **Pressupostos:** dados de humor/bem-estar não normais → via **não paramétrica** (a paramétrica não é reportada onde a variável é não normal).
2. **Fenômeno:** o humor deteriora-se de forma **não linear (cúbica)**, precipitando-se no **Dia 7**; a mudança concentra-se no **eixo energia–fadiga**, com a **fadiga física** como marcador mais precoce, sensível e confiável.
3. **HIIT:** efeito de **acúmulo** (só o D7 difere; interação Condição×Momento n.s.), não de choque agudo isolado; confundido com volume (não é dose-resposta).
4. **Carga:** externa fixa; interna revela fadiga (FC↓, PSE↑); **session-RPE > TRIMP** sob fadiga.
5. **Medida:** variância dominada por traço ⇒ decisão individual exige **médias de ≥ 3–7 coletas** e limiares por MDC; a "não-resposta" das negativas é **efeito piso** (BF favorável ao nulo na Confusão), não ausência de fenômeno.
6. **Robustez:** convergência entre modelos mistos, permutação (PERMANOVA), bayesiano, bootstrap e ROC sustenta as conclusões independentemente do método.

---

*Reprodutibilidade: `scripts/analise/` (a1_psych, a2_dynamics, a3_within, mvmixed, polynomial, robust, posthoc, normality, loadprofile). App interativo: `Artigos/App_Analitico.html`. Relatórios detalhados: `Artigos/*.md`.*
