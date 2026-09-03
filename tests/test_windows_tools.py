import unittest
from types import SimpleNamespace
from unittest.mock import patch

from skills import windows


class WindowsToolsTests(unittest.TestCase):
    @patch("skills.windows.psutil.sensors_battery")
    def test_battery_status_reports_state(self, battery):
        battery.return_value = SimpleNamespace(percent=80, power_plugged=True, secsleft=3600)

        result = windows.get_battery_status()

        self.assertIn("80%", result)
        self.assertIn("charging", result)

    @patch("skills.windows._send_virtual_key")
    @patch("skills.windows._require_windows", return_value=None)
    def test_adjust_volume_uses_bounded_key_presses(self, _, send_key):
        result = windows.adjust_volume("up", "large")

        self.assertIn("Volume moved up", result)
        self.assertEqual(send_key.call_count, windows.VOLUME_AMOUNTS["large"])
        send_key.assert_called_with(windows.VK_VOLUME_UP)

    @patch("skills.windows._send_virtual_key")
    @patch("skills.windows._require_windows", return_value=None)
    def test_media_control_accepts_only_fixed_actions(self, _, send_key):
        self.assertIn("Sent media action", windows.media_control("next"))
        send_key.assert_called_once_with(windows.VK_MEDIA_NEXT_TRACK)
        self.assertIn("must be", windows.media_control("type text"))

    @patch("skills.windows.subprocess.Popen")
    @patch("skills.windows._require_windows", return_value=None)
    def test_shutdown_uses_fixed_command_only_after_router_permission(self, _, popen):
        result = windows.shutdown_computer()

        self.assertEqual(result, "Windows is shutting down.")
        popen.assert_called_once_with(["shutdown", "/s", "/t", "0"])


if __name__ == "__main__":
    unittest.main()
