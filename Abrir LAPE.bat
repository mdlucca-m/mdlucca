@echo off
rem ===================================================================
rem  Abre o LAPE neste computador, em um duplo clique.
rem
rem  Existe porque as tres coisas que davam errado ao fazer isso a mao
rem  sao sempre as mesmas, e nenhuma delas e culpa de quem digita:
rem
rem    1. a janela do terminal abre em C:\Users\seu-nome, e nao na pasta
rem       do sistema -- e nao avisa;
rem    2. o endereco 127.0.0.1:8000 vai parar no terminal em vez do
rem       navegador, porque os dois se parecem na tela;
rem    3. o PowerShell e o Prompt de Comando tem sintaxes diferentes, e
rem       um comando que serve para um da erro no outro.
rem
rem  Aqui as tres estao resolvidas: este arquivo entra na pasta certa,
rem  abre o navegador sozinho e sobe o servidor.
rem
rem  DIFERENCA PARA O 'Subir LAPE.bat': aquele publica o endereco fixo
rem  para o laboratorio inteiro (e depende do tunel do ngrok). Este aqui
rem  serve so NESTE computador, e por isso sempre funciona.
rem
rem  Os dois buscam atualizacao antes de subir. So este aqui nao buscava,
rem  e quem so usa este ficava para tras sem nada avisar: o sistema subia
rem  igual, com o codigo da semana passada.
rem ===================================================================
setlocal
title LAPE - neste computador

rem %~dp0 e a pasta DESTE arquivo. E o que dispensa o cd na mao.
cd /d "%~dp0"

echo.
echo   LAPE - Laboratorio de Psicologia do Esporte e do Exercicio
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
echo.

rem O navegador abre ANTES do servidor de proposito: ele leva um segundo
rem para carregar, e nesse tempo o servidor ja subiu. Se aparecer erro de
rem conexao, basta atualizar a pagina.
start "" http://127.0.0.1:8000

echo   subindo o sistema...
echo   Esta janela precisa FICAR ABERTA: e ela que mantem o LAPE de pe.
echo   Para desligar o LAPE, feche esta janela.
echo.

python scripts\lape_agent.py api --port 8000

rem So chega aqui se o servidor parou. Sem o pause, a janela sumiria
rem levando a mensagem de erro junto -- que e exatamente o que impede
rem de descobrir o motivo.
echo.
echo   ------------------------------------------------------------------
echo   O LAPE parou. Se houve erro, ele esta nas linhas acima.
echo   ------------------------------------------------------------------
pause
