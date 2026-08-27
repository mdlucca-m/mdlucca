#!/usr/bin/env bash
# Põe o LAPE no ar com um endereço https público, sem Docker e sem conta.
#
#   bash deploy/publicar.sh
#
# Como funciona: o serviço continua escutando só em 127.0.0.1 (ninguém alcança
# a porta de fora), e o cloudflared abre uma conexão de SAÍDA até a Cloudflare,
# que devolve um endereço https. Nenhuma porta é aberta no firewall, nenhum IP
# público é necessário, e o certificado vem pronto.
#
# Sem opção nenhuma, o endereço é sorteado e MUDA a cada reinício. Para um
# endereço que não muda:
#
#   --fixo              endereço fixo grátis, sem domínio próprio (ngrok). Uma
#                       conta gratuita dá direito a um domínio reservado. No
#                       plano grátis, quem abre pela primeira vez vê uma página
#                       de aviso do ngrok antes do site.
#   --permanente        endereço fixo no seu domínio (Cloudflare). Sem página de
#                       aviso, mas exige um domínio hospedado na Cloudflare.
#   --dominio NOME      o domínio a usar, na primeira vez de cada modo
#   --porta N           porta local do serviço (padrão: 8000)
#   --endereco          diz qual é o endereço que está no ar agora
#   --parar             encerra o que este script deixou rodando
#   --sem-atualizar     não procura atualizações antes de subir
#
# Escolhido o modo uma vez, ele fica gravado: nas próximas vezes basta rodar
# o script sem opção nenhuma.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
PORTA=8000
PERMANENTE=0
FIXO=0
DOMINIO=""
TUNEL=lape
EXEC="$RAIZ/.lape-run"
ARQ_NGROK="$EXEC/dominio-ngrok.txt"
ARQ_CF="$EXEC/dominio-cloudflare.txt"
ARQ_END="$EXEC/endereco.txt"

azul()  { printf '\033[1;34m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
aviso() { printf '\033[1;33m! %s\033[0m\n' "$*"; }
erro()  { printf '\033[1;31m! %s\033[0m\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fixo) FIXO=1; shift ;;
    --permanente) PERMANENTE=1; shift ;;
    --dominio) DOMINIO="$2"; shift 2 ;;
    --tunel) TUNEL="$2"; shift 2 ;;
    --porta) PORTA="$2"; shift 2 ;;
    --endereco) mostrar_endereco=1; shift ;;
    --parar) parar_tudo=1; shift ;;
    --sem-atualizar) SEM_ATUALIZAR=1; shift ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) erro "opção desconhecida: $1" ;;
  esac
done

# Modo escolhido uma vez fica escolhido: rodar sem opção nenhuma não pode
# trocar o endereço fixo por um sorteado e matar o link que todos guardaram.
if [[ "$FIXO" == 0 && "$PERMANENTE" == 0 ]]; then
  if   [[ -f "$ARQ_CF"    ]]; then PERMANENTE=1
  elif [[ -f "$ARQ_NGROK" ]]; then FIXO=1
  fi
fi

parar_tunel() {
  pid="$(cat "$EXEC/tunel.pid" 2>/dev/null || true)"
  if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
  fi
  rm -f "$EXEC/tunel.pid"
}

parar() {
  for nome in api tunel; do
    # .pid vazio acontece quando uma subida anterior morreu antes de o
    # processo nascer: o teste do número evita agir sobre nada
    pid="$(cat "$EXEC/$nome.pid" 2>/dev/null || true)"
    if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      verde "Encerrado: $nome"
    fi
    rm -f "$EXEC/$nome.pid"
  done
  # endereço de serviço parado não é endereço
  rm -f "$ARQ_END"
}
if [[ "${parar_tudo:-0}" == 1 ]]; then parar; exit 0; fi

# Sobe em segundo plano e ninguém vê a tela onde o endereço é impresso. Este
# é o jeito de perguntar depois qual é o endereço de agora.
if [[ "${mostrar_endereco:-0}" == 1 ]]; then
  [[ -f "$ARQ_END" ]] || { aviso "O LAPE não está no ar. Suba com  bash deploy/publicar.sh"; exit 1; }
  echo
  verde "  Endereço de agora:"
  echo
  echo "    $(cat "$ARQ_END")/entrar"
  echo
  exit 0
fi

mkdir -p "$EXEC"
trap 'echo; aviso "Encerrando…"; parar; exit 0' INT TERM

# ------------------------------------------------------------ 0. atualização
# Quem sobe o serviço quer o serviço no ar, não um comando para decorar.
# A atualização acontece aqui, sozinha, antes de subir qualquer coisa.
#
# Três regras, todas para o mesmo fim -- nunca deixar o laboratório fora do
# ar por causa de uma atualização:
#   1. só puxa no ramo principal (ramo de trabalho é de quem sabe o que está
#      fazendo; não cabe ao script mexer);
#   2. só puxa sem alteração local pendente (nada é sobrescrito);
#   3. --ff-only: se divergiu, para e avisa em vez de inventar um merge.
# Falhar em qualquer ponto -- sem internet, sem git, ramo trocado -- vira um
# aviso amarelo, e o serviço sobe com o código que já está no disco.
atualizar_codigo() {
  if [[ "${SEM_ATUALIZAR:-0}" == 1 ]]; then azul "Atualização dispensada (--sem-atualizar)"; return; fi
  [[ -d "$RAIZ/.git" ]] || return 0
  command -v git >/dev/null || { aviso "git não encontrado: seguindo com o código que está no disco."; return 0; }
  local ramo antes depois quantas ultima
  ramo="$(git -C "$RAIZ" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [[ "$ramo" != "main" && "$ramo" != "master" ]]; then
    aviso "No ramo '${ramo:-?}': não atualizo sozinho, para não atrapalhar quem está trabalhando."
    return 0
  fi
  # `data/` fica de fora de propósito: ali mora o banco vivo, que muda a cada
  # cadastro. Se ele contasse como "alteração local", a atualização nunca
  # aconteceria na máquina do laboratório -- que é justamente a única máquina
  # onde ela precisa acontecer.
  if [[ -n "$(git -C "$RAIZ" status --porcelain -- . ':(exclude)data' 2>/dev/null)" ]]; then
    aviso "Há alterações locais no código: não vou sobrescrever. Seguindo com o código atual."
    return 0
  fi
  antes="$(git -C "$RAIZ" rev-parse HEAD 2>/dev/null || true)"
  azul "Procurando atualizações…"
  if ! git -C "$RAIZ" pull --ff-only > "$EXEC/atualizacao.log" 2>&1; then
    aviso "Não deu para atualizar agora -- seguindo com o código atual. O banco não foi tocado."
    tail -n 3 "$EXEC/atualizacao.log" 2>/dev/null | sed 's/^/  /'
    return 0
  fi
  depois="$(git -C "$RAIZ" rev-parse HEAD 2>/dev/null || true)"
  if [[ "$antes" == "$depois" ]]; then
    verde "Código já estava atualizado"
  else
    quantas="$(git -C "$RAIZ" rev-list --count "$antes..$depois" 2>/dev/null || echo '?')"
    verde "Código atualizado ($quantas mudança(s) nova(s))"
    ultima="$(git -C "$RAIZ" log -1 --pretty=%s 2>/dev/null || true)"
    [[ -n "$ultima" ]] && echo "  a mais recente: $ultima"
  fi
}
atualizar_codigo

# ------------------------------------------------------------------ 1. Python
command -v python3 >/dev/null || erro "Python 3 não encontrado. Instale-o e rode de novo."
python3 - <<'PY' || erro "É preciso Python 3.9 ou mais novo."
import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)
PY

# --------------------------------------------------------------- 2. cloudflared
CF="$EXEC/cloudflared"
if command -v cloudflared >/dev/null 2>&1; then
  CF="$(command -v cloudflared)"
elif [[ ! -x "$CF" ]]; then
  azul "Baixando o cloudflared (uma vez só)…"
  case "$(uname -s)-$(uname -m)" in
    Linux-x86_64)   ALVO=cloudflared-linux-amd64 ;;
    Linux-aarch64)  ALVO=cloudflared-linux-arm64 ;;
    Darwin-arm64|Darwin-x86_64) ALVO=cloudflared-darwin-$( [[ "$(uname -m)" == arm64 ]] && echo arm64 || echo amd64 ).tgz ;;
    *) erro "Sistema não reconhecido. Instale o cloudflared à mão: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/" ;;
  esac
  URL="https://github.com/cloudflare/cloudflared/releases/latest/download/$ALVO"
  if [[ "$ALVO" == *.tgz ]]; then
    curl -fsSL "$URL" | tar -xz -C "$EXEC" cloudflared
  else
    curl -fsSL -o "$CF" "$URL"
  fi
  chmod +x "$CF"
fi
verde "cloudflared: $("$CF" --version | head -1)"

# ------------------------------------------------------------------- 3. acesso
if [[ -f .env ]]; then set -a; . ./.env; set +a; fi
CONTAS=$(python3 - <<'PY'
import sys; sys.path.insert(0, "scripts")
from lape.db import Database
from lape import config
db = Database(config.DB_PATH); db.migrate()
print(db.scalar("SELECT COUNT(*) FROM members WHERE login IS NOT NULL") or 0)
db.close()
PY
)
if [[ "$CONTAS" == "0" ]]; then
  azul "Nenhum acesso cadastrado. Vamos criar o seu."
  read -rp "  Seu nome: " NOME
  read -rp "  Seu e-mail (será o login): " LOGIN
  SENHA="$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')"
  python3 scripts/lape_agent.py usuarios --criar "$NOME" "$LOGIN" --senha "$SENHA" --perfil admin
  echo
  verde "  ANOTE AGORA — esta senha não é mostrada de novo:"
  echo   "    login: $LOGIN"
  echo   "    senha: $SENHA"
  echo
  read -rp "  Anotou? Enter para continuar. " _
fi

# -------------------------------------------------------------------- 4. serviço
parar
azul "Subindo o serviço…"
# Escuta só em 127.0.0.1: quem chega de fora vem pelo túnel, e mais ninguém.
LAPE_BEHIND_HTTPS=1 LAPE_TRUST_PROXY=1 \
  nohup python3 scripts/lape_agent.py api --host 127.0.0.1 --port "$PORTA" \
  > "$EXEC/api.log" 2>&1 &
echo $! > "$EXEC/api.pid"

# Perguntar só "a porta responde?" não serve. Se um serviço antigo ainda
# estiver segurando a porta, o novo morre ao tentar abri-la — e a conferência
# passa, porque quem respondeu foi o velho. O túnel sobe apontando para o
# serviço errado, e quem atualizou o sistema recarrega a página e vê tudo
# igual, sem nenhuma mensagem de erro em lugar nenhum.
API_PID="$(cat "$EXEC/api.pid")"
for _ in $(seq 1 40); do
  kill -0 "$API_PID" 2>/dev/null || break
  curl -fsS -m 2 "http://127.0.0.1:$PORTA/api/health" >/dev/null 2>&1 && break
  sleep 0.5
done
if ! kill -0 "$API_PID" 2>/dev/null; then
  tail -20 "$EXEC/api.log"
  echo
  DONO="$( (command -v lsof >/dev/null && lsof -ti :"$PORTA" | head -1) || true)"
  if [[ -n "${DONO:-}" ]]; then
    aviso "A porta $PORTA já está ocupada pelo processo $DONO:"
    ps -p "$DONO" -o args= 2>/dev/null | sed 's/^/    /'
    echo
    aviso "Provavelmente é um LAPE antigo. Encerre-o com:  kill $DONO"
    aviso "ou suba este numa porta livre:  bash deploy/publicar.sh --porta 8010"
  fi
  erro "O serviço morreu ao subir."
fi
curl -fsS -m 3 "http://127.0.0.1:$PORTA/api/health" >/dev/null \
  || { tail -20 "$EXEC/api.log"; erro "O serviço subiu mas não respondeu. Log acima."; }
verde "Serviço no ar em 127.0.0.1:$PORTA"

# --------------------------------------------------------------------- 5. túnel
# Três modos, um só resultado: $ENDERECO. Deste lado nada muda — o serviço
# continua escutando só em 127.0.0.1.
ENDERECO=""

if [[ "$FIXO" == 1 ]]; then
  NG="$EXEC/ngrok"
  command -v ngrok >/dev/null 2>&1 && NG="$(command -v ngrok)"
  if [[ ! -x "$NG" ]]; then
    azul "Baixando o ngrok (uma vez só)…"
    case "$(uname -s)-$(uname -m)" in
      Linux-x86_64)   ARQ=ngrok-v3-stable-linux-amd64.tgz ;;
      Linux-aarch64)  ARQ=ngrok-v3-stable-linux-arm64.tgz ;;
      Darwin-x86_64)  ARQ=ngrok-v3-stable-darwin-amd64.tgz ;;
      Darwin-arm64)   ARQ=ngrok-v3-stable-darwin-arm64.tgz ;;
      *) erro "sistema não reconhecido para baixar o ngrok: $(uname -s)-$(uname -m)" ;;
    esac
    curl -fsSL "https://bin.equinox.io/c/bNyj1mQVY4c/$ARQ" -o "$EXEC/ngrok.tgz"
    tar -xzf "$EXEC/ngrok.tgz" -C "$EXEC"
    rm -f "$EXEC/ngrok.tgz"
    chmod +x "$NG"
  fi
  verde "ngrok pronto"

  [[ -z "$DOMINIO" && -f "$ARQ_NGROK" ]] && DOMINIO="$(cat "$ARQ_NGROK")"
  if [[ -z "$DOMINIO" ]]; then
    cat <<'TXT'

  Endereço fixo gratuito — três passos, uma vez só:

    1. Crie a conta gratuita em  https://dashboard.ngrok.com/signup
    2. Copie o authtoken de      https://dashboard.ngrok.com/get-started/your-authtoken
    3. Reserve o domínio em      https://dashboard.ngrok.com/domains
       (a conta gratuita dá direito a um, do tipo lape-udesc.ngrok-free.app)

TXT
    read -r -p "  Cole o authtoken: " TOKEN
    # As duas páginas ficam a um clique uma da outra. Quem cola o id do
    # domínio no lugar do authtoken só descobre o engano num log de vinte
    # linhas, e a mensagem de lá não diz qual dos dois errou.
    if [[ "$TOKEN" =~ ^(rd|ak|cr|tn|ep|as|ed)_ ]]; then
      echo
      aviso "Isso é um identificador de recurso do ngrok — pelo prefixo, o do"
      aviso "próprio domínio reservado. O authtoken é outra coisa, bem mais longa:"
      echo "    https://dashboard.ngrok.com/get-started/your-authtoken"
      echo
      erro "Authtoken inválido. Rode de novo com o token certo."
    fi
    [[ -n "$TOKEN" ]] && "$NG" config add-authtoken "$TOKEN" >/dev/null
    read -r -p "  Cole o domínio reservado: " DOMINIO
  fi
  DOMINIO="${DOMINIO#https://}"; DOMINIO="${DOMINIO#http://}"; DOMINIO="${DOMINIO%/}"
  [[ -n "$DOMINIO" ]] || erro "Sem domínio reservado não dá para fixar o endereço."
  printf '%s' "$DOMINIO" > "$ARQ_NGROK"

  azul "Abrindo o túnel fixo…"
  nohup "$NG" http --url="https://$DOMINIO" --log=stdout "127.0.0.1:$PORTA" \
    > "$EXEC/tunel.log" 2>&1 &
  echo $! > "$EXEC/tunel.pid"

  # o próprio ngrok publica em 127.0.0.1:4040 o que conseguiu abrir — mais
  # confiável do que acreditar no domínio que a pessoa digitou
  for _ in $(seq 1 30); do
    ENDERECO="$(curl -fsS http://127.0.0.1:4040/api/tunnels 2>/dev/null \
      | grep -oE 'https://[a-zA-Z0-9.-]+' | head -1 || true)"
    [[ -n "$ENDERECO" ]] && break
    sleep 1
  done
  [[ -n "$ENDERECO" ]] || { tail -20 "$EXEC/tunel.log"; \
    erro "O túnel fixo não abriu. Log acima. Confira o authtoken e o domínio."; }

elif [[ "$PERMANENTE" == 1 ]]; then
  [[ -z "$DOMINIO" && -f "$ARQ_CF" ]] && DOMINIO="$(cat "$ARQ_CF")"
  if [[ -z "$DOMINIO" ]]; then
    cat <<'TXT'

  Endereço fixo no domínio do laboratório, pela Cloudflare. Sem página de
  aviso e sem limite de sessão, mas exige um domínio já hospedado lá:

    · lape.udesc.br, se a universidade delegar o subdomínio, ou
    · um domínio próprio — um .com.br no registro.br sai por poucos reais ao
      ano, e a Cloudflare não cobra nada pelo túnel.

  Com o domínio em mãos:

    bash deploy/publicar.sh --permanente --dominio lape.seu-dominio.br

  O script cuida do resto. Da segunda vez em diante, só --permanente.

  Sem domínio nenhum, o equivalente gratuito é  bash deploy/publicar.sh --fixo

TXT
    parar
    exit 0
  fi
  DOMINIO="${DOMINIO#https://}"; DOMINIO="${DOMINIO#http://}"; DOMINIO="${DOMINIO%/}"

  if [[ ! -f "$HOME/.cloudflared/cert.pem" ]]; then
    azul "Autorize o cloudflared no navegador que vai abrir (uma vez só)…"
    "$CF" tunnel login
    [[ -f "$HOME/.cloudflared/cert.pem" ]] || erro "A autorização não foi concluída."
  fi
  if ! "$CF" tunnel list 2>/dev/null | grep -q "\b$TUNEL\b"; then
    azul "Criando o túnel '$TUNEL'…"
    "$CF" tunnel create "$TUNEL"
  fi
  azul "Apontando $DOMINIO para o túnel…"
  "$CF" tunnel route dns --overwrite-dns "$TUNEL" "$DOMINIO" >/dev/null
  printf '%s' "$DOMINIO" > "$ARQ_CF"

  azul "Abrindo o túnel permanente…"
  nohup "$CF" tunnel --no-autoupdate run --url "http://127.0.0.1:$PORTA" "$TUNEL" \
    > "$EXEC/tunel.log" 2>&1 &
  echo $! > "$EXEC/tunel.pid"
  ENDERECO="https://$DOMINIO"

  # DNS leva um pouco na primeira vez: isso é aviso, não motivo para abortar
  RESPONDEU=0
  for _ in $(seq 1 20); do
    if curl -fsS "$ENDERECO/api/health" >/dev/null 2>&1; then RESPONDEU=1; break; fi
    sleep 3
  done
  [[ "$RESPONDEU" == 1 ]] || aviso "O túnel subiu, mas $DOMINIO ainda não respondeu — o DNS costuma levar alguns minutos na primeira vez."

else
  # O túnel sorteado é cortesia da Cloudflare, sem garantia de disponibilidade
  # — o próprio aviso no log diz isso. Às vezes ele pede o endereço e a
  # resposta não vem. Uma segunda tentativa custa pouco; desistir na primeira
  # é que não.
  for tentativa in 1 2; do
    if [[ "$tentativa" == 1 ]]; then
      azul "Abrindo o túnel…"
    else
      aviso "A Cloudflare não devolveu endereço. Tentando mais uma vez…"
      parar_tunel
      rm -f "$EXEC/tunel.log"
    fi
    nohup "$CF" tunnel --no-autoupdate --url "http://127.0.0.1:$PORTA" \
      > "$EXEC/tunel.log" 2>&1 &
    echo $! > "$EXEC/tunel.pid"
    TUNEL_PID=$!

    for _ in $(seq 1 90); do
      ENDERECO="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$EXEC/tunel.log" | head -1 || true)"
      [[ -n "$ENDERECO" ]] && break
      # túnel morto não vai imprimir endereço nenhum
      kill -0 "$TUNEL_PID" 2>/dev/null || break
      sleep 1
    done
    [[ -n "$ENDERECO" ]] && break
  done
  if [[ -z "$ENDERECO" ]]; then
    tail -20 "$EXEC/tunel.log"
    echo
    aviso "O túnel sorteado é de cortesia e cai às vezes. Rode o comando de novo."
    aviso "Para não depender dele: bash deploy/publicar.sh --fixo"
    erro "A Cloudflare não devolveu endereço em duas tentativas."
  fi
fi

printf '%s' "$ENDERECO" > "$ARQ_END"

# ------------------------------------------------------------------ 6. conferir
echo
LAPE_BEHIND_HTTPS=1 LAPE_TRUST_PROXY=1 python3 scripts/lape_agent.py publicar || true

echo
verde "═══════════════════════════════════════════════════════════════"
verde "  No ar. Envie este endereço às pessoas:"
echo
echo   "    $ENDERECO/entrar"
echo
echo   "  Painel .............. $ENDERECO/"
echo   "  Cadastro ............ $ENDERECO/app"
verde "═══════════════════════════════════════════════════════════════"
echo
if [[ "$FIXO" == 1 || "$PERMANENTE" == 1 ]]; then
  verde "Este endereço é fixo: fechou a janela, ele volta o MESMO na próxima vez."
  aviso "Só funciona com o serviço rodando — ele roda aqui."
  [[ "$FIXO" == 1 ]] && aviso "No plano gratuito do ngrok, quem abre pela primeira vez vê uma página de aviso antes do site. Basta clicar em Visit Site."
else
  aviso "Enquanto esta janela estiver aberta, o endereço funciona."
  aviso "Fechou ou desligou o computador, o endereço cai — e volta OUTRO na"
  aviso "próxima vez. Para um endereço fixo: --fixo (grátis) ou --permanente."
fi
echo
echo "Para encerrar: Ctrl+C — ou, de outra janela, bash deploy/publicar.sh --parar"
echo "Para rever este endereço depois: bash deploy/publicar.sh --endereco"
echo
while kill -0 "$(cat "$EXEC/api.pid")" 2>/dev/null; do sleep 5; done
