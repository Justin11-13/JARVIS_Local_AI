"""Markdown-aware hierarchical chunking for JARVIS RAG knowledge."""

from __future__ import annotations

import re

from services.rag.document_loader import load_documents


DEFAULT_CHUNK_SIZE = 1200
DEFAULT_OVERLAP = 200

MARKDOWN_HEADING_PATTERN = re.compile(
    r"^(#{1,6})\s+(.+?)\s*$",
    re.MULTILINE,
)


def split_markdown_sections(
    content: str,
) -> list[dict]:
    """
    Split Markdown content into sections while preserving
    the heading hierarchy.

    Each returned section contains:

    - heading
    - level
    - section_path
    - content
    """

    matches = list(
        MARKDOWN_HEADING_PATTERN.finditer(
            content
        )
    )

    if not matches:
        return [
            {
                "heading": "",
                "level": 0,
                "section_path": [],
                "content": content.strip(),
            }
        ]

    sections = []

    first_match = matches[0]

    preamble = content[
        : first_match.start()
    ].strip()

    if preamble:
        sections.append(
            {
                "heading": "",
                "level": 0,
                "section_path": [],
                "content": preamble,
            }
        )

    heading_stack: list[str] = []

    for index, match in enumerate(
        matches
    ):
        heading_marks = match.group(1)
        heading_text = (
            match.group(2).strip()
        )

        heading_level = len(
            heading_marks
        )

        while (
            len(heading_stack)
            >= heading_level
        ):
            heading_stack.pop()

        heading_stack.append(
            heading_text
        )

        if index + 1 < len(matches):
            end = matches[
                index + 1
            ].start()
        else:
            end = len(content)

        start = match.start()

        section_content = (
            content[start:end].strip()
        )

        if not section_content:
            continue

        sections.append(
            {
                "heading": heading_text,
                "level": heading_level,
                "section_path": (
                    heading_stack.copy()
                ),
                "content": section_content,
            }
        )

    return sections


def split_large_text(
    text: str,
    chunk_size: int,
    overlap: int,
) -> list[str]:
    """
    Split an oversized Markdown section into
    overlapping chunks.
    """

    if len(text) <= chunk_size:
        return [text]

    chunks = []

    start = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        chunk = text[
            start:end
        ].strip()

        if chunk:
            chunks.append(
                chunk
            )

        if end >= len(text):
            break

        start += (
            chunk_size - overlap
        )

    return chunks


def build_embedding_content(
    source: str,
    section_path: list[str],
    content: str,
    metadata: dict | None = None,
) -> str:
    """
    Add hierarchy context to the text used for embedding.

    The original Markdown content remains unchanged,
    while embedding_content provides stronger semantic
    context for retrieval.
    """

    hierarchy = " > ".join(section_path) or "(none)"

    lines = [f"Source: {source}"]
    metadata = metadata or {}
    if metadata.get("title"):
        lines.append(f"Title: {metadata['title']}")
    if metadata.get("aliases"):
        lines.append(f"Aliases: {', '.join(metadata['aliases'])}")
    if metadata.get("tags"):
        lines.append(f"Tags: {', '.join(metadata['tags'])}")
    lines.append(f"Section: {hierarchy}")
    return "\n".join(lines) + f"\n\n{content}"


def chunk_documents(
    documents: list[dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[dict]:
    """
    Split documents using Markdown hierarchy.

    Oversized sections are divided into smaller
    overlapping chunks.
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0."
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative."
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size."
        )

    chunks = []

    for document in documents:
        source = document["source"]
        content = document["content"]

        sections = (
            split_markdown_sections(
                content
            )
        )

        chunk_id = 0

        for section in sections:
            heading = section[
                "heading"
            ]

            heading_level = section[
                "level"
            ]

            section_path = section[
                "section_path"
            ]

            section_content = section[
                "content"
            ]

            smaller_chunks = (
                split_large_text(
                    section_content,
                    chunk_size,
                    overlap,
                )
            )

            for (
                part_index,
                chunk_content,
            ) in enumerate(
                smaller_chunks
            ):
                embedding_content = (
                    build_embedding_content(
                        source,
                        section_path,
                        chunk_content,
                        document,
                    )
                )

                chunks.append(
                    {
                        **{
                            key: value
                            for key, value in document.items()
                            if key not in {"content", "index_material"}
                        },
                        "source": source,
                        "chunk_id": chunk_id,
                        "section": heading,
                        "heading_level":
                            heading_level,
                        "section_part":
                            part_index,
                        "section_path":
                            section_path,
                        "content":
                            chunk_content,
                        "embedding_content":
                            embedding_content,
                    }
                )

                chunk_id += 1

    return chunks


if __name__ == "__main__":
    documents = load_documents()

    chunks = chunk_documents(
        documents
    )

    print(
        f"Loaded documents: "
        f"{len(documents)}"
    )

    print(
        f"Created chunks: "
        f"{len(chunks)}"
    )

    print()

    for chunk in chunks[:10]:
        print(
            f"Source: "
            f"{chunk['source']}"
        )

        print(
            f"Chunk ID: "
            f"{chunk['chunk_id']}"
        )

        print(
            f"Section: "
            f"{chunk['section'] or '(none)'}"
        )

        print(
            "Section path: "
            + (
                " > ".join(
                    chunk["section_path"]
                )
                or "(none)"
            )
        )

        print(
            f"Heading level: "
            f"{chunk['heading_level']}"
        )

        print(
            f"Section part: "
            f"{chunk['section_part']}"
        )

        print()

        print(
            chunk["embedding_content"][
                :500
            ]
        )

        print()
        print(
            "-" * 70
        )
