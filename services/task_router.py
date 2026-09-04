from typing import Any, Callable

from services.permission_manager import ActionRequest, PermissionDecision, PermissionManager
from services.notification_service import NotificationService
from services.task_manager import TaskManager


class TaskRouter:
    """Enforce tool-routing policy before a JARVIS tool is executed."""

    def __init__(
        self,
        task_manager: TaskManager,
        notification_service: NotificationService,
    ):
        self.task_manager = task_manager
        self.notification_service = notification_service
        self.permission_manager = PermissionManager()
        self.pending_action_request: dict[str, Any] | None = None

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
        response = self._confirmation_response(decision)
        if decision.request.action in {"create_obsidian_note", "append_obsidian_note", "update_obsidian_note"}:
            preview = str(arguments.get("content") or arguments.get("replacement_text") or "")
            response["submission_preview"] = preview[:2000]
            response["message"] = (
                f"Obsidian write preview\nVault: {arguments.get('vault_id', '')}\n"
                f"Path: {arguments.get('relative_path', '')}\n\n{preview[:2000]}\n\n"
                "Confirm this local note change? Reply yes or no."
            )
        return response

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
            confirmations_remaining = pending_request.get("confirmations_remaining", 1)
            if confirmations_remaining > 1:
                pending_request["confirmations_remaining"] = confirmations_remaining - 1
                return True, "该操作仍需要确认。是否继续？请回复 yes 或 no。", None
            self.pending_action_request = None
            result = pending_request["execute"]()
            return True, "已确认，正在执行该操作。", result

        if normalized_input in no_answers:
            self.pending_action_request = None
            return True, "已取消等待确认的操作。", None

        return True, "目前有一个操作等待确认。请回复 yes 或 no。", None
