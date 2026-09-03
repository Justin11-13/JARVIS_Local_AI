"""Local-only API for the Flutter desktop client.

The API reuses the same tool registry and TaskRouter as the CLI.  It binds to
loopback only when started through the documented command, so the desktop UI
cannot turn JARVIS tools into a network service.
"""

from __future__ import annotations

from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.main import (
    AVAILABLE_TOOLS,
    BRAIN_PROVIDER,
    BRAIN_STATUS,
    codex_not_configured_reply,
    task_manager,
    task_router,
)
from skills.project import load_projects
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
        }
    return {"result": str(result)}


def _execute_native_tool(function_name: str, arguments: dict[str, Any], user_input: str) -> dict[str, Any]:
    result = task_router.execute_tool(
        function_name=function_name,
        arguments=arguments,
        user_input=user_input,
        available_tools=AVAILABLE_TOOLS,
    )
    return _serialize_tool_result(result)


@app.get("/api/health")
def health() -> dict[str, Any]:
    """Report API availability without contacting a reasoning backend or tool."""
    return {
        "status": "ready",
        "brain": BRAIN_PROVIDER,
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
        return {"reply": reply, "tool_results": []}

    with _conversation_lock:
        handled, pending_message, pending_result = (
            task_router.handle_pending_open_interpreter_confirmation(user_input)
        )
        if handled:
            result = _serialize_tool_result(pending_result) if pending_result else None
            return {
                "reply": pending_message or "Confirmation handled.",
                "tool_results": [result] if result else [],
            }

    return {"reply": codex_not_configured_reply(), "tool_results": []}
