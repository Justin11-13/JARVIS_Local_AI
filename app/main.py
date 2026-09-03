"""JARVIS runtime composition root.

This module owns the native tool registry and the policy services shared by the
terminal and loopback API. It intentionally does not start, load, or import a
local language model. Codex integration is added through a policy-controlled
executor in a later migration phase.
"""

from services.agents.open_interpreter import OpenInterpreterAdapter
from services.notification_service import NotificationService
from services.task_manager import TaskManager
from services.task_router import TaskRouter
from skills.files import list_files, read_file, search_files
from skills.git import git_status
from skills.project import (
    get_project_info,
    list_projects,
    open_project,
    refresh_project_registry,
)
from skills.system import get_system_info, open_app


BRAIN_PROVIDER = "codex"
BRAIN_STATUS = "not_configured"
OPEN_INTERPRETER_ROUTING_MODE = "automatic"

open_interpreter = OpenInterpreterAdapter()
task_manager = TaskManager()
notification_service = NotificationService()
task_router = TaskRouter(
    routing_mode=OPEN_INTERPRETER_ROUTING_MODE,
    open_interpreter=open_interpreter,
    task_manager=task_manager,
    notification_service=notification_service,
)


AVAILABLE_TOOLS = {
    "open_app": open_app,
    "get_system_info": get_system_info,
    "list_projects": list_projects,
    "get_project_info": get_project_info,
    "open_project": open_project,
    "git_status": git_status,
    "list_files": list_files,
    "read_file": read_file,
    "search_files": search_files,
    "refresh_project_registry": refresh_project_registry,
}


def codex_not_configured_reply() -> str:
    """Describe the deliberate Phase 1 boundary without pretending to reason."""
    return (
        "Codex is the configured JARVIS reasoning backend, but its executor is "
        "not configured yet. Native tools and the existing Open Interpreter "
        "permission flow remain available through their explicit interfaces."
    )


def display_tool_result(result) -> None:
    """Show a routed tool result without assuming a particular executor."""
    if not isinstance(result, dict):
        print("[Tool Result]", result)
        return

    display_result = {
        "task": result.get("task"),
        "success": result.get("success"),
        "status": result.get("status"),
        "risk": result.get("risk"),
        "result": result.get("result"),
    }
    if result.get("message"):
        display_result["message"] = result["message"]
    if result.get("error"):
        display_result["error"] = result["error"]
    print("[Tool Result]", display_result)

    if notification := result.get("notification"):
        print("\n[JARVIS Notification]", notification)


def handle_router_confirmation(user_input: str) -> bool:
    """Handle an already-approved Open Interpreter request from the CLI."""
    handled, message, result = task_router.handle_pending_open_interpreter_confirmation(
        user_input
    )
    if not handled:
        return False

    if message:
        print(f"\nJARVIS > {message}")
    if result:
        display_tool_result(result)
        final_result = result.get("result") or result.get("error") or "任务已结束。"
        print(f"\nJARVIS > {final_result}")
    return True


def run_jarvis() -> None:
    """Run the lightweight terminal shell without allocating model resources."""
    print()
    print("=" * 60)
    print("JARVIS v0.6")
    print(f"Reasoning backend: {BRAIN_PROVIDER} ({BRAIN_STATUS})")
    print(f"Open Interpreter mode: {OPEN_INTERPRETER_ROUTING_MODE}")
    print("输入 exit 退出")
    print("=" * 60)

    while True:
        user_input = input("\nYou > ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "bye"}:
            print("\nJARVIS > Goodbye.")
            break
        if handle_router_confirmation(user_input):
            continue
        print(f"\nJARVIS > {codex_not_configured_reply()}")


if __name__ == "__main__":
    run_jarvis()
