# Artigo 2 — Dinâmica agudo–crônica do humor sob microciclo de choque de HIIT no handebol: resposta da sessão, acúmulo semanal e corroboração fisiológica

> **Nota de proveniência.** Nova análise dos dados do projeto *Handebol São José 2024* (27 atletas, 456 observações; três sessões de HIIT em dias 2, 4 e 7), reexecutada de forma independente em Python. A inferência respeita a estrutura de medidas repetidas (modelos mistos, agregação por atleta, permutação restrita ao indivíduo). Atletas anonimizados.

---

## Resumo

**Objetivo.** Separar, num microciclo pré-competitivo de sete dias com três sessões de HIIT, a **resposta aguda** (da sessão) do **acúmulo crônico** (progressão semanal) do humor, e corroborá-los com a carga interna e a adaptação física. **Métodos.** Efeito do dia por modelo linear misto (intercepto aleatório de atleta); resposta aguda pré→pós **agregada por atleta** (corrigindo a pseudorreplicação), com dz, IC por *bootstrap* de *cluster* e correção FDR; confirmação multivariada por Hotelling T² pareado e PERMANOVA com permutação restrita ao atleta; contraste HIIT vs técnico-tático no nível do dia; carga interna (FC de pico, PSE) e adaptação (T-CAR, CMJ). **Resultados.** O humor deteriorou ao longo da semana, com pico de perturbação no **Dia 7** (efeito do dia máximo na fadiga física, *F* ≈ 18,9; vigor e fadiga *F* ≈ 8,2–8,4). A resposta aguda concentrou-se no eixo energia–fadiga (fadiga física dz = **+0,97**; fadiga +0,59; TMD +0,57; vigor −0,45), com as **quatro subescalas negativas não significativas** após correção. O perfil multivariado deslocou-se (Hotelling *F*(6,21) = 2,52; *p* = 0,054, limítrofe; eixo energia–fadiga *F*(2,25) = 5,59; *p* = 0,010; PERMANOVA pré→pós *p* = 0,003). No nível do dia, os dias de HIIT foram mais pesados (TMD +1,90; vigor −0,39), mas a mudança aguda **não** distinguiu HIIT de treino técnico-tático — sinal de **acúmulo**, não de choque agudo isolado. A carga interna corroborou: FC de pico decrescente (**184 → 181 bpm** entre a 1ª e a 3ª sessão) com esforço percebido mantido — assinatura de fadiga acumulada dentro da semana. A aptidão prévia (covariável de base, avaliada imediatamente antes da semana) moderou a resposta: o atleta mais apto fadigou menos (T-CAR PV × fadiga física da semana *ρ* = −0,54; *p* = 0,005). **Conclusão.** No handebol de elite, o HIIT deteriora o humor por **acúmulo semanal no eixo energia–fadiga**, não por um choque agudo qualitativamente distinto do treino comum; a vulnerabilidade associa-se a um **traço de aptidão** prévio.

**Palavras-chave:** HIIT; monitoramento de carga; modelos mistos; PERMANOVA; Fitness–Fadiga; handebol.

---

## 1. Introdução

Separar a resposta aguda de uma sessão do acúmulo de fadiga ao longo de uma semana é um problema central — e parcialmente não resolvido — do monitoramento em esportes coletivos. A dificuldade é tanto de desenho (é preciso medir intensivamente, pré e pós, ao longo de vários dias) quanto de análise: medidas dentro de dias, dentro de atletas, geram dependência que a ANOVA de medidas repetidas e a regressão simples não acomodam. Tratar as observações como independentes (pseudorreplicação) infla artificialmente a significância. Este estudo aplica a um microciclo real de handebol — com três sessões de HIIT concentradas — um conjunto de métodos que respeitam a hierarquia dos dados (modelos mistos, agregação por atleta, permutação restrita ao indivíduo) e triangula frequentista, multivariado e fisiológico para responder: **o HIIT piora o humor por um choque agudo próprio, ou por acúmulo ao longo da semana?**

## 2. Métodos

**Desenho.** Observacional longitudinal, medidas repetidas intraindividuais, condições ecológicas. Microciclo de sete dias (21–27/04/2024): Dia 1 repouso/baseline; dias 2, 4 e 7 com HIIT + técnico-tático; dias 3, 5 e 6 técnico-tático + jogos. *Nota estrutural:* os dias de HIIT são também os de menor volume — modalidade e volume permanecem confundidos.

**Variáveis.** BRUMS (seis subescalas + TMD), fadiga física e mental (0–10). Carga interna nas três sessões de HIIT (22, 24, 27/04): frequência cardíaca (pré/pós de cada série) e PSE. **Escopo temporal:** todas as análises restringem-se à janela de 21–28/04/2024; a velocidade de pico do teste de Carminatti (T-CAR) avaliada em 15/04 entra **apenas como covariável de base** entre atletas, não como desfecho de adaptação.

**Análise.** (1) *Efeito do dia*: modelo linear misto `y ~ C(dia) + (1|atleta)`, teste omnibus de Wald sobre os termos de dia, ICC de atleta, correção FDR entre variáveis. (2) *Resposta aguda*: para cada dia de treino, Δ = última − primeira coleta; deltas **agregados por atleta** (n = 27) antes do teste (t pareado, Wilcoxon); dz com IC 95% por *bootstrap* de *cluster* (2.000 reamostragens de atletas inteiros); FDR. (3) *Multivariada*: Hotelling T² pareado sobre o vetor de deltas nas seis subescalas, e no eixo energia–fadiga; PERMANOVA (distância euclidiana, variáveis padronizadas) com **permutação restrita ao atleta** (3.000 permutações). (4) *HIIT vs técnico-tático*: médias por atleta nos dias de treino, contraste pareado. (5) *Carga interna e adaptação*: comportamento por sessão; moderação da resposta pela aptidão prévia (Spearman entre atletas).

## 3. Resultados

### 3.1 Trajetória semanal: deterioração por acúmulo

O humor deteriorou-se ao longo da semana, com pico de perturbação no **Dia 7** (Tabela 1). O efeito do dia foi máximo na **fadiga física** e concentrou-se no eixo energia–fadiga; a Depressão não variou significativamente (efeito piso). Os ICC de atleta (0,30–0,71) confirmam forte componente de traço — o efeito do dia é **intra-sujeito**.

**Tabela 1.** Efeito do dia (modelo misto; FDR).

| Variável | *F* (aprox.) | *p* (FDR) | ICC atleta |
|---|---|---|---|
| Fadiga física | 18,9 | < 0,001 | 0,46 |
| Vigor | 8,4 | < 0,001 | 0,57 |
| Fadiga (BRUMS) | 8,2 | < 0,001 | 0,59 |
| TMD | 5,1 | < 0,001 | 0,59 |
| Raiva | 3,8 | 0,001 | 0,30 |
| Tensão | 3,7 | 0,002 | 0,70 |
| Confusão | 3,5 | 0,002 | 0,38 |
| Fadiga mental | 3,4 | 0,002 | 0,71 |
| Depressão | 1,6 | 0,150 (n.s.) | 0,68 |

As médias diárias desenham um **dente de serra** com picos nos dias de HIIT (2, 4, 7) e alívio parcial nos técnico-táticos intercalados, convergindo para o pior estado no Dia 7 (TMD: 2,1 → 4,7 → 4,5 → 5,7 → 1,8 → 4,5 → **8,0**; Vigor 7,5 → … → **4,7**; fadiga física 4,3 → … → **7,6**).

### 3.2 Resposta aguda: específica do eixo energia–fadiga

Corrigida a pseudorreplicação, apenas o eixo energia–fadiga sobrevive à correção FDR (Tabela 2). As quatro subescalas negativas não respondem — efeito piso (ver Artigo 1).

**Tabela 2.** Resposta aguda pré→pós (agregada por atleta, dias 2–7).

| Variável | Δ | dz [IC 95%] | *p* (FDR) | |
|---|---|---|---|---|
| Fadiga física | +1,81 | **+0,97** [+0,69; +1,37] | < 0,001 | ✔ |
| Fadiga (BRUMS) | +1,76 | +0,59 [+0,36; +0,88] | 0,019 | ✔ |
| TMD | +3,14 | +0,57 [+0,29; +0,89] | 0,019 | ✔ |
| Vigor | −0,80 | −0,45 [−0,80; −0,12] | 0,061 | (limítrofe) |
| Tensão | +0,27 | +0,40 [+0,04; +0,72] | 0,090 | n.s. |
| Fadiga mental | +0,49 | +0,33 [−0,02; +0,67] | 0,151 | n.s. |
| Depressão | +0,14 | +0,18 | 0,468 | n.s. |
| Raiva | +0,19 | +0,13 | 0,567 | n.s. |
| Confusão | −0,03 | −0,06 | 0,757 | n.s. |

### 3.3 Confirmação multivariada

O deslocamento do perfil de humor foi confirmado por duas vias que respeitam as medidas repetidas (Tabela 3). O Hotelling sobre as seis subescalas fica **no limiar** (*p* = 0,054): as quatro dimensões negativas não-responsivas acrescentam ruído que dilui o teste global. Quando restrito ao **eixo energia–fadiga**, o efeito é robusto (*p* = 0,010). A PERMANOVA, livre de distribuição, confirma o deslocamento pré→pós (*p* = 0,003) e a diferença entre dias de HIIT e sem HIIT (*p* = 0,008).

**Tabela 3.** Testes multivariados (agregados/permutados por atleta).

| Teste | Estatística | *p* | Efeito |
|---|---|---|---|
| Hotelling T² — 6 subescalas | *F*(6,21) = 2,52 | 0,054 | D = 0,83 |
| Hotelling T² — eixo energia–fadiga | *F*(2,25) = 5,59 | **0,010** | D = 0,66 |
| PERMANOVA — pré vs pós | pseudo-*F* = 1,75 | 0,003 | — |
| PERMANOVA — HIIT vs não-HIIT | pseudo-*F* = 2,71 | 0,008 | — |

### 3.4 HIIT versus técnico-tático: nível do dia ≠ resposta aguda

Duas perguntas distintas devem ser separadas (Tabela 4). **No nível do dia**, os dias de HIIT são mais pesados — maior TMD (+1,90) e fadiga, menor vigor (−0,39). **Na resposta aguda intra-sessão**, porém, a mudança pré→pós **não** distingue HIIT de treino técnico-tático (intervalos de dz sobrepostos). As duas leituras não se contradizem: descrevem, respectivamente, o *nível* do dia e a *variação* da sessão. Como HIIT e volume estão confundidos, o efeito **não** é dose-resposta.

**Tabela 4.** HIIT vs técnico-tático (nível do dia, pareado por atleta).

| Variável | HIIT | Sem HIIT | Δ | dz | *p* |
|---|---|---|---|---|---|
| TMD | 5,26 | 3,36 | +1,90 | +0,48 | 0,023 |
| Fadiga (BRUMS) | 5,79 | 5,27 | +0,52 | +0,40 | 0,057 |
| Vigor | 5,16 | 5,54 | −0,39 | −0,39 | 0,064 |
| Fadiga física | 6,25 | 6,03 | +0,22 | +0,18 | 0,382 |

### 3.5 Corroboração fisiológica dentro da semana

A carga interna corrobora a leitura de acúmulo: entre a primeira e a terceira sessão de HIIT (22 → 27/04), a **FC de pico caiu (183,8 → 180,8 bpm)** enquanto o esforço percebido se manteve alto e estável — o atleta entrega esforço máximo com um pico cardíaco cada vez menor, assinatura clássica de fadiga acumulada, aqui documentada **dentro da própria semana**. A aptidão prévia (covariável de base, avaliada em 15/04) **modera** essa resposta: o atleta com maior velocidade de pico do T-CAR fadigou menos ao longo da semana (T-CAR PV × fadiga física média *ρ* = −0,54; *p* = 0,005; × TMD *ρ* = −0,28; n.s.). Como o estímulo foi prescrito a 104% da PV individual, o custo interno é relativo e equalizado: correr mais rápido em absoluto não implica fadigar mais, e a vulnerabilidade à fadiga da semana associa-se a um traço de aptidão prévio. *Nota de escopo:* a magnitude da adaptação aeróbia/neuromuscular ao longo do mesociclo (ganhos de T-CAR e CMJ) situa-se fora da janela de 21–28/04 e, por isso, não é objeto deste artigo.

## 4. Discussão

O achado mais informativo é a dissociação entre **nível do dia** e **resposta aguda**. Que os dias de HIIT sejam mais pesados, mas que a variação pré→pós não os distinga do treino técnico-tático, indica que o handebol — modalidade intermitente de alta intensidade — impõe, mesmo no treino tático, um estresse agudo que se iguala perceptualmente ao do HIIT. O prejuízo do HIIT emerge, portanto, como um **pedágio cumulativo**: ao concentrar três sessões intensas no microciclo, ele impede a restauração completa da homeostase entre os dias, e o saldo se expressa em fadiga residual e queda de vigor no Dia 7. A recuperação noturna é real, mas incompleta — o piso de fadiga sobe e o teto de vigor desce a cada ciclo.

A convergência das vias sustenta essa leitura: os quatro efeitos que sobrevivem à correção FDR são precisamente os do eixo energia–fadiga; o teste multivariado é significativo justamente nesse eixo; e o marcador fisiológico (FC de pico) move-se em espelho com o vigor, ao passo que a PSE acompanha a perturbação. A "estabilidade" das emoções negativas em dias de HIIT **não** deve tranquilizar a comissão técnica — é artefato do piso (Artigo 1), não ausência de estresse.

**Limitações.** Confundimento perfeito volume × modalidade (o efeito não é dose-resposta); "pré/pós" definido como primeira/última coleta do dia (mistura efeito de sessão e de hora do dia); amostra única, masculina, um microciclo; e a moderação entre atletas (n = 27) é exploratória e de baixa potência.

## 5. Conclusão

No handebol de elite, o HIIT deteriora o humor por **acúmulo semanal**, concentrado no eixo energia–fadiga, e não por um choque agudo qualitativamente distinto do treino comum. O sinal é mensurável, fisiologicamente corroborado e concentrado nas dimensões bem medidas do BRUMS. A bandeira de alerta do monitoramento deve considerar a **tendência ao longo do microciclo** — não a variação de uma única sessão — e reconhecer que a vulnerabilidade à fadiga é, em boa parte, um **traço de aptidão** identificável antes do bloco.
