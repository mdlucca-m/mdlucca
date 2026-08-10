# Limites e derivadas da trajetória de humor

Tratamento de **cálculo** da dinâmica do humor ao longo do microciclo: a
trajetória diária como função contínua, a **derivada** (velocidade de acúmulo de
fadiga) obtida pela definição por **limite**, a segunda derivada (aceleração) e os
**limites assintóticos** (estado estacionário). Aplicado à fadiga física — o
marcador-sentinela. Reproduzível: `python limites_derivadas.py`.

## A. A trajetória como função contínua

A média diária da fadiga física foi ajustada por uma função **saturante**:

    f(t) = L − (L − f₁)·e^{−k(t−1)},   com L = 6,78 · f₁ = 4,29 · k = 0,76 (R² = 0,76)

que cresce rápido no início e desacelera rumo a um teto L. A reta **tangente** em
t = 2 (painel A) tem inclinação f′(2) = 0,89 — é a derivada naquele ponto.

## B. Derivada pela definição (limite da razão incremental)

A derivada é o limite da razão incremental quando o passo h → 0:

    f′(t₀) = lim_{h→0} [ f(t₀+h) − f(t₀) ] / h

Numericamente, em t₀ = 2:

| h | [f(t₀+h)−f(t₀)]/h |
|---|---|
| 1 | 0,621 |
| 0,5 | 0,738 |
| 0,25 | 0,808 |
| 0,1 | 0,855 |
| 0,05 | 0,871 |
| 0,01 | 0,885 |
| 0,001 | 0,887 |

A razão incremental **converge para f′(2) = 0,887** (painel B) — a definição de
derivada em ação sobre os dados do estudo.

## C. Derivada e segunda derivada — velocidade e aceleração

Derivando analiticamente:

    f′(t) = k(L − f₁)·e^{−k(t−1)}   (velocidade de acúmulo, pts/dia)
    f″(t) = −k²(L − f₁)·e^{−k(t−1)} < 0   (aceleração — sempre negativa)

| Dia t | f′(t) | interpretação |
|---|---|---|
| 1 | 1,90 | acúmulo mais rápido (início da semana) |
| 2 | 0,89 | desacelerando |
| 4 | 0,19 | quase estável |
| 7 | 0,02 | praticamente saturado |

A **velocidade de acúmulo é positiva e decrescente** (painel C), e a **aceleração é
negativa** (f″ < 0): a fadiga acumula, mas cada vez mais devagar — comportamento de
saturação. As diferenças centrais empíricas (Δ/dia calculado dos dados) acompanham a
derivada analítica, com o ruído esperado dos dias de menor carga (D5).

## D. Limites assintóticos e o modelo teórico fitness–fadiga

- **Estado estacionário:** lim_{t→∞} f(t) = **L = 6,78** — a fadiga física tende a um
  teto; sem novo estímulo, a taxa de acúmulo vai a zero (f′ → 0).
- **Modelo teórico fitness–fadiga** (pós-sessão), com o estado como desvio da linha
  de base: State(t) = k₁·e^{−t/τ₁} − k₂·e^{−t/τ₂}. Sua derivada é

      State′(t) = −(k₁/τ₁)·e^{−t/τ₁} + (k₂/τ₂)·e^{−t/τ₂}

  e o **ponto crítico** (State′(t*) = 0) ocorre em

      t* = ln[(k₂/τ₂)/(k₁/τ₁)] / (1/τ₂ − 1/τ₁)

  Nele o estado atinge o **nadir/pico de fadiga aguda** (a derivada troca de sinal:
  antes o efeito de recuperação domina, depois relaxa). Com parâmetros ilustrativos
  (fadiga rápida, fitness lenta), t* ≈ 2,7 (painel D). E **lim_{t→∞} State(t) = 0**:
  sem novo estímulo, o estado retorna à linha de base.

## Leitura

O cálculo formaliza o que os dados já mostravam: a fadiga física **acumula com
velocidade positiva mas decrescente** (derivada > 0, aceleração < 0) e **satura**
num teto (limite finito). O modelo teórico fitness–fadiga dá o arcabouço contínuo —
a derivada zera no pico de fadiga (ponto crítico) e o estado retorna à base no
limite. Traduzindo para o treino: o maior salto de fadiga é no início do
microciclo; perto do fim, a curva achata — e o monitoramento por **tendência**
(a derivada) antecipa a saturação antes que o escore absoluto a revele.

Figura: `limites_derivadas_fig.png` (A: trajetória e tangente; B: razão incremental → derivada; C: velocidade e aceleração; D: modelo teórico, ponto crítico e limite).
