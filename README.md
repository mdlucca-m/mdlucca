# LAPE — Sistema de gestão da produção científica

Banco de dados, agentes de coleta automática, área de cadastro com login e
painel de indicadores do **LAPE — Laboratório de Psicologia do Esporte e do
Exercício** (UDESC/CEFID).

```
 planilhas (.xlsx) ─┐                                  ┌─► painel interativo  /
 Currículo Lattes   ├─► agente curador ─► SQLite ──────┼─► área do integrante /app
 bases externas    ─┤         ▲                        └─► API REST          /api
 cadastro na web   ─┘         └── agente rastreador (OpenAlex, Crossref,
                                   PubMed, Scopus, Web of Science)
```

---

## Índice

- [Início rápido](#início-rápido)
- [O site: painel, login e cadastro](#o-site-painel-login-e-cadastro)
- [Publicar na nuvem](#publicar-na-nuvem)
- [Os dois agentes digitais](#os-dois-agentes-digitais)
- [API REST](#api-rest)
- [O que o painel mostra](#o-que-o-painel-mostra)
- [Os dados de entrada](#os-dados-de-entrada)
- [Automação](#automação)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Testes](#testes)

---

## Início rápido

```bash
pip install -r requirements.txt

# 1. planilha complementar de cadastros (integrantes, linhas, projetos, eventos)
python3 scripts/make_templates.py

# 2. carrega tudo e publica o painel estático em docs/index.html
python3 scripts/lape_agent.py curador --offline

# 3. cria o primeiro acesso
python3 scripts/lape_agent.py usuarios \
  --criar "Alexandro Andrade" andrade@udesc.br --perfil admin

# 4. sobe o site
python3 scripts/lape_agent.py api --port 8000
```

Abra <http://127.0.0.1:8000> e entre com o login criado.

---

## O site: painel, login e cadastro

Um único serviço responde por tudo, sempre lendo direto do banco:

| Endereço | O que é |
|---|---|
| `/` | Painel de indicadores, remontado a cada acesso com os dados atuais |
| `/entrar` | Tela de acesso |
| `/app` | Área do integrante: cadastro de perfil, artigos, submissões, projetos |
| `/api` | API REST |

### Quem pode o quê

| Perfil | Pode |
|---|---|
| `leitura` | Consultar o painel e a API |
| `integrante` | Tudo acima + editar **o próprio perfil**, cadastrar artigos, submissões, projetos e atividades |
| `coordenacao` | Tudo acima + editar qualquer registro, criar linhas de pesquisa, rodar os agentes, aprovar achados |
| `admin` | Tudo acima + criar acessos, ver o registro de atividade, exportar o banco |

Um integrante que tentar alterar o cadastro de outra pessoa recebe `403` — a
regra está no servidor, não só na tela.

### O que cada pessoa cadastra em `/app`

- **Meu perfil** — nome, variações do nome, função, titulação, linha de
  pesquisa, instituição, Lattes, ORCID, e-mail, telefone, minibiografia.
  Mostra artigos, projetos e **índice h**.
- **Artigos** — título, autores, situação, linha, datas de cada versão,
  submissão, aceite, publicação, periódico, DOI, Qualis, fator de impacto.
- **Submissões** — revista, data, decisão, motivo da recusa, rodadas de revisão.
- **Projetos** — título, coordenação, financiador, processo, valor, vigência,
  parecer ético e equipe.
- **Linhas de pesquisa** e **atividades/reuniões** (coordenação).
- **Administração** — rodar os agentes, aprovar achados do rastreador, liberar
  acesso a novos integrantes, registro de atividade.

### Gerenciar acessos pela linha de comando

```bash
python3 scripts/lape_agent.py usuarios                                   # lista
python3 scripts/lape_agent.py usuarios --criar "Nome" email@udesc.br     # senha gerada
python3 scripts/lape_agent.py usuarios --criar "Nome" x@udesc.br --perfil coordenacao
python3 scripts/lape_agent.py usuarios --redefinir 12                    # nova senha
python3 scripts/lape_agent.py usuarios --perfil-de 12 coordenacao
```

Senhas são guardadas como PBKDF2-HMAC-SHA256 com sal aleatório e 240 000
iterações — o banco nunca contém a senha. A sessão vive num cookie HttpOnly
com validade de 14 dias.

---

## Publicar na nuvem

O sistema é um contêiner só. O que precisa persistir é **um arquivo**: o banco
SQLite. Qualquer opção abaixo entrega um link `https://…` que os integrantes
acessam com login e senha.

### Docker (servidor próprio ou da universidade)

```bash
export LAPE_ADMIN_LOGIN=andrade@udesc.br
export LAPE_ADMIN_PASSWORD='uma-senha-longa-de-verdade'
docker compose up -d
```

O primeiro administrador é criado na subida inicial. Coloque o `nginx.conf` de
`deploy/` na frente para ter HTTPS e defina `LAPE_BEHIND_HTTPS=1`.

### Fly.io

```bash
fly launch --no-deploy --copy-config
fly volumes create lape_dados --size 1 --region gru
fly secrets set LAPE_ADMIN_LOGIN=... LAPE_ADMIN_PASSWORD=... \
                SCOPUS_API_KEY=... WOS_API_KEY=...
fly deploy      # → https://lape-udesc.fly.dev
```

### Render

Suba o repositório no GitHub e use **New → Blueprint** apontando para
`render.yaml`. Defina `LAPE_ADMIN_LOGIN` e `LAPE_ADMIN_PASSWORD` no painel do
serviço. O blueprint reserva um disco de 1 GB para o banco: **sem disco o
SQLite é apagado a cada nova versão**, e discos não existem no plano gratuito
do Render — para custo zero, prefira o `docker-compose.yml` num servidor da
universidade.

### Servidor sem Docker

`deploy/lape.service` (systemd) + `deploy/nginx.conf` (HTTPS) +
`deploy/backup.sh` (backup diário do banco, agendável no cron).

### Variáveis de ambiente

| Variável | Para quê |
|---|---|
| `LAPE_DB` | Caminho do banco (na nuvem, aponte para o volume) |
| `LAPE_HOST` / `LAPE_PORT` | Onde o servidor escuta (`0.0.0.0` em contêiner) |
| `LAPE_PUBLIC_DASHBOARD` | `1` deixa o painel visível sem login |
| `LAPE_BEHIND_HTTPS` | `1` marca o cookie como `Secure` — **use sempre que houver HTTPS** |
| `LAPE_ADMIN_LOGIN` / `LAPE_ADMIN_PASSWORD` | Primeiro administrador, criado na subida |
| `LAPE_API_TOKEN` | Token de serviço para scripts e CI (vale como admin) |
| `LAPE_SESSION_DAYS` | Validade da sessão (padrão: 14) |
| `SCOPUS_API_KEY`, `SCOPUS_INST_TOKEN`, `WOS_API_KEY` | Bases proprietárias |
| `LAPE_CONTACT_EMAIL` | E-mail de contato para o *polite pool* do Crossref/OpenAlex |

---

## Os dois agentes digitais

### Agente rastreador — busca informação lá fora

```bash
python3 scripts/lape_agent.py rastreador                 # as quatro tarefas
python3 scripts/lape_agent.py rastreador enriquecer
python3 scripts/lape_agent.py rastreador citar
python3 scripts/lape_agent.py rastreador perfis
python3 scripts/lape_agent.py rastreador descobrir --desde 2020
```

| Tarefa | O que faz | Fonte |
|---|---|---|
| `descobrir` | Acha publicações dos integrantes que ainda não estão no banco | OpenAlex (por ORCID ou nome + instituição) |
| `enriquecer` | Preenche DOI, periódico, ISSN, ano e link dos artigos incompletos | Crossref + OpenAlex, casando pelo título |
| `citar` | Atualiza citações e guarda o histórico | OpenAlex (aberta), Scopus e Web of Science (com chave) |
| `perfis` | Traz **índice h**, i10 e total de citações de cada pesquisador | Perfil público do OpenAlex |

O que ele encontra fica **pendente de aprovação** — nada entra direto:

```bash
python3 scripts/lape_agent.py revisar --list
python3 scripts/lape_agent.py revisar --aceitar 12 15
python3 scripts/lape_agent.py revisar --auto     # aceita as que têm 2+ autores já cadastrados
```

Ou, pela web, em **Área do integrante → Administração**.

### Agente curador — mantém o banco

```bash
python3 scripts/lape_agent.py curador              # ciclo completo
python3 scripts/lape_agent.py curador --offline    # sem consultar as bases
python3 scripts/lape_agent.py curador --janela 10  # análises de 10 anos
python3 scripts/lape_agent.py status               # resumo e lacunas
```

Carrega planilhas e Lattes, consolida grafias de nomes, deriva status e datas,
recalcula o índice h, valida e regenera o painel.

**Regra que vale em todo o sistema:** o que o laboratório digitou nunca é
sobrescrito por fonte externa. Os agentes só preenchem campos vazios.

---

## API REST

| Rota | Método | Perfil | Descrição |
|---|---|---|---|
| `/api/auth/login` | POST | — | `{"login": "...", "senha": "..."}` |
| `/api/auth/logout` | POST | — | Encerra a sessão |
| `/api/auth/me` | GET | — | Quem está autenticado |
| `/api/auth/senha` | POST | leitura | `{"atual": "...", "nova": "..."}` |
| `/api/auth/usuarios` | POST | admin | Cria acesso para um integrante |
| `/api/health` | GET | — | Status e contagens |
| `/api/metrics[/<bloco>]` | GET | leitura | Todos os indicadores em JSON |
| `/api/articles` | GET/POST | leitura / integrante | Filtros: `status`, `linha`, `ano`, `q`, `limit`, `offset` |
| `/api/articles/<id>` | GET | leitura | Artigo com autores, submissões, marcos e histórico de citações |
| `/api/researchers/<id>` | GET | leitura | Ficha do pesquisador: projetos, artigos, coautores, índice h |
| `/api/submissions`, `/api/projects`, `/api/events`, `/api/members`, `/api/research-lines`, `/api/institutions` | GET/POST | — | Idem para as demais entidades |
| `/api/discoveries` | GET | leitura | Achados pendentes do rastreador |
| `/api/discoveries/<id>/review` | POST | coordenação | `{"action": "aceitar"}` ou `"ignorar"` |
| `/api/agents/tracker` | POST | coordenação | Dispara o rastreador |
| `/api/agents/curator` | POST | coordenação | Dispara o ciclo completo |
| `/api/audit` | GET | coordenação | Registro de atividade |
| `/api/export/sqlite` | GET | admin | Baixa o banco |

O `POST` aceita **os mesmos nomes de coluna das planilhas**:

```bash
# 1. entra e guarda o cookie
curl -c cookies.txt -X POST http://127.0.0.1:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login":"andrade@udesc.br","senha":"..."}'

# 2. cadastra um artigo
curl -b cookies.txt -X POST http://127.0.0.1:8000/api/articles \
  -H 'Content-Type: application/json' \
  -d '{"Título":"Ansiedade competitiva em nadadores",
       "Autores":"Andrade; Vilarino; Loiane",
       "Status":"Publicado","Ano":2024,
       "Periódico":"Journal of Sports Sciences",
       "DOI":"10.1080/02640414.2024.1234",
       "Data de submissão":"2023-11-10","Data do aceite":"2024-03-15",
       "Linha de pesquisa":"Psicologia do Esporte e do Exercício"}'
```

Para scripts e CI, use o token de serviço em vez do cookie:

```bash
export LAPE_API_TOKEN="uma-senha-longa"
curl -H "Authorization: Bearer $LAPE_API_TOKEN" http://127.0.0.1:8000/api/metrics
```

---

## O que o painel mostra

Servido em `/` (ao vivo) e exportado em `docs/index.html` (arquivo único, sem
dependências externas, funciona offline e no GitHub Pages). Tema claro/escuro,
imprimível, com barra de filtros, tabelas ordenáveis e ficha de pesquisador em
painel lateral.

**Filtros no topo** — linha de pesquisa, ano, integrante e busca livre. Os
blocos marcados como *filtrável* respondem na hora; os demais mostram o
laboratório inteiro.

| Seção | Conteúdo |
|---|---|
| Visão geral | KPIs, situação dos artigos, publicações por ano com acumulado, funil da produção, produção por linha |
| Índice de linhas de pesquisa | Uma ficha por linha; clique para filtrar o painel |
| **Banco de pesquisadores** | Nome, linha, projetos, artigos, publicados, submetidos, **índice h** e citações — ordenável, com ficha completa ao clicar |
| **Projetos** | Coordenação, financiador, equipe, vigência, situação e recursos |
| Artigos em produção | Título, início, autores, tempo em aberto, carga por responsável |
| Artigos submetidos | Revista, data, tentativas, tempo em avaliação |
| Publicações por ano | Total, média anual, série histórica, periódicos mais usados |
| Artigos mais citados | Scopus, Web of Science e OpenAlex — geral e últimos 5 anos |
| Artigos por integrante | Envolvimento por etapa, respeitando os filtros |
| Rede de colaboração | Grafo de coautoria clicável, densidade, grau médio, duplas mais produtivas |
| Tempos do ciclo editorial | Início→publicação, submissão→aceite, aceite→publicação |
| Submissões e recusas | Tentativas por artigo, intervalos entre submissões, motivos das recusas, revistas |
| Datas de aceite | Aceites com o tempo desde a primeira submissão |
| Calendário e atividades | Calendário navegável, próximas atividades, tipos |
| Linha do tempo | Mapa de calor ano × mês e evolução anual comparada |
| Distribuição espacial | Mapa de atividades e instituições parceiras |
| Achados do rastreador | Publicações encontradas aguardando aprovação |
| Qualidade dos dados | Lacunas a preencher e histórico de cargas |

Para publicar a versão estática no GitHub Pages: **Settings → Pages → Deploy
from a branch → pasta `/docs`**.

---

## Os dados de entrada

Coloque qualquer `.xlsx`, `.xls` ou `.csv` em `data/raw/`. O importador
reconhece abas e colunas pelo nome, tolerando acentuação, maiúsculas e
sinônimos — não é preciso renomear nada.

### Planilha do laboratório (já suportada)

`LAPE_Gestao_Indicadores_Cientificos_v3.xlsx`

| Aba | Vira |
|---|---|
| Pipeline de Artigos | Artigos, equipe, responsável e marcos de versão |
| Tentativas de Submissão | Uma submissão por bloco (formato largo → longo automaticamente) |
| Métricas / Histórico Mensal / Como usar | Ignoradas — o painel recalcula esses números |

### Planilha complementar (gerada por `make_templates.py`)

`LAPE_cadastros.xlsx`, com **Integrantes**, **Linhas de Pesquisa**,
**Instituições**, **Publicações**, **Projetos**, **Eventos** e **Motivos de
recusa**. A aba Integrantes já vem preenchida com os nomes encontrados nas
outras planilhas.

> **A coluna `Variações` é a mais importante.** Liste ali, separadas por ponto
> e vírgula, todas as grafias da mesma pessoa (`Alexandro; Andrade;
> ANDRADE, A.`). É isso que faz a rede de colaboração, a contagem por
> integrante e o índice h ficarem corretos. `lape_agent.py status` aponta as
> duplicatas suspeitas.

### Currículo Lattes

No currículo em lattes.cnpq.br, clique no ícone **XML** (“Exportar / Currículo
em XML”) e salve o `.zip` em `data/raw/` com `lattes` no nome — por exemplo
`data/raw/lattes_alexandro_andrade.zip`. O parser lê artigos publicados,
artigos aceitos e trabalhos em eventos, e mescla pelo título.

> A raspagem direta de `buscatextual.cnpq.br` não é usada: aquela página exige
> sessão e CAPTCHA. O XML é o caminho oficial e estável.

### Sem chave de API o sistema continua funcionando

O **OpenAlex** é aberto e já fornece contagem de citações para todo artigo com
DOI, além do índice h de quem tiver ORCID cadastrado. Scopus e Web of Science
entram quando as chaves existirem.

---

## Automação

`.github/workflows/lape.yml` roda toda segunda-feira às 9h (e a cada envio de
planilha nova): executa os testes, o curador e o rastreador, e faz commit do
banco e do painel atualizados. As chaves vão em **Settings → Secrets and
variables → Actions**.

Num servidor próprio, agende o curador no cron e deixe o site no ar:

```cron
0 6 * * *  cd /opt/lape && python3 scripts/lape_agent.py curador >> logs/lape.log 2>&1
0 3 * * *  /opt/lape/deploy/backup.sh
```

---

## Estrutura do projeto

```
sql/schema.sql              esquema (16 tabelas + 8 views analíticas)
scripts/
  lape_agent.py             console: rastreador, curador, api, usuarios, revisar, status
  run_pipeline.py           pipeline direto, sem os agentes
  make_templates.py         gera a planilha complementar de cadastros
  migrate.R                 aplica o mesmo schema.sql pelo R
  lape/
    config.py               caminhos, janela de análise, credenciais
    util.py                 normalização de datas, nomes e títulos
    mapping.py              sinônimos de abas, colunas e vocabulário controlado
    db.py                   SQLite: upserts idempotentes, fusão de integrantes
    auth.py                 senhas, sessões e permissões
    ingest_excel.py         planilhas → banco (formato largo → longo incluso)
    ingest_lattes.py        XML do Lattes → banco
    ingest_citations.py     Scopus e Web of Science
    sources.py              OpenAlex, Crossref, PubMed (só biblioteca padrão)
    metrics.py              indicadores, índice h, rede, séries temporais
    report.py               gera o painel HTML
    api.py                  site + API REST
    agents/tracker.py       agente rastreador
    agents/curator.py       agente curador
    templates/              painel, login, área do integrante, CSS comum
data/raw/                   planilhas e XML do Lattes (entrada)
data/geo/                   GeoJSON opcional para o mapa
docs/index.html             painel estático (saída)
deploy/                     systemd, nginx e backup
Dockerfile, docker-compose.yml, render.yaml, fly.toml
tests/                      64 testes, sem acesso à rede
```

O `scripts/migrate.R` continua funcionando: aplica o mesmo `sql/schema.sql`,
então quem preferir analisar em R lê o mesmo banco.

---

## Testes

```bash
python3 -m unittest discover -s tests -v
```

Conferem a ingestão contra os números que a própria planilha do laboratório
calcula (por exemplo, os 12,5 dias médios entre uma recusa e a nova submissão),
sobem um servidor HTTP real para testar login, permissões e cadastro, e
substituem as bases externas por respostas gravadas — rodam sem rede.
