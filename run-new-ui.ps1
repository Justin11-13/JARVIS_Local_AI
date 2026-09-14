[CmdletBinding()]
param(
    [ValidateSet("development", "internal-test")]
    [string]$Edition = "development",
    [switch]$Verify
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$ElectronRoot = Join-Path $Root "electron_motion_preview"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$ElectronBinary = Join-Path $ElectronRoot "node_modules\electron\dist\electron.exe"
$EditionConfigPath = Join-Path $Root "config\editions.json"
$NpmCommand = Get-Command npm -ErrorAction SilentlyContinue

if (-not $NpmCommand) {
    throw "npm was not found on PATH. Install Node.js, then run .\setup.ps1."
}
if (-not (Test-Path -LiteralPath $ElectronBinary)) {
    throw "Electron dependencies are missing. Run .\setup.ps1 first."
}
if (-not (Test-Path -LiteralPath $EditionConfigPath)) {
    throw "Edition configuration is missing: $EditionConfigPath"
}
$EditionConfig = Get-Content -LiteralPath $EditionConfigPath -Raw | ConvertFrom-Json
$EditionProfile = $EditionConfig.editions.$Edition
if ($null -eq $EditionProfile) {
    throw "Unknown JARVIS edition: $Edition"
}
if (-not $Verify -and -not (Test-Path -LiteralPath $VenvPython)) {
    throw "The JARVIS Python environment is missing. Run .\setup.ps1 first."
}

$PreviousEdition = $env:JARVIS_EDITION
$env:JARVIS_EDITION = $Edition
Push-Location -LiteralPath $ElectronRoot
$ExitCode = 1
try {
    if ($Verify) {
        & $NpmCommand.Source run verify -- "--edition=$Edition"
    } else {
        & $NpmCommand.Source start -- "--edition=$Edition"
    }
    $ExitCode = $LASTEXITCODE
} finally {
    Pop-Location
    $env:JARVIS_EDITION = $PreviousEdition
}
exit $ExitCode
