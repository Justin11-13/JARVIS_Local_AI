import unittest

from app.api import ChatRequest, chat_with_jarvis, fast_reply


class ApiFastReplyTests(unittest.TestCase):
    def test_exact_greeting_uses_the_local_fast_path(self):
        self.assertEqual(fast_reply("  你好  "), "你好！我是 JARVIS。有什么可以帮你的吗？")

    def test_question_stays_on_the_codex_migration_path(self):
        self.assertIsNone(fast_reply("你好，你可以做什么？"))

    def test_fast_path_needs_no_reasoning_backend(self):
        result = chat_with_jarvis(ChatRequest(message="hello"))

        self.assertEqual(result["tool_results"], [])
        self.assertIn("JARVIS", result["reply"])

    def test_general_chat_does_not_fall_back_to_a_local_model(self):
        result = chat_with_jarvis(ChatRequest(message="检查我的项目"))

        self.assertEqual(result["tool_results"], [])
        self.assertIn("Codex", result["reply"])


if __name__ == "__main__":
    unittest.main()
