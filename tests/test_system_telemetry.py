import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services import system_telemetry as telemetry


class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.cache = patch.multiple(telemetry, _cached=None, _sampled_at=0.0)
        self.cache.start()
        self.addCleanup(self.cache.stop)

    @patch.object(telemetry, "_read_gpus", return_value=([], "Not supported"))
    @patch.object(telemetry.psutil, "virtual_memory")
    @patch.object(telemetry.psutil, "cpu_percent", return_value=0.0)
    def test_on_demand_sampling_and_shared_cache(self, cpu, memory, gpu):
        memory.return_value = SimpleNamespace(total=1000, available=600, percent=40.0)
        first = telemetry.read_system_telemetry()
        second = telemetry.read_system_telemetry()
        cpu.assert_called_once_with(interval=0.1)
        gpu.assert_called_once()
        self.assertEqual(first, second)
        self.assertEqual(first["cpu_percent"], 0.0)
        self.assertEqual(first["memory_used_bytes"], 400)
        self.assertEqual(first["gpu_error"], "Not supported")
        self.assertIn("+00:00", first["sampled_at"])

    @patch.object(telemetry, "_read_gpus", return_value=([{"id": "0"}], None))
    @patch.object(telemetry.psutil, "virtual_memory", return_value=SimpleNamespace(total=1000, available=500, percent=50))
    @patch.object(telemetry.psutil, "cpu_percent", return_value=12)
    def test_cache_is_not_mutable_by_callers(self, *_):
        telemetry.read_system_telemetry()["gpus"][0]["id"] = "modified"
        self.assertEqual(telemetry.read_system_telemetry()["gpus"][0]["id"], "0")

    @patch.object(telemetry, "pynvml", None)
    def test_cpu_can_work_without_gpu_bindings(self):
        devices, message = telemetry._read_gpus()
        self.assertEqual(devices, [])
        self.assertIn("nvidia-ml-py", message)

    def test_unsupported_gpu_metrics_are_null_not_zero(self):
        class Unsupported(Exception):
            pass
        with patch.object(telemetry, "pynvml") as nvml, patch.object(telemetry, "_nvml_initialized", True):
            nvml.NVMLError = Unsupported
            nvml.nvmlDeviceGetCount.return_value = 1
            nvml.nvmlDeviceGetName.return_value = "Test GPU"
            nvml.nvmlDeviceGetUtilizationRates.side_effect = Unsupported()
            nvml.nvmlDeviceGetMemoryInfo.side_effect = Unsupported()
            nvml.nvmlDeviceGetTemperature.side_effect = Unsupported()
            devices, message = telemetry._read_gpus()
            self.assertIsNone(message)
            self.assertIsNone(devices[0]["utilization_percent"])
            self.assertIsNone(devices[0]["memory_used_bytes"])
            self.assertIsNone(devices[0]["temperature_c"])


if __name__ == "__main__":
    unittest.main()
