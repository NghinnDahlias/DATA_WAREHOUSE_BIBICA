$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
$statePath=Join-Path $repoRoot '.runtime/api-service.json'
if (!(Test-Path -LiteralPath $statePath)) { Write-Host 'No owned repository API state.'; exit 0 }
$state=Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
$process=Get-Process -Id $state.pid -ErrorAction SilentlyContinue
if ($process) {
    if ($process.StartTime.ToUniversalTime().ToString('o') -ne $state.started) { throw 'PID start time differs. Process was not stopped.' }
    Stop-Process -Id $process.Id
}
Remove-Item -LiteralPath $statePath
Write-Host 'Repository API stopped.'
