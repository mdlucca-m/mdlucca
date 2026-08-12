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
| 2 | **Lacunas a buscar** | define os temas/lacunas (ex.: nado artístico, cheerleading, unidades motoras, flow, burnout). |
| 3 | **Agente busca + verifica DOI + cataloga** | `Execute Command` roda `automation/atualizar-biblioteca.sh`, que chama o agente (Claude Code headless): busca internacional → verifica DOI → **append sem duplicar** em `biblioteca.json` → reinjeta no HTML → commit/push. Imprime `NOVOS=<n>`. |
| 4 | **Quantos novos?** | extrai `NOVOS=<n>` do log. |
| 5 | **Houve novidade?** | ramifica se `n > 0`. |
| 6a/6b | **Digest / Nada novo** | e-mail com o resumo dos novos artigos, ou no-op. |

## Requisitos
- **Claude Code CLI** disponível no host do n8n (o nó 3 usa `claude -p`). Sem ele, o
  script apenas pula a etapa do agente (falha graciosa) e nada é commitado.
- `repo` (nó 2) apontando para o clone do projeto; credencial SMTP + env `DIGEST_EMAIL`
  para o e-mail (troque por Telegram/Slack se preferir).

## Rodar na mão
```bash
bash automation/atualizar-biblioteca.sh "nado artístico; cheerleading; unidades motoras"
```
> Trate qualquer token do Claude/GitHub como segredo (use as credenciais do n8n).
