"""Bounded, local, persistent conversational memory for JARVIS."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from threading import Lock


_SENSITIVE_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_ -]?key|access[_ -]?token|secret|password|authorization)"
    r"\s*[:=]\s*([^\s,;]+)"
)
_BEARER_TOKEN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*")


@dataclass(frozen=True)
class MemoryTurn:
    user: str
    assistant: str
    speech: str
    created_at: str


class JarvisMemory:
    """Keep local conversation history and a smaller reasoning context."""

    def __init__(
        self,
        max_turns: int = 6,
        storage_path: Path | None = None,
        context_turns: int | None = None,
    ):
        if max_turns < 1:
            raise ValueError("max_turns must be at least 1")
        if context_turns is not None and context_turns < 1:
            raise ValueError("context_turns must be at least 1")

        self._turns: deque[MemoryTurn] = deque(maxlen=max_turns)
        self._storage_path = storage_path
        self._context_turns = min(context_turns or max_turns, max_turns)
        self._lock = Lock()
        self._load()

    @staticmethod
    def _safe_text(value: str) -> str:
        redacted = _SENSITIVE_ASSIGNMENT.sub(r"\1=[REDACTED]", value)
        return _BEARER_TOKEN.sub("Bearer [REDACTED]", redacted)

    def _load(self) -> None:
        if self._storage_path is None or not self._storage_path.is_file():
            return

        try:
            payload = json.loads(self._storage_path.read_text(encoding="utf-8"))
            turns = payload.get("turns", []) if isinstance(payload, dict) else []

            for item in turns:
                if not isinstance(item, dict):
                    continue
                user = str(item.get("user", "")).strip()
                assistant = str(item.get("assistant", "")).strip()
                if not user or not assistant:
                    continue
                self._turns.append(
                    MemoryTurn(
                        user=user,
                        assistant=assistant,
                        speech=str(item.get("speech", assistant)).strip() or assistant,
                        created_at=str(item.get("created_at", "")),
                    )
                )
        except (OSError, json.JSONDecodeError) as error:
            print(f"[Memory] Could not load conversation history: {error}")

    def _save(self) -> None:
        if self._storage_path is None:
            return

        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._storage_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(
                {"version": 1, "turns": [asdict(turn) for turn in self._turns]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary_path.replace(self._storage_path)

    def remember(self, user: str, assistant: str, speech: str = "") -> None:
        user = self._safe_text(user.strip())
        assistant = self._safe_text(assistant.strip())
        speech = self._safe_text(speech.strip()) or assistant
        if not user or not assistant:
            return

        with self._lock:
            self._turns.append(
                MemoryTurn(
                    user=user,
                    assistant=assistant,
                    speech=speech,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
            )
            try:
                self._save()
            except OSError as error:
                print(f"[Memory] Could not save conversation history: {error}")

    def history(self) -> list[dict]:
        """Return a safe snapshot for restoring the desktop conversation."""
        with self._lock:
            return [asdict(turn) for turn in self._turns]

    def gemini_contents(self) -> list[dict]:
        """Return recent turns as conversation history, never system instructions."""
        with self._lock:
            turns = list(self._turns)[-self._context_turns :]

        contents = []
        for turn in turns:
            contents.extend(
                [
                    {"role": "user", "parts": [{"text": turn.user}]},
                    {"role": "model", "parts": [{"text": turn.assistant}]},
                ]
            )
        return contents

    def clear(self) -> None:
        with self._lock:
            self._turns.clear()
            try:
                self._save()
            except OSError as error:
                print(f"[Memory] Could not clear conversation history: {error}")

    def __len__(self) -> int:
        with self._lock:
            return len(self._turns)
