"""Start the built Windows app and its local API without a terminal or Flutter."""

from __future__ import annotations

import ctypes
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener


ROOT = Path(__file__).resolve().parents[1]
DESKTOP_EXE = ROOT / "desktop_ui/build/windows/x64/runner/Release/desktop_ui.exe"
LOG_PATH = ROOT / "tmp/desktop-startup.log"
# Local health checks must not travel through a configured HTTP proxy.
LOCAL_HTTP = build_opener(ProxyHandler({}))


def api_ready() -> bool:
    try:
        with LOCAL_HTTP.open("http://127.0.0.1:8765/api/health", timeout=1) as response:
            health = json.load(response)
        return (
            isinstance(health, dict)
            and health.get("status") == "ready"
            and isinstance(health.get("brain"), str)
        )
    except (OSError, URLError, ValueError):
        return False


def _start_api() -> subprocess.Popen:
    """Start one loopback API process that this launcher owns."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("ab") as log:
        return subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn", "app.api:app",
                "--host", "127.0.0.1", "--port", "8765",
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )


def _wait_for_api(api: subprocess.Popen) -> None:
    deadline = time.monotonic() + 30
    while not api_ready():
        if api.poll() is not None:
            raise RuntimeError("The local API could not start. Check the startup log.")
        if time.monotonic() >= deadline:
            raise TimeoutError("The local API did not become ready within 30 seconds.")
        time.sleep(0.25)


def _stop_owned_api(api: subprocess.Popen) -> None:
    """End only the API process that this launcher created."""
    if api.poll() is not None:
        return

    api.terminate()
    try:
        api.wait(timeout=5)
    except subprocess.TimeoutExpired:
        api.kill()
        api.wait(timeout=5)


def launch() -> None:
    if not DESKTOP_EXE.is_file():
        raise FileNotFoundError(
            "The JARVIS desktop build is missing. In the JARVIS folder, run:\n"
            ".\\run-desktop.ps1 -BuildOnly -Release"
        )

    owned_api = None
    if not api_ready():
        owned_api = _start_api()
        try:
            _wait_for_api(owned_api)
        except Exception:
            _stop_owned_api(owned_api)
            raise

    try:
        desktop = subprocess.Popen(
            [str(DESKTOP_EXE)],
            cwd=DESKTOP_EXE.parent,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        desktop.wait()
    finally:
        if owned_api is not None:
            _stop_owned_api(owned_api)


def main() -> int:
    try:
        launch()
        return 0
    except Exception as error:
        # pythonw has no console: retain diagnostics and show a visible failure.
        message = str(error)
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with LOG_PATH.open("a", encoding="utf-8") as log:
                traceback.print_exc(file=log)
            message += f"\n\nStartup log:\n{LOG_PATH}"
        except OSError:
            pass
        ctypes.windll.user32.MessageBoxW(None, message, "JARVIS could not start", 0x10)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
