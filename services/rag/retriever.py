"""Expanded retrieval and deterministic reranking for JARVIS knowledge."""

from pathlib import PurePosixPath

from services.rag.embedding import EmbeddingService
from services.rag.keyword_store import KeywordStore
from services.rag.vector_store import VectorStore

DEFAULT_CANDIDATE_K = 30
DEFAULT_TOP_K = 5
DEFAULT_MAX_PER_SOURCE = 2

PERMISSION_TERMS = ("权限", "權限", "permission", "restriction", "execution", "安全", "confirmation", "确认", "確認")
CAPABILITY_TERMS = ("你能做什么", "你可以做什么", "你的能力", "功能", "capability", "capabilities")
FUTURE_TERMS = ("未来", "未來", "planned", "future", "计划", "計劃", "roadmap", "long-term")
CURRENT_TERMS = ("现在", "現在", "目前", "当前", "當前", "你能做什么", "你可以做什么", "你的权限", "你的權限", "你的能力", "current", "currently", "implemented")
WIKI_TERMS = ("obsidian", "vault", "我的笔记", "我的筆記", "我的知识库", "我的知識庫", "我的资料", "我的資料")

EXPANSIONS = {
    "permission": "permission model, execution restrictions, security boundary, tool allow-list, confirmation requirements, Python policy enforcement",
    "capability": "current implemented capabilities, native tools, available functions",
    "future": "planned future features, roadmap",
    "wiki": "personal wiki notes, Obsidian vault, note title, aliases, tags",
}

SOURCE_BONUSES = {
    "permission": {"routing_and_permissions.md": 0.10, "architecture.md": 0.05, "integrations.md": 0.04},
    "capability": {"native_tools.md": 0.10, "architecture.md": 0.04, "milestones.md": 0.03},
    "future": {"future_features.md": 0.10, "milestones.md": 0.05, "integrations.md": 0.04},
}


def _contains(query: str, terms: tuple[str, ...]) -> bool:
    normalized = query.casefold()
    return any(term.casefold() in normalized for term in terms)


def classify_query(query: str) -> set[str]:
    kinds = set()
    if _contains(query, PERMISSION_TERMS):
        kinds.add("permission")
    if _contains(query, CAPABILITY_TERMS):
        kinds.add("capability")
    if _contains(query, FUTURE_TERMS):
        kinds.add("future")
    if _contains(query, CURRENT_TERMS):
        kinds.add("current")
    if _contains(query, WIKI_TERMS):
        kinds.add("wiki")
    return kinds


def expand_query(query: str) -> str:
    kinds = classify_query(query)
    additions = [EXPANSIONS[kind] for kind in ("permission", "capability", "future", "wiki") if kind in kinds]
    if not additions:
        return query
    return f"{query}\n\nRetrieval context:\nJARVIS,\n" + ",\n".join(additions)


def rerank_bonus(query: str, metadata: dict) -> float:
    kinds = classify_query(query)
    source_name = PurePosixPath(str(metadata.get("source", "")).replace("\\", "/")).name.casefold()
    section = " ".join((str(metadata.get("section", "")), str(metadata.get("section_path", "")))).casefold()
    bonus = sum(SOURCE_BONUSES[kind].get(source_name, 0.0) for kind in kinds if kind in SOURCE_BONUSES)

    normalized_query = query.casefold()
    title = str(metadata.get("title", "")).casefold()
    aliases = str(metadata.get("aliases", "")).casefold().split(" | ")
    tags = str(metadata.get("tags", "")).casefold().split(" | ")
    if title and title in normalized_query:
        bonus += 0.12
    if any(alias and alias in normalized_query for alias in aliases):
        bonus += 0.10
    if any(tag and tag in normalized_query for tag in tags):
        bonus += 0.06
    authority = str(metadata.get("authority", "")).casefold()
    bonus += {"official": 0.04, "course": 0.03, "ai-generated": -0.04}.get(authority, 0.0)
    if str(metadata.get("status", "")).casefold() == "archived":
        bonus -= 0.08

    if "current" in kinds:
        if source_name == "future_features.md":
            bonus -= 0.12
        if any(term in section for term in ("planned", "future", "long-term", "未来", "未來", "计划", "計劃")):
            bonus -= 0.08
        if any(term in section for term in ("completed", "current", "implemented")):
            bonus += 0.04
    return bonus


def apply_source_diversity(results: list[dict], top_k: int, max_per_source: int = DEFAULT_MAX_PER_SOURCE) -> list[dict]:
    selected, deferred, counts = [], [], {}
    for result in results:
        source = result.get("source", "")
        if counts.get(source, 0) < max_per_source:
            selected.append(result)
            counts[source] = counts.get(source, 0) + 1
        else:
            deferred.append(result)
        if len(selected) == top_k:
            return selected
    selected.extend(deferred[: max(0, top_k - len(selected))])
    return selected


class Retriever:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.keyword_store = KeywordStore()

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K, domains: tuple[str, ...] | list[str] | None = None) -> list[dict]:
        query = query.strip()
        if not query:
            return []
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")
        vector_count = self.vector_store.count()
        if vector_count == 0:
            return []

        retrieval_query = expand_query(query)
        query_embedding = self.embedding_service.embed_text(retrieval_query)
        filters = [{"access": "rag"}]
        if domains:
            filters.append({"knowledge_domain": {"$in": list(domains)}})
        where = filters[0] if len(filters) == 1 else {"$and": filters}
        results = self.vector_store.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(DEFAULT_CANDIDATE_K, vector_count),
            include=["documents", "metadatas", "distances"],
            where=where,
        )
        retrieved_by_id = {}
        for vector_id, document, metadata, distance in zip(results.get("ids", [[]])[0], results.get("documents", [[]])[0], results.get("metadatas", [[]])[0], results.get("distances", [[]])[0]):
            similarity = 1.0 - float(distance)
            bonus = rerank_bonus(query, metadata)
            retrieved_by_id[vector_id] = {
                "source": metadata.get("source"), "chunk_id": metadata.get("chunk_id"),
                "section": metadata.get("section", ""), "section_path": metadata.get("section_path", ""),
                "heading_level": metadata.get("heading_level", 0), "section_part": metadata.get("section_part", 0),
                "source_path": metadata.get("source_path", ""), "source_type": metadata.get("source_type", ""),
                "knowledge_domain": metadata.get("knowledge_domain", ""), "vault_id": metadata.get("vault_id", ""),
                "vault_name": metadata.get("vault_name", ""), "title": metadata.get("title", ""),
                "access": metadata.get("access", "rag"), "status": metadata.get("status", "current"),
                "authority": metadata.get("authority", ""), "source_url": metadata.get("source_url", ""),
                "updated_at": metadata.get("updated_at", ""), "aliases": metadata.get("aliases", ""),
                "tags": metadata.get("tags", ""), "content": document, "distance": float(distance), "similarity": similarity,
                "rerank_bonus": bonus, "keyword_bonus": 0.0, "score": similarity + bonus, "retrieval_query": retrieval_query,
            }

        keyword_results = self.keyword_store.search(query, DEFAULT_CANDIDATE_K, domains=domains)
        keyword_ids = [item["vector_id"] for item in keyword_results]
        missing_ids = [vector_id for vector_id in keyword_ids if vector_id not in retrieved_by_id]
        if missing_ids:
            keyword_vectors = self.vector_store.collection.get(
                ids=missing_ids,
                include=["documents", "metadatas", "embeddings"],
            )
            for vector_id, document, metadata, embedding in zip(
                keyword_vectors.get("ids", []), keyword_vectors.get("documents", []),
                keyword_vectors.get("metadatas", []), keyword_vectors.get("embeddings", []),
            ):
                similarity = sum(float(left) * float(right) for left, right in zip(query_embedding, embedding))
                bonus = rerank_bonus(query, metadata)
                retrieved_by_id[vector_id] = {
                    "source": metadata.get("source"), "chunk_id": metadata.get("chunk_id"),
                    "section": metadata.get("section", ""), "section_path": metadata.get("section_path", ""),
                    "heading_level": metadata.get("heading_level", 0), "section_part": metadata.get("section_part", 0),
                    "source_path": metadata.get("source_path", ""), "source_type": metadata.get("source_type", ""),
                    "knowledge_domain": metadata.get("knowledge_domain", ""), "vault_id": metadata.get("vault_id", ""),
                    "vault_name": metadata.get("vault_name", ""), "title": metadata.get("title", ""),
                    "access": metadata.get("access", "rag"), "status": metadata.get("status", "current"),
                    "authority": metadata.get("authority", ""), "source_url": metadata.get("source_url", ""),
                    "updated_at": metadata.get("updated_at", ""), "aliases": metadata.get("aliases", ""),
                    "tags": metadata.get("tags", ""), "content": document, "distance": 1.0 - similarity,
                    "similarity": similarity, "rerank_bonus": bonus, "keyword_bonus": 0.0,
                    "score": similarity + bonus, "retrieval_query": retrieval_query,
                }
        for rank, keyword_result in enumerate(keyword_results):
            candidate = retrieved_by_id.get(keyword_result["vector_id"])
            if candidate:
                candidate["keyword_bonus"] = max(0.02, 0.08 - rank * 0.005)
                candidate["score"] += candidate["keyword_bonus"]

        retrieved = list(retrieved_by_id.values())
        retrieved.sort(key=lambda item: item["score"], reverse=True)
        return apply_source_diversity(retrieved, top_k)


if __name__ == "__main__":
    retriever = Retriever()
    for question in ("Gemini 有什么 execution restrictions？", "你的权限是什么？", "你现在可以使用 Codex 修改代码吗？"):
        print(f"\nQuery: {question}")
        for result in retriever.retrieve(question):
            print(f"- {result['source']} | {result['section_path'] or result['section']} | similarity={result['similarity']:.4f} score={result['score']:.4f}")
