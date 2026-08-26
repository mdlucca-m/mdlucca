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
- [Publicar na nuvem — custo zero](#publicar-na-nuvem--custo-zero)
- [Camadas de dados (lakehouse)](#camadas-de-dados-lakehouse)
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

## Publicar na nuvem — custo zero

O sistema inteiro é um contêiner só, e o que precisa sobreviver é **um
arquivo**: o banco SQLite. Isso permite três caminhos sem nenhuma mensalidade.

> Planos gratuitos de plataformas mudam com frequência, e quase nenhum oferece
> **disco persistente** de graça — sem disco, o banco é apagado a cada nova
> versão. Por isso os caminhos abaixo não dependem de plano gratuito de
> fornecedor nenhum.

### Caminho 1 — computador do laboratório + túnel do Cloudflare

**O mais simples, e o único que não pede cartão de crédito.** Um computador do
LAPE que fique ligado vira o servidor; o túnel do Cloudflare dá um endereço
`https://` público sem abrir uma única porta no firewall da universidade.

```bash
git clone https://github.com/mdlucca-m/mdlucca.git lape && cd lape
sudo bash deploy/instalar.sh          # escolha a opção 2 (túnel)
```

O instalador pergunta o token do túnel e os dados do administrador, instala o
Docker e sobe tudo. O token sai de <https://one.dash.cloudflare.com> →
**Networks → Tunnels → Create a tunnel**, apontando o serviço para
`http://lape:8000`.

| Prós | Contras |
|---|---|
| Zero real, sem cartão | Depende de a máquina ficar ligada |
| Nenhuma porta aberta no firewall | O endereço cai se a máquina desligar |
| HTTPS pelo Cloudflare | |

### Caminho 2 — VM sempre gratuita (Oracle Cloud)

A camada **Always Free** da Oracle Cloud inclui máquinas ARM Ampere que não
expiram, com disco próprio. Dá um servidor de verdade, ligado o tempo todo.
Exige cartão só para verificação de identidade.

```bash
# na VM recém-criada (Ubuntu):
git clone https://github.com/mdlucca-m/mdlucca.git lape && cd lape
sudo bash deploy/instalar.sh          # escolha a opção 1 (IP público)
```

Você precisa de um domínio apontando para o IP. Sem domínio próprio, registre
um gratuito em <https://duckdns.org> (`lape.duckdns.org`). O **Caddy** pede,
instala e renova o certificado HTTPS sozinho — nada a configurar nem a pagar.

Depois de criar a VM, libere as portas 80 e 443 em **VCN → Security Lists →
Ingress Rules** (o instalador cuida do firewall de dentro da máquina).

| Prós | Contras |
|---|---|
| Ligado 24h, endereço fixo | Cadastro exige cartão (não é cobrado) |
| Disco persistente de verdade | Precisa de um domínio (gratuito serve) |
| HTTPS automático e renovado sozinho | |

### Caminho 3 — servidor da própria universidade

Se a UDESC ceder uma máquina ou VM, é o mesmo comando do Caminho 2, com um
domínio `lape.udesc.br` apontado pelo setor de TI. Para rodar sem Docker,
use `deploy/lape.service` (systemd) com `deploy/nginx.conf` na frente.

### Painel público sem servidor (opcional)

Só o painel, sem login nem cadastro, pode ir para o **GitHub Pages** — grátis e
sem máquina nenhuma. É opcional e desligado por padrão: rode o workflow
manualmente em **Actions → LAPE → Run workflow** marcando *Publicar o painel no
GitHub Pages*.

> A página fica **pública na internet**, com títulos de artigos, nomes dos
> integrantes, histórico de submissões e motivos de recusa. Só ligue se o
> laboratório quiser mesmo essa vitrine.

### Depois de subir, em qualquer caminho

```bash
# carregar planilhas e recalcular tudo
docker compose -f docker-compose.prod.yml exec lape \
  python3 scripts/lape_agent.py curador

# liberar acesso a um integrante (ou faça pela web, em /app → Administração)
docker compose -f docker-compose.prod.yml exec lape \
  python3 scripts/lape_agent.py usuarios --criar "Nome" email@udesc.br

# acompanhar
docker compose -f docker-compose.prod.yml logs -f lape
```

Backup: `deploy/backup.sh` usa `sqlite3.backup`, que respeita transações em
andamento — copiar o arquivo direto pode gerar um banco corrompido.

### Variáveis de ambiente

| Variável | Para quê |
|---|---|
| `LAPE_DOMINIO` | Domínio usado pelo Caddy no `docker-compose.prod.yml` |
| `CLOUDFLARE_TUNNEL_TOKEN` | Token do túnel (Caminho 1) |
| `LAPE_DB` | Caminho do banco (na nuvem, aponte para o volume) |
| `LAPE_HOST` / `LAPE_PORT` | Onde o servidor escuta (`0.0.0.0` em contêiner) |
| `LAPE_PUBLIC_DASHBOARD` | `1` deixa o painel visível sem login |
| `LAPE_BEHIND_HTTPS` | `1` marca o cookie como `Secure` — **use sempre que houver HTTPS** |
| `LAPE_ADMIN_LOGIN` / `LAPE_ADMIN_PASSWORD` | Primeiro administrador, criado na subida |
| `LAPE_API_TOKEN` | Token de serviço para scripts e CI (vale como admin) |
| `LAPE_SESSION_DAYS` | Validade da sessão (padrão: 14) |
| `SCOPUS_API_KEY`, `SCOPUS_INST_TOKEN`, `WOS_API_KEY` | Bases proprietárias |
| `LAPE_CONTACT_EMAIL` | E-mail de contato para o *polite pool* do Crossref/OpenAlex |

Copie `.env.example` para `.env` e ajuste. O `.env` não vai para o repositório.

---

## Camadas de dados (lakehouse)

O mesmo banco guarda três camadas, cada uma com um trabalho diferente.

| Camada | Onde | O que é | Some se apagar? |
|---|---|---|---|
| **Bronze** | `data/lake/bronze/<data>/` | O arquivo cru, como chegou, com `sha256` e tamanho | Não — dá para recapturar |
| **Prata** | `data/db.sqlite` (`sql/schema.sql`) | Dado operacional, normalizado — **a fonte de verdade** | Sim |
| **Ouro** | tabelas `fact_*`/`dim_*` + Parquet | Modelo dimensional para consulta rápida | Não — é reconstruída |

**Por que bronze existe:** se amanhã o importador mudar, a planilha daquele dia
continua guardada, com impressão digital, para reprocessar. **Por que ouro
existe:** um cruzamento "medida × recorte" vira um único `JOIN`, em vez de
percorrer o modelo operacional.

```bash
python3 scripts/lape_agent.py lake                        # bronze → ouro → medição
python3 scripts/lape_agent.py lake --exportar             # + Parquet (ou CSV)
python3 scripts/lape_agent.py lake --linhagem             # de onde veio cada carga
python3 scripts/lape_agent.py lake --consultar publicados linha
```

O curador já chama o lakehouse no fim do ciclo — não é preciso rodar à mão.

### Histórico medido

A cada execução, `metric_snapshot` grava o valor de 14 indicadores (total e por
linha de pesquisa). É isso que faz o painel mostrar **“▲ 3 em 30 dias”** com
número medido, e não estimado. Essa tabela sobrevive à reconstrução da camada
ouro — apagar os fatos não apaga a série.

### Consulta analítica

A camada ouro expõe **11 medidas × 10 dimensões**, combináveis com quebra e
filtro. O cliente nunca escreve SQL: escolhe chaves de uma lista, e cada chave
traz a expressão pronta.

```bash
curl -b cookies.txt 'http://127.0.0.1:8000/api/query?medida=citacoes&por=ano_publicacao&quebra=linha'
curl -b cookies.txt 'http://127.0.0.1:8000/api/catalog'    # o que existe
```

| Medidas | Dimensões |
|---|---|
| artigos, publicados, submetidos, em produção, citações, citações por artigo, tentativas, recusas, dias até publicar, dias até aceite, autores por artigo | linha, situação, ano, ano de publicação, periódico, Qualis, tipo de estudo, responsável, idioma, origem do registro |

Filtros aceitos: `linha`, `status`, `ano`, `periodico`, `qualis`, `responsavel`,
`integrante`, `de`, `ate`.

### Saída para outras ferramentas

`lake --exportar` grava a camada ouro em **Parquet** (formato colunar que abre
no pandas, no R via `arrow`, no DuckDB e no Power BI sem precisar do SQLite).
Sem o `pyarrow` instalado, a exportação cai para CSV automaticamente:

```bash
pip install pyarrow      # opcional; fora dele, CSV
```

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
| `/api/state` | GET | leitura | Consulta barata: mudou alguma coisa? |
| `/api/catalog` | GET | leitura | Medidas e dimensões disponíveis |
| `/api/query` | GET | leitura | `?medida=&por=&quebra=&linha=&ano=…` |
| `/api/history` | GET | leitura | `?metrica=publicados` — série medida |
| `/api/lake/lineage` | GET | coordenação | De onde veio cada carga |
| `/api/agents/lake` | POST | coordenação | Reconstrói o lakehouse |
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
dependências externas, funciona offline e no GitHub Pages).

**Navegação por abas.** Cada aba é plotada no momento em que você entra nela,
contra o recorte atual — nada é desenhado à toa. Ao vivo, o painel reconfere os
dados a cada 25 s por uma consulta barata (`/api/state`) e só recarrega tudo
quando algo mudou; durante a recarga o desenho anterior fica no lugar, sem
esqueleto e sem salto.

**Barra de filtros única, acima de tudo.** Ano em botões (é o filtro que todo
mundo procura primeiro), linha, situação, integrante e busca livre. Mais o
seletor **“Segmentar por”**, que muda a dimensão de agrupamento dos gráficos.

**Toda figura tem par em tabela.** Cada gráfico traz os botões `Tabela` e `CSV`:
nenhum valor existe apenas dentro de uma dica de mouse. As tabelas ordenam por
qualquer coluna, filtram, paginam e exportam.

| Aba | Conteúdo |
|---|---|
| Visão geral | KPIs com variação medida e minigráfico, rosca por segmento, colunas por ano com régua de média, funil da produção, treemap por linha |
| **Explorar dados** | Medida × recorte × quebra × forma, refeito na hora pela camada analítica |
| Linhas de pesquisa | Ficha por linha + colunas empilhadas comparando etapas |
| Banco de pesquisadores | Índice h em ranking, dispersão produção × impacto, tabela ordenável, ficha em painel lateral |
| Projetos | KPIs, barras por financiador, halteres de vigência, tabela |
| Artigos em produção | Carga por responsável, distribuição de idade (quartis), tabela |
| Artigos submetidos | Espera mediana e máxima, tabela por revista |
| Publicações | Colunas por ano + acumulado, série histórica, periódicos mais usados |
| Artigos mais citados | Abas Scopus / WoS / OpenAlex, ranking, dispersão idade × impacto |
| Artigos por integrante | Colunas empilhadas por etapa, tabela cruzada |
| Rede de colaboração | Grafo de coautoria clicável, densidade, duplas mais produtivas |
| Tempos do ciclo editorial | Distribuição das três etapas, faixas de tempo, dispersão tentativas × tempo |
| Submissões e recusas | **Sankey** do caminho das submissões, tentativas, decisões, motivos, intervalos |
| Datas de aceite | Halteres submissão → aceite, tabela |
| Calendário e atividades | Calendário navegável, próximas atividades, tipos e anos |
| Linha do tempo | Mapa de calor ano × mês, evolução anual comparada, histórico medido |
| Distribuição espacial | Mapa de bolhas, locais, instituições |
| Achados do rastreador | Publicações aguardando aprovação |
| Qualidade e origem | Lacunas, últimas cargas e **linhagem** (arquivo, sha256, linhas) |

### Formas disponíveis

Colunas (simples, empilhadas, agrupadas, com linha de referência), barras
ranqueadas, linhas com mira que encontra o X, área, rosca com chamadas, funil,
dispersão com alvo de 24 px, halteres, mapa de calor sequencial, distribuição
(quartis + mediana + pontos), treemap, Sankey, rede de força, bolhas
geográficas, minigráfico e medidor.

### Sobre as cores

A paleta categórica foi **verificada por script** para daltonismo e contraste,
nos dois modos, sobre as superfícies em que o painel realmente desenha:

| | Pior par adjacente (protanopia) | Pior par (visão normal) |
|---|---|---|
| Claro | ΔE 9,1 | ΔE 19,6 |
| Escuro | ΔE 8,4 | ΔE 19,3 |

Regras que valem em todo o painel: cor categórica segue a **entidade**, nunca a
posição no ranking (filtrar não repinta quem sobrou); nunca se gera uma nona cor
— o excedente vira “Outros”; sequencial é um só matiz claro→escuro; dispersão,
bolha e mapa usam no máximo três séries (o limite que passa no teste de “todos
os pares”); e texto nunca veste a cor da série.

O modo escuro não é uma inversão automática: são os mesmos oito matizes
reposicionados para a superfície escura e verificados como conjunto.

Para publicar a versão estática no GitHub Pages, veja
[Publicar na nuvem](#publicar-na-nuvem--custo-zero).

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
sql/schema.sql              camada prata: esquema operacional
sql/gold.sql                camada ouro: modelo dimensional (fatos e dimensões)
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
    lake.py                 lakehouse: bronze, ouro, histórico e consulta analítica
    metrics.py              indicadores, índice h, rede, séries temporais
    report.py               gera o painel HTML
    api.py                  site + API REST
    agents/tracker.py       agente rastreador
    agents/curator.py       agente curador
    templates/
      theme.css             sistema de design e paleta verificada
      charts.js             biblioteca de gráficos (sem dependências)
      dashboard.html/.js    painel
      login.html, app.html  acesso e área do integrante
data/raw/                   planilhas e XML do Lattes (entrada)
data/geo/                   GeoJSON opcional para o mapa
data/lake/                  bronze e ouro (fora do git; em produção, no volume)
docs/index.html             painel estático (saída)
deploy/
  instalar.sh               instalação em um comando (Docker + HTTPS + admin)
  Caddyfile                 HTTPS automático e gratuito
  lape.service, nginx.conf  alternativa sem Docker
  backup.sh                 backup diário do banco
  healthcheck.py            verificação de saúde do contêiner
Dockerfile
docker-compose.yml          desenvolvimento
docker-compose.prod.yml     produção: aplicação + Caddy (+ túnel opcional)
.env.example                modelo de configuração
tests/                      96 testes, sem acesso à rede
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
sobem um servidor HTTP real para testar login, permissões, cadastro e as
consultas analíticas, e substituem as bases externas por respostas gravadas —
rodam sem rede.

Os testes do lakehouse cobrem as três camadas: deduplicação por `sha256` no
bronze, cálculo das durações e reconstrução sem duplicar no ouro, preservação do
histórico entre reconstruções, e a recusa de medidas, dimensões e filtros fora
da lista — inclusive com valores de filtro contendo SQL, que são tratados como
dado e não como comando.
