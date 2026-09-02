from pathlib import Path
from typing import Callable

from services.agents.open_interpreter import OpenInterpreterAdapter
from services.notification_service import NotificationService
from services.task_manager import TaskManager


class TaskRouter:
    """Enforce tool-routing policy before a JARVIS tool is executed."""

    VALID_OPEN_INTERPRETER_MODES = {"manual", "ask", "automatic"}

    def __init__(
        self,
        routing_mode: str,
        open_interpreter: OpenInterpreterAdapter,
        task_manager: TaskManager,
        notification_service: NotificationService,
    ):
        if routing_mode not in self.VALID_OPEN_INTERPRETER_MODES:
            raise ValueError(f"Unsupported Open Interpreter routing mode: {routing_mode}")

        self.routing_mode = routing_mode
        self.open_interpreter = open_interpreter
        self.task_manager = task_manager
        self.notification_service = notification_service
        self.pending_open_interpreter_request: dict | None = None

    @staticmethod
    def validate_open_interpreter_workspace(
        workspace: str,
    ) -> tuple[Path | None, str | None]:
        workspace = workspace.strip()

        if not workspace:
            return None, "Open Interpreter workspace is missing."

        if workspace in {"/", "\\", "."}:
            return None, "Open Interpreter requires an explicit workspace directory."

        try:
            workspace_path = Path(workspace).expanduser().resolve()
        except OSError as error:
            return None, f"Invalid workspace: {error}"

        if not workspace_path.exists():
            return None, f"Workspace does not exist: {workspace_path}"

        if not workspace_path.is_dir():
            return None, f"Workspace is not a directory: {workspace_path}"

        if workspace_path == Path(workspace_path.anchor):
            return None, "Open Interpreter cannot use an entire drive as its workspace."

        return workspace_path, None

    @staticmethod
    def classify_open_interpreter_risk(task: str) -> str:
        normalized_task = task.lower()

        high_risk_keywords = {
            "删除", "delete", "remove", "erase", "wipe", "清空", "格式化",
            "format disk", "管理员", "administrator", "admin privilege",
            "registry", "注册表", "shutdown", "关机", "重启电脑",
            "restart computer", "reboot", "powershell as admin",
            "system configuration", "系统设置",
        }
        if any(keyword in normalized_task for keyword in high_risk_keywords):
            return "high"

        read_only_phrases = {
            "不要修改", "不要编辑", "不要创建", "不要写入", "不要移动",
            "不要重命名", "不要更改", "不要改变", "只读", "仅读取",
            "仅分析", "只分析", "不要做任何修改", "不要修改任何东西",
            "不要修改任何内容", "do not modify", "don't modify", "do not edit",
            "don't edit", "do not write", "read only", "read-only",
            "do not change", "don't change", "do not create",
        }
        if any(phrase in normalized_task for phrase in read_only_phrases):
            return "low"

        medium_risk_keywords = {
            "修改", "编辑", "modify", "edit", "rename", "重命名", "move",
            "移动", "create", "创建", "write", "写入", "replace", "替换",
            "install", "安装", "update file", "更新文件", "copy", "复制",
        }
        if any(keyword in normalized_task for keyword in medium_risk_keywords):
            return "medium"

        return "low"

    @staticmethod
    def user_explicitly_requested_open_interpreter(user_input: str) -> bool:
        normalized_input = user_input.strip().lower()
        keywords = {
            "open interpreter", "用open interpreter", "用 open interpreter",
            "使用open interpreter", "使用 open interpreter", "交给open interpreter",
            "交给 open interpreter", "让open interpreter", "让 open interpreter",
        }
        return any(keyword in normalized_input for keyword in keywords)

    @staticmethod
    def user_explicitly_requested_project_scan(user_input: str) -> bool:
        normalized_input = user_input.strip().lower()
        keywords = {
            "扫描项目", "扫描我的项目", "扫描开发项目", "找项目", "查找项目",
            "发现项目", "刷新项目", "重新扫描项目", "refresh project",
            "refresh projects", "scan project", "scan projects", "discover project",
            "discover projects", "find project", "find projects",
        }
        return any(keyword in normalized_input for keyword in keywords)

    def request_open_interpreter(self, task: str, workspace: str) -> dict:
        if self.routing_mode == "manual":
            return {
                "success": False,
                "status": "manual_mode",
                "error": "Open Interpreter is in manual mode. It can only be used when the user explicitly requests it.",
            }

        task = task.strip()
        if not task:
            return {
                "success": False,
                "status": "validation_failed",
                "error": "Open Interpreter task is missing.",
            }

        workspace_path, validation_error = self.validate_open_interpreter_workspace(workspace)
        if validation_error:
            return {
                "success": False,
                "status": "validation_failed",
                "error": validation_error,
            }

        risk = self.classify_open_interpreter_risk(task)
        self.pending_open_interpreter_request = {
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
            "message": f"这个 Open Interpreter 任务风险等级为 {risk.upper()}。是否继续？请回复 yes 或 no。",
        }

    def _delegate_to_open_interpreter(self, task: str, workspace: str) -> dict:
        task = task.strip()
        if not task:
            return self._execution_validation_error("Open Interpreter task is missing.")

        workspace_path, validation_error = self.validate_open_interpreter_workspace(workspace)
        if validation_error:
            return self._execution_validation_error(validation_error)

        risk = self.classify_open_interpreter_risk(task)
        managed_task = self.task_manager.create_task(title=task[:80], agent="open_interpreter")
        self.task_manager.start_task(managed_task.id)

        result = self.open_interpreter.run_task(
            task=task,
            workspace=str(workspace_path),
            skip_git_repo_check=True,
        )

        if result.get("success"):
            self.task_manager.complete_task(managed_task.id, result=result.get("result", ""))
        else:
            self.task_manager.fail_task(
                managed_task.id,
                error=result.get("error", "Unknown Open Interpreter error."),
            )

        notification = self.notification_service.notify_task_status(
            status=result.get("status", "failed"),
            title=task,
            result=result.get("result", ""),
            error=result.get("error", ""),
        )
        return {
            "task": self.task_manager.get_task(managed_task.id),
            "risk": risk,
            "result": result.get("result", ""),
            "success": result.get("success", False),
            "status": result.get("status", "failed"),
            "error": result.get("error", ""),
            "notification": notification,
        }

    @staticmethod
    def _execution_validation_error(error: str) -> dict:
        return {
            "task": None,
            "result": "",
            "success": False,
            "status": "validation_failed",
            "error": error,
            "notification": "",
        }

    def execute_tool(
        self,
        function_name: str,
        arguments: dict,
        user_input: str,
        available_tools: dict[str, Callable],
    ):
        if function_name == "request_open_interpreter":
            task = arguments.get("task", "")
            workspace = arguments.get("workspace", "")
            risk = self.classify_open_interpreter_risk(task)

            if self.routing_mode == "manual":
                return {
                    "success": False,
                    "status": "manual_mode",
                    "error": "Open Interpreter routing is set to manual. The user must explicitly request Open Interpreter.",
                }

            if self.routing_mode == "automatic" and risk == "low":
                return self._delegate_to_open_interpreter(task, workspace)

            return self.request_open_interpreter(task, workspace)

        if function_name == "delegate_to_open_interpreter":
            task = arguments.get("task", "")
            workspace = arguments.get("workspace", "")
            risk = self.classify_open_interpreter_risk(task)
            explicitly_requested = self.user_explicitly_requested_open_interpreter(user_input)

            if self.routing_mode == "manual" and not explicitly_requested:
                return {
                    "success": False,
                    "status": "routing_blocked",
                    "error": "Open Interpreter is in manual mode. The user did not explicitly request Open Interpreter.",
                }

            if self.routing_mode == "ask" and not explicitly_requested:
                return self.request_open_interpreter(task, workspace)

            if self.routing_mode == "automatic" and risk in {"medium", "high"}:
                return self.request_open_interpreter(task, workspace)

            return self._delegate_to_open_interpreter(task, workspace)

        if function_name == "refresh_project_registry" and not self.user_explicitly_requested_project_scan(user_input):
            return {
                "success": False,
                "status": "routing_blocked",
                "error": "refresh_project_registry can only be used when the user explicitly asks to scan, discover, refresh, or find projects.",
            }

        function_to_call = available_tools.get(function_name)
        if not function_to_call:
            return f"Tool '{function_name}' is not available."

        try:
            return function_to_call(**arguments)
        except Exception as error:
            return f"Tool '{function_name}' failed: {error}"

    def handle_pending_open_interpreter_confirmation(self, user_input: str) -> tuple[bool, str | None, dict | None]:
        if not self.pending_open_interpreter_request:
            return False, None, None

        normalized_input = user_input.strip().lower()
        yes_answers = {"yes", "y", "继续", "可以", "确认", "同意", "好", "好的", "ok", "okay"}
        no_answers = {"no", "n", "不要", "取消", "不同意", "不用", "算了"}

        if normalized_input in yes_answers:
            pending_request = self.pending_open_interpreter_request
            self.pending_open_interpreter_request = None
            result = self._delegate_to_open_interpreter(
                task=pending_request["task"],
                workspace=pending_request["workspace"],
            )
            return True, "已确认，正在交给 Open Interpreter 执行。", result

        if normalized_input in no_answers:
            self.pending_open_interpreter_request = None
            return True, "已取消 Open Interpreter 任务。", None

        return True, "目前有一个 Open Interpreter 任务等待确认。请回复 yes 或 no。", None
