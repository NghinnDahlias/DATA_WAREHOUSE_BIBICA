$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
$statePath=Join-Path $repoRoot '.runtime/frontend-service.json'
if (!(Test-Path -LiteralPath $statePath)) { Write-Host 'No owned frontend state.'; exit 0 }
$state=Get-Content -Raw -LiteralPath $statePath | ConvertFrom-Json
$process=Get-Process -Id $state.pid -ErrorAction SilentlyContinue
if ($process -and $process.StartTime.ToUniversalTime().ToString('o') -eq $state.started) { Stop-Process -Id $process.Id -ErrorAction Stop }
Remove-Item -LiteralPath $statePath
Write-Host 'Repository frontend stopped.'
