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

  O endereço vale enquanto esta janela estiver aberta, e muda a cada reinício.
  Para um endereço fixo, veja -Permanente.

.EXAMPLE
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\deploy\publicar.ps1

.EXAMPLE
  .\deploy\publicar.ps1 -Parar
#>
param(
  [int]$Porta = 8000,
  [switch]$Permanente,
  [switch]$Parar
)

$ErrorActionPreference = "Stop"
$Raiz = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Raiz
$Exec = Join-Path $Raiz ".lape-run"

function Azul  { param($t) Write-Host $t -ForegroundColor Cyan }
function Verde { param($t) Write-Host $t -ForegroundColor Green }
function Aviso { param($t) Write-Host "! $t" -ForegroundColor Yellow }
function Erro  { param($t) Write-Host "! $t" -ForegroundColor Red; exit 1 }

function Parar-Tudo {
  foreach ($nome in @("api", "tunel")) {
    $arquivo = Join-Path $Exec "$nome.pid"
    if (Test-Path $arquivo) {
      $pidAlvo = Get-Content $arquivo
      Stop-Process -Id $pidAlvo -Force -ErrorAction SilentlyContinue
      Remove-Item $arquivo -ErrorAction SilentlyContinue
      Verde "Encerrado: $nome"
    }
  }
}

if ($Parar) { Parar-Tudo; exit 0 }
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
if ($Permanente) {
  Write-Host @"

  Endereco fixo pede uma conta gratuita da Cloudflare. Tres passos, uma vez so:

    .\.lape-run\cloudflared.exe tunnel login
    .\.lape-run\cloudflared.exe tunnel create lape
    .\.lape-run\cloudflared.exe tunnel route dns lape lape.seu-dominio.br

  Depois, para subir:

    .\.lape-run\cloudflared.exe tunnel run --url http://127.0.0.1:$Porta lape

  Sem dominio proprio da para usar um gratuito (duckdns.org) delegado a
  Cloudflare. Para comecar agora, rode este script sem -Permanente.

"@
  exit 0
}

Azul "Abrindo o tunel..."
$tunel = Start-Process -FilePath $CF `
  -ArgumentList "tunnel", "--no-autoupdate", "--url", "http://127.0.0.1:$Porta" `
  -WorkingDirectory $Raiz -PassThru -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $Exec "tunel.log") `
  -RedirectStandardError  (Join-Path $Exec "tunel.err")
$tunel.Id | Out-File (Join-Path $Exec "tunel.pid") -Encoding ascii

# o cloudflared escreve o endereco na saida de erro, nao na padrao
$endereco = $null
foreach ($i in 1..60) {
  Start-Sleep -Seconds 1
  foreach ($arquivo in @("tunel.err", "tunel.log")) {
    $caminho = Join-Path $Exec $arquivo
    if (Test-Path $caminho) {
      $achado = Select-String -Path $caminho -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' `
        -AllMatches -ErrorAction SilentlyContinue |
        ForEach-Object { $_.Matches } | Select-Object -First 1
      if ($achado) { $endereco = $achado.Value; break }
    }
  }
  if ($endereco) { break }
}
if (-not $endereco) {
  Get-Content (Join-Path $Exec "tunel.err") -Tail 20 -ErrorAction SilentlyContinue
  Erro "O tunel nao abriu. Log acima."
}

# ------------------------------------------------------------------ 6. conferir
Write-Host ""
& $Python scripts\lape_agent.py publicar

Write-Host ""
Verde "==============================================================="
Verde "  No ar. Envie este endereco as pessoas:"
Write-Host ""
Write-Host "    $endereco/entrar"
Write-Host ""
Write-Host "  Painel ......... $endereco/"
Write-Host "  Cadastro ....... $endereco/app"
Verde "==============================================================="
Write-Host ""
Aviso "Enquanto esta janela estiver aberta, o endereco funciona."
Aviso "Fechou ou desligou o computador, o endereco cai - e volta OUTRO na"
Aviso "proxima vez. Para endereco fixo: .\deploy\publicar.ps1 -Permanente"
Write-Host ""
Write-Host "Para encerrar: feche esta janela, ou rode .\deploy\publicar.ps1 -Parar"
Write-Host ""

try {
  while (-not $api.HasExited) { Start-Sleep -Seconds 5 }
} finally {
  Parar-Tudo
}
