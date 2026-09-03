"""Local Bring Your Own Key (BYOK) brain configuration.

This module deliberately contains configuration only.  It never sends a key,
logs a key, or gives a provider permission to execute a Windows action.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PROVIDER = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
SUPPORTED_PROVIDERS = frozenset({"gemini"})
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


@dataclass(frozen=True)
class BYOKConfig:
    """The selected cloud brain, without exposing its credential."""

    provider: str
    model: str
    enabled: bool
    error: str | None = None

    @property
    def is_supported(self) -> bool:
        return self.provider in SUPPORTED_PROVIDERS

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> "BYOKConfig":
        provider = values.get("JARVIS_BRAIN_PROVIDER", DEFAULT_PROVIDER).strip().lower()
        provider = provider or DEFAULT_PROVIDER
        model = values.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
        enabled = values.get("GEMINI_ENABLED", "false").strip().lower() in _TRUE_VALUES

        if provider not in SUPPORTED_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
            return cls(
                provider=provider,
                model=model,
                enabled=False,
                error=f"Unsupported BYOK provider '{provider}'. Currently supported: {supported}.",
            )

        return cls(provider=provider, model=model, enabled=enabled)


def load_byok_config() -> BYOKConfig:
    """Load the user-local .env selection without ever returning the API key."""
    load_dotenv(ROOT_DIR / ".env")
    return BYOKConfig.from_mapping(os.environ)
