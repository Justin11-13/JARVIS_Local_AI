import base64
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from services.windows_speech_service import WindowsSpeechService


class WindowsSpeechServiceTests(unittest.TestCase):
    @patch("services.windows_speech_service.sys.platform", "win32")
    @patch("services.windows_speech_service.subprocess.Popen")
    def test_speaks_through_environment_not_shell_text(self, popen):
        process = MagicMock()
        process.communicate.return_value = (b"", b"")
        process.returncode = 0
        popen.return_value = process

        WindowsSpeechService().speak("Hello from JARVIS")

        command = popen.call_args.args[0]
        environment = popen.call_args.kwargs["env"]
        script = base64.b64decode(command[-1]).decode("utf-16-le")
        self.assertIn("powershell.exe", command)
        self.assertNotIn("Hello from JARVIS", command)
        self.assertEqual(environment["JARVIS_SPEECH_TEXT"], "Hello from JARVIS")
        self.assertEqual(
            popen.call_args.kwargs["creationflags"],
            subprocess.CREATE_NO_WINDOW,
        )
        self.assertIn("Speech_OneCore\\Settings\\TextToSpeech", script)
        self.assertIn("$settings.Speed", script)
