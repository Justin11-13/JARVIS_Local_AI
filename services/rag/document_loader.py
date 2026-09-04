from pathlib import Path

from services.rag.obsidian_loader import load_obsidian_documents
from services.rag.source_registry import knowledge_sources

SUPPORTED_EXTENSIONS = {".md", ".txt"}


def load_documents(knowledge_dir: str = "knowledge") -> list[dict]:
    if knowledge_dir == "knowledge":
        documents = []
        for source in knowledge_sources():
            if source["source_type"] == "obsidian":
                documents.extend(load_obsidian_documents(source))
            else:
                documents.extend(_load_directory(Path(source["path"]), source))
        return documents

    return _load_directory(Path(knowledge_dir), None)


def _load_directory(base_path: Path, source_config: dict | None) -> list[dict]:

    if not base_path.exists():
        raise FileNotFoundError(f"Knowledge directory does not exist: {base_path}")

    if not base_path.is_dir():
        raise NotADirectoryError(f"Knowledge path is not a directory: {base_path}")

    documents = []

    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(encoding="utf-8").strip()

            if not content:
                continue

            if source_config:
                relative_path = file_path.relative_to(base_path).as_posix()
                document = {
                    "source": f"knowledge/jarvis/{relative_path}",
                    "source_path": relative_path,
                    "source_type": "internal",
                    "knowledge_domain": "jarvis",
                    "access": "rag",
                    "status": "current",
                    "authority": "project",
                    "title": file_path.stem.replace("_", " ").title(),
                    "content": content,
                    "index_material": content,
                }
            else:
                document = {"source": file_path.as_posix(), "content": content}
            documents.append(document)

        except (OSError, UnicodeDecodeError) as error:
            print(f"[RAG] Warning: failed to read {file_path}: {error}")

    return documents


if __name__ == "__main__":
    docs = load_documents()

    print(f"Loaded {len(docs)} documents.\n")

    for doc in docs:
        print(f"Source: {doc['source']}")
        print(f"Characters: {len(doc['content'])}")
        print("-" * 50)
