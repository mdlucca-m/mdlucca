#!/usr/bin/env bash
# ============================================================
#  De Lucca Esporte - iniciar o sistema no Mac/Linux
#  Rode:  bash iniciar.sh   (ou de permissao com: chmod +x iniciar.sh)
# ============================================================
cd "$(dirname "$0")"
echo
echo " == De Lucca Esporte - iniciando o sistema =="
echo

# 1) Python instalado?
PY=python3
command -v $PY >/dev/null 2>&1 || PY=python
if ! command -v $PY >/dev/null 2>&1; then
  echo " [ERRO] Python nao encontrado. Instale em https://www.python.org/downloads"
  exit 1
fi

# 2) Dependencias (so instala se faltar)
if ! $PY -c "import fastapi, uvicorn, numpy, scipy" >/dev/null 2>&1; then
  echo " Instalando dependencias (so na primeira vez)..."
  $PY -m pip install --quiet -r requirements.txt
fi

# 3) Banco de dados (so cria se nao existir)
if [ ! -f "data/db.sqlite" ]; then
  echo " Preparando o banco de dados..."
  $PY scripts/ingest.py --db data/db.sqlite
fi

# 4) Abre o navegador ~4s depois
URL="http://127.0.0.1:8000/app/gerir.html"
( sleep 4; (command -v open >/dev/null && open "$URL") || (command -v xdg-open >/dev/null && xdg-open "$URL") ) >/dev/null 2>&1 &

echo
echo " Sistema no ar em: $URL"
echo " Para PARAR: aperte Ctrl+C nesta janela."
echo

# 5) Sobe o servidor
exec $PY -m uvicorn app.api:app --host 127.0.0.1 --port 8000
