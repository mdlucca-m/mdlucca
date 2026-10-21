# Atualização — estados de humor no handebol (revisão sistemática)

Material da atualização, feita em outubro de 2026, da revisão sistemática *Estados de humor em atletas de handebol
no treinamento e na competição* (PCC, PRISMA 2020). A versão anterior tinha 26 estudos e 27 relatórios. A versão
atualizada tem **36 estudos e 38 relatórios**.

## O que tem aqui

- **`revisao_sistematica_humor_handebol_atualizada.docx`** e **`.pdf`** — o texto completo atualizado em ABNT.
  Inclui o fluxograma PRISMA para revisões atualizadas, as tabelas e figuras recalculadas, a extração completa
  (Apêndice A) e os relatórios excluídos ou não recuperados (Apêndice B).
- **`triagem_rodada1_533.json`** — primeira rodada, com a triagem por título e resumo dos 533 registros que
  passaram pela deduplicação e pelo filtro automático. As fontes foram PubMed, Europe PMC (resumo e texto
  completo) e Crossref. Cada registro tem decisão (`incluir`/`dúvida`/`excluir`), motivo em vocabulário fechado e
  trecho de evidência.
- **`triagem_rodada2_191.json`** — segunda rodada, com 191 registros novos vindos do Semantic Scholar (busca
  booleana em lote) e do Dialnet. Foram deduplicados contra a primeira rodada e contra os estudos já incluídos.
- **`extracao_estudos_novos.json`** — extração dos 11 relatórios avaliados no texto completo (N1 a N8 e U049,
  U107, U150), no formulário da revisão.
  - N7 ficou **inelegível**: o instrumento de afeto não tem nome nem validação declarados.
  - N8 entrou pelo resumo, porque os metadados da revista indicam texto em inglês.
  - O N9 (resumo de congresso da mesma amostra de Ratz-Sulyok et al., 2026) não está neste arquivo. Ele é tratado
    como relatório adicional e montado a partir do H34.
- **`excluidos_e_nao_recuperados.json`** — excluídos depois da leitura do texto completo e registros não
  recuperados na segunda rodada.
- **`../busca_humor_2026-10-21/`** — saída do robô `scripts/lape/busca_revisao.py` com as estratégias S1 a S5,
  incluindo as bases Semantic Scholar e Dialnet acrescentadas nesta atualização.

## Números da atualização (PRISMA)

| Etapa | Rodada 1 | Rodada 2 | Total |
|---|---|---|---|
| Registros identificados | 3.572 | 754 | 4.326 |
| Duplicatas removidas | 627 | 267 | 894 |
| Removidos pelo filtro automático (sem handebol com termo de humor ou psicológico) | 2.412 | 296 | 2.708 |
| Triados por título e resumo | 533 | 191 | 724 |
| Excluídos na triagem | 506 | 177 | 683 |
| Procurados para leitura (já incluídos na versão anterior: 14) | 27 | 14 | 41 |
| Não recuperados | 2 | 3 | 5 |
| Avaliados no texto completo | 11 | 11 | 22 |
| Excluídos no texto completo | 4 | 8 | 12 |
| Incluídos (relatórios) | 7 | 3 | 10 |

Na rodada 2, o PubMed e o Europe PMC foram consultados de novo e não trouxeram nenhum registro novo. Por isso a
coluna da rodada 2 soma só o Semantic Scholar (549) e o Dialnet (205).

A busca de citações no OpenCitations acrescentou mais um estudo, Morenas-Aguilar et al. (2023).

Fontes que não responderam e foram declaradas como limitação no texto:
- o OpenAlex, por limite diário sem chave;
- o DOAJ, que estava fora do ar;
- a LILACS e a SciELO, que bloquearam o acesso automatizado;
- a Scopus e a Web of Science, que exigem a chave ou a rede da universidade.

## O que isto NÃO é

**Isto não é uma decisão de triagem da revisão.** A triagem, a leitura do texto completo e a extração foram feitas
por agentes de IA (Claude) contra os critérios do protocolo, com a justificativa e o trecho literal de cada decisão.
O sistema do LAPE tem um fluxo próprio de triagem com dois avaliadores (`scripts/lape/revisao.py`, tela
`/triagem`). Estes arquivos servem como **sugestão para acelerar essa triagem**: cada decisão ainda precisa da
conferência de um avaliador humano antes de contar como decisão da revisão.

Pendências para o avaliador humano:
- Obter o texto de Hemmatinezhad et al. (2012, *International Journal of Sport Studies*, v. 2, n. 3), com 95
  handebolistas e BRUMS segundo uma citação secundária. Com o texto em mãos, o estudo tende a entrar.
- Conferir os estudos incluídos só pelo resumo (Buchheit 2015, Diachenko e Tyshchenko 2025, Obregón Sibón et al.
  2017) e o preprint de Bugten et al. (2026).
- A busca do robô (`../busca_humor_2026-10-21/`: 5.819 passagens, 3.438 distintos) trouxe três títulos sobre
  handebol e emoção que não passaram pelas rodadas acima. São três trabalhos suecos com equipes femininas, sem
  resumo nem DOI no registro:
  - *Emotion, concentration and performance in a Swedish female handball team* (2014);
  - *Emotion and concentration regulation training in Swedish female handball players* (2014);
  - *Emotions and Performance in Elite Women Handball* (2018).

  Pelo título, usam perfis emoção-desempenho do modelo IZOF ou instrumento próprio da equipe, o que tende à
  exclusão por não medirem humor com instrumento declarado. Ainda assim, precisam de triagem.
