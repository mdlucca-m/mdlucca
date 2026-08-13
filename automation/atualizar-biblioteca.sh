#!/usr/bin/env bash
# Atualiza a Biblioteca Virtual usando o agente pessoal (biblioteca-delucca), via
# Claude Code em modo headless — BUSCA POR MODALIDADE. Pensado para ser chamado por
# um nó "Execute Command" do n8n (ver automation/biblioteca.n8n.json).
#
# Uso:   ./automation/atualizar-biblioteca.sh "flow; burnout; clima motivacional"
# Env:   REPO_DIR     (default: diretório do repo)
#        BRANCH       (default: branch atual)
#        MODALIDADES  (default: as 7 modalidades estéticas; separadas por ';')
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(git rev-parse --show-toplevel)}"
cd "$REPO_DIR"
GAPS="${1:-capacidades físicas e variáveis fisiológicas; capacidade neuromuscular; potência muscular; pliometria; força reativa (RFD); variáveis psicológicas (flow, burnout, clima motivacional, autofala, resiliência, coping); biomecânica / derivadas}"
MODALIDADES="${MODALIDADES:-Ginástica rítmica; Ginástica artística; Ginástica aeróbica; Ginástica acrobática; Patinação artística; Nado artístico; Dança}"
BRANCH="${BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"

echo "[biblioteca] lacunas: $GAPS"
echo "[biblioteca] modalidades: $MODALIDADES"

count_json(){ python3 -c "import json;print(len(json.load(open('biblioteca/biblioteca.json'))))" 2>/dev/null || echo 0; }
ANTES="$(count_json)"

# 1) Um passo por MODALIDADE — o agente busca, verifica DOI e grava os novos em
#    biblioteca/_new-auto-<slug>.json (schema completo), sem duplicar DOIs já no acervo.
IFS=';' read -ra MODS <<< "$MODALIDADES"
i=0
for MOD in "${MODS[@]}"; do
  MOD="$(echo "$MOD" | sed 's/^ *//;s/ *$//')"; [ -z "$MOD" ] && continue
  i=$((i+1))
  echo "[biblioteca] ($i) modalidade: $MOD"
  claude -p --permission-mode acceptEdits \
    "Use o subagente biblioteca-delucca. Busque NOVOS artigos peer-reviewed com DOI verificável,
     publicados APENAS em inglês, português ou espanhol,
     SOMENTE da modalidade estética feminina '${MOD}', sobre: ${GAPS}.
     NÃO duplique DOIs já presentes em biblioteca/biblioteca.json (leia o campo doi).
     Grave APENAS os novos como um array JSON em biblioteca/_new-auto-${i}.json, no schema COMPLETO:
     authors, year, title, journal, doi, citations, sport, topic, finding, design, design_conf, subvar, n,
     biomech(bool), methods[], stats_approach, effect_size(bool), es_note, roc(bool), derivatives(bool),
     variables[] (subconjunto de Neuro/Psico/Performance/Fadiga), modalities[], n_modalities(int).
     Verifique cada DOI no PubMed. Ao final imprima 'MOD=${MOD} NOVOS=<n>'." \
    || { echo "[biblioteca] claude CLI indisponível — pulei a modalidade '$MOD'"; }
done

# 2) Mescla os _new-auto-*.json (sem duplicar DOI) e regenera o HTML
python3 biblioteca/merge_new.py || echo "[biblioteca] merge_new.py: nada a mesclar"
python3 biblioteca/build.py || echo "[biblioteca] build.py falhou — HTML não regenerado"

# 3) Versiona se houve mudança
DEPOIS="$(count_json)"; NOVOS=$(( DEPOIS - ANTES )); [ "$NOVOS" -lt 0 ] && NOVOS=0
if ! git diff --quiet -- biblioteca/ || [ -n "$(git status --porcelain biblioteca/)" ]; then
  git add biblioteca/biblioteca.json biblioteca/biblioteca-enriched.json biblioteca/biblioteca.html
  git commit -q -m "chore(biblioteca): atualização automática por modalidade ($(date -u +%F)) — +${NOVOS} → ${DEPOIS}"
  for i in 1 2 3 4; do git push origin "$BRANCH" && break || sleep $((2**i)); done
  echo "[biblioteca] commitado e enviado (total ${DEPOIS}). NOVOS=${NOVOS}"
else
  echo "[biblioteca] nada novo — biblioteca já está atualizada. NOVOS=0"
fi
