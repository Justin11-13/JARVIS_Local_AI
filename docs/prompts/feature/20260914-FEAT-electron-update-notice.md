# Electron Internal Test Update Notice

- Date: 2026-09-14
- Type: FEAT
- Status: IMPLEMENTED — source/static/Node verified; live packaged remote-release UI acceptance remains pending
- Owner: Electron Internal Test update flow

## Original Request / 原始需求

用户希望 JARVIS 能检测是否有新版本，让用户知道有更新，并让用户进入更新流程。

## Goal / 目标

为可下载的 Electron Internal Test package 增加有界的版本检查、用户可见的更新通知，以及打开可信 Release 下载页面的显式操作。

## Scope / 修改范围

- Electron Internal Test main process 的固定 GitHub Release update check。
- preload 的最小 update bridge，不把任意网络请求或 URL 控制权交给 Renderer。
- Renderer 的启动后检查、Settings 手动检查、更新通知、稍后隐藏和打开下载页面。
- 无依赖的版本比较与 Release payload validation tests。
- Internal Test package 文件清单与当前文档、CHANGELOG。

## Non-Goals / 非目标

- 不修改 JARVIS Core API、AI、权限、RAG、用户数据存储或 Theme 行为。
- 不实现静默下载、静默安装、差分更新或自动重启。
- 不把 development edition 自动升级到 Internal Test channel。
- 不执行 Git push、tag 或 GitHub Release；这些仍由 91 - Git & Release 负责。

## Before / 修改前

- Electron package 没有 update checker、update IPC 或用户可见 update notice。
- `connect-src` 保持 `none`，Renderer 没有直接 HTTP 网络权限。
- Internal Test installer 是 Electron + bundled Core 的 NSIS package；Release asset 名称为 `JARVIS-Internal-Test-<version>-Setup.exe`。

## Investigation / 调查

- `electron_motion_preview_internal_test/main.cjs` 是 packaged Core lifecycle 与 IPC owner。
- `preload.cjs` 暴露固定、逐项 allowlisted bridge；Renderer 通过 `window.jarvisCore` 消费它。
- Settings 页面已有手动控制与 status pattern，Chat header 适合放非阻塞的 update notice。
- 当前 repository origin 是 `Justin11-13/JARVIS_Local_AI`；Internal Test update check 将只接受 HTTPS GitHub Release URL 与匹配的 Internal Test Windows installer asset。

## Decision / 决策

使用 GitHub Releases API 的非阻塞检查：启动时检查一次，Settings 可手动再次检查；只有发现比当前 `app.getVersion()` 更新且带有匹配 NSIS asset 的 Release 才显示 notice。点击 `Download update` 后由 main process 打开已验证的 Release 页面。检查失败、未发布 Internal Test asset、旧版本和不支持的运行环境均保持不同且可见的状态。

## Implementation / 实现

- Added `electron_motion_preview_internal_test/update-checker.cjs` with bounded GitHub Releases fetching, semantic-version comparison, Internal Test installer asset selection, HTTPS GitHub URL validation and explicit failure states.
- Added main-process `jarvis-update-check` and `jarvis-update-open` handlers. The main process owns network access and opens only the Release URL returned by the validated checker; Renderer cannot submit an arbitrary URL.
- Added `window.jarvisUpdate` with only `check()` and `open()` methods through the existing context-isolated preload.
- Added one automatic check after renderer startup, a Settings `Check now` action, and a non-blocking Chat header notice with `Download update` and `Later` actions.
- Added the checker to the Internal Test Electron Builder allowlist so the packaged app contains the same update contract.

## Files Changed / 修改文件

- `electron_motion_preview_internal_test/update-checker.cjs`
- `electron_motion_preview_internal_test/main.cjs`
- `electron_motion_preview_internal_test/preload.cjs`
- `electron_motion_preview_internal_test/package.json`
- `electron_motion_preview_internal_test/renderer/motion.html`
- `electron_motion_preview_internal_test/renderer/unified.css`
- `electron_motion_preview_internal_test/renderer/unified.js`
- `electron_motion_preview_internal_test/test/update-checker.cjs`
- `electron_motion_preview_internal_test/test/static-verify.cjs`
- `docs/info/01-project-overview/CURRENT_STATE.md`
- `docs/info/02-architecture/ARCHITECTURE_OVERVIEW.md`
- `docs/info/03-modules/MODULE_INVENTORY.md`
- `docs/info/05-integrations/ELECTRON_CORE_PACKAGING.md`
- `docs/CHANGELOG.md`
- This Prompt Record

## Architecture Impact / 架构影响

Update detection belongs to the Electron main process as an external-release adapter. The Renderer remains local-only and consumes a small preload contract. Core/API, permissions, AI, RAG, user data and Theme ownership are unchanged. The update channel is explicitly `internal-test`; development edition does not silently enter this channel.

## Dependency Impact / 依赖影响

No package or runtime dependency was added. The implementation uses the packaged Electron/Node runtime `fetch`, `AbortController`, `shell.openExternal` and existing context isolation.

## Behavior Impact / 行为影响

The packaged Internal Test client checks once after startup and exposes a manual Settings check. A newer published Release with an exact `JARVIS-Internal-Test-<version>-Setup.exe` asset shows a visible notice. `Download update` opens the validated Release page; the user downloads and runs the NSIS installer explicitly. No background download, silent install or automatic restart was added.

## Fallback Check / 兜底检查

No silent fallback introduced. Network failure, timeout, malformed response, unsupported channel, missing published installer and unavailable development mode each remain explicit statuses or errors. A missing update bridge is displayed as unavailable rather than treated as up to date.

## Compatibility Check / 兼容检查

No compatibility layer introduced. The update checker uses the new explicit Internal Test channel and asset contract. User data remains under the existing AppData boundary and is not modified by checking.

## Verification / 验证

- Unit tests cover version ordering, Internal Test asset selection, no-release state, malformed/untrusted payloads, explicit network failure and bounded timeout.
- Static verifier covers package inclusion, main/preload contract, HTML/CSS/Renderer notice contract and the no-arbitrary-URL boundary.
- `node --check` passed for main, preload, update checker and renderer.
- `npm run verify:static` passed.
- `node --test test/*.cjs` passed: 64 tests, 0 failures.
- A live packaged Release with a newer version was not fabricated or required for this contract test; the mock payload tests prove the available/update/no-release branches.

## Result / 当前结果

IMPLEMENTED — Internal Test source, static contract, version/update checker tests and the existing Electron Node suite are complete. The future Release must publish a bumped version with the exact Internal Test installer asset name for the notice to appear.

## Documentation Updated / 已更新文档

- This Prompt Record (created before implementation and completed after verification).
- `docs/info/01-project-overview/CURRENT_STATE.md`
- `docs/info/02-architecture/ARCHITECTURE_OVERVIEW.md`
- `docs/info/03-modules/MODULE_INVENTORY.md`
- `docs/info/05-integrations/ELECTRON_CORE_PACKAGING.md`
- `docs/CHANGELOG.md`

## Follow-Up / 后续

91 - Git & Release must publish future Internal Test installers with a bumped semantic version and the exact `JARVIS-Internal-Test-<version>-Setup.exe` asset name for detection to report an update.
