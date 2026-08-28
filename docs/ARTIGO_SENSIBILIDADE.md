# Artigo curto: sensibilidade do humor ao tipo de estímulo

Arquivo gerado: `data/ARTIGO_SENSIBILIDADE_HUMOR.docx`

## O que o artigo responde

Qual dimensão do humor responde mais a cada tipo de estímulo, e qual delas
separa um estímulo do outro. A PERMANOVA foi retirada por pedido; toda a inferência é descritiva,
univariada e por medidas repetidas. O artigo acompanha também a migração dos
perfis de humor ao longo da semana.

## Desenho da comparação

O microciclo tem sete dias. Os cinco primeiros formam um bloco alternado:

| dia | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|-----|---|---|---|---|---|---|---|
| estímulo | repouso | HIIT | jogo | HIIT | jogo | técnico e tático | HIIT |

A comparação principal usa os dias 2 e 4 como condição HIIT, os dias 3 e 5
como condição jogo e o dia 1 como repouso. O dia 7 também é dia de HIIT, mas
fica fora do bloco porque carrega o acúmulo da semana inteira; ele entra na
Tabela 1 e na descrição do acúmulo, nunca na média da condição HIIT.

## Qual série de médias diárias

O relatório completo traz **duas** séries de médias diárias, e elas divergem:

| série | onde | o que é |
|-------|------|---------|
| estimativa em dois passos | Tabela 19 | agrega primeiro por atleta, depois por dia; corrige a pseudorreplicação |
| média bruta por dia | Tabela 52 | média simples de todas as observações do dia |

O próprio relatório registra a divergência na Nota de reconciliação. Este
artigo usa a **estimativa em dois passos**, que é a série adotada pelo
relatório na seção sobre o comportamento de cada variável ao longo da semana.
A primeira versão deste artigo usava a média bruta; a troca muda os valores e
torna o resultado mais nítido, porque com a série corrigida a PTH nos dias de
jogo fica no valor de repouso.

## Índices da análise de sensibilidade

Todos calculados em `scripts/artigo4p/analise.py` sobre as médias por condição.

| índice | definição |
|--------|-----------|
| resposta ao HIIT | afastamento absoluto da média sob HIIT em relação ao repouso, em % do repouso |
| resposta ao jogo | o mesmo, para os dias de jogo |
| especificidade | diferença absoluta entre a média sob HIIT e a média sob jogo, em % do repouso |

Os três são lidos junto ao W de Kendall (variação entre dias) e ao percentual
de observações no piso da escala, porque uma subescala concentrada no valor
mínimo produz percentuais grandes a partir de variações irrelevantes.

## Resultado principal

| dimensão | resposta HIIT | resposta jogo | especificidade | piso | leitura |
|----------|---------------|---------------|----------------|------|---------|
| PTH | 86% | 0% | 86% | 21,9% | sensor global e discriminante |
| Fadiga | 38% | 30% | 8% | 7,7% | sensor de carga, sem discriminação |
| Vigor | 28% | 26% | 2% | 8,6% | sensor de carga, sem discriminação |
| Tensão, depressão, raiva, confusão | n.a. | n.a. | n.a. | 49,6% a 80,5% | limitadas pelo piso |

A PTH sobe 86% nos dias de HIIT e fica no valor de repouso nos dias de jogo:
é a única variável que informa ao mesmo tempo a magnitude e o tipo do
estímulo. Vigor e fadiga informam a magnitude e não o tipo.

## Migração dos perfis de humor

| critério | dia 1 | dia 7 | diferença |
|----------|-------|-------|-----------|
| Morgan: perfil iceberg | 71,4% | 32,6% | −38,8 p.p. |
| Morgan: humor perturbado | 47,6% | 71,7% | +24,1 p.p. |
| Parsons-Smith: iceberg | 21,4% | 6,5% | −14,9 p.p. |
| Parsons-Smith: superfície | 47,6% | 60,9% | +13,3 p.p. |

A equipe perde o perfil favorável sem migrar para perfis clinicamente
negativos: os quatro perfis restantes movem-se menos de 4 pontos percentuais.
Nos dias de HIIT o índice iceberg cai (dz = −0,64), o eixo vigor e fadiga se
inverte (dz = −0,67) e a PTH sobe (dz = +0,54), com os três intervalos de
confiança afastados do zero.

## Origem dos dados

Nenhum valor é estimado ou inventado. Cada número vem de uma tabela do
conjunto de análises já realizado:

Todas as tabelas citadas são do relatório completo
(`data/ARTIGO_HUMOR_VERSAO_FINAL.docx`).

| dado | origem |
|------|--------|
| médias diárias em dois passos | Tabela 19 |
| efeito do dia no modelo misto (F, eta², p) | Tabela 19 de resultados |
| resposta aguda pré e pós, com IC 95% | Tabela 24 |
| efeito piso por subescala | Tabela 3 |
| ICC(2,1), SEM e MDC entre dias | Tabela 57 |
| perfil de Morgan dia a dia | Tabela 20 |
| perfis de Parsons-Smith | Tabela 21 |
| métricas do perfil em dias de HIIT | Tabela 22 |
| efeito do dia de HIIT por variável | Tabela 52 de resultados |
| mudança confiável atleta a atleta | Tabela 34 |

## Como regerar

```
python3 scripts/artigo4p/dados.py               # confere a série diária
python3 scripts/artigo4p/analise.py             # índices de sensibilidade
python3 scripts/artigo4p/figuras_analiticas.py data/fig4p
python3 scripts/artigo4p/gerar_artigo.py -o data/ARTIGO_SENSIBILIDADE_HUMOR.docx
python3 scripts/artigo4p/verificar_artigo.py data/ARTIGO_SENSIBILIDADE_HUMOR.docx
python3 scripts/resultados/verificar_estilo.py data/ARTIGO_SENSIBILIDADE_HUMOR.docx
```

## Formatação

A4 retrato, margens de 3 cm à esquerda e no topo e 2 cm à direita e embaixo,
Times New Roman 12, recuo de 1,25 cm, tabelas em apresentação tabular com
título acima e fonte abaixo, figuras com legenda acima e fonte abaixo. A
entrelinha do corpo é de 1,0 em vez de 1,5: com 1,5 o conjunto de texto,
quatro tabelas e duas figuras ocuparia seis páginas, e o pedido é de quatro.

Figuras em 300 dpi, fundo branco, sem linhas de grade, todas em painéis
compostos:

| figura | o que mostra |
|--------|--------------|
| 1 | comportamento diário de nove variáveis, com linha de base do dia 1, sentido do desvio preenchido e ajuste linear |
| 2 | média por condição, especificidade e resposta aguda |
| 3 | efeito do dia de HIIT com IC 95% e mudança confiável atleta a atleta |
| 4 | migração diária pelo critério de Morgan, deslocamento entre os perfis de Parsons-Smith e efeito do HIIT sobre o perfil |

Com quatro figuras e cinco tabelas o artigo passa de quatro para cerca de seis
páginas. O corte para quatro páginas exige a remoção de duas figuras.

## Restrições de redação atendidas

Nenhum travessão, nenhum traço de meia risca fora de números e nenhum
gerúndio. Verificado por `scripts/resultados/verificar_estilo.py`.
