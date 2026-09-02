param([switch]$BuildOnly, [switch]$Release)

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$Flutter = "C:\Flutter-3.44.9\flutter\bin\flutter.bat"
$DesktopUi = Join-Path $PSScriptRoot "desktop_ui"
$DesktopPubCache = Join-Path $PSScriptRoot ".pub-cache"
$BuildMode = if ($Release) { "--release" } else { "--debug" }

if (-not $BuildOnly -and -not (Test-Path -LiteralPath $Python)) {
    Write-Host "JARVIS virtual environment was not found."
    Write-Host "Run: python -m venv .venv"
    exit 1
}

if (-not (Test-Path -LiteralPath $Flutter)) {
    Write-Host "Flutter SDK was not found at C:\Flutter-3.44.9\flutter."
    exit 1
}

$PreviousPubCache = $env:PUB_CACHE
$PreviousProcessDirectory = [Environment]::CurrentDirectory
$DesktopExitCode = 1

Push-Location -LiteralPath $DesktopUi
try {
    # Keep PowerShell's location and the native process directory in sync.
    [Environment]::CurrentDirectory = $DesktopUi
    # Resolve app packages independently of the user's shared AppData Pub cache.
    # This is process-local and is restored when the launcher finishes.
    $env:PUB_CACHE = $DesktopPubCache
    Write-Host "Flutter project: $DesktopUi"
    Write-Host "Dependency cache: $DesktopPubCache"
    & $Flutter pub get --enforce-lockfile
    if ($LASTEXITCODE -ne 0) {
        throw "Dependency setup failed. Flutter was not started; see the first error above."
    }

    if ($BuildOnly) {
        & $Flutter build windows $BuildMode --no-pub
    } else {
        $ExistingApi = Get-NetTCPConnection -LocalAddress "127.0.0.1" -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
        if (-not $ExistingApi) {
            Start-Process -FilePath $Python -ArgumentList "-m", "uvicorn", "app.api:app", "--host", "127.0.0.1", "--port", "8765" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
            Start-Sleep -Seconds 1
        }
        # Use exactly the package configuration generated above.
        & $Flutter run -d windows $BuildMode --no-pub
    }
    $DesktopExitCode = $LASTEXITCODE
} catch {
    Write-Error $_
} finally {
    $env:PUB_CACHE = $PreviousPubCache
    [Environment]::CurrentDirectory = $PreviousProcessDirectory
    Pop-Location
}

exit $DesktopExitCode
