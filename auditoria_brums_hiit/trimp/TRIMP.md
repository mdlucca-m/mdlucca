# Carga interna por TRIMP — resultados

TRIMP (*Training Impulse*) é, por definição, **intensidade × duração**. A planilha
de FC/PSE **não registrou duração** de fase/sessão; portanto reporta-se aqui o
que é honesto sem duração. Reproduzível: `python trimp.py` (lê `fc_fases.csv` +
`../modelagem/base_modelagem.csv`, ambos anonimizados).

## Como foi calculado

- **Intensidade por fase** pela fração da reserva de FC (%HRR) com a ponderação
  exponencial de **Banister** (homens):
  `w = %HRR · 0,64 · e^(1,92 · %HRR)`, com `%HRR = (FCpós − FCrepouso)/(FCmax − FCrepouso)`.
  FCrepouso = menor FC pré do atleta; FCmax = maior FC de pico do atleta.
- **TRIMP relativo por sessão** = Σ das ponderações das 5 fases (duração unitária
  por fase). É um índice **comparável** entre atletas/sessões, **não** um AU absoluto.
- Sessões com < 3 fases de FC válidas foram descartadas (FC ausente).

> **TRIMP absoluto (AU):** basta multiplicar `w` pela duração real de cada fase
> (`TRIMP_fase = duração_min · w`). Informe as durações e recalculo os AU.

## Resultados

**Intensidade quase-máxima e estável.** O %HRR médio ficou entre **0,87 e 0,91**
(87–91% da reserva de FC) nas quatro sessões — teto fisiológico, coerente com a
FC de pico de 97–99% da FCmáx observada. O TRIMP relativo por sessão variou pouco
(15,1–17,0), com leve mínimo na S3.

| Sessão | TRIMP relativo | %HRR | Foster (ΣPSE) |
|---|---|---|---|
| S1 | 16,98 | 0,91 | 32,8 |
| S2 | 16,43 | 0,89 | 32,5 |
| S3 | 15,11 | 0,87 | 35,3 |
| S4 | 16,46 | 0,89 | 32,6 |

**As duas famílias de carga interna são praticamente independentes.** TRIMP (FC)
× carga de Foster (ΣPSE), no nível atleta-sessão: **r = −0,05** (Spearman ρ =
−0,04; n = 101). Como a intensidade de FC está comprimida no teto (todos ~89%
HRR), a carga baseada em FC quase não varia, enquanto a PSE ainda distingue
sessões — por isso os dois marcadores **não se acompanham** neste contexto
quase-máximo. (Uma primeira versão sem limpeza dava r = 0,53, inflado por duas
sessões com FC ausente lançadas como zero — corrigido.)

**Carga interna não prediz a perturbação aguda do humor.** TRIMP relativo médio
do atleta × Δ PTH agudo nos dias de HIIT: **r = −0,32, p = 0,12 (n.s.), n = 25**.
Converge com o achado via PSE (r ≈ −0,05): **a magnitude da carga — seja por FC,
seja por PSE — não determina o tamanho da resposta aguda de humor.**

**Monotonia e strain (família TRIMP), semana:** monotonia 13,2 ± 6,7; strain
854 ± 490 (unidades relativas).

## Limitações (honestas)

1. **Sem duração** → TRIMP é relativo (por fase-unidade), não AU absoluto.
2. **%HRR no teto** (≈0,89) comprime a faixa do TRIMP e reduz seu poder
   discriminativo entre sessões/atletas — a PSE tem mais variância útil aqui.
3. **FCmax/FCrepouso são proxies de campo** (máx/mín observados), não medidas de
   laboratório; a normalização por atleta pode introduzir ruído.

Em resumo: as sessões foram uniformemente quase-máximas por FC, a carga por FC e
por PSE medem coisas diferentes neste regime, e nenhuma das duas prevê a resposta
aguda de humor — reforçando que o humor responde a fatores além do custo
fisiológico da sessão. Figura: `trimp_figuras.png`.
