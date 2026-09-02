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
│   └── project_registry.py
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

## Roadmap

### Developer Agent

- [ ] Git diff
- [ ] Automated project tests
- [ ] Project diagnostics
- [ ] Permission layer
- [ ] Safe file creation
- [ ] Safe code modification
- [ ] Code review tools
- [ ] Test-and-fix agent loop
- [ ] Git commit approval workflow
- [ ] Git push approval workflow

### Voice

- [ ] Wake word detection
- [ ] "Jarvis" voice wake
- [ ] Built-in microphone support
- [ ] Speech-to-text
- [ ] Text-to-speech
- [ ] Continuous conversation mode

### Memory

- [ ] SQLite memory
- [ ] Recent project memory
- [ ] Task history
- [ ] User preferences
- [ ] Long-term memory retrieval

### Vision

- [ ] Screenshot capture
- [ ] Screenshot understanding
- [ ] Visual error analysis
- [ ] UI debugging

### Interface

- [ ] Desktop UI
- [ ] Liquid Glass interface
- [ ] System status dashboard
- [ ] Voice activity indicator
- [ ] Device management

### Cross-Platform

- [ ] Android
- [ ] iOS
- [ ] macOS
- [ ] Linux
- [ ] Web interface
- [ ] Multi-device communication

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