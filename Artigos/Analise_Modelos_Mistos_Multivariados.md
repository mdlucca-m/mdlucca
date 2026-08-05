# Modelos mistos multivariados do eixo energia–fadiga (microciclo 21–28/04/2024)

> **Escopo.** Semana de 21–27/04. Modelagem **conjunta** das quatro variáveis do eixo energia–fadiga (Vigor, Fadiga, Fadiga física, TMD) num único modelo multinível, com respostas padronizadas (z), efeitos fixos específicos por traço e efeitos aleatórios **não estruturados** por atleta (covariância livre entre traços). Formato empilhado (1.824 linhas = 27 atletas × ~17 obs × 4 traços). Reprodutibilidade: `../scripts/analise/mvmixed.py`. Atletas anonimizados.

---

## 1. Por que multivariado

As variáveis do eixo energia–fadiga são **respostas correlacionadas**: analisá-las uma a uma ignora sua covariância, infla o erro tipo I e não revela a estrutura conjunta. O modelo misto multivariado (`resp ~ 0 + traço + traço:preditor`, com efeitos aleatórios não estruturados `traço | atleta`) estima simultaneamente (i) o efeito de cada preditor sobre cada traço e (ii) a **matriz de covariância entre traços no nível do atleta** — o que um atleta "é" no espaço multivariado do humor.

## 2. Modelo 1 — efeito do dia (multivariado)

Os quatro traços movem-se conjuntamente ao longo da semana, todos significativos (Tabela 1): a fadiga física tem a maior inclinação, o vigor a única negativa. O teste **multivariado conjunto** do efeito do dia (LRT do termo `traço:dia`) é esmagador: **χ²(4) = 118,9; p ≈ 9 × 10⁻²⁵** — o perfil de humor **desloca-se** de forma multivariada ao longo do microciclo (contraparte paramétrica da PERMANOVA e do Hotelling).

**Tabela 1.** Inclinação por dia (respostas em z; modelo multivariado).

| Traço | β/dia (z) | *p* | β/dia (bruto)† |
|---|---|---|---|
| Fadiga física | +0,144 | < 0,001 | +0,34/dia |
| Fadiga (BRUMS) | +0,088 | < 0,001 | +0,34/dia |
| Vigor | −0,086 | < 0,001 | −0,27/dia |
| TMD | +0,041 | 0,017 | +0,40/dia |

†β em z × DP do traço (Vigor 3,12; Fadiga 3,89; Fadiga física 2,34; TMD 9,64).

## 3. A estrutura multivariada: correlação entre-atletas

O produto central do modelo é a **matriz de correlação dos efeitos aleatórios de atleta** (Tabela 2) — como os traços se organizam **entre indivíduos**. O padrão é o do eixo energia–fadiga como **dimensão de traço**: quem pontua alto em fadiga (física e do BRUMS) e em perturbação total pontua **baixo** em vigor.

**Tabela 2.** Correlação entre-atletas dos traços (efeitos aleatórios não estruturados).

| | Fadiga física | Fadiga | TMD | Vigor |
|---|---|---|---|---|
| **Fadiga física** | +1,00 | +0,77 | +0,60 | −0,46 |
| **Fadiga** | +0,77 | +1,00 | +0,86 | −0,41 |
| **TMD** | +0,60 | +0,86 | +1,00 | **−0,65** |
| **Vigor** | −0,46 | −0,41 | −0,65 | +1,00 |

**Leitura.** As fortes correlações positivas entre fadiga física, fadiga e TMD (+0,60 a +0,86) e as negativas com o vigor (−0,41 a −0,65) confirmam, no nível do atleta, um **contínuo bipolar energia↔fadiga**. Isto é o que só o modelo multivariado entrega: a fadiga e o vigor não são quatro coisas independentes, mas faces de uma mesma disposição individual — justificativa estatística para tratar o eixo energia–fadiga como a dimensão-alvo do monitoramento.

## 4. Modelo 2 — efeito do HIIT (multivariado)

Restrito aos dias de treino e modelando o efeito do dia-HIIT (vs técnico-tático) por traço conjuntamente (Tabela 3), o deslocamento é significativo no **TMD** e na **fadiga física**, marginal na fadiga e não significativo no vigor — coerente com um efeito de dia-HIIT concentrado na perturbação/fadiga física.

**Tabela 3.** Efeito do dia-HIIT por traço (multivariado; dias 2–7).

| Traço | β(HIIT) (z) | *p* |
|---|---|---|
| TMD | +0,204 | 0,002 |
| Fadiga física | +0,163 | 0,014 |
| Fadiga (BRUMS) | +0,124 | 0,060 |
| Vigor | −0,084 | 0,203 |

## 5. Modelo 3 — crescimento cúbico multivariado

Estendendo o modelo multivariado a um crescimento polinomial (traço-específico), o **termo cúbico (t³) é significativo para os quatro traços conjuntamente** (Tabela 4) — a não-linearidade cúbica documentada nas análises univariadas (subida–alívio–precipitação) **sobrevive** na modelagem multivariada.

**Tabela 4.** Coeficiente cúbico (t³) por traço no modelo multivariado.

| Traço | coef. t³ | *p* |
|---|---|---|
| Fadiga física | +0,0355 | < 0,001 |
| Vigor | −0,0252 | < 0,001 |
| Fadiga (BRUMS) | +0,0229 | < 0,001 |
| TMD | +0,0200 | < 0,001 |

## 6. Síntese e nota de método

O modelo misto multivariado fecha o circuito analítico do microciclo por uma via paramétrica que respeita simultaneamente a **estrutura de medidas repetidas** e a **covariância entre desfechos**:

1. O perfil de humor **desloca-se** ao longo da semana de forma multivariada (LRT p ≈ 9 × 10⁻²⁵), com a fadiga física à frente.
2. A **correlação entre-atletas** confirma o eixo energia–fadiga como **dimensão de traço** (fadiga↔vigor até −0,65) — o alvo natural do monitoramento.
3. O efeito do dia-HIIT concentra-se em TMD e fadiga física.
4. A **não-linearidade cúbica** é multivariada e robusta.

**Limitação de método.** A implementação (statsmodels) estima a covariância multivariada **no nível do atleta** (efeitos aleatórios não estruturados) mas assume resíduos homoscedásticos entre traços na camada de observação; a covariância residual cruzada intra-observação não é separadamente identificada. Um modelo totalmente multivariado (p. ex., `MCMCglmm`/`brms` em R, com resíduo não estruturado) refinaria essa camada — recomendação para a versão confirmatória. As conclusões substantivas (deslocamento multivariado, estrutura de traço, cúbica) são, contudo, estáveis e convergem com PERMANOVA, Hotelling e as análises univariadas.
