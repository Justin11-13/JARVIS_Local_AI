from sentence_transformers import SentenceTransformer

from services.rag.chunker import chunk_documents
from services.rag.document_loader import load_documents

DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class EmbeddingService:
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> list[float]:
        """
        Convert one piece of text into an embedding vector.
        """
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def embed_chunks(
        self,
        chunks: list[dict],
    ) -> list[dict]:
        """
        Add an embedding vector to every RAG chunk.
        """

        if not chunks:
            return []

        texts = [
            chunk.get(
                "embedding_content",
                chunk["content"],
            )
            for chunk in chunks
        ]

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        embedded_chunks = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):
            embedded_chunks.append(
                {
                    **chunk,
                    "embedding": embedding.tolist(),
                }
            )

        return embedded_chunks


if __name__ == "__main__":
    documents = load_documents()
    chunks = chunk_documents(documents)

    print(f"Documents: {len(documents)}")
    print(f"Chunks: {len(chunks)}")
    print()

    embedding_service = EmbeddingService()

    embedded_chunks = embedding_service.embed_chunks(chunks)

    print()
    print(f"Embedded chunks: {len(embedded_chunks)}")

    if embedded_chunks:
        first_chunk = embedded_chunks[0]

        print(f"Source: {first_chunk['source']}")
        print(f"Chunk ID: {first_chunk['chunk_id']}")
        print(f"Embedding dimensions: {len(first_chunk['embedding'])}")

        print()
        print("First 10 embedding values:")
        print(first_chunk["embedding"][:10])
