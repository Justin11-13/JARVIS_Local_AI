"""Decide whether a user question should consult the local RAG knowledge base."""

from __future__ import annotations

import re
from dataclasses import dataclass


JARVIS_KNOWLEDGE_TERMS = {
    # Product
    "jarvis",
    "javis",

    # Architecture
    "architecture",
    "架构",
    "構架",
    "结构",
    "結構",

    # Project scope
    "project scope",
    "scope",
    "项目范围",
    "項目範圍",

    # Tools / capabilities
    "native tool",
    "native tools",
    "tool",
    "tools",
    "功能",
    "能力",
    "可以做什么",
    "能做什么",

    # Routing
    "routing",
    "router",
    "task router",
    "taskrouter",
    "路由",

    # Permissions / safety
    "permission",
    "permissions",
    "permission manager",
    "permissionmanager",
    "权限",
    "權限",
    "安全机制",
    "安全機制",
    "risk",
    "风险",
    "風險",

    # Knowledge / memory
    "rag",
    "knowledge",
    "knowledge base",
    "memory",
    "long-term memory",
    "长期记忆",
    "長期記憶",
    "知识库",
    "知識庫",

    # Project internals
    "task manager",
    "taskmanager",
    "notification",
    "notifications",
    "milestone",
    "milestones",
    "development principle",
    "development principles",
}


JARVIS_REFERENCE_PATTERNS = (
    r"\bmy\s+jarvis\b",
    r"\bthis\s+jarvis\b",
    r"\bjarvis['’]s\b",
    r"我的\s*jarvis",
    r"这个\s*jarvis",
    r"這個\s*jarvis",
)

JARVIS_INTEGRATION_PATTERNS = (
    r"\bjarvis\b.{0,30}\b(?:gemini|codex)\b",
    r"\b(?:gemini|codex)\b.{0,30}\bjarvis\b",
    r"(?:你的|你现在|你目前|在\s*jarvis\s*(?:中|里)).{0,20}(?:gemini|codex)",
    r"(?:gemini|codex).{0,20}(?:在你|你的|你现在|你目前)",
)

OBSIDIAN_TERMS = (
    "obsidian", "vault", "我的笔记", "我的筆記", "我的知识库", "我的知識庫",
    "我的资料", "我的資料", "我记录的", "我記錄的", "课程笔记", "課程筆記",
)


@dataclass(frozen=True)
class KnowledgeRoute:
    use_rag: bool
    domains: tuple[str, ...] = ()


def route_knowledge(query: str) -> KnowledgeRoute:
    normalized = " ".join(query.strip().lower().split())
    if not normalized:
        return KnowledgeRoute(False)
    obsidian = any(term in normalized for term in OBSIDIAN_TERMS)
    jarvis = _is_jarvis_query(normalized)
    # A Vault query includes its JARVIS subtree as well as other knowledge.
    jarvis = jarvis or obsidian
    domains = tuple(domain for domain, selected in (("jarvis", jarvis), ("obsidian", obsidian)) if selected)
    return KnowledgeRoute(bool(domains), domains)


def _is_jarvis_query(normalized: str) -> bool:
    if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in JARVIS_REFERENCE_PATTERNS):
        return True
    if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in JARVIS_INTEGRATION_PATTERNS):
        return True
    return any(term in normalized for term in JARVIS_KNOWLEDGE_TERMS)


def should_use_rag(query: str) -> bool:
    """
    Return True when the question appears to concern knowledge
    stored in the JARVIS knowledge base.

    This router is deliberately local and deterministic.
    It does not call Gemini.
    """

    return route_knowledge(query).use_rag


if __name__ == "__main__":
    while True:
        try:
            question = input(
                "Question (Ctrl+C to exit): "
            )
        except KeyboardInterrupt:
            print()
            break

        print(
            "Use RAG:",
            should_use_rag(question),
        )
