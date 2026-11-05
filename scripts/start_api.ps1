param([string]$Python='', [int]$Port=8001)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot
if (!$Python) {
    $Python=Join-Path $repoRoot '.venv/Scripts/python.exe'
    if (!(Test-Path -LiteralPath $Python)) { $Python=Join-Path $repoRoot '../.venv/Scripts/python.exe' }
    if (!(Test-Path -LiteralPath $Python)) { $Python=(Get-Command python.exe).Source }
}
$Python=(Resolve-Path -LiteralPath $Python).Path
$expectedDb=& $Python -X utf8 -c "from src.api.db import database_dsn; from psycopg.conninfo import conninfo_to_dict; print(conninfo_to_dict(database_dsn()).get('dbname',''))"
if ($LASTEXITCODE -ne 0 -or !$expectedDb) { throw 'Repository database configuration is invalid.' }
New-Item -ItemType Directory -Force '.runtime' | Out-Null
$statePath=Join-Path $repoRoot '.runtime/api-service.json'
if (Test-Path -LiteralPath $statePath) {
    $state=Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
    $existing=Get-Process -Id $state.pid -ErrorAction SilentlyContinue
    if ($existing -and $existing.StartTime.ToUniversalTime().ToString('o') -eq $state.started) {
        $health=Invoke-RestMethod -Uri "http://127.0.0.1:$($state.port)/health" -TimeoutSec 5
        if ($health.data.ready -and $state.port -eq $Port -and $health.data.database -eq $expectedDb) {
            Write-Host "Repo API http://127.0.0.1:$Port/docs"
            exit 0
        }
        throw 'Owned API is running with a different configuration. Stop it using stop_api.ps1 first.'
    }
}
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
    throw "Port $Port is already in use. No process was stopped."
}
$pidPath=Join-Path $repoRoot '.runtime/api.pid.json'
if (Test-Path -LiteralPath $pidPath) { Remove-Item -LiteralPath $pidPath }
Start-Process -FilePath $Python -ArgumentList '-X','utf8','scripts/serve_api.py','--port',"$Port" -WorkingDirectory $repoRoot -WindowStyle Hidden -RedirectStandardOutput "$repoRoot/.runtime/api.out.log" -RedirectStandardError "$repoRoot/.runtime/api.err.log" | Out-Null
for ($attempt=0; $attempt -lt 60 -and !(Test-Path -LiteralPath $pidPath); $attempt++) { Start-Sleep -Milliseconds 200 }
if (!(Test-Path -LiteralPath $pidPath)) { throw 'API did not start. See .runtime/api.err.log.' }
$actual=Get-Content -Raw -LiteralPath $pidPath | ConvertFrom-Json
$process=Get-Process -Id $actual.pid -ErrorAction Stop
$state=@{pid=$process.Id;started=$process.StartTime.ToUniversalTime().ToString('o');port=$Port;database=$expectedDb}
$state | ConvertTo-Json | Set-Content -Encoding utf8 -LiteralPath $statePath
$ready=$false
for ($attempt=0; $attempt -lt 40 -and !$ready; $attempt++) {
    try { $health=Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2; $ready=$health.data.ready } catch {}
    if (!$ready) { Start-Sleep -Milliseconds 250 }
}
if (!$ready) { throw 'API readiness failed. Check repository DSN and .runtime/api.err.log.' }
Write-Host "Repo API http://127.0.0.1:$Port/docs"
