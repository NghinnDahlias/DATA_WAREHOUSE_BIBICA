param([int]$Port=5174)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot
New-Item -ItemType Directory -Force '.runtime' | Out-Null
$statePath=Join-Path $repoRoot '.runtime/frontend-service.json'
if (!(Test-Path -LiteralPath 'frontend/node_modules/vite/bin/vite.js')) { throw 'Run npm --prefix frontend ci first.' }
if (Test-Path -LiteralPath $statePath) {
    $state=Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
    $existing=Get-Process -Id $state.pid -ErrorAction SilentlyContinue
    if ($existing -and $existing.StartTime.ToUniversalTime().ToString('o') -eq $state.started) {
        if ($state.port -ne $Port) { throw 'Owned frontend has a different port. Stop it using stop_frontend.ps1 first.' }
        $response=Invoke-WebRequest "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) { Write-Host "Repo dashboard http://127.0.0.1:$Port"; exit 0 }
    }
}
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) { throw "Port $Port is in use. No process was stopped." }
$nodeCommand=(Get-Command node.exe).Source
$process=Start-Process -FilePath $nodeCommand -ArgumentList 'node_modules/vite/bin/vite.js','--host','127.0.0.1','--port',"$Port",'--strictPort' -WorkingDirectory "$repoRoot/frontend" -WindowStyle Hidden -PassThru -RedirectStandardOutput "$repoRoot/.runtime/frontend.out.log" -RedirectStandardError "$repoRoot/.runtime/frontend.err.log"
@{pid=$process.Id;started=$process.StartTime.ToUniversalTime().ToString('o');port=$Port} | ConvertTo-Json | Set-Content -Encoding utf8 -LiteralPath $statePath
for ($attempt=0;$attempt -lt 40;$attempt++) {
    try {
        $response=Invoke-WebRequest "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) { Write-Host "Repo dashboard http://127.0.0.1:$Port"; exit 0 }
    } catch {}
    Start-Sleep -Milliseconds 250
}
throw 'Frontend did not start. See .runtime/frontend.err.log.'
