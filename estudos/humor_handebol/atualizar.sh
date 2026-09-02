#!/usr/bin/env bash
# Reconstrói tudo, do zero, em um comando: base canônica, análises, banco, busca e exportações.
set -euo pipefail
cd "$(dirname "$0")"
export HH_RAIZ="$PWD"
echo "▶ 1/8  base canônica a partir da fonte-verdade"
python3 analise/base_v2.py
echo "▶ 2/8  classificação nos perfis e matriz de reconciliação"
python3 analise/V2_perfis.py
echo "▶ 3/8  análises (descritiva, séries, não paramétrica, paramétrica, modelo misto)"
python3 analise/V2_a1.py && python3 analise/V2_a2.py && python3 analise/V2_a3.py && python3 analise/V2_audit.py
python3 analise/V2_assoc.py
echo "▶ 4/8  banco único"
python3 scripts/construir_base.py
echo "▶ 5/8  acervo das planilhas, referências e índice de busca"
python3 scripts/colher_planilhas.py
python3 scripts/casar_dois.py || echo "  (busca de DOI indisponível; mantido o que já havia)"
python3 scripts/indexar_busca.py
echo "▶ 6/8  auditoria de qualidade, reconferência e otimização da carga"
python3 analise/V2_qual.py && python3 analise/V2_conf.py && python3 analise/V2_otim.py
python3 analise/V2_psico.py && python3 analise/V2_falta.py && python3 analise/V2_unid.py
python3 analise/V2_te.py && python3 analise/V2_estim.py
python3 analise/V2_proto.py
python3 analise/V2_cruz.py
python3 analise/V2_decomp.py
python3 scripts/gravar_qualidade.py
echo "▶ 7/8  modelos de árvore, diagnóstico e mapa CRISP-DM"
python3 analise/V2_ml.py && python3 analise/V2_ml2.py && python3 analise/V2_ml3.py && python3 analise/V2_crispdm.py
echo "▶ 8/8  exportações, painel e figuras"
python3 scripts/exportar.py
python3 scripts/exportar_painel.py
python3 scripts/montar_painel.py
for f in figuras/UV*.py figuras/UM*.py figuras/UQ*.py figuras/UP*.py; do [ -e "$f" ] && python3 "$f"; done
python3 scripts/montar_artigo1.py && python3 scripts/montar_artigo2.py
python3 scripts/montar_anexo.py && python3 scripts/montar_qualidade.py
python3 scripts/conferir_figuras.py > /dev/null || echo "  ATENÇÃO: referência de figura ou tabela inexistente"
echo "✔ pronto — consulte com ./scripts/consultar.py resumo"
