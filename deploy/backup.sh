#!/usr/bin/env bash
# Backup diário do banco. Agende no cron:
#   0 3 * * * /opt/lape/deploy/backup.sh
set -euo pipefail
DB="${LAPE_DB:-/opt/lape/data/db.sqlite}"
DEST="${LAPE_BACKUP_DIR:-/opt/lape/backups}"
KEEP="${LAPE_BACKUP_KEEP:-30}"

mkdir -p "$DEST"
STAMP="$(date +%Y%m%d_%H%M%S)"
# sqlite3.backup respeita transações em andamento; copiar o arquivo não.
python3 - "$DB" "$DEST/db_$STAMP.sqlite" <<'PY'
import sqlite3, sys
origem, destino = sys.argv[1], sys.argv[2]
with sqlite3.connect(origem) as src, sqlite3.connect(destino) as dst:
    src.backup(dst)
PY
gzip -f "$DEST/db_$STAMP.sqlite"
find "$DEST" -name 'db_*.sqlite.gz' -mtime "+$KEEP" -delete
echo "backup: $DEST/db_$STAMP.sqlite.gz"
