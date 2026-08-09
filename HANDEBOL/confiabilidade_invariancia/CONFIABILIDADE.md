# Confiabilidade · significância · invariância

Confiabilidade interna de cada subescala do BRUMS, teste prático de
significância (o IC95% do α cruza 0,70?) e invariância de medida pré→pós.
Reproduzível: `python confiabilidade.py` (lê `../analises_avancadas/itens_brums.csv`).

## A. Confiabilidade por subescala (n = 456 respostas de item)

| Subescala | k | α de Cronbach | IC95% | ω de McDonald | r inter-item | Adequada (α≥0,70)? |
|---|---|---|---|---|---|---|
| Raiva | 4 | 0,868 | [0,847; 0,887] | 0,871 | 0,624 | ✔ |
| Depressão | 4 | 0,845 | [0,821; 0,867] | 0,872 | 0,627 | ✔ |
| Fadiga | 4 | 0,795 | [0,763; 0,824] | 0,824 | 0,473 | ✔ |
| Vigor | 4 | 0,684 | [0,633; 0,728] | 0,775 | 0,383 | limítrofe¹ |
| Confusão | 4 | 0,653 | [0,598; 0,702] | 0,682 | 0,320 | limítrofe¹ |
| Tensão | 4 | 0,427 | [0,337; 0,509] | 0,474 | 0,163 | ✘ |

Os valores de α reproduzem a Tabela de confiabilidade do manuscrito. Três
subescalas — **Raiva, Depressão e Fadiga** — são confiáveis com folga (α e ω
acima de 0,80; IC95% inteiramente acima de 0,70). **Vigor** e **Confusão**
ficam abaixo de 0,70 no α, mas o ω (que não pressupõe cargas iguais entre itens)
sobe para 0,78 e 0,68 e o **limite superior do IC do α atinge/cruza 0,70** — daí
"limítrofe": aceitáveis para uso agregado, com cautela no item. **Tensão** é a
única frágil de fato (α = 0,43, ω = 0,47, r inter-item = 0,16): o efeito piso é
severo (49,6 % de zeros nessa subescala) e um item destoa dos demais.

> ¹ **Significância prática:** onde α < 0,70 mas o IC95% alcança 0,70, a diferença
> em relação ao critério não é estatisticamente firme — a subescala não é
> "reprovada", apenas medida com menos precisão nesta amostra pequena. Onde o IC
> inteiro fica abaixo de 0,70 (Tensão), a baixa confiabilidade é significativa.

## B. Invariância de medida pré→pós

Cargas fatoriais de 1 fator por subescala estimadas separadamente no **pré**
(n = 135) e no **pós** (n = 135) e comparadas.

| Indicador | Pré | Pós |
|---|---|---|
| CFI por grupo (CFA, módulo `analises_avancadas`) | 1,01 | 1,02 |
| **Congruência de cargas (Tucker φ)** | **0,987** | |
| Invariância métrica sustentada? | **Sim** (φ ≥ 0,95) | |

As cargas dos 20 itens elegíveis (item `tensao_1` excluído por variância
degenerada) mantêm praticamente a mesma estrutura antes e depois do microciclo:
Tucker φ = 0,987 (bem acima do corte 0,95), com os pontos do painel B alinhados
à diagonal. **A escala mede o mesmo construto da mesma forma nos dois momentos**,
o que é a condição para interpretar a mudança pré→pós como mudança de estado —
e não como deriva psicométrica do instrumento.

> Nota de método: a congruência de Tucker e o CFI por grupo cobrem a invariância
> **configural + métrica**. O teste formal escalar (ΔCFI encadeando
> configural→métrico→escalar num único modelo multigrupo) exige `lavaan`/R e está
> roteirizado em `../analises_avancadas/replicacao_R.R`.

Figura: `confiabilidade_fig.png` (A: α com IC95% e ω por subescala; B: cargas pré×pós com Tucker φ).
