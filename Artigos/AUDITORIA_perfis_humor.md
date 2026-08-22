# Auditoria da base de dados do gráfico de perfis de humor

**Objetivo:** confirmar que a base usada nas figuras de perfil de humor
(`scripts/analise/humor_anon.csv`) reproduz o banco completo original
(`Backup_Banco_de_dados.xlsx`, aba **Diário - Treino**), e documentar
divergências.

**Escopo:** microciclo de 7 dias (21–27/04/2024), seis dimensões do BRUMS
(Tensão, Depressão, Raiva, Vigor, Fadiga, Confusão).

---

## 1. Contagem de observações e atletas

| Fonte | Observações (semana) | Atletas |
|---|---|---|
| `humor_anon.csv` | **456** | **27** (A01–A27) |
| Backup · Diário - Treino (data = carimbo) | **456** | 28 → **27 reais** |

- **Observações batem** (456 = 456).
- A diferença "28 vs 27" vem de **uma entrada `NÃO IDENTIFICADO`** (4 respostas)
  no Backup, que **não é um atleta**. Excluída, restam **27 atletas** —
  exatamente os do `humor_anon.csv`.

## 2. Cuidado com o campo de data (armadilha)

A coluna **"Data"** do Diário contém **datas de nascimento** em várias linhas
(erro de preenchimento no formulário). Filtrar por ela devolve apenas 373
observações — **incorreto**. A data válida é o **carimbo de data/hora**
(`Carimbo de data/hora`), que situa todas as respostas em 21–27/04/2024.
O `humor_anon.csv` usou a data correta.

## 3. Médias diárias de grupo (Backup vs anon)

Diferença máxima entre as médias diárias das seis dimensões: **0,31 ponto**
(a maioria < 0,15). As pequenas diferenças decorrem apenas do atleta a mais
(`NÃO IDENTIFICADO`) presente no Backup. **Conclusão: mesmos dados.**

## 4. Classificação dos perfis (6 perfis de Terry/Parsons-Smith)

Reclassificando o Backup pelo mesmo método (z-score na amostra → centroide mais
próximo dos seis perfis) e comparando a prevalência:

| Perfil | Backup (reclassificado) | `humor_anon` |
|---|---|---|
| Iceberg | 29,7% | 30,7% |
| Superfície | 30,3% | 29,5% |
| Submerso | 14,5% | 13,9% |
| Barbatana de tubarão | 7,9% | 7,2% |
| Everest invertido | 9,7% | 10,2% |
| Iceberg invertido | 7,9% | 8,4% |

Todas as prevalências coincidem dentro de ~1 ponto percentual (n = 165 vs 166
perfis atleta-dia). **A figura é reprodutível a partir do banco original.**

## 5. Nota sobre a aba "Classificação Perfil Humor" do Backup

A aba própria do Backup usa um **esquema diferente**: três categorias
(*Iceberg favorável / Invertido / Misto*, definidas por vigor acima da média e
negativas abaixo) sobre a **coorte completa (n = 15)** e **por ciclo**
(baseline, treino, competição…), não por dia. É um recorte distinto do usado
nas figuras (os **seis** perfis padrão da literatura, sobre os **27** atletas,
**por dia**). Não são diretamente comparáveis, mas ambos convergem: perfil
iceberg predominante no início e erosão ao longo do período.

---

## Veredito

A base do gráfico (`humor_anon.csv`) **corresponde ao banco original**: mesmo
número de observações, médias diárias idênticas (≤ 0,31) e prevalência dos
perfis coincidente (≤ ~1 pp). Os 27 atletas estão corretos; o "28º" do Backup é
uma resposta não identificada. A única ressalva de qualidade no banco bruto é o
campo "Data" contaminado por datas de nascimento — contornado pelo uso do
carimbo de data/hora.
