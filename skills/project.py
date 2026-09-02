import json
import os
import shutil
import subprocess
from pathlib import Path

from services.project_registry import refresh_projects

ROOT_DIR = Path(__file__).resolve().parent.parent
PROJECTS_FILE = ROOT_DIR / "config" / "projects.json"


def load_projects() -> dict:
    """
    Load projects from the local project registry.

    If the registry does not exist or is invalid,
    automatically rescan configured project roots.
    """

    if not PROJECTS_FILE.exists():
        return refresh_projects()

    try:
        with PROJECTS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return data.get("projects", {})

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return refresh_projects()


def find_project(project_name: str):
    """
    Find a registered project by name.
    """

    projects = load_projects()

    target = project_name.strip().lower()

    for name, project in projects.items():
        if name.lower() == target:
            return name, project

    return None, None


def list_projects() -> str:
    """
    List all discovered projects.

    Returns:
        Registered project names and frameworks.
    """

    projects = load_projects()

    if not projects:
        return "No projects are registered."

    result = []

    for name, project in projects.items():
        framework = project.get(
            "framework",
            "Unknown",
        )

        result.append(f"{name} ({framework})")

    return "Registered projects: " + ", ".join(result)


def get_project_info(project_name: str) -> str:
    """
    Get information about a registered project.

    Args:
        project_name: Registered project name.

    Returns:
        Project information.
    """

    name, project = find_project(project_name)

    if not project:
        return f"Project '{project_name}' is not registered."

    path = project.get(
        "path",
        "",
    )

    framework = project.get(
        "framework",
        "Unknown",
    )

    description = project.get(
        "description",
        "No description",
    )

    git_enabled = project.get(
        "git",
        False,
    )

    path_exists = os.path.isdir(path)

    return (
        f"Project: {name}. "
        f"Framework: {framework}. "
        f"Git repository: {git_enabled}. "
        f"Description: {description}. "
        f"Path: {path}. "
        f"Path exists: {path_exists}."
    )


def open_project(project_name: str) -> str:
    """
    Open a registered project in Visual Studio Code.

    Args:
        project_name: Registered project name.

    Returns:
        Result of the operation.
    """

    name, project = find_project(project_name)

    if not project:
        return f"Project '{project_name}' is not registered."

    path = project.get("path")

    if not path or not os.path.isdir(path):
        return f"The configured path for '{name}' does not exist."

    code_command = shutil.which("code")

    if code_command:
        subprocess.Popen(
            [
                code_command,
                path,
            ]
        )

        return f"Project '{name}' opened in Visual Studio Code."

    vscode_path = os.path.expandvars(
        r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"
    )

    if os.path.exists(vscode_path):
        subprocess.Popen(
            [
                vscode_path,
                path,
            ]
        )

        return f"Project '{name}' opened in Visual Studio Code."

    return "Visual Studio Code was not found."


def refresh_project_registry() -> str:
    """
    Rescan configured development folders
    and refresh the JARVIS project registry.

    Returns:
        Summary of discovered projects.
    """

    projects = refresh_projects()

    if not projects:
        return "No projects were discovered."

    names = []

    for name, project in projects.items():
        framework = project.get(
            "framework",
            "Unknown",
        )

        names.append(f"{name} ({framework})")

    return (
        f"Project registry refreshed. "
        f"Discovered {len(projects)} projects: " + ", ".join(names)
    )
