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
            "success": None,
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
        managed_task = self.task_manager.create_task(
            title=decision.request.purpose[:80],
            agent=decision.request.executor,
        )
        self.task_manager.wait_for_approval_task(managed_task.id)
        self.pending_action_request = {
            "request": decision.request,
            "task_id": managed_task.id,
            "risk": decision.risk,
            "confirmations_remaining": max(1, decision.confirmation_count),
            "execute": lambda: self._execute_confirmed_native_action(
                managed_task.id,
                function_to_call,
                arguments,
                decision.request.action,
            ),
        }
        response = self._confirmation_response(decision)
        response["task"] = self.task_manager.get_task(managed_task.id)
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
        managed_task = self.task_manager.create_task(
            title=request.purpose[:80],
            agent=request.executor,
        )
        self.task_manager.wait_for_approval_task(managed_task.id)
        self.pending_action_request = {
            "request": request,
            "task_id": managed_task.id,
            "risk": decision.risk,
            "confirmations_remaining": max(1, decision.confirmation_count),
            "execute": lambda: self._execute_external_action(
                request,
                execute,
                task_id=managed_task.id,
            ),
        }
        response = self._confirmation_response(decision)
        response["task"] = self.task_manager.get_task(managed_task.id)
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
        task_id: str | None = None,
    ) -> dict:
        if task_id is None:
            managed_task = self.task_manager.create_task(
                title=request.purpose[:80],
                agent=request.executor,
            )
            task_id = managed_task.id

        self.task_manager.start_task(task_id)
        try:
            raw_result = execute()
        except Exception as error:
            result = {
                "success": False,
                "status": "failed",
                "result": "",
                "error": f"External executor failed: {error}",
            }
        else:
            result = self._normalize_external_result(raw_result)

        if result["success"] is True and result["status"] == "completed":
            self.task_manager.complete_task(task_id, result=result["result"])
        elif result["success"] is None and result["status"] == "awaiting_confirmation":
            # A model response can be a confirmation request for a native action.
            # It is neither a completed external action nor an execution failure.
            self.task_manager.wait_for_approval_task(task_id)
            if self.pending_action_request:
                self.pending_action_request["related_task_id"] = task_id
        else:
            self.task_manager.fail_task(task_id, error=result["error"])

        notification = ""
        if result["success"] is not None:
            notification = self.notification_service.notify_task_status(
                status=result["status"],
                title=request.purpose,
                result=result["result"],
                error=result["error"],
            )
        response = {
            "task": self.task_manager.get_task(task_id),
            "success": result["success"],
            "status": result["status"],
            "result": result["result"],
            "error": result["error"],
            "executor": request.executor,
            "tool_calls": result.get("tool_calls", []),
            "notification": notification,
        }
        # Safe transport diagnostics may cross the application boundary, but
        # only as bounded metadata. User/model content and credentials remain
        # owned by their existing result fields.
        if isinstance(result.get("timings"), dict):
            response["timings"] = result["timings"]
        if isinstance(result.get("native_intent_proposal"), dict):
            # This is a bounded candidate for the application layer to validate
            # and route.  It is never an execution result or an authority grant.
            response["native_intent_proposal"] = result["native_intent_proposal"]
        return response

    @staticmethod
    def _normalize_external_result(result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            return {
                "success": False,
                "status": "failed",
                "result": "",
                "error": "External executor returned an invalid result.",
            }

        if result.get("success") is True and result.get("status") == "completed":
            return {
                **result,
                "result": str(result.get("result", "")),
                "error": str(result.get("error", "")),
            }

        status = result.get("status")
        if result.get("success") is None and status == "awaiting_confirmation":
            return {
                **result,
                "success": None,
                "status": "awaiting_confirmation",
                "result": str(result.get("result", "")),
                "error": str(result.get("error", "")),
            }

        return {
            **result,
            "success": False,
            "status": status if isinstance(status, str) else "failed",
            "result": str(result.get("result", "")),
            "error": str(result.get("error") or "External executor failed."),
        }

    @staticmethod
    def _execute_native_function(
        function_name: str,
        function_to_call: Callable,
        arguments: dict,
    ) -> dict[str, Any]:
        try:
            result = function_to_call(**arguments)
        except Exception as error:
            return {
                "tool_name": function_name,
                "success": False,
                "status": "failed",
                "result": "",
                "error": f"Tool execution failed: {error}",
            }

        if isinstance(result, dict):
            if result.get("success") is True and result.get("status") == "completed":
                return {**result, "tool_name": function_name}
            return {
                **result,
                "tool_name": function_name,
                "success": False,
                "status": result.get("status", "failed"),
                "result": str(result.get("result", "")),
                "error": str(result.get("error") or "Tool returned a failed result."),
            }

        if isinstance(result, str):
            return {
                "tool_name": function_name,
                "success": True,
                "status": "completed",
                "result": result,
                "error": "",
            }

        return {
            "tool_name": function_name,
            "success": False,
            "status": "failed",
            "result": "",
            "error": "Tool returned an invalid result.",
        }

    def _execute_confirmed_native_action(
        self,
        task_id: str,
        function_to_call: Callable,
        arguments: dict,
        function_name: str,
    ) -> dict[str, Any]:
        self.task_manager.start_task(task_id)
        result = self._execute_native_function(
            function_name,
            function_to_call,
            arguments,
        )
        if result["success"] is True and result["status"] == "completed":
            self.task_manager.complete_task(task_id, result=result["result"])
        else:
            self.task_manager.fail_task(task_id, error=result["error"])
        result["task"] = self.task_manager.get_task(task_id)
        return result

    def execute_tool(
        self,
        function_name: str,
        arguments: dict,
        user_input: str,
        available_tools: dict[str, Callable],
        *,
        force_confirmation: bool = False,
    ):
        if function_name == "refresh_project_registry" and not self.user_explicitly_requested_project_scan(user_input):
            return {
                "success": False,
                "status": "routing_blocked",
                "error": "refresh_project_registry can only be used when the user explicitly asks to scan, discover, refresh, or find projects.",
            }

        function_to_call = available_tools.get(function_name)
        if not function_to_call:
            return {
                "tool_name": function_name,
                "success": False,
                "status": "failed",
                "result": "",
                "error": f"Tool '{function_name}' is not available.",
            }

        decision = self.permission_manager.evaluate(
            ActionRequest(
                executor="native",
                action=function_name,
                purpose=user_input.strip() or function_name,
            )
        )
        # Model proposals remain untrusted: PermissionManager still owns the
        # risk decision. Low-risk candidates use the normal read-only/explicit
        # local path; medium/high-risk candidates remain awaiting confirmation.
        if force_confirmation or decision.requires_confirmation:
            return self._request_native_confirmation(decision, function_to_call, arguments)

        return self._execute_native_function(
            function_name,
            function_to_call,
            arguments,
        )

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
            self._settle_related_task(pending_request.get("related_task_id"), result)
            return True, "已确认，正在执行该操作。", result

        if normalized_input in no_answers:
            pending_request = self.pending_action_request
            self.pending_action_request = None
            task_id = pending_request.get("task_id")
            related_task_id = pending_request.get("related_task_id")
            for pending_task_id in {task_id, related_task_id} - {None}:
                self.task_manager.deny_task(pending_task_id)
            return True, "已取消等待确认的操作。", {
                "success": False,
                "status": "denied",
                "result": "",
                "error": "User denied the requested action.",
                "task": self.task_manager.get_task(task_id) if task_id else None,
            }

        return True, "目前有一个操作等待确认。请回复 yes 或 no。", None

    def _settle_related_task(self, task_id: str | None, result: Any) -> None:
        """Finish the model request that yielded the pending native action."""
        if not task_id or not isinstance(result, dict):
            return

        if result.get("success") is True and result.get("status") == "completed":
            self.task_manager.complete_task(task_id, result=str(result.get("result", "")))
        elif result.get("status") == "denied":
            self.task_manager.deny_task(task_id, error=str(result.get("error") or "User denied the requested action."))
        else:
            self.task_manager.fail_task(task_id, error=str(result.get("error") or "External executor failed."))
