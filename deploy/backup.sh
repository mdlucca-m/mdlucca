#!/usr/bin/env bash
# Cópia de segurança do banco, para agendar no cron:
#   0 3 * * * /opt/lape/deploy/backup.sh
#
# Numa instalação que roda a API, isto quase nunca é necessário: o próprio
# serviço copia sozinho, acompanhando o cadastro. Este script existe para o
# caso de a API não estar no ar — e para quem prefere o cron.
#
# A implementação é uma só, em scripts/lape/backup.py. Duas implementações de
# backup divergem, e a hora de descobrir a divergência é sempre a pior.
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

python3 scripts/lape_agent.py ${LAPE_DB:+--db "$LAPE_DB"} backup --forcar
