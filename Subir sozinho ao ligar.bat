@echo off
rem ===================================================================
rem  Faz o LAPE subir sozinho toda vez que voce entrar no Windows.
rem
rem  Existe pela mesma razao do "Subir LAPE.bat": o comando equivalente
rem  tem de ser digitado no PowerShell, dentro da pasta certa, com a
rem  politica de execucao liberada -- e cada uma dessas tres coisas ja
rem  deu errado nesta maquina. Aqui e um duplo clique.
rem
rem  O modo NAO e passado de proposito. O publicar.ps1 le o modo que ja
rem  esta gravado (endereco fixo do ngrok, ou dominio proprio) e registra
rem  a tarefa com ele. Passar -Fixo aqui a mao seria mais uma chance de
rem  a tarefa subir num modo diferente do que o laboratorio usa, e o link
rem  que todo mundo tem salvo morreria de manha.
rem
rem  Para DESLIGAR depois: "Nao subir sozinho.bat", ao lado deste.
rem ===================================================================
setlocal
title LAPE - subir sozinho ao ligar

cd /d "%~dp0"

echo.
echo   LAPE - subir sozinho ao ligar o computador
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

powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\publicar.ps1" -AoLigar

echo.
echo   ------------------------------------------------------------------
echo   Se apareceu a confirmacao acima, o LAPE passa a subir sozinho
echo   quando voce entrar no Windows -- no mesmo endereco de sempre.
echo.
echo   A tarefa se reergue sozinha se cair, e funciona com o notebook
echo   na bateria. Para desligar: "Nao subir sozinho.bat".
echo   ------------------------------------------------------------------
echo.
pause
