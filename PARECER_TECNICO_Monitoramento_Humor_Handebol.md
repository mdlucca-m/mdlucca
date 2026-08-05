# Parecer Técnico e Estatístico

**Manuscrito:** *Monitoramento Psicométrico do Humor e da Fadiga em Atletas de Handebol durante um Microciclo de Treinamento de Alta Intensidade: Estudo Observacional Longitudinal com Validação Robusta*

**Natureza da avaliação:** revisão editorial e estatística por pares (double-blind equivalente), com verificação independente dos dados-fonte.

**Base documental analisada:**
- `Artigo_Final_.docx` (manuscrito completo; ~41.000 palavras, 43 tabelas, ~59 figuras, 5 esquemas, 4 quadros).
- `Avaliações Handebol São José 2024.xlsx` (workbook analítico com 43 abas).
- `HIIT_FC_PSE.xlsx`, `COLETAS.xlsx`, `Backup_Banco_de_dados.xlsx` (bases brutas, item a item, carga interna e ciclos de competição/lesão).

**Perfil do parecerista assumido:** editor de periódico internacional em ciências do esporte; doutor em estatística; membro de comitê de psicologia do esporte. O parecer prioriza — a pedido — a crítica das **análises estatísticas**, com verificação empírica nos dados brutos.

---

## 1. Recomendação editorial

**Decisão sugerida: revisão maior (*major revision*) — com prognóstico favorável.**

O trabalho é, do ponto de vista metodológico-estatístico, **muito acima da média** da literatura de monitoramento em esportes coletivos. A tese central — *distinguir limitação de mensuração de ausência de efeito* — é original, defensável e executada com um arsenal inferencial que raramente se vê reunido num único estudo aplicado. Verifiquei de forma independente os pilares empíricos (descritivas, efeito piso, psicometria de item e decomposição traço/estado) e **todos se reproduzem** nos dados-fonte.

O que impede o aceite direto não é a qualidade da análise, e sim **três problemas de forma e escopo** e **um punhado de fragilidades inferenciais** que precisam ser explicitadas e/ou corrigidas: (i) o manuscrito é, na prática, três artigos comprimidos em um; (ii) confundimentos estruturais de desenho que limitam o alcance causal; e (iii) algumas conclusões psicométricas que a própria estrutura dos dados não licencia plenamente. Nenhum é fatal; todos são endereçáveis.

---

## 2. Verificação independente da base de dados

Antes de julgar o mérito, reexecutei checagens sobre os arquivos brutos. Registro-as porque conferem credibilidade ao restante do parecer e porque um editor deve reportar o que efetivamente auditou.

| Verificação | Manuscrito | Recomputado por mim | Status |
|---|---|---|---|
| N de observações | 456 | 456 | ✅ |
| N de atletas | 27 | 27 (únicos) | ✅ |
| Janela / dias | 21–27/04 (7 dias) | 7 datas, 21–27/04 | ✅ |
| Média Vigor / Fadiga | 5,70 / 5,65 | 5,70 / 5,64 | ✅ |
| % piso Confusão / Depressão / Raiva / Tensão | 80,5 / 67,1 / 59,6 / 49,6 | 80,5 / 67,1 / 59,6 / 49,6 | ✅ |
| Item "Apavorado" (tensao_1): % piso | ~100% | 99,6% (2 categorias usadas) | ✅ |
| Item "Alerta" (vigor_4): % piso | 53% | 52,7% | ✅ |
| ICC atleta (traço) — Tensão/Depressão/Raiva/PTH | 0,71/0,68/0,31/0,60 | 0,69/0,70/0,29/0,60 | ✅ |

**Conclusão da auditoria:** as estatísticas descritivas, o efeito piso, a psicometria no nível do item e a decomposição de variância traço/estado — que são a espinha dorsal do argumento — **reproduzem-se fielmente**. Não há sinais de seleção oportunista de resultados nesses pontos. Além disso, retifico uma suspeita inicial: os dados **item a item** dos 24 itens do BRUMS **existem** (aba `Itens BRUMS`, 456×24), de modo que AFC/TRI/ω ordinal/DIF são, em princípio, reproduzíveis — o que a versão anterior do dataset (apenas somas de subescala) não permitia. Recomendo que o repositório de dados publicado inclua explicitamente essa base de itens, e não apenas as somas.

---

## 3. Pontos fortes

**3.1. A contribuição metodológica é o verdadeiro artigo.** O maior mérito não é substantivo (que o humor piora sob HIIT já se sabia), e sim demonstrar, *com os próprios dados*, o custo de ignorar a estrutura de medidas repetidas. A demonstração de que a correção da pseudorreplicação (agregação por atleta) derruba dois efeitos "significativos" (fadiga mental, depressão) e recua fatores de Bayes de "extremos" (10⁴–10¹²) para "moderados" é pedagogicamente poderosa e transferível. O cálculo do efeito de desenho (deff ≈ 10,5; 456 observações ≈ 43 independentes) é o tipo de honestidade estatística que raramente se vê e deve ser preservado.

**3.2. Validação recíproca psicometria ↔ resposta ao treino.** O achado de que o efeito piso prediz quantitativamente a não-responsividade (|dz| = 0,588 − 0,00631·%piso; r = −0,93; R² = 0,86) é elegante e substantivamente importante: converte a "estabilidade" das subescalas negativas de achado substantivo em artefato de mensuração. É a ideia mais original do manuscrito e merece ser o eixo da narrativa (ver §6).

**3.3. Triangulação inferencial genuína.** Frequentista (modelos mistos, FDR), permutacional (PERMANOVA restrita ao atleta), multivariada paramétrica (Hotelling T²), bayesiana (BF JZS + ROPE/equivalência), tamanho de efeito multivariado (D de Mahalanobis) com três esquemas de bootstrap (casos percentil, BCa, residual multinível CGR). A convergência entre vias independentes é o padrão-ouro para blindar conclusões contra dependência de método. O uso de ROPE/equivalência para *afirmar ausência de efeito* (Confusão) — em vez de inferir nulidade de um p não significativo — é correto e sofisticado.

**3.4. Bateria psicométrica alinhada a COSMIN/Standards.** α e ω **ordinais** (policóricos) em vez de α de Pearson sobre itens ordinais com piso; AFC WLSMV com SE robusto ao *cluster*; comparação de modelos concorrentes (1/2/6 fatores/bifatorial); índices bifatoriais (ECV = 0,50; ωH = 0,71); HTMT; TRI (GRM) com informação condicional; SEM/MDC; ICC(1,1) vs ICC(1,7); teoria da generalizabilidade. É um tratamento de qualidade psicométrica que a maioria dos estudos de monitoramento simplesmente não faz.

**3.5. Corroboração objetiva e dissociação Fitness–Fadiga.** A integração de carga interna (FC, PSE, TRIMP vs session-RPE) e de marcadores objetivos (T-CAR, CMJ, Baker) fornece validade de construto convergente ao autorrelato e ilustra empiricamente o paradigma Fitness–Fadiga (aptidão sobe no mesociclo; fadiga aguda concentra-se no microciclo terminal). A observação de que o session-RPE cresce enquanto o TRIMP cardíaco cai (supressão da FC sob fadiga) é um alerta prático valioso.

**3.6. Transparência e reprodutibilidade.** Pipeline documentado (scripts e1_00–e1_07), Quadro 3 auditável ligando objetivo→método→pacote R→resultado, análise de sensibilidade (coorte completa n = 19 vs n = 27) e declaração explícita de limitações. Este é o comportamento de um estudo que quer ser verificado — e, na parte que verifiquei, ele resiste.

---

## 4. Pontos fracos e preocupações (ênfase estatística)

Organizo por natureza do problema, do mais estrutural ao mais pontual.

### 4.1. Desenho e identificação causal

**(C1) Confundimento perfeito volume × modalidade.** Os dias de HIIT (2, 4, 7) são também os de menor volume. Como os próprios autores reconhecem, nenhum modelo dissocia os dois com estes dados. A consequência precisa ficar ainda mais visível no *abstract* e nas conclusões: **qualquer efeito atribuído ao "HIIT" é, na verdade, efeito de "dia-tipo-HIIT" (intensidade + baixo volume + posição no microciclo) e não deve ser lido como dose-resposta.** O E-value (1,72–1,95) é uma boa mitigação, mas confirma que um confundidor moderado anula a associação de nível do dia.

**(C2) Definição de "pré/pós" e heterogeneidade extrema de coleta.** "Pré" e "pós" são a primeira e a última coleta do dia — misturando efeito de sessão e de hora do dia (declarado). Porém a auditoria revela um problema adicional **não suficientemente enfatizado**: o número de coletas por atleta-dia varia de **1 a 7**, e o total por atleta varia de **3 a 31** observações. O "cerca de cinco pares pré/pós por atleta" é uma média que esconde um desbalanceamento severo. Isso (i) torna o contraste agudo qualitativamente diferente entre atletas (para alguns, "pré→pós" separa 7 medições; para outros, 2), e (ii) levanta a possibilidade de **resposta não-aleatória** (atletas mais fatigados podem ter respondido mais — ou menos). A análise de sensibilidade cobre *missingness* de dias inteiros, mas não o mecanismo de propensão de resposta intradia. Recomendo: reportar a distribuição de coletas/atleta-dia, testar sensibilidade a "primeira vs última" contra "média da manhã vs média da tarde", e discutir MNAR.

**(C3) Amostra e poder.** n = 27 (e N efetivo ≈ 43). Os autores declaram poder de 80% apenas para ρ ≥ 0,52 e dz ≥ 0,58 — honesto, mas implica que **todos os resultados nulos de nível individual são inconclusivos, não evidências de ausência**. Isso precisa ser dito em cada nulo entre-atletas (moderação, regressões de carga→resposta), não só na seção de limitações.

### 4.2. Mensuração e psicometria

**(P1) Ajuste absoluto da AFC: SRMR = 0,169.** O manuscrito celebra CFI = 0,960 e RMSEA = 0,027, mas o SRMR de 0,169 é **mais que o dobro** do limiar de 0,08 e não deve ser tratado como mera nota de rodapé. A explicação (esparsidade/piso sob WLSMV) é parcialmente legítima, mas a combinação "CFI excelente + SRMR péssimo" indica que o modelo reproduz mal a matriz de covariâncias observadas justamente nos itens de piso. A afirmação "ajuste excelente" deve ser **qualificada** para "bom ajuste incremental, com ajuste absoluto comprometido nos itens de piso". Sugiro reportar também o WRMR e os resíduos padronizados por item.

**(P2) Invariância só demonstrável no eixo Vigor–Fadiga — e o PTH depende das negativas.** A invariância longitudinal só pôde ser testada colapsando categorias no eixo energia–fadiga; nas negativas, o piso impede o teste. Contudo, o **PTH/TMD** — outcome central de boa parte da inferência (trajetória semanal, "pico no Dia 7", regressão de determinantes) — **inclui** as cinco subescalas, quatro das quais **não têm invariância estabelecida**. Há aqui uma tensão lógica que precisa ser enfrentada de frente: comparar PTH ao longo do tempo herda a não-comparabilidade dos componentes não-invariantes. Recomendo: (a) reportar o PTH restrito ao eixo (Vigor–Fadiga) como *outcome* primário sensível, mantendo o PTH completo como secundário; ou (b) usar escores fatoriais/latentes num modelo de crescimento com invariância parcial (alignment de Muthén evita o colapso de categorias).

**(P3) TRI/GRM sob violação de independência local.** Declarado como exploratório — correto. Mas convém reforçar que 456 observações vêm de 27 pessoas: os SE dos parâmetros de item são **otimistas**. Os parâmetros de "Apavorado" (99,6% no piso, 2 categorias) são, como os próprios autores sinalizam, numericamente instáveis; eu iria além e **removeria esse item das figuras de informação** ou o marcaria visualmente como não-estimável, para não sugerir discriminação psicométrica onde há apenas ruído de estimação.

**(P4) "Reabilitação" da Tensão (ω ordinal = 0,79).** A leitura de que o α = 0,43 é artefato de piso e não defeito de construto é plausível e bem-argumentada — mas note-se que o ω ordinal de 0,79 e a AVE de 0,49 (abaixo de 0,50) coexistem, e a fidedignidade de *estado* (intra-atleta) da Tensão cai para 0,31. Ou seja: a Tensão pode ser um construto medível **entre** atletas e ainda assim **inútil para detectar mudança** dentro do atleta — que é o uso pretendido no monitoramento. A conclusão prática ("não descartar, mas interpretar com cautela o escore bruto") está correta; sugiro apenas separar mais nitidamente *validade de traço* de *sensibilidade de estado*.

### 4.3. Inferência e multiplicidade

**(I1) Multiplicidade controlada apenas por família.** FDR é aplicado *dentro* de cada variável/bloco, não no conjunto das dezenas de análises. Com 17 objetivos específicos, 43 tabelas e ~59 figuras, o "jardim dos caminhos que se bifurcam" é um risco real. Os autores rotulam corretamente as análises exploratórias (rede, agrupamento, derivadas, defasagem cruzada, dose-resposta) como geradoras de hipóteses — mas a **quantidade** dessas análises, mesmo rotuladas, dilui a mensagem confirmatória. A solução é editorial (ver §6): separar rigorosamente um núcleo confirmatório pré-especificável de um apêndice exploratório.

**(I2) Hotelling limítrofe nas 6 subescalas (p = 0,054).** O manuscrito lida bem com isto (mostra que o eixo energia–fadiga concentra o efeito, D = 0,66, p = 0,010), mas o *headline* multivariado nas 6 dimensões **não** é significativo no contraste restrito aos dias de treino. A redação deve garantir que nenhum leitor apressado saia com a impressão de um deslocamento multivariado global significativo — a PERMANOVA (p = 0,0002) e o Hotelling (p = 0,054) medem coisas ligeiramente diferentes (a PERMANOVA inclui baseline e usa permutação), e essa diferença precisa de uma frase explícita.

**(I3) Inconsistência interna no "quantas coletas".** A teoria da generalizabilidade indica **≥ 3 coletas** para Φ ≥ 0,80; a recomendação prática do texto é **≥ 5–7 dias**; a ICC(1,7) usa 7. São três números para a mesma pergunta. Não são contraditórios (Φ absoluta vs ICC de consistência vs janela clínica), mas o leitor aplicado precisa de **uma** regra operacional. Recomendo reconciliar num único quadro: "mínimo estatístico = 3; recomendado para tendência = 5–7".

**(I4) Modelo linear sobre desfechos com piso severo.** Os efeitos do dia/agudos das subescalas negativas são estimados por modelos lineares mistos sobre variáveis com 50–80% no zero e forte assimetria (Shapiro p < 0,001; resíduos com cauda direita e leve heterocedasticidade, Fig. 34). Bootstrap de cluster atenua, mas o especificação linear é sub-ótima. Como os próprios autores sugerem (Gama/log), o caminho correto é **modelos de contagem/censurados** (Tobit/hurdle) ou **cumulative-link mixed models (CLMM)** ordinais — que respeitam o piso e podem discriminar melhor "efeito pequeno" de "não-detectável". Isto é, inclusive, uma das direções futuras mais promissoras (§6).

### 4.4. Governança de dados (não-científico, mas relevante para publicação)

**(G1) Dados identificáveis.** As bases compartilhadas (`Itens BRUMS`, `Competição`, `Chave (confidencial)`, `Dicionário Atletas`) contêm **nomes reais** de atletas menores de idade em parte da amostra (amplitude 17,8–38,2 anos → há atletas < 18). A anonimização A01–A27 do manuscrito é revertível pela chave. Para submissão internacional (e conformidade LGPD/GDPR e com o parecer do CEP), o pacote de dados abertos **deve** ser desidentificado de forma irreversível antes de qualquer depósito, e a chave confidencial nunca deve circular junto. Este ponto é bloqueante para *data sharing*, ainda que não afete os resultados.

---

## 5. Recomendações

### Maiores (condicionam o aceite)
1. **Fatiar o manuscrito.** Ele é, no mínimo, dois artigos: (A) *Validação psicométrica e responsividade do BRUMS num microciclo de handebol (com a tese piso ↔ responsividade)*; (B) *Dinâmica agudo–crônica do humor e da carga interna sob microciclo de choque de HIIT*. Tentar publicar tudo junto prejudica ambos. Um periódico internacional pedirá corte de ~60% do volume atual.
2. **Requalificar o ajuste da AFC** (SRMR) e **resolver a tensão de invariância do PTH** (P1, P2).
3. **Foregrounding honesto dos confundimentos** (C1) e do desbalanceamento de coleta (C2) no *abstract*.
4. **Uma regra única de agregação** para a prática (I3) e **modelagem adequada ao piso** para as negativas (I4).
5. **Desidentificação irreversível** do pacote de dados (G1).

### Menores
- Reportar distribuição de coletas por atleta-dia e IC do deff.
- Marcar itens não-estimáveis (Apavorado) nas figuras de TRI.
- Reconciliar a nota "n = 37" que aparece no resumo bruto do workbook com o N analítico (27); explicitar o funil da coorte (temporada → microciclo).
- Uniformizar "5 fatores (PCA) vs 6 fatores (fa)" numa única recomendação com justificativa.
- Padronizar reporte de tamanhos de efeito (a "convenção dupla" é boa, mas escolher **um** como primário evita a impressão de *method-shopping*).

---

## 6. Direções futuras **com os dados que já temos**

Diferentemente da agenda genérica do manuscrito ("coletar mais, incluir mulheres, medir cortisol"), destaco análises **executáveis imediatamente** com os arquivos já disponíveis — de maior retorno científico e sem nova coleta:

**6.1. Ligar humor → competição e lesão (a análise de maior valor não realizada).**
O backup contém `Pré competição`, `Competição`, `Pós Competição` e `Lesões Sul-Centro-Americano` (maio–jun/2024, com datas, jogos e tipos de lesão), além da matriz de `Participação` por ciclo. O microciclo monitorado (21–27/04) **antecede** esse torneio. Isso permite um desenho **prospectivo real**: a trajetória de fadiga/queda do iceberg em abril prediz (a) o estado de humor na competição e (b) a ocorrência de lesão no torneio? Mesmo com poucos eventos, um modelo de sobrevivência penalizado (Firth) ou uma análise descritiva atleta-a-atleta transformaria o BRUMS de marcador **descritivo** em **preditor acionável** — exatamente o *upgrade* que o próprio manuscrito diz faltar, e que os dados já sustentam.

**6.2. Modelo estrutural latente completo (SEM multinível).**
O manuscrito valida o *measurement model* (AFC) e deixa o *structural model* como "agenda". Com os itens (`Itens BRUMS`) + carga interna (FC/PSE) + T-CAR, é viável **agora** um SEM de dois níveis (atleta/observação) ligando fadiga latente ↔ carga interna latente ↔ aptidão, propagando o erro de medida (em vez de regredir somas observadas). Isso ataca diretamente a fragilidade (P2/I4).

**6.3. Modelos dinâmicos (DSEM / state-space) para separar agudo de acúmulo.**
Com até 31 observações intensivas por atleta, um **Dynamic Structural Equation Model** (ou modelo multinível AR(1)) estimaria formalmente a *inércia* da fadiga, a recuperação noturna e o carryover entre dias como parâmetros — substituindo a descrição de "% de recuperação" por um modelo de estado. É o método correto para a pergunta "agudo vs crônico" que o estudo persegue.

**6.4. Modelos de localização-escala (MELSM) para "quem é volátil".**
O estudo observa iSD/MSSD descritivamente. Um *mixed-effects location-scale model* modela a variância intra-atleta como função de carga/aptidão — identificando não só quem tem pior humor médio, mas **quem é mais instável sob carga**, o subgrupo de risco que a média esconde (conecta a §4.6.4 e §5.11).

**6.5. Reanálise das negativas com CLMM/Tobit.**
Refazer os efeitos do dia/agudos das subescalas de piso com modelos ordinais de ligação cumulativa ou censurados testaria formalmente se a "não-resposta" sobrevive a um modelo que respeita o piso — fechando de vez o argumento piso ↔ responsividade com o método adequado, não com modelo linear + ressalva.

**6.6. Invariância por alignment e DIF longitudinal.**
Aplicar o método de *alignment* (Muthén) aos 7 dias evitaria o colapso de categorias e permitiria testar invariância aproximada em todas as subescalas — resolvendo P2 sem descartar dados.

**6.7. Trajetória sazonal do T-CAR como moderador variável no tempo.**
Há **cinco** avaliações de T-CAR na temporada (aba `Masculino`). Modelar a aptidão como covariável *time-varying* (não só baseline) refina a moderação "quem é mais vulnerável" e a dissociação Fitness–Fadiga com muito mais poder do que a correlação entre-atletas atual.

---

## 7. Síntese do parecer

Este é um manuscrito de **rigor estatístico incomum** para a área, cuja principal contribuição é metodológica: mostrar que respeitar a estrutura de medidas repetidas muda as conclusões, e que, em atletas de elite, a *ausência de sinal* nas subescalas negativas do BRUMS é uma **limitação de mensuração** (efeito piso + variância dominada por traço), não uma ausência de fenômeno. Verifiquei os pilares empíricos nos dados brutos e eles se sustentam.

As objeções não são à correção das análises — que é alta — mas ao **escopo** (três artigos em um), a **confundimentos de desenho** que precisam de mais destaque, e a **algumas conclusões psicométricas** (ajuste absoluto da AFC, invariância do PTH) que a estrutura dos dados não licencia integralmente e que devem ser requalificadas. Todas são corrigíveis em revisão.

O caminho de maior impacto, contudo, está fora do texto atual e **dentro dos dados já coletados**: ligar a trajetória de humor do microciclo aos desfechos de **competição e lesão** do torneio subsequente, e migrar da inferência sobre somas observadas para **modelos latentes dinâmicos**. Feito isso, o trabalho deixa de ser uma excelente descrição de um microciclo para se tornar uma demonstração de que o monitoramento subjetivo **prediz** o que importa.

**Recomendação final: revisão maior, com convite explícito à ressubmissão.**

---

*Parecer elaborado com verificação independente dos dados-fonte (Python/openpyxl; recomputação de descritivas, efeito piso, psicometria de item e decomposição de variância traço/estado). As checagens reproduziram os valores centrais reportados no manuscrito.*
