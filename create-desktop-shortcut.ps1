$ErrorActionPreference = "Stop"
$PythonWindowed = Join-Path $PSScriptRoot ".venv\Scripts\pythonw.exe"
$DesktopExe = Join-Path $PSScriptRoot "desktop_ui\build\windows\x64\runner\Release\desktop_ui.exe"
$ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "JARVIS.lnk"

if (-not (Test-Path -LiteralPath $PythonWindowed)) {
    throw "JARVIS virtual environment is missing. Create .venv and install requirements.txt first."
}
if (-not (Test-Path -LiteralPath $DesktopExe)) {
    throw "Build the desktop app first: .\run-desktop.ps1 -BuildOnly -Release"
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
if ((Test-Path -LiteralPath $ShortcutPath) -and
    ($Shortcut.TargetPath -ne $PythonWindowed -or $Shortcut.Arguments -ne "-m app.desktop_launcher")) {
    throw "A different JARVIS shortcut already exists at $ShortcutPath. It was not replaced."
}
$Shortcut.TargetPath = $PythonWindowed
$Shortcut.Arguments = "-m app.desktop_launcher"
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.IconLocation = "$DesktopExe,0"
$Shortcut.Description = "Open JARVIS and start its local API"
$Shortcut.Save()
Write-Host "Created desktop shortcut: $ShortcutPath"
