# Automação com n8n

Quatro fluxos prontos para importar no n8n. Eles cobrem as duas direções:

```
  n8n  ──POST /api/hooks/n8n──▶  LAPE      "roda o curador", "cadastra isto"
  LAPE ──POST no webhook do n8n──▶ n8n     "publiquei um artigo", "achei algo novo"
```

## Antes de importar

Defina estas variáveis de ambiente **no n8n** (Settings → Variables, ou o
`.env` da instância):

| Variável | Para quê |
|---|---|
| `LAPE_URL` | Endereço do LAPE, sem barra no fim (`https://lape.udesc.br`) |
| `LAPE_API_TOKEN` | O mesmo valor de `LAPE_API_TOKEN` no LAPE — autentica n8n → LAPE |
| `LAPE_WEBHOOK_SECRET` | O mesmo valor de `LAPE_WEBHOOK_SECRET` no LAPE — autentica LAPE → n8n |
| `LAPE_EMAIL_COORDENACAO` | Para onde vão os avisos |
| `LAPE_SLACK_CANAL` | Só no fluxo 02, se usar Slack |
| `LAPE_DRIVE_PASTA` | Só no fluxo 03: id da pasta do Google Drive |

E no LAPE (arquivo `.env`):

```bash
LAPE_API_TOKEN=uma-chave-longa-e-aleatoria
LAPE_WEBHOOK_SECRET=outra-chave-longa-e-aleatoria
```

> Gere as duas com `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`.
> São chaves diferentes de propósito: uma vale para entrar, a outra para provar
> que a mensagem saiu mesmo do LAPE.

## Os fluxos

| Arquivo | O que faz | Dispara por |
|---|---|---|
| `01-atualizacao-diaria.json` | Roda o curador de madrugada; se sobrou achado pendente, avisa a coordenação | Agenda, 03:00 |
| `02-avisar-publicacao.json` | Recebe o aviso do LAPE e anuncia no Slack quando um artigo é publicado | Webhook do LAPE |
| `03-planilha-do-drive.json` | Planilha nova numa pasta do Drive vira cadastro no LAPE e recálculo | Google Drive |
| `04-busca-semanal.json` | Segunda de manhã, procura produção nova nas bases e manda a lista por e-mail | Agenda, 09:00 seg |

Importar: **n8n → Workflows → Import from File**.

## Ligando o LAPE ao n8n

O fluxo 02 espera receber eventos. Depois de ativá-lo no n8n, copie a URL de
produção do nó *LAPE avisa* e cadastre no LAPE:

```bash
curl -b cookies.txt -X POST https://lape.udesc.br/api/webhooks \
  -H 'Content-Type: application/json' \
  -d '{"nome":"n8n — publicações","url":"https://n8n.exemplo/webhook/lape-evento",
       "evento":"artigo.publicado"}'
```

Ou, sem linha de comando: **Painel → Dados → Automação → Cadastrar webhook**.
Ali também dá para disparar um teste e ver o resultado na hora.

## Eventos que o LAPE emite

Assine `*` para receber todos, ou um nome específico:

| Evento | Quando acontece |
|---|---|
| `artigo.cadastrado` | Artigo criado ou atualizado |
| `artigo.publicado` | Artigo passou para publicado |
| `submissao.registrada` | Nova tentativa de submissão |
| `projeto.cadastrado` | Projeto criado ou atualizado |
| `integrante.cadastrado` | Integrante criado ou atualizado |
| `evento.cadastrado` | Atividade ou reunião cadastrada |
| `descoberta.encontrada` | O rastreador achou publicação nova |
| `descoberta.aceita` | Achado promovido a artigo do banco |
| `agente.concluido` | Um agente terminou de rodar |
| `lake.atualizado` | Camada analítica reconstruída |

Formato da mensagem:

```json
{
  "event": "artigo.publicado",
  "entity": "articles",
  "entity_id": 42,
  "detail": "Ansiedade competitiva em nadadores",
  "at": "2026-08-26T19:40:00",
  "data": { "title": "...", "doi": "10.1080/...", "journal": "...", "year": 2026 }
}
```

Cabeçalhos: `X-LAPE-Event` com o nome do evento e `X-LAPE-Signature` com
`sha256=<hmac do corpo>`. **Confira a assinatura antes de agir** — o nó
*Conferir a assinatura* do fluxo 02 faz exatamente isso, e serve de modelo.

Entrega em segundo plano, com três tentativas e espera crescente. Uma
automação fora do ar nunca trava o cadastro de um artigo no LAPE.

## O que o n8n pode pedir ao LAPE

`POST /api/hooks/n8n`, autenticado por `Authorization: Bearer $LAPE_API_TOKEN`
ou pela assinatura HMAC:

```jsonc
{ "acao": "curador", "rastrear": false }              // recarrega, recalcula, publica
{ "acao": "rastreador", "tarefas": ["descobrir"] }    // vai às bases externas
{ "acao": "lake", "exportar": true }                  // reconstrói a camada analítica
{ "acao": "cadastrar", "entidade": "articles",        // cadastra registros
  "dados": [ { "Título": "...", "Autores": "...", "Status": "Publicado" } ] }
```

Em `cadastrar`, as chaves são **os mesmos nomes de coluna das planilhas** — é o
que permite ligar uma planilha do Drive ao banco sem escrever conversão.

## Sem n8n

Nada aqui é obrigatório. O `.github/workflows/lape.yml` já roda o mesmo ciclo
todos os dias, e o `deploy/instalar.sh` deixa o cron pronto num servidor
próprio. O n8n entra quando o laboratório quiser ligar o LAPE a Drive, e-mail,
Slack, Telegram ou planilhas de terceiros sem escrever código.
