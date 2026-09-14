# README Current-State Reconciliation / README 当前状态校准

Status: `IMPLEMENTED` — documentation-only change. / 状态：`IMPLEMENTED`，仅文档变更。

Owner: `91 Git & Release`

Date: `2026-09-10`

## Request

Rewrite the GitHub README so it is clear about current functionality, future
scope, dependencies, complete setup steps, AI subscription/API truth,
security/privacy, and the difference between the New Electron UI and the Legacy
Flutter client. The latest direction was to make the New UI the primary story
and treat the old UI as compatibility: `把旧版的替换成新版`.

## Baseline and repository boundary

- Documentation was reconciled against clean baseline
  `main@07df06f92c3a90eb2fa2dc2bd42cc76271e7d21f`.
- This worktree is detached at that baseline and had no source changes before
  this task.
- The separate main checkout had 120 uncommitted entries at audit time (31
  tracked modifications and 89 untracked files), including Electron/Luna
  integration work. Those changes were not copied, staged, committed, or
  represented as runnable in this README.
- The clean baseline does not contain `electron_motion_preview/`, its
  `package.json`/lockfile, the active Luna adapters, or the coordination
  documents that exist only in the separate dirty checkout.

## Scope

Changed only:

- `README.md`
- `docs/CHANGELOG.md`
- this task record

Explicit non-goals:

- no Flutter, Python, Electron, API, test, dependency, or shortcut source
  changes;
- no source copying from the separate main checkout;
- no package installation, runtime launch, or AI-provider login;
- no commit, push, branch switch, merge, or main-checkout/index mutation.

## Documentation decisions

The README now states:

1. The New Electron UI is the primary development direction and intended
   replacement.
2. The Legacy Flutter UI remains the only runnable desktop client in this clean
   baseline and is explicitly a compatibility/recovery path.
3. The replacement is not complete here: no Electron source, package manifest,
   lockfile, shortcut, or clean-clone runtime evidence is available.
4. Current implementation, preview work, planned Phase A–C work, and Phase D
   out-of-scope work are separated with status labels.
5. Gemini BYOK is optional in the baseline; managed subscription and Direct API
   Luna transport are preview-only integration work outside this snapshot.
6. Core readiness, authentication/key state, model access, quota, and AI
   availability are separate facts. No provider or model fallback is implied.
7. Existing Legacy screenshots remain labelled examples; no New UI screenshot,
   badge, benchmark, or unsupported runtime claim was added.

## Verification

- Ran `git diff --check` after the README and documentation record edits.
- Ran local Markdown target/path checks for the files referenced by the README;
  all referenced local files exist.
- Inspected final status and diff scope; only the three scoped documentation
  files changed.
- Application tests, Flutter builds, Electron package checks, AI login, and
  runtime acceptance were not run; this task did not change implementation and
  the clean baseline does not contain the New UI source.

## Follow-up gate

When the Electron/Luna integration is committed into a clean release snapshot,
reconcile this README again with the actual package scripts, shortcut entrypoint,
test results, Core startup evidence, provider/account state, and real-window
acceptance. Do not remove the Legacy compatibility instructions until that
replacement gate is genuinely met.
