# Curva ROC das derivadas

Em vez do nível absoluto, usa a **derivada aguda** (Δ = pós − pré, por atleta-dia)
como escore diagnóstico. Pergunta: a **taxa de variação** do humor discrimina um
**dia de HIIT** melhor do que o nível absoluto? Alvo: dia de HIIT (2/4/7) vs dia
sem HIIT (1/3/5/6); 135 pares atleta-dia; IC95% por bootstrap agrupado por atleta.
Reproduzível: `python roc_derivadas.py`.

## AUC da derivada vs AUC do nível

| Variável | AUC derivada (Δ agudo) | IC95% | AUC nível (média do dia) | Ganho da derivada |
|---|---|---|---|---|
| Fadiga física | **0,59** | [0,51; 0,67] | 0,58 | +0,01 |
| Fadiga | 0,55 | [0,50; 0,64] | 0,57 | −0,02 |
| Vigor | 0,54 | [0,50; 0,63] | 0,58 | −0,04 |
| Fadiga mental | 0,50 | [0,50; 0,60] | 0,52 | −0,02 |
| PTH (TMD) | 0,50 | [0,50; 0,60] | **0,60** | −0,10 |

## Leitura

A **derivada aguda é um diagnóstico fraco** do dia de HIIT: a melhor é a fadiga
física (AUC 0,59), e as demais ficam próximas do acaso (0,50–0,55) — os intervalos
de confiança quase todos tocam 0,50. Mais informativo é o **contraste com o nível**:
para o **PTH**, o nível do dia discrimina bem melhor (AUC 0,60) do que a sua
derivada (0,50), e em nenhuma variável a derivada supera o nível de forma relevante
(o único "ganho" positivo, na fadiga física, é +0,01 — desprezível).

Isso **converge com os módulos de comparação entre dias e de interação**: o salto
agudo pré→pós (a derivada) é semelhante entre dias de HIIT e sem HIIT, ao passo que
a **assinatura do HIIT vive no nível diário e no acúmulo** (o PTH em nível é o que
melhor separa). Em termos de monitoramento: para *classificar* um dia como sendo de
HIIT, o **estado (nível)** carrega mais sinal do que a *velocidade* de mudança
naquele dia — coerente com "o HIIT perturba o dia, não o salto agudo".

> Nota: a orientação de cada escore é ajustada para AUC ≥ 0,50 (a fadiga física
> sobe no HIIT; o vigor cai). Como no módulo ROC principal, a discriminação global
> do tipo de dia por um único marcador de humor é modesta — o valor do BRUMS está
> na tendência individual, não na classificação pontual.

Figura: `roc_derivadas_fig.png` (A: curvas ROC das derivadas agudas; B: AUC derivada vs nível, com IC95% por bootstrap por atleta).
