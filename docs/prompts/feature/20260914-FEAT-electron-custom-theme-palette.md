# 20260914-FEAT-electron-custom-theme-palette

## Metadata / 元数据

- Date: 2026-09-14
- Type: FEAT
- Status: IMPLEMENTED (source/static/Node verified; normal Electron visual and package acceptance pending handoff)
- Owner: Electron renderer UI
- Surface: `electron_motion_preview/` and `electron_motion_preview_internal_test/`

## Original Request / 原始需求

用户希望在 Theme 页面增加调色盘，让用户可以自行修改 border、Core、background、font 等颜色；当前四个主题预设仍要保留。

## Goal / 目标

在两套 Electron edition 的 Theme page 提供可理解的本地颜色控制。颜色修改应立即影响当前窗口的卡片、文字、边界、Core hologram 等视觉层，并能在重新打开同一 edition 后恢复；用户可以一键回到当前 preset。

## Scope / 修改范围

- 为 Theme page 增加 8 个 HTML color controls：background、surface、border、accent、text、muted、Core A、Core B。
- 使用 renderer-local storage 保存经过白名单和 `#RRGGBB` 校验的 custom overrides。
- 将 custom overrides 映射到已有 CSS custom properties，并同步已有 hologram Core palette。
- 在 development 与 internal-test Electron renderer、static verifier 和当前项目文档中保持同一 contract。

## Non-Goals / 非目标

- 不改变 Core/API、bridge、routing、permission、conversation、usage 或 Flutter 行为。
- 不加入远程主题同步、系统 Windows accent/theme 写入、第三方 provider、fallback 或自动重试。
- 不删除或重命名既有 `Amber Core`、`Cyan Circuit`、`Violet Pulse`、`Matrix Green` preset。
- 不在本轮修改无关的 Electron package、Core binary 或安装器配置。

## Before / 修改前

Theme page 只有 preset selector；preset 通过 `jarvis.ui.theme.v1` 选择并驱动 CSS token，用户不能在保留 preset 的基础上微调颜色。

## Investigation / 调查

- 两个 edition 的 `renderer/unified.js` 都是 Theme state、local persistence 和 Core palette sync 的 owner。
- `renderer/unified.css` 已将 surface、accent、status 和 Core 视觉拆成 CSS variables；`hologram.js` 已提供受控 `setPalette()`，因此不需要新建视觉或 Core service。
- 两个 edition 的 `motion.html`、CSS 和 static verifier 结构可保持同步；没有需要修改的 API 或 package dependency。

## Root Cause / 根本原因

缺少用户可编辑的 Theme 控件和 custom-token persistence；既有 preset 只能在预设之间切换，无法表达用户自己的 border/Core/font 颜色。

## Decision / 决策

- 继续以 `data-theme` + CSS variables 作为 preset 的 SSOT，并以 `jarvis.ui.theme.custom.v1` 保存同一 edition 的 custom overrides。
- 只接受已知字段和六位十六进制颜色；无效 storage 内容被忽略，不会切换到另一个 provider 或运行时路径。
- custom overrides 在 preset 应用后重新写入 inline CSS variables；切换 preset 时保留用户 overrides，Reset 才会清除 custom values。
- 保存失败必须在 Theme page status 中显示；当前窗口仍应用已选颜色，不把失败伪装成成功。

## Implementation / 实现

- `unified.js`：增加 palette field allowlist、颜色规范化/读取、CSS token 映射、local persistence、即时 input listener 和 Reset action；Core A/B 通过既有 `syncCorePalette()` 更新 hologram。
- `motion.html`：在 Theme inspector 加入 Custom palette card、8 个 color inputs、hex output、状态文字和 Reset custom palette button。
- `unified.css`：增加 2-column palette layout、swatch focus/keyboard states，以及窄窗口的一列响应式布局。
- `test/static-verify.cjs`：验证两 edition 的 8 个 controls、storage/apply/reset contract 和 palette CSS contract。

## Files Changed / 修改文件

- `electron_motion_preview/renderer/unified.js`
- `electron_motion_preview/renderer/motion.html`
- `electron_motion_preview/renderer/unified.css`
- `electron_motion_preview/test/static-verify.cjs`
- `electron_motion_preview_internal_test/renderer/unified.js`
- `electron_motion_preview_internal_test/renderer/motion.html`
- `electron_motion_preview_internal_test/renderer/unified.css`
- `electron_motion_preview_internal_test/test/static-verify.cjs`
- `docs/prompts/feature/20260914-FEAT-electron-custom-theme-palette.md`
- `docs/info/01-project-overview/CURRENT_STATE.md`
- `docs/info/03-modules/MODULE_INVENTORY.md`
- `docs/INDEX.md`
- `docs/CHANGELOG.md`

## Architecture Impact / 架构影响

这是 presentation-local renderer change。UI 仍只通过既有 bridge 读取/提交应用状态；CSS custom properties 与现有 `hologram.js` palette setter 负责视觉同步，不增加反向依赖，不改变 Core/API 层。

## Dependency Impact / 依赖影响

没有新增或升级 package、Python dependency、Electron dependency 或 Core resource。

## Behavior Impact / 行为影响

- Theme 页面打开后显示当前 preset/custom values。
- 用户拖动任意 swatch 会即时更新当前 edition 的视觉；关闭再打开后从 local storage 恢复。
- Border、surface/background、accent、text/muted 和 Core A/B 通过既有语义 token 影响对应卡片、控件、文字与 hologram。
- Reset custom palette 清除 8 个 override，恢复当前 preset 的颜色。

## Fallback Check / 兜底检查

未增加 silent fallback。malformed storage、未知字段和非法颜色只会被忽略；local persistence 失败在页面 status 中明确显示，当前已应用颜色不会被伪装成已持久化。

## Compatibility Check / 兼容检查

未增加兼容层或第二套 Theme implementation。两套 edition 共享相同的 palette contract，但各自 renderer-local storage 仍保持 edition 隔离。

## Testing / 测试

- `npm run verify:static`：development passed；internal-test passed。
- `node --test test/*.cjs`：development `59/59` passed；internal-test `59/59` passed。
- `node --check renderer/unified.js`：development passed；internal-test passed。
- 正常 Electron/WebGL visual acceptance 和安装器重打包交由 release handoff；当前受限 host 既有 GPU/cache 阻断仍未被隐藏或绕过。

## Result / 最终结果

两套 Electron Theme page 现在都提供可即时编辑、可本地持久化、可 Reset 的 8 项调色盘，同时保留四个 preset 和 Core palette sync。静态与 Node regression 已通过；没有修改 Core/API 或 package dependency。

## Documentation Updated / 已更新文档

- `docs/INDEX.md`
- `docs/info/01-project-overview/CURRENT_STATE.md`
- `docs/info/03-modules/MODULE_INVENTORY.md`
- `docs/CHANGELOG.md`

## Follow-Up / 后续

冻结此 renderer slice 后，由 91 release handoff 通知 30 重新打包安装包；30 仍需按其正常流程做 package/runtime/installer checks。不要在打包前引入未记录的 UI 或 Core 变更。

No silent fallback introduced. No compatibility layer introduced.
