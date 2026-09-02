import os
import shutil
import subprocess
import psutil


def open_app(app: str) -> str:
    """
    Open a supported application on Windows.

    Args:
        app: Name of the application to open.

    Returns:
        Result message.
    """

    normalized = app.lower().strip()

    if normalized in [
        "vscode",
        "vs code",
        "visual studio code",
        "code",
    ]:
        command = shutil.which("code")

        if command:
            subprocess.Popen([command])
            return "Visual Studio Code opened successfully."

        vscode_path = os.path.expandvars(
            r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"
        )

        if os.path.exists(vscode_path):
            subprocess.Popen([vscode_path])
            return "Visual Studio Code opened successfully."

        return "Visual Studio Code was not found."

    return f"Application '{app}' is not supported yet."

def get_system_info() -> str:
    """
    Get the current Windows computer CPU and memory usage.

    Returns:
        Current CPU and RAM usage.
    """

    cpu = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()

    return (
        f"CPU usage: {cpu}%. "
        f"Memory usage: {memory.percent}%."
    )