"""Fish Audio cloud TTS, used only after the user selects that provider."""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class FishSpeechError(RuntimeError):
    """A safe, user-facing Fish Audio configuration or request failure."""


class FishSpeechService:
    _endpoint = "https://api.fish.audio/v1/tts"

    def synthesize(self, text: str) -> bytes:
        api_key = os.environ.get("FISH_API_KEY", "").strip()
        if not api_key:
            raise FishSpeechError(
                "Fish Audio is not configured. Add FISH_API_KEY to the local .env file, then restart JARVIS Core."
            )

        payload: dict[str, object] = {
            "text": text,
            "format": "wav",
            "sample_rate": 44_100,
            "normalize": True,
            "latency": "normal",
        }
        reference_id = os.environ.get("FISH_REFERENCE_ID", "").strip()
        if reference_id:
            payload["reference_id"] = reference_id

        request = Request(
            self._endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "model": "s2-pro",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                audio = response.read()
        except HTTPError as error:
            if error.code == 401:
                message = "Fish Audio rejected the configured API key."
            elif error.code == 402:
                message = "Fish Audio has no available credits for this request."
            else:
                message = f"Fish Audio rejected this speech request ({error.code})."
            raise FishSpeechError(message) from error
        except URLError as error:
            raise FishSpeechError(
                "Fish Audio could not be reached. Check the network connection and try again."
            ) from error

        if not audio:
            raise FishSpeechError("Fish Audio returned no audio.")
        return audio
