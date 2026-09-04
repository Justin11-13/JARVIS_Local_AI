import unittest
from pathlib import Path
import tempfile

from services.jarvis_memory import JarvisMemory


class JarvisMemoryTests(unittest.TestCase):
    def test_memory_keeps_bounded_turns_as_conversation_roles(self):
        memory = JarvisMemory(max_turns=2)
        memory.remember("first user", "first assistant")
        memory.remember("second user", "second assistant")
        memory.remember("third user", "third assistant")

        self.assertEqual(len(memory), 2)
        self.assertEqual(
            memory.gemini_contents(),
            [
                {"role": "user", "parts": [{"text": "second user"}]},
                {"role": "model", "parts": [{"text": "second assistant"}]},
                {"role": "user", "parts": [{"text": "third user"}]},
                {"role": "model", "parts": [{"text": "third assistant"}]},
            ],
        )

    def test_empty_turn_is_not_remembered_and_clear_removes_session_memory(self):
        memory = JarvisMemory()
        memory.remember("", "answer")
        memory.remember("question", "")
        self.assertEqual(len(memory), 0)
        memory.remember("question", "answer")
        memory.clear()
        self.assertEqual(memory.gemini_contents(), [])

    def test_persistent_history_survives_a_new_memory_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "conversation.json"
            first = JarvisMemory(
                max_turns=10,
                context_turns=1,
                storage_path=path,
            )
            first.remember(
                "第一题",
                "第一个回答",
                "The first answer.",
            )
            first.remember(
                "第二题 password=hunter2",
                "第二个回答",
                "The second answer.",
            )

            restored = JarvisMemory(
                max_turns=10,
                context_turns=1,
                storage_path=path,
            )

            self.assertEqual(len(restored.history()), 2)
            self.assertIn("password=[REDACTED]", restored.history()[1]["user"])
            self.assertNotIn("hunter2", path.read_text(encoding="utf-8"))
            self.assertEqual(
                restored.gemini_contents(),
                [
                    {
                        "role": "user",
                        "parts": [{"text": "第二题 password=[REDACTED]"}],
                    },
                    {
                        "role": "model",
                        "parts": [{"text": "第二个回答"}],
                    },
                ],
            )


if __name__ == "__main__":
    unittest.main()
