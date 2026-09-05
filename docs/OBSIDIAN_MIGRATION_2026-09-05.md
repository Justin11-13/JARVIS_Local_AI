---
title: 2026-09-05 Vault Migration
tags: [jarvis, migration, record]
jarvis_access: rag
type: change
category: records
status: completed
authority: tool-result
created: 2026-09-05
updated: 2026-09-05
project: JARVIS
---

# 2026-09-05 Vault Migration

## What changed
The user requested Obsidian as JARVIS's canonical long-term knowledge store. Folder rules were read from the Vault root and JARVIS rules; no deeper applicable rules were present.
Twenty repository knowledge files were classified. Eleven non-empty Markdown sources migrated, two architecture assets matched existing Vault files, six generated visual-check artifacts and one empty file remain only in the local backup. Four meaningful notes were added for data architecture, RAG behavior, the user's storage decision and migration context.

## Preservation
All original source bytes and the two modified existing notes were backed up to the ignored repo path tmp/knowledge-migration-2026-09-05. Each removed source was hash checked against its backup and target. PROJECT_SCOPE.md retains a small operational pointer; no private raw chat or runtime database was copied to the Git Vault.
Historical and unverified claims remain explicitly marked and local-only. The pre-Codex analysis was marked superseded while preserving its text and image links.

## Validation
Python 126 tests passed. New WikiLinks resolve to real targets. No source-code tree, credential store, cache or Programming folder was moved. Git commit/push was not performed.

## Related
- [[JARVIS/Knowledge/Architecture/Current/Data Architecture|Current data architecture]]
- [[JARVIS/Memory/Decisions/Obsidian Canonical Knowledge Store|User decision]]
- [[JARVIS/Records/Context/2026-09-05 Knowledge Migration|Context]]

## Migration manifest

| Original repo file | Destination / disposition |
|---|---|
| knowledge/jarvis/architecture.md | JARVIS/Knowledge/Architecture/Target/Original Assistant Architecture.md |
| knowledge/jarvis/development_principles.md | JARVIS/Knowledge/Projects/Development Principles.md |
| knowledge/jarvis/future_features.md | JARVIS/Plans/Roadmap/Original Feature Roadmap.md |
| knowledge/jarvis/integrations.md | JARVIS/Knowledge/Integrations/Integration Design.md |
| knowledge/jarvis/JARVIS_CURRENT_ARCHITECTURE.architecture.json | JARVIS/Architecture/JARVIS_CURRENT_ARCHITECTURE.architecture.json |
| knowledge/jarvis/JARVIS_CURRENT_ARCHITECTURE.html | JARVIS/Architecture/JARVIS_CURRENT_ARCHITECTURE.html |
| knowledge/jarvis/JARVIS_CURRENT_ARCHITECTURE.visual-check.1440x900.dark.png | kept in local migration backup; generated verification artifact or empty file |
| knowledge/jarvis/JARVIS_CURRENT_ARCHITECTURE.visual-check.1440x900.light.png | kept in local migration backup; generated verification artifact or empty file |
| knowledge/jarvis/JARVIS_CURRENT_ARCHITECTURE.visual-check.2048x1320.dark.png | kept in local migration backup; generated verification artifact or empty file |
| knowledge/jarvis/JARVIS_CURRENT_ARCHITECTURE.visual-check.2048x1320.light.png | kept in local migration backup; generated verification artifact or empty file |
| knowledge/jarvis/JARVIS_CURRENT_ARCHITECTURE.visual-check.html | kept in local migration backup; generated verification artifact or empty file |
| knowledge/jarvis/JARVIS_CURRENT_ARCHITECTURE.visual-check.json | kept in local migration backup; generated verification artifact or empty file |
| knowledge/jarvis/JARVIS_CURRENT_PROJECT_ANALYSIS.md | JARVIS/Records/Changes/Architecture Analysis Before Codex Integration.md |
| knowledge/jarvis/JARVIS_MEMORY_CODEX_TARGET.md | JARVIS/Knowledge/Architecture/Target/Memory and Codex Delivery Design.md |
| knowledge/jarvis/milestones.md | JARVIS/Records/Changes/Early Project Milestones.md |
| knowledge/jarvis/native_tools.md | JARVIS/Knowledge/Tools/Native Tool Design Principles.md |
| knowledge/jarvis/PROJECT_SCOPE.md | JARVIS/Knowledge/Projects/Project Scope.md |
| knowledge/jarvis/rag_system.md | kept in local migration backup; generated verification artifact or empty file |
| knowledge/jarvis/routing_and_permissions.md | JARVIS/Knowledge/Components/Routing and Permission Design.md |
| knowledge/jarvis/task_and_notifications.md | JARVIS/Knowledge/Components/Task and Notification Design.md |
