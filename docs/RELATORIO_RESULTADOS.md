# Relatório de resultados em ABNT

`data/RESULTADOS_HUMOR_HANDEBOL.docx` traz apenas os resultados que o
orientador pediu, em documento autônomo.

```bash
python3 scripts/resultados/gerar_relatorio.py -o data/RESULTADOS_HUMOR_HANDEBOL.docx
python3 scripts/resultados/verificar_relatorio.py data/RESULTADOS_HUMOR_HANDEBOL.docx
python3 scripts/resultados/verificar_estilo.py data/RESULTADOS_HUMOR_HANDEBOL.docx
```

## Estrutura

Oito seções, seis tabelas e seis figuras, com cerca de 3.000 palavras de texto
descritivo.

| Seção | Tabela | Figura |
|---|---|---|
| 1 Delineamento e momento da coleta | | |
| 2 Caracterização da carga de treino | Tabela 1 | Figura 1 |
| 3 Trajetória diária do humor | Tabela 2 | Figura 2 |
| 4 Resposta aguda ao treino | Tabela 3 | Figura 3 |
| 5 Comparação entre dias de HIIT e dias de volume | Tabela 4 | Figura 4 |
| 6 Perfis de humor | Tabela 5 | Figura 5 |
| 7 Carga interna nas sessões de HIIT | Tabela 6 | Figura 6 |
| 8 Recomendações para a comissão técnica e para os atletas | | |

## Formato

**ABNT NBR 14724.** A4 retrato, margens de 3 cm à esquerda e no topo e 2 cm à
direita e embaixo, Times New Roman 12, entrelinha 1,5 no corpo, recuo de 1,25
cm na primeira linha. Tabelas em apresentação tabular, isto é, sem bordas
laterais, com traço no topo, sob o cabeçalho e no rodapé. Título acima e fonte
abaixo, tanto em tabelas quanto em figuras. Notas e fontes em espaço simples e
corpo 10.

**Figuras.** Fundo branco, sem nenhuma linha de grade, sem moldura superior nem
direita, 300 dpi. A paleta passou pelo validador de acessibilidade cromática
(`scripts/validate_palette.js` da skill de visualização) e atende aos critérios
de separação para daltonismo e de contraste. Cada série carrega marcador
próprio, além da cor, o que preserva a leitura em impressão monocromática.

**Restrições de redação.** Nenhum travessão e nenhum gerúndio, verificados por
`verificar_estilo.py` sobre as 3.689 palavras do documento gerado. O
verificador distingue gerúndio verbal de palavras terminadas em `-ndo` que não
são gerúndio, como "quando", "segundo" e "mundo".

## As análises estatísticas explicadas

O texto não apenas reporta os números: explica por que cada método foi
escolhido e o que mudaria sem ele.

- **Modelo linear misto** com intercepto aleatório por atleta, para as médias
  diárias. Justificado pela estrutura aninhada dos dados e pelo
  desbalanceamento entre atletas, que contribuíram com três a sete dias.
- **Correção da pseudorreplicação** por agregação das diferenças por atleta
  antes do teste. O texto quantifica o custo de ignorá-la: com correlação
  intraclasse próxima de 0,60 e cerca de 17 observações por atleta, o efeito
  de desenho é de aproximadamente 10,5, de modo que o conjunto equivale a
  cerca de 43 observações independentes.
- **Dupla convenção de tamanho de efeito**, com o dz padronizado pelo desvio
  intraindividual e o d de Cohen pelo desvio total, e a explicação de por que
  aplicar os cortes clássicos ao dz produz interpretação inflada.
- **Intervalos de confiança por bootstrap de clusters**, com 2.000
  reamostragens de atletas inteiros, que preservam a dependência intra-atleta.
- **Correção de Benjamini-Hochberg** para as nove comparações.
- **Confirmação multivariada** por duas vias independentes: Hotelling T²
  pareado e PERMANOVA com permutação restrita ao atleta.
- **Fatores de Bayes JZS**, que quantificam a força da evidência de forma
  independente do valor de p.
- **Efeito piso** reportado por subescala e ligado à ausência de resposta, com
  a decomposição de variância entre traço e estado como segunda via de
  explicação.
- **Diferença em diferenças e E-values** para o efeito específico do HIIT, que
  não sobrevive a essa análise.

## Origem dos dados

Todo valor vem de uma tabela do `Artigo_Final_`, e a nota de cada tabela
declara a origem. Nenhum número foi estimado.

| Tabela do relatório | Origem no artigo |
|---|---|
| 1 Carga por dia | Esquema 1 e seção 3.3 (conteúdo, sessões, duração); Tabela 48 (FC, PSE); Tabela 19 (humor) |
| 2 Médias diárias | Tabela 19; inclinações da Tabela 64 |
| 3 Resposta aguda | Tabela 23; efeito piso da Tabela 2 |
| 4 Por tipo de dia | Tabela 27; diferença em diferenças da Tabela 65 |
| 5 Perfis | Tabelas 20 e 21 |
| 6 Sessões de HIIT | Tabelas 48, 55 e 68 |

Nos dias sem HIIT a frequência cardíaca e a percepção de esforço constam como
`n.d.`, porque a seção 3.4 do artigo declara que foram registradas apenas nas
sessões de HIIT. A lacuna fica visível em vez de preenchida por estimativa.

## Conferência visual pendente

A conversão para PDF não pôde ser feita aqui: o LibreOffice deste ambiente
falha até com um `.docx` mínimo. A validação de esquema OOXML passa, e as 38
verificações estruturais confirmam formato, conteúdo e estilo, mas a
conferência da paginação impressa continua pendente.
