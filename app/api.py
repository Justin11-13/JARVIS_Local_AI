"""Local-only API for the Flutter desktop client.

The API reuses the same tool registry and TaskRouter as the CLI.  It binds to
loopback only when started through the documented command, so the desktop UI
cannot turn JARVIS tools into a network service.
"""

from __future__ import annotations

import re
from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.main import (
    AVAILABLE_TOOLS,
    BRAIN_MODEL,
    BRAIN_PROVIDER,
    BRAIN_STATUS,
    gemini,
    gemini_not_configured_reply,
    jarvis_memory,
    task_manager,
    task_router,
)
from skills.project import load_projects
from services.native_intent import resolve_native_intent
from services.system_telemetry import read_system_telemetry


app = FastAPI(title="JARVIS Local API", version="0.1.0")

_conversation_lock = Lock()

# Pure greetings do not need a reasoning backend.
FAST_REPLIES = {
    "你好": "你好！我是 JARVIS。有什么可以帮你的吗？",
    "您好": "您好！我是 JARVIS。有什么可以帮你的吗？",
    "hi": "Hi! I am JARVIS. How can I help?",
    "hello": "Hello! I am JARVIS. How can I help?",
}


def fast_reply(message: str) -> str | None:
    """Return a local reply only for an exact, non-actionable greeting."""
    normalized = " ".join(message.strip().lower().split())
    return FAST_REPLIES.get(normalized)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12_000)


class ToolRequest(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    relative_path: str = Field(default=".", max_length=500)
    keyword: str = Field(default="", max_length=500)


def _serialize_tool_result(result: Any) -> dict[str, Any]:
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
            "requires_confirmation": result.get("requires_confirmation"),
            "confirmation_count": result.get("confirmation_count"),
            "confirmation_step": result.get("confirmation_step"),
            "audit_summary": result.get("audit_summary"),
            "submission_preview": result.get("submission_preview"),
            "tool_calls": result.get("tool_calls"),
        }
    return {"result": str(result)}


def _execute_native_tool(function_name: str, arguments: dict[str, Any], user_input: str) -> dict[str, Any]:
    result = task_router.execute_tool(
        function_name=function_name,
        arguments=arguments,
        user_input=user_input,
        available_tools=AVAILABLE_TOOLS,
    )
    serialized = _serialize_tool_result(result)
    if not isinstance(result, dict):
        serialized["success"] = True
        serialized["status"] = "completed"
    return serialized


GEMINI_LOCAL_TOOL_SCHEMAS = {
    "open_app": ({"app"}, set()),
    "get_system_info": (set(), set()),
    "list_projects": (set(), set()),
    "get_project_info": ({"project_name"}, set()),
    "open_project": ({"project_name"}, set()),
    "git_status": ({"project_name"}, set()),
    "list_files": ({"project_name"}, {"relative_path"}),
    "read_file": ({"project_name", "relative_path"}, set()),
    "search_files": ({"project_name", "keyword"}, {"relative_path"}),
    "refresh_project_registry": (set(), set()),
    "get_battery_status": (set(), set()),
    "get_network_status": (set(), set()),
    "list_running_processes": (set(), set()),
    "adjust_volume": ({"direction"}, {"amount"}),
    "toggle_mute": (set(), set()),
    "media_control": ({"action"}, set()),
    "open_known_folder": ({"folder"}, set()),
    "open_windows_setting": ({"setting"}, set()),
    "lock_computer": (set(), set()),
    "shutdown_computer": (set(), set()),
    "restart_computer": (set(), set()),
    "sleep_computer": (set(), set()),
}

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
SENSITIVE_FILE_SUFFIXES = {".pem", ".key", ".pfx", ".p12"}
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?im)\b(api[_-]?key|access[_-]?token|auth[_-]?token|password|secret|private[_-]?key|authorization)\b"
    r"\s*([:=])\s*([^\s,;]+)"
)


def _execute_gemini_safe_tool(function_name: str, arguments: dict[str, Any], user_input: str) -> dict[str, Any]:
    """Validate Gemini's local-tool proposal before it reaches the registry."""
    schema = GEMINI_LOCAL_TOOL_SCHEMAS.get(function_name)
    if schema is None:
        return {
            "success": False,
            "status": "routing_blocked",
            "result": "",
            "error": f"Gemini requested unavailable tool '{function_name}'.",
        }

    required_keys, optional_keys = schema
    supplied_keys = set(arguments)
    if not required_keys.issubset(supplied_keys) or not supplied_keys.issubset(required_keys | optional_keys):
        return {
            "success": False,
            "status": "validation_failed",
            "result": "",
            "error": f"Gemini supplied invalid arguments for '{function_name}'.",
        }

    normalized_arguments: dict[str, str] = {}
    for key, value in arguments.items():
        maximum_length = 500 if key in {"relative_path", "keyword"} else 200
        if not isinstance(value, str) or not value.strip() or len(value) > maximum_length:
            return {
                "success": False,
                "status": "validation_failed",
                "result": "",
                "error": f"Gemini supplied an invalid '{key}' argument.",
            }
        normalized_arguments[key] = value.strip()

    allowed_values = {
        "adjust_volume": {"direction": {"up", "down"}, "amount": {"small", "medium", "large"}},
        "media_control": {"action": {"play_pause", "next", "previous", "stop"}},
        "open_known_folder": {"folder": {"desktop", "documents", "downloads", "pictures", "music", "videos"}},
        "open_windows_setting": {"setting": {"display", "sound", "wifi", "bluetooth", "power", "notifications", "privacy"}},
    }
    for key, valid_values in allowed_values.get(function_name, {}).items():
        if key in normalized_arguments and normalized_arguments[key].lower() not in valid_values:
            return {
                "success": False,
                "status": "validation_failed",
                "result": "",
                "error": f"Gemini supplied an unsupported '{key}' value for '{function_name}'.",
            }

    if function_name == "adjust_volume" and "amount" not in normalized_arguments:
        normalized_arguments["amount"] = "medium"

    if function_name == "read_file" and _is_sensitive_file(normalized_arguments["relative_path"]):
        return {
            "success": False,
            "status": "routing_blocked",
            "result": "",
            "error": "JARVIS does not send credential or secret files to Gemini.",
        }

    result = _execute_native_tool(function_name, normalized_arguments, user_input)
    return _redact_gemini_tool_result(result)


def _is_sensitive_file(relative_path: str) -> bool:
    file_name = relative_path.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return file_name in SENSITIVE_FILE_NAMES or any(file_name.endswith(suffix) for suffix in SENSITIVE_FILE_SUFFIXES)


def _redact_gemini_tool_result(result: dict[str, Any]) -> dict[str, Any]:
    """Keep common credential values out of the cloud-bound tool response."""
    safe_result = dict(result)
    value = safe_result.get("result")
    if isinstance(value, str):
        safe_result["result"] = SENSITIVE_VALUE_PATTERN.sub(r"\1\2 [REDACTED]", value)
    return safe_result


def _chat_response(user_input: str, reply: str, tool_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the API response and retain the completed turn in local session memory."""
    jarvis_memory.remember(user_input, reply)
    return {"reply": reply, "tool_results": tool_results}


@app.get("/api/health")
def health() -> dict[str, Any]:
    """Report API availability without contacting a reasoning backend or tool."""
    return {
        "status": "ready",
        "brain": BRAIN_PROVIDER,
        "brain_model": BRAIN_MODEL,
        "brain_status": BRAIN_STATUS,
        "routing_mode": task_router.routing_mode,
        "task_count": len(task_manager.list_tasks()),
    }


@app.get("/api/system-info")
def system_info() -> dict[str, Any]:
    return _execute_native_tool("get_system_info", {}, "Show local system status.")


@app.get("/api/telemetry")
def telemetry() -> dict[str, Any]:
    """Read local counters without executing a tool or adding a task."""
    return read_system_telemetry()


@app.get("/api/projects")
def projects() -> dict[str, Any]:
    """Return only projects already present in the registered-project registry."""
    return {"projects": load_projects()}


@app.post("/api/projects/git-status")
def project_git_status(request: ToolRequest) -> dict[str, Any]:
    return _execute_native_tool(
        "git_status",
        {"project_name": request.project_name},
        f"Show Git status for registered project {request.project_name}.",
    )


@app.post("/api/projects/list-files")
def project_files(request: ToolRequest) -> dict[str, Any]:
    return _execute_native_tool(
        "list_files",
        {"project_name": request.project_name, "relative_path": request.relative_path},
        f"List files in registered project {request.project_name}.",
    )


@app.post("/api/projects/read-file")
def project_file(request: ToolRequest) -> dict[str, Any]:
    if request.relative_path in {"", "."}:
        raise HTTPException(status_code=422, detail="A project-relative file path is required.")
    return _execute_native_tool(
        "read_file",
        {"project_name": request.project_name, "relative_path": request.relative_path},
        f"Read a file in registered project {request.project_name}.",
    )


@app.post("/api/projects/search")
def project_search(request: ToolRequest) -> dict[str, Any]:
    if not request.keyword.strip():
        raise HTTPException(status_code=422, detail="A search keyword is required.")
    return _execute_native_tool(
        "search_files",
        {
            "project_name": request.project_name,
            "keyword": request.keyword,
            "relative_path": request.relative_path,
        },
        f"Search a registered project for {request.keyword}.",
    )


@app.post("/api/projects/refresh")
def refresh_projects() -> dict[str, Any]:
    """The explicit API action satisfies TaskRouter's project-scan guard."""
    return _execute_native_tool(
        "refresh_project_registry",
        {},
        "Refresh projects.",
    )


@app.post("/api/chat")
def chat_with_jarvis(request: ChatRequest) -> dict[str, Any]:
    """Handle safe local replies and pending approvals during the migration."""
    user_input = request.message.strip()
    reply = fast_reply(user_input)
    if reply:
        return _chat_response(user_input, reply, [])

    with _conversation_lock:
        handled, pending_message, pending_result = (
            task_router.handle_pending_confirmation(user_input)
        )
        if handled:
            result = _serialize_tool_result(pending_result) if pending_result else None
            reply = pending_message or "Confirmation handled."
            if isinstance(pending_result, dict) and pending_result.get("executor") == "gemini":
                reply = pending_result.get("result") or pending_result.get("error") or reply
            return _chat_response(user_input, reply, [result] if result else [])

        native_intent = resolve_native_intent(user_input)
        if native_intent:
            result = _execute_native_tool(
                native_intent.function_name,
                native_intent.arguments,
                user_input,
            )
            reply = result.get("result") or result.get("error") or native_intent.description
            return _chat_response(user_input, reply, [result])

        if not gemini.is_configured():
            return _chat_response(user_input, gemini_not_configured_reply(), [])

        result = task_router.execute_external_action(
            executor="gemini",
            action="generate_response",
            purpose=user_input,
            execute=lambda: gemini.generate_response(
                user_input,
                execute_tool=lambda function_name, arguments: _execute_gemini_safe_tool(
                    function_name,
                    arguments,
                    user_input,
                ),
                memory_contents=jarvis_memory.gemini_contents(),
            ),
        )
        reply = result.get("result") or result.get("error") or "Gemini returned no response."
        return _chat_response(user_input, reply, [_serialize_tool_result(result)])
