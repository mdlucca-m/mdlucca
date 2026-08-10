# Análise preditiva — prever o estado pós-treino

Quão bem, e a partir de quê, conseguimos **prever** o estado de humor pós-treino
de um atleta? Diferente das análises anteriores (todas *in-sample*), aqui a
avaliação é **fora da amostra**, com **validação leave-one-athlete-out**
(`LeaveOneGroupOut` agrupado pelo atleta): o modelo nunca vê o atleta que está
prevendo. Isso respeita a estrutura de medidas repetidas e mede a generalização
real para um **atleta novo**. As predições fora-da-dobra são acumuladas e o
R²/AUC é calculado uma única vez sobre elas (pooled). 135 pares pré→pós, 27
atletas. Reproduzível: `python preditiva.py`.

## A. Regressão — previsibilidade do estado pós por conjunto de preditores

R² fora-da-dobra (quanto maior, melhor; negativo = pior que prever a média):

| Preditores | PTH (TMD) | Fadiga física | Vigor |
|---|---|---|---|
| Média global (referência) | −0,07 | −0,04 | −0,06 |
| **Baseline** (o pré do próprio dia) | **+0,37** | **+0,27** | **+0,36** |
| Baseline + contexto (HIIT, dia) | +0,36 | +0,29 | +0,35 |
| Perfil pré completo (todas as subescalas + contexto) | +0,38 | +0,22 | +0,35 |

**O estado pós é modestamente previsível (R² ≈ 0,3–0,4) — e o sinal vem quase
inteiramente da linha de base do próprio atleta.** Sair da "média global" para o
"baseline" é o salto que importa (de R² negativo para ≈ +0,3/0,4). A partir daí:

> **Adicionar o contexto da sessão (HIIT, dia) ao baseline não melhora a previsão:**
> ΔR² = **−0,013** (PTH), **+0,020** (fadiga física), **−0,015** (vigor) — ruído em
> torno de zero. E o perfil pré completo não supera o baseline simples (chega a
> piorar, por sobreajuste). Esta é a **confirmação preditiva** do desacoplamento
> carga↔humor: saber que o dia teve HIIT não ajuda a prever o humor pós **além**
> do que o estado pré do atleta já diz. O que prediz o atleta é o próprio atleta.

## B. Classificação — prever o "dia perturbado" (fadiga física pós ≥ 7)

Alvo binário no corte de Youden do módulo ROC (fadiga física pós ≥ 7; prevalência
60 %). AUC fora-da-dobra (leave-one-athlete-out):

| Modelo | AUC |
|---|---|
| Baseline — só a fadiga física pré (logística) | 0,66 |
| **Perfil pré completo — logística** | **0,70** |
| Perfil pré completo — floresta aleatória | 0,66 |

Dá para antecipar um dia de fadiga física alta com discriminação **moderada**
(AUC 0,70), a partir do perfil de humor pré-treino. A importância relativa
(floresta) coloca **fadiga, estado físico, fadiga mental, tensão e vigor** como
os principais preditores — e o **HIIT como a variável de MENOR importância**
(painel C). Novamente: a antecipação vive no estado de humor do atleta, não no
rótulo da sessão.

## Leitura

A análise preditiva fecha o círculo com o resto do estudo, agora sob o critério
mais exigente (generalização para atleta novo):

1. **O estado pós é previsível, mas modestamente** (R² ≈ 0,3–0,4; AUC ≈ 0,70) — há
   sinal real, não é aleatório.
2. **O preditor é a linha de base individual**, não a carga/contexto da sessão. O
   HIIT não agrega poder preditivo sobre o baseline — desacoplamento confirmado
   fora da amostra.
3. **Implicação aplicada:** para antecipar como um atleta chegará ao fim do treino,
   a informação mais valiosa é o seu **próprio estado pré** (linha de base
   individual) — o que sustenta o monitoramento individualizado por tendência, com
   a fadiga física como sentinela, e não um alerta genérico baseado no tipo de sessão.

> Nota de método: validação leave-one-athlete-out (27 dobras); modelos Ridge e
> RandomForest com padronização em *pipeline* (ajuste só no treino de cada dobra);
> reporta-se o melhor R² entre linear e floresta por célula. R²/AUC calculados
> sobre as predições fora-da-dobra acumuladas. Amostra pequena (n = 135 pares, 27
> atletas): os valores absolutos de R² devem ser lidos como ordem de grandeza, mas
> a **comparação entre conjuntos de preditores** (o ΔR² do contexto ≈ 0) é o
> resultado robusto.

Figura: `preditiva_fig.png` (A: R² por conjunto de preditores; B: AUC do dia perturbado; C: importância das variáveis).
