import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent

ROOTS_FILE = ROOT_DIR / "config" / "project_roots.json"
PROJECTS_FILE = ROOT_DIR / "config" / "projects.json"


PROJECT_MARKERS = {
    "composer.json": "PHP",
    "artisan": "Laravel",
    "package.json": "Node.js",
    "manage.py": "Django",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "pom.xml": "Java Maven",
    "build.gradle": "Java Gradle",
}


def load_project_roots() -> list[Path]:
    if not ROOTS_FILE.exists():
        return []

    with ROOTS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    roots = []

    for root in data.get("roots", []):
        path = Path(root).expanduser().resolve()

        if path.exists() and path.is_dir():
            roots.append(path)

    return roots


def detect_framework(project_path: Path) -> str:
    # Laravel first because Laravel also has composer.json
    if (project_path / "artisan").exists():
        return "Laravel"

    if (project_path / "manage.py").exists():
        return "Django"

    if (project_path / "pom.xml").exists():
        return "Java Maven"

    if (project_path / "build.gradle").exists():
        return "Java Gradle"

    if (project_path / "pyproject.toml").exists():
        return "Python"

    if (project_path / "requirements.txt").exists():
        return "Python"

    if (project_path / "package.json").exists():
        return "Node.js"

    if (project_path / "composer.json").exists():
        return "PHP"

    return "Unknown"


def looks_like_project(path: Path) -> bool:
    if (path / ".git").exists():
        return True

    for marker in PROJECT_MARKERS:
        if (path / marker).exists():
            return True

    return False


def scan_projects() -> dict:
    projects = {}

    ignored_dirs = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "vendor",
        "__pycache__",
        "storage",
    }

    for root in load_project_roots():
        for path in root.rglob("*"):

            if not path.is_dir():
                continue

            if any(
                part in ignored_dirs
                for part in path.parts
            ):
                continue

            if not looks_like_project(path):
                continue

            name = path.name

            projects[name] = {
                "path": str(path),
                "framework": detect_framework(path),
                "git": (path / ".git").exists(),
                "description": "",
            }

    return projects


def save_projects(projects: dict) -> None:
    data = {
        "projects": projects
    }

    PROJECTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with PROJECTS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def refresh_projects() -> dict:
    projects = scan_projects()
    save_projects(projects)

    return projects