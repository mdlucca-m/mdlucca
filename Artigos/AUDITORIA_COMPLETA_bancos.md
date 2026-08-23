# Auditoria completa dos bancos de dados — microciclo 21–27/04/2024

**Fontes auditadas (arquivos enviados):** `Backup — Banco de dados.xlsx`, `Avaliações Handebol São José 2024.xlsx`,
`HIIT_FC_PSE.xlsx`, `resultados_handebol.xlsx`, `Paper1_Humor_ARTIGO_CORRIGIDO_20260820.docx`.

> **Confidencialidade:** os arquivos contêm a aba **Chave (confidencial)** com os nomes reais (A01–A27 → nome).
> Nada com nome real foi copiado para o repositório. Só derivados **anonimizados** (A01–A27) foram salvos.

---

## 1. Intervalo de datas — o microciclo é 21–27/04 (7 dias), não 21–28

- Pelo **carimbo real de envio** (não pela coluna "Data", contaminada por datas de nascimento), as respostas se
  concentram em **21 a 27/04/2024**: 42 · 94 · 75 · 60 · 71 · 68 · 46 = **456 observações**. Há **1** envio isolado
  em 29/04 e **nenhum** em 28/04.
- Os rótulos de aba "Questionários **21–28**/abr" e "Log … **23–29**/04" são rótulos de intervalo; a própria nota de
  origem confirma o filtro válido **21–27/abr, n=456**. **Conclusão: não há um 8º dia (28/04).** O microciclo
  analisado está correto.

## 2. Coorte — 27 atletas (A01–A27)

- O Diário bruto tem **inconsistências de nome** (ex.: "LUÍS/LUIS GUSTAVO", "MTHEUA" para Matheus, "GUSTA"/"GUSTAVO
  PAIVA"), inflando para ~53 grafias distintas, além de 15 nomes com 1 única resposta (participação marginal/duplicatas).
- Após a consolidação pela **Chave**, restam **27 atletas (A01–A27)** com as **456 observações** — exatamente o
  `humor_anon.csv` usado em todas as análises. **A base do estudo está correta e reproduzível.**

## 3. Inventário completo de variáveis (21–27/04, todos os atletas)

| Domínio | Variáveis | n | Cobertura | Já usado? |
|---|---|---|---|---|
| **BRUMS** | Tensão, Depressão, Raiva, Vigor, Fadiga, Confusão, TMD | 456 obs · pré/mid/pós | completo | ✅ |
| **Fadiga percebida** | Física (0–10), Mental (0–10) | 456 | completo | ✅ |
| **Sonolência** | **Epworth (0–24)** | 456 | **100%** | ❌ **NOVO** |
| **Estresse** | **PSS (escala de estresse percebido)** | 456 | **100%** | ❌ **NOVO** |
| **HIIT interno** | FC pré/pós, ΔFC, PSE — por sessão (S1/S2/S3) × fase (aquec.+4 séries) | 390 reg · 26 atletas | completo | parcial |
| **Aptidão** | T-CAR (pico de velocidade / cap. aeróbia) | — | — | ✅ |

**As duas séries psicométricas novas (Epworth e PSS) têm resolução temporal igual à do BRUMS** (uma medida por
envio), 100% preenchidas — prontas para entrar no estudo.

## 4. O que as variáveis novas mostram

**Sonolência (Epworth)** — *sobe com o microciclo e acompanha o eixo da fadiga:*
- D1 **8,8 → D7 11,5** · dz **+0,58** · **p = 0,019**
- Correlações: Epworth × Fadiga **ρ +0,34** (p<0,001); × TMD **ρ +0,37** (p<0,001); × Vigor **ρ −0,23** (p=0,002).

**Estresse (PSS)** — *permanece estável, desacoplado da carga física:*
- D1 **22,7 → D7 21,6** · dz **−0,19** · p = 0,414 (não significativo)
- Correlações: PSS × TMD **ρ +0,24** (p=0,002); × Fadiga ρ −0,04 (ns); × Vigor ρ −0,14 (p=0,073).

**Leitura:** os atletas ficam progressivamente **mais sonolentos** (marcador de recuperação/sono seguindo o acúmulo
de carga), mas **não mais estressados**. Isso reforça a tese central do estudo: **sobrecarga funcional** (erosão do
iceberg no eixo energia–fadiga) **sem quadro de estresse/sofrimento psicológico**. O PSS estável é uma evidência
independente de que o desgaste é físico-energético, não afetivo-negativo.

## 5. Carga interna do HIIT (FC/PSE) — assinatura de acúmulo

Médias por sessão (S1=D2, S2=D4, S3=D7):

| Sessão | FC pré | FC pós | ΔFC | PSE |
|---|---|---|---|---|
| S1 | 121 | 176 | 56 | 6,6 |
| S2 | 120 | 175 | 56 | 6,5 |
| S3 | **112** | 172 | **61** | **7,1** |

Na última sessão (D7) a **FC pré é menor** (chega mais cansado/depletado), o **ΔFC é maior** e a **PSE é a mais alta**
— assinatura clássica de acúmulo de carga ao longo da semana. **Vantagem:** o HIIT usa os **mesmos códigos A01–A27**
do BRUMS, então FC/PSE são **diretamente ligáveis** ao humor por atleta (26 dos 27 têm as duas coisas).

## 6. Armadilhas de qualidade confirmadas (para não repetir)

1. **Coluna "Data" contaminada** com datas de nascimento → filtrar por ela devolve 373 (errado). Usar o **carimbo**.
2. **Nomes com erros de digitação** no Diário bruto → sempre consolidar pela Chave antes de contar atletas.
3. Rótulos de aba ("21–28", "23–29") **não** definem o intervalo real dos dados.

## 7. Veredito

A base do estudo (`humor_anon.csv`: 456 obs, 27 atletas, 21–27/04) **corresponde exatamente aos bancos originais**.
Não há dia 28/04. A auditoria **encontrou dois conjuntos de dados 100% coletados e ainda não usados — Epworth
(sonolência) e PSS (estresse)** — que enriquecem o estudo e sustentam a interpretação de sobrecarga funcional sem
distresse. A carga interna do HIIT (FC/PSE) está disponível e ligável por atleta.

**Derivados anonimizados salvos:** `scripts/analise/humor_epworth_pss_anon.csv` (456×14, com Epworth e PSS) e
`scripts/analise/hiit_fcpse_anon.csv` (390 registros de FC/PSE por sessão×fase).
