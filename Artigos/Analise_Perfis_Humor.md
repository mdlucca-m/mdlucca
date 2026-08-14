# Análise transversal dos perfis de humor ao longo do microciclo (Parsons-Smith) — 21–28/04/2024

> Classificação de cada observação num dos **seis perfis de humor** (Parsons-Smith et al., 2017): iceberg, iceberg invertido, Everest invertido, barbatana de tubarão, superfície e submerso — por atribuição ao **centroide canônico mais próximo** sobre as seis subescalas padronizadas (z) na amostra. Reanálise independente (Python). 27 atletas, 456 observações. Atletas anonimizados.

---

## 1. Distribuição dos perfis e evolução na semana

**Global:** Iceberg 31,6% · Superfície 31,1% · Submerso 10,3% · Everest invertido 9,2% · **Barbatana de tubarão 9,2%** · Iceberg invertido 8,6%.

**Por dia (%):** a assinatura do acúmulo aparece na migração dos perfis (Fig 1):

| Dia | Iceberg | Barbatana | Superfície | Iceberg inv. | Everest inv. | Submerso |
|---|---|---|---|---|---|---|
| 1 | **40,5** | 2,4 | 26,2 | 9,5 | 14,3 | 7,1 |
| 4 | 30,0 | 8,3 | 35,0 | 10,0 | 8,3 | 8,3 |
| 7 | **17,4** | **28,3** | 28,3 | 6,5 | 8,7 | 10,9 |

**Como o grupo começa e termina a semana.** Começa **saudável** (iceberg 40%, índice-iceberg z = **+0,52**) e termina **fatigado** (iceberg 17%, índice-iceberg = **−0,47**). O achado mais marcante é a explosão da **barbatana de tubarão** — o perfil de fadiga em pico com vigor ainda preservado — de **2% (D1) para 28% (D7)**. A queda do índice-iceberg do D1 ao D7 é significativa (**Mann-Whitney p = 1,5×10⁻³**).

> **Barbatana de tubarão, iceberg invertido, Everest invertido:** o perfil que domina o fim da semana é a **barbatana de tubarão** (fadiga alta com vigor ainda visível) — coerente com fadiga aguda sem colapso afetivo. O **iceberg invertido** (vigor baixo, negativas altas) permanece raro (6–15%), e o **Everest invertido** (pior perfil, tudo negativo alto) até diminui (14%→9%). Ou seja: o grupo **fadiga fisicamente sem desabar emocionalmente** — o custo é somático, não afetivo.

## 2. Pré vs pós — variação dentro do dia

| Momento | Índice iceberg (z) | % Iceberg | % Superfície |
|---|---|---|---|
| **Pré** | +0,20 | 37% | 25% |
| **Pós** | −0,28 | 24% | 33% |

Dentro de cada dia, o treino **piora o perfil**: o índice-iceberg cai e o iceberg cede lugar à superfície (**Wilcoxon, agregado por atleta, p = 0,0005**). A variação intra-dia soma-se ao acúmulo semanal (Fig 3).

## 3. Qual dia tem mais variação?

| Dia | DP entre atletas (índice) | IQR do TMD | \|Δ pré→pós\| médio (TMD) |
|---|---|---|---|
| 1 | 1,40 | 9,0 | 7,60 |
| **6** | **1,43** | 10,0 | **7,75** |
| 7 | 1,39 | 11,8 | 5,06 |

O **Dia 6** apresenta a **maior dispersão entre atletas** e a **maior variação intra-dia (pré→pós)** — um dia técnico-tático de véspera da última sessão de HIIT, em que os atletas divergem mais (uns já muito fatigados, outros ainda recuperados). Contudo, o teste de **Fligner-Killeen** indica que a variância do índice-iceberg **não difere significativamente entre os dias** (estat. = 7,71; **p = 0,26**) — a heterogeneidade é alta em toda a semana, não exclusiva de um dia (Fig 4).

## 4. Relação fadiga física × fadiga mental × fadiga (BRUMS)

| Par | Spearman ρ | rmcorr (intra-atleta) |
|---|---|---|
| **Fadiga física × Fadiga BRUMS** | **+0,68** | +0,64 |
| Fadiga física × Fadiga mental | +0,50 | +0,44 |
| Fadiga mental × Fadiga BRUMS | +0,46 | +0,45 |

E, sobretudo, as **trajetórias divergem** (Fig 5):

| Dia | Fadiga física | Fadiga BRUMS | Fadiga mental |
|---|---|---|---|
| 1 | 4,26 | 3,74 | 4,81 |
| 7 | **7,57** | **7,48** | 5,13 |

**A fadiga física e a fadiga do BRUMS sobem juntas e quase em paralelo (ρ = 0,68), praticamente dobrando na semana; a fadiga mental permanece estável (4,8 → 5,1).** É uma **dissociação**: o custo do microciclo inscreve-se no **corpo** (fadiga física/somática), não na **mente** — o mesmo padrão de preservação afetiva que sustenta o perfil "barbatana" (fadiga alta, mas sem colapso emocional).

## 5. E na última semana de pré-temporada?

O microciclo monitorado **é** a semana final pré-competitiva de choque. Seu desfecho (Dia 7) é o **perfil mais fatigado da série**: iceberg reduzido a 17%, barbatana de tubarão em 28%, índice-iceberg negativo (−0,47) e fadiga física/BRUMS no pico (7,5–7,6/10). Em termos de forma (Fig 6, radar z): no **D1** o vigor projeta-se acima das negativas (**iceberg clássico**); no **D7** o vigor recua e a fadiga sobe ao mesmo nível — o **perfil achata-se**. Este é o retrato psicológico do "pedágio" acumulado do bloco, esperado e reversível pelo tapering subsequente.

## 6. Explicação estatística (síntese)

- **Migração de perfis** (transversal): iceberg↓, barbatana↑ — teste de tendência do índice-iceberg significativo (Mann-Whitney D1×D7 p = 0,0015).
- **Variação dentro do dia:** Wilcoxon pré×pós p = 0,0005 (piora sistemática).
- **Variação entre dias:** Fligner p = 0,26 (variância homogênea; a dispersão é intrínseca à heterogeneidade individual — coerente com o ICC de traço 0,3–0,7).
- **Dissociação da fadiga:** física e BRUMS convergem (ρ = 0,68) e respondem; a mental é preservada — sustenta a leitura de custo somático, não afetivo.
- **Cautela metodológica:** os seis perfis dependem do critério de centroide sobre z **dentro da amostra** (sem normas de escore-T); o predomínio de "superfície/iceberg" é sensível a essa padronização e deve ser lido como **descrição transversal**, não norma populacional.

---

**Referência do método de perfis:** Parsons-Smith, R. L., Terry, P. C., & Machin, M. A. (2017). Identification and description of novel mood profile clusters. *Frontiers in Psychology, 8*, 1958. https://doi.org/10.3389/fpsyg.2017.01958

*Reprodutibilidade: `scripts/analise/profiles.py` · figuras 4K em `Artigos/figuras/perfil_*.png` · página interativa `Artigos/Perfis_Humor.html`.*
