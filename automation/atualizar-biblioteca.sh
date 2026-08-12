#!/usr/bin/env bash
# Atualiza a Biblioteca Virtual usando o agente pessoal (biblioteca-delucca), via
# Claude Code em modo headless. Pensado para ser chamado por um nó "Execute Command"
# do n8n (ver automation/biblioteca.n8n.json).
#
# Uso:   ./automation/atualizar-biblioteca.sh "nado artístico EMG; cheerleading; unidades motoras"
# Env:   REPO_DIR (default: diretório do repo)  ·  BRANCH (default: branch atual)
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(git rev-parse --show-toplevel)}"
cd "$REPO_DIR"
GAPS="${1:-nado artístico; cheerleading; unidades motoras / taxa de disparo; flow; burnout}"
BRANCH="${BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"

echo "[biblioteca] buscando lacunas: $GAPS"

# 1) Agente headless: busca internacional + verificação de DOI + catálogo sem duplicar
claude -p --permission-mode acceptEdits \
  "Use o subagente biblioteca-delucca. Busque NOVOS artigos internacionais (peer-reviewed,
   DOI verificável) SOMENTE de esportes estéticos FEMININOS sobre: ${GAPS}.
   Para cada artigo novo, faça APPEND em biblioteca/biblioteca.json no MESMO schema
   (authors, year, title, journal, doi, citations, sport, topic, finding), SEM duplicar DOIs já existentes.
   Depois, reinjete os dados em biblioteca/biblioteca.html (marcador /*DATA*/ ... /*SYNTH*/) mantendo o layout.
   Ao final, imprima em UMA linha: 'NOVOS=<n>' com a quantidade de artigos adicionados." \
  || { echo "[biblioteca] claude CLI indisponível — pulei a etapa do agente"; }

# 2) Versiona se houve mudança
if ! git diff --quiet -- biblioteca/; then
  git add biblioteca/biblioteca.json biblioteca/biblioteca.html
  git commit -q -m "chore(biblioteca): atualização automática ($(date -u +%F))"
  for i in 1 2 3 4; do git push origin "$BRANCH" && break || sleep $((2**i)); done
  echo "[biblioteca] alterações commitadas e enviadas."
else
  echo "[biblioteca] nada novo — biblioteca já está atualizada."
fi
