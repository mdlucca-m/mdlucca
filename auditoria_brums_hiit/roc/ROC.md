# Análise ROC — capacidade discriminativa do BRUMS

Quão bem cada variável do humor/fadiga **separa** dois estados? AUC (área sob a
curva ROC) com IC95% por **bootstrap agrupado por atleta** (reamostragem de
atletas, respeitando as medidas repetidas), ponto de corte de **Youden** e
sensibilidade/especificidade nesse corte. Reproduzível: `python roc_analise.py`
(lê `../modelagem/base_modelagem.csv`, anonimizada).

## (a) Discriminar PÓS de PRÉ-treino — detecta a resposta aguda?

| Variável | AUC | IC95% | corte | sens. | espec. |
|---|---|---|---|---|---|
| **Fadiga física** | **0,70** | 0,64–0,77 | ≥ 7 | 0,60 | 0,73 |
| PTH (TMD) | 0,61 | 0,54–0,69 | — | 0,79 | 0,40 |
| Fadiga | 0,61 | 0,55–0,68 | — | 0,43 | 0,73 |
| Vigor (↓) | 0,58 | 0,52–0,65 | — | 0,24 | 0,88 |
| Fadiga mental | 0,56 | 0,51–0,60 | — | 0,33 | 0,76 |
| Raiva | 0,54 | 0,50–0,59 | — | — | — |
| Tensão | 0,53 | 0,50–0,57 | — | — | — |
| Depressão | 0,53 | 0,50–0,58 | — | — | — |
| Confusão | 0,51 | 0,50–0,55 | — | — | — |

Só a **fadiga física** discrimina o pós do pré com AUC **moderada (0,70)** — o
único marcador com valor diagnóstico prático para a resposta aguda. PTH e fadiga
ficam em AUC fraca (~0,61); as demais são indistinguíveis do acaso (IC inclui
0,5). Confirma, por outro ângulo, que a fadiga física é o **sentinela** do
estado agudo.

## (b) Discriminar dia de HIIT de dia sem HIIT (nível atleta×dia)

| Variável | AUC | IC95% |
|---|---|---|
| PTH (TMD) | 0,58 | 0,53–0,66 |
| Confusão | 0,56 | 0,52–0,60 |
| Fadiga física | 0,55 | 0,50–0,63 |
| Fadiga | 0,55 | 0,51–0,61 |
| Vigor | 0,54 | 0,50–0,60 |
| demais | ≤ 0,55 | inclui 0,5 |

Nenhuma variável separa bem o **tipo de dia**: todas as AUC ficam entre 0,52 e
0,58. Coerente com o quadro geral — o HIIT eleva o humor perturbado *em média*
(ΔPTH +2,43), mas o valor **medido em um único dia** classifica mal se aquele
dia foi de HIIT, porque a variabilidade individual domina o sinal.

## Leitura conjunta

A capacidade diagnóstica está **concentrada e é modesta**: apenas a fadiga
física atinge AUC moderada, e somente para detectar a *resposta aguda* (pré→pós),
não o *tipo de treino*. Reforça a recomendação prática do estudo — monitorar por
**tendência** (a trajetória ao longo de dias), com a **fadiga física** como
sentinela e uma **linha de base individual**, em vez de tentar classificar um dia
isolado por um escore de humor. As curvas estão em `curvas_roc_pre_pos.png` e
`curvas_roc_hiit.png`.
