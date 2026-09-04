import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

from services.rag.chunker import chunk_documents
from services.rag.indexer import current_index_config
from services.rag.knowledge_router import should_use_rag
from services.rag.rag_service import classify_wiki_task, retrieval_limit_for_query
from services.rag.keyword_store import KeywordStore
from services.rag.retriever import apply_source_diversity, expand_query, rerank_bonus


class RagFinalIntegrationTests(unittest.TestCase):
    def test_chunk_embedding_content_includes_source_and_hierarchy(self):
        chunks = chunk_documents([{
            "source": "knowledge/jarvis/architecture.md",
            "content": "# JARVIS Architecture\n\n## Reasoning Layer\n\n### Restrictions\n\nPython remains authoritative.",
        }])
        chunk = chunks[-1]
        self.assertEqual(
            chunk["section_path"],
            ["JARVIS Architecture", "Reasoning Layer", "Restrictions"],
        )
        self.assertTrue(chunk["embedding_content"].startswith(
            "Source: knowledge/jarvis/architecture.md\n"
            "Section: JARVIS Architecture > Reasoning Layer > Restrictions\n\n"
        ))

    def test_index_config_is_versioned_for_final_strategies(self):
        config = current_index_config()
        self.assertEqual(config["index_version"], 6)
        self.assertEqual(config["chunking_strategy"], "markdown-hierarchy-v1")
        self.assertEqual(config["embedding_strategy"], "source-metadata-hierarchy-content-v1")

    def test_router_uses_rag_only_for_jarvis_specific_gemini_questions(self):
        self.assertTrue(should_use_rag("你的权限是什么？"))
        self.assertTrue(should_use_rag("你现在可以使用 Codex 修改代码吗？"))
        self.assertFalse(should_use_rag("什么是 PHP array？"))
        self.assertFalse(should_use_rag("Gemini 是什么？"))

        from services.rag.knowledge_router import route_knowledge
        self.assertEqual(route_knowledge("我的 Obsidian 笔记说了什么？").domains, ("obsidian",))
        self.assertEqual(route_knowledge("根据我的笔记比较 JARVIS 权限").domains, ("jarvis", "obsidian"))

    def test_permission_expansion_and_current_future_reranking(self):
        expanded = expand_query("你的权限是什么？")
        self.assertIn("permission model", expanded)
        current_bonus = rerank_bonus("你的权限是什么？", {
            "source": "knowledge/jarvis/routing_and_permissions.md",
            "section_path": "Current > Implemented",
        })
        future_bonus = rerank_bonus("你的权限是什么？", {
            "source": "knowledge/jarvis/future_features.md",
            "section_path": "Planned Future",
        })
        self.assertGreater(current_bonus, future_bonus)

    def test_source_diversity_limits_first_pass_then_fills(self):
        ranked = [
            {"source": "a.md", "score": 5},
            {"source": "a.md", "score": 4},
            {"source": "a.md", "score": 3},
            {"source": "b.md", "score": 2},
            {"source": "c.md", "score": 1},
        ]
        selected = apply_source_diversity(ranked, top_k=4, max_per_source=2)
        self.assertEqual([item["source"] for item in selected], ["a.md", "a.md", "b.md", "c.md"])

    def test_wiki_synthesis_queries_expand_retrieval_depth(self):
        self.assertEqual(classify_wiki_task("总结我的全部笔记并列出下一步"), "synthesis")
        self.assertEqual(retrieval_limit_for_query("总结我的全部笔记"), 10)
        self.assertEqual(classify_wiki_task("我的测试笔记写了什么？"), "lookup")
        self.assertEqual(retrieval_limit_for_query("我的测试笔记写了什么？"), 5)

    def test_keyword_store_can_search_after_background_thread_warmup(self):
        with TemporaryDirectory() as directory:
            store = KeywordStore(Path(directory) / "keyword.sqlite")
            chunk = {
                "source": "obsidian://wiki/test.md",
                "chunk_id": 0,
                "title": "JARVIS Test",
                "content": "连接 Obsidian 与 JARVIS 的测试笔记",
                "knowledge_domain": "obsidian",
                "access": "rag",
            }
            worker = Thread(target=lambda: store.upsert_chunks([chunk]))
            worker.start()
            worker.join()

            results = store.search("Obsidian", domains=("obsidian",))

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["vector_id"], store.vector_id(chunk))
            store.close()


if __name__ == "__main__":
    unittest.main()
