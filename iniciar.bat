@echo off
REM ============================================================
REM  De Lucca Esporte - iniciar o sistema no Windows (1 clique)
REM  Duplo-clique neste arquivo. Ele instala o necessario,
REM  prepara o banco e abre o sistema no navegador.
REM ============================================================
cd /d "%~dp0"
title De Lucca Esporte - Sistema Biomecanico
echo.
echo  == De Lucca Esporte - iniciando o sistema ==
echo.

REM Modo DONO (uso local na sua maquina): libera todos os recursos sem licenca.
REM Para vender/hospedar, remova esta linha e use uma licenca (LICENSING.md).
set MDLUCCA_DEV=1

REM 1) Python instalado?
where python >nul 2>nul
if errorlevel 1 (
  echo  [ERRO] Python nao encontrado.
  echo  Instale em https://www.python.org/downloads
  echo  e MARQUE a caixa "Add Python to PATH" durante a instalacao.
  echo.
  pause
  exit /b 1
)

REM 2) Dependencias (so instala se faltar)
python -c "import fastapi, uvicorn, numpy, scipy" >nul 2>nul
if errorlevel 1 (
  echo  Instalando dependencias (so na primeira vez)...
  python -m pip install --quiet -r requirements.txt
)

REM 3) Banco de dados (so cria se nao existir)
if not exist "data\db.sqlite" (
  echo  Preparando o banco de dados...
  python scripts\ingest.py --db data\db.sqlite
)

REM 4) Abre o navegador ~5s depois (tempo do servidor subir)
start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:8000/app/gerir.html"

echo.
echo  Sistema no ar em: http://127.0.0.1:8000/app/gerir.html
echo  (o navegador abre sozinho em instantes)
echo.
echo  Para PARAR o sistema: feche esta janela ou aperte Ctrl+C.
echo.

REM 5) Sobe o servidor (fica rodando nesta janela)
python -m uvicorn app.api:app --host 127.0.0.1 --port 8000
