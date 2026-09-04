import unittest
from unittest.mock import patch

from app.api import (
    ChatRequest,
    _execute_gemini_safe_tool,
    chat_with_jarvis,
    fast_reply,
    plain_display_text,
    split_reply_for_speech,
)
from app.main import task_router
from services.jarvis_memory import JarvisMemory


class ApiFastReplyTests(unittest.TestCase):
    def setUp(self):
        memory_patch = patch("app.api.jarvis_memory", JarvisMemory(max_turns=20))
        memory_patch.start()
        self.addCleanup(memory_patch.stop)

    def test_exact_greeting_uses_the_local_fast_path(self):
        self.assertEqual(fast_reply("  你好  "), "你好！我是 JARVIS。有什么可以帮你？")

    def test_question_stays_on_the_codex_migration_path(self):
        self.assertIsNone(fast_reply("你好，你可以做什么？"))

    def test_reply_protocol_keeps_display_and_english_narration_separate(self):
        display, speech = split_reply_for_speech(
            "[DISPLAY]\n您好。\n[VOICE_EN]\nHello."
        )

        self.assertEqual(display, "您好。")
        self.assertEqual(speech, "Hello.")

    def test_display_text_removes_markdown_emphasis_but_preserves_code(self):
        display = plain_display_text(
            "***System management***\n* Check CPU\n```python\nvalue = ** 2\n```"
        )

        self.assertIn("System management", display)
        self.assertIn("• Check CPU", display)
        self.assertNotIn("***System", display)
        self.assertIn("value = ** 2", display)

    def test_fast_path_needs_no_reasoning_backend(self):
        result = chat_with_jarvis(ChatRequest(message="hello"))

        self.assertEqual(result["tool_results"], [])
        self.assertIn("JARVIS", result["reply"])

    @patch("app.api.gemini")
    def test_capability_question_is_an_immediate_bilingual_fast_reply(self, gemini):
        result = chat_with_jarvis(ChatRequest(message="你能做什么？"))

        self.assertIn("CPU", result["reply"])
        self.assertIn("I can check CPU", result["speech"])
        self.assertEqual(result["tool_results"], [])
        gemini.generate_response.assert_not_called()

    def test_chat_history_returns_completed_local_turns(self):
        from app.api import chat_history

        chat_with_jarvis(ChatRequest(message="hello"))

        history = chat_history()["turns"]
        self.assertEqual(history[0]["user"], "hello")
        self.assertIn("JARVIS", history[0]["assistant"])

    @patch("app.api.gemini")
    def test_unconfigured_gemini_does_not_send_general_chat(self, gemini):
        gemini.is_configured.return_value = False

        result = chat_with_jarvis(ChatRequest(message="检查我的项目"))

        self.assertEqual(result["tool_results"], [])
        self.assertIn("Gemini", result["reply"])

    @patch("app.api._execute_native_tool")
    def test_known_safe_chat_request_uses_native_tool(self, execute_native_tool):
        execute_native_tool.return_value = {"result": "CPU usage: 10%. Memory usage: 20%."}

        result = chat_with_jarvis(ChatRequest(message="我的 CPU 和 RAM 现在用了多少？"))

        execute_native_tool.assert_called_once_with(
            "get_system_info",
            {},
            "我的 CPU 和 RAM 现在用了多少？",
        )
        self.assertEqual(result["reply"], "CPU usage: 10%. Memory usage: 20%.")
        self.assertEqual(len(result["tool_results"]), 1)

    @patch("app.api.gemini")
    def test_unmatched_chat_sends_user_text_to_configured_gemini(self, gemini):
        gemini.is_configured.return_value = True
        gemini.generate_response.return_value = {
            "success": True,
            "status": "completed",
            "result": "[DISPLAY]\n这是 Gemini 的回答。\n[VOICE_EN]\nThis is Gemini's answer.",
            "error": "",
        }

        result = chat_with_jarvis(ChatRequest(message="帮我解释这个 Python error"))

        gemini.generate_response.assert_called_once()
        args, kwargs = gemini.generate_response.call_args
        self.assertEqual(args, ("帮我解释这个 Python error",))
        self.assertTrue(callable(kwargs["execute_tool"]))
        self.assertEqual(result["reply"], "这是 Gemini 的回答。")
        self.assertEqual(result["speech"], "This is Gemini's answer.")
        self.assertEqual(result["tool_results"][0]["status"], "completed")
        task_router.pending_action_request = None

    @patch("app.api._execute_native_tool")
    def test_gemini_safe_tool_allows_only_exact_registered_project_arguments(self, execute_native_tool):
        execute_native_tool.return_value = {"success": True, "status": "completed", "result": "Clean."}

        result = _execute_gemini_safe_tool(
            "git_status",
            {"project_name": "JARVIS"},
            "Is JARVIS clean?",
        )

        execute_native_tool.assert_called_once_with(
            "git_status",
            {"project_name": "JARVIS"},
            "Is JARVIS clean?",
        )
        self.assertTrue(result["success"])

    @patch("app.api._execute_native_tool")
    def test_gemini_local_tool_can_read_a_registered_project_file(self, execute_native_tool):
        execute_native_tool.return_value = {"success": True, "status": "completed", "result": "print('hello')"}

        result = _execute_gemini_safe_tool(
            "read_file",
            {"project_name": "JARVIS", "relative_path": "app/main.py"},
            "Explain app/main.py",
        )

        execute_native_tool.assert_called_once_with(
            "read_file",
            {"project_name": "JARVIS", "relative_path": "app/main.py"},
            "Explain app/main.py",
        )
        self.assertEqual(result["result"], "print('hello')")

    @patch("app.api._execute_native_tool")
    def test_gemini_local_tool_blocks_secret_files_and_redacts_common_secret_values(self, execute_native_tool):
        blocked = _execute_gemini_safe_tool(
            "read_file",
            {"project_name": "JARVIS", "relative_path": ".env"},
            "Read the environment file",
        )
        self.assertEqual(blocked["status"], "routing_blocked")
        execute_native_tool.assert_not_called()

        execute_native_tool.return_value = {
            "success": True,
            "status": "completed",
            "result": "API_KEY=do-not-send\npassword: also-do-not-send",
        }
        redacted = _execute_gemini_safe_tool(
            "read_file",
            {"project_name": "JARVIS", "relative_path": "example.txt"},
            "Read the example",
        )
        self.assertIn("[REDACTED]", redacted["result"])
        self.assertNotIn("do-not-send", redacted["result"])

    @patch("app.api._execute_native_tool")
    def test_gemini_safe_tool_blocks_file_and_write_proposals(self, execute_native_tool):
        result = _execute_gemini_safe_tool(
            "delete_file",
            {"path": "important.txt"},
            "Delete this file",
        )

        execute_native_tool.assert_not_called()
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "routing_blocked")

    @patch("app.api._execute_native_tool")
    def test_gemini_safe_tool_rejects_extra_arguments(self, execute_native_tool):
        result = _execute_gemini_safe_tool(
            "list_projects",
            {"include_paths": True},
            "Show my projects",
        )

        execute_native_tool.assert_not_called()
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "validation_failed")


if __name__ == "__main__":
    unittest.main()
