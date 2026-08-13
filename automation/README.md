# Automação (estilo n8n)

Importe `delucca-pipeline.n8n.json` no n8n (**Workflows → Import from File**).
O fluxo liga o agendamento à publicação, chamando o pipeline Python no meio.

## Os nós (o caminho)

| # | Nó | O que faz |
|---|----|-----------|
| 1 | **Agenda (semanal)** | dispara o fluxo (ex.: segunda 08:00). |
| 2 | **Config do deck** | define qual conteúdo gerar (`content/caminho.json`) e a pasta de saída. |
| 3 | **Verificar DOIs (Crossref)** | confere cada referência; serve para alertar se algo falhar. |
| 4 | **Gerar** | `Execute Command` roda `python -m engine.pipeline` → HTML + PNG 1080/4K + PDF. |
| 5 | **Ler lâminas** | lê os PNGs gerados como binários. |
| 6 | **Publicar/Agendar** | envia ao Instagram via Meta Graph API (carrossel). |
| 7 | **Notificar** | confirma a execução (troque por e-mail/Telegram/Slack). |

## Variáveis de ambiente (no n8n)
- `IG_USER_ID` — ID da conta Instagram Business.
- `IG_TOKEN` — token de acesso da Meta Graph API.
- O nó 4 assume o projeto em `/opt/delucca` (ajuste o caminho ao seu host).

## Fluxo resumido
```
Agenda → Config ─┬─► Verificar DOIs (alerta)
                 └─► Gerar (Python) → Ler lâminas → Publicar (IG) → Notificar
```

## Sem Meta Graph API?
Troque o nó 6 por **e-mail/Telegram** anexando o PDF (`engine/dist/<deck>/<deck>.pdf`)
para aprovação manual antes de postar. O restante do fluxo é idêntico.

> Publicar no Instagram requer conta Business + app Meta aprovado. Trate `IG_TOKEN`
> como segredo (use as credenciais do n8n, não deixe em texto plano).

---

# Biblioteca (atualização automática) — `biblioteca.n8n.json`

Mantém a **Biblioteca Virtual** (`biblioteca/`) crescendo sozinha, com curadoria do
subagente `biblioteca-delucca`.

## Os nós
| # | Nó | O que faz |
|---|----|-----------|
| 1 | **Agenda (semanal)** | dispara toda segunda 07:00. |
| 2 | **Lacunas a buscar** | define `gaps` (ex.: variáveis psicológicas — flow, burnout, clima motivacional, autofala, resiliência, coping…; biomecânica/derivadas; bayesiano; ROC; tamanho de efeito) **e** `modalidades` (as 7 modalidades estéticas). |
| 3 | **Agente busca POR MODALIDADE + verifica DOI + cataloga** | `Execute Command` roda `automation/atualizar-biblioteca.sh`, que **itera cada modalidade** e chama o agente (Claude Code headless): busca internacional → verifica DOI no PubMed → grava os novos por modalidade em `_new-auto-<i>.json` (schema completo com `design`, `biomech`, `methods`, `stats_approach`, `effect_size`, `roc`, `derivatives`, `variables`, `modalities`). Depois `merge_new.py` mescla sem duplicar DOI e `build.py` regenera o HTML → commit/push. Imprime `NOVOS=<n>` (delta). |
| 4 | **Quantos novos?** | extrai `NOVOS=<n>` do log. |
| 5 | **Houve novidade?** | ramifica se `n > 0`. |
| 6a/6b | **Digest / Nada novo** | e-mail com o resumo dos novos artigos, ou no-op. |

## Requisitos
- **Claude Code CLI** disponível no host do n8n (o nó 3 usa `claude -p`). Sem ele, o
  script apenas pula a etapa do agente (falha graciosa) e nada é commitado.
- `repo` (nó 2) apontando para o clone do projeto; credencial SMTP + env `DIGEST_EMAIL`
  para o e-mail (troque por Telegram/Slack se preferir).

## 3º agente — `metodos-pmc` (texto completo)
O agente **`metodos-pmc`** (`.claude/agents/metodos-pmc.md`) aprofunda entradas já
catalogadas lendo o **texto completo open-access no PubMed Central**: resolve DOI→PMCID,
confere licença, baixa o full text, localiza a seção de **Métodos** e re-processa
**instrumentos, variáveis analisadas, amostra, população e análise estatística** (o
abstract costuma omitir). Os patches (`biblioteca/_pmc-*.json`) são aplicados por
`python3 biblioteca/apply_pmc.py` e o HTML é regenerado por `build.py`. As fichas ganham
os campos **População / Instrumentos / Variáveis analisadas** e o selo *“texto completo PMC”*.
> Rodar na mão (headless): `claude -p "Use o agente metodos-pmc nos DOIs open-access do acervo…"`,
> depois `python3 biblioteca/apply_pmc.py && python3 biblioteca/build.py`.

## Rodar na mão
```bash
# gaps no 1º argumento; modalidades via env MODALIDADES (o script itera cada uma)
MODALIDADES="Ginástica rítmica; Nado artístico; Cheerleading" \
  bash automation/atualizar-biblioteca.sh "flow; burnout; clima motivacional; resiliência"
```
> Trate qualquer token do Claude/GitHub como segredo (use as credenciais do n8n).
