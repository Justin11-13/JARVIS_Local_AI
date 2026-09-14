[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SpecPath = Join-Path $PSScriptRoot "core.spec"
$BuildPath = Join-Path $PSScriptRoot "core-build"
$DistPath = Join-Path $PSScriptRoot "core-dist"
$CoreExecutable = Join-Path $DistPath "jarvis-core\jarvis-core.exe"
$CodexPrepareScript = Join-Path $PSScriptRoot "prepare-codex-cli.ps1"

if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "JARVIS build Python was not found at $PythonPath."
}
if (-not (Test-Path -LiteralPath $SpecPath -PathType Leaf)) {
    throw "PyInstaller specification was not found at $SpecPath."
}
if (-not (Test-Path -LiteralPath $CodexPrepareScript -PathType Leaf)) {
    throw "Bundled Codex CLI preparation script was not found at $CodexPrepareScript."
}

& $PythonPath -m PyInstaller --noconfirm --clean --distpath $DistPath --workpath $BuildPath $SpecPath
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE."
}
if (-not (Test-Path -LiteralPath $CoreExecutable -PathType Leaf)) {
    throw "PyInstaller completed without producing $CoreExecutable."
}

& $CodexPrepareScript -DestinationRoot (Join-Path $DistPath "jarvis-core\codex")
if ($LASTEXITCODE -ne 0) {
    throw "Bundled Codex CLI preparation failed with exit code $LASTEXITCODE."
}

Write-Host "Core package: $CoreExecutable"
