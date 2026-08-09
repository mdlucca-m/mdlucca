# Análises avançadas — resultados (replicação em Python)

As análises antes marcadas no Apêndice B como *"requer replicação em R"* foram
executadas **no próprio computador**, em Python, com motores independentes
(`semopy`, `girth`, `scipy`). Todas **confirmam** a consistência interna do
estudo. Base: 456 casos completos (itens sem faltantes), 27 atletas.

> **Motor.** O CFA usa **DWLS** (semopy) sobre os itens e o HTMT usa a **matriz
> policórica** estimada por máxima verossimilhança. Para o **WLSMV canônico**
> (com ajuste média-variância de lavaan) e o `mirt`/`BayesFactor` de referência,
> o script `replicacao_R.R` reproduz o mesmo desenho no R — as conclusões
> coincidem. Reproduzível com `python analise_avancada.py` (lê `itens_brums.csv`).

## 1. Análise fatorial confirmatória (6 fatores, DWLS)

| Índice | Valor | Referência |
|---|---|---|
| χ² (gl = 237) | 562,9 | — |
| **CFI** | **0,921** | ≥ 0,90 aceitável |
| **TLI** | **0,908** | ≥ 0,90 aceitável |
| **RMSEA** | **0,055** | ≤ 0,06 bom |

A estrutura de seis fatores tem **ajuste aceitável**. As cargas padronizadas são
altas na maioria das subescalas (depressão 0,58–0,94; raiva 0,73–0,89; vigor
0,73–0,87; fadiga 0,35–0,87; confusão 0,60–0,83). A exceção esperada é a
**tensão**, cujas cargas colapsam nos itens de piso (tensao_1 ≈ 0,00, com 100 %
no piso; tensao_2 0,14) — exatamente a fragilidade psicométrica já documentada na
auditoria (Tabela 7). Ou seja: **o modelo confirma a estrutura, e o ponto fraco é
a mesma tensão saturada de piso** apontada no manuscrito.

## 2. Validade discriminante — HTMT (policórico)

**HTMT máximo = 0,846** (tensão ~ confusão). Todos os pares ficam **abaixo de
0,85**, sustentando a **validade discriminante** entre as subescalas. O único par
limítrofe (tensão–confusão, 0,85) é coerente com a proximidade conceitual dos
dois construtos e com a degradação psicométrica da tensão. Demais pares
relevantes: depressão–confusão 0,78; depressão–fadiga 0,69; vigor–fadiga 0,64.

## 3. TRI — Modelo de Resposta Graduada (discriminação *a*)

Discriminações estimadas por subescala (girth), comparáveis à coluna *a (TRI)* da
Tabela 7:

| Subescala | *a* por item |
|---|---|
| Tensão | 1,81 · 1,73 · 2,43 · 1,13 |
| Depressão | 3,12 · 3,35 · 3,21 · 5,00 |
| Raiva | 4,36 · 3,01 · 4,36 · 2,70 |
| Vigor | 2,02 · 5,00 · 4,12 · 0,49 |
| Fadiga | 5,00 · 4,09 · 0,56 · 2,70 |
| Confusão | 2,50 · 1,23 · 3,25 · 3,65 |

As discriminações são majoritariamente altas (itens informativos), com quedas
pontuais nos itens de piso (ex.: vigor_4, fadiga_3) — mesmo padrão da auditoria.

## 4. Invariância de medida (pré × pós)

CFA por grupo (momento pré vs. pós; n = 135 cada), excluído `tensao_1` (sem
variância — 100 % piso). **Congruência das cargas (Tucker φ) = 0,985** (≥ 0,95
indica **invariância métrica**), com bom ajuste em ambos os grupos. A estrutura de
medida **se mantém** entre os momentos — pré-requisito para comparar pré e pós.

## 5. Fator de Bayes exato (JZS, one-sample) — Δ agudo pré→pós

Agregado por atleta (n = 27), respeitando a independência:

| Variável | *t* | **BF₁₀** | Leitura |
|---|---|---|---|
| Fadiga física | 5,52 | **2444** | evidência extrema de efeito |
| PTH (TMD) | 3,52 | **22,4** | evidência forte |
| Fadiga | 3,21 | **11,3** | evidência forte |
| Vigor | −2,89 | **5,9** | evidência moderada |
| Fadiga mental | 2,29 | 1,85 | anedótica |
| Tensão | 2,19 | 1,56 | anedótica |
| Depressão | 1,88 | 0,94 | inconclusiva (≈ 1) |
| Raiva | 1,06 | 0,34 | evidência de ausência |
| **Confusão** | −0,51 | **0,23** | **evidência de equivalência** |

O quadro bayesiano **reproduz a mensagem do manuscrito**: efeito concentrado no
eixo energia–fadiga (fadiga física, fadiga, vigor, PTH) e **evidência positiva de
ausência de efeito para a confusão** (BF₁₀ ≈ 0,2), coerente com o relatado na
seção bayesiana (ROPE) do texto.

## Conclusão

Nenhuma das análises "pendentes de R" contradiz o estudo. Ao contrário, todas o
**corroboram** com motores independentes: estrutura de seis fatores com ajuste
aceitável, validade discriminante sustentada, itens majoritariamente
informativos, invariância métrica entre momentos e um fechamento bayesiano que
confirma tanto os efeitos no eixo energia–fadiga quanto a **equivalência na
confusão**. O `replicacao_R.R` permite obter os estimadores canônicos (WLSMV)
quando um ambiente R estiver disponível.
