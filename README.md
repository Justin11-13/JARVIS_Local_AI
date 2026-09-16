JARVIS — Local-first Windows AI Assistant

JARVIS — 本地优先的 Windows AI 助手

JARVIS is an open-source, local-first Windows personal AI assistant.

Its architecture separates intelligence, policy, execution, personal data, structured knowledge, and engineering escalation into independent authorities instead of allowing one AI model to control the entire system.

JARVIS 是一个开源、本地优先的 Windows 个人 AI 助手。

其架构将 智能、策略控制、执行、个人数据、结构化知识和工程升级路径 分离为不同的权威模块，而不是让单一 AI 模型直接控制整个系统。

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

JARVIS follows a simple rule: AI can propose actions, but Core decides what is allowed to execute.

JARVIS 遵循一个核心原则：AI 可以提出操作，但最终是否允许执行由 Core 决定。

⸻

Current Milestone / 当前里程碑

The current public-facing milestone is:

JARVIS Internal Test v0.1.0

The Internal Test edition packages:

* Electron desktop application
* Local Python / FastAPI JARVIS Core
* Windows tool adapters
* Bundled Windows x64 Codex CLI
* Codex App Server transport
* Local configuration and runtime storage

into a single Windows installer.

当前公开测试里程碑为：

JARVIS Internal Test v0.1.0

内测版将以下组件封装进一个 Windows 安装器：

* Electron 桌面端
* 本地 Python / FastAPI JARVIS Core
* Windows 工具适配层
* 内置 Windows x64 Codex CLI
* Codex App Server transport
* 本地配置与运行数据存储

Unfinished product surfaces are excluded from the Internal Test edition.

尚未完成的产品页面不会进入 Internal Test 版本。

⸻

Internal Test Status / 内测状态

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

目前仍未完成独立干净 Windows 环境的安装验收。

安装器尚未进行代码签名，因此 Windows 可能显示 SmartScreen 或应用控制警告。

This is an internal pre-release, not a stable production release.

当前版本属于内测预发布版本，不是稳定生产版本。

⸻

Editions / 版本

Edition / 版本	Purpose / 用途	Available Pages / 页面
JARVIS Internal Test	Completed tester-facing capabilities / 已完成、可供测试者使用的功能	Assistant, History, Core, Tool Results, Device, AI Connections, Usage, Settings, Memory, Knowledge, Theme, Voice, Events, Errors
JARVIS Development	Active development and future-feature validation / 开发中功能与未来能力验证	Internal Test pages + Tasks, Working Context, Automation, Codex Handoff development surfaces

Both editions share the same architecture and Core contracts.

Internal Test does not only hide unfinished navigation. Direct access to unfinished development routes is also blocked.

两个版本共享相同的架构与 Core contracts。

Internal Test 不只是隐藏尚未完成的导航入口，同时也会阻止直接访问对应的开发路由。

⸻

Current Features / 当前功能

Assistant and Core / 助手与 Core

* Starts or reuses the local Core at 127.0.0.1:8765.
* Reports Core health separately from AI availability.
* Supports multi-turn conversations.
* Allows explicit reopening of saved local conversations.
* Streams AI responses when supported by the selected provider.
* Renders a constrained and safe Markdown subset.
* Preserves truthful execution states.

Supported states include:

completed
failed
awaiting_confirmation
denied
session_busy

JARVIS does not convert failures, denials, or confirmation requirements into fake success states.

JARVIS 不会把失败、拒绝或等待确认状态包装成成功。

⸻

Bounded Windows Tools / 有界 Windows 工具

JARVIS exposes Windows capabilities through explicitly registered tools instead of unrestricted shell access.

Current tool categories include:

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
* Selected keyboard and mouse actions

Higher-risk operations such as:

Sleep
Restart
Shutdown

require explicit user confirmation.

The AI model does not receive unrestricted Shell or administrator authority.

Execution remains inside JARVIS Core policy.

JARVIS 通过明确注册的工具暴露 Windows 能力，而不是直接给予 AI 无限 Shell 权限。

所有实际执行仍受 Core 的权限与策略控制。

⸻

Desktop Experience / 桌面体验

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
* Live hardware/system information when available
* Tool Results surface
* Events surface
* Errors surface
* Windows OneCore voice support
* Optional automatic reading of new replies
* JARVIS-only token usage when providers report real usage
* GitHub Release update checking

Custom theme values are persisted locally for:

background
surface
border
accent
text
muted text
Core A
Core B

Users can reset customized colors back to a preset theme.

Update checking only reports available trusted releases.

Downloading and installing updates remain explicit user actions.

⸻

AI Connections / AI 连接

JARVIS never bundles developer credentials.

Every tester must use their own account or API key.

JARVIS 不会把开发者自己的账号凭据或 API Key 打包进安装器。

每位测试者必须使用自己的账号或 Key。

⸻

Managed ChatGPT Connection / ChatGPT 管理连接

The current ChatGPT connection uses:

JARVIS
    ↓
Codex App Server transport
    ↓
Bundled Windows x64 Codex CLI
    ↓
Official user authentication

The Codex CLI is the bundled runtime component.

Codex App Server is the transport/protocol used by JARVIS to communicate with that component.

They are not separate AI providers.

Connection Flow / 连接流程

1. Select ChatGPT Subscription.
2. Start the JARVIS-managed sign-in flow.
3. Complete official browser authentication using your own account.
4. Return to JARVIS.
5. Check the reported account/model state.
6. Send a normal, non-fixed message.
7. Confirm that a real response is returned.

A selected model name is not proof of connectivity.

实际选择了模型名称，并不代表连接已经成功。

必须发送一条真实的普通消息并成功获得回复，才能认为 AI 路径已经通过验证。

Disconnecting JARVIS only stops JARVIS from using its managed transport.

It must not silently sign the user out of unrelated Codex clients.

⸻

Direct API / API 直连

Supported connection categories currently include:

* OpenAI
* Gemini
* DeepSeek
* Supported OpenAI-compatible endpoints

Connection Flow / 连接流程

1. Select Direct API.
2. Select the provider.
3. Enter required endpoint and model information.
4. Enter your own API key.
5. Send a normal question.
6. Verify the real provider response.

Possible failures remain explicit:

Invalid API key
Unavailable model
Quota exhausted
Provider error
Network failure
Invalid endpoint

JARVIS does not silently switch providers.

API requests may incur provider charges.

⸻

Local Data / 本地数据

Internal Test writable application data is stored under:

%LOCALAPPDATA%\JARVIS\InternalTest

Local data can include:

* Conversations
* Settings
* Runtime state
* Usage records
* Tool results
* Events
* Error records
* Existing memory records
* Runtime/task records generated by Core

Unfinished task runs are not silently resumed after restart.

⸻

Memory Status / Memory 当前状态

The Internal Test edition already exposes a Memory surface and existing local memory/runtime records.

However, the target operational-memory architecture is not yet complete.

Current:

Memory UI
Existing local records
Runtime memory behavior

Target:

SQLite MemoryStore
User Model
Preferences
Memory Review
Context Builder integration
Migration and recovery rules

This distinction prevents the existence of a Memory page from being interpreted as completion of the full target Memory architecture.

⸻

Obsidian / 可选结构化知识

Obsidian is optional.

It is not required for:

* Chat
* Core health
* Local tools
* Settings
* Local conversations

JARVIS treats personal runtime data and structured knowledge as separate authorities.

Local Storage
    ↓
Personal / operational data
Obsidian Vault
    ↓
Structured knowledge

Disconnecting a Vault removes JARVIS access but does not delete the original notes.

⸻

Safe Obsidian Test / 安全测试

For testing:

1. Create a temporary Vault.
2. Use non-private Markdown notes.
3. Open Knowledge.
4. Enter a Vault name.
5. Enter the full Vault folder path.
6. Connect the Vault.
7. Refresh.
8. Verify the registered source.
9. Disconnect.
10. Confirm that the original files still exist.
11. Restart JARVIS.
12. Confirm that the disconnected Vault is not accessed automatically.

Important:

Registered
≠ Indexed
≠ Retrieved
≠ Used by AI

Vault registration, indexing, retrieval, and AI usage are separate outcomes.

路径注册成功并不代表：

* 已完成索引
* 已被检索
* 已经进入 AI Context
* 已被 AI 实际使用

⸻

Events Status / Events 当前状态

The current Internal Test edition contains an Events surface for recorded runtime events.

This does not mean that the full target Event Bus architecture is complete.

Current:

Runtime event records
Events UI
Basic observability

Future:

Event Bus
Publish / Subscribe
Event filtering
Event routing
Proactive triggers
Presence events
Automation integration

⸻

Requirements / 系统要求

Internal Test Users / 内测用户

Required:

* Windows 10 or Windows 11
* x64 architecture
* GPU/driver capable of running the Electron WebGL surface

Internet is required when using cloud AI providers.

AI access requires either:

* a ChatGPT account with supported Codex access, or
* a personal API key for a supported provider

Obsidian is optional.

The Obsidian application does not need to remain open when registering an existing Vault directory.

⸻

Bundled Runtime / 已包含运行环境

Internal Test includes:

* Application runtime
* Python Core
* Windows x64 Codex CLI transport runtime

Testers do not need to separately install:

Python
Node.js
npm
Flutter
Codex CLI

⸻

Source Development / 源码开发

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

Install / 安装

Current installer artifact:

electron_motion_preview_internal_test\
└─ release\
   └─ JARVIS-Internal-Test-0.1.0-Setup.exe

Installation

1. Run JARVIS-Internal-Test-0.1.0-Setup.exe.
2. Choose an installation directory.
3. Complete installation.
4. Launch JARVIS Internal Test from Desktop or Start.
5. Open Core.
6. Confirm Core reports ready.
7. Open AI Connections.
8. Configure one AI connection.
9. Send a normal message.
10. Confirm a real provider response.

The unsigned installer may trigger Windows SmartScreen or application-control warnings.

⸻

Build from Source / 从源码构建

git clone https://github.com/Justin11-13/JARVIS_Local_AI.git
cd JARVIS_Local_AI
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd electron_motion_preview_internal_test
npm ci
npm run verify:static
npm run package:win

The build pipeline produces:

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

Edition Source Directories / 版本源码目录

Development edition:

electron_motion_preview/

Internal Test edition:

electron_motion_preview_internal_test/

Edition-specific runtime behavior must use the repository’s defined startup scripts and edition configuration.

Directory names themselves are not executable commands.

⸻

Verification / 验证

Internal Test static verification:

cd electron_motion_preview_internal_test
npm run verify:static

Node regression tests:

node --test test\*.cjs

Python regression tests are located under:

tests/

Static tests verify source-level expectations.

They do not prove:

* rendered UI correctness
* WebGL runtime behavior
* installer behavior
* clean-machine compatibility
* provider connectivity
* OS-specific behavior

Those require real runtime acceptance testing.

⸻

Architecture / 架构

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

Authoritative architecture documents:

TARGET_ARCHITECTURE.md
CURRENT_STATE.md
AGENTS.md
docs/INDEX.md

Authority Model

TARGET_ARCHITECTURE.md
→ target system design
CURRENT_STATE.md
→ current implementation truth
AGENTS.md
→ engineering rules
README.md
→ public-facing overview

README must never claim a capability that is not supported by the current implementation state.

⸻

Security Boundary / 安全边界

JARVIS currently applies multiple security boundaries.

Local API

The Core API binds to loopback only.

127.0.0.1

Loopback reduces network exposure, but loopback alone is not treated as complete authorization.

Core security must also rely on:

* tool validation
* argument validation
* permission policy
* confirmation requirements
* renderer bridge restrictions
* explicit failure
* fail-closed behavior

⸻

Electron Boundary

The renderer accesses privileged functionality through a constrained preload bridge.

The renderer does not receive unrestricted Node.js or system authority.

⸻

Tool Boundary

Core validates:

* tool names
* tool arguments
* permission requirements
* execution state

Higher-risk actions require explicit user confirmation.

⸻

Packaging Boundary

Release packages must exclude developer-specific or private data, including:

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

* AI providers
* databases
* tools
* legacy implementations

Errors remain observable.

Security failures fail closed.

⸻

Known Limitations / 已知限制

Current known limitations include:

* Clean Windows machine installer acceptance is pending.
* Installer is not code-signed.
* Target SQLite operational-memory migration is incomplete.
* Target persistent task architecture is incomplete.
* Wake Word is not a completed Internal Test capability.
* Microphone STT is not a completed Internal Test capability.
* Voice Interrupt is not a completed Internal Test capability.
* Full Automation Engine is not complete.
* Proactive assistance is not complete.
* Full Screen Awareness is not complete.
* Codex Handoff is not complete.
* Full Knowledge Manager governance is not complete.
* End-to-end RAG acceptance remains future work.
* Hardware metrics depend on device support.
* Unsupported hardware values must report unavailable.
* AI availability depends on provider, account access, model availability, quota, and network.

⸻

Target Architecture Roadmap / 目标架构路线

Some foundations already exist.

The following phases describe the target completion state, not a claim that every listed capability is completely unimplemented.

部分基础能力目前已经存在。

以下阶段描述的是 目标完成状态，并不代表其中所有内容均尚未实现。

⸻

Phase A — Core Foundation / 核心基础

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

Phase B — Assistant Capabilities / 助手能力

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

The Agent Runtime is an escalation path, not the default path for every request.

⸻

Phase C — Proactive Assistant / 主动助手

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

Out of Current Scope / 当前范围之外

The following capabilities are not currently authorized roadmap work:

* Camera Vision
* Multi-device support
* Mobile Companion
* IoT
* Smart-home control
* Physical-environment awareness

These capabilities require separate explicit authorization before entering the implementation roadmap.

以下功能目前不属于已授权开发范围：

* Camera Vision
* 多设备支持
* 手机 Companion
* IoT
* 智能家居控制
* 物理环境感知

在进入正式实现路线之前，必须重新取得明确授权。

⸻

Codex Handoff / Codex 工程升级

Codex Handoff is different from the Codex App Server transport currently used for managed ChatGPT connectivity.

Codex App Server Transport
→ AI connection transport
→ Current infrastructure
Codex Handoff
→ Engineering task escalation
→ Future controlled capability

A future Codex Handoff may allow JARVIS to escalate authorized engineering tasks such as:

Repository inspection
Code modification
Testing
Build operations
Engineering diagnostics

but only after explicit authorization and under bounded authority.

⸻

Project Principles / 项目原则

JARVIS follows these engineering principles:

1. One authority for every important concept.
    每个重要概念只有一个权威来源。
2. No silent fallback.
    禁止静默兜底。
3. No legacy compatibility by default.
    默认不保留旧版兼容路径。
4. Fail explicitly.
    失败必须明确显示。
5. Preserve truthful state.
    保持真实执行状态。
6. Security fails closed.
    安全检查失败时拒绝执行。
7. Use structured results.
    使用结构化结果。
8. Keep lifecycle transitions observable.
    生命周期状态变化必须可观察。
9. High cohesion, low coupling.
    高内聚、低耦合。
10. One-way dependencies.
    保持单向依赖。
11. Derived indexes are not authoritative.
    派生索引不是权威数据源。
12. Every repository change is documented and verified.
    每次 Repository 改动都必须记录并验证。

⸻

Contributing / 参与开发

Before modifying the repository:

1. Read AGENTS.md
2. Read docs/INDEX.md
3. Read relevant CURRENT_STATE documentation
4. Read related change records
5. Confirm the task scope
6. Modify the smallest responsible module
7. Update documentation
8. Run relevant tests
9. Inspect the final Git diff

Contributors should preserve:

* authority boundaries
* Core contracts
* explicit failure states
* security policy
* platform isolation
* documentation consistency

Platform-specific functionality should not leak into Core contracts unless the capability is genuinely cross-platform.

For platform adapters, contributors should normally work in dedicated branches such as:

adapter/macos-system
adapter/macos-audio
adapter/linux-system
feature/wake-word
fix/core-session-lock

Platform-specific implementations should remain isolated from shared Core logic whenever possible.

⸻

License / 许可证

JARVIS is licensed under the Apache License 2.0.

Third-party dependencies retain their own licenses, copyright notices, and attribution requirements.

JARVIS 使用 Apache License 2.0。

所有第三方组件继续遵守各自的许可证、版权声明与 attribution 要求。

⸻

Development Status Notice / 开发状态说明

JARVIS is under active development.

Current screenshots, hardware values, response times, UI surfaces, and implementation details may change.

Any displayed hardware metrics or response times are examples from a specific development environment and must not be interpreted as performance benchmarks.

JARVIS 目前仍处于持续开发阶段。

截图、硬件数值、响应时间、UI 页面以及部分实现细节都可能继续变化。

开发阶段展示的硬件数据与响应时间仅代表当次运行环境，不应视为正式性能基准。