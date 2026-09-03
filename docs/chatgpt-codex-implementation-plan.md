# JARVIS ChatGPT UI + Codex Implementation Plan

> Status / 状态: proposed implementation plan, not an implemented executor.
>
> This replaces the local-model direction. It does not add Ollama, Qwen, any
> local LLM, or a GPT API client.

## 1. Product Decision / 产品决定

JARVIS remains the local coordinator and safety boundary. It chooses a small,
scoped executor only after Python policy has classified the request and, where
needed, obtained confirmation.

| Request type / 请求类型 | Executor / 执行者 | Boundary / 边界 |
| --- | --- | --- |
| Simple Windows operation, telemetry, registered-project inspection, or a known safe command / 简单 Windows 操作、监控、已注册项目检查或已知安全命令 | Direct Python or PowerShell / 直接 Python 或 PowerShell | Native allowlist, validated arguments and paths / 原生白名单、验证参数与路径 |
| Bounded lightweight local workflow that native tools cannot cover / 原生工具无法覆盖的受限轻量本地流程 | Open Interpreter, on demand / 按需 Open Interpreter | Keep the existing workspace, mode, risk, and confirmation guards / 保留现有工作目录、模式、风险与确认保护 |
| General question, research, or response that benefits from ChatGPT web search / 一般问题、研究或需要 ChatGPT 网页搜索的回答 | ChatGPT UI executor / ChatGPT 界面执行器 | Use the visible, signed-in ChatGPT interface; no GPT API / 使用已登录的可见 ChatGPT 界面；不使用 GPT API |
| Large codebase task, debugging, implementation, refactor, or test loop / 大型代码库任务、调试、实现、重构或测试循环 | Codex executor / Codex 执行器 | Hand off to authenticated Codex; JARVIS still owns permissions / 交给已认证 Codex；权限仍由 JARVIS 管理 |

**Non-negotiable rule / 不可妥协规则:** all state-changing, destructive,
privileged, or externally submitted actions must pass the Python permission and
risk layer. An AI suggestion is never authorization.

## 2. ChatGPT UI Flow / ChatGPT 界面流程

The requested `open GPT → enter request in the visible search/chat bar → fetch
results` workflow is implemented only through the user-facing UI, never through
a GPT API.

```text
User request / 用户请求
        ↓
TaskRouter classifies intent, risk, and data scope / TaskRouter 分类意图、风险、数据范围
        ↓
External submission needed? / 是否需要向外部提交？
  ├─ Yes: show exactly what will be sent and require confirmation
  └─ No: reject or use a local executor
        ↓
Open the authenticated ChatGPT desktop/browser UI / 打开已认证的 ChatGPT 桌面或浏览器界面
        ↓
Enter the approved prompt in the visible composer/search bar / 在可见输入栏填入已批准的请求
        ↓
Wait for the visible response and citations / 等待可见回复和引用
        ↓
Fetch visible result into a structured task record / 将可见结果提取为结构化任务记录
        ↓
Display result, citations, source, and limits in JARVIS / 在 JARVIS 显示结果、引用、来源和限制
```

`fetch results` means reading the final visible UI response and its visible
citations after completion. It must not intercept private web traffic, reuse a
session cookie, bypass a CAPTCHA, or automate credentials. The user remains in
control of the signed-in ChatGPT session. ChatGPT's own UI supports web search
and displays cited results in the conversation; see the [OpenAI web-search
documentation](https://learn.chatgpt.com/zh-Hans/docs/web-search).

### Data and confirmation / 数据与确认

- Read-only local requests can be prepared locally, but sending text, files,
  screenshots, clipboard data, project code, or secrets to ChatGPT is an
  external submission and requires per-request confirmation.
- The confirmation card must show the selected executor, exact prompt or
  attachment summary, destination, risk level, and expected state change.
- The executor must return a clear `cancelled`, `blocked`, or `not configured`
  result rather than silently falling back to another AI service.

## 3. Reused Foundation / 复用现有基础

The migration builds on existing code instead of recreating JARVIS:

- `services/task_router.py` remains the routing and policy decision point.
- `services/task_manager.py` remains the task lifecycle/history point.
- `services/agents/open_interpreter.py` remains the Open Interpreter adapter.
- Existing Open Interpreter workspace validation, `manual` / `ask` /
  `automatic` modes, risk classification, confirmation flow, and project
  registry guard remain in force.
- Native Windows/project tools and the FastAPI/Flutter desktop bridge remain
  the local foundation.
- Existing logging and desktop error reporting remain the diagnostic path.

## 4. Phased Delivery / 分阶段实施

### Phase 1 — Unified permission gate / 统一权限闸门

**Goal / 目标:** make Python policy the mandatory gate for native tools, Open
Interpreter, ChatGPT UI, and Codex before adding new executors.

- Define one action request/result schema: executor, purpose, data scope, risk,
  required confirmation, and audit-safe summary.
- Extend the existing risk policy to direct Python/PowerShell actions and every
  external UI submission.
- Keep existing Open Interpreter behaviour compatible; do not weaken its modes
  or workspace guard.
- Return a pending-confirmation task rather than running a state-changing
  action immediately.

**Acceptance / 验收:** unit tests prove that file writes, installs, deletes,
admin commands, Git commit/push, browser/UI submissions, and Codex execution
cannot start without the required confirmation.

### Phase 2 — Direct lightweight executor / 直接轻量执行器

**Goal / 目标:** use direct Python/PowerShell for predictable small operations
instead of paying an AI-agent cost.

- Reuse native skills where present; add only explicit, narrow commands.
- Validate executable, arguments, target paths, project registration, and
  working directory before execution.
- Support dry-run/preflight results where meaningful.
- Record command summary, result, duration, and failure in the existing task
  and logging systems; never log secrets.

**Acceptance / 验收:** supported read-only actions run locally; unsupported
commands are rejected or routed for confirmation; invalid paths and shell
metacharacters cannot bypass validation.

### Phase 3 — Open Interpreter refinement / Open Interpreter 精简化

**Goal / 目标:** keep Open Interpreter as an on-demand, bounded local executor
for lightweight flexible work—not as the main reasoning brain.

- Preserve the current adapter and its existing modes.
- Add a clear router reason when it is selected over direct native execution.
- Limit inputs to an approved workspace and report its command/output summary.
- Route broader reasoning away from Open Interpreter to ChatGPT UI or Codex.

**Acceptance / 验收:** current Open Interpreter tests continue to pass; manual,
ask, and automatic mode decisions remain deterministic and confirmation works.

### Phase 4 — ChatGPT UI executor v1 / ChatGPT 界面执行器 v1

**Goal / 目标:** deliver the approved visible-UI workflow with no GPT API.

- Add a `ChatGPTUiExecutor` adapter under `services/agents/`.
- Use supported local UI/browser control only after consent; open an existing
  signed-in ChatGPT surface, paste the approved prompt, wait, and fetch the
  visible completed answer/citations.
- Store only a minimal structured result: outcome, visible text, citations,
  timestamps, executor status, and error reason.
- Do not automate login, password entry, CAPTCHA handling, hidden DOM/network
  access, or file uploads without a new explicit confirmation.

**Acceptance / 验收:** mock adapter tests cover prompt confirmation, timeout,
cancel, unavailable signed-in session, and visible result parsing. A supervised
manual test confirms that the UI opens, submits only the approved text, and
shows fetched results/citations in JARVIS.

### Phase 5 — Codex executor v1 / Codex 执行器 v1

**Goal / 目标:** hand off repository-scale work to authenticated Codex without
embedding a GPT API key.

- Add a narrow Codex adapter under `services/agents/` using a supported local
  Codex hand-off mechanism.
- Pass approved repository context and a task brief; preserve project registry
  boundaries.
- Surface proposal, commands/actions requested, progress, final result, and
  test evidence in JARVIS tasks.
- Require JARVIS confirmation before any state-changing Codex action; do not
  equate a Codex recommendation with permission.

**Acceptance / 验收:** a fixture repository can be inspected and a proposed
change returned, but writes/test commands/commits remain blocked until the user
approves them. The UI presents a clear unavailable state when Codex is not
configured.

### Phase 6 — Unified desktop tasks and observability / 统一桌面任务与可观测性

**Goal / 目标:** make executor choice and permission state understandable in the
Flutter UI.

- Display selected executor, status, risk, approval request, visible source
  links/citations, and safe error details in Assistant and Tasks.
- Persist only the minimum user-approved task history after a separate privacy
  decision.
- Keep telemetry independent from AI-backend availability.

**Acceptance / 验收:** closing/opening the desktop app manages its local API as
documented; CPU/RAM/GPU telemetry continues when ChatGPT/Codex is unavailable;
each executor failure is distinguishable in Errors.

### Phase 7 — Later capabilities / 后续能力

Voice, screenshots, system tray/background lifecycle, notifications, and
documented hardware integrations come only after the permission model and the
four executor paths are stable.

## 5. Explicit Non-Goals / 明确不做的事

- No Ollama, Qwen, local model download, local model server, or model manager.
- No OpenAI/GPT API, API key, API proxy, or hidden web endpoint.
- No unrestricted shell, PowerShell, administrator, file-write, Git, browser,
  or desktop control granted to an AI.
- No silent external prompt, attachment, clipboard, source-code, or secret
  upload.
- No replacement of the existing task, routing, Open Interpreter, logging, or
  project-registry foundations without a demonstrated conflict.

## 6. Implementation Order / 实施顺序

Implement and test one phase at a time. Phase 1 is the smallest required code
change and must be stable before Phase 2 begins. The taskbar/API lifecycle and
telemetry are separate local foundations; an unavailable AI executor must never
make CPU, memory, or GPU monitoring report `N/A` when the local API is healthy.
