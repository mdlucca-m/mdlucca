# Planilha de Controle e Prescrição de Treinamento — Voleibol

Planilha completa (.xlsx) para planejamento periodizado e controle de carga de equipes de voleibol.

## Arquivos

| Arquivo | Uso |
|---|---|
| `Planilha_Voleibol_Controle_e_Prescricao_de_Treinamento.xlsx` | Versão com dados de exemplo (12 atletas fictícios, 4 semanas de registros) para ver todos os cálculos e gráficos funcionando |
| `Planilha_Voleibol_Controle_e_Prescricao_de_Treinamento_EM_BRANCO.xlsx` | Mesmas fórmulas, pronta para uso, sem dados de exemplo |
| `gerar_planilha_volei.py` | Gerador (openpyxl) — permite regerar ou customizar a planilha |

## Abas

1. **Início** — instruções, legenda de cores e definição das métricas
2. **Cadastro** — atletas (idade, IMC, alcances e impulsões calculados)
3. **Exercícios** — biblioteca com 42 exercícios de voleibol
4. **Macrociclo** — temporada dividida em mesociclos, com dinâmica volume × intensidade
5. **Mesociclo** — microciclos do mesociclo selecionado, previsto × realizado
6. **Microciclo** — semana de treino e distribuição de conteúdos por dia
7. **Prescrição** — prescrição exercício a exercício, por equipe ou por atleta
8. **Carga (PSE)** — carga interna, aguda 7 d, crônica 28 d, ACWR e zona de risco
9. **Wellness** — Índice de Hooper diário
10. **Presença** — chamada e % de assiduidade por atleta
11. **Testes** — bateria de avaliações físicas
12. **Atleta** — área do atleta: perfil, monotonia/strain e treino prescrito
13. **Painel** — dashboard da equipe com 5 gráficos
14. **Listas** — fonte de todos os menus suspensos

## Métricas

- **Carga interna (UA)** = duração (min) × PSE da sessão (0–10) — Foster et al. (2001)
- **ACWR** = carga aguda (7 d) ÷ carga crônica (média semanal de 28 d) — Gabbett (2016)
- **Monotonia** = média das cargas diárias da semana ÷ desvio-padrão delas
- **Strain** = carga semanal × monotonia — Foster (1998)
- **Índice de Hooper** = sono + estresse + fadiga + dor muscular (4 a 28; maior = pior) — Hooper & Mackinnon (1995)

## Regerar

```bash
pip install openpyxl
python3 gerar_planilha_volei.py
```

> A planilha é uma ferramenta de organização do treino. Não substitui avaliação médica ou fisioterápica.
