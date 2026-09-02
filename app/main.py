from ollama import chat

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

# ============================================================
# JARVIS Configuration
# ============================================================

MODEL = "qwen3:8b"

OPEN_INTERPRETER_ROUTING_MODE = "automatic"
# Options:
# "manual"
# "ask"
# "automatic"

open_interpreter = OpenInterpreterAdapter()
task_manager = TaskManager()
notification_service = NotificationService()
task_router = TaskRouter(
    routing_mode=OPEN_INTERPRETER_ROUTING_MODE,
    open_interpreter=open_interpreter,
    task_manager=task_manager,
    notification_service=notification_service,
)


# ============================================================
# System Prompt
# ============================================================

BASE_SYSTEM_PROMPT = """
You are JARVIS, a local Windows AI assistant.


# General Rules

- Reply mainly in Chinese.
- Complete every part of the user's request.
- A single request may require multiple tool calls.
- Continue using tools until the entire request is completed.
- Never invent tools.
- Never claim that an action succeeded unless a tool confirmed it.
- Keep responses concise.


# Windows Applications

- Use open_app when the user asks to open an installed Windows application.

- The open_app tool automatically searches the Windows application registry,
  so do not assume an application is unsupported before calling the tool.


# System Information

- Use get_system_info when the user asks about CPU or RAM.


# Project Management

- Use list_projects when the user asks what projects exist.

- Use get_project_info when the user asks about a registered project.

- Use open_project when the user asks to open a registered project.

- Use refresh_project_registry only when the user explicitly asks JARVIS
  to scan, discover, refresh, or find local development projects.

- Project discovery only scans configured project roots.

- Never invent project paths.

- Never call refresh_project_registry merely because the user provides
  an arbitrary local directory path.

- A local directory path does not automatically mean it is a development
  project.


# Git

- Use git_status when the user asks about the Git status of a project.

- Never invent Git information.


# Native Project File Tools

- Use list_files when the user asks what files or folders exist in a
  registered project.

- Use read_file when the user asks to inspect or read a registered
  project file.

- Use search_files when the user asks to find code, text, classes,
  functions, routes, models, or keywords inside a registered project.

- File tools are read-only.

- Do not claim to modify files.

- When referring to the root folder of a project, use "." as relative_path,
  not "/" or an absolute path.

- list_files, read_file, and search_files are only for registered
  JARVIS projects.

- Never use a Windows absolute path as project_name or relative_path
  for list_files, read_file, or search_files.


# Open Interpreter

- Open Interpreter is intended for complex local execution tasks that are
  not naturally covered by existing JARVIS native tools.

- Good Open Interpreter tasks include:
  - arbitrary local directory workflows
  - batch file processing
  - analyzing multiple files
  - generating summaries from multiple files
  - reorganizing files
  - creating output files
  - dynamic command execution
  - multi-step local workflows

- Do not use Open Interpreter for simple operations already supported by
  native JARVIS tools.

- Before calling any Open Interpreter tool, both the task and workspace
  must be clearly known.

- If the task or workspace is missing, ask a concise follow-up question.

- Never guess an Open Interpreter workspace.

- Never use "/", "\\", ".", a drive root, or the current working directory
  as a guessed Open Interpreter workspace.

- The workspace must be an existing local directory explicitly provided
  by the user or resolved from a known registered project.

- Preserve important user constraints such as:
  - "do not modify files"
  - "read only"
  - "do not delete anything"

- If the user provides an arbitrary local directory that is not a registered
  project, do not ask the user to register it just to complete a general
  local file-processing task.


# Open Interpreter Risk Levels

- low:
  Read-only or analysis operations.

  Examples:
  - reading files
  - listing files
  - analyzing files
  - generating summaries
  - read-only diagnostics
  - inspecting data

- medium:
  Operations that create or modify local state.

  Examples:
  - creating files
  - editing files
  - renaming files
  - moving files
  - replacing file content
  - installing software

- high:
  Destructive, privileged, or system-level operations.

  Examples:
  - deleting files
  - destructive commands
  - formatting disks
  - administrator operations
  - registry changes
  - shutdown or restart
  - important system configuration changes


# Open Interpreter Routing Modes

- manual:
  Only use Open Interpreter when the user explicitly asks for it.

  Never automatically call request_open_interpreter.

- ask:
  If JARVIS determines Open Interpreter is more appropriate than native
  tools, call request_open_interpreter first.

  Do not execute Open Interpreter before confirmation unless the user
  explicitly requested Open Interpreter.

- automatic:
  Low-risk Open Interpreter tasks may be executed automatically.

  Medium-risk and high-risk Open Interpreter tasks require confirmation
  before execution.

- Never automatically execute medium-risk or high-risk operations.


# Open Interpreter Tools

There are two Open Interpreter tools.


1. request_open_interpreter

- Creates a pending Open Interpreter request.

- Does not execute Open Interpreter.

- Use in ask mode when the user did not explicitly request Open Interpreter.

- Use in automatic mode for medium-risk and high-risk tasks.


2. delegate_to_open_interpreter

- Executes an Open Interpreter task.

- In manual mode, only use when the user explicitly requests Open Interpreter.

- In ask mode, direct execution is allowed when the user explicitly requests
  Open Interpreter.

- In automatic mode, low-risk tasks may use this directly.

- Medium-risk and high-risk automatic tasks must be confirmed first.


# Tool Routing Priority

1. Prefer native JARVIS tools when the requested capability is already
   supported.

2. Do not force native project tools onto arbitrary local directories.

3. Do not use project discovery merely because the user provides a local path.

4. For arbitrary local multi-file workflows, follow the Open Interpreter
   routing mode.

5. Manual:
   user must explicitly request Open Interpreter.

6. Ask:
   use request_open_interpreter before non-explicit Open Interpreter tasks.

7. Automatic:
   low risk -> delegate_to_open_interpreter
   medium risk -> request_open_interpreter
   high risk -> request_open_interpreter


# Safety

- Never invent tools.
- Never invent project paths.
- Never invent Git information.
- Never claim an action succeeded unless a tool confirmed it.
"""

SYSTEM_PROMPT = (
    BASE_SYSTEM_PROMPT
    + f"""

# Runtime Configuration

Open Interpreter routing mode: {OPEN_INTERPRETER_ROUTING_MODE}

Important:

- If mode is "manual":
  - never call request_open_interpreter automatically.
  - only call delegate_to_open_interpreter when the user explicitly asks
    to use Open Interpreter.

- If mode is "ask":
  - use request_open_interpreter for suitable tasks when Open Interpreter
    was not explicitly requested.
  - never directly delegate a non-explicit Open Interpreter task.

- If mode is "automatic":
  - low-risk tasks may call delegate_to_open_interpreter directly.
  - medium-risk tasks must use request_open_interpreter.
  - high-risk tasks must use request_open_interpreter.

- Never automatically execute medium-risk or high-risk Open Interpreter
  operations.
"""
)


# ============================================================
# Tool Registry
# ============================================================

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


# ============================================================
# Ollama Tool Definitions
# ============================================================

TOOLS = [
    open_app,
    get_system_info,
    list_projects,
    get_project_info,
    open_project,
    git_status,
    list_files,
    read_file,
    search_files,
    refresh_project_registry,
    {
        "type": "function",
        "function": {
            "name": "request_open_interpreter",
            "description": (
                "Create a pending Open Interpreter request requiring user "
                "confirmation. Use in ask mode for non-explicit Open "
                "Interpreter tasks. In automatic mode use for medium-risk "
                "or high-risk Open Interpreter tasks. This tool does not "
                "execute Open Interpreter."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": (
                            "The complete task that would be delegated, "
                            "including important user constraints."
                        ),
                    },
                    "workspace": {
                        "type": "string",
                        "description": (
                            "The explicit existing local directory where "
                            "Open Interpreter would perform the task."
                        ),
                    },
                },
                "required": [
                    "task",
                    "workspace",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_open_interpreter",
            "description": (
                "Execute a task using Open Interpreter. In manual mode "
                "use only when explicitly requested. In ask mode direct "
                "execution requires an explicit Open Interpreter request. "
                "In automatic mode this may be used directly only for "
                "low-risk tasks. Medium-risk and high-risk automatic tasks "
                "require confirmation first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": (
                            "The complete Open Interpreter task including "
                            "important constraints."
                        ),
                    },
                    "workspace": {
                        "type": "string",
                        "description": (
                            "An explicit existing local directory where "
                            "Open Interpreter is allowed to work."
                        ),
                    },
                },
                "required": [
                    "task",
                    "workspace",
                ],
            },
        },
    },
]


# ============================================================
# Tool Result Display
# ============================================================


def display_tool_result(
    result,
):
    if not isinstance(
        result,
        dict,
    ):
        print(
            "[Tool Result]",
            result,
        )
        return

    display_result = {
        "task": result.get("task"),
        "success": result.get("success"),
        "status": result.get("status"),
        "risk": result.get("risk"),
        "result": result.get("result"),
    }

    if result.get("message"):
        display_result["message"] = result.get("message")

    if result.get("error"):
        display_result["error"] = result.get("error")

    print(
        "[Tool Result]",
        display_result,
    )

    notification = result.get("notification")

    if notification:
        print(
            "\n[JARVIS Notification]",
            notification,
        )


def execute_routed_tool(
    tool_call,
    user_input: str,
):
    function_name = tool_call.function.name
    arguments = tool_call.function.arguments

    print(f"\n[JARVIS Tool] {function_name}({arguments})")

    return task_router.execute_tool(
        function_name=function_name,
        arguments=arguments,
        user_input=user_input,
        available_tools=AVAILABLE_TOOLS,
    )


def handle_router_confirmation(
    user_input: str,
):
    handled, message, result = (
        task_router.handle_pending_open_interpreter_confirmation(user_input)
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


# ============================================================
# Main JARVIS Loop
# ============================================================


def run_jarvis():
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    print()
    print("=" * 60)
    print("JARVIS Local v0.5")
    print(f"Model: {MODEL}")
    print(f"Open Interpreter mode: {OPEN_INTERPRETER_ROUTING_MODE}")
    print("输入 exit 退出")
    print("=" * 60)

    while True:
        user_input = input("\nYou > ").strip()

        if not user_input:
            continue

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        if user_input.lower() in {
            "exit",
            "quit",
            "bye",
        }:
            print("\nJARVIS > Goodbye.")
            break

        # ----------------------------------------------------
        # Pending OI Confirmation
        # ----------------------------------------------------

        if handle_router_confirmation(user_input):
            continue

        # ----------------------------------------------------
        # Add User Message
        # ----------------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        try:
            # ------------------------------------------------
            # JARVIS Agent Loop
            # ------------------------------------------------

            for step in range(10):
                response = chat(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS,
                    think=False,
                )

                messages.append(response.message)

                tool_calls = response.message.tool_calls

                # --------------------------------------------
                # No Tool Calls
                # --------------------------------------------

                if not tool_calls:
                    print(
                        "\nJARVIS >",
                        response.message.content,
                    )
                    break

                # --------------------------------------------
                # Execute Tools
                # --------------------------------------------

                for tool_call in tool_calls:
                    result = execute_routed_tool(
                        tool_call,
                        user_input,
                    )

                    display_tool_result(result)

                    messages.append(
                        {
                            "role": "tool",
                            "content": str(result),
                            "tool_name": (tool_call.function.name),
                        }
                    )

            else:
                print("\nJARVIS > 任务执行步骤超过限制，已停止。")

        except Exception as error:
            print(
                "\n[JARVIS Error]",
                error,
            )


# ============================================================
# Entry Point
# ============================================================


if __name__ == "__main__":
    run_jarvis()
