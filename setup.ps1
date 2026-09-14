[CmdletBinding()]
param(
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$Verify
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$PythonLock = Join-Path $Root "requirements.lock.txt"
$ElectronRoot = Join-Path $Root "electron_motion_preview"

if (-not $SkipPython) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw "Python was not found on PATH. Install CPython 3.12.x or newer, then rerun setup.ps1."
    }
    if (-not (Test-Path -LiteralPath $PythonLock)) {
        throw "The locked Python dependency file is missing: $PythonLock"
    }
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Write-Host "Creating JARVIS virtual environment..."
        & $PythonCommand.Source -m venv (Join-Path $Root ".venv")
        if ($LASTEXITCODE -ne 0) {
            throw "Python virtual environment creation failed."
        }
    }
    Write-Host "Installing locked Python dependencies..."
    & $VenvPython -m pip install -r $PythonLock
    if ($LASTEXITCODE -ne 0) {
        throw "Python dependency installation failed."
    }
}

if (-not $SkipNode) {
    $NodeCommand = Get-Command node -ErrorAction SilentlyContinue
    $NpmCommand = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $NodeCommand -or -not $NpmCommand) {
        throw "Node.js and npm were not found on PATH. Install Node.js 22.12.x or newer, then rerun setup.ps1."
    }
    $NodeVersion = [version]( (& $NodeCommand.Source --version).Trim().TrimStart("v") )
    if ($NodeVersion -lt [version]"22.12.0") {
        throw "Node.js $NodeVersion is too old. Electron dependencies require Node.js 22.12.0 or newer."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $ElectronRoot "package-lock.json"))) {
        throw "Electron package-lock.json is missing: $ElectronRoot"
    }
    Push-Location -LiteralPath $ElectronRoot
    try {
        Write-Host "Installing locked Electron dependencies..."
        & $NpmCommand.Source ci
        if ($LASTEXITCODE -ne 0) {
            throw "Electron dependency installation failed."
        }
        if ($Verify) {
            & $NpmCommand.Source run verify:static
            if ($LASTEXITCODE -ne 0) { throw "Electron static verification failed." }
            & $NodeCommand.Source --test test/*.cjs
            if ($LASTEXITCODE -ne 0) { throw "Electron Node regression tests failed." }
        }
    } finally {
        Pop-Location
    }
}

if ($Verify -and -not $SkipPython) {
    Push-Location -LiteralPath $Root
    try {
        & $VenvPython -m compileall -q app services tests
        if ($LASTEXITCODE -ne 0) { throw "Python compile check failed." }
    } finally {
        Pop-Location
    }
}

Write-Host "JARVIS setup completed. Run .\run-new-ui.ps1 to start the New Electron UI."
