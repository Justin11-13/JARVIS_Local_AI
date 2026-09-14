# Current State / 当前能力

System Status includes an explicit Windows Battery Class detail path, and the Electron Device page now reads the structured `/api/system-status` endpoint for battery capacity/cycle display.

Status: CURRENT, source/mock/static/bridge-contract verified; ordinary-user Electron/Python runtime acceptance remains pending. Baseline main@07df06f92c3a90eb2fa2dc2bd42cc76271e7d21f, 2026-09-13.

已核对源码入口：Flutter/FastAPI、受限 Codex App Server Luna 文本 transport、有界原生工具 110 项（含 Audio 7 项、Brightness 4 项、Wallpaper 2 项、Windows OS Theme 2 项与 System Status 6 项，以及 App/Power/Window/Files/Clipboard/Network/Bluetooth/Audio Device/Media/Keyboard-Mouse controls）、项目/Git/文件只读工具、Obsidian 5 项工具、JSON conversation/task history、RAG、telemetry、Windows/Fish TTS。`services/tool_catalog.py` 现在是 provider-neutral tool metadata SSOT；Gemini declarations、API required/optional schemas 与 managed-GPT intent catalog 从它派生，`app/main.py` 仍是执行 registry。System Status 的 Battery 同时保留 `psutil` 基础状态与 Windows Battery Class 详细容量/循环读取，Electron Device 通过 structured system-status endpoint 展示这些字段。
Audio、Brightness、Wallpaper、Windows OS Theme 与 System Status 的源码、registry、permission、model schema、bounded native-intent routing、structured result boundary 与 mock tests 已加入；此前一批次又完成 App Control、Power、Window Management、Files、Clipboard、Network、Bluetooth、Audio Devices、Media 与 Keyboard/Mouse 的同一边界接入，并记录 focused `156/156`、全量 `294/294`。本次 canonical tool catalog refactor 新增 `tests/test_tool_catalog.py`，相关 regression 为 `62/62`，当前全量 `python -m unittest discover -s tests` 执行 `299` tests，其中 `291` passed、`8` 个既有 output-language/locale mock contract failures（不在本次 refactor touched lines），changed modules/tests 的 `py_compile` 通过，registry/API schema/native-intent/Gemini/catalog/intent parity 为 `110/110/110/110/110/110` 且无重复 declaration。最终测试使用可正常启动的 Python 3.12.14 verification venv；checkout-local Python 3.14.6 `.venv` 因 Windows Access Denied 无法启动，不作为验证证据。只读 Windows Battery Class probe 在当前环境未发现 readable system battery device，因此 live capacity/cycle values 仍待普通用户 Windows acceptance；Bluetooth per-device connection、audio default-device selection、current-media metadata 与真实 input/window/device behavior 的 Windows acceptance 也仍待普通用户环境。现有 JARVIS local visual theme presets 与 Windows OS Theme 保持分离。
参考 [架构与限制](../02-architecture/ARCHITECTURE_OVERVIEW.md) 和 [模块接口](../03-modules/MODULE_INVENTORY.md)。

Flutter 另有一个 desktop-only、isolated 的 `core_motion_preview.dart` CustomPainter 研究入口；它不在
主 Assistant/navigation tree 中，不调用 Core/model/tool/telemetry。它的 source、widget test 与 Windows
build 已验证，但 native-window visual comparison/screenshot 仍待用户确认，因此不能作为整页 UI 已验收或
真实系统状态的证据。

另有 `electron_motion_preview/` 的 experimental Electron shell，复制 11 原型的真实
`motion.html`、`unified.css`、`unified.js`、`hologram.js`，并保持本地-only WebGL、navigation、Pause/Low
motion 与 renderer isolation 边界。用户获批 Electron install script 后安装了 Electron 39.8.10，并移除了
仅用于 GPU/cache 诊断的 per-process `userData/sessionData` override；受限 Codex sandbox 的一次对照运行以
`0xC0000135` 退出，伴随 cache access denied、GPU cache creation failure 与 `ERR_FAILED` 页面加载，该失败
保留为诊断历史且没有通过代码 workaround 掩盖。
最新普通用户验收以 `ONGZHENGAN\\ongzh` 运行（`adminRole=False`）：无参数 `npm run verify` 返回 0，
输出 `verification: passed`、`webglActive: true`、`canvasSize: [1152, 662]`，并通过 tasks navigation、
 pause、low-motion 与 renderer Node isolation 检查；同一普通用户此前的 `npx electron .` 窗口曾显示
`JARVIS · proposed desktop UI`，存在独立 GPU child 和 `--enable-sandbox` renderer，随后已关闭进程。
现在主进程按 edition 将窗口标题映射为开发版/内测版；该映射已通过 source/static checks，两个 shortcut 的
新标题仍待用户下次实际打开确认。当前
shell runtime 已在普通环境验证，未加入 GPU flag/fallback；Electron 自身的两条 GPU state diagnostic 未使
验证失败。此前实验记录中的“EXE 未打包”状态已被本次 Internal Test 完整安装器实现取代；当前 Codex 受限运行身份为
`ONGZHENGAN\\codexsandboxonline`，默认 Electron profile 位于 `%APPDATA%\\jarvis-electron-motion-preview`，
对 `CodexSandboxUsers` 只有读取权限；这解释了受限运行中的 cache `拒绝访问`，不应通过修改 JARVIS 代码解决。
此前根目录曾有 `Microsoft/Spelling/neutral`、`Ƞ젊Ǐ`、`Ꞑ�ǭ` 三个空的诊断残留；在逐项确认路径位于
preview、无 reparse point、无内容、无源码/配置/Git 引用后，已按用户批准精准删除，连同空的
`Microsoft/Spelling` 父目录一并移除。历史 packager 曾因乱码路径 `ENOENT` 失败，但当前源码没有写入路径，
具体创建者仍未确认；删除不代表已定位来源。
后续复核还发现一个另命名的空残留 `electron_motion_preview/▐␹ǌ/Microsoft/Spelling/neutral`；它不在已批准
删除清单内，本次未删除，不能宣称 preview 下所有历史诊断目录均已清空。

当前桌面入口已明确分开：`JARVIS 开发版.lnk` 位于用户 Desktop，目标为
`electron_motion_preview/node_modules/electron/dist/electron.exe`，工作目录为
`electron_motion_preview`、参数为 `.`，窗口标题为 `JARVIS · 开发版`；`JARVIS 内测版.lnk` 指向独立的
`electron_motion_preview_internal_test` 副本并带 `--edition=internal-test`，窗口标题为 `JARVIS · 内测版`。
开发版保留 Working context 页面；内测版不在页面 allowlist 中，按钮隐藏且直接 `#working-context` 路由回到 Assistant。
此前读取到的开发版 link
`create-desktop-shortcut.ps1` 与 `create-internal-test-shortcut.ps1` 现会校验并修复这两个已命名入口。原确认的 Flutter
快捷方式已改名为 `JARVIS - Legacy UI.lnk`，仍保留 `app.desktop_launcher`、Release build、Core/API
与现有功能测试入口。新版 Electron 入口仍是实验性 UI，但启动时由 main process 检查真实 Core health，
仅在无 listener 时启动现有 `uvicorn app.api:app`，不打开 Flutter、不杀未知端口占用；这不是正式 UI
替换或 Target Architecture 决策。两个入口均由用户明确保留；内测版仅用于开发验证。

### Internal Test packaged Windows installer / 内测版完整 Windows 安装器

Status: IMPLEMENTED — final local package and packaged content verified; newly generated unsigned Core/Electron runtime launch is blocked by Windows Application Control on this host; clean-machine installer acceptance remains pending.

`electron_motion_preview_internal_test/` now builds a complete x64 NSIS installer rather than an Electron-only shell.
PyInstaller produces the Core `onedir` runtime, Electron Builder places it at
`resources/core/jarvis-core.exe`, and NSIS uses `oneClick=false` with
`allowToChangeInstallationDirectory=true`, so the user can choose the install directory. The final local artifact is
`electron_motion_preview_internal_test/release/JARVIS-Internal-Test-0.1.0-Setup.exe` (816,647,011 bytes in the current build,
SHA-256 `3501645D93FF9A73402998488A0BA4D90E470F919F8563CCA4501FD17E4EE8B3`).
The package also includes the Windows x64 native Codex CLI App Server at
`resources/core/codex/codex.exe`; users do not need to install Node.js, npm or Codex CLI separately. The user's ChatGPT/Codex
login remains user-owned and is not embedded in the installer.
The static verifier and Node suite (`64/64`) passed, and the packed `app.asar` contains the update checker, preload
bridge, and update-notice UI markers. A live check against the fixed GitHub Releases API returned the explicit
`not_published` status for current version `0.1.0`; no update was claimed. The final generated unsigned Core and
Electron binaries could not be launched on this host because Windows Application Control blocked them; no policy
bypass was attempted. The installer itself has not yet been installed under a separate clean Windows account, so
the destination chooser and clean-machine pass remain pending.
Read-only package resources and safe default registries are bundled; `.env`, credentials, current-machine config/data,
Obsidian Vault contents and personal project/app paths are excluded. Mutable state is written to
`%LOCALAPPDATA%\JARVIS\InternalTest`.

The packaged Internal Test client now has an explicit update-notice flow. Its Electron main process checks the fixed
GitHub Releases API once after startup and exposes a manual `Settings → Application updates → Check now` action
through a narrow preload bridge. Only a newer published Release carrying a matching
`JARVIS-Internal-Test-<version>-Setup.exe` asset produces the Chat header `UPDATE AVAILABLE` notice; the user then
chooses `Download update` to open the validated Release page. Network failures, missing releases and unsupported
development/source runs remain visible statuses; no silent download, install or restart is performed.

### Electron foreground Core client / Electron 前台 Core 测试入口

`electron_motion_preview/` 现在包含一个仍属测试入口的 bounded foreground client：sandboxed
preload 只暴露固定的 Core-backed operations，覆盖 `health`、`telemetry`、conversation list/open/history/session/chat、
system info、projects/Git/files/search/refresh、Obsidian vault metadata、TaskManager records、AI mode 选择，
以及 `speechSettings`、`speechVoices`、`speakReply`、`stopSpeech`。主进程只请求
`127.0.0.1:8765` 的固定 API path；normal launch 先由
`core-supervisor.cjs` 复用 ready Core，或用固定 shell-free 参数启动并持有现有 API child，失败/超时/
非 ready 占用均以可见错误结束；`--verify` 只做 WebGL/renderer 检查而不要求 Core。renderer 不直接访问
网络；它保存 edition-scoped Events/Errors/terminal Tool Results，并保存当前 active conversation ID 供当前
窗口与显式 History open 使用，但新启动不会读取该 ID；完整 terminal transcript 由 Core 写入本地 JSON。
Core `ready` 与 `/api/health.ai` 状态分开显示。既有 Core 继续拥有
routing、native execution、PermissionRequest/Decision 和 ToolResult truth；Electron 只显示
`completed`、`awaiting_confirmation`、`denied`、`failed`、`session_busy` 等结构化结果，不能直接
执行工具或把 pending/error 变成成功。

`app/api.py` 的 `ChatRequest` 已声明与 Flutter 已使用的 `conversation_id` 相同的 opaque-ID 校验；`GET /api/tasks`
只读投影 `TaskManager.list_tasks()`，terminal task records 写入 `data/memory/task-history.json`，重启时未完成项只标为
`interrupted`，不会自动恢复。Electron Pages 的 Tasks、Tool Results、
 Core connection、Device/Context、AI Connections、Memory/Knowledge、Voice、Events 与 Errors 现在通过固定 bridge 显示 Core/API
结果或显式 unavailable；Both Electron editions' Voice pages initialize local voice state before listing Windows OneCore voice packages, store the selection, and support Test voice.
项目 Git/files/read/search 与 registry rescan 均由用户触发并保持 Core 边界。
没有改变 routing、permission、Luna transport 或 task semantics。Electron 仍保留严格 CSP、
`nodeIntegration: false`、`contextIsolation: true`、`sandbox: true`、默认 web security、导航/弹窗/
webview/权限拒绝和 GPU child 日志。System monitor 现在通过固定 bridge 读取既有 `/api/telemetry`；
已存在 API 的 renderer 页面显示真实结果或 explicit unavailable，Automation/Handoff 等无现有实现的页面仍明确是 PLANNED/demo。
Token Usage 同时提供 Feature inspector 页面和中央 Core stage 顶部、与 Chat/Feature 共用 `--floating-top` 锚点的独立 compact widget preview；widget 现在只展示
JARVIS 自己的 provider-reported Input/Output/Total 三项 k/M compact summary，宽度约 360px 且没有关闭按钮，不显示 heatmap 或 trend chart；Core canvas 使用独立的
垂直居中区域，不被顶部浮层布局推偏，也不提供内部 scrollbar。Widget 只读取 edition-scoped `jarvis.foreground.token-usage.v1.{edition}` response records，
因此不会把用户在 Codex 客户端里的其他 usage 混入。Managed Luna 从固定 App Server `thread/tokenUsage/updated` 读取 JARVIS-owned ephemeral thread 的
explicit cumulative totals，按 turn 计算 delta 后写入同一 provider record；Direct API 继续从每次 provider response 读取明确 usage。Managed ChatGPT 通过固定
`/api/settings/ai/usage` → App Server `account/usage/read` 另外提供账号级 summary/daily buckets，renderer 以 edition-scoped localStorage 单独持久化，并只在显式
Feature Usage 页面刷新和展示；14-day SVG trend 仍包含轻量 X-axis
日期 ticks、Y-axis token scale labels，以及每个已绘制 point 的 hover/focus tooltip（k/M compact value）。Direct API 则继续从每次 provider response 的明确
input/output/total usage DTO 实时写入 provider store；Feature 页面按当前连接类型选择对应来源，不混加或估算缺失字段。Managed account 的 unavailable/disconnected/stale 与 Direct API 的
not_supported/account-RPC 状态都保持显式，绝不读取或推导 quota/billing。

Electron Assistant 的当前窗口 transcript 由 renderer-local `ConversationStore` 按 turn 追加：每轮的
user message、assistant placeholder/result、ToolResult 与 confirmation controls 都带有自己的 turn
identity；真实 Core 返回前的 assistant placeholder 显示 `Thinking…`，不代表请求已完成。失败、拒绝、等待确认和晚到的旧 epoch response 不会更新其他 turn。普通历史阅读不会被强制拉回，
但新 user turn、真实回复/显式失败和 confirmation controls 会自动跟随到最新内容。每次 terminal response 由
`JarvisMemory` 按 opaque conversation ID 写入 `data/memory/conversation.json`；`GET /api/chat/conversations`
列出摘要，`POST /api/chat/history/open` 读取指定已保存 chat。每次重开 Electron 窗口都从空 active view
开始；Pages → History 的 `Open chat` 才能显式恢复旧 chat，`Start new chat` 显式开始新的 ID。不会按日历日自动创建新 chat。`awaiting_confirmation` 不写入
Core JSON，也不从 renderer localStorage 恢复；confirmation 必须在当前运行中结束。`/api/chat/history` 仍在独立
Memory 页面显示 primary 兼容视图；独立 Knowledge 页面显示注册的 Obsidian vault metadata，并提供显式
Refresh connection、Connect / reconnect 与 Disconnect 控制。独立 Core connection 页面提供
Refresh（只请求固定 /api/health）和 Reconnect Core（复用现有 CoreSupervisor；ready listener 直接复用，
端口离线时只启动当前 shortcut 持有的 Core child）；非 ready listener、启动失败或超时仍以明确错误显示，
不会杀未知进程、发消息或创建新 conversation。页面会显示最近一次 health check，并保持 2 秒自动轮询；按钮位于说明文字下方的独立操作行。该页可在 Core offline 时打开，便于执行重连。

消息身份显示：user 行不再渲染头像；assistant 行复用侧栏现有 JARVIS logo。每次真实 Core 请求完成或
显式失败后，assistant 行显示 measured `Response time X.Xs`；离线草稿拦截不伪造耗时。Core 文本回复继续遵守
`[DISPLAY]` 后跟选定输出语言正文、`[VOICE_EN]` 后跟简洁英文 narration 的双区块协议；API 的 `ChatRequest.output_language` 默认是
`en`，可显式使用 `zh-CN`；API 拆分为 `reply`/`speech`，
renderer 不显示协议标签。DISPLAY 允许安全 Markdown（标题、段落、逐行列表、强调、引用、代码块与受限链接）；
renderer 也会将顺序递增的同一行编号项目拆成有序列表，
由 renderer-local DOM subset 渲染；raw HTML 与不安全链接只作为文字显示。VOICE_EN 仍是纯文本 narration，
不会朗读 Markdown 标记。
Tool Result 记录现在只在专用 Tool Results 页面显示，Chat 不再追加 completed/failed/session_busy 等终态
审计卡片；`awaiting_confirmation` 在 Chat 中只显示 Yes/No 控件，完整 JSON 仅保留在 Tool Results 页面；denied
终态在 Chat 中保留 assistant 回复而不重复追加 denied JSON。健康状态前端每 2 秒轮询；Core 冷启动的
30 秒是 supervisor 的有界上限，不是 AI 连接的固定等待。`/api/health` 仍不主动联系推理后端；
首次看到 Core online 时 renderer 通过固定 `POST /api/settings/ai/check` 自动触发一次 managed
transport verification，不创建 thread/turn，也不发 inference probe。Direct API 没有无推理检查端点，
保持显式 `not_checked` 直到用户发送请求。AI status 不会被 UI 伪造为 available。
`core-bridge.cjs` 对 `sendMessage` 使用明确的 65000ms bounded timeout，以覆盖现有 60 秒 AI
transport 等待；其他快速 Core surface 仍使用 15000ms 默认值。自动 `aiCheck` 在进行时只禁用普通
消息发送，输入框仍可编辑并保留草稿，避免 `/api/chat` 与 Core 共享锁竞争；timeout/transport failure
仍显式显示且不会自动重发结果未知的 turn。

当前 composer 的普通 Enter 继续走既有 submit guards；IME composition Enter 不会发送。请求进行中只禁用
 send action，input 仍可编辑并保留下一条草稿；自动 AI check 期间同样只禁用 send action；pending
 confirmation/offline/重复发送边界不变。仅限应用窗口
 的 `Ctrl+L` 在 modal 未打开时聚焦 composer、保留草稿并把 caret 放到末尾；没有异步响应路径会主动抢回焦点。
Transcript presentation 进一步压缩：user message 右侧紧凑块、JARVIS message 左侧较小 logo，长 user 文本在块内
 左对齐换行，消息行不再绘制全宽 separator；turn ownership、chronology、ToolResult/confirmation 和历史滚动
保持不变。该 composer/message refinement 当前 source 与 static checks 已通过，真实 Electron 焦点/视觉观察仍待
普通用户/99 QA，不应写成 runtime `VERIFIED`。

Chat `#messages` 保留唯一的原生纵向滚动容器并隐藏视觉 scrollbar；普通 append 仍尊重用户滚离底部的阅读位置，
但新的 user turn、真实回复/显式失败和 confirmation controls 会使用可取消的两帧 tail settle 强制显示最新内容，避免 Yes/No
卡片落在可视区外或异步布局造成滚动撕裂。

Electron preview 当前另有一个 90 Integration 的 floating-window workspace layout（IN PROGRESS）：主窗口只
保留中央 WebGL core；左侧 chat pane 改成独立的小浮动窗口，右上 page launcher 与 Tasks/Tools/AI 等
改成独立 inspector 小浮窗，不再把任何 sidebar 栏位写入 shell。Pages 默认只显示紧凑 toggle icon，点击后以 5 列
网格展开；选择页面时 inspector 覆盖 Pages 区域，详情标题栏保留 Pages toggle，避免导航长期遮挡 Core；打开后 5 秒
没有指针或键盘操作会自动关闭，交互会重新计时；Pages 图标 hover/focus 会显示页面名称。
  chat/core/page header 不绘制额外横向分隔线，输入框与发送按钮也按约 80% 密度缩放；composer input 使用可收缩的 zero-basis flex，hint 在窄宽度会省略，send action 保持固定触控宽度。
  Chat message body 与 Markdown paragraph 允许在气泡内换行，不再用单行 intrinsic width 撑开窗口；Core stage、core-space 与 canvas 也明确保持 `min-width: 0`/`max-width: 100%`。
  Settings 的 Low motion 仍默认关闭，只有本地明确保存 `true` 才启用；选择后以 `jarvis.motion.low.v1` 持久化并减慢 Core elapsed-time 推进，但不停止 RAF 或 Core rotation。
  系统 `prefers-reduced-motion` 样式与监听仍作为独立 accessibility override 保留。Feature launcher 展开和页面选择分别使用
  `feature-nav-enter`/`feature-page-enter`，并在重复进入前取消实际 CSS animation、强制建立新的样式边界；rapid switch 会取消旧动画。Pages launcher 现在提供 Settings inspector：日期默认显示英文 `en-US` 短格式，
  可通过受限的 `jarvis.clock.locale.v1` 切换 `zh-CN`；独立的 Response language 默认使用 English，Settings 可在 English/中文之间切换，
  选择以 `jarvis.response.language.v1` 保存在 renderer 本地并只影响之后发送的新回复，不翻译既有历史；浮窗自动关闭可在 Settings 选择 5/10/25/30/60 秒或 Never，点击、键盘与面板滚动都会重新计时。
  Automatic speech 默认关闭；用户开启后通过 `jarvis.auto-speech.enabled.v1` 在本地 preview profile 持久化，重开窗口恢复开关但不重播旧消息；both editions' Voice pages use
  `GET /api/system-speech/voices` to list Windows OneCore voice packages and store the selected voice ID in `jarvis.auto-speech.voice.v1`.
  Test voice is available before sending;
  朗读随后新完成的回复及 awaiting-confirmation prompt，关闭会停止当前 Windows system speech 并清空队列。preview 不提供逐条 `Read reply`/手动播放按钮；朗读失败在 Settings 显示，
  文字回复保持不变。speech enqueue 现在在 assistant DOM 更新前于同一响应任务内调用固定 bridge，并以 turn 阶段区分 confirmation/reply；
  native confirmation 使用权限层完整提示文本。Windows system voice 在 `Load()` 前将可寻址合成流重置到 offset 0，进程/合成启动耗时仍由现有 TTS service 决定，
  不宣称完全零延迟。
  Automatic speech 现在由 renderer 在本地按回复文字检测 Han/Latin 比例；中文回复优先使用用户已选的中文 voice，
  否则选择已安装列表中第一个 `zh-CN`、再选择其它 `zh-*` voice，英文和其它文字继续使用当前选择或 Windows default。
  每个 streamed response 在第一个可见文字出现时固定一个 voice ID，所有后续 speech chunks 复用它；voice inventory 在 Core ready 后后台读取，
  不增加 Luna/Core inference 请求，也不阻塞 chat request。没有中文 voice 时保留当前选择并记录显式提示，不静默声称已使用中文包。
  Streaming chat（IMPLEMENTED — source/static/mock verified; normal provider/Windows audio runtime pending）：两版 Electron 通过固定
  `/api/chat/stream` 接收 `start`/`delta`/`complete`/`error` NDJSON 事件，renderer 在模型 delta 到达时更新当前 assistant turn；
  `StreamProjector` 隐藏 `[DISPLAY]`/`[VOICE_EN]` 协议 marker，`DisplayPacer` 默认以约 42 chars/s、50ms tick 受控揭示
  burst response；这是 renderer-only presentation pacing，不降低 Core/provider/TTS 生成速度，terminal DOM 会在 visual target
  drain 后再替换，避免完整内容一闪切换。开启 Automatic speech 后，`SpeechChunker` 从已显示 response text 在 72–240 字符窗口内选择最后一个句子边界产出
  batched provisional speech chunk；逗号与冒号不会单独触发 TTS，terminal `[VOICE_EN]` 仍是 canonical response narration，但不会在已消费或已暂存的 display speech 后重复播放（短回复的 final flush 也只保留一份）；队列只让
  current/next 进入合成与播放，其余文本保留为最多 8 项、不会阻塞文字流的待处理队列。TTS synthesis 返回 WAV 后由 renderer 按序播放；
  synthesis/playback failure 只显示为明确 speech error，不改变文字结果。Automatic speech Off 时不会调用 synthesis；新消息会立即停止本地
  Audio、清空 speech queue、取消旧 Core stream，并让 managed adapter 尝试 interrupt 当前 turn，迟到事件按 request generation 丢弃。
  每个 streamed turn 记录 `requestReceivedAt`、`firstModelTokenAt`、`firstTextRenderedAt`、`firstSpeechChunkCreatedAt`、
  `firstTtsAudioReadyAt`、`firstAudioPlaybackAt`、`responseCompletedAt` 及其 derived latency fields；当前只完成 source/static/mock
  验证，没有把真实 provider、Windows WAV 或 Electron 普通窗口延迟写成已测量数值。`totalResponseMs` 仍记录实际 stream
  completion，不包含 presentation pacing drain。2026-09-13 follow-up FIX 已将 managed Luna adapter 的流式生命周期锁
  从线程所有权绑定的 `RLock` 改为可跨 Starlette worker thread 恢复/关闭的 primitive `Lock`，并通过跨线程完成 stream
  的 Python regression 验证；Core 重启后仍需由用户重测完整 stream、自动朗读和 Windows WAV 播放。
  Settings 另外提供 `Run in background` 与 `Start on login` 两个默认关闭的 Electron runtime 开关。前者关闭窗口时隐藏并保留同一
  JARVIS-owned Core child，再次打开同一 shortcut 会聚焦原窗口；后者通过 Windows login-item API 设置开机启动。两项配置分别按
  development/internal-test edition 保存在 Electron `userData`，读取、写入或 OS API 失败会显示为明确 unavailable，不改用替代路径。
hologram 内层与桥接线使用与外层 shell 相同的原点，保持 Core 几何中心对齐。Pages 将 Memory 与 Knowledge 分成独立
`Memory` 与 `Knowledge` inspector；Memory 只显示 conversation history，Knowledge 只显示注册的 Obsidian metadata；新增 `Theme` inspector 作为视觉预设唯一入口。
Pages launcher 默认收起为紧凑 icon；展开后固定为每行 5 个图标，让每个可见图标在下方显示已有的页面短名称，并用更高的按钮行、网格间距与响应式 card 宽度保持标签单行且不被裁剪。选择页面后 inspector 在同一 Pages 区域覆盖 launcher，详情标题栏的 Pages toggle 可重新展开导航；launcher、inspector 与内部内容卡片使用横向矩形比例、统一留白和圆角。Rounded card surfaces 现在使用独立绘制边界；Pages 外框切换保留 opacity/位移动画，但不再用 blur 或 fractional scale 二次采样，以改善 Windows DPI 下的 border 清晰度；切换页面时 inspector header 与内容分别使用 `page-header-enter`/`page-view-enter` 做短暂的淡入、18px 横向到位与 bounded blur，并可在下一次切换时中断。这只改变呈现，不改变页面路由、edition allowlist 或 inspector 行为。
Theme page 复用本地持久化的 `Amber Core`、`Cyan Circuit`、`Violet Pulse` 与 `Matrix Green` 主题，CSS surface/accent/status
与 Core shader palette 同步变化；当前两套 edition 另提供 background、surface、border、accent、text、muted、Core A/Core B 八项
custom palette controls，输入即时映射到既有 CSS tokens、保存到 edition-local storage，并可 Reset 回当前 preset。Settings 还提供默认关闭的
Electron background/start-on-login lifecycle controls，均不改变 Core/AI、权限或 bridge 语义。
背景使用低对比主题 instrument 元素。
当前 managed host 的 `npm run verify` 在 renderer 加载前仍会遇到 GPU 子进程 `exitCode=-1073741515`、Chromium cache
`拒绝访问 (0x5)` 与 `ERR_FAILED (-2)`；这属于环境验证阻断，未加入 GPU workaround/fallback，也未进行打包。
System monitor 不再占用 Pages 或独立 inspector 页面，改为 Chat 卡片正下方左侧 card stack 中的紧凑小卡片，显示
既有 `/api/telemetry` 提供的 CPU、GPU、Memory 快照；renderer 通过固定 `telemetry` IPC 轮询，缺失或不支持的指标显示
`—`，并以 `LIVE · GPU UNAVAILABLE`/`UNAVAILABLE` 明确可用性，不补造零值。chat 原有的 Core/AI/Connection/Model
`RUNTIME` 也收纳在同一卡片内。UI 明确分为第一层中央 Core 与第二层 chat/monitor/Pages 浮动卡片；Chat、Token Usage widget 与 Pages 共用按左侧 Chat+monitor 卡片组总高度计算、并额外上提的 `--floating-top` 顶部锚点（正常最小 36px，矮窗口最小 28px），桌面窗口的 Chat 高度会在保留顶部保护、24px 底部安全间距与 10px 卡片间距后伸展；monitor 只用 170px 作为左侧布局预留，实际卡片按 metrics/runtime 内容自适应高度，不再被固定高度撑出底部空白。Core canvas 使用 `--core-height` 与 `top: 50%` 独立居中，短窗口自动收紧高度避免遮挡；浮动卡片仍不覆盖 Core 或右侧 Pages inspector。
Pages inspector 与 launcher 同宽并在同一区域覆盖显示，使用 `--dock-top-offset: 0px` 与 Chat 共用顶部锚点；inspector 采用内容自适应高度，并以 `--dock-overlay-bottom-gap: 24px` 作为 viewport `max-height`，短页面不会填满无内容区域，长内容仍在圆角卡片内部滚动且不碰 viewport 底部。`.page-stack` 建立明确的 column flex 高度边界，每个 Feature `panel-view` 都是可收缩的独立纵向 `overflow-y: auto` 容器，并保留横向溢出保护、overscroll containment 与稳定 scrollbar gutter，确保所有长页面可以继续向下读取。收起/展开、覆盖与切换页面使用可中断且尊重 Low motion/系统 reduced-motion 的 opacity/transform/filter 过渡；History 的 `Open chat` 会先给按钮/行级等待反馈，成功恢复旧 transcript 后再做一次同样受限的内容过渡，失败保持在 History。
Core header 与底部说明文字已移除，中央第一层只保留 Core canvas；左下角 Motion 控制条隐藏，但 Core RAF、旋转与 Settings Low motion 仍由原有状态逻辑控制。Core stage 的背景网格 overlay 已移除，保留主题背景、orbit ring 与 Core canvas。
当前 connected Pages 通过固定 bridge 读取已有 `/api/chat/history`、`/api/tasks`、`/api/system-info`、`/api/projects`、
project inspection/refresh、`/api/obsidian/vaults`、`/api/system-speech/settings`、`/api/system-speech/voices` 与 AI mode endpoint；Windows Speech per-user settings 缺失时 Core 明确返回 Windows default（speed 0），不把有效的系统默认语音显示成 unavailable；both editions' Voice selection
uses the same speech contract for `/api/system-speech`, while the Knowledge connection form uses the same fixed bridge
调用既有 `POST /api/obsidian/vaults` 注册和 `POST /api/obsidian/disconnect` 断开，默认 `default_access=excluded`，不在 renderer 扫描或持久化路径。
Tasks/Tools 导航不再显示伪造的示例计数，Tools 页保留本窗口真实
ToolResult，Events 页保留本窗口非 error 级别的 lifecycle/recovery evidence，Errors 页只保留本窗口
`error` 级别的 bridge/Core/surface failure；两个清理动作互不删除对方记录。没有 direct renderer HTTP、凭据回显或自动 OS action。
Both editions expose the Voice inspector through the edition allowlist; `#voice` is accepted in each edition, while Settings' Automatic speech
controls and the existing speech bridge remain unchanged.
Automation、Codex handoff、STT、wake、SQLite operational memory 等仍是 PLANNED/demo。
布局不改变 bridge、权限、routing、Core storage、confirmation 或页面未实现能力语义；renderer 仅增加 Settings 状态与浮窗活动计时、分开的 Memory/Knowledge inspectors、History inspector、分开的 Events/Errors inspectors、Theme inspector、受限 speech bridge/voice inventory 和 Chat scroll anchor；真实 1366×768 与
大桌面截图验收仍交由普通用户/99 QA。

本次 turn/message-list、availability/startup 与 local persistence package 的 source、Node model 和 supervisor regression 已通过；
当前受限 host 的 Python 进程 ACL 使真实 Core supervisor 启动返回 `拒绝访问`，因此普通用户 shortcut
启动与 renderer 输入/确认/History 观察仍需在用户环境完成，不能写成 runtime `VERIFIED`。本地文件加载与
renderer localStorage 恢复只在对应 runtime 可用后验收。

补充验证：在真实 Windows 权限下运行 `npm run verify` 已返回 `verification: passed` 与 `webglActive: true`；
同一环境的 `CoreSupervisor.ensureReady()` 冷启动也返回 `core.status: ready`。Electron 的 cache/GPU cache
access-denied 仅为既有诊断警告，未启用 GPU fallback。若窗口再次显示 offline，应先核对 `127.0.0.1:8765`
是否有 listener，再重开 Preview/Legacy shortcut。

本次 M3a source/contract implementation 是 `IN PROGRESS`，尚未称为 runtime/UI `VERIFIED`：
`npm run verify:static` 与 `node --test test/core-contract.cjs`（7/7）通过，但当前受限 host 的
`npm run verify` 重现 GPU child `0xC0000135`，伴随 cache access denied/GPU cache creation failure，
最终 `ERR_FAILED (-2)` 加载 `motion.html`。按 GPU 清理停止规则没有重新加入 flag、fallback、强制
SwiftShader 或 profile workaround；该段仅保留此前受限 host 的历史证据，本次 packaged Internal Test 的最新
Core/Electron 运行验证见上面的安装器状态。
本轮 runtime-lifecycle 改动后的再次尝试还出现 Electron `crashpad_client_win.cc:869 not connected`；
这同样只记录为受限环境阻断，不改变代码权限边界或通过 workaround 掩盖。

不属于本基线：read_obsidian_note、SQLite operational memory、后台 worker/API、MemoryManager/ContextBuilder、Codex handoff/coding-memory UI。历史 working-tree 笔记包含这些能力，但不能作为 main 已实现依据。

已实现最小 managed Luna 与 Direct provider foreground chat：用户在 Settings 手动选择 managed ChatGPT
subscription App Server，或 Direct OpenAI Responses、Gemini Interactions、DeepSeek Chat Completions、
或 HTTPS OpenAI-compatible Chat Completions gateway。managed mode 仍只使用 exact `gpt-5.6-luna`，
Direct mode 的 model 是用户显式输入的协议兼容候选，必须在发送真实消息后由账号/endpoint 确认，不能被 UI 伪称可用。managed mode 只有 managed ChatGPT login
且 `model/list` 包含 Luna 时运行；每个模型 turn 使用
空临时工作目录和 allowed `:read-only` profile；无 RAG、Vault、项目、屏幕、原生工具、
dynamic tool、MCP、plugin、browser 或 shell 能力。Core health 当前报告
独立的 `core.status` 与 `ai` mode/status/model/last check，不能将 Core ready 误读成账号、key、
model access 或额度已经验证。Electron 首次 Core online 会自动完成 managed transport 的无推理
handshake。Direct key 只在当前 Core memory，不会持久化、回显或自动测试；Direct
request 不创建 Codex thread，`store:false` 且不传 subscription mapping/context。失败不回退 Gemini、
其他模型或另一 mode。明确的现有 native intents 仍在模型前
由 Core 路由并经原 permissions/confirmation（power 请求经一次确认）；关机入口接受一组
有限、整句匹配的 `shutdown/shut down` 与 `pc/computer` 英文变体及常用中文“关闭电脑”表达，
仍不让 Luna 参与本地执行判断。对于 exact resolver 未命中但包含明确本地操作线索的短请求，
managed Luna 现在可在同一 text turn 中返回一个严格 marker 形式的候选；Core 只把它当作
不可信输入，复用现有 schema/敏感文件校验并交给 PermissionManager。低风险候选走既有安全
执行路径，中高风险候选进入一次用户确认，绝不让模型直接执行。普通问答不请求该 marker；
畸形、未知或低置信度候选会被清理并显式保持为文字回复。`open_app` 继续只接受
`config/apps.json` 中已发现的 Start Menu shortcut；中文“打开”/“启动”与应用名称之间可不加
空格，因此 `打开Google Classroom` 会复用现有 Google Classroom registry entry 与
`find_app` 的保守匹配，找不到或 shortcut 失效时仍返回明确失败。

AI status 当前可为 `unconfigured`、`not_checked`、`available`、`authentication_failed`、
`model_unavailable`、`rate_limited`、`network_error`、`service_error` 或 managed transport explicit
failure；它不改变 Core 的 `ready`。有 pending native confirmation 时 mode/key endpoint 返回 409，
不跨 mode 转移 context。Windows managed App Server child 已配置 hidden creation flags；重启 Core 后
模型请求不弹出可见 cmd 窗口的实际人工确认仍待完成。

每个 JARVIS conversation 现在拥有独立、opaque 的 App Server transport mapping；首轮仅为该
conversation `thread/start`，并要求返回的 thread 明确为 `ephemeral`。mapping 只含 thread ID、
固定 owner/version 与认证上下文 hash，且只保存在当前 Core 进程内存；HTTP/UI 不暴露它，也不写入
`conversation.json`。Core/child restart 后不恢复旧 mapping 或 Codex history，下一次请求会按明确的
ephemeral 生命周期创建新的临时 thread。新建桌面对话才申请新的 JARVIS conversation ID；等待原生
确认时 UI 禁止新对话，避免 yes/no 作用在被隐藏的待确认请求。

managed Luna 的 App Server 现在由 `CodexAppServerAdapter` 在 Core 生命周期内按需持有：首次窗口
自动检查或第一条真实请求会创建 adapter-owned child、空 temporary CWD 并完成既有
initialize/account/model/profile 校验，
后续请求复用同一健康 child、JSON-RPC session 与已验证状态，不重复握手。adapter 内部 lifecycle lock
保证并发初始化只有一个 owner；stdout 与 stderr 均持续排空。child 崩溃、协议/权限/认证失败或
timeout 会使 resident 状态失效，当前请求返回显式错误且不重发未知 turn；下一次请求才可重新验证。
Core shutdown 只清理该 adapter 自己的 child 与 temporary CWD，mode 边界也会使 managed 验证失效。相同
resident child 中，已通过 owner/version/auth hash 校验且 developer-instruction context 未变化的
ephemeral thread 会跳过重复 `thread/resume`；context 变化仍显式 resume，child/Core restart 则显式创建
新的 ephemeral thread，不把旧 mapping 送回 Codex thread store。JARVIS child 还显式使用 `low`
reasoning effort，不修改用户全局 Codex 配置。响应在 provider 明确报告时可带去敏的 `usage` DTO；`[JARVIS_TIMING]`
记录只包含 opaque request id、阶段毫秒数、transport generation、`thread_resume_skipped`、
`thread_recreated` 和 provider 可提供的 `first_token_ms`，不记录账号或密钥。
turn response 的 provider usage 不写入 Core transcript 或 timing store；Direct API records 由 renderer 以
edition-scoped localStorage 保存供 JARVIS widget 与对应 Feature view 展示，Managed `account/usage/read` snapshot 则只供
显式 Feature Usage 页面展示。两者都不携带账号 identity、credentials 或 auth material 跨 Core boundary。

Proposal mode 复用同一 resident child、thread mapping、`:read-only` profile 与握手，不新增
classifier turn 或 AI probe；模型候选仍经过 API 的 schema/path 校验与 TaskRouter，低风险工具
使用既有 PermissionManager 允许路径，中高风险工具保持 Yes/No confirmation。候选执行后的
awaiting/denied/completed 记录沿用既有 Tool Results 与 pending confirmation contract。

受限 runtime acceptance（临时 8767、同一测试 conversation、三次非私密 `tell`、现有 managed subscription）
已实测：cold HTTP 8063.6ms / adapter total 8050.9ms，warm-1 2239.1ms / 2225.3ms，warm-2 1813.6ms /
1806.8ms；后两次均 `transport_reused=true`、generation 1，握手阶段为 null。cold 的 turn completion
6428.1ms 与 warm 的 2188.4/1786.6ms 仍属于外部模型/服务路径，因此该小样本只证明复用生效，不承诺固定
秒数或首 token；8765 原有 listener 未被重启或取样。

指定 ChatGPT cloud 项目 `Jarvis Chat` 不是当前本机 App Server 可读 project：实际 `project/read`
返回 `project not found`。因此新 transport 没有宣称该云端归属，亦没有用 CWD、同名本地 project
或 sidebar section 伪造分类；这是独立的未实现 integration gap。

此前记录的“Codex sidebar 没有 JARVIS chat”运行时观察已被用户最新截图推翻：修改前的持久 App Server
thread 确实出现在 Codex 的“最近”列表。本次 source/test 修复要求 Codex 返回 ephemeral thread，并将
mapping 改为 RAM-only；旧的 Codex 条目不由 JARVIS 自动删除，修改后的 Desktop 列表仍需用户重启
JARVIS 后观察。当前无推理 live probe 在 App Server `initialize` 阶段因 child 提前退出，未到达
`thread/start`，所以实际返回的 ephemeral 字段与桌面列表仍未宣称已验收。

若同一 resident ephemeral thread 的 `thread/resume` 明确报告 active writer/thread-store conflict，当前
source 仍显示 `session_busy`，不会在该冲突路径静默创建替代 thread。非冲突的 child restart 由上面的
ephemeral 生命周期策略处理；真实 Codex Desktop 列表清理与人工视觉验收不在自动测试范围。

已完成 M1.1（90 Integration）：路由/API 以显式 ToolResult 传递原生成功、
未知工具/异常失败、等待确认和拒绝；确认任务使用进程内
`waiting_approval`/`denied` 状态，外部 callback 异常收束为终态 failed。Python
93 tests、Flutter 30 tests 和 `flutter analyze` 已通过；Core 重启后 health
为 ready。M1.2 仍负责逐工具业务失败字符串契约，M6 仍负责 durable lifecycle。

未接入 operational SQLite、RAG/KM model context、Automation、Voice/Screen、Codex handoff
或真实数据迁移。Phase D 未授权。受限 Luna transport 的 Core HTTP 真值和 native deny 回归已
验证；Release desktop 已启动并保持 Core 连接。用户已在 Release UI 验证 Luna 文本回复，以及原生 sleep
请求的可见确认选项和拒绝路径（`awaiting_confirmation → denied`）；拒绝未执行系统睡眠。参见
`docs/prompts/feature/20260906-FEAT-codex-subscription-desktop-chat.md`。
