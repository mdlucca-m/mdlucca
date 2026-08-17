# Reprodução das análises estatísticas — Perfil de humor (handebol de elite)

Este pacote reproduz, do dado bruto até cada número do artigo, toda a análise
estatística. Serve como **prova de originalidade e integridade dos dados**:
qualquer pessoa com o arquivo original do formulário roda os scripts e obtém
exatamente os mesmos resultados.

## Arquivos

| Script | O que faz |
|---|---|
| `00_ingestao_anonimizacao.py` | Lê o export bruto do formulário, **data cada resposta pelo carimbo automático** (imune a edição), recalcula as escalas item a item e substitui os nomes por códigos **A01–A27**. Gera `humor_anon.csv`. |
| `01_analises_estatisticas.py` | A partir de `humor_anon.csv`, reproduz **todas** as análises: normalidade, Wilcoxon pré→pós e D1→D7, Friedman + W de Kendall, ICC, correlações, perfis de humor + qui-quadrado, MANOVA (escores T), pós-teste, T-CAR e Epworth/PSS. |

## Por que isto comprova a originalidade

1. **Datação inviolável.** Cada observação é alocada ao dia/momento pelo
   *Carimbo de data/hora* automático do formulário — não pela data digitada
   (que continha erros). A janela real (21–27/04/2024) é, assim, verificável.
2. **Pontuação auditável.** As escalas são recalculadas dos itens crus
   (`"2= Moderadamente"` → 2), sem etapas ocultas.
3. **Anonimização determinística.** Os nomes (com grafias inconsistentes) são
   casados aos códigos A01–A27 por sobreposição de tokens com a chave privada.
4. **Reprodutibilidade total.** `01` regenera cada valor do artigo a partir do
   banco anonimizado.

## Dados necessários (mantidos localmente pelo pesquisador)

Coloque na mesma pasta dos scripts (⚠️ **não versione/compartilhe** os dois primeiros):

- `COLETAS_original.xlsx` — export original do formulário (aba `Diario`). **Contém nomes reais.**
- `key.csv` — **chave privada** `code,name` (A01–A27 ↔ nome). **Mantenha em sigilo.**
- `tcar2_features.csv` — desempenho no T-CAR por atleta (já anonimizado, `ID = A01..A27`).

A saída `humor_anon.csv` **não contém nomes** e é a única base que pode ser compartilhada.

## Como rodar

```bash
pip install pandas numpy scipy statsmodels openpyxl
python 00_ingestao_anonimizacao.py      # gera humor_anon.csv
python 01_analises_estatisticas.py      # imprime todos os resultados
```

## Conferência de integridade (opcional)

O script `00` imprime a contagem de respostas por dia — deve ser
**42, 94, 75, 60, 71, 68, 46** (21 a 27/04), totalizando 456 registros brutos;
`01` reduz ao conjunto analítico de **286** observações (baseline único +
pré/pós) e reproduz, entre outros: vigor D1→D7 *dz* = −1,33; fadiga *dz* = +0,78;
MANOVA Wilks λ = 0,181 (p < 0,001); migração de perfis iceberg 48% → 22% e
barbatana de tubarão 4% → 22% (χ² não significativo); sonolência ↔ fadiga
ρ = 0,52.

## Observações honestas

- O Epworth aqui é a **versão de 6 itens** (0–18) constante do formulário — sem
  ponto de corte clínico padrão.
- O limiar do T-CAR em `01` é uma versão simplificada em nível de atleta; o valor
  (~14,9 km/h) coincide com o artigo, mas a AUC exata usa o modelo logístico em
  nível de dia descrito no texto.
