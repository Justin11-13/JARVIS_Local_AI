# JARVIS — Local-first Windows AI Assistant / 本地优先的 Windows AI 助手

JARVIS is an open-source Windows personal AI assistant. It keeps intelligence, control, execution, personal data, and structured knowledge under separate authorities.

JARVIS 是一个开源的 Windows 个人 AI 助手。它把智能、控制、执行、个人数据和结构化知识交给不同的权威模块负责。

```text
Luna / selected AI = Intelligence / 智能
JARVIS Core         = Policy and control / 策略与控制
Python Tools        = Bounded execution / 有界执行
Local storage       = Personal and operational data / 个人与运行数据
Obsidian            = Optional structured knowledge / 可选结构化知识
Codex               = Authorized engineering escalation / 授权后的工程升级路径
```

The current public-facing milestone is **JARVIS Internal Test**. It packages the Electron desktop, local Python Core, and Windows Codex App Server transport into one installer. Unfinished product pages are excluded.

当前面向测试者的里程碑是 **JARVIS 内测版**。它把 Electron 桌面端、本地 Python Core 和 Windows Codex App Server transport 封装进同一个安装器，并排除尚未完成的产品页面。

> **Internal test status / 内测状态：** The final rebuilt installer is published as the [`v0.1` GitHub pre-release](https://github.com/Justin11-13/JARVIS_Local_AI/releases/tag/v0.1). Installation under a separate clean Windows account is still pending. The installer is unsigned, so Windows may show a SmartScreen or application-control warning. / 最终重封安装包已发布到 [`v0.1` GitHub 内测 Release](https://github.com/Justin11-13/JARVIS_Local_AI/releases/tag/v0.1)，但尚未在独立的干净 Windows 账户完成安装验收。安装器目前未签名，因此 Windows 可能显示 SmartScreen 或应用控制警告。

[安装 Install](#install--安装内测版) · [功能 Features](#current-features--当前功能) · [AI 连接](#ai-connections--ai-连接) · [Obsidian](#obsidian-optional--可选-obsidian) · [未来范围](#future-scope--未来范围) · [安全](#security-boundary--安全边界)

这是开发阶段截图。硬件数值和响应时间仅为当次示例，不代表性能基准。

## Editions / 版本

| Edition / 版本 | Purpose / 用途 | Pages / 页面 |
| --- | --- | --- |
| **JARVIS Internal Test / 内测版** | Completed user-facing capabilities / 已完成、面向测试者的功能 | Assistant, History, Core, Tool Results, Device, AI Connections, Usage, Settings, Memory, Knowledge, Theme, Voice, Events, Errors |
| **JARVIS Development / 开发版** | Active development and future-feature validation / 开发中功能与未来能力验证 | 内测页面，加上 Tasks、Working Context、Automation、Codex Handoff 开发表面 |

Both editions share one architecture and one set of Core contracts. Internal Test hides unfinished navigation and also blocks direct access to those development routes.

两个版本共用同一架构和 Core contracts。内测版不仅隐藏未完成入口，也会阻止直接访问对应的开发路由。

## Current Features / 当前功能

### Assistant and Core / 助手与 Core

- Starts or reuses the local Core at `127.0.0.1:8765`. / 启动或复用本机 `127.0.0.1:8765` Core。
- Reports Core health separately from AI availability. / Core 健康状态与 AI 可用状态分开显示。
- Supports multi-turn chat and explicit reopening of saved local conversations. / 支持多轮聊天，并允许用户明确打开本地历史对话。
- Streams supported AI replies and renders a safe Markdown subset. / 支持 AI 流式回复，并安全渲染受限 Markdown。
- Preserves truthful states including `completed`, `failed`, `awaiting_confirmation`, `denied`, and `session_busy`. / 保留真实状态，不把失败、等待确认或拒绝包装成成功。

### Bounded Windows Tools / 有界 Windows 工具

- Reads system, battery, network, process, audio-device, project, Git, and file information through declared tools. / 通过已声明工具读取系统、电池、网络、进程、音频设备、项目、Git 和文件信息。
- Supports registered operations such as app launch, volume/media control, brightness, clipboard, wallpaper, window management, and selected keyboard/mouse actions. / 支持打开应用、音量和媒体控制、亮度、剪贴板、壁纸、窗口管理及部分键鼠操作。
- Requires explicit confirmation for higher-risk operations such as sleep, restart, and shutdown. / 睡眠、重启、关机等高风险操作必须取得明确确认。
- Keeps execution inside Core policy; AI receives neither unrestricted shell nor administrator authority. / 执行权留在 Core，AI 不获得无限制 Shell 或管理员权限。

### Desktop Experience / 桌面体验

- Animated WebGL JARVIS Core with Amber, Cyan, Violet, and Matrix themes. / WebGL 动态 Core，提供 Amber、Cyan、Violet 和 Matrix 主题。
- Theme supports eight locally persisted custom colors for background, surface, border, accent, text, muted text, Core A, and Core B, with reset to preset. / Theme 支持 8 项本地持久化自定义颜色：background、surface、border、accent、text、muted text、Core A、Core B，并可重置回预设。
- Low motion, background mode, and optional start-on-login. / 支持 Low motion、后台运行和可选开机启动。
- Live local system information when supported by the machine. / 在设备支持时显示真实本机状态。
- Separate Tool Results, Events, and Errors surfaces. / Tool Results、Events 和 Errors 分页显示。
- Windows OneCore voice selection, test playback, and optional automatic reading of new replies. / 可选择 Windows OneCore 语音、试听，并自动朗读新的回复。
- JARVIS-only token usage when the provider reports real usage. / Provider 提供真实 usage 时，仅显示 JARVIS 自己的 Token 使用量。
- Internal Test checks the trusted GitHub Release channel and shows an explicit update notice; downloading and installing remain user actions. / 内测版会检查受信任的 GitHub Release channel 并显示更新提示；下载和安装仍由用户明确执行。

### Local Data and Knowledge / 本地数据与知识

- Conversations and task records stay local; unfinished task runs are not silently resumed after restart. / 对话和任务记录保存在本地；重启后不会偷偷恢复未完成任务。
- Internal Test mutable data is stored under `%LOCALAPPDATA%\JARVIS\InternalTest`. / 内测版可写数据保存在 `%LOCALAPPDATA%\JARVIS\InternalTest`。
- Obsidian Vaults are optional. Disconnect removes JARVIS access without deleting notes. / Obsidian Vault 为可选连接；断开只取消 JARVIS 访问，不删除笔记。
- Personal runtime data and structured knowledge remain separate authorities. / 个人运行数据与结构化知识保持不同权威来源。

## Requirements / 系统要求

### Internal Test Users / 内测用户

- Windows 10 or Windows 11, x64.
- A GPU/driver that supports the Electron WebGL surface. / 支持 Electron WebGL 的显卡和驱动。
- Internet access when using a cloud AI provider. / 使用云端 AI 时需要网络。
- Either a ChatGPT account with Codex access, or a personal API key for OpenAI, Gemini, DeepSeek, or a supported OpenAI-compatible endpoint. / 需要具备 Codex 权限的 ChatGPT 账号，或者自备 OpenAI、Gemini、DeepSeek 或受支持 OpenAI-compatible endpoint 的 API Key。
- Obsidian is optional; the application does not need to be running to register an existing Vault folder. / Obsidian 非必需；注册已有 Vault 文件夹时，Obsidian 应用不必保持运行。

The installer includes the application runtime, Python Core, and Windows x64 Codex CLI transport. Testers do not need Python, Node.js, npm, Flutter, or a separate Codex CLI installation.

安装器已包含应用运行时、Python Core 和 Windows x64 Codex CLI transport。内测用户无需另外安装 Python、Node.js、npm、Flutter 或 Codex CLI。

### Source Development / 源码开发

- Windows 10/11 x64
- Git
- Python compatible with repository requirements / 与项目依赖兼容的 Python
- Node.js and npm
- PowerShell

Flutter is only required for the legacy desktop client, not the Electron Internal Test edition.

Flutter 仅用于旧版桌面客户端，不是 Electron 内测版的运行要求。

## Install / 安装内测版

Current local installer / 当前本地产物：

```text
electron_motion_preview_internal_test\release\JARVIS-Internal-Test-0.1.0-Setup.exe
```

Published asset / 已发布资产：[JARVIS-Internal-Test-0.1.0-Setup.exe](https://github.com/Justin11-13/JARVIS_Local_AI/releases/download/v0.1/JARVIS-Internal-Test-0.1.0-Setup.exe)

```text
Size / 大小: 816,647,011 bytes
SHA-256: 3501645D93FF9A73402998488A0BA4D90E470F919F8563CCA4501FD17E4EE8B3
```

1. Run the Setup executable. / 运行 Setup 安装器。
2. Choose an installation directory. / 选择安装目录。
3. Launch **JARVIS 内测版** from Desktop or Start. / 从桌面或开始菜单打开 **JARVIS 内测版**。
4. Open **Core** and confirm `ready`. / 打开 **Core**，确认状态为 `ready`。
5. Open **AI Connections** and configure one connection. / 打开 **AI Connections**，配置一种 AI 连接。

A selected model name is not connectivity proof. Send a real, non-fixed message before treating an AI path as verified.

选中模型名称不代表已经连通。必须成功发送一条非固定真实消息，才能把该 AI 路径视为已验证。

The unsigned installer has not completed separate clean-machine acceptance. It is an internal pre-release, not a stable production release.

当前未签名安装器尚未完成独立干净环境验收，因此属于内测产物，不是稳定发行版。

## AI Connections / AI 连接

JARVIS never bundles the developer's credentials. Every tester uses their own account or API key.

JARVIS 不会打包开发者的凭据。每位测试者必须使用自己的账号或 API Key。

### Managed ChatGPT Subscription / ChatGPT 订阅连接

1. Select **ChatGPT Subscription**. / 选择 **ChatGPT Subscription**。
2. Start the JARVIS-managed sign-in flow. / 启动由 JARVIS 管理的登录流程。
3. Complete official browser login with your own account. / 在官方浏览器页面登录自己的账号。
4. Return and check the reported account/model state. / 返回 JARVIS，检查账号和模型状态。
5. Send a normal question to verify a real response. / 发送普通问题，验证真实回复。

Disconnect stops JARVIS from using the managed transport. It must not silently sign the user out of unrelated Codex clients.

断开连接只停止 JARVIS 使用该 transport，不应偷偷让用户的其他 Codex 客户端退出登录。

### Direct API / API 直连

1. Select **Direct API**. / 选择 **Direct API**。
2. Choose OpenAI, Gemini, DeepSeek, or the supported OpenAI-compatible option. / 选择 OpenAI、Gemini、DeepSeek 或受支持的 OpenAI-compatible 选项。
3. Enter your own endpoint/model details where required and your API key. / 按需要填写 endpoint、model 和自己的 API Key。
4. Send a normal question to verify provider and model access. / 发送普通问题，验证 Provider 和 Model 权限。

API calls may incur charges. Invalid keys, unavailable models, exhausted quota, and network failures remain explicit. JARVIS does not silently switch provider.

API 请求可能产生费用。无效 Key、模型不可用、额度耗尽和网络失败都会明确显示；JARVIS 不会偷偷切换 Provider。

## Obsidian Optional / 可选 Obsidian

Obsidian is not required for chat, Core health, local tools, settings, or local conversations.

聊天、Core 健康检查、本地工具、设置和本地对话都不依赖 Obsidian。

Safe test / 安全测试步骤：

1. Create a temporary Vault with non-private Markdown notes. / 建立仅含非隐私 Markdown 的临时 Vault。
2. Open **Knowledge**. / 打开 **Knowledge**。
3. Enter a Vault name and full folder path. / 输入 Vault 名称和完整文件夹路径。
4. Connect, refresh, and verify the registered source. / 连接并刷新，确认来源已注册。
5. Disconnect and confirm the original files still exist. / 断开连接，确认原文件仍然存在。
6. Restart JARVIS and confirm the disconnected Vault is not accessed automatically. / 重启后确认已断开的 Vault 不会被自动访问。

Registration, indexing, and model retrieval are separate outcomes. A registered path is not proof that a note was indexed or used by AI.

注册、索引和模型检索是三个不同结果。路径注册成功不代表笔记已经建立索引或被 AI 使用。

## Build from Source / 从源码构建

```powershell
git clone https://github.com/Justin11-13/JARVIS_Local_AI.git
cd JARVIS_Local_AI
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd electron_motion_preview_internal_test
npm ci
npm run verify:static
npm run package:win
```

The pipeline builds a PyInstaller `onedir` Core, bundles the pinned Windows Codex CLI transport, and produces an x64 NSIS installer. Generated dependencies and build outputs are not source authority.

该流程会构建 PyInstaller `onedir` Core、打包固定版本的 Windows Codex CLI transport，并生成 x64 NSIS 安装器。生成的依赖和构建产物不是源码权威。

Use `electron_motion_preview --edition=development` for development and `electron_motion_preview_internal_test --edition=internal-test` for Internal Test behavior.

开发版使用 `electron_motion_preview --edition=development`；内测行为使用 `electron_motion_preview_internal_test --edition=internal-test`。

## Verification / 验证

```powershell
cd electron_motion_preview_internal_test
npm run verify:static
node --test test\*.cjs
```

Python regression tests are under `tests/`. Static tests do not prove rendered UI or installer behavior; those require real runtime acceptance.

Python 回归测试位于 `tests/`。静态测试不能证明真实 UI 和安装器行为，仍需实际运行验收。

## Known Limitations / 已知限制

- Clean-machine installer acceptance is pending. / 干净电脑安装验收尚未完成。
- The installer is not code-signed. / 安装器尚未进行代码签名。
- Operational memory and task storage have not completed the target SQLite migration. / 个人运行记忆与任务存储尚未完成目标 SQLite 迁移。
- Wake word, microphone STT, Voice Interrupt, full automation, proactive behavior, Screen Awareness, and Codex Handoff are not finished Internal Test capabilities. / 唤醒词、语音输入、语音打断、完整自动化、主动助手、屏幕感知和 Codex Handoff 尚未成为内测完成能力。
- Obsidian registration exists, but full Knowledge Manager governance and end-to-end RAG acceptance remain future work. / 已有 Obsidian 注册，但完整 Knowledge Manager 治理和端到端 RAG 验收仍属未来工作。
- Hardware metrics depend on the machine; unsupported values must show unavailable. / 硬件数据取决于设备，不支持的项目必须显示 unavailable。
- AI availability depends on account access, model availability, quota, provider, and network. / AI 可用性取决于账号权限、模型、额度、Provider 和网络。

## Architecture / 架构

```text
Electron desktop / 桌面端
      ↓
FastAPI / JARVIS Core
      ↓
Routing · Permission · Task/Tool policy
      ↓
Python tools and bounded adapters
      ↓
Windows · local storage · Obsidian · selected AI provider
```

- Authoritative target / 权威目标：[TARGET_ARCHITECTURE.md](docs/architecture/TARGET_ARCHITECTURE.md)
- Current implementation / 当前实现：[CURRENT_STATE.md](docs/info/01-project-overview/CURRENT_STATE.md)
- Engineering rules / 工程规则：[AGENTS.md](AGENTS.md)

## Security Boundary / 安全边界

- API binds to loopback only. / API 只监听本机 loopback。
- Renderer uses a constrained Electron preload bridge. / Renderer 通过受限 Electron preload bridge 访问能力。
- Core validates tool names and arguments. / Core 校验工具名称和参数。
- High-risk actions require confirmation. / 高风险操作需要确认。
- Package excludes developer `.env`, keys, tokens, personal Vault, conversations, and machine-specific registries. / 安装包不包含开发者 `.env`、Key、Token、私人 Vault、对话或机器专属 registry。
- Errors remain observable; no silent provider, database, tool, or legacy fallback. / 错误保持可见，不允许静默 Provider、数据库、工具或旧版兜底。

Use non-sensitive data during testing. This is not a security-certified production release.

测试时请使用非敏感数据。本项目目前不是经过安全认证的生产发行版。

## Future Scope / 未来范围

The target product covers **Phase A-C only**. These are planned directions, not claims of current implementation.

目标产品当前只涵盖 **Phase A-C**。以下是规划方向，不代表已经实现。

### Phase A — Core Foundation / 核心基础

- Luna intelligence with explicit provider and connection state. / Luna 智能与明确的 Provider、连接状态。
- Deterministic Core control and permission enforcement. / 确定性的 Core 控制与权限执行。
- Bounded Python tools and structured `ToolResult`. / 有界 Python 工具和结构化 `ToolResult`。
- SQLite personal/operational memory, User Model, and Preferences. / SQLite 个人与运行记忆、User Model 和 Preferences。
- Optional Obsidian knowledge, Knowledge Manager, RAG, and LLM Wiki. / 可选 Obsidian 知识、Knowledge Manager、RAG 和 LLM Wiki。
- AI usage, configuration, migration, recovery, testing, and observability foundations. / AI usage、配置、迁移、恢复、测试和可观察性基础。

### Phase B — Assistant Capabilities / 助手能力

- Persistent Tasks and Automation Engine. / 持久化 Tasks 与 Automation Engine。
- Scheduled, recurring, conditional, and missed tasks. / 定时、重复、条件和错过任务处理。
- Wake Word, STT, TTS, and Voice Interrupt. / 唤醒词、STT、TTS 和语音打断。
- Working Context and privacy-bounded Screen Awareness. / Working Context 和具备隐私边界的 Screen Awareness。
- Bounded multi-step Agent Runtime as an escalation path, not default routing. / 有界多步骤 Agent Runtime，只作为升级路径而非默认路由。

### Phase C — Proactive Assistant / 主动助手

- Event Bus and event filtering. / Event Bus 与事件过滤。
- Proactive assistance and smart notifications. / 主动协助和智能通知。
- Presence Awareness and Error Monitor. / Presence Awareness 与 Error Monitor。
- User-authorized Codex Handoff. / 必须经用户授权的 Codex Handoff。

### Phase D — Not Authorized / 未授权

Camera Vision, multi-device support, mobile companion, IoT, smart-home control, and physical-environment awareness are future expansion only. They must not be implemented without explicit user authorization.

Camera Vision、多设备、手机 Companion、IoT、智能家居和物理环境感知只属于未来扩展。没有用户明确授权时不得实现。

## Project Principles / 项目原则

1. One authority for every important concept. / 每个重要概念只有一个权威来源。
2. No silent fallback. / 禁止静默兜底。
3. No legacy compatibility by default. / 默认不保留旧版兼容路径。
4. Fail explicitly and preserve truthful state. / 明确失败并保持真实状态。
5. Security fails closed. / 安全验证失败时拒绝执行。
6. Structured results and observable lifecycle transitions. / 使用结构化结果和可观察状态变化。
7. High cohesion, low coupling, and one-way dependencies. / 高内聚、低耦合、单向依赖。
8. Derived indexes are never authoritative. / 派生索引永远不是权威来源。
9. Every repository change is documented and verified. / 每次 Repository 改动都要记录和验证。

## Contributing / 参与开发

Read [AGENTS.md](AGENTS.md), then [docs/INDEX.md](docs/INDEX.md), relevant current-state documentation, and related change records before editing code.

修改源码前，请依次阅读 [AGENTS.md](AGENTS.md)、[docs/INDEX.md](docs/INDEX.md)、相关当前状态文档和历史改动记录。保持任务范围清晰、记录所有变更、运行相关测试并检查最终 Git diff。

## License / 许可证

JARVIS is licensed under the [Apache License 2.0](LICENSE). Third-party components retain their own licenses and notices.

JARVIS 使用 [Apache License 2.0](LICENSE)。第三方组件继续遵守各自许可证和 notice。
