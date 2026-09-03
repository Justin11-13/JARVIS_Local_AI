import unittest

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


if __name__ == "__main__":
    unittest.main()
