JARVIS — Local-first Windows AI Assistant

JARVIS — 本地优先的 Windows AI 助手

JARVIS is an open-source, local-first Windows personal AI assistant designed around strict separation of intelligence, control, execution, personal data, structured knowledge, and engineering authority.

JARVIS 是一个开源、本地优先的 Windows 个人 AI 助手。系统通过明确边界，将智能、控制、执行、个人数据、结构化知识及工程权限分离。

AI can propose actions, but JARVIS Core decides what is allowed to execute.
AI 可以提出操作，但最终是否允许执行由 JARVIS Core 决定。

⸻

Table of Contents / 目录

1. Overview / 项目概览
2. Internal Test / 当前内测版本
3. Current Capabilities / 当前能力
4. Installation & Development / 安装与开发
5. Architecture & Security / 架构与安全
6. Roadmap / 路线图
7. Contributing & License / 贡献与许可证

⸻

1. Overview / 项目概览

1.1 Authority Model / 权威模型

Selected AI Provider / Model
        ↓
Intelligence / 智能
JARVIS Core
        ↓
Policy · Routing · Permission · Control
策略 · 路由 · 权限 · 控制
Python Tools / Platform Adapters
        ↓
Bounded Execution / 有界执行
Local Storage
        ↓
Personal & Operational Data
个人与运行数据
Obsidian
        ↓
Optional Structured Knowledge
可选结构化知识
Codex Handoff
        ↓
Authorized Engineering Escalation
授权后的工程升级路径

Authority / 权威	Responsibility / 职责
Selected AI	Reasoning and language intelligence / 推理与语言智能
JARVIS Core	Policy, routing, permissions and lifecycle control / 策略、路由、权限和生命周期控制
Python Tools	Bounded system execution / 有界系统执行
Local Storage	Personal and operational runtime data / 个人与运行数据
Obsidian	Optional structured knowledge / 可选结构化知识
Codex Handoff	Authorized engineering escalation / 授权工程升级

⸻

1.2 Editions / 版本

Edition / 版本	Purpose / 用途	Available Surfaces / 页面
JARVIS Internal Test	Completed tester-facing capabilities / 已完成、供测试者使用的功能	Assistant, History, Core, Tool Results, Device, AI Connections, Usage, Settings, Memory, Knowledge, Theme, Voice, Events, Errors
JARVIS Development	Active development and future capability validation / 开发中功能和未来能力验证	Internal Test + Tasks, Working Context, Automation, Codex Handoff development surfaces

Both editions share the same architecture and Core contracts.

Internal Test not only hides unfinished navigation, but also blocks direct access to unfinished development routes.

两个版本共享相同架构与 Core contracts。

Internal Test 不只隐藏尚未完成的页面入口，也会阻止直接访问相关开发路由。

⸻

2. Internal Test / 当前内测版本

2.1 Current Milestone / 当前里程碑

JARVIS Internal Test v0.1.0

The current Internal Test packages the following components into one Windows installer:

* Electron desktop application
* Local Python / FastAPI JARVIS Core
* Windows platform adapters
* Bundled Windows x64 Codex CLI
* Codex App Server transport
* Local configuration and runtime storage

当前 Internal Test 将以下组件封装为一个 Windows 安装器：

* Electron 桌面端
* 本地 Python / FastAPI JARVIS Core
* Windows Platform Adapter
* 内置 Windows x64 Codex CLI
* Codex App Server transport
* 本地配置与运行数据存储

Unfinished product surfaces are excluded from the Internal Test edition.

尚未完成的产品页面不会进入 Internal Test。

⸻

2.2 Release Status / 发布状态

Release: v0.1.0 GitHub Pre-release

Installer:

JARVIS-Internal-Test-0.1.0-Setup.exe

Size:

816,647,011 bytes

SHA-256:

3501645D93FF9A73402998488A0BA4D90E470F919F8563CCA4501FD17E4EE8B3

The rebuilt installer has been published as a GitHub pre-release.

Clean Windows machine acceptance is still pending.

The installer is currently unsigned, so Windows may display SmartScreen or application-control warnings.

最终重封安装包已经发布为 GitHub Pre-release。

目前仍未完成独立干净 Windows 环境验收。

安装器尚未进行代码签名，因此 Windows 可能显示 SmartScreen 或应用控制警告。

This is an internal pre-release, not a stable production release.
当前版本属于内测预发布版本，不是稳定生产版本。

⸻

2.3 Known Limitations / 已知限制

Current known limitations include:

* Clean Windows machine installer acceptance is pending.
* Installer is not code-signed.
* Target SQLite operational-memory migration is incomplete.
* Target persistent task architecture is incomplete.
* Wake Word is not yet a completed Internal Test capability.
* Microphone STT is not yet complete.
* Voice Interrupt is not yet complete.
* Full Automation Engine is not yet complete.
* Proactive assistance is not yet complete.
* Full Screen Awareness is not yet complete.
* Codex Handoff is not yet complete.
* Full Knowledge Manager governance is not yet complete.
* End-to-end RAG acceptance remains future work.
* Hardware metrics depend on device support.
* Unsupported hardware values must report unavailable.
* AI availability depends on provider, account access, model availability, quota and network.

⸻

3. Current Capabilities / 当前能力

3.1 Assistant & Core / 助手与 Core

The current Core can:

* Start or reuse the local Core at 127.0.0.1:8765
* Report Core health separately from AI availability
* Support multi-turn conversations
* Reopen saved local conversations
* Stream AI responses when supported
* Render a constrained safe Markdown subset
* Preserve truthful execution state

Supported execution states include:

completed
failed
awaiting_confirmation
denied
session_busy

JARVIS does not convert failure, denial or confirmation requirements into fake success states.

JARVIS 不会将失败、拒绝或等待确认状态包装成成功。

⸻

3.2 Windows Tools / Windows 工具

JARVIS exposes Windows capabilities through explicitly registered tools rather than unrestricted shell access.

Current categories include:

* System information
* Battery information
* Network information
* Process information
* Audio-device information
* Project inspection
* Git information
* File operations
* Application launch
* Volume control
* Media control
* Brightness control
* Clipboard operations
* Wallpaper management
* Window management
* Selected keyboard and mouse operations

Higher-risk actions such as:

Sleep
Restart
Shutdown

require explicit user confirmation.

The AI does not receive unrestricted shell or administrator authority.

所有实际操作仍由 JARVIS Core 控制。

⸻

3.3 Desktop Experience / 桌面体验

The Electron desktop currently provides:

* Animated WebGL JARVIS Core
* Amber theme
* Cyan theme
* Violet theme
* Matrix theme
* Custom theme colors
* Low Motion mode
* Background mode
* Optional start-on-login
* Live hardware information when supported
* Tool Results surface
* Events surface
* Errors surface
* Windows OneCore voice support
* Optional automatic reading of new replies
* JARVIS-only token usage when provider usage data is available
* GitHub Release update checking

Custom theme values include:

background
surface
border
accent
text
muted text
Core A
Core B

⸻

3.4 AI Connections / AI 连接

JARVIS never bundles developer credentials.

Every tester must use their own account or API key.

JARVIS 不会将开发者凭据打包进安装器。

⸻

3.4.1 Managed ChatGPT Connection

Current transport:

JARVIS
    ↓
Codex App Server transport
    ↓
Bundled Windows x64 Codex CLI
    ↓
Official user authentication

The bundled Codex CLI is the runtime component.

Codex App Server is the communication transport used by JARVIS.

They are not separate AI providers.

Connection verification requires a real non-fixed message.

A selected model name alone is not proof of connectivity.

⸻

3.4.2 Direct API

Current supported provider categories:

* OpenAI
* Gemini
* DeepSeek
* Supported OpenAI-compatible endpoints

Possible failures remain explicit:

Invalid API key
Unavailable model
Quota exhausted
Provider error
Network failure
Invalid endpoint

JARVIS does not silently switch providers.

⸻

3.5 Local Data / 本地数据

Internal Test writable data is stored under:

%LOCALAPPDATA%\JARVIS\InternalTest

Local data may include:

* Conversations
* Settings
* Runtime state
* Usage records
* Tool results
* Events
* Errors
* Existing memory records
* Runtime/task records generated by Core

Unfinished task runs are not silently resumed after restart.

⸻

3.6 Memory / 记忆

Current

Memory UI
Existing local records
Runtime memory behavior

Target

SQLite MemoryStore
User Model
Preferences
Memory Review
Context Builder integration
Migration and recovery rules

The existence of the Memory page does not mean the final target Memory architecture is complete.

⸻

3.7 Knowledge & Obsidian / 知识与 Obsidian

Obsidian is optional.

It is not required for:

* Chat
* Core health
* Local tools
* Settings
* Local conversations

Authority separation:

Local Storage
    ↓
Personal / operational data
Obsidian Vault
    ↓
Structured knowledge

Disconnecting a Vault removes JARVIS access without deleting original notes.

Registration, indexing, retrieval and AI usage are different stages:

Registered
≠ Indexed
≠ Retrieved
≠ Used by AI

⸻

3.8 Events / 事件

The current Internal Test includes an Events surface for recorded runtime events.

Current

Runtime event records
Events UI
Basic observability

Target

Event Bus
Publish / Subscribe
Event filtering
Event routing
Proactive triggers
Presence events
Automation integration

The current Events page does not mean the full Event Bus architecture is complete.

⸻

4. Installation & Development / 安装与开发

4.1 User Requirements / 用户系统要求

Internal Test requires:

* Windows 10 or Windows 11
* x64 architecture
* GPU/driver capable of running the Electron WebGL surface
* Internet access when using cloud AI providers
* A supported ChatGPT/Codex account or supported API provider credentials

Obsidian is optional.

⸻

4.2 Bundled Runtime / 已包含运行环境

Internal Test already includes:

* Application runtime
* Python Core
* Windows x64 Codex CLI runtime

Testers do not need to separately install:

Python
Node.js
npm
Flutter
Codex CLI

⸻

4.3 Install / 安装

Current installer artifact:

electron_motion_preview_internal_test\
└─ release\
   └─ JARVIS-Internal-Test-0.1.0-Setup.exe

Installation flow:

1. Run JARVIS-Internal-Test-0.1.0-Setup.exe
2. Choose an installation directory
3. Complete installation
4. Launch JARVIS Internal Test
5. Open Core
6. Confirm Core reports ready
7. Open AI Connections
8. Configure one connection
9. Send a real message
10. Confirm a real provider response

⸻

4.4 Source Development / 源码开发

Development requirements:

* Windows 10 / 11 x64
* Git
* Python compatible with repository requirements
* Node.js
* npm
* PowerShell

Flutter is only required for the legacy desktop client.

Flutter is not required for the Electron Internal Test edition.

⸻

4.5 Build from Source / 从源码构建

git clone https://github.com/Justin11-13/JARVIS_Local_AI.git
cd JARVIS_Local_AI
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd electron_motion_preview_internal_test
npm ci
npm run verify:static
npm run package:win

Build pipeline:

Python source
    ↓
PyInstaller onedir Core
    ↓
Bundled Windows x64 Codex CLI
    ↓
Electron application
    ↓
x64 NSIS installer

Generated dependencies and build outputs are not source authority.

⸻

4.6 Source Directories / 源码目录

Development edition:

electron_motion_preview/

Internal Test edition:

electron_motion_preview_internal_test/

Directory names are source locations, not executable commands.

⸻

4.7 Verification / 验证

Static verification:

cd electron_motion_preview_internal_test
npm run verify:static

Node regression tests:

node --test test\*.cjs

Python regression tests are under:

tests/

Static tests do not prove:

* rendered UI correctness
* WebGL runtime behavior
* installer behavior
* clean-machine compatibility
* provider connectivity
* OS-specific runtime behavior

These require runtime acceptance testing.

⸻

5. Architecture & Security / 架构与安全

5.1 Runtime Architecture / 运行架构

Electron Desktop
        ↓
Constrained Preload Bridge
        ↓
FastAPI / JARVIS Core
        ↓
Routing
Permission
Task / Tool Policy
        ↓
Bounded Python Tools
Platform Adapters
        ↓
Windows
Local Storage
Obsidian
Selected AI Provider

⸻

5.2 Documentation Authority / 文档权威关系

TARGET_ARCHITECTURE.md
→ target system design
CURRENT_STATE.md
→ current implementation truth
AGENTS.md
→ engineering rules
docs/INDEX.md
→ documentation index
README.md
→ public-facing overview

README must never claim capabilities not supported by the current implementation state.

⸻

5.3 Security Boundary / 安全边界

Local API

The Core API binds to:

127.0.0.1

Loopback reduces network exposure, but loopback alone is not treated as authorization.

Core security also depends on:

* Tool validation
* Argument validation
* Permission policy
* Confirmation requirements
* Renderer bridge restrictions
* Explicit failures
* Fail-closed behavior

⸻

Electron Boundary

Renderer access to privileged functionality goes through a constrained preload bridge.

The renderer does not receive unrestricted Node.js or operating-system authority.

⸻

Tool Boundary

Core validates:

Tool name
Arguments
Permission requirements
Execution state

Higher-risk operations require confirmation.

⸻

Packaging Boundary

Release packages must exclude:

.env
API keys
Authentication tokens
Personal Vaults
Private conversations
Machine-specific registries
Developer credentials

⸻

Failure Policy

JARVIS does not silently fall back between:

AI providers
Databases
Tools
Legacy implementations

Errors remain observable.

Security failures fail closed.

⸻

6. Roadmap / 路线图

Some foundations already exist.

The following phases describe the target completion state rather than implying that every listed capability is completely unimplemented.

部分基础能力目前已经存在。以下阶段表示目标完成状态。

⸻

6.1 Phase A — Core Foundation / 核心基础

Target completion includes:

* Explicit AI provider/model state
* Deterministic Core policy
* Permission enforcement
* Bounded Python tools
* Structured ToolResult
* SQLite personal and operational memory
* User Model
* Preferences
* Optional Obsidian knowledge
* Knowledge Manager
* RAG
* LLM Wiki
* AI usage tracking
* Configuration governance
* Migration
* Recovery
* Testing foundations
* Observability foundations

⸻

6.2 Phase B — Assistant Capabilities / 助手能力

Target capabilities:

* Persistent Tasks
* Automation Engine
* Scheduled tasks
* Recurring tasks
* Conditional tasks
* Missed-task handling
* Wake Word
* STT
* TTS
* Voice Interrupt
* Working Context
* Privacy-bounded Screen Awareness
* Bounded multi-step Agent Runtime

Agent Runtime is an escalation path, not the default routing path.

⸻

6.3 Phase C — Proactive Assistant / 主动助手

Target capabilities:

* Event Bus
* Event filtering
* Event subscriptions
* Proactive assistance
* Smart notifications
* Presence Awareness
* Error Monitor
* User-authorized Codex Handoff

⸻

6.4 Out of Current Scope / 当前范围之外

The following are not currently part of the authorized implementation roadmap:

* Camera Vision
* Multi-device support
* Mobile Companion
* IoT
* Smart-home control
* Physical-environment awareness

These require separate explicit authorization before entering implementation.

⸻

6.5 Codex Handoff / Codex 工程升级

Codex Handoff is separate from the current Codex App Server transport.

Codex App Server Transport
→ AI connection transport
→ Current infrastructure
Codex Handoff
→ Engineering task escalation
→ Future controlled capability

Future Codex Handoff may support authorized tasks such as:

Repository inspection
Code modification
Testing
Build operations
Engineering diagnostics

under explicit authorization and bounded authority.

⸻

7. Contributing & License / 贡献与许可证

7.1 Engineering Principles / 工程原则

JARVIS follows these principles:

1. One authority for every important concept.
2. No silent fallback.
3. No legacy compatibility by default.
4. Fail explicitly.
5. Preserve truthful state.
6. Security fails closed.
7. Use structured results.
8. Keep lifecycle transitions observable.
9. High cohesion, low coupling.
10. One-way dependencies.
11. Derived indexes are never authoritative.
12. Every repository change is documented and verified.

对应中文：

1. 每个重要概念只有一个权威来源。
2. 禁止静默兜底。
3. 默认不保留旧版兼容路径。
4. 失败必须明确显示。
5. 保持真实执行状态。
6. 安全检查失败时拒绝执行。
7. 使用结构化结果。
8. 生命周期变化必须可观察。
9. 高内聚、低耦合。
10. 保持单向依赖。
11. 派生索引不是权威来源。
12. 每次 Repository 改动必须记录并验证。

⸻

7.2 Contribution Workflow / 贡献流程

Before modifying the repository:

1. Read AGENTS.md
2. Read docs/INDEX.md
3. Read relevant CURRENT_STATE documentation
4. Read related change records
5. Confirm task scope
6. Create a dedicated branch
7. Modify the smallest responsible module
8. Update documentation
9. Run relevant tests
10. Inspect final Git diff
11. Open Pull Request

Recommended branch naming:

adapter/macos-system
adapter/macos-audio
adapter/linux-system
feature/wake-word
feature/automation-engine
fix/core-session-lock
fix/provider-state

Platform-specific implementations should remain inside the relevant platform adapter whenever possible.

Shared Core contracts should only be modified when the capability is genuinely cross-platform.

⸻

7.3 Platform Adapter Direction / 平台 Adapter 方向

Recommended structure:

JARVIS
├─ core/
│  ├─ routing/
│  ├─ permissions/
│  ├─ tasks/
│  └─ contracts/
│
├─ platform/
│  ├─ windows/
│  ├─ macos/
│  └─ linux/
│
├─ tools/
├─ storage/
├─ knowledge/
└─ desktop/

Example:

Core request:
system.volume.set(50)
Windows:
platform/windows/audio
macOS:
platform/macos/audio
Linux:
platform/linux/audio

The Core should depend on a capability contract, not on a specific operating-system implementation.

⸻

7.4 License / 许可证

JARVIS is licensed under the Apache License 2.0.

Third-party dependencies retain their own licenses, copyright notices, and attribution requirements.

JARVIS 使用 Apache License 2.0。

所有第三方组件继续遵守各自许可证、版权声明和 attribution 要求。

⸻

Development Status Notice / 开发状态说明

JARVIS is under active development.

Screenshots, hardware values, response times, UI surfaces and implementation details may change.

Displayed hardware metrics or response times represent individual development environments and must not be interpreted as formal performance benchmarks.

JARVIS 目前仍处于持续开发阶段。

截图、硬件数值、响应时间、UI 页面以及实现细节都可能继续变化。

开发阶段展示的数据仅代表对应运行环境，不应视为正式性能基准。