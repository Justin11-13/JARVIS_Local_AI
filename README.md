# JARVIS Local AI Assistant

JARVIS is an open-source, local-first AI assistant designed to run on your own computer.

It uses local AI models through Ollama and provides controlled tools for interacting with Windows, software projects, Git, and project files.

## Current Features

- Local AI using Ollama
- Qwen3 8B support
- Multi-step agent loop
- Open Windows applications
- Check CPU and RAM usage
- Register and open projects
- Check Git status
- Read project files
- Search project code

## Requirements

- Windows 11
- Python 3
- Ollama
- Git
- Qwen3 8B

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd JARVIS
```

### 2. Create a Python virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Install Ollama

Install Ollama for your operating system.

Then download the default JARVIS model:

```powershell
ollama pull qwen3:8b
```

### 6. Configure projects

Create your local project configuration:

```powershell
Copy-Item config\projects.example.json config\projects.json
```

Then edit:

```text
config/projects.json
```

Example:

```json
{
  "projects": {
    "Example Project": {
      "path": "C:\\path\\to\\your\\project",
      "framework": "Laravel",
      "description": "Example project"
    }
  }
}
```

### 7. Start JARVIS

```powershell
python -m app.main
```

## Example Commands

You can ask JARVIS:

```text
打开 VS Code
```

```text
我的电脑 RAM 用了多少？
```

```text
打开 FYP
```

```text
检查 FYP 的 Git status
```

```text
看看 FYP 根目录有什么文件
```

```text
读取 FYP 的 composer.json
```

## Architecture

```text
User
  ↓
Local AI Model
  ↓
JARVIS Agent Loop
  ↓
Tool Router
  ↓
JARVIS Skills
  ├── System
  ├── Projects
  ├── Git
  └── Files
  ↓
Local Computer
```

The AI model does not receive unrestricted operating-system access.

Instead, JARVIS exposes explicitly registered tools that the model may request.

## Security

JARVIS follows a controlled tool-based architecture.

The AI does not currently receive unrestricted shell access.

Current tools are designed around specific operations such as:

- Opening supported applications
- Reading CPU and RAM usage
- Opening registered projects
- Reading Git status
- Listing project files
- Reading project files
- Searching project code

High-risk capabilities such as arbitrary terminal execution, file deletion, Git push, and system modification should require additional permission controls.

## Roadmap

- [ ] Git diff
- [ ] Automated project tests
- [ ] Permission system
- [ ] Code editing tools
- [ ] Voice wake word
- [ ] Speech-to-text
- [ ] Text-to-speech
- [ ] Long-term memory
- [ ] Desktop UI
- [ ] Android support
- [ ] iOS support
- [ ] macOS support
- [ ] Linux support
- [ ] Web interface

## Local Configuration

The following files should remain local and should not be committed:

```text
.venv/
.env
config/projects.json
```

Use the provided example configuration:

```text
config/projects.example.json
```

## License

This project is licensed under the Apache License 2.0.

See the `LICENSE` file for details.