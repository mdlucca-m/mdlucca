#!/usr/bin/env bash
#
# Instalador do LAPE em uma máquina Linux (Ubuntu/Debian) — custo zero.
#
#   sudo bash deploy/instalar.sh
#
# Serve tanto para uma VM sempre gratuita na nuvem quanto para um computador
# do próprio laboratório. O script:
#   1. instala o Docker, se ainda não houver;
#   2. cria o arquivo .env perguntando o essencial;
#   3. libera as portas 80 e 443 (só no modo com IP público);
#   4. sobe a aplicação com HTTPS automático ou por túnel do Cloudflare;
#   5. mostra o endereço final e o acesso do administrador.
#
# É seguro rodar de novo: nada é apagado, o .env existente é preservado.

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

azul()  { printf '\033[1;34m%s\033[0m\n' "$*"; }
verde() { printf '\033[1;32m%s\033[0m\n' "$*"; }
aviso() { printf '\033[1;33m%s\033[0m\n' "$*"; }
erro()  { printf '\033[1;31m%s\033[0m\n' "$*" >&2; }

if [[ "${EUID}" -ne 0 ]]; then
  erro "Rode com sudo: sudo bash deploy/instalar.sh"
  exit 1
fi

# ---------------------------------------------------------------- Docker
instalar_docker() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    verde "Docker já instalado."
    return
  fi
  azul "Instalando o Docker…"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
  fi
  local codinome
  codinome="$(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")"
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $codinome stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
  verde "Docker instalado."
}

# ---------------------------------------------------------------- .env
criar_env() {
  if [[ -f .env ]]; then
    verde "Arquivo .env já existe — mantido como está."
    return
  fi
  azul "Vamos criar o arquivo .env."
  echo
  echo "Como esta máquina será acessada?"
  echo "  1) Tem IP público e um domínio apontado para ela (HTTPS automático)"
  echo "  2) Não tem IP público — usar túnel gratuito do Cloudflare"
  read -rp "Escolha [1/2]: " modo

  local dominio="" token=""
  if [[ "$modo" == "2" ]]; then
    echo
    echo "Crie o túnel em one.dash.cloudflare.com → Networks → Tunnels,"
    echo "aponte-o para  http://lape:8000  e copie o token."
    read -rp "Token do túnel: " token
    dominio="lape.local"
  else
    echo
    echo "Informe o domínio já apontado para o IP desta máquina."
    echo "Sem domínio próprio, registre um gratuito em duckdns.org."
    read -rp "Domínio (ex.: lape.duckdns.org): " dominio
  fi

  echo
  read -rp "Nome do administrador [Administracao LAPE]: " admin_nome
  read -rp "Login do administrador (e-mail): " admin_login
  read -rsp "Senha do administrador (mínimo 8 caracteres): " admin_senha; echo
  read -rp "E-mail de contato para Crossref/OpenAlex (opcional): " contato

  if [[ ${#admin_senha} -lt 8 ]]; then
    erro "A senha precisa de pelo menos 8 caracteres."
    exit 1
  fi

  umask 077
  cat > .env <<ENV
LAPE_DOMINIO=${dominio}
CLOUDFLARE_TUNNEL_TOKEN=${token}
LAPE_ADMIN_NAME=${admin_nome:-Administracao LAPE}
LAPE_ADMIN_LOGIN=${admin_login}
LAPE_ADMIN_PASSWORD=${admin_senha}
LAPE_PUBLIC_DASHBOARD=0
LAPE_CONTACT_EMAIL=${contato}
SCOPUS_API_KEY=
SCOPUS_INST_TOKEN=
WOS_API_KEY=
ENV
  chmod 600 .env
  verde "Arquivo .env criado (só o dono consegue ler)."
}

# ---------------------------------------------------------------- firewall
liberar_portas() {
  azul "Liberando as portas 80 e 443…"
  if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    ufw allow 80/tcp  >/dev/null || true
    ufw allow 443/tcp >/dev/null || true
    verde "Portas liberadas no ufw."
  fi
  # Imagens Ubuntu da Oracle Cloud vêm com iptables fechado por padrão.
  if command -v iptables >/dev/null 2>&1 && iptables -L INPUT -n | grep -q REJECT; then
    iptables -I INPUT 1 -p tcp --dport 80  -j ACCEPT || true
    iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT || true
    if command -v netfilter-persistent >/dev/null 2>&1; then
      netfilter-persistent save >/dev/null 2>&1 || true
    fi
    verde "Portas liberadas no iptables."
  fi
  aviso "Se estiver numa nuvem, libere 80 e 443 também no painel do provedor"
  aviso "(Oracle Cloud: VCN → Security Lists → Ingress Rules)."
}

# ---------------------------------------------------------------- subir
subir() {
  # O contêiner roda como usuário sem privilégios: as planilhas precisam ser
  # legíveis por ele.
  if [[ -d data/raw ]]; then
    chmod -R a+rX data/raw || true
  fi

  local token
  token="$(grep -E '^CLOUDFLARE_TUNNEL_TOKEN=' .env | cut -d= -f2-)"
  azul "Construindo a imagem e subindo os serviços…"
  if [[ -n "$token" ]]; then
    docker compose -f docker-compose.prod.yml --profile tunel up -d --build lape cloudflared
    verde "Serviços no ar através do túnel do Cloudflare."
    echo "O endereço é o hostname que você configurou no painel do túnel."
  else
    liberar_portas
    docker compose -f docker-compose.prod.yml up -d --build lape caddy
    local dominio
    dominio="$(grep -E '^LAPE_DOMINIO=' .env | cut -d= -f2-)"
    verde "Serviços no ar."
    echo
    echo "  Painel ............. https://${dominio}/"
    echo "  Entrar ............. https://${dominio}/entrar"
    echo "  Área do integrante   https://${dominio}/app"
    echo
    aviso "O certificado HTTPS leva de 10 a 60 segundos para ser emitido."
  fi
}

# ---------------------------------------------------------------- resumo
resumo() {
  echo
  azul "Próximos passos"
  echo "  1. Entre com o login de administrador que você definiu."
  echo "  2. Libere acesso aos demais integrantes em: Área do integrante → Administração."
  echo "  3. Coloque as planilhas em data/raw/ e rode o curador:"
  echo "       docker compose -f docker-compose.prod.yml exec lape \\"
  echo "         python3 scripts/lape_agent.py curador"
  echo "  4. Backup diário do banco (crontab -e):"
  echo "       0 3 * * * cd ${RAIZ} && docker compose -f docker-compose.prod.yml \\"
  echo "                 exec -T lape bash deploy/backup.sh"
  echo
  echo "  Ver o log:    docker compose -f docker-compose.prod.yml logs -f lape"
  echo "  Atualizar:    git pull && docker compose -f docker-compose.prod.yml up -d --build"
}

azul "== Instalação do LAPE =="
instalar_docker
criar_env
subir
resumo
