from services.rag.retriever import Retriever

DEFAULT_TOP_K = 5
DEFAULT_MIN_SIMILARITY = 0.45


class RAGService:
    def __init__(
        self,
        top_k: int = DEFAULT_TOP_K,
        min_similarity: float = DEFAULT_MIN_SIMILARITY,
    ):
        self.retriever = Retriever()
        self.top_k = top_k
        self.min_similarity = min_similarity

    def retrieve_context(
        self,
        query: str,
    ) -> dict:
        """
        Retrieve relevant JARVIS knowledge for a user query.
        """

        query = query.strip()

        if not query:
            return {
                "query": "",
                "context": "",
                "sources": [],
                "chunks": [],
            }

        results = self.retriever.retrieve(
            query=query,
            top_k=self.top_k,
        )

        relevant_results = [
            result for result in results if result["similarity"] >= self.min_similarity
        ]

        if not relevant_results:
            return {
                "query": query,
                "context": "",
                "sources": [],
                "chunks": [],
            }

        context_parts = []
        sources = []

        for index, result in enumerate(
            relevant_results,
            start=1,
        ):
            source = result["source"]
            chunk_id = result["chunk_id"]

            section_path = result.get("section_path") or result.get("section") or ""

            lines = [
                f"[Knowledge {index}]",
                f"Source: {source}",
            ]

            if section_path:
                lines.append(f"Section: {section_path}")

            lines.extend(
                [
                    f"Chunk: {chunk_id}",
                    "",
                    result["content"],
                ]
            )

            context_parts.append("\n".join(lines))

            if source not in sources:
                sources.append(source)

        return {
            "query": query,
            "context": "\n\n".join(context_parts),
            "sources": sources,
            "chunks": relevant_results,
        }

    def build_augmented_message(
        self,
        query: str,
    ) -> dict:
        """
        Add retrieved JARVIS knowledge to the user message.

        If no relevant knowledge exists, return the original
        user message unchanged.
        """

        rag_result = self.retrieve_context(query)

        context = rag_result["context"]

        if not context:
            return {
                **rag_result,
                "message": query,
                "used_rag": False,
            }

        message = f"""
The user asked the following question:

{query}

Relevant JARVIS knowledge has been retrieved below.

Use this knowledge as the primary source of truth when the
question concerns JARVIS.

Important rules:
- Do not invent JARVIS capabilities.
- Distinguish implemented features from planned features.
- If the retrieved knowledge is insufficient, say so.
- Do not claim future functionality is currently available.
- Prefer the most specific retrieved section when multiple
  knowledge chunks discuss the same topic.

RETRIEVED JARVIS KNOWLEDGE:

{context}

Now answer the user's original question directly.
""".strip()

        return {
            **rag_result,
            "message": message,
            "used_rag": True,
        }


if __name__ == "__main__":
    rag_service = RAGService()

    question = input("Ask JARVIS knowledge: ")

    result = rag_service.build_augmented_message(question)

    print()
    print(f"RAG used: {result['used_rag']}")
    print()

    print("Sources:")

    for source in result["sources"]:
        print(f"- {source}")

    print()
    print("=" * 70)
    print("AUGMENTED MESSAGE")
    print("=" * 70)
    print()
    print(result["message"])
