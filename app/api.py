"""Local-only API for the Flutter desktop client.

The API reuses the same tool registry and TaskRouter as the CLI. It binds to
loopback only when started through the documented command, so the desktop UI
cannot turn JARVIS tools into a network service.
"""

from __future__ import annotations

import inspect
import json
import re
from threading import Lock, Timer
from time import monotonic
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from app.main import (
    AVAILABLE_TOOLS,
    ai_connection,
    jarvis_memory,
    ai_unavailable_reply,
    luna,
    task_manager,
    task_router,
)
from services.native_intent import (
    parse_native_intent_proposal,
    resolve_native_intent,
    should_request_native_intent_proposal,
)
from services.rag.knowledge_router import route_knowledge
from services.rag.source_registry import load_obsidian_vaults, remove_obsidian_vault, save_obsidian_vault
from services.system_telemetry import read_system_telemetry
from services.fish_speech_service import FishSpeechError, FishSpeechService
from services.windows_speech_service import WindowsSpeechError, WindowsSpeechService
from skills.project import load_projects


app = FastAPI(
    title="JARVIS Local API",
    version="0.1.0",
)

# The chat endpoint resolves registered native intents before it delegates a
# remaining request to the configured reasoning backend.
ROUTING_MODE = "native_tools_first"


# ---------------------------------------------------------------------------
# RAG initialization
# ---------------------------------------------------------------------------

@app.on_event("startup")
def initialize_rag_index() -> None:
    """
    Prepare the local knowledge base after the API is already able to start.

    A short delay lets the desktop UI connect without waiting for the heavy
    embedding runtime. RAG requests still wait safely for this same one-time
    preparation when they arrive before the background warm-up finishes.
    """
    warmup = Timer(1.0, _warm_rag_service)
    warmup.daemon = True
    warmup.start()


@app.on_event("shutdown")
def shutdown_ai_transport() -> None:
    """Release only the JARVIS-owned managed Luna child on Core shutdown."""
    close = getattr(luna, "close", None)
    if callable(close):
        close()


_conversation_lock = Lock()

_rag_lock = Lock()
_rag_service: Any | None = None
_rag_index_ready = False


def _get_rag_service() -> Any:
    """
    Synchronize the index, then initialize and reuse the RAG service.

    Indexing and retrieval share one lock and one embedding model, preventing
    duplicate cold loads when a request overlaps background preparation.
    """
    global _rag_index_ready, _rag_service

    if _rag_service is not None and _rag_index_ready:
        return _rag_service

    with _rag_lock:
        if not _rag_index_ready:
            try:
                from services.rag.indexer import update_index

                update_index()
            except Exception as error:
                print(
                    f"[RAG] Knowledge index update failed: {error}"
                )
                raise
            else:
                _rag_index_ready = True

        if _rag_service is None:
            from services.rag.rag_service import RAGService

            _rag_service = RAGService()

    return _rag_service


def _warm_rag_service() -> None:
    """Warm RAG in the background without blocking desktop startup."""
    try:
        _get_rag_service()
        print("[RAG] Background warm-up completed.")
    except Exception as error:
        print(f"[RAG] Background warm-up failed: {error}")


# ---------------------------------------------------------------------------
# Fast local replies
# ---------------------------------------------------------------------------

FAST_REPLIES = {
    "你好": "你好！我是 JARVIS。有什么可以帮你？",
    "您好": "你好！我是 JARVIS。有什么可以帮你？",
    "hi": "Hi! I am JARVIS. How can I help?",
    "hello": "Hello! I am JARVIS. How can I help?",
    "你能做什么": (
        "我可以检查 CPU、内存和 GPU 状态，控制音量与媒体播放，打开已安装的应用，"
        "查看已注册项目、Git 状态和项目文件，并在敏感系统操作前请求确认。"
    ),
    "你可以做什么": (
        "我可以检查 CPU、内存和 GPU 状态，控制音量与媒体播放，打开已安装的应用，"
        "查看已注册项目、Git 状态和项目文件，并在敏感系统操作前请求确认。"
    ),
    "what can you do": (
        "I can check CPU, memory, and GPU status; control volume and media playback; "
        "open installed apps; inspect registered projects, Git status, and project files; "
        "and request confirmation before sensitive system actions."
    ),
}

FAST_SPEECH_REPLIES = {
    "你好": "Hello! I am JARVIS. How can I help?",
    "您好": "Hello! I am JARVIS. How can I help?",
    "你能做什么": (
        "I can check CPU, memory, and GPU status, control volume and media playback, "
        "open installed apps, inspect registered projects, Git status, and project files, "
        "and request confirmation before sensitive system actions."
    ),
    "你可以做什么": (
        "I can check CPU, memory, and GPU status, control volume and media playback, "
        "open installed apps, inspect registered projects, Git status, and project files, "
        "and request confirmation before sensitive system actions."
    ),
}


def _normalized_fast_reply(message: str) -> str:
    return " ".join(message.strip().lower().split()).rstrip("?!？！。")


def fast_reply(message: str) -> str | None:
    """
    Return a local reply only for an exact, non-actionable greeting.
    """
    return FAST_REPLIES.get(_normalized_fast_reply(message))


def fast_speech_reply(message: str) -> str | None:
    """Return the English narration for a fixed local reply when available."""
    return FAST_SPEECH_REPLIES.get(_normalized_fast_reply(message))


# ---------------------------------------------------------------------------
# API request models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=12_000,
    )
    conversation_id: str = Field(
        default="primary",
        min_length=1,
        max_length=64,
        pattern=r"^(primary|jarvis-[0-9a-f-]{36})$",
    )


class AiModeRequest(BaseModel):
    mode: str = Field(min_length=1, max_length=40)


class DirectApiKeyRequest(BaseModel):
    # This value is accepted only over loopback and retained in the running
    # Core process. It is never included in a response, health data, or logs.
    api_key: str = Field(min_length=1, max_length=500)
    conversation_id: str = Field(
        default="primary",
        min_length=1,
        max_length=64,
        pattern=r"^(primary|jarvis-[0-9a-f-]{36})$",
    )


class SpeechRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=12_000,
    )


class ToolRequest(BaseModel):
    project_name: str = Field(
        min_length=1,
        max_length=200,
    )

    relative_path: str = Field(
        default=".",
        max_length=500,
    )

    keyword: str = Field(
        default="",
        max_length=500,
    )


class ObsidianVaultRequest(BaseModel):
    vault_id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    path: str = Field(min_length=1, max_length=1000)
    default_access: str = Field(default="excluded", max_length=20)


class ObsidianOpenRequest(BaseModel):
    vault_id: str = Field(min_length=1, max_length=80)
    relative_path: str = Field(min_length=1, max_length=500)


# ---------------------------------------------------------------------------
# Native tool execution
# ---------------------------------------------------------------------------

def _serialize_tool_result(
    result: Any,
) -> dict[str, Any]:
    if isinstance(result, dict):
        return {
            "success": result.get("success"),
            "status": result.get("status"),
            "risk": result.get("risk"),
            "result": result.get("result"),
            "message": result.get("message"),
            "error": result.get("error"),
            "action": result.get("action"),
            "executor": result.get("executor"),
            "data_scope": result.get("data_scope"),
            "requires_confirmation": result.get(
                "requires_confirmation"
            ),
            "confirmation_count": result.get(
                "confirmation_count"
            ),
            "confirmation_step": result.get(
                "confirmation_step"
            ),
            "tool_name": result.get("tool_name"),
            "proposal_confidence": result.get("proposal_confidence"),
            "task": result.get("task"),
            "audit_summary": result.get(
                "audit_summary"
            ),
            "submission_preview": result.get(
                "submission_preview"
            ),
            "tool_calls": result.get(
                "tool_calls"
            ),
        }

    return {
        "success": False,
        "status": "failed",
        "result": "",
        "error": "Core received an invalid tool result.",
    }


def _execute_native_tool(
    function_name: str,
    arguments: dict[str, Any],
    user_input: str,
    *,
    force_confirmation: bool = False,
) -> dict[str, Any]:
    router_kwargs = {
        "function_name": function_name,
        "arguments": arguments,
        "user_input": user_input,
        "available_tools": AVAILABLE_TOOLS,
    }
    if force_confirmation:
        router_kwargs["force_confirmation"] = True
    result = task_router.execute_tool(**router_kwargs)

    serialized = _serialize_tool_result(
        result
    )

    return serialized


# Fish Audio output is a user-selected cloud request only. It is deliberately
# outside TaskRouter: speech synthesis cannot perform tools or receive authority.
_fish_speech_service = FishSpeechService()
_windows_speech_service = WindowsSpeechService()


@app.post("/api/speech")
def synthesize_speech(request: SpeechRequest) -> Response:
    try:
        audio = _fish_speech_service.synthesize(request.text.strip())
    except FishSpeechError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return Response(
        content=audio,
        media_type="audio/wav",
        headers={"Cache-Control": "no-store"},
    )


@app.post("/api/system-speech", status_code=204)
def speak_with_windows_voice(request: SpeechRequest) -> Response:
    try:
        _windows_speech_service.speak(request.text.strip())
    except WindowsSpeechError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return Response(status_code=204)


@app.get("/api/system-speech/settings")
def windows_speech_settings() -> dict[str, Any]:
    try:
        return _windows_speech_service.settings()
    except WindowsSpeechError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/system-speech/stop", status_code=204)
def stop_windows_voice() -> Response:
    _windows_speech_service.stop()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Gemini local tool boundary
# ---------------------------------------------------------------------------

GEMINI_LOCAL_TOOL_SCHEMAS = {
    "open_app": (
        {"app"},
        set(),
    ),
    "get_system_info": (
        set(),
        set(),
    ),
    "list_projects": (
        set(),
        set(),
    ),
    "get_project_info": (
        {"project_name"},
        set(),
    ),
    "open_project": (
        {"project_name"},
        set(),
    ),
    "git_status": (
        {"project_name"},
        set(),
    ),
    "list_files": (
        {"project_name"},
        {"relative_path"},
    ),
    "read_file": (
        {
            "project_name",
            "relative_path",
        },
        set(),
    ),
    "search_files": (
        {
            "project_name",
            "keyword",
        },
        {"relative_path"},
    ),
    "refresh_project_registry": (
        set(),
        set(),
    ),
    "get_battery_status": (
        set(),
        set(),
    ),
    "get_network_status": (
        set(),
        set(),
    ),
    "list_running_processes": (
        set(),
        set(),
    ),
    "adjust_volume": (
        {"direction"},
        {"amount"},
    ),
    "toggle_mute": (
        set(),
        set(),
    ),
    "media_control": (
        {"action"},
        set(),
    ),
    "open_known_folder": (
        {"folder"},
        set(),
    ),
    "open_windows_setting": (
        {"setting"},
        set(),
    ),
    "lock_computer": (
        set(),
        set(),
    ),
    "shutdown_computer": (
        set(),
        set(),
    ),
    "restart_computer": (
        set(),
        set(),
    ),
    "sleep_computer": (
        set(),
        set(),
    ),
    "search_obsidian_notes": (
        {"keyword"},
        {"vault_id"},
    ),
    "open_obsidian_note": (
        {"vault_id", "relative_path"},
        set(),
    ),
    "create_obsidian_note": (
        {"vault_id", "relative_path", "content"},
        set(),
    ),
    "append_obsidian_note": (
        {"vault_id", "relative_path", "content"},
        set(),
    ),
    "update_obsidian_note": (
        {"vault_id", "relative_path", "expected_text", "replacement_text"},
        set(),
    ),
}


def _native_intent_catalog() -> list[dict[str, Any]]:
    """Describe the registered allowlist without exposing implementation data."""
    catalog: list[dict[str, Any]] = []
    for function_name, (required, optional) in GEMINI_LOCAL_TOOL_SCHEMAS.items():
        if function_name not in AVAILABLE_TOOLS:
            continue
        function = AVAILABLE_TOOLS[function_name]
        doc = inspect.getdoc(function) or ""
        description = next(
            (line.strip() for line in doc.splitlines() if line.strip()),
            function_name.replace("_", " "),
        )
        catalog.append(
            {
                "name": function_name,
                "description": description[:160],
                "required_arguments": sorted(required),
                "optional_arguments": sorted(optional),
            }
        )
    return catalog


SENSITIVE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "service-account.json",
}


SENSITIVE_FILE_SUFFIXES = {
    ".pem",
    ".key",
    ".pfx",
    ".p12",
}


SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?im)\b("
    r"api[_-]?key|"
    r"access[_-]?token|"
    r"auth[_-]?token|"
    r"password|"
    r"secret|"
    r"private[_-]?key|"
    r"authorization"
    r")\b"
    r"\s*([:=])\s*([^\s,;]+)"
)


def _validate_gemini_tool_arguments(
    function_name: str,
    arguments: dict[str, Any],
    *,
    source: str = "Gemini",
) -> tuple[dict[str, str] | None, dict[str, Any] | None]:
    """Apply the one shared schema/path boundary to model tool candidates."""
    schema = GEMINI_LOCAL_TOOL_SCHEMAS.get(function_name)
    if schema is None:
        return None, {
            "success": False,
            "status": "routing_blocked",
            "result": "",
            "error": f"{source} requested unavailable tool '{function_name}'.",
        }

    if not isinstance(arguments, dict):
        return None, {
            "success": False,
            "status": "validation_failed",
            "result": "",
            "error": f"{source} supplied invalid arguments for '{function_name}'.",
        }

    required_keys, optional_keys = schema
    supplied_keys = set(arguments)
    valid_keys = required_keys | optional_keys
    if not required_keys.issubset(supplied_keys) or not supplied_keys.issubset(valid_keys):
        return None, {
            "success": False,
            "status": "validation_failed",
            "result": "",
            "error": f"{source} supplied invalid arguments for '{function_name}'.",
        }

    normalized_arguments: dict[str, str] = {}
    for key, value in arguments.items():
        maximum_length = (
            12_000
            if key in {"content", "expected_text", "replacement_text"}
            else 500
            if key in {"relative_path", "keyword"}
            else 200
        )
        if (
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(value, str)
            or not value.strip()
            or len(value) > maximum_length
        ):
            return None, {
                "success": False,
                "status": "validation_failed",
                "result": "",
                "error": f"{source} supplied an invalid '{key}' argument.",
            }
        normalized_arguments[key] = value.strip()

    allowed_values = {
        "adjust_volume": {
            "direction": {"up", "down"},
            "amount": {"small", "medium", "large"},
        },
        "media_control": {
            "action": {"play_pause", "next", "previous", "stop"},
        },
        "open_known_folder": {
            "folder": {"desktop", "documents", "downloads", "pictures", "music", "videos"},
        },
        "open_windows_setting": {
            "setting": {"display", "sound", "wifi", "bluetooth", "power", "notifications", "privacy"},
        },
    }
    for key, valid_values in allowed_values.get(function_name, {}).items():
        if key in normalized_arguments and normalized_arguments[key].lower() not in valid_values:
            return None, {
                "success": False,
                "status": "validation_failed",
                "result": "",
                "error": f"{source} supplied an unsupported '{key}' value for '{function_name}'.",
            }

    if function_name == "adjust_volume" and "amount" not in normalized_arguments:
        normalized_arguments["amount"] = "medium"

    if function_name == "read_file" and _is_sensitive_file(normalized_arguments["relative_path"]):
        return None, {
            "success": False,
            "status": "routing_blocked",
            "result": "",
            "error": (
                "JARVIS does not send credential or secret files to Gemini."
                if source == "Gemini"
                else "JARVIS does not send credential or secret files to model transports."
            ),
        }

    return normalized_arguments, None


def _execute_gemini_safe_tool(
    function_name: str,
    arguments: dict[str, Any],
    user_input: str,
) -> dict[str, Any]:
    """Validate Gemini's local-tool proposal before native execution."""
    normalized_arguments, validation_error = _validate_gemini_tool_arguments(
        function_name,
        arguments,
        source="Gemini",
    )
    if validation_error:
        return validation_error

    result = _execute_native_tool(
        function_name,
        normalized_arguments or {},
        user_input,
    )
    return _redact_gemini_tool_result(result)


def _is_sensitive_file(
    relative_path: str,
) -> bool:
    file_name = (
        relative_path
        .replace("\\", "/")
        .rsplit("/", 1)[-1]
        .lower()
    )

    return (
        file_name
        in SENSITIVE_FILE_NAMES
        or any(
            file_name.endswith(suffix)
            for suffix
            in SENSITIVE_FILE_SUFFIXES
        )
    )


def _redact_gemini_tool_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Keep common credential values out of cloud-bound
    Gemini tool responses.
    """

    safe_result = dict(result)

    value = safe_result.get(
        "result"
    )

    if isinstance(value, str):
        safe_result["result"] = (
            SENSITIVE_VALUE_PATTERN.sub(
                r"\1\2 [REDACTED]",
                value,
            )
        )

    return safe_result


# ---------------------------------------------------------------------------
# Chat/session helpers
# ---------------------------------------------------------------------------

DISPLAY_MARKER = "[DISPLAY]"
VOICE_MARKER = "[VOICE_EN]"


def plain_display_text(value: str) -> str:
    """Normalize line endings without destroying the display Markdown structure."""
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _plain_speech_text(value: str) -> str:
    """Remove display-only Markdown markers when no dedicated narration exists."""
    parts = value.split("```")

    for index in range(0, len(parts), 2):
        prose = parts[index]
        prose = re.sub(r"(?m)^\s*#{1,6}\s+", "", prose)
        prose = re.sub(r"(?m)^\s*[-+*]\s+", "• ", prose)
        prose = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", prose)
        prose = re.sub(r"_{1,3}(.+?)_{1,3}", r"\1", prose)
        parts[index] = prose

    return "```".join(parts)


def split_reply_for_speech(reply: str) -> tuple[str, str]:
    """Keep the user's display language separate from an English narration."""
    display, separator, narration = reply.partition(VOICE_MARKER)
    if not separator:
        cleaned_reply = plain_display_text(reply.strip())
        return cleaned_reply, _plain_speech_text(cleaned_reply)
    if display.lstrip().startswith(DISPLAY_MARKER):
        display = display.lstrip()[len(DISPLAY_MARKER) :]
    cleaned_display = plain_display_text(display.strip())
    cleaned_narration = narration.strip()
    return cleaned_display, cleaned_narration or _plain_speech_text(cleaned_display)


def _chat_response(
    user_input: str,
    reply: str,
    tool_results: list[dict[str, Any]],
    speech_reply: str | None = None,
    rag_result: dict[str, Any] | None = None,
    timings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Return the API response and retain the completed
    turn in local session memory.
    """

    display_reply, embedded_speech_reply = split_reply_for_speech(reply)
    narration = (speech_reply or embedded_speech_reply).strip()

    jarvis_memory.remember(
        user_input,
        display_reply,
        narration,
    )

    response = {
        "reply": display_reply,
        "speech": narration,
        "tool_results": tool_results,
    }
    if isinstance(timings, dict):
        response["timings"] = timings
    if rag_result:
        response.update({
            "used_rag": bool(rag_result.get("used_rag")),
            "knowledge_domains": rag_result.get("domains", []),
            "citations": rag_result.get("citations", []),
        })
    return response


def _generate_ai_response(
    user_input: str,
    conversation_id: str,
    *,
    request_native_intent_proposal: bool = False,
) -> dict[str, Any]:
    """Keep transport metadata local and optionally request one Luna proposal marker."""
    managed_subscription = ai_connection.mode == "managed_subscription"
    if managed_subscription:
        # The service owns the selected mode; the existing managed adapter owns
        # its private session protocol and state.
        adapter_kwargs: dict[str, Any] = {
            "transport_session": jarvis_memory.transport_session(conversation_id),
        }
        if request_native_intent_proposal:
            adapter_kwargs["intent_catalog"] = _native_intent_catalog()
        result = luna.generate_response(
            user_input,
            **adapter_kwargs,
        )
    else:
        result = ai_connection.generate_response(user_input, transport_session=None)

    if (
        isinstance(result, dict)
        and result.get("success") is True
        and isinstance(result.get("result"), str)
    ):
        cleaned_reply, proposal = parse_native_intent_proposal(
            result["result"],
            {
                entry["name"]
                for entry in _native_intent_catalog()
                if isinstance(entry, dict) and isinstance(entry.get("name"), str)
            },
        )
        result["result"] = cleaned_reply
        if request_native_intent_proposal and proposal is not None:
            result["native_intent_proposal"] = proposal.to_dict()
    transport_session = result.pop("transport_session", None)
    transport_timings = result.get("timings")
    if managed_subscription and result.get("success") is True:
        if not isinstance(transport_session, dict):
            failed_result = {
                "success": False,
                "status": "session_persistence_failed",
                "result": "",
                "error": "Luna completed but did not return a JARVIS-owned transport session mapping.",
                "tool_calls": [],
            }
            if isinstance(transport_timings, dict):
                failed_result["timings"] = transport_timings
            return failed_result
        try:
            jarvis_memory.remember_transport_session(conversation_id, transport_session)
        except ValueError:
            failed_result = {
                "success": False,
                "status": "session_persistence_failed",
                "result": "",
                "error": "JARVIS could not persist the owned Luna session mapping.",
                "tool_calls": [],
            }
            if isinstance(transport_timings, dict):
                failed_result["timings"] = transport_timings
            return failed_result
    return result


def _execute_native_intent_proposal(
    proposal_data: Any,
    user_input: str,
) -> dict[str, Any]:
    """Validate and queue one Luna candidate through the normal Core boundary."""
    if not isinstance(proposal_data, dict):
        return {
            "success": False,
            "status": "validation_failed",
            "result": "",
            "error": "Luna returned an invalid native-intent proposal; no local action was executed.",
        }

    function_name = proposal_data.get("function_name")
    arguments = proposal_data.get("arguments")
    confidence = proposal_data.get("confidence")
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError, OverflowError):
        confidence_value = -1.0
    if (
        not isinstance(function_name, str)
        or not isinstance(arguments, dict)
        or isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence_value <= 1
        or confidence_value < 0.75
    ):
        return {
            "success": False,
            "status": "validation_failed",
            "result": "",
            "error": "Luna returned an invalid native-intent proposal; no local action was executed.",
        }

    normalized_arguments, validation_error = _validate_gemini_tool_arguments(
        function_name,
        arguments,
        source="Luna",
    )
    if validation_error:
        # The shared validator intentionally returns no model-supplied values;
        # only its bounded reason crosses the API boundary.
        return validation_error

    result = _execute_native_tool(
        function_name,
        normalized_arguments or {},
        user_input,
    )
    result.setdefault("tool_name", function_name)
    if result.get("status") == "awaiting_confirmation":
        result["proposal_confidence"] = round(confidence_value, 3)
    return result


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health() -> dict[str, Any]:
    """
    Report API availability without contacting
    a reasoning backend or tool.
    """

    return {
        # Core status is only the local API/control-plane status. It does not
        # claim that a cloud account, key, model, or quota is usable.
        "core": {"status": "ready"},
        "ai": ai_connection.snapshot().to_dict(),
        "routing_mode": ROUTING_MODE,
        "task_count": len(
            task_manager.list_tasks()
        ),
    }


@app.get("/api/tasks")
def tasks() -> dict[str, Any]:
    """Return the current in-process task lifecycle records for local inspection."""

    return {"tasks": task_manager.list_tasks()}


def _ensure_ai_mode_can_change() -> None:
    if task_router.pending_action_request is not None:
        raise HTTPException(
            status_code=409,
            detail="Resolve the pending JARVIS confirmation before changing AI connection mode.",
        )


@app.post("/api/settings/ai/mode")
def set_ai_mode(request: AiModeRequest) -> dict[str, Any]:
    """Select the next explicit AI transport without moving any conversation state."""
    with _conversation_lock:
        _ensure_ai_mode_can_change()
        try:
            snapshot = ai_connection.select_mode(request.mode)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
    return {"ai": snapshot.to_dict()}


@app.post("/api/settings/ai/check")
def check_ai_connection() -> dict[str, Any]:
    """Verify the selected AI transport without submitting a user turn.

    Managed subscription mode performs only the existing App Server
    initialize/account/model/read-only handshake. Direct API mode has no
    non-inference check in the current adapter and therefore remains explicit
    about being unverified.
    """
    with _conversation_lock:
        snapshot = ai_connection.check_ready()
    verification = (
        "managed_transport"
        if snapshot.mode == "managed_subscription"
        else "direct_api_inference_not_run"
    )
    return {
        "ai": snapshot.to_dict(),
        "verification": verification,
    }


@app.post("/api/settings/ai/direct-api-key")
def set_direct_api_key(request: DirectApiKeyRequest) -> dict[str, Any]:
    """Keep a user-entered Direct API key in-memory for this Core lifetime only."""
    with _conversation_lock:
        _ensure_ai_mode_can_change()
        try:
            snapshot = ai_connection.set_direct_api_key(request.api_key)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
    return {"ai": snapshot.to_dict()}


def _reset_rag_runtime() -> None:
    global _rag_index_ready, _rag_service
    with _rag_lock:
        _rag_index_ready = False
        _rag_service = None


@app.get("/api/obsidian/vaults")
def obsidian_vaults() -> dict[str, Any]:
    vaults = []
    for vault in load_obsidian_vaults():
        indexed_chunks = 0
        try:
            service = _get_rag_service()
            indexed_chunks = len(service.retriever.vector_store.collection.get(where={"vault_id": vault["id"]}, include=[]).get("ids", []))
        except Exception as error:
            print(f"[RAG] Warning: could not count Obsidian chunks: {error}")
        vaults.append({
            "id": vault["id"], "name": vault["name"], "enabled": True,
            "default_access": vault["default_access"], "indexed_chunks": indexed_chunks,
        })
    return {"vaults": vaults}


@app.post("/api/obsidian/vaults")
def register_obsidian_vault(request: ObsidianVaultRequest) -> dict[str, Any]:
    try:
        entry = save_obsidian_vault(request.vault_id, request.name, request.path, request.default_access)
        _reset_rag_runtime()
        _get_rag_service()
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"id": entry["id"], "name": entry["name"], "enabled": True, "default_access": entry["default_access"]}


@app.delete("/api/obsidian/vaults/{vault_id}")
def unregister_obsidian_vault(vault_id: str) -> dict[str, Any]:
    try:
        removed = remove_obsidian_vault(vault_id)
        if removed:
            _reset_rag_runtime()
            _get_rag_service()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if not removed:
        raise HTTPException(status_code=404, detail="Obsidian vault was not found.")
    return {"removed": True, "id": vault_id}


@app.post("/api/obsidian/reindex")
def reindex_obsidian() -> dict[str, Any]:
    _reset_rag_runtime()
    service = _get_rag_service()
    return {"status": "completed", "stored_vectors": service.retriever.vector_store.count()}


@app.post("/api/obsidian/open")
def open_obsidian_source(request: ObsidianOpenRequest) -> dict[str, Any]:
    return _execute_native_tool(
        "open_obsidian_note",
        {"vault_id": request.vault_id, "relative_path": request.relative_path},
        "Open the selected Obsidian citation.",
    )


@app.get("/api/system-info")
def system_info() -> dict[str, Any]:
    return _execute_native_tool(
        "get_system_info",
        {},
        "Show local system status.",
    )


@app.get("/api/chat/history")
def chat_history() -> dict[str, Any]:
    """Restore bounded conversation history from local persistent memory."""
    return {"turns": jarvis_memory.history()}


@app.post("/api/chat/session")
def create_chat_session() -> dict[str, str]:
    """Issue an opaque local conversation key; no App Server thread is created here."""
    return {"conversation_id": jarvis_memory.create_conversation_id()}


@app.get("/api/telemetry")
def telemetry() -> dict[str, Any]:
    """
    Read local counters without executing a tool
    or adding a task.
    """

    return read_system_telemetry()


@app.get("/api/projects")
def projects() -> dict[str, Any]:
    """
    Return only projects already present in the
    registered-project registry.
    """

    return {
        "projects": load_projects()
    }


@app.post(
    "/api/projects/git-status"
)
def project_git_status(
    request: ToolRequest,
) -> dict[str, Any]:
    return _execute_native_tool(
        "git_status",
        {
            "project_name":
                request.project_name,
        },
        (
            "Show Git status for registered "
            f"project {request.project_name}."
        ),
    )


@app.post(
    "/api/projects/list-files"
)
def project_files(
    request: ToolRequest,
) -> dict[str, Any]:
    return _execute_native_tool(
        "list_files",
        {
            "project_name":
                request.project_name,
            "relative_path":
                request.relative_path,
        },
        (
            "List files in registered project "
            f"{request.project_name}."
        ),
    )


@app.post(
    "/api/projects/read-file"
)
def project_file(
    request: ToolRequest,
) -> dict[str, Any]:
    if request.relative_path in {
        "",
        ".",
    }:
        raise HTTPException(
            status_code=422,
            detail=(
                "A project-relative file "
                "path is required."
            ),
        )

    return _execute_native_tool(
        "read_file",
        {
            "project_name":
                request.project_name,
            "relative_path":
                request.relative_path,
        },
        (
            "Read a file in registered project "
            f"{request.project_name}."
        ),
    )


@app.post(
    "/api/projects/search"
)
def project_search(
    request: ToolRequest,
) -> dict[str, Any]:
    if not request.keyword.strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "A search keyword is required."
            ),
        )

    return _execute_native_tool(
        "search_files",
        {
            "project_name":
                request.project_name,
            "keyword":
                request.keyword,
            "relative_path":
                request.relative_path,
        },
        (
            "Search a registered project for "
            f"{request.keyword}."
        ),
    )


@app.post(
    "/api/projects/refresh"
)
def refresh_projects() -> dict[str, Any]:
    """
    The explicit API action satisfies TaskRouter's
    project-scan guard.
    """

    return _execute_native_tool(
        "refresh_project_registry",
        {},
        "Refresh projects.",
    )


@app.post("/api/chat")
def chat_with_jarvis(
    request: ChatRequest,
) -> dict[str, Any]:
    """
    Handle local intents, pending confirmations, and isolated Luna text chat.
    """

    user_input = (
        request.message.strip()
    )

    # -------------------------------------------------------
    # 1. Exact local greeting
    # -------------------------------------------------------

    reply = fast_reply(
        user_input
    )

    if reply:
        return _chat_response(
            user_input,
            reply,
            [],
            speech_reply=fast_speech_reply(user_input),
        )

    lock_started = monotonic()
    with _conversation_lock:
        lock_timings = {
            "lock_wait_ms": round((monotonic() - lock_started) * 1000, 1),
        }

        # ---------------------------------------------------
        # 2. Pending confirmation
        # ---------------------------------------------------

        (
            handled,
            pending_message,
            pending_result,
        ) = (
            task_router
            .handle_pending_confirmation(
                user_input
            )
        )

        if handled:
            result = (
                _serialize_tool_result(
                    pending_result
                )
                if pending_result
                else None
            )

            reply = (
                pending_message
                or "Confirmation handled."
            )

            if (
                isinstance(
                    pending_result,
                    dict,
                )
                and pending_result.get(
                    "executor"
                )
                    == "codex_app_server"
            ):
                reply = (
                    pending_result.get(
                        "result"
                    )
                    or pending_result.get(
                        "error"
                    )
                    or reply
                )

            return _chat_response(
                user_input,
                reply,
                [result] if result else [],
                timings=lock_timings,
            )

        # ---------------------------------------------------
        # 3. Deterministic native intent
        # ---------------------------------------------------

        native_intent = (
            resolve_native_intent(
                user_input
            )
        )

        if native_intent:
            result = (
                _execute_native_tool(
                    native_intent.function_name,
                    native_intent.arguments,
                    user_input,
                )
            )

            if result.get("status") == "awaiting_confirmation":
                # The permission response owns the user-facing confirmation
                # text. Falling back to the intent description here made the
                # renderer/speech bridge announce only a short action label
                # instead of the actual Yes/No prompt.
                reply = result.get("message") or "此操作需要确认。是否继续？请回复 yes 或 no。"
            else:
                reply = (
                    result.get("result")
                    or result.get("error")
                    or native_intent.description
                )

            return _chat_response(
                user_input,
                reply,
                [result],
                timings=lock_timings,
            )

        # ---------------------------------------------------
        # 4. Isolated Luna text chat
        # ---------------------------------------------------

        request_native_intent_proposal = (
            ai_connection.mode == "managed_subscription"
            and should_request_native_intent_proposal(user_input)
        )
        result = (
            task_router
            .execute_external_action(
                executor=ai_connection.executor(),
                action="generate_response",
                purpose=user_input,
                execute=lambda: (
                    _generate_ai_response(
                        user_input,
                        request.conversation_id,
                        request_native_intent_proposal=request_native_intent_proposal,
                    )
                ),
            )
        )

        # ---------------------------------------------------
        # 5. Final response
        # ---------------------------------------------------

        model_reply = (
            result.get("result")
            or result.get("error")
            or ai_unavailable_reply()
        )

        tool_results = [_serialize_tool_result(result)]
        proposal_result = None
        if result.get("success") is True and result.get("native_intent_proposal"):
            proposal_result = _execute_native_intent_proposal(
                result.get("native_intent_proposal"),
                user_input,
            )
            tool_results.append(_serialize_tool_result(proposal_result))
            if proposal_result.get("status") == "awaiting_confirmation":
                reply = (
                    proposal_result.get("message")
                    or "此操作需要确认。是否继续？请回复 yes 或 no。"
                )
            elif proposal_result.get("success") is True:
                reply = proposal_result.get("result") or model_reply
            else:
                reply = (
                    proposal_result.get("error")
                    or "Luna 的本地操作建议未通过 Core 校验，未执行。"
                )
        else:
            reply = model_reply

        adapter_timings = result.get("timings")
        timings = {
            **lock_timings,
            **adapter_timings,
        } if isinstance(adapter_timings, dict) else lock_timings

        return _chat_response(
            user_input,
            reply,
            tool_results,
            rag_result={"used_rag": False, "sources": [], "chunks": []},
            timings=timings,
        )
