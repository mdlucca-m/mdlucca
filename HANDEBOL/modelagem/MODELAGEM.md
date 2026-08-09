# Modelagem estatística completa — resultados

Todos os modelos inferenciais do estudo, ajustados de forma reproduzível com o
**atleta como unidade** (efeitos aleatórios) — a correção de pseudorreplicação
que é o eixo metodológico do trabalho. Base: 456 observações, 27 atletas.
Reproduzível com `python modelagem.py` (lê `base_modelagem.csv`, anonimizada).
Motor: `statsmodels` (MixedLM), estimação por máxima verossimilhança.

## A. Resposta aguda pré→pós (modelo misto, intercepto aleatório) + FDR

| Desfecho | b(pós) | dz¹ | p (FDR) | sig. |
|---|---|---|---|---|
| Fadiga física | +1,65 | +1,06 | <0,001 | ✔ |
| PTH (TMD) | +3,47 | +0,68 | <0,001 | ✔ |
| Fadiga | +1,50 | +0,62 | <0,001 | ✔ |
| Vigor | −1,09 | −0,56 | <0,001 | ✔ |
| Fadiga mental | +0,57 | +0,44 | 0,005 | ✔ |
| Tensão | +0,20 | +0,42 | 0,126 | — |
| Depressão | +0,36 | +0,36 | 0,066 | — |
| Raiva | +0,37 | +0,20 | 0,219 | — |
| Confusão | −0,04 | −0,10 | 0,716 | — |

Sobrevivem à correção FDR exatamente as variáveis do **eixo energia–fadiga**
(fadiga física, fadiga, vigor, PTH) mais a fadiga mental. Tensão, depressão,
raiva e confusão não sobrevivem — como no manuscrito.

> ¹ *dz agregado por atleta* (DP das médias-por-atleta das diferenças). É maior
> que o *dz por observação* da Tabela 22 (fadiga física 0,76), que usa a DP dos
> ~135 pares. Os dois são válidos e diferem apenas no denominador (nível de
> agregação); a significância e o sinal coincidem.

## B. Acúmulo no microciclo (crescimento com inclinação aleatória por atleta)

| Desfecho | inclinação/dia | p | var. da inclinação (atletas) |
|---|---|---|---|
| Fadiga física | +0,34 | <0,001 | 0,008 (homogênea) |
| Vigor | −0,28 | 0,002 | 0,123 |
| Fadiga | +0,30 | 0,006 | 0,191 |
| PTH (TMD) | +0,46 | 0,088 | **1,13 (alta)** |

O acúmulo de **fadiga física** é robusto e homogêneo entre atletas. Para o
**PTH**, a inclinação média é positiva (+0,46/dia) mas apenas marginal quando se
admitem **inclinações individuais** — e a variância dessas inclinações é grande
(1,13): a perturbação total **acumula de formas muito diferentes entre atletas**.
Isto refina a leitura do manuscrito (que reporta +0,53/dia, p=0,010, com
intercepto aleatório): o efeito médio existe, mas a heterogeneidade individual é
a característica dominante — coerente com a tipologia (20/6/1) e o drill por
atleta do sistema analista.

## C. Efeito do HIIT vs. técnico-tático (nível atleta×dia, dias 2–7)

| Desfecho | Δ (HIIT − sem) | p |
|---|---|---|
| PTH (TMD) | **+2,43** | 0,003 |
| Fadiga | +0,67 | 0,036 |
| Vigor | −0,61 | 0,015 |
| Fadiga física | +0,48 | 0,023 |
| Fadiga mental | +0,19 | 0,318 |

O ΔPTH do HIIT (+2,43) reproduz o valor do manuscrito (+2,47). Nos dias de HIIT o
humor é mensuravelmente mais perturbado — no mesmo eixo energia–fadiga.

## D. Interação Condição × Momento (o HIIT muda a *resposta aguda*?)

| Desfecho | pós × HIIT | p |
|---|---|---|
| PTH (TMD) | +0,18 | **0,910** |
| Vigor | +0,07 | 0,901 |
| Fadiga | +0,70 | 0,283 |
| Fadiga física | +0,93 | 0,035 |

Para o **PTH** não há interação (p=0,910) — confirma o achado central do
manuscrito de que o *salto agudo* pré→pós **não** difere entre HIIT e
técnico-tático (a perturbação vem do nível do dia, não do estímulo agudo
específico). A exceção informativa é a **fadiga física** (p=0,035): o HIIT
amplifica especificamente o custo físico agudo — o que se espera de um estímulo
quase-máximo e que reforça a fadiga física como o marcador mais sensível.

## E. Confirmação multivariada (Hotelling T²)

| Conjunto | F | p | D de Mahalanobis |
|---|---|---|---|
| 6 subescalas | F(6,21) = **2,52** | 0,054 | 0,83 |
| eixo vigor+fadiga | F(2,25) = **5,59** | 0,010 | 0,66 |

As seis subescalas juntas ficam no limiar (p=0,054), mas quando o teste é
focado no **eixo vigor+fadiga** o efeito multivariado é claramente significativo
(p=0,010) — a mudança de humor é real e **concentrada nesse eixo**, não difusa
pelas seis dimensões. Reproduz exatamente o Hotelling do manuscrito.

## Síntese

Os modelos convergem numa história única e coerente: a resposta de humor ao
microciclo de HIIT é **real, aguda e acumulada, e mora no eixo energia–fadiga**;
o *salto agudo* não depende do tipo de treino (só a fadiga física é amplificada
pelo HIIT); e a **heterogeneidade individual** — sobretudo no PTH — é uma
característica de primeira ordem, não ruído. Tudo isso respeitando a estrutura de
medidas repetidas (atleta como unidade), que é a contribuição metodológica
central do trabalho.
