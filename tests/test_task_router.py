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
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"], "native result")

    def test_explicit_force_confirmation_overrides_low_risk_permission(self):
        calls = []
        result = self.router.execute_tool(
            function_name="get_system_info",
            arguments={},
            user_input="Please inspect my system.",
            available_tools={"get_system_info": lambda: calls.append(True) or "telemetry"},
            force_confirmation=True,
        )

        self.assertIsNone(result["success"])
        self.assertEqual(result["status"], "awaiting_confirmation")
        self.assertEqual(calls, [])

        handled, _, confirmed = self.router.handle_pending_confirmation("yes")
        self.assertTrue(handled)
        self.assertTrue(confirmed["success"])
        self.assertEqual(calls, [True])

    def test_model_low_risk_proposal_uses_normal_permission_path(self):
        calls = []
        result = self.router.execute_tool(
            function_name="get_system_info",
            arguments={},
            user_input="Please inspect my hardware status.",
            available_tools={"get_system_info": lambda: calls.append(True) or "telemetry"},
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"], "telemetry")
        self.assertEqual(calls, [True])

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
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"], "refreshed")

    def test_confirmation_required_native_tool_waits_for_confirmation(self):
        calls = []
        result = self.router.execute_tool(
            function_name="write_file",
            arguments={"content": "safe"},
            user_input="Create the report.",
            available_tools={"write_file": lambda content: calls.append(content) or "written"},
        )
        self.assertIsNone(result["success"])
        self.assertEqual(result["status"], "awaiting_confirmation")
        self.assertEqual(result["task"]["status"], "waiting_approval")
        self.assertEqual(calls, [])

        handled, message, confirmed_result = self.router.handle_pending_confirmation("yes")
        self.assertTrue(handled)
        self.assertEqual(message, "已确认，正在执行该操作。")
        self.assertTrue(confirmed_result["success"])
        self.assertEqual(confirmed_result["status"], "completed")
        self.assertEqual(confirmed_result["result"], "written")
        self.assertEqual(confirmed_result["task"]["status"], "completed")
        self.assertEqual(calls, ["safe"])

    def test_rejected_native_confirmation_does_not_execute_tool(self):
        calls = []
        awaiting = self.router.execute_tool(
            function_name="git_push",
            arguments={},
            user_input="Push the changes.",
            available_tools={"git_push": lambda: calls.append(True) or "pushed"},
        )
        handled, message, result = self.router.handle_pending_confirmation("no")
        self.assertTrue(handled)
        self.assertEqual(message, "已取消等待确认的操作。")
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "denied")
        self.assertEqual(result["task"]["id"], awaiting["task"]["id"])
        self.assertEqual(result["task"]["status"], "denied")
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
        self.assertIsNone(result["success"])
        self.assertEqual(result["status"], "awaiting_confirmation")
        self.assertEqual(calls, [])

        handled, _, confirmed_result = self.router.handle_pending_confirmation("yes")
        self.assertTrue(handled)
        self.assertTrue(confirmed_result["success"])
        self.assertEqual(confirmed_result["task"]["status"], "completed")
        self.assertEqual(calls, [True])

    def test_unknown_tool_is_failed_instead_of_a_success_string(self):
        result = self.router.execute_tool(
            function_name="not_registered",
            arguments={},
            user_input="Do an unknown thing.",
            available_tools={},
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertIn("not available", result["error"])

    def test_native_exception_is_failed_instead_of_a_success_string(self):
        def broken_tool():
            raise RuntimeError("native exploded")

        result = self.router.execute_tool(
            function_name="get_system_info",
            arguments={},
            user_input="Check my system.",
            available_tools={"get_system_info": broken_tool},
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertIn("native exploded", result["error"])

    def test_approved_external_exception_finishes_the_waiting_task_as_failed(self):
        def broken_executor():
            raise RuntimeError("external exploded")

        awaiting = self.router.request_external_action(
            executor="chatgpt_ui",
            action="submit_prompt",
            purpose="Explain this error.",
            execute=broken_executor,
        )
        self.assertEqual(awaiting["task"]["status"], "waiting_approval")

        handled, _, result = self.router.handle_pending_confirmation("yes")

        self.assertTrue(handled)
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["task"]["status"], "failed")
        self.assertNotEqual(result["task"]["status"], "running")
        self.assertIn("external exploded", result["error"])

    def test_duplicate_confirmation_does_not_execute_the_consumed_request_twice(self):
        calls = []
        self.router.execute_tool(
            function_name="write_file",
            arguments={"content": "safe"},
            user_input="Create the report.",
            available_tools={"write_file": lambda content: calls.append(content) or "written"},
        )

        first_handled, _, first_result = self.router.handle_pending_confirmation("yes")
        second_handled, second_message, second_result = self.router.handle_pending_confirmation("yes")

        self.assertTrue(first_handled)
        self.assertTrue(first_result["success"])
        self.assertFalse(second_handled)
        self.assertIsNone(second_message)
        self.assertIsNone(second_result)
        self.assertEqual(calls, ["safe"])

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

    def test_gemini_confirmation_response_keeps_both_tasks_waiting_then_denies_them(self):
        native_awaiting = self.router.execute_tool(
            function_name="sleep_computer",
            arguments={},
            user_input="Put the computer to sleep.",
            available_tools={"sleep_computer": lambda: "slept"},
        )

        gemini_awaiting = self.router.execute_external_action(
            executor="gemini",
            action="generate_response",
            purpose="Put the computer to sleep.",
            execute=lambda: {
                "success": None,
                "status": "awaiting_confirmation",
                "result": "Please confirm.",
                "error": "",
            },
        )

        self.assertIsNone(gemini_awaiting["success"])
        self.assertEqual(gemini_awaiting["status"], "awaiting_confirmation")
        self.assertEqual(gemini_awaiting["task"]["status"], "waiting_approval")
        self.assertEqual(native_awaiting["task"]["status"], "waiting_approval")

        handled, _, denied = self.router.handle_pending_confirmation("no")

        self.assertTrue(handled)
        self.assertEqual(denied["status"], "denied")
        self.assertEqual(denied["task"]["status"], "denied")
        self.assertEqual(
            self.router.task_manager.get_task(gemini_awaiting["task"]["id"])["status"],
            "denied",
        )

    def test_gemini_confirmation_response_finishes_related_task_after_approved_failure(self):
        native_awaiting = self.router.execute_tool(
            function_name="sleep_computer",
            arguments={},
            user_input="Put the computer to sleep.",
            available_tools={"sleep_computer": lambda: (_ for _ in ()).throw(RuntimeError("sleep exploded"))},
        )
        gemini_awaiting = self.router.execute_external_action(
            executor="gemini",
            action="generate_response",
            purpose="Put the computer to sleep.",
            execute=lambda: {
                "success": None,
                "status": "awaiting_confirmation",
                "result": "Please confirm.",
                "error": "",
            },
        )

        handled, _, failed = self.router.handle_pending_confirmation("yes")

        self.assertTrue(handled)
        self.assertFalse(failed["success"])
        self.assertEqual(failed["task"]["status"], "failed")
        self.assertEqual(
            self.router.task_manager.get_task(gemini_awaiting["task"]["id"])["status"],
            "failed",
        )
        self.assertEqual(
            self.router.task_manager.get_task(native_awaiting["task"]["id"])["status"],
            "failed",
        )


if __name__ == "__main__":
    unittest.main()
