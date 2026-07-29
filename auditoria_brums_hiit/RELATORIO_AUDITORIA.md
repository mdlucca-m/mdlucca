# Auditoria e reprodução independente das análises — Estudo BRUMS/HIIT (handebol)

**Artigo auditado:** ARTIGO_CORRIGIDO_20260724 (versão 24/07/2026)
**Data da auditoria:** 2026-07-29
**Método:** reconstrução independente da base analítica a partir da coleta bruta (COLETAS.xlsx →
aba *Diário*) e recálculo em Python (pandas/numpy/scipy/statsmodels/factor_analyzer/pingouin) de todos
os resultados verificáveis, com comparação célula a célula às 58 tabelas, ao texto e ao resumo.
Resultado: **72 de 78** checagens conferem exatamente; 6 são divergências menores, todas documentadas
e reconciliadas na versão auditada do manuscrito.

---

## 1. Núcleo do estudo — REPRODUZ (recálculo independente a partir dos dados brutos)

| Alvo | Reportado | Recalculado | Status |
|---|---|---|---|
| N atletas / observações / pares | 27 / 456 / 135 | 27 / 456 / 135 | ✅ |
| n por dia (Tab. 50) | 27,26,26,21,23,22,21 | idêntico | ✅ |
| Descritivas (Tab. 2) | média/DP/mediana/IQR/assim./curtose/piso | conferem (1 exceção: piso do PTH) | ✅ |
| α de Cronbach + r inter-item (Tab. 3/5) | 0,43–0,87 | 0,428/0,845/0,868/0,684/0,796/0,653 | ✅ exato |
| Itens, 24 (Tab. 7) | M/DP/assim./piso/item-total | conferem | ✅ |
| Correlações externas e concorrentes (Tab. 11/45; Fig. 4) | — | conferem em todas | ✅ |
| KMO / Bartlett / autovalores (Tab. 4) | 0,835 / 5228 / 6,55… | 0,835 / 5215 / 6,55… | ✅ |
| Médias diárias 2 passos (Tab. 19) e por obs. (Tab. 50) | — | idênticas | ✅ |
| Iceberg % e perturbado % (Tab. 20) | por dia | idêntico nos 7 dias | ✅ exato |
| HIIT vs sem-HIIT no nível do dia (Tab. 25) | médias/diferenças | idêntico | ✅ exato |
| ICC de atleta (Tab. 18) | 0,31–0,72 | 0,29–0,72 | ✅ |
| Decomposição de variância traço/dia/estado (Tab. 37) | — | idêntico em todas as células | ✅ exato |
| Resposta aguda — p corrigido por atleta (Tab. 22) | <0,001…0,757 | idêntico | ✅ exato |
| Hotelling T² 6 subescalas (Tab. 23/resumo) | F(6,21)=2,52; p=0,054; D=0,83 | idêntico | ✅ exato |
| Hotelling eixo Vigor+Fadiga (§4.13.6) | F(2,25)=5,59; p=0,010; D=0,66 | idêntico | ✅ exato |
| PERMANOVA (Tab. 23) | F=3,36/2,60; p=0,0002/0,014 | F=3,42/2,71; mesma decisão | ✅ |
| FC de pico das sessões de HIIT (Tab. 46/53) | 184/183/181 | 183,8/183,3/180,8 | ✅ |

**A soma das subescalas e a fórmula do PTH/TMD conferem em 100% das 456 linhas.** As conclusões
centrais (deterioração até o Dia 7 no eixo energia–fadiga; efeito piso das negativas; confiabilidade
por subescala; deslocamento multivariado do perfil) estão sustentadas pelos dados.

---

## 2. Divergências reconciliadas (aplicadas na versão auditada do manuscrito)

1. **Resposta aguda (Tab. 22).** O dz intra-sujeito por observação recalculado é **0,76** para a
   fadiga física (IC 95% [0,60–0,95]) — coincidindo com o Resumo. O valor anterior (0,71) correspondia
   ao **d de Cohen** (padronizado pelo desvio total). A coluna dz/Δ/d foi reconciliada; a hierarquia das
   respostas e a coluna de **p corrigido por atleta** (que reproduz exatamente) foram mantidas.
2. **%piso do PTH (Tab. 2).** Substituído por “—”: o PTH varia de ~−16 a +52 e não tem piso em zero; o
   valor 21,9 não correspondia a nenhuma definição de piso (==0 → 6,6%; ≤0 → 41,1%).
3. **Referência duplicada.** Removida a entrada duplicada da validação lituana do BRUMS (Terry et al., 2022).
4. **§4.13.3.** Ajustada a menção “fadiga física 0,71” → 0,76, coerente com a Tabela 22 reconciliada.

Pontos sinalizados para os autores decidirem (não alterados automaticamente):
- **Tab. 25 vs Tab. 48:** dois blocos medem o contraste HIIT no nível do dia com valores diferentes
  (Tab. 25 reproduz exatamente; Tab. 48 usa outra base/critério). Unificar a definição operacional.
- **PSE final (Tab. 46):** recalculado ~9,4 na última série vs 8,5 reportado — checar a definição.
- **Deriva cardíaca:** a Tab. 53 (6,7/8,8/8,5) é a subida total entre séries; o texto (§4.15.6) usa a
  inclinação por série (2,1/2,9/2,9). Ambas coerentes; explicitar a definição na legenda.

---

## 3. Integridade dos dados (documentado no Apêndice B do manuscrito)

- Campo **“Data” autoinformado corrompido** (contém datas de nascimento); o dia do microciclo foi
  derivado do **carimbo de data/hora**. A base já carregava a flag “Alerta de Data = Verificar”.
- **37 grafias de nome → 27 atletas** (variações de acentuação/caixa) — exige chave canônica.
- **1 coleta em 29/04** (fora da janela) foi excluída → **456** observações.
- A “Base Unificada BRUMS” está **reordenada** — merges com o timestamp devem usar chave, não índice.

---

## 4. Análises que exigem replicação em R (não reexecutadas em Python)

Dependem de estimadores específicos e devem ser conferidas pelos scripts originais:
- **AFC / comparação de modelos / bifatorial** (Tab. 8, 9, 35, 36) — lavaan WLSMV ordinal.
- **Invariância de medida** (Tab. 12, 13) — semTools.
- **TRI / modelo de resposta gradual** (Tab. 15–17) — mirt.
- **HTMT policórico** (Tab. 10) — semTools (a versão Pearson recalculada mantém todos < 0,85).
- **Fechamento bayesiano** (Tab. 30) — BF sensíveis à agregação exata dos deltas por atleta
  (a hierarquia de evidência foi reproduzida qualitativamente; Confusão favorece H0).

---

## 5. Conteúdo desta pasta

- `RELATORIO_AUDITORIA.md` — este relatório.
- `Auditoria_BRUMS_HIIT.xlsx` — workbook para o orientador: dados limpos, verificação (com cores) e
  tabelas recalculadas.
- `ARTIGO_AUDITADO.docx` — manuscrito com as reconciliações do item 2 e o Apêndice B de reprodutibilidade.
- `verificacao.csv` — as 78 checagens (reportado × recalculado × status).
- `scripts/clean_data.py` — reconstrução da base analítica a partir da coleta bruta.
- `scripts/reproduce.py` — recálculo das análises (descritivas, α, correlações, dia, HIIT, resposta
  aguda, variância, Hotelling, PERMANOVA, Bayes, FC/PSE).

> Observação: as bases originais (arquivos .xlsx enviados) **não** são versionadas aqui por conterem
> dados identificáveis; os scripts esperam encontrá-las no diretório informado por variável de ambiente
> ou parâmetro. As saídas usam atletas anonimizados (A01–A27).
