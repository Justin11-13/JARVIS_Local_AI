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
| General question, research, or response that benefits from ChatGPT web search / 一般问题、研究或需要 ChatGPT 网页搜索的回答 | ChatGPT UI executor / ChatGPT 界面执行器 | Use the visible, signed-in ChatGPT interface; no GPT API / 使用已登录的可见 ChatGPT 界面；不使用 GPT API |
| Large codebase task, debugging, implementation, refactor, or test loop / 大型代码库任务、调试、实现、重构或测试循环 | Codex executor / Codex 执行器 | Hand off to authenticated Codex; JARVIS still owns permissions / 交给已认证 Codex；权限仍由 JARVIS 管理 |

All state-changing, destructive, privileged, or externally submitted actions
must pass the Python permission layer. An AI suggestion is never authorization.

## 2. ChatGPT UI Flow / ChatGPT 界面流程

```text
User request
        ↓
TaskRouter classifies intent and data scope
        ↓
External submission needed?
  ├─ Yes: show exactly what will be sent and require confirmation
  └─ No: reject or use a native tool
        ↓
Open the authenticated ChatGPT desktop/browser UI
        ↓
Submit the approved prompt and wait for the visible response
        ↓
Return the visible result and citations to JARVIS
```

The executor must not intercept private web traffic, reuse session cookies,
bypass CAPTCHA, automate credentials, or silently fall back to another AI.

## 3. Reused Foundation / 复用现有基础

- `services/task_router.py` remains the routing and policy decision point.
- `services/task_manager.py` remains the task lifecycle/history point.
- Native Windows/project tools and the FastAPI/Flutter desktop bridge remain
  the local foundation.
- Existing logging and desktop error reporting remain the diagnostic path.

## 4. Phased Delivery / 分阶段实施

### Phase 1 — Unified permission gate / 统一权限闸门

- Keep one action request/result schema covering executor, purpose, data scope,
  risk, required confirmation, and audit-safe summary.
- Require confirmation before state-changing native actions or external text
  submission.
- Reject unsupported actions rather than silently selecting another executor.

### Phase 2 — Direct lightweight executor / 直接轻量执行器

- Reuse native skills and add only explicit, narrow commands.
- Validate executable, arguments, target paths, project registration, and
  working directory before execution.
- Record safe result and failure summaries without logging secrets.

### Phase 3 — ChatGPT UI executor v1 / ChatGPT 界面执行器 v1

- Use supported visible UI/browser control only after consent.
- Store a minimal structured result: outcome, visible text, citations,
  timestamps, executor status, and error reason.
- Cover confirmation, timeout, cancellation, unavailable session, and visible
  result parsing with tests.

### Phase 4 — Codex executor v1 / Codex 执行器 v1

- Use a supported Codex hand-off mechanism for repository-scale work.
- Preserve project registry and permission boundaries.
- Surface task progress, final result, and test evidence in JARVIS.

### Phase 5 — Unified desktop tasks and observability / 统一桌面任务与可观测性

- Display selected executor, status, approval request, citations, and safe error
  details in Assistant and Tasks.
- Keep telemetry independent from AI-backend availability.

## 5. Explicit Non-Goals / 明确不做的事

- No Ollama, Qwen, local model download, local model server, or model manager.
- No OpenAI/GPT API, API key, API proxy, or hidden web endpoint.
- No unrestricted shell, PowerShell, administrator, file-write, Git, browser,
  or desktop control granted to an AI.
- No silent external prompt, attachment, clipboard, source-code, or secret
  upload.

## 6. Implementation Order / 实施顺序

Implement and test one phase at a time. The taskbar/API lifecycle and telemetry
are separate local foundations; an unavailable AI executor must never make CPU,
memory, or GPU monitoring report `N/A` when the local API is healthy.
