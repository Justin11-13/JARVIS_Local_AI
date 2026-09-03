from services.rag.embedding import EmbeddingService
from services.rag.vector_store import VectorStore

DEFAULT_TOP_K = 5


class Retriever:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[dict]:
        """
        Retrieve the most relevant knowledge chunks
        for a user query.
        """

        query = query.strip()

        if not query:
            return []

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        vector_count = self.vector_store.count()

        if vector_count == 0:
            return []

        # Convert the user question into an embedding.
        query_embedding = self.embedding_service.embed_text(query)

        # Search ChromaDB for the closest vectors.
        results = self.vector_store.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(
                top_k,
                vector_count,
            ),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        documents = results.get(
            "documents",
            [[]],
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]],
        )[0]

        distances = results.get(
            "distances",
            [[]],
        )[0]

        retrieved = []

        for (
            document,
            metadata,
            distance,
        ) in zip(
            documents,
            metadatas,
            distances,
        ):
            similarity = 1.0 - float(distance)

            retrieved.append(
                {
                    "source": metadata.get("source"),
                    "chunk_id": metadata.get("chunk_id"),
                    "section": metadata.get(
                        "section",
                        "",
                    ),
                    "section_path": metadata.get(
                        "section_path",
                        "",
                    ),
                    "heading_level": metadata.get(
                        "heading_level",
                        0,
                    ),
                    "section_part": metadata.get(
                        "section_part",
                        0,
                    ),
                    "content": document,
                    "distance": float(distance),
                    "similarity": similarity,
                }
            )

        return retrieved


if __name__ == "__main__":
    retriever = Retriever()

    question = input("Ask JARVIS knowledge: ")

    results = retriever.retrieve(question)

    print()
    print(f"Retrieved {len(results)} chunks.")
    print()

    for index, result in enumerate(
        results,
        start=1,
    ):
        print(f"Result #{index}")

        print(f"Source: {result['source']}")

        print(f"Section: {result['section_path'] or result['section'] or '(none)'}")

        print(f"Chunk ID: {result['chunk_id']}")

        print(f"Similarity: {result['similarity']:.4f}")

        print()

        print(result["content"][:600])

        print()
        print("-" * 70)
