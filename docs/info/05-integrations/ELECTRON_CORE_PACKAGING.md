# Electron + JARVIS Core Windows Packaging / Electron + JARVIS Core Windows 封装

Status: IMPLEMENTED — final local Internal Test package built and packaged content verified; newly generated unsigned Core/Electron runtime launch is blocked by Windows Application Control on this host; clean-machine installer acceptance remains pending.

## Purpose

`electron_motion_preview_internal_test/` now has a complete Windows x64 packaging path. The generated NSIS Setup contains the Electron Internal Test client and a PyInstaller `onedir` JARVIS Core. It is not an Electron UI-only shell and does not depend on the development repository or `.venv` after installation.

## Package Layout

| Layer | Packaged location | Responsibility |
|---|---|---|
| Electron UI | `resources/app.asar` | Internal Test renderer, preload, fixed main-process bridge and UI lifecycle |
| JARVIS Core | `resources/core/jarvis-core.exe` plus its `_internal/` directory | Complete FastAPI, routing, permissions, native tools, RAG dependencies and Core resources |
| Codex CLI App Server | `resources/core/codex/codex.exe` | Bundled Windows x64 native `@openai/codex` runtime used by managed ChatGPT subscription transport |
| Read-only defaults | Core `_internal/config/`, `_internal/knowledge/jarvis/` | Safe empty registries and bundled JARVIS knowledge; no current-machine paths |
| Embedding model | Core `_internal/huggingface/` | Offline `paraphrase-multilingual-MiniLM-L12-v2` model cache |
| User data | `%LOCALAPPDATA%\JARVIS\InternalTest\` | Memory, task history, RAG indexes, logs, user config and optional `.env` |

The package does not include the repository `.env`, API keys, tokens, current `data/`, current `config/` JSON files, Obsidian Vault contents, or machine-specific project/app paths. The required Codex CLI executable is bundled, so an end user does not need to install Node.js, npm or Codex CLI separately. Managed ChatGPT/Codex authentication remains user-owned and is read from the user's normal Codex profile; credentials are never bundled or copied by the installer.

## Core Lifecycle

The packaged Electron main process resolves the Core executable from `process.resourcesPath\core\jarvis-core.exe` and starts it with a fixed working directory. The supervisor always probes `127.0.0.1:8765/api/health` first:

- a ready existing JARVIS Core is reused;
- an offline port starts only the packaged Core owned by this Electron process;
- a non-ready or unknown listener is reported as an explicit port conflict;
- shutdown closes only the Core child created by this Electron process.

The packaged Core sets `JARVIS_PACKAGED=1`, resolves immutable resources from its frozen resource root, and writes mutable state under `%LOCALAPPDATA%`. Development mode keeps the existing repository-relative `.venv` and `data/` behavior.

When the managed transport starts, packaged Core resolves `codex/codex.exe` beside `jarvis-core.exe` first. Development mode keeps the explicit `JARVIS_CODEX_COMMAND` override, the user's `%APPDATA%/npm/codex.cmd` installation when present, and the existing `codex.cmd` command contract. A missing bundled executable or failed user authentication remains an explicit AI connection failure; the package does not silently switch providers.

## Installer Behavior

The Internal Test `package.json` uses Electron Builder NSIS with:

- `oneClick=false`;
- `allowToChangeInstallationDirectory=true`;
- x64 Windows target;
- desktop and Start Menu shortcuts;
- artifact name `JARVIS-Internal-Test-0.1.0-Setup.exe`.

This produces a normal Setup executable rather than a portable single-file application. The installer UI is therefore able to show the destination page and let the user choose the installation directory.

## Update Notice / 更新提示

The packaged Internal Test client checks the fixed GitHub Releases API once after startup and also exposes
`Settings → Application updates → Check now`. Only a newer published Release with an asset matching
`JARVIS-Internal-Test-<version>-Setup.exe` is reported as available. The Chat header shows a non-blocking
`UPDATE AVAILABLE` notice; `Download update` opens the validated Release page so the user can download and run the
NSIS installer explicitly. This currently does not perform a silent download, automatic install or automatic restart.

The update request is owned by Electron main process and uses a bounded timeout. Renderer keeps `connect-src 'none'`
and receives only `window.jarvisUpdate.check()`/`open()` through preload; no arbitrary URL is accepted. Future releases
must bump the package semantic version and publish the matching Internal Test installer asset. The update channel is
explicitly `internal-test` and does not change Core/API or `%LOCALAPPDATA%\JARVIS\InternalTest` user data.

## Build Entry Points

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r packaging\requirements-build.txt
Set-Location electron_motion_preview_internal_test
npm install
npm run package:win
```

`npm install` uses the pinned build-time `@openai/codex` dependency. `packaging/build-core.ps1` runs `packaging/prepare-codex-cli.ps1` after PyInstaller to copy and license-record the Windows x64 native CLI into the Core output. The result is written to `electron_motion_preview_internal_test/release/`. Build outputs are ignored generated artifacts and are not source-controlled.

## Verification Evidence

The latest local build produced an `816,647,011` byte Setup executable with SHA-256
`3501645D93FF9A73402998488A0BA4D90E470F919F8563CCA4501FD17E4EE8B3`. The bundled
Codex CLI is `295,447,856` bytes with SHA-256
`E86FFD96751DED51F669B520D70BA3139B514EB36313A8EEEEDDE37BAA7B58E3`. Its current
Authenticode status is `NotSigned` because no release signing certificate is configured.
Evidence collected for this build:

- PyInstaller Core build completed successfully with `jarvis-core.exe` present.
- `app.asar` contains `update-checker.cjs`, the narrow preload update bridge, and the renderer update-notice flow.
- `npm run verify:static` passed and the Electron Node suite passed `64/64`.
- The fixed GitHub Releases API check returned explicit `not_published` for channel `internal-test` and current version `0.1.0`; no update was falsely reported as available.
- The final generated unsigned Core and Electron binaries could not be launched on this host because Windows Application Control blocked them. No policy bypass or silent fallback was used.

The installer was built and its NSIS configuration was verified, but it was not installed into a second clean Windows account during this task. A clean-machine acceptance pass must still confirm the destination chooser, first-install permissions, shortcut launch, optional AI setup, update notice against a published newer Internal Test release, and behavior when another process already occupies port `8765`.
