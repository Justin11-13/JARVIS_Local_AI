import json
import os
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


def list_files(project_name: str, relative_path: str = ".") -> str:
    """
    List files and folders inside a registered project.

    Args:
        project_name: Name of the registered project.
        relative_path: Relative folder path inside the project.

    Returns:
        Files and folders inside the requested path.
    """

    name, project_path = _find_project_path(project_name)

    if relative_path in ["", "/", "\\"]:
      relative_path = "."

    if not project_path:
        return f"Project '{project_name}' is not registered."

    base_path = Path(project_path).resolve()
    target_path = (base_path / relative_path).resolve()

    # 防止跑出 project folder
    if base_path not in target_path.parents and target_path != base_path:
        return "Access denied: path is outside the project."

    if not target_path.exists():
        return f"Path '{relative_path}' does not exist."

    if not target_path.is_dir():
        return f"Path '{relative_path}' is not a folder."

    items = []

    for item in sorted(target_path.iterdir()):
        item_type = "DIR" if item.is_dir() else "FILE"

        items.append(
            f"[{item_type}] {item.name}"
        )

    if not items:
        return f"Folder '{relative_path}' is empty."

    return (
        f"Files in project '{name}', path '{relative_path}':\n"
        + "\n".join(items)
    )


def read_file(project_name: str, relative_path: str) -> str:
    """
    Read a text file inside a registered project.

    Args:
        project_name: Name of the registered project.
        relative_path: Relative file path inside the project.

    Returns:
        File contents.
    """

    name, project_path = _find_project_path(project_name)

    if not project_path:
        return f"Project '{project_name}' is not registered."

    base_path = Path(project_path).resolve()
    target_path = (base_path / relative_path).resolve()

    if base_path not in target_path.parents:
        return "Access denied: path is outside the project."

    if not target_path.exists():
        return f"File '{relative_path}' does not exist."

    if not target_path.is_file():
        return f"'{relative_path}' is not a file."

    # 第一版先限制大小
    max_size = 100_000

    if target_path.stat().st_size > max_size:
        return (
            f"File '{relative_path}' is too large. "
            f"Maximum readable size is {max_size} bytes."
        )

    try:
        content = target_path.read_text(
            encoding="utf-8"
        )

        return (
            f"File: {relative_path}\n\n"
            f"{content}"
        )

    except UnicodeDecodeError:
        return (
            f"File '{relative_path}' is not a supported text file."
        )


def search_files(
    project_name: str,
    keyword: str,
    relative_path: str = ".",
) -> str:
    """
    Search for a keyword in text files inside a registered project.

    Args:
        project_name: Name of the registered project.
        keyword: Text to search for.
        relative_path: Folder to search inside.

    Returns:
        Matching files and lines.
    """

    name, project_path = _find_project_path(project_name)

    if relative_path in ["", "/", "\\"]:
        relative_path = "."

    if not project_path:
        return f"Project '{project_name}' is not registered."

    base_path = Path(project_path).resolve()
    search_root = (base_path / relative_path).resolve()

    if base_path not in search_root.parents and search_root != base_path:
        return "Access denied: path is outside the project."

    if not search_root.exists():
        return f"Path '{relative_path}' does not exist."

    ignored_dirs = {
        ".git",
        ".venv",
        "node_modules",
        "vendor",
        "__pycache__",
        "storage",
    }

    allowed_extensions = {
        ".py",
        ".php",
        ".json",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".md",
        ".txt",
        ".xml",
        ".yml",
        ".yaml",
    }

    matches = []

    for root, dirs, files in os.walk(search_root):
        dirs[:] = [
            d for d in dirs
            if d not in ignored_dirs
        ]

        for file_name in files:
            file_path = Path(root) / file_name

            if file_path.suffix.lower() not in allowed_extensions:
                continue

            try:
                lines = file_path.read_text(
                    encoding="utf-8"
                ).splitlines()
            except (UnicodeDecodeError, OSError):
                continue

            for line_number, line in enumerate(lines, start=1):
                if keyword.lower() in line.lower():
                    relative = file_path.relative_to(base_path)

                    matches.append(
                        f"{relative}:{line_number}: {line.strip()}"
                    )

                    if len(matches) >= 50:
                        break

            if len(matches) >= 50:
                break

        if len(matches) >= 50:
            break

    if not matches:
        return (
            f"No matches found for '{keyword}' "
            f"in project '{name}'."
        )

    return (
        f"Search results for '{keyword}' in '{name}':\n"
        + "\n".join(matches)
    )