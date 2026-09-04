"""JARVIS runtime composition root.

This module owns the native tool registry and the policy services shared by the
terminal and loopback API. It intentionally does not start, load, or import a
local language model. Gemini is an optional BYOK cloud brain; any future Codex
integration remains policy-controlled.
"""

from pathlib import Path

from services.agents.gemini import GeminiAdapter
from services.agents.open_interpreter import OpenInterpreterAdapter
from services.byok_config import load_byok_config
from services.notification_service import NotificationService
from services.jarvis_memory import JarvisMemory
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
from skills.windows import (
    adjust_volume,
    get_battery_status,
    get_network_status,
    list_running_processes,
    lock_computer,
    media_control,
    open_known_folder,
    open_windows_setting,
    restart_computer,
    shutdown_computer,
    sleep_computer,
    toggle_mute,
)


OPEN_INTERPRETER_ROUTING_MODE = "automatic"

byok_config = load_byok_config()
BRAIN_PROVIDER = byok_config.provider
BRAIN_MODEL = byok_config.model
open_interpreter = OpenInterpreterAdapter()
gemini = GeminiAdapter()
BRAIN_STATUS = "unsupported" if byok_config.error else ("configured" if gemini.is_configured() else "not_configured")
task_manager = TaskManager()
notification_service = NotificationService()
jarvis_memory = JarvisMemory(
    max_turns=100,
    context_turns=6,
    storage_path=(
        Path(__file__).resolve().parents[1]
        / "data"
        / "memory"
        / "conversation.json"
    ),
)
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
    "get_battery_status": get_battery_status,
    "get_network_status": get_network_status,
    "list_running_processes": list_running_processes,
    "adjust_volume": adjust_volume,
    "toggle_mute": toggle_mute,
    "media_control": media_control,
    "lock_computer": lock_computer,
    "open_known_folder": open_known_folder,
    "open_windows_setting": open_windows_setting,
    "shutdown_computer": shutdown_computer,
    "restart_computer": restart_computer,
    "sleep_computer": sleep_computer,
}


def gemini_not_configured_reply() -> str:
    """Explain how to enable the optional cloud understanding fallback."""
    return (
        "Gemini cloud understanding is not configured. Add a valid local API key, "
        "select JARVIS_BRAIN_PROVIDER=gemini, choose a supported Gemini model, "
        "and set GEMINI_ENABLED=true in .env."
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
    """Handle an already-pending action confirmation from the CLI."""
    handled, message, result = task_router.handle_pending_confirmation(user_input)
    if not handled:
        return False

    if message:
        print(f"\nJARVIS > {message}")
    if result:
        display_tool_result(result)
        if isinstance(result, dict):
            final_result = result.get("result") or result.get("error") or "任务已结束。"
        else:
            final_result = str(result)
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
        print(f"\nJARVIS > {gemini_not_configured_reply()}")


if __name__ == "__main__":
    run_jarvis()
