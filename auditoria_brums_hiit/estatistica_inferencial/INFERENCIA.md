# Estatística inferencial — bateria clássica

Complementa os modelos mistos (`../modelagem/`) com os testes clássicos que um
comitê espera, sempre respeitando as medidas repetidas (agregação por atleta,
n=27) e reportando **tamanho de efeito + IC95%** e **correção FDR**. Reproduzível:
`python inferencia.py` (lê `../modelagem/base_modelagem.csv`, anonimizada).

## A. Resposta aguda pré→pós — t pareado + Wilcoxon, dz (IC95% bootstrap), FDR

| Desfecho | Δ | dz | IC95% | t | p (FDR) | sig. |
|---|---|---|---|---|---|---|
| Fadiga física | +1,65 | **+1,06** | [0,75; 1,54] | +5,52 | <0,001 | ✔ |
| PTH (TMD) | +3,47 | **+0,68** | [0,39; 1,04] | +3,52 | 0,007 | ✔ |
| Fadiga | +1,50 | **+0,62** | [0,40; 0,92] | +3,21 | 0,011 | ✔ |
| Vigor | −1,09 | **−0,56** | [−0,97; −0,22] | −2,89 | 0,017 | ✔ |
| Fadiga mental | +0,57 | +0,44 | [0,10; 0,78] | +2,29 | 0,055 | — |
| Tensão | +0,20 | +0,42 | [0,09; 0,76] | +2,19 | 0,057 | — |
| Depressão | +0,36 | +0,36 | [0,07; 0,64] | +1,88 | 0,092 | — |
| Raiva | +0,37 | +0,20 | [−0,18; 0,54] | +1,06 | 0,334 | — |
| Confusão | −0,04 | −0,10 | [−0,53; 0,28] | −0,51 | 0,613 | — |

Quatro variáveis do **eixo energia–fadiga** (fadiga física, PTH, fadiga, vigor)
sobrevivem ao FDR; o Wilcoxon concorda com o t pareado em todas. Ver `forest_dz.png`.

## B. Efeito do dia — Friedman (casos completos, n=19) e ANOVA de MR (Greenhouse–Geisser)

| Desfecho | Friedman χ² | p | RM-ANOVA F | p (GG) |
|---|---|---|---|---|
| Fadiga física | 48,8 | <0,001 | 13,00 | <0,001 |
| Vigor | 14,7 | 0,022 | 6,34 | 0,001 |
| Fadiga | 13,2 | 0,040 | 3,10 | 0,023 |
| PTH (TMD) | 7,6 | 0,269 | 2,17 | 0,094 |

O efeito do dia é claro para **fadiga física, vigor e fadiga**. Para o **PTH**,
os testes clássicos são n.s. — coerente com o modelo misto de inclinação
aleatória, que mostrou o acúmulo do PTH dominado pela **heterogeneidade
individual** (efeito médio marginal).

## C. HIIT vs. técnico-tático — t pareado no nível do atleta (dias 2–7)

| Desfecho | Δ (HIIT−sem) | dz | t | p |
|---|---|---|---|---|
| PTH (TMD) | +1,90 | +0,48 | +2,42 | 0,023 |
| Fadiga | +0,52 | +0,40 | +2,00 | 0,057 |
| Vigor | −0,39 | −0,39 | −1,94 | 0,064 |
| Fadiga física | +0,22 | +0,18 | +0,89 | 0,382 |
| Fadiga mental | +0,17 | +0,13 | +0,67 | 0,507 |

Só o **PTH** difere significativamente (dias de HIIT mais perturbados). (Aqui a
média do atleta agrega todos os momentos do dia; o modelo misto no nível
atleta×dia dá ΔPTH +2,43, mesma direção.)

## D. Correlações repetidas (rm_corr, Bakdash & Marusich) — subescala × externos

**17 de 24** correlações significativas após FDR. As mais fortes (todas
intra-sujeito, com IC95%):

| Par | r | IC95% |
|---|---|---|
| Fadiga × Estado físico | −0,65 | [−0,70; −0,60] |
| Fadiga × Fadiga física | +0,64 | [0,58; 0,69] |
| Vigor × Estado físico | +0,47 | [0,40; 0,54] |
| Vigor × Fadiga física | −0,46 | [−0,53; −0,38] |
| Fadiga × Fadiga mental | +0,45 | [0,38; 0,53] |
| Fadiga × Estado mental | −0,45 | [−0,52; −0,37] |

O acoplamento intra-sujeito é dominado pelo **eixo fadiga↔estado físico** — a
fadiga (subescala) acompanha de perto a fadiga física e o estado físico
autopercebido, como esperado por validade concorrente.

## E. ICC do atleta — partição de variância (fração de traço estável)

| Subescala | ICC(atleta) |
|---|---|
| Tensão | 0,71 |
| Fadiga mental | 0,70 |
| Depressão | 0,68 |
| PTH (TMD) | 0,59 |
| Fadiga | 0,58 |
| Vigor | 0,55 |
| Fadiga física | 0,42 |
| Raiva | 0,00 |
| Confusão | 0,00 |

O ICC é a fração da variância que é **traço estável** (entre atletas). Valores
de 0,55–0,71 na maioria indicam boa separação entre atletas; **raiva e confusão
= 0** porque são dominadas pelo piso (quase sem variância entre atletas) — a
mesma limitação psicométrica recorrente. A fadiga física tem ICC menor (0,42)
justamente por ser a mais **responsiva** (mais variância de estado/dia, menos de
traço) — o que a torna o melhor sinal de mudança aguda.

## Síntese

Os testes clássicos **confirmam** o quadro dos modelos mistos: efeito agudo e
efeito do dia reais e concentrados no eixo energia–fadiga; HIIT eleva o PTH no
nível do dia; acoplamento intra-sujeito fadiga↔estado físico; e a fadiga física
como a variável mais responsiva (alto dz, baixo ICC de traço) — a candidata a
marcador sentinela. Figura: `forest_dz.png`.
