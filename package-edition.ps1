[CmdletBinding()]
param(
    [ValidateSet("development", "internal-test")]
    [string]$Edition = "internal-test",
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$ElectronRoot = Join-Path $Root "electron_motion_preview"
$EditionConfigPath = Join-Path $Root "config\editions.json"
$NpxCommand = Get-Command npx -ErrorAction SilentlyContinue

if (-not $NpxCommand) {
    throw "npx was not found on PATH. Install Node.js, then run .\setup.ps1."
}
if (-not (Test-Path -LiteralPath $EditionConfigPath)) {
    throw "Edition configuration is missing: $EditionConfigPath"
}
if (-not (Test-Path -LiteralPath (Join-Path $ElectronRoot "node_modules\.bin\electron-packager.cmd"))) {
    throw "Electron packaging dependencies are missing. Run .\setup.ps1 first."
}

$EditionConfig = Get-Content -LiteralPath $EditionConfigPath -Raw | ConvertFrom-Json
$Profile = $EditionConfig.editions.$Edition
if ($null -eq $Profile) {
    throw "Unknown JARVIS edition: $Edition"
}

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $Root "dist\editions"
} elseif (-not [IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot = Join-Path $Root $OutputRoot
}
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$PreviousEdition = $env:JARVIS_EDITION
$env:JARVIS_EDITION = $Edition
Push-Location -LiteralPath $ElectronRoot
try {
    Write-Host "Building $($Profile.displayName) into $OutputRoot..."
    & $NpxCommand.Source --no-install electron-packager . $Profile.packageName `
        --platform=win32 `
        --arch=x64 `
        --executable-name=$Profile.executableName `
        --out=$OutputRoot `
        --overwrite `
        --asar
    if ($LASTEXITCODE -ne 0) {
        throw "Electron packaging failed for edition $Edition."
    }
} finally {
    Pop-Location
    $env:JARVIS_EDITION = $PreviousEdition
}

$ExpectedPackage = Join-Path $OutputRoot "$($Profile.packageName)-win32-x64"
if (-not (Test-Path -LiteralPath $ExpectedPackage)) {
    throw "Packaging completed without the expected output directory: $ExpectedPackage"
}
Write-Host "Edition package ready: $ExpectedPackage"
Write-Host "Use .\install-edition.ps1 -Edition $Edition -PackagePath `"$ExpectedPackage`" for a local test install."
