# Revisão crítica — protocolo de revisão sistemática (handebol)

**Materiais revisados**

| Arquivo | Conteúdo |
|---|---|
| `ESTUDO_RS_HANDEBOL_ABNT.docx` | Manuscrito, 214 parágrafos, 15 tabelas/quadros, 58 referências |
| `BIBLIOTECA_HANDEBOL.sqlite` | 2.445 artigos, 5 famílias de variável, 4.433 marcações, 5.804 sub-variáveis |
| `BIBLIOTECA_HANDEBOL.xlsx` | Painel + 6 abas (Todos 2.445; Psicológicas 952) |

Todos os números abaixo são reproduzíveis com
`python3 scripts/auditoria_revisao.py ESTUDO.docx BIBLIOTECA.sqlite`
(28 achados, 9 bloqueadores).

---

## Veredito

O método (seções 3.1–3.12) é sólido e, em pontos específicos, acima da média:
a auditoria de rendimento por bloco de busca (Tabela 2), o tratamento explícito
da instabilidade do kappa (3.7) e a declaração das ausências de cobertura (3.4)
são práticas que a maioria dos protocolos omite. As 58 referências foram
verificadas por amostragem e são reais: segundo o PubMed, 9 dos 12 DOIs
testados resolvem para registros indexados, e os 6 cujos metadados recuperei
conferem com o manuscrito em autores, ano, volume e páginas.

O problema não está no método: está em que **a seção 4 não reporta o corpus
que a seção 3 descreve.** As Tabelas 4 a 7 e o Apêndice B foram calculados
sobre um recorte da biblioteca de 2.445 artigos, não sobre os 914 registros
únicos do fluxo PRISMA. Enquanto isso não for corrigido, os resultados
preliminares não sustentam nenhuma das conclusões da seção 5, e o Apêndice B
não pode ser distribuído ao bolsista como tabela de extração.

---

## Bloqueadores

### B1. Dois corpora diferentes apresentados como um só fluxo PRISMA

A seção 4.1 fecha o PRISMA em **914 registros únicos** (1527 − 613). A seção
4.2 abre com "foram recuperados **952** registros com conteúdo psicológico" e
todas as tabelas seguintes usam essa base. **952 > 914** — é aritmeticamente
impossível que o segundo seja um subconjunto do primeiro.

A origem dos 952 está identificada, e é exata:

```sql
SELECT COUNT(*) FROM artigo_variavel WHERE variavel='psicologicas';  -- 952
```

É o recorte "Variáveis psicológicas" da biblioteca de 2.445 artigos — o mesmo
número que aparece na aba homônima do `.xlsx` (953 linhas − cabeçalho) e no
Painel. Confirmações adicionais de que **toda** a seção 4 vem dessa biblioteca,
e não da busca:

- Tabela 6 (países): Alemanha 88, Espanha 76, Noruega 42, Brasil 30… reproduz
  dígito a dígito `SELECT pais, COUNT(*) … WHERE id IN (recorte psicológico)`.
- Tabela 5 (instrumentos): idem, os 12 valores batem exatamente.
- Tabela 7 (n = 331 textos completos): `tem_texto_completo=1` dentro do
  recorte psicológico = **331**.

**Correção.** Duas saídas, e a escolha é de mérito, não de redação:

1. Recalcular as Tabelas 4–7 sobre os 914 registros do PRISMA — é o que a
   seção 4 promete entregar; ou
2. Manter os números, e reescrever 4.2–4.3 declarando explicitamente que
   caracterizam uma biblioteca auxiliar de 2.445 artigos, **fora** do fluxo
   PRISMA, com o total (2.445), o recorte (952) e o critério de marcação
   declarados. Nesse caso a seção 5 não pode extrair conclusões sobre "o
   campo" a partir dela sem essa ressalva.

### B2. A janela de elegibilidade 2006–2026 é violada pelo corpus reportado

O Quadro 1 fixa a janela em 2006–2026. A biblioteca vai de **1972** a 2026, e
**45 dos 952** registros reportados estão fora da janela.

O texto de 4.2 já reflete isso sem dizer: "725 registros entre 2016 e 2026
contra 182 entre 2006 e 2015" — 725 + 182 = **907**, não 952. Os 45 que faltam
são exatamente os anteriores a 2006, omitidos sem declaração.

### B3. Delineamentos e população inelegíveis dentro do corpus reportado

- **55** dos 952 têm `tipo_estudo` excluído pelo Quadro 2: revisões (19),
  revisões sistemáticas (10), capítulos de livro (18), trabalhos em anais (8).
- **124** dos 952 não mencionam handebol (nem *handball*, *balonmano*,
  *andebol*, *handboll*) em título, resumo ou palavras-chave — embora 3.11
  afirme que a varredura já removeu 136 registros nessa exata condição. A
  varredura descrita não foi aplicada ao corpus que a seção 4 reporta.

### B4. "Conteúdo psicológico" está inflado em ~37%

Pela própria taxonomia de sub-variáveis da base, **354 dos 952** registros
marcados como `psicologicas` **não possuem nenhuma sub-variável psicológica**.
Outros 142 têm apenas construtos psicofísicos ou periféricos (percepção de
esforço, bem-estar, sono, cognição). Sobram **456** com pelo menos um construto
psicológico no sentido do objetivo geral.

As sub-variáveis mais frequentes *dentro* do recorte "psicológico" delatam o
problema: Estresse (185), **Velocidade/Sprint (147)**, Motivação (141),
**Potência/Salto (138)**, Cognição (137), **Resistência aeróbica (109)**,
**Aterrissagem/Joelho/LCA (73)**.

A causa é estrutural: 425 dos 952 artigos carregam de 2 a 5 famílias de
variável simultaneamente, e a marcação `psicologicas` é atribuída ao artigo
inteiro. Só 527 são exclusivamente psicológicos.

### B5. A Tabela 5 não contém instrumentos psicométricos

Rotulada "Instrumentos psicométricos mais frequentes", ela lista, entre os 12
mais frequentes: teste de agilidade Illinois/T/505 (169), PSE/Borg (146),
coleta salivar/sanguínea (70), CMJ (55), sprint com fotocélulas (38),
DXA/bioimpedância (35), analisador de lactato (33), monitor de FC (30),
GPS/LPS (28) e plataforma de força (28). O único item inequivocamente
psicométrico é "Escala de motivação (SMS/TEOSQ)" (36); "Questionário/escala
(genérico)" (391) não informa nada.

O campo `instrumentos` da base lista **todos** os instrumentos do artigo, não
os psicométricos. O objetivo específico (b) — "catalogar os instrumentos
psicométricos e verificar a correspondência entre instrumento e construto
declarado" — não pode ser respondido a partir desse campo. É preciso um campo
`instrumento_psicometrico` derivado de um dicionário controlado (CSAI-2R,
POMS, ACSI-28, TOPS, ABQ, GEQ, PANAS, SMS, TEOSQ…), com a versão e o idioma,
como aliás o Quadro 3 já prevê.

### B6. O Apêndice B não reconcilia com a base

**49 das 80 linhas** da Tabela 9 declaram um `n` diferente do campo `amostra`
da base para o mesmo estudo. Amostra da divergência:

| Estudo (truncado) | `n` no Apêndice B | `amostra` na base |
|---|---|---|
| Effects of Recreational Soccer and Team Handball T… | 31 | n = 10 |
| Integrated monitoring of training and sport perfor… | 13 | n = 2022 |
| Handball small-sided games and running-based high-… | 30 | n = 45 |
| Validity of a reactive agility test for aerobic an… | 13 | n = 17 |
| Characterizing Psychomotor Abilities of Male Handb… | 20 | n = 75 |

E nenhuma das duas versões confere com a fonte. O estudo "Integrated
monitoring…" (Skarbalius, *Front Sports Act Living*, 2026;
[10.3389/fspor.2026.1869707](https://doi.org/10.3389/fspor.2026.1869707), via
PubMed) é um **estudo observacional longitudinal** de uma temporada inteira
(193 dias, 159 sessões, 34 jogos) com jogadoras **semiprofissionais**; o
Apêndice B o classifica como "pré-pós (intervenção)" em nível
"elite/internacional", com n = 13, e a base registra `n = 2022` — o ano da
temporada lido como tamanho amostral.

Outros defeitos na mesma tabela:

- Células truncadas em pleno texto: `Idade = "mean age of"`, `País = "Arabia
  Saudit"`, títulos cortados em 50 caracteres.
- Contradições internas: linha com `n = 30` e `Sexo = "45M / 45F"`.
- Construtos não sustentados pelo registro: "Validity of a reactive agility
  test" recebe construto *motivação*, mas suas variáveis analisadas na base são
  potência, VO₂max, frequência cardíaca e lactato — nenhuma psicológica.
- `Borg`/`RPE scale` mapeado para *motivação* e *burnout e saúde mental*.

Enquanto essa tabela não for reconstruída, ela não pode ir para o bolsista como
referência de conferência (Quadro 6, etapa 6) — ele conferiria contra um alvo
errado.

---

## Graves

### G1. A Tabela 1 e a base entregue descrevem buscas diferentes

| Fonte | Tabela 1 (docx) | `fonte` na base |
|---|---|---|
| PubMed/MEDLINE | 281 | 1875 |
| Scopus | 708 | 240 |
| LILACS | 34 | 147 |
| Web of Science | 308 | 56 |
| Europe PMC | 196 | — |
| ScienceDirect | — (acesso "recusado", §3.4) | **127** |
| **Total** | **1527** ✓ | 2445 |

A seção 3.4 declara que "o acesso programático ao ScienceDirect foi recusado",
mas a base entregue contém 127 registros dessa fonte. E o Europe PMC, que
responde por 196 registros na Tabela 1, não existe na base. Ou a declaração de
3.4 está incorreta, ou a base é de outra execução — e nesse caso a data de
última busca ("2026/08/27", item 7 do PRISMA) não se aplica a ela.

Some-se: o Apêndice A traz **seis** estratégias (PubMed, Scopus, WoS, LILACS,
ScienceDirect, **Google Scholar**), o Quadro 4 fala em "6 consultas", e 4.1
fala em "cinco bases". O Google Scholar nunca é declarado como fonte nem sua
exclusão é justificada.

### G2. Tabela 2 × Tabela 1: 302 contra 281

A linha #11 da Tabela 2 ("ESTRATÉGIA FINAL") rende **302** registros no PubMed;
a Tabela 1 reporta **281** recuperados nessa base. A diferença de 21 não é
explicada. Se decorre do filtro de janela temporal aplicado depois, diga-o na
nota da tabela.

### G3. Contagens internas que não fecham

- Quadro 4: etapa 6 remove 136 → 914 − 136 = **778**; a etapa 7 diz **787**.
- §3.6: "165 permanecem em análise". §3.11: "registros desprovidos de resumo
  (159)". A base tem **168** sem resumo dentro do recorte psicológico (269 na
  biblioteca inteira). Três números para a mesma quantidade.

### G4. A base da Tabela 4 não é declarada nem reproduzível

As porcentagens implicam **n = 344** (95 ÷ 0,276), número que não aparece em
nenhum ponto do manuscrito. Recontando as mesmas famílias sobre a base:

| Família | Tabela 4 | Recontagem na base |
|---|---|---|
| ansiedade e estresse | 95 | 235 |
| motivação | 50 | 141 |
| cognição e atenção | 43 | 137 |
| burnout e saúde mental | 35 | 69 |
| coping e resiliência | 26 | 71 |
| autoeficácia e confiança | 21 | 53 |

Nenhuma base — 952, 914 ou 344 — reconcilia. A nota diz que a contagem recai
"sobre os registros classificados como prováveis inclusões na pré-triagem":
declare esse n, e como a pré-triagem chegou a ele.

### G5. Sinalizações de integridade de metadados nunca reportadas

A própria base marca **`doi_suspeito = 1` em 82 registros** (41 dentro do
corpus reportado). O manuscrito não os menciona. Em paralelo, **39 registros**
têm no DOI um ano que difere do campo `ano` em 2 anos ou mais:

| `ano` | DOI | Título |
|---|---|---|
| 2026 | `10.1016/j.jsams.`**`2006`**`.03.027` | Cooper's 12 Minute Run Systematically Underes… |
| 2025 | `10.1093/eurheartj/ehq025` (EHJ, 2010) | Effects on Cardiac Dimensions and Peak Oxygen… |
| 2024 | `10.1097/BRS.0b013e3181b967ea` (*Spine*, 2009) | Effect of concentric exercise-induced fatigue… |

Há ainda DOI malformado com ponto final (`10.1136/bjsm.2002.004374.`). Isso
importa porque as **2.366 referências ABNT** da base são geradas a partir
desses campos — e **459 delas saem sem volume**. Qualquer referência exportada
de um registro com DOI trocado aponta para outro artigo.

Sugestão: resolver todos os DOIs contra o Crossref, gravar
`doi_verificado`/`doi_divergente` e bloquear a geração de referência para os
divergentes. (Não pude executar essa verificação aqui: a política de rede do
ambiente bloqueia `api.crossref.org` com 403. A verificação por PubMed que
consegui rodar cobriu 12 DOIs e não encontrou problema neles.)

### G6. Ruído de extração nos campos que alimentam as tabelas

- `amostra`: **20 registros** com valor no intervalo de anos-calendário
  (`n = 2022`, `n = 2019`…) — ano lido como tamanho amostral.
- `populacao`: idades absurdas, ex. "feminino; Jovem/Base; **~82 anos**" para
  uma amostra de jovens.
- `desenho_estudo`: **1.473 de 2.445 (60%)** valem "Não especificado no
  resumo" — e é esse o campo que sustentaria o objetivo específico (c).
- `tipo_estudo` mistura tipo de documento (Artigo de periódico 283, Capítulo de
  livro 42) com delineamento (ECR 107, Transversal, Coorte). São dois eixos e
  precisam de dois campos.

### G7. Telemetria inconsistente

`execucoes.texto_integral = 879`, mas `tem_texto_completo = 1` conta **808** e
`texto_completo_arquivo` está preenchido em **808**. O valor 879 é exatamente a
contagem de `fonte_metodos` — provável troca de coluna na rotina que grava o
painel.

---

## Norma ABNT

| # | Achado | Norma |
|---|---|---|
| A1 | Página em **paisagem**, formato Carta (27,9 × 21,6 cm); margem esquerda 2,0 cm | NBR 14724: A4 retrato, margens 3/3/2/2 |
| A2 | **58 de 58** referências com ponto duplo: `BANDURA, A.. Self-efficacy…` | erro de concatenação (também em 4 registros da base) |
| A3 | **Nenhuma** das 58 referências destaca o título do periódico | NBR 6023 exige destaque tipográfico |
| A4 | 5 referências nunca citadas: GOULD (2002), GÜLER (2026), PELLET (2026), RICE (2016), WANG (2024) | NBR 6023: só obras citadas |
| A5 | §4.3 e §5 remetem à "Tabela 6" para práticas de relato; o dado está na Tabela 7 (Tabela 6 é a distribuição geográfica) | — |
| A6 | Faltam Resumo, Abstract, palavras-chave, Sumário e Conclusão. O Quadro 5 lista "Resumo — Parcial" e "7 Conclusão — Pendente", mas a seção 7 real é "Esqueleto do estudo" | NBR 14724 / NBR 6028 |
| A7 | Acentos removidos nas Tabelas 5, 6 e 8 ("Questionario", "generico", "Tunisia", "Polonia", "Franca", "Japao", "Emocoes", "Estresse Psicologico") | descritores MeSH/DeCS precisam ser reproduzidos literalmente |
| A8 | Folha de rosto com `[Autoria]`, `[Instituição]`, `[Cidade, ano]`; 4 blocos `[A PREENCHER]` | — |
| A9 | "Duas décadas completas" para 2006–2026 = 21 anos | — |

Títulos de seção não usam estilos de título do Word — não há como gerar sumário
automático.

---

## Método — pontos a decidir

**M1 (o mais importante).** A seção 3.1 declara **PRISMA 2020**, mas estrutura a
pergunta em **PCC** e define o objetivo como "mapear a extensão de um campo em
vez de estimar o efeito de uma intervenção". Essa é a definição de *scoping
review*, cuja diretriz é a **PRISMA-ScR**. Ou se adota a PRISMA-ScR (e então
3.9 — risco de viés e certeza da evidência — sai, porque scoping reviews não a
fazem), ou se reformula a pergunta em PICO com objetivo de síntese e se mantém
a PRISMA 2020. Manter as duas coisas ao mesmo tempo é o ponto que um parecerista
levantará primeiro.

**M2.** Europe PMC e PubMed/MEDLINE se sobrepõem quase integralmente (o Europe
PMC indexa o MEDLINE). Declará-los como bases independentes infla a contagem de
identificação — a deduplicação resolve o efeito, mas a Tabela 1 deveria
registrar a sobreposição.

**M3.** Verificar no MeSH Browser se `Team Sports` é descritor válido, e
justificar `Mood Disorders` — é descritor clínico e pode não recuperar estudos
de estados de humor em atletas (POMS), que é o alvo pretendido.

**M4.** O texto afirma 62 termos livres no bloco de conceito e 27 no de
contexto; a Tabela 8 lista apenas o vocabulário controlado e os termos de
população. Sem os termos livres, a busca não é reexecutável a partir do
apêndice, o que contraria o que 3.11 promete.

**M5.** A seção 3.7 especifica bem os coeficientes (kappa, PABAK, AC1), mas nem
ela nem o Quadro 6 fixam **limiar de decisão** para a calibração: "concordância
insuficiente" precisa de um valor (ex.: prosseguir só com AC1 ≥ 0,80 no lote de
calibração).

---

## O que está bom e deve ser preservado

- **Introdução** — encadeia teoria (Bandura, Nicholls, Deci & Ryan) →
  instrumentação (CSAI-2R, POMS, ABQ) → nível de grupo (Carron, Morgan) →
  especificidade do handebol, e a justificativa decorre do encadeamento em vez
  de ser afirmada.
- **Tabela 2** — submeter cada bloco isoladamente e quantificar o ganho do
  vocabulário controlado (86 registros, 32% sobre o termo livre) é auditoria de
  busca que quase nenhum protocolo publica. A aritmética confere.
- **§3.7** — reconhecer a instabilidade do kappa sob desbalanço e reportar
  PABAK e AC1 é tecnicamente correto e raro neste nível.
- **§3.5** — declarar a inexistência de descritor MeSH para handebol, com
  verificação no MeSH Browser, e assumir a consequência.
- **§3.6** — não triar registros sem resumo por título isolado é a decisão
  metodologicamente certa.
- **Referências** — são reais. Segundo o PubMed, 9 dos 12 DOIs testados
  resolvem para registros indexados; dos 6 cujos metadados recuperei, os seis
  conferem com o manuscrito em autores, ano, volume e páginas — ŚWIDWA
  ([10.1371/journal.pone.0353879](https://doi.org/10.1371/journal.pone.0353879)),
  RATZ-SULYOK ([10.3390/sports14070289](https://doi.org/10.3390/sports14070289)),
  KIM ([10.3390/sports14040128](https://doi.org/10.3390/sports14040128)),
  FILÓ ([10.3389/fspor.2026.1868532](https://doi.org/10.3389/fspor.2026.1868532)),
  SKARBALIUS ([10.3389/fspor.2026.1869707](https://doi.org/10.3389/fspor.2026.1869707))
  e BAUER ([10.3389/fspor.2026.1765225](https://doi.org/10.3389/fspor.2026.1765225)).
  Os 3 que não resolvem são de periódicos fora do índice, não erros.
- **Deduplicação da biblioteca entregue** — 0 DOIs repetidos, 0 PMIDs
  repetidos, 1 título repetido em 2.445. Limpa.
- **Tabelas 1, 3 e 7** — aritmética interna correta (1527 = soma por base;
  1527 − 613 = 914; todos os percentuais sobre 331 conferem).

---

## Ordem de correção sugerida

1. **Decidir o corpus** (B1). Tudo em resultados depende dessa escolha.
2. Aplicar janela, delineamento e menção ao handebol ao corpus escolhido
   (B2, B3) e reportar o novo n.
3. Separar `instrumento_psicometrico` de `instrumentos`, e a marcação de
   construto no nível do desfecho, não do artigo (B4, B5).
4. Regerar o Apêndice B a partir da base corrigida, com conferência manual dos
   80 primeiros contra o texto completo (B6).
5. Reconciliar a Tabela 1 com a fonte real dos dados e declarar Scholar e
   ScienceDirect (G1, G2).
6. Verificar DOIs contra o Crossref e bloquear referências divergentes (G5).
7. Acertar ABNT: A4 retrato, margens, ponto duplo, destaque do periódico,
   referências não citadas, remissão à Tabela 7 (A1–A5).
8. Resolver PRISMA 2020 × PRISMA-ScR (M1).

Itens 1–4 são pré-requisito para circular o documento; 5–8 são pré-requisito
para submetê-lo.
