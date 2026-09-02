# JARVIS Windows desktop

Native Flutter workspace: Assistant, Tasks, Device, Settings and Errors. A steel/cyan
instrument-style shell shares its typography, colors and components through
`lib/console_theme.dart`. There are no image downloads, web views or blur layers.
The state indicator only animates while a chat request is outstanding.

## Run

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run-desktop.ps1
```

The launcher starts the local API if port 8765 is free. After backend source
changes, restart the existing JARVIS API process before running the desktop app.

## Live monitoring

- CPU and physical memory readings, plus NVIDIA GPU utilization, VRAM and
  temperature, refresh every 2 seconds through `GET /api/telemetry`.
- Settings offers 2, 5 or 10 seconds. The monitor's pause button stops polling.
  Minimizing hides the Flutter application and suspends polling; restoring it
  refreshes immediately. Merely moving focus to another app does not pause it.
- Only one request may be in flight; read requests time out and retry on the
  next poll. There is no busy loop or streaming socket. Health refreshes every
  30 seconds, or when disconnected.
- At most 60 CPU/RAM samples stay in memory. Graphs use actual sample timestamps
  and a fixed 0–100% scale. Errors and paused readings are marked as stale.
- Backend sampling is on demand with a one-second shared cache. CPU sampling
  sleeps for 100 ms in a worker thread. Monitoring never calls the model,
  enters TaskRouter, or creates TaskManager history.
- NVIDIA's `nvidia-ml-py` bindings call the installed NVML driver in-process.
  No repeated `nvidia-smi` subprocesses, driver installs, GPU power changes or
  privileged hardware writes. Unsupported GPU metrics show N/A. AMD/Intel
  GPU monitoring is not implemented; CPU/RAM continue normally.
- Monitoring is lightweight but not free. Laptop GPU queries can affect idle
  power behavior; use pause or a slower interval when running on battery.

## Existing behavior and boundaries

The composer starts as one line and grows upward to five lines, then scrolls
internally. Ctrl+Enter sends; two consecutive Enter presses within 600 ms also
send (the first inserts a newline). Shift+Enter always inserts a newline. Active
IME composition and held/repeated Enter keys do not trigger double-Enter send.

Errors collects UI/runtime exceptions, chat request failures, failed tool results
and connection-error transitions. The conversation shows a compact failure notice;
tool success evidence remains expandable. UI failures use a neutral fallback
instead of Flutter's debug red panel, without suppressing console/IDE diagnostics.
Reports include time, source, occurrence count and available stack traces, with
copy and confirmed-clear controls. Up to 50 unique reports stay in memory for
this app session; individual fields are capped at 32 KiB. Nothing is written to
disk or uploaded. Backend errors are included only when returned to this UI;
this is not a collector for historical Python logs or native process crashes.

Chat and tool evidence still use `/api/chat`, including the existing text-based
confirmation flow. Keyboard submission sends once; suggestions fill the composer without
executing anything. Tasks lists this UI session only, not the entire Core history.
The UI does not fake token streaming, a live stop button or model liveness.

Voice, wake word, floating companion and model/routing settings are marked as
planned or read-only. Appearance/monitor preferences last for this app session.
The permission preview is a demonstration and never authorizes execution.

## Checks

```powershell
flutter analyze
flutter test
flutter build windows --release
```

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m tests.benchmark_telemetry
```

The widget suite covers navigation at 1440/960/600/390 px, 130% text scaling,
keyboard submission, session history, offline feedback, lifecycle pause/resume,
bounded chart history and request-overlap prevention. It also covers diagnostic
capture/copy/clear, compact fallback, duplicate limits, expansion-state isolation,
one-to-five-line composer sizing, double Enter and IME/Shift+Enter protection.
