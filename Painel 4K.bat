@echo off
rem ===================================================================
rem  Sobe o Painel 4K (dispersao 3D, funil cilindrico, cartao
rem  holografico) em um duplo clique.
rem
rem  E um programa SEPARADO do site principal do LAPE -- le o mesmo
rem  banco (data\db.sqlite), mas abre so nesta tela, em
rem  http://localhost:8501, e nao pelo link publico do "Subir LAPE.bat".
rem  Na primeira vez, instala sozinho as bibliotecas que faltam
rem  (streamlit, plotly, sqlalchemy) -- so demora nessa primeira vez.
rem
rem  Para ter na area de trabalho: clique com o botao direito neste
rem  arquivo, "Enviar para" > "Area de trabalho (criar atalho)".
rem ===================================================================
setlocal
title LAPE - Painel 4K

rem %~dp0 e a pasta DESTE arquivo. E o que dispensa o cd na mao.
cd /d "%~dp0"

echo.
echo   LAPE - Painel 4K
echo   pasta: %CD%
echo.

if not exist "scripts\lape_streamlit_4k.py" (
  echo   ! Este arquivo nao esta na pasta do sistema.
  echo     Ele precisa ficar junto da pasta "scripts". Se voce o copiou
  echo     para a area de trabalho, apague a copia e crie um ATALHO no
  echo     lugar: botao direito no arquivo original, "Enviar para" ^>
  echo     "Area de trabalho (criar atalho)".
  echo.
  pause
  exit /b 1
)

set PY=python
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo   ! Python nao encontrado. Instale em python.org e marque
    echo     "Add to PATH", depois rode este atalho de novo.
    echo.
    pause
    exit /b 1
  )
  set PY=py
)

%PY% -c "import streamlit, sqlalchemy, plotly" >nul 2>nul
if errorlevel 1 (
  echo   Primeira vez: instalando as bibliotecas do painel
  echo   ^(streamlit, sqlalchemy, plotly^) -- so demora agora...
  echo.
  %PY% -m pip install -r requirements-painel4k.txt
  if errorlevel 1 (
    echo.
    echo   ! Nao consegui instalar as bibliotecas. Confira sua internet
    echo     e rode este atalho de novo.
    pause
    exit /b 1
  )
  echo.
)

rem O Streamlit pergunta um e-mail na PRIMEIRA vez que roda em qualquer
rem pasta, e fica PARADO na janela esperando resposta -- sem ninguem
rem para digitar algo ali, o duplo clique "nao faz nada" (a janela abre,
rem trava calada, o navegador nunca chega a abrir). Gravar a credencial
rem vazia de antemao pula essa pergunta para sempre, em qualquer pasta.
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit" >nul 2>nul
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  echo [general] > "%USERPROFILE%\.streamlit\credentials.toml"
  echo email = "" >> "%USERPROFILE%\.streamlit\credentials.toml"
)

echo   abrindo o painel -- o navegador abre sozinho em instantes...
echo.
echo   ------------------------------------------------------------------
echo   Esta janela precisa FICAR ABERTA: e ela que mantem o painel no ar.
echo   Endereco: http://localhost:8501  (so nesta maquina)
echo   Para desligar: feche esta janela, ou aperte Ctrl+C aqui.
echo   ------------------------------------------------------------------
echo.

%PY% -m streamlit run scripts\lape_streamlit_4k.py --browser.gatherUsageStats false

pause
