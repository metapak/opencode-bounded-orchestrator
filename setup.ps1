$ErrorActionPreference = "Stop"
Write-Host "============================================================" -ForegroundColor DarkGray
Write-Host " OpenCode Bounded Orchestrator 0.1.0" -ForegroundColor Cyan
Write-Host " Guided setup / Windows" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor DarkGray
Write-Host "OpenCode V2 roles inherit the current session model by default."
Write-Host "Use /connect and /models in OpenCode to configure providers.`n"
& "$PSScriptRoot\scripts\install.ps1"
exit $LASTEXITCODE
