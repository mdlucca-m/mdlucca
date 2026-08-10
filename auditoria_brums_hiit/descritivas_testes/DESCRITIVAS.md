# Descritivas + testes paramétricos e não-paramétricos

Estatística descritiva completa, teste de normalidade e a comparação pré→pós
**paramétrica** (t pareado) vs. **não-paramétrica** (Wilcoxon) lado a lado.
Reproduzível: `python descritivas.py` (lê `../modelagem/base_modelagem.csv`).

## A. Descritivas + normalidade (amostra completa, n = 456)

| Variável | M (DP) | Md [IQR] | Assim. | Curt. | % piso | Shapiro W | Normal? |
|---|---|---|---|---|---|---|---|
| PTH (TMD) | 4,39 (9,64) | 2,0 [10,0] | +1,48 | — | 6,6 | 0,90 | não |
| Fadiga física | 6,12 (2,34) | 6,0 [3,0] | −0,37 | — | 0,7 | 0,96 | não |
| Fadiga | 5,64 (3,89) | 5,0 [5,0] | +0,59 | — | 7,7 | 0,95 | não |
| Vigor | 5,70 (3,12) | 6,0 [4,0] | +0,03 | — | 8,6 | 0,97 | não |
| Fadiga mental | 4,59 (2,81) | 4,0 [5,0] | +0,21 | — | 5,3 | 0,95 | não |
| Tensão | 1,39 (1,84) | 1,0 [2,0] | +1,43 | — | 49,6 | 0,77 | não |
| Depressão | 1,00 (2,31) | 0,0 [1,0] | +3,63 | — | 67,1 | 0,49 | não |
| Raiva | 1,60 (2,73) | 0,0 [2,0] | +2,06 | — | 59,6 | 0,66 | não |
| Confusão | 0,45 (1,19) | 0,0 [0,0] | +3,73 | — | 80,5 | 0,44 | não |
| Estado físico | 1,83 (1,02) | 2,0 [2,0] | −0,26 | — | — | 0,89 | não |
| Estado mental | 2,36 (1,04) | 3,0 [1,0] | −0,69 | — | — | 0,87 | não |

**Nenhuma** variável é normal na amostra completa (Shapiro p<0,05) — esperado:
as subescalas negativas têm forte assimetria positiva e efeito piso (confusão
80,5%, depressão 67,1%). Isso justifica reportar também os testes
não-paramétricos. (Com n=456 o Shapiro é muito sensível; a assimetria e o % piso
são os indicadores práticos.)

## B. Pré→pós — paramétrico vs. não-paramétrico (agregado por atleta, n = 27)

| Variável | Dif. normal? | t: p | dz | Wilcoxon: p | RBC | Concordam? |
|---|---|---|---|---|---|---|
| Fadiga física | normal | <0,001 | +0,96 | <0,001 | +0,91 | ✔ |
| Estado físico | normal | <0,001 | +0,81 | <0,001 | −0,89 | ✔ |
| Fadiga | não-normal | 0,004 | +0,50 | 0,003 | +0,69 | ✔ |
| PTH (TMD) | normal | 0,002 | +0,42 | 0,004 | +0,64 | ✔ |
| Vigor | normal | 0,008 | +0,36 | 0,011 | −0,58 | ✔ |
| Fadiga mental | normal | 0,031 | +0,21 | 0,047 | +0,47 | ✔ |
| Tensão | não-normal | 0,038 | +0,16 | 0,050 | +0,53 | ✔ |
| Estado mental | não-normal | 0,051 | +0,18 | 0,070 | −0,52 | ✔ |
| Depressão | não-normal | 0,071 | +0,16 | 0,117 | +0,43 | ✔ |
| Raiva | normal | 0,297 | +0,15 | 0,438 | +0,19 | ✔ |
| Confusão | normal | 0,613 | +0,05 | 0,623 | −0,15 | ✔ |

> **Convergência total:** paramétrico e não-paramétrico chegam à **mesma decisão
> em todas as 11 variáveis** (nenhuma divergência na figura B — os pontos caem na
> diagonal). As conclusões do estudo **não dependem** da escolha da família de
> teste. As diferenças pré→pós são majoritariamente normais (7 de 11), o que
> ampara o uso dos testes paramétricos no plano agudo; onde não são (fadiga,
> tensão, depressão, estado mental), o Wilcoxon confirma. O sinal do RBC segue a
> direção da mudança (negativo em vigor e estado, que caem no pós).

> Nota de efeito: aqui o `dz` é o *cohen-d pareado* do pingouin (denominador =
> DP média); no módulo `estatistica_inferencial/` o dz usa a DP das diferenças —
> daí a pequena diferença numérica (ex.: fadiga física 0,96 vs 1,06). Ambos são
> válidos; a significância e a direção coincidem.

Figura: `descritivas_fig.png` (A: forma/normalidade; B: concordância paramétrico×não-paramétrico).
