# JARVIS Local AI Assistant

JARVIS is a local-first Windows assistant foundation. This candidate branch
combines a Python Core, a loopback FastAPI service, the New Electron desktop
client, a Legacy Flutter compatibility client, guarded Windows tools, project
inspection, live telemetry, optional Obsidian/RAG knowledge, and explicit AI
transport boundaries.

The New Electron UI is the primary desktop direction and the Legacy Flutter
client remains available as a compatibility entrypoint. The Electron renderer
does not own routing, permissions, native execution, or AI-provider fallback;
the Python Core remains authoritative.

The Core owns routing, validation, permissions, confirmation, and tool-result
truth. A model may propose a bounded operation; it does not receive an
unrestricted shell, administrator access, or permission to bypass the Core.

> Documentation status: this README is reconciled against candidate branch
> `codex/electron-source-candidate-20260912`, based on
> `main@07df06f92c3a90eb2fa2dc2bd42cc76271e7d21f`.
>
> The reviewed Electron handoff contains 45 source/test files with a separate
> SHA-256 manifest. One later test-only import correction is included in this
> candidate with its updated file hash. This branch is still a development
> candidate: it has not been published as a GitHub release, and
> managed-account/runtime acceptance is not claimed for every machine.

[New UI preview](#new-electron-ui) ·
[Installation](#installation) ·
[Legacy compatibility desktop](#legacy-flutter-compatibility-desktop) ·
[Security](#security-and-privacy) ·
[Roadmap](#roadmap) ·
[Edition profiles](docs/editions.md) ·
[Desktop guide](desktop_ui/README.md) ·
[License](LICENSE)

## Status at a glance

| Surface | Status in this checkout | Boundary |
| --- | --- | --- |
| Python Core and loopback API | `IMPLEMENTED` | Local service on `127.0.0.1:8765`; API readiness does not prove AI access. |
| Electron New UI | `CANDIDATE — source and static checks included` | Primary UI direction; normal Core/Luna/confirmation smoke remains environment-bound. |
| Legacy Flutter Windows UI | `IMPLEMENTED — compatibility path` | Retained for recovery and compatibility; not the primary UI direction. |
| Gemini BYOK chat | `IMPLEMENTED — optional` | Requires the user's own local Gemini key; no silent provider fallback. |
| Obsidian and local RAG | `IMPLEMENTED — opt-in` | Vault registration, access labels, local indexing, citations, and confirmation-gated note writes. |
| Luna managed subscription / Direct API | `CANDIDATE — external prerequisites` | Source supports exact `gpt-5.6-luna`; managed login/model access or a user-entered Direct API key is still required. |
| ChatGPT UI executor and Codex engineering handoff | `PLANNED` | No automatic handoff is performed by this checkout. |
| Phase D expansion | `OUT OF SCOPE` | Camera vision, mobile, IoT, smart-home, and physical-environment awareness require explicit authorization. |

## Desktop preview

The **New Electron UI is the primary product direction** and is included in this
candidate. The screenshots below are still Legacy Flutter examples because no
Electron screenshot is being invented or presented as a runtime benchmark.

These screenshots are existing Legacy Flutter examples. Telemetry values,
response times, model labels, and connected-state indicators are examples from
the captured session, not benchmarks or proof that every fresh clone is
configured.

### Assistant workspace

![Legacy Flutter Assistant page with a Chinese conversation and live CPU, memory, and NVIDIA GPU monitoring](docs/screenshots/assistant-workspace.png)

### Device dashboard

![Legacy Flutter Device page with CPU, memory, NVIDIA GPU, and local runtime status](docs/screenshots/device-dashboard.png)

The images were captured on Windows on September 3, 2026. They do not contain
API keys or personal file paths, but they still should not be treated as live
data for another machine.

## Current features

### New Electron UI — primary direction

The candidate includes `electron_motion_preview/`, its npm lockfile, the fixed
Core bridge/supervisor, the sandboxed renderer, and the static/Node regression
tests. It is started by `run-new-ui.ps1`, which launches the Electron shell; the
main process starts or reuses the local Core on `127.0.0.1:8765` and fails
explicitly on a non-JARVIS port occupant.

The candidate has source/static evidence, but it is not a universal runtime
guarantee. Core readiness, managed login, exact model access, quota, speech,
GPU support, and native confirmation are separate facts.

### Legacy Flutter Windows client — compatibility path

The supported desktop app is under [`desktop_ui/`](desktop_ui/). It provides:

- **Assistant:** bounded chat, native-tool evidence, and one-step confirmation
  for sensitive power actions.
- **Tasks:** local conversation/task views for the current application flow;
  this is not a durable scheduler or a complete job-history service.
- **Device:** CPU, physical-memory, and optional NVIDIA telemetry with bounded
  chart history, pause, and refresh intervals.
- **Settings:** local UI/monitoring settings, optional speech configuration,
  and Obsidian knowledge controls.
- **Errors:** session diagnostics with occurrence counts, details, copy, and
  confirmed clear. UI notices stay compact without hiding console diagnostics.

The visual language is a steel/cyan desktop instrument surface. The composer
supports Ctrl+Enter, protected IME composition, Shift+Enter newlines, and the
existing double-Enter send gesture.

### Core and local API

The FastAPI service and terminal CLI reuse the same Core tool registry and
`services/task_router.py` policy. The current API includes:

- `GET /api/health` — Core and configuration information;
- `GET /api/telemetry` — CPU, memory, and optional NVIDIA metrics;
- `POST /api/chat` and `GET /api/chat/history` — bounded conversation flow;
- `GET /api/system-info` — local system information;
- `/api/projects/...` — registered-project metadata, Git status, file listing,
  file reading, search, and explicit registry refresh;
- `/api/obsidian/...` — vault registration, removal, reindexing, and source
  opening; and
- `/api/system-speech...` — local Windows speech settings, speech, and stop.

The API binds to loopback when launched by the supplied scripts. Do not expose
it to a network without designing and verifying a separate authentication and
permission boundary.

### Native tools

The Python Core currently contains bounded tools for:

- discovering and opening registered Windows applications;
- reading system, battery, network, process, and supported NVIDIA status;
- volume, mute, and selected media controls;
- opening known folders and selected Windows Settings pages;
- locking, sleeping, restarting, and shutting down Windows after confirmation;
- discovering projects under configured roots and opening them in VS Code;
- reading project metadata, Git status, files, and source searches; and
- searching/opening Obsidian notes plus confirmation-gated create, append, and
  exact-text update operations.

Project file tools are read-only. Obsidian note writes are a separate,
explicitly confirmed path; they do not grant the model general file-write
access.

### Telemetry

Monitoring reads actual local counters and does not call the language model,
create a task, or execute an operating-system action.

- CPU and physical-memory readings work without an AI backend.
- NVIDIA utilization, VRAM, and temperature require a working NVIDIA driver
  and NVML support; unsupported metrics are shown as unavailable.
- The default refresh interval is two seconds, with slower intervals and pause.
- Polling pauses while the Flutter window is minimized, and requests do not
  overlap.

Telemetry is local and useful, but not free: GPU queries can affect laptop
power usage. Pause monitoring or choose a slower interval on battery power.

### Projects, Git, and files

Project discovery is restricted to configured roots. Current detection covers
common Laravel/PHP, Django/Python, Node.js, Maven, Gradle, and Git projects.
JARVIS can list projects, inspect project metadata, open a project, show Git
status, list files, read supported text files, and search source code.

Create local project-root configuration from the example file:

```powershell
if (-not (Test-Path config\project_roots.json)) {
    Copy-Item config\project_roots.example.json config\project_roots.json
}
```

Only directories in `config/project_roots.json` are scanned. Generated
registries such as `config/apps.json` and `config/projects.json` stay local and
must not be committed.

### Obsidian and RAG

Obsidian is optional. A vault is excluded by default until the user registers
it and selects an access policy. The current policy labels are:

- `rag` — eligible note content may be indexed and sent as context to the
  configured Gemini provider;
- `local-only` — local search/open operations may use the note, but its body is
  not sent as model context; and
- `excluded` — ignore the note for JARVIS retrieval.

JARVIS keeps the vault path and index locally, skips protected folders, and
returns citations for retrieved notes. Reindexing is explicit from the
desktop UI/API. A first RAG warm-up may download or initialize the local
embedding/vector dependencies; it does not make a vault public or grant the
model arbitrary filesystem access.

### Speech

This baseline supports optional reply speech, not voice input or wake-word
conversation. Windows system speech uses the selected Windows voice and speed.
Fish Audio is an optional cloud provider configured through local `.env`
values; only the selected reply narration is sent to that provider. Speech
providers do not receive native-tool authority.

## Not available in this snapshot

The following are not guaranteed by a fresh clone without external setup or
additional acceptance:

- managed ChatGPT subscription transport or access to the exact Luna model;
- OpenAI Direct API transport without a user-entered key and provider access;
- a successful normal Electron window on hosts with incompatible GPU/cache/ACL
  conditions;
- ChatGPT UI delegation or Codex engineering handoff;
- Ollama, Qwen, another local model, or a GPT API client;
- unrestricted shell/PowerShell, administrator access, arbitrary browser
  control, arbitrary file writing, Git commit, or Git push by the model;
- microphone input, wake word, STT, barge-in, or voice verification;
- system tray/background lifecycle controls and a durable scheduler; and
- autonomous computer control.

The checked-in [ChatGPT UI + Codex implementation plan](docs/chatgpt-codex-implementation-plan.md)
is a proposed plan, not proof that an executor exists. It must not be used to
claim a feature is implemented.

## New Electron UI and Legacy Flutter relationship

The two UI directions have different status and entry points:

| UI | Role | Core relationship |
| --- | --- | --- |
| Electron New UI | **Primary candidate UI**; source and lockfile are included in this branch. | Consumes the same loopback Core through a fixed main-process bridge; it does not own routing, permissions, tools, or telemetry. |
| Legacy Flutter | **Compatibility client**; retained for recovery and comparison. | Uses the current Core/API foundation through `desktop_ui/`. |

The Electron candidate is the replacement direction, but a healthy window must
still be distinguished from Core readiness and AI availability. A UI opening
successfully is not proof that the Core is ready, a provider is authenticated,
a model is available, or a request can execute a local action.

The candidate's `electron_motion_preview/` has a sandboxed preload and fixed
bridge to `127.0.0.1:8765`. Its surface includes Core health, telemetry,
conversation, projects/Git/files/search, tasks, Obsidian metadata, AI mode,
and bounded speech operations. Renderer code is not an HTTP client and does
not receive tool or shell authority.

That active line also contains a proposed Luna foreground path:

- **Managed subscription:** the local Codex App Server, managed ChatGPT login,
  exact model `gpt-5.6-luna`, and a `:read-only` profile. The account must be
  signed in and must actually expose that model.
- **Direct API:** the exact Luna model through the OpenAI Responses API, with
  a user-entered OpenAI API key held only in the Core process. Normal provider
  billing, quota, account, and model-access limits apply.
- **No silent fallback:** a failed managed transport, missing model, failed
  login, missing key, quota error, or network error is reported explicitly;
  JARVIS does not silently switch to Gemini, another model, or another mode.
- **No model execution authority:** Luna text transport does not receive
  shell, browser, filesystem, MCP, plugin, or native-tool authority. Existing
  native intents remain on the Core permission/confirmation path.

The candidate records contain source/static tests and some ordinary-user
runtime evidence, but several real-window, audio, Core-startup, and
managed-account acceptance rows remain environment-bound or pending. They are
not a universal release claim.

### Target architecture reference

The active coordination line maintains the canonical target at the relative
path `docs/architecture/TARGET_ARCHITECTURE.md`. That file is not present in
this clean baseline, so this README intentionally does not link to it as if a
fresh clone could open it. The checked-in implementation plan above is the
available roadmap artifact; neither it nor this README replaces the canonical
Target document.

## Requirements

### Required for the New Electron candidate

- Windows with PowerShell.
- CPython 3.12.x or newer with `venv` and `pip`.
- Node.js `>=22.12.0` and npm.
- Git for cloning and source inspection.
- A managed Codex installation (`codex.cmd`) and a signed-in account with
  access to exact `gpt-5.6-luna` only if managed AI chat is required. The UI can
  open without this external account, but AI status will remain unavailable.

The candidate's `setup.ps1` creates `.venv`, installs the captured
`requirements.lock.txt`, runs `npm ci` in `electron_motion_preview/`, and can
run the static/Node checks. It never writes credentials or starts an AI turn.

### Required for the Legacy Flutter compatibility build

- Windows with PowerShell. Windows 11 is the current development environment;
  this repository does not declare a minimum Windows version.
- Git for cloning and source inspection.
- A CPython installation with `venv` and `pip`. The candidate includes a
  Python lock captured with Python 3.12.14; verify the interpreter with
  `python --version` before creating `.venv`.
- Flutter Windows tooling. `desktop_ui/pubspec.yaml` requires Dart `^3.12.2`.
  The current development environment used Flutter 3.44.9 / Dart 3.12.2;
  that is an observed toolchain, not a fabricated minimum.
- Visual Studio with **Desktop development with C++** for Windows Flutter
  builds.
- Windows Developer Mode when Flutter plugin symlinks are required during a
  build. It is not needed merely to run an already-built Release app.

The compatibility `run-desktop.ps1` currently contains a default Flutter path for
the original development machine. If that path does not exist on your PC,
edit the script's `$Flutter` value to your own `flutter.bat` before building.
The commands below do not depend on a personal absolute path.

### Python packages

`requirements.txt` is the human-maintained top-level dependency declaration.
For this candidate, `setup.ps1` installs the captured versions from
`requirements.lock.txt`:

```text
fastapi
pydantic
python-dotenv
uvicorn[standard]
psutil
nvidia-ml-py==13.610.43
chromadb==1.5.9
sentence-transformers==6.0.1
watchfiles==1.2.0
```

The unpinned packages follow the resolver selected by your environment. The
first RAG initialization can be heavier than the Core-only startup because it
uses the pinned Chroma and sentence-transformers dependencies.

### Optional current integrations

- **Gemini BYOK:** a Google AI Studio/Gemini API key in local `.env`.
- **Fish Audio:** a Fish Audio key and, if needed, an authorized reference
  voice ID in local `.env`.
- **NVIDIA telemetry:** an installed NVIDIA driver/NVML-capable environment;
  CPU and memory monitoring continue without it.
- **Obsidian:** a local vault that the user explicitly registers in Settings.

### AI/account prerequisites

The Electron source and lockfile are included in this candidate:

- The active Electron lockfile resolves Electron `39.8.10` and
  `@electron/packager` `19.1.1`; its package metadata requires Node `>=22.12.0`.
- The managed Luna path requires a local Codex installation, a managed
  ChatGPT login, and access to exact `gpt-5.6-luna`; it is not a free/unlimited
  service guarantee.
- The Direct API path requires an OpenAI API key, network access, provider
  billing/quota, and exact model access.

These account prerequisites are not bundled into the repository and are not
silently replaced by Gemini or another provider.

## Installation

All commands below are PowerShell commands from a fresh clone. The repository
remote verified for this checkout is:

```text
https://github.com/Justin11-13/JARVIS_Local_AI.git
```

### 1. Clone the candidate branch

```powershell
git clone --branch codex/electron-source-candidate-20260912 --single-branch https://github.com/Justin11-13/JARVIS_Local_AI.git
cd JARVIS_Local_AI
git log -1 --oneline
```

The branch must be published before this command can work from GitHub. If the
candidate is later promoted to `main`, clone `main` instead and verify the
reported commit and candidate records.

### 2. Install the locked Python and Electron dependencies

```powershell
python --version
node --version
.\setup.ps1 -Verify
```

`setup.ps1 -Verify` runs Python compile checks, `npm run verify:static`, and 34
Electron Node tests. It does not claim that a real managed account, GPU, audio
device, or native confirmation window has been accepted. Do not commit `.venv/`,
`electron_motion_preview/node_modules/`, downloaded model/cache data, or local
databases.

### 3. Configure Gemini BYOK (optional)

Gemini is optional. The Core and local telemetry can start without it, while
free-form cloud reasoning needs the user's own key.

```powershell
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
}
notepad .env
```

Set only the local values you intend to use:

```dotenv
JARVIS_BRAIN_PROVIDER=gemini
GEMINI_API_KEY=PASTE_YOUR_OWN_KEY_HERE
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_ENABLED=true
```

Never put the key in Git, an issue, a screenshot, a prompt, or a source file.
Google's current documentation should be checked before distributing a build:

- [Gemini API key guide](https://ai.google.dev/gemini-api/docs/api-key)
- [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms)

JARVIS does not silently replace an unsupported provider or model with Gemini.
An unavailable provider remains unavailable and must be corrected explicitly.

### 4. Configure project roots (optional)

```powershell
if (-not (Test-Path config\project_roots.json)) {
    Copy-Item config\project_roots.example.json config\project_roots.json
}
notepad config\project_roots.json
```

Use paths that exist on your own machine. The scanner never treats an
unregistered directory as a project root.

### 5. Configure optional reply speech

Windows system speech uses the voices installed in **Settings → Time & language
→ Speech**. It does not require an API key.

For Fish Audio, keep credentials local:

```dotenv
FISH_API_KEY=PASTE_YOUR_OWN_KEY_HERE
FISH_REFERENCE_ID=OPTIONAL_AUTHORIZED_VOICE_MODEL_ID
```

A valid key without provider credits or access may still produce no audio. JARVIS
does not replace a failed speech provider with browser speech or another hidden
provider.

## New Electron UI

The New Electron UI is included in this candidate and is the primary desktop
direction. Its package boundary is:

```text
electron_motion_preview/package.json
electron_motion_preview/package-lock.json
```

Run the candidate after setup:

```powershell
.\run-new-ui.ps1 -Edition development
```

The shared source also exposes an `internal-test` profile. Its current
renderer-routing difference and the named package/install/uninstall workflow
are recorded in [`docs/editions.md`](docs/editions.md). The internal profile
must not be distributed until its Core port, instance ownership, and separate
user-data directory are verified end to end.

Check the existing desktop shortcut without changing it:

```powershell
.\verify-new-ui-shortcut.ps1
```

For renderer/WebGL verification without starting the Core:

```powershell
.\run-new-ui.ps1 -Verify
```

Normal startup uses `core-supervisor.cjs` to reuse a ready Core or start the
project-local `.venv\Scripts\python.exe` on `127.0.0.1:8765`. A non-ready
service already occupying that port is reported as an explicit failure. The
Electron shell does not include an installer or a bundled Python/Node runtime.

The current candidate verification is source/static verified, not a universal
runtime or managed-account acceptance. See [AI and billing boundaries](#ai-and-
billing-boundaries) before selecting a transport.

### Candidate verification boundary

- `npm ci` completed from `electron_motion_preview/package-lock.json`.
- `npm run verify:static` passed.
- `node --test test/*.cjs` passed with 34/34 tests.
- Candidate Python dependency installation and `compileall` passed.
- The full Python test discovery passed 156/156 after the test-only import correction;
  the corrected file has a new hash and is recorded separately from the
  original 45-file handoff fingerprint.
- A short local Core smoke returned `core.status = ready` from
  `http://127.0.0.1:8765/api/health`; it also correctly reported AI as
  `managed_subscription` / `not_checked` without an account check or inference.
- On the current restricted host, `run-new-ui.ps1 -Verify` reached Electron but
  failed at the renderer boundary because the GPU child exited with
  `0xC0000135`, the cache directory was not writable, and Electron returned
  `ERR_FAILED`. No GPU flag or hidden fallback was added; this remains a
  machine-specific acceptance gate.
- Real managed login, model access, native confirmation, audio, and normal
  Electron/Core smoke remain explicit acceptance steps, not inferred status.

## Legacy Flutter compatibility desktop

The Legacy Flutter client is retained as a compatibility and recovery path,
not the long-term UI direction.

### Build and run

After correcting the `$Flutter` path in `run-desktop.ps1` if necessary:

```powershell
.\run-desktop.ps1 -BuildOnly -Release
.\run-desktop.ps1
```

The script uses a repository-local `.pub-cache/`, runs `flutter pub get
--enforce-lockfile`, and starts the loopback API on `127.0.0.1:8765` only when
that port is not already listening. The first build downloads Flutter
packages; later builds reuse the local cache.

The current shortcut script creates the **Legacy UI** shortcut only after a
Release build:

```powershell
.\create-desktop-shortcut.ps1
```

The `.lnk` file is a convenience launcher, not a standalone installer. Keep
the repository, the virtual environment, the Release executable, its DLLs, and
its `data/` directory together. Do not assume a shortcut created on one PC can
be copied to another PC.

### Development mode

For the terminal CLI with Python auto-reload:

```powershell
.\dev.ps1
```

For a terminal-only run without auto-reload:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

For an explicit local API process:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.api:app --host 127.0.0.1 --port 8765
```

The CLI auto-reload process and the desktop API process are separate. After
changing Python backend code, stop and restart the API that the desktop is
actually using.

### Stop and restart safely

- Stop a foreground CLI/API with `Ctrl+C` in the terminal that launched it.
- Close the Legacy app before rebuilding its Windows executable.
- A shortcut-owned API is stopped by the launcher when its own window closes;
  an API that was already running is reused and left alone.
- Before stopping anything by PID, inspect the listener on `127.0.0.1:8765`
  and confirm that it is the JARVIS process you started. Do not kill an
  unrelated process merely because it owns the port.

Check Core readiness without implying AI readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/health | ConvertTo-Json -Depth 8
```

### Verification

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\run-desktop.ps1 -BuildOnly
```

For Flutter checks, use the same SDK path and repository-local cache as the
launcher:

```powershell
$env:PUB_CACHE = Join-Path $PWD ".pub-cache"
$Flutter = "C:\path\to\flutter\bin\flutter.bat"
Push-Location desktop_ui
try {
    & $Flutter pub get --enforce-lockfile
    & $Flutter analyze --no-pub
    & $Flutter test --no-pub
} finally {
    Pop-Location
}
```

These are verification commands, not a claim that they have passed on every
machine. The build and test result must be recorded for the exact checkout and
toolchain used.

## AI and billing boundaries

### Gemini in this baseline

Gemini is a user-configured optional cloud brain. Python validates model tool
names, arguments, paths, secret boundaries, and permission decisions before a
native operation runs. Gemini does not receive the `.env` key, an unrestricted
terminal, or arbitrary file contents.

Cloud providers may process prompts and responses under their own terms. Do not
send passwords, private keys, confidential source, or personal data unless you
have deliberately reviewed the provider's current policy and accepted that
data flow.

### Luna transport in this candidate

The candidate uses two explicit, user-selected transports for the exact model
`gpt-5.6-luna`:

- managed Codex App Server with managed ChatGPT authentication; or
- OpenAI Direct API with a user-entered key held only in the Core process.

Neither path is a free/unlimited guarantee, and not every account necessarily
has access to the exact model. Core health, login/key state, model access,
quota, and AI availability are separate facts. A UI that opened successfully
does not prove them.

No transport silently falls back to another model, provider, or mode. The
Electron shell and Core source are included, but managed login, model access,
quota, and normal-user smoke are external acceptance requirements.

## Security and privacy

JARVIS is intentionally conservative:

- Python Core policy, not model wording, decides whether an action may run.
- Sensitive power actions require explicit confirmation.
- Project paths are restricted to registered roots.
- Project file tools are read-only and credential-like files/results are
  filtered before model context is built.
- Obsidian notes are excluded by default and carry explicit access labels.
- `.env`, API keys, local registries, RAG indexes, caches, logs, and databases
  stay out of Git.
- The loopback API should not be exposed to a LAN or public tunnel without a
  separately verified authentication and permission design.
- A model response is not an authorization, and a successful HTTP response is
  not proof that a requested side effect occurred.

The locked Electron dependency audit currently reports three high-severity
dependency-node findings for `extract-zip@2.0.1`, reached through the direct
development dependencies `electron` and `@electron/packager`. npm reports no
available fix for this advisory range; `npm audit --omit=dev` reports zero
production findings. The package is used by Electron installation/packaging
paths, not by the renderer's application code. Re-run the audit before a
public release, and do not apply an unreviewed `npm audit fix --force`.

The native-tool boundary does not provide arbitrary PowerShell, arbitrary
shell, arbitrary file deletion/modification, Git commit/push, or
administrator-level operations to the model.

## Local files and generated data

Keep these machine-local and never commit credentials or generated runtime
state:

```text
.env
.venv/
.pub-cache/
desktop_ui/build/
desktop_ui/.dart_tool/
tmp/
data/
config/apps.json
config/projects.json
config/project_roots.json
config/obsidian_vaults.json
__pycache__/
*.pyc
*.db
*.sqlite
*.sqlite3
```

Use the checked-in example files instead:

```text
.env.example
config/apps.example.json
config/projects.example.json
config/project_roots.example.json
```

## Example requests

These examples use the current bounded tool vocabulary; they do not authorize
actions by themselves.

```text
打开 Chrome
```

```text
我的 CPU 和 RAM 现在用了多少？
```

```text
重新扫描我的 project
```

```text
检查 FYP 的 Git status
```

```text
读取 FYP 的 composer.json
```

```text
在 FYP 里面搜索 RoomController
```

For a high-risk request such as shutting down Windows, the Core must ask for a
clear confirmation before execution. A model or a README example cannot
pre-approve it.

## Roadmap

The project is being developed in bounded Phase A–C. The current Legacy baseline
is a foundation, not the complete target architecture.

### Phase A — Core

Target direction:

- Luna intelligence through an explicitly selected transport;
- JARVIS Core control, routing, permissions, and Python tools;
- SQLite operational/personal memory and user preferences;
- Obsidian, Knowledge Manager, RAG, and LLM Wiki boundaries; and
- attributable AI usage tracking.

The current checkout has only the parts listed under [Current features](#current-features).
Target items are not automatically implemented because they appear on a
roadmap.

### Phase B — Assistant

Planned/targeted work includes tasks and automation, scheduled and missed-task
policy, wake word, STT, TTS/voice interrupt, working context, and screen
awareness. Voice input and wake word are not available in this snapshot.

### Phase C — Proactive

After the necessary Core and Assistant foundations are stable, the target is an
event bus with filtering, proactive assistance, smart notifications, presence
awareness, error monitoring, and an explicitly authorized Codex handoff.

### Phase D — explicitly out of scope

Camera vision, mobile/multi-device support, IoT, smart-home control, and
physical-environment awareness are future-only. A general request to
“continue” or “implement the architecture” does not authorize Phase D.

## Repository structure

```text
JARVIS_Local_AI/
├── app/
│   ├── main.py                 # Core registry and terminal loop
│   ├── api.py                  # Loopback FastAPI interface
│   └── desktop_launcher.py     # Legacy desktop/API launcher
├── desktop_ui/                 # Flutter Windows client and widget tests
├── config/                     # Example configuration; local copies are ignored
├── docs/
│   ├── screenshots/            # README screenshots
│   └── chatgpt-codex-implementation-plan.md
├── knowledge/                  # Repository-owned knowledge sources
├── services/                   # Routing, tasks, telemetry, speech, memory, RAG
├── skills/                     # Bounded native/project/file/Git tools
├── electron_motion_preview/    # New Electron candidate and Node tests
├── config/editions.json         # Shared development/internal-test profile contract
├── tests/                      # Python regression tests
├── .env.example
├── dev.ps1
├── setup.ps1                   # Candidate clean setup and static checks
├── run-new-ui.ps1              # Start or verify the New Electron UI
├── verify-new-ui-shortcut.ps1  # Read-only Electron shortcut ownership check
├── package-edition.ps1         # Build a named local Windows edition package
├── install-edition.ps1         # Install one named package and shortcut
├── uninstall-edition.ps1       # Remove app files, preserving user data
├── run-desktop.ps1
├── create-desktop-shortcut.ps1
├── LICENSE
├── README.md
├── requirements.txt
└── requirements.lock.txt
```

The lock file captures the Python environment used for this candidate. The
repository still does not bundle Python, Node.js, Electron, Codex login state,
model weights, a Vault, or private configuration.

## Troubleshooting

### `python` is not recognized

Install a supported CPython distribution, open a new PowerShell window, and
rerun `python --version`. This repository does not silently switch to another
interpreter.

### Flutter SDK not found

The launcher currently has a development-machine default path. Install the
Flutter Windows SDK, ensure its `flutter.bat` is available, and edit the
`$Flutter` value in `run-desktop.ps1` to that path. Then rerun `flutter doctor -v`
and the Release build.

### Flutter plugin or Visual Studio build failure

Confirm Visual Studio's **Desktop development with C++** workload and Windows
Developer Mode. These are build prerequisites, not Python packages. Do not
disable security controls or run as administrator merely to hide an unresolved
toolchain error.

### API is offline or the port is occupied

Check the actual listener and Core health:

```powershell
Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8765 -State Listen
Invoke-RestMethod http://127.0.0.1:8765/api/health | ConvertTo-Json -Depth 8
```

If another application owns the port, stop only a confirmed JARVIS process or
choose a separately designed configuration. Do not kill an unknown process.

### Core is ready but AI is unavailable

`/api/health` being reachable means the local Core is serving. It does not
prove Gemini is configured, a key is valid, a model is accessible, or a cloud
request can complete. Check `.env` explicitly; no hidden provider fallback is
performed.

### NVIDIA metrics show unavailable

CPU and memory do not require NVIDIA. Check the installed driver and NVML
support. The app should show an explicit unavailable state rather than inventing
zeroes.

### RAG starts slowly or cannot index

The first RAG initialization may download/load embedding dependencies. Check the
terminal output, confirm the configured Obsidian path exists, and reindex only
after reviewing the displayed scope. Do not copy a vault into the repository or
commit the generated `data/` index.

### The New UI preview is missing

Confirm that `electron_motion_preview/package.json` and
`electron_motion_preview/package-lock.json` are present, then run
`.\setup.ps1`. The New UI starts with `.\run-new-ui.ps1`; it does not require
the Legacy Flutter SDK.

## Contributing

Keep changes narrow and traceable:

1. Read the current implementation and its documented boundary.
2. Keep routing and permission decisions in the Python Core.
3. Validate paths, arguments, data scope, and confirmation requirements.
4. Add focused tests for security-sensitive behavior.
5. Keep generated files, credentials, local profiles, and runtime logs out of
   commits.
6. Record what is implemented, what was actually verified, and what remains
   blocked or planned.

Do not claim a Target or Preview feature is current merely because a plan,
mockup, screenshot, or separate dirty worktree describes it.

## License

JARVIS is licensed under the Apache License 2.0. See [`LICENSE`](LICENSE) for
the complete terms.
