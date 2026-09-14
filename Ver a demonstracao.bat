@echo off
rem ===================================================================
rem  Abre a DEMONSTRACAO do LAPE, em um duplo clique.
rem
rem  Dados inventados, num banco separado (data\demo.sqlite). O banco de
rem  verdade nao e tocado -- da para abrir isto sem medo nenhum.
rem
rem  Serve para ver as telas funcionando ANTES de ter dado real: ninguem
rem  consegue decidir se uma tela serve olhando para "sem dados".
rem
rem  Entrar com:  demo@lape.local   senha: demo12345
rem ===================================================================
setlocal
title LAPE - demonstracao (dados inventados)
cd /d "%~dp0"

echo.
echo   LAPE - DEMONSTRACAO
echo   Dados ficticios. Nomes, titulos e numeros sao inventados.
echo   O banco de verdade nao e tocado.
echo.

if not exist "scripts\lape_agent.py" (
  echo   ! Este arquivo nao esta na pasta do sistema.
  pause
  exit /b 1
)

rem Gera a massa so na primeira vez. Regerar a cada duplo clique
rem apagaria o que a pessoa tivesse experimentado na tela anterior.
if not exist "data\demo.sqlite" (
  echo   gerando a massa de teste, uma vez so...
  echo.
  python scripts\lape_agent.py demo --acesso "Demonstracao" demo@lape.local --senha demo12345
  if errorlevel 1 (
    echo.
    echo   ! Nao deu para gerar a massa. O erro esta acima.
    pause
    exit /b 1
  )
)

echo.
echo   entrar com:  demo@lape.local     senha: demo12345
echo   Esta janela precisa FICAR ABERTA.
echo.
start "" http://127.0.0.1:8001
python scripts\lape_agent.py --db data\demo.sqlite api --port 8001

echo.
echo   A demonstracao parou. Se houve erro, ele esta nas linhas acima.
pause
