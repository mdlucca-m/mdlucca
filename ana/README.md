# Ana — assistente pessoal de pesquisa

A Ana responde perguntas sobre o estudo consultando a base, não a memória. É
uma configuração, não um produto: um servidor MCP que expõe a base única do
estudo de humor em handebol, uma persona que diz como usar essas ferramentas, e
uma memória pequena para o que já foi decidido.

```
  pergunta ──► Ana (persona) ──► ferramentas MCP ──► base única (somente leitura)
                    │                                 acervo de 218 abas
                    │                                 JSONs de modelagem
                    └──────────────────────────────►  memória de decisões
```

## Instalar

```bash
cd ana && ./instalar.sh          # registra em .mcp.json, para o Claude Code
./instalar.sh --desktop          # mostra o trecho para o Claude Desktop
```

O instalador reescreve os caminhos absolutos para a máquina onde é executado, de
modo que o `.mcp.json` versionado não precisa ser editado à mão.

Depois disso, no Claude Code:

- `/ana` carrega a persona na conversa em curso;
- o subagente `ana` (em `.claude/agents/ana.md`) responde em contexto próprio;
- as dezoito ferramentas `mcp__ana__*` ficam disponíveis diretamente.

## Sem cliente nenhum

```bash
./ana.py orientar                          # o mapa: o que existe e por onde entrar
./ana.py serie Vigor                       # série diária, derivadas, piso de ruído
./ana.py resultado --variavel Tensão --sig
./ana.py confronto                         # onde as três vias divergem
./ana.py modelo --parte diagnostico        # a checagem de reversão à média
./ana.py qualidade --parte discrepantes    # domínio, Tukey, z e z modificado
./ana.py otimizar --parte precos           # o que segura o microciclo
./ana.py buscar "piso de ruído"
./ana.py lembrar "periódico alvo" "Frontiers in Psychology"
./ana.py recordar --escopo handebol
```

## As quinze ferramentas

| Ferramenta | Responde |
|---|---|
| `ana_orientar` | o que existe na base e qual ferramenta usar |
| `ana_resultado` | os 305 resultados estatísticos, filtráveis |
| `ana_serie` | série diária suavizada, derivadas, choques |
| `ana_confronto` | onde não paramétrica, paramétrica e modelo misto divergem |
| `ana_perfil` | prevalência dos seis perfis por recorte |
| `ana_auditoria` | por que sete versões divergiam |
| `ana_modelo` | desempenho, árvore, subgrupo, diagnóstico, CRISP-DM |
| `ana_qualidade` | dicionário de tipos, conferência dos escores, faltantes, univariada, discrepantes, reconferência |
| `ana_otimizar` | resposta dose-humor, distribuição ótima da carga, preços-sombra, fronteira eficiente |
| `ana_cruzamento` | filtro binomial e piso de ruído; abscissa, velocidade, aceleração e zona de indecisão de cada cruzamento |
| `ana_decomposicao` | componentes de variância, fidedignidade da série, choque contra deriva, identidade do filtro |
| `ana_protocolo` | janelas de coleta pelo carimbo, regra de composição do valor diário e seu impacto |
| `ana_referencia` | DOI, PubMed, acesso aberto |
| `ana_buscar` | texto completo sobre 282.776 células de acervo |
| `ana_sql` | consulta livre, somente leitura |
| `ana_lembrar` · `ana_recordar` · `ana_esquecer` | a memória de decisões |

## O que ela sabe além dos resultados

Duas auditorias estão na base e a Ana distingue as duas: a de procedência
(D1–D6) responde de onde vem cada número, a de qualidade (Q1–Q6) responde se ele
está correto. A segunda reconstruiu 4.113 escores por fórmula sem encontrar
divergência, e a reconferência recalculou 65 valores dos três documentos por um
caminho de código independente. `ana_qualidade` abre as duas; `ana_otimizar`
abre a programação linear da carga, com os preços-sombra que dizem o que
realmente comprime o microciclo.

## O que a Ana não faz

- Não escreve na base do estudo. `ana_sql` recusa qualquer coisa que não seja
  `SELECT` ou `WITH`; a única escrita é a própria memória.
- Não guarda resultado na memória. Resultado mora na base e se consulta; memória
  é para decisão, preferência e pendência.
- Não cita nem exporta os arquivos com nomes reais de atletas. A base a que ela
  tem acesso já é anonimizada (A01–A27).
- Não estima o número que a consulta não trouxe. Diz «não está na base».

## Arquivos

| Arquivo | Papel |
|---|---|
| `ana_mcp.py` | servidor MCP, JSON-RPC sobre stdio, só biblioteca padrão |
| `ana.py` | as mesmas ferramentas pela linha de comando |
| `memoria.py` | memória em SQLite, com semeadura das decisões já tomadas |
| `instalar.sh` | registro no cliente MCP |
| `../.claude/skills/ana/SKILL.md` | a persona e as regras |
| `../.claude/agents/ana.md` | a Ana como subagente |
