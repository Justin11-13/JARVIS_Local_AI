import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
PROJECTS_FILE = ROOT_DIR / "config" / "projects.json"


def _load_projects() -> dict:
    if not PROJECTS_FILE.exists():
        return {}

    with PROJECTS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return data.get("projects", {})


def _find_project_path(project_name: str):
    projects = _load_projects()
    target = project_name.strip().lower()

    for name, project in projects.items():
        if name.lower() == target:
            return name, project.get("path")

    return None, None


def git_status(project_name: str) -> str:
    """
    Get the Git status of a registered project.

    Args:
        project_name: Name of the registered project.

    Returns:
        Current branch and changed files.
    """

    if not shutil.which("git"):
        return "Git is not installed or Git is not available in PATH."

    name, path = _find_project_path(project_name)

    if not path:
        return f"Project '{project_name}' is not registered."

    if not os.path.isdir(path):
        return f"Project path for '{name}' does not exist."

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                path,
                "status",
                "--short",
                "--branch",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return (
                f"Git status failed for '{name}': "
                f"{result.stderr.strip()}"
            )

        output = result.stdout.strip()

        if not output:
            return f"No Git status output for '{name}'."

        return (
            f"Git status for '{name}':\n"
            f"{output}"
        )

    except subprocess.TimeoutExpired:
        return f"Git status timed out for '{name}'."