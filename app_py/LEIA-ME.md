# ELASE · Sistema de prescrição e análise de desempenho

Voleibol masculino adulto. Python e SQLite, **sem instalar nada**.

```bash
cd app_py
python3 abrir.py
```

Sobe o servidor **e** procura sozinho um endereço para os atletas: tenta o
`cloudflared` que já exista, baixa o certo para o seu sistema se não existir, e
cai no `ssh` (localhost.run) se o download não for. Cada falha diz o motivo e o
que fazer — nenhuma delas deixa você sem saída, porque o endereço da **rede
local** aparece antes de qualquer túnel e não depende de internet.

Para não tentar túnel nenhum:

```bash
python3 abrir.py --rede      # só a rede local (mesmo wi-fi)
python3 elase.py             # só localhost, o modo mais simples
```

Abre em <http://localhost:8000>. O banco (`elase.db`) é criado na primeira
execução, já com a periodização em blocos e a biblioteca de exercícios.

O PIN inicial do preparador é **1234** — troque na aba **Elenco**.

---

## O link para o atleta: leia isto antes

O app serve uma página que o atleta abre no celular dele, se cadastra e entra
na própria área. **Mas o link só funciona se o celular dele conseguir alcançar
o computador onde o servidor está rodando.** Em `localhost` a página só abre na
máquina que está rodando o programa. Isso não é limitação do app — é como
funciona qualquer servidor.

Há três caminhos, do mais simples ao mais definitivo:

### 1. A rede do ginásio (mesmo wi-fi) — funciona hoje, de graça

```bash
python3 elase.py --host 0.0.0.0
```

Descubra o endereço da máquina na rede:

```bash
hostname -I | awk '{print $1}'      # Linux
ipconfig getifaddr en0              # macOS
ipconfig                            # Windows: "Endereço IPv4"
```

O link vira `http://192.168.0.15:8000` (com o número que apareceu). Quem
estiver no **mesmo wi-fi** abre normalmente.

Serve para: treino na academia, cadastro do elenco inteiro em dez minutos,
check-in e registro de série durante a sessão.
Não serve para: o atleta preencher em casa.

### 2. Um túnel temporário — endereço público sem hospedar

```bash
python3 abrir.py
```

Faz tudo sozinho. Se der certo, imprime o endereço `https://...` numa caixa,
com o link do cadastro pronto para copiar. Vale **enquanto o programa estiver
aberto**, e o endereço muda a cada vez que você abre — bom para a primeira
rodada de cadastros, ruim como solução permanente.

**Se não abrir**, o programa diz o motivo que leu do próprio túnel. Os três
casos comuns:

| O que aparece | O que é | O que fazer |
|---|---|---|
| `not in allowlist`, `403`, `connection refused` | a rede bloqueia | teste no 4G do celular compartilhando internet |
| `esta máquina não tem ssh` e o download falhou | sem saída para a internet | use a rede local (caminho 1) |
| trava sem dizer nada | antivírus barrou o cloudflared | libere, ou use a rede local |

Em qualquer um deles a **rede local continua funcionando** e basta para
cadastrar o elenco no ginásio.

### 3. Hospedagem de verdade — endereço fixo, sempre no ar

Qualquer serviço que rode Python serve (Render, Railway, Fly.io,
PythonAnywhere, ou uma VPS). O app não tem dependência nenhuma, então o deploy
é copiar a pasta e rodar `python3 elase.py --host 0.0.0.0 --porta $PORT`.

**Antes de pôr na internet aberta**, três coisas:

1. Troque o PIN na aba Elenco. O padrão está escrito aqui neste arquivo.
2. Use HTTPS (os serviços acima já dão). O PIN viaja no cabeçalho do pedido; em
   HTTP puro qualquer um na rede lê.
3. O `elase.db` guarda contato de emergência e histórico de lesão. É dado de
   saúde: faça backup e não deixe a pasta exposta.

O PIN é tranca de porta de sala, não de cofre: impede o atleta de abrir a
prescrição sem querer. Não é autenticação forte e o app não finge que é.

---

## As onze abas

| Aba | Quem usa | O que faz |
|---|---|---|
| **Início** | todos | Situação do macrociclo e o link do cadastro |
| **Cadastro** | atleta | Ficha em um formulário; com cadastro liberado ele entra na hora |
| **Minha Sessão** | atleta | Check-in, série a série com carga e reps, check-out com PSE |
| **Bem-estar** | atleta | Sono, dor, estresse, KSS e os 24 itens da BRUMS |
| **Análise** | todos | ACWR, monotonia, strain, prontidão e Z por subescala |
| **Testes** | todos | Bateria específica do voleibol: saltos, 1RM, sprints, agilidade |
| **Exercícios** | preparador | Biblioteca com dica técnica e o vídeo de cada movimento |
| **Elenco** | preparador | Quem está no grupo, ativação e configuração |
| **Prescrição** | preparador | O que está montado, com carga prevista e contatos |
| **Sistema** | preparador | Gera o microciclo semana após semana, sem teto |
| **SQL** | preparador | Console de leitura sobre o banco |

## O sistema de treinamento

Três sessões de sala por semana (segunda, quarta, sexta). O resto é quadra, e a
carga de quadra entra pela PSE do check-out.

Toda sessão tem a mesma ordem: **mobilidade → educativo de LPO → barra**.

- **A · Força máxima** — arranco, agachamento, supino, posterior, ombro, core
- **B · Potência** — clean, jump squat, drop jump, caixote, dorsais
- **C · Força-velocidade** — snatch pull, agachamento frontal, barreiras, sprints

### Mobilidade articular

Tornozelo, quadril e ombro em **toda** sessão, cada um pelo motivo dele:

| Articulação | Por que entra | Exemplos |
|---|---|---|
| **Tornozelo** | sem dorsiflexão não se agacha fundo nem se aterrissa bem — e aterrissagem é o gesto mais repetido do voleibol | knee-to-wall, panturrilha no step, agachamento profundo sustentado |
| **Quadril** | fecha a profundidade do agachamento e absorve o salto | 90/90 com rotação, cossaco, psoas ajoelhado, hip airplane |
| **Ombro e torácica** | quem ataca centenas de bolas por semana perde amplitude e rotação interna do lado dominante | passagem de bastão, deslizamento na parede, cross-body, open book, extensão no rolo |

Os exercícios giram entre as três sessões: mesma articulação, estímulo
diferente, e ninguém repete a mesma coisa três vezes por semana até enjoar.

**"Rotadores do ombro com elástico" não é mobilidade** — é força do manguito, e
continua no grupo Força. As duas coisas entram, e são diferentes.

### Educativos de LPO

A progressão vai da **posição** ao movimento inteiro. Quem pula etapa aprende a
compensar, e compensação sob carga é como se machuca.

- **Arranco** — agachamento overhead → arranco de força → snatch balance → arranco do alto
- **Clean** — front rack → tall clean → clean de força → clean do joelho
- **Impulsão** — tríplice extensão com bastão → push press → split jerk educativo

Entram **antes** da barra pesada: é com o sistema nervoso descansado que se
aprende técnica. O volume cai conforme o macrociclo avança (4 educativos na
acumulação, 2 na realização) mas **nunca chega a zero** — a técnica do arranco
se perde em duas semanas sem toque.

### Vídeos

Cada exercício tem um botão de vídeo na tela do atleta, e uma dica técnica
escrita ao lado do nome.

Os vídeos **não vêm preenchidos com links prontos**, e isso é deliberado: eu não
consigo assistir a um vídeo para conferir se ele mostra o movimento certo, e
demonstração errada num app de treino não é link quebrado — é risco de lesão.
Então o botão abre uma **busca**, que sempre funciona e mostra várias fontes
para comparar.

Na aba **Exercícios** você fixa o vídeo que quiser em cada um; a partir daí é o
seu que o atleta vê. O melhor de todos é filmar um atleta do próprio elenco
executando: é o padrão que você quer que copiem, com a sua linguagem.

Há sugestões prontas para os **educativos de arranco**, da Exercise Library da
Catalyst Athletics (Greg Everett) — uma fonte só, um vídeo curto por exercício:

```bash
python3 videos_sugeridos.py            # mostra a lista, não grava nada
python3 videos_sugeridos.py --aplicar  # grava, depois de você confirmar
```

Ele nunca sobrescreve um vídeo que você já fixou.

**Para a mobilidade de ombro não há sugestão pronta**, e o motivo está no
arquivo: não existe uma biblioteca única equivalente à da Catalyst, e espalhar
links de canais avulsos numa tela que o atleta segue sozinho é o contrário do
que este projeto faz. Filme os seus.

### Por que o ombro entra em toda sessão

O que sustenta a escolha, para quando alguém perguntar:

- **GIRD** (déficit de rotação interna glenoumeral) é o achado mais comum no
  atleta de gesto acima da cabeça, e vem da repetição do ataque e do saque.
  Há ensaio randomizado em **voleibolistas masculinos** com déficit de rotação
  interna testando exercício com faixa elástica ([Springer, BMC Musculoskelet
  Disord 2020](https://link.springer.com/article/10.1186/s12891-020-03414-y)).
- **A torácica vem antes do ombro.** Amplitude acima da cabeça depende de
  extensão torácica; déficit ali joga o estresse para o resto da cadeia
  ([revisão de triagem, NASM](https://www.nasm.org/resource-center/blog/training/shoulder-mobility-for-overhead-athletes-a-screening-guide)).
  Há ensaio randomizado de mobilidade torácica em voleibolistas adolescentes
  ([BMC Sports Sci Med Rehabil](https://link.springer.com/article/10.1186/s13102-026-01618-8)).
- **Mobilidade e estabilidade são coisas diferentes** e as duas entram: a
  amplitude pelo alongamento e pela torácica, o controle pelo wall slide, Y-T-W
  e rotação externa com faixa — que no app estão no grupo Força, não Mobilidade.

Séries, repetições e %1RM saem da posição no macrociclo; os contatos
pliométricos saem do campo `plio` do bloco, repartidos **entre os exercícios**
da semana. A periodização é editável na aba Elenco e o gerador acompanha.

**Os oito blocos são um macrociclo, não a temporada.** A semana 9 é a posição 1
do ciclo 2; a semana 100 é a posição 4 do ciclo 13. A última sexta de cada
Realização é um **reteste** de 1RM e salto — é ele que faz o ciclo seguinte
valer mais, porque os mesmos 85% passam a significar mais quilos.

Gerar nunca sobrescreve: dia que já tem sessão prescrita é pulado.

## O que o sistema recusa fazer

- **ACWR com menos de 21 dias** não recebe zona de risco; a tela diz que o
  histórico é curto. Um ACWR de dez dias parece diagnóstico e não é.
- **Z de humor sem 6 coletas com variação** não existe. Base sem desvio não tem
  desvio padrão, e sem ele não há Z.
- **Monotonia com desvio zero** é indefinida, não zero. Devolver 0 se leria
  como "ótima variação" quando é o caso máximo.
- **Componente de prontidão que falta** é excluído da média, não contado como
  zero. Quem não respondeu a BRUMS não é quem está com o humor péssimo.
- **Nenhum dado financeiro.** Não há coluna de salário ou renda no banco, e um
  teste automatizado garante que não volte a haver.

## Testes

```bash
python3 testes.py                       # 52 testes: banco, análise, sistema, API
node teste_tela.js                      # 35 verificações no navegador (servidor de pé)
```

O teste de navegador precisa do Playwright e do servidor rodando na porta 8777
(ou defina `BASE=http://127.0.0.1:porta`).

## Arquivos

```
app_py/
  elase.py        servidor HTTP e rotas da API
  banco.py        esquema SQL, conexão, constantes da BRUMS
  analise.py      ACWR, monotonia, strain, Z, quartis, Spearman, prontidão
  sistema.py      gerador do microciclo, sem limite de semanas
  testes.py       testes de unidade e de API
  teste_tela.js   teste de interface no navegador
  videos_sugeridos.py  sugestões de vídeo para os educativos de arranco
  web/            index.html, app.js, estilo.css
  elase.db        banco (criado ao rodar; não vai para o repositório)
```

## Backup

O banco é um arquivo só. Copie `elase.db` e está feito. Com o servidor parado,
a cópia é consistente; com ele rodando, copie também `elase.db-wal`.
