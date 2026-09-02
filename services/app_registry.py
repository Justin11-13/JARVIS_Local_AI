import json
import os
from difflib import SequenceMatcher
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_FILE = ROOT_DIR / "config" / "apps.json"


START_MENU_LOCATIONS = [
    Path(
        os.path.expandvars(
            r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"
        )
    ),
    Path(
        os.path.expandvars(
            r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"
        )
    ),
]


def _normalize_name(name: str) -> str:
    """
    Normalize an application name for matching.
    """

    return (
        name.lower()
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )


def scan_installed_apps() -> dict:
    """
    Scan Windows Start Menu shortcuts.

    Returns:
        Dictionary containing discovered applications.
    """

    apps = {}

    for start_menu in START_MENU_LOCATIONS:

        if not start_menu.exists():
            continue

        for shortcut in start_menu.rglob("*.lnk"):

            app_name = shortcut.stem.strip()

            if not app_name:
                continue

            normalized = _normalize_name(app_name)

            apps[normalized] = {
                "name": app_name,
                "shortcut": str(shortcut),
            }

    return apps


def save_registry(apps: dict) -> None:
    """
    Save discovered applications to apps.json.
    """

    REGISTRY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "apps": apps
    }

    with REGISTRY_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def refresh_registry() -> dict:
    """
    Rescan installed applications and save the registry.

    Returns:
        Updated application registry.
    """

    apps = scan_installed_apps()

    save_registry(apps)

    return apps


def load_registry() -> dict:
    """
    Load the application registry.

    If the registry does not exist, create it automatically.
    """

    if not REGISTRY_FILE.exists():
        return refresh_registry()

    try:
        with REGISTRY_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        return data.get(
            "apps",
            {},
        )

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return refresh_registry()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(
        None,
        a,
        b,
    ).ratio()


def find_app(query: str):
    """
    Find an installed application using exact and fuzzy matching.

    Args:
        query: User-provided application name.

    Returns:
        Matching application dictionary or None.
    """

    apps = load_registry()

    normalized_query = _normalize_name(
        query
    )

    # Exact match
    if normalized_query in apps:
        return apps[normalized_query]

    # Partial match
    partial_matches = []

    for key, app in apps.items():

        if (
            normalized_query in key
            or key in normalized_query
        ):
            partial_matches.append(
                app
            )

    if len(partial_matches) == 1:
        return partial_matches[0]

    # Fuzzy match
    best_match = None
    best_score = 0.0

    for key, app in apps.items():

        score = _similarity(
            normalized_query,
            key,
        )

        if score > best_score:
            best_score = score
            best_match = app

    # Avoid opening unrelated apps
    if best_score >= 0.60:
        return best_match

    return None