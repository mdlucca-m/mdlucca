# Mapeamento handebol e psicologia — triagem por saúde mental

Material de apoio para a revisão de mapeamento sobre variáveis psicológicas em
atletas de handebol no treino e na competição. Parte do arquivo
`INCLUIDOS_MAPPING_HANDEBOL.md.docx` (16 confirmados em texto completo, 183
incluídos por resumo, 28 excluídos) e aplica a ele o critério de **saúde
mental** pedido na instrução de trabalho ("os que tiverem algum desfecho com
saúde mental e handebol selecionar para a próxima fase").

## O que tem aqui

- **`INCLUIDOS_MAPPING_HANDEBOL_corrigido.docx`** / **`.md`** — o documento
  original corrigido (caixa de texto, DOIs, autores, títulos e periódicos) e
  reorganizado: critério de saúde mental por escrito, síntese numérica,
  protocolo original, tabela dos 28 excluídos, os 16 confirmados e os 183 por
  resumo, cada um com a decisão anterior (seis famílias) e a nova decisão
  (saúde mental) com motivo. A seção 3 do documento lista todas as correções.
- **`triagem_saude_mental.json`** — os mesmos registros em formato estruturado
  (`autores`, `ano`, `titulo`, `revista`, `doi`, `descricao`, `resumo`,
  `triagem_6_familias`, `saude_mental`, `motivo_saude_mental`), para importar
  no fluxo de triagem do LAPE.

## Resultado

| Decisão (saúde mental)  | Lista dos 183 | 16 confirmados |
|-------------------------|---------------|----------------|
| ENTRA                   | 76            | 7              |
| ENTRA (limítrofe)       | 22            | 0              |
| VERIFICAR               | 0             | 0              |
| NÃO ENTRA (limítrofe)   | 11            | 0              |
| NÃO ENTRA               | 74            | 9              |

## O que isto NÃO é

**Isto não é uma decisão de triagem da revisão.** Cada registro foi lido e
classificado por um agente de IA (Claude) a partir das descrições e resumos já
presentes no arquivo original, contra o critério de saúde mental escrito na
seção 2 do documento. Só os 11 registros que tinham ficado em VERIFICAR
tiveram o resumo ou o texto completo consultados em fontes abertas; os demais
partem das descrições já presentes no arquivo. O fluxo do
LAPE tem triagem com dois avaliadores e consolidação de conflito
(`scripts/lape/revisao.py`, tela `/triagem`). Estes arquivos são sugestão para
acelerar essa triagem, não substituto dela.

## Como foi feito

1. Extração do texto do `.docx` e separação em registros (número, referência,
   descrição, resumo, decisão anterior).
2. Correção automática de caixa de texto com lista de siglas e nomes próprios,
   mais correções manuais de referências (ver seção 3 do documento).
3. Definição do critério de saúde mental em duas vertentes (sofrimento psíquico
   e saúde mental positiva), com base no consenso do COI sobre saúde mental de
   atletas (Reardon et al., 2019) e no modelo de duplo contínuo (Keyes, 2002).
4. Aplicação do critério a cada um dos 183 + 16 registros, com motivo por
   escrito. Os 11 casos em que a decisão dependia do texto completo foram
   resolvidos consultando resumo ou texto nas fontes abertas (a fonte está no
   motivo de cada um).
