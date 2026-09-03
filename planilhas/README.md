# Planilha de Controle e Prescrição de Treinamento — Voleibol

Planilhas (.xlsx) para planejamento periodizado, prescrição e controle de carga de equipes de voleibol,
com esquema de banco de dados equivalente para aplicativo.

## Arquivos

| Arquivo | Uso |
|---|---|
| `Planilha_Voleibol_Forca_e_Potencia_v2.xlsx` | **Versão atual (23 abas)** — com dados de exemplo de um elenco masculino adulto |
| `Planilha_Voleibol_Forca_e_Potencia_v2_EM_BRANCO.xlsx` | Mesmas fórmulas, sem os dados de exemplo |
| `schema_app_voleibol.sql` | Esquema PostgreSQL (26 tabelas, 5 views) equivalente à planilha |
| `gerar_planilha_volei_v2.py` | Gerador da v2 (openpyxl) |
| `partes/` | Módulos do gerador e o montador `montar_v2.py` |
| `Planilha_Voleibol_Controle_e_Prescricao_de_Treinamento*.xlsx` | Versão 1 (14 abas, sem o módulo de força) |
| `gerar_planilha_volei.py` | Gerador da v1 |

## Abas da versão 2

**Cadastro e avaliação** — Cadastro (identificação, contato, socioeconômico, histórico esportivo, saúde) ·
Antropometria (perfil restrito ISAK, % de gordura por Jackson-Pollock 7 dobras, somatotipo Heath-Carter) ·
Testes (alcances, impulsões, SJ, CMJ, drop jump com RSI, sprint, agilidade, IMTP) ·
Perfil F-V-P (F0, V0, Pmax e desequilíbrio força-velocidade pelo método de Samozino).

**Planejamento** — Exercícios (89 exercícios) · Programa PF (as 8 séries do documento original) ·
Macrociclo · Mesociclo · **Bloco Base** (8 semanas de periodização em blocos com microciclos de choque) ·
Microciclo.

**Prescrição** — Prescrição (técnico-tático) · **Prescrição Força** (%1RM, carga em kg, velocidade-alvo,
perda de velocidade, tonelagem; as 8 semanas já prescritas) · Força 1RM (Epley/Brzycki + matriz de 1RM atual).

**Controle** — Carga (PSE) com ACWR, monotonia e strain · Saltos (contatos pliométricos, quadra e jogo) ·
Wellness (Índice de Hooper) · Presença.

**Painéis** — Área do Atleta · Painel da equipe · KPIs Força · Evidências (60 referências).

## Métodos e referências

- **Carga interna (UA)** = duração × PSE da sessão — Foster et al. (2001)
- **ACWR** = carga aguda 7 d ÷ carga crônica 28 d — Gabbett (2016). Só classificado após 21 dias de histórico
- **Monotonia e strain** — Foster (1998)
- **Índice de Hooper** — Hooper & Mackinnon (1995)
- **Periodização em blocos** — Issurin (2010, 2016); Stone et al. (2021); Rønnestad et al. (2018)
- **Derivados de LPO** — Suchomel et al. (2015, 2017, 2020)
- **Dose de pliometria** — Sáez de Villarreal et al. (2009)
- **Treinamento por velocidade** — Weakley et al. (2020); Hickmott et al. (2022); Greig et al. (2023)
- **Perfil força-velocidade** — Morin & Samozino (2016); Jiménez-Reyes et al. (2017, 2019), com as ressalvas
  de Lindberg et al. (2021), Bobbert et al. (2024) e Solberg et al. (2025)
- **% de gordura** — Jackson & Pollock (1978/1980) + Siri (1961) · **Somatotipo** — Carter & Heath (1990)
- **Potência de pico** — Sayers et al. (1999)

A aba **Evidências** traz as 60 referências completas, com achado principal, aplicação e link.

## Regerar

```bash
pip install openpyxl
python3 partes/montar_v2.py      # monta o gerador v2 a partir da v1 + as partes
python3 gerar_planilha_volei_v2.py
```

## Banco de dados

```bash
createdb volei_app
psql -d volei_app -f schema_app_voleibol.sql
```

Testado em PostgreSQL 16. Usa colunas geradas (carga em UA, Índice de Hooper, impulsões, 1RM de Epley e
Brzycki, tonelagem) e views de KPI (`vw_1rm_atual`, `vw_carga_acwr`, `vw_carga_semanal`, `vw_saltos_semana`,
`vw_forca_semana`).

> **LGPD** — as tabelas de cadastro, socioeconômico e saúde guardam dados pessoais e sensíveis. Colete com
> consentimento por escrito, restrinja o acesso por papel e registre quem consulta.

> Estas ferramentas organizam o treino. Não substituem avaliação médica ou fisioterápica: os indicadores de
> risco são apoio à decisão do técnico e do preparador físico.
