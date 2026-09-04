"""Load and validate local knowledge sources without exposing them to the LLM."""

from __future__ import annotations

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "obsidian_vaults.json"


def load_obsidian_vaults(config_path: Path = DEFAULT_CONFIG_PATH) -> list[dict]:
    if not config_path.is_file():
        return []
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"[RAG] Warning: failed to read Obsidian configuration: {error}")
        return []

    vaults = []
    seen_ids, seen_paths = set(), set()
    for item in payload.get("vaults", []) if isinstance(payload, dict) else []:
        if not isinstance(item, dict) or not item.get("enabled", True):
            continue
        vault_id = str(item.get("id", "")).strip()
        name = str(item.get("name", vault_id)).strip()
        raw_path = str(item.get("path", "")).strip()
        if not vault_id or not raw_path:
            continue
        path = Path(raw_path)
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            print(f"[RAG] Warning: Obsidian vault '{name}' is unavailable: {error}")
            continue
        key = str(resolved).casefold()
        if not resolved.is_dir() or vault_id in seen_ids or key in seen_paths:
            continue
        seen_ids.add(vault_id)
        seen_paths.add(key)
        vaults.append({
            "id": vault_id,
            "name": name or vault_id,
            "path": resolved,
            "default_access": str(item.get("default_access", "excluded")).casefold(),
        })
    return vaults


def knowledge_sources() -> list[dict]:
    sources = [{
        "id": "internal:jarvis",
        "source_type": "internal",
        "knowledge_domain": "jarvis",
        "path": ROOT_DIR / "knowledge" / "jarvis",
    }]
    sources.extend({
        "id": f"obsidian:{vault['id']}",
        "source_type": "obsidian",
        "knowledge_domain": "obsidian",
        **vault,
    } for vault in load_obsidian_vaults())
    return sources


def save_obsidian_vault(vault_id: str, name: str, path: str, default_access: str = "excluded") -> dict:
    resolved = Path(path).resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError("The Obsidian vault path must be an existing directory.")
    if default_access not in {"rag", "local-only", "excluded"}:
        raise ValueError("Unsupported default access value.")
    vault_id = vault_id.strip()
    if not vault_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in vault_id):
        raise ValueError("Vault ID may contain only letters, numbers, hyphens, and underscores.")
    payload = {"vaults": []}
    if DEFAULT_CONFIG_PATH.is_file():
        try:
            loaded = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("vaults"), list):
                payload = loaded
        except (OSError, json.JSONDecodeError):
            pass
    entry = {"id": vault_id, "name": name.strip() or vault_id, "path": str(resolved), "enabled": True, "default_access": default_access}
    payload["vaults"] = [item for item in payload["vaults"] if isinstance(item, dict) and item.get("id") != vault_id]
    payload["vaults"].append(entry)
    DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = DEFAULT_CONFIG_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(DEFAULT_CONFIG_PATH)
    return entry


def remove_obsidian_vault(vault_id: str) -> bool:
    if not DEFAULT_CONFIG_PATH.is_file():
        return False
    payload = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
    before = payload.get("vaults", [])
    after = [item for item in before if not isinstance(item, dict) or item.get("id") != vault_id]
    if len(after) == len(before):
        return False
    payload["vaults"] = after
    temporary = DEFAULT_CONFIG_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(DEFAULT_CONFIG_PATH)
    return True
