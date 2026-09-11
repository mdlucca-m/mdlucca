@echo off
rem ===================================================================
rem  Sobe o LAPE com endereco fixo, em um duplo clique.
rem
rem  Existe porque as tres coisas que dao errado ao fazer isso a mao sao
rem  sempre as mesmas: a janela abre em C:\Users\seu-nome e nao na pasta
rem  do sistema, "git" sai digitado como "get", e o PowerShell recusa o
rem  script por politica de execucao. Aqui as tres estao resolvidas.
rem
rem  Para ter na area de trabalho: clique com o botao direito neste
rem  arquivo, "Enviar para" > "Area de trabalho (criar atalho)". O atalho
rem  guarda o caminho certo, e o duplo clique passa a funcionar de
rem  qualquer lugar.
rem ===================================================================
setlocal
title LAPE - subindo o sistema

rem %~dp0 e a pasta DESTE arquivo. E o que dispensa o cd na mao.
cd /d "%~dp0"

echo.
echo   LAPE - Laboratorio de Psicologia do Esporte e do Exercicio
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

where git >nul 2>nul
if errorlevel 1 (
  echo   . git nao encontrado -- seguindo sem buscar atualizacao.
  echo     O sistema sobe com a versao que ja esta nesta pasta.
) else (
  echo   buscando atualizacao...
  git pull --ff-only
  if errorlevel 1 (
    echo.
    echo   . nao deu para atualizar agora. Seguindo com a versao desta
    echo     pasta -- nada foi perdido, e da para tentar de novo depois.
    echo.
  )
)

echo   subindo o sistema e abrindo o endereco fixo...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\publicar.ps1" -Fixo

echo.
echo   ------------------------------------------------------------------
echo   Se o endereco apareceu acima, o sistema esta no ar.
echo   Esta janela precisa FICAR ABERTA: e ela que mantem o tunel de pe.
echo   Para desligar: feche esta janela, ou rode
echo       powershell -ExecutionPolicy Bypass -File deploy\publicar.ps1 -Parar
echo   ------------------------------------------------------------------
echo.
pause
