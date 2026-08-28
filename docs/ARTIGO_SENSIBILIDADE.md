# Artigo curto: sensibilidade do humor ao tipo de estímulo

Arquivo gerado: `data/ARTIGO_SENSIBILIDADE_HUMOR.docx`

## O que o artigo responde

Qual dimensão do humor responde mais a cada tipo de estímulo, e qual delas
separa um estímulo do outro. A PERMANOVA foi retirada por pedido; toda a
inferência é descritiva, univariada e por medidas repetidas.

## Desenho da comparação

O microciclo tem sete dias. Os cinco primeiros formam um bloco alternado:

| dia | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|-----|---|---|---|---|---|---|---|
| estímulo | repouso | HIIT | jogo | HIIT | jogo | técnico e tático | HIIT |

A comparação principal usa os dias 2 e 4 como condição HIIT, os dias 3 e 5
como condição jogo e o dia 1 como repouso. O dia 7 também é dia de HIIT, mas
fica fora do bloco porque carrega o acúmulo da semana inteira; ele entra na
Tabela 1 e na descrição do acúmulo, nunca na média da condição HIIT.

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
| PTH | 160% | 57% | 103% | 21,9% | sensor global e discriminante |
| Fadiga | 55% | 47% | 8% | 7,7% | sensor de carga, sem discriminação |
| Vigor | 26% | 26% | 0% | 8,6% | sensor de carga, sem discriminação |
| Tensão, depressão, raiva, confusão | n.a. | n.a. | n.a. | 49,6% a 80,5% | limitadas pelo piso |

A PTH é a única variável que informa ao mesmo tempo a magnitude e o tipo do
estímulo. Vigor e fadiga informam a magnitude e não o tipo.

## Origem dos dados

Nenhum valor é estimado ou inventado. Cada número vem de uma tabela do
conjunto de análises já realizado:

| dado | origem |
|------|--------|
| médias diárias e Friedman | Tabela 6 do relatório de perfil |
| pós-teste de cada dia contra o dia 1 | Tabela 8 do relatório de perfil |
| consistência entre dias (ICC) | Tabela 7 do relatório de perfil |
| resposta aguda pré e pós, corrigida | Tabela 23 do relatório completo |
| efeito piso por subescala | Tabela 2 do relatório completo |

## Como regerar

```
python3 scripts/artigo4p/figuras.py data/fig4p
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

Figuras em 300 dpi, fundo branco, sem linhas de grade. As duas figuras são
painéis compostos: a Figura 1 traz as sete dimensões em grade e a Figura 2
reúne médias por condição, especificidade e resposta aguda em três quadros.

## Restrições de redação atendidas

Nenhum travessão, nenhum traço de meia risca fora de números e nenhum
gerúndio. Verificado por `scripts/resultados/verificar_estilo.py`.
