# Artigo 3 — Acoplamento psicofisiológico e resposta individual no microciclo de choque de HIIT: das três sessões à decisão no nível do atleta

> **Nota de proveniência e escopo.** Análise **restrita à semana de 21–28/04/2024** (microciclo de sete dias; três sessões de HIIT em 22, 24 e 27/04). Reexecutada de forma independente em Python. Nenhum dado fora dessa janela é usado; a aptidão prévia (T-CAR de 15/04) entra **apenas como covariável de base**. Atletas anonimizados (A01–A27).

---

## Resumo

**Objetivo.** Ir além do efeito médio de grupo e caracterizar, dentro do microciclo de choque, (i) a progressão da fadiga entre as três sessões de HIIT e seu acoplamento com a carga interna; e (ii) a resposta **individual** — quem muda de forma confiável, quanto oscila e qual o limiar de mudança real por atleta. **Métodos.** Progressão do humor entre as três sessões de HIIT (modelo misto, inclinação por sessão); carga interna por sessão (FC de pico, HRR, PSE); acoplamento intra-atleta FC×humor por correlação de medidas repetidas (rmcorr); Índice de Mudança Confiável (RCI) do Dia 1 ao Dia 7; variabilidade intra-individual (iSD, MSSD); e erro típico da medida (ETM) vs menor mudança relevante (SWC). **Resultados.** O humor deteriorou-se progressivamente entre as sessões, **precipitando-se na terceira**: a perturbação total subiu de 4,6 (S1) para 8,3 (S3), com inclinação de **+1,9/sessão** (*p* = 0,023); vigor caiu −0,7/sessão (*p* = 0,001) e fadiga física +1,0/sessão (*p* < 0,001). A carga interna revelou a assinatura de fadiga acumulada: a **FC de pico declinou (184 → 181 bpm)** enquanto a PSE se manteve. O acoplamento intra-atleta foi claro — nas sessões em que o atleta atingiu maior FC de pico (frescor), o vigor foi maior (rmcorr = **+0,57**) e a perturbação menor (**−0,48**). No nível individual, a resposta foi **heterogênea**: a fadiga física teve a mudança mais confiável (14 de 21 atletas com aumento confiável; nenhum redução), o vigor caiu de forma confiável em 7, e o TMD variou muito entre atletas (iSD = 5,5; MSSD = 48). O erro típico excedeu a menor mudança relevante em todas as escalas (fadiga física a menos ruidosa, ETM = 20%). A aptidão pré-semana moderou a fadiga (T-CAR × fadiga física *ρ* = −0,54; *p* = 0,005). **Conclusão.** O custo do microciclo de choque acumula-se e se precipita na sessão final, acoplado ao rebaixamento do pico cardíaco; a decisão de monitoramento deve ser **individual**, ancorada na fadiga física como sentinela e na mudança mínima detectável de cada atleta.

**Palavras-chave:** microciclo de choque; frequência cardíaca de pico; rmcorr; mudança confiável; monitoramento individualizado; handebol.

---

## 1. Introdução

O efeito médio de grupo — útil para descrever "o que o HIIT faz" — é insuficiente para a decisão prática, que é sempre sobre **um atleta**. Duas perguntas ficam por responder quando o estudo se encerra na média: (1) como a fadiga evolui **entre as sessões** do próprio microciclo, e se essa evolução se acopla ao custo fisiológico de cada sessão; e (2) no nível individual, quem responde de forma confiável, quanto cada atleta oscila naturalmente, e qual o limiar acima do qual uma mudança pode ser tomada como real, e não como ruído de medida. Este artigo responde a ambas **dentro da própria semana monitorada** (21–28/04/2024), sem recorrer a dados de outras fases da temporada, articulando a carga interna das três sessões de HIIT à resposta de humor e traduzindo os efeitos médios em decisões no nível do atleta.

## 2. Métodos

**Escopo.** Microciclo de sete dias (21–27/04); três sessões de HIIT (dias 2, 4 e 7 = 22, 24 e 27/04). Carga interna registrada nas três sessões (FC pré/pós por série; PSE). A aptidão pré-semana (velocidade de pico do T-CAR avaliada em 15/04) é usada **exclusivamente como covariável de base** entre atletas.

**Análise.** (1) *Progressão entre sessões*: humor por atleta em cada dia de HIIT; inclinação por ordem de sessão em modelo misto (`y ~ ordem + (1|atleta)`). (2) *Carga interna por sessão*: FC de pico, recuperação a 1 min (HRR), PSE; tendência entre S1–S3. (3) *Acoplamento intra-atleta*: correlação de medidas repetidas (rmcorr; Bakdash & Marusich) entre FC de pico/PSE e humor, com o atleta como bloco, sobre as três sessões. (4) *Mudança individual confiável*: RCI do Dia 1 ao Dia 7, com erro-padrão de medida SEM = DP·√(1−ω) e mudança mínima detectável MDC₉₅ = 1,96·√2·SEM; mudança confiável quando |z| > 1,96. (5) *Variabilidade intra-individual*: desvio-padrão intra-atleta (iSD) e diferença quadrática média sucessiva (MSSD). (6) *Utilidade da medida*: erro típico da medida (ETM) vs menor mudança relevante (SWC = 0,2·DP entre atletas).

## 3. Resultados

### 3.1 A fadiga se precipita na sessão final

O humor deteriorou-se progressivamente entre as três sessões de HIIT, com aceleração para a última (Tabela 1). A perturbação total quase dobrou de S1 para S3; vigor e fadiga física acompanharam, com inclinações significativas por sessão.

**Tabela 1.** Progressão do humor entre as três sessões de HIIT (D2 → D4 → D7).

| Variável | S1 (D2) | S2 (D4) | S3 (D7) | Inclinação/sessão | *p* |
|---|---|---|---|---|---|
| TMD (perturbação) | 4,61 | 4,76 | 8,28 | **+1,89** | 0,023 |
| Fadiga física | 5,59 | 6,53 | 7,56 | +0,99 | < 0,001 |
| Fadiga (BRUMS) | 5,17 | 5,76 | 7,46 | +1,08 | < 0,001 |
| Vigor | 5,66 | 5,28 | 4,49 | −0,74 | 0,001 |

O padrão — incremento pequeno de S1 para S2 e salto de S2 para S3 — indica **acúmulo que se precipita**, não deterioração linear uniforme.

### 3.2 Carga interna: assinatura de fadiga acumulada

Entre as três sessões, a **FC de pico declinou (183,8 → 183,3 → 180,8 bpm)** enquanto o esforço percebido se manteve ou aumentou (PSE 6,6 → 6,5 → 7,1) e a recuperação a 1 min piorou levemente (Tabela 2). O atleta entrega esforço percebido máximo com um pico cardíaco cada vez menor — a assinatura clássica da fadiga acumulada, aqui documentada **dentro da própria semana**.

**Tabela 2.** Carga interna por sessão de HIIT (S1–S3).

| Sessão | FC de pico (bpm) | HRR 1′ | PSE |
|---|---|---|---|
| S1 (22/04) | 183,8 | 25,8 | 6,55 |
| S2 (24/04) | 183,3 | 27,5 | 6,50 |
| S3 (27/04) | 180,8 | 28,3 | 7,06 |

### 3.3 Acoplamento psicofisiológico intra-atleta

O humor e a carga interna acoplam-se **dentro do atleta** ao longo das três sessões (Tabela 3): na sessão em que o atleta atinge maior FC de pico — marcador de frescor —, o vigor é maior (rmcorr = +0,57) e a perturbação e a fadiga física, menores (−0,48 e −0,51). A percepção de esforço acompanha a perturbação de forma mais fraca. A convergência entre o marcador fisiológico e o psicométrico, ambos no eixo energia–fadiga, sustenta a validade de construto do autorrelato: **o rebaixamento objetivo do pico cardíaco carrega a piora do humor** — a repetição das sessões piora o estado sobretudo por reduzir o pico cardíaco alcançável, não pela mera contagem de sessões.

**Tabela 3.** Acoplamento intra-atleta (rmcorr, 3 sessões, n = 68 observações, 26 atletas).

| Par | rmcorr |
|---|---|
| FC de pico × Vigor | **+0,57** |
| FC de pico × Fadiga física | −0,51 |
| FC de pico × TMD | −0,48 |
| PSE × TMD | +0,39 |
| PSE × Fadiga física | +0,21 |

### 3.4 Resposta individual: quem muda de forma confiável

A tradução dos efeitos médios em decisões individuais (RCI, Dia 1 → Dia 7) mostra que a **fadiga física é a resposta mais confiável** (Tabela 4): 14 de 21 atletas apresentaram aumento confiável e **nenhum** redução. O vigor caiu de forma confiável em 7 atletas; o TMD respondeu de modo heterogêneo (8 aumentos confiáveis, 2 reduções). A MDC₉₅ fornece o limiar prático por escala: variações menores que ≈ 2,3 pontos na fadiga física, ≈ 4 no vigor/fadiga e ≈ 8,5 no TMD **não** devem ser interpretadas como mudança real de um atleta.

**Tabela 4.** Mudança individual confiável (RCI, D1 → D7; n = 21).

| Variável | MDC₉₅ | Aumento confiável | Sem mudança | Redução confiável |
|---|---|---|---|---|
| Fadiga física | 2,34 | **14** | 7 | 0 |
| Fadiga (BRUMS) | 3,89 | 10 | 10 | 1 |
| TMD | 8,45 | 8 | 11 | 2 |
| Vigor | 3,96 | 0 | 14 | 7 |

### 3.5 Variabilidade individual e utilidade da medida

As dimensões do eixo energia–fadiga são as que efetivamente **flutuam** dentro do atleta (Tabela 5): vigor e fadiga têm as maiores iSD, enquanto as subescalas negativas permanecem quase fixas (Tensão iSD = 0,94; Confusão 0,65) — só faz sentido procurar resposta aguda onde há variância de estado. Contudo, o erro típico da medida excede a menor mudança relevante em todas as variáveis (utilidade "marginal" no critério de Hopkins), sendo a **fadiga física a menos ruidosa** (ETM = 20%). Daí a recomendação: decidir por **médias de múltiplas coletas**, não por leituras isoladas.

**Tabela 5.** Variabilidade intra-individual e erro de medida.

| Variável | iSD | MSSD | ETM (%) | SWC | Utilidade |
|---|---|---|---|---|---|
| Fadiga física | — | — | 1,21 (20%) | 0,32 | marginal |
| Vigor | 2,05 | 6,9 | 1,46 (26%) | 0,50 | marginal |
| Fadiga | 2,45 | 11,1 | 1,66 (29%) | 0,62 | marginal |
| TMD | 5,54 | 48,1 | 4,41 (100%) | 1,52 | marginal |
| Tensão | 0,94 | 1,6 | — | — | — |
| Confusão | 0,65 | 1,2 | — | — | — |

### 3.6 Aptidão prévia como covariável de base

Usada apenas como covariável de base (medida em 15/04, imediatamente antes da semana), a aptidão aeróbia moderou a fadiga do microciclo: o atleta com maior velocidade de pico do T-CAR fadigou menos (T-CAR × fadiga física média da semana *ρ* = −0,54; *p* = 0,005; × TMD *ρ* = −0,28; n.s.). Como o estímulo foi prescrito a 104% da velocidade de pico individual, o custo interno é relativo e equalizado — de modo que a vulnerabilidade à fadiga da semana associa-se a um **traço de aptidão prévio**, e não à intensidade absoluta corrida.

## 4. Discussão

Dentro do próprio microciclo, três leituras se integram. Primeiro, a fadiga **acumula-se e se precipita**: o salto da perturbação ocorre na terceira sessão, não linearmente — coerente com uma reserva de recuperação que se esgota. Segundo, essa piora está **acoplada ao custo fisiológico**: nas sessões em que o pico cardíaco cai, o vigor cai e a perturbação sobe, dentro do mesmo atleta — o autorrelato não é um relato isolado, mas converge com o marcador cardiovascular, o que confere robustez de construto ao monitoramento subjetivo. Terceiro, e decisivo para a prática, a resposta é **individual**: a fadiga física é a variável-sentinela (mudança mais confiável, menor erro), o vigor responde de forma consistente na direção da queda, e o TMD, embora sensível em média, é ruidoso demais para leitura pontual. A heterogeneidade (iSD elevado no TMD; parte dos atletas sem mudança confiável) reforça que o alvo do monitoramento é o **desvio de cada atleta em relação à sua própria linha de base**, acima da mudança mínima detectável.

**Limitações.** Progressão entre sessões confundida com o acúmulo semanal (as sessões são também os dias 2, 4 e 7); "pré/pós" definidos como primeira/última coleta do dia; três sessões por atleta limitam a estimação intra-individual; amostra masculina única; e a aptidão prévia, embora tratada como covariável de base pré-semana, foi medida fora da janela de sete dias. As análises individuais (RCI, variabilidade, moderação, n = 21–27) são de baixa potência e devem ser lidas como aplicadas/descritivas.

## 5. Conclusão

O custo do microciclo de choque de HIIT acumula-se e **se precipita na sessão final**, acoplado, dentro de cada atleta, ao rebaixamento do pico cardíaco. A tradução para a prática é inequívoca: monitorar por **fadiga física** (a sentinela mais confiável e menos ruidosa), por **médias de múltiplas coletas**, contra a **linha de base individual** e acima da **mudança mínima detectável** de cada escala — convertendo o BRUMS de gatilho reativo em instrumento de vigilância individual dentro do microciclo.
