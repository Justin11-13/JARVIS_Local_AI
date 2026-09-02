from pathlib import Path

from ollama import chat

from services.agents.open_interpreter import OpenInterpreterAdapter
from services.notification_service import NotificationService
from services.task_manager import TaskManager
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

pending_open_interpreter_request = None


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
# Open Interpreter Validation
# ============================================================


def validate_open_interpreter_workspace(
    workspace: str,
) -> tuple[Path | None, str | None]:
    workspace = workspace.strip()

    if not workspace:
        return None, "Open Interpreter workspace is missing."

    if workspace in {"/", "\\", "."}:
        return (
            None,
            "Open Interpreter requires an explicit workspace directory.",
        )

    try:
        workspace_path = Path(workspace).expanduser().resolve()

    except OSError as error:
        return None, f"Invalid workspace: {error}"

    if not workspace_path.exists():
        return (
            None,
            f"Workspace does not exist: {workspace_path}",
        )

    if not workspace_path.is_dir():
        return (
            None,
            f"Workspace is not a directory: {workspace_path}",
        )

    # Prevent C:\, D:\, etc.
    if workspace_path == Path(workspace_path.anchor):
        return (
            None,
            "Open Interpreter cannot use an entire drive as its workspace.",
        )

    return workspace_path, None


# ============================================================
# Open Interpreter Risk Classification
# ============================================================


def classify_open_interpreter_risk(
    task: str,
) -> str:
    normalized_task = task.lower()

    # ========================================================
    # High Risk
    # ========================================================

    high_risk_keywords = {
        "删除",
        "delete",
        "remove",
        "erase",
        "wipe",
        "清空",
        "格式化",
        "format disk",
        "管理员",
        "administrator",
        "admin privilege",
        "registry",
        "注册表",
        "shutdown",
        "关机",
        "重启电脑",
        "restart computer",
        "reboot",
        "powershell as admin",
        "system configuration",
        "系统设置",
    }

    if any(keyword in normalized_task for keyword in high_risk_keywords):
        return "high"

    # ========================================================
    # Explicit Read-Only / No Modification
    # ========================================================

    read_only_phrases = {
        "不要修改",
        "不要编辑",
        "不要创建",
        "不要写入",
        "不要移动",
        "不要重命名",
        "不要更改",
        "不要改变",
        "只读",
        "仅读取",
        "仅分析",
        "只分析",
        "不要做任何修改",
        "不要修改任何东西",
        "不要修改任何内容",
        "do not modify",
        "don't modify",
        "do not edit",
        "don't edit",
        "do not write",
        "read only",
        "read-only",
        "do not change",
        "don't change",
        "do not create",
    }

    explicitly_read_only = any(
        phrase in normalized_task for phrase in read_only_phrases
    )

    if explicitly_read_only:
        return "low"

    # ========================================================
    # Medium Risk
    # ========================================================

    medium_risk_keywords = {
        "修改",
        "编辑",
        "modify",
        "edit",
        "rename",
        "重命名",
        "move",
        "移动",
        "create",
        "创建",
        "write",
        "写入",
        "replace",
        "替换",
        "install",
        "安装",
        "update file",
        "更新文件",
        "copy",
        "复制",
    }

    if any(keyword in normalized_task for keyword in medium_risk_keywords):
        return "medium"

    return "low"


# ============================================================
# Open Interpreter Confirmation Request
# ============================================================


def request_open_interpreter(
    task: str,
    workspace: str,
) -> dict:
    global pending_open_interpreter_request

    if OPEN_INTERPRETER_ROUTING_MODE == "manual":
        return {
            "success": False,
            "status": "manual_mode",
            "error": (
                "Open Interpreter is in manual mode. "
                "It can only be used when the user explicitly requests it."
            ),
        }

    task = task.strip()

    if not task:
        return {
            "success": False,
            "status": "validation_failed",
            "error": "Open Interpreter task is missing.",
        }

    workspace_path, validation_error = validate_open_interpreter_workspace(workspace)

    if validation_error:
        return {
            "success": False,
            "status": "validation_failed",
            "error": validation_error,
        }

    risk = classify_open_interpreter_risk(task)

    pending_open_interpreter_request = {
        "task": task,
        "workspace": str(workspace_path),
        "risk": risk,
    }

    return {
        "success": True,
        "status": "awaiting_confirmation",
        "task": task,
        "workspace": str(workspace_path),
        "risk": risk,
        "message": (
            f"这个 Open Interpreter 任务风险等级为 {risk.upper()}。"
            "是否继续？请回复 yes 或 no。"
        ),
    }


# ============================================================
# Open Interpreter Execution
# ============================================================


def delegate_to_open_interpreter(
    task: str,
    workspace: str,
) -> dict:
    task = task.strip()

    if not task:
        return {
            "task": None,
            "result": "",
            "success": False,
            "status": "validation_failed",
            "error": "Open Interpreter task is missing.",
            "notification": "",
        }

    workspace_path, validation_error = validate_open_interpreter_workspace(workspace)

    if validation_error:
        return {
            "task": None,
            "result": "",
            "success": False,
            "status": "validation_failed",
            "error": validation_error,
            "notification": "",
        }

    risk = classify_open_interpreter_risk(task)

    # --------------------------------------------------------
    # Create Managed Task
    # --------------------------------------------------------

    managed_task = task_manager.create_task(
        title=task[:80],
        agent="open_interpreter",
    )

    task_manager.start_task(managed_task.id)

    # --------------------------------------------------------
    # Execute Open Interpreter
    # --------------------------------------------------------

    result = open_interpreter.run_task(
        task=task,
        workspace=str(workspace_path),
        skip_git_repo_check=True,
    )

    # --------------------------------------------------------
    # Update Task Manager
    # --------------------------------------------------------

    if result.get("success"):
        task_manager.complete_task(
            managed_task.id,
            result=result.get(
                "result",
                "",
            ),
        )

    else:
        task_manager.fail_task(
            managed_task.id,
            error=result.get(
                "error",
                "Unknown Open Interpreter error.",
            ),
        )

    task_info = task_manager.get_task(managed_task.id)

    # --------------------------------------------------------
    # Notification
    # --------------------------------------------------------

    notification = notification_service.notify_task_status(
        status=result.get(
            "status",
            "failed",
        ),
        title=task,
        result=result.get(
            "result",
            "",
        ),
        error=result.get(
            "error",
            "",
        ),
    )

    return {
        "task": task_info,
        "risk": risk,
        "result": result.get(
            "result",
            "",
        ),
        "success": result.get(
            "success",
            False,
        ),
        "status": result.get(
            "status",
            "failed",
        ),
        "error": result.get(
            "error",
            "",
        ),
        "notification": notification,
    }


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
    "request_open_interpreter": request_open_interpreter,
    "delegate_to_open_interpreter": delegate_to_open_interpreter,
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
# Routing Helpers
# ============================================================


def user_explicitly_requested_open_interpreter(
    user_input: str,
) -> bool:
    normalized_input = user_input.strip().lower()

    open_interpreter_keywords = {
        "open interpreter",
        "用open interpreter",
        "用 open interpreter",
        "使用open interpreter",
        "使用 open interpreter",
        "交给open interpreter",
        "交给 open interpreter",
        "让open interpreter",
        "让 open interpreter",
    }

    return any(keyword in normalized_input for keyword in open_interpreter_keywords)


def user_explicitly_requested_project_scan(
    user_input: str,
) -> bool:
    normalized_input = user_input.strip().lower()

    project_scan_keywords = {
        "扫描项目",
        "扫描我的项目",
        "扫描开发项目",
        "找项目",
        "查找项目",
        "发现项目",
        "刷新项目",
        "重新扫描项目",
        "refresh project",
        "refresh projects",
        "scan project",
        "scan projects",
        "discover project",
        "discover projects",
        "find project",
        "find projects",
    }

    return any(keyword in normalized_input for keyword in project_scan_keywords)


# ============================================================
# Tool Execution
# ============================================================


def execute_tool(
    tool_call,
    user_input: str,
):
    function_name = tool_call.function.name
    arguments = tool_call.function.arguments

    # ========================================================
    # Open Interpreter Request Guard
    # ========================================================

    if function_name == "request_open_interpreter":
        task = arguments.get(
            "task",
            "",
        )

        workspace = arguments.get(
            "workspace",
            "",
        )

    risk = classify_open_interpreter_risk(task)

    # ----------------------------------------------------
    # Manual Mode
    # ----------------------------------------------------

    if OPEN_INTERPRETER_ROUTING_MODE == "manual":
        return {
            "success": False,
            "status": "manual_mode",
            "error": (
                "Open Interpreter routing is set to manual. "
                "The user must explicitly request Open Interpreter."
            ),
        }

    # ----------------------------------------------------
    # Automatic Mode + LOW Risk
    # ----------------------------------------------------

    if OPEN_INTERPRETER_ROUTING_MODE == "automatic" and risk == "low":
        return delegate_to_open_interpreter(
            task=task,
            workspace=workspace,
        )
    # ========================================================
    # Open Interpreter Delegate Guard
    # ========================================================

    if function_name == "delegate_to_open_interpreter":
        explicitly_requested = user_explicitly_requested_open_interpreter(user_input)

        task = arguments.get(
            "task",
            "",
        )

        workspace = arguments.get(
            "workspace",
            "",
        )

        risk = classify_open_interpreter_risk(task)

        # ----------------------------------------------------
        # Manual Mode
        # ----------------------------------------------------

        if OPEN_INTERPRETER_ROUTING_MODE == "manual" and not explicitly_requested:
            return {
                "success": False,
                "status": "routing_blocked",
                "error": (
                    "Open Interpreter is in manual mode. "
                    "The user did not explicitly request Open Interpreter."
                ),
            }

        # ----------------------------------------------------
        # Ask Mode
        # ----------------------------------------------------

        if OPEN_INTERPRETER_ROUTING_MODE == "ask" and not explicitly_requested:
            return request_open_interpreter(
                task=task,
                workspace=workspace,
            )

        # ----------------------------------------------------
        # Automatic Mode
        # ----------------------------------------------------

        if OPEN_INTERPRETER_ROUTING_MODE == "automatic" and risk in {
            "medium",
            "high",
        }:
            return request_open_interpreter(
                task=task,
                workspace=workspace,
            )

    # ========================================================
    # Project Registry Guard
    # ========================================================

    if function_name == "refresh_project_registry":
        if not user_explicitly_requested_project_scan(user_input):
            return {
                "success": False,
                "status": "routing_blocked",
                "error": (
                    "refresh_project_registry can only be used when "
                    "the user explicitly asks to scan, discover, "
                    "refresh, or find projects."
                ),
            }

    # ========================================================
    # Execute Tool
    # ========================================================

    function_to_call = AVAILABLE_TOOLS.get(function_name)

    print(f"\n[JARVIS Tool] {function_name}({arguments})")

    if not function_to_call:
        return f"Tool '{function_name}' is not available."

    try:
        return function_to_call(**arguments)

    except Exception as error:
        return f"Tool '{function_name}' failed: {error}"


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


# ============================================================
# Pending Open Interpreter Confirmation
# ============================================================


def handle_pending_open_interpreter_confirmation(
    user_input: str,
):
    global pending_open_interpreter_request

    if not pending_open_interpreter_request:
        return False

    normalized_input = user_input.strip().lower()

    yes_answers = {
        "yes",
        "y",
        "继续",
        "可以",
        "确认",
        "同意",
        "好",
        "好的",
        "ok",
        "okay",
    }

    no_answers = {
        "no",
        "n",
        "不要",
        "取消",
        "不同意",
        "不用",
        "算了",
    }

    # --------------------------------------------------------
    # Confirm
    # --------------------------------------------------------

    if normalized_input in yes_answers:
        pending_request = pending_open_interpreter_request

        pending_open_interpreter_request = None

        print("\nJARVIS > 已确认，正在交给 Open Interpreter 执行。")

        result = delegate_to_open_interpreter(
            task=pending_request["task"],
            workspace=pending_request["workspace"],
        )

        display_tool_result(result)

        final_result = result.get("result") or result.get("error") or "任务已结束。"

        print(
            "\nJARVIS >",
            final_result,
        )

        return True

    # --------------------------------------------------------
    # Reject
    # --------------------------------------------------------

    if normalized_input in no_answers:
        pending_open_interpreter_request = None

        print("\nJARVIS > 已取消 Open Interpreter 任务。")

        return True

    # --------------------------------------------------------
    # Invalid Confirmation
    # --------------------------------------------------------

    print("\nJARVIS > 目前有一个 Open Interpreter 任务等待确认。请回复 yes 或 no。")

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

        if handle_pending_open_interpreter_confirmation(user_input):
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
                    result = execute_tool(
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
