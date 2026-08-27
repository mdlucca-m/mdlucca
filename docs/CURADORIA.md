# Curadoria e geração do manuscrito

Pipeline que aplica os critérios de elegibilidade à biblioteca, gera as tabelas
de resultados dos dados e produz o manuscrito corrigido em ABNT.

```
scripts/
  gerar_manuscrito.py      CLI: produz o .docx corrigido
  testar_curadoria.py      46 verificações
  curadoria/
    psicometria.py         dicionário de 65 instrumentos + famílias de construto
    elegibilidade.py       critérios dos Quadros 1 e 2, com motivo por exclusão
    tabelas.py             Tabelas 1 e 3 a 8, geradas do corpus
    extracao.py            Apêndice B, com alertas de conferência
    referencias.py         NBR 6023 + auditoria de integridade de DOI
  manuscrito/
    correcoes.py           substituições e supressões no texto do original
    secoes.py              seções 4 a 7, com prosa gerada dos dados
```

## Uso

```bash
python3 scripts/gerar_manuscrito.py \
    --original ESTUDO_RS_HANDEBOL_ABNT.docx \
    --db data/BIBLIOTECA_HANDEBOL.sqlite \
    --saida data/ESTUDO_RS_HANDEBOL_CORRIGIDO.docx

python3 scripts/testar_curadoria.py
python3 scripts/auditoria_revisao.py data/ESTUDO_RS_HANDEBOL_CORRIGIDO.docx \
                                     data/BIBLIOTECA_HANDEBOL.sqlite
```

## O corpus

Aplicados os critérios dos Quadros 1 e 2 aos 2.445 registros da biblioteca,
**483 são elegíveis**. Cada exclusão recebe um único motivo, o primeiro
aplicável na ordem do Quadro 2:

| Motivo | n |
|---|---:|
| não mede variável psicológica | 1.476 |
| fora da janela 2006–2026 | 177 |
| população não é de handebol | 177 |
| delineamento inelegível | 113 |
| fora de treinamento ou competição | 19 |
| **elegíveis** | **483** |

Dos 483, **96 nomeiam um instrumento psicométrico** no título, resumo ou
palavras-chave; nos outros 387 o construto é declarado sem que o instrumento
seja nomeado, e a elegibilidade quanto ao eixo Conceito permanece a confirmar
contra o texto completo. As tabelas assinalam essa distinção em vez de
dissolvê-la na contagem.

## Decisões que valem registro

**Ausência de evidência não é evidência de inelegibilidade.** O critério de
contexto exclui apenas quando há evidência positiva de contexto clínico,
escolar ou laboratorial sem vínculo esportivo. Um campo pouco informativo — que
diz só "masculino" — não exclui. É o mesmo princípio que a §3.6 já aplicava aos
registros sem resumo. A primeira versão da regra fazia o contrário e descartava
61 estudos de treino cujo campo de contexto só trazia o sexo da amostra.

**A percepção de esforço não sustenta elegibilidade sozinha.** PSE e Borg são
medidas psicofísicas de intensidade percebida, não psicometria de construto.
Tratá-las como esta última é o que fazia um estudo de carga de treino aparecer
como estudo de motivação, e responde por parte da inflação de 37% apontada no
achado B4.

**O dicionário roda sobre o texto primário, não sobre o campo derivado.** O
campo `instrumentos` da biblioteca agrega rótulos como "Questionário / escala
(genérico)" e "Escala de motivação (SMS/TEOSQ)" — este último não diz qual dos
dois instrumentos foi usado. A detecção corre sobre título, resumo e
palavras-chave, e os rótulos agregados são removidos antes. Por isso a Tabela 5
é um piso: estudos que nomeiam o instrumento apenas na seção de método não são
alcançados.

**Falsos positivos que o dicionário evita.** `TAIS` casava com o português
"tais como"; exige-se agora o nome por extenso ou o acrônimo seguido de
"questionnaire"/"inventory"/"scale". `LSS` casava com a Toxic Leadership Scale,
instrumento diferente.

**Campo duvidoso sinalizado é conferível; campo duvidoso apresentado como valor
não é.** O Apêndice B marca "a conferir" quando o tamanho amostral coincide com
um ano-calendário (`n = 2022` num estudo de temporada inteira) ou quando a
idade média é implausível ou incompatível com o nível competitivo. Das 483
linhas, **308 trazem ao menos um alerta** — e essa é a lista de conferência do
bolsista, não um defeito da tabela.

**PRISMA-ScR, não PRISMA 2020.** O objetivo declarado é mapear a extensão de um
campo, a pergunta está estruturada em PCC, e é a PRISMA-ScR a diretriz
correspondente. Como consequência, a §3.9 deixa de prever avaliação de risco de
viés e passa a caracterização metodológica; e o registro do protocolo migra do
PROSPERO, que não aceita revisões de escopo, para o OSF.

## O que o gerador faz ao original

Reaproveita a prosa que a revisão não questionou — introdução, objetivos, §3.3
a §3.8, §3.10 a §3.12 — e reescreve o resto:

| Onde | O quê |
|---|---|
| §3.1, §3.2, §3.9, §3.10 | PRISMA-ScR; registro no OSF; caracterização no lugar de risco de viés |
| §3.4 | sobreposição Europe PMC/MEDLINE; Google Scholar declarado como verificação de sensibilidade, não como fonte |
| §7 (era §3.7/Quadro 6) | limiar de calibração declarado: AC1 ≥ 0,80 em lote de cinquenta |
| Tabela 1 | substituída pela procedência real dos registros |
| §4 inteira | reescrita sobre o corpus de 483, com a base declarada em cada tabela |
| §4.4 (nova) | integridade dos metadados: 111 dos 483 com pendência de identificador |
| §5, §6, §7 | discussão, limitações e conclusão renumeradas e reescritas |
| Referências | ponto duplo corrigido, periódico em itálico, 5 não citadas removidas (58 → 53) |
| Formato | A4 retrato, margens 3/3/2/2, estilos de título nativos, Resumo/Abstract/Sumário |

O que permanece pendente de decisão humana, e por isso continua marcado no
documento: autoria e instituição na folha de rosto, resumo e abstract,
identificador de registro no OSF, e a discussão e a conclusão definitivas, que
dependem da conferência dos textos completos.

## Verificação

`scripts/auditoria_revisao.py` funciona como teste de regressão: **9
bloqueadores no manuscrito original, 0 no corrigido**. Os nove achados restantes
no documento corrigido são quatro marcadores pendentes de decisão humana e
cinco notas sobre a qualidade dos dados da biblioteca — que o manuscrito agora
declara na §4.4 em vez de omitir.

A auditoria audita o documento, não uma expectativa fixa: lê a base implícita
nos percentuais da Tabela 4 e confere contra a triagem reproduzida; lê a
Tabela 5 e verifica que seus itens são psicométricos; lê a Tabela 4 e reconta
cada família sobre o corpus. Uma tabela editada à mão que deixe de fechar com
os dados aparece como achado.

O `.docx` gerado passa na validação de esquema OOXML. A conversão para PDF não
pôde ser feita aqui: o LibreOffice deste ambiente falha até com um `.docx`
mínimo, de modo que a conferência visual em página impressa continua pendente.
