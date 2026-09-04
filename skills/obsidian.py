"""Bounded Obsidian vault tools. Paths are always vault-relative."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from urllib.parse import quote

from services.rag.source_registry import load_obsidian_vaults
from services.rag.obsidian_loader import load_obsidian_documents

BLOCKED_PARTS = {".obsidian", ".trash", ".git"}
DEFAULT_FRONTMATTER = {
    "tags": "[]",
    "jarvis_access": "rag",
    "status": "current",
    "authority": "personal",
}


def _refresh_index() -> str:
    try:
        from services.rag.indexer import update_index
        update_index()
        return " Index updated."
    except Exception as error:
        print(f"[RAG] Warning: Obsidian note changed but reindex failed: {error}")
        return " Note saved; index refresh will retry later."


def _vault(vault_id: str) -> dict:
    for item in load_obsidian_vaults():
        if item["id"] == vault_id:
            return item
    raise ValueError(f"Unknown or disabled Obsidian vault: {vault_id}")


def _safe_note(vault_id: str, relative_path: str, *, must_exist: bool) -> tuple[dict, Path, str]:
    vault = _vault(vault_id)
    root = Path(vault["path"]).resolve(strict=True)
    clean = relative_path.strip().replace("\\", "/").lstrip("/")
    if not clean or any(part in {"", ".", ".."} or part.casefold() in BLOCKED_PARTS for part in Path(clean).parts):
        raise ValueError("The Obsidian note path is invalid or protected.")
    if not clean.casefold().endswith(".md"):
        clean += ".md"
    target = (root / Path(clean)).resolve(strict=must_exist)
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError("The note path escapes the configured vault.") from error
    if must_exist and (not target.is_file() or target.suffix.casefold() != ".md"):
        raise ValueError("The requested Obsidian note does not exist.")
    return vault, target, clean


def _with_default_frontmatter(content: str, title: str) -> str:
    """Add JARVIS Wiki defaults without replacing user-provided properties."""
    normalized = content.lstrip("\ufeff")
    defaults = {
        "title": title,
        **DEFAULT_FRONTMATTER,
        "created": date.today().isoformat(),
    }
    if normalized.startswith("---\n"):
        closing = normalized.find("\n---", 4)
        if closing >= 0:
            frontmatter = normalized[4:closing]
            existing_keys = {
                line.split(":", 1)[0].strip().casefold()
                for line in frontmatter.splitlines()
                if ":" in line and not line.lstrip().startswith("-")
            }
            additions = [f"{key}: {value}" for key, value in defaults.items() if key.casefold() not in existing_keys]
            if not additions:
                return normalized
            separator = "" if not frontmatter or frontmatter.endswith("\n") else "\n"
            return normalized[:closing] + separator + "\n".join(additions) + normalized[closing:]

    header = "\n".join(f"{key}: {value}" for key, value in defaults.items())
    return f"---\n{header}\n---\n\n{normalized.lstrip()}"


def search_obsidian_notes(keyword: str, vault_id: str = "") -> str:
    term = keyword.strip().casefold()
    if not term:
        raise ValueError("A search keyword is required.")
    matches = []
    vaults = [_vault(vault_id)] if vault_id else load_obsidian_vaults()
    for vault in vaults:
        for document in load_obsidian_documents(vault):
            searchable = " ".join((document["source_path"], document["title"], " ".join(document["aliases"]), " ".join(document["tags"]), document["content"])).casefold()
            if term in searchable:
                matches.append(f"{vault['id']}:{document['source_path']}")
                if len(matches) >= 20:
                    return "\n".join(matches)
    return "\n".join(matches) if matches else "No matching Obsidian notes were found."


def open_obsidian_note(vault_id: str, relative_path: str) -> str:
    vault, _, clean = _safe_note(vault_id, relative_path, must_exist=True)
    uri = f"obsidian://open?vault={quote(vault['name'], safe='')}&file={quote(clean, safe='')}"
    os.startfile(uri)
    return f"Opened {clean} in Obsidian."


def create_obsidian_note(vault_id: str, relative_path: str, content: str) -> str:
    _, target, clean = _safe_note(vault_id, relative_path, must_exist=False)
    if target.exists():
        raise FileExistsError("The Obsidian note already exists; it was not overwritten.")
    target.parent.mkdir(parents=True, exist_ok=True)
    note_content = _with_default_frontmatter(content, Path(clean).stem)
    target.write_text(note_content.rstrip() + "\n", encoding="utf-8")
    return f"Created Obsidian note: {clean}.{_refresh_index()}"


def append_obsidian_note(vault_id: str, relative_path: str, content: str) -> str:
    _, target, clean = _safe_note(vault_id, relative_path, must_exist=True)
    existing = target.read_text(encoding="utf-8")
    separator = "" if not existing or existing.endswith("\n") else "\n"
    with target.open("a", encoding="utf-8", newline="") as handle:
        handle.write(separator + content.rstrip() + "\n")
    return f"Appended to Obsidian note: {clean}.{_refresh_index()}"


def update_obsidian_note(vault_id: str, relative_path: str, expected_text: str, replacement_text: str) -> str:
    _, target, clean = _safe_note(vault_id, relative_path, must_exist=True)
    existing = target.read_text(encoding="utf-8")
    if not expected_text or expected_text not in existing:
        raise ValueError("The expected note text was not found; no changes were written.")
    updated = existing.replace(expected_text, replacement_text, 1)
    target.write_text(updated, encoding="utf-8")
    return f"Updated one verified section in Obsidian note: {clean}.{_refresh_index()}"
