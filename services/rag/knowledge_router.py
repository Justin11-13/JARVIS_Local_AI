"""Decide whether a user question should consult the local RAG knowledge base."""

from __future__ import annotations

import re


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

    # Gemini
    "gemini",

    # Codex
    "codex",

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


def should_use_rag(query: str) -> bool:
    """
    Return True when the question appears to concern knowledge
    stored in the JARVIS knowledge base.

    This router is deliberately local and deterministic.
    It does not call Gemini.
    """

    normalized = " ".join(
        query.strip().lower().split()
    )

    if not normalized:
        return False

    for pattern in JARVIS_REFERENCE_PATTERNS:
        if re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE,
        ):
            return True

    return any(
        term in normalized
        for term in JARVIS_KNOWLEDGE_TERMS
    )


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