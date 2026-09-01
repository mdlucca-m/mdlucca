#!/usr/bin/env bash
# Reconstrói tudo, do zero, em um comando: base canônica, análises, banco, busca e exportações.
set -euo pipefail
cd "$(dirname "$0")"
export HH_RAIZ="$PWD"
echo "▶ 1/6  base canônica a partir da fonte-verdade"
python3 analise/base_v2.py
echo "▶ 2/6  classificação nos perfis e matriz de reconciliação"
python3 analise/V2_perfis.py
echo "▶ 3/6  análises (descritiva, séries, não paramétrica, paramétrica, modelo misto)"
python3 analise/V2_a1.py && python3 analise/V2_a2.py && python3 analise/V2_a3.py && python3 analise/V2_audit.py
echo "▶ 4/6  banco único"
python3 scripts/construir_base.py
echo "▶ 5/6  acervo das planilhas, referências e índice de busca"
python3 scripts/colher_planilhas.py
python3 scripts/casar_dois.py || echo "  (busca de DOI indisponível; mantido o que já havia)"
python3 scripts/indexar_busca.py
echo "▶ 6/6  exportações e figuras"
python3 scripts/exportar.py
for f in figuras/UV*.py; do [ -e "$f" ] && python3 "$f"; done
echo "✔ pronto — consulte com ./scripts/consultar.py resumo"
