# Modelo teórico, R², erro-padrão, bayesiano e multivariada

Formalização matemática da resposta de humor ao microciclo e sua estimação por
**três vias que convergem** — frequentista (R²/erro-padrão), bayesiana (Gibbs) e
multivariada (MANOVA/PERMANOVA). Reproduzível: `python modelo_teorico.py`
(lê `../modelagem/base_modelagem.csv`). Ver o diagrama em `framework_fig.png`.

## Modelo matemático teórico

Fundo teórico — modelo **impulso-resposta fitness–fadiga** (Banister):

    State(t) = p₀ + k₁·g(t) − k₂·h(t),   g,h = Σ wᵢ·e^{−(t−i)/τ}  (τ_fitness > τ_fatigue)

O estado a cada instante é o saldo entre um traço lento de "aptidão" (vigor) e um
traço rápido de "fadiga" (custo agudo). A forma **estimável** desse balanço, com o
atleta como unidade, é o modelo linear de efeitos mistos:

    Yᵢⱼₜ = β₀ + β₁·Pós + β₂·Dia + β₃·HIIT + uᵢ + εᵢⱼₜ,   uᵢ ~ N(0,τ²),  ε ~ N(0,σ²)

em que **uᵢ** é o desvio individual (traço) e o **ICC = τ²/(τ²+σ²)** mede a fração
da variância que é entre atletas.

## 1. Coeficiente de determinação (Nakagawa & Schielzeth) e erro-padrão

| Desfecho | R² marginal (fixos) | R² condicional (fixos+individual) | ICC | β(Pós) ± SE |
|---|---|---|---|---|
| PTH (TMD) | 0,058 | 0,616 | 0,59 | 3,47 ± 0,76 |
| Fadiga física | 0,212 | 0,584 | 0,47 | 1,65 ± 0,20 |
| Vigor | 0,063 | 0,594 | 0,57 | −1,09 ± 0,26 |
| Fadiga | 0,079 | 0,631 | 0,60 | 1,50 ± 0,30 |

O achado central salta aos olhos: o **R² marginal é pequeno** (os efeitos fixos —
Pós/Dia/HIIT — explicam de 6 % a 21 % da variância), mas o **R² condicional é
grande** (0,58–0,63) quando se adiciona a dimensão **individual**. Ou seja,
**a maior parte do que o modelo explica vem de quem é o atleta**, não do
protocolo — a assinatura quantitativa da individualidade (painel A). A fadiga
física é a exceção parcial: tem o maior R² marginal (0,21), coerente com ser o
marcador mais "de estado". Os erros-padrão (painel B) mostram efeitos fixos bem
determinados para o Pós e o HIIT; o intervalo do "Dia" é estreito e positivo.

## 2. Estimação bayesiana (amostrador de Gibbs)

Modelo hierárquico gaussiano conjugado, priors fracos, 6 000 iterações
(descarte 1 500):

| Desfecho | β(Pós) posterior | SE bayesiano | ICr 95 % | P(efeito > 0) |
|---|---|---|---|---|
| PTH (TMD) | 3,48 | 0,76 | [1,98; 4,99] | 1,00 |
| Fadiga física | 1,65 | 0,20 | [1,25; 2,04] | 1,00 |

A posterior bayesiana **coincide com a estimativa frequentista** (β 3,48 vs 3,47;
SE idêntico; painel C), com **P(efeito > 0) = 1,00** — probabilidade posterior
praticamente certa de que o microciclo eleva o PTH e a fadiga física. As duas
filosofias de inferência chegam ao mesmo lugar, o que reforça a robustez do efeito.

## 3. Análise multivariada

Tratando as seis subescalas como um vetor de resposta:

| Teste | Estatística | p |
|---|---|---|
| MANOVA (traço de Pillai) | 0,057 · F = 2,67 | 0,016 |
| PERMANOVA pareada (Anderson, 2001) | pseudo-F = 10,93 · R² = 0,174 | 0,001 |

A **MANOVA** paramétrica e a **PERMANOVA** por permutação restrita (troca pré/pós
dentro do atleta, 9 999 reamostragens, distância euclidiana sobre o perfil-z, com
remoção do bloco atleta) **concordam**: a mudança pré→pós é um **deslocamento
multivariado significativo** do vetor de humor, e explica **17,4 %** da variância
multivariada pareada (painel D). Complementa o Hotelling T² do módulo de modelagem
por uma via distribuição-livre.

## Framework e leitura

As três vias — **determinação (R²) + erro-padrão** (frequentista), **Gibbs**
(bayesiano) e **MANOVA/PERMANOVA** (multivariada) — convergem para o mesmo quadro
(diagrama em `framework_fig.png`): há um efeito real e bem determinado do
microciclo no **eixo energia–fadiga** (β do Pós positivo para PTH/fadiga/fadiga
física, negativo para vigor; P posterior = 1,00; deslocamento multivariado
significativo), mas a **maior parte da variância explicável é individual**
(R² condicional ≫ marginal; ICC ≈ 0,47–0,60). É a mesma conclusão do estudo,
agora ancorada num modelo matemático explícito e triangulada por três métodos de
estimação independentes.

Figuras: `modelo_teorico_fig.png` (A: R² marginal×condicional; B: efeitos fixos ± erro-padrão; C: posterior bayesiano vs frequentista; D: PERMANOVA) e `framework_fig.png` (diagrama do modelo teórico → forma estimável → três vias de estimação → multivariada).
