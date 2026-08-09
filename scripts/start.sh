#!/usr/bin/env sh
# Entrypoint de producao: garante o banco no disco PERSISTENTE antes de subir.
# Se o banco ja existe (disco persistente), preserva os dados (alunos, sessoes,
# links). So cria do zero na primeira vez, a partir de data/dashboard_extracted.json.
set -e

DB="${MDLUCCA_DB:-/data/db.sqlite}"
mkdir -p "$(dirname "$DB")"

if [ ! -f "$DB" ]; then
  echo "[start] banco inexistente em $DB — criando de data/dashboard_extracted.json"
  python3 scripts/ingest.py --db "$DB"
else
  echo "[start] banco existente em $DB — preservando dados"
fi

exec uvicorn app.api:app --host 0.0.0.0 --port "${PORT:-8000}"
