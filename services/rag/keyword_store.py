"""Local SQLite FTS5 index used alongside semantic retrieval."""

from __future__ import annotations

import json
import re
import sqlite3
from threading import RLock
from pathlib import Path

DEFAULT_KEYWORD_DB_PATH = Path("data/rag/keyword.sqlite")


class KeywordStore:
    def __init__(self, path: Path = DEFAULT_KEYWORD_DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        # FastAPI warms the RAG service in a background thread and serves chat
        # requests in worker threads. SQLite permits this when access to the
        # shared connection is explicitly serialized.
        self._lock = RLock()
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(vector_id UNINDEXED, source UNINDEXED, title, aliases, tags, content, metadata UNINDEXED)"
        )

    @staticmethod
    def vector_id(chunk: dict) -> str:
        return f"{chunk['source']}::chunk_{chunk['chunk_id']}"

    def upsert_chunks(self, chunks: list[dict]) -> None:
        with self._lock, self.connection:
            for chunk in chunks:
                vector_id = self.vector_id(chunk)
                self.connection.execute("DELETE FROM wiki_fts WHERE vector_id = ?", (vector_id,))
                metadata = {key: value for key, value in chunk.items() if key not in {"content", "embedding", "embedding_content"}}
                self.connection.execute(
                    "INSERT INTO wiki_fts(vector_id, source, title, aliases, tags, content, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (vector_id, chunk["source"], chunk.get("title", ""), " ".join(chunk.get("aliases", [])), " ".join(chunk.get("tags", [])), chunk["content"], json.dumps(metadata, ensure_ascii=False)),
                )

    def delete_by_source(self, source: str) -> None:
        with self._lock, self.connection:
            self.connection.execute("DELETE FROM wiki_fts WHERE source = ?", (source,))

    def clear(self) -> None:
        with self._lock, self.connection:
            self.connection.execute("DELETE FROM wiki_fts")

    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def search(self, query: str, limit: int = 12, domains: tuple[str, ...] | list[str] | None = None, rag_only: bool = True) -> list[dict]:
        tokens = re.findall(r"[\w\-]+", query.casefold(), flags=re.UNICODE)
        if not tokens:
            return []
        expression = " OR ".join(f'"{token}"' for token in tokens[:12])
        with self._lock:
            rows = self.connection.execute(
                "SELECT vector_id, metadata, bm25(wiki_fts, 0, 0, 4, 3, 2, 1, 0) AS rank FROM wiki_fts WHERE wiki_fts MATCH ? ORDER BY rank LIMIT ?",
                (expression, limit * 3),
            ).fetchall()
        results = []
        for vector_id, raw_metadata, rank in rows:
            metadata = json.loads(raw_metadata)
            if domains and metadata.get("knowledge_domain") not in domains:
                continue
            if rag_only and metadata.get("access", "rag") != "rag":
                continue
            results.append({"vector_id": vector_id, "keyword_rank": float(rank)})
            if len(results) == limit:
                break
        return results
