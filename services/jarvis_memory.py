"""Small local, in-session conversational memory for JARVIS."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryTurn:
    user: str
    assistant: str


class JarvisMemory:
    """Keep a bounded local transcript and format it for the selected brain."""

    def __init__(self, max_turns: int = 6):
        if max_turns < 1:
            raise ValueError("max_turns must be at least 1")
        self._turns: deque[MemoryTurn] = deque(maxlen=max_turns)

    def remember(self, user: str, assistant: str) -> None:
        user = user.strip()
        assistant = assistant.strip()
        if user and assistant:
            self._turns.append(MemoryTurn(user=user, assistant=assistant))

    def gemini_contents(self) -> list[dict]:
        """Return previous turns as conversation history, never as system instructions."""
        contents = []
        for turn in self._turns:
            contents.extend(
                [
                    {"role": "user", "parts": [{"text": turn.user}]},
                    {"role": "model", "parts": [{"text": turn.assistant}]},
                ]
            )
        return contents

    def clear(self) -> None:
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)
