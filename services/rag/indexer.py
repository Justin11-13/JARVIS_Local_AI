import hashlib
import json
from pathlib import Path

from services.rag.chunker import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP,
    chunk_documents,
)
from services.rag.document_loader import (
    load_documents,
)
from services.rag.embedding import (
    DEFAULT_MODEL_NAME,
    EmbeddingService,
)
from services.rag.vector_store import (
    VectorStore,
)
from services.rag.keyword_store import KeywordStore


INDEX_VERSION = 6
CHUNKING_STRATEGY = "markdown-hierarchy-v1"
EMBEDDING_STRATEGY = "source-metadata-hierarchy-content-v1"


DEFAULT_MANIFEST_PATH = Path(
    "data/rag/index_manifest.json"
)


def calculate_content_hash(
    content: str,
) -> str:
    """
    Calculate a stable SHA-256 hash for document content.
    """

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


def current_index_config() -> dict:
    """
    Describe the indexing configuration that affects
    stored vectors.
    """

    return {
        "index_version": INDEX_VERSION,
        "embedding_model": DEFAULT_MODEL_NAME,
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "overlap": DEFAULT_OVERLAP,
        "chunking_strategy": CHUNKING_STRATEGY,
        "embedding_strategy": EMBEDDING_STRATEGY,
        "keyword_strategy": "sqlite-fts5-v1",
    }


def load_manifest(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict:
    """
    Load the RAG index manifest.

    Legacy manifests are treated as incompatible and
    will trigger a rebuild.
    """

    if not manifest_path.exists():
        return {
            "config": {},
            "documents": {},
        }

    try:
        data = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        print(
            f"[RAG] Failed to read manifest: {error}"
        )

        return {
            "config": {},
            "documents": {},
        }

    if not isinstance(data, dict):
        return {
            "config": {},
            "documents": {},
        }

    # New manifest format.
    if (
        isinstance(
            data.get("config"),
            dict,
        )
        and isinstance(
            data.get("documents"),
            dict,
        )
    ):
        return data

    # Old V1 manifest:
    #
    # {
    #   "knowledge/file.md": "hash"
    # }
    #
    # Treat it as legacy so the index is rebuilt.
    return {
        "config": {},
        "documents": {},
    }


def save_manifest(
    document_hashes: dict[str, str],
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> None:
    """
    Save current index configuration and document hashes.
    """

    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = {
        "config": current_index_config(),
        "documents": document_hashes,
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def index_config_changed(
    previous_config: dict,
) -> bool:
    """
    Return True when the existing vector index was
    created using an incompatible configuration.
    """

    return (
        previous_config
        != current_index_config()
    )


def rebuild_index(
    documents: list[dict],
    current_hashes: dict[str, str],
    vector_store: VectorStore,
    keyword_store: KeywordStore,
) -> None:
    """
    Completely rebuild the vector index.
    """

    print(
        "[RAG] Index configuration changed "
        "or no compatible index exists."
    )

    print(
        "[RAG] Rebuilding knowledge index..."
    )

    vector_store.reset()
    keyword_store.clear()

    chunks = chunk_documents(
        documents
    )

    print(
        f"Chunks requiring embedding: "
        f"{len(chunks)}"
    )

    if chunks:
        embedding_service = (
            EmbeddingService()
        )

        embedded_chunks = (
            embedding_service.embed_chunks(
                chunks
            )
        )

        vector_store.add_chunks(
            embedded_chunks
        )
        keyword_store.upsert_chunks(chunks)

    save_manifest(
        current_hashes
    )

    print()
    print(
        f"Stored vectors: "
        f"{vector_store.count()}"
    )

    print(
        "Knowledge index rebuild completed."
    )


def update_index() -> None:
    """
    Synchronize knowledge documents with ChromaDB.

    The index is rebuilt automatically when the
    indexing configuration changes.
    """

    documents = load_documents()

    current_documents = {
        document["source"]: document
        for document in documents
    }

    current_hashes = {
        source: calculate_content_hash(document.get("index_material", document["content"]))
        for source, document
        in current_documents.items()
    }

    manifest = load_manifest()

    previous_config = (
        manifest.get(
            "config",
            {},
        )
    )

    previous_hashes = (
        manifest.get(
            "documents",
            {},
        )
    )

    vector_store = VectorStore()
    keyword_store = KeywordStore()

    print(
        f"Knowledge documents: "
        f"{len(documents)}"
    )

    # --------------------------------------------------
    # Full rebuild when index configuration changes
    # --------------------------------------------------

    if index_config_changed(
        previous_config
    ):
        rebuild_index(
            documents=documents,
            current_hashes=current_hashes,
            vector_store=vector_store,
            keyword_store=keyword_store,
        )

        return

    # --------------------------------------------------
    # Normal incremental update
    # --------------------------------------------------

    new_sources = []
    modified_sources = []
    unchanged_sources = []

    for (
        source,
        current_hash,
    ) in current_hashes.items():

        previous_hash = (
            previous_hashes.get(
                source
            )
        )

        if previous_hash is None:
            new_sources.append(
                source
            )

        elif (
            previous_hash
            != current_hash
        ):
            modified_sources.append(
                source
            )

        else:
            unchanged_sources.append(
                source
            )

    deleted_sources = [
        source
        for source
        in previous_hashes
        if source
        not in current_hashes
    ]

    print(
        f"New: {len(new_sources)}"
    )

    print(
        f"Modified: "
        f"{len(modified_sources)}"
    )

    print(
        f"Deleted: "
        f"{len(deleted_sources)}"
    )

    print(
        f"Unchanged: "
        f"{len(unchanged_sources)}"
    )

    changed_sources = (
        new_sources
        + modified_sources
    )

    # --------------------------------------------------
    # New / modified documents
    # --------------------------------------------------

    if changed_sources:
        changed_documents = [
            current_documents[source]
            for source
            in changed_sources
        ]

        chunks = chunk_documents(
            changed_documents
        )

        print(
            f"Chunks requiring embedding: "
            f"{len(chunks)}"
        )

        embedding_service = (
            EmbeddingService()
        )

        embedded_chunks = (
            embedding_service.embed_chunks(
                chunks
            )
        )

        # Only delete old vectors after new embeddings
        # were created successfully.
        for source in modified_sources:
            vector_store.delete_by_source(
                source
            )
            keyword_store.delete_by_source(source)

        vector_store.add_chunks(
            embedded_chunks
        )
        keyword_store.upsert_chunks(chunks)

    # --------------------------------------------------
    # Deleted documents
    # --------------------------------------------------

    for source in deleted_sources:
        print(
            "Removing deleted source: "
            f"{source}"
        )

        vector_store.delete_by_source(
            source
        )
        keyword_store.delete_by_source(source)

    save_manifest(
        current_hashes
    )

    print()
    print(
        f"Stored vectors: "
        f"{vector_store.count()}"
    )

    print(
        "Knowledge index is up to date."
    )


if __name__ == "__main__":
    update_index()
