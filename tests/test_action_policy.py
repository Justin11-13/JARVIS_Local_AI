import unittest

from services.permission_manager import ActionRequest, PermissionManager


class PermissionManagerTests(unittest.TestCase):
    def setUp(self):
        self.policy = PermissionManager()

    def test_read_only_native_action_is_allowed(self):
        decision = self.policy.evaluate(
            ActionRequest("native", "read_file", "Read a registered project file.")
        )

        self.assertEqual(decision.risk, "low")
        self.assertFalse(decision.requires_confirmation)

    def test_file_write_requires_confirmation(self):
        decision = self.policy.evaluate(
            ActionRequest("native", "write_file", "Create a report file.")
        )

        self.assertEqual(decision.risk, "medium")
        self.assertTrue(decision.requires_confirmation)

    def test_delete_and_admin_actions_require_high_risk_confirmation(self):
        for action in ("delete_file", "admin_command"):
            with self.subTest(action=action):
                decision = self.policy.evaluate(ActionRequest("native", action, action))
                self.assertEqual(decision.risk, "high")
                self.assertTrue(decision.requires_confirmation)
                self.assertEqual(decision.confirmation_count, 1)

    def test_git_commit_and_push_require_confirmation(self):
        for action in ("git_commit", "git_push"):
            with self.subTest(action=action):
                decision = self.policy.evaluate(ActionRequest("native", action, action))
                self.assertTrue(decision.requires_confirmation)

    def test_chatgpt_and_codex_actions_require_confirmation(self):
        for executor in ("chatgpt_ui", "codex"):
            with self.subTest(executor=executor):
                decision = self.policy.evaluate(
                    ActionRequest(executor, "submit_task", "Send the approved prompt.", "external")
                )
                self.assertTrue(decision.requires_confirmation)

    def test_user_authored_gemini_chat_does_not_need_second_confirmation(self):
        decision = self.policy.evaluate(
            ActionRequest("gemini", "generate_response", "Explain this error.", "external_submission")
        )

        self.assertEqual(decision.risk, "low")
        self.assertFalse(decision.requires_confirmation)

    def test_power_actions_require_one_confirmation(self):
        for action in ("shutdown_computer", "restart_computer", "sleep_computer"):
            with self.subTest(action=action):
                decision = self.policy.evaluate(ActionRequest("native", action, action))
                self.assertEqual(decision.risk, "high")
                self.assertEqual(decision.confirmation_count, 1)

    def test_unknown_action_is_never_allowed_by_default(self):
        decision = self.policy.evaluate(ActionRequest("native", "unknown_action", "Do something."))

        self.assertEqual(decision.risk, "high")
        self.assertTrue(decision.requires_confirmation)


if __name__ == "__main__":
    unittest.main()
