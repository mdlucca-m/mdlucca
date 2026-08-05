# Desmembramento em três artigos — Monitoramento de humor no microciclo de handebol de elite

Conforme o parecer técnico (`../PARECER_TECNICO_Monitoramento_Humor_Handebol.md`), o manuscrito original — extenso demais para um único periódico (≈41 mil palavras, 43 tabelas, ~59 figuras, 17 objetivos específicos) — foi **reanalisado do zero** a partir das bases brutas e **reorganizado em três artigos independentes e publicáveis**, cada um com uma pergunta, um método-núcleo e uma contribuição próprios.

## Escopo temporal (importante)

**Todas as análises restringem-se à semana de 21–28/04/2024** — o microciclo pré-competitivo de sete dias (21–27/04; três sessões de HIIT em 22, 24 e 27/04), com 456 observações do BRUMS em 27 atletas. Dados de outras fases da temporada (competição, pós-competição, lesões de maio–junho) **não** são usados. Os testes físicos (T-CAR, CMJ), avaliados fora da janela, entram **apenas como covariável de base** (aptidão prévia medida em 15/04, imediatamente antes da semana), nunca como desfecho de adaptação sazonal.

A reanálise foi reexecutada em Python (numpy, scipy, statsmodels) sobre os dados item a item (24 itens do BRUMS), a carga interna das três sessões de HIIT e os **demais questionários coletados na mesma janela** — recuperação percebida (TQR), sonolência (Epworth) e estresse percebido (PSS-14). Os valores recomputados **convergem com — e em vários pontos reproduzem exatamente** — os do relatório original, o que sustenta a fidedignidade dos resultados.

**Cobertura de instrumentos (dentro da janela):** BRUMS (24 itens → 6 subescalas + TMD), fadiga física/mental (0–10), **TQR** (recuperação 6–20), **Epworth** (sonolência 0–18), **PSS-14** (estresse) e **autoavaliações de estado físico/mental** (item único, 1–5). Achados-chave: a TQR responde ao microciclo (aguda e cronicamente) e integra o eixo energia–fadiga; a Epworth capta acúmulo crônico; o PSS é traço estável e **não** rastreia o microciclo (Artigo 2, §3.6; Artigo 1, §4); e a **autoavaliação física de item único** é um proxy eficiente do eixo energia–fadiga (rmcorr = −0,70; AUC = 0,83 para dia de fadiga alta), sustentando um protocolo ultraenxuto (Artigo 3, §3.7).

## Os três artigos (todos dentro da janela 21–28/04)

| # | Título curto | Pergunta central | Contribuição |
|---|---|---|---|
| **1** | [Psicometria do BRUMS](Artigo_1_Psicometria_BRUMS.md) | O que o instrumento consegue medir nesta população? | A **lei do piso**: o efeito piso prediz a responsividade (R² = 0,85); traço domina a variância; limiares de decisão individual (SEM/MDC/Φ). |
| **2** | [Dinâmica agudo–crônica do HIIT](Artigo_2_Dinamica_HIIT_Humor.md) | O HIIT piora o humor por choque agudo ou por acúmulo? | Separa **nível do dia** de **resposta aguda**; deterioração por acúmulo no eixo energia–fadiga; corroboração fisiológica (FC pico ↓, PSE →) dentro da semana. |
| **3** | [Acoplamento psicofisiológico e resposta individual](Artigo_3_Acoplamento_Psicofisiologico_Individual.md) | Como a fadiga evolui entre as 3 sessões e quem responde? | Progressão S1→S2→S3 (a fadiga se precipita na 3ª sessão); acoplamento intra-atleta FC×humor (rmcorr +0,57); RCI, variabilidade e limiares individuais. |

## Relatórios de análise dirigida (companion)

Além dos três artigos, dois relatórios aprofundam análises específicas dentro da janela:

- **[Carga interna/externa e baseline](Analise_Carga_Interna_Externa_HIIT.md)** — baseline 21/04; carga externa derivada do T-CAR (4×4 min @ 104% PV: velocidade 16,5 km/h, ~2.929 m/sessão); carga interna (FC, PSE, TRIMP) e a dissociação TRIMP↓ vs session-RPE↑; variáveis psicológicas por sessão.
- **[Análises robustas](Analises_Robustas_ROC_Derivadas_Alometria.md)** — tamanhos de efeito com IC bootstrap (dz D1→D7 fadiga física = +1,74; D de Mahalanobis = 1,55); derivadas (velocidade/aceleração da mudança); curvas não lineares (melhor ajuste cúbico); ajustes logísticos (OR aptidão = 0,50/km·h⁻¹); escalonamento alométrico; **ROC** (sessão de HIIT AUC ≈ 0,5 vs acúmulo D7–D1 AUC = 0,86).
- **[Post hoc](Analise_PostHoc_Comparacoes.md)** — comparações par a par entre dias (EMM do modelo misto, Tukey/Holm) e entre sessões de HIIT: fadiga física e vigor diferem do baseline já no D2; TMD só no D7 (maior contraste D5→D7); queda da FC de pico concentrada em S2→S3.

## Divisão de responsabilidades analíticas

- **Artigo 1** possui os resultados psicométricos (fidedignidade, estrutura, erro de medida, generalizabilidade) e **fornece** ao Artigo 2 a interpretação da lei do piso.
- **Artigo 2** possui a inferência de grupo sobre a resposta ao treino (efeito do dia, resposta aguda, multivariada) e **fornece** ao Artigo 3 o pano de fundo médio que o nível individual detalha.
- **Artigo 3** aprofunda o nível **intra-atleta** (acoplamento fisiológico–psicológico e decisão individual), inteiramente dentro do microciclo.

## Reprodutibilidade

Scripts de reanálise (em `../scripts/analise/`): `a1_psych.py`, `a2_dynamics.py`, `a3_within.py`, sobre datasets derivados da janela (`humor.csv`, `items.csv`, `fc_sessions.csv`, `phys.csv` — este último só como covariável de base).

## Nota de governança de dados

As bases originais contêm dados **identificáveis** (nomes reais, incluindo atletas menores de 18 anos) e uma chave de anonimização reversível. Para submissão e depósito de dados abertos, o pacote deve ser **desidentificado de forma irreversível** e a chave nunca deve circular junto — em conformidade com a LGPD/GDPR e com o parecer do Comitê de Ética. Todos os produtos textuais aqui mantêm os atletas anonimizados (A01–A27).
