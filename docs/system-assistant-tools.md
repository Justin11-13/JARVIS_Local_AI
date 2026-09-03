# JARVIS Windows Assistant Tools

This page describes native, fixed-function Windows tools. A reasoning provider
may propose one, but Python validates its name and arguments before running it.
JARVIS does not expose arbitrary PowerShell or arbitrary executable commands.

## Available now

| Category | Tools | Confirmation |
| --- | --- | --- |
| Applications | discover/open a registered Windows application | no |
| System status | CPU/RAM, battery, active network interfaces, running process list | no |
| Audio and media | raise/lower volume, mute toggle, play/pause, next, previous, stop | no |
| Windows navigation | open a standard user folder, open a fixed Windows Settings page | no |
| Session safety | lock workstation | once |
| Power | sleep, restart, shutdown | once |
| Development projects | list/open registered projects, Git status, list/read/search registered project files | no for read-only; secret files remain blocked from cloud responses |

## Still not available

These are not labelled as completed because Windows alone cannot reliably
provide them across every machine, hardware vendor, or signed-in application.

| Capability | Why it is not available yet |
| --- | --- |
| Exact volume percentage | Requires Core Audio integration rather than relative standard media keys. |
| Display brightness | Depends on laptop/display driver support; external displays often need vendor DDC/CI support. |
| Wi-Fi, Bluetooth, VPN connection changes | Need separate connection profiles, device selection, and confirmation design. |
| Close/force-close processes | Requires process-selection UI and elevated-risk handling. |
| General file create/move/rename/delete | Needs a user-visible target preview and confirmation flow outside registered projects. |
| Screenshot, camera, microphone, screen recording | Need explicit privacy indicators and user consent. |
| Browser form submission, online purchases, messages | Need site-specific automation and high-risk approval rules. |
| Voice, wake word, speaker verification | Need microphone, speech-to-text, text-to-speech, and privacy settings. |
| Manufacturer-specific hardware | Fan curves, RGB, GPU modes, keyboard lighting, battery charge limits, etc. require verified vendor APIs. |
| Codex delegation | Optional coding-executor selection and a bounded task handoff are not integrated yet. |

## Risk rules

- Low risk: status reads, app opening, volume/media controls, known folders, and fixed settings pages.
- Medium risk: locking the workstation and future state-changing non-destructive actions. One confirmation is required.
- High risk: power actions, deletion, administrator actions, credential changes, and future destructive operations. One explicit confirmation is required.
