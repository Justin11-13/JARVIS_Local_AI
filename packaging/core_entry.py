"""Frozen JARVIS Core entry point for the Internal Test Windows package."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def resource_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parents[1]


def app_data_root() -> Path:
    configured = os.environ.get("JARVIS_APP_DATA_DIR", "").strip()
    if configured:
        return Path(configured)
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    local_root = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return local_root / "JARVIS" / "InternalTest"


def configure_runtime() -> tuple[Path, Path]:
    resources = resource_root()
    data_root = app_data_root()
    config_root = data_root / "config"

    os.environ["JARVIS_PACKAGED"] = "1"
    os.environ.setdefault("JARVIS_RESOURCE_ROOT", str(resources))
    os.environ.setdefault("JARVIS_APP_DATA_DIR", str(data_root))
    os.environ.setdefault("JARVIS_CONFIG_DIR", str(config_root))
    os.environ.setdefault("HF_HOME", str(resources / "huggingface"))
    os.environ.setdefault("HF_HUB_CACHE", str(resources / "huggingface" / "hub"))

    config_root.mkdir(parents=True, exist_ok=True)
    (data_root / "data").mkdir(parents=True, exist_ok=True)
    (data_root / "logs").mkdir(parents=True, exist_ok=True)
    os.chdir(data_root)
    return resources, data_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="JARVIS Core")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser.parse_args()


def main() -> None:
    configure_runtime()
    args = parse_args()

    import uvicorn

    from app.api import app

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
