@echo off
rem ===================================================================
rem  Abre o LAPE neste computador DIRETO NO MURAL, sem pedir login.
rem
rem  Para o computador ligado numa TV, sem ninguem sentado na frente
rem  para digitar usuario e senha. As outras entradas do sistema (login,
rem  cadastro, editar artigo) continuam exigindo senha do mesmo jeito --
rem  isto libera so a TELA DE LEITURA, que e o mural em si.
rem
rem  Depois que a janela do navegador abrir:
rem    1. aperte o botao de tela cheia no canto do mural (ou F11);
rem    2. deixe a janela do navegador em primeiro plano;
rem    3. NAO feche a janela preta deste .bat -- e ela que mantem o
rem       sistema de pe. Minimize, nao feche.
rem
rem  Se a maquina reiniciar sozinha (falta de luz, Windows Update), quem
rem  quiser que o mural volte a subir sozinho usa o "Subir sozinho ao
rem  ligar.bat" -- este aqui e so para o duplo clique manual.
rem ===================================================================
setlocal
title LAPE - Mural (leitura publica, sem login)

cd /d "%~dp0"

echo.
echo   LAPE - Mural para TV
echo   pasta: %CD%
echo.

if not exist "scripts\lape_agent.py" (
  echo   ! Este arquivo nao esta na pasta do sistema.
  echo     Ele precisa ficar junto da pasta "scripts". Se voce o copiou
  echo     para a area de trabalho, apague a copia e crie um ATALHO no
  echo     lugar: botao direito no arquivo original, "Enviar para" ^>
  echo     "Area de trabalho (criar atalho)".
  echo.
  pause
  exit /b 1
)

where git >nul 2>nul
if errorlevel 1 (
  echo   . git nao encontrado -- seguindo sem buscar atualizacao.
) else (
  python scripts\lape_agent.py proteger >nul 2>nul
  echo   buscando atualizacao...
  git pull --ff-only
  if errorlevel 1 (
    echo.
    echo   . nao deu para atualizar agora. Seguindo com a versao desta
    echo     pasta -- nada foi perdido, e da para tentar de novo depois.
    echo.
  )
)
echo.

rem So esta janela enxerga esta variavel -- nao muda o resto do sistema,
rem nem fica gravada em lugar nenhum. A area de cadastro (usuario e
rem senha) continua exigindo login mesmo com isto ligado.
set LAPE_PUBLIC_DASHBOARD=1

rem Direto no mural, ja em modo TV -- nao na tela de entrar.
start "" http://127.0.0.1:8000/tv

echo   subindo o mural...
echo   Esta janela precisa FICAR ABERTA (pode minimizar): e ela que
echo   mantem o LAPE de pe. Para desligar, feche esta janela.
echo.

python scripts\lape_agent.py api --port 8000

echo.
echo   ------------------------------------------------------------------
echo   O mural parou. Se houve erro, ele esta nas linhas acima.
echo   ------------------------------------------------------------------
pause
