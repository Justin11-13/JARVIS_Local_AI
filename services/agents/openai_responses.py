"""Direct OpenAI Responses API adapter for the exact Luna model.

This adapter has no JARVIS tool authority and does not persist a conversation.
Core chooses it explicitly; it never falls back to another provider or model.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from time import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from services.agents.luna_model import DEFAULT_LUNA_MODEL
from services.jarvis_system_prompt import JARVIS_SYSTEM_PROMPT


RESPONSES_URL = "https://api.openai.com/v1/responses"


@dataclass(frozen=True)
class DirectApiState:
    """Last direct-API observation, intentionally excluding the credential."""

    status: str
    detail: str = ""
    checked_at: float | None = None


class OpenAIResponsesAdapter:
    """Perform one text-only Responses request with an explicitly supplied key."""

    def __init__(self, *, model: str = DEFAULT_LUNA_MODEL, timeout: int = 60):
        self.model = model
        self.timeout = timeout
        self.state = DirectApiState("unconfigured")

    @property
    def provider(self) -> str:
        return "openai_api"

    def generate_response(self, user_message: str, *, api_key: str | None) -> dict[str, Any]:
        """Call the exact model without tools, stored conversation state, or fallback."""
        if not api_key:
            message = "Direct API is not configured. Enter an OpenAI API key in JARVIS Settings first."
            self.state = DirectApiState("unconfigured", message)
            return self._error("unconfigured", message)

        payload = {
            "model": self.model,
            "instructions": JARVIS_SYSTEM_PROMPT,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": user_message}]}],
            # Direct API mode intentionally has no server-side conversation or
            # tool state. The desktop's local transcript is not sent as context.
            "store": False,
        }
        request = Request(
            RESPONSES_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as error:
            status, message = self._http_failure(error)
            self.state = DirectApiState(status, message, time())
            return self._error(status, message)
        except (URLError, TimeoutError) as error:
            message = "OpenAI Direct API could not be reached. Check the network connection and retry."
            self.state = DirectApiState("network_error", message, time())
            return self._error("network_error", message)
        except OSError:
            message = "OpenAI Direct API could not be reached. Check the network connection and retry."
            self.state = DirectApiState("network_error", message, time())
            return self._error("network_error", message)

        try:
            response = json.loads(raw.decode("utf-8"))
            text = self._output_text(response)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
            message = "OpenAI Direct API returned an invalid text response."
            self.state = DirectApiState("service_error", message, time())
            return self._error("service_error", message)

        self.state = DirectApiState("available", "Direct API responded.", time())
        return {
            "success": True,
            "status": "completed",
            "result": text,
            "error": "",
            "provider": self.provider,
            "model": self.model,
            "tool_calls": [],
        }

    @staticmethod
    def _output_text(response: Any) -> str:
        if not isinstance(response, dict):
            raise ValueError("Response must be an object.")
        output = response.get("output")
        if not isinstance(output, list):
            raise ValueError("Response has no output list.")
        parts = [
            item.get("text", "")
            for message in output
            if isinstance(message, dict)
            and isinstance(message.get("content"), list)
            for item in message["content"]
            if isinstance(item, dict) and item.get("type") == "output_text"
        ]
        text = "\n".join(part for part in parts if isinstance(part, str)).strip()
        if not text:
            raise ValueError("Response contained no output text.")
        return text

    def _http_failure(self, error: HTTPError) -> tuple[str, str]:
        if error.code == 401:
            return "authentication_failed", "OpenAI Direct API rejected the configured key."
        if error.code in {403, 404}:
            return "model_unavailable", f"The Direct API account cannot access the required Luna model '{self.model}'."
        if error.code == 429:
            return "rate_limited", "OpenAI Direct API rate limit or quota was reached."
        return "service_error", f"OpenAI Direct API returned HTTP {error.code}."

    def _error(self, status: str, message: str) -> dict[str, Any]:
        return {
            "success": False,
            "status": status,
            "result": "",
            "error": message,
            "provider": self.provider,
            "model": self.model,
            "tool_calls": [],
        }
