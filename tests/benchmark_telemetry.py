"""Manual read-only benchmark: python -m tests.benchmark_telemetry."""
import json
import statistics
import time

from services.system_telemetry import read_system_telemetry


def main():
    read_system_telemetry()  # Exclude one-time driver initialization.
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    latencies = []
    for _ in range(16):
        time.sleep(2)
        start = time.perf_counter()
        data = read_system_telemetry()
        latencies.append((time.perf_counter() - start) * 1000)
    elapsed = time.perf_counter() - wall_start
    cpu_ms = (time.process_time() - cpu_start) * 1000
    print(json.dumps({"samples": len(latencies), "elapsed_seconds": round(elapsed, 2),
        "median_wall_ms_including_100ms_sleep": round(statistics.median(latencies), 3),
        "process_cpu_ms_total": round(cpu_ms, 3),
        "process_cpu_ms_per_sample": round(cpu_ms / len(latencies), 3),
        "one_core_cpu_percent": round(cpu_ms / (elapsed * 10), 4),
        "payload_bytes": len(json.dumps(data).encode()), "last_sample": data}, indent=2))


if __name__ == "__main__":
    main()
