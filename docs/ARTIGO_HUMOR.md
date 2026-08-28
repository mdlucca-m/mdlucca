# Versão final do artigo de humor

`data/ARTIGO_HUMOR_VERSAO_FINAL.docx` é o `Artigo_Final_` com as correções
auditadas aplicadas. O documento foi editado no lugar — descompactar, alterar
`word/document.xml`, recompactar — para preservar as **73 tabelas e 67
imagens**. Reconstruí-lo do zero perderia tudo isso.

```bash
python3 scripts/artigo/corrigir_final.py Artigo_Final_.docx \
        -o data/ARTIGO_HUMOR_VERSAO_FINAL.docx
python3 scripts/artigo/verificar_final.py Artigo_Final_.docx \
        data/ARTIGO_HUMOR_VERSAO_FINAL.docx
```

A verificação roda como teste de regressão: as dez checagens **falham no
original e passam na versão final**.

## O que foi corrigido

Cada correção é sustentada por outra passagem do próprio artigo.

| # | Correção | O que a sustenta |
|---|---|---|
| 1 | **Tabela 35, linha do Vigor**: “Sobrevive ao FDR: Não” → **Sim** | A Tabela 23 dá `p_FDR = 0,005`; a Figura 42 e duas passagens do texto listam o vigor entre as quatro variáveis sobreviventes. A célula era o único ponto discordante. |
| 2 | **Resumo**: passa a nomear as três subescalas abaixo do critério | A Tabela 3 registra α = 0,65 (confusão) e 0,68 (vigor), além de 0,43 (tensão). O resumo citava só a tensão. Os três ω correspondentes (0,84, 0,79, 0,79) vêm da Tabela 43. |
| 3 | **Tabelas 3, 43 e 56**: cada legenda declara de que coeficiente o SEM e o MDC₉₅ derivam (α, ω, ICC) | As três reportavam a mesma grandeza com valores diferentes, sem dizer a origem. |
| 4 | **Tabela 56 designada referência** para decisão individual | O MDC₉₅ é limiar de decisão prática; com três valores por subescala o leitor não sabe qual aplicar. O da Tabela 56 parte da estabilidade teste-reteste. |
| 5 | **Tabelas 19 e 52**: cada legenda declara o estimador e remete à nota | Reportam a mesma média diária com valores diferentes (PTH no Dia 3: 2,87 e 4,5). |

## O que foi sinalizado, não corrigido

Três pontos exigem voltar aos dados brutos. A nova **seção 4.16 — Nota de
reconciliação** os registra no corpo do artigo, com os valores em conflito e o
que precisa ser feito. Nada foi inventado para fechar conta.

**O número de observações.** O Esquema 1 descreve uma coleta no Dia 1
(baseline) e coletas pré e pós nos Dias 2 a 7 — no máximo **13 por atleta**, e
com 27 atletas, **351**. O manuscrito reporta **456**, e o próprio esquema
estampa “27 atletas · 456 observações válidas”. Tomando os 135 pares pré→pós
declarados chega-se a 270 observações pareadas mais os baselines, ainda abaixo
do reportado. É preciso publicar o fluxo de dados e reconciliar o denominador.

**Qual MDC₉₅ vale.** Para a tensão o limiar varia de 1,83 a 3,69 conforme o
coeficiente — um fator de dois numa decisão clínica. A escolha editorial da
Tabela 56 como referência precisa de confirmação dos autores.

**As médias diárias.** “Dois passos” não é definido em nenhum ponto do
manuscrito, e a divergência com a Tabela 52 não é explicada.

## O que examinei e concluí estar certo

Vale registrar, porque a primeira leitura sugeriu problema onde não havia:

- **A diferença de `dz` do vigor (0,39 × 0,45) já é explicada pelo artigo** —
  o `dz` da Tabela 23 é agrupado por observação (135 pares) e inclui a
  variância entre atletas; o da Tabela 34 é agregado por atleta. O texto diz
  isso explicitamente. Não é contradição.
- **Numeração impecável** — 70 tabelas, 59 figuras e 4 quadros, todos
  sequenciais, sem lacunas nem repetições, e **todos citados no texto**.
- **O enquadramento do HIIT é honesto no corpo** — o Quadro 4 conclui
  “inconclusivo” para as quatro variáveis e a Tabela 65 mostra a
  diferença-em-diferenças não significativa (p 0,255–0,845). O artigo afirma
  que “o salto agudo intrassessão não é atribuível ao HIIT”. A ênfase do
  título é mais forte que a evidência, mas a seção 3.3 declara o
  confundimento entre volume e modalidade. Deixei o título como está: mudá-lo
  é decisão editorial dos autores, não correção de erro.

## Contexto

Este arquivo é uma de seis versões em circulação, e não é a mais recente — ver
`scripts/humor/comparar_versoes.py` e a comparação publicada. As outras cinco
carregam problemas que esta não tem, entre eles tamanhos de efeito sem
correção de pseudorreplicação. A recomendação permanece: adotar esta versão e
arquivar as demais.
