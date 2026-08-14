# Amplitude, ruído e sinal — o que oscila de verdade no microciclo (21–28/04/2024)

> Duas perguntas do orientador respondidas de forma quantitativa: **(1) qual a amplitude** (range) das variáveis na semana; **(2) quanto dessa oscilação é sinal do microciclo e quanto é ruído**. Reanálise independente em Python (numpy, scipy, statsmodels) sobre a base bruta (27 atletas, 456 observações). Atletas anonimizados (A01–A27).

---

## 1. Como separei ruído de análise (método)

Toda observação de humor é **sinal + traço + ruído**. Decompus a variância de cada variável por um modelo de dois fatores `y ~ atleta + dia` (soma de quadrados tipo I), obtendo três parcelas que somam 100%:

| Parcela | O que é | É "análise" ou "ruído"? |
|---|---|---|
| **Sinal do microciclo** (efeito do dia) | a trajetória sistemática que os 7 dias impõem ao grupo | **Análise** — é o fenômeno de interesse |
| **Traço** (entre atletas) | diferenças individuais estáveis (quem é sempre mais fatigado) | **Análise**, mas de outra natureza (quem, não o quê) |
| **Ruído** (resíduo) | erro de medida + flutuação aleatória intra-atleta | **Ruído** — o que não se deve interpretar |

Do ruído derivam os limiares de decisão:
- **ETM** (erro típico de medida) = DP do resíduo = **piso de ruído**.
- **MDC95** = 1,96·√2·ETM = mudança mínima **detectável** acima do ruído (para 1 atleta, 1 coleta).
- **MDC95 do grupo** = MDC95/√n — o ruído da **média** de ~27 atletas encolhe por √n.
- **SWC** = 0,2·DP-entre-atletas = mudança mínima **relevante** (critério de Cohen).

A regra é simples: **uma variação só é "análise" (sinal) se supera o MDC95; abaixo disso é ruído** e não deve ser interpretada como mudança real.

---

## 2. Amplitude (range) das variáveis

| Variável | min–max | Amplitude total | IQR | **Amplitude do sinal** (trajetória do grupo) | Amplitude intra-atleta (média) |
|---|---|---|---|---|---|
| Fadiga física (0–10) | 0–10 | 10,0 | 3,0 | **3,30** | 6,04 |
| Fadiga BRUMS (0–20) | 0–16 | 16,0 | 5,0 | **3,74** | 8,37 |
| Vigor (0–20) | 0–15 | 15,0 | 4,0 | **2,83** | 7,11 |
| PTH/TMD | −12–52 | 64,0 | 10,0 | **6,24** | 20,11 |
| Fadiga mental (0–10) | 0–10 | 10,0 | 5,0 | 0,92 | 4,96 |
| Raiva | 0–15 | 15,0 | 2,0 | 1,81 | 5,85 |
| Confusão | 0–9 | 9,0 | 0,0 | 0,80 | 2,22 |
| Depressão | 0–16 | 16,0 | 1,0 | 0,84 | 3,00 |
| Tensão | 0–8 | 8,0 | 0,6 | 0,60 | 3,04 |

**Leitura.** A amplitude **total** engana — usa quase toda a escala, mas isso mistura atletas diferentes. O que importa é a hierarquia:

> **Amplitude do sinal < amplitude intra-atleta < amplitude total.** A trajetória do grupo (sinal) move a fadiga física ~3,3 pontos e o TMD ~6,2 pontos na semana. Mas **um atleta individual oscila o dobro** (6,0 e 20,1) — porque a oscilação individual é sinal **+ ruído**. A maior parte do "sobe-e-desce" que se vê no dia a dia de um atleta **não é o microciclo: é ruído** (Fig C).

---

## 3. Quanto é sinal, quanto é traço, quanto é ruído (Fig A)

| Variável | % Sinal (dia) | % Traço | % Ruído | ETM (ruído) | SNR (ampl./ETM) |
|---|---|---|---|---|---|
| **Fadiga física** | **12,0** | 42,3 | 45,7 | 1,64 | **2,02** |
| Vigor | 4,9 | 53,7 | 41,5 | 2,08 | 1,36 |
| Fadiga BRUMS | 4,2 | 58,4 | 37,4 | 2,47 | 1,52 |
| Raiva | 3,5 | 32,3 | 64,2 | 2,27 | 0,80 |
| Confusão | 2,8 | 40,8 | 56,3 | 0,93 | 0,86 |
| PTH/TMD | 2,5 | 61,1 | 36,3 | 6,03 | 1,04 |
| Fadiga mental | 1,3 | 72,9 | 25,8 | 1,48 | 0,62 |

**Leitura.** O sinal do microciclo é sempre a **menor** fatia da variância (1–12%). O grosso é **traço** (32–73%: quem você é) e **ruído** (26–64%). A **fadiga física é a variável com maior fração de sinal (12%) e melhor SNR (2,0)** — confirma-a como o marcador mais limpo do microciclo, coerente com sua maior AUC (0,86) e maior dz agudo (0,97) nos relatórios anteriores. As subescalas negativas (raiva, confusão) são **dominadas por ruído** (>56%) — não há o que interpretar nelas ao longo da semana.

---

## 4. A oscilação supera o ruído? Veredito em dois níveis (Fig B)

O mesmo sinal tem **dois veredictos**, e confundi-los é o erro clássico do monitoramento:

| Variável | Amplitude do sinal | MDC95 **individual** | Supera? | MDC95 **grupo** (÷√n) | Supera? |
|---|---|---|---|---|---|
| Fadiga física | 3,30 | 4,54 | **NÃO** | 0,56 | **SIM** |
| Fadiga BRUMS | 3,74 | 6,84 | **NÃO** | 0,85 | **SIM** |
| Vigor | 2,83 | 5,77 | **NÃO** | 0,71 | **SIM** |
| PTH/TMD | 6,24 | 16,71 | **NÃO** | 2,07 | **SIM** |

> **No grupo, a oscilação semanal é sinal real** — supera o MDC do grupo por **4 a 6×** (e o efeito do dia é significativo, *p* < 0,001 nos modelos mistos). **No indivíduo, a mesma oscilação cabe dentro do ruído** — está abaixo do MDC95 individual. Não é contradição: o ruído da **média** de 27 atletas encolhe por √27 ≈ 5,2. Por isso a leitura **grupal** do microciclo é robusta, mas a **decisão individual** (este atleta piorou?) exige **médias de ≥3 coletas** para baixar o MDC individual até o nível da oscilação — exatamente o que a análise de generalizabilidade já mostrava (Φ ≥ 0,80 com ≥3 coletas).

A Fig D mostra isso visualmente para a fadiga física: a média diária e a LOWESS (sinal) saltam da faixa estreita de IC do grupo, mas **cabem** na banda larga de ruído individual (±MDC).

---

## 5. O movimento é direcional (sinal) ou aleatório (ruído)?

Uma última checagem: a deriva **líquida** da semana (D7−D1) vs o DP do ruído. Se a deriva > 1 ruído, o movimento é direcional, não vaivém aleatório.

| Variável | Deriva semanal \|D7−D1\| | Ruído (DP resíduo) | **Deriva/Ruído** |
|---|---|---|---|
| **Fadiga física** | 3,30 | 1,58 | **2,09** |
| Fadiga BRUMS | 3,74 | 2,38 | 1,57 |
| Vigor | 2,83 | 2,00 | 1,41 |
| PTH/TMD | 5,95 | 5,80 | 1,03 |

A fadiga física acumula **~2 desvios de ruído** de deriva direcional — o sinal mais claro. O TMD acumula ~1 (deriva e ruído quase empatados: seu sinal só emerge por agregação e no salto do Dia 7).

---

## 6. Síntese

1. **Amplitude:** o sinal do microciclo move a fadiga física ~3,3 e o TMD ~6,2 pontos; a oscilação **individual** é ~2× maior porque carrega ruído junto.
2. **Ruído vs análise:** 1–12% da variância é o **sinal do microciclo**, 32–73% é **traço estável**, 26–64% é **ruído**. A **fadiga física** tem o melhor sinal (12%, SNR 2,0); as subescalas negativas são ruído.
3. **Regra de decisão:** interprete a variação **do grupo** livremente (sinal 4–6× o ruído da média); para o **indivíduo**, só confie em mudanças acima do **MDC95 individual** (≈4,5 na fadiga física, ≈17 no TMD) — ou use **médias de ≥3 coletas** para reduzir esse limiar.
4. **Direcionalidade:** a fadiga física é o único marcador cuja deriva semanal supera 2× o ruído — o mais confiável para "ler" o acúmulo.

---

*Reprodutibilidade: `scripts/analise/amplitude.py` · figuras 4K em `Artigos/figuras/amp_*.png` · página interativa `Artigos/Amplitude_Ruido_Sinal.html`. Consistente com `Analise_Estatistica_Consolidada.md` (§3 generalizabilidade Φ, §5 dz agudos, §9 ROC).*
