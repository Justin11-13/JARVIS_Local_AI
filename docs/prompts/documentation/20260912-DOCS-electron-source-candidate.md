# Electron Source Candidate / 新版 Electron 源码候选

Status: `IN PROGRESS` — source candidate validation, not a verified release.

Date: `2026-09-12`

Branch: `codex/electron-source-candidate-20260912`

Base: `main@07df06f92c3a90eb2fa2dc2bd42cc76271e7d21f`

## Scope

The 45-file whitelist from the source coordination handoff was copied one file
at a time from the main checkout into this isolated candidate. The main
checkout, main index, and main branch were not modified. The coordination
manifest itself is not part of this candidate; the current source-set
fingerprint and post-freeze delta are recorded below.

The original source handoff was verified before and after copy as `45/45` SHA-256
matches. The original manifest fingerprint identifies the pre-fix source
snapshot. The later test-only correction is now included in this candidate as a
separate post-freeze delta with its own hash; therefore the original 45-file
fingerprint is historical, not the final candidate fingerprint.

For the current 45-file source set, the deterministic fingerprint is
`725AA519938A80A5330B40A20FE691C5D6187C60398901D77F2279E54A775D7E`, computed
as SHA-256 over the UTF-8, newline-terminated, path-sorted lines
`relative-path<TAB>current-file-SHA256`. This explicitly includes the updated
`tests/test_api_fast_replies.py` hash below.

## Candidate-only additions

- `setup.ps1`: checks Python/Node prerequisites, creates `.venv`, installs the
  captured Python lock, runs `npm ci`, and optionally runs static checks.
- `run-new-ui.ps1`: starts the included Electron shell or its renderer/WebGL
  verification mode.
- `requirements.lock.txt`: captured from the clean Python 3.12.14 candidate
  environment.
- README, CHANGELOG, and this documentation record.

## Verification performed

- `npm ci` in `electron_motion_preview/`: passed; 131 packages installed.
  npm reported 3 high-severity audit advisories; no `npm audit fix --force` was
  run.
- `npm run verify:static`: passed.
- `node --test test/*.cjs`: 34/34 passed.
- Clean candidate `.venv` using Python 3.12.14:
  `pip install -r requirements.txt`: passed.
- `python -m compileall -q app services tests`: passed.
- Post-freeze test-only correction: added the missing module-level
  `jarvis_memory` import in `tests/test_api_fast_replies.py`. The updated
  SHA-256 is
  `87EEE9C45367E68918A6BAF8268DC64F9CBB3026D18ED9ABF0CB993810DD92A7`.
- Full Python regression discovery after that correction: 156/156 passed. The
  suite uses mocks for provider boundaries; this is not an AI/runtime result.
- Short local Core smoke: `/api/health` returned `core.status = ready` and
  correctly reported managed AI as `not_checked`; no account check or inference
  was performed. The listener was stopped after the check.
- `run-new-ui.ps1 -Verify` failed on the current restricted host after the GPU
  child exited with `0xC0000135`, cache writes were denied, and Electron
  returned `ERR_FAILED` while loading the renderer. No GPU workaround or hidden
  fallback was added.

## Explicit non-claims

- No managed Codex login, `gpt-5.6-luna` request, Direct API request, paid
  inference, or account credential was used.
- No normal Electron/Core window smoke, native confirmation, audio, or managed
  AI acceptance is claimed from this candidate run.
- No Windows EXE or public GitHub Release was created or uploaded.
- `node_modules/`, `.venv/`, logs, generated indexes, private configs, Vault
  data, and credentials remain excluded.

## Dependency audit

`npm audit` reports three high-severity dependency-node findings. They are the
same `extract-zip@2.0.1` node reached through direct development dependencies
`electron@39.8.10` and `@electron/packager@19.1.1`, covering the advisories
`GHSA-jmr9-qjv8-65gv` and `GHSA-7pqw-9j4j-h8q3`. npm reports no available fix.
`npm audit --omit=dev` reports zero findings. No forced audit fix was applied;
the finding remains a release-review item for the install/packaging path.

## Remaining gates

1. Recalculate and record the final candidate fingerprint after the candidate
   file set is frozen; preserve the original 45-file fingerprint as history.
2. Decide whether the install/packaging audit finding is acceptable for the
   intended source candidate or requires a narrowly scoped dependency change.
3. Perform ordinary-user Core/Luna/confirmation smoke without claiming managed
   account availability for users who have not configured it.
