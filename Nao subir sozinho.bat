@echo off
rem ===================================================================
rem  Desliga a subida automatica do LAPE ao entrar no Windows.
rem
rem  Existe pela mesma razao do "Subir LAPE.bat": o comando equivalente
rem  tem de ser digitado no PowerShell, dentro da pasta certa, com a
rem  politica de execucao liberada -- e cada uma dessas tres coisas ja
rem  deu errado nesta maquina. Aqui e um duplo clique.
rem
rem  O LAPE continua funcionando: o que sai e so a subida automatica.
rem  Para subir na hora, use "Subir LAPE.bat" como antes.
rem ===================================================================
setlocal
title LAPE - nao subir sozinho

cd /d "%~dp0"

echo.
echo   LAPE - desligar a subida automatica
echo   pasta: %CD%
echo.

if not exist "deploy\publicar.ps1" (
  echo   ! Este arquivo nao esta na pasta do sistema.
  echo     Ele precisa ficar junto da pasta "deploy". Se voce o copiou
  echo     para a area de trabalho, apague a copia e crie um ATALHO no
  echo     lugar: botao direito no arquivo original, "Enviar para" ^>
  echo     "Area de trabalho (criar atalho)".
  echo.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\publicar.ps1" -NaoAoLigar

echo.
echo   ------------------------------------------------------------------
echo   O LAPE nao sobe mais sozinho ao ligar o computador.
echo.
echo   Para subir na hora, use "Subir LAPE.bat" como antes.
echo   ------------------------------------------------------------------
echo.
pause
