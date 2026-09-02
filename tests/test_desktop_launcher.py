import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app import desktop_launcher as launcher


class DesktopLauncherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.executable = self.root / "Release/desktop_ui.exe"
        self.executable.parent.mkdir()
        self.executable.touch()
        self.log = self.root / "tmp/desktop-startup.log"
        for name, value in (
            ("ROOT", self.root),
            ("DESKTOP_EXE", self.executable),
            ("LOG_PATH", self.log),
        ):
            patcher = patch.object(launcher, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_existing_api_launches_only_the_compiled_app(self):
        with patch.object(launcher, "api_ready", return_value=True), patch.object(
            launcher.subprocess, "Popen"
        ) as start:
            launcher.launch()
        start.assert_called_once_with(
            [str(self.executable)],
            cwd=self.executable.parent,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.assertFalse(self.log.exists())

    def test_cold_start_waits_for_api_and_stays_on_loopback(self):
        api = MagicMock()
        api.poll.return_value = None
        with patch.object(launcher, "api_ready", side_effect=[False, False, True]), patch.object(
            launcher.subprocess, "Popen", return_value=api
        ) as start, patch.object(launcher.time, "sleep") as sleep:
            launcher.launch()
        self.assertEqual(start.call_count, 2)
        backend, desktop = start.call_args_list
        self.assertEqual(backend.args[0], [
            launcher.sys.executable, "-m", "uvicorn", "app.api:app",
            "--host", "127.0.0.1", "--port", "8765",
        ])
        self.assertEqual(backend.kwargs["cwd"], self.root)
        self.assertEqual(backend.kwargs["creationflags"], subprocess.CREATE_NO_WINDOW)
        self.assertEqual(desktop.args[0], [str(self.executable)])
        sleep.assert_called_once_with(0.25)
        api.terminate.assert_not_called()

    def test_api_exit_does_not_open_an_offline_window(self):
        api = MagicMock()
        api.poll.return_value = 1
        with patch.object(launcher, "api_ready", return_value=False), patch.object(
            launcher.subprocess, "Popen", return_value=api
        ) as start, self.assertRaisesRegex(RuntimeError, "could not start"):
            launcher.launch()
        self.assertEqual(start.call_count, 1)

    def test_unready_api_has_a_bounded_wait(self):
        api = MagicMock()
        api.poll.return_value = None
        with patch.object(launcher, "api_ready", return_value=False), patch.object(
            launcher.subprocess, "Popen", return_value=api
        ) as start, patch.object(launcher.time, "monotonic", side_effect=[0, 31]), self.assertRaises(
            TimeoutError
        ):
            launcher.launch()
        self.assertEqual(start.call_count, 1)

    def test_missing_build_does_not_start_the_backend(self):
        with patch.object(launcher, "DESKTOP_EXE", self.root / "missing.exe"), patch.object(
            launcher.subprocess, "Popen"
        ) as start, self.assertRaisesRegex(FileNotFoundError, "-BuildOnly -Release"):
            launcher.launch()
        start.assert_not_called()

    def test_startup_failure_is_visible_and_logged(self):
        with patch.object(launcher, "launch", side_effect=RuntimeError("Startup failure")), patch.object(
            launcher.ctypes, "windll"
        ) as windows:
            self.assertEqual(launcher.main(), 1)
        windows.user32.MessageBoxW.assert_called_once()
        self.assertIn("Startup failure", windows.user32.MessageBoxW.call_args.args[1])
        self.assertIn(str(self.log), windows.user32.MessageBoxW.call_args.args[1])
        self.assertIn("RuntimeError: Startup failure", self.log.read_text(encoding="utf-8"))

    def test_health_requires_a_jarvis_shaped_response(self):
        for body, expected in (
            (b'{"status":"ready","model":"qwen3:8b","routing_mode":"ask"}', True),
            (b'{"status":"ready"}', False),
            (b'[]', False),
            (b'not json', False),
        ):
            with self.subTest(body=body), patch.object(
                launcher.LOCAL_HTTP, "open", return_value=io.BytesIO(body)
            ) as request:
                self.assertEqual(launcher.api_ready(), expected)
                request.assert_called_once_with("http://127.0.0.1:8765/api/health", timeout=1)

    def test_unreachable_api_is_not_ready(self):
        with patch.object(launcher.LOCAL_HTTP, "open", side_effect=OSError("Connection refused")):
            self.assertFalse(launcher.api_ready())


if __name__ == "__main__":
    unittest.main()
