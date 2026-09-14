# ELASE · Sistema de prescrição e análise de desempenho

Voleibol masculino adulto. Python e SQLite, **sem instalar nada**.

```bash
cd app_py
python3 elase.py
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

Com `cloudflared` ou `ngrok` instalado:

```bash
cloudflared tunnel --url http://localhost:8000
```

Ele devolve um endereço `https://...` que funciona de qualquer lugar,
**enquanto o comando estiver rodando**. Bom para a primeira rodada de
cadastros; ruim como solução permanente (o endereço muda a cada vez).

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

## As dez abas

| Aba | Quem usa | O que faz |
|---|---|---|
| **Início** | todos | Situação do macrociclo e o link do cadastro |
| **Cadastro** | atleta | Ficha em um formulário; com cadastro liberado ele entra na hora |
| **Minha Sessão** | atleta | Check-in, série a série com carga e reps, check-out com PSE |
| **Bem-estar** | atleta | Sono, dor, estresse, KSS e os 24 itens da BRUMS |
| **Análise** | todos | ACWR, monotonia, strain, prontidão e Z por subescala |
| **Testes** | todos | Bateria específica do voleibol: saltos, 1RM, sprints, agilidade |
| **Elenco** | preparador | Quem está no grupo, ativação e configuração |
| **Prescrição** | preparador | O que está montado, com carga prevista e contatos |
| **Sistema** | preparador | Gera o microciclo semana após semana, sem teto |
| **SQL** | preparador | Console de leitura sobre o banco |

## O sistema de treinamento

Três sessões de sala por semana (segunda, quarta, sexta). O resto é quadra, e a
carga de quadra entra pela PSE do check-out.

- **A · Força máxima** — arranco, agachamento, supino, posterior, ombro, core
- **B · Potência** — clean, jump squat, drop jump, caixote, dorsais
- **C · Força-velocidade** — snatch pull, agachamento frontal, barreiras, sprints

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
python3 testes.py                       # 42 testes: banco, análise, sistema, API
node teste_tela.js                      # 30 verificações no navegador (servidor de pé)
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
  web/            index.html, app.js, estilo.css
  elase.db        banco (criado ao rodar; não vai para o repositório)
```

## Backup

O banco é um arquivo só. Copie `elase.db` e está feito. Com o servidor parado,
a cópia é consistente; com ele rodando, copie também `elase.db-wal`.
