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
- **`resumos_reais_98.json`** — para cada um dos 98 registros que seguem
  para o texto completo, o resumo real consultado (ou a fonte, quando só foi
  possível busca web), a decisão e o motivo.
- **`extracao_texto_completo.xlsx`** / **`.json`** e **`relatorio_texto_completo.docx`** —
  fase de texto completo dos 98: tabela de extração (país, desenho, amostra,
  nível, contexto, variáveis de saúde mental com instrumento e momento,
  resultados, decisão após leitura, justificativa, limitação) e o relatório
  com uma ficha por registro. 49 foram lidos no texto completo em acesso
  aberto; os outros 49 só pelo resumo real (editoras pagas ou sites que
  bloqueiam download), o que está marcado em cada ficha.
- **`fontes_texto_completo.json`** — de onde veio o texto completo de cada
  um dos 49 obtidos (URL e número de palavras).
- **`triagem_saude_mental.json`** — os mesmos registros em formato estruturado
  (`autores`, `ano`, `titulo`, `revista`, `doi`, `descricao`, `resumo`,
  `triagem_6_familias`, `saude_mental`, `motivo_saude_mental`), para importar
  no fluxo de triagem do LAPE.

## Resultado

| Decisão (saúde mental)  | Lista dos 183 | 16 confirmados |
|-------------------------|---------------|----------------|
| ENTRA                   | 69            | 7              |
| ENTRA (limítrofe)       | 29            | 0              |
| VERIFICAR               | 0             | 0              |
| NÃO ENTRA (limítrofe)   | 11            | 0              |
| NÃO ENTRA               | 74            | 9              |

## O que isto NÃO é

**Isto não é uma decisão de triagem da revisão.** Cada registro foi lido e
classificado por um agente de IA (Claude) a partir das descrições e resumos já
presentes no arquivo original, contra o critério de saúde mental escrito na
seção 2 do documento. Os 98 registros que seguem para o texto completo e os
11 que tinham ficado em VERIFICAR tiveram o resumo real (ou o texto completo)
consultado em fontes abertas; os NÃO ENTRA partem das descrições já presentes
no arquivo. O fluxo do
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
5. Checagem por resumo real dos 98 que seguem para o texto completo
   (`resumos_reais_98.json`): 96 confirmados, 2 sem resumo localizado
   (nºs 33 e 113), 8 rebaixados para limítrofe e 1 promovido a ENTRA.
6. Fase de texto completo (`extracao_texto_completo.xlsx`,
   `relatorio_texto_completo.docx`): download do PDF de acesso aberto via
   Europe PMC, Semantic Scholar e sites dos periódicos (49 obtidos, título
   conferido contra o registro); leitura e extração por seis agentes de IA
   em paralelo com esquema único; os 49 sem texto completo foram extraídos
   só pelo resumo real e assim marcados. Resultado: 62 ENTRA, 32 ENTRA
   (limítrofe), 3 NÃO ENTRA (limítrofe) (nºs 175, 179, 187) e 1 NÃO ENTRA
   (nº 169). Onze registros mudaram de decisão em relação à triagem por
   resumo.
