# Resíduos, coeficientes e psicometria robusta

Camada de robustez adicional. Reproduzível: `python analise.py`.
Fontes: `modelagem/base_modelagem.csv`, `analises_avancadas/itens_brums.csv`.

## A. Coeficientes e resíduos dos modelos mistos
Modelo `y ~ Pós + Dia + HIIT + (1|atleta)` (REML) para PTH, fadiga física, fadiga e vigor.
Reporta efeitos fixos (β, EP, z, p, IC95%), componentes de variância (atleta/resíduo),
ICC, e o **diagnóstico de resíduos condicionais** (resíduo vs. ajustado, Q–Q,
escala–locação, histograma; Shapiro e heterocedasticidade de Spearman) e os
interceptos aleatórios por atleta (BLUPs). Figura: `residuos_coef_fig.png`.

## B. Psicometria robusta por subescala
α de Cronbach, **α ordinal** (Spearman), **ω de McDonald**, **AVE**, **CR**
(confiabilidade composta) e correlação item-total corrigida; validade
discriminante de **Fornell–Larcker** (√AVE vs. correlações entre subescalas).
Figura: `psicometria_robusta_fig.png`.

## C. Análise fatorial exploratória (AFE) e cargas
KMO, esfericidade de Bartlett, autovalores (scree), **análise paralela**
(Horn), número de fatores por Kaiser e por paralela, e a **matriz de cargas**
rotacionada (promax, 6 fatores) com a variância explicada. Figura: `afe_cargas_fig.png`.
