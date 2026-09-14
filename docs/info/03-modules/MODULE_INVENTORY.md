# Module Inventory / 当前组件清单

Status: CURRENT, source/static-inspected; Audio/Brightness/Wallpaper/Windows OS Theme/System Status source/mock/static/bridge-contract verification is complete, the structured Electron Device endpoint is wired, while ordinary-user runtime acceptance remains pending. Baseline: main@07df06f92c3a90eb2fa2dc2bd42cc76271e7d21f, 2026-09-13.
本文是当前模块文档原本；Obsidian Components 目录保存阅读镜像。接口名是定位入口，不代表正式冻结 DTO。Does not own 是职责约束，不声称所有旧实现已符合。

## Managed Subscription and Direct Provider Connection / 订阅与 Direct Provider 连接

- Owns：`AiConnectionService` 只拥有前台 text transport 的显式手动选择：`managed_subscription`
  或 `direct_api`；不拥有 native execution、任务生命周期、存储或自动 routing。
- Paths/interfaces：`services/ai_connection.py`、`services/agents/luna_model.py`、
  `services/agents/openai_responses.py`、`services/agents/direct_api_providers.py`、
  `services/agents/codex_app_server.py`；API 提供 Settings
  endpoints 与无推理的 `/api/settings/ai/check`，`/api/health` 继续提供分离的 `core` 与 `ai`
  snapshot。
- Storage/secret boundary：Direct API 的 provider/model/base URL（仅 gateway）与 key 只在当前 Core
  process memory；key 永不持久化、返回或记录日志。未经用户实际调用授权时保持 `not_checked`。
- Failure/status：没有 provider/model/mode fallback；managed transport 可在 Electron 首次 Core
  ready 后自动做 initialize/account/model/read-only profile 检查；Direct API 没有无推理验证端点，
  仍保持 `not_checked` 直到用户显式发送请求。当前 Direct provider 是 OpenAI Responses、Gemini
  Interactions、DeepSeek Chat Completions，或用户提供的 HTTPS OpenAI-compatible Chat Completions
  gateway；每种协议独立解析响应，不能把任意 key/model 当作兼容。pending native confirmation 拒绝连接修改。
  Windows App Server child 已配置 `CREATE_NO_WINDOW`，Core restart 后的实际人工确认仍待完成；没有
  user key 与明确授权时 Direct paid inference 不是已验证行为。

## Desktop Core Motion Preview / 桌面核心球体预览

- Owns：一个 isolated、simulated-only 的 Flutter visual study；不拥有 Core health、AI status、
  actual request state、telemetry 或任何 execution capability。
- Paths/interfaces：`desktop_ui/lib/core_motion_preview.dart` 是 `flutter run -d windows -t` 的独立入口；
  `desktop_ui/test/core_motion_preview_test.dart` 仅验证 UI state/ticker lifecycle。
- Rendering/lifecycle：deterministic `CustomPainter` 画投影网络球壳、环、轨道、粒子与光晕；
  `RepaintBoundary` 限制区域，painter 约 30 Hz 更新；TickerMode、lifecycle、Pause、Low motion 均停止 ticker。
- Status：source/test/build verified；未接入主 Assistant，且自动化环境未捕获 native preview window，因此
  visual comparison/screenshot 是 user review gate，不能写成 verified UI integration。现有 Flutter Release
  入口标记为 `JARVIS - Legacy UI.lnk`，仍用于真实 Core/API 与功能测试。

## Electron WebGL Shell Validation / Electron WebGL 隔离壳验证

- Owns：`electron_motion_preview/` 拥有 experimental presentation wrapper 和一个窄的 Core client
  bridge；不拥有 Core/API 的 routing、AI、工具、权限或 telemetry sampling。它现在可读取既有 telemetry、
  history/list/open、TaskManager、system info、project registry、Obsidian vault metadata、Windows speech settings
  and snapshots installed Windows voice packages; both Electron editions' Voice pages initialize voice state, save voice selection, and test presentation;
  edition-scoped localStorage 继续保存 Events、Errors、terminal Tool Results 和 UI preferences。
- Paths/interfaces：`main.cjs` 建立单一 sandboxed BrowserWindow；`core-supervisor.cjs` 在 normal launch
  先检查固定 loopback health，必要时以 shell-free 固定参数启动并持有现有 `uvicorn app.api:app`
  child；`preload.cjs` 暴露固定的 health、telemetry、history/list/open、session、chat、system/project/tasks/Obsidian/AI
  surfaces 与 `speechSettings`/`speechVoices`/`speakReply`/`stopSpeech` IPC；新增 `chatStreamStart`/`chatStreamCancel`/
  `chatStreamEvent` 与 `synthesizeSpeech` 固定 IPC；`core-bridge.cjs` 请求 `127.0.0.1:8765` 的固定 Core/API path；`renderer/` 保留本地 WebGL 视觉与动态 Core/AI/chat/result
  surface，`conversation-store.js` 维护当前窗口的 turn ownership/epoch，`test/static-verify.cjs`、
  `test/core-contract.cjs`、`test/core-supervisor.cjs` 与 `test/conversation-store.cjs` 检查安全、协议、
  启动和消息状态边界。
- Streaming chat：`/api/chat/stream` 由 `core-bridge.cjs` 按 NDJSON 行读取，`main.cjs` 通过固定 IPC
  转发事件，`renderer/response-stream.js` 负责 `[DISPLAY]`/`[VOICE_EN]` projection，并从已显示 response text 交给
  72–240 字符窗口、sentence-batching `SpeechChunker`；窗口内选择最后一个自然边界，逗号与冒号不会单独触发新的 TTS item；terminal `[VOICE_EN]` 仍保留为 canonical narration，不在已消费或已暂存 display speech 后重复播放，短回复的 final flush 也只产生一个 item。
  `renderer/unified.js` 负责渐进 display、response metrics、取消与 turn ownership。
  `renderer/auto-speech.js` 只保留 current/next 合成槽和最多 8 项文本待处理队列，不让 TTS backpressure
  停住后续文字；`synthesizeSpeech` 返回 WAV 后由 renderer Audio 顺序播放。managed
  `CodexAppServerAdapter` 的 resident lifecycle 使用 primitive `Lock` 串行化 process/session；这是因为同步 stream
  generator 可能在不同 Starlette worker thread 之间恢复或关闭，不能使用要求同一线程释放的 `RLock`。该边界已由跨线程
  stream regression 覆盖。
- Boundary：renderer 没有 Node integration 或直接 HTTP；bridge 不接受任意 channel、URL、command、
  file 或 SQL。remote navigation、popup、webview 与权限请求均被拒绝；prototype 自有 Page
  Visibility/Pause/Low motion 生命周期逻辑保留。
- Runtime lifecycle：`main.cjs` 使用单实例锁；Settings 的 `Run in background`（默认关闭）让 close
  隐藏窗口并保留同一 Electron/Core child，再次打开同一 shortcut 只聚焦该窗口。`Start on login`
 （默认关闭）通过 `app.setLoginItemSettings` 写入 Windows 登录项。两个值按 edition 保存到
  `userData/jarvis-runtime-{edition}.json`，只通过固定 preload IPC 读写；没有托盘、远程唤醒或替代启动路径。
- CSP：script 仅允许本地 self；为保留原型现有少量 inline layout styles，style 允许 `unsafe-inline`，不
  代表开放脚本或网络执行。
- Runtime profile：此前按进程隔离的临时 `userData/sessionData` override 仅用于 GPU/cache 诊断，已移除；
  现在不再替换 Electron 的默认 profile 路径。
- Status：用户在 profile 清理前确认获批安装后的真实 `npm run verify`、`webglActive: true` 与动画窗口；
  清理后受限 host 的一次对照运行以 `0xC0000135` 退出并导致 `ERR_FAILED`，未加入 flag/fallback，该
  结果保留为诊断历史。随后以普通非管理员 `ONGZHENGAN\\ongzh` 执行的 `npm run verify` 返回 0，输出
  `webglActive: true` 与 `canvasSize: [1152, 662]`；同一普通用户的 `npx electron .` 也已启动并确认
  窗口标题为 `JARVIS · proposed desktop UI`、独立 GPU child 和 `--enable-sandbox` renderer。该标题是本次改动前
  的 runtime 观察；现在 main process 按 edition 固定为 `JARVIS · 开发版` 或 `JARVIS · 内测版`，已通过
  source/static checks，下一次真实窗口打开仍是用户验收点。EXE 仍未打包，且打包不是该实验完成条件，实验未授权
  platform migration。
- Root-cause boundary：受限 host 以 `ONGZHENGAN\\codexsandboxonline` 运行，默认 profile 对
  `CodexSandboxUsers` 只有 `ReadAndExecute`，因此 cache access denied 是环境权限证据；GPU child 的
  `0xC0000135` 只确认 Windows loader dependency failure，具体 DLL 尚未由静态检查定位。不得在此模块
  通过 GPU flag、fallback 或 profile override 掩盖该问题；普通非管理员环境已验证，不需要系统级 workaround。
  历史上曾有 `Microsoft/Spelling/neutral`、`Ƞ젊Ǐ`、`Ꞑ�ǭ` 三个空诊断残留；它们及空父目录已在确认
  无 reparse point、无内容、无源码/配置/Git 引用后精准删除。历史 packager 的乱码路径 `ENOENT` 已证实，
  但这些目录的创建者未证实；删除不代表已定位来源。
  当前复核另见空目录 `electron_motion_preview/▐␹ǌ/Microsoft/Spelling/neutral`；该名称不在已批准清单内，
  本次未删除。
- User entrypoints：`C:\Users\ongzh\Desktop\JARVIS 开发版.lnk` 由
  `create-desktop-shortcut.ps1` 写入项目内 `node_modules/electron/dist/electron.exe` 的绝对 target，参数
  `.`、工作目录为 `electron_motion_preview`；`C:\Users\ongzh\Desktop\JARVIS 内测版.lnk` 指向
  `electron_motion_preview_internal_test` 并带 `--edition=internal-test`。normal launch 先检查/启动真实 Core，`--verify` 只检查
  renderer。两个 shortcut 已在用户 Desktop 创建并复核其工作目录、参数与描述；main process 现在将前者标题固定为
  `JARVIS · 开发版`、后者固定为 `JARVIS · 内测版`，并阻止 renderer 静态 `<title>` 覆盖版本标识；该入口仅用于 WebGL
  视觉/交互与 M3a Core foreground contract 测试，连接只经固定 bridge；
  它不是正式 UI、EXE package 或 Flutter 替代品。M3a 与本次 availability FIX 当前仍 `IN PROGRESS`：
  source/static/supervisor tests 通过，但当前受限 host 的 Python ACL 使真实 supervisor cold start 返回
  `拒绝访问`，所以 Core/Luna/native UI 观察尚未称为 verified，也没有加入 GPU workaround。
- Conversation boundary：当前窗口 transcript 由 `conversation-store.js` 按 turn 追加并在 DOM 上写入
  `data-turn-id`；confirmation decision 复用原 turn，stale epoch response 被拒绝。terminal turn 由 Core
  通过 `JarvisMemory` 写入 `data/memory/conversation.json`，`/api/chat/conversations` 列表和
  `/api/chat/history/open` 只读取指定 opaque conversation。每次 Electron 重开窗口都从新的 active chat
  开始；History inspector 的 `Open chat` 才显式恢复任一已保存 chat，`Start new chat` 切换 ID，不再按本地日历日自动轮换。
  pending confirmation 只留在运行内存，不写入 Core JSON 或 renderer localStorage。
  Core offline 时 input 保持可编辑但 send 被禁用，
  不会自动排队或在重连后发送草稿。user 行不渲染头像，assistant 行复用现有 brand logo；真实 Core
  请求结果或显式失败会在 assistant 行显示 measured `Response time X.Xs`，离线拦截不伪造耗时。
  Tool Result 记录只在专用 Tool Results 页面呈现；Chat 不再追加 completed/failed/session_busy 等终态审计卡片。
  `awaiting_confirmation` 只显示 Yes/No controls，完整 JSON 仅在 Tool Results 页面保留；denied 终态保留
  assistant reply 且不在 Chat 重复追加 JSON。health 每 2 秒轮询；Core 首次 online transition 会
  额外调用一次固定 `aiCheck`，只验证 managed transport，不创建 thread 或 turn；30 秒仅是 Core
  supervisor 冷启动上限。AI `not_checked` 仍表示没有完成相应 transport verification，不会被 UI 伪造为 available。
  `core-bridge.cjs` 为 `sendMessage` 使用 65000ms operation-specific bounded timeout，覆盖现有 AI
  adapter/provider 的 60 秒单次等待；其他快速 Core operation 继续使用 15000ms 默认值。renderer 在
  `aiCheck` in-flight 时只禁用普通 send，保留可编辑输入与草稿，并在检查结束后恢复发送；timeout 或
  transport failure 仍是显式结果，不会重发未知 turn。

- Layout refinement (IN PROGRESS)：renderer 正在把 Electron preview 改为无 sidebar 的 floating-window workspace：
  主窗口只保留中央 WebGL core，左侧 chat pane 成为独立小窗口，右上 Pages 默认显示 compact toggle，展开后以 5 列
  launcher 提供 Tasks/Tools/AI 等入口；选择页面后同一位置的 inspector 覆盖 launcher，详情 header 保留 Pages toggle。
  chat card 已移除冗余标题和手动新建入口，内部密度约缩至原来的 80%（包括 composer）；打开页面后 5 秒没有指针或键盘操作会自动关闭，
  交互会重新计时；Pages 图标 hover/focus 显示页面名；
  chat/core/page header 不增加横向分隔线。composer input、hint 与 send button 使用 shrinkable flex sizing，message body/Markdown paragraph
  在气泡内换行，Core stage/core-space/canvas 保持 `min-width: 0` 与 `max-width: 100%`，避免窄窗口横向溢出。Low motion 默认关闭，只有本地
  明确保存 `true` 才启用；选择后以 `jarvis.motion.low.v1` 持久化并将 Core elapsed-time 推进放慢，但不停止 RAF 或 Core rotation；系统
  `prefers-reduced-motion` 样式与变化监听作为独立 accessibility override 保留。
  hologram 内层与桥接线不再使用额外的水平偏移，保持 Core 几何中心与外层 shell 对齐。
  日期默认使用英文 `en-US` 短格式；Settings 通过受限 `jarvis.clock.locale.v1=zh-CN` 切换中文日期；独立的 Response language 默认是 `en`，
  Settings 可切换为 `zh-CN`，通过 `jarvis.response.language.v1` 保存并随新 chat/stream 请求传给 Core；它不翻译历史或改变 UI 日期语言。
  自动朗读开关默认关闭，用户开启后通过
  `jarvis.auto-speech.enabled.v1` 在本地 preview profile 持久化，重开窗口恢复开关但不重播旧消息；both editions' Voice pages use
  `speechVoices` bridge 列出 Windows OneCore voice packages，以 `jarvis.auto-speech.voice.v1` 保存选择，并提供 Test voice。
  Pages 将 Memory 与 Knowledge 分成独立的 `Memory` 与 `Knowledge` inspector：前者只加载 conversation history，后者只加载注册的
  Obsidian metadata；另有独立 `Theme` inspector 作为视觉预设的唯一入口，避免 Settings 重复拥有主题选择器。
  System monitor 已从 Pages/独立 inspector 页面移除，改为 Chat 卡片正下方左侧 card stack 中的紧凑小卡片，使用固定 bridge 轮询既有
  `/api/telemetry` 显示 CPU、GPU、Memory；缺失指标显示 `—`，GPU 缺失标注 `LIVE · GPU UNAVAILABLE`，Core/网络失败标注 `UNAVAILABLE`。
  chat 原有的 Core/AI/Connection/Model `RUNTIME` 也在同一卡片内。
  UI 明确分为中央 Core 基础层与 chat/monitor/Pages 第二浮动层；Chat、Token Usage widget 与 Pages 共用按左侧 Chat+monitor 卡片组总高度计算、并额外上提的
  `--floating-top` 顶部锚点（正常最小 36px、矮窗口最小 28px），桌面 Chat 高度按 viewport 剩余空间伸展（保留顶部保护与 24px 底部安全间距），monitor 只以 170px 作为布局预留，实际卡片按 metrics/runtime 内容自适应高度，两者同宽并在其下方保持 10px 间距，不占用右侧 Pages inspector；Core canvas 使用 `--core-height` 与 `top: 50%` 独立垂直居中，短窗口收紧高度避免遮挡；左下角 Motion control strip 不再显示，Core canvas 与 Settings Low motion 状态逻辑保留。
  Pages launcher 采用默认收起、展开后每行 5 列的短标签单行网格；inspector card 与 launcher 同宽并在同一区域覆盖，
  Pages 浮层使用 0px top offset 与 24px bottom gap 计算 `max-height`，短页面按内容收紧、长内容在 card 内部滚动，均不碰 viewport 底部；`.page-stack` 使用 column flex 高度边界，每个 Feature `panel-view` 都是可收缩且独立的纵向 `overflow-y: auto` 容器，并保留横向溢出保护和稳定 scrollbar gutter。Core stage 不再绘制背景网格，仅保留主题背景、orbit ring 与 Core canvas。导航收起/展开、页面覆盖与页面切换使用
  `feature-nav-enter`/`feature-page-enter`、`page-header-enter`/`page-view-enter` 及 opacity/transform/filter 的可中断过渡；renderer 会取消实际 CSS animation、强制建立样式边界并在 `animationend`/`animationcancel` 后清理 class，History 恢复使用 `conversation-restore`，Low motion 或系统
  reduced-motion 时不加入空间位移；History `Open chat` 的当前 row 只显示等待反馈，不改变 Core 请求。
  Core header/底部说明已移除，第一层只保留 Core canvas；Motion control strip 隐藏但不改变 RAF/Low motion 状态逻辑；
  背景网格已移除，剩余光晕与 orbit ring 只是视觉 instrument，不代表 telemetry；
  真实窗口截图与窄窗口/reduced-motion 检查仍待普通用户/99 QA。

- Composer/message refinement (IN PROGRESS)：`renderer/composer-behavior.js` 提供可测试的 IME Enter guard、应用内
  `Ctrl+L` focus/caret-to-end 与 draft-preserving helper。`unified.js` 让 busy request 期间 input 保持可编辑而只禁用
  send action；pending/offline/duplicate guards、modal priority 和异步不抢焦点边界保持不变。消息 presentation 采用
  user 右侧紧凑块、JARVIS 左侧较小 brand logo、长文本块内左对齐换行，并移除 per-message 全宽 separator；
  `composer-focus.cjs` 与 `static-verify.cjs` 已通过，真实 Electron focus/visual QA 仍待普通用户/99 QA。
  真实 Core 返回前的 assistant placeholder 与中央 motion `thinking` 说明统一显示 `Thinking…`；这只是 pending 状态文案，
  不改变请求、计时或结果语义。
  Chat `#messages` 保留唯一原生纵向滚动容器并隐藏视觉 scrollbar；普通 append 尊重用户滚离底部的阅读位置，新的 user turn、
  真实回复/显式失败和 confirmation controls 则通过可取消的两帧 tail settle 强制显示最新内容，避免 Yes/No 卡片落在可视区外或产生撕裂。
  Pages 现在有 Settings entry：日期语言受限为 `en-US`/`zh-CN`，浮窗 auto-close 可选择时间或 Never；`auto-speech.js` 对随后 completed turn
  与明确的 awaiting-confirmation prompt
  按 turn 阶段 key 去重并顺序调用既有 Windows system speech，关闭时停止当前播放并清空队列。没有逐条
  `Read reply`/手动播放按钮，语音错误只在 Settings 显式显示且不改变文字。speech enqueue 在 assistant DOM 更新前
  于同一响应任务内直接启动 bridge；native confirmation 使用完整权限提示；Windows system voice 播放前将可寻址合成流置于
  offset 0 并主动 `Load()`，其自身启动时间仍属于既有服务边界。独立 Theme page 提供本地
  持久化的 `Amber Core`、`Cyan Circuit`、`Violet Pulse`、`Matrix Green` 主题，CSS token 与 hologram shader palette
  同步更新，默认仍为 `amber`；preset SSOT 仍为既有 `jarvis.ui.theme.v1` localStorage key。Theme page 另有八项
  background/surface/border/accent/text/muted/Core A/Core B color controls，custom values 经过 allowlist 与 `#RRGGBB`
  校验后保存到 `jarvis.ui.theme.custom.v1`，即时覆盖 presentation tokens，并可 Reset 回 preset；不改变 Core/API/permission。

## Runtime and API / 运行时与接口

- Owns：启动、共享实例、HTTP 请求编排；不拥有独立数据库 schema、检索算法或新的权限语义。
- Paths/entries：app/main.py run_jarvis、AVAILABLE_TOOLS；app/api.py chat_with_jarvis、health、chat_history；app/desktop_launcher.py。
- Inputs/outputs：ChatRequest/ToolRequest、HTTP JSON、speech bytes/status；CLI 用户文字与终端输出。
- Depends on：router、Codex App Server adapter、JarvisMemory、RAG、speech/telemetry；used by Flutter JarvisApi / terminal。
- Storage/flow：委托 memory；API → policy → service → response。composition 使用全局实例及 conversation lock。
- Permissions：safe-tool argument/target checks、TaskRouter policy；API 不是无权限 OS shell。
- Failure/status：M1.1 已让 router/API 传递显式 completed/failed/awaiting
  ToolResult，未知或异常不再由序列化误报成功；RAG 失败继续无上下文调用仍是
  独立 gap。普通文本仅使用用户手动选择的 exact Luna 受限 transport；其失败显式返回，
  不回退 Gemini、另一连接 mode 或其他模型。90 是本包共享文件 writer。

## Canonical Tool Metadata / 原生工具元数据

- Owns：provider-neutral native-tool names, descriptions, parameter properties and required keys；不拥有执行函数、permission policy、provider client、UI 或 native-intent phrase aliases。
- Paths/interfaces：`services/tool_catalog.py` 的 `TOOL_DEFINITIONS`、`build_tool_definitions()`、`build_tool_schemas()`、`build_intent_catalog()`。
- Inputs/outputs：JSON-compatible canonical definitions → copied Gemini declarations、API required/optional schema map、managed-GPT bounded intent catalog。
- Dependencies/users：仅 Python standard library；`services/agents/gemini.py`、`app/api.py` 使用其 provider/API views；`app/main.py` 的 `AVAILABLE_TOOLS` 仍是执行 registry。
- Storage/flow：静态源码 metadata，无独立 storage；provider/API 读取 derived view，不修改 canonical list。
- Boundary：结构化 schema 只描述 action/argument contract；range、path、sensitive-file、permission、confirmation 与 unsupported-capability policy 仍由 API/TaskRouter/PermissionManager/native adapters 负责。
- Failure/status：builder 返回独立 copies；当前 110 个 definitions 与 registry、Gemini declaration、API schema、intent view 由 parity tests 检查。没有为 managed GPT 打开 model-side native function calling。

## Routing and Permissions / 路由与权限

- Owns：native/external 路由、动作风险、待确认请求；不拥有 task 生命周期、SQL、UI。
- Paths/entries：services/task_router.py TaskRouter.execute_tool、execute_external_action、handle_pending_confirmation；services/permission_manager.py evaluate；services/native_intent.py resolve_native_intent。
- Inputs/outputs：tool name、arguments、user input、ActionRequest(executor/action/purpose/data_scope) → callable result 或 PermissionDecision/pending dict。
- Depends on：TaskManager、NotificationService、native callbacks；used by API/CLI/Codex adapter integration。
- Storage/flow：单个进程内 pending_action_request → yes/no → stored callable；无 durable approval。
- Permissions：分类 allow/confirmation；未知工具不能正常调用；当前 unknown action policy 为确认，而非完整 capability-deny 模型。
- Failure/status：M1.1 将原生异常/未知工具结构化失败，待确认保持
  `success: null`/`waiting_approval`，并在拒绝或批准后的异常时终结关联任务。
  无冻结 C2 的 request/run fingerprint、过期和重新校验；逐工具业务失败字符串
  合约属 M1.2。显式 power phrases 先落在 narrow native-intent allowlist（包含有限的
  `shutdown/shut down` + `pc/computer` 变体），仍由 PermissionManager 要求确认，不暴露给 Luna。
  managed Luna 对 exact resolver 未命中的短本地操作请求可返回一个不可信 marker；API 复用同一
  schema/path validator，TaskRouter 仍交给 PermissionManager：低风险候选执行，中高风险候选
  进入 confirmation，候选失败保持显式且不触发 fallback。
- Semantic owner：01 高层 routing、05 policy；shared router 由 90 接线。

## Tasks and Notifications / 任务与通知

- Owns：Task 状态/时间/结果与通知文字；不拥有 routing、Gemini、RAG、数据库 migrations 或主动通知策略。
- Paths/interfaces：services/task_manager.py create_task/start_task/complete_task/fail_task/get_task/list_tasks；services/notification_service.py notify_task_status。
- Inputs/outputs：title/agent/id/result/error → Task/dict；status/title → message string。
- Depends on：stdlib datetime/uuid/dataclass；used by TaskRouter/API health 与只读 `GET /api/tasks`。
- Storage/flow：`TaskManager.tasks` 同时作为当前状态与 `data/memory/task-history.json` 的 owner，queued → running → waiting_approval →
  completed/failed/denied/interrupted；保存时用 sibling `task-history.lock` 协调当前进程、用 PID/UUID 唯一临时文件执行原子替换，
  Windows 短暂 access-denied 只对同一替换操作做有界重试；NotificationService 返回文本，无自动恢复或通知数据库。
- Permissions：状态变化不是执行授权；无 worker cancellation/verification guarantee。
- Failure/status：不存在 task 返回 None；状态方法无终态 compare-and-set；Core 重启会将未完成 task 明确标为 `interrupted`，不会恢复或重发。持久 external handle/ACL failure 在有界重试后仍显式记录，不能切换存储或伪造成功。VALID_STATUSES 列表不等于全部行为存在。没有独立 TaskRun/scheduler。Electron Tasks 页只读显示持久化记录。
- Owners：06 tasks、09 notifications；M1.1 有界 writer 例外见 ownership。

## Conversation Memory / 对话记忆

- Owns：terminal 聊天历史、脱敏、近期模型 context 与 opaque conversation index；不拥有 SQLite、User Model、knowledge publication 或全局 ContextResult。
- Path/interface：services/jarvis_memory.py JarvisMemory.remember/history/gemini_contents/clear、create_conversation_id、transport_session、remember_transport_session；composition 参数 100/6。
- Inputs/outputs：user/assistant/speech → MemoryTurn list 或 Gemini contents；JARVIS conversation ID → 当前 Core 进程内的 opaque owned transport mapping。
- Dependencies/users：deque、Lock、JSON、Path；API 与 Gemini request composition 消费。
- Storage/flow：memory deque（仍按 composition 的 max_turns 限制模型 context）与全部 terminal conversation records → temporary JSON → replace `data/memory/conversation.json`；启动加载。managed transport mapping 只存于 RAM，不写入或从该文件恢复；mapping 只存 thread ID、owner/version/auth-context hash，不存 token 或账号原文。旧 `transport_sessions` 字段会被忽略且不再写回。`awaiting_confirmation` 永不写入。
- Permissions：正则脱敏，不构成全量 data-access policy；context 不授权执行。
- Failure/status：load/save errors 打印，内存可能继续存在；terminal failed/denied outcome 与 timing 可恢复，未知或 pending outcome 不会伪装成完成。主分支无 SQLite MemoryManager。02 owns。

## RAG and Knowledge Retrieval / 检索

- Owns：来源、分块、embedding、索引、retrieval/citations；不拥有个人偏好 authority、知识批准发布或执行授权。
- Paths/interfaces：services/rag/；knowledge_sources、load_obsidian_documents、Retriever.retrieve、RAGService.retrieve_context/build_augmented_message；indexer。
- Inputs/outputs：query/domains、Markdown metadata → context/sources/chunks/used_rag/message。
- Dependencies/users：sentence-transformers、Chroma、SQLite FTS、filesystem；API knowledge route 消费。
- Storage/flow：internal knowledge + configured Vaults → chunks → indexes → rerank/diversity → model context。
- Permissions：access metadata 和来源边界存在；loader 保留 local-only，不能当作全部输出均已安全。实时访问撤回闭环待完善。
- Failure/status：API 可捕获检索异常继续推理；index 非 operational memory，无原子双索引保证。03 owns。旧 Vault-only 迁移记录仅描述其他快照。

## Audio Tools / 音频工具

- Owns：Windows default render endpoint 的 master volume 与 mute state；不拥有 UI、routing、permission policy、设备选择或 hardware-vendor control。
- Paths/interfaces：`skills/audio.py` 的 `get_volume`、`set_volume`、`volume_up`、`volume_down`、`mute`、`unmute`、`get_mute_state`。
- Inputs/outputs：integer percentage/step → existing dictionary ToolResult；成功返回 final actual `data`，失败返回 `{code, detail}` error。
- Dependencies/users：`pycaw` + `comtypes` Windows Core Audio；`app/main.py` registry、TaskRouter/API 调用。
- Permissions：`get_volume`、`get_mute_state` 为 READ；其它五个 action 为 LOW；所有调用仍经过 PermissionManager/TaskRouter。
- Validation/failure：0–100 level、1–100 step；不静默 clamp；非 Windows、缺少 backend、缺少 endpoint、COM/API failure 都显式 failed。
- Audit：每个 Audio operation 通过 `services/audit_logger.py` 的 `jarvis.audit` logger 记录脱敏 UTC event；不创建第二个 durable store。

## Brightness Tools / 亮度工具

- Owns：Windows WMI/CIM display brightness for the first supported display; does not own UI, routing, permission policy, display selection, or hardware-vendor control.
- Paths/interfaces：`skills/brightness.py` 的 `get_brightness`、`set_brightness`、`brightness_up`、`brightness_down`。
- Inputs/outputs：integer percentage/step → existing dictionary ToolResult；成功返回 final actual `data`，失败返回 `{code, detail}` error。
- Dependencies/users：fixed `powershell.exe` WMI/CIM commands；`app/main.py` registry、TaskRouter/API 调用。
- Permissions：`get_brightness` 为 READ；其它三个 action 为 LOW；所有调用仍经过 PermissionManager/TaskRouter。
- Validation/failure：0–100 level、1–100 step；不静默 clamp；非 Windows、PowerShell unavailable/timeout、unsupported display、invalid response 与 WMI/API failure 都显式 failed。
- Display boundary：当前公开接口使用第一个受支持 display；内部 selector boundary 接受 trusted `monitor_id`，但本 phase 不暴露多显示器选择。
- Audit：每个 Brightness operation 通过 `services/audit_logger.py` 的 `jarvis.audit` logger 记录脱敏 UTC event；不创建第二个 durable store。

## Wallpaper Tools / 壁纸工具

- Owns：Windows effective desktop wallpaper path 的读取与设置；不拥有 UI、routing、permission policy、动态壁纸/幻灯片、路径选择或 hardware-vendor control。
- Paths/interfaces：`skills/wallpaper.py` 的 `get_wallpaper`、`set_wallpaper`。
- Inputs/outputs：validated image-file path → existing dictionary ToolResult；成功返回 Windows read-back 的 effective `data.path`，失败返回 `{code, detail}` error。
- Dependencies/users：Python `ctypes` → User32 `SystemParametersInfoW`；`app/main.py` registry、TaskRouter/API 调用。
- Permissions：`get_wallpaper` 为 READ；`set_wallpaper` 为 LOW；所有调用仍经过 PermissionManager/TaskRouter。
- Validation/failure：只接受存在的 regular file、`.bmp`/`.jpg`/`.jpeg`/`.png` 扩展名与 matching basic signature；非 Windows、路径/格式错误、空 read-back 与 User32 failure 都显式 failed。
- Audit：每个 Wallpaper operation 通过 `services/audit_logger.py` 的 `jarvis.audit` logger 记录脱敏 UTC event；不创建第二个 durable store。

## Windows OS Theme Tools / Windows OS Theme 工具

- Owns：当前用户 Windows Personalize light/dark theme values；不拥有 JARVIS presentation theme、UI rendering、routing、permission policy、Night Light、accent color 或 per-application theme control。
- Paths/interfaces：`skills/theme.py` 的 `get_theme`、`set_theme`。
- Inputs/outputs：`light`/`dark` mode → existing dictionary ToolResult；成功返回两个 registry values 的 read-back 与 canonical `data.mode`，失败返回 `{code, detail}` error。
- Dependencies/users：guarded standard-library `winreg` → `HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize`；`app/main.py` registry、TaskRouter/API 调用。
- Permissions：`get_theme` 为 READ；`set_theme` 为 LOW；所有调用仍经过 PermissionManager/TaskRouter。
- Validation/failure：只接受 `light`/`dark`；缺失、非 REG_DWORD 0/1、application/system values mixed、非 Windows 与 registry read/write failure 都显式 failed。
- Audit：每个 Theme operation 通过 `services/audit_logger.py` 的 `jarvis.audit` logger 记录脱敏 UTC event；不创建第二个 durable store。

## System Status Tools / System Status 工具

- Owns：通过 `psutil` 按需读取 CPU、physical RAM、system-drive disk、uptime 与 basic battery 状态；Windows Battery Class detail reads additionally own optional mWh capacity/cycle-count acquisition。此模块不拥有桌面 monitor cache、后台采样、UI、routing 或 permission policy。
- Paths/interfaces：`skills/system_status.py` 的 `get_cpu_usage`、`get_ram_usage`、`get_disk_usage`、`get_system_uptime`、`get_battery_status`、`get_system_summary`。
- Inputs/outputs：六个无参数 READ operation → existing dictionary ToolResult；成功 `data` 为 structured metrics，失败为 `{code, detail}` error。
- Dependencies/users：existing `psutil` dependency；`app/main.py` registry、`app/api.py` schema、TaskRouter 调用。
- Permissions：六个 action 都是 READ、low risk、无需 confirmation；仍经过 PermissionManager/TaskRouter。
- Validation/failure：finite 0–100 percentages、non-negative byte counts、positive/consistent totals、non-negative uptime、valid battery shape 与 native Battery Class response layout；psutil/ctypes failure 或 malformed response 显式 failed，summary 不返回 CPU/RAM/disk/uptime partial data。无电池设备以 `battery_available: false`、null battery fields 显式返回；Battery detail hardware/driver 不支持时保留 `battery_details_available`、per-field availability、null capacity/cycle fields 与 `battery_details_error`。
- Audit：每个 System Status operation 通过 `services/audit_logger.py` 的 `jarvis.audit` logger 记录脱敏 UTC event；不创建第二个 durable store。
- Boundary：`get_battery_status` 的唯一 authoritative owner 已从 `skills/windows.py` 迁移到本模块；已有 `skills/system.py` 的 `get_system_info` 与 `services/system_telemetry.py` desktop monitor 保持既有边界。Electron Device 通过 `GET /api/system-status` → `get_system_summary()` 读取 structured snapshot；旧 `/api/system-info` surface 未改变。

## Native Tools and Registries / 原生工具与注册表

- Owns：有界 OS/project/file/git/Vault 操作与资源发现；不拥有高层 routing、权限自我批准或 model reasoning。
- Paths/interfaces：skills/system.py、system_status.py、project.py、git.py、files.py、audio.py、brightness.py、wallpaper.py、theme.py、windows.py、apps.py、power.py、window_manager.py、file_management.py、clipboard.py、network.py、bluetooth.py、audio_devices.py、media.py、input_control.py、obsidian.py；`services/tool_catalog.py`；services/app_registry.py、project_registry.py、audit_logger.py。
- Inputs/outputs：已声明参数（app/project/path/query/action/content）→ 工具文本或 dict；AVAILABLE_TOOLS 是当前可调用清单。
- Registry：`app/main.py` owns execution for 110 canonical tools across system/app, Audio, Brightness, Wallpaper, Theme, System Status, project/Git/files, Windows helpers, App/Power/Window/File/Clipboard/Network/Bluetooth/Audio Device/Media/Keyboard-Mouse controls, and Obsidian; `services/tool_catalog.py` owns their provider-neutral metadata. No `read_obsidian_note` registration exists. `search_files(query, root)` is local filename search and project text search is `search_project_files`; power actions use the canonical `lock_pc`/`sleep_pc`/`shutdown_pc`/`restart_pc` names.
  `open_app` 通过 `config/apps.json` 的已发现 Start Menu shortcut（例如 Google Classroom）执行；
  中文 `打开`/`启动` 可与名称直接相连，仍受 registry fuzzy lookup、shortcut 存在性与 PermissionManager 约束。
- Dependencies/users：Windows APIs/subprocess、配置 JSON、filesystem、Vault helpers；TaskRouter 调用。
- Storage/flow：注册资源 → 路径/输入校验 → OS/read/write → tool result；项目扫描更新 config/projects.json。
- Permissions：project/Vault boundary、protected paths、Obsidian write preview/confirmation；仅当前注册能力，不等于任意 shell/file editing。
- Failure/status：new PC-control adapters return structured success/failure with explicit unsupported-capability errors and no hidden fallback; older unrelated helpers in `skills/windows.py` retain their pre-existing string contracts until explicitly migrated. App registry refresh is explicit; `open_app` does not silently refresh it. 05 owns, knowledge-operation semantics coordinate with 04.

## Remaining Software PC-Control Adapters / 剩余软件级 PC 控制适配器

| Module | Owns / 负责 | Does not own / 不负责 | Main interfaces |
|---|---|---|---|
| `skills/apps.py` | Registered shortcut launch, process metadata, graceful app termination | Arbitrary executable paths, shell commands, force-kill policy | `open_app`, `list_running_apps`, `close_app` |
| `skills/power.py` | Fixed lock/sleep/shutdown/restart operations | Routing, confirmation, arbitrary power commands | `lock_pc`, `sleep_pc`, `shutdown_pc`, `restart_pc` |
| `skills/window_manager.py` | User32 window snapshot and bounded window state/position operations | UI rendering, routing, arbitrary window handles from model input | `list_windows`, focus/minimize/maximize/restore/close/move/resize/snap/topmost/show-desktop |
| `skills/file_management.py` | Validated regular-file operations, filename search, ZIP create/extract safety | Project text-search semantics, unrestricted directory deletion, overwrite | `open_file`, create/copy/move/rename/delete/search/zip/unzip |
| `skills/clipboard.py` | Unicode text clipboard read/write/clear | Arbitrary clipboard formats, persistent clipboard storage | `read_clipboard_text`, `write_clipboard_text`, `clear_clipboard` |
| `skills/network.py` | Fixed Wi-Fi/IP/gateway/DNS/ping/usage operations | Arbitrary network commands, provider selection | Wi-Fi, IP, gateway, DNS, `ping`, usage, `flush_dns` actions |
| `skills/bluetooth.py` | PnP Bluetooth discovery and bounded radio state operations | Generic per-device connect/disconnect, routing | status, on/off, list, explicit unsupported connect/disconnect |
| `skills/audio_devices.py` | pycaw endpoint discovery and default endpoint reads | Generic default endpoint selection until a stable setter exists | list/default input/output and explicit setter limitations |
| `skills/media.py` | Fixed foreground `WM_APPCOMMAND` transport messages | Current-player metadata, player selection, stale/fallback metadata | play/pause/next/previous/stop and explicit metadata limitation |
| `skills/input_control.py` | Bounded named-key, text, cursor, click, scroll, and drag input | UI automation, arbitrary virtual keys, permission decisions | `press_key`, `hotkey`, `type_text`, mouse actions |

All rows depend on `skills/_tool_support.py` for the shared structured result and audit boundary; they are invoked only through the registry and TaskRouter.

## Managed Luna and Direct Provider Integration / Managed Luna 与 Direct Provider 集成

- Owns：`services/ai_connection.py` 只选择 user-requested `managed_subscription`/`direct_api`，并在
  Direct API 中选择显式 provider/model；
  `codex_app_server.py` 只拥有 managed ChatGPT subscription Luna text transport；
  `openai_responses.py` 与 `direct_api_providers.py` 只拥有对应协议的 Direct API text submission。
  它们都不拥有 Python 执行权、task truth、
  Codex handoff 或 UI。遗留
  `services/agents/gemini.py` 仍拥有其旧 request/function-call protocol，但其 declarations 消费
  `services/tool_catalog.py`，不在 active chat path。
- Paths/interfaces：AiConnectionService.select_mode/set_direct_api_config/check_ready/read_account_usage/generate_response/snapshot；
  CodexAppServerAdapter.check_ready/read_account_usage/generate_response/stream_response、OpenAIResponsesAdapter.generate_response/stream_response、
  GeminiInteractionsAdapter.generate_response/stream_response、OpenAICompatibleChatAdapter.generate_response/stream_response、
  AiConnectionService.stream_response、AppServerState；`services/tool_catalog.py` 的 provider-neutral definitions。
  `luna_model.DEFAULT_LUNA_MODEL` 是 managed subscription 的 exact identifier SSOT；legacy Gemini adapter、jarvis_system_prompt.py。
- Inputs/outputs：最新用户文字与可选 owned transport mapping → managed exact `gpt-5.6-luna` 或
  user-selected Direct provider/model 的 success/status/result/error/tool_calls dict；`tool_calls` 必须为空。Core 只在保守本地操作
  gate 命中时附带当前 native catalog，模型最多返回可清理的 intent marker；candidate 不属于
  adapter authority。
- Dependencies/users：packaged Internal Test 使用随包的 Windows x64 `resources/core/codex/codex.exe`；development
  mode 使用显式 `JARVIS_CODEX_COMMAND`、用户 `%APPDATA%/npm/codex.cmd` 或既有 `codex.cmd` contract。两者都需要
  official managed ChatGPT login，或 OpenAI Responses、Gemini Interactions、DeepSeek/OpenAI-compatible Chat
  Completions API；app/main.py 与 API。Direct key 只在 Core process memory，不返回、日志或 persistent storage，
  Codex credentials 也不会进入安装包。
- Storage/flow：Electron 首次 Core online 的 `aiCheck` 或第一条真实请求会让 adapter 持有 empty
  temporary CWD + `:read-only` profile，完成 initialize/account/model/profile 校验后常驻同一 Core
  生命周期；Core/Memory mapping → local App Server `thread/start`（要求 `ephemeral: true` 且返回值
  必须确认 ephemeral）或同一 resident child 的 `thread/resume` → `turn/start` → text result。
  后续请求复用同一健康 child/session 与已验证 handshake，不重复初始化；同一 resident child 中
  developer-instruction context 未变化的已验证 thread 会跳过重复 `thread/resume`。JARVIS child 显式
  使用 low reasoning effort，不修改用户全局 Codex 配置。owner、version 或 auth hash 不符会显式
  拒绝 resume；child/Core restart 后不把过期 ephemeral mapping 送回 Codex，而是按明确生命周期创建
  新的 ephemeral thread。不会把 Vault/project/screen/RAG/native capability 传给模型。child 崩溃、
  协议/权限/认证失败或 timeout 会清除 resident 状态且不重发未知 turn；下次新请求才重新验证。
  Core shutdown 与 mode boundary 只清理/失效 adapter-owned 资源。`read_account_usage()` 在同一 managed
  child 上调用官方 `account/usage/read`，只返回去敏的 summary/date buckets；Direct API 不调用该 RPC，
  而由各自 response 的明确 usage DTO 负责 usage 展示。当前 ChatGPT cloud Jarvis Chat
  project 不可被本机 App Server `project/read` 识别，未宣称绑定。
- Streaming flow：选定 adapter 读取其原生 SSE/JSONL 事件，只将文本 delta 暴露给
  `TaskRouter.execute_external_action_stream()`；TaskManager 负责 running/completed/cancelled 记账，API
  生成 terminal response/history。关闭 generator 会显式关闭 upstream；managed App Server 发送
  `turn/interrupt`，Direct HTTP 保留网络错误/取消状态，不切换 provider 或 mode。
- Permissions：Core retains policy. App Server 启动时禁用 MCP/plugins/browser/computer use；禁止项
  fail closed，model 不能调用 JARVIS tools。Luna marker 仅是 untrusted suggestion，经过 API
  shared validator 与 TaskRouter 的风险决策：低风险候选走正常允许路径，中高风险候选进入
  confirmation；普通问答不请求 marker。
- Failure/status：Core health 与 selected AI snapshot 分开。Direct no-key/auth/model/rate/network/service
  failures结构化且 explicit；不回退其他 provider/model 或另一 mode。Gateway 仅接受没有凭据、query/fragment、
  local host 或 private IP 的 HTTPS base URL，且 JARVIS 只在其后追加 `/chat/completions`。Windows start hides only
  adapter-owned App Server cmd child; stdout/stderr 持续 drain，shutdown 只终止 adapter 自己创建的 tree。
  safe phase timing 通过 response metadata 与 `[JARVIS_TIMING]` 输出提供 lock/spawn/handshake/thread/turn/
  total、`thread_resume_skipped` 与 `thread_recreated`；`connection_check` 只记录握手阶段，仍可能没有 response token；实际 streamed turn
  的首 delta 由 renderer `firstModelTokenAt` 记录；不含消息、token、账号或密钥。01 owns long-term
  semantics；90 is the scoped integration writer for this package。若同一 resident ephemeral thread 明确
  报告 active-writer/thread-store conflict，仍为 `session_busy`：提示另一 Codex client 占用且不创建
  replacement thread；其他 errors 不由此翻译或 fallback。ephemeral transport 不应物化为 ChatGPT
  sidebar chat；旧条目不由 JARVIS 自动删除，最终列表状态需由用户 Desktop 观察。
  `user_disconnected` 是 Core-owned、非敏感 status 位：用户显式断开后 Electron 健康轮询不得自动调用
  managed reconnect；只有用户选择 mode、输入 Direct API key 或点击 refresh 才重新允许检查。该意图仅存活于当前 Core 生命周期。

## Desktop UI / 桌面呈现

- Owns：Assistant/Tasks/Device/Settings/Errors、DTO、交互；不拥有 SQL、权限决定或 OS 执行。
- Paths/interfaces：desktop_ui/lib/main.dart、workspace_pages.dart、jarvis_api.dart JarvisApi.createConversation/sendMessage/health/telemetry/conversationHistory；runtime_monitor、error_log。Electron `renderer/motion.html`/`unified.js` 通过 fixed IPC 消费 Core surfaces。
- Inputs/outputs：用户消息/选择、HTTP DTO → widgets、confirmation cards、citations、request。
- Dependencies/users：Flutter、HTTP、SpeechController；由桌面 launcher 启动供用户使用。
- Storage/flow：页面 state/历史 archive、opaque Core conversation ID、API conversation history；不是 persistent worker/coding-memory UI，也不展示或管理 App Server/Codex thread。
- Permissions：用户交互交给 Core；卡片不证明 backend authorization 已完成。
- Failure/status：连接错误、offline/stale 状态与 Errors 记录；M1.1 widget
  regression 验证 awaiting 和 terminal denied 都不会进入 Error log 成为 false
  failed。当前 pending native action group 只提供 `Yes, continue` / `No, cancel` controls；denied 结果
  在 Chat 保留 assistant reply，结构化证据仍位于 Tool Results 页面；它们
  只向既有 Core conversation endpoint 发送 `yes`/`no`，终态后消失，不能直接执行工具。11 owns，
  公共 UI 入口按 90 single-writer。pending confirmation 存在时不能新建 UI conversation，防止跨会话确认。
- Electron AI connection controls use one two-column action row: equal-width 48px controls, a 12px
  row gap, then 18px to the status and 14px to the explanatory note. This is presentation-only and
  does not alter Core connection state or transport policy.
- Electron Core connection page uses fixed jarvis-core-health for Refresh and
  jarvis-core-reconnect for Reconnect Core. The latter delegates to the main-process
  CoreSupervisor.ensureReady() single-owner promise, reuses a ready listener, or starts only the
  current edition's owned child when the port is offline; non-ready/failed startup remains explicit.
  The page continuously polls health every 2 seconds, displays the latest check time, and keeps its
  Refresh/Reconnect controls in a separate row below the description. The page does not send chat turns, create conversations, accept endpoint parameters, or kill unknown
  processes.
 - Electron keeps `AI connections` as an inspector, while `Token usage` is a Feature page plus a compact
  three-metric preview widget in a dedicated Core-stage top slot sharing the Chat/Feature top anchor (the preview is persistent and has no close control, the Core canvas remains centered in its own stage region, and the widget has no internal scrollbar). The compact widget reads only renderer-owned
  `jarvis.foreground.token-usage.v1.{edition}` `tokenUsageRecords` created by JARVIS responses with
  `source: provider_reported`; it shows Input/Output/Total values in compact k/M form and has no
  heatmap or trend chart. Managed Luna supplies current-turn deltas from the owned ephemeral thread's
  `thread/tokenUsage/updated` cumulative totals; Direct API supplies provider response usage. Managed ChatGPT account summary/daily buckets from `account/usage/read` remain
  on the explicit Feature page through the separate
  `jarvis.foreground.chatgpt-account-usage.v1.{edition}` localStorage snapshot; those account buckets never
  enter the widget because they cannot distinguish JARVIS from the user's other Codex usage. In Direct API
  mode, terminal provider-reported input/output/total counts refresh the widget and Feature page through the
  provider store after each reported response; Managed turn deltas refresh the JARVIS widget through the same
  store. The full Feature trend draws X-axis date ticks and Y-axis token
  scale labels; each plotted point supports pointer hover and keyboard focus to reveal its date and compact k/M
  value. The active source is selected by connection mode; values are never mixed and missing input/output
  fields are not inferred. `GET /api/settings/ai/usage` reports explicit `not_supported` for Direct API because
  providers expose response usage rather than one portable account RPC. Account balance, quota, and billing remain
  unimplemented. In Direct API mode,
  the connection page renders a provider-specific, text-only model-ID catalog under the action row. The
  catalog is protocol guidance, not a live account/model availability check; OpenAI-compatible gateways
  intentionally have no fixed list.
- Direct provider/model form changes are local dirty drafts until `aiDirectConfig` succeeds. Health
  snapshots cannot overwrite an unsaved draft with the previous Core provider; after a successful
  config submission, Core becomes authoritative again. This prevents the two-second health poll from
  reverting a user-selected adapter to OpenAI.
- Electron separates `Device` and `Working context` Pages. Device only loads the existing read-only
  system-info surface. Working context only loads the registered-project registry and its bounded
  Git/file/search inspection actions; it remains available in the `development` edition and is hidden
  from the explicit `internal-test` edition, including direct hash routing. It is not automatically
  attached to chat messages.
- Electron also separates `Events` and `Errors` Pages. Both views reuse the same bounded renderer
  `eventRecords` store: `Events` renders existing non-`error` lifecycle/recovery records, while `Errors`
  renders only records with the existing `error` level. Each page has an independent clear action; no new
  Core endpoint, persistence, error translation, or fallback is introduced.
- Electron Knowledge/Obsidian controls now use the fixed `obsidianVaults`, `obsidianConnect`, and
  `obsidianDisconnect` bridge operations. `Refresh connection` performs the existing metadata check;
  Connect / reconnect explicitly submits a user-provided vault name and full folder path to the existing
  Core registration endpoint with `default_access=excluded`; Disconnect removes only JARVIS registration
  and keeps user Vault files. The renderer never scans a path or stores the path, and an unavailable Core
  bridge remains an explicit failure.
- The Pages launcher keeps one short, single-line `.nav-label` under every declared icon. Its expanded
  button row, grid spacing, responsive 380/360/340px dock widths, and rounded rectangular surfaces make
  labels and page content readable in both editions; the compact launcher is labeled `Feature`, and
  the internal-test edition exposes Voice through its explicit allowlist. Rounded cards share a crisp
  isolated paint boundary; the outer launcher/inspector transition uses opacity and integer-pixel
  translation without blur or fractional scale, while page-content transitions use bounded
  `page-header-enter`/`page-view-enter` fade, translation, and blur. No
  route, bridge, permission, or inspector contract changes here.

## Voice Output / 语音输出

- Owns：reply TTS/stop；不拥有 STT、wake、voice identity、自动授权或 scheduler。
- Paths/interfaces：services/windows_speech_service.py、fish_speech_service.py；API `/api/system-speech`、`/api/system-speech/voices`、
  `/api/system-speech/settings`、`/api/system-speech/stop`、`/api/system-speech/synthesize`、`/api/speech`；Flutter SpeechController.speak/stop。
- Electron preview 通过固定 `speechSettings`/`speechVoices`/`speakReply`/`stopSpeech`/`synthesizeSpeech` IPC 复用 Windows system speech；Settings 显示真实
  Windows voice settings（缺少可选 per-user registry settings 时返回 Windows default），both editions' Voice inspectors list and select Windows OneCore voice packages and provide Test voice；
  自动朗读默认关闭，开启后消费 streamed narration chunks，不提供消息级手动朗读按钮。
- Inputs/outputs：text/provider → Windows playback 或 Fish Audio WAV bytes。
- Dependencies/users：Windows voice、Fish remote service、Flutter audio；Assistant/settings 调用。
- Storage/flow：`jarvis.auto-speech.voice.v1` 只在当前 Electron edition local profile 保存 voice ID；空值使用 Windows default。当前音频状态与供应商配置
  不是长期 knowledge；指定 voice 不可用时保留显式错误，不静默换语音。
- Language matching：renderer 使用本地 Han/Latin heuristic 检测回复语言；中文先保留用户选择的中文 voice，否则选择已安装列表中的第一个
  `zh-CN`、再选择其它 `zh-*` voice。英文/其它文字继续使用当前选择。voice inventory 在 Core ready 后异步加载，单个 streamed response
  在第一个可见文字后固定 voice ID，所有 queued speech chunks 复用该 ID；检测不增加模型请求延迟。没有中文 package 时保留当前 voice 并记录显式提示。
- Permissions：Fish 会发送朗读文本到外部，Windows 路径本地；provider 选择不授权其他操作。
- Output protocol：Core 文本 transport 仍要求 `[DISPLAY]` + `[VOICE_EN]` 双区块；API/renderer 分离并显示 display 正文，
  `renderer/markdown-renderer.js` 以无依赖、DOM-only subset 渲染标题、段落、列表、强调、引用和代码，并拆分常见的同一行递增编号项目；raw HTML/不安全链接不执行。
  Automatic speech 不消费协议标签或 presentation Markdown；streamed turn 先消费已显示 response text 的清理后 chunks，
  `DisplayPacer` 只以默认约 42 chars/s 控制 DOM reveal，不改变 Core/provider/TTS 生成速度；terminal response 仍保留 `speech`
  narration，且不会重复消费同一 response；streamed turn
  的 `requestReceivedAt`、`firstModelTokenAt`、`firstTextRenderedAt`、`firstSpeechChunkCreatedAt`、
  `firstTtsAudioReadyAt`、`firstAudioPlaybackAt`、`responseCompletedAt` 与 derived fields 由 renderer
  记录在当前 response metadata，不写入独立 durable telemetry store。
- Failure/status：错误映射到 API/UI；未实测音频，voice input/wake/barge-in 不是当前完整能力。08 owns。

## Telemetry / 设备遥测

- Owns：CPU/memory/可选 GPU 快照；不拥有工作上下文、屏幕观察、presence/通知决策。
- Path/interface：services/system_telemetry.py read_system_telemetry；GET /api/telemetry。
- Inputs/outputs：请求 → metrics/availability；used by Flutter runtime_monitor/Device。
- Dependencies/storage：系统指标与可选 NVIDIA tooling、短期进程缓存，不写个人知识库。
- Flow/permissions：本机读指标 → API → UI；无控制机器行为。
- Failure/status：可选指标缺失应呈现 unavailable，不能补造数值；本次未对真实 GPU 验收。
