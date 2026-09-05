"""Exercise real note tools through chat policy, without Windows or cloud effects."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.api import ChatRequest, chat_with_jarvis, _execute_gemini_safe_tool
from services.jarvis_memory import JarvisMemory
from services.notification_service import NotificationService
from services.task_manager import TaskManager
from services.task_router import TaskRouter


class NoteConversationApiTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.memory = JarvisMemory()
        self.router = TaskRouter(TaskManager(), NotificationService())
        vault = {"id": "test", "name": "Test", "path": self.root, "default_access": "excluded"}
        for target, value in (("app.api.jarvis_memory", self.memory), ("app.api.task_router", self.router)):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch("skills.obsidian.load_obsidian_vaults", return_value=[vault])
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("app.api.gemini")
        self.gemini = patcher.start()
        self.addCleanup(patcher.stop)
        self.gemini.is_configured.return_value = True
        self.gemini.generate_response.return_value = {"success": True, "status": "completed", "result": "Explanation", "error": ""}

    def note(self, name, content, access="rag"):
        path = self.root / (name + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\njarvis_access: {access}\n---\n{content}", encoding="utf-8")
        return path

    def chat(self, text):
        return chat_with_jarvis(ChatRequest(message=text))

    def test_search_read_followup_explanation_uses_fresh_same_note(self):
        path = self.note("Python", "First Python text")
        self.assertIn("First Python text", self.chat("帮我找python教程")["reply"])
        path.write_text("---\njarvis_access: rag\n---\nUpdated Python text", encoding="utf-8")
        self.assertIn("Updated Python text", self.chat("你不能读取?")["reply"])
        self.chat("继续解释")
        args, kwargs = self.gemini.generate_response.call_args
        self.assertIn("Updated Python text", args[0])
        self.assertIn("test:Python.md", args[0])
        self.assertIsNone(kwargs["execute_tool"])

    def test_multiple_matches_wait_for_selection_and_block_model_guess(self):
        self.note("Python A", "First")
        self.note("Python B", "Second")
        response = self.chat("帮我找Python教程")
        self.assertIn("回复编号", response["reply"])
        self.assertEqual(len(response["tool_results"]), 1)
        blocked = _execute_gemini_safe_tool("read_obsidian_note", {"vault_id": "test", "relative_path": "Python A.md"}, "find Python")
        self.assertEqual(blocked["status"], "selection_required")
        self.assertIn("回复编号", self.chat("99")["reply"])
        self.assertIn("Second", self.chat("第二个")["reply"])
        self.assertIn("Second", self.chat("读一下")["reply"])
        self.assertIn("First", self.chat("第一个")["reply"])
        self.gemini.generate_response.assert_not_called()

    @patch("skills.obsidian.os.startfile")
    def test_open_tutorial_never_launches_app_and_followup_reads(self, startfile):
        self.note("Python", "Actual body")
        response = self.chat("open the python tutorial")
        self.assertIn("Opened", response["reply"])
        startfile.assert_called_once()
        self.assertTrue(startfile.call_args.args[0].startswith("obsidian://"))
        self.assertIn("Actual body", self.chat("read it")["reply"])

    @patch("skills.system.refresh_registry")
    @patch("skills.system.find_app", return_value=None)
    @patch("skills.obsidian.os.startfile")
    def test_missing_app_reports_failure_and_offers_note_without_opening(self, startfile, find, refresh):
        self.note("Python", "A note")
        response = self.chat("open Python")
        self.assertEqual(response["tool_results"][0]["status"], "failed")
        self.assertIn("回复编号", response["reply"])
        startfile.assert_not_called()
        self.chat("1")
        startfile.assert_called_once()

    def test_revoked_note_is_not_read_from_old_context(self):
        self.note("Python", "Shared text")
        self.chat("find Python tutorial")
        self.note("Python", "NEW PRIVATE TEXT", "local-only")
        response = self.chat("read it")
        self.assertNotIn("NEW PRIVATE TEXT", str(response))
        self.assertEqual(response["tool_results"][0]["status"], "failed")
        self.assertIsNone(self.memory.notes.selected)

    @patch("skills.system.refresh_registry")
    @patch("skills.system.find_app", return_value=None)
    def test_model_application_failure_also_offers_bounded_recovery(self, find, refresh):
        self.note("Python", "A note")
        result = _execute_gemini_safe_tool("open_app", {"app": "Python"}, "Could you launch Python please")
        self.assertEqual(result["status"], "failed")
        self.assertIn("回复编号", result["error"])
        self.assertIsNone(self.memory.notes.selected)
        blocked = _execute_gemini_safe_tool("read_obsidian_note", {"vault_id": "test", "relative_path": "Python.md"}, "open Python")
        self.assertEqual(blocked["status"], "selection_required")

    def test_moved_note_is_rediscovered_but_not_silently_substituted(self):
        path = self.note("Python", "Original")
        self.chat("find Python tutorial")
        folder = self.root / "Moved"
        folder.mkdir()
        path.rename(folder / "Python.md")
        response = self.chat("read it")
        self.assertIn("回复编号", response["reply"])
        self.assertEqual(response["tool_results"][0]["status"], "failed")
        self.assertIn("Original", self.chat("1")["reply"])

    def test_missing_phrase_retries_topic_once_and_new_search_replaces_context(self):
        self.note("Python", "Python content")
        response = self.chat("find Python beginner tutorial")
        self.assertEqual(len(response["tool_results"]), 2)
        self.assertIn("改用", response["reply"])
        self.assertIn("Python content", self.chat("1")["reply"])
        self.chat("find Rust tutorial")
        self.assertIn("没有确定", self.chat("read it")["reply"])

    def test_cancel_clear_and_expiry_remove_targets(self):
        self.note("Python", "text")
        self.chat("find Python tutorial")
        self.chat("取消")
        self.assertIsNone(self.memory.notes.selected)
        self.chat("find Python tutorial")
        for i in range(6):
            self.memory.notes.handle(f"unrelated {i}", None)
        self.assertIsNone(self.memory.notes.selected)
        self.chat("find Python tutorial")
        self.memory.clear()
        self.assertIsNone(self.memory.notes.selected)

    def test_pending_confirmation_takes_precedence_over_note_followup(self):
        self.note("Python", "text")
        self.chat("find Python tutorial")
        self.router.execute_tool("shutdown_computer", {}, "shutdown", {"shutdown_computer": lambda: "should not execute"})
        response = self.chat("read it")
        self.assertIn("yes", response["reply"])
        self.assertEqual(response["tool_results"], [])

    def test_explanation_without_note_context_remains_general_chat(self):
        self.chat("解释一下")
        self.gemini.generate_response.assert_called_once()


if __name__ == "__main__":
    unittest.main()
