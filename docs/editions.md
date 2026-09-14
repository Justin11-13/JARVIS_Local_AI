# JARVIS editions / 双版本范围

Status: `IN PROGRESS` — the renderer edition slice exists in the integration
checkout, while package/Core port/data-directory integration is still pending.
This record is the current scope contract; it is not a public Release claim.

## Product decision

There is one codebase and one shared implementation. The two editions select
different launch/build profiles; they are not copied projects.

| Edition | User-facing name | Source launch | Page policy | Intended user data | Core contract |
|---|---|---|---|---|---|
| `development` | **JARVIS Development** | `.\run-new-ui.ps1 -Edition development` | Keep all current and future Pages, including work-in-progress surfaces. | `%LOCALAPPDATA%\JARVIS\Development` | `127.0.0.1:8765`, instance `jarvis-development` |
| `internal-test` | **JARVIS Internal Test** | `.\run-new-ui.ps1 -Edition internal-test` | Show only the explicitly accepted allowlist; unfinished/placeholder/disabled Pages are hidden and direct routes fall back to Assistant. | `%LOCALAPPDATA%\JARVIS\InternalTest` | `127.0.0.1:8766`, instance `jarvis-internal-test` |

The port and data-directory values above are the required contract for the
packaging/Core handoff. They must not be treated as implemented until the Core
health response, Core supervisor, bridge, and storage owners all consume and
verify the same edition/instance. Until then, the existing fixed-port and
repository-relative storage behavior is a release blocker for the internal
artifact.

## Current internal-test Page difference

The current 90-owned renderer slice observes this allowlist:

`Assistant`, `Tool Results`, `Device & working context`, `AI connections &
usage`, `Settings`, `Memory & knowledge`, `Theme`, `Voice`, and `Events &
errors`.

It hides `Tasks`, `Automation`, and `Codex handoff`, and rejects their direct
hash routes by returning to `Assistant`. This is a renderer-routing result,
not a statement that every allowlisted page has passed final internal-user
acceptance. `Memory`, `Voice`, and `AI connections` still require individual
evidence review before the internal artifact is distributed.

Development intentionally keeps all of those Pages visible so future work can
be developed and reviewed in the same codebase.

## Build and local installation

Install common dependencies once:

```powershell
.\setup.ps1
```

Build a named Windows package (local/internal use only):

```powershell
.\package-edition.ps1 -Edition internal-test
```

Install it under `%LOCALAPPDATA%\JARVIS\Internal-Test` and create the clearly
named `JARVIS Internal Test.lnk` shortcut:

```powershell
.\install-edition.ps1 -Edition internal-test
```

The corresponding development profile uses `JARVIS Development` names. The
shortcut passes the edition explicitly to Electron; it does not copy `.env`,
Codex login state, API keys, project registries, or Vault registration.

Uninstall application files without removing user data:

```powershell
.\uninstall-edition.ps1 -Edition internal-test
```

The uninstall script validates its exact `%LOCALAPPDATA%\JARVIS\<edition>`
target and refuses to remove a shortcut owned by another application. User
data is deliberately preserved; any future data-removal option must be a
separate explicit operation.

## Internal artifact Definition of Done

The internal package is not ready for distribution until all of these are
true:

- the frozen 90 edition renderer files are copied and hash-verified;
- the final accepted Page allowlist is evidence-backed, including the
  `Memory`, `Voice`, and `AI connections` rows;
- Core health reports the edition/instance identity and the supervisor refuses
  a ready Core belonging to the other edition;
- the internal profile uses its own Core port and user-data root without
  overwriting development settings, chats, credentials, or Vault registration;
- both named shortcuts start only their owned Core process and never kill an
  unrelated listener;
- install/launch/uninstall are tested on the intended Windows host; and
- the artifact is shared internally only. No public GitHub Release or upload is
  implied by this workflow.
