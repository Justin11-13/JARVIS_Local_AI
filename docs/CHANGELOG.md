# Changelog / 改动时间线

## 2026-09-14 — Electron Internal Test Update Notice and Rebuild Handoff (IMPLEMENTED — source/static/Node/package verified)

Internal Test Electron now checks the fixed GitHub Releases API once after startup and exposes
`Settings → Application updates → Check now`. Only a newer published Release with the exact
`JARVIS-Internal-Test-<version>-Setup.exe` asset shows `UPDATE AVAILABLE`; `Download update` opens the validated
Release page and never silently downloads, installs, or restarts. The source package is now kept under
`electron_motion_preview_internal_test/` with `packaging/` build scripts; generated binaries remain Release assets.
The final rebuilt installer is `816,647,011` bytes with SHA-256
`3501645D93FF9A73402998488A0BA4D90E470F919F8563CCA4501FD17E4EE8B3`; the Electron Node suite passed `64/64`.
The unsigned package could not be launched on this host because Windows Application Control blocked the generated
Core/Electron binaries; no policy bypass was attempted. Details: [Electron Internal Test Update Notice](prompts/feature/20260914-FEAT-electron-update-notice.md)
and [Electron + JARVIS Core Windows Packaging](info/05-integrations/ELECTRON_CORE_PACKAGING.md).
The bilingual README now links to the published `v0.1` asset and records the same final checksum.

## 2026-09-14 — Electron Custom Theme Palette (IMPLEMENTED — source/static/Node verified; package handoff pending)

两套 Electron edition 的 Theme page 新增本地调色盘，用户可即时调整 background、surface、border、accent、text、muted、Core A 与 Core B，颜色经过白名单与 `#RRGGBB` 校验后保存到 edition-local storage，并可 Reset 回四个既有 preset。CSS token 与 hologram Core palette 继续通过既有 renderer contract 同步；未改变 Core/API、bridge、权限或 package dependency。两套 static verifier、Node suite 均通过 `59/59`，`unified.js` syntax check 通过；正常 Electron visual 与安装包重打包交由 release handoff。详情见 [Electron Custom Theme Palette](prompts/feature/20260914-FEAT-electron-custom-theme-palette.md)。

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
