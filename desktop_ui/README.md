# JARVIS Windows desktop

Native Flutter workspace: Assistant, Tasks, Device, Settings and Errors. A steel/cyan
instrument-style shell shares its typography, colors and components through
`lib/console_theme.dart`. There are no image downloads, web views or blur layers.
The state indicator only animates while a chat request is outstanding.

## Desktop shortcut

One-time setup from the repository root:

```powershell
.\run-desktop.ps1 -BuildOnly -Release
.\create-desktop-shortcut.ps1
```

Double-click **JARVIS** on the Windows desktop. The shortcut uses the virtual
environment's `pythonw.exe` to launch the compiled Release app without a terminal,
dependency downloads or recompilation. It reuses a healthy local API, or starts
one on `127.0.0.1:8765` and waits up to 30 seconds for readiness before opening
the window. It does not start or load a local language model.
Startup failures show a dialog; local launcher/API diagnostics are appended to
`tmp/desktop-startup.log` (ignored by Git).

When the shortcut starts the API, it owns that API process and stops it when the
desktop app closes. A healthy API that was already running is reused and left
alone, so another active JARVIS window is not disrupted. This does not add
Windows startup/login behavior or a keyboard hotkey. Each activation opens an
app window. Keep the repository and its build folder in place; this shortcut is
not a standalone installer.

After changing Flutter code, close the Release app and rerun
`.\run-desktop.ps1 -BuildOnly -Release`. The desktop shortcut then uses the updated
build; it does not need to be recreated unless the repository moves.

Building Flutter plugins on Windows requires Developer Mode and Visual Studio's
**Desktop development with C++** workload. Enable Developer Mode under **Settings
→ System → For developers**. These are Windows/toolchain prerequisites and are
not Python packages, so they are documented rather than placed in
`requirements.txt`. Developer Mode can be disabled again when only running the
already-built shortcut.

## Run

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run-desktop.ps1
```

The launcher starts the local API if port 8765 is free. After backend source
changes, restart the existing JARVIS API process before running the desktop app.

The launcher uses a project-local `.pub-cache/`, resolves the committed lockfile
before building, and fixes both the shell and native working directory to
`desktop_ui/`. This avoids depending on a missing or inconsistent shared
`AppData/Local/Pub/Cache` when compiling. The first launch downloads dependencies;
later launches reuse this cache. The shared Pub cache and Flutter SDK are untouched,
and the caller's `PUB_CACHE` and working directory are restored on exit.

To verify dependencies and the Windows build without launching an app or API:

```powershell
.\run-desktop.ps1 -BuildOnly
```

When running Flutter commands manually, use the same cache (`$env:PUB_CACHE =
"C:\Users\ongzh\JARVIS\.pub-cache"`) before `flutter pub get`, or use the launcher
again to regenerate package resolution for its isolated cache.

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
executing anything. Assistant starts empty after every restart; prior locally saved
turns appear as expandable archives under Tasks. The UI does not fake token
streaming, a live stop button or model liveness.

Use **Read reply** beside a completed Assistant response with the session voice
provider selected in Settings. **Windows system voice** follows the voice and
speed selected in Windows Speech settings on every read, displays that live
selection in JARVIS Settings, and keeps text on this device. **Fish Audio cloud** sends only that reply
text to Fish Audio after the user selects it; its API key is read only from the
local `.env` file and is never placed in Flutter. Neither provider enters
TaskRouter, receives computer-execution authority, or includes, clones or
imitates the copyrighted *Iron Man* JARVIS character voice.
Voice input, wake word, floating companion and model/routing settings remain
explicitly planned or read-only. Appearance/monitor preferences last for this
app session. The permission preview is a demonstration and never authorizes
execution.

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
