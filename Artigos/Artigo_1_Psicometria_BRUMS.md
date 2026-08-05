# Artigo 1 — Qualidade de medida e responsividade do BRUMS em atletas de elite: efeito piso, decomposição traço–estado e limiares para a decisão individual

> **Nota de proveniência.** Este texto é uma **nova análise** dos dados do projeto *Handebol São José 2024* (27 atletas, 456 observações, 24 itens do BRUMS), reexecutada de forma independente em Python (numpy, scipy, statsmodels). Todos os valores abaixo foram recomputados a partir das bases brutas item a item; convergem com — e em vários pontos reproduzem exatamente — os resultados do relatório original, o que confere robustez às conclusões. Atletas anonimizados (A01–A27).

---

## Resumo

**Contexto.** O uso do *Brunel Mood Scale* (BRUMS) no monitoramento de carga pressupõe que o instrumento seja confiável e sensível na população específica — condição raramente verificada com rigor psicométrico contemporâneo. **Objetivo.** Avaliar, num microciclo real de handebol de elite, (i) a estrutura e a fidedignidade do BRUMS sob itens ordinais com efeito piso; (ii) a partição da variância do humor em traço e estado; e (iii) os limiares de erro de medida que condicionam a decisão no nível do atleta. **Métodos.** Análise fatorial exploratória (KMO, Bartlett, análise paralela), comparação de estruturas por fator principal, confiabilidade (α, ω, split-half, item-total), decomposição de variância em três níveis (atleta/dia/estado) por modelo misto, erro-padrão de medida (SEM) e mudança mínima detectável (MDC₉₅), e teoria da generalizabilidade. **Resultados.** A adequação fatorial foi boa (KMO = 0,835; Bartlett χ²(276) = 5.228; *p* < 0,001) e a estrutura de seis fatores superou nitidamente os modelos de 1 e 2 fatores (RMSR 0,131 → 0,086 → 0,028). A fidedignidade foi boa nas subescalas bem distribuídas (Fadiga α = 0,80; Depressão 0,85; Raiva 0,87) e frágil na Tensão (α = 0,43), efeito de piso severo (50–80% no zero nas subescalas negativas). A variância foi dominada pelo **traço** (ICC de atleta 0,26–0,67), e o erro típico excede a menor mudança relevante em todas as escalas — de modo que **uma coleta isolada rende dependabilidade Φ = 0,57**, sendo necessárias **≥ 3 coletas para Φ ≥ 0,80**. O achado central é uma **lei de mensuração**: a magnitude do efeito piso prediz quase deterministicamente a responsividade aguda de cada subescala (|dz| = 0,588 − 0,0063·%piso; *r* = −0,92; R² = 0,85). **Conclusão.** A "não-resposta" das emoções negativas ao treino é, sobretudo, **limitação de mensuração** — não ausência do fenômeno. O monitoramento válido nessa população deve ancorar-se no eixo energia–fadiga, por médias de múltiplas coletas referenciadas à linha de base do próprio atleta.

**Palavras-chave:** psicometria; efeito piso; fidedignidade ordinal; erro de medida; generalizabilidade; monitoramento.

---

## 1. Introdução

O monitoramento subjetivo do humor tornou-se ferramenta padrão na gestão de carga em esportes coletivos, com o BRUMS entre os instrumentos mais usados. Contudo, três problemas de mensuração são sistematicamente ignorados na literatura aplicada: (1) o α de Cronbach é reportado sobre itens ordinais de 5 pontos, o que o enviesa quando a suposição de continuidade é violada; (2) a validade de estrutura e a invariância de medida raramente são testadas na própria amostra; e (3) o erro de medida individual — que determina se uma mudança observada é sinal ou ruído — quase nunca é quantificado. Em populações de elite, esses problemas convergem num fenômeno único: as subescalas negativas do BRUMS tendem ao **piso**, porque atletas saudáveis raramente endossam depressão, raiva ou confusão. A questão que este trabalho endereça é se a consequente "estabilidade" dessas dimensões sob carga é um achado substantivo (o atleta é emocionalmente resiliente) ou um **artefato de mensuração** (o instrumento não consegue registrar variação a partir de um patamar já assentado no zero). Distinguir os dois casos é condição para interpretar corretamente qualquer estudo de monitoramento.

## 2. Métodos

**Amostra e delineamento.** 27 atletas de handebol masculino de primeira divisão (22,2 ± 3,7 anos), avaliados por medidas repetidas ao longo de um microciclo pré-competitivo de sete dias (21–27/04/2024), totalizando 456 observações válidas do BRUMS (24 itens, 0–4) e medidas complementares (fadiga física e mental 0–10, sonolência, PSS).

**Análises.** Adequação fatorial por KMO e teste de esfericidade de Bartlett; número de fatores por **análise paralela de Horn** (500 matrizes aleatórias) sobre autovalores da matriz de correlações. Comparação das estruturas de 1, 2 e 6 fatores por extração de fator principal iterativa, avaliada pelo resíduo quadrático médio da matriz reproduzida (RMSR). Fidedignidade por α de Cronbach, ω de McDonald (cargas de um fator), split-half (Spearman-Brown) e correlação item-total corrigida. Confiabilidade de agregação por ICC(1,1) e ICC(1,7). **Decomposição de variância** em três níveis (estado ⊂ dia ⊂ atleta) por modelo misto REML com intercepto aleatório de atleta e componente de dia. Erro-padrão de medida SEM = DP·√(1 − fidedignidade), mudança mínima detectável MDC₉₅ = 1,96·√2·SEM. **Teoria da generalizabilidade**: dependabilidade Φ = σ²ₐ / (σ²ₐ + (σ²_d + σ²ₑ)/k) para k coletas.

## 3. Resultados

### 3.1 Distribuições e efeito piso

As subescalas negativas concentram a maioria das respostas no escore mínimo, ao passo que vigor e fadiga ocupam bem a escala (Tabela 1). Nenhuma variável é normal (Shapiro *p* < 0,001).

**Tabela 1.** Descritivas e efeito piso por subescala (456 observações).

| Subescala | Média | DP | % no piso |
|---|---|---|---|
| Vigor | 5,70 | 3,12 | 8,6 |
| Fadiga | 5,64 | 3,89 | 7,7 |
| Tensão | 1,39 | 1,84 | 49,6 |
| Raiva | 1,60 | 2,73 | 59,6 |
| Depressão | 1,00 | 2,31 | 67,1 |
| Confusão | 0,45 | 1,19 | 80,5 |

### 3.2 Estrutura fatorial

A adequação foi boa (**KMO = 0,835**; Bartlett χ²(276) = **5.228**; *p* < 0,001). A análise paralela reteve 5–6 fatores (autovalores 6,55; 2,99; 1,97; 1,44; 1,35; 1,10, contra p95 aleatório de 1,51; 1,42; 1,36; 1,31; 1,26; 1,22), acumulando **64,1%** da variância em seis fatores — coincidindo com a estrutura teórica do BRUMS. A comparação de estruturas confirma a multidimensionalidade: o ajuste absoluto melhora monotonicamente da solução de 1 fator (RMSR = 0,131) para a de 6 (RMSR = 0,028), descartando um fator geral único de "humor" (Tabela 2).

**Tabela 2.** Comparação de estruturas (extração de fator principal).

| Estrutura | RMSR | Variância comum |
|---|---|---|
| 1 fator | 0,131 | 24,6% |
| 2 fatores (pos/neg) | 0,086 | 35,0% |
| 6 fatores (teórico) | **0,028** | 54,2% |

### 3.3 Fidedignidade

**Tabela 3.** Fidedignidade e homogeneidade por subescala.

| Subescala | α | ω | Split-half | *r* inter-item | Item-total mín. |
|---|---|---|---|---|---|
| Raiva | 0,87 | 0,91 | 0,89 | 0,62 | 0,66 |
| Depressão | 0,85 | 0,91 | 0,88 | 0,63 | 0,66 |
| Fadiga | 0,80 | 0,87 | 0,79 | 0,47 | 0,22 |
| Vigor | 0,68 | 0,83 | 0,68 | 0,38 | 0,11 |
| Confusão | 0,65 | 0,79 | 0,72 | 0,32 | 0,20 |
| Tensão | 0,43 | 0,69 | 0,59 | 0,16 | 0,11 |

O α da Tensão (0,43) é o único abaixo do critério, com *r* inter-item de apenas 0,16 — reflexo direto do piso: quando quase todos pontuam zero, resta pouca covariância para o coeficiente clássico capturar. Note-se, porém, que o ω baseado em cargas (0,69) é substancialmente maior, sinalizando que a fragilidade é da **soma bruta**, não necessariamente do construto latente — o que recomenda cautela, e não descarte, da subescala.

### 3.4 Traço versus estado, e a precisão da decisão individual

A decomposição de variância revela que o humor é, nesta população, **majoritariamente traço** (Tabela 4): 26–67% da variância situa-se entre atletas (diferenças estáveis), 12–14% no dia, e a fração de **estado agudo** (a única que uma sessão pode mover) é minoritária em quase todas as escalas.

**Tabela 4.** Decomposição de variância em três níveis (%).

| Subescala | Traço (atleta) | Dia | Estado |
|---|---|---|---|
| Depressão | 67,4 | 11,8 | 20,8 |
| Tensão | 67,1 | 12,2 | 20,7 |
| Fadiga | 56,3 | 12,2 | 31,4 |
| Vigor | 52,7 | 13,2 | 34,1 |
| Confusão | 37,7 | 14,4 | 47,9 |
| Raiva | 26,4 | 37,4 | 36,2 |

A consequência prática é quantificada pela agregação e pela generalizabilidade. A confiabilidade de uma coleta isolada é apenas moderada, mas a média semanal é boa a excelente (Tabela 5); e a **dependabilidade Φ** de uma decisão absoluta sobre um indivíduo passa de **0,57** (1 coleta) para **0,80** (3 coletas) e **0,90** (7 coletas) — base quantitativa para nunca decidir a partir de uma leitura única.

**Tabela 5.** Confiabilidade de 1 coleta vs média de 7 dias, e dependabilidade Φ (TMD).

| Subescala | ICC(1,1) | ICC(1,7) | | k coletas | Φ (TMD) |
|---|---|---|---|---|---|
| Depressão | 0,70 | 0,94 | | 1 | 0,57 |
| Tensão | 0,69 | 0,94 | | 2 | 0,73 |
| Fadiga | 0,57 | 0,90 | | 3 | **0,80** |
| Vigor | 0,52 | 0,88 | | 5 | 0,87 |
| Confusão | 0,38 | 0,81 | | 7 | 0,90 |
| Raiva | 0,29 | 0,74 | | | |

### 3.5 A lei do piso: efeito de mensuração prediz responsividade

O resultado que integra o artigo é a relação entre o efeito piso de uma subescala e a magnitude de sua resposta aguda ao treino (|dz| pré→pós agregado por atleta; ver Artigo 2 para a estimação da resposta). A associação é **quase determinística**:

> **|dz| = 0,588 − 0,0063 × (%piso);  *r* = −0,92;  R² = 0,85**

Fadiga (7,7% no piso) e Vigor (8,6%) exibem as maiores respostas (|dz| = 0,59 e 0,45); à medida que o piso cresce, a resposta desvanece — Tensão (49,6%; 0,40), Depressão (67,1%; 0,18), Raiva (59,6%; 0,13), até a Confusão (80,5%; 0,06). Ou seja, **85% da variação na responsividade entre subescalas é explicada apenas pelo piso**. A detectabilidade da resposta ao treino é, antes de tudo, uma propriedade de mensuração.

## 4. Discussão

Três conclusões emergem. Primeiro, o BRUMS é **estruturalmente sólido** nesta amostra (seis fatores, boa adequação, fidedignidade alta na maioria das subescalas), mas com fragilidade **localizada** na Tensão, atribuível ao piso e não a defeito de construto. Segundo, o humor é dominantemente **traço**: quem o atleta é pesa mais do que como ele está num dado dia, o que torna a comparação contra normas de grupo pouco informativa e recomenda referências intraindividuais. Terceiro — e mais importante — a "estabilidade" das emoções negativas sob carga **não deve ser lida como resiliência mensurável**: ela é, em grande parte, um teto de mensuração (piso) somado a um piso de variância de estado. A convergência entre a lei do piso (R² = 0,85) e a decomposição de variância fecha o argumento: as subescalas que não respondem são exatamente as de maior piso e menor variância de estado.

Para a prática, isso reorienta o monitoramento: (i) acompanhar o **eixo energia–fadiga** (vigor, fadiga, fadiga física), que carrega a informação; (ii) interpretar as subescalas negativas com cautela, sem tomar sua calmaria como ausência de estresse; e (iii) basear decisões individuais em **médias de ≥ 3–7 coletas** e na **MDC₉₅** de cada escala, nunca numa leitura isolada. A subescala Tensão deve ser interpretada à luz do contexto (prontidão competitiva vs mal-estar), não descartada.

**Limitações.** Amostra única, masculina, um microciclo; itens ordinais com piso severo impedem testar invariância nas subescalas negativas (a comparabilidade temporal só é assegurada no eixo energia–fadiga); e a modelagem por fator principal/ω clássico deve ser complementada, em trabalho confirmatório, por AFC com estimador ordinal (WLSMV) e TRI de resposta gradual — cujos parâmetros, sob 456 observações de 27 pessoas, devem ser lidos com erros-padrão otimistas.

## 5. Conclusão

O BRUMS mede com precisão o eixo energia–fadiga em atletas de elite e mede com pouca informação as emoções negativas — não porque estas sejam estáveis, mas porque o instrumento atinge o piso. A decisão de monitoramento válida decorre diretamente da estrutura de medida: **eixo energia–fadiga, médias de múltiplas coletas, limiares de mudança mínima detectável e referência individual.**
