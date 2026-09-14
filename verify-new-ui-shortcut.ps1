[CmdletBinding()]
param(
    [string]$ShortcutPath = "",
    [string]$ExpectedElectronRoot = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ExpectedElectronRoot)) {
    $ExpectedElectronRoot = Join-Path $PSScriptRoot "electron_motion_preview"
} elseif (-not [IO.Path]::IsPathRooted($ExpectedElectronRoot)) {
    $ExpectedElectronRoot = Join-Path $PSScriptRoot $ExpectedElectronRoot
}
$ElectronRoot = [IO.Path]::GetFullPath($ExpectedElectronRoot)
$ElectronBinary = [IO.Path]::GetFullPath((Join-Path $ElectronRoot "node_modules\electron\dist\electron.exe"))

if ([string]::IsNullOrWhiteSpace($ShortcutPath)) {
    $ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "JARVIS - New UI Preview (Test).lnk"
} elseif (-not [IO.Path]::IsPathRooted($ShortcutPath)) {
    $ShortcutPath = Join-Path $PSScriptRoot $ShortcutPath
}
$ShortcutPath = [IO.Path]::GetFullPath($ShortcutPath)

if (-not (Test-Path -LiteralPath $ShortcutPath)) {
    throw "The Electron New UI shortcut was not found: $ShortcutPath"
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$WorkingDirectory = if ($Shortcut.WorkingDirectory) {
    [IO.Path]::GetFullPath($Shortcut.WorkingDirectory)
} else {
    ""
}
$TargetPath = if ($Shortcut.TargetPath) {
    [IO.Path]::GetFullPath($Shortcut.TargetPath)
} else {
    ""
}

$workingDirectoryMatches = $WorkingDirectory.Equals($ElectronRoot, [StringComparison]::OrdinalIgnoreCase)
$targetMatchesElectron = $TargetPath.Equals($ElectronBinary, [StringComparison]::OrdinalIgnoreCase)
$targetUsesElectronWorkingDirectory = [string]::IsNullOrWhiteSpace($TargetPath) -and $Shortcut.Arguments -eq "."
$pointsToElectron = $workingDirectoryMatches -and ($targetMatchesElectron -or $targetUsesElectronWorkingDirectory)
$pointsToForbiddenLegacyUi = $Shortcut.WorkingDirectory -match "desktop_ui|Flutter"
$pointsToHtmlPrototype = $Shortcut.Arguments -match "\.html" -or $Shortcut.TargetPath -match "\.html"

if (-not $pointsToElectron -or $pointsToForbiddenLegacyUi -or $pointsToHtmlPrototype) {
    throw "The shortcut does not point to the current Electron New UI: $ShortcutPath"
}

[pscustomobject]@{
    verification = "passed"
    shortcut = $ShortcutPath
    targetPath = $Shortcut.TargetPath
    arguments = $Shortcut.Arguments
    workingDirectory = $Shortcut.WorkingDirectory
    electronRoot = $ElectronRoot
    targetMatchesElectron = $targetMatchesElectron
    targetUsesElectronWorkingDirectory = $targetUsesElectronWorkingDirectory
    forbiddenLegacyUi = $pointsToForbiddenLegacyUi
    htmlPrototype = $pointsToHtmlPrototype
} | ConvertTo-Json -Depth 4
