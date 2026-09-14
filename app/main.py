"""JARVIS runtime composition root.

This module owns the native tool registry and the policy services shared by the
terminal and loopback API. It intentionally does not start, load, or import a
local language model. Luna foreground chat is transported through the local
Codex App Server with managed ChatGPT authentication; execution remains
policy-controlled in Python.
"""

from pathlib import Path

from services.agents.codex_app_server import CodexAppServerAdapter
from services.agents.openai_responses import OpenAIResponsesAdapter
from services.ai_connection import AiConnectionService
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
from skills.obsidian import append_obsidian_note, create_obsidian_note, open_obsidian_note, search_obsidian_notes, update_obsidian_note
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


luna = CodexAppServerAdapter()
direct_luna = OpenAIResponsesAdapter()
ai_connection = AiConnectionService(subscription=luna, direct_api=direct_luna)
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
    "search_obsidian_notes": search_obsidian_notes,
    "open_obsidian_note": open_obsidian_note,
    "create_obsidian_note": create_obsidian_note,
    "append_obsidian_note": append_obsidian_note,
    "update_obsidian_note": update_obsidian_note,
}


def ai_unavailable_reply() -> str:
    """Explain the selected transport failure without switching transports."""
    snapshot = ai_connection.snapshot()
    if snapshot.mode == "direct_api" and snapshot.status == "unconfigured":
        return "Direct API is not configured. Enter an OpenAI API key in Settings, then explicitly test or send a request."
    return snapshot.detail or "The selected Luna transport is not ready. JARVIS did not switch transports."


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
    snapshot = ai_connection.snapshot()
    print(f"Reasoning backend: {snapshot.mode} ({snapshot.status})")
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
        print(f"\nJARVIS > {ai_unavailable_reply()}")


if __name__ == "__main__":
    run_jarvis()
