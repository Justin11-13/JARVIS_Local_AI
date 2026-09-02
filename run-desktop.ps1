$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$Flutter = "C:\Flutter-3.44.9\flutter\bin\flutter.bat"

if (-not (Test-Path $Python)) {
    Write-Host "JARVIS virtual environment was not found."
    Write-Host "Run: python -m venv .venv"
    exit 1
}

if (-not (Test-Path $Flutter)) {
    Write-Host "Flutter SDK was not found at C:\Flutter-3.44.9\flutter."
    exit 1
}

$ExistingApi = Get-NetTCPConnection -LocalAddress "127.0.0.1" -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue

if (-not $ExistingApi) {
    Start-Process -FilePath $Python -ArgumentList "-m", "uvicorn", "app.api:app", "--host", "127.0.0.1", "--port", "8765" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
    Start-Sleep -Seconds 1
}

Set-Location (Join-Path $PSScriptRoot "desktop_ui")
& $Flutter run -d windows
