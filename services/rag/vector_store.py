from pathlib import Path

import chromadb

DEFAULT_DB_PATH = "data/rag/chroma"
DEFAULT_COLLECTION_NAME = "jarvis_knowledge"


class VectorStore:
    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ):
        self.db_path = db_path
        self.collection_name = collection_name

        Path(db_path).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(path=db_path)

        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
            },
        )

    def add_chunks(
        self,
        chunks: list[dict],
    ) -> None:
        """
        Store embedded chunks in ChromaDB.
        """

        if not chunks:
            return

        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for chunk in chunks:
            vector_id = f"{chunk['source']}::chunk_{chunk['chunk_id']}"

            ids.append(vector_id)

            # Store the original knowledge text.
            documents.append(chunk["content"])

            embeddings.append(chunk["embedding"])

            metadata = {
                "source": chunk["source"],
                "chunk_id": chunk["chunk_id"],
            }

            if "section" in chunk:
                metadata["section"] = chunk["section"]

            if "section_path" in chunk:
                metadata["section_path"] = " > ".join(chunk["section_path"])

            if "heading_level" in chunk:
                metadata["heading_level"] = chunk["heading_level"]

            if "section_part" in chunk:
                metadata["section_part"] = chunk["section_part"]

            for key in (
                "source_path", "source_type", "knowledge_domain", "vault_id",
                "vault_name", "title", "access", "status", "authority",
                "source_url", "updated_at",
            ):
                value = chunk.get(key)
                if value not in (None, ""):
                    metadata[key] = value
            for key in ("aliases", "tags"):
                values = chunk.get(key)
                if values:
                    metadata[key] = " | ".join(str(value) for value in values)

            metadatas.append(metadata)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def count(self) -> int:
        return self.collection.count()

    def delete_by_source(
        self,
        source: str,
    ) -> None:
        self.collection.delete(
            where={
                "source": source,
            }
        )

    def clear(self) -> None:
        """
        Delete all vectors while keeping the collection.
        """

        existing = self.collection.get()

        ids = existing.get("ids", [])

        if ids:
            self.collection.delete(ids=ids)

    def reset(self) -> None:
        """
        Completely recreate the Chroma collection.

        Use this when the RAG index schema, embedding
        model, or chunking strategy changes.
        """

        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass

        self.collection = self._get_or_create_collection()


if __name__ == "__main__":
    store = VectorStore()

    print(f"Stored vectors: {store.count()}")
