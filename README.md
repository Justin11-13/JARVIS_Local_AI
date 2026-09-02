# JARVIS Local AI Assistant

JARVIS is an open-source, local-first AI assistant designed to run on your own computer.

It uses local AI models through Ollama and provides controlled tools for interacting with Windows applications, development projects, Git repositories, and project files.

The project follows a tool-based architecture so the AI model does not receive unrestricted operating-system access.

---

## Current Features

### Local AI

- Local AI through Ollama
- Qwen3 8B as the current default model
- No GPT API required
- No Codex required
- Chinese and English natural-language interaction

### Multi-Step Agent Loop

JARVIS can complete requests that require multiple tool calls.

Example:

```text
打开 FYP，然后检查它的 Git status
```

Possible flow:

```text
User
  ↓
Qwen3 8B
  ↓
open_project
  ↓
Tool result
  ↓
git_status
  ↓
Tool result
  ↓
Final response
```

The agent loop also has a maximum step limit to reduce the risk of uncontrolled loops.

### Windows Application Discovery

JARVIS can automatically discover many installed Windows applications through Start Menu shortcuts.

Current capabilities include:

- Scan Windows Start Menu applications
- Generate a local application registry
- Exact application-name matching
- Partial application-name matching
- Fuzzy application-name matching
- Automatically refresh the registry when an application is not found

Example commands:

```text
打开 Chrome
```

```text
打开 Visual Studio Code
```

```text
打开 Spotify
```

The application registry is generated locally and should not be committed to Git.

### System Information

JARVIS can read basic local system information.

Current system tools:

- CPU usage
- RAM usage

Example:

```text
我的 CPU 和 RAM 现在用了多少？
```

### Automatic Project Discovery

JARVIS can scan configured development directories and automatically discover software projects.

Project scanning is restricted to configured project roots.

Example local configuration:

```json
{
  "roots": [
    "C:\\Users\\YOUR_USERNAME\\GitHub",
    "C:\\Users\\YOUR_USERNAME\\Documents\\GitHub"
  ]
}
```

Current framework detection includes:

- Laravel
- PHP
- Django
- Python
- Node.js
- Java Maven
- Java Gradle
- Git repositories

Example command:

```text
重新扫描我的 project
```

### Project Management

Current project capabilities:

- Refresh the project registry
- List discovered projects
- Get project information
- Detect project framework
- Detect whether a project uses Git
- Check whether the project path exists
- Open projects in Visual Studio Code

Example commands:

```text
我有哪些 project？
```

```text
告诉我 FYP 的资料
```

```text
打开 FYP
```

### Git Integration

Current Git capabilities:

- Check Git status
- Detect the current branch
- Detect modified files
- Detect untracked files

Example:

```text
检查 FYP 的 Git status
```

### Read-Only Project File Tools

JARVIS currently provides read-only project file access.

It can:

- List project files and folders
- Read supported text files
- Search project source code
- Search keywords
- Search classes
- Search functions
- Search routes
- Search models

Example commands:

```text
看看 FYP 根目录有什么文件
```

```text
读取 FYP 的 composer.json
```

```text
在 FYP 里面搜索 RoomController
```

### Project Path Protection

Project file tools are restricted to registered project directories.

Requests attempting to escape a registered project directory should be rejected.

Example:

```text
../../Windows/System32
```

should not be allowed to expose files outside the registered project.

### Open Interpreter Routing

Open Interpreter is an optional execution backend for complex local workflows
that are not covered by JARVIS native tools. JARVIS keeps routing and safety
policy in `services/task_router.py`.

Current routing modes:

- `manual`: Open Interpreter runs only when the user explicitly requests it.
- `ask`: JARVIS requests confirmation before non-explicit delegation.
- `automatic`: low-risk read-only tasks may run directly; medium-risk and
  high-risk tasks require confirmation.

Open Interpreter always requires an explicit existing subdirectory as its
workspace. Current directories, drive roots, and missing directories are
rejected. Pending requests can be confirmed or cancelled before execution.

### Development Auto-Reload

JARVIS includes a development workflow using `watchfiles`.

Run:

```powershell
.\dev.ps1
```

During development:

```text
Modify Python code
  ↓
Save file
  ↓
watchfiles detects the change
  ↓
JARVIS automatically restarts
  ↓
Updated code is loaded
```

This avoids manually restarting JARVIS after every code change.

---

## Architecture

```text
                         User
                          │
                          ▼
                     Qwen3 8B
                          │
                          ▼
                 JARVIS Agent Loop
                          │
                          ▼
                     Tool Router
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
     System            Projects            Git
     Skills             Skills            Skills
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                       Files
                       Skills
                          │
                          ▼
                       Services
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
       App Registry              Project Registry
             │                         │
             ▼                         ▼
    Windows Start Menu         Configured Scan Roots
             │                         │
             ▼                         ▼
   Installed Applications      Development Projects
```

The language model decides which registered tool is appropriate.

The JARVIS engine controls what tools actually exist and how those tools execute.

---

## Project Structure

```text
JARVIS_Local_AI/
├── app/
│   └── main.py
│
├── config/
│   ├── apps.example.json
│   ├── project_roots.example.json
│   └── projects.example.json
│
├── memory/
│   └── __init__.py
│
├── services/
│   ├── __init__.py
│   ├── app_registry.py
│   ├── notification_service.py
│   ├── project_registry.py
│   ├── task_manager.py
│   ├── task_router.py
│   └── agents/
│       └── open_interpreter.py
│
├── skills/
│   ├── files.py
│   ├── git.py
│   ├── project.py
│   └── system.py
│
├── tests/
│
├── .gitignore
├── dev.ps1
├── LICENSE
├── README.md
└── requirements.txt
```

Generated local configuration files such as `apps.json`, `projects.json`, and `project_roots.json` should remain local.

---

## Requirements

Current development environment:

- Windows 11
- Python 3
- Git
- Ollama
- Qwen3 8B

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Justin11-13/JARVIS_Local_AI.git
cd JARVIS_Local_AI
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Install Ollama

Install Ollama for Windows.

Then pull the current default model:

```powershell
ollama pull qwen3:8b
```

Confirm it is installed:

```powershell
ollama list
```

### 6. Configure project scan roots

Copy the example configuration:

```powershell
Copy-Item config\project_roots.example.json config\project_roots.json
```

Then edit:

```text
config/project_roots.json
```

Example:

```json
{
  "roots": [
    "C:\\Users\\YOUR_USERNAME\\GitHub",
    "C:\\Users\\YOUR_USERNAME\\Documents\\GitHub"
  ]
}
```

JARVIS only scans directories configured here.

### 7. Optional project configuration

If required:

```powershell
Copy-Item config\projects.example.json config\projects.json
```

Local project configuration should not be committed.

### 8. Start JARVIS

```powershell
python -m app.main
```

---

## Development Mode

JARVIS supports automatic restart during development.

### Install `watchfiles`

```powershell
.\.venv\Scripts\python.exe -m pip install watchfiles
```

### Start development mode

```powershell
.\dev.ps1
```

When Python source files change, JARVIS will automatically restart and load the updated code.

For normal usage, use:

```powershell
python -m app.main
```

---

## Example Commands

### Applications

```text
打开 Chrome
```

```text
打开 Spotify
```

```text
打开 Visual Studio Code
```

### System

```text
我的 CPU 和 RAM 现在用了多少？
```

### Project Discovery

```text
重新扫描我的 project
```

### Projects

```text
我有哪些 project？
```

```text
告诉我 FYP 的资料
```

```text
打开 FYP
```

### Multi-Step Request

```text
打开 FYP，然后检查它的 Git status
```

### Files

```text
看看 FYP 根目录有什么文件
```

```text
读取 FYP 的 composer.json
```

```text
在 FYP 里面搜索 RoomController
```

---

## Security Model

JARVIS currently follows an allow-listed tool architecture.

The AI model does not receive unrestricted PowerShell or shell access.

### Currently Allowed

- Open discovered applications
- Read CPU usage
- Read RAM usage
- Discover projects from configured roots
- List discovered projects
- Read project metadata
- Open projects
- Read Git status
- List project files
- Read project files
- Search project source code

### Currently Restricted

JARVIS does not currently provide unrestricted access to:

- Arbitrary PowerShell execution
- Arbitrary shell execution
- File deletion
- File modification
- Code modification
- Git commit
- Git push
- System configuration changes
- Administrator-level system operations

Higher-risk capabilities should be protected by a dedicated permission layer before being added.

---

## Local Configuration

The following files should remain local and should not be committed:

```text
.venv/
.env
config/apps.json
config/projects.json
config/project_roots.json
__pycache__/
*.pyc
*.db
*.sqlite
*.sqlite3
```

Use example configuration files instead:

```text
config/apps.example.json
config/projects.example.json
config/project_roots.example.json
```

---

## Development Status

JARVIS is currently an experimental local AI agent.

Current focus:

```text
Local AI
+
Multi-Step Agent Loop
+
Windows Application Discovery
+
Automatic Project Discovery
+
Git Status
+
Read-Only Developer Tools
```

It is not yet intended to provide unrestricted autonomous control of a computer.

---

## Product Master Plan

This section describes the intended product direction. A feature marked
**Planned** is not available yet. Existing features remain deliberately
conservative while the broader permission system is built.

### Product Vision

JARVIS is intended to become a local-first personal Windows AI assistant:
not only a chatbot, but a system that can understand a request, select a safe
executor, observe the result, continue when appropriate, and notify the user.

~~~text
User
 ↓
Understand intent
 ↓
Choose tool or agent
 ↓
Check policy and permission
 ↓
Execute
 ↓
Observe result
 ↓
Notify user
~~~

### Product Architecture

~~~text
                         JARVIS
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
   Voice Interface     JARVIS Brain       Desktop UI
          │                 │                  │
    Wake word / STT     Intent / Router      Settings
          │                 │                  │
          └──────────── TaskRouter ───────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   Native Tools         Local AI          Specialist Agents
   Windows / APIs       Ollama / Qwen     Open Interpreter / Codex
                            │
                      Permission Layer
                            │
                      Task Execution
                            │
                  Monitor and Notification
~~~

**Implemented foundation:** local Qwen through Ollama, a text conversation
loop, native tools, TaskRouter, TaskManager, terminal notifications, and Open
Interpreter routing safeguards.

**Planned:** voice, desktop UI, settings, local API, browser control, hardware
integrations, and optional cloud-model providers.

### Brain, Models, and Executors

The JARVIS Brain interprets user intent. It does not receive unrestricted
system access; Python policy decides what is actually allowed.

| Component | Role | Current status |
| --- | --- | --- |
| Local Qwen via Ollama | Conversation, intent understanding, simple reasoning, and tool selection. | Implemented; default model is qwen3:8b. |
| Native JARVIS tools | Small supported actions such as opening apps, reading system information, project inspection, Git status, and read-only file access. | Implemented. |
| Open Interpreter | General local workflows and multi-file execution beyond native-tool coverage. | Implemented with explicit workspace validation, risk classification, and manual / ask / automatic modes. |
| Codex or another cloud provider | Heavy software-engineering work such as repository-wide debugging, refactoring, and implementation/test loops. | Planned and optional. |
| Future specialist agents | Clearly scoped capabilities such as browser or hardware control. | Planned. |

Intended model routing:

~~~text
Simple or normal work        → Local Qwen + Native tools
General local workflows      → Open Interpreter when policy allows
Heavy coding work            → Optional Codex or another specialist
~~~

Normal usage should remain local-first. Cloud models are an optional
enhancement, not a requirement.

### Computer, Application, Browser, and Project Control

Application control is planned in three levels:

1. **Native/direct control** — predictable actions through Windows or supported
   APIs, such as opening an application, reading system status, or controlling
   volume.
2. **Generic computer control** — a controlled agent can operate an interface
   when no dedicated integration exists.
3. **Dedicated integration** — high-value integrations, for example browser,
   Spotify, Windows, or supported hardware APIs.

**Implemented foundation:** Start Menu application discovery, app opening,
project discovery from configured roots, registered-project information,
opening projects in VS Code, Git status, and read-only project file tools.

**Planned:** closing applications, volume/media controls, browser automation,
project test execution, Git diff, diagnostics, safe file changes, and
dedicated hardware integrations. Hardware support must use a documented vendor
API, CLI, or supported controller; Open Interpreter alone does not create
hardware support.

### Voice, Desktop UI, and Settings

**Planned voice flow:**

~~~text
Microphone
 ↓
Wake word: Jarvis
 ↓
Speech-to-text
 ↓
JARVIS Brain and TaskRouter
 ↓
Execution
 ↓
Text-to-speech
~~~

A wake word should begin a short conversation session so the user can make
follow-up requests without repeating it. The planned stack includes
openWakeWord, voice activity detection, faster-whisper, and Piper or Kokoro.

**Planned desktop experience:**

- Desktop UI, system tray, background lifecycle controls, and notifications.
- Settings for model/provider, microphone, wake word, conversation timeout,
  project roots, application scan roots, routing mode, and agent settings.
- Desktop orb/pet, status dashboard, Liquid Glass visual language, and
  accessible reduced-motion behavior.

Users should configure these options in the UI rather than editing model or
scan-path constants in source code.

### Permission and Security Model

JARVIS must enforce policy before an executor starts. A prompt or model
decision is never the final security boundary.

~~~text
User request
 ↓
Risk classification
 ↓
Permission check
 ↓
Allowed?
 ├── No  → reject or offer a restricted safe action
 └── Yes → Native tool / Open Interpreter / future agent
~~~

The planned trust model has four levels:

| Level | Condition | Intended permissions |
| --- | --- | --- |
| 0 — Locked | Windows device is locked. | Very limited low-risk actions; no private data or privileged work. |
| 1 — Restricted | Device unlocked but speaker is not verified. | General questions and selected low-risk actions only. |
| 2 — Trusted | Authorized Windows session and verified voice, where voice is enabled. | Broader private/project access, still subject to policy. |
| 3 — Critical confirmation | A destructive, privileged, external, or state-changing action is requested. | Explicit confirmation is required for that specific action. |

Voice verification is an additional trust signal, never the only authorization
factor for destructive or privileged operations.

**Implemented safeguards:** explicit Open Interpreter workspace requirements;
manual, ask, and automatic routing modes; LOW / MEDIUM / HIGH risk
classification; and confirmation for medium/high-risk automatic work.

**Planned safeguards:** the full locked/restricted/trusted state model,
credential protection, file-write permissions, terminal/PowerShell policy,
Git commit/push approval, and external-message approval.

### Task Lifecycle and Notifications

A task should be tracked rather than simply launched and forgotten.

~~~text
QUEUED → RUNNING → OBSERVING → COMPLETED
                    ↓
                  FAILED
~~~

Complex agents may retry a bounded, safe recovery loop before reporting a
failure.

**Implemented foundation:** managed Open Interpreter tasks track creation,
start, completion, duration, result, and error; terminal notifications report
completion or failure.

**Planned:** observation/retry policy, task history, Windows notifications,
desktop UI notifications, and voice notifications.

### Local API

**Planned:** a FastAPI local API will keep the desktop UI separate from JARVIS
internal modules.

~~~text
Desktop UI
 ↓
FastAPI Local API
 ↓
JARVIS Core
 ↓
TaskRouter
 ↓
Tools / Models / Agents
~~~

Likely local endpoints include task, status, apps, projects, settings, and
model. The API must preserve the same policy checks as the CLI; it must not
become a bypass around TaskRouter.

### Delivery Phases

#### Phase 0 — Current Foundation

- [x] Ollama + qwen3:8b, agent tool loop, and native application/system tools.
- [x] Project discovery, project registry, Git status, and read-only project
  file tools.
- [x] Open Interpreter adapter, workspace validation, risk routing, pending
  confirmation, task lifecycle records, terminal notification, and TaskRouter
  extraction.

#### Phase 1 — Safe Developer Workflow

- [ ] Git diff and project diagnostics.
- [ ] Run tests for registered projects and report results.
- [ ] Safe file creation and code modification with confirmation.
- [ ] Code review and bounded test-and-fix workflows.
- [ ] Explicit Git commit and Git push approval flows.
- [ ] Optional Codex adapter for heavy coding tasks.

#### Phase 2 — Full Permission Boundary

- [ ] Locked, restricted, and trusted modes.
- [ ] Critical-action confirmation for deletion, installations, admin actions,
  system settings, credentials, and external communications.
- [ ] Explicit terminal, PowerShell, browser, and file-write policies.

#### Phase 3 — Local API and Desktop Product

- [ ] FastAPI local API.
- [ ] Desktop settings, system tray, lifecycle controls, and status dashboard.
- [ ] Windows notifications and accessible visual design.

#### Phase 4 — Voice and Multimodal Interaction

- [ ] Wake word, microphone input, STT, TTS, and conversation sessions.
- [ ] Screenshot capture, screenshot understanding, and visual error analysis.
- [ ] Voice verification as an additional trust signal.

#### Phase 5 — Expansion

- [ ] Local SQLite task history, project context, and user preferences.
- [ ] Browser and dedicated application integrations.
- [ ] Supported hardware integrations.
- [ ] Evaluate web, mobile, macOS, Linux, and multi-device support after the
  Windows local-first workflow is stable.

### Non-Negotiable Engineering Rules

- Do not expose unrestricted shell, PowerShell, or administrator access to a
  language model.
- Prefer native tools whenever they safely support the request.
- Keep policy in Python and route all new agents through TaskRouter.
- Validate paths, workspaces, and tool arguments before execution.
- Require confirmation for destructive, privileged, external, or
  state-changing actions.
- Keep local AI as the default path whenever practical.

---

## AI Model

The current default model is:

```text
Qwen3 8B
```

running locally through Ollama.

The architecture is designed so the underlying model can be replaced in the future without rewriting the entire tool system.

Possible future model routing:

```text
Fast Model
  ↓
Simple commands and routing

Main Model
  ↓
Conversation and tool usage

Deep Model
  ↓
Complex reasoning and development tasks

Vision Model
  ↓
Screenshot and image understanding
```

---

## Contributing

Contributions are welcome.

When adding new tools:

1. Keep each tool focused on one clear capability.
2. Do not give the language model unrestricted shell access.
3. Validate tool arguments before execution.
4. Validate file paths before accessing files.
5. Add permission checks before destructive operations.
6. Keep platform-specific implementation separated where practical.
7. Add tests for security-sensitive functionality.

---

## License

This project is licensed under the Apache License 2.0.

See the `LICENSE` file for details.
