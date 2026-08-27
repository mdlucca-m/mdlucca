<#
.SYNOPSIS
  Põe o LAPE no ar com um endereço https público. Windows, sem Docker, sem conta.

.DESCRIPTION
  O serviço continua escutando só em 127.0.0.1 — ninguém alcança a porta de
  fora. Quem abre o caminho é o cloudflared, que faz uma conexão de SAÍDA até a
  Cloudflare e recebe de volta um endereço https. Por isso:

    · nenhuma porta precisa ser aberta no firewall da universidade;
    · o computador não precisa de IP público;
    · o certificado https vem pronto;
    · o Windows não vai pedir autorização de firewall.

  Sem opção nenhuma, o endereço é sorteado e MUDA a cada reinício — serve para
  começar hoje, não como endereço do laboratório. Para um endereço que não muda:

    -Fixo        endereço fixo grátis, sem domínio próprio (ngrok). Uma conta
                 gratuita, um domínio reservado do tipo lape.ngrok-free.app.
                 A ressalva: no plano grátis, quem abre pela primeira vez vê
                 uma página de aviso do ngrok antes do site.
    -Permanente  endereço fixo no seu próprio domínio (Cloudflare). Sem página
                 de aviso e sem limite de sessão, mas exige um domínio na
                 Cloudflare — lape.udesc.br, se a universidade delegar, ou um
                 domínio próprio.

  Escolhido o modo uma vez, ele fica gravado: nas próximas vezes basta repetir
  a mesma opção, sem redigitar token nem domínio.

.EXAMPLE
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\deploy\publicar.ps1

.EXAMPLE
  .\deploy\publicar.ps1 -Parar

.EXAMPLE
  # endereco fixo, gratuito, sem dominio proprio
  .\deploy\publicar.ps1 -Fixo

.EXAMPLE
  # endereco fixo no dominio do laboratorio
  .\deploy\publicar.ps1 -Permanente -Dominio lape.udesc.br

.EXAMPLE
  # sobe sozinho toda vez que voce entrar no Windows
  .\deploy\publicar.ps1 -AoLigar

.EXAMPLE
  # qual e o endereco de hoje? (tambem copia para a area de transferencia)
  .\deploy\publicar.ps1 -Endereco
#>
param(
  [int]$Porta = 8000,
  [switch]$Fixo,
  [switch]$Permanente,
  [string]$Dominio = "",
  [string]$Tunel = "lape",
  [switch]$Parar,
  [switch]$Endereco,
  [switch]$AoLigar,
  [switch]$NaoAoLigar
)

$ErrorActionPreference = "Stop"
$Raiz = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Raiz
$Exec = Join-Path $Raiz ".lape-run"
$arqNgrok = Join-Path $Exec "dominio-ngrok.txt"
$arqCF    = Join-Path $Exec "dominio-cloudflare.txt"
$arqEnd   = Join-Path $Exec "endereco.txt"

# Modo escolhido uma vez fica escolhido. Sem isto, rodar o script sem opcao
# nenhuma trocaria o endereco fixo por um sorteado -- e o link que o
# laboratorio inteiro tem salvo morreria em silencio.
if (-not $Fixo -and -not $Permanente) {
  if (Test-Path $arqCF)        { $Permanente = $true }
  elseif (Test-Path $arqNgrok) { $Fixo = $true }
}

function Azul  { param($t) Write-Host $t -ForegroundColor Cyan }
function Verde { param($t) Write-Host $t -ForegroundColor Green }
function Aviso { param($t) Write-Host "! $t" -ForegroundColor Yellow }
# Sair por erro depois de o servico ja estar de pe deixaria a porta 8000
# ocupada e a proxima tentativa falharia sem explicacao.
function Erro  { param($t) Write-Host "! $t" -ForegroundColor Red; Parar-Tudo; exit 1 }

function Parar-Tudo {
  foreach ($nome in @("api", "tunel")) {
    $arquivo = Join-Path $Exec "$nome.pid"
    if (-not (Test-Path $arquivo)) { continue }
    # Um .pid vazio existe sempre que uma subida anterior morreu antes de o
    # processo nascer. `Stop-Process -Id $null` e erro terminante, e com
    # ErrorActionPreference = Stop derrubava o script inteiro na largada --
    # deixando a pessoa sem servico e sem entender por que.
    $pidAlvo = Get-Content $arquivo -ErrorAction SilentlyContinue | Select-Object -First 1
    if ("$pidAlvo".Trim() -match '^\d+$') {
      Stop-Process -Id ([int]"$pidAlvo".Trim()) -Force -ErrorAction SilentlyContinue
      Verde "Encerrado: $nome"
    }
    Remove-Item $arquivo -ErrorAction SilentlyContinue
  }
  # endereco de servico parado nao e endereco: apagar evita mandar a alguem
  # um link que ninguem esta atendendo
  Remove-Item $arqEnd -ErrorAction SilentlyContinue
}

# ------------------------------------------------- subir junto com o Windows
$NomeTarefa = "LAPE - publicar"

function Agendar {
  # Tarefa do usuario, nao do sistema: nao pede administrador, e sobe quando
  # a pessoa faz login -- que e quando o computador do laboratorio comeca a
  # servir de qualquer jeito.
  # o modo vai junto: sem isso, quem configurou endereco fixo veria a tarefa
  # subir um tunel sorteado toda manha, e o link enviado ao laboratorio morria
  $modo = ""
  if ($Fixo)       { $modo = " -Fixo" }
  if ($Permanente) { $modo = " -Permanente" }
  if ($Dominio)    { $modo += " -Dominio $Dominio" }
  $acao = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$($MyInvocation.MyCommand.Path)`" -Porta $Porta$modo" `
    -WorkingDirectory $Raiz
  $gatilho = New-ScheduledTaskTrigger -AtLogOn
  $config  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2)
  Register-ScheduledTask -TaskName $NomeTarefa -Action $acao -Trigger $gatilho `
    -Settings $config -Force | Out-Null
  Verde "Pronto: o LAPE vai subir sozinho toda vez que voce entrar no Windows."
  if ($Fixo -or $Permanente) {
    Verde "Com o endereco fixo que voce ja configurou -- o mesmo de sempre."
  } else {
    Aviso "Ele sobe escondido, e o endereco sorteado muda a cada subida."
    Aviso "Para saber o endereco do dia:  .\deploy\publicar.ps1 -Endereco"
    Aviso "Para nao ter de perguntar nunca mais: -Fixo (gratis) ou -Permanente."
  }
}

if ($AoLigar)    { Agendar; exit 0 }
if ($NaoAoLigar) {
  Unregister-ScheduledTask -TaskName $NomeTarefa -Confirm:$false -ErrorAction SilentlyContinue
  Verde "O LAPE nao sobe mais sozinho."
  exit 0
}
if ($Parar) { Parar-Tudo; exit 0 }

# Sobe escondido pela tarefa agendada, ninguem ve a tela onde o endereco e
# impresso. Este e o jeito de perguntar depois qual e o endereco de hoje.
if ($Endereco) {
  if (-not (Test-Path $arqEnd)) {
    Aviso "O LAPE nao esta no ar. Suba com  .\deploy\publicar.ps1"
    exit 1
  }
  $atual = (Get-Content $arqEnd -Raw).Trim()
  Write-Host ""
  Verde "  Endereco de agora:"
  Write-Host ""
  Write-Host "    $atual/entrar"
  Write-Host ""
  try {
    Set-Clipboard -Value "$atual/entrar"
    Verde "  (copiado - e so colar no WhatsApp ou no e-mail)"
  } catch { }
  Write-Host ""
  exit 0
}
New-Item -ItemType Directory -Force -Path $Exec | Out-Null

# ------------------------------------------------------------------ 1. Python
$Python = $null
foreach ($c in @("python", "python3", "py")) {
  $achado = Get-Command $c -ErrorAction SilentlyContinue
  if ($achado) { $Python = $achado.Source; break }
}
if (-not $Python) { Erro "Python nao encontrado. Instale em python.org e marque 'Add to PATH'." }
$versao = & $Python -c "import sys; print('%d.%d' % sys.version_info[:2])"
if ([version]$versao -lt [version]"3.9") { Erro "E preciso Python 3.9 ou mais novo (achei $versao)." }
Verde "Python $versao"

# --------------------------------------------------------------- 2. cloudflared
$CF = Join-Path $Exec "cloudflared.exe"
$noPath = Get-Command cloudflared -ErrorAction SilentlyContinue
if ($noPath) { $CF = $noPath.Source }
elseif (-not (Test-Path $CF)) {
  Azul "Baixando o cloudflared (uma vez so)..."
  $arq = if ([Environment]::Is64BitOperatingSystem) { "cloudflared-windows-amd64.exe" }
         else { "cloudflared-windows-386.exe" }
  $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/$arq"
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -Uri $url -OutFile $CF -UseBasicParsing
}
Verde "cloudflared pronto"

# ------------------------------------------------------------------- 3. acesso
if (Test-Path (Join-Path $Raiz ".env")) {
  Get-Content (Join-Path $Raiz ".env") | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)$') {
      [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim('"'), "Process")
    }
  }
}

$contas = & $Python -c @"
import sys; sys.path.insert(0, 'scripts')
from lape.db import Database
from lape import config
db = Database(config.DB_PATH); db.migrate()
print(db.scalar('SELECT COUNT(*) FROM members WHERE login IS NOT NULL') or 0)
db.close()
"@
if ($contas.Trim() -eq "0") {
  Azul "Nenhum acesso cadastrado. Vamos criar o seu."
  $nome  = Read-Host "  Seu nome"
  $login = Read-Host "  Seu e-mail (sera o login)"
  $senha = & $Python -c "import secrets; print(secrets.token_urlsafe(12))"
  $senha = $senha.Trim()
  & $Python scripts\lape_agent.py usuarios --criar $nome $login --senha $senha --perfil admin
  Write-Host ""
  Verde  "  ANOTE AGORA - esta senha nao e mostrada de novo:"
  Write-Host "    login: $login"
  Write-Host "    senha: $senha"
  Write-Host ""
  Read-Host "  Anotou? Enter para continuar"
}

# -------------------------------------------------------------------- 4. servico
Parar-Tudo
Azul "Subindo o servico..."
# O cookie so vale sob https (o tunel), e o endereco real do visitante vem do
# cabecalho que o cloudflared preenche.
$env:LAPE_BEHIND_HTTPS = "1"
$env:LAPE_TRUST_PROXY  = "1"
$api = Start-Process -FilePath $Python `
  -ArgumentList "scripts\lape_agent.py", "api", "--host", "127.0.0.1", "--port", "$Porta" `
  -WorkingDirectory $Raiz -PassThru -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $Exec "api.log") `
  -RedirectStandardError  (Join-Path $Exec "api.err")
if (-not $api) { Erro "Nao consegui iniciar o servico." }
$api.Id | Out-File (Join-Path $Exec "api.pid") -Encoding ascii

$ok = $false
foreach ($i in 1..40) {
  try {
    Invoke-RestMethod -Uri "http://127.0.0.1:$Porta/api/health" -TimeoutSec 2 | Out-Null
    $ok = $true; break
  } catch { Start-Sleep -Milliseconds 500 }
}
if (-not $ok) {
  Get-Content (Join-Path $Exec "api.err") -Tail 20 -ErrorAction SilentlyContinue
  Erro "O servico nao subiu. Log acima."
}
Verde "Servico no ar em 127.0.0.1:$Porta"

# --------------------------------------------------------------------- 5. tunel
# Tres modos, um so resultado: $Link. Do lado de ca nada muda -- o servico
# continua escutando so em 127.0.0.1, e quem abre o caminho e sempre uma
# conexao de saida.
$Link = $null

function Esperar-Tunel {
  param($padrao, $processo, $segundos = 90)
  foreach ($i in 1..$segundos) {
    Start-Sleep -Seconds 1
    foreach ($arquivo in @("tunel.err", "tunel.log")) {
      $caminho = Join-Path $Exec $arquivo
      if (Test-Path $caminho) {
        $achado = Select-String -Path $caminho -Pattern $padrao -AllMatches `
          -ErrorAction SilentlyContinue | ForEach-Object { $_.Matches } | Select-Object -First 1
        if ($achado) { return $achado.Value }
      }
    }
    # tunel que morreu nao vai imprimir endereco nenhum: esperar o resto do
    # prazo so faz a pessoa olhar para uma tela parada
    if ($processo -and $processo.HasExited) { return $null }
  }
  return $null
}

function Parar-Tunel {
  $arquivo = Join-Path $Exec "tunel.pid"
  if (-not (Test-Path $arquivo)) { return }
  $alvo = Get-Content $arquivo -ErrorAction SilentlyContinue | Select-Object -First 1
  if ("$alvo".Trim() -match '^\d+$') {
    Stop-Process -Id ([int]"$alvo".Trim()) -Force -ErrorAction SilentlyContinue
  }
  Remove-Item $arquivo -ErrorAction SilentlyContinue
}

function Mostrar-Log-Do-Tunel {
  Get-Content (Join-Path $Exec "tunel.err") -Tail 20 -ErrorAction SilentlyContinue
  Get-Content (Join-Path $Exec "tunel.log") -Tail 20 -ErrorAction SilentlyContinue
}

# ---------------------------------------------- 5a. endereco fixo gratuito
if ($Fixo) {
  $NG = Join-Path $Exec "ngrok.exe"
  $noPath = Get-Command ngrok -ErrorAction SilentlyContinue
  if ($noPath) { $NG = $noPath.Source }
  elseif (-not (Test-Path $NG)) {
    Azul "Baixando o ngrok (uma vez so)..."
    $arq = if ([Environment]::Is64BitOperatingSystem) { "ngrok-v3-stable-windows-amd64.zip" }
           else { "ngrok-v3-stable-windows-386.zip" }
    $zip = Join-Path $Exec "ngrok.zip"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri "https://bin.equinox.io/c/bNyj1mQVY4c/$arq" -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $Exec -Force
    Remove-Item $zip -ErrorAction SilentlyContinue
  }
  Verde "ngrok pronto"

  if (-not $Dominio -and (Test-Path $arqNgrok)) {
    $Dominio = (Get-Content $arqNgrok -Raw).Trim()
  }
  if (-not $Dominio) {
    Write-Host @"

  Endereco fixo gratuito -- tres passos, uma vez so:

    1. Crie a conta gratuita em  https://dashboard.ngrok.com/signup
    2. Copie o authtoken de      https://dashboard.ngrok.com/get-started/your-authtoken
    3. Reserve o dominio em      https://dashboard.ngrok.com/domains
       (a conta gratuita da direito a um, do tipo lape-udesc.ngrok-free.app)

"@
    $token = Read-Host "  Cole o authtoken"
    if ($token) { & $NG config add-authtoken $token.Trim() | Out-Null }
    $Dominio = Read-Host "  Cole o dominio reservado"
  }
  $Dominio = ($Dominio -replace '^https?://', '').Trim().TrimEnd('/')
  if (-not $Dominio) { Erro "Sem dominio reservado nao da para fixar o endereco." }
  $Dominio | Out-File $arqNgrok -Encoding ascii

  Azul "Abrindo o tunel fixo..."
  $procTunel = Start-Process -FilePath $NG `
    -ArgumentList "http", "--domain=$Dominio", "--log=stdout", "127.0.0.1:$Porta" `
    -WorkingDirectory $Raiz -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $Exec "tunel.log") `
    -RedirectStandardError  (Join-Path $Exec "tunel.err")
  if (-not $procTunel) { Erro "Nao consegui iniciar o tunel." }
  $procTunel.Id | Out-File (Join-Path $Exec "tunel.pid") -Encoding ascii

  # o proprio ngrok publica em 127.0.0.1:4040 o que conseguiu abrir -- e mais
  # confiavel do que confiar no dominio que a pessoa digitou
  foreach ($i in 1..30) {
    Start-Sleep -Seconds 1
    try {
      $painel = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 2
      $publico = $painel.tunnels | Where-Object { $_.public_url -like "https://*" } |
                 Select-Object -First 1
      if ($publico) { $Link = $publico.public_url; break }
    } catch { }
  }
  if (-not $Link) {
    Mostrar-Log-Do-Tunel
    Erro "O tunel fixo nao abriu. Log acima. Confira o authtoken e o dominio reservado."
  }
}

# -------------------------------------- 5b. endereco fixo no dominio proprio
elseif ($Permanente) {
  if (-not $Dominio -and (Test-Path $arqCF)) {
    $Dominio = (Get-Content $arqCF -Raw).Trim()
  }
  if (-not $Dominio) {
    Write-Host @"

  Endereco fixo no dominio do laboratorio, pela Cloudflare. Sem pagina de
  aviso e sem limite de sessao, mas exige um dominio ja hospedado la:

    · lape.udesc.br, se a universidade delegar o subdominio, ou
    · um dominio proprio -- um .com.br no registro.br sai por poucos reais
      ao ano, e a Cloudflare nao cobra nada pelo tunel.

  Com o dominio em maos:

    .\deploy\publicar.ps1 -Permanente -Dominio lape.seu-dominio.br

  O script cuida do resto: autoriza no navegador, cria o tunel, aponta o DNS
  e sobe. Da segunda vez em diante, so -Permanente.

  Sem dominio nenhum, o equivalente gratuito e  .\deploy\publicar.ps1 -Fixo

"@
    Parar-Tudo
    exit 0
  }
  $Dominio = ($Dominio -replace '^https?://', '').Trim().TrimEnd('/')

  $cert = Join-Path $env:USERPROFILE ".cloudflared\cert.pem"
  if (-not (Test-Path $cert)) {
    Azul "Autorize o cloudflared no navegador que vai abrir (uma vez so)..."
    & $CF tunnel login
    if (-not (Test-Path $cert)) { Erro "A autorizacao nao foi concluida." }
  }
  $lista = (& $CF tunnel list 2>&1 | Out-String)
  if ($lista -notmatch [regex]::Escape($Tunel)) {
    Azul "Criando o tunel '$Tunel'..."
    & $CF tunnel create $Tunel
  }
  Azul "Apontando $Dominio para o tunel..."
  & $CF tunnel route dns --overwrite-dns $Tunel $Dominio | Out-Null
  $Dominio | Out-File $arqCF -Encoding ascii

  Azul "Abrindo o tunel permanente..."
  $procTunel = Start-Process -FilePath $CF `
    -ArgumentList "tunnel", "--no-autoupdate", "run", "--url", "http://127.0.0.1:$Porta", $Tunel `
    -WorkingDirectory $Raiz -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $Exec "tunel.log") `
    -RedirectStandardError  (Join-Path $Exec "tunel.err")
  if (-not $procTunel) { Erro "Nao consegui iniciar o tunel." }
  $procTunel.Id | Out-File (Join-Path $Exec "tunel.pid") -Encoding ascii

  $Link = "https://$Dominio"
  # o DNS pode levar um minuto para propagar; nao e motivo para abortar, so
  # para avisar -- o tunel ja esta de pe e o endereco passa a responder
  $respondeu = $false
  foreach ($i in 1..20) {
    Start-Sleep -Seconds 3
    try {
      Invoke-RestMethod -Uri "$Link/api/health" -TimeoutSec 4 | Out-Null
      $respondeu = $true; break
    } catch { }
  }
  if (-not $respondeu) {
    Aviso "O tunel subiu, mas $Dominio ainda nao respondeu."
    Aviso "DNS costuma levar ate uns minutos na primeira vez. Tente abrir daqui a pouco."
  }
}

# ------------------------------------------- 5c. endereco sorteado (padrao)
else {
  # O tunel sorteado e servico de cortesia da Cloudflare, sem garantia de
  # disponibilidade -- o proprio aviso no log diz isso. As vezes ele pede o
  # endereco e a resposta nao vem. Uma segunda tentativa custa pouco e
  # resolve a maior parte dos casos; desistir na primeira e que nao.
  foreach ($tentativa in 1..2) {
    if ($tentativa -gt 1) {
      Aviso "A Cloudflare nao devolveu endereco. Tentando mais uma vez..."
      Parar-Tunel
      Remove-Item (Join-Path $Exec "tunel.err") -ErrorAction SilentlyContinue
      Remove-Item (Join-Path $Exec "tunel.log") -ErrorAction SilentlyContinue
    } else {
      Azul "Abrindo o tunel..."
    }
    $procTunel = Start-Process -FilePath $CF `
      -ArgumentList "tunnel", "--no-autoupdate", "--url", "http://127.0.0.1:$Porta" `
      -WorkingDirectory $Raiz -PassThru -WindowStyle Hidden `
      -RedirectStandardOutput (Join-Path $Exec "tunel.log") `
      -RedirectStandardError  (Join-Path $Exec "tunel.err")
    if (-not $procTunel) { Erro "Nao consegui iniciar o tunel." }
    $procTunel.Id | Out-File (Join-Path $Exec "tunel.pid") -Encoding ascii

    # o cloudflared escreve o endereco na saida de erro, nao na padrao
    $Link = Esperar-Tunel 'https://[a-z0-9-]+\.trycloudflare\.com' $procTunel
    if ($Link) { break }
  }
  if (-not $Link) {
    Mostrar-Log-Do-Tunel
    Write-Host ""
    Aviso "O tunel sorteado e de cortesia e cai as vezes. Rode o comando de novo."
    Aviso "Para nao depender dele: .\deploy\publicar.ps1 -Fixo"
    Erro "A Cloudflare nao devolveu endereco em duas tentativas."
  }
}

$Link | Out-File $arqEnd -Encoding ascii

# ------------------------------------------------------------------ 6. conferir
Write-Host ""
& $Python scripts\lape_agent.py publicar

Write-Host ""
Verde "==============================================================="
Verde "  No ar. Envie este endereco as pessoas:"
Write-Host ""
Write-Host "    $Link/entrar"
Write-Host ""
Write-Host "  Painel ......... $Link/"
Write-Host "  Cadastro ....... $Link/app"
Verde "==============================================================="
Write-Host ""
if ($Fixo -or $Permanente) {
  Verde "Este endereco e fixo: fechou a janela, ele volta o MESMO na proxima vez."
  Aviso "So funciona com esta janela aberta -- o servico roda aqui."
  if ($Fixo) {
    Aviso "No plano gratuito do ngrok, quem abre pela primeira vez ve uma pagina"
    Aviso "de aviso antes do site. Basta clicar em Visit Site."
  }
} else {
  Aviso "Enquanto esta janela estiver aberta, o endereco funciona."
  Aviso "Fechou ou desligou o computador, o endereco cai - e volta OUTRO na"
  Aviso "proxima vez. Para endereco fixo: -Fixo (gratis) ou -Permanente (dominio)."
}
Write-Host ""
Write-Host "Para encerrar: feche esta janela, ou rode .\deploy\publicar.ps1 -Parar"
Write-Host "Para rever este endereco depois: .\deploy\publicar.ps1 -Endereco"
if (-not (Get-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue)) {
  Write-Host "Para subir sozinho toda vez: .\deploy\publicar.ps1 -AoLigar"
}
Write-Host ""

try {
  while (-not $api.HasExited) { Start-Sleep -Seconds 5 }
} finally {
  Parar-Tudo
}
