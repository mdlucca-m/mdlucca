# Auditoria e reprodução independente das análises — Estudo BRUMS/HIIT (handebol)

**Artigo auditado:** ARTIGO_CORRIGIDO_20260724 (versão 24/07/2026)
**Data:** 2026-07-29 · **Revisão final:** reprodução ampliada + correções aplicadas
**Método:** reconstrução independente da base analítica a partir da coleta bruta (COLETAS.xlsx →
aba *Diário*) e da carga interna (HIIT_FC_PSE.xlsx → *Dados A×S*), com recálculo em Python
(pandas/numpy/scipy/statsmodels/factor_analyzer/pingouin) e comparação célula a célula às 58 tabelas,
ao texto e ao resumo.

**Resultado global: 84 checagens — 77 conferem exatamente; 7 foram reconciliadas/corrigidas** (todas
documentadas abaixo e no Apêndice B do manuscrito auditado). Nenhuma correção altera as conclusões do
estudo.

---

## 1. Reproduz a partir dos dados brutos (recálculo independente)

| Bloco | Alvo | Status |
|---|---|---|
| Amostra | 27 atletas · 456 obs · 135 pares · n por dia (27,26,26,21,23,22,21) | ✅ exato |
| Descritivas (Tab. 2) | média/DP/mediana/IQR/assimetria/curtose/piso | ✅ (piso do PTH corrigido) |
| Confiabilidade (Tab. 3/5) | α de Cronbach + r inter-item (6 subescalas) | ✅ exato |
| Itens (Tab. 7) | M/DP/assimetria/piso/item-total (24 itens) | ✅ |
| Correlações (Tab. 11/45; Fig. 4) | subescalas × externas e concorrentes | ✅ |
| Fatorial (Tab. 4) | KMO 0,835 · Bartlett · autovalores | ✅ |
| Efeito do dia (Tab. 18/19/50) | ICC de atleta · médias diárias (2 passos e por obs.) | ✅ |
| Perfis (Tab. 20) | iceberg % e perturbado % por dia | ✅ exato |
| HIIT nível do dia (Tab. 25) | médias/diferenças por observação | ✅ exato |
| HIIT nível do dia (Tab. 48/55) | médias/dz/Wilcoxon-FDR por dia (2 passos) | ✅ exato |
| Variância traço/dia/estado (Tab. 37) | decomposição em 3 níveis | ✅ exato |
| Resposta aguda (Tab. 22) | p corrigido por atleta (todas as subescalas) | ✅ exato |
| Multivariada (Tab. 23/§4.13.6) | Hotelling T² 6 sub. (F=2,52;p=0,054;D=0,83) e eixo (F=5,59;p=0,010;D=0,66) | ✅ exato |
| PERMANOVA (Tab. 23) | pré/pós e HIIT (direção + significância) | ✅ |
| Carga interna (Tab. 46/47/53) | FC de pico, FC pós, deriva, ICC/CV/Friedman | ✅ |

**Confirmação de agregação:** o contraste HIIT vs. técnico-tático no nível do dia reproduz **exatamente**
sob duas ponderações — por observação (**Tab. 25**) e por dia, em dois passos (**Tab. 48/55**). Não são
erros: são a mesma comparação sob pesos diferentes, e ambas convergem (menor vigor, maior fadiga/PTH no
HIIT). Notas de esclarecimento foram acrescentadas às legendas.

---

## 2. Correções e reconciliações aplicadas ao manuscrito (Apêndice B)

1. **Resposta aguda (Tab. 22).** dz intra-sujeito por observação adotado = **0,76** para a fadiga física
   (IC 95% [0,60–0,95]), coerente com o Resumo; o 0,71 anterior era o *d de Cohen*. A coluna de **p
   corrigido por atleta** (que reproduz exatamente) foi mantida.
2. **%piso do PTH (Tab. 2).** 21,9 → **“—”** (o PTH varia de ~−16 a +52; não tem piso em zero).
3. **PSE final (Tab. 46/47/53).** 8,5/8,5/9,1 → **9,3/9,3/9,6** (média da 4ª/última série, conforme o
   método). O aumento do PSE **entre** as sessões **não é significativo** (Friedman **p = 0,45**, não
   0,004): o esforço final fica próximo do teto da escala. A queda da **FC de pico** entre sessões
   permanece significativa (Friedman p = 0,001).
4. **Deriva cardíaca (Tab. 46/53).** Esclarecido na legenda: é a subida total da FC entre a 1ª e a 4ª
   série (≈ 3× a inclinação por série citada no texto).
5. **Referência duplicada** (Terry et al., 2022, BRUMS-LTU) removida; menção em §4.13.3 alinhada ao novo dz.

---

## 3. Integridade dos dados (documentado no Apêndice B)

- Campo **“Data” autoinformado corrompido** (contém datas de nascimento); o dia foi derivado do
  **carimbo de data/hora**. O banco já traz a flag “Alerta de Data = Verificar”.
- **37 grafias de nome → 27 atletas** (acentuação/caixa) — exige chave canônica.
- **1 coleta em 29/04** (fora da janela) excluída → **456** observações.
- A “Base Unificada BRUMS” está **reordenada** — merges devem usar chave, não índice de linha.

---

## 4. Análises que exigem replicação em R (não reexecutadas em Python)

Dependem de estimadores específicos e devem ser conferidas pelos scripts originais:
AFC/comparação de modelos/bifatorial (Tab. 8, 9, 35, 36 — lavaan WLSMV), invariância (Tab. 12, 13 —
semTools), TRI/GRM (Tab. 15–17 — mirt), HTMT policórico (Tab. 10 — semTools; a versão Pearson mantém
todos < 0,85) e o fechamento bayesiano (Tab. 30 — BF sensíveis à agregação exata dos deltas). A
hierarquia de evidência bayesiana foi reproduzida qualitativamente (Confusão favorece H0).

---

## 5. Conteúdo desta pasta

- `RELATORIO_AUDITORIA.md` — este relatório.
- `Auditoria_BRUMS_HIIT.xlsx` — workbook para o orientador (dados limpos, verificação com cores, tabelas recalculadas).
- `ARTIGO_AUDITADO.docx` — manuscrito com todas as correções e o Apêndice B de reprodutibilidade.
- `verificacao.csv` — as 84 checagens (reportado × recalculado × status).
- `scripts/clean_data.py`, `scripts/reproduce.py` — pipeline reproduzível.

> As bases originais não são versionadas (dados identificáveis). Os scripts leem os `.xlsx` do diretório
> em `BRUMS_DATA_DIR`; as saídas usam atletas anonimizados (A01–A27).
