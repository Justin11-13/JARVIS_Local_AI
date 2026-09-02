"""Read-only desktop telemetry. No model calls, task history, or background loop."""

import atexit
from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from time import monotonic

import psutil

try:
    import pynvml
except ImportError:  # CPU/RAM still work before optional driver bindings exist.
    pynvml = None


_lock = Lock()
_cached: dict | None = None
_sampled_at = 0.0
_nvml_initialized = False


def _shutdown_gpu() -> None:
    if pynvml is not None and _nvml_initialized:
        try:
            pynvml.nvmlShutdown()
        except pynvml.NVMLError:
            pass


def _read_gpus() -> tuple[list[dict], str | None]:
    """Query NVIDIA's driver in-process; no subprocess or new GPU workload."""
    global _nvml_initialized
    if pynvml is None:
        return [], "GPU monitoring needs nvidia-ml-py. Install requirements.txt."
    try:
        if not _nvml_initialized:
            pynvml.nvmlInit()
            _nvml_initialized = True
            atexit.register(_shutdown_gpu)
        devices = []
        for index in range(pynvml.nvmlDeviceGetCount()):
            handle = pynvml.nvmlDeviceGetHandleByIndex(index)
            name = pynvml.nvmlDeviceGetName(handle)
            record = {"id": str(index), "name": name.decode() if isinstance(name, bytes) else name,
                      "utilization_percent": None, "memory_used_bytes": None,
                      "memory_total_bytes": None, "temperature_c": None}
            # Unsupported metrics remain null, never a fabricated zero.
            try:
                record["utilization_percent"] = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
            except pynvml.NVMLError:
                pass
            try:
                memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
                record["memory_used_bytes"] = memory.used
                record["memory_total_bytes"] = memory.total
            except pynvml.NVMLError:
                pass
            try:
                record["temperature_c"] = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except pynvml.NVMLError:
                pass
            devices.append(record)
        return devices, None if devices else "No NVIDIA GPU detected. AMD/Intel monitoring is not connected."
    except pynvml.NVMLError as error:
        return [], f"NVIDIA monitoring unavailable: {error}. CPU and memory monitoring continue."


def read_system_telemetry() -> dict:
    """Sample on demand, sharing a one-second cache between desktop clients.

    The short blocking sample runs in FastAPI's worker thread, not its event
    loop. Unlike interval=None, it is valid even on a thread's first call.
    The wait sleeps; it does not busy-spin. No requests means no sampling.
    """
    global _cached, _sampled_at
    with _lock:
        if _cached is not None and monotonic() - _sampled_at < 1.0:
            return deepcopy(_cached)
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        gpus, gpu_error = _read_gpus()
        _cached = {
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "memory_used_bytes": memory.total - memory.available,
            "memory_total_bytes": memory.total,
            "sampled_at": datetime.now(timezone.utc).isoformat(),
            "gpus": gpus,
            "gpu_error": gpu_error,
        }
        _sampled_at = monotonic()
        return deepcopy(_cached)
