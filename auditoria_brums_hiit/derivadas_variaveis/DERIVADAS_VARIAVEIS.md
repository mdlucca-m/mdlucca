# Derivadas por variável e por atleta

Estende o cálculo de derivadas a **todas as variáveis** do eixo humor e à
**derivada individual** de cada atleta. Reproduzível: `python derivadas_variaveis.py`.

## A/B. Derivada f'(t) da trajetória — velocidade de mudança

Ajuste cúbico da média diária de cada variável e sua derivada analítica:

| Variável | f'(1) | f'(7) | Inclinação média (pts/dia) | Direção |
|---|---|---|---|---|
| PTH (TMD) | +4,83 | +6,07 | **+0,53** | acumula |
| Fadiga | +2,49 | +2,23 | +0,44 | acumula |
| Fadiga física | +2,44 | +1,72 | +0,38 | acumula |
| Fadiga mental | +0,16 | +0,67 | +0,03 | estável |
| Vigor | −2,72 | −1,75 | **−0,28** | cai |

O **PTH** tem a maior velocidade média de acúmulo (+0,53/dia); **fadiga** e
**fadiga física** acumulam de forma parecida (+0,4/dia); o **vigor cai** (derivada
negativa); a **fadiga mental é praticamente plana** (derivada ≈ 0). Os painéis A/B
mostram as trajetórias e suas velocidades — todas com forte curvatura (a velocidade
não é constante: acelera e desacelera ao longo da semana).

## C/D. Derivada individual (inclinação por atleta) — heterogeneidade

Inclinação dV/dia de cada atleta (regressão linear):

| Variável | Média | DP | % positivas | Faixa |
|---|---|---|---|---|
| PTH (TMD) | +0,43 | **1,45** | 58 % | [−1,4; +4,3] |
| Fadiga física | +0,42 | **0,40** | **92 %** | [−0,1; +1,9] |
| Fadiga | +0,29 | 0,57 | 77 % | [−0,9; +1,6] |
| Fadiga mental | +0,04 | 0,49 | 69 % | [−2,0; +0,7] |
| Vigor | −0,29 | 0,50 | 27 % | [−1,5; +0,4] |

Aqui está o achado central desta camada: **a mesma velocidade média esconde
heterogeneidades muito diferentes**. O **PTH** tem inclinação média positiva
(+0,43/dia) mas dispersão enorme (DP 1,45) e apenas **58 %** dos atletas com
derivada positiva — ou seja, quase metade **não acumula** transtorno de humor, e há
quem melhore. Já a **fadiga física** tem derivada quase universalmente positiva
(**92 %**) e dispersão pequena (DP 0,40): quase todos acumulam fadiga física, de
forma consistente. O **vigor** cai na maioria (73 % com derivada negativa). O painel
D mostra isso: a "caixa" do PTH é larguíssima, a da fadiga física é estreita.

## Leitura

As derivadas por variável confirmam o **eixo energético** (PTH/fadiga/fadiga física
com derivada positiva; vigor negativa; fadiga mental plana) e a curvatura das
trajetórias (velocidade variável). Mas a mensagem mais forte vem da **derivada
individual**: a **fadiga física acumula de forma homogênea** (a derivada é um
marcador confiável para todos), enquanto o **PTH acumula de forma idiossincrática**
(a derivada só faz sentido individualmente). Isso reproduz — agora no espaço das
*taxas de variação* — a variância de inclinação aleatória do módulo de modelagem
(var ≈ 1,13 para o PTH; ≈ 0,01 para a fadiga física) e reforça o monitoramento
**individualizado por tendência**, com a fadiga física como sentinela consistente.

Figura: `derivadas_variaveis_fig.png` (A: trajetórias z; B: velocidades f'(t); C: derivada média por variável; D: derivada individual por atleta).
