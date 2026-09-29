# Atualização — poluição do ar, idoso, atividade física

Material de apoio para atualizar a revisão de mapeamento publicada:

> Andrade, A. et al. (2023). Effects of Air Pollution on the Health of Older
> Adults during Physical Activities: Mapping Review. *Int. J. Environ. Res.
> Public Health*, 20, 3506. <https://doi.org/10.3390/ijerph20043506>
> Busca original concluída em 12/06/2022.

## O que tem aqui

- **`relatorio_completo_atualizacao.docx`** — análise comparativa (artigo
  original × atualização), crescimento ano a ano da produção científica,
  síntese redigida dos artigos novos, e a tabela de extração completa (113
  estudos: 58 originais + 55 confirmados), nas mesmas colunas das Tabelas
  4–6 do artigo publicado.
- **`triagem_28_mantidos.json`**, **`triagem_68_incertos_pubmed.json`**,
  **`triagem_108_incertos_scopus_wos.json`** — os três lotes de triagem por
  resumo real (via PubMed), em ordem cronológica de execução. Juntos somam
  204 registros com decisão (`manter`/`incerto`/`excluir`) e justificativa
  PECOS. Dos 204, 55 foram confirmados como `manter` — são esses 55 que
  entram na tabela de extração do relatório acima.

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
4. Os 40 mantidos por título + os promovidos dos dois lotes de incertos
   foram extraídos campo a campo (país, idade, sexo, tipo de atividade
   física, poluentes, ambiente, desfecho, achado) a partir do resumo real —
   nunca do texto completo, que segue dependendo de acesso institucional.
   Onde o resumo não informava um campo, ele ficou marcado `"NR"`
   (not reported); nenhum dado foi inferido.

## Limitações a levar em conta

- Extração feita só com o **resumo**, não o texto completo — idade, sexo e
  instrumento de atividade física ficam `"NR"` em boa parte dos 55 (ver
  seção 3 do relatório para os números exatos).
- 156 dos 332 incertos permanecem sem resumo acessível a partir deste
  ambiente (nem Scopus, Web of Science, CrossRef, Unpaywall ou Semantic
  Scholar respondem a chamadas diretas aqui) — dependem de acesso
  institucional feito da universidade.
- As 6 bases do protocolo original ainda não rodadas nesta atualização:
  CINAHL, Cochrane, Embase, LILACS, PsycINFO, SPORTDiscus.
