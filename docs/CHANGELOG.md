# Changelog / 改动时间线

## 2026-09-14 — Internal Test README and Phase Scope (IMPLEMENTED)

根目录 README 已改为中英双语，并以内测版 Electron + packaged Core 为主要入口；补齐 Windows 安装、Managed ChatGPT、Direct API、可选 Obsidian、源码构建、安全边界和真实限制，同时将未来方向按权威 Target Architecture 的 Phase A-C 分开标为计划；Phase D 继续明确为未授权。此次仅修改文档，不改变运行时。详情见 [Internal Test README and Phase Scope](prompts/documentation/20260914-DOCS-internal-test-readme-and-phases.md)。

## 2026-09-12 — Electron source candidate and clean setup

Status: `IN PROGRESS` — candidate validation; not a verified release.

- Added the manifest-approved Electron/Core/API/AI source snapshot to branch
  `codex/electron-source-candidate-20260912` without copying the main checkout
  wholesale.
- Added `setup.ps1`, `run-new-ui.ps1`, and the captured Python
  `requirements.lock.txt` for fresh-clone setup and the New Electron entrypoint.
- Verified `npm ci`, Electron static verification, and 34 Node tests; created a
  clean Python 3.12.14 venv, installed the locked dependencies, and passed
  Python compile checks.
- The first focused Python run found one test-only `jarvis_memory` import-scope
  error. The correction was included as a separate post-freeze delta with its
  updated hash; the full Python test discovery now passes 156/156.
- The original 45-file fingerprint remains historical. The final candidate
  fingerprint still needs to be recalculated after the source set is frozen.
- npm audit identified three high-severity dependency-node findings for
  `extract-zip@2.0.1` through Electron and the packager; npm reports no fix and
  `npm audit --omit=dev` reports zero findings. No forced fix was applied.
- The current 45-file source-set fingerprint is
  `725AA519938A80A5330B40A20FE691C5D6187C60398901D77F2279E54A775D7E` using
  the documented path-sorted `path<TAB>sha256` input. Electron's real
  `run-new-ui.ps1 -Verify` remains blocked on this host by GPU exit
  `0xC0000135`, cache ACL refusal, and renderer `ERR_FAILED`; no workaround was
  introduced.
- A short Core smoke returned `/api/health` with `core.status = ready` and AI
  `not_checked`; no account check or inference was performed, and the listener
  was stopped afterward.
- Managed login/model access, Core/Luna/confirmation smoke, audio, GPU/ACL
  behavior, and internal-package distribution remain explicit acceptance or
  environment gates. No credentials, `.venv`, `node_modules`, logs, or private
  runtime data are included.

See [`20260912-DOCS-electron-source-candidate.md`](prompts/documentation/20260912-DOCS-electron-source-candidate.md).

## 2026-09-10 — README New UI-first reconciliation

Status: `IMPLEMENTED` — documentation only. No runtime or source replacement
was performed.

- Rewrote the GitHub README around the current clean baseline and its real
  implementation boundary.
- Documented the New Electron UI as the primary development direction and the
  Legacy Flutter UI as the runnable compatibility path.
- Added explicit status labels for implemented, preview, planned, and out of
  scope work; documented the Phase A–C target without presenting it as current
  behavior.
- Added verified baseline dependencies, setup/build/run/stop/check commands,
  AI billing and subscription boundaries, security/privacy rules, and the
  missing-Electron-source limitation.
- Kept existing Legacy screenshots as examples and did not invent New UI
  screenshots, badges, benchmark numbers, or runtime claims.

See the task record:
[`20260910-DOCS-readme-current-state-reconciliation.md`](prompts/documentation/20260910-DOCS-readme-current-state-reconciliation.md)
