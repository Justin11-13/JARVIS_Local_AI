[CmdletBinding()]
param(
    [ValidateSet("development", "internal-test")]
    [string]$Edition = "internal-test"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$EditionConfigPath = Join-Path $Root "config\editions.json"
if (-not (Test-Path -LiteralPath $EditionConfigPath)) {
    throw "Edition configuration is missing: $EditionConfigPath"
}
$EditionConfig = Get-Content -LiteralPath $EditionConfigPath -Raw | ConvertFrom-Json
$Profile = $EditionConfig.editions.$Edition
if ($null -eq $Profile) {
    throw "Unknown JARVIS edition: $Edition"
}

$LocalAppData = [Environment]::GetFolderPath("LocalApplicationData")
$InstallParent = [IO.Path]::GetFullPath((Join-Path $LocalAppData "JARVIS"))
$InstallRoot = [IO.Path]::GetFullPath((Join-Path $InstallParent $Profile.installDirectoryName))
if (-not $InstallRoot.StartsWith($InstallParent + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to uninstall outside the JARVIS application directory: $InstallRoot"
}

$ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "$($Profile.shortcutName).lnk"
if (Test-Path -LiteralPath $ShortcutPath) {
    $Shell = New-Object -ComObject WScript.Shell
    $Existing = $Shell.CreateShortcut($ShortcutPath)
    $LauncherPath = Join-Path $InstallRoot "launch-$Edition.ps1"
    if ($Existing.Arguments -notlike "*$LauncherPath*") {
        throw "The shortcut does not belong to this JARVIS edition: $ShortcutPath"
    }
    Remove-Item -LiteralPath $ShortcutPath -Force
    Write-Host "Removed shortcut: $ShortcutPath"
}

if (Test-Path -LiteralPath $InstallRoot) {
    Remove-Item -LiteralPath $InstallRoot -Recurse -Force
    Write-Host "Removed application files: $InstallRoot"
} else {
    Write-Host "Application files were already absent: $InstallRoot"
}
Write-Host "User data is not removed by this script."
