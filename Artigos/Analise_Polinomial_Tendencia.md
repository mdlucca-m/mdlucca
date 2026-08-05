# Análise polinomial da trajetória — tendências ortogonais, crescimento multinível e contrastes (microciclo 21–28/04/2024)

> **Escopo.** Semana de 21–27/04. Decomposição do efeito do dia em **polinômios ortogonais** (até 6ª ordem) no modelo misto; **modelos de crescimento polinomial multinível** com inclinações aleatórias (comparados por AIC e LRT); e contrastes complementares (HIIT × técnico-tático par a par; pré→pós por dia). Reprodutibilidade: `../scripts/analise/polynomial.py`. Atletas anonimizados.

---

## 1. Análise de tendência por polinômios ortogonais

Decompondo o efeito do dia (7 níveis) em componentes ortogonais, testa-se estatisticamente **a forma** da trajetória. O resultado é consistente entre as variáveis: as componentes **linear e cúbica são significativas**, a **quadrática em geral não** (Tabela 1). A componente **linear** capta a deterioração global da semana; a **cúbica** capta o padrão em **gangorra com precipitação** (subida inicial, alívio no meio, disparo final) — exatamente o que as derivadas e o post hoc D5→D7 haviam mostrado.

**Tabela 1.** Coeficientes das tendências ortogonais (β; modelo misto). *** p<0,001, ** p<0,01, * p<0,05.

| Variável | Linear | Quadrática | Cúbica | Quártica | Componentes significativas |
|---|---|---|---|---|---|
| **Fadiga física** | +2,13*** | −0,39 | **+1,25*** | +0,45* | linear, cúbica (quárt., sext.) |
| **Vigor** | −1,77*** | +0,63* | **−1,17*** | −0,19 | linear, quadrática, cúbica |
| **Fadiga (BRUMS)** | +2,08*** | +0,03 | **+1,34*** | +0,37 | linear, cúbica |
| **TMD** | +2,91*** | +1,61 | **+2,83*** | +0,33 | linear, cúbica (sext.) |

**Leitura.** A trajetória do humor no microciclo **não é linear**: sobre a tendência descendente global (linear) sobrepõe-se uma **estrutura cúbica** significativa em todas as variáveis — a assinatura da recuperação parcial do meio de semana seguida da precipitação no Dia 7. A ausência de componente quadrática (exceto vigor) descarta uma simples aceleração/curva em U e confirma a natureza **em três fases** (subida–alívio–disparo) da dinâmica.

## 2. Modelos de crescimento polinomial multinível

Ajustando modelos de crescimento com **inclinações aleatórias por atleta** e comparando ordens (linear/quadrático/cúbico), o **cúbico vence por AIC** para todas as variáveis, e o teste de razão de verossimilhança **cúbico vs quadrático é altamente significativo** (Tabela 2). Ou seja: a não-linearidade cúbica **persiste** mesmo depois de acomodar a heterogeneidade individual de trajetória — não é artefato de médias de grupo.

**Tabela 2.** Comparação de ordens de crescimento (AIC; LRT; coef. cúbico t³).

| Variável | AIC linear | AIC quadr. | AIC cúbico | LRT cúbico vs quadr. | Coef. t³ |
|---|---|---|---|---|---|
| TMD | 3026,9 | 3024,0 | **3006,6** | χ² = 19,5; *p* < 0,001 | +0,20 (*p* < 0,001) |
| Fadiga física | 1866,1 | 1865,6 | **1833,7** | χ² = 34,0; *p* < 0,001 | +0,08 (*p* < 0,001) |
| Vigor | 2055,7 | 2053,6 | **2035,2** | χ² = 20,4; *p* < 0,001 | −0,08 (*p* < 0,001) |

O termo cúbico é significativo (*p* < 0,001) em todos os casos; o quadrático, marginal. A trajetória é, portanto, **cúbica** — a formulação polinomial correta para modelar o humor neste microciclo é `y ~ poly(dia, 3) + (poly(dia,1) | atleta)`.

## 3. Contrastes complementares

### 3a. HIIT × técnico-tático (pares de dias, Holm)

Os pares HIIT–TT significativos concentram-se **quase exclusivamente no Dia 7** (Tabela 3): D7 difere dos dias técnico-táticos em fadiga física (+1,6 a +1,8) e vigor (−1,4 a −1,6); os primeiros dias de HIIT (D2, D4) **não** diferem dos TT. Isso reforça que a "diferença do HIIT" no nível do dia é, na verdade, **efeito de acúmulo** que se manifesta na terceira sessão — não uma pesagem intrínseca de cada sessão de HIIT.

**Tabela 3.** Pares HIIT–TT significativos (Holm p < 0,05).

| Variável | Pares sig. (de 9) | Quais |
|---|---|---|
| Fadiga física | 3 | D7×D3, D7×D5, D7×D6 |
| Vigor | 3 | D7×D3, D7×D5, D7×D6 |
| TMD | 1 | D7×D5 (Δ = +6,2) |

### 3b. Pré→pós dentro de cada dia (agregado por atleta, FDR)

A **fadiga física responde agudamente em TODOS os dias de treino** (dz = 0,47–0,97; todos sobrevivem ao FDR) — é o marcador de resposta de sessão mais consistente. O TMD só responde no D6, e o vigor não sobrevive ao FDR em nenhum dia isolado (Tabela 4).

**Tabela 4.** Resposta aguda pré→pós por dia (dz; * = FDR < 0,05).

| Variável | D2 | D3 | D4 | D5 | D6 | D7 |
|---|---|---|---|---|---|---|
| **Fadiga física** | +0,97* | +0,47* | +0,79* | +0,73* | +0,51* | +0,73* |
| TMD | +0,31 | +0,16 | +0,50 | +0,17 | +0,75* | +0,53 |
| Vigor | −0,39 | −0,22 | −0,26 | −0,12 | −0,64 | −0,20 |

---

## 4. Síntese

1. **A forma é cúbica, não linear** — as tendências ortogonais mostram componentes **linear + cúbica** significativas em todas as variáveis (quadrática ausente), e os modelos de crescimento multinível confirmam o **cúbico** por AIC e LRT (*p* < 0,001), mesmo com inclinações aleatórias. A dinâmica tem três fases: subida inicial, alívio no meio da semana, precipitação no Dia 7.
2. **O "efeito HIIT" do nível do dia é acúmulo** — os contrastes HIIT–TT só se acendem no **D7**, não nas primeiras sessões de HIIT.
3. **A fadiga física é o marcador de sessão universal** — responde pré→pós em **todos** os dias de treino, ao contrário do TMD e do vigor.

A recomendação de modelagem que emerge: para descrever o humor neste tipo de microciclo, usar **crescimento polinomial cúbico multinível** (fixo até 3ª ordem, aleatório na inclinação linear), e monitorar a **fadiga física** como variável de resposta aguda por excelência.
