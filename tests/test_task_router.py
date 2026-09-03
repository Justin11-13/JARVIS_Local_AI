import tempfile
import unittest
from pathlib import Path

from services.notification_service import NotificationService
from services.task_manager import TaskManager
from services.task_router import TaskRouter


class FakeOpenInterpreter:
    def __init__(self):
        self.calls = []

    def run_task(self, task: str, workspace: str, skip_git_repo_check: bool) -> dict:
        self.calls.append(
            {
                "task": task,
                "workspace": workspace,
                "skip_git_repo_check": skip_git_repo_check,
            }
        )
        return {
            "success": True,
            "status": "completed",
            "result": "done",
            "error": "",
        }


class TaskRouterTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.adapter = FakeOpenInterpreter()
        self.router = TaskRouter(
            routing_mode="automatic",
            open_interpreter=self.adapter,
            task_manager=TaskManager(),
            notification_service=NotificationService(),
        )

    def tearDown(self):
        self.workspace.cleanup()

    def test_invalid_routing_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            TaskRouter(
                routing_mode="unrestricted",
                open_interpreter=FakeOpenInterpreter(),
                task_manager=TaskManager(),
                notification_service=NotificationService(),
            )

    @property
    def workspace_path(self) -> str:
        return self.workspace.name

    def test_high_risk_overrides_read_only_language(self):
        risk = self.router.classify_open_interpreter_risk(
            "Do not modify anything, but delete the temporary files."
        )

        self.assertEqual(risk, "high")

    def test_explicit_read_only_language_is_low_risk(self):
        risk = self.router.classify_open_interpreter_risk(
            "分析这个目录，不要修改任何东西。"
        )

        self.assertEqual(risk, "low")

    def test_known_read_only_native_tool_does_not_require_open_interpreter_arguments(self):
        result = self.router.execute_tool(
            function_name="get_system_info",
            arguments={},
            user_input="检查状态",
            available_tools={"get_system_info": lambda: "native result"},
        )

        self.assertEqual(result, "native result")

    def test_automatic_low_risk_request_executes_immediately(self):
        result = self.router.execute_tool(
            function_name="request_open_interpreter",
            arguments={
                "task": "List the files. Do not modify anything.",
                "workspace": self.workspace_path,
            },
            user_input="分析这个资料夹",
            available_tools={},
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(self.adapter.calls), 1)

    def test_automatic_medium_risk_requires_confirmation(self):
        result = self.router.execute_tool(
            function_name="delegate_to_open_interpreter",
            arguments={
                "task": "Create a summary file.",
                "workspace": self.workspace_path,
            },
            user_input="整理这个资料夹",
            available_tools={},
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "awaiting_confirmation")
        self.assertEqual(len(self.adapter.calls), 0)

    def test_high_risk_open_interpreter_task_requires_one_confirmation(self):
        result = self.router.execute_tool(
            function_name="delegate_to_open_interpreter",
            arguments={
                "task": "Delete temporary files.",
                "workspace": self.workspace_path,
            },
            user_input="Use Open Interpreter to delete temporary files.",
            available_tools={},
        )

        self.assertEqual(result["confirmation_count"], 1)
        self.assertEqual(len(self.adapter.calls), 0)
        _, _, final_result = self.router.handle_pending_confirmation("yes")
        self.assertTrue(final_result["success"])
        self.assertEqual(len(self.adapter.calls), 1)

    def test_current_directory_cannot_be_open_interpreter_workspace(self):
        result = self.router.execute_tool(
            function_name="request_open_interpreter",
            arguments={
                "task": "List the files. Do not modify anything.",
                "workspace": ".",
            },
            user_input="分析这个资料夹",
            available_tools={},
        )

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(len(self.adapter.calls), 0)

    def test_missing_directory_cannot_be_open_interpreter_workspace(self):
        missing_workspace = f"{self.workspace_path}\\missing"

        result = self.router.execute_tool(
            function_name="request_open_interpreter",
            arguments={
                "task": "List the files. Do not modify anything.",
                "workspace": missing_workspace,
            },
            user_input="分析这个资料夹",
            available_tools={},
        )

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(len(self.adapter.calls), 0)

    def test_drive_root_cannot_be_open_interpreter_workspace(self):
        drive_root = Path(self.workspace_path).anchor

        result = self.router.execute_tool(
            function_name="request_open_interpreter",
            arguments={
                "task": "List the files. Do not modify anything.",
                "workspace": drive_root,
            },
            user_input="分析这个资料夹",
            available_tools={},
        )

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(len(self.adapter.calls), 0)

    def test_ask_mode_non_explicit_delegation_requires_confirmation(self):
        self.router.routing_mode = "ask"

        result = self.router.execute_tool(
            function_name="delegate_to_open_interpreter",
            arguments={
                "task": "List the files.",
                "workspace": self.workspace_path,
            },
            user_input="分析这个资料夹",
            available_tools={},
        )

        self.assertEqual(result["status"], "awaiting_confirmation")
        self.assertEqual(len(self.adapter.calls), 0)

    def test_manual_mode_blocks_non_explicit_delegation(self):
        self.router.routing_mode = "manual"

        result = self.router.execute_tool(
            function_name="delegate_to_open_interpreter",
            arguments={
                "task": "List the files.",
                "workspace": self.workspace_path,
            },
            user_input="分析这个资料夹",
            available_tools={},
        )

        self.assertEqual(result["status"], "routing_blocked")
        self.assertEqual(len(self.adapter.calls), 0)

    def test_manual_mode_allows_explicit_delegation(self):
        self.router.routing_mode = "manual"

        result = self.router.execute_tool(
            function_name="delegate_to_open_interpreter",
            arguments={
                "task": "List the files. Do not modify anything.",
                "workspace": self.workspace_path,
            },
            user_input="Use Open Interpreter to list the files.",
            available_tools={},
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(self.adapter.calls), 1)

    def test_confirmation_executes_saved_request(self):
        self.router.request_open_interpreter(
            task="Create a summary file.",
            workspace=self.workspace_path,
        )

        handled, message, result = (
            self.router.handle_pending_open_interpreter_confirmation("确认")
        )

        self.assertTrue(handled)
        self.assertEqual(message, "已确认，正在交给 Open Interpreter 执行。")
        self.assertTrue(result["success"])
        self.assertEqual(len(self.adapter.calls), 1)
        self.assertIsNone(self.router.pending_open_interpreter_request)

    def test_rejection_clears_saved_request_without_execution(self):
        self.router.request_open_interpreter(
            task="Create a summary file.",
            workspace=self.workspace_path,
        )

        handled, message, result = (
            self.router.handle_pending_open_interpreter_confirmation("取消")
        )

        self.assertTrue(handled)
        self.assertEqual(message, "已取消 Open Interpreter 任务。")
        self.assertIsNone(result)
        self.assertEqual(len(self.adapter.calls), 0)
        self.assertIsNone(self.router.pending_open_interpreter_request)

    def test_project_refresh_requires_explicit_scan_intent(self):
        result = self.router.execute_tool(
            function_name="refresh_project_registry",
            arguments={},
            user_input="这是一个目录 C:\\work",
            available_tools={"refresh_project_registry": lambda: "refreshed"},
        )

        self.assertEqual(result["status"], "routing_blocked")

    def test_project_refresh_allows_explicit_scan_intent(self):
        result = self.router.execute_tool(
            function_name="refresh_project_registry",
            arguments={},
            user_input="请重新扫描我的项目",
            available_tools={"refresh_project_registry": lambda: "refreshed"},
        )

        self.assertEqual(result, "refreshed")

    def test_confirmation_required_native_tool_does_not_execute_until_confirmed(self):
        calls = []
        result = self.router.execute_tool(
            function_name="write_file",
            arguments={"content": "safe"},
            user_input="Create the report.",
            available_tools={"write_file": lambda content: calls.append(content) or "written"},
        )

        self.assertEqual(result["status"], "awaiting_confirmation")
        self.assertEqual(calls, [])

        handled, message, confirmed_result = self.router.handle_pending_confirmation("yes")

        self.assertTrue(handled)
        self.assertEqual(message, "已确认，正在执行该操作。")
        self.assertEqual(confirmed_result, "written")
        self.assertEqual(calls, ["safe"])

    def test_rejected_native_confirmation_does_not_execute_tool(self):
        calls = []
        self.router.execute_tool(
            function_name="git_push",
            arguments={},
            user_input="Push the changes.",
            available_tools={"git_push": lambda: calls.append(True) or "pushed"},
        )

        handled, message, result = self.router.handle_pending_confirmation("no")

        self.assertTrue(handled)
        self.assertEqual(message, "已取消等待确认的操作。")
        self.assertIsNone(result)
        self.assertEqual(calls, [])

    def test_high_risk_native_tool_requires_one_confirmation_before_execution(self):
        calls = []
        result = self.router.execute_tool(
            function_name="delete_file",
            arguments={"path": "important.txt"},
            user_input="Delete the file.",
            available_tools={"delete_file": lambda path: calls.append(path) or "deleted"},
        )

        self.assertEqual(result["confirmation_count"], 1)
        self.assertEqual(calls, [])

        handled, message, final_result = self.router.handle_pending_confirmation("是的")
        self.assertTrue(handled)
        self.assertEqual(message, "已确认，正在执行该操作。")
        self.assertEqual(final_result, "deleted")
        self.assertEqual(calls, ["important.txt"])

    def test_legacy_open_interpreter_confirmation_method_still_works(self):
        self.router.request_open_interpreter(
            task="Create a summary file.",
            workspace=self.workspace_path,
        )

        handled, message, result = self.router.handle_pending_open_interpreter_confirmation("取消")

        self.assertTrue(handled)
        self.assertEqual(message, "已取消 Open Interpreter 任务。")
        self.assertIsNone(result)

    def test_non_gemini_external_action_sends_nothing_until_confirmation(self):
        calls = []
        result = self.router.request_external_action(
            executor="chatgpt_ui",
            action="submit_prompt",
            purpose="Explain this error.",
            execute=lambda: calls.append(True) or {
                "success": True,
                "status": "completed",
                "result": "Explanation",
                "error": "",
            },
        )

        self.assertEqual(result["status"], "awaiting_confirmation")
        self.assertEqual(result["submission_preview"], "Explain this error.")
        self.assertEqual(calls, [])

        handled, _, confirmed_result = self.router.handle_pending_confirmation("yes")

        self.assertTrue(handled)
        self.assertTrue(confirmed_result["success"])
        self.assertEqual(calls, [True])

    def test_gemini_text_action_executes_without_second_confirmation(self):
        calls = []
        result = self.router.execute_external_action(
            executor="gemini",
            action="generate_response",
            purpose="Explain this error.",
            execute=lambda: calls.append(True) or {
                "success": True,
                "status": "completed",
                "result": "Explanation",
                "error": "",
            },
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"], "Explanation")
        self.assertEqual(calls, [True])


if __name__ == "__main__":
    unittest.main()
