"""Core-owned selection and safe status for the two approved Luna transports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from services.agents.codex_app_server import CodexAppServerAdapter
from services.agents.openai_responses import OpenAIResponsesAdapter


MANAGED_SUBSCRIPTION = "managed_subscription"
DIRECT_API = "direct_api"
AI_CONNECTION_MODES = frozenset({MANAGED_SUBSCRIPTION, DIRECT_API})


@dataclass(frozen=True)
class AiConnectionSnapshot:
    mode: str
    status: str
    detail: str
    model: str
    checked_at: str | None
    key_configured: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "status": self.status,
            "detail": self.detail,
            "model": self.model,
            "checked_at": self.checked_at,
            "key_configured": self.key_configured,
        }


class AiConnectionService:
    """Select a requested AI transport; never infer, fallback, or migrate context."""

    def __init__(
        self,
        *,
        subscription: CodexAppServerAdapter,
        direct_api: OpenAIResponsesAdapter,
    ):
        self.subscription = subscription
        self.direct_api = direct_api
        self._mode = MANAGED_SUBSCRIPTION
        # Kept only in the Core process: never persisted, logged, or returned.
        self._direct_api_key: str | None = None

    @property
    def mode(self) -> str:
        return self._mode

    def select_mode(self, mode: str) -> AiConnectionSnapshot:
        if mode not in AI_CONNECTION_MODES:
            raise ValueError("Unsupported AI connection mode.")
        if mode != self._mode and (
            mode == MANAGED_SUBSCRIPTION or self._mode == MANAGED_SUBSCRIPTION
        ):
            # A mode boundary is also an auth/permission-context boundary. Do
            # not carry a resident managed child across it; the next managed
            # request must repeat the existing verification handshake.
            self.subscription.invalidate()
        self._mode = mode
        return self.snapshot()

    def set_direct_api_key(self, api_key: str) -> AiConnectionSnapshot:
        normalized = api_key.strip()
        if not normalized:
            raise ValueError("An OpenAI API key is required.")
        self._direct_api_key = normalized
        # Saving a key is not a network verification and does not imply access.
        self.direct_api.state = self.direct_api.state.__class__("not_checked")
        return self.snapshot()

    def generate_response(
        self,
        user_message: str,
        *,
        transport_session: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if self._mode == MANAGED_SUBSCRIPTION:
            return self.subscription.generate_response(
                user_message,
                transport_session=transport_session,
            )
        # Direct API mode deliberately receives no App Server mapping and no
        # prior turn context. Switching does not transfer a conversation.
        return self.direct_api.generate_response(user_message, api_key=self._direct_api_key)

    def check_ready(self) -> AiConnectionSnapshot:
        """Check the selected transport without silently sending inference.

        Managed subscription mode has a local App Server handshake that can be
        verified without a user message. Direct API mode has no equivalent
        non-inference check in the current adapter, so it remains explicitly
        ``not_checked`` until the user sends a request.
        """
        if self._mode == MANAGED_SUBSCRIPTION:
            self.subscription.check_ready()
        return self.snapshot()

    def executor(self) -> str:
        return "codex_app_server" if self._mode == MANAGED_SUBSCRIPTION else "openai_api"

    def snapshot(self) -> AiConnectionSnapshot:
        if self._mode == MANAGED_SUBSCRIPTION:
            state = self.subscription.state
            checked_at = (
                datetime.fromtimestamp(state.checked_at, UTC).isoformat()
                if state.checked_at is not None
                else None
            )
            return AiConnectionSnapshot(
                mode=self._mode,
                status=state.status,
                detail=state.detail,
                model=self.subscription.active_model,
                checked_at=checked_at,
                key_configured=False,
            )
        state = self.direct_api.state
        checked_at = (
            datetime.fromtimestamp(state.checked_at, UTC).isoformat()
            if state.checked_at is not None
            else None
        )
        return AiConnectionSnapshot(
            mode=self._mode,
            status=state.status,
            detail=state.detail,
            model=self.direct_api.model,
            checked_at=checked_at,
            key_configured=self._direct_api_key is not None,
        )
