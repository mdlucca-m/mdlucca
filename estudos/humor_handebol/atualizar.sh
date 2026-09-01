#!/usr/bin/env bash
# Reconstrói tudo, do zero, em um comando: base canônica, análises, banco, busca e exportações.
set -euo pipefail
cd "$(dirname "$0")"
export HH_RAIZ="$PWD"
echo "▶ 1/7  base canônica a partir da fonte-verdade"
python3 analise/base_v2.py
echo "▶ 2/7  classificação nos perfis e matriz de reconciliação"
python3 analise/V2_perfis.py
echo "▶ 3/7  análises (descritiva, séries, não paramétrica, paramétrica, modelo misto)"
python3 analise/V2_a1.py && python3 analise/V2_a2.py && python3 analise/V2_a3.py && python3 analise/V2_audit.py
echo "▶ 4/7  banco único"
python3 scripts/construir_base.py
echo "▶ 5/7  acervo das planilhas, referências e índice de busca"
python3 scripts/colher_planilhas.py
python3 scripts/casar_dois.py || echo "  (busca de DOI indisponível; mantido o que já havia)"
python3 scripts/indexar_busca.py
echo "▶ 6/7  modelos de árvore, diagnóstico e mapa CRISP-DM"
python3 analise/V2_ml.py && python3 analise/V2_ml2.py && python3 analise/V2_ml3.py && python3 analise/V2_crispdm.py
echo "▶ 7/7  exportações, painel e figuras"
python3 scripts/exportar.py
python3 scripts/exportar_painel.py
python3 scripts/montar_painel.py
for f in figuras/UV*.py figuras/UM*.py; do [ -e "$f" ] && python3 "$f"; done
echo "✔ pronto — consulte com ./scripts/consultar.py resumo"
