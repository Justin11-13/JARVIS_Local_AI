"""Small dependency-free parser for the Obsidian properties JARVIS uses."""

from __future__ import annotations


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text

    metadata: dict[str, object] = {}
    current_list: str | None = None
    for raw_line in text[4:end].splitlines():
        line = raw_line.rstrip()
        if line.lstrip().startswith("- ") and current_list:
            value = line.lstrip()[2:].strip().strip("\"'")
            metadata.setdefault(current_list, []).append(value)
            continue
        if ":" not in line:
            current_list = None
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if not key:
            continue
        if not value:
            metadata[key] = []
            current_list = key
        elif value.startswith("[") and value.endswith("]"):
            metadata[key] = [item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()]
            current_list = None
        else:
            metadata[key] = value.strip("\"'")
            current_list = None
    body_start = end + len("\n---")
    return metadata, text[body_start:].lstrip("\r\n")


def string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
