# JARVIS Local AI Assistant — Project Scope

## 1. Product Scope and Current Baseline

### Current implemented scope / 当前已实现范围

JARVIS currently provides a local Flutter desktop shell and loopback API. Its
reliable, implemented capabilities are:

- live CPU, physical-memory, and supported NVIDIA GPU monitoring through the
  local API;
- explicit system/project API operations: project listing, registered-project
  Git status, file listing, reading, searching, and project-registry refresh;
- native Core tools for application discovery/opening, system information,
  project discovery, and registered-project read-only file work;
- an Open Interpreter adapter with workspace validation, routing modes, risk
  classification, confirmation, task records, and notifications;
- a desktop shortcut that starts the API with the app and stops the API instance
  it owns when the window closes.

The desktop chat composer is **not** a natural-language tool router yet. It
currently supports exact greetings and responses to an already-pending Open
Interpreter confirmation. A CPU/RAM request typed into chat will not yet call
the telemetry endpoint, and “打开 Chrome” will not yet call either the native
`open_app` tool or Open Interpreter. The Device page and Assistant monitor show
telemetry; application opening requires an explicit Core/API/router caller.

### Explicit exclusions / 明确排除

The current product has no Ollama, Qwen, other local model runtime, GPT API,
ChatGPT UI executor, Codex executor, automatic browser control, unrestricted
PowerShell, automatic file-writing chat workflow, or autonomous computer
control.

### Target Product Goal / 目标产品范围

Build an open-source, local-first Windows AI assistant named JARVIS.

JARVIS should behave like a personal desktop AI assistant that can understand natural-language requests, use direct Python/PowerShell for small supported work, use Open Interpreter only on demand for bounded local workflows, hand general reasoning to the authenticated ChatGPT UI, use Codex for software-engineering work, manage tasks, and notify the user when work is completed.

The long-term goal is to make JARVIS usable by normal users without requiring them to write code.

JARVIS does not require a local language model runtime and must not add Ollama,
Qwen, or a GPT API client. ChatGPT interaction is through the user-facing,
authenticated UI only; Codex is the specialist for heavy coding work.

External AI or specialist agents may be integrated when useful, but they should remain optional.


# 2. Target Architecture

Target architecture:

User Text / Voice
↓
JARVIS Core
↓
Task Router
├── Native Python / PowerShell Tools
├── Open Interpreter (on demand)
├── ChatGPT UI (planned, no API)
├── Codex (planned)
└── Future Agents
↓
Task Manager
↓
Notification System
├── Terminal
├── Windows Notification
├── Desktop Pet / Orb
└── Voice


# 3. Current Native JARVIS Capabilities

JARVIS currently supports native tools for common and safe operations.

## Windows Applications

- Discover installed applications from Windows Start Menu / registry-like app discovery
- Open installed applications
- Exact matching
- Partial matching
- Fuzzy matching

## System Information

- Read CPU usage
- Read RAM usage
- Uses psutil

## Project Registry

- Automatically discover development projects from configured roots
- Detect common frameworks / project types
- Laravel / PHP
- Django / Python
- Node.js
- Maven
- Gradle
- Git

Available project functions:

- list projects
- get project information
- open project in VS Code
- refresh project registry

Project discovery only scans configured project roots.

## Git

- Read git status

## Read-Only File Tools

Native file tools are restricted to registered projects.

Available functions:

- list files
- read file
- search files

These tools are read-only.

They must not modify files.

Project root should use "." as relative_path.

Do not use arbitrary Windows absolute paths as native project relative paths.


# 4. Open Interpreter Integration

Open Interpreter is integrated as a general-purpose local execution backend.

It should NOT replace JARVIS.

JARVIS remains the main assistant and router.

Open Interpreter acts as execution hands for workflows that are not naturally supported by native JARVIS tools.

Typical Open Interpreter use cases:

- arbitrary local directory workflows
- batch file processing
- multi-file analysis
- generating summaries from local files
- creating or modifying files
- renaming / moving files
- dynamic command execution
- multi-step local workflows
- ad-hoc computer tasks

Simple operations should remain native whenever possible.

Examples:

open application
→ Native tool

CPU / RAM
→ Native tool

git status
→ Native tool

read one registered project file
→ Native tool

complex arbitrary local directory processing
→ Open Interpreter


# 5. Open Interpreter Adapter

Current adapter:

services/agents/open_interpreter.py

Open Interpreter is invoked through:

interpreter exec

The adapter:

- validates availability
- accepts task
- accepts workspace
- supports workspace restriction
- captures stdout
- captures stderr as execution log
- returns success / failed / timeout
- uses a timeout
- supports --skip-git-repo-check

The adapter must not guess the workspace.


# 6. Workspace Safety

Before Open Interpreter can run:

- task must exist
- workspace must exist
- workspace must be a directory
- workspace must be explicit
- do not use "/"
- do not use "\\"
- do not use "."
- do not use current working directory as guessed workspace
- do not allow an entire drive root such as C:\
- preserve user restrictions such as:
  - do not modify files
  - read only
  - do not delete anything


# 7. Open Interpreter Routing Modes

JARVIS supports three routing modes.

## Manual

Open Interpreter is only used when the user explicitly requests it.

Example:

"Use Open Interpreter to analyze C:\Users\...\folder"

Normal complex tasks must not automatically trigger Open Interpreter.

## Ask

JARVIS may determine that Open Interpreter is appropriate.

It must first create a pending request and ask the user for confirmation.

Flow:

User task
↓
JARVIS recommends Open Interpreter
↓
request_open_interpreter
↓
awaiting_confirmation
↓
User yes / no
↓
If yes:
delegate_to_open_interpreter

This mode currently works.

## Automatic

JARVIS may automatically use Open Interpreter depending on risk.

LOW risk
→ execute automatically

MEDIUM risk
→ ask first

HIGH risk
→ ask first

Automatic routing is implemented and tested.


# 8. Open Interpreter Risk Classification

Current risk levels:

## LOW

Read-only or analysis work.

Examples:

- read files
- analyze files
- list directory contents
- generate summaries
- read-only diagnostics
- inspect data
- "do not modify anything"
- read only

Automatic mode may execute LOW risk tasks directly.

## MEDIUM

Tasks that change local state.

Examples:

- create file
- edit file
- rename file
- move file
- copy file
- write file
- replace file contents
- install software

Automatic mode must ask for confirmation.

## HIGH

Destructive, privileged, or system-level operations.

Examples:

- delete files
- remove files
- wipe / clear content
- format disk
- administrator operations
- registry changes
- shutdown
- reboot
- system configuration changes

Automatic mode must never execute these directly.

It must request confirmation first.

Risk classification currently uses keyword-based rules.

Important:

Negation must be handled.

Example:

"不要修改任何东西"

must NOT be classified as MEDIUM just because it contains "修改".

Explicit read-only phrases should override medium-risk modification keywords unless a high-risk operation is present.


# 9. Code-Level Routing Guards

Do not rely only on the LLM system prompt.

Routing rules must also be enforced in Python.

Current guards include:

- manual mode blocks automatic Open Interpreter requests
- ask mode blocks direct non-explicit delegation
- automatic mode converts LOW risk to direct execution
- automatic MEDIUM / HIGH becomes confirmation request
- refresh_project_registry cannot be used just because a random local path exists
- project scanning must only happen when the user explicitly asks to scan / discover / refresh projects

The goal is policy-controlled routing rather than allowing the model to freely execute any tool.


# 10. Pending Open Interpreter Confirmation

JARVIS keeps:

pending_open_interpreter_request

Pending request contains:

- task
- workspace
- risk

Accepted confirmation examples:

- yes
- y
- 继续
- 可以
- 确认
- 同意
- 好
- 好的
- ok
- okay

Rejected examples:

- no
- n
- 不要
- 取消
- 不同意
- 不用
- 算了

If confirmed:

Open Interpreter executes the saved task.

If rejected:

The pending request is cleared.


# 11. Task Manager

Current file:

services/task_manager.py

Every managed agent task should track:

- id
- title
- agent
- status
- created_at
- started_at
- completed_at
- date
- duration_seconds
- result
- error

Supported statuses should include:

- queued
- running
- waiting_approval
- completed
- completed_with_warnings
- failed
- cancelled

Task Manager is already connected to Open Interpreter.

Open Interpreter tasks currently record:

- creation time
- start time
- completion time
- duration
- result
- error


# 12. Notification System

Current file:

services/notification_service.py

Current first-level notification output:

Terminal notification

Example:

[JARVIS Notification] 任务已完成。

The notification service should later support:

- terminal
- Windows toast
- desktop pet / orb
- voice


# 13. Current Main Runtime

Current entry point:

python -m app.main

Development auto-reload:

dev.ps1

Development should use the project's virtual environment executables.

The current main loop:

User input
↓
Codex executor (when configured)
↓
Action proposal / tool selection
↓
Python routing guards
↓
Tool execution
↓
Tool result returned to the requesting interface
↓
Final JARVIS response


# 14. Current Project Structure

Approximate structure:

JARVIS/
├── app/
│   └── main.py
│
├── config/
│   ├── apps.example.json
│   ├── apps.json
│   ├── project_roots.example.json
│   ├── project_roots.json
│   ├── projects.example.json
│   └── projects.json
│
├── memory/
│   └── __init__.py
│
├── services/
│   ├── __init__.py
│   ├── app_registry.py
│   ├── project_registry.py
│   ├── task_manager.py
│   ├── task_router.py
│   ├── notification_service.py
│   └── agents/
│       ├── __init__.py
│       └── open_interpreter.py
│
├── skills/
│   ├── files.py
│   ├── git.py
│   ├── project.py
│   └── system.py
│
├── tests/
├── dev.ps1
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore


# 15. Current Completed Milestones

Completed:

- Native tools, TaskRouter, and Open Interpreter integration
- agent tool loop
- Windows application discovery
- open app
- CPU / RAM
- project discovery
- project information
- open project
- git status
- read-only project file tools
- Open Interpreter integration
- Open Interpreter workspace validation
- missing-information follow-up
- Task Manager integration
- task date / timestamps
- duration tracking
- notification service
- terminal notification
- Open Interpreter Manual mode
- Open Interpreter Ask mode
- Open Interpreter Automatic mode
- LOW / MEDIUM / HIGH risk routing
- code-level routing guards
- project-registry routing guard
- TaskRouter refactor for Open Interpreter routing policy


# 16. Current Routing Boundary

Open Interpreter routing policy is now centralized in:

services/task_router.py

TaskRouter is responsible for:

- routing mode
- Open Interpreter risk classification
- explicit user intent checks
- policy enforcement
- choosing Native vs Open Interpreter vs future Codex
- deciding whether confirmation is required

app/main.py keeps the conversation loop, tool definitions, and terminal output.

The next routing work should extend this boundary for future agents without
weakening the existing native-tool and Open Interpreter guards.

Target:

User
↓
JARVIS Core
↓
TaskRouter
├── Native
├── Open Interpreter
├── Codex
└── Future Agents


# 17. Codex Integration — Future

Codex should become the specialist for heavy coding tasks.

Examples:

- large repo changes
- multi-file coding
- refactoring
- implementation + test loops
- bug fixing
- repository-wide changes

Preferred routing:

Simple coding question
→ Codex (when configured)

Simple project inspection
→ Native tools

General local execution
→ Open Interpreter

Heavy coding / repository changes
→ Codex

Codex should not replace JARVIS.

JARVIS remains the coordinator.


# 18. Future Desktop Product

Long-term desktop experience:

- GUI
- settings page
- system tray
- background operation
- desktop orb / pet
- notifications
- voice interaction
- wake word
- microphone input
- speaker verification
- configurable routing modes
- configurable reasoning backend
- project roots management
- backend lifecycle controls


# 19. Future Voice Architecture

Possible future stack:

Wake word
→ openWakeWord

Voice Activity Detection
→ VAD

Speech-to-text
→ faster-whisper

Text-to-speech
→ Piper or Kokoro

Speaker verification
→ owner voice verification

Important:

Voice verification must not be the only authorization factor for destructive or privileged actions.


# 20. Permission Model

Future privileged actions should use a trust-gated permission model.

Heavy / privileged actions are allowed only when:

- the computer is already unlocked by the authorized user
- the current speaker is verified as the authorized user's voice

If either condition fails:

JARVIS stays in restricted mode.

Restricted mode permits only simple, low-risk operations.


# 21. Development Principles

When modifying this project:

- inspect the existing code before changing it
- preserve working functionality
- prefer small incremental changes
- do not over-engineer
- do not rewrite working modules unnecessarily
- reuse existing services
- keep routing policy separate from execution adapters
- keep agent adapters independent
- native tools should remain simple and safe
- do not give Open Interpreter unrestricted authority
- do not remove validation or routing guards
- never silently weaken permission checks
- test after each routing change
