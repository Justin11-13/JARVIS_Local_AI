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
    MODEL,
    SYSTEM_PROMPT,
    TOOLS,
    chat,
    task_manager,
    task_router,
)
from skills.project import load_projects
from services.system_telemetry import read_system_telemetry


app = FastAPI(title="JARVIS Local API", version="0.1.0")

_conversation_lock = Lock()
_messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]


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
    """Report API availability without contacting a model or tool."""
    return {
        "status": "ready",
        "model": MODEL,
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
    """Run the existing local-model tool loop behind the same routing policy."""
    user_input = request.message.strip()
    with _conversation_lock:
        handled, pending_message, pending_result = task_router.handle_pending_open_interpreter_confirmation(user_input)
        if handled:
            result = _serialize_tool_result(pending_result) if pending_result else None
            return {
                "reply": pending_message or "Confirmation handled.",
                "tool_results": [result] if result else [],
            }

        _messages.append({"role": "user", "content": user_input})
        tool_results: list[dict[str, Any]] = []

        try:
            for _ in range(10):
                response = chat(model=MODEL, messages=_messages, tools=TOOLS, think=False)
                _messages.append(response.message)
                tool_calls = response.message.tool_calls

                if not tool_calls:
                    return {
                        "reply": response.message.content or "No response was returned.",
                        "tool_results": tool_results,
                    }

                for tool_call in tool_calls:
                    result = task_router.execute_tool(
                        function_name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                        user_input=user_input,
                        available_tools=AVAILABLE_TOOLS,
                    )
                    serialized = _serialize_tool_result(result)
                    serialized["tool_name"] = tool_call.function.name
                    tool_results.append(serialized)
                    _messages.append(
                        {
                            "role": "tool",
                            "content": str(result),
                            "tool_name": tool_call.function.name,
                        }
                    )
        except Exception as error:  # Preserve the CLI's user-visible error boundary.
            raise HTTPException(status_code=503, detail=f"JARVIS Core is unavailable: {error}") from error

    return {
        "reply": "The task exceeded the 10-step safety limit and was stopped.",
        "tool_results": tool_results,
    }
