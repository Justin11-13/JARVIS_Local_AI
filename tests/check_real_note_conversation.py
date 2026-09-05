"""Manual local acceptance against configured vault; no cloud or opening apps."""
from unittest.mock import patch

from app.api import ChatRequest, chat_with_jarvis
from services.jarvis_memory import JarvisMemory


def main():
    memory = JarvisMemory()
    with patch("app.api.jarvis_memory", memory), patch("app.api.gemini") as gemini:
        gemini.is_configured.return_value = False
        search = chat_with_jarvis(ChatRequest(message="帮我找python教程"))
        assert search["tool_results"][0]["success"], search["reply"]
        assert memory.notes.candidates, "No shared Python notes found"
        print("Shared candidates:", len(memory.notes.candidates))
        if memory.notes.selected is None:
            index = next((i for i, note in enumerate(memory.notes.candidates, 1) if "Python Complete Learning Guide" in note["relative_path"]), 1)
            selected = chat_with_jarvis(ChatRequest(message=str(index)))
            assert selected["tool_results"][0]["success"], selected["reply"]
        target = dict(memory.notes.selected)
        followup = chat_with_jarvis(ChatRequest(message="读一下"))
        assert followup["tool_results"][0]["success"], followup["reply"]
        assert target == memory.notes.selected
        print("Follow-up reads the selected note:", target["relative_path"])
        print("Reply characters:", len(followup["reply"]))
        gemini.generate_response.assert_not_called()
        print("No cloud request; no Windows app opened; history kept in memory only.")


if __name__ == "__main__":
    main()
