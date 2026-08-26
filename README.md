# LAPE — Banco de dados e painel de indicadores científicos

Sistema automatizado de gestão da produção científica do **LAPE — Laboratório de
Psicologia do Esporte e do Exercício** (UDESC/CEFID).

Transforma as planilhas do laboratório em um banco de dados consultável, busca em
tempo real os metadados e as citações dos artigos nas bases bibliográficas, e
publica um painel HTML autocontido com todos os indicadores.

```
planilhas (.xlsx)  ─┐
Currículo Lattes    ├─►  agente curador ─►  SQLite ─►  painel HTML + API REST
bases externas     ─┘         ▲
                              └── agente rastreador (OpenAlex, Crossref,
                                  PubMed, Scopus, Web of Science)
```

---

## Início rápido

```bash
pip install -r requirements.txt

# 1. gera a planilha complementar de cadastros (integrantes, linhas, eventos)
python3 scripts/make_templates.py

# 2. roda o ciclo completo e publica o painel em docs/index.html
python3 scripts/lape_agent.py curador

# 3. abre o painel
xdg-open docs/index.html     # Linux
open docs/index.html         # macOS
```

Sem internet? Use `python3 scripts/lape_agent.py curador --offline`.

---

## Os dois agentes digitais

### Agente rastreador — busca informação lá fora

Vai às bases bibliográficas e traz o que falta. Não decide nada: tudo o que
encontra fica pendente de aprovação.

```bash
python3 scripts/lape_agent.py rastreador                    # as três tarefas
python3 scripts/lape_agent.py rastreador enriquecer         # completa DOI, periódico, ano
python3 scripts/lape_agent.py rastreador citar              # atualiza citações
python3 scripts/lape_agent.py rastreador descobrir --desde 2020
```

| Tarefa | O que faz | Fonte |
|---|---|---|
| `descobrir` | Procura publicações dos integrantes que ainda não estão no banco e registra em `discoveries` | OpenAlex (por ORCID ou nome + instituição) |
| `enriquecer` | Preenche DOI, periódico, ISSN, ano e link dos artigos incompletos | Crossref + OpenAlex, casando pelo título |
| `citar` | Atualiza as contagens de citação e grava o histórico | OpenAlex (aberta), Scopus e Web of Science (com chave) |

Aprovar ou descartar o que ele encontrou:

```bash
python3 scripts/lape_agent.py revisar --list
python3 scripts/lape_agent.py revisar --aceitar 12 15
python3 scripts/lape_agent.py revisar --ignorar 13
python3 scripts/lape_agent.py revisar --auto      # aceita as que têm 2+ autores já cadastrados
```

### Agente curador — mantém o banco

Carrega as planilhas e o Lattes, consolida, valida, recalcula os indicadores e
regenera o painel.

```bash
python3 scripts/lape_agent.py curador                      # ciclo completo
python3 scripts/lape_agent.py curador --offline            # sem consultar as bases
python3 scripts/lape_agent.py curador --janela 10          # análises de 10 anos
python3 scripts/lape_agent.py status                       # resumo e lacunas
```

**Regra que vale em todo o sistema:** o que o laboratório digitou nunca é
sobrescrito por fonte externa. Os agentes só preenchem campos vazios.

---

## API REST

```bash
python3 scripts/lape_agent.py api --port 8000
```

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | O painel HTML |
| `/api` | GET | Índice das rotas |
| `/api/health` | GET | Status do serviço e contagens |
| `/api/metrics` | GET | Todos os indicadores em JSON |
| `/api/metrics/<bloco>` | GET | Um bloco (`publications`, `network`, `submissions`, …) |
| `/api/articles` | GET | Filtros: `status`, `linha`, `ano`, `q`, `limit`, `offset` |
| `/api/articles/<id>` | GET | Artigo com autores, submissões, marcos e histórico de citações |
| `/api/articles` | POST | Cadastra ou atualiza (objeto ou lista) |
| `/api/submissions`, `/api/members`, `/api/events`, `/api/research-lines`, `/api/institutions` | GET / POST | Idem para as demais entidades |
| `/api/discoveries` | GET | Achados pendentes do rastreador |
| `/api/discoveries/<id>/review` | POST | `{"action": "aceitar"}` ou `{"action": "ignorar"}` |
| `/api/agents/tracker` | POST | Dispara o rastreador |
| `/api/agents/curator` | POST | Dispara o ciclo completo |
| `/api/export/sqlite` | GET | Baixa o banco |

O `POST` aceita **os mesmos nomes de coluna das planilhas**, então dá para
cadastrar em português:

```bash
curl -X POST http://127.0.0.1:8000/api/articles \
  -H 'Content-Type: application/json' \
  -d '{"Título":"Ansiedade competitiva em nadadores",
       "Autores":"Andrade; Vilarino; Loiane",
       "Status":"Publicado","Ano":2024,
       "Periódico":"Journal of Sports Sciences",
       "DOI":"10.1080/02640414.2024.1234",
       "Data de início":"2023-02-01",
       "Data de submissão":"2023-11-10",
       "Data do aceite":"2024-03-15",
       "Linha de pesquisa":"Psicologia do Esporte e do Exercício"}'
```

Proteja a API fora da rede local com um token:

```bash
export LAPE_API_TOKEN="uma-senha-longa"
curl -H "Authorization: Bearer uma-senha-longa" http://127.0.0.1:8000/api/health
```

---

## O painel

Arquivo único em `docs/index.html`, sem nenhuma dependência externa — funciona
offline, por e-mail ou no GitHub Pages. Tem tema claro/escuro e é imprimível.

| Seção | Conteúdo |
|---|---|
| Visão geral | KPIs, situação dos artigos, publicações por ano |
| Índice de linhas de pesquisa | Uma ficha por linha, com produção e equipe |
| Artigos em produção | Título, data de início, autores, progresso de versões |
| Artigos submetidos | Título, revista atual, data de submissão, tempo em avaliação |
| Publicações por ano | Últimos 5 anos, total e média anual, série histórica |
| Artigos mais citados | Scopus, Web of Science e OpenAlex — geral e últimos 5 anos |
| Artigos por integrante | Envolvimento de cada pessoa por etapa |
| Rede de colaboração | Grafo de coautoria, densidade, grau médio, duplas mais produtivas |
| Tempos do ciclo editorial | Início→publicação, submissão→aceite, aceite→publicação |
| Submissões e recusas | Tentativas por artigo, intervalos entre submissões, motivos das recusas |
| Datas de aceite | Aceites com o tempo desde a primeira submissão |
| Calendário e atividades | Calendário navegável, próximas atividades, tipos |
| Linha do tempo | Mapa de calor ano × mês de publicações, submissões e atividades |
| Distribuição espacial | Mapa de atividades e instituições parceiras |
| Achados do rastreador | Publicações encontradas aguardando aprovação |
| Qualidade dos dados | Lacunas a preencher e histórico de cargas |

Para publicar no GitHub Pages: **Settings → Pages → Source: Deploy from a branch
→ pasta `/docs`**.

---

## Os dados de entrada

Coloque qualquer arquivo `.xlsx`, `.xls` ou `.csv` em `data/raw/`. O importador
reconhece as abas e as colunas pelo nome, tolerando variações de acentuação,
maiúsculas e sinônimos — não é preciso renomear nada.

### Planilha do laboratório (já suportada)

`LAPE_Gestao_Indicadores_Cientificos_v3.xlsx`

| Aba | Vira |
|---|---|
| Pipeline de Artigos | Artigos, equipe, responsável e marcos de versão |
| Tentativas de Submissão | Uma submissão por bloco (formato largo → longo automaticamente) |
| Métricas / Histórico Mensal / Como usar | Ignoradas — o painel recalcula esses números |

### Planilha complementar (gerada por `make_templates.py`)

`LAPE_cadastros.xlsx`, com as abas **Integrantes**, **Linhas de Pesquisa**,
**Instituições**, **Publicações**, **Eventos** e **Motivos de recusa**.
A aba Integrantes já vem preenchida com os nomes encontrados nas outras
planilhas.

> **A coluna `Variações` é a mais importante.** Liste ali, separadas por ponto e
> vírgula, todas as grafias da mesma pessoa (`Alexandro; Andrade; ANDRADE, A.`).
> É isso que faz a rede de colaboração e a contagem por integrante ficarem
> corretas. `python3 scripts/lape_agent.py status` aponta as duplicatas suspeitas.

### Currículo Lattes

No currículo em lattes.cnpq.br, clique no ícone **XML** (“Exportar / Currículo em
XML”) e salve o `.zip` em `data/raw/` com `lattes` no nome — por exemplo
`data/raw/lattes_alexandro_andrade.zip`. O parser lê artigos publicados, artigos
aceitos e trabalhos em eventos, e mescla com o que já existe pelo título.

> A raspagem direta de `buscatextual.cnpq.br` não é usada: aquela página exige
> sessão e CAPTCHA. O XML é o caminho oficial e estável.

### Chaves de API (opcionais)

```bash
export SCOPUS_API_KEY="..."        # dev.elsevier.com
export SCOPUS_INST_TOKEN="..."     # opcional, acesso fora da rede da instituição
export WOS_API_KEY="..."           # developer.clarivate.com (WoS Starter API)
export LAPE_CONTACT_EMAIL="..."    # e-mail de contato (polite pool do Crossref/OpenAlex)
```

Sem chave nenhuma o sistema continua funcionando: o **OpenAlex** é aberto e já
fornece contagem de citações para todo artigo com DOI.

---

## Automação

`.github/workflows/lape.yml` executa toda segunda-feira às 9h (e a cada envio de
planilha nova): roda os testes, o curador e o rastreador, e faz commit do banco e
do painel atualizados. As chaves de API vão em **Settings → Secrets and variables
→ Actions**.

Para rodar num servidor próprio, agende o curador no cron e deixe a API no ar:

```cron
0 6 * * *  cd /opt/lape && python3 scripts/lape_agent.py curador >> logs/lape.log 2>&1
```

---

## Estrutura

```
sql/schema.sql              esquema do banco (13 tabelas + 6 views analíticas)
scripts/
  lape_agent.py             console dos agentes (rastreador, curador, api, revisar, status)
  run_pipeline.py           pipeline direto, sem os agentes
  make_templates.py         gera a planilha complementar de cadastros
  migrate.R                 aplica o mesmo schema.sql pelo R
  lape/
    config.py               caminhos, janela de análise, credenciais
    util.py                 normalização de datas, nomes e títulos
    mapping.py              sinônimos de abas, colunas e vocabulário controlado
    db.py                   SQLite: upserts idempotentes, fusão de integrantes
    ingest_excel.py         planilhas → banco (inclui formato largo → longo)
    ingest_lattes.py        XML do Lattes → banco
    ingest_citations.py     Scopus e Web of Science
    sources.py              OpenAlex, Crossref, PubMed (só biblioteca padrão)
    metrics.py              todos os indicadores
    report.py               gera o painel HTML
    api.py                  API REST
    agents/tracker.py       agente rastreador
    agents/curator.py       agente curador
    templates/              HTML, CSS e JavaScript do painel
data/raw/                   planilhas e XML do Lattes (entrada)
data/geo/                   GeoJSON opcional para o mapa
docs/index.html             painel gerado (saída)
tests/                      29 testes, sem acesso à rede
```

O `scripts/migrate.R` continua funcionando: ele aplica o mesmo `sql/schema.sql`,
então quem preferir analisar os dados em R lê o mesmo banco.

---

## Testes

```bash
python3 -m unittest discover -s tests -v
```

Os testes conferem a ingestão contra os números que a própria planilha do
laboratório calcula (por exemplo, os 12,5 dias médios entre uma recusa e a nova
submissão) e substituem as bases externas por respostas gravadas, para rodarem
sem rede.
