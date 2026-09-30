# Atualização — poluição do ar, idoso, atividade física

Material de apoio para atualizar a revisão de mapeamento publicada:

> Andrade, A. et al. (2023). Effects of Air Pollution on the Health of Older
> Adults during Physical Activities: Mapping Review. *Int. J. Environ. Res.
> Public Health*, 20, 3506. <https://doi.org/10.3390/ijerph20043506>
> Busca original concluída em 12/06/2022.

## O que tem aqui

- **`relatorio_completo_atualizacao.docx`** — análise comparativa (artigo
  original × atualização), crescimento ano a ano da produção científica,
  síntese redigida dos artigos novos, e a tabela de extração completa (116
  estudos: 58 originais + 58 confirmados), nas mesmas colunas das Tabelas
  4–6 do artigo publicado.
- **`triagem_28_mantidos.json`**, **`triagem_68_incertos_pubmed.json`**,
  **`triagem_108_incertos_scopus_wos.json`** — os três lotes de triagem por
  resumo real (via PubMed), em ordem cronológica de execução. Juntos somam
  204 registros com decisão (`manter`/`incerto`/`excluir`) e justificativa
  PECOS.
- **`triagem_12_pendentes_resolvidos.json`**, **`triagem_3_novos_mantidos.json`**
  — um quarto lote, adicionado depois: dos 40 registros mantidos por título
  (passo 2 abaixo), 12 nunca tinham sido efetivamente lidos por resumo real
  nem recebido decisão — ficaram pendentes por uma falha de execução, sem
  registro em nenhum arquivo. Resolvidos agora: 3 confirmados (`manter`,
  dados de extração em `triagem_3_novos_mantidos.json`), 6 incertos (falta
  confirmar recorte etário — coortes tipo UK Biobank/painéis domiciliares
  gerais, sem subanálise de idosos no resumo) e 3 excluídos (um deles,
  Cassilhas et al. 2022, é uma **duplicata** do estudo #41 já presente no
  artigo original — a busca da atualização redevolveu um registro que já
  fazia parte do corpus publicado). Ver `triagem_12_pendentes_resolvidos.json`
  para a decisão e justificativa de cada um.
- Somando os quatro lotes: 28 + 3 = 31 confirmados vindos do grupo mantido
  por título, mais 26 + 1 = 27 confirmados vindos dos incertos com resumo —
  **58 confirmados no total**, que entram na tabela de extração do relatório
  acima.

## O que isto NÃO é

**Isto não é uma decisão de triagem da revisão.** Cada registro nestes
arquivos foi lido e classificado por um agente de IA (Claude) contra os
cinco critérios PECOS da Tabela 2 do artigo original — não por um avaliador
humano cadastrado. O sistema do LAPE já tem um fluxo próprio de triagem com
dois avaliadores e consolidação de conflito (`scripts/lape/revisao.py`,
tela `/triagem`), desenhado de propósito para não fechar uma decisão sem
confirmação humana. Estes arquivos são **sugestão para acelerar essa
triagem**, não substituto dela — cada decisão aqui ainda precisa passar por
um avaliador humano antes de contar como decisão da revisão.

## Metodologia, resumida

1. Busca da atualização rodada com `lape_agent.py biblioteca --atualizar
   --code poluicao_idosos_af` (PubMed + Scopus + Web of Science) — 1.873
   registros publicados desde o corte original.
2. Triagem por título contra os critérios PECOS: 1.501 excluídos, 40
   mantidos, 332 incertos.
3. Dos 332 incertos, 68 tinham PMID direto (base PubMed) e 108 vieram do
   Scopus/Web of Science mas também estavam indexados no PubMed (achados
   por conversão DOI→PMID) — os dois lotes ganharam acesso ao resumo real
   e foram reclassificados. Os outros 156 incertos seguem sem resumo
   acessível a partir deste ambiente.
4. Os confirmados (31 do grupo mantido por título + 27 promovidos dos
   incertos) foram extraídos campo a campo (país, idade, sexo, tipo de
   atividade física, poluentes, ambiente, desfecho, achado) a partir do
   resumo real — nunca do texto completo, que segue dependendo de acesso
   institucional. Onde o resumo não informava um campo, ele ficou marcado
   `"NR"` (not reported); nenhum dado foi inferido.

## Limitações a levar em conta

- Extração feita só com o **resumo**, não o texto completo — idade, sexo e
  instrumento de atividade física ficam `"NR"` em boa parte dos 58 (ver
  seção 3 do relatório para os números exatos).
- 162 registros seguem sem decisão final confirmável a partir deste
  ambiente: 156 dos 332 incertos por título nunca tiveram resumo acessível
  (nem Scopus, Web of Science, CrossRef, Unpaywall ou Semantic Scholar
  respondem a chamadas diretas aqui), e mais 6 do quarto lote leram o
  resumo mas ficaram `incerto` por falta de confirmação do recorte etário
  (coortes gerais tipo UK Biobank, sem subanálise de idosos declarada).
  Todos dependem de acesso institucional ou leitura humana para fechar.
- As 6 bases do protocolo original ainda não rodadas nesta atualização:
  CINAHL, Cochrane, Embase, LILACS, PsycINFO, SPORTDiscus.
- O quarto lote (`triagem_12_pendentes_resolvidos.json`) existe porque 12
  dos 40 registros mantidos por título nunca chegaram a ser processados na
  primeira passada — um erro de execução, não uma decisão. Achado e
  corrigido ao montar a Figura 1 (fluxograma PRISMA-ScR) para este mesmo
  material.
