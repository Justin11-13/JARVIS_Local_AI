import unittest

from services.notification_service import NotificationService
from services.task_manager import TaskManager
from services.task_router import TaskRouter


class TaskRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = TaskRouter(
            task_manager=TaskManager(),
            notification_service=NotificationService(),
        )

    def test_known_read_only_native_tool_executes(self):
        result = self.router.execute_tool(
            function_name="get_system_info",
            arguments={},
            user_input="检查状态",
            available_tools={"get_system_info": lambda: "native result"},
        )
        self.assertEqual(result, "native result")

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

    def test_confirmation_required_native_tool_waits_for_confirmation(self):
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

    def test_non_gemini_external_action_waits_for_confirmation(self):
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
