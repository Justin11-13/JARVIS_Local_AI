[CmdletBinding()]
param(
    [ValidateSet("development", "internal-test")]
    [string]$Edition = "internal-test",
    [string]$PackagePath = "",
    [switch]$NoShortcut
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

if ([string]::IsNullOrWhiteSpace($PackagePath)) {
    $PackagePath = Join-Path $Root "dist\editions\$($Profile.packageName)-win32-x64"
} elseif (-not [IO.Path]::IsPathRooted($PackagePath)) {
    $PackagePath = Join-Path $Root $PackagePath
}
$PackagePath = [IO.Path]::GetFullPath($PackagePath)
$PackageExe = Join-Path $PackagePath "$($Profile.executableName).exe"
if (-not (Test-Path -LiteralPath $PackageExe)) {
    throw "The edition package or executable is missing: $PackageExe"
}

$LocalAppData = [Environment]::GetFolderPath("LocalApplicationData")
$InstallRoot = Join-Path $LocalAppData "JARVIS\$($Profile.installDirectoryName)"
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$InstallParent = [IO.Path]::GetFullPath((Join-Path $LocalAppData "JARVIS"))
if (-not $InstallRoot.StartsWith($InstallParent + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to install outside the JARVIS application directory: $InstallRoot"
}

New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
Copy-Item -Path (Join-Path $PackagePath "*") -Destination $InstallRoot -Recurse -Force
$InstalledExe = Join-Path $InstallRoot "$($Profile.executableName).exe"
if (-not (Test-Path -LiteralPath $InstalledExe)) {
    throw "The installed edition executable is missing: $InstalledExe"
}

$LauncherPath = Join-Path $InstallRoot "launch-$Edition.ps1"
$LauncherContent = @"
`$ErrorActionPreference = "Stop"
`$ExecutablePath = Join-Path `$PSScriptRoot "$($Profile.executableName).exe"
if (-not (Test-Path -LiteralPath `$ExecutablePath)) {
    throw "The installed JARVIS executable is missing: `$ExecutablePath"
}
`$Process = Start-Process -FilePath `$ExecutablePath -ArgumentList "--edition=$Edition" -WorkingDirectory `$PSScriptRoot -PassThru -Wait
exit `$Process.ExitCode
"@
Set-Content -LiteralPath $LauncherPath -Value $LauncherContent -Encoding UTF8

$ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "$($Profile.shortcutName).lnk"
if (-not $NoShortcut) {
    $PowerShellPath = Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0\powershell.exe"
    $Shell = New-Object -ComObject WScript.Shell
    if (Test-Path -LiteralPath $ShortcutPath) {
        $Existing = $Shell.CreateShortcut($ShortcutPath)
        if ($Existing.TargetPath -ne $PowerShellPath -or $Existing.Arguments -notlike "*$LauncherPath*") {
            throw "A different shortcut already exists at $ShortcutPath. It was not replaced."
        }
    }
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $PowerShellPath
    $Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$LauncherPath`""
    $Shortcut.WorkingDirectory = $InstallRoot
    $Shortcut.Description = "$($Profile.displayName)"
    $Shortcut.Save()
    Write-Host "Created shortcut: $ShortcutPath"
}

Write-Host "Installed $($Profile.displayName): $InstallRoot"
Write-Host "User data is preserved by uninstall; the Core edition/data isolation contract must be verified before internal distribution."
