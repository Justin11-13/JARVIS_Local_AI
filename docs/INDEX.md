# JARVIS Documentation Index / 项目文档地图

Engineering rules: [AGENTS](../AGENTS.md), project-local only. 不修改全局 Codex personalization。
文档范围：这里是当前实现与变更记录地图；M3a Electron 前台接入条目标明 source/contract 与 runtime
验证的边界，不把阻断的窗口验收写成 VERIFIED。

## Current Implementation / 当前实现

- [Current State](info/01-project-overview/CURRENT_STATE.md)：基线与已存在/未存在能力。
- [Electron + JARVIS Core Windows Packaging](info/05-integrations/ELECTRON_CORE_PACKAGING.md)：Internal Test 完整 Core + Electron 资源边界、AppData 数据边界、NSIS 可选安装目录与实际验证证据。
- [Electron Internal Test Update Notice](prompts/feature/20260914-FEAT-electron-update-notice.md)：固定 GitHub Releases channel、版本/asset 校验、启动与手动检查、显式下载页面和失败状态边界。
- [Software-Level PC Control](info/05-integrations/SOFTWARE_PC_CONTROL.md)：Audio/Brightness/Wallpaper/Windows OS Theme/System Status 到 Keyboard/Mouse 的全部 written software-control phases、canonical registry/schema/permission/native-intent boundary、显式 unsupported limits 和 Windows runtime acceptance 边界。
- [Software-Level PC Control Audio](prompts/feature/20260913-FEAT-software-pc-control-audio.md)：Audio domain 的分阶段 PC control 实施记录。
- [Software-Level PC Control Brightness](prompts/feature/20260913-FEAT-software-pc-control-brightness.md)：Brightness domain 的完整实施、验证和 Windows runtime 限制记录。
- [Software-Level PC Control Wallpaper](prompts/feature/20260913-FEAT-software-pc-control-wallpaper.md)：Wallpaper domain 的完整实施、验证和 Windows runtime 限制记录。
- [Software-Level PC Control Theme](prompts/feature/20260913-FEAT-software-pc-control-theme.md)：Windows OS light/dark Theme domain 的完整实施、验证和 runtime 限制记录。
- [Software-Level PC Control System Status](prompts/feature/20260913-FEAT-software-pc-control-system-status.md)：System Status structured `psutil` tools、Windows Battery Class capacity/cycle detail、Battery owner migration、Electron Device bridge、验证和 runtime 限制记录。
- [Software-Level PC Control Remaining Domains](prompts/feature/20260913-FEAT-software-pc-control-remaining-domains.md)：App Control 至 Keyboard/Mouse 的一次性实现、canonical action migration、结构化失败边界、测试与发现的 bug/限制。
- [Canonical Tool Definition Catalog](prompts/refactor/20260913-REFACTOR-canonical-tool-definition-catalog.md)：统一 provider-neutral tool metadata，并由同一来源派生 Gemini declarations、API schemas 与 managed-GPT intent catalog。
- [Local Storage and History Chat](info/04-storage/STORAGE_OVERVIEW.md)：terminal conversations/tasks、renderer evidence 的本地持久化边界，以及 History list/open/new-chat contract；pending confirmation 不落盘。
- [Local Chat Persistence and History Chat](prompts/feature/20260913-FEAT-local-chat-persistence-and-history.md)：本次 per-conversation transcript、TaskManager persistence、Electron History page 与 no-daily-rotation 实施记录。
- [Chat Launch and Background Lifecycle](prompts/feature/20260913-FEAT-chat-launch-and-background-lifecycle.md)：Electron 开发版/内测版每次启动新 chat、History 显式恢复，以及默认关闭的后台运行/开机自启设置与 History 错误 UI。
- [Low-Latency Streaming Text and Synchronized TTS](prompts/feature/20260913-FEAT-low-latency-streaming-text-synchronized-tts.md)：Core NDJSON delta stream、Electron 两版渐进渲染、分块 Windows OneCore TTS、取消、指标和验证边界。
- [Electron Speech Short-Reply Duplication and Windows Default Settings](prompts/bugfix/20260914-FIX-electron-speech-short-reply-and-settings.md)：修复短回复在 terminal narration 合并时重复朗读，并让缺少可选 Windows Speech registry settings 的用户显示 Windows default 而不是 unavailable。
- [Automatic Language-Matched Speech Voices](prompts/feature/20260913-FEAT-auto-language-speech-voice.md)：按回复文字本地识别中文、自动选择已安装 `zh-CN` voice、固定单条回复的语音包，并记录无中文 voice 时的显式行为。
- [Response Latency Optimization](prompts/bugfix/20260913-FIX-response-latency-optimization.md)：JARVIS managed child 的显式 low reasoning effort、resident thread context 复用、阶段 timing 与验证边界。
- [Electron Token Usage Card](prompts/feature/20260913-FEAT-electron-token-usage-card.md)：Usage 作为 Feature page 展示完整 stats/heatmap/trend，并在 Core stage 上方保留 compact realtime preview；这是后续 JARVIS-only widget summary 的基础记录，始终只显示明确 provider-reported counts，不新增 account/quota telemetry。
- [Codex Account Usage Integration](prompts/feature/20260913-FEAT-codex-account-usage.md)：Managed ChatGPT 通过 `account/usage/read` 提供持久化 account summary/daily buckets；Direct API 保留 response-level provider usage，Managed Luna turn delta 与 Direct usage 共同进入 JARVIS widget，但 account 来源仍在 Feature 页面明确分开。
- [JARVIS-only Token Usage Widget Summary](prompts/feature/20260914-FEAT-jarvis-only-token-widget-summary.md)：Core-stage widget 只显示 JARVIS provider-reported Input/Output/Total；Managed 通过 App Server `thread/tokenUsage/updated` 的当前 turn delta 接入，不包含用户在 Codex 客户端的 account usage，也不显示 chart；完整 Feature usage chart 保留。
- [Token Usage Widget Axes and Point Details](prompts/feature/20260914-FEAT-token-widget-chart-axes-tooltip.md)：完整 Feature trend chart 增加 X/Y 轴刻度、14-day 日期 ticks、k/M token scale 与 hover/focus point detail；compact widget 的 chart 已由上面的 JARVIS-only summary 取代。
- [Electron Token Usage Widget Placement](prompts/bugfix/20260913-FIX-electron-token-usage-widget-placement.md)：将 preview 放入 Core 上方独立小 widget slot，预留 canvas 安全区并移除 preview 内部 scrollbar；完整 Usage inspector 保持独立。
- [Electron Core Connection Page](prompts/feature/20260913-FEAT-electron-core-connection-page.md)：Pages → Core 的运行时 health Refresh 与 bounded supervisor Reconnect；失败保持显式，不新增 Core/AI fallback。
- [Electron Core Foreground Integration](prompts/feature/20260909-FEAT-electron-core-foreground-integration.md)：M3a 测试入口接入固定 loopback Core bridge；静态/协议测试通过，当前 host 的 GPU loader 仍阻断真实窗口验收。
- [Electron Settings and Automatic Speech Replies](prompts/feature/20260909-FEAT-electron-settings-auto-speech.md)：Pages Settings 入口、英文/中文日期选择和默认关闭的自动朗读回复；复用固定 Windows system speech bridge，不提供逐条手动朗读按钮。
- [Electron Speech Sync and Theme Presets](prompts/feature/20260909-FEAT-electron-speech-sync-and-theme-presets.md)：同一响应任务内立即启动受限 speech bridge，并在 Settings 提供 Amber/Cyan/Violet/Matrix 主题预设；不改变 Windows TTS 所有权或增加 fallback。
- [Electron Custom Theme Palette](prompts/feature/20260914-FEAT-electron-custom-theme-palette.md)：两套 Electron edition 的 Theme page 提供 background/surface/border/accent/text/muted/Core A/Core B 八项本地调色盘，立即应用、持久化并可 Reset；保留既有四个 preset。
- [Electron Pages Memory & Knowledge Merge and Theme Page](prompts/feature/20260909-FEAT-electron-pages-memory-knowledge-theme.md)：历史记录，曾将 Memory 与 Knowledge 合并并加入 Theme page；合并部分已被后续页面拆分 supersede。
- [Electron Separate Memory and Knowledge Pages](prompts/feature/20260913-FEAT-separate-memory-knowledge-pages.md)：开发版与内测版都将 Memory、Knowledge 分成独立 inspector，并保留独立只读刷新边界。
- [Electron Separate Events and Errors Pages](prompts/feature/20260913-FEAT-separate-events-errors-pages.md)：开发版与内测版都将本窗口的 Events、Errors 分成独立 inspector，按既有 event level 展示并独立清理。
- [Hide Voice from Internal Test Edition](prompts/configuration/20260913-CONFIG-hide-voice-internal-test.md) (historical record; superseded by the current Voice Feature record below).
- [Electron Windows Voice Packages and Low Motion](prompts/feature/20260913-FEAT-electron-windows-voice-packages-and-low-motion.md): Both editions expose the runtime Windows OneCore voice inventory, selection, refresh, and test controls; Settings Low motion slows Core rotation without stopping it, and the Pages launcher uses the English `Feature` label with a separated responsive Voice action row.
- [Electron Obsidian Connect and Reconnect](prompts/feature/20260913-FEAT-electron-obsidian-connect-reconnect.md)：Knowledge 页提供运行时注册检查、Connect/reconnect 与 Disconnect；断开只移除 JARVIS 注册，不删除 Vault 文件。
- [Electron Pages Launcher Labels and Spacing](prompts/feature/20260913-FEAT-electron-pages-launcher-labels.md)：Pages 浮动面板显示每个可见入口的短名称，并增加纵向间距；不改变页面路由或 edition allowlist。
- [Electron Pages Launcher Width and Single-Line Labels](prompts/bugfix/20260913-FIX-electron-pages-label-wrap.md)：扩大 Pages card 的响应式宽度并保持标签单行，避免 Settings/Knowledge 被拆成两行。
- [Electron Pages Card Spacing and Rounded Surfaces](prompts/bugfix/20260913-FIX-electron-pages-card-spacing.md)：统一 Pages 页面内部间距，并为 launcher、inspector 与内容卡片增加矩形比例和圆角。
- [Electron Card Border Rendering Polish](prompts/feature/20260913-FEAT-electron-card-border-rendering.md)：统一 rounded surface 的绘制边界，并移除 Pages 外框切换时的 blur/scale 二次采样，让 Windows DPI 下的 card border 更清晰。
- [Electron Feature Top Anchor and Motion/Grid Cleanup](prompts/bugfix/20260913-FIX-electron-feature-top-anchor-and-hide-motion-controls.md)：让 Feature 与 Chat 共用顶部锚点，隐藏左下角 Motion control strip，并移除 Core stage 背景网格；保留 Core 动画与 Low motion 状态逻辑。
- [Electron Side Card Vertical Stretch](prompts/bugfix/20260913-FIX-electron-side-card-vertical-stretch.md)：让桌面 Chat/monitor stack 与右侧 inspector 使用 viewport 可用高度向下伸展，并保留顶部保护与底部安全间距。
- [Electron Monitor Content Height and Flexible Feature Page](prompts/bugfix/20260913-FIX-electron-monitor-content-height-and-flexible-feature-page.md)：移除 System Monitor 的固定空白高度，让 Feature inspector 按内容自适应并以 viewport max-height 与底部安全间距约束。
- [Electron Feature Page Switch Animation](prompts/feature/20260913-FEAT-electron-feature-page-switch-animation.md)：Feature 切换时让 inspector header 与页面内容以可中断的淡入/横向到位动画进入，并尊重 Low motion/reduced-motion。
- [Electron Feature Launcher Animation](prompts/feature/20260913-FEAT-electron-feature-launcher-animation.md)：实际 Feature launcher 展开与页面选择增加可见、可中断的 surface animation；Low motion 只在用户明确开启后生效。
- [Electron Feature Animation and Scroll Fix](prompts/bugfix/20260913-FIX-electron-feature-animation-and-scroll-containers.md)：修复动画与基础 transition 合并导致的不可见问题；所有 Feature panel view 现在独立纵向滚动并保留底部安全间距。
- [Electron Narrow-Window Flex Layout](prompts/bugfix/20260913-FIX-electron-narrow-window-flex-layout.md)：让 composer、Chat 消息气泡与 Core canvas 在窗口缩小时可收缩、换行且不溢出。
- [Electron Page and History Transitions](prompts/feature/20260913-FEAT-electron-page-and-chat-transitions.md)：Pages 每行 5 个图标、详情 card 同宽与 viewport 预留，以及页面切换和 History 恢复动画。
- [Electron Collapsible Pages Navigation](prompts/feature/20260913-FEAT-collapsible-pages-overlay-navigation.md)：Pages 默认收起为 compact icon；展开后 5 列导航，详情页覆盖 Pages card 并保留切换入口，同时下移浮层并保留底部安全间距。
- [Electron Chat Scroll Anchor and Hidden Scrollbar](prompts/bugfix/20260909-FIX-electron-chat-scroll-anchor.md)：保留 Chat 原生滚动、隐藏滚动条，并避免异步回复抢回用户滚动位置。
- [Electron Confirmation Speech and Chat Tail Follow-up](prompts/bugfix/20260910-FIX-electron-confirmation-speech-and-chat-tail.md)：Automatic speech 朗读 awaiting-confirmation prompt，并修正连续 DOM append 的尾部跟随竞态。
- [Electron Confirmation Tail and Speech Start Follow-up](prompts/bugfix/20260910-FIX-electron-confirmation-tail-and-speech-start.md)：新回复强制收敛到 Chat 尾部、confirmation 使用完整权限提示，并从 Windows 语音流 offset 0 开始播放。
- [Markdown Chat Output Rendering](prompts/feature/20260910-FEAT-markdown-chat-rendering.md)：保留 DISPLAY Markdown 结构并在 Electron Chat 以安全 DOM subset 渲染；VOICE_EN 继续保持纯文本。
- [Automatic AI Transport Check](prompts/feature/20260910-FEAT-ai-transport-auto-check.md)：Core online 后由 Electron 自动触发 managed Luna 的无推理 transport verification；Direct API 不自动发起付费请求。
- [Native Intent Risk Routing and Localized App Open](prompts/bugfix/20260910-FIX-native-intent-risk-routing-and-localized-app-open.md)：Luna low-risk 候选复用正常 permission allow 路径，并支持无空格中文打开已登记应用。
- [Verified Subscription Desktop Chat](prompts/feature/20260906-FEAT-codex-subscription-desktop-chat.md)：90 与用户已完成 Luna 文本回复、原生确认按钮及拒绝链路桌面验收；不代表后台或并发已验收。
- [Architecture Overview](info/02-architecture/ARCHITECTURE_OVERVIEW.md)：结构、层级、依赖、边界、数据流、存储和差距。
- [Module Inventory](info/03-modules/MODULE_INVENTORY.md)：职责、接口、输入输出、依赖、权限、失败与限制。

## Target and Coordination / 目标与协调

- [Bounded Agent Upgrade](prompts/plan/20260908-PLAN-bounded-agent.md)：已采纳后续有界多步Agent方向；复用现有权限/结果/TaskRun契约，非默认路由，尚未实现或派发。

- [Contract Readiness Gates](prompts/plan/20260907-PLAN-contract-readiness.md)：已采纳Authority/结果/权限/状态/显式降级原则，按既有C1–C5补齐编码前决策与验收；不是新增实现或已完成契约冻结。

- [Engineering Foundations](prompts/plan/20260907-PLAN-engineering-foundations.md)：轻量安全/隐私/配置/迁移/备份恢复/测试/可观察性/context预算，按现有里程碑纳入；PLANNED，未派发实现。

- [Session Isolation Package](prompts/plan/20260907-PLAN-session-isolation.md)：90 与用户已验证 JARVIS-owned thread reuse、Core restart 和 desktop sidebar 无刷屏；ChatGPT 云端 Jarvis Chat 归属仍不受当前 App Server 支持。
- [Active-Writer Conflict Fix](prompts/bugfix/20260907-FIX-luna-active-writer-conflict.md)：90 已完成 `session_busy` 无 replacement-chat 的自动回归；用户已确认 JARVIS transport 不产生可见 ChatGPT sidebar chat，故当前 UI 不提供安全的 competing-client 手动入口。
- [Luna Dual Connection](prompts/feature/20260907-FEAT-luna-dual-connection.md)：90 已接线 manual Direct API/managed subscription selection、Core/AI split status 和无可见 cmd child；真实 Direct API inference 仍需用户 key 与付费测试确认。

- [Codex Subscription Chat Package](prompts/plan/20260906-PLAN-codex-subscription-chat.md)：已交付首个受限前台闭环的原始授权与范围；实际结果见上方 VERIFIED 实现记录，后台及并发不在已验收范围。

- [Previous Runtime/Luna Order](prompts/plan/20260906-PLAN-runtime-luna-order.md)：历史顺序；接入方式与下一步以订阅接入工作包为准。

- [Module Development Plan](prompts/plan/20260906-PLAN-module-development.md)：结构重整方式、未完成模块、未来scope与新任务分工。计划不是当前实现。

[Target](architecture/TARGET_ARCHITECTURE.md) 仍为目标权威，已由 90 按用户批准更新订阅 foreground transport 边界。现有代码冲突必须记为 gap。Phase A–C only，Phase D 需明确授权。
Obsidian 沿用既有治理记录（不是已实现模块）：
- [Development Ownership](../../Documents/GitHub/obsidian-vault/JARVIS/Plans/Roadmap/DEVELOPMENT_OWNERSHIP.md)
- [M0 contracts and migration](../../Documents/GitHub/obsidian-vault/JARVIS/Plans/Roadmap/M0%20Development%20Coordination.md)
- [M1.1 work package](../../Documents/GitHub/obsidian-vault/JARVIS/Plans/Roadmap/M1.1%20Work%20Package.md)

上述跨仓库链接是本机导航，不保证其他 clone 可用；找不到时必须报告，不能猜测权限或契约。app/main.py/app/api.py 等共享入口仍按 single-writer。SQLite operational schema 归 02；RAG FTS 归 03。模型内容、RAG 与 coding classification 均不是执行授权。

## Documentation Authority and Sync / 文档权威与同步

Repository docs/info 是当前实现说明原本；源码提供核验依据，文档不能覆盖真实实现。Obsidian 对应 Current/Components 是带 source、baseline 的阅读镜像；禁止双向独立改写。
Target、ownership、契约、计划各自保留既有权威，不因 implementation SSOT 改变产品目标。
普通开发先相关 Info → 搜索相关 Prompt Record → 相关源码，不扫描全部历史。
新规则不默认保留兼容；M0 C1 中过渡 serializer 要求如需保留，必须在实施记录明确原因、范围、owner、删除条件和里程碑，不可当成永久默认。

## History and Testing / 历史与验证

- [Documentation task records](prompts/documentation/)：迁移、同步与工程规则变更。
- [Bug-fix records](prompts/bugfix/)：已调查的运行时与行为修复记录。
- [Changelog](CHANGELOG.md)：已完成文档任务时间线。
- tests/ 和 desktop_ui/test/ 是测试入口；本轮没有重跑应用测试。
- docs/OBSIDIAN_MIGRATION_2026-09-05.md、旧 Codex plan 等保留历史，不能优先于当前基线说明。

## Obsidian Navigation / 知识库入口

使用已有 JARVIS/Knowledge、Plans、Records、Memory；不创建 JARVIS/docs 或新知识根。实现镜像位于 Current/Components，历史放 Records/Changes，未来工作放 Plans。Memory 不是通用工程文档目录。
