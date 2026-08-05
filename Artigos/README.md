# Desmembramento em três artigos — Monitoramento de humor no handebol de elite

Conforme o parecer técnico (`../PARECER_TECNICO_Monitoramento_Humor_Handebol.md`), o manuscrito original — extenso demais para um único periódico (≈41 mil palavras, 43 tabelas, ~59 figuras, 17 objetivos específicos) — foi **reanalisado do zero** a partir das bases brutas e **reorganizado em três artigos independentes e publicáveis**, cada um com uma pergunta, um método-núcleo e uma contribuição próprios.

Toda a reanálise foi reexecutada em Python (numpy, scipy, statsmodels) sobre os dados item a item (24 itens do BRUMS, 456 observações, 27 atletas) e sobre as bases de carga interna, testes físicos e ciclos de competição/lesão. Os valores recomputados **convergem com — e em vários pontos reproduzem exatamente** — os do relatório original, o que sustenta a fidedignidade dos resultados.

## Os três artigos

| # | Título curto | Pergunta central | Contribuição |
|---|---|---|---|
| **1** | [Psicometria do BRUMS](Artigo_1_Psicometria_BRUMS.md) | O que o instrumento consegue medir nesta população? | A **lei do piso**: o efeito piso prediz a responsividade (R² = 0,85); traço domina a variância; limiares de decisão individual (SEM/MDC/Φ). |
| **2** | [Dinâmica agudo–crônica do HIIT](Artigo_2_Dinamica_HIIT_Humor.md) | O HIIT piora o humor por choque agudo ou por acúmulo? | Separa **nível do dia** de **resposta aguda**; deterioração por acúmulo no eixo energia–fadiga; corroboração fisiológica (FC pico ↓, PSE →) e Fitness–Fadiga. |
| **3** | [Prognóstico: competição e lesão](Artigo_3_Prognostico_Competicao_Lesao.md) | A fadiga do microciclo persiste? Prediz lesão? | **Novo:** o tapering reverte o choque (vigor dz = +1,27); trajetória não prediz estado individual; fadiga física do microciclo antecede lesões (exploratório). |

## Divisão de responsabilidades analíticas

- **Artigo 1** possui os resultados psicométricos (fidedignidade, estrutura, erro de medida, generalizabilidade) e **fornece** ao Artigo 2 a interpretação da lei do piso.
- **Artigo 2** possui a inferência sobre a resposta ao treino (efeito do dia, resposta aguda, multivariada, carga interna) e **fornece** ao Artigo 1 as estimativas de responsividade (|dz|) que ancoram a lei do piso.
- **Artigo 3** estende ambos ao horizonte da temporada (competição e lesão), material **ausente** do manuscrito original.

## Reprodutibilidade

Scripts de reanálise (em `../scripts/analise/`): `a1_psych.py`, `a2_dynamics.py`, `a3_prognosis.py`, sobre datasets derivados (`humor.csv`, `items.csv`, `phys.csv`, `comp_*.csv`, `injuries.csv`).

## Nota de governança de dados

As bases originais contêm dados **identificáveis** (nomes reais, incluindo atletas menores de 18 anos) e uma chave de anonimização reversível. Para submissão e depósito de dados abertos, o pacote deve ser **desidentificado de forma irreversível** e a chave nunca deve circular junto — em conformidade com a LGPD/GDPR e com o parecer do Comitê de Ética. Todos os produtos textuais aqui mantêm os atletas anonimizados (A01–A27).
