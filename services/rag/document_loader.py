from pathlib import Path

SUPPORTED_EXTENSIONS = {".md", ".txt"}


def load_documents(knowledge_dir: str = "knowledge") -> list[dict]:
    base_path = Path(knowledge_dir)

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

            documents.append(
                {
                    "source": file_path.as_posix(),
                    "content": content,
                }
            )

        except (OSError, UnicodeDecodeError) as error:
            print(f"[RAG] Failed to read {file_path}: {error}")

    return documents


if __name__ == "__main__":
    docs = load_documents()

    print(f"Loaded {len(docs)} documents.\n")

    for doc in docs:
        print(f"Source: {doc['source']}")
        print(f"Characters: {len(doc['content'])}")
        print("-" * 50)
