import os
import shutil
import subprocess
import psutil


import os
import subprocess

import psutil

from services.app_registry import (
    find_app,
    refresh_registry,
)


def open_app(app: str) -> str:
    """
    Open an installed Windows application.

    The application is discovered automatically from the
    Windows Start Menu application registry.

    Args:
        app: Name of the application to open.

    Returns:
        Result of the operation.
    """

    match = find_app(app)

    # 第一次找不到就重新扫描
    if not match:
        refresh_registry()
        match = find_app(app)

    if not match:
        return (
            f"Application '{app}' "
            "could not be found."
        )

    shortcut = match.get(
        "shortcut"
    )

    name = match.get(
        "name",
        app,
    )

    if not shortcut:
        return (
            f"Application '{name}' "
            "does not have a launch shortcut."
        )

    if not os.path.exists(shortcut):
        return (
            f"Shortcut for '{name}' "
            "does not exist."
        )

    try:
        os.startfile(shortcut)

        return (
            f"{name} opened successfully."
        )

    except OSError as error:
        return (
            f"Failed to open '{name}': "
            f"{error}"
        )


def get_system_info() -> str:
    """
    Get current CPU and memory usage.

    Returns:
        Current CPU and RAM usage.
    """

    cpu = psutil.cpu_percent(
        interval=0.5
    )

    memory = psutil.virtual_memory()

    return (
        f"CPU usage: {cpu}%. "
        f"Memory usage: {memory.percent}%."
    )