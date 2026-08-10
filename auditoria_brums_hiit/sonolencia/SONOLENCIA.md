# Sonolência — o item "Sonolento" do BRUMS

**Sim, a sonolência foi medida** — ela é o item **"Sonolento"** (`fadiga_3`), o
terceiro item da subescala **Fadiga** do BRUMS (junto de Esgotado, Exausto e
Cansado). E ela se comporta de um jeito que merece destaque: **anda na contramão
dos outros itens de fadiga**. Reproduzível: `python sonolencia.py`.

## A/B. Resposta aguda — a sonolência CAI, a exaustão SOBE

| Item de Fadiga | Pré → Pós | Δ | dz | p (Wilcoxon) |
|---|---|---|---|---|
| Esgotado | 1,07 → 1,83 | +0,76 | +0,74 | <0,001 |
| Exausto | 1,13 → 1,78 | +0,65 | +0,84 | <0,001 |
| Cansado | 1,43 → 2,01 | +0,58 | +0,54 | 0,006 |
| **Sonolento** | 1,08 → 0,81 | **−0,27** | **−0,55** | 0,007 |

Os três itens de exaustão **aumentam** significativamente após o treino (dz +0,54
a +0,84), como esperado. Mas a **sonolência DIMINUI** de forma igualmente
significativa (dz −0,55): logo após o exercício os atletas estão **menos
sonolentos** — o exercício agudo é **ativador/despertador** (aumenta o alerta),
ainda que eleve a exaustão física. Sonolência e fadiga, portanto, **não são a
mesma coisa** no plano agudo: exercício ↑ exaustão, mas ↓ sonolência.

## C. A sonolência é descolada dos demais itens de fadiga

Correlação de medidas repetidas (intra-atleta) do Sonolento:

| Sonolento × | r |
|---|---|
| Esgotado | +0,00 |
| Exausto | +0,03 |
| Cansado | +0,10 |
| Vigor | −0,12 |

O item Sonolento é **praticamente ortogonal** aos outros itens de fadiga
(r ≈ 0,00–0,10) — não sobe nem desce junto com a exaustão dentro do mesmo atleta.
A associação (fraca) mais coerente é negativa com o Vigor (−0,12): mais sonolência,
menos energia.

## D. Remover a sonolência melhora a subescala Fadiga

| Subescala Fadiga | α de Cronbach |
|---|---|
| Com Sonolento (4 itens) | 0,795 [0,76; 0,82] |
| **Sem Sonolento (3 itens)** | **0,897 [0,88; 0,91]** |

A confiabilidade da subescala Fadiga **salta de 0,80 para 0,90** quando o item
Sonolento é removido. Isso confirma, por outra via, o que a AFC e a TRI já
apontavam: o item Sonolento tem **carga fatorial baixa (0,35)** e **discriminação
TRI baixa (a = 0,56)** — é o item que **enfraquece** a subescala Fadiga.

## Leitura

A sonolência (item "Sonolento") é o **caso mais claro de má-medida do
instrumento** neste contexto: comporta-se de forma oposta e independente dos demais
itens de fatiga, porque captura um construto diferente — o **eixo sono↔alerta**, e
não a exaustão. Do ponto de vista fisiológico, faz sentido: o HIIT ativa
agudamente (adrenalina, temperatura, arousal), reduzindo a sensação de sono ao
mesmo tempo em que aumenta a exaustão física. Do ponto de vista psicométrico, o
item deveria ser tratado à parte da subescala Fadiga (ou reavaliado). É uma
recomendação concreta de medida que emerge do estudo — e um lembrete de que
**"cansado" e "com sono" não são sinônimos** para o atleta pós-treino.

> Observação: não houve escala dedicada de sonolência/sono (Epworth, Karolinska,
> PSQI) na coleta — a sonolência está disponível apenas como este item do BRUMS.
> Uma escala específica de sonolência/qualidade do sono seria um acréscimo natural
> em coletas futuras.

Figura: `sonolencia_fig.png` (A: Δ pré→pós dos 4 itens; B: dz por item; C: rm_corr do Sonolento; D: α da Fadiga com vs sem Sonolento).
