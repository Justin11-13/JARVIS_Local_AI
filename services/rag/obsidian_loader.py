"""Safely load explicitly shared Markdown notes from configured Obsidian vaults."""

from __future__ import annotations

from pathlib import Path

from services.rag.frontmatter_parser import parse_frontmatter, string_list

SKIPPED_DIRECTORIES = {".obsidian", ".trash", ".git", "node_modules", "attachments"}
VALID_ACCESS = {"rag", "local-only", "excluded"}


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def load_obsidian_documents(vault: dict) -> list[dict]:
    root = Path(vault["path"]).resolve(strict=True)
    documents = []
    for file_path in sorted(root.rglob("*.md")):
        relative = file_path.relative_to(root)
        if any(part.casefold() in SKIPPED_DIRECTORIES or part.startswith(".") for part in relative.parts[:-1]):
            continue
        try:
            resolved = file_path.resolve(strict=True)
            if not resolved.is_file() or not _inside(resolved, root):
                continue
            raw_content = resolved.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            print(f"[RAG] Warning: failed to read Obsidian note {relative.as_posix()}: {error}")
            continue

        properties, content = parse_frontmatter(raw_content)
        access = str(properties.get("jarvis_access", vault.get("default_access", "excluded"))).casefold()
        if access not in VALID_ACCESS:
            access = "excluded"
        if access == "excluded" or not content.strip():
            continue
        relative_path = relative.as_posix()
        documents.append({
            "source": f"obsidian://{vault['id']}/{relative_path}",
            "source_path": relative_path,
            "source_type": "obsidian",
            "knowledge_domain": "obsidian",
            "vault_id": vault["id"],
            "vault_name": vault["name"],
            "title": str(properties.get("title") or file_path.stem),
            "aliases": string_list(properties.get("aliases")),
            "tags": string_list(properties.get("tags")),
            "access": access,
            "status": str(properties.get("status", "current")),
            "authority": str(properties.get("authority", "personal")),
            "source_url": str(properties.get("source_url", "")),
            "updated_at": str(properties.get("updated_at", "")),
            "content": content.strip(),
            "index_material": raw_content.strip(),
        })
    return documents
