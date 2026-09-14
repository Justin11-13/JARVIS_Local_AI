# Changelog / 改动时间线

## 2026-09-14 — Fix duplicate short speech and unavailable Windows voice settings (IMPLEMENTED — source/static/Python/Node verified; real audio acceptance pending)

修复两版 Electron 的短回复朗读链路：流式阶段已经暂存但尚未达到 chunk 最小长度的文字，不会在 complete event 再追加完整 `response.speech`，因此短回复不会重复朗读。Windows Speech service 也不再把缺少可选的 per-user `Speech_OneCore` settings key 当成系统语音不可用；它会明确返回 `Windows default` 与 speed `0`，同时合成脚本使用 Windows Runtime 默认 voice。两版 Electron static verifier 与 Node suite 均通过 `59/59`，Windows Speech focused tests 通过 `5/5`。
详情见 [Speech duplicate and Windows default settings fix](prompts/bugfix/20260914-FIX-electron-speech-short-reply-and-settings.md)。

## 2026-09-14 — Internal Test README and Phase Scope (IMPLEMENTED)

根目录 README 已改为中英双语，并以内测版 Electron + packaged Core 为主要入口；补齐 Windows 安装、Managed ChatGPT、Direct API、可选 Obsidian、源码构建、安全边界和真实限制，同时将未来方向按权威 Target Architecture 的 Phase A-C 分开标为计划；Phase D 继续明确为未授权。此次仅修改文档，不改变运行时。详情见 [Internal Test README and Phase Scope](prompts/documentation/20260914-DOCS-internal-test-readme-and-phases.md)。

## 2026-09-14 — Bundle Codex CLI in the Internal Test installer (IMPLEMENTED — package/runtime/source/static verified; clean-machine install pending)

The Internal Test Windows x64 installer now includes the native Codex CLI App Server at
`resources/core/codex/codex.exe`. JARVIS Core resolves this packaged executable before development-only command
paths, so users no longer need to install Node.js, npm or Codex CLI manually. The build pins `@openai/codex` `0.153.2`,
records its Apache-2.0 notice, and keeps ChatGPT/Codex authentication user-owned; no credentials are bundled. The
current Setup is `816,689,454` bytes (SHA-256
`137B9FED575B83757485F4419A94D5A98EEA346BAA75FFB94C68D731DE63F199`); bundled CLI smoke check, packaged Core health,
Electron static verification, Electron Node `58/58`, and focused Python adapter `44/44` passed. Clean-machine install,
first-login and provider acceptance remain pending.
Details: [Bundled Codex CLI installer record](prompts/feature/20260914-FEAT-bundle-codex-cli-installer.md) and
[Electron + JARVIS Core Windows Packaging](info/05-integrations/ELECTRON_CORE_PACKAGING.md).

## 2026-09-14 — Build complete Internal Test Electron + JARVIS Core Windows installer (IMPLEMENTED — package/runtime verified on current host; clean-machine install pending)

Internal Test now has a complete Windows x64 packaging path: PyInstaller `onedir` builds the Core,
Electron Builder assembles it under `resources/core/jarvis-core.exe`, and NSIS uses an assisted installer
with `oneClick=false` and `allowToChangeInstallationDirectory=true`. Packaged Core resources include the
offline embedding model and safe default registries, while `.env`, credentials, current-machine `config/`
and `data/`, Obsidian Vaults, and personal project/app paths stay excluded; mutable runtime state moves to
`%LOCALAPPDATA%\JARVIS\InternalTest`. The final local Setup is about 753 MB. Final Core health, packaged
Electron `--verify`, normal Electron-to-Core startup/shutdown, both static verifiers, both supervisor suites
(`8/8` each), Python compileall, and runtime-path assertions passed. The installer has not yet been installed
on a separate clean Windows account, so destination-chooser and clean-machine acceptance remain pending.
Details: [Electron + JARVIS Core Windows Packaging](info/05-integrations/ELECTRON_CORE_PACKAGING.md) and
[Internal Test Electron + Core installer record](prompts/feature/20260914-FEAT-internal-test-electron-core-installer.md).

## 2026-09-14 — Forward Managed JARVIS turn usage to the widget (IMPLEMENTED — source/static/Python/Node verified; native visual pending)

Managed Luna now consumes the official App Server `thread/tokenUsage/updated` notifications for the
owned ephemeral JARVIS thread. Explicit cumulative thread totals are converted to the current-turn
delta and forwarded through the existing `provider_reported` response DTO, so the compact JARVIS
widget can persist Managed Input/Output/Total values without importing account-wide ChatGPT/Codex
usage. Replayed prior-turn notifications are filtered by thread/turn identity; missing or decreasing
counters remain unavailable. The account-level Feature Usage source stays separate. Focused Python
usage/adapter tests passed (`47/47`); both Electron static verifiers and Node suites remain green
(`57/57` each). Native visual acceptance remains pending under the existing Windows GPU/runtime blocker.
Details: [JARVIS-only Token Usage widget summary](prompts/feature/20260914-FEAT-jarvis-only-token-widget-summary.md).

## 2026-09-14 — Make Token Usage Widget JARVIS-only Summary (IMPLEMENTED — source/static/Node verified; native visual pending)

Core-stage Token Usage widget no longer renders a heatmap or trend chart. It now shows compact
Input, Output, and Total values from JARVIS's own persisted renderer `provider_reported` response
records (`jarvis.foreground.token-usage.v1.{edition}`), formatted in `k`/`M` units and kept explicit
as `—` when a provider field is absent. Managed ChatGPT account buckets, which cannot distinguish
JARVIS from the user's other Codex client usage, remain confined to the explicit Feature Usage page;
the full Feature chart remains available. Both editions now label the widget `JARVIS USAGE` and keep
the same bridge/API/persistence contracts. Both static verifiers and both Electron Node suites passed
(`57/57` each); native visual acceptance remains pending under the existing Windows GPU/runtime blocker.
Details: [JARVIS-only Token Usage widget summary](prompts/feature/20260914-FEAT-jarvis-only-token-widget-summary.md).

## 2026-09-14 — Add Token Usage Widget Axes and Point Details (PARTIALLY SUPERSEDED — source/static/Node verified; native hover pending)

The full Feature usage chart now shows a subtle vertical Y axis
with compact `k`/`M` scale labels, X-axis date ticks, and a marker for each plotted day. Hovering
or keyboard-focusing a marker exposes its date and current token value (for example, `9/13 · 12.4k tokens`)
through an in-chart tooltip plus accessible label/title. Both Electron editions share the
same renderer implementation; the compact Core widget was subsequently changed to the JARVIS-only
three-metric summary above. Managed ChatGPT account usage and Direct API provider usage remain separate
and persistent, with no Core/API or storage contract changes. Both static verifiers and both Electron
Node suites passed (`57/57` each); native hover acceptance remains pending under the existing Windows
GPU/runtime blocker. Details: [Token Usage widget axes and point details](prompts/feature/20260914-FEAT-token-widget-chart-axes-tooltip.md).

## 2026-09-14 — JARVIS Response Language Preference (IMPLEMENTED — source/API/static/contract verified; native Electron runtime pending)

JARVIS text replies now default to English through `ChatRequest.output_language=en`; Settings in both Electron
editions adds a separate Response language selector for English/中文. The selected value is saved locally under
`jarvis.response.language.v1` and is forwarded through preload/main/Core bridge to `/api/chat` and `/api/chat/stream`,
then into managed Luna and Direct provider prompts. Date language, UI language, local history, `[VOICE_EN]`, and
provider/permission behavior remain separate; existing history is not translated and no global UI language switch was added.
Both `npm run verify:static` and `node --test test/*.cjs` suites passed (`57/57` each); changed Python modules compile and
the Python regression set excluding the unrelated `test_rag_final.py` passed (`302/302`). Native Electron `--verify`
remains pending because this Windows environment's GPU child exits with `-1073741515`; `test_rag_final.py` remains
blocked by the environment's missing `chromadb` module. Details: [JARVIS output language setting](prompts/feature/20260913-FEAT-output-language-setting.md).

## 2026-09-14 — Connect Codex Account Usage and Keep Direct API Usage Separate (IMPLEMENTED — Feature-page source/static/focused verification passed; compact widget behavior superseded; native runtime pending)

接入官方 Codex App Server `account/usage/read`：Managed ChatGPT 的账号汇总与每日 usage buckets
现在通过 Core 的 `GET /api/settings/ai/usage` 读取、去敏并以 edition-scoped renderer localStorage
持久化；显式 Feature 页面会实时刷新并明确标记 live/cached/stale/unavailable。Core 顶部 compact widget
后来改为只显示 JARVIS 自己的 provider-response summary，不再消费 account buckets。
Direct API 不会触发 Managed account RPC，而是继续使用 OpenAI Responses、Gemini、DeepSeek 或
OpenAI-compatible provider 在每次 chat response 中明确报告的 input/output/total counts；两种来源
不会混加，也不会估算缺失的 input/output。两版 Electron 的 bridge/preload/main 都已接入固定 endpoint，
新增 adapter/API/renderer/static/contract tests。focused Python `6/6`、两版 static `17/17` 与语法检查
通过；既有 output-language contract failures 和 Electron runtime/GPU 限制保持原样。详情见
[Codex account usage integration](prompts/feature/20260913-FEAT-codex-account-usage.md)。

## 2026-09-13 — Canonical Tool Definition Catalog (IMPLEMENTED — scoped source/parity/regression verified; unrelated full-suite failures remain; Windows runtime unchanged)

新增 `services/tool_catalog.py` 作为 provider-neutral native-tool metadata SSOT，删除
`GeminiAdapter` 的重复 110 项手写 declarations 与 API 的重复 required/optional schema mapping；
Gemini declarations、API schema 与 managed-GPT bounded intent catalog 现在从同一份 definitions 派生。
`app/main.py` 的 `AVAILABLE_TOOLS` 仍是执行 registry，权限、TaskRouter、native-intent aliases、
unsupported-capability errors 与 managed GPT text-only 行为没有改变。新增 catalog parity tests；本次
`3/3` catalog、`62/62` 相关回归、changed-module `py_compile` 与
`110/110/110/110/110/110` registry/schema/alias/Gemini/catalog/intent parity 均通过。全量 suite 当前执行
`299` tests，其中 `291` passed、`8` 个既有 output-language/locale mock contract failures（不在本次
refactor touched lines）。详情见
[Canonical Tool Definition Catalog](prompts/refactor/20260913-REFACTOR-canonical-tool-definition-catalog.md)。

## 2026-09-13 — Keep JARVIS Chat Out of Codex History (IMPLEMENTED — source/API/focused regression verified; runtime/desktop observation pending)

修复 managed Luna 将 JARVIS 聊天写入 Codex“最近”列表的问题：App Server thread 现在明确使用并校验
`ephemeral: true`，非临时响应 fail closed；transport mapping 只保存在当前 Core 进程内存，不再写入或从
`conversation.json` 恢复。JARVIS 本地 terminal transcript 保持持久化；Core/child restart 后创建新的临时
thread，不恢复旧 Codex history。旧的 Codex 条目不由 JARVIS 自动删除。详情见
[JARVIS/Codex history isolation](prompts/bugfix/20260913-FIX-jarvis-chat-not-in-codex-history.md)。

## 2026-09-13 — Automatic Language-Matched Speech Voices (IMPLEMENTED — source/focused tests verified; Windows runtime pending)

两版 Electron automatic speech 现在在 renderer 本地按回复文字识别中文与非中文：中文回复优先使用用户已选的中文 voice，
否则按已安装列表选择第一个 `zh-CN` voice，再退到其它 `zh-*` voice；英文/其它文字继续使用用户当前选择或 Windows default。
同一条 streamed response 会固定一个 voice ID，避免不同 speech chunk 之间换包。voice inventory 在 Core ready 后后台加载，
不阻塞 chat request，也不增加 Luna/Core inference 请求；没有中文 voice 时保留当前选择并记录显式提示，不静默伪装为中文语音。
语言检测、voice selection、队列 voice 传递与两版 static/Node focused suite `34/34` 已通过；真实 Windows audio/shortcut runtime 仍待重启后验收。
详情见 [Automatic Language-Matched Speech Voices](prompts/feature/20260913-FEAT-auto-language-speech-voice.md)。

## 2026-09-13 — Widen Token Widget and Restore Core Scale (IMPLEMENTED — source/static/local-browser render verified; native window pending)

两版 Electron 将默认 Token Usage trend-only widget 宽度从 320px 调整为最大 360px；Core canvas normal height 调整为 `clamp(390px, 56vh, 600px)`，短窗口限制为 300–400px，保持 stage 居中并提升 Core 可读尺寸。widget 关闭按钮已移除，作为常驻 preview；完整 Usage 页面仍从 Feature 进入。两版 static verifier、Node suites 各 54/54、本地浏览器尺寸/无关闭按钮检查通过；原生 Electron 窗口仍需单独验收。详情见 [Token widget size and close control](prompts/bugfix/20260913-FIX-electron-token-widget-size-and-close-control.md)。

## 2026-09-13 — Lift Floating Cards and Center Core (IMPLEMENTED — source/static/local-browser render verified; native window pending)

两版 Electron 将 Chat、Token Usage trend-only widget 与 Feature 共用的 `--floating-top` 整体上提（正常最小 36px、矮窗口最小 28px）。Core canvas 不再使用固定的 240px 顶部 reserve，改用受限 `--core-height` 在 Core stage 的 `top: 50%` 垂直居中；矮窗口自动收紧 Core 高度，避免 widget 遮挡。页面内容、bridge、Core/API、持久化与路由不变。两版 static verifier、Node suites 各 54/54、本地 Chromium 几何检查和 `git diff --check` 通过；原生 Electron 窗口仍需单独验收。详情见 [Floating cards and Core centering](prompts/bugfix/20260913-FIX-electron-floating-cards-and-core-centering.md)。

## 2026-09-13 — Complete Remaining Software PC-Control Domains (IMPLEMENTED — source/mock/static verified; Windows runtime pending)

完成 App Control、Power、Window Management、Files、Clipboard、Network、Bluetooth、Audio Devices、Media 与 Keyboard/Mouse 的
canonical native-tool modules，并接入 registry、permission、API/Gemini schemas、native-intent routing、audit boundary 与回归用例。
不支持的 generic Bluetooth per-device connection、audio default-device selection 与 current-media metadata 保持显式错误；
本批次 focused regression `156/156`、全量 Python regression `294/294`、changed-module `py_compile` 和 registry/schema/native-intent/Gemini parity `110/110/110/110` 已通过；真实 Windows device/window/input acceptance 仍待普通用户环境确认。详情见
[Software-Level PC Control Remaining Domains](prompts/feature/20260913-FEAT-software-pc-control-remaining-domains.md)。

## 2026-09-13 — Fix Scrolling Across All Feature Pages (IMPLEMENTED — source/static/Node verified; native window pending)

修复两版 Electron Feature inspector 的共享高度链：`.page-stack` 现在建立明确的 column flex 容器，活动 `.panel-view` 作为可收缩 flex item 保持自己的纵向滚动。Tasks、History、Core、Memory、Knowledge、Settings、Voice 等所有 Feature 页面在内容超出 card 高度时都能继续向下读取；没有修改页面路由、Core/API、bridge、权限或持久化。两版 static verifier 与全部 Node test entrypoints 通过；原生 Electron 窗口仍需单独验收。详情见 [Feature pages scroll chain fix](prompts/bugfix/20260913-FIX-electron-feature-pages-scroll-chain.md)。

## 2026-09-13 — Managed Luna Response Latency Optimization (IMPLEMENTED — source/focused tests verified; shortcut runtime pending)

JARVIS 的 adapter-owned managed Luna child 现在显式使用 `low` reasoning effort，不再继承用户全局 Codex 的 `max` 设置；同一健康 child 且 developer-instruction context 未变化时复用已验证 thread，跳过重复 `thread/resume` RPC，并输出 `thread_resume_skipped` timing。Core restart、mapping/auth 校验和 context 变化仍走原有显式恢复与失败路径。未切换模型/provider、未改全局配置、未加入 fallback 或 retry。详情见 [Response Latency Optimization](prompts/bugfix/20260913-FIX-response-latency-optimization.md)。

## 2026-09-13 — Move Token Usage Preview into a Core-top Widget (IMPLEMENTED — source/static/local-browser render verified; native window pending)

Token Usage preview 已从 Core canvas 的覆盖层移到 Core stage 顶部、与 Chat/Feature 共用顶部锚点的独立小 widget：预览只保留 320px 级别的 Daily token trend，
summary、activity heatmap 和状态说明留在完整页面，不再使用内部 scrollbar；Core canvas 预留顶部安全区，hologram 保持在 widget 下方完整显示。Feature → Usage 的完整 inspector
与滚动行为、provider-reported realtime/persistent usage 数据不变。两版 Electron static verifier、Node suites 各 54/54 与本地
1280×720 Chromium render 检查通过；原生 Electron 窗口仍需单独验收。详情见 [Token Usage widget placement fix](prompts/bugfix/20260913-FIX-electron-token-usage-widget-placement.md)。

## 2026-09-13 — Batch Speech Chunks Within Sentence Window (IMPLEMENTED — source/tests verified; Windows audio smoothness pending)

继续修复 speech 断句：两版 Electron 的 `SpeechChunker` 现在使用 `72–240` 字符窗口，并选择窗口内最后一个自然句子边界，
而不是在第一个达到最小长度的句号处立即切分。连续短句会合并到同一 TTS item；无标点文本达到上限才按空格有界切分。
文字流、Windows speech bridge、current/next queue 和取消语义不变。详情见 [Speech Chunk Batching Follow-Up](prompts/bugfix/20260913-FIX-speech-chunk-batching.md)。

## 2026-09-13 — Fix Feature Animation Visibility and Page Scrolling (IMPLEMENTED — source/static/test verified; native window pending)

修复两版 Electron 中 Feature launcher/inspector 的进入效果不明显问题：保留 `.action-dock` 340ms 与 inspector 400ms 动画，进入前会取消旧 CSS animation、强制建立新的样式边界，快速切换不会留下旧动画。所有 Feature `panel-view` 现在拥有明确的纵向滚动容器、横向溢出保护与稳定 scrollbar gutter，长页面可以在 card 内完整读取；Low motion 仍只在用户明确开启时生效。两版 Electron Node suites 各 53/53、完整 Python regression 275/275 通过；原生窗口仍需单独验收。详情见 [Feature animation and scroll fix](prompts/bugfix/20260913-FIX-electron-feature-animation-and-scroll-containers.md)。

## 2026-09-13 — Fix Speech Chunk Fragmentation (IMPLEMENTED — source/tests verified; Windows audio smoothness pending)

调整两版 Electron 的 `SpeechChunker`：默认 chunk 从 `18–72` 改为 `32–120` 字符，只在句号、问号、感叹号、分号或换行处分段，逗号和冒号不再单独触发 TTS。
这样可以减少短音频连续合成/播放造成的断续；文字 streaming、current/next 预合成、取消和错误语义不变。详情见 [Speech Chunk Fragmentation Fix](prompts/bugfix/20260913-FIX-speech-chunk-fragmentation.md)。

## 2026-09-13 — Fix Internal-Test Voice State Initialization (IMPLEMENTED — source/static verified; Windows audio pending)

修复内测版 Voice renderer 遗漏 `installedSpeechVoices`、`selectedSpeechVoiceId` 与 `currentSpeechVoiceName` 初始化，导致 Voice 页面显示
`selectedSpeechVoiceId is not defined`，并在自动语音真正调用 Windows speech bridge 前失败。两版 static verifier 现在都检查这些声明；没有修改
Windows voice、Core/API、TTS queue 或 fallback 语义。详情见 [Internal-Test Voice State Fix](prompts/bugfix/20260913-FIX-internal-test-voice-state.md)。

## 2026-09-13 — Fix TaskManager Windows History Access Denied (IMPLEMENTED — Python regression verified)

修复 `TaskManager` 写入 `data/memory/task-history.json` 时，固定 `task-history.tmp` 与目标文件替换可能被
Windows `WinError 5` 中断的问题。保存现在在 sibling `task-history.lock` 下执行，临时文件按 PID/UUID 隔离，
并对短暂的 Windows replacement `PermissionError` 进行有界重试；长期占用或真实 ACL 失败仍保留原始 warning，
不切换备用存储、不伪造成功。TaskManager persistence tests 4/4、完整 Python regression 275/275 通过；API
回归改用无持久化 TaskManager，避免测试任务竞争生产历史文件。Core/API、任务状态、路由和权限语义未改变。
详情见 [TaskManager Windows history access-denied fix](prompts/bugfix/20260913-FIX-task-history-windows-access-denied.md)。

## 2026-09-13 — Fix Cross-Thread Streaming Lock Failure (IMPLEMENTED — source/regression verified; runtime retest pending)

修复 managed Luna 流式响应在 FastAPI/Starlette worker thread 于不同 `yield` 之间恢复或关闭时，使用线程所有权绑定的
`RLock` 导致 `cannot release un-acquired lock` 的问题。`CodexAppServerAdapter` 现在使用仍能串行保护 resident
process/session 的 primitive `Lock`，并新增跨 worker thread 完成 stream 的回归测试；没有加入 retry、provider fallback
或兼容层。Core 进程需要重启后才会加载此修改。详情见 [Streaming Lock Fix](prompts/bugfix/20260913-FIX-streaming-cross-thread-lock.md)。

## 2026-09-13 — Electron Token Usage Feature Card (IMPLEMENTED — source/static/test verified; native window pending)

Token Usage 现在恢复为 Feature page，并在中央 Core stage 上方保留缩小版 realtime preview；两者显示同一份
summary stats、28-day activity heatmap 与 14-day token trend 数据。OpenAI Responses、OpenAI-compatible/DeepSeek
与 Gemini 只在 provider 明确返回 usage 时透传 input/output/total counts，renderer 按 development/internal-test
edition 分开写入 localStorage，并在 terminal response 后实时刷新；没有 usage 的 managed ChatGPT subscription 或
gateway 响应保持 unavailable。未新增 account/quota/billing endpoint、inference probe、模型/API fallback 或 Core storage。
Python focused/full suites、两版 Electron static/Node suites 与 syntax checks 已通过；当前 host 的原生 Electron window
仍需单独 acceptance。
详情见 [Electron Token Usage Card](prompts/feature/20260913-FEAT-electron-token-usage-card.md)。

## 2026-09-13 — Electron Feature Launcher Animation (IMPLEMENTED — source/static verified; runtime pending)

两份 Electron edition 的实际 `Feature` launcher 现在在展开时使用 `feature-nav-enter`，选择页面时使用 `feature-page-enter`，并与既有 inspector header/content transition 分开管理；rapid switching 会取消 stale animation。Low motion 改为仅在本地明确保存 `true` 时启用，fresh profile 默认 Standard motion；不改变 Core/API、路由、权限、持久化或 shortcut 语义。详情见 [Electron Feature Launcher Animation](prompts/feature/20260913-FEAT-electron-feature-launcher-animation.md)。

## 2026-09-13 — Electron Narrow-Window Flex Layout (IMPLEMENTED — source/static verified; runtime pending)

两份 Electron renderer 已为 composer input、hint、send button、Chat message body/Markdown paragraph 与 Core canvas 增加明确的 flex/min-width/最大宽度边界；长 user text 会在气泡内换行，窄窗口不会把输入控件或 Core canvas 撑出容器。未改变 transcript、滚动、Core/API、bridge、权限、持久化或 shortcut 行为。详情见 [Electron Narrow-Window Flex Layout](prompts/bugfix/20260913-FIX-electron-narrow-window-flex-layout.md)。

## 2026-09-13 — Electron Feature Page Switch Animation (IMPLEMENTED — source/static verified; runtime pending)

两份 Electron edition 的 Feature 页面切换已强化为可见的 header/content 淡入与 18px 横向到位过渡，保留 bounded blur、token 中断和 Low motion/reduced-motion 路径；不动画 card 尺寸或布局属性，也不改变路由、滚动、Core/API、bridge、权限、持久化与 shortcut 语义。详情见 [Electron Feature Page Switch Animation](prompts/feature/20260913-FEAT-electron-feature-page-switch-animation.md)。

## 2026-09-13 — Software-Level PC Control System Status (IMPLEMENTED — source/mock/static/bridge-contract verified; Windows runtime pending)

新增 `skills/system_status.py`，通过现有 `psutil` 提供 structured read-only `get_cpu_usage`、`get_ram_usage`、`get_disk_usage`、`get_system_uptime`、`get_battery_status` 与 `get_system_summary`；Battery 的 registry owner 从 `skills/windows.py` 迁移到该模块，未保留旧兼容实现。追加显式 read-only Windows Battery Class IOCTL detail path，在驱动报告时把剩余/full-charge/design mWh capacity 与 cycle count 放入 structured result；不支持时保留 null、availability flag 与 detail error。Electron 两个 edition 的 Device page 通过固定 `/api/system-status` bridge 展示这些诊断字段。已完成 registry、API schema、READ permission、Gemini declaration、bounded native-intent routing、structured failure、audit、native-layout mock tests、bridge contract tests 与 static verification。首轮回归捕获并修正了 compound CPU-plus-disk phrase 落入旧 CPU/RAM shortcut 的 partial-routing root cause；完整 focused regression `137 tests`、`py_compile`、47/47/47 parity、两版 bridge contract 各 16/16、两版 full Electron Node suite 各 52/52、static verifier 与 syntax checks 通过。FastAPI `tests.test_api_fast_replies` 已使用项目 `.venv\Scripts\python.exe` 的 Python 3.14.6 运行时通过 `42/42`；此前的 `pydantic_core` mismatch 是 bundled Python 3.12 错误读取项目 3.14 依赖造成的解释器调用问题。只读 Battery Class probe 未发现 readable system battery device。真实 Windows battery endpoint 与窗口 acceptance 仍待完成。详情见 [Software-Level PC Control System Status](prompts/feature/20260913-FEAT-software-pc-control-system-status.md)。

## 2026-09-13 — Software-Level PC Control Theme (IMPLEMENTED — source/mock verified; Windows runtime pending)

新增独立 `skills/theme.py`，通过 guarded Python `winreg` 访问 Windows current-user Personalize settings，提供 `get_theme` 与 `set_theme(mode)`，只支持 `light`/`dark`。实现会同时读取/写入 `AppsUseLightTheme` 与 `SystemUsesLightTheme`，mixed/malformed/missing state 显式失败，不混入 Night Light，也不改变 JARVIS presentation-local visual theme。Theme 与 Wallpaper/Audio/Brightness focused regression batch 共 `111 tests` 通过，`py_compile` 与 42/42/42 registry-schema-declaration static check 通过；FastAPI test module 仍受 `.venv`/bundled Python 3.12 `pydantic_core` binary mismatch 阻断。未进行真实 Windows theme mutation；普通用户 endpoint acceptance 仍待完成。详情见 [Software-Level PC Control Theme](prompts/feature/20260913-FEAT-software-pc-control-theme.md)。

## 2026-09-13 — Software-Level PC Control Wallpaper (IMPLEMENTED — source/mock verified; Windows runtime pending)

新增独立 `skills/wallpaper.py`，通过固定 `ctypes` User32 `SystemParametersInfoW` 路径提供 `get_wallpaper` 与 `set_wallpaper`。已接入 registry、API schema、READ/LOW permission、bounded native-intent routing、structured ToolResult 和现有审计 logger；设置前严格验证 regular file、`.bmp`/`.jpg`/`.jpeg`/`.png` 扩展名与 basic signature，并在写入后回读 effective path。Wallpaper 与 Audio/Brightness focused regression batch 共 `98 tests` 通过，`py_compile` 与 40/40/40 registry-schema-declaration static check 通过；FastAPI test module 仍受 `.venv`/bundled Python 3.12 `pydantic_core` binary mismatch 阻断。未进行真实 Windows wallpaper mutation；普通用户 endpoint acceptance 仍待完成。详情见 [Software-Level PC Control Wallpaper](prompts/feature/20260913-FEAT-software-pc-control-wallpaper.md)。

## 2026-09-13 — Low-Latency Streaming Text and Synchronized TTS (IMPLEMENTED — source/static/mock verified; runtime pending)

新增 Core `/api/chat/stream` NDJSON `start`/`delta`/`complete`/`error` contract、managed/Direct provider
stream adapters、TaskRouter cancellation/task accounting，以及固定 Electron main/preload bridge。两版 renderer
现在通过 renderer-only `DisplayPacer` 以默认约 42 chars/s 逐步显示响应，并从已显示的 response text 按 18–72 字符边界产生 provisional speech chunks；该 pacing 不降低 Core/provider/TTS 生成速度，response-time metric 仍使用实际 stream completion；terminal
`[VOICE_EN]` 仍保留为 canonical response narration，不会在 streamed display speech 后重复播放。current/next
WAV synthesis/playback 队列保持顺序；Automatic speech Off 不合成，TTS failure 不影响文字，新消息会取消旧
stream/audio。新增 request-relative response latency metrics 与 focused Python/Node/static/mock tests；本次 pacing
targeted Node tests 两版各 `12/12` 通过，static gate 通过；完整 Electron suite 当前各有一个既有
`core-contract.cjs` 的 `systemStatus` allowlist expectation mismatch，未因本次显示 pacing 改动而修改无关 contract。
本轮
真实运行已验证 Core NDJSON `start`/`delta`/`complete`，但修正后的普通 Electron Windows TTS 仍待重测。
详情见 [feature record](prompts/feature/20260913-FEAT-low-latency-streaming-text-synchronized-tts.md)。

## 2026-09-13 — Software-Level PC Control Brightness (IMPLEMENTED — source/mock verified; Windows runtime pending)

新增独立 `skills/brightness.py`，通过固定 Windows WMI/CIM `powershell.exe` 路径提供 `get_brightness`、`set_brightness`、`brightness_up` 与 `brightness_down`。已接入 registry、API schema、READ/LOW permission、bounded native-intent routing、structured ToolResult 和现有审计 logger；严格验证 0–100 level、1–100 step，不静默 clamp，不使用 UI/hardware-key/third-party fallback。Audio/Brightness 完整 focused batch 已通过 69 tests；FastAPI test module 仍受现有 Python 3.12/3.14 `pydantic_core` binary mismatch 阻断；Wallpaper 及后续 domains 尚未开始。详情见 [Software-Level PC Control Brightness](prompts/feature/20260913-FEAT-software-pc-control-brightness.md) 和 [current integration info](info/05-integrations/SOFTWARE_PC_CONTROL.md)。

## 2026-09-13 — Electron Monitor Content Height and Flexible Feature Page (IMPLEMENTED — source/static verified; runtime pending)

两份 Electron edition 已把 System Monitor 从固定 220px 高度改为内容自适应，保留 170px 左侧布局预留但不再强行撑出底部空白；Feature/inspector card 改为内容自适应高度，并以 viewport `max-height` 与 24px 底部安全间距限制长页面，短页面不会填满空白区域。页面滚动、路由、Core/API、bridge、权限、持久化与 shortcut 语义不变。详情见 [Electron Monitor Content Height and Flexible Feature Page](prompts/bugfix/20260913-FIX-electron-monitor-content-height-and-flexible-feature-page.md)。

## 2026-09-13 — Software-Level PC Control Audio Phase 1 (IMPLEMENTED — source/mock verified; Windows runtime pending)

新增独立 `skills/audio.py`，通过 pycaw/comtypes 提供 `get_volume`、`set_volume`、`volume_up`、`volume_down`、`mute`、`unmute` 与 `get_mute_state`。工具复用现有 TaskRouter/API ToolResult 边界，返回 final actual Audio `data` 与结构化 `{code, detail}` error；输入范围严格验证，不静默 clamp。新增 READ/LOW 权限分类、bounded native-intent 路由、legacy Gemini declarations/API schema、隐私脱敏的 `jarvis.audit` logger 与 mock endpoint tests。没有加入 virtual-key/PowerShell fallback、UI、硬件厂商控制或 Brightness。当前普通/隔离 Python runtime 未安装 pycaw/comtypes，因此真实 Windows endpoint 仍待依赖安装后的普通用户验收。详情见 [Software-Level PC Control Audio](prompts/feature/20260913-FEAT-software-pc-control-audio.md) 和 [current integration info](info/05-integrations/SOFTWARE_PC_CONTROL.md)。

## 2026-09-13 — Electron Side Card Vertical Stretch (IMPLEMENTED — targeted layout verified; full suite blocked by pre-existing contracts; runtime pending)

两份 Electron edition 的桌面 Chat/monitor card stack 现在按 viewport 剩余高度向下伸展，保留顶部保护、10px 卡片间距与底部安全空间；右侧 Feature/Tool inspector 改为从共享顶部锚点延伸至 24px 底部间距，不再受 580px 上限限制。矮窗口继续使用收紧的高度保护，长内容仍在卡片内部滚动。无页面路由、Core/API、bridge、权限、持久化或 shortcut 语义变化。详情见 [Electron Side Card Vertical Stretch](prompts/bugfix/20260913-FIX-electron-side-card-vertical-stretch.md)。

## 2026-09-13 — Electron Feature Anchor and Grid-Free Stage (IMPLEMENTED — source/static verified; runtime pending)

两份 Electron edition 的 Feature/Pages 浮层现在使用与 Chat 相同的顶部锚点（`--dock-top-offset: 0px`），仍保留 24px 底部安全间距。左下角 Motion control strip 已隐藏，但 Core RAF、旋转、Pause 与 Settings Low motion 状态逻辑不变。Core stage 背景网格 overlay 与对应主题 token 已移除，主题背景、orbit ring 与 Core canvas 保留。无路由、bridge、Core/API、权限、持久化或 shortcut 语义变化。详情见 [Electron Feature Top Anchor and Motion/Grid Cleanup](prompts/bugfix/20260913-FIX-electron-feature-top-anchor-and-hide-motion-controls.md)。

## 2026-09-13 — Electron Card Border Rendering Polish (IMPLEMENTED — source/static verified; runtime pending)

两份 Electron edition 的 rounded card surfaces 现在统一使用独立绘制边界、`background-clip: padding-box` 与 backface visibility，减少 Windows fractional DPI 下的 1px border 二次采样。Pages launcher/inspector 外框切换保留 opacity/位移动画，但移除外框自身的 blur 与 `scale(.96)`；页面内容和 History restore 的既有过渡不变。没有修改 Core、AI、IPC、routing、permissions、persistence 或 shortcut。详情见 [Electron Card Border Rendering Polish](prompts/feature/20260913-FEAT-electron-card-border-rendering.md)。

## 2026-09-13 — Voice Visibility and Feature Navigation Polish (IMPLEMENTED — source/static verified; runtime pending)

Both Electron editions now expose the Voice inspector through their explicit page allowlists. The compact Pages launcher uses the English `Feature` label with a wider single-line control, and the Voice refresh/test buttons move into a dedicated full-width row below the introduction so they do not compete with the heading or wrap over content. No route, bridge, permission, Core, AI, or fallback semantics changed. The corresponding Feature record is [Electron Voice, Motion, and Feature Navigation](prompts/feature/20260913-FEAT-electron-windows-voice-packages-and-low-motion.md).

## 2026-09-13 — Electron Windows Voice Packages and Low Motion Feature (IMPLEMENTED — source/static verified; runtime pending)

开发版新增完整 Voice feature：Pages → Voice 通过固定 Core bridge 实时读取 Windows OneCore 已安装语音包，支持刷新、选择、试听，选择以 `jarvis.auto-speech.voice.v1` 保存在当前 Electron edition，并由 automatic speech 传回指定 voice ID；空选择明确表示使用 Windows 当前默认语音。内测版继续隐藏 Voice 入口。新增 `GET /api/system-speech/voices` 与可选 speech voice contract，不使用 browser `speechSynthesis`、不安装 voice package、指定语音不可用时不静默换语音。

Settings 新增 `jarvis.motion.low.v1` 的 Low motion feature。启用后只将 Core elapsed-time 推进缩放为 0.18，RAF、可见性与 Pause 生命周期不变，因此 Core 仍持续旋转；页面过渡继续尊重 reduced-motion。两版 Electron 的 syntax/static/Node contract tests 与 Windows speech focused tests（3/3）已通过；Impeccable detector 因缺少 HTML parser modules 降级为 regex，报告既有 aphoristic-copy warnings 与 grid-background advisory。真实 Windows voice list/audio 与 shortcut 观察仍待普通用户运行时验收。详情见 [Windows voice packages and Low motion feature record](prompts/feature/20260913-FEAT-electron-windows-voice-packages-and-low-motion.md)。

## 2026-09-13 — Collapsible Pages Navigation and Overlay Inspector (IMPLEMENTED — source/static verified; runtime pending)

开发版与内测版的 Pages 默认收起为紧凑 icon；点击后展开完整入口，并保持每行 5 个图标与单行标签。选择页面后，详情 inspector 覆盖原 Pages 区域，标题栏保留 Pages toggle，用户可直接重新展开导航切换页面。Pages 浮层下移 12px，详情高度扣除该偏移并保留 24px 底部安全间距；收起/展开使用 opacity/transform/filter 过渡并尊重 reduced-motion。未改变路由、Core/API、权限、持久化、confirmation 或 fallback 语义。

两份 edition 的 renderer syntax/static checks 已通过；Impeccable detector 因缺少 HTML parser modules 降级为 regex 扫描，只报告既有 `aphoristic-cadence` 文案提示。真实 Electron 窗口仍需重新加载 shortcut 后验收，未写成 runtime VERIFIED。详情见
docs/prompts/feature/20260913-FEAT-collapsible-pages-overlay-navigation.md。

## 2026-09-13 — Align Pages Card and Add Page/History Transitions (IMPLEMENTED — source/static verified; runtime pending)

开发版与内测版的 Pages launcher 改为每行 5 个图标，页面短名称保持单行；下方 inspector 与 launcher
保持同宽，并按导航卡高度预留 viewport 空间，长内容继续在圆角 card 内滚动。Pages 切换使用可中断、
尊重 Low motion/系统 reduced-motion 的淡入位移；History 的 `Open chat` 在等待 Core 结果时提供行级反馈，
成功恢复 transcript 后再播放一次受限过渡，失败不会离开 History。未改变路由、Core/API、权限、持久化、
confirmation 或 fallback 语义。

两份 edition 的 renderer syntax/static checks 已通过；Impeccable detector 因缺少 HTML parser modules
降级为 regex 扫描，只报告既有 `aphoristic-cadence` 文案提示。受限 host 的 Electron GPU/cache
加载阻断仍在，未将本轮改动写成真实窗口 runtime VERIFIED。详情见
docs/prompts/feature/20260913-FEAT-electron-page-and-chat-transitions.md。

## 2026-09-13 — Add Electron Core Connection Page (IMPLEMENTED — source/static verified; runtime pending)

开发版与内测版新增 Pages → Core 页面，提供运行时 Refresh 与 Reconnect Core。Refresh 只检查固定
127.0.0.1:8765/api/health；Reconnect 通过新的固定 IPC 复用现有 CoreSupervisor.ensureReady()，
ready listener 直接复用，端口离线时只启动当前 edition 持有的 Core child。非 ready 端口占用、缺少
runtime、启动失败或超时保持明确错误，不杀未知进程、不发消息、不创建替代 conversation，也不增加
inference probe、fallback 或权限范围。

Core 页现在显示最近一次 health check 时间，并把两个操作按钮移到说明文字下方的独立操作行，便于
确认页面是否仍在自动刷新，同时避免窄窗口挤压说明文字。

两份 edition 的 syntax/static checks 已覆盖 Core 页面、allowlist、main/preload bridge 与 --verify
页面存在性；本次真实 Electron verify 先因已有 shortcut 持有 single-instance lock（Windows code 5）未产生
verification snapshot，使用隔离临时 user-data profile 重试又因 GPU child exit `-1073741515` 返回
`ERR_FAILED`。未关闭正常 shortcut，因此没有把桌面操作写成 runtime VERIFIED。详情见
docs/prompts/feature/20260913-FEAT-electron-core-connection-page.md。

## 2026-09-13 — Fresh Chat Launch and Optional Electron Runtime Lifecycle (IMPLEMENTED — source/static verified; runtime pending)

Electron 开发版与内测版现在每次启动都从新的 active chat 开始；只有 Pages → History → `Open chat` 会显式恢复已保存对话，
`Start new chat` 清除当前选择。Settings 新增默认关闭的 `Run in background` 与 `Start on login`：前者关闭窗口时隐藏并保留同一
Electron/Core child，重新打开同一 shortcut 通过单实例聚焦原窗口；后者使用 Windows login-item API。History card 同步扩大为圆角矩形，
`conversation-list` handler/版本不匹配显示简短可操作提示，完整错误仍保留在 Errors/status title。未改变 Core/API、AI、权限、pending
confirmation 或 fallback 语义。

两份 edition 的 `node --test test/*.cjs` 文件级验证各 40/40（含 38 个 Node contract/model 测试用例、composer-focus 与 static verifier）及 syntax check 通过；Windows shortcut、登录项、隐藏/重新聚焦和 fresh-launch
行为仍待普通用户运行时验收，未将受限环境的源代码检查写成桌面 VERIFIED。受限 `npm run verify` 仍被 Electron
`crashpad_client_win.cc:869 not connected` 阻断，未加入 GPU/profile workaround。

## 2026-09-13 — Local Chat Persistence and History Chat (IMPLEMENTED — source/static verified; runtime pending)

Core 现在按 opaque conversation ID 将 terminal chat turns、脱敏后的 terminal Tool Results 与 response timing 写入本地
`data/memory/conversation.json`；TaskManager 将 terminal records 写入 `data/memory/task-history.json`，Core 重启时
未完成 task 只明确标为 `interrupted`，不会恢复或重发。Electron 开发版与内测版新增 Pages → History，可列出并打开
指定 chat；每次重开窗口从新的 active chat 开始，只有 History 的 `Open chat` 或 `Start new chat` 才显式选择会话，移除按日历日自动轮换。Events、Errors
与 terminal Tool Results 也按 edition 写入 renderer localStorage。`pending confirmation`、active work、凭据和未知结果
不落盘/不自动执行；明确失败、拒绝和验证阻断结果保留为对应的非成功终态。固定 bridge、权限、Luna、mapping、session_busy 与 no-fallback 语义保持不变。

两份 Electron Node suites 各 37/37、syntax check 与 `git diff --check` 通过；使用隔离 Python runtime 的
Codex adapter、AI connection、memory 与 task persistence focused tests 共 47/47 通过。
`tests.test_api_fast_replies`
仍因该 runtime 未安装 `fastapi` 而无法导入，未宣称 API 回归通过。真实 shortcut 重开与 History 视觉验收仍待普通用户环境。
本轮 Electron `--verify` 在受限 host 重现既有 GPU child/cache ACL/`ERR_FAILED (-2)` 阻断；内测版本地 npm script
虽缺少可解析的 `electron` executable，但用共享主运行时加 `--edition=internal-test` 也复现同一阻断。没有用
GPU flag、fallback 或重写 shortcut 掩盖该失败。

详情见 [Local chat persistence and History Chat feature record](prompts/feature/20260913-FEAT-local-chat-persistence-and-history.md) 和
[Storage overview](info/04-storage/STORAGE_OVERVIEW.md)。

## 2026-09-13 — Tune Electron Pages Card Spacing and Rounded Surfaces (IMPLEMENTED — source/static verified)

统一 Pages inspector 的内容留白与 section 间距，扩大 header/content 内边距；launcher 与 inspector 保持横向矩形并使用 18px 圆角，内部 instrument、tool result、task/settings list、empty/code surface 使用一致的圆角。路由、页面 allowlist、Core bridge 和权限语义不变。

详情见 [Pages card spacing and rounded surfaces bugfix record](prompts/bugfix/20260913-FIX-electron-pages-card-spacing.md)。

## 2026-09-13 — Widen Electron Pages Launcher Labels (IMPLEMENTED — source/static verified)

扩大 Pages 浮动 card 的响应式宽度（桌面 380px、窄窗口 360/340px），并将页面短名称保持为单行；Settings、Knowledge 等标签不再因六列网格宽度不足而折行。开发版与内测版保持相同布局，页面路由、allowlist、Core bridge 与权限语义不变。

详情见 [Pages launcher width and single-line labels bugfix record](prompts/bugfix/20260913-FIX-electron-pages-label-wrap.md)。

## 2026-09-13 — Expand Electron Pages Launcher Labels (IMPLEMENTED — source/static verified)

Pages 浮动 launcher 现在显示已有的页面短名称并在图标与名称之间保留清晰间距；按钮行高、网格行距和面板内边距同步增加，避免名称被裁剪或 hover tooltip 覆盖。开发版与内测版源码及静态/契约测试同步，路由、页面 allowlist、Core bridge 与权限语义不变。

详情见 [Pages launcher labels and spacing feature record](prompts/feature/20260913-FEAT-electron-pages-launcher-labels.md)。

## 2026-09-13 — Add Electron Obsidian Connect / Reconnect Controls (IMPLEMENTED — source/static verified)

Knowledge 页现在通过固定 Electron bridge 调用既有 Obsidian 注册 API：Refresh connection 检查实时注册状态，Connect / reconnect
要求用户输入 Vault 名称和完整文件夹路径，Disconnect 继续只移除 JARVIS 注册而不删除 Vault 文件。重连默认使用 `excluded`
访问级别，不扩大 RAG、Core 权限或路径扫描范围；开发版与内测版源码和 bridge/contract/static tests 已同步通过。

详情见 [Electron Obsidian connect/reconnect feature record](prompts/feature/20260913-FEAT-electron-obsidian-connect-reconnect.md)。

## 2026-09-13 — Hide Voice from Internal Test Edition (IMPLEMENTED — source/static verified)

内测版从 `internalTestPages` allowlist 移除 `voice`，因此导航入口隐藏且直接 `#voice` 路由回到 Assistant；开发版继续保留
Voice inspector。Settings 中的 Automatic speech、既有 Windows speech bridge、Core/API、权限和 shortcut 参数均不变。

详情见 [internal-test Voice visibility configuration record](prompts/configuration/20260913-CONFIG-hide-voice-internal-test.md)。

## 2026-09-13 — Prevent Electron Chat False 15-second Timeout (IMPLEMENTED — source/static verified)

修复 Electron Chat 将同步 `/api/chat` 请求按 15 秒截断的问题：`sendMessage` 现在使用明确的 65 秒
bounded timeout，与现有 AI transport 的 60 秒单次等待保持余量。Core online 后的自动 `aiCheck` 进行时，
普通发送会暂时禁用但输入草稿仍可编辑，避免与 Core 共享锁竞争；没有加入 retry、fallback 或 replacement
turn。开发版与内测版 bridge、renderer 和 contract/static tests 已同步通过。

详情见 [Electron Chat Core timeout FIX record](prompts/bugfix/20260913-FIX-electron-chat-core-timeout.md)。

## 2026-09-13 — Separate Events and Errors Pages (IMPLEMENTED — source/static verified)

开发版与内测版都将原 `Events & errors` inspector 拆成独立的 `Events` 和 `Errors` 页面。两页继续复用同一个
bounded renderer event store：Events 显示既有非 `error` lifecycle/recovery records，Errors 只显示既有 `error`
级别 failure；各自的清理按钮不会删除另一类记录。没有新增 Core/API endpoint、持久化、权限、错误翻译或 fallback。

详情见 [separate Events and Errors pages feature record](prompts/feature/20260913-FEAT-separate-events-errors-pages.md)。

## 2026-09-13 — Separate Memory and Knowledge Pages (IMPLEMENTED — source/static verified)

开发版与内测版都将原 `Memory & knowledge` inspector 拆成独立的 `Memory` 和 `Knowledge` 页面：前者只显示 Core conversation history，后者只显示 registered Obsidian vault metadata；刷新按钮与 Core operation 一一对应，未新增存储、扫描、RAG 或权限行为。

详情见 [separate Memory and Knowledge pages feature record](prompts/feature/20260913-FEAT-separate-memory-knowledge-pages.md)。

## 2026-09-13 — Keep Working Context in Development, Hide from Internal Test (IMPLEMENTED — source/static verified)

调整两个 Electron edition 的 Working context 边界：开发版保留页面与既有项目检查，内测版从页面 allowlist 移除该入口并拒绝 `#working-context` 路由。没有删除 Core project APIs、扫描权限或 shortcut 参数；未重新打开 shortcut。

详情见 [Working context edition configuration record](prompts/configuration/20260913-CONFIG-working-context-development-only.md)。

## 2026-09-13 — Distinguish Electron Edition Window Titles (IMPLEMENTED — source/static verified)

Electron 主进程现在按 edition 固定窗口标题：`JARVIS 开发版.lnk` 显示 `JARVIS · 开发版`，`JARVIS 内测版.lnk`（`--edition=internal-test`）显示 `JARVIS · 内测版`。同时拦截 renderer 的旧 HTML 标题，避免加载后覆盖版本标识；未修改 shortcut 参数、Core/API 或页面行为，也未重新打开 shortcut。

详情见 [Electron edition window title configuration record](prompts/configuration/20260913-CONFIG-electron-edition-window-titles.md)。

## 2026-09-13 — Internal Electron Copy and Shortcut (IMPLEMENTED — copy/shortcut verified)

新增 `electron_motion_preview_internal_test` 内测源码副本，并创建 `C:\Users\ongzh\Desktop\JARVIS 内测版.lnk`：工作目录指向副本，参数为 `. --edition=internal-test`；当时的版本策略允许 developer-only Working context 显示，后续已由上方配置调整为内测版隐藏。普通用户入口同步采用用户已改名的 `JARVIS 开发版.lnk`；现有普通版未被覆盖。副本排除重复 `node_modules`，复用同一 Electron runtime。

详情见 [internal Electron copy and shortcut record](prompts/configuration/20260913-CONFIG-internal-electron-shortcut-copy.md)。

## 2026-09-13 — Hide Working Context from Ordinary Users (IMPLEMENTED — source/static verified)

Working context 项目扫描与 Git/file/search inspector 最初标记为 developer-only：普通 shortcut 隐藏该 Pages 入口，直接 route 也回到 Assistant；该策略随后由最新 edition 配置 supersede，现改为开发版保留、内测版隐藏。没有删除 Core project APIs、改变扫描根目录或扩大权限。

详情见 [Working context visibility configuration record](prompts/configuration/20260913-CONFIG-hide-working-context-for-ordinary-users.md)。

## 2026-09-13 — Separate Electron Device and Working Context Pages (IMPLEMENTED — source/static verified)

Electron 将原来的 `Device & working context` 拆为 `Device` 与 `Working context` 两个页面：前者只显示本机只读系统信息，后者只显示 registered projects 和既有 Git/file/search inspection。页面 description 明确说明工作上下文不会自动附加到聊天，也没有新增数据读取或权限边界。

详情见 [separate Working context page feature record](prompts/feature/20260913-FEAT-separate-working-context-page.md)。

## 2026-09-13 — Preserve Direct Provider Selection During Health Poll (IMPLEMENTED — source/static verified)

修复 Electron AI connection 下拉框在约 2 秒 health poll 后从用户选择的 adapter 回到旧 OpenAI 的问题。原因是 renderer 无条件把旧 Core snapshot 写回未提交的 provider/model 表单；现在本地草稿优先，只有 Direct API 配置成功后才重新采用 Core 返回值。未修改 polling interval、Core/API、provider、权限、credentials 或 shortcut。

详情见 [Direct provider selection FIX record](prompts/bugfix/20260913-FIX-direct-provider-selection-reverted-by-health-poll.md)。

## 2026-09-13 — Electron AI Model Catalog and Token Usage Page (IMPLEMENTED — source/static verified)

Electron 将 AI Connections 和 Token Usage 拆成独立 Pages；Token Usage 继续明确 Core 尚未提供 account/quota/token telemetry。Direct API connection buttons 下方现在按 provider 列出 JARVIS text-only adapter 可提交的 model IDs：OpenAI GPT-5.6、Gemini Interactions、DeepSeek V4；每一项仍须用户发送请求才验证真实账号 access。OpenAI-compatible gateway 不显示虚构的固定 model list。未新增 API/telemetry request、付费 probe、Core transport 或 shortcut restart。

详情见 [AI model catalog and Token Usage feature record](prompts/feature/20260913-FEAT-electron-ai-model-catalog-and-token-usage-page.md)。

## 2026-09-13 — Electron AI Connection Spacing (IMPLEMENTED — source/static verified)

Electron AI Connection 的 Direct API input、等宽 Connect/Disconnect controls、status 与说明文字现有明确的垂直间距与行距；狭窄面板中按钮文字可换行且不会被裁切。此为 renderer-only layout 调整，未修改 Core、transport、credential 或用户 Desktop shortcut，也没有自动重启 Electron。

详情见 [AI connection spacing FIX record](prompts/bugfix/20260913-FIX-electron-ai-connection-spacing.md)。

## 2026-09-13 — Gemini, DeepSeek, and Compatible Gateway Direct Providers (IMPLEMENTED — source/static verified)

Direct API 现在可显式配置 OpenAI Responses、Google Gemini Interactions、DeepSeek Chat Completions，或一个用户提供的 HTTPS OpenAI-compatible Chat Completions gateway。provider/model/key 仍只存活在当前 Core memory；Direct 配置不执行付费探测，只有用户发送消息才会验证真实 access。Gemini/DeepSeek/gateway 均为 text-only、无 tools 的 adapter，失败不会切换 provider/model/transport。Gateway 只接受无凭据、无 query/fragment、非 local/private-IP 的 HTTPS base URL，并由 JARVIS 固定追加 `/chat/completions`。

Electron 的真实 AI 页面加入 provider、model、conditional gateway URL 与 key 配置控件，并继续通过固定 loopback IPC 调用唯一 Core endpoint；没有重开用户 shortcut 或用任何真实 key 进行 inference。17 项 Python targeted tests、Electron syntax/static/contract tests 已通过；真实账号/模型 access 待用户显式测试。

详情见 [Direct Provider feature record](prompts/feature/20260913-FEAT-direct-provider-gemini-deepseek-gateway.md)。

## 2026-09-12 — AI/Obsidian Disconnect Controls (IMPLEMENTED — runtime API verified)

加入 JARVIS 范围的 AI 断开/重连检查与 Obsidian 注册断开接口；断开不注销共享账号、不删除 vault 文件。临时 loopback Core 验证了 AI disconnect 成功，managed reconnect 返回真实 App Server unavailable 错误。
修复 Electron AI 页面将上述操作区放在 `unified.js` 后、导致 renderer 无法取得 DOM 控件的问题；现显示当前连接状态，并按 ChatGPT subscription / Direct API 呈现对应连接与断开操作。
订阅连接操作区改为同一行的等宽按钮，避免窄窗口下连接与断开按钮上下错位。
按钮文字现会在极窄空间内换行而不会裁切；同时已在真实 Core 验证 Direct API 与 ChatGPT subscription 双向切换及回切后的 managed reconnect。
修复用户点击 AI disconnect 后健康轮询自动重连的问题：Core snapshot 记录当前生命周期内的显式断开意图，只有用户主动 refresh、切换 mode 或输入 Direct API key 才可重新检查。
AI transport selector 不再在切换请求期间禁用；用户未配置 Direct API key 时仍可立即切回 ChatGPT subscription，较早请求不会覆盖最新选择。

## 2026-09-12 — Edition Pages Routing (IMPLEMENTED — static verified)

Development keeps all Pages; internal-test hides unfinished Pages and rejects their direct hash routes. Details: [edition Pages routing record](prompts/feature/20260912-FEAT-edition-pages-routing.md).

## 2026-09-12 — API Test Memory Import Scope Fix (IMPLEMENTED — isolated regression)

补充 `tests/test_api_fast_replies.py` 的 module-level `jarvis_memory` import，修复 clean Python 回归中的 `NameError`。
该变更是 45 项冻结源码之后的独立测试差异；114 项指定 Python tests 现已全部通过，未修改生产运行时。

详情见 [API test memory import scope FIX record](prompts/bugfix/20260912-FIX-api-test-memory-import-scope.md)。

## 2026-09-10 — Electron Obsolete Assistant Note Cleanup (IMPLEMENTED — source/static verified)

删除 Electron renderer 中两处指向已移除 `#assistant-note` 的无效 DOM 更新调用。
`setText`、Core 状态、聊天、Markdown、滚动、自动朗读、工具结果与安全边界均保持不变。
修改前已将未跟踪 renderer 保存到临时备份；`node --check`、`npm run verify:static` 与 34 个 Electron Node tests 全部通过。

详情见 [obsolete assistant-note FIX record](prompts/bugfix/20260910-FIX-electron-obsolete-assistant-note.md)。

## 2026-09-10 — Automatic AI Transport Check on Preview Open (IN PROGRESS — source/static verified)

Electron preview 在首次看到 Core ready 后自动调用固定 `POST /api/settings/ai/check`。
managed Luna 只建立或复用 JARVIS-owned App Server，并验证 initialize、managed login、exact
`gpt-5.6-luna` 与 `:read-only` profile；不创建 thread、不发送 turn、不做 inference probe。
Direct API 不自动发起付费请求，继续保持显式 `not_checked` 直到用户发送请求。检查阶段仅记录
opaque request id 与安全阶段耗时，不记录消息、账号、密钥或 token。Adapter/service/API/bridge
回归与 Electron static/contract tests 已通过；真实 managed account/window 仍需用户环境观察。

详情见 [Automatic AI Transport Check feature record](prompts/feature/20260910-FEAT-ai-transport-auto-check.md)。

## 2026-09-10 — Markdown Chat Output Rendering (IMPLEMENTED — source/static verified)

Chat 的 `DISPLAY` 回复现在保留并安全渲染 Markdown：标题、段落、逐行有序/无序列表、强调、引用、行内/围栏代码与受限链接不再连成单一文本块；常见的同一行递增编号项目也会拆成列表。Core 仍使用 `[DISPLAY]` + `[VOICE_EN]` 双区块；API 只规范换行，Automatic speech 继续消费独立的纯文本 narration。renderer 不使用 `innerHTML`，raw HTML 与不安全链接不会执行。
`node --check`、`npm run verify:static`、34 个 Electron Node tests 与 Python compile 通过；API 整组测试因当前环境缺少 `fastapi` 未能导入，普通 Electron runtime 仍受既有 GPU/cache stop rule 限制。

详情见 [Markdown chat output rendering FEAT record](prompts/feature/20260910-FEAT-markdown-chat-rendering.md)。

## 2026-09-10 — Electron Confirmation Tail and Speech Start Follow-up (IMPLEMENTED — source/static verified)

新回复与 `awaiting_confirmation` Yes/No 卡片会在两帧布局收敛后强制定位到 Chat 尾部，确保最新控件可见；用户手动阅读旧消息时仍保持位置，直到发起新的 turn。
确定性 native confirmation 现在把权限层的完整 `message` 同时用于显示与自动朗读，并以 turn 阶段区分 confirmation/reply，避免后续结果被同一 turn 去重吞掉。
Windows system speech 在播放前显式重置可寻址流到 offset 0 并调用 `Load()`，不再从非零位置开始。`node --check renderer/unified.js`、`npm run verify:static`、31 个 Electron Node tests、speech 单元测试与 Python compile 通过；API 整组测试仍受当前环境缺少 `fastapi` 阻断，普通 Electron runtime 仍受既有 GPU/cache stop rule 限制。

详情见 [Electron confirmation tail and speech start FIX record](prompts/bugfix/20260910-FIX-electron-confirmation-tail-and-speech-start.md)。

## 2026-09-10 — Native Intent Risk Routing and Google Classroom App Resolution (IMPLEMENTED — source/targeted tests)

Luna native-intent candidate 不再覆盖 `PermissionManager` 的风险 decision：low-risk 候选沿既有 allow path 执行，
medium/high-risk 候选继续进入 Yes/No confirmation。27 个 bounded fuzzy aliases 仍只是 proposal gate，不拥有选择或执行权。
修复中文 `打开`/`启动` 后不带空格时 resolver 直接失败的问题；当前 `config/apps.json` 已有 Google Classroom shortcut，
因此 `打开Google Classroom` 会进入既有 `open_app` registry/permission 路径。没有扩大 Desktop scan、shell 或任意路径执行。
49 个 native/router/adapter tests、compileall 与只读 registry lookup 通过；API 整组测试仍受当前环境缺少 `fastapi` 阻断，
没有把它标为全绿 runtime 验证。

详情见 [native intent risk routing and localized app-open FIX record](prompts/bugfix/20260910-FIX-native-intent-risk-routing-and-localized-app-open.md)。

## 2026-09-10 — Electron Confirmation Speech and Chat Tail Follow-up (IMPLEMENTED — source/static verified)

Automatic speech 开启后会朗读 `awaiting_confirmation` 的 user-facing prompt，沿用既有 stop/clear、generation 与 turn-ID 去重；
enqueue 仍在 assistant DOM 更新前同一响应任务内启动。Chat append 在 pending animation frame 的同步批次中保持底部跟随，
用户滚离底部时仍会取消定位并保留阅读位置；原生滚动继续可用且视觉 scrollbar 隐藏。
`npm run verify:static`、31 个 Electron Node tests、renderer syntax check 与 `git diff --check` 通过；普通 Electron runtime 未因既有
GPU/cache stop rule 重启。

详情见 [Electron confirmation speech and chat tail FIX record](prompts/bugfix/20260910-FIX-electron-confirmation-speech-and-chat-tail.md)。

## 2026-09-10 — Managed Luna Native-Intent Proposal Boundary (IMPLEMENTED — source/targeted tests)

managed `gpt-5.6-luna` 现在只在短本地操作请求上收到当前 27-tool catalog，并可在同一 text turn
返回可清理的 `[JARVIS_INTENT]` 候选；Core 复用既有 schema/敏感文件检查，TaskRouter 对候选额外
强制 Yes/No confirmation，模型从未获得 callable、shell、browser、MCP 或 plugin authority。
普通问答不增加 classifier turn；未知、畸形或低置信度候选显式不执行。47 个 native/router/adapter
回归与三个新增 API proposal tests 通过；整组 API 还有一个既有 `jarvis_memory` 未导入的
`NameError`，真实 Core/Luna 验收待重启。

详情见 [Luna native-intent proposal feature record](prompts/feature/20260910-FEAT-luna-native-intent-proposals.md)。

## 2026-09-10 — Native Shutdown Intent Aliases (IMPLEMENTED — source change)

补齐 `shutdown pc`、`shutdown the pc` 等明确关机表达，使其回到既有 native confirmation 路径；
没有让 Luna 直接调用 Windows 工具，也没有改变权限、按钮或模型 transport。resolver 回归已补充，
但当前受限 host 无法启动 Python 解释器，运行时测试仍待正常 Core 重启与安全的 `no → denied` 验收。

详情见 [native shutdown intent aliases bugfix record](prompts/bugfix/20260910-FIX-native-shutdown-intent-aliases.md)。

## 2026-09-10 — Electron Thinking Placeholder Copy (IMPLEMENTED — source/static verified)

真实 Core 返回前，Chat assistant placeholder 与中央 Core 的 `thinking` 说明统一显示 `Thinking…`，不再显示
`Waiting for a real Core response…`。现有阶段日志确认截图中的约 12.9 秒主要位于外部 Luna `turn_completion`，
本次只调整文案，不改变请求、模型、权限、计时或 fallback 语义。

详情见 [Electron thinking placeholder copy bugfix record](prompts/bugfix/20260910-FIX-electron-thinking-placeholder-copy.md)。

## 2026-09-10 — Chat Tool Result Surface (IMPLEMENTED — source/static verified)

Chat 不再追加 completed/failed/session_busy 等终态 Tool Result 卡片；完整结构化结果继续写入专用 Tool Results 页面。
待确认操作仍只在 Chat 保留 Yes/No 控件，assistant 回复、denied 反馈、Core routing/permission、自动朗读与
bridge contract 均未改变。`node --check renderer/unified.js`、`npm run verify:static` 与 `git diff --check` 通过；
没有新增 fallback、模型/工具权限或 API 改动。

## 2026-09-09 — Resident Luna App Server and Phase Timing (IMPLEMENTED — scoped runtime verified)

managed `gpt-5.6-luna` 现在由 `CodexAppServerAdapter` 在 Core 生命周期内按需启动并复用同一 adapter-owned
App Server child、JSON-RPC session、temporary CWD 与已验证 initialize/account/model/read-only profile 状态；
后续请求只执行既有 thread start/resume 与 turn start，不重复握手。内部 lifecycle lock 保证并发初始化单一
owner，stdout/stderr 持续 drain；Core shutdown、mode boundary、child/protocol/auth/permission failure 和
timeout 会清理或失效 resident 状态，未知 turn 结果不自动重发，`session_busy` 不创建 replacement thread。
响应与 `[JARVIS_TIMING]` 日志仅包含 opaque request id、safe 阶段毫秒数、generation、复用标记和不可观测的
`first_token_ms: null`，不记录消息、token、账号或密钥。API 增加最小 shutdown hook 与 safe timing metadata
透传；没有 startup AI probe、streaming、model/provider/reasoning/permission/UI/SQLite 改动。

适配器 27 项定向测试、AI connection 4 项与 API timing/shutdown 测试通过；全套 134 项中唯一失败是既有
`test_direct_api_mode_does_not_receive_or_write_managed_thread_context` 的测试自身缺少 `jarvis_memory` 导入，
不是本包引入。临时 8767 Core 的同一测试 conversation 三次 `tell`（现有 managed subscription）实际测得：
cold HTTP 8063.6ms / adapter total 8050.9ms（spawn 21.3ms、initialize 168.0ms、model 1248.7ms、turn completion
6428.1ms）；warm-1 2239.1ms / total 2225.3ms、warm-2 1813.6ms / total 1806.8ms，两次均 generation 1、
`transport_reused=true`。这证明握手/child 已复用，但外部 turn completion 仍是主要耗时；不代表绝对 SLA 或首 token，
8765 原有旧 Core 未被重启。

详情见 [Resident Luna Transport and Phase Timing feature record](prompts/feature/20260909-FEAT-resident-luna-transport-and-phase-timing.md)。

## 2026-09-09 — Electron Confirmation Actions and Denied Reply (IN PROGRESS — source/static verified)

Chat 中的 pending confirmation 现在只显示 `Yes, continue` / `No, cancel` 两个按钮；完整 awaiting JSON
继续保留在 Tool Results 页面。用户选择 `No` 后，原 turn 的 assistant reply 保持可见，Chat 不再重复追加 denied
JSON 卡片。Core confirmation、权限、session_busy、自动朗读与 bridge contract 均未改变。

详情见 [Electron confirmation actions and denied reply bugfix record](prompts/bugfix/20260909-FIX-electron-confirmation-actions-and-denied-reply.md)。

## 2026-09-09 — Electron Settings Persistence and Panel Activity (IN PROGRESS — source/static verified)

Settings 新增浮窗自动关闭选择（5/10/25/30/60 秒或 Never），选择保存在本地 preview profile；Pages/inspector 的点击、键盘和内容滚动
都会重新计算倒计时。Automatic speech 仍默认关闭，但用户开启后会持久化开关状态，重开窗口恢复设置且不会重播历史回复；关闭仍停止当前
Windows system speech 并清空队列。AI `not_checked` 语义保持真实：Core health 不主动探测 AI，首次真实请求后才报告 transport 结果，未加入伪造状态或隐式 prewarm。
`npm run verify:static`、Node syntax、Core contract checks 已通过；普通 Electron runtime 仍受既有 GPU/cache stop rule 约束。

详情见 [Electron Settings Persistence and Panel Activity feature record](prompts/feature/20260909-FEAT-electron-settings-persistence-and-panel-activity.md)。

## 2026-09-09 — Electron Existing Core Surface Integration (IN PROGRESS — source/contract verified)

新版 Electron preview 已通过固定 loopback bridge 接入现有 Core 的 conversation history、TaskManager records、system info、
project registry/Git/files/read/search/refresh、Obsidian vault metadata、Windows speech settings 与 AI transport selection。
Tasks、Tools、Device/Context、AI、Memory/Knowledge、Voice、Events 页面不再用静态成功/default/sample 值；失败会显示 explicit
unavailable，ToolResult 与 confirmation 仍由 Core 路由和权限边界决定。新增 `GET /api/tasks` 只读投影现有进程内 TaskManager，
没有新建持久化或 scheduler。未实现的 SQLite memory、STT、wake、automation、handoff 等继续标为 PLANNED/demo；没有读取或回显
credentials，没有 direct renderer HTTP、GPU workaround、打包或 Git publish。`npm run verify:static`、Core contract 13/13 与 Node
syntax checks 通过；当前受限 host 的 Electron GPU/cache `0xC0000135`/`ERR_FAILED` stop rule 仍阻断正常 runtime 验证。

详情见 [Electron Existing Surface Integration feature record](prompts/feature/20260909-FEAT-electron-existing-surface-integration.md)。

## 2026-09-09 — Electron System Monitor Telemetry Bridge (IMPLEMENTED — source/contract verified)

Electron preview 的 System Monitor 不再使用静态 CPU/GPU/Memory 示例读数。新增固定的 `telemetry` Core bridge operation，复用既有
`GET /api/telemetry`，由 `main.cjs`/`preload.cjs` 暴露给 renderer；卡片每 2 秒更新真实快照，缺失指标显示 `—`，GPU 不可用时显示
`LIVE · GPU UNAVAILABLE`，Core/网络失败显示 `UNAVAILABLE`。没有新增 OS 命令、数据库、fallback、GPU workaround 或未来能力；其他 Pages
仍保持 demo/unconnected。`npm run verify:static`、`node --test test/core-contract.cjs`（10/10）与 Node syntax checks 通过；当前受限 host 的
`npm run verify` 仍在 renderer 加载前被既有 GPU child `-1073741515`、cache access denied `(0x5)` 与 `ERR_FAILED (-2)` 阻断，按 stop rule 未继续 runtime launch。

## 2026-09-09 — Electron Memory & Knowledge Pages Merge and Theme Page (IN PROGRESS)

Electron preview 的 Pages launcher 将 Memory 与 Knowledge 合并为单一 `Memory & knowledge` inspector，并新增独立的
`Theme` page。既有 `Amber Core`、`Cyan Circuit`、`Violet Pulse`、`Matrix Green` 选择器从 Settings 移到 Theme page，
Settings 只保留日期语言与默认关闭的 Automatic speech；没有改变 Core/API、Flutter、权限、存储或 GPU 诊断边界。
源码、静态契约、相关 Node tests 与静态浏览器页面检查通过；普通 Electron runtime 仍受此前记录的 managed-host GPU/cache stop rule 约束。

详情见 [Electron Pages Memory & Knowledge Merge and Theme Page feature record](prompts/feature/20260909-FEAT-electron-pages-memory-knowledge-theme.md)。

## 2026-09-09 — Electron Chat Scroll Anchor and Hidden Scrollbar (IN PROGRESS)

Chat 保留原生滚轮/触控板/键盘滚动，但隐藏主滚动条。新增可取消的单帧底部跟随：用户滚离底部时不再被异步回复强制拉回，
assistant 长回复更新也会在仍贴近底部时正确跟随，减少滚动撕裂与无法滚到底的现象。未改变 Core/API、conversation store、主题或安全边界。
源码、静态契约与静态浏览器 computed-style 检查通过；普通 Electron runtime 仍受既有 managed-host GPU/cache stop rule 约束。

详情见 [Electron Chat Scroll Anchor and Hidden Scrollbar bugfix record](prompts/bugfix/20260909-FIX-electron-chat-scroll-anchor.md)。

## 2026-09-09 — Voice Failure Feedback Deferred (PLANNED)

按用户要求，将语音模式的失败播报、系统固定提示和显式降级策略留待语音输入/唤醒阶段定义；当前自动朗读范围不变，未派发实现。
详见 [Voice Failure Feedback](prompts/plan/20260909-PLAN-voice-failure-feedback.md)。

## 2026-09-09 — Electron Speech Sync and Theme Presets (IN PROGRESS)

Electron preview 的 Automatic speech 现在在同一响应任务内、assistant DOM 更新前立即调用既有固定 Windows speech bridge，
移除了 renderer 自身的额外 microtask 排队；文字仍立即写入，Windows system voice 的进程/合成启动时间仍保持真实可见边界。
Settings 新增本地持久化主题预设：`Amber Core`（默认）、`Cyan Circuit`、`Violet Pulse`、`Matrix Green`；surface、accent、状态色和
WebGL Core shader palette 会一起切换。没有加入 browser `speechSynthesis`、手动朗读按钮、provider fallback、GPU workaround 或 Core/API 改动。
相关 Node/static checks 已通过；当前 managed host 的 `npm run verify` 在 renderer 前因 GPU 子进程
`exitCode=-1073741515`、Chromium cache `拒绝访问 (0x5)` 和最终 `ERR_FAILED (-2)` 停止；按 GPU stop rule 未加入 workaround、未打包、未继续 `npx electron .`。

详情见 [Electron Speech Sync and Theme Presets feature record](prompts/feature/20260909-FEAT-electron-speech-sync-and-theme-presets.md)。

## 2026-09-09 — Electron Settings and Automatic Speech Replies (IN PROGRESS)

Electron preview 的 Pages launcher 现在包含 Settings inspector，可选择 Chat 日期的 `en-US`/`zh-CN` 格式，
并提供默认关闭的 Automatic speech 开关。开启后只朗读随后新完成的回复，按 turn ID 去重并顺序播放；关闭时停止当前
Windows system speech、清空待播放队列。语音失败在 Settings 中显式显示，文字回复不受影响。此次需求覆盖上一轮逐条
`Read reply`/手动播放要求，preview 不添加消息级朗读按钮；不使用浏览器 `speechSynthesis`、其他 provider、fallback 或 GPU workaround。
`auto-speech.cjs`、Core speech contract 和 `npm run verify:static` 已通过；完整 Electron/audio runtime 观察仍待普通用户环境，
没有运行打包流程。

详情见 [Electron Settings and Automatic Speech Replies feature record](prompts/feature/20260909-FEAT-electron-settings-auto-speech.md)。

## 2026-09-09 — Electron Composer Focus and Compact Transcript FIX (IN PROGRESS)

Electron Assistant composer 现在保留普通 Enter 的 submit guards，并在 IME composition Enter 时阻止发送；请求进行中
只禁用 send action，input 仍可编辑下一条草稿。应用窗口内的 `Ctrl+L` 在 modal 未打开时聚焦 composer、保留 draft
并将 caret 放到末尾，没有异步响应抢回焦点。Transcript 改为 user 右侧紧凑块、JARVIS 左侧较小 brand logo，长 user
文本在块内左对齐换行，移除每条消息的全宽 separator；turn、ToolResult、confirmation、chronology 和滚动语义不变。
`composer-focus.cjs`、Node syntax 与 `npm run verify:static` 已通过；真实 Electron 焦点/视觉观察仍待普通用户/99 QA，
没有重新触发既有 GPU stop rule、加入 workaround/fallback 或打包 EXE。该记录中的 Settings/TTS 仍是当时范围外；
后续独立 feature 已在上方记录。

详情见 [composer focus and compact transcript FIX record](prompts/bugfix/20260909-FIX-electron-composer-focus-and-compact-messages.md)。

## 2026-09-09 — Electron Compact Core Workspace Layout (IN PROGRESS)

90 Integration 正在将新版 Electron preview 改为无 sidebar 的 floating-window workspace：主窗口只保留中央 WebGL
JARVIS core，左侧 chat pane 变成独立小窗口，右上 page launcher 与局部 inspector 变成独立小浮窗；支持
Escape、键盘焦点与 reduced-motion。chat card 已移除冗余标题和手动 New conversation 控件，内部内容密度约缩至
80%（包括输入框/发送按钮）；inspector 从 launcher 下方带淡入位移动画展开，Pages 图标 hover/focus 显示页面名，
chat/core/page header 不绘制额外横向分隔线；打开 inspector 后 5 秒无指针/键盘操作自动收回，交互会重新计时；Low motion 默认关闭但仍可手动开启，系统 reduced-motion 监听保留；hologram 内层与桥接线回到外层 shell 的共同原点，避免 Core 中心视觉偏左。renderer 按本地日历日刷新前台 conversation view（保留同一 opaque conversation ID；发送中、待确认或 Core offline 时延后），
在该布局记录创建时，日期默认使用 `en-US` 英文短格式且尚未包含独立 Settings 面板；随后由上方
Electron Settings feature record 增加受限 locale 切换与自动朗读开关。
并在失败时保留原会话、显示明确错误，不新增后台 chat。实时本地时间/日期和低对比琥珀 instrument background 已接入；所有未接线
页面仍明确 sample/planned。未修改 Core/API storage、权限、routing、Target、Flutter 或打包流程；真实
1366×768/大桌面截图验收待用户/99 QA。
System monitor 已从 Pages 和大型 inspector 页面移除，改为 Chat 卡片正下方左侧 card stack 中的紧凑卡片，仅显示
CPU、GPU、Memory 静态示例读数，并标注 `LOCAL SAMPLE · NO TELEMETRY`；chat 原有的 Core/AI/Connection/Model `RUNTIME` 也并入
同一卡片，不新增真实 telemetry 或额外页面。UI 明确分为中央 Core 基础层与 chat/monitor/Pages 第二浮动层，Chat 与 Pages
共用按左侧 Chat+monitor 卡片组总高度动态计算、再略向上偏移 24px（矮窗口 16px）的垂直居中顶部锚点（正常最小 52px、矮窗口最小 40px），Chat 高度缩短为 470px（矮窗口 400px），monitor 与 Chat 同宽并在其下方排列，不遮挡 Core 或右侧 Pages inspector；删除浮窗后方的 Core header 与底部说明文字。
Pages 展开 inspector card 改为 viewport-aware、最大 580px 并保留底部留白，长内容继续在卡片内滚动。

详情见 [compact workspace layout record](prompts/feature/20260909-FEAT-electron-compact-core-workspace-layout.md)。

## 2026-09-09 — Electron Chat Identity and Response Time (VERIFIED — scoped renderer)

新版 Electron preview 的 user 消息不再显示头像，assistant 消息复用现有 JARVIS brand logo；每次实际
 Core 请求完成或显式失败会显示一位小数的 `Response time`。这只是 renderer presentation 变更，Core、
AI、权限、ToolResult、确认流程和刷新边界不变；静态验证与普通用户视觉复核均已通过。启动时 AI 预热仍未实现。

详情见 [chat identity/response-time feature record](prompts/feature/20260909-FEAT-electron-chat-identity-response-time.md)。

## 2026-09-09 — Electron Tool Result Disclosure and AI Status Timing (VERIFIED — scoped renderer)

终态 Tool Result 改为原生 `<details>` dropdown，默认收起完整 JSON；`awaiting_confirmation` 保持展开以显示
Yes/No 控件。renderer health 仍每 2 秒轮询；30 秒只是 Core supervisor 冷启动上限，不是 AI 连接的固定等待。
`/api/health` 不主动探测推理后端，因此 `ai.status=not_checked` 保持真实语义。未修改 Core/API、AI transport、
权限或确认协议；普通用户重启窗口后的视觉复核已确认。启动时 AI 预热仍未实现，`not_checked` 继续表示尚未发起真实 AI 请求。

详情见 [Tool Result/AI status feature record](prompts/feature/20260909-FEAT-tool-result-disclosure-and-ai-status.md)。

## 2026-09-09 — Electron Availability and Core Startup FIX (IN PROGRESS)

修复新版 Electron preview 的可用性闭环：断开 Core 时 composer 仍可编辑草稿，但发送按钮与提交动作
明确受阻，Core/AI 状态行的指示灯不再把 disconnected 显示成绿色。新版快捷方式生成脚本会写入明确的
项目内 `electron.exe` target；normal launch 由 main process 只检查 `127.0.0.1:8765/api/health`，无
listener 时以固定 shell-free 参数启动并持有现有 Core API，非 ready 占用、缺少 Python、启动失败或
超时均可见且不杀未知进程。新增 supervisor 回归覆盖 ready reuse、cold start、port conflict、child
failure、timeout、cold-start race 与精确 child cleanup；20/20 Node tests 与 `verify:static` 通过。当前 Codex 受限
host 启动 `.venv` 返回 Windows `拒绝访问`，普通用户桌面启动/离线草稿/原生确认仍待 99 QA；没有
加入 GPU flag/fallback、Luna、SQLite、Flutter 或 refresh transcript persistence。详情见
[availability FIX record](prompts/bugfix/20260909-FIX-electron-availability-and-core-startup.md)。
根目录 `.gitignore` 同步补齐 `node_modules/`、`out/` 与 `release/`，避免未来纳入未跟踪 preview 时带入生成物。

## 2026-09-09 — Electron Conversation Message List FIX (IN PROGRESS)

修复 Electron Assistant transcript 的 turn ownership：每轮 user message 与 assistant placeholder/result
按 `data-turn-id` 追加，ToolResult/原生 confirmation controls 保留在所属 turn；失败、拒绝、
`awaiting_confirmation`、非显式 completed 和 stale epoch response 不再覆盖或污染其他回合。新增
renderer-local `ConversationStore`、底部感知滚动和 focused 6-case Node regression（含三轮、长消息、
批准后失败重试、拒绝、重复确认与新会话隔离）；`npm run verify:static` 与 syntax checks 通过。
刷新仍不会恢复正文：当前 bridge 只持久化 opaque conversation ID，后端 `/api/chat/history` 未暴露且
不是 per-conversation UI restore contract。真实 Electron 多轮/滚动/确认窗口观察仍受既有 GPU loader
停止规则阻断，未接入 SQLite、未改 Core/Target、未打包或 push。详情见
[conversation-list FIX record](prompts/bugfix/20260909-FIX-electron-conversation-message-list.md)。

## 2026-09-09 — Electron Core Foreground Integration (IN PROGRESS)

90 added a bounded Electron test-client bridge for the existing Core: a sandboxed preload exposes only
fixed health/session/chat operations to `127.0.0.1:8765`; the renderer persists an opaque conversation ID,
separates Core and AI status, sends real `/api/chat` text, and renders structured ToolResult/confirmation
states without treating pending, denied, failed, or `session_busy` as success. `ChatRequest.conversation_id`
now matches the existing opaque-ID client contract. Static checks and the seven-case Node bridge contract suite
passed. Current restricted-host `npm run verify` remains blocked by the pre-existing Electron GPU child
`0xC0000135`/cache access failure followed by `ERR_FAILED`; no GPU workaround, fallback, profile override,
packaging, or UI runtime claim was added. The existing opaque `ChatRequest` field mapping was checked;
TaskRouter/permission/native-intent regression suites
passed (29/29); the combined API suite has one unrelated existing `NameError` in its test body. Details:
[M3a record](prompts/feature/20260909-FEAT-electron-core-foreground-integration.md).

## 2026-09-09 — Electron Preview Desktop Shortcut

新增用户桌面快捷方式 `JARVIS - New UI Preview (Test).lnk`，直接启动项目内 Electron 39.8.10 preview，
参数为 `.`、工作目录为 `electron_motion_preview`；实际窗口、GPU child、sandboxed renderer、退出和无异常
目录均已验证。原确认的 Flutter 快捷方式 `JARVIS.lnk` 仅改名为 `JARVIS - Legacy UI.lnk`，其 launcher
目标、参数和 Release 图标保持不变，描述已标记为 `Legacy UI / 旧版 UI`。`create-desktop-shortcut.ps1`
以后生成带 Legacy 标识的 Flutter 入口；README 与
Current Info/Obsidian 已同步。新版仍是独立 `PROPOSED · UI CONCEPT`/demo，不连接 Core/AI/API/telemetry，
不代表正式 UI 替换；未打包 EXE、未改 Target、未接入其他项目。

## 2026-09-09 — Electron Preview Residual Cleanup

在用户批准的精确清单内，删除 `electron_motion_preview/Microsoft/Spelling/neutral`、其空父目录
`Microsoft/Spelling` 与 `Microsoft`，以及两个空乱码目录 `Ƞ젊Ǐ`（`0220 C80A 01CF`）和
`Ꞑ�ǭ`（`A790 DFED 01ED`）。删除前确认所有路径位于 preview 内、不是 reparse point、没有文件，也没有
源码/配置/Git 引用；删除后目标不存在，受保护 source/config/renderer/test 文件 hash 未变化。未触碰
`node_modules`、package files、AppData profile/cache、其他项目或截图；未使用递归删除。乱码目录的历史
创建者仍未确认，packaging/EXE 未运行。

## 2026-09-09 — Ordinary-User Electron Shell Boundary Verified

最新只读复测以普通 Windows 用户 `ONGZHENGAN\\ongzh` 运行，`adminRole=False`；无参数 `npm run verify` 返回
0，输出 `verification: passed`、`webglActive: true`、`canvasSize: [1152, 662]`，并通过 navigation、
pause、low-motion 与 renderer isolation 检查。随后 `npx electron .` 显示窗口标题 `JARVIS · proposed desktop UI`，
确认独立 GPU child 和 `--enable-sandbox` renderer，进程已关闭。运行前后 `Microsoft/Spelling/neutral`、
`Ƞ젊Ǐ`、`Ꞑ�ǭ` 的精确目录集合未变化，没有新乱码目录；这些历史残留的创建者仍未确认。该实验以普通用户
运行验证为完成边界，未打包 EXE，且 packaging 不构成完成条件；没有新增源码 workaround、GPU flag、fallback、
权限修改或系统级变更。

## 2026-09-09 — Electron WebGL Shell Real-Environment Verification

profile workaround 清理后的受限 sandbox 失败保留为诊断历史；在获批的真实/elevated 环境单次执行
`npm run verify` 通过，输出 `verification: passed`、`webglActive: true`、`canvasSize: [1152, 662]`。
随后单次 `npx electron .` 正常启动，窗口标题为 `JARVIS · proposed desktop UI`，并确认独立 GPU child
与 sandboxed renderer。`npm run verify:static` 继续通过；未重新加入 profile/GPU workaround、GPU flags 或
fallback，未打包 EXE，未修改 JARVIS 主项目其他模块。Electron preview `.gitignore` 补充 `out/`、
`release/` 与 `*.log`，为后续纳入 Git 做边界准备。

## 2026-09-09 — Electron Host Boundary Investigation

记录 profile 清理后的单次受控失败：当前 Codex sandbox 身份对默认 Electron profile 只有读取权限，解释了
cache access denied；GPU child `0xC0000135` 按 Windows 定义属于 DLL/manifest loader dependency failure，
但静态检查未证明 Electron 包内直接缺失文件。该次记录当时未更改权限、驱动或系统 runtime，未重新加入
profile/GPU workaround；后续普通用户复测结果见本文件顶部，未运行打包。

## 2026-09-09 — Remove GPU Diagnosis Profile Override

移除 Electron shell 中仅用于 GPU/cache 诊断的 per-process `userData/sessionData` 临时 profile，保留
Electron 安全配置、CSP、renderer isolation、`--verify`、显式非零退出和 GPU child 日志。用户此前在获批
安装 Electron 后确认真实环境 `npm run verify`、`webglActive: true` 与可见动画窗口；移除 workaround 后，
当前宿主再次验证触发 `0xC0000135` GPU child、cache access denied、GPU cache creation failure 和
`ERR_FAILED`。未加入 GPU flags/fallback；独立 `npm run verify:static` 随后通过，但普通启动与 EXE
未执行，runtime 验证仍按停止条件待处理。

## 2026-09-09 — Electron WebGL Shell Validation Blocked

新增隔离的 `electron_motion_preview/` 技术验证壳，直接复用 11 原型的本地 HTML/CSS/JS/WebGL 资源，
加入 CSP、sandbox、context isolation、无 Node renderer、权限/导航/弹窗/webview 拒绝和静态验证。
Node syntax/static checks 已通过；npm 缓存权限与主机 usage gate 阻断 Electron 安装，因此没有虚报
runtime、WebGL、EXE、进程生命周期或视觉验收。未改 Flutter 主桌面、Core/API、Target、数据或原型源。

详情见 [Electron validation record](prompts/feature/20260908-FEAT-electron-webgl-shell-validation.md)。

## 2026-09-08 — Isolated Flutter Core Motion Preview

新增 desktop-only `CustomPainter` preview target，模拟黑金投影网络球壳、同心环、轨道粒子、光晕及四种
visual states。它不接入 Assistant/Core/API/telemetry；low-motion、pause、lifecycle 和 dispose 均有测试。
全量 Flutter 36 tests、analyze 与 Windows build 通过。Release process 有本地 CPU/memory 样本，但当前
automation 不能捕获 native window，视觉 screenshot/user comparison 仍待确认；未改 Target、未 merge/commit/push。
见 [FEAT record](prompts/feature/20260908-FEAT-flutter-core-motion-preview.md)。

## 2026-09-08 — Bounded Agent Direction Recorded

按用户要求记录多步Agent目标体验、Core逐步验证、受控重试/停止/预算及前置契约。Native优先，工程handoff仍须授权；不采用无依据每日token目标或新状态体系。仅计划与导航，无实现/任务派发；Obsidian未同步。见 [PLAN](prompts/plan/20260908-PLAN-bounded-agent.md)。

## 2026-09-07 — Contract Readiness Principles Adopted

按用户要求将合适原则转成既有C1–C5的编码前决策及测试门禁，明确retry粒度、显式降级和工程handoff授权边界。仅计划与导航四文件变更，未改Target/M0原契约/源码、未派发任务；Obsidian未同步。见 [PLAN](prompts/plan/20260907-PLAN-contract-readiness.md)。

## 2026-09-07 — Foundations Scope Refinement

按用户要求仅保留合适的轻量底座；复杂系统不再列为延期待办，知识管理不强制完整状态机或confidence数值。仅修改计划与本时间线，不派发任务、不改源码/Target。见 [PLAN](prompts/plan/20260907-PLAN-engineering-foundations.md)。

## 2026-09-07 — Engineering Foundations Plan

筛选用户架构加强建议，将八类底座纳入既有M1.2–M9门禁与owner；区分敏感级别与保留策略、复用双health语义、加入恢复演练与预算约束，暂缓企业级平台。仅计划/导航四文件修改，不改Target/源码、不派发任务、不push；Obsidian本轮未同步。见 [PLAN](prompts/plan/20260907-PLAN-engineering-foundations.md)。

## 2026-09-07 — Desktop Error Report / 收工前错误记录

按用户要求仅记录截图：ObsidianVaultPanel 的 `Null check operator used on a null value` 与另一条折叠的 `Tool failed`。尚未调查或修复，不派发任务；今日停止。详情见 [待处理记录](prompts/bugfix/20260907-FIX-desktop-errors-pending.md)。

## 2026-09-07 — Luna Dual Connection and Hidden App Server Window

90 接线 user-selected Direct OpenAI API 或 managed ChatGPT subscription App Server 的 exact
`gpt-5.6-luna` text transport；Core health 与 AI status 分离，Direct key 只在当前 Core memory 且
输入不等于已验证。没有 fallback/context migration，pending confirmation 阻止 mode change。修复
Windows `codex.cmd` 每回合显示 cmd child：adapter 现在创建隐藏子进程。Python 42、Flutter 34 和
analyze 通过；真实 Direct paid API 和重启后无 cmd window 的桌面人工验收仍待用户执行。

详情见 [FEAT record](prompts/feature/20260907-FEAT-luna-dual-connection.md)。

## 2026-09-07 — Luna Active-Writer Conflict

90 将 owned Luna thread 的明确 active-writer/thread-store conflict 归一为 `session_busy`，提示
用户先处理另一 Codex client，并保证不创建 replacement chat。Python 44、Flutter 32 和 Dart
analyze 通过；用户重开 shortcut 后得到 READY completed 且 ChatGPT sidebar 无新 chat，确认 transport
不暴露为可人工占用的 UI chat，故不强制进行 hidden-thread multi-client 操作。未改模型、权限、工具、
Memory/SQLite、RAG、后台或 project binding。

详情见 [FIX record](prompts/bugfix/20260907-FIX-luna-active-writer-conflict.md)。

## 2026-09-07 — Session Isolation Work Package

90 实现 JARVIS conversation 到 owned App Server transport thread 的持久映射；同一会话使用
`thread/resume`，认证/owner/version 不符显式失败而不静默新建。当前 Core 三次连续回复及重启后
续聊均通过。指定 ChatGPT 云端 Jarvis Chat project 在本机 App Server 返回 `project not found`，
因此未伪装绑定、未创建本地替代项目。用户 Release/Codex UI 已验收 ONE、TWO、THREE 位于同一
chat，后两条没有新增 sidebar chat。未改模型、权限、
SQLite/RAG/worker/历史聊天，也未 merge/commit/push。

详情见 [实现记录](prompts/feature/20260907-FEAT-session-isolation.md) 与 [PLAN](prompts/plan/20260907-PLAN-session-isolation.md)。

## 2026-09-07 — Subscription Desktop Chat QA / 订阅桌面对话验收

90 与用户交付 VERIFIED：Luna 文本回复及 `sleep the computer` 的原生确认按钮已通过桌面验收；拒绝提交 `no`，真实显示 `awaiting_confirmation → denied`，未执行睡眠。交接报告 Flutter 31 passed、analyze/Windows Release build 通过、Core 路由回归 50 passed；00 未重跑这些测试或独立检查截图。仓库实现记录与 Current State 已读取核对，Obsidian 同步由 90 报告。后台认知、前后台并发、持久化及完整 M3 不在本次 VERIFIED 范围。无 merge/commit/push。

详情见 [实现记录](prompts/feature/20260906-FEAT-codex-subscription-desktop-chat.md) 与 [00 汇总记录](prompts/documentation/20260907-DOCS-subscription-chat-acceptance.md)。

## 2026-09-06 — Codex Subscription Chat Authorization

记录用户批准的 ChatGPT 订阅登录方向与 90 限定接入工作包，替代暂停的 API-key 迁移。先同步 Target/Obsidian，再验证桌面对话；控制/执行和工程授权边界不放宽。仅计划与导航修改，接入尚未实现，镜像同步尚待 90 执行，无源码修改或 push。

详情见 [PLAN record](prompts/plan/20260906-PLAN-codex-subscription-chat.md)。

## 2026-09-06 — M1.1 Truthful Tool Results and Task Bookkeeping

将未知工具、原生异常、外部 callback 异常和无效返回变为显式失败；确认等待
使用 `success: null` 与 `waiting_approval`，拒绝记录为 `denied`，批准后的
异常不再遗留 `running`。同时修复 Gemini 外层把本地确认误标为 Tool failed 的
结果传播，以及 Flutter 将预期 `denied` 误写入 Errors 的分类。93 Python、30
Flutter 测试和 Flutter 静态分析通过；Release 重建、Core health 已验证。Luna、
SQLite、Target、真实数据、merge/push 均未变更。

99 QA 桌面验收：重建 Release 显示 `awaiting_confirmation → denied`，Core
Connected，拒绝未产生 Tool failed/Error 记录。

详情见 [FIX record](prompts/bugfix/20260906-FIX-m11-truthful-tool-results.md)。

## 2026-09-06 — Delivery Order Update / 顺序调整

同步运行基线恢复记录：90已报告VERIFIED；当前下一步M1.1，随后提前交付M3a Luna最小桌面对话。完整SQLite/Memory不阻塞该文本闭环；工具/RAG开放仍受安全门禁约束。仅文档同步，无本轮源码修改或Git push。

详情见 [PLAN record](prompts/plan/20260906-PLAN-runtime-luna-order.md)。

## 2026-09-06 — Core Runtime Baseline Recovery / Core 运行基线恢复

恢复现有 Python 3.14.6 venv 基础解释器并验证 loopback health 与只读系统信息。
修复 Core/Flutter health 的 routing mode 契约；发现并清理 stale Release
binary。开启 Windows Developer Mode 后，Release 重建、launcher 启动、Core
health、桌面 Connected 和桌面只读系统信息结果均通过。未改 Target、数据库、
权限或模型接线；M1.1 仍未开始。

详情见 [FIX record](prompts/bugfix/20260906-FIX-core-runtime-baseline.md)。

## 2026-09-06 — Module Planning / 模块规划

按现行工程规则定稿结构重整方式、未完成清单、Phase A–C范围、分模块开任务指令与并行门禁；同步现有Obsidian Plans/Records。未实施模块代码。

详情见 [PLAN record](prompts/plan/20260906-PLAN-module-development.md)。

## 2026-09-06 — Documentation Migration / 文档迁移

采用用户附件作为项目 AGENTS，补齐实现文档地图与基线说明，同步既有 Obsidian Current/Components/Records，标记旧工作树能力差异。无业务源码、依赖或数据库变化。

详细范围与验证见 [DOCS record](prompts/documentation/20260906-DOCS-obsidian-structure-migration.md)。
# 2026-09-12

- **FIX**: 修复 Electron AI connection 控件同步函数的意外自递归。此前 renderer 初始化会在实际 Core 状态被渲染前抛出栈溢出，使正常已启动的 Core 长期显示为 `Checking Core`。
- **UI**: Core 在线后自动触发现有 AI 连接检查，避免启动时长期显示 `not_checked`；Direct API 仍保持显式验证。
