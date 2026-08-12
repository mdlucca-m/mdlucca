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
GAPS="${1:-biomecânica / cinemática / mecânica; RFD e derivadas; estatística bayesiana; curva ROC; tamanho de efeito; unidades motoras / taxa de disparo; flow; burnout}"
BRANCH="${BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"

echo "[biblioteca] buscando lacunas: $GAPS"

# 1) Agente headless: busca internacional + verificação de DOI + catálogo sem duplicar
claude -p --permission-mode acceptEdits \
  "Use o subagente biblioteca-delucca. Busque NOVOS artigos internacionais (peer-reviewed,
   DOI verificável) SOMENTE de esportes estéticos FEMININOS sobre: ${GAPS}.
   Para cada artigo novo, faça APPEND em biblioteca/biblioteca.json E em biblioteca/biblioteca-enriched.json,
   SEM duplicar DOIs já existentes, no schema COMPLETO:
   authors, year, title, journal, doi, citations, sport, topic, finding,
   design, design_conf, subvar, n,
   biomech(bool), methods[], stats_approach, effect_size(bool), es_note, roc(bool), derivatives(bool),
   variables[], modalities[], n_modalities(int).
   Verifique cada DOI no PubMed. Ao final, imprima em UMA linha: 'NOVOS=<n>' com a quantidade adicionada." \
  || { echo "[biblioteca] claude CLI indisponível — pulei a etapa do agente"; }

# 1b) Regenera o HTML a partir dos dados (builder versionado)
python3 biblioteca/build.py || echo "[biblioteca] build.py falhou — HTML não regenerado"

# 2) Versiona se houve mudança
if ! git diff --quiet -- biblioteca/; then
  git add biblioteca/biblioteca.json biblioteca/biblioteca-enriched.json biblioteca/biblioteca.html
  git commit -q -m "chore(biblioteca): atualização automática ($(date -u +%F))"
  for i in 1 2 3 4; do git push origin "$BRANCH" && break || sleep $((2**i)); done
  echo "[biblioteca] alterações commitadas e enviadas."
else
  echo "[biblioteca] nada novo — biblioteca já está atualizada."
fi
