[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DestinationRoot
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$CodexPackageRoot = Join-Path $ProjectRoot "electron_motion_preview_internal_test\node_modules\@openai\codex"
$CodexPlatformRoot = Join-Path (Split-Path $CodexPackageRoot -Parent) "codex-win32-x64"
$CodexExecutable = Join-Path $CodexPlatformRoot "vendor\x86_64-pc-windows-msvc\bin\codex.exe"
$CodexManifest = Join-Path $CodexPackageRoot "package.json"
$PlatformManifest = Join-Path $CodexPlatformRoot "package.json"

if (-not (Test-Path -LiteralPath $CodexExecutable -PathType Leaf)) {
    throw "The Windows x64 Codex CLI was not found at $CodexExecutable. Run npm install in electron_motion_preview_internal_test first."
}
if (-not (Test-Path -LiteralPath $CodexManifest -PathType Leaf)) {
    throw "The Codex CLI package manifest was not found at $CodexManifest. Run npm install in electron_motion_preview_internal_test first."
}
if (-not (Test-Path -LiteralPath $PlatformManifest -PathType Leaf)) {
    throw "The Windows x64 Codex CLI package manifest was not found at $PlatformManifest. Run npm install in electron_motion_preview_internal_test first."
}

$CodexPackage = Get-Content -LiteralPath $CodexManifest -Raw | ConvertFrom-Json
$PlatformPackage = Get-Content -LiteralPath $PlatformManifest -Raw | ConvertFrom-Json
if ($CodexPackage.name -ne "@openai/codex" -or $CodexPackage.license -ne "Apache-2.0") {
    throw "The bundled Codex package identity or license metadata is unexpected."
}
if ($CodexPackage.version -ne ([string]$PlatformPackage.version -replace '-win32-x64$', '')) {
    throw "The Codex CLI package and Windows x64 package versions do not match."
}

New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
Copy-Item -LiteralPath $CodexExecutable -Destination (Join-Path $DestinationRoot "codex.exe") -Force
Copy-Item -LiteralPath $CodexManifest -Destination (Join-Path $DestinationRoot "codex-package.json") -Force
Copy-Item -LiteralPath $PlatformManifest -Destination (Join-Path $DestinationRoot "codex-platform-package.json") -Force

$Notice = @"
JARVIS bundles the Windows x64 native executable from @openai/codex $($CodexPackage.version).

License: Apache-2.0
Source: https://github.com/openai/codex
The bundled executable is used only as JARVIS's local App Server transport.
Authentication and user account data remain in the user's own Codex profile and are never bundled.
"@
Set-Content -LiteralPath (Join-Path $DestinationRoot "THIRD-PARTY-NOTICE.txt") -Value $Notice -Encoding UTF8

Write-Host "Bundled Codex CLI $($CodexPackage.version): $DestinationRoot\codex.exe"
