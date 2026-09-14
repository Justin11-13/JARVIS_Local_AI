# Internal Test README and Phase Scope

- Status: IMPLEMENTED
- Date: 2026-09-14
- Type: DOCS

## Original Request

根据 JARVIS 内测版重写双语 README，并加入未来 scope 与 phase。

## Goal

让中英文读者都能区分内测版当前能力、开发版入口、安装与连接要求、已知限制，以及权威 Target Architecture 中 Phase A-C 的未来范围。

## Scope

- 将根目录 `README.md` 重写为中英双语。
- 以内测版 Electron + packaged Core 为主要产品入口。
- 记录 ChatGPT Subscription、Direct API 和可选 Obsidian 的真实边界。
- 摘要列出 Phase A、Phase B、Phase C，并明确 Phase D 未授权。

## Non-Goals

- 不修改源码、依赖、安装包或运行时配置。
- 不新增或实现任何 Phase 功能。
- 不把 source/static verification 写成 clean-machine acceptance。
- 不改变 `TARGET_ARCHITECTURE.md`。

## Before

README 仍以旧 Flutter/Gemini BYOK 基线为开头，混合历史实施计划、当前 Electron 能力和未来目标，且未以内测安装包为主要使用路径。

## Decision

README 使用四种明确状态：当前内测能力、需要用户配置、当前限制、未来 Phase。Repository architecture 文档继续是完整权威，README 只提供项目入口摘要。

## Files Changed

- `README.md`
- `docs/prompts/documentation/20260914-DOCS-internal-test-readme-and-phases.md`
- `docs/CHANGELOG.md`

## Architecture / Dependency / Behavior Impact

Documentation only. No architecture, dependency, permission, storage, provider, or runtime behavior changed.

## Fallback Check

No silent fallback introduced.

## Compatibility Check

No compatibility layer introduced.

## Testing

- Verified all README-local relative links resolve to repository files.
- Verified the major README sections provide corresponding English and Chinese explanations.
- Checked terminology against the internal-test edition allowlist, packaging records, current-state documentation, and authoritative Phase A-C scope.
- Reviewed the final documentation diff.

## Result

The bilingual README now presents the Windows Internal Test edition first, keeps development instructions separate, and labels future scope as planned rather than implemented.

## Documentation Updated

This record and `docs/CHANGELOG.md`.

## Follow-Up

After clean-machine installer acceptance, add a verified installation screenshot and replace the current acceptance warning. Do not expand Phase D without explicit user authorization.
