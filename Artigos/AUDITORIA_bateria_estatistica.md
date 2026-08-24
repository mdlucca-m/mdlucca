# Auditoria da bateria estatística (omnibus · post hoc · Dunnett · tipo de dia)

Computado do dado real anonimizado (`silver.mood` + `silver.wellbeing`), no nível
**atleta-dia** (média das respostas do dia), com **casos completos** (atletas com
os 7 dias: **n = 19** de 27). Tudo determinístico (sementes fixas) e materializado
em `gold.an_bat_*` para reauditoria. Sementes: bootstrap e simulação de Dunnett com
`seed = 7`.

> **Nota sobre a amostra.** Dos 27 atletas, apenas **19 têm os 7 dias**. Toda ANOVA
> de medidas repetidas exige desenho balanceado, então a análise abaixo usa esses 19.
> Um segundo cenário (imputar os dias ausentes pela média do dia, para chegar a n = 27)
> é reportado onde muda a conclusão, porque **a imputação pela média do dia infla o F**
> (reduz artificialmente a variância de erro) e provavelmente explica os números mais
> altos descritos na solicitação.

## Veredito por afirmação

| # | Afirmação auditada | O que o dado real reproduz | Veredito |
|---|---|---|---|
| 1 | **Descritivas** — média, DP, EPM, IC 95% por bootstrap, mediana, quartis, amplitude, % de piso, assimetria e curtose, 11 var × 7 dias | Todas computadas; 77 linhas em `an_bat_desc` | **Confirma** |
| 2 | **ANOVA-RM (Mauchly + Greenhouse-Geisser) e Friedman (W de Kendall) concordam integralmente** | Concordam em **11/11** variáveis quanto a haver ou não efeito de dia | **Confirma** (a concordância) |
| 3 | **Sete variáveis têm efeito de dia** | **Seis** (casos completos): fadiga física, vigor, tensão, confusão, Epworth e fadiga. Chega a 7 (entra a PTH) só no cenário imputado n = 27 | **Não bate** (6, não 7) |
| 4 | **Fadiga física lidera (F = 14,51; η²ₚ = 0,446)** | **Lidera, sim.** F = **13,0**; η²ₚ = **0,42** (n = 19). No cenário imputado n = 27: F = **20,85**; η²ₚ = **0,445** | **Ranking confirma; F não bate** |
| 5 | **Seguida de vigor (F = 11,26; η²ₚ = 0,385)** | **É a 2ª, sim.** F = **6,34**; η²ₚ = **0,26** (n = 19); F = **7,77**; η²ₚ = **0,23** (n = 27 imputado) | **Ranking confirma; F não bate em nenhum cenário** |
| 6 | **Post hoc: 21 pares × 7 métodos** (bruto, Tukey, Bonferroni, Holm, Šidák, Benjamini-Hochberg, Conover-Iman + Holm) | Os 7 métodos computam e estão em `an_bat_posthoc` (126 linhas para as 6 variáveis significativas) | **Confirma** (computável) |
| 7 | **Dunnett vs basal: vigor, fadiga e fadiga física diferem em 6 dias; tensão e confusão em 5** | Muito mais conservador: **vigor 3/6, fadiga 1/6, fadiga física 4/6, tensão 0/6, confusão 2/6** (máx.\|T\| sob t-multivariada, ρ = 0,5, n = 19) | **Não bate** |
| 8 | **Por tipo de dia: todo contraste significativo tem o basal de um lado; HIIT, jogo e técnico não se separam entre si** | Verdadeiro para fadiga, fadiga física e tensão. **Vigor e confusão mostram também HIIT × jogo** (Wilcoxon bruto, sem correção) | **Parcial** |

## O que sai da auditoria

**A metodologia é toda legítima e reproduzível.** Descritivas completas, dupla via
omnibus (paramétrica com correção de esfericidade e não paramétrica), os sete
métodos de post hoc e o Dunnett de medidas repetidas por simulação foram todos
executados sobre o dado real e ficam gravados no gold.

**As conclusões estruturais se sustentam:** as duas vias omnibus concordam; a
**fadiga física é o marcador com maior efeito de dia** e o **vigor vem em seguida**;
a esfericidade é violada na maioria das variáveis (Mauchly p < 0,05), o que torna a
correção de Greenhouse-Geisser não só apropriada como necessária; e os contrastes
por tipo de dia são dominados pelo eixo **basal vs demais**.

**Os números exatos descritos na solicitação não se reproduzem** a partir da análise
defensável em casos completos. Em particular:

- **F = 14,51 / η²ₚ = 0,446 (fadiga física)** e **F = 11,26 / η²ₚ = 0,385 (vigor)**
  são mais altos do que o dado permite (13,0 / 0,42 e 6,34 / 0,26). O η²ₚ da fadiga
  física coincide com o cenário **imputado n = 27** (0,445), o que sugere que os
  números da solicitação vieram de um tratamento que **completa os atletas ausentes**;
  esse caminho, porém, **infla o F** e não é o mais conservador.
- O **Dunnett** descrito (quase todos os dias diferindo do basal) corresponderia a um
  teste **sem ajuste** ou a um n bem maior; o Dunnett de medidas repetidas com
  controle do erro-família rende bem menos contrastes.

## Recomendação

Adotar o cenário **casos completos (n = 19)** como resultado principal, por ser o
mais conservador e sem imputação, e **relatar explicitamente o n**. Se o objetivo
for aproveitar os 27 atletas, o caminho correto não é imputar pela média do dia
(que infla o F), e sim um **modelo misto** (`statsmodels` MixedLM já disponível no
projeto), que acomoda dados desbalanceados sem inflar a significância. Posso montar
essa versão e recolocar os números lado a lado.

Tabelas de apoio no lakehouse: `an_bat_desc`, `an_bat_omnibus`, `an_bat_posthoc`,
`an_bat_dunnett`, `an_bat_daytype`. Reprodução: `python -c "import audit_battery as A; A.run()"`.

## Atualização: os dois caminhos, resolvidos (n = 19, n = 27 e modelo misto)

Materializei os **três caminhos** em `gold.an_two_*` e no painel (aba *Dois caminhos*)
e no documento ABNT (Seção 5). Resumo:

| Caminho | Amostra | Variáveis com efeito de dia | Fadiga física | Vigor |
|---|---|---|---|---|
| Casos completos (sem imputação) | n = 19 | **6/11** | F = 13,0 · η²ₚ = 0,42 | F = 6,34 · η²ₚ = 0,26 |
| Imputado pela média do dia | n = 27 | **7/11** | F = 20,9 · η²ₚ = 0,45 | F = 7,8 · η²ₚ = 0,23 |
| **Modelo misto (sem imputação)** | n = 27 | **7/11** | χ² = 102,2 · p < 0,001 | χ² = 52,7 · p < 0,001 |

**Resolução:** o "sete variáveis" **se sustenta** com a amostra cheia — o **modelo misto**,
que não imputa nada, também acusa a sétima (a **PTH** cruza o limiar com os 27 atletas).
Logo, não é artefato de imputação. O que **não se reproduz** são os **valores exatos de F**
descritos originalmente (14,51 / 11,26): o η²ₚ da fadiga física bate com o cenário imputado
(0,45 ≈ 0,446), mas o F imputado é 20,9 (não 14,51), e o vigor não bate em nenhum caminho.
A imputação pela média **infla o F** (encolhe o erro) sem elevar o η²ₚ, por isso deve ser
evitada como base de inferência. **Recomendação:** relatar n = 19 como principal e o
**modelo misto** como via correta para aproveitar os 27.
