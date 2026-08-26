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
#   --permanente   usa um túnel nomeado (endereço fixo; pede conta gratuita)
#   --porta N      porta local do serviço (padrão: 8000)
#   --parar        encerra o que este script deixou rodando
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
PORTA=8000
PERMANENTE=0
EXEC="$RAIZ/.lape-run"

azul()  { printf '\033[1;34m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
aviso() { printf '\033[1;33m! %s\033[0m\n' "$*"; }
erro()  { printf '\033[1;31m! %s\033[0m\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --permanente) PERMANENTE=1; shift ;;
    --porta) PORTA="$2"; shift 2 ;;
    --parar) parar_tudo=1; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) erro "opção desconhecida: $1" ;;
  esac
done

parar() {
  for nome in api tunel; do
    if [[ -f "$EXEC/$nome.pid" ]] && kill -0 "$(cat "$EXEC/$nome.pid")" 2>/dev/null; then
      kill "$(cat "$EXEC/$nome.pid")" 2>/dev/null || true
      verde "Encerrado: $nome"
    fi
    rm -f "$EXEC/$nome.pid"
  done
}
if [[ "${parar_tudo:-0}" == 1 ]]; then parar; exit 0; fi

mkdir -p "$EXEC"
trap 'echo; aviso "Encerrando…"; parar; exit 0' INT TERM

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

for _ in $(seq 1 40); do
  curl -fsS -m 2 "http://127.0.0.1:$PORTA/api/health" >/dev/null 2>&1 && break
  sleep 0.5
done
curl -fsS -m 3 "http://127.0.0.1:$PORTA/api/health" >/dev/null \
  || { tail -20 "$EXEC/api.log"; erro "O serviço não subiu. Log acima."; }
verde "Serviço no ar em 127.0.0.1:$PORTA"

# --------------------------------------------------------------------- 5. túnel
azul "Abrindo o túnel…"
if [[ "$PERMANENTE" == 1 ]]; then
  cat <<'TXT'

  Endereço fixo pede uma conta gratuita da Cloudflare. Três passos:

    1. cloudflared tunnel login          (abre o navegador, você autoriza)
    2. cloudflared tunnel create lape
    3. cloudflared tunnel route dns lape lape.seu-dominio.br

  Depois rode:  cloudflared tunnel run --url http://127.0.0.1:8000 lape

  Sem domínio próprio, dá para usar um gratuito (duckdns.org) apontado para
  a Cloudflare. Se preferir começar sem nada disso, rode este script sem
  --permanente: o endereço sai na hora, só muda a cada reinício.

TXT
  exit 0
fi

nohup "$CF" tunnel --no-autoupdate --url "http://127.0.0.1:$PORTA" \
  > "$EXEC/tunel.log" 2>&1 &
echo $! > "$EXEC/tunel.pid"

ENDERECO=""
for _ in $(seq 1 60); do
  ENDERECO="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$EXEC/tunel.log" | head -1 || true)"
  [[ -n "$ENDERECO" ]] && break
  sleep 1
done
[[ -n "$ENDERECO" ]] || { tail -20 "$EXEC/tunel.log"; erro "O túnel não abriu. Log acima."; }

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
aviso "Enquanto esta janela estiver aberta, o endereço funciona."
aviso "Fechou ou desligou o computador, o endereço cai — e volta OUTRO"
aviso "na próxima vez. Para um endereço fixo: bash deploy/publicar.sh --permanente"
echo
echo "Para encerrar: Ctrl+C — ou, de outra janela, bash deploy/publicar.sh --parar"
echo
while kill -0 "$(cat "$EXEC/api.pid")" 2>/dev/null; do sleep 5; done
