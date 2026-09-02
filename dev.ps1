$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$Watchfiles = Join-Path $PSScriptRoot ".venv\Scripts\watchfiles.exe"

if (-not (Test-Path $Python)) {
    Write-Host "JARVIS virtual environment was not found."
    Write-Host "Run: python -m venv .venv"
    exit 1
}

if (-not (Test-Path $Watchfiles)) {
    Write-Host "watchfiles is not installed."
    Write-Host "Run: .\.venv\Scripts\python.exe -m pip install watchfiles"
    exit 1
}

Write-Host "Starting JARVIS Development Mode..."
Write-Host "Auto reload is enabled."
Write-Host ""

& $Watchfiles "$Python -m app.main" $PSScriptRoot
