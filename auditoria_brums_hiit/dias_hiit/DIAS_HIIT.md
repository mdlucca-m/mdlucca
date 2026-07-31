# Comparação entre os dias do microciclo

Três contrastes sobre a **resposta aguda** (Δ = pós − pré, por atleta-dia) do
microciclo de sete dias — HIIT nos dias **2, 4 e 7**; técnico-tático (sem HIIT)
nos dias **1, 3, 5 e 6**. Reproduzível: `python dias_hiit.py`.

## A. Entre os dias de HIIT (D2 vs D4 vs D7)

As três sessões de HIIT produzem uma resposta aguda **estatisticamente
equivalente** — o teste de Friedman sobre o Δ agudo é **não significativo em
todas as variáveis**:

| Variável | Δ D2 | Δ D4 | Δ D7 | Friedman χ² | p |
|---|---|---|---|---|---|
| PTH (TMD) | +1,14 | +3,43 | +3,50 | 0,73 | 0,69 |
| Fadiga física | +2,50 | +1,86 | +1,64 | 2,74 | 0,25 |
| Vigor | −1,21 | −1,14 | −0,57 | 3,79 | 0,15 |
| Fadiga | +2,36 | +0,64 | +1,50 | 2,44 | 0,30 |
| Fadiga mental | +0,43 | +0,29 | +0,79 | 0,93 | 0,63 |

**As três sessões de HIIT são um estímulo consistente:** a perturbação aguda de
humor não difere entre a primeira (D2), a segunda (D4) e a terceira (D7) — não há
sinal de habituação nem de amplificação progressiva da resposta *aguda* ao longo
do microciclo. (Os testes par-a-par de Wilcoxon, com FDR, confirmam.)

## B. Entre os dias SEM HIIT (D1, D3, D5, D6)

Os dias técnico-táticos são equivalentes entre si em quase tudo — **exceto no PTH**:

| Variável | Δ D1 | Δ D3 | Δ D5 | Δ D6 | Friedman χ² | p |
|---|---|---|---|---|---|---|
| **PTH (TMD)** | **+7,45** | +2,45 | +3,09 | **+9,55** | 9,03 | **0,029** |
| Fadiga física | +1,91 | +1,00 | +2,18 | +1,82 | 1,74 | 0,63 |
| Vigor | −2,18 | −1,09 | −0,73 | −3,00 | 5,01 | 0,17 |
| Fadiga | +2,82 | +1,18 | +1,73 | +2,18 | 2,91 | 0,41 |
| Fadiga mental | +1,27 | 0,00 | +1,27 | +1,36 | 0,25 | 0,25 |

O único contraste significativo é o PTH: os dias **1 e 6** têm perturbação aguda
bem maior (Δ ≈ +7 a +10) que os dias 3 e 5 (Δ ≈ +2 a +3). Ou seja, **nem todo dia
sem HIIT é igual** — há dias técnico-táticos que mexem tanto no humor quanto (ou
mais que) os de HIIT, provavelmente por fatores de contexto (início de semana,
véspera/carga acumulada). As demais variáveis são estáveis entre dias sem HIIT.

## C. HIIT vs SEM HIIT (resposta aguda média por atleta)

Comparando, por atleta, a média do Δ agudo nos dias de HIIT contra a dos dias sem
HIIT (Wilcoxon pareado + t, dz, RBC, FDR):

| Variável | Δ HIIT | Δ SEM | dz | p (FDR) | Difere? |
|---|---|---|---|---|---|
| PTH (TMD) | +2,99 | +3,49 | −0,09 | 0,88 | não |
| Fadiga física | +2,00 | +1,35 | +0,38 | 0,49 | não |
| Vigor | −0,91 | −1,29 | +0,18 | 0,84 | não |
| Fadiga | +1,68 | +1,10 | +0,25 | 0,73 | não |
| Fadiga mental | +0,58 | +0,52 | +0,04 | 0,99 | não |

**A resposta aguda pré→pós é estatisticamente semelhante entre dias de HIIT e sem
HIIT** — nenhuma variável difere após FDR. A fadiga física é a que mais tende a
subir nos dias de HIIT (dz = 0,38), a favor da amplificação já descrita, mas o
efeito não sobrevive à correção neste contraste agregado por atleta. Este achado
é **coerente com a interação Condição×Momento nula** do módulo de modelagem
(p = 0,910 para o PTH): o *salto agudo* pré→pós não é a assinatura do HIIT.

## Leitura integrada

A assinatura do HIIT **não** está no salto agudo (que é parecido em qualquer dia),
mas no **nível do dia** e no **acúmulo** ao longo da semana — o painel D mostra o
PTH médio subindo até o pico no D7 (o terceiro e último HIIT), com o vale no D5.
Combinando os três contrastes: (i) as três sessões de HIIT são um estímulo agudo
**consistente**; (ii) os dias sem HIIT são equivalentes, salvo o PTH em D1/D6; e
(iii) HIIT e sem-HIIT não diferem no salto agudo — o efeito do HIIT vive no nível
diário e no acúmulo (ΔPTH day-level +2,43 no módulo de modelagem), não na
magnitude da resposta pré→pós. Consistente com todo o restante do estudo.

Figura: `dias_hiit_fig.png` (A: entre dias de HIIT; B: entre dias sem HIIT; C: HIIT vs sem; D: nível de PTH por dia D1→D7).
