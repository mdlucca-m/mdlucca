#!/usr/bin/env bash
# Registra a Ana como servidor MCP no cliente escolhido.
#
#   ./instalar.sh              → escreve .mcp.json na raiz do repositório (Claude Code)
#   ./instalar.sh --desktop    → mostra o trecho para o claude_desktop_config.json
set -euo pipefail
cd "$(dirname "$0")"
ANA="$PWD/ana_mcp.py"
RAIZ="$(cd .. && pwd)"

TRECHO=$(cat <<JSON
{
  "mcpServers": {
    "ana": {
      "command": "python3",
      "args": ["$ANA"],
      "env": {"HH_RAIZ": "$RAIZ/estudos/humor_handebol"}
    },
    "lape-corpus": {
      "command": "python3",
      "args": ["$RAIZ/scripts/lape_agent.py", "rag", "mcp"]
    }
  }
}
JSON
)

if [ "${1:-}" = "--desktop" ]; then
  echo "Cole em ~/Library/Application Support/Claude/claude_desktop_config.json"
  echo "(macOS) ou %APPDATA%\\Claude\\claude_desktop_config.json (Windows):"
  echo
  echo "$TRECHO"
  exit 0
fi

python3 - "$RAIZ/.mcp.json" <<PY
import json, sys, pathlib
alvo = pathlib.Path(sys.argv[1])
novo = json.loads('''$TRECHO''')
atual = json.loads(alvo.read_text()) if alvo.exists() else {}
atual.setdefault("mcpServers", {}).update(novo["mcpServers"])
alvo.write_text(json.dumps(atual, ensure_ascii=False, indent=2) + "\n")
print(f"registrado em {alvo}: {', '.join(novo['mcpServers'])}")
PY

python3 memoria.py semear >/dev/null
echo "memória semeada. Teste com:  ./ana.py orientar"
