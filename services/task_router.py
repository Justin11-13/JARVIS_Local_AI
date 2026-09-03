from pathlib import Path
from typing import Any, Callable

from services.agents.open_interpreter import OpenInterpreterAdapter
from services.permission_manager import ActionRequest, PermissionDecision, PermissionManager
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
        self.permission_manager = PermissionManager()
        self.pending_action_request: dict[str, Any] | None = None
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
        confirmation_count = 1
        pending_request = {
            "task": task,
            "workspace": str(workspace_path),
            "risk": risk,
        }
        self.pending_open_interpreter_request = pending_request
        self.pending_action_request = {
            "request": ActionRequest(
                executor="open_interpreter",
                action="delegate_to_open_interpreter",
                purpose=task,
                data_scope="approved_workspace",
            ),
            "risk": risk,
            "confirmations_remaining": confirmation_count,
            "execute": lambda: self._delegate_to_open_interpreter(
                task=task,
                workspace=str(workspace_path),
            ),
        }

        return {
            "success": True,
            "status": "awaiting_confirmation",
            "task": task,
            "workspace": str(workspace_path),
            "risk": risk,
            "confirmation_count": confirmation_count,
            "confirmation_step": 1,
            "message": (
                f"这个 Open Interpreter 任务风险等级为 {risk.upper()}。是否继续？请回复 yes 或 no。"
            ),
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

    @staticmethod
    def _confirmation_response(decision: PermissionDecision) -> dict:
        required_count = max(1, decision.confirmation_count)
        confirmation_message = "此操作需要确认。是否继续？请回复 yes 或 no。"
        return {
            "success": True,
            "status": "awaiting_confirmation",
            "risk": decision.risk,
            "action": decision.request.action,
            "executor": decision.request.executor,
            "data_scope": decision.request.data_scope,
            "requires_confirmation": True,
            "confirmation_count": required_count,
            "confirmation_step": 1,
            "audit_summary": decision.audit_summary,
            "message": confirmation_message,
        }

    def _request_native_confirmation(
        self,
        decision: PermissionDecision,
        function_to_call: Callable,
        arguments: dict,
    ) -> dict:
        self.pending_action_request = {
            "request": decision.request,
            "risk": decision.risk,
            "confirmations_remaining": max(1, decision.confirmation_count),
            "execute": lambda: self._execute_native_function(function_to_call, arguments),
        }
        self.pending_open_interpreter_request = None
        return self._confirmation_response(decision)

    def request_external_action(
        self,
        executor: str,
        action: str,
        purpose: str,
        execute: Callable[[], dict],
    ) -> dict:
        """Require consent before any user text is submitted to an external service."""
        request = ActionRequest(
            executor=executor,
            action=action,
            purpose=purpose,
            data_scope="external_submission",
        )
        decision = self.permission_manager.evaluate(request)
        self.pending_action_request = {
            "request": request,
            "risk": decision.risk,
            "confirmations_remaining": max(1, decision.confirmation_count),
            "execute": lambda: self._execute_external_action(request, execute),
        }
        self.pending_open_interpreter_request = None

        response = self._confirmation_response(decision)
        response["submission_preview"] = purpose
        response["message"] = (
            f"这段文字会发送到 {executor.title()} 进行理解；未包含本地文件或系统资料。"
            "是否继续？请回复 yes 或 no。"
        )
        return response

    def execute_external_action(
        self,
        executor: str,
        action: str,
        purpose: str,
        execute: Callable[[], dict],
    ) -> dict:
        """Run an external action only when the policy permits it directly."""
        request = ActionRequest(
            executor=executor,
            action=action,
            purpose=purpose,
            data_scope="external_submission",
        )
        decision = self.permission_manager.evaluate(request)
        if decision.requires_confirmation:
            return self.request_external_action(executor, action, purpose, execute)

        return self._execute_external_action(request, execute)

    def _execute_external_action(
        self,
        request: ActionRequest,
        execute: Callable[[], dict],
    ) -> dict:
        managed_task = self.task_manager.create_task(title=request.purpose[:80], agent=request.executor)
        self.task_manager.start_task(managed_task.id)
        result = execute()

        if result.get("success"):
            self.task_manager.complete_task(managed_task.id, result=result.get("result", ""))
        else:
            self.task_manager.fail_task(
                managed_task.id,
                error=result.get("error", "External executor failed."),
            )

        notification = self.notification_service.notify_task_status(
            status=result.get("status", "failed"),
            title=request.purpose,
            result=result.get("result", ""),
            error=result.get("error", ""),
        )
        return {
            "task": self.task_manager.get_task(managed_task.id),
            "success": result.get("success", False),
            "status": result.get("status", "failed"),
            "result": result.get("result", ""),
            "error": result.get("error", ""),
            "executor": request.executor,
            "tool_calls": result.get("tool_calls", []),
            "notification": notification,
        }

    @staticmethod
    def _execute_native_function(function_to_call: Callable, arguments: dict):
        try:
            return function_to_call(**arguments)
        except Exception as error:
            return f"Tool execution failed: {error}"

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

        decision = self.permission_manager.evaluate(
            ActionRequest(
                executor="native",
                action=function_name,
                purpose=user_input.strip() or function_name,
            )
        )
        if decision.requires_confirmation:
            return self._request_native_confirmation(decision, function_to_call, arguments)

        return self._execute_native_function(function_to_call, arguments)

    def handle_pending_confirmation(self, user_input: str) -> tuple[bool, str | None, Any | None]:
        """Apply a yes/no reply to the one action currently awaiting approval."""
        if not self.pending_action_request:
            return False, None, None

        normalized_input = user_input.strip().lower()
        yes_answers = {"yes", "y", "是", "是的", "继续", "可以", "确认", "同意", "好", "好的", "ok", "okay"}
        no_answers = {"no", "n", "不要", "取消", "不同意", "不用", "算了"}

        if normalized_input in yes_answers:
            pending_request = self.pending_action_request
            request = pending_request["request"]
            is_open_interpreter = request.executor == "open_interpreter"
            confirmations_remaining = pending_request.get("confirmations_remaining", 1)
            if confirmations_remaining > 1:
                pending_request["confirmations_remaining"] = confirmations_remaining - 1
                return True, "该操作仍需要确认。是否继续？请回复 yes 或 no。", None
            self.pending_action_request = None
            self.pending_open_interpreter_request = None
            result = pending_request["execute"]()
            if is_open_interpreter:
                return True, "已确认，正在交给 Open Interpreter 执行。", result
            return True, "已确认，正在执行该操作。", result

        if normalized_input in no_answers:
            request = self.pending_action_request["request"]
            self.pending_action_request = None
            self.pending_open_interpreter_request = None
            if request.executor == "open_interpreter":
                return True, "已取消 Open Interpreter 任务。", None
            return True, "已取消等待确认的操作。", None

        request = self.pending_action_request["request"]
        if request.executor == "open_interpreter":
            return True, "目前有一个 Open Interpreter 任务等待确认。请回复 yes 或 no。", None
        return True, "目前有一个操作等待确认。请回复 yes 或 no。", None

    def handle_pending_open_interpreter_confirmation(
        self,
        user_input: str,
    ) -> tuple[bool, str | None, Any | None]:
        """Backward-compatible name for the former Open Interpreter-only flow."""
        return self.handle_pending_confirmation(user_input)
